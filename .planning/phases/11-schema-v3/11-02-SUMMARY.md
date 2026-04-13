---
phase: 11-schema-v3
plan: "02"
subsystem: schema
tags: [jsonschema, validation, cli, track-enum, v3, backward-compat]

# Dependency graph
requires:
  - phase: 11-01
    provides: "Seed-42 regression guard (8 pinned tests) — confirmed passing before any schema touch"
provides:
  - "Extended ALERT_SCHEMA with visual_only, visual_contradictory, temporal track values"
  - "severity and description removed from ALERT_SCHEMA required array"
  - "keyframe_uris added to visual_data properties"
  - "_META_SCHEMA_V2 with v3 fields: visual_gt_source, contradictory, sequence_id, sequence_position, sequence_length"
  - "Track-aware validation in validate_scenarios: uri/contradictory/sequence_id enforcement"
  - "None-safe description guard in validate_scenarios"
  - "CLI --track extended with stub errors for visual_only/visual_contradictory/temporal"
  - "21-test regression suite in test_schema_v3.py encoding schema v3 behavioral contract"
affects:
  - "11-03 onwards: all generator phases can now emit new track values"
  - "Phase 12 (visual_only generator): schema ready, CLI stub in place"
  - "Phase 13 (visual_contradictory generator): schema ready, CLI stub in place"
  - "Phase 14 (temporal generator): schema ready, CLI stub in place"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Track-aware validation: per-track field requirements enforced in validate_scenarios after GT distribution check"
    - "Stub error pattern: new CLI tracks raise UsageError with phase reference, not silent empty file"
    - "None-safe string guard: (s.get('description') or '').lower() handles absent and None"

key-files:
  created:
    - tests/test_schema_v3.py
    - tests/test_task1_tdd.py
  modified:
    - psai_bench/schema.py
    - psai_bench/validation.py
    - psai_bench/cli.py
    - tests/test_core.py

key-decisions:
  - "severity and description removed from ALERT_SCHEMA required — visual_only scenarios never have them, and removing from required never invalidates existing v2 scenarios"
  - "Track-aware validation inserted before track consistency check in validate_scenarios, capped at 5 errors to prevent flood"
  - "CLI stub branches raise UsageError immediately (no scenarios variable reached), so no uninitialized variable risk"
  - "test_core.py test_missing_required_field_fails updated to delete zone (still required) instead of severity (now optional) — auto-fixed as Rule 1 bug"

patterns-established:
  - "Schema extension pattern: additive-only changes (new enum values, new optional properties, removal from required) never break existing scenarios"
  - "TDD for schema changes: write 6 minimal RED tests targeting specific behaviors, implement, verify GREEN, then create comprehensive regression file"

requirements-completed: [INFRA-01, INFRA-02, INFRA-03, TEST-01]

# Metrics
duration: 20min
completed: 2026-04-13
---

# Phase 11 Plan 02: Schema v3 Extension Summary

**ALERT_SCHEMA extended with 3 new tracks, relaxed required array, keyframe_uris, _META_SCHEMA_V2 with 5 v3 fields, track-aware validation with uri/contradictory/sequence_id enforcement, and CLI stub errors — all 168 tests pass**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-04-13T18:20:00Z
- **Completed:** 2026-04-13T18:45:00Z
- **Tasks:** 2
- **Files modified:** 6 (including test_core.py fix)

## Accomplishments

