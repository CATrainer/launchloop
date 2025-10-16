from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.utils.helpers import generate_uuid
from app.utils.validators import validate_subdomain, sanitize_input
from app.services.cache import cache_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    
    # Sanitize input
    name = sanitize_input(project_data.name, max_length=200)
    
    project = Project(
        id=generate_uuid(),
        user_id=user.id,
        name=name,
        status=ProjectStatus.DRAFT
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    logger.info("Project created", extra={"project_id": project.id, "user_id": user.id})
    
    return project


@router.get("", response_model=List[ProjectListResponse])
async def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects for current user"""
    
    projects = db.query(Project).filter(
        Project.user_id == user.id
    ).order_by(Project.updated_at.desc()).all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
    
    if project_data.subdomain is not None:
        # Validate subdomain
        if not validate_subdomain(project_data.subdomain):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subdomain format"
            )
        
        # Check availability
        existing = db.query(Project).filter(
            Project.subdomain == project_data.subdomain,
            Project.id != project_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subdomain already taken"
            )
        
        project.subdomain = project_data.subdomain
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return None


@router.post("/{project_id}/publish")
async def publish_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain required for publishing"
        )
    
    if not project.html_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must be generated before publishing"
        )
    
    project.status = ProjectStatus.PUBLISHED
    project.published_at = datetime.utcnow()
    project.subdomain_reserved_at = datetime.utcnow()
    
    db.commit()
    
    # Cache the HTML for fast serving
    if project.html_content:
        cache_service.cache_project_html(project.subdomain, project.html_content)
    
    logger.info("Project published", extra={
        "project_id": project.id,
        "subdomain": project.subdomain,
        "user_id": user.id
    })
    
    return {"message": "Project published successfully"}


@router.post("/{project_id}/unpublish")
async def unpublish_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unpublish a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.status = ProjectStatus.GENERATED
    
    db.commit()
    
    # Invalidate cache
    if project.subdomain:
        cache_service.invalidate_project_cache(subdomain=project.subdomain)
    if project.custom_domain:
        cache_service.invalidate_project_cache(domain=project.custom_domain)
    
    logger.info("Project unpublished", extra={
        "project_id": project.id,
        "user_id": user.id
    })
    
    return {"message": "Project unpublished successfully"}


@router.post("/{project_id}/save-state")
async def save_creation_state(
    project_id: str,
    state_data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save project creation flow state for persistence"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Save creation state
    project.creation_state = state_data
    project.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "State saved successfully"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}
