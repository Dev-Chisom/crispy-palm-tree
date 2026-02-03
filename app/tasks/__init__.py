"""Celery tasks for background jobs."""

from app.tasks.celery_app import celery_app
from app.tasks.data_ingestion import (
    fetch_stock_prices,
    update_fundamentals,
    calculate_indicators,
)
from app.tasks.signal_generation import (
    generate_signal,
    batch_signal_generation,
)
from app.tasks.scheduled_tasks import (
    update_all_stock_prices,
    update_all_fundamentals,
    recalculate_all_indicators,
)
from app.tasks.ml_training_tasks import (
    train_lstm_for_stock,
    train_classifier_model_task,
    train_lstm_for_all_stocks,
    retrain_classifier_model,
)

__all__ = [
    "celery_app",
    "fetch_stock_prices",
    "update_fundamentals",
    "calculate_indicators",
    "generate_signal",
    "batch_signal_generation",
    "update_all_stock_prices",
    "update_all_fundamentals",
    "recalculate_all_indicators",
    "train_lstm_for_stock",
    "train_classifier_model_task",
    "train_lstm_for_all_stocks",
    "retrain_classifier_model",
]
