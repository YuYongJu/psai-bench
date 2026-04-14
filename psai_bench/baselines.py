"""Baseline systems for PSAI-Bench.

These establish lower bounds that any real system must beat to be considered functional.
Results from these baselines populate Section 7.2 of the specification.
"""

import numpy as np

from psai_bench.schema import VERDICTS

# Default dispatch action for each verdict class (per CONTEXT.md Phase 19 decision).
# Derived from predicted verdict, not ground truth.
VERDICT_TO_DEFAULT_DISPATCH: dict[str, str] = {
    "THREAT":     "armed_response",
    "SUSPICIOUS": "operator_review",
    "BENIGN":     "auto_suppress",
}


def random_baseline(scenarios: list[dict], seed: int = 42) -> list[dict]:
    """Uniform random baseline. Predicts THREAT/SUSPICIOUS/BENIGN with equal probability.

    Expected Safety Score: ~0.50 (TDR ≈ 0.67, FASR ≈ 0.33)
    """
    rng = np.random.RandomState(seed)
    outputs = []
    for s in scenarios:
        verdict = rng.choice(VERDICTS)
        outputs.append({
            "alert_id": s["alert_id"],
            "verdict": verdict,
            "dispatch": VERDICT_TO_DEFAULT_DISPATCH[verdict],
            "confidence": round(float(rng.uniform(0.3, 0.7)), 2),
            "reasoning": f"Random baseline: selected {verdict} uniformly at random.",
            "factors_considered": ["none (random)"],
            "processing_time_ms": 1,
            "model_info": {
                "name": "random_baseline",
                "version": "1.0",
                "provider": "psai-bench",
                "estimated_cost_usd": 0.0,
            },
        })
    return outputs


def majority_class_baseline(scenarios: list[dict]) -> list[dict]:
    """Always predicts the most common ground truth class in the evaluation set.

    This tests whether a system is just learning the class distribution.
    """
    from collections import Counter

    gt_counts = Counter(s["_meta"]["ground_truth"] for s in scenarios)
    majority = gt_counts.most_common(1)[0][0]

    outputs = []
    for s in scenarios:
        outputs.append({
            "alert_id": s["alert_id"],
            "verdict": majority,
            "dispatch": VERDICT_TO_DEFAULT_DISPATCH[majority],
            "confidence": 0.99,
            "reasoning": f"Majority class baseline: always predicts {majority}.",
            "factors_considered": ["class distribution"],
            "processing_time_ms": 1,
            "model_info": {
                "name": "majority_class_baseline",
                "version": "1.0",
                "provider": "psai-bench",
                "estimated_cost_usd": 0.0,
            },
        })
    return outputs


def always_suspicious_baseline(scenarios: list[dict]) -> list[dict]:
    """Always predicts SUSPICIOUS.

    Achieves TDR=1.0 (all threats detected) but FASR=0.0 (no false alarms suppressed).
    Safety Score = 0.75 at 3:1 weighting, but receives SUSPICIOUS cap penalty.
    This baseline demonstrates why the SUSPICIOUS cap exists.
    """
    outputs = []
    for s in scenarios:
        outputs.append({
            "alert_id": s["alert_id"],
            "verdict": "SUSPICIOUS",
            "dispatch": VERDICT_TO_DEFAULT_DISPATCH["SUSPICIOUS"],
            "confidence": 0.50,
            "reasoning": "Always-suspicious baseline: every alert flagged for human review.",
            "factors_considered": ["none (constant prediction)"],
            "processing_time_ms": 1,
            "model_info": {
                "name": "always_suspicious_baseline",
                "version": "1.0",
                "provider": "psai-bench",
                "estimated_cost_usd": 0.0,
            },
        })
    return outputs


def severity_heuristic_baseline(scenarios: list[dict]) -> list[dict]:
    """Simple rule-based baseline using severity and zone sensitivity.

    Rules:
    - CRITICAL severity → THREAT
    - HIGH severity + restricted/utility zone → THREAT
    - HIGH severity + other zone → SUSPICIOUS
    - MEDIUM severity → SUSPICIOUS
    - LOW severity → BENIGN

    This represents the simplest non-random system: a lookup table on two fields.
    Any AI system that can't beat this is not adding value over basic rules.
    """
    outputs = []
    for s in scenarios:
        severity = s["severity"]
        zone_type = s["zone"]["type"]

        if severity == "CRITICAL":
            verdict = "THREAT"
            conf = 0.90
        elif severity == "HIGH" and zone_type in ("restricted", "utility"):
            verdict = "THREAT"
            conf = 0.80
        elif severity == "HIGH":
            verdict = "SUSPICIOUS"
            conf = 0.70
        elif severity == "MEDIUM":
            verdict = "SUSPICIOUS"
            conf = 0.55
        else:
            verdict = "BENIGN"
            conf = 0.85

        outputs.append({
            "alert_id": s["alert_id"],
            "verdict": verdict,
            "dispatch": VERDICT_TO_DEFAULT_DISPATCH[verdict],
            "confidence": conf,
            "reasoning": (
                f"Heuristic: severity={severity}, zone={zone_type}. "
                f"Applied severity-zone lookup table."
            ),
            "factors_considered": ["severity", "zone_type"],
            "processing_time_ms": 1,
            "model_info": {
                "name": "severity_heuristic_baseline",
                "version": "1.0",
                "provider": "psai-bench",
                "estimated_cost_usd": 0.0,
            },
        })
    return outputs
