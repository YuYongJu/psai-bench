# Project Research Summary

**Project:** PSAI-Bench
**Domain:** Open-source Python ML benchmark — GitHub release packaging
**Researched:** 2026-04-12
**Confidence:** HIGH

## Executive Summary

PSAI-Bench is a complete, implemented benchmark for evaluating frontier AI models in physical security scenarios. The benchmark core (CLI, scorer, generators, evaluators, baselines, statistics) is finished at v1.0rc1. The work remaining is entirely a release packaging problem: add the documentation, CI infrastructure, metadata, and repository hygiene required for a credible public GitHub release. No new benchmark logic needs to be written.

The recommended approach follows the pattern of well-maintained Python ML benchmarks (SWE-bench, MMLU, MLE-bench): comprehensive README with results table and citation block, clean GitHub Actions CI with a test matrix, Apache-2.0 LICENSE file, a small set of community files (CONTRIBUTING.md, CODE_OF_CONDUCT.md), and pyproject.toml metadata completed for public distribution. The entire release scope is low-complexity work — the highest-complexity item (GitHub Actions CI) is medium complexity, and everything else is low. Total scope is 10 discrete artifacts.

The primary risks are repo hygiene issues that must be resolved before any public push: 16MB of generated JSON files embedded in git history (requires git-filter-repo rewrite), 12 ruff lint errors that block a green CI badge, and a numpy version pin gap that could break benchmark reproducibility across library versions. Sequence matters — history rewrite and lint fixes must precede CI, and CI must pass before the README badges go live. Execute in dependency order and the risks are fully preventable.

## Key Findings

### Recommended Stack

The existing stack (Python 3.10+, pytest, numpy, pandas, setuptools) is sound and requires minimal changes. The only tooling additions needed are ruff (tighten pin from >=0.1 to >=0.8), GitHub Actions CI (replacing the absent test automation), codecov-action v5 for coverage badge, and pre-commit with ruff hooks. Explicitly excluded: mypy/pyright (high false-positive rate with numpy/pandas), tox/nox (GHA matrix subsumes this), sphinx/mkdocs (over-engineering for a CLI benchmark), Docker (unnecessary — no untrusted code execution), and automated PyPI publishing (out of scope for v1.0).

**Core technologies:**
- ruff >=0.8: lint + format — single tool replacing black/flake8/isort, already partially configured
- GitHub Actions matrix (3.10/3.11/3.12): CI — native, free for public repos, no infrastructure overhead
- codecov-action v5: coverage badge — public repos can opt out of token requirement
- pre-commit >=3.5: contributor lint enforcement — two hooks, zero friction

### Expected Features

The benchmark functionality is complete. Every "feature" for v1.0 is a release artifact. Research against HumanEval, SWE-bench, MMLU, BIG-bench, MLE-bench, and MTEB establishes what researchers expect in a credible benchmark before citing or extending it.

**Must have (table stakes):**
- README with results table, quickstart, scenario track comparison, methodology note, dataset provenance, citation block — the single highest-value artifact; every comparable benchmark has this
- LICENSE file (Apache-2.0 text) — legally required for OSS claims; current pyproject.toml declares the license but the file does not exist
- GitHub Actions CI (test + lint, green badge) — signals maintained project to researchers
- Lint-clean codebase (fix 12 ruff errors) — gates CI badge; broken lint before public release is a credibility risk
- CONTRIBUTING.md — expected by researchers wanting to add evaluators or scenarios
- CODE_OF_CONDUCT.md — trivial Contributor Covenant boilerplate; GitHub prompts for it
- CHANGELOG.md — single v1.0.0 entry; signals version maturity
- pyproject.toml metadata complete (authors, URLs, classifiers) — required for proper citation
- .gitignore updated + git history cleaned — 16MB generated data must leave git history before public push
- Version bump to 1.0.0 — signals stability

**Should have (differentiators):**
- Pre-computed results in repo (results/) — PSAI-Bench is unique among comparable benchmarks in shipping example evaluation outputs; immediately demonstrates the tool works
- Perception-reasoning gap analysis prominently surfaced in README — the core research contribution; GPT-4o TDR=0.999 but Aggregate=0.580 is a compelling, concrete finding
- Safety-weighted metrics explanation — TDR/FASR/ECE have non-obvious security domain semantics; 3-4 sentence methodology note differentiates from generic accuracy benchmarks
- Three scenario track table (metadata/visual/multi-sensor) — makes research design legible at a glance

**Defer (v2+):**
- HuggingFace Spaces leaderboard — only justified with 5+ model evaluations
- Expanded test coverage beyond 47% — add after CI baseline is green
- Additional model evaluations (Claude, Gemini) — needed before a multi-column comparison table is credible
- Jupyter notebook tutorial — only if user demand emerges

### Architecture Approach

