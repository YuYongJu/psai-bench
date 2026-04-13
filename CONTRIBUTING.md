# Contributing to PSAI-Bench

Thank you for your interest in contributing to PSAI-Bench! This document covers development setup and guidelines.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YuYongJu/psai-bench.git
cd psai-bench

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify setup
psai-bench --help
pytest -q
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=psai_bench --cov-report=term-missing

# Run a specific test file
pytest tests/test_cli.py -v
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting. Pre-commit hooks run automatically, but you can also run manually:

```bash
ruff check .          # Lint
ruff check --fix .    # Auto-fix
ruff format .         # Format
```

## Adding a New Evaluator

To add support for a new model API:

1. Create a new class in `psai_bench/evaluators.py` extending `BaseEvaluator`
2. Implement `_call_api()` returning `(response_text, latency_ms, cost)`
3. Add the class to the `EVALUATORS` registry dict
4. Add the model name to the CLI `--model` choice list in `cli.py`
5. Document the required environment variable

## Adding New Scenarios

Scenario generators are in `psai_bench/generators.py`. All generators must:

- Accept a `seed` parameter for reproducibility
- Return dicts conforming to `ALERT_SCHEMA` (see `schema.py`)
- Include `_meta` with `ground_truth`, `difficulty`, `dataset`, and `category`
- Produce realistic distributions (see `distributions.py`)

## Pull Request Guidelines

1. Create a branch from `main`
2. Write tests for new functionality
3. Ensure `ruff check .` passes with no errors
4. Ensure all tests pass: `pytest -q`
5. Write a clear PR description explaining the change

## Reporting Issues

Please open a GitHub issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version and OS
