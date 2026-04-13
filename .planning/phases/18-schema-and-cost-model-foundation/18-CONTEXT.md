# Phase 18: Schema and Cost Model Foundation - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

The dispatch schema contract and cost model are stable, published, and independently testable before any scoring or generation code is written.

</domain>

<decisions>
## Implementation Decisions

### Architecture (from research — ALL researchers agree)
- dispatch is a PARALLEL optional field alongside verdict — never replaces 3-class triage
- VERDICTS constant must NOT change — add separate DISPATCH_ACTIONS constant
- Ground truth stays 3-class (THREAT/SUSPICIOUS/BENIGN)
- OUTPUT_SCHEMA: verdict remains required, dispatch is optional
- _meta: add optimal_dispatch, adversarial_type fields

### Cost Model (from research)
- New standalone psai_bench/cost_model.py module
- CostModel dataclass with configurable per-action costs indexed by (dispatch_action, ground_truth) tuple
- Default cost values are PROVISIONAL benchmark assumptions — documented as configurable
- compute_optimal_dispatch() uses a published decision table: GT × site_type × zone_sensitivity → action
- Cost reported under 3+ cost-ratio assumptions (low/medium/high) — sensitivity analysis built in
- SITE_THREAT_MULTIPLIERS: substation=5x, campus=2x, etc.

### Decision Rubric (DOC-01)
- Must be written BEFORE compute_optimal_dispatch() — the function implements the rubric
- Parallels v2.0 decision-rubric.md pattern
- GT × site_type × zone_sensitivity → optimal dispatch action

### Packaging Fix
- scipy must be declared as direct dependency in pyproject.toml (currently undeclared, pulled transitively via sklearn)

### Claude's Discretion
- Internal implementation details of CostModel
- Exact cost values within documented ranges
- Decision table specifics (which combos → which actions)
- REQUEST_DATA special handling in cost matrix

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/schema.py — VERDICTS tuple (imported by 6 consumers), OUTPUT_SCHEMA, _META_SCHEMA_V2
- psai_bench/scorer.py — score_run (DO NOT MODIFY), _score_partition, ScoreReport
- psai_bench/baselines.py — 4 baselines (will consume dispatch in Phase 19)
- psai_bench/distributions.py — assign_ground_truth_v2 (returns 3-class GT)
- pyproject.toml — dependencies (scipy missing)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond research decisions.

</specifics>

<deferred>
## Deferred Ideas

- score_dispatch_run() → Phase 19
- Baseline dispatch output → Phase 19
- AdversarialV4Generator → Phase 20

</deferred>
