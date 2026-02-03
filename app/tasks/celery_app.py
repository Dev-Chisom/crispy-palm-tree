"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "signaliq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.data_ingestion", "app.tasks.signal_generation", "app.tasks.scheduled_tasks"],
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
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    worker_prefetch_multiplier=4,  # Limit prefetch to reduce memory usage
    result_expires=3600,  # Expire results after 1 hour to free memory
    beat_schedule={
        # Daily price updates - after US market close (9:30 PM UTC = 4:30 PM EST)
        "update-all-stock-prices-daily": {
            "task": "update_all_stock_prices",
            "schedule": crontab(hour=21, minute=30),  # 9:30 PM UTC daily
        },
        # Weekly fundamentals update - Sunday at midnight UTC
        "update-all-fundamentals-weekly": {
            "task": "update_all_fundamentals",
            "schedule": crontab(hour=0, minute=0, day_of_week=0),  # Sunday midnight
        },
        # Hourly indicator recalculation
        "recalculate-all-indicators-hourly": {
            "task": "recalculate_all_indicators",
            "schedule": crontab(minute=0),  # Every hour at :00
        },
    },
)
