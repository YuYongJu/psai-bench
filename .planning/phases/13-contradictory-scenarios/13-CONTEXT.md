# Phase 13: Contradictory Scenarios - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (research settled key decisions)

<domain>
## Phase Boundary

Users can generate contradictory scenarios where metadata and video content deliberately disagree and GT always follows the video content label.

</domain>

<decisions>
## Implementation Decisions

### Contradictory Design (from research)
- Two sub-types: overreach (metadata=THREAT, video=BENIGN) and underreach (metadata=BENIGN, video=THREAT)
- GT always follows video content, never metadata — this is the test design, not a bug
- `_meta.contradictory = true` flag required on all contradictory scenarios
- `_meta.metadata_derived_gt` stores what assign_ground_truth_v2 would have returned (for analysis)
- `_meta.video_derived_gt` stores GT from video content label (this IS the ground truth)
- Need new GT derivation path — bypass assign_ground_truth_v2 for contradictory scenarios
- Contradictory description pools: plausible-but-wrong descriptions (threat-sounding for benign video, benign-sounding for threat video)

### Implementation Pattern (from architecture research)
- ContradictoryGenerator builds on VisualOnlyGenerator pattern (Phase 12)
- New description pools: CONTRADICTORY_THREAT_DESCRIPTIONS and CONTRADICTORY_BENIGN_DESCRIPTIONS in distributions.py
- Automated test must assert metadata_derived_gt != video_derived_gt for ALL contradictory scenarios

### Claude's Discretion
- Internal ContradictoryGenerator implementation details
- Exact description pool content (must be plausible-but-wrong)
- Balance between overreach and underreach sub-types

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- `psai_bench/generators.py` — VisualOnlyGenerator (Phase 12 reference), MetadataGenerator
- `psai_bench/distributions.py` — UCF_CATEGORY_MAP, existing description pools, assign_ground_truth_v2
- `psai_bench/schema.py` — ALERT_SCHEMA with contradictory _meta field (Phase 11)
- `psai_bench/cli.py` — visual_contradictory stub raises UsageError

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond research decisions.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
