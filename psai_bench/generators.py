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
            site_type = sample_site_type(self.rng)
            for _ in range(10):  # max 10 resamples
                blocked = SITE_CATEGORY_BLOCKLIST.get(site_type, set())
                if cat not in blocked:
                    break
                site_type = sample_site_type(self.rng)

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

            site_type = sample_site_type(self.rng)
            for _ in range(10):
                blocked = SITE_CATEGORY_BLOCKLIST.get(site_type, set())
                if cat not in blocked:
                    break
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
