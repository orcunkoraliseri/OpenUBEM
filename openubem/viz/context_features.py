"""Per-run OSM urban-context cache: roads / green space / derived block boundaries (T23).

Phase-G source side (PLAN Phase G). Same fetch-once-then-cache reproducibility
discipline as `basemap_raster.py` (T16): the network touch happens ONLY here,
at generation time; the shipped viewer embeds the cached bytes and performs
zero runtime fetch (PLAN §2 offline constraint).

This is OSM CONTEXT, not simulation output (Phase-G binding preamble rule 1):
roads/green/blocks are never routed through `acquisition/osm_fetcher.py`'s
building-specific 7-step cleaner + quality-flag logic — `ox.features.
features_from_bbox` is called directly here, with different tags, using the
SAME pinned `osmnx` version guard.

Block boundaries are DERIVED (preamble rule 3): `shapely.ops.polygonize` on the
fetched road network's line geometries, kept as exterior-ring-only outlines,
tagged `derived=True` / `source="osm_road_polygonize"` — never presented as an
authoritative OSM object or a cadastre/parcel source.

Fetch failure / no network -> that layer's cache is simply not written and the
function returns `None` for it, non-fatal, mirroring `generate_basemap`.
"""

from __future__ import annotations

import json
from pathlib import Path

import osmnx as ox
from packaging.version import Version
from shapely.geometry import Polygon, mapping
from shapely.ops import polygonize, unary_union

assert Version("1.9") <= Version(ox.__version__) < Version("2.0"), (
    f"osmnx version out of pinned range [1.9, 2.0): {ox.__version__}"
)

_ATTRIBUTION = "© OpenStreetMap contributors"

ROADS_NAME = "06_context_roads.geojson"
GREEN_NAME = "06_context_green.geojson"
BLOCKS_NAME = "06_context_blocks.geojson"
SIDECAR_NAME = "06_context.json"

_ROAD_TAGS = {"highway": True}
_GREEN_TAGS = {
    "leisure": ["park", "garden", "pitch"],
    "landuse": ["grass", "forest", "meadow", "recreation_ground", "village_green"],
    "natural": ["wood", "scrub"],
}


def _feature_id(gdf) -> list[str]:
    """Stable per-feature id from osmnx's (element_type, osmid) index, mirroring
    `acquisition/osm_fetcher.py::_flatten_tags`'s `osm_id` derivation."""
    g = gdf.reset_index()
    if "element_type" in g.columns and "osmid" in g.columns:
        return (g["element_type"].astype(str) + "/" + g["osmid"].astype(str)).tolist()
    return [str(i) for i in range(len(g))]


