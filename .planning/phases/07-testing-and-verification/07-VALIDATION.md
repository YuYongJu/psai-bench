---
phase: 7
slug: testing-and-verification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-13
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/test_leakage.py tests/test_decision_rubric.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_leakage.py tests/test_decision_rubric.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 0 | TEST-01 | — | N/A | infra | `test -f tests/conftest.py` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | TEST-01, SCEN-05 | — | N/A | integration | `python -m pytest tests/test_leakage.py -v` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | TEST-02 | — | N/A | unit | `python -m pytest tests/test_decision_rubric.py -v` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 2 | TEST-03, SCEN-07 | — | N/A | integration | `python -m pytest tests/test_core.py -k backward -v` | ✅ | ⬜ pending |
| 07-01-05 | 01 | 2 | TEST-04 | — | N/A | integration | `python -m pytest tests/test_leakage.py -k ambiguity -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures for v2 scenario generation
- [ ] `tests/test_leakage.py` — stubs for decision stump and ambiguity tests
- [ ] `tests/test_decision_rubric.py` — stubs for GT verification tests

*Existing infrastructure (pytest, numpy, jsonschema) covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI passes across Python 3.10/3.11/3.12 | TEST-01 through TEST-04 | Requires CI environment | Push branch, verify GitHub Actions matrix passes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
