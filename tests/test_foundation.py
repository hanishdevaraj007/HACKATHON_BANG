"""
Foundation test suite — validates that the repository skeleton is intact.

These tests verify:
  1. JSON schemas exist and are valid JSON
  2. Configuration files load correctly
  3. Example events validate against the event schema
  4. Scoring constants match the frozen contract
  5. Repository component directories are discoverable
  6. Shared contracts module works

Run with: python -m pytest tests/ -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.contracts import (
    PROJECT_ROOT as CONTRACTS_ROOT,
    CONFIG_DIR,
    SCENARIOS_DIR,
    SCHEMA_DIR,
    DATA_DIR,
    load_zone_config,
    load_organization_config,
    load_scoring_config,
    load_scenario,
    load_event_schema,
    load_incident_schema,
    SCORING_RULES,
    MAX_SCORE,
    SEVERITY_BANDS,
    get_severity,
    EVENT_TYPES,
    SOURCE_TYPES,
)


# ===========================================================================
# Schema existence tests
# ===========================================================================
class TestSchemaExistence:
    """Verify that all required JSON schemas exist and are parseable."""

    def test_event_schema_exists(self):
        path = SCHEMA_DIR / "event.schema.json"
        assert path.exists(), f"Missing: {path}"

    def test_incident_schema_exists(self):
        path = SCHEMA_DIR / "incident.schema.json"
        assert path.exists(), f"Missing: {path}"

    def test_scoring_schema_exists(self):
        path = SCHEMA_DIR / "scoring.schema.json"
        assert path.exists(), f"Missing: {path}"

    def test_event_schema_is_valid_json(self):
        schema = load_event_schema()
        assert "$schema" in schema
        assert schema["title"] == "Normalized Security Event"

    def test_incident_schema_is_valid_json(self):
        schema = load_incident_schema()
        assert "$schema" in schema
        assert schema["title"] == "Security Incident"


# ===========================================================================
# Configuration loading tests
# ===========================================================================
class TestConfigLoading:
    """Verify configuration files load and contain expected structure."""

    def test_zone_config_loads(self):
        config = load_zone_config()
        assert "zones" in config
        assert len(config["zones"]) >= 6  # Z0, Z1, Z2, Z3-LAB, Z3-ARCHIVE, Z4

    def test_zone_config_has_required_fields(self):
        config = load_zone_config()
        required_fields = [
            "zone_id", "name", "level", "authorized_roles",
            "authorized_persons", "allowed_hours", "required_auth",
            "escort_required", "cameras", "devices", "network_segment", "assets"
        ]
        for zone in config["zones"]:
            for field in required_fields:
                assert field in zone, f"Zone {zone.get('zone_id', '?')} missing field: {field}"

    def test_organization_config_loads(self):
        config = load_organization_config()
        assert "organization" in config
        assert config["organization"]["name"] == "Meridian Research Campus"

    def test_organization_has_roles(self):
        config = load_organization_config()
        assert "roles" in config
        assert len(config["roles"]) >= 4

    def test_organization_has_persons(self):
        config = load_organization_config()
        assert "persons" in config
        assert len(config["persons"]) >= 3

    def test_scoring_config_loads(self):
        config = load_scoring_config()
        assert "rules" in config
        assert "max_score" in config
        assert "severity_bands" in config
        assert config["max_score"] == 100


# ===========================================================================
# Example event validation tests
# ===========================================================================
class TestExampleEvents:
    """Verify example events exist and validate against the event schema."""

    @pytest.fixture
    def example_events(self):
        path = DATA_DIR / "examples" / "example_events.json"
        assert path.exists(), f"Missing: {path}"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["events"]

    @pytest.fixture
    def event_schema(self):
        return load_event_schema()

    def test_example_events_file_exists(self):
        path = DATA_DIR / "examples" / "example_events.json"
        assert path.exists()

    def test_example_events_count(self, example_events):
        # We require at least 9 example events per the contract
        assert len(example_events) >= 9

    def test_example_events_have_required_fields(self, example_events):
        required = ["event_id", "timestamp", "event_type", "source"]
        for event in example_events:
            for field in required:
                assert field in event, f"Event {event.get('event_id', '?')} missing: {field}"

    def test_example_events_cover_required_types(self, example_events):
        required_types = {
            "person_enter", "person_exit", "object_place", "object_pickup",
            "badge_swipe", "login_success", "usb_insert", "file_access",
            "network_transfer"
        }
        present_types = {e["event_type"] for e in example_events}
        missing = required_types - present_types
        assert not missing, f"Missing example event types: {missing}"

    def test_example_events_validate_with_jsonschema(self, example_events, event_schema):
        """Validate each example event against the JSON schema."""
        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        validator = jsonschema.Draft7Validator(event_schema)
        for event in example_events:
            errors = list(validator.iter_errors(event))
            assert not errors, (
                f"Event {event['event_id']} failed validation: "
                f"{[e.message for e in errors]}"
            )


# ===========================================================================
# Scoring contract tests
# ===========================================================================
class TestScoringContract:
    """Verify the FROZEN scoring constants are correct."""

    def test_unauthorized_zone_access_score(self):
        assert SCORING_RULES["unauthorized_zone_access"] == 25

    def test_after_hours_activity_score(self):
        assert SCORING_RULES["after_hours_activity"] == 15

    def test_sensitive_asset_interaction_score(self):
        assert SCORING_RULES["sensitive_asset_interaction"] == 20

    def test_usb_activity_score(self):
        assert SCORING_RULES["usb_activity"] == 15

    def test_large_outbound_transfer_score(self):
        assert SCORING_RULES["large_outbound_transfer"] == 15

    def test_multi_signal_correlation_score(self):
        assert SCORING_RULES["multi_signal_correlation"] == 10

    def test_max_score(self):
        assert MAX_SCORE == 100

    def test_max_score_is_exact_sum_of_rules(self):
        """Prove that the maximum possible score is exactly 100 (sum of all rules)."""
        rule_sum = sum(SCORING_RULES.values())
        assert rule_sum == 100, f"Sum of scoring rules is {rule_sum}, expected exactly 100"
        assert MAX_SCORE == 100

    def test_severity_low(self):
        assert get_severity(0) == "LOW"
        assert get_severity(29) == "LOW"

    def test_severity_medium(self):
        assert get_severity(30) == "MEDIUM"
        assert get_severity(59) == "MEDIUM"

    def test_severity_high(self):
        assert get_severity(60) == "HIGH"
        assert get_severity(79) == "HIGH"

    def test_severity_critical(self):
        assert get_severity(80) == "CRITICAL"
        assert get_severity(100) == "CRITICAL"

    def test_severity_bands_cover_full_range(self):
        """Every score from 0 to 100 must map to exactly one severity."""
        for score in range(0, 101):
            severity = get_severity(score)
            assert severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}, (
                f"Score {score} has no severity mapping"
            )

    def test_scoring_config_matches_constants(self):
        """Config file must match the Python constants."""
        config = load_scoring_config()
        for rule in config["rules"]:
            rule_name = rule["rule_name"]
            assert rule_name in SCORING_RULES, f"Unknown rule in config: {rule_name}"
            assert rule["points"] == SCORING_RULES[rule_name], (
                f"Config score for {rule_name} ({rule['points']}) != "
                f"constant ({SCORING_RULES[rule_name]})"
            )


# ===========================================================================
# Repository structure tests
# ===========================================================================
class TestRepositoryStructure:
    """Verify that the expected component directories exist."""

    @pytest.mark.parametrize("dirname", [
        "backend", "cv", "cyber", "frontend",
        "tests", "docs", "schema", "config",
        "data", "scripts",
    ])
    def test_component_directory_exists(self, dirname):
        path = PROJECT_ROOT / dirname
        assert path.exists(), f"Missing directory: {dirname}/"
        assert path.is_dir(), f"Expected directory, got file: {dirname}"

    def test_backend_is_python_package(self):
        assert (PROJECT_ROOT / "backend" / "__init__.py").exists()

    def test_cv_is_python_package(self):
        assert (PROJECT_ROOT / "cv" / "__init__.py").exists()

    def test_cyber_is_python_package(self):
        assert (PROJECT_ROOT / "cyber" / "__init__.py").exists()

    def test_frontend_has_index_html(self):
        assert (PROJECT_ROOT / "frontend" / "index.html").exists()


# ===========================================================================
# Contracts module tests
# ===========================================================================
class TestContractsModule:
    """Verify the shared contracts module functions correctly."""

    def test_project_root_is_correct(self):
        assert CONTRACTS_ROOT.exists()
        assert (CONTRACTS_ROOT / "requirements.txt").exists()

    def test_event_types_list(self):
        assert "person_enter" in EVENT_TYPES
        assert "object_unattended" in EVENT_TYPES
        assert "badge_swipe" in EVENT_TYPES
        assert "network_transfer" in EVENT_TYPES
        assert len(EVENT_TYPES) >= 15

    def test_source_types_list(self):
        assert "camera" in SOURCE_TYPES
        assert "badge_reader" in SOURCE_TYPES
        assert len(SOURCE_TYPES) >= 6


# ===========================================================================
# Scenario fixture loading tests
# ===========================================================================
class TestScenarioFixtures:
    """Verify ground-truth scenario contracts load and are well-formed."""

    def test_scenarios_directory_exists(self):
        assert SCENARIOS_DIR.exists()
        assert SCENARIOS_DIR.is_dir()

    def test_bag_handoff_scenario_loads(self):
        scenario = load_scenario("bag_handoff")
        assert scenario["scenario_id"] == "SCENARIO-BAG-HANDOFF-001"
        assert len(scenario["timeline"]) >= 7
        assert len(scenario["expected_relationships"]) >= 5
        offsets = [step["t_offset_sec"] for step in scenario["timeline"]]
        assert offsets == sorted(offsets)

    def test_exfiltration_scenario_loads(self):
        scenario = load_scenario("exfiltration")
        assert scenario["scenario_id"] == "SCENARIO-EXFILTRATION-001"
        assert len(scenario["timeline"]) >= 6
        offsets = [step["t_offset_sec"] for step in scenario["timeline"]]
        assert offsets == sorted(offsets)
        stages = [step["stage"] for step in scenario["timeline"]]
        assert "badge_access" in stages
        assert "usb_insertion" in stages
        assert "sensitive_file_access" in stages
        assert "large_outbound_transfer" in stages


# ===========================================================================
# Referential integrity tests
# ===========================================================================
class TestReferentialIntegrity:
    """Verify cross-file references between configs, devices, persons, and zones."""

    @pytest.fixture
    def zones(self):
        return {z["zone_id"]: z for z in load_zone_config()["zones"]}

    @pytest.fixture
    def org(self):
        return load_organization_config()

    def test_no_invalid_zone_references(self, zones, org):
        """All zones referenced in organization entities and scenarios must exist in zones.json."""
        for device in org.get("devices", []):
            assert device["zone_id"] in zones, f"Device {device['device_id']} references unknown zone {device['zone_id']}"
        for camera in org.get("cameras", []):
            assert camera["zone_id"] in zones, f"Camera {camera['camera_id']} references unknown zone {camera['zone_id']}"
        for asset in org.get("assets", []):
            assert asset["zone_id"] in zones, f"Asset {asset['asset_id']} references unknown zone {asset['zone_id']}"

        # Scenarios
        bag_scenario = load_scenario("bag_handoff")
        assert bag_scenario["location"]["zone_id"] in zones

        exfil_scenario = load_scenario("exfiltration")
        assert exfil_scenario["target_zone"]["zone_id"] in zones
        for step in exfil_scenario["timeline"]:
            if "zone_id" in step:
                assert step["zone_id"] in zones, f"Scenario step references unknown zone {step['zone_id']}"

    def test_no_invalid_person_references(self, zones, org):
        """All person IDs referenced in zone authorized_persons and scenarios must exist in organization.json."""
        known_person_ids = {p["person_id"] for p in org["persons"]}
        for zone in zones.values():
            for pid in zone.get("authorized_persons", []):
                assert pid in known_person_ids, f"Zone {zone['zone_id']} authorizes unknown person {pid}"

        exfil_scenario = load_scenario("exfiltration")
        assert exfil_scenario["actor"]["person_id"] in known_person_ids

    def test_no_invalid_device_references(self, zones, org):
        """All devices listed in zones must exist in the organization device registry."""
        known_devices = {d["device_id"] for d in org.get("devices", [])}
        for zone in zones.values():
            for dev_id in zone.get("devices", []):
                assert dev_id in known_devices, f"Zone {zone['zone_id']} references uncataloged device {dev_id}"


# ===========================================================================
# Collaboration and protected contracts tests
# ===========================================================================
class TestCollaborationAndContracts:
    """Verify multi-agent collaboration governance and protected contract documentation."""

    @pytest.mark.parametrize("doc_name", [
        "AI_MULTI_AGENT_COLLABORATION_RULES.md",
        "COMPONENT_CHANGE_MATRIX.md",
        "HANDOFF_CHECKLIST.md",
        "EVENT_CONTRACT.md",
        "INCIDENT_CONTRACT.md",
        "ZONE_POLICY.md",
        "ARCHITECTURE.md",
        "COMPONENT_BOUNDARIES.md",
        "DECISION_LOG.md",
    ])
    def test_governance_doc_exists(self, doc_name):
        doc_path = PROJECT_ROOT / "docs" / doc_name
        assert doc_path.exists(), f"Missing required governance doc: docs/{doc_name}"
        assert doc_path.stat().st_size > 200, f"Governance doc docs/{doc_name} is unexpectedly empty"

    @pytest.mark.parametrize("contract_path", [
        "schema/event.schema.json",
        "schema/incident.schema.json",
        "schema/scoring.schema.json",
        "config/organization.json",
        "config/zones.json",
        "config/scoring.json",
        "backend/contracts.py",
    ])
    def test_protected_contract_file_exists(self, contract_path):
        path = PROJECT_ROOT / contract_path
        assert path.exists(), f"Protected contract file missing: {contract_path}"


# ===========================================================================
# Event fixtures validation tests
# ===========================================================================
class TestEventFixturesValidation:
    """Verify every event fixture in tests/fixtures/events/ validates against event.schema.json."""

    def test_event_fixtures_directory_exists(self):
        fixtures_dir = PROJECT_ROOT / "tests" / "fixtures" / "events"
        assert fixtures_dir.exists()
        assert fixtures_dir.is_dir()

    def test_all_event_fixtures_validate(self):
        import jsonschema
        schema = load_event_schema()
        validator = jsonschema.Draft7Validator(schema)
        fixtures_dir = PROJECT_ROOT / "tests" / "fixtures" / "events"
        fixture_files = list(fixtures_dir.glob("*.json"))
        assert len(fixture_files) >= 11, f"Expected at least 11 fixtures, found {len(fixture_files)}"

        for fixture_file in fixture_files:
            with open(fixture_file, "r", encoding="utf-8") as f:
                event = json.load(f)
            errors = list(validator.iter_errors(event))
            assert not errors, f"Fixture {fixture_file.name} failed schema validation: {[e.message for e in errors]}"

