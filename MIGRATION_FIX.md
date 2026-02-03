# 🚨 PRODUCTION DATABASE MIGRATION FIX

## Problem
The `stocks.stock_type` column doesn't exist in production, causing 500 errors:
```
psycopg2.errors.UndefinedColumn: column stocks.stock_type does not exist
```

## Solution: Run Alembic Migration

The migration file `7f785400ecea_add_stock_type_and_dividend_fields.py` needs to be applied to production.

---

## Option 1: Railway CLI (Recommended)

### Step 1: Install Railway CLI
```bash
npm i -g @railway/cli
```

### Step 2: Login to Railway
```bash
railway login
```

### Step 3: Link to Your Project
```bash
railway link
```
Select your project when prompted.

### Step 4: Run Migration
```bash
railway run alembic upgrade head
```

This will:
- Connect to your Railway PostgreSQL database
- Run all pending migrations
- Add the `stock_type` column to `stocks` table
- Add `dividend_yield`, `dividend_per_share`, `dividend_payout_ratio` to `fundamentals` table

---

## Option 2: Railway One-Off Service

### Step 1: Create Temporary Service
1. Go to Railway dashboard
2. Click **+ New** → **Empty Service**
3. Name it: `migration-runner`

### Step 2: Configure Service
1. **Source**: Connect to your GitHub repo (same as main service)
2. **Start Command**: `alembic upgrade head`
3. **Environment Variables**: Copy all from your main web service:
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
   - (All other env vars)

### Step 3: Deploy and Wait
1. Click **Deploy**
2. Watch logs - should see:
   ```
   INFO  [alembic.runtime.migration] Running upgrade  -> 7f785400ecea, add_stock_type_and_dividend_fields
   ```
3. Wait for completion (usually < 30 seconds)

### Step 4: Delete Service
Once migration completes, delete the temporary service.

---

## Option 3: Direct Database Connection (Advanced)

If you have direct database access:

```bash
# Connect to Railway PostgreSQL
psql $DATABASE_URL

# Then run:
\dt  # List tables to verify connection

# Exit psql, then run migration:
alembic upgrade head
```

---

## Verification

After running migration, verify it worked:

### Check via Railway CLI:
```bash
railway run python -c "
from app.database import SessionLocal
from app.models.stock import Stock
db = SessionLocal()
stock = db.query(Stock).first()
print(f'Stock type column exists: {hasattr(stock, \"stock_type\")}')
print(f'Stock type value: {stock.stock_type}')
db.close()
"
```

### Check via API:
```bash
curl https://your-app.up.railway.app/api/v1/markets/US/stocks
```

Should return 200 OK (not 500 error).

---

## What the Migration Does

1. **Creates `stocktype` enum**: `GROWTH`, `DIVIDEND`, `HYBRID`
2. **Adds `stock_type` column** to `stocks` table (nullable)
3. **Adds dividend columns** to `fundamentals` table:
   - `dividend_yield`
   - `dividend_per_share`
   - `dividend_payout_ratio`
4. **Creates index** on `stocks.stock_type`

---

## Rollback (If Needed)

If something goes wrong, you can rollback:

```bash
railway run alembic downgrade -1
```

This will remove the columns (but keep existing data safe).

---

## Quick Fix Script

I've created `scripts/run_migrations_railway.sh` that you can use:

```bash
railway run bash scripts/run_migrations_railway.sh
```

---

## After Migration

Once migration completes:
1. ✅ API endpoints should work (no more 500 errors)
2. ✅ `stock_type` will be `NULL` for existing stocks (this is OK)
3. ✅ New stocks can have `stock_type` set
4. ✅ Stock classifier will populate `stock_type` when fundamentals are updated

---

## Need Help?

If migration fails:
1. Check Railway logs for error messages
2. Verify `DATABASE_URL` is correct
3. Ensure PostgreSQL service is running
4. Check database connection permissions
