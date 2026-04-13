# Phase 9: Scoring and Schema Updates - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the opaque aggregate scoring with a transparent metrics dashboard. Handle ambiguous scenarios separately. Simplify the output schema to accept minimal non-LLM outputs.

</domain>

<decisions>
## Implementation Decisions

### Metrics Dashboard
- CLI table output via `print()` with labeled rows — clean, grep-able, no external dependencies
- Keep aggregate score but print the formula alongside it: `Aggregate = 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` with configurable weights
- Decisiveness = fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS)
- New `format_dashboard()` function in `scorer.py` — keeps scoring and display co-located
- Dashboard shows: TDR, FASR, Decisiveness, Calibration (ECE), per-difficulty accuracy as separate labeled values

### Ambiguous Scenario Handling
- Compute metrics twice: main metrics EXCLUDE ambiguous scenarios, then a separate "Ambiguous Bucket" section shows performance on those
- Ambiguous scenarios do NOT affect the aggregate score
- Detect ambiguous scenarios via `_meta.ambiguity_flag == True` (set by Phase 6 generator)
- System that gives THREAT or BENIGN on an ambiguous scenario is not penalized

### Schema Simplification
- Remove `reasoning` from OUTPUT_SCHEMA `required` list, remove `minLength` constraint
- Remove `processing_time_ms` from OUTPUT_SCHEMA `required` list
- Add `description` field to `confidence` in JSON Schema: "probability that the verdict is correct"
- Minimal valid output: `alert_id` + `verdict` + `confidence` only — add test to verify

### Claude's Discretion
- Exact formatting of the dashboard table
- Whether to add a `--format json` flag for machine-readable dashboard output
- Internal refactoring of `score_run` to support ambiguous exclusion
- Aggregate weight values (suggested 0.4/0.3/0.2/0.1 but can adjust if better justified)

</decisions>

<code_context>
## Existing Code Insights

### Files to Modify
- `psai_bench/scorer.py` — `score_run()`, `ScoreReport`, add `format_dashboard()`, add Decisiveness metric, handle ambiguous scenarios
- `psai_bench/schema.py` — `OUTPUT_SCHEMA` required list, confidence description
- `psai_bench/cli.py` — wire dashboard output to `score` command

### Reusable Assets
- `ScoreReport` dataclass — add `decisiveness` field
- `score_run()` — modify to partition ambiguous/non-ambiguous scenarios
- `_ece()`, `_brier_score()`, `_safety_score()` — keep as-is
- Existing test infrastructure (125 tests)

### Current Issues to Fix
- OUTPUT_SCHEMA requires `reasoning` (minLength: 20) and `processing_time_ms` — both should be optional
- `aggregate_score` computed with opaque formula — needs published weights
- No Decisiveness metric exists
- No ambiguous scenario handling in scoring

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond what's captured in decisions.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
