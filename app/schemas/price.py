"""Price schemas."""

from pydantic import BaseModel
from typing import List
from datetime import datetime


class PriceResponse(BaseModel):
    """Schema for stock price response."""

    time: datetime
    stock_id: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        from_attributes = True


class PriceListResponse(BaseModel):
    """Schema for price list response."""

    items: List[PriceResponse]
    total: int
