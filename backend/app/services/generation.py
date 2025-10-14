from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from app.models.project import Project, ProjectStatus
from app.models.generation import Generation, GenerationType, GenerationStatus
from app.models.user import User
from app.services.templates import template_registry
from app.services.llm import llm_service
from app.services.images import image_service
from app.services.storage import storage_service
from app.utils.helpers import generate_uuid, get_tier_limits, should_reset_usage, get_usage_reset_date


class GenerationService:
    """Service for managing generation process"""
    
    def can_user_generate(self, user: User, generation_type: str) -> tuple[bool, str]:
        """Check if user can create a new generation"""
        
        # Reset usage if needed
        if should_reset_usage(user.usage_reset_date):
            user.generations_used_this_month = 0
            user.revisions_used_this_month = 0
            user.usage_reset_date = get_usage_reset_date()
        
        limits = get_tier_limits(user.tier.value)
        
        if generation_type == GenerationType.NEW.value:
            max_gens = limits["generations_per_month"]
            if max_gens != -1 and user.generations_used_this_month >= max_gens:
                return False, f"Monthly generation limit reached ({max_gens})"
        
        elif generation_type == GenerationType.REVISION.value:
            max_revs = limits["revisions_per_month"]
            if max_revs != -1 and user.revisions_used_this_month >= max_revs:
                return False, f"Monthly revision limit reached ({max_revs})"
        
        return True, ""
    
    def create_generation(
        self,
        db: Session,
        user: User,
        project: Project,
        template_id: str,
        input_data: Dict[str, Any],
        generation_type: str = GenerationType.NEW.value
    ) -> Generation:
        """Create a new generation record"""
        
        # Get template config
        template = template_registry.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template_config = template['config']
        
        # Count existing generations for this project
        generation_count = db.query(Generation).filter(
            Generation.project_id == project.id
        ).count()
        
        # Create generation
        generation = Generation(
            id=generate_uuid(),
            project_id=project.id,
            generation_number=generation_count + 1,
            type=GenerationType(generation_type),
            template_id=template_id,
            template_version=template_config['version'],
            input_data=input_data,
            status=GenerationStatus.PENDING,
            progress=0
        )
        
        db.add(generation)
        
        # Update project status
        project.status = ProjectStatus.GENERATING
        
        # Increment user usage counter
        if generation_type == GenerationType.NEW.value:
            user.generations_used_this_month += 1
        else:
            user.revisions_used_this_month += 1
        
        db.commit()
        db.refresh(generation)
        
        return generation
    
    def update_generation_progress(
        self,
        db: Session,
        generation_id: str,
        status: GenerationStatus,
        progress: int,
        error_message: str = None
    ):
        """Update generation status and progress"""
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if generation:
            generation.status = status
            generation.progress = progress
            if error_message:
                generation.error_message = error_message
            db.commit()
    
    def assemble_html(
        self,
        template_html: str,
        generated_copy: Dict[str, Any],
        images: list
    ) -> str:
        """Assemble final HTML from template and generated content"""
        
        html = template_html
        
        # Replace copy variables
        for key, value in generated_copy.items():
            placeholder = "{{" + key.upper() + "}}"
            html = html.replace(placeholder, str(value))
        
        # Replace image URLs
        for img in images:
            placeholder = "{{IMAGE_" + img["id"].upper() + "}}"
            if img["status"] == "success" and img.get("r2_url"):
                html = html.replace(placeholder, img["r2_url"])
            else:
                # Use placeholder image
                html = html.replace(placeholder, "/placeholder.png")
        
        return html
    
    def complete_generation(
        self,
        db: Session,
        generation_id: str,
        generated_copy: Dict[str, Any],
        images: list,
        html_content: str,
        llm_cost: float = 0.0,
        image_cost: float = 0.0
    ):
        """Mark generation as complete and update project"""
        
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return
        
        generation.generated_copy = generated_copy
        generation.images = images
        generation.status = GenerationStatus.COMPLETE
        generation.progress = 100
        generation.completed_at = datetime.utcnow()
        generation.llm_cost = llm_cost
        generation.image_cost = image_cost
        generation.total_cost = llm_cost + image_cost
        
        # Update project
        project = generation.project
        project.template_id = generation.template_id
        project.template_version = generation.template_version
        project.generated_data = generated_copy
        project.html_content = html_content
        project.status = ProjectStatus.GENERATED
        
        db.commit()


# Global service instance
generation_service = GenerationService()
