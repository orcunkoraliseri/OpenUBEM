"""Tests for openubem.viz.cityjson_emitter (T03) + geojson_context (T04).

Synthetic in-memory fixture: two buildings that both reuse the small real DOE
Restaurant IDF (tests/fixtures/viz/Restaurant_QuickServiceRestaurant_90.1-2013.idf)
placed at two distinct UTM centroids, so positioning (Option A true relative
frame) is exercised without needing the heavy 738-building pilot on disk.
"""
import json
import math
import os

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from openubem.viz.cityjson_emitter import (
    build_cityjson,
    dumps,
    footprint_centroids_utm,
)
from openubem.viz.geojson_context import build_context_geojson
from openubem.viz.geometry_extract import collect_geometry

_FIXTURE_IDF = os.path.join(
    os.path.dirname(__file__), "fixtures", "viz",
    "Restaurant_QuickServiceRestaurant_90.1-2013.idf",
)

# Two footprint centroids ~250 m apart in EPSG:32618 metres.
_CENTROID_A = (500000.0, 4500000.0)
_CENTROID_B = (500250.0, 4500180.0)


def _square(cx, cy, half=10.0):
    return Polygon([(cx - half, cy - half), (cx + half, cy - half),
                    (cx + half, cy + half), (cx - half, cy + half)])


@pytest.fixture(scope="module")
def manifest_df():
    return pd.DataFrame([
        {"osm_id": "way/B", "idf_path": _FIXTURE_IDF,
         "zoning_strategy": "single_zone", "num_zones": 3,
         "generation_status": "success", "data_quality_flag": "no_height"},
        {"osm_id": "way/A", "idf_path": _FIXTURE_IDF,
         "zoning_strategy": "single_zone", "num_zones": 3,
         "generation_status": "success", "data_quality_flag": ""},
    ])


@pytest.fixture(scope="module")
def buildings_gdf():
    return gpd.GeoDataFrame(
        {
            "osm_id": ["way/A", "way/B"],
            "levels": [1, 1],
            "year_built": [1990.0, 1985.0],
            "geometry": [_square(*_CENTROID_A), _square(*_CENTROID_B)],
        },
        crs="EPSG:32618",
    )


@pytest.fixture(scope="module")
def cityjson(manifest_df, buildings_gdf):
    return build_cityjson(manifest_df, buildings_gdf)


def _decode_vertex(cityjson, idx):
    s = cityjson["transform"]["scale"]
    t = cityjson["transform"]["translate"]
    v = cityjson["vertices"][idx]
    return (v[0] * s[0] + t[0], v[1] * s[1] + t[1], v[2] * s[2] + t[2])


