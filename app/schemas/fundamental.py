"""Fundamental data schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class FundamentalResponse(BaseModel):
    """Schema for fundamental data response."""

    id: int
    stock_id: int
    date: date
    revenue: Optional[float]
    eps: Optional[float]
    pe_ratio: Optional[float]
    debt_ratio: Optional[float]
    earnings_growth: Optional[float]
    updated_at: datetime

    class Config:
        from_attributes = True
