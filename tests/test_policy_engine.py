import uuid
from backend.policy_engine import PolicyEngine

def test_unauthorized_zone_access():
    engine = PolicyEngine()
    
    # Bob (P002) role=employee (max zone 2)
    # Z3-LAB is level 3, requires researcher or security_admin
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "person_enter",
        "actor": {
            "entity_type": "person",
            "entity_id": "P002"
        },
        "location": {"zone_id": "Z3-LAB"},
        "source": {"source_type": "camera", "source_id": "CAM-Z3L-01"}
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 1
    assert violations[0]["attributes"]["violation_type"] == "unauthorized_zone_access"
    assert violations[0]["attributes"]["score"] == 25

def test_authorized_zone_access():
    engine = PolicyEngine()
    
    # Alice (P001) role=researcher
    # Z3-LAB allows researchers
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "person_enter",
        "actor": {
            "entity_type": "person",
            "entity_id": "P001"
        },
        "location": {"zone_id": "Z3-LAB"},
        "source": {"source_type": "camera", "source_id": "CAM-Z3L-01"}
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 0

def test_after_hours_access():
    engine = PolicyEngine()
    
    # Alice (P001) in Z3-LAB (allowed 08:00 - 18:00)
    # Event at 21:00Z
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T21:00:00Z",
        "event_type": "person_enter",
        "actor": {
            "entity_type": "person",
            "entity_id": "P001"
        },
        "location": {"zone_id": "Z3-LAB"},
        "source": {"source_type": "camera", "source_id": "CAM-Z3L-01"}
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 1
    assert violations[0]["attributes"]["violation_type"] == "after_hours_activity"
    assert violations[0]["attributes"]["score"] == 15

def test_usb_activity_in_restricted_zone():
    engine = PolicyEngine()
    
    # Bob in Z2
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "usb_insert",
        "actor": {
            "entity_type": "person",
            "entity_id": "P002"
        },
        "location": {"zone_id": "Z2"},
        "source": {"source_type": "endpoint_agent", "source_id": "WS-Z2-01"}
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 1
    assert violations[0]["attributes"]["violation_type"] == "usb_activity"
    assert violations[0]["attributes"]["score"] == 15

def test_sensitive_asset_interaction():
    engine = PolicyEngine()
    
    # Alice accessing confidential file
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "file_access",
        "actor": {
            "entity_type": "person",
            "entity_id": "P001"
        },
        "location": {"zone_id": "Z3-LAB"},
        "source": {"source_type": "endpoint_agent", "source_id": "WS-Z3L-01"},
        "attributes": {
            "classification": "confidential"
        }
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 1
    assert violations[0]["attributes"]["violation_type"] == "sensitive_asset_interaction"
    assert violations[0]["attributes"]["score"] == 20

def test_large_outbound_transfer():
    engine = PolicyEngine()
    
    # Alice transferring 200MB out
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "network_transfer",
        "actor": {
            "entity_type": "person",
            "entity_id": "P001"
        },
        "location": {"zone_id": "Z3-LAB"},
        "source": {"source_type": "network_monitor", "source_id": "FW-CORE-01"},
        "attributes": {
            "direction": "outbound",
            "bytes_transferred": 200000000
        }
    }
    
    violations = engine.evaluate_event(event)
    assert len(violations) == 1
    assert violations[0]["attributes"]["violation_type"] == "large_outbound_transfer"
    assert violations[0]["attributes"]["score"] == 15
