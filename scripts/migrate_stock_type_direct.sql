-- Direct SQL migration for stock_type and dividend fields
-- Run this in Railway PostgreSQL Query interface if Alembic fails

-- Step 1: Create enum type if it doesn't exist
DO $$ 
BEGIN 
    CREATE TYPE stocktype AS ENUM ('GROWTH', 'DIVIDEND', 'HYBRID', 'UNKNOWN');
EXCEPTION 
    WHEN duplicate_object THEN 
        NULL;
END $$;

-- Step 2: Add stock_type column to stocks table (if it doesn't exist)
DO $$ 
BEGIN 
    ALTER TABLE stocks ADD COLUMN stock_type stocktype;
EXCEPTION 
    WHEN duplicate_column THEN 
        NULL;
END $$;

-- Step 3: Create index on stock_type (if it doesn't exist)
CREATE INDEX IF NOT EXISTS ix_stocks_stock_type ON stocks(stock_type);

-- Step 4: Add dividend columns to fundamentals table (if they don't exist)
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

-- Step 5: Set default value for existing stocks (optional)
UPDATE stocks SET stock_type = 'UNKNOWN' WHERE stock_type IS NULL;

-- Verify migration
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'stocks' AND column_name = 'stock_type';

SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'fundamentals' AND column_name IN ('dividend_yield', 'dividend_per_share', 'dividend_payout_ratio');
