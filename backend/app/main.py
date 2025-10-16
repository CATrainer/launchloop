from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.config import settings
from app.api import api_router
from app.middleware.subdomain import subdomain_middleware
from app.database import SessionLocal
from app.services.cache import cache_service
from app.utils.logger import get_logger
import sentry_sdk

logger = get_logger(__name__)

# Initialize Sentry if configured
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=settings.ENV
    )

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Build allowed origins list
allowed_origins = [settings.FRONTEND_URL]
if settings.CORS_ORIGINS:
    # Split comma-separated origins and strip whitespace
    additional_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    allowed_origins.extend(additional_origins)

# Log CORS configuration on startup
logger.info("CORS Configuration", extra={"allowed_origins": allowed_origins})

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Subdomain routing middleware
app.middleware("http")(subdomain_middleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "environment": settings.ENV
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        logger.error("Database health check failed", extra={"error": str(e)})
    
    # Check Redis
    try:
        if cache_service.redis_client:
            cache_service.redis_client.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not configured"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
        logger.error("Redis health check failed", extra={"error": str(e)})
    
    # Determine overall status
    all_healthy = checks["database"] == "healthy" and checks["redis"] in ["healthy", "not configured"]
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Launch Loop API",
        "version": "1.0.0",
        "environment": settings.ENV,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error("Unhandled exception", extra={
        "path": request.url.path,
        "method": request.method,
        "error": str(exc)
    }, exc_info=True)
    
    # Send to Sentry if configured
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    # Don't expose internal details in production
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again later."
        }
    )
