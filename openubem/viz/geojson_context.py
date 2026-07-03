"""Extruded-footprint LOD-0 placeholders for failed/absent buildings (T04).

A building whose IDF generation failed or was skipped has NO IDF, so the T03
CityJSON emitter cannot render it — yet the carried-forward
`plot_eui_choropleth` convention is "failed = hatched grey, never invisible".
This module emits a lightweight scene-space `FeatureCollection` of
footprint-extruded placeholders (one `Feature` per absent building) so the
viewer always has geometry to hatch.

These are EXPLICITLY non-faithful approximations (footprint × `levels × 3.5 m`,
not model geometry): every feature is tagged `is_approximation: true` and must
never be shown where IDF fidelity is claimed. Footprint source is the per-run
`01_buildings.gpkg` (real UTM coords) — never a live OSM re-fetch (PLAN §9.5).

Frame: features are emitted in the SAME scene frame as the T03 CityJSON
(UTM EPSG:32618 minus the shared `common_origin`), so placeholders sit correctly
among the real buildings. This is viewer scene-space, not RFC-7946 geographic
GeoJSON; the CRS + common_origin are recorded on the collection for recovery.
"""

from __future__ import annotations

import math

from shapely.geometry import mapping

_FLOOR_TO_FLOOR_M = 3.5
_REFERENCE_SYSTEM = "https://www.opengis.net/def/crs/EPSG/0/32618"


def _height_m(levels, height_m) -> float:
    """Placeholder extrusion height, mirroring the pipeline's floor logic."""
    try:
        if levels is not None and not (isinstance(levels, float) and math.isnan(levels)):
            return max(1, int(levels)) * _FLOOR_TO_FLOOR_M
    except (TypeError, ValueError):
        pass
    try:
        if height_m is not None and not (isinstance(height_m, float) and math.isnan(height_m)):
            return max(1, math.ceil(float(height_m) / _FLOOR_TO_FLOOR_M)) * _FLOOR_TO_FLOOR_M
    except (TypeError, ValueError):
        pass
    return _FLOOR_TO_FLOOR_M


def _translate_ring(coords, ox, oy):
    return [[float(x) - ox, float(y) - oy] for (x, y, *_) in coords]


def _footprint_to_scene(geom, ox, oy):
    """Translate a footprint polygon into scene-local metres (UTM − origin)."""
    gj = mapping(geom)
    if gj["type"] == "Polygon":
        gj = {"type": "Polygon",
              "coordinates": [_translate_ring(r, ox, oy) for r in gj["coordinates"]]}
    elif gj["type"] == "MultiPolygon":
        gj = {"type": "MultiPolygon",
              "coordinates": [[_translate_ring(r, ox, oy) for r in poly]
                              for poly in gj["coordinates"]]}
    return gj


def build_context_geojson(buildings_gdf, emitted_osm_ids, common_origin) -> dict:
    """Build the placeholder FeatureCollection for absent/failed buildings.

    Args:
        buildings_gdf: per-run `01_buildings.gpkg` (needs `osm_id`, geometry,
            `levels`, `height_m`).
        emitted_osm_ids: osm_ids that DO have real CityJSON geometry (T03) —
            these are excluded (they are never placeholders).
        common_origin: (ox, oy, oz) shared scene origin from T03.

    Returns:
        A GeoJSON FeatureCollection dict (scene-local metres). Deterministic:
        features sorted by `osm_id`.
    """
    emitted = set(str(o) for o in emitted_osm_ids)
    ox, oy = float(common_origin[0]), float(common_origin[1])

    has_levels = "levels" in buildings_gdf.columns
    has_height = "height_m" in buildings_gdf.columns

    records = []
    for i, osm_id in enumerate(buildings_gdf["osm_id"]):
        osm_id = str(osm_id)
        if osm_id in emitted:
            continue
        geom = buildings_gdf.geometry.iloc[i]
        if geom is None or geom.is_empty:
            continue
        levels = buildings_gdf["levels"].iloc[i] if has_levels else None
        height_m = buildings_gdf["height_m"].iloc[i] if has_height else None
        records.append((osm_id, geom, levels, height_m))

    records.sort(key=lambda t: t[0])

    features = [
        {
            "type": "Feature",
            "geometry": _footprint_to_scene(geom, ox, oy),
            "properties": {
                "osm_id": osm_id,
                "height": _height_m(levels, height_m),
                "is_approximation": True,
            },
        }
        for (osm_id, geom, levels, height_m) in records
    ]

    return {
        "type": "FeatureCollection",
        "openubem:frame": {
            "referenceSystem": _REFERENCE_SYSTEM,
            "common_origin": [ox, oy, 0.0],
            "note": "scene-local metres (UTM − common_origin); LOD-0 approximation",
        },
        "features": features,
    }
