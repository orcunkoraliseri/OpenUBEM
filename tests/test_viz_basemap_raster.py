"""Tests for `basemap_raster` (T16).

NO live network in this suite (PLAN §2 hard rule) — the ONE real tile fetch is
monkeypatched at `basemap_raster._fetch_tile_image`, the sole network boundary.
`rasterio.warp.transform_bounds`/`reproject` are pure local PROJ/GDAL math, not
network calls, so the fake still exercises the real reprojection path.
"""

from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import Polygon

from openubem.viz import basemap_raster

_UTM_CRS = "EPSG:32618"


@pytest.fixture
def buildings_gdf():
    # A small square footprint near NYC, in the pilot's own UTM zone.
    poly = Polygon([(585500, 4511500), (585600, 4511500),
                     (585600, 4511600), (585500, 4511600)])
    return gpd.GeoDataFrame({"osm_id": ["way/X"], "geometry": [poly]}, crs=_UTM_CRS)


def _fake_fetch_factory(px=8):
    """A monkeypatch double for `_fetch_tile_image` — no network, real PROJ math."""
    calls = []

    def _fake(w, s, e, n, *, zoom, provider):
        from rasterio.warp import transform_bounds
        calls.append((w, s, e, n, zoom, provider))
        minx, miny, maxx, maxy = transform_bounds("EPSG:4326", "EPSG:3857", w, s, e, n)
        rng = np.random.default_rng(0)
        img = rng.integers(0, 255, size=(px, px, 4), dtype=np.uint8)
        return img, (minx, maxx, miny, maxy)

    return _fake, calls


def test_generate_basemap_writes_png_and_sidecar_within_tolerance(
    buildings_gdf, tmp_path, monkeypatch,
):
    fake, calls = _fake_fetch_factory()
    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", fake)

    sidecar = basemap_raster.generate_basemap(
        buildings_gdf, tmp_path, padding_frac=0.05, target_px=64)

    assert sidecar is not None, "generate_basemap must succeed with a stubbed fetch"
    assert calls, "the fetch boundary must have been invoked (reproject is exercised)"

    png_path = tmp_path / basemap_raster.BASEMAP_PNG_NAME
    json_path = tmp_path / basemap_raster.BASEMAP_SIDECAR_NAME
    assert png_path.exists() and png_path.stat().st_size > 0
    assert json_path.exists()

    on_disk = json.loads(json_path.read_text(encoding="utf-8"))
    assert on_disk == sidecar

    assert sidecar["crs"] == _UTM_CRS
    assert sidecar["attribution"]
    assert sidecar["fetched_px"] == [8, 8]

    # Padded UTM bounds (5% of a 100x100 m square = 5 m each side).
    minx, miny, maxx, maxy = buildings_gdf.total_bounds
    px_pad = (maxx - minx) * 0.05
    py_pad = (maxy - miny) * 0.05
    expected = (minx - px_pad, miny - py_pad, maxx + px_pad, maxy + py_pad)

    got = sidecar["extent_utm"]
    # A tiny (100 m-ish) bbox at ~41N: mercator round-trip + an 8x8 source grid
    # introduce sub-pixel/edge slop, but never anything close to the ~17 m
    # meridian-convergence error a bare relabel (no reproject) would leave.
    tol = 3.0
    for got_v, exp_v in zip(got, expected):
        assert abs(got_v - exp_v) < tol, f"{got} vs expected {expected}"


