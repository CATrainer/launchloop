from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, Tier, PaymentStatus
from app.schemas.user import UserCreate
from app.utils.helpers import generate_uuid, get_usage_reset_date
from app.utils.jwt import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        id=generate_uuid(),
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        tier=Tier.FREE,
        payment_status=PaymentStatus.ACTIVE,
        usage_reset_date=get_usage_reset_date()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate a user"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    return user


def create_user_token(user: User) -> str:
    """Create JWT token for user"""
    return create_access_token({
        "userId": user.id,
        "email": user.email,
        "role": user.role.value
    })
