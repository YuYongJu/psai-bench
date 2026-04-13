# Architecture Patterns

**Domain:** PSAI-Bench v3.0 -- visual-only scenarios, contradictory scenarios, temporal sequences, frame extraction baseline
**Researched:** 2026-04-13
**Confidence:** HIGH (based on direct code reading, all claims traceable to specific files)

---

## Existing Architecture -- The Stable Floor

Before describing what changes, document the floor that must not break.

| Component | File | Role |
|-----------|------|------|
| `MetadataGenerator` | generators.py | UCF Crime + Caltech scenarios; v1/v2 dispatch |
| `VisualGenerator` | generators.py | Wraps MetadataGenerator, populates visual_data |
| `MultiSensorGenerator` | generators.py | Wraps VisualGenerator, layers sensor events |
| `VisualTrackMapper` | video_mapper.py | Real UCF Crime test videos -> PSAI-Bench alerts |
| `assign_ground_truth_v2` | distributions.py | Metadata-signal-weighted GT computation |
| `score_run` / `ScoreReport` | scorer.py | Per-alert scoring, partitions ambiguous vs main |
| `_score_partition` | scorer.py | Vectorized metric computation over a flat scenario list |
| `ALERT_SCHEMA` | schema.py | jsonschema-validated input contract for scenarios |
| `OUTPUT_SCHEMA` | schema.py | jsonschema-validated output contract for systems |
| CLI commands | cli.py | generate, score, baselines, compare, evaluate, analyze_gap |

Current data flow: generator emits `list[dict]` alerts -> system under test emits `list[dict]` outputs -> `score_run()` matches by `alert_id` -> `ScoreReport`.

---

## Four Integration Points That Determine the Build

### Integration Point 1: Schema -- Visual-Only Scenarios Hit a Required-Field Wall

`ALERT_SCHEMA` (schema.py line 14-105) marks these fields as `required`: `severity` (enum, non-null), `description` (minLength: 10), `zone` (object), `device` (object), `context` (object with required subfields). Visual-only scenarios intentionally strip most of this -- that IS the test.

Two choices:

**Option A -- Schema v3 with track-aware optional fields (chosen)**

Add `"visual_only"`, `"visual_contradictory"`, `"temporal"` to the track enum. Remove `severity` and `description` from top-level `required` for these tracks. Enforce presence via track-aware logic in `validation.py` rather than schema required array.

Tradeoff: slightly more logic in validation.py, but the schema accurately represents what the data actually looks like. Systems receiving visual_only alerts will not see a deceptive `"Camera alert triggered"` description placeholder.

**Option B -- Uninformative placeholder values**

Always emit `severity: "MEDIUM"`, `description: "Camera alert triggered"`, stub zone/device. Schema unchanged.

Rejected because: (1) systems could pattern-match on the placeholder description, introducing leakage; (2) contradictory scenarios become indistinguishable from visual-only in the JSON since both would have the same stub description; (3) it is dishonest about what the scenario type is.

**Decision: Option A.** Extend the track enum, make severity/description optional at the schema level, validate presence by track in validation.py.

---

### Integration Point 2: Ground Truth Assignment Diverges by Track

There is an invisible coupling in the current architecture. `VisualGenerator.generate_ucf_crime()` calls `metadata_gen.generate_ucf_crime()` which dispatches to `generate_ucf_crime_v2()` which calls `assign_ground_truth_v2()`. That function (distributions.py) derives GT from metadata signals: zone_type, zone_sensitivity, time_of_day, device_fpr, badge_access. For visual-only and contradictory scenarios, these metadata signals are absent or intentionally false. Using `assign_ground_truth_v2` on them would produce arbitrary GT unrelated to video content.

Correct GT source by track:

