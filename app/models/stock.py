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


class Stock(Base):
    """Stock model representing a stock symbol."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    market = Column(Enum(Market), nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
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
