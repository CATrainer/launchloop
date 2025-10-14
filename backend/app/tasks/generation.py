from celery import Task
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.generation import GenerationStatus
from app.services.generation import generation_service
from app.services.templates import template_registry
from app.services.llm import llm_service
from app.services.images import image_service
from app.services.storage import storage_service
import time


class GenerationTask(Task):
    """Base task with database session"""
    
    def __call__(self, *args, **kwargs):
        with SessionLocal() as db:
            kwargs['db'] = db
            return self.run(*args, **kwargs)


@celery_app.task(base=GenerationTask, bind=True)
def process_generation(self, generation_id: str, db=None):
    """
    Process a generation request
    This is the main orchestrator task
    """
    
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
        
        # Generate copy with LLM
        generated_copy = llm_service.generate_copy(
            template_config,
            generation.input_data
        )
        
        # Update status: generating images
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.GENERATING_IMAGES, 40
        )
        
        # Generate images
        image_specs = template_config.get('image_specs', [])
        images = image_service.generate_images(
            image_specs,
            generation.input_data,
            generated_copy
        )
        
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
                except Exception as e:
                    img['status'] = 'failed'
                    img['error'] = str(e)
            
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
        generation_service.complete_generation(
            db,
            generation_id,
            generated_copy,
            images,
            html_content,
            llm_cost=0.20,  # Estimated
            image_cost=0.30  # Estimated ($0.04 per image × 4, plus buffer)
        )
        
        return {
            "status": "success",
            "generation_id": generation_id
        }
    
    except Exception as e:
        # Mark as failed
        generation_service.update_generation_progress(
            db,
            generation_id,
            GenerationStatus.FAILED,
            0,
            error_message=str(e)
        )
        
        raise
