#!/usr/bin/env python3
"""Add asset_type column to stocks table directly."""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_asset_type_column():
    """Add asset_type column to stocks table."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("🔄 Connecting to database...")
    engine = create_engine(database_url)
    
    with engine.begin() as conn:  # Use begin() for transaction
        print("📊 Adding asset_type column...")
        
        # Create enum type if it doesn't exist
        print("   Creating assettype enum...")
        conn.execute(text("""
            DO $$ 
            BEGIN 
                CREATE TYPE assettype AS ENUM ('STOCK', 'ETF', 'MUTUAL_FUND');
            EXCEPTION 
                WHEN duplicate_object THEN 
                    NULL;
            END $$;
        """))
        
        # Add asset_type column
        print("   Adding asset_type column to stocks table...")
        conn.execute(text("""
            DO $$ 
            BEGIN 
                ALTER TABLE stocks ADD COLUMN asset_type assettype;
            EXCEPTION 
                WHEN duplicate_column THEN 
                    NULL;
            END $$;
        """))
        
        # Set default value for existing rows
        print("   Setting default value for existing stocks...")
        conn.execute(text("""
            UPDATE stocks SET asset_type = 'STOCK' WHERE asset_type IS NULL;
        """))
        
        # Create index
        print("   Creating index on asset_type...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_stocks_asset_type ON stocks(asset_type);
        """))
        
        # Verify migration
        print("✅ Verifying migration...")
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'asset_type';
        """))
        
        if result.fetchone():
            print("✅ Migration successful! asset_type column exists.")
        else:
            print("❌ WARNING: asset_type column not found after migration")
            sys.exit(1)
        
        print("✅ All done! asset_type column added successfully.")

if __name__ == "__main__":
    add_asset_type_column()
