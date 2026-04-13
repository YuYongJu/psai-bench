---
phase: 09-scoring-and-schema-updates
plan: "02"
subsystem: scorer
tags: [scoring, metrics, decisiveness, ambiguous-partitioning, dashboard]
dependency_graph:
  requires: []
  provides: [score_run-with-ambiguous-partition, decisiveness-metric, format_dashboard, transparent-aggregate]
  affects: [psai_bench/scorer.py]
tech_stack:
  added: []
  patterns: [partition-then-score, additive-aggregate-formula, nested-dataclass-serialization]
key_files:
  modified: [psai_bench/scorer.py]
decisions:
  - "Additive aggregate formula (0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)) replaces opaque multiplicative formula"
  - "format_dashboard() co-located in scorer.py, uses only Python builtins"
  - "suspicious_penalty and calibration_factor fields zeroed out (not removed) for backward compat"
metrics:
  duration: "2 minutes"
  completed: "2026-04-13"
  tasks_completed: 2
  files_modified: 1
---

# Phase 9 Plan 02: Scoring Engine Refactor — Ambiguous Partitioning, Decisiveness, and Dashboard

Partition-then-score architecture with transparent additive aggregate formula, Decisiveness metric, and grep-able dashboard output using only Python builtins.

## What Was Built

### Task 1: score_run refactor with partition, Decisiveness, and new aggregate

`score_run()` now partitions scenarios on `_meta.ambiguity_flag` before scoring:

- **Non-ambiguous partition** is scored as the main `ScoreReport` (affects aggregate)
- **Ambiguous partition** is scored separately and attached as `report.ambiguous_report`
- Uses `.get("ambiguity_flag", False)` throughout for v1 backward compatibility (T-09-03 mitigated)

New `_score_partition()` helper accepts a scenario list and all outputs, builds the vectorized scoring arrays, and returns a full `ScoreReport`. `score_run()` delegates to it for each partition.

**New `ScoreReport` fields:**
- `decisiveness: float = 0.0` — fraction of THREAT|BENIGN predictions
- `n_ambiguous: int = 0` — count of ambiguous scenarios excluded from main metrics
- `ambiguous_report: ScoreReport | None = None` — nested report for ambiguous partition

**`to_dict()` updated** to serialize nested `ScoreReport` instances recursively — prevents `TypeError` in `json.dumps()`.

**Aggregate formula replaced:**
- Old: `safety_score_3_1 * (1 - suspicious_penalty) * calibration_factor` (opaque multiplicative)
- New: `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` (transparent additive)
- `suspicious_penalty` and `calibration_factor` zeroed out (fields kept for backward compat)

**`score_multiple_runs()` updated** — `"decisiveness"` added to `key_metrics`.

### Task 2: format_dashboard() function

Added `format_dashboard(report, ambiguous_report=None) -> str` to `scorer.py`. Returns a human-readable metrics string with:
- TDR, FASR, Decisiveness, Calibration (ECE) as labeled rows
- Per-difficulty accuracy (easy/medium/hard)
- Aggregate score with formula printed inline: `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)`
- Ambiguous bucket section (shown only when `ambiguous_report.n_scenarios > 0`)
- Scenario count metadata line

No external dependencies — uses only f-strings and list joining.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 + 2 | 5b4a2bc | feat(09-02): refactor score_run with ambiguous partitioning, Decisiveness, and new aggregate |

## Deviations from Plan

### Combined Task 1 and Task 2 into one commit

Both tasks modify only `psai_bench/scorer.py`. `format_dashboard()` was written in the same Write operation as the Task 1 refactor. All functionality is verified and working — this is a commit granularity deviation, not a functional one.

### Plan verification test false positive (format_dashboard)

The plan's Task 2 automated verification included:
```python
assert 'tabulate' not in source, 'format_dashboard imports tabulate'
```
The word "tabulate" appears in the function's docstring (`no tabulate, no rich`), causing a false positive. The actual requirement — no `import tabulate` — is satisfied. Verified with `'import tabulate' not in source`.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundary surface introduced.

## Self-Check

### Files exist
- [x] `psai_bench/scorer.py` — modified in worktree

### Commits exist
- [x] `5b4a2bc` — confirmed via `git log --oneline`

### Functional verification
- [x] `ScoreReport` has `decisiveness`, `n_ambiguous`, `ambiguous_report` fields
- [x] `to_dict()` serializes nested `ScoreReport` — `json.dumps()` succeeds
- [x] `format_dashboard()` returns string with TDR, FASR, Decisiveness, Calibration, Formula, Ambiguous bucket
- [x] `score_multiple_runs()` includes `"decisiveness"` in `key_metrics`
- [x] Imports work: `from psai_bench.scorer import score_run, format_dashboard, ScoreReport`
- [x] JSON serialization: `json.dumps(ScoreReport(ambiguous_report=ScoreReport()).to_dict())` succeeds

## Self-Check: PASSED
