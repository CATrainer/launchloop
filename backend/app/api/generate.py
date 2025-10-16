from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.generation import Generation
from app.schemas.generation import (
    GenerationCreate,
    GenerationResponse,
    QuestionResponse,
    ExtractionResponse
)
from app.services.generation import generation_service
from app.services.llm import llm_service
from app.services.templates import template_registry
from app.tasks.generation import process_generation
import json

router = APIRouter()


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
    print(f"🔍 RAW Generation request body:")
    print(json.dumps(body, indent=2))
    
    # Parse with Pydantic
    try:
        generation_data = GenerationCreate(**body)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
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
    
    # Check if user can generate
    can_generate, error_msg = generation_service.can_user_generate(
        user,
        generation_data.type.value
    )
    
    if not can_generate:
        print(f"❌ Generation blocked for user {user.id} (tier: {user.tier.value})")
        print(f"   Reason: {error_msg}")
        print(f"   Generations used: {user.generations_used_this_month}")
        print(f"   Revisions used: {user.revisions_used_this_month}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
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
