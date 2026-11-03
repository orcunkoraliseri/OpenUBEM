"""T11.8 -- reusable newer-skew de-bias corrector (`semantic/debias.py`) +
the opt-in `_ml_tier` hook. Input-Imputation arc, Phase C
(`docs/docs_ACTIVE/input/imputation/docs_Done/PLAN_phaseC_ml_imputer.md`
T11.8). Covers the (a)-(f) "How to test" list plus the CP-3b-local
prerequisite: default-off byte-identity + end-to-end provenance tagging.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from openubem import config
from openubem.semantic import debias
from openubem.semantic import imputation as imp
from openubem.semantic.debias import _thin_strata, debias_newer_skew, debias_stratified
from openubem.semantic.imputation import ImputeConfig, impute_missing

_SEED = 42


# ── (a) marginal match + rank preservation ──────────────────────────────────

class TestDebiasNewerSkewMarginalAndRank:
    def test_corrected_marginal_matches_observed_donor_marginal(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.Series(rng.normal(1970, 15, size=1000))
        base = pd.Series(rng.choice(donors.to_numpy(), size=300, replace=False))
        # Simulate knn-style neighbour-averaging: variance-compress + shift
        # newer, but as a MONOTONIC (rank-preserving) transform of `base`.
        raw_fills = base * 0.3 + 0.7 * donors.mean() + 25.0

        corrected = debias_newer_skew(raw_fills, donors, rng=rng)

        ks_before = stats.ks_2samp(raw_fills, donors).statistic
        ks_after = stats.ks_2samp(corrected, donors).statistic
        assert ks_after < ks_before
        assert ks_after < 0.10  # near-zero -- corrected marginal ~ donor marginal

    def test_rank_order_preserved_vs_raw_fills(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.Series(rng.normal(1970, 15, size=1000))
        base = pd.Series(rng.choice(donors.to_numpy(), size=300, replace=False))
        raw_fills = base * 0.3 + 0.7 * donors.mean() + 25.0

        corrected = debias_newer_skew(raw_fills, donors, rng=rng)

        rho, _ = stats.spearmanr(raw_fills.to_numpy(), corrected.to_numpy())
        assert rho > 0.999


# ── (b) newer-skewed fills pulled toward the (older) donor mean ─────────────

class TestDebiasPullsNewerSkewTowardDonorMean:
    def test_mean_moves_toward_donor_mean(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.Series(rng.uniform(1960, 2010, size=1000))  # mean ~1985
        fills = pd.Series(rng.normal(2010, 3, size=200))  # tight newer cluster

        corrected = debias_newer_skew(fills, donors, rng=rng)

        donor_mean = donors.mean()
        raw_gap = abs(fills.mean() - donor_mean)
        corrected_gap = abs(corrected.mean() - donor_mean)
        assert corrected_gap < raw_gap
        assert corrected.mean() < fills.mean()  # pulled OLDER


# ── (c) thin-stratum decline ─────────────────────────────────────────────────

class TestThinStratumSkip:
    def test_thin_stratum_returned_unchanged(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.concat([
            pd.Series(rng.uniform(1950, 1970, size=50), index=[f"d_office_{i}" for i in range(50)]),
            pd.Series(rng.uniform(1980, 1990, size=5), index=[f"d_retail_{i}" for i in range(5)]),
        ])
        fills = pd.Series(
            [2015.0, 2016.0, 2017.0],
            index=["f_office_0", "f_retail_0", "f_retail_1"],
        )
        strata = pd.concat([
            pd.Series(["office"] * 50, index=donors.index[:50]),
            pd.Series(["retail"] * 5, index=donors.index[50:]),
            pd.Series(["office", "retail", "retail"], index=fills.index),
        ])

        corrected = debias_stratified(fills, donors, strata, rng=rng, min_donors=30)

        assert corrected.loc["f_retail_0"] == fills.loc["f_retail_0"]
        assert corrected.loc["f_retail_1"] == fills.loc["f_retail_1"]
        assert corrected.loc["f_office_0"] != fills.loc["f_office_0"]

    def test_thin_strata_helper_flags_the_right_label(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.concat([
            pd.Series(rng.uniform(1950, 1970, size=50), index=[f"d_office_{i}" for i in range(50)]),
            pd.Series(rng.uniform(1980, 1990, size=5), index=[f"d_retail_{i}" for i in range(5)]),
        ])
        strata = pd.Series(
            ["office"] * 50 + ["retail"] * 5,
            index=donors.index,
        )
        thin = _thin_strata(donors, strata, min_donors=30)
        assert thin == {"retail"}


# ── (d) determinism ──────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_seed_byte_identical(self):
        rng = np.random.default_rng(_SEED)
        donors = pd.Series(rng.normal(1970, 15, size=500))
        fills = pd.Series(rng.normal(2005, 5, size=100))

        out1 = debias_newer_skew(fills, donors, rng=np.random.default_rng(_SEED))
        out2 = debias_newer_skew(fills, donors, rng=np.random.default_rng(_SEED))
        pd.testing.assert_series_equal(out1, out2)

    def test_output_independent_of_rng_value(self):
        """The transform has no free/random component (rank + linear
        interpolation only) -- `rng` is accepted for API symmetry but not
        consumed, so ANY rng (or None) yields the identical result."""
        rng_seed = np.random.default_rng(_SEED)
        donors = pd.Series(rng_seed.normal(1970, 15, size=500))
        fills = pd.Series(rng_seed.normal(2005, 5, size=100))

        out_a = debias_newer_skew(fills, donors, rng=None)
        out_b = debias_newer_skew(fills, donors, rng=np.random.default_rng(999))
        pd.testing.assert_series_equal(out_a, out_b)


# ── (f) structural no-EUI guard ──────────────────────────────────────────────

class TestNoEUILeakage:
    """Mirrors `test_ml_imputer.py::TestNoEUILeakage` -- structural pin for
    plan §2 rule 3 / T11.8 "How": `debias.py` must never reference an
    EUI/`total_eui`/`*_eui_kwh_m2` column by name anywhere in its call graph
    (the quantile-mapping transform reads only two empirical CDFs of
    OBSERVED data)."""

    _FUNCS = (debias_newer_skew, debias_stratified, _thin_strata)

    def test_no_function_code_references_eui_by_name(self):
        for func in self._FUNCS:
            referenced = set(func.__code__.co_names)
            leaked = [n for n in referenced if "eui" in n.lower()]
            assert not leaked, (
                f"{func.__qualname__} co_names references EUI-like name(s) {leaked} -- "
                "zero-fitted-params violation (plan §2 rule 3)."
            )


# ── (e) no-op byte-identity + end-to-end `_ml_tier` wiring ──────────────────

class _FakeKnnImputer:
    """Stub MLImputer: constant raw prediction (severe synthetic newer-skew,
    no per-row differentiating signal) + HIGH confidence on every row --
    isolates the T11.8 hook from needing a real fitted sklearn model."""

    is_classifier = False

    def __init__(self, raw_value: float):
        self._raw_value = raw_value

    def predict(self, X):
        return pd.Series([self._raw_value] * len(X), index=X.index, dtype=float)

    def confidence(self, X):
        return pd.Series(["HIGH"] * len(X), index=X.index, dtype=object)


def _debias_wiring_gdf(rng):
    """238 rows: 200 observed 'office' donors (~1950-1970), 5 observed
    'retail' donors (~1980-1990, below min_donors=30), 30 masked 'office'
    rows, 3 masked 'retail' rows -- all `year_built` NaN on the masked rows."""
    n_office_obs, n_retail_obs, n_office_mask, n_retail_mask = 200, 5, 30, 3
    use_class = (
        ["office"] * n_office_obs + ["retail"] * n_retail_obs
        + ["office"] * n_office_mask + ["retail"] * n_retail_mask
    )
    year_built = np.concatenate([
        rng.uniform(1950, 1970, size=n_office_obs),
        rng.uniform(1980, 1990, size=n_retail_obs),
        np.full(n_office_mask, np.nan),
        np.full(n_retail_mask, np.nan),
    ])
    gdf = pd.DataFrame({"use_class": use_class, "year_built": year_built})
    office_mask_idx = gdf.index[n_office_obs + n_retail_obs: n_office_obs + n_retail_obs + n_office_mask]
    retail_mask_idx = gdf.index[n_office_obs + n_retail_obs + n_office_mask:]
    return gdf, office_mask_idx, retail_mask_idx


@pytest.mark.skipif(
    not hasattr(config, "IMPUTE_DEBIAS_NEWERSKEW"),
    reason=(
        "OPEN-44 / OPEN-17: config.IMPUTE_DEBIAS_NEWERSKEW was never shipped to "
        "openubem/config.py. Wiring it (and the _ml_tier hook it gates) is a "
        "promotion decision reserved to the user (OPEN-17), not something this test "
        "may enact. Every test in this class needs the flag, so the whole class is "
        "guarded; it will run again unmodified once the flag lands."
    ),
)
class TestMlTierDebiasHook:
    def test_disabled_by_default_never_calls_debias(self, monkeypatch):
        """(e) no-op byte-identity: with `config.IMPUTE_DEBIAS_NEWERSKEW`
        left at its shipped all-False default, `debias_stratified` must
        never be invoked -- proving `_ml_tier`'s fill path is byte-identical
        to pre-T11.8 (the conditional block is never entered)."""
        assert not config.IMPUTE_DEBIAS_NEWERSKEW.get("year_built", False)

        calls = []
        original = debias.debias_stratified

        def spy(*a, **k):
            calls.append(1)
            return original(*a, **k)

        monkeypatch.setattr(debias, "debias_stratified", spy)
        monkeypatch.setattr(imp, "build_ml_imputer", lambda *a, **k: _FakeKnnImputer(2015.0))
        monkeypatch.setitem(config.IMPUTE_ML_METHOD_BY_TARGET, "year_built", "knn")

        rng = np.random.default_rng(_SEED)
        gdf, office_idx, retail_idx = _debias_wiring_gdf(rng)
        mask = gdf["year_built"].isna()

        value, token = imp._ml_tier(gdf, "year_built", mask, rng)

        assert calls == []
        # raw fake fill (2015.0) passes through completely unmodified
        assert (value.loc[office_idx] == 2015.0).all()
        assert (value.loc[retail_idx] == 2015.0).all()
        assert (token.loc[office_idx] == "ML_KNN_HIGH").all()

    def test_enabled_corrects_non_thin_stratum_and_skips_thin_stratum(self, monkeypatch):
        """(rule 3/4 wiring) with the flag ON: the non-thin 'office' stratum
        (200 donors >= min_donors=30) gets quantile-mapped away from the
        constant newer-skewed raw fill toward the older donor range and
        tagged DEBIAS_NEWERSKEW_QMAP; the thin 'retail' stratum (5 donors <
        30) keeps its raw fill unchanged and is tagged
        DEBIAS_SKIPPED_THINSTRATUM. The ML_KNN_<TIER> token is unaffected
        either way."""
        monkeypatch.setattr(imp, "build_ml_imputer", lambda *a, **k: _FakeKnnImputer(2015.0))
        monkeypatch.setitem(config.IMPUTE_ML_METHOD_BY_TARGET, "year_built", "knn")
        monkeypatch.setitem(config.IMPUTE_DEBIAS_NEWERSKEW, "year_built", True)

        rng = np.random.default_rng(_SEED)
        gdf, office_idx, retail_idx = _debias_wiring_gdf(rng)
        mask = gdf["year_built"].isna()

        value, token = imp._ml_tier(gdf, "year_built", mask, rng)

        # office: corrected, pulled well below the raw 2015.0 fake fill,
        # toward the ~1950-1970 donor range (all raw fills tied -> maps to
        # the donor median, ~1960).
        assert (value.loc[office_idx] < 2000.0).all()
        assert value.loc[office_idx].mean() == pytest.approx(1960.0, abs=15.0)
        # retail: thin stratum -- raw fill kept exactly
        assert (value.loc[retail_idx] == 2015.0).all()

        # token unaffected by debias either way
        assert (token.loc[office_idx] == "ML_KNN_HIGH").all()
        assert (token.loc[retail_idx] == "ML_KNN_HIGH").all()

        # provenance flags appended alongside the token, on `gdf` itself
        # (mutated in place by the hook -- see `_ml_tier` docstring)
        assert gdf.loc[office_idx, "data_quality_flag"].str.contains("DEBIAS_NEWERSKEW_QMAP").all()
        assert gdf.loc[retail_idx, "data_quality_flag"].str.contains("DEBIAS_SKIPPED_THINSTRATUM").all()

    def test_global_fallback_fires_when_no_stratifier_column_present(self, monkeypatch):
        """T11.8b: with the flag ON, `method == 'knn'`, and NEITHER
        `use_class` NOR `archetype_id` present as a column, the hook must NOT
        stay a no-op (the pre-T11.8b behaviour) -- it applies
        `debias_newer_skew` GLOBALLY (one pool, no strata) over the whole
        observed-donor marginal and tags every corrected row
        `DEBIAS_NEWERSKEW_QMAP_GLOBAL` (distinct from the stratified
        `DEBIAS_NEWERSKEW_QMAP`)."""
        monkeypatch.setattr(imp, "build_ml_imputer", lambda *a, **k: _FakeKnnImputer(2015.0))
        monkeypatch.setitem(config.IMPUTE_ML_METHOD_BY_TARGET, "year_built", "knn")
        monkeypatch.setitem(config.IMPUTE_DEBIAS_NEWERSKEW, "year_built", True)

        rng = np.random.default_rng(_SEED)
        n_obs, n_mask = 200, 30
        year_built = np.concatenate([
            rng.uniform(1950, 1970, size=n_obs),
            np.full(n_mask, np.nan),
        ])
        # No `use_class` / `archetype_id` column at all -- mirrors the real
        # Stage-1 01_buildings.gpkg schema that triggered the T11.8b pivot.
        gdf = pd.DataFrame({"year_built": year_built})
        mask_idx = gdf.index[n_obs:]
        mask = gdf["year_built"].isna()

        value, token = imp._ml_tier(gdf, "year_built", mask, rng)

        # global donor pool (200 >= min_donors=30) clears the floor -> fires
        assert (value.loc[mask_idx] < 2000.0).all()
        assert value.loc[mask_idx].mean() == pytest.approx(1960.0, abs=15.0)
        assert (token.loc[mask_idx] == "ML_KNN_HIGH").all()
        assert gdf.loc[mask_idx, "data_quality_flag"].str.contains(
            "DEBIAS_NEWERSKEW_QMAP_GLOBAL"
        ).all()
        # the stratified-only flag must NOT appear on these rows
        assert not gdf.loc[mask_idx, "data_quality_flag"].str.contains(
            "DEBIAS_NEWERSKEW_QMAP$", regex=True
        ).any()

    def test_global_fallback_noop_below_min_donors(self, monkeypatch):
        """T11.8b: no stratifier column AND the global observed-donor pool
        is below `min_donors=30` -> stays a no-op, exactly as pre-T11.8b (no
        flag, raw fill kept)."""
        monkeypatch.setattr(imp, "build_ml_imputer", lambda *a, **k: _FakeKnnImputer(2015.0))
        monkeypatch.setitem(config.IMPUTE_ML_METHOD_BY_TARGET, "year_built", "knn")
        monkeypatch.setitem(config.IMPUTE_DEBIAS_NEWERSKEW, "year_built", True)

        rng = np.random.default_rng(_SEED)
        n_obs, n_mask = 10, 5  # below min_donors=30
        year_built = np.concatenate([
            rng.uniform(1950, 1970, size=n_obs),
            np.full(n_mask, np.nan),
        ])
        gdf = pd.DataFrame({"year_built": year_built})
        mask_idx = gdf.index[n_obs:]
        mask = gdf["year_built"].isna()

        value, token = imp._ml_tier(gdf, "year_built", mask, rng)

        assert (value.loc[mask_idx] == 2015.0).all()
        assert (token.loc[mask_idx] == "ML_KNN_HIGH").all()
        if "data_quality_flag" in gdf.columns:
            assert not gdf.loc[mask_idx, "data_quality_flag"].str.contains(
                "DEBIAS_NEWERSKEW_QMAP_GLOBAL"
            ).any()

    def test_disabled_for_non_knn_method_even_if_flag_set(self, monkeypatch):
        """The hook only fires for `method == 'knn'` (T11.8 "How"/"What" --
        "the only target the flag ships for"). With `missforest` selected,
        the flag being True must still be a no-op."""
        monkeypatch.setattr(imp, "build_ml_imputer", lambda *a, **k: _FakeKnnImputer(2015.0))
        monkeypatch.setitem(config.IMPUTE_ML_METHOD_BY_TARGET, "year_built", "missforest")
        monkeypatch.setitem(config.IMPUTE_DEBIAS_NEWERSKEW, "year_built", True)

        rng = np.random.default_rng(_SEED)
        gdf, office_idx, retail_idx = _debias_wiring_gdf(rng)
        mask = gdf["year_built"].isna()

        value, token = imp._ml_tier(gdf, "year_built", mask, rng)

        assert (value.loc[office_idx] == 2015.0).all()
        assert (value.loc[retail_idx] == 2015.0).all()
        assert (token.loc[office_idx] == "ML_MISSFOREST_HIGH").all()


# ── full-pipeline default-off byte-identity via `impute_missing` ────────────

class TestImputeMissingDefaultOff:
    def test_opt_in_ml_without_debias_flag_matches_two_runs(self):
        """A second, independent proof at the `impute_missing` public-API
        level (not just the `_ml_tier` unit): two identical runs (opt-in
        `ml`, `IMPUTE_DEBIAS_NEWERSKEW` left at its shipped default) produce
        byte-identical output -- determinism + no hidden state leak from the
        T11.8 addition."""
        rng = np.random.default_rng(_SEED)
        n = 1200
        gdf = pd.DataFrame({
            "footprint_area_m2": rng.uniform(50, 500, size=n),
            "centroid_x": rng.uniform(0, 5000, size=n),
            "centroid_y": rng.uniform(0, 5000, size=n),
            "use_class": rng.choice(["office", "residential"], size=n),
            "archetype_id": rng.choice(["office", "residential"], size=n),
            "year_built": 1950 + rng.integers(0, 70, size=n).astype(float),
        })
        mask_idx = rng.choice(gdf.index, size=40, replace=False)
        gdf.loc[mask_idx, "year_built"] = np.nan

        cfg = ImputeConfig(per_input_tiers={"year_built": ("ml", "statistical")})
        out1 = impute_missing(gdf, cfg=cfg, rng=np.random.default_rng(_SEED))
        out2 = impute_missing(gdf, cfg=cfg, rng=np.random.default_rng(_SEED))
        pd.testing.assert_frame_equal(out1, out2)
