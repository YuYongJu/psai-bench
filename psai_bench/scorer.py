"""PSAI-Bench scoring engine.

Implements all metrics defined in Section 4 of the specification:
- Primary: TDR, FASR, ACC, Safety Score
- Calibration: ECE, Brier Score, Overconfidence Rate
- Secondary: SUSPICIOUS fraction, penalty, aggregate score
- Per-difficulty breakdowns
- Cross-dataset generalization gap
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ScoreReport:
    """Complete scoring report for a single evaluation run."""

    # Primary metrics
    tdr: float = 0.0            # Threat Detection Rate
    fasr: float = 0.0           # False Alarm Suppression Rate
    accuracy: float = 0.0       # 3-class accuracy
    safety_score_1_1: float = 0.0   # Safety Score at 1:1 weight
    safety_score_3_1: float = 0.0   # Safety Score at 3:1 weight (default)
    safety_score_10_1: float = 0.0  # Safety Score at 10:1 weight

    # Calibration
    ece: float = 0.0            # Expected Calibration Error
    brier_score: float = 0.0    # Brier Score
    overconfidence_rate: float = 0.0  # Fraction of wrong predictions with confidence > 0.8

    # Secondary
    suspicious_fraction: float = 0.0
    suspicious_penalty: float = 0.0
    calibration_factor: float = 0.0
    aggregate_score: float = 0.0

    # Per-difficulty breakdown
    accuracy_easy: float = 0.0
    accuracy_medium: float = 0.0
    accuracy_hard: float = 0.0
    safety_score_easy: float = 0.0
    safety_score_medium: float = 0.0
    safety_score_hard: float = 0.0

    # Per-dataset scores (for generalization gap)
    per_dataset_accuracy: dict = field(default_factory=dict)
    generalization_gap: float = 0.0

    # Confusion matrix
    confusion_matrix: dict = field(default_factory=dict)

    # Metadata
    n_scenarios: int = 0
    n_threats: int = 0
    n_benign: int = 0
    n_suspicious_gt: int = 0

    # Cost/latency (if reported)
    mean_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    mean_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, np.floating):
                d[k] = float(v)
            elif isinstance(v, np.integer):
                d[k] = int(v)
            else:
                d[k] = v
        return d


def _safety_score(tdr: float, fasr: float, w_threat: float, w_false: float) -> float:
    """Compute Safety Score = (w_threat * TDR + w_false * FASR) / (w_threat + w_false)."""
    if w_threat + w_false == 0:
        return 0.0
    return (w_threat * tdr + w_false * fasr) / (w_threat + w_false)


def _ece(confidences: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error with equal-width bins."""
    if len(confidences) == 0:
        return 0.0
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = correct[mask].mean()
        bin_conf = confidences[mask].mean()
        ece += mask.sum() / len(confidences) * abs(bin_acc - bin_conf)
    return float(ece)


def _brier_score(confidences: np.ndarray, correct: np.ndarray) -> float:
    """Mean squared error between confidence and correctness."""
    if len(confidences) == 0:
        return 0.0
    return float(np.mean((confidences - correct.astype(float)) ** 2))


