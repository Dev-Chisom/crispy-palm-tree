web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --limit-concurrency 100
worker: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=50