| Track | GT Source | Function to Use |
|-------|-----------|-----------------|
| `metadata` (v1/v2) | Metadata signals | `assign_ground_truth_v2()` (existing) |
| `visual` (existing) | Metadata signals (metadata is present and accurate) | `assign_ground_truth_v2()` (existing) |
| `visual_only` (new) | Video content = UCF Crime category | `UCF_CATEGORY_MAP[cat]["ground_truth"]` |
| `visual_contradictory` (new) | Video content overrides metadata | `UCF_CATEGORY_MAP[cat]["ground_truth"]` |
| `temporal` (new) | Metadata signals, same as v2 | `assign_ground_truth_v2()` (existing) |

For contradictory scenarios, the ground truth is always what the video shows, not what the metadata claims. That is the test design: did the model's visual perception override its textual priors? `_meta.ground_truth` must reflect the video, `_meta.contradictory = True` signals the mismatch, and `_meta.visual_gt_source = "video_category"` documents why.

`VisualTrackMapper.generate_from_annotations()` already uses `UCF_CATEGORY_MAP[cat]["ground_truth"]` directly -- it is the correct base for visual-only and contradictory generation.

---

### Integration Point 3: Temporal Sequences Break the Flat List Assumption

Every current component assumes independent, unordered alerts. In `scorer.py`:
- `score_run` builds `output_map = {o["alert_id"]: o for o in outputs}` -- no ordering concept
- `_score_partition` iterates over scenarios with no group awareness
- `format_dashboard` has no sequence concept in its output

Temporal sequences need: (a) a grouping signal, (b) position within sequence, (c) per-sequence scoring (did the model escalate at the right alert?), (d) a separate scoring function.

The constraint that resolves the design: `score_run` must remain unchanged for backward compat. It is the benchmark's scoring contract and 133 tests depend on it. Sequence scoring is additive -- a new `score_sequences()` function that groups by `_meta.sequence_id` and adds escalation metrics on top of per-alert correctness.

For evaluated systems: each alert in a sequence gets its own `alert_id` and its own verdict/confidence. The sequence structure is visible in the scenario JSON through `_meta.sequence_id` and `_meta.sequence_position`. Systems can use these to correlate alerts. The scored output remains the same per-alert OUTPUT_SCHEMA -- no new output fields required from systems.

---

### Integration Point 4: Frame Extraction Baseline Is Protocol, Not Code

Current `baselines.py` has four heuristic baselines: random, majority_class, always_suspicious, severity_heuristic. All run without API keys on metadata only. They are cheap to run in CI.

A frame extraction baseline requires: (1) extracting keyframes from video, (2) calling an image-capable LLM with the keyframe, (3) obtaining triage verdicts. This is structurally identical to `evaluators.py` (API calls, response parsing, OUTPUT_SCHEMA conformance). It is not a metadata heuristic and does not belong in baselines.py.

Decision: frame extraction is an evaluation protocol, not a code baseline. The benchmark defines what counts as a valid frame extraction run (which frames, how to present them, required output schema, how to compute the gap metric). Users execute it themselves using the visual_only scenarios. The benchmark's job is scoring the outputs -- `score_run()` already handles this.

A new CLI command `analyze_frame_gap` can compute the gap between a frame-extraction run and a full-video run without requiring the benchmark to perform the extraction itself.

---

## Component Map: Modified vs New

### Components That Require Modification

**`psai_bench/schema.py`**
- Add `"visual_only"`, `"visual_contradictory"`, `"temporal"` to the `track` enum in `ALERT_SCHEMA`
- Remove `severity` and `description` from the top-level `required` array (make optional at schema level)
- Add optional `visual_data` structure fields: `keyframe_uris` (list of image URIs for frame extraction)
- Add v3 `_meta` fields to `_META_SCHEMA_V2`: `visual_gt_source`, `contradictory`, `sequence_id`, `sequence_position`, `sequence_length`, update `generation_version` enum to include `"v3"`
- All additions are backward-compatible: the `required` reduction only relaxes constraints, new `_meta` fields are all optional per existing pattern

