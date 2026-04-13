# Pitfalls Research: v3.0 Visual / Contradictory / Temporal / Frame-Extraction Features

**Domain:** Adding visual-only scenarios, contradictory scenarios, temporal alert sequences,
and frame extraction baseline to PSAI-Bench — an existing benchmark with 133 tests,
strict seed reproducibility, and the BYOS (bring-your-own-system) contract.
**Researched:** 2026-04-13
**Confidence:** HIGH — derived directly from repo inspection of existing generators.py,
schema.py, scorer.py, video_mapper.py, test_leakage.py, and the v3.0 VISION.md.

---

## Critical Pitfalls

### Pitfall 1: Visual-Only Scenarios Still Have Leaky Metadata Fields

**What goes wrong:**
`ALERT_SCHEMA` marks `severity`, `description`, `zone`, and `context` as required fields.
A "visual-only" scenario cannot simply omit them — the schema validator will reject it.
The naive fix is to populate these with dummy values ("Unknown", "LOW", etc.). But any
non-null dummy value becomes a signal. A model that sees `severity = "UNKNOWN"` as a
new enum value immediately knows "this is a visual-only scenario" — which leaks the
scenario type itself, allowing models to switch reasoning strategies rather than testing
perception. Worse, if the dummy description string is the same for every visual-only
scenario, a depth-1 decision tree can identify the track label from the description field,
violating the leakage test in `test_leakage.py`.

**Why it happens:**
Schema enforces completeness; visual-only intent conflicts with schema completeness.

**Consequences:**
- Leakage tests fail on visual-only scenarios if dummy text is uniform
- Models learn to detect visual-only scenarios from text fields, not from video
- The benchmark measures "track detection skill" not "visual perception skill"

**Prevention:**
- Add `"visual_only": true` to `_meta` (not exposed to evaluated systems) rather than
  signaling it via public fields
- Populate required fields with plausible-but-uninformative values drawn from the existing
  shared description pools — same descriptions used across all tracks, not a unique sentinel
- For severity: sample from the real distribution, not a fixed value
- Run the leakage test (`test_leakage.py`) specifically on visual-only scenarios after
  generation to confirm no field achieves >70% stump accuracy on this subset

**Detection:**
- `test_leakage.py` fails on visual-only subset
- Description field value is identical across all visual-only scenarios
- `track` field value is "visual" for all visual-only scenarios — if the schema exposes this,
  models can trivially route on it

**Phase:** Visual Track implementation — first design decision before writing any generator code.

---

### Pitfall 2: Contradictory Scenario Ground Truth Becomes Circular

**What goes wrong:**
A contradictory scenario has metadata saying X while video shows Y. The ground truth is
determined by "video overrides metadata." But the current `assign_ground_truth_v2` function
in `distributions.py` computes ground truth from metadata signals only (weighted_sum of
zone sensitivity, time of day, device FPR, recent events). If you feed a contradictory
scenario through the same GT function, you get the metadata-derived GT — not the
video-derived GT — making the scenario incoherent. The scenario labeled "metadata says
BENIGN, video shows THREAT" will have GT = BENIGN if the metadata GT function runs.

**Why it happens:**
The GT function was written for metadata-only scenarios. Contradictory scenarios require
a new GT assignment path that ignores the metadata signals and resolves from the
video content label directly.

**Consequences:**
- A system that correctly reads the video and says THREAT gets scored wrong
- Ground truth is not defensible ("why is GT = BENIGN when the video clearly shows fence-cutting?")
- Published decision rubric cannot explain the label coherently

**Prevention:**
- Contradictory scenarios must have their GT set explicitly from the video content label
  (`UCF_CATEGORY_MAP[category]["ground_truth"]`), bypassing the weighted-sum function entirely
- Add a new `_meta` field: `"gt_source": "video"` for contradictory scenarios and
  `"gt_source": "context"` for normal scenarios — this makes the GT derivation auditable
- Add a test: for every contradictory scenario where video_label == "THREAT",
  `_meta.ground_truth` must equal "THREAT" regardless of metadata signals

**Detection:**
- Scenario has `description: "Routine activity"` + video of fence-cutting + GT = BENIGN
- Decision rubric cannot explain the GT label without contradiction

**Phase:** Contradictory scenario generation — before any ground truth is assigned.

---

### Pitfall 3: Temporal Sequences Break the Per-Alert Scoring Contract

