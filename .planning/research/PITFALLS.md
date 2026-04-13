# Domain Pitfalls: v4.0 Operational Realism

**Domain:** AI benchmark — adding 5-class dispatch, cost-aware scoring, multi-site generalization, adversarial robustness to an existing 3-class benchmark
**Researched:** 2026-04-13
**Source basis:** Direct codebase analysis (scorer.py, schema.py, generators.py, validation.py, tests/). Evidence lines cited throughout.

---

## Critical Pitfalls

### Pitfall 1: Metric Definitions Are Baked Into 3-Class Assumptions

**What goes wrong:** Every primary metric in `scorer.py` is derived from the three-way partition {THREAT, SUSPICIOUS, BENIGN}. TDR is "THREAT caught as THREAT or SUSPICIOUS" (lines 423–427). FASR is "BENIGN caught as BENIGN" (lines 429–433). Decisiveness is "not SUSPICIOUS" (lines 458–461). The aggregate score formula (lines 465–469) combines all four metrics. With 5-class dispatch, SUSPICIOUS disappears as a verdict class; the THREAT/BENIGN/SUSPICIOUS partition no longer exists, so every formula is undefined.

**Why it happens:** Adding dispatch classes feels like "extend the enum." It is not. It requires re-deriving what detection, suppression, and decisiveness mean in a 5-class space before a single line of code is written.

**Consequences:** If SUSPICIOUS is removed from the output schema without updating the metric definitions first, TDR becomes undefined (what does "THREAT caught as SUSPICIOUS" mean when SUSPICIOUS is gone?), FASR remains calculable but loses its counterpart, decisiveness inverts (now 100% decisive by definition — useless), and the aggregate produces a number that means nothing.

**Prevention:** Define new metric semantics on paper before touching code. Specific questions to answer: Does "operator review" count as a partial detection for TDR purposes? Does "auto-suppress" count as suppression for FASR? What is the dispatch equivalent of decisiveness? Only after written answers to these do you change `ScoreReport`.

**Detection:** Tests that pass `SUSPICIOUS` in `verdict` will silently accept invalid dispatch classes once the schema is updated but before metrics are fixed. Write tests that assert metric invariants (e.g., TDR + miss_rate = 1.0) before changing the schema.

---

### Pitfall 2: `VERDICTS` Is the Viral Constant — It Touches Six Systems

**What goes wrong:** `schema.py` line 140 defines `VERDICTS = ("THREAT", "SUSPICIOUS", "BENIGN")`. This constant is imported and used in:
- `validation.py` line 95: rejects any output whose verdict is not in VERDICTS
- `validation.py` line 284: iterates VERDICTS to check class balance in ground truth
- `baselines.py` line 20: picks uniformly from VERDICTS for the random baseline
- `test_core.py` line 237: asserts every generated scenario's `_meta.ground_truth` is in VERDICTS
- `test_leakage.py` line 127: asserts exactly 3 GT classes exist
- `OUTPUT_SCHEMA` enum (schema.py line 123): schema validation rejects non-VERDICTS values
- `_META_SCHEMA_V2` ground_truth enum (schema.py line 148): same lock

Changing `VERDICTS` without understanding all six downstream uses produces either silent failures (baselines generate 5-class outputs that old scorers process as 0% accuracy) or hard crashes (jsonschema validation raises on every output that uses a new dispatch class).

**Why it happens:** The constant was designed as a single source of truth, which is correct. The mistake is treating "add to the tuple" as the change, when it's actually "change the type system across six consumers simultaneously."

**Consequences:** The 238 existing tests will fail in ways that appear unrelated to the change (balance checks, schema validation, baseline accuracy assertions, ground truth membership checks).

**Prevention:** Map every import of `VERDICTS` before changing it. The backward-compatible path is to add a separate `DISPATCH_CLASSES` constant and a `DISPATCH_OUTPUT_SCHEMA`, keeping `VERDICTS` unchanged for 3-class users. The `verdict` field stays as-is; a new `dispatch` field carries the 5-class decision. Existing outputs remain valid; new outputs carry both fields.

