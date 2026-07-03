"""Neighbourhood IDFs -> one CityJSON v2.0 city model (T03).

One `Building` CityObject per `osm_id`, each with two `MultiSurface` geometries:
`"lod": "1"` (walls + roof only, the navigation mass) and `"lod": "3"`
(walls + roof + `Window`/`Door` semantic surfaces nested under their parent
`WallSurface`). No triangulation at emit time — exact polygon vertex lists are
stored; the browser earcut-triangulates on load.

Positioning (MANAGER RULING 2026-07-02, Option A / true relative frame, PLAN
§9 ruling 8 + T03 §How): all buildings share ONE neighbourhood coordinate frame
so the file is a standards-valid city model, not 738 masses stacked at the
origin. Vertices are emitted as `IDF + footprint_centroid_UTM − common_origin`
(`collect_geometry(recentre=False)` gives the exact builder-local frame
`IDF = UTM − footprint_centroid`; `footprint_centroid_UTM` is read back from the
per-run `01_buildings.gpkg`, EPSG:32618). `common_origin` keeps metres small and
WebGL-float32-friendly. Absolute lat/lon geo-referencing stays post-MVP (V07),
recoverable exactly as `UTM = vertex + common_origin`.

Determinism (T03 test d / CP-Reproducibility): buildings iterated sorted by
`osm_id`, surfaces sorted by `surf_name`, vertices stored as integer millimetres
(CityJSON canonical `transform`), `json.dump(sort_keys=True)` at write time —
byte-identical across runs on identical input.
"""

from __future__ import annotations

import json
import math

from openubem.viz.geometry_extract import collect_geometry, parse_idf

# LOD-1 mass = opaque exterior shell (walls + roof). Floors/interior/slab are
# not part of either LOD per PLAN §0 + T03 §What (walls+roof / +windows/doors).
_LOD1_CATEGORIES = ("wall", "roof")
_SUBSURFACE_CATEGORIES = ("window", "door")

_SEMANTIC_TYPE = {
    "wall": "WallSurface",
    "roof": "RoofSurface",
    "window": "Window",
    "door": "Door",
}

# Millimetre integer vertices via the CityJSON transform: canonical, compact,
# perfectly deterministic, and 0.5 mm max rounding — far inside CP-Geometry's
# 1 cm tolerance.
_SCALE = 0.001
_REFERENCE_SYSTEM = "https://www.opengis.net/def/crs/EPSG/0/32618"

VIEWER_SPEC_VERSION = "0.1.0"
LOD_SPEC_VERSION = "0.1.0"


def footprint_centroids_utm(buildings_gdf) -> dict[str, tuple[float, float]]:
    """Return {osm_id: (cx, cy)} footprint centroids in the run's UTM CRS.

    This is the exact inverse of `footprint.translate_to_origin`'s centroid
    subtraction (footprint.py:53) — the offset that maps each builder-local IDF
    frame back to shared UTM.
    """
    out: dict[str, tuple[float, float]] = {}
    for osm_id, geom in zip(buildings_gdf["osm_id"], buildings_gdf.geometry):
        if geom is None or geom.is_empty:
            continue
        c = geom.centroid
        out[str(osm_id)] = (float(c.x), float(c.y))
    return out


def _window_parent_map(idf_data) -> dict[str, str]:
    """Map each sub-surface's own name -> its parent wall name, from the IDF.

    collect_geometry does not carry the parent-wall linkage on subwin records,
    so it is re-derived here from the authoritative IDF fields
    (FenestrationSurface field[3] / Window field[2] / Door field[2]).
    """
    m: dict[str, str] = {}
    for fen in idf_data.get("FENESTRATIONSURFACE:DETAILED", []):
        if len(fen) >= 4 and fen[0].strip() and fen[3].strip():
            m[fen[0].strip()] = fen[3].strip()
    for win in idf_data.get("WINDOW", []):
        if len(win) >= 3 and win[0].strip() and win[2].strip():
            m[win[0].strip()] = win[2].strip()
    for door in idf_data.get("DOOR", []):
        if len(door) >= 3 and door[0].strip() and door[2].strip():
            m[door[0].strip()] = door[2].strip()
    return m


