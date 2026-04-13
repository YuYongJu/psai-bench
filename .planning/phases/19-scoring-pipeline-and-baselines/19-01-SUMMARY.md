---
phase: 19-scoring-pipeline-and-baselines
plan: "01"
subsystem: scoring
tags: [scorer, cost_model, dispatch, format_dashboard, tdd]
dependency_graph:
  requires: [18-02]
  provides: [score_dispatch_run, format_dashboard-cost-extension]
  affects: [psai_bench.scorer]
tech_stack:
  added: []
  patterns: [TDD-red-green, keyword-only-param, delegation-pattern]
key_files:
  created:
    - tests/test_scoring_dispatch.py
  modified:
    - psai_bench/scorer.py
decisions:
  - "cost_report param is keyword-only (after *) so existing positional callers (report, ambiguous_report, track_reports) are unaffected"
  - "score_dispatch_run() delegates 100% to cost_model.score_dispatch — no logic duplicated in scorer.py"
  - "Cost section is strictly appended after N= line — no insertion into existing lines"
metrics:
  duration_minutes: 12
  completed_date: "2026-04-13"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
requirements: [SCORE-01, SCORE-02]
---

# Phase 19 Plan 01: Score Dispatch Run and Dashboard Cost Section Summary

**One-liner:** score_dispatch_run() public delegation wrapper added to scorer.py; format_dashboard() extended with keyword-only cost_report param that appends a Dispatch Cost Analysis section without altering any existing output line.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Failing tests for score_dispatch_run + format_dashboard | 4fd96df | tests/test_scoring_dispatch.py |
| 1 (GREEN) | Add score_dispatch_run() to scorer.py | 16ccfbf | psai_bench/scorer.py |
| 2 (GREEN) | Extend format_dashboard() with cost_report param | 1d9b21b | psai_bench/scorer.py |

## What Was Built

**score_dispatch_run()** — new public function in `psai_bench/scorer.py` that accepts `(scenarios, outputs, model=None)` and returns a `CostScoreReport`. It is a one-line delegation to `_cost_model_score_dispatch` (aliased import of `cost_model.score_dispatch`). This satisfies SCORE-01: the scorer module is now the public import surface for dispatch evaluation without any coupling to existing triage scoring logic.

**format_dashboard() extension** — signature changed from `(report, ambiguous_report=None, track_reports=None)` to `(report, ambiguous_report=None, track_reports=None, *, cost_report=None)`. The `*` forces `cost_report` to be keyword-only, making the change backward-compatible for all existing positional callers. When `cost_report is not None`, a `=== Dispatch Cost Analysis ===` block is appended after the `N= scenarios` line containing: cost ratio, total/mean/optimal USD costs, missing dispatch count, 3-profile sensitivity analysis (low/medium/high), and per-action counts sorted alphabetically.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None. The new surface (score_dispatch_run receiving caller-supplied outputs) was already addressed in the plan's threat model (T-19-01): unrecognized dispatch values increment `n_missing_dispatch` via the existing cost_model guard — no exception is raised and no new attack surface was introduced.

## Test Results

- **140 tests pass** across test_scoring_dispatch.py, test_core.py, test_cost_model.py, test_cli.py, test_phase15_regression.py
- 10 new tests in test_scoring_dispatch.py — all green
- 0 existing tests broken

## Self-Check: PASSED

- tests/test_scoring_dispatch.py: FOUND
- psai_bench/scorer.py contains `score_dispatch_run`: FOUND
- psai_bench/scorer.py contains `cost_report`: FOUND
- Commits 4fd96df, 16ccfbf, 1d9b21b: all present in git log
