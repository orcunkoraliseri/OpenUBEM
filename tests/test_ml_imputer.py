"""T11.1-T11.5 -- classical-ML imputer (`build_ml_imputer` / §3E ML tier).

Input-Imputation arc, Phase C (`PLAN_phaseC_ml_imputer.md`). Covers every
"How to test" in T11.1 (registry/floors/no-EUI guard), T11.2 (confidence/
tokens), T11.3 (`_ml_tier` wiring + canonical-order reorder), T11.4
(`impute_column` auto/model_path, KDE/PDE byte-identity), T11.5 (joblib
persistence). Stops at CP-3a -- no evaluation-harness / EUI content here
(that is T11.6, gated behind manager audit).
"""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from scipy import stats
from shapely.geometry import Point

from openubem import config
from openubem.semantic import imputation as imp
from openubem.semantic.imputation import (
    BelowFloorError,
    ImputeConfig,
    MLImputer,
    build_ml_imputer,
    impute_column,
    impute_missing,
    load_ml_imputer,
    save_ml_imputer,
)

_SEED = 42
_FEATURE_COLS = ["footprint_area_m2", "centroid_x", "centroid_y", "use_class", "archetype_id"]


# ── shared fixtures ───────────────────────────────────────────────────────

def _synthetic_gdf(n, rng, level_signal=True):
    footprint = rng.uniform(50, 500, size=n)
    x = rng.uniform(0, 5000, size=n)
    y = rng.uniform(0, 5000, size=n)
    use_class = rng.choice(["office", "residential"], size=n)
    year_built = 1950 + rng.integers(0, 70, size=n).astype(float)
    if level_signal:
        levels = np.clip(np.round(1 + footprint / 50.0 + rng.normal(scale=0.05, size=n)), 1, 20)
    else:
        levels = np.clip(np.round(5 + rng.normal(scale=8.0, size=n)), 1, 30)
    return gpd.GeoDataFrame(
        {
            "footprint_area_m2": footprint,
            "centroid_x": x,
            "centroid_y": y,
            "use_class": use_class,
            "archetype_id": use_class,
            "year_built": year_built,
            "levels": levels,
        },
        geometry=[Point(a, b) for a, b in zip(x, y)],
    )


@pytest.fixture(scope="module")
def big_gdf():
    """>=6000 rows -- clears every method's floor including histgbm (>=5000)."""
    return _synthetic_gdf(6000, np.random.default_rng(_SEED), level_signal=True)


@pytest.fixture(scope="module")
def small_gdf():
    """50 rows -- below every method's floor."""
    return _synthetic_gdf(50, np.random.default_rng(_SEED), level_signal=True)


# ── T11.1 -- build_ml_imputer core + 6-method registry ──────────────────────

