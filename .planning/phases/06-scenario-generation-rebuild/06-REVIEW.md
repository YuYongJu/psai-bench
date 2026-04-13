---
phase: "06"
reviewed: 2026-04-13T00:00:00Z
depth: standard
status: findings
severity_counts:
  critical: 0
  high: 0
  medium: 0
  low: 4
files_reviewed: 5
files_reviewed_list:
  - psai_bench/distributions.py
  - psai_bench/generators.py
  - psai_bench/schema.py
  - psai_bench/cli.py
  - psai_bench/__init__.py
---

# Phase 06: Code Review Report

**Reviewed:** 2026-04-13
**Depth:** standard
**Files Reviewed:** 5
**Status:** findings (1 warning, 3 info)

## Summary

Phase 06 correctly implements the core v2 scenario generation design. The `assign_ground_truth_v2` weighted scoring function is mathematically sound, SCEN-03 compliance (severity alone cannot cross the threshold) is verified, v1 backward compatibility is preserved by the `version="v1"` default throughout, `_META_SCHEMA_V2` correctly documents all new fields including `ambiguity_flag: boolean`, and the SITE_CATEGORY_BLOCKLIST entries are appropriate for each site type.

One boundary mismatch between the generator and the scoring function causes a specific badge access value to receive an incorrect score weight. Three additional informational items are documented below.

---

## Warnings

### WR-01: Badge access boundary mismatch — value 10 scored in wrong bucket

**File:** `psai_bench/distributions.py:404` and `psai_bench/generators.py:328`

**Issue:** The generator's "moderate" badge bucket uses `randint(10, 30)`, which in numpy produces values from 10 to 29 inclusive (upper bound excluded). The scoring function then checks `badge_access_minutes_ago <= 10`, which catches value 10 and applies the stronger "recent" score of -0.45 rather than the intended "moderate" score of -0.25. Any scenario where `badge_minutes_ago == 10` gets a weighted_sum that is 0.20 lower than intended, which can flip its GT from SUSPICIOUS to BENIGN.

**Fix:** Change the scoring boundary from `<= 10` to `< 10` to match the generator's intent:

```python
# distributions.py line 404
if badge_access_minutes_ago is not None and badge_access_minutes_ago < 10:
    badge_score = -0.45
elif badge_access_minutes_ago is not None and badge_access_minutes_ago <= 30:
    badge_score = -0.25
```

Alternatively, change the generator's moderate bucket to `randint(11, 31)` so that 10 is only reachable from the "recent" bucket.

---

## Info

### IN-01: `rng` parameter in `assign_ground_truth_v2` is accepted but never used

**File:** `psai_bench/distributions.py:389`

**Issue:** The function signature accepts `rng: "np.random.RandomState"` but the body contains no calls to it. The function is fully deterministic, which is correct per GT-03. However, the unused parameter is misleading — callers may assume it introduces randomness.

**Fix:** Either remove the parameter (breaking change, requires updating two call sites in generators.py) or document it inline:

```python
def assign_ground_truth_v2(
    zone_type: str,
    zone_sensitivity: int,
    time_of_day: str,
    device_fpr: float,
    severity: str,
    badge_access_minutes_ago: int | None,
    rng: "np.random.RandomState",  # reserved for future stochastic tie-breaking; currently unused
) -> tuple[str, float, bool]:
```

### IN-02: Documented scoring range [-1.25, +1.25] is inaccurate

**File:** `psai_bench/distributions.py:344`

**Issue:** The comment states the range is `[-1.25, +1.25]`. The actual attainable extremes are approximately +1.31 (restricted zone at sensitivity 5, night, CRITICAL, FPR near 0.01) and -1.23 (parking zone at sensitivity 1, day, LOW, FPR near 0.99, badge 1 min ago). Verified with the scoring formula. The inaccuracy does not affect runtime behavior but could mislead anyone reasoning about edge case scoring.

**Fix:** Update the comment:

```python
# Signal scoring: each signal contributes to a weighted_sum.
# Empirical range: approximately [-1.23, +1.31] at extreme input combinations.
```

### IN-03: No `--version` flag on the `psai-bench` CLI root

**File:** `psai_bench/cli.py:19-22` and `psai_bench/__init__.py:3`

**Issue:** `__init__.py` was bumped to `2.0.0` but there is no `@click.version_option()` on the `main` group, so `psai-bench --version` returns an error. The `--version` option on the `generate` subcommand refers to the generation algorithm version (v1/v2), which is a different concept.

**Fix:** Add a version option to the Click group:

```python
from psai_bench import __version__

@click.group()
@click.version_option(version=__version__, prog_name="psai-bench")
def main():
    """PSAI-Bench: Physical Security AI Triage Benchmark."""
    pass
```

### IN-04: Blocklist resample loop has no failure signal

**File:** `psai_bench/generators.py:229-233` (same pattern at lines 318-322)

**Issue:** The loop resamples site type up to 10 times when a blocked category-site combo is drawn, but silently continues with the blocked combo if all 10 resamples fail. For low-probability blocklist entries with high category weights this is unlikely in practice, but a failed resample produces a nonsense scenario with no diagnostic.

**Fix:** Use `for/else` to detect exhaustion:

```python
site_type = sample_site_type(self.rng)
for _ in range(10):
    blocked = SITE_CATEGORY_BLOCKLIST.get(site_type, set())
    if cat not in blocked:
        break
    site_type = sample_site_type(self.rng)
else:
    # All resamples exhausted — log or handle the blocked combo explicitly
    pass
```

---

## What Was Verified Clean

- **SCEN-03 compliance:** `_SEVERITY_THREAT_SCORES` max is +0.25, `_GT_THRESHOLD` is 0.30. Severity alone cannot cross the threshold. Verified mathematically.
- **v1 backward compatibility:** `MetadataGenerator(seed=42)` defaults to `version="v1"`, which bypasses `generate_ucf_crime_v2` entirely. `VisualGenerator` and `MultiSensorGenerator` both pass `version` through to their internal generators. The v1 path is unchanged.
- **`_META_SCHEMA_V2` correctness:** All five new v2 fields (`generation_version`, `weighted_sum`, `adversarial`, `ambiguity_flag`, `description_category`) are present in the schema definition and match what `generate_ucf_crime_v2` populates in the `_meta` block.
- **SITE_CATEGORY_BLOCKLIST entries:** All blocked combos are site-appropriate. `Shoplifting` and `Robbery` are correctly excluded from solar/substation/industrial (no retail context). `RoadAccidents` exclusions from solar, industrial, commercial, and campus are reasonable.
- **Adversarial injection (`_inject_adversarial_signals`):** `rng.randint(0, 3)` produces 0, 1, or 2. All three branches are reachable. The flip logic correctly inverts signals.
- **Description pool sampling in v2:** `desc_type_roll < 0.70` gives ambiguous (~70%), `< 0.85` gives unambiguous threat (~15%), else gives unambiguous benign (~15%). The pool-size comments in distributions.py (63%/23%/14%) annotate pool membership ratios, not draw probabilities — the intentional divergence is consistent with controlling GT distribution independently of pool composition.
- **No hardcoded secrets or credentials** in any reviewed file.
- **No unsafe Python anti-patterns** (no bare `except:`, no mutable default arguments, no use of `exec`/`compile` for dynamic code execution).

---

_Reviewed: 2026-04-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
