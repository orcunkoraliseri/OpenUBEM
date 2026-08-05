"""Throwaway diagnostic (read-only): characterise building-to-building
footprint overlap in the layout_assign viewer scenes vs the real-auto control.

For each CityObject in an embedded CityJSON scene (extracted straight out of
the viewer HTML's <script id="scene-data"> block, same technique as
diagnose_blank_viewer.py), this:
  - builds an approximate 2D footprint polygon as the convex hull of every
    XY vertex belonging to that object's LOD-1 ("1", mass) geometry
    (walls+roof) -- a generic, shape-agnostic proxy that works the same way
    for both a real OSM footprint and a substituted DOE-prototype mass,
    without needing per-archetype special-casing. This can slightly
    OVER-estimate area/overlap for concave buildings (the hull fills in any
    notches), but the same method is applied uniformly to BOTH the
    layout_assign and the real_auto scene, so the two remain a fair,
    like-for-like comparison (a genuine overlap will show up in both if
    present in both; a hull-inflation artefact would show up in both too).
  - reports its axis-independent bounding rectangle (shapely
    minimum_rotated_rectangle) width/depth and aspect ratio -- this is what
    exposes the "long thin bar" shape-mismatch hypothesis.
  - reports its own footprint_centroid_utm attribute (the REAL building's
    centroid, always embedded regardless of resolution_mode -- see
    openubem/viz/cityjson_emitter.py build_cityjson()'s
    `"footprint_centroid_utm": [cx, cy]`) converted into the same
    scene-local frame as the vertices (subtract +common_origin_utm), so it
    can be compared directly against the computed polygon's own centroid --
    a mismatch here means the substituted mass is not even centred on the
    real building's centroid.
  - finds all pairwise polygon intersections (via shapely STRtree) with
    positive area above a small numerical-noise threshold, and reports the
    count of overlapping pairs, overlap-area distribution, and the percent
    of buildings involved in at least one overlap.

No files are modified. No pipeline module is imported (avoids touching
layout_assigner.py/builder.py while another executor edits them) except
`openubem.viz`, which is read here only for lightweight JSON parsing that is
already duplicated locally to avoid even that soft dependency.
"""
import json
import re
import sys
from pathlib import Path

import shapely
from shapely.geometry import MultiPoint
from shapely.strtree import STRtree

SCENE_RE = re.compile(
    r'<script id="scene-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def load_scene(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    m = SCENE_RE.search(text)
    if not m:
        raise RuntimeError(f"scene-data script tag not found in {html_path}")
    payload = m.group(1).replace("<\\/", "</")
    return json.loads(payload)


def building_footprints(cityjson: dict) -> dict:
    """key -> {"poly": shapely Polygon|None, "centroid_attr": (x,y)|None,
    "n_verts": int} in the scene-local (transform-applied, common-origin-
    subtracted-by-construction) frame the vertices array already uses."""
    scale = cityjson["transform"]["scale"]
    verts = cityjson["vertices"]
    ox, oy, _ = cityjson["metadata"]["+common_origin_utm"]
    out = {}
    for key, co in cityjson["CityObjects"].items():
        xy = []
        for g in co.get("geometry", []):
            if g.get("lod") != "1":
                continue
            for surf in g.get("boundaries", []):
                for ring in surf:
                    for vi in ring:
                        vx, vy, _ = verts[vi]
                        xy.append((vx * scale[0], vy * scale[1]))
        poly = None
        if len(xy) >= 3:
            hull = MultiPoint(xy).convex_hull
            if hull.geom_type == "Polygon" and hull.area > 0:
                poly = hull
        attrs = co.get("attributes", {})
        centroid_attr = attrs.get("footprint_centroid_utm")
        centroid_local = None
        if centroid_attr is not None:
            centroid_local = (centroid_attr[0] - ox, centroid_attr[1] - oy)
        out[key] = {"poly": poly, "centroid_attr_local": centroid_local, "n_verts": len(xy)}
    return out


def shape_stats(poly):
    if poly is None:
        return None
    mrr = poly.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)
    import math
    edges = [math.dist(coords[i], coords[i + 1]) for i in range(4)]
    w, d = sorted([edges[0], edges[1]])
    return {"width_m": w, "depth_m": d, "aspect_ratio": (d / w) if w > 0 else float("inf"),
            "hull_area_m2": poly.area, "centroid": (poly.centroid.x, poly.centroid.y)}


