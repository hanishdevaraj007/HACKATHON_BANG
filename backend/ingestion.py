"""
Normalized Event Ingestion and Store Interface.

Provides schema validation, event persistence via EventStore, duplicate detection,
and a lightweight pub-sub publisher extension point for correlation engine subscribers.

OWNED BY: Backend Team (Component B)
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import jsonschema

from backend.config import DEFAULT_DB_PATH
from backend.contracts import load_event_schema
from backend.db import (
    event_exists_record,
    get_event_record,
    init_db,
    insert_event_record,
    query_event_records,
)


class ValidationError(Exception):
    """Raised when an event fails validation against schema/event.schema.json."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Event validation failed: {'; '.join(errors)}")


class DuplicateEventError(Exception):
    """Raised when an event with an existing event_id is submitted."""

    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Duplicate event_id: {event_id}")


def validate_event(event: Dict[str, Any]) -> List[str]:
    """
    Validate an event dictionary against the normalized event JSON schema.
    Returns a list of error message strings. If empty, validation succeeded.
    """
    schema = load_event_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for err in validator.iter_errors(event):
        path = ".".join(str(p) for p in err.path) if err.path else "root"
        errors.append(f"{path}: {err.message}")
    return errors


class EventPublisher:
    """Lightweight in-memory pub-sub publisher for live event notifications."""

    def __init__(self):
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback function fn(event) to receive ingested events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister a callback function."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event: Dict[str, Any]) -> None:
        """Publish an ingested event to all registered subscribers."""
        for callback in list(self._subscribers):
            try:
                callback(event)
            except Exception:
                # Callback failures must never interrupt event ingestion
                pass


class EventStore:
    """
    Durable SQLite Event Store interface.
    
    Exposes a stable Python API for future backend correlation components, FSMs,
    and HTTP controllers without requiring FastAPI.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        init_db(self.db_path)
        self.publisher = EventPublisher()

    def insert(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate, store, and publish a normalized security event.
        
        Raises:
            ValidationError: If event fails JSON schema validation.
            DuplicateEventError: If event_id already exists in SQLite.
        """
        if not isinstance(event, dict):
            raise ValidationError(["Payload must be a JSON object"])

        # 1. Validate against schema/event.schema.json
        errors = validate_event(event)
        if errors:
            raise ValidationError(errors)

        event_id = event["event_id"]

        # 2. Check for duplicate event_id
        if self.event_exists(event_id):
            raise DuplicateEventError(event_id)

        # 3. Timestamp handling: preserve event's timestamp, add ingested_at UTC
        ingested_at = datetime.now(timezone.utc).isoformat()

        # 4. Serialize raw JSON and persist to SQLite
        import json
        raw_json_str = json.dumps(event, separators=(",", ":"))
        insert_event_record(self.db_path, event, raw_json_str, ingested_at)

        # 5. Notify pub-sub subscribers
        self.publisher.publish(event)

        return event

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a stored event by UUID."""
        return get_event_record(self.db_path, event_id)

    def event_exists(self, event_id: str) -> bool:
        """Check if an event_id exists in the store."""
        return event_exists_record(self.db_path, event_id)

    def query(
        self,
        limit: int = 100,
        offset: int = 0,
        since: Optional[str] = None,
        until: Optional[str] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        zone_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query events with deterministic sorting (timestamp ASC, event_id ASC)."""
        return query_event_records(
            self.db_path,
            limit=limit,
            offset=offset,
            since=since,
            until=until,
            event_type=event_type,
            source=source,
            zone_id=zone_id,
            actor_id=actor_id,
        )
