---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Operational Realism — Phases 18-22
status: planning
stopped_at: Roadmap created for v4.0, Phase 18 ready to plan
last_updated: "2026-04-13T23:56:10.458Z"
last_activity: 2026-04-13
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 10
  completed_plans: 10
  percent: 100
---

# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-13)

**Core value:** Non-trivially-solvable benchmark extended to operational decision-support — measuring not just "what is this?" but "what should you do about it?"
**Current focus:** v4.0 — Operational Realism (Phase 18: Schema and Cost Model Foundation)

## Current Position

Phase: 22 of 22 (cli integration, tests, and documentation)
Plan: Not started
Status: Ready to plan
Last activity: 2026-04-13

Progress: [░░░░░░░░░░] 0% (v4.0 starting)

## Performance Metrics

**Velocity:**

- Total plans completed: ~28 (v1.0 + v2.0 + v3.0)
- Average duration: unknown
- Total execution time: unknown

**By Phase (v4.0):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 18 (schema + cost model) | 0/? | - | - |
| 19 (scoring + baselines) | 0/? | - | - |
| 20 (adversarial v4) | 0/? | - | - |
| 21 (multi-site) | 0/? | - | - |
| 22 (CLI + tests + docs) | 0/? | - | - |
| 18 | 2 | - | - |
| 19 | 2 | - | - |
| 20 | 2 | - | - |
| 21 | 2 | - | - |
| 22 | 2 | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- v1.0: Infrastructure is solid (CLI, scoring engine, stats, CI) — keep
- v2.0: Context-dependent GT is the core design change; 133 tests now passing
- v2.0: "Bring Your Own System" is the primary workflow
- v3.0: Visual-only fields populated from shared description pools (not sentinels/nulls) — leakage test constraint settles the design conflict
- v3.0: score_run() is a public contract — temporal scoring ships as separate score_sequences()
- v3.0: Frame extraction is evaluation protocol, not benchmark code
- v4.0: dispatch is a parallel optional field alongside verdict — never replaces 3-class triage (VERDICTS constant must not change)
- v4.0: cost dollar values are provisional benchmark assumptions — expose --cost-profile flag, report at 3+ cost-ratio assumptions
- v4.0: AdversarialV4Generator gets isolated RNG instance — prevents seed regression in existing tracks
- v4.0: SCORE-04 (compute_site_generalization_gap) belongs in Phase 21 (multi-site) not Phase 19 — it measures site differences, not dispatch scoring
- v4.0: DOC-01 (dispatch decision rubric) belongs in Phase 18 — compute_optimal_dispatch() depends on the decision table existing before implementation

### Pending Todos

- Phase 18 research flag: cost dollar values are LOW confidence — label defaults as "provisional benchmark assumptions" in documentation
- Phase 18 research flag: write compute_optimal_dispatch() decision table (GT x site_type x zone_sensitivity -> dispatch action) before implementing
- Phase 20 research flag: document GT assignment rule for behavioral adversarials — signals determine GT, not narrative
- Phase 21: run logistic regression leakage audit on non-site features before publishing generalization metric

### Blockers/Concerns

- scipy is imported in statistics.py but undeclared in pyproject.toml — fix in Phase 18 when touching pyproject.toml
- VERDICTS constant touches 6 consumers — add DISPATCH_ACTIONS as separate constant, never change VERDICTS
- Multi-site leakage audit (Phase 21) may reveal SITE_CATEGORY_BLOCKLIST creates structural site-identity signal — flag as potential scope risk

## Session Continuity

Last session: 2026-04-13
Stopped at: Roadmap created for v4.0, Phase 18 ready to plan
Resume file: None
