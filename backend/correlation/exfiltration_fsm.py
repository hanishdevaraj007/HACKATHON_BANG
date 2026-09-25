import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from backend.correlation.models import CorrelatedActivity, Relationship

class ExfiltrationFSM:
    TIMEOUT_SECONDS = 600  # 10 minutes

    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.correlation_id = f"CORR-EXFIL-{uuid.uuid4().hex[:8]}"
        self.state = "IDLE"
        
        self.started_at: Optional[datetime] = None
        self.last_updated_at: Optional[datetime] = None
        
        self.evidence_event_ids = set()
        self.matched_rules = set()
        
        self.device_id: Optional[str] = None
        self.zone_id: Optional[str] = None

    def process_event(self, event: Dict[str, Any]) -> Optional[CorrelatedActivity]:
        event_type = event.get("event_type")
        timestamp_str = event.get("timestamp")
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

        if self.last_updated_at and (dt - self.last_updated_at).total_seconds() > self.TIMEOUT_SECONDS:
            self.state = "EXPIRED"
            return None

        # Policy violations just enrich our evidence if they involve our actor
        if event_type == "policy_violation":
            attrs = event.get("attributes", {})
            v_type = attrs.get("violation_type")
            source_evt = attrs.get("trigger_event_id")
            
            act = event.get("actor") or {}
            act_id = act.get("entity_id") or act.get("track_id")
            if act_id == self.actor_id and self.state != "IDLE":
                self.evidence_event_ids.add(event["event_id"])
                if source_evt:
                    self.evidence_event_ids.add(source_evt)
                self.matched_rules.add(v_type)
            return None

        actor = event.get("actor") or {}
        actor_id = actor.get("entity_id") or actor.get("track_id")
        
        if actor_id != self.actor_id:
            return None

        loc = event.get("location") or {}
        evt_zone_id = loc.get("zone_id")
        
        device = event.get("device") or {}
        evt_device_id = device.get("device_id")

        if self.state == "IDLE":
            if event_type in ["person_enter", "badge_swipe"]:
                self.state = "ZONE_ACTIVITY"
                self.zone_id = evt_zone_id
                self.started_at = dt
                self.last_updated_at = dt
                self.evidence_event_ids.add(event["event_id"])
                self.matched_rules.add("zone_entry")

        elif self.state == "ZONE_ACTIVITY":
            if event_type == "usb_insert":
                self.state = "USB_ACTIVITY"
                self.device_id = evt_device_id
                self.last_updated_at = dt
                self.evidence_event_ids.add(event["event_id"])
                self.matched_rules.add("usb_insertion")

        elif self.state == "USB_ACTIVITY":
            if event_type == "file_access":
                attrs = event.get("attributes", {})
                if attrs.get("classification") in ["confidential", "secret", "top_secret"]:
                    self.state = "SENSITIVE_FILE_ACCESS"
                    self.last_updated_at = dt
                    self.evidence_event_ids.add(event["event_id"])
                    self.matched_rules.add("sensitive_file_read")

        elif self.state == "SENSITIVE_FILE_ACCESS":
            if event_type == "network_transfer":
                attrs = event.get("attributes", {})
                if attrs.get("direction") == "outbound" and attrs.get("bytes_transferred", 0) > 104857600:
                    self.state = "COMPLETED"
                    self.last_updated_at = dt
                    self.evidence_event_ids.add(event["event_id"])
                    self.matched_rules.add("large_outbound_transfer")
                    return self._build_activity(dt)
                    
        return None

    def _build_activity(self, completed_dt: datetime) -> CorrelatedActivity:
        relationships = [
            Relationship(**{"from": self.actor_id, "relation": "exfiltrated_data_from", "to": str(self.zone_id)})
        ]
        if self.device_id:
            relationships.append(Relationship(**{"from": self.actor_id, "relation": "used_device", "to": self.device_id}))
            
        return CorrelatedActivity(
            pattern="data_exfiltration_sequence",
            correlation_id=self.correlation_id,
            actor_id=self.actor_id,
            device_id=self.device_id,
            started_at=self.started_at.isoformat().replace("+00:00", "Z"),
            completed_at=completed_dt.isoformat().replace("+00:00", "Z"),
            evidence_event_ids=list(self.evidence_event_ids),
            relationships=relationships,
            matched_rules=list(self.matched_rules),
            state="COMPLETED",
            confidence=0.85,
            metadata={"zone_id": self.zone_id}
        )