**Detection:** Run `grep -rn "VERDICTS" .` before committing any schema change. If the list is longer than you expect, stop and map it fully.

---

### Pitfall 3: The `verdict` vs. `dispatch` Architectural Decision Is a Gating Question

**What goes wrong:** The v4.0 milestone requires 5-class dispatch decisions. The current `OUTPUT_SCHEMA` requires `verdict` in `["THREAT", "SUSPICIOUS", "BENIGN"]`. There are exactly two paths:

**Path A — Replace:** `verdict` enum becomes the 5 dispatch classes. Every existing output file, test fixture, CLI command, and integration guide that uses `verdict` breaks immediately. The 3-class TDR/FASR metrics become meaningless. The 238 tests fail.

**Path B — Additive:** Keep `verdict` (3-class) required; add `dispatch` (5-class) optional. Existing users continue unaffected. New users populate both. The scorer adds a parallel scoring path for dispatch decisions. Backward compatibility is preserved by the field being optional.

**Why it matters:** This is the decision that determines the scope of every other change in v4.0. If Path A is chosen, the cost is a complete test suite overhaul and a breaking release. If Path B is chosen, the cost is two parallel scoring paths that must stay consistent.

**Consequences of deferring:** Every implementation decision made before resolving this choice may need to be undone. If you write cost-aware scoring using `verdict` and then decide to use `dispatch`, the scoring functions need to be rewritten.

**Prevention:** Commit to Path A or Path B in writing before writing any v4.0 code. The milestone context states "backward compatibility for 3-class triage users" — this is strong evidence for Path B.

---

### Pitfall 4: The Confusion Matrix Is Hardcoded as 3x3

**What goes wrong:** `scorer.py` lines 502–510 hardcode `labels = ["THREAT", "SUSPICIOUS", "BENIGN"]` and build a 3x3 confusion matrix. Downstream consumers in tests (`test_core.py` lines 357–359), the dashboard (`format_dashboard`), and any external tooling that parses JSON output all assume `confusion_matrix["THREAT"]["THREAT"]` is a valid key path.

**Why it matters:** With 5 dispatch classes, the confusion matrix becomes 5x5 (or N×3 if ground truth stays 3-class while predictions are 5-class). The former shape breaks all existing matrix tests. The latter shape is ambiguous and requires documenting which dimension is which.

**Prevention:** Define the confusion matrix shape explicitly before coding. If ground truth stays 3-class (THREAT/SUSPICIOUS/BENIGN) and predictions become 5-class dispatch, the matrix is 3 rows × 5 columns. Name both axes explicitly in the schema docs. Test the new shape with fixture data before wiring it to the dashboard.

**Detection:** `test_core.py` lines 345–359 will fail immediately if the matrix shape changes without updating the test.

---

### Pitfall 5: Cost Numbers Without Sensitivity Analysis Are Indefensible

**What goes wrong:** `VISION.md` quotes "$200-500 for false dispatch" and "potentially catastrophic" for missed threats. These are placeholders, not defensible values. If the benchmark publishes a single cost model without sensitivity analysis, any user can object that their armed response costs $50 (contracted security) or $2,000 (off-duty police). Different cost assumptions flip system rankings: System A beats System B at 10:1 missed-threat weight but loses at 3:1. A published benchmark that changes its winner based on cost assumptions is not a benchmark — it is a parameter choice.

**Why it happens:** The existing scorer already handles this correctly for safety scores (three weight ratios: 1:1, 3:1, 10:1 at `scorer.py` lines 442–444). The temptation is to add a single "operational cost" metric the same way accuracy was added: one number.

**Consequences:** The benchmark becomes a tool for cherry-picking results. A vendor running their system can find the cost ratio that makes them win and cite only that number.

