# AI Multi-Agent Collaboration Rules

> **STATUS: MANDATORY READING** for every AI coding agent before writing any code.
>
> This document governs how multiple AI-assisted developers work on this shared
> codebase without destroying each other's work.

---

## Rule 1 — Component Ownership

### MENTOR / ARCHITECT
Owns: `docs/`, `schema/`, `config/`, integration scripts, release testing, architecture decisions, shared contracts, cross-component wiring.

The mentor is the **final authority** for shared-contract changes.

### COMPONENT A — Computer Vision
Primary ownership: `cv/`

May create/update:
- `cv/*`
- `tests/test_cv_*`
- CV-specific docs within `cv/`
- Local CV fixtures in `tests/fixtures/cv/`

Read-only: `schema/*`, `config/*`, `backend/*`, `cyber/*`, `frontend/*`

The CV developer must **consume** the shared event contract.
The CV developer **MUST NOT** modify the event schema merely to simplify CV implementation.

### COMPONENT B — Security Backend / Correlation
Primary ownership: `backend/`, `cyber/`

May create/update:
- `backend/*` (except `backend/contracts.py` which is mentor-owned)
- `cyber/*`
- `tests/test_backend_*`, `tests/test_correlation_*`, `tests/test_cyber_*`

Read-only: `schema/*`, `config/*`, `cv/*`, `frontend/*`

The backend developer **MUST NOT** modify CV detection logic to compensate for backend assumptions.

### COMPONENT C — Frontend / Dashboard
Primary ownership: `frontend/`

May create/update:
- `frontend/*`
- `tests/test_frontend_*`
- `assets/*` (UI assets)

Read-only: `schema/*`, `config/*`, `backend/*`, `cyber/*`, `cv/*`

The frontend developer **MUST NOT** modify backend routes merely because the UI needs different data. API changes must be proposed to the mentor.

---

## Rule 2 — Protected Shared Files (CONTRACT FILES)

These files are **READ-ONLY** for all component agents. Only the mentor may modify them:

```
schema/event.schema.json
schema/incident.schema.json
schema/scoring.schema.json
config/organization.json
config/zones.json
config/scoring.json
backend/contracts.py
docs/EVENT_CONTRACT.md
docs/INCIDENT_CONTRACT.md
docs/ZONE_POLICY.md
docs/ARCHITECTURE.md
docs/COMPONENT_BOUNDARIES.md
docs/AI_MULTI_AGENT_COLLABORATION_RULES.md
```

If an implementation appears impossible under the current contract:

1. **STOP**
2. Explain the mismatch
3. Identify the required contract change
4. Wait for mentor decision

**Do NOT work around the contract by silently changing it.**

---

## Rule 3 — No Drive-By Changes

While working on a component, an AI agent must NOT:

- Reformat unrelated files
- Rename unrelated directories
- Upgrade dependencies without justification
- Rewrite unrelated modules
- Clean up unrelated code
- Change naming conventions in another component
- Replace an existing implementation merely because it prefers another style
- Modify README documentation unrelated to its component
- Delete unused-looking files unless verified as genuinely obsolete

**Minimal changes are preferred.**

---

## Rule 4 — Do Not Claim File Ownership by Conversation

The **repository itself** is the authority.

Before changing a file:

1. Inspect it
2. Determine its ownership (see Rule 1 and `docs/COMPONENT_CHANGE_MATRIX.md`)
3. Determine whether it is shared
4. Check current branch/state
5. Confirm that the task authorizes modification

If ownership is unclear: **DO NOT GUESS. Report the conflict.**

---

## Rule 5 — Git Is Part of the Safety Model

Developers should work on separate branches:

```
feat/cv-physical-events
feat/backend-correlation
feat/frontend-dashboard
```

Never commit work directly to `main` during parallel development unless the mentor explicitly chooses to do so.

Recommended commit style:

