"""Fundamental data model."""

from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Fundamental(Base):
    """Fundamental data model for stock financial metrics."""

    __tablename__ = "fundamentals"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    revenue = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)  # Earnings per share
    pe_ratio = Column(Float, nullable=True)  # Price-to-earnings ratio
    debt_ratio = Column(Float, nullable=True)
    earnings_growth = Column(Float, nullable=True)  # Percentage
    dividend_yield = Column(Float, nullable=True)  # Dividend yield percentage
    dividend_per_share = Column(Float, nullable=True)  # Dividend per share
    dividend_payout_ratio = Column(Float, nullable=True)  # Dividend payout ratio percentage
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    stock = relationship("Stock", back_populates="fundamentals")

    # Unique constraint on stock_id and date
    __table_args__ = (
        Index("idx_fundamentals_stock_date", "stock_id", "date", unique=True),
    )

    def __repr__(self):
        return f"<Fundamental(stock_id={self.stock_id}, date={self.date}, pe_ratio={self.pe_ratio})>"
