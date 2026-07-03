"""Tests for `context_features` (T23) and its `viewer_export.build_scene` wiring (T24).

NO live network in this suite (PLAN §2 hard rule) — the ONE real fetch boundary
`ox.features.features_from_bbox` is monkeypatched, mirroring
`test_viz_basemap_raster.py`'s treatment of `_fetch_tile_image`. The real live
fetch is exercised only in T27's LIVE_SMOKE (one-off, out of CI).
"""

from __future__ import annotations

import json

import geopandas as gpd
import osmnx as ox
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon

from openubem.viz import context_features

_UTM_CRS = "EPSG:32618"  # nyc_centre's own zone (covers -78..-72 lon)


@pytest.fixture
def buildings_gdf():
    poly = Polygon([(585500, 4511500), (585600, 4511500),
                     (585600, 4511600), (585500, 4511600)])
    return gpd.GeoDataFrame({"osm_id": ["way/X"], "geometry": [poly]}, crs=_UTM_CRS)


def _mi(rows):
    return pd.MultiIndex.from_tuples(
        [(r[0], r[1]) for r in rows], names=["element_type", "osmid"])


def _roads_fixture_gdf():
    """A 2x2 lattice (3 verticals x 3 horizontals) near the pilot's own UTM
    zone -> exactly 4 enclosed cells when polygonized. Plus one non-line
    feature (a traffic-signal Point) that must be filtered out.

    Each line is densified to include EVERY lattice point it passes through
    (not just its own two endpoints): reprojection (EPSG:4326 -> UTM) is
    vertex-by-vertex and slightly nonlinear, so a crossing point that is only
    implicitly colinear on a 2-vertex line in lon/lat (never reprojected as
    its own vertex) lands a metre or so off the OTHER line's reprojected
    chord — a real, not floating-point-noise, mismatch that breaks
    `polygonize`'s node-sharing. Making every grid vertex an explicit point
    on every line it lies on guarantees the shared corner reprojects to the
    bit-identical UTM coordinate on both lines.
    """
    lons = [-74.002, -74.001, -74.000]
    lats = [40.748, 40.749, 40.750]
    geoms = []
    rows = []
    for i, lon in enumerate(lons):
        geoms.append(LineString([(lon, lat) for lat in lats]))
        rows.append(("way", 1000 + i))
    for j, lat in enumerate(lats):
        geoms.append(LineString([(lon, lat) for lon in lons]))
        rows.append(("way", 2000 + j))
    # a non-line feature that must be dropped (highway=traffic_signals is a node)
    geoms.append(Point(-74.0015, 40.7485))
    rows.append(("node", 3000))
    highway_vals = ["residential"] * 6 + ["traffic_signals"]
    gdf = gpd.GeoDataFrame(
        {"highway": highway_vals, "geometry": geoms}, index=_mi(rows), crs="EPSG:4326")
    return gdf


def _green_fixture_gdf():
    p1 = Polygon([(-74.0018, 40.7482), (-74.0016, 40.7482),
                  (-74.0016, 40.7484), (-74.0018, 40.7484)])
    p2 = Polygon([(-74.0008, 40.7492), (-74.0006, 40.7492),
                  (-74.0006, 40.7494), (-74.0008, 40.7494)])
    line = LineString([(-74.0018, 40.7482), (-74.0016, 40.7484)])  # must be dropped
    gdf = gpd.GeoDataFrame(
        {"leisure": ["park", "garden", None], "geometry": [p1, p2, line]},
        index=_mi([("way", 4001), ("way", 4002), ("way", 4003)]),
        crs="EPSG:4326",
    )
    return gdf


def _fake_features_from_bbox(bbox=None, tags=None):
    if tags == context_features._ROAD_TAGS:
        return _roads_fixture_gdf()
    if tags == context_features._GREEN_TAGS:
        return _green_fixture_gdf()
    raise AssertionError(f"unexpected tags passed to features_from_bbox: {tags}")


