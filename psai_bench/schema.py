"""PSAI-Bench Alert Schema and Output Schema definitions.

These schemas define the exact input/output contract for evaluated systems.
All scenario generators produce alerts conforming to ALERT_SCHEMA.
All system outputs must conform to OUTPUT_SCHEMA.
"""

from jsonschema import validate

ALERT_SCHEMA = {
    "type": "object",
    "required": [
        "alert_id", "timestamp", "track",
        "source_type", "zone", "device", "context",
    ],
    "properties": {
        "alert_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "track": {
            "type": "string",
            "enum": [
                "visual", "metadata", "multi_sensor",       # existing v2 tracks
                "visual_only", "visual_contradictory", "temporal",  # v3 new tracks
                "adversarial_v4",                           # v4 behavioral adversarial
            ],
        },
        "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "description": {"type": "string", "minLength": 10},
        "source_type": {
            "type": "string",
            "enum": ["camera", "pir", "badge_reader", "vibration", "thermal"],
        },
        "zone": {
            "type": "object",
            "required": ["id", "name", "type", "sensitivity", "operating_hours"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["perimeter", "interior", "parking", "utility", "restricted"],
                },
                "sensitivity": {"type": "integer", "minimum": 1, "maximum": 5},
                "operating_hours": {"type": "string"},
            },
        },
        "device": {
            "type": "object",
            "required": ["id", "false_positive_rate", "total_events_30d", "model"],
            "properties": {
                "id": {"type": "string"},
                "false_positive_rate": {"type": "number", "minimum": 0, "maximum": 1},
                "total_events_30d": {"type": "integer", "minimum": 0},
                "model": {"type": "string"},
            },
        },
        "context": {
            "type": "object",
            "required": [
                "recent_zone_events_1h", "weather", "time_of_day",
                "expected_activities", "site_type",
            ],
            "properties": {
                "recent_zone_events_1h": {"type": "array"},
                "recent_badge_access_1h": {"type": "array"},
                "weather": {
                    "type": "object",
                    "properties": {
                        "condition": {"type": "string"},
                        "temp_f": {"type": "number"},
                        "wind_mph": {"type": "number"},
                    },
                },
                "time_of_day": {
                    "type": "string",
                    "enum": ["day", "night", "dawn", "dusk"],
                },
                "expected_activities": {"type": "array", "items": {"type": "string"}},
                "cross_zone_activity": {"type": "object"},
                "site_type": {
                    "type": "string",
                    "enum": ["solar", "substation", "commercial", "industrial", "campus"],
                },
            },
        },
        "visual_data": {
            "type": ["object", "null"],
            "properties": {
                "type": {"type": "string", "enum": ["video_clip", "image", "null"]},
                "uri": {"type": ["string", "null"]},
                "duration_sec": {"type": ["number", "null"]},
                "resolution": {"type": ["string", "null"]},
                "keyframe_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URIs of extracted keyframes for frame-extraction baseline",
                },
            },
        },
        "additional_sensors": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source_type", "event_type", "timestamp"],
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["badge_reader", "pir", "vibration", "thermal"],
                    },
                    "event_type": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "details": {"type": "object"},
                },
            },
        },
    },
}

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["alert_id", "verdict", "confidence"],
    "properties": {
        "alert_id": {"type": "string"},
        "verdict": {"type": "string", "enum": ["THREAT", "SUSPICIOUS", "BENIGN"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "probability that the verdict is correct"},
        "reasoning": {"type": "string"},
        "factors_considered": {"type": "array", "items": {"type": "string"}},
        "processing_time_ms": {"type": "integer", "minimum": 0},
        "model_info": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "provider": {"type": "string"},
                "estimated_cost_usd": {"type": "number"},
            },
        },
    },
}

VERDICTS = ("THREAT", "SUSPICIOUS", "BENIGN")
DISPATCH_ACTIONS = (
    "armed_response", "patrol", "operator_review",
    "auto_suppress", "request_data",
)
DIFFICULTIES = ("easy", "medium", "hard")

# _meta block structure (not schema-validated — benchmark-internal only).
# v2 adds generation_version, weighted_sum, adversarial, ambiguity_flag, description_category.
_META_SCHEMA_V2 = {
    "type": "object",
    "properties": {
        "ground_truth": {"type": "string", "enum": ["THREAT", "SUSPICIOUS", "BENIGN"]},
        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
        "source_dataset": {"type": "string"},
        "source_category": {"type": "string"},
        "seed": {"type": "integer"},
        "index": {"type": "integer"},
        "generation_version": {"type": "string", "enum": ["v1", "v2", "v3", "v4"]},
        "weighted_sum": {"type": "number"},
        "adversarial": {"type": "boolean"},
        "ambiguity_flag": {"type": "boolean"},
        "description_category": {"type": "string"},
        # v3 fields (all optional)
        "visual_gt_source": {
            "type": "string",
            "enum": ["video_category", "metadata_signals"],
            "description": "Whether GT was derived from video content or metadata signal weighting",
        },
        "contradictory": {
            "type": "boolean",
            "description": "True if scenario metadata intentionally misrepresents video content",
        },
        "sequence_id": {
            "type": ["string", "null"],
            "description": "Group identifier for temporal sequences; null for independent alerts",
        },
        "sequence_position": {
            "type": ["integer", "null"],
            "description": "1-indexed position within sequence; null for independent alerts",
        },
        "sequence_length": {
            "type": ["integer", "null"],
            "description": "Total alerts in this sequence; null for independent alerts",
        },
    },
    "required": ["ground_truth", "difficulty", "source_dataset", "source_category", "seed", "index"],
}

# v4 additions — additive mutations; do not modify dicts above this line
OUTPUT_SCHEMA["properties"]["dispatch"] = {
    "type": "string",
    "enum": list(DISPATCH_ACTIONS),
    "description": "Recommended operational action (optional; required for cost scoring)",
}

_META_SCHEMA_V2["properties"]["optimal_dispatch"] = {
    "type": "string",
    "enum": list(DISPATCH_ACTIONS),
    "description": "Benchmark-computed optimal action for cost scoring",
}
_META_SCHEMA_V2["properties"]["adversarial_type"] = {
    "type": ["string", "null"],
    "enum": [None, "signal_flip", "loitering_as_waiting",
             "authorized_as_intrusion", "environmental_as_human"],
    "description": "v4 adversarial sub-type; null for non-adversarial scenarios",
}


def validate_alert(alert: dict) -> None:
    """Validate an alert against the PSAI-Bench Alert Schema. Raises ValidationError."""
    validate(instance=alert, schema=ALERT_SCHEMA)


def validate_output(output: dict) -> None:
    """Validate a system output against the PSAI-Bench Output Schema. Raises ValidationError."""
    validate(instance=output, schema=OUTPUT_SCHEMA)
