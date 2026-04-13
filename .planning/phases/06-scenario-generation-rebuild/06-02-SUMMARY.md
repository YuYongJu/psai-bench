---
phase: 06-scenario-generation-rebuild
plan: "02"
subsystem: scenario-generation
tags: [generators, schema, cli, version-bump, v2, adversarial, ambiguity-flag]
dependency_graph:
  requires: [DESCRIPTION_POOL_AMBIGUOUS, DESCRIPTION_POOL_UNAMBIGUOUS_THREAT, DESCRIPTION_POOL_UNAMBIGUOUS_BENIGN, assign_ground_truth_v2]
  provides: [MetadataGenerator-v2, generate_ucf_crime_v2, _inject_adversarial_signals, _META_SCHEMA_V2, CLI-version-flag]
  affects: [psai_bench/generators.py, psai_bench/schema.py, psai_bench/cli.py, psai_bench/__init__.py]
tech_stack:
  added: []
  patterns: [adversarial-injection, version-dispatch, schema-documentation]
key_files:
  created: []
  modified:
    - psai_bench/generators.py
    - psai_bench/schema.py
    - psai_bench/cli.py
    - psai_bench/__init__.py
decisions:
  - version param defaults to "v1" in MetadataGenerator, VisualGenerator, MultiSensorGenerator — backward-compat shim ensures existing callers unaffected
  - _inject_adversarial_signals uses randint(0,3) for 3-way flip (severity, zone, time+device) — probability splits evenly giving diverse adversarial types
  - _meta.adversarial=True always upgrades difficulty from "easy" to "medium" — adversarial scenarios should never be easy by design (SCEN-04)
  - version_suffix omitted from filename when v1 (no "_v1" suffix) — preserves backward compat for downstream scripts expecting original filenames
  - _META_SCHEMA_V2 added as importable constant for programmatic inspection but not enforced by validate_alert (which uses ALERT_SCHEMA) — _meta is benchmark-internal
metrics:
  duration: "<5 min"
  completed_date: "2026-04-13"
  tasks_completed: 2
  files_modified: 4
requirements_satisfied: [SCEN-04, GT-02]
---

# Phase 06 Plan 02: Wire v2 Generator, Schema, CLI, and Version Bump Summary

**One-liner:** MetadataGenerator(version="v2") with adversarial signal injection (~20%), ambiguity_flag propagation in _meta, _META_SCHEMA_V2 constant, --version CLI flag, and version bump to 2.0.0.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | v2 generation path with adversarial injection | e2940f1 | psai_bench/generators.py |
| 2 | Schema documentation, CLI --version flag, version 2.0.0 | e2940f1 | psai_bench/schema.py, psai_bench/cli.py, psai_bench/__init__.py |

## What Was Built

### Task 1: v2 Generation Path (generators.py)

**MetadataGenerator** updated with:
- `version: str = "v1"` parameter in `__init__` — v1 default preserves backward compat
- `generate_ucf_crime()` dispatches to `generate_ucf_crime_v2(n)` when `self.version == "v2"`
- `generate_ucf_crime_v2()` new method: draws descriptions from shared pools (70% ambiguous, 15% threat, 15% benign), assigns GT via `assign_ground_truth_v2()`, injects adversarial signals for ~20% of scenarios
- `_inject_adversarial_signals()` helper: 3-way random flip — severity flip (0), zone flip (1), time+device FPR flip (2) — forces one signal to contradict the others

**VisualGenerator** and **MultiSensorGenerator** both accept `version` param and pass it through the delegation chain.

**Verification results:**
- 46/200 adversarial scenarios (23%) — within expected 10-30% range
- 34/200 ambiguous scenarios, 0 incorrectly labeled (all SUSPICIOUS)
- 31 descriptions appear across multiple GT classes (same text → different GT by context)
- Deterministic: same seed → identical GT sequence

### Task 2: Schema, CLI, Version (schema.py, cli.py, __init__.py)

**schema.py:** `_META_SCHEMA_V2` constant added — documents all v2 _meta fields (ground_truth, difficulty, source_dataset, source_category, seed, index, generation_version, weighted_sum, adversarial, ambiguity_flag, description_category). Not enforced by `validate_alert()` since _meta is benchmark-internal only.

**cli.py:** `--version [v1|v2]` option added to `generate` command. Default v1. Wires into MetadataGenerator, VisualGenerator, MultiSensorGenerator. Output filename includes `_v2` suffix when version != v1.

**__init__.py:** `__version__` bumped to `"2.0.0"`.

## Verification Results

```
v1 backward compat: all 50 scenarios have no ambiguity_flag, no generation_version
v2 generation: 200 scenarios, all have generation_version="v2"
Adversarial count: 46/200 = 23.0% (expected 10-30%)
Ambiguous: 34, wrongly labeled: 0
Descriptions across GT classes: 31 (requirement: > 0)
Adversarial type pairs include HIGH+BENIGN and LOW+THREAT
CLI v2 invocation exits 0: metadata_ucf_seed42_v2.json written
CLI v1 default exits 0: metadata_ucf_seed42.json written
_META_SCHEMA_V2 importable, ambiguity_flag in properties: True
psai_bench.__version__ == "2.0.0"
129 tests pass
```

## Deviations from Plan

None — plan executed exactly as written. All code was pre-implemented in commit `e2940f1` (an ancestor of the plan's dependency commit `42f082b`), which contained both the Plan 06-01 distributions work and the Plan 06-02 wiring work in a single commit. All acceptance criteria verified green against the existing code.

## Known Stubs

None.

## Threat Flags

None — `--version` flag constrained by `click.Choice(["v1", "v2"])` (T-06-04 mitigated). No new network endpoints or file access patterns introduced.

## Self-Check: PASSED

- `psai_bench/generators.py` has generate_ucf_crime_v2: VERIFIED (line 279)
- `psai_bench/schema.py` has _META_SCHEMA_V2 with ambiguity_flag: VERIFIED (line 134-150)
- `psai_bench/cli.py` has --version flag: VERIFIED (line 31-32)
- `psai_bench/__init__.py` version is "2.0.0": VERIFIED
- Commit `e2940f1` exists as ancestor: VERIFIED (git log confirms)
- 129 tests pass: VERIFIED
