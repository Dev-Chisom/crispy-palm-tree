"""Stock model."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class Market(enum.Enum):
    """Market enumeration."""

    US = "US"
    NGX = "NGX"


class StockType(enum.Enum):
    """Stock type classification."""

    GROWTH = "GROWTH"  # High growth, reinvests profits, high P/E
    DIVIDEND = "DIVIDEND"  # Regular dividends, stable income, lower growth
    HYBRID = "HYBRID"  # Both growth and dividend characteristics


class AssetType(enum.Enum):
    """Asset type classification."""

    STOCK = "STOCK"  # Individual company stock
    ETF = "ETF"  # Exchange-Traded Fund
    MUTUAL_FUND = "MUTUAL_FUND"  # Mutual Fund


class Stock(Base):
    """Stock model representing a stock symbol."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    market = Column(Enum(Market), nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    asset_type = Column(Enum(AssetType), nullable=True, default=AssetType.STOCK, index=True)  # STOCK, ETF, or MUTUAL_FUND
    stock_type = Column(Enum(StockType), nullable=True, index=True)  # Growth, Dividend, or Hybrid
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    fundamentals = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="stock", cascade="all, delete-orphan")
    signal_history = relationship("SignalHistory", back_populates="stock", cascade="all, delete-orphan")
    technical_indicators = relationship(
        "TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Stock(symbol={self.symbol}, market={self.market.value})>"
