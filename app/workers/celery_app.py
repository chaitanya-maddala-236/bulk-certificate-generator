from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bulk_certificate_generator",
    broker=settings.redis_url,
    backend=None,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=False,
    task_ignore_result=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)
