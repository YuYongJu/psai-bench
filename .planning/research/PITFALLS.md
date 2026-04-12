# Pitfalls Research

**Domain:** Open-source release of an existing Python ML benchmark
**Researched:** 2026-04-12
**Confidence:** HIGH (most pitfalls are directly observed in the repo or well-documented in official sources)

---

## Critical Pitfalls

### Pitfall 1: Large Files Permanently Embedded in Git History

**What goes wrong:**
The 16MB of generated JSON (3 files in `data/generated/`) was committed in the first and only real commit (7eda522). Even after adding `data/generated/` to `.gitignore` and removing files from the working tree, the data remains in git history. Every `git clone` of the repo downloads those 16MB forever. GitHub also has a soft warning threshold at 50MB total repo size and a hard limit at 100MB for individual files.

**Why it happens:**
First commit contained everything at once. With a 2-commit history there's no "safe" commit to rebase onto — the large files sit in the very first content commit.

**How to avoid:**
Use `git-filter-repo` (recommended by git official docs over deprecated `git filter-branch`) to excise the three files from all history before the repo is public. With only 2 commits this is fast and low-risk. Steps:
1. `pip install git-filter-repo`
2. `git filter-repo --path data/generated/ --invert-paths`
3. Force-push to remote with `git push --force-with-lease`
4. Verify with `git cat-file --batch-check --batch-all-objects | sort -k3 -n | tail` — large blobs should be gone

**Warning signs:**
- `git count-objects -vH` shows pack size > 2MB after removing data files from working tree
- `du -sh .git/` is larger than the source code itself
- GitHub repo "About" sidebar shows repository size > 5MB

**Phase to address:** Repository Hygiene (before any public push — this must be the very first action)

---

### Pitfall 2: Generated Data Removed from Git But Not Reproducible

**What goes wrong:**
Files are stripped from history, `.gitignore` is updated, but there is no documented, tested way for a new user to regenerate the exact scenarios. They clone the repo, run `psai-bench score`, and get a `FileNotFoundError` on `data/generated/metadata_ucf_seed42.json`. The benchmark is effectively unusable without a reproduction step.

**Why it happens:**
The `psai-bench generate` command exists, but the exact invocation (track, source, n, seed, output path) that produces the canonical evaluation set is not documented. Users guess wrong seeds or wrong output paths and get different scenario files that produce different scores, breaking comparability.

**How to avoid:**
- Add a `Makefile` or `scripts/reproduce.sh` with exact generate commands for each canonical dataset
- Document the exact invocations in README under a "Reproduce Benchmark Data" section
- Consider adding a `psai-bench download-data` or `psai-bench init` subcommand that runs all generation steps with canonical defaults
- Add an integration test that runs `psai-bench generate --track metadata --source ucf --n 100 --seed 42` and asserts the first scenario's ID matches the expected value (detects numpy RNG drift across versions)

**Warning signs:**
- README mentions `data/generated/` directory but does not show the `psai-bench generate` command
- CI passes but does not run `psai-bench generate` at all
- `psai-bench generate` output file name differs from the path used in `psai-bench score` examples

**Phase to address:** Repository Hygiene + README Documentation

---

### Pitfall 3: NumPy RNG Output Changes Across Library Versions

**What goes wrong:**
`psai-bench generate --seed 42` produces scenario IDs and ground-truth labels that differ between numpy 1.24 and numpy 2.x because numpy's random Generator bit stream is explicitly not version-stable (documented in NEP 19). A user on numpy 2.0 regenerates the canonical dataset, gets slightly different scenarios, and scores look wrong when compared to the published baseline results.

**Why it happens:**
`pyproject.toml` pins `numpy>=1.24` with no upper bound. numpy 2.0 was released in 2024 and contains generator changes. The project uses numpy for scenario generation (random sampling, label assignment), making bit-for-bit reproducibility version-sensitive.

**How to avoid:**
- Pin numpy to a major version range in pyproject.toml: `numpy>=1.24,<3`
- Document in README which numpy version was used for the canonical v1.0 dataset: "Generated with numpy 1.26.x, seed=42"
- Alternatively, ship a SHA-256 checksum for each canonical JSON file so users can verify their regeneration matches

**Warning signs:**
- CI tests only run on the latest numpy
- No numpy version pinned in CI matrix
- Integration test hashes scenario IDs but test passes on numpy 1.x, fails silently on numpy 2.x

**Phase to address:** Repository Hygiene + CI Setup

---

### Pitfall 4: Broken `pip install` Due to Missing Package Metadata

