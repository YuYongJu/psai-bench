---
phase: 15-scoring-updates
plan: "01"
subsystem: scorer
tags: [scoring, sequences, temporal, dashboard, track-breakdown]
dependency_graph:
  requires: []
  provides: [SequenceScoreReport, score_sequences, format_dashboard-track_reports, partition_by_track]
  affects: [psai_bench/scorer.py, tests/test_scoring_sequences.py]
tech_stack:
  added: []
  patterns: [dataclass-for-report, grouped-iteration-by-meta-field, ast-inspection-in-test]
key_files:
  created: [tests/test_scoring_sequences.py]
  modified: [psai_bench/scorer.py]
decisions:
  - "score_sequences groups by _meta.sequence_id and classifies sequences directly — does not delegate to score_run or _score_partition"
  - "early_detection_rate defined as first THREAT verdict at index 0 or 1 (first two alerts in sorted order)"
  - "Test for score_run isolation uses ast.walk instead of source string scan — avoids false positives from docstrings"
  - "format_dashboard track_reports rendered after Aggregate Score, before ambiguous bucket — preserves visual hierarchy"
  - "partition_by_track defaults missing track field to 'metadata' — backward compatible with v1 scenarios"
metrics:
  duration_seconds: 281
  completed_date: "2026-04-13"
  tasks_completed: 2
  files_modified: 2
---

# Phase 15 Plan 01: Sequence Scoring and Track Dashboard Summary

One-liner: SequenceScoreReport dataclass and score_sequences() for temporal sequence evaluation, plus per-track TDR/FASR/Decisiveness/Aggregate breakdown in format_dashboard.

## What Was Built

### Task 1: SequenceScoreReport and score_sequences()

Added to `psai_bench/scorer.py` (before `_safety_score`):

- `SequenceScoreReport` dataclass with 7 metric fields: `n_sequences`, `n_threat_sequences`, `n_benign_sequences`, `early_detection_rate`, `late_detection_rate`, `missed_sequence_rate`, `false_escalation_rate`, plus `per_sequence_results` dict.
- `score_sequences(scenarios, outputs)` function that:
  - Groups alerts by `_meta.sequence_id` (silently skips alerts without it)
  - Sorts each group by `_meta.sequence_position`
  - Classifies sequences as threat (any GT == "THREAT") or benign (all GT BENIGN/SUSPICIOUS)
  - Computes early/late/missed detection rates for threat sequences
  - Computes false escalation rate for benign sequences
  - Stores per-sequence verdicts and pattern in `per_sequence_results`
  - Does not call `score_run()` — verified by AST inspection test

Created `tests/test_scoring_sequences.py` with 13 tests covering:
- Early detection (index 0 and index 1)
- Middle detection (neither early nor late)
- Late detection (only at last alert)
- Missed sequences
- Benign sequence with and without false escalation
- SUSPICIOUS-only sequences classified as benign
- Mixed files (non-sequence alerts skipped, count unaffected)
- Empty input returns zero-valued report
- score_run isolation verified via AST
- Two-sequence aggregation (rates average correctly)
- per_sequence_results populated with pattern, is_threat_seq, model_verdicts

### Task 2: format_dashboard per-track breakdown and partition_by_track

Extended `format_dashboard` signature:
```python
def format_dashboard(
    report: ScoreReport,
    ambiguous_report: ScoreReport | None = None,
    track_reports: dict[str, ScoreReport] | None = None,
) -> str:
```

- Existing callers with 1 or 2 arguments are completely unaffected (default None)
- When `track_reports` is provided and non-empty, appends `=== Per-Track Breakdown ===` section with one line per track showing TDR, FASR, Decisiveness, Aggregate, N
- When `metadata` and `visual_only` (or `visual_contradictory`) both present, appends `=== Perception-Reasoning Gap (Preview) ===` with the gap value and Phase 16 note
- Track names left-padded to 24 chars; metrics to 4 decimal places

Added `partition_by_track(scenarios)` helper:
- Partitions scenarios list by `track` field
- Defaults missing `track` to `"metadata"` for v1 backward compatibility
- Returns `dict[str, list[dict]]`

## Test Results

| Suite | Before | After |
|-------|--------|-------|
| Baseline (201 tests) | 201 pass | 201 pass |
| New sequence tests | — | 13 pass |
| **Total** | **201** | **214** |

## Commits

| Hash | Description |
|------|-------------|
| 9b15e93 | feat(15-01): add SequenceScoreReport dataclass and score_sequences() function |
| 0a94f3a | feat(15-01): extend format_dashboard with per-track breakdown and add partition_by_track |

## Deviations from Plan

None — plan executed exactly as written.

The worktree required a `git reset --hard 5d32871` before execution because it was based on an older commit (`a9ae81c`) that predated `format_dashboard`, `_score_partition`, and `decisiveness`. The reset was a setup correction, not a deviation from the plan's intended scope.

## Known Stubs

None. All metrics are computed from real input data. No hardcoded empty values flow to rendering.

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes introduced. `score_sequences` and `partition_by_track` are pure computation functions with no I/O.

## Self-Check: PASSED

- psai_bench/scorer.py: FOUND
- tests/test_scoring_sequences.py: FOUND
- .planning/phases/15-scoring-updates/15-01-SUMMARY.md: FOUND
- Commit 9b15e93: FOUND
- Commit 0a94f3a: FOUND
