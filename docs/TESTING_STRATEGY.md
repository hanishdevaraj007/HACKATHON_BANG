# Testing Strategy

> **Audience:** All developers and AI agents.

## Test Framework

- **Framework:** pytest
- **Config:** `pytest.ini` in project root
- **Test directory:** `tests/`
- **Naming convention:** `test_*.py` files, `test_*` functions, `Test*` classes

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_foundation.py -v

# Run specific test class
python -m pytest tests/test_foundation.py::TestScoringContract -v

# Run specific test
python -m pytest tests/test_foundation.py::TestScoringContract::test_max_score -v

# Run with print output visible
python -m pytest tests/ -v -s
```

## Test Categories

### Foundation Tests (Mentor-owned)
File: `tests/test_foundation.py`

These validate the repository skeleton:
- Schema files exist and are valid JSON
- Configuration files load correctly
- Example events conform to schema
- Scoring constants match the frozen contract
- Repository directories exist
- Contracts module works

**These tests must ALWAYS pass. Do not modify them without mentor approval.**

### Component A Tests (CV team)
Files: `tests/test_cv_*.py`

Should validate:
- YOLO detection produces valid bounding boxes
- Tracking IDs are assigned consistently
- Zone mapping works for configured cameras
- Generated events conform to `schema/event.schema.json`
- Confidence values are in range [0.0, 1.0]
- Edge cases: empty frames, no detections, multiple persons

### Component B Tests (Backend team)
Files: `tests/test_backend_*.py`, `tests/test_cyber_*.py`

Should validate:
- API endpoints return correct status codes
- Event ingestion validates against schema
- Entity resolution links related events
- Policy evaluation produces correct signals
- Scoring produces correct points for each rule
- Correlation FSM state transitions are correct
- Incident generation assembles evidence correctly
- WebSocket messages conform to schema
- Synthetic cyber events are properly labeled

### Component C Tests (Dashboard team)
Files: `tests/test_frontend_*.py`

Should validate (where practical):
- HTML files are well-formed
- JavaScript has no syntax errors
- API response parsing works correctly
- WebSocket message handling works

## Test Requirements

### Every Feature Needs a Test
Per Rule 6 in `docs/AI_ENGINEERING_RULES.md`, no feature is complete without a test.

### Schema Validation in Tests
Use jsonschema to validate generated data:

```python
import json
import jsonschema

def test_my_event_conforms_to_schema():
    with open("schema/event.schema.json") as f:
        schema = json.load(f)
    
    event = generate_my_event()  # Your function
    jsonschema.validate(event, schema)  # Raises on failure
```

### Test Data & Fixtures
Cyber telemetry is synthetic/scripted. Computer-vision validation uses real recorded scenario video when the asset is available. Unit tests may use synthetic CV fixtures.
- Use `data/examples/example_events.json` and `tests/fixtures/` as reference contracts.
- Deterministic ground-truth scenarios are in `config/scenarios/`.
- Honestly identify synthetic data; never label synthetic telemetry as live capture.

### Test Independence
- Each test must be independent — no shared mutable state
- Use pytest fixtures for shared setup
- Tests must pass in any order

## Before Declaring Done

Per Rule 19:
1. Run `python -m pytest tests/ -v`
2. ALL tests must pass
3. Report the actual test output
4. Do NOT claim tests passed without running them
