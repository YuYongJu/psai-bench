# Technology Stack: PSAI-Bench v4.0

**Project:** psai-bench — v4.0 Operational Realism milestone
**Researched:** 2026-04-13
**Confidence:** HIGH — all findings verified directly from source files

---

## Verdict: No New Dependencies Required

Every v4.0 feature — 5-class dispatch, cost-aware scoring, multi-site generalization, adversarial
robustness — maps to application-logic changes in existing code. The PROJECT.md constraint
("No new dependencies unless strictly needed for scenario generation") holds.

---

## Existing Stack and v4.0 Role

### Core Runtime

| Package | Pinned In | v4.0 Role |
|---------|-----------|-----------|
| `numpy>=1.24` | `pyproject.toml` direct | All new scoring math: cost lookups, expected cost aggregation, 5-class confusion matrix, per-site-type accuracy arrays |
| `jsonschema>=4.0` | `pyproject.toml` direct | Extend `OUTPUT_SCHEMA` verdict enum from 3 to 5 values; extend `_META_SCHEMA_V2` generation_version to include "v4" |
| `click>=8.0` | `pyproject.toml` direct | New CLI commands for cost scoring, adversarial reporting |
| `pandas>=2.0` | `pyproject.toml` direct | Already imported; useful for site-type pivot tables in generalization analysis |
| `scikit-learn>=1.3` | `pyproject.toml` direct | Pulls in `scipy` transitively; existing pattern |
| `tabulate>=0.9` | `pyproject.toml` direct | Dashboard formatting for cost report |
| `matplotlib>=3.7` | `pyproject.toml` direct | Cost sensitivity curves if visualization added to CLI |

### Transitive (via scikit-learn)

| Package | Status | v4.0 Role |
|---------|--------|-----------|
| `scipy` | Transitive only — NOT in pyproject.toml | `statistics.py` already imports `from scipy import stats as scipy_stats`; used for McNemar's test and bootstrap CIs. Cost sensitivity analysis (varying cost weights) could use `scipy.optimize` if needed |

**Action required:** Add `scipy>=1.10` as a direct dependency to `pyproject.toml`. It is already
used in `psai_bench/statistics.py` but is missing from the declared dependencies. This is a latent
packaging bug — `pip install psai-bench` could install a version of scikit-learn that does not
bring the version of scipy statistics.py expects. Fix this in v4.0 regardless of new features.

---

## Feature-to-Stack Mapping

### 5-Class Dispatch Decisions

**What changes:** `OUTPUT_SCHEMA` verdict enum, `scorer.py` metrics, `schema.py` constants.

| File | Change | Package Used |
|------|--------|--------------|
| `psai_bench/schema.py` | Add `DISPATCH_VERDICTS` tuple with 5 values; update `OUTPUT_SCHEMA` enum | `jsonschema` |
| `psai_bench/scorer.py` | Replace 3-class confusion matrix with 5-class; add `dispatch_accuracy` metric; re-derive TDR/FASR from dispatch verdicts | `numpy` |
| `psai_bench/scorer.py` | `ScoreReport` gets `dispatch_accuracy`, `dispatch_confusion_matrix` fields | stdlib `dataclasses` |

The 5 classes are: `ARMED_RESPONSE`, `PATROL`, `OPERATOR_REVIEW`, `AUTO_SUPPRESS`,
`REQUEST_DATA`. These map onto the existing 3-class schema as follows for backward compat scoring:
- `ARMED_RESPONSE` + `PATROL` → THREAT-equivalent for TDR
- `AUTO_SUPPRESS` → BENIGN-equivalent for FASR
- `OPERATOR_REVIEW` + `REQUEST_DATA` → SUSPICIOUS-equivalent for Decisiveness

This mapping preserves every existing metric while adding 5-class-specific metrics on top.

**No new packages needed.**

### Cost-Aware Scoring

**What changes:** New `score_cost()` function in `scorer.py`; new `CostModel` dataclass.

The cost model is a lookup table `(dispatch_verdict, ground_truth) -> float`. Expected operational
cost is a dot product of frequencies and costs — pure numpy arithmetic.

