# Phase 17: Evaluation Protocol - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (documentation phase)

<domain>
## Phase Boundary

A researcher can understand exactly how to evaluate any system against all four tracks using only the published documentation.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure documentation phase. Document must accurately reflect the final implementation from Phases 11-16.

Key requirements:
- PROTO-01: docs/EVALUATION_PROTOCOL.md documents GT definitions, scoring protocol, and sequence evaluation rules
- Must cover all 4 tracks: metadata, visual_only, visual_contradictory, temporal
- Must explain score_run vs score_sequences and when to use each
- Must explain frame extraction procedure (uniform sampling, never annotation-guided, deterministic)
- Must explain cross-track comparison interpretation (perception-reasoning gap)
- Must include worked examples per track

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/scorer.py — score_run, score_sequences, compute_perception_gap, format_dashboard
- psai_bench/generators.py — All generators (MetadataGenerator, VisualOnlyGenerator, ContradictoryGenerator, TemporalSequenceGenerator)
- psai_bench/frame_extraction.py — extract_keyframes (Phase 16)
- psai_bench/cli.py — All CLI commands
- psai_bench/distributions.py — assign_ground_truth_v2, description pools
- docs/decision-rubric.md — Existing GT documentation (metadata track)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond above.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
