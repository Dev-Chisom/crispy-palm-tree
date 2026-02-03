"""Stock schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.stock import Market, StockType


class StockCreate(BaseModel):
    """Schema for creating a stock."""

    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    market: Market
    sector: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=10)
    is_active: bool = True


class StockResponse(BaseModel):
    """Schema for stock response."""

    id: int
    symbol: str
    name: str
    market: Market
    sector: Optional[str]
    currency: str
    stock_type: Optional[StockType] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StockListResponse(BaseModel):
    """Schema for paginated stock list response."""

    items: List[StockResponse]
    total: int
    page: int
    page_size: int
