# PSAI-Bench Evaluation Protocol

Version: v4.0 — Adds dispatch scoring, cost model, multi-site generalization, and adversarial v4 (Phases 18-22)

---

## 1. Overview

PSAI-Bench evaluates AI systems on physical security alert triage across four tracks.
Each track tests a different information regime: metadata signals only, video content
only, video that contradicts metadata, and multi-alert temporal sequences.

### The Four Tracks

| Track | `track` field | Generator class | GT derivation |
|---|---|---|---|
| Metadata | `metadata` | `MetadataGenerator` | `assign_ground_truth_v2()` weighted sum |
| Visual-Only | `visual_only` | `VisualOnlyGenerator` | `UCF_CATEGORY_MAP[category]["ground_truth"]` directly |
| Visual-Contradictory | `visual_contradictory` | `ContradictoryGenerator` | `_meta.video_derived_gt` (always video, never metadata) |
| Temporal | `temporal` | `TemporalSequenceGenerator` | Per-alert `assign_ground_truth_v2()` on varying signals |

### Core Research Question

Does video perception add value over metadata-only triage for physical security AI?
The perception-reasoning gap (see Section 8) quantifies this difference across models.

### How GT Fields Are Used

All scenarios contain a `_meta` dict that is benchmark-side only. **`_meta` fields
are never sent to evaluated systems.** The `_meta.ground_truth` field is the final
ground truth used for scoring. Additional `_meta` fields like `video_derived_gt`,
`metadata_derived_gt`, `sequence_id`, and `ambiguity_flag` are used by the scoring
infrastructure only.

### Signal Visibility Rules

For the metadata track, all context signals (`zone`, `device`, `severity`, `description`,
`context`) are present. For the visual-only track, `severity` and `description` fields
are intentionally absent from the scenario dict — the evaluated system must reason
from video content and remaining context fields. For the temporal track, signals vary
alert-by-alert within a sequence.

---

## 2. Track 1: Metadata Track

### GT Derivation

Ground truth is assigned by `assign_ground_truth_v2()` in `psai_bench/distributions.py`.
This function takes five signals from the scenario dict, converts each to a numeric
score, sums them, and applies thresholds.

**Cross-reference:** [docs/decision-rubric.md](decision-rubric.md) contains the
complete signal scoring tables, threshold values, and worked examples for the
`assign_ground_truth_v2()` function. This document does not duplicate those tables —
the rubric is the canonical reference for metadata GT derivation.

### The Five Signals

| # | Signal | Source field |
|---|--------|-------------|
| 1 | Zone type & sensitivity | `alert.zone.type`, `alert.zone.sensitivity` |
| 2 | Time of day | `alert.context.time_of_day` |
| 3 | Device false positive rate | `alert.device.false_positive_rate` |
| 4 | Alert severity | `alert.severity` |
| 5 | Badge access recency | `alert.context.recent_badge_access_1h[*].minutes_ago` |

**Important:** Description text (`alert.description`) is NOT an input to GT derivation.
The same description string can appear in scenarios labeled THREAT, SUSPICIOUS, or BENIGN
depending on the five signals above. Systems that rely on description wording will
produce systematically wrong labels.

### Scoring Function

```python
from psai_bench.scorer import score_run
report = score_run(scenarios, outputs)  # → ScoreReport
```

Scored per-alert. Each output dict must have `alert_id`, `verdict` (THREAT/SUSPICIOUS/BENIGN),
and `confidence` (0.0–1.0). Scenarios with `_meta.ambiguity_flag=True` are partitioned
into `report.ambiguous_report` and excluded from the main aggregate.

### Worked Example: One THREAT Case

**Inputs:**
- Zone: `restricted`, sensitivity = 5
- Time: `night`
- Device FPR: 0.10
- Severity: `LOW`
- Badge: none

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | +0.40 × (0.6 + 4×0.2) = +0.40 × 1.40 | +0.5600 |
| Time | night | +0.3500 |
| FPR | 0.15 − (0.10 × 0.4444) | +0.1056 |
| Severity | LOW | -0.2000 |
| Badge | no badge data | 0.0000 |
| **Total** | | **+0.8156** |

`+0.8156 > +0.30` → **GT = THREAT**

Interpretation: Someone is in a restricted zone at night, captured by a reliable camera
(low FPR), with no badge scan on record. The LOW severity label is overridden by the
strong zone + time + device reliability signals.

### Worked Example: One BENIGN Case

**Inputs:**
- Zone: `parking`, sensitivity = 1
- Time: `day`
- Device FPR: 0.90
- Severity: `CRITICAL`
- Badge: 3 minutes ago

| Signal | Calculation | Score |
|--------|-------------|-------|
| Zone | -0.15 × (0.6 + 0×0.2) = -0.15 × 0.60 | -0.0900 |
| Time | day | -0.2000 |
| FPR | 0.15 − (0.90 × 0.4444) | -0.2500 |
| Severity | CRITICAL | +0.2500 |
| Badge | 3 min ≤ 10 min → | -0.4500 |
| **Total** | | **-0.7400** |

`-0.74 < -0.30` → **GT = BENIGN**

