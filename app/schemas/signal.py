"""Signal schemas."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.signal import SignalType, RiskLevel, HoldingPeriod


class SignalExplanation(BaseModel):
    """Schema for signal explanation JSON."""

    summary: str
    factors: Dict[str, Any]
    triggers: List[str]
    risks: List[str]
    invalidation_conditions: List[str]


class SignalCreate(BaseModel):
    """Schema for creating a signal (internal use)."""

    stock_id: int
    signal_type: SignalType
    confidence_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    holding_period: HoldingPeriod
    explanation: Dict[str, Any]


class SignalResponse(BaseModel):
    """Schema for signal response."""

    id: int
    stock_id: int
    signal_type: SignalType
    confidence_score: float
    risk_level: RiskLevel
    holding_period: HoldingPeriod
    explanation: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    """Schema for signal list response."""

    items: List[SignalResponse]
    total: int
    page: Optional[int] = None
    page_size: Optional[int] = None
