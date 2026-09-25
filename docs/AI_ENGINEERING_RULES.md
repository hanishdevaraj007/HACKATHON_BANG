# AI Engineering Rules

> **Audience:** Every AI coding agent and human developer working on this project.
> These rules are NON-NEGOTIABLE. Violating them creates integration failures.

## The 20 Rules

### Rule 1: Read Before Coding
Read the relevant documentation before writing any code:
- `docs/PROJECT_OVERVIEW.md` — Always
- `docs/COMPONENT_BOUNDARIES.md` — Always
- `docs/EVENT_CONTRACT.md` — If touching events
- `docs/INCIDENT_CONTRACT.md` — If touching incidents or scoring
- `docs/ZONE_POLICY.md` — If touching zones or policies
- `docs/ARCHITECTURE.md` — If making structural changes

### Rule 2: Do Not Invent Interfaces
Use the interfaces defined in this repository. If you need a new interface, document it in `docs/DECISION_LOG.md` and get mentor approval before implementing.

### Rule 3: Do Not Silently Alter Shared Contracts
The files in `schema/`, `config/`, and `backend/contracts.py` are shared contracts. If you believe a change is needed:
1. Document the proposed change in `docs/DECISION_LOG.md`
2. Explain why the current contract is insufficient
3. Get mentor approval
4. Update ALL affected components simultaneously

### Rule 4: Do Not Change Another Component's Architecture
You may only modify files within your component boundary (see `docs/COMPONENT_BOUNDARIES.md`). If you need a change in another component, document it as a request.

### Rule 5: Preserve Backward Compatibility
When modifying shared contracts, ensure existing consumers continue to work. Add new fields as nullable. Do not remove or rename existing fields.

### Rule 6: Every Feature Must Have a Test
No feature is complete without a corresponding test in `tests/`. Write the test BEFORE or ALONGSIDE the implementation. A feature without a test is an unverified claim.

### Rule 7: Every API Must Have an Example
Every REST endpoint must have:
- An example request (with headers and body)
- An example response (with status code and body)
- Error response examples

Document these in the code (docstrings) or in dedicated API documentation.

### Rule 8: Document Changed Files
After every implementation session, report:
- Files created
- Files modified
- Files deleted
- Tests added
- Tests passing/failing

### Rule 9: No Secrets in Source Code
- No API keys, passwords, or tokens in any file
- Use environment variables via `python-dotenv`
- Add secret patterns to `.gitignore`
- If you need a secret for development, document the environment variable name in `config/` but never its value

### Rule 10: No Unnecessary Dependencies
Before adding a dependency:
1. Check if the functionality exists in the standard library
2. Check if an existing dependency already provides it
3. If a new dependency is truly needed, add it to `requirements.txt` with a pinned version and document why in `docs/DECISION_LOG.md`

### Rule 11: Do Not Replace Deterministic Logic with an LLM
Security decisions (scoring, correlation, access policy evaluation) MUST use deterministic code. An LLM may only be used for:
- Generating natural-language narrative text from structured JSON
- Never for scoring, detection, classification, or correlation

### Rule 12: Do Not Claim Unsupported CV Capabilities
The CV pipeline can:
- Detect objects (persons, bags, etc.) using YOLO
- Track objects across frames using supported trackers
- Map detections to zones via configured camera-zone mappings

The CV pipeline CANNOT:
- Perform face recognition
- Perform biometric identification
- Re-identify persons across cameras
- Detect emotions, intent, or suspicious behavior directly
- Read text from signs or documents

Do not claim or pretend otherwise.

### Rule 13: Never Fabricate Evidence
- Every event must come from a real source processor or a clearly labeled synthetic generator
- Never generate fake events to make a demo look better
- Never backfill events to create a pattern that didn't happen
- Never modify raw evidence references

### Rule 14: Label Synthetic Data
All synthetic/test telemetry must be clearly labeled:
- In the event `attributes`, include `"synthetic": true`
- In network transfer events, include `"transfer_label": "SYNTHETIC"`
- In documentation, state that data is synthetic

### Rule 15: Graceful Degradation
Every component must handle failures gracefully:
- If the CV pipeline is down, the backend should still process badge/cyber events
- If the database is unavailable, log the error and return a meaningful HTTP error
- If the WebSocket connection drops, the frontend should show disconnected status and retry
- If the LLM is unavailable, the incident should display without narrative text

### Rule 16: Simple Over Elegant
Prefer a simple, working implementation over an elegant, abstract one:
- A working function is better than an unused class hierarchy
- A hardcoded lookup table is better than a complex config system nobody uses
- A direct SQL query is better than an ORM abstraction for a hackathon

### Rule 17: Prefer Simple Working Implementation
Do not build infrastructure you don't need yet:
- No message queues until proven necessary
- No caching layer until you have a performance problem
- No microservice boundaries until the monolith is too big

### Rule 18: Do Not Rewrite Without Reason
If existing code works and passes its tests, do not rewrite it for style preferences. Refactoring is allowed only when:
- It fixes a bug
- It's necessary for a new feature
- It resolves a documented performance issue
- It's agreed upon in the decision log

### Rule 19: Run Tests Before Declaring Completion
Before reporting that a task is done:
1. Run `python -m pytest tests/ -v`
2. All tests must pass
3. Report the actual test output
4. Do not claim tests passed if you did not run them

### Rule 20: Report Exactly What Changed
After every implementation session, provide:
```
FILES CREATED: [list]
FILES MODIFIED: [list]
FILES DELETED: [list]
TESTS ADDED: [list]
TESTS PASSING: [count]
TESTS FAILING: [count and reasons]
REMAINING WORK: [list]
KNOWN ISSUES: [list]
```

## For AI Agents Specifically

If you are an AI coding agent (Copilot, Cursor, Windsurf, Claude, etc.):

1. **You do not have prior conversation context.** All context is in this repository.
2. **Read docs/ before writing code.** Every time.
3. **Do not guess.** If a contract, interface, or configuration is not documented, ask your human operator or check the schema files.
4. **Do not silently expand scope.** If the human asks you to add a button, add a button. Do not also refactor the entire page layout.
5. **Validate your output.** Run tests. Check that your code actually imports, runs, and produces the expected output.
6. **Admit limitations.** If you cannot do something, say so. Do not fabricate a solution.
