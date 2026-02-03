#!/usr/bin/env python3
"""Run database migration directly using SQLAlchemy.

This script can be run as a one-off service in Railway or locally.
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the stock_type migration directly."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("🔄 Connecting to database...")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        print("📊 Running migration...")
        
        # Create enum type if it doesn't exist
        print("   Creating stocktype enum...")
        conn.execute(text("""
            DO $$ 
            BEGIN 
                CREATE TYPE stocktype AS ENUM ('GROWTH', 'DIVIDEND', 'HYBRID', 'UNKNOWN');
            EXCEPTION 
                WHEN duplicate_object THEN 
                    NULL;
            END $$;
        """))
        conn.commit()
        
        # Add stock_type column
        print("   Adding stock_type column to stocks table...")
        conn.execute(text("""
            DO $$ 
            BEGIN 
                ALTER TABLE stocks ADD COLUMN stock_type stocktype;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    NULL;
            END $$;
        """))
        conn.commit()
        
        # Create index
        print("   Creating index on stock_type...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stocks_stock_type ON stocks(stock_type);"))
        conn.commit()
        
        # Add dividend columns to fundamentals
        print("   Adding dividend columns to fundamentals table...")
        conn.execute(text("""
            DO $$ 
            BEGIN 
                ALTER TABLE fundamentals ADD COLUMN dividend_yield FLOAT;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    NULL;
            END $$;
        """))
        conn.commit()
        
        conn.execute(text("""
            DO $$ 
            BEGIN 
                ALTER TABLE fundamentals ADD COLUMN dividend_per_share FLOAT;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    NULL;
            END $$;
        """))
        conn.commit()
        
        conn.execute(text("""
            DO $$ 
            BEGIN 
                ALTER TABLE fundamentals ADD COLUMN dividend_payout_ratio FLOAT;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    NULL;
            END $$;
        """))
        conn.commit()
        
        # Verify migration
        print("✅ Verifying migration...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'stock_type';
        """))
        
        if result.fetchone():
            print("✅ Migration successful! stock_type column exists.")
        else:
            print("❌ WARNING: stock_type column not found after migration")
        
        # Check dividend columns
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fundamentals' 
            AND column_name IN ('dividend_yield', 'dividend_per_share', 'dividend_payout_ratio');
        """))
        
        dividend_cols = [row[0] for row in result.fetchall()]
        if len(dividend_cols) == 3:
            print(f"✅ Migration successful! Dividend columns added: {', '.join(dividend_cols)}")
        else:
            print(f"⚠️  WARNING: Expected 3 dividend columns, found {len(dividend_cols)}")
    
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
