---
phase: 07-testing-and-verification
plan: 02
subsystem: testing
tags: [testing, decision-rubric, backward-compatibility, ground-truth, tdd]
dependency_graph:
  requires: [07-01, phase-06-scenario-generation]
  provides: [GT-decision-verification, backward-compatibility-verification]
  affects: [test suite coverage, benchmark validity guarantees]
tech_stack:
  added: []
  patterns: [parametrized-pytest, session-scoped-fixtures, tdd-green]
key_files:
  created:
    - tests/test_decision_rubric.py
  modified:
    - tests/test_core.py
decisions:
  - "Used source_category (not category) for v1 _meta field — verified from generators.py line 270"
  - "Confirmed B3 config (restricted/5/day/0.85/HIGH/5min) → SUSPICIOUS: weighted_sum=-0.1678 falls in SUSPICIOUS band"
metrics:
  duration: ~8 minutes
  completed: 2026-04-13T05:38:04Z
  tasks_completed: 2
  files_created: 1
  files_modified: 1
---

# Phase 7 Plan 2: GT Decision Rubric and Backward Compatibility Tests Summary

**One-liner:** 11 parametrized GT rubric tests (including 3 adversarial cases) and 5 backward compatibility tests proving default params still produce v1-compatible output with 14 UCF categories and THREAT-heavy distribution.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create GT decision function and ambiguity flag tests | e179459 | tests/test_decision_rubric.py (created) |
| 2 | Add backward compatibility tests to test_core.py | 1396939 | tests/test_core.py (modified, +41 lines) |

## What Was Built

**tests/test_decision_rubric.py** (new, 83 lines):
- `_gt()` helper wraps `assign_ground_truth_v2` with a fixed `np.random.RandomState(42)`
- `TestKnownGTConfigs`: 9 parametrized configs covering all 3 GT classes, including adversarial cases:
  - T2: restricted/5/night/0.10/LOW → THREAT (severity alone cannot override zone+time signals)
  - B2: parking/1/day/0.90/CRITICAL/3min → BENIGN (badge + benign zone override CRITICAL severity)
  - B3: restricted/5/day/0.85/HIGH/5min → SUSPICIOUS (badge reduces but restricted+HIGH keep it out of BENIGN)
- `TestAmbiguityFlag`: 2 tests using `v2_scenarios_1000` session fixture verifying ambiguity metadata correctness

**tests/test_core.py** (extended, +41 lines):
- `TestBackwardCompatibility` class appended without modifying existing code
- 5 tests covering: schema validity, scenario count (3000), 14 UCF categories present, THREAT > 40% distribution, no `ambiguity_flag` in v1 `_meta`

## Test Results

- All 11 tests in `test_decision_rubric.py` pass
- All 72 tests in `test_core.py` pass (67 pre-existing + 5 new)
- No regressions introduced

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Field Path Correction] Used source_category instead of category**
- **Found during:** Task 2 pre-implementation read
- **Issue:** Plan specified `s["_meta"]["category"]` but v1 generator writes `source_category` (generators.py line 270)
- **Fix:** Used `s["_meta"]["source_category"]` in `test_v1_all_14_categories_present`
- **Files modified:** tests/test_core.py
- **Commit:** 1396939

## Known Stubs

None. All tests use live generator output via session fixtures.

## Threat Flags

None. Test-only code; no network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- tests/test_decision_rubric.py: exists and contains TestKnownGTConfigs, TestAmbiguityFlag
- tests/test_core.py: contains TestBackwardCompatibility with 5 test methods
- Commits e179459 and 1396939 confirmed in git log
- All tests pass: 11/11 in test_decision_rubric.py, 72/72 in test_core.py