def overlap_report(fps: dict, area_threshold_m2: float = 0.5):
    keys = [k for k, v in fps.items() if v["poly"] is not None]
    polys = [fps[k]["poly"] for k in keys]
    if not polys:
        return {"n_buildings_with_poly": 0, "n_overlap_pairs": "not found",
                "pct_buildings_in_overlap": "not found", "overlap_areas": []}
    tree = STRtree(polys)
    involved = set()
    pairs_seen = set()
    overlap_areas = []
    for i, poly in enumerate(polys):
        cand_idx = tree.query(poly)
        for j in cand_idx:
            j = int(j)
            if j <= i:
                continue
            other = polys[j]
            if not poly.intersects(other):
                continue
            inter = poly.intersection(other)
            a = inter.area
            if a > area_threshold_m2:
                pair = (keys[i], keys[j])
                pairs_seen.add(pair)
                involved.add(keys[i]); involved.add(keys[j])
                overlap_areas.append(a)
    n = len(keys)
    pct = 100.0 * len(involved) / n if n else 0.0
    return {
        "n_buildings_with_poly": n,
        "n_overlap_pairs": len(pairs_seen),
        "n_buildings_involved": len(involved),
        "pct_buildings_in_overlap": pct,
        "overlap_areas": sorted(overlap_areas),
        "example_pairs": list(pairs_seen)[:10],
    }


def centroid_offset_report(fps: dict):
    """Distance between each building's computed hull centroid and its own
    footprint_centroid_utm attribute (converted to scene-local). Large,
    systematic offsets in layout_assign but not real_auto would show the
    substituted mass is not even anchored on the real building's centroid."""
    import math
    offsets = []
    for key, v in fps.items():
        if v["poly"] is None or v["centroid_attr_local"] is None:
            continue
        cx, cy = v["poly"].centroid.x, v["poly"].centroid.y
        ax, ay = v["centroid_attr_local"]
        offsets.append(math.dist((cx, cy), (ax, ay)))
    if not offsets:
        return {"n": "not found", "median_offset_m": "not found", "max_offset_m": "not found"}
    offsets.sort()
    n = len(offsets)
    return {
        "n": n,
        "median_offset_m": offsets[n // 2],
        "p90_offset_m": offsets[int(n * 0.9)],
        "max_offset_m": offsets[-1],
    }


def main(paths):
    for p in paths:
        path = Path(p)
        print(f"\n{'=' * 70}\n{path.name}\n{'=' * 70}")
        scene = load_scene(path)
        cj = scene["cityjson"]
        fps = building_footprints(cj)
        n_no_poly = sum(1 for v in fps.values() if v["poly"] is None)
        print(f"n_CityObjects = {len(fps)}, n with no computable LOD-1 hull polygon = {n_no_poly}")

        rep = overlap_report(fps)
        print(f"overlap pairs (hull-intersection area > 0.5 m2) = {rep['n_overlap_pairs']}")
        print(f"buildings involved in >=1 overlap = {rep.get('n_buildings_involved', 'not found')} "
              f"({rep['pct_buildings_in_overlap'] if isinstance(rep['pct_buildings_in_overlap'], str) else format(rep['pct_buildings_in_overlap'], '.2f')}% of {rep['n_buildings_with_poly']})")
        areas = rep["overlap_areas"]
        if areas:
            print(f"overlap area (m2): min={areas[0]:.2f} median={areas[len(areas)//2]:.2f} "
                  f"p90={areas[int(len(areas)*0.9)]:.2f} max={areas[-1]:.2f}")
            print(f"example overlapping pairs: {rep['example_pairs']}")
        else:
            print("overlap area (m2): not found")

        cent = centroid_offset_report(fps)
        print(f"hull-centroid vs footprint_centroid_utm offset (m): n={cent['n']}, "
              f"median={cent.get('median_offset_m')}, p90={cent.get('p90_offset_m')}, "
              f"max={cent.get('max_offset_m')}")

        yield fps


if __name__ == "__main__":
    list(main(sys.argv[1:]))
