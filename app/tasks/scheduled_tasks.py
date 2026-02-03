"""Scheduled Celery tasks for periodic data updates."""

from celery.schedules import crontab
from app.tasks.celery_app import celery_app
from app.tasks.data_ingestion import fetch_stock_prices, update_fundamentals, calculate_indicators
from app.database import SessionLocal
from app.models.stock import Stock
from datetime import datetime


@celery_app.task(name="update_all_stock_prices")
def update_all_stock_prices():
    """
    Update prices for all active stocks.
    Runs daily after market close (9:30 PM UTC = 4:30 PM EST).
    """
    db = SessionLocal()
    try:
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        results = []
        
        for stock in stocks:
            try:
                result = fetch_stock_prices.delay(stock.symbol, stock.market.value)
                results.append({"symbol": stock.symbol, "task_id": result.id})
            except Exception as e:
                results.append({"symbol": stock.symbol, "error": str(e)})
        
        return {
            "status": "success",
            "stocks_updated": len(stocks),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="update_all_fundamentals")
def update_all_fundamentals():
    """
    Update fundamentals for all active stocks.
    Runs weekly on Sunday at midnight UTC.
    """
    db = SessionLocal()
    try:
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        results = []
        
        for stock in stocks:
            try:
                result = update_fundamentals.delay(stock.symbol)
                results.append({"symbol": stock.symbol, "task_id": result.id})
            except Exception as e:
                results.append({"symbol": stock.symbol, "error": str(e)})
        
        return {
            "status": "success",
            "stocks_updated": len(stocks),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="recalculate_all_indicators")
def recalculate_all_indicators():
    """
    Recalculate technical indicators for all active stocks.
    Runs hourly to keep indicators fresh.
    """
    db = SessionLocal()
    try:
        stocks = db.query(Stock).filter(Stock.is_active == True).all()
        results = []
        
        for stock in stocks:
            try:
                result = calculate_indicators.delay(stock.symbol)
                results.append({"symbol": stock.symbol, "task_id": result.id})
            except Exception as e:
                results.append({"symbol": stock.symbol, "error": str(e)})
        
        return {
            "status": "success",
            "stocks_updated": len(stocks),
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


