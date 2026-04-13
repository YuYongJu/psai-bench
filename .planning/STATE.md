---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Perception-Reasoning Gap
status: planning
stopped_at: Roadmap created for v3.0 — Phase 11 ready to plan
last_updated: "2026-04-13T00:00:00.000Z"
last_activity: 2026-04-13
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 10
  completed_plans: 0
  percent: 0
---

# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-13)

**Core value:** Non-trivially-solvable benchmark where no single input field reveals ground truth — extended to test whether video perception adds value over metadata-only triage
**Current focus:** v3.0 — Perception-Reasoning Gap (Phase 11: Schema v3)

## Current Position

Phase: 11 of 17 (Schema v3)
Plan: — (not started)
Status: Ready to plan
Last activity: 2026-04-13 — Roadmap created, Phase 11 ready to plan

Progress: [████░░░░░░] 40% (v1.0 + v2.0 complete, v3.0 starting)

## Performance Metrics

**Velocity:**

- Total plans completed: ~18 (v1.0 + v2.0)
- Average duration: unknown
- Total execution time: unknown

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| v1.0 (1-5) | ~9 | - | - |
| v2.0 (6-10) | 9 | - | - |
| v3.0 (11-17) | 0/10 | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- v1.0: Infrastructure is solid (CLI, scoring engine, stats, CI) — keep
- v2.0: Context-dependent GT is the core design change; 133 tests now passing
- v2.0: "Bring Your Own System" is the primary workflow
- v3.0: Visual-only fields populated from shared description pools (not sentinels/nulls) — leakage test constraint settles the design conflict
- v3.0: score_run() is a public contract — temporal scoring ships as separate score_sequences()
- v3.0: Frame extraction is evaluation protocol, not benchmark code

### Pending Todos

None yet.

### Blockers/Concerns

- Pin seed-42 regression hash BEFORE any generator changes (highest-risk step — do it first in Phase 11)
- Visual-only leakage test behavior unconfirmed until generator exists — run test_leakage.py immediately after first generation batch
- Contradictory description pools must be plausible-but-wrong (not obviously wrong) — budget a review pass in Phase 13

## Session Continuity

Last session: 2026-04-13
Stopped at: Roadmap created for v3.0, Phase 11 ready to plan
Resume file: None
