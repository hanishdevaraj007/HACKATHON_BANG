"""
Backend Package Initialization.

Exports core ingestion models, store interface, database initializers, and FastAPI application.

OWNED BY: Backend Team (Component B)
"""

from backend.app import app
from backend.db import init_db
from backend.ingestion import (
    DuplicateEventError,
    EventPublisher,
    EventStore,
    ValidationError,
    validate_event,
)

__all__ = [
    "app",
    "init_db",
    "EventStore",
    "EventPublisher",
    "ValidationError",
    "DuplicateEventError",
    "validate_event",
]
