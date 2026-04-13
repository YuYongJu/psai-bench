"""Tests for compute_site_generalization_gap() in psai_bench.scorer.

Tests cover all 5 behaviors specified in the plan:
1. Two site types: per_site_accuracy keys match both sites, gap == max - min
2. Single site type: one key, gap == 0.0
3. Empty scenarios: returns empty per_site_accuracy, gap 0.0, train/test None
4. train_site/test_site args: adds train_accuracy and test_accuracy keys
5. score_run is NOT called (function computes accuracy directly)
"""

import pytest

from psai_bench.scorer import compute_site_generalization_gap


def _make_scenario(alert_id: str, site_type: str, ground_truth: str) -> dict:
    """Minimal scenario dict with just the fields we need."""
    return {
        "alert_id": alert_id,
        "context": {"site_type": site_type},
        "_meta": {
            "ground_truth": ground_truth,
            "difficulty": "medium",
            "source_dataset": "test",
            "ambiguity_flag": False,
        },
    }


def _make_output(alert_id: str, verdict: str) -> dict:
    return {"alert_id": alert_id, "verdict": verdict, "confidence": 0.9}


# ---------------------------------------------------------------------------
# Behavior 1: Two site types — per_site_accuracy keys match both, gap correct
# ---------------------------------------------------------------------------

class TestTwoSiteTypes:
    def test_keys_match_both_site_types(self):
        scenarios = [
            _make_scenario("a1", "solar", "THREAT"),
            _make_scenario("a2", "solar", "BENIGN"),
            _make_scenario("a3", "commercial", "THREAT"),
            _make_scenario("a4", "commercial", "BENIGN"),
        ]
        outputs = [
            _make_output("a1", "THREAT"),   # correct
            _make_output("a2", "BENIGN"),   # correct
            _make_output("a3", "BENIGN"),   # wrong
            _make_output("a4", "BENIGN"),   # correct
        ]
        result = compute_site_generalization_gap(scenarios, outputs)
        assert set(result["per_site_accuracy"].keys()) == {"solar", "commercial"}

    def test_gap_equals_max_minus_min(self):
        scenarios = [
            _make_scenario("a1", "solar", "THREAT"),
            _make_scenario("a2", "solar", "BENIGN"),
            _make_scenario("a3", "commercial", "THREAT"),
            _make_scenario("a4", "commercial", "BENIGN"),
        ]
        outputs = [
            _make_output("a1", "THREAT"),   # solar correct: 1
            _make_output("a2", "BENIGN"),   # solar correct: 2 → solar acc = 1.0
            _make_output("a3", "BENIGN"),   # commercial wrong: 0
            _make_output("a4", "BENIGN"),   # commercial correct: 1 → commercial acc = 0.5
        ]
        result = compute_site_generalization_gap(scenarios, outputs)
        accs = result["per_site_accuracy"]
        expected_gap = max(accs.values()) - min(accs.values())
        assert abs(result["generalization_gap"] - expected_gap) < 1e-9
        assert abs(accs["solar"] - 1.0) < 1e-9
        assert abs(accs["commercial"] - 0.5) < 1e-9
        assert abs(result["generalization_gap"] - 0.5) < 1e-9

    def test_returns_required_top_level_keys(self):
        scenarios = [_make_scenario("a1", "solar", "THREAT")]
        outputs = [_make_output("a1", "THREAT")]
        result = compute_site_generalization_gap(scenarios, outputs)
        for key in ("per_site_accuracy", "generalization_gap", "train_site", "test_site"):
            assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Behavior 2: Single site type — one key, gap == 0.0
# ---------------------------------------------------------------------------

class TestSingleSiteType:
    def test_single_site_one_key(self):
        scenarios = [
            _make_scenario("b1", "solar", "THREAT"),
            _make_scenario("b2", "solar", "BENIGN"),
        ]
        outputs = [
            _make_output("b1", "THREAT"),
            _make_output("b2", "BENIGN"),
        ]
        result = compute_site_generalization_gap(scenarios, outputs)
        assert list(result["per_site_accuracy"].keys()) == ["solar"]

    def test_single_site_gap_is_zero(self):
        scenarios = [
            _make_scenario("b1", "solar", "THREAT"),
            _make_scenario("b2", "solar", "BENIGN"),
        ]
        outputs = [
            _make_output("b1", "THREAT"),
            _make_output("b2", "BENIGN"),
        ]
        result = compute_site_generalization_gap(scenarios, outputs)
        assert result["generalization_gap"] == 0.0


