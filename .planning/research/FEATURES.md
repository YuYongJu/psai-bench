# Feature Landscape

**Domain:** Physical security AI benchmark — operational decision-support evaluation
**Researched:** 2026-04-13
**Milestone scope:** v4.0 (5-class dispatch, cost-aware scoring, multi-site generalization, adversarial robustness)

---

## Framing: The Critical Design Decision

Before feature classification, one unresolved design question dominates v4.0:

**Are dispatch classes a replacement for the triage classification, or a second layer on top of it?**

VISION.md describes 5 dispatch actions (armed response, patrol, operator review, auto-suppress, request data). The current OUTPUT_SCHEMA has `verdict: THREAT | SUSPICIOUS | BENIGN`. These are conceptually different: one is a classification of the event, the other is an operational response decision.

**Option A — Two-layer:** Keep verdict (THREAT/SUSPICIOUS/BENIGN), add required `dispatch_action` field. Verdict explains what happened; dispatch_action says what to do. Backward compatible: old systems produce verdict only.

**Option B — Replace:** verdict becomes the 5-class dispatch label. Simpler schema, but breaks backward compatibility and loses the perception-vs-response distinction.

The research supports Option A. Real GSOCs make two decisions: (1) what is this? (2) what do I do about it? These aren't the same question. A THREAT in a parking lot warrants patrol; a THREAT in a restricted zone warrants armed response. The dispatch decision depends on threat classification AND site context. Option A preserves this distinction and maintains backward compatibility.

**This must be resolved before building v4.0 schema, scoring, or CLI.**

---

## Table Stakes

Features that a benchmark claiming "operational realism" cannot omit.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Cost-sensitive scoring framework | Field standard — accuracy-only is insufficient for asymmetric-cost domains (missed threat >> false dispatch) | Medium | Well-established theory (cost matrix, expected total cost — PMC5217743). Dollar amounts in VISION.md are assumptions, not industry data — mark as provisional. |
| Adversarial robustness test scenarios | Any "AI security" claim requires robustness characterization; NIST AI 100-2e2025 covers taxonomy | Low (scenarios already partially exist) | v2.0 has ~20% adversarial injection; v4.0 expands to semantic-level adversarials (distinct from pixel-perturbation literature) |
| Per-action breakdown in results | Without separating dispatch classes, the score is uninterpretable for operators | Low | Same philosophy as v2.0's separate metric dashboard |
| Updated output schema | Any new dispatch output field needs schema validation and docs | Low | Must preserve backward compat (v1.0 verdict-only still valid) |

## Differentiators

Features that would distinguish PSAI-Bench from any existing benchmark.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 5-class dispatch output evaluation | No existing benchmark evaluates operational dispatch decisions — CyberSOCEval (MCQ accuracy), ExCyTIn-Bench (multistep agent tasks), NIST frameworks (capability maturity) — all classify or reason, none score a dispatch action | Medium | Requires new GT mapping: what is the "correct" dispatch for each scenario? |
| Dispatch-conditioned cost model | Expected operational cost scoring ties benchmark results directly to dollars, the language of security operations buyers | Medium | Cost matrix structure is established (ordinal cost via linear absolute loss); dollar values need domain validation |
| Multi-site generalization testing | Equivalent to leave-one-domain-out in domain generalization literature; site types (solar/substation/commercial/campus) are the "domains" | High | Novel because: (a) site-specific GT already exists in schema, (b) no benchmark does this for physical security, (c) methodologically grounded in CVPR 2024 "Rethinking Evaluation Protocol" |
| Semantic adversarial scenarios | Distinct from pixel-perturbation adversarial ML — context signal manipulation (authorized access presenting as intrusion) is "natural adversarial" and directly attacks the multi-signal reasoning the benchmark tests | Medium | Positions PSAI-Bench in natural adversarial examples literature, not input perturbation literature |

## Anti-Features

Features to explicitly not build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Single aggregate dispatch score | Hides which dispatch class is failing; a system that never calls armed response scores identically to one that always calls it — one hides threats, one bankrupts the client | Report per-class precision/recall + expected cost separately |
| Cost model with hardcoded dollar amounts | $200-500 armed response, $5-15 operator review (VISION.md) are plausible but uncited assumptions; locking them in creates wrong baselines | Make cost values configurable parameters with documented defaults and a --cost-profile flag |
| Collapsing dispatch into 3-class GT | Mapping armed_response→THREAT, patrol→SUSPICIOUS, auto_suppress→BENIGN loses the operational nuance (a patrol-to-restricted-zone is not the same as a SUSPICIOUS verdict) | Keep dispatch GT as its own 5-class taxonomy |
| Adversarial scenarios that require video processing | v4.0 semantic adversarials are context-signal-level, not pixel-level — building video perturbation attacks is out of scope and out of domain | Stay in the textual/metadata adversarial space |
| Training the benchmark on a single site, testing on the same | This is the status quo and what generalization testing is meant to challenge | Require hold-out site evaluation in the multi-site protocol |

