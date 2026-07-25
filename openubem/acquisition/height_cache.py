"""Height-cache layout + one-off Overture pull entry point (E-UTCI-09 height
backfill sub-plan, T04/T05).

`pull_overture` is a MANUAL, ONE-OFF network entry point (plan hard rule 4).
It is never called at import time, never re-exported from any `__init__`,
and must never be reachable from `pytest`, CI, or a production pipeline
entry point. Everything downstream of T05 reads the local cache via
`load_cached`, which never fetches.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from openubem.config import HEIGHT_CACHE_DIR

# WGS84 spherical-earth approximation: 1 degree of latitude ~= 111,320 m
# (standard geodesy constant, e.g. Snyder 1987 "Map Projections: A Working
# Manual" -- not fitted to any OpenUBEM output). Longitude degrees are
# scaled by cos(latitude) because meridians converge toward the poles.
_M_PER_DEG_LAT = 111_320.0

# The 4 E-UTCI-09-affected cells' coordinates, copied verbatim from
# scripts/validation/v12_cell_pipeline.py::CELL_CONFIGS (plan F-J) rather
# than imported from that script, so this module's import path stays free
# of any script-only dependency.
AFFECTED_CELLS: dict = {
    "nyc_suburban": {"lat": 40.7052, "lon": -73.5985, "radius_m": 500.0, "epsg": 32618},
    "nyc_rural": {"lat": 42.0396, "lon": -74.1143, "radius_m": 1000.0, "epsg": 32618},
    "austin_centre": {"lat": 30.2672, "lon": -97.7431, "radius_m": 500.0, "epsg": 32614},
    "austin_rural": {"lat": 30.5788, "lon": -98.2700, "radius_m": 1000.0, "epsg": 32614},
}

# Proven-reachable Overture Buildings endpoint (T12.6 CP-4 LIVE_SMOKE
# precedent, docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md
# and scratchpad/t12_cp4_live_smoke.py) -- reused rather than re-derived,
# per hard rule 4 ("do not retry against another service").
OVERTURE_ENDPOINT = "s3://overturemaps-us-west-2/release/2026-06-17.0/theme=buildings/type=building/*"


def cell_bbox(lat: float, lon: float, radius_m: float) -> "tuple[float, float, float, float]":
    """(lat, lon, radius_m) -> WGS84 (minx, miny, maxx, maxy) bbox."""
    dlat = radius_m / _M_PER_DEG_LAT
    dlon = radius_m / (_M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def _cache_path(cell: str) -> Path:
    return HEIGHT_CACHE_DIR / f"overture_{cell}.parquet"


def _manifest_path() -> Path:
    return HEIGHT_CACHE_DIR / "manifest.json"


def load_cached(cell: str) -> gpd.GeoDataFrame:
    """Read-only: never fetches. Raises a clear error if T05 has not been run
    for this cell yet."""
    path = _cache_path(cell)
    if not path.exists():
        raise FileNotFoundError(
            f"height_cache.load_cached({cell!r}): no cached Overture pull at {path}. "
            "Run pull_overture(cell) manually first (plan T05) -- this reader "
            "never fetches from the network."
        )
    return gpd.read_parquet(path)


def load_manifest() -> dict:
    path = _manifest_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest_row(cell: str, bbox, row_count: int, endpoint: str) -> dict:
    manifest = load_manifest()
    manifest[cell] = {
        "bbox_wgs84": list(bbox),
        "row_count": row_count,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
    }
    HEIGHT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _manifest_path().write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest[cell]


def pull_overture(cell: str, *, endpoint: str = OVERTURE_ENDPOINT) -> gpd.GeoDataFrame:
    """MANUAL, ONE-OFF network entry point -- plan T05, hard rule 4.

    Never call this from pytest, CI, or any pipeline module. It performs a
    single real network fetch (`overture_fetcher.fetch_overture(endpoint=...)`)
    scoped to one of the 4 E-UTCI-09-affected cells' bboxes, then writes the
    result and a manifest row to `HEIGHT_CACHE_DIR`. If the endpoint is
    unreachable or the pull errors, this raises -- the caller must STOP and
    report, never retry against a different service or substitute another
    dataset (hard rule 4).
    """
    if cell not in AFFECTED_CELLS:
        raise ValueError(
            f"pull_overture: {cell!r} is not one of the 4 affected cells: "
            f"{sorted(AFFECTED_CELLS)}"
        )
    from openubem.acquisition.overture_fetcher import fetch_overture

    spec = AFFECTED_CELLS[cell]
    bbox = cell_bbox(spec["lat"], spec["lon"], spec["radius_m"])
    layer = fetch_overture(bbox=bbox, endpoint=endpoint)

    HEIGHT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    layer.to_parquet(_cache_path(cell))
    _write_manifest_row(cell, bbox, len(layer), endpoint)
    return layer
