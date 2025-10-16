from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.generation import GenerationStatus, Generation, GenerationType
from app.services.generation import generation_service
from app.services.templates import template_registry
from app.services.llm import llm_service
from app.services.images import image_service
from app.services.storage import storage_service
from app.utils.logger import get_logger
import time

logger = get_logger(__name__)


class GenerationTask(Task):
    """Base task with database session"""
    
    def __call__(self, *args, **kwargs):
        with SessionLocal() as db:
            kwargs['db'] = db
            return self.run(*args, **kwargs)


@celery_app.task(
    base=GenerationTask,
    bind=True,
    time_limit=600,  # 10 minutes hard limit
    soft_time_limit=540,  # 9 minutes soft limit
    max_retries=3,
    default_retry_delay=60
)
def process_generation(self, generation_id: str, db=None):
    """
    Process a generation request
    This is the main orchestrator task
    
    Time limit: 10 minutes (600s) hard, 9 minutes (540s) soft
    Retries: Up to 3 times on transient failures
    """
    
    logger.info("Generation task started", extra={
        "generation_id": generation_id,
        "attempt": self.request.retries + 1
    })
    
    try:
        # Update status: analyzing
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.ANALYZING, 10
        )
        time.sleep(0.5)  # Small delay for UI feedback
        
        # Load generation
        from app.models.generation import Generation
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            raise Exception("Generation not found")
        
        # Get template
        template = template_registry.get_template(generation.template_id)
        if not template:
            raise Exception(f"Template {generation.template_id} not found")
        
        template_config = template['config']
        
        # Update status: generating copy
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.GENERATING_COPY, 20
        )
        
        # Generate copy with LLM (returns tuple with cost)
        generated_copy, llm_cost = llm_service.generate_copy(
            template_config,
            generation.input_data
        )
        
        logger.info("Copy generation complete", extra={
            "generation_id": generation_id,
            "llm_cost": round(llm_cost, 4)
        })
        
        # Update status: generating images
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.GENERATING_IMAGES, 40
        )
        
        # Generate images
        image_specs = template_config.get('image_specs', [])
        images, image_cost = image_service.generate_images(
            image_specs,
            generation.input_data,
            generated_copy
        )
        
        logger.info("Image generation complete", extra={
            "generation_id": generation_id,
            "image_count": len(images),
            "image_cost": round(image_cost, 4)
        })
        
        # Upload images to R2 and update progress
        for i, img in enumerate(images):
            if img['status'] == 'success' and img.get('url'):
                try:
                    # Download from DALL-E temp URL
                    image_data = image_service.download_image(img['url'])
                    
                    # Upload to R2
                    r2_url = storage_service.upload_image(
                        image_data,
                        filename=f"projects/{generation.project_id}/{img['id']}.png"
                    )
                    
                    img['r2_url'] = r2_url
                    logger.debug("Image uploaded to R2", extra={
                        "image_id": img['id'],
                        "generation_id": generation_id
                    })
                except Exception as e:
                    img['status'] = 'failed'
                    img['error'] = str(e)
                    logger.error("Image upload failed", extra={
                        "image_id": img['id'],
                        "generation_id": generation_id,
                        "error": str(e)
                    })
            
            # Update progress (40 -> 60 range, split by number of images)
            progress = 40 + int((i + 1) / len(images) * 20)
            generation_service.update_generation_progress(
                db, generation_id, GenerationStatus.GENERATING_IMAGES, progress
            )
        
        # Update status: assembling
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.ASSEMBLING, 85
        )
        
        # Get template HTML
        template_html = template_registry.get_template_html(generation.template_id)
        if not template_html:
            raise Exception("Template HTML not found")
        
        # Assemble final HTML
        html_content = generation_service.assemble_html(
            template_html,
            generated_copy,
            images
        )
        
        # Complete generation
        total_cost = llm_cost + image_cost
        generation_service.complete_generation(
            db,
            generation_id,
            generated_copy,
            images,
            html_content,
            llm_cost=llm_cost,
            image_cost=image_cost
        )
        
        logger.info("Generation completed successfully", extra={
            "generation_id": generation_id,
            "total_cost": round(total_cost, 4),
            "llm_cost": round(llm_cost, 4),
            "image_cost": round(image_cost, 4)
        })
        
        return {
            "status": "success",
            "generation_id": generation_id
        }
    
    except SoftTimeLimitExceeded:
        # Task taking too long - mark as failed
        # Get current progress to keep where it was
        current_generation = db.query(Generation).filter(Generation.id == generation_id).first()
        current_progress = current_generation.progress if current_generation else 0
        
        logger.error("Generation task timeout", extra={
            "generation_id": generation_id,
            "progress_at_timeout": current_progress
        })
        
        generation_service.update_generation_progress(
            db,
            generation_id,
            GenerationStatus.FAILED,
            current_progress,  # Keep progress where it timed out
            error_message="Generation took longer than expected and timed out. This can happen during high AI service demand. Your credit has been refunded. Please try again."
        )
        # Refund user credit
        _refund_user_credit(db, generation_id)
        raise
    
    except Exception as e:
        error_str = str(e)
        logger.error("Generation task failed", extra={
            "generation_id": generation_id,
            "error": error_str,
            "attempt": self.request.retries + 1
        }, exc_info=True)
        
        # Get current progress before deciding what to do
        current_generation = db.query(Generation).filter(Generation.id == generation_id).first()
        current_progress = current_generation.progress if current_generation else 0
        
        # Check if error is retryable
        retryable_errors = [
            "rate_limit",
            "timeout",
            "connection",
            "temporary",
            "503",
            "429",
            "overloaded"
        ]
        
        is_retryable = any(keyword in error_str.lower() for keyword in retryable_errors)
        
        if is_retryable and self.request.retries < self.max_retries:
            # Retry with exponential backoff - but DON'T reset progress
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            
            # Keep progress where it was, just update status to show retrying
            generation_service.update_generation_progress(
                db,
                generation_id,
                GenerationStatus.GENERATING_COPY,  # Keep in progress state
                current_progress,  # DON'T reset to 0
                error_message=f"Retrying due to {error_str[:100]}... (attempt {self.request.retries + 2}/{self.max_retries + 1})"
            )
            
            logger.info("Retrying generation", extra={
                "generation_id": generation_id,
                "retry_in_seconds": retry_delay,
                "attempt": self.request.retries + 2,
                "progress_kept_at": current_progress
            })
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Permanent failure or max retries reached
            # Keep progress where it failed, don't reset to 0
            user_friendly_error = _make_error_user_friendly(error_str)
            generation_service.update_generation_progress(
                db,
                generation_id,
                GenerationStatus.FAILED,
                current_progress,  # Keep at failure point, not 0
                error_message=user_friendly_error
            )
            # Refund user credit
            _refund_user_credit(db, generation_id)
            raise


