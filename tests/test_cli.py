"""CLI integration tests for psai-bench commands.

Tests that CLI commands execute correctly with valid arguments.
Does NOT test API evaluators (requires network + API keys).
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from psai_bench.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def generated_scenarios(tmp_path):
    """Generate a small set of scenarios for CLI testing."""
    from psai_bench.generators import MetadataGenerator

    gen = MetadataGenerator(seed=42)
    scenarios = gen.generate_ucf_crime(50)
    out_file = tmp_path / "test_scenarios.json"
    with open(out_file, "w") as f:
        json.dump(scenarios, f)
    return str(out_file), scenarios


class TestCLIHelp:
    """Test that all CLI commands have working --help."""

    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "PSAI-Bench" in result.output

    def test_generate_help(self, runner):
        result = runner.invoke(main, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--track" in result.output

    def test_score_help(self, runner):
        result = runner.invoke(main, ["score", "--help"])
        assert result.exit_code == 0
        assert "--scenarios" in result.output

    def test_baselines_help(self, runner):
        result = runner.invoke(main, ["baselines", "--help"])
        assert result.exit_code == 0

    def test_compare_help(self, runner):
        result = runner.invoke(main, ["compare", "--help"])
        assert result.exit_code == 0
        assert "--outputs-a" in result.output

    def test_validate_scenarios_help(self, runner):
        result = runner.invoke(main, ["validate-scenarios", "--help"])
        assert result.exit_code == 0

    def test_validate_submission_help(self, runner):
        result = runner.invoke(main, ["validate-submission", "--help"])
        assert result.exit_code == 0


class TestCLIGenerate:
    """Test the generate command."""

    def test_generate_metadata_ucf(self, runner, tmp_path):
        result = runner.invoke(main, [
            "generate",
            "--track", "metadata",
            "--source", "ucf",
            "--n", "10",
            "--seed", "42",
            "--output", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Generated 10 UCF Crime metadata scenarios" in result.output
        out_file = tmp_path / "metadata_ucf_seed42.json"
        assert out_file.exists()
        with open(out_file) as f:
            data = json.load(f)
        assert len(data) == 10

    def test_generate_metadata_caltech(self, runner, tmp_path):
        result = runner.invoke(main, [
            "generate",
            "--track", "metadata",
            "--source", "caltech",
            "--n", "10",
            "--seed", "42",
            "--output", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Generated 10 Caltech metadata scenarios" in result.output

    def test_generate_multi_sensor(self, runner, tmp_path):
        result = runner.invoke(main, [
            "generate",
            "--track", "multi_sensor",
            "--n", "5",
            "--seed", "42",
            "--output", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "Generated 5 multi-sensor scenarios" in result.output


class TestCLIScore:
    """Test the score command."""

    def test_score_table_format(self, runner, generated_scenarios):
        scenarios_file, scenarios = generated_scenarios
        # Create outputs matching the scenarios
        outputs = []
        for s in scenarios:
            outputs.append({
                "alert_id": s["alert_id"],
                "verdict": s["_meta"]["ground_truth"],
                "confidence": 0.9,
                "reasoning": "Test perfect prediction for CLI scoring test.",
                "processing_time_ms": 100,
            })
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(outputs, f)
            outputs_file = f.name

        result = runner.invoke(main, [
            "score",
            "--scenarios", scenarios_file,
            "--outputs", outputs_file,
        ])
        assert result.exit_code == 0
        assert "Primary Metrics" in result.output
        assert "Threat Detection Rate" in result.output

    def test_score_json_format(self, runner, generated_scenarios):
        scenarios_file, scenarios = generated_scenarios
        outputs = [{
            "alert_id": s["alert_id"],
            "verdict": s["_meta"]["ground_truth"],
            "confidence": 0.9,
            "reasoning": "Perfect prediction for JSON format test.",
            "processing_time_ms": 100,
        } for s in scenarios]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(outputs, f)
            outputs_file = f.name

        result = runner.invoke(main, [
            "score",
            "--scenarios", scenarios_file,
            "--outputs", outputs_file,
            "--format", "json",
        ])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "tdr" in parsed
        assert "accuracy" in parsed


class TestCLIBaselines:
    """Test the baselines command."""

    def test_baselines_runs(self, runner, generated_scenarios, tmp_path):
        scenarios_file, _ = generated_scenarios
        result = runner.invoke(main, [
            "baselines",
            "--scenarios", scenarios_file,
            "--output", str(tmp_path / "baselines"),
        ])
        assert result.exit_code == 0
        assert "RANDOM BASELINE" in result.output
        assert "MAJORITY_CLASS BASELINE" in result.output
        assert (tmp_path / "baselines" / "baseline_summary.json").exists()


class TestCLIValidation:
    """Test validation commands."""

    def test_validate_scenarios(self, runner, generated_scenarios):
        scenarios_file, _ = generated_scenarios
        result = runner.invoke(main, [
            "validate-scenarios",
            "--scenarios", scenarios_file,
        ])
        assert result.exit_code == 0

    def test_validate_submission(self, runner, generated_scenarios):
        scenarios_file, scenarios = generated_scenarios
        outputs = [{
            "alert_id": s["alert_id"],
            "verdict": "BENIGN",
            "confidence": 0.5,
            "reasoning": "Test submission for validation test.",
            "processing_time_ms": 100,
        } for s in scenarios]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(outputs, f)
            outputs_file = f.name

        result = runner.invoke(main, [
            "validate-submission",
            "--scenarios", scenarios_file,
            "--outputs", outputs_file,
        ])
        assert result.exit_code == 0


class TestCLICompare:
    """Test the compare command."""

    def test_compare_two_systems(self, runner, generated_scenarios):
        scenarios_file, scenarios = generated_scenarios
        # System A: perfect
        outputs_a = [{
            "alert_id": s["alert_id"],
            "verdict": s["_meta"]["ground_truth"],
            "confidence": 0.9,
            "reasoning": "Perfect system A for comparison test.",
            "processing_time_ms": 100,
        } for s in scenarios]
        # System B: always BENIGN
        outputs_b = [{
            "alert_id": s["alert_id"],
            "verdict": "BENIGN",
            "confidence": 0.5,
            "reasoning": "Always benign system B for comparison test.",
            "processing_time_ms": 100,
        } for s in scenarios]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fa:
            json.dump(outputs_a, fa)
            file_a = fa.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fb:
            json.dump(outputs_b, fb)
            file_b = fb.name

        result = runner.invoke(main, [
            "compare",
            "--scenarios", scenarios_file,
            "--outputs-a", file_a,
            "--outputs-b", file_b,
        ])
        assert result.exit_code == 0
        assert "McNemar" in result.output
        assert "System A" in result.output


class TestCLIAnalyzeSuspicious:
    """Test the suspicious cap analysis command."""

    def test_analyze_suspicious_cap(self, runner, generated_scenarios, tmp_path):
        scenarios_file, _ = generated_scenarios
        out_file = str(tmp_path / "suspicious_analysis.json")
        result = runner.invoke(main, [
            "analyze-suspicious-cap",
            "--scenarios", scenarios_file,
            "--output", out_file,
        ])
        assert result.exit_code == 0
        assert Path(out_file).exists()
        with open(out_file) as f:
            data = json.load(f)
        assert len(data) > 0
        assert "target_suspicious_rate" in data[0]
