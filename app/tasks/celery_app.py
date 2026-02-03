"""Celery application configuration."""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "signaliq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.data_ingestion", "app.tasks.signal_generation"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)
