# Backend Event Ingestion Subsystem

> **Component:** Security Backend / Correlation (Component B)
> **Ownership:** Component B Team
> **Status:** Operational (Foundation Phase - Ingestion & Store)

---

## 1. Purpose

The Backend Event Ingestion Subsystem provides a durable, validated event storage pipeline for normalized security events emitted by computer vision sensors, access control systems, endpoint agents, and network monitors. 

It validates incoming JSON events against `schema/event.schema.json`, enforces event ID uniqueness, indexes core entity fields, stores events durably in SQLite, and provides both a Python service interface (`EventStore`) and FastAPI REST endpoints (`POST /api/v1/events`, `GET /api/v1/events`).

---

## 2. Input

* **Format:** JSON object conforming to `schema/event.schema.json`
* **Modalities Supported:**
  * **Video / CCTV:** `person_enter`, `person_exit`, `object_place`, `object_pickup`, `object_unattended`
  * **Badge / Access Control:** `badge_swipe`, `door_open`, `door_close`
  * **Endpoint:** `login_success`, `login_failure`, `usb_insert`, `usb_remove`, `file_access`
  * **Network:** `network_transfer`
* **Required Fields:** `event_id` (UUID v4), `timestamp` (ISO 8601 UTC), `event_type`, `source` (`source_type`, `source_id`).

---

## 3. Output

* **Durable Storage:** SQLite record in `events` table.
* **REST Response:**
  * `POST /api/v1/events`: HTTP 201 Created returning stored event object.
  * `GET /api/v1/events`: HTTP 200 OK returning paginated JSON list of events sorted deterministically.
  * `GET /api/v1/events/{event_id}`: HTTP 200 OK returning exact event dict.
* **Pub-Sub Notifications:** Emits live event dictionaries to registered Python `EventPublisher` subscribers for downstream correlation state machines.

---

## 4. API Endpoints

| Method | Endpoint | Status | Description |
|---|---|---|---|
| `GET` | `/health` | 200 | Health check and liveness verification |
| `POST` | `/api/v1/events` | 201 | Ingest and validate a normalized security event |
| `GET` | `/api/v1/events` | 200 | Query stored events (filters: `limit`, `offset`, `since`, `until`, `event_type`, `source`, `zone_id`, `actor_id`) |
| `GET` | `/api/v1/events/{event_id}` | 200 | Retrieve a single event by UUID (404 if missing) |

### Error Responses
* **HTTP 422 Unprocessable Entity:** Payload fails JSON schema validation.
* **HTTP 409 Conflict:** Event with `event_id` already exists.
* **HTTP 404 Not Found:** Event ID does not exist.

---

## 5. Database Design

* **Engine:** SQLite
* **Location:** Default `data/events.db` (configurable via `MERIDIAN_DB_PATH` or `EventStore(db_path=...)`). Excluded from Git via `.gitignore`.
* **Table Schema (`events`):**
  * `event_id` (TEXT PRIMARY KEY)
  * `timestamp` (TEXT NOT NULL, ISO 8601 UTC)
  * `event_type` (TEXT NOT NULL)
  * `source_type` (TEXT NOT NULL)
  * `source_id` (TEXT NOT NULL)
  * `actor_id` (TEXT)
  * `zone_id` (TEXT)
  * `device_id` (TEXT)
  * `confidence` (REAL NOT NULL)
  * `raw_ref` (TEXT)
  * `raw_json` (TEXT NOT NULL, canonical event json)
  * `ingested_at` (TEXT NOT NULL, server arrival time UTC)
* **Indices:** `idx_events_timestamp`, `idx_events_type`, `idx_events_actor`, `idx_events_zone`, `idx_events_source`.
* **Ordering:** All queries return records sorted deterministically by `timestamp ASC, event_id ASC`.

---

## 6. How to Run

### Run FastAPI Dev Server
```powershell
python -m uvicorn backend.app:app --reload --port 8000
```

### Access API Documentation
Open `http://127.0.0.1:8000/docs` in your browser for Swagger UI.

### Python Programmatic Usage
```python
from backend.ingestion import EventStore

store = EventStore()
stored_event = store.insert(event_dict)
events = store.query(event_type="badge_swipe", limit=50)
```

---

## 7. Tests

Run backend ingestion unit tests:
```powershell
python -m pytest tests/test_backend_ingestion.py -v
```

All backend tests execute against isolated temporary SQLite databases and do not require external network, YOLO, or OpenCV assets.

---

## 8. Dependencies

* `Python 3.10+`
* `fastapi`
* `uvicorn`
* `pydantic`
* `jsonschema`
* `sqlite3` (Python standard library)

---

## 9. Ownership

* **Primary Owner:** Backend / Correlation Developer (Component B)
* **Read-Only Contracts Consumed:** `schema/event.schema.json`, `backend/contracts.py`

---

## 10. Known Limitations

* **No Correlation Engine Yet:** This module handles ingestion and storage only. Entity resolution, FSM correlation, and incident scoring are implemented in subsequent tasks.
* **SQLite Concurrency:** SQLite supports single-writer concurrency. For high-volume streaming ingest beyond hackathon scale, a WAL-mode or pooled connection manager would be required.
