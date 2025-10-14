from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.rate_limit import RateLimit
from app.utils.helpers import generate_uuid
from app.config import settings


def check_rate_limit(
    identifier: str,
    action: str,
    max_count: int,
    window_minutes: int = 60
) -> bool:
    """
    Check if rate limit is exceeded
    Returns True if within limit, raises HTTPException if exceeded
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Find existing rate limit record
        rate_limit = db.query(RateLimit).filter(
            RateLimit.identifier == identifier,
            RateLimit.action == action,
            RateLimit.reset_at > now
        ).first()
        
        if rate_limit:
            if rate_limit.count >= max_count:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again after {rate_limit.reset_at.isoformat()}"
                )
            # Increment count
            rate_limit.count += 1
            db.commit()
        else:
            # Create new rate limit record
            new_rate_limit = RateLimit(
                id=generate_uuid(),
                identifier=identifier,
                action=action,
                count=1,
                reset_at=now + timedelta(minutes=window_minutes)
            )
            db.add(new_rate_limit)
            db.commit()
        
        return True
    finally:
        db.close()


def get_client_ip(request: Request) -> str:
    """Get client IP from request"""
    # Check X-Forwarded-For header (from proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return request.client.host if request.client else "unknown"
