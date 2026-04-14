"""Site-type leakage audit for PSAI-Bench scenario generator.

What this test audits
---------------------
SITE_CATEGORY_BLOCKLIST in generators.py prevents certain UCF categories from
appearing at certain site types (e.g., Shoplifting is blocked at solar and
substation sites). This structural rule creates a correlation between the
category distribution and site_type — which means a probe model trained only
on non-site features might be able to infer site_type above chance.

This test trains a logistic regression probe on non-site features and verifies
that site_type prediction accuracy stays at or below 60%. If the blocklist
creates >60% predictability, the multi-site generalization metric (Phase 21
compute_site_generalization_gap) is invalid because a model could cheat by
learning site identity from category patterns rather than decision quality.

Why SITE_CATEGORY_BLOCKLIST is the suspected leakage source
------------------------------------------------------------
The blocklist is asymmetric: solar and substation have 4 and 3 blocked
categories respectively, while commercial/campus block only RoadAccidents.
This means category distributions differ sharply between site types. A probe
observing "no Shoplifting category ever appears" at this site can confidently
predict it is solar or substation — not commercial or campus.

What to do if the test fails
-----------------------------
1. Inspect which feature drives the leakage — check LR coefficients for the
   category one-hot columns.
2. The fix options are:
   a. Reduce SITE_CATEGORY_BLOCKLIST (accept more implausible category-site
      combos in exchange for statistical fairness).
   b. Add post-hoc category resampling to balance per-site distributions.
   c. Accept the leakage and document in EVALUATION_PROTOCOL.md that the
      multi-site generalization metric must not use category-based features.
3. If leakage is confirmed and accepted (not fixed), add:
      @pytest.mark.xfail(strict=False, reason="Known partial leakage from
      SITE_CATEGORY_BLOCKLIST — document in EVALUATION_PROTOCOL.md")
4. Never lower LEAKAGE_THRESHOLD to make this test pass — that defeats its purpose.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from psai_bench.generators import MetadataGenerator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEAKAGE_THRESHOLD = 0.60
SEED = 42
N_SCENARIOS = 600

# Feature names used by the probe — must NOT include site_type or derivatives.
FEATURE_NAMES = [
    "category",     # _meta.source_category — one-hot encoded
    "time_of_day",  # context.time_of_day — one-hot encoded
    "weather",      # context.weather.condition — one-hot encoded
    "zone_type",    # zone.type — one-hot encoded
    "zone_sensitivity",  # zone.sensitivity — integer 1-5
]


# ---------------------------------------------------------------------------
# Helper: scenario generation and feature extraction
# ---------------------------------------------------------------------------

def _generate_scenarios(seed: int = SEED, n: int = N_SCENARIOS) -> list[dict]:
    """Generate UCF Crime scenarios with a fixed seed for reproducibility."""
    gen = MetadataGenerator(seed=seed)
    return gen.generate_ucf_crime(n=n)


def _build_feature_matrix(scenarios: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build feature matrix X and label vector y for the site leakage probe.

    Features (probe inputs — must NOT include site_type):
    - category       : _meta.source_category  (one-hot)
    - time_of_day    : context.time_of_day    (one-hot)
    - weather        : context.weather.condition (one-hot)
    - zone_type      : zone.type              (one-hot)
    - zone_sensitivity: zone.sensitivity      (integer, passed as-is)

    Labels (probe target):
    - site_type      : context.site_type

    Returns:
        X: (n_samples, n_features) numeric matrix
        y: (n_samples,) integer-encoded site_type labels
        col_names: list of column names for X (for auditing)
    """
    categories = [s["_meta"]["source_category"] for s in scenarios]
    time_of_days = [s["context"]["time_of_day"] for s in scenarios]
    weathers = [s["context"]["weather"]["condition"] for s in scenarios]
    zone_types = [s["zone"]["type"] for s in scenarios]
    zone_sensitivities = np.array(
        [s["zone"]["sensitivity"] for s in scenarios], dtype=float
    ).reshape(-1, 1)

    # Encode each categorical feature
    def _onehot(values: list[str]) -> tuple[np.ndarray, list[str]]:
        le = LabelEncoder()
        encoded = le.fit_transform(values).reshape(-1, 1)
        ohe = OneHotEncoder(sparse_output=False)
        matrix = ohe.fit_transform(encoded)
        names = [str(c) for c in le.classes_]
        return matrix, names

    cat_matrix, cat_names = _onehot(categories)
    tod_matrix, tod_names = _onehot(time_of_days)
    weather_matrix, weather_names = _onehot(weathers)
    zone_matrix, zone_names = _onehot(zone_types)

    X = np.hstack([cat_matrix, tod_matrix, weather_matrix, zone_matrix, zone_sensitivities])
    col_names = (
        [f"category={c}" for c in cat_names]
        + [f"time_of_day={t}" for t in tod_names]
        + [f"weather={w}" for w in weather_names]
        + [f"zone_type={z}" for z in zone_names]
        + ["zone_sensitivity"]
    )

    # Encode site_type labels (y)
    site_types = [s["context"]["site_type"] for s in scenarios]
    le_site = LabelEncoder()
    y = le_site.fit_transform(site_types)

    return X, y, col_names


