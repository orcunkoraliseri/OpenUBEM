import glob
import json
import math
import os
import sys
from multiprocessing import Pool

import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = "C:/Users/o_iseri/Desktop/OpenUBEM/"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

EVID = ROOT + "openubem/outputs/eu_evidence/EU-11/"
VIEW = ROOT + "docs/docs_DONE/SETUP/europeanLocations/outputs_3D/"
OUT = EVID + "division_residual_2026-09-29/"
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
WING_TOL_M = 0.10
BOUNDARY_TOL_M = 0.10
TURN = -0.17

CLASS_ORDER = [
    "OK", "S1_one_flat_per_floor_by_data", "U1_cut_lost_at_idf_write", "U2_more_than_12_flats",
    "U3_cut_breaks_hard_rule_C4_C5", "U4_other_box", "V1_divided_shape_rule_broken",
    "V2_divided_unbalanced", "V3_divided_wrapped_flat", "X_no_sidecar",
]


def reflex_vertices(poly):
    poly = orient(poly, 1.0)
    out = []
    for ring in [poly.exterior] + list(poly.interiors):
        c = list(ring.coords)[:-1]
        n = len(c)
        for i in range(n):
            a, b, d = c[i - 1], c[i], c[(i + 1) % n]
            la = math.hypot(b[0] - a[0], b[1] - a[1])
            lb = math.hypot(d[0] - b[0], d[1] - b[1])
            if la < 0.3 or lb < 0.3:
                continue
            cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
            if cr / (la * lb) < TURN:
                out.append(Point(b))
    return out


