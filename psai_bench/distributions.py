"""Empirical distributions for scenario generation.

This module IS Appendix A of the spec: it documents every assumption made when
converting raw dataset annotations into structured PSAI-Bench alerts. Each
distribution is sourced from published data or security industry norms, cited inline.

All randomness flows through numpy RandomState seeded by the caller, ensuring
reproducibility.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Zone distributions
# ---------------------------------------------------------------------------
# Zone types weighted by typical critical infrastructure camera placement.
# Source: ASIS Physical Security Professional (PSP) study material, 2024 edition.
# Perimeter cameras outnumber interior cameras ~3:1 at solar/substation sites.
ZONE_TYPES = ["perimeter", "interior", "parking", "utility", "restricted"]
ZONE_WEIGHTS = [0.35, 0.15, 0.15, 0.20, 0.15]

# Sensitivity by zone type (1-5 scale). Restricted zones are always high.
# These are means; actual values are drawn from clipped normal distributions.
ZONE_SENSITIVITY = {
    "perimeter": (3.0, 0.8),   # mean, std
    "interior": (2.5, 0.7),
    "parking": (2.0, 0.6),
    "utility": (3.5, 0.8),
    "restricted": (4.5, 0.5),
}

ZONE_NAMES = {
    "perimeter": [
        "North Fence Line", "South Fence Line", "East Perimeter", "West Perimeter",
        "Main Gate", "Service Gate", "Perimeter Road", "Fence Sector A",
        "Fence Sector B", "Fence Sector C",
    ],
    "interior": [
        "Control Room", "Equipment Hall", "Server Room", "Maintenance Bay",
        "Storage Area", "Interior Corridor A", "Interior Corridor B",
    ],
    "parking": [
        "Main Parking Lot", "Staff Parking", "Visitor Parking", "Loading Dock",
    ],
    "utility": [
        "Transformer Yard", "Panel Array Section 1", "Panel Array Section 2",
        "Inverter Station", "Battery Storage", "Substation Bus",
        "Cooling System", "Generator Pad",
    ],
    "restricted": [
        "High Voltage Area", "Control Cabinet", "SCADA Room",
        "Fuel Storage", "Vault", "Secure Enclosure",
    ],
}

# ---------------------------------------------------------------------------
# Device distributions
# ---------------------------------------------------------------------------
# False positive rates for outdoor security cameras in real deployments.
# Source: Calipsa (2023) industry report: outdoor cameras generate 95-98% false alarms.
# We model the device's historical FPR as observed over 30 days.
DEVICE_FPR = {
    "low_quality": (0.85, 0.08),    # cheap outdoor PTZ, mean 85% FPR
    "mid_quality": (0.60, 0.12),    # mid-range fixed camera with basic analytics
    "high_quality": (0.30, 0.10),   # premium camera with on-edge AI filtering
}
DEVICE_QUALITY_WEIGHTS = [0.40, 0.40, 0.20]  # most deployed cameras are low/mid

CAMERA_MODELS = {
    "low_quality": ["Generic-PTZ-2MP", "Budget-Bullet-1080p", "Analog-Dome-Convert"],
    "mid_quality": ["Axis-P3245-V", "Hikvision-DS-2CD2T47", "Dahua-IPC-HFW5442T"],
    "high_quality": ["Axis-Q1808-LE", "Bosch-Flexidome-7100i", "Hanwha-XNO-9082R"],
}

# 30-day event counts. High-traffic zones generate more events.
# Source: empirical, based on typical solar farm camera event logs.
EVENTS_30D_BY_ZONE = {
    "perimeter": (450, 150),   # mean, std. Perimeter cameras are busiest (wildlife, weather).
    "interior": (80, 30),
    "parking": (200, 80),
    "utility": (120, 50),
    "restricted": (40, 20),    # restricted areas should have few events if working properly
}

# ---------------------------------------------------------------------------
# Weather distributions
# ---------------------------------------------------------------------------
# Weather conditions weighted by frequency in southwestern US (where Caltech Camera
# Traps data was collected) and typical continental US for UCF Crime.
WEATHER_CONDITIONS = ["clear", "partly_cloudy", "overcast", "rain", "fog", "wind", "snow"]
WEATHER_WEIGHTS_NORMAL = [0.35, 0.25, 0.15, 0.10, 0.05, 0.08, 0.02]

# Temperature ranges by time of day (Fahrenheit), modeled as (mean, std)
TEMP_BY_TOD = {
    "day": (78, 12),
    "night": (58, 10),
    "dawn": (55, 8),
    "dusk": (68, 10),
}

WIND_MPH = (8, 6)  # mean, std. Clipped to [0, 50].

# ---------------------------------------------------------------------------
# Time of day distributions
# ---------------------------------------------------------------------------
# Security incidents cluster at night. False alarms are uniform.
# Source: SDM Magazine 2023 alarm statistics report.
TOD_OPTIONS = ["day", "night", "dawn", "dusk"]
TOD_WEIGHTS_THREAT = [0.20, 0.50, 0.15, 0.15]   # threats peak at night
TOD_WEIGHTS_BENIGN = [0.35, 0.25, 0.20, 0.20]    # benign is more uniform

# Operating hours formats
OPERATING_HOURS = {
    "24/7": "24/7",
    "business": "06:00-18:00",
    "night_only": "18:00-06:00",
    "extended": "05:00-22:00",
}

# ---------------------------------------------------------------------------
# Site type distribution
# ---------------------------------------------------------------------------
SITE_TYPES = ["solar", "substation", "commercial", "industrial", "campus"]
SITE_WEIGHTS = [0.30, 0.20, 0.20, 0.20, 0.10]

# Expected activities by site type (what SHOULD be happening there)
EXPECTED_ACTIVITIES = {
    "solar": [
        "scheduled maintenance crew", "vegetation management", "panel cleaning",
        "wildlife activity", "weather events",
    ],
    "substation": [
        "utility crew access", "scheduled inspection", "equipment testing",
        "vegetation management",
    ],
    "commercial": [
        "employee access", "delivery", "customer traffic", "cleaning crew",
        "security patrol",
    ],
    "industrial": [
        "shift change", "forklift operation", "loading/unloading",
        "maintenance crew", "vendor access",
    ],
    "campus": [
        "student traffic", "staff access", "delivery", "event setup",
        "grounds maintenance",
    ],
}

# ---------------------------------------------------------------------------
# UCF Crime category → alert mapping
# ---------------------------------------------------------------------------
# How each UCF Crime category translates to a triage scenario.
# ground_truth: what the correct verdict should be
# severity_range: possible severity levels for this category
# description_templates: how the alert would be described by a camera/analytics system
UCF_CATEGORY_MAP = {
    "Abuse": {
        "ground_truth": "THREAT",
        "severity_range": ["HIGH", "CRITICAL"],
        "description_templates": [
            "Aggressive physical interaction detected between individuals",
            "Violent behavior observed in camera field of view",
            "Physical altercation in progress",
        ],
    },
    "Arrest": {
        "ground_truth": "SUSPICIOUS",
        "severity_range": ["MEDIUM", "HIGH"],
        "description_templates": [
            "Multiple individuals in close physical contact, one restrained",
            "Unusual gathering with physical restraint observed",
            "Person being held by multiple individuals",
        ],
    },
    "Arson": {
        "ground_truth": "THREAT",
        "severity_range": ["CRITICAL"],
        "description_templates": [
            "Fire or smoke detected in monitored area",
            "Thermal anomaly with rapid temperature increase",
            "Visible flames detected by camera analytics",
        ],
    },
    "Assault": {
        "ground_truth": "THREAT",
        "severity_range": ["HIGH", "CRITICAL"],
        "description_templates": [
            "Aggressive physical contact between individuals",
            "Person struck or pushed by another individual",
            "Violent confrontation detected",
        ],
    },
    "Burglary": {
        "ground_truth": "THREAT",
        "severity_range": ["HIGH", "CRITICAL"],
        "description_templates": [
            "Unauthorized entry detected at building perimeter",
            "Person attempting to breach secured entrance",
            "Forced entry indicators at access point",
            "Individual climbing fence near restricted area",
        ],
    },
    "Explosion": {
        "ground_truth": "THREAT",
        "severity_range": ["CRITICAL"],
        "description_templates": [
            "Sudden high-intensity visual/audio event detected",
            "Shockwave and debris detected by multiple sensors",
            "Catastrophic event detected in monitored zone",
        ],
    },
    "Fighting": {
        "ground_truth": "THREAT",
        "severity_range": ["HIGH"],
        "description_templates": [
            "Multiple individuals engaged in physical conflict",
            "Aggressive mutual contact between two or more people",
            "Physical fight in progress",
        ],
    },
    "RoadAccidents": {
        "ground_truth": "SUSPICIOUS",
        "severity_range": ["MEDIUM", "HIGH"],
        "description_templates": [
            "Vehicle collision detected near facility",
            "Sudden vehicle stop with debris on roadway",
            "Traffic incident in camera view",
        ],
    },
    "Robbery": {
        "ground_truth": "THREAT",
        "severity_range": ["CRITICAL"],
        "description_templates": [
            "Forcible theft in progress",
            "Armed individual confronting person",
            "Violent property seizure detected",
        ],
    },
    "Shooting": {
        "ground_truth": "THREAT",
        "severity_range": ["CRITICAL"],
        "description_templates": [
            "Possible weapon discharge detected",
            "Individual with weapon observed",
            "Gunshot-like event detected by audio analytics",
        ],
    },
    "Shoplifting": {
        "ground_truth": "SUSPICIOUS",
        "severity_range": ["LOW", "MEDIUM"],
        "description_templates": [
            "Unusual item concealment behavior detected",
            "Person exhibiting theft-associated movement patterns",
            "Potential merchandise removal without checkout",
        ],
    },
    "Stealing": {
        "ground_truth": "THREAT",
        "severity_range": ["MEDIUM", "HIGH"],
        "description_templates": [
            "Unauthorized removal of equipment detected",
            "Person carrying items away from restricted area",
            "Possible theft of site materials",
        ],
    },
    "Vandalism": {
        "ground_truth": "THREAT",
        "severity_range": ["MEDIUM", "HIGH"],
        "description_templates": [
            "Destructive behavior detected against property",
            "Person damaging facility equipment",
            "Intentional property damage in progress",
        ],
    },
    "Normal": {
        "ground_truth": "BENIGN",
        "severity_range": ["LOW"],
        "description_templates": [
            "Routine activity detected in monitored area",
            "Motion detected, consistent with normal operations",
            "Person observed in authorized area during operating hours",
            "Vehicle movement consistent with expected traffic pattern",
            "Environmental motion trigger (wind, vegetation, shadow)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Shared description pools (v2) — decoupled from UCF categories
# ---------------------------------------------------------------------------
# AMBIGUOUS: same description can appear across THREAT, SUSPICIOUS, or BENIGN GT
# depending on context (zone, time, device FPR, badge access). ~63% of v2 descriptions.
DESCRIPTION_POOL_AMBIGUOUS = [
    "Motion detected, human-shaped silhouette, zone-perimeter, 02:14",
    "Person observed near access point, no badge event in prior 30 min",
    "Individual moving along fence line, gait analysis inconclusive",
    "Vehicle stopped outside facility, engine running, no appointment on file",
    "Two persons detected in utility corridor, unscheduled access",
    "Human presence detected at remote site, no recent badge grant",
    "Motion near high-voltage equipment, identity unverified",
    "Person loitering near entry point, 18 min stationary",
    "Unscheduled vehicle approaching perimeter gate, slow speed",
    "Individual carrying equipment toward exit, badge scan 4 min ago",
    "Person crouching near panel array section, tool visible",
    "Motion detected in restricted zone, personnel roster not updated",
    "Camera analytics: unusual gait pattern detected, zone-3, 23:47",
    "Multiple persons congregating near service gate, partial obstruction",
    "Person detected on perimeter road, no escort logged, 01:05",
    "Individual accessing storage area, authorization status unconfirmed",
    "Vehicle traversing access road outside posted hours",
    "Person detected near fuel storage area, no hot work permit active",
    "Camera trigger: human-class object, zone-interior, low confidence 0.62",
    "Motion detected in equipment hall, shift schedule shows no activity expected",
    "Person near cooling system, carrying bag, movement purposeful",
    "Thermal signature detected near battery storage, source unconfirmed",
]

# UNAMBIGUOUS THREAT: always indicate high threat signal regardless of context (~23% of pool).
DESCRIPTION_POOL_UNAMBIGUOUS_THREAT = [
    "Visible flames detected in panel array, fire suppression not triggered",
    "Person cutting perimeter fence with visible tool, 03:22",
    "Gunshot-like audio event detected, multiple sensor confirmations",
    "Forced entry at control cabinet door, physical damage visible",
    "Smoke rising from transformer yard, thermal spike +40F above baseline",
    "Perimeter breach: fence displacement confirmed by vibration sensor",
    "Explosive-like event detected: sudden pressure and light burst",
    "Camera analytics: assault-class motion between two persons detected",
]

# UNAMBIGUOUS BENIGN: always indicate low threat signal regardless of context (~14% of pool).
DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN = [
    "Environmental trigger: wind gust 22 mph causing vegetation motion",
    "Camera false activation: spider web on lens, no motion in scene",
    "Small animal (rabbit-class) crossing sensor field, no human present",
    "Scheduled maintenance crew confirmed via badge: 3 personnel authorized",
    "Camera self-test trigger, no scene content, internal diagnostic",
]

# ---------------------------------------------------------------------------
# V2 Ground Truth Decision Function
# ---------------------------------------------------------------------------
# GT determined by weighted combination of context signals, not by category alone.
# Signal scoring: each signal contributes to a weighted_sum in [-1.25, +1.25].
# Negative = BENIGN evidence, Positive = THREAT evidence.
# GT thresholds: sum > +0.30 → THREAT, sum < -0.30 → BENIGN, else → SUSPICIOUS
#
# SCEN-03 compliance: severity max score = 0.25 < threshold 0.30.
# Severity alone can never cross the threshold.

_GT_THRESHOLD = 0.30
_AMBIGUITY_THRESHOLD = 0.10  # |sum| < this → "ambiguous by design"

_ZONE_THREAT_SCORES = {
    "restricted": +0.40,
    "utility": +0.25,
    "perimeter": +0.10,
    "interior": 0.00,
    "parking": -0.15,
}

_TIME_THREAT_SCORES = {
    "night": +0.35,
    "dawn": +0.15,
    "dusk": +0.10,
    "day": -0.20,
}

_SEVERITY_THREAT_SCORES = {
    "CRITICAL": +0.25,
    "HIGH": +0.15,
    "MEDIUM": 0.00,
    "LOW": -0.20,
}


def _device_fpr_score(fpr: float) -> float:
    """Map device FPR to threat score. Linear: FPR=0.05 → +0.13, FPR=0.95 → -0.27."""
    return round(0.15 - (fpr * (0.40 / 0.90)), 3)


def assign_ground_truth_v2(
    zone_type: str,
    zone_sensitivity: int,
    time_of_day: str,
    device_fpr: float,
    severity: str,
    badge_access_minutes_ago: int | None,
    rng: "np.random.RandomState",
) -> tuple[str, float, bool]:
    """Assign ground truth using a weighted multi-signal scoring function.

    Returns:
        tuple: (ground_truth label, weighted_sum, is_ambiguous)
    """
    zone_base = _ZONE_THREAT_SCORES.get(zone_type, 0.0)
    sensitivity_factor = 0.6 + (zone_sensitivity - 1) * 0.2
    zone_score = zone_base * sensitivity_factor

    time_score = _TIME_THREAT_SCORES.get(time_of_day, 0.0)
    fpr_score = _device_fpr_score(device_fpr)
    severity_score = _SEVERITY_THREAT_SCORES.get(severity, 0.0)

    if badge_access_minutes_ago is not None and badge_access_minutes_ago < 10:
        badge_score = -0.45
    elif badge_access_minutes_ago is not None and badge_access_minutes_ago <= 30:
        badge_score = -0.25
    else:
        badge_score = 0.0

    weighted_sum = zone_score + time_score + fpr_score + severity_score + badge_score
    weighted_sum = round(weighted_sum, 4)

    is_ambiguous = abs(weighted_sum) < _AMBIGUITY_THRESHOLD

    if weighted_sum > _GT_THRESHOLD:
        gt = "THREAT"
    elif weighted_sum < -_GT_THRESHOLD:
        gt = "BENIGN"
    else:
        gt = "SUSPICIOUS"

    return gt, weighted_sum, is_ambiguous


# All severity levels — used for severity_noise injection.
ALL_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# ---------------------------------------------------------------------------
# Caltech Camera Traps → alert mapping
# ---------------------------------------------------------------------------
# Camera trap triggers are overwhelmingly false alarms (70% empty).
# Real-world outdoor cameras at infrastructure sites have similar FPR profiles.
CALTECH_CATEGORY_MAP = {
    "empty": {
        "ground_truth": "BENIGN",
        "weight": 0.70,  # 70% of Caltech images are empty triggers
        "severity_range": ["LOW"],
        "description_templates": [
            "Motion sensor triggered, no visible cause",
            "Environmental trigger detected (wind/shadow/vegetation)",
            "False motion activation, camera field clear",
            "Sensor triggered by environmental conditions",
        ],
    },
    "animal_small": {
        "ground_truth": "BENIGN",
        "weight": 0.12,
        "severity_range": ["LOW"],
        "description_templates": [
            "Small animal detected in camera view",
            "Wildlife motion trigger (small mammal or bird)",
            "Non-human motion detected near ground level",
        ],
    },
    "animal_large": {
        "ground_truth": "BENIGN",
        "weight": 0.08,
        "severity_range": ["LOW", "MEDIUM"],
        "description_templates": [
            "Large animal detected near perimeter",
            "Significant wildlife activity (deer/coyote class)",
            "Large non-human entity moving through monitored zone",
        ],
    },
    "vehicle": {
        "ground_truth": "SUSPICIOUS",
        "weight": 0.05,
        "severity_range": ["MEDIUM", "HIGH"],
        "description_templates": [
            "Unscheduled vehicle detected at remote site",
            "Vehicle approaching facility outside operating hours",
            "Unknown vehicle stopped near perimeter",
        ],
    },
    "person": {
        "ground_truth": "SUSPICIOUS",
        "weight": 0.05,
        "severity_range": ["MEDIUM", "HIGH", "CRITICAL"],
        "description_templates": [
            "Person detected at remote unmanned facility",
            "Human presence at site outside scheduled maintenance",
            "Individual observed near restricted perimeter",
        ],
    },
}

# ---------------------------------------------------------------------------
# Cross-zone activity patterns (for multi-sensor track)
# ---------------------------------------------------------------------------
CROSS_ZONE_PATTERNS = {
    "correlated_threat": {
        "description": "Multiple zones triggered in sequence suggesting coordinated intrusion",
        "zone_count": (2, 4),
        "time_spread_minutes": (1, 15),
    },
    "isolated_benign": {
        "description": "Single zone triggered with no correlated activity",
        "zone_count": (1, 1),
        "time_spread_minutes": (0, 0),
    },
    "maintenance_pattern": {
        "description": "Badge access followed by expected zone triggers",
        "zone_count": (1, 3),
        "time_spread_minutes": (5, 60),
    },
}

# ---------------------------------------------------------------------------
# Access control event types (for multi-sensor track)
# ---------------------------------------------------------------------------
ACCESS_EVENTS = {
    "badge_granted": {"ground_truth_bias": "BENIGN", "weight": 0.60},
    "badge_denied": {"ground_truth_bias": "SUSPICIOUS", "weight": 0.15},
    "door_forced": {"ground_truth_bias": "THREAT", "weight": 0.10},
    "door_held_open": {"ground_truth_bias": "SUSPICIOUS", "weight": 0.10},
    "tailgate_detected": {"ground_truth_bias": "SUSPICIOUS", "weight": 0.05},
}


def sample_zone(rng: np.random.RandomState) -> dict:
    """Generate a random zone configuration."""
    zone_type = rng.choice(ZONE_TYPES, p=ZONE_WEIGHTS)
    mean, std = ZONE_SENSITIVITY[zone_type]
    sensitivity = int(np.clip(rng.normal(mean, std), 1, 5))
    name = rng.choice(ZONE_NAMES[zone_type])
    hours_key = rng.choice(["24/7", "business", "night_only", "extended"], p=[0.5, 0.2, 0.2, 0.1])
    return {
        "id": f"zone-{rng.randint(1000, 9999)}",
        "name": name,
        "type": zone_type,
        "sensitivity": sensitivity,
        "operating_hours": OPERATING_HOURS[hours_key],
    }


def sample_device(zone_type: str, rng: np.random.RandomState) -> dict:
    """Generate a random device configuration appropriate for the zone."""
    quality = rng.choice(
        ["low_quality", "mid_quality", "high_quality"], p=DEVICE_QUALITY_WEIGHTS
    )
    mean_fpr, std_fpr = DEVICE_FPR[quality]
    fpr = float(np.clip(rng.normal(mean_fpr, std_fpr), 0.01, 0.99))
    mean_events, std_events = EVENTS_30D_BY_ZONE[zone_type]
    events = max(1, int(rng.normal(mean_events, std_events)))
    model = rng.choice(CAMERA_MODELS[quality])
    return {
        "id": f"cam-{rng.randint(10000, 99999)}",
        "false_positive_rate": round(fpr, 3),
        "total_events_30d": events,
        "model": model,
    }


def sample_weather(time_of_day: str, rng: np.random.RandomState) -> dict:
    """Generate weather conditions."""
    condition = rng.choice(WEATHER_CONDITIONS, p=WEATHER_WEIGHTS_NORMAL)
    mean_temp, std_temp = TEMP_BY_TOD[time_of_day]
    temp = round(float(rng.normal(mean_temp, std_temp)), 1)
    wind = round(float(np.clip(rng.normal(*WIND_MPH), 0, 50)), 1)
    return {"condition": condition, "temp_f": temp, "wind_mph": wind}


def sample_site_type(rng: np.random.RandomState) -> str:
    """Sample a site type."""
    return rng.choice(SITE_TYPES, p=SITE_WEIGHTS)
