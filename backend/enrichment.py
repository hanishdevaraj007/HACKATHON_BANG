from typing import Any, Callable, Dict, List, Tuple

from backend.entity_resolution import EntityResolutionEngine
from backend.policy_engine import PolicyEngine


class EnrichmentService:
    """
    Orchestrates the enrichment pipeline:
    1. Entity Resolution (linking tracks/accounts to persons)
    2. Policy Evaluation (checking for zone/hours/assets violations)
    
    Can be hooked up to the EventStore's publisher to process events as they arrive.
    """

    def __init__(self, event_store=None):
        self.resolution_engine = EntityResolutionEngine()
        self.policy_engine = PolicyEngine()
        self.event_store = event_store
        
        # Subscriptions for downstream consumers (like the Correlation Engine)
        # They will receive (enriched_event, list_of_policy_violations)
        self._subscribers: List[Callable[[Dict[str, Any], List[Dict[str, Any]]], None]] = []

    def subscribe(self, callback: Callable[[Dict[str, Any], List[Dict[str, Any]]], None]) -> None:
        """Register a callback fn(enriched_event, violations)."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any], List[Dict[str, Any]]], None]) -> None:
        """Unregister a callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def process_event(self, raw_event: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a single raw event through the enrichment pipeline.
        Returns the enriched event and any generated policy violations.
        """
        # 1. Entity Resolution
        enriched_event = self.resolution_engine.resolve_event(raw_event)
        
        # 2. Policy Evaluation
        violations = self.policy_engine.evaluate_event(enriched_event)
        
        # Optionally persist policy violations back to the event store so they are durable
        # Wait, if we call event_store.insert(), it will publish them back and we might get a loop!
        # To avoid loops, we only persist them if they are not already policy_violation type.
        if self.event_store and raw_event.get("event_type") != "policy_violation":
            for violation in violations:
                try:
                    self.event_store.insert(violation)
                except Exception:
                    # Ignore validation/duplicate errors for generated signals to not block pipeline
                    pass
                    
        # 3. Notify downstream consumers
        for callback in list(self._subscribers):
            try:
                callback(enriched_event, violations)
            except Exception:
                pass
                
        return enriched_event, violations
