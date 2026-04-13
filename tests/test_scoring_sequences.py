"""Tests for temporal sequence scoring (score_sequences).

Covers early/late/missed detection rates, false escalation rate,
mixed-file behavior, and empty input edge cases.
"""

import pytest

from psai_bench.scorer import SequenceScoreReport, score_sequences


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_seq_scenario(
    seq_id: str,
    position: int,
    seq_length: int,
    ground_truth: str,
    pattern: str = "monotonic_escalation",
    alert_id: str | None = None,
) -> dict:
    """Minimal valid sequence scenario with _meta.sequence_id populated."""
    if alert_id is None:
        alert_id = f"{seq_id}-pos{position}"
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
            "expected_activities": [],
            "site_type": "solar",
        },
        "visual_data": None,
        "additional_sensors": [],
        "_meta": {
            "ground_truth": ground_truth,
            "difficulty": "medium",
            "source_dataset": "ucf_crime",
            "source_category": "Normal",
            "seed": 42,
            "index": 0,
            "sequence_id": seq_id,
            "sequence_position": position,
            "sequence_length": seq_length,
            "escalation_pattern": pattern,
        },
    }


def _make_seq_output(alert_id: str, verdict: str, confidence: float = 0.85) -> dict:
    """Minimal valid output dict for sequence tests."""
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


# ---------------------------------------------------------------------------
# 4-alert threat sequence fixture used across multiple tests
#
# GT layout: pos1=BENIGN, pos2=SUSPICIOUS, pos3=THREAT, pos4=THREAT
# Alert IDs: seq-a-pos1, seq-a-pos2, seq-a-pos3, seq-a-pos4
# ---------------------------------------------------------------------------