```
feat(cv): add tracked detections
feat(backend): add event ingestion
feat(frontend): add incident panel
test(correlation): add bag handoff fixture
fix(backend): correct zone lookup for Z3-ARCHIVE
```

Avoid giant commits containing unrelated work.

---

## Rule 6 — Pull Before Starting Major Work

Before beginning a new implementation task:

1. Inspect current branch
2. Pull latest approved changes
3. Inspect `git status`
4. Inspect relevant files
5. Verify shared contracts have not changed unexpectedly

**Never blindly reset or force-push.**

---

## Rule 7 — Never Destroy Other Agent Work

If Git shows:
- Merge conflicts
- Unexpected modifications
- Changed shared files
- Uncommitted work from another developer

**DO NOT** automatically delete, reset, checkout, or overwrite those changes.

Stop and report the conflict.

**Never use destructive commands** such as:

```
git reset --hard
git clean -fd
git checkout .
git restore .
```

unless the mentor explicitly instructs it.

---

## Rule 8 — Contract-First Development

Every component must implement against contracts.

**Correct flow:**
```
DOCUMENT → CONTRACT → IMPLEMENTATION → TEST → INTEGRATION
```

**Never:**
```
IMPLEMENTATION → change contract to fit implementation
```

---

## Rule 9 — API Changes Require Coordination

If a developer believes an API needs a new endpoint, changed request/response structure, renamed field, or removed field, they must **NOT** silently modify the API contract.

They must report:
- **PROBLEM** — what doesn't work
- **CURRENT CONTRACT** — what it says now
- **PROPOSED CHANGE** — what they need
- **WHY NEEDED** — concrete justification
- **AFFECTED COMPONENTS** — who else is impacted
- **BACKWARD-COMPATIBILITY IMPACT** — what breaks

The mentor decides.

---

## Rule 10 — Schema Changes Require Coordination

The event schema is shared infrastructure. Never add a field solely because it is convenient.

Every schema change must answer:
- **WHY?**
- **WHICH PRODUCERS USE IT?**
- **WHICH CONSUMERS USE IT?**
- **IS IT REQUIRED OR OPTIONAL?**
- **DO EXISTING TESTS STILL PASS?**

Mentor approval required.

---

## Rule 11 — No Hard-Coded Organization Logic

**Never write:**
```python
if zone == "server_room":
    restricted = True
```

**Instead:** load zone policy configuration from `config/zones.json`.

Never hard-code employee names, zone security levels, device assignments, asset relationships, or allowed hours inside component logic. Use configuration.

---

## Rule 12 — No Hidden Cross-Component Dependencies

A component must NOT import internal implementation details from another component merely because it is convenient.

**Use:**
- Shared contracts (`backend/contracts.py`)
- Documented functions/interfaces
- API endpoints
- Event schema

**Do NOT** directly depend on another component's internal classes unless the architecture explicitly defines that interface.

---

## Rule 13 — Test Before Integrating

Every component should pass its component-level tests before integration. Integration testing happens only after the component acceptance criteria pass.

---

## Rule 14 — Tests Must Not Depend on Randomness

Use deterministic fixtures. If randomness is required:
- Use an explicit seed
- Document it
- Make the test reproducible

---

## Rule 15 — Real vs Synthetic Data Must Be Honestly Identified

The project uses:
- **Real recorded video** + **real pretrained CV inference** for physical events
- **Synthetic/scripted cyber telemetry** for endpoint, network, and identity events

Do NOT label synthetic cyber events as real enterprise logs.
Do NOT fabricate camera events and call them computer-vision detections.

---

## Rule 16 — LLM Is Never Load-Bearing

An agent must NEVER introduce an LLM dependency into:
- Event detection
- Zone authorization
- Correlation
- Incident scoring
- Evidence generation

LLM is a separate narrative layer. The system must work without it.

---

## Rule 17 — Security Facts Require Evidence

Do NOT generate: "malicious", "confirmed attacker", "guilty"