**What goes wrong:**
The current scorer (`scorer.py`) operates on independent alerts: each alert gets one
prediction, one GT, one score. Temporal sequences require a model to see alerts 1-4 before
triaging alert 5. If the benchmark still scores each alert independently, two problems emerge:

1. **Alert 1 is unscored correctly but unfair.** Alert 1 has no prior context, so any system
   that says "SUSPICIOUS" on it (because there is no pattern yet) gets penalized even though
   that is the correct initial response. A system that says "THREAT" on alert 1 of a 5-alert
   escalation sequence gets a false positive — but that's the right pattern-detection call.

2. **Sequence-aware scoring is not supported.** The scorer has no concept of a sequence ID,
   no "score the final alert in context of the sequence" mode, and no "did the system
   correctly detect the escalation pattern" metric.

**Why it happens:**
The scoring contract was designed around independent alerts. Sequence scoring requires
group-level evaluation, not per-alert evaluation.

**Consequences:**
- Systems optimized for independent triage will score incorrectly on sequences
- No fair comparison between sequence-aware and sequence-unaware systems
- SUSPICIOUS overuse (the known pathology from v2.0 evaluation) will be even worse on
  early alerts in a sequence — unfairly penalized by TDR

**Prevention:**
- Add `sequence_id` and `sequence_position` to `_meta` (not exposed to systems)
- Add `"context": {"sequence_history": [...]}` to alerts 2-5 in a sequence, containing
  summaries of prior alerts — this is what gets exposed to the system
- Define scoring at two levels: per-alert (existing scorer, unchanged) and per-sequence
  (new: did the system correctly escalate by alert N?)
- Keep sequence scoring separate from existing metrics so 133 existing tests are unaffected
- Document which metric applies to sequence scenarios in the evaluation protocol

**Detection:**
- All systems report SUSPICIOUS on alert 1 of every sequence (no baseline to compare against)
- TDR for sequences is significantly lower than for independent alerts (not a model failure —
  a scoring design failure)

**Phase:** Temporal sequence design — before scoring logic is touched.

---

### Pitfall 4: Seed Reproducibility Breaks When New Generators Share the Same RNG Stream

**What goes wrong:**
Every existing generator (`MetadataGenerator`, `VisualGenerator`, `MultiSensorGenerator`)
takes a `seed` parameter and creates `np.random.RandomState(seed)`. If a new generator
(e.g., `ContradictoryGenerator`) is added and the caller passes the same seed, both generators
consume from independent RNG instances seeded at 42 — which is fine. But if any caller
creates one RNG and passes it to multiple generators in sequence (or if a generator internally
spawns sub-generators), the RNG state is shared and any change to one generator's call count
shifts all subsequent generation. This is the classic "RNG stream coupling" problem.

**Why it happens:**
Current generators appear isolated, but `VisualTrackMapper` imports and calls private
functions from `generators.py` (`_assign_difficulty`, `_generate_timestamp`). If new
generators do the same, internal call counts become load-bearing.

**Consequences:**
- Existing 133 tests that assert scenario determinism may fail after adding new generators
- `psai-bench generate --seed 42 --track metadata` produces different output if the
  metadata generator's internal call count changes due to refactoring
- Published benchmark scores become non-reproducible across versions

**Prevention:**
- Each generator must own its RNG instance exclusively: `self.rng = np.random.RandomState(seed)`
- Never share RNG instances between generator classes
- Never call a generator's public methods from another generator's internal methods
- Add a regression test: generate 100 metadata scenarios with seed=42, hash the first
  scenario's `alert_id` and `_meta.ground_truth`, and assert it equals a pinned value
  in the test. This test breaks immediately if the stream shifts.

**Detection:**
- Existing determinism tests fail after adding a new generator file
- `test_core.py` `test_generator_determinism` test fails with a new import at module level

**Phase:** Every phase that adds a new generator — pin the regression hash before touching anything.

---

### Pitfall 5: Frame Extraction Baseline Becomes an Unfair Comparison Baseline

**What goes wrong:**
The "frame extraction baseline" is described as: extract keyframes, describe them with an
image model, compare to full-video temporal analysis. The pitfall is defining what "fair"
means. If the keyframe extractor picks frames that contain the anomaly (e.g., frame 1200
of a burglary where the person is clearly visible), the keyframe baseline will perform nearly
as well as temporal analysis — falsely concluding that "temporal understanding adds no value."
If the keyframe extractor picks non-anomaly frames (e.g., empty scene), it underperforms
unfairly.

