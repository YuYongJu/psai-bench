# Phase 11: Schema v3 - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

The schema supports all three new tracks with backward-compatible field definitions and the seed-42 regression is pinned before any generator touches the RNG stream.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key research constraints:
- Track enum extends to include `visual_only`, `visual_contradictory`, `temporal`
- `severity` and `description` move from schema-level required to track-specific validation
- `_meta` v3 fields: `visual_gt_source`, `contradictory`, `sequence_id`, `sequence_position`
- Seed-42 regression hash must be pinned BEFORE any generator changes (pitfalls research)
- score_run() must NOT be modified
- Existing v2.0 scenarios must still validate against updated schema

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- `psai_bench/schema.py` — ALERT_SCHEMA, _META_SCHEMA_V2, OUTPUT_SCHEMA
- `psai_bench/validation.py` — validate_scenarios, validate_submission
- `psai_bench/cli.py` — track choices in generate command
- `tests/` — 133 existing tests

### Integration Points
- Schema changes unblock all subsequent phases (12-17)
- Track-aware validation needed in validation.py
- CLI track enum needs extension

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
