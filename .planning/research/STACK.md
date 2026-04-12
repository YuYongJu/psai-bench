# Stack Research

**Domain:** Open-source Python benchmark/CLI tool — GitHub publication packaging
**Researched:** 2026-04-12
**Confidence:** HIGH (versions verified against PyPI and GitHub releases)

## Recommended Stack

### Core Technologies (additions to existing stack)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| ruff | `>=0.8,<1.0` | Lint + format (replaces flake8, black, isort) | Already in dev deps but pinned too loosely (`>=0.1`). Ruff is the standard for new Python projects — single tool for lint and format. Current: 0.15.10. |
| GitHub Actions | — | CI matrix across Python 3.10/3.11/3.12 | Native GitHub integration, free for public repos, zero infrastructure. The matrix replaces tox/nox entirely. |
| codecov-action | `v5` | Coverage badge + PR diff annotations | v5 is current stable; public repos can opt out of token requirement. Gives the coverage badge without managing a separate service. |
| pre-commit | `>=3.5` | Enforce ruff on commit for contributors | Two hooks (`ruff-check`, `ruff-format`), zero contributor friction. Keeps PRs clean before CI runs. |

### Supporting Libraries (already in pyproject.toml, version notes only)

| Library | Current Pin | Recommendation | Notes |
|---------|-------------|---------------|-------|
| pytest | `>=7.0` | `>=7.4` | 7.4 fixes several fixture edge cases; 8.x is stable but 7.4 is safer for broad compat |
| pytest-cov | `>=4.0` | keep | Fine as-is |
| numpy | `>=1.24` | keep | Fine for Python 3.10+ floor |
| pandas | `>=2.0` | keep | Fine |
| setuptools | `>=68` (build) | keep | Still the right build backend for this project size; no reason to switch to hatchling |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `actions/checkout` | CI: checkout code | Pin to `@v4` |
| `actions/setup-python` | CI: install Python matrix | Pin to `@v5` |
| `codecov/codecov-action` | CI: upload coverage report | Pin to `@v5`; no token needed for public repos (opt-out enabled) |
| shields.io | Static badges in README | No account needed, generates SVG badges from URL parameters |

## Installation

```bash
# Update dev extras in pyproject.toml (see pyproject.toml changes below)
pip install -e ".[dev]"

# Install pre-commit hooks (one-time per dev machine)
pip install pre-commit
pre-commit install
```

## pyproject.toml Changes Needed

```toml
# 1. Fix readme to point to file (currently inline text)
readme = "README.md"

# 2. Add authors and URLs
authors = [
    {name = "Your Name", email = "you@example.com"}
]
[project.urls]
Homepage = "https://github.com/YuYongJu/psai-bench"
Repository = "https://github.com/YuYongJu/psai-bench"
Issues = "https://github.com/YuYongJu/psai-bench/issues"

# 3. Add PyPI classifiers
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

# 4. Tighten ruff pin in dev extras
[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.0",
    "ruff>=0.8",
    "pre-commit>=3.5",
]

# 5. Add ruff lint config (currently only line-length is set)
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "W"]
# E = pycodestyle errors, F = pyflakes, I = isort, UP = pyupgrade, W = warnings
```

## GitHub Actions Workflow

`.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: ruff format --check .
      - run: pytest --cov=psai_bench --cov-report=xml
      - uses: codecov/codecov-action@v5
        if: matrix.python-version == '3.12'   # upload once, not 3x
        with:
          files: ./coverage.xml
```

## pre-commit Config

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.10
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
```

## README Badges

```markdown
[![CI](https://github.com/YuYongJu/psai-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/YuYongJu/psai-bench/actions)
[![codecov](https://codecov.io/gh/YuYongJu/psai-bench/branch/main/graph/badge.svg)](https://codecov.io/gh/YuYongJu/psai-bench)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/psai-bench)](https://pypi.org/project/psai-bench/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
```

Note: PyPI version badge only relevant if publishing to PyPI. The Python version and license badges work with shields.io static parameters without PyPI publication.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| ruff (lint + format) | black + flake8 + isort | Never for new projects; ruff subsumes all three faster |
| GitHub Actions matrix | tox / nox | When you need local multi-version testing; for CI-only, GHA matrix is sufficient |
| codecov | coveralls | If already using coveralls ecosystem; codecov is more feature-rich for public repos |
| setuptools | hatchling | For new projects without existing setuptools config; not worth migrating here |
| README-only docs | mkdocs / sphinx | When building an API library with many public functions; benchmark CLI doesn't need it |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| mypy / pyright | numpy/pandas type stubs are painful; research code has dynamic patterns that generate false positives; ROI is low for a benchmark tool | ruff's UP rules catch real modernization issues without type annotation overhead |
| tox / nox | Adds a dependency and config layer that GHA matrix already handles | GitHub Actions matrix with `python-version: ["3.10", "3.11", "3.12"]` |
| sphinx / mkdocs / readthedocs | Over-engineering for a CLI benchmark; docs sites require ongoing maintenance | Comprehensive README with results table, quickstart, and citation block |
| semantic-release / commitizen | Automated changelog tooling adds friction for a single-author research tool | Manual version bumps in pyproject.toml + hand-written CHANGELOG.md |
| Docker | pip install is the correct distribution for a benchmark tool | `pip install psai-bench` or `pip install -e .` |
| PyPI publish action | Project scope is GitHub publication, not PyPI distribution | Ship the wheel/sdist manually if needed; don't automate until there's demand |
| dependabot (Python) | Dependency PRs for a research benchmark create noise without value | Pin ranges in pyproject.toml, update manually at milestone boundaries |

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| ruff 0.15.x | Python 3.10–3.12 | Ruff itself runs on any Python; rules target the project's floor |
| pytest 7.4+ | Python 3.10–3.12 | pytest 8.x also works; 7.4 is safer if contributors have older toolchains |
| codecov-action v5 | GitHub Actions runner (ubuntu-latest) | v6 requires node24, planned but not yet released; v5 is stable |

## Sources

- [ruff PyPI page](https://pypi.org/project/ruff/) — version 0.15.10 confirmed current (April 9, 2026)
- [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit) — pre-commit hook rev v0.15.10 confirmed
- [codecov/codecov-action GitHub](https://github.com/codecov/codecov-action) — v5 confirmed current stable; v6 (node24) planned but not released
- [GitHub Marketplace: codecov-action](https://github.com/marketplace/actions/codecov) — public repo token opt-out confirmed in v5

---
*Stack research for: PSAI-Bench open-source release packaging*
*Researched: 2026-04-12*
