# Roadmap: PSAI-Bench

## Milestones

- ✅ **v1.0 Release** - Phases 1-5 (shipped 2026-04-13)
- 🚧 **v2.0 Fix the Foundation** - Phases 6-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 Release (Phases 1-5) - SHIPPED 2026-04-13</summary>

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Repository Hygiene** - Fix lint, purge generated data from git history, update .gitignore
- [x] **Phase 2: Project Metadata + Licensing** - Complete pyproject.toml, add LICENSE, configure pre-commit
- [x] **Phase 3: Test Coverage Expansion** - Add CLI and statistics tests to raise coverage to meaningful levels
- [x] **Phase 4: GitHub Actions CI** - Wire test matrix and coverage badge; verify first green run
- [x] **Phase 5: Documentation + Release** - Write README, community files, CHANGELOG, bump version to 1.0.0

### Phase 1: Repository Hygiene
**Goal**: The repository is clean enough to push publicly — no lint errors, no generated data in git, no tracked build artifacts
**Depends on**: Nothing (first phase)
**Requirements**: REPO-01, REPO-02, REPO-03
**Success Criteria** (what must be TRUE):
  1. `ruff check .` exits 0 with no errors or warnings on the working tree
  2. `data/generated/` and build artifacts (*.egg-info, .coverage, .ruff_cache) are absent from `git ls-files`
  3. `git log --all --oneline` shows a history with no commits containing files over 1MB (generated JSON purged)
  4. `git status` on a fresh clone shows a clean working tree with no untracked generated data
**Plans**: 2 plans
Plans:
- [x] 01-01-PLAN.md — Fix lint errors, update .gitignore, untrack generated data
- [x] 01-02-PLAN.md — Rewrite git history to purge generated JSON blobs

### Phase 2: Project Metadata + Licensing
**Goal**: The package has complete OSS identity — correct legal standing, citable authorship, and contributor tooling in place before CI runs
**Depends on**: Phase 1
**Requirements**: DOCS-02, PKG-01, PKG-03
**Success Criteria** (what must be TRUE):
  1. `LICENSE` file exists at repo root containing Apache-2.0 full text; GitHub shows "Apache-2.0" license badge
  2. `pip show psai-bench` returns Author, Home-page, and Classifier fields (not empty)
  3. `pre-commit run --all-files` exits 0 (ruff-check and ruff-format hooks both pass)
  4. `python -c "import psai_bench; print(psai_bench.__version__)"` returns a valid semver string
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Simplify OUTPUT_SCHEMA and update validation logic
- [x] 09-02-PLAN.md — Scoring engine: ambiguous partition, Decisiveness, new aggregate, format_dashboard
- [x] 09-03-PLAN.md — Wire dashboard to CLI, delete stale commands, update tests

### Phase 3: Test Coverage Expansion
**Goal**: The test suite covers CLI commands and the statistics module at meaningful levels, and CI will not break on a clean environment due to missing generated data
**Depends on**: Phase 2
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. `pytest --co -q` lists test cases for CLI commands (generate, score, compare, gap) — previously 0 CLI tests
  2. `pytest --cov=psai_bench --cov-report=term-missing` shows statistics module coverage above 80%
  3. All 67 existing tests continue to pass after new tests are added
  4. NumPy version constraint and reproducibility note are documented in pyproject.toml or a REPRODUCIBILITY note
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Simplify OUTPUT_SCHEMA and update validation logic
- [x] 09-02-PLAN.md — Scoring engine: ambiguous partition, Decisiveness, new aggregate, format_dashboard
- [x] 09-03-PLAN.md — Wire dashboard to CLI, delete stale commands, update tests

### Phase 4: GitHub Actions CI
**Goal**: Every push and pull request automatically runs the full test suite across Python 3.10/3.11/3.12 and produces a green badge
**Depends on**: Phase 3
**Requirements**: PKG-02
**Success Criteria** (what must be TRUE):
  1. `.github/workflows/ci.yml` exists and triggers on push and pull_request to main
  2. The Actions tab shows a green check on the latest commit across all three Python version matrix entries
  3. A codecov coverage report is uploaded and a badge URL is available for use in the README
  4. `ruff check .` and `pytest` both run as separate CI steps without failures
**Plans**: 3 plans
Plans:
- [x] 09-01-PLAN.md — Simplify OUTPUT_SCHEMA and update validation logic
- [x] 09-02-PLAN.md — Scoring engine: ambiguous partition, Decisiveness, new aggregate, format_dashboard
- [x] 09-03-PLAN.md — Wire dashboard to CLI, delete stale commands, update tests

### Phase 5: Documentation + Release
**Goal**: PSAI-Bench is publicly presentable — a researcher landing on the repo immediately understands the research contribution, can reproduce results, and can cite the work
**Depends on**: Phase 4
**Requirements**: DOCS-01, DOCS-03, DOCS-04, DOCS-05, REL-01, REL-02
**Success Criteria** (what must be TRUE):
  1. README opens with the perception-reasoning gap hypothesis and GPT-4o concrete numbers (TDR=0.999, Aggregate=0.580) within the first 200 words
  2. README contains a results table (GPT-4o vs 4 baselines), three-track scenario table, BibTeX citation block, and all three shields.io badges (Python, License, CI)
  3. `pip install .` on a clean Python 3.10 environment succeeds and `psai-bench --help` returns the CLI help text
  4. CONTRIBUTING.md, CODE_OF_CONDUCT.md, and CHANGELOG.md exist at repo root
  5. `python -c "import psai_bench; print(psai_bench.__version__)"` returns `1.0.0`

</details>

---

- ✅ **v2.0 Fix the Foundation** — Phases 6-10, 9 plans, shipped 2026-04-13 ([archive](milestones/v2.0-ROADMAP.md))
