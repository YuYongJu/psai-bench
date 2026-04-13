# Project Research Summary

**Project:** PSAI-Bench v3.0 — Perception-Reasoning Gap milestone
**Domain:** Physical security AI benchmark — visual, contradictory, and temporal scenario additions
**Researched:** 2026-04-13
**Confidence:** HIGH

## Executive Summary

PSAI-Bench v3.0 adds three scenario tracks to an existing benchmark that ships 133 passing tests, strict seed reproducibility, and a BYOS (bring-your-own-system) evaluation contract. The benchmark generates structured scenario data; it does not process video. This constraint is the load-bearing design principle for every decision below. Visual-only scenarios, contradictory scenarios, and temporal sequences are all generator additions — new fields in alert dicts, new distributions data, new scoring partitions — with no video processing in the benchmark itself. The only feature that touches actual video bytes is the frame extraction baseline, which is rearchitected as an evaluation protocol (not benchmark code) based on direct inspection of baselines.py.

The recommended approach is purely additive: extend schema.py first (enables all downstream work), then build generators for each new track in dependency order, then add scoring, CLI, and documentation. All schema additions are backward-compatible — removing fields from `required` never invalidates existing scenarios, and new `_meta` fields are optional by convention. The existing `score_run()` function is the benchmark's scoring contract and must not be modified; temporal sequence scoring ships as a new `score_sequences()` function alongside it. The only new dependency is `opencv-python-headless >= 4.10` in a new `[visual]` optional extras group — everything else (generators, scoring, schema, CLI) uses existing numpy, click, and jsonschema.

The primary risk is metadata leakage in visual-only scenarios. Three different approaches appear across the research files, and only one passes the existing `test_leakage.py` test. STACK.md recommends sentinel values (`"NO_DESCRIPTION_VISUAL_ONLY_TRACK"`); ARCHITECTURE.md recommends null fields (schema optional); PITFALLS.md demonstrates that both are trivially detectable by the depth-1 stump the leakage test uses. The correct approach is to populate required fields from the existing shared description pools so the leakage test on the visual-only subset does not fail. This conflict between research files must be resolved at schema design time — before any generator code is written.

---

## Key Findings

### Stack: Minimal Additions Required

Three of four v3.0 features require zero new dependencies. Visual-only, contradictory, and temporal scenarios are pure generator additions using existing numpy for RNG, jsonschema for validation, and click for CLI. The frame extraction baseline is reclassified as an evaluation protocol — users run it themselves, the benchmark scores outputs — eliminating the dependency concern for the benchmark itself. If a benchmark-internal frame extraction tool is ever added, it uses `opencv-python-headless >= 4.10` in a new `[visual]` optional group.

**Core technologies (unchanged):**
- numpy >= 1.24: all generator RNG, scoring partitions, temporal sequence math
- click >= 8.0: CLI extensions for new generator subcommands
- jsonschema >= 4.0: schema validation for additive alert dict fields
- anthropic / openai / google-genai: already in `[api]` optional group for vision LLM calls

**New optional dependency:**
- `opencv-python-headless >= 4.10` in new `[visual]` group — frame extraction only, ships own ffmpeg, headless CI-safe, Python 3.7–3.13 wheels confirmed on PyPI

**Rejected and why:** decord (abandoned June 2021, no Python 3.12 wheels), decord2 (single-maintainer fork), ffmpeg subprocess (hidden system dependency breaks portable pip install), Pillow (cv2.imencode handles frame encoding), PyAV (requires system libav build), scenedetect (semantic selection is wrong for the baseline by design).

### Features: Table Stakes and Complexity

**Must have (table stakes):**
- Visual-only scenario generation (MEDIUM complexity) — the visual track is decoration without it; requires schema extension and GT derivation from UCF Crime category, not metadata signals
- Contradictory scenario flag in `_meta` (LOW complexity) — without it, BYOS users cannot filter or report per-type accuracy; results are uninterpretable
- Frame extraction baseline (LOW complexity) — reclassified as evaluation protocol, not benchmark code; a new `analyze-frame-gap` CLI command computes the gap from two result files
- Visual track scoring / TDR+FASR by track (LOW complexity) — partition existing `_score_partition` by track value; minor scorer extension
- Sequence group identifier in schema (LOW-MEDIUM complexity) — `sequence_id` and `sequence_position` in `_meta`; backward-compatible optional fields
- Sequence GT that evolves across alerts (MEDIUM complexity) — `TemporalSequenceGenerator` with escalating/de-escalating narrative arc
- Temporal scoring (HIGH complexity) — `score_sequences()` as a separate function; most significant new component

