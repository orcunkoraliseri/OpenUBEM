"""Throwaway (read-only): measure the RAW (S=1, unscaled) baseline prototype's
own footprint bounding box directly from its IDF file, using the exact same
extraction path (openubem.viz.geometry_extract.collect_geometry) the viewer
pipeline uses -- so it is an apples-to-apples comparison against the
convex-hull bbox measured from the embedded viewer scenes.

Read-only: only imports openubem.viz.geometry_extract (a READ path, not
layout_assigner.py/builder.py). Does not write anything.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")))

from shapely.geometry import MultiPoint

from openubem.viz.geometry_extract import collect_geometry

_LOD1 = ("wall", "roof")


def main(idf_path):
    g = collect_geometry(idf_path, recentre=False)
    xy = []
    for (_, _, cat, verts, _sn) in g["faces"]:
        if cat in _LOD1:
            for (x, y, z) in verts:
                xy.append((x, y))
    print(f"{Path(idf_path).name}")
    print(f"  n_wall+roof faces = {sum(1 for f in g['faces'] if f[2] in _LOD1)}")
    print(f"  n_xy_verts = {len(xy)}")
    if len(xy) < 3:
        print("  not found: fewer than 3 XY vertices")
        return
    hull = MultiPoint(xy).convex_hull
    mrr = hull.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)
    import math
    edges = [math.dist(coords[i], coords[i + 1]) for i in range(4)]
    w, d = sorted([edges[0], edges[1]])
    xs = [p[0] for p in xy]; ys = [p[1] for p in xy]
    print(f"  raw bbox X=[{min(xs):.2f},{max(xs):.2f}]  Y=[{min(ys):.2f},{max(ys):.2f}]")
    print(f"  min-rotated-rect: {w:.3f} x {d:.3f} m, aspect={d/w:.3f}")
    print(f"  convex hull area = {hull.area:.3f} m2")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)

# quick centroid-distance-from-origin check (appended)
def _centroid_check(idf_path):
    g = collect_geometry(idf_path, recentre=False)
    xy = [(x, y) for (_, _, cat, verts, _sn) in g["faces"] if cat in _LOD1 for (x, y, z) in verts]
    hull = MultiPoint(xy).convex_hull
    import math
    d = math.dist((hull.centroid.x, hull.centroid.y), (0, 0))
    print(f"  centroid={hull.centroid.x:.3f},{hull.centroid.y:.3f}  dist_from_local_origin(0,0)={d:.3f} m")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        _centroid_check(p)
