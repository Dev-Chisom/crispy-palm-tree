#!/bin/bash

# Start Celery worker for SignalIQ

cd "$(dirname "$0")/.."

echo "🚀 Starting Celery worker..."
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "   Start Redis: docker start signaliq_redis"
    echo "   Or: redis-server"
    exit 1
fi

echo "✅ Redis is running"
echo ""

# Start Celery worker
python3 -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --time-limit=300 \
    --soft-time-limit=240
