# Roadmap: PSAI-Bench

## Milestones

- ✅ **v1.0 Release** - Phases 1-5 (shipped 2026-04-13)
- ✅ **v2.0 Fix the Foundation** — Phases 6-10 (shipped 2026-04-13)
- 🚧 **v3.0 Perception-Reasoning Gap** — Phases 11-17 (in progress)

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

### 🚧 v3.0 Perception-Reasoning Gap (In Progress)

**Milestone Goal:** Add visual-only, contradictory, and temporal scenario tracks plus a perception-reasoning gap metric — making the benchmark genuinely publishable as a multi-modal evaluation tool.

- [x] **Phase 11: Schema v3** - Extend schema with new tracks, relax required fields for visual tracks, add _meta v3 fields, pin seed-42 regression hash (completed 2026-04-13)
- [x] **Phase 12: Visual-Only Scenarios** - Build VisualOnlyGenerator with UCF Crime-based GT derivation and leakage-safe field population (completed 2026-04-13)
- [x] **Phase 13: Contradictory Scenarios** - Build ContradictoryGenerator with video-derived GT, dual GT storage, and contradictory description pools (completed 2026-04-13)
- [x] **Phase 14: Temporal Sequences** - Build TemporalSequenceGenerator with escalation narrative patterns and sequence threading (completed 2026-04-13)
- [x] **Phase 15: Scoring Updates** - Add track partitioning, score_sequences(), and perception-reasoning gap metric without modifying score_run() (completed 2026-04-13)
- [ ] **Phase 16: CLI Extensions** - Extend --track choices and add score-sequences, analyze-frame-gap subcommands
- [ ] **Phase 17: Evaluation Protocol** - Write docs/EVALUATION_PROTOCOL.md documenting GT definitions, scoring protocol, and frame extraction baseline

## Phase Details

### Phase 11: Schema v3
**Goal**: The schema supports all three new tracks with backward-compatible field definitions and the seed-42 regression is pinned before any generator touches the RNG stream
**Depends on**: Phase 10
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, TEST-01, TEST-05
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track visual_only` is accepted by the CLI argument parser (track enum extended)
  2. An existing v2.0 scenario dict validates against the updated ALERT_SCHEMA without errors — no required fields removed or changed
  3. A v3 scenario with `_meta.visual_gt_source`, `_meta.contradictory`, `_meta.sequence_id`, and `_meta.sequence_position` validates without schema errors
  4. `pytest` exits 0 with all 133 existing tests passing after schema changes are applied
  5. `generate_ucf_crime(seed=42)` output hash matches the pinned regression value in a dedicated test
**Plans**: 2 plans

Plans:
- [x] 11-01-PLAN.md — Pin seed-42 regression hash (tests/test_seed_regression.py)
- [x] 11-02-PLAN.md — Extend schema track enum, relax required, add _meta v3 fields, track-aware validation

### Phase 12: Visual-Only Scenarios
**Goal**: Users can generate visual-only scenarios where ground truth is derived from video content labels, not metadata signals, and existing leakage tests pass on the visual-only subset
**Depends on**: Phase 11
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04, TEST-02
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track visual_only --count 100` produces a scenario file where every scenario has a video URI and camera ID but no description or severity derived from metadata signals
  2. Each visual-only scenario's `_meta.visual_gt_source` equals `"video_category"` and GT matches the UCF Crime category mapping
  3. `test_leakage.py` passes on a visual-only scenario batch — no single field achieves >70% stump accuracy in predicting GT
  4. `VisualOnlyGenerator(seed=42)` produces identical output on two consecutive runs (RNG isolation confirmed)
**Plans**: 1 plan

Plans:
- [x] 12-01-PLAN.md — Implement VisualOnlyGenerator (generators.py + cli.py) and test suite (conftest.py + test_visual_only.py)

### Phase 13: Contradictory Scenarios
**Goal**: Users can generate contradictory scenarios where metadata and video content deliberately disagree and GT always follows the video content label
**Depends on**: Phase 12
**Requirements**: CONTRA-01, CONTRA-02, CONTRA-03, CONTRA-04, TEST-03
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track visual_contradictory --count 100` produces a scenario file where every scenario has `_meta.contradictory = True`
  2. Both overreach (metadata=THREAT, video=BENIGN) and underreach (metadata=BENIGN, video=THREAT) sub-types appear in generated batches
  3. An automated test asserts that `metadata_derived_gt != video_derived_gt` for all contradictory scenarios — no scenario has aligned metadata and video GT
  4. Contradictory description pools are present in `distributions.py` with plausible-but-wrong descriptions (not obviously wrong)
**Plans**: 2 plans

Plans:
- [x] 13-01-PLAN.md — Add description pools (CONTRADICTORY_THREAT_DESCRIPTIONS, CONTRADICTORY_BENIGN_DESCRIPTIONS) and implement ContradictoryGenerator in generators.py
- [x] 13-02-PLAN.md — Tests (conftest.py + test_contradictory.py) and CLI wiring (replace visual_contradictory UsageError stub)

### Phase 14: Temporal Sequences
**Goal**: Users can generate temporal alert sequences of 3-5 related alerts with escalation narrative patterns threaded by sequence_id
**Depends on**: Phase 11
**Requirements**: TEMP-01, TEMP-02, TEMP-04
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track temporal --count 50` produces a scenario file where alerts share `sequence_id` values in groups of 3-5 with monotonically increasing timestamps
  2. All three escalation pattern types appear in generated batches: monotonic escalation, escalation-then-resolution, and false alarm sequence
  3. `sequence_position` values within each group are unique integers starting at 1 — no duplicate positions within a sequence
  4. Escalation point varies across sequences (not always alert 2 of 5) — a position-stump leakage test passes
