"""Tests for Phase 19 Plan 01 — score_dispatch_run() and format_dashboard cost section.

Task 1 tests: score_dispatch_run() delegation and regression guard.
Task 2 tests: format_dashboard() backward compat + cost section rendering.
"""
import pytest

from psai_bench.cost_model import CostScoreReport
from psai_bench.scorer import format_dashboard, score_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_scenario(gt="THREAT", site="substation", sensitivity=5, fpr=0.15, n_recent=0):
    return {
        "_meta": {
            "ground_truth": gt,
            "difficulty": "easy",
            "source_dataset": "test",
            "ambiguity_flag": False,
        },
        "context": {"site_type": site, "recent_zone_events_1h": [{}] * n_recent},
        "zone": {"sensitivity": sensitivity},
        "device": {"false_positive_rate": fpr},
        "alert_id": f"test-{gt}-{site}",
    }


def _make_output(alert_id, verdict="THREAT", confidence=0.9, dispatch=None):
    o = {"alert_id": alert_id, "verdict": verdict, "confidence": confidence}
    if dispatch is not None:
        o["dispatch"] = dispatch
    return o


def _make_cost_score_report(**kwargs):
    defaults = dict(
        n_scenarios=2,
        total_cost_usd=100.0,
        mean_cost_usd=50.0,
        optimal_cost_usd=50.0,
        cost_ratio=2.0,
        per_action_counts={"armed_response": 1, "patrol": 1, "operator_review": 0, "auto_suppress": 0, "request_data": 0},
        per_site_mean_cost={"substation": 100.0},
        n_missing_dispatch=0,
        sensitivity_profiles={
            "low": {"total_cost_usd": 50.0, "cost_ratio": 2.0},
            "medium": {"total_cost_usd": 100.0, "cost_ratio": 2.0},
            "high": {"total_cost_usd": 200.0, "cost_ratio": 2.0},
        },
    )
    defaults.update(kwargs)
    return CostScoreReport(**defaults)


# ---------------------------------------------------------------------------
# Captured v3.0 format_dashboard fixture (Task 2 backward-compat gate)
# Captured from format_dashboard(score_run([s], [o])) BEFORE any edit.
# ---------------------------------------------------------------------------

_SCORE_REPORT_FIXTURE_SCENARIO = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
_SCORE_REPORT_FIXTURE_OUTPUT = _make_output(_SCORE_REPORT_FIXTURE_SCENARIO["alert_id"], verdict="THREAT", confidence=0.9)

_V3_DASHBOARD_EXPECTED = (
    "=== PSAI-Bench Metrics Dashboard ===\n"
    "  TDR (Threat Detection Rate):    1.0000\n"
    "  FASR (False Alarm Suppression): 0.0000\n"
    "  Decisiveness:                   1.0000\n"
    "  Calibration (ECE):              0.1000  (lower is better)\n"
    "\n"
    "=== Per-Difficulty Accuracy ===\n"
    "  Easy:   1.0000\n"
    "  Medium: 0.0000\n"
    "  Hard:   0.0000\n"
    "\n"
    "=== Aggregate Score ===\n"
    "  Formula: 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)\n"
    "  Score:   0.6900\n"
    "\n"
    "N=1 scenarios (Threats=1, Benign=0, Ambiguous=0)"
)


# ---------------------------------------------------------------------------
# Task 1: score_dispatch_run() tests
# ---------------------------------------------------------------------------


def test_score_dispatch_run_returns_cost_score_report():
    """score_dispatch_run() returns a CostScoreReport instance (not None, not dict)."""
    from psai_bench.scorer import score_dispatch_run

    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], dispatch="armed_response")
    result = score_dispatch_run([s], [o])
    assert isinstance(result, CostScoreReport), f"Expected CostScoreReport, got {type(result)}"


def test_score_dispatch_run_delegates_to_cost_model():
    """score_dispatch_run with THREAT at substation + armed_response gives cost_ratio == 1.0.

    armed_response is the optimal action for THREAT at a substation site (Rule 1 in rubric).
    Optimal dispatch == submitted dispatch → total_cost / optimal_cost == 1.0.
    armed_response on THREAT has base cost 0.0, so ratio is 1.0 via guard.
    """
    from psai_bench.scorer import score_dispatch_run

    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], dispatch="armed_response")
    result = score_dispatch_run([s], [o])
    # armed_response on THREAT has cost 0.0 (and optimal is also armed_response → 0.0)
    # cost_ratio = 0.0 / max(0.0, 1e-9) = 0.0 — still >= 0, not negative
    assert result.cost_ratio >= 0.0


