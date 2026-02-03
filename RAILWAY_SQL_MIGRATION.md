# 🚀 Railway SQL Migration - Direct Database Fix

## Problem
The `stocks.stock_type` column doesn't exist, causing 500 errors. Alembic migration hasn't run.

## ✅ EASIEST FIX: Run SQL Directly in Railway

### Step 1: Access Railway Database
1. Go to [Railway Dashboard](https://railway.app)
2. Select project: **chic-imagination**
3. Select service: **Postgres-H2e5** (your PostgreSQL service)
4. Click **"Query"** tab (or **"Data"** → **"Query"**)

### Step 2: Run SQL Migration
Copy and paste this SQL into the query editor:

```sql
-- Create enum type
DO $$ 
BEGIN 
    CREATE TYPE stocktype AS ENUM ('GROWTH', 'DIVIDEND', 'HYBRID', 'UNKNOWN');
EXCEPTION 
    WHEN duplicate_object THEN 
        NULL;
END $$;

-- Add stock_type column
DO $$ 
BEGIN 
    ALTER TABLE stocks ADD COLUMN stock_type stocktype;
EXCEPTION 
    WHEN duplicate_column THEN 
        NULL;
END $$;

-- Create index
CREATE INDEX IF NOT EXISTS ix_stocks_stock_type ON stocks(stock_type);

-- Add dividend columns
DO $$ 
BEGIN 
    ALTER TABLE fundamentals ADD COLUMN dividend_yield FLOAT;
EXCEPTION 
    WHEN duplicate_column THEN 
        NULL;
END $$;

DO $$ 
BEGIN 
    ALTER TABLE fundamentals ADD COLUMN dividend_per_share FLOAT;
EXCEPTION 
    WHEN duplicate_column THEN 
        NULL;
END $$;

DO $$ 
BEGIN 
    ALTER TABLE fundamentals ADD COLUMN dividend_payout_ratio FLOAT;
EXCEPTION 
    WHEN duplicate_column THEN 
        NULL;
END $$;
```

### Step 3: Click "Run" or "Execute"

### Step 4: Verify
Run this to verify columns exist:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'stocks' AND column_name = 'stock_type';
```

Should return: `stock_type`

---

## Alternative: Use Full SQL Script

The complete SQL script is in: `scripts/migrate_stock_type_direct.sql`

Copy the entire file content and run it in Railway's Query interface.

---

## After Migration

1. ✅ API endpoints will work (no more 500 errors)
2. ✅ Existing stocks will have `stock_type = NULL` (this is OK)
3. ✅ New stocks can have `stock_type` set
4. ✅ Stock classifier will populate `stock_type` automatically

---

## Why This Works

- Runs directly in PostgreSQL (no Alembic needed)
- Uses `DO $$` blocks to handle errors gracefully
- Safe to run multiple times (won't fail if columns exist)
- No CLI connection issues

---

## Quick Copy-Paste SQL

```sql
DO $$ BEGIN CREATE TYPE stocktype AS ENUM ('GROWTH', 'DIVIDEND', 'HYBRID', 'UNKNOWN'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE stocks ADD COLUMN stock_type stocktype; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS ix_stocks_stock_type ON stocks(stock_type);
DO $$ BEGIN ALTER TABLE fundamentals ADD COLUMN dividend_yield FLOAT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE fundamentals ADD COLUMN dividend_per_share FLOAT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE fundamentals ADD COLUMN dividend_payout_ratio FLOAT; EXCEPTION WHEN duplicate_column THEN NULL; END $$;
```

Just paste this into Railway's Query interface and run!
