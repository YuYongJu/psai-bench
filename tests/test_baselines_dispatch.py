"""Tests for dispatch field injection in all 4 baseline functions.

SCORE-03 requirement: all baseline outputs include a 'dispatch' key
so they can be evaluated with score_dispatch_run() without post-processing.
"""

import pytest

from psai_bench.baselines import (
    VERDICT_TO_DEFAULT_DISPATCH,
    always_suspicious_baseline,
    majority_class_baseline,
    random_baseline,
    severity_heuristic_baseline,
)
from psai_bench.schema import DISPATCH_ACTIONS


# ---------------------------------------------------------------------------
# Shared fixture: minimal valid scenarios for baseline testing
# ---------------------------------------------------------------------------

def _make_scenario(alert_id, ground_truth, severity="LOW", zone_type="perimeter"):
    return {
        "alert_id": alert_id,
        "timestamp": "2026-01-15T14:30:00+00:00",
        "track": "metadata",
        "severity": severity,
        "description": "Routine activity detected in monitored area",
        "source_type": "camera",
        "zone": {
            "id": "zone-1001",
            "name": "North Fence Line",
            "type": zone_type,
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
            "expected_activities": [],
            "site_type": "commercial",
        },
        "_meta": {
            "ground_truth": ground_truth,
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Normal",
            "seed": 42,
            "index": 0,
        },
    }


@pytest.fixture
def mixed_scenarios():
    """Small set of scenarios covering THREAT / SUSPICIOUS / BENIGN ground truths."""
    return [
        _make_scenario("a1", "THREAT", severity="CRITICAL"),
        _make_scenario("a2", "SUSPICIOUS", severity="MEDIUM"),
        _make_scenario("a3", "BENIGN", severity="LOW"),
    ]


# ---------------------------------------------------------------------------
# VERDICT_TO_DEFAULT_DISPATCH mapping correctness
# ---------------------------------------------------------------------------

def test_verdict_to_dispatch_mapping_importable():
    """VERDICT_TO_DEFAULT_DISPATCH must be importable from psai_bench.baselines."""
    assert isinstance(VERDICT_TO_DEFAULT_DISPATCH, dict)


def test_verdict_to_dispatch_mapping_values():
    """Every value in VERDICT_TO_DEFAULT_DISPATCH is a member of DISPATCH_ACTIONS."""
    for verdict, action in VERDICT_TO_DEFAULT_DISPATCH.items():
        assert action in DISPATCH_ACTIONS, (
            f"VERDICT_TO_DEFAULT_DISPATCH[{verdict!r}] = {action!r} "
            f"is not in DISPATCH_ACTIONS"
        )


def test_verdict_to_dispatch_mapping_covers_all_verdicts():
    """VERDICT_TO_DEFAULT_DISPATCH must cover all 3 verdict classes exactly."""
    from psai_bench.schema import VERDICTS
    for v in VERDICTS:
        assert v in VERDICT_TO_DEFAULT_DISPATCH, (
            f"Verdict {v!r} missing from VERDICT_TO_DEFAULT_DISPATCH"
        )


def test_verdict_to_dispatch_explicit_values():
    """Assert exact mapping values per CONTEXT.md decision."""
    assert VERDICT_TO_DEFAULT_DISPATCH["THREAT"] == "armed_response"
    assert VERDICT_TO_DEFAULT_DISPATCH["SUSPICIOUS"] == "operator_review"
    assert VERDICT_TO_DEFAULT_DISPATCH["BENIGN"] == "auto_suppress"


# ---------------------------------------------------------------------------
# random_baseline
# ---------------------------------------------------------------------------

def test_random_baseline_has_dispatch_field(mixed_scenarios):
    """Every output from random_baseline has a 'dispatch' key."""
    outputs = random_baseline(mixed_scenarios, seed=42)
    assert len(outputs) == len(mixed_scenarios)
    for out in outputs:
        assert "dispatch" in out, f"Missing 'dispatch' in output: {out}"


def test_random_baseline_dispatch_in_dispatch_actions(mixed_scenarios):
    """random_baseline dispatch values are all in DISPATCH_ACTIONS."""
    outputs = random_baseline(mixed_scenarios, seed=42)
    for out in outputs:
        assert out["dispatch"] in DISPATCH_ACTIONS


def test_random_baseline_dispatch_matches_verdict(mixed_scenarios):
    """random_baseline dispatch == VERDICT_TO_DEFAULT_DISPATCH[verdict] for each output."""
    outputs = random_baseline(mixed_scenarios, seed=42)
    for out in outputs:
        expected = VERDICT_TO_DEFAULT_DISPATCH[out["verdict"]]
        assert out["dispatch"] == expected


def test_random_baseline_existing_keys_preserved(mixed_scenarios):
    """All original keys are still present — no regressions."""
    required_keys = {
        "alert_id", "verdict", "confidence", "reasoning",
        "factors_considered", "processing_time_ms", "model_info",
    }
    outputs = random_baseline(mixed_scenarios, seed=42)
    for out in outputs:
        assert required_keys.issubset(out.keys()), (
            f"Missing keys in output: {required_keys - out.keys()}"
        )


