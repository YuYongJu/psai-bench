# Requirements: PSAI-Bench v2.0

**Defined:** 2026-04-13
**Core Value:** Non-trivially-solvable benchmark where no single input field reveals ground truth

## v2.0 Requirements

### Scenario Generation

- [ ] **SCEN-01**: Ground truth is determined by a documented decision function combining description + zone + time + device + severity, not by category alone
- [ ] **SCEN-02**: Description pool is shared across all GT classes — same description appears with THREAT, SUSPICIOUS, and BENIGN ground truth in different contexts
- [ ] **SCEN-03**: Severity correlates with ground truth at ~70% (not 100%) — some scenarios have deliberately misleading severity
- [ ] **SCEN-04**: Adversarial scenarios exist with 2+ conflicting signals (e.g., HIGH severity + BENIGN GT, LOW severity + THREAT GT, night + restricted zone + recent badge = BENIGN)
- [ ] **SCEN-05**: Single-field decision stump accuracy is below 70% for every field (description, severity, zone, time, device FPR) — verified by automated test
- [ ] **SCEN-06**: Site-inappropriate categories are eliminated (no shoplifting at solar farms, no road accidents indoors)
- [ ] **SCEN-07**: Default parameters (seed=42, no flags) still produce v1.0-compatible output for backward compatibility

### Ground Truth

- [ ] **GT-01**: Published decision rubric document explains the ground truth assignment logic with worked examples
- [ ] **GT-02**: Scenarios flagged as "ambiguous by design" (reasonable operators would disagree) get GT=SUSPICIOUS with an ambiguity flag in _meta
- [ ] **GT-03**: Ground truth assignment function is deterministic given scenario context (not random)

### Scoring

- [ ] **SCORE-01**: Metrics reported as a dashboard (TDR, FASR, Decisiveness, Calibration, per-difficulty accuracy) — not collapsed into a single opaque aggregate
- [ ] **SCORE-02**: Decisiveness metric replaces SUSPICIOUS penalty: fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS)
- [ ] **SCORE-03**: If aggregate score is computed, it uses published additive weights with documented justification
- [ ] **SCORE-04**: Scoring handles ambiguous-flagged scenarios separately (system that says THREAT or BENIGN on an ambiguous scenario is not penalized — it made a decisive call under uncertainty)

### Output Schema

- [ ] **SCHEMA-01**: Reasoning field is optional (not required, no minimum word count)
- [ ] **SCHEMA-02**: Confidence field definition is explicit in schema: "probability that the verdict is correct"
- [ ] **SCHEMA-03**: Processing_time_ms is optional
- [ ] **SCHEMA-04**: Schema validates correctly for minimal outputs (alert_id + verdict + confidence only)

### Documentation

- [ ] **DOCS-01**: README reframed around "Bring Your Own System" workflow: generate → run YOUR system → score
- [ ] **DOCS-02**: Built-in evaluators documented as reference implementations / examples, not the canonical path
- [ ] **DOCS-03**: Decision rubric published as a standalone document
- [ ] **DOCS-04**: Results table updated with v2.0 scenarios (or removed if no evaluations run yet)
- [ ] **DOCS-05**: Known limitations section honest about what v2.0 does and doesn't test

### Testing

- [ ] **TEST-01**: Automated test verifies no single field achieves >70% decision stump accuracy on generated scenarios
- [ ] **TEST-02**: Tests verify decision rubric produces expected GT for known scenario configurations
- [ ] **TEST-03**: Tests verify backward compatibility — default params produce same output as v1.0
- [ ] **TEST-04**: Tests verify ambiguous-flagged scenarios have correct metadata

## v3.0 Requirements (Deferred)

### Visual Track

- **VIS-01**: Visual-only scenarios (no description/severity, just video + minimal metadata)
- **VIS-02**: Contradictory scenarios (metadata says X, video shows Y)
- **VIS-03**: Frame extraction baseline for comparison

### Temporal

- **TEMP-01**: Alert sequences (3-5 related alerts building a narrative)
- **TEMP-02**: Escalation pattern testing

## Out of Scope

| Feature | Reason |
|---------|--------|
| Running model evaluations | User's job — benchmark provides scenarios and scoring only |
| Web dashboard | CLI-first design; not needed for v2.0 |
| Dispatch decisions (5 action types) | v4.0 — requires operational research |
| Cost-aware scoring ($/decision) | v4.0 — requires cost model |
| Video processing implementation | v3.0 — requires visual track redesign |
| Adversarial robustness (evasion attacks) | v4.0 |
| Multi-annotator ground truth | Would be ideal but requires human annotators — out of scope |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCEN-01 | Phase 6 | Pending |
| SCEN-02 | Phase 6 | Pending |
| SCEN-03 | Phase 6 | Pending |
| SCEN-04 | Phase 6 | Pending |
| SCEN-05 | Phase 7 | Pending |
| SCEN-06 | Phase 6 | Pending |
| SCEN-07 | Phase 7 | Pending |
| GT-01 | Phase 8 | Pending |
| GT-02 | Phase 6 | Pending |
| GT-03 | Phase 6 | Pending |
| SCORE-01 | Phase 9 | Pending |
| SCORE-02 | Phase 9 | Pending |
| SCORE-03 | Phase 9 | Pending |
| SCORE-04 | Phase 9 | Pending |
| SCHEMA-01 | Phase 9 | Pending |
| SCHEMA-02 | Phase 9 | Pending |
| SCHEMA-03 | Phase 9 | Pending |
| SCHEMA-04 | Phase 9 | Pending |
| DOCS-01 | Phase 10 | Pending |
| DOCS-02 | Phase 10 | Pending |
| DOCS-03 | Phase 10 | Pending |
| DOCS-04 | Phase 10 | Pending |
| DOCS-05 | Phase 10 | Pending |
| TEST-01 | Phase 7 | Pending |
| TEST-02 | Phase 7 | Pending |
| TEST-03 | Phase 7 | Pending |
| TEST-04 | Phase 7 | Pending |

**Coverage:**
- v2.0 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initial definition*
