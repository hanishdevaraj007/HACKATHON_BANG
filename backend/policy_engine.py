import uuid
from datetime import datetime
from typing import Any, Dict, List

from backend.contracts import load_zone_config, load_organization_config

class PolicyEngine:
    """
    Evaluates events against organization and zone policies.
    Returns a list of 'policy_violation' events for any detected rule breaks.
    """
    
    def __init__(self):
        self.zone_config = load_zone_config()
        self.org_config = load_organization_config()
        
        # Build lookups
        self.zones = {z["zone_id"]: z for z in self.zone_config.get("zones", [])}
        self.persons = {p["person_id"]: p for p in self.org_config.get("persons", [])}

    def evaluate_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate an enriched event. If policies are violated, returns
        new event dictionaries of type 'policy_violation'.
        """
        violations = []
        
        actor = event.get("actor")
        location = event.get("location")
        event_type = event.get("event_type")
        timestamp_str = event.get("timestamp")
        
        try:
            # Python 3.11+ can parse Z, replacing just in case
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return []
            
        person_id = actor.get("entity_id") if isinstance(actor, dict) else None
        zone_id = location.get("zone_id") if isinstance(location, dict) else None
        
        # We need both person and zone for most policy checks
        if not person_id or not zone_id:
            return []
            
        zone = self.zones.get(zone_id)
        person = self.persons.get(person_id)
        
        if not zone or not person:
            return []
            
        role = person.get("role")
        
        # 1. Access Authorization Check
        authorized = False
        if role in zone.get("authorized_roles", []):
            authorized = True
        if person_id in zone.get("authorized_persons", []):
            authorized = True
            
        if not authorized:
            # UNAUTHORIZED ACCESS (+25)
            violations.append(self._create_violation(
                event,
                violation_type="unauthorized_zone_access",
                score=25,
                description=f"Person {person_id} (role: {role}) unauthorized in zone {zone_id}"
            ))

        # 2. Allowed Hours Check
        allowed_hours = zone.get("allowed_hours")
        if allowed_hours:
            start_str = allowed_hours.get("start", "00:00")
            end_str = allowed_hours.get("end", "23:59")
            try:
                sh, sm = map(int, start_str.split(':'))
                eh, em = map(int, end_str.split(':'))
                start_time = sh * 60 + sm
                end_time = eh * 60 + em
                event_time = dt.hour * 60 + dt.minute
                
                # Standard day shift
                if start_time < end_time:
                    if not (start_time <= event_time <= end_time):
                        violations.append(self._create_violation(
                            event,
                            violation_type="after_hours_activity",
                            score=15,
                            description=f"Activity outside allowed hours ({start_str}-{end_str}) in {zone_id}"
                        ))
                # Night shift crossing midnight
                else:
                    if not (event_time >= start_time or event_time <= end_time):
                        violations.append(self._create_violation(
                            event,
                            violation_type="after_hours_activity",
                            score=15,
                            description=f"Activity outside allowed hours ({start_str}-{end_str}) in {zone_id}"
                        ))
            except Exception:
                pass # Malformed hours config

        # 3. Asset Sensitivity Check
        target = event.get("target")
        is_sensitive = False
        if event_type == "file_access":
            attrs = event.get("attributes", {})
            if attrs.get("classification") in ["confidential", "secret", "top_secret"]:
                is_sensitive = True
        elif target and target.get("entity_type") == "asset":
            if target.get("entity_id") in zone.get("assets", []) and zone.get("level", 0) >= 3:
                is_sensitive = True
                
        if is_sensitive:
            violations.append(self._create_violation(
                event,
                violation_type="sensitive_asset_interaction",
                score=20,
                description=f"Interaction with sensitive asset/file in {zone_id}"
            ))

        # 4. USB Policy Check
        if event_type == "usb_insert":
            if zone.get("level", 0) >= 2:
                violations.append(self._create_violation(
                    event,
                    violation_type="usb_activity",
                    score=15,
                    description=f"USB inserted in level {zone.get('level')} zone"
                ))

        # 5. Network Transfer Check
        if event_type == "network_transfer":
            attrs = event.get("attributes", {})
            direction = attrs.get("direction")
            bytes_transferred = attrs.get("bytes_transferred", 0)
            
            # Default threshold: 100 MB
            if direction == "outbound" and bytes_transferred > 104857600:
                violations.append(self._create_violation(
                    event,
                    violation_type="large_outbound_transfer",
                    score=15,
                    description=f"Large outbound transfer: {bytes_transferred} bytes"
                ))
                
        return violations

    def _create_violation(self, trigger_event: dict, violation_type: str, score: int, description: str) -> dict:
        """Create a valid event dictionary for the policy violation."""
        return {
            "event_id": str(uuid.uuid4()),
            "timestamp": trigger_event["timestamp"],
            "event_type": "policy_violation",
            "source": {
                "source_type": "access_control",
                "source_id": "policy_engine",
                "source_name": "Policy Engine"
            },
            "actor": trigger_event.get("actor"),
            "location": trigger_event.get("location"),
            "attributes": {
                "violation_type": violation_type,
                "score": score,
                "description": description,
                "trigger_event_id": trigger_event["event_id"]
            },
            "confidence": 1.0,
            "raw_ref": None
        }
