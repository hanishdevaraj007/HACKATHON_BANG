# Team Workflow

> **Audience:** All team members and their AI coding agents.

## Development Process

### Phase 1: Foundation (COMPLETE)
- Repository structure ✅
- Schemas and contracts ✅
- Configuration files ✅
- Documentation ✅
- Test infrastructure ✅

### Phase 2: Component Development (CURRENT)
Each team member works independently on their component:
- **Component A:** CV pipeline → emits normalized events
- **Component B:** Backend API + correlation engine → consumes events, produces incidents
- **Component C:** Dashboard → consumes API/WebSocket, displays incidents

### Phase 3: Integration
- Components connect via REST API and WebSocket
- Integration tests validate end-to-end flow
- See `docs/INTEGRATION_CHECKPOINTS.md`

### Phase 4: Demo
- End-to-end demonstration with synthetic data
- Live dashboard showing correlated incidents

## Working With Your AI Agent

### Before Starting Any Task

1. Have your AI agent read these documents:
   - `docs/PROJECT_OVERVIEW.md`
   - `docs/COMPONENT_BOUNDARIES.md`
   - `docs/AI_ENGINEERING_RULES.md`
   - The contract doc relevant to your component

2. Use the prompt template from `docs/PROMPT_TEMPLATE.md`

### During Implementation

1. Work within your component directory ONLY
2. Emit/consume data matching the schemas in `schema/`
3. Write tests for every feature
4. Run `python -m pytest tests/ -v` frequently

### After Each Session

1. Have your AI agent report what changed (Rule 20)
2. Run tests and verify they pass (Rule 19)
3. Commit with a descriptive message
4. If you need a contract change, document it in `docs/DECISION_LOG.md`

## Git Workflow

### Branch Naming
```
component-a/feature-name
component-b/feature-name
component-c/feature-name
```

### Commit Messages
```
[component-a] Add YOLO detection pipeline
[component-b] Implement event ingestion API
[component-c] Add incident list component
[mentor] Update event schema with new field
```

### Merge Process
1. Work on your component branch
2. Run ALL tests (not just your component's)
3. Create pull request
4. Mentor reviews for contract compliance
5. Merge

## Communication

### Requesting Contract Changes
1. Document in `docs/DECISION_LOG.md`
2. Include: what, why, impact on other components
3. Mentor reviews and decides

### Reporting Integration Issues
1. Document the exact error
2. Note which component produces the data and which consumes it
3. Reference the relevant schema
4. Mentor coordinates the fix

## Quick Reference: Key Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_foundation.py -v

# Run backend (once Component B implements it)
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```
