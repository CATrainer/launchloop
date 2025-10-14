from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class GenerationType(str, enum.Enum):
    NEW = "new"
    REVISION = "revision"


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING_COPY = "generating_copy"
    GENERATING_IMAGES = "generating_images"
    ASSEMBLING = "assembling"
    COMPLETE = "complete"
    FAILED = "failed"


class Generation(Base):
    __tablename__ = "generations"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    generation_number = Column(Integer, nullable=False)
    type = Column(SQLEnum(GenerationType), nullable=False)
    
    # Template & data
    template_id = Column(String(255), nullable=False)
    template_version = Column(String(50), nullable=False)
    input_data = Column(JSON, nullable=False)  # User's answers
    generated_copy = Column(JSON)  # LLM output
    
    # Images
    images = Column(JSON)  # URLs + metadata
    
    # Status tracking
    status = Column(SQLEnum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    error_message = Column(Text)
    
    # Costs tracking (internal)
    llm_cost = Column(Float)
    image_cost = Column(Float)
    total_cost = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="generations")
