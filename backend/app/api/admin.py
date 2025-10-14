"""
Admin API routes
Requires admin role for all endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.models.project import Project
from app.models.generation import Generation, GenerationStatus
from app.models.admin_action import AdminAction
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/overview")
async def get_admin_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard overview with key metrics"""
    
    # User metrics
    total_users = db.query(func.count(User.id)).scalar()
    active_users_30d = db.query(func.count(User.id)).filter(
        User.last_active_at >= datetime.utcnow() - timedelta(days=30)
    ).scalar()
    
    # Tier breakdown
    tier_counts = db.query(
        User.tier,
        func.count(User.id)
    ).group_by(User.tier).all()
    
    # Project metrics
    total_projects = db.query(func.count(Project.id)).scalar()
    published_projects = db.query(func.count(Project.id)).filter(
        Project.status == "published"
    ).scalar()
    
    # Generation metrics  
    total_generations = db.query(func.count(Generation.id)).scalar()
    failed_generations = db.query(func.count(Generation.id)).filter(
        Generation.status == GenerationStatus.FAILED
    ).scalar()
    
    # Recent activity
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
    recent_generations = db.query(Generation).order_by(desc(Generation.created_at)).limit(5).all()
    
    return {
        "users": {
            "total": total_users,
            "active_30d": active_users_30d,
            "by_tier": {tier: count for tier, count in tier_counts}
        },
        "projects": {
            "total": total_projects,
            "published": published_projects
        },
        "generations": {
            "total": total_generations,
            "failed": failed_generations,
            "success_rate": round((total_generations - failed_generations) / total_generations * 100, 2) if total_generations > 0 else 0
        },
        "recent_activity": {
            "users": [{"id": u.id, "email": u.email, "created_at": u.created_at} for u in recent_users],
            "generations": [{"id": g.id, "status": g.status.value, "created_at": g.created_at} for g in recent_generations]
        }
    }


@router.get("/users")
async def search_users(
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Search and filter users"""
    
    query = db.query(User)
    
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    
    if tier:
        query = query.filter(User.tier == tier)
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "users": users,
        "limit": limit,
        "offset": offset
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Get user's projects
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    
    # Get user's generations
    generations = db.query(Generation).join(Project).filter(
        Project.user_id == user_id
    ).order_by(desc(Generation.created_at)).limit(10).all()
    
    return {
        "user": user,
        "projects": projects,
        "recent_generations": generations
    }


@router.post("/users/{user_id}/change-tier")
async def change_user_tier(
    user_id: str,
    tier: str,
    reason: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Manually change a user's tier"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    old_tier = user.tier
    user.tier = tier
    
    # Log admin action
    action = AdminAction(
        admin_user_id=current_user.id,
        action_type="change_tier",
        affected_user_id=user_id,
        details={
            "old_tier": old_tier.value,
            "new_tier": tier
        },
        reason=reason
    )
    db.add(action)
    db.commit()
    
    return {"success": True, "user": user}


@router.post("/users/{user_id}/reset-usage")
async def reset_user_usage(
    user_id: str,
    reason: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reset a user's monthly usage counts"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.generations_used_this_month = 0
    user.revisions_used_this_month = 0
    
    # Log admin action
    action = AdminAction(
        admin_user_id=current_user.id,
        action_type="reset_usage",
        affected_user_id=user_id,
        details={},
        reason=reason
    )
    db.add(action)
    db.commit()
    
    return {"success": True, "user": user}


@router.get("/generations")
async def list_generations(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all generations with optional status filter"""
    
    query = db.query(Generation)
    
    if status:
        query = query.filter(Generation.status == status)
    
    total = query.count()
    generations = query.order_by(desc(Generation.created_at)).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "generations": generations,
        "limit": limit,
        "offset": offset
    }


@router.get("/generations/{generation_id}")
async def get_generation_detail(
    generation_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get detailed generation information"""
    
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(404, "Generation not found")
    
    return {
        "generation": generation,
        "project": generation.project,
        "user": generation.project.user if generation.project else None
    }


@router.post("/generations/{generation_id}/retry")
async def retry_generation(
    generation_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retry a failed generation"""
    
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(404, "Generation not found")
    
    if generation.status != GenerationStatus.FAILED:
        raise HTTPException(400, "Can only retry failed generations")
    
    # Reset status and queue new task
    generation.status = GenerationStatus.PENDING
    generation.progress = 0
    generation.error_message = None
    db.commit()
    
    # Queue Celery task
    from app.tasks.generation import process_generation
    process_generation.delay(generation_id)
    
    # Log admin action
    action = AdminAction(
        admin_user_id=current_user.id,
        action_type="retry_generation",
        affected_user_id=generation.project.user_id if generation.project else None,
        details={"generation_id": generation_id},
        reason="Manual retry by admin"
    )
    db.add(action)
    db.commit()
    
    return {"success": True, "generation": generation}
