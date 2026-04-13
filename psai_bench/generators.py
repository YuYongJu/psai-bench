"""Scenario generators for each PSAI-Bench evaluation track.

Each generator converts raw dataset annotations into standardized PSAI-Bench
alerts. The generation is fully deterministic given a seed, ensuring reproducibility.

Usage:
    from psai_bench.generators import MetadataGenerator, VisualGenerator
    gen = MetadataGenerator(seed=42)
    scenarios = gen.generate_ucf_crime(n=3000)
"""

from datetime import datetime, timedelta, timezone

import numpy as np

from psai_bench.distributions import (
    ACCESS_EVENTS,
    CALTECH_CATEGORY_MAP,
    EXPECTED_ACTIVITIES,
    TOD_OPTIONS,
    TOD_WEIGHTS_BENIGN,
    TOD_WEIGHTS_THREAT,
    UCF_CATEGORY_MAP,
    sample_device,
    sample_site_type,
    sample_weather,
    sample_zone,
)

# Difficulty assignment thresholds.
# Easy: unambiguous ground truth, high-severity or clearly benign.
# Medium: moderate ambiguity, could require context to decide.
# Hard: conflicting signals, edge cases, adversarial-adjacent.
DIFFICULTY_RULES = {
    # UCF categories by inherent ambiguity
    "easy_categories": {"Arson", "Explosion", "Shooting", "Normal"},
    "hard_categories": {"Arrest", "RoadAccidents", "Shoplifting"},
    # Everything else is medium by default, modulated by context signals
}

# Caltech-specific difficulty: empty triggers and common animals are easy to dismiss,
# but vehicles/people at remote sites are harder.
CALTECH_DIFFICULTY_RULES = {
    "easy_categories": {"empty", "animal_small"},
    "hard_categories": {"vehicle", "person"},
    # animal_large is medium (could be mistaken for a person at distance)
}

# Categories that are implausible at certain site types.
# If a combo is drawn, resample the site type instead of generating nonsense.
SITE_CATEGORY_BLOCKLIST = {
    "solar": {"Shoplifting", "Robbery", "Arrest", "RoadAccidents"},
    "substation": {"Shoplifting", "Robbery", "Arrest"},
    "industrial": {"Shoplifting", "RoadAccidents"},
    "commercial": {"RoadAccidents"},
    "campus": {"RoadAccidents"},
}


def _assign_difficulty(
    category: str,
    zone_sensitivity: int,
    time_of_day: str,
    device_fpr: float,
    rng: np.random.RandomState,
    dataset: str = "ucf_crime",
) -> str:
    """Assign difficulty based on category + contextual ambiguity signals.

    Difficulty is not random. It's determined by how many conflicting signals
    exist in the scenario. A burglary at night in a restricted zone is easier
    to classify than a burglary during business hours in a parking lot.
    """
    # Pick the right difficulty rules for the dataset
    rules = CALTECH_DIFFICULTY_RULES if dataset == "caltech" else DIFFICULTY_RULES

    if category in rules.get("easy_categories", set()):
        base = "easy"
    elif category in rules.get("hard_categories", set()):
        base = "hard"
    else:
        base = "medium"

    benign_cats = {"Normal", "empty", "animal_small", "animal_large"}

    # Contextual modifiers that increase ambiguity
    ambiguity_score = 0

    # Low sensitivity zone + threat/suspicious = harder
    if zone_sensitivity <= 2 and category not in benign_cats:
        ambiguity_score += 1

    # Daytime threats are harder (more expected activity to confuse with)
    if time_of_day == "day" and category not in benign_cats:
        ambiguity_score += 1

    # High-FPR device makes all verdicts less certain
    if device_fpr > 0.80:
        ambiguity_score += 1

    # Night + benign = harder (why is something triggering at night?)
    if time_of_day == "night" and category in benign_cats and category != "Normal":
        ambiguity_score += 1

    # High-sensitivity zone + benign = harder (alert from a sensitive zone feels urgent)
    if zone_sensitivity >= 4 and category in benign_cats:
        ambiguity_score += 1

    # Promote difficulty based on ambiguity
    if base == "easy" and ambiguity_score >= 2:
        return "medium"
    if base == "easy" and ambiguity_score == 1 and rng.random() < 0.3:
        return "medium"
    if base == "medium" and ambiguity_score >= 2:
        return "hard"
    if base == "medium" and ambiguity_score == 0:
        if rng.random() < 0.3:
            return "easy"

    return base


def _generate_timestamp(
    time_of_day: str, rng: np.random.RandomState
) -> str:
    """Generate a plausible ISO-8601 timestamp for the given time of day."""
    base_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    day_offset = int(rng.randint(0, 365))
    hour_ranges = {"day": (8, 17), "night": (22, 5), "dawn": (5, 7), "dusk": (18, 21)}
    lo, hi = hour_ranges[time_of_day]
    if lo > hi:  # night wraps around midnight
        hour = int(rng.choice(list(range(lo, 24)) + list(range(0, hi + 1))))
    else:
        hour = int(rng.randint(lo, hi + 1))
    minute = int(rng.randint(0, 60))
    second = int(rng.randint(0, 60))
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)
    return ts.isoformat()


def _generate_recent_events(
    zone_type: str, time_of_day: str, rng: np.random.RandomState
) -> list[dict]:
    """Generate plausible recent zone events for context."""
    count = max(0, int(rng.poisson(2)))
    events = []
    for _ in range(count):
        minutes_ago = int(rng.randint(1, 60))
        events.append({
            "minutes_ago": minutes_ago,
            "type": rng.choice(["motion", "analytics_alert", "door_event", "environmental"]),
            "resolved": bool(rng.choice([True, False], p=[0.7, 0.3])),
        })
    return events


