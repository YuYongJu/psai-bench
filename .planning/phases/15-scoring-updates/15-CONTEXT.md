# Phase 15: Scoring Updates - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (research settled key decisions)

<domain>
## Phase Boundary

The scoring dashboard partitions results by track, score_sequences() measures sequence evaluation metrics, and the perception-reasoning gap is computable — all without modifying score_run().

</domain>

<decisions>
## Implementation Decisions

### Scoring Design (from research)
- score_run() is a public contract — MUST NOT be modified (133+ tests depend on it)
- Track partitioning: format_dashboard displays per-track TDR/FASR breakdowns when multiple tracks present
- score_sequences() is a NEW function with SequenceScoreReport dataclass — additive, not replacing
- Temporal metrics: escalation latency, correct-escalation rate, correct-resolution rate
- Perception-reasoning gap metric: computed when both metadata and visual results exist

### Track Partitioning Strategy
- score_run() returns a single ScoreReport for ALL scenarios (backward compatible)
- New: partition scenarios by track field, run scoring per partition, display in dashboard
- Dashboard shows overall + per-track breakdown

### Validation Updates
- Track-specific required field validation (visual_only must have visual_data.uri, etc.)
- Already partially done in Phase 11 (validation.py) — extend if needed

### Claude's Discretion
- SequenceScoreReport dataclass fields and formulas
- Dashboard formatting for multi-track display
- Gap metric computation details

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/scorer.py — score_run(), ScoreReport, format_dashboard(), _score_partition()
- psai_bench/generators.py — All generators (metadata, visual_only, contradictory, temporal)
- psai_bench/validation.py — Track-aware validation from Phase 11
- psai_bench/schema.py — Schema v3

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond research decisions.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