UCF Crime temporal annotations already provide the anomaly start/end frames
(`anomaly_segments` in `_meta`). If keyframe selection uses these annotations — even
indirectly — the baseline is cheating. The entire point is to measure whether temporal
understanding finds the anomaly that keyframe sampling would miss.

**Why it happens:**
Keyframe selection strategy is underspecified. "Extract keyframes" can mean anything from
uniform sampling to motion-based selection to annotation-guided selection.

**Consequences:**
- If keyframes are annotation-guided: baseline artificially inflated, conclusion wrong
- If keyframes are uniformly sampled: result depends on sampling rate, not model capability
- Published conclusion ("temporal analysis adds X% over keyframes") is not reproducible
  unless keyframe strategy is fully specified and deterministic

**Prevention:**
- Define keyframe strategy precisely: uniform temporal sampling at N frames per video,
  where N is fixed (e.g., N=4), and selection is deterministic given a seed
- Never expose `anomaly_segments` to the keyframe extractor — treat it as ground truth only
- Implement the baseline as a PSAI-Bench internal tool (not user-defined), so it is
  identical across all comparisons
- Document the exact sampling strategy in the evaluation protocol

**Detection:**
- Keyframe baseline accuracy exceeds random baseline by more than 20pp on visual-only
  scenarios — suggests annotation leakage into frame selection

**Phase:** Frame extraction baseline design — before any implementation.

---

### Pitfall 6: UCF Crime Video Label Distribution Creates Class Imbalance in Visual Track

**What goes wrong:**
UCF Crime test set has 140 anomaly videos across 13 categories + 150 normal videos (290 total).
Mapping these to THREAT/SUSPICIOUS/BENIGN via `UCF_CATEGORY_MAP` produces a specific
distribution that is not balanced. Some categories map to SUSPICIOUS
(e.g., Arrest, Shoplifting) and some to THREAT (Arson, Shooting, Explosion). Normal maps to
BENIGN. The resulting class distribution in visual-only scenarios may differ substantially
from the metadata-track distribution, making cross-track score comparisons misleading
(a system scoring better on visual-only may just be benefiting from a more favorable class
distribution, not better visual perception).

**Why it happens:**
UCF Crime was not designed with a balanced GT distribution for PSAI-Bench's three-class schema.

**Consequences:**
- TDR and FASR metrics are not comparable between visual and metadata tracks if class distributions differ
- Published results need a distribution disclaimer to be scientifically valid
- The leakage test `test_class_balance` may fail on visual-only scenarios (65% threshold
  may be violated if BENIGN dominates due to 150 normal videos)

**Prevention:**
- Compute and document the class distribution of visual-only scenarios before publishing
- If distribution is highly imbalanced, apply stratified subsampling to match the metadata
  track distribution — or report cross-track comparisons as distribution-adjusted
- Run `test_class_balance` specifically on visual-only scenarios after generation

**Detection:**
- BENIGN > 60% of visual-only scenarios (150 normal / 290 total = 51.7% BENIGN before mapping)
- Cross-track TDR comparison shows large difference unexplained by model capability

**Phase:** Visual track generation — after mapping is defined, before scoring is implemented.

---

## Moderate Pitfalls

### Pitfall 7: Contradictory Scenarios Require Human-Auditable Pairs, Not Algorithmic Flip

**What goes wrong:**
The easiest implementation of "contradictory scenario" is: take an existing metadata scenario,
flip the description to say the opposite, keep the video label. But algorithmic flipping of
descriptions produces implausible pairs. "Person detected near perimeter" flipped to "No activity
detected" while the video shows a burglary is too obvious — models detect the contradiction
immediately from the text alone and route to the video. The scenario tests "can you detect a
contradiction" not "can you perceive what the video shows."

**Prevention:**
- Use the existing `DESCRIPTION_POOL_AMBIGUOUS` pool for the text side of contradictory scenarios
  so the text does not obviously contradict the video
- The contradiction should be subtle: metadata says "Routine vehicle movement" while video shows
  a person on foot in a restricted zone — not "No activity" while the video shows an explosion
- Design the contradiction so a system relying only on metadata would plausibly say BENIGN,
  and a system using video correctly says THREAT
- Document a typology of contradiction pairs in the evaluation protocol (e.g., 3 contradiction
  archetypes) so researchers know what they are testing

**Phase:** Contradictory scenario design — specification phase before coding.

---

### Pitfall 8: Temporal Sequence Position Leaks Information