def score_run(
    scenarios: list[dict],
    outputs: list[dict],
) -> ScoreReport:
    """Score a single evaluation run.

    Args:
        scenarios: List of PSAI-Bench alert dicts with _meta.ground_truth and _meta.difficulty.
        outputs: List of system output dicts with verdict, confidence, processing_time_ms.

    Returns:
        ScoreReport with all metrics computed.
    """
    # Build lookup from alert_id to output
    output_map = {o["alert_id"]: o for o in outputs}

    # Parallel arrays for vectorized computation
    gt_verdicts = []
    pred_verdicts = []
    confidences = []
    difficulties = []
    datasets = []
    latencies = []
    costs = []

    n_missing = 0
    for s in scenarios:
        aid = s["alert_id"]
        if aid not in output_map:
            # Missing responses are scored as incorrect with zero confidence.
            # A system cannot game the benchmark by skipping hard scenarios.
            n_missing += 1
            gt_verdicts.append(s["_meta"]["ground_truth"])
            pred_verdicts.append("MISSING")  # guaranteed wrong for any ground truth
            confidences.append(0.0)
            difficulties.append(s["_meta"]["difficulty"])
            datasets.append(s["_meta"]["source_dataset"])
            continue
        out = output_map[aid]
        gt_verdicts.append(s["_meta"]["ground_truth"])
        pred_verdicts.append(out["verdict"])
        confidences.append(out["confidence"])
        difficulties.append(s["_meta"]["difficulty"])
        datasets.append(s["_meta"]["source_dataset"])
        latencies.append(out.get("processing_time_ms", 0))
        if out.get("model_info", {}).get("estimated_cost_usd"):
            costs.append(out["model_info"]["estimated_cost_usd"])

    n = len(gt_verdicts)
    if n == 0:
        return ScoreReport()

    gt = np.array(gt_verdicts)
    pred = np.array(pred_verdicts)
    conf = np.array(confidences, dtype=float)
    diff = np.array(difficulties)
    ds = np.array(datasets)
    correct = (gt == pred)

    report = ScoreReport(n_scenarios=n)

    # --- Primary metrics ---

    # Threat Detection Rate: threats caught as THREAT or SUSPICIOUS
    threat_mask = gt == "THREAT"
    report.n_threats = int(threat_mask.sum())
    if report.n_threats > 0:
        detected = (pred[threat_mask] == "THREAT") | (pred[threat_mask] == "SUSPICIOUS")
        report.tdr = float(detected.mean())

    # False Alarm Suppression Rate: benign events correctly classified as BENIGN
    benign_mask = gt == "BENIGN"
    report.n_benign = int(benign_mask.sum())
    if report.n_benign > 0:
        suppressed = pred[benign_mask] == "BENIGN"
        report.fasr = float(suppressed.mean())

    # Suspicious ground truth count
    report.n_suspicious_gt = int((gt == "SUSPICIOUS").sum())

    # 3-class accuracy
    report.accuracy = float(correct.mean())

    # Safety scores at three weight ratios
    report.safety_score_1_1 = _safety_score(report.tdr, report.fasr, 1, 1)
    report.safety_score_3_1 = _safety_score(report.tdr, report.fasr, 3, 1)
    report.safety_score_10_1 = _safety_score(report.tdr, report.fasr, 10, 1)

    # --- Calibration ---
    report.ece = _ece(conf, correct.astype(float))
    report.brier_score = _brier_score(conf, correct.astype(float))

    wrong_mask = ~correct
    if wrong_mask.sum() > 0:
        overconf = (conf[wrong_mask] > 0.8).mean()
        report.overconfidence_rate = float(overconf)

    # --- SUSPICIOUS fraction and penalty ---
    report.suspicious_fraction = float((pred == "SUSPICIOUS").mean())
    report.suspicious_penalty = max(0.0, (report.suspicious_fraction - 0.30) * 2)
    report.calibration_factor = max(0.5, 1.0 - report.ece)
    report.aggregate_score = (
        report.safety_score_3_1
        * (1 - report.suspicious_penalty)
        * report.calibration_factor
    )

    # --- Per-difficulty breakdown ---
    for d in ["easy", "medium", "hard"]:
        mask = diff == d
        if mask.sum() == 0:
            continue
        acc = float(correct[mask].mean())
        setattr(report, f"accuracy_{d}", acc)

        # Per-difficulty safety score
        d_threat = (gt[mask] == "THREAT")
        d_benign = (gt[mask] == "BENIGN")
        d_tdr = float(
            ((pred[mask][d_threat] == "THREAT") | (pred[mask][d_threat] == "SUSPICIOUS")).mean()
        ) if d_threat.sum() > 0 else 0.0
        d_fasr = float(
            (pred[mask][d_benign] == "BENIGN").mean()
        ) if d_benign.sum() > 0 else 0.0
        setattr(report, f"safety_score_{d}", _safety_score(d_tdr, d_fasr, 3, 1))

    # --- Per-dataset generalization ---
    unique_datasets = np.unique(ds)
    for d in unique_datasets:
        mask = ds == d
        report.per_dataset_accuracy[d] = float(correct[mask].mean())

    if len(report.per_dataset_accuracy) > 1:
        accs = list(report.per_dataset_accuracy.values())
        report.generalization_gap = max(accs) - min(accs)

    # --- Confusion matrix ---
    labels = ["THREAT", "SUSPICIOUS", "BENIGN"]
    cm = {}
    for true_label in labels:
        cm[true_label] = {}
        for pred_label in labels:
            cm[true_label][pred_label] = int(
                ((gt == true_label) & (pred == pred_label)).sum()
            )
    report.confusion_matrix = cm

    # --- Latency/cost ---
    if latencies:
        lat = np.array(latencies, dtype=float)
        report.mean_latency_ms = float(lat.mean())
        report.p95_latency_ms = float(np.percentile(lat, 95))
    if costs:
        report.mean_cost_usd = float(np.mean(costs))

    return report


def score_multiple_runs(
    scenarios: list[dict],
    all_outputs: list[list[dict]],
) -> dict:
    """Score multiple runs and compute aggregate statistics.

    MLPerf requires 5 runs with mean, std, min, max reported.

    Returns:
        Dict with per-run reports, mean, std, min, max for key metrics.
    """
    reports = [score_run(scenarios, outputs) for outputs in all_outputs]

    key_metrics = [
        "accuracy", "tdr", "fasr", "safety_score_3_1", "ece",
        "aggregate_score", "suspicious_fraction",
    ]

    summary = {"runs": [r.to_dict() for r in reports]}
    for metric in key_metrics:
        values = [getattr(r, metric) for r in reports]
        summary[f"{metric}_mean"] = float(np.mean(values))
        summary[f"{metric}_std"] = float(np.std(values))
        summary[f"{metric}_min"] = float(np.min(values))
        summary[f"{metric}_max"] = float(np.max(values))

    return summary