def _inject_adversarial_signals(
    base_severity: str,
    zone_type: str,
    zone_sensitivity: int,
    time_of_day: str,
    device_fpr: float,
    rng: np.random.RandomState,
) -> tuple[str, str, int, str, float]:
    """Override one context signal to create a conflicting scenario (SCEN-04)."""
    flip_choice = rng.randint(0, 3)

    if flip_choice == 0:
        if zone_type in ("restricted", "utility") or time_of_day == "night":
            new_severity = "LOW"
        else:
            new_severity = "HIGH"
        return new_severity, zone_type, zone_sensitivity, time_of_day, device_fpr
    elif flip_choice == 1:
        if base_severity in ("HIGH", "CRITICAL"):
            new_zone = "parking"
            new_sens = rng.randint(1, 3)
        else:
            new_zone = "restricted"
            new_sens = min(rng.randint(4, 6), 5)
        return base_severity, new_zone, new_sens, time_of_day, device_fpr
    else:
        if zone_type in ("restricted", "utility"):
            new_time = "day"
            new_fpr = float(np.clip(rng.normal(0.88, 0.05), 0.70, 0.99))
        else:
            new_time = "night"
            new_fpr = float(np.clip(rng.normal(0.12, 0.05), 0.01, 0.30))
        return base_severity, zone_type, zone_sensitivity, new_time, new_fpr


def _sample_valid_site(category: str, rng: np.random.RandomState) -> str:
    """Sample a site type that isn't blocked for the given category."""
    site_type = sample_site_type(rng)
    for _ in range(10):
        blocked = SITE_CATEGORY_BLOCKLIST.get(site_type, set())
        if category not in blocked:
            return site_type
        site_type = sample_site_type(rng)
    # Fallback: pick deterministically from valid sites
    from psai_bench.distributions import SITE_TYPES
    valid = [s for s in SITE_TYPES if category not in SITE_CATEGORY_BLOCKLIST.get(s, set())]
    return rng.choice(valid) if valid else site_type