**What goes wrong:**
`pip install psai-bench` (or `pip install -e .`) appears to succeed but the installed package is missing critical files or metadata. Specifically:
- `readme` field in `pyproject.toml` currently uses `{text = "...", content-type = "text/plain"}` with a one-line description — not the actual README.md file. PyPI will show a bare one-liner instead of the full README.
- `project.urls` (homepage, repository, documentation) are absent — PyPI listing looks unfinished.
- `project.authors` is absent — no author attribution on PyPI.
- `project.classifiers` are absent — the package won't appear in PyPI searches for "machine learning" or "benchmarks".

**Why it happens:**
`pyproject.toml` was created functionally (enough to make `pip install -e .` work) but never configured for public distribution.

**How to avoid:**
- Switch `readme` to `readme = "README.md"` (standard form)
- Add `authors`, `keywords`, `classifiers`, and `[project.urls]`
- Run `pip install -e . && pip show psai-bench` to verify metadata before publishing
- Use `twine check dist/*` after building to catch PyPI metadata validation errors before upload

**Warning signs:**
- `pip show psai-bench` shows empty Home-page or Author
- PyPI package page shows the bare description string instead of formatted README
- `python -c "import importlib.metadata; print(importlib.metadata.metadata('psai-bench')['Summary'])"` returns the wrong string

**Phase to address:** Project Metadata + PyPI Packaging

---

### Pitfall 5: LICENSE File Absent Despite License Declaration

**What goes wrong:**
`pyproject.toml` declares `license = "Apache-2.0"` but there is no `LICENSE` file in the repository. This is legally incomplete: downstream users have no document to satisfy the Apache 2.0 obligation of including the license text with redistributions. GitHub's "Used by" and license detection features will also fail to detect the license.

**Why it happens:**
Metadata declaration and physical file are two separate things. It's easy to write `license = "Apache-2.0"` in TOML and consider it done.

**How to avoid:**
- Copy the full Apache-2.0 license text into `LICENSE` (not `LICENSE.md`) at repo root
- Add copyright header: `Copyright 2026 [Author Name]`
- Apache 2.0 also recommends a `NOTICE` file for attribution — not required here (no third-party Apache-licensed code to attribute) but good practice
- Verify GitHub detects the license via the repository "About" sidebar

**Warning signs:**
- GitHub sidebar shows "No license" or question mark next to the repo
- `pip show psai-bench` shows `License: UNKNOWN`
- `twine check dist/*` warns about license metadata

**Phase to address:** Documentation + Licensing (first phase)

---

### Pitfall 6: CI That Passes Locally But Breaks on First Run

**What goes wrong:**
GitHub Actions CI is written but fails on its first run because:
- Tests assume `data/generated/` files exist (they are now gitignored)
- The `api` optional dependency group references `google-genai>=1.0` but the package is actually `google-generativeai` or `google-genai` (the SDK was renamed in 2024)
- Python 3.10 matrix entry succeeds locally but `actions/setup-python` may not have 3.10 cached on the runner, causing a slow cold start or an unexpected failure

**Why it happens:**
CI is written to mirror local dev assumptions. Tests that pass locally pass because the developer has the generated files and the right packages already installed. A clean CI environment exposes assumptions.

**How to avoid:**
- Ensure no test imports or opens files in `data/generated/` without first running `psai-bench generate`
- Add a CI step that runs the generate command before tests, or mock file I/O in tests
- Verify `google-genai` package name on PyPI before writing it into CI requirements
- Run `act` locally to simulate GitHub Actions before pushing the workflow
- Pin `actions/setup-python` to `@v5` (current stable) not a commit hash or `@main`

**Warning signs:**
- CI fails on the very first run with `FileNotFoundError` or `ModuleNotFoundError`
- Workflow uses `actions/setup-python@v3` (deprecated, uses Node.js 16 which is EOL)
- Workflow installs `.[api]` but evaluators tests are not skipped when API keys are absent

**Phase to address:** CI Setup

---

### Pitfall 7: README Explains What, Not Why — Fails to Land the Research Contribution

**What goes wrong:**
The README describes how to install and run the benchmark but buries or omits the core research claim: "Do frontier models actually benefit from video data or just reason about metadata?" Without this framing, a LinkedIn reader skims past it, and an academic user doesn't know why this benchmark is different from existing security datasets.

**Why it happens:**
Technical authors default to documentation mode (usage, API reference, commands) and skip narrative mode (motivation, gap in existing work, key finding).