**What goes wrong:**
If temporal sequences always follow a fixed escalation pattern (alert 1 = BENIGN, alert 5 =
THREAT), a model that learns the position-to-label mapping from training data will correctly
predict alert 5 = THREAT without reading the content. Position itself becomes a leakage field.

**Prevention:**
- Vary the escalation point across sequences: some sequences escalate at position 3, some at 4,
  some at 5
- Include decoy sequences that plateau at SUSPICIOUS without escalating to THREAT
- Add `sequence_position` to `_meta` but not to the exposed alert fields
- Run a position-stump test: a depth-1 tree predicting GT from sequence position should not
  exceed 70% accuracy (same threshold as the existing leakage test)

**Phase:** Temporal sequence generation — before building the sequence generator.

---

### Pitfall 9: Adding New Schema Fields Breaks Existing Schema Validation Tests

**What goes wrong:**
`ALERT_SCHEMA` uses JSON Schema. Adding a new required field (e.g., `sequence_id` or
`visual_only_flag`) to the schema breaks all existing test fixtures that use `_make_scenario()`
in `test_core.py` — they omit the new required field and will fail `validate_alert()`.

**Prevention:**
- New fields for v3.0 features should go in `_meta` (not schema-validated) wherever possible
- If a new schema field is truly needed, add it as `"required": false` with a default, not as
  a new required field
- After any schema change, run the full 133-test suite before proceeding

**Phase:** Any phase that modifies `schema.py`.

---

### Pitfall 10: Video URIs Are User-Local Paths — Scoring Must Be Path-Agnostic

**What goes wrong:**
`visual_data.uri` currently stores either a local path (e.g., `/Users/.../ucf_crime/Burglary/...`)
or a HuggingFace path (`hf://...`). The scorer never reads these paths — it scores outputs,
not videos. But if any benchmark tool (e.g., a new frame extraction baseline runner) tries to
open `visual_data.uri` on a system where videos are stored at a different path, it fails with
`FileNotFoundError`. Users who run `psai-bench generate` on one machine and `psai-bench score`
on another will get path errors.

**Prevention:**
- Keep video paths relative or symbolic (dataset-relative, not absolute)
- The frame extraction baseline must accept a `--video-dir` override that remaps URIs at runtime
- Document in the evaluation protocol that visual track scenarios require local video files and
  how to configure the path mapping

**Phase:** Frame extraction baseline implementation.

---

### Pitfall 11: Caltech Camera Traps Cannot Support Visual-Only Scenarios Without New Annotations

**What goes wrong:**
Caltech Camera Traps provides species/empty annotations, not temporal anomaly annotations.
A "visual-only" scenario from Caltech would show a camera trap image (or short clip) of a
coyote and ask the system to triage it. But without knowing the camera's deployment context
(solar farm vs. wildlife preserve), the GT for "coyote in frame" is undefined. UCF Crime has
clear anomaly/normal labels directly usable for visual-only GT. Caltech does not.

**Prevention:**
- Visual-only scenarios should come exclusively from UCF Crime in v3.0
- Caltech remains metadata-only track (as in v2.0)
- Document this scope decision explicitly in the evaluation protocol to prevent future
  contributors from adding Caltech visual-only scenarios without additional annotation work

**Phase:** Visual track scoping — milestone planning.

---

## Minor Pitfalls

### Pitfall 12: Temporal Sequence Timestamps Must Be Internally Consistent

**What goes wrong:**
Alerts in a sequence are generated independently. If alert 1 has `timestamp = 2026-03-15T14:30:00`
and alert 3 has `timestamp = 2026-03-15T13:45:00` (earlier than alert 1), the sequence is
temporally incoherent. A model that reads timestamps will see alerts "going back in time" and
either error or produce garbage reasoning.

**Prevention:**
- Generate sequence timestamps by incrementing from a base timestamp: alert N has
  `base + (N-1) * interval_minutes`
- `interval_minutes` should vary (e.g., 5-20 minutes) to reflect realistic alert spacing
- Add a test: for every sequence, all alerts must have strictly increasing timestamps

**Phase:** Temporal sequence generator implementation.

---

### Pitfall 13: "Contradictory" Scenario Requires Two Distinct Ground Truth Labels During Construction

**What goes wrong:**
During development, a contradictory scenario must track both the metadata-derived GT
(what the metadata signals say) and the video-derived GT (what the video shows). If only one
is stored, the evaluation protocol cannot verify the contradiction is meaningful (i.e., the
two GT signals genuinely disagree). A scenario that happens to have `metadata_gt = SUSPICIOUS`
and `video_gt = THREAT` is a contradiction. A scenario where both agree is not.

