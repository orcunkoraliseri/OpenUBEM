from __future__ import annotations

import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from geomeppy import IDF as GeomIDF
from shapely.geometry import MultiPolygon, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem import config
from openubem.idf.surfaces import find_mismatched_interzone_pairs

EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
G = EV / "geometry_24_2026-10-10"
NEAR_DUP_M = 0.005
COLLINEAR_DEG = 0.1
TURN_DEG = 0.001
GPKG = {"ES-MAD-BERRUGUETE": "ES-MAD-BERRUGUETE", "IT-BOL-GALVANI2": "IT-BOL-GALVANI2"}

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except Exception:
    pass


def ring_stats(coords):
    pts = list(coords)
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    n = len(pts)
    seg = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]
    collinear = 0
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        a = (p1[0] - p0[0], p1[1] - p0[1])
        b = (p2[0] - p1[0], p2[1] - p1[1])
        la, lb = math.hypot(*a), math.hypot(*b)
        if la == 0 or lb == 0:
            continue
        c = (a[0] * b[0] + a[1] * b[1]) / (la * lb)
        turn = math.degrees(math.acos(max(-1.0, min(1.0, c))))
        if turn < TURN_DEG:
            collinear += 1
    repeated_exact = sum(1 for i in range(n) if pts[i] == pts[(i + 1) % n])
    repeated_1mm = sum(1 for s in seg if s < 0.001)
    near_dup = sum(1 for s in seg if s < NEAR_DUP_M)
    return {"n": n, "collinear": collinear, "shortest": min(seg) if seg else float("nan"),
            "repeated_exact": repeated_exact, "repeated_1mm": repeated_1mm, "near_dup": near_dup}


def footprint_row(geom):
    parts = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    holes = sum(len(p.interiors) for p in parts)
    rs = [ring_stats(p.exterior.coords) for p in parts]
    for p in parts:
        rs += [ring_stats(r.coords) for r in p.interiors]
    xs = [c for p in parts for c in p.exterior.coords]
    ax = [abs(v) for c in xs for v in c]
    return {
        "fp_parts": len(parts), "fp_interior_rings": holes, "fp_ring_vertices": sum(r["n"] for r in rs[:len(parts)]),
        "fp_collinear_vertices": sum(r["collinear"] for r in rs), "fp_shortest_segment_m": min(r["shortest"] for r in rs),
        "fp_repeated_point_exact": sum(r["repeated_exact"] for r in rs), "fp_repeated_point_1mm": sum(r["repeated_1mm"] for r in rs),
        "fp_near_dup_5mm": sum(r["near_dup"] for r in rs), "fp_min_abs_coord": min(ax), "fp_max_abs_coord": max(ax),
        "fp_area_m2": geom.area, "fp_valid": bool(geom.is_valid),
    }


def poly_area3(coords):
    ax = ay = az = 0.0
    n = len(coords)
    for i in range(n):
        x1, y1, z1 = coords[i]
        x2, y2, z2 = coords[(i + 1) % n]
        ax += (y1 - y2) * (z1 + z2)
        ay += (z1 - z2) * (x1 + x2)
        az += (x1 - x2) * (y1 + y2)
    return 0.5 * math.sqrt(ax * ax + ay * ay + az * az)


def effective_len(coords):
    pts = [tuple(c) for c in coords]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        for i in range(n):
            p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            v1 = [a - b for a, b in zip(p0, p1)]
            v2 = [a - b for a, b in zip(p2, p1)]
            l1, l2 = math.sqrt(sum(c * c for c in v1)), math.sqrt(sum(c * c for c in v2))
            drop = l1 < NEAR_DUP_M or l2 < NEAR_DUP_M
            if not drop and l1 > 0 and l2 > 0:
                cosv = max(-1.0, min(1.0, sum(a * b for a, b in zip(v1, v2)) / (l1 * l2)))
                drop = math.degrees(math.acos(-cosv)) < COLLINEAR_DEG
            if drop:
                del pts[i]
                changed = True
                break
    return len(pts)


def idf_row(path: Path, prefix: str):
    idf = GeomIDF(str(path))
    bsd = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    by = {str(s.Name).upper(): s for s in bsd}
    raw_mis = find_mismatched_interzone_pairs(idf)
    pairs = set()
    for s in bsd:
        o = str(s.Outside_Boundary_Condition_Object or "").upper()
        if o and o in by:
            pairs.add(tuple(sorted((str(s.Name).upper(), o))))
    eff_diff = 0
    nd_surfaces = 0
    for a, b in pairs:
        ea, eb = effective_len(by[a].coords), effective_len(by[b].coords)
        if ea != eb:
            eff_diff += 1
        if ea != len(by[a].coords) or eb != len(by[b].coords):
            nd_surfaces += 1
    slivers = sum(1 for s in bsd if poly_area3(list(s.coords)) < 1e-6)
    rep = 0
    mags = []
    for s in bsd:
        c = list(s.coords)
        n = len(c)
        rep += sum(1 for i in range(n) if tuple(c[i]) == tuple(c[(i + 1) % n]))
        mags += [abs(v) for p in c for v in p[:2]]
    return {
        f"{prefix}_surfaces": len(bsd), f"{prefix}_zones": len(idf.idfobjects["ZONE"]), f"{prefix}_interzone_pairs": len(pairs),
        f"{prefix}_raw_count_mismatch_pairs": len(raw_mis), f"{prefix}_effective_count_mismatch_pairs": eff_diff,
        f"{prefix}_pairs_with_neardup_or_collinear": nd_surfaces, f"{prefix}_surfaces_lt_1e-6_m2": slivers,
        f"{prefix}_repeated_vertices": rep, f"{prefix}_min_abs_xy": min(mags) if mags else float("nan"),
        f"{prefix}_max_abs_xy": max(mags) if mags else float("nan"),
    }


def main():
    inv = pd.read_csv(G / "geometry_24_inventory.csv", dtype=str)
    gp = {d: gpd.read_file(ROOT / "openubem" / "outputs" / "eu02" / d / "02_residential_manifest.gpkg").set_index("osm_id") for d in GPKG}
    rows = []
    for _, r in inv.iterrows():
        d, b = r["district"], r["building_id"]
        out = {"district": d, "building_id": b, "stem": r["stem"]}
        out.update(footprint_row(gp[d].loc[b].geometry))
        out.update(idf_row(ROOT / r["idf_win_2026_10_06"], "ours"))
        fx = r["idf_fixed_home_package"]
        if isinstance(fx, str) and fx:
            out.update(idf_row(Path(fx), "fixed"))
        if d.startswith("IT"):
            out.update(idf_row(G / "4J_bologna" / "idf_f000" / f"it__{b}__caseA__f000.idf", "j4"))
        rows.append(out)
        print(d, b, "done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(G / "footprint_forensics.csv", index=False)
    print(len(df))


if __name__ == "__main__":
    main()