**How to avoid:**
- Open README with a one-paragraph "Why this exists" that names the perception-reasoning gap hypothesis explicitly
- Include the actual GPT-4o result (TDR=0.999 but Aggregate=0.580 due to SUSPICIOUS overuse) as the motivating example — concrete numbers are more compelling than abstractions
- Add a results table early in the README (before installation instructions)
- Add a "Citation" or "How to Cite" section — academic benchmarks without a citation block are frequently not cited even when used

**Warning signs:**
- README section order: Installation → Usage → Results (burying the "so what")
- No concrete numbers in the first two paragraphs
- No citation block or CITATION.cff file

**Phase to address:** Documentation (README)

---

### Pitfall 8: Results JSON Files in Git Create Expectations of Permanence

**What goes wrong:**
`results/` is currently committed (15 files, ~16MB). The PROJECT.md notes a pending decision: "Keep results/ in repo as examples." If results stay in git, future evaluations that change scores will create confusing commits ("why did the GPT-4o score change?"), and contributors may think they need to re-run expensive API evaluations just to contribute code changes.

**Why it happens:**
Results feel like documentation at the time of first commit. They become technical debt when the benchmark evolves.

**How to avoid:**
- Move canonical results to a GitHub Release asset (zip file attached to v1.0.0 tag) rather than committed files
- Keep only a small `results/examples/` with synthetic/baseline outputs (no API costs, deterministic) in git
- Add `results/evaluations/*.json` to `.gitignore` and document in CONTRIBUTING.md that model evaluation results should not be committed

**Warning signs:**
- `results/` contains files > 1MB committed to git
- CI runs `psai-bench score` against actual model outputs and commits the results
- Contributors can't run the full test suite without API keys because tests reference `results/evaluations/`

**Phase to address:** Repository Hygiene

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `pyproject.toml` readme as inline text | Works for local install | PyPI shows bare description; README.md not distributed | Never — costs 1 line to fix |
| No upper bound on numpy (`>=1.24`) | Avoids `ResolutionImpossible` errors | Generation bit-stream may change in numpy 2.x, breaking score comparisons | Never for benchmark data integrity |
| Generated data in git | First-clone "just works" | Repo bloats; users can't trust data is from canonical seed | Never — documented seed + generate command is correct approach |
| Skipping CITATION.cff | Saves 10 minutes | Academic users don't cite the tool; impact is invisible | Never for a benchmark targeting researchers |
| CI tests skip all API-dependent tests | No API key costs | Core evaluation path untested in CI | Acceptable if mocking strategy is documented |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub Actions + `data/generated/` | Tests assume files exist from working tree | Add a setup step or use pytest fixtures that generate minimal test data at test time |
| PyPI + setuptools + `pyproject.toml` | `readme = {text = "..."}` doesn't pull in README.md | Use `readme = "README.md"` — setuptools resolves this to the file |
| `google-genai` optional dep | Package name changed during 2024 SDK unification | Verify current PyPI package name is `google-genai` (not `google-generativeai`) before publishing |
| HuggingFace dataset download | UCF Crime dataset requires HuggingFace login; undocumented for new users | Add a "Dataset Access" section to README explaining HF login requirement |
| Apache-2.0 + PyPI classifiers | `license = "Apache-2.0"` in TOML is SPDX format but classifiers use a different string | Classifiers entry must be `"License :: OSI Approved :: Apache Software License"` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Generating 3,000+ scenarios in a single test run | CI takes 3+ minutes per test suite, developers skip running tests | Generate small N (100) in tests, use seed fixture | CI test suites; affects any machine running full test suite |
| Loading entire JSON scenario file into memory for scoring | Scoring 3,000-scenario file peaks at 500MB+ RAM | Stream or batch-process scenarios; issue is latent with current file sizes | Files > 10k scenarios |
| Matplotlib rendering in CI | Tests that import `psai_bench.cli` pull in matplotlib, causing backend errors on headless CI | Set `MPLBACKEND=Agg` in CI environment or use `matplotlib.use('Agg')` before import | Headless Linux CI runners |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| API key in evaluator docstring as `api_key="sk-..."` | Copy-paste accident commits real key | Keep placeholder but add `NEVER pass real keys in code` comment; `.env` already in `.gitignore` |
| CI workflow with `OPENAI_API_KEY` secret | Secret exposure if workflow is triggered by forked PR | Use `if: github.event_name != 'pull_request_target'` guard; mark evaluator tests as `[skip-ci-api]` |
| No `SECURITY.md` | Unclear responsible disclosure path for benchmark data poisoning or scoring manipulation issues | Add minimal `SECURITY.md` pointing to maintainer email or GitHub private vulnerability reporting |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| CLI generates files to `data/generated/` by default but scores expects them at specific paths | First-time user runs `psai-bench score` and gets FileNotFoundError with unhelpful message | Quickstart in README shows generate → score pipeline in exact sequence with copy-pasteable commands |
| `psai-bench evaluate` requires API keys with no graceful degradation | User without API keys can't explore the benchmark at all | Ensure `psai-bench baselines` and `psai-bench score` work without any API keys; document this clearly |
| No `--help` output in README | Users don't know what subcommands exist | Add `psai-bench --help` output as a code block near the top of README |

