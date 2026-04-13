"""Integration and backward-compatibility tests for PSAI-Bench v4.0.

Tests five groups:
  Group 1: E2E pipeline (generate → baseline → score_dispatch_run)
  Group 2: Adversarial v4 behavioral pattern presence in pipeline
  Group 3: Backward compat — score_run unchanged on v1 output
  Group 4: Backward compat — score_dispatch_run graceful on v1 output
  Group 5: CLI --site-type filter seed reproducibility
"""

import json
import math

import pytest
from click.testing import CliRunner

from psai_bench.baselines import random_baseline
from psai_bench.cli import main
from psai_bench.cost_model import DISPATCH_ACTIONS, CostScoreReport
from psai_bench.generators import AdversarialV4Generator, MetadataGenerator
from psai_bench.scorer import ScoreReport, score_dispatch_run, score_run


# ---------------------------------------------------------------------------
# Group 1: TestE2EPipeline
# ---------------------------------------------------------------------------


class TestE2EPipeline:
    """E2E pipeline: generate → random_baseline → score_dispatch_run."""

    def test_e2e_generate_to_score_dispatch(self):
        scenarios = AdversarialV4Generator(seed=42).generate(50)
        outputs = random_baseline(scenarios, seed=42)
        result = score_dispatch_run(scenarios, outputs)

        assert isinstance(result, CostScoreReport)
        assert result.n_scenarios >= 0
        assert result.cost_ratio >= 0
        assert set(result.per_action_counts.keys()) == set(DISPATCH_ACTIONS)
        assert result.n_scenarios + result.n_missing_dispatch == 50

    def test_e2e_cost_ratio_is_finite(self):
        scenarios = AdversarialV4Generator(seed=42).generate(50)
        outputs = random_baseline(scenarios, seed=42)
        result = score_dispatch_run(scenarios, outputs)

        assert math.isfinite(result.cost_ratio)


# ---------------------------------------------------------------------------
# Group 2: TestE2EAdversarialV4Presence
# ---------------------------------------------------------------------------


class TestE2EAdversarialV4Presence:
    """Adversarial v4 behavioral pattern verification within the E2E pipeline."""

    def test_adversarial_v4_types_in_pipeline(self):
        scenarios = AdversarialV4Generator(seed=42).generate(50)
        adversarial_types = {s["_meta"]["adversarial_type"] for s in scenarios}
        assert len(adversarial_types) == 3, (
            f"Expected all 3 adversarial types, got: {adversarial_types}"
        )

    def test_adversarial_v4_optimal_dispatch_present(self):
        scenarios = AdversarialV4Generator(seed=42).generate(10)
        outputs = random_baseline(scenarios, seed=42)
        result = score_dispatch_run(scenarios, outputs)

        assert result.per_action_counts, "per_action_counts must not be empty"


# ---------------------------------------------------------------------------
# Group 3: TestBackwardCompatScoreRun
# ---------------------------------------------------------------------------


class TestBackwardCompatScoreRun:
    """score_run() returns correct metrics on v1-era outputs (no dispatch field)."""

    def _make_v1_scenarios_and_outputs(self, n: int = 10):
        """Return (scenarios, outputs) where outputs match ground truth perfectly (v1 shape)."""
        scenarios = MetadataGenerator(seed=42).generate_ucf_crime(n)
        outputs = []
        for s in scenarios:
            gt = s["_meta"]["ground_truth"]
            outputs.append({
                "alert_id": s["alert_id"],
                "verdict": gt,
                "confidence": 0.95,
                "processing_time_ms": 1,
            })
        return scenarios, outputs

    def test_v1_score_run_key_metrics_unchanged(self):
        scenarios, outputs = self._make_v1_scenarios_and_outputs(10)

        # Verify v1 shape — no dispatch key in output
        assert "dispatch" not in outputs[0]

        report = score_run(scenarios, outputs)

        # Perfect predictions: TDR, FASR, accuracy all == 1.0
        # (score_run partitions on ambiguity_flag; v1 scenarios have none)
        assert report.tdr == pytest.approx(1.0), f"tdr={report.tdr}"
        assert report.fasr == pytest.approx(1.0), f"fasr={report.fasr}"
        assert report.accuracy == pytest.approx(1.0), f"accuracy={report.accuracy}"

    def test_v1_output_score_run_returns_score_report(self):
        scenarios, outputs = self._make_v1_scenarios_and_outputs(10)
        report = score_run(scenarios, outputs)
        assert isinstance(report, ScoreReport)


# ---------------------------------------------------------------------------
# Group 4: TestBackwardCompatDispatchRun
# ---------------------------------------------------------------------------


