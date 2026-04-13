# Phase 9: Scoring and Schema Updates - Research

**Researched:** 2026-04-13
**Domain:** Python scoring engine, JSON Schema validation, CLI output formatting
**Confidence:** HIGH (all findings verified directly from codebase)

## Summary

Phase 9 modifies five files: `scorer.py`, `schema.py`, `cli.py`, `validation.py`, and `tests/test_core.py`. All changes are self-contained within the scoring and schema subsystem. The codebase is well-structured and the required changes are surgical.

The primary risk is test breakage: at least 6 existing tests assert behavior that this phase explicitly inverts. The planner must sequence test updates as a distinct wave, not an afterthought. Missing this will cause the suite to fail mid-phase and create confusion about what is broken vs intentionally changed.

The secondary risk is a silent dependency contradiction: CONTEXT.md specifies "no external dependencies" for dashboard output, but the existing `_print_report_table` function imports `tabulate`. The new `format_dashboard()` function must not import `tabulate`, and the old function must be replaced rather than supplemented.

**Primary recommendation:** Implement in four ordered waves — (1) schema.py changes, (2) scorer.py changes, (3) cli.py wiring, (4) test updates. Do not mix schema and test changes in the same wave.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- CLI table output via `print()` with labeled rows — clean, grep-able, no external dependencies
- Keep aggregate score but print the formula alongside it: `Aggregate = 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` with configurable weights
- Decisiveness = fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS)
- New `format_dashboard()` function in `scorer.py` — keeps scoring and display co-located
- Dashboard shows: TDR, FASR, Decisiveness, Calibration (ECE), per-difficulty accuracy as separate labeled values
- Compute metrics twice: main metrics EXCLUDE ambiguous scenarios, then a separate "Ambiguous Bucket" section shows performance on those
- Ambiguous scenarios do NOT affect the aggregate score
- Detect ambiguous scenarios via `_meta.ambiguity_flag == True` (set by Phase 6 generator)
- System that gives THREAT or BENIGN on an ambiguous scenario is not penalized
- Remove `reasoning` from OUTPUT_SCHEMA `required` list, remove `minLength` constraint
- Remove `processing_time_ms` from OUTPUT_SCHEMA `required` list
- Add `description` field to `confidence` in JSON Schema: "probability that the verdict is correct"
- Minimal valid output: `alert_id` + `verdict` + `confidence` only — add test to verify

### Claude's Discretion
- Exact formatting of the dashboard table
- Whether to add a `--format json` flag for machine-readable dashboard output
- Internal refactoring of `score_run` to support ambiguous exclusion
- Aggregate weight values (suggested 0.4/0.3/0.2/0.1 but can adjust if better justified)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCORE-01 | Metrics reported as a dashboard (TDR, FASR, Decisiveness, Calibration, per-difficulty accuracy) — not collapsed into a single opaque aggregate | New `format_dashboard()` in `scorer.py` replaces `_print_report_table()` in `cli.py`; no external deps |
| SCORE-02 | Decisiveness metric replaces SUSPICIOUS penalty: fraction of predictions that are THREAT or BENIGN (not SUSPICIOUS) | Add `decisiveness` field to `ScoreReport`; remove `suspicious_penalty` / `calibration_factor` as aggregate components |
| SCORE-03 | If aggregate score is computed, it uses published additive weights with documented justification | Rewrite aggregate formula as `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)`; print formula in dashboard |
| SCORE-04 | Scoring handles ambiguous-flagged scenarios separately | Partition on `_meta.ambiguity_flag` inside `score_run`; add `ambiguous_report` to return or separate ScoreReport |
| SCHEMA-01 | Reasoning field is optional (not required, no minimum word count) | Remove `"reasoning"` from `OUTPUT_SCHEMA["required"]`; remove `minLength` from properties |
| SCHEMA-02 | Confidence field definition is explicit in schema: "probability that the verdict is correct" | Add `"description": "probability that the verdict is correct"` to `confidence` property in OUTPUT_SCHEMA |
| SCHEMA-03 | Processing_time_ms is optional | Remove `"processing_time_ms"` from `OUTPUT_SCHEMA["required"]` |
| SCHEMA-04 | Schema validates correctly for minimal outputs (alert_id + verdict + confidence only) | Verified by new test; requires SCHEMA-01 + SCHEMA-03 complete first |
</phase_requirements>

## Standard Stack