def zone_corners(z, fb, plate_reflex):
    c = list(z.exterior.coords)[:-1]
    if not Polygon(c).exterior.is_ccw:
        c = c[::-1]
    n = len(c)

    def interior_edge(j):
        p, q = c[j % n], c[(j + 1) % n]
        return fb.distance(Point((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)) > 0.05

    def near_reflex(pt):
        p = Point(pt)
        return any(p.distance(r) <= WING_TOL_M for r in plate_reflex)

    cut_made = 0
    wing = 0
    for i in range(n):
        a, b, d = c[i - 1], c[i], c[(i + 1) % n]
        la = math.hypot(b[0] - a[0], b[1] - a[1])
        lb = math.hypot(d[0] - b[0], d[1] - b[1])
        if la < 0.3 or lb < 0.3:
            continue
        cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
        if not (cr / (la * lb) < TURN and fb.distance(Point(b)) > BOUNDARY_TOL_M):
            continue
        cut_made += 1
        f = i
        guard = 0
        while interior_edge(f) and guard < n:
            f += 1
            guard += 1
        g = i
        guard = 0
        while interior_edge(g - 1) and guard < n:
            g -= 1
            guard += 1
        if near_reflex(c[f % n]) or near_reflex(c[g % n]):
            wing += 1
    return cut_made, wing


def analyse_sidecar(j):
    sp = 1.0
    zone_max = 0
    max_v = 0
    c13 = 0
    wings = 0
    seen = {}
    for f in j["floors"]:
        zs = [Polygon(z["coords_m"]).buffer(0) for z in f["zones"]]
        zs = [z for z in zs if not z.is_empty]
        if len(zs) < 2:
            continue
        areas = [z.area for z in zs]
        sp = min(sp, min(areas) / max(areas))
        key = tuple(sorted(round(a, 3) for a in areas)) + (len(zs),)
        if key in seen:
            fc = seen[key]
        else:
            union = unary_union(zs).buffer(0.01).buffer(-0.01)
            fb = union.boundary
            plate_reflex = []
            sharp = unary_union(zs).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
            for g in getattr(sharp, "geoms", [sharp]):
                if g.geom_type == "Polygon":
                    plate_reflex += reflex_vertices(g)
            fc_cut = 0
            fc_wing = 0
            fc_zone_max = 0
            fc_v = 0
            for z in zs:
                if z.geom_type != "Polygon":
                    continue
                cm, wg = zone_corners(z, fb, plate_reflex)
                fc_cut += cm
                fc_wing += wg
                fc_zone_max = max(fc_zone_max, cm)
                fc_v = max(fc_v, len(z.exterior.coords) - 1)
            fc = (fc_cut, fc_wing, fc_zone_max, fc_v)
            seen[key] = fc
        c13 = max(c13, fc[0] - fc[1])
        wings = max(wings, fc[1])
        zone_max = max(zone_max, fc[2])
        max_v = max(max_v, fc[3])
    return sp, zone_max, c13, wings, max_v


def u3_analysis(district, row, j):
    import geopandas as gpd
    from openubem.geometry.european_nocore import cut_storey_nocore, lobes_of
    from openubem.geometry.european_residential import allocate_european_dwellings
    from scripts.run_eu_s2_campaign import _drop_redundant_ring_vertices

    if j is None:
        return dict(district=district, building_id=row.building_id, failed_checks="", cause="no_sidecar")
    base = dict(district=district, building_id=row.building_id, k_max=j.get("observed_max_per_floor"),
                storeys=j.get("storeys"), dwellings=j.get("dwellings_total"))
    gdf = u3_analysis.cache.get(district)
    if gdf is None:
        gdf = gpd.read_file(ROOT + f"openubem/outputs/eu02/{district}/02_residential_manifest.gpkg")
        gdf["osm_id"] = gdf["osm_id"].astype(str)
        u3_analysis.cache[district] = gdf
    hit = gdf[gdf.osm_id == str(row.building_id)]
    if hit.empty:
        return dict(base, failed_checks="", cause="footprint_not_found")
    fp = hit.geometry.iloc[0]
    alloc = allocate_european_dwellings(
        archetype_id=row.archetype_id, building_type=row.building_type,
        n_apartment=j["dwellings_total"], n_storey=j["storeys"], plate_area_m2=float(fp.area),
    )
    counts = sorted({fa.dwelling_count for fa in alloc.floor_allocations if fa.dwelling_count > 0})
    if isinstance(fp, Polygon):
        fp = Polygon(_drop_redundant_ring_vertices(list(fp.exterior.coords)), list(fp.interiors))
    causes = {"hole": 0, "contains": 0, "points_gt_40": 0, "lobed": 0, "overlap": 0}
    failed = set()
    max_pts = 0
    failing_counts = []
    for cnt in counts:
        try:
            plate, live, checks, verdict = cut_storey_nocore(fp, cnt)
        except Exception as exc:
            failing_counts.append(f"{cnt}:{type(exc).__name__}")
            continue
        bad = [c for c in ("C4", "C5") if not checks[c]["pass"]]
        if not bad:
            continue
        failing_counts.append(str(cnt))
        failed.update(bad)
        if any(len(f.interiors) for f in live):
            causes["hole"] += 1
        reps = [f.representative_point() for f in live]
        if any(i != jx and fi.contains(pt) for i, fi in enumerate(live) for jx, pt in enumerate(reps)):
            causes["contains"] += 1
        pts = max((len(f.exterior.coords) - 1 for f in live), default=0)
        max_pts = max(max_pts, pts)
        if pts > 40:
            causes["points_gt_40"] += 1
        if any(lobes_of(f) is not None for f in live):
            causes["lobed"] += 1
        worst = 0.0
        for a in range(len(live)):
            for b in range(a + 1, len(live)):
                worst = max(worst, live[a].intersection(live[b]).area)
        if worst >= 0.02:
            causes["overlap"] += 1
    primary = ",".join(k for k, v in causes.items() if v) or "not_reproduced"
    return dict(base, counts_tried=";".join(map(str, counts)), failing_counts=";".join(failing_counts),
                failed_checks="+".join(sorted(failed)), max_points=max_pts, cause=primary, **causes)


u3_analysis.cache = {}


def run_district(district):
    E = EVID
    m = pd.read_csv(glob.glob(f"{E}{district}_merged_2026-09-08/*manifest*.csv")[0], dtype=str)
    p = pd.read_csv(f"{E}{district}_recut_2026-09-08/prepared_buildings.csv", dtype=str).set_index("building_id")
    rows, u3, v3 = [], [], []
    for _, r in m.iterrows():
        bid = r.building_id
        go = r.geometry_outcome if isinstance(r.geometry_outcome, str) else ""
        if bid in p.index:
            fr = p.fallback_reason.get(bid)
            stem = p.stem.get(bid)
        else:
            fr, stem = None, None
        fr = "" if (fr is None or isinstance(fr, float)) else fr
        sc = f"{VIEW}eu_{district}_data/layouts/{bid}.json"
        j = json.load(open(sc, encoding="utf-8")) if os.path.exists(sc) else None
        k = (j or {}).get("observed_max_per_floor")
        st = (j or {}).get("storeys")
        dw = (j or {}).get("dwellings_total")
        sp = zmax = c13 = wings = maxv = None
        if j and (not j.get("fallback_reason") or str(j.get("fallback_reason")).startswith("NOCORE_BEST_EFFORT")):
            sp, zmax, c13, wings, maxv = analyse_sidecar(j)
        if "REROUTED" in go:
            cls = "U1_cut_lost_at_idf_write"
        elif go.startswith("FALLBACK"):
            if "DENSITY" in fr:
                cls = "U2_more_than_12_flats"
            elif k == 1:
                cls = "S1_one_flat_per_floor_by_data"
            elif "C4" in fr or "C5" in fr:
                cls = "U3_cut_breaks_hard_rule_C4_C5"
            else:
                cls = "U4_other_box"
        elif "BEST_EFFORT" in go:
            cls = "V1_divided_shape_rule_broken"
        elif j is None:
            cls = "X_no_sidecar"
        elif sp is not None and sp < 0.5:
            cls = "V2_divided_unbalanced"
        elif zmax and zmax >= 1:
            cls = "V3_divided_wrapped_flat"
        else:
            cls = "OK"
        fa = float(r.floor_area_m2) if isinstance(r.floor_area_m2, str) else None
        rows.append(dict(
            district=district, building_id=bid, stem=stem, geometry_outcome=go, fallback_reason=fr,
            k_max=k, storeys=st, dwellings=dw, floor_area_m2=fa,
            m2_per_dwelling=(fa / dw if (fa and dw) else None), min_spread=sp, c13_bent_walls=c13,
            wing_bends=wings, max_zone_vertices=maxv, **{"class": cls},
            v1_also_unbalanced=bool(sp is not None and sp < 0.5), v1_also_wrapped=bool(zmax and zmax >= 1),
        ))
        if cls == "V3_divided_wrapped_flat":
            v3.append(dict(district=district, building_id=bid, stem=stem, c13_bent_walls=c13,
                           wing_bends=wings, split="wrap" if c13 >= 1 else "wing_bend_only"))
        if cls == "U3_cut_breaks_hard_rule_C4_C5":
            u3.append(u3_analysis(district, r, j))
    return rows, u3, v3


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    with Pool(4) as pool:
        results = pool.map(run_district, DISTRICTS)
    rows = [x for r in results for x in r[0]]
    u3 = [x for r in results for x in r[1]]
    v3 = [x for r in results for x in r[2]]
    df = pd.DataFrame(rows)
    df.to_csv(OUT + "division_status.csv", index=False)
    pd.DataFrame(u3).to_csv(OUT + "u3_causes.csv", index=False)
    pd.DataFrame(v3).to_csv(OUT + "v3_split.csv", index=False)
    tab = pd.crosstab(df["class"], df["district"])
    hist = {c: {d: int(tab.loc[c, d]) if c in tab.index else 0 for d in DISTRICTS} for c in CLASS_ORDER}
    hist = {c: dict(v, Fleet=sum(v.values())) for c, v in hist.items()}
    hist["Total"] = {d: int((df.district == d).sum()) for d in DISTRICTS}
    hist["Total"]["Fleet"] = len(df)
    json.dump(hist, open(OUT + "histogram.json", "w"), indent=1)
    print(pd.crosstab(df["class"], df["district"], margins=True).to_string())
    print(df[df["class"].str.startswith("V1")].groupby("district")[["v1_also_unbalanced", "v1_also_wrapped"]].sum())
    v = pd.DataFrame(v3)
    print(v.groupby(["district", "split"]).size().unstack(fill_value=0), v.split.value_counts().to_dict())
    u = pd.DataFrame(u3)
    print(u.cause.value_counts().to_dict(), u.failed_checks.value_counts().to_dict())


if __name__ == "__main__":
    main()