---

## "Looks Done But Isn't" Checklist

- [ ] **LICENSE file:** `license = "Apache-2.0"` in pyproject.toml looks done — verify the actual `LICENSE` file exists at repo root with full Apache 2.0 text
- [ ] **README:** README.md file exists — verify it contains results table, citation block, and "why this exists" framing, not just usage docs
- [ ] **Git history:** `data/generated/` removed from `.gitignore` working tree — verify it's also purged from git history (`git cat-file --batch-check --batch-all-objects | grep blob | sort -k3 -n | tail` should show no blobs > 100KB)
- [ ] **Reproducibility:** `psai-bench generate` command documented — verify the README shows exact flags that produce canonical v1.0 datasets
- [ ] **CI green:** Workflow file exists — verify first run completes without `FileNotFoundError` on generated data or missing `MPLBACKEND`
- [ ] **PyPI metadata:** `pip show psai-bench` shows correct name/author/URL — verify after `pip install -e .`, not just by reading pyproject.toml
- [ ] **Optional deps:** `pip install psai-bench[api]` works — verify `google-genai` package name is current on PyPI
- [ ] **Results in git:** `results/` is committed — verify decision is deliberate (example outputs) vs. accidental (full eval results); large evaluation JSONs should not be in git

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Large files in git history (not yet public) | LOW | `git filter-repo --path data/generated/ --invert-paths` + force push; 2-commit history makes this fast |
| Large files in git history (already public, cloned by others) | HIGH | Must notify existing cloners; force-push rewrites their history; coordinate timing or accept the repo size |
| Wrong numpy version breaks scenario reproducibility | MEDIUM | Pin numpy in pyproject.toml; publish SHA-256 checksums for canonical JSON files in release notes |
| CI broken on first run | LOW | Fix missing env vars, add generate step, re-push; CI is gated behind branch protection so no users are affected |
| PyPI upload with wrong metadata | MEDIUM | `pip install psai-bench` will pull wrong version; must yank release on PyPI and re-publish; plan metadata carefully before first PyPI push |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Large files in git history | Repository Hygiene (Phase 1 — before public push) | `git count-objects -vH` shows pack < 1MB; GitHub repo size < 2MB |
| Generated data not reproducible | Repository Hygiene + README | `git clone` + README quickstart commands produce matching SHA-256 for canonical files |
| NumPy RNG version drift | Repository Hygiene + CI | CI matrix tests on pinned numpy version; integration test asserts scenario ID hash |
| Broken pip install metadata | Project Metadata | `twine check dist/*` passes; PyPI listing shows full README and author |
| LICENSE file absent | Documentation + Licensing | `ls LICENSE` exists; GitHub sidebar shows "Apache-2.0" |
| CI broken on first run | CI Setup | First green run on a clean branch with no local state |
| README explains what not why | Documentation (README) | README opens with research hypothesis and concrete GPT-4o numbers within first 200 words |
| Results JSON permanence | Repository Hygiene | `git ls-files results/evaluations/` returns empty (or only baseline/example outputs) |

---

## Sources

- [git-filter-repo (official git-recommended tool)](https://github.com/newren/git-filter-repo)
- [NumPy NEP 19 — RNG version stability policy](https://numpy.org/neps/nep-0019-rng-policy.html)
- [setuptools data files in pyproject.toml](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)
- [Python Packaging User Guide — writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Common Python packaging mistakes (jwodder.github.io)](https://jwodder.github.io/kbits/posts/pypkg-mistakes/)
- [Applying the Apache 2.0 license](https://www.apache.org/legal/apply-license.html)
- [PEP 639 — License metadata in Python packages](https://peps.python.org/pep-0639/)
- [Python in GitHub Actions (hynek.me)](https://hynek.me/articles/python-github-actions/)
- Direct repo inspection: `git show --stat 7eda522`, `git ls-files`, `pyproject.toml`, `.gitignore`, `psai_bench/evaluators.py`

---
*Pitfalls research for: open-source release of existing Python ML benchmark (PSAI-Bench)*
*Researched: 2026-04-12*