class MetadataGenerator:
    """Generate Metadata Track scenarios from UCF Crime and Caltech Camera Traps annotations."""

    def __init__(self, seed: int = 42, version: str = "v1"):
        self.rng = np.random.RandomState(seed)
        self.seed = seed
        self.version = version

    def generate_ucf_crime(self, n: int = 3000) -> list[dict]:
        """Generate n metadata-only scenarios derived from UCF Crime categories.

        The UCF Crime dataset has 13 anomaly categories + Normal. We sample
        categories proportionally to the test set distribution, then generate
        full alert metadata for each.
        """
        if self.version == "v2":
            return self.generate_ucf_crime_v2(n)
        categories = list(UCF_CATEGORY_MAP.keys())
        # Weight Normal higher to match real-world class imbalance (most alerts are benign)
        weights = [1.0] * (len(categories) - 1) + [4.0]
        weights = np.array(weights) / sum(weights)

        scenarios = []
        for i in range(n):
            cat = self.rng.choice(categories, p=weights)
            mapping = UCF_CATEGORY_MAP[cat]

            gt = mapping["ground_truth"]
            tod_weights = TOD_WEIGHTS_THREAT if gt == "THREAT" else TOD_WEIGHTS_BENIGN
            time_of_day = self.rng.choice(TOD_OPTIONS, p=tod_weights)

            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)

            # Sample site type, rejecting implausible category-site combos
            site_type = _sample_valid_site(cat, self.rng)

            severity = self.rng.choice(mapping["severity_range"])
            description = self.rng.choice(mapping["description_templates"])

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day, device["false_positive_rate"],
                self.rng, dataset="ucf_crime",
            )

            alert = {
                "alert_id": f"ucf-meta-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "metadata",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": [],
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                # PSAI-Bench metadata (not sent to evaluated systems)
                "_meta": {
                    "ground_truth": gt,
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": i,
                },
            }
            scenarios.append(alert)

        return scenarios

    def generate_ucf_crime_v2(self, n: int = 3000) -> list[dict]:
        """Generate n v2 scenarios with context-dependent GT and shared description pool."""
        from psai_bench.distributions import (
            DESCRIPTION_POOL_AMBIGUOUS,
            DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN,
            DESCRIPTION_POOL_UNAMBIGUOUS_THREAT,
            assign_ground_truth_v2,
        )

        categories = list(UCF_CATEGORY_MAP.keys())
        weights = [1.0] * (len(categories) - 1) + [4.0]
        weights = np.array(weights) / sum(weights)

        adversarial_flags = self.rng.random(n) < 0.20

        scenarios = []
        for i in range(n):
            cat = self.rng.choice(categories, p=weights)

            desc_type_roll = self.rng.random()
            if desc_type_roll < 0.70:
                description = self.rng.choice(DESCRIPTION_POOL_AMBIGUOUS)
                desc_category = "ambiguous"
            elif desc_type_roll < 0.85:
                description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_THREAT)
                desc_category = "unambiguous_threat"
            else:
                description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN)
                desc_category = "unambiguous_benign"

            severity_range = UCF_CATEGORY_MAP[cat]["severity_range"]
            severity = self.rng.choice(severity_range)

            time_of_day = self.rng.choice(TOD_OPTIONS, p=[0.25, 0.35, 0.20, 0.20])
            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)

            site_type = _sample_valid_site(cat, self.rng)

            badge_roll = self.rng.random()
            if badge_roll < 0.20:
                badge_minutes_ago = int(self.rng.randint(1, 10))
            elif badge_roll < 0.40:
                badge_minutes_ago = int(self.rng.randint(10, 30))
            else:
                badge_minutes_ago = None

            is_adversarial = bool(adversarial_flags[i])
            if is_adversarial:
                severity, adj_zone_type, adj_sensitivity, time_of_day, adj_fpr = (
                    _inject_adversarial_signals(
                        severity, zone["type"], zone["sensitivity"],
                        time_of_day, device["false_positive_rate"], self.rng,
                    )
                )
                zone["type"] = adj_zone_type
                zone["sensitivity"] = adj_sensitivity
                device["false_positive_rate"] = round(adj_fpr, 3)

            gt, weighted_sum, is_ambiguous = assign_ground_truth_v2(
                zone_type=zone["type"],
                zone_sensitivity=zone["sensitivity"],
                time_of_day=time_of_day,
                device_fpr=device["false_positive_rate"],
                severity=severity,
                badge_access_minutes_ago=badge_minutes_ago,
                rng=self.rng,
            )

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day,
                device["false_positive_rate"], self.rng, dataset="ucf_crime",
            )
            if is_adversarial and difficulty == "easy":
                difficulty = "medium"

            badge_access_events = []
            if badge_minutes_ago is not None:
                badge_access_events = [{
                    "minutes_ago": badge_minutes_ago,
                    "event_type": "badge_granted",
                    "resolved": True,
                }]

            alert = {
                "alert_id": f"ucf-meta-v2-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "metadata",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": badge_access_events,
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "weighted_sum": weighted_sum,
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": i,
                    "adversarial": is_adversarial,
                    "ambiguity_flag": is_ambiguous,
                    "description_category": desc_category,
                    "generation_version": "v2",
                },
            }
            scenarios.append(alert)

        return scenarios

    def generate_caltech(self, n: int = 5000) -> list[dict]:
        """Generate n metadata-only scenarios from Caltech Camera Traps categories."""
        if self.version == "v2":
            return self.generate_caltech_v2(n)
        categories = list(CALTECH_CATEGORY_MAP.keys())
        weights = [CALTECH_CATEGORY_MAP[c]["weight"] for c in categories]
        weights = np.array(weights) / sum(weights)

        scenarios = []
        for i in range(n):
            cat = self.rng.choice(categories, p=weights)
            mapping = CALTECH_CATEGORY_MAP[cat]

            gt = mapping["ground_truth"]
            tod_weights = TOD_WEIGHTS_THREAT if gt == "THREAT" else TOD_WEIGHTS_BENIGN
            time_of_day = self.rng.choice(TOD_OPTIONS, p=tod_weights)

            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)
            site_type = sample_site_type(self.rng)
            severity = self.rng.choice(mapping["severity_range"])
            description = self.rng.choice(mapping["description_templates"])

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day, device["false_positive_rate"],
                self.rng, dataset="caltech",
            )

            alert = {
                "alert_id": f"caltech-meta-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "metadata",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": [],
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "difficulty": difficulty,
                    "source_dataset": "caltech_camera_traps",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": i,
                },
            }
            scenarios.append(alert)

        return scenarios

    def generate_caltech_v2(self, n: int = 5000) -> list[dict]:
        """Generate n v2 Caltech scenarios with context-dependent GT."""
        from psai_bench.distributions import (
            DESCRIPTION_POOL_AMBIGUOUS,
            DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN,
            DESCRIPTION_POOL_UNAMBIGUOUS_THREAT,
            assign_ground_truth_v2,
        )

        categories = list(CALTECH_CATEGORY_MAP.keys())
        weights = [CALTECH_CATEGORY_MAP[c]["weight"] for c in categories]
        weights = np.array(weights) / sum(weights)

        adversarial_flags = self.rng.random(n) < 0.20

        scenarios = []
        for i in range(n):
            cat = self.rng.choice(categories, p=weights)
            mapping = CALTECH_CATEGORY_MAP[cat]

            desc_type_roll = self.rng.random()
            if desc_type_roll < 0.70:
                description = self.rng.choice(DESCRIPTION_POOL_AMBIGUOUS)
                desc_category = "ambiguous"
            elif desc_type_roll < 0.85:
                description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_THREAT)
                desc_category = "unambiguous_threat"
            else:
                description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN)
                desc_category = "unambiguous_benign"

            severity = self.rng.choice(mapping["severity_range"])
            time_of_day = self.rng.choice(TOD_OPTIONS, p=[0.25, 0.35, 0.20, 0.20])
            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)
            site_type = sample_site_type(self.rng)

            badge_roll = self.rng.random()
            if badge_roll < 0.20:
                badge_minutes_ago = int(self.rng.randint(1, 10))
            elif badge_roll < 0.40:
                badge_minutes_ago = int(self.rng.randint(10, 30))
            else:
                badge_minutes_ago = None

            is_adversarial = bool(adversarial_flags[i])
            if is_adversarial:
                severity, adj_zone_type, adj_sensitivity, time_of_day, adj_fpr = (
                    _inject_adversarial_signals(
                        severity, zone["type"], zone["sensitivity"],
                        time_of_day, device["false_positive_rate"], self.rng,
                    )
                )
                zone["type"] = adj_zone_type
                zone["sensitivity"] = adj_sensitivity
                device["false_positive_rate"] = round(adj_fpr, 3)

            gt, weighted_sum, is_ambiguous = assign_ground_truth_v2(
                zone_type=zone["type"],
                zone_sensitivity=zone["sensitivity"],
                time_of_day=time_of_day,
                device_fpr=device["false_positive_rate"],
                severity=severity,
                badge_access_minutes_ago=badge_minutes_ago,
                rng=self.rng,
            )

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day,
                device["false_positive_rate"], self.rng, dataset="caltech",
            )
            if is_adversarial and difficulty == "easy":
                difficulty = "medium"

            badge_access_events = []
            if badge_minutes_ago is not None:
                badge_access_events = [{
                    "minutes_ago": badge_minutes_ago,
                    "event_type": "badge_granted",
                    "resolved": True,
                }]

            alert = {
                "alert_id": f"caltech-meta-v2-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "metadata",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": badge_access_events,
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "weighted_sum": weighted_sum,
                    "difficulty": difficulty,
                    "source_dataset": "caltech_camera_traps",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": i,
                    "adversarial": is_adversarial,
                    "ambiguity_flag": is_ambiguous,
                    "description_category": desc_category,
                    "generation_version": "v2",
                },
            }
            scenarios.append(alert)

        return scenarios


