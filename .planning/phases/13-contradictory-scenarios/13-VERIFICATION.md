---
phase: 13-contradictory-scenarios
verified: 2026-04-13T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 13: Contradictory Scenarios Verification Report

**Phase Goal:** Users can generate contradictory scenarios where metadata and video content deliberately disagree and GT always follows the video content label
**Verified:** 2026-04-13
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `generate --track visual_contradictory` produces scenarios with `_meta.contradictory=True` | VERIFIED | CLI produces 20 scenarios; all have `_meta.contradictory=True`. `psai-bench generate --track visual_contradictory --n 20` exits 0, writes `visual_contradictory_all_seed42.json`. |
| 2 | Both overreach and underreach sub-types appear | VERIFIED | 100-scenario batch: 57 overreach (video=BENIGN), 43 underreach (video=THREAT). `test_both_subtypes_present` confirms in 200-scenario batch. |
| 3 | Automated test asserts `metadata_derived_gt != video_derived_gt` for all scenarios | VERIFIED | `test_gt_divergence` in `tests/test_contradictory.py` passes across all 200 fixture scenarios. Full generator verify confirms on 100 scenarios. |
| 4 | Contradictory description pools are plausible-but-wrong | VERIFIED | Both `CONTRADICTORY_THREAT_DESCRIPTIONS` and `CONTRADICTORY_BENIGN_DESCRIPTIONS` have 12 entries each (>= 8 required). Min entry length 75 chars. No forbidden words in either pool (checked: "benign", "normal", "routine", "authorized" in threat pool; "breach", "intrusion", "forced", "attack", "weapon" in benign pool). |
| 5 | GT always follows video content label | VERIFIED | All scenarios: `_meta.ground_truth == _meta.video_derived_gt`. `test_ground_truth_follows_video` passes. Generator code at line 919: `"ground_truth": video_derived_gt`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `psai_bench/distributions.py` | CONTRADICTORY_THREAT_DESCRIPTIONS and CONTRADICTORY_BENIGN_DESCRIPTIONS pools | VERIFIED | Both exported at line 348 and 368. 12 entries each. All entries >= 75 chars. |
| `psai_bench/generators.py` | ContradictoryGenerator class with generate() method | VERIFIED | Class at line 753. Implements dual GT storage, overreach/underreach sub-types, RNG isolation. |
| `tests/conftest.py` | `contradictory_scenarios_200` session-scoped fixture | VERIFIED | Fixture present at correct scope, imports ContradictoryGenerator(seed=42).generate(200). |
| `tests/test_contradictory.py` | Full test suite for CONTRA-01 through CONTRA-04 and TEST-03 | VERIFIED | 13 tests, all passing. Includes `test_gt_divergence` and `test_both_subtypes_present`. |
| `psai_bench/cli.py` | `visual_contradictory` track wired to ContradictoryGenerator | VERIFIED | Lines 82-86: elif branch calls ContradictoryGenerator(seed=seed).generate(count). UsageError stub fully removed for this track. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ContradictoryGenerator.generate()` | `assign_ground_truth_v2` | compute metadata_derived_gt only — never as final GT | VERIFIED | `assign_ground_truth_v2` called at line 833 in retry loop. Result stored as `metadata_derived_gt` only. `ground_truth` set from `video_derived_gt` at line 919. |
| `_meta.ground_truth` | `_meta.video_derived_gt` | always equal — video overrides metadata | VERIFIED | Code: `"ground_truth": video_derived_gt` at line 919. Generator assertion confirmed on 100 scenarios. |
| `tests/conftest.py` | `psai_bench/generators.ContradictoryGenerator` | session-scoped fixture import | VERIFIED | Fixture imports ContradictoryGenerator by name, returns 200 scenarios. |
| `psai_bench/cli.py` | `ContradictoryGenerator.generate()` | `elif track == 'visual_contradictory'` branch | VERIFIED | Branch at lines 82-86, lazy import pattern matching visual_only convention. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `ContradictoryGenerator.generate()` | `video_derived_gt` | `UCF_CATEGORY_MAP[cat]["ground_truth"]` — deterministic from category selection | Yes — drawn from hardcoded category map, not hardcoded empty | FLOWING |
| `ContradictoryGenerator.generate()` | `metadata_derived_gt` | `assign_ground_truth_v2()` called with biased signals | Yes — computed via scoring function with real signal weights | FLOWING |
| `visual_data.uri` | `cat`, `idx` | `f"ucf-crime/test/{cat}/{idx:05d}.mp4"` | Yes — synthetic URI encoding category and index; consistent with VisualOnlyGenerator pattern (intentional design) | FLOWING |

Note: `visual_data.uri` values are synthetic (no actual video files). This is the established benchmark design pattern for all generators — real video files are not stored in the repo; URIs are identifiers for external retrieval.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Generator produces 100 scenarios with all _meta invariants | `ContradictoryGenerator(seed=42).generate(100)` | 100 scenarios, overreach=57, underreach=43, GT divergence=True, determinism=True | PASS |
| Description pools meet size and content requirements | Import + len + min-len + forbidden-word check | Threat: 12 entries, min 79 chars, no forbidden words. Benign: 12 entries, min 75 chars, no forbidden words. | PASS |
| CLI produces scenario file for `visual_contradictory` track | `psai-bench generate --track visual_contradictory --n 20` | Exits 0. Writes JSON with 20 scenarios, all contradictory=True, GT divergence=True. | PASS |
| Full test suite runs without regression | `pytest tests/ -x -q` | 193 passed in 13.61s (was 180 before phase 13; 13 new tests added). | PASS |
| `test_contradictory.py` all 13 tests pass | `pytest tests/test_contradictory.py -v` | 13/13 passed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CONTRA-01 | 13-01, 13-02 | ContradictoryGenerator produces scenarios where metadata and video content disagree | SATISFIED | Generator enforces divergence via retry loop; test_all_scenarios_have_contradictory_flag passes; severity and description fields present as misleading metadata. |
| CONTRA-02 | 13-01, 13-02 | Two sub-types: overreach (metadata=THREAT, video=BENIGN) and underreach (metadata=BENIGN, video=THREAT) | SATISFIED | 57 overreach + 43 underreach in 100-scenario batch; test_both_subtypes_present passes. |
| CONTRA-03 | 13-01, 13-02 | GT always follows video content; `_meta.contradictory=true` flag present | SATISFIED | `_meta.ground_truth == _meta.video_derived_gt` enforced in generator; test_ground_truth_follows_video passes. |
| CONTRA-04 | 13-01 | Contradictory description pools added to distributions.py | SATISFIED | Both pools in distributions.py with 12 entries each; plausible-but-wrong content verified. |
| TEST-03 | 13-02 | Contradictory scenario GT always follows video label (automated verification) | SATISFIED | test_gt_divergence asserts metadata_derived_gt != video_derived_gt for all 200 fixture scenarios; 193 total tests pass. |

### Anti-Patterns Found

No anti-patterns found in the phase 13 modified files. The `UsageError` remaining in cli.py is for the `temporal` track (Phase 14) — expected and correct.

### Human Verification Required

None. All must-haves are programmatically verifiable and verified.

### Gaps Summary

No gaps. All 5 roadmap success criteria are satisfied, all 5 requirements are covered, all key artifacts exist and are substantively implemented, all key links are wired, and behavioral spot-checks confirm end-to-end operation.

---

_Verified: 2026-04-13_
_Verifier: Claude (gsd-verifier)_