Interpretation: A known employee badged in 3 minutes ago at a low-sensitivity parking
camera with a 90% false positive rate during daytime. The CRITICAL severity from the
analytics engine is not credible — the badge access and unreliable device overwhelm it.

---

## 3. Track 2: Visual-Only Track

### GT Derivation

Ground truth is derived directly from the UCF Crime category label, bypassing the
weighted-sum function entirely:

```python
gt = UCF_CATEGORY_MAP[category]["ground_truth"]
```

The `_meta.visual_gt_source` field is always `"video_category"` on every visual-only
scenario, confirming the derivation source.

### What the Evaluated System Sees

The evaluated system receives `visual_data.uri` in the format
`"ucf-crime/test/{category}/{index:05d}.mp4"`. No `severity` or `description` field
is present in the scenario dict (they are intentionally omitted — see `VIS-01`, `VIS-04`
in the generator code). Metadata fields `zone`, `device`, `context.time_of_day`,
`context.weather`, and `context.site_type` are present for contextual grounding but
are not used for GT assignment.

### Leakage Constraint

Description and severity are absent so that no single text field reveals GT. A metadata-only
system reading only text cannot determine the correct label for this track. The video URI
encodes the category, but the evaluated system must reason from visual content (frames)
to produce a verdict.

### UCF Crime Category → Ground Truth Mapping

| UCF Category | Ground Truth |
|---|---|
| Abuse | THREAT |
| Arrest | SUSPICIOUS |
| Arson | THREAT |
| Assault | THREAT |
| Burglary | THREAT |
| Explosion | THREAT |
| Fighting | THREAT |
| Normal | BENIGN |
| RoadAccidents | SUSPICIOUS |
| Robbery | THREAT |
| Shooting | THREAT |
| Shoplifting | SUSPICIOUS |
| Stealing | THREAT |
| Vandalism | THREAT |

10 THREAT categories, 3 SUSPICIOUS categories, 1 BENIGN category.

### Scoring Function

```python
from psai_bench.scorer import score_run
report = score_run(scenarios, outputs)  # → ScoreReport (same as metadata track)
```

Scored per-alert against `_meta.ground_truth`, which equals the category's
`UCF_CATEGORY_MAP` value.

### Worked Example: Visual-Only Scenario

```python
{
    "alert_id": "ucf-visual-only-00042",
    "timestamp": "2026-03-15T02:14:33+00:00",
    "track": "visual_only",
    # severity and description fields are absent
    "source_type": "camera",
    "zone": {"type": "restricted", "sensitivity": 4, "operating_hours": "24/7", ...},
    "device": {"false_positive_rate": 0.28, ...},
    "context": {
        "time_of_day": "night",
        "site_type": "industrial",
        ...
    },
    "visual_data": {
        "type": "video_clip",
        "uri": "ucf-crime/test/Arson/00042.mp4",
        "duration_sec": 47.3,
        "resolution": "1280x720",
        "keyframe_uris": []
    },
    "_meta": {
        "ground_truth": "THREAT",      # from UCF_CATEGORY_MAP["Arson"]["ground_truth"]
        "visual_gt_source": "video_category",
        "source_category": "Arson",
        "ambiguity_flag": False,
        "generation_version": "v3",
        ...
    }
}
```

GT determination: the category is `Arson`. `UCF_CATEGORY_MAP["Arson"]["ground_truth"]`
is `"THREAT"`. No weighted sum is computed. The zone, device, and time context do not
influence the label.

---

## 4. Track 3: Visual-Contradictory Track

### GT Derivation

**Ground truth always equals `_meta.video_derived_gt`, never `_meta.metadata_derived_gt`.**
The `_meta.contradictory` field is `True` on every scenario in this track.

A correct system must ignore the misleading metadata signals and reason from video content.
A metadata-only system will produce wrong verdicts on this track by design.

### Two Sub-types

**Overreach:** Metadata signals → THREAT, video content → BENIGN

- `_meta.video_derived_gt = "BENIGN"` (category: `Normal`)
- `_meta.metadata_derived_gt = "THREAT"` (or SUSPICIOUS)
- Context bias: `zone.type` in `{restricted, utility}`, `zone.sensitivity` in [4, 5],
  `time_of_day` in `{night, dawn}`, `severity` in `{HIGH, CRITICAL}`, no badge scan,
  device FPR ~0.85 (low_quality profile — a high false-positive rate device, but the
  strong zone+time+severity signals push the metadata sum above the THREAT threshold)
- Description drawn from `CONTRADICTORY_THREAT_DESCRIPTIONS` pool

**Underreach:** Metadata signals → BENIGN, video content → THREAT

- `_meta.video_derived_gt = "THREAT"` (an anomaly UCF category, e.g., Assault, Robbery)
- `_meta.metadata_derived_gt = "BENIGN"` (or SUSPICIOUS)
- Context bias: `zone.type` in `{parking, interior}`, `zone.sensitivity` in [1, 2],
  `time_of_day = "day"`, `severity = "LOW"`, badge scan 1–9 minutes ago,
  device FPR ~0.30 (high_quality profile)