class VisualGenerator:
    """Generate Visual Track scenarios.

    These are identical to Metadata Track scenarios but with visual_data populated.
    The visual_data.uri field points to the actual video/image file from the source
    dataset. Evaluators must download the source datasets separately.
    """

    def __init__(self, seed: int = 42, version: str = "v1"):
        self.rng = np.random.RandomState(seed)
        self.metadata_gen = MetadataGenerator(seed=seed, version=version)

    def generate_ucf_crime(self, n: int = 3000) -> list[dict]:
        """Generate Visual Track scenarios from UCF Crime.

        Same scenarios as metadata track but with visual_data populated.
        URI format: ucf_crime/{category}/{video_id}.mp4
        """
        scenarios = self.metadata_gen.generate_ucf_crime(n)
        for s in scenarios:
            s["track"] = "visual"
            s["alert_id"] = s["alert_id"].replace("meta", "visual")
            cat = s["_meta"]["source_category"]
            idx = s["_meta"]["index"]
            s["visual_data"] = {
                "type": "video_clip",
                "uri": f"ucf_crime/{cat}/{cat}_{idx:04d}.mp4",
                "duration_sec": round(float(self.rng.uniform(5, 120)), 1),
                "resolution": self.rng.choice(["320x240", "640x480", "1280x720"]),
            }
        return scenarios

    def generate_caltech(self, n: int = 3000) -> list[dict]:
        """Generate Visual Track scenarios from Caltech Camera Traps."""
        scenarios = self.metadata_gen.generate_caltech(n)
        for s in scenarios:
            s["track"] = "visual"
            s["alert_id"] = s["alert_id"].replace("meta", "visual")
            cat = s["_meta"]["source_category"]
            idx = s["_meta"]["index"]
            s["visual_data"] = {
                "type": "image",
                "uri": f"caltech_traps/{cat}/{cat}_{idx:06d}.jpg",
                "duration_sec": None,
                "resolution": self.rng.choice(["1920x1080", "2048x1536"]),
            }
        return scenarios


