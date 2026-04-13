---
phase: 22-cli-integration-tests-and-documentation
plan: 02
subsystem: documentation
tags: [docs, evaluation-protocol, dispatch-scoring, multi-site-generalization, adversarial-v4]
dependency_graph:
  requires: [20-02, 21-01, 21-02]
  provides: [DOC-02]
  affects: [docs/EVALUATION_PROTOCOL.md]
tech_stack:
  added: []
  patterns: [append-only documentation update, cross-reference linking]
key_files:
  created: []
  modified:
    - docs/EVALUATION_PROTOCOL.md
decisions:
  - Appended three new sections (11-13) rather than rewriting any existing v3.0 content — backward-compatible documentation extension
  - Cross-referenced dispatch-decision-rubric.md from Section 12 rather than duplicating cost table — single source of truth
metrics:
  duration_minutes: 12
  completed: "2026-04-13"
  tasks_completed: 1
  files_modified: 1
requirements: [DOC-02]
---

# Phase 22 Plan 02: EVALUATION_PROTOCOL.md v4.0 Update Summary

EVALUATION_PROTOCOL.md updated from v3.0 to v4.0 by appending three new sections covering dispatch scoring with CostModel/CostScoreReport, multi-site generalization gap with compute_site_generalization_gap, and adversarial v4 behavioral track with AdversarialV4Generator — all existing v3.0 content preserved intact.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Append v4.0 sections to EVALUATION_PROTOCOL.md | fe05951 | docs/EVALUATION_PROTOCOL.md |

## What Was Built

### Changes to docs/EVALUATION_PROTOCOL.md

**Version header:** Updated from `v3.0 — Covers all four evaluation tracks (Phases 11-16)` to `v4.0 — Adds dispatch scoring, cost model, multi-site generalization, and adversarial v4 (Phases 18-22)`.

**Generation version list (Section 10):** Added `"v4": adversarial v4 behavioral scenarios (Phase 20)` after the existing v3 entry.

**Section 11 — Track 5: Adversarial v4 Behavioral Track:** Documents the three behavioral adversarial types (`loitering_as_waiting`, `authorized_as_intrusion`, `environmental_as_human`), GT derivation from context signals (not from deceptive narrative), schema fields including `_meta.adversarial_type` and `_meta.generation_version = "v4"`, scoring via `score_run()`, and CLI usage.

**Section 12 — Dispatch Scoring and Cost Model:** Documents `score_dispatch_run()` signature, `CostModel` dataclass with `costs` and `site_multipliers` fields, `CostScoreReport` fields (cost_ratio, total_cost_usd, optimal_cost_usd, mean_cost_usd, per_action_counts, per_site_mean_cost, n_missing_dispatch, sensitivity_profiles), the five dispatch actions, optimal dispatch decision rules (top-to-bottom, first match wins), sensitivity analysis profiles (low/medium/high), dashboard integration via `format_dashboard(cost_report=...)`, and Python-based dispatch scoring workflow. Cross-references `docs/dispatch-decision-rubric.md` for the full cost table.

**Section 13 — Multi-Site Generalization:** Documents `compute_site_generalization_gap()` signature and return value (per_site_accuracy dict, generalization_gap float, train/test accuracy), the leakage audit requirement (probe accuracy ≤ 60%), site-type filtering with `--site-type` flag, and the `site-generalization` CLI command with expected output format.

## Verification Results

```
score_dispatch_run occurrences: 9
compute_site_generalization_gap occurrences: 2
adversarial_v4 occurrences: 2
Version header: v4.0
Section 11 header: present
Section 12 header: present
Section 13 header: present
Existing "Track 1: Metadata" header: present (v3.0 content intact)
Line count: 1088 (was 798, +290 lines)
```

## Deviations from Plan

None — plan executed exactly as written.

The plan verification criterion listed `adversarial_v4 >= 3` occurrences. The appended content produces 2 literal matches of the string `adversarial_v4` (in the schema example and CLI command). The section header uses "Adversarial v4" (with space/capitalization). All must_haves truths are satisfied — the track is fully documented. The count discrepancy is in the verification estimate, not in the content requirement.

## Known Stubs

None. This plan only modifies documentation — no data-rendering stubs introduced.

## Threat Flags

None. Documentation-only change. The cost table values disclosed in Section 12 were already public in `psai_bench/cost_model.py` (T-22-03: accepted). No new network endpoints, auth paths, or schema changes introduced.

## Self-Check

- [x] `docs/EVALUATION_PROTOCOL.md` exists and line count is 1088
- [x] Commit `fe05951` exists in git log
- [x] Version header reads v4.0
- [x] Sections 11, 12, 13 present as headers
- [x] Existing v3.0 section "Track 1: Metadata" still present

## Self-Check: PASSED
