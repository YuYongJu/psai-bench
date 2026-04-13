# Project Research Summary

**Project:** psai-bench — v4.0 Operational Realism
**Domain:** Physical security AI benchmark — operational decision-support evaluation
**Researched:** 2026-04-13
**Confidence:** HIGH (stack and architecture), MEDIUM (features), LOW (cost dollar values)

## Executive Summary

PSAI-Bench v4.0 extends a working 3-class benchmark (THREAT/SUSPICIOUS/BENIGN) into an operationally realistic evaluation suite for physical security AI systems. The four additions — 5-class dispatch decisions, cost-aware scoring, multi-site generalization testing, and semantic adversarial robustness — are all implementable as additive changes within the existing Python stack (numpy, jsonschema, click, pandas, scikit-learn). No new dependencies are required beyond declaring the already-used scipy as a direct dependency in pyproject.toml. The core architectural constraint is that dispatch classes are a parallel optional output field alongside verdict, not a replacement for it. This decision is resolved and must be treated as locked before any schema code is written.

The central technical challenge is that the existing codebase bakes 3-class assumptions into six separate locations (VERDICTS constant, OUTPUT_SCHEMA enum, _META_SCHEMA_V2 ground_truth enum, scorer.py metrics, baselines.py outputs, and validation.py balance checks). Every v4.0 change must be additive around these coupling points. The build order enforces this: schema extension first (zero breaking changes), then the isolated cost_model.py module, then baselines, then scorer extension, then new generators, then CLI wiring, then comprehensive tests. Each step is independently testable before the next begins.

The primary risk is not technical complexity but defensibility of the cost model. The dollar values in VISION.md ($200-500 per false armed response, ~$5-15 for operator review time) are plausible assumptions, not validated industry figures. A single expected-cost number without sensitivity analysis is non-reproducible and cherry-pickable. The mitigation is already established by the existing scorer pattern: report expected operational cost at multiple cost-ratio assumptions and require the cost vector to be recorded in output metadata. Make cost profiles user-configurable via JSON so operators can supply their actual costs.

## Key Findings

### Recommended Stack

The entire v4.0 feature set is implementable in the current stack. Direct inspection of pyproject.toml and all source modules confirms that numpy handles all new scoring math (cost lookups, 5-class confusion matrices, site-type partitioning), jsonschema validates schema extensions, click handles new CLI commands, and the numpy RandomState isolation pattern already provides deterministic adversarial injection. One latent packaging bug must be fixed: scipy is imported in statistics.py but not declared in pyproject.toml as a direct dependency. This creates a fragile transitive dependency through scikit-learn and must be corrected in v4.0 regardless of new features.

**Core technologies:**
- `numpy>=1.24`: All new scoring math — cost dot products, per-site accuracy arrays, 5-class confusion matrix
- `jsonschema>=4.0`: Schema validation for optional dispatch field and new _meta fields
- `click>=8.0`: Three new CLI commands (score-dispatch, site-generalization, generate adversarial_v4) plus new flags on existing commands
- `scipy>=1.10` (declare as direct): Already used in statistics.py for McNemar's test and bootstrap CIs — undeclared dependency that must be formalized

**Alternatives rejected:**
- `pulp`/`scipy.optimize` for cost minimization: overkill — cost scoring is expected value arithmetic, not optimization
- `faker` for adversarial text generation: v4.0 adversarials use fixed description pools for deterministic reproducibility
- `sklearn.metrics.classification_report`: existing numpy-direct metrics are sufficient and match documented formulas

### Expected Features

**Must have (table stakes):**
- Cost-sensitive scoring framework — accuracy-only is insufficient for asymmetric-cost domains where a missed threat costs orders of magnitude more than a false dispatch
- Per-action breakdown in results — a system that never calls armed response scores identically to one that always calls it without class-level reporting
- 5-class dispatch output field (optional, backward-compatible) — `dispatch` alongside `verdict` in OUTPUT_SCHEMA
- Updated _meta schema with `optimal_dispatch` and `adversarial_type` fields
- Adversarial robustness scenarios with distinct metric (Adversarial Accuracy Drop)

