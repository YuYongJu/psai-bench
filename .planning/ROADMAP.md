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
**Plans**: TBD

### Phase 3: Test Coverage Expansion
**Goal**: The test suite covers CLI commands and the statistics module at meaningful levels, and CI will not break on a clean environment due to missing generated data
**Depends on**: Phase 2
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. `pytest --co -q` lists test cases for CLI commands (generate, score, compare, gap) — previously 0 CLI tests
  2. `pytest --cov=psai_bench --cov-report=term-missing` shows statistics module coverage above 80%
  3. All 67 existing tests continue to pass after new tests are added
  4. NumPy version constraint and reproducibility note are documented in pyproject.toml or a REPRODUCIBILITY note
**Plans**: TBD

### Phase 4: GitHub Actions CI
**Goal**: Every push and pull request automatically runs the full test suite across Python 3.10/3.11/3.12 and produces a green badge
**Depends on**: Phase 3
**Requirements**: PKG-02
**Success Criteria** (what must be TRUE):
  1. `.github/workflows/ci.yml` exists and triggers on push and pull_request to main
  2. The Actions tab shows a green check on the latest commit across all three Python version matrix entries
  3. A codecov coverage report is uploaded and a badge URL is available for use in the README
  4. `ruff check .` and `pytest` both run as separate CI steps without failures
**Plans**: TBD

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

### 🚧 v2.0 Fix the Foundation (In Progress)

**Milestone Goal:** Rebuild the benchmark's scientific foundation so results are meaningful — context-dependent ground truth, no single-field leakage, transparent scoring, system-agnostic design.

- [ ] **Phase 6: Scenario Generation Rebuild** - Replace hardcoded GT lookup with a context-dependent decision function and shared description pool
- [ ] **Phase 7: Testing and Verification** - Verify leakage is eliminated, backward compatibility holds, and ambiguous scenario metadata is correct
- [ ] **Phase 8: Decision Rubric Documentation** - Publish the GT assignment logic as a standalone document with worked examples
- [ ] **Phase 9: Scoring and Schema Updates** - Replace opaque aggregate with separate metrics dashboard and simplify output schema
- [ ] **Phase 10: Documentation and Release** - Update README for BYOS workflow, document built-in evaluators as examples, publish v2.0

### Phase 6: Scenario Generation Rebuild
**Goal**: Generated scenarios are non-trivially-solvable — no single field predicts ground truth, descriptions are shared across GT classes, severity is noisy, adversarial cases exist, and site-inappropriate categories are removed
**Depends on**: Phase 5
**Requirements**: SCEN-01, SCEN-02, SCEN-03, SCEN-04, SCEN-06, GT-02, GT-03
**Success Criteria** (what must be TRUE):
  1. Running `psai-bench generate` produces scenarios where the same description text appears across THREAT, SUSPICIOUS, and BENIGN ground truth labels in different contexts
  2. Generated scenarios include cases with HIGH severity + BENIGN ground truth and LOW severity + THREAT ground truth (adversarial pairs are present in output)
  3. Solar farm scenarios contain no shoplifting or road accident categories; indoor facility scenarios contain no road accidents
  4. Scenarios flagged as "ambiguous by design" have `GT=SUSPICIOUS` and an `ambiguity_flag` field present in their `_meta` block
  5. The ground truth assignment function is deterministic: given identical context inputs, it always returns the same label
**Plans**: TBD

### Phase 7: Testing and Verification
**Goal**: Automated tests confirm that leakage is eliminated across all fields, the decision rubric produces expected labels for known configurations, ambiguous scenario metadata is correct, and default parameters still reproduce v1.0-compatible output
**Depends on**: Phase 6
**Requirements**: SCEN-05, SCEN-07, TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. `pytest` includes a test that generates scenarios and asserts every field (description, severity, zone, time, device FPR) achieves less than 70% decision stump accuracy
  2. `pytest` includes tests that assert the GT assignment function returns known-correct labels for a set of fixed scenario configurations
  3. `pytest` includes a test that runs `psai-bench generate --seed 42` with no flags and asserts the output matches v1.0 schema and category distributions
  4. `pytest` includes a test that generates scenarios and asserts all ambiguous-flagged scenarios have `_meta.ambiguity_flag = true` and `GT = SUSPICIOUS`
  5. All new tests pass in CI across Python 3.10/3.11/3.12
