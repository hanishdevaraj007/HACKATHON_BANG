"""
Shared contracts module.

This module provides Python representations of the project's JSON schemas
and configurations. It is the SINGLE SOURCE OF TRUTH for constants that
multiple components depend on.

OWNED BY: Mentor (architecture team)
DO NOT MODIFY without updating docs/DECISION_LOG.md and notifying all teams.
"""

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Path helpers — work on Windows and Linux
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SCENARIOS_DIR = CONFIG_DIR / "scenarios"
SCHEMA_DIR = PROJECT_ROOT / "schema"
DATA_DIR = PROJECT_ROOT / "data"


def _load_json(path: Path) -> dict:
    """Load a JSON file and return its contents as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Configuration loaders
# ---------------------------------------------------------------------------
def load_zone_config() -> dict:
    """Load zone configuration from config/zones.json."""
    return _load_json(CONFIG_DIR / "zones.json")


def load_organization_config() -> dict:
    """Load organization configuration from config/organization.json."""
    return _load_json(CONFIG_DIR / "organization.json")


def load_scoring_config() -> dict:
    """Load scoring configuration from config/scoring.json."""
    return _load_json(CONFIG_DIR / "scoring.json")


def load_scenario(name: str) -> dict:
    """Load a scenario definition from config/scenarios/<name>.json."""
    filename = f"{name}.json" if not name.endswith(".json") else name
    return _load_json(SCENARIOS_DIR / filename)


# ---------------------------------------------------------------------------
# Schema loaders
# ---------------------------------------------------------------------------
def load_event_schema() -> dict:
    """Load the normalized event JSON schema."""
    return _load_json(SCHEMA_DIR / "event.schema.json")


def load_incident_schema() -> dict:
    """Load the incident JSON schema."""
    return _load_json(SCHEMA_DIR / "incident.schema.json")


# ---------------------------------------------------------------------------
# FROZEN scoring constants — DO NOT CHANGE
# ---------------------------------------------------------------------------
SCORING_RULES = {
    "unauthorized_zone_access": 25,
    "after_hours_activity": 15,
    "sensitive_asset_interaction": 20,
    "usb_activity": 15,
    "large_outbound_transfer": 15,
    "multi_signal_correlation": 10,
}

MAX_SCORE = 100

SEVERITY_BANDS = [
    {"label": "LOW",      "min": 0,  "max": 29},
    {"label": "MEDIUM",   "min": 30, "max": 59},
    {"label": "HIGH",     "min": 60, "max": 79},
    {"label": "CRITICAL", "min": 80, "max": 100},
]


def get_severity(score: int) -> str:
    """Return severity label for a given score. Score is NOT a probability."""
    clamped = max(0, min(score, MAX_SCORE))
    for band in SEVERITY_BANDS:
        if band["min"] <= clamped <= band["max"]:
            return band["label"]
    return "LOW"


# ---------------------------------------------------------------------------
# Event type constants
# ---------------------------------------------------------------------------
EVENT_TYPES = [
    "person_enter",
    "person_exit",
    "object_place",
    "object_pickup",
    "object_unattended",
    "badge_swipe",
    "login_success",
    "login_failure",
    "usb_insert",
    "usb_remove",
    "file_access",
    "network_transfer",
    "door_open",
    "door_close",
    "policy_violation",
]

SOURCE_TYPES = [
    "camera",
    "badge_reader",
    "endpoint_agent",
    "network_monitor",
    "access_control",
    "identity_provider",
]
