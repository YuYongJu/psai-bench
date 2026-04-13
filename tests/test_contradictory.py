"""Contradictory scenario test suite for PSAI-Bench Phase 13.

Validates ContradictoryGenerator output for CONTRA-01 through CONTRA-04 and TEST-03.
"""

import pytest

from psai_bench.generators import ContradictoryGenerator
from psai_bench.schema import validate_alert


class TestContradictoryScenarios:
    """Functional tests for ContradictoryGenerator output correctness."""

    def test_all_scenarios_have_contradictory_flag(self, contradictory_scenarios_200):
        """CONTRA-01: Every scenario must have _meta.contradictory == True."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["_meta"]["contradictory"] is True, (
                f"Scenario {i}: expected _meta.contradictory=True, got {s['_meta']['contradictory']!r}"
            )

    def test_gt_divergence(self, contradictory_scenarios_200):
        """TEST-03: metadata_derived_gt must differ from video_derived_gt in every scenario."""
        for i, s in enumerate(contradictory_scenarios_200):
            meta_gt = s["_meta"]["metadata_derived_gt"]
            video_gt = s["_meta"]["video_derived_gt"]
            assert meta_gt != video_gt, (
                f"Scenario {i}: metadata_derived_gt={meta_gt!r} == video_derived_gt={video_gt!r} "
                f"— GT divergence requirement violated"
            )

    def test_ground_truth_follows_video(self, contradictory_scenarios_200):
        """CONTRA-03: ground_truth must equal video_derived_gt, not metadata_derived_gt."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["_meta"]["ground_truth"] == s["_meta"]["video_derived_gt"], (
                f"Scenario {i}: ground_truth={s['_meta']['ground_truth']!r} != "
                f"video_derived_gt={s['_meta']['video_derived_gt']!r} — "
                "GT must equal video_derived_gt — metadata GT must not become the final label"
            )

    def test_both_subtypes_present(self, contradictory_scenarios_200):
        """CONTRA-02: Both overreach and underreach sub-types must appear in a 200-scenario batch."""
        overreach = [s for s in contradictory_scenarios_200 if s["_meta"]["video_derived_gt"] == "BENIGN"]
        underreach = [s for s in contradictory_scenarios_200 if s["_meta"]["video_derived_gt"] == "THREAT"]
        assert len(overreach) > 0, "No overreach scenarios (video=BENIGN)"
        assert len(underreach) > 0, "No underreach scenarios (video=THREAT)"

    def test_track_is_visual_contradictory(self, contradictory_scenarios_200):
        """All scenarios must have track == 'visual_contradictory'."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["track"] == "visual_contradictory", (
                f"Scenario {i}: track={s['track']!r}"
            )

    def test_severity_and_description_present(self, contradictory_scenarios_200):
        """CONTRA-01: severity and description must be present — they are the misleading metadata."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert "severity" in s, (
                f"Scenario {i}: severity must be present (it's the misleading metadata)"
            )
            assert "description" in s, (
                f"Scenario {i}: description must be present (it's the misleading metadata)"
            )
            assert isinstance(s["description"], str) and len(s["description"]) >= 10, (
                f"Scenario {i}: description must be a string with >= 10 chars, "
                f"got {s['description']!r}"
            )

    def test_visual_data_uri_present(self, contradictory_scenarios_200):
        """Every scenario must have a non-null visual_data.uri."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["visual_data"] is not None, (
                f"Scenario {i}: visual_data must not be None"
            )
            assert s["visual_data"]["uri"] is not None, (
                f"Scenario {i}: visual_data.uri must not be None"
            )
            assert isinstance(s["visual_data"]["uri"], str), (
                f"Scenario {i}: visual_data.uri must be a string"
            )
            assert len(s["visual_data"]["uri"]) > 0, (
                f"Scenario {i}: visual_data.uri must not be empty"
            )

    def test_visual_gt_source_is_video_category(self, contradictory_scenarios_200):
        """All scenarios must have _meta.visual_gt_source == 'video_category'."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["_meta"]["visual_gt_source"] == "video_category", (
                f"Scenario {i}: visual_gt_source={s['_meta']['visual_gt_source']!r}"
            )

    def test_generation_version_is_v3(self, contradictory_scenarios_200):
        """All scenarios must have _meta.generation_version == 'v3'."""
        for i, s in enumerate(contradictory_scenarios_200):
            assert s["_meta"]["generation_version"] == "v3", (
                f"Scenario {i}: generation_version={s['_meta']['generation_version']!r}"
            )

    def test_schema_valid(self, contradictory_scenarios_200):
        """Every scenario must pass validate_alert() — severity and description are present."""
        for i, s in enumerate(contradictory_scenarios_200):
            try:
                validate_alert(s)
            except Exception as exc:
                pytest.fail(f"Scenario {i} failed validate_alert(): {exc}")

    def test_determinism(self):
        """ContradictoryGenerator(seed=42).generate(200) must be identical on two calls."""
        s1 = ContradictoryGenerator(seed=42).generate(200)
        s2 = ContradictoryGenerator(seed=42).generate(200)
        assert s1 == s2, "ContradictoryGenerator is not deterministic with the same seed"

    def test_overreach_descriptions_are_threat_sounding(self, contradictory_scenarios_200):
        """Overreach scenarios must have HIGH or CRITICAL severity (biased metadata signals)."""
        overreach = [s for s in contradictory_scenarios_200 if s["_meta"]["video_derived_gt"] == "BENIGN"]
        for s in overreach:
            assert s["severity"] in ("HIGH", "CRITICAL"), (
                f"Overreach scenario should have HIGH or CRITICAL severity, got {s['severity']!r}"
            )

    def test_underreach_descriptions_are_benign_sounding(self, contradictory_scenarios_200):
        """Underreach scenarios must have LOW severity (biased toward benign)."""
        underreach = [s for s in contradictory_scenarios_200 if s["_meta"]["video_derived_gt"] == "THREAT"]
        for s in underreach:
            assert s["severity"] == "LOW", (
                f"Underreach scenario should have LOW severity, got {s['severity']!r}"
            )
