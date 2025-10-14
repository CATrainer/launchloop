from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectStatus
from app.config import settings


async def subdomain_middleware(request: Request, call_next):
    """Handle subdomain routing to published projects"""
    host = request.headers.get("host", "")
    
    # Check if this is the main domain or API subdomain
    main_domains = [
        settings.MAIN_DOMAIN,
        f"www.{settings.MAIN_DOMAIN}",
        f"api.{settings.MAIN_DOMAIN}",
        f"staging.{settings.MAIN_DOMAIN}",
    ]
    
    if any(domain in host for domain in main_domains):
        return await call_next(request)
    
    # Extract subdomain
    parts = host.split(".")
    if len(parts) < 2:
        return await call_next(request)
    
    subdomain = parts[0]
    
    # Check if it's a published project
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
            return HTMLResponse(content=project.html_content)
        
    finally:
        db.close()
    
    # If no project found, continue with normal routing
    return await call_next(request)
