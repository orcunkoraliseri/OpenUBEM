"""T07 — imputation routing subsystem + strict mode (`openubem/semantic/imputation.py`).

Input-Imputation arc, Phase B PINNED CONTRACT (`impute_missing` / `ImputeConfig` /
`StrictImputationError`). `impute_missing` is ADDITIVE / STANDALONE in Phase B --
these tests exercise it directly, never through `enrich_semantics` (scope boundary).

Load-bearing properties under test:
  (1) canonical fallback order fusion -> spatial -> statistical -> ml, first
      non-null value per row wins (a spatial hit skips the statistical call
      entirely for that attribute; a spatial miss falls through to statistical
      with the correct registered token);
  (2) a disabled tier is never invoked (no stub-fill);
  (3) `cfg`/`config.py` resolution happens at CALL time, not import/construction
      time, so monkeypatching `config.IMPUTE_ENABLED_TIERS` / `IMPUTE_STRICT_MODE`
      is honoured by a default (`cfg=None`) call;
  (4) strict mode fills nothing and raises `StrictImputationError` listing every
      residual (attribute, row_index) gap; no gaps -> returns unchanged;
  (5) force-enabling `fusion`/`ml` (both Phase C/D skeleton stubs) raises
      `NotImplementedError` -- surfaced, never caught-and-swallowed;
  (6) real (non-mocked) end-to-end fills: a genuine T06 spatial-donor hit via
      geometry, and a genuine T04/T05-style group-median statistical fallback --
      proving the router is wired to real primitives, not mocks only.
"""
from unittest.mock import Mock

import numpy as np
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from openubem import config
from openubem.semantic import imputation as imp
from openubem.semantic.imputation import ImputeConfig, StrictImputationError, impute_missing


def _pt_gdf(rows):
    geoms = [Point(r.pop("x"), r.pop("y")) for r in rows]
    return gpd.GeoDataFrame(rows, geometry=geoms)


def _cat_grid_gdf(overrides, default="office", spacing=60.0, n=5):
    """5x5 grid scaled so the production `DEFAULT_RADIUS_M=100`/`DEFAULT_K=10`
    neighbourhood matches the immediate 8-neighbour ring (mirrors
    `test_spatial_impute.py`'s smaller-scale grid, ratio-preserved)."""
    rows = [
        {"x": gx * spacing, "y": gy * spacing, "use_class": overrides.get((gx, gy), default)}
        for gy in range(n) for gx in range(n)
    ]
    return _pt_gdf(rows)


def _idx_at(gdf, x, y):
    match = gdf.index[(gdf.geometry.x == x) & (gdf.geometry.y == y)]
    assert len(match) == 1
    return match[0]


# ── (3) config.py resolution happens at call time, not construction time ────

