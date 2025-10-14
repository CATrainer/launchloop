from celery import Celery
from app.config import settings

celery_app = Celery(
    "launch_loop",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.generation', 'app.tasks.export', 'app.tasks.email']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
)