def build_cityjson(manifest_df, buildings_gdf) -> dict:
    """Build the neighbourhood CityJSON dict (geometry only; attributes T05/T06).

    Args:
        manifest_df: Step-3 manifest (needs `osm_id`, `idf_path`); only rows
            whose `osm_id` has a footprint centroid are emitted.
        buildings_gdf: per-run `01_buildings.gpkg` (needs `osm_id` + geometry in
            a projected UTM CRS, e.g. EPSG:32618).

    Returns:
        A CityJSON v2.0 dict. `metadata` carries `referenceSystem` +
        `+common_origin_utm`; T07 augments it with the reproducibility block.
    """
    centroids = footprint_centroids_utm(buildings_gdf)

    rows = [r for r in manifest_df.itertuples(index=False)
            if str(r.osm_id) in centroids]
    rows.sort(key=lambda r: str(r.osm_id))
    if not rows:
        raise ValueError("No manifest rows with a matching footprint centroid.")

    all_cx = [centroids[str(r.osm_id)][0] for r in rows]
    all_cy = [centroids[str(r.osm_id)][1] for r in rows]
    ox = float(math.floor(min(all_cx)))
    oy = float(math.floor(min(all_cy)))

    vertices: list[list[int]] = []
    vindex: dict[tuple[int, int, int], int] = {}

    def add_vertex(mx: float, my: float, mz: float) -> int:
        key = (int(round(mx * 1000.0)), int(round(my * 1000.0)),
               int(round(mz * 1000.0)))
        idx = vindex.get(key)
        if idx is None:
            idx = len(vertices)
            vindex[key] = idx
            vertices.append([key[0], key[1], key[2]])
        return idx

    city_objects: dict[str, dict] = {}

    for r in rows:
        osm_id = str(r.osm_id)
        cx, cy = centroids[osm_id]
        g = collect_geometry(r.idf_path, recentre=False)
        parent_map = _window_parent_map(parse_idf(r.idf_path))

        def to_surface(verts) -> list[list[int]]:
            ring = [add_vertex(x + cx - ox, y + cy - oy, z)
                    for (x, y, z) in verts]
            return [ring]

        opaque = sorted(
            ((sn, cat, verts) for (_, _, cat, verts, sn) in g["faces"]
             if cat in _LOD1_CATEGORIES),
            key=lambda t: t[0],
        )
        subs = sorted(
            ((sn, cat, verts) for (_, _, cat, verts, sn) in g["subwin"]
             if cat in _SUBSURFACE_CATEGORIES),
            key=lambda t: t[0],
        )

        # LOD-1: opaque shell only.
        lod1_boundaries, lod1_surfaces, lod1_values = [], [], []
        for i, (sn, cat, verts) in enumerate(opaque):
            lod1_boundaries.append(to_surface(verts))
            lod1_surfaces.append({"type": _SEMANTIC_TYPE[cat], "surf_name": sn})
            lod1_values.append(i)

        # LOD-3: opaque shell + sub-surfaces nested under their parent wall.
        lod3_boundaries, lod3_surfaces, lod3_values = [], [], []
        name_to_idx: dict[str, int] = {}
        for i, (sn, cat, verts) in enumerate(opaque):
            lod3_boundaries.append(to_surface(verts))
            lod3_surfaces.append({"type": _SEMANTIC_TYPE[cat], "surf_name": sn})
            lod3_values.append(i)
            name_to_idx[sn] = i
        for (sn, cat, verts) in subs:
            si = len(lod3_surfaces)
            surf = {"type": _SEMANTIC_TYPE[cat], "surf_name": sn}
            parent_name = parent_map.get(sn)
            if parent_name is not None and parent_name in name_to_idx:
                pidx = name_to_idx[parent_name]
                surf["parent"] = pidx
                lod3_surfaces[pidx].setdefault("children", []).append(si)
            lod3_boundaries.append(to_surface(verts))
            lod3_surfaces.append(surf)
            lod3_values.append(si)

        city_objects[osm_id] = {
            "type": "Building",
            "attributes": {"footprint_centroid_utm": [cx, cy]},
            "geometry": [
                {"type": "MultiSurface", "lod": "1",
                 "boundaries": lod1_boundaries,
                 "semantics": {"surfaces": lod1_surfaces, "values": lod1_values}},
                {"type": "MultiSurface", "lod": "3",
                 "boundaries": lod3_boundaries,
                 "semantics": {"surfaces": lod3_surfaces, "values": lod3_values}},
            ],
        }

    return {
        "type": "CityJSON",
        "version": "2.0",
        "transform": {"scale": [_SCALE, _SCALE, _SCALE],
                      "translate": [0.0, 0.0, 0.0]},
        "metadata": {
            "referenceSystem": _REFERENCE_SYSTEM,
            "+common_origin_utm": [ox, oy, 0.0],
        },
        "CityObjects": city_objects,
        "vertices": vertices,
    }


def dumps(cityjson: dict) -> str:
    """Deterministic serialization: sorted keys, compact separators."""
    return json.dumps(cityjson, sort_keys=True, separators=(",", ":"))
