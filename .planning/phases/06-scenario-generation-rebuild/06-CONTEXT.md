# Phase 6: Scenario Generation Rebuild - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Rebuild the scenario generation system so that no single input field (description, severity, zone, time, device) predicts ground truth above 70% accuracy. Ground truth is determined by a weighted scoring function that combines 3+ context signals, not by category lookup. The description pool is shared across GT classes. ~20% of scenarios are adversarial with conflicting signals.

</domain>

<decisions>
## Implementation Decisions

### GT Decision Function
- GT determined by weighted scoring of 3+ signals (not any single field)
- Structured as a point-based system: each signal contributes points toward THREAT/BENIGN, threshold determines GT
- 20% of scenarios are adversarial (conflicting signals)
- Normal/Benign scenarios CAN have threatening-sounding descriptions (authorized maintenance at night, etc.)
- Decision function is deterministic given scenario context (not random post-hoc)

### Description Pool
- 20-25 shared/ambiguous descriptions that appear across ALL GT classes
- 10-15 unambiguous descriptions for extreme cases (~30% of total): "Visible flames" = always THREAT, "Clear sky no motion" = always BENIGN
- Descriptions decoupled from UCF category — sampled from pool, not from category templates
- Style: terse analytics system output ("Motion detected, human-shaped, zone-3-perimeter, 02:14")

### Backward Compatibility
- New `version` parameter: `MetadataGenerator(version="v2")` for new logic
- Default `version="v1"` preserves existing behavior exactly
- CLI gets `--version v2` flag
- GPT-4o results kept but renamed to `gpt-4o_ucf_metadata_v1_run1.json`
- Version bumped to 2.0.0

### Claude's Discretion
- Exact weights in the scoring function
- Exact description text for the shared pool
- How to handle the Caltech generator (apply same pattern or defer)
- Internal data structure for the decision function

</decisions>

<code_context>
## Existing Code Insights

### Files to Modify
- `psai_bench/distributions.py` — replace UCF_CATEGORY_MAP severity_range and description_templates with shared pools + decision function
- `psai_bench/generators.py` — MetadataGenerator gains `version` param, v2 path uses decision function
- `psai_bench/schema.py` — add ambiguity_flag to _meta
- `psai_bench/cli.py` — add --version flag to generate command

### Reusable Assets
- Zone sampling (sample_zone) — clean, no leakage
- Device sampling (sample_device) — clean, no leakage  
- Weather sampling (sample_weather) — clean
- Site type sampling — clean
- Difficulty assignment function — may need update for v2 scenarios
- All test infrastructure (103 tests)

### Current Leakage (what we're fixing)
- UCF_CATEGORY_MAP: each category → 1 GT, 1 severity range, 1 set of descriptions
- 45 descriptions, all map to exactly 1 GT class (100% leakage)
- Severity: LOW=BENIGN, CRITICAL=THREAT with zero overlap (85.7% leakage)

</code_context>

<specifics>
## Specific Ideas

The weighted scoring approach should work like this:
- Each scenario gets signal scores: zone_score, time_score, device_score, severity_score, description_category_score
- Scores are [-1, +1] where negative = BENIGN, positive = THREAT
- Weighted sum determines GT: < -threshold → BENIGN, > +threshold → THREAT, between → SUSPICIOUS
- Adversarial scenarios are created by forcing one signal to contradict the others

</specifics>

<deferred>
## Deferred Ideas

- Caltech generator v2 — apply same pattern but may do in a follow-up if time is tight
- Visual track v2 — deferred to v3.0
- Multi-sensor track v2 — deferred to v3.0

</deferred>
