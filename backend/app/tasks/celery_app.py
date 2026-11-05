import os
from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "retinax_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    broker_connection_retry_on_startup=True
)

celery_app.autodiscover_tasks(["backend.app.tasks"])
