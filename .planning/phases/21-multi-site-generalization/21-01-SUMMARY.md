---
phase: 21-multi-site-generalization
plan: 01
subsystem: scorer, cli
tags: [site-generalization, multi-site, scoring, cli, filtering]
dependency_graph:
  requires: []
  provides: [compute_site_generalization_gap, --site-type-filter, site-generalization-cmd]
  affects: [psai_bench/scorer.py, psai_bench/cli.py]
tech_stack:
  added: []
  patterns: [post-generation-filter, direct-accuracy-computation]
key_files:
  created: [tests/test_site_generalization.py]
  modified: [psai_bench/scorer.py, psai_bench/cli.py]
decisions:
  - compute_site_generalization_gap computes accuracy directly without calling score_run to keep the function lightweight and avoid ambiguity-partition side effects
  - Output filename unchanged when --site-type is provided to preserve artifact identity invariant
metrics:
  duration_minutes: 12
  completed: "2026-04-13T23:30:56Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
---

# Phase 21 Plan 01: Multi-Site Generalization — Scoring Function and CLI Summary

Adds per-site generalization measurement to PSAI-Bench: a scoring function that computes per-site accuracy and the gap between best and worst sites, plus two CLI entry points to invoke it.

## What Was Implemented

### Task 1: compute_site_generalization_gap() in scorer.py

Inserted after `compute_perception_gap()` at line 358 of scorer.py.

**Signature:**
```python
def compute_site_generalization_gap(
    scenarios: list[dict],
    outputs: list[dict],
    train_site: str | None = None,
    test_site: str | None = None,
) -> dict:
```

**Return dict keys:**
- `per_site_accuracy`: `{site_type: float}` for all site types present in scenarios
- `generalization_gap`: `max(accs) - min(accs)`, or `0.0` if fewer than 2 sites
- `train_site`: the `train_site` argument value (may be `None`)
- `test_site`: the `test_site` argument value (may be `None`)
- `train_accuracy`: `per_site_accuracy[train_site]` if train_site present, else `None`
- `test_accuracy`: `per_site_accuracy[test_site]` if test_site present, else `None`

**Implementation:** Builds `{alert_id: verdict}` lookup from outputs, partitions scenarios by `context.site_type`, computes accuracy per site (missing output = incorrect). Does NOT call `score_run()`.

**Tests:** 18 tests in `tests/test_site_generalization.py` covering all 5 specified behaviors including a `monkeypatch` test that patches `score_run` to raise and confirms it is never called.

**Commit:** `b938a60`

### Task 2: CLI additions in cli.py

**A. `--site-type` option on `generate` command**

Added as a `click.Choice` option with 5 valid values (`solar`, `substation`, `commercial`, `industrial`, `campus`). Applied as a post-generation list comprehension filter after all `scenarios.extend()`/`gen.generate()` calls and before the output filename is computed. Output filename is unchanged regardless of whether `--site-type` is provided.

**B. `site-generalization` subcommand**

New command `psai-bench site-generalization` with options:
- `--scenarios PATH` (required)
- `--outputs PATH` (required)
- `--train [solar|substation|commercial|industrial|campus]`
- `--test [solar|substation|commercial|industrial|campus]`

Prints a sorted per-site accuracy table and the generalization gap float. Conditionally prints train/test accuracy if those args were provided and their site type was present in the scenarios.

**Commit:** `fcb7e59`

## Verification Output

### Seed Reproducibility (from plan verification section)

```
Full set commercial count: 85
Filtered count: 85
Counts match: True
Field-identical alerts: 85/85
Seed reproducibility: PASS
```

Every alert in the `--site-type commercial` filtered output appears in the full unfiltered output with identical field values. The filter is a pure view — it does not alter the RNG sequence.

### CLI Help Output

```
--site-type [solar|substation|commercial|industrial|campus]
            Filter generated scenarios to a single site type (post-generation, seed-safe).
```

```
Usage: python -m psai_bench.cli site-generalization [OPTIONS]
  --scenarios PATH  Generated scenario file (JSON).  [required]
  --outputs PATH    System outputs file (JSON).  [required]
  --train [solar|substation|commercial|industrial|campus]
  --test  [solar|substation|commercial|industrial|campus]
```

### Test Suite

```
334 passed in 24.26s
```

All pre-existing tests pass; 18 new tests added.

### score_run Unchanged

`git diff 71c5364 HEAD -- psai_bench/scorer.py` shows only the addition of `compute_site_generalization_gap` between `compute_perception_gap` and `_safety_score`. The bodies of `score_run`, `_score_partition`, `format_dashboard`, and all other existing functions are untouched.

## Deviations from Plan

None. Plan executed exactly as written.

## Known Stubs

None. All returned values are computed from real scenario and output data.

## Threat Flags

None. No new network endpoints, auth paths, or file access patterns introduced. CLI file inputs use `click.Path(exists=True)` (read-only). `--site-type` values are constrained to `click.Choice` enum.

## Self-Check: PASSED

- `tests/test_site_generalization.py` exists: FOUND
- `psai_bench/scorer.py` contains `def compute_site_generalization_gap`: FOUND
- `psai_bench/cli.py` contains `site-generalization`: FOUND
- Commit `b938a60` exists: FOUND
- Commit `fcb7e59` exists: FOUND
- 334 tests pass: CONFIRMED