**`psai_bench/distributions.py`**
- Add `CONTRADICTORY_THREAT_DESCRIPTIONS`: descriptions that read as benign but pair with threat videos. Example: "Authorized maintenance personnel observed", "Routine patrol activity detected", "Scheduled equipment check in progress"
- Add `CONTRADICTORY_BENIGN_DESCRIPTIONS`: descriptions that read as threatening but pair with benign videos. Example: "Aggressive behavior detected near perimeter", "Unauthorized access attempt flagged", "Suspicious individual loitering"
- These are distinct from `DESCRIPTION_POOL_AMBIGUOUS` -- ambiguous descriptions are vague, contradictory descriptions are directionally misleading in the opposite direction from the video's ground truth

**`psai_bench/scorer.py`**
- Add `SequenceScoreReport` dataclass (new, no changes to `ScoreReport`)
- Add `score_sequences(scenarios, outputs) -> SequenceScoreReport` (new function, does not touch `score_run`)
- `format_dashboard` gets an optional sequence section if `sequence_report` is provided

**`psai_bench/cli.py`**
- Extend `--track` choices in `generate` command to include the three new track values
- Add `score-sequences` command (separate from `score`)
- Add `analyze-frame-gap` command that takes two result files (frame-extraction run + full-video run) and reports the gap

**`psai_bench/validation.py`**
- Add track-aware validation: `visual_only` and `visual_contradictory` alerts must have `visual_data.uri` non-null
- `visual_contradictory` alerts must have `_meta.contradictory = True` and `_meta.visual_gt_source = "video_category"`
- `temporal` alerts must have `_meta.sequence_id` and `_meta.sequence_position` set

### New Components

**`VisualOnlyGenerator` class (psai_bench/generators.py)**

Generates scenarios with only `visual_data` populated and minimal metadata. Does NOT wrap MetadataGenerator -- that coupling is the wrong model for visual-only. Instead, builds directly from UCF Crime video annotations via `VisualTrackMapper`. Sets `severity = None`, `description = None`, `zone = {}`, `device = {}`, `context = {}`. Track is `"visual_only"`. GT comes from `UCF_CATEGORY_MAP[cat]["ground_truth"]`, not `assign_ground_truth_v2`. `_meta.visual_gt_source = "video_category"`.

**`ContradictoryGenerator` class (psai_bench/generators.py)**

Generates scenarios where metadata signals point opposite to video ground truth. Mechanism:
1. Generate a base visual scenario (category known from video)
2. If video category maps to THREAT GT, replace description with a sample from `CONTRADICTORY_THREAT_DESCRIPTIONS` (sounds benign) and set severity LOW or MEDIUM
3. If video category maps to BENIGN GT, replace description with a sample from `CONTRADICTORY_BENIGN_DESCRIPTIONS` (sounds threatening) and set severity HIGH or CRITICAL
4. Set `_meta.contradictory = True`, `_meta.visual_gt_source = "video_category"`, track = `"visual_contradictory"`

`_meta.ground_truth` reflects the video (the correct answer). The metadata is intentionally wrong.

**`TemporalSequenceGenerator` class (psai_bench/generators.py)**

Generates groups of 3-5 related alerts. Design decisions:

- A sequence has a `sequence_id` string (e.g., `"seq-0042"`), a shared site context (same zone, site_type, camera device), and escalating timestamps (5-15 minutes between alerts)
- Threat sequences: first 1-2 alerts are SUSPICIOUS or ambiguous (early signs), last 1-2 alerts are clear THREAT (pattern confirmed)
- Benign sequences: first alert triggers high severity, subsequent alerts provide context (badge access, scheduled maintenance) that resolves to BENIGN
- Generator emits a **flat list** of alerts with `_meta.sequence_id` and `_meta.sequence_position` set. They can be mixed with independent alerts in a single evaluation file.
- Uses `assign_ground_truth_v2` for individual alert GT, but the sequence-level narrative is constructed by the generator logic, not the GT function

GT for temporal sequences: each alert has its own GT (which may be SUSPICIOUS early in a threat sequence, THREAT later). The sequence-level metric is whether the model correctly escalated at the right position.

