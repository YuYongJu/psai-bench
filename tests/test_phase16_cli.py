"""Phase 16 CLI tests: score-sequences, analyze-frame-gap, and frame_extraction unit tests."""

import json
import sys
import unittest.mock
from pathlib import Path

import pytest
from click.testing import CliRunner

from psai_bench.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temporal_scenario_file(tmp_path):
    """Generate 3 temporal sequences using TemporalSequenceGenerator and write to JSON."""
    from psai_bench.generators import TemporalSequenceGenerator

    scenarios = TemporalSequenceGenerator(seed=42).generate(3)
    out_file = tmp_path / "temporal_scenarios.json"
    with open(out_file, "w") as f:
        json.dump(scenarios, f)
    return str(out_file), scenarios


@pytest.fixture
def minimal_outputs(temporal_scenario_file, tmp_path):
    """Build minimal outputs (BENIGN, confidence=0.5) from temporal scenario list."""
    _, scenarios = temporal_scenario_file
    outputs = [
        {"alert_id": s["alert_id"], "verdict": "BENIGN", "confidence": 0.5}
        for s in scenarios
    ]
    out_file = tmp_path / "minimal_outputs.json"
    with open(out_file, "w") as f:
        json.dump(outputs, f)
    return str(out_file)


@pytest.fixture
def metadata_scenario_file(tmp_path):
    """Generate 20 metadata scenarios and write to JSON."""
    from psai_bench.generators import MetadataGenerator

    scenarios = MetadataGenerator(seed=42).generate_ucf_crime(20)
    out_file = tmp_path / "metadata_scenarios.json"
    with open(out_file, "w") as f:
        json.dump(scenarios, f)
    return str(out_file), scenarios


@pytest.fixture
def metadata_outputs(metadata_scenario_file, tmp_path):
    """Build minimal outputs for metadata scenarios."""
    _, scenarios = metadata_scenario_file
    outputs = [
        {"alert_id": s["alert_id"], "verdict": "BENIGN", "confidence": 0.5}
        for s in scenarios
    ]
    out_file = tmp_path / "metadata_outputs.json"
    with open(out_file, "w") as f:
        json.dump(outputs, f)
    return str(out_file)


class TestScoreSequencesCLI:
    """Tests for the score-sequences subcommand."""

    def test_score_sequences_table_output(self, runner, temporal_scenario_file, minimal_outputs):
        scenario_path, _ = temporal_scenario_file
        result = runner.invoke(main, [
            "score-sequences",
            "--scenarios", scenario_path,
            "--outputs", minimal_outputs,
        ])
        assert result.exit_code == 0, result.output
        assert "=== Sequence Score Report ===" in result.output

    def test_score_sequences_json_output(self, runner, temporal_scenario_file, minimal_outputs):
        scenario_path, _ = temporal_scenario_file
        result = runner.invoke(main, [
            "score-sequences",
            "--scenarios", scenario_path,
            "--outputs", minimal_outputs,
            "--format", "json",
        ])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert "n_sequences" in parsed

    def test_score_sequences_help(self, runner):
        result = runner.invoke(main, ["score-sequences", "--help"])
        assert result.exit_code == 0
        assert "--scenarios" in result.output


class TestAnalyzeFrameGapCLI:
    """Tests for the analyze-frame-gap subcommand."""

    def test_analyze_frame_gap_output(
        self, runner, metadata_scenario_file, metadata_outputs
    ):
        scenario_path, _ = metadata_scenario_file
        # Use the same metadata scenarios/outputs for both tracks — gap math doesn't
        # need real visual scenarios; we just need valid files.
        result = runner.invoke(main, [
            "analyze-frame-gap",
            "--metadata-scenarios", scenario_path,
            "--metadata-results", metadata_outputs,
            "--visual-scenarios", scenario_path,
            "--visual-results", metadata_outputs,
        ])
        assert result.exit_code == 0, result.output
        assert "=== Perception-Reasoning Gap Analysis ===" in result.output

    def test_analyze_frame_gap_shows_scores(
        self, runner, metadata_scenario_file, metadata_outputs
    ):
        scenario_path, _ = metadata_scenario_file
        result = runner.invoke(main, [
            "analyze-frame-gap",
            "--metadata-scenarios", scenario_path,
            "--metadata-results", metadata_outputs,
            "--visual-scenarios", scenario_path,
            "--visual-results", metadata_outputs,
        ])
        assert result.exit_code == 0, result.output
        assert "Metadata aggregate score" in result.output
        assert "Visual aggregate score" in result.output

    def test_analyze_frame_gap_help(self, runner):
        result = runner.invoke(main, ["analyze-frame-gap", "--help"])
        assert result.exit_code == 0


class TestFrameExtraction:
    """Tests for psai_bench.frame_extraction module."""

    def test_importable_without_cv2(self):
        """Module-level import must succeed even without cv2 installed."""
        import psai_bench.frame_extraction  # noqa: F401

    def test_raises_import_error_without_cv2(self):
        """extract_keyframes() must raise ImportError with pip install message when cv2 absent."""
        import psai_bench.frame_extraction as fe

        with unittest.mock.patch.dict(sys.modules, {"cv2": None}):
            with pytest.raises(ImportError, match="pip install"):
                fe.extract_keyframes("dummy.mp4")

    def test_raises_value_error_for_zero_interval(self):
        """extract_keyframes() must raise ValueError for keyframe_interval_sec <= 0."""
        cv2 = pytest.importorskip("cv2")  # noqa: F841 — skip if cv2 not installed
        import psai_bench.frame_extraction as fe

        with pytest.raises(ValueError, match="keyframe_interval_sec must be > 0"):
            fe.extract_keyframes("any.mp4", keyframe_interval_sec=0)

    def test_pyproject_visual_group(self):
        """pyproject.toml must have [visual] group with opencv-python-headless."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "opencv-python-headless" in content
        # Check that [visual] group or visual = [ is present near the dep
        assert 'visual = [' in content or '[visual]' in content
