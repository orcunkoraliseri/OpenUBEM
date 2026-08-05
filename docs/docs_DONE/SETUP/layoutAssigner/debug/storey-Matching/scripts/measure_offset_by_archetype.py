"""Throwaway (read-only): break the hull-centroid vs footprint_centroid_utm
offset down by archetype_id, to check whether it is a fixed per-archetype
constant (as the near-identical median/p90 in measure_layout_assign_overlap.py
suggested) rather than random noise. Also reports named-building bbox/aspect
comparisons between the layout_assign and real_auto scenes for the same
osm_id, matched by CityObject key."""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import MultiPoint

SCENE_RE = re.compile(
    r'<script id="scene-data" type="application/json">(.*?)</script>', re.DOTALL)


def load_scene(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    m = SCENE_RE.search(text)
    payload = m.group(1).replace("<\\/", "</")
    return json.loads(payload)


def analyze(path_str):
    path = Path(path_str)
    scene = load_scene(path)
    cj = scene["cityjson"]
    scale = cj["transform"]["scale"]
    verts = cj["vertices"]
    ox, oy, _ = cj["metadata"]["+common_origin_utm"]

    by_arch = defaultdict(list)
    shapes = {}
    for key, co in cj["CityObjects"].items():
        attrs = co.get("attributes", {})
        arch = attrs.get("archetype_id", "UNKNOWN")
        xy = []
        for g in co.get("geometry", []):
            if g.get("lod") != "1":
                continue
            for surf in g.get("boundaries", []):
                for ring in surf:
                    for vi in ring:
                        vx, vy, _ = verts[vi]
                        xy.append((vx * scale[0], vy * scale[1]))
        if len(xy) < 3:
            continue
        hull = MultiPoint(xy).convex_hull
        if hull.geom_type != "Polygon":
            continue
        mrr = hull.minimum_rotated_rectangle
        coords = list(mrr.exterior.coords)
        edges = [math.dist(coords[i], coords[i + 1]) for i in range(4)]
        w, d = sorted([edges[0], edges[1]])
        shapes[key] = {"arch": arch, "w": w, "d": d, "area": hull.area,
                        "centroid": (hull.centroid.x, hull.centroid.y)}
        centroid_attr = attrs.get("footprint_centroid_utm")
        if centroid_attr is not None:
            ax, ay = centroid_attr[0] - ox, centroid_attr[1] - oy
            offset = math.dist((hull.centroid.x, hull.centroid.y), (ax, ay))
            by_arch[arch].append(offset)

    print(f"\n=== {path.name}: offset (m) by archetype_id ===")
    for arch, offs in sorted(by_arch.items(), key=lambda kv: -len(kv[1])):
        offs_sorted = sorted(offs)
        n = len(offs_sorted)
        print(f"  {arch:30s} n={n:5d}  median={offs_sorted[n//2]:8.3f}  "
              f"min={offs_sorted[0]:8.3f}  max={offs_sorted[-1]:8.3f}")
    return shapes


def compare_named(shapes_la_assign, shapes_la_auto, sample_keys):
    print("\n=== named-building bbox/aspect comparison (layout_assign vs real_auto) ===")
    for k in sample_keys:
        a = shapes_la_assign.get(k)
        b = shapes_la_auto.get(k)
        if a is None or b is None:
            print(f"  {k}: not found in one of the two scenes")
            continue
        print(f"  {k}  archetype={a['arch']}")
        print(f"    real_auto      : {b['w']:.1f} x {b['d']:.1f} m  aspect={b['d']/b['w']:.2f}  area(hull)={b['area']:.1f} m2")
        print(f"    layout_assign  : {a['w']:.1f} x {a['d']:.1f} m  aspect={a['d']/a['w']:.2f}  area(hull)={a['area']:.1f} m2")


if __name__ == "__main__":
    nyc_assign = analyze(sys.argv[1])
    nyc_auto = analyze(sys.argv[2])
    la_assign = analyze(sys.argv[3])
    la_auto = analyze(sys.argv[4])

    # Pick a handful of buildings shared between the assign/auto scenes for
    # the same city, biased toward the archetype the coordinator named.
    shared_la = [k for k in la_assign if la_assign[k]["arch"] == "MidriseApartment" and k in la_auto][:6]
    compare_named(la_assign, la_auto, shared_la)
    shared_nyc = [k for k in nyc_assign if k in nyc_auto][:6]
    compare_named(nyc_assign, nyc_auto, shared_nyc)
