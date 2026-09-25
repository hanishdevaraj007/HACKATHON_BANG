# Component Boundaries

> **Audience:** All developers and AI agents. Read this BEFORE writing any code.
> This document defines WHO owns WHAT and what you MAY and MAY NOT modify.

## Ownership Model

### MENTOR (Architecture Team)

**Responsibilities:**
- Contracts and schemas (`schema/`, `backend/contracts.py`)
- Integration testing across components
- Architecture decisions (`docs/DECISION_LOG.md`)
- Release testing and demo coordination
- Documentation maintenance (`docs/`)

**Owns:**
- `schema/*`
- `config/*`
- `backend/contracts.py`
- `docs/*`
- `tests/test_foundation.py`
- `README.md`
- `requirements.txt`
- `pytest.ini`
- `.gitignore`

---

### COMPONENT A — CV / Physical Events

**Owner:** Component A developer

**Directory:** `cv/`

**Responsibilities:**
- Video ingestion and frame extraction
- YOLO-based object detection (persons, objects)
- Object tracking across frames
- Camera-to-zone mapping
- Generating normalized events for: `person_enter`, `person_exit`, `object_place`, `object_pickup`
- CV-specific tests in `tests/test_cv_*.py`

**May modify:**
- `cv/*` — Full ownership
- `tests/test_cv_*.py` — Create and modify CV tests
- `data/examples/` — Add CV-specific example data
- `scripts/` — Add CV-specific utility scripts

**May NOT modify:**
- `schema/*` — Request changes through mentor
- `config/*` — Request changes through mentor
- `backend/*` — Belongs to Component B
- `cyber/*` — Belongs to Component B
- `frontend/*` — Belongs to Component C
- `backend/contracts.py` — Shared contract, mentor-owned
- `docs/*` — Request updates through mentor (except adding CV-specific docs within `cv/docs/`)

**Input:** Video frames (from file or simulated feed)

**Output:** Normalized events conforming to `schema/event.schema.json`, submitted to backend via REST API `POST /api/v1/events`

---

### COMPONENT B — Security Intelligence Backend

**Owner:** Component B developer

**Directories:** `backend/`, `cyber/`

**Responsibilities:**
- FastAPI application and REST API
- WebSocket server for real-time push
- Event ingestion and storage (SQLite)
- Entity resolution engine
- Policy evaluation against zone config
- Correlation engine (deterministic FSMs)
- Incident generation and scoring
- Evidence timeline and graph assembly
- Synthetic cyber telemetry generation (`cyber/`)
- Backend-specific tests in `tests/test_backend_*.py`

**May modify:**
- `backend/*` — Full ownership (EXCEPT `backend/contracts.py`)
- `cyber/*` — Full ownership
- `tests/test_backend_*.py` — Create and modify backend tests
- `tests/test_cyber_*.py` — Create and modify cyber tests
- `data/examples/` — Add backend-specific example data
- `scripts/` — Add backend-specific utility scripts

**May NOT modify:**
- `schema/*` — Request changes through mentor
- `config/*` — Request changes through mentor
- `backend/contracts.py` — Shared contract, mentor-owned (propose changes via decision log)
- `cv/*` — Belongs to Component A
- `frontend/*` — Belongs to Component C

**Input:** Normalized events from Component A and synthetic cyber telemetry

**Output:** REST API responses, WebSocket messages conforming to incident schema

---

### COMPONENT C — Dashboard

**Owner:** Component C developer

**Directory:** `frontend/`

**Responsibilities:**
- Dashboard layout and design (vanilla HTML/CSS/JS)
- Real-time event stream display
- Incident list with severity indicators
- Evidence timeline visualization per incident
- Evidence graph visualization per incident
- Scoring breakdown display
- WebSocket connection management
- Frontend-specific tests (if applicable)

**May modify:**
- `frontend/*` — Full ownership
- `tests/test_frontend_*.py` — Create and modify frontend tests
- `assets/*` — Add UI assets (icons, images)

**May NOT modify:**
- `schema/*` — Request changes through mentor
- `config/*` — Request changes through mentor
- `backend/*` — Belongs to Component B
- `cv/*` — Belongs to Component A
- `cyber/*` — Belongs to Component B
- `backend/contracts.py` — Shared contract

**Input:** REST API responses and WebSocket messages from backend

**Output:** Visual dashboard

---

## Shared Resources (Read-Only for Components)

These files are shared across all components and may only be modified by the mentor:

| File/Directory | Purpose | Modifier |
|---------------|---------|----------|
| `schema/event.schema.json` | Event contract | Mentor only |
| `schema/incident.schema.json` | Incident contract | Mentor only |
| `schema/scoring.schema.json` | Scoring contract | Mentor only |
| `config/zones.json` | Zone configuration | Mentor only |
| `config/organization.json` | Org configuration | Mentor only |
| `config/scoring.json` | Scoring rules | Mentor only |
| `backend/contracts.py` | Python constants | Mentor only |

## How to Request a Contract Change

1. Create an entry in `docs/DECISION_LOG.md`
2. Describe: what you need changed, why, and what breaks if it doesn't change
3. Tag it with your component (A/B/C)
4. The mentor reviews and either approves or provides an alternative
5. If approved, the mentor updates all affected files simultaneously

## Integration Points

```
Component A (CV) ──POST /api/v1/events──→ Component B (Backend)
                                              │
                                              ├──→ SQLite (persistence)
                                              ├──→ Correlation Engine
                                              ├──→ Incident Engine
                                              │
Component C (Dashboard) ←──WebSocket /ws──────┘
Component C (Dashboard) ←──GET /api/v1/*──────┘
```
