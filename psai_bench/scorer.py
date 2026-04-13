"""PSAI-Bench scoring engine.

Implements all metrics defined in Section 4 of the specification:
- Primary: TDR, FASR, ACC, Safety Score
- Calibration: ECE, Brier Score, Overconfidence Rate
- Secondary: SUSPICIOUS fraction, penalty, aggregate score
- Decisiveness: fraction of THREAT|BENIGN predictions (non-SUSPICIOUS)
- Per-difficulty breakdowns
- Cross-dataset generalization gap
- Ambiguous scenario partitioning (excluded from main aggregate)
"""

from __future__ import annotations

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
    suspicious_penalty: float = 0.0   # Zeroed out — kept for backward compat
    calibration_factor: float = 0.0   # Zeroed out — kept for backward compat
    aggregate_score: float = 0.0
    decisiveness: float = 0.0    # Fraction of THREAT|BENIGN predictions (not SUSPICIOUS)

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
    n_ambiguous: int = 0

    # Cost/latency (if reported)
    mean_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    mean_cost_usd: float = 0.0

    # Nested report for ambiguous partition (excluded from main aggregate)
    ambiguous_report: ScoreReport | None = None

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        d = {}
        for k, v in self.__dict__.items():
            if isinstance(v, np.floating):
                d[k] = float(v)
            elif isinstance(v, np.integer):
                d[k] = int(v)
            elif isinstance(v, ScoreReport):
                d[k] = v.to_dict()
            elif v is None:
                d[k] = v
            else:
                d[k] = v
        return d


def format_dashboard(report: ScoreReport, ambiguous_report: ScoreReport | None = None) -> str:
    """Format a ScoreReport as a human-readable metrics dashboard.

    Uses only Python builtins. Output is grep-able by metric name.
    No external dependencies (no tabulate, no rich).
    """
    lines = []
    lines.append("=== PSAI-Bench Metrics Dashboard ===")
    lines.append(f"  TDR (Threat Detection Rate):    {report.tdr:.4f}")
    lines.append(f"  FASR (False Alarm Suppression): {report.fasr:.4f}")
    lines.append(f"  Decisiveness:                   {report.decisiveness:.4f}")
    lines.append(f"  Calibration (ECE):              {report.ece:.4f}  (lower is better)")
    lines.append("")
    lines.append("=== Per-Difficulty Accuracy ===")
    lines.append(f"  Easy:   {report.accuracy_easy:.4f}")
    lines.append(f"  Medium: {report.accuracy_medium:.4f}")
    lines.append(f"  Hard:   {report.accuracy_hard:.4f}")
    lines.append("")
    lines.append("=== Aggregate Score ===")
    lines.append("  Formula: 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)")
    lines.append(f"  Score:   {report.aggregate_score:.4f}")

    # Use ambiguous_report from the report itself if not passed separately
    amb = ambiguous_report or report.ambiguous_report
    if amb is not None and amb.n_scenarios > 0:
        lines.append("")
        lines.append(f"=== Ambiguous Bucket (N={amb.n_scenarios}, excluded from aggregate) ===")
        lines.append(f"  TDR:          {amb.tdr:.4f}")
        lines.append(f"  FASR:         {amb.fasr:.4f}")
        lines.append(f"  Decisiveness: {amb.decisiveness:.4f}")

    lines.append("")
    lines.append(
        f"N={report.n_scenarios} scenarios "
        f"(Threats={report.n_threats}, Benign={report.n_benign}, Ambiguous={report.n_ambiguous})"
    )

    return "\n".join(lines)


