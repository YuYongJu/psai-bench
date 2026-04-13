# Phase 21: Multi-Site Generalization - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (research settled key decisions)

<domain>
## Phase Boundary

Users can measure how well a system trained on one site type generalizes to another, backed by a leakage audit confirming site identity is not inferable from non-site features.

</domain>

<decisions>
## Implementation Decisions

### Multi-Site Design (from research)
- --site-type CLI filter for post-generation site-specific extraction (preserves seed reproducibility)
- LODO (leave-one-domain-out) evaluation protocol
- compute_site_generalization_gap() in scorer.py alongside existing functions
- site-generalization CLI command: --train site_a --test site_b → per-site accuracy + gap
- site_type already exists in ALERT_SCHEMA context (5 values: solar, substation, commercial, industrial, campus)

### Leakage Audit (SITE-02 — REQUIRED)
- Logistic regression probe: train on non-site features to predict site_type
- Must score ≤60% accuracy to confirm no structural leakage
- SITE_CATEGORY_BLOCKLIST may create leakage (some categories only appear at certain sites)
- Run audit on v2 scenario batch; document results

### Claude's Discretion
- Implementation details of site filtering
- Generalization gap metric formula
- Leakage audit test structure

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/scorer.py — score_run, partition_by_track, compute_perception_gap (reference patterns)
- psai_bench/generators.py — all generators produce context.site_type
- psai_bench/cli.py — generate command (add --site-type filter)
- psai_bench/distributions.py — SITE_TYPES, SITE_WEIGHTS

</code_context>

<specifics>
No specific requirements beyond research decisions.
</specifics>

<deferred>
None.
</deferred>