- Extended `ALERT_SCHEMA` track enum from 3 values to 6 (`visual_only`, `visual_contradictory`, `temporal` added)
- Removed `severity` and `description` from `ALERT_SCHEMA` required array — existing v2 scenarios still validate (backward compat confirmed by 21 regression tests)
- Added `keyframe_uris` to `visual_data` for frame-extraction baseline (Phase 17)
- Added 5 v3 fields to `_META_SCHEMA_V2`: `visual_gt_source`, `contradictory`, `sequence_id`, `sequence_position`, `sequence_length`; extended `generation_version` enum to include `"v3"`
- Fixed None-safe description bug in `validate_scenarios` (was `s.get("description", "").lower()` — crashes if description=None; now `(s.get("description") or "").lower()`)
- Added track-aware validation block with per-track enforcement and 5-error cap
- Extended CLI `--track` choice with 3 new values; stub branches raise informative `UsageError` referencing the implementing phase
- Created `tests/test_schema_v3.py` with 21 tests across 4 classes encoding the full behavioral contract
- All 168 tests pass (141 original + 6 TDD + 21 schema_v3 tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend ALERT_SCHEMA, _META_SCHEMA_V2, fix validation.py None-guard, extend CLI track enum** - `5f66394` (feat)
2. **Task 2: Add schema validation tests for v3 fields and track-aware validation** - `2add75f` (test)

## Files Created/Modified

- `psai_bench/schema.py` — ALERT_SCHEMA track enum extended (6 values), severity/description removed from required, keyframe_uris added to visual_data, _META_SCHEMA_V2 extended with 5 v3 fields and generation_version enum
- `psai_bench/validation.py` — None-safe description guard fixed; track-aware validation block added (28 lines)
- `psai_bench/cli.py` — --track extended to 6 choices; 3 elif stub branches raising UsageError
- `tests/test_core.py` — test_missing_required_field_fails updated to delete zone instead of severity (auto-fix: Rule 1)
- `tests/test_schema_v3.py` — 21-test comprehensive regression suite (4 classes)
- `tests/test_task1_tdd.py` — 6-test TDD RED/GREEN driver for Task 1 behaviors

## Decisions Made

- `severity` and `description` removed from required (not made track-conditional) — simplest approach that never invalidates v2 scenarios; track-aware validation enforces semantic requirements at a higher level
- CLI stubs `raise click.UsageError` before the `version_suffix` line is reached — avoids uninitialized `scenarios` variable, gives informative message referencing the implementing phase
- `generation_version` enum extended from `{"type": "string"}` to `{"enum": ["v1", "v2", "v3"]}` — adds type safety without breaking existing v1/v2 scenarios

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_core.py test_missing_required_field_fails after schema change**
- **Found during:** Task 1 (full suite run after implementation)
- **Issue:** `test_missing_required_field_fails` deleted `severity` expecting `ValidationError`. After removing severity from required, the test no longer raised — so 1 test failed.
- **Fix:** Changed the test to delete `zone` (which remains required for all tracks) instead of `severity`. Added comment explaining why.
- **Files modified:** `tests/test_core.py`
- **Verification:** Full suite 168/168 passing
- **Committed in:** `5f66394` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug in existing test)
**Impact on plan:** The fix was necessary — the test was validating old schema behavior that we intentionally changed. Updating it is the correct response, not reverting the schema change.

## Issues Encountered

- Worktree base was on wrong commit (`a9ae81c`) instead of required `9ae051e0` (which has the Phase 11-01 seed regression tests). Reset with `git reset --hard 9ae051e0...` before execution. Identical to the initialization correction in 11-01.

## Threat Surface Scan

The track-aware validation in `validate_scenarios` (T-11-04, T-11-05 from threat model) was implemented correctly:
- None-safe description guard prevents AttributeError crash injection via None-description scenarios (T-11-04 mitigated)
- Track error output capped at 5 + count summary — cannot produce unbounded output from large scenario files (T-11-05 accepted/controlled)
- ALERT_SCHEMA enum rejects unknown track values via jsonschema validate_alert() (T-11-03 mitigated)

No new trust boundaries or network endpoints introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Schema is the foundation for all Phase 12-17 work. All schema changes are in place.
- Phase 12 (visual_only generator): schema accepts the track, CLI has stub error pointing to Phase 12, validation enforces uri requirement
- Phase 13 (visual_contradictory): schema and validation ready
- Phase 14 (temporal): schema and validation ready
- All 141 original tests + 8 seed regression tests still passing — seed-42 guard confirmed

## Self-Check

- [x] `tests/test_schema_v3.py` exists with 21 tests
- [x] `tests/test_task1_tdd.py` exists with 6 tests
- [x] Commit `5f66394` exists (Task 1)
- [x] Commit `2add75f` exists (Task 2)
- [x] Full suite: 168 tests passing
- [x] `visual_only` in ALERT_SCHEMA track enum
- [x] `severity` not in ALERT_SCHEMA required
- [x] `visual_gt_source` in _META_SCHEMA_V2
- [x] `(s.get("description") or "").lower()` in validation.py
- [x] CLI --track visual_only raises UsageError with "Phase 12"

---
*Phase: 11-schema-v3*
*Completed: 2026-04-13*
