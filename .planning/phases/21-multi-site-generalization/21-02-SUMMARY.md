---
phase: 21-multi-site-generalization
plan: "02"
subsystem: testing
tags: [leakage-audit, site-generalization, logistic-regression, pytest]
requires: ["21-01"]
provides: ["site-leakage-ci-guard"]
affects: ["tests/test_site_leakage.py"]
tech_stack:
  added: ["sklearn.linear_model.LogisticRegression", "sklearn.model_selection.cross_val_score", "sklearn.preprocessing.LabelEncoder", "sklearn.preprocessing.OneHotEncoder"]
  patterns: ["5-fold stratified cross-validation", "logistic regression probe", "one-hot feature encoding"]
key_files:
  created:
    - tests/test_site_leakage.py
  modified: []
decisions:
  - "Probe accuracy 0.34 is well below 0.60 threshold — no xfail marker needed"
  - "Used _meta.source_category (not top-level category key which does not exist)"
  - "Weather extracted as context.weather.condition (a dict, not a string)"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-13"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
requirements_satisfied: [SITE-02]
---

# Phase 21 Plan 02: Site Leakage Audit Summary

One-liner: Logistic regression probe on category/time/weather/zone features scores 34% site_type accuracy — SITE_CATEGORY_BLOCKLIST creates no actionable structural leakage.

## Objective

Verify that the SITE_CATEGORY_BLOCKLIST in generators.py does not create enough category-to-site correlation that a probe model could infer site identity without reading context.site_type directly. The leakage audit must run in CI as a repeatable pytest test so future changes to distributions.py are caught automatically.

## What Was Built

**tests/test_site_leakage.py** — 3-test pytest module that:

1. **test_leakage_below_threshold**: Trains a logistic regression (max_iter=500, 5-fold CV) on 31 features derived from category (14 one-hot), time_of_day (4 one-hot), weather condition (7 one-hot), zone_type (5 one-hot), and zone_sensitivity (integer) to predict site_type. Asserts mean cross-val accuracy <= 0.60.

2. **test_feature_extraction_excludes_site_type**: Asserts that no column in the feature matrix is derived from context.site_type. Verifies all 5 expected feature groups are present.

3. **test_fixed_seed_reproducibility**: Runs the probe twice with seed=42 and asserts float equality of accuracy, confirming deterministic generation.

## Probe Accuracy

**0.3400** (34%) with seed=42, n=600 scenarios.

This is 26 percentage points below the 60% threshold. The SITE_CATEGORY_BLOCKLIST creates minimal structural leakage — the probe cannot reliably distinguish solar from substation even though both block Shoplifting/Robbery/Arrest, because the category distributions overlap substantially across other shared categories (Arson, Vandalism, Burglary, etc.).

No xfail marker was added. The test passes cleanly.

## Feature Contributions

The 31-column feature matrix (no site_type) broke down as:
- 14 category one-hot columns (Abuse, Arrest, Arson, Assault, Burglary, Explosion, Fighting, Normal, RoadAccidents, Robbery, Shooting, Shoplifting, Stealing, Vandalism)
- 4 time_of_day one-hot columns
- 7 weather condition one-hot columns
- 5 zone_type one-hot columns
- 1 zone_sensitivity integer

Category columns are the most likely leakage vector (Shoplifting, Robbery, Arrest are blocked from solar/substation). Despite this, the logistic regression cannot exploit the correlation effectively — the blocklist affects ~4 of 14 categories, leaving sufficient ambiguity across the remaining shared categories.

## Test Runtime

**5.68 seconds** (threshold: 30 seconds). Well within budget.

## Deviations from Plan

**1. [Rule 1 - Bug] Incorrect feature extraction paths from plan's interface spec**

- **Found during:** Task 1, feature extraction implementation
- **Issue:** The plan's `<interfaces>` block documented `scenario["category"]` (does not exist — the key is `scenario["_meta"]["source_category"]`) and treated `scenario["context"]["weather"]` as a string (it is a dict — the condition string is at `["context"]["weather"]["condition"]`).
- **Fix:** Used correct paths: `_meta.source_category` for category, `context.weather.condition` for weather condition.
- **Files modified:** tests/test_site_leakage.py (applied during initial write — no separate fix commit needed)

## Self-Check

**Files exist:**
- tests/test_site_leakage.py: FOUND

**Commits exist:**
- be6721b: FOUND (feat(21-02): add site leakage audit test)

**Test output verified:**
- All 3 tests pass in 5.68s
- Full suite: 334 passed, 0 failed
- Probe accuracy: 0.3400 (34%) — below 60% threshold

## Self-Check: PASSED
