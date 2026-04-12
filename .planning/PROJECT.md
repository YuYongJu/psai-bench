# PSAI-Bench

## What This Is

PSAI-Bench is an open-source benchmark for evaluating AI models on physical security alert triage. It generates realistic security scenarios (metadata, visual, multi-sensor tracks) grounded in real datasets (UCF Crime, Caltech Pedestrian) and scores model outputs on safety-weighted metrics. The core research contribution is measuring the "perception-reasoning gap" — whether frontier models actually benefit from video data or just reason about contextual metadata.

## Core Value

Provide a rigorous, reproducible benchmark that reveals whether AI video analysis adds real value to physical security triage — or whether models are just reasoning about metadata.

## Current Milestone: v1.0 Open-Source Release

**Goal:** Make PSAI-Bench publishable on GitHub and presentable on LinkedIn as a polished open-source benchmark.

**Target features:**
- Fix all lint errors and clean up code quality
- Add proper project metadata (authors, classifiers, URLs)
- Create comprehensive documentation (README with results, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT)
- Clean repository hygiene (gitignore generated data, make everything reproducible)
- Add GitHub Actions CI/CD (tests, lint, coverage)
- Improve test coverage (CLI, statistics, integration tests)
- Final polish (version bump, CHANGELOG, clean install verification)

## Requirements

### Validated

- ✓ 3-track scenario generation (metadata, visual, multi-sensor) — v1.0rc1
- ✓ Safety-weighted scoring engine (TDR, FASR, ECE, Brier, aggregate) — v1.0rc1
- ✓ 4 statistical baselines (random, majority, always-suspicious, severity heuristic) — v1.0rc1
- ✓ Frontier model evaluators (Claude, GPT-4o, Gemini Flash) — v1.0rc1
- ✓ McNemar's test and bootstrap CIs for system comparison — v1.0rc1
- ✓ Perception-reasoning gap analysis CLI — v1.0rc1
- ✓ 67 passing tests covering schema, generators, scorer, baselines, validation — v1.0rc1

### Active

- [ ] Code quality (lint clean, no unused imports)
- [ ] Project metadata (authors, URLs, classifiers in pyproject.toml)
- [ ] README.md with results table, architecture, quickstart, citation
- [ ] LICENSE file (Apache-2.0)
- [ ] CONTRIBUTING.md and CODE_OF_CONDUCT.md
- [ ] Repository hygiene (generated data out of git, reproducible)
- [ ] GitHub Actions CI (tests, lint, coverage)
- [ ] Expanded test coverage (CLI, statistics, integration)
- [ ] Version bump to 1.0.0 and CHANGELOG.md

### Out of Scope

- Running additional model evaluations (Claude, Gemini) — cost and time, not needed for release
- Visual track model evaluations — future research work
- Web dashboard or visualization UI — benchmark is CLI-first
- Paper writing — separate effort, README serves as intro

## Context

- Single commit repo at v1.0rc1, all code by one author
- 67/67 tests pass, 47% overall coverage (core logic well-tested, CLI/downloader/video_mapper untested)
- 12 ruff lint errors (auto-fixable)
- 16MB generated JSON data + 16MB results currently tracked in git
- One GPT-4o evaluation on UCF metadata completed
- Built with: Python 3.10+, numpy, pandas, scikit-learn, click, jsonschema, matplotlib
- Datasets: UCF Crime (real videos via HuggingFace), Caltech Pedestrian (synthetic metadata)

## Constraints

- **License**: Apache-2.0 (already declared, need file)
- **Python**: >=3.10 (type union syntax used)
- **Dependencies**: Minimize — API clients are optional extras
- **Data**: Generated data must be reproducible from seed, not committed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Apache-2.0 license | Permissive, standard for academic tools | — Pending |
| Keep results/ in repo as examples | Useful for users to see expected output format | — Pending |
| Generated data out of git | 16MB+ bloats repo, reproducible via `psai-bench generate` | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-12 after milestone v1.0 initialization*