```
# Pseudocode — no new imports
cost_matrix = np.array(...)           # 5 dispatch x 3 GT classes
expected_cost = np.sum(freq * cost_matrix[verdict_idx, gt_idx])
```

Default cost values (from VISION.md):
- False `ARMED_RESPONSE` on benign: $200–500
- Missed threat (`AUTO_SUPPRESS` on THREAT): catastrophic — weight by site type
- `OPERATOR_REVIEW`: $5–15 operator time
- `AUTO_SUPPRESS` on benign: $0 (optimal)

The `CostModel` should be user-configurable so operators can supply their actual per-site costs via
a JSON config. `jsonschema` validates the config; numpy computes the score.

**No new packages needed.**

### Multi-Site Generalization Testing

**What changes:** New partition logic in `scorer.py` — partition by `context.site_type` rather
than `_meta.source_dataset`.

The existing `generalization_gap` field in `ScoreReport` uses `source_dataset` (UCF-Crime,
Caltech). For v4.0, a parallel `per_site_accuracy` dict and `site_generalization_gap` are needed.

`context.site_type` already exists in `ALERT_SCHEMA` with the right enum:
`["solar", "substation", "commercial", "industrial", "campus"]`. The scenario generators already
populate it via `sample_site_type()` in `distributions.py`.

**Implementation:** Extend `_score_partition()` to also track `s["context"]["site_type"]` in
parallel arrays, compute per-site accuracy using numpy boolean masks, report max-min gap.

**No new packages needed.**

### Adversarial Robustness Scenarios

**What changes:** New scenario templates in `distributions.py`; new adversarial category flag
in `_meta`.

The three target adversarial patterns from VISION.md:
1. Loitering-as-authorized-waiting — `distributions.py` already has loitering descriptions and
   authorized access events. New scenarios combine them with BENIGN ground truth.
2. Authorized-as-intrusion — Mismatched badge access + restricted zone + correct GT = BENIGN.
3. Environmental-as-human — Existing `environmental_cause_probable` description pool, high severity
   metadata. GT = BENIGN. Tests whether models over-trust severity field.

These are scenario design decisions, not library decisions. The generation infrastructure
(`generators.py`, `distributions.py`, `np.random.RandomState`) already handles deterministic
adversarial injection (v2.0 shipped ~20%).

`_META_SCHEMA_V2` needs a new `adversarial_pattern` string field alongside the existing
`adversarial: bool` flag, so scorers can partition by attack type.

**No new packages needed.**

---

## Alternatives Considered and Rejected

| Category | Considered | Rejected Because |
|----------|------------|-----------------|
| Cost modeling | `pulp` or `scipy.optimize` for cost minimization | Overkill — cost scoring is expected value, not optimization. Arithmetic suffices. |
| 5-class metrics | `sklearn.metrics.classification_report` | Already using numpy directly; adding sklearn call adds no value and obscures the documented formulas |
| Adversarial scenario generation | `faker` for richer text generation | Scenarios use fixed description pools by design — reproducibility and leakage prevention require deterministic text, not generated text |
| Generalization testing | Separate analysis library | Per-site partitioning is 10 lines of numpy; no library warranted |

---

## Dependency Action Items

1. **Add `scipy>=1.10` to direct dependencies in `pyproject.toml`.** It is already used in
   `statistics.py` but undeclared. This is a packaging correctness fix, not a new dependency.

2. **No other dependency changes.** All v4.0 features are implementable within the existing stack.

---

## Sources

- Direct inspection of `pyproject.toml` (confirmed dependencies)
- Direct inspection of `psai_bench/scorer.py` (confirmed numpy-only math, existing generalization gap)
- Direct inspection of `psai_bench/schema.py` (confirmed OUTPUT_SCHEMA, site_type enum, _META_SCHEMA_V2)
- Direct inspection of `psai_bench/statistics.py` (confirmed undeclared scipy import)
- Direct inspection of `psai_bench/distributions.py` (confirmed site_type enum, adversarial description pools)
- `.planning/PROJECT.md` constraint: "No new dependencies unless strictly needed for scenario generation"
- `.planning/VISION.md` v4.0 cost values and dispatch class definitions
