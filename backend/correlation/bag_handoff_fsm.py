import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from backend.correlation.models import CorrelatedActivity, Relationship

class BagHandoffFSM:
    TIMEOUT_SECONDS = 300  # 5 minutes

    def __init__(self, object_id: str):
        self.object_id = object_id
        self.correlation_id = f"CORR-BAG-{uuid.uuid4().hex[:8]}"
        self.state = "UNKNOWN"
        
        self.placer_id: Optional[str] = None
        self.retriever_id: Optional[str] = None
        self.zone_id: Optional[str] = None
        
        self.started_at: Optional[datetime] = None
        self.last_updated_at: Optional[datetime] = None
        
        # Deduplicated evidence
        self.evidence_event_ids = set()
        self.matched_rules = set()

    def process_event(self, event: Dict[str, Any]) -> Optional[CorrelatedActivity]:
        """
        Processes an event and returns a CorrelatedActivity if the FSM reaches a terminal success state.
        Returns None if still in progress or expired/irrelevant.
        """
        event_type = event.get("event_type")
        timestamp_str = event.get("timestamp")
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

        # Expire check
        if self.last_updated_at and (dt - self.last_updated_at).total_seconds() > self.TIMEOUT_SECONDS:
            self.state = "EXPIRED"
            return None

        actor = event.get("actor") or {}
        actor_id = actor.get("entity_id") or actor.get("track_id")
        loc = event.get("location") or {}
        evt_zone_id = loc.get("zone_id")

        if self.state == "UNKNOWN":
            if event_type == "object_place":
                # Ensure object_id matches
                obj = event.get("object") or {}
                if obj.get("object_id") == self.object_id:
                    self.state = "PLACED"
                    self.placer_id = actor_id
                    self.zone_id = evt_zone_id
                    self.started_at = dt
                    self.last_updated_at = dt
                    self.evidence_event_ids.add(event["event_id"])
                    self.matched_rules.add("object_place")

        elif self.state == "PLACED":
            if evt_zone_id != self.zone_id:
                return None  # Ignore events in different zones

            if event_type == "object_unattended":
                obj = event.get("object") or {}
                if obj.get("object_id") == self.object_id:
                    self.state = "UNATTENDED"
                    self.last_updated_at = dt
                    self.evidence_event_ids.add(event["event_id"])
                    self.matched_rules.add("object_unattended")
            
            elif event_type == "person_exit" and actor_id == self.placer_id:
                self.state = "UNATTENDED"
                self.last_updated_at = dt
                self.evidence_event_ids.add(event["event_id"])
                self.matched_rules.add("placer_exit")

        elif self.state == "UNATTENDED":
            if evt_zone_id != self.zone_id:
                return None

            if event_type == "object_pickup":
                obj = event.get("object") or {}
                if obj.get("object_id") == self.object_id:
                    if actor_id != self.placer_id:
                        self.state = "RETRIEVED"
                        self.retriever_id = actor_id
                        self.last_updated_at = dt
                        self.evidence_event_ids.add(event["event_id"])
                        self.matched_rules.add("different_actor_retrieval")
                    else:
                        # Picked up by the same person, not a suspicious handoff
                        self.state = "EXPIRED"

        elif self.state == "RETRIEVED":
            if event_type == "person_exit" and actor_id == self.retriever_id:
                self.state = "REMOVED"
                self.last_updated_at = dt
                self.evidence_event_ids.add(event["event_id"])
                self.matched_rules.add("retriever_exit")
                return self._build_activity(dt)
                
        return None

    def _build_activity(self, completed_dt: datetime) -> CorrelatedActivity:
        relationships = [
            Relationship(**{"from": str(self.placer_id), "relation": "placed", "to": self.object_id}),
            Relationship(**{"from": str(self.retriever_id), "relation": "picked_up", "to": self.object_id})
        ]
        
        return CorrelatedActivity(
            pattern="unattended_object_handoff",
            correlation_id=self.correlation_id,
            actor_id=self.retriever_id, 
            object_id=self.object_id,
            started_at=self.started_at.isoformat().replace("+00:00", "Z"),
            completed_at=completed_dt.isoformat().replace("+00:00", "Z"),
            evidence_event_ids=list(self.evidence_event_ids),
            relationships=relationships,
            matched_rules=list(self.matched_rules),
            state="COMPLETED",
            confidence=0.9,
            metadata={"zone_id": self.zone_id, "placer_id": self.placer_id}
        )
