"""Phase 15 regression test suite.

Guards:
- score_run() contract (signature and return type)
- compute_perception_gap() correctness and error handling
- Track-aware validation behavior (SCORE-04)
- Full test_core.py regression (all tests still pass)
"""

import inspect
import subprocess

import pytest

from psai_bench.scorer import (
    ScoreReport,
    compute_perception_gap,
    score_run,
)
from psai_bench.generators import MetadataGenerator, VisualOnlyGenerator
from psai_bench.validation import validate_scenarios


# ---------------------------------------------------------------------------
# Helpers (duplicated from test_core.py since tests/ has no __init__.py)
# ---------------------------------------------------------------------------

def _make_scenario(alert_id, ground_truth, difficulty="medium", dataset="ucf_crime", category="Normal"):
    """Minimal valid scenario for testing scorer/validation."""
    return {
        "alert_id": alert_id,
        "timestamp": "2026-01-15T14:30:00+00:00",
        "track": "metadata",
        "severity": "LOW",
        "description": "Routine activity detected in monitored area",
        "source_type": "camera",
        "zone": {
            "id": "zone-1001",
            "name": "North Fence Line",
            "type": "perimeter",
            "sensitivity": 3,
            "operating_hours": "24/7",
        },
        "device": {
            "id": "cam-10001",
            "false_positive_rate": 0.6,
            "total_events_30d": 200,
            "model": "Axis-P3245-V",
        },
        "context": {
            "recent_zone_events_1h": [],
            "weather": {"condition": "clear", "temp_f": 72.0, "wind_mph": 5.0},
            "time_of_day": "day",
            "expected_activities": ["scheduled maintenance crew"],
            "site_type": "solar",
        },
        "visual_data": None,
        "additional_sensors": [],
        "_meta": {
            "ground_truth": ground_truth,
            "difficulty": difficulty,
            "source_dataset": dataset,
            "source_category": category,
            "seed": 42,
            "index": 0,
        },
    }


def _make_output(alert_id, verdict, confidence=0.85):
    """Minimal valid output dict."""
    return {
        "alert_id": alert_id,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": "This is a test reasoning string that meets the twenty word minimum requirement for the benchmark output schema.",
        "factors_considered": ["severity", "zone"],
        "processing_time_ms": 150,
        "model_info": {
            "name": "test-model",
            "version": "1.0",
            "provider": "test",
            "estimated_cost_usd": 0.001,
        },
    }


def _make_visual_only_scenario(alert_id, ground_truth, has_uri=True):
    s = _make_scenario(alert_id, ground_truth)
    s["track"] = "visual_only"
    s["visual_data"] = {
        "type": "video_clip",
        "uri": "ucf-crime/Normal/00001.mp4" if has_uri else None,
        "duration_sec": 10.0,
        "resolution": "1280x720",
        "keyframe_uris": [],
    }
    s["_meta"]["visual_gt_source"] = "video_category"
    return s


def _make_temporal_scenario(alert_id, ground_truth, seq_id, position, seq_length):
    s = _make_scenario(alert_id, ground_truth)
    s["track"] = "temporal"
    s["_meta"]["sequence_id"] = seq_id
    s["_meta"]["sequence_position"] = position
    s["_meta"]["sequence_length"] = seq_length
    s["_meta"]["escalation_pattern"] = "monotonic_escalation"
    return s


# ---------------------------------------------------------------------------
# 1. TestComputePerceptionGap (RED — compute_perception_gap does not exist yet)
# ---------------------------------------------------------------------------

