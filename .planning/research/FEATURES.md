# Feature Landscape: PSAI-Bench v3.0

**Domain:** Visual and temporal track additions to an existing security alert triage benchmark
**Milestone:** v3.0 Perception-Reasoning Gap
**Researched:** 2026-04-13
**Confidence:** HIGH

## Framing Note

v2.0 shipped a complete Metadata Track with context-dependent GT, context-dependent scoring, 133 tests, and BYOS workflow. The v3.0 features are additions to that foundation. Every feature here must respect the constraint that video processing is explicitly out of scope — the benchmark generates structured scenario data; the evaluated system processes it. No video decoding libraries, no frame extraction pipelines, no video file bundling. The benchmark's job is to define what the visual content shows (in structured form) and let the system decide how to use that.

---

## What Already Exists

| Component | State |
|-----------|-------|
| `VisualGenerator` | Stub. Clones MetadataGenerator output, replaces `track`, adds `visual_data.uri`. GT is still determined by metadata signals — video URI is decoration. |
| `ALERT_SCHEMA.visual_data` | Object with `type`, `uri`, `duration_sec`, `resolution`. No content description field. |
| `_META_SCHEMA_V2` | No visual- or sequence-specific fields. |
| `baselines.py` | Four baselines, all metadata-only. No frame extraction baseline. |
| `scorer.py` | Per-alert independent scoring. No sequence-aware scoring. |

---

## Table Stakes

Features that must exist for the benchmark to deliver on its stated v3.0 claims. Missing any of these makes the benchmark untestable for the features it advertises.

| Feature | Why Required | Complexity | Dependencies |
|---------|--------------|------------|--------------|
| Visual-only scenario generation | VISION.md core claim: "video + minimal metadata, system derives everything from video." Without this the visual track remains decoration. | MEDIUM | Schema extension needed: `visual_ground_truth_description` in `visual_data`; strip severity, description, zone from alert body for visual-only scenarios. GT must derive from visual content description, not context signals. |
| Contradictory scenario flag in `_meta` | Without a flag identifying which scenarios are contradictory, BYOS users cannot filter them or report contradictory-specific accuracy. Results are uninterpretable. | LOW | New `_meta` field `contradictory: bool`; existing `adversarial` field is a model for this. |
| Frame extraction baseline | Visual track needs at least one non-random baseline, otherwise there is no floor to beat. The frame extraction baseline simulates a system that converts keyframes to text descriptions. It makes the research question "does full-video temporal analysis beat static keyframe description?" answerable. | LOW | New function in `baselines.py`. Can be implemented with synthetic frame descriptions drawn from `visual_ground_truth_description`. No new dependencies. |
| Visual track scoring (TDR/FASR by track) | Without per-track metric breakdowns, the benchmark cannot answer "does visual input improve triage?" — which is the entire research question. | LOW | The scorer already aggregates globally. Need to partition results by `track` field. Minor extension of existing scorer. |
| Sequence group identifier in schema | Temporal sequences require a `sequence_id` to link related alerts. Without it, evaluators cannot load sequences as ordered groups. | LOW-MEDIUM | Schema extension. Backward-compatible if optional field. |
| Sequence GT that evolves across alerts | If GT for alert N+1 is independent of alert N, temporal sequences add no value. The escalation pattern must be encoded so the full sequence produces a narrative arc: e.g., BENIGN → SUSPICIOUS → THREAT. | MEDIUM | New generator for `TemporalSequenceGenerator`. Produces groups of 3-5 alerts with monotonically escalating or de-escalating GT and explicit causal links in context. |
| Temporal scoring | The existing scorer evaluates each alert independently. Temporal sequences require sequence-level evaluation: did the system escalate at the right alert? Did it correctly identify when the threat resolved? | HIGH | Most significant new component. Separate scoring path from per-alert scoring. May require new metrics: escalation latency (how many alerts until system escalated), false escalation rate. |

---

## Differentiators

