from fastapi import APIRouter
from app.api import auth, projects, generate, signups, admin, webhooks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(generate.router, prefix="/generate", tags=["generate"])
api_router.include_router(signups.router, prefix="/signups", tags=["signups"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
