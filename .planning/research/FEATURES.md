# Feature Research

**Domain:** Open-source ML benchmark release artifacts
**Researched:** 2026-04-12
**Confidence:** HIGH

## Framing Note

The benchmark core (CLI, scorer, generators, evaluators) is complete at v1.0rc1. Every "feature" here is a **release artifact** — documentation, metadata, and presentation scaffolding needed to publish PSAI-Bench as a credible open-source benchmark. None of these involve writing new benchmark logic.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that every successful benchmark includes. Missing any of these makes the project feel unfinished to researchers evaluating whether to cite or extend it.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| README results table | MMLU, MLE-bench, BIG-bench all embed model scores directly; first thing researchers look for | LOW | Gates on `results/` decision — commit GPT-4o UCF metadata run as example output |
| BibTeX citation block | Universally present in every benchmark examined (HumanEval, SWE-bench, MMLU, MTEB, BIG-bench, MLE-bench); absence signals "not citable" | LOW | Single arXiv-style BibTeX entry; no paper yet so cite GitHub repo + year |
| pip install + one-command quickstart | SWE-bench, HumanEval, MTEB all start with install + minimal usage example; researchers test locally before reading further | LOW | `pip install psai-bench` then `psai-bench generate --scenario ucf --n 50` |
| LICENSE file | Apache-2.0 already declared in pyproject.toml; not having the actual file is a red flag for enterprise users | LOW | File needs to exist at repo root; decision already made |
| Shields.io badges (3 max) | Python version, CI status, License — the standard triad for Python tools; more than 3 is noise | LOW | `python-3.10+`, `tests passing`, `Apache-2.0` |
| CONTRIBUTING.md | SWE-bench and MTEB both reference it; tells researchers how to submit new evaluations or extend scenarios | LOW | Short file: how to run tests, how to add a model evaluator, issue templates |
| CODE_OF_CONDUCT.md | Standard for credible OSS; GitHub prompts for it; trivial to add | LOW | Use Contributor Covenant boilerplate verbatim |
| Example output files in repo | HumanEval provides `example_problem.jsonl` and `example_solutions.jsonl`; users need to see expected format before running | LOW | The existing `results/evaluations/gpt-4o_ucf_metadata_run1.json` serves this purpose directly |
| CHANGELOG.md | Signals version maturity for a v1.0 release; researchers need to know what changed between versions | LOW | Single entry for v1.0.0; establish format for future versions |
| GitHub Actions CI badge (tests + lint) | Researchers checking if a benchmark is maintained look for green CI; absence raises reliability questions | MEDIUM | pytest + ruff via Actions; generates the CI badge |
| Clean .gitignore (generated data excluded) | 16MB generated JSON bloats the repo; reproducible-by-seed means data shouldn't be committed | LOW | Add `data/` and generated scenario files; keep `results/` as example outputs |
| Reproducible generate command with seed | Users must be able to regenerate the exact benchmark scenarios that produced the published results | LOW | Already implemented; needs to be prominently documented in README |

### Differentiators (Competitive Advantage)

