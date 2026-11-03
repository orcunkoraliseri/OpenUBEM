"""OPEN-66: a zoneless IDF must never be reported as success."""
import tempfile
from pathlib import Path

import geopandas as gpd
import pytest
from geomeppy import IDF

from openubem.idf import builder as builder_mod
from openubem.idf.builder import BuildingIDF
from tests.test_builder_elevators_wired import _make_row


def _build(row):
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        (out_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, out_path)
    return manifest, bidf.idf


def test_zero_zone_idf_is_not_success(monkeypatch):
    def _extrude_nothing(idf, zones, context):
        for z in zones:
            z["extruded"] = True

    monkeypatch.setattr(builder_mod, "extrude_geometry", _extrude_nothing)
    row = _make_row("LargeOffice", footprint_area_m2=2000.0, levels=4)
    manifest, idf = _build(row)
    assert len(idf.idfobjects["ZONE"]) == 0
    assert manifest["generation_status"] == "failed_no_zones", manifest
    assert manifest["idf_path"] == ""
    assert manifest["num_zones"] == 0


@pytest.mark.parametrize("exc", [NotImplementedError, IndexError])
def test_coreperim_intersect_match_failure_keeps_zones(monkeypatch, exc):
    original = IDF.intersect_match
    calls = {"n": 0}

    def _flaky(self, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise exc("simulated geomeppy failure")
        return original(self, *a, **k)

    monkeypatch.setattr(IDF, "intersect_match", _flaky)
    row = _make_row("LargeOffice", footprint_area_m2=2000.0, levels=4)
    manifest, idf = _build(row)
    assert calls["n"] >= 2
    assert len(idf.idfobjects["ZONE"]) > 0
    assert manifest["generation_status"] != "failed_no_zones", manifest