**`SequenceScoreReport` dataclass and `score_sequences()` function (psai_bench/scorer.py)**

```python
@dataclass
class SequenceScoreReport:
    n_sequences: int = 0
    n_threat_sequences: int = 0
    n_benign_sequences: int = 0
    early_detection_rate: float = 0.0    # Model escalated to THREAT within first 2 alerts of threat seq
    late_detection_rate: float = 0.0     # Model detected threat, but only at last alert
    missed_sequence_rate: float = 0.0    # Model never detected threat in a threat sequence
    false_escalation_rate: float = 0.0   # Model escalated on a benign sequence
    per_sequence_results: dict = field(default_factory=dict)

def score_sequences(
    scenarios: list[dict],
    outputs: list[dict],
) -> SequenceScoreReport:
    """Score temporal sequence evaluation.

    Groups alerts by _meta.sequence_id, sorts by _meta.sequence_position,
    then evaluates each sequence as a unit: did the model detect the threat
    at the right point? Did it escalate on benign sequences?

    Alerts without sequence_id are ignored (not an error -- mixed files are allowed).
    """
```

---

## Data Flow Changes

**Unchanged flow (metadata, visual, multi_sensor -- all v1/v2 scenarios):**
```
Generator -> list[alert] -> [user's system] -> list[output] -> score_run() -> ScoreReport
```

**New flow for visual_only:**
```
VisualOnlyGenerator (from VisualTrackMapper, UCF Crime annotations)
  -> list[alert: visual_data.uri set, severity/description null, context empty]
  -> [user's system with video processing capability]
  -> list[output: alert_id, verdict, confidence]
  -> score_run() -> ScoreReport
  (GT is from video category; scoring reveals whether model can triage without metadata)
```

**New flow for visual_contradictory:**
```
ContradictoryGenerator (from VisualTrackMapper + CONTRADICTORY_*_DESCRIPTIONS pools)
  -> list[alert: video shows X, metadata claims opposite of X]
  -> [user's system]
  -> list[output]
  -> score_run() -> ScoreReport
  (GT follows video; scoring reveals whether model was misled by misleading text)
```

**New flow for temporal sequences:**
```
TemporalSequenceGenerator
  -> list[alert: standard metadata, _meta.sequence_id + sequence_position set]
  -> [user's system, which may use sequence context]
  -> list[output: per-alert verdicts]
  -> score_run() -> ScoreReport           (per-alert metrics, unchanged)
  -> score_sequences() -> SequenceScoreReport  (sequence-level escalation metrics, new)
```

`score_run()` handles temporal scenarios correctly without changes because it matches by `alert_id` regardless of sequence membership. `score_sequences()` adds the grouping layer.

---

## Schema Changes Required

### ALERT_SCHEMA changes

```python
# Track enum extended
"track": {
    "type": "string",
    "enum": [
        "visual", "metadata", "multi_sensor",  # existing
        "visual_only", "visual_contradictory", "temporal"  # new
    ]
}

# severity and description moved from required to optional
# (required list shrinks from 9 fields to 7 for visual tracks)
# Track-aware enforcement moves to validation.py

# visual_data expanded
"visual_data": {
    "type": ["object", "null"],
    "properties": {
        "type": {"type": "string", "enum": ["video_clip", "image", "null"]},
        "uri": {"type": ["string", "null"]},
        "duration_sec": {"type": ["number", "null"]},
        "resolution": {"type": ["string", "null"]},
        "keyframe_uris": {          # NEW -- for frame extraction protocol
            "type": "array",
            "items": {"type": "string"},
            "description": "URIs of extracted keyframes for frame-extraction baseline"
        }
    }
}
```

### _META_SCHEMA_V2 additions

