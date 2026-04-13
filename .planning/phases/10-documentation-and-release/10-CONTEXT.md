# Phase 10: Documentation and Release - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure/docs phase — decisions largely dictated by requirements)

<domain>
## Phase Boundary

Rewrite README to lead with BYOS workflow, reposition built-in evaluators as examples, link decision rubric, handle v2.0 results, and add honest Known Limitations section.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — this is a documentation phase with very specific success criteria. The requirements (DOCS-01 through DOCS-05) dictate exactly what needs to be in the README. Use the existing README structure as a starting point and modify to match requirements.

Key requirements:
- DOCS-01: README leads with BYOS workflow (generate → run your system → score) with 3-step example
- DOCS-02: Built-in evaluators documented as reference implementations / examples
- DOCS-03: Decision rubric linked from README (`docs/decision-rubric.md` created in Phase 8)
- DOCS-04: Results table updated for v2.0 or removed with explanation
- DOCS-05: Known Limitations section honest about what v2.0 does and doesn't test

</decisions>

<code_context>
## Existing Code Insights

### Files to Modify
- `README.md` — main documentation rewrite

### Existing Assets
- `docs/decision-rubric.md` — created in Phase 8, ready to link
- `psai_bench/cli.py` — CLI commands for generate, score (reference for 3-step example)
- Current README has results table with GPT-4o v1.0 results that are now invalid

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow the success criteria exactly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
