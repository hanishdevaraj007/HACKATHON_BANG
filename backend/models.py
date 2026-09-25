"""
Pydantic API Data Models and Response Schemas.

Provides lightweight request/response wrappers for FastAPI endpoints.
All models remain fully compatible with schema/event.schema.json.

OWNED BY: Backend Team (Component B)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response body."""

    error: str = Field(..., description="Error category or status summary")
    detail: Any = Field(..., description="Detailed error messages or validation issues")


class EventIngestResponse(BaseModel):
    """Response returned upon successful event ingestion."""

    status: str = "success"
    event_id: str
    message: str = "Event ingested and persisted successfully"
    event: Dict[str, Any]


class EventListResponse(BaseModel):
    """Response returned when querying events list."""

    count: int
    limit: int
    offset: int
    events: List[Dict[str, Any]]
