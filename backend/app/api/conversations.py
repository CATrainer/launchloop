from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, ConversationMessage, ConversationPhase, MessageType
from app.services.conversation import ConversationService
from app.services.conversation_ai import ConversationAI
from app.services.llm import LLMService
import json
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class CreateConversationRequest(BaseModel):
    project_id: Optional[str] = None

class SendMessageRequest(BaseModel):
    message: str

class ConversationResponse(BaseModel):
    id: str
    phase: str
    message_count: int
    extracted_data: dict
    created_at: str

class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    message_type: str
    quick_replies: Optional[List[str]] = None
    templates: Optional[List[dict]] = None
    created_at: str


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new conversation
    Returns conversation ID for subsequent messages
    """
    conversation_service = ConversationService(db)
    conversation = conversation_service.create_conversation(
        user_id=user.id,
        project_id=request.project_id
    )
    
    # Add welcome message from AI
    welcome_message = """👋 Hey! I'm your AI strategist. I'll help you create a landing page that actually converts.

Here's how this works: Just tell me about your product naturally, like you're explaining it to a friend. I'll ask some smart follow-ups, and we'll build your page together.

**So - what are you building?**"""
    
    conversation_service.add_message(
        conversation_id=conversation.id,
        sender="ai",
        content=welcome_message,
        message_type=MessageType.TEXT
    )
    
    logger.info(f"Created conversation {conversation.id} for user {user.id}")
    
    return ConversationResponse(
        id=conversation.id,
        phase=conversation.phase.value,
        message_count=conversation.message_count,
        extracted_data=conversation.extracted_data or {},
        created_at=conversation.created_at.isoformat()
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation state"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse(
        id=conversation.id,
        phase=conversation.phase.value,
        message_count=conversation.message_count,
        extracted_data=conversation.extracted_data or {},
        created_at=conversation.created_at.isoformat()
    )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in conversation"""
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Query messages directly to avoid lazy loading issues
    messages_list = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(ConversationMessage.created_at).all()
    
    messages = [
        MessageResponse(
            id=msg.id,
            sender=msg.sender,
            content=msg.content,
            message_type=msg.message_type.value,
            quick_replies=msg.quick_replies,
            templates=msg.templates,
            created_at=msg.created_at.isoformat()
        )
        for msg in messages_list
    ]
    
    return messages


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User sends a message
    Returns immediately, AI response streams via SSE endpoint
    """
    conversation_service = ConversationService(db)
    
    # Verify conversation exists and belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    user_message = conversation_service.add_message(
        conversation_id=conversation_id,
        sender="user",
        content=request.message,
        message_type=MessageType.TEXT
    )
    
    # Update engagement level based on message length
    conversation.user_engagement_level = conversation_service.determine_engagement_level(conversation)
    db.commit()
    
    logger.info(f"User message added to conversation {conversation_id}")
    
    return {
        "status": "processing",
        "message_id": user_message.id,
        "stream_url": f"/api/v1/conversations/{conversation_id}/stream"
    }


@router.get("/{conversation_id}/stream")
async def stream_ai_response(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events endpoint for streaming AI responses
    This is where the MAGIC happens - natural conversation streaming
    """
    
    # Verify conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get the last user message BEFORE the generator (while session is active)
    last_user_message = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id,
        ConversationMessage.sender == "user"
    ).order_by(ConversationMessage.created_at.desc()).first()
    
    if not last_user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found to respond to"
        )
    
    user_message_text = last_user_message.content
    
    async def event_generator():
        """Generate SSE events for streaming response"""
        try:
            # Initialize services
            conversation_service = ConversationService(db)
            llm_service = LLMService()
            conversation_ai = ConversationAI(llm_service)
            conversation_ai.conversation_service.db = db
            
            # Extract data from message (parallel with response generation)
            extracted_data = await conversation_ai.extract_data_from_message(
                user_message_text,
                conversation
            )
            
            if extracted_data:
                conversation_service.update_extracted_data(conversation_id, extracted_data)
                # Refresh conversation object
                db.refresh(conversation)
            
            # Generate AI response
            response_data = await conversation_ai.generate_response(conversation, user_message_text)
            
            # Stream the message content with typing effect
            message_id = conversation_service.add_message(
                conversation_id=conversation_id,
                sender="ai",
                content="",  # Will update with streamed content
                message_type=MessageType[response_data.get("message_type", "TEXT").upper()],
                quick_replies=response_data.get("quick_replies"),
                templates=response_data.get("templates"),
                thinking_status=response_data.get("thinking_status")
            ).id
            
            # Stream message content character by character for smooth typing effect
            message_content = response_data.get("message", "")
            accumulated_text = ""
            
            # Stream at ~50ms per chunk for natural typing
            chunk_size = 3  # characters per chunk
            for i in range(0, len(message_content), chunk_size):
                chunk = message_content[i:i+chunk_size]
                accumulated_text += chunk
                
                # Send chunk to frontend
                yield f"data: {json.dumps({'type': 'chunk', 'message_id': message_id, 'chunk': chunk, 'accumulated': accumulated_text})}\n\n"
                
                await asyncio.sleep(0.05)  # 50ms delay for smooth typing
            
            # Update message in DB with full content
            message = db.query(ConversationMessage).filter(
                ConversationMessage.id == message_id
            ).first()
            message.content = accumulated_text
            db.commit()
            
            # Update conversation with any extracted data from AI
            if response_data.get("extracted_data"):
                conversation_service.update_extracted_data(
                    conversation_id,
                    response_data["extracted_data"]
                )
            
            # Check for phase transition
            if response_data.get("should_transition") and response_data.get("next_phase"):
                next_phase = ConversationPhase[response_data["next_phase"]]
                conversation_service.transition_phase(conversation_id, next_phase)
            else:
                # Intelligent phase check
                next_phase = conversation_service.should_transition_phase(conversation)
                if next_phase:
                    conversation_service.transition_phase(conversation_id, next_phase)
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message_id': message_id, 'message_type': response_data.get('message_type', 'text'), 'quick_replies': response_data.get('quick_replies'), 'templates': response_data.get('templates')})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': 'Failed to generate response'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/{conversation_id}/select-template")
async def select_template(
    conversation_id: str,
    template_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User selects a template"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation.selected_template_id = template_id
    db.commit()
    
    logger.info(f"Template {template_id} selected for conversation {conversation_id}")
    
    return {"status": "success", "template_id": template_id}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"status": "deleted"}
