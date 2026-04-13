# Phase 14: Temporal Sequences - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (research settled key decisions)

<domain>
## Phase Boundary

Users can generate temporal alert sequences of 3-5 related alerts with escalation narrative patterns threaded by sequence_id.

</domain>

<decisions>
## Implementation Decisions

### Temporal Design (from research)
- TemporalSequenceGenerator produces groups of 3-5 related alerts sharing a sequence_id
- Alerts within a sequence have monotonically increasing timestamps
- sequence_position values are unique integers starting at 1
- 3 escalation pattern types required: monotonic escalation, escalation-then-resolution, false alarm sequence
- Escalation point varies across sequences (not always alert 2 of 5) — prevents position leakage
- Temporal sequences still use assign_ground_truth_v2 (unlike visual-only/contradictory)

### Pattern Definitions
- **Monotonic escalation:** severity/threat increases with each alert in sequence (e.g., LOW→MEDIUM→HIGH→CRITICAL)
- **Escalation-then-resolution:** severity increases then drops (e.g., LOW→HIGH→HIGH→LOW — badge scan resolves concern)
- **False alarm sequence:** initial high-severity alert followed by benign context (e.g., HIGH→LOW→LOW — camera FP confirmed)

### Pitfalls (from research)
- Scoring design (per-sequence) determines what data the generator emits — but score_sequences() is Phase 15
- Generator must emit enough _meta for Phase 15 scorer to work: sequence_id, sequence_position, escalation_pattern
- Each alert in sequence gets its own GT via assign_ground_truth_v2 with context signals that evolve across the sequence

### Claude's Discretion
- Internal TemporalSequenceGenerator implementation
- How context signals evolve across alerts in a sequence
- Exact alert count distribution (3-5)

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/generators.py — MetadataGenerator (v2 with assign_ground_truth_v2), VisualOnlyGenerator, ContradictoryGenerator
- psai_bench/distributions.py — assign_ground_truth_v2, description pools, sampling functions
- psai_bench/schema.py — _meta with sequence_id, sequence_position, sequence_length fields (Phase 11)
- psai_bench/cli.py — temporal stub raises UsageError

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond research decisions.

</specifics>

<deferred>
## Deferred Ideas

- score_sequences() function → Phase 15

</deferred>
