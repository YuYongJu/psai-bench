# Phase 16: CLI Extensions - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Users can invoke all three new generators from the CLI and compute the frame extraction baseline gap without any code changes.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure CLI/packaging infrastructure phase.

Key requirements:
- FRAME-01: opencv-python-headless added as optional [visual] dependency in pyproject.toml
- FRAME-02: Frame extraction baseline extracts keyframes WITHOUT using anomaly_segments (fairness constraint)
- FRAME-03: analyze-frame-gap CLI command computes perception-reasoning gap from two result files
- New CLI commands: score-sequences, analyze-frame-gap
- All 3 new track generators already wired to CLI in prior phases

</decisions>

<code_context>
## Existing Code Insights

### Key Files
- psai_bench/cli.py — All CLI commands, generate already wired for all tracks
- psai_bench/scorer.py — score_sequences(), compute_perception_gap() from Phase 15
- psai_bench/baselines.py — Existing baselines (random, majority, always_suspicious, severity_heuristic)
- pyproject.toml — Package configuration with existing [api] optional group

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond above.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
