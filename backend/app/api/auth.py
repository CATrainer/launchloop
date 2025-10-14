from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth import create_user, authenticate_user, create_user_token
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import check_rate_limit, get_client_ip
from app.models.user import User
from app.tasks.email import send_welcome_email

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
async def signup(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Sign up a new user"""
    
    # Rate limiting
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip, "signup", max_count=10, window_minutes=1440)  # 10 per day
    
    # Create user
    user = create_user(db, user_data)
    
    # Create JWT token
    token = create_user_token(user)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    # Send welcome email (async task)
    send_welcome_email.delay(user.email)
    
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Log in a user"""
    
    # Authenticate user
    user = authenticate_user(db, credentials.email, credentials.password)
    
    # Create JWT token
    token = create_user_token(user)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return user


@router.post("/logout")
async def logout(response: Response):
    """Log out a user"""
    
    # Clear cookie
    response.delete_cookie(key="token")
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get current user"""
    return user
