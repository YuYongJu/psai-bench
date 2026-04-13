"""Visual-only scenario test suite for PSAI-Bench Phase 12.

Validates VisualOnlyGenerator output for:
- Schema conformance (severity/description absent, visual_data.uri present)
- GT correctness (UCF_CATEGORY_MAP[source_category]["ground_truth"] == _meta.ground_truth)
- RNG determinism (seed=42 produces identical output on two calls)
- Leakage safety (no single metadata field predicts GT above 70% stump accuracy)

VIS-01, VIS-02, VIS-03, VIS-04, TEST-02 requirements.
"""

import numpy as np
import pytest
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

from psai_bench.distributions import UCF_CATEGORY_MAP
from psai_bench.generators import VisualOnlyGenerator
from psai_bench.schema import validate_alert


# ---------------------------------------------------------------------------
# Stump accuracy helper
# ---------------------------------------------------------------------------

def _stump_accuracy(scenarios, extractor_fn, is_numeric=False):
    """Fit a depth-1 decision stump on a single extracted field and return training accuracy.

    Training accuracy is a worst-case upper bound for leakage — if the stump can't
    achieve 70% on its own training data, the field carries no exploitable signal.
    """
    X_raw = [extractor_fn(s) for s in scenarios]
    y_labels = [s["_meta"]["ground_truth"] for s in scenarios]

    le_gt = LabelEncoder()
    y = le_gt.fit_transform(y_labels)

    if is_numeric:
        X = np.array(X_raw, dtype=float).reshape(-1, 1)
    else:
        le = LabelEncoder()
        X = le.fit_transform(X_raw).reshape(-1, 1)

    clf = DecisionTreeClassifier(max_depth=1, random_state=42)
    clf.fit(X, y)
    return clf.score(X, y)


# ---------------------------------------------------------------------------
# Core scenario tests
# ---------------------------------------------------------------------------

class TestVisualOnlyScenarios:
    """Functional tests for VisualOnlyGenerator output correctness."""

    def test_all_have_video_uri(self, visual_only_scenarios_200):
        """VIS-01: Every scenario must have a non-null visual_data.uri."""
        for s in visual_only_scenarios_200:
            assert s["visual_data"] is not None, "visual_data must not be None"
            assert s["visual_data"]["uri"] is not None, "visual_data.uri must not be None"
            assert isinstance(s["visual_data"]["uri"], str), "visual_data.uri must be a string"
            assert len(s["visual_data"]["uri"]) > 0, "visual_data.uri must not be empty"

    def test_no_severity_or_description_key(self, visual_only_scenarios_200):
        """VIS-04: Neither 'severity' nor 'description' key may appear in any scenario."""
        for i, s in enumerate(visual_only_scenarios_200):
            assert "severity" not in s, (
                f"Scenario {i} has a 'severity' key — must be absent, not null"
            )
            assert "description" not in s, (
                f"Scenario {i} has a 'description' key — must be absent, not null"
            )

    def test_gt_source_is_video_category(self, visual_only_scenarios_200):
        """VIS-02: All scenarios must have _meta.visual_gt_source == 'video_category'."""
        for i, s in enumerate(visual_only_scenarios_200):
            assert s["_meta"]["visual_gt_source"] == "video_category", (
                f"Scenario {i} has visual_gt_source={s['_meta']['visual_gt_source']!r}"
            )

    def test_gt_matches_ucf_map(self, visual_only_scenarios_200):
        """VIS-02: _meta.ground_truth must match UCF_CATEGORY_MAP[source_category]['ground_truth']."""
        for i, s in enumerate(visual_only_scenarios_200):
            cat = s["_meta"]["source_category"]
            expected_gt = UCF_CATEGORY_MAP[cat]["ground_truth"]
            actual_gt = s["_meta"]["ground_truth"]
            assert actual_gt == expected_gt, (
                f"Scenario {i} (category={cat!r}): "
                f"expected GT={expected_gt!r}, got {actual_gt!r}"
            )

    def test_schema_valid(self, visual_only_scenarios_200):
        """Every scenario must pass validate_alert() — severity/description are optional in v3."""
        for i, s in enumerate(visual_only_scenarios_200):
            try:
                validate_alert(s)
            except Exception as exc:
                pytest.fail(f"Scenario {i} failed validate_alert(): {exc}")

    def test_determinism(self):
        """VIS-01: VisualOnlyGenerator(seed=42).generate(200) must be identical on two calls."""
        s1 = VisualOnlyGenerator(seed=42).generate(200)
        s2 = VisualOnlyGenerator(seed=42).generate(200)
        assert s1 == s2, "VisualOnlyGenerator is not deterministic with the same seed"

    def test_generation_version_is_v3(self, visual_only_scenarios_200):
        """All scenarios must have _meta.generation_version == 'v3'."""
        for i, s in enumerate(visual_only_scenarios_200):
            assert s["_meta"]["generation_version"] == "v3", (
                f"Scenario {i} has generation_version={s['_meta']['generation_version']!r}"
            )

    def test_track_is_visual_only(self, visual_only_scenarios_200):
        """All scenarios must have track == 'visual_only'."""
        for s in visual_only_scenarios_200:
            assert s["track"] == "visual_only"

    def test_visual_data_structure(self, visual_only_scenarios_200):
        """visual_data must have type='video_clip', numeric duration, and string resolution."""
        for i, s in enumerate(visual_only_scenarios_200):
            vd = s["visual_data"]
            assert vd["type"] == "video_clip", f"Scenario {i}: type={vd['type']!r}"
            assert isinstance(vd["duration_sec"], (int, float)), (
                f"Scenario {i}: duration_sec must be numeric"
            )
            assert vd["duration_sec"] >= 4.0, f"Scenario {i}: duration too short"
            assert isinstance(vd["resolution"], str), f"Scenario {i}: resolution must be a string"
            assert "keyframe_uris" in vd, f"Scenario {i}: missing keyframe_uris field"
            assert isinstance(vd["keyframe_uris"], list), f"Scenario {i}: keyframe_uris must be list"


