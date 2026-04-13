---
phase: 06-scenario-generation-rebuild
plan: "01"
subsystem: scenario-generation
tags: [distributions, ground-truth, description-pool, blocklist, v2]
dependency_graph:
  requires: []
  provides: [DESCRIPTION_POOL_AMBIGUOUS, DESCRIPTION_POOL_UNAMBIGUOUS_THREAT, DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN, assign_ground_truth_v2, SITE_CATEGORY_BLOCKLIST-v2]
  affects: [psai_bench/generators.py, psai_bench/distributions.py]
tech_stack:
  added: []
  patterns: [weighted-sum-scoring, pure-function-gt, description-pool-decoupling]
key_files:
  created: []
  modified:
    - psai_bench/distributions.py
    - psai_bench/generators.py
decisions:
  - Severity max score (0.25) is deliberately below GT threshold (0.30) so severity alone cannot determine GT — satisfies SCEN-03
  - Badge access within 10 min = -0.45 (strong benign), 10-30 min = -0.25 (moderate), beyond 30 = 0.0
  - Description pools are static constants, not generated — no injection risk, O(1) memory
metrics:
  duration: "<5 min"
  completed_date: "2026-04-13"
  tasks_completed: 2
  files_modified: 2
requirements_satisfied: [SCEN-01, SCEN-02, SCEN-03, SCEN-06, GT-03]
---

# Phase 06 Plan 01: Shared Description Pools and assign_ground_truth_v2 Summary

**One-liner:** Shared 35-entry description pool (22 ambiguous + 13 unambiguous) and weighted multi-signal `assign_ground_truth_v2` pure function replacing category-hardcoded GT labels.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add shared description pools to distributions.py | e2940f1 | psai_bench/distributions.py |
| 2 | Implement assign_ground_truth_v2 and expand site blocklist | e2940f1 | psai_bench/distributions.py, psai_bench/generators.py |

## What Was Built

### Task 1: Description Pools
Three description pool constants added to `psai_bench/distributions.py`:

- `DESCRIPTION_POOL_AMBIGUOUS`: 22 terse analytics-style descriptions that appear across all GT classes (same description → different GT based on zone/time/device)
- `DESCRIPTION_POOL_UNAMBIGUOUS_THREAT`: 8 clearly threatening descriptions (fire, fence-cutting, gunshot, forced entry, smoke+thermal, perimeter breach, explosion, assault)
- `DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN`: 5 clearly benign descriptions (wind/vegetation motion, spider web, small animal, badge-confirmed crew, camera self-test)
- Total: 35 descriptions; 13/35 = 37% unambiguous (satisfies CONTEXT.md "~30%" constraint)

### Task 2: assign_ground_truth_v2 and blocklist expansion

`assign_ground_truth_v2(zone_type, zone_sensitivity, time_of_day, device_fpr, severity, badge_access_minutes_ago, rng)` implemented as a pure deterministic function:

- Signals: zone_score (base × sensitivity_factor) + time_score + fpr_score + severity_score + badge_score
- GT thresholds: weighted_sum > +0.30 → THREAT, < -0.30 → BENIGN, else SUSPICIOUS
- Returns: (gt_label, weighted_sum, is_ambiguous)
- SCEN-03 satisfied: max severity score = 0.25 < threshold 0.30

`SITE_CATEGORY_BLOCKLIST` in `generators.py` expanded:
- solar: Shoplifting, Robbery, Arrest, RoadAccidents
- substation: Shoplifting, Robbery, Arrest
- industrial: Shoplifting, RoadAccidents
- commercial: RoadAccidents
- campus: RoadAccidents

## Verification Results

```
pools OK: 22+8+5=35
Test 1 PASS: THREAT (restricted+night+low-FPR+HIGH → score=1.188)
Test 2 PASS: BENIGN (parking+day+high-FPR+LOW+badge-2min → score=-1.19)
Test 3 PASS: max severity 0.25 < threshold 0.3
Test 4 PASS: deterministic (same inputs → same output)
Test 5 PASS: SITE_CATEGORY_BLOCKLIST correct
129 tests passed in 8.53s
```

## Deviations from Plan

None — plan executed exactly as written. Both tasks were already implemented in commit `e2940f1` (feat(06): rebuild scenario generation with context-dependent ground truth), which is an ancestor of the current HEAD. All acceptance criteria verified green.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced. Description pools are static constants.

## Self-Check: PASSED

- `psai_bench/distributions.py` exists: FOUND
- `psai_bench/generators.py` exists: FOUND
- Commit `e2940f1` exists: FOUND (ancestor of HEAD)
- All 35 description pool entries importable: VERIFIED
- `assign_ground_truth_v2` importable: VERIFIED
- 129 tests pass: VERIFIED