**Should have (differentiators):**
- Dispatch-conditioned cost model with configurable cost profiles (--cost-profile JSON flag) — no existing benchmark evaluates operational dispatch decisions in cost terms
- Multi-site generalization evaluation using leave-one-domain-out protocol — novel for physical security, methodologically grounded in domain generalization literature
- Semantic adversarial scenarios (loitering-as-waiting, authorized-as-intrusion, environmental-as-human) — distinct from pixel-perturbation attacks; tests domain reasoning, not signal processing
- `site-generalization` CLI command with per-site-type generalization gap reporting

**Defer (v2+):**
- Video-based adversarial scenarios — out of scope per VISION.md; textual/metadata adversarials are the right domain
- Automated cost profile inference — user supplies cost matrix; benchmark does not guess it
- Multi-site scenario rebalancing — document distribution, do not force equal class counts
- Social engineering pattern adversarial (multi-alert temporal sequences) — requires sequence track infrastructure not yet in scope

### Architecture Approach

v4.0 follows a strictly additive integration pattern. The 3-class verdict system (THREAT/SUSPICIOUS/BENIGN) is preserved in all existing paths. A new optional `dispatch` field carries the 5-class operational decision. A new isolated module (cost_model.py) handles all dispatch cost logic with no coupling to existing scoring code. New generators live in separate classes with isolated RNG state to prevent seed regression. All new CLI commands are additive; all existing commands remain backward-compatible when new flags are absent.

**Major components:**
1. `schema.py` extension — adds optional `dispatch` field to OUTPUT_SCHEMA, `optimal_dispatch` and `adversarial_type` to _META_SCHEMA_V2, `DISPATCH_ACTIONS` constant; zero breaking changes
2. `psai_bench/cost_model.py` (new) — `DISPATCH_COSTS` lookup table, `SITE_THREAT_MULTIPLIERS`, `compute_optimal_dispatch(gt, context)`, `score_dispatch()`, `CostScoreReport` dataclass; fully isolated from existing modules until scorer imports it
3. `scorer.py` extension — new `score_dispatch_run()` alongside `score_run()`; `format_dashboard()` gains optional `cost_report` parameter; `_score_partition`, `score_run`, and `ScoreReport` are untouched
4. `baselines.py` extension — `VERDICT_TO_DEFAULT_DISPATCH` mapping adds `dispatch` field to all 4 baseline outputs; no signature changes
5. `AdversarialV4Generator` (new class in generators.py) — isolated RNG, `ADV_V4_*` description pools in distributions.py (separate from existing pools to prevent RNG contamination)
6. Multi-site generalization — `compute_site_generalization_gap()` in scorer.py, `--site-type` filter on `generate` CLI (post-generation filtering to preserve seed reproducibility)
7. `cli.py` wiring — three new commands, two modified commands; backward-compat defaults everywhere

**Data flows:**
- Standard path (unchanged): `score_run()` → `ScoreReport` → `format_dashboard()`
- Dispatch path (new, additive): `score_dispatch_run()` → `CostScoreReport` → `format_dashboard(cost_report=...)`
- Site generalization path (new): `compute_site_generalization_gap(train_site, test_site)` → gap dict
- Adversarial analysis path (new): `score_run()` → `partition_by_adversarial_type()` → per-type accuracy breakdown

### Critical Pitfalls

1. **VERDICTS is a viral constant touching 6 consumers** — changing it breaks validation.py, baselines.py, test_core.py, test_leakage.py, OUTPUT_SCHEMA, and _META_SCHEMA_V2 simultaneously. Prevention: add `DISPATCH_ACTIONS` as a separate constant; keep `VERDICTS` unchanged; `dispatch` is a new optional field, never replacing `verdict`.