Features that distinguish the v3.0 benchmark from all prior work and justify the "Perception-Reasoning Gap" framing.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Contradictory scenarios (visual overrides metadata) | No existing physical security benchmark tests whether a model's visual perception can override textual priors. GroundLie360 (2025) handles contradictory text-video in misinformation detection — the same mechanism applied to security triage is novel. This is the primary research contribution. | MEDIUM | Two sub-types: (1) metadata-says-THREAT, video-shows-BENIGN (overreach); (2) metadata-says-BENIGN, video-shows-THREAT (underreach). GT follows video. Must track which modality the system trusted — add `modality_followed` to output schema or track by comparing verdict to metadata-implied vs. video-implied verdict. |
| Perception-reasoning gap metric | The measurable outcome of the contradictory scenario design: how often does adding visual data change the verdict, and is that change correct? This is what makes a paper publishable — a concrete gap metric. | LOW | Derived metric computed at scoring time, not a generator feature. Compare metadata-track accuracy vs. visual-track accuracy on matched contradictory scenarios. |
| Temporal escalation patterns | Real-world security triage involves sequential reasoning. No public physical security benchmark encodes escalation sequences. TSB-AD and similar time-series anomaly benchmarks handle continuous signals, not discrete alert sequences with narrative structure. | HIGH | Each 3-5 alert sequence should have a "trigger alert" — the alert at which a correctly-functioning system should escalate. GT for the sequence includes: trigger index, expected escalation verdict, expected final verdict. |
| Visual ground truth description field | Making the visual content machine-readable (as a structured description) without shipping video files or requiring processing infrastructure. This is the design choice that enables the BYOS model to work for visual scenarios. | LOW-MEDIUM | New field in `visual_data`: `content_description` (string, LLM-readable description of what the video shows) and `ground_truth_visual_event` (structured enum of event type). Populated during generation from UCF Crime category. |

---

## Anti-Features

| Feature | Why Requested | Why to Avoid | What to Do Instead |
|---------|---------------|--------------|-------------------|
| Video file bundling | Seems necessary for a "visual track" | Shipping 100+ GB of video files is incompatible with BYOS model, Apache-2.0 licensing of derived UCF Crime/Caltech content, and GitHub constraints. Explicit project constraint: "no video processing implementation — v3.0." | Ship `visual_data.uri` (existing) plus `visual_data.content_description` (new). Users who can process video use the URI. Users who can't use the structured description. Both are valid BYOS approaches. |
| Real video frame extraction pipeline | Makes the frame extraction baseline "real" | Requires ffmpeg or cv2 dependency. Project constraint: "no new dependencies unless strictly needed." Frame extraction is the user's job; the baseline should simulate what a keyframe-based system would produce, not actually implement one. | Frame extraction baseline uses synthetic descriptions drawn from the scenario's `visual_ground_truth_description`. It demonstrates the design pattern and gives a score floor. |
| Full video temporal analysis (ground truth from video processing) | Would make GT fully principled | Requires processing real video to determine GT — that's the user's system's job, not the benchmark's job. GT for visual scenarios must be determined at generation time. | GT is determined by the UCF Crime category and injected visual content description. Same deterministic-generation principle as metadata GT. |
| Continuous temporal scoring (VUS, range-AUC) | Appropriate for time-series anomaly detection benchmarks (TSB-AD pattern) | PSAI-Bench produces discrete alerts (3-class per alert), not continuous anomaly scores over time. VUS metrics assume a continuous score signal with a sliding threshold. | Sequence-level scoring: escalation latency, correct-escalation rate, correct-resolution rate. These are discrete, interpretable, and domain-appropriate for security SOC workflows. |
| Aggregate sequence score with time decay | Sounds sophisticated | Time decay weights assume earlier alerts matter less — opposite of security triage where early detection of an escalating threat is more valuable, not less. Any decay function encodes an arbitrary domain assumption. | Keep scoring transparent and separate: per-alert accuracy, escalation latency, resolution accuracy. Let operators weight by their priorities (existing pattern from v2.0). |

---