def _make_4alert_threat_seq(seq_id: str = "seq-a") -> list[dict]:
    return [
        _make_seq_scenario(seq_id, 1, 4, "BENIGN"),
        _make_seq_scenario(seq_id, 2, 4, "SUSPICIOUS"),
        _make_seq_scenario(seq_id, 3, 4, "THREAT"),
        _make_seq_scenario(seq_id, 4, 4, "THREAT"),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSequenceScoring:

    def test_threat_seq_early_detection(self):
        """Model escalates to THREAT at position 1 (index 0) — early detection."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "THREAT"),     # early: index 0
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "BENIGN"),
            _make_seq_output("seq-a-pos4", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.n_sequences == 1
        assert report.n_threat_sequences == 1
        assert report.n_benign_sequences == 0
        assert report.early_detection_rate == 1.0
        assert report.missed_sequence_rate == 0.0
        assert report.late_detection_rate == 0.0
        assert report.false_escalation_rate == 0.0

    def test_threat_seq_early_detection_second_alert(self):
        """Model escalates to THREAT at position 2 (index 1) — still early."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "THREAT"),     # early: index 1
            _make_seq_output("seq-a-pos3", "BENIGN"),
            _make_seq_output("seq-a-pos4", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.early_detection_rate == 1.0
        assert report.missed_sequence_rate == 0.0

    def test_threat_seq_middle_detection(self):
        """Model outputs THREAT at position 3 (index 2, not first two, not last)."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "THREAT"),     # middle: index 2
            _make_seq_output("seq-a-pos4", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.early_detection_rate == 0.0
        assert report.late_detection_rate == 0.0
        assert report.missed_sequence_rate == 0.0
        assert report.n_threat_sequences == 1

    def test_threat_seq_late_detection(self):
        """Model outputs THREAT only at the last alert (index 3 of 4) — late detection."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "BENIGN"),
            _make_seq_output("seq-a-pos4", "THREAT"),     # late: last index
        ]
        report = score_sequences(scenarios, outputs)

        assert report.late_detection_rate == 1.0
        assert report.early_detection_rate == 0.0
        assert report.missed_sequence_rate == 0.0

    def test_threat_seq_missed(self):
        """Model never outputs THREAT on any alert — missed sequence."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "BENIGN"),
            _make_seq_output("seq-a-pos4", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.missed_sequence_rate == 1.0
        assert report.early_detection_rate == 0.0
        assert report.late_detection_rate == 0.0
        assert report.false_escalation_rate == 0.0

    def test_benign_seq_no_false_escalation(self):
        """All-BENIGN sequence, model returns BENIGN — no false escalation."""
        scenarios = [
            _make_seq_scenario("seq-b", 1, 3, "BENIGN"),
            _make_seq_scenario("seq-b", 2, 3, "BENIGN"),
            _make_seq_scenario("seq-b", 3, 3, "BENIGN"),
        ]
        outputs = [
            _make_seq_output("seq-b-pos1", "BENIGN"),
            _make_seq_output("seq-b-pos2", "BENIGN"),
            _make_seq_output("seq-b-pos3", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.n_benign_sequences == 1
        assert report.n_threat_sequences == 0
        assert report.false_escalation_rate == 0.0

    def test_benign_seq_false_escalation(self):
        """All-BENIGN sequence, model returns THREAT on one alert — false escalation."""
        scenarios = [
            _make_seq_scenario("seq-b", 1, 3, "BENIGN"),
            _make_seq_scenario("seq-b", 2, 3, "BENIGN"),
            _make_seq_scenario("seq-b", 3, 3, "BENIGN"),
        ]
        outputs = [
            _make_seq_output("seq-b-pos1", "BENIGN"),
            _make_seq_output("seq-b-pos2", "THREAT"),   # false escalation
            _make_seq_output("seq-b-pos3", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.n_benign_sequences == 1
        assert report.false_escalation_rate == 1.0
        assert report.missed_sequence_rate == 0.0
        assert report.early_detection_rate == 0.0

    def test_suspicious_only_seq_is_benign_class(self):
        """Sequence with all SUSPICIOUS GT is classified as benign (no THREAT GT)."""
        scenarios = [
            _make_seq_scenario("seq-c", 1, 3, "SUSPICIOUS"),
            _make_seq_scenario("seq-c", 2, 3, "SUSPICIOUS"),
            _make_seq_scenario("seq-c", 3, 3, "SUSPICIOUS"),
        ]
        outputs = [
            _make_seq_output("seq-c-pos1", "THREAT"),   # false escalation on suspicious seq
            _make_seq_output("seq-c-pos2", "BENIGN"),
            _make_seq_output("seq-c-pos3", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert report.n_benign_sequences == 1
        assert report.n_threat_sequences == 0
        assert report.false_escalation_rate == 1.0

    def test_mixed_file_skips_non_sequence(self):
        """Non-sequence scenarios (no sequence_id in _meta) are silently skipped."""
        # Sequence scenario
        seq_scenarios = _make_4alert_threat_seq()
        # Non-sequence scenarios (no sequence_id)
        non_seq = [
            {
                "alert_id": "standalone-1",
                "timestamp": "2026-01-15T14:30:00+00:00",
                "track": "metadata",
                "severity": "LOW",
                "description": "Standalone alert with no sequence",
                "source_type": "camera",
                "zone": {"id": "zone-1", "name": "Zone", "type": "perimeter",
                         "sensitivity": 3, "operating_hours": "24/7"},
                "device": {"id": "cam-1", "false_positive_rate": 0.3,
                           "total_events_30d": 100, "model": "test"},
                "context": {"recent_zone_events_1h": [], "weather": {},
                            "time_of_day": "day", "expected_activities": [], "site_type": "solar"},
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": "THREAT",
                    "difficulty": "medium",
                    "source_dataset": "ucf_crime",
                    "source_category": "Normal",
                    "seed": 42,
                    "index": 99,
                    # No sequence_id key at all
                },
            }
        ]
        all_scenarios = seq_scenarios + non_seq
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "THREAT"),
            _make_seq_output("seq-a-pos4", "BENIGN"),
            _make_seq_output("standalone-1", "THREAT"),
        ]
        report = score_sequences(all_scenarios, outputs)

        # Only the 1 sequence counts — standalone is skipped
        assert report.n_sequences == 1
        assert report.n_threat_sequences == 1

    def test_empty_scenarios_returns_zero_report(self):
        """score_sequences([], []) returns zero-valued SequenceScoreReport."""
        report = score_sequences([], [])

        assert isinstance(report, SequenceScoreReport)
        assert report.n_sequences == 0
        assert report.n_threat_sequences == 0
        assert report.n_benign_sequences == 0
        assert report.early_detection_rate == 0.0
        assert report.late_detection_rate == 0.0
        assert report.missed_sequence_rate == 0.0
        assert report.false_escalation_rate == 0.0

    def test_score_run_not_called(self):
        """score_sequences must not call score_run internally."""
        import inspect
        import ast
        from psai_bench import scorer

        source = inspect.getsource(scorer.score_sequences)
        tree = ast.parse(source)
        # Walk AST looking for any Call node whose func is named score_run
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "score_run"
        ]
        assert not calls, (
            "score_sequences must not call score_run() — found call in AST"
        )

    def test_multiple_sequences_aggregates_correctly(self):
        """Two threat sequences: one early, one missed. Rates should average."""
        # Sequence 1: early detection (model hits THREAT at index 0)
        seq1 = [
            _make_seq_scenario("seq-x", 1, 3, "BENIGN"),
            _make_seq_scenario("seq-x", 2, 3, "THREAT"),
            _make_seq_scenario("seq-x", 3, 3, "THREAT"),
        ]
        # Sequence 2: missed (model never outputs THREAT)
        seq2 = [
            _make_seq_scenario("seq-y", 1, 3, "BENIGN"),
            _make_seq_scenario("seq-y", 2, 3, "THREAT"),
            _make_seq_scenario("seq-y", 3, 3, "THREAT"),
        ]
        all_scenarios = seq1 + seq2
        outputs = [
            _make_seq_output("seq-x-pos1", "THREAT"),   # early hit at index 0
            _make_seq_output("seq-x-pos2", "BENIGN"),
            _make_seq_output("seq-x-pos3", "BENIGN"),
            _make_seq_output("seq-y-pos1", "BENIGN"),   # missed
            _make_seq_output("seq-y-pos2", "BENIGN"),
            _make_seq_output("seq-y-pos3", "BENIGN"),
        ]
        report = score_sequences(all_scenarios, outputs)

        assert report.n_sequences == 2
        assert report.n_threat_sequences == 2
        assert report.early_detection_rate == 0.5    # 1 of 2 sequences
        assert report.missed_sequence_rate == 0.5    # 1 of 2 sequences
        assert report.late_detection_rate == 0.0

    def test_per_sequence_results_populated(self):
        """per_sequence_results dict is populated with at least pattern and is_threat_seq keys."""
        scenarios = _make_4alert_threat_seq()
        outputs = [
            _make_seq_output("seq-a-pos1", "BENIGN"),
            _make_seq_output("seq-a-pos2", "BENIGN"),
            _make_seq_output("seq-a-pos3", "BENIGN"),
            _make_seq_output("seq-a-pos4", "BENIGN"),
        ]
        report = score_sequences(scenarios, outputs)

        assert "seq-a" in report.per_sequence_results
        result = report.per_sequence_results["seq-a"]
        assert "is_threat_seq" in result
        assert result["is_threat_seq"] is True
        assert "model_verdicts" in result
        assert len(result["model_verdicts"]) == 4