def _make_error_user_friendly(error_str: str) -> str:
    """Convert technical error messages to user-friendly ones"""
    error_lower = error_str.lower()
    
    # Map technical errors to user-friendly messages
    if "rate" in error_lower and "limit" in error_lower:
        return "We're hitting API rate limits. This usually resolves in a few minutes. Please try again shortly."
    
    if "timeout" in error_lower or "timed out" in error_lower:
        return "The generation took too long and timed out. This can happen during high demand. Please try again."
    
    if "json" in error_lower and ("parse" in error_lower or "decode" in error_lower):
        return "There was an issue processing the AI response. Please try generating again."
    
    if "connection" in error_lower or "network" in error_lower:
        return "We're having trouble connecting to our AI services. Please check your internet connection and try again."
    
    if "overloaded" in error_lower or "503" in error_str or "502" in error_str:
        return "Our AI services are temporarily overloaded. Please wait a moment and try again."
    
    if "401" in error_str or "unauthorized" in error_lower:
        return "Authentication error. Please log out and log back in."
    
    if "404" in error_str or "not found" in error_lower:
        return "Required resource not found. Please contact support if this persists."
    
    # If no match, return a generic but helpful message
    return f"Generation failed due to a technical issue. Please try again. If this persists, contact support with this error: {error_str[:100]}"


def _refund_user_credit(db, generation_id: str):
    """Refund user credit when generation fails"""
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            return
        
        user = generation.project.user
        if generation.type == GenerationType.NEW:
            user.generations_used_this_month = max(0, user.generations_used_this_month - 1)
            logger.info("Refunded generation credit", extra={
                "user_id": user.id,
                "generation_id": generation_id
            })
        else:
            user.revisions_used_this_month = max(0, user.revisions_used_this_month - 1)
            logger.info("Refunded revision credit", extra={
                "user_id": user.id,
                "generation_id": generation_id
            })
        db.commit()
    except Exception as e:
        logger.error("Failed to refund credit", extra={
            "generation_id": generation_id,
            "error": str(e)
        })
