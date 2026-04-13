# Dispatch Decision Rubric — PSAI-Bench v4

This document describes the exact logic used by `compute_optimal_dispatch(gt, context)`
(implemented in `psai_bench/cost_model.py`) to assign the benchmark-optimal dispatch action
to each scenario. A researcher who reads only this document can reproduce any scenario's
`optimal_dispatch` label by hand, given the ground truth verdict and three context signals.

---

## 1. Overview

Dispatch is a parallel decision alongside ground truth (GT). Where GT answers *"how serious
is this alert?"*, dispatch answers *"what action should an operator take?"* given the
classification AND site context.

**GT alone does not determine dispatch.** A THREAT at a substation warrants an armed response;
a THREAT at a commercial property during business hours warrants only a patrol. Dispatch
captures this operational nuance.

Dispatch has exactly 5 classes, defined by the `DISPATCH_ACTIONS` constant in
`psai_bench/schema.py`:

| Action | Meaning |
|--------|---------|
| `armed_response` | Escalate to armed security or law enforcement |
| `patrol` | Send a physical patrol to verify |
| `operator_review` | Flag for human operator review; no physical response yet |
| `auto_suppress` | Suppress alert automatically; no action required |
| `request_data` | Request additional sensor data before deciding |

The three inputs to `compute_optimal_dispatch(gt, context)` are:

| # | Input | Source field |
|---|-------|-------------|
| 1 | Ground truth verdict | `gt` ∈ `{"THREAT", "SUSPICIOUS", "BENIGN"}` |
| 2 | Site type | `context["site_type"]` ∈ `{"substation", "solar", "industrial", "campus", "commercial"}` |
| 3 | Zone sensitivity | `context["zone"]["sensitivity"]` — integer 1–5 |

For BENIGN verdicts, two additional signals apply:

| # | Input | Source field |
|---|-------|-------------|
| 4 | Device false positive rate | `context["device"]["false_positive_rate"]` — float 0.0–1.0 |
| 5 | Recent zone event count | `len(context["recent_zone_events_1h"])` — integer ≥ 0 |

---

## 2. Primary Decision Table (GT × site_type × zone_sensitivity)

### 2.1 GT = THREAT

| Condition | Dispatch |
|-----------|----------|
| `site_type` ∈ `{"substation", "solar"}` | `armed_response` |
| `zone_sensitivity` ≥ 4 (any site) | `armed_response` |
| `site_type` ∈ `{"industrial", "campus"}` AND `zone_sensitivity` ∈ {2, 3} | `patrol` |
| `site_type` == `"commercial"` AND `zone_sensitivity` ≤ 3 | `patrol` |
| `zone_sensitivity` == 1 (any site) | `patrol` |

Rules are evaluated top-to-bottom; first match wins.

**Rationale:** Substations and solar farms are critical infrastructure where any confirmed
threat warrants immediate escalation regardless of zone sensitivity. High-sensitivity zones
(≥ 4) at other site types also warrant escalation. Low-sensitivity zones (sensitivity 1) cap
the response at patrol — a confirmed threat in a low-confidence zone should be verified
physically before escalating.

### 2.2 GT = SUSPICIOUS

| Condition | Dispatch |
|-----------|----------|
| `zone_sensitivity` ≥ 4 | `patrol` |
| `zone_sensitivity` ≤ 3 | `operator_review` |

**Rationale:** A suspicious (unconfirmed) alert in a high-sensitivity zone warrants a physical
check; the cost of a false negative is high. In lower-sensitivity zones, operator review
suffices — a human can decide whether to escalate.

### 2.3 GT = BENIGN

| Condition | Dispatch |
|-----------|----------|
| `device.false_positive_rate` ≥ 0.70 | `auto_suppress` |
| `device.false_positive_rate` < 0.70 AND `len(recent_zone_events_1h)` ≥ 3 | `request_data` |
| otherwise | `auto_suppress` |

**Rationale:** An unreliable device (FPR ≥ 0.70) generating a benign-GT alert should be
suppressed automatically — the alert is not credible. A reliable device generating an unusual
frequency of alerts (≥ 3 events in the last hour) in a benign context warrants data collection
before any action. All other benign alerts are safely suppressed.

---

## 3. Site Threat Multipliers (for cost model)

These multipliers scale the cost matrix THREAT column entries. Higher-criticality sites carry
greater cost for missed threats.

| Site type | Multiplier |
|-----------|-----------|
| `substation` | 5.0 |
| `solar` | 3.0 |
| `industrial` | 2.5 |
| `campus` | 2.0 |
| `commercial` | 1.5 |

The multiplier applies **only to THREAT-column cells** of the cost matrix (Section 5). The
SUSPICIOUS and BENIGN columns are unaffected by the site multiplier.

**Formula:** `effective_cost(decision, gt="THREAT") = base_cost × site_threat_multiplier`

---

## 4. Worked Examples

These examples are hand-verifiable and serve as fixtures for `test_dispatch_rubric.py`.

### Example 1 — armed_response: THREAT at substation

**Inputs:**
- GT: `THREAT`
- site_type: `substation`
- zone_sensitivity: 3

**Decision:** site_type ∈ {substation, solar} → **`armed_response`**

---

### Example 2 — patrol: THREAT at commercial site

**Inputs:**
- GT: `THREAT`
- site_type: `commercial`
- zone_sensitivity: 2