class VisualOnlyGenerator:
    """Generate Visual-Only Track scenarios for the v3 perception-reasoning gap experiment.

    Visual-only scenarios derive ground truth directly from UCF Crime video category labels
    (video_category source), not from metadata signal weighting. There is no description or
    severity field — the evaluated system must reason from video content alone.

    RNG isolation: this generator owns its own np.random.RandomState and never shares it
    with MetadataGenerator or any other generator (Pitfall 4 isolation rule).
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.seed = seed

    def generate(self, n: int = 500) -> list[dict]:
        """Generate n visual-only scenarios from UCF Crime categories.

        Ground truth is derived directly from UCF_CATEGORY_MAP[category]["ground_truth"].
        No description or severity key is present in the output dicts.
        """
        categories = list(UCF_CATEGORY_MAP.keys())
        # Weight Normal higher to match real-world class imbalance — same as MetadataGenerator
        # to avoid class imbalance leakage between tracks (VIS-03, D-03).
        weights = [1.0] * (len(categories) - 1) + [4.0]
        weights_arr = np.array(weights) / sum(weights)

        resolutions = ["1280x720", "1920x1080", "640x480"]

        scenarios = []
        for i in range(n):
            cat = self.rng.choice(categories, p=weights_arr)
            mapping = UCF_CATEGORY_MAP[cat]

            # GT comes from video category label, not metadata signal weighting (VIS-02)
            gt = mapping["ground_truth"]

            # Same TOD distribution as MetadataGenerator — shared pools prevent leakage (VIS-03)
            tod_weights = TOD_WEIGHTS_THREAT if gt == "THREAT" else TOD_WEIGHTS_BENIGN
            time_of_day = self.rng.choice(TOD_OPTIONS, p=tod_weights)

            zone = sample_zone(self.rng)
            device = sample_device(zone["type"], self.rng)
            weather = sample_weather(time_of_day, self.rng)

            # Use valid-site sampler so solar/substation don't get Shoplifting etc.
            site_type = _sample_valid_site(cat, self.rng)

            difficulty = _assign_difficulty(
                cat, zone["sensitivity"], time_of_day, device["false_positive_rate"],
                self.rng, dataset="ucf_crime",
            )

            # Synthetic URI — deterministic, no I/O required (T-12-01: intentional design)
            uri = f"ucf-crime/test/{cat}/{i:05d}.mp4"
            duration_sec = round(float(self.rng.uniform(4.0, 120.0)), 1)
            resolution = self.rng.choice(resolutions)

            alert = {
                "alert_id": f"ucf-visual-only-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "visual_only",
                # severity and description intentionally omitted (VIS-01, VIS-04)
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone["type"], time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": [],
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": {
                    "type": "video_clip",
                    "uri": uri,
                    "duration_sec": duration_sec,
                    "resolution": resolution,
                    "keyframe_uris": [],
                },
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": i,
                    "generation_version": "v3",
                    "visual_gt_source": "video_category",  # VIS-02
                    "adversarial": False,
                    "ambiguity_flag": False,
                },
            }
            scenarios.append(alert)

        return scenarios


class ContradictoryGenerator:
    """Generate Visual-Contradictory Track scenarios where metadata misrepresents video content.

    Two sub-types:
    - Overreach: metadata signals suggest THREAT, video content is BENIGN (Normal category)
    - Underreach: metadata signals suggest BENIGN, video content is THREAT (anomaly category)

    GT always follows video content. metadata_derived_gt is stored in _meta for analysis
    but is never used as the final ground_truth.

    RNG isolation: owns its own np.random.RandomState (Pitfall 4).
    """

    # THREAT-labeled UCF categories only (excludes SUSPICIOUS: Arrest, RoadAccidents, Shoplifting)
    _UNDERREACH_CATEGORIES = [
        "Abuse", "Arson", "Assault", "Burglary", "Explosion",
        "Fighting", "Robbery", "Shooting", "Stealing", "Vandalism",
    ]

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.seed = seed

    def generate(self, n: int = 500) -> list[dict]:
        """Generate n contradictory scenarios with guaranteed GT divergence.

        Each scenario has _meta.metadata_derived_gt != _meta.video_derived_gt.
        Final ground_truth always equals video_derived_gt.
        """
        from psai_bench.distributions import (
            CONTRADICTORY_BENIGN_DESCRIPTIONS,
            CONTRADICTORY_THREAT_DESCRIPTIONS,
            assign_ground_truth_v2,
        )

        resolutions = ["1280x720", "1920x1080", "640x480"]
        low_fpr_mean, low_fpr_std = 0.85, 0.08    # low_quality profile
        high_fpr_mean, high_fpr_std = 0.30, 0.10  # high_quality profile

        scenarios = []
        i = 0
        attempts = 0
        max_attempts = n * 20  # safety ceiling

        while len(scenarios) < n and attempts < max_attempts:
            attempts += 1
            idx = i  # monotonic scenario index

            # Sub-type selection: ~50% overreach, ~50% underreach
            is_overreach = self.rng.random() < 0.50

            if is_overreach:
                # OVERREACH: video=BENIGN (Normal), metadata signals biased toward THREAT
                cat = "Normal"
                video_derived_gt = UCF_CATEGORY_MAP[cat]["ground_truth"]  # "BENIGN"

                zone_type = self.rng.choice(["restricted", "utility"])
                zone_sensitivity = int(np.clip(self.rng.randint(4, 6), 1, 5))
                time_of_day = self.rng.choice(["night", "dawn"])
                severity = self.rng.choice(["HIGH", "CRITICAL"])
                badge_minutes_ago = None
                device_fpr = float(np.clip(self.rng.normal(low_fpr_mean, low_fpr_std), 0.01, 0.99))
                description = self.rng.choice(CONTRADICTORY_THREAT_DESCRIPTIONS)
            else:
                # UNDERREACH: video=THREAT (anomaly category), metadata signals biased toward BENIGN
                cat = self.rng.choice(self._UNDERREACH_CATEGORIES)
                video_derived_gt = UCF_CATEGORY_MAP[cat]["ground_truth"]  # "THREAT"

                zone_type = self.rng.choice(["parking", "interior"])
                zone_sensitivity = int(np.clip(self.rng.randint(1, 3), 1, 5))
                time_of_day = "day"
                severity = "LOW"
                badge_minutes_ago = int(self.rng.randint(1, 10))
                device_fpr = float(np.clip(self.rng.normal(high_fpr_mean, high_fpr_std), 0.01, 0.99))
                description = self.rng.choice(CONTRADICTORY_BENIGN_DESCRIPTIONS)

            # Compute metadata_derived_gt from biased signals — must differ from video_derived_gt.
            # Retry by resampling zone and time if they accidentally agree (up to 10 retries).
            agreed = True
            for _retry in range(11):
                metadata_derived_gt, _ws, _amb = assign_ground_truth_v2(
                    zone_type=zone_type,
                    zone_sensitivity=zone_sensitivity,
                    time_of_day=time_of_day,
                    device_fpr=device_fpr,
                    severity=severity,
                    badge_access_minutes_ago=badge_minutes_ago,
                    rng=self.rng,
                )
                if metadata_derived_gt != video_derived_gt:
                    agreed = False
                    break
                # Resample zone and time only (not sub-type or category)
                if is_overreach:
                    zone_type = self.rng.choice(["restricted", "utility"])
                    zone_sensitivity = int(np.clip(self.rng.randint(4, 6), 1, 5))
                    time_of_day = self.rng.choice(["night", "dawn"])
                else:
                    zone_type = self.rng.choice(["parking", "interior"])
                    zone_sensitivity = int(np.clip(self.rng.randint(1, 3), 1, 5))

            if agreed:
                # After 10 retries, GTs still agree — skip this scenario
                i += 1
                continue

            # Build remaining fields
            zone_name = self.rng.choice(list(UCF_CATEGORY_MAP.keys()))  # placeholder draw consumed
            zone = {
                "id": f"zone-{self.rng.randint(100, 999)}",
                "name": self.rng.choice(
                    ["North Fence Line", "East Perimeter", "Control Room", "Transformer Yard",
                     "Main Parking Lot", "Equipment Hall", "SCADA Room", "Inverter Station"]
                ),
                "type": zone_type,
                "sensitivity": zone_sensitivity,
                "operating_hours": "24/7",
            }

            device = sample_device(zone_type, self.rng)
            device["false_positive_rate"] = round(device_fpr, 3)

            weather = sample_weather(time_of_day, self.rng)
            site_type = _sample_valid_site(cat, self.rng)

            duration_sec = round(float(self.rng.uniform(4.0, 120.0)), 1)
            resolution = self.rng.choice(resolutions)

            difficulty = _assign_difficulty(
                cat, zone_sensitivity, time_of_day, device_fpr,
                self.rng, dataset="ucf_crime",
            )

            alert = {
                "alert_id": f"ucf-contradictory-{idx:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "visual_contradictory",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone_type, time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": (
                        [{"minutes_ago": badge_minutes_ago, "event_type": "badge_granted",
                          "resolved": True}]
                        if badge_minutes_ago is not None else []
                    ),
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": {
                    "type": "video_clip",
                    "uri": f"ucf-crime/test/{cat}/{idx:05d}.mp4",
                    "duration_sec": duration_sec,
                    "resolution": resolution,
                    "keyframe_uris": [],
                },
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": video_derived_gt,
                    "video_derived_gt": video_derived_gt,
                    "metadata_derived_gt": metadata_derived_gt,
                    "contradictory": True,
                    "visual_gt_source": "video_category",
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": cat,
                    "seed": self.seed,
                    "index": idx,
                    "generation_version": "v3",
                    "adversarial": False,
                    "ambiguity_flag": False,
                },
            }
            scenarios.append(alert)
            i += 1

        return scenarios


class TemporalSequenceGenerator:
    """Generate Temporal Sequence Track scenarios for Phase 14.

    Produces groups of 3-5 related alerts threaded by sequence_id with monotonically
    increasing timestamps and three escalation narrative patterns:
    - monotonic_escalation: alerts escalate from LOW/MEDIUM to HIGH severity
    - escalation_then_resolution: escalates to peak then resolves with badge scan
    - false_alarm: starts high-severity, subsequent alerts show it was benign

    The escalation_pattern stored in _meta gives Phase 15's score_sequences() the
    label it needs to measure escalation latency and resolution detection.

    RNG isolation: owns its own np.random.RandomState (Pitfall 4).
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.seed = seed

    def generate(self, n_sequences: int = 50) -> list[dict]:
        """Generate n_sequences temporal sequences, returning a flat list of alerts."""
        alerts = []
        global_index = 0
        patterns = ["monotonic_escalation", "escalation_then_resolution", "false_alarm"]
        for seq_idx in range(n_sequences):
            pattern = patterns[seq_idx % 3]
            seq_alerts = self._build_sequence(seq_idx, pattern, global_index)
            alerts.extend(seq_alerts)
            global_index += len(seq_alerts)
        return alerts

    def _build_sequence(self, seq_idx: int, pattern: str, start_index: int) -> list[dict]:
        """Build a single temporal sequence of 3-5 alerts."""
        from psai_bench.distributions import (
            DESCRIPTION_POOL_AMBIGUOUS,
            DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN,
            DESCRIPTION_POOL_UNAMBIGUOUS_THREAT,
            DEVICE_FPR,
            DEVICE_QUALITY_WEIGHTS,
            assign_ground_truth_v2,
        )

        seq_length = int(self.rng.randint(3, 6))  # 3, 4, or 5
        # turn_point: 1-indexed, in range [2, seq_length-1] (numpy randint exclusive of high)
        # For seq_length=3: randint(2, 3) always gives 2. For seq_length=5: gives 2, 3, or 4.
        # This guarantees at least one post-turn alert exists.
        turn_point = int(self.rng.randint(2, seq_length))

        # Sample shared per-sequence context
        categories = list(UCF_CATEGORY_MAP.keys())
        category = self.rng.choice(categories)
        site_type = _sample_valid_site(category, self.rng)
        zone_sensitivity = int(self.rng.choice([1, 2, 3, 4, 5]))  # base sensitivity

        # Device sampling (shared across sequence)
        quality = self.rng.choice(
            ["low_quality", "mid_quality", "high_quality"], p=DEVICE_QUALITY_WEIGHTS
        )
        mean_fpr, std_fpr = DEVICE_FPR[quality]
        device_fpr = float(np.clip(self.rng.normal(mean_fpr, std_fpr), 0.01, 0.99))
        device_type = quality  # e.g. "low_quality", "mid_quality", "high_quality"

        # Base timestamp and interval
        base_time_str = _generate_timestamp("day", self.rng)
        base_dt = datetime.fromisoformat(base_time_str)
        interval_minutes = int(self.rng.randint(5, 21))

        # Weather sampled once per sequence
        weather = sample_weather("day", self.rng)

        alerts = []
        for pos in range(1, seq_length + 1):
            # Determine signal trajectory based on pattern and position
            if pattern == "monotonic_escalation":
                if pos < turn_point:
                    severity = self.rng.choice(["LOW", "MEDIUM"])
                    zone_type = self.rng.choice(["lobby", "parking"])
                    time_of_day = self.rng.choice(["day", "evening"])
                    badge_access_minutes_ago = None
                    description = self.rng.choice(DESCRIPTION_POOL_AMBIGUOUS)
                else:
                    severity = "HIGH"
                    zone_type = "restricted"
                    time_of_day = "night"
                    badge_access_minutes_ago = None
                    description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_THREAT)

            elif pattern == "escalation_then_resolution":
                if pos <= turn_point:
                    severity = "LOW" if pos == 1 else "HIGH"
                    zone_type = "restricted"
                    time_of_day = "night"
                    badge_access_minutes_ago = None
                    if pos == turn_point:
                        description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_THREAT)
                    else:
                        description = self.rng.choice(DESCRIPTION_POOL_AMBIGUOUS)
                else:
                    severity = "LOW"
                    zone_type = "restricted"
                    time_of_day = "night"
                    badge_access_minutes_ago = int(self.rng.randint(3, 10))
                    description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN)

            else:  # false_alarm
                if pos == 1:
                    severity = self.rng.choice(["HIGH", "CRITICAL"])
                    zone_type = "restricted"
                    time_of_day = "night"
                    badge_access_minutes_ago = None
                    description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_THREAT)
                else:
                    severity = "LOW"
                    zone_type = self.rng.choice(["parking", "lobby"])
                    time_of_day = "day"
                    badge_access_minutes_ago = int(self.rng.randint(1, 8))
                    description = self.rng.choice(DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN)

            # Compute GT for this alert's signals
            gt, weighted_sum, _ = assign_ground_truth_v2(
                zone_type=zone_type,
                zone_sensitivity=zone_sensitivity,
                time_of_day=time_of_day,
                device_fpr=device_fpr,
                severity=severity,
                badge_access_minutes_ago=badge_access_minutes_ago,
                rng=self.rng,
            )

            difficulty = _assign_difficulty(
                category, zone_sensitivity, time_of_day, device_fpr, self.rng,
                dataset="ucf_crime",
            )

            # Compute strictly increasing timestamp for this position
            ts = base_dt + timedelta(minutes=interval_minutes * (pos - 1))
            timestamp = ts.isoformat()

            recent_events = _generate_recent_events(zone_type, time_of_day, self.rng)
            badge_events = (
                [] if badge_access_minutes_ago is None
                else [{"minutes_ago": badge_access_minutes_ago}]
            )

            alert = {
                "alert_id": f"ucf-temporal-{seq_idx:04d}-{pos:02d}",
                "timestamp": timestamp,
                "track": "temporal",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": {
                    "zone_id": f"zone-{seq_idx:04d}",
                    "zone_type": zone_type,
                    "zone_sensitivity": zone_sensitivity,
                },
                "device": {
                    "device_id": f"cam-{seq_idx:04d}-{pos:02d}",
                    "device_type": device_type,
                    "fpr": round(device_fpr, 3),
                },
                "context": {
                    "recent_zone_events_1h": recent_events,
                    "recent_badge_access_1h": badge_events,
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "weighted_sum": weighted_sum,
                    "difficulty": difficulty,
                    "source_dataset": "ucf_crime",
                    "source_category": category,
                    "seed": self.seed,
                    "index": start_index + (pos - 1),
                    "generation_version": "v3",
                    "sequence_id": f"seq-{seq_idx:04d}",
                    "sequence_position": pos,
                    "sequence_length": seq_length,
                    "escalation_pattern": pattern,
                },
            }
            alerts.append(alert)

        return alerts


