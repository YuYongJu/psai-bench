"""Statistical significance testing for PSAI-Bench.

Implements the tests required by the specification:
- McNemar's test: Is system A significantly better than system B (or random)?
- Confidence intervals: 95% CIs for all reported metrics
- Multi-run consistency: Are 5 runs consistent (detect high variance)?
"""

import numpy as np
from scipy import stats as scipy_stats


def mcnemar_test(
    gt: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
) -> dict:
    """McNemar's test comparing two systems on the same scenarios.

    Tests whether the disagreements between systems A and B are symmetric.
    If not, one system is significantly better.

    Args:
        gt: Ground truth labels (n,)
        pred_a: System A predictions (n,)
        pred_b: System B predictions (n,)

    Returns:
        Dict with chi2 statistic, p-value, and which system is better.
    """
    correct_a = (pred_a == gt)
    correct_b = (pred_b == gt)

    # McNemar contingency: cases where systems disagree
    # b: A correct, B wrong
    # c: A wrong, B correct
    b = int(np.sum(correct_a & ~correct_b))
    c = int(np.sum(~correct_a & correct_b))

    # Use continuity correction for small samples
    if b + c == 0:
        return {
            "chi2": 0.0,
            "p_value": 1.0,
            "significant": False,
            "better_system": "neither",
            "a_only_correct": b,
            "b_only_correct": c,
        }

    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = float(1 - scipy_stats.chi2.cdf(chi2, df=1))

    better = "A" if b > c else "B" if c > b else "neither"

    return {
        "chi2": float(chi2),
        "p_value": p_value,
        "significant": p_value < 0.01,  # spec requires p < 0.01
        "better_system": better,
        "a_only_correct": b,
        "b_only_correct": c,
    }


def proportion_ci(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Wilson score interval for a proportion.

    More accurate than normal approximation for small samples or extreme proportions.
    Used for confidence intervals on accuracy, TDR, FASR.
    """
    if total == 0:
        return (0.0, 0.0)

    p_hat = successes / total
    z = scipy_stats.norm.ppf(1 - (1 - confidence) / 2)
    z2 = z ** 2

    denominator = 1 + z2 / total
    center = (p_hat + z2 / (2 * total)) / denominator
    spread = z * np.sqrt((p_hat * (1 - p_hat) + z2 / (4 * total)) / total) / denominator

    return (max(0.0, float(center - spread)), min(1.0, float(center + spread)))


def bootstrap_ci(
    values: np.ndarray,
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> tuple[float, float]:
    """Bootstrap confidence interval for any metric.

    Used for metrics that aren't simple proportions (ECE, Brier, Safety Score).
    """
    if len(values) == 0:
        return (0.0, 0.0)

    rng = np.random.RandomState(seed)
    boot_means = np.array([
        np.mean(rng.choice(values, size=len(values), replace=True))
        for _ in range(n_bootstrap)
    ])

    alpha = 1 - confidence
    lo = float(np.percentile(boot_means, 100 * alpha / 2))
    hi = float(np.percentile(boot_means, 100 * (1 - alpha / 2)))
    return (lo, hi)


def compute_all_cis(
    scenarios: list[dict],
    outputs: list[dict],
    confidence: float = 0.95,
) -> dict:
    """Compute confidence intervals for all primary metrics.

    Returns dict mapping metric name to (point_estimate, ci_low, ci_high).
    """
    output_map = {o["alert_id"]: o for o in outputs}

    gt_list = []
    pred_list = []
    conf_list = []
    correct_list = []

    for s in scenarios:
        aid = s["alert_id"]
        if aid not in output_map:
            # Missing responses count as incorrect
            gt_list.append(s["_meta"]["ground_truth"])
            pred_list.append("MISSING")
            conf_list.append(0.0)
            correct_list.append(False)
            continue
        out = output_map[aid]
        gt_list.append(s["_meta"]["ground_truth"])
        pred_list.append(out["verdict"])
        conf_list.append(out["confidence"])
        correct_list.append(s["_meta"]["ground_truth"] == out["verdict"])

    gt = np.array(gt_list)
    pred = np.array(pred_list)
    correct = np.array(correct_list)
    n = len(gt)

    result = {}

    # Accuracy CI (Wilson)
    acc = int(correct.sum())
    ci = proportion_ci(acc, n, confidence)
    result["accuracy"] = (acc / n if n > 0 else 0, ci[0], ci[1])

    # TDR CI
    threat_mask = gt == "THREAT"
    if threat_mask.sum() > 0:
        detected = ((pred[threat_mask] == "THREAT") | (pred[threat_mask] == "SUSPICIOUS"))
        tdr_n = int(detected.sum())
        tdr_total = int(threat_mask.sum())
        ci = proportion_ci(tdr_n, tdr_total, confidence)
        result["tdr"] = (tdr_n / tdr_total, ci[0], ci[1])

    # FASR CI
    benign_mask = gt == "BENIGN"
    if benign_mask.sum() > 0:
        suppressed = (pred[benign_mask] == "BENIGN")
        fasr_n = int(suppressed.sum())
        fasr_total = int(benign_mask.sum())
        ci = proportion_ci(fasr_n, fasr_total, confidence)
        result["fasr"] = (fasr_n / fasr_total, ci[0], ci[1])

    return result


def check_run_consistency(
    reports: list[dict],
    metric: str = "accuracy",
    max_cv: float = 0.05,
) -> dict:
    """Check whether multiple runs are consistent.

    For deterministic systems, all runs should be identical.
    For stochastic systems, coefficient of variation should be < max_cv.
    """
    values = [r.get(metric, 0) for r in reports]
    if not values:
        return {"consistent": False, "reason": "no runs"}

    mean = np.mean(values)
    std = np.std(values)
    cv = std / mean if mean > 0 else 0

    is_deterministic = std == 0
    is_consistent = cv <= max_cv

    return {
        "metric": metric,
        "n_runs": len(values),
        "mean": float(mean),
        "std": float(std),
        "cv": float(cv),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "is_deterministic": is_deterministic,
        "is_consistent": is_consistent,
        "reason": (
            "deterministic (all identical)" if is_deterministic
            else f"CV={cv:.4f} {'<=' if is_consistent else '>'} {max_cv}"
        ),
    }
