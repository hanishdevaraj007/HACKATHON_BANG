# Decision Log

> **Audience:** All team members and AI agents.
> Record ALL architectural decisions, contract change requests, and rationale here.

## Format

Each entry should include:
- **Date:** YYYY-MM-DD
- **Author:** Who proposed the decision
- **Component:** Mentor / A / B / C
- **Decision:** What was decided
- **Rationale:** Why this decision was made
- **Alternatives Considered:** What else was evaluated
- **Impact:** What components/files are affected

---

## Decisions

### DL-001: Technology Stack Selection
- **Date:** 2025-03-15
- **Author:** Mentor
- **Component:** All
- **Decision:** Use Python/FastAPI/SQLite/OpenCV/YOLO/vanilla HTML/CSS/JS
- **Rationale:** Minimal stack for a hackathon. Easy to run on Windows. No unnecessary infrastructure.
- **Alternatives Considered:** 
  - Django (too heavy for hackathon)
  - PostgreSQL (requires installation)
  - React (build system complexity, learning curve)
  - Neo4j (unnecessary infrastructure for in-memory graph)
- **Impact:** All components

### DL-002: Deterministic Scoring Over ML
- **Date:** 2025-03-15
- **Author:** Mentor
- **Component:** Backend
- **Decision:** Use a deterministic point-based scoring system, not ML-based risk scoring
- **Rationale:** Security scoring must be explainable and auditable. Points can be traced to specific rules and evidence. ML scores are opaque.
- **Alternatives Considered:**
  - Random forest risk classifier (not explainable enough)
  - Bayesian network (too complex for hackathon)
- **Impact:** backend/, scoring config, incident schema

### DL-003: Identity Resolution Without Biometrics
- **Date:** 2025-03-15
- **Author:** Mentor
- **Component:** CV, Backend
- **Decision:** Use zone + time + badge correlation for identity resolution. No face recognition or biometric re-identification.
- **Rationale:** Face recognition is ethically complex, technically unreliable without training data, and not needed for the MVP. Zone/time/badge heuristic is sufficient and honest.
- **Alternatives Considered:**
  - Face recognition (ethical, technical, and accuracy concerns)
  - Gait analysis (unsupported, unreliable)
- **Impact:** cv/, backend/

### DL-004: In-Memory Evidence Graph
- **Date:** 2025-03-15
- **Author:** Mentor
- **Component:** Backend, Frontend
- **Decision:** Evidence graphs are lightweight JSON structures in memory, not a graph database.
- **Rationale:** Neo4j or similar adds infrastructure complexity. The evidence graph for a single incident is small enough to represent as JSON with nodes/edges arrays.
- **Impact:** backend/, frontend/

### DL-005: LLM Is Optional and Never Load-Bearing
- **Date:** 2025-03-15
- **Author:** Mentor
- **Component:** All
- **Decision:** LLM integration is optional. It receives structured incident JSON and returns narrative text. It is never used for detection, scoring, or correlation.
- **Rationale:** Security decisions must be deterministic. LLMs hallucinate. The system must function identically with or without an LLM.
- **Impact:** All components

### DL-006: Inclusion of object_unattended Event Type
- **Date:** 2026-09-25
- **Author:** Mentor / Architect
- **Component:** All (CV, Backend, Contracts)
- **Decision:** Explicitly add `object_unattended` to canonical `event_type` enum in `schema/event.schema.json` and `backend/contracts.py`.
- **Rationale:** Physical scenarios (such as bag drops and suspicious handoffs) require a discrete state transition event when a placed object remains stationary without an associated actor nearby, distinct from the initial placement event.
- **Alternatives Considered:**
  - Repurposing `object_place` with an elapsed time attribute (ambiguous FSM trigger)
  - Treating unattended objects solely as an internal CV alert without publishing an event (breaks multi-modal correlation contract)
- **Impact:** `schema/event.schema.json`, `backend/contracts.py`, `docs/EVENT_CONTRACT.md`, tests and fixtures.

---

## Pending Proposals

_No pending proposals at this time._

---

## Template for New Entries

```
### DL-XXX: [Title]
- **Date:** YYYY-MM-DD
- **Author:** [Name or Component]
- **Component:** [Mentor / A / B / C]
- **Decision:** [What was decided]
- **Rationale:** [Why]
- **Alternatives Considered:** [What else was evaluated]
- **Impact:** [What's affected]
```
