"""Throwaway diagnostic: extract embedded CityJSON scene from a viewer HTML
and report vertex bounding box + basic geometry sanity stats. Read-only,
does not modify the HTML files. Written to debug the storey-Matching
blank-viewer report (layoutAssigner arc)."""
import json
import re
import sys
from pathlib import Path

SCENE_RE = re.compile(
    r'<script id="scene-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)


def load_scene(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    m = SCENE_RE.search(text)
    if not m:
        raise RuntimeError(f"scene-data script tag not found in {html_path}")
    payload = m.group(1)
    # reverse the </ -> <\/ escape done by _scene_json
    payload = payload.replace("<\\/", "</")
    return json.loads(payload)


def analyze(path_str: str):
    path = Path(path_str)
    print(f"\n=== {path.name} ({path.stat().st_size:,} bytes) ===")
    scene = load_scene(path)
    cj = scene["cityjson"]
    verts = cj["vertices"]
    n = len(verts)
    print(f"n_vertices = {n}")
    if n == 0:
        print("vertices array EMPTY (not found)")
    else:
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        scale = cj["transform"]["scale"]
        print(f"transform.scale = {scale}, translate = {cj['transform']['translate']}")
        print(f"raw int bbox: x[{min(xs)}, {max(xs)}]  y[{min(ys)}, {max(ys)}]  z[{min(zs)}, {max(zs)}]")
        print(f"metres bbox:  x[{min(xs)*scale[0]:.2f}, {max(xs)*scale[0]:.2f}]  "
              f"y[{min(ys)*scale[1]:.2f}, {max(ys)*scale[1]:.2f}]  "
              f"z[{min(zs)*scale[2]:.2f}, {max(zs)*scale[2]:.2f}]")

    cos = cj["CityObjects"]
    n_buildings = len(cos)
    print(f"n_CityObjects (buildings) = {n_buildings}")

    n_geoms = 0
    n_lod1_boundaries = 0
    n_lod3_boundaries = 0
    n_empty_lod1 = 0
    n_empty_lod3 = 0
    degenerate_rings = 0
    lod_values_seen = set()
    example_bad = []
    for key, co in cos.items():
        geoms = co.get("geometry", [])
        n_geoms += len(geoms)
        for g in geoms:
            lod_values_seen.add(g.get("lod"))
            b = g.get("boundaries", [])
            if g.get("lod") == "1":
                n_lod1_boundaries += len(b)
                if len(b) == 0:
                    n_empty_lod1 += 1
            elif g.get("lod") == "3":
                n_lod3_boundaries += len(b)
                if len(b) == 0:
                    n_empty_lod3 += 1
            for surf in b:
                for ring in surf:
                    if len(ring) < 3:
                        degenerate_rings += 1
                        if len(example_bad) < 5:
                            example_bad.append((key, g.get("lod"), ring))

    print(f"n_geometry_entries total = {n_geoms}")
    print(f"lod values seen = {sorted(str(x) for x in lod_values_seen)}")
    print(f"lod1: total boundary surfaces = {n_lod1_boundaries}, buildings with EMPTY lod1 boundaries = {n_empty_lod1}")
    print(f"lod3: total boundary surfaces = {n_lod3_boundaries}, buildings with EMPTY lod3 boundaries = {n_empty_lod3}")
    print(f"degenerate rings (<3 verts) = {degenerate_rings}")
    if example_bad:
        print(f"example degenerate: {example_bad}")

    # attribute presence check
    n_with_resolution_mode = sum(1 for co in cos.values() if "resolution_mode" in co.get("attributes", {}))
    n_with_zoning_strategy = sum(1 for co in cos.values() if "zoning_strategy" in co.get("attributes", {}))
    n_with_total_eui = sum(1 for co in cos.values() if "total_eui_kwh_m2" in co.get("attributes", {}))
    print(f"buildings with resolution_mode attr = {n_with_resolution_mode}")
    print(f"buildings with zoning_strategy attr = {n_with_zoning_strategy}")
    print(f"buildings with total_eui_kwh_m2 attr = {n_with_total_eui}")

    # sample one building's geometry structure
    first_key = next(iter(cos))
    print(f"\nsample building key = {first_key!r}")
    print(json.dumps(cos[first_key], indent=None)[:800])

    return scene


if __name__ == "__main__":
    for p in sys.argv[1:]:
        try:
            analyze(p)
        except Exception as e:
            print(f"\n=== {p} ===\nFAILED TO ANALYZE: {type(e).__name__}: {e}")