- Description drawn from `CONTRADICTORY_BENIGN_DESCRIPTIONS` pool

**Guarantee:** The generator enforces `metadata_derived_gt != video_derived_gt` via a
retry loop of up to 10 attempts. If after 10 retries the GTs still agree, the candidate
is dropped and a new one is generated.

### Scoring Function

```python
from psai_bench.scorer import score_run
report = score_run(scenarios, outputs)  # → ScoreReport
```

GT = `_meta.video_derived_gt`. Scored per-alert.

### Worked Example: Overreach Scenario

```python
{
    "alert_id": "ucf-contradictory-00001",
    "track": "visual_contradictory",
    "severity": "HIGH",
    "description": "Perimeter breach indicator: fence disturbance sensor triggered, zone-north, 02:18",
    "zone": {"type": "restricted", "sensitivity": 5, ...},
    "device": {"false_positive_rate": 0.83, ...},
    "context": {"time_of_day": "night", ...},
    "visual_data": {
        "uri": "ucf-crime/test/Normal/00001.mp4",   # Normal category — BENIGN video
        ...
    },
    "_meta": {
        "ground_truth": "BENIGN",           # video_derived_gt wins
        "video_derived_gt": "BENIGN",        # Normal → BENIGN
        "metadata_derived_gt": "THREAT",     # zone+time+severity → THREAT
        "contradictory": True,
        "visual_gt_source": "video_category",
        ...
    }
}
```

GT = `BENIGN`. A metadata-only system sees: restricted zone, sensitivity 5, night, HIGH
severity, no badge — and produces THREAT. The video shows normal activity. A correct system
reasons from video to produce BENIGN.

### Worked Example: Underreach Scenario

```python
{
    "alert_id": "ucf-contradictory-00002",
    "track": "visual_contradictory",
    "severity": "LOW",
    "description": "Routine motion trigger: environmental cause probable, sensor auto-reset, 14:30",
    "zone": {"type": "parking", "sensitivity": 1, ...},
    "device": {"false_positive_rate": 0.31, ...},
    "context": {"time_of_day": "day", "recent_badge_access_1h": [{"minutes_ago": 4}], ...},
    "visual_data": {
        "uri": "ucf-crime/test/Assault/00002.mp4",   # Assault category — THREAT video
        ...
    },
    "_meta": {
        "ground_truth": "THREAT",            # video_derived_gt wins
        "video_derived_gt": "THREAT",         # Assault → THREAT
        "metadata_derived_gt": "BENIGN",      # daytime + badge + parking → BENIGN
        "contradictory": True,
        "visual_gt_source": "video_category",
        ...
    }
}
```

GT = `THREAT`. A metadata-only system sees: parking zone, day, LOW severity, badge 4
minutes ago — and produces BENIGN. The video shows an assault. A correct system produces THREAT.

---

## 5. Track 4: Temporal Track

### GT Derivation

Each alert in a temporal sequence has its own GT, computed by `assign_ground_truth_v2()`
applied to that alert's individual signals. Signals vary across positions in the sequence
according to the escalation pattern — this is what creates the temporal dynamic.

The five signals (`zone_type`, `zone_sensitivity`, `time_of_day`, `device_fpr`, `severity`)
change across positions. `badge_access_minutes_ago` also changes, creating resolution events.
Each alert's `_meta.ground_truth` reflects its own computed label, not the sequence's label.

### Escalation Patterns

Three patterns are assigned round-robin (`seq_idx % 3`):

**`monotonic_escalation`** — signals escalate from low-threat to high-threat at `turn_point`:
- Positions < `turn_point`: severity in `{LOW, MEDIUM}`, zone_type in `{lobby, parking}`,
  time_of_day in `{day, evening}`, no badge scan
  (note: `lobby` and `evening` are not in the standard signal maps and score as 0.0)
- Positions ≥ `turn_point`: severity = `HIGH`, zone_type = `restricted`, time_of_day = `night`,
  no badge scan

**`escalation_then_resolution`** — escalates to peak then resolves:
- Position 1: severity = `LOW`, zone_type = `restricted`, time_of_day = `night`, no badge
- Positions 2 to `turn_point`: severity = `HIGH`, zone_type = `restricted`, time_of_day = `night`, no badge
- Positions > `turn_point`: severity = `LOW`, zone_type = `restricted`, time_of_day = `night`,
  badge scan 3–9 minutes ago (clears the threat)

**`false_alarm`** — starts with high signal, subsequent alerts resolve it:
- Position 1: severity in `{HIGH, CRITICAL}`, zone_type = `restricted`, time_of_day = `night`, no badge
- Positions 2+: severity = `LOW`, zone_type in `{parking, lobby}`, time_of_day = `day`,
  badge scan 1–7 minutes ago

### Sequence Structure

`_meta.sequence_id` (format: `"seq-NNNN"`) groups alerts into a sequence.
`_meta.sequence_position` is 1-based and monotonically increasing within each sequence.
`_meta.sequence_length` is the total count (3–5 alerts, sampled uniformly).
`_meta.escalation_pattern` stores the pattern string.

