#!/usr/bin/env python3
"""Fetch data directly (without Celery) for testing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.stock import Stock, Market
from app.services.data_fetcher import DataFetcher
from app.models.price import StockPrice
from app.models.fundamental import Fundamental
from app.services.indicator_calculator import IndicatorCalculator
from datetime import datetime, timedelta


def fetch_prices_direct(symbol: str, market: Market):
    """Fetch prices directly."""
    db = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            print(f"❌ Stock {symbol} not found")
            return

        print(f"📈 Fetching prices for {symbol}...")
        
        if market == Market.US:
            prices_df = DataFetcher.fetch_us_stock_prices(symbol, period="1y")
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
            prices_df = DataFetcher.fetch_ngx_stock_prices(symbol, start_date, end_date)

        if prices_df is None or prices_df.empty:
            print(f"❌ No price data fetched for {symbol}")
            return

        count = 0
        for _, row in prices_df.iterrows():
            existing = (
                db.query(StockPrice)
                .filter(
                    StockPrice.stock_id == stock.id,
                    StockPrice.time == row["time"],
                )
                .first()
            )

            if not existing:
                price = StockPrice(
                    stock_id=stock.id,
                    time=row["time"],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
                db.add(price)
                count += 1

        db.commit()
        print(f"✅ Added {count} price records for {symbol}")
        return count
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch data directly (no Celery)")
    parser.add_argument("symbol", type=str, help="Stock symbol")
    parser.add_argument("--market", choices=["US", "NGX"], default="US", help="Market")

    args = parser.parse_args()
    market = Market.US if args.market == "US" else Market.NGX
    
    fetch_prices_direct(args.symbol, market)


if __name__ == "__main__":
    main()
