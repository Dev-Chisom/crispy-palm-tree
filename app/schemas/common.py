"""Common schemas for API responses."""

from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class Meta(BaseModel):
    """Metadata for API responses."""

    timestamp: datetime
    cache_hit: bool = False
    page: Optional[int] = None
    page_size: Optional[int] = None
    total: Optional[int] = None


class SuccessResponse(BaseModel):
    """Standard success response format."""

    success: bool = True
    data: Any
    meta: Optional[Meta] = None


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = False
    error: ErrorDetail