**Plans**: TBD

### Phase 8: Decision Rubric Documentation
**Goal**: The ground truth assignment logic is published as a human-readable document so any researcher can audit why a given scenario received its label
**Depends on**: Phase 6
**Requirements**: GT-01
**Success Criteria** (what must be TRUE):
  1. A `docs/decision-rubric.md` (or equivalent) file exists that describes the full decision function: which context signals are used, how they combine, and what threshold/logic produces each GT class
  2. The document contains at least three worked examples — one per GT class (THREAT, SUSPICIOUS, BENIGN) — showing a concrete scenario context and the step-by-step reasoning to its label
  3. The document explicitly calls out the adversarial cases: why HIGH severity can yield BENIGN and why LOW severity can yield THREAT
**Plans**: TBD

### Phase 9: Scoring and Schema Updates
**Goal**: Scoring reports a transparent metrics dashboard instead of a single opaque aggregate, ambiguous scenarios are handled separately, and the output schema accepts minimal non-LLM outputs
**Depends on**: Phase 6
**Requirements**: SCORE-01, SCORE-02, SCORE-03, SCORE-04, SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04
**Success Criteria** (what must be TRUE):
  1. `psai-bench score` outputs a dashboard showing TDR, FASR, Decisiveness, Calibration (ECE), and per-difficulty accuracy as separate labeled values — not a single aggregate number
  2. A Decisiveness metric is present in output, defined as fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS)
  3. If an aggregate score is shown, its formula is printed alongside it with documented weights
  4. `psai-bench score` does not penalize a system that gives THREAT or BENIGN on a scenario flagged as ambiguous — the scoring output shows ambiguous scenarios handled in a separate bucket
  5. A minimal output file containing only `alert_id`, `verdict`, and `confidence` passes schema validation without errors
**Plans**: TBD

### Phase 10: Documentation and Release
**Goal**: The repository communicates the BYOS workflow as the primary path, built-in evaluators are correctly positioned as examples, v2.0 results are accurately represented, and known limitations are honest
**Depends on**: Phase 9
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05
**Success Criteria** (what must be TRUE):
  1. README leads with "Bring Your Own System" workflow: generate scenarios → run your system → score outputs — with a concrete three-step example in the first screen of content
  2. Built-in evaluators section in README (or EVALUATORS.md) states they are reference implementations and example integrations, not the intended path for production use
  3. `docs/decision-rubric.md` is linked from the README (satisfies DOCS-03 publication requirement)
  4. Results table in README reflects v2.0 scenarios or is explicitly removed with a note explaining why (v1.0 results are invalid under new scenarios)
  5. A Known Limitations section exists in README that honestly states what v2.0 does and does not test (e.g., no video track, no multi-annotator GT, 3-class triage only)

## Progress

**Execution Order:**
Phases execute strictly in numeric order: 6 → 7 → 8 → 9 → 10

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Repository Hygiene | v1.0 | 2/2 | Complete | 2026-04-13 |
| 2. Project Metadata + Licensing | v1.0 | ?/? | Complete | 2026-04-13 |
| 3. Test Coverage Expansion | v1.0 | ?/? | Complete | 2026-04-13 |
| 4. GitHub Actions CI | v1.0 | ?/? | Complete | 2026-04-13 |
| 5. Documentation + Release | v1.0 | ?/? | Complete | 2026-04-13 |
| 6. Scenario Generation Rebuild | v2.0 | 0/? | Not started | - |
| 7. Testing and Verification | v2.0 | 0/? | Not started | - |
| 8. Decision Rubric Documentation | v2.0 | 0/? | Not started | - |
| 9. Scoring and Schema Updates | v2.0 | 0/? | Not started | - |
| 10. Documentation and Release | v2.0 | 0/? | Not started | - |