### Core (no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | already installed | JSON Schema validation for OUTPUT_SCHEMA | Already used in `schema.py`; `validate_output()` calls it |
| numpy | already installed | Array operations in scorer | Already used throughout `scorer.py` |
| click | already installed | CLI framework | Already used in `cli.py` |

### No New Dependencies Required
The locked decision specifies `print()` for dashboard output — no `tabulate`, no `rich`, no `colorama`. The `format_dashboard()` function must use only Python builtins. [VERIFIED: codebase inspection]

### Tabulate: Must Be Removed from score Path
`cli.py` line 107 imports `tabulate` inside `_print_report_table()`. This function is called by the `score` command (line 102) and the `baselines` command (line 193). The new `format_dashboard()` replaces `_print_report_table()` for the `score` command. The `baselines` command should also use `format_dashboard()` for consistency, which eliminates the need for `tabulate` in those code paths. [VERIFIED: cli.py lines 102-102, 193]

**Note on tabulate:** If `tabulate` is only used in `_print_report_table()` (and not elsewhere), it can potentially be removed from dependencies entirely. Verify with `grep -r "tabulate"` before removing it from pyproject.toml — the `compare` and other commands do not appear to use it. [ASSUMED: other commands don't use tabulate; planner should verify]

## Architecture Patterns

### Pattern 1: Partition-Then-Score
The locked decision requires computing metrics twice — once excluding ambiguous scenarios, once only for them. The cleanest implementation is to partition the scenario list at the top of `score_run()` and call the existing scoring logic on each partition.

```python
# Verified pattern: _meta.ambiguity_flag is a boolean (schema.py line 145)
# _META_SCHEMA_V2 shows: "ambiguity_flag": {"type": "boolean"}
# Partition inside score_run():
non_ambiguous = [s for s in scenarios if not s["_meta"].get("ambiguity_flag", False)]
ambiguous = [s for s in scenarios if s["_meta"].get("ambiguity_flag", False)]

# Score main bucket (used for aggregate)
main_report = _score_partition(non_ambiguous, outputs)
# Score ambiguous bucket (display only, no aggregate impact)
ambiguous_report = _score_partition(ambiguous, outputs) if ambiguous else None
```

Two implementation options for returning both results:
- **Option A (recommended):** Add `ambiguous_report: ScoreReport | None` field to `ScoreReport` — keeps `score_run()` signature unchanged (callers still get one object).
- **Option B:** Return a tuple `(main, ambiguous)` — breaks all existing callers in `cli.py` and `baselines` command.

Option A is safer because it leaves existing callers functional with no changes. [ASSUMED: Option A preferred; planner confirms]

### Pattern 2: format_dashboard() in scorer.py
```python
# No imports needed beyond what scorer.py already has
def format_dashboard(report: ScoreReport, ambiguous_report: ScoreReport | None = None) -> str:
    """Return a formatted metrics dashboard string. No external dependencies."""
    lines = []
    lines.append("=== PSAI-Bench Metrics Dashboard ===")
    lines.append(f"  TDR (Threat Detection Rate):    {report.tdr:.4f}")
    lines.append(f"  FASR (False Alarm Suppression): {report.fasr:.4f}")
    lines.append(f"  Decisiveness:                   {report.decisiveness:.4f}")
    lines.append(f"  Calibration (ECE):              {report.ece:.4f}  (lower is better)")
    lines.append("")
    lines.append("=== Per-Difficulty Accuracy ===")
    lines.append(f"  Easy:   {report.accuracy_easy:.4f}")
    lines.append(f"  Medium: {report.accuracy_medium:.4f}")
    lines.append(f"  Hard:   {report.accuracy_hard:.4f}")
    lines.append("")
    lines.append("=== Aggregate Score ===")
    lines.append("  Formula: 0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)")
    lines.append(f"  Score:   {report.aggregate_score:.4f}")
    if ambiguous_report is not None and ambiguous_report.n_scenarios > 0:
        lines.append("")
        lines.append(f"=== Ambiguous Bucket (N={ambiguous_report.n_scenarios}, excluded from aggregate) ===")
        lines.append(f"  TDR:          {ambiguous_report.tdr:.4f}")
        lines.append(f"  FASR:         {ambiguous_report.fasr:.4f}")
        lines.append(f"  Decisiveness: {ambiguous_report.decisiveness:.4f}")
    return "\n".join(lines)
```

The planner has full discretion on exact formatting. The above is a reference pattern. [ASSUMED: exact formatting TBD]

### Pattern 3: New Aggregate Formula
The current aggregate formula (line 209-213 in scorer.py):
```python
# CURRENT (to be replaced):
report.suspicious_penalty = max(0.0, (report.suspicious_fraction - 0.30) * 2)
report.calibration_factor = max(0.5, 1.0 - report.ece)
report.aggregate_score = (
    report.safety_score_3_1
    * (1 - report.suspicious_penalty)
    * report.calibration_factor
)
```

New formula:
```python
# NEW (additive, weights sum to 1.0):
report.decisiveness = float((pred_non_ambiguous == "THREAT") | 
                            (pred_non_ambiguous == "BENIGN")).mean()
report.aggregate_score = (
    0.4 * report.tdr
    + 0.3 * report.fasr
    + 0.2 * report.decisiveness
    + 0.1 * (1.0 - report.ece)
)
```

The weights 0.4/0.3/0.2/0.1 are user-suggested but Claude has discretion to adjust. They sum to 1.0, which is good practice for interpretability. The formula is additive (not multiplicative), making it transparent. [VERIFIED: CONTEXT.md decisions; formula values ASSUMED as starting point]

### ScoreReport Field Changes
Fields to **add:**
- `decisiveness: float = 0.0` — fraction of (non-ambiguous) predictions that are THREAT or BENIGN

Fields to **remove** (or zero out and deprecate):
- `suspicious_penalty` — replaced by Decisiveness; keep field for backward compat but set to 0.0
- `calibration_factor` — no longer used in aggregate; keep field but set to 0.0

Fields that **survive unchanged:**
- `suspicious_fraction` — still useful diagnostic info, keep
- All primary metrics (tdr, fasr, accuracy, safety_score_*)
- All calibration metrics (ece, brier_score, overconfidence_rate)
- All per-difficulty fields
- `per_dataset_accuracy`, `generalization_gap`
- `confusion_matrix`
- All metadata fields (n_scenarios, n_threats, etc.)
- Latency/cost fields

Fields to **add for ambiguous partition:**
- `n_ambiguous: int = 0` — count of ambiguous scenarios found
- `ambiguous_report: ScoreReport | None = None` — nested report for ambiguous bucket

**Dataclass nesting caveat:** Python dataclasses with mutable defaults require `field(default_factory=...)`. `ScoreReport | None = None` is safe as-is since `None` is immutable. [VERIFIED: existing pattern in ScoreReport uses `field(default_factory=dict)` for dicts]

### Anti-Patterns to Avoid
- **Changing `score_run()` return type:** Returning a tuple would break all existing callers. Use nested field instead.
- **Importing tabulate in format_dashboard():** Violates the "no external dependencies" locked decision.
- **Applying ambiguous exclusion to TDR/FASR individually without a clean partition:** Computing metrics with hand-crafted masks inside the existing monolithic loop would be fragile. Refactor to a `_score_partition()` helper that accepts any list of (scenario, output) pairs.
- **Removing `suspicious_penalty` and `calibration_factor` fields from ScoreReport:** These fields appear in `to_dict()` output and may be consumed by downstream tools. Zero them out and leave the fields in place rather than deleting them.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON Schema validation | Custom `if` checks on output dict | `jsonschema.validate()` (already used) | Already in codebase; handles nested schema, type coercion, error messages |
| Dashboard text formatting | ASCII box-drawing characters, padding arithmetic | Simple `f-string` rows with `print()` | Simpler is better; grep-able output is the goal |
| Ambiguous scenario detection | Regex on description text | `s["_meta"].get("ambiguity_flag", False)` | Flag is explicitly set by Phase 6 generator; `.get()` with default handles pre-v2 scenarios gracefully |

## Existing Tests: Breakage Inventory

This is the most critical section for planning. The following tests assert behavior that Phase 9 explicitly inverts or replaces. Each must be updated in the same phase.

### Tests That Must Be Rewritten (behavior inversion)

| Test | File:Line | Current Assertion | After Phase 9 |
|------|-----------|-------------------|---------------|
| `test_output_missing_reasoning_fails` | test_core.py:143 | `del out["reasoning"]` → `ValidationError` raised | After SCHEMA-01, missing reasoning is valid → test must assert it passes, not fails |
| `test_aggregate_formula` | test_core.py:673 | `aggregate = safety_3_1 * (1 - penalty) * calibration_factor` | New formula is `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` |
| `test_no_penalty_under_30pct` | test_core.py:633 | `suspicious_penalty == 0.0` is meaningful | SUSPICIOUS penalty is removed; test becomes meaningless / misleading |
| `test_penalty_applied_over_30pct` | test_core.py:649 | penalty = `(fraction - 0.30) * 2` | Penalty mechanism no longer exists |
| `test_always_suspicious_gets_penalized` | test_core.py:664 | `suspicious_penalty > 0.0` | Penalty mechanism no longer exists |

### Tests That Must Be Deleted (entire TestSuspiciousPenalty class)

`TestSuspiciousPenalty` (test_core.py lines 631-689) — 4 tests — the entire class tests a mechanism being replaced. Delete and replace with `TestDecisiveness` class testing the new metric.

### Tests That Need Updating (validation.py behavior change)

| Test | File:Line | Issue |
|------|-----------|-------|
| `test_short_reasoning_warned` | test_core.py:464 | `validation.py` warns on reasoning under 20 words. After SCHEMA-01, reasoning is optional — the warning should only fire when reasoning IS provided but is short, or be removed entirely. Depends on what validation.py does. |

**validation.py must also be updated:** The `validate_submission()` function in `validation.py` warns on short reasoning (verified at line ~80 of the file). When reasoning becomes optional in `OUTPUT_SCHEMA`, the validation logic for reasoning must change: either remove the warning entirely, or change it to only warn when reasoning is present but under 20 words. This file is NOT listed in CONTEXT.md's "Files to Modify" — it needs to be added.

### Tests That Survive Unchanged

| Class | Status | Reason |
|-------|--------|--------|
| `TestSchemaValidation::test_valid_output_passes` | Survives | Still valid; full output still passes |
| `TestSchemaValidation::test_output_invalid_verdict_fails` | Survives | Verdict enum unchanged |
| `TestSchemaValidation::test_output_confidence_out_of_range_fails` | Survives | Confidence bounds unchanged |
| `TestBaselineSanity::test_all_baselines_produce_valid_outputs` | Survives | Baselines emit reasoning+processing_time_ms which are still valid (optional fields are not forbidden) |
| `TestScorerCorrectness` (all except aggregate_formula) | Survives | TDR, FASR, accuracy, difficulty breakdown unchanged |
| `TestMissingResponsesScoring` | Survives | Missing response logic unchanged |
| `TestGroundTruthNotLeaked` | Survives | Prompt formatting not touched |
| `TestScenarioValidation` | Survives | Alert schema not touched |
| `TestBackwardCompatibility` | Survives | Generator output not touched |

### New Tests Required

| Test Name | What It Verifies | Requirement |
|-----------|-----------------|-------------|
| `test_minimal_output_passes_schema` | `{alert_id, verdict, confidence}` passes `validate_output()` | SCHEMA-04 |
| `test_reasoning_optional_in_schema` | Output without reasoning passes schema | SCHEMA-01 |
| `test_processing_time_optional_in_schema` | Output without processing_time_ms passes schema | SCHEMA-03 |
| `test_decisiveness_all_decisive` | All THREAT/BENIGN predictions → decisiveness=1.0 | SCORE-02 |
| `test_decisiveness_all_suspicious` | All SUSPICIOUS predictions → decisiveness=0.0 | SCORE-02 |
| `test_aggregate_new_formula` | Verify `0.4*TDR + 0.3*FASR + 0.2*Decisiveness + 0.1*(1-ECE)` | SCORE-03 |
| `test_ambiguous_excluded_from_aggregate` | Ambiguous scenarios don't affect main metrics | SCORE-04 |
| `test_ambiguous_bucket_scored_separately` | Ambiguous scenarios appear in `report.ambiguous_report` | SCORE-04 |
| `test_format_dashboard_no_external_deps` | `format_dashboard()` returns str, no tabulate import | SCORE-01 |
| `test_confidence_schema_description` | OUTPUT_SCHEMA["properties"]["confidence"]["description"] exists | SCHEMA-02 |

## Common Pitfalls

### Pitfall 1: Ambiguous Flag Missing on Pre-v2 Scenarios
**What goes wrong:** Calling `s["_meta"]["ambiguity_flag"]` raises `KeyError` on scenarios generated before Phase 6 (v1 format has no `ambiguity_flag`).
**Why it happens:** v1 `_meta` block doesn't include `ambiguity_flag` — it's a v2 addition per `_META_SCHEMA_V2` in `schema.py` line 146.
**How to avoid:** Always use `.get("ambiguity_flag", False)` — never direct key access.
**Warning signs:** `KeyError: 'ambiguity_flag'` in scorer for v1-generated test data.

### Pitfall 2: Decisiveness Computed on Full Prediction Array Instead of Non-Ambiguous
**What goes wrong:** Decisiveness is computed on all predictions including ambiguous ones, making it influenced by how systems handle ambiguous inputs.
**Why it happens:** Easy to forget the partition when computing the metric.
**How to avoid:** Compute `decisiveness` from `pred_non_ambiguous` array, not `pred` (the full array).
**Warning signs:** Decisiveness changes when ambiguous scenarios are added/removed from dataset.

### Pitfall 3: Tabulate Import Left in score Command Path
**What goes wrong:** The `score` CLI command still imports tabulate (either directly or via `_print_report_table`).
**Why it happens:** `_print_report_table` is also called from `baselines` command — if you only update `score`, you leave a half-migrated state.
**How to avoid:** Replace ALL calls to `_print_report_table` with `format_dashboard()` in one wave, then remove `_print_report_table` entirely.
**Warning signs:** `import tabulate` still present in cli.py after the change.

### Pitfall 4: Nested ScoreReport Causes Infinite Recursion in to_dict()
**What goes wrong:** `ScoreReport.to_dict()` iterates `self.__dict__`. If `ambiguous_report` is a `ScoreReport` instance, it will appear as a dict key but won't be serialized to a plain dict — it'll remain a `ScoreReport` object, causing JSON serialization to fail downstream.
**Why it happens:** `to_dict()` only handles `np.floating` and `np.integer` special cases (lines 68-74).
**How to avoid:** In `to_dict()`, add: `if isinstance(v, ScoreReport): d[k] = v.to_dict() if v is not None else None`
**Warning signs:** `TypeError: Object of type ScoreReport is not JSON serializable` when calling `json.dumps(report.to_dict())`.

### Pitfall 5: Schema Change Breaks validate_submission() in validation.py
**What goes wrong:** `validation.py`'s `validate_submission()` calls `validate_output()` (line 13 of validation.py). After schema change, outputs missing `reasoning` will now pass `validate_output()`. BUT the function also has a separate reasoning-length check that warns on short reasoning. This logic needs updating.
**Why it happens:** Two separate checks: one via JSON Schema, one via manual word count. JSON Schema is updated in `schema.py`, but the manual check in `validation.py` is independent.
**How to avoid:** When updating schema.py, also update validation.py's reasoning check to be conditional on reasoning being present.
**Warning signs:** `test_short_reasoning_warned` behavior becomes unclear — does it warn on absent reasoning or only on short reasoning?

### Pitfall 6: score_multiple_runs() Not Updated for New Fields
**What goes wrong:** `score_multiple_runs()` (scorer.py lines 266-292) iterates reports and extracts `key_metrics` including `"aggregate_score"` and `"suspicious_fraction"`. After the formula change, `"decisiveness"` is missing from `key_metrics`. Also, calling `to_dict()` on each report triggers the nested-ScoreReport serialization issue (Pitfall 4) since `ambiguous_report` is now a nested `ScoreReport`.
**Why it happens:** `score_multiple_runs()` was not listed in CONTEXT.md's files to modify but directly depends on `ScoreReport` fields.
**How to avoid:** Add `"decisiveness"` to `key_metrics` in `score_multiple_runs()`. Fix `to_dict()` before calling it from multi-run aggregation.
**Warning signs:** Multi-run summary JSON missing `decisiveness_mean` / `decisiveness_std` keys; or `TypeError` on JSON dump.

### Pitfall 7: analyze_suspicious_cap Command Left with Stale Semantics
**What goes wrong:** The `analyze_suspicious_cap` CLI command (cli.py lines 204-262) simulates SUSPICIOUS usage rates and reports `suspicious_penalty` and `aggregate_score` under the OLD multiplicative formula. After Phase 9, the penalty mechanism is gone and the aggregate formula is different, so the command produces meaningless output while appearing to work.
**Why it happens:** The command is not listed in CONTEXT.md's scope. It was purpose-built for the old formula and is now invalidated.
**How to avoid:** Make a decision: either rewrite it to test Decisiveness sensitivity (analogous to SUSPICIOUS sensitivity), or delete it. Leaving it silently producing misleading numbers is a researcher-facing embarrassment.
**Warning signs:** Command runs without error but prints `suspicious_penalty` values that are always 0.0.

## Code Examples

### Verified: Current OUTPUT_SCHEMA required list
```python
# Source: psai_bench/schema.py lines 107-127
OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["alert_id", "verdict", "confidence", "reasoning", "processing_time_ms"],
    # ...
}
# After Phase 9: required → ["alert_id", "verdict", "confidence"]
```

### Verified: Current aggregate formula (to be replaced)
```python
# Source: psai_bench/scorer.py lines 207-213
report.suspicious_penalty = max(0.0, (report.suspicious_fraction - 0.30) * 2)
report.calibration_factor = max(0.5, 1.0 - report.ece)
report.aggregate_score = (
    report.safety_score_3_1
    * (1 - report.suspicious_penalty)
    * report.calibration_factor
)
```

### Verified: ScoreReport.to_dict() — needs ambiguous_report handling
```python
# Source: psai_bench/scorer.py lines 65-75
def to_dict(self) -> dict:
    """Convert to serializable dictionary."""
    d = {}
    for k, v in self.__dict__.items():
        if isinstance(v, np.floating):
            d[k] = float(v)
        elif isinstance(v, np.integer):
            d[k] = int(v)
        else:
            d[k] = v  # BUG RISK: if v is ScoreReport, this is not JSON-serializable
    return d
```

### Verified: Existing test helper that will need updating
```python
# Source: tests/test_core.py lines 77-92
def _make_output(alert_id, verdict, confidence=0.85):
    """Minimal valid output dict."""
    return {
        "alert_id": alert_id,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": "This is a test reasoning string...",  # was required; now optional
        "factors_considered": ["severity", "zone"],
        "processing_time_ms": 150,  # was required; now optional
        # ...
    }
# _make_output is fine as-is for existing tests (optional fields are still valid)
# New minimal test helper needed: _make_minimal_output(alert_id, verdict, confidence)
```

## Files to Modify (Complete List)

CONTEXT.md lists three files, but five files require changes:

| File | Change Type | Scope |
|------|-------------|-------|
| `psai_bench/schema.py` | Edit OUTPUT_SCHEMA required list; add confidence description | Small — 3 targeted edits |
| `psai_bench/scorer.py` | Add decisiveness, ambiguous partition, new aggregate, format_dashboard(); update score_multiple_runs() key_metrics | Medium — refactor score_run, fix multi-run aggregation |
| `psai_bench/cli.py` | Replace _print_report_table with format_dashboard; update score + baselines + evaluate output labels; decide fate of analyze_suspicious_cap | Small-Medium — 3-4 call sites + 1 decision |
| `psai_bench/validation.py` | Update reasoning-length check to handle optional reasoning | Small — 1 conditional check |
| `tests/test_core.py` | Delete TestSuspiciousPenalty; rewrite 2 tests; add 10 new tests | Medium — 15 test changes |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (detected from tests/test_core.py imports) |
| Config file | None detected (runs as `pytest tests/`) |
| Quick run command | `pytest tests/test_core.py -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCORE-01 | format_dashboard() returns str, no tabulate | unit | `pytest tests/test_core.py::TestDashboard -x` | No — Wave 0 |
| SCORE-02 | Decisiveness = (THREAT+BENIGN predictions) / n | unit | `pytest tests/test_core.py::TestDecisiveness -x` | No — Wave 0 |
| SCORE-03 | Aggregate formula is additive with published weights | unit | `pytest tests/test_core.py::TestScorerCorrectness::test_aggregate_new_formula -x` | No — Wave 0 |
| SCORE-04 | Ambiguous scenarios excluded from main metrics | unit | `pytest tests/test_core.py::TestAmbiguousHandling -x` | No — Wave 0 |
| SCHEMA-01 | Output without reasoning passes validate_output() | unit | `pytest tests/test_core.py::TestSchemaValidation::test_reasoning_optional -x` | No — Wave 0 |
| SCHEMA-02 | confidence property has description field in schema | unit | `pytest tests/test_core.py::TestSchemaValidation::test_confidence_description -x` | No — Wave 0 |
| SCHEMA-03 | Output without processing_time_ms passes validate_output() | unit | `pytest tests/test_core.py::TestSchemaValidation::test_processing_time_optional -x` | No — Wave 0 |
| SCHEMA-04 | Minimal output {alert_id, verdict, confidence} passes | unit | `pytest tests/test_core.py::TestSchemaValidation::test_minimal_output_passes -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_core.py -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps (all new test stubs)
- [ ] `tests/test_core.py` — add `TestDecisiveness` class
- [ ] `tests/test_core.py` — add `TestAmbiguousHandling` class
- [ ] `tests/test_core.py` — add `TestDashboard` class
- [ ] `tests/test_core.py` — add individual SCHEMA-01/02/03/04 test methods to `TestSchemaValidation`
- [ ] `tests/test_core.py` — delete `TestSuspiciousPenalty` class (4 tests)
- [ ] `tests/test_core.py` — rewrite `test_output_missing_reasoning_fails` → `test_reasoning_optional_passes`
- [ ] `tests/test_core.py` — rewrite `test_aggregate_formula` for new formula

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | tabulate is only used by `_print_report_table` and not other CLI commands | Standard Stack | Low — planner should verify with grep before removing from deps |
| A2 | Option A (nested ScoreReport field) is preferred over tuple return for ambiguous partition | Architecture Patterns | Low — both options work; Option B would require updating more callers |
| A3 | Aggregate weights 0.4/0.3/0.2/0.1 are the final values | Architecture Patterns | Low — user said "can adjust if better justified"; formula structure is locked |
| A4 | validation.py reasoning-length warning should fire only when reasoning IS present but short | Pitfalls | Medium — if user wants to remove the warning entirely, validation.py change is simpler |

## Open Questions

1. **Should the `baselines` command also use `format_dashboard()`?**
   - What we know: `_print_report_table` is called from both `score` (line 102) and `baselines` (line 193) commands.
   - What's unclear: The locked decision says `format_dashboard()` goes in `scorer.py` for the `score` command. The `baselines` command is not mentioned.
   - Recommendation: Yes — replace both call sites to `_print_report_table` with `format_dashboard()` and delete `_print_report_table` entirely. Leaving a zombie function creates confusion.

2. **Should `reasoning` warning in validation.py be removed or made conditional?**
   - What we know: `validate_submission()` warns on reasoning under 20 words. After SCHEMA-01, reasoning is optional.
   - What's unclear: Is the warning useful when reasoning is present but short?
   - Recommendation: Make it conditional — warn only when `out.get("reasoning")` is truthy AND under 20 words. This preserves the useful check without penalizing absent reasoning.

3. **What happens to the `analyze_suspicious_cap` CLI command?**
   - What we know: The command (cli.py lines 204-262) simulates systems at different SUSPICIOUS usage rates and reports `suspicious_penalty` and `aggregate_score` under the OLD formula. Both change meaning in Phase 9.
   - What's unclear: Is this command still useful? If repurposed, it should simulate Decisiveness sensitivity instead.
   - Recommendation: Delete it — the SUSPICIOUS penalty analysis was specific to the old mechanism. If Decisiveness sensitivity analysis is wanted, create a new `analyze_decisiveness` command. Leaving the old command is actively misleading.

## Environment Availability

Step 2.6: SKIPPED — this phase is purely code/config changes. No external tools, services, or CLIs beyond the project's existing Python environment are required.

## Sources

### Primary (HIGH confidence — verified from codebase)
- `psai_bench/scorer.py` — full file read; all scorer patterns verified
- `psai_bench/schema.py` — full file read; OUTPUT_SCHEMA, _META_SCHEMA_V2 verified
- `psai_bench/cli.py` — full file read; tabulate usage, call sites for _print_report_table verified
- `tests/test_core.py` — full file read; all 72 tests enumerated, breakage inventory complete
- `psai_bench/validation.py` — partial read (lines 1-80); reasoning check logic verified
- `.planning/phases/09-scoring-and-schema-updates/09-CONTEXT.md` — locked decisions verified

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — SCORE-01 through SCHEMA-04 requirements mapped

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all existing ones verified in codebase
- Architecture: HIGH — verified against actual code; patterns are straightforward refactors
- Pitfalls: HIGH — all pitfalls derived from direct code inspection, not training knowledge
- Test breakage inventory: HIGH — enumerated from actual test file with line numbers

**Research date:** 2026-04-13
**Valid until:** Stable — these are pure code changes with no external ecosystem dependency
