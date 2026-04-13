---
phase: 19-scoring-pipeline-and-baselines
plan: "02"
subsystem: baselines
tags: [baselines, dispatch, scoring, tdd]
dependency_graph:
  requires: []
  provides: [VERDICT_TO_DEFAULT_DISPATCH, dispatch-field-in-baselines]
  affects: [scoring-pipeline, cost-model-evaluation]
tech_stack:
  added: []
  patterns: [module-level-mapping, tdd-red-green]
key_files:
  created:
    - tests/test_baselines_dispatch.py
  modified:
    - psai_bench/baselines.py
decisions:
  - "dispatch derived from predicted verdict (not GT) — mapping locked in 19-CONTEXT.md"
  - "VERDICT_TO_DEFAULT_DISPATCH covers all 3 verdicts exhaustively; KeyError impossible in production paths"
  - "DISPATCH_ACTIONS import retained for documentation/validation clarity even though no runtime loop needed"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-13"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 2
requirements: [SCORE-03]
---

# Phase 19 Plan 02: Baseline Dispatch Field Injection Summary

VERDICT_TO_DEFAULT_DISPATCH module-level mapping added to baselines.py; dispatch field injected into all 4 baseline outputs using TDD.

## What Was Built

Added `VERDICT_TO_DEFAULT_DISPATCH` at module level in `psai_bench/baselines.py` and injected a `"dispatch"` key into every output dict from all 4 baseline functions. This satisfies SCORE-03: baselines can now be evaluated with `score_dispatch_run()` without any manual post-processing step.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| RED | Failing tests for dispatch field and mapping | e4e9454 | tests/test_baselines_dispatch.py |
| GREEN | VERDICT_TO_DEFAULT_DISPATCH + dispatch in all 4 baselines | 2018496 | psai_bench/baselines.py |

## Mapping

```python
VERDICT_TO_DEFAULT_DISPATCH = {
    "THREAT":     "armed_response",
    "SUSPICIOUS": "operator_review",
    "BENIGN":     "auto_suppress",
}
```

Covers all 3 verdict classes exhaustively. All baseline functions produce verdicts exclusively from `VERDICTS = ("THREAT", "SUSPICIOUS", "BENIGN")` — KeyError is impossible.

## Verification

- `from psai_bench.baselines import VERDICT_TO_DEFAULT_DISPATCH` succeeds
- All 4 baselines: every output dict has `"dispatch"` with value in `DISPATCH_ACTIONS`
- `always_suspicious_baseline`: dispatch is always `"operator_review"`
- `severity_heuristic_baseline`: CRITICAL severity → verdict=THREAT → dispatch=armed_response; LOW → BENIGN → auto_suppress
- Full suite: **289 tests passed, 0 failures** (no regressions)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths, or trust boundary changes introduced.

## Self-Check: PASSED

- `psai_bench/baselines.py` exists with VERDICT_TO_DEFAULT_DISPATCH and dispatch in all 4 functions
- `tests/test_baselines_dispatch.py` exists with 22 tests
- Commit e4e9454 exists (RED — test file)
- Commit 2018496 exists (GREEN — implementation)
- Full test suite: 289 passed
