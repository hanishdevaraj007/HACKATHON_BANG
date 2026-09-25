"""
Database Layer for Event Storage.

Provides direct SQLite persistence, initialization, and querying operations.
Executes raw SQL using parameterized queries to ensure security and thread safety.

OWNED BY: Backend Team (Component B)
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import DEFAULT_DB_PATH, DEFAULT_QUERY_LIMIT, MAX_QUERY_LIMIT


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    """Create and return a SQLite connection with dict row factory."""
    path = Path(db_path)
    if path != Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Initialize SQLite database tables and indices if they do not exist."""
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                actor_id TEXT,
                zone_id TEXT,
                device_id TEXT,
                confidence REAL NOT NULL,
                raw_ref TEXT,
                raw_json TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp, event_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_actor ON events(actor_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_zone ON events(zone_id);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_type, source_id);"
        )
    conn.close()


def extract_index_fields(event: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract indexed fields safely from a normalized event dict."""
    actor = event.get("actor")
    actor_id = actor.get("entity_id") if isinstance(actor, dict) else None

    location = event.get("location")
    zone_id = location.get("zone_id") if isinstance(location, dict) else None

    device = event.get("device")
    device_id = device.get("device_id") if isinstance(device, dict) else None

    source = event.get("source", {})
    source_type = source.get("source_type", "unknown")
    source_id = source.get("source_id", "unknown")

    return {
        "actor_id": actor_id,
        "zone_id": zone_id,
        "device_id": device_id,
        "source_type": source_type,
        "source_id": source_id,
    }


def insert_event_record(
    db_path: Path | str, event: Dict[str, Any], raw_json: str, ingested_at: str
) -> None:
    """Insert a validated event into the SQLite database using parameterized SQL."""
    idx = extract_index_fields(event)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, timestamp, event_type, source_type, source_id,
                    actor_id, zone_id, device_id, confidence, raw_ref,
                    raw_json, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event["event_id"],
                    event["timestamp"],
                    event["event_type"],
                    idx["source_type"],
                    idx["source_id"],
                    idx["actor_id"],
                    idx["zone_id"],
                    idx["device_id"],
                    float(event.get("confidence", 1.0)),
                    event.get("raw_ref"),
                    raw_json,
                    ingested_at,
                ),
            )
    finally:
        conn.close()


def event_exists_record(db_path: Path | str, event_id: str) -> bool:
    """Check if an event_id already exists in SQLite."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT 1 FROM events WHERE event_id = ? LIMIT 1;", (event_id,)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_event_record(db_path: Path | str, event_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an event by ID from SQLite and reconstruct original dict."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT raw_json FROM events WHERE event_id = ? LIMIT 1;", (event_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row["raw_json"])
    finally:
        conn.close()


def query_event_records(
    db_path: Path | str,
    limit: int = DEFAULT_QUERY_LIMIT,
    offset: int = 0,
    since: Optional[str] = None,
    until: Optional[str] = None,
    event_type: Optional[str] = None,
    source: Optional[str] = None,
    zone_id: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query events from SQLite with deterministic sorting (timestamp ASC, event_id ASC).
    Supports filtering by time range, event_type, source, zone_id, and actor_id.
    """
    conn = get_connection(db_path)
    query_parts = ["SELECT raw_json FROM events WHERE 1=1"]
    params: List[Any] = []

    if since:
        query_parts.append("AND timestamp >= ?")
        params.append(since)
    if until:
        query_parts.append("AND timestamp <= ?")
        params.append(until)
    if event_type:
        query_parts.append("AND event_type = ?")
        params.append(event_type)
    if source:
        query_parts.append("AND (source_type = ? OR source_id = ?)")
        params.extend([source, source])
    if zone_id:
        query_parts.append("AND zone_id = ?")
        params.append(zone_id)
    if actor_id:
        query_parts.append("AND actor_id = ?")
        params.append(actor_id)

    # Deterministic sorting requirement: timestamp ascending, tie-breaker event_id ascending
    query_parts.append("ORDER BY timestamp ASC, event_id ASC")

    # Limit / Offset clamping
    safe_limit = min(max(1, limit), MAX_QUERY_LIMIT)
    safe_offset = max(0, offset)

    query_parts.append("LIMIT ? OFFSET ?")
    params.extend([safe_limit, safe_offset])

    sql = " ".join(query_parts)

    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [json.loads(row["raw_json"]) for row in rows]
    finally:
        conn.close()
