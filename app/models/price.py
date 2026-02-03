"""Stock price model (TimescaleDB hypertable)."""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class StockPrice(Base):
    """Stock price model for OHLCV data (TimescaleDB hypertable)."""

    __tablename__ = "stock_prices"

    time = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="prices")

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_stock_prices_stock_time", "stock_id", "time"),
    )

    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, time={self.time}, close={self.close})>"
