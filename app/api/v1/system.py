"""System health and diagnostic API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any, Optional
from app.database import get_db
from app.models.stock import Stock
from app.schemas.common import SuccessResponse, Meta
from app.config import settings
from app.services.cache import cache_service

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/system/status", response_model=SuccessResponse)
def get_system_status(db: Session = Depends(get_db)):
    """
    Get system status including database, cache, and background jobs.
    """
    status: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {},
        "cache": {},
        "stocks": {},
        "background_jobs": {},
    }
    
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        status["database"]["connected"] = True
        status["database"]["error"] = None
    except Exception as e:
        status["database"]["connected"] = False
        status["database"]["error"] = str(e)
    
    # Check cache (Redis)
    try:
        test_key = "health_check_test"
        cache_service.set(test_key, "test", 10)
        cached = cache_service.get(test_key)
        cache_service.delete(test_key)
        status["cache"]["connected"] = cached == "test"
        status["cache"]["error"] = None
    except Exception as e:
        status["cache"]["connected"] = False
        status["cache"]["error"] = str(e)
    
    # Check stocks in database
    try:
        total_stocks = db.query(Stock).count()
        active_stocks = db.query(Stock).filter(Stock.is_active == True).count()
        stocks_with_prices = db.query(Stock).join(Stock.prices).distinct().count()
        stocks_with_fundamentals = db.query(Stock).join(Stock.fundamentals).distinct().count()
        
        status["stocks"] = {
            "total": total_stocks,
            "active": active_stocks,
            "with_prices": stocks_with_prices,
            "with_fundamentals": stocks_with_fundamentals,
        }
    except Exception as e:
        status["stocks"]["error"] = str(e)
    
    # Check Celery configuration
    try:
        from app.tasks.celery_app import celery_app
        
        # Try to inspect active workers (this may fail if workers aren't running)
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        scheduled = inspect.scheduled()
        registered = inspect.registered()
        
        status["background_jobs"] = {
            "celery_configured": True,
            "broker_url": settings.celery_broker_url[:20] + "..." if settings.celery_broker_url else None,
            "workers_active": active_workers is not None and len(active_workers) > 0,
            "worker_count": len(active_workers) if active_workers else 0,
            "scheduled_tasks": len(scheduled) if scheduled else 0,
            "registered_tasks": len(registered.get(list(registered.keys())[0], [])) if registered else 0,
            "error": None,
        }
    except Exception as e:
        status["background_jobs"] = {
            "celery_configured": True,
            "workers_active": False,
            "error": str(e),
        }
    
    return SuccessResponse(
        data=status,
        meta=Meta(timestamp=datetime.utcnow()),
    )


@router.get("/system/stocks/sample")
def get_sample_stocks(db: Session = Depends(get_db)):
    """Get a sample of stocks to verify data exists."""
    stocks = db.query(Stock).limit(10).all()
    
    result = []
    for stock in stocks:
        price_count = len(stock.prices) if stock.prices else 0
        has_fundamentals = stock.fundamentals is not None and len(stock.fundamentals) > 0
        
        result.append({
            "id": stock.id,
            "symbol": stock.symbol,
            "name": stock.name,
            "market": stock.market.value if stock.market else None,
            "price_records": price_count,
            "has_fundamentals": has_fundamentals,
            "is_active": stock.is_active,
        })
    
    return SuccessResponse(
        data={"stocks": result, "total_in_db": db.query(Stock).count()},
        meta=Meta(timestamp=datetime.utcnow()),
    )