def _write_geojson(path: Path, features: list[dict], crs_str: str) -> None:
    fc = {
        "type": "FeatureCollection",
        "crs": crs_str,
        "features": features,
    }
    path.write_text(json.dumps(fc, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _fetch_roads_gdf(bbox_wgs84):
    """The ONE network boundary for roads — tests monkeypatch `ox.features.features_from_bbox`."""
    return ox.features.features_from_bbox(bbox=bbox_wgs84, tags=_ROAD_TAGS)


def _fetch_green_gdf(bbox_wgs84):
    """The ONE network boundary for green space — same fetch fn, different tags."""
    return ox.features.features_from_bbox(bbox=bbox_wgs84, tags=_GREEN_TAGS)


def _roads_to_features(raw_gdf, utm_crs_str, fid) -> list[dict]:
    keep = raw_gdf.geom_type.isin(["LineString", "MultiLineString"])
    gdf = raw_gdf[keep].copy()
    gdf["__fid"] = [f for f, k in zip(fid, keep) if k]
    gdf = gdf.to_crs(utm_crs_str)
    has_highway = "highway" in gdf.columns
    records = []
    for i in range(len(gdf)):
        geom = gdf.geometry.iloc[i]
        if geom is None or geom.is_empty:
            continue
        highway = str(gdf["highway"].iloc[i]) if has_highway else ""
        records.append((str(gdf["__fid"].iloc[i]), geom, highway))
    records.sort(key=lambda t: t[0])
    return [
        {"type": "Feature", "geometry": mapping(geom),
         "properties": {"osm_id": rid, "highway": highway}}
        for (rid, geom, highway) in records
    ]


def _green_to_features(raw_gdf, utm_crs_str, fid) -> list[dict]:
    keep = raw_gdf.geom_type.isin(["Polygon", "MultiPolygon"])
    gdf = raw_gdf[keep].copy()
    gdf["__fid"] = [f for f, k in zip(fid, keep) if k]
    gdf = gdf.to_crs(utm_crs_str)
    records = []
    for i in range(len(gdf)):
        geom = gdf.geometry.iloc[i]
        if geom is None or geom.is_empty:
            continue
        records.append((str(gdf["__fid"].iloc[i]), geom))
    records.sort(key=lambda t: t[0])
    return [
        {"type": "Feature", "geometry": mapping(geom),
         "properties": {"osm_id": rid}}
        for (rid, geom) in records
    ]


def _roads_to_lines(raw_gdf, utm_crs_str):
    """Flatten LineString/MultiLineString road geometries into a plain list of
    UTM LineStrings, for `shapely.ops.polygonize` (block derivation)."""
    keep = raw_gdf.geom_type.isin(["LineString", "MultiLineString"])
    gdf = raw_gdf[keep].to_crs(utm_crs_str)
    lines = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "LineString":
            lines.append(geom)
        elif geom.geom_type == "MultiLineString":
            lines.extend(geom.geoms)
    return lines


def _blocks_to_features(lines) -> list[dict]:
    """Derive block outlines by polygonizing the road network (preamble rule 3):
    exterior-ring-only, tagged `derived`/`source` — a pure geometric derivation
    of the fetched roads, deterministic, never snapped to buildings.

    `unary_union` first: `polygonize` only splits linework at shared endpoints,
    not at plain geometric crossings, so raw un-noded road lines (e.g. one
    LineString crossing another mid-span) would polygonize into a single
    outer ring instead of the enclosed cells. `unary_union` nodes the network
    at every intersection before polygonizing (deterministic, pure geometry)."""
    merged = unary_union(lines)
    polys = list(polygonize(merged))
    records = []
    for p in polys:
        outline = Polygon(p.exterior)
        c = outline.centroid
        records.append((round(c.x, 3), round(c.y, 3), outline))
    records.sort(key=lambda t: (t[0], t[1]))
    return [
        {"type": "Feature", "geometry": mapping(outline),
         "properties": {"derived": True, "source": "osm_road_polygonize"}}
        for (_, _, outline) in records
    ]


def generate_context_features(
    buildings_gdf,
    out_dir,
    *,
    padding_frac: float = 0.05,
) -> dict:
    """Fetch + reproject + cache the three OSM context layers; return a dict of
    `{"roads": Path|None, "green": Path|None, "blocks": Path|None, "sidecar": Path|None}`.

    Any layer's fetch failure (no network, empty result, ...) is swallowed and
    that layer's Path is `None` — non-fatal, mirroring `generate_basemap` (T16).
    A missing/unusable CRS on `buildings_gdf` returns all-`None` (no bbox to fetch).
    """
    out_dir = Path(out_dir)
    result = {"roads": None, "green": None, "blocks": None, "sidecar": None}

    utm_crs = buildings_gdf.crs
    if utm_crs is None:
        return result
    utm_crs_str = utm_crs.to_string()

    try:
        from rasterio.warp import transform_bounds
    except Exception:  # noqa: BLE001 - non-fatal by design
        return result

    try:
        minx, miny, maxx, maxy = (float(v) for v in buildings_gdf.total_bounds)
        px = (maxx - minx) * padding_frac
        py = (maxy - miny) * padding_frac
        minx, miny, maxx, maxy = minx - px, miny - py, maxx + px, maxy + py
        west, south, east, north = transform_bounds(utm_crs_str, "EPSG:4326", minx, miny, maxx, maxy)
        bbox_wgs84 = (north, south, east, west)
    except Exception:  # noqa: BLE001 - non-fatal by design
        return result

    out_dir.mkdir(parents=True, exist_ok=True)

    roads_lines_utm: list = []

    try:
        raw_roads = _fetch_roads_gdf(bbox_wgs84)
        if raw_roads is not None and len(raw_roads):
            fid = _feature_id(raw_roads)
            features = _roads_to_features(raw_roads, utm_crs_str, fid)
            if features:
                path = out_dir / ROADS_NAME
                _write_geojson(path, features, utm_crs_str)
                result["roads"] = path
            roads_lines_utm = _roads_to_lines(raw_roads, utm_crs_str)
    except Exception:  # noqa: BLE001 - non-fatal by design (PLAN T23 §What)
        roads_lines_utm = []

    try:
        raw_green = _fetch_green_gdf(bbox_wgs84)
        if raw_green is not None and len(raw_green):
            fid = _feature_id(raw_green)
            features = _green_to_features(raw_green, utm_crs_str, fid)
            if features:
                path = out_dir / GREEN_NAME
                _write_geojson(path, features, utm_crs_str)
                result["green"] = path
    except Exception:  # noqa: BLE001 - non-fatal by design
        pass

    try:
        if roads_lines_utm:
            block_features = _blocks_to_features(roads_lines_utm)
            if block_features:
                path = out_dir / BLOCKS_NAME
                _write_geojson(path, block_features, utm_crs_str)
                result["blocks"] = path
    except Exception:  # noqa: BLE001 - non-fatal by design
        pass

    sidecar = {
        "crs": utm_crs_str,
        "extent_utm": [minx, miny, maxx, maxy],
        "attribution": _ATTRIBUTION,
        "provider": "osmnx",
        "tags": {"roads": _ROAD_TAGS, "green": _GREEN_TAGS},
    }
    sidecar_path = out_dir / SIDECAR_NAME
    sidecar_path.write_text(json.dumps(sidecar, sort_keys=True, indent=2), encoding="utf-8")
    result["sidecar"] = sidecar_path

    return result
