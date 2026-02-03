"""Signal models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SignalType(enum.Enum):
    """Signal type enumeration."""

    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    NO_SIGNAL = "NO_SIGNAL"


class RiskLevel(enum.Enum):
    """Risk level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class HoldingPeriod(enum.Enum):
    """Holding period enumeration."""

    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class Signal(Base):
    """Signal model for AI-generated trading signals."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type = Column(Enum(SignalType), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(Enum(RiskLevel), nullable=False)
    holding_period = Column(Enum(HoldingPeriod), nullable=False)
    explanation = Column(JSON, nullable=False)  # JSON explanation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    stock = relationship("Stock", back_populates="signals")

    __table_args__ = (
        Index("idx_signals_stock_created", "stock_id", "created_at"),
    )

    def __repr__(self):
        return f"<Signal(stock_id={self.stock_id}, type={self.signal_type.value}, confidence={self.confidence_score})>"


class SignalHistory(Base):
    """Signal history model for backtesting."""

    __tablename__ = "signal_history"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type = Column(Enum(SignalType), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    stock = relationship("Stock", back_populates="signal_history")
    signal = relationship("Signal", foreign_keys=[signal_id])

    __table_args__ = (
        Index("idx_signal_history_stock_created", "stock_id", "created_at"),
    )

    def __repr__(self):
        return f"<SignalHistory(stock_id={self.stock_id}, type={self.signal_type.value}, created_at={self.created_at})>"