All alerts in a sequence share the same `sequence_id`. The scoring function groups
by `sequence_id`, sorts by `sequence_position`, and evaluates as a unit.

### Temporal Zone and Device Field Shape

Temporal scenarios use different dict shapes for zone and device than other tracks:

```python
# Temporal scenario zone and device fields
"zone": {
    "zone_id": "zone-0003",
    "zone_type": "restricted",    # note: zone_type, not type
    "zone_sensitivity": 4,        # note: zone_sensitivity, not sensitivity
}
"device": {
    "device_id": "cam-0003-01",
    "device_type": "high_quality",
    "fpr": 0.284,                 # note: fpr, not false_positive_rate
}
```

### Scoring Function

```python
from psai_bench.scorer import score_sequences
report = score_sequences(scenarios, outputs)  # → SequenceScoreReport
```

**Use `score_sequences`, NOT `score_run`, for temporal track.** `score_run` evaluates
alerts individually and ignores sequence structure. `score_sequences` groups alerts by
`_meta.sequence_id`, evaluates each sequence as a unit, and computes escalation metrics.

### SequenceScoreReport Fields

| Field | Definition |
|---|---|
| `n_sequences` | Total number of sequences evaluated |
| `n_threat_sequences` | Sequences containing at least one alert with GT == `THREAT` |
| `n_benign_sequences` | Sequences where all alert GTs are `BENIGN` or `SUSPICIOUS` |
| `early_detection_rate` | Fraction of threat sequences where model first returned `THREAT` at position 0 or 1 (0-indexed, i.e., alert 1 or 2) |
| `late_detection_rate` | Fraction of threat sequences where model's first `THREAT` appeared only at the last alert position |
| `missed_sequence_rate` | Fraction of threat sequences where model never returned `THREAT` on any alert |
| `false_escalation_rate` | Fraction of benign sequences where model returned `THREAT` on at least one alert |

Missing outputs (no entry in outputs file for that `alert_id`) are treated as verdict
`"MISSING"`. Scenarios without `_meta.sequence_id` in the scenarios file are silently
skipped — mixed-track files are allowed.

### Worked Example: Monotonic Escalation Sequence

A 4-alert `monotonic_escalation` sequence with `turn_point = 3`, device FPR = 0.60:

| Pos | severity | zone_type | time_of_day | badge | GT computation | GT |
|---|---|---|---|---|---|---|
| 1 | LOW | lobby | day | none | zone=0(lobby→0.0)×factor + time=-0.20 + fpr≈-0.12 + sev=-0.20 + badge=0 ≈ -0.52 | BENIGN |
| 2 | MEDIUM | parking | evening | none | zone=-0.15×0.60 + time=0.0(evening→0.0) + fpr≈-0.12 + sev=0.00 + badge=0 ≈ -0.21 | SUSPICIOUS |
| 3 | HIGH | restricted | night | none | zone=+0.40×1.00 + time=+0.35 + fpr≈-0.12 + sev=+0.15 + badge=0 ≈ +0.78 | THREAT |
| 4 | HIGH | restricted | night | none | same as pos 3 ≈ +0.78 | THREAT |

This is a threat sequence (`n_threat_sequences` += 1). The threat first appears at position 3
(0-indexed: index 2, which is > 1), so it is neither early nor late if the sequence has
length 4 (last index = 3) — it's a middle detection.

**Model output A** (early detection): `["THREAT", "THREAT", "THREAT", "THREAT"]`
→ first THREAT at index 0 → `early_detection_rate` contribution.

**Model output B** (missed): `["BENIGN", "SUSPICIOUS", "SUSPICIOUS", "SUSPICIOUS"]`
→ no THREAT verdict → `missed_sequence_rate` contribution.

---

## 6. Scoring Functions Reference

### score_run — Individual Alert Scoring

Used for: **metadata**, **visual_only**, **visual_contradictory** tracks.

```python
from psai_bench.scorer import score_run
report: ScoreReport = score_run(scenarios, outputs)
```

**Inputs:**
- `scenarios`: list of scenario dicts with `_meta.ground_truth`, `_meta.difficulty`,
  `_meta.source_dataset`, and optionally `_meta.ambiguity_flag`
- `outputs`: list of dicts `{"alert_id": str, "verdict": str, "confidence": float, ...}`

**Outputs:** `ScoreReport` with:

| Field | Definition |
|---|---|
| `tdr` | Threat Detection Rate: fraction of THREAT scenarios predicted as THREAT or SUSPICIOUS |
| `fasr` | False Alarm Suppression Rate: fraction of BENIGN scenarios predicted as BENIGN |
| `decisiveness` | Fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS) |
| `ece` | Expected Calibration Error (equal-width bins, lower is better) |
| `aggregate_score` | `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` |
| `accuracy` | 3-class accuracy (exact match) |
| `n_scenarios` | Total scenarios scored |
| `n_threats` | Count of THREAT GT scenarios |
| `n_benign` | Count of BENIGN GT scenarios |
| `n_ambiguous` | Count of scenarios with `ambiguity_flag=True` (excluded from main aggregate) |
| `ambiguous_report` | Nested `ScoreReport` for the ambiguous partition (or `None`) |

