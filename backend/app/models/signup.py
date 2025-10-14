from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Signup(Base):
    __tablename__ = "signups"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email = Column(String(255), nullable=False, index=True)
    signup_metadata = Column(JSON)  # referrer, utm params, etc
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    project = relationship("Project", back_populates="signups")
