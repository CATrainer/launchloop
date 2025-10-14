from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.generation import GenerationType, GenerationStatus


class QuestionResponse(BaseModel):
    field: str
    question: str
    example: Optional[str]
    required: bool


class ExtractionResponse(BaseModel):
    product_type: str
    target_audience: str
    problem: str
    solution_approach: str
    stage: str
    founder_background: Optional[str]
    completeness_score: float
    suggested_templates: List[str]


class GenerationCreate(BaseModel):
    project_id: str
    template_id: str
    input_data: Dict[str, Any]
    type: GenerationType = GenerationType.NEW


class GenerationResponse(BaseModel):
    id: str
    project_id: str
    generation_number: int
    type: GenerationType
    template_id: str
    template_version: str
    input_data: Dict[str, Any]
    generated_copy: Optional[Dict[str, Any]]
    images: Optional[List[Dict[str, Any]]]
    status: GenerationStatus
    progress: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