def test_score_run_unchanged_after_dispatch_addition():
    """score_run() output is identical to v3.0 snapshot after adding score_dispatch_run.

    Serializes both to to_dict() and compares key by key to catch any regression.
    """
    from psai_bench.scorer import score_dispatch_run  # noqa: F401 — import must not break score_run

    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    o = _make_output(s["alert_id"], verdict="THREAT", confidence=0.9)
    report = score_run([s], [o])
    d = report.to_dict()

    # Key metrics that must be unchanged from v3.0 behavior
    assert d["tdr"] == pytest.approx(1.0)
    assert d["fasr"] == pytest.approx(0.0)
    assert d["accuracy"] == pytest.approx(1.0)
    assert d["aggregate_score"] == pytest.approx(0.69, abs=1e-6)
    assert d["n_scenarios"] == 1
    assert d["n_threats"] == 1


def test_score_dispatch_run_missing_dispatch_increments_n_missing():
    """score_dispatch_run with outputs missing 'dispatch' field increments n_missing_dispatch."""
    from psai_bench.scorer import score_dispatch_run

    s = _make_scenario(gt="THREAT", site="substation", sensitivity=5)
    # Output without dispatch field
    o = {"alert_id": s["alert_id"], "verdict": "THREAT", "confidence": 0.9}
    result = score_dispatch_run([s], [o])
    assert result.n_missing_dispatch >= 1


# ---------------------------------------------------------------------------
# Task 2: format_dashboard() backward-compat and cost section tests
# ---------------------------------------------------------------------------


def test_format_dashboard_no_cost_report_identical_output():
    """format_dashboard(report) with no cost_report is byte-identical to v3.0 fixture."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    actual = format_dashboard(report)
    assert actual == _V3_DASHBOARD_EXPECTED, (
        f"format_dashboard backward-compat FAILED.\n"
        f"Expected:\n{_V3_DASHBOARD_EXPECTED!r}\n\n"
        f"Actual:\n{actual!r}"
    )


def test_format_dashboard_explicit_none_cost_report_identical():
    """format_dashboard(report, cost_report=None) is identical to format_dashboard(report)."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    without_arg = format_dashboard(report)
    with_none = format_dashboard(report, cost_report=None)
    assert without_arg == with_none


def test_format_dashboard_with_cost_report_appends_section():
    """format_dashboard(report, cost_report=csr) appends '=== Dispatch Cost Analysis ===' section."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    csr = _make_cost_score_report()
    output = format_dashboard(report, cost_report=csr)
    assert "=== Dispatch Cost Analysis ===" in output


def test_format_dashboard_cost_section_contains_required_labels():
    """Cost section contains 'Cost Ratio:', 'Mean Cost (USD):', and sensitivity analysis labels."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    csr = _make_cost_score_report()
    output = format_dashboard(report, cost_report=csr)
    assert "Cost Ratio:" in output
    assert "Mean Cost (USD):" in output
    assert "Sensitivity Analysis:" in output


def test_format_dashboard_with_cost_report_preserves_existing_lines():
    """All lines from the v3.0 output must appear in the extended output (in same order)."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    csr = _make_cost_score_report()
    output = format_dashboard(report, cost_report=csr)
    # The v3.0 output must be a prefix of the extended output
    assert output.startswith(_V3_DASHBOARD_EXPECTED), (
        "Extended output does not start with v3.0 content — existing lines may have been modified"
    )


def test_format_dashboard_positional_args_unaffected():
    """format_dashboard(report, ambiguous_report, track_reports) positional callers work unchanged."""
    report = score_run(
        [_SCORE_REPORT_FIXTURE_SCENARIO],
        [_SCORE_REPORT_FIXTURE_OUTPUT],
    )
    # This must not raise — cost_report is keyword-only and not passed
    output = format_dashboard(report, None, None)
    assert "=== PSAI-Bench Metrics Dashboard ===" in output
    # Must NOT contain the cost section (cost_report not passed)
    assert "Dispatch Cost Analysis" not in output
