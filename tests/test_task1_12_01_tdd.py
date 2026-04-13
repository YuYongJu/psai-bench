"""TDD RED: VisualOnlyGenerator import and basic contract test.

This file is the RED phase stub — it fails because VisualOnlyGenerator
does not exist yet. Remove this file after implementing the class.
"""
import pytest


def test_visual_only_generator_importable():
    """VisualOnlyGenerator must be importable from psai_bench.generators."""
    from psai_bench.generators import VisualOnlyGenerator  # noqa: F401


def test_visual_only_generator_basic_contract():
    """VisualOnlyGenerator(seed=42).generate(5) must return 5 dicts with correct keys."""
    from psai_bench.generators import VisualOnlyGenerator

    s = VisualOnlyGenerator(seed=42).generate(5)
    assert len(s) == 5
    for sc in s:
        assert sc["track"] == "visual_only"
        assert "severity" not in sc
        assert "description" not in sc
        assert sc["visual_data"]["uri"] is not None
        assert sc["_meta"]["visual_gt_source"] == "video_category"
        assert sc["_meta"]["generation_version"] == "v3"
