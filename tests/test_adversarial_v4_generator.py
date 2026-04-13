"""TDD tests for AdversarialV4Generator — Phase 20 Plan 02.

RED phase: written before the implementation. All tests must fail until
AdversarialV4Generator is appended to generators.py.
"""

import json

import pytest


def test_adversarial_v4_generator_importable():
    from psai_bench.generators import AdversarialV4Generator  # noqa: F401


def test_generate_returns_50_scenarios():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    assert len(scenarios) == 50


def test_all_scenarios_have_correct_track():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["track"] == "adversarial_v4", f"Bad track: {s['track']}"


def test_generation_version_is_v4():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["_meta"]["generation_version"] == "v4", (
            f"Bad version: {s['_meta']['generation_version']}"
        )


def test_adversarial_flag_is_true():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["_meta"]["adversarial"] is True


def test_adversarial_type_valid_values():
    from psai_bench.generators import AdversarialV4Generator

    valid_types = {
        "loitering_as_waiting",
        "authorized_as_intrusion",
        "environmental_as_human",
    }
    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["_meta"]["adversarial_type"] in valid_types, (
            f"Invalid adversarial_type: {s['_meta']['adversarial_type']}"
        )


def test_all_three_adversarial_types_present():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    types_seen = {s["_meta"]["adversarial_type"] for s in scenarios}
    assert len(types_seen) == 3, f"Not all 3 adversarial types appeared: {types_seen}"


def test_ground_truth_valid_values():
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["_meta"]["ground_truth"] in {"THREAT", "SUSPICIOUS", "BENIGN"}, (
            f"Invalid ground_truth: {s['_meta']['ground_truth']}"
        )


def test_adversarial_type_never_signal_flip():
    """v4 scenarios must not use 'signal_flip' — that is a v2/v3 type."""
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate(50)
    for s in scenarios:
        assert s["_meta"]["adversarial_type"] != "signal_flip", (
            "adversarial_type must not be 'signal_flip' for v4 scenarios"
        )


def test_seed_reproducibility():
    from psai_bench.generators import AdversarialV4Generator

    gen1 = AdversarialV4Generator(seed=42)
    scenarios1 = gen1.generate(50)

    gen2 = AdversarialV4Generator(seed=42)
    scenarios2 = gen2.generate(50)

    assert json.dumps(scenarios1, sort_keys=True) == json.dumps(scenarios2, sort_keys=True), (
        "Seed reproducibility failed: two runs with seed=42 produced different output"
    )


def test_rng_isolation_from_metadata_generator():
    """Creating AdversarialV4Generator must not contaminate MetadataGenerator output."""
    from psai_bench.generators import AdversarialV4Generator, MetadataGenerator

    # Baseline: MetadataGenerator output without any AdversarialV4Generator
    meta_gen_a = MetadataGenerator(seed=42, version="v2")
    output_a = json.dumps(meta_gen_a.generate_ucf_crime(100), sort_keys=True)

    # Create (but don't use) an AdversarialV4Generator — must not affect global state
    _ = AdversarialV4Generator(seed=42)

    meta_gen_b = MetadataGenerator(seed=42, version="v2")
    output_b = json.dumps(meta_gen_b.generate_ucf_crime(100), sort_keys=True)

    assert output_a == output_b, (
        "RNG CONTAMINATION: MetadataGenerator output changed after AdversarialV4Generator creation"
    )


def test_rng_isolation_full_execution():
    """Running AdversarialV4Generator.generate() must not contaminate MetadataGenerator."""
    from psai_bench.generators import AdversarialV4Generator, MetadataGenerator

    # Baseline
    meta_gen_a = MetadataGenerator(seed=42, version="v2")
    output_a = json.dumps(meta_gen_a.generate_ucf_crime(100), sort_keys=True)

    # Run the adversarial generator fully
    adv_gen = AdversarialV4Generator(seed=42)
    _ = adv_gen.generate(50)  # consume RNG state of adversarial generator

    # MetadataGenerator with same seed must produce identical output
    meta_gen_b = MetadataGenerator(seed=42, version="v2")
    output_b = json.dumps(meta_gen_b.generate_ucf_crime(100), sort_keys=True)

    assert output_a == output_b, (
        "RNG CONTAMINATION: MetadataGenerator output changed after AdversarialV4Generator.generate()"
    )


def test_generate_default_n():
    """Default n=100 should produce exactly 100 scenarios."""
    from psai_bench.generators import AdversarialV4Generator

    gen = AdversarialV4Generator(seed=42)
    scenarios = gen.generate()
    assert len(scenarios) == 100
