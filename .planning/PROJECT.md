# PSAI-Bench

## What This Is

PSAI-Bench is an open-source benchmark for evaluating any AI system (LLM, ML, rule-based, hybrid) on physical security alert triage. Users bring their own system, run it against PSAI-Bench scenarios, and score the outputs. The benchmark provides the scenarios, ground truth, scoring engine, and statistical tools — not the system under test.

## Core Value

Provide a rigorous, non-trivially-solvable benchmark where no single input field reveals the ground truth — models must reason across multiple context signals to triage correctly.

## Current Milestone: v2.0 Fix the Foundation

**Goal:** Rebuild the benchmark's scientific foundation so results are meaningful — context-dependent ground truth, no single-field leakage, transparent scoring, system-agnostic design.

**Target features:**
- Context-dependent ground truth (same description → different GT based on zone/time/device)
- Shared description pool across all GT classes (break 100% description leakage)
- Noisy severity (~70% correlated, not 100%) (break 85.7% severity leakage)
- Adversarial scenarios with deliberately conflicting signals
- Published decision rubric (every GT label justified)
- Separated metrics dashboard (no opaque aggregate)
- Simplified output schema (reasoning optional, confidence defined as P(verdict correct))
- "Bring Your Own System" as the primary workflow
- Updated README and documentation

## Requirements

### Validated

- ✓ CLI architecture (click-based, well-structured) — v1.0
- ✓ Scoring engine implementation (math correct) — v1.0
- ✓ Statistical tools (McNemar's, bootstrap CIs, run consistency) — v1.0
- ✓ 103 passing tests, 68% coverage — v1.0
- ✓ GitHub Actions CI (Python 3.10/3.11/3.12 matrix) — v1.0
- ✓ Apache-2.0 LICENSE, CONTRIBUTING, CODE_OF_CONDUCT — v1.0
- ✓ Repository hygiene (clean git history, no generated data committed) — v1.0
- ✓ Project metadata (pyproject.toml with authors, URLs, classifiers) — v1.0

### Active

(Defined per v2.0 milestone — see REQUIREMENTS.md)

### Out of Scope

- Running model evaluations (costs money, depends on API keys — user's job)
- Web dashboard or visualization UI — benchmark is CLI-first
- Paper writing — separate effort
- Video processing implementation — v3.0
- Dispatch decisions (5 action types) — v4.0
- Cost-aware scoring — v4.0

## Context

- v1.0 shipped: repo at github.com/YuYongJu/psai-bench, all infrastructure working
- v1.0 flaw: scenario generation has critical leakage (description=100%, severity=85.7% predictive of GT)
- v1.0 flaw: ground truth labels are arbitrary (hardcoded category→GT, no justification)
- v1.0 flaw: aggregate scoring formula is multiplicative, opaque, uses magic numbers
- v1.0 flaw: output schema requires reasoning (excludes non-LLM systems)
- v1.0 flaw: built-in evaluators force a hardcoded prompt instead of testing user's system
- GPT-4o evaluation exists but results are unreliable due to scenario leakage
- VISION.md documents v2.0/v3.0/v4.0 roadmap

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
*Last updated: 2026-04-13 after milestone v2.0 initialization*
