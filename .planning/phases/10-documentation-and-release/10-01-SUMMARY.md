---
phase: 10-documentation-and-release
plan: "01"
subsystem: documentation
tags: [readme, byos, v2.0, documentation]
dependency_graph:
  requires: []
  provides: [updated-readme]
  affects: [first-impression, researcher-onboarding]
tech_stack:
  added: []
  patterns: [byos-workflow, reference-implementation-framing]
key_files:
  created: []
  modified:
    - README.md
decisions:
  - "Removed 0.580 from Results explanation text to satisfy acceptance criteria (grep count = 0); context is preserved by stating v1.0 results had single-field leakage"
  - "Used --version v2 flag in generate examples and adjusted filename to metadata_ucf_seed42_v2.json to match actual CLI output path"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-13"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 1
---

# Phase 10 Plan 01: README Rewrite for v2.0 BYOS Workflow Summary

README rewritten to lead with the Bring Your Own System 3-step workflow, reposition built-in evaluators as reference implementations, link the decision rubric, remove invalid v1.0 results, and add honest Known Limitations.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Rewrite README.md for v2.0 BYOS workflow | 1988075 |

## What Was Built

The README was rewritten from scratch to reflect v2.0's BYOS-first design philosophy:

- **BYOS workflow leads** — 3-step `generate` / run-your-system / `score` workflow appears within the first screen of content (lines 9–26)
- **Built-in evaluators repositioned** — GPT-4o/Claude/Gemini evaluators are now described as reference implementations, not the primary path
- **Decision rubric linked** — `docs/decision-rubric.md` linked from the "What PSAI-Bench Tests" section with accurate anchor text
- **v1.0 results removed** — Results section replaced with an explanation of why v1.0 results are not meaningful under v2.0 context-dependent ground truth
- **Known Limitations added** — 5 honest limitations: 3-class triage only, no video in v2.0, single-annotator GT, synthetic scenarios, no temporal context
- **Metrics table updated** — Aggregate Score and SUSPICIOUS penalty replaced with Decisiveness metric
- **Citation updated** — year corrected to 2026, note field updated to reflect BYOS benchmark design

## Deviations from Plan

### Minor Adjustments

**1. [Rule 1 - Bug] Removed 0.580 from Results explanation text**
- **Found during:** Acceptance criteria verification
- **Issue:** The plan's sample Results text included "Aggregate=0.580" in the explanation paragraph, but the acceptance criteria requires `grep -c "0.580" README.md` to return 0 (verifying old results table is gone)
- **Fix:** Removed the specific metric values from the explanation text. The key message (v1.0 results invalid due to leakage) is fully preserved
- **Files modified:** README.md
- **Commit:** 1988075 (same commit, caught before committing)

**2. [Rule 2 - Accuracy] Added --version v2 flag to generate examples**
- **Found during:** Reading cli.py before writing**
- **Issue:** The plan's example command `psai-bench generate ... --n 3000 --seed 42` defaults to `--version v1`, which produces v1.0 scenarios with single-field leakage. The BYOS workflow should use v2 scenarios
- **Fix:** Added `--version v2` to both generate examples and adjusted the output filename to `metadata_ucf_seed42_v2.json` to match actual CLI behavior (cli.py line 71)
- **Files modified:** README.md
- **Commit:** 1988075

## Verification Results

All acceptance criteria passed:

```
grep -c "Bring Your Own System" README.md  → 2
grep -c "reference implementation" README.md  → 2
grep -c "decision-rubric.md" README.md  → 2
grep -c "Known Limitations" README.md  → 1
grep -c "0.580" README.md  → 0 (PASS)
grep -c "Severity Heuristic" README.md  → 0 (PASS)
grep -c "Decisiveness" README.md  → 2
grep -c "No video track" README.md  → 1
grep -c "Single-annotator" README.md  → 1
grep -c "3-class triage" README.md  → 1
BYOS workflow visible within first 30 lines  → Line 9 (PASS)
```

## Known Stubs

None. All sections contain real content. No placeholder text or hardcoded empty values.

## Threat Flags

None. Documentation-only change — no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

- README.md exists and contains all required sections
- Commit 1988075 exists in git log
- All grep acceptance criteria verified above
