# Phase 8: Decision Rubric Documentation - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `docs/decision-rubric.md` — a human-readable document explaining the ground truth assignment logic so any researcher can audit why a given scenario received its label.

</domain>

<decisions>
## Implementation Decisions

### Document Structure
- Single file: `docs/decision-rubric.md`
- Sections: overview of the decision function, signal definitions, scoring mechanics, threshold logic, worked examples, adversarial case explanations
- Three worked examples minimum: one THREAT, one SUSPICIOUS, one BENIGN
- Explicit adversarial case documentation: why HIGH severity can yield BENIGN and why LOW severity can yield THREAT

### Content Source
- Read `psai_bench/distributions.py` — the actual `assign_ground_truth_v2` function IS the source of truth
- Document the exact signal weights, thresholds, and scoring bands as implemented in code
- Do NOT invent or simplify the logic — document what the code actually does

### Claude's Discretion
- Exact wording and formatting style
- Whether to include a summary table or flowchart
- How much mathematical notation vs. plain English
- Additional examples beyond the required 3

</decisions>

<code_context>
## Existing Code Insights

### Source of Truth
- `psai_bench/distributions.py` — `assign_ground_truth_v2()` function with all signal weights and thresholds
- `psai_bench/generators.py` — `_inject_adversarial_signals()` for adversarial case mechanics
- `tests/test_decision_rubric.py` — 9 known-correct configurations that serve as concrete examples

### Integration Points
- Phase 10 will link this document from the README (DOCS-03)
- `docs/` directory may need creation

</code_context>

<specifics>
## Specific Ideas

No specific requirements — straightforward documentation of existing logic.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
