---
phase: 09-scoring-and-schema-updates
verified: 2026-04-13T00:00:00Z
status: passed
score: 13/13 must-haves verified
overrides_applied: 0
---

# Phase 9: Scoring and Schema Updates Verification Report

**Phase Goal:** Scoring reports a transparent metrics dashboard instead of a single opaque aggregate, ambiguous scenarios are handled separately, and the output schema accepts minimal non-LLM outputs
**Verified:** 2026-04-13
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

Roadmap Success Criteria verified:

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `psai-bench score` outputs a dashboard showing TDR, FASR, Decisiveness, Calibration (ECE), and per-difficulty accuracy as separate labeled values | VERIFIED | `cli.py` score command calls `format_dashboard(report)` via `click.echo`; `format_dashboard` produces labeled rows for TDR, FASR, Decisiveness, Calibration (ECE), per-difficulty accuracy |
| 2 | A Decisiveness metric is present in output, defined as fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS) | VERIFIED | `ScoreReport.decisiveness` field set in `_score_partition()` as `(pred == "THREAT") | (pred == "BENIGN")).mean()`; printed as labeled row in `format_dashboard` |
| 3 | If an aggregate score is shown, its formula is printed alongside it with documented weights | VERIFIED | `format_dashboard` emits `"  Formula: 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)"` immediately before the score value |
| 4 | `psai-bench score` does not penalize THREAT/BENIGN verdicts on ambiguous scenarios — ambiguous scenarios shown in a separate bucket | VERIFIED | `score_run()` partitions on `_meta.ambiguity_flag`; non-ambiguous partition is the main report; ambiguous partition scored as `report.ambiguous_report`; `format_dashboard` shows ambiguous bucket section when `amb.n_scenarios > 0` |
| 5 | A minimal output file with only `alert_id`, `verdict`, and `confidence` passes schema validation | VERIFIED | `OUTPUT_SCHEMA["required"] == ["alert_id", "verdict", "confidence"]`; `validate_output({"alert_id": "test-1", "verdict": "THREAT", "confidence": 0.9})` raises no exception |

Plan must-haves verified (consolidated):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | An output without reasoning passes schema validation without error | VERIFIED | `reasoning` removed from `OUTPUT_SCHEMA["required"]`; `minLength` constraint absent from reasoning property |
| 7 | An output without processing_time_ms passes schema validation without error | VERIFIED | `processing_time_ms` removed from `OUTPUT_SCHEMA["required"]` |
| 8 | The confidence field has description "probability that the verdict is correct" | VERIFIED | `OUTPUT_SCHEMA["properties"]["confidence"]["description"] == "probability that the verdict is correct"` |
| 9 | validation.py does not warn on missing reasoning — only on present-but-short reasoning | VERIFIED | Line 105-106: `reasoning = out.get("reasoning"); if reasoning and len(reasoning.split()) < 20:` — absent reasoning skips the check |
| 10 | The SUSPICIOUS fraction warning no longer references a penalty | VERIFIED | Warning message: `"High SUSPICIOUS fraction reduces Decisiveness metric."` — no "penalty" word |
| 11 | Scoring excludes ambiguous scenarios from main metrics and aggregate | VERIFIED | `score_run()` partitions; `_score_partition(non_ambiguous, outputs)` produces main report; n_ambiguous tracked separately |
| 12 | format_dashboard() returns a string with no external dependency imports | VERIFIED | `format_dashboard` in `scorer.py` uses only f-strings and list joining; `tabulate` not imported anywhere in `cli.py` |
| 13 | score_multiple_runs() includes decisiveness in key_metrics | VERIFIED | `key_metrics` list in `score_multiple_runs()` includes `"decisiveness"` |

