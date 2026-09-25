# Prompt Template for AI Coding Agents

> **Audience:** Team members using AI coding agents (Copilot, Cursor, Claude, etc.)
> Copy and customize this template for each task you give your AI agent.

## How to Use This Template

1. Copy the template below
2. Fill in the bracketed sections with your specific task details
3. Give it to your AI coding agent as the initial prompt
4. After the agent completes work, use the VERIFICATION CHECKLIST before accepting

---

## MASTER PROMPT TEMPLATE

```
# CONTEXT

You are working on the Meridian Security Platform, a multi-modal security
event correlation system. This is a hackathon project with three independent
components developed by different teams.

You have NO prior conversation context. All context is in the repository.

# CURRENT REPOSITORY STATE

The repository contains:
- Established directory structure with component boundaries
- JSON schemas in schema/ (event, incident, scoring)
- Configuration in config/ (zones, organization, scoring)
- Shared contracts in backend/contracts.py
- Foundation test suite in tests/test_foundation.py
- Documentation in docs/

[Describe any additional current state, e.g., "Component B has a basic
FastAPI app at backend/app.py with event ingestion endpoint."]

# COMPONENT

[Your component: A (CV), B (Backend), or C (Dashboard)]

# OBJECTIVE

[Clear, specific description of what you want the agent to do.
Example: "Implement the YOLO detection pipeline that processes video
frames and emits normalized person_enter/person_exit events."]

# READ FIRST

Before writing any code, read these files:
- docs/PROJECT_OVERVIEW.md
- docs/COMPONENT_BOUNDARIES.md
- docs/AI_ENGINEERING_RULES.md
- [Add component-specific docs, e.g., docs/EVENT_CONTRACT.md]

# CONTRACTS

The following contracts are IMMUTABLE:
- schema/event.schema.json — All events must conform to this
- schema/incident.schema.json — All incidents must conform to this
- config/scoring.json — Scoring values are FROZEN
- backend/contracts.py — Shared Python constants

# INPUT

[What data does your code receive?
Example: "Video frames as numpy arrays from OpenCV VideoCapture"]

# OUTPUT

[What data does your code produce?
Example: "Normalized events conforming to schema/event.schema.json,
sent via HTTP POST to http://localhost:8000/api/v1/events"]

# FILES ALLOWED TO CHANGE

[List specific files/directories]
- [component_dir]/*
- tests/test_[component]_*.py

# FILES NOT TO CHANGE

- schema/*
- config/*
- backend/contracts.py
- [other component directories]
- docs/* (request changes through docs/DECISION_LOG.md)

# DEPENDENCIES

[List any dependencies already available in requirements.txt]
- Do NOT add new dependencies without documenting why
- Check requirements.txt for what's already available

# CONSTRAINTS

1. Follow all rules in docs/AI_ENGINEERING_RULES.md
2. Use Python for backend, vanilla HTML/CSS/JS for frontend
3. Must work on Windows
4. No hardcoded secrets
5. No unnecessary dependencies
6. All timestamps in UTC ISO 8601
7. [Add component-specific constraints]

# IMPLEMENTATION REQUIREMENTS

[Specific technical requirements]
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

# TEST REQUIREMENTS

1. Write tests in tests/test_[component]_[feature].py
2. Every function must have at least one test
3. Validate output against JSON schemas
4. Tests must pass with: python -m pytest tests/ -v

# ACCEPTANCE CRITERIA

[Clear, measurable criteria]
1. [Criterion 1]
2. [Criterion 2]
3. All existing tests still pass
4. New tests are written and pass
5. No files outside allowed list were modified

# EXPECTED OUTPUT REPORT

After completing the task, provide this report:

FILES CREATED: [list with brief descriptions]
FILES MODIFIED: [list with what changed]
FILES DELETED: [list if any]
TESTS ADDED: [list test functions]
TESTS PASSING: [count]
TESTS FAILING: [count and reasons]
DEPENDENCIES ADDED: [list if any, with justification]
REMAINING WORK: [what's not done yet]
KNOWN ISSUES: [any problems discovered]
```

---

## VERIFICATION CHECKLIST

After your AI agent completes a task, verify these before accepting:

```
□ Agent read the required documentation
□ All output conforms to the JSON schemas
□ No files outside the allowed list were modified
□ No new dependencies were added without justification
□ Tests were written for new features
□ All tests pass (run: python -m pytest tests/ -v)
□ No secrets were committed
□ No synthetic data is presented as real
□ The output report is complete and honest
□ The code actually runs (not just "should work")
```

### If Verification Fails

1. Note specifically what failed
2. Create a new prompt for the agent with:
   - The original task context
   - What was completed correctly
   - What specifically needs to be fixed
   - The error messages or test failures
3. Do NOT let the agent start from scratch — it should fix the specific issues

---

## EXAMPLE: Component A Task Prompt

```
# CONTEXT
[Standard context paragraph from template]

# COMPONENT
Component A — CV / Physical Events

# OBJECTIVE
Implement a basic video frame processor that:
1. Opens a video file using OpenCV
2. Runs YOLO detection on each frame
3. Identifies persons and objects
4. Generates normalized events for person_enter when a new track appears

# READ FIRST
- docs/PROJECT_OVERVIEW.md
- docs/COMPONENT_BOUNDARIES.md  
- docs/AI_ENGINEERING_RULES.md
- docs/EVENT_CONTRACT.md
- schema/event.schema.json

# FILES ALLOWED TO CHANGE
- cv/*
- tests/test_cv_*.py

# ACCEPTANCE CRITERIA
1. cv/detector.py processes a video file
2. Detected persons generate person_enter events
3. Events validate against schema/event.schema.json
4. At least 3 tests in tests/test_cv_detection.py
5. All tests pass
```
