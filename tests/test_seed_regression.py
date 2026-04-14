"""Seed-42 regression guard.

These tests pin the exact first-scenario output of MetadataGenerator(seed=42)
for both v1 and v2. Any change to generators.py, distributions.py, or
numpy's RNG call sequence that shifts the stream will cause these tests to
fail immediately — before broken scenarios reach the benchmark.

If you need to intentionally change the seed-42 output (e.g., a distribution
fix that changes GT assignment), update these pinned values in a dedicated
commit with a clear message explaining why. Never update silently.

Pinned: 2026-04-13 (Phase 11 Schema v3)
"""

import hashlib
import json


from psai_bench.generators import MetadataGenerator

# --- Pinned values (populated by running generators on 2026-04-13) ---
# Update intentionally if distribution logic changes; document why in commit.

_PINNED_V1_ALERT_ID = "ucf-meta-00000"
_PINNED_V1_GROUND_TRUTH = "THREAT"
_PINNED_V1_SHA256 = "d768f509d6fad28aa78c19a61491e29d11469aa4502991db595db50cb0366c69"

_PINNED_V2_ALERT_ID = "ucf-meta-v2-00000"
_PINNED_V2_GROUND_TRUTH = "SUSPICIOUS"
_PINNED_V2_SHA256 = "d01630c1927964d36d96a4fdcd83d1299b9ef8872badd9f60543b2ca1a59bbe4"


class TestSeedRegression:
    """Pin seed-42 scenario content for both generator versions."""

    def test_v1_seed42_first_alert_id(self):
        """First alert ID from seed=42 v1 must not change."""
        gen = MetadataGenerator(seed=42, version="v1")
        scenarios = gen.generate_ucf_crime(n=1)
        assert scenarios[0]["alert_id"] == _PINNED_V1_ALERT_ID, (
            f"v1 seed=42 alert_id drifted: got {scenarios[0]['alert_id']!r}, "
            f"expected {_PINNED_V1_ALERT_ID!r}. "
            "RNG stream has shifted. Check recent changes to generators.py or distributions.py."
        )

    def test_v1_seed42_first_ground_truth(self):
        """First scenario GT from seed=42 v1 must not change."""
        gen = MetadataGenerator(seed=42, version="v1")
        scenarios = gen.generate_ucf_crime(n=1)
        assert scenarios[0]["_meta"]["ground_truth"] == _PINNED_V1_GROUND_TRUTH, (
            f"v1 seed=42 ground_truth drifted: got {scenarios[0]['_meta']['ground_truth']!r}, "
            f"expected {_PINNED_V1_GROUND_TRUTH!r}."
        )

    def test_v1_seed42_first_scenario_hash(self):
        """Full first-scenario hash from seed=42 v1 must not change."""
        gen = MetadataGenerator(seed=42, version="v1")
        scenarios = gen.generate_ucf_crime(n=1)
        actual = hashlib.sha256(
            json.dumps(scenarios[0], sort_keys=True, default=str).encode()
        ).hexdigest()
        assert actual == _PINNED_V1_SHA256, (
            f"v1 seed=42 scenario hash drifted. Any field changed. "
            f"Got: {actual!r}, expected: {_PINNED_V1_SHA256!r}"
        )

    def test_v2_seed42_first_alert_id(self):
        """First alert ID from seed=42 v2 must not change."""
        gen = MetadataGenerator(seed=42, version="v2")
        scenarios = gen.generate_ucf_crime(n=1)
        assert scenarios[0]["alert_id"] == _PINNED_V2_ALERT_ID, (
            f"v2 seed=42 alert_id drifted: got {scenarios[0]['alert_id']!r}, "
            f"expected {_PINNED_V2_ALERT_ID!r}. "
            "RNG stream has shifted."
        )

    def test_v2_seed42_first_ground_truth(self):
        """First scenario GT from seed=42 v2 must not change."""
        gen = MetadataGenerator(seed=42, version="v2")
        scenarios = gen.generate_ucf_crime(n=1)
        assert scenarios[0]["_meta"]["ground_truth"] == _PINNED_V2_GROUND_TRUTH

    def test_v2_seed42_first_scenario_hash(self):
        """Full first-scenario hash from seed=42 v2 must not change."""
        gen = MetadataGenerator(seed=42, version="v2")
        scenarios = gen.generate_ucf_crime(n=1)
        actual = hashlib.sha256(
            json.dumps(scenarios[0], sort_keys=True, default=str).encode()
        ).hexdigest()
        assert actual == _PINNED_V2_SHA256, (
            f"v2 seed=42 scenario hash drifted. "
            f"Got: {actual!r}, expected: {_PINNED_V2_SHA256!r}"
        )

    def test_v1_generate_version_not_in_meta(self):
        """v1 _meta must NOT have 'generation_version' key (it was not added until v2)."""
        gen = MetadataGenerator(seed=42, version="v1")
        scenarios = gen.generate_ucf_crime(n=1)
        # v1 scenarios have no generation_version field -- this tests backward compat (TEST-05)
        assert "generation_version" not in scenarios[0]["_meta"], (
            "v1 scenarios unexpectedly gained generation_version field. "
            "This would change the v1 hash and break backward compat."
        )

    def test_v2_generation_version_is_v2(self):
        """v2 _meta must have 'generation_version': 'v2' (backward compat — TEST-05)."""
        gen = MetadataGenerator(seed=42, version="v2")
        scenarios = gen.generate_ucf_crime(n=1)
        assert scenarios[0]["_meta"].get("generation_version") == "v2", (
            "v2 scenarios must have generation_version='v2' in _meta."
        )