**Prevention:** Follow the existing pattern: report expected operational cost at multiple cost ratio assumptions (e.g., false dispatch cost = 1x, 10x, 50x relative to operator review time). Never report a single operational cost score without the accompanying sensitivity table. The cost model must be documented with explicit assumptions and users must be able to supply their own cost vectors.

**Detection:** If any metric in `ScoreReport` is named `operational_cost` or `expected_cost` without a corresponding `operational_cost_params` that records what cost vector was used, the metric is non-reproducible.

---

### Pitfall 6: Multi-Site Generalization Testing Has Structural Leakage

**What goes wrong:** The generator already couples `site_type` to correlated features: zone names (ZONE_NAMES dict by zone type, `distributions.py`), device quality distributions (which are site-independent but the SITE_CATEGORY_BLOCKLIST in `generators.py` line 51 filters categories by site), and scenario descriptions (the shared pool is not stratified by site type, so frequency distributions of descriptions differ across sites). A "train on solar / test on commercial" split designed to measure generalization will leak site identity through these correlated features.

**Concrete example:** Solar scenarios never contain "Shoplifting" or "Robbery" categories (SITE_CATEGORY_BLOCKLIST line 51). A model fine-tuned on solar scenarios learns that Shoplifting → BENIGN is an impossible label. When tested on commercial scenarios where Shoplifting → THREAT, the model's prior is wrong. But the gap measured is not "does the model generalize?" — it is "did we accidentally teach the model site identity through category filtering?"

**Why it happens:** The SITE_CATEGORY_BLOCKLIST was correctly added to prevent contextual nonsense (no road accidents at indoor facilities). It was not designed with generalization testing in mind.

**Prevention:** When building multi-site splits, audit which generator features are correlated with site type. At minimum: verify that zone name vocabulary does not uniquely identify sites, verify that category distributions in the test split are not a strict subset of train split categories, and document which features a model could use as site-identity proxies. If a model can determine site type from the feature vector without using `context.site_type`, the generalization test is compromised.

**Detection:** Train a simple logistic regression on generated scenarios with `site_type` removed from input. If it can classify site type above chance from the remaining features, leakage exists.

---

## Moderate Pitfalls

### Pitfall 7: v4.0 "Adversarial" Conflicts with v2.0 `adversarial` Flag

**What goes wrong:** `_meta.adversarial` (schema.py line 156) currently marks scenarios where one context signal was deliberately flipped to create conflicting signals (e.g., HIGH severity + BENIGN ground truth). The injection logic is in `generators.py` `_inject_adversarial_signals` (line 157), which flips severity, zone type, or time-of-day. This is signal-conflict adversarial.

The v4.0 adversarial scenarios described in VISION.md are behavioral adversarial: "loitering that looks like authorized waiting," "authorized access that looks like intrusion," "environmental events that look like human activity." These are different — they involve plausible real-world deception scenarios, not mechanically inverted signal values.

If both are stored under `_meta.adversarial = True`, the metrics conflate two distinct model failure modes. A model failing on signal-conflict adversarial is failing on reasoning. A model failing on behavioral adversarial is failing on pattern recognition. These require different interventions.

**Prevention:** Add a new `_meta.adversarial_type` field with values like `"signal_conflict"` (existing) and `"behavioral_deception"` (new). Report adversarial metrics split by type.

---

### Pitfall 8: Decisiveness Becomes Meaningless in 5-Class Output

**What goes wrong:** Decisiveness is currently defined as "fraction of THREAT|BENIGN predictions (not SUSPICIOUS)." It measures whether the model avoids hedging. In a 5-class dispatch schema, if SUSPICIOUS is removed, every prediction is by definition "decisive" — the metric is 1.0 for all systems and provides no discriminative signal.

**Prevention:** Redefine decisiveness for 5-class: perhaps "fraction of predictions that are auto-suppress or armed response" (the two most definitive actions), or "fraction of predictions that are not operator-review" (the hedge equivalent). Document the new definition explicitly. Do not preserve the field name `decisiveness` if the formula changes; rename it to avoid silent semantic drift.

