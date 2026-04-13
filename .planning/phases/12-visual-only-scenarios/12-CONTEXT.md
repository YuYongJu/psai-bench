# Phase 12: Visual-Only Scenarios - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped — research settled key decisions)

<domain>
## Phase Boundary

Users can generate visual-only scenarios where ground truth is derived from video content labels, not metadata signals, and existing leakage tests pass on the visual-only subset.

</domain>

<decisions>
## Implementation Decisions

### Visual-Only Design (from research)
- GT derived from UCF Crime category mapping (video content label), NOT from assign_ground_truth_v2
- `_meta.visual_gt_source = "video_category"` makes the GT derivation path explicit
- Fields populated from shared description pools (NOT sentinel values, NOT nulls) to avoid leakage
- `severity` and `description` keys omitted entirely from visual-only scenarios (schema v3 made them optional)
- `visual_data` must include URI, duration, resolution — this is the primary data source
- VisualOnlyGenerator does NOT wrap MetadataGenerator — builds directly from VisualTrackMapper pattern

### Leakage Safety (from pitfalls research)
- Visual-only scenarios must pass existing test_leakage.py stump tests
- No dummy/sentinel metadata values that create trivially detectable signals
- Run leakage tests immediately after first generation batch

### Claude's Discretion
- Internal implementation details of VisualOnlyGenerator
- Exact field population strategy for non-video fields
- Test structure and fixture design

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- `psai_bench/generators.py` — VisualGenerator (existing stub), MetadataGenerator (reference)
- `psai_bench/video_mapper.py` — VisualTrackMapper (builds from UCF Crime annotations)
- `psai_bench/distributions.py` — UCF_CATEGORY_MAP, description pools
- `psai_bench/schema.py` — ALERT_SCHEMA (already extended in Phase 11)
- `psai_bench/cli.py` — generate command (visual_only stub raises UsageError)

### Caltech Scope
- Caltech Camera Traps is metadata-only in v3.0 — no visual-only scenarios from Caltech

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond research decisions above.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
