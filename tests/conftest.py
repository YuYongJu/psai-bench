"""Session-scoped pytest fixtures for PSAI-Bench test suite.

These fixtures generate scenario sets once per test session and reuse them
across all test files, avoiding the 10x+ performance penalty of per-function
regeneration.
"""

import pytest

from psai_bench.generators import MetadataGenerator


@pytest.fixture(scope="session")
def v2_scenarios_1000():
    """1000 v2 scenarios for leakage and ambiguity tests.

    Uses seed=42 for reproducibility. Generated once per session.
    """
    gen = MetadataGenerator(seed=42, version="v2")
    return gen.generate_ucf_crime(n=1000)


@pytest.fixture(scope="session")
def v1_scenarios_default():
    """3000 v1 scenarios for backward compatibility tests.

    Uses seed=42 with default version="v1". Generated once per session.
    """
    gen = MetadataGenerator(seed=42)
    return gen.generate_ucf_crime(n=3000)
