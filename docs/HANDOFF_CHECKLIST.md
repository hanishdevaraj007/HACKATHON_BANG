# Developer Handoff Checklist

> **Audience:** Junior developers, incoming contributors, and AI coding agents.
> **Purpose:** Read this checklist before starting any implementation work in this repository.

---

## 1. What is this project?
The **Meridian Security Platform** is a multi-modal security event correlation platform built for a national-level hackathon. It correlates physical activity (CCTV person tracking, object placement/pickup/unattended states, badge swipes) and cyber telemetry (workstation logins, USB insertion, file access, outbound network transfers) across the fictional Meridian Research Campus. It detects security incidents, scores them deterministically on a 0–100 scale, and generates an explainable evidence graph and timeline for human security analysts.

---

## 2. What component do I own?
There are three independent component developer roles:
- **Component A (CV / Physical Video Developer):** Owns `cv/`, `tests/test_cv_*`. Ingests video frames, runs YOLO/tracking, and emits events conforming to `schema/event.schema.json`.
- **Component B (Backend & Security Correlation Developer):** Owns `backend/`, `cyber/`, `tests/test_backend_*`, `tests/test_correlation_*`, `tests/test_cyber_*`. Implements event normalization, entity resolution, zone policy evaluation, correlation FSMs, deterministic incident scoring, and FastAPI REST/WebSocket endpoints.
- **Component C (Frontend / Dashboard Developer):** Owns `frontend/`, `tests/test_frontend_*`. Builds the analyst dashboard using vanilla HTML, modern CSS design tokens, and vanilla JavaScript to render real-time incident alerts, evidence graphs, and replay timelines.

---

## 3. Which files can I modify?
Consult [`docs/COMPONENT_CHANGE_MATRIX.md`](COMPONENT_CHANGE_MATRIX.md) for full permissions. In short:
- **CV Developer:** `cv/*`, `tests/test_cv_*`, local CV test fixtures.
- **Backend Developer:** `backend/*` (except `backend/contracts.py`), `cyber/*`, `tests/test_backend_*`, `tests/test_correlation_*`, `tests/test_cyber_*`.
- **Frontend Developer:** `frontend/*`, `tests/test_frontend_*`, `assets/*`.

---

## 4. Which files must I never modify?
The following are **PROTECTED CONTRACT FILES** owned solely by the mentor/architect:
- `schema/event.schema.json`
- `schema/incident.schema.json`
- `schema/scoring.schema.json`
- `config/organization.json`
- `config/zones.json`
- `config/scoring.json`
- `backend/contracts.py`
- `docs/EVENT_CONTRACT.md`
- `docs/INCIDENT_CONTRACT.md`
- `docs/ZONE_POLICY.md`
- `docs/ARCHITECTURE.md`
- `docs/COMPONENT_BOUNDARIES.md`
- `docs/AI_MULTI_AGENT_COLLABORATION_RULES.md`
- `docs/COMPONENT_CHANGE_MATRIX.md`
- `tests/test_foundation.py`

Component developers and AI agents must treat these as **READ-ONLY**.

---

## 5. What contracts must I read?
Before writing any code, read:
1. [`README.md`](../README.md)
2. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
3. [`docs/COMPONENT_BOUNDARIES.md`](COMPONENT_BOUNDARIES.md)
4. [`docs/AI_MULTI_AGENT_COLLABORATION_RULES.md`](AI_MULTI_AGENT_COLLABORATION_RULES.md)
5. [`docs/EVENT_CONTRACT.md`](EVENT_CONTRACT.md)
6. [`docs/INCIDENT_CONTRACT.md`](INCIDENT_CONTRACT.md)
7. [`docs/ZONE_POLICY.md`](ZONE_POLICY.md)
8. [`docs/COMPONENT_CHANGE_MATRIX.md`](COMPONENT_CHANGE_MATRIX.md)

---

## 6. How do I install dependencies?
Clone the repository and install dependencies using Python:
```powershell
python -m pip install -r requirements.txt
```
For running test suites and schema validation:
```powershell
python -m pip install pytest jsonschema
```

---

## 7. How do I run tests?
To execute the complete test suite:
```powershell
python -m pytest tests/ -v
```
To run only your component tests:
- CV team: `python -m pytest tests/test_cv_*.py -v`
- Backend team: `python -m pytest tests/test_backend_*.py -v`
- Foundation verification: `python -m pytest tests/test_foundation.py -v`

---

## 8. How do I run the backend later?
When Component B implements the FastAPI service:
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```
API documentation will be available at `http://localhost:8000/docs`.
Frontend can connect via WebSocket at `ws://localhost:8000/ws/events` and `ws://localhost:8000/ws/incidents`.

---

## 9. How do I run a scenario later?
Scenario definitions live in `config/scenarios/`:
- `config/scenarios/bag_handoff.json` (Suspicious bag drop and pickup)
- `config/scenarios/exfiltration.json` (Multi-modal insider exfiltration chain)

To replay or validate scenarios:
```powershell
# Cyber simulation / event feeder (when implemented in Component B)
python scripts/simulate_scenario.py --scenario bag_handoff
python scripts/simulate_scenario.py --scenario exfiltration
```

---

## 10. How do I report my work?
At the end of every implementation task, generate a structured report conforming to **Rule 18**:
```markdown
FILES CREATED: [exact list]
FILES MODIFIED: [exact list]
FILES DELETED: [exact list or None]
WHY EACH WAS CHANGED: [rationale]
DEPENDENCIES ADDED: [list or None]
COMMANDS EXECUTED: [list]
TESTS EXECUTED: [exact test command]
ACTUAL TEST RESULTS: [pass/fail count and output summary]
KNOWN FAILURES: [list or None]
KNOWN LIMITATIONS: [list]
UNFINISHED WORK: [list]
NEXT RECOMMENDED TASK: [description]
```

---

## 11. What happens if I need another component?
- **Do not edit another component's files.**
- If you find an API route or schema field missing, submit a proposal to the mentor via `docs/DECISION_LOG.md`.
- In your component code, use an internal adapter or mock/fixture while awaiting mentor review.
- Never write cross-component drive-by changes.
