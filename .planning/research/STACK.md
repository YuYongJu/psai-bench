# Technology Stack — v3.0 Visual Track Additions

**Project:** PSAI-Bench v3.0 (Perception-Reasoning Gap milestone)
**Researched:** 2026-04-13
**Scope:** Stack additions for visual-only scenarios, contradictory scenarios, temporal sequences, frame extraction baseline

---

## Critical Framing

PSAI-Bench generates scenarios and scores outputs. It does NOT process video in its main path. The evaluated system (user-provided) processes video. This shapes every dependency decision below:

- **Visual-only scenarios, contradictory scenarios, temporal alert sequences:** Zero new dependencies. All three are generator code additions — new fields in alert dicts, new distributions data, new scoring partitions. Existing numpy handles everything.
- **Frame extraction baseline:** The only feature that touches actual video bytes. Must be an optional dependency group, not a core requirement.
- **Scoring updates for new tracks:** Pure numpy/scipy. No new libraries.

The existing constraint from PROJECT.md — "No new dependencies unless strictly needed for scenario generation" — holds for three of four features. Frame extraction is a baseline, not generation. It gets its own install group.

---

## What Is Already Sufficient (Do Not Change)

| Library | Current Pin | Covers |
|---------|-------------|--------|
| numpy >= 1.24 | core dep | All new generators, scoring partitions, temporal sequence math |
| click >= 8.0 | core dep | CLI extensions for new generator subcommands |
| jsonschema >= 4.0 | core dep | Schema validation for new alert dict fields (additive only) |
| anthropic >= 0.40 | `[api]` optional | Vision LLM image description calls in frame extraction baseline |
| openai >= 1.0 | `[api]` optional | Vision LLM image description calls in frame extraction baseline |
| google-genai >= 1.0 | `[api]` optional | Vision LLM image description calls in frame extraction baseline |

The `[api]` optional group already covers the vision LLM calls needed for the frame extraction baseline (extract keyframe → base64-encode → pass to vision API → get scene description → score as metadata). No additions to that group.

---

## New Optional Dependency: Frame Extraction Baseline

### Decision: opencv-python-headless >= 4.10

**Current version:** 4.13.0.92 (released 2026-02-05, actively maintained by opencv org)

**Add to:** New `[visual]` optional dependency group in pyproject.toml

```toml
[project.optional-dependencies]
visual = [
    "opencv-python-headless>=4.10",
]
```

**Install for frame extraction baseline:**
```bash
pip install "psai-bench[visual,api]"
```

### Why opencv-python-headless

**Rejected: decord (dmlc/decord)**
Last PyPI release: 0.6.0, June 14, 2021. Maintenance marked inactive (Snyk package health). 198 open GitHub issues with no recent resolution. Confirmed does not publish wheels for Python 3.12+. The CI matrix already targets Python 3.10/3.11/3.12 — decord breaks this immediately.

**Rejected: decord2 (active fork)**
Releases through April 2026, but single-maintainer fork of an abandoned upstream. Inappropriate for a reproducibility-focused benchmark that must be installable across Python versions without build-time failures.

**Rejected: ffmpeg via subprocess**
Requires the `ffmpeg` system binary. Cannot be declared as a pip dependency — `pip install psai-bench[visual]` would silently miss it. Breaks portability across contributor machines and CI. A hidden system dependency is worse than a heavier Python wheel.

**opencv-python-headless rationale:**
- Ships its own ffmpeg (LGPL wheel), no system binaries needed
- Pre-built wheels for Python 3.7–3.13 confirmed on PyPI as of 2026-02-05
- The `-headless` variant has no X11/GUI dependencies — correct for server/CI use
- `VideoCapture` is sufficient for uniform-interval keyframe sampling (the correct baseline design — sample every N seconds, not semantically)
- Actively maintained under the official opencv organization

**What it does in the baseline:**

```python
import cv2, base64

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
interval_frames = int(fps * keyframe_interval_sec)  # e.g., every 5 seconds

frames = []
frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % interval_frames == 0:
        _, buf = cv2.imencode(".jpg", frame)
        frames.append(base64.b64encode(buf).decode())
    frame_idx += 1
cap.release()
# frames -> vision LLM via existing [api] group -> description -> metadata-track scorer
```

---

## Generator Extensions — No New Libraries

All three new scenario types are implemented as additions to `generators.py` and `distributions.py`. Existing numpy RNG and dict construction handle all logic.

### Visual-Only Scenarios

New generator method (`generate_visual_only`) or flag on existing `VisualGenerator`. Alert dict changes:

```python
s["track"] = "visual_only"  # new track value
s["visual_data"]["visual_only"] = True  # new flag on existing dict
s["visual_data"]["stripped_fields"] = ["description", "severity", "zone"]

# Sentinel values to catch accidental metadata use
s["description"] = "NO_DESCRIPTION_VISUAL_ONLY_TRACK"
s["severity"] = "UNSET"
s["zone"]["type"] = "UNSET"
s["zone"]["sensitivity"] = -1
```

Ground truth uses the same `assign_ground_truth_v2` from `distributions.py`, driven by video content signals stored in `_meta`. The test system must read the video; the scoring system reads `_meta.ground_truth` as always.

### Contradictory Scenarios

Extension of existing adversarial injection. The contradiction is declared at generation time — no runtime video parsing.

New data in `distributions.py`:
- `CONTRADICTION_PAIRS`: list of `(metadata_description, video_scene_label, correct_verdict)` tuples. Plain Python list.
- `VIDEO_SCENE_DESCRIPTIONS`: pool of video-content descriptions for the contradiction field. Plain Python list.

