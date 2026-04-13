# Ground Truth Decision Rubric — PSAI-Bench v2

This document describes the exact logic used by `assign_ground_truth_v2` (in
`psai_bench/distributions.py`) to assign ground truth labels to benchmark
scenarios. A researcher who reads only this document can reproduce any
scenario's label by hand, given the five context signals.

---

## 1. Overview

In PSAI-Bench v2, ground truth is **not** determined by event category or
severity level alone. Instead, five context signals are each converted to a
numeric score, summed into a `weighted_sum`, and compared against thresholds.

This design means a high severity alert can be labeled BENIGN (if context
strongly exonerates it) and a low severity alert can be labeled THREAT (if
context strongly implicates it). This is intentional — the benchmark tests
whether an AI system can reason about context, not just read severity labels.

The five signals are:

| # | Signal | Source field |
|---|--------|-------------|
| 1 | Zone type & sensitivity | `alert.zone.type`, `alert.zone.sensitivity` |
| 2 | Time of day | `alert.context.time_of_day` |
| 3 | Device false positive rate | `alert.device.false_positive_rate` |
| 4 | Alert severity | `alert.severity` |
| 5 | Badge access recency | `alert.context.recent_badge_access_1h[*].minutes_ago` (or null if array empty) |

---

## 2. Decision Thresholds

```
weighted_sum > +0.30   →  THREAT
weighted_sum < -0.30   →  BENIGN
-0.30 ≤ weighted_sum ≤ +0.30  →  SUSPICIOUS

Additionally:
|weighted_sum| < 0.10  →  flagged "ambiguous by design" (GT remains SUSPICIOUS)
```

Implemented as Python constants:

```python
_GT_THRESHOLD         = 0.30
_AMBIGUITY_THRESHOLD  = 0.10
```

The final `weighted_sum` is rounded to 4 decimal places before comparison.

---

## 3. Signal Definitions and Scores

### 3.1 Zone Type (base score, then multiplied by sensitivity factor)

Base scores:

| Zone type   | Base score |
|-------------|------------|
| `restricted` | +0.40 |
| `utility`    | +0.25 |
| `perimeter`  | +0.10 |
| `interior`   |  0.00 |
| `parking`    | -0.15 |

Sensitivity factor (zone sensitivity is an integer 1–5):

```
sensitivity_factor = 0.6 + (zone_sensitivity - 1) × 0.2
```

| Sensitivity | Factor |
|-------------|--------|
| 1           | 0.60   |
| 2           | 0.80   |
| 3           | 1.00   |
| 4           | 1.20   |
| 5           | 1.40   |

**Final zone score** = base_score × sensitivity_factor

Examples:
- `restricted` zone, sensitivity 5: +0.40 × 1.40 = **+0.560**
- `parking` zone, sensitivity 2: -0.15 × 0.80 = **-0.120**
- `interior` zone, any sensitivity: 0.00 × factor = **0.000**

### 3.2 Time of Day

| Time  | Score |
|-------|-------|
| `night` | +0.35 |
| `dawn`  | +0.15 |
| `dusk`  | +0.10 |
| `day`   | -0.20 |

### 3.3 Alert Severity

| Severity   | Score |
|------------|-------|
| `CRITICAL` | +0.25 |
| `HIGH`     | +0.15 |
| `MEDIUM`   |  0.00 |
| `LOW`      | -0.20 |

**Critical design constraint (SCEN-03):** The maximum severity score (+0.25) is
below the THREAT threshold (+0.30). Severity alone can **never** push
`weighted_sum` past a threshold. At least one other signal must contribute.

### 3.4 Device False Positive Rate (FPR)

Linear formula:

```
fpr_score = 0.15 - (fpr × (0.40 / 0.90))
          = 0.15 - (fpr × 0.4444...)
```

Result is rounded to 3 decimal places before being added to the sum.

Interpretation: a reliable device (low FPR) provides a positive threat signal
because its alerts are credible. An unreliable device (high FPR) provides a
negative signal because its alerts are frequently false.

Reference values:

| FPR  | Score   |
|------|---------|
| 0.05 | +0.128  |
| 0.10 | +0.106  |
| 0.15 | +0.083  |
| 0.20 | +0.061  |
| 0.50 | -0.072  |
| 0.85 | -0.228  |
| 0.90 | -0.250  |
| 0.95 | -0.272  |

### 3.5 Badge Access Recency

| Condition                                       | Score |
|-------------------------------------------------|-------|
| Badge scan < 10 minutes ago                     | -0.45 |
| Badge scan ≥ 10 and ≤ 30 minutes ago            | -0.25 |
| No badge data (`badge_access_minutes_ago = null`) |  0.00 |

