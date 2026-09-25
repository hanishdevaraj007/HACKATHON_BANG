"""
Backend Event Ingestion Test Suite.

Validates schema enforcement, SQLite persistence, duplicate detection, deterministic
timestamp sorting, tie-breaking, filtering, server restart persistence, and FastAPI REST endpoints.

OWNED BY: Backend Team (Component B)
Run with: python -m pytest tests/test_backend_ingestion.py -v
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app import app, get_event_store
from backend.ingestion import DuplicateEventError, EventPublisher, EventStore, ValidationError, validate_event


# ---------------------------------------------------------------------------
# Fixtures for valid event payloads matching schema/event.schema.json
# ---------------------------------------------------------------------------
@pytest.fixture
def camera_event():
    return {
        "event_id": "a1b2c3d4-e5f6-4a7b-8c9d-0123456789ab",
        "timestamp": "2025-03-15T10:00:00Z",
        "event_type": "person_enter",
        "source": {"source_type": "camera", "source_id": "CAM-Z0-01", "source_name": "Lobby Camera 01"},
        "actor": {
            "entity_type": "person",
            "entity_id": "P001",
            "entity_name": "Alice Chen",
            "badge_id": "B-1001",
            "account_id": "achen",
            "track_id": "trk_991",
        },
        "target": {"entity_type": "zone", "entity_id": "Z0", "entity_name": "Lobby / Reception"},
        "object": None,
        "device": {"device_id": "CAM-Z0-01", "device_type": "camera", "device_name": "Lobby Camera 01"},
        "location": {"zone_id": "Z0", "zone_name": "Lobby / Reception"},
        "attributes": {"detection_class": "person", "direction": "inbound"},
        "confidence": 0.95,
        "raw_ref": "frames/cam_z0_01/frame_001.jpg",
    }


@pytest.fixture
def badge_event():
    return {
        "event_id": "b2c3d4e5-f6a7-4b8c-9d0e-123456789abc",
        "timestamp": "2025-03-15T10:01:00Z",
        "event_type": "badge_swipe",
        "source": {"source_type": "badge_reader", "source_id": "BADGE-Z1-ENTRY", "source_name": "Office Gate"},
        "actor": {
            "entity_type": "person",
            "entity_id": "P002",
            "entity_name": "Bob Martinez",
            "badge_id": "B-1002",
            "account_id": "bmartinez",
            "track_id": None,
        },
        "target": {"entity_type": "door", "entity_id": "DOOR-Z1-01", "entity_name": "Office Main Door"},
        "object": {"object_type": "badge", "object_id": "B-1002", "object_description": "RFID Badge"},
        "device": {"device_id": "BADGE-Z1-ENTRY", "device_type": "badge_reader"},
        "location": {"zone_id": "Z1", "zone_name": "Employee Offices"},
        "attributes": {"access_result": "granted", "auth_method": "badge"},
        "confidence": 1.0,
        "raw_ref": "logs/badge/gate_01.log",
    }


@pytest.fixture
def endpoint_event():
    return {
        "event_id": "c3d4e5f6-a7b8-4c9d-8e1f-2a3b4c5d6e7f",
        "timestamp": "2025-03-15T10:02:00Z",
        "event_type": "usb_insert",
        "source": {"source_type": "endpoint_agent", "source_id": "WS-Z1-01", "source_name": "Workstation Z1-01"},
        "actor": {
            "entity_type": "account",
            "entity_id": "P001",
            "entity_name": "Alice Chen",
            "badge_id": "B-1001",
            "account_id": "achen",
            "track_id": None,
        },
        "target": {"entity_type": "workstation", "entity_id": "WS-Z1-01", "entity_name": "Research Terminal"},
        "object": {"object_type": "usb_device", "object_id": "USB-9921", "object_description": "Flash Drive"},
        "device": {"device_id": "WS-Z1-01", "device_type": "workstation"},
        "location": {"zone_id": "Z1", "zone_name": "Employee Offices"},
        "attributes": {"usb_vendor": "SanDisk", "capacity_gb": 32},
        "confidence": 1.0,
        "raw_ref": "sysmon/usb_insert.log",
    }


@pytest.fixture
def network_event():
    return {
        "event_id": "d4e5f6a7-b8c9-4d0e-8f2a-3b4c5d6e7f8a",
        "timestamp": "2025-03-15T10:03:00Z",
        "event_type": "network_transfer",
        "source": {"source_type": "network_monitor", "source_id": "FW-CORE-01", "source_name": "Core Firewall"},
        "actor": {
            "entity_type": "account",
            "entity_id": "P003",
            "entity_name": "Carol Okafor",
            "badge_id": "B-1003",
            "account_id": "cokafor",
            "track_id": None,
        },
        "target": {"entity_type": "network_resource", "entity_id": "EXT-STORAGE"},
        "object": None,
        "device": {"device_id": "FW-CORE-01", "device_type": "firewall"},
        "location": {"zone_id": "Z4", "zone_name": "Core Server Room"},
        "attributes": {"direction": "outbound", "bytes_transferred": 50000000},
        "confidence": 1.0,
        "raw_ref": "netflow/flow_01.json",
    }


@pytest.fixture
def temp_store(tmp_path):
    """Provide an EventStore backed by a temporary SQLite file."""
    db_file = tmp_path / "test_events.db"
    return EventStore(db_path=db_file)


# ===========================================================================
# Unit Tests (Tests 1 - 14)
# ===========================================================================

def test_1_valid_camera_event_accepted(temp_store, camera_event):
    """TEST 1: Valid camera event accepted."""
    result = temp_store.insert(camera_event)
    assert result["event_id"] == camera_event["event_id"]
    assert result["event_type"] == "person_enter"


def test_2_valid_badge_event_accepted(temp_store, badge_event):
    """TEST 2: Valid badge event accepted."""
    result = temp_store.insert(badge_event)
    assert result["event_id"] == badge_event["event_id"]
    assert result["event_type"] == "badge_swipe"


def test_3_valid_endpoint_event_accepted(temp_store, endpoint_event):
    """TEST 3: Valid endpoint event accepted."""
    result = temp_store.insert(endpoint_event)
    assert result["event_id"] == endpoint_event["event_id"]
    assert result["event_type"] == "usb_insert"


def test_4_valid_network_event_accepted(temp_store, network_event):
    """TEST 4: Valid network event accepted."""
    result = temp_store.insert(network_event)
    assert result["event_id"] == network_event["event_id"]
    assert result["event_type"] == "network_transfer"


def test_5_invalid_event_rejected(temp_store):
    """TEST 5: Invalid event rejected (missing fields / bad UUID / bad type)."""
    invalid_event = {
        "event_id": "not-a-valid-uuid",
        "timestamp": "2025-03-15T10:00:00Z",
        "event_type": "invalid_event_type_name",
        "source": {"source_type": "camera"}, # missing source_id
    }
    with pytest.raises(ValidationError) as exc_info:
        temp_store.insert(invalid_event)
    
    errors = exc_info.value.errors
    assert len(errors) > 0


def test_6_event_persisted_to_sqlite(temp_store, camera_event):
    """TEST 6: Event persisted to SQLite."""
    temp_store.insert(camera_event)
    assert temp_store.event_exists(camera_event["event_id"]) is True


def test_7_stored_event_retrieved_exactly(temp_store, camera_event):
    """TEST 7: Stored event can be retrieved exactly."""
    temp_store.insert(camera_event)
    retrieved = temp_store.get_event(camera_event["event_id"])
    assert retrieved == camera_event


def test_8_duplicate_event_handled_deterministically(temp_store, camera_event):
    """TEST 8: Duplicate event handled deterministically (raises DuplicateEventError)."""
    temp_store.insert(camera_event)
    with pytest.raises(DuplicateEventError) as exc_info:
        temp_store.insert(camera_event)
    assert exc_info.value.event_id == camera_event["event_id"]


def test_9_events_sorted_by_timestamp(temp_store, camera_event, badge_event, network_event):
    """TEST 9: Events are sorted by timestamp ascending."""
    # Insert in reverse time order
    network_event["timestamp"] = "2025-03-15T12:00:00Z"
    badge_event["timestamp"] = "2025-03-15T11:00:00Z"
    camera_event["timestamp"] = "2025-03-15T10:00:00Z"

    temp_store.insert(network_event)
    temp_store.insert(badge_event)
    temp_store.insert(camera_event)

    results = temp_store.query(limit=10)
    timestamps = [e["timestamp"] for e in results]
    assert timestamps == ["2025-03-15T10:00:00Z", "2025-03-15T11:00:00Z", "2025-03-15T12:00:00Z"]


def test_10_equal_timestamps_use_deterministic_tie_breaking(temp_store, camera_event, badge_event):
    """TEST 10: Equal timestamps use deterministic tie-breaking (event_id ascending)."""
    same_time = "2025-03-15T12:00:00Z"
    camera_event["timestamp"] = same_time
    badge_event["timestamp"] = same_time

    # Set distinct event_ids
    camera_event["event_id"] = "11111111-2222-4333-8444-555555555555"
    badge_event["event_id"]  = "00000000-2222-4333-8444-555555555555"

    # Insert camera first, then badge
    temp_store.insert(camera_event)
    temp_store.insert(badge_event)

    results = temp_store.query(limit=10)
    ids = [e["event_id"] for e in results]
    # '0000...' comes before '1111...' alphabetically
    assert ids == ["00000000-2222-4333-8444-555555555555", "11111111-2222-4333-8444-555555555555"]


def test_11_filtering_by_event_type(temp_store, camera_event, badge_event):
    """TEST 11: Filtering by event_type works."""
    temp_store.insert(camera_event)
    temp_store.insert(badge_event)

    camera_results = temp_store.query(event_type="person_enter")
    assert len(camera_results) == 1
    assert camera_results[0]["event_id"] == camera_event["event_id"]

    badge_results = temp_store.query(event_type="badge_swipe")
    assert len(badge_results) == 1
    assert badge_results[0]["event_id"] == badge_event["event_id"]


def test_12_filtering_by_actor(temp_store, camera_event, badge_event):
    """TEST 12: Filtering by actor works."""
    camera_event["actor"]["entity_id"] = "P001"
    badge_event["actor"]["entity_id"] = "P002"

    temp_store.insert(camera_event)
    temp_store.insert(badge_event)

    p1_results = temp_store.query(actor_id="P001")
    assert len(p1_results) == 1
    assert p1_results[0]["actor"]["entity_id"] == "P001"

    p2_results = temp_store.query(actor_id="P002")
    assert len(p2_results) == 1
    assert p2_results[0]["actor"]["entity_id"] == "P002"


def test_13_filtering_by_zone(temp_store, camera_event, network_event):
    """TEST 13: Filtering by zone works."""
    camera_event["location"]["zone_id"] = "Z0"
    network_event["location"]["zone_id"] = "Z4"

    temp_store.insert(camera_event)
    temp_store.insert(network_event)

    z0_results = temp_store.query(zone_id="Z0")
    assert len(z0_results) == 1
    assert z0_results[0]["event_id"] == camera_event["event_id"]

    z4_results = temp_store.query(zone_id="Z4")
    assert len(z4_results) == 1
    assert z4_results[0]["event_id"] == network_event["event_id"]


def test_14_backend_restart_persists_events(tmp_path, camera_event):
    """TEST 14: Backend restart does not erase persisted events."""
    db_file = tmp_path / "persistent_events.db"

    # First session: insert event
    store1 = EventStore(db_path=db_file)
    store1.insert(camera_event)

    # Simulated restart: create new store instance on same DB file
    store2 = EventStore(db_path=db_file)
    assert store2.event_exists(camera_event["event_id"]) is True

    retrieved = store2.get_event(camera_event["event_id"])
    assert retrieved == camera_event


# ===========================================================================
# API Endpoint Integration Tests (FastAPI TestClient)
# ===========================================================================

@pytest.fixture
def client_with_temp_db(tmp_path):
    """FastAPI TestClient overriding get_event_store dependency with temp DB."""
    db_file = tmp_path / "api_test_events.db"
    store = EventStore(db_path=db_file)
    
    app.dependency_overrides[get_event_store] = lambda: store
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api_health(client_with_temp_db):
    """Test /health and /api/v1/health endpoints."""
    response = client_with_temp_db.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_post_valid_event(client_with_temp_db, camera_event):
    """Test POST /api/v1/events accepts valid event and returns HTTP 201."""
    response = client_with_temp_db.post("/api/v1/events", json=camera_event)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == camera_event["event_id"]


def test_api_post_invalid_event(client_with_temp_db):
    """Test POST /api/v1/events rejects invalid payload with HTTP 422."""
    invalid_event = {"event_id": "bad-id", "event_type": "unknown_type"}
    response = client_with_temp_db.post("/api/v1/events", json=invalid_event)
    assert response.status_code == 422
    assert "error" in response.json()


def test_api_post_duplicate_event(client_with_temp_db, camera_event):
    """Test POST /api/v1/events handles duplicate with HTTP 409 Conflict."""
    res1 = client_with_temp_db.post("/api/v1/events", json=camera_event)
    assert res1.status_code == 201

    res2 = client_with_temp_db.post("/api/v1/events", json=camera_event)
    assert res2.status_code == 409
    assert "Conflict" in res2.json()["error"]


def test_api_get_events_list(client_with_temp_db, camera_event, badge_event):
    """Test GET /api/v1/events lists stored events with pagination and filters."""
    client_with_temp_db.post("/api/v1/events", json=camera_event)
    client_with_temp_db.post("/api/v1/events", json=badge_event)

    response = client_with_temp_db.get("/api/v1/events?limit=10")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert len(body["events"]) == 2


def test_api_get_event_by_id(client_with_temp_db, camera_event):
    """Test GET /api/v1/events/{event_id} retrieves event or 404 if missing."""
    client_with_temp_db.post("/api/v1/events", json=camera_event)

    res_found = client_with_temp_db.get(f"/api/v1/events/{camera_event['event_id']}")
    assert res_found.status_code == 200
    assert res_found.json()["event_id"] == camera_event["event_id"]

    missing_id = "00000000-0000-4000-8000-000000000000"
    res_missing = client_with_temp_db.get(f"/api/v1/events/{missing_id}")
    assert res_missing.status_code == 404


def test_pub_sub_subscriber_notification(temp_store, camera_event):
    """Test EventPublisher notifies subscribers upon event insertion."""
    received = []

    def subscriber(evt):
        received.append(evt)

    temp_store.publisher.subscribe(subscriber)
    temp_store.insert(camera_event)

    assert len(received) == 1
    assert received[0]["event_id"] == camera_event["event_id"]
