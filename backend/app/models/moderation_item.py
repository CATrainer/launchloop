from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum
from datetime import datetime
import enum
from app.database import Base


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationItem(Base):
    __tablename__ = "moderation_items"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    
    flagged_reason = Column(String(255), nullable=False)
    flagged_content = Column(JSON, nullable=False)
    
    status = Column(SQLEnum(ModerationStatus), default=ModerationStatus.PENDING, nullable=False, index=True)
    reviewed_by = Column(String(36))
    reviewed_at = Column(DateTime)
    decision = Column(String(50))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
