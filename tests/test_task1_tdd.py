"""TDD RED tests for Task 1: schema v3 changes.

These are the minimal tests to drive Task 1 implementation.
After Task 2 creates the comprehensive test_schema_v3.py, these
remain as a record of the TDD process. They should all pass after
implementation.
"""
import pytest
from jsonschema import validate

from psai_bench.schema import _META_SCHEMA_V2, validate_alert


def _base_scenario():
    """Minimal valid v2 scenario."""
    return {
        "alert_id": "tdd-001",
        "timestamp": "2026-01-01T12:00:00+00:00",
        "track": "metadata",
        "severity": "HIGH",
        "description": "Suspicious activity detected near perimeter fence.",
        "source_type": "camera",
        "zone": {
            "id": "z-001", "name": "North Perimeter", "type": "perimeter",
            "sensitivity": 4, "operating_hours": "00:00-24:00",
        },
        "device": {
            "id": "cam-001", "false_positive_rate": 0.15,
            "total_events_30d": 120, "model": "Axis P3245",
        },
        "context": {
            "recent_zone_events_1h": [],
            "weather": {"condition": "clear", "temp_f": 65.0, "wind_mph": 5.0},
            "time_of_day": "night",
            "expected_activities": [],
            "site_type": "solar",
        },
        "visual_data": None,
        "additional_sensors": [],
        "_meta": {
            "ground_truth": "THREAT",
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Burglary",
            "seed": 42,
            "index": 0,
            "generation_version": "v2",
        },
    }


class TestTask1TDD:
    """RED tests driving Task 1 implementation."""

    def test1_v2_scenario_validates(self):
        """Test 1: existing v2 scenario (has severity + description) validates — backward compat."""
        validate_alert(_base_scenario())  # must not raise

    def test2_v3_scenario_without_severity_validates(self):
        """Test 2: v3 scenario missing severity validates — severity no longer required."""
        s = _base_scenario()
        s["track"] = "visual_only"
        del s["severity"]
        validate_alert(s)  # must not raise after schema change

    def test3_visual_only_track_accepted(self):
        """Test 3: track='visual_only' must be in the track enum."""
        s = _base_scenario()
        s["track"] = "visual_only"
        del s["severity"]
        del s["description"]
        validate_alert(s)  # must not raise after track enum extension

    def test4_v3_meta_fields_validate(self):
        """Test 4: _meta v3 fields are accepted (all optional)."""
        meta = {
            "ground_truth": "THREAT",
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Burglary",
            "seed": 42,
            "index": 0,
            "generation_version": "v3",
            "visual_gt_source": "video_category",
            "contradictory": False,
            "sequence_id": None,
            "sequence_position": None,
            "sequence_length": None,
        }
        validate(instance=meta, schema=_META_SCHEMA_V2)  # must not raise

    def test5_description_none_does_not_raise(self):
        """Test 5: validate_scenarios with description=None must not raise AttributeError."""
        from psai_bench.validation import validate_scenarios
        s = _base_scenario()
        s["description"] = None  # explicitly None
        try:
            validate_scenarios([s])
        except AttributeError as e:
            pytest.fail(f"validate_scenarios raised AttributeError on description=None: {e}")

    def test6_visual_only_track_cli_succeeds(self):
        """Test 6: psai-bench generate --track visual_only now succeeds (Phase 12 implemented)."""
        import json
        import tempfile
        from pathlib import Path

        from click.testing import CliRunner

        from psai_bench.cli import generate

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.invoke(generate, [
                "--track", "visual_only", "--n", "5", "--output", tmp,
            ])
            assert result.exit_code == 0, (
                f"Expected exit_code 0 for visual_only track, got {result.exit_code}: {result.output!r}"
            )
            # Verify output file was written with correct scenarios
            out_files = list(Path(tmp).glob("visual_only_*.json"))
            assert len(out_files) == 1, f"Expected 1 output file, got: {out_files}"
            data = json.loads(out_files[0].read_text())
            assert len(data) == 5
            assert all(s["track"] == "visual_only" for s in data)