The existing flat package structure (psai_bench/ at root) is correct — no src/ layout migration needed. The release adds three new layers on top of the unchanged package: a tooling layer (.github/workflows/ci.yml, .pre-commit-config.yaml), a documentation layer (README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md), and metadata changes to pyproject.toml. The module architecture is complete; the only structural changes are in data/generated/ (removed from git) and tests/ (optional expansion).

**Major components:**
1. CLI (cli.py / click) — generate to evaluate to score to compare pipeline; untested, must not require generated data files in CI
2. Core engine (scorer.py, statistics.py, validation.py, schema.py) — safety-weighted metrics and statistical tests; tested at 67 tests, 47% coverage
3. Data layer (distributions.py, downloader.py, video_mapper.py) — HuggingFace dataset fetch and frame extraction; partially untested

**Build order (dependency-constrained):**
1. Lint fixes + .gitignore + git rm cached artifacts (unblocks CI)
2. pyproject.toml metadata (add authors, classifiers, urls, ruff lint config)
3. LICENSE + community files (independent, no ordering constraints)
4. CI workflow (depends on lint-clean code and ruff config in pyproject.toml)
5. README.md (written last — requires clean CI for badge, results/ for table)
6. CHANGELOG.md + version bump (final gate before release commit)

### Critical Pitfalls

1. **16MB generated JSON in git history** — must run `git filter-repo --path data/generated/ --invert-paths` and force-push before the repo is public; recovery cost is LOW now (2-commit history), HIGH after public clones exist. This is the very first action.

2. **NumPy RNG version drift breaks reproducibility** — numpy>=1.24 with no upper bound allows numpy 2.x, which changes the random Generator bitstream (NEP 19). Fix: pin numpy>=1.24,<3 and document the exact numpy version used for canonical v1.0 datasets. Add SHA-256 checksums for canonical JSON files to release notes.

3. **CI broken on first run** — tests currently assume data/generated/ files exist from working tree; CI has a clean environment. Fix: ensure no test opens files in data/generated/ without a generate step, or mock file I/O in tests. Also set MPLBACKEND=Agg for headless CI.

4. **README explains what, not why** — technical documentation mode buries the core research contribution. Fix: open README with the perception-reasoning gap hypothesis and concrete GPT-4o numbers (TDR=0.999 but Aggregate=0.580) within the first 200 words. Put results table before installation instructions.

5. **LICENSE file absent despite license declaration** — pyproject.toml declares Apache-2.0 but the file does not exist. GitHub shows "No license", pip show returns License: UNKNOWN. Fix: first thing after git history cleanup.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Repository Hygiene
**Rationale:** Three blockers must be eliminated before any public-facing work is credible: the large files in git history (irreversible once public), the 12 lint errors (block CI from ever going green), and the build artifacts tracked in git. This phase has zero dependencies and unblocks every subsequent phase.
**Delivers:** Clean git history (<2MB), lint-passing codebase, proper .gitignore, build artifacts removed
**Addresses:** Table stakes (clean .gitignore), lint-clean prerequisite for CI badge
**Avoids:** Pitfall 1 (large files in history), Pitfall 3 (CI broken on first run — lint portion), Pitfall 8 (results JSON permanence — decide and act)

### Phase 2: Project Metadata + Licensing
**Rationale:** pyproject.toml completion and LICENSE file are independent of CI and README but are prerequisites for credible citation and OSS legal standing. These are fast, low-risk changes that should land before CI so the metadata is correct when CI first runs.
**Delivers:** Complete pyproject.toml (authors, URLs, classifiers, ruff lint config), LICENSE file (Apache-2.0), version bumped to 1.0.0
**Addresses:** Table stakes (LICENSE, pyproject.toml metadata, version bump)
**Avoids:** Pitfall 4 (broken pip install metadata), Pitfall 5 (LICENSE absent)

### Phase 3: Community Files
**Rationale:** CONTRIBUTING.md, CODE_OF_CONDUCT.md, and CHANGELOG.md have no dependencies and no ordering constraints among themselves. Group together as a single low-effort phase.
**Delivers:** CONTRIBUTING.md (how to add evaluators/datasets), CODE_OF_CONDUCT.md (Contributor Covenant), CHANGELOG.md (v1.0.0 entry)
**Addresses:** Table stakes (all three files), GitHub community profile completeness

### Phase 4: CI Setup
**Rationale:** CI depends on lint-clean code (Phase 1) and [tool.ruff.lint] config in pyproject.toml (Phase 2). This phase wires the GitHub Actions matrix, sets coverage threshold at current level minus 2 points (45%), uploads coverage to codecov, and verifies first green run.
**Delivers:** .github/workflows/ci.yml, .pre-commit-config.yaml, green CI badge URL
**Uses:** GitHub Actions matrix (3.10/3.11/3.12), ruff, pytest-cov, codecov-action v5
**Avoids:** Pitfall 6 (CI broken on first run — data file and API key portions), Anti-Pattern 1 (installing api extras in CI), Anti-Pattern 2 (coverage threshold too high)