**Differentiators:**
- Contradictory scenarios (MEDIUM) — no existing physical security benchmark tests visual-perception override of textual priors; primary research contribution
- Perception-reasoning gap metric (LOW) — derived metric at scoring time comparing metadata-track vs visual-track accuracy on matched contradictory scenarios; what makes results publishable
- Temporal escalation patterns (HIGH) — no public physical security benchmark encodes discrete alert sequences with narrative structure
- Visual ground truth description field (LOW-MEDIUM) — `visual_data.content_description` makes visual content machine-readable without shipping video files; enables the BYOS model for visual scenarios

**Defer to v2+ (anti-features confirmed):**
- Video file bundling — incompatible with BYOS model, Apache-2.0 licensing, and GitHub constraints
- Real video frame extraction in the benchmark — user's system's job, not the benchmark's
- Continuous temporal scoring (VUS, range-AUC) — inappropriate for discrete alert sequences
- Aggregate sequence score with time decay — encodes arbitrary domain assumptions, reduces transparency

### Architecture: Build Order and Component Map

The architecture is additive. The existing data flow (`Generator -> list[alert] -> [user's system] -> list[output] -> score_run() -> ScoreReport`) is unchanged for all v1/v2 scenarios. Three new flows are added in parallel with the existing one.

**Critical design decisions confirmed by code inspection:**
1. Schema must be modified first — ALERT_SCHEMA marks `severity` and `description` as required, which conflicts with visual-only scenarios that must omit them. Option A (track-aware optional fields via validation.py) is chosen over Option B (uninformative placeholders) to prevent leakage.
2. GT assignment diverges by track — `assign_ground_truth_v2` uses metadata signals and must NOT be called for visual-only or contradictory scenarios; those must use `UCF_CATEGORY_MAP[cat]["ground_truth"]` directly.
3. Temporal sequences break the flat-list assumption in `score_run()` — solved by a new `score_sequences()` function that does not touch `score_run`, preserving all 133 test contracts.
4. Frame extraction is protocol, not code — `baselines.py` structure explicitly excludes API-dependent code; frame extraction goes in `docs/EVALUATION_PROTOCOL.md` and a new `analyze-frame-gap` CLI command.

**Major components — modified:**
- `schema.py` — extend track enum; relax required array; add `_meta` v3 fields (all optional)
- `distributions.py` — add `CONTRADICTORY_THREAT_DESCRIPTIONS` and `CONTRADICTORY_BENIGN_DESCRIPTIONS` pools
- `scorer.py` — add `SequenceScoreReport` dataclass and `score_sequences()` function; add track partitioning to dashboard
- `cli.py` — extend `--track` choices; add `score-sequences` and `analyze-frame-gap` commands
- `validation.py` — add track-aware validation (visual_only requires `visual_data.uri`; contradictory requires `_meta.contradictory = True`; temporal requires `sequence_id`)

**Major components — new:**
- `VisualOnlyGenerator` — builds directly from `VisualTrackMapper`; does NOT wrap `MetadataGenerator`; GT from UCF Crime category
- `ContradictoryGenerator` — uses `VisualOnlyGenerator` pattern + contradictory description pools; sets `_meta.contradictory = True`; GT follows video
- `TemporalSequenceGenerator` — generates flat list of 3-5 linked alerts with `sequence_id`, `sequence_position`, escalating timestamps; uses `assign_ground_truth_v2` per-alert (temporal track retains metadata signals)

### Critical Pitfalls

