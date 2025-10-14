from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User, Role
from app.utils.jwt import decode_access_token
from datetime import datetime


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT cookie"""
    token = request.cookies.get("token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Update last active
    user.last_active_at = datetime.utcnow()
    db.commit()
    
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """Require user to be admin"""
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
