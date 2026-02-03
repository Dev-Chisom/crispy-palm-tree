"""Signal API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models.stock import Stock, Market
from app.models.signal import Signal, SignalHistory, SignalType
from app.models.technical_indicator import TechnicalIndicator
from app.models.fundamental import Fundamental
from app.models.price import StockPrice
from app.schemas.signal import SignalResponse, SignalListResponse
from app.schemas.common import SuccessResponse, ErrorResponse, Meta
from app.services.cache import cache_service
from app.services.signal_generator import SignalGenerator
from app.services.investment_signal_generator import InvestmentSignalGenerator
from app.services.ml_signal_generator import MLSignalGenerator
from app.services.indicator_calculator import IndicatorCalculator
from app.services.explanation_generator import ExplanationGenerator
from app.services.data_fetcher import DataFetcher
from app.config import settings
import pandas as pd

router = APIRouter()


@router.get("/{symbol}/signal", response_model=SuccessResponse)
def get_stock_signal(
    symbol: str,
    use_ml: bool = Query(True, description="Use ML models if available"),
    db: Session = Depends(get_db),
):
    """Get current AI signal for a stock (with ML enhancement if available)."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Check cache
    cache_key = f"signal:{symbol}"
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    # Get latest signal from database
    latest_signal = (
        db.query(Signal)
        .filter(Signal.stock_id == stock.id)
        .order_by(Signal.created_at.desc())
        .first()
    )

    if latest_signal:
        # Check if signal is still fresh (within cache TTL)
        signal_age = (datetime.utcnow() - latest_signal.created_at).total_seconds()
        if signal_age < settings.redis_cache_ttl_signal:
            result = SignalResponse.model_validate(latest_signal)
            cache_service.set(cache_key, result.model_dump(), settings.redis_cache_ttl_signal)
            return SuccessResponse(
                data=result,
                meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
            )

    # Check if we have sufficient price data before attempting generation
    price_count = db.query(StockPrice).filter(StockPrice.stock_id == stock.id).count()
    
    if price_count < 20:
        # Not enough data - return latest signal if available, or suggest data fetch
        if latest_signal:
            result = SignalResponse.model_validate(latest_signal)
            return SuccessResponse(
                data=result,
                meta=Meta(
                    timestamp=datetime.utcnow(),
                    message=f"Using cached signal (insufficient price data: {price_count} records, need 20+)",
                ),
            )
        raise HTTPException(
            status_code=503,
            detail=f"Insufficient price data for {stock.symbol} ({price_count} records, need 20+). Please wait for data ingestion to complete or trigger data fetch manually.",
        )

    # Generate new signal if not cached or stale
    # This would typically be done via Celery task, but we'll do it synchronously here
    # In production, this should trigger a background task
    try:
        if use_ml:
            signal_data = _generate_signal_for_stock_with_ml(stock, db)
        else:
            signal_data = _generate_signal_for_stock(stock, db)
        result = SignalResponse.model_validate(signal_data)
        cache_service.set(cache_key, result.model_dump(), settings.redis_cache_ttl_signal)
        return SuccessResponse(
            data=result,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
        )
    except Exception as e:
        # If generation fails, return the latest signal from DB if available
        # This prevents 500 errors when Yahoo Finance is slow/unavailable
        if latest_signal:
            result = SignalResponse.model_validate(latest_signal)
            return SuccessResponse(
                data=result,
                meta=Meta(
                    timestamp=datetime.utcnow(),
                    message=f"Using cached signal (generation failed: {str(e)})",
                ),
            )
        # Only raise error if we have no signal at all
        raise HTTPException(
            status_code=503,
            detail=f"Error generating signal and no cached signal available: {str(e)}. Please ensure price data is available in the database.",
        )


