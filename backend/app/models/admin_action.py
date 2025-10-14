from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AdminAction(Base):
    __tablename__ = "admin_actions"
    
    id = Column(String(36), primary_key=True)
    admin_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    action_type = Column(String(100), nullable=False, index=True)
    affected_user_id = Column(String(36))
    affected_project_id = Column(String(36))
    
    details = Column(JSON, nullable=False)
    reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    admin = relationship("User", back_populates="admin_actions", foreign_keys=[admin_user_id])
