from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.signup import Signup
from app.schemas.signup import SignupCreate, SignupResponse
from app.utils.helpers import generate_uuid
from app.tasks.email import send_signup_notification

router = APIRouter()


@router.post("", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def create_signup(
    signup_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a signup from a published landing page
    This endpoint is public and doesn't require authentication
    """
    
    email = signup_data.get("email")
    subdomain = signup_data.get("subdomain")
    metadata = signup_data.get("metadata", {})
    
    if not email or not subdomain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and subdomain required"
        )
    
    # Find project by subdomain
    project = db.query(Project).filter(
        Project.subdomain == subdomain,
        Project.status == ProjectStatus.PUBLISHED
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create signup
    signup = Signup(
        id=generate_uuid(),
        project_id=project.id,
        email=email,
        metadata=metadata
    )
    
    db.add(signup)
    
    # Update project stats
    project.signups_count += 1
    project.last_signup_at = datetime.utcnow()
    
    db.commit()
    db.refresh(signup)
    
    # Send notification email to project owner (async)
    owner = project.user
    send_signup_notification.delay(
        owner.email,
        project.name,
        project.subdomain
    )
    
    return signup


@router.get("/project/{project_id}", response_model=List[SignupResponse])
async def list_project_signups(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all signups for a project"""
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get signups
    signups = db.query(Signup).filter(
        Signup.project_id == project_id
    ).order_by(Signup.created_at.desc()).all()
    
    return signups


@router.get("/project/{project_id}/export")
async def export_signups(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export signups as CSV"""
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get signups
    signups = db.query(Signup).filter(
        Signup.project_id == project_id
    ).order_by(Signup.created_at.desc()).all()
    
    # Generate CSV
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Email", "Signed Up At", "Referrer", "User Agent"])
    
    # Write data
    for signup in signups:
        metadata = signup.signup_metadata or {}
        writer.writerow([
            signup.email,
            signup.created_at.isoformat(),
            metadata.get("referrer", ""),
            metadata.get("userAgent", "")
        ])
    
    csv_content = output.getvalue()
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=signups_{project.subdomain}.csv"
        }
    )