**Decision:** site_type == "commercial" AND sensitivity ≤ 3 → **`patrol`**

---

### Example 3 — patrol: SUSPICIOUS in high-sensitivity zone

**Inputs:**
- GT: `SUSPICIOUS`
- zone_sensitivity: 4

**Decision:** sensitivity ≥ 4 → **`patrol`**

---

### Example 4 — operator_review: SUSPICIOUS in low-sensitivity zone

**Inputs:**
- GT: `SUSPICIOUS`
- zone_sensitivity: 2

**Decision:** sensitivity ≤ 3 → **`operator_review`**

---

### Example 5 — auto_suppress: BENIGN from unreliable device

**Inputs:**
- GT: `BENIGN`
- device.false_positive_rate: 0.85

**Decision:** FPR ≥ 0.70 → **`auto_suppress`**

---

### Example 6 — request_data: BENIGN with unusual event frequency

**Inputs:**
- GT: `BENIGN`
- device.false_positive_rate: 0.40
- len(recent_zone_events_1h): 5

**Decision:** FPR < 0.70 AND recent_zone_events_1h count ≥ 3 → **`request_data`**

---

## 5. Cost Matrix (Provisional Benchmark Assumptions)

> **These values are provisional benchmark assumptions — not sourced from industry data.**
> They are calibrated to reflect relative operational costs in physical security, not
> absolute dollar figures. Override with `--cost-profile <json>` (available in Phase 22).

| Decision | GT = THREAT | GT = SUSPICIOUS | GT = BENIGN |
|----------|------------|-----------------|-------------|
| `armed_response` | 0.0 | 200.0 | 500.0 |
| `patrol` | 0.0 | 20.0 | 50.0 |
| `operator_review` | 50.0 | 0.0 | 10.0 |
| `auto_suppress` | 1000.0 | 20.0 | 0.0 |
| `request_data` | 30.0 | 5.0 | 15.0 |

**Reading the table:**
- Row = model's dispatch decision
- Column = actual ground truth
- Value = cost incurred by that (decision, GT) pair

**Key design choices:**
- `auto_suppress` on a real THREAT costs 1000.0 — missing a true threat is catastrophic
- `armed_response` on a BENIGN costs 500.0 — unnecessary armed responses are expensive and damaging to operator trust
- `operator_review` on a THREAT costs 50.0 — a human review loop delays response but doesn't eliminate it
- Correct decisions (dispatch == optimal_dispatch) cost 0.0 by definition

**THREAT column scaling:** After looking up the base cost, multiply the THREAT column by the
site_threat_multiplier (Section 3) before scoring. Example: `auto_suppress` on a THREAT at
a substation costs `1000.0 × 5.0 = 5000.0`.

---

## 6. Sensitivity Analysis (3 cost-ratio profiles)

Three built-in profiles allow benchmarking across different operational risk tolerances.

| Profile | Description | Adjustment |
|---------|-------------|-----------|
| `low` | Conservative site; lower stakes | All costs × 0.5 |
| `medium` | Default (as above) | No adjustment — use base values |
| `high` | Critical infrastructure; missed threats catastrophic | THREAT column × 2.0 (applied after site multiplier) |

**Usage in scoring:** Pass `--cost-profile low|medium|high` (or a JSON file path for custom
values) to `psai-bench score-dispatch`. The profile affects the cost matrix before any
site_threat_multiplier is applied.

**Example — high profile, auto_suppress on THREAT at substation:**
```
base_cost = 1000.0
× site_multiplier(substation) = 5.0  →  5000.0
× high_profile_threat_factor = 2.0   →  10000.0
```

---

## 7. Relationship to Ground Truth Rubric

Cross-reference: `docs/decision-rubric.md` — the GT assignment rubric.

**Two-step pipeline:**

```
alert + context
      │
      ▼
assign_ground_truth_v2()   ←── docs/decision-rubric.md
      │
      │  gt ∈ {"THREAT", "SUSPICIOUS", "BENIGN"}
      ▼
compute_optimal_dispatch()  ←── this document
      │
      │  optimal_dispatch ∈ DISPATCH_ACTIONS
      ▼
  _meta = {ground_truth: gt, optimal_dispatch: dispatch, ...}
```

GT is computed first (by the weighted signal sum in `decision-rubric.md`), then
`optimal_dispatch` is computed from GT + context (by this document). The two computations
are independent — optimal_dispatch does not feed back into GT.

**Storage:** Both values are written to `_meta` at scenario generation time and remain
fixed for the lifetime of the scenario set. Model outputs are scored against these stored
values at evaluation time.

---

## 8. Reproducibility

To compute `optimal_dispatch` for any scenario by hand:

1. Read `_meta.ground_truth` (or compute it via `docs/decision-rubric.md`)
2. Read `context.site_type`
3. Read `zone.sensitivity`
4. If GT == THREAT: apply Section 2.1 rules top-to-bottom; first match wins
5. If GT == SUSPICIOUS: apply Section 2.2 rule (sensitivity threshold)
6. If GT == BENIGN: read `device.false_positive_rate` and `len(context.recent_zone_events_1h)`; apply Section 2.3 rules top-to-bottom

All constants, thresholds, and table values in this document match the source of truth in
`psai_bench/cost_model.py` at commit-time.
