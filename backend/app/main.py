from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import api_router
from app.middleware.subdomain import subdomain_middleware
import sentry_sdk

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
if settings.ALLOWED_ORIGINS:
    # Split comma-separated origins and strip whitespace
    additional_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
    allowed_origins.extend(additional_origins)

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Launch Loop API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }
