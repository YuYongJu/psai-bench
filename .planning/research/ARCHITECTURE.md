# Architecture Patterns: PSAI-Bench v4.0

**Domain:** Physical security AI benchmark — operational decision-support extension
**Researched:** 2026-04-13
**Scope:** How 5-class dispatch, cost-aware scoring, multi-site generalization, and adversarial robustness integrate with the v3.0 codebase

---

## The Load-Bearing Architectural Decision

**5-class dispatch is an action space, not a replacement for the classification space.**

Ground truth remains 3-class (THREAT / SUSPICIOUS / BENIGN). The dispatch decision
(armed_response, patrol, operator_review, auto_suppress, request_data) is the *recommended
action* given a classification in a specific context. This distinction is non-negotiable:

- Without it, there is no well-defined "optimal dispatch" to score against (a SUSPICIOUS label
  alone doesn't determine the optimal action — context does).
- Without it, backward compatibility with all v1/v2/v3 scenarios breaks.
- Without it, the seed-reproducibility guarantee breaks (any RNG-consuming change to an
  existing generator path breaks it).

All four features must be additive, not mutative.

---

## Existing Architecture: What's Already Here

### Module Map

```
psai_bench/
  schema.py       — ALERT_SCHEMA, OUTPUT_SCHEMA, VERDICTS, _META_SCHEMA_V2
  generators.py   — MetadataGenerator, VisualGenerator, VisualOnlyGenerator,
                    ContradictoryGenerator, TemporalSequenceGenerator
  scorer.py       — score_run, ScoreReport, score_sequences, compute_perception_gap,
                    format_dashboard, partition_by_track
  distributions.py — assign_ground_truth_v2, description pools, sample_* helpers
  baselines.py    — random, majority_class, always_suspicious, severity_heuristic
  cli.py          — generate, score, score-sequences, analyze-frame-gap,
                    baselines, compare, validate-*, evaluate, analyze-gap
  validation.py   — validate_scenarios, validate_submission
  statistics.py   — mcnemar_test, compute_all_cis, bootstrap CIs
```

### 3-Class Assumptions Baked Into 6 Locations

These are the coupling points that v4.0 must not break:

| Location | Specific Assumption |
|----------|---------------------|
| `schema.py` VERDICTS | Tuple `("THREAT", "SUSPICIOUS", "BENIGN")` |
| `schema.py` OUTPUT_SCHEMA | `verdict` enum restricted to 3 values |
| `schema.py` _META_SCHEMA_V2 | `ground_truth` enum restricted to 3 values |
| `scorer.py` _score_partition | TDR = caught as THREAT or SUSPICIOUS; FASR = classified BENIGN; 3x3 confusion matrix; decisiveness = not-SUSPICIOUS |
| `baselines.py` | All 4 baselines produce 3-class outputs, import VERDICTS |
| `distributions.py` | `assign_ground_truth_v2()` returns 3-class GT |

All changes must be additive around these locations.

### What's Already Solved (Leverage These)

- `context.site_type` — 5 values (solar, substation, commercial, industrial, campus) already in ALERT_SCHEMA
- `SITE_CATEGORY_BLOCKLIST` — already filters implausible category-site combinations
- `ScoreReport.per_dataset_accuracy` — already measures generalization gap across datasets
- `_inject_adversarial_signals` — signal-level adversarial injection (20% of v2 scenarios)
- Seed-isolated RNG per generator (each generator owns its own `np.random.RandomState`)
- `_meta.adversarial` flag — already tracked

---

## New Architecture: Component Boundaries

### 1. Schema Extension (schema.py)

Two additive changes:

**OUTPUT_SCHEMA — add optional `dispatch` field:**
```python
OUTPUT_SCHEMA["properties"]["dispatch"] = {
    "type": "string",
    "enum": [
        "armed_response",
        "patrol",
        "operator_review",
        "auto_suppress",
        "request_data",
    ],
    "description": "Recommended operational action (optional; required for cost scoring)"
}

DISPATCH_ACTIONS = (
    "armed_response", "patrol", "operator_review",
    "auto_suppress", "request_data"
)
```

The `dispatch` field is optional in OUTPUT_SCHEMA so that v1/v2/v3 output files still validate.
Systems that only produce `verdict` continue to work with all existing scoring.

**_META_SCHEMA_V2 — add `optimal_dispatch` and `site_profile`:**
```python
# In _META_SCHEMA_V2 properties:
"optimal_dispatch": {
    "type": "string",
    "enum": DISPATCH_ACTIONS,
    "description": "Benchmark-computed optimal action for cost scoring"
},
"adversarial_type": {
    "type": ["string", "null"],
    "enum": [None, "signal_flip", "loitering_as_waiting",
             "authorized_as_intrusion", "environmental_as_human"],
    "description": "v4 adversarial sub-type; null for non-adversarial scenarios"
},
```

### 2. Cost Model (new module: psai_bench/cost_model.py)

Entirely new module. No existing code touches it. It has two responsibilities:

**A. Compute optimal_dispatch from GT + context:**
```python
DISPATCH_COSTS = {
    # (decision, ground_truth) -> cost in USD
    ("armed_response", "BENIGN"):    500.0,   # false armed response
    ("armed_response", "SUSPICIOUS"): 200.0,  # probably unnecessary
    ("armed_response", "THREAT"):      0.0,   # correct action
    ("patrol",         "BENIGN"):     50.0,   # wasted patrol
    ("patrol",         "SUSPICIOUS"): 20.0,   # reasonable escalation
    ("patrol",         "THREAT"):      0.0,   # correct action
    ("operator_review","BENIGN"):     10.0,   # operator time, minor waste
    ("operator_review","SUSPICIOUS"):  0.0,   # correct holding pattern
    ("operator_review","THREAT"):     50.0,   # delayed response = harm
    ("auto_suppress",  "BENIGN"):      0.0,   # correct suppression
    ("auto_suppress",  "SUSPICIOUS"): 20.0,   # risky suppression
    ("auto_suppress",  "THREAT"):   1000.0,   # missed threat = catastrophic
    ("request_data",   "BENIGN"):     15.0,   # unnecessary data request
    ("request_data",   "SUSPICIOUS"):  5.0,   # reasonable data gathering
    ("request_data",   "THREAT"):     30.0,   # delayed response
}

SITE_THREAT_MULTIPLIERS = {
    "substation":   5.0,   # critical infrastructure; missed threats catastrophic
    "solar":        3.0,
    "industrial":   2.5,
    "commercial":   1.5,
    "campus":       2.0,
}

def compute_optimal_dispatch(gt: str, context: dict) -> str:
    """Compute the benchmark's optimal dispatch action for a ground truth + context pair.

    This is the decision a perfect oracle would make, used as the reference
    for expected cost scoring.
    """
    ...

def score_dispatch(
    scenarios: list[dict],
    outputs: list[dict],
) -> "CostScoreReport":
    """Score dispatch decisions against optimal. Requires dispatch field in outputs."""
    ...
```

**B. CostScoreReport dataclass:**
```python
@dataclass
class CostScoreReport:
    n_scenarios: int = 0
    total_cost_usd: float = 0.0
    mean_cost_usd: float = 0.0
    optimal_cost_usd: float = 0.0          # cost if perfect dispatch everywhere
    cost_ratio: float = 0.0                 # total / optimal (1.0 = perfect)
    per_action_counts: dict = field(default_factory=dict)
    per_site_mean_cost: dict = field(default_factory=dict)
    n_missing_dispatch: int = 0            # outputs without dispatch field
```

### 3. Scorer Extension (scorer.py)

Do not modify `_score_partition`, `score_run`, or `ScoreReport` fields. All existing metrics
must remain stable.

Two additive changes only:

**A. Import and call from cost_model in a new top-level function:**
```python
# New function alongside score_run — not replacing it
def score_dispatch_run(
    scenarios: list[dict],
    outputs: list[dict],
) -> "CostScoreReport":
    from psai_bench.cost_model import score_dispatch
    return score_dispatch(scenarios, outputs)
```

**B. Extend format_dashboard to accept an optional CostScoreReport:**
```python
def format_dashboard(
    report: ScoreReport,
    ambiguous_report: ScoreReport | None = None,
    track_reports: dict[str, ScoreReport] | None = None,
    cost_report: "CostScoreReport | None" = None,   # NEW, optional
) -> str:
    ...
    if cost_report is not None:
        lines.append("")
        lines.append("=== Cost-Aware Scoring ===")
        lines.append(f"  Total cost:   ${cost_report.total_cost_usd:.2f}")
        lines.append(f"  Optimal cost: ${cost_report.optimal_cost_usd:.2f}")
        lines.append(f"  Cost ratio:   {cost_report.cost_ratio:.3f}  (1.0 = optimal)")
```

### 4. Baselines Extension (baselines.py)

Each baseline function must add a `dispatch` field computed from its `verdict`.
This is a local mapping — no change to the function signature needed.

```python
# New module-level helper:
VERDICT_TO_DEFAULT_DISPATCH = {
    "THREAT":     "armed_response",
    "SUSPICIOUS": "operator_review",
    "BENIGN":     "auto_suppress",
}
```

Each baseline's output dict gets:
```python
"dispatch": VERDICT_TO_DEFAULT_DISPATCH[verdict],
```

This is the simplest defensible mapping. The baselines are lower bounds — their dispatch
logic intentionally has no nuance. That's the point: any evaluated system should produce
lower expected costs than these.

### 5. Generators: Multi-Site (generators.py)

The infrastructure exists. The work is:

**A. Add `--site-type` filter to `generate` CLI command:**
```python
@click.option(
    "--site-type",
    type=click.Choice(["solar", "substation", "commercial", "industrial", "campus", "all"]),
    default="all",
    help="Generate scenarios for a specific site type only."
)
```

In the generator, pass `site_type_filter` to a new wrapper that rejects scenarios where
`context.site_type != site_type_filter`. This must be done via post-filtering (not by
changing the RNG sequence) to preserve seed reproducibility.

**B. Add `compute_site_generalization_gap` to scorer.py:**
```python
def compute_site_generalization_gap(
    scenarios: list[dict],
    outputs: list[dict],
    train_site: str,
    test_site: str,
) -> dict:
    """Score separately on train_site and test_site, return gap.

    Returns: {train_site_score, test_site_score, generalization_gap}
    """
    train_scenarios = [s for s in scenarios if s["context"]["site_type"] == train_site]
    test_scenarios  = [s for s in scenarios if s["context"]["site_type"] == test_site]
    train_report = score_run(train_scenarios, outputs)
    test_report  = score_run(test_scenarios, outputs)
    return {
        "train_site": train_site,
        "test_site": test_site,
        "train_aggregate": train_report.aggregate_score,
        "test_aggregate": test_report.aggregate_score,
        "generalization_gap": train_report.aggregate_score - test_report.aggregate_score,
    }
```

**C. CLI command:**
```
psai-bench site-generalization \
  --scenarios data/generated/metadata_all.json \
  --outputs results/gpt4o_run1.json \
  --train-site solar \
  --test-site commercial
```

### 6. Generators: Adversarial v4 (generators.py + distributions.py)

Current adversarial (`_inject_adversarial_signals`) is signal-level: it flips severity,
zone, or time to create conflicting metadata. v4 adversarial is behavioral: the scenario
narrative describes a pattern that superficially resembles authorized activity.

**New AdversarialV4Generator class:**
```python
class AdversarialV4Generator:
    """Generate v4 behavioral adversarial scenarios.

    Three sub-types:
    - loitering_as_waiting: person lingers 20+ min near entry but has badge history
    - authorized_as_intrusion: badge access + unusual path through restricted zone
    - environmental_as_human: thermal/PIR trigger from equipment, description sounds human
    """

    ADVERSARIAL_TYPES = [
        "loitering_as_waiting",
        "authorized_as_intrusion",
        "environmental_as_human",
    ]

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)   # isolated RNG
        self.seed = seed

    def generate(self, n: int = 300) -> list[dict]:
        ...
```

New description pools in `distributions.py` (not mixed into existing pools, to avoid
contaminating v2/v3 scenario generation):

```python
# v4 behavioral adversarial descriptions — in distributions.py
ADV_V4_LOITERING_AS_WAITING = [...]   # reads as suspicious but has benign explanation
ADV_V4_AUTHORIZED_AS_INTRUSION = [...] # reads as authorized but spatial pattern is wrong
ADV_V4_ENVIRONMENTAL_AS_HUMAN = [...]  # sensor ambiguity descriptions
```

`_meta.adversarial_type` distinguishes v4 adversarial from v2/v3 signal-flip adversarial.

**CLI:**
```
psai-bench generate --track adversarial_v4 --n 300 --seed 42
```

Requires adding `"adversarial_v4"` to the track enum in both `ALERT_SCHEMA` and the
`generate` CLI command's track `click.Choice`.

### 7. CLI (cli.py)

New and modified commands:

| Command | Status | Purpose |
|---------|--------|---------|
| `generate --track adversarial_v4` | New | Generate v4 behavioral adversarial scenarios |
| `generate --site-type [name]` | Modified (new option) | Filter to single site type |
| `score --include-dispatch` | Modified (new flag) | Run cost scoring alongside standard scoring |
| `score-dispatch` | New | Score dispatch decisions only, produce CostScoreReport |
| `site-generalization` | New | Cross-site generalization gap analysis |
| `baselines` | Modified | Baselines now also produce `dispatch` field |

All existing commands (`score`, `baselines`, `compare`, `validate-*`, `score-sequences`,
`analyze-frame-gap`) must remain backward-compatible with v1/v2/v3 scenario and output files.

---

## Data Flow for v4.0

### Standard scoring path (unchanged):
```
scenarios.json + outputs.json
  → score_run()
  → ScoreReport (TDR, FASR, Decisiveness, ECE, Aggregate)
  → format_dashboard()
```

### Dispatch scoring path (new, additive):
```
scenarios.json (with _meta.optimal_dispatch) + outputs.json (with dispatch field)
  → score_dispatch_run()
  → CostScoreReport (total_cost, cost_ratio, per_site_mean_cost)
  → format_dashboard(cost_report=...)  [optional, appended section]
```

### Site generalization path (new):
```
mixed-site scenarios.json + outputs.json
  → compute_site_generalization_gap(train_site="solar", test_site="commercial")
  → {train_aggregate, test_aggregate, generalization_gap}
```

### Adversarial analysis path (new):
```
adversarial_v4_scenarios.json + outputs.json
  → score_run() (standard metrics)
  → partition_by_adversarial_type()  [new helper]
  → per-type accuracy breakdown
```

---

## Build Order

This ordering minimizes integration risk. Each step is independently testable.

### Step 1: Schema (schema.py)
Add `dispatch` to OUTPUT_SCHEMA (optional field). Add `optimal_dispatch` and
`adversarial_type` to _META_SCHEMA_V2. Add `DISPATCH_ACTIONS` constant. Update
`generation_version` enum to include "v4". Zero breaking changes.

**Test:** All 238 existing tests still pass. New tests: validate outputs with and without
`dispatch` field.

### Step 2: Cost Model (new psai_bench/cost_model.py)
Implement `DISPATCH_COSTS`, `SITE_THREAT_MULTIPLIERS`, `compute_optimal_dispatch()`,
`score_dispatch()`, `CostScoreReport`. Fully isolated — no existing module imports it yet.

**Test:** Unit tests on cost computation, optimal dispatch logic for each GT class and site type.

### Step 3: Baselines (baselines.py)
Add `VERDICT_TO_DEFAULT_DISPATCH` mapping. Add `dispatch` field to all 4 baseline outputs.
No signature changes.

**Test:** Baselines produce valid dispatch values. Existing baseline tests still pass.

### Step 4: Scorer extension (scorer.py)
Add `score_dispatch_run()` function. Extend `format_dashboard()` signature with optional
`cost_report` parameter (default None, backward-compatible). No changes to `_score_partition`,
`score_run`, or `ScoreReport`.

**Test:** `format_dashboard` without cost_report produces identical output to current.
`score_dispatch_run` produces correct `CostScoreReport`.

### Step 5: Generators — Adversarial v4 (generators.py + distributions.py)
Add `AdversarialV4Generator` class. Add description pools in `distributions.py` with `ADV_V4_`
prefix (no contamination of existing pools). Add `adversarial_v4` to ALERT_SCHEMA track enum.

**Test:** Generator produces correct `adversarial_type` in `_meta`. Scenarios validate against
updated ALERT_SCHEMA. Existing generators still produce identical output for same seed.

### Step 6: Generators — Multi-Site (generators.py + cli.py)
Add `--site-type` option to `generate` command using post-generation filtering. Add
`compute_site_generalization_gap()` to `scorer.py`. Add `site-generalization` CLI command.

**Test:** `--site-type solar` produces only solar scenarios. `--site-type all` (default)
matches current behavior. Cross-site gap computes correctly.

### Step 7: CLI integration (cli.py)
Wire all new commands. Add `--include-dispatch` flag to `score`. Update `baselines` to
print dispatch distribution. Add `score-dispatch` command. Add `site-generalization` command.

**Test:** CLI smoke tests. Help text accurate. Backward compat: existing `score` and
`baselines` invocations produce identical output without new flags.

### Step 8: Tests (tests/)
- Schema validation tests for new fields
- Cost model unit tests
- Dispatch scoring integration tests
- Multi-site filtering tests
- AdversarialV4Generator output validation
- End-to-end: generate v4 scenarios → run baselines → score dispatch → assert cost_ratio

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Merging dispatch with verdict
**What goes wrong:** Using a single 5-class `verdict` field for dispatch replaces the
3-class classification, breaking all existing scoring math (TDR, FASR require THREAT/BENIGN
as labels), making optimal dispatch impossible to compute from GT alone, and invalidating
all existing output files.
**Instead:** `dispatch` is a parallel optional field alongside `verdict`. Classification
and dispatch are separate concerns.

### Anti-Pattern 2: Modifying existing generator RNG sequences
**What goes wrong:** Any change to `generate_ucf_crime_v2` or similar that consumes
RNG calls (even adding a new `rng.choice()`) changes the output of all scenarios after
that point for the same seed. This breaks the seed-reproducibility guarantee.
**Instead:** New generators get new isolated `np.random.RandomState` instances. New
fields in existing generators are computed deterministically from already-sampled values
(no new RNG consumption).

### Anti-Pattern 3: Making dispatch required in OUTPUT_SCHEMA
**What goes wrong:** All existing output files from v1/v2/v3 evaluations become invalid.
`validate_submission` rejects them. Users cannot re-score historical runs.
**Instead:** `dispatch` is optional in OUTPUT_SCHEMA. `score_dispatch_run()` counts and
reports `n_missing_dispatch` separately from the cost metrics.

### Anti-Pattern 4: Mixing v4 adversarial descriptions into existing pools
**What goes wrong:** v4 behavioral adversarial descriptions in `DESCRIPTION_POOL_AMBIGUOUS`
change the output of `generate_ucf_crime_v2` for any seed (pool size changes → different
random indices). Same RNG-contamination problem.
**Instead:** Separate `ADV_V4_*` pools in `distributions.py`. Existing pools are append-only
and only safe to append to at the end (or use new names).

### Anti-Pattern 5: Computing optimal_dispatch purely from GT class
**What goes wrong:** THREAT at a campus → optimal dispatch may be patrol. THREAT at a
substation → optimal dispatch is armed response. A flat GT-to-dispatch mapping ignores
the site multipliers that make cost scoring meaningful.
**Instead:** `compute_optimal_dispatch(gt, context)` takes both GT and context (specifically
`context.site_type` and `zone.sensitivity`). The cost model is context-aware.

---

## Scalability Considerations

| Concern | Current (238 tests, v3.0) | v4.0 Addition |
|---------|--------------------------|---------------|
| Test count | 238 | +50-80 new tests estimated |
| Scenario generation time | O(n) per track | No change for existing tracks; AdversarialV4Generator same pattern |
| Scoring computation | O(n) vectorized via numpy | CostScoreReport adds O(n) dict lookups; negligible |
| CLI command count | 10 commands | +3 new commands (score-dispatch, site-generalization, generate adversarial_v4) |
| Memory | Scenarios loaded into memory | No change; generators yield lists |

---

## Component Dependency Map

```
distributions.py  (ADV_V4_* pools — no new imports)
    ↑
generators.py  (AdversarialV4Generator — imports distributions.ADV_V4_*)
    ↑
schema.py  (DISPATCH_ACTIONS, updated OUTPUT_SCHEMA, updated ALERT_SCHEMA track enum)
    ↑
cost_model.py  (imports schema.DISPATCH_ACTIONS — NEW MODULE)
    ↑
baselines.py  (imports schema.DISPATCH_ACTIONS for VERDICT_TO_DEFAULT_DISPATCH)
scorer.py    (imports cost_model.score_dispatch in new score_dispatch_run)
    ↑
cli.py  (imports all of the above for new commands)
    ↑
tests/  (imports everything)
```

---

## Open Decisions Requiring Phase-Level Resolution

1. **Exact dispatch cost values.** The costs shown ($200-500 armed response, etc.) are from
   VISION.md. Before implementation, these need a defensible source or explicit "benchmark
   assumption" labeling. The benchmark makes these numbers auditable by publishing them.

2. **optimal_dispatch assignment rule.** The `compute_optimal_dispatch` function needs a
   documented decision rule (similar to the rubric for 3-class GT). Suggested: THREAT at
   sensitivity 4-5 or site substation/solar → armed_response; THREAT at lower sensitivity →
   patrol; SUSPICIOUS → operator_review; BENIGN high-FPR device → auto_suppress; BENIGN
   otherwise → auto_suppress; ambiguous cases → request_data.

3. **AdversarialV4Generator ground truth assignment.** Behavioral adversarials need a defined
   GT. Recommended: use `assign_ground_truth_v2` on the actual context signals (not the
   narrative). The _narrative_ is adversarial (designed to fool), but the _signals_ still
   determine GT. This is consistent with v2/v3 adversarial design.

4. **Whether `site-generalization` needs train/test scenario files or a single mixed file.**
   Single mixed file with site-type filtering is simpler and aligns with existing
   `per_dataset_accuracy` pattern. Confirm before CLI design is locked.
