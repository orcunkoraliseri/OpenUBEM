"""T01-T09b -- draw tier registry, all six pure methods, `_draw_tier` wiring,
the zero-EUI/determinism structural guard, and the CP-DRAW metric harness
extension (`openubem/semantic/draw_methods.py` + `openubem/semantic/
imputation.py::_draw_tier` + `openubem/validation/mask_recover.py`).

Input-Imputation arc, Part II of `docs/docs_ACTIVE/input/imputation/
implementation/IMPLEMENTATION_phaseC_ml_imputer.md` (the variance-preserving
`draw` tier, opt-in / OFF). Load-bearing properties under test:

  (1) `config.IMPUTE_ENABLED_TIERS` is untouched (`draw` stays out of the
      default tuple) -- as of T07, `_CANONICAL_TIER_ORDER`/
      `_TIER_HANDLER_NAMES` in `imputation.py` DO know about `draw` (it is
      reachable), but ONLY via an explicit `ImputeConfig.per_input_tiers`
      opt-in; the default-cfg `impute_missing` router output stays
      byte-identical, since `draw` is never in the default enabled tuple.
  (2) `DRAW_METHODS` is a typed dict registry holding all six methods (`kde`,
      `pmm`, `hotdeck`, `resid`, `catfreq`, `abb`). The `DRAW_<METHOD>_<TIER>`
      token constants exist with the exact strings (manager-ratification
      request, T01 "How", ratified at CP-A).
  (3) Each method restores variance and beats a median-fill on KS distance by
      a wide margin, respects observed-range clamping (or the real-donor
      invariant), abstains cleanly on small/absent strata, and is
      deterministic (same seed -> byte-identical draws).
  (4) T07: `_draw_tier` dispatches on `config.IMPUTE_DRAW_METHOD_BY_TARGET`,
      stamps `DRAW_*_HIGH/MED` tokens, and is reachable ONLY opt-in.
  (5) T08: no draw function (or `_draw_tier`) ever references an EUI-like
      name in its `__code__.co_names`; the whole `draw` tier is deterministic
      end-to-end via `impute_missing`.
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps
from shapely.geometry import Point

from openubem import config
from openubem.semantic import draw_methods as dm
from openubem.semantic import imputation as imp
from openubem.semantic.imputation import impute_missing


# ── T01 -- registry scaffold + opt-in config surface + byte-identity floor ──

class TestDefaultByteIdentity:
    def test_enabled_tiers_untouched(self):
        assert config.IMPUTE_ENABLED_TIERS == ("fusion", "spatial", "statistical")
        assert "draw" not in config.IMPUTE_ENABLED_TIERS

    def test_canonical_tier_order_and_handler_registry_wired_but_opt_in(self):
        # T07 wires "draw" into the canonical order/handler registry (between
        # "ml" and "statistical") so an EXPLICIT per_input_tiers request can
        # reach it -- but it is still never in the DEFAULT enabled tuple
        # (config.IMPUTE_ENABLED_TIERS, asserted separately above), so a
        # caller that never opts in never triggers _draw_tier at all.
        assert imp._CANONICAL_TIER_ORDER == ("fusion", "spatial", "ml", "draw", "statistical")
        assert imp._TIER_HANDLER_NAMES["draw"] == "_draw_tier"

    def test_default_cfg_router_output_unchanged(self):
        # Same fixture/expected values as test_imputation_routing.py's
        # TestRealStatisticalGroupMedian -- proves importing draw_methods.py
        # and adding config.IMPUTE_DRAW_METHOD_BY_TARGET does not perturb the
        # default (fusion, spatial, statistical) router path at all.
        df = pd.DataFrame({
            "use_class": ["office", "office", "residential", "residential", "office"],
            "levels": [2.0, 4.0, 10.0, 12.0, float("nan")],
        })
        out_a = impute_missing(df)
        out_b = impute_missing(df)
        pd.testing.assert_frame_equal(out_a, out_b)
        assert out_a.loc[4, "levels"] == pytest.approx(3.0)
        assert out_a.loc[4, "provenance_levels"] == "GROUPMODE_MED"

    def test_draw_method_by_target_config_default_empty(self):
        assert config.IMPUTE_DRAW_METHOD_BY_TARGET == {}

    def test_registry_is_a_typed_dict(self):
        assert isinstance(dm.DRAW_METHODS, dict)

    def test_token_constants_exact_strings(self):
        assert dm.DRAW_KDE_HIGH == "DRAW_KDE_HIGH"
        assert dm.DRAW_KDE_MED == "DRAW_KDE_MED"
        assert dm.DRAW_PMM_HIGH == "DRAW_PMM_HIGH"
        assert dm.DRAW_PMM_MED == "DRAW_PMM_MED"
        assert dm.DRAW_HOTDECK_HIGH == "DRAW_HOTDECK_HIGH"
        assert dm.DRAW_HOTDECK_MED == "DRAW_HOTDECK_MED"
        assert dm.DRAW_RESID_HIGH == "DRAW_RESID_HIGH"
        assert dm.DRAW_RESID_MED == "DRAW_RESID_MED"
        assert dm.DRAW_ABB_HIGH == "DRAW_ABB_HIGH"
        assert dm.DRAW_ABB_MED == "DRAW_ABB_MED"
        assert dm.DRAW_CATFREQ_HIGH == "DRAW_CATFREQ_HIGH"
        assert dm.DRAW_CATFREQ_MED == "DRAW_CATFREQ_MED"


# ── T02 -- M1 `kde` draw ─────────────────────────────────────────────────────

def _bimodal_stratum(seed: int, n_per_mode: int = 40):
    rng_data = np.random.default_rng(seed)
    lo = rng_data.normal(1950, 5, size=n_per_mode)
    hi = rng_data.normal(2000, 5, size=n_per_mode)
    return np.concatenate([lo, hi])


class TestKDE:
    def test_registered_under_kde(self):
        assert "kde" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["kde"] is dm.draw_kde

    def test_variance_within_20pct_and_beats_median_ks(self):
        observed = _bimodal_stratum(seed=123)
        n_missing = 40
        targets = ["s1"] * n_missing
        observed_by_stratum = {"s1": observed}

        draws = dm.draw_kde(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0

        std_ratio = np.std(draws) / np.std(observed)
        assert 0.8 <= std_ratio <= 1.2, f"std_ratio={std_ratio}"

        ks_draw = sps.ks_2samp(draws, observed).statistic
        median_fill = np.full(n_missing, np.median(observed))
        ks_median = sps.ks_2samp(median_fill, observed).statistic
        assert ks_draw < ks_median * 0.5, f"ks_draw={ks_draw} ks_median={ks_median}"

    def test_small_stratum_abstains(self):
        observed_by_stratum = {"s1": [2020.0, 2021.0, 2022.0]}  # n=3 < floor 5
        draws = dm.draw_kde(observed_by_stratum, ["s1", "s1"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_unknown_stratum_abstains(self):
        draws = dm.draw_kde({}, ["missing_stratum"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_clamped_to_observed_bounds_by_default(self):
        observed = list(range(1950, 2000))  # n=50
        draws = dm.draw_kde({"s1": observed}, ["s1"] * 30, np.random.default_rng(config.RANDOM_SEED))
        assert (draws >= 1950).all() and (draws <= 1999).all()

    def test_explicit_bounds_override_per_stratum_range(self):
        observed = list(range(1950, 2000))
        draws = dm.draw_kde(
            {"s1": observed}, ["s1"] * 30, np.random.default_rng(config.RANDOM_SEED),
            bounds=(1900.0, 2020.0),
        )
        assert (draws >= 1900).all() and (draws <= 2020).all()

    def test_determinism_same_seed_twice_run_byte_identical(self):
        observed = _bimodal_stratum(seed=7)
        observed_by_stratum = {"s1": observed}
        targets = ["s1"] * 25
        d1 = dm.draw_kde(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        d2 = dm.draw_kde(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        np.testing.assert_array_equal(d1, d2)

    def test_multi_stratum_independent_draws(self):
        rng_data = np.random.default_rng(3)
        s1 = rng_data.normal(1960, 3, size=30)
        s2 = rng_data.normal(2010, 3, size=30)
        observed_by_stratum = {"s1": s1, "s2": s2}
        targets = ["s1"] * 10 + ["s2"] * 10
        draws = dm.draw_kde(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        assert draws[:10].mean() < draws[10:].mean()  # s1 cluster << s2 cluster

    def test_mixed_abstain_and_fill_strata(self):
        observed_by_stratum = {
            "big": _bimodal_stratum(seed=11),
            "tiny": [2000.0, 2001.0],  # n=2 < floor -- abstains
        }
        targets = ["big", "tiny", "big", "tiny"]
        draws = dm.draw_kde(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        assert not np.isnan(draws[0]) and not np.isnan(draws[2])
        assert np.isnan(draws[1]) and np.isnan(draws[3])


# ── T03 -- M2 `pmm` (predictive-mean-matching) ──────────────────────────────

class TestPMM:
    def test_registered_under_pmm(self):
        assert "pmm" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["pmm"] is dm.draw_pmm

    def test_real_donor_invariant_variance_and_beats_median_ks(self):
        rng_data = np.random.default_rng(21)
        young = rng_data.normal(1955, 5, size=40)
        old = rng_data.normal(2005, 5, size=40)
        observed_by_stratum = {"young": young, "old": old}
        targets = ["young"] * 40

        draws = dm.draw_pmm(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0

        all_observed = np.concatenate([young, old])
        assert np.isin(draws, all_observed).all(), "real-donor invariant violated"

        assert np.std(draws) > 1.0  # variance preserved, not collapsed to a point

        ks_draw = sps.ks_2samp(draws, young).statistic
        median_fill = np.full(40, np.median(young))
        ks_median = sps.ks_2samp(median_fill, young).statistic
        assert ks_draw < ks_median * 0.5, f"ks_draw={ks_draw} ks_median={ks_median}"

    def test_thin_stratum_borrows_cross_stratum_donors(self):
        rng_data = np.random.default_rng(22)
        young = rng_data.normal(1955, 5, size=40)
        observed_by_stratum = {"young": young, "thin": [1956.0]}  # n=1, no floor on pmm
        targets = ["thin"] * 5

        draws = dm.draw_pmm(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0
        all_observed = np.concatenate([young, [1956.0]])
        assert np.isin(draws, all_observed).all()

    def test_unknown_stratum_falls_back_to_global_median(self):
        rng_data = np.random.default_rng(23)
        young = rng_data.normal(1955, 5, size=20)
        old = rng_data.normal(2005, 5, size=20)
        observed_by_stratum = {"young": young, "old": old}

        draws = dm.draw_pmm(observed_by_stratum, ["never_seen_stratum"] * 3, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0
        assert np.isin(draws, np.concatenate([young, old])).all()

    def test_abstain_when_no_observed_anywhere(self):
        draws = dm.draw_pmm({}, ["s1", "s1"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_determinism_same_seed_twice_run_byte_identical(self):
        rng_data = np.random.default_rng(24)
        young = rng_data.normal(1955, 5, size=30)
        old = rng_data.normal(2005, 5, size=30)
        observed_by_stratum = {"young": young, "old": old}
        targets = ["young"] * 15 + ["old"] * 15

        d1 = dm.draw_pmm(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        d2 = dm.draw_pmm(observed_by_stratum, targets, np.random.default_rng(config.RANDOM_SEED))
        np.testing.assert_array_equal(d1, d2)


# ── T04 -- M3 `hotdeck` (spatial donor draw) ────────────────────────────────

_HD_RADIUS = 15.0  # scaled to the 10 m synthetic grid spacing below, not DEFAULT_RADIUS_M=100
_HD_K = 8


def _clustered_gdf(attr: str, seed: int, spacing: float = 10.0):
    """Two spatially separated 5x5 clusters (A near origin, B far away) so a
    missing row's k-nearest-within-radius donor pool is unambiguous."""
    rng_data = np.random.default_rng(seed)
    vals_a = rng_data.normal(50.0, 8.0, size=25)
    vals_b = rng_data.normal(200.0, 8.0, size=25)

    rows, geoms = [], []
    k = 0
    for gy in range(5):
        for gx in range(5):
            rows.append({attr: vals_a[k]})
            geoms.append(Point(gx * spacing, gy * spacing))
            k += 1
    k = 0
    for gy in range(5):
        for gx in range(5):
            rows.append({attr: vals_b[k]})
            geoms.append(Point(1000 + gx * spacing, 1000 + gy * spacing))
            k += 1
    gdf = gpd.GeoDataFrame(rows, geometry=geoms)
    return gdf, vals_a, vals_b


