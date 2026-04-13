"""Tests for psai_bench.cost_model — Phase 18 Plan 02.

Task 1 tests (1-13): CostModel, DISPATCH_COSTS, compute_optimal_dispatch()
Task 2 tests (14-21): score_dispatch() with 3-assumption sensitivity analysis
"""
import copy
import pytest

from psai_bench.cost_model import (
    CostModel,
    CostScoreReport,
    DISPATCH_COSTS,
    SITE_THREAT_MULTIPLIERS,
    compute_optimal_dispatch,
    score_dispatch,
)
from psai_bench.schema import DISPATCH_ACTIONS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_scenario(gt="THREAT", site="substation", sensitivity=5, fpr=0.15, n_recent=0):
    return {
        "_meta": {"ground_truth": gt},
        "context": {"site_type": site, "recent_zone_events_1h": [{}] * n_recent},
        "zone": {"sensitivity": sensitivity},
        "device": {"false_positive_rate": fpr},
        "alert_id": f"test-{gt}-{site}",
    }


def _make_output(alert_id, dispatch="armed_response"):
    return {"alert_id": alert_id, "verdict": "THREAT", "confidence": 0.9, "dispatch": dispatch}


# ---------------------------------------------------------------------------
# Task 1: compute_optimal_dispatch() decision table
# ---------------------------------------------------------------------------


def test_01_threat_substation_sensitivity5_armed_response():
    """Example 1 from rubric: THREAT at substation → armed_response (site rule)."""
    result = compute_optimal_dispatch(
        "THREAT", {"site_type": "substation", "zone": {"sensitivity": 5}}
    )
    assert result == "armed_response"


def test_02_threat_solar_sensitivity4_armed_response():
    """THREAT at solar (critical infra) → armed_response regardless of sensitivity."""
    result = compute_optimal_dispatch(
        "THREAT", {"site_type": "solar", "zone": {"sensitivity": 4}}
    )
    assert result == "armed_response"


def test_03_threat_commercial_sensitivity2_patrol():
    """Example 2 from rubric: THREAT at commercial, sensitivity 2 → patrol."""
    result = compute_optimal_dispatch(
        "THREAT", {"site_type": "commercial", "zone": {"sensitivity": 2}}
    )
    assert result == "patrol"


def test_04_threat_campus_sensitivity1_patrol():
    """THREAT at campus, sensitivity 1 → patrol (low sensitivity cap)."""
    result = compute_optimal_dispatch(
        "THREAT", {"site_type": "campus", "zone": {"sensitivity": 1}}
    )
    assert result == "patrol"


def test_05_suspicious_sensitivity5_patrol():
    """Example 3 from rubric: SUSPICIOUS, sensitivity 5 >= 4 → patrol."""
    result = compute_optimal_dispatch(
        "SUSPICIOUS", {"zone": {"sensitivity": 5}}
    )
    assert result == "patrol"


def test_06_suspicious_sensitivity2_operator_review():
    """Example 4 from rubric: SUSPICIOUS, sensitivity 2 <= 3 → operator_review."""
    result = compute_optimal_dispatch(
        "SUSPICIOUS", {"zone": {"sensitivity": 2}}
    )
    assert result == "operator_review"


def test_07_benign_high_fpr_auto_suppress():
    """Example 5 from rubric: BENIGN, FPR=0.85 >= 0.70 → auto_suppress."""
    result = compute_optimal_dispatch(
        "BENIGN",
        {
            "zone": {"sensitivity": 2},
            "device": {"false_positive_rate": 0.85},
            "context": {"recent_zone_events_1h": []},
        },
    )
    assert result == "auto_suppress"


def test_08_benign_low_fpr_many_events_request_data():
    """Example 6 from rubric: BENIGN, FPR=0.40 < 0.70, 5 recent events >= 3 → request_data."""
    result = compute_optimal_dispatch(
        "BENIGN",
        {
            "zone": {"sensitivity": 2},
            "device": {"false_positive_rate": 0.40},
            "context": {"recent_zone_events_1h": [{}, {}, {}, {}, {}]},
        },
    )
    assert result == "request_data"


def test_09_benign_low_fpr_zero_events_auto_suppress():
    """BENIGN, FPR=0.40 < 0.70, 0 recent events → auto_suppress (otherwise branch)."""
    result = compute_optimal_dispatch(
        "BENIGN",
        {
            "zone": {"sensitivity": 2},
            "device": {"false_positive_rate": 0.40},
            "context": {"recent_zone_events_1h": []},
        },
    )
    assert result == "auto_suppress"


def test_10_invalid_gt_raises_value_error():
    """Unrecognized GT raises ValueError."""
    with pytest.raises(ValueError):
        compute_optimal_dispatch("INVALID", {})


def test_11_return_value_always_in_dispatch_actions():
    """Return value is always in DISPATCH_ACTIONS for any valid GT."""
    cases = [
        ("THREAT", {"site_type": "substation", "zone": {"sensitivity": 5}}),
        ("THREAT", {"site_type": "commercial", "zone": {"sensitivity": 1}}),
        ("SUSPICIOUS", {"zone": {"sensitivity": 4}}),
        ("SUSPICIOUS", {"zone": {"sensitivity": 1}}),
        ("BENIGN", {"zone": {"sensitivity": 1}, "device": {"false_positive_rate": 0.9}, "context": {"recent_zone_events_1h": []}}),
        ("BENIGN", {"zone": {"sensitivity": 1}, "device": {"false_positive_rate": 0.1}, "context": {"recent_zone_events_1h": [{}, {}, {}]}}),
    ]
    for gt, ctx in cases:
        result = compute_optimal_dispatch(gt, ctx)
        assert result in DISPATCH_ACTIONS, f"Got {result!r} for GT={gt!r}"