@router.post("/generate", response_model=SuccessResponse)
def generate_signal(
    symbol: str = Body(..., description="Stock symbol"),
    db: Session = Depends(get_db),
):
    """Generate signal for a stock (admin/internal endpoint)."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    try:
        signal_data = _generate_signal_for_stock(stock, db)
        result = SignalResponse.model_validate(signal_data)
        return SuccessResponse(
            data=result,
            meta=Meta(timestamp=datetime.utcnow()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.get("/top", response_model=SuccessResponse)
def get_top_signals(
    market: Optional[str] = Query(None, description="Filter by market (US or NGX)"),
    signal_type: Optional[SignalType] = Query(None, description="Filter by signal type"),
    limit: int = Query(10, ge=1, le=100, description="Number of top signals"),
    db: Session = Depends(get_db),
):
    """Get top signals today by confidence score."""
    # Check cache
    cache_key = f"top_signals:{market}:{signal_type}:{limit}"
    cached = cache_service.get(cache_key)
    if cached:
        return SuccessResponse(
            data=cached,
            meta=Meta(timestamp=datetime.utcnow(), cache_hit=True),
        )

    query = db.query(Signal).join(Stock).filter(Stock.is_active == True)

    if market:
        # Convert string to Market enum if needed
        try:
            if isinstance(market, str):
                market_enum = Market[market.upper()]
            else:
                market_enum = market
            query = query.filter(Stock.market == market_enum)
        except (KeyError, AttributeError):
            # Invalid market value, skip filter
            pass
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)

    # Get today's signals
    today = datetime.utcnow().date()
    query = query.filter(Signal.created_at >= datetime.combine(today, datetime.min.time()))

    signals = query.order_by(Signal.confidence_score.desc()).limit(limit).all()

    result = SignalListResponse(
        items=[SignalResponse.model_validate(signal) for signal in signals],
        total=len(signals),
    )

    # Cache for 15 minutes
    cache_service.set(cache_key, result.model_dump(), 900)

    return SuccessResponse(
        data=result,
        meta=Meta(timestamp=datetime.utcnow(), cache_hit=False),
    )


@router.get("/{symbol}/history", response_model=SuccessResponse)
def get_signal_history(
    symbol: str,
    limit: int = Query(50, ge=1, le=200, description="Number of historical signals"),
    db: Session = Depends(get_db),
):
    """Get historical signals for a stock (for backtesting)."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    history = (
        db.query(SignalHistory)
        .filter(SignalHistory.stock_id == stock.id)
        .order_by(SignalHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    # Convert to dict format since SignalHistory has different fields
    history_data = [
        {
            "id": h.id,
            "stock_id": h.stock_id,
            "signal_type": h.signal_type.value,
            "confidence_score": h.confidence_score,
            "created_at": h.created_at,
        }
        for h in history
    ]

    return SuccessResponse(
        data=history_data,
        meta=Meta(timestamp=datetime.utcnow()),
    )


def _generate_signal_for_stock(stock: Stock, db: Session) -> Signal:
    """Internal function to generate signal for a stock."""
    # Try to get price data from database first (faster, no network calls)
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.time.desc())
        .limit(200)
        .all()
    )
    
    if not prices or len(prices) < 20:
        raise ValueError(f"Insufficient price data in database for {stock.symbol} ({len(prices) if prices else 0} records, need 20+)")
    
    # Use database data (fast, no network delay)
    prices_df = pd.DataFrame(
        [
            {
                "time": p.time,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
            }
            for p in prices
        ]
    )
    prices_df = prices_df.sort_values("time")
    # Keep time as column (not index) for compatibility with indicator calculator

    # Calculate indicators
    indicators = IndicatorCalculator.calculate_all_indicators(prices_df)

    # Get latest technical indicator from DB or calculate
    latest_indicator = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.stock_id == stock.id)
        .order_by(TechnicalIndicator.date.desc())
        .first()
    )

    if latest_indicator:
        # Use DB indicators if available
        indicators.update(
            {
                "rsi": latest_indicator.rsi,
                "macd": latest_indicator.macd,
                "macd_signal": latest_indicator.macd_signal,
                "macd_histogram": latest_indicator.macd_histogram,
                "sma_20": latest_indicator.sma_20,
                "sma_50": latest_indicator.sma_50,
                "sma_200": latest_indicator.sma_200,
                "ema_12": latest_indicator.ema_12,
                "ema_26": latest_indicator.ema_26,
                "bollinger_upper": latest_indicator.bollinger_upper,
                "bollinger_lower": latest_indicator.bollinger_lower,
                "volume_avg": latest_indicator.volume_avg,
            }
        )

    # Get fundamentals
    fundamental = (
        db.query(Fundamental)
        .filter(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .first()
    )

    fundamentals_dict = {}
    if fundamental:
        fundamentals_dict = {
            "revenue": fundamental.revenue,
            "eps": fundamental.eps,
            "pe_ratio": fundamental.pe_ratio,
            "debt_ratio": fundamental.debt_ratio,
            "earnings_growth": fundamental.earnings_growth,
            "dividend_yield": fundamental.dividend_yield,
            "dividend_per_share": fundamental.dividend_per_share,
            "dividend_payout_ratio": fundamental.dividend_payout_ratio,
        }
        
        # Classify stock and update if needed
        from app.services.stock_classifier import StockClassifier
        from app.models.stock import StockType
        
        stock_type = StockClassifier.classify_stock(
            dividend_yield=fundamental.dividend_yield,
            earnings_growth=fundamental.earnings_growth,
            pe_ratio=fundamental.pe_ratio,
            dividend_payout_ratio=fundamental.dividend_payout_ratio,
        )
        
        # Update stock classification
        if stock.stock_type != stock_type:
            stock.stock_type = stock_type
            db.commit()

    # Generate investment signal (optimized for long-term investing, not trading)
    signal_result = InvestmentSignalGenerator.generate_investment_signal(
        indicators=indicators,
        fundamentals=fundamentals_dict,
        prices_df=prices_df,
    )
    
    # Investment signal generator already includes investment-focused explanation
    explanation = signal_result.get("explanation", {})
    
    # Add stock classification and investor recommendations
    if fundamental:
        from app.services.stock_classifier import StockClassifier
        from app.models.stock import StockType
        
        stock_type = stock.stock_type or StockClassifier.classify_stock(
            dividend_yield=fundamental.dividend_yield,
            earnings_growth=fundamental.earnings_growth,
            pe_ratio=fundamental.pe_ratio,
            dividend_payout_ratio=fundamental.dividend_payout_ratio,
        )
        
        investor_recommendation = StockClassifier.get_investor_recommendation(
            stock_type=stock_type,
            signal_type=signal_result["signal_type"].value,
        )
        
        explanation["stock_classification"] = {
            "stock_type": stock_type.value,
            "investor_recommendation": investor_recommendation,
        }

    # Create signal record
    signal = Signal(
        stock_id=stock.id,
        signal_type=signal_result["signal_type"],
        confidence_score=signal_result["confidence_score"],
        risk_level=signal_result["risk_level"],
        holding_period=signal_result["holding_period"],
        explanation=explanation,
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    # Create history record
    history = SignalHistory(
        signal_id=signal.id,
        stock_id=stock.id,
        signal_type=signal.signal_type,
        confidence_score=signal.confidence_score,
    )
    db.add(history)
    db.commit()

    return signal


def _generate_signal_for_stock_with_ml(stock: Stock, db: Session) -> Signal:
    """Internal function to generate signal using ML models."""
    # Get price data from database (fast, no network calls)
    # Pre-check already validated we have enough data
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.time.desc())
        .limit(200)
        .all()
    )
    
    if not prices or len(prices) < 20:
        raise ValueError(f"Insufficient price data in database for {stock.symbol} ({len(prices) if prices else 0} records, need 20+)")
    
    # Use database data (fast, no network delay)
    prices_df = pd.DataFrame(
        [
            {
                "time": p.time,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
            }
            for p in prices
        ]
    )
    prices_df = prices_df.sort_values("time")
    # Keep time as column (not index) for compatibility with indicator calculator

    # Calculate indicators
    indicators = IndicatorCalculator.calculate_all_indicators(prices_df)

    # Get latest technical indicator from DB or calculate
    latest_indicator = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.stock_id == stock.id)
        .order_by(TechnicalIndicator.date.desc())
        .first()
    )

    if latest_indicator:
        # Use DB indicators if available
        indicators.update(
            {
                "rsi": latest_indicator.rsi,
                "macd": latest_indicator.macd,
                "macd_signal": latest_indicator.macd_signal,
                "macd_histogram": latest_indicator.macd_histogram,
                "sma_20": latest_indicator.sma_20,
                "sma_50": latest_indicator.sma_50,
                "sma_200": latest_indicator.sma_200,
                "ema_12": latest_indicator.ema_12,
                "ema_26": latest_indicator.ema_26,
                "bollinger_upper": latest_indicator.bollinger_upper,
                "bollinger_lower": latest_indicator.bollinger_lower,
                "volume_avg": latest_indicator.volume_avg,
            }
        )

    # Get fundamentals
    fundamental = (
        db.query(Fundamental)
        .filter(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.date.desc())
        .first()
    )

    fundamentals_dict = {}
    if fundamental:
        fundamentals_dict = {
            "revenue": fundamental.revenue,
            "eps": fundamental.eps,
            "pe_ratio": fundamental.pe_ratio,
            "debt_ratio": fundamental.debt_ratio,
            "earnings_growth": fundamental.earnings_growth,
        }

    # Use ML signal generator
    ml_generator = MLSignalGenerator(use_lstm=True, use_classifier=True, fallback_to_rules=True)
    
    signal_result = ml_generator.generate_signal_with_ml(
        symbol=stock.symbol,
        indicators=indicators,
        fundamentals=fundamentals_dict,
        prices_df=prices_df,
    )

    # Enhance explanation
    current_price = prices_df["close"].iloc[-1]
    technical_data = {
        "score": 50,
        "trend": "bullish" if signal_result["signal_type"].value == "BUY" else "bearish",
    }
    fundamental_data = {
        "score": 50,
        **fundamentals_dict,
    }
    trend_data = {"score": 50}
    volatility_data = {"score": 50}

    explanation = ExplanationGenerator.generate_explanation(
        signal_type=signal_result["signal_type"],
        confidence_score=signal_result["confidence_score"],
        risk_level=signal_result["risk_level"],
        holding_period=signal_result["holding_period"],
        technical_data=technical_data,
        fundamental_data=fundamental_data,
        trend_data=trend_data,
        volatility_data=volatility_data,
        current_price=current_price,
        indicators=indicators,
    )

    # Merge ML explanation
    if signal_result.get("ml_used"):
        explanation["ml_prediction"] = signal_result["explanation"].get("ml_prediction")
        explanation["hybrid_approach"] = True

    # Create signal record
    signal = Signal(
        stock_id=stock.id,
        signal_type=signal_result["signal_type"],
        confidence_score=signal_result["confidence_score"],
        risk_level=signal_result["risk_level"],
        holding_period=signal_result["holding_period"],
        explanation=explanation,
    )

    db.add(signal)
    db.commit()
    db.refresh(signal)

    # Create history record
    history = SignalHistory(
        signal_id=signal.id,
        stock_id=stock.id,
        signal_type=signal.signal_type,
        confidence_score=signal.confidence_score,
    )
    db.add(history)
    db.commit()

    return signal