def test_generate_basemap_returns_none_on_fetch_failure(buildings_gdf, tmp_path, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("no network")

    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", _boom)
    assert basemap_raster.generate_basemap(buildings_gdf, tmp_path) is None
    assert not (tmp_path / basemap_raster.BASEMAP_PNG_NAME).exists()


def test_generate_basemap_no_crs_returns_none(tmp_path, monkeypatch):
    fake, _ = _fake_fetch_factory()
    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", fake)
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf = gpd.GeoDataFrame({"osm_id": ["way/Y"], "geometry": [poly]})  # no CRS
    assert basemap_raster.generate_basemap(gdf, tmp_path) is None


def test_generate_basemap_bumps_auto_zoom_to_avoid_upsampling(tmp_path, monkeypatch):
    """Debug fix D04 (docs_ACTIVE/3D/debug/PLAN_3dviz_debug_representation.md):
    `zoom="auto"` alone under-selects tile zoom for a real-scale (~1.5 km)
    neighbourhood bbox, so the fetched raster is far smaller than `target_px`
    and gets blurrily upsampled. The fetch must now be called with a
    bumped-up int zoom (still resolved by pure local tile-count math, no
    extra network call). Uses a cell-scale footprint (not the 100 m unit
    fixture, whose auto zoom already saturates the provider's max_zoom)."""
    import contextily as ctx

    from openubem.viz import basemap_raster

    # ~1.5 km x 1.5 km footprint near Austin, TX — comparable to a phaseE cell.
    poly = Polygon([(620000, 3350000), (621500, 3350000),
                     (621500, 3351500), (620000, 3351500)])
    cell_gdf = gpd.GeoDataFrame({"osm_id": ["way/Z"], "geometry": [poly]}, crs="EPSG:32614")

    fake, calls = _fake_fetch_factory()
    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", fake)

    sidecar = basemap_raster.generate_basemap(
        cell_gdf, tmp_path, padding_frac=0.05, target_px=3072)

    assert sidecar is not None
    assert len(calls) == 1, "still exactly one network boundary call"
    called_zoom = calls[0][4]
    assert isinstance(called_zoom, int), "auto must resolve to a concrete int before the fetch"

    minx, miny, maxx, maxy = cell_gdf.total_bounds
    px_pad = (maxx - minx) * 0.05
    py_pad = (maxy - miny) * 0.05
    from rasterio.warp import transform_bounds
    west, south, east, north = transform_bounds(
        "EPSG:32614", "EPSG:4326", minx - px_pad, miny - py_pad, maxx + px_pad, maxy + py_pad)
    base_zoom = ctx.tile._calculate_zoom(west, south, east, north)

    assert called_zoom > base_zoom, "must bump past the under-selecting auto zoom for a real-scale bbox"
    assert called_zoom <= base_zoom + 3, "bump capped at +3 (§6.4)"
    assert sidecar["zoom"] == called_zoom, "sidecar must record the resolved int, not the literal 'auto'"


def test_generate_basemap_explicit_int_zoom_honoured_verbatim(buildings_gdf, tmp_path, monkeypatch):
    """F-B1: an explicit int `zoom` must pass through unchanged, never resolved/bumped."""
    from openubem.viz import basemap_raster

    fake, calls = _fake_fetch_factory()
    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", fake)

    sidecar = basemap_raster.generate_basemap(
        buildings_gdf, tmp_path, padding_frac=0.05, target_px=3072, zoom=12)

    assert sidecar is not None
    assert calls[0][4] == 12
    assert sidecar["zoom"] == 12


def test_generate_basemap_non_rgba_band_count(buildings_gdf, tmp_path, monkeypatch):
    """RGB-only (3-band) tile sources must still reproject + write cleanly."""
    def _fake_rgb(w, s, e, n, *, zoom, provider):
        from rasterio.warp import transform_bounds
        minx, miny, maxx, maxy = transform_bounds("EPSG:4326", "EPSG:3857", w, s, e, n)
        rng = np.random.default_rng(1)
        img = rng.integers(0, 255, size=(6, 6, 3), dtype=np.uint8)
        return img, (minx, maxx, miny, maxy)

    monkeypatch.setattr(basemap_raster, "_fetch_tile_image", _fake_rgb)
    sidecar = basemap_raster.generate_basemap(buildings_gdf, tmp_path, target_px=32)
    assert sidecar is not None
    assert sidecar["fetched_px"] == [6, 6]
