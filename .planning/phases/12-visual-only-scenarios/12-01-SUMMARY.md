---
phase: 12-visual-only-scenarios
plan: "01"
subsystem: testing
tags: [generators, visual-only, ucf-crime, leakage, tdd, scikit-learn]

requires:
  - phase: 11-schema-v3-extension
    provides: v3 ALERT_SCHEMA with track enum including visual_only and relaxed required fields (severity/description optional)

provides:
  - VisualOnlyGenerator class in psai_bench/generators.py with isolated RNG, UCF Crime GT derivation, and v3 _meta fields
  - CLI visual_only track wired to VisualOnlyGenerator (replaces UsageError stub)
  - tests/test_visual_only.py with 12 tests covering schema, GT correctness, determinism, and leakage stumps
  - visual_only_scenarios_200 session fixture in tests/conftest.py

affects: [13-visual-contradictory, 14-temporal-sequences, evaluation-protocol]

tech-stack:
  added: []
  patterns:
    - "VisualOnlyGenerator owns isolated np.random.RandomState(seed) — never shares RNG with other generators (Pitfall 4)"
    - "GT derived from UCF_CATEGORY_MAP[cat]['ground_truth'] directly (video_category source), not signal weighting"
    - "Severity and description omitted entirely from dict (not set to null) for visual-only track"
    - "Shared distribution pools (sample_zone, sample_device, sample_site_type) across all tracks for leakage safety"
    - "Decision stump (max_depth=1) on training data as worst-case leakage upper bound"

key-files:
  created:
    - tests/test_visual_only.py
  modified:
    - psai_bench/generators.py
    - psai_bench/cli.py
    - tests/conftest.py
    - tests/test_task1_tdd.py

key-decisions:
  - "VisualOnlyGenerator does not subclass MetadataGenerator — built directly to own isolated RNG stream"
  - "Synthetic URI format ucf-crime/test/{cat}/{i:05d}.mp4 encodes category (intentional T-12-01 design, not sent to evaluated systems)"
  - "keyframe_uris: [] included in visual_data to establish v3 schema precedent even though no keyframes generated yet"
  - "Normal category weighted at 4.0 (same as MetadataGenerator) to avoid class imbalance leakage between tracks"

patterns-established:
  - "TDD RED commit before implementation: failing import test committed first"
  - "Stump leakage tests use training accuracy on 200 scenarios as worst-case upper bound"
  - "Visual-only _meta block includes visual_gt_source, adversarial, ambiguity_flag for v3 parity"

requirements-completed: [VIS-01, VIS-02, VIS-03, VIS-04, TEST-02]

duration: 18min
completed: 2026-04-13
---

# Phase 12 Plan 01: Visual-Only Scenarios Summary

**VisualOnlyGenerator class with UCF Crime video-category GT derivation, isolated RNG, absent severity/description, and leakage-safe shared distribution pools — 180 tests passing**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-04-13T00:00:00Z
- **Completed:** 2026-04-13T00:18:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- VisualOnlyGenerator produces deterministic visual-only scenarios where GT comes directly from UCF Crime category labels (not metadata signal weighting), with severity and description absent from the dict entirely
- CLI visual_only track wired — `psai-bench generate --track visual_only --n 100` produces valid JSON with visual_data.uri set and _meta.visual_gt_source == "video_category"
- 12 new tests in test_visual_only.py covering schema validation, GT correctness, determinism, visual data structure, and three leakage stump tests (zone_type, time_of_day, device_fpr — all below 70%)
- All 168 pre-existing tests continue to pass (total now 180)

## Task Commits

Each task was committed atomically:

1. **TDD RED** - `98ffeb5` (test: failing TDD stub for VisualOnlyGenerator import and contract)
2. **Task 1: Implement VisualOnlyGenerator and wire CLI** - `16e40cd` (feat)
3. **Chore: Remove TDD RED stub** - `68e18f5` (chore)
4. **Task 2: Add test fixtures and visual-only test suite** - `5743ff6` (test)