Features that distinguish PSAI-Bench from generic LLM benchmarks and support the core research claim.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Pre-computed results in repo (`results/`) | Most benchmarks make users run everything themselves (SWE-bench, MMLU); having a real GPT-4o result immediately demonstrates the tool works and provides a comparison anchor | LOW | Commit `results/evaluations/` and `results/baselines/`; document as "example outputs" |
| Perception-reasoning gap analysis prominently surfaced | The unique research contribution — measuring whether video data actually changes model decisions vs. metadata-only reasoning; no other physical security benchmark does this | LOW | README "Key Findings" section with a concrete gap metric from the GPT-4o run |
| Safety-weighted metrics explained in README | TDR/FASR/ECE have non-obvious security domain meanings; explaining the weighting rationale (false negatives cost more than false positives in security) differentiates from generic F1/accuracy tables | LOW | 3-4 sentence methodology note in README, full details in architecture section |
| Three scenario tracks documented (metadata, visual, multi-sensor) | Explicitly showing the three difficulty tiers helps researchers understand the research design at a glance | LOW | Comparison table in README: track → input modality → what it tests |
| Real dataset provenance (UCF Crime, Caltech Pedestrian) | Links to data sources and explains the grounding in real incident data — distinguishes from synthetic-only benchmarks | LOW | Dataset section in README with HuggingFace and citation links |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Jupyter notebook quickstart | BIG-bench and MTEB use them; users may expect interactive tutorials | BIG-bench is a 200+ contributor project with dedicated infra; a notebook for a CLI tool adds maintenance burden without proportional value; notebooks go stale | Good README with copy-pasteable CLI commands is faster for users and zero maintenance |
| HuggingFace Spaces / web leaderboard | MTEB directs to HF Spaces; looks polished | Requires separate infrastructure, ongoing hosting, and maintenance; PROJECT.md explicitly says CLI-first; single GPT-4o result doesn't justify a leaderboard | Results table in README; add HF Spaces after more model evaluations exist |
| Docker evaluation environment | SWE-bench and MLE-bench use Docker | Those benchmarks execute untrusted model-generated code that must be sandboxed; PSAI-Bench passes prompts to API endpoints — no sandboxing needed; Docker adds setup friction | Simple `pip install` with optional API key configuration |
| Model comparison matrix across all providers | Seems like a natural benchmark output | Only GPT-4o UCF metadata has been evaluated; a sparse comparison table (one model, one track) looks weaker than no table; fabricating results is a research integrity issue | Show GPT-4o vs baselines for the one completed evaluation; add columns as evaluations are run |
| Automated leaderboard via PR submission | SWE-bench accepts community result submissions | Requires review process, validation infrastructure, and ongoing maintenance; wrong for v1.0 with one author | Accept result submissions as issues or PRs with raw JSON; manually curate |

---

## Feature Dependencies

```
CI (GitHub Actions)
    └──generates──> CI badge in README

results/ in repo (committed)
    └──enables──> Results table in README
    └──enables──> Pre-computed results differentiator
    └──enables──> Perception-reasoning gap example in README

LICENSE file
    └──required for──> License badge

pyproject.toml metadata (authors, URLs)
    └──required for──> PyPI version badge (if published)
    └──required for──> Proper citation block

.gitignore (data/ excluded)
    └──depends on──> Reproducible seed generate command documented
```

### Dependency Notes

- **results/ commit decision gates README content:** The PROJECT.md marks this as a pending key decision. If `results/` is excluded from git, the results table in README requires fetching and documenting results elsewhere. Resolve this first — the recommendation is to keep `results/` as example outputs (the data is small, ~16MB, and has research value).
- **CI badge requires Actions to pass:** The 12 ruff lint errors and CLI/statistics test gaps must be fixed before the CI badge shows green. Badge before CI is a credibility risk.
- **Citation block does not require a paper:** Cite the GitHub repo with a year. BibTeX can reference a `misc` type with `howpublished = {\url{...}}`. This is standard for software without a published paper.

---

## MVP Definition

### Launch With (v1.0 Release)

The minimum needed to publish on GitHub and present on LinkedIn as credible benchmark infrastructure.

- [ ] README with: badges, quickstart (install + generate + score), scenario track table, results table (GPT-4o vs baselines), methodology note (safety weighting), dataset provenance, citation block — **the single highest-value artifact**
- [ ] LICENSE file (Apache-2.0) — **required for any OSS claim**
- [ ] CONTRIBUTING.md — short, tells researchers how to add model evaluators
- [ ] CODE_OF_CONDUCT.md — boilerplate, required for GitHub community profile
- [ ] GitHub Actions CI (test + lint) — green badge signals maintained project
- [ ] Lint clean (12 ruff errors fixed) — required for CI to pass
- [ ] .gitignore updated (generated data excluded, results/ kept) — repo hygiene
- [ ] CHANGELOG.md with v1.0.0 entry — signals version maturity
- [ ] pyproject.toml metadata complete (authors, URLs, classifiers) — required for proper citation and PyPI readiness
- [ ] Version bumped to 1.0.0 — signals stability to researchers

