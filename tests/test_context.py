"""Tests for openubem.geometry.context (T07)."""
import math

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from openubem.geometry.context import discover_context


def _square(cx: float, cy: float, side: float) -> Polygon:
    h = side / 2
    return Polygon([(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)])


def _make_gdf(rows: list[dict]) -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    gdf["_simplified_geom"] = gdf["geometry"]
    return gdf


class TestContext:
    def _base_gdf(self) -> gpd.GeoDataFrame:
        rows = [
            {"osm_id": f"b{i}", "geometry": _square(i * 20.0, 0.0, 10.0),
             "height_m": 5.0 * i if i > 0 else float("nan"),
             "levels": float("nan")}
            for i in range(5)
        ]
        return _make_gdf(rows)

    def test_returns_4_neighbours(self):
        gdf = self._base_gdf()
        target_row = gdf[gdf["osm_id"] == "b2"].iloc[0]
        target_poly, cx, cy = target_row["_simplified_geom"], 40.0, 0.0
        ctx = discover_context(target_row, gdf, cx, cy, sphere_radius_m=30.0)
        names = [c["name"] for c in ctx]
        assert len(ctx) >= 2  # b1 at 20m and b3 at 60m within 30m sphere from b2 centre
        assert "shade_b2" not in names

    def test_self_exclusion(self):
        gdf = self._base_gdf()
        target_row = gdf[gdf["osm_id"] == "b0"].iloc[0]
        ctx = discover_context(target_row, gdf, 0.0, 0.0, sphere_radius_m=30.0)
        assert all(c["name"] != "shade_b0" for c in ctx)

    def test_empty_result_isolated_building(self):
        far_rows = [
            {"osm_id": "near", "geometry": _square(0.0, 0.0, 10.0),
             "height_m": 5.0, "levels": float("nan")},
            {"osm_id": "far", "geometry": _square(200.0, 200.0, 10.0),
             "height_m": 5.0, "levels": float("nan")},
        ]
        gdf = _make_gdf(far_rows)
        target_row = gdf[gdf["osm_id"] == "far"].iloc[0]
        ctx = discover_context(target_row, gdf, 200.0, 200.0, sphere_radius_m=30.0)
        assert ctx == []

    def test_coordinate_translation(self):
        rows = [
            {"osm_id": "target", "geometry": _square(1000.0, 2000.0, 10.0),
             "height_m": 5.0, "levels": float("nan")},
            {"osm_id": "neighbour", "geometry": _square(1020.0, 2000.0, 10.0),
             "height_m": 5.0, "levels": float("nan")},
        ]
        gdf = _make_gdf(rows)
        target_row = gdf[gdf["osm_id"] == "target"].iloc[0]
        ctx = discover_context(target_row, gdf, 1000.0, 2000.0, sphere_radius_m=30.0)
        assert len(ctx) == 1
        for x, y in ctx[0]["coords"]:
            assert abs(x) < 50
            assert abs(y) < 50

    def test_height_from_height_m(self):
        rows = [
            {"osm_id": "t", "geometry": _square(0.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": float("nan")},
            {"osm_id": "n", "geometry": _square(15.0, 0.0, 10.0),
             "height_m": 12.0, "levels": float("nan")},
        ]
        gdf = _make_gdf(rows)
        target_row = gdf[gdf["osm_id"] == "t"].iloc[0]
        ctx = discover_context(target_row, gdf, 0.0, 0.0, sphere_radius_m=30.0)
        assert len(ctx) == 1
        assert abs(ctx[0]["height"] - 12.0) < 1e-6

    def test_height_fallback_levels(self):
        rows = [
            {"osm_id": "t", "geometry": _square(0.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": float("nan")},
            {"osm_id": "n", "geometry": _square(15.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": 3.0},
        ]
        gdf = _make_gdf(rows)
        target_row = gdf[gdf["osm_id"] == "t"].iloc[0]
        ctx = discover_context(target_row, gdf, 0.0, 0.0, sphere_radius_m=30.0)
        assert len(ctx) == 1
        assert abs(ctx[0]["height"] - 10.5) < 1e-6

    def test_height_fallback_both_nan(self):
        rows = [
            {"osm_id": "t", "geometry": _square(0.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": float("nan")},
            {"osm_id": "n", "geometry": _square(15.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": float("nan")},
        ]
        gdf = _make_gdf(rows)
        target_row = gdf[gdf["osm_id"] == "t"].iloc[0]
        ctx = discover_context(target_row, gdf, 0.0, 0.0, sphere_radius_m=30.0)
        assert len(ctx) == 1
        assert abs(ctx[0]["height"] - 3.5) < 1e-6

    def test_name_format(self):
        rows = [
            {"osm_id": "t", "geometry": _square(0.0, 0.0, 10.0),
             "height_m": float("nan"), "levels": float("nan")},
            {"osm_id": "abc123", "geometry": _square(15.0, 0.0, 10.0),
             "height_m": 5.0, "levels": float("nan")},
        ]
        gdf = _make_gdf(rows)
        target_row = gdf[gdf["osm_id"] == "t"].iloc[0]
        ctx = discover_context(target_row, gdf, 0.0, 0.0, sphere_radius_m=30.0)
        assert ctx[0]["name"] == "shade_abc123"
