"""Tests for schema.py v4 extensions — DISPATCH_ACTIONS, dispatch field in OUTPUT_SCHEMA,
_META_SCHEMA_V2 additions (optimal_dispatch, adversarial_type, v4 generation_version).
"""

import pytest
from jsonschema import ValidationError

from psai_bench.schema import (
    DISPATCH_ACTIONS,
    VERDICTS,
    OUTPUT_SCHEMA,
    _META_SCHEMA_V2,
    validate_output,
)


# Test 1: backward compat — output without dispatch field still validates
def test_validate_output_no_dispatch():
    validate_output({"alert_id": "x", "verdict": "THREAT", "confidence": 0.9})


# Test 2: output with a valid dispatch field validates
def test_validate_output_with_dispatch():
    validate_output(
        {"alert_id": "x", "verdict": "THREAT", "confidence": 0.9, "dispatch": "armed_response"}
    )


# Test 3: output with an invalid dispatch action raises ValidationError
def test_validate_output_invalid_dispatch_raises():
    with pytest.raises(ValidationError):
        validate_output(
            {"alert_id": "x", "verdict": "THREAT", "confidence": 0.9, "dispatch": "invalid_action"}
        )


# Test 4: VERDICTS tuple is byte-identical to v3.0
def test_verdicts_unchanged():
    assert VERDICTS == ("THREAT", "SUSPICIOUS", "BENIGN")


# Test 5: DISPATCH_ACTIONS is a 5-tuple with the correct values
def test_dispatch_actions_constant():
    assert isinstance(DISPATCH_ACTIONS, tuple)
    assert len(DISPATCH_ACTIONS) == 5
    assert DISPATCH_ACTIONS == (
        "armed_response",
        "patrol",
        "operator_review",
        "auto_suppress",
        "request_data",
    )


# Test 6: "dispatch" is NOT in OUTPUT_SCHEMA["required"]
def test_dispatch_not_in_output_schema_required():
    assert "dispatch" not in OUTPUT_SCHEMA["required"]


# Test 7: _META_SCHEMA_V2 has optimal_dispatch with enum matching DISPATCH_ACTIONS
def test_meta_schema_optimal_dispatch():
    assert "optimal_dispatch" in _META_SCHEMA_V2["properties"]
    prop = _META_SCHEMA_V2["properties"]["optimal_dispatch"]
    assert prop["type"] == "string"
    assert tuple(prop["enum"]) == DISPATCH_ACTIONS


# Test 8: _META_SCHEMA_V2 has adversarial_type with ["string", "null"] type
def test_meta_schema_adversarial_type():
    assert "adversarial_type" in _META_SCHEMA_V2["properties"]
    prop = _META_SCHEMA_V2["properties"]["adversarial_type"]
    assert prop["type"] == ["string", "null"]
    assert None in prop["enum"]


# Test 9: "v4" is in the generation_version enum
def test_meta_schema_generation_version_v4():
    gen_version_enum = _META_SCHEMA_V2["properties"]["generation_version"]["enum"]
    assert "v4" in gen_version_enum


# Test 10: "v4" is NOT in _META_SCHEMA_V2["required"]
def test_generation_version_not_required():
    assert "generation_version" not in _META_SCHEMA_V2.get("required", [])
