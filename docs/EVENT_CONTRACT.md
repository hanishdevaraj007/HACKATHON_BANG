# Event Contract

> **Audience:** All developers and AI agents working on source processors or event consumers.
> This is the CANONICAL reference for the normalized event schema.

## Purpose

Every source processor — whether it's the CV pipeline analyzing video, a badge reader logging swipes, or an endpoint agent detecting USB insertions — MUST emit events conforming to this single schema.

The schema file is: `schema/event.schema.json`

## Required Fields

These fields are ALWAYS required on every event:

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string (UUID v4) | Globally unique event identifier |
| `timestamp` | string (ISO 8601 UTC) | When the event occurred. ALWAYS UTC. |
| `event_type` | string (enum) | Canonical event type from the allowed list |
| `source` | object | The system/sensor that generated this event |

## Nullable Fields

These fields may be `null` when the information is unavailable:

| Field | Type | When Null |
|-------|------|-----------|
| `actor` | object or null | When the actor is unknown (e.g., unidentified person on camera) |
| `target` | object or null | When there is no target entity |
| `object` | object or null | When no physical/digital object is involved |
| `device` | object or null | When device context is not applicable |
| `location` | object or null | When location cannot be determined |
| `attributes` | object or null | When there are no event-type-specific attributes |
| `raw_ref` | string or null | When no raw evidence reference is available |

## Confidence

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `confidence` | number | 0.0 – 1.0 | Source processor's confidence in the event |

- `1.0` = Deterministic (badge swipe, login event)
- `0.7 – 0.99` = High confidence CV detection
- `0.5 – 0.69` = Moderate confidence
- Below `0.5` = Low confidence, should be flagged

## Allowed Event Types

```
person_enter       — Person detected entering a zone (CV)
person_exit        — Person detected leaving a zone (CV)
object_place       — Object placed/left in a location (CV)
object_pickup      — Object picked up from a location (CV)
object_unattended  — Object stationary with no associated person in proximity (CV)
badge_swipe        — Badge used at a reader (access control)
login_success      — Successful authentication (endpoint)
login_failure      — Failed authentication attempt (endpoint)
usb_insert         — USB device plugged in (endpoint)
usb_remove         — USB device removed (endpoint)
file_access        — File read/write/copy/delete (endpoint)
network_transfer   — Network data transfer (network monitor)
door_open          — Door opened (access control)
door_close         — Door closed (access control)
policy_violation   — Direct policy violation signal (any source)
```

## Source Object

```json
{
    "source_type": "camera",
    "source_id": "CAM-Z0-01",
    "source_name": "Lobby Main Camera"
}
```

Allowed `source_type` values:
- `camera` — CCTV / video feed
- `badge_reader` — Physical badge/card reader
- `endpoint_agent` — Software agent on a workstation
- `network_monitor` — Network monitoring device
- `access_control` — Access control system
- `identity_provider` — Identity/authentication system

## Actor Object

```json
{
    "entity_type": "person",
    "entity_id": "P001",
    "entity_name": "Alice Chen",
    "badge_id": "B-1001",
    "account_id": "achen",
    "track_id": "TRK-20250315-001"
}
```

- `entity_id` may be null when identity is unresolved
- `track_id` is the camera tracking ID — NOT biometric. It only tracks within a single camera session.
- `badge_id` and `account_id` link to known identity when available

## Target Object

```json
{
    "entity_type": "zone",
    "entity_id": "Z0",
    "entity_name": "Lobby / Reception"
}
```

Allowed target `entity_type` values: `zone`, `device`, `file`, `network_resource`, `door`, `workstation`, `server`, `asset`

## Attributes (Per Event Type)

### person_enter / person_exit
```json
{
    "direction": "inbound",
    "detection_class": "person",
    "bbox": [100, 50, 200, 300]
}
```

### object_place / object_pickup / object_unattended
```json
{
    "detection_class": "backpack",
    "action": "unattended",
    "stationary_seconds": 60,
    "nearest_person_distance_m": 4.5
}
```

### badge_swipe
```json
{
    "access_result": "granted",
    "auth_method": "badge"
}
```

### login_success / login_failure
```json
{
    "auth_method": "password+mfa",
    "session_id": "sess-abc123"
}
```

### usb_insert / usb_remove
```json
{
    "usb_vendor": "SanDisk",
    "usb_serial": "XYZ789",
    "capacity_gb": 32
}
```

### file_access
```json
{
    "action": "copy",
    "file_path": "D:\\Research\\prototype.pdf",
    "destination": "E:\\USB_DRIVE\\",
    "file_size_bytes": 15728640,
    "classification": "confidential"
}
```

### network_transfer
```json
{
    "direction": "outbound",
    "protocol": "HTTPS",
    "source_ip": "10.0.3.101",
    "destination_ip": "203.0.113.50",
    "destination_port": 443,
    "bytes_transferred": 524288000,
    "duration_seconds": 120,
    "transfer_label": "SYNTHETIC"
}
```

## Timestamp Rules

1. ALL timestamps MUST be UTC
2. ALL timestamps MUST be ISO 8601 format: `2025-03-15T09:15:00Z`
3. Source processors must convert local time to UTC before emitting events
4. The `Z` suffix is required

## Example Events

See `data/examples/example_events.json` for 9 complete example events covering all required types.

## Validation

To validate an event against the schema:

```python
import json
import jsonschema

with open("schema/event.schema.json") as f:
    schema = json.load(f)

# your_event is a dict
jsonschema.validate(your_event, schema)
```