```python
"visual_gt_source": {
    "type": "string",
    "enum": ["video_category", "metadata_signals"],
    "description": "Whether GT was derived from video content or metadata signal weighting"
},
"contradictory": {
    "type": "boolean",
    "description": "True if scenario metadata intentionally misrepresents video content"
},
"sequence_id": {
    "type": ["string", "null"],
    "description": "Group identifier for temporal sequences; null for independent alerts"
},
"sequence_position": {
    "type": ["integer", "null"],
    "description": "0-indexed position within sequence; null for independent alerts"
},
"sequence_length": {
    "type": ["integer", "null"],
    "description": "Total alerts in this sequence; null for independent alerts"
},
# generation_version extended
"generation_version": {"type": "string", "enum": ["v1", "v2", "v3"]}
```

All are optional in the schema -- v1/v2 scenarios remain valid without these fields.

---

## Build Order

Dependencies are strict. Each step lists what it unblocks.

**Step 1: Schema v3 (schema.py) -- MUST BE FIRST**

Extend track enum, relax required array, add _meta v3 fields. Zero risk -- purely additive. No existing tests break because enum expansion never invalidates existing values, and removing from required never invalidates existing valid scenarios. Must be done first because every downstream generator and validator needs the new field definitions.

Unlocks: Steps 2, 3, 4, 5, 6.

**Step 2: Distributions additions (distributions.py) -- parallel with others after Step 1**

Add `CONTRADICTORY_THREAT_DESCRIPTIONS` and `CONTRADICTORY_BENIGN_DESCRIPTIONS`. Needed only by ContradictoryGenerator. Can be done in parallel with Step 3.

Unlocks: Step 4 (ContradictoryGenerator).

**Step 3: VisualOnlyGenerator (generators.py) -- after Step 1**

Builds on existing `VisualTrackMapper`. Sets `visual_gt_source = "video_category"`. Simpler than contradictory or temporal -- good proof-of-concept for the visual-only track before implementing harder cases. Does not call `assign_ground_truth_v2`.

Unlocks: Step 4 (serves as reference implementation).

**Step 4: ContradictoryGenerator (generators.py) -- after Steps 2 and 3**

Uses VisualOnlyGenerator pattern + CONTRADICTORY_*_DESCRIPTIONS pools. Swaps metadata signals to opposite direction. Sets `contradictory = True`.

Unlocks: Step 5 (visual track scoring).

**Step 5: Scorer and validation updates for visual tracks (scorer.py, validation.py) -- after Step 4**

`score_run` works without changes on visual_only and contradictory scenarios -- it matches by alert_id. What needs adding:
- Track partitioning in `_score_partition` so the dashboard can break down visual_only vs contradictory accuracy separately
- Track-aware validation warnings in `validate_submission` (visual_only alerts must have visual_data.uri)
These are additive changes, not rewrites.

Unlocks: Step 8 (CLI for visual tracks).

**Step 6: TemporalSequenceGenerator (generators.py) -- after Step 1, parallel with Steps 3-5**

Largest new generator. Generates cohesive sequences with temporal narrative. Independent of Steps 3/4 -- temporal sequences are metadata-track scenarios. Can run in parallel with visual track work once Step 1 is done.

Unlocks: Step 7.

**Step 7: score_sequences() (scorer.py) -- after Step 6**

New function and dataclass. Does not touch `score_run`. Requires temporal scenarios to test against.

Unlocks: Step 8 (sequence CLI command).

**Step 8: CLI updates (cli.py) -- after Steps 5 and 7**

Extend `--track` choices in `generate`. Add `score-sequences` command. Add `analyze-frame-gap` command. Both additive -- no existing commands change signature.

**Step 9: Frame extraction protocol document -- after Steps 3-5 are working**

No code dependencies. Write after visual-only scenarios exist so the protocol can reference the exact scenario format. Lives in `docs/EVALUATION_PROTOCOL.md`. Specifies: which frames to extract (first/middle/last + evenly-spaced N frames), how to present to model (single image per alert vs. collage), required output schema (identical to OUTPUT_SCHEMA), how to compute the gap metric (`analyze-frame-gap` command).

