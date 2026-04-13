"""Extended tests for statistics module — targeting coverage gaps.

Covers compute_all_cis, proportion_ci edge cases, and bootstrap_ci
properties that weren't tested in test_core.py.
"""

import numpy as np
import pytest

from psai_bench.statistics import (
    bootstrap_ci,
    check_run_consistency,
    compute_all_cis,
    mcnemar_test,
    proportion_ci,
)


def _make_scenario(alert_id, ground_truth):
    return {
        "alert_id": alert_id,
        "_meta": {"ground_truth": ground_truth, "difficulty": "medium"},
    }


def _make_output(alert_id, verdict, confidence=0.8):
    return {
        "alert_id": alert_id,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": "Test output for statistics test suite.",
        "processing_time_ms": 100,
    }


class TestComputeAllCIs:
    """Tests for compute_all_cis — previously 0% coverage."""

    def test_perfect_predictions_cis(self):
        scenarios = [
            _make_scenario("a1", "THREAT"),
            _make_scenario("a2", "BENIGN"),
            _make_scenario("a3", "THREAT"),
            _make_scenario("a4", "BENIGN"),
        ]
        outputs = [
            _make_output("a1", "THREAT"),
            _make_output("a2", "BENIGN"),
            _make_output("a3", "THREAT"),
            _make_output("a4", "BENIGN"),
        ]
        cis = compute_all_cis(scenarios, outputs)
        assert "accuracy" in cis
        point, lo, hi = cis["accuracy"]
        assert point == 1.0
        assert lo <= point <= hi

    def test_all_wrong_predictions_cis(self):
        scenarios = [
            _make_scenario("a1", "THREAT"),
            _make_scenario("a2", "BENIGN"),
        ]
        outputs = [
            _make_output("a1", "BENIGN"),
            _make_output("a2", "THREAT"),
        ]
        cis = compute_all_cis(scenarios, outputs)
        point, lo, hi = cis["accuracy"]
        assert point == 0.0
        assert lo <= hi

    def test_missing_outputs_count_as_wrong(self):
        scenarios = [
            _make_scenario("a1", "THREAT"),
            _make_scenario("a2", "BENIGN"),
            _make_scenario("a3", "THREAT"),
        ]
        outputs = [
            _make_output("a1", "THREAT"),
        ]
        cis = compute_all_cis(scenarios, outputs)
        point, _, _ = cis["accuracy"]
        assert point == pytest.approx(1 / 3, abs=0.01)

    def test_tdr_ci_present_when_threats_exist(self):
        scenarios = [
            _make_scenario("a1", "THREAT"),
            _make_scenario("a2", "THREAT"),
            _make_scenario("a3", "BENIGN"),
        ]
        outputs = [
            _make_output("a1", "THREAT"),
            _make_output("a2", "SUSPICIOUS"),
            _make_output("a3", "BENIGN"),
        ]
        cis = compute_all_cis(scenarios, outputs)
        assert "tdr" in cis
        point, lo, hi = cis["tdr"]
        assert point == 1.0  # Both threats detected (THREAT + SUSPICIOUS count)
        assert lo <= point <= hi

    def test_fasr_ci_present_when_benign_exist(self):
        scenarios = [
            _make_scenario("a1", "BENIGN"),
            _make_scenario("a2", "BENIGN"),
            _make_scenario("a3", "THREAT"),
        ]
        outputs = [
            _make_output("a1", "BENIGN"),
            _make_output("a2", "THREAT"),  # False alarm
            _make_output("a3", "THREAT"),
        ]
        cis = compute_all_cis(scenarios, outputs)
        assert "fasr" in cis
        point, lo, hi = cis["fasr"]
        assert point == 0.5  # 1 of 2 benign correctly suppressed


class TestProportionCIEdgeCases:
    """Edge cases for Wilson score interval."""

    def test_zero_total(self):
        lo, hi = proportion_ci(0, 0)
        assert lo == 0.0
        assert hi == 0.0

    def test_all_successes(self):
        lo, hi = proportion_ci(100, 100)
        assert lo > 0.95
        assert hi == 1.0

    def test_no_successes(self):
        lo, hi = proportion_ci(0, 100)
        assert lo < 1e-10  # effectively zero (floating point)
        assert hi < 0.05

    def test_small_sample(self):
        lo, hi = proportion_ci(1, 2)
        assert 0.0 < lo < 0.5
        assert 0.5 < hi < 1.0

    def test_different_confidence(self):
        lo_95, hi_95 = proportion_ci(50, 100, confidence=0.95)
        lo_99, hi_99 = proportion_ci(50, 100, confidence=0.99)
        # 99% CI should be wider
        assert (hi_99 - lo_99) > (hi_95 - lo_95)


class TestBootstrapCIProperties:
    """Property tests for bootstrap CI."""

    def test_empty_values(self):
        lo, hi = bootstrap_ci(np.array([]))
        assert lo == 0.0
        assert hi == 0.0

    def test_constant_values(self):
        values = np.array([0.5] * 100)
        lo, hi = bootstrap_ci(values)
        assert lo == pytest.approx(0.5, abs=0.001)
        assert hi == pytest.approx(0.5, abs=0.001)

    def test_ci_contains_mean(self):
        rng = np.random.RandomState(42)
        values = rng.normal(0.7, 0.1, size=200)
        lo, hi = bootstrap_ci(values)
        assert lo < np.mean(values) < hi

    def test_wider_ci_for_more_variance(self):
        rng = np.random.RandomState(42)
        narrow = bootstrap_ci(rng.normal(0.5, 0.01, size=100))
        wide = bootstrap_ci(rng.normal(0.5, 0.2, size=100))
        assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])


class TestRunConsistencyExtended:
    """Extended tests for check_run_consistency."""

    def test_empty_reports(self):
        result = check_run_consistency([])
        assert result["consistent"] is False
        assert result["reason"] == "no runs"

    def test_single_run(self):
        result = check_run_consistency([{"accuracy": 0.8}])
        assert result["is_deterministic"] == True  # noqa: E712 — numpy bool
        assert result["n_runs"] == 1

    def test_custom_metric(self):
        reports = [{"tdr": 0.9}, {"tdr": 0.91}, {"tdr": 0.89}]
        result = check_run_consistency(reports, metric="tdr")
        assert result["metric"] == "tdr"
        assert result["n_runs"] == 3

    def test_high_variance_flagged(self):
        reports = [{"accuracy": 0.3}, {"accuracy": 0.9}]
        result = check_run_consistency(reports, max_cv=0.05)
        assert result["is_consistent"] == False  # noqa: E712 — numpy bool

    def test_custom_max_cv(self):
        reports = [{"accuracy": 0.8}, {"accuracy": 0.82}]
        strict = check_run_consistency(reports, max_cv=0.001)
        relaxed = check_run_consistency(reports, max_cv=0.5)
        assert not strict["is_consistent"] or relaxed["is_consistent"]