1. **Metadata leakage in visual-only scenarios** — STACK.md recommends sentinel values, ARCHITECTURE.md recommends null fields; both fail `test_leakage.py` because a depth-1 stump detects the track from the description or severity field. PITFALLS.md is correct: populate required fields from the existing shared description pools drawn from the same distributions as all other tracks. Resolve this conflict at schema design time before any generator code is written.

2. **Contradictory GT resolves from metadata, not video** — If `assign_ground_truth_v2` runs on contradictory scenarios, GT follows metadata signals and the scenario is incoherent. Contradictory scenarios must bypass the weighted-sum function and take GT directly from `UCF_CATEGORY_MAP[cat]["ground_truth"]`. Store both `metadata_derived_gt` and `video_derived_gt` in `_meta`; add a test asserting they differ for all `contradictory = True` scenarios.

3. **Temporal sequences penalize correct early SUSPICIOUS responses** — Per-alert independent scoring penalizes a system that correctly returns SUSPICIOUS on alert 1 of a 5-alert escalation sequence. Keep per-alert scoring unchanged for existing tests; add `score_sequences()` as a separate scoring path. Document which metric applies to which scenario type in the evaluation protocol.

4. **RNG stream coupling breaks seed reproducibility** — New generators sharing an RNG instance or importing private functions from `generators.py` shift existing call counts and break determinism tests. Each generator must own its own `np.random.RandomState(seed)`. Pin the seed-42 scenario hash regression test before touching any generator file.

5. **Schema changes break 133 existing tests** — Adding new required fields to `ALERT_SCHEMA` invalidates all existing `_make_scenario()` fixtures. All new fields must go in `_meta` (not schema-validated) or be optional with defaults. Run the full test suite after every schema.py change before proceeding.

---

## Implications for Roadmap

The user-specified build order is: schema → visual → contradictory → temporal → scoring → CLI → protocol. This matches the dependency graph from ARCHITECTURE.md and is confirmed correct.

### Phase 1: Schema v3
**Rationale:** Every downstream generator and validator needs the new field definitions. Schema changes are purely additive (enum expansion, required relaxation, optional `_meta` fields) and carry the highest regression risk if done later. This phase also resolves the three-way design conflict on visual-only field handling — STACK.md (sentinels), ARCHITECTURE.md (nulls), and PITFALLS.md (shared pools) all recommend different approaches; the leakage test constraint settles it in favor of shared pools.
**Delivers:** Extended `ALERT_SCHEMA` with new track values; relaxed required array for visual tracks; `_meta` v3 fields (visual_gt_source, contradictory, sequence_id, sequence_position, sequence_length, generation_version: v3); track-aware validation in `validation.py`
**Addresses:** Table stakes — sequence group identifier; visual-only schema prerequisite
**Avoids:** Pitfall 9 (schema breaks existing tests), Pitfall 1 (leakage design conflict resolved explicitly)

### Phase 2: Visual-Only Scenarios
**Rationale:** Simpler than contradictory; serves as reference implementation for the visual track pattern before harder cases. Unblocked by schema phase. Does not depend on contradictory or temporal work.
**Delivers:** `VisualOnlyGenerator` class; UCF Crime-only visual-only scenarios; GT from `UCF_CATEGORY_MAP`; `visual_gt_source = "video_category"` in `_meta`; class balance audit against UCF Crime distribution
**Addresses:** Table stakes — visual-only scenario generation
**Avoids:** Pitfall 4 (RNG isolation), Pitfall 6 (class imbalance — compute and document distribution), Pitfall 11 (Caltech excluded from visual-only in v3.0)

### Phase 3: Contradictory Scenarios
**Rationale:** Depends on visual-only generator as reference implementation and on new description pools in `distributions.py`. The primary research contribution. Natural follow from visual-only since both use `video_category` GT.
**Delivers:** `CONTRADICTORY_THREAT_DESCRIPTIONS` and `CONTRADICTORY_BENIGN_DESCRIPTIONS` pools in `distributions.py`; `ContradictoryGenerator` class; `_meta.contradictory = True` plus dual GT storage; test asserting `metadata_derived_gt != video_derived_gt` for all contradictory scenarios
**Addresses:** Differentiator — contradictory scenarios (visual overrides metadata); table stakes — contradictory flag
**Avoids:** Pitfall 2 (GT must come from video category, not metadata signals), Pitfall 7 (descriptions must be plausible-but-wrong, not obviously wrong)