**Prefer:** "suspicious activity", "potential data exfiltration", "policy violation", "correlated security incident"

The system reports evidence, not convictions.

---

## Rule 18 — AI Agent Must Report Actual Work

At the end of every coding task, the IDE agent must report:

```
FILES CREATED: [exact list]
FILES MODIFIED: [exact list]
FILES DELETED: [exact list]
WHY EACH WAS CHANGED: [rationale]
DEPENDENCIES ADDED: [list]
COMMANDS EXECUTED: [list]
TESTS EXECUTED: [list]
ACTUAL TEST RESULTS: [pass/fail with output]
KNOWN FAILURES: [list]
KNOWN LIMITATIONS: [list]
UNFINISHED WORK: [list]
NEXT RECOMMENDED TASK: [description]
```

Never report "all good" without evidence.

---

## Rule 19 — Stop Conditions

An AI agent must **STOP** and report when:

- Shared contract must change
- Another component must be modified
- Tests fail for an unrelated component
- Dependency conflict appears
- Repository contains unexpected modifications
- Requirements contradict documentation
- Architectural decision is unclear
- An implementation would require unsupported assumptions

The correct response is NOT to improvise.

---

## Rule 20 — No Massive Rewrites

Prefer small, reviewable changes.

If a rewrite appears necessary, first document:
- **WHY REWRITE**
- **WHAT IS REPLACED**
- **WHAT IS PRESERVED**
- **WHAT BREAKS**
- **WHAT TESTS PROVE EQUIVALENCE**

Then wait for mentor approval if another component is affected.

---

## Rule 21 — Master AI / IDE AI Separation

Each member has:

```
MASTER AI → creates/verifies tailored implementation prompts
    ↓
IDE AI → implements the current task
    ↓
IDE AI → tests and reports
    ↓
MASTER AI → verifies the IDE AI result before generating next prompt
```

The IDE AI does NOT decide architecture.
The Master AI does NOT assume the IDE AI implemented the task correctly.

---

## Rule 22 — Component Tasks Are Atomic

**Do NOT instruct an agent:** "Build the entire backend."

**Instead:**
1. "Implement normalized event ingestion according to this contract."
2. "Implement policy enrichment."
3. "Implement entity resolution."
4. "Implement correlation."

This makes debugging and verification possible.

---

## AI Agent Startup Protocol

**BEFORE writing any code, every AI agent must:**

1. Read `README.md`
2. Read `docs/ARCHITECTURE.md`
3. Read `docs/COMPONENT_BOUNDARIES.md`
4. Read `docs/AI_MULTI_AGENT_COLLABORATION_RULES.md`
5. Read `docs/EVENT_CONTRACT.md` and `docs/INCIDENT_CONTRACT.md`
6. Read component-specific README (if it exists in the component directory)
7. Inspect `git status`
8. Inspect current branch
9. Inspect changed files
10. Identify owned paths (see `docs/COMPONENT_CHANGE_MATRIX.md`)
11. Confirm task acceptance criteria
12. Implement **only** the requested task
13. Run component tests
14. Run relevant foundation tests
15. Report exact results

---

## Cross-Component Anti-Patterns

### BAD: Frontend changes backend schema
> Frontend developer modifies `schema/incident.schema.json` because a UI field is missing.

### GOOD: Frontend reports the gap
> "Required field `incident_summary` missing from API response. Proposing addition to `docs/DECISION_LOG.md`."
> Mentor decides whether to extend the API.

### BAD: CV developer changes event schema
> CV developer modifies `schema/event.schema.json` because CV produces a different object shape.

### GOOD: CV adapter converts internal data
> CV module converts its internal detection structure into the frozen event contract format before emitting.

### BAD: Backend developer changes frontend files
> Backend developer modifies `frontend/js/app.js` to test an API endpoint.

### GOOD: Backend writes API tests independently
> Backend writes `tests/test_backend_api.py` using `httpx` or `TestClient`.
