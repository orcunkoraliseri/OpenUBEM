"""B08a (measurement only, read-only): diagnose the residual cross-building
placement defect after B05.

Three questions (plan PLAN_storey-matching_implementation.md, B08a):
  1. Anchor  -- is offset ~= ||local_centroid|| of the building's own scaled
     prototype (envelope anchored at local (0,0), not the real centroid)?
  2. Layer   -- does the offset already exist in the emitted IDF, or is it
     introduced by the viewer path (geometry_extract.py / cityjson_emitter.py)?
  3. Physics -- does anything downstream consume inter-building placement?
     (answered by grep, not by this script -- see progress-log entry)

Method for Q1/Q2 (independent of openubem/viz's own placement code, so a
match is real evidence, not a tautology):
  - `predicted_offset`: parsed straight from each building's own real, saved,
    post-B05 IDF (`BuildingIDF.build()` output from the B05f run -- current
    HEAD, no changes to layout_assigner.py/builder.py since that run, see
    progress-log entry) using `openubem.viz.geometry_extract.collect_geometry`
    (a READ-only import, not an edit -- same function A4/B05d/measure_raw_
    baseline_footprint.py already used for this exact purpose). LOD-1
    (wall+roof) face vertices in the *local* (un-recentred, un-placed) frame;
    hull centroid distance from local (0,0).
  - `measured_offset`: parsed from the CURRENT (post-B05) viewer HTML scene
    the pipeline already emitted (`openubem/outputs/{cell}_layout_assign_
    viewer.html`, built 2026-07-26 12:39-12:51 from the same real pipeline
    run) -- world-frame hull centroid vs the building's own
    `footprint_centroid_utm` attribute, exactly `measure_offset_by_
    archetype.py`'s method, but keeping every building's own row instead of
    only the archetype aggregate.
  - `planar_k` (diagnostic column): predicted_offset / raw_offset_for_that_
    archetype, where raw_offset is the SAME hull-centroid-from-origin measure
    applied to the untouched S=1 baseline IDF on disk. Isotropic scaling
    around a fixed local origin (no rotation, no re-centring -- confirmed by
    reading scale_baseline_idf() and geometry_extract.py) means this ratio
    IS planar_scale_factor, to floating-point precision, without having to
    re-derive it from the real_area/baseline_area pipeline inputs.

No file under openubem/ is modified. No files under openubem/viz/ are
modified (import only).
"""
import csv
import math
import re
import json
from pathlib import Path

import pandas as pd
from shapely.geometry import MultiPoint