**Ambiguous partition:** Scenarios with `_meta.ambiguity_flag=True` are scored
separately in `report.ambiguous_report` and excluded from the main aggregate. This
prevents "gameable" scenarios from inflating or deflating main metrics.

**Missing outputs:** Any scenario without a matching `alert_id` in outputs is scored as
incorrect with confidence=0. A system cannot game the benchmark by skipping hard scenarios.

### score_sequences — Sequence-Level Scoring

Used for: **temporal** track only.

```python
from psai_bench.scorer import score_sequences
report: SequenceScoreReport = score_sequences(scenarios, outputs)
```

Same input format as `score_run`. Scenarios without `_meta.sequence_id` are silently skipped.
Groups by `sequence_id`, sorts by `sequence_position`, evaluates each sequence as a unit.
See Section 5 for field definitions.

### Aggregate Score Formula

```
aggregate_score = 0.4 * TDR + 0.3 * FASR + 0.2 * Decisiveness + 0.1 * (1 - ECE)
```

This is the primary single-number ranking metric. TDR is weighted heaviest (safety-critical:
missing a real threat is the worst error). FASR is second (false alarm fatigue erodes trust).
Decisiveness rewards systems that commit to a verdict rather than defaulting to SUSPICIOUS.
ECE penalizes miscalibrated confidence scores.

Note: The older `suspicious_penalty` and `calibration_factor` fields are retained in
`ScoreReport` for backward compatibility but are set to 0.0 in the current formula.

### Mixed-Track Files

When a single file contains scenarios from multiple tracks, use `partition_by_track()`
to split, then score each partition separately:

```python
from psai_bench.scorer import partition_by_track, score_run, format_dashboard

partitions = partition_by_track(scenarios)
track_reports = {}
for track_name, track_scenarios in partitions.items():
    if track_name == "temporal":
        continue  # use score_sequences separately
    track_reports[track_name] = score_run(track_scenarios, outputs)

combined_report = score_run(scenarios, outputs)
dashboard = format_dashboard(combined_report, track_reports=track_reports)
print(dashboard)
```

`format_dashboard()` renders a gap preview when both `metadata` and `visual_only` (or
`visual_contradictory`) tracks are present in `track_reports`.

---

## 7. Frame Extraction Baseline

### Purpose

Establish the visual-only baseline: what performance does uniform frame sampling achieve
when used as the visual input to a model? This baseline is intentionally simple — it
uses no anomaly metadata, no learned sampling, no adaptive selection.

### Function

```python
from psai_bench.frame_extraction import extract_keyframes

frames: list[bytes] = extract_keyframes(
    video_path="ucf-crime/test/Arson/00042.mp4",
    keyframe_interval_sec=5.0,   # default
    max_frames=50,               # default
)
```

**Install:** `pip install "psai-bench[visual]"` (adds `opencv-python-headless` optional dep)

**Returns:** list of JPEG-encoded bytes (not base64). Callers encode to base64 if needed
for model API payloads:

```python
import base64
b64_frames = [base64.b64encode(f).decode() for f in frames]
```

### CRITICAL Constraint: MUST NOT Use anomaly_segments

> **FRAME-02 constraint:** `extract_keyframes()` MUST NOT use `_meta.anomaly_segments`
> for frame selection. Selection is purely uniform interval (every N seconds).

This is the fairness constraint: the evaluated system and the baseline both see the same
frames regardless of whether anomaly annotations exist. Using anomaly segment boundaries
to select frames would constitute information leakage and invalidate any comparison.

The `extract_keyframes()` function receives only `video_path`, `keyframe_interval_sec`,
and `max_frames`. It has no access to `_meta` fields.

### Parameters

| Parameter | Type | Default | Effect |
|---|---|---|---|
| `video_path` | str | required | Local path or URL readable by OpenCV |
| `keyframe_interval_sec` | float | 5.0 | Seconds between sampled frames |
| `max_frames` | int | 50 | Hard cap on returned frames (prevents memory issues on long videos) |

### Determinism

Given the same video file and parameters, output is identical across runs. The function
uses OpenCV's `cv2.VideoCapture` with `CAP_PROP_FPS` for interval calculation. Frames
are selected at `frame_idx % interval_frames == 0` in order.

### Typical Workflow

```python
# 1. Extract frames
frames = extract_keyframes(video_path, keyframe_interval_sec=5.0, max_frames=50)

# 2. Encode for API
b64_frames = [base64.b64encode(f).decode() for f in frames]

# 3. Send to model API with prompt and visual_only scenario context
verdict = call_model_api(prompt=prompt, images=b64_frames)

# 4. Collect output dict
output = {"alert_id": scenario["alert_id"], "verdict": verdict, "confidence": 0.85}
```

---

## 8. Cross-Track Gap Analysis (Perception-Reasoning Gap)

### Formula

```
gap = metadata_aggregate_score − visual_aggregate_score
```

Implemented in:

```python
from psai_bench.scorer import compute_perception_gap

gap: float = compute_perception_gap(metadata_report, visual_report)
```