### Phase 5: README
**Rationale:** README is written last because it depends on a passing CI run (for badge status), confirmed results/ content (for results table), and final package metadata (for install instructions). Writing it last means everything it references is real and verified.
**Delivers:** README.md — perception-reasoning gap framing, scenario track table, results table (GPT-4o vs 4 baselines), methodology note, quickstart (install + generate + score), dataset provenance, BibTeX citation block, shields.io badges
**Addresses:** All differentiators (gap analysis, safety metrics, track table, pre-computed results); table stakes (README, quickstart, citation, badges)
**Avoids:** Pitfall 2 (generated data not reproducible — document exact generate invocations), Pitfall 7 (README explains what not why — open with research hypothesis and concrete numbers), Anti-Pattern 3 (pyproject readme field + README in same commit)

### Phase Ordering Rationale

- Phase 1 (hygiene) must be first: git history rewrite is irreversible after public push; lint errors block CI from ever showing green; both are zero-dependency actions
- Phase 2 (metadata) before CI: ruff lint config must exist in pyproject.toml before ruff check . in CI is meaningful; README field change and README.md creation must land together
- Phase 3 (community files) can slot anywhere between 2 and 5 but groups naturally with metadata work
- Phase 4 (CI) requires phases 1 and 2; must produce a green badge URL before README references it
- Phase 5 (README) last: aggregates outputs from all prior phases into the project's public face

### Research Flags

Phases with standard patterns (skip research-phase):
- **Phase 1 (hygiene):** git-filter-repo is well-documented; ruff --fix is deterministic; no unknowns
- **Phase 2 (metadata):** pyproject.toml field names are well-documented in Python Packaging User Guide
- **Phase 3 (community files):** boilerplate content with established templates (Contributor Covenant, CHANGELOG format)
- **Phase 4 (CI):** GitHub Actions Python matrix is thoroughly documented

Phases likely needing attention during planning:
- **Phase 4 (CI):** Verify google-genai is the correct current PyPI package name before writing optional dep install steps; verify evaluator test mocking strategy does not leak into required test paths
- **Phase 5 (README):** Resolve the results/ permanence decision before writing the README results table — if large evaluation JSONs move to GitHub Release assets, the README must point there instead of results/evaluations/

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | ruff, GitHub Actions, codecov versions verified against PyPI and GitHub releases as of 2026-04-12 |
| Features | HIGH | Cross-referenced against 6 comparable benchmarks (HumanEval, SWE-bench, MMLU, BIG-bench, MLE-bench, MTEB) |
| Architecture | HIGH | Based on direct repo inspection (git ls-files, pyproject.toml, module structure); no inference needed |
| Pitfalls | HIGH | Most pitfalls directly observed in the repo (large files, missing LICENSE, lint errors, pyproject.toml gaps) |

**Overall confidence:** HIGH

### Gaps to Address

- **results/ permanence decision:** PROJECT.md marks this as a pending key decision. Research recommendation is to keep results/ as example outputs (research value, ~16MB is acceptable), but if that decision flips, README content and .gitignore must change accordingly. Resolve before Phase 5.
- **Canonical generate invocations:** The exact psai-bench generate flags that produced the canonical v1.0 dataset need to be confirmed and documented. Without this, reproducibility documentation in the README cannot be written accurately. Confirm during Phase 1 or 2.
- **numpy version used for v1.0 dataset:** The exact numpy version active when 7eda522 was committed should be identified so the README and release notes can document it for reproducibility. Address during Phase 1.

## Sources

### Primary (HIGH confidence)
- ruff PyPI page (pypi.org/project/ruff/) — v0.15.10 confirmed current
- astral-sh/ruff-pre-commit (github.com/astral-sh/ruff-pre-commit) — pre-commit hook rev confirmed
- codecov/codecov-action (github.com/codecov/codecov-action) — v5 stable, v6 not yet released
- Python Packaging User Guide (packaging.python.org) — pyproject.toml metadata fields
- NumPy NEP 19 (numpy.org/neps/nep-0019-rng-policy.html) — RNG version stability policy
- git-filter-repo (github.com/newren/git-filter-repo) — recommended by git official docs
- Contributor Covenant (contributor-covenant.org) — CODE_OF_CONDUCT boilerplate
- Direct repo inspection: git show --stat 7eda522, git ls-files, pyproject.toml, .gitignore

### Secondary (MEDIUM confidence)
- HumanEval, SWE-bench, MMLU, BIG-bench, MLE-bench, MTEB GitHub repos — feature/badge pattern analysis
- daily.dev badge best practices — "3 max, stick to what's truthful"
- hynek.me/articles/python-github-actions/ — Python CI patterns

---
*Research completed: 2026-04-12*
*Ready for roadmap: yes*
