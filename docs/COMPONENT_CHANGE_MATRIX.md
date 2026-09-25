# Component Change Matrix

> **Audience:** All team members, mentors, and AI coding agents.
> **Enforcement:** Mandatory. Check this matrix before touching any file.

This matrix defines file and directory modification permissions across all project roles.

---

## Permission Matrix

| Path / Subsystem | Mentor / Architect | CV Developer (Component A) | Backend / Correlation (Component B) | Frontend / Dashboard (Component C) |
|---|---|---|---|---|
| `schema/*` | **WRITE** (Final Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `config/*` | **WRITE** (Final Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `docs/*` (Architecture & Contracts) | **WRITE** (Final Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `docs/` (Component-specific) | **WRITE** (Review) | WRITE (CV notes) | WRITE (Backend notes) | WRITE (Frontend notes) |
| `backend/contracts.py` | **WRITE** (Final Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `backend/*` (Implementation) | **WRITE** (Integration) | READ-ONLY | **WRITE** (Primary Owner) | READ-ONLY |
| `cyber/*` (Telemetry/Simulation) | **WRITE** (Integration) | READ-ONLY | **WRITE** (Primary Owner) | READ-ONLY |
| `cv/*` (Vision Pipeline) | **WRITE** (Integration) | **WRITE** (Primary Owner) | READ-ONLY | READ-ONLY |
| `frontend/*` (UI / Dashboard) | **WRITE** (Integration) | READ-ONLY | READ-ONLY | **WRITE** (Primary Owner) |
| `assets/*` (UI/Static Assets) | **WRITE** | READ-ONLY | READ-ONLY | **WRITE** |
| `data/examples/*` | **WRITE** (Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `config/scenarios/*` | **WRITE** (Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `tests/test_foundation.py` | **WRITE** (Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `tests/test_cv_*` | **WRITE** (Review) | **WRITE** (Component Owner)| READ-ONLY | READ-ONLY |
| `tests/test_backend_*` | **WRITE** (Review) | READ-ONLY | **WRITE** (Component Owner)| READ-ONLY |
| `tests/test_correlation_*` | **WRITE** (Review) | READ-ONLY | **WRITE** (Component Owner)| READ-ONLY |
| `tests/test_cyber_*` | **WRITE** (Review) | READ-ONLY | **WRITE** (Component Owner)| READ-ONLY |
| `tests/test_frontend_*` | **WRITE** (Review) | READ-ONLY | READ-ONLY | **WRITE** (Component Owner)|
| `tests/fixtures/` | **WRITE** (Shared fixtures)| WRITE (CV fixtures) | WRITE (Backend fixtures) | READ-ONLY |
| `requirements.txt` | **WRITE** (Authority) | READ (Propose changes) | READ (Propose changes) | READ-ONLY |
| `.gitignore` | **WRITE** (Authority) | READ-ONLY | READ-ONLY | READ-ONLY |
| `README.md` | **WRITE** (Authority) | READ-ONLY | READ-ONLY | READ-ONLY |

---

## Permission Definitions

### WRITE (Final Authority)
The mentor/architect has sole modification rights. No component developer or AI agent may modify these files without explicit review and approval recorded in `docs/DECISION_LOG.md`.

### WRITE (Primary Owner)
The assigned component developer and their AI coding agent have full ownership to create, modify, and test files within this path. Other component agents must treat this path as READ-ONLY.

### READ-ONLY
The developer and AI agent may inspect and consume the file, import modules or schemas from it, and write tests against its public interfaces. They **MUST NOT** edit, reformat, rename, or delete the file.

---

## Conflict Resolution Protocol

If your component implementation requires a change to a file marked **READ-ONLY**:

1. **STOP IMMEDIATELY**. Do not write code modifying that file.
2. File a Contract Change Request in `docs/DECISION_LOG.md` (or notify the mentor).
3. Specify:
   - What capability is missing.
   - Exact lines/fields proposed to change.
   - Why local component adapter logic cannot solve the issue.
   - Impact on other components.
4. Wait for mentor sign-off before proceeding.
