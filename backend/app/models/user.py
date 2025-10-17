from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class Role(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class Tier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ULTIMATE = "ultimate"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class PaymentStatus(str, enum.Enum):
    ACTIVE = "active"
    FAILED = "failed"
    GRACE_PERIOD = "grace_period"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(Role), default=Role.USER, nullable=False)
    
    # Subscription
    tier = Column(SQLEnum(Tier), default=Tier.FREE, nullable=False)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True)
    subscription_status = Column(SQLEnum(SubscriptionStatus))
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.ACTIVE, nullable=False)
    
    # Usage tracking
    generations_used_this_month = Column(Integer, default=0, nullable=False)
    revisions_used_this_month = Column(Integer, default=0, nullable=False)
    usage_reset_date = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    admin_actions = relationship("AdminAction", back_populates="admin", foreign_keys="AdminAction.admin_user_id")
    exports = relationship("Export", back_populates="user", cascade="all, delete-orphan")