class TestBuildImputer:
    def test_fits_on_large_frame_and_predicts_finite_values(self, big_gdf):
        imputer = build_ml_imputer(big_gdf, "year_built", _FEATURE_COLS, method="missforest")
        X = big_gdf.iloc[:50]
        preds = imputer.predict(X)
        assert np.isfinite(preds.to_numpy(dtype=float)).all()

    def test_below_floor_raises_below_floor_error(self, small_gdf):
        with pytest.raises(BelowFloorError) as exc:
            build_ml_imputer(small_gdf, "year_built", _FEATURE_COLS, method="missforest")
        assert exc.value.method == "missforest"
        assert exc.value.floor == 1000
        assert exc.value.n_observed == len(small_gdf)

    def test_eui_feature_column_raises(self, big_gdf):
        gdf = big_gdf.assign(total_eui_kwh_m2=1.0)
        with pytest.raises(ValueError, match="zero-fitted-params"):
            build_ml_imputer(gdf, "year_built", _FEATURE_COLS + ["total_eui_kwh_m2"])

    def test_eui_target_column_raises(self, big_gdf):
        gdf = big_gdf.rename(columns={"year_built": "total_eui_kwh_m2"})
        with pytest.raises(ValueError, match="zero-fitted-params"):
            build_ml_imputer(gdf, "total_eui_kwh_m2", _FEATURE_COLS)

    @pytest.mark.parametrize("method", ["missforest", "mice", "knn", "rf", "histgbm", "linear"])
    def test_each_method_constructs_and_fits(self, big_gdf, method):
        imputer = build_ml_imputer(big_gdf, "year_built", _FEATURE_COLS, method=method)
        assert isinstance(imputer, MLImputer)
        preds = imputer.predict(big_gdf.iloc[:20])
        assert np.isfinite(preds.to_numpy(dtype=float)).all()

    def test_unknown_method_raises(self, big_gdf):
        with pytest.raises(ValueError, match="unknown method"):
            build_ml_imputer(big_gdf, "year_built", _FEATURE_COLS, method="deep_generative")

    def test_classifier_target_use_class(self, big_gdf):
        # use_class must correlate with a feature for a classifier to beat
        # chance -- big_gdf's use_class is an independent random draw, so
        # build a dedicated frame with a real footprint->use_class signal.
        gdf = big_gdf.copy()
        gdf["use_class"] = np.where(gdf["footprint_area_m2"] > 275, "office", "residential")
        gdf["archetype_id"] = gdf["use_class"]
        mask_idx = gdf.index[:80]
        true_vals = gdf.loc[mask_idx, "use_class"].copy()
        gdf.loc[mask_idx, "use_class"] = None
        imputer = build_ml_imputer(
            gdf, "use_class", ["footprint_area_m2", "centroid_x", "centroid_y", "year_built"],
            method="rf",
        )
        assert imputer.is_classifier
        preds = imputer.predict(gdf.loc[mask_idx])
        assert (preds.to_numpy() == true_vals.to_numpy()).mean() > 0.7


# ── T11.2 -- dispersion -> confidence + ML_<METHOD>_<TIER> tokens ──────────

class TestConfidence:
    def test_clean_signal_yields_mostly_high(self, big_gdf):
        imputer = build_ml_imputer(big_gdf, "levels", _FEATURE_COLS, method="rf")
        conf = imputer.confidence(big_gdf.iloc[:80])
        counts = conf.value_counts()
        assert counts.get("HIGH", 0) / len(conf) > 0.9

    def test_noisy_signal_yields_more_low(self, big_gdf):
        rng = np.random.default_rng(_SEED)
        noisy = _synthetic_gdf(len(big_gdf), rng, level_signal=False)
        imputer = build_ml_imputer(noisy, "levels", _FEATURE_COLS, method="rf")
        conf = imputer.confidence(noisy.iloc[:80])
        counts = conf.value_counts()
        assert counts.get("LOW", 0) + counts.get("MEDIUM", 0) > counts.get("HIGH", 0)

    def test_confidence_values_are_canonical_tiers(self, big_gdf):
        imputer = build_ml_imputer(big_gdf, "year_built", _FEATURE_COLS, method="rf")
        conf = imputer.confidence(big_gdf.iloc[:30])
        assert set(conf.unique()).issubset({"HIGH", "MEDIUM", "LOW"})

    def test_ml_tier_token_suffix_agrees_with_confidence(self, big_gdf):
        gdf = big_gdf.copy()
        mask_idx = gdf.index[:60]
        gdf.loc[mask_idx, "year_built"] = np.nan
        remaining = gdf["year_built"].isna()
        value, token = imp._ml_tier(gdf, "year_built", remaining, np.random.default_rng(_SEED))
        filled = value.notna()
        assert filled.any()
        for idx in gdf.index[filled]:
            tok = token.loc[idx]
            assert tok.startswith("ML_MISSFOREST_")
            assert tok.endswith("HIGH") or tok.endswith("MED")
        # LOW-confidence rows (if any) must be declined (value stays null)
        declined = remaining & ~filled
        assert (value.loc[declined].isna()).all()


# ── T11.3 -- _ml_tier wiring + canonical-order reorder + opt-in config ─────

