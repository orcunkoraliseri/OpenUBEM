"""External-data fusion precedence layer (`openubem/semantic/fusion.py` +
`openubem/acquisition/overture_fetcher.py`).

Input-Imputation arc, Phase D (T12.1-T12.4). NO live network anywhere in this
file (plan §2 rule 6) -- every source is exercised via a mock adapter or the
small committed fixtures under `openubem/data/fixtures/fusion/` (rule 4
chicken-and-egg note: the real Overture query is deferred to the T12.6
LIVE_SMOKE, not this suite).

Load-bearing properties under test:
  (1) T12.1 registry round-trips; `precedence_for` filters to available
      sources, in the configured order; a first-hit source short-circuits a
      second (miss rows still reach it); a source reading an EUI column trips
      the structural guard.
  (2) T12.2 `fetch_overture`/`OvertureSource` against the committed slice:
      centroid-within-polygon hit, nearest-within-tolerance hit, out-of-range
      miss, CRS-mismatch handling, use_class raw-category crosswalk.
  (3) T12.3 `LidarSource` zonal height (direct HIGH) + derived levels (MED);
      unset path -> unavailable, silently skipped. `AssessorSource` PIN join
      and spatial-overlap join; field-map remap.
  (4) T12.4 `_fusion_tier` contract: fills via `FUSED_<SOURCE>_HIGH/MED`,
      misses fall through to spatial/statistical; default `impute_missing()`
      never calls `_fusion_tier` (byte-identical no-fusion path).
"""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from openubem import config
from openubem.semantic import fusion
from openubem.semantic import imputation as imp
from openubem.semantic.imputation import ImputeConfig, impute_missing
from openubem.acquisition.overture_fetcher import fetch_overture

FIXTURES = Path(__file__).parent.parent / "openubem" / "data" / "fixtures" / "fusion"
OVERTURE_SLICE = FIXTURES / "overture_testcell_slice.parquet"
LIDAR_NDSM = FIXTURES / "lidar_testcell_ndsm.tif"
ASSESSOR_GPKG = FIXTURES / "assessor_testcell.gpkg"
_CRS = "EPSG:32618"