import sys
sys.path.insert(0, str(Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")))

from openubem.viz.geometry_extract import collect_geometry
from openubem.geometry.layout_assigner import ARCHETYPE_IDF_MAP, get_registry

_LOD1 = ("wall", "roof")

WORK_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_b05f_work\after_B05")
VIEWER_HTML = {
    "nyc_suburban": Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\nyc_suburban_layout_assign_viewer.html"),
    "la_suburban": Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\la_suburban_layout_assign_viewer.html"),
}
OUT_CSV = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\simulation-Resolution\layoutAssigner\debug\storey-Matching\results\b08a_placement_diagnosis.csv")

SCENE_RE = re.compile(
    r'<script id="scene-data" type="application/json">(.*?)</script>', re.DOTALL)


def local_hull_centroid(idf_path):
    g = collect_geometry(str(idf_path), recentre=False)
    xy = [(x, y) for (_, _, cat, verts, _sn) in g["faces"] if cat in _LOD1
          for (x, y, z) in verts]
    if len(xy) < 3:
        return None
    hull = MultiPoint(xy).convex_hull
    if hull.geom_type != "Polygon":
        return None
    return hull.centroid.x, hull.centroid.y


def load_scene(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    m = SCENE_RE.search(text)
    payload = m.group(1).replace("<\\/", "</")
    return json.loads(payload)


def measured_offsets(html_path: Path) -> dict:
    """osm_id -> (archetype_id, measured_offset_m, world_hull_centroid_xy)."""
    scene = load_scene(html_path)
    cj = scene["cityjson"]
    scale = cj["transform"]["scale"]
    verts = cj["vertices"]
    ox, oy, _ = cj["metadata"]["+common_origin_utm"]
    out = {}
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
        centroid_attr = attrs.get("footprint_centroid_utm")
        if centroid_attr is None:
            continue
        ax, ay = centroid_attr[0] - ox, centroid_attr[1] - oy
        offset = math.dist((hull.centroid.x, hull.centroid.y), (ax, ay))
        out[key] = (arch, offset)
    return out


def main():
    reg = get_registry()

    # ---- raw (S=1) per-archetype local hull centroid, offset from (0,0) ----
    archetypes_needed = set()
    manifests = {}
    for cell in ("nyc_suburban", "la_suburban"):
        mpath = WORK_ROOT / cell / "step3_layout_assign" / "03_manifest.parquet"
        df = pd.read_parquet(mpath)
        manifests[cell] = df
        archetypes_needed |= set(df["archetype_id"].unique())

    raw_offset = {}
    raw_missing = []
    for arch in sorted(archetypes_needed):
        fname = ARCHETYPE_IDF_MAP.get(arch)
        if fname is None:
            continue  # Courthouse / OpenUBEMUnknown / other D5 no-baseline archetypes
        raw_path = reg.base_dir / fname
        if not raw_path.exists():
            raw_missing.append(arch)
            continue
        c = local_hull_centroid(raw_path)
        if c is None:
            raw_missing.append(arch)
            continue
        raw_offset[arch] = math.dist(c, (0.0, 0.0))

    print("Raw (S=1) per-archetype local hull-centroid offset from (0,0):")
    for arch, off in sorted(raw_offset.items(), key=lambda kv: -kv[1]):
        print(f"  {arch:25s} {off:8.3f} m   file={ARCHETYPE_IDF_MAP[arch]}")
    if raw_missing:
        print("Archetypes with no baseline file / unmeasurable raw offset:", raw_missing)

    # ---- per-building predicted offset (from real generated IDFs) ----------
    rows = []
    skipped_no_baseline = 0
    skipped_no_idf = 0
    for cell, df in manifests.items():
        for _, r in df.iterrows():
            arch = r["archetype_id"]
            if arch not in ARCHETYPE_IDF_MAP:
                skipped_no_baseline += 1
                continue
            idf_path = Path(r["idf_path"])
            if not idf_path.exists():
                skipped_no_idf += 1
                continue
            c = local_hull_centroid(idf_path)
            if c is None:
                skipped_no_idf += 1
                continue
            lcx, lcy = c
            predicted = math.dist((lcx, lcy), (0.0, 0.0))
            raw_off = raw_offset.get(arch)
            planar_k = predicted / raw_off if raw_off else float("nan")
            rows.append({
                "cell": cell,
                "osm_id": r["osm_id"],
                "archetype": arch,
                "planar_k": planar_k,
                "local_centroid_x": lcx,
                "local_centroid_y": lcy,
                "predicted_offset": predicted,
            })

    print(f"\nBuilt predicted_offset for {len(rows)} buildings "
          f"(skipped: {skipped_no_baseline} no-baseline/D5-fallback archetype, "
          f"{skipped_no_idf} missing/unparseable idf).")

    # ---- measured offset from the current post-B05 viewer scenes -----------
    meas = {}
    for cell, html_path in VIEWER_HTML.items():
        m = measured_offsets(html_path)
        print(f"{cell}: measured_offsets parsed for {len(m)} CityObjects from {html_path.name}")
        meas[cell] = m

    matched = 0
    unmatched = 0
    for row in rows:
        m = meas[row["cell"]].get(row["osm_id"])
        if m is None:
            row["measured_offset"] = ""
            unmatched += 1
            continue
        m_arch, m_off = m
        row["measured_offset"] = m_off
        if m_arch != row["archetype"]:
            row["archetype_mismatch"] = m_arch
        matched += 1

    print(f"Matched predicted<->measured for {matched} buildings, {unmatched} unmatched.")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["osm_id", "cell", "archetype", "planar_k", "local_centroid_x",
                  "local_centroid_y", "predicted_offset", "measured_offset"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"\nWrote {OUT_CSV} ({len(rows)} rows)")

    # ---- per-archetype fit ---------------------------------------------
    by_arch = {}
    for row in rows:
        if row["measured_offset"] == "":
            continue
        by_arch.setdefault(row["archetype"], []).append(
            (row["predicted_offset"], row["measured_offset"]))

    print("\n=== per-archetype fit: predicted vs measured offset (m) ===")
    print(f"{'archetype':25s} {'n':>5s} {'med_pred':>10s} {'med_meas':>10s} "
          f"{'med_resid':>10s} {'med_ratio':>10s}")
    for arch, pairs in sorted(by_arch.items(), key=lambda kv: -len(kv[1])):
        preds = sorted(p for p, _ in pairs)
        meass = sorted(m for _, m in pairs)
        resids = sorted(m - p for p, m in pairs)
        ratios = sorted(m / p for p, m in pairs if p > 1e-9)
        n = len(pairs)
        med = lambda a: a[len(a) // 2] if a else float("nan")
        print(f"{arch:25s} {n:5d} {med(preds):10.3f} {med(meass):10.3f} "
              f"{med(resids):10.3f} {med(ratios):10.3f}")


if __name__ == "__main__":
    main()