2. **Metric definitions (TDR/FASR/Decisiveness) are undefined in 5-class space** — if SUSPICIOUS disappears, TDR has no partial-detection class and decisiveness becomes trivially 1.0. Prevention: write new metric semantics on paper before touching ScoreReport. The backward-compat mapping resolves this: ARMED_RESPONSE+PATROL map to THREAT-equivalent, AUTO_SUPPRESS to BENIGN-equivalent, OPERATOR_REVIEW+REQUEST_DATA to SUSPICIOUS-equivalent.

3. **Cost model without sensitivity analysis is non-reproducible** — VISION.md dollar values are provisional assumptions; different cost ratios flip system rankings. Prevention: report expected cost at multiple cost-ratio assumptions; record cost vector in output metadata; expose --cost-profile flag.

4. **Seed reproducibility breaks if generator RNG sequences change** — adding new rng.choice() calls inside existing generators shifts all downstream outputs for the same seed, breaking test_seed_regression.py. Prevention: new generators get new isolated np.random.RandomState instances; all v4.0 generation gated under generation_version "v4".

5. **Multi-site generalization has structural site-identity leakage** — SITE_CATEGORY_BLOCKLIST means solar scenarios never contain Shoplifting/Robbery categories, so a model can infer site type from category distribution without seeing context.site_type. Prevention: run a logistic regression probe with site_type masked before publishing any generalization metric.

## Implications for Roadmap

All 4 researchers converge on the same build order. The grouping below maps their 8-step sequence into phases that can be planned, tracked, and tested independently.

### Phase 1: Schema and Cost Model Foundation

**Rationale:** Every other v4.0 change depends on the schema contract (what fields exist, what values they accept) and the cost model (what optimal_dispatch means for a given GT+context pair). These two components have zero coupling to each other during construction but everything downstream depends on both being stable.

**Delivers:** Extended OUTPUT_SCHEMA (optional dispatch field), extended _META_SCHEMA_V2 (optimal_dispatch, adversarial_type), DISPATCH_ACTIONS constant, new cost_model.py with DISPATCH_COSTS table, SITE_THREAT_MULTIPLIERS, compute_optimal_dispatch(), score_dispatch(), CostScoreReport dataclass, scipy declared as direct dependency in pyproject.toml.

**Addresses:** 5-class dispatch output schema (table stakes), cost-aware scoring framework (table stakes), configurable cost profiles (differentiator)

**Avoids:** VERDICTS viral constant breaking 6 consumers (Pitfall 2); backward compatibility for v1/v2/v3 outputs (Pitfall 3); metric undefined state (Pitfall 1) — documented 3→5 class mapping before code

**Open decision requiring resolution in this phase:** The exact compute_optimal_dispatch decision rule — which GT × site_type × zone_sensitivity combinations map to which dispatch action. Must be written as a decision table before implementation.

### Phase 2: Scoring Pipeline and Baselines

**Rationale:** With schema and cost model stable, the scoring pipeline can be extended and baselines updated. These are additive changes to existing files with established patterns to follow.

**Delivers:** score_dispatch_run() function in scorer.py, format_dashboard() extended with optional cost_report parameter (default None), VERDICT_TO_DEFAULT_DISPATCH mapping in baselines.py, dispatch field added to all 4 baseline outputs, updated score_multiple_runs key_metrics list.

**Addresses:** Per-action breakdown in results (table stakes), cost ratio reporting at multiple assumptions (anti-cherry-pick)

**Avoids:** Hardcoded 3x3 confusion matrix breakage (Pitfall 4) — cost scoring uses separate CostScoreReport, not ScoreReport; score_multiple_runs key_metrics maintenance trap (Pitfall 9)

### Phase 3: Adversarial v4 Generator

**Rationale:** AdversarialV4Generator is self-contained — isolated RNG, isolated description pools, isolated adversarial_type value. Does not touch existing generators or scoring path. Build before multi-site to keep phase scope minimal.

**Delivers:** AdversarialV4Generator class in generators.py, ADV_V4_LOITERING_AS_WAITING, ADV_V4_AUTHORIZED_AS_INTRUSION, ADV_V4_ENVIRONMENTAL_AS_HUMAN description pools in distributions.py (isolated from existing pools), adversarial_v4 track added to ALERT_SCHEMA enum, meta.adversarial_type field populated, generate --track adversarial_v4 CLI command, Adversarial Accuracy Drop metric.