def _cfg(**kwargs):
    base = dict(
        FUSION_SOURCES_BY_TARGET=dict(config.FUSION_SOURCES_BY_TARGET),
        FUSION_OVERTURE_SLICE_PATH=None,
        FUSION_OVERTURE_ENDPOINT=None,
        FUSION_LIDAR_NDSM_PATH=None,
        FUSION_ASSESSOR_PATH=None,
        FUSION_ASSESSOR_FIELDS={},
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _target_gdf(rows, crs=_CRS):
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


# ── T12.1 -- registry / precedence / structural guard ────────────────────────

class _MockSource(fusion.FusionSource):
    name = "mock_hit"
    source_token = "MOCKHIT"

    def available(self, cfg):
        return True

    def join(self, gdf, attr, cfg):
        value = pd.Series(np.nan, index=gdf.index, dtype=float)
        value.iloc[0] = 99.0
        derived = pd.Series(False, index=gdf.index)
        return value, derived


class _MockMissSource(fusion.FusionSource):
    name = "mock_miss"
    source_token = "MOCKMISS"

    def available(self, cfg):
        return True

    def join(self, gdf, attr, cfg):
        return fusion._empty_value(gdf, attr), pd.Series(False, index=gdf.index)


class _MockUnavailableSource(fusion.FusionSource):
    name = "mock_unavailable"
    source_token = "MOCKUNAVAIL"

    def available(self, cfg):
        return False

    def join(self, gdf, attr, cfg):
        raise AssertionError("join() must never be called on an unavailable source")


class _MockEuiReaderSource(fusion.FusionSource):
    name = "mock_eui_reader"
    source_token = "MOCKEUI"

    def available(self, cfg):
        return True

    def join(self, gdf, attr, cfg):
        _ = gdf["total_eui"]  # would-be zero-fitted-params violation
        return fusion._empty_value(gdf, attr), pd.Series(False, index=gdf.index)


@pytest.fixture(autouse=True)
def _register_mocks():
    for cls in (_MockSource, _MockMissSource, _MockUnavailableSource, _MockEuiReaderSource):
        fusion._REGISTRY[cls.name] = cls
    yield
    for cls in (_MockSource, _MockMissSource, _MockUnavailableSource, _MockEuiReaderSource):
        fusion._REGISTRY.pop(cls.name, None)


class TestRegistry:
    def test_get_source_round_trips(self):
        src = fusion.get_source("mock_hit")
        assert isinstance(src, _MockSource)

    def test_unknown_source_raises(self):
        with pytest.raises(KeyError):
            fusion.get_source("does_not_exist")

    def test_precedence_for_filters_to_available_in_configured_order(self):
        cfg = _cfg(FUSION_SOURCES_BY_TARGET={"levels": ("mock_unavailable", "mock_hit", "mock_miss")})
        sources = fusion.precedence_for("levels", cfg)
        assert [s.name for s in sources] == ["mock_hit", "mock_miss"]

    def test_first_hit_wins_second_not_called_for_that_row_miss_reaches_it(self):
        gdf = _target_gdf([
            {"levels": np.nan, "geometry": Point(0, 0)},
            {"levels": np.nan, "geometry": Point(1, 1)},
        ])
        cfg = _cfg(FUSION_SOURCES_BY_TARGET={"levels": ("mock_hit", "mock_miss")})
        value, token = fusion.fuse(gdf, "levels", cfg)
        assert value.iloc[0] == pytest.approx(99.0)
        assert token.iloc[0] == "FUSED_MOCKHIT_HIGH"
        # row 1 was a miss for mock_hit; mock_miss ran for it and also missed
        assert pd.isna(value.iloc[1])
        assert token.iloc[1] is None

    def test_eui_reading_source_trips_structural_guard(self):
        gdf = _target_gdf([{"levels": np.nan, "total_eui": 120.0, "geometry": Point(0, 0)}])
        cfg = _cfg(FUSION_SOURCES_BY_TARGET={"levels": ("mock_eui_reader",)})
        with pytest.raises(ValueError, match="zero-fitted-params"):
            fusion.fuse(gdf, "levels", cfg)


# ── T12.2 -- Overture adapter ─────────────────────────────────────────────────

class TestOvertureFetch:
    def test_fetch_overture_offline_slice_no_network(self):
        layer = fetch_overture(slice_path=str(OVERTURE_SLICE))
        assert len(layer) == 2
        assert set(layer.columns) >= {"id", "height", "levels", "use_class", "year_built", "geometry"}
        assert layer.loc[layer["id"] == "overture-A", "height"].iat[0] == pytest.approx(30.0)
        assert layer.loc[layer["id"] == "overture-A", "levels"].iat[0] == pytest.approx(8.0)

    def test_endpoint_and_slice_path_both_none_raises(self):
        with pytest.raises(ValueError):
            fetch_overture()


class TestOvertureSource:
    def _cfg_overture(self):
        return _cfg(
            FUSION_SOURCES_BY_TARGET={
                "height": ("overture",), "levels": ("overture",),
                "year_built": ("overture",), "use_class": ("overture",),
            },
            FUSION_OVERTURE_SLICE_PATH=str(OVERTURE_SLICE),
        )

    def test_centroid_within_polygon_direct_hit(self):
        gdf = _target_gdf([{
            "height": np.nan, "geometry": box(500002, 4500002, 500018, 4500018),
        }])
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "height", cfg)
        assert value.iloc[0] == pytest.approx(30.0)
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_nearest_within_tolerance_hit(self):
        # centroid at (500125, 4500006) -- 5 m outside overture-B's east edge
        gdf = _target_gdf([{
            "levels": np.nan, "geometry": box(500121, 4500002, 500129, 4500010),
        }])
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "levels", cfg)
        assert value.iloc[0] == pytest.approx(3.0)
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_out_of_tolerance_is_a_miss(self):
        gdf = _target_gdf([{
            "levels": np.nan, "geometry": box(500900, 4500900, 500910, 4500910),
        }])
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "levels", cfg)
        assert pd.isna(value.iloc[0])
        assert token.iloc[0] is None

    def test_year_built_direct_hit(self):
        gdf = _target_gdf([{
            "year_built": np.nan, "geometry": box(500002, 4500002, 500018, 4500018),
        }])
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "year_built", cfg)
        assert value.iloc[0] == pytest.approx(1995.0)
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_use_class_raw_category_is_crosswalked(self):
        gdf = _target_gdf([{
            "use_class": None, "geometry": box(500002, 4500002, 500018, 4500018),
        }])
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "use_class", cfg)
        # overture "office" -> osm_to_use_class.json "commercial"
        assert value.iloc[0] == "commercial"
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_crs_mismatch_is_handled(self):
        # target gdf in geographic CRS; overture slice is EPSG:32618 -- the
        # source layer must be reprojected to match before joining.
        gdf = _target_gdf(
            [{"height": np.nan, "geometry": box(500002, 4500002, 500018, 4500018)}],
            crs=_CRS,
        ).to_crs("EPSG:4326")
        cfg = self._cfg_overture()
        value, token = fusion.fuse(gdf, "height", cfg)
        assert value.iloc[0] == pytest.approx(30.0)
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_no_geometry_column_is_a_noop(self):
        df = pd.DataFrame({"height": [np.nan]})
        cfg = self._cfg_overture()
        value, token = fusion.fuse(df, "height", cfg)
        assert pd.isna(value.iloc[0])


