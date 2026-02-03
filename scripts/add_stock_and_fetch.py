#!/usr/bin/env python3
"""Add a stock and trigger Celery tasks to fetch real data."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.stock import Stock, Market
from app.tasks.data_ingestion import fetch_stock_prices, update_fundamentals, calculate_indicators
from app.services.data_fetcher import DataFetcher


def add_stock(symbol: str, name: str, market: Market, sector: str = None):
    """Add a stock to the database."""
    db = SessionLocal()
    try:
        # Check if stock exists
        existing = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if existing:
            print(f"✅ Stock {symbol} already exists")
            return existing

        # Fetch stock info from API for US stocks
        if market == Market.US:
            print(f"📡 Fetching info for {symbol}...")
            info = DataFetcher.fetch_us_stock_info(symbol)
            if info:
                name = info.get("name", name)
                sector = info.get("sector", sector)
                print(f"   Found: {name} ({sector})")

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


def trigger_data_fetch(symbol: str, market: Market):
    """Trigger Celery tasks to fetch data for a stock."""
    print(f"\n📊 Triggering data fetch for {symbol}...")
    
    # Trigger price fetch
    print("  📈 Queuing price fetch task...")
    price_task = fetch_stock_prices.delay(symbol, market.value)
    print(f"     Task ID: {price_task.id}")
    
    # Trigger fundamentals fetch
    print("  💰 Queuing fundamentals fetch task...")
    fund_task = update_fundamentals.delay(symbol)
    print(f"     Task ID: {fund_task.id}")
    
    # Trigger indicators calculation
    print("  📊 Queuing indicators calculation task...")
    ind_task = calculate_indicators.delay(symbol)
    print(f"     Task ID: {ind_task.id}")
    
    print(f"\n✅ All tasks queued for {symbol}")
    print("   Check Celery worker logs for progress")
    print(f"   Price Task: {price_task.id}")
    print(f"   Fundamentals Task: {fund_task.id}")
    print(f"   Indicators Task: {ind_task.id}")
    
    return price_task, fund_task, ind_task


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Add stock and fetch real data via Celery")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL, GTCO)")
    parser.add_argument("--name", type=str, help="Stock name (auto-fetched for US stocks)")
    parser.add_argument("--market", choices=["US", "NGX"], default="US", help="Market")
    parser.add_argument("--sector", type=str, help="Stock sector")
    parser.add_argument("--add-only", action="store_true", help="Only add stock, don't fetch data")

    args = parser.parse_args()

    market = Market.US if args.market == "US" else Market.NGX

    # Add stock
    stock = add_stock(args.symbol, args.name or args.symbol, market, args.sector)
    if not stock:
        print("❌ Failed to add stock")
        return 1

    # Trigger data fetch (unless --add-only)
    if not args.add_only:
        trigger_data_fetch(args.symbol, market)
        print("\n💡 Make sure Celery worker is running:")
        print("   python3 -m celery -A app.tasks.celery_app worker --loglevel=info")
    else:
        print("\n💡 To fetch data, run:")
        print(f"   python3 scripts/add_stock_and_fetch.py {args.symbol} --market {args.market}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
