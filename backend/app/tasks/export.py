from app.tasks import celery_app
from app.database import SessionLocal


@celery_app.task
def process_export(export_id: str):
    """
    Process an export request
    This will be fully implemented in later phases
    """
    with SessionLocal() as db:
        # TODO: Implement export logic
        # 1. Get project HTML
        # 2. Package as ZIP with assets
        # 3. Upload to R2
        # 4. Update export record
        pass
