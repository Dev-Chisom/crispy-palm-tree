#!/bin/bash

# SignalIQ Backend Setup Script

set -e

echo "🚀 Setting up SignalIQ Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing!"
fi

# Check if Docker is running (for docker-compose)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Docker is available. You can start services with: docker-compose up -d"
    read -p "Start PostgreSQL and Redis with Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose up -d
        echo "⏳ Waiting for services to be ready..."
        sleep 5
    fi
fi

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Initialize TimescaleDB hypertable
echo "📊 Initializing TimescaleDB hypertable..."
python scripts/init_timescaledb.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure PostgreSQL and Redis are running"
echo "2. Update .env file with your configuration"
echo "3. Start Celery worker: celery -A app.tasks.celery_app worker --loglevel=info"
echo "4. Start FastAPI server: uvicorn app.main:app --reload"
echo "5. Visit http://localhost:8000/docs for API documentation"