### Add After Validation (v1.x)

- [ ] Expanded test coverage (CLI tests, statistics tests) — add once CI baseline is green; currently 47% coverage
- [ ] Additional model evaluations (Claude, Gemini) — needed before a multi-column comparison table is credible
- [ ] HuggingFace dataset card — when multiple evaluations justify a proper leaderboard

### Future Consideration (v2+)

- [ ] HuggingFace Spaces leaderboard — only justified with 5+ model evaluations
- [ ] Jupyter notebook tutorial — only if user requests emerge or adoption warrants it
- [ ] Visual track model evaluations — out of scope for v1.0, requires video processing infrastructure

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| README (results, quickstart, citation) | HIGH | LOW | P1 |
| LICENSE file | HIGH | LOW | P1 |
| GitHub Actions CI | HIGH | MEDIUM | P1 |
| Lint clean | HIGH | LOW | P1 (gates CI) |
| Shields.io badges | HIGH | LOW | P1 (gates on CI passing) |
| .gitignore cleanup | MEDIUM | LOW | P1 |
| CONTRIBUTING.md | MEDIUM | LOW | P1 |
| CODE_OF_CONDUCT.md | LOW | LOW | P1 (trivial, expected) |
| CHANGELOG.md | MEDIUM | LOW | P1 |
| pyproject.toml metadata | MEDIUM | LOW | P1 |
| Expanded test coverage | MEDIUM | MEDIUM | P2 |
| Additional model evaluations | HIGH | HIGH (API cost) | P3 |
| HuggingFace Spaces leaderboard | MEDIUM | HIGH | P3 |

---

## Competitor / Comparator Analysis

| Feature | HumanEval | SWE-bench | MMLU | BIG-bench | MLE-bench | PSAI-Bench Plan |
|---------|-----------|-----------|------|-----------|-----------|-----------------|
| Results table in README | No | Leaderboard | Yes (in README) | Plot image | Yes (in README) | Yes — GPT-4o vs 4 baselines |
| BibTeX citation | Yes | Yes (3 entries) | Yes | Yes | Yes | Yes — single entry |
| Quickstart (install + run) | Yes | Yes | Minimal | Yes | Yes | Yes — install + generate + score |
| Badges | None | Python, License, PyPI | None | None | None | CI, Python, License |
| CONTRIBUTING.md | No | Yes | No | Yes | No | Yes |
| Example output files | Yes (.jsonl) | No | No | Yes (via Colab) | No | Yes (results/evaluations/) |
| Jupyter notebooks | No | No | No | Yes (Colab) | No | No — CLI-first |
| Docker requirement | No | Yes | No | No | Yes | No — unnecessary |
| Pre-committed result examples | No | No | No | No | No | Yes — differentiator |

---

## Sources

- HumanEval (openai/human-eval): https://github.com/openai/human-eval — badge absence, citation format, example jsonl pattern
- SWE-bench (swe-bench/SWE-bench): https://github.com/swe-bench/SWE-bench — badge triad (Python/License/PyPI), multiple citation entries, Docker overhead
- MMLU (hendrycks/test): https://github.com/hendrycks/test — results table directly in README, two-entry citation pattern
- BIG-bench (google/BIG-bench): https://github.com/google/BIG-bench — Colab notebooks, leaderboard plot, CONTRIBUTING patterns
- MLE-bench (openai/mle-bench): https://github.com/openai/mle-bench — performance table format with multiple columns, authors section
- MTEB (embeddings-benchmark/mteb): https://github.com/embeddings-benchmark/mteb — 3-badge pattern, Apache-2.0, leaderboard-as-HF-Spaces pattern
- Shields.io: https://shields.io/ — badge implementation reference
- daily.dev badge best practices: https://daily.dev/blog/readme-badges-github-best-practices — "3 max, stick to what's truthful"

---
*Feature research for: open-source ML benchmark release*
*Researched: 2026-04-12*
