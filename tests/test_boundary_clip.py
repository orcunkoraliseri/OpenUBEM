import hashlib
import json

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, box

from openubem.acquisition.boundary_clip import (
    clip_to_boundary,
    split_residential,
    write_manifests,
)


def _frame():
    return gpd.GeoDataFrame(
        {"osm_id": ["res", "unknown", "shop"], "building_tag": ["house", "yes", "retail"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(3, 0, 4, 1)],
        crs="EPSG:3857",
    )


def _boundary(tmp_path):
    path = tmp_path / "boundary.geojson"
    gpd.GeoDataFrame(geometry=[box(-0.1, -0.1, 2.1, 1.1)], crs="EPSG:3857").to_crs(4326).to_file(path, driver="GeoJSON")
    return path


def test_clip_split_and_write_manifests_are_disjoint(tmp_path):
    path = _boundary(tmp_path)
    clipped = clip_to_boundary(_frame(), path, verify_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    residential, excluded, counts = split_residential(
        clipped, {"house": "residential", "yes": "unknown", "retail": "non_residential"}
    )
    assert set(residential.osm_id) == {"res"}
    assert set(excluded.osm_id) == {"unknown"}
    assert counts == {"total": 2, "residential": 1, "unknown": 1, "non_residential": 0, "annexes_removed": 0}
    write_manifests(residential, excluded, counts, tmp_path / "manifests", neighbourhood_id="TEST", source_endpoint="https://example.test", licence="Test licence")
    assert json.loads((tmp_path / "manifests" / "02_exclusion_counts.json").read_text())["neighbourhood_id"] == "TEST"
    source = json.loads((tmp_path / "manifests" / "01_source.json").read_text())
    assert source["source_endpoint"] == "https://example.test"
    assert source["licence"] == "Test licence"


def test_straddling_footprint_uses_representative_point(tmp_path):
    path = _boundary(tmp_path)
    frame = gpd.GeoDataFrame({"osm_id": ["edge"], "building_tag": ["house"]}, geometry=[box(1.9, 0, 2.2, 1)], crs="EPSG:3857")
    assert list(clip_to_boundary(frame, path).osm_id) == ["edge"]


def test_concave_polygon_with_centroid_outside_is_retained(tmp_path):
    path = tmp_path / "l_boundary.geojson"
    l_shape = Polygon([(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)])
    gpd.GeoDataFrame(geometry=[l_shape], crs="EPSG:3857").to_crs(4326).to_file(path, driver="GeoJSON")
    frame = gpd.GeoDataFrame({"osm_id": ["l"], "building_tag": ["house"]}, geometry=[l_shape], crs="EPSG:3857")
    assert not l_shape.contains(l_shape.centroid)
    assert list(clip_to_boundary(frame, path).osm_id) == ["l"]


def test_bad_boundary_checksum_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="checksum mismatch"):
        clip_to_boundary(_frame(), _boundary(tmp_path), verify_sha256="bad")
