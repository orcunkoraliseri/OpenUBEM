import glob
import json
import math
import os
import re
import sys

import pandas as pd
from shapely.affinity import translate
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = "C:/Users/o_iseri/Desktop/OpenUBEM/"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from openubem.geometry import european_nocore as N

EVID = ROOT + "openubem/outputs/eu_evidence/EU-11/"
VIEW = ROOT + "docs/docs_DONE/SETUP/europeanLocations/outputs_3D/"
BASE = EVID + "rulebook_2026-09-30/baseline.csv"
OUT = EVID + "bentwall_2026-09-30/"
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
GATED = N._GATED_CHECKS + ("C12",)
TOUCH_M = 0.05


def idf_storeys(path):
    t = open(path, errors="ignore").read()
    by = {}
    for blk in re.findall(r"(?is)BUILDINGSURFACE:DETAILED,(.*?);", t):
        vals = [re.sub(r"\s*!.*", "", v).strip().rstrip(",;") for v in blk.split("\n") if v.strip()]
        if len(vals) < 15 or vals[1].lower() != "floor":
            continue
        try:
            xyz = vals[11:]
            ring = [tuple(float(x) for x in xyz[i:i + 3]) for i in range(0, len(xyz) - 2, 3)]
        except ValueError:
            continue
        z = round(min(p[2] for p in ring), 2)
        by.setdefault(z, []).append(Polygon([(p[0], p[1]) for p in ring]).buffer(0))
    out = []
    for z in sorted(by):
        uniq = []
        for q in by[z]:
            if not any(q.symmetric_difference(w).area < 0.01 for w in uniq):
                uniq.append(q)
        out.append(uniq)
    return out


def live_polys(flats):
    live = []
    for f in flats:
        if f is None or f.is_empty:
            continue
        if f.geom_type != "Polygon":
            parts = [g for g in getattr(f, "geoms", []) if g.geom_type == "Polygon"]
            if not parts:
                continue
            f = max(parts, key=lambda g: g.area)
        live.append(f)
    return live


def parts_of(flats, k):
    live = live_polys(flats)
    if not live:
        return []
    whole = unary_union(live).buffer(0)
    parts = [g for g in getattr(whole, "geoms", [whole]) if g.geom_type == "Polygon"]
    out = []
    for p in parts:
        mine = [f for f in live if f.representative_point().within(p)]
        if mine:
            out.append((p, mine, k if len(parts) == 1 else len(mine)))
    return out


def census_frame(flats):
    smooth = unary_union(flats).buffer(0.01).buffer(-0.01)
    sharp = unary_union(flats).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
    reflex = []
    for g in getattr(sharp, "geoms", [sharp]):
        if g.geom_type == "Polygon":
            reflex += N._plate_reflex_points(g)
    return smooth.boundary, reflex