**Prevention:**
- Store both `metadata_derived_gt` and `video_derived_gt` in `_meta` for contradictory scenarios
- Final `ground_truth` in `_meta` is always `video_derived_gt` for contradictory scenarios
- Add a test: all scenarios with `_meta.contradictory = True` must have
  `metadata_derived_gt != video_derived_gt`

**Phase:** Contradictory scenario generation.

---

### Pitfall 14: Frame Extraction Baseline Depends on External CV Libraries Not Currently in Deps

**What goes wrong:**
Keyframe extraction requires reading video files: either OpenCV (`cv2`) or PyAV or similar.
These are not in `pyproject.toml` and carry significant binary dependencies (OpenCV is ~50MB
installed). Adding them as hard dependencies bloats the install for all users who only need
the metadata track.

**Prevention:**
- Add video dependencies as an optional extras group: `pip install psai-bench[visual]`
- Baseline runner should import these lazily with a helpful error if missing:
  `"Frame extraction requires: pip install psai-bench[visual]"`
- Do not add `opencv-python` to core deps — it conflicts with `opencv-python-headless` in
  server environments

**Phase:** Frame extraction baseline implementation.

---

## Phase-Specific Warning Summary

| Phase Topic | Critical Pitfall | Mitigation |
|-------------|-----------------|------------|
| Visual-only generator | Leaky dummy metadata fields | Use shared description pools; run leakage test on visual subset |
| Visual-only generator | Caltech has no anomaly annotations | UCF Crime only for visual-only |
| Contradictory scenarios | GT resolves from metadata, not video | New GT path: `video_derived_gt` bypasses weighted-sum function |
| Contradictory scenarios | Descriptions too obviously wrong | Use ambiguous descriptions that do not directly contradict video |
| Temporal sequences | Per-alert scorer penalizes correct early SUSPICIOUS | Add sequence-level scoring; keep per-alert scorer for existing tests |
| Temporal sequences | Position leaks GT | Vary escalation point; add position-stump leakage test |
| Temporal sequences | Incoherent timestamps | Generate incrementally from base timestamp |
| Seed reproducibility | New generators share RNG streams | Each generator owns its own `RandomState(seed)` |
| Seed reproducibility | New code shifts existing RNG call count | Pin regression hash test before any generator change |
| Frame extraction baseline | Annotation leakage into keyframe selection | Uniform temporal sampling, never use `anomaly_segments` for selection |
| Frame extraction baseline | Video CV deps bloat install | Optional `psai-bench[visual]` extras group |
| Schema changes | New required fields break 133 tests | Prefer `_meta` additions; never add required public schema fields |
| Video URIs | Absolute paths break on different machines | Relative paths + `--video-dir` override |
| Class balance | UCF Crime distribution != metadata distribution | Compute visual-only class dist; stratify if needed |

---

## Integration Regression Risk

The 133 existing tests must not regress. The following changes carry the highest regression risk:

| Change | Tests at Risk | Guard |
|--------|--------------|-------|
| Modifying `schema.py` | All `validate_alert()` calls in `test_core.py` | Run full test suite before merging |
| Modifying `distributions.py` | `test_leakage.py`, `test_core.py::test_generator_determinism` | Pin hash before and verify after |
| Modifying `generators.py` internal functions | `VisualTrackMapper` (imports private functions) | Any change to `_assign_difficulty` or `_generate_timestamp` is high risk |
| Adding imports to `generators.py` | Module-level RNG calls shift stream | Verify seed-42 scenario ID hash unchanged |
| Adding scoring metrics to `scorer.py` | `test_core.py::test_scorer_*` | New metrics must not change existing metric values |

---

## Sources

- Direct inspection: `/psai_bench/generators.py`, `schema.py`, `scorer.py`, `video_mapper.py`,
  `baselines.py`, `distributions.py`, `tests/test_leakage.py`, `tests/test_core.py`
- `.planning/PROJECT.md` — constraint: 133 tests must not regress; seed reproducibility hard constraint
- `.planning/VISION.md` — v3.0 feature definitions and contradictory scenario design intent
- NumPy RandomState documentation — `np.random.RandomState` per-instance isolation
- UCF Crime dataset structure: 140 anomaly test videos (13 categories) + 150 normal, with temporal annotations

---
*Pitfalls research for: PSAI-Bench v3.0 — visual/contradictory/temporal/frame-extraction milestone*
*Researched: 2026-04-13*