# ── OPEN-13 -- `_load_overture_layer` cached-read guard (no prior coverage) ──

class TestOvertureCachedReadGuard:
    def _normalized_gdf(self):
        return gpd.GeoDataFrame(
            {
                "id": ["overture-C"],
                "height": [12.0],
                "levels": [3.0],
                "use_class": ["residential"],
                "year_built": [1990],
            },
            geometry=[box(0, 0, 10, 10)],
            crs=_CRS,
        )

    def test_normalized_schema_cache_hit_skips_fetch_overture(self, monkeypatch, tmp_path):
        import openubem.acquisition.overture_fetcher as overture_fetcher_mod

        def _boom(*args, **kwargs):
            raise AssertionError("fetch_overture must not be called on a normalized-schema cache hit")

        monkeypatch.setattr(overture_fetcher_mod, "fetch_overture", _boom)

        slice_path = tmp_path / "normalized_cache.parquet"
        self._normalized_gdf().to_parquet(slice_path)

        cfg = _cfg(FUSION_OVERTURE_SLICE_PATH=str(slice_path))
        layer = fusion._load_overture_layer(cfg)
        assert set(layer.columns) == fusion._NORMALIZED_OVERTURE_COLUMNS
        assert layer["id"].iat[0] == "overture-C"

    def test_raw_schema_slice_goes_through_fetch_overture(self, monkeypatch):
        import openubem.acquisition.overture_fetcher as overture_fetcher_mod

        sentinel = object()
        calls = []

        def _spy(*args, **kwargs):
            calls.append((args, kwargs))
            return sentinel

        monkeypatch.setattr(overture_fetcher_mod, "fetch_overture", _spy)

        # OVERTURE_SLICE carries the raw (pre-normalization) schema -- the
        # guard's column-set comparison must not match it.
        cfg = _cfg(FUSION_OVERTURE_SLICE_PATH=str(OVERTURE_SLICE))
        layer = fusion._load_overture_layer(cfg)
        assert layer is sentinel
        assert len(calls) == 1

    def test_guard_set_equals_fetchers_normalized_columns(self):
        from openubem.acquisition.overture_fetcher import _NORMALIZED_COLUMNS
        # OPEN-13 regression. The first assert is the load-bearing one: it pins
        # the fetcher's schema to the six names `_load_overture_layer`'s cached-read
        # guard was written against. A schema change in overture_fetcher fails HERE,
        # forcing a human to re-examine the guard. The second assert is a
        # tautology by construction (fusion derives its set from this tuple) and is
        # kept only to document that derivation.
        assert set(_NORMALIZED_COLUMNS) == {
            "id", "height", "levels", "use_class", "year_built", "geometry",
        }
        assert fusion._NORMALIZED_OVERTURE_COLUMNS == set(_NORMALIZED_COLUMNS)


