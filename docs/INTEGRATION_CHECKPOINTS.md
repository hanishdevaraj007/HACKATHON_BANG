# Integration Checkpoints

> **Audience:** All team members and mentor.
> These are the milestones where components must prove they work together.

## Overview

Integration happens in phases. Each checkpoint verifies that specific cross-component contracts are working.

---

## Checkpoint 1: Event Ingestion (Components A + B)

**Goal:** Component A can send events to Component B's API.

### Prerequisites
- [ ] Component B has `POST /api/v1/events` endpoint running
- [ ] Component A can generate at least one valid normalized event

### Verification Steps
1. Component A generates a `person_enter` event
2. Event validates against `schema/event.schema.json`
3. Component A sends HTTP POST to `http://localhost:8000/api/v1/events`
4. Component B returns HTTP 201 with the stored event
5. Component B stores the event in SQLite

### Test
```bash
# From Component A, send a test event:
python -c "
import json, httpx
with open('data/examples/example_events.json') as f:
    events = json.load(f)['events']
resp = httpx.post('http://localhost:8000/api/v1/events', json=events[0])
print(resp.status_code, resp.json())
"
```

### Success Criteria
- HTTP 201 response
- Event appears in `GET /api/v1/events`
- No schema validation errors

---

## Checkpoint 2: Real-Time Dashboard (Components B + C)

**Goal:** Component C receives real-time events via WebSocket from Component B.

### Prerequisites
- [ ] Component B has WebSocket endpoint at `/ws`
- [ ] Component C has WebSocket connection logic in `frontend/js/app.js`

### Verification Steps
1. Start Component B backend
2. Open Component C dashboard in browser
3. Connection status shows "Connected"
4. Send an event via POST to Component B
5. Event appears in Component C dashboard in real-time

### Success Criteria
- WebSocket connects successfully
- Events appear within 1 second of ingestion
- Dashboard shows event data correctly

---

## Checkpoint 3: Incident Generation (Component B internal)

**Goal:** The correlation engine produces incidents from multiple events.

### Prerequisites
- [ ] Entity resolution is functional
- [ ] Policy evaluation is functional
- [ ] At least one correlation FSM is implemented

### Verification Steps
1. Send a sequence of events representing unauthorized access + USB insertion
2. Correlation engine detects the pattern
3. Incident is generated with correct scoring
4. Score breakdown lists each contributing rule

### Test Scenario
```
Event 1: badge_swipe — Bob Martinez (employee) at Z3-LAB (unauthorized)
Event 2: usb_insert — bmartinez at WS-Z3L-01 in Z3-LAB
Event 3: file_access — bmartinez copies confidential file to USB

Expected: Incident with score >= 60 (unauthorized_zone_access:25 + usb_activity:15 + sensitive_asset_interaction:20)
```

### Success Criteria
- Incident generated automatically
- Score matches expected calculation
- Score breakdown is correct
- Incident conforms to `schema/incident.schema.json`

---

## Checkpoint 4: Full Pipeline (Components A + B + C)

**Goal:** End-to-end: video → events → correlation → incident → dashboard.

### Prerequisites
- [ ] All previous checkpoints pass
- [ ] Component A processes at least one test video
- [ ] Component B correlation engine is functional
- [ ] Component C displays incidents with evidence

### Verification Steps
1. Component A processes a test video, generates events
2. Events flow to Component B via API
3. Component B correlates events, generates incident
4. Incident pushed to Component C via WebSocket
5. Dashboard shows incident with timeline and score breakdown

### Success Criteria
- Complete data flow from video to dashboard
- All intermediate data conforms to schemas
- Incident evidence timeline is correct
- Score breakdown is visible

---

## Checkpoint 5: Demo Readiness

**Goal:** The system is ready for live demonstration.

### Prerequisites
- [ ] All previous checkpoints pass
- [ ] At least one compelling demo scenario works end-to-end

### Demo Scenario
1. Show the dashboard (empty, connected)
2. Start the CV pipeline on a test video
3. Events appear in real-time on dashboard
4. Inject synthetic cyber events (USB, file access, network transfer)
5. Correlation engine generates an incident
6. Incident appears on dashboard with:
   - Severity indicator
   - Score with breakdown
   - Evidence timeline
   - Evidence graph
7. (Optional) Show LLM narrative explanation

### Success Criteria
- Demo runs without errors for 3+ minutes
- All displayed data is consistent
- Score breakdown is explainable
- Evidence timeline is chronologically correct
- System recovers gracefully from any component failure

---

## Integration Issue Template

When an integration issue is found, document it:

```
### Issue: [Brief description]
- **Date:** YYYY-MM-DD
- **Reporter:** [Component A/B/C]
- **Checkpoint:** [1-5]
- **Producer:** Component [A/B/C] — [what it sends]
- **Consumer:** Component [A/B/C] — [what it expects]
- **Error:** [Exact error message or mismatch]
- **Schema Reference:** [Which schema field is involved]
- **Status:** [open / investigating / resolved]
- **Resolution:** [How it was fixed]
```
