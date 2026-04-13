---
phase: 13-contradictory-scenarios
plan: 01
subsystem: scenario-generation
tags: [contradictory, generator, distributions, v3]
requirements: [CONTRA-01, CONTRA-02, CONTRA-03, CONTRA-04]

dependency_graph:
  requires:
    - 12-01 (VisualOnlyGenerator pattern — class structure and RNG isolation)
    - 11-02 (schema v3 _meta fields: contradictory, visual_gt_source, metadata_derived_gt, video_derived_gt)
  provides:
    - ContradictoryGenerator class with generate() method
    - CONTRADICTORY_THREAT_DESCRIPTIONS pool (12 entries)
    - CONTRADICTORY_BENIGN_DESCRIPTIONS pool (12 entries)
  affects:
    - psai_bench/distributions.py (new pools)
    - psai_bench/generators.py (new class)

tech_stack:
  added: []
  patterns:
    - Dual GT storage: metadata_derived_gt and video_derived_gt both in _meta; final ground_truth = video_derived_gt
    - GT divergence enforcement: assign_ground_truth_v2 runs only to compute metadata_derived_gt; retry loop (max 10) resamples zone/time if signals accidentally agree; incoherent scenarios skipped
    - RNG isolation: ContradictoryGenerator owns np.random.RandomState(seed) exclusively

key_files:
  created: []
  modified:
    - psai_bench/distributions.py
    - psai_bench/generators.py

decisions:
  - "Zone name sampled from a fixed inline list (not ZONE_NAMES dict) to avoid extra RNG draws that would consume randomness from the zone-type and sensitivity draws already made; keeps RNG stream deterministic"
  - "SUSPICIOUS categories (Arrest, RoadAccidents, Shoplifting) excluded from underreach pool so video_derived_gt is always strictly THREAT for underreach — makes the divergence test deterministic"
  - "sample_device() called then device_fpr overridden post-call to preserve device model/event-count sampling while enforcing the biased FPR profile for GT computation"

metrics:
  duration_minutes: 25
  completed_date: "2026-04-13"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
  tests_before: 180
  tests_after: 180
---

# Phase 13 Plan 01: Contradictory Scenario Generator Summary

ContradictoryGenerator with 12-entry overreach/underreach description pools — dual GT storage where metadata_derived_gt is always computed but video_derived_gt is always the final ground_truth.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add contradictory description pools to distributions.py | 8572cc8 | psai_bench/distributions.py |
| 2 | Implement ContradictoryGenerator in generators.py | 7f539ef | psai_bench/generators.py |

## What Was Built

**distributions.py additions:**

- `CONTRADICTORY_THREAT_DESCRIPTIONS` (12 entries): plausible security-alert text that would make a metadata-only system call THREAT, while the video shows Normal (BENIGN) activity. Examples: fence-disturbance sensor alerts, coordinated-movement analytics, thermal anomalies. No "benign", "normal", "routine", or "authorized" substring anywhere in pool.
- `CONTRADICTORY_BENIGN_DESCRIPTIONS` (12 entries): plausible routine-activity text that would make a metadata-only system call BENIGN or SUSPICIOUS, while the video shows an actual anomaly (THREAT). Examples: scheduled maintenance windows, low-confidence analytics triggers, PTZ repositioning events. No "breach", "intrusion", "forced", "attack", or "weapon" substring anywhere in pool.

**generators.py addition:**

`ContradictoryGenerator` class with `generate(n)` method:
- Isolated RNG (`np.random.RandomState(seed)`) — never shares state with other generators
- Two sub-types: overreach (~50%) and underreach (~50%) selected per-scenario via `rng.random() < 0.50`
- Overreach: `cat = "Normal"`, zone biased to restricted/utility at night/dawn, severity HIGH/CRITICAL
- Underreach: cat from 10 THREAT-only UCF categories, zone biased to parking/interior daytime, severity LOW, badge < 10 min ago
- `assign_ground_truth_v2` called to compute `metadata_derived_gt` from biased signals; if result accidentally equals `video_derived_gt`, resamples zone/time up to 10 times; skips scenario after 10 failed retries
- `_meta.ground_truth` always equals `_meta.video_derived_gt`
- Both `metadata_derived_gt` and `video_derived_gt` stored in `_meta` for audit (Pitfall 13)
- track = "visual_contradictory", severity and description present (distinguishes from visual_only)
- generation_version = "v3", visual_gt_source = "video_category"

## Verification Results

```
ContradictoryGenerator(seed=42).generate(100):
  OK: 100 scenarios
  overreach (BENIGN video): 57
  underreach (THREAT video): 43
  GT divergence: True (all 100)
  Deterministic: True (two runs identical)
  Track: {'visual_contradictory'}
  Existing tests: 180 passed, 0 failed
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. ContradictoryGenerator produces fully wired scenarios. Video URIs are synthetic (intentional design; consistent with VisualOnlyGenerator pattern).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: information_disclosure | psai_bench/generators.py | metadata_derived_gt in _meta could reveal contradictory design if _meta is not stripped before sending alerts to evaluated systems — mitigated per T-13-01 by convention; evaluation protocol must document _meta stripping |

## Self-Check: PASSED

- `psai_bench/distributions.py` exists and exports both pools: VERIFIED
- `psai_bench/generators.py` contains `class ContradictoryGenerator`: VERIFIED
- Commit `8572cc8` exists: VERIFIED
- Commit `7f539ef` exists: VERIFIED
- 180 tests pass: VERIFIED
- GT divergence on 100 scenarios: VERIFIED
- Determinism: VERIFIED
