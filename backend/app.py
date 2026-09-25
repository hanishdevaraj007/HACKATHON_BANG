"""
FastAPI Application and Event Ingestion Endpoints.

Exposes REST API routes for normalizing, validating, persisting, and querying
security events. Wraps the underlying EventStore service layer.

OWNED BY: Backend Team (Component B)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.config import DEFAULT_DB_PATH
from backend.ingestion import DuplicateEventError, EventStore, ValidationError
from backend.models import ErrorResponse, EventListResponse

app = FastAPI(
    title="Meridian Security Platform - Backend API",
    description="Multi-Modal Security Event Correlation Platform - Ingestion Subsystem API",
    version="0.1.0",
)

# Global or configurable EventStore singleton for app execution
_event_store_instance: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Dependency provider for EventStore. Can be overridden in pytest tests."""
    global _event_store_instance
    if _event_store_instance is None:
        _event_store_instance = EventStore(DEFAULT_DB_PATH)
    return _event_store_instance


# ---------------------------------------------------------------------------
# Exception Handlers — Ensured non-crashing server behavior
# ---------------------------------------------------------------------------
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Unprocessable Entity", "detail": exc.errors},
    )


@app.exception_handler(DuplicateEventError)
async def duplicate_event_handler(request: Request, exc: DuplicateEventError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "Conflict", "detail": f"Event ID {exc.event_id} already exists"},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Unprocessable Entity", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Service liveness health check."""
    return {"status": "ok", "service": "meridian-backend-ingestion"}


# ---------------------------------------------------------------------------
# Event Ingestion & Query Endpoints
# ---------------------------------------------------------------------------
@app.post(
    "/api/v1/events",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    responses={
        201: {"description": "Event accepted and persisted"},
        409: {"model": ErrorResponse, "description": "Duplicate event_id"},
        422: {"model": ErrorResponse, "description": "Schema validation failed"},
    },
    tags=["Events"],
)
async def ingest_event(
    event: Dict[str, Any],
    store: EventStore = Depends(get_event_store),
):
    """
    Ingest a single normalized security event.
    
    Validates payload against schema/event.schema.json, checks for duplicate event_id,
    and persists the record to SQLite. Returns HTTP 201 Created on success.
    """
    stored_event = store.insert(event)
    return stored_event


@app.get(
    "/api/v1/events",
    response_model=EventListResponse,
    tags=["Events"],
)
async def list_events(
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Query offset for pagination"),
    since: Optional[str] = Query(None, description="ISO 8601 UTC start timestamp filter"),
    until: Optional[str] = Query(None, description="ISO 8601 UTC end timestamp filter"),
    event_type: Optional[str] = Query(None, description="Canonical event_type filter"),
    source: Optional[str] = Query(None, description="Source ID or source_type filter"),
    zone_id: Optional[str] = Query(None, description="Location zone_id filter"),
    actor_id: Optional[str] = Query(None, description="Actor entity_id filter"),
    store: EventStore = Depends(get_event_store),
):
    """
    Query ingested events sorted deterministically by timestamp ASC, event_id ASC.
    """
    events = store.query(
        limit=limit,
        offset=offset,
        since=since,
        until=until,
        event_type=event_type,
        source=source,
        zone_id=zone_id,
        actor_id=actor_id,
    )
    return EventListResponse(
        count=len(events),
        limit=limit,
        offset=offset,
        events=events,
    )


@app.get(
    "/api/v1/events/{event_id}",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Stored event retrieved"},
        404: {"model": ErrorResponse, "description": "Event not found"},
    },
    tags=["Events"],
)
async def get_event_by_id(
    event_id: str,
    store: EventStore = Depends(get_event_store),
):
    """Retrieve a single stored event by UUID."""
    event = store.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found",
        )
    return event