---

## Feature Details by Area

### 1. Five-Class Dispatch Decisions

**What industry does:** Real GSOCs (HiveWatch, VectorFlow, similar) use AI to route alerts to action tiers. The typical taxonomy confirmed in industry sources: armed/law enforcement dispatch (highest urgency, highest cost), security patrol dispatch (medium urgency), operator review queue (human-in-loop), auto-suppress/resolve (verified benign), and request additional data (pan camera, check adjacent feeds). This is not a benchmark invention — it reflects actual GSOC decision flow.

**Ground truth challenge:** Dispatch GT requires a documented decision function that combines verdict with site context. The same THREAT verdict at a solar perimeter → patrol; at a substation control room → armed response. The decision function must be published and auditable, consistent with v2.0 philosophy.

**Output schema impact:**
- Add `dispatch_action: "ARMED_RESPONSE" | "PATROL" | "OPERATOR_REVIEW" | "AUTO_SUPPRESS" | "REQUEST_DATA"` (required for v4.0 systems)
- Keep `verdict: THREAT | SUSPICIOUS | BENIGN` (required for all; backward compat)
- v1.0/v2.0/v3.0 outputs remain valid — scoring dispatches only when dispatch_action present

**Ordinal structure:** Dispatch classes have a natural partial ordering by urgency and cost: ARMED_RESPONSE > PATROL > OPERATOR_REVIEW > AUTO_SUPPRESS, with REQUEST_DATA orthogonal (it's a data-gathering action, not a threat-response action). This partial order should inform the cost matrix design.

### 2. Cost-Aware Scoring

**Mathematical framework (HIGH confidence):** The ordinal cost-sensitive literature (PMC5217743) provides the standard approach:

- Cost matrix C where C[i][j] = cost of predicting class j when true class is i
- Total classification cost TC = trace(C × F^T) where F is the confusion matrix
- For ordinal classes, off-diagonal entries scale with distance: C[i][j] ∝ |j - i|

**For dispatch-specific costs:** The cost asymmetry is extreme and non-symmetric:
- False ARMED_RESPONSE: ~$200-500 per dispatch (VISION.md estimate — needs validation)
- Missed ARMED_RESPONSE when needed: catastrophic (life-safety or major loss)
- OPERATOR_REVIEW when AUTO_SUPPRESS correct: ~$5-15 operator time
- AUTO_SUPPRESS when OPERATOR_REVIEW needed: missed review opportunity (lower stakes)

**Implementation approach:** Expected Operational Cost (EOC) metric:
```
EOC = sum over all scenarios: cost_matrix[true_dispatch][predicted_dispatch] / N
```
Report EOC alongside per-class precision/recall. Do not fold EOC into a single aggregate.

**Cost profile configurability:** Users need to plug in their own cost assumptions. A `--cost-profile` option with a JSON cost matrix + a documented default profile that matches VISION.md's estimates. This is table stakes for the feature to be useful — a solar farm and a hospital have different cost structures.

### 3. Multi-Site Generalization Testing

**Domain generalization framing (HIGH confidence):** This maps directly to leave-one-domain-out (LODO) evaluation from the domain generalization literature. Site types = domains. Evaluation protocol: generate scenarios across N site types, hold out one site type, measure performance on the held-out site.

**What the CVPR 2024 "Rethinking Evaluation Protocol" finding means for PSAI-Bench:** Validation data must come from the training distribution, not the test domain. For PSAI-Bench: any prompt tuning or system calibration a user does cannot use held-out-site scenarios. The evaluation protocol document must specify this constraint.

**Site types in existing schema:** `site_type` field already exists in schema.py with enum ["solar", "substation", "commercial", "industrial", "campus"]. This is the domain taxonomy to use.

**Generalization Gap metric:** GG = performance_on_trained_sites - performance_on_held_out_site. Report per site type, not just aggregate. A system that collapses on commercial sites but excels at solar is a different risk profile than one that degrades uniformly.

**GT implications:** Some adversarial scenarios are site-specific by design (solar-specific wildlife, substation-specific environmental). GT distribution will differ across site types — this is expected and should be documented.

### 4. Adversarial Robustness

**PSAI-Bench adversarials are semantic, not pixel-perturbation (HIGH confidence):** The adversarial ML literature (NIST AI 100-2e2025, springer reviews) focuses on input perturbations, adversarial patches, and prompt injection. PSAI-Bench v4.0 adversarials are fundamentally different — they are "natural adversarial examples" where context signals are internally consistent but designed to produce a counterintuitive ground truth.

**Four semantic adversarial categories for v4.0:**
1. **Authorized-as-intrusion:** Person near restricted zone with expired badge credential, recent zone activity logged. Looks like authorized maintenance; GT = THREAT (badge expired, no active maintenance scheduled).
2. **Loitering-as-authorized-waiting:** Person stationary near entrance for 15 min, during business hours, no badge event. Looks threatening; GT = BENIGN (scheduled delivery pickup, expected_activities includes it).
3. **Environmental-as-human:** PIR trigger + camera detects moving object + thermal shows heat signature. Looks like THREAT; GT = BENIGN (confirmed via adjacent camera: HVAC exhaust duct).
4. **Social engineering pattern:** Sequential badge attempts across multiple entry points across 20 min. Multi-alert temporal pattern; GT = THREAT. Requires sequence track to express properly.

**Distinction from v2.0 adversarials:** v2.0 adversarials are signal-level conflicts (HIGH severity + BENIGN GT). v4.0 adversarials are scenario-level: the signals are consistent, but the correct reasoning requires domain knowledge that naive pattern-matching misses. This is the harder and more interesting case.

**Robustness metric:** Adversarial Accuracy Drop (AAD) = accuracy_on_standard - accuracy_on_adversarial_subset. Report separately from overall metrics. A system with low AAD has robust reasoning; high AAD means it's pattern-matching on surface features.

---

## Feature Dependencies

```
dispatch_action field → updated output schema
updated output schema → updated validation
updated output schema → updated CLI score command
cost-aware scoring → dispatch_action field (needs dispatch GT)
cost-aware scoring → cost matrix configuration
cost-aware scoring → Expected Operational Cost metric

multi-site generalization → site_type in scenarios (already exists)
multi-site generalization → updated evaluation protocol document
multi-site generalization → new CLI flag or sub-command for hold-out evaluation

adversarial scenarios → scenario generation updates
adversarial scenarios → updated _meta schema (adversarial_type field)
adversarial scenarios → Adversarial Accuracy Drop metric
```

---

## MVP Recommendation for v4.0

**Build first (blocks everything else):**
1. Resolve two-layer vs. replace design decision — write decision record before touching schema
2. Update OUTPUT_SCHEMA with dispatch_action (backward compatible)
3. Update _META_SCHEMA with dispatch_gt and adversarial_type fields
4. Define dispatch GT decision function and document it

**Build second (core value):**
5. Cost matrix framework with configurable cost profiles
6. Expected Operational Cost metric + per-class dispatch breakdown
7. Expand adversarial scenario generation with v4.0 semantic categories
8. Adversarial Accuracy Drop metric

**Build third (differentiator):**
9. Multi-site generalization evaluation protocol and CLI
10. Generalization Gap metric per site type
11. Updated evaluation protocol document covering all four v4.0 additions

**Defer:**
- Video-based adversarial scenarios (out of scope per VISION.md, too complex)
- Automated cost profile inference (user provides cost matrix; benchmark doesn't guess it)
- Multi-site scenario rebalancing (ensure site type distribution is documented, not forced-equal)

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| 5-class dispatch taxonomy | HIGH | Confirmed against GSOC industry sources (HiveWatch, SIA) |
| Cost matrix math framework | HIGH | PMC5217743, well-established ordinal classification literature |
| Dollar cost estimates | LOW | VISION.md figures are plausible assumptions, not sourced from industry data |
| Multi-site generalization methodology | HIGH | Direct mapping to domain generalization literature (LODO evaluation); CVPR 2024 evaluation protocol paper |
| Adversarial scenario classification | HIGH | NIST AI 100-2e2025 confirms semantic adversarials are distinct from perturbation attacks |
| No existing benchmark has 5-class dispatch evaluation | HIGH | CyberSOCEval (MCQ), ExCyTIn-Bench (agent tasks), SandboxAQ (maturity model) — none score operational dispatch actions |

---

## Sources

- PMC5217743: Cost-Sensitive Performance Metric for Comparing Multiple Ordinal Classifiers — https://pmc.ncbi.nlm.nih.gov/articles/PMC5217743/
- NIST AI 100-2e2025: Adversarial Machine Learning Taxonomy — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2025.pdf
- CyberSOCEval (CrowdStrike + Meta, Sep 2025) — https://arxiv.org/html/2509.20166v2
- Cost-Sensitive Evaluation for Binary Classifiers (arXiv 2510.22016) — https://arxiv.org/abs/2510.22016
- CVPR 2024 "Rethinking the Evaluation Protocol of Domain Generalization" — https://openaccess.thecvf.com/content/CVPR2024/papers/Yu_Rethinking_the_Evaluation_Protocol_of_Domain_Generalization_CVPR_2024_paper.pdf
- SIA "Transforming Physical Security: How AI is Changing the GSOC" (Mar 2025) — https://www.securityindustry.org/2025/03/03/transforming-physical-security-how-ai-is-changing-the-gsoc/
- HiveWatch GSOC OS — https://hivewatch.com/gsoc-operating-system/