class MultiSensorGenerator:
    """Generate Multi-Sensor Track scenarios with fused sensor data."""

    def __init__(self, seed: int = 42, version: str = "v1"):
        self.rng = np.random.RandomState(seed)
        self.visual_gen = VisualGenerator(seed=seed, version=version)

    def generate(self, n: int = 1000) -> list[dict]:
        """Generate n multi-sensor scenarios.

        Starts with Visual Track scenarios and layers access control,
        motion, and thermal sensor events on top.
        """
        base_scenarios = self.visual_gen.generate_ucf_crime(n)

        for s in base_scenarios:
            s["track"] = "multi_sensor"
            s["alert_id"] = s["alert_id"].replace("visual", "multi")
            gt = s["_meta"]["ground_truth"]

            # Add access control events
            num_access = max(0, int(self.rng.poisson(1.5)))
            access_events = []
            for _ in range(num_access):
                event_types = list(ACCESS_EVENTS.keys())
                if gt == "THREAT":
                    # Threats correlate with denied/forced events
                    probs = [0.1, 0.25, 0.35, 0.2, 0.1]
                elif gt == "BENIGN":
                    # Benign correlates with granted events
                    probs = [0.7, 0.1, 0.05, 0.1, 0.05]
                else:
                    probs = [e["weight"] for e in ACCESS_EVENTS.values()]
                probs = np.array(probs) / sum(probs)
                event_type = self.rng.choice(event_types, p=probs)

                minutes_offset = int(self.rng.randint(-10, 10))
                access_events.append({
                    "source_type": "badge_reader",
                    "event_type": event_type,
                    "timestamp": s["timestamp"],  # simplified; offset in real impl
                    "details": {
                        "badge_id": f"badge-{self.rng.randint(1000, 9999)}",
                        "door_id": f"door-{self.rng.randint(100, 999)}",
                        "minutes_offset": minutes_offset,
                    },
                })

            # Add motion/thermal events
            num_motion = max(0, int(self.rng.poisson(1)))
            for _ in range(num_motion):
                sensor_type = self.rng.choice(["pir", "vibration", "thermal"])
                access_events.append({
                    "source_type": sensor_type,
                    "event_type": self.rng.choice([
                        "motion_detected", "vibration_anomaly", "thermal_spike",
                        "perimeter_break", "ground_disturbance",
                    ]),
                    "timestamp": s["timestamp"],
                    "details": {
                        "sensor_id": f"{sensor_type}-{self.rng.randint(100, 999)}",
                        "reading": round(float(self.rng.uniform(0.3, 1.0)), 2),
                    },
                })

            s["additional_sensors"] = access_events

            # Multi-sensor scenarios are generally harder because more data = more ambiguity
            if s["_meta"]["difficulty"] == "easy" and self.rng.random() < 0.4:
                s["_meta"]["difficulty"] = "medium"

        return base_scenarios


