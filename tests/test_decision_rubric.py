"""GT decision function and ambiguity flag tests.

TEST-02: Decision rubric produces expected GT for known configurations.
TEST-04: Ambiguous-flagged scenarios have correct metadata.
"""

import numpy as np
import pytest

from psai_bench.distributions import assign_ground_truth_v2


def _gt(zone_type, zone_sensitivity, time_of_day, device_fpr, severity, badge_minutes_ago=None):
    """Call assign_ground_truth_v2 with a fixed rng and return (gt_label, weighted_sum, is_ambiguous)."""
    rng = np.random.RandomState(42)
    gt, ws, is_ambiguous = assign_ground_truth_v2(
        zone_type=zone_type,
        zone_sensitivity=zone_sensitivity,
        time_of_day=time_of_day,
        device_fpr=device_fpr,
        severity=severity,
        badge_access_minutes_ago=badge_minutes_ago,
        rng=rng,
    )
    return gt, ws, is_ambiguous


class TestKnownGTConfigs:
    """TEST-02: Decision rubric produces expected GT for known configurations."""

    CONFIGS = [
        # THREAT configs
        ("T1_canonical_threat",      "restricted", 5, "night", 0.15, "HIGH",     None, "THREAT",     False),
        ("T2_adversarial_low_sev",   "restricted", 5, "night", 0.10, "LOW",      None, "THREAT",     False),
        ("T3_utility_night",         "utility",    4, "night", 0.20, "LOW",      None, "THREAT",     False),
        # SUSPICIOUS configs
        ("S1_ambiguous_by_design",   "interior",   3, "dusk",  0.50, "MEDIUM",   None, "SUSPICIOUS", True),
        ("S2_non_ambiguous_susp",    "perimeter",  3, "night", 0.50, "LOW",      None, "SUSPICIOUS", False),
        ("S3_perimeter_dusk_ambig",  "perimeter",  3, "dusk",  0.60, "MEDIUM",   None, "SUSPICIOUS", True),
        # BENIGN configs
        ("B1_canonical_benign",      "parking",    2, "day",   0.85, "LOW",      5,    "BENIGN",     False),
        ("B2_adversarial_critical",  "parking",    1, "day",   0.90, "CRITICAL", 3,    "BENIGN",     False),
        # B3 is adversarial: HIGH sev + restricted + day + badge = SUSPICIOUS, NOT BENIGN
        ("B3_adversarial_high_restricted", "restricted", 5, "day", 0.85, "HIGH", 5,    "SUSPICIOUS", False),
    ]

    @pytest.mark.parametrize(
        "name,zone_type,zone_sensitivity,time_of_day,device_fpr,severity,badge,expected_gt,expected_ambiguous",
        CONFIGS,
        ids=[c[0] for c in CONFIGS],
    )
    def test_known_config(self, name, zone_type, zone_sensitivity, time_of_day,
                          device_fpr, severity, badge, expected_gt, expected_ambiguous):
        gt, ws, is_ambiguous = _gt(zone_type, zone_sensitivity, time_of_day,
                                    device_fpr, severity, badge)
        assert gt == expected_gt, (
            f"Config '{name}': expected GT={expected_gt}, got GT={gt} (weighted_sum={ws:.4f})"
        )
        assert is_ambiguous == expected_ambiguous, (
            f"Config '{name}': expected ambiguous={expected_ambiguous}, got {is_ambiguous}"
        )


class TestAmbiguityFlag:
    """TEST-04: Ambiguous-flagged scenarios have correct metadata."""

    def test_ambiguous_scenarios_have_suspicious_gt(self, v2_scenarios_1000):
        """Every scenario with ambiguity_flag=true must have GT=SUSPICIOUS."""
        ambiguous = [s for s in v2_scenarios_1000 if s["_meta"].get("ambiguity_flag", False)]
        assert len(ambiguous) > 0, "No ambiguous scenarios found — expected some in 1000 v2 scenarios"
        for s in ambiguous:
            assert s["_meta"]["ground_truth"] == "SUSPICIOUS", (
                f"Ambiguous scenario {s['alert_id']} has GT={s['_meta']['ground_truth']}, expected SUSPICIOUS"
            )

    def test_non_ambiguous_scenarios_exist_per_class(self, v2_scenarios_1000):
        """Non-flagged scenarios must exist for each GT class."""
        non_ambiguous = [s for s in v2_scenarios_1000 if not s["_meta"].get("ambiguity_flag", False)]
        gt_classes = {s["_meta"]["ground_truth"] for s in non_ambiguous}
        for expected_class in ("THREAT", "SUSPICIOUS", "BENIGN"):
            assert expected_class in gt_classes, (
                f"No non-ambiguous scenarios found with GT={expected_class}"
            )
