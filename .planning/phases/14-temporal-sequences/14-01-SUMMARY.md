---
phase: 14-temporal-sequences
plan: "01"
subsystem: generators
tags: [temporal, sequence-generator, escalation-patterns, tdd]
dependency_graph:
  requires:
    - psai_bench/distributions.py (assign_ground_truth_v2, description pools)
    - psai_bench/generators.py (helper functions: _assign_difficulty, _generate_timestamp, _generate_recent_events, _sample_valid_site)
  provides:
    - TemporalSequenceGenerator class
    - temporal track CLI support
    - Phase 14 test suite
  affects:
    - psai_bench/generators.py
    - psai_bench/cli.py
    - tests/conftest.py
    - tests/test_temporal.py
tech_stack:
  added: []
  patterns:
    - RNG isolation via dedicated np.random.RandomState per generator class
    - Monotonic timestamp computation via base_dt + timedelta(minutes=interval*(pos-1))
    - Pattern-driven signal trajectories (turn_point governs escalation/resolution pivot)
key_files:
  created:
    - tests/test_temporal.py
  modified:
    - psai_bench/generators.py
    - psai_bench/cli.py
    - tests/conftest.py
decisions:
  - "Used list(UCF_CATEGORY_MAP.keys()) for category sampling — UCF_CATEGORIES alias does not exist in code"
  - "Description pools imported locally inside _build_sequence following ContradictoryGenerator pattern"
  - "lobby zone_type used as-is for neutral zone trajectory — assign_ground_truth_v2 returns 0.0 score for unknown zone types, achieving intended neutral signal"
  - "Weather sampled once per sequence with sample_weather('day', rng) — WEATHER_POOL constant does not exist"
metrics:
  duration: "~8 minutes"
  completed_date: "2026-04-13"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
  files_created: 1
  tests_added: 8
  tests_total: 201
requirements:
  - TEMP-01
  - TEMP-02
  - TEMP-04
---

# Phase 14 Plan 01: Temporal Sequence Generator Summary

TemporalSequenceGenerator producing 3-5 alert sequences with three escalation patterns — monotonic_escalation, escalation_then_resolution, false_alarm — using turn_point-driven signal trajectories and base+interval timestamp computation to guarantee strict monotonicity.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement TemporalSequenceGenerator | 4fa2d55 | psai_bench/generators.py |
| 2 | Tests and CLI wiring | 7fa43bc | tests/test_temporal.py, tests/conftest.py, psai_bench/cli.py |

## What Was Built

**TemporalSequenceGenerator** (`psai_bench/generators.py`):
- `generate(n_sequences)` returns flat list of alerts; 50 sequences yield 150-250 alerts
- `_build_sequence(seq_idx, pattern, start_index)` builds one sequence:
  - `seq_length = rng.randint(3, 6)` — gives 3, 4, or 5
  - `turn_point = rng.randint(2, seq_length)` — guarantees post-turn alerts always exist
  - Shared per-sequence context: category, site_type, zone_sensitivity, device, weather
  - Timestamp: `base_dt + timedelta(minutes=interval_minutes*(pos-1))` for strict monotonicity
- Pattern signal trajectories wired precisely per plan spec

**Test suite** (`tests/test_temporal.py`): 8 tests
- `test_sequence_groups` — every group has 3-5 alerts, exactly 50 groups
- `test_all_patterns_present` — all three pattern values present in 50-sequence batch
- `test_unique_positions` — positions are [1..seq_length], no gaps or duplicates
- `test_monotonic_timestamps` — strictly increasing, no ties
- `test_escalation_point_varies` — at least 2 distinct turn positions across monotonic sequences
- `test_rng_isolation` — two runs with seed=42 produce identical alert_id lists
- `test_track_field` — all alerts have track="temporal"
- `test_meta_fields_present` — all required _meta keys present, generation_version="v3"

**conftest.py**: `temporal_scenarios_50` session-scoped fixture added after `contradictory_scenarios_200`.

**cli.py**: Replaced `UsageError` stub with `TemporalSequenceGenerator(seed=seed).generate(count)` wiring. CLI outputs "Generated N temporal sequences (M total alerts)".

## Verification Results

- `pytest tests/ -x -q`: 201 passed (133 prior + 8 new, 0 regressions)
- `generate --track temporal --n 10`: exits 0, outputs "Generated 10 temporal sequences (45 total alerts)"
- `generate(50)`: 203 alerts, 50 unique sequence_ids, all 3 escalation patterns present
- Timestamps strictly increasing within every sequence group
- Turn point varies: 2+ distinct escalation positions across monotonic sequences
- RNG isolation verified: identical alert_id lists on two consecutive calls with seed=42

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UCF_CATEGORIES alias does not exist — used UCF_CATEGORY_MAP**
- **Found during:** Task 1 implementation
- **Issue:** Plan spec references `UCF_CATEGORIES` but the actual constant in distributions.py is `UCF_CATEGORY_MAP` (a dict, not a list). No `UCF_CATEGORIES` alias exists.
- **Fix:** Used `list(UCF_CATEGORY_MAP.keys())` for category sampling.
- **Files modified:** psai_bench/generators.py

**2. [Rule 1 - Bug] WEATHER_POOL does not exist — used sample_weather()**
- **Found during:** Task 1 implementation
- **Issue:** Plan spec says "sample from WEATHER_POOL or equivalent" but `WEATHER_POOL` is not defined anywhere in distributions.py.
- **Fix:** Used `sample_weather("day", self.rng)` which generates a proper weather dict using the existing `WEATHER_CONDITIONS` pool.
- **Files modified:** psai_bench/generators.py

**3. [Rule 3 - Pattern] Description pools imported locally per ContradictoryGenerator pattern**
- **Found during:** Task 1 implementation
- **Issue:** Plan says "All three description pools are already imported from distributions.py in generators.py" but the module-level imports (lines 16-28) do not include the description pools. ContradictoryGenerator imports them locally inside `generate()`.
- **Fix:** Imported `DESCRIPTION_POOL_AMBIGUOUS`, `DESCRIPTION_POOL_UNAMBIGUOUS_THREAT`, `DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN`, and `assign_ground_truth_v2` locally inside `_build_sequence()`.
- **Files modified:** psai_bench/generators.py

## Known Stubs

None. All sequence fields are fully wired. The `lobby` zone_type used in monotonic_escalation pre-turn signals is intentional — `assign_ground_truth_v2` returns 0.0 for unknown zone types (via `.get("lobby", 0.0)`), achieving the neutral signal trajectory the plan intended.

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries were introduced. Threat register T-14-01 through T-14-03 from the plan cover the accepted risks (unbounded --n count, unvalidated escalation_pattern in _meta, seq-XXXX format leaking count).

## Self-Check: PASSED

- [x] `psai_bench/generators.py` contains `class TemporalSequenceGenerator` — FOUND
- [x] `tests/test_temporal.py` exists with all 8 test functions — FOUND
- [x] `tests/conftest.py` contains `temporal_scenarios_50` fixture — FOUND
- [x] Commit 4fa2d55 exists — FOUND
- [x] Commit 7fa43bc exists — FOUND
- [x] 201 tests pass — VERIFIED