**Addresses:** Semantic adversarial robustness scenarios (differentiator), adversarial_type field distinguishing signal-conflict (v2) from behavioral deception (v4) (table stakes for interpretability)

**Avoids:** v4 adversarial conflating with v2 signal-conflict flag (Pitfall 7) — separate adversarial_type values; seed reproducibility breakage (Pitfall 10) — isolated RNG and separate ADV_V4_* pools

**Open decision requiring resolution before this phase:** Ground truth assignment rule for behavioral adversarials. Recommended: use assign_ground_truth_v2 on actual context signals, not adversarial narrative.

### Phase 4: Multi-Site Generalization

**Rationale:** Highest complexity feature. Requires a structural leakage audit before implementation — SITE_CATEGORY_BLOCKLIST creates site-identity signal that may compromise the generalization test's validity. Build after all other features are stable; any discovered leakage problem is self-contained and does not block other phases.

**Delivers:** compute_site_generalization_gap(scenarios, outputs, train_site, test_site) in scorer.py, --site-type option on generate CLI (post-generation filter, seed-safe), site-generalization CLI command, per-site-type accuracy reporting, Generalization Gap metric.

**Addresses:** Multi-site generalization testing (differentiator), LODO evaluation protocol

**Avoids:** Structural site leakage through category distributions (Pitfall 6) — leakage audit step required before metric is published; audit must run a logistic regression probe with site_type masked and verify chance-level site classification from remaining features

**Evaluation protocol note:** Any prompt tuning or system calibration a user performs cannot use held-out-site scenarios. This constraint must be documented before multi-site results are accepted as benchmark submissions.

### Phase 5: CLI Integration and Tests

**Rationale:** All new functions, classes, and modules exist but are unwired from the CLI and lack comprehensive tests. Wire everything together and verify backward compatibility across v1/v2/v3 scenario files.

**Delivers:** score --include-dispatch flag, score-dispatch command, site-generalization command, baselines updated to print dispatch distribution, full test suite covering schema validation, cost model unit tests, dispatch scoring integration, multi-site filtering, AdversarialV4Generator output validation, end-to-end flow: generate v4 → run baselines → score dispatch → assert cost_ratio.

**Addresses:** CLI backward compatibility for all existing commands, estimated +50-80 new tests alongside 238 existing (all must pass)

**Avoids:** evaluators.py silent conversion of unrecognized dispatch classes to SUSPICIOUS (Pitfall 11) — any v4.0 dispatch evaluator is a new file (evaluators_v4.py); validation balance check assuming 3 classes (Pitfall 12) — update balance check before any 5-class generation runs

### Phase Ordering Rationale

- Schema and cost model first because the dispatch field definition is the dependency all other work requires
- Cost model is isolated enough to build in Phase 1 before any consumers exist and can be fully unit-tested in isolation
- Baselines and scorer (Phase 2) are the next natural consumers; both are additive-only changes with existing patterns to follow
- Adversarial v4 (Phase 3) is self-contained and benefits from stable schema to validate against; does not depend on scorer changes
- Multi-site (Phase 4) comes last in the feature work because it requires an audit step that could surface architectural issues; better to have all other work stable before discovering leakage problems
- CLI and tests (Phase 5) wires the entire system and validates integration across all phases simultaneously

### Research Flags

