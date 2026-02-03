#!/bin/bash

# SignalIQ Backend Server Startup Script

set -e

echo "🚀 Starting SignalIQ Backend Server..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please create .env file with the following variables:"
    echo ""
    cat << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/signaliq_db
TIMESCALEDB_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173
YFINANCE_ENABLED=true
ENVIRONMENT=development
DEBUG=true
EOF
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Check PostgreSQL connection
echo "🔍 Checking PostgreSQL connection..."
if ! python -c "
from app.config import settings
from sqlalchemy import create_engine, text
try:
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ PostgreSQL connection: OK')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('💡 Make sure PostgreSQL is running and DATABASE_URL is correct')
    exit(1)
" 2>&1; then
    echo ""
    echo "⚠️  PostgreSQL check failed. Continuing anyway..."
fi

# Check Redis connection
echo "🔍 Checking Redis connection..."
if ! python -c "
from app.config import settings
import redis
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print('✅ Redis connection: OK')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('💡 Make sure Redis is running and REDIS_URL is correct')
    exit(1)
" 2>&1; then
    echo ""
    echo "⚠️  Redis check failed. Continuing anyway..."
fi

echo ""
echo "✅ Starting FastAPI server..."
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