---

### Pitfall 9: The `score_multiple_runs` Key Metrics List Is a Maintenance Trap

**What goes wrong:** `scorer.py` lines 573–577 hardcode `key_metrics = ["accuracy", "tdr", "fasr", "safety_score_3_1", "ece", "aggregate_score", "suspicious_fraction", "decisiveness"]`. When new cost-aware metrics are added to `ScoreReport`, this list must be manually updated or the new metrics will not appear in multi-run statistical summaries.

**Prevention:** Either derive the key metrics list from `ScoreReport` field names with an annotation/tag, or add a test that asserts every `ScoreReport` field of type `float` appears in `key_metrics`.

---

### Pitfall 10: Seed Reproducibility Breaks If Generator Logic Changes

**What goes wrong:** `PROJECT.md` requires "same seed + same params = same scenarios." Any change to generator logic — including new site types, new adversarial scenario types, new category blocklist entries — changes the output for existing seeds. The `test_seed_regression.py` test exists explicitly to catch this.

**Prevention:** v4.0 scenario generation changes (new adversarial behavioral types, new dispatch-relevant metadata) must be gated behind a new `generation_version` value (currently `"v1"`, `"v2"`, `"v3"` in schema.py line 154). Existing scenarios at `generation_version: "v3"` must be unchanged. New v4.0 features generate at `generation_version: "v4"` with a new seed space. Do not mix generation versions in the same scenario set without explicit version-stratified analysis.

---

## Minor Pitfalls

### Pitfall 11: Evaluators Reference 3-Class in Prompt Templates

**What goes wrong:** `evaluators.py` line 27 contains the prompt: "Classify the alert as one of: THREAT, SUSPICIOUS, or BENIGN." Line 108 normalizes invalid verdicts to `"SUSPICIOUS"` as default. If v4.0 adds dispatch classes, the evaluator prompts must be updated, and the fallback normalization logic must change or it will silently convert unrecognized dispatch classes into SUSPICIOUS.

**Prevention:** Treat `evaluators.py` as a reference implementation, not production code. Any v4.0 dispatch evaluator should be a new file (`evaluators_v4.py`) rather than modifying the existing one, to preserve backward-compatible examples.

---

### Pitfall 12: Validation Balance Check Assumes 3 Classes at Minimum 5% Each

**What goes wrong:** `validation.py` lines 282–286 iterate over `VERDICTS` and warn if any class appears at less than 5% of scenarios. With 5 dispatch classes as ground truth, the balance check logic is wrong — there are now 5 classes to check, and the thresholds for acceptability may differ per class (armed response should be rare; auto-suppress may dominate).

**Prevention:** Update the balance check before any 5-class scenario generation runs. Otherwise validation will silently pass on badly imbalanced dispatch label distributions.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| 5-class output schema | `VERDICTS` viral change breaks 6 consumers simultaneously | Map all imports before any change; additive `dispatch` field preferred over replacing `verdict` |
| Metric re-derivation | TDR/FASR/Decisiveness are undefined in 5-class space | Write new definitions on paper before touching ScoreReport |
| Confusion matrix extension | Hardcoded 3x3 at scorer.py:502 breaks tests and dashboard | Define matrix shape (3×5 vs 5×5) before implementation |
| Cost model | Single cost number is non-reproducible and cherry-pickable | Report at multiple cost ratio assumptions; record params in output |
| Multi-site split construction | Site-type identity leaks through category distributions and zone vocabulary | Audit feature-site correlations; verify with site-type classifier probe |
| Adversarial scenario generation | v4.0 behavioral adversarial conflates with v2.0 signal-conflict adversarial flag | Add `adversarial_type` field; report metrics split by type |
| Seed regression | Generator logic changes break `test_seed_regression.py` | Gate all v4.0 generation under `generation_version: "v4"` |
| Backward compatibility | 3-class users break if `verdict` enum changes | Require `verdict` unchanged; `dispatch` is new optional field |
