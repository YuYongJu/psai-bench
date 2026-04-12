# Architecture Research

**Domain:** Python ML benchmark — open-source release packaging
**Researched:** 2026-04-12
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│                  psai_bench/cli.py (click)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌───────────┐  ┌────────────────────┐    │
│  │  generators  │  │ evaluators│  │     baselines      │    │
│  │ (scenarios)  │  │(Claude/   │  │ (random, majority, │    │
│  │              │  │ GPT/Gemini│  │  heuristic)        │    │
│  └──────┬───────┘  └─────┬─────┘  └─────────┬──────────┘    │
│         │                │                  │               │
├─────────┴────────────────┴──────────────────┴───────────────┤
│                     Core Engine                              │
│  ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐  │
│  │  scorer  │  │statistics │  │ validation │  │  schema  │  │
│  │(TDR/FASR │  │(McNemar's,│  │(jsonschema)│  │(dataclass│  │
│  │ ECE/Brier│  │ bootstrap)│  │            │  │ types)   │  │
│  └──────────┘  └───────────┘  └────────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Data Layer                               │
│  ┌─────────────────┐  ┌────────────────────────────────┐    │
│  │  distributions  │  │  downloader / video_mapper     │    │
│  │ (UCF/Caltech    │  │  (HuggingFace dataset fetch,   │    │
│  │  label priors)  │  │   frame extraction)            │    │
│  └─────────────────┘  └────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Existing Module Responsibilities

| Module | Responsibility | Status |
|--------|----------------|--------|
| `cli.py` | Click command group: generate, evaluate, score, compare, analyze | Exists, untested |
| `generators.py` | 3-track scenario generation (metadata, visual, multi-sensor) | Exists, tested |
| `evaluators.py` | API calls to Claude / GPT-4o / Gemini, response parsing | Exists, untested |
| `baselines.py` | 4 deterministic baselines for statistical comparison | Exists, tested |
| `scorer.py` | Safety-weighted metrics (TDR, FASR, ECE, Brier, aggregate) | Exists, tested |
| `statistics.py` | McNemar's test, bootstrap CIs, perception-reasoning gap | Exists, untested |
| `validation.py` | jsonschema-based scenario and response validation | Exists, tested |
| `schema.py` | Dataclass types and JSON schema definitions | Exists, tested |
| `distributions.py` | UCF Crime / Caltech label priors and sampling weights | Exists, tested |
| `downloader.py` | HuggingFace dataset fetch, caching | Exists, untested |
| `video_mapper.py` | Frame extraction, visual track construction | Exists, untested |

## Recommended Project Structure

The existing flat structure is correct for a Python package. The release adds tooling and documentation layers:

```
psai-bench/
├── psai_bench/                # Existing — Python package (unchanged)
│   ├── __init__.py
│   ├── cli.py
│   ├── generators.py
│   ├── evaluators.py
│   ├── baselines.py
│   ├── scorer.py
│   ├── statistics.py
│   ├── validation.py
│   ├── schema.py
│   ├── distributions.py
│   ├── downloader.py
│   └── video_mapper.py
├── tests/                     # Existing — expand coverage
│   ├── test_core.py           # Existing (67 tests)
│   ├── test_cli.py            # NEW — CLI integration tests
│   └── test_statistics.py     # NEW — McNemar's, bootstrap CIs
├── results/                   # Existing — keep in git as reference output
│   ├── baselines/
│   └── evaluations/
├── data/                      # Partially gitignored
│   ├── generated/             # MODIFY gitignore to exclude (16MB, reproducible)
│   └── raw/                   # Already gitignored
├── .github/                   # NEW directory
│   └── workflows/
│       └── ci.yml             # NEW — test matrix + lint + coverage
├── pyproject.toml             # MODIFY — add authors, urls, classifiers, ruff lint config, readme pointer
├── .gitignore                 # MODIFY — add data/generated/, .coverage, .ruff_cache/, .pytest_cache/
├── README.md                  # NEW — quickstart, results table, citation, CI badge
├── LICENSE                    # NEW — Apache-2.0 text
├── CONTRIBUTING.md            # NEW — how to add evaluators, datasets, or metrics
├── CODE_OF_CONDUCT.md         # NEW — Contributor Covenant boilerplate
└── CHANGELOG.md               # NEW — single entry: v1.0.0 initial release
```

### Structure Rationale

- **No `src/` layout:** Existing flat layout (`psai_bench/` at root) works. Converting to `src/` layout for a v1.0 release would break the existing editable install and provides no benefit for a single-package benchmark.
- **`results/` stays in git:** Intentional — users benefit from seeing expected output format without running evaluations. Keep but document in README.
- **`data/generated/` leaves git:** Currently 16MB tracked; these are deterministic outputs of `psai-bench generate --seed 42` and have no place in version control.
- **Single workflow file:** One `ci.yml` is sufficient. A separate `release.yml` is out of scope — this project doesn't publish to PyPI.

## Architectural Patterns

### Pattern 1: CI Workflow Structure

**What:** GitHub Actions matrix testing with lint, test, and coverage gates.
**When to use:** All Python OSS projects with `>=3.10` requirement.
**Trade-offs:** Matrix increases CI time 3x, but validates the `requires-python` claim actually holds.

```yaml
# .github/workflows/ci.yml skeleton
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
      - run: pip install ".[dev]"        # NOT .[dev,api] — no real API calls in CI
      - run: ruff check .
      - run: pytest --cov=psai_bench --cov-fail-under=45
```

**Critical:** Install only `.[dev]`, never `.[dev,api]`. The `api` extras (anthropic, openai, google-genai) would hit live APIs and require secrets. All evaluator tests must be skipped or mocked.

### Pattern 2: pyproject.toml Metadata Completion

**What:** Augment the existing `[project]` table with the fields required for a credible OSS release.
**When to use:** Before publishing to any public platform or linking from papers/blog posts.

```toml
[project]
# Change inline text to file reference (requires README.md to exist first):
readme = "README.md"

# Add these sections:
authors = [{name = "Addison Apisarnthanarax", email = "..."}]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
[project.urls]
Homepage = "https://github.com/YuYongJu/psai-bench"
Repository = "https://github.com/YuYongJu/psai-bench"

# Add ruff lint config (required for CI ruff check to be meaningful):
[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = []
```

### Pattern 3: .gitignore Cleanup + Cache Removal

**What:** Remove currently-tracked artifacts that should never have been committed, update gitignore to prevent recurrence.
**When to use:** Before the repo goes public — once public, history is visible.

Files to `git rm --cached` (tracked but should not be):
- `data/generated/` (3 JSON files, ~16MB)
- `psai_bench.egg-info/` (build artifact directory)
- `.coverage` (test coverage database)
- `.ruff_cache/` (linter cache)

Additions to `.gitignore`:
```gitignore
# Generated benchmark data (reproducible via: psai-bench generate --seed 42)
data/generated/

# Build artifacts
*.egg-info/

# Test and lint caches
.coverage
.pytest_cache/
.ruff_cache/
```

## Data Flow

### Benchmark Execution Flow

```
psai-bench generate --dataset ucf --seed 42
    ↓
generators.py → distributions.py → data/generated/*.json

psai-bench evaluate --model gpt-4o --scenarios data/generated/metadata_ucf_seed42.json
    ↓
evaluators.py → [OpenAI API] → validation.py → results/evaluations/*.json

psai-bench score --results results/evaluations/gpt-4o_ucf_metadata_run1.json
    ↓
scorer.py → statistics.py → tabular output (stdout)

psai-bench compare --baseline results/baselines/ --model results/evaluations/
    ↓
statistics.py → McNemar's test + bootstrap CIs → stdout
```

### CI Flow

```
git push
    ↓
ci.yml: checkout → setup-python (3.10/3.11/3.12)
    ↓
pip install .[dev]   (no api extras)
    ↓
ruff check .         (lint gate — must pass before tests run)
    ↓
pytest --cov=psai_bench --cov-fail-under=45
    ↓
[pass/fail badge → README.md]
```

## Integration Points

### New Files and Their Dependencies

| New File | Depends On | Blocks |
|----------|------------|--------|
| `LICENSE` | Nothing | Nothing (independent) |
| `CONTRIBUTING.md` | Nothing | Nothing (independent) |
| `CODE_OF_CONDUCT.md` | Nothing | Nothing (independent) |
| `CHANGELOG.md` | Final version number | Version bump |
| `.github/workflows/ci.yml` | Lint-clean code, `[tool.ruff.lint]` in pyproject.toml | README CI badge |
| `README.md` | CI badge URL, clean test run, results/ content | pyproject.toml `readme = "README.md"` |
| `pyproject.toml` (readme field) | `README.md` exists | Nothing |

### Modified Files and What Changes

| Modified File | Change | Dependency |
|---------------|--------|------------|
| `pyproject.toml` | Add authors, classifiers, urls, ruff lint config | Must add `[tool.ruff.lint]` before CI lint step |
| `pyproject.toml` | Change `readme = {text=...}` to `readme = "README.md"` | README.md must exist first |
| `.gitignore` | Add data/generated/, .coverage, .ruff_cache/, .pytest_cache/ | Must run `git rm --cached` in same commit |
| `tests/test_core.py` | Expand or split — add CLI tests, statistics tests | Lint must be clean first |

### Build Order (Dependency-Constrained)

Phase work should follow this order to avoid blocked states:

1. **Lint fixes + .gitignore + git rm cached artifacts** — No dependencies. Unblocks CI. Run `ruff check --fix .` then `git rm --cached` the artifact directories.

2. **pyproject.toml metadata** — Add authors, classifiers, urls, `[tool.ruff.lint]` config. Change `readme` field ONLY after README.md exists (do in same commit or use placeholder initially).

3. **License + community files** — `LICENSE` (Apache-2.0 boilerplate), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`. No dependencies, no ordering constraints among the three.

4. **Test coverage expansion** — Add `tests/test_cli.py` and `tests/test_statistics.py`. Depends on lint being clean so CI doesn't fail at the lint step before reaching tests.

5. **GitHub Actions CI** — `ci.yml` with Python 3.10/3.11/3.12 matrix. Depends on lint-clean code and `[tool.ruff.lint]` in pyproject.toml. Verifying locally first (`act` or manual push to branch) recommended.

6. **README.md** — Write last among the documentation. Requires: clean CI run (for badge status), results/ content (for results table), finalized project metadata (for install instructions). README enables the `readme = "README.md"` pyproject change.

7. **CHANGELOG.md + version bump** — Single entry: v1.0.0. Bump `version` in pyproject.toml from `1.0.0rc1` to `1.0.0`. This is the final gate before the release commit.

## Anti-Patterns

### Anti-Pattern 1: Installing API Extras in CI

**What people do:** `pip install ".[dev,api]"` in CI to get full dependency coverage.
**Why it's wrong:** evaluators.py makes real API calls to OpenAI/Anthropic/Google. CI has no API keys, so evaluator tests will fail or be skipped, and the install wastes time/bandwidth.
**Do this instead:** Install only `.[dev]`. Mark any evaluator tests with `@pytest.mark.skipif` or `pytest.importorskip` for API clients. If evaluator unit tests are added, mock the HTTP layer with `unittest.mock`.

### Anti-Pattern 2: Setting Coverage Threshold Too High Initially

**What people do:** Set `--cov-fail-under=80` immediately on a project with 47% coverage.
**Why it's wrong:** CI fails from day one, is immediately disabled or `--no-cov`, and the threshold becomes a fiction.
**Do this instead:** Set threshold at current level minus 2 points (`--cov-fail-under=45`). Ratchet up as tests are added. This makes the threshold a regression guard, not an aspirational lie.

### Anti-Pattern 3: Committing pyproject.toml readme Change Before README Exists

**What people do:** Update `readme = "README.md"` in pyproject.toml in a separate commit before the README file exists.
**Why it's wrong:** `pip install .` and build tools will error on missing readme file. Users cloning mid-history get a broken install.
**Do this instead:** The pyproject.toml `readme` field change and README.md creation must land in the same commit.

## Sources

- Python Packaging User Guide (packaging.python.org) — pyproject.toml metadata fields
- GitHub Actions documentation — Python workflow patterns
- PEP 517/518 — build system requirements
- Contributor Covenant (contributor-covenant.org) — CODE_OF_CONDUCT boilerplate

---
*Architecture research for: PSAI-Bench open-source release packaging*
*Researched: 2026-04-12*