## Files Created/Modified

- `psai_bench/generators.py` — Added VisualOnlyGenerator class (100 lines) after MultiSensorGenerator; isolated RNG, UCF Crime GT derivation, synthetic URIs
- `psai_bench/cli.py` — Replaced visual_only UsageError stub with VisualOnlyGenerator call; count defaults to 500
- `tests/conftest.py` — Added visual_only_scenarios_200 session-scoped fixture
- `tests/test_visual_only.py` — New: TestVisualOnlyScenarios (9 tests) + TestVisualOnlyLeakage (3 stump tests)
- `tests/test_task1_tdd.py` — Updated stale test6 that expected UsageError; now tests successful CLI execution

## Decisions Made

- Used isolated `self.rng = np.random.RandomState(seed)` — never shared with other generators. This is the critical Pitfall 4 isolation required for determinism guarantees.
- GT derived from `UCF_CATEGORY_MAP[cat]["ground_truth"]` directly, not from `assign_ground_truth_v2`. The video_category source is the defining characteristic of the visual-only track.
- `keyframe_uris: []` included in visual_data — establishes the v3 schema precedent even though no keyframes are extracted yet (Phase 14 will populate them).
- Category weights identical to MetadataGenerator (`[1.0] * 13 + [4.0]` for Normal) — prevents class imbalance leakage between tracks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated stale test6 that expected visual_only CLI to raise UsageError**
- **Found during:** Task 1 (implement VisualOnlyGenerator and wire CLI)
- **Issue:** `test_task1_tdd.py::TestTask1TDD::test6_visual_only_track_cli_raises_usage_error` expected a `click.UsageError` from the visual_only CLI track — this was correct when the track was a stub, but becomes a failing test after we wire the generator.
- **Fix:** Updated test6 to verify successful CLI execution: exit_code 0, output file written, 5 scenarios with correct track value.
- **Files modified:** `tests/test_task1_tdd.py`
- **Verification:** `pytest tests/test_task1_tdd.py` — 6/6 pass.
- **Committed in:** `16e40cd` (Task 1 commit)

**2. [Note] Plan says "--count 100" but CLI option is "--n"**
- **Found during:** Pre-execution review (advisor call)
- **Issue:** The plan's must_have truth and verification commands reference `--count 100 / --count 50`, but the actual CLI option is `--n`. This is a plan documentation error, not a code error.
- **Fix:** Used `--n` in all verification commands. No code changes needed.
- **Impact:** Zero — implementation correct, only plan wording was off.

---

**Total deviations:** 1 auto-fixed (Rule 1 stale test), 1 documentation note (plan used wrong flag name)
**Impact on plan:** Stale test update necessary for correctness; no scope creep. CLI flag discrepancy had no runtime impact.

## Issues Encountered

- Worktree branch was at `a9ae81c` (Phase 5) instead of `5704c1f` (Phase 12 HEAD). Required `git reset --hard master` to advance to the correct base before execution could begin.
- Baseline test count is 168 (not 133 as the plan stated) — Phase 11 added test_schema_v3.py. Used 168 as the actual baseline throughout.

## Known Stubs

None — `keyframe_uris: []` is intentionally empty per T-12-01 design note. The field is present in the schema and populated as an empty list; actual keyframe extraction is Phase 14 scope.

## Threat Flags

No new threat surface introduced beyond what is documented in the plan's threat model (T-12-01, T-12-02, T-12-03 all addressed in implementation).

## Next Phase Readiness

- VisualOnlyGenerator is ready for Phase 13 (visual_contradictory track) to build on
- The `visual_only` track is fully wired in CLI and schema — Phase 14 temporal track can follow the same pattern
- Leakage stump tests establish the reusable `_stump_accuracy` helper pattern for future visual track tests

---
*Phase: 12-visual-only-scenarios*
*Completed: 2026-04-13*