class TestHotdeck:
    def test_registered_under_hotdeck(self):
        assert "hotdeck" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["hotdeck"] is dm.draw_hotdeck

    def test_real_donor_invariant_variance_and_beats_median_ks(self):
        gdf, vals_a, vals_b = _clustered_gdf("levels", seed=31)
        # cluster A occupies rows 0-24 (5x5 grid, index = gy*5+gx). Checkerboard
        # split so every missing cell has an orthogonal (dist=10 < radius=15)
        # OBSERVED neighbour -- a sequential top/bottom split would leave the
        # far half's missing cells with no donor within radius at all.
        even_idx = [gy * 5 + gx for gy in range(5) for gx in range(5) if (gx + gy) % 2 == 0]
        odd_idx = [gy * 5 + gx for gy in range(5) for gx in range(5) if (gx + gy) % 2 == 1]
        missing_rows = even_idx
        observed_donors = vals_a[odd_idx]

        gdf.loc[missing_rows, "levels"] = np.nan
        mask = pd.Series(False, index=gdf.index)
        mask.iloc[missing_rows] = True

        draws = dm.draw_hotdeck(gdf, "levels", mask, np.random.default_rng(config.RANDOM_SEED),
                                 k=_HD_K, radius=_HD_RADIUS)
        filled = draws.iloc[missing_rows]
        assert filled.notna().all()
        assert np.isin(filled.to_numpy(dtype=float), observed_donors).all(), "real-donor invariant violated"
        assert filled.std() > 0.5

        ks_draw = sps.ks_2samp(filled.to_numpy(dtype=float), vals_a).statistic
        median_fill = np.full(len(filled), np.median(observed_donors))
        ks_median = sps.ks_2samp(median_fill, vals_a).statistic
        assert ks_draw < ks_median * 0.8, f"ks_draw={ks_draw} ks_median={ks_median}"

    def test_abstains_when_isolated(self):
        gdf, _va, _vb = _clustered_gdf("levels", seed=32)
        lone = gpd.GeoDataFrame({"levels": [np.nan]}, geometry=[Point(5000.0, 5000.0)])
        gdf = pd.concat([gdf, lone], ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry")

        mask = pd.Series(False, index=gdf.index)
        mask.iloc[-1] = True

        draws = dm.draw_hotdeck(gdf, "levels", mask, np.random.default_rng(config.RANDOM_SEED),
                                 k=_HD_K, radius=_HD_RADIUS)
        assert pd.isna(draws.iloc[-1])

    def test_abstains_when_no_observed_neighbour(self):
        gdf, _va, _vb = _clustered_gdf("levels", seed=33)
        # blank out ALL of cluster A's attr (rows 0-24) except leave one row
        # missing (the target) -- every one of its neighbours is also NaN.
        gdf.loc[list(range(25)), "levels"] = np.nan
        mask = pd.Series(False, index=gdf.index)
        mask.iloc[0] = True

        draws = dm.draw_hotdeck(gdf, "levels", mask, np.random.default_rng(config.RANDOM_SEED),
                                 k=_HD_K, radius=_HD_RADIUS)
        assert pd.isna(draws.iloc[0])

    def test_determinism_same_seed_twice_run_byte_identical(self):
        gdf, _va, _vb = _clustered_gdf("levels", seed=34)
        missing_rows = list(range(10))
        gdf.loc[missing_rows, "levels"] = np.nan
        mask = pd.Series(False, index=gdf.index)
        mask.iloc[missing_rows] = True

        d1 = dm.draw_hotdeck(gdf, "levels", mask, np.random.default_rng(config.RANDOM_SEED),
                              k=_HD_K, radius=_HD_RADIUS)
        d2 = dm.draw_hotdeck(gdf, "levels", mask, np.random.default_rng(config.RANDOM_SEED),
                              k=_HD_K, radius=_HD_RADIUS)
        pd.testing.assert_series_equal(d1, d2)


# ── T05 -- M4 `resid` (stochastic residual) ─────────────────────────────────

class TestResid:
    def test_registered_under_resid(self):
        assert "resid" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["resid"] is dm.draw_resid

    def test_central_accuracy_variance_and_beats_median_ks(self):
        rng_data = np.random.default_rng(41)
        observed = rng_data.normal(2000.0, 15.0, size=60)
        targets = ["s1"] * 60

        draws = dm.draw_resid({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0

        median_o = np.median(observed)
        assert draws.mean() == pytest.approx(median_o, abs=3.0)  # central accuracy kept

        std_ratio = np.std(draws) / np.std(observed)
        assert 0.7 <= std_ratio <= 1.3, f"std_ratio={std_ratio}"

        ks_draw = sps.ks_2samp(draws, observed).statistic
        median_fill = np.full(60, median_o)
        ks_median = sps.ks_2samp(median_fill, observed).statistic
        assert ks_draw < ks_median * 0.5, f"ks_draw={ks_draw} ks_median={ks_median}"

    def test_small_stratum_abstains(self):
        observed_by_stratum = {"s1": [2020.0, 2021.0, 2022.0]}  # n=3 < floor 5
        draws = dm.draw_resid(observed_by_stratum, ["s1", "s1"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_clamped_to_explicit_bounds(self):
        observed = np.array([10.0, 20.0, 30.0, 40.0, 1000.0])  # n=5, median=30
        draws = dm.draw_resid(
            {"s1": observed}, ["s1"] * 50, np.random.default_rng(config.RANDOM_SEED),
            bounds=(0.0, 25.0),
        )
        assert (draws >= 0.0).all() and (draws <= 25.0).all()

    def test_default_clamp_stays_within_observed_range(self):
        observed = np.array([10.0, 20.0, 30.0, 40.0, 1000.0])
        draws = dm.draw_resid({"s1": observed}, ["s1"] * 50, np.random.default_rng(config.RANDOM_SEED))
        assert (draws >= 10.0).all() and (draws <= 1000.0).all()

    def test_determinism_same_seed_twice_run_byte_identical(self):
        rng_data = np.random.default_rng(42)
        observed = rng_data.normal(2000.0, 10.0, size=30)
        targets = ["s1"] * 20
        d1 = dm.draw_resid({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        d2 = dm.draw_resid({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        np.testing.assert_array_equal(d1, d2)


# ── T06 -- M5 `catfreq` (categorical empirical-frequency draw) ─────────────

def _catfreq_gdf(n_a: int = 100, n_b: int = 100):
    """Two `archetype_id` strata with skewed `use_class` proportions."""
    rows = (
        [{"archetype_id": "A", "use_class": "office"}] * int(0.8 * n_a)
        + [{"archetype_id": "A", "use_class": "retail"}] * (n_a - int(0.8 * n_a))
        + [{"archetype_id": "B", "use_class": "residential"}] * int(0.6 * n_b)
        + [{"archetype_id": "B", "use_class": "industrial"}] * (n_b - int(0.6 * n_b))
    )
    return pd.DataFrame(rows)


class TestCatFreq:
    def test_registered_under_catfreq(self):
        assert "catfreq" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["catfreq"] is dm.draw_catfreq

    def test_reproduces_stratum_proportions_and_recovers_minority(self):
        gdf = _catfreq_gdf(n_a=100, n_b=100)
        # append 200 missing rows in stratum A
        missing = pd.DataFrame({"archetype_id": ["A"] * 200, "use_class": [None] * 200})
        gdf = pd.concat([gdf, missing], ignore_index=True)
        mask = gdf["use_class"].isna()

        draws = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        filled = draws.loc[mask]
        assert filled.notna().all()

        counts = filled.value_counts()
        assert "retail" in counts.index, "mode-fill would never recover the minority category"
        observed_freq = counts / counts.sum()
        # chi-square goodness-of-fit vs the true stratum-A proportions (80/20)
        expected = pd.Series({"office": 0.8, "retail": 0.2})
        obs_counts = np.array([counts.get("office", 0), counts.get("retail", 0)])
        exp_counts = expected.reindex(["office", "retail"]).to_numpy() * obs_counts.sum()
        chi2, pval = sps.chisquare(obs_counts, exp_counts)
        assert pval > 0.01, f"chi2={chi2} pval={pval} counts={counts.to_dict()}"

    def test_mode_fill_would_never_recover_minority(self):
        gdf = _catfreq_gdf(n_a=100, n_b=100)
        # sanity check on the fixture itself: mode of stratum A is "office" only
        stratum_a = gdf.loc[gdf["archetype_id"] == "A", "use_class"]
        assert stratum_a.mode().iat[0] == "office"
        assert (stratum_a == "retail").any()  # minority exists in the data...
        # ...but a MODE fill (what `_statistical_tier` does) would never emit it

    def test_self_stratification_guard_falls_back_to_global(self):
        # only `use_class` present -- no `archetype_id` -- so imputing
        # `use_class` itself must NOT stratify by itself (guard), and must
        # fall back to the global observed frequency table instead of
        # crashing / silently abstaining.
        rows = [{"use_class": "office"}] * 80 + [{"use_class": "retail"}] * 20
        gdf = pd.DataFrame(rows)
        missing = pd.DataFrame({"use_class": [None] * 100})
        gdf = pd.concat([gdf, missing], ignore_index=True)
        mask = gdf["use_class"].isna()

        draws = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        filled = draws.loc[mask]
        assert filled.notna().all()
        assert "retail" in filled.value_counts().index

    def test_small_stratum_falls_back_to_global(self):
        rows = (
            [{"archetype_id": "A", "use_class": "office"}] * 2  # n=2 < floor 5
            + [{"archetype_id": "B", "use_class": "residential"}] * 60
            + [{"archetype_id": "B", "use_class": "industrial"}] * 40
        )
        gdf = pd.DataFrame(rows)
        missing = pd.DataFrame({"archetype_id": ["A"] * 10, "use_class": [None] * 10})
        gdf = pd.concat([gdf, missing], ignore_index=True)
        mask = gdf["use_class"].isna()

        draws = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        filled = draws.loc[mask]
        assert filled.notna().all()  # falls through to the global pool, not abstain
        assert set(filled.unique()).issubset({"residential", "industrial"})

    def test_abstain_when_neither_stratum_nor_global_clears_floor(self):
        rows = [{"archetype_id": "A", "use_class": "office"}] * 3  # n=3 < floor 5, and it's the WHOLE pool
        gdf = pd.DataFrame(rows)
        missing = pd.DataFrame({"archetype_id": ["A"] * 5, "use_class": [None] * 5})
        gdf = pd.concat([gdf, missing], ignore_index=True)
        mask = gdf["use_class"].isna()

        draws = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        assert draws.loc[mask].isna().all()

    def test_determinism_same_seed_twice_run_byte_identical(self):
        gdf = _catfreq_gdf(n_a=60, n_b=60)
        missing = pd.DataFrame({"archetype_id": ["A"] * 40, "use_class": [None] * 40})
        gdf = pd.concat([gdf, missing], ignore_index=True)
        mask = gdf["use_class"].isna()

        d1 = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        d2 = dm.draw_catfreq(gdf, "use_class", mask, np.random.default_rng(config.RANDOM_SEED))
        pd.testing.assert_series_equal(d1, d2)


# ── T06b -- M6 `abb` (approximate-Bayesian-bootstrap donor draw) ───────────

class TestABB:
    def test_registered_under_abb(self):
        assert "abb" in dm.DRAW_METHODS
        assert dm.DRAW_METHODS["abb"] is dm.draw_abb

    def test_real_donor_invariant_resists_depletion_and_beats_median_ks(self):
        observed = np.array([10.0, 20.0, 30.0, 40.0, 50.0])  # n=5, exactly at the floor
        targets = ["s1"] * 40

        draws = dm.draw_abb({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).sum() == 0
        assert np.isin(draws, observed).all(), "real-donor invariant violated"

        fixed_donor_baseline = np.full(40, observed[0])
        assert len(set(draws.tolist())) > len(set(fixed_donor_baseline.tolist())), (
            "ABB should resist donor depletion vs a fixed-donor draw"
        )
        assert np.std(draws) > 0

        ks_draw = sps.ks_2samp(draws, observed).statistic
        median_fill = np.full(40, np.median(observed))
        ks_median = sps.ks_2samp(median_fill, observed).statistic
        assert ks_draw < ks_median, f"ks_draw={ks_draw} ks_median={ks_median}"

    def test_small_stratum_abstains(self):
        observed_by_stratum = {"s1": [2020.0, 2021.0, 2022.0]}  # n=3 < floor 5
        draws = dm.draw_abb(observed_by_stratum, ["s1", "s1"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_unknown_stratum_abstains(self):
        draws = dm.draw_abb({}, ["missing_stratum"], np.random.default_rng(config.RANDOM_SEED))
        assert np.isnan(draws).all()

    def test_determinism_same_seed_twice_run_byte_identical(self):
        rng_data = np.random.default_rng(51)
        observed = rng_data.normal(2000.0, 10.0, size=20)
        targets = ["s1"] * 30
        d1 = dm.draw_abb({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        d2 = dm.draw_abb({"s1": observed}, targets, np.random.default_rng(config.RANDOM_SEED))
        np.testing.assert_array_equal(d1, d2)


# ── T07 -- `_draw_tier` wired into the router (opt-in only) ────────────────

def _year_built_gdf(n_per_stratum: int = 30, missing_frac: float = 0.3, seed: int = 61):
    rng_data = np.random.default_rng(seed)
    rows = []
    for stratum, mean in (("office", 1960.0), ("residential", 2005.0)):
        for y in rng_data.normal(mean, 8.0, size=n_per_stratum):
            rows.append({"use_class": stratum, "year_built": float(y)})
    df = pd.DataFrame(rows)
    n_missing = int(len(df) * missing_frac)
    missing_idx = rng_data.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_idx, "year_built"] = np.nan
    return df


class TestDrawTierRouting:
    def test_default_enabled_tiers_unaffected_by_wiring(self):
        assert config.IMPUTE_ENABLED_TIERS == ("fusion", "spatial", "statistical")
        assert "draw" not in config.IMPUTE_ENABLED_TIERS

    def test_draw_tier_fills_with_kde_provenance_when_opted_in(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"year_built": "kde"})
        df = _year_built_gdf()
        cfg = imp.ImputeConfig(per_input_tiers={"year_built": ("draw", "statistical")})
        out = impute_missing(df, cfg=cfg, targets=["year_built"])
        assert out["year_built"].isna().sum() == 0
        tokens = out.loc[df["year_built"].isna(), "provenance_year_built"]
        assert tokens.isin([dm.DRAW_KDE_HIGH, dm.DRAW_KDE_MED]).all()

    def test_unconfigured_target_abstains_and_falls_through_to_statistical(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {})
        df = _year_built_gdf()
        cfg = imp.ImputeConfig(per_input_tiers={"year_built": ("draw", "statistical")})
        out = impute_missing(df, cfg=cfg, targets=["year_built"])
        assert out["year_built"].isna().sum() == 0
        tokens = out.loc[df["year_built"].isna(), "provenance_year_built"]
        assert (tokens == "GROUPMODE_MED").all()

    def test_unknown_method_name_abstains_gracefully_never_raises(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"year_built": "not_a_real_method"})
        df = _year_built_gdf()
        cfg = imp.ImputeConfig(per_input_tiers={"year_built": ("draw", "statistical")})
        out = impute_missing(df, cfg=cfg, targets=["year_built"])
        assert out["year_built"].isna().sum() == 0
        tokens = out.loc[df["year_built"].isna(), "provenance_year_built"]
        assert (tokens == "GROUPMODE_MED").all()

    def test_default_cfg_still_byte_identical_even_with_draw_configured(self, monkeypatch):
        # Same fixture/expected values as TestDefaultByteIdentity -- proves that
        # simply CONFIGURING config.IMPUTE_DRAW_METHOD_BY_TARGET (without a
        # per_input_tiers opt-in) still has zero effect: "draw" is reachable
        # now (T07), but only via explicit opt-in, never the default tuple.
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"levels": "kde", "year_built": "pmm"})
        df = pd.DataFrame({
            "use_class": ["office", "office", "residential", "residential", "office"],
            "levels": [2.0, 4.0, 10.0, 12.0, float("nan")],
        })
        out_a = impute_missing(df)
        out_b = impute_missing(df)
        pd.testing.assert_frame_equal(out_a, out_b)
        assert out_a.loc[4, "levels"] == pytest.approx(3.0)
        assert out_a.loc[4, "provenance_levels"] == "GROUPMODE_MED"

    def test_catfreq_routes_through_gdf_shaped_path_with_tokens(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"use_class": "catfreq"})
        rows = (
            [{"archetype_id": "A", "use_class": "office"}] * 80
            + [{"archetype_id": "A", "use_class": "retail"}] * 20
        )
        df = pd.DataFrame(rows)
        missing = pd.DataFrame({"archetype_id": ["A"] * 30, "use_class": [None] * 30})
        df = pd.concat([df, missing], ignore_index=True)
        cfg = imp.ImputeConfig(per_input_tiers={"use_class": ("draw", "statistical")})
        out = impute_missing(df, cfg=cfg, targets=["use_class"])
        assert out["use_class"].isna().sum() == 0
        tokens = out.loc[df["use_class"].isna(), "provenance_use_class"]
        assert tokens.isin([dm.DRAW_CATFREQ_HIGH, dm.DRAW_CATFREQ_MED]).all()
        assert "retail" in out.loc[df["use_class"].isna(), "use_class"].unique()

    def test_hotdeck_routes_through_gdf_shaped_path_with_geometry(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"levels": "hotdeck"})
        gdf, _vals_a, _vals_b = _clustered_gdf("levels", seed=71)
        missing_rows = list(range(0, 25, 2))
        gdf.loc[missing_rows, "levels"] = np.nan
        cfg = imp.ImputeConfig(per_input_tiers={"levels": ("draw", "statistical")})
        out = impute_missing(gdf, cfg=cfg, targets=["levels"])
        assert out["levels"].isna().sum() == 0
        tokens = out.loc[gdf["levels"].isna(), "provenance_levels"]
        assert tokens.isin([dm.DRAW_HOTDECK_HIGH, dm.DRAW_HOTDECK_MED]).all()


# ── T08 -- zero-fitted-params structural guard + whole-tier determinism ────

class TestNoEUILeakage:
    """Mirrors `test_ml_imputer.py::TestNoEUILeakage` / `test_debias.py::
    TestNoEUILeakage`'s `__code__.co_names` structural pin (Part II §II.1
    rule 3): no draw function or `_draw_tier` may ever reference an EUI/
    `total_eui`/`*_eui_kwh_m2`-like name."""

    _FUNCS = (
        dm.draw_kde,
        dm.draw_pmm,
        dm.draw_hotdeck,
        dm.draw_resid,
        dm.draw_catfreq,
        dm.draw_abb,
        dm._empirical_freqs,
        imp._draw_tier,
        imp._draw_stratum_col_for,
    )

    def test_no_function_code_references_eui_by_name(self):
        for func in self._FUNCS:
            referenced = set(func.__code__.co_names)
            leaked = [n for n in referenced if "eui" in n.lower()]
            assert not leaked, (
                f"{func.__qualname__} co_names references EUI-like name(s) {leaked} -- "
                "zero-fitted-params violation (Part II §II.1 rule 3)."
            )


class TestDrawTierDeterminism:
    def test_same_seed_twice_run_byte_identical_across_whole_tier(self, monkeypatch):
        monkeypatch.setattr(
            config, "IMPUTE_DRAW_METHOD_BY_TARGET", {"year_built": "kde", "levels": "resid"},
        )
        rng_data = np.random.default_rng(81)
        rows = []
        for stratum, mean in (("office", 1960.0), ("residential", 2005.0)):
            for y in rng_data.normal(mean, 8.0, size=25):
                rows.append({
                    "use_class": stratum,
                    "year_built": float(y),
                    "levels": float(rng_data.integers(1, 15)),
                })
        df = pd.DataFrame(rows)
        df.loc[df.sample(frac=0.3, random_state=1).index, "year_built"] = np.nan
        df.loc[df.sample(frac=0.3, random_state=2).index, "levels"] = np.nan

        cfg = imp.ImputeConfig(per_input_tiers={
            "year_built": ("draw", "statistical"),
            "levels": ("draw", "statistical"),
        })
        out_a = impute_missing(
            df, cfg=cfg, targets=["year_built", "levels"],
            rng=np.random.default_rng(config.RANDOM_SEED),
        )
        out_b = impute_missing(
            df, cfg=cfg, targets=["year_built", "levels"],
            rng=np.random.default_rng(config.RANDOM_SEED),
        )
        pd.testing.assert_frame_equal(out_a, out_b)
        assert out_a["year_built"].isna().sum() == 0
        assert out_a["levels"].isna().sum() == 0