class TestConfigResolutionAtCallTime:
    def test_default_cfg_honours_monkeypatched_enabled_tiers(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_ENABLED_TIERS", ())
        df = pd.DataFrame({"levels": [3.0, float("nan")]})
        out = impute_missing(df)  # cfg=None -> default ImputeConfig(), tiers read lazily
        assert pd.isna(out.loc[1, "levels"])  # no tiers enabled -> nothing filled

    def test_default_cfg_honours_monkeypatched_strict_mode(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_STRICT_MODE", True)
        df = pd.DataFrame({"levels": [3.0, float("nan")]})
        with pytest.raises(StrictImputationError) as exc:
            impute_missing(df)
        assert ("levels", 1) in exc.value.missing

    def test_explicit_cfg_overrides_monkeypatched_config(self, monkeypatch):
        monkeypatch.setattr(config, "IMPUTE_STRICT_MODE", True)
        df = pd.DataFrame({"levels": [3.0, 3.0]})  # no gaps at all
        out = impute_missing(df, cfg=ImputeConfig(strict=False))
        assert list(out["levels"]) == [3.0, 3.0]


# ── (1) fallback order: spatial hit skips statistical; spatial miss falls through ──

class TestFallbackOrder:
    def test_spatial_hit_skips_statistical_tier(self, monkeypatch):
        stub_value = pd.Series([np.nan, 7.0], index=[0, 1], dtype=float)
        stub_token = pd.Series([None, "HOTDECK_NEIGHBOR_HIGH"], index=[0, 1], dtype=object)
        monkeypatch.setattr(imp, "_spatial_tier", lambda gdf, attr, mask, rng: (stub_value, stub_token))
        stat_mock = Mock()
        monkeypatch.setattr(imp, "_statistical_tier", stat_mock)

        df = pd.DataFrame({"levels": [2.0, float("nan")]})
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")))

        assert out.loc[1, "levels"] == 7.0
        assert out.loc[1, "provenance_levels"] == "HOTDECK_NEIGHBOR_HIGH"
        stat_mock.assert_not_called()

    def test_spatial_miss_falls_to_statistical_with_correct_token(self, monkeypatch):
        miss_value = pd.Series(np.nan, index=[0, 1, 2], dtype=float)
        miss_token = pd.Series([None, None, None], index=[0, 1, 2], dtype=object)
        monkeypatch.setattr(imp, "_spatial_tier", lambda gdf, attr, mask, rng: (miss_value, miss_token))

        df = pd.DataFrame({
            "use_class": ["office", "office", "office"],
            "levels": [4.0, 6.0, float("nan")],
        })
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")))

        assert out.loc[2, "levels"] == pytest.approx(5.0)  # median(4, 6)
        assert out.loc[2, "provenance_levels"] == "GROUPMODE_MED"
        assert "GROUPMODE_MED" in out.loc[2, "data_quality_flag"]


# ── (2) disabled tier is never invoked ───────────────────────────────────────

class TestDisabledTierNeverInvoked:
    def test_spatial_disabled_statistical_only(self, monkeypatch):
        spatial_mock = Mock()
        monkeypatch.setattr(imp, "_spatial_tier", spatial_mock)

        df = pd.DataFrame({
            "use_class": ["office", "office", "office"],
            "levels": [4.0, 6.0, float("nan")],
        })
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("statistical",)))

        spatial_mock.assert_not_called()
        assert out.loc[2, "levels"] == pytest.approx(5.0)
        assert out.loc[2, "provenance_levels"] == "GROUPMODE_MED"

    def test_per_input_tiers_overrides_global_enabled_tiers(self, monkeypatch):
        spatial_mock = Mock()
        monkeypatch.setattr(imp, "_spatial_tier", spatial_mock)

        df = pd.DataFrame({
            "use_class": ["office", "office", "office"],
            "levels": [4.0, 6.0, float("nan")],
        })
        cfg = ImputeConfig(
            enabled_tiers=("spatial", "statistical"),
            per_input_tiers={"levels": ("statistical",)},
        )
        out = impute_missing(df, cfg=cfg)

        spatial_mock.assert_not_called()
        assert out.loc[2, "levels"] == pytest.approx(5.0)


# ── (4) strict / audit mode ───────────────────────────────────────────────────

class TestStrictMode:
    def test_raises_listing_every_residual_gap_and_fills_nothing(self):
        df = pd.DataFrame({
            "year_built": [1995.0, float("nan")],
            "levels": [float("nan"), 3.0],
        })
        with pytest.raises(StrictImputationError) as exc:
            impute_missing(df, cfg=ImputeConfig(strict=True))
        assert set(exc.value.missing) == {("year_built", 1), ("levels", 0)}
        # Fills nothing -- original frame untouched (strict raises before any fill).
        assert pd.isna(df.loc[1, "year_built"])
        assert pd.isna(df.loc[0, "levels"])

    def test_no_gaps_returns_unchanged(self):
        df = pd.DataFrame({"year_built": [1995.0, 2001.0], "levels": [3.0, 4.0]})
        out = impute_missing(df, cfg=ImputeConfig(strict=True))
        pd.testing.assert_frame_equal(out, df)
        assert out is not df  # a copy, not the same object


# ── (5) force-enabled Phase C/D skeleton stubs raise, never swallowed ────────