### Phase 4: Temporal Sequences
**Rationale:** Largest new component; independent of visual/contradictory work (temporal scenarios use metadata signals, not video GT). Isolated so it can slip without blocking visual track delivery. Highest implementation risk in the milestone.
**Delivers:** `TemporalSequenceGenerator` class; sequences of 3-5 linked alerts with `sequence_id`, `sequence_position`, escalating/de-escalating GT narrative; varied escalation points (not fixed position); monotonically increasing timestamps
**Addresses:** Table stakes — sequence GT that evolves across alerts; differentiator — temporal escalation patterns
**Avoids:** Pitfall 3 (keep per-alert scoring unchanged), Pitfall 8 (vary escalation point; add position-stump leakage test), Pitfall 12 (timestamps must be strictly increasing)

### Phase 5: Scoring Updates
**Rationale:** Scoring depends on scenarios existing to test against. Adds track partitioning, sequence scoring, and perception-reasoning gap metric without touching the existing `score_run()` contract.
**Delivers:** Track partitioning in `_score_partition` (visual_only, visual_contradictory, temporal breakdowns in dashboard); `SequenceScoreReport` dataclass; `score_sequences()` function; perception-reasoning gap metric (derived from matched contradictory scenario comparisons)
**Addresses:** Table stakes — visual track scoring; temporal scoring; differentiator — perception-reasoning gap metric
**Avoids:** Pitfall 3 (score_sequences is separate from score_run; all 133 tests unchanged)

### Phase 6: CLI Extensions
**Rationale:** CLI is the last code layer; depends on generators and scoring being stable. Purely additive — no existing commands change signature.
**Delivers:** Extended `--track` choices in `generate` command; `score-sequences` subcommand; `analyze-frame-gap` subcommand
**Addresses:** Table stakes — frame extraction baseline (as protocol tool, not code)
**Avoids:** Pitfall 10 (video-dir override for path remapping in analyze-frame-gap)

### Phase 7: Evaluation Protocol Document
**Rationale:** No code dependencies. Written after visual-only scenarios exist so the protocol can reference the exact scenario format and schema fields. Documents the decisions made across all prior phases.
**Delivers:** `docs/EVALUATION_PROTOCOL.md` — GT definition for each track; frame extraction baseline specification (uniform N-frame sampling, never using `anomaly_segments` for selection, deterministic given seed); scoring protocol for sequences; cross-track comparison guidelines; Caltech scope limitation for visual-only
**Addresses:** Differentiator — evaluation protocol document
**Avoids:** Pitfall 5 (keyframe strategy specified precisely, never annotation-guided)

### Phase Ordering Rationale

- Schema first because it unblocks all generators and validators; doing it later risks breaking in-progress generator code
- Visual before contradictory because contradictory builds on visual's `video_category` GT pattern; doing them together increases risk of the GT design error (Pitfall 2)
- Temporal isolated from visual/contradictory because temporal uses metadata signals (not video GT) — the two tracks have no runtime dependency on each other, and isolation lets temporal slip without affecting the visual milestone
- Scoring after generators because scoring tests require generated scenarios; the partition logic depends on which tracks exist
- CLI last because it exposes what's stable; adding subcommands before scoring is done risks shipping a command that errors on the first run
- Protocol last because it documents what was actually built, including decisions that resolve during implementation

### Research Flags

Phases with well-documented patterns (standard implementation, no deeper research needed):
- **Phase 1 (Schema):** Additive JSON Schema extension is a solved pattern; backward-compat rules are explicit in jsonschema docs
- **Phase 5 (Scoring):** Partition-by-field pattern already exists in `_score_partition`; adding a sibling function is straightforward
- **Phase 6 (CLI):** click subcommand extension is well-documented

