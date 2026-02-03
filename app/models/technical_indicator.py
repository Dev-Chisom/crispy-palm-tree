"""Technical indicator model."""

from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class TechnicalIndicator(Base):
    """Technical indicator model for calculated technical metrics."""

    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    rsi = Column(Float, nullable=True)  # Relative Strength Index
    macd = Column(Float, nullable=True)  # MACD line
    macd_signal = Column(Float, nullable=True)  # MACD signal line
    macd_histogram = Column(Float, nullable=True)  # MACD histogram
    sma_20 = Column(Float, nullable=True)  # Simple Moving Average 20
    sma_50 = Column(Float, nullable=True)  # Simple Moving Average 50
    sma_200 = Column(Float, nullable=True)  # Simple Moving Average 200
    ema_12 = Column(Float, nullable=True)  # Exponential Moving Average 12
    ema_26 = Column(Float, nullable=True)  # Exponential Moving Average 26
    bollinger_upper = Column(Float, nullable=True)  # Bollinger Bands upper
    bollinger_lower = Column(Float, nullable=True)  # Bollinger Bands lower
    bollinger_middle = Column(Float, nullable=True)  # Bollinger Bands middle
    volume_avg = Column(Float, nullable=True)  # Average volume

    # Relationships
    stock = relationship("Stock", back_populates="technical_indicators")

    # Unique constraint on stock_id and date
    __table_args__ = (
        Index("idx_technical_indicators_stock_date", "stock_id", "date", unique=True),
    )

    def __repr__(self):
        return f"<TechnicalIndicator(stock_id={self.stock_id}, date={self.date}, rsi={self.rsi})>"
