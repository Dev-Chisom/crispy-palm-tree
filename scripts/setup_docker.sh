#!/bin/bash

# Docker Setup Script for SignalIQ Backend

set -e

echo "🐳 Setting up SignalIQ with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check network connectivity
echo "🔍 Checking network connectivity..."
if ! ping -c 1 docker.io > /dev/null 2>&1; then
    echo "⚠️  Warning: Cannot reach Docker Hub (docker.io)"
    echo "   This may be due to:"
    echo "   - VPN blocking Docker Hub"
    echo "   - Network firewall"
    echo "   - Internet connectivity issues"
    echo ""
    echo "   Trying to pull images anyway..."
    echo ""
fi

# Stop any existing containers
echo "🛑 Stopping existing containers (if any)..."
docker-compose down 2>/dev/null || true

# Pull images
echo "📥 Pulling Docker images..."
echo "   This may take a few minutes on first run..."
echo ""

# Try to pull images with retries
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose pull 2>&1 | tee /tmp/docker_pull.log; then
        echo "✅ Images pulled successfully"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⚠️  Pull failed, retrying ($RETRY_COUNT/$MAX_RETRIES)..."
            sleep 5
        else
            echo "❌ Failed to pull images after $MAX_RETRIES attempts"
            echo ""
            echo "💡 Solutions:"
            echo "   1. Check your internet connection"
            echo "   2. Disable VPN temporarily"
            echo "   3. Check Docker Desktop network settings"
            echo "   4. Try using local PostgreSQL instead"
            exit 1
        fi
    fi
done

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
MAX_WAIT=30
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if docker exec signaliq_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    else
        WAIT_COUNT=$((WAIT_COUNT + 1))
        if [ $WAIT_COUNT -lt $MAX_WAIT ]; then
            echo "   Waiting... ($WAIT_COUNT/$MAX_WAIT)"
            sleep 1
        else
            echo "⚠️  PostgreSQL is taking longer than expected"
        fi
    fi
done

# Check Redis
echo "🔍 Checking Redis..."
if docker exec signaliq_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis may still be starting"
fi

# Create database and run migrations
echo ""
echo "📊 Setting up database..."
echo "   Creating database (if needed)..."
docker exec signaliq_postgres psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='signaliq_db'" | grep -q 1 || \
    docker exec signaliq_postgres psql -U postgres -c "CREATE DATABASE signaliq_db;" || true

echo "   Running migrations..."
cd /Users/chisomgenevieveonwugbenu/Desktop/stock-backend
alembic upgrade head || echo "⚠️  Migrations may need to be run manually"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Docker setup complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 Services Status:"
docker-compose ps
echo ""
echo "🔗 Connection Info:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo "   Database: signaliq_db"
echo "   User: postgres"
echo "   Password: postgres"
echo ""
echo "📝 Next steps:"
echo "   1. Run migrations: alembic upgrade head"
echo "   2. Initialize TimescaleDB: python scripts/init_timescaledb.py"
echo "   3. Start server: python3 -m uvicorn app.main:app --reload"
echo ""
