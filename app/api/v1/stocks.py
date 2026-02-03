"""Stock API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from app.database import get_db
from app.models.stock import Stock, Market
from app.models.price import StockPrice
from app.models.fundamental import Fundamental
from app.models.technical_indicator import TechnicalIndicator
from app.schemas.stock import StockResponse, StockListResponse, StockCreate
from app.schemas.price import PriceResponse, PriceListResponse
from app.schemas.fundamental import FundamentalResponse
from app.schemas.technical_indicator import TechnicalIndicatorResponse
from app.schemas.common import SuccessResponse, ErrorResponse, Meta
from app.services.cache import cache_service
from app.config import settings
from app.tasks.data_ingestion import fetch_stock_prices, update_fundamentals, calculate_indicators
from app.services.data_fetcher import DataFetcher

router = APIRouter()


@router.get("", response_model=SuccessResponse)
def list_stocks(
    market: Optional[Market] = Query(None, description="Filter by market"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List all stocks with pagination and filters."""
    query = db.query(Stock).filter(Stock.is_active == True)

    if market:
        query = query.filter(Stock.market == market)
    if sector:
        query = query.filter(Stock.sector == sector)

    total = query.count()
    offset = (page - 1) * page_size
    stocks = query.offset(offset).limit(page_size).all()

    return SuccessResponse(
        data=StockListResponse(
            items=[StockResponse.model_validate(stock) for stock in stocks],
            total=total,
            page=page,
            page_size=page_size,
        ),
        meta=Meta(
            timestamp=datetime.utcnow(),
            page=page,
            page_size=page_size,
            total=total,
        ),
    )


@router.post("", response_model=SuccessResponse, status_code=201)
def create_stock(stock_data: StockCreate, db: Session = Depends(get_db)):
    """Create a new stock and automatically trigger data fetching."""
    # Check if stock already exists
    existing = db.query(Stock).filter(Stock.symbol == stock_data.symbol.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Stock {stock_data.symbol} already exists")

    # Fetch stock info from API for US stocks
    name = stock_data.name
    sector = stock_data.sector
    if stock_data.market == Market.US:
        try:
            info = DataFetcher.fetch_us_stock_info(stock_data.symbol)
            if info:
                name = info.get("name", name)
                sector = info.get("sector", sector)
        except Exception:
            pass  # Use provided values if fetch fails

    # Create stock
    stock = Stock(
        symbol=stock_data.symbol.upper(),
        name=name,
        market=stock_data.market,
        sector=sector,
        currency=stock_data.currency,
        is_active=stock_data.is_active,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)

    # Automatically trigger data fetching in background
    try:
        fetch_stock_prices.delay(stock.symbol, stock.market.value)
        update_fundamentals.delay(stock.symbol)
        calculate_indicators.delay(stock.symbol)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Warning: Failed to queue data fetch tasks for {stock.symbol}: {e}")

    return SuccessResponse(
        data=StockResponse.model_validate(stock),
        meta=Meta(timestamp=datetime.utcnow()),
    )


@router.get("/{identifier}", response_model=SuccessResponse)
def get_stock(identifier: str, db: Session = Depends(get_db)):
    """
    Get stock details by symbol or ID.
    
    Supports both:
    - GET /api/v1/stocks/AAPL (by symbol)
    - GET /api/v1/stocks/1 (by ID)
    """
    # Try to parse as integer ID first
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        # Not an integer, treat as symbol
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")

    return SuccessResponse(
        data=StockResponse.model_validate(stock),
        meta=Meta(timestamp=datetime.utcnow()),
    )


@router.get("/{identifier}/prices", response_model=SuccessResponse)
def get_stock_prices(
    identifier: str,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
):
    """Get OHLCV price data for a stock (by symbol or ID)."""
    # Try to parse as integer ID first
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        # Not an integer, treat as symbol
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")

    # Check cache (use symbol for cache key)
    cache_key = f"stock_prices:{stock.symbol}:{start_date}:{end_date}:{limit}"
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    query = db.query(StockPrice).filter(StockPrice.stock_id == stock.id)

    if start_date:
        query = query.filter(StockPrice.time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(StockPrice.time <= datetime.combine(end_date, datetime.max.time()))

    prices = query.order_by(StockPrice.time.desc()).limit(limit).all()

    result = PriceListResponse(
        items=[PriceResponse.model_validate(price) for price in prices],
        total=len(prices),
    )

    # Cache result
    cache_service.set(cache_key, result.model_dump(), settings.redis_cache_ttl_price)

    return SuccessResponse(
        data=result,
        meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
    )


@router.get("/{identifier}/fundamentals", response_model=SuccessResponse)
def get_stock_fundamentals(identifier: str, db: Session = Depends(get_db)):
    """Get latest fundamental data for a stock (by symbol or ID)."""
    # Try to parse as integer ID first
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        # Not an integer, treat as symbol
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")

    # Check cache (use symbol for cache key)
    cache_key = f"stock_fundamentals:{stock.symbol}"
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    fundamental = (
        db.query(Fundamental)
        .filter(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .first()
    )

    if not fundamental:
        # Return empty response instead of 404
        return SuccessResponse(
            data=None,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
        )

    result = FundamentalResponse.model_validate(fundamental)

    # Cache result
    cache_service.set(cache_key, result.model_dump(), settings.redis_cache_ttl_fundamental)

    return SuccessResponse(
        data=result,
        meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
    )


@router.get("/{identifier}/indicators", response_model=SuccessResponse)
def get_stock_indicators(
    identifier: str,
    limit: int = Query(30, ge=1, le=100, description="Number of recent indicators"),
    db: Session = Depends(get_db),
):
    """Get technical indicators for a stock (by symbol or ID)."""
    # Try to parse as integer ID first
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        # Not an integer, treat as symbol
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")

    indicators = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.stock_id == stock.id)
        .order_by(TechnicalIndicator.date.desc())
        .limit(limit)
        .all()
    )

    # Return empty array if no indicators (don't return 404)
    return SuccessResponse(
        data=[TechnicalIndicatorResponse.model_validate(ind) for ind in indicators],
        meta=Meta(timestamp=datetime.utcnow()),
    )


@router.get("/{identifier}/signal", response_model=SuccessResponse)
def get_stock_signal_from_stocks(
    identifier: str,
    use_ml: bool = Query(True, description="Use ML models if available"),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint: Get signal for a stock (by symbol or ID).
    Matches frontend expectation: /api/v1/stocks/{identifier}/signal
    Delegates to signals endpoint.
    """
    # Resolve identifier to symbol
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")
    
    # Import here to avoid circular dependency
    from app.api.v1 import signals
    return signals.get_stock_signal(stock.symbol, use_ml, db)


@router.get("/{identifier}/backtest", response_model=SuccessResponse)
def get_stock_backtest_from_stocks(
    identifier: str,
    start_date: Optional[date] = Query(None, description="Start date (default: 1 year ago)"),
    end_date: Optional[date] = Query(None, description="End date (default: today)"),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint: Get backtest for a stock (by symbol or ID).
    Matches frontend expectation: /api/v1/stocks/{identifier}/backtest
    Delegates to backtest endpoint.
    """
    # Resolve identifier to symbol
    try:
        stock_id = int(identifier)
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
    except ValueError:
        stock = db.query(Stock).filter(Stock.symbol == identifier.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {identifier} not found")
    
    # Import here to avoid circular dependency
    from app.api.v1 import backtest
    return backtest.get_backtest_performance(stock.symbol, start_date, end_date, db)