class TestRouting:
    def test_ml_fills_residual_after_spatial_group_median_declines_rest(self, big_gdf):
        """Spatial tier is dense/uniform on the main grid (always finds
        high-confidence neighbours) -- so to prove ML fills the *residual*
        spatial declines, mask an isolated MNAR pocket (a tight cluster far
        from the main grid, all masked together): each pocket row's own
        neighbourhood is >=60% missing (its neighbours are the OTHER pocket
        rows), tripping T06's MNAR guard so spatial declines them and ML
        (which only needs global complete cases, not local ones) picks them
        up. Statistical (group-median) is available as the final fallback
        for anything both decline."""
        rng = np.random.default_rng(_SEED)
        gdf = big_gdf.copy()

        pocket_x = rng.uniform(9000, 9050, size=80)
        pocket_y = rng.uniform(9000, 9050, size=80)
        pocket = gpd.GeoDataFrame(
            {
                "footprint_area_m2": rng.uniform(50, 500, size=80),
                "centroid_x": pocket_x,
                "centroid_y": pocket_y,
                "use_class": rng.choice(["office", "residential"], size=80),
                "archetype_id": rng.choice(["office", "residential"], size=80),
                "year_built": 1950 + rng.integers(0, 70, size=80).astype(float),
                "levels": rng.integers(1, 10, size=80).astype(float),
            },
            geometry=[Point(a, b) for a, b in zip(pocket_x, pocket_y)],
        )
        gdf = pd.concat([gdf, pocket], ignore_index=True)
        mask_idx = gdf.index[-80:]
        gdf.loc[mask_idx, "year_built"] = np.nan

        out = impute_missing(
            gdf,
            cfg=ImputeConfig(per_input_tiers={"year_built": ("spatial", "ml", "statistical")}),
            rng=np.random.default_rng(_SEED),
        )
        assert out.loc[mask_idx, "year_built"].notna().all()
        tokens = out.loc[mask_idx, "provenance_year_built"]
        assert tokens.isin(["HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED", "ML_MISSFOREST_HIGH",
                             "ML_MISSFOREST_MED", "GROUPMODE_MED"]).all()
        # spatial must have declined (MNAR pocket) and ML must have fired
        assert not tokens.isin(["HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED"]).any()
        assert tokens.isin(["ML_MISSFOREST_HIGH", "ML_MISSFOREST_MED"]).any()

    def test_sub_floor_frame_ml_skipped_falls_to_groupmode(self, small_gdf):
        gdf = small_gdf.copy()
        gdf.loc[gdf.index[:10], "year_built"] = np.nan
        out = impute_missing(
            gdf,
            cfg=ImputeConfig(per_input_tiers={"year_built": ("ml", "statistical")}),
            rng=np.random.default_rng(_SEED),
        )
        filled_tokens = out.loc[out.index[:10], "provenance_year_built"]
        assert (filled_tokens == "GROUPMODE_MED").all()

    def test_canonical_order_reorder_is_behaviour_preserving_for_non_ml_routing(self, monkeypatch, big_gdf):
        """Proves the T11.3 reorder (`fusion,spatial,ml,statistical`) changes
        nothing for any run that never enables `ml` -- byte-identity between
        the reordered canonical tuple and the pre-T11.3 tuple, both restricted
        to a tier set that excludes `ml`."""
        rng = np.random.default_rng(_SEED)
        gdf = big_gdf.copy()
        mask_idx = rng.choice(gdf.index, size=40, replace=False)
        gdf.loc[mask_idx, "levels"] = np.nan

        cfg = ImputeConfig(enabled_tiers=("spatial", "statistical"))
        out_new_order = impute_missing(gdf, cfg=cfg, rng=np.random.default_rng(_SEED))

        monkeypatch.setattr(imp, "_CANONICAL_TIER_ORDER", ("fusion", "spatial", "statistical", "ml"))
        out_old_order = impute_missing(gdf, cfg=cfg, rng=np.random.default_rng(_SEED))

        pd.testing.assert_frame_equal(out_new_order, out_old_order)

    def test_ml_never_fires_when_not_in_enabled_tiers(self, big_gdf):
        rng = np.random.default_rng(_SEED)
        gdf = big_gdf.copy()
        mask_idx = rng.choice(gdf.index, size=30, replace=False)
        gdf.loc[mask_idx, "year_built"] = np.nan
        out = impute_missing(
            gdf, cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")),
            rng=np.random.default_rng(_SEED),
        )
        tokens = out.loc[mask_idx, "provenance_year_built"]
        assert not tokens.str.startswith("ML_").any()


