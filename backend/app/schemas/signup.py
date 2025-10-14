from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any


class SignupCreate(BaseModel):
    email: EmailStr
    metadata: Optional[Dict[str, Any]] = None


class SignupResponse(BaseModel):
    id: str
    project_id: str
    email: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True