Both arguments are `ScoreReport` objects from `score_run()`. Both must have
`n_scenarios > 0` (raises `ValueError` otherwise).

### Interpretation

| Gap value | Meaning |
|---|---|
| gap > +0.02 | Metadata context helps — video perception alone is insufficient for this model |
| gap < -0.02 | Visual track outperforms — model benefits from seeing video |
| −0.02 ≤ gap ≤ +0.02 | Negligible difference |

A large positive gap indicates the model is metadata-dependent: it performs well when
context signals (zone, time, severity) are available but struggles from video alone. A
negative gap would be unusual and indicates the video provides stronger signal than the
metadata context for this model.

### CLI

```bash
psai-bench analyze-frame-gap \
  --metadata-results  results/model_metadata.json \
  --visual-results    results/model_visual.json \
  --metadata-scenarios data/generated/metadata_scenarios.json \
  --visual-scenarios   data/generated/visual_only_scenarios.json
```

This command loads both results files, calls `score_run()` on each, calls
`compute_perception_gap()`, and prints:

```
=== Perception-Reasoning Gap Analysis ===
  Metadata aggregate score: 0.6823  (N=500)
  Visual aggregate score:   0.4417  (N=500)
  Gap (metadata - visual):  +0.2406

  Interpretation: Metadata context boosts aggregate by 24.1% — video perception alone is insufficient.
```

### Which Track to Use for the Visual Side

Use `visual_only` or `visual_contradictory` — not the legacy `visual` track (which has
both metadata and video content, making the comparison invalid). The `analyze-frame-gap`
command does not enforce this; the researcher must ensure the correct scenario files are
passed.

### Dashboard Preview

When `format_dashboard()` is called with `track_reports` containing both `metadata` and
`visual_only` (or `visual_contradictory`), a gap preview is rendered:

```
=== Perception-Reasoning Gap (Preview) ===
  Gap (metadata aggregate - visual_only aggregate): +0.2406
  Note: compute full gap analysis with `analyze-frame-gap` command (Phase 16)
```

---

## 9. CLI Quick Reference

### Generate Scenarios

```bash
# Metadata track — UCF Crime categories, 3000 scenarios
psai-bench generate --track metadata --source ucf --n 3000 --seed 42

# Metadata track — Caltech Camera Traps, 5000 scenarios
psai-bench generate --track metadata --source caltech --n 5000 --seed 42

# Visual-only track (VisualOnlyGenerator)
psai-bench generate --track visual_only --n 500 --seed 42

# Visual-contradictory track (ContradictoryGenerator)
psai-bench generate --track visual_contradictory --n 500 --seed 42

# Temporal track (n = number of sequences, not alerts)
# Each sequence is 3–5 alerts, so output has 3n–5n total alerts
psai-bench generate --track temporal --n 50 --seed 42
```

### Score Results

```bash
# Individual-alert scoring (metadata, visual_only, visual_contradictory)
psai-bench score \
  --scenarios data/generated/scenarios.json \
  --outputs   results/model_outputs.json

# Temporal sequence scoring (temporal track)
psai-bench score-sequences \
  --scenarios data/generated/temporal_scenarios.json \
  --outputs   results/model_outputs.json
```

### Gap Analysis

```bash
# Perception-reasoning gap between metadata and visual track
psai-bench analyze-frame-gap \
  --metadata-results    results/model_metadata.json \
  --visual-results      results/model_visual.json \
  --metadata-scenarios  data/generated/metadata_scenarios.json \
  --visual-scenarios    data/generated/visual_only_scenarios.json
```

### Output Format

`score` and `score-sequences` accept `--format json` or `--format table` (default: `table`).
Output files from `generate` are written to `data/generated/` by default.

---

## 10. Reproducibility

### Seed Guarantees

All generators use `np.random.RandomState(seed)`. Same seed = identical output.
Default seed is 42 for all generators.

```python
gen = MetadataGenerator(seed=42)
scenarios_a = gen.generate_ucf_crime(n=3000)

gen2 = MetadataGenerator(seed=42)
scenarios_b = gen2.generate_ucf_crime(n=3000)

assert scenarios_a == scenarios_b  # always true
```

### RNG Isolation

Each generator class owns its own `np.random.RandomState`. RNG state is never shared
between `MetadataGenerator`, `VisualOnlyGenerator`, `ContradictoryGenerator`, and
`TemporalSequenceGenerator`. This means generating 500 visual-only scenarios does not
affect the sequence of random draws in the metadata generator.

```python
# Safe: each generator is independent
meta_gen = MetadataGenerator(seed=42)
visual_gen = VisualOnlyGenerator(seed=42)
contra_gen = ContradictoryGenerator(seed=42)
temporal_gen = TemporalSequenceGenerator(seed=42)
```

### Generation Version

`_meta.generation_version` records which generator version produced the scenario:
- `"v1"`: original metadata generator
- `"v2"`: metadata generator with `assign_ground_truth_v2()` and adversarial injection
- `"v3"`: visual-only, visual-contradictory, and temporal generators (Phases 11-14)
- `"v4"`: adversarial v4 behavioral scenarios (Phase 20)

