---
phase: 09-scoring-and-schema-updates
plan: 01
subsystem: schema
tags: [jsonschema, validation, output-schema, psai-bench]

requires: []
provides:
  - Simplified OUTPUT_SCHEMA accepting minimal non-LLM outputs (alert_id, verdict, confidence only)
  - Confidence field with explicit description: "probability that the verdict is correct"
  - Conditional reasoning length check (only fires when reasoning is present)
  - SUSPICIOUS fraction warning updated to reference Decisiveness metric
  - 4 new/rewritten schema validation tests
affects: [scoring, validation, documentation, evaluators]

tech-stack:
  added: []
  patterns:
    - "Optional field pattern: remove from required[], keep in properties{} for when-present validation"

key-files:
  created: []
  modified:
    - psai_bench/schema.py
    - psai_bench/validation.py
    - tests/test_core.py

key-decisions:
  - "reasoning and processing_time_ms removed from OUTPUT_SCHEMA required list — non-LLM systems should not be penalized for missing these fields"
  - "minLength constraint removed from reasoning property — length validation now handled by validation.py warn, not schema rejection"
  - "confidence description added inline to schema property for self-documenting API contract"

patterns-established:
  - "Optional field pattern: drop from required[], keep in properties for type/format validation when present"

requirements-completed: [SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04]

duration: 15min
completed: 2026-04-13
---

# Phase 09 Plan 01: Scoring and Schema Updates Summary

**OUTPUT_SCHEMA simplified to 3 required fields (alert_id, verdict, confidence), enabling rule-based and heuristic systems to participate without reasoning or timing fields**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-13T00:00:00Z
- **Completed:** 2026-04-13
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- OUTPUT_SCHEMA required list reduced from 5 fields to 3 — reasoning and processing_time_ms are now optional
- minLength:20 constraint removed from reasoning property; validation.py warns on short-but-present reasoning only
- confidence property now carries a description ("probability that the verdict is correct") for self-documenting schema
- SUSPICIOUS fraction warning updated from "penalty per Section 4.5" to "reduces Decisiveness metric" (scoring model changed)
- test_output_missing_reasoning_fails replaced with test_reasoning_optional_passes; 3 additional schema tests added
- Full test suite: 106 tests passing (was 103; net +3 from 4 added, 1 removed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update OUTPUT_SCHEMA and validation.py** - `c04836b` (feat)
2. **Task 2: Update and add schema tests in test_core.py** - `2949597` (test)

## Files Created/Modified

- `psai_bench/schema.py` - OUTPUT_SCHEMA required list and reasoning/confidence property definitions updated
- `psai_bench/validation.py` - Reasoning check made conditional; SUSPICIOUS warning message updated
- `tests/test_core.py` - Old reasoning-fails test replaced; 4 new schema tests added

## Decisions Made

- reasoning and processing_time_ms removed from required list so non-LLM systems (rule-based, heuristic classifiers) can submit valid outputs with only alert_id, verdict, confidence
- minLength:20 removed from schema property to allow reasoning="" or absent reasoning to pass schema validation; length warning is still surfaced in validate_submission() when reasoning is present but short
- SUSPICIOUS warning message changed to reference Decisiveness rather than "penalty per Section 4.5" since the penalty-based scoring formula is being replaced with separate metrics

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- pytest binary used the installed system psai-bench package rather than the worktree source. Switching to `python -m pytest` resolved the import conflict. No code changes required.

## Next Phase Readiness

- Schema is ready for 09-02 (scoring/metrics updates)
- validate_submission() still warns on short reasoning when present — this is correct behavior
- All 106 tests pass; no regressions

## Self-Check

- [x] `psai_bench/schema.py` exists and has required=["alert_id","verdict","confidence"]
- [x] `psai_bench/validation.py` has conditional reasoning check and updated SUSPICIOUS warning
- [x] `tests/test_core.py` has 4 new schema tests, old test replaced
- [x] Commit c04836b exists (Task 1)
- [x] Commit 2949597 exists (Task 2)
- [x] 106 tests passing

## Self-Check: PASSED

---
*Phase: 09-scoring-and-schema-updates*
*Completed: 2026-04-13*