# ── T12.3 -- LiDAR nDSM zonal adapter ────────────────────────────────────────

class TestLidarSource:
    def _cfg_lidar(self, path=None):
        return _cfg(
            FUSION_SOURCES_BY_TARGET={"height": ("lidar",), "levels": ("lidar",)},
            FUSION_LIDAR_NDSM_PATH=str(path) if path else None,
        )

    def test_zonal_mean_height_direct_high(self):
        gdf = _target_gdf([{"height": np.nan, "geometry": box(500030, 4500030, 500040, 4500040)}])
        cfg = self._cfg_lidar(LIDAR_NDSM)
        value, token = fusion.fuse(gdf, "height", cfg)
        assert value.iloc[0] == pytest.approx(24.5)
        assert token.iloc[0] == "FUSED_LIDAR_HIGH"

    def test_derived_levels_from_height_is_med(self):
        gdf = _target_gdf([{"levels": np.nan, "geometry": box(500030, 4500030, 500040, 4500040)}])
        cfg = self._cfg_lidar(LIDAR_NDSM)
        value, token = fusion.fuse(gdf, "levels", cfg)
        assert value.iloc[0] == pytest.approx(7.0)  # floor(24.5 / 3.5) = 7
        assert token.iloc[0] == "FUSED_LIDAR_MED"

    def test_unset_path_source_unavailable_silently_skipped(self):
        gdf = _target_gdf([{"height": np.nan, "geometry": box(500030, 4500030, 500040, 4500040)}])
        cfg = self._cfg_lidar(None)
        assert fusion.precedence_for("height", cfg) == []
        value, token = fusion.fuse(gdf, "height", cfg)
        assert pd.isna(value.iloc[0])

    def test_no_raster_coverage_is_a_miss(self):
        gdf = _target_gdf([{"height": np.nan, "geometry": box(600000, 4600000, 600010, 4600010)}])
        cfg = self._cfg_lidar(LIDAR_NDSM)
        value, token = fusion.fuse(gdf, "height", cfg)
        assert pd.isna(value.iloc[0])


# ── T12.3 -- assessor join adapter ───────────────────────────────────────────

class TestAssessorSource:
    def _cfg_assessor(self, field_map):
        return _cfg(
            FUSION_SOURCES_BY_TARGET={"year_built": ("assessor",), "use_class": ("assessor",)},
            FUSION_ASSESSOR_PATH=str(ASSESSOR_GPKG),
            FUSION_ASSESSOR_FIELDS=field_map,
        )

    def test_pin_join_by_bbl(self):
        gdf = _target_gdf([{
            "year_built": np.nan, "bbl": "P001", "geometry": Point(0, 0),
        }])
        cfg = self._cfg_assessor({"year_built": "YearBuilt", "pin": "BBL", "pin_gdf_col": "bbl"})
        value, token = fusion.fuse(gdf, "year_built", cfg)
        assert value.iloc[0] == pytest.approx(1960.0)
        assert token.iloc[0] == "FUSED_ASSESSOR_HIGH"

    def test_spatial_overlap_join_when_no_pin(self):
        gdf = _target_gdf([{
            "use_class": None, "geometry": box(500302, 4500302, 500308, 4500308),
        }])
        cfg = self._cfg_assessor({"use_class": "BldgClass"})
        value, token = fusion.fuse(gdf, "use_class", cfg)
        assert value.iloc[0] == "residential"
        assert token.iloc[0] == "FUSED_ASSESSOR_HIGH"

    def test_field_map_remaps_municipality_specific_columns(self):
        gdf = _target_gdf([{"year_built": np.nan, "bbl": "P002", "geometry": Point(0, 0)}])
        cfg = self._cfg_assessor({"year_built": "YearBuilt", "pin": "BBL", "pin_gdf_col": "bbl"})
        value, token = fusion.fuse(gdf, "year_built", cfg)
        assert value.iloc[0] == pytest.approx(2005.0)

    def test_unmapped_attribute_is_a_noop(self):
        gdf = _target_gdf([{"levels": np.nan, "bbl": "P001", "geometry": Point(0, 0)}])
        cfg = self._cfg_assessor({"year_built": "YearBuilt", "pin": "BBL", "pin_gdf_col": "bbl"})
        value, token = fusion.fuse(gdf, "levels", cfg)
        assert pd.isna(value.iloc[0])


