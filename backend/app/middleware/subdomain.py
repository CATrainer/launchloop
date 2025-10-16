from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectStatus
from app.config import settings
from app.services.cache import cache_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def subdomain_middleware(request: Request, call_next):
    """Handle subdomain routing to published projects"""
    # Skip subdomain logic for CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Check X-Original-Host first (set by Cloudflare Worker)
    # We use X-Original-Host instead of X-Forwarded-Host because Cloudflare
    # overwrites X-Forwarded-Host when proxying through api.thelaunchloop.com
    host = request.headers.get("x-original-host", "") or request.headers.get("host", "")
    
    # Log at INFO level so we can see it in Railway logs
    logger.info("Subdomain middleware processing", extra={
        "host": host,
        "x_original_host": request.headers.get("x-original-host"),
        "x_forwarded_host": request.headers.get("x-forwarded-host"),
        "original_host": request.headers.get("host"),
        "path": request.url.path
    })
    
    # Check if this is the main domain or API subdomain
    # Use EXACT match, not substring match!
    main_domains = [
        settings.MAIN_DOMAIN,
        f"www.{settings.MAIN_DOMAIN}",
        f"api.{settings.MAIN_DOMAIN}",
        f"staging.{settings.MAIN_DOMAIN}",
    ]
    
    if host in main_domains:
        logger.info("Host matches main domain, skipping subdomain routing", extra={"host": host})
        return await call_next(request)
    
    # Extract subdomain
    parts = host.split(".")
    if len(parts) < 2:
        logger.info("No subdomain detected, skipping", extra={"host": host})
        return await call_next(request)
    
    subdomain = parts[0]
    logger.info("Extracted subdomain", extra={"subdomain": subdomain, "host": host})
    
    # Try to get from cache first
    cached_html = cache_service.get_cached_project_html(subdomain)
    if cached_html:
        logger.debug("Serving project from cache", extra={"subdomain": subdomain})
        return HTMLResponse(content=cached_html)
    
    # Cache miss - query database
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # First check custom domain
        project = db.query(Project).filter(
            Project.custom_domain == host,
            Project.custom_domain_verified == True,
            Project.status == ProjectStatus.PUBLISHED
        ).first()
        
        # If not custom domain, check subdomain
        if not project:
            project = db.query(Project).filter(
                Project.subdomain == subdomain,
                Project.status == ProjectStatus.PUBLISHED
            ).first()
        
        if project and project.html_content:
            # Cache for 1 hour
            cache_service.cache_project_html(subdomain, project.html_content, ttl=3600)
            logger.info("Project loaded and cached", extra={
                "subdomain": subdomain,
                "project_id": project.id
            })
            return HTMLResponse(content=project.html_content)
        else:
            logger.info("No project found for subdomain", extra={"subdomain": subdomain, "host": host})
        
    finally:
        db.close()
    
    # If no project found, continue with normal routing
    return await call_next(request)
