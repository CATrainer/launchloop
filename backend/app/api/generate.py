from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import json
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.schemas.generation import GenerationCreate, GenerationResponse, ExtractionResponse, QuestionResponse
from app.services.generation import generation_service
from app.services.templates import template_registry
from app.services.llm import llm_service
from app.tasks.generation import process_generation
from app.utils.logger import get_logger
from app.middleware.rate_limit import check_rate_limit
from app.models.generation import Generation, GenerationStatus

logger = get_logger(__name__)

router = APIRouter()


@router.post("/{generation_id}/retry")
async def retry_generation(
    generation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry a failed generation"""
    
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    # Verify ownership
    project = db.query(Project).filter(Project.id == generation.project_id).first()
    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Can only retry failed generations
    if generation.status != "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only retry failed generations"
        )
    
    # Reset generation status
    generation.status = "PENDING"
    generation.progress = 0
    generation.error_message = None
    db.commit()
    
    # Queue task
    process_generation.delay(generation.id)
    
    return {"message": "Generation retrying", "generation_id": generation.id}


@router.post("/extract")
async def extract_info(
    user_input: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract structured information from user's product description"""
    
    description = user_input.get("description", "")
    
    if not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description required"
        )
    
    # Extract info using LLM
    extracted = llm_service.extract_product_info(description)
    
    # Get template recommendations
    product_type = extracted.get("product_type", "b2b_saas")
    stage = extracted.get("stage", "idea")
    
    suggested_templates = template_registry.recommend_templates(product_type, stage)
    extracted["suggested_templates"] = suggested_templates
    
    return extracted


@router.post("/questions")
async def generate_questions(
    request_data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate questions to fill gaps in extracted data"""
    
    template_id = request_data.get("template_id")
    extracted_data = request_data.get("extracted_data", {})
    
    if not template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template ID required"
        )
    
    # Get template
    template = template_registry.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Generate questions
    questions = llm_service.generate_questions(
        template['config'],
        extracted_data
    )
    
    return {"questions": questions}


@router.post("", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new generation"""
    
    # Get raw body for debugging
    body = await request.json()
    logger.debug("Generation request received", extra={
        "project_id": body.get('project_id'),
        "template_id": body.get('template_id'),
        "type": body.get('type')
    })
    
    # Parse with Pydantic
    try:
        generation_data = GenerationCreate(**body)
    except Exception as e:
        logger.error("Generation request validation error", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    # Rate limiting: 3 generations per hour to prevent abuse
    check_rate_limit(
        user.id,
        "generation",
        max_count=3,
        window_minutes=60
    )
    
    # Get project
    project = db.query(Project).filter(
        Project.id == generation_data.project_id,
        Project.user_id == user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check for pending/running generations (idempotency)
    pending_generation = db.query(Generation).filter(
        Generation.project_id == project.id,
        Generation.status.in_([
            GenerationStatus.PENDING,
            GenerationStatus.ANALYZING,
            GenerationStatus.GENERATING_COPY,
            GenerationStatus.GENERATING_IMAGES,
            GenerationStatus.ASSEMBLING
        ])
    ).first()
    
    if pending_generation:
        logger.info("Returning existing pending generation", extra={
            "generation_id": pending_generation.id,
            "user_id": user.id
        })
        return pending_generation
    
    # Check if user can generate
    can_generate, error_msg = generation_service.can_user_generate(
        user,
        generation_data.type.value
    )
    
    if not can_generate:
        logger.warning("Generation blocked - limit reached", extra={
            "user_id": user.id,
            "tier": user.tier.value,
            "reason": error_msg,
            "generations_used": user.generations_used_this_month,
            "revisions_used": user.revisions_used_this_month
        })
        
        # Get tier limits for better error message
        from app.utils.helpers import get_tier_limits
        limits = get_tier_limits(user.tier.value)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": error_msg,
                "tier": user.tier.value,
                "generations_used": user.generations_used_this_month,
                "generations_limit": limits["generations_per_month"],
                "revisions_used": user.revisions_used_this_month,
                "revisions_limit": limits["revisions_per_month"],
                "usage_reset_date": user.usage_reset_date.isoformat() if user.usage_reset_date else None
            }
        )
    
    # Create generation
    generation = generation_service.create_generation(
        db,
        user,
        project,
        generation_data.template_id,
        generation_data.input_data,
        generation_data.type.value
    )
    
    # Queue background task
    process_generation.delay(generation.id)
    
    logger.info("Generation queued", extra={
        "generation_id": generation.id,
        "project_id": project.id,
        "user_id": user.id,
        "type": generation_data.type.value
    })
    
    return generation


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get generation status"""
    
    generation = db.query(Generation).join(Project).filter(
        Generation.id == generation_id,
        Project.user_id == user.id
    ).first()
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    return generation


@router.get("/templates", response_model=List[dict])
async def list_templates():
    """List all available templates"""
    
    templates = template_registry.get_all_templates()
    return templates
