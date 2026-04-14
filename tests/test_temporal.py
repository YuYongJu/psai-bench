"""Tests for Phase 14: TemporalSequenceGenerator.

Covers sequence structure, escalation pattern coverage, position uniqueness,
timestamp monotonicity, escalation-point variation, and RNG isolation.
"""

from collections import defaultdict


from psai_bench.generators import TemporalSequenceGenerator


def test_sequence_groups(temporal_scenarios_50):
    """Every sequence_id group has exactly 3, 4, or 5 alerts; total = 50 unique groups."""
    groups = defaultdict(list)
    for alert in temporal_scenarios_50:
        groups[alert["_meta"]["sequence_id"]].append(alert)

    assert len(groups) == 50, f"Expected 50 sequence_ids, got {len(groups)}"
    for seq_id, alerts in groups.items():
        assert len(alerts) in {3, 4, 5}, (
            f"Sequence {seq_id} has {len(alerts)} alerts — expected 3, 4, or 5"
        )


def test_all_patterns_present(temporal_scenarios_50):
    """All three escalation pattern values are present in a 50-sequence batch."""
    patterns = {a["_meta"]["escalation_pattern"] for a in temporal_scenarios_50}
    assert patterns == {"monotonic_escalation", "escalation_then_resolution", "false_alarm"}, (
        f"Unexpected pattern set: {patterns}"
    )


def test_unique_positions(temporal_scenarios_50):
    """Within each group, sequence_position values are exactly [1..seq_length], no gaps or dups.

    Also verifies _meta.sequence_length == len(group) for every alert.
    """
    groups = defaultdict(list)
    for alert in temporal_scenarios_50:
        groups[alert["_meta"]["sequence_id"]].append(alert)

    for seq_id, alerts in groups.items():
        seq_length = alerts[0]["_meta"]["sequence_length"]
        positions = sorted(a["_meta"]["sequence_position"] for a in alerts)
        expected = list(range(1, seq_length + 1))
        assert positions == expected, (
            f"Sequence {seq_id}: positions {positions} != expected {expected}"
        )
        for a in alerts:
            assert a["_meta"]["sequence_length"] == len(alerts), (
                f"Sequence {seq_id}: sequence_length field {a['_meta']['sequence_length']} "
                f"!= actual group length {len(alerts)}"
            )


def test_monotonic_timestamps(temporal_scenarios_50):
    """Timestamps within each sequence group are strictly increasing (no ties, no reversals)."""
    groups = defaultdict(list)
    for alert in temporal_scenarios_50:
        groups[alert["_meta"]["sequence_id"]].append(alert)

    for seq_id, alerts in groups.items():
        sorted_alerts = sorted(alerts, key=lambda a: a["_meta"]["sequence_position"])
        timestamps = [a["timestamp"] for a in sorted_alerts]
        assert timestamps == sorted(timestamps), (
            f"Sequence {seq_id}: timestamps not in ascending order: {timestamps}"
        )
        assert len(set(timestamps)) == len(timestamps), (
            f"Sequence {seq_id}: duplicate timestamps found: {timestamps}"
        )


def test_escalation_point_varies(temporal_scenarios_50):
    """Turn point varies across monotonic_escalation sequences — at least 2 distinct positions."""
    turn_positions = set()
    for alert in temporal_scenarios_50:
        if alert["_meta"]["escalation_pattern"] != "monotonic_escalation":
            continue
        if alert["severity"] in ("HIGH", "CRITICAL") or alert["zone"]["zone_type"] == "restricted":
            turn_positions.add(alert["_meta"]["sequence_position"])

    assert len(turn_positions) >= 2, (
        f"Expected at least 2 distinct turn positions in monotonic_escalation sequences, "
        f"got: {turn_positions}"
    )


def test_rng_isolation():
    """TemporalSequenceGenerator(seed=42).generate(50) called twice produces identical output."""
    g1 = TemporalSequenceGenerator(seed=42)
    s1 = g1.generate(50)
    g2 = TemporalSequenceGenerator(seed=42)
    s2 = g2.generate(50)
    assert [a["alert_id"] for a in s1] == [a["alert_id"] for a in s2], (
        "alert_id lists differ between two runs with same seed — RNG state not isolated"
    )


def test_track_field(temporal_scenarios_50):
    """Every alert has track='temporal'."""
    assert all(a["track"] == "temporal" for a in temporal_scenarios_50), (
        "Some alerts have wrong track field"
    )


def test_meta_fields_present(temporal_scenarios_50):
    """Every alert _meta contains all required temporal keys with correct generation_version."""
    required_keys = {
        "sequence_id", "sequence_position", "sequence_length",
        "escalation_pattern", "generation_version",
    }
    for alert in temporal_scenarios_50:
        meta = alert["_meta"]
        missing = required_keys - set(meta.keys())
        assert not missing, (
            f"Alert {alert['alert_id']} missing _meta keys: {missing}"
        )
    assert all(a["_meta"]["generation_version"] == "v3" for a in temporal_scenarios_50), (
        "Some alerts have wrong generation_version"
    )