# ---------------------------------------------------------------------------
# majority_class_baseline
# ---------------------------------------------------------------------------

def test_majority_class_baseline_has_dispatch_field(mixed_scenarios):
    """Every output from majority_class_baseline has a 'dispatch' key."""
    outputs = majority_class_baseline(mixed_scenarios)
    assert len(outputs) == len(mixed_scenarios)
    for out in outputs:
        assert "dispatch" in out, f"Missing 'dispatch' in output: {out}"


def test_majority_class_baseline_dispatch_in_dispatch_actions(mixed_scenarios):
    """majority_class_baseline dispatch values are all in DISPATCH_ACTIONS."""
    outputs = majority_class_baseline(mixed_scenarios)
    for out in outputs:
        assert out["dispatch"] in DISPATCH_ACTIONS


def test_majority_class_baseline_dispatch_matches_verdict(mixed_scenarios):
    """majority_class_baseline dispatch == VERDICT_TO_DEFAULT_DISPATCH[verdict]."""
    outputs = majority_class_baseline(mixed_scenarios)
    for out in outputs:
        expected = VERDICT_TO_DEFAULT_DISPATCH[out["verdict"]]
        assert out["dispatch"] == expected


def test_majority_class_baseline_existing_keys_preserved(mixed_scenarios):
    """All original keys are still present — no regressions."""
    required_keys = {
        "alert_id", "verdict", "confidence", "reasoning",
        "factors_considered", "processing_time_ms", "model_info",
    }
    outputs = majority_class_baseline(mixed_scenarios)
    for out in outputs:
        assert required_keys.issubset(out.keys())


# ---------------------------------------------------------------------------
# always_suspicious_baseline
# ---------------------------------------------------------------------------

def test_always_suspicious_baseline_has_dispatch_field(mixed_scenarios):
    """Every output from always_suspicious_baseline has a 'dispatch' key."""
    outputs = always_suspicious_baseline(mixed_scenarios)
    assert len(outputs) == len(mixed_scenarios)
    for out in outputs:
        assert "dispatch" in out, f"Missing 'dispatch' in output: {out}"


def test_always_suspicious_baseline_dispatch_is_operator_review(mixed_scenarios):
    """always_suspicious_baseline always produces dispatch='operator_review'."""
    outputs = always_suspicious_baseline(mixed_scenarios)
    for out in outputs:
        assert out["dispatch"] == "operator_review", (
            f"Expected 'operator_review' (SUSPICIOUS verdict), got {out['dispatch']!r}"
        )


def test_always_suspicious_baseline_existing_keys_preserved(mixed_scenarios):
    """All original keys are still present — no regressions."""
    required_keys = {
        "alert_id", "verdict", "confidence", "reasoning",
        "factors_considered", "processing_time_ms", "model_info",
    }
    outputs = always_suspicious_baseline(mixed_scenarios)
    for out in outputs:
        assert required_keys.issubset(out.keys())


# ---------------------------------------------------------------------------
# severity_heuristic_baseline
# ---------------------------------------------------------------------------

def test_severity_heuristic_baseline_has_dispatch_field(mixed_scenarios):
    """Every output from severity_heuristic_baseline has a 'dispatch' key."""
    outputs = severity_heuristic_baseline(mixed_scenarios)
    assert len(outputs) == len(mixed_scenarios)
    for out in outputs:
        assert "dispatch" in out, f"Missing 'dispatch' in output: {out}"


def test_severity_heuristic_critical_verdict_and_dispatch():
    """CRITICAL severity → verdict=THREAT, dispatch=armed_response."""
    scenario = _make_scenario("crit-1", "THREAT", severity="CRITICAL", zone_type="perimeter")
    outputs = severity_heuristic_baseline([scenario])
    out = outputs[0]
    assert out["verdict"] == "THREAT"
    assert out["dispatch"] == "armed_response"


def test_severity_heuristic_low_verdict_and_dispatch():
    """LOW severity → verdict=BENIGN, dispatch=auto_suppress."""
    scenario = _make_scenario("low-1", "BENIGN", severity="LOW", zone_type="perimeter")
    outputs = severity_heuristic_baseline([scenario])
    out = outputs[0]
    assert out["verdict"] == "BENIGN"
    assert out["dispatch"] == "auto_suppress"


def test_severity_heuristic_dispatch_matches_verdict(mixed_scenarios):
    """severity_heuristic_baseline dispatch == VERDICT_TO_DEFAULT_DISPATCH[verdict] for each output."""
    outputs = severity_heuristic_baseline(mixed_scenarios)
    for out in outputs:
        expected = VERDICT_TO_DEFAULT_DISPATCH[out["verdict"]]
        assert out["dispatch"] == expected


def test_severity_heuristic_existing_keys_preserved(mixed_scenarios):
    """All original keys are still present — no regressions."""
    required_keys = {
        "alert_id", "verdict", "confidence", "reasoning",
        "factors_considered", "processing_time_ms", "model_info",
    }
    outputs = severity_heuristic_baseline(mixed_scenarios)
    for out in outputs:
        assert required_keys.issubset(out.keys())
