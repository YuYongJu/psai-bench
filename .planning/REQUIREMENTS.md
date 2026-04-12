# Requirements: PSAI-Bench

**Defined:** 2026-04-12
**Core Value:** Rigorous benchmark revealing whether AI video analysis adds real value to physical security triage

## v1 Requirements

Requirements for open-source release. Each maps to roadmap phases.

### Repository Hygiene

- [ ] **REPO-01**: All ruff lint errors fixed (12 errors: unused imports, f-strings, unused variable)
- [ ] **REPO-02**: Generated data removed from git tracking and .gitignore updated (data/generated/, .coverage, .ruff_cache/, *.egg-info/)
- [ ] **REPO-03**: Git history rewritten to purge 16MB of generated JSON before public push

### Documentation

- [ ] **DOCS-01**: README.md with research claim lead, results table, quickstart, architecture overview, BibTeX citation, 3 badges (Python version, License, CI status)
- [ ] **DOCS-02**: LICENSE file with full Apache-2.0 text
- [ ] **DOCS-03**: CONTRIBUTING.md with development setup, testing instructions, and PR guidelines
- [ ] **DOCS-04**: CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- [ ] **DOCS-05**: CHANGELOG.md documenting v1.0 release

### Packaging

- [ ] **PKG-01**: pyproject.toml updated with authors, project URLs, classifiers, keywords, readme=README.md, tightened ruff pin
- [ ] **PKG-02**: GitHub Actions CI workflow (pytest + ruff on Python 3.10/3.11/3.12, coverage upload to codecov)
- [ ] **PKG-03**: Pre-commit configuration with ruff-check and ruff-format hooks

### Quality

- [ ] **QUAL-01**: Test coverage expanded for CLI commands (from 0% to meaningful coverage)
- [ ] **QUAL-02**: Test coverage expanded for statistics module (from 48% to >80%)
- [ ] **QUAL-03**: NumPy RNG version documented or pinned for reproducible scenario generation

### Release

- [ ] **REL-01**: Version bumped from 1.0.0rc1 to 1.0.0
- [ ] **REL-02**: Clean install from scratch verified (pip install . works, psai-bench CLI functional, all tests pass)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Evaluations

- **EVAL-01**: Run Claude Sonnet and Gemini Flash evaluations on metadata track
- **EVAL-02**: Run visual track evaluations to measure perception-reasoning gap
- **EVAL-03**: Multi-run consistency analysis (5 runs per model)

### Publication

- **PUB-01**: PyPI package publication with publish workflow
- **PUB-02**: arXiv preprint submission
- **PUB-03**: Interactive results leaderboard

## Out of Scope

| Feature | Reason |
|---------|--------|
| Jupyter notebooks | Maintenance burden without proportional value for CLI-first tool |
| Sphinx/mkdocs documentation site | Over-engineering for a benchmark tool; README is sufficient |
| Web dashboard | CLI-first design; not needed for v1.0 |
| OAuth/API key management UI | CLI env vars are standard for benchmark tools |
| Docker containerization | pip install is sufficient for Python package |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REPO-01 | Phase 1 | Pending |
| REPO-02 | Phase 1 | Pending |
| REPO-03 | Phase 1 | Pending |
| DOCS-02 | Phase 2 | Pending |
| PKG-01 | Phase 2 | Pending |
| PKG-03 | Phase 2 | Pending |
| QUAL-01 | Phase 3 | Pending |
| QUAL-02 | Phase 3 | Pending |
| QUAL-03 | Phase 3 | Pending |
| PKG-02 | Phase 4 | Pending |
| DOCS-01 | Phase 5 | Pending |
| DOCS-03 | Phase 5 | Pending |
| DOCS-04 | Phase 5 | Pending |
| DOCS-05 | Phase 5 | Pending |
| REL-01 | Phase 5 | Pending |
| REL-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-12*
*Last updated: 2026-04-12 after initial definition*