# ── T12.4 -- `_fusion_tier` contract + opt-in byte-identity ──────────────────

class TestFusionTier:
    def test_fusion_fills_overlapping_rows_and_stamps_high_token(self, monkeypatch):
        monkeypatch.setattr(config, "FUSION_SOURCES_BY_TARGET", {
            "year_built": ("overture",),
        })
        monkeypatch.setattr(config, "FUSION_OVERTURE_SLICE_PATH", str(OVERTURE_SLICE))
        gdf = _target_gdf([
            {"year_built": np.nan, "geometry": box(500002, 4500002, 500018, 4500018)},
            {"year_built": np.nan, "geometry": box(500900, 4500900, 500910, 4500910)},
        ])
        out = impute_missing(
            gdf, targets=["year_built"],
            cfg=ImputeConfig(per_input_tiers={"year_built": ("fusion",)}),
        )
        assert out.loc[0, "year_built"] == pytest.approx(1995.0)
        assert out.loc[0, "provenance_year_built"] == "FUSED_OVERTURE_HIGH"
        assert "FUSED_OVERTURE_HIGH" in out.loc[0, "data_quality_flag"]
        assert pd.isna(out.loc[1, "year_built"])  # miss -- no other tier enabled

    def test_fusion_miss_falls_through_to_spatial_then_statistical(self, monkeypatch):
        monkeypatch.setattr(config, "FUSION_SOURCES_BY_TARGET", {"levels": ("overture",)})
        monkeypatch.setattr(config, "FUSION_OVERTURE_SLICE_PATH", str(OVERTURE_SLICE))
        gdf = _target_gdf([
            {"levels": 4.0, "use_class": "office", "geometry": box(500900, 4500900, 500910, 4500910)},
            {"levels": 6.0, "use_class": "office", "geometry": box(500910, 4500910, 500920, 4500920)},
            {"levels": np.nan, "use_class": "office", "geometry": box(500920, 4500920, 500930, 4500930)},
        ])
        out = impute_missing(
            gdf, targets=["levels"],
            cfg=ImputeConfig(per_input_tiers={"levels": ("fusion", "statistical")}),
        )
        assert out.loc[2, "levels"] == pytest.approx(5.0)  # group-median fallback
        assert out.loc[2, "provenance_levels"] == "GROUPMODE_MED"

    def test_lidar_derived_levels_row_stamps_med_token(self, monkeypatch):
        monkeypatch.setattr(config, "FUSION_SOURCES_BY_TARGET", {"levels": ("lidar",)})
        monkeypatch.setattr(config, "FUSION_LIDAR_NDSM_PATH", str(LIDAR_NDSM))
        gdf = _target_gdf([{"levels": np.nan, "geometry": box(500030, 4500030, 500040, 4500040)}])
        out = impute_missing(
            gdf, targets=["levels"],
            cfg=ImputeConfig(per_input_tiers={"levels": ("fusion",)}),
        )
        assert out.loc[0, "levels"] == pytest.approx(7.0)
        assert out.loc[0, "provenance_levels"] == "FUSED_LIDAR_MED"

    def test_default_impute_missing_calls_fusion_tier_as_byte_identical_noop(self, monkeypatch):
        # T12-ship (2026-07-13): `fusion` is now IN config.IMPUTE_ENABLED_TIERS'
        # default tuple, replacing the retired pre-ship contract (fusion never
        # called by default). `_fusion_tier` IS invoked for each targeted
        # attribute on the default path, but -- with no fusion source
        # configured (the default state) -- it is a byte-identical no-op
        # fall-through to spatial/statistical.
        spy_calls = []
        real_fusion_tier = imp._fusion_tier

        def _spy(gdf, attr, mask, rng):
            spy_calls.append(attr)
            return real_fusion_tier(gdf, attr, mask, rng)

        monkeypatch.setattr(imp, "_fusion_tier", _spy)
        rows = [
            {"year_built": 1990.0, "levels": np.nan, "geometry": Point(0, 0)},
            {"year_built": np.nan, "levels": 5.0, "geometry": Point(5, 0)},
            {"year_built": 2000.0, "levels": 5.0, "geometry": Point(0, 5)},
        ]
        gdf = _target_gdf([dict(r) for r in rows])
        before = gdf.copy()
        out = impute_missing(gdf)  # cfg=None -> default IMPUTE_ENABLED_TIERS

        assert set(spy_calls) == {"year_built", "levels"}
        pd.testing.assert_frame_equal(gdf, before)  # input untouched
        assert "fusion" in set(config.IMPUTE_ENABLED_TIERS)

        # Prove the fusion no-op is byte-identical: rerun on a fresh identical
        # gdf with fusion excluded and compare full outputs (values + provenance).
        gdf_no_fusion = _target_gdf([dict(r) for r in rows])
        out_no_fusion = impute_missing(
            gdf_no_fusion,
            cfg=ImputeConfig(enabled_tiers=("spatial", "statistical")),
        )
        pd.testing.assert_frame_equal(
            out.drop(columns="geometry"),
            out_no_fusion.drop(columns="geometry"),
        )

    def test_fusion_never_emits_low_token(self, monkeypatch):
        # A source returning a hit is always graded HIGH or MED by `fuse` --
        # there is no code path to LOW (plan §2 rule 4).
        monkeypatch.setattr(config, "FUSION_SOURCES_BY_TARGET", {"height": ("overture",)})
        monkeypatch.setattr(config, "FUSION_OVERTURE_SLICE_PATH", str(OVERTURE_SLICE))
        gdf = _target_gdf([{"height": np.nan, "geometry": box(500002, 4500002, 500018, 4500018)}])
        value, token = fusion.fuse(gdf, "height")
        assert token.iloc[0] in ("FUSED_OVERTURE_HIGH", "FUSED_OVERTURE_MED")
        assert "LOW" not in str(token.iloc[0])


# ── no-EUI-column module-level structural guard (mirrors TestNoImputerFeedback) ──

class TestNoEuiColumnEverRead:
    def test_fuse_rejects_a_gdf_carrying_an_eui_column(self):
        gdf = _target_gdf([{"levels": np.nan, "total_eui": 150.0, "geometry": Point(0, 0)}])
        with pytest.raises(ValueError, match="zero-fitted-params"):
            fusion.fuse(gdf, "levels", _cfg())

    def test_overture_source_join_rejects_eui_column(self):
        gdf = _target_gdf([{
            "height": np.nan, "site_eui_kwh_m2": 100.0,
            "geometry": box(500002, 4500002, 500018, 4500018),
        }])
        cfg = _cfg(FUSION_OVERTURE_SLICE_PATH=str(OVERTURE_SLICE))
        with pytest.raises(ValueError, match="zero-fitted-params"):
            fusion.OvertureSource().join(gdf, "height", cfg)


# ── CP-1 gate suite / other imputation suites -- reused directly by the
# runner listed in the task; nothing else lives here.