class TestBackwardCompatDispatchRun:
    """score_dispatch_run() handles v1 outputs (no dispatch field) gracefully."""

    def _make_v1_scenarios_and_outputs(self, n: int = 5):
        scenarios = MetadataGenerator(seed=42).generate_ucf_crime(n)
        outputs = []
        for s in scenarios:
            gt = s["_meta"]["ground_truth"]
            outputs.append({
                "alert_id": s["alert_id"],
                "verdict": gt,
                "confidence": 0.90,
                "processing_time_ms": 1,
                # No 'dispatch' field — v1 shape
            })
        return scenarios, outputs

    def test_v1_output_score_dispatch_run_no_raise(self):
        scenarios, outputs = self._make_v1_scenarios_and_outputs(5)

        # Must not raise
        result = score_dispatch_run(scenarios, outputs)

        assert result.n_missing_dispatch == 5, (
            f"Expected n_missing_dispatch=5 (all missing), got {result.n_missing_dispatch}"
        )
        assert result.n_scenarios == 0, (
            f"Expected n_scenarios=0 (no scorable dispatch), got {result.n_scenarios}"
        )

    def test_v1_output_score_dispatch_run_returns_cost_score_report(self):
        scenarios, outputs = self._make_v1_scenarios_and_outputs(5)
        result = score_dispatch_run(scenarios, outputs)
        assert isinstance(result, CostScoreReport)


# ---------------------------------------------------------------------------
# Group 5: TestCLISiteTypeFilter
# ---------------------------------------------------------------------------


class TestCLISiteTypeFilter:
    """CLI --site-type filter: subset + deterministic across runs."""

    def test_site_type_filter_is_subset_of_full_generation(self, tmp_path):
        runner = CliRunner()

        # Filtered run: only solar sites
        filtered_out = tmp_path / "filtered"
        filtered_out.mkdir()
        result_filtered = runner.invoke(main, [
            "generate",
            "--track", "metadata",
            "--source", "ucf",
            "--n", "100",
            "--seed", "42",
            "--site-type", "solar",
            "--output", str(filtered_out),
        ])
        assert result_filtered.exit_code == 0, (
            f"Filtered generate failed:\n{result_filtered.output}"
        )

        filtered_file = filtered_out / "metadata_ucf_seed42.json"
        with open(filtered_file) as f:
            filtered_scenarios = json.load(f)

        # All retained scenarios must be solar
        for s in filtered_scenarios:
            assert s["context"]["site_type"] == "solar", (
                f"Non-solar scenario leaked through: {s['context']['site_type']}"
            )

        # Full run: no site-type filter
        full_out = tmp_path / "full"
        full_out.mkdir()
        result_full = runner.invoke(main, [
            "generate",
            "--track", "metadata",
            "--source", "ucf",
            "--n", "100",
            "--seed", "42",
            "--output", str(full_out),
        ])
        assert result_full.exit_code == 0, (
            f"Full generate failed:\n{result_full.output}"
        )

        full_file = full_out / "metadata_ucf_seed42.json"
        with open(full_file) as f:
            full_scenarios = json.load(f)

        full_ids = {s["alert_id"] for s in full_scenarios}
        filtered_ids = {s["alert_id"] for s in filtered_scenarios}

        assert filtered_ids.issubset(full_ids), (
            "Filtered alert_ids are not a subset of full generation alert_ids"
        )

    def test_site_type_filter_seed_deterministic(self, tmp_path):
        runner = CliRunner()

        common_args = [
            "generate",
            "--track", "metadata",
            "--source", "ucf",
            "--n", "100",
            "--seed", "42",
            "--site-type", "commercial",
        ]

        # First run
        out1 = tmp_path / "run1"
        out1.mkdir()
        r1 = runner.invoke(main, common_args + ["--output", str(out1)])
        assert r1.exit_code == 0, f"Run1 failed:\n{r1.output}"

        # Second run
        out2 = tmp_path / "run2"
        out2.mkdir()
        r2 = runner.invoke(main, common_args + ["--output", str(out2)])
        assert r2.exit_code == 0, f"Run2 failed:\n{r2.output}"

        file1 = out1 / "metadata_ucf_seed42.json"
        file2 = out2 / "metadata_ucf_seed42.json"

        with open(file1) as f:
            scenarios1 = json.load(f)
        with open(file2) as f:
            scenarios2 = json.load(f)

        ids1 = [s["alert_id"] for s in scenarios1]
        ids2 = [s["alert_id"] for s in scenarios2]

        assert ids1 == ids2, (
            "Two runs with the same seed and --site-type commercial produced different alert_ids"
        )
