# Phase 19: Scoring Pipeline and Baselines - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Users who supply `dispatch` fields in their output get cost-aware scoring alongside existing triage metrics — and all 4 baselines output dispatch decisions by default.

</domain>

<decisions>
## Implementation Decisions

### Scoring (from research)
- score_dispatch_run() wraps cost_model.score_dispatch() — lives in scorer.py alongside score_run()
- score_run() is BYTE-FOR-BYTE identical to v3.0 — no modifications
- format_dashboard() extended with optional cost_report parameter
- When cost_report is None, dashboard output is identical to v3.0

### Baselines (from research)
- VERDICT_TO_DEFAULT_DISPATCH mapping: THREAT→armed_response, SUSPICIOUS→operator_review, BENIGN→auto_suppress
- All 4 baselines (random, majority_class, always_suspicious, severity_heuristic) add dispatch field
- No baseline signature changes — dispatch is added to output dicts

### Claude's Discretion
- Implementation details of score_dispatch_run() wrapper
- Dashboard formatting for cost section
- Test structure

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/scorer.py — score_run (DO NOT MODIFY), format_dashboard, ScoreReport
- psai_bench/cost_model.py — CostModel, score_dispatch, CostScoreReport (Phase 18)
- psai_bench/baselines.py — random_baseline, majority_class_baseline, always_suspicious_baseline, severity_heuristic_baseline

</code_context>

<specifics>
No specific requirements beyond research decisions.
</specifics>

<deferred>
None.
</deferred>