## Feature Dependencies

```
Schema: visual_ground_truth_description in visual_data
    └──enables──> Visual-only scenario generation (GT derives from description, not context signals)
    └──enables──> Contradictory scenario generation (metadata GT vs visual GT conflict)
    └──enables──> Frame extraction baseline (baseline reads content_description field)

Schema: _meta.contradictory flag
    └──enables──> Contradictory-specific accuracy reporting in scorer
    └──enables──> Perception-reasoning gap metric computation

Schema: sequence_id + alert_index_in_sequence
    └──enables──> TemporalSequenceGenerator
    └──enables──> Temporal scoring path in scorer

TemporalSequenceGenerator
    └──depends on──> MetadataGenerator v2 (reuse context-dependent GT)
    └──produces──> Linked alerts with escalating GT narrative
    └──enables──> Temporal scoring

Temporal scoring
    └──depends on──> sequence_id grouping in scenarios
    └──new component──> Separate from per-alert scoring
    └──produces──> Escalation latency, correct-escalation rate

Frame extraction baseline
    └──depends on──> visual_ground_truth_description field
    └──added to──> baselines.py
    └──enables──> Visual track score floor
```

---

## Complexity and Phase Sequencing Rationale

**Visual-only + contradictory scenarios (ship together):** Both depend on `visual_ground_truth_description` in the schema. Visual-only strips metadata signals; contradictory adds metadata that conflicts with visual content. Same schema extension gates both. Natural single phase.

**Temporal sequences (separate phase):** The only feature that touches schema, generators, AND scorer simultaneously. Sequence-ID threading through the schema, a new generator class, a new scoring path, and new metrics. Highest implementation risk. Should be its own phase so it can slip independently without blocking visual track delivery.

**Frame extraction baseline (fast follow):** One new function in `baselines.py`, no schema changes, no new deps. Can ship with visual track or immediately after. LOW risk.

**Evaluation protocol document:** Documents the evaluation procedure for all three new feature types. No code, but must reflect final decisions on GT definition, scoring protocol, and sequence evaluation rules. Should be the last artifact of v3.0, not the first.

---

## Concrete Complexity Estimates

| Feature | Estimated LOC | Test Surface | Risk |
|---------|---------------|--------------|------|
| Schema extension (visual content description + sequence fields) | ~20-40 | Schema validation tests | Low |
| Visual-only generator | ~100-150 | 3-5 new test cases | Medium |
| Contradictory scenario injection | ~80-120 | Edge cases: both signals agree, only one overrides | Medium |
| Frame extraction baseline | ~30-50 | Baseline output format tests | Low |
| Temporal sequence generator | ~200-300 | Sequence ordering, escalation logic, GT arc | High |
| Temporal scorer | ~150-250 | Escalation latency computation, edge cases (all-BENIGN sequence, immediate-THREAT sequence) | High |
| Perception-reasoning gap metric | ~30-50 | Derived from existing scorer output | Low |
| Evaluation protocol doc | Non-code | N/A | Low |

---

## Sources

- PSAI-Bench VISION.md — primary feature specification, contradiction and temporal sequence design
- PSAI-Bench PROJECT.md — constraints (no video processing, no new deps, Apache-2.0)
- GroundLie360 (2025): https://arxiv.org/html/2509.08008v1 — contradictory text-video benchmark pattern (misinformation domain, same mechanism)
- TSB-AD benchmark: https://github.com/TheDatumOrg/TSB-AD — temporal anomaly scoring patterns; VUS-PR metric identified as inappropriate for discrete alert setting
- Video-MME / AKS (CVPR 2025): https://arxiv.org/abs/2502.21271 — frame extraction baseline patterns; establishes that keyframe-vs-full-video is an active research question with measurable gaps
- KDD 2025 survey on time-series anomaly detection: https://inria.hal.science/hal-05218929/file/kdd_survey.pdf — scoring patterns for alert-based evaluation

---
*Research for PSAI-Bench v3.0 milestone*
*Researched: 2026-04-13*
