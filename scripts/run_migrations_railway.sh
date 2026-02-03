#!/bin/bash
# Script to run Alembic migrations on Railway
# Usage: railway run bash scripts/run_migrations_railway.sh

set -e

echo "═══════════════════════════════════════════════════════"
echo "🔄 Running Database Migrations on Railway"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "   Make sure you're running this in Railway with DATABASE_URL configured"
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo ""

# Check current migration status
echo "📊 Checking current migration status..."
alembic current

echo ""
echo "🔄 Running migrations..."
alembic upgrade head

echo ""
echo "✅ Migrations completed successfully!"
echo ""
echo "📊 Verifying migration..."
alembic current

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Migration Complete!"
echo "═══════════════════════════════════════════════════════"