Badge provides only benign evidence. Its absence contributes nothing.

---

## 4. Scoring Formula

```
weighted_sum = zone_score + time_score + fpr_score + severity_score + badge_score
weighted_sum = round(weighted_sum, 4)
```

Then:
- `is_ambiguous = (|weighted_sum| < 0.10)`
- If `weighted_sum > 0.30` → GT = `THREAT`
- If `weighted_sum < -0.30` → GT = `BENIGN`
- Otherwise → GT = `SUSPICIOUS`

---

## 5. Quick Reference: All Signal Scores

| Signal | Value | Score |
|--------|-------|-------|
| Zone: restricted | sens=1 | +0.240 |
| Zone: restricted | sens=3 | +0.400 |
| Zone: restricted | sens=5 | +0.560 |
| Zone: utility | sens=3 | +0.250 |
| Zone: perimeter | sens=3 | +0.100 |
| Zone: interior | any | 0.000 |
| Zone: parking | sens=1 | -0.090 |
| Zone: parking | sens=2 | -0.120 |
| Time: night | — | +0.350 |
| Time: dawn | — | +0.150 |
| Time: dusk | — | +0.100 |
| Time: day | — | -0.200 |
| Severity: CRITICAL | — | +0.250 |
| Severity: HIGH | — | +0.150 |
| Severity: MEDIUM | — | 0.000 |
| Severity: LOW | — | -0.200 |
| FPR: 0.10 | — | +0.106 |
| FPR: 0.50 | — | -0.072 |
| FPR: 0.85 | — | -0.228 |
| FPR: 0.90 | — | -0.250 |
| Badge < 10 min | — | -0.450 |
| Badge 10–30 min | — | -0.250 |
| No badge | — | 0.000 |

---

## 6. Worked Examples

These three examples are drawn from the verified test configurations in
`tests/test_decision_rubric.py` (class `TestKnownGTConfigs`).

### Example 1 — THREAT: T1_canonical_threat

**Inputs:**
- Zone: `restricted`, sensitivity = 5
- Time: `night`
- Device FPR: 0.15
- Severity: `HIGH`
- Badge: none

**Calculation:**

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | +0.40 × (0.6 + 4×0.2) = +0.40 × 1.40 | +0.5600 |
| Time | night | +0.3500 |
| FPR | 0.15 − (0.15 × 0.4444) | +0.0830 |
| Severity | HIGH | +0.1500 |
| Badge | no badge data | 0.0000 |
| **Total** | | **+1.1430** |

`1.1430 > 0.30` → **GT = THREAT** (not ambiguous)

**Interpretation:** Restricted zone at highest sensitivity, recorded at night
by a reliable camera, with no exonerating badge scan. Every signal points the
same direction.

---

### Example 2 — SUSPICIOUS (ambiguous): S1_ambiguous_by_design

**Inputs:**
- Zone: `interior`, sensitivity = 3
- Time: `dusk`
- Device FPR: 0.50
- Severity: `MEDIUM`
- Badge: none

**Calculation:**

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | 0.00 × (0.6 + 2×0.2) = 0.00 × 1.00 | 0.0000 |
| Time | dusk | +0.1000 |
| FPR | 0.15 − (0.50 × 0.4444) | -0.0720 |
| Severity | MEDIUM | 0.0000 |
| Badge | no badge data | 0.0000 |
| **Total** | | **+0.0280** |

`-0.30 ≤ 0.028 ≤ +0.30` → **GT = SUSPICIOUS**
`|0.028| < 0.10` → **ambiguity_flag = true**

**Interpretation:** Neutral zone, neutral severity, mediocre camera, just past
day — signals nearly cancel out. This scenario is deliberately placed near the
center of the decision space and marked ambiguous because no reasonable
evaluator should be highly confident in either direction.

---

### Example 3 — BENIGN: B1_canonical_benign

**Inputs:**
- Zone: `parking`, sensitivity = 2
- Time: `day`
- Device FPR: 0.85
- Severity: `LOW`
- Badge: 5 minutes ago

**Calculation:**

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | -0.15 × (0.6 + 1×0.2) = -0.15 × 0.80 | -0.1200 |
| Time | day | -0.2000 |
| FPR | 0.15 − (0.85 × 0.4444) | -0.2280 |
| Severity | LOW | -0.2000 |
| Badge | 5 min ≤ 10 min | -0.4500 |
| **Total** | | **-1.1980** |

`-1.198 < -0.30` → **GT = BENIGN** (not ambiguous)

**Interpretation:** Low-sensitivity parking lot during daytime, triggered by an
unreliable camera, at LOW severity, while a badge scan just confirmed authorized
presence. Every signal points toward benign.

