# Phase 22: CLI Integration, Tests, and Documentation - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure + documentation phase)

<domain>
## Phase Boundary

All v4.0 features are wired, tested, and documented — the full test suite passes with no regressions, and users have a complete reference for dispatch scoring and the updated evaluation protocol.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — integration and documentation phase.

Key requirements:
- TEST-01: All 337 existing tests pass (no regressions)
- TEST-02: Dispatch scoring tests verify cost computation for known scenarios
- TEST-03: Adversarial v4 generation tests verify behavioral pattern presence
- TEST-04: Multi-site filtering preserves seed reproducibility
- TEST-05: Backward compatibility — v1/v2/v3 output files score correctly without dispatch field
- DOC-02: Updated EVALUATION_PROTOCOL.md with dispatch scoring, cost model, and multi-site generalization

### Integration Test Requirements
- E2E: generate → baseline → score_dispatch_run → assert cost_ratio and per_action_breakdown
- v1.0 output (no dispatch) + score_run() = same result as v3.0
- v1.0 output + score_dispatch_run() = clear error or graceful handling

</decisions>

<code_context>
## Existing Code Insights

### Already Implemented in Prior Phases
- Phase 18: schema.py (DISPATCH_ACTIONS, dispatch field), cost_model.py, dispatch-decision-rubric.md
- Phase 19: scorer.py (score_dispatch_run), baselines.py (dispatch field), format_dashboard cost_report
- Phase 20: generators.py (AdversarialV4Generator), cli.py (adversarial_v4 track)
- Phase 21: scorer.py (compute_site_generalization_gap), cli.py (--site-type, site-generalization)
- docs/EVALUATION_PROTOCOL.md exists from Phase 17 — needs v4.0 additions

</code_context>

<specifics>
No specific requirements beyond above.
</specifics>

<deferred>
None.
</deferred>
