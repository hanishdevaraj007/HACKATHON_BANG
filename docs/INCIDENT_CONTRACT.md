# Incident Contract

> **Audience:** All developers and AI agents working on the correlation engine, scoring, or incident display.
> This document defines the incident lifecycle, scoring model, and output schema.

## Incident Lifecycle

```
EVENT                  A normalized event arrives
  ↓
SIGNAL                 Policy engine evaluates → may produce a policy signal
  ↓
CORRELATED ACTIVITY    Correlation FSM groups related signals across time/space/identity
  ↓
INCIDENT               Incident engine assembles evidence, scores, and persists
```

### Important Nuances

- **Critical policy violations may generate an immediate signal.** For example, an unauthorized person badging into a restricted zone (Z3/Z4) produces an `unauthorized_zone_access` signal directly, without needing a second correlated event.
- **Behavioral chains use correlation.** For example, USB insertion + file copy + network transfer builds up over multiple events.
- **Not every alert requires two events.** A single high-severity policy violation is a valid signal on its own.

## The FROZEN Scoring Model

> ⚠️ **DO NOT MODIFY THESE VALUES.** They are the immutable contract.

| Rule | Signal Type | Points |
|------|------------|--------|
| Unauthorized restricted-zone access | `unauthorized_zone_access` | **+25** |
| After-hours activity | `after_hours_activity` | **+15** |
| Sensitive asset interaction | `sensitive_asset_interaction` | **+20** |
| USB activity | `usb_activity` | **+15** |
| Large outbound transfer | `large_outbound_transfer` | **+15** |
| 3+ correlated signals | `multi_signal_correlation` | **+10** |

**Maximum score: 100**

### Severity Bands

| Severity | Score Range |
|----------|-----------|
| LOW | 0 – 29 |
| MEDIUM | 30 – 59 |
| HIGH | 60 – 79 |
| CRITICAL | 80 – 100 |

### Score Is NOT a Probability

- A score of 75 does NOT mean "75% chance of a security incident"
- It means "the deterministic scoring rules assigned 75 points based on observed signals"
- Every score must have a named breakdown explaining which rules fired and why

### Score Breakdown Example

```json
{
  "score": 75,
  "severity": "HIGH",
  "score_breakdown": [
    {
      "rule_name": "unauthorized_zone_access",
      "points": 25,
      "description": "Bob Martinez (P002) accessed Z3-LAB without authorization. Role 'employee' max zone level is 2.",
      "evidence_event_ids": ["07a8b9c0-d1e2-4f3a-4b5c-6d7e8f901213"]
    },
    {
      "rule_name": "usb_activity",
      "points": 15,
      "description": "USB device (SanDisk 32GB, serial XYZ789) inserted at workstation WS-Z3L-01 in restricted zone Z3-LAB.",
      "evidence_event_ids": ["07a8b9c0-d1e2-4f3a-4b5c-6d7e8f901213"]
    },
    {
      "rule_name": "sensitive_asset_interaction",
      "points": 20,
      "description": "Confidential file prototype_design_v3.pdf copied to USB drive.",
      "evidence_event_ids": ["18b9c0d1-e2f3-4a4b-5c6d-7e8f90121324"]
    },
    {
      "rule_name": "after_hours_activity",
      "points": 15,
      "description": "Activity occurred at 11:45 UTC, within business hours but USB+file activity in restricted zone elevates concern.",
      "evidence_event_ids": ["07a8b9c0-d1e2-4f3a-4b5c-6d7e8f901213"]
    }
  ]
}
```

## Incident Schema

The full JSON schema is at `schema/incident.schema.json`.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | string | Format: `INC-{8-char-hex}` |
| `created_at` | string (ISO 8601 UTC) | When the incident was first created |
| `updated_at` | string (ISO 8601 UTC) | Most recent update |
| `status` | enum | `open`, `investigating`, `escalated`, `resolved`, `false_positive` |
| `severity` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `score` | integer (0-100) | Deterministic risk score |
| `score_breakdown` | array | Named breakdown of every scoring rule that fired |
| `title` | string | Short human-readable title |
| `signals` | array | Policy signals that contributed |
| `events` | array | Event IDs composing the evidence |
| `entities` | object | Resolved entities involved |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string or null | Detailed description (may be LLM-generated) |
| `evidence_graph` | object or null | Lightweight in-memory evidence graph |
| `timeline` | array or null | Chronological evidence timeline |
| `llm_narrative` | string or null | Optional LLM summary (NEVER load-bearing) |

## Evidence Graph

The evidence graph is a lightweight in-memory structure with nodes and edges. **No graph database.**

```json
{
  "evidence_graph": {
    "nodes": [
      {"id": "P002", "type": "person", "label": "Bob Martinez"},
      {"id": "Z3-LAB", "type": "zone", "label": "R&D Laboratory"},
      {"id": "USB-SN-XYZ789", "type": "object", "label": "USB Drive"}
    ],
    "edges": [
      {"source": "P002", "target": "Z3-LAB", "relationship": "accessed", "timestamp": "2025-03-15T11:45:00Z"},
      {"source": "P002", "target": "USB-SN-XYZ789", "relationship": "inserted", "timestamp": "2025-03-15T11:45:00Z"}
    ]
  }
}
```

## Evidence Timeline

```json
{
  "timeline": [
    {"timestamp": "2025-03-15T11:45:00Z", "description": "USB device inserted at WS-Z3L-01", "event_id": "07a8...", "zone_id": "Z3-LAB"},
    {"timestamp": "2025-03-15T11:47:30Z", "description": "Confidential file copied to USB", "event_id": "18b9...", "zone_id": "Z3-LAB"}
  ]
}
```

## Correlation Model

MVP correlation uses:

- **Finite state machines** — deterministic, auditable state transitions
- **Temporal constraints** — events must occur within a configurable time window
- **Spatial constraints** — events must occur in related zones
- **Identity relationships** — events must involve the same resolved actor
- **Policy context** — zone authorization and business hours
- **Object relationships** — same USB device, same file
- **Device relationships** — same workstation, same network segment
- **Deterministic explainable scoring** — every point is traceable to a rule and evidence

## Entity Model

The system tracks these entity types:

| Entity | Description | Example ID |
|--------|-------------|------------|
| Person | Physical individual | P001 |
| Badge | Physical access card | B-1001 |
| Account | Digital identity | achen |
| Device | Hardware device | WS-Z1-02 |
| IP | Network address | 10.0.1.102 |
| CameraTrack | Visual tracking ID | TRK-20250315-001 |
| Object | Physical/digital object | USB-SN-XYZ789 |
| Zone | Physical area | Z3-LAB |
| Asset | Protected resource | ASSET-PROTOTYPE-A |

### Identity Resolution Heuristic

The MVP identity resolution is:

```
camera_track + zone + time_proximity + badge_activity = resolved_identity
```

This means:
1. Camera sees a person (track ID assigned)
2. Person is in a specific zone
3. A badge swipe occurs at the same zone within ±30 seconds
4. Therefore, the camera track likely corresponds to the badge holder

**This is NOT biometric re-identification.** See `docs/KNOWN_LIMITATIONS.md`.

## Python Constants

The scoring constants are also available in `backend/contracts.py`:

```python
from backend.contracts import SCORING_RULES, MAX_SCORE, SEVERITY_BANDS, get_severity

score = SCORING_RULES["unauthorized_zone_access"]  # 25
severity = get_severity(75)  # "HIGH"
```
