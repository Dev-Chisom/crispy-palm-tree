"""Script to initialize TimescaleDB hypertable for stock_prices."""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not set in environment")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Enable TimescaleDB extension
        print("Enabling TimescaleDB extension...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
        conn.commit()

        # Check if hypertable already exists
        result = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = 'stock_prices'
                );
                """
            )
        )
        exists = result.scalar()

        if not exists:
            # Create hypertable
            print("Creating hypertable for stock_prices...")
            conn.execute(text("SELECT create_hypertable('stock_prices', 'time');"))
            conn.commit()
            print("✓ Hypertable created successfully!")
        else:
            print("✓ Hypertable already exists")

        print("TimescaleDB initialization complete!")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
