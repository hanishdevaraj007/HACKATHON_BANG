import copy
from datetime import datetime
from typing import Any, Dict, Optional

from backend.contracts import load_organization_config

class EntityResolutionEngine:
    """
    Resolves identities (persons) from raw events using configuration and heuristics.
    Outputs a new, schema-compatible enriched event dictionary.
    """

    def __init__(self):
        self.org_config = load_organization_config()
        
        # Build lookup tables from organization.json
        self.badge_to_person = {}
        self.account_to_person = {}
        for person in self.org_config.get("persons", []):
            if person.get("badge_id"):
                self.badge_to_person[person["badge_id"]] = person
            if person.get("account_id"):
                self.account_to_person[person["account_id"]] = person
                
        # In-memory heuristic state
        # track_id -> person_id mapping for CV events
        self.track_to_person: Dict[str, str] = {}
        
        # Keep track of recent badge swipes per zone to correlate with CV tracks
        # zone_id -> list of recent badge_swipe events
        self.recent_badge_swipes: Dict[str, list] = {}
        
    def resolve_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a raw event and returns an enriched copy with resolved actor/target.
        Never mutates the input event.
        """
        enriched = copy.deepcopy(event)
        
        actor = enriched.get("actor")
        if not actor:
            return enriched
            
        event_type = enriched.get("event_type")
        timestamp_str = enriched.get("timestamp")
        
        try:
            # Python 3.11+ can parse "Z" as UTC, but replace to be safe
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return enriched

        # 1. Resolve explicit badge_id
        badge_id = actor.get("badge_id")
        if badge_id and badge_id in self.badge_to_person:
            person = self.badge_to_person[badge_id]
            actor["entity_type"] = "person"
            actor["entity_id"] = person["person_id"]
            actor["entity_name"] = person["name"]
            actor["account_id"] = person.get("account_id")
            
            # Store badge swipe for proximity heuristic
            if event_type == "badge_swipe":
                loc = enriched.get("location") or {}
                zone_id = loc.get("zone_id")
                if zone_id:
                    if zone_id not in self.recent_badge_swipes:
                        self.recent_badge_swipes[zone_id] = []
                    self.recent_badge_swipes[zone_id].append({
                        "timestamp": dt,
                        "person_id": person["person_id"],
                        "name": person["name"],
                        "account_id": person.get("account_id")
                    })
                    # Cleanup old swipes (keep last 5 mins to be safe)
                    self.recent_badge_swipes[zone_id] = [
                        s for s in self.recent_badge_swipes[zone_id] 
                        if (dt - s["timestamp"]).total_seconds() < 300
                    ]

        # 2. Resolve explicit account_id
        elif actor.get("account_id") and actor["account_id"] in self.account_to_person:
            person = self.account_to_person[actor["account_id"]]
            actor["entity_type"] = "person"
            actor["entity_id"] = person["person_id"]
            actor["entity_name"] = person["name"]
            actor["badge_id"] = person.get("badge_id")
            
        # 3. Resolve CV track_id using proximity heuristic
        elif actor.get("track_id"):
            track_id = actor["track_id"]
            
            # If already resolved, just attach it
            if track_id in self.track_to_person:
                person_id = self.track_to_person[track_id]
                # Find person in org config
                person = next((p for p in self.org_config.get("persons", []) if p["person_id"] == person_id), None)
                if person:
                    actor["entity_type"] = "person"
                    actor["entity_id"] = person["person_id"]
                    actor["entity_name"] = person["name"]
                    actor["badge_id"] = person.get("badge_id")
                    actor["account_id"] = person.get("account_id")
            else:
                # Try proximity heuristic for new tracks
                loc = enriched.get("location") or {}
                zone_id = loc.get("zone_id")
                if zone_id and zone_id in self.recent_badge_swipes:
                    for swipe in reversed(self.recent_badge_swipes[zone_id]):
                        diff = abs((dt - swipe["timestamp"]).total_seconds())
                        if diff <= 5.0:  # Within 5 seconds
                            # Match found!
                            self.track_to_person[track_id] = swipe["person_id"]
                            actor["entity_type"] = "person"
                            actor["entity_id"] = swipe["person_id"]
                            actor["entity_name"] = swipe["name"]
                            actor["account_id"] = swipe["account_id"]
                            # Don't break, the last loop gives us the most recent swipe matching condition
                            break

        return enriched
