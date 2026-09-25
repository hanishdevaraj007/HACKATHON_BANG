"""
Backend Configuration Module.

Provides configuration settings for the backend event store, database paths,
and runtime settings. Can be overridden via environment variables.

OWNED BY: Backend Team (Component B)
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Default SQLite database path for runtime events
DEFAULT_DB_PATH = Path(
    os.getenv("MERIDIAN_DB_PATH", str(DATA_DIR / "events.db"))
)

# Ingestion defaults
DEFAULT_QUERY_LIMIT = 100
MAX_QUERY_LIMIT = 1000
