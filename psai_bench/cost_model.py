"""PSAI-Bench cost model for dispatch-aware scoring.

Implements the decision table from docs/dispatch-decision-rubric.md.
This module is intentionally isolated from scorer.py — it is imported
by score_dispatch_run() in Phase 19 but has no coupling to existing
scoring logic.

Cost values are provisional benchmark assumptions. See rubric for
override instructions (--cost-profile in Phase 22).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from psai_bench.schema import DISPATCH_ACTIONS


# ---------------------------------------------------------------------------
# Cost tables (provisional benchmark assumptions)
# ---------------------------------------------------------------------------

DISPATCH_COSTS: dict[tuple[str, str], float] = {
    # (dispatch_action, ground_truth) -> base cost in USD
    ("armed_response", "BENIGN"):      500.0,
    ("armed_response", "SUSPICIOUS"):  200.0,
    ("armed_response", "THREAT"):        0.0,
    ("patrol",         "BENIGN"):       50.0,
    ("patrol",         "SUSPICIOUS"):   20.0,
    ("patrol",         "THREAT"):        0.0,
    ("operator_review", "BENIGN"):      10.0,
    ("operator_review", "SUSPICIOUS"):   0.0,
    ("operator_review", "THREAT"):      50.0,
    ("auto_suppress",  "BENIGN"):        0.0,
    ("auto_suppress",  "SUSPICIOUS"):   20.0,
    ("auto_suppress",  "THREAT"):     1000.0,
    ("request_data",   "BENIGN"):       15.0,
    ("request_data",   "SUSPICIOUS"):    5.0,
    ("request_data",   "THREAT"):       30.0,
}

SITE_THREAT_MULTIPLIERS: dict[str, float] = {
    "substation": 5.0,
    "solar":      3.0,
    "industrial": 2.5,
    "campus":     2.0,
    "commercial": 1.5,
}


# ---------------------------------------------------------------------------
# CostModel dataclass
# ---------------------------------------------------------------------------

@dataclass
class CostModel:
    """Configurable cost model for dispatch scoring.

    Costs are indexed by (dispatch_action, ground_truth) tuple.
    Defaults are provisional benchmark assumptions — labeled as such
    in docs/dispatch-decision-rubric.md.
    """

    costs: dict = field(default_factory=lambda: dict(DISPATCH_COSTS))
    site_multipliers: dict = field(default_factory=lambda: dict(SITE_THREAT_MULTIPLIERS))

    def effective_cost(self, action: str, gt: str, site_type: str) -> float:
        """Return cost for (action, gt) scaled by site threat multiplier.

        The THREAT column is multiplied by the site multiplier.
        SUSPICIOUS and BENIGN columns use base costs.
        """
        base = self.costs[(action, gt)]
        if gt == "THREAT":
            return base * self.site_multipliers.get(site_type, 1.0)
        return base


# ---------------------------------------------------------------------------
# CostScoreReport dataclass
# ---------------------------------------------------------------------------

@dataclass
class CostScoreReport:
    """Scoring report for dispatch cost evaluation."""

    n_scenarios: int = 0
    total_cost_usd: float = 0.0
    mean_cost_usd: float = 0.0
    optimal_cost_usd: float = 0.0
    cost_ratio: float = 0.0        # total / optimal (1.0 = optimal)
    per_action_counts: dict = field(default_factory=dict)
    per_site_mean_cost: dict = field(default_factory=dict)
    n_missing_dispatch: int = 0
    sensitivity_profiles: dict = field(default_factory=dict)
    # Structure: {"low": {"total_cost_usd": ..., "cost_ratio": ...}, "medium": {...}, "high": {...}}

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        result: dict = {}
        for k, v in self.__dict__.items():
            if isinstance(v, dict):
                # Recursively ensure keys are strings, values are numeric
                result[k] = v
            elif isinstance(v, (int, float)):
                result[k] = v
            else:
                result[k] = v
        return result


# ---------------------------------------------------------------------------
# compute_optimal_dispatch()
# ---------------------------------------------------------------------------

def compute_optimal_dispatch(gt: str, context: dict) -> str:
    """Compute the benchmark-optimal dispatch action for a scenario.

    Implements the decision table from docs/dispatch-decision-rubric.md exactly.
    Rules are evaluated top-to-bottom within each GT class; first match wins.

    Args:
        gt: Ground truth verdict — one of {"THREAT", "SUSPICIOUS", "BENIGN"}.
        context: Scenario context dict. May be a flat scenario dict (with top-level
                 site_type, zone, device keys) or a nested scenario (with context.site_type).

    Returns:
        One of DISPATCH_ACTIONS.

    Raises:
        ValueError: If gt is not a recognized value.
    """
    # Extract site_type — support both flat and nested scenario shapes
    site_type = (
        context.get("site_type")
        or context.get("context", {}).get("site_type", "commercial")
    ) or "commercial"

    # Extract zone sensitivity
    sensitivity = context.get("zone", {}).get("sensitivity", 3)

    if gt == "THREAT":
        # Rule 1: critical infrastructure sites → armed_response
        if site_type in ("substation", "solar"):
            return "armed_response"
        # Rule 2: high sensitivity zone → armed_response
        if sensitivity >= 4:
            return "armed_response"
        # Rule 3–5: all remaining cases → patrol
        # (industrial/campus/commercial with sensitivity 1-3)
        return "patrol"

    elif gt == "SUSPICIOUS":
        # Rule 1: high sensitivity → patrol
        if sensitivity >= 4:
            return "patrol"
        # Rule 2: low/medium sensitivity → operator_review
        return "operator_review"

    elif gt == "BENIGN":
        # Extract BENIGN-specific signals
        fpr = context.get("device", {}).get("false_positive_rate", 0.5)
        recent_events = context.get("context", {}).get("recent_zone_events_1h", [])

        # Rule 1: unreliable device → auto_suppress
        if fpr >= 0.70:
            return "auto_suppress"
        # Rule 2: reliable device with unusual frequency → request_data
        if len(recent_events) >= 3:
            return "request_data"
        # Rule 3: otherwise → auto_suppress
        return "auto_suppress"

    else:
        raise ValueError(
            f"Unrecognized ground truth value: {gt!r}. "
            f"Expected one of {{'THREAT', 'SUSPICIOUS', 'BENIGN'}}."
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _aggregate_costs(
    pairs: list[tuple[str, str, str, str]],
    model: CostModel,
) -> tuple[float, float]:
    """Sum submitted and optimal costs for matched pairs.

    Args:
        pairs: List of (submitted_dispatch, optimal_action, gt, site_type) tuples.
        model: CostModel to use for cost lookups.

    Returns:
        (total_submitted_cost, total_optimal_cost) tuple.
    """
    total_submitted = 0.0
    total_optimal = 0.0
    for submitted_dispatch, optimal_action, gt, site_type in pairs:
        total_submitted += model.effective_cost(submitted_dispatch, gt, site_type)
        total_optimal += model.effective_cost(optimal_action, gt, site_type)
    return total_submitted, total_optimal


# ---------------------------------------------------------------------------
# score_dispatch()
# ---------------------------------------------------------------------------

def score_dispatch(
    scenarios: list[dict],
    outputs: list[dict],
    model: CostModel | None = None,
) -> CostScoreReport:
    """Score dispatch decisions against optimal benchmark actions.

    Computes expected operational cost comparing submitted dispatch decisions
    to the benchmark's compute_optimal_dispatch() reference. Reports at 3
    cost-ratio assumptions per docs/dispatch-decision-rubric.md Section 6.

    Args:
        scenarios: List of scenario dicts from generate (each has _meta.ground_truth
                   and context.site_type, zone.sensitivity, device.false_positive_rate).
        outputs: List of output dicts (each may have 'dispatch' field).
        model: Optional CostModel to override defaults.

    Returns:
        CostScoreReport with expected cost, optimal cost, cost ratio,
        and per_action breakdown.
    """
    if model is None:
        model = CostModel()

    # Build output lookup by alert_id
    output_map = {o["alert_id"]: o for o in outputs}

    # Initialize report accumulators
    report = CostScoreReport()
    report.per_action_counts = {action: 0 for action in DISPATCH_ACTIONS}

    # Accumulate costs and stats
    # pairs for sensitivity analysis: (submitted, optimal, gt, site_type)
    cost_pairs: list[tuple[str, str, str, str]] = []

    # Per-site cost tracking: site_type -> [costs]
    site_costs: dict[str, list[float]] = {}

    for scenario in scenarios:
        alert_id = scenario.get("alert_id", "")

        # T-18-04: access _meta.ground_truth defensively
        meta = scenario.get("_meta", {})
        gt = meta.get("ground_truth")
        if not gt or gt not in ("THREAT", "SUSPICIOUS", "BENIGN"):
            report.n_missing_dispatch += 1
            continue

        # Extract site_type from scenario (uses nested context.site_type)
        site_type = (
            scenario.get("site_type")
            or scenario.get("context", {}).get("site_type", "commercial")
        ) or "commercial"

        # Get submitted output
        out = output_map.get(alert_id)
        if out is None:
            report.n_missing_dispatch += 1
            continue

        submitted_dispatch = out.get("dispatch")
        if submitted_dispatch is None:
            report.n_missing_dispatch += 1
            continue

        # Compute optimal action for this scenario
        try:
            optimal_action = compute_optimal_dispatch(gt, scenario)
        except ValueError:
            report.n_missing_dispatch += 1
            continue

        # Track submitted action count
        if submitted_dispatch in report.per_action_counts:
            report.per_action_counts[submitted_dispatch] += 1

        # Compute costs
        submitted_cost = model.effective_cost(submitted_dispatch, gt, site_type)
        optimal_cost = model.effective_cost(optimal_action, gt, site_type)

        report.total_cost_usd += submitted_cost
        report.optimal_cost_usd += optimal_cost
        report.n_scenarios += 1

        # Track pair for sensitivity analysis
        cost_pairs.append((submitted_dispatch, optimal_action, gt, site_type))

        # Track per-site costs
        site_costs.setdefault(site_type, []).append(submitted_cost)

    # Compute derived metrics
    if report.n_scenarios > 0:
        report.mean_cost_usd = report.total_cost_usd / report.n_scenarios
        # T-18-05: guard against zero denominator
        report.cost_ratio = report.total_cost_usd / max(report.optimal_cost_usd, 1e-9)

    # Per-site mean cost
    for site, costs_list in site_costs.items():
        report.per_site_mean_cost[site] = sum(costs_list) / len(costs_list)

    # ---------------------------------------------------------------------------
    # Sensitivity profiles (Section 6 of rubric)
    # ---------------------------------------------------------------------------

    # "medium" — default model (already computed)
    med_submitted, med_optimal = _aggregate_costs(cost_pairs, model)
    report.sensitivity_profiles["medium"] = {
        "total_cost_usd": med_submitted,
        "cost_ratio": med_submitted / max(med_optimal, 1e-9),
    }

    # "low" — all costs × 0.5
    low_model = CostModel(
        costs={k: v * 0.5 for k, v in model.costs.items()},
        site_multipliers=dict(model.site_multipliers),
    )
    low_submitted, low_optimal = _aggregate_costs(cost_pairs, low_model)
    report.sensitivity_profiles["low"] = {
        "total_cost_usd": low_submitted,
        "cost_ratio": low_submitted / max(low_optimal, 1e-9),
    }

    # "high" — THREAT column × 2.0 (non-THREAT columns unchanged)
    high_costs = {}
    for (action, gt_key), v in model.costs.items():
        if gt_key == "THREAT":
            high_costs[(action, gt_key)] = v * 2.0
        else:
            high_costs[(action, gt_key)] = v
    high_model = CostModel(
        costs=high_costs,
        site_multipliers=dict(model.site_multipliers),
    )
    high_submitted, high_optimal = _aggregate_costs(cost_pairs, high_model)
    report.sensitivity_profiles["high"] = {
        "total_cost_usd": high_submitted,
        "cost_ratio": high_submitted / max(high_optimal, 1e-9),
    }

    return report