class TestComputePerceptionGap:

    def test_gap_positive(self):
        """metadata agg=0.75, visual agg=0.60 -> gap == 0.15."""
        m = ScoreReport(aggregate_score=0.75, n_scenarios=100)
        v = ScoreReport(aggregate_score=0.60, n_scenarios=100)
        gap = compute_perception_gap(m, v)
        assert abs(gap - 0.15) < 1e-9, f"Expected 0.15, got {gap}"

    def test_gap_negative(self):
        """metadata agg=0.55, visual agg=0.70 -> gap == -0.15."""
        m = ScoreReport(aggregate_score=0.55, n_scenarios=100)
        v = ScoreReport(aggregate_score=0.70, n_scenarios=100)
        gap = compute_perception_gap(m, v)
        assert abs(gap - (-0.15)) < 1e-9, f"Expected -0.15, got {gap}"

    def test_gap_zero(self):
        """Same report used for both -> gap == 0.0."""
        r = ScoreReport(aggregate_score=0.80, n_scenarios=50)
        gap = compute_perception_gap(r, r)
        assert gap == 0.0

    def test_gap_raises_on_empty_metadata(self):
        """metadata n_scenarios=0 -> ValueError with 'metadata_report' in message."""
        v = ScoreReport(aggregate_score=0.60, n_scenarios=100)
        with pytest.raises(ValueError, match="metadata_report"):
            compute_perception_gap(ScoreReport(n_scenarios=0), v)

    def test_gap_raises_on_empty_visual(self):
        """visual n_scenarios=0 -> ValueError with 'visual_report' in message."""
        m = ScoreReport(aggregate_score=0.75, n_scenarios=100)
        with pytest.raises(ValueError, match="visual_report"):
            compute_perception_gap(m, ScoreReport(n_scenarios=0))

    def test_gap_with_real_scored_reports(self):
        """Generate 50 metadata + 50 visual_only scenarios, score each, compute gap."""
        # Metadata scenarios
        meta_gen = MetadataGenerator(seed=99)
        meta_scenarios = meta_gen.generate_ucf_crime(n=50)
        meta_outputs = [
            _make_output(s["alert_id"], "BENIGN") for s in meta_scenarios
        ]
        meta_report = score_run(meta_scenarios, meta_outputs)

        # Visual-only scenarios
        visual_gen = VisualOnlyGenerator(seed=99)
        visual_scenarios = visual_gen.generate(n=50)
        visual_outputs = [
            _make_output(s["alert_id"], "BENIGN") for s in visual_scenarios
        ]
        visual_report = score_run(visual_scenarios, visual_outputs)

        gap = compute_perception_gap(meta_report, visual_report)
        assert isinstance(gap, float)


# ---------------------------------------------------------------------------
# 2. TestScoreRunContractGuard
# ---------------------------------------------------------------------------

class TestScoreRunContractGuard:

    def test_score_run_signature_unchanged(self):
        """score_run() must have exactly ['scenarios', 'outputs'] parameters."""
        sig = inspect.signature(score_run)
        params = list(sig.parameters.keys())
        assert params == ["scenarios", "outputs"], (
            f"score_run signature changed — expected ['scenarios', 'outputs'], got {params}"
        )

    def test_score_run_returns_score_report(self):
        """score_run([], []) must return a ScoreReport instance."""
        result = score_run([], [])
        assert isinstance(result, ScoreReport)

    def test_score_run_empty_returns_zero_report(self):
        """score_run([], []) returns ScoreReport with n_scenarios==0."""
        result = score_run([], [])
        assert result.n_scenarios == 0


# ---------------------------------------------------------------------------
# 3. TestTrackValidationBehavior (SCORE-04)
# ---------------------------------------------------------------------------

class TestTrackValidationBehavior:

    def test_visual_only_missing_uri_is_error(self):
        """visual_only scenario with visual_data.uri=None -> validation fails with visual_data.uri in error."""
        scenario = _make_visual_only_scenario("vo-001", "BENIGN", has_uri=False)
        report = validate_scenarios([scenario])
        assert not report.passed
        assert any("visual_data.uri" in e for e in report.errors), (
            f"Expected 'visual_data.uri' in errors, got: {report.errors}"
        )

    def test_visual_contradictory_missing_contradictory_flag_is_error(self):
        """visual_contradictory without _meta.contradictory -> validation fails."""
        scenario = _make_visual_only_scenario("vc-001", "THREAT", has_uri=True)
        scenario["track"] = "visual_contradictory"
        # _meta.contradictory is NOT set (missing)
        report = validate_scenarios([scenario])
        assert not report.passed

    def test_temporal_missing_sequence_id_is_error(self):
        """temporal track without _meta.sequence_id -> validation fails."""
        scenario = _make_scenario("t-001", "THREAT")
        scenario["track"] = "temporal"
        scenario["_meta"]["sequence_position"] = 1
        # sequence_id deliberately omitted
        report = validate_scenarios([scenario])
        assert not report.passed

    def test_valid_visual_only_passes(self):
        """Well-formed visual_only scenario with uri set -> no track errors."""
        scenario = _make_visual_only_scenario("vo-ok-001", "BENIGN", has_uri=True)
        report = validate_scenarios([scenario])
        # Should have no track-related errors (warnings about distribution are ok)
        track_errors = [e for e in report.errors if "track" in e.lower() or "visual_data.uri" in e]
        assert len(track_errors) == 0, f"Unexpected track errors: {track_errors}"


# ---------------------------------------------------------------------------
# 4. TestFullRegression133
# ---------------------------------------------------------------------------

class TestFullRegression133:

    def test_all_core_tests_pass(self):
        """Guard: all tests in test_core.py must pass with no modifications."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_core.py", "-q", "--tb=short"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"test_core.py regression failed:\n{result.stdout}\n{result.stderr}"
        )
