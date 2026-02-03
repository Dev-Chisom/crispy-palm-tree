"""Celery tasks for data ingestion."""

from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime, date
import pandas as pd
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.stock import Stock, Market
from app.models.price import StockPrice
from app.models.fundamental import Fundamental
from app.models.technical_indicator import TechnicalIndicator
from app.services.data_fetcher import DataFetcher
from app.services.indicator_calculator import IndicatorCalculator


@celery_app.task(name="fetch_stock_prices")
def fetch_stock_prices(symbol: str, market: str):
    """
    Fetch and store stock prices.

    Args:
        symbol: Stock symbol
        market: Market (US or NGX)
    """
    db: Session = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}

        prices_df = None
        if market == Market.US.value:
            prices_df = DataFetcher.fetch_us_stock_prices(symbol, period="1y")
        elif market == Market.NGX.value:
            # Fetch NGX stocks via Yahoo Finance (format: SYMBOL.NG)
            from datetime import datetime, timedelta
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
            prices_df = DataFetcher.fetch_ngx_stock_prices(symbol, start_date, end_date)

        if prices_df is None or prices_df.empty:
            return {"status": "error", "message": f"No price data fetched for {symbol}"}

        # Store prices in database
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

        db.commit()
        return {"status": "success", "symbol": symbol, "records": len(prices_df)}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="update_fundamentals")
def update_fundamentals(symbol: str):
    """
    Update fundamental data for a stock.

    Args:
        symbol: Stock symbol
    """
    db: Session = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}

        if stock.market == Market.US:
            fundamentals_dict = DataFetcher.fetch_us_stock_fundamentals(symbol)
        elif stock.market == Market.NGX:
            # NGX fundamentals may be limited on Yahoo Finance
            # Try to fetch what's available
            fundamentals_dict = DataFetcher.fetch_us_stock_fundamentals(f"{symbol}.NG")
            if not fundamentals_dict:
                fundamentals_dict = {}  # Return empty if not available
        else:
            return {"status": "error", "message": f"Unsupported market: {stock.market.value}"}

        if not fundamentals_dict:
            return {"status": "error", "message": f"No fundamental data fetched for {symbol}"}

        # Store or update fundamental data
        fundamental = (
            db.query(Fundamental)
            .filter(Fundamental.stock_id == stock.id, Fundamental.date == date.today())
            .first()
        )

        if fundamental:
            # Update existing
            fundamental.revenue = fundamentals_dict.get("revenue")
            fundamental.eps = fundamentals_dict.get("eps")
            fundamental.pe_ratio = fundamentals_dict.get("pe_ratio")
            fundamental.debt_ratio = fundamentals_dict.get("debt_ratio")
            fundamental.earnings_growth = fundamentals_dict.get("earnings_growth")
            fundamental.dividend_yield = fundamentals_dict.get("dividend_yield")
            fundamental.dividend_per_share = fundamentals_dict.get("dividend_per_share")
            fundamental.dividend_payout_ratio = fundamentals_dict.get("dividend_payout_ratio")
        else:
            # Create new
            fundamental = Fundamental(
                stock_id=stock.id,
                date=date.today(),
                revenue=fundamentals_dict.get("revenue"),
                eps=fundamentals_dict.get("eps"),
                pe_ratio=fundamentals_dict.get("pe_ratio"),
                debt_ratio=fundamentals_dict.get("debt_ratio"),
                earnings_growth=fundamentals_dict.get("earnings_growth"),
                dividend_yield=fundamentals_dict.get("dividend_yield"),
                dividend_per_share=fundamentals_dict.get("dividend_per_share"),
                dividend_payout_ratio=fundamentals_dict.get("dividend_payout_ratio"),
            )
            db.add(fundamental)

        db.commit()
        return {"status": "success", "symbol": symbol}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="calculate_indicators")
def calculate_indicators(symbol: str):
    """
    Calculate and store technical indicators for a stock.

    Args:
        symbol: Stock symbol
    """
    db: Session = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return {"status": "error", "message": f"Stock {symbol} not found"}

        # Get recent price data
        prices = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.time.desc())
            .limit(200)
            .all()
        )

        if len(prices) < 20:
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

        # Calculate indicators
        indicators = IndicatorCalculator.calculate_all_indicators(prices_df)

        # Store latest indicator
        latest_date = prices_df["time"].iloc[-1].date() if hasattr(prices_df["time"].iloc[-1], "date") else date.today()

        indicator = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.stock_id == stock.id, TechnicalIndicator.date == latest_date)
            .first()
        )

        if indicator:
            # Update existing
            indicator.rsi = indicators.get("rsi")
            indicator.macd = indicators.get("macd")
            indicator.macd_signal = indicators.get("macd_signal")
            indicator.macd_histogram = indicators.get("macd_histogram")
            indicator.sma_20 = indicators.get("sma_20")
            indicator.sma_50 = indicators.get("sma_50")
            indicator.sma_200 = indicators.get("sma_200")
            indicator.ema_12 = indicators.get("ema_12")
            indicator.ema_26 = indicators.get("ema_26")
            indicator.bollinger_upper = indicators.get("bollinger_upper")
            indicator.bollinger_lower = indicators.get("bollinger_lower")
            indicator.bollinger_middle = indicators.get("bollinger_middle")
            indicator.volume_avg = indicators.get("volume_avg")
        else:
            # Create new
            indicator = TechnicalIndicator(
                stock_id=stock.id,
                date=latest_date,
                rsi=indicators.get("rsi"),
                macd=indicators.get("macd"),
                macd_signal=indicators.get("macd_signal"),
                macd_histogram=indicators.get("macd_histogram"),
                sma_20=indicators.get("sma_20"),
                sma_50=indicators.get("sma_50"),
                sma_200=indicators.get("sma_200"),
                ema_12=indicators.get("ema_12"),
                ema_26=indicators.get("ema_26"),
                bollinger_upper=indicators.get("bollinger_upper"),
                bollinger_lower=indicators.get("bollinger_lower"),
                bollinger_middle=indicators.get("bollinger_middle"),
                volume_avg=indicators.get("volume_avg"),
            )
            db.add(indicator)

        db.commit()
        return {"status": "success", "symbol": symbol}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
