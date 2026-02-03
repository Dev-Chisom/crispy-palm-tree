#!/usr/bin/env python3
"""Script to fetch sample stock data for testing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.stock import Stock, Market
from app.tasks.data_ingestion import fetch_stock_prices, update_fundamentals, calculate_indicators
from app.services.data_fetcher import DataFetcher


def add_sample_stock(symbol: str, name: str, market: Market, sector: str = None):
    """Add a sample stock to the database."""
    db = SessionLocal()
    try:
        # Check if stock exists
        existing = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if existing:
            print(f"✅ Stock {symbol} already exists")
            return existing

        # Fetch stock info from API
        if market == Market.US:
            info = DataFetcher.fetch_us_stock_info(symbol)
            if info:
                name = info.get("name", name)
                sector = info.get("sector", sector)

        # Create stock
        stock = Stock(
            symbol=symbol.upper(),
            name=name,
            market=market,
            sector=sector,
            currency="USD" if market == Market.US else "NGN",
            is_active=True
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
        print(f"✅ Added stock: {stock.symbol} - {stock.name}")
        return stock
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding stock {symbol}: {e}")
        return None
    finally:
        db.close()


def fetch_data_for_stock(symbol: str):
    """Fetch all data for a stock."""
    db = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            print(f"❌ Stock {symbol} not found. Add it first.")
            return

        print(f"\n📊 Fetching data for {symbol}...")

        # Fetch prices
        print("  📈 Fetching prices...")
        result = fetch_stock_prices.delay(symbol, stock.market.value)
        print(f"     Task ID: {result.id}")
        print(f"     Status: {result.status}")

        # Fetch fundamentals
        print("  💰 Fetching fundamentals...")
        result = update_fundamentals.delay(symbol)
        print(f"     Task ID: {result.id}")

        # Calculate indicators
        print("  📊 Calculating indicators...")
        result = calculate_indicators.delay(symbol)
        print(f"     Task ID: {result.id}")

        print(f"\n✅ Data fetching tasks queued for {symbol}")
        print("   Check Celery worker logs for progress")

    finally:
        db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch sample stock data")
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol")
    parser.add_argument("--name", type=str, help="Stock name (auto-fetched for US stocks)")
    parser.add_argument("--market", choices=["US", "NGX"], default="US", help="Market")
    parser.add_argument("--sector", type=str, help="Stock sector")
    parser.add_argument("--add-only", action="store_true", help="Only add stock, don't fetch data")

    args = parser.parse_args()

    market = Market.US if args.market == "US" else Market.NGX

    # Add stock
    stock = add_sample_stock(args.symbol, args.name or args.symbol, market, args.sector)
    if not stock:
        return

    # Fetch data (unless --add-only)
    if not args.add_only:
        fetch_data_for_stock(args.symbol)


if __name__ == "__main__":
    main()
