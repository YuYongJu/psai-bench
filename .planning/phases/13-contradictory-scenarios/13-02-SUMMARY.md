---
phase: 13-contradictory-scenarios
plan: "02"
subsystem: tests-and-cli
tags: [testing, cli, contradictory-scenarios, phase-13]
dependency_graph:
  requires: [13-01]
  provides: [contradictory-test-suite, visual_contradictory-cli-track]
  affects: [tests/conftest.py, tests/test_contradictory.py, psai_bench/cli.py]
tech_stack:
  added: []
  patterns: [session-scoped-fixture, pytest-class-tests, lazy-import-cli]
key_files:
  created: [tests/test_contradictory.py]
  modified: [tests/conftest.py, psai_bench/cli.py]
decisions:
  - "Test class named TestContradictoryScenarios following test_visual_only.py pattern — single class covers all functional + schema assertions"
  - "13 tests written (plan required >= 12) — determinism test added standalone, not fixture-dependent"
  - "CLI wiring uses lazy import (from psai_bench.generators import ContradictoryGenerator inside elif) matching visual_only branch convention"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-13"
  tasks_completed: 2
  files_modified: 3
requirements: [CONTRA-01, CONTRA-02, CONTRA-03, TEST-03]
---

# Phase 13 Plan 02: Tests and CLI Wiring Summary

Tests and CLI wiring for ContradictoryGenerator — 13-test suite covering CONTRA-01 through CONTRA-04 and TEST-03, plus `visual_contradictory` track wired in CLI replacing the UsageError stub.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add contradictory_scenarios_200 fixture and write test suite | cc9c5d0 | tests/conftest.py, tests/test_contradictory.py |
| 2 | Wire ContradictoryGenerator into CLI | 916b6fe | psai_bench/cli.py |

## What Was Built

**tests/conftest.py** — Extended with `contradictory_scenarios_200` session-scoped fixture importing `ContradictoryGenerator(seed=42).generate(200)`. Follows the existing `visual_only_scenarios_200` pattern exactly.

**tests/test_contradictory.py** — 13-test suite in `TestContradictoryScenarios` class:
- `test_gt_divergence` — asserts `metadata_derived_gt != video_derived_gt` for every scenario (TEST-03 core requirement)
- `test_both_subtypes_present` — asserts both overreach (video=BENIGN) and underreach (video=THREAT) appear (CONTRA-02)
- `test_ground_truth_follows_video` — asserts `ground_truth == video_derived_gt`, not metadata_derived_gt (CONTRA-03)
- `test_all_scenarios_have_contradictory_flag` — CONTRA-01 flag check
- `test_overreach_descriptions_are_threat_sounding` — severity in (HIGH, CRITICAL) for overreach
- `test_underreach_descriptions_are_benign_sounding` — severity == LOW for underreach
- Plus: track, schema, severity+description presence, visual_data uri, visual_gt_source, generation_version, determinism

**psai_bench/cli.py** — `visual_contradictory` elif branch replaced: UsageError stub removed, `ContradictoryGenerator(seed=seed).generate(count)` wired in. Output filename, JSON dump, and distribution printout apply automatically from the shared code below the elif chain.

## Verification Results

```
pytest tests/ -x -q: 193 passed
psai-bench generate --track visual_contradictory --n 20:
  Count: 20, All contradictory: True, GT divergence: True
  Overreach: 14, Underreach: 6
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced. Test output to /tmp is accepted per T-13-05.

## Self-Check: PASSED

- tests/conftest.py exists and contains `contradictory_scenarios_200`: FOUND
- tests/test_contradictory.py exists and contains `test_gt_divergence`: FOUND
- psai_bench/cli.py contains `ContradictoryGenerator`: FOUND
- Commit cc9c5d0 exists: FOUND
- Commit 916b6fe exists: FOUND
- All 193 tests pass: CONFIRMED