def corners(poly, flats, boundary=None, reflex=None):
    if boundary is None:
        boundary = poly.boundary
        reflex = N._plate_reflex_points(poly)
    out = []
    for fi, flat in enumerate(flats):
        c = list(flat.exterior.coords)[:-1]
        if not Polygon(c).exterior.is_ccw:
            c = c[::-1]
        n = len(c)

        def interior_edge(j):
            p, q = c[j % n], c[(j + 1) % n]
            return boundary.distance(Point((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)) > 0.05

        def near_reflex(pt):
            p = Point(pt)
            return any(p.distance(r) <= N.WING_BEND_TOLERANCE_M for r in reflex)

        for i in range(n):
            a, b, d = c[i - 1], c[i], c[(i + 1) % n]
            la = math.hypot(b[0] - a[0], b[1] - a[1])
            lb = math.hypot(d[0] - b[0], d[1] - b[1])
            if la < 0.3 or lb < 0.3:
                continue
            cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
            if not (cr / (la * lb) < N.BENT_CORNER_TURN and boundary.distance(Point(b)) > 0.10):
                continue
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
            pf, pg = c[f % n], c[g % n]
            out.append(dict(flat=fi, corner=b, ends=[pf, pg], wing=near_reflex(pf) or near_reflex(pg)))
    return out


def touched(flats, pt):
    p = Point(pt)
    return sum(1 for f in flats if f.distance(p) <= TOUCH_M)


def classify(poly, flats, k, base, cn, walls, cache, boundary=None, reflex=None):
    if boundary is None:
        boundary = poly.boundary
        reflex = N._plate_reflex_points(poly)
    if cn["wing"]:
        return "wing_bend", "", touched(flats, cn["corner"])
    pts = list(cn["ends"])
    wall = None
    for i, j, verts in walls:
        if cn["flat"] not in (i, j) or len(verts) < 3:
            continue
        if any(Point(v).distance(Point(cn["corner"])) <= TOUCH_M for v in verts[1:-1]):
            wall = (i, j, verts)
            break
    if wall is not None:
        pts += [wall[2][0], wall[2][-1]]
    interior = [p for p in pts if boundary.distance(Point(p)) > N.WALL_END_TOLERANCE_M]
    if touched(flats, cn["corner"]) >= 3 or any(touched(flats, p) >= 3 for p in interior):
        return "junction_wrap", "", touched(flats, cn["corner"])
    if wall is None:
        return "interior_end", "", touched(flats, cn["corner"])
    i, j, verts = wall
    e0, e1 = verts[0], verts[-1]
    if interior or any(Point(e).distance(r) <= N.WING_BEND_TOLERANCE_M for e in (e0, e1) for r in reflex):
        return "interior_end", "", touched(flats, cn["corner"])
    key = (i, j, round(e0[0], 3), round(e0[1], 3), round(e1[0], 3), round(e1[1], 3))
    if key not in cache:
        trial = N._straightened(flats, i, j, e0, e1)
        if trial is None:
            cache[key] = None
        else:
            rec = N._score_cut(poly, trial, k)
            cache[key] = (rec, N._strictly_better(base, rec))
    hit = cache[key]
    if hit is None:
        return "no_chord", "", touched(flats, cn["corner"])
    rec, accepts = hit
    broken = [c for c in GATED if base["checks"][c]["pass"] and not rec["checks"][c]["pass"]]
    lower = rec["checks"]["C13"]["value"] < base["checks"]["C13"]["value"]
    if not broken and lower:
        return "straight_missed", "accepted_by_engine" if accepts else "spread_lower_only", touched(flats, cn["corner"])
    return "straight_not_better", "+".join(broken) if broken else ("C13_not_lower" if not lower else ""), touched(flats, cn["corner"])


def home_storeys(row, gc_cache):
    district, bid = row.district, row.building_id
    if row.geom_source == "installed_sidecar":
        j = json.load(open(f"{VIEW}eu_{district}_data/layouts/{bid}.json", encoding="utf-8"))
        return [([Polygon(z["coords_m"]).buffer(0) for z in f["zones"]], int(f.get("dwelling_count") or len(f["zones"]))) for f in j["floors"]]
    g = gc_cache[district].loc[bid]
    path = f"{EVID}{district}_fix_2026-09-29/idfs/{g.stem_new}.idf"
    return [(fl, len(fl)) for fl in idf_storeys(path)]


def main():
    os.makedirs(OUT + "scratch/", exist_ok=True)
    bl = pd.read_csv(BASE, dtype=str)
    v3 = bl[bl.cls.str.startswith("V3")].copy()
    gc_cache = {}
    for d in DISTRICTS:
        gc = pd.read_csv(EVID + "division_residual_2026-09-29/scratch/t05/gate_candidates.csv", dtype=str)
        gc_cache[d] = gc[gc.district == d].set_index("building_id")
    rows, homes = [], []
    geo_cache = {}
    for _, r in v3.iterrows():
        if r.geom_source == "fix_idf_not_a_partition_blank":
            rows.append(dict(district=r.district, building_id=r.building_id, stem=r.stem, storey=-1, k=0, c13_storey=0,
                             storey_failed_checks="", corner_x="", corner_y="", flats_touching=0, type="no_geometry",
                             straight_breaks="", basis="none"))
            homes.append(dict(district=r.district, building_id=r.building_id, stem=r.stem, geom_source=r.geom_source,
                              n_storeys=0, c13_total=0, error="no_geometry"))
            continue
        try:
            storeys = home_storeys(r, gc_cache)
        except Exception as exc:
            homes.append(dict(district=r.district, building_id=r.building_id, stem=r.stem, geom_source=r.geom_source,
                              n_storeys=0, c13_total=0, error=type(exc).__name__))
            continue
        c13_total = 0
        n_done = 0
        for s, (fl, k) in enumerate(storeys):
            for poly0, flats0, kk in parts_of(fl, k):
                cx, cy = poly0.centroid.x, poly0.centroid.y
                poly = translate(poly0, -cx, -cy)
                flats = [translate(f, -cx, -cy) for f in flats0]
                if any(f.geom_type != "Polygon" for f in flats):
                    continue
                key = (kk, round(poly.area, 3), tuple(sorted((round(f.area, 3), round(f.centroid.x, 2), round(f.centroid.y, 2)) for f in flats)))
                if key not in geo_cache:
                    base = N._score_cut(poly, flats, kk)
                    c13 = N.c13_bent_walls(poly, flats)
                    walls = N._party_walls(flats)
                    cache = {}
                    out = []
                    for cn in corners(poly, flats):
                        t, broken, nt = classify(poly, flats, kk, base, cn, walls, cache)
                        out.append(dict(corner_x=round(cn["corner"][0] + cx, 3), corner_y=round(cn["corner"][1] + cy, 3),
                                        flats_touching=nt, type=t, straight_breaks=broken, basis="engine"))
                    if c13 == 0 and len(flats) > 1:
                        cb, cr_ = census_frame(flats)
                        seen = {(o["corner_x"], o["corner_y"]) for o in out}
                        for cn in corners(poly, flats, cb, cr_):
                            xy = (round(cn["corner"][0] + cx, 3), round(cn["corner"][1] + cy, 3))
                            if xy in seen:
                                continue
                            t, broken, nt = classify(poly, flats, kk, base, cn, walls, cache, cb, cr_)
                            out.append(dict(corner_x=xy[0], corner_y=xy[1], flats_touching=nt, type=t,
                                            straight_breaks=broken, basis="census"))
                    failed = [c for c in GATED if not base["checks"][c]["pass"]]
                    geo_cache[key] = (c13, out, "+".join(failed))
                c13, out, failed = geo_cache[key]
                c13_total += c13
                n_done += 1
                for o in out:
                    rows.append(dict(district=r.district, building_id=r.building_id, stem=r.stem, storey=s, k=kk,
                                     c13_storey=c13, storey_failed_checks=failed, **o))
        homes.append(dict(district=r.district, building_id=r.building_id, stem=r.stem, geom_source=r.geom_source,
                          n_storeys=n_done, c13_total=c13_total, error=""))
    have = {(x["district"], x["building_id"]) for x in rows}
    for h in homes:
        if (h["district"], h["building_id"]) not in have:
            rows.append(dict(district=h["district"], building_id=h["building_id"], stem=h["stem"], storey=-1, k=0, c13_storey=0,
                             storey_failed_checks="", corner_x="", corner_y="", flats_touching=0, type="no_bend",
                             straight_breaks="", basis="none"))
    pd.DataFrame(rows).to_csv(OUT + "bentwall_why.csv", index=False)
    pd.DataFrame(homes).to_csv(OUT + "scratch/bentwall_homes.csv", index=False)
    print(len(v3), len(homes), len(rows))
    summary(bl)


ORDER = ["straight_missed", "straight_not_better", "no_chord", "interior_end", "junction_wrap", "wing_bend", "no_bend", "no_geometry"]


def summary(bl):
    w = pd.read_csv(OUT + "bentwall_why.csv")
    e = w[w.basis == "engine"]
    L = ["# Bent party walls: why each V3 home is bent (T01, 2026-09-30)", "",
         "Engine basis = the corner test of `_flat_bends` on the plate itself (what C13 counts). Census basis = the same test on the smoothed plate the census used, added only on storeys where the engine sees C13 = 0.", ""]
    L += ["## Corners per type (engine basis, 478 of 478 homes read)", "", "| district | " + " | ".join(ORDER[:-2]) + " |", "|---|" + "---|" * (len(ORDER) - 2)]
    for d in DISTRICTS:
        x = e[e.district == d].type.value_counts()
        L.append(f"| {d} | " + " | ".join(str(int(x.get(t, 0))) for t in ORDER[:-2]) + " |")
    x = e.type.value_counts()
    L.append("| all | " + " | ".join(str(int(x.get(t, 0))) for t in ORDER[:-2]) + " |")
    L += ["", f"Corners on engine basis: {len(e)}. Census-basis extra corners (storeys with C13 = 0): {int((w.basis == 'census').sum())}. Homes with no geometry (fix IDF floors are not a partition): {int((w.type == 'no_geometry').sum())} of 478. Homes read with no corner on either basis (`no_bend`): {int((w.type == 'no_bend').sum())} of 478. Homes with a row: {w.groupby(['district', 'building_id']).ngroups} of 478.", ""]
    sm = e[e.type == "straight_missed"].straight_breaks.value_counts().to_dict()
    L += [f"`straight_missed` = {int((e.type == 'straight_missed').sum())} corners; engine would accept the straight wall on {sm.get('accepted_by_engine', 0)}, the other {sm.get('spread_lower_only', 0)} are refused only because the C12 spread value drops (no check breaks).", ""]
    worst = {}
    for bid, g in w.groupby("building_id"):
        t = set(g.type)
        worst[bid] = next(o for o in ORDER if o in t)
    wd = pd.Series(worst).value_counts()
    L += ["## Homes by worst type (order: " + ", ".join(ORDER) + ")", ""] + [f"- {t}: {int(wd.get(t, 0))} of 478" for t in ORDER] + [""]
    v3 = bl[bl.cls.str.startswith("V3")]
    z = v3[v3.n_storeys_C13_fail == "0"]
    zn = z[z.geom_source != "fix_idf_not_a_partition_blank"]
    bad = w[w.building_id.isin(zn.building_id) & (~w.type.isin(["wing_bend", "no_bend"]))]
    L += ["## The 128 homes with C13 = 0 on every storey", "",
          f"- 128 of 478 in baseline.csv; {len(z) - len(zn)} of 128 have no geometry (blank), {len(zn)} of 128 read.",
          f"- {len(zn) - bad.building_id.nunique()} of {len(zn)} show only wing_bend corners or no cut-made corner at all.",
          f"- {bad.building_id.nunique()} of {len(zn)} are exceptions (census-basis corner not a wing bend, or one engine straight_not_better); ids: " + ", ".join(sorted(bad.building_id.unique())), ""]
    sp = pd.read_csv(ROOT + "openubem/outputs/eu_evidence/EU-11/division_residual_2026-09-29/v3_split.csv", dtype=str)
    mad = sp[(sp.district == "ES-MAD-BERRUGUETE") & (sp.split == "wrap")].head(25)
    L += ["## Madrid 25-home sample", "", "First 25 Madrid `wrap` homes of v3_split.csv, engine basis, corners per type. Mapping to the 7 / 5 / 8 check: junction = junction_wrap; interior or wing end = interior_end + wing_bend; not better = straight_not_better + straight_missed + no_chord.", "",
          "| home | " + " | ".join(ORDER[:-2]) + " |", "|---|" + "---|" * (len(ORDER) - 2)]
    tot = dict.fromkeys(ORDER, 0)
    for bid in mad.building_id:
        x = e[(e.district == "ES-MAD-BERRUGUETE") & (e.building_id == bid)].type.value_counts()
        for t in ORDER[:-2]:
            tot[t] += int(x.get(t, 0))
        L.append(f"| {bid} | " + " | ".join(str(int(x.get(t, 0))) for t in ORDER[:-2]) + " |")
    L += ["", f"Homes in sample: {len(mad)}. Totals: junction {tot['junction_wrap']} / interior-or-wing end {tot['interior_end'] + tot['wing_bend']} / not better {tot['straight_not_better'] + tot['straight_missed'] + tot['no_chord']}, expected 7 / 5 / 8.", ""]
    f = v3[(v3.n_storeys != v3.n_storeys_pass_verdict_and_c12) & (v3.geom_source != "fix_idf_not_a_partition_blank")]
    L += ["## The 3 homes that fail a check", ""]
    for _, r in f.iterrows():
        sj = json.loads(r.storeys_json)
        ch = sorted({c for x in sj for c in ["C1", "C3", "C4", "C5", "C6", "C10", "C11", "C12"] if not x[c + "_ok"]})
        n = sum(1 for x in sj if not (x["verdict"] == "PASS" and x["c12_ok"]))
        L.append(f"- {r.district} {r.building_id}: {'+'.join(ch)} on {n} of {len(sj)} storeys")
    L += [""]
    open(OUT + "bentwall_summary.md", "w", encoding="utf-8").write(chr(10).join(L) + chr(10))


if __name__ == "__main__":
    main()
