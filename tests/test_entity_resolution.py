import uuid
from backend.entity_resolution import EntityResolutionEngine

def test_resolve_badge_swipe():
    engine = EntityResolutionEngine()
    
    # Alice Chen has badge_id "B-1001" and person_id "P001"
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:00Z",
        "event_type": "badge_swipe",
        "source": {"source_type": "badge_reader", "source_id": "BADGE-Z1-ENTRY"},
        "actor": {
            "entity_type": "unknown",
            "badge_id": "B-1001"
        },
        "location": {"zone_id": "Z1"}
    }
    
    resolved = engine.resolve_event(event)
    
    assert resolved["actor"]["entity_type"] == "person"
    assert resolved["actor"]["entity_id"] == "P001"
    assert resolved["actor"]["entity_name"] == "Alice Chen"
    
def test_resolve_account_login():
    engine = EntityResolutionEngine()
    
    # Bob Martinez has account_id "bmartinez" and person_id "P002"
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:00Z",
        "event_type": "login_success",
        "source": {"source_type": "endpoint_agent", "source_id": "WS-Z1-01"},
        "actor": {
            "entity_type": "unknown",
            "account_id": "bmartinez"
        },
        "location": {"zone_id": "Z1"}
    }
    
    resolved = engine.resolve_event(event)
    
    assert resolved["actor"]["entity_type"] == "person"
    assert resolved["actor"]["entity_id"] == "P002"
    assert resolved["actor"]["entity_name"] == "Bob Martinez"
    assert resolved["actor"]["badge_id"] == "B-1002"

def test_resolve_cv_track_proximity():
    engine = EntityResolutionEngine()
    
    # 1. Provide badge swipe
    badge_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:00Z",
        "event_type": "badge_swipe",
        "source": {"source_type": "badge_reader", "source_id": "BADGE-Z1-ENTRY"},
        "actor": {
            "entity_type": "unknown",
            "badge_id": "B-1002" # Bob
        },
        "location": {"zone_id": "Z1"}
    }
    engine.resolve_event(badge_event)
    
    # 2. Provide cv event within 5s in the same zone
    cv_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:03Z",
        "event_type": "person_enter",
        "source": {"source_type": "camera", "source_id": "CAM-Z1-01"},
        "actor": {
            "entity_type": "person",
            "track_id": "TRK-001"
        },
        "location": {"zone_id": "Z1"}
    }
    resolved_cv = engine.resolve_event(cv_event)
    
    assert resolved_cv["actor"]["entity_id"] == "P002"
    assert resolved_cv["actor"]["entity_name"] == "Bob Martinez"

    # 3. Subsequent CV events with same track_id should auto-resolve
    cv_event2 = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:10Z",
        "event_type": "person_exit",
        "source": {"source_type": "camera", "source_id": "CAM-Z1-01"},
        "actor": {
            "entity_type": "person",
            "track_id": "TRK-001"
        },
        "location": {"zone_id": "Z1"}
    }
    resolved_cv2 = engine.resolve_event(cv_event2)
    assert resolved_cv2["actor"]["entity_id"] == "P002"

def test_unresolved_cv_track():
    engine = EntityResolutionEngine()
    
    # CV event without any badge swipe
    cv_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T09:15:03Z",
        "event_type": "person_enter",
        "source": {"source_type": "camera", "source_id": "CAM-Z1-01"},
        "actor": {
            "entity_type": "person",
            "track_id": "TRK-UNKNOWN"
        },
        "location": {"zone_id": "Z1"}
    }
    resolved = engine.resolve_event(cv_event)
    
    # Entity ID should not be set
    assert resolved["actor"].get("entity_id") is None
