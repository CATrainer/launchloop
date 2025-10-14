from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.models.user import Role, Tier, SubscriptionStatus, PaymentStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    role: Role
    tier: Tier
    subscription_status: Optional[SubscriptionStatus]
    payment_status: PaymentStatus
    generations_used_this_month: int
    revisions_used_this_month: int
    usage_reset_date: datetime
    created_at: datetime
    last_active_at: datetime
    
    class Config:
        from_attributes = True