def _run_probe(X: np.ndarray, y: np.ndarray) -> float:
    """Run 5-fold cross-validated logistic regression and return mean accuracy."""
    scores = cross_val_score(
        LogisticRegression(max_iter=500, random_state=0),
        X,
        y,
        cv=5,
        scoring="accuracy",
    )
    return float(scores.mean())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSiteLeakageAudit:
    """SITE-02: Logistic regression probe on non-site features must not predict
    site_type above 60% accuracy.

    Three behaviors tested:
    1. Probe accuracy is at or below 60% (leakage_below_threshold)
    2. Feature matrix does not include any site_type column (feature_extraction_excludes_site_type)
    3. Running twice with seed=42 gives identical accuracy (fixed_seed_reproducibility)
    """

    def test_leakage_below_threshold(self):
        """Logistic regression on non-site features must predict site_type <= 60%.

        A probe accuracy above 60% means the SITE_CATEGORY_BLOCKLIST creates
        enough structural correlation that site identity can be inferred without
        ever reading context.site_type. This would invalidate the multi-site
        generalization metric.
        """
        scenarios = _generate_scenarios(seed=SEED)
        X, y, col_names = _build_feature_matrix(scenarios)
        mean_accuracy = _run_probe(X, y)

        print(f"\nSite leakage probe accuracy (seed={SEED}, n={N_SCENARIOS}): {mean_accuracy:.4f}")
        print(f"Threshold: {LEAKAGE_THRESHOLD}")
        print(f"Result: {'PASS' if mean_accuracy <= LEAKAGE_THRESHOLD else 'FAIL — LEAKAGE DETECTED'}")

        assert mean_accuracy <= LEAKAGE_THRESHOLD, (
            f"Site leakage detected: probe accuracy {mean_accuracy:.3f} > {LEAKAGE_THRESHOLD}. "
            f"Check SITE_CATEGORY_BLOCKLIST in generators.py — categories may uniquely identify sites. "
            f"Features used: {FEATURE_NAMES}"
        )

    def test_feature_extraction_excludes_site_type(self):
        """Feature matrix must not contain any column derived from context.site_type."""
        scenarios = _generate_scenarios(seed=SEED)
        X, y, col_names = _build_feature_matrix(scenarios)

        # Verify no site_type leakage in column names
        site_type_cols = [name for name in col_names if "site_type" in name.lower()]
        assert len(site_type_cols) == 0, (
            f"Feature matrix contains site_type-derived columns: {site_type_cols}. "
            f"Probe must only use: {FEATURE_NAMES}"
        )

        # Verify the expected feature groups are present
        assert any("category=" in c for c in col_names), "category one-hot columns missing"
        assert any("time_of_day=" in c for c in col_names), "time_of_day one-hot columns missing"
        assert any("weather=" in c for c in col_names), "weather one-hot columns missing"
        assert any("zone_type=" in c for c in col_names), "zone_type one-hot columns missing"
        assert "zone_sensitivity" in col_names, "zone_sensitivity column missing"

        print(f"\nFeature columns ({len(col_names)} total): {col_names}")

    def test_fixed_seed_reproducibility(self):
        """Running the probe twice with seed=42 must yield identical accuracy.

        Ensures the leakage audit is deterministic — same seed always produces
        the same probe accuracy, making CI failures reliably attributable to
        generator changes rather than random variance.
        """
        scenarios_a = _generate_scenarios(seed=SEED)
        X_a, y_a, _ = _build_feature_matrix(scenarios_a)
        accuracy_a = _run_probe(X_a, y_a)

        scenarios_b = _generate_scenarios(seed=SEED)
        X_b, y_b, _ = _build_feature_matrix(scenarios_b)
        accuracy_b = _run_probe(X_b, y_b)

        print(f"\nRun 1 accuracy: {accuracy_a:.6f}")
        print(f"Run 2 accuracy: {accuracy_b:.6f}")

        assert accuracy_a == accuracy_b, (
            f"Probe accuracy is not reproducible: run 1={accuracy_a:.6f}, run 2={accuracy_b:.6f}. "
            f"MetadataGenerator(seed={SEED}) must produce identical scenarios on each call."
        )