class TestForceEnabledSkeletonStubs:
    def test_fusion_force_enabled_raises_not_implemented(self):
        df = pd.DataFrame({"levels": [float("nan")]})
        cfg = ImputeConfig(enabled_tiers=("fusion", "spatial", "statistical"))
        with pytest.raises(NotImplementedError, match="fusion tier is Phase D"):
            impute_missing(df, cfg=cfg)

    def test_ml_force_enabled_below_floor_falls_through(self):
        # Phase C is now built (T11.3): a 1-row all-NaN `levels` frame is
        # sub-floor for `missforest` (floor=1000) -- `_ml_tier` catches
        # `BelowFloorError` internally and returns an all-null (value, token)
        # tier result (fall-through), not an exception. With enabled_tiers=
        # ("ml",) only, no other tier can fill the gap either, so the row
        # stays NaN and impute_missing must NOT raise.
        df = pd.DataFrame({"levels": [float("nan")]})
        cfg = ImputeConfig(enabled_tiers=("ml",))
        out = impute_missing(df, cfg=cfg)
        assert pd.isna(out.loc[0, "levels"])

    def test_default_tiers_never_touch_fusion_or_ml(self):
        # Zero observed values anywhere -> statistical tier cannot help either;
        # default (spatial+statistical only) must NOT raise -- it just leaves
        # the gap unfilled, since fusion/ml are excluded from the default tuple.
        df = pd.DataFrame({"levels": [float("nan"), float("nan")]})
        out = impute_missing(df)
        assert pd.isna(out["levels"]).all()


# ── (6) real (non-mocked) end-to-end fills ───────────────────────────────────

