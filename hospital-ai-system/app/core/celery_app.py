from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "hospital_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery_app.task(name="ping")
def ping():
    """Simple task to verify Celery + Redis connectivity."""
    return "pong"
