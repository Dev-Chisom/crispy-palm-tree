"""Market API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.stock import Stock, Market, AssetType
from app.models.signal import Signal, SignalType
from app.schemas.stock import StockResponse, StockListResponse
from app.schemas.signal import SignalResponse, SignalListResponse
from app.schemas.common import SuccessResponse, Meta
from app.services.cache import cache_service

router = APIRouter()


@router.get("/{market}/stocks", response_model=SuccessResponse)
def get_market_stocks(
    market: Market,
    asset_type: Optional[AssetType] = None,
    db: Session = Depends(get_db),
):
    """Get all stocks/ETFs/Mutual Funds for a specific market."""
    # Build cache key
    cache_key = f"market_stocks:{market.value}"
    if asset_type:
        cache_key += f":{asset_type.value}"
    
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    query = db.query(Stock).filter(Stock.market == market, Stock.is_active == True)
    if asset_type:
        query = query.filter(Stock.asset_type == asset_type)
    stocks = query.all()

    # Safely serialize stocks, handling missing columns gracefully
    stock_items = []
    for stock in stocks:
        try:
            stock_dict = {
                "id": stock.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "market": stock.market,
                "sector": stock.sector,
                "currency": stock.currency,
                "is_active": stock.is_active,
                "created_at": stock.created_at,
            }
            # Only include asset_type if column exists (migration applied)
            if hasattr(stock, 'asset_type'):
                stock_dict["asset_type"] = stock.asset_type
            else:
                stock_dict["asset_type"] = AssetType.STOCK
            # Only include stock_type if column exists (migration applied)
            if hasattr(stock, 'stock_type'):
                stock_dict["stock_type"] = stock.stock_type
            else:
                stock_dict["stock_type"] = None
            stock_items.append(StockResponse.model_validate(stock_dict))
        except Exception as e:
            # Log error but continue with other stocks
            print(f"Warning: Error serializing stock {stock.symbol}: {e}")
            continue

    result = StockListResponse(
        items=stock_items,
        total=len(stock_items),
        page=1,
        page_size=len(stock_items),
    )

    # Cache for 1 hour
    cache_service.set(cache_key, result.model_dump(), 3600)

    return SuccessResponse(
        data=result,
        meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
    )


@router.get("/{market}/highlights", response_model=SuccessResponse)
def get_market_highlights(market: Market, db: Session = Depends(get_db)):
    """Get market highlights (top movers, signals)."""
    # Check cache
    cache_key = f"market_highlights:{market.value}"
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    # Get top BUY signals
    top_buy_signals = (
        db.query(Signal)
        .join(Stock)
        .filter(Stock.market == market, Stock.is_active == True, Signal.signal_type == SignalType.BUY)
        .order_by(Signal.confidence_score.desc())
        .limit(5)
        .all()
    )

    # Get top SELL signals
    top_sell_signals = (
        db.query(Signal)
        .join(Stock)
        .filter(Stock.market == market, Stock.is_active == True, Signal.signal_type == SignalType.SELL)
        .order_by(Signal.confidence_score.desc())
        .limit(5)
        .all()
    )

    result = {
        "top_buy_signals": [SignalResponse.model_validate(s).model_dump() for s in top_buy_signals],
        "top_sell_signals": [SignalResponse.model_validate(s).model_dump() for s in top_sell_signals],
        "market": market.value,
    }

    # Cache for 15 minutes
    cache_service.set(cache_key, result, 900)

    return SuccessResponse(
        data=result,
        meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
    )