Phases needing `/gsd-research-phase` during planning:
- **Phase 1 (Cost Model):** Dollar values in VISION.md are provisional assumptions (LOW confidence). The cost ratio sensitivity analysis design needs a defensible methodology before implementation. The optimal_dispatch decision rule requires a written, auditable decision table.
- **Phase 3 (Adversarial v4):** Behavioral adversarial GT assignment rule needs explicit documentation. The boundary between "signals determine GT" and "narrative determines GT" must be resolved in writing before any scenarios are generated.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Scoring Pipeline):** Additive functions alongside existing ones; optional parameters with backward-compatible defaults. The existing codebase has multiple direct examples to follow.
- **Phase 4 (Multi-Site):** LODO evaluation is well-documented methodology. Main risk is the leakage audit, which is a concrete engineering task, not an unknown pattern.
- **Phase 5 (CLI + Tests):** Standard CLI wiring and test patterns already established across 238 existing tests.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All conclusions from direct source file inspection; no external dependencies required; undeclared scipy dependency confirmed in statistics.py |
| Features | HIGH (taxonomy), LOW (costs) | 5-class dispatch taxonomy confirmed against GSOC industry sources; cost dollar values are VISION.md assumptions with no industry validation |
| Architecture | HIGH | Build order, component boundaries, and anti-patterns grounded in direct codebase analysis with specific line references |
| Pitfalls | HIGH | All 12 pitfalls cite specific file locations and line numbers; VERDICTS viral constant map is complete |

**Overall confidence:** HIGH — with one bounded LOW-confidence area (cost dollar values) that has a clear mitigation path (configurable profiles + multi-assumption reporting).

### Gaps to Address

- **Cost dollar values (LOW confidence):** VISION.md figures are plausible assumptions, not sourced from industry data. Handle by: (1) labeling defaults as "provisional benchmark assumptions" in documentation, (2) requiring --cost-profile to record the cost vector used in output metadata, (3) reporting expected cost at minimum 3 cost-ratio assumptions before declaring any system ranking. Phase 1 research flag should include finding or constructing a defensible source for default values.

- **optimal_dispatch decision rule:** The rubric for compute_optimal_dispatch(gt, context) is described in general terms but not fully specified. The exact mapping of GT × site_type × zone_sensitivity → dispatch action must be written as a decision table before implementation, or the benchmark's reference answers are undefined.

- **Site leakage audit scope:** PITFALLS.md identifies SITE_CATEGORY_BLOCKLIST as a structural leakage source. ARCHITECTURE.md does not address this. The leakage audit in Phase 4 may reveal that the multi-site generalization metric requires more foundational work than the phase scope assumes. Flag as potential phase-scope risk.

- **Social engineering adversarial deferred:** FEATURES.md includes a 4th behavioral adversarial category (multi-alert temporal sequence) that ARCHITECTURE.md omits from AdversarialV4Generator. This is intentionally deferred but must be documented so it does not surface as a gap during Phase 3 planning.

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `psai_bench/scorer.py`, `psai_bench/schema.py`, `psai_bench/generators.py`, `psai_bench/distributions.py`, `psai_bench/statistics.py`, `psai_bench/baselines.py`, `psai_bench/validation.py` — all findings cite specific line numbers
- `pyproject.toml` — confirmed declared dependencies and missing scipy
- `.planning/PROJECT.md` — "No new dependencies unless strictly needed for scenario generation" constraint
- `.planning/VISION.md` — v4.0 dispatch class definitions and provisional cost values
- PMC5217743: Cost-Sensitive Performance Metric for Comparing Multiple Ordinal Classifiers
- NIST AI 100-2e2025: Adversarial Machine Learning Taxonomy
- CVPR 2024 "Rethinking the Evaluation Protocol of Domain Generalization"

### Secondary (MEDIUM confidence)

- HiveWatch GSOC OS documentation — 5-class dispatch taxonomy confirmed against real GSOC decision flow
- SIA "Transforming Physical Security: How AI is Changing the GSOC" (Mar 2025) — operational context for dispatch decisions
- CyberSOCEval (CrowdStrike + Meta, Sep 2025) — confirmed no existing benchmark scores operational dispatch actions
- Cost-Sensitive Evaluation for Binary Classifiers (arXiv 2510.22016) — cost matrix framework

### Tertiary (LOW confidence)

- VISION.md cost dollar values ($200-500 armed response, $5-15 operator review) — plausible assumptions; no independent industry validation found

---
*Research completed: 2026-04-13*
*Ready for roadmap: yes*
