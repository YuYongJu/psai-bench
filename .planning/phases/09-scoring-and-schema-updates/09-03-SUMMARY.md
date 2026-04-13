---
phase: 09-scoring-and-schema-updates
plan: "03"
subsystem: cli-and-tests
tags: [cli, testing, scoring, dashboard, cleanup]
dependency_graph:
  requires: [09-01, 09-02]
  provides: [CLI wired to format_dashboard, stale tests removed, new scorer tests]
  affects: [psai_bench/cli.py, tests/test_core.py, tests/test_cli.py]
tech_stack:
  added: []
  patterns: [format_dashboard integration, TDD red-green for new scorer behavior]
key_files:
  modified:
    - psai_bench/cli.py
    - tests/test_core.py
    - tests/test_cli.py
decisions:
  - "Deleted _print_report_table entirely — tabulate dependency eliminated from CLI"
  - "Deleted analyze_suspicious_cap CLI command — simulated invalid SUSPICIOUS penalty mechanism"
  - "Deleted TestSuspiciousPenalty (4 tests) — tested old multiplicative formula, now replaced"
  - "Fixed two stale test_cli.py tests as deviation Rule 1 — they tested removed behavior"
metrics:
  duration_minutes: 15
  tasks_completed: 2
  files_modified: 3
  completed_date: "2026-04-13"
---

# Phase 09 Plan 03: CLI Wiring and Test Cleanup Summary

**One-liner:** CLI score/baselines commands now output format_dashboard() result; TestSuspiciousPenalty removed and replaced with TestDecisiveness, TestAmbiguousHandling, TestDashboard covering new scoring model.

## What Was Done

### Task 1: Wire format_dashboard into CLI, remove stale commands

- Replaced both `_print_report_table(report)` call sites in `score` and `baselines` commands with `click.echo(format_dashboard(report))`
- Deleted `_print_report_table` function entirely (was tabulate-dependent, displayed old SUSPICIOUS penalty/calibration_factor metrics)
- Deleted `analyze_suspicious_cap` command entirely — tested old SUSPICIOUS penalty cap mechanism (0.30 threshold), which is now replaced by the transparent additive formula
- `tabulate` no longer imported anywhere in cli.py
- `numpy` import retained — still used by the `compare` command

### Task 2: Update test_core.py and fix test_cli.py

- **Deleted** `TestSuspiciousPenalty` class (4 tests): `test_no_penalty_under_30pct`, `test_penalty_applied_over_30pct`, `test_always_suspicious_gets_penalized`, `test_aggregate_formula` — all tested old multiplicative aggregate formula
- **Added** `TestDecisiveness` (2 tests): all-THREAT/BENIGN -> decisiveness=1.0; all-SUSPICIOUS -> decisiveness=0.0
- **Added** `TestAmbiguousHandling` (2 tests): ambiguous scenarios excluded from n_scenarios in main report; ambiguous_report contains the ambiguous partition
- **Added** `TestDashboard` (2 tests): format_dashboard returns str with TDR/FASR/Decisiveness/Formula; test_aggregate_new_formula verifies `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)`
- Full test suite: **129 passed, 0 failed**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_cli.py had two stale tests referencing removed behavior**
- **Found during:** Task 2 full suite run
- **Issue:** `TestCLIScore.test_score_table_format` asserted `"Primary Metrics" in result.output` — the new dashboard uses `"PSAI-Bench Metrics Dashboard"` header. `TestCLIAnalyzeSuspicious.test_analyze_suspicious_cap` invoked the deleted `analyze-suspicious-cap` CLI command.
- **Fix:** Updated the table format assertion to match new dashboard output header; deleted `TestCLIAnalyzeSuspicious` class entirely.
- **Files modified:** `tests/test_cli.py`
- **Commit:** 8e4cad9

## Self-Check

### Files Exist
- `psai_bench/cli.py` — modified
- `tests/test_core.py` — modified
- `tests/test_cli.py` — modified

### Commits Exist
- e68148b: `feat(09-03): wire format_dashboard into CLI, remove _print_report_table and analyze_suspicious_cap`
- 8e4cad9: `test(09-03): delete TestSuspiciousPenalty, add TestDecisiveness/Ambiguous/Dashboard`

## Self-Check: PASSED

Both commits exist, all 129 tests pass, no stale artifacts remain.