**Score:** 13/13 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `psai_bench/schema.py` | Simplified OUTPUT_SCHEMA with optional reasoning and processing_time_ms | VERIFIED | `required: ["alert_id", "verdict", "confidence"]`; no `minLength` on reasoning; confidence has description |
| `psai_bench/validation.py` | Updated reasoning check (conditional) and SUSPICIOUS fraction message | VERIFIED | Reasoning check guarded with `if reasoning and ...`; SUSPICIOUS warning references Decisiveness |
| `psai_bench/scorer.py` | Partition-then-score with ambiguous handling, Decisiveness, new aggregate, format_dashboard() | VERIFIED | All four changes implemented and functional |
| `psai_bench/cli.py` | CLI wiring for format_dashboard, removal of _print_report_table and analyze_suspicious_cap | VERIFIED | score and baselines commands call `format_dashboard()`; `_print_report_table` absent; `analyze_suspicious_cap` absent; no `tabulate` import |
| `tests/test_core.py` | TestDecisiveness, TestAmbiguousHandling, TestDashboard classes; rewritten aggregate test; deleted TestSuspiciousPenalty | VERIFIED | All four new test classes present; `TestSuspiciousPenalty` absent; `test_aggregate_new_formula` present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `psai_bench/schema.py` | `psai_bench/validation.py` | `validate_output()` called inside `validate_submission()` | VERIFIED | Line 111: `validate_output(out)` called in `validate_submission()` loop |
| `psai_bench/cli.py::score` | `psai_bench/scorer.py::format_dashboard` | `from psai_bench.scorer import format_dashboard; click.echo(format_dashboard(report))` | VERIFIED | Lines 102-103 of cli.py |
| `psai_bench/cli.py::baselines` | `psai_bench/scorer.py::format_dashboard` | `from psai_bench.scorer import format_dashboard; click.echo(format_dashboard(report))` | VERIFIED | Lines 142-146 of cli.py |
| `psai_bench/scorer.py::score_run` | `psai_bench/scorer.py::_score_partition` | `score_run` partitions scenarios and delegates to `_score_partition` | VERIFIED | `_score_partition(non_ambiguous, outputs)` and `_score_partition(ambiguous, outputs)` called in `score_run` |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `format_dashboard` | `report.tdr`, `report.fasr`, `report.decisiveness`, `report.ece`, `report.aggregate_score` | `_score_partition()` vectorized numpy computation over scenario/output pairs | Yes — computed from actual ground-truth and prediction arrays | FLOWING |
| `score_run` | `main_report`, `amb_report` | `_score_partition(non_ambiguous, outputs)` and `_score_partition(ambiguous, outputs)` | Yes — both partitions scored from real data | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Result | Status |
|----------|--------|--------|
| `OUTPUT_SCHEMA["required"] == ["alert_id", "verdict", "confidence"]` | Confirmed | PASS |
| `validate_output({"alert_id": "x", "verdict": "THREAT", "confidence": 0.9})` raises no exception | No exception | PASS |
| `ScoreReport` has `decisiveness`, `n_ambiguous`, `ambiguous_report` fields | All present | PASS |
| `to_dict()` with nested `ScoreReport` serializes via `json.dumps()` without error | Serializes cleanly | PASS |
| `format_dashboard()` returns string containing TDR, FASR, Decisiveness, "Formula", "0.4*TDR" | All present | PASS |
| `format_dashboard()` with `ambiguous_report.n_scenarios > 0` shows ambiguous bucket | Shown | PASS |
| Absent reasoning in output — no validation warning | No warning emitted | PASS |
| Present but short reasoning in output — warning emitted | Warning emitted | PASS |
| SUSPICIOUS fraction warning text contains "Decisiveness", not "penalty" | Correct text | PASS |
| `tabulate` absent from `cli.py` | Confirmed absent | PASS |
| `_print_report_table` absent from `cli.py` | Confirmed absent | PASS |
| `analyze_suspicious_cap` absent from `cli.py` | Confirmed absent | PASS |
| `score_multiple_runs` key_metrics includes "decisiveness" | Confirmed | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCORE-01 | 09-02, 09-03 | Metrics reported as a dashboard (TDR, FASR, Decisiveness, Calibration, per-difficulty accuracy) — not collapsed into a single opaque aggregate | SATISFIED | `format_dashboard()` in `scorer.py` produces labeled rows for each metric; wired to `score` and `baselines` CLI commands |
| SCORE-02 | 09-02, 09-03 | Decisiveness metric replaces SUSPICIOUS penalty: fraction of predictions that are THREAT or BENIGN | SATISFIED | `ScoreReport.decisiveness` computed in `_score_partition()` as decisive predictions / total; `suspicious_penalty` zeroed out |
| SCORE-03 | 09-02, 09-03 | If aggregate score is computed, it uses published additive weights with documented justification | SATISFIED | `aggregate_score = 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)`; formula printed in dashboard output |
| SCORE-04 | 09-02, 09-03 | Scoring handles ambiguous-flagged scenarios separately | SATISFIED | `score_run()` partitions on `_meta.ambiguity_flag`; ambiguous partition returned as `report.ambiguous_report` |
| SCHEMA-01 | 09-01 | Reasoning field is optional (not required, no minimum word count) | SATISFIED | `reasoning` absent from `OUTPUT_SCHEMA["required"]`; `minLength` removed from reasoning property |
| SCHEMA-02 | 09-01 | Confidence field definition is explicit: "probability that the verdict is correct" | SATISFIED | `OUTPUT_SCHEMA["properties"]["confidence"]["description"]` set to that exact string |
| SCHEMA-03 | 09-01 | Processing_time_ms is optional | SATISFIED | `processing_time_ms` absent from `OUTPUT_SCHEMA["required"]` |
| SCHEMA-04 | 09-01 | Schema validates correctly for minimal outputs (alert_id + verdict + confidence only) | SATISFIED | `validate_output({"alert_id": "test-1", "verdict": "THREAT", "confidence": 0.9})` raises no exception |

All 8 requirements (SCORE-01 through SCORE-04, SCHEMA-01 through SCHEMA-04) are SATISFIED.

---

### Anti-Patterns Found

No blockers found. Spot-checks on modified files confirm:

- No `TODO` or `FIXME` in schema.py, validation.py, scorer.py, or cli.py for the changes made in this phase
- No empty implementations (`return null`, `return []`) in the new scoring logic
- `format_dashboard()` returns a fully-built string from all ScoreReport fields — no hardcoded empty data
- `decisive_mask.mean()` computes a real ratio from partition predictions, not a constant

---

### Human Verification Required

None. All truths verified programmatically.

---

### Gaps Summary

No gaps. All 13 must-have truths are verified. All 8 requirements are satisfied. The phase goal is achieved:

1. **Transparent metrics dashboard:** `format_dashboard()` reports TDR, FASR, Decisiveness, Calibration (ECE), and per-difficulty accuracy as separately labeled values.
2. **Ambiguous scenarios handled separately:** `score_run()` partitions on `_meta.ambiguity_flag`; ambiguous scenarios are scored in `report.ambiguous_report` and excluded from the main aggregate.
3. **Minimal non-LLM outputs accepted:** `OUTPUT_SCHEMA["required"]` is `["alert_id", "verdict", "confidence"]`; reasoning and processing_time_ms are optional.

Test suite confirms: 129 tests pass, 0 failures.

---

_Verified: 2026-04-13_
_Verifier: Claude (gsd-verifier)_
