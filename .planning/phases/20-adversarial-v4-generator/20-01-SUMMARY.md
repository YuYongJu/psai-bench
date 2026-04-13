---
phase: 20-adversarial-v4-generator
plan: 01
subsystem: schema-and-distributions
tags: [schema, distributions, adversarial, v4, tdd]
dependency_graph:
  requires: [phase-18 schema extensions, phase-19 scoring pipeline]
  provides: [adversarial_v4 track enum value, ADV_V4_* description pools]
  affects: [psai_bench/schema.py, psai_bench/distributions.py]
tech_stack:
  added: []
  patterns: [TDD red-green, isolated pool constants]
key_files:
  created: [tests/test_adversarial_v4_schema.py]
  modified: [psai_bench/schema.py, psai_bench/distributions.py]
decisions:
  - ADV_V4_* pools placed before function definitions in distributions.py to match existing data-constant layout
  - Pools contain 8 entries each — fixed size documented in plan to prevent future seed regression
  - Description narrative intentionally misleads (wrong ground truth direction); actual GT flows from context signals
metrics:
  duration: ~8 minutes
  completed: 2026-04-13
  tasks_completed: 2
  files_modified: 2
  files_created: 1
requirements_satisfied: [ADV-02, ADV-03]
---

# Phase 20 Plan 01: Schema Track Enum + ADV_V4 Description Pools Summary

Schema foundation for v4 behavioral adversarials: `adversarial_v4` added to ALERT_SCHEMA track enum and three isolated ADV_V4_* description pools added to distributions.py, each with 8 deceptive descriptions whose narrative contradicts the ground truth assigned by context signals.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| TDD-RED | Failing tests for adversarial_v4 track | ecdcfb3 | tests/test_adversarial_v4_schema.py |
| 1 | Add adversarial_v4 to ALERT_SCHEMA track enum | d7481c5 | psai_bench/schema.py |
| 2 | Create ADV_V4_* description pools | 2954525 | psai_bench/distributions.py |

## Verification

Plan verification scripts passed:
- `validate_alert({"track": "adversarial_v4", ...})` does not raise ValidationError
- `validate_alert({"track": "metadata", ...})` still passes (backward compat)
- `validate_alert({"track": "unknown_track", ...})` raises ValidationError
- All three ADV_V4_* pools importable with 8 entries each
- All five existing pool sizes unchanged: DESCRIPTION_POOL_AMBIGUOUS=22, DESCRIPTION_POOL_UNAMBIGUOUS_THREAT=8, DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN=5, CONTRADICTORY_THREAT_DESCRIPTIONS=12, CONTRADICTORY_BENIGN_DESCRIPTIONS=12
- Full test suite: 303 passed, 0 failed

## Decisions Made

1. **Pool placement:** ADV_V4_* constants inserted between ACCESS_EVENTS dict and the sampling functions — consistent with how other data constants are organized throughout distributions.py.

2. **Pool size fixed at 8:** Plan explicitly documents 8 entries per pool. These sizes must not change after this commit because pool size changes break seed reproducibility for existing tracks using numpy RandomState.

3. **Deceptive narrative design:** Each pool's descriptions intentionally mislabel the event (loitering, intrusion, human presence) while the actual ground truth is BENIGN — assigned by `assign_ground_truth_v2` on context signals. This is the behavioral adversarial design: the text misleads, the signals don't.

## Deviations from Plan

None — plan executed exactly as written. Worktree required `git reset --hard b0a909b` before editing because the worktree HEAD was at Phase 5 (`a9ae81c`); after reset all existing pools were present with the correct sizes.

## Known Stubs

None. Both changes are foundational constants; no data flows to UI and no generator logic exists yet (Plan 02 adds AdversarialV4Generator).

## Threat Flags

None. Changes are additive read-only constants and a schema enum extension. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries.

## Self-Check: PASSED

- tests/test_adversarial_v4_schema.py: exists, 64 lines, 4 tests
- psai_bench/schema.py: adversarial_v4 in track enum at line 24
- psai_bench/distributions.py: ADV_V4_LOITERING_AS_WAITING, ADV_V4_AUTHORIZED_AS_INTRUSION, ADV_V4_ENVIRONMENTAL_AS_HUMAN defined
- Commits: ecdcfb3 (test RED), d7481c5 (feat schema), 2954525 (feat distributions) — all in git log
- 303 tests pass
