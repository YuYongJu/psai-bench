# State

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-13 — Milestone v2.0 started

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-13)

**Core value:** Non-trivially-solvable benchmark where no single input field reveals ground truth
**Current focus:** v2.0 — Fix the Foundation

## Accumulated Context

### Decisions

- v1.0: Infrastructure is solid (CLI, scoring engine, stats, CI, 103 tests) — keep
- v1.0: Scenario generation has critical leakage — rebuild
- v1.0: Aggregate scoring formula is opaque — replace with separate metrics
- v1.0: Output schema forces LLM assumptions — simplify
- v2.0: Context-dependent GT is the core design change
- v2.0: "Bring Your Own System" is the primary workflow, built-in evaluators are examples

### Pending Todos

None yet.

### Blockers/Concerns

- Decision rubric for context-dependent GT needs careful design — determines benchmark quality
- Backward compatibility: default params must still produce v1.0-compatible output
- Existing GPT-4o results will be invalid under new scenarios — document this

## Session Continuity

Last session: 2026-04-13
Stopped at: Milestone v2.0 initialized, defining requirements
Resume file: None
