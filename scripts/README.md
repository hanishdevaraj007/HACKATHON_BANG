# Scripts Directory

Utility scripts for development, testing, and demonstration.

## Planned Scripts

- `setup_env.py` — Environment setup and validation
- `generate_synthetic_events.py` — Generate synthetic event data for testing
- `run_demo.py` — Run the full demo stack

## Rules

- All scripts must work on Windows (no bash-only commands).
- Use `python` not `python3` (Windows convention).
- Do not hardcode absolute paths.
- Use `pathlib.Path` for cross-platform path handling.
