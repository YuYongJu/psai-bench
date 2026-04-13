---
phase: 20-adversarial-v4-generator
plan: "02"
subsystem: generators
tags: [adversarial, behavioral-deception, rng-isolation, tdd, cli]
dependency_graph:
  requires: [20-01]
  provides: [AdversarialV4Generator, adversarial_v4-cli-track]
  affects: [psai_bench/generators.py, psai_bench/cli.py]
tech_stack:
  added: []
  patterns: [isolated-rng, behavioral-signal-design, round-robin-pattern-assignment]
key_files:
  created: [tests/test_adversarial_v4_generator.py]
  modified: [psai_bench/generators.py, psai_bench/cli.py]
decisions:
  - "RNG isolation via own np.random.RandomState — same pattern as ContradictoryGenerator and VisualOnlyGenerator"
  - "Round-robin pattern assignment then permutation shuffle — guarantees all 3 types appear even for n=3"
  - "difficulty always 'hard' for adversarial_v4 — no _assign_difficulty call needed, all scenarios are by design hard"
  - "Default n=100 (not 50) to match ContradictoryGenerator/VisualOnlyGenerator convention"
metrics:
  duration: "~25 minutes"
  completed: "2026-04-13T23:14:38Z"
  tasks_completed: 2
  files_changed: 3
requirements: [ADV-01, ADV-04]
---

# Phase 20 Plan 02: AdversarialV4Generator Implementation Summary

**One-liner:** AdversarialV4Generator with isolated RNG, three behavioral deception patterns, and CLI wiring via `--track adversarial_v4`.

## What Was Built

`AdversarialV4Generator` appended to `psai_bench/generators.py`. The class produces behavioral adversarial scenarios where the description text is designed to suggest the wrong verdict, but `assign_ground_truth_v2` resolves the actual ground truth from biased-but-real context signals. Three pattern types:

- **loitering_as_waiting** — description looks like loitering threat; signals (recent badge <10 min, daytime, low zone sensitivity) resolve to BENIGN
- **authorized_as_intrusion** — description looks like unauthorized entry; signals (interior zone, recent badge) resolve to BENIGN
- **environmental_as_human** — description looks like human presence; signals (high-FPR device ~0.85, parking/perimeter, LOW severity) resolve to BENIGN

RNG isolation is enforced via `np.random.RandomState(seed)` owned exclusively by the generator instance, matching the ContradictoryGenerator and VisualOnlyGenerator pattern established in earlier phases.

CLI wired in `psai_bench/cli.py` with `"adversarial_v4"` added to `click.Choice` and an `elif` branch invoking `AdversarialV4Generator`.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 RED | Add failing TDD tests | 0764f05 | tests/test_adversarial_v4_generator.py |
| 1 GREEN | Implement AdversarialV4Generator | bd186ad | psai_bench/generators.py |
| 2 | Wire adversarial_v4 CLI track | f93b15d | psai_bench/cli.py |

## Verification Results

- `AdversarialV4Generator(seed=42).generate(50)` → 50 scenarios, all 3 adversarial_type values present
- Seed reproducibility: two runs with seed=42 produce byte-identical JSON
- RNG isolation: `MetadataGenerator(seed=42, version='v2').generate_ucf_crime(100)` output unchanged regardless of AdversarialV4Generator creation or full execution
- CLI: `psai-bench generate --track adversarial_v4 --n 50 --seed 42` exits 0, writes valid file
- Phase 20 acceptance test: two identical CLI runs produce byte-identical output files
- Full test suite: **316 tests pass**, 0 failures

## Deviations from Plan

None — plan executed exactly as written. The class was appended after `MultiSensorGenerator` (which is the actual last class in the file; `TemporalSequenceGenerator` precedes it). The plan's instruction "after TemporalSequenceGenerator" was interpreted as "at the bottom of the file" per the code template provided.

## Known Stubs

None. All data flows are live: `assign_ground_truth_v2` computes actual GT from context signals; description pools are populated from ADV_V4_* constants added in Plan 01.

## Threat Flags

No new security-relevant surface introduced. The generator produces deterministic in-memory data structures; the CLI writes to a user-specified output directory (existing pattern, no path traversal risk from `--track` or `--seed` parameters).

## Self-Check: PASSED

- `psai_bench/generators.py` — AdversarialV4Generator class appended: FOUND
- `psai_bench/cli.py` — adversarial_v4 in click.Choice and elif branch: FOUND
- `tests/test_adversarial_v4_generator.py` — 13 tests: FOUND
- Commit 0764f05 (RED tests): FOUND
- Commit bd186ad (GREEN generator): FOUND
- Commit f93b15d (CLI wiring): FOUND
- 316 tests pass: VERIFIED
