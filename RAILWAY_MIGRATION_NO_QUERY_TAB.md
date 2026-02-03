# 🚀 Railway Migration - No Query Tab Available

## Problem
Railway's PostgreSQL service doesn't have a "Query" tab in the Database interface.

## ✅ Solution Options

### Option 1: One-Off Service (Easiest) ⭐ RECOMMENDED

#### Step 1: Create Temporary Service
1. Railway Dashboard → **+ New** → **Empty Service**
2. Name it: `migration-runner`

#### Step 2: Configure Service
1. **Source**: Connect to your GitHub repo (same as main service)
2. **Start Command**: 
   ```
   python scripts/run_migration.py
   ```
3. **Environment Variables**: Copy ALL from `crispy-palm-tree` service:
   ```
   DATABASE_URL=${{Postgres-H2e5.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   CELERY_BROKER_URL=${{Redis.REDIS_URL}}
   CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
   CORS_ORIGINS=...
   (Copy all other env vars)
   ```

#### Step 3: Deploy and Monitor
1. Click **Deploy**
2. Watch logs - you should see:
   ```
   🔄 Connecting to database...
   📊 Running migration...
      Creating stocktype enum...
      Adding stock_type column to stocks table...
      Creating index on stock_type...
      Adding dividend columns to fundamentals table...
   ✅ Migration successful! stock_type column exists.
   ✅ Migration complete!
   ```
3. Wait for completion (usually < 1 minute)

#### Step 4: Clean Up
Once migration completes successfully:
1. Delete the `migration-runner` service
2. Your main service is ready!

---

### Option 2: Use Railway CLI (If Fixed)

If you fix the CLI connection issue:

```bash
# Update CLI
npm update -g @railway/cli

# Clear cache
rm -rf ~/.railway

# Re-login
railway login

# Link and run
railway link
railway run python scripts/run_migration.py
```

---

### Option 3: Use psql Locally

If you have the `DATABASE_URL`:

```bash
# Extract connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database

# Connect via psql
psql $DATABASE_URL

# Then run SQL from scripts/migrate_stock_type_direct.sql
```

Or run the Python script locally:
```bash
export DATABASE_URL="your-railway-database-url"
python scripts/run_migration.py
```

---

### Option 4: Wait for Auto-Migration on Deploy

Since `Procfile` is updated with:
```
web: alembic upgrade head && uvicorn app.main:app ...
```

The next deploy will automatically run migrations. Just:
1. Wait for current build to complete
2. Or trigger a redeploy
3. Migrations will run automatically

---

## ✅ Recommended: Option 1 (One-Off Service)

This is the easiest and most reliable method:

1. **Create service** → `migration-runner`
2. **Start command** → `python scripts/run_migration.py`
3. **Copy env vars** → From `crispy-palm-tree`
4. **Deploy** → Watch logs
5. **Delete service** → After success

Takes ~2 minutes total!

---

## Verify Migration Worked

After migration, test the API:
```bash
curl https://your-app.up.railway.app/api/v1/markets/US/stocks
```

Should return **200 OK** (not 500 error).

---

## What the Migration Does

1. Creates `stocktype` enum (GROWTH, DIVIDEND, HYBRID, UNKNOWN)
2. Adds `stock_type` column to `stocks` table
3. Adds `dividend_yield`, `dividend_per_share`, `dividend_payout_ratio` to `fundamentals` table
4. Creates index on `stock_type`

All columns are **nullable**, so existing data is safe.
