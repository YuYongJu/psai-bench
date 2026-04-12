# Phase 1: Repository Hygiene - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

The repository is clean enough to push publicly — no lint errors, no generated data in git, no tracked build artifacts. This phase handles: fixing 12 ruff lint errors, updating .gitignore to exclude generated data and build artifacts, removing tracked generated files from git, and rewriting git history to purge the 16MB of generated JSON committed in the initial squash commit.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Key technical notes from research:
- Use `ruff check --fix .` for auto-fixable lint errors (11 of 12 are auto-fixable)
- One unused variable (F841) may need `--unsafe-fixes` or manual fix
- Use `git filter-repo` to purge data/generated/ from history (preferred over BFG)
- Keep results/ in git (research differentiator — small size, useful as example outputs)
- Remove data/generated/, *.egg-info/, .coverage, .ruff_cache/, .pytest_cache/ from git tracking

</decisions>

<code_context>
## Existing Code Insights

### Current Lint Errors (12 total)
- 9x F401 unused imports (psai_bench/evaluators.py, generators.py, etc.)
- 2x F541 f-string without placeholders (cli.py)
- 1x F841 unused variable

### Files Currently Tracked That Shouldn't Be
- data/generated/metadata_caltech_seed42.json
- data/generated/metadata_ucf_seed42.json
- data/generated/visual_ucf_real_seed42.json
- psai_bench.egg-info/ (4 files)

### Git History
- Single content commit (7eda522) contains all generated data
- .planning/ commits added on top

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
