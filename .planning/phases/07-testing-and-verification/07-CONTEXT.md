# Phase 7: Testing and Verification - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Write automated tests that confirm Phase 6's scenario generation rebuild works correctly: no single field predicts ground truth above 70%, the decision rubric produces expected labels for known configurations, ambiguous scenario metadata is correct, and default parameters still produce v1.0-compatible output.

</domain>

<decisions>
## Implementation Decisions

### Test Organization
- New `tests/test_leakage.py` for leakage/decision stump tests
- New `tests/test_decision_rubric.py` for GT function label verification
- Extend `tests/test_core.py` for backward compatibility tests
- Shared pytest fixtures in `conftest.py` for generated scenario sets (avoid regenerating per test)
- 1000 scenarios for decision stump tests (statistically significant, fast in CI)
- CI matrix: Python 3.10, 3.11, 3.12 per success criteria

### Leakage Verification Method
- Use sklearn `DecisionTreeClassifier(max_depth=1)` for decision stump accuracy
- Assert <0.70 accuracy for each field individually (matching SCEN-05/TEST-01 exactly)
- Label encoding for ordinal fields (severity), one-hot for nominal (zone type, description)
- Also verify class balance: no GT class exceeds 65% of scenarios (revised from 50% — research verified SUSPICIOUS reaches 53.5% at n=1000 due to wide scoring band; 50% is empirically impossible without Phase 6 threshold changes)

### Ground Truth Verification
- 9-12 known-correct configurations: ~3 per GT class (THREAT, SUSPICIOUS, BENIGN), including 2-3 adversarial cases
- Backward compatibility: generate with default params, validate schema AND verify category distribution matches v1.0 expectations (same categories, same GT mapping pattern)
- Pass criteria: same scenario count, same schema, same categories present, same GT distribution pattern (NOT exact field values)
- Ambiguity flag: assert every scenario with `ambiguity_flag=true` has `GT=SUSPICIOUS`, AND assert some non-flagged scenarios exist for each GT class

### Claude's Discretion
- Exact known-correct scenario configurations for GT tests
- Specific field encoding details for decision stump
- conftest.py fixture implementation details

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/test_core.py` — 103 existing tests with helper functions `_make_scenario()`, `_make_output()`
- `tests/test_cli.py` — CLI integration tests
- `tests/test_statistics.py` — Statistical test suite
- `psai_bench/generators.py` — `MetadataGenerator` with `generate_ucf_crime()` method
- `psai_bench/schema.py` — `validate_alert()`, `validate_output()`, `ALERT_SCHEMA`

### Established Patterns
- Tests use pytest with numpy assertions
- Helper functions create minimal valid scenarios for isolated testing
- Generators accept seed parameter for determinism
- Schema validation via jsonschema

### Integration Points
- Phase 6 creates the v2 generation path (`MetadataGenerator(version="v2")`)
- Phase 6 adds `_meta.ambiguity_flag` to schema
- Phase 6 implements the decision function in `distributions.py` or `generators.py`
- Existing CI config needs Python matrix update

</code_context>

<specifics>
## Specific Ideas

- Decision stump test should test ALL fields: description, severity, zone type, time_of_day, device FPR
- Known-correct GT configs should include adversarial cases from Phase 6 (HIGH severity + BENIGN GT, LOW severity + THREAT GT)
- Backward compat test should use `MetadataGenerator(version="v1")` or default params and verify output matches v1.0 behavior

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
