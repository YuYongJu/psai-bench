---
phase: 16-cli-extensions
plan: "01"
subsystem: cli
tags: [cli, frame-extraction, scoring, temporal, perception-gap]
dependency_graph:
  requires: [psai_bench/scorer.py:score_sequences, psai_bench/scorer.py:compute_perception_gap]
  provides: [psai_bench/frame_extraction.py:extract_keyframes, psai_bench/cli.py:score-sequences, psai_bench/cli.py:analyze-frame-gap]
  affects: [psai_bench/cli.py, pyproject.toml]
tech_stack:
  added: [opencv-python-headless>=4.10 (optional, [visual] group)]
  patterns: [Click subcommand, function-level cv2 guard, CliRunner integration tests]
key_files:
  created:
    - psai_bench/frame_extraction.py
    - tests/test_phase16_cli.py
  modified:
    - psai_bench/cli.py
    - pyproject.toml
decisions:
  - "Function-level cv2 guard: import cv2 inside extract_keyframes() (not module-level) so the module is safely importable for testing/introspection without cv2 installed"
  - "analyze-frame-gap takes 4 arguments (2 scenario files + 2 results files) to be fully self-contained — no shared scenario file assumption between tracks"
  - "score-sequences follows the same score command pattern: file args, table/json format choice, calls scorer directly"
  - "kept analyze-gap command entirely untouched — the two commands serve different use cases (per-run gap vs multi-model directory scan)"
metrics:
  duration: "~15 minutes"
  completed: "2026-04-13"
  tasks: 3
  files: 4
requirements_closed: [FRAME-01, FRAME-02, FRAME-03]
---

# Phase 16 Plan 01: CLI Extensions — score-sequences, analyze-frame-gap, frame_extraction Summary

**One-liner:** Uniform-interval keyframe extraction baseline (cv2, function-level guard) + two CLI subcommands wiring scorer.score_sequences and scorer.compute_perception_gap to the command line.

## What Was Built

Three artifacts close the Phase 16 requirements:

**1. `psai_bench/frame_extraction.py`** (FRAME-01, FRAME-02)
- `extract_keyframes(video_path, keyframe_interval_sec=5.0, max_frames=50)` — uniform-interval JPEG frame sampling using cv2
- cv2 import is guarded at function-level (not module-level): importing the module without cv2 is safe; the ImportError with `pip install "psai-bench[visual]"` only fires when `extract_keyframes()` is called
- FRAME-02 fairness constraint enforced by design: frame selection is purely time-based, `anomaly_segments` is never referenced
- `max_frames=50` cap prevents memory issues on long videos (T-16-02)

**2. `pyproject.toml`** — `[visual]` optional dependency group added after `api` group:
```toml
visual = [
    "opencv-python-headless>=4.10",
]
```

**3. `psai_bench/cli.py`** — two new subcommands (FRAME-03):
- `score-sequences` (`score_sequences_cmd`): wraps `scorer.score_sequences()`, supports `--format table|json`
- `analyze-frame-gap` (`analyze_frame_gap`): loads 4 files (metadata scenarios + results, visual scenarios + results), calls `score_run()` on each pair, then `compute_perception_gap()`

**4. `tests/test_phase16_cli.py`** — 10 tests across 3 classes:
- `TestScoreSequencesCLI`: table output, JSON output, --help
- `TestAnalyzeFrameGapCLI`: output header, score lines, --help
- `TestFrameExtraction`: safe import without cv2, ImportError with pip message, ValueError for zero interval, pyproject [visual] group check

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Function-level cv2 guard | Module importable without cv2; ImportError fires at call-time not import-time. Enables signature/docstring testing without opencv installed. |
| 4-argument analyze-frame-gap | Each track has its own scenario file — no assumption that metadata and visual scenarios share a common file. Makes the command usable independently. |
| score-sequences mirrors score pattern | Consistent UX: same --scenarios/--outputs/--format options, same file-open pattern, calls scorer directly. |
| analyze-gap left untouched | The two commands are complementary, not duplicates: analyze-gap scans a results directory across runs; analyze-frame-gap computes per-file cross-track gap. |

## Test Count

10 new tests in `tests/test_phase16_cli.py`. Full suite: **238 tests pass** (228 existing + 10 new), zero regressions.

## Deviations from Plan

None — plan executed exactly as written. The `sys.modules["cv2"] = None` trick for mocking ImportError (noted in the plan) works correctly: setting a module to `None` in `sys.modules` causes `import cv2` inside the function to raise `ImportError`, matching the plan's description.

## Requirements Closed

- FRAME-01: `extract_keyframes()` implemented with uniform-interval sampling using cv2
- FRAME-02: Frame selection never uses `anomaly_segments` (structural constraint, enforced by implementation)
- FRAME-03: `score-sequences` and `analyze-frame-gap` CLI subcommands implemented and tested

## Commits

| Hash | Description |
|------|-------------|
| `7777e18` | feat(16-01): add [visual] dep group and frame_extraction.py baseline module |
| `570a704` | feat(16-01): add score-sequences and analyze-frame-gap CLI subcommands (FRAME-03) |
| `b6d2ffa` | test(16-01): add Phase 16 CLI tests and frame_extraction unit tests |

## Known Stubs

None.

## Threat Flags

No new security surface introduced beyond what was modeled in the plan's STRIDE register. All file I/O is researcher-owned local files; `click.Path(exists=True)` validates existence before open.

## Self-Check: PASSED

- `psai_bench/frame_extraction.py` exists and is importable
- `psai_bench/cli.py` registers `score-sequences` and `analyze-frame-gap` commands
- `tests/test_phase16_cli.py` exists with 10 tests, all green
- `pyproject.toml` contains `opencv-python-headless>=4.10` in `[visual]` group
- Commits `7777e18`, `570a704`, `b6d2ffa` present in git log