def test_12_cost_model_instantiation():
    """CostModel can be instantiated with no args; has costs and site_multipliers."""
    cm = CostModel()
    assert hasattr(cm, "costs")
    assert hasattr(cm, "site_multipliers")
    assert isinstance(cm.costs, dict)
    assert isinstance(cm.site_multipliers, dict)


def test_13_dispatch_costs_has_15_entries():
    """DISPATCH_COSTS has exactly 15 entries (5 actions × 3 GT classes)."""
    assert len(DISPATCH_COSTS) == 15


# ---------------------------------------------------------------------------
# Task 2: score_dispatch() with sensitivity analysis
# ---------------------------------------------------------------------------


def test_14_score_dispatch_with_dispatch_field_returns_report_with_cost_ratio():
    """score_dispatch() with all dispatches present returns CostScoreReport with cost_ratio > 0."""
    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    # Wrong dispatch (auto_suppress on THREAT) → incurs cost > 0 → cost_ratio > 1
    o = _make_output(s["alert_id"], dispatch="auto_suppress")
    report = score_dispatch([s], [o])
    assert isinstance(report, CostScoreReport)
    assert report.cost_ratio > 0


def test_15_score_dispatch_no_dispatch_field_n_missing():
    """score_dispatch() with no dispatch field returns n_missing_dispatch == len(outputs)."""
    scenarios = [_make_scenario(gt="THREAT", site="substation", sensitivity=5)]
    # Output has no dispatch field
    outputs = [{"alert_id": scenarios[0]["alert_id"], "verdict": "THREAT", "confidence": 0.9}]
    report = score_dispatch(scenarios, outputs)
    assert report.n_missing_dispatch == len(outputs)


def test_16_score_dispatch_per_action_counts_keys():
    """score_dispatch() returns per_action_counts with keys from DISPATCH_ACTIONS."""
    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], dispatch="armed_response")
    report = score_dispatch([s], [o])
    for action in DISPATCH_ACTIONS:
        assert action in report.per_action_counts


def test_17_sensitivity_profiles_structure():
    """CostScoreReport.sensitivity_profiles has keys 'low', 'medium', 'high'."""
    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], dispatch="armed_response")
    report = score_dispatch([s], [o])
    assert "low" in report.sensitivity_profiles
    assert "medium" in report.sensitivity_profiles
    assert "high" in report.sensitivity_profiles
    for key in ("low", "medium", "high"):
        assert "total_cost_usd" in report.sensitivity_profiles[key]
        assert "cost_ratio" in report.sensitivity_profiles[key]


def test_18_perfect_dispatcher_cost_ratio_one():
    """For perfect dispatcher (all actions match optimal), cost_ratio == 1.0."""
    # THREAT at substation, sensitivity 5 → optimal is armed_response
    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    # Optimal: armed_response (cost = 0.0 for THREAT), but we need > 0 to get ratio.
    # Use BENIGN with reliable device, few events → auto_suppress (cost 0.0 for BENIGN).
    # Actually cost(armed_response, THREAT) = 0.0 × multiplier = 0.0.
    # Use commercial SUSPICIOUS sensitivity=2 → operator_review, cost(operator_review, SUSPICIOUS)=0.0
    s2 = _make_scenario(gt="SUSPICIOUS", site="commercial", sensitivity=2)
    s2["alert_id"] = "test-suspicious-commercial"
    o2 = _make_output(s2["alert_id"], dispatch="operator_review")
    # Also use BENIGN auto_suppress (cost=0.0 for BENIGN)
    s3 = _make_scenario(gt="BENIGN", site="commercial", sensitivity=2, fpr=0.85)
    s3["alert_id"] = "test-benign-commercial"
    o3 = _make_output(s3["alert_id"], dispatch="auto_suppress")
    report = score_dispatch([s, s2, s3], [_make_output(s["alert_id"]), o2, o3])
    # All optimal → cost_ratio should be 1.0
    assert report.cost_ratio == pytest.approx(1.0, abs=1e-6)


def test_19_worst_dispatcher_cost_ratio_high():
    """Worst dispatcher (auto_suppress on THREAT at substation) → cost_ratio >> 1.0."""
    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], dispatch="auto_suppress")
    report = score_dispatch([s], [o])
    # auto_suppress on THREAT has base cost 1000, × site_multiplier(substation)=5 = 5000
    # optimal is armed_response: cost(armed_response, THREAT) = 0.0
    # So cost_ratio >> 1
    assert report.cost_ratio > 100


def test_20_score_dispatch_no_scorer_import():
    """score_dispatch does NOT import or call anything from scorer.py."""
    import ast
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "psai_bench", "cost_model.py"
    )
    with open(path) as f:
        tree = ast.parse(f.read())
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    scorer_imports = [
        n for n in imports
        if hasattr(n, "module") and n.module and "scorer" in n.module
    ]
    assert not scorer_imports, f"Found scorer imports: {scorer_imports}"


def test_21_per_site_mean_cost_has_unique_sites():
    """per_site_mean_cost dict has an entry for each unique site_type present in scenarios."""
    s1 = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    s2 = _make_scenario(gt="SUSPICIOUS", site="solar", sensitivity=3)
    s2["alert_id"] = "test-suspicious-solar"
    o1 = _make_output(s1["alert_id"], dispatch="auto_suppress")  # costly
    o2 = _make_output(s2["alert_id"], dispatch="patrol")
    report = score_dispatch([s1, s2], [o1, o2])
    assert "substation" in report.per_site_mean_cost
    assert "solar" in report.per_site_mean_cost
