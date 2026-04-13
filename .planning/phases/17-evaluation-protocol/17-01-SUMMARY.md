---
phase: 17-evaluation-protocol
plan: 01
subsystem: documentation
tags: [evaluation-protocol, documentation, PROTO-01]
dependency_graph:
  requires:
    - psai_bench/scorer.py
    - psai_bench/generators.py
    - psai_bench/frame_extraction.py
    - psai_bench/distributions.py
    - psai_bench/cli.py
    - docs/decision-rubric.md
  provides:
    - docs/EVALUATION_PROTOCOL.md
  affects:
    - researcher onboarding
    - evaluation reproducibility
tech_stack:
  added: []
  patterns:
    - documentation-from-source (all rules derived from actual Python source, not memory)
key_files:
  created:
    - docs/EVALUATION_PROTOCOL.md
  modified: []
decisions:
  - "Cross-reference decision-rubric.md for metadata GT signal tables rather than duplicating — single source of truth for assign_ground_truth_v2() scoring"
  - "Document actual FPR values from code: overreach uses low_quality profile (~0.85 FPR), not 'low-FPR device' as plan description implied"
  - "Note that temporal generator uses 'lobby' and 'evening' zone/time values that score as 0.0 in the signal maps — document accurately not idiomatically"
metrics:
  duration: ~25 minutes
  completed: 2026-04-13
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 17 Plan 01: Evaluation Protocol Summary

## One-Liner

Complete PSAI-Bench evaluation protocol — four-track GT derivation, `score_run`/`score_sequences` routing, `extract_keyframes` FRAME-02 constraint, perception-reasoning gap formula, and worked examples derived from source code.

## What Was Built

Created `docs/EVALUATION_PROTOCOL.md` (798 lines, 10 sections) from direct inspection of the source files for Phases 11-16. Every GT rule, scoring formula, and field definition was verified against the actual Python implementation before writing.

The document satisfies PROTO-01: a researcher reading only this document can evaluate any AI system against all four PSAI-Bench tracks without reading source code.

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write docs/EVALUATION_PROTOCOL.md | ce77ea9 | docs/EVALUATION_PROTOCOL.md |

## Section Coverage

- **Section 1:** Overview — four tracks, research question, `_meta` visibility rules
- **Section 2:** Metadata Track — five-signal GT, cross-reference to decision-rubric.md, two worked examples (THREAT and BENIGN with full signal tables)
- **Section 3:** Visual-Only Track — UCF_CATEGORY_MAP direct GT, leakage constraint, full 14-category GT table, worked example with scenario dict snippet
- **Section 4:** Visual-Contradictory Track — `video_derived_gt` always wins, overreach/underreach explained with actual FPR values, two worked examples
- **Section 5:** Temporal Track — per-alert GT computation, three escalation patterns with actual field values from `_build_sequence()`, `SequenceScoreReport` field definitions, worked example
- **Section 6:** Scoring Functions Reference — `score_run` and `score_sequences` inputs/outputs, aggregate score formula (`0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)`), mixed-track partitioning
- **Section 7:** Frame Extraction Baseline — `extract_keyframes()` signature, FRAME-02 MUST NOT constraint on `anomaly_segments`, install, determinism
- **Section 8:** Perception-Reasoning Gap — formula, `compute_perception_gap()`, interpretation table, CLI command, dashboard preview
- **Section 9:** CLI Quick Reference — generate/score/gap commands for all tracks
- **Section 10:** Reproducibility — seed guarantees, RNG isolation, generation version, submission validation

## Deviations from Plan

### Auto-fixed Issues

None — this was a documentation-only task.

### Accuracy Corrections (versus plan text, matching source code)

**1. Overreach FPR value corrected**
- **Found during:** Reading ContradictoryGenerator source
- **Issue:** Plan described overreach as using a "low-FPR device" — misleading. The code uses `low_fpr_mean = 0.85` (the `low_quality` device profile), which is a HIGH false positive rate (85%)
- **Fix:** Documented the actual 0.85 FPR value with explanation that strong zone+time+severity signals override it
- **Impact:** Researcher accuracy

**2. Temporal zone/time values documented accurately**
- **Found during:** Reading `_build_sequence()` source
- **Issue:** Plan said "day zone" for monotonic_escalation pre-turn alerts. Actual code uses `zone_type = "lobby"` and `time_of_day = "evening"`, neither of which exist in `_ZONE_THREAT_SCORES` or `_TIME_THREAT_SCORES` — they score as 0.0 via `dict.get()` defaults
- **Fix:** Documented the actual string values with a parenthetical explaining they resolve to 0.0

**3. Temporal zone/device field shapes differ**
- **Found during:** Reading temporal alert dict construction
- **Issue:** Temporal scenarios use `zone_type`/`zone_sensitivity` (not `type`/`sensitivity`) and `fpr` (not `false_positive_rate`)
- **Fix:** Documented the actual field names in Section 5 with a code snippet

## Known Stubs

None. This is a documentation plan — no runtime data flows.

## Threat Flags

None. Documentation-only. No new trust boundaries introduced.

## Self-Check: PASSED

| Check | Result |
|---|---|
| `docs/EVALUATION_PROTOCOL.md` exists | FOUND |
| `17-01-SUMMARY.md` exists | FOUND |
| Commit `ce77ea9` exists | FOUND |
| File line count ≥ 300 | 798 lines |
| Automated verification (15 checks) | All passed |
