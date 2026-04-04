"""PSAI-Bench Alert Schema and Output Schema definitions.

These schemas define the exact input/output contract for evaluated systems.
All scenario generators produce alerts conforming to ALERT_SCHEMA.
All system outputs must conform to OUTPUT_SCHEMA.
"""

from jsonschema import validate, ValidationError

ALERT_SCHEMA = {
    "type": "object",
    "required": [
        "alert_id", "timestamp", "track", "severity", "description",
        "source_type", "zone", "device", "context",
    ],
    "properties": {
        "alert_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "track": {"type": "string", "enum": ["visual", "metadata", "multi_sensor"]},
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
    "required": ["alert_id", "verdict", "confidence", "reasoning", "processing_time_ms"],
    "properties": {
        "alert_id": {"type": "string"},
        "verdict": {"type": "string", "enum": ["THREAT", "SUSPICIOUS", "BENIGN"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string", "minLength": 20},
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
DIFFICULTIES = ("easy", "medium", "hard")


def validate_alert(alert: dict) -> None:
    """Validate an alert against the PSAI-Bench Alert Schema. Raises ValidationError."""
    validate(instance=alert, schema=ALERT_SCHEMA)


def validate_output(output: dict) -> None:
    """Validate a system output against the PSAI-Bench Output Schema. Raises ValidationError."""
    validate(instance=output, schema=OUTPUT_SCHEMA)
