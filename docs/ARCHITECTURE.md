# Architecture

> **Audience:** Developers and AI coding agents.
> Read `PROJECT_OVERVIEW.md` first.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        REAL WORLD                                │
│   (cameras, badge readers, workstations, network, people)        │
└────────────┬──────────────┬──────────────┬──────────────────────┘
             │              │              │
             ▼              ▼              ▼
┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
│  CV Pipeline   │ │ Badge/Access   │ │ Cyber Telemetry  │
│  (Component A) │ │ Control        │ │ (Component B)    │
│                │ │ (Component B)  │ │                  │
│  - YOLO detect │ │ - Badge swipes │ │ - Endpoint agent │
│  - Tracking    │ │ - Door events  │ │ - Network monitor│
│  - Zone map    │ │                │ │ - File access    │
└───────┬────────┘ └───────┬────────┘ └────────┬─────────┘
        │                  │                    │
        └──────────────────┼────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  NORMALIZED EVENT BUS   │
              │  (event.schema.json)    │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   ENTITY RESOLUTION     │
              │                         │
              │   camera_track + zone   │
              │   + time + badge        │
              │   = resolved identity   │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  ZONE / POLICY CONTEXT  │
              │                         │
              │  zones.json + org.json  │
              │  + scoring.json         │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   CORRELATION ENGINE    │
              │                         │
              │  Deterministic FSMs     │
              │  Temporal constraints   │
              │  Spatial constraints    │
              │  Identity relationships │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    INCIDENT ENGINE      │
              │                         │
              │  Scoring (FROZEN)       │
              │  Evidence assembly      │
              │  Timeline generation    │
              │  Graph construction     │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    FastAPI Backend       │
              │                         │
              │  REST API  +  WebSocket │
              │  SQLite persistence     │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │      DASHBOARD          │
              │    (Component C)        │
              │                         │
              │  Vanilla HTML/CSS/JS    │
              │  Real-time via WS       │
              │  Evidence timeline      │
              │  Evidence graph viz     │
              └────────────┬────────────┘
                           │
                           ▼ (optional)
              ┌─────────────────────────┐
              │    LLM NARRATIVE        │
              │  (NEVER load-bearing)   │
              │                         │
              │  Structured JSON in →   │
              │  Natural language out   │
              └─────────────────────────┘
```

## Data Flow

### 1. Source Processors → Normalized Events

Each source processor (CV, badge, endpoint, network) converts raw data into normalized events conforming to `schema/event.schema.json`.

**Key rule:** All components MUST emit events through this schema. No component may create its own event format.

### 2. Entity Resolution

The entity resolution layer attempts to link entities across modalities:

```
Camera Track TRK-001 detected entering Z0 at 09:15:00
    + Badge B-1001 swiped at Z0 at 09:14:55
    + Same zone (Z0) + time proximity (5 seconds)
    = Likely the same person (Alice Chen, P001)
```

**This is NOT biometric re-identification.** It is a heuristic based on:
- Camera tracking ID (same track = same person within a camera session)
- Zone overlap (same zone at roughly the same time)
- Time proximity (events within a configurable window)
- Badge activity (badge swipe provides known identity)

### 3. Policy Enrichment

Events are enriched with policy context from zone configuration:
- Is the actor authorized for this zone?
- Is this within allowed hours?
- Does the zone require escort?
- Are there sensitive assets in this zone?

### 4. Correlation Engine

The correlation engine uses **deterministic finite state machines** to detect patterns:

```
STATE: idle
  → badge_swipe(unauthorized zone) → STATE: zone_violation_detected
  → usb_insert(restricted zone) → STATE: data_risk_detected
  
STATE: zone_violation_detected
  → file_access(sensitive asset) → STATE: exfiltration_risk
  → person_exit(same zone) → STATE: resolved (log only)

STATE: data_risk_detected  
  → file_access(copy to USB) → STATE: exfiltration_risk
  → usb_remove(no file copy) → STATE: resolved (log only)

STATE: exfiltration_risk
  → network_transfer(large outbound) → STATE: critical_incident
  → TIMEOUT(30 min) → STATE: generate_incident
```

**Important:** Critical policy violations (e.g., unauthorized zone access) may generate an immediate policy signal without requiring additional correlated events. Behavioral chains use temporal correlation.

### 5. Incident Generation

When the correlation engine reaches an incident-generating state:
1. Collect all contributing events
2. Apply the FROZEN scoring rules
3. Generate the score breakdown
4. Determine severity from score
5. Build the evidence timeline
6. Construct the evidence graph (in-memory, no graph DB)
7. Persist the incident

### 6. API / WebSocket

- **REST API** (`/api/v1/`): CRUD for incidents, events, zones, configuration
- **WebSocket** (`/ws`): Real-time push of new events and incidents to the dashboard

### 7. Dashboard

Vanilla HTML/CSS/JavaScript dashboard displaying:
- Real-time event stream
- Active incidents with severity
- Evidence timeline for each incident
- Evidence graph visualization
- Scoring breakdown

### 8. Optional LLM Narrative

If configured, an LLM generates a natural-language explanation of structured incident JSON. The LLM:
- Receives ONLY the structured incident JSON
- Returns ONLY a text narrative
- Is NEVER in the decision path
- Can be disabled without losing any functionality
- Must not be used for scoring, detection, or correlation

## Database

SQLite with tables for:
- `events` — normalized events
- `incidents` — generated incidents
- `signals` — policy signals

No ORM required for MVP. Direct SQL with parameterized queries.

## API Design (Planned)

```
GET    /api/v1/events              — List events (paginated)
GET    /api/v1/events/{event_id}   — Get single event
POST   /api/v1/events              — Ingest event (from source processors)

GET    /api/v1/incidents           — List incidents (paginated, filterable)
GET    /api/v1/incidents/{id}      — Get single incident with full evidence
PATCH  /api/v1/incidents/{id}      — Update incident status

GET    /api/v1/zones               — List zone configurations
GET    /api/v1/config/scoring      — Get scoring configuration

WS     /ws                         — Real-time event and incident stream
```

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite over PostgreSQL | Single-file DB, zero config, sufficient for hackathon scale |
| FastAPI over Flask | Async support, auto OpenAPI docs, Pydantic validation |
| Vanilla JS over React | No build step, simpler handoff, faster to demo |
| YOLO over custom model | Pre-trained, proven, no training data needed |
| JSON schemas over Protobuf | Human-readable, easy to validate, adequate for scope |
| In-memory graph over Neo4j | No infrastructure dependency, sufficient for evidence viz |
| FSMs over ML correlation | Deterministic, explainable, auditable, appropriate for security |
