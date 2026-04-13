# PSAI-Bench

## What This Is

PSAI-Bench is an open-source benchmark for evaluating any AI system (LLM, ML, rule-based, hybrid) on physical security alert triage. Users bring their own system, run it against PSAI-Bench scenarios, and score the outputs. The benchmark provides the scenarios, ground truth, scoring engine, and statistical tools — not the system under test.

## Core Value

Provide a rigorous, non-trivially-solvable benchmark where no single input field reveals the ground truth — models must reason across multiple context signals to triage correctly.

## Current Milestone: v3.0 Perception-Reasoning Gap

**Goal:** Make the benchmark genuinely publishable — add visual-only scenarios, contradictory scenarios, temporal alert sequences, and frame extraction baseline to measure whether video actually adds value over metadata-only triage.

**Target features:**
- Visual-only scenarios (video + minimal metadata — no description, severity, or zone context)
- Contradictory scenarios (metadata says X, video shows Y — visual perception overrides text)
- Temporal alert sequences (3-5 related alerts building a narrative, escalation patterns)
- Frame extraction baseline (keyframe image description vs full video temporal analysis)
- Visual and temporal track scoring updates
- Evaluation protocol document

## Requirements

### Validated

- ✓ CLI architecture (click-based, well-structured) — v1.0
- ✓ Scoring engine implementation (math correct) — v1.0
- ✓ Statistical tools (McNemar's, bootstrap CIs, run consistency) — v1.0
- ✓ 133 passing tests — v2.0
- ✓ GitHub Actions CI (Python 3.10/3.11/3.12 matrix) — v1.0
- ✓ Apache-2.0 LICENSE, CONTRIBUTING, CODE_OF_CONDUCT — v1.0
- ✓ Repository hygiene (clean git history, no generated data committed) — v1.0
- ✓ Project metadata (pyproject.toml with authors, URLs, classifiers) — v1.0
- ✓ Context-dependent GT (weighted multi-signal scoring, no single-field leakage) — v2.0
- ✓ Shared description pools across GT classes — v2.0
- ✓ Adversarial scenario injection (~20%) — v2.0
- ✓ Transparent metrics dashboard (TDR, FASR, Decisiveness, ECE) — v2.0
- ✓ Simplified output schema (reasoning/processing_time optional) — v2.0
- ✓ Published decision rubric with worked examples — v2.0
- ✓ BYOS-first README and documentation — v2.0

### Active

(Defined per v3.0 milestone — see REQUIREMENTS.md)

### Out of Scope

- Running model evaluations (costs money, depends on API keys — user's job)
- Web dashboard or visualization UI — benchmark is CLI-first
- Paper writing — separate effort
- Video processing implementation — v3.0
- Dispatch decisions (5 action types) — v4.0
- Cost-aware scoring — v4.0

## Context

- v1.0 shipped: repo at github.com/YuYongJu/psai-bench, all infrastructure working
- v2.0 shipped: scientific foundation rebuilt — context-dependent GT, 133 tests, BYOS workflow
- v2.0 fixed all v1.0 leakage flaws (description, severity, category no longer predict GT)
- GPT-4o evaluation exists but results need re-running on v2.0 scenarios
- VISION.md documents v3.0/v4.0 roadmap

## Constraints

- **Backward compatibility**: v1.0 scenarios must still be generatable with default params
- **License**: Apache-2.0 (established)
- **Python**: >=3.10
- **No new dependencies** unless strictly needed for scenario generation
- **Seed reproducibility**: same seed + same params = same scenarios

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Apache-2.0 license | Permissive, standard for academic tools | ✓ Good |
| Keep results/ in repo | Example outputs help users understand format | ✓ Good |
| Generated data out of git | Reproducible via CLI, not committed | ✓ Good |
| v1.0 evaluators = reference implementation | User brings their own system; evaluators are examples | — v2.0 |
| Context-dependent GT | Description alone must NOT predict GT | — v2.0 |
| Separate metrics, no aggregate | Transparent > clever | — v2.0 |
| Reasoning field optional | Support classifiers, not just LLMs | — v2.0 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after milestone v3.0 initialization*