**Plans**: 1 plan

Plans:
- [x] 14-01-PLAN.md — Implement TemporalSequenceGenerator with isolated RNG, sequence threading, and all three escalation pattern types

### Phase 15: Scoring Updates
**Goal**: The scoring dashboard partitions results by track, score_sequences() measures sequence evaluation metrics, and the perception-reasoning gap is computable — all without modifying score_run()
**Depends on**: Phases 12, 13, 14
**Requirements**: SCORE-01, SCORE-02, SCORE-03, SCORE-04, TEMP-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. `psai-bench score results.json` displays per-track TDR and FASR breakdowns (metadata, visual_only, visual_contradictory, temporal) when multiple tracks are present
  2. `score_sequences(results)` returns a `SequenceScoreReport` with escalation latency, correct-escalation rate, and correct-resolution rate for a temporal scenario batch
  3. Perception-reasoning gap metric is computed and displayed when both metadata-track and visual-track results exist in the same results file
  4. All 133 existing tests pass with zero modifications to `score_run()` — the function signature and behavior are unchanged
  5. Track-specific required field validation rejects a visual_only scenario missing `visual_data.uri` with an informative error
**Plans**: 2 plans

Plans:
- [x] 15-01-PLAN.md — SequenceScoreReport, score_sequences(), format_dashboard track partitioning
- [x] 15-02-PLAN.md — compute_perception_gap(), Phase 15 regression test suite

### Phase 16: CLI Extensions
**Goal**: Users can invoke all three new generators from the CLI and compute the frame extraction baseline gap without any code changes
**Depends on**: Phases 15
**Requirements**: FRAME-01, FRAME-02, FRAME-03
**Success Criteria** (what must be TRUE):
  1. `psai-bench generate --track [visual_only|visual_contradictory|temporal] --help` shows valid options and exits 0
  2. `psai-bench score-sequences results.json` runs against a temporal results file and prints a SequenceScoreReport summary
  3. `psai-bench analyze-frame-gap metadata_results.json visual_results.json` computes and prints the perception-reasoning gap metric
**Plans**: 2 plans

Plans:
- [ ] 16-01: Extend --track choices; add score-sequences and analyze-frame-gap CLI subcommands; add opencv-python-headless to [visual] optional group in pyproject.toml

### Phase 17: Evaluation Protocol
**Goal**: A researcher can understand exactly how to evaluate any system against all four tracks using only the published documentation
**Depends on**: Phase 16
**Requirements**: PROTO-01
**Success Criteria** (what must be TRUE):
  1. `docs/EVALUATION_PROTOCOL.md` exists and defines GT derivation rules for all four tracks (metadata, visual_only, visual_contradictory, temporal) with worked examples
  2. The document specifies the frame extraction baseline procedure: uniform N-frame sampling, never using anomaly_segments for selection, deterministic given seed
  3. The document explains which scoring function applies to which track (score_run vs score_sequences) and how to interpret cross-track comparisons
**Plans**: 2 plans

Plans:
- [ ] 17-01: Write docs/EVALUATION_PROTOCOL.md with GT definitions, scoring protocol, and frame extraction baseline specification

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Repository Hygiene | v1.0 | 2/2 | Complete | 2026-04-13 |
| 2. Project Metadata + Licensing | v1.0 | 3/3 | Complete | 2026-04-13 |
| 3. Test Coverage Expansion | v1.0 | 3/3 | Complete | 2026-04-13 |
| 4. GitHub Actions CI | v1.0 | 3/3 | Complete | 2026-04-13 |
| 5. Documentation + Release | v1.0 | 3/3 | Complete | 2026-04-13 |
| 6-10. v2.0 Foundation | v2.0 | 9/9 | Complete | 2026-04-13 |
| 11. Schema v3 | v3.0 | 2/2 | Complete    | 2026-04-13 |
| 12. Visual-Only Scenarios | v3.0 | 1/1 | Complete    | 2026-04-13 |
| 13. Contradictory Scenarios | v3.0 | 2/2 | Complete    | 2026-04-13 |
| 14. Temporal Sequences | v3.0 | 1/1 | Complete    | 2026-04-13 |
| 15. Scoring Updates | v3.0 | 2/2 | Complete    | 2026-04-13 |
| 16. CLI Extensions | v3.0 | 0/1 | Not started | - |
| 17. Evaluation Protocol | v3.0 | 0/1 | Not started | - |
