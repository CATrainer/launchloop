from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth import create_user, authenticate_user, create_user_token
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit, get_client_ip
from app.models.user import User
from app.tasks.email import send_welcome_email
from app.utils.validators import validate_email
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
async def signup(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Sign up a new user"""
    
    # Validate email
    is_valid, email_or_error = validate_email(user_data.email)
    if not is_valid:
        logger.warning("Signup blocked - invalid email", extra={
            "email": user_data.email,
            "error": email_or_error
        })
        raise HTTPException(
            status_code=400,
            detail=email_or_error
        )
    
    # Use normalized email
    user_data.email = email_or_error
    
    # Rate limiting
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip, "signup", max_count=10, window_minutes=1440)  # 10 per day
    
    logger.info("User signup initiated", extra={"email": user_data.email})
    
    # Create user
    user = create_user(db, user_data)
    
    # Create JWT token
    token = create_user_token(user)
    
    # Set HTTP-only cookie
    # secure=True only in production (requires HTTPS)
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=settings.ENV == "production",  # Only HTTPS in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
        domain=None  # Let browser handle it
    )
    
    # Send welcome email (async task)
    send_welcome_email.delay(user.email)
    
    logger.info("User signup complete", extra={"user_id": user.id, "email": user.email})
    
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Log in a user"""
    
    # Validate email format
    is_valid, email_or_error = validate_email(credentials.email)
    if not is_valid:
        # Don't reveal if email is invalid, just say credentials are wrong
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Authenticate user
    user = authenticate_user(db, email_or_error, credentials.password)
    
    logger.info("User login successful", extra={"user_id": user.id})
    
    # Create JWT token
    token = create_user_token(user)
    
    # Set HTTP-only cookie
    # secure=True only in production (requires HTTPS)
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=settings.ENV == "production",  # Only HTTPS in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
        domain=None  # Let browser handle it
    )
    
    return user


@router.post("/logout")
async def logout(response: Response):
    """Log out a user"""
    
    # Clear cookie with same parameters as when it was set
    response.delete_cookie(
        key="token",
        domain=None,
        path="/"
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user"""
    return user