When comparing systems across papers or runs, ensure the same generation version and
seed are used. Version differences may change GT labels for the same scenario index.

### Submission Verification

Before submitting outputs, validate scenario and output files:

```bash
psai-bench validate-scenarios --scenarios data/generated/scenarios.json
psai-bench validate-submission --scenarios data/generated/scenarios.json \
                               --outputs results/model_outputs.json
```

These commands check schema compliance, alert_id coverage, and verdict value validity
before scoring begins.

---

## 11. Track 5: Adversarial v4 Behavioral Track

### Overview

The adversarial v4 track tests systems against behavioral deception: scenarios where
ground truth is determined by context signals as usual, but the description text is
crafted to suggest a different verdict. Unlike v2 adversarials (signal_conflict), v4
adversarials use naturalistic behavioral framing — an authorized person described as
suspicious, an animal described as human movement.

### Adversarial Types

| `_meta.adversarial_type` | Pattern | GT derivation |
|--------------------------|---------|---------------|
| `loitering_as_waiting`   | Subject in restricted zone described as waiting for a pickup | From zone+time+device signals |
| `authorized_as_intrusion`| Authorized personnel described as an intruder | From badge access recency |
| `environmental_as_human` | Animal or environmental trigger described as human activity | From device FPR + zone type |

**Key invariant:** `_meta.adversarial_type` is `signal_conflict` for v2/v3 scenarios
and one of the three behavioral types for v4. They must not be mixed.

### GT Derivation

Ground truth is assigned by `assign_ground_truth_v2()` on the actual context signals.
The description narrative is deceptive — the GT is always from context, not narrative.

### Schema Fields

Every adversarial v4 scenario has:

```python
{
    "track": "adversarial_v4",
    "_meta": {
        "ground_truth": "THREAT" | "SUSPICIOUS" | "BENIGN",
        "adversarial": True,
        "adversarial_type": "loitering_as_waiting" | "authorized_as_intrusion" | "environmental_as_human",
        "generation_version": "v4",
        ...
    }
}
```

### Scoring

Scored with `score_run()`. No special scoring function — behavioral adversarials test
whether the model uses context signals or falls for the deceptive narrative.

```python
from psai_bench.scorer import score_run
report = score_run(scenarios, outputs)
```

### CLI

```bash
psai-bench generate --track adversarial_v4 --n 100 --seed 42 --output data/generated/
```

RNG isolation: `AdversarialV4Generator` owns its own `np.random.RandomState`. Generating
adversarial v4 scenarios does not affect the RNG stream of any other generator.

---

## 12. Dispatch Scoring and Cost Model

### Overview

v4.0 adds optional dispatch scoring alongside the existing triage metrics. Systems that
output a `dispatch` field in their results can be scored for operational cost-effectiveness.
Dispatch scoring is additive — `score_run()` is unchanged and triage metrics are unaffected.

The dispatch field accepts one of five actions:

| Action | When to use |
|--------|-------------|
| `armed_response` | Confirmed threat at high-value or critical site |
| `patrol` | Probable threat or high-sensitivity SUSPICIOUS event |
| `operator_review` | Uncertain; needs human review |
| `auto_suppress` | Reliable false alarm; safe to dismiss |
| `request_data` | Borderline benign; gather more data before deciding |

### Output Format

System outputs must include `dispatch` alongside `verdict`:

```json
{
    "alert_id": "ucf-meta-00042",
    "verdict": "THREAT",
    "dispatch": "armed_response",
    "confidence": 0.91,
    "reasoning": "...",
    "processing_time_ms": 340
}
```

The `dispatch` field is optional for backward compatibility — outputs without it are
counted in `n_missing_dispatch` and excluded from cost scoring.

### Scoring Function

```python
from psai_bench.scorer import score_dispatch_run
from psai_bench.cost_model import CostModel

# With default cost profile
cost_report = score_dispatch_run(scenarios, outputs)

# With custom cost profile
custom_model = CostModel(
    costs={(action, gt): cost for ...},  # override DISPATCH_COSTS
    site_multipliers={"substation": 10.0, ...},  # override threat multipliers
)
cost_report = score_dispatch_run(scenarios, outputs, model=custom_model)
```

`score_dispatch_run()` does NOT call `score_run()`. Call both independently:

```python
triage_report  = score_run(scenarios, outputs)          # → ScoreReport
dispatch_report = score_dispatch_run(scenarios, outputs) # → CostScoreReport
```

### CostScoreReport Fields

| Field | Type | Meaning |
|-------|------|---------|
| `cost_ratio` | float | submitted_cost / optimal_cost. 1.0 = optimal; higher = worse |
| `total_cost_usd` | float | Sum of effective costs for all scored scenarios |
| `optimal_cost_usd` | float | Sum of costs if optimal action was taken for each scenario |
| `mean_cost_usd` | float | total_cost_usd / n_scenarios |
| `per_action_counts` | dict | Count of each submitted dispatch action |
| `per_site_mean_cost` | dict | Mean cost broken down by site_type |
| `n_missing_dispatch` | int | Outputs without a `dispatch` field (excluded from scoring) |
| `sensitivity_profiles` | dict | Cost ratios under low/medium/high cost assumptions |