New `_meta` fields:
```python
"_meta": {
    ...
    "contradiction_type": "video_overrides_metadata",
    "declared_contradiction": {
        "metadata_signal": "routine_activity",
        "video_signal": "fence_cutting",
        "correct_source": "video",
    },
    "generation_version": "v3",
}
```

### Temporal Alert Sequences

Groups of 3–5 alerts sharing a `sequence_id`. Each alert is a normal alert dict with additional `_meta` fields. Timestamps are generated using existing `_generate_timestamp` with constrained offsets (5–15 minute gaps between sequence members, using existing numpy RNG).

New `_meta` fields:
```python
"sequence_id": "seq-00042",
"sequence_position": 2,       # 0-indexed
"sequence_length": 4,
"escalation_pattern": "rising",  # rising | falling | spike | stable
```

`sequence_id` is the grouping key for both generation and scoring. No new data structures beyond the fields above.

---

## Scoring Extensions — No New Libraries

Three new partitions added to `scorer.py`, all using existing numpy array operations:

| New Metric | What It Measures | Implementation Note |
|------------|-----------------|---------------------|
| `visual_only_accuracy` | Accuracy on `track == "visual_only"` scenarios | Filter by track value, pass to existing `_score_partition` |
| `contradiction_override_rate` | Fraction of contradictory scenarios where system chose the video-correct verdict | Read `_meta.declared_contradiction.correct_source`, compare to prediction |
| `temporal_coherence_score` | Fraction of sequences where escalation verdicts match declared `escalation_pattern` | Group by `sequence_id`, check verdict ordering within each group |

`ScoreReport` dataclass: three new float fields (backward-compatible via Python dataclass defaults). `format_dashboard` gets three new display lines. No existing fields change — all v1/v2 tests remain valid.

---

## Schema Changes — No New Libraries

All changes are additive. jsonschema handles them via `additionalProperties: false` relaxation on optional object keys (or `additionalProperties: true` in existing schema — check `schema.py`).

New optional fields:
- `visual_data.visual_only` (boolean)
- `visual_data.stripped_fields` (array of strings)
- `_meta.sequence_id` (string)
- `_meta.sequence_position` (integer)
- `_meta.sequence_length` (integer)
- `_meta.escalation_pattern` (string, enum: rising/falling/spike/stable)
- `_meta.contradiction_type` (string, enum: video_overrides_metadata/metadata_overrides_video)
- `_meta.declared_contradiction` (object with metadata_signal, video_signal, correct_source)
- `_meta.generation_version` (string — already exists in v2 scenarios)

All `required` lists in schema.py remain unchanged. Backward-compatible with v1/v2 scenarios.

---

## What NOT to Add

| Library | Why Not |
|---------|---------|
| decord | Abandoned since 2021, no Python 3.12 wheels, 198 open issues |
| decord2 | Single-maintainer fork; portability risk across CI Python matrix |
| imageio / imageio-ffmpeg | Downloads ffmpeg binary at runtime — same hidden system dependency problem as subprocess |
| Pillow | Not needed — cv2.imencode handles frame-to-JPEG-bytes for base64 encoding |
| torch / torchvision | Massive dependency; inappropriate for a benchmark tool; not needed for uniform sampling |
| PyAV (av) | Requires system libav/libavcodec build; complex install; overkill for uniform frame sampling |
| scenedetect | Semantic keyframe detection is wrong for this baseline by design — uniform interval is the correct baseline |
| pydantic | Already using jsonschema; adding a second validation layer creates inconsistency |
| Any new LLM library | Existing `[api]` group covers anthropic + openai + google-genai for vision calls |
| scipy (new) | Already transitively available via scikit-learn; no direct import needed |

---

## Updated pyproject.toml (v3.0 diff)

```toml
# Add new optional group
[project.optional-dependencies]
visual = [
    "opencv-python-headless>=4.10",
]

# Existing groups unchanged:
# dev = [pytest>=7.0, pytest-cov>=4.0, ruff>=0.8]
# api = [anthropic>=0.40, openai>=1.0, google-genai>=1.0]
```

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| "No new deps for generators/scoring" | HIGH | Verifiable directly from existing codebase — all logic is dict manipulation and numpy operations |
| opencv-python-headless choice | HIGH | PyPI confirms 4.13.0.92 released 2026-02-05; actively maintained; correct for headless server use |
| decord original abandonment | HIGH | Last PyPI release June 2021 confirmed; Snyk marks maintenance inactive |
| decord2 instability | MEDIUM | Active on PyPI through April 2026 but single-maintainer fork; portability risk not worth taking |
| ffmpeg subprocess rejection | HIGH | System binary requirement breaks portable pip install — confirmed problem for cross-platform CI |
| Scoring extensions in pure numpy | HIGH | All proposed metrics are array slicing and partitioning; existing `_score_partition` pattern already handles this |
| Schema additive compatibility | HIGH | Python dataclass field defaults provide backward compat; confirmed by existing v1→v2 migration pattern |

---

## Sources

- [opencv-python-headless PyPI](https://pypi.org/project/opencv-python-headless/) — version 4.13.0.92, released 2026-02-05
- [decord PyPI](https://pypi.org/project/decord/) — version 0.6.0, last released June 2021
- [Snyk decord health](https://snyk.io/advisor/python/decord) — maintenance status: Inactive
- [decord GitHub](https://github.com/dmlc/decord) — 198 open issues; no recent releases
- [decord2 PyPI](https://pypi.org/project/decord2/) — active fork, v3.3.0 released April 2026
- [Towards Data Science: Lightning Fast Video Reading](https://towardsdatascience.com/lightning-fast-video-reading-in-python-c1438771c4e6/) — performance comparison confirming decord speed advantage (moot given maintenance status)

---
*Stack research for: PSAI-Bench v3.0 visual track additions*
*Researched: 2026-04-13*
