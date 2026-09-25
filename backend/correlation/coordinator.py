from typing import Dict, Any, List, Optional
from backend.correlation.models import CorrelatedActivity
from backend.correlation.bag_handoff_fsm import BagHandoffFSM
from backend.correlation.exfiltration_fsm import ExfiltrationFSM

class CorrelationCoordinator:
    """
    Routes enriched events and policy signals to active state machines.
    Responsible for creating, tracking, and pruning FSMs.
    """
    def __init__(self):
        # Key: object_id -> BagHandoffFSM
        self.bag_fsms: Dict[str, BagHandoffFSM] = {}
        # Key: actor_id -> ExfiltrationFSM
        self.exfil_fsms: Dict[str, ExfiltrationFSM] = {}

    def process_event(self, event: Dict[str, Any]) -> List[CorrelatedActivity]:
        completed_activities = []
        
        # 1. Routing to Bag Handoff FSMs
        # These are keyed by object_id
        obj = event.get("object") or {}
        object_id = obj.get("object_id")
        
        # Determine if we should create a new Bag FSM (e.g., on object_place)
        if event.get("event_type") == "object_place" and object_id:
            if object_id not in self.bag_fsms:
                self.bag_fsms[object_id] = BagHandoffFSM(object_id)
                
        # Send event to the relevant Bag FSM if it exists
        if object_id and object_id in self.bag_fsms:
            activity = self.bag_fsms[object_id].process_event(event)
            if activity:
                completed_activities.append(activity)
                del self.bag_fsms[object_id]
        
        # Also need to route person_exit to ALL bag FSMs that this person might be involved in
        # For simplicity in MVP, we can broadcast person_exit to all active Bag FSMs
        if event.get("event_type") == "person_exit":
            to_delete = []
            for oid, fsm in self.bag_fsms.items():
                activity = fsm.process_event(event)
                if activity:
                    completed_activities.append(activity)
                    to_delete.append(oid)
                elif fsm.state == "EXPIRED":
                    to_delete.append(oid)
            for oid in to_delete:
                del self.bag_fsms[oid]

        # 2. Routing to Exfiltration FSMs
        # These are keyed by actor_id
        actor = event.get("actor") or {}
        actor_id = actor.get("entity_id") or actor.get("track_id")
        
        if event.get("event_type") == "policy_violation":
            # For policy violation, try to extract actor from the event if not present in root actor
            pass # The FSM handles it if actor_id matches
            
        if actor_id:
            if actor_id not in self.exfil_fsms:
                # Only initialize if we see a valid trigger. IDLE expects person_enter or badge_swipe.
                # Actually, an FSM can just be created lazily.
                if event.get("event_type") in ["person_enter", "badge_swipe"]:
                    self.exfil_fsms[actor_id] = ExfiltrationFSM(actor_id)
            
            if actor_id in self.exfil_fsms:
                activity = self.exfil_fsms[actor_id].process_event(event)
                if activity:
                    completed_activities.append(activity)
                    del self.exfil_fsms[actor_id]
                elif self.exfil_fsms[actor_id].state == "EXPIRED":
                    del self.exfil_fsms[actor_id]

        # General Pruning of expired FSMs could be done here as well on every event if needed
        # But we handle it passively when events are routed.
        
        return completed_activities
