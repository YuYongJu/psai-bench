# Requirements: PSAI-Bench v4.0

**Defined:** 2026-04-13
**Core Value:** Non-trivially-solvable benchmark extended to operational decision-support — measuring not just "what is this?" but "what should you do about it?"

## v4.0 Requirements

### Schema & Dispatch Foundation

- [ ] **DISP-01**: OUTPUT_SCHEMA adds optional `dispatch` field with 5-class enum (armed_response, patrol, operator_review, auto_suppress, request_data)
- [ ] **DISP-02**: `_meta` adds `optimal_dispatch` field — benchmark-computed optimal action for each scenario
- [ ] **DISP-03**: `_meta` adds `adversarial_type` field distinguishing signal-conflict (v2) from behavioral (v4)
- [ ] **DISP-04**: Existing `verdict` field unchanged — 3-class triage preserved for backward compatibility
- [ ] **DISP-05**: DISPATCH_ACTIONS constant defined in schema.py with all 5 action types

### Cost Model

- [ ] **COST-01**: `cost_model.py` with CostModel dataclass, configurable per-action costs indexed by (dispatch_action, ground_truth) tuple
- [ ] **COST-02**: Default cost profile with provisional values documented as configurable
- [ ] **COST-03**: `compute_optimal_dispatch()` determines optimal action from GT + site context using published decision table
- [ ] **COST-04**: `score_dispatch_run()` computes CostScoreReport with expected cost, optimal cost, cost ratio, per-action breakdown
- [ ] **COST-05**: Cost reported under 3+ cost-ratio assumptions — sensitivity analysis built in

### Scoring & Baselines

- [ ] **SCORE-01**: `score_dispatch_run()` is additive alongside `score_run()` — no modifications to existing scoring functions
- [ ] **SCORE-02**: `format_dashboard()` extended with optional `cost_report` for dispatch cost display
- [ ] **SCORE-03**: All 4 baselines add `dispatch` field via VERDICT_TO_DEFAULT_DISPATCH mapping
- [ ] **SCORE-04**: `compute_site_generalization_gap()` measures per-site accuracy differences using LODO protocol

### Adversarial Robustness

- [ ] **ADV-01**: `AdversarialV4Generator` produces behavioral adversarial scenarios (loitering-as-waiting, authorized-as-intrusion, environmental-as-human)
- [ ] **ADV-02**: New `ADV_V4_*` description pools in distributions.py — separate from existing pools
- [ ] **ADV-03**: `adversarial_v4` track added to ALERT_SCHEMA track enum
- [ ] **ADV-04**: Generator uses `assign_ground_truth_v2` on actual signals (GT from context, not narrative)

### Multi-Site Generalization

- [ ] **SITE-01**: `--site-type` CLI filter for post-generation site-specific scenario extraction
- [ ] **SITE-02**: Site leakage audit confirms site_type cannot be inferred from non-site features
- [ ] **SITE-03**: Generalization gap metric and `site-generalization` CLI command

### Testing & Documentation

- [ ] **TEST-01**: All 238 existing tests pass (no regressions)
- [ ] **TEST-02**: Dispatch scoring tests verify cost computation for known scenarios
- [ ] **TEST-03**: Adversarial v4 generation tests verify behavioral pattern presence
- [ ] **TEST-04**: Multi-site filtering preserves seed reproducibility
- [ ] **TEST-05**: Backward compatibility — v1/v2/v3 output files score correctly without dispatch field
- [ ] **DOC-01**: Dispatch decision rubric published (GT × site_context → optimal_dispatch table)
- [ ] **DOC-02**: Updated EVALUATION_PROTOCOL.md with dispatch scoring and cost model documentation

## v5.0 Requirements (Deferred)

- Real-time streaming evaluation protocol
- Multi-language scenario descriptions
- Human-in-the-loop ground truth annotation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Running model evaluations | User's job — benchmark provides scenarios and scoring only |
| Web dashboard | CLI-first design |
| Replacing 3-class verdict | Backward compatibility — dispatch is additive |
| Pixel-perturbation adversarial | PSAI-Bench tests semantic/behavioral adversarial, not input perturbations |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DISP-01 | Phase 18 | Pending |
| DISP-02 | Phase 18 | Pending |
| DISP-03 | Phase 18 | Pending |
| DISP-04 | Phase 18 | Pending |
| DISP-05 | Phase 18 | Pending |
| COST-01 | Phase 18 | Pending |
| COST-02 | Phase 18 | Pending |
| COST-03 | Phase 18 | Pending |
| COST-04 | Phase 18 | Pending |
| COST-05 | Phase 18 | Pending |
| DOC-01 | Phase 18 | Pending |
| SCORE-01 | Phase 19 | Pending |
| SCORE-02 | Phase 19 | Pending |
| SCORE-03 | Phase 19 | Pending |
| ADV-01 | Phase 20 | Pending |
| ADV-02 | Phase 20 | Pending |
| ADV-03 | Phase 20 | Pending |
| ADV-04 | Phase 20 | Pending |
| SITE-01 | Phase 21 | Pending |
| SITE-02 | Phase 21 | Pending |
| SITE-03 | Phase 21 | Pending |
| SCORE-04 | Phase 21 | Pending |
| TEST-01 | Phase 22 | Pending |
| TEST-02 | Phase 22 | Pending |
| TEST-03 | Phase 22 | Pending |
| TEST-04 | Phase 22 | Pending |
| TEST-05 | Phase 22 | Pending |
| DOC-02 | Phase 22 | Pending |

**Coverage:**
- v4.0 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

---
*Requirements defined: 2026-04-13*
*Traceability updated: 2026-04-13 after roadmap creation*
