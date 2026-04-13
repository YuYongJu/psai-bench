"""Tests for adversarial_v4 track enum addition to ALERT_SCHEMA — Phase 20 Plan 01.

TDD: these tests are written BEFORE the implementation change.
"""

import pytest
from jsonschema import ValidationError

from psai_bench.schema import validate_alert


# Minimal valid alert skeleton used across tests.
_BASE = {
    "alert_id": "test-001",
    "timestamp": "2026-01-01T00:00:00+00:00",
    "source_type": "camera",
    "zone": {
        "id": "z1",
        "name": "North Fence",
        "type": "perimeter",
        "sensitivity": 3,
        "operating_hours": "24/7",
    },
    "device": {
        "id": "d1",
        "false_positive_rate": 0.5,
        "total_events_30d": 100,
        "model": "Generic-PTZ-2MP",
    },
    "context": {
        "recent_zone_events_1h": [],
        "weather": {},
        "time_of_day": "day",
        "expected_activities": [],
        "site_type": "solar",
    },
}


def _alert(**kwargs):
    a = dict(_BASE)
    a.update(kwargs)
    return a


# Test 1: adversarial_v4 track value is accepted by validate_alert
def test_adversarial_v4_track_accepted():
    validate_alert(_alert(track="adversarial_v4"))


# Test 2: existing v2 track "metadata" is still accepted (backward compat)
def test_metadata_track_still_accepted():
    validate_alert(_alert(track="metadata"))


# Test 3: existing v3 track "visual_contradictory" is still accepted
def test_visual_contradictory_track_still_accepted():
    validate_alert(_alert(track="visual_contradictory"))


# Test 4: unknown track value is rejected
def test_unknown_track_rejected():
    with pytest.raises(ValidationError):
        validate_alert(_alert(track="unknown_track"))