class TestEmitter:
    def test_a_valid_cityjson_v2_structure(self, cityjson):
        # Structural CityJSON v2.0 check (cjio not installed).
        assert cityjson["type"] == "CityJSON"
        assert cityjson["version"] == "2.0"
        assert "transform" in cityjson and "vertices" in cityjson
        assert set(cityjson["metadata"]) >= {"referenceSystem", "+common_origin_utm"}
        assert cityjson["metadata"]["referenceSystem"].endswith("/32618")
        n_verts = len(cityjson["vertices"])
        for v in cityjson["vertices"]:
            assert len(v) == 3 and all(isinstance(c, int) for c in v)
        for osm_id, co in cityjson["CityObjects"].items():
            assert co["type"] == "Building"
            for geom in co["geometry"]:
                assert geom["type"] == "MultiSurface"
                assert geom["lod"] in ("1", "3")
                surfaces = geom["semantics"]["surfaces"]
                values = geom["semantics"]["values"]
                assert len(values) == len(geom["boundaries"])
                for val in values:
                    assert 0 <= val < len(surfaces)  # semantic index in range
                for surface in geom["boundaries"]:
                    for ring in surface:
                        for vi in ring:
                            assert 0 <= vi < n_verts  # vertex index in range

    def test_b_each_building_has_lod1_and_lod3(self, cityjson):
        for co in cityjson["CityObjects"].values():
            lods = {g["lod"] for g in co["geometry"]}
            assert lods == {"1", "3"}

    def test_c_lod1_no_openings_lod3_has_openings(self, cityjson):
        for co in cityjson["CityObjects"].values():
            by_lod = {g["lod"]: g for g in co["geometry"]}
            lod1_types = {s["type"] for s in by_lod["1"]["semantics"]["surfaces"]}
            lod3_types = {s["type"] for s in by_lod["3"]["semantics"]["surfaces"]}
            assert lod1_types.isdisjoint({"Window", "Door"})
            assert "Window" in lod3_types  # fixture has 3 windows + 1 door

    def test_c2_windows_nested_under_parent_wall(self, cityjson):
        co = next(iter(cityjson["CityObjects"].values()))
        lod3 = next(g for g in co["geometry"] if g["lod"] == "3")
        surfaces = lod3["semantics"]["surfaces"]
        windows = [s for s in surfaces if s["type"] in ("Window", "Door")]
        assert windows, "expected sub-surfaces"
        for w in windows:
            assert "parent" in w
            parent = surfaces[w["parent"]]
            assert parent["type"] == "WallSurface"
            assert w["surf_name"] != parent["surf_name"]

    def test_d_byte_identical_across_runs(self, manifest_df, buildings_gdf):
        a = dumps(build_cityjson(manifest_df, buildings_gdf))
        b = dumps(build_cityjson(manifest_df, buildings_gdf))
        assert a == b

    def test_e_vertex_roundtrip_through_offsets(self, cityjson, buildings_gdf):
        """CP-Geometry: (CityJSON_vertex + common_origin) − footprint_centroid_UTM
        == source IDF (recentre=False) vertex, within 1 cm.
        """
        ox, oy, _ = cityjson["metadata"]["+common_origin_utm"]
        centroids = footprint_centroids_utm(buildings_gdf)
        source = collect_geometry(_FIXTURE_IDF, recentre=False)
        # index source opaque faces by surf_name for lookup
        src_by_name = {sn: verts for (_, _, cat, verts, sn) in source["faces"]
                       if cat in ("wall", "roof")}
        checked = 0
        for osm_id, co in cityjson["CityObjects"].items():
            cx, cy = centroids[osm_id]
            lod1 = next(g for g in co["geometry"] if g["lod"] == "1")
            for surface, sem in zip(lod1["boundaries"],
                                    lod1["semantics"]["values"]):
                surf_name = lod1["semantics"]["surfaces"][sem]["surf_name"]
                src_verts = src_by_name[surf_name]
                ring = surface[0]
                assert len(ring) == len(src_verts)
                for vi, (sx, sy, sz) in zip(ring, src_verts):
                    dx, dy, dz = _decode_vertex(cityjson, vi)
                    rx = dx + ox - cx
                    ry = dy + oy - cy
                    rz = dz
                    assert abs(rx - sx) <= 0.01
                    assert abs(ry - sy) <= 0.01
                    assert abs(rz - sz) <= 0.01
                    checked += 1
        assert checked > 0

    def test_positioning_buildings_not_stacked(self, cityjson, buildings_gdf):
        """Two buildings at distinct UTM centroids must occupy distinct XY
        regions in the shared frame (Option A), not overlap at the origin.
        """
        centroids = footprint_centroids_utm(buildings_gdf)
        ox, oy, _ = cityjson["metadata"]["+common_origin_utm"]
        xy = {}
        for osm_id, co in cityjson["CityObjects"].items():
            lod1 = next(g for g in co["geometry"] if g["lod"] == "1")
            xs, ys = [], []
            for surface in lod1["boundaries"]:
                for vi in surface[0]:
                    dx, dy, _dz = _decode_vertex(cityjson, vi)
                    xs.append(dx); ys.append(dy)
            xy[osm_id] = (sum(xs) / len(xs), sum(ys) / len(ys))
        (ax, ay), (bx, by) = xy["way/A"], xy["way/B"]
        # centroids differ by ~ (250,180) m -> local centroids differ similarly
        assert math.hypot(ax - bx, ay - by) > 100.0


class TestContextPlaceholders:
    """T04: extruded-footprint placeholders for buildings with no IDF."""

    @pytest.fixture(scope="class")
    def gdf_with_absent(self):
        # A and B have IDFs (emitted); C has NO IDF (must become a placeholder).
        return gpd.GeoDataFrame(
            {
                "osm_id": ["way/A", "way/B", "way/C"],
                "levels": [1, 1, 4],
                "height_m": [None, None, None],
                "geometry": [_square(*_CENTROID_A), _square(*_CENTROID_B),
                             _square(500600.0, 4500400.0)],
            },
            crs="EPSG:32618",
        )

    def test_placeholder_set_is_absent_buildings_only(self, gdf_with_absent):
        fc = build_context_geojson(
            gdf_with_absent, emitted_osm_ids={"way/A", "way/B"},
            common_origin=(500000.0, 4500000.0, 0.0),
        )
        ids = {f["properties"]["osm_id"] for f in fc["features"]}
        assert ids == {"way/C"}

    def test_every_feature_has_height_and_osm_id_and_flag(self, gdf_with_absent):
        fc = build_context_geojson(
            gdf_with_absent, emitted_osm_ids={"way/A", "way/B"},
            common_origin=(500000.0, 4500000.0, 0.0),
        )
        for f in fc["features"]:
            assert f["properties"]["osm_id"]
            assert f["properties"]["height"] == 4 * 3.5  # 4 levels
            assert f["properties"]["is_approximation"] is True
            assert f["geometry"]["type"] in ("Polygon", "MultiPolygon")

    def test_no_absent_buildings_yields_empty_collection(self, gdf_with_absent):
        fc = build_context_geojson(
            gdf_with_absent, emitted_osm_ids={"way/A", "way/B", "way/C"},
            common_origin=(500000.0, 4500000.0, 0.0),
        )
        assert fc["features"] == []
        assert fc["type"] == "FeatureCollection"