---

## Anti-Patterns to Avoid

### Anti-Pattern: Modifying score_run() for sequences

**What:** Changing `score_run` to handle sequences inline, perhaps by detecting `sequence_id` in `_meta` and grouping automatically.
**Why bad:** `score_run` is the benchmark's scoring contract. 133 tests depend on it. Sequence awareness in the flat scorer creates ordering complexity, breaks backward compat for every caller, and muddles the output schema (does a sequence need one verdict or N?).
**Instead:** `score_sequences()` is a separate function. It groups by `sequence_id` internally and calls `score_run` for per-alert metrics, then adds escalation metrics on top.

### Anti-Pattern: Reusing DESCRIPTION_POOL_AMBIGUOUS for contradictory scenarios

**What:** Using "Unusual movement detected" or "Suspicious activity in zone" for the contradictory track.
**Why bad:** Ambiguous descriptions are vague, not directional. A model that returns SUSPICIOUS on "Unusual movement detected" + fence-cutting video was not misled by the description -- it hedged appropriately. The contradictory test requires descriptions that actively point the wrong direction.
**Instead:** Dedicated `CONTRADICTORY_THREAT_DESCRIPTIONS` and `CONTRADICTORY_BENIGN_DESCRIPTIONS` pools where each description is specifically chosen to mislead in the opposite direction from the video's GT.

### Anti-Pattern: Frame extraction logic in baselines.py

**What:** Building keyframe extraction and image LLM calls into `baselines.py`.
**Why bad:** Requires API keys, video processing dependencies, network calls -- all things baseline tests explicitly avoid. Makes an expensive, environment-dependent baseline mandatory for the benchmark.
**Instead:** Frame extraction is an evaluation protocol. Users run it themselves using visual_only scenarios. The benchmark scores the outputs. `analyze-frame-gap` CLI command computes the metric from two result files.

### Anti-Pattern: Using assign_ground_truth_v2 for visual-only/contradictory scenarios

**What:** Calling the metadata-signal-weighted GT function on scenarios where metadata is absent (visual_only) or intentionally false (contradictory).
**Why bad:** With minimal metadata, `assign_ground_truth_v2` produces weighted_sum values near zero, resulting in mostly SUSPICIOUS GT regardless of video content. The GT becomes arbitrary noise uncorrelated with what the video actually shows.
**Instead:** `visual_gt_source = "video_category"` -- GT from `UCF_CATEGORY_MAP[cat]["ground_truth"]` directly. This is what `VisualTrackMapper` already does and it is correct.

### Anti-Pattern: Wrapping MetadataGenerator for visual-only scenarios

**What:** Following the existing VisualGenerator pattern (wrap MetadataGenerator, then patch `visual_data`).
**Why bad:** MetadataGenerator generates full metadata including description, severity, zone, device -- all the fields that visual-only scenarios must NOT have. Stripping them after generation is fragile and still calls `assign_ground_truth_v2` internally.
**Instead:** `VisualOnlyGenerator` builds directly from `VisualTrackMapper`. It does not inherit from or compose MetadataGenerator.

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Schema wall for visual-only | HIGH | Read full ALERT_SCHEMA; required array directly observed |
| GT assignment split needed | HIGH | Traced code path VisualGenerator -> MetadataGenerator -> assign_ground_truth_v2 |
| Temporal scoring design | HIGH | Read full scorer.py; flat list assumption is explicit in code |
| Frame extraction as protocol-not-code | HIGH | baselines.py structure clearly excludes API-dependent code |
| Contradictory description pool requirement | HIGH | DESCRIPTION_POOL_AMBIGUOUS confirmed non-directional in distributions.py |
| SequenceScoreReport metric specifics | MEDIUM | Early detection = first 2 alerts is reasonable; exact thresholds need validation once temporal scenarios exist |
| Track-aware validation approach | MEDIUM | validation.py not read in full; pattern inferred from test_core.py validation test patterns |