Phases that may need validation during implementation:
- **Phase 2 (Visual-Only):** Leakage test behavior on visual-only subset is untested until the generator exists; run `test_leakage.py` immediately after first generation batch
- **Phase 4 (Temporal):** `early_detection_rate` threshold (first 2 alerts) needs validation once temporal scenarios exist; not calibrated against real data
- **Phase 5 (Scoring):** UCF Crime class distribution audit needed before publishing cross-track comparisons; distribution-adjusted reporting may be required

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All decisions traceable to PyPI release dates and pip install constraints; decord abandonment confirmed; opencv-python-headless wheels confirmed for target Python matrix |
| Features | HIGH | Derived from direct VISION.md spec plus code inspection of what the stub VisualGenerator currently does; gaps between spec and implementation clearly identified |
| Architecture | HIGH | All claims traceable to specific file/line; required array and GT function call chain directly observed in schema.py, generators.py, scorer.py |
| Pitfalls | HIGH | Derived from direct code inspection including test_leakage.py stump threshold, test_core.py fixture patterns, and distributions.py pool contents |

**Overall confidence:** HIGH

### Gaps to Address During Implementation

- **Leakage test behavior on visual-only subset:** Predicted to pass with shared description pools; not empirically confirmed until the generator exists. Run `test_leakage.py` immediately after first generation batch and tune pool sampling if needed.

- **Temporal escalation threshold calibration:** `early_detection_rate` defined as "THREAT detected within first 2 alerts of a threat sequence." This threshold is reasonable but arbitrary until real temporal scenarios exist. Validate during Phase 4 and adjust `SequenceScoreReport` field definitions before Phase 5.

- **UCF Crime class distribution for visual track:** 150 normal / 290 total = 51.7% BENIGN before mapping; actual distribution depends on `UCF_CATEGORY_MAP` thresholds. Compute in Phase 2 before Phase 5 cross-track comparisons are built. May require stratified subsampling.

- **Track-aware validation in `validation.py`:** ARCHITECTURE.md inferred the extension pattern from test_core.py without reading validation.py in full. Read validation.py at the start of Phase 1 to confirm the pattern before writing track-aware logic.

- **Contradictory description subtlety calibration:** Pitfall 7 warns that algorithmic flipping produces obviously wrong descriptions. The CONTRADICTORY_*_DESCRIPTIONS pools must be hand-curated or human-reviewed before use. Budget for a review pass in Phase 3.

---

## Sources

### Primary (HIGH confidence — direct code inspection or official sources)
- PSAI-Bench `psai_bench/schema.py` — ALERT_SCHEMA required array, track enum
- PSAI-Bench `psai_bench/generators.py` — VisualGenerator, MetadataGenerator, VisualTrackMapper coupling
- PSAI-Bench `psai_bench/scorer.py` — score_run flat-list assumption, _score_partition pattern
- PSAI-Bench `psai_bench/distributions.py` — assign_ground_truth_v2, DESCRIPTION_POOL_AMBIGUOUS
- PSAI-Bench `psai_bench/baselines.py` — baseline structure, API-dependency exclusion
- PSAI-Bench `tests/test_leakage.py` — stump accuracy threshold (70%), leakage test design
- PSAI-Bench `.planning/VISION.md` — v3.0 feature definitions and design intent
- PSAI-Bench `.planning/PROJECT.md` — no-new-deps constraint, 133-test regression requirement
- opencv-python-headless PyPI — version 4.13.0.92, released 2026-02-05, Python 3.7–3.13 wheels confirmed

### Secondary (MEDIUM confidence — well-established external patterns)
- GroundLie360 (2025): https://arxiv.org/html/2509.08008v1 — contradictory text-video benchmark pattern from misinformation domain; same mechanism applied to security triage
- Video-MME / AKS (CVPR 2025): https://arxiv.org/abs/2502.21271 — frame extraction vs full-video gap; keyframe baseline patterns
- TSB-AD benchmark: https://github.com/TheDatumOrg/TSB-AD — VUS-PR metric identified as inappropriate for discrete alert sequences

### Tertiary (referenced, not independently verified)
- Snyk decord health report — maintenance status: Inactive (confirmed by PyPI last-release date)
- KDD 2025 survey on time-series anomaly detection — scoring patterns for alert-based evaluation

---
*Research completed: 2026-04-13*
*Ready for roadmap: yes*
