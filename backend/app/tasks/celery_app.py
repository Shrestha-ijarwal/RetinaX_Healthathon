import os
import logging
from backend.app.core.config import settings

logger = logging.getLogger("retinax.celery")

try:
    from celery import Celery

    celery_app = Celery(
        "retinax_care",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["backend.app.tasks.reminder_tasks"]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,
        task_track_started=True,
    )
except ImportError:
    logger.warning("Celery is not installed in the current environment; running in fallback simulation mode.")
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(f):
                def delay_wrapper(*a, **kw):
                    return f(*a, **kw)
                f.delay = delay_wrapper
                return f
            return decorator
    celery_app = DummyCelery()
