# Roadmap: PSAI-Bench

## Milestones

- ✅ **v1.0 Release** - Phases 1-5 (shipped 2026-04-13)
- ✅ **v2.0 Fix the Foundation** — Phases 6-10 (shipped 2026-04-13)
- ✅ **v3.0 Perception-Reasoning Gap** — Phases 11-17 (shipped 2026-04-13)
- 🔄 **v4.0 Operational Realism** — Phases 18-22 (in progress)

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

---

- ✅ **v3.0 Perception-Reasoning Gap** — Phases 11-17, 10 plans, shipped 2026-04-13 ([archive](milestones/v3.0-ROADMAP.md))

---

## v4.0 Operational Realism — Phases 18-22

- [ ] **Phase 18: Schema and Cost Model Foundation** - Extend schema with dispatch field, define cost model, publish dispatch decision rubric
- [ ] **Phase 19: Scoring Pipeline and Baselines** - Add dispatch scoring function, extend dashboard, update all baselines
- [ ] **Phase 20: Adversarial v4 Generator** - Implement behavioral adversarial scenarios with isolated RNG and separate description pools
- [ ] **Phase 21: Multi-Site Generalization** - Add site-type filtering, leakage audit, and generalization gap metric
- [ ] **Phase 22: CLI Integration, Tests, and Documentation** - Wire all new commands, verify 100% backward compatibility, complete test suite

## Phase Details

### Phase 18: Schema and Cost Model Foundation
**Goal**: The dispatch schema contract and cost model are stable, published, and independently testable before any scoring or generation code is written
**Depends on**: Phase 17
**Requirements**: DISP-01, DISP-02, DISP-03, DISP-04, DISP-05, COST-01, COST-02, COST-03, COST-04, COST-05, DOC-01
**Success Criteria** (what must be TRUE):
  1. A JSON output with `dispatch: "armed_response"` validates against OUTPUT_SCHEMA; a JSON without `dispatch` also validates (optional field, backward compatible)
  2. `from psai_bench.cost_model import CostModel, compute_optimal_dispatch` imports without error and `compute_optimal_dispatch("THREAT", {"site_type": "solar"})` returns one of the 5 DISPATCH_ACTIONS values
  3. `cost_model.py` with a custom cost profile JSON reports expected cost at a minimum of 3 cost-ratio assumptions (low/medium/high)
  4. The dispatch decision rubric document (GT x site_type x zone_sensitivity -> optimal_dispatch table) exists and is referenced from DOC-01
  5. `scipy` is declared as a direct dependency in pyproject.toml and `pip install psai-bench` on a clean environment pulls it explicitly
**Plans**: 2 plans
Plans:
- [ ] 18-01-PLAN.md — Schema extension (dispatch field, DISPATCH_ACTIONS, _meta fields, v4 version) + scipy fix + dispatch decision rubric
- [ ] 18-02-PLAN.md — Cost model (cost_model.py: CostModel, DISPATCH_COSTS, compute_optimal_dispatch, score_dispatch, sensitivity analysis)

### Phase 19: Scoring Pipeline and Baselines
**Goal**: Users who supply `dispatch` fields in their output get cost-aware scoring alongside the existing triage metrics — and all 4 baselines output dispatch decisions by default
**Depends on**: Phase 18
**Requirements**: SCORE-01, SCORE-02, SCORE-03
**Success Criteria** (what must be TRUE):
  1. `score_dispatch_run(outputs, scenarios)` returns a `CostScoreReport` with expected cost, optimal cost, cost ratio, and per-action breakdown — and `score_run()` is byte-for-byte identical to its v3.0 implementation
  2. `format_dashboard(report, cost_report=None)` with no `cost_report` produces output identical to v3.0; with a `cost_report` it appends a dispatch cost section
  3. Running any of the 4 baselines against a v4.0 scenario set produces output JSON where every entry has a `dispatch` field with one of the 5 valid DISPATCH_ACTIONS values
**Plans**: TBD

### Phase 20: Adversarial v4 Generator
**Goal**: Users can generate behavioral adversarial scenarios where ground truth is assigned from context signals — not the deceptive narrative — and these scenarios are distinguishable from v2 signal-conflict adversarials
**Depends on**: Phase 18
**Requirements**: ADV-01, ADV-02, ADV-03, ADV-04
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track adversarial_v4 --n 50 --seed 42` produces 50 scenarios where `_meta.adversarial_type` is one of `loitering_as_waiting`, `authorized_as_intrusion`, or `environmental_as_human`
  2. All 3 behavioral adversarial pattern types appear in a generation batch of 50 scenarios (no single type dominates 100%)
  3. Running `--seed 42 --track adversarial_v4` twice produces byte-identical output, and running `--seed 42 --track standard` continues to produce the same output as it did in v3.0 (isolated RNG confirmed)
  4. `_meta.adversarial_type` for a v2 scenario reads `signal_conflict`; for a v4 scenario reads one of the 3 behavioral types — never mixed
**Plans**: TBD

### Phase 21: Multi-Site Generalization
**Goal**: Users can measure how well a system trained on one site type generalizes to another, and confidence in that metric is backed by a leakage audit confirming site identity is not inferable from non-site features
**Depends on**: Phase 19
**Requirements**: SITE-01, SITE-02, SITE-03, SCORE-04
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track standard --n 300 --seed 42 --site-type commercial` produces only scenarios with `context.site_type == "commercial"` and the same seed without `--site-type` produces the full superset (post-generation filter, seed-safe)
  2. A logistic regression probe trained on non-site features (description, category, time, weather) to predict `site_type` scores at or below 60% accuracy — confirming no structural site leakage from non-site fields
  3. `psai-bench site-generalization --train solar --test commercial --outputs outputs.json` produces a per-site accuracy table and a generalization gap value
  4. `compute_site_generalization_gap()` is implemented in scorer.py alongside the existing scoring functions, not in a separate module
**Plans**: TBD

### Phase 22: CLI Integration, Tests, and Documentation
**Goal**: All v4.0 features are wired, tested, and documented — the full test suite passes with no regressions, and users have a complete reference for dispatch scoring and the updated evaluation protocol
**Depends on**: Phase 20, Phase 21
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, DOC-02
**Success Criteria** (what must be TRUE):
  1. `pytest` exits 0 with all 238 existing tests plus new v4.0 tests passing — no regressions on any v1/v2/v3 fixture
  2. A v1.0 output file (no `dispatch` field) scored with `score_run()` produces the same result as in v3.0; scored with `score_dispatch_run()` raises a clear error or returns a report indicating no dispatch data
  3. An end-to-end integration test runs: generate v4.0 scenarios → run a baseline → call `score_dispatch_run()` → assert `cost_ratio` is a positive float and `per_action_breakdown` has entries for all 5 dispatch classes
  4. `EVALUATION_PROTOCOL.md` documents dispatch scoring, the cost model, configurable cost profiles, and the multi-site generalization protocol with the leakage audit results
**Plans**: TBD

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 18. Schema and Cost Model Foundation | 0/2 | Not started | - |
| 19. Scoring Pipeline and Baselines | 0/? | Not started | - |
| 20. Adversarial v4 Generator | 0/? | Not started | - |
| 21. Multi-Site Generalization | 0/? | Not started | - |
| 22. CLI Integration, Tests, and Documentation | 0/? | Not started | - |
