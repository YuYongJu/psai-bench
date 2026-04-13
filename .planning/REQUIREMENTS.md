# Requirements: PSAI-Bench v3.0

**Defined:** 2026-04-13
**Core Value:** Non-trivially-solvable benchmark where no single input field reveals ground truth — now extended to test whether video perception adds value over metadata-only triage

## v3.0 Requirements

### Schema & Infrastructure

- [ ] **INFRA-01**: Schema v3 extends track enum to include `visual_only`, `visual_contradictory`, `temporal`
- [ ] **INFRA-02**: `severity` and `description` are no longer required at schema level — enforced per-track in validation
- [ ] **INFRA-03**: `_meta` v3 adds `visual_gt_source`, `contradictory`, `sequence_id`, `sequence_position` fields
- [ ] **INFRA-04**: Seed-42 regression hash pinned before any generator changes

### Visual-Only Track

- [ ] **VIS-01**: `VisualOnlyGenerator` produces scenarios with video URI + minimal metadata (timestamp, camera ID only)
- [ ] **VIS-02**: Visual-only scenario GT derived from video content label, not metadata signals
- [ ] **VIS-03**: Visual-only scenarios use shared description pools (not sentinel values) to avoid leakage
- [ ] **VIS-04**: `psai-bench generate --track visual_only` CLI command produces visual-only scenario files

### Contradictory Track

- [ ] **CONTRA-01**: `ContradictoryGenerator` produces scenarios where metadata and video content disagree
- [ ] **CONTRA-02**: Two sub-types: overreach (metadata=THREAT, video=BENIGN) and underreach (metadata=BENIGN, video=THREAT)
- [ ] **CONTRA-03**: GT always follows video content, never metadata — `_meta.contradictory=true` flag present
- [ ] **CONTRA-04**: Contradictory description pools added to `distributions.py`

### Temporal Sequences

- [ ] **TEMP-01**: `TemporalSequenceGenerator` produces groups of 3-5 related alerts with `sequence_id` threading
- [ ] **TEMP-02**: At least 3 escalation pattern types: monotonic escalation, escalation-then-resolution, false alarm sequence
- [ ] **TEMP-03**: `score_sequences()` function with `SequenceScoreReport` — escalation latency, correct-escalation rate, correct-resolution rate
- [ ] **TEMP-04**: `psai-bench generate --track temporal` CLI command produces temporal sequence files

### Scoring & Validation

- [ ] **SCORE-01**: Scorer partitions results by track (metadata, visual_only, contradictory, temporal) in dashboard
- [ ] **SCORE-02**: Perception-reasoning gap metric computed when both metadata and visual results exist
- [ ] **SCORE-03**: `score_run()` unchanged — new scoring is additive via `score_sequences()` and track partitioning
- [ ] **SCORE-04**: Validation enforces track-specific required fields

### Frame Extraction & Protocol

- [ ] **FRAME-01**: `opencv-python-headless` added as optional `[visual]` dependency in pyproject.toml
- [ ] **FRAME-02**: Frame extraction baseline extracts keyframes without using `anomaly_segments`
- [ ] **FRAME-03**: `analyze-frame-gap` CLI command computes perception-reasoning gap from two result files
- [ ] **PROTO-01**: `docs/EVALUATION_PROTOCOL.md` documents GT definitions, scoring protocol, and sequence evaluation rules

### Testing

- [ ] **TEST-01**: All existing 133 tests pass (no regressions)
- [ ] **TEST-02**: Visual-only scenarios pass leakage tests (no single field >70% stump accuracy)
- [ ] **TEST-03**: Contradictory scenario GT always follows video label (automated verification)
- [ ] **TEST-04**: Temporal sequence scoring produces expected metrics for known patterns
- [ ] **TEST-05**: Backward compatibility — `generate --version v2` still produces identical output

## v4.0 Requirements (Deferred)

### Dispatch Decisions
- **DISP-01**: 5-class dispatch decisions (armed response, patrol, operator review, auto-suppress, request data)
- **DISP-02**: Cost-aware scoring with per-action cost model

### Multi-Site Generalization
- **SITE-01**: Cross-site generalization testing (train on solar, test on commercial)

### Adversarial Robustness
- **ADV-01**: Evasion attack scenarios (loitering as waiting, authorized as intrusion)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Running model evaluations | User's job — benchmark provides scenarios and scoring only |
| Web dashboard | CLI-first design |
| Multi-annotator GT | Requires human annotators — out of scope |
| Caltech visual-only scenarios | No video annotations exist for Caltech Camera Traps |
| Real-time video processing | Benchmark is offline evaluation, not streaming |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Pending | Pending |
| INFRA-02 | Pending | Pending |
| INFRA-03 | Pending | Pending |
| INFRA-04 | Pending | Pending |
| VIS-01 | Pending | Pending |
| VIS-02 | Pending | Pending |
| VIS-03 | Pending | Pending |
| VIS-04 | Pending | Pending |
| CONTRA-01 | Pending | Pending |
| CONTRA-02 | Pending | Pending |
| CONTRA-03 | Pending | Pending |
| CONTRA-04 | Pending | Pending |
| TEMP-01 | Pending | Pending |
| TEMP-02 | Pending | Pending |
| TEMP-03 | Pending | Pending |
| TEMP-04 | Pending | Pending |
| SCORE-01 | Pending | Pending |
| SCORE-02 | Pending | Pending |
| SCORE-03 | Pending | Pending |
| SCORE-04 | Pending | Pending |
| FRAME-01 | Pending | Pending |
| FRAME-02 | Pending | Pending |
| FRAME-03 | Pending | Pending |
| PROTO-01 | Pending | Pending |
| TEST-01 | Pending | Pending |
| TEST-02 | Pending | Pending |
| TEST-03 | Pending | Pending |
| TEST-04 | Pending | Pending |
| TEST-05 | Pending | Pending |

**Coverage:**
- v3.0 requirements: 29 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 29

---
*Requirements defined: 2026-04-13*
