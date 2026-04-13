---
phase: 15-scoring-updates
plan: "02"
subsystem: scorer
tags: [scoring, perception-gap, track-validation, regression-testing, tdd]
dependency_graph:
  requires:
    - phase: 15-01
      provides: [SequenceScoreReport, score_sequences, partition_by_track, format_dashboard-track_reports]
  provides:
    - compute_perception_gap() in psai_bench/scorer.py
    - tests/test_phase15_regression.py with 4 test classes (14 tests)
  affects: [phase-16-frame-gap-analysis]
tech-stack:
  added: []
  patterns:
    - "TDD red-green for pure functions: write failing import tests before adding implementation"
    - "Duplicate test helpers locally when tests/ has no __init__.py (avoid cross-module import)"
    - "Subprocess guard pattern: TestFullRegression133 spawns pytest subprocess and asserts returncode==0"
key-files:
  created: [tests/test_phase15_regression.py]
  modified: [psai_bench/scorer.py]
key-decisions:
  - "compute_perception_gap() inserted between score_sequences() and _safety_score() to keep public API functions grouped before private helpers"
  - "ValueError raised (not returned) when either report has n_scenarios==0 — callers should validate inputs; T-15-05 mitigated"
  - "_make_scenario/_make_output helpers duplicated in test_phase15_regression.py rather than imported from test_core.py — tests/ has no __init__.py and relative imports would break on pytest collection"
  - "TestFullRegression133 asserts returncode==0 (not a hardcoded count) — worktree has 77 tests in test_core.py, not 133 as plan stated; the guard still enforces no regression"
  - "score_run() is completely unmodified — signature ['scenarios','outputs'], body, and behavior identical to base commit 07b51f8"
patterns-established:
  - "Perception gap computation: gap = metadata.aggregate_score - visual.aggregate_score; positive means metadata context helps"
  - "Track validation SCORE-04: visual_only requires visual_data.uri; visual_contradictory requires _meta.contradictory=True and visual_gt_source='video_category'; temporal requires _meta.sequence_id and sequence_position"
requirements-completed: [SCORE-02, SCORE-04, TEST-04]
duration: 15min
completed: 2026-04-13
---

# Phase 15 Plan 02: Perception Gap Metric and Phase 15 Regression Suite Summary

**compute_perception_gap() added to scorer.py using TDD, with 14-test regression suite confirming gap computation, score_run() contract lock, SCORE-04 track validation, and full test_core.py guard.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-04-13
- **Tasks:** 2
- **Files modified:** 2 (psai_bench/scorer.py, tests/test_phase15_regression.py)

## Accomplishments

- Added `compute_perception_gap(metadata_report, visual_report) -> float` to scorer.py between score_sequences() and _safety_score()
- Validated n_scenarios > 0 on both inputs; raises ValueError with descriptive message (T-15-05 mitigated)
- Created tests/test_phase15_regression.py with 14 tests across 4 classes:
  - TestComputePerceptionGap (6): positive/negative/zero gap, ValueError on empty metadata, ValueError on empty visual, real scored reports
  - TestScoreRunContractGuard (3): signature locked to ['scenarios','outputs'], return type, empty-input behavior
  - TestTrackValidationBehavior (4): SCORE-04 confirmed — visual_only missing uri, visual_contradictory missing flag, temporal missing sequence_id all fail; valid visual_only passes
  - TestFullRegression133 (1): subprocess guard verifying test_core.py returncode==0
- Full suite: 228 tests passing (214 baseline + 14 new), zero regressions

## Task Commits

TDD Task 1 had two commits (RED then GREEN):

1. **Task 1 RED: Failing tests for compute_perception_gap** - `369650a` (test)
2. **Task 1 GREEN: Add compute_perception_gap() to scorer.py** - `31a2146` (feat)
3. **Task 2: Complete Phase 15 regression test suite** - `268de2d` (feat)

## Files Created/Modified

- `psai_bench/scorer.py` — Added `compute_perception_gap()` at line 301 (between score_sequences and _safety_score); score_run() at line 523 unmodified
- `tests/test_phase15_regression.py` — New file; 4 test classes, 14 tests, local helper duplicates

## Decisions Made

- Inserted compute_perception_gap() in the public-API section (after score_sequences, before _safety_score) to maintain grouping convention established in Plan 15-01
- Chose ValueError over returning NaN for empty inputs — callers should gate on n_scenarios; ValueError surfaces misuse immediately
- Duplicated _make_scenario/_make_output locally rather than importing from test_core — tests/ has no __init__.py and pytest import isolation would fail
- TestFullRegression133 asserts returncode==0 not a hardcoded count — the plan's "133 tests" count is incorrect for this worktree (worktree has 77 tests in test_core.py); the subprocess guard is still correct and enforces no regression

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Worktree rebased onto master before execution**
- **Found during:** Initial setup
- **Issue:** Worktree branch `worktree-agent-ac0b5ab9` was at commit `a9ae81c` (phase 5 state), predating all Phase 15 work; plan required base `07b51f8`
- **Fix:** `git rebase master` — worktree fast-forwarded to master HEAD
- **Files modified:** None (setup correction only)
- **Verification:** `git rev-parse HEAD` confirmed `07b51f8b85fa6f9f49a95b05491dd7c7ec77eb9f`

**2. [Rule 1 - Bug] Plan's "133 test_core.py tests" count corrected in implementation**
- **Found during:** Task 2 (TestFullRegression133 design)
- **Issue:** Plan states "All 133 existing test_core.py tests pass" and names the class TestFullRegression133, but test_core.py actually contains 77 tests in this worktree (214 total across all files)
- **Fix:** Implemented the class as specified (subprocess + returncode==0 assertion) without hardcoding 133 as a count; class name retained as TestFullRegression133 per plan
- **Files modified:** tests/test_phase15_regression.py
- **Verification:** Test passes; pytest output shows 77 tests in test_core.py, all passing

---

**Total deviations:** 2 auto-fixed (1 setup correction, 1 count discrepancy in plan)
**Impact on plan:** Both handled cleanly. Setup correction was required to reach the correct base. Count discrepancy was resolved by implementing the intent (no regression) rather than the incorrect literal value.

## Issues Encountered

None — after rebasing to the correct base, execution proceeded without blocking issues.

## Known Stubs

None. compute_perception_gap() is a pure computation function with no hardcoded values. All test assertions use real computed values from generators and score_run().

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes introduced.
- T-15-05 (Tampering): mitigated — n_scenarios validated before computation; ValueError raised with descriptive message
- TestFullRegression133 subprocess: only reads pytest exit code from same-repo process; no external network access (T-15-07 accepted)

## Next Phase Readiness

- Phase 15 complete: SequenceScoreReport + score_sequences (15-01) and compute_perception_gap (15-02) both delivered
- Phase 16 (frame-gap analysis / analyze-frame-gap command) can import compute_perception_gap directly from psai_bench.scorer
- No blockers

---
*Phase: 15-scoring-updates*
*Completed: 2026-04-13*