def test_generate_context_features_writes_three_caches_and_sidecar(
    buildings_gdf, tmp_path, monkeypatch,
):
    monkeypatch.setattr(ox.features, "features_from_bbox", _fake_features_from_bbox)

    result = context_features.generate_context_features(buildings_gdf, tmp_path, padding_frac=0.05)

    assert result["roads"] is not None and result["roads"].exists()
    assert result["green"] is not None and result["green"].exists()
    assert result["blocks"] is not None and result["blocks"].exists()
    assert result["sidecar"] is not None and result["sidecar"].exists()

    sidecar = json.loads(result["sidecar"].read_text(encoding="utf-8"))
    assert sidecar["crs"] == _UTM_CRS
    assert sidecar["attribution"] == "© OpenStreetMap contributors"

    minx, miny, maxx, maxy = buildings_gdf.total_bounds
    px = (maxx - minx) * 0.05
    py = (maxy - miny) * 0.05
    expected = (minx - px, miny - py, maxx + px, maxy + py)
    for got_v, exp_v in zip(sidecar["extent_utm"], expected):
        assert abs(got_v - exp_v) < 1e-6

    roads_fc = json.loads(result["roads"].read_text(encoding="utf-8"))
    assert roads_fc["type"] == "FeatureCollection"
    assert roads_fc["crs"] == _UTM_CRS
    # 6 LineStrings kept, the Point dropped.
    assert len(roads_fc["features"]) == 6
    for f in roads_fc["features"]:
        assert f["geometry"]["type"] == "LineString"
        assert f["properties"]["highway"] == "residential"

    green_fc = json.loads(result["green"].read_text(encoding="utf-8"))
    # 2 Polygons kept, the LineString dropped.
    assert len(green_fc["features"]) == 2
    for f in green_fc["features"]:
        assert f["geometry"]["type"] == "Polygon"

    blocks_fc = json.loads(result["blocks"].read_text(encoding="utf-8"))
    # A 3x3 lattice (2x2 grid of cells) polygonizes into exactly 4 enclosed cells.
    assert len(blocks_fc["features"]) == 4
    for f in blocks_fc["features"]:
        assert f["properties"]["derived"] is True
        assert f["properties"]["source"] == "osm_road_polygonize"
        assert f["geometry"]["type"] == "Polygon"


def test_generate_context_features_roads_fetch_failure_is_non_fatal(
    buildings_gdf, tmp_path, monkeypatch,
):
    def _fake(bbox=None, tags=None):
        if tags == context_features._ROAD_TAGS:
            raise RuntimeError("no network")
        return _green_fixture_gdf()

    monkeypatch.setattr(ox.features, "features_from_bbox", _fake)
    result = context_features.generate_context_features(buildings_gdf, tmp_path)

    assert result["roads"] is None
    assert result["green"] is not None
    # No road lines to polygonize -> blocks is also None (not a stale/fabricated derivation).
    assert result["blocks"] is None
    assert result["sidecar"] is not None  # sidecar write does not depend on network


def test_generate_context_features_green_fetch_failure_is_non_fatal(
    buildings_gdf, tmp_path, monkeypatch,
):
    def _fake(bbox=None, tags=None):
        if tags == context_features._GREEN_TAGS:
            raise RuntimeError("no network")
        return _roads_fixture_gdf()

    monkeypatch.setattr(ox.features, "features_from_bbox", _fake)
    result = context_features.generate_context_features(buildings_gdf, tmp_path)

    assert result["green"] is None
    assert result["roads"] is not None
    assert result["blocks"] is not None  # roads still succeeded, blocks still derivable


def test_generate_context_features_total_fetch_failure_no_exception(
    buildings_gdf, tmp_path, monkeypatch,
):
    def _boom(bbox=None, tags=None):
        raise RuntimeError("no network at all")

    monkeypatch.setattr(ox.features, "features_from_bbox", _boom)
    result = context_features.generate_context_features(buildings_gdf, tmp_path)

    assert result["roads"] is None
    assert result["green"] is None
    assert result["blocks"] is None
    assert result["sidecar"] is not None


def test_generate_context_features_no_crs_returns_all_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ox.features, "features_from_bbox", _fake_features_from_bbox)
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf = gpd.GeoDataFrame({"osm_id": ["way/Y"], "geometry": [poly]})  # no CRS
    result = context_features.generate_context_features(gdf, tmp_path)
    assert result == {"roads": None, "green": None, "blocks": None, "sidecar": None}
