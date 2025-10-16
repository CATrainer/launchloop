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
        logger.error("Generation task timeout", extra={"generation_id": generation_id})
        generation_service.update_generation_progress(
            db,
            generation_id,
            GenerationStatus.FAILED,
            0,
            error_message="Generation timed out. Please try again."
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
            # Retry with exponential backoff
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info("Retrying generation", extra={
                "generation_id": generation_id,
                "retry_in_seconds": retry_delay,
                "attempt": self.request.retries + 2
            })
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Permanent failure or max retries reached
            generation_service.update_generation_progress(
                db,
                generation_id,
                GenerationStatus.FAILED,
                0,
                error_message=error_str
            )
            # Refund user credit
            _refund_user_credit(db, generation_id)
            raise


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
