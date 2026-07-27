"""Throwaway (read-only): check to full float precision whether different
buildings of the same archetype in a layout_assign scene share EXACTLY
identical substituted footprint dimensions (not just equal to 1 decimal),
and report the archetype-level distribution of substituted footprint area."""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import MultiPoint

SCENE_RE = re.compile(
    r'<script id="scene-data" type="application/json">(.*?)</script>', re.DOTALL)


def load_scene(html_path):
    text = Path(html_path).read_text(encoding="utf-8")
    m = SCENE_RE.search(text)
    return json.loads(m.group(1).replace("<\\/", "</"))


def main(path_str):
    scene = load_scene(path_str)
    cj = scene["cityjson"]
    scale = cj["transform"]["scale"]
    verts = cj["vertices"]

    by_arch_area = defaultdict(list)
    for key, co in cj["CityObjects"].items():
        arch = co.get("attributes", {}).get("archetype_id", "UNKNOWN")
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
        by_arch_area[arch].append(hull.area)

    print(f"=== {Path(path_str).name} ===")
    for arch, areas in sorted(by_arch_area.items(), key=lambda kv: -len(kv[1])):
        areas_sorted = sorted(areas)
        n = len(areas_sorted)
        distinct = sorted(set(round(a, 6) for a in areas_sorted))
        print(f"{arch:25s} n={n:5d}  min={areas_sorted[0]:.6f}  max={areas_sorted[-1]:.6f}  "
              f"n_distinct_values(6dp)={len(distinct)}")
        if len(distinct) <= 5:
            print(f"    distinct values: {distinct}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
