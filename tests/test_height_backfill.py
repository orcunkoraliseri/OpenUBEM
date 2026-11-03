"""E-UTCI-09 height-backfill sub-plan T10 -- regression + provenance suite.

Covers: T04 bbox math + cache-miss guard; `fuse()` filling `height_m` from the
committed offline Overture slice (F-E, NEVER the network); T07's provenance-
token and minimum-height-floor invariants; a guard that `pull_overture` stays
unreachable from any pipeline entry point; and T09's NO_NEIGHBOUR_FLAG fix
(E-UTCI-10). No live network anywhere in this file (plan hard rule 4).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from openubem import config
from openubem.acquisition import height_cache
from openubem.semantic import fusion
from openubem.semantic.imputation import ImputeConfig, impute_missing
from openubem.semantic.spatial_impute import (
    knn_fill, neighbour_vote, MNAR_BLOCKED_FLAG, NO_NEIGHBOUR_FLAG,
)

REPO = Path(__file__).resolve().parent.parent
OVERTURE_SLICE = REPO / "openubem" / "data" / "fixtures" / "fusion" / "overture_testcell_slice.parquet"
_CRS = "EPSG:32618"


def _target_gdf(rows, crs=_CRS):
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


# ── T04 -- bbox math + cache-miss guard ──────────────────────────────────────

class TestCellBbox:
    @pytest.mark.parametrize("cell, spec", list(height_cache.AFFECTED_CELLS.items()))
    def test_bbox_contains_centre_and_has_expected_span(self, cell, spec):
        lat, lon, radius_m = spec["lat"], spec["lon"], spec["radius_m"]
        minx, miny, maxx, maxy = height_cache.cell_bbox(lat, lon, radius_m)
        assert minx < lon < maxx
        assert miny < lat < maxy

        ns_span_m = (maxy - miny) * height_cache._M_PER_DEG_LAT
        assert ns_span_m == pytest.approx(2 * radius_m, rel=0.02)

    def test_pull_overture_rejects_a_cell_outside_the_4_affected(self):
        with pytest.raises(ValueError, match="not one of the 4 affected cells"):
            height_cache.pull_overture("nyc_urban")

    def test_load_cached_raises_clear_error_on_missing_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(height_cache, "HEIGHT_CACHE_DIR", tmp_path)
        with pytest.raises(FileNotFoundError, match="no cached Overture pull"):
            height_cache.load_cached("nyc_suburban")


# ── T05 hard rule 4 -- pull_overture stays unreachable from any pipeline ────

class TestPullOvertureNeverAutoReachable:
    def test_pull_overture_not_referenced_outside_its_own_module_and_tests(self):
        skip_dirs = {"scratchpad", ".git", "__pycache__"}
        hits = []
        for py_file in REPO.rglob("*.py"):
            if any(part in skip_dirs for part in py_file.parts):
                continue
            if py_file == REPO / "openubem" / "acquisition" / "height_cache.py":
                continue
            if py_file == Path(__file__):
                continue
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            if "pull_overture" in text:
                hits.append(str(py_file.relative_to(REPO)))
        assert hits == [], f"pull_overture referenced outside its own module/tests: {hits}"


# ── T07 -- `fuse()` filling `height_m` from the committed offline slice ─────

class TestFuseHeightFromOfflineSlice:
    def _cfg(self):
        from types import SimpleNamespace
        return SimpleNamespace(
            FUSION_SOURCES_BY_TARGET={"height_m": ("overture",)},
            FUSION_OVERTURE_SLICE_PATH=str(OVERTURE_SLICE),
            FUSION_OVERTURE_ENDPOINT=None,
            FUSION_LIDAR_NDSM_PATH=None,
            FUSION_ASSESSOR_PATH=None,
            FUSION_ASSESSOR_FIELDS={},
        )

    def test_fuse_fills_height_m_direct_hit_high_confidence(self):
        gdf = _target_gdf([{
            "height_m": np.nan, "geometry": box(500002, 4500002, 500018, 4500018),
        }])
        value, token = fusion.fuse(gdf, "height_m", self._cfg())
        assert value.iloc[0] == pytest.approx(30.0)
        assert token.iloc[0] == "FUSED_OVERTURE_HIGH"

    def test_fuse_miss_is_null_not_a_default(self):
        gdf = _target_gdf([{
            "height_m": np.nan, "geometry": box(500900, 4500900, 500910, 4500910),
        }])
        value, token = fusion.fuse(gdf, "height_m", self._cfg())
        assert pd.isna(value.iloc[0])
        assert token.iloc[0] is None


# ── T07 -- `_fusion_tier` provenance + minimum-height-floor invariants ──────

class TestFusionTierProvenanceAndFloor:
    def test_every_newly_filled_height_m_row_carries_a_token(self, monkeypatch):
        monkeypatch.setattr(config, "FUSION_SOURCES_BY_TARGET", {"height_m": ("overture",)})
        monkeypatch.setattr(config, "FUSION_OVERTURE_SLICE_PATH", str(OVERTURE_SLICE))
        gdf = _target_gdf([
            {"height_m": np.nan, "geometry": box(500002, 4500002, 500018, 4500018)},  # hit
            {"height_m": np.nan, "geometry": box(500900, 4500900, 500910, 4500910)},  # miss
        ])
        before_notna = gdf["height_m"].notna().sum()
        out = impute_missing(
            gdf, targets=["height_m"],
            cfg=ImputeConfig(per_input_tiers={"height_m": ("fusion",)}),
        )
        after_notna = out["height_m"].notna().sum()
        assert after_notna == before_notna + 1  # only the hit row landed

        newly_filled = gdf["height_m"].isna() & out["height_m"].notna()
        assert newly_filled.sum() == 1
        assert out.loc[newly_filled, "provenance_height_m"].notna().all()
        assert (out.loc[newly_filled, "provenance_height_m"] != "").all()
        assert out.loc[newly_filled, "provenance_height_m"].iat[0] == "FUSED_OVERTURE_HIGH"

        # the miss row stays NaN -- never a silent 0.0 / fabricated default
        still_missing = out.loc[gdf["height_m"].isna() & out["height_m"].isna()]
        assert len(still_missing) == 1

    def test_below_floor_fused_height_is_discarded_not_filled(self, monkeypatch):
        # A mock source below the T07(c) minimum-height sanity floor
        # (_MIN_HEIGHT_FLOOR_M = 2.1 m, IRC/IBC R305.1 minimum ceiling
        # height) must be left NaN, not landed, even though `fuse()` itself
        # returns a real HIGH-confidence hit.
        class _BelowFloorSource(fusion.FusionSource):
            name = "_test_below_floor_source"
            source_token = "TESTBELOWFLOOR"

            def available(self, cfg):
                return True

            def join(self, gdf, attr, cfg):
                value = pd.Series(np.nan, index=gdf.index, dtype=float)
                value.iloc[0] = 0.216  # the real absurd value found in nyc_suburban
                return value, pd.Series(False, index=gdf.index)

        fusion._REGISTRY[_BelowFloorSource.name] = _BelowFloorSource
        try:
            monkeypatch.setattr(
                config, "FUSION_SOURCES_BY_TARGET", {"height_m": ("_test_below_floor_source",)}
            )
            gdf = _target_gdf([{"height_m": np.nan, "geometry": Point(0, 0)}])

            # fuse() itself has no floor concept -- it reports the raw hit
            raw_value, raw_token = fusion.fuse(gdf, "height_m")
            assert raw_value.iloc[0] == pytest.approx(0.216)
            assert raw_token.iloc[0] == "FUSED_TESTBELOWFLOOR_HIGH"

            # _fusion_tier applies the floor and discards it
            out = impute_missing(
                gdf, targets=["height_m"],
                cfg=ImputeConfig(per_input_tiers={"height_m": ("fusion",)}),
            )
            assert pd.isna(out.loc[0, "height_m"])
            assert out.loc[0, "provenance_height_m"] in ("", None) or pd.isna(out.loc[0, "provenance_height_m"])
        finally:
            fusion._REGISTRY.pop(_BelowFloorSource.name, None)

    def test_default_config_fusion_is_still_a_noop_for_height_m(self):
        # Production default: FUSION_SOURCES_BY_TARGET == {} -- confirms the
        # CP-B byte-identical no-op property holds for height_m specifically,
        # not just the synthetic year_built/levels cases in test_fusion.py.
        assert config.FUSION_SOURCES_BY_TARGET == {}
        assert fusion.precedence_for("height_m") == []
        gdf = _target_gdf([{"height_m": np.nan, "geometry": box(500002, 4500002, 500018, 4500018)}])
        value, token = fusion.fuse(gdf, "height_m")
        assert pd.isna(value.iloc[0])
        assert token.iloc[0] is None


# ── T09 -- E-UTCI-10 fix: zero-neighbour rows recorded, not silently skipped ─

class TestZeroNeighbourFlaggedDistinctly:
    def test_knn_fill_zero_neighbour_row_gets_distinct_flag_not_mnar(self):
        # A single isolated point far from every other row -- zero neighbours
        # within the default search radius.
        gdf = gpd.GeoDataFrame(
            {"height_m": [np.nan, 30.0, 30.0, 30.0]},
            geometry=[Point(0, 0), Point(10, 10), Point(10, 20), Point(20, 10)],
        )
        value, dispersion, confidence, gdf_out = knn_fill(gdf, "height_m", k=5, radius=1.0)
        assert pd.isna(value.iloc[0])
        flag = str(gdf_out.loc[0, "data_quality_flag"])
        assert NO_NEIGHBOUR_FLAG in flag
        assert MNAR_BLOCKED_FLAG not in flag

    def test_neighbour_vote_zero_neighbour_row_gets_distinct_flag_not_mnar(self):
        gdf = gpd.GeoDataFrame(
            {"use_class": [None, "Office", "Office", "Office"]},
            geometry=[Point(0, 0), Point(10, 10), Point(10, 20), Point(20, 10)],
        )
        value, agreement, confidence, gdf_out = neighbour_vote(gdf, "use_class", k=5, radius=1.0)
        assert value.iloc[0] is None
        flag = str(gdf_out.loc[0, "data_quality_flag"])
        assert NO_NEIGHBOUR_FLAG in flag
        assert MNAR_BLOCKED_FLAG not in flag

    def test_no_neighbour_and_mnar_blocked_partition_missing_exactly(self):
        # 8-neighbour interior grid where the centre is missing and every
        # neighbour is ALSO missing (zero donors -> MNAR-blocked, not
        # zero-neighbour -- neighbours exist, they're just all missing too).
        rows = []
        geoms = []
        for gy in range(3):
            for gx in range(3):
                rows.append({"height_m": np.nan})
                geoms.append(Point(gx * 10.0, gy * 10.0))
        gdf = gpd.GeoDataFrame(rows, geometry=geoms)
        value, dispersion, confidence, gdf_out = knn_fill(gdf, "height_m", k=8, radius=15.0)
        missing = gdf["height_m"].isna()
        filled = missing & value.notna()
        flags = gdf_out["data_quality_flag"].astype(str)
        blocked = missing & flags.str.contains(MNAR_BLOCKED_FLAG, regex=False)
        no_neighbour = missing & flags.str.contains(NO_NEIGHBOUR_FLAG, regex=False)
        silent = missing & ~filled & ~blocked & ~no_neighbour
        assert int(silent.sum()) == 0
        assert (filled | blocked | no_neighbour).sum() == missing.sum()
