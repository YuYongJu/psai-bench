---
phase: 18-schema-and-cost-model-foundation
plan: "01"
subsystem: schema
tags: [schema, dispatch, cost-model, scipy, backward-compatible]
dependency_graph:
  requires: []
  provides:
    - psai_bench.schema.DISPATCH_ACTIONS
    - psai_bench.schema.OUTPUT_SCHEMA.dispatch (optional field)
    - psai_bench.schema._META_SCHEMA_V2.optimal_dispatch
    - psai_bench.schema._META_SCHEMA_V2.adversarial_type
    - docs/dispatch-decision-rubric.md
  affects:
    - psai_bench/cost_model.py (Plan 02 — imports DISPATCH_ACTIONS)
    - psai_bench/generators.py (AdversarialV4Generator — uses adversarial_type)
tech_stack:
  added: [scipy>=1.10]
  patterns: [post-dict-mutation for additive schema changes, TDD red-green]
key_files:
  created:
    - tests/test_schema_v4.py
    - docs/dispatch-decision-rubric.md
  modified:
    - psai_bench/schema.py
    - pyproject.toml
decisions:
  - "dispatch field added as post-dict mutation (not inline) to preserve zero-diff readability of existing schema literals"
  - "DISPATCH_ACTIONS placed immediately after VERDICTS to collocate related constants"
  - "scipy declared as direct (not optional) dependency — required by cost_model.py statistics"
  - "generation_version enum extended inline; optimal_dispatch/adversarial_type added as post-dict mutations to _META_SCHEMA_V2"
metrics:
  duration: "~25 minutes"
  completed: "2026-04-13"
  tasks_completed: 2
  files_created: 2
  files_modified: 2
  tests_added: 10
  tests_total: 248
---

# Phase 18 Plan 01: Schema and Cost Model Foundation Summary

Schema contract extended for v4.0 with DISPATCH_ACTIONS constant, optional dispatch field in OUTPUT_SCHEMA, _META_SCHEMA_V2 additions for optimal_dispatch and adversarial_type, and published dispatch decision rubric — zero breaking changes, 248/248 tests pass.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add failing schema v4 tests | 6cfaddf | tests/test_schema_v4.py |
| 1 (GREEN) | Extend schema.py, fix scipy dep | 0539e95 | psai_bench/schema.py, pyproject.toml |
| 2 | Write dispatch decision rubric | c218947 | docs/dispatch-decision-rubric.md |

## What Was Built

**schema.py extensions (additive only):**
- `DISPATCH_ACTIONS = ("armed_response", "patrol", "operator_review", "auto_suppress", "request_data")` — 5-tuple constant added immediately after `VERDICTS` (line 141); `VERDICTS` is byte-identical to v3.0
- `OUTPUT_SCHEMA["properties"]["dispatch"]` — optional string field with enum restricted to `DISPATCH_ACTIONS`; not added to `required` list — backward-compatible with all v3.0 outputs
- `_META_SCHEMA_V2["properties"]["optimal_dispatch"]` — benchmark-computed optimal action; enum matches `DISPATCH_ACTIONS`
- `_META_SCHEMA_V2["properties"]["adversarial_type"]` — v4 adversarial sub-type; type `["string", "null"]`; enum includes `None` and 4 named sub-types
- `_META_SCHEMA_V2["properties"]["generation_version"]["enum"]` — extended from `["v1","v2","v3"]` to `["v1","v2","v3","v4"]` (inline change inside dict literal)

**pyproject.toml:**
- `scipy>=1.10` added to direct `dependencies` (not optional-dependencies); placed after numpy

**docs/dispatch-decision-rubric.md:**
- Full 8-section document covering: overview, primary decision table (GT × site_type × zone_sensitivity), site threat multipliers, 6 worked examples (one per dispatch action + extra for request_data), provisional cost matrix, 3 sensitivity profiles (low/medium/high), pipeline diagram, reproducibility guide

## Verification

```
VERDICTS unchanged: ('THREAT', 'SUSPICIOUS', 'BENIGN')
backward compat OK
scipy>=1.10
rubric OK
248 passed in 36.61s
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. This plan is schema-only — no rendering or data wiring involved.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes at external trust boundaries. The `dispatch` enum in OUTPUT_SCHEMA is restricted to `DISPATCH_ACTIONS` — invalid values raise `ValidationError` as required by T-18-01.

## Self-Check: PASSED

- `psai_bench/schema.py` — FOUND and verified
- `pyproject.toml` — contains `scipy>=1.10` — FOUND
- `docs/dispatch-decision-rubric.md` — FOUND and content verified
- `tests/test_schema_v4.py` — FOUND, 10/10 tests pass
- Commit `6cfaddf` — FOUND (RED: failing tests)
- Commit `0539e95` — FOUND (GREEN: schema + pyproject)
- Commit `c218947` — FOUND (rubric document)
- 248/248 tests pass (238 pre-existing + 10 new)
- `VERDICTS` tuple unchanged: `("THREAT", "SUSPICIOUS", "BENIGN")`
- `"dispatch"` not in `OUTPUT_SCHEMA["required"]` — confirmed
