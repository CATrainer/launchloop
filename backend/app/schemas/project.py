from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    initial_description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subdomain: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    status: ProjectStatus
    subdomain: Optional[str]
    custom_domain: Optional[str]
    template_id: Optional[str]
    template_version: Optional[str]
    generated_data: Optional[Dict[str, Any]]
    html_content: Optional[str]
    signups_count: int
    export_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    id: str
    name: str
    status: ProjectStatus
    subdomain: Optional[str]
    signups_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True