class AdversarialV4Generator:
    """Generate Adversarial V4 Track scenarios with behavioral deception patterns.

    Three pattern types: loitering_as_waiting, authorized_as_intrusion,
    environmental_as_human. In each pattern, the description text suggests the
    wrong verdict; ground truth is computed from actual context signals via
    assign_ground_truth_v2.

    RNG isolation: owns its own np.random.RandomState to prevent seed regression
    in existing tracks (Pitfall 10 from PITFALLS.md).
    """

    _PATTERN_TYPES = [
        "loitering_as_waiting",
        "authorized_as_intrusion",
        "environmental_as_human",
    ]

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.seed = seed

    def generate(self, n: int = 100) -> list[dict]:
        from psai_bench.distributions import (
            ADV_V4_AUTHORIZED_AS_INTRUSION,
            ADV_V4_ENVIRONMENTAL_AS_HUMAN,
            ADV_V4_LOITERING_AS_WAITING,
            EXPECTED_ACTIVITIES,
            assign_ground_truth_v2,
        )

        # Assign pattern types in round-robin order then shuffle for variety
        pattern_assignments = (self._PATTERN_TYPES * ((n // 3) + 1))[:n]
        pattern_assignments = list(self.rng.permutation(pattern_assignments))

        pool_map = {
            "loitering_as_waiting": ADV_V4_LOITERING_AS_WAITING,
            "authorized_as_intrusion": ADV_V4_AUTHORIZED_AS_INTRUSION,
            "environmental_as_human": ADV_V4_ENVIRONMENTAL_AS_HUMAN,
        }

        scenarios = []
        for i, pattern_type in enumerate(pattern_assignments):
            description = self.rng.choice(pool_map[pattern_type])

            if pattern_type == "loitering_as_waiting":
                zone_type = self.rng.choice(["parking", "interior"])
                zone_sensitivity = int(np.clip(self.rng.randint(1, 3), 1, 5))
                time_of_day = "day"
                severity = "LOW"
                badge_minutes_ago = int(self.rng.randint(1, 9))
                device_fpr = float(np.clip(self.rng.normal(0.60, 0.10), 0.01, 0.99))

            elif pattern_type == "authorized_as_intrusion":
                zone_type = "interior"
                zone_sensitivity = int(np.clip(self.rng.randint(2, 4), 1, 5))
                time_of_day = self.rng.choice(["day", "dusk"])
                severity = self.rng.choice(["LOW", "MEDIUM"])
                badge_minutes_ago = int(self.rng.randint(1, 8))
                device_fpr = float(np.clip(self.rng.normal(0.55, 0.12), 0.01, 0.99))

            else:  # environmental_as_human
                zone_type = self.rng.choice(["perimeter", "parking"])
                zone_sensitivity = int(np.clip(self.rng.randint(1, 3), 1, 5))
                time_of_day = self.rng.choice(["day", "dawn"])
                severity = "LOW"
                badge_minutes_ago = None
                device_fpr = float(np.clip(self.rng.normal(0.85, 0.08), 0.01, 0.99))

            # Build zone dict directly (not via sample_zone — we control zone_type for GT)
            zone_name_options = {
                "perimeter": ["North Fence Line", "East Perimeter", "West Perimeter", "Main Gate"],
                "interior": ["Control Room", "Equipment Hall", "Interior Corridor A"],
                "parking": ["Main Parking Lot", "Staff Parking", "Visitor Parking"],
            }
            zone = {
                "id": f"zone-{self.rng.randint(100, 999)}",
                "name": self.rng.choice(zone_name_options.get(zone_type, ["Zone-A"])),
                "type": zone_type,
                "sensitivity": zone_sensitivity,
                "operating_hours": "24/7",
            }

            device = sample_device(zone_type, self.rng)
            device["false_positive_rate"] = round(device_fpr, 3)

            weather = sample_weather(time_of_day, self.rng)
            site_type = _sample_valid_site("Normal", self.rng)

            gt, weighted_sum, is_ambiguous = assign_ground_truth_v2(
                zone_type=zone_type,
                zone_sensitivity=zone_sensitivity,
                time_of_day=time_of_day,
                device_fpr=device_fpr,
                severity=severity,
                badge_access_minutes_ago=badge_minutes_ago,
                rng=self.rng,
            )

            badge_events = []
            if badge_minutes_ago is not None:
                badge_events = [{
                    "minutes_ago": badge_minutes_ago,
                    "event_type": "badge_granted",
                    "resolved": True,
                }]

            alert = {
                "alert_id": f"adv-v4-{i:05d}",
                "timestamp": _generate_timestamp(time_of_day, self.rng),
                "track": "adversarial_v4",
                "severity": severity,
                "description": description,
                "source_type": "camera",
                "zone": zone,
                "device": device,
                "context": {
                    "recent_zone_events_1h": _generate_recent_events(
                        zone_type, time_of_day, self.rng
                    ),
                    "recent_badge_access_1h": badge_events,
                    "weather": weather,
                    "time_of_day": time_of_day,
                    "expected_activities": EXPECTED_ACTIVITIES.get(site_type, []),
                    "cross_zone_activity": {},
                    "site_type": site_type,
                },
                "visual_data": None,
                "additional_sensors": [],
                "_meta": {
                    "ground_truth": gt,
                    "weighted_sum": weighted_sum,
                    "difficulty": "hard",  # all adversarial scenarios are hard
                    "source_dataset": "adv_v4_behavioral",
                    "source_category": "Normal",
                    "seed": self.seed,
                    "index": i,
                    "adversarial": True,
                    "adversarial_type": pattern_type,
                    "ambiguity_flag": is_ambiguous,
                    "generation_version": "v4",
                },
            }
            scenarios.append(alert)

        return scenarios
