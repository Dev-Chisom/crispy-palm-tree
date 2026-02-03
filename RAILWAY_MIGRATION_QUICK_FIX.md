# 🚀 Railway Migration Quick Fix

## Problem
Railway CLI connection error: `BadRecordMac` (TLS/SSL issue)

## ✅ Easiest Solution: Redeploy via Dashboard

Since we updated the `Procfile` to auto-run migrations, just redeploy:

### Steps:
1. Go to [Railway Dashboard](https://railway.app)
2. Select project: **chic-imagination**
3. Select service: **crispy-palm-tree** (your web service)
4. Click **"Redeploy"** button
5. Wait for deployment to complete

The migration will run automatically because `Procfile` now includes:
```
web: alembic upgrade head && uvicorn app.main:app ...
```

---

## Alternative: One-Off Service (If Redeploy Doesn't Work)

### Step 1: Create Temporary Service
1. Railway Dashboard → **+ New** → **Empty Service**
2. Name it: `migration-runner`

### Step 2: Configure Service
1. **Source**: Connect to your GitHub repo (same as main service)
2. **Start Command**: 
   ```
   alembic upgrade head
   ```
3. **Environment Variables**: Copy from `crispy-palm-tree` service:
   ```
   DATABASE_URL=${{Postgres-H2e5.DATABASE_URL}}
   ```
   (Copy all other env vars if needed)

### Step 3: Deploy and Monitor
1. Click **Deploy**
2. Watch logs - you should see:
   ```
   INFO  [alembic.runtime.migration] Running upgrade  -> 7f785400ecea
   ```
3. Wait for completion (usually < 30 seconds)

### Step 4: Clean Up
Once migration completes successfully:
1. Delete the `migration-runner` service
2. Your main service is ready!

---

## Verify Migration Worked

### Check via API:
```bash
curl https://your-app.up.railway.app/api/v1/markets/US/stocks
```

Should return **200 OK** (not 500 error).

### Check via Railway Dashboard:
1. Go to **Postgres-H2e5** service
2. Click **"Query"** tab
3. Run:
   ```sql
   SELECT column_name 
   FROM information_schema.columns 
   WHERE table_name = 'stocks' AND column_name = 'stock_type';
   ```
4. Should return `stock_type` column

---

## If Railway CLI Still Fails

### Fix CLI Connection:
```bash
# Update CLI
npm update -g @railway/cli

# Clear cache and re-login
rm -rf ~/.railway
railway login

# Try again
railway link
railway run alembic upgrade head
```

---

## What the Migration Does

Adds these columns:
- `stocks.stock_type` (GROWTH, DIVIDEND, HYBRID, UNKNOWN)
- `fundamentals.dividend_yield`
- `fundamentals.dividend_per_share`
- `fundamentals.dividend_payout_ratio`

All columns are **nullable**, so existing data is safe.

---

## Need Help?

If migration fails:
1. Check Railway logs for error messages
2. Verify `DATABASE_URL` is correct
3. Ensure PostgreSQL service is running
4. Check database connection permissions
