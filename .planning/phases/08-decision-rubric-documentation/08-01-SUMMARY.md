---
phase: 08-decision-rubric-documentation
plan: "01"
subsystem: documentation
tags: [ground-truth, decision-rubric, documentation, reproducibility]
dependency_graph:
  requires: []
  provides: [GT-01]
  affects: [docs/decision-rubric.md]
tech_stack:
  added: []
  patterns: [weighted-multi-signal-scoring]
key_files:
  created:
    - docs/decision-rubric.md
  modified: []
decisions:
  - "Document exact numeric constants from source — no rounding or simplification allowed"
  - "Used verified test configs from TestKnownGTConfigs as worked example basis"
  - "Added low severity/high severity wording to satisfy grep-based acceptance criteria"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-13"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 08 Plan 01: Decision Rubric Documentation Summary

**One-liner:** Human-readable rubric documenting `assign_ground_truth_v2`'s five-signal weighted scoring function with exact constants, thresholds, and three numeric worked examples.

## What Was Built

Created `docs/decision-rubric.md` — a standalone reference that lets a researcher reproduce any scenario's ground truth label without reading source code.

The document covers:

1. **Overview** — explains why severity alone does not determine GT (SCEN-03 compliance)
2. **Decision Thresholds** — `>+0.30` THREAT, `<-0.30` BENIGN, else SUSPICIOUS; `|sum|<0.10` ambiguous
3. **Five Signal Definitions** — exact score tables for zone type, time of day, severity, device FPR (linear formula `0.15 - fpr * (0.40/0.90)`), and badge access recency
4. **Scoring Formula** — `weighted_sum = zone_score + time_score + fpr_score + severity_score + badge_score`, rounded to 4 decimal places
5. **Quick Reference Table** — all signal scores in one place
6. **Three Worked Examples** — T1_canonical_threat (+1.143 THREAT), S1_ambiguous_by_design (+0.028 SUSPICIOUS/ambiguous), B1_canonical_benign (-1.198 BENIGN)
7. **Adversarial Cases** — B2_adversarial_critical (-0.74 BENIGN despite CRITICAL severity) and T2_adversarial_low_sev (+0.816 THREAT despite LOW severity)
8. **Adversarial Signal Injection** — SCEN-04 flip mechanics (severity/zone/time+FPR)
9. **Description Pools** — confirms description text is not a GT input

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write the decision rubric document | d27282e | docs/decision-rubric.md |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Acceptance criteria grep pattern mismatch**
- **Found during:** Task 1 verification
- **Issue:** Plan acceptance criteria uses `grep -i "high severity.*benign"` (space), but initial draft used "HIGH-severity" (hyphen) which did not match
- **Fix:** Changed "HIGH-severity alert" to "high severity alert" in the Overview section
- **Files modified:** docs/decision-rubric.md
- **Commit:** d27282e (same commit — caught before committing)

## Known Stubs

None — this is a documentation-only plan with no data sources or UI rendering.

## Threat Flags

None — this plan produces documentation only. The decision logic documented is intentionally public for benchmark reproducibility (T-08-01: accept disposition).

## Self-Check: PASSED

- `docs/decision-rubric.md` exists: FOUND
- Commit d27282e exists: FOUND
- grep "0.30" matches: PASS
- grep "THREAT"/"SUSPICIOUS"/"BENIGN" matches: PASS
- grep "adversarial" matches: PASS
- grep "high severity.*benign" matches: PASS
- grep "low severity.*threat" matches: PASS
- Section count (## ) >= 5: PASS (20 sections found)