### Cost Model

Default costs are provisional benchmark assumptions defined in `psai_bench/cost_model.py`.
See `docs/dispatch-decision-rubric.md` for the full cost table and override instructions.

**Optimal dispatch** is computed by `compute_optimal_dispatch(gt, context)` from the
decision table in `docs/dispatch-decision-rubric.md`. Rules (top-to-bottom, first match wins):

- THREAT at substation/solar site → `armed_response`
- THREAT with zone sensitivity ≥ 4 → `armed_response`
- THREAT otherwise → `patrol`
- SUSPICIOUS with sensitivity ≥ 4 → `patrol`
- SUSPICIOUS otherwise → `operator_review`
- BENIGN with device FPR ≥ 0.70 → `auto_suppress`
- BENIGN with ≥ 3 recent zone events → `request_data`
- BENIGN otherwise → `auto_suppress`

### Sensitivity Analysis

`CostScoreReport.sensitivity_profiles` contains cost ratios under three assumptions:

| Profile | Description |
|---------|-------------|
| `low` | All costs × 0.5 |
| `medium` | Default costs (same as main report) |
| `high` | THREAT column costs × 2.0 (SUSPICIOUS/BENIGN unchanged) |

### Dashboard Integration

Pass `cost_report` to `format_dashboard()` to append the dispatch cost section:

```python
from psai_bench.scorer import format_dashboard, score_run, score_dispatch_run

triage = score_run(scenarios, outputs)
dispatch = score_dispatch_run(scenarios, outputs)
print(format_dashboard(triage, cost_report=dispatch))
```

Omitting `cost_report` produces output byte-identical to the v3.0 dashboard (backward compat).

### CLI

The `score` command scores triage only. To score dispatch, use Python directly:

```python
import json
from psai_bench.scorer import score_run, score_dispatch_run, format_dashboard

with open("scenarios.json") as f:
    scenarios = json.load(f)
with open("outputs.json") as f:
    outputs = json.load(f)

print(format_dashboard(score_run(scenarios, outputs), cost_report=score_dispatch_run(scenarios, outputs)))
```

---

## 13. Multi-Site Generalization

### Overview

v4.0 adds a generalization gap metric that measures how well a system trained or tuned
on one site type performs when evaluated on a different site type. A system that overfits
to substation scenarios will exhibit a large generalization gap when evaluated on campus
or commercial scenarios.

### Leakage Audit

Before using the generalization metric, confirm that site identity is not structurally
inferable from non-site features (description, category, time, weather). A logistic
regression probe trained only on non-site features to predict `site_type` must score at
or below 60% accuracy. This audit is implemented as a pytest test in `tests/test_site_leakage.py`.

Run: `pytest tests/test_site_leakage.py -v`

The audit must pass before interpreting generalization gap values. If the audit fails,
site-type information has leaked into non-site features and gap values are confounded.

### Scoring Function

```python
from psai_bench.scorer import compute_site_generalization_gap

result = compute_site_generalization_gap(
    scenarios,  # list of scenario dicts (must have context.site_type and _meta.ground_truth)
    outputs,    # list of output dicts (alert_id + verdict)
    train_site="solar",       # optional: include train_accuracy in result
    test_site="commercial",   # optional: include test_accuracy in result
)
```

**Does NOT call `score_run()`** — accuracy is computed directly from alert_id matching.
Missing outputs count as incorrect (same policy as `_score_partition`).

### Return Value

```python
{
    "per_site_accuracy": {"solar": 0.82, "commercial": 0.61, ...},
    "generalization_gap": 0.21,  # max(accs) - min(accs); 0.0 if fewer than 2 sites
    "train_site": "solar",       # echoes argument
    "test_site": "commercial",   # echoes argument
    "train_accuracy": 0.82,      # per_site_accuracy[train_site], or None if absent
    "test_accuracy": 0.61,       # per_site_accuracy[test_site], or None if absent
}
```

**Interpretation:** A `generalization_gap` below 0.10 indicates robust cross-site
generalization. Values above 0.20 indicate meaningful site-specific overfitting.

### Site-Type Filtering

Generate site-specific scenario subsets with `--site-type`:

```bash
# Generate only solar scenarios (post-generation filter, seed-safe)
psai-bench generate --track metadata --source ucf --n 300 --seed 42 --site-type solar

# Full generation (superset — same seed)
psai-bench generate --track metadata --source ucf --n 300 --seed 42
```

The filter runs after generation. The same seed produces the same full scenario set;
`--site-type` is a pure post-generation filter and does not affect the RNG stream.

### CLI Command

```bash
psai-bench site-generalization \
  --scenarios data/generated/scenarios.json \
  --outputs   results/model_outputs.json \
  --train     solar \
  --test      commercial
```

Output:
```
=== Per-Site Accuracy ===
  campus          0.7241
  commercial      0.6100
  solar           0.8200
  substation      0.7800

Generalization gap: 0.2100
Train site (solar): 0.8200
Test site  (commercial):  0.6100
```
