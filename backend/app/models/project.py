from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    GENERATED = "generated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True)
    
    # Landing page specific
    subdomain = Column(String(255), unique=True, index=True)
    subdomain_reserved_at = Column(DateTime)
    subdomain_released_at = Column(DateTime)
    custom_domain = Column(String(255), unique=True, index=True)
    custom_domain_verified = Column(Boolean, default=False, nullable=False)
    
    # Template & generation
    template_id = Column(String(255))
    template_version = Column(String(50))
    generated_data = Column(JSON)  # All copy fields
    html_content = Column(Text)
    
    # Creation flow state (for persistence)
    creation_state = Column(JSON)  # {step: int, extracted_data: dict, answers: dict, selected_template: str}
    
    # Signups tracking
    signups_count = Column(Integer, default=0, nullable=False)
    last_signup_at = Column(DateTime)
    
    # Export tracking
    last_exported_at = Column(DateTime)
    export_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    generations = relationship("Generation", back_populates="project", cascade="all, delete-orphan")
    signups = relationship("Signup", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="project", cascade="all, delete-orphan")
