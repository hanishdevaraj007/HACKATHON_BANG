from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class Relationship(BaseModel):
    from_entity: str = Field(alias="from")
    relation: str
    to_entity: str = Field(alias="to")

    model_config = ConfigDict(populate_by_name=True)

class CorrelatedActivity(BaseModel):
    pattern: str
    correlation_id: str
    actor_id: Optional[str] = None
    object_id: Optional[str] = None
    device_id: Optional[str] = None
    started_at: str
    completed_at: str
    evidence_event_ids: List[str]
    relationships: List[Relationship]
    matched_rules: List[str]
    state: str
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