@dataclass
class SequenceScoreReport:
    """Scoring report for temporal sequence evaluation."""

    n_sequences: int = 0
    n_threat_sequences: int = 0    # sequences containing at least one THREAT ground truth
    n_benign_sequences: int = 0    # sequences where all GT are BENIGN or SUSPICIOUS
    early_detection_rate: float = 0.0   # threat seqs where model reached THREAT in first 2 alerts
    late_detection_rate: float = 0.0    # threat seqs where model first hit THREAT only at last alert
    missed_sequence_rate: float = 0.0   # threat seqs where model never returned THREAT
    false_escalation_rate: float = 0.0  # benign seqs where model returned THREAT on any alert
    per_sequence_results: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def score_sequences(
    scenarios: list[dict],
    outputs: list[dict],
) -> SequenceScoreReport:
    """Score temporal sequence evaluation.

    Groups alerts by _meta.sequence_id, sorts by _meta.sequence_position,
    evaluates each sequence as a unit.

    Alerts without sequence_id in _meta are silently ignored — mixed files allowed.
    Does NOT call or modify score_run().
    """
    # Build output lookup
    output_map = {o["alert_id"]: o for o in outputs}

    # Group scenarios by sequence_id — skip those without one
    sequences: dict[str, list[dict]] = {}
    for s in scenarios:
        seq_id = s.get("_meta", {}).get("sequence_id")
        if seq_id is None:
            continue
        sequences.setdefault(seq_id, []).append(s)

    if not sequences:
        return SequenceScoreReport()

    n_threat_seqs = 0
    n_benign_seqs = 0
    n_early = 0
    n_late = 0
    n_missed = 0
    n_false_escalation = 0
    per_sequence_results: dict = {}

    for seq_id, alerts in sequences.items():
        # Sort by sequence_position
        sorted_alerts = sorted(alerts, key=lambda s: s["_meta"]["sequence_position"])

        # Classify: threat if any alert has GT == "THREAT"
        is_threat_seq = any(a["_meta"]["ground_truth"] == "THREAT" for a in sorted_alerts)

        # Collect model verdicts in order
        model_verdicts = []
        for a in sorted_alerts:
            out = output_map.get(a["alert_id"])
            verdict = out["verdict"] if out is not None else "MISSING"
            model_verdicts.append(verdict)

        # Get escalation pattern from first alert (all alerts in seq share it)
        pattern = sorted_alerts[0]["_meta"].get("escalation_pattern", "")

        per_sequence_results[seq_id] = {
            "pattern": pattern,
            "is_threat_seq": is_threat_seq,
            "model_verdicts": model_verdicts,
        }

        if is_threat_seq:
            n_threat_seqs += 1
            last_idx = len(model_verdicts) - 1

            threat_indices = [i for i, v in enumerate(model_verdicts) if v == "THREAT"]
            if not threat_indices:
                # Model never returned THREAT — missed
                n_missed += 1
            else:
                first_threat_idx = threat_indices[0]
                if first_threat_idx <= 1:
                    # THREAT appeared at index 0 or 1 (first two alerts) — early
                    n_early += 1
                elif first_threat_idx == last_idx:
                    # First THREAT only at last alert — late
                    n_late += 1
                # Otherwise: detected in the middle — neither early nor late nor missed
        else:
            n_benign_seqs += 1
            if "THREAT" in model_verdicts:
                n_false_escalation += 1

    n_sequences = len(sequences)
    report = SequenceScoreReport(
        n_sequences=n_sequences,
        n_threat_sequences=n_threat_seqs,
        n_benign_sequences=n_benign_seqs,
        early_detection_rate=n_early / n_threat_seqs if n_threat_seqs > 0 else 0.0,
        late_detection_rate=n_late / n_threat_seqs if n_threat_seqs > 0 else 0.0,
        missed_sequence_rate=n_missed / n_threat_seqs if n_threat_seqs > 0 else 0.0,
        false_escalation_rate=n_false_escalation / n_benign_seqs if n_benign_seqs > 0 else 0.0,
        per_sequence_results=per_sequence_results,
    )
    return report


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


def _score_partition(
    scenarios: list[dict],
    outputs: list[dict],
) -> ScoreReport:
    """Score a single partition of scenarios.

    Args:
        scenarios: List of scenario dicts with _meta.ground_truth and _meta.difficulty.
        outputs: List of ALL system output dicts (will be filtered by alert_id).

    Returns:
        ScoreReport with all metrics computed for this partition.
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

    for s in scenarios:
        aid = s["alert_id"]
        if aid not in output_map:
            # Missing responses are scored as incorrect with zero confidence.
            # A system cannot game the benchmark by skipping hard scenarios.
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

    # --- SUSPICIOUS fraction and Decisiveness ---
    report.suspicious_fraction = float((pred == "SUSPICIOUS").mean())

    # Decisiveness: fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS)
    decisive_mask = (pred == "THREAT") | (pred == "BENIGN")
    report.decisiveness = float(decisive_mask.mean()) if n > 0 else 0.0

    # Aggregate: transparent additive formula (backward-compat fields zeroed out)
    report.suspicious_penalty = 0.0
    report.calibration_factor = 0.0
    report.aggregate_score = (
        0.4 * report.tdr
        + 0.3 * report.fasr
        + 0.2 * report.decisiveness
        + 0.1 * (1.0 - report.ece)
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


def score_run(
    scenarios: list[dict],
    outputs: list[dict],
) -> ScoreReport:
    """Score a single evaluation run.

    Partitions scenarios into non-ambiguous (main metrics) and ambiguous (separate bucket).
    Ambiguous scenarios are those where _meta.ambiguity_flag is True. Missing ambiguity_flag
    defaults to False for backward compatibility with v1 scenarios.

    Args:
        scenarios: List of PSAI-Bench alert dicts with _meta.ground_truth and _meta.difficulty.
        outputs: List of system output dicts with verdict, confidence, processing_time_ms.

    Returns:
        ScoreReport with all metrics computed. report.ambiguous_report holds the ambiguous
        partition metrics (None if no ambiguous scenarios exist).
    """
    if not scenarios:
        return ScoreReport()

    # Partition on ambiguity_flag — always use .get() for v1 backward compat
    non_ambiguous = [s for s in scenarios if not s["_meta"].get("ambiguity_flag", False)]
    ambiguous = [s for s in scenarios if s["_meta"].get("ambiguity_flag", False)]

    # Score the non-ambiguous partition (main metrics)
    main_report = _score_partition(non_ambiguous, outputs)
    main_report.n_ambiguous = len(ambiguous)

    # Score ambiguous partition separately if any exist
    if ambiguous:
        amb_report = _score_partition(ambiguous, outputs)
        main_report.ambiguous_report = amb_report

    return main_report


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
        "aggregate_score", "suspicious_fraction", "decisiveness",
    ]

    summary = {"runs": [r.to_dict() for r in reports]}
    for metric in key_metrics:
        values = [getattr(r, metric) for r in reports]
        summary[f"{metric}_mean"] = float(np.mean(values))
        summary[f"{metric}_std"] = float(np.std(values))
        summary[f"{metric}_min"] = float(np.min(values))
        summary[f"{metric}_max"] = float(np.max(values))

    return summary
