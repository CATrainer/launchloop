from sqlalchemy import Column, String, JSON, DateTime, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class ConversationPhase(str, enum.Enum):
    """
    Internal phase tracking - NEVER shown to user
    User experiences continuous conversation
    """
    IDEA_SATURATION = "IDEA_SATURATION"  # Understanding the product
    NAME_DISCUSSION = "NAME_DISCUSSION"  # Figuring out name
    TEMPLATE_SELECTION = "TEMPLATE_SELECTION"  # Showing template options
    DATA_GATHERING = "DATA_GATHERING"  # Collecting template-specific data
    GENERATION = "GENERATION"  # Creating the page

class MessageType(str, enum.Enum):
    """Types of messages the AI can send"""
    TEXT = "text"
    QUICK_REPLIES = "quick_replies"
    TEMPLATE_SELECTION = "template_selection"
    THINKING = "thinking"
    GENERATION_PROGRESS = "generation_progress"

class EngagementLevel(str, enum.Enum):
    """User's communication style"""
    LOW = "low"  # Brief responses - AI should be concise
    MEDIUM = "medium"  # Moderate - AI can be conversational
    HIGH = "high"  # Detailed - AI can match depth

class Conversation(Base):
    """
    Tracks the conversation state with confidence scores
    This is the SECRET SAUCE - confidence-based progression
    """
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    
    # Current phase (internal, not shown to user)
    phase = Column(SQLEnum(ConversationPhase), default=ConversationPhase.IDEA_SATURATION)
    
    # Extracted data with confidence scores
    # Structure: { "field_name": { "value": "...", "confidence": 0.8, "reasoning": "..." } }
    extracted_data = Column(JSON, default=dict)
    
    # Selected template and its data
    selected_template_id = Column(String, nullable=True)
    template_data = Column(JSON, default=dict)  # Template-specific fields
    
    # Conversation metadata
    user_engagement_level = Column(SQLEnum(EngagementLevel), default=EngagementLevel.MEDIUM)
    message_count = Column(Float, default=0)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """Individual messages in the conversation"""
    __tablename__ = "conversation_messages"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    sender = Column(String, nullable=False)  # 'user' or 'ai'
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    
    # Optional structured data
    quick_replies = Column(JSON, nullable=True)  # List of quick reply options
    templates = Column(JSON, nullable=True)  # Template recommendations
    thinking_status = Column(String, nullable=True)  # "Analyzing your idea..."
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class DataField:
    """
    Helper class for confidence-scored data fields
    Not a DB model - just for type safety
    """
    def __init__(self, value: str = None, confidence: float = 0.0, reasoning: str = ""):
        self.value = value
        self.confidence = confidence  # 0.0 to 1.0
        self.reasoning = reasoning
    
    def to_dict(self):
        return {
            "value": self.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            value=data.get("value"),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", "")
        )