# ── T11.4 -- impute_column: method='auto' + model_path, KDE/PDE byte-identity ──

class TestImputeColumnAuto:
    def test_kde_output_matches_independent_reference(self):
        """Golden-array check: impute_column(method='kde') must reproduce the
        exact same gaussian_kde-resample values an independent, from-scratch
        call to scipy produces under the same seed (proves T11.4 did not
        perturb the pre-existing KDE code path)."""
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.nan, np.nan])
        rng1 = np.random.default_rng(7)
        result = impute_column(s, method="kde", rng=rng1)

        observed = s.dropna().astype(float)
        kde = stats.gaussian_kde(observed, bw_method="scott")
        rng2 = np.random.default_rng(7)
        expected = kde.resample(3, seed=rng2)[0]

        np.testing.assert_array_equal(result[s.isna()].to_numpy(), expected)

    def test_pde_output_matches_independent_reference(self):
        s = pd.Series([np.nan, np.nan, np.nan, np.nan])
        bounds = (0.0, 10.0)
        rng1 = np.random.default_rng(11)
        result = impute_column(s, method="pde", bounds=bounds, rng=rng1)

        rng2 = np.random.default_rng(11)
        expected = rng2.uniform(bounds[0], bounds[1], size=4)
        np.testing.assert_array_equal(result.to_numpy(), expected)

    def test_auto_routes_to_kde_for_partial_missing(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, np.nan, np.nan])
        r_auto = impute_column(s, method="auto", rng=np.random.default_rng(99))
        r_kde = impute_column(s, method="kde", rng=np.random.default_rng(99))
        pd.testing.assert_series_equal(r_auto, r_kde)

    def test_auto_routes_to_pde_for_all_missing(self):
        s = pd.Series([np.nan, np.nan, np.nan])
        bounds = (1.0, 5.0)
        r_auto = impute_column(s, method="auto", bounds=bounds, rng=np.random.default_rng(3))
        r_pde = impute_column(s, method="pde", bounds=bounds, rng=np.random.default_rng(3))
        pd.testing.assert_series_equal(r_auto, r_pde)

    def test_model_path_loads_persisted_imputer_and_fills(self, big_gdf):
        imputer = build_ml_imputer(big_gdf, "year_built", [], method="missforest")
        path = os.path.join(tempfile.gettempdir(), "test_ml_imputer_auto_route.joblib")
        save_ml_imputer(imputer, path)

        s = pd.Series([1990.0, np.nan, 2000.0, np.nan])
        result = impute_column(s, method="auto", model_path=path, rng=np.random.default_rng(1))
        assert result.notna().all()
        assert result.iloc[0] == 1990.0
        assert result.iloc[2] == 2000.0

    def test_ml_method_requires_model_path(self):
        s = pd.Series([1.0, np.nan])
        with pytest.raises(ValueError, match="model_path"):
            impute_column(s, method="ml", rng=np.random.default_rng(1))

    def test_unknown_method_still_raises(self):
        s = pd.Series([np.nan])
        with pytest.raises(ValueError, match="unknown method"):
            impute_column(s, method="histogram", rng=np.random.default_rng(1))


# ── T11.5 -- joblib persistence + frozen-reload determinism ────────────────

