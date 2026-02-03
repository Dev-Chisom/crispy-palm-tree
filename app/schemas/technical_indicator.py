"""Technical indicator schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class TechnicalIndicatorResponse(BaseModel):
    """Schema for technical indicator response."""

    id: int
    stock_id: int
    date: date
    rsi: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    sma_20: Optional[float]
    sma_50: Optional[float]
    sma_200: Optional[float]
    ema_12: Optional[float]
    ema_26: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]
    bollinger_middle: Optional[float]
    volume_avg: Optional[float]

    class Config:
        from_attributes = True