# ---------------------------------------------------------------------------
# Leakage stump tests (TEST-02, VIS-03)
# ---------------------------------------------------------------------------

class TestVisualOnlyLeakage:
    """Decision stump leakage tests — no single metadata field may predict GT above 70%.

    TEST-02, VIS-03: visual-only scenarios use shared distribution pools (same
    sample_zone/sample_device/sample_site_type as MetadataGenerator) precisely
    so that metadata signals carry no exploitable GT signal.
    """

    MAX_STUMP_ACCURACY = 0.70

    def test_leakage_stump_zone_type(self, visual_only_scenarios_200):
        """zone['type'] must not predict ground_truth above 70% stump accuracy."""
        acc = _stump_accuracy(
            visual_only_scenarios_200,
            extractor_fn=lambda s: s["zone"]["type"],
            is_numeric=False,
        )
        assert acc < self.MAX_STUMP_ACCURACY, (
            f"zone_type stump accuracy={acc:.3f} exceeds threshold {self.MAX_STUMP_ACCURACY} "
            f"— metadata leakage detected"
        )

    def test_leakage_stump_time_of_day(self, visual_only_scenarios_200):
        """context['time_of_day'] must not predict ground_truth above 70% stump accuracy."""
        acc = _stump_accuracy(
            visual_only_scenarios_200,
            extractor_fn=lambda s: s["context"]["time_of_day"],
            is_numeric=False,
        )
        assert acc < self.MAX_STUMP_ACCURACY, (
            f"time_of_day stump accuracy={acc:.3f} exceeds threshold {self.MAX_STUMP_ACCURACY} "
            f"— metadata leakage detected"
        )

    def test_leakage_stump_device_fpr(self, visual_only_scenarios_200):
        """device['false_positive_rate'] must not predict ground_truth above 70% stump accuracy."""
        acc = _stump_accuracy(
            visual_only_scenarios_200,
            extractor_fn=lambda s: s["device"]["false_positive_rate"],
            is_numeric=True,
        )
        assert acc < self.MAX_STUMP_ACCURACY, (
            f"device_fpr stump accuracy={acc:.3f} exceeds threshold {self.MAX_STUMP_ACCURACY} "
            f"— metadata leakage detected"
        )
