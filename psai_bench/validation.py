"""Validation and quality control for PSAI-Bench scenarios and submissions.

Catches issues that would embarrass us if a researcher found them:
- Output schema violations
- Missing responses (silent skips)
- Scenario internal consistency
- Difficulty distribution drift
- Confidence value integrity
"""

from collections import Counter
from dataclasses import dataclass, field

from psai_bench.schema import VERDICTS, validate_output


@dataclass
class ValidationReport:
    """Results from validating a submission or scenario set."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: bool = True

    def error(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def warn(self, msg: str):
        self.warnings.append(msg)

    def summary(self) -> str:
        lines = []
        if self.passed:
            lines.append("PASSED" + (f" with {len(self.warnings)} warnings" if self.warnings else ""))
        else:
            lines.append(f"FAILED: {len(self.errors)} errors, {len(self.warnings)} warnings")
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN: {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Submission validation
# ---------------------------------------------------------------------------

def validate_submission(
    scenarios: list[dict],
    outputs: list[dict],
    n_runs_expected: int = 5,
) -> ValidationReport:
    """Validate a system submission against PSAI-Bench requirements.

    Checks:
    1. Every scenario has a response (no silent skips)
    2. Every output conforms to OUTPUT_SCHEMA
    3. Verdicts are valid
    4. Confidence values are in [0, 1]
    5. Reasoning meets minimum length (20 words)
    6. SUSPICIOUS fraction reported
    """
    report = ValidationReport()
    scenario_ids = {s["alert_id"] for s in scenarios}
    output_ids = {o["alert_id"] for o in outputs}

    # Check coverage: every scenario must have a response
    missing = scenario_ids - output_ids
    if missing:
        report.error(
            f"{len(missing)} scenarios have no response. "
            f"Missing IDs (first 10): {sorted(missing)[:10]}. "
            f"Missing responses are scored as incorrect."
        )

    extra = output_ids - scenario_ids
    if extra:
        report.warn(
            f"{len(extra)} outputs reference unknown scenario IDs. "
            f"These will be ignored. First 5: {sorted(extra)[:5]}"
        )

    # Validate each output
    invalid_verdicts = []
    bad_confidence = []
    short_reasoning = []
    schema_errors = []

    for out in outputs:
        aid = out.get("alert_id", "UNKNOWN")

        # Verdict check
        verdict = out.get("verdict")
        if verdict not in VERDICTS:
            invalid_verdicts.append(aid)

        # Confidence range
        conf = out.get("confidence")
        if conf is not None:
            if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                bad_confidence.append(aid)

        # Reasoning length (only checked when reasoning is present and non-empty)
        reasoning = out.get("reasoning")
        if reasoning and len(reasoning.split()) < 20:
            short_reasoning.append(aid)

        # Full schema validation
        try:
            validate_output(out)
        except Exception as e:
            schema_errors.append((aid, str(e)[:100]))

    if invalid_verdicts:
        report.error(
            f"{len(invalid_verdicts)} outputs have invalid verdicts. "
            f"Must be THREAT/SUSPICIOUS/BENIGN. First 5: {invalid_verdicts[:5]}"
        )

    if bad_confidence:
        report.error(
            f"{len(bad_confidence)} outputs have confidence outside [0, 1]. "
            f"First 5: {bad_confidence[:5]}"
        )

    if short_reasoning:
        report.warn(
            f"{len(short_reasoning)} outputs have reasoning under 20 words. "
            f"These receive RQ=0 per Section 5.4."
        )

    if schema_errors:
        report.error(
            f"{len(schema_errors)} outputs fail schema validation. "
            f"First 3: {schema_errors[:3]}"
        )

    # SUSPICIOUS fraction warning
    susp_count = sum(1 for o in outputs if o.get("verdict") == "SUSPICIOUS")
    susp_frac = susp_count / len(outputs) if outputs else 0
    if susp_frac > 0.30:
        report.warn(
            f"SUSPICIOUS fraction is {susp_frac:.1%} (>{30:.0%}). "
            f"High SUSPICIOUS fraction reduces Decisiveness metric."
        )

    return report


# ---------------------------------------------------------------------------
# Scenario quality validation
# ---------------------------------------------------------------------------

# Which description patterns are plausible for which site types.
# A shoplifting description at a solar farm is nonsensical.
_SITE_INCOMPATIBLE_CATEGORIES = {
    "solar": {"Shoplifting", "Robbery"},
    "substation": {"Shoplifting", "Robbery"},
    "campus": set(),  # most things can happen on a campus
    "commercial": set(),  # commercial sites see everything
    "industrial": {"Shoplifting"},
}

# Description fragments that are implausible for certain zone types
_ZONE_DESCRIPTION_CONFLICTS = {
    "perimeter": {"checkout", "merchandise", "store"},
    "restricted": {"customer", "shopping", "checkout"},
    "parking": {"forced entry", "breach secured entrance"},
}

# Per-dataset difficulty targets. Caltech is inherently easier (70% empty triggers)
# so its distribution legitimately skews Easy. The spec targets apply to the
# combined evaluation set, not individual datasets.
DIFFICULTY_TARGETS_DEFAULT = {
    "easy": (0.25, 0.40),    # 30% ± 10%
    "medium": (0.30, 0.55),  # 40% ± 15%
    "hard": (0.10, 0.35),    # 25% ± 15%
}

# Caltech gets wider bounds because its category structure is inherently less ambiguous
DIFFICULTY_TARGETS_CALTECH = {
    "easy": (0.30, 0.65),    # empty triggers dominate → mostly easy
    "medium": (0.15, 0.45),
    "hard": (0.05, 0.25),
}

DIFFICULTY_TARGETS = DIFFICULTY_TARGETS_DEFAULT  # used by default


def validate_scenarios(scenarios: list[dict]) -> ValidationReport:
    """Validate generated scenarios for internal consistency and quality.

    Checks:
    1. Description-site coherence (no shoplifting at solar farms)
    2. Description-zone coherence (no "checkout" at perimeter)
    3. Difficulty distribution matches spec targets
    4. Ground truth label distribution is reasonable
    5. No duplicate alert IDs
    6. All required _meta fields present
    """
    report = ValidationReport()

    if not scenarios:
        report.error("No scenarios to validate.")
        return report

    # Duplicate IDs
    ids = [s["alert_id"] for s in scenarios]
    dupes = [aid for aid, count in Counter(ids).items() if count > 1]
    if dupes:
        report.error(f"{len(dupes)} duplicate alert IDs: {dupes[:5]}")

    # Required meta fields
    required_meta = {"ground_truth", "difficulty", "source_dataset", "source_category"}
    meta_valid = True
    for s in scenarios:
        meta = s.get("_meta", {})
        missing = required_meta - set(meta.keys())
        if missing:
            report.error(f"Scenario {s.get('alert_id', '?')}: missing _meta fields: {missing}")
            meta_valid = False
            break  # one is enough to flag the issue

    if not meta_valid:
        return report  # can't run further checks without _meta

    # Description-site coherence
    site_conflicts = []
    for s in scenarios:
        site = s.get("context", {}).get("site_type", "")
        cat = s.get("_meta", {}).get("source_category", "")
        incompatible = _SITE_INCOMPATIBLE_CATEGORIES.get(site, set())
        if cat in incompatible:
            site_conflicts.append((s["alert_id"], cat, site))

    if site_conflicts:
        report.warn(
            f"{len(site_conflicts)} scenarios have category-site mismatches "
            f"(e.g., {site_conflicts[0][1]} at {site_conflicts[0][2]}). "
            f"These are implausible but not invalid for benchmark purposes. "
            f"Consider filtering or documenting as known limitation."
        )

    # Description-zone coherence
    zone_conflicts = []
    for s in scenarios:
        zone_type = s.get("zone", {}).get("type", "")
        desc = s.get("description", "").lower()
        bad_fragments = _ZONE_DESCRIPTION_CONFLICTS.get(zone_type, set())
        for frag in bad_fragments:
            if frag in desc:
                zone_conflicts.append((s["alert_id"], zone_type, frag))
                break

    if zone_conflicts:
        report.warn(
            f"{len(zone_conflicts)} scenarios have description-zone conflicts "
            f"(e.g., '{zone_conflicts[0][2]}' in {zone_conflicts[0][1]} zone). "
            f"First 5: {[(c[0], c[1], c[2]) for c in zone_conflicts[:5]]}"
        )

    # Difficulty distribution - use dataset-appropriate targets
    n = len(scenarios)
    datasets_in_set = set(s.get("_meta", {}).get("source_dataset", "") for s in scenarios)
    if datasets_in_set == {"caltech_camera_traps"}:
        diff_targets = DIFFICULTY_TARGETS_CALTECH
    else:
        diff_targets = DIFFICULTY_TARGETS_DEFAULT

    diff_counts = Counter(s["_meta"]["difficulty"] for s in scenarios)
    for level, (lo, hi) in diff_targets.items():
        frac = diff_counts.get(level, 0) / n
        if frac < lo or frac > hi:
            report.warn(
                f"Difficulty '{level}' is {frac:.1%} of scenarios "
                f"(target: {lo:.0%}-{hi:.0%}). "
                f"Count: {diff_counts.get(level, 0)}/{n}"
            )

    # Ground truth distribution
    gt_counts = Counter(s["_meta"]["ground_truth"] for s in scenarios)
    total = sum(gt_counts.values())
    for verdict in VERDICTS:
        frac = gt_counts.get(verdict, 0) / total
        if frac < 0.05:
            report.warn(
                f"Ground truth '{verdict}' is only {frac:.1%} of scenarios. "
                f"Low representation may reduce statistical power for this class."
            )

    # Track consistency
    tracks = set(s["track"] for s in scenarios)
    if len(tracks) > 1:
        report.warn(f"Mixed tracks in scenario set: {tracks}. Score separately per track.")

    return report