class TestRealSpatialFill:
    def test_genuine_knn_donor_hit_high_confidence(self):
        rows = [
            {"x": 1000, "y": 1000, "levels": float("nan")},
            {"x": 990, "y": 1000, "levels": 8.0},
            {"x": 1010, "y": 1000, "levels": 8.0},
            {"x": 1000, "y": 990, "levels": 8.0},
            {"x": 1000, "y": 1010, "levels": 8.0},
            {"x": 1005, "y": 1005, "levels": 8.0},
        ]
        gdf = _pt_gdf(rows)
        out = impute_missing(gdf, cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")))

        assert out.loc[0, "levels"] == pytest.approx(8.0)
        assert out.loc[0, "provenance_levels"] in ("HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED")
        assert out.loc[0, "provenance_levels"] in out.loc[0, "data_quality_flag"]

    def test_no_geometry_spatial_tier_is_a_noop_falls_to_statistical(self):
        df = pd.DataFrame({
            "use_class": ["office", "office", "office"],
            "levels": [4.0, 6.0, float("nan")],
        })
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")))
        assert out.loc[2, "levels"] == pytest.approx(5.0)
        assert out.loc[2, "provenance_levels"] == "GROUPMODE_MED"


class TestRealStatisticalGroupMedian:
    def test_stratified_group_median_no_leakage(self):
        df = pd.DataFrame({
            "use_class": ["office", "office", "residential", "residential", "office"],
            "levels": [2.0, 4.0, 10.0, 12.0, float("nan")],
        })
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert out.loc[4, "levels"] == pytest.approx(3.0)  # median(office) = median(2, 4)
        assert out.loc[4, "provenance_levels"] == "GROUPMODE_MED"

    def test_empty_stratum_falls_back_to_global_median(self):
        df = pd.DataFrame({
            "use_class": ["office", "office", "residential"],
            "levels": [2.0, 4.0, float("nan")],  # residential stratum has no observed levels
        })
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert out.loc[2, "levels"] == pytest.approx(3.0)  # falls back to global observed median
        assert out.loc[2, "provenance_levels"] == "GROUPMODE_MED"

    def test_zero_observed_values_leaves_row_unfilled(self):
        df = pd.DataFrame({"levels": [float("nan"), float("nan")]})
        out = impute_missing(df, cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert pd.isna(out["levels"]).all()


# ── T07.2 categorical routing (`use_class` via neighbour_vote + group-mode) ──

class TestRealCategoricalSpatialFill:
    def test_genuine_neighbour_vote_donor_hit_stamps_hotdeck_token(self):
        gdf = _cat_grid_gdf({(2, 2): None})
        out = impute_missing(
            gdf, targets=["use_class"],
            cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")),
        )
        i = _idx_at(gdf, 120.0, 120.0)
        assert out.loc[i, "use_class"] == "office"
        assert out.loc[i, "provenance_use_class"] in ("HOTDECK_NEIGHBOR_HIGH", "HOTDECK_NEIGHBOR_MED")
        assert out.loc[i, "provenance_use_class"] in out.loc[i, "data_quality_flag"]


class TestCategoricalMNARFallsThrough:
    def test_mnar_blocked_neighbourhood_falls_through_spatial_tier(self):
        # Center's own neighbourhood is >=60% missing -> T06 deactivates the
        # spatial value for it (MNAR guard); `_spatial_tier` trusts that
        # determination and does not fill the row -- it stays NaN/untouched,
        # exactly like the continuous precedent (neither re-runs the MNAR
        # filter nor surfaces T06's `gdf_out` flag onto the outer frame).
        overrides = {(2, 2): None}
        missing_neighbours = [(1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3)]
        for cell in missing_neighbours:
            overrides[cell] = None
        gdf = _cat_grid_gdf(overrides)
        out = impute_missing(
            gdf, targets=["use_class"], cfg=ImputeConfig(enabled_tiers=("spatial",)),
        )
        i = _idx_at(gdf, 120.0, 120.0)
        assert pd.isna(out.loc[i, "use_class"])
        assert out.loc[i, "provenance_use_class"] == ""


class TestRealCategoricalStatisticalGroupMode:
    def test_group_mode_fallback_stamps_groupmode_med_token(self):
        df = pd.DataFrame({
            "archetype_id": ["A", "A", "A", "A"],
            "use_class": ["office", "office", "residential", None],
        })
        out = impute_missing(df, targets=["use_class"], cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert out.loc[3, "use_class"] == "office"  # mode(office, office, residential)
        assert out.loc[3, "provenance_use_class"] == "GROUPMODE_MED"
        assert "GROUPMODE_MED" in out.loc[3, "data_quality_flag"]

    def test_zero_observed_values_leaves_row_unfilled(self):
        df = pd.DataFrame({"use_class": [None, None]})
        out = impute_missing(df, targets=["use_class"], cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert pd.isna(out["use_class"]).all()

    def test_self_stratification_guard_uses_archetype_id_not_use_class(self):
        # If `use_class` were (wrongly) chosen as its own strat column, every
        # missing row's own stratum key is itself NaN at fill time, so ALL
        # missing rows would collapse onto the single tie-broken GLOBAL mode.
        # With the guard routing to `archetype_id` instead, each archetype
        # group recovers its OWN (unambiguous, non-tied) mode.
        df = pd.DataFrame({
            "archetype_id": ["A", "A", "B", "B", "A", "B"],
            "use_class": ["office", "office", "residential", "residential", None, None],
        })
        out = impute_missing(df, targets=["use_class"], cfg=ImputeConfig(enabled_tiers=("statistical",)))
        assert out.loc[4, "use_class"] == "office"        # group A's own mode
        assert out.loc[5, "use_class"] == "residential"   # group B's own mode
        assert out.loc[4, "provenance_use_class"] == "GROUPMODE_MED"
        assert out.loc[5, "provenance_use_class"] == "GROUPMODE_MED"


# ── determinism (Rule 8) ──────────────────────────────────────────────────────

class TestDeterminism:
    def test_repeated_calls_are_byte_identical(self):
        rows = [
            {"x": 0, "y": 0, "use_class": "office", "levels": float("nan")},
            {"x": 5, "y": 0, "use_class": "office", "levels": 6.0},
            {"x": 0, "y": 5, "use_class": "office", "levels": 6.0},
        ]
        gdf = _pt_gdf(rows)
        out_a = impute_missing(gdf, rng=np.random.default_rng(config.RANDOM_SEED))
        out_b = impute_missing(gdf, rng=np.random.default_rng(config.RANDOM_SEED))
        pd.testing.assert_frame_equal(out_a, out_b)
