"""Celery tasks for signal generation."""

from sqlalchemy.orm import Session
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.stock import Stock
from app.models.price import StockPrice
from app.models.fundamental import Fundamental
from app.models.technical_indicator import TechnicalIndicator
from app.models.signal import Signal, SignalHistory
from app.services.signal_generator import SignalGenerator
from app.services.indicator_calculator import IndicatorCalculator
from app.services.explanation_generator import ExplanationGenerator
from app.services.data_fetcher import DataFetcher
from app.services.cache import cache_service
from app.config import settings
import pandas as pd


@celery_app.task(name="generate_signal")
def generate_signal(symbol: str):
    """
    Generate signal for a stock.

    Args:
        symbol: Stock symbol
    """
    db: Session = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}

        # Get price data
        prices = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.time.desc())
            .limit(200)
            .all()
        )

        if not prices:
            return {"status": "error", "message": f"Insufficient price data for {symbol}"}

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

        # Get indicators
        latest_indicator = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.stock_id == stock.id)
            .order_by(TechnicalIndicator.date.desc())
            .first()
        )

        indicators = {}
        if latest_indicator:
            indicators = {
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
        else:
            # Calculate on the fly
            indicators = IndicatorCalculator.calculate_all_indicators(prices_df)

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

        # Generate signal
        signal_result = SignalGenerator.generate_signal(
            indicators=indicators,
            fundamentals=fundamentals_dict,
            prices_df=prices_df,
        )

        # Enhance explanation
        current_price = prices_df["close"].iloc[-1]
        technical_data = {
            "score": signal_result.get("composite_score", 50),
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

        # Create signal
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

        # Create history
        history = SignalHistory(
            signal_id=signal.id,
            stock_id=stock.id,
            signal_type=signal.signal_type,
            confidence_score=signal.confidence_score,
        )
        db.add(history)
        db.commit()

        # Clear cache
        cache_key = f"signal:{symbol}"
        cache_service.delete(cache_key)

        return {
            "status": "success",
            "symbol": symbol,
            "signal_type": signal_result["signal_type"].value,
            "confidence": signal_result["confidence_score"],
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="batch_signal_generation")
def batch_signal_generation(market: str = None):
    """
    Generate signals for all active stocks.

    Args:
        market: Optional market filter (US or NGX)
    """
    db: Session = SessionLocal()
    try:
        query = db.query(Stock).filter(Stock.is_active == True)
        if market:
            from app.models.stock import Market
            query = query.filter(Stock.market == Market[market])

        stocks = query.all()
        results = []

        for stock in stocks:
            result = generate_signal.delay(stock.symbol)
            results.append({"symbol": stock.symbol, "task_id": result.id})

        return {
            "status": "success",
            "stocks_processed": len(stocks),
            "tasks": results,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