# ---------------------------------------------------------------------------
# Behavior 3: Empty scenarios list
# ---------------------------------------------------------------------------

class TestEmptyScenarios:
    def test_empty_returns_correct_structure(self):
        result = compute_site_generalization_gap([], [])
        assert result["per_site_accuracy"] == {}
        assert result["generalization_gap"] == 0.0
        assert result["train_site"] is None
        assert result["test_site"] is None

    def test_empty_no_train_accuracy_key_when_no_sites(self):
        result = compute_site_generalization_gap([], [], train_site="solar", test_site="commercial")
        # No scenarios → no accuracy values — but keys should exist with None
        assert result.get("train_accuracy") is None
        assert result.get("test_accuracy") is None


# ---------------------------------------------------------------------------
# Behavior 4: train_site / test_site args add train_accuracy / test_accuracy
# ---------------------------------------------------------------------------

class TestTrainTestSiteArgs:
    def setup_method(self):
        self.scenarios = [
            _make_scenario("c1", "solar", "THREAT"),
            _make_scenario("c2", "solar", "BENIGN"),
            _make_scenario("c3", "commercial", "THREAT"),
            _make_scenario("c4", "commercial", "BENIGN"),
        ]
        self.outputs = [
            _make_output("c1", "THREAT"),   # solar correct
            _make_output("c2", "BENIGN"),   # solar correct → solar acc = 1.0
            _make_output("c3", "BENIGN"),   # commercial wrong
            _make_output("c4", "BENIGN"),   # commercial correct → commercial acc = 0.5
        ]

    def test_train_accuracy_present(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="commercial"
        )
        assert "train_accuracy" in result

    def test_test_accuracy_present(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="commercial"
        )
        assert "test_accuracy" in result

    def test_train_accuracy_matches_per_site(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="commercial"
        )
        assert abs(result["train_accuracy"] - result["per_site_accuracy"]["solar"]) < 1e-9

    def test_test_accuracy_matches_per_site(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="commercial"
        )
        assert abs(result["test_accuracy"] - result["per_site_accuracy"]["commercial"]) < 1e-9

    def test_train_site_recorded_in_result(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="commercial"
        )
        assert result["train_site"] == "solar"
        assert result["test_site"] == "commercial"

    def test_unknown_train_site_returns_none(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="campus", test_site="commercial"
        )
        assert result["train_accuracy"] is None

    def test_unknown_test_site_returns_none(self):
        result = compute_site_generalization_gap(
            self.scenarios, self.outputs, train_site="solar", test_site="industrial"
        )
        assert result["test_accuracy"] is None

    def test_no_train_test_keys_when_args_none(self):
        result = compute_site_generalization_gap(self.scenarios, self.outputs)
        # When not passing train/test, keys should not appear or be None
        # (either absence or None is acceptable — we check None is consistent with test_site=None)
        assert result["train_site"] is None
        assert result["test_site"] is None


# ---------------------------------------------------------------------------
# Behavior 5: score_run is NOT called — direct accuracy computation
# ---------------------------------------------------------------------------

class TestDoesNotCallScoreRun:
    def test_missing_output_counts_as_incorrect(self):
        """Scenarios with no matching output must count as incorrect (same policy as _score_partition)."""
        scenarios = [
            _make_scenario("d1", "solar", "THREAT"),
            _make_scenario("d2", "solar", "BENIGN"),
        ]
        # Only provide output for d1, d2 has no output → d2 counts as incorrect
        outputs = [_make_output("d1", "THREAT")]
        result = compute_site_generalization_gap(scenarios, outputs)
        # d1 correct (1), d2 missing → incorrect (0) → solar acc = 0.5
        assert abs(result["per_site_accuracy"]["solar"] - 0.5) < 1e-9

    def test_function_importable_without_mocking_score_run(self):
        """Importing and calling compute_site_generalization_gap must work in isolation."""
        from psai_bench.scorer import compute_site_generalization_gap as fn
        assert callable(fn)

    def test_accuracy_computed_independently_of_score_run(self, monkeypatch):
        """Patch score_run to raise — compute_site_generalization_gap must still work."""
        import psai_bench.scorer as scorer_module

        def _fail(*args, **kwargs):
            raise AssertionError("score_run must not be called by compute_site_generalization_gap")

        monkeypatch.setattr(scorer_module, "score_run", _fail)

        scenarios = [_make_scenario("e1", "solar", "THREAT")]
        outputs = [_make_output("e1", "THREAT")]
        # Must not raise
        result = scorer_module.compute_site_generalization_gap(scenarios, outputs)
        assert result["per_site_accuracy"]["solar"] == 1.0
