import pytest
from datetime import datetime
import uuid

from backend.correlation.bag_handoff_fsm import BagHandoffFSM
from backend.correlation.exfiltration_fsm import ExfiltrationFSM
from backend.correlation.coordinator import CorrelationCoordinator

def test_bag_handoff_fsm_success():
    coordinator = CorrelationCoordinator()
    
    # 1. Person A places bag
    evt1 = {
        "event_id": "evt1",
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "object_place",
        "actor": {"entity_id": "P001"},
        "object": {"object_id": "BAG_01"},
        "location": {"zone_id": "Z1"}
    }
    
    activities = coordinator.process_event(evt1)
    assert len(activities) == 0
    assert "BAG_01" in coordinator.bag_fsms
    assert coordinator.bag_fsms["BAG_01"].state == "PLACED"
    
    # 2. Object becomes unattended
    evt2 = {
        "event_id": "evt2",
        "timestamp": "2025-03-15T12:01:00Z",
        "event_type": "object_unattended",
        "actor": {"entity_id": "P001"}, # Not always present, but for simplicity
        "object": {"object_id": "BAG_01"},
        "location": {"zone_id": "Z1"}
    }
    
    activities = coordinator.process_event(evt2)
    assert len(activities) == 0
    assert coordinator.bag_fsms["BAG_01"].state == "UNATTENDED"
    
    # 3. Person B picks up bag
    evt3 = {
        "event_id": "evt3",
        "timestamp": "2025-03-15T12:02:00Z",
        "event_type": "object_pickup",
        "actor": {"entity_id": "P002"},
        "object": {"object_id": "BAG_01"},
        "location": {"zone_id": "Z1"}
    }
    
    activities = coordinator.process_event(evt3)
    assert len(activities) == 0
    assert coordinator.bag_fsms["BAG_01"].state == "RETRIEVED"
    
    # 4. Person B exits
    evt4 = {
        "event_id": "evt4",
        "timestamp": "2025-03-15T12:03:00Z",
        "event_type": "person_exit",
        "actor": {"entity_id": "P002"},
        "location": {"zone_id": "Z1"}
    }
    
    activities = coordinator.process_event(evt4)
    assert len(activities) == 1
    
    act = activities[0]
    assert act.pattern == "unattended_object_handoff"
    assert act.actor_id == "P002"
    assert act.object_id == "BAG_01"
    assert "evt1" in act.evidence_event_ids
    assert "evt3" in act.evidence_event_ids
    assert act.state == "COMPLETED"

def test_bag_handoff_fsm_same_person():
    coordinator = CorrelationCoordinator()
    
    evt1 = {
        "event_id": "evt1",
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "object_place",
        "actor": {"entity_id": "P001"},
        "object": {"object_id": "BAG_02"},
        "location": {"zone_id": "Z1"}
    }
    coordinator.process_event(evt1)
    
    evt2 = {
        "event_id": "evt2",
        "timestamp": "2025-03-15T12:01:00Z",
        "event_type": "object_unattended",
        "object": {"object_id": "BAG_02"},
        "location": {"zone_id": "Z1"}
    }
    coordinator.process_event(evt2)
    
    # P001 picks it up again - shouldn't trigger handoff
    evt3 = {
        "event_id": "evt3",
        "timestamp": "2025-03-15T12:02:00Z",
        "event_type": "object_pickup",
        "actor": {"entity_id": "P001"},
        "object": {"object_id": "BAG_02"},
        "location": {"zone_id": "Z1"}
    }
    activities = coordinator.process_event(evt3)
    assert len(activities) == 0
    assert "BAG_02" in coordinator.bag_fsms
    assert coordinator.bag_fsms["BAG_02"].state == "EXPIRED"

def test_exfiltration_sequence():
    coordinator = CorrelationCoordinator()
    
    # 1. Zone activity
    evt1 = {
        "event_id": "evt1",
        "timestamp": "2025-03-15T12:00:00Z",
        "event_type": "person_enter",
        "actor": {"entity_id": "P003"},
        "location": {"zone_id": "Z3"}
    }
    activities = coordinator.process_event(evt1)
    assert len(activities) == 0
    assert coordinator.exfil_fsms["P003"].state == "ZONE_ACTIVITY"
    
    # 2. USB activity
    evt2 = {
        "event_id": "evt2",
        "timestamp": "2025-03-15T12:01:00Z",
        "event_type": "usb_insert",
        "actor": {"entity_id": "P003"},
        "device": {"device_id": "WS-01"},
        "location": {"zone_id": "Z3"}
    }
    coordinator.process_event(evt2)
    assert coordinator.exfil_fsms["P003"].state == "USB_ACTIVITY"
    
    # 3. Policy violation enriches it
    evt_pol = {
        "event_id": "pol_1",
        "timestamp": "2025-03-15T12:01:00Z",
        "event_type": "policy_violation",
        "actor": {"entity_id": "P003"},
        "attributes": {
            "violation_type": "usb_activity",
            "trigger_event_id": "evt2"
        }
    }
    coordinator.process_event(evt_pol)
    assert "pol_1" in coordinator.exfil_fsms["P003"].evidence_event_ids
    
    # 4. Sensitive file read
    evt3 = {
        "event_id": "evt3",
        "timestamp": "2025-03-15T12:02:00Z",
        "event_type": "file_access",
        "actor": {"entity_id": "P003"},
        "attributes": {"classification": "confidential"}
    }
    coordinator.process_event(evt3)
    assert coordinator.exfil_fsms["P003"].state == "SENSITIVE_FILE_ACCESS"
    
    # 5. Large outbound transfer
    evt4 = {
        "event_id": "evt4",
        "timestamp": "2025-03-15T12:03:00Z",
        "event_type": "network_transfer",
        "actor": {"entity_id": "P003"},
        "attributes": {
            "direction": "outbound",
            "bytes_transferred": 200000000
        }
    }
    activities = coordinator.process_event(evt4)
    assert len(activities) == 1
    
    act = activities[0]
    assert act.pattern == "data_exfiltration_sequence"
    assert act.actor_id == "P003"
    assert "evt1" in act.evidence_event_ids
    assert "pol_1" in act.evidence_event_ids
    assert "evt4" in act.evidence_event_ids
    assert act.state == "COMPLETED"
