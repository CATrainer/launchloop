from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ExportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    EXPIRED = "expired"


class Export(Base):
    __tablename__ = "exports"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(SQLEnum(ExportStatus), default=ExportStatus.PENDING, nullable=False, index=True)
    download_url = Column(String(512))
    file_size_bytes = Column(Integer)
    
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="exports")
    project = relationship("Project", back_populates="exports")
