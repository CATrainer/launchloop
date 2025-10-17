from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.conversation import (
    Conversation, ConversationMessage, ConversationPhase,
    EngagementLevel, MessageType, DataField
)
from app.utils.helpers import generate_uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    """
    Manages conversation state and intelligence
    This is the SECRET SAUCE - confidence-based, context-aware conversation
    """
    
    # Confidence thresholds for progression
    HIGH_CONFIDENCE = 0.7
    MEDIUM_CONFIDENCE = 0.5
    LOW_CONFIDENCE = 0.3
    
    # Core data fields we need to extract
    CORE_FIELDS = [
        "problem_statement",
        "target_audience",
        "unique_value",
        "product_stage",
        "product_name"
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, user_id: str, project_id: str = None) -> Conversation:
        """Start a new conversation"""
        conversation = Conversation(
            id=generate_uuid(),
            user_id=user_id,
            project_id=project_id,
            phase=ConversationPhase.IDEA_SATURATION,
            extracted_data={},
            template_data={},
            user_engagement_level=EngagementLevel.MEDIUM,
            message_count=0
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        **kwargs
    ) -> ConversationMessage:
        """Add a message to the conversation"""
        message = ConversationMessage(
            id=generate_uuid(),
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            message_type=message_type,
            quick_replies=kwargs.get("quick_replies"),
            templates=kwargs.get("templates"),
            thinking_status=kwargs.get("thinking_status")
        )
        
        self.db.add(message)
        
        # Update conversation metadata
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if sender == "user":
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def update_extracted_data(
        self,
        conversation_id: str,
        extracted_data: Dict[str, Dict]
    ) -> Conversation:
        """
        Update extracted data with confidence scores
        Merges new data with existing (higher confidence wins)
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        current_data = conversation.extracted_data or {}
        
        # Merge data - higher confidence wins
        for field, new_data in extracted_data.items():
            current_field = current_data.get(field, {})
            current_confidence = current_field.get("confidence", 0.0)
            new_confidence = new_data.get("confidence", 0.0)
            
            if new_confidence > current_confidence:
                current_data[field] = new_data
                logger.info(f"Updated {field} with confidence {new_confidence}")
        
        conversation.extracted_data = current_data
        conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def determine_engagement_level(self, conversation: Conversation) -> EngagementLevel:
        """
        Analyze user's communication style from recent messages
        Match AI verbosity to user's style
        """
        # Get last 5 user messages
        recent_messages = [
            m for m in conversation.messages[-5:]
            if m.sender == "user"
        ]
        
        if not recent_messages:
            return EngagementLevel.MEDIUM
        
        avg_length = sum(len(m.content) for m in recent_messages) / len(recent_messages)
        
        if avg_length < 50:
            return EngagementLevel.LOW  # Brief - AI should be concise
        elif avg_length < 200:
            return EngagementLevel.MEDIUM  # Moderate - conversational
        else:
            return EngagementLevel.HIGH  # Detailed - AI can match depth
    
    def can_transition_to_template_selection(self, conversation: Conversation) -> bool:
        """
        INTELLIGENT transition decision based on confidence scores
        NOT rule-based ("after N questions")
        """
        data = conversation.extracted_data
        
        # Need high confidence on core fields
        problem_confidence = data.get("problem_statement", {}).get("confidence", 0)
        audience_confidence = data.get("target_audience", {}).get("confidence", 0)
        
        # Must have good understanding of problem and audience
        if problem_confidence < self.HIGH_CONFIDENCE:
            return False
        if audience_confidence < self.HIGH_CONFIDENCE:
            return False
        
        # Need minimum conversation depth (avoid rushing)
        if conversation.message_count < 3:
            return False
        
        # Value proposition can be fuzzier for early-stage ideas
        value_confidence = data.get("unique_value", {}).get("confidence", 0)
        product_stage = data.get("product_stage", {}).get("value")
        
        if product_stage == "idea" and value_confidence > self.MEDIUM_CONFIDENCE:
            return True
        elif value_confidence > self.MEDIUM_CONFIDENCE:
            return True
        
        return False
    
    def can_transition_to_generation(self, conversation: Conversation) -> bool:
        """
        Check if we have all required template data with high confidence
        """
        if not conversation.selected_template_id:
            return False
        
        # Get template required fields
        from app.services.template_service import TemplateService
        template_service = TemplateService()
        template = template_service.get_template(conversation.selected_template_id)
        
        if not template:
            return False
        
        # All required fields must have high confidence
        template_data = conversation.template_data or {}
        
        for field in template.required_fields:
            field_data = template_data.get(field["id"], {})
            confidence = field_data.get("confidence", 0)
            
            if confidence < self.HIGH_CONFIDENCE:
                logger.info(f"Field {field['id']} confidence too low: {confidence}")
                return False
        
        return True
    
    def get_missing_fields(self, conversation: Conversation) -> List[str]:
        """
        Get list of fields we still need with low confidence
        Helps AI know what to ask about
        """
        missing = []
        
        if conversation.phase == ConversationPhase.IDEA_SATURATION:
            # Check core fields
            for field in self.CORE_FIELDS:
                data = conversation.extracted_data.get(field, {})
                confidence = data.get("confidence", 0)
                
                if confidence < self.HIGH_CONFIDENCE:
                    missing.append(field)
        
        elif conversation.phase == ConversationPhase.DATA_GATHERING:
            # Check template fields
            from app.services.template_service import TemplateService
            template_service = TemplateService()
            template = template_service.get_template(conversation.selected_template_id)
            
            if template:
                template_data = conversation.template_data or {}
                
                for field in template.required_fields:
                    field_data = template_data.get(field["id"], {})
                    confidence = field_data.get("confidence", 0)
                    
                    if confidence < self.HIGH_CONFIDENCE:
                        missing.append(field["label"])
        
        return missing
    
    def should_transition_phase(self, conversation: Conversation) -> Optional[ConversationPhase]:
        """
        Determine if we should transition to a new phase
        Returns new phase if ready, None otherwise
        """
        current_phase = conversation.phase
        
        if current_phase == ConversationPhase.IDEA_SATURATION:
            if self.can_transition_to_template_selection(conversation):
                return ConversationPhase.NAME_DISCUSSION
        
        elif current_phase == ConversationPhase.NAME_DISCUSSION:
            # Always move to template selection after discussing name
            name_data = conversation.extracted_data.get("product_name", {})
            if name_data.get("confidence", 0) > self.MEDIUM_CONFIDENCE or conversation.message_count > 10:
                return ConversationPhase.TEMPLATE_SELECTION
        
        elif current_phase == ConversationPhase.TEMPLATE_SELECTION:
            # Move to data gathering after template selected
            if conversation.selected_template_id:
                return ConversationPhase.DATA_GATHERING
        
        elif current_phase == ConversationPhase.DATA_GATHERING:
            if self.can_transition_to_generation(conversation):
                return ConversationPhase.GENERATION
        
        return None
    
    def transition_phase(self, conversation_id: str, new_phase: ConversationPhase) -> Conversation:
        """Transition to a new conversation phase"""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        old_phase = conversation.phase
        conversation.phase = new_phase
        conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        logger.info(f"Conversation {conversation_id} transitioned: {old_phase} → {new_phase}")
        
        return conversation
    
    def format_conversation_history(
        self,
        conversation: Conversation,
        last_n: int = 5
    ) -> str:
        """Format recent conversation history for AI context"""
        recent_messages = conversation.messages[-last_n:] if conversation.messages else []
        
        formatted = []
        for msg in recent_messages:
            sender_label = "User" if msg.sender == "user" else "AI"
            formatted.append(f"{sender_label}: {msg.content}")
        
        return "\n".join(formatted)
    
    def format_knowledge_state(self, conversation: Conversation) -> str:
        """Format extracted data with confidence scores for AI context"""
        data = conversation.extracted_data or {}
        
        formatted = []
        for field, field_data in data.items():
            value = field_data.get("value", "unknown")
            confidence = field_data.get("confidence", 0)
            
            confidence_label = (
                "HIGH" if confidence >= self.HIGH_CONFIDENCE
                else "MEDIUM" if confidence >= self.MEDIUM_CONFIDENCE
                else "LOW"
            )
            
            formatted.append(f"- {field}: \"{value}\" (confidence: {confidence:.2f} - {confidence_label})")
        
        return "\n".join(formatted) if formatted else "No data extracted yet"