---

## 7. Adversarial Cases — Counterintuitive Labels

These cases illustrate how context can override severity.

### 7.1 Why HIGH (or CRITICAL) Severity Can Yield BENIGN — B2_adversarial_critical

**Inputs:**
- Zone: `parking`, sensitivity = 1
- Time: `day`
- Device FPR: 0.90
- Severity: `CRITICAL`
- Badge: 3 minutes ago

**Calculation:**

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | -0.15 × (0.6 + 0×0.2) = -0.15 × 0.60 | -0.0900 |
| Time | day | -0.2000 |
| FPR | 0.15 − (0.90 × 0.4444) | -0.2500 |
| Severity | CRITICAL | +0.2500 |
| Badge | 3 min ≤ 10 min | -0.4500 |
| **Total** | | **-0.7400** |

`-0.74 < -0.30` → **GT = BENIGN**

**Interpretation:** A known employee badged in 3 minutes ago at a
low-sensitivity parking camera that raises false alarms 90% of the time during
daytime. The CRITICAL severity label from the analytics engine is not credible
— the badge access and unreliable device overwhelm it mathematically.

This is a deliberate adversarial design. An AI evaluator that simply maps
CRITICAL → escalate will fail these cases.

---

### 7.2 Why LOW Severity Can Yield THREAT — T2_adversarial_low_sev

**Inputs:**
- Zone: `restricted`, sensitivity = 5
- Time: `night`
- Device FPR: 0.10
- Severity: `LOW`
- Badge: none

**Calculation:**

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | +0.40 × (0.6 + 4×0.2) = +0.40 × 1.40 | +0.5600 |
| Time | night | +0.3500 |
| FPR | 0.15 − (0.10 × 0.4444) | +0.1060 |
| Severity | LOW | -0.2000 |
| Badge | no badge data | 0.0000 |
| **Total** | | **+0.8160** |

`0.816 > 0.30` → **GT = THREAT**

**Interpretation:** Someone is in a restricted zone at night, captured by a
reliable camera, with no badge scan on record. The LOW severity label from
analytics is not reassuring — zone, time, and device reliability all point
strongly toward threat.

---

## 8. Adversarial Signal Injection (SCEN-04)

Approximately 20% of generated scenarios have one context signal deliberately
flipped by `_inject_adversarial_signals` in `psai_bench/generators.py`. The
flip creates a conflicting evidence scenario by choosing one of three targets:

| Flip target | What changes |
|-------------|-------------|
| 0 — Severity | If in a high-threat context (restricted/utility zone or night), severity is forced to LOW. Otherwise forced to HIGH. |
| 1 — Zone | If the severity is HIGH/CRITICAL, zone is flipped to `parking` (low sensitivity 1–2). Otherwise flipped to `restricted` (high sensitivity 4–5). |
| 2 — Time + FPR | If in a high-threat zone (restricted/utility), time is forced to `day` and FPR to ~0.88. Otherwise time is forced to `night` and FPR to ~0.12. |

The flipped signal is reflected in the final context fields the AI evaluator
sees. The `_meta.ground_truth` label is always computed **after** the flip, so
it reflects the actual combined context, not the pre-flip state.

---

## 9. Description Pools — Text Is Not a GT Input

Scenario descriptions are drawn from shared text pools:

| Pool | Share (approx.) | Content |
|------|-----------------|---------|
| Ambiguous | ~63% | Text that could describe either a normal or suspicious event |
| Unambiguous-threat | ~23% | Text that sounds clearly threatening |
| Unambiguous-benign | ~14% | Text that sounds clearly routine |

**Crucially, the description text is NOT an input to `assign_ground_truth_v2`.**
The same description string (e.g., "Person detected near perimeter") can appear
in scenarios labeled THREAT, SUSPICIOUS, or BENIGN, depending on the five
context signals. An AI evaluator that ignores context and relies solely on
description wording will produce systematically wrong labels.

---

## 10. Reproducibility

To compute the GT label for any scenario by hand:

1. Read `zone.type` and `zone.sensitivity` → compute zone_score
2. Read `context.time_of_day` → look up time_score
3. Read `device.false_positive_rate` → apply FPR formula
4. Read `severity` → look up severity_score
5. Read `context.recent_badge_access_1h` array → if non-empty, use first entry's `minutes_ago`; if empty, treat as null → apply badge rule
6. Sum all five scores, round to 4 decimal places
7. Compare to ±0.30 and ±0.10 thresholds

All constants, formulas, and thresholds in this document match the source of
truth at commit-time values in `psai_bench/distributions.py`.
