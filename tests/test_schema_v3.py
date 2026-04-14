"""Tests for Schema v3 changes: track enum extension, required relaxation, _meta v3 fields,
track-aware validation, and None-safe description handling.

All tests in this file are regression tests — they encode what the schema MUST accept
and reject after Phase 11 changes. If any test fails after a future change, it means
something that was supposed to be valid is now rejected, or vice versa.
"""

import pytest
from jsonschema import ValidationError

from psai_bench.schema import _META_SCHEMA_V2, validate_alert
from psai_bench.validation import validate_scenarios


# ---------------------------------------------------------------------------
# Helpers — minimal valid scenario dicts for each track
# ---------------------------------------------------------------------------

def _base_v2_scenario(alert_id="test-001"):
    """Minimal valid v2 scenario (has severity + description — both required in v2)."""
    return {
        "alert_id": alert_id,
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


def _visual_only_scenario(alert_id="vis-001"):
    """Minimal valid v3 visual_only scenario — no severity or description."""
    s = _base_v2_scenario(alert_id)
    s["track"] = "visual_only"
    del s["severity"]
    del s["description"]
    s["visual_data"] = {
        "type": "video_clip",
        "uri": "ucf_crime/Burglary/Burglary_001.mp4",
        "duration_sec": 60.0,
        "resolution": "1280x720",
    }
    s["_meta"]["visual_gt_source"] = "video_category"
    s["_meta"]["generation_version"] = "v3"
    return s


class TestSchemaV3TrackEnum:
    """Track enum accepts new v3 values and still accepts v2 values."""

    def test_metadata_track_still_valid(self):
        validate_alert(_base_v2_scenario())  # must not raise

    def test_visual_track_still_valid(self):
        s = _base_v2_scenario()
        s["track"] = "visual"
        s["visual_data"] = {"type": "video_clip", "uri": "some/path.mp4",
                            "duration_sec": 30.0, "resolution": "1280x720"}
        validate_alert(s)  # must not raise

    def test_visual_only_track_accepted(self):
        validate_alert(_visual_only_scenario())  # must not raise

    def test_visual_contradictory_track_accepted(self):
        s = _visual_only_scenario()
        s["track"] = "visual_contradictory"
        validate_alert(s)  # must not raise

    def test_temporal_track_accepted(self):
        s = _base_v2_scenario()
        s["track"] = "temporal"
        validate_alert(s)  # must not raise

    def test_unknown_track_rejected(self):
        s = _base_v2_scenario()
        s["track"] = "not_a_valid_track"
        with pytest.raises(ValidationError):
            validate_alert(s)


class TestSchemaV3RequiredRelaxed:
    """severity and description are no longer schema-required; zone/device/context still required."""

    def test_v3_scenario_without_severity_validates(self):
        s = _base_v2_scenario()
        s["track"] = "visual_only"
        del s["severity"]
        validate_alert(s)  # must not raise

    def test_v3_scenario_without_description_validates(self):
        s = _base_v2_scenario()
        s["track"] = "visual_only"
        del s["description"]
        validate_alert(s)  # must not raise

    def test_v3_scenario_without_both_severity_and_description_validates(self):
        validate_alert(_visual_only_scenario())  # must not raise

    def test_scenario_without_zone_still_rejected(self):
        s = _base_v2_scenario()
        del s["zone"]
        with pytest.raises(ValidationError):
            validate_alert(s)

    def test_scenario_without_device_still_rejected(self):
        s = _base_v2_scenario()
        del s["device"]
        with pytest.raises(ValidationError):
            validate_alert(s)

    def test_scenario_without_context_still_rejected(self):
        s = _base_v2_scenario()
        del s["context"]
        with pytest.raises(ValidationError):
            validate_alert(s)


class TestMetaSchemaV3Fields:
    """_meta v3 fields are accepted when present (all optional)."""

    def test_v3_meta_fields_accepted(self):
        from jsonschema import validate
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

    def test_contradictory_flag_accepted(self):
        from jsonschema import validate
        meta = {
            "ground_truth": "THREAT",
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Burglary",
            "seed": 42,
            "index": 0,
            "generation_version": "v3",
            "visual_gt_source": "video_category",
            "contradictory": True,
        }
        validate(instance=meta, schema=_META_SCHEMA_V2)  # must not raise

    def test_sequence_fields_accepted(self):
        from jsonschema import validate
        meta = {
            "ground_truth": "SUSPICIOUS",
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Arrest",
            "seed": 42,
            "index": 5,
            "generation_version": "v3",
            "sequence_id": "seq-0001",
            "sequence_position": 2,
            "sequence_length": 4,
        }
        validate(instance=meta, schema=_META_SCHEMA_V2)  # must not raise

    def test_v2_meta_still_valid_without_v3_fields(self):
        """v2 _meta must still validate — backward compat."""
        from jsonschema import validate
        meta = {
            "ground_truth": "BENIGN",
            "difficulty": "easy",
            "source_dataset": "ucf_crime",
            "source_category": "Normal",
            "seed": 42,
            "index": 0,
            "generation_version": "v2",
            "weighted_sum": 0.3,
            "adversarial": False,
            "ambiguity_flag": False,
            "description_category": "ambiguous",
        }
        validate(instance=meta, schema=_META_SCHEMA_V2)  # must not raise


class TestTrackAwareValidation:
    """validate_scenarios enforces track-specific field requirements."""

    def test_visual_only_missing_uri_is_error(self):
        s = _visual_only_scenario()
        s["visual_data"]["uri"] = None  # clear the URI
        report = validate_scenarios([s])
        assert not report.passed
        assert any("visual_data.uri" in e for e in report.errors)

    def test_visual_only_with_uri_passes(self):
        s = _visual_only_scenario()
        report = validate_scenarios([s])
        # Should pass (no errors) or only warnings about distribution/track mixing
        assert not any("visual_data.uri" in e for e in report.errors)

    def test_visual_contradictory_missing_contradictory_flag_is_error(self):
        s = _visual_only_scenario()
        s["track"] = "visual_contradictory"
        # _meta.contradictory not set (or False)
        s["_meta"].pop("contradictory", None)
        report = validate_scenarios([s])
        assert not report.passed
        assert any("contradictory" in e for e in report.errors)

    def test_temporal_missing_sequence_id_is_error(self):
        s = _base_v2_scenario()
        s["track"] = "temporal"
        # _meta.sequence_id not set
        report = validate_scenarios([s])
        assert not report.passed
        assert any("sequence_id" in e for e in report.errors)

    def test_none_description_does_not_raise(self):
        """validate_scenarios must not raise AttributeError when description=None."""
        s = _visual_only_scenario()
        s["description"] = None  # explicitly None, not absent
        # This would raise AttributeError if the None-safe fix was not applied
        try:
            validate_scenarios([s])
        except AttributeError as e:
            pytest.fail(f"validate_scenarios raised AttributeError on description=None: {e}")