class TestPersistence:
    @pytest.mark.parametrize("method", ["missforest", "mice", "knn", "rf", "histgbm", "linear"])
    def test_reload_predict_and_confidence_are_byte_identical(self, big_gdf, method):
        imputer = build_ml_imputer(big_gdf, "year_built", _FEATURE_COLS, method=method)
        X = big_gdf.iloc[:40]
        p1 = imputer.predict(X)
        c1 = imputer.confidence(X)

        path = os.path.join(tempfile.gettempdir(), f"test_ml_imputer_persist_{method}.joblib")
        save_ml_imputer(imputer, path)
        reloaded = load_ml_imputer(path)

        p2 = reloaded.predict(X)
        c2 = reloaded.confidence(X)
        np.testing.assert_array_equal(p1.to_numpy(dtype=float), p2.to_numpy(dtype=float))
        assert (c1 == c2).all()

    def test_reload_classifier_round_trip(self, big_gdf):
        gdf = big_gdf.copy()
        mask_idx = gdf.index[:30]
        gdf.loc[mask_idx, "use_class"] = None
        imputer = build_ml_imputer(
            gdf, "use_class", ["footprint_area_m2", "centroid_x", "centroid_y", "year_built"],
            method="rf",
        )
        X = gdf.loc[mask_idx]
        p1 = imputer.predict(X)

        path = os.path.join(tempfile.gettempdir(), "test_ml_imputer_persist_classifier.joblib")
        save_ml_imputer(imputer, path)
        reloaded = load_ml_imputer(path)
        p2 = reloaded.predict(X)
        assert (p1.to_numpy() == p2.to_numpy()).all()


# ── zero-fitted-params structural guard (mirrors eui_impact.TestNoImputerFeedback) ──

class TestNoEUILeakage:
    """Structural pin for plan §2 rule 3: no EUI/total_eui/*_eui_kwh_m2 column
    may ever appear in an ML fit call graph. Mirrors
    `eui_impact.TestNoImputerFeedback`'s `__code__.co_names` inspection."""

    _FUNCS = (
        build_ml_imputer,
        MLImputer.predict,
        MLImputer.confidence,
        MLImputer._prep,
        MLImputer._encode_matrix,
        imp._ml_tier,
        imp._ml_feature_cols_for,
        imp._build_supervised_estimator,
    )

    _GUARD_NAME = "_assert_no_eui_leakage"  # the guard itself legitimately names "eui"

    def test_no_function_code_references_eui_by_name(self):
        for func in self._FUNCS:
            referenced = set(func.__code__.co_names) - {self._GUARD_NAME}
            leaked = [n for n in referenced if "eui" in n.lower()]
            assert not leaked, (
                f"{func.__qualname__} co_names references EUI-like name(s) {leaked} -- "
                "zero-fitted-params violation (plan §2 rule 3)."
            )

    def test_build_ml_imputer_invokes_the_eui_guard(self):
        assert "_assert_no_eui_leakage" in build_ml_imputer.__code__.co_names

    def test_guard_raises_on_eui_columns(self):
        with pytest.raises(ValueError, match="zero-fitted-params"):
            imp._assert_no_eui_leakage(["total_eui_kwh_m2", "heating_eui_kwh_m2"])

    def test_guard_passes_clean_columns(self):
        imp._assert_no_eui_leakage(["footprint_area_m2", "centroid_x", "use_class"])


# ── default run stays untouched (opt-in only, plan §2 rule 6) ──────────────

class TestOptInOnly:
    def test_ml_not_in_default_enabled_tiers(self):
        assert "ml" not in config.IMPUTE_ENABLED_TIERS

    def test_default_impute_missing_never_invokes_ml_tier(self, monkeypatch, big_gdf):
        ml_calls = []
        monkeypatch.setattr(imp, "_ml_tier", lambda *a, **k: ml_calls.append(1) or (
            pd.Series(np.nan, index=a[0].index), pd.Series([None] * len(a[0]), index=a[0].index)
        ))
        gdf = big_gdf.copy()
        gdf.loc[gdf.index[:20], "year_built"] = np.nan
        impute_missing(gdf, rng=np.random.default_rng(_SEED))
        assert ml_calls == []
