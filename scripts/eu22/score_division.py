from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing as mp
import re
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
DRYRUN = ROOT / "scripts" / "analysis" / "eu_rulebook_dryrun_2026-09-30.py"
MAX_WORKERS = 4
FLOOR_TO_FLOOR_M = 3.0
SIMPLIFY_M = 0.005
SPIKE_M = 0.01
CLOSE_M = 0.02
COLLINEAR_M = 1e-4
KEEP_CLASSES = ("OK", "V3_divided_wrapped_flat", "S1_one_flat_per_floor_by_data")
CHECKS = ["C1", "C3", "C4", "C5", "C6", "C10", "C11", "C12", "C13"]
COLUMNS = [
    "district", "building_id", "stem", "cls", "zones", "k_max", "dw_used_1006", "moved_1006", "moved_1006_reason",
    "dw_match", "n_storeys", "n_storeys_fail_verdict", "n_storeys_fail_c12",
] + [f"n_storeys_{c}_fail" for c in CHECKS] + ["class_source"]
_BS = re.compile(r"(?is)BUILDINGSURFACE:DETAILED,(.*?);")
_DR = None
_CENSUS = None


def _driver():
    global _DR
    if _DR is None:
        spec = importlib.util.spec_from_file_location("eu_rulebook_dryrun", DRYRUN)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _DR = mod
    return _DR


def _census():
    global _CENSUS
    if _CENSUS is None:
        _CENSUS = _driver()._load_census()
    return _CENSUS


def _drop_spikes(coords):
    pts = list(coords)[:-1]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            ux, uy, vx, vy = a[0] - b[0], a[1] - b[1], c[0] - b[0], c[1] - b[1]
            lu, lv = (ux * ux + uy * uy) ** 0.5, (vx * vx + vy * vy) ** 0.5
            if lu < 1e-9 or lv < 1e-9:
                del pts[i]
                changed = True
                break
            if (ux * vx + uy * vy) / (lu * lv) > 0.9999 or abs(ux * vy - uy * vx) / max(lu, lv) < SPIKE_M and (ux * vx + uy * vy) > 0:
                del pts[i]
                changed = True
                break
    return pts


def _raw_polygon(frags):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    geom = frags[0] if len(frags) == 1 else unary_union(frags)
    if geom.geom_type != "Polygon" or not geom.is_valid:
        geom = geom.buffer(0)
    if geom.geom_type != "Polygon":
        geom = max((g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"), key=lambda g: g.area)
    ring = Polygon(geom.exterior)
    simple = ring.simplify(COLLINEAR_M)
    return simple if simple.geom_type == "Polygon" and simple.is_valid and not simple.is_empty else ring


def _clean_polygon(frags):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    geom = unary_union(frags).buffer(CLOSE_M, join_style=2, mitre_limit=5.0).buffer(-CLOSE_M, join_style=2, mitre_limit=5.0)
    if geom.geom_type != "Polygon":
        geom = max((g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"), key=lambda g: g.area)
    ring = Polygon(_drop_spikes(geom.exterior.coords))
    simple = ring.simplify(SIMPLIFY_M)
    return simple if simple.geom_type == "Polygon" and simple.is_valid and not simple.is_empty else ring


def _zone_footprints(path, clean=False):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    text = open(path, errors="ignore").read()
    zones = {}
    for blk in _BS.findall(text):
        vals = [re.sub(r"\s*!.*", "", v).strip().rstrip(",;") for v in blk.split(chr(10)) if v.strip()]
        if len(vals) < 15:
            continue
        try:
            xyz = vals[11:]
            ring = [tuple(float(x) for x in xyz[i:i + 3]) for i in range(0, len(xyz) - 2, 3)]
        except ValueError:
            continue
        rec = zones.setdefault(vals[3], {"floors": [], "top": float("-inf")})
        rec["top"] = max(rec["top"], max(q[2] for q in ring))
        if vals[1].lower() == "floor":
            rec["floors"].append((min(q[2] for q in ring), Polygon([(q[0], q[1]) for q in ring]).buffer(0)))
    out = {}
    for name, rec in zones.items():
        if not rec["floors"]:
            continue
        z0 = min(f[0] for f in rec["floors"])
        polys = [f[1] for f in rec["floors"] if abs(f[0] - z0) < 1e-6]
        out[name] = (round(z0, 2), rec["top"], (_raw_polygon(polys) if len(polys) == 1 else _clean_polygon(polys)))
    return out


def _storey_groups(path, clean=False):
    by = {}
    for name, (z0, top, poly) in _zone_footprints(path, clean).items():
        if "_dwelling_" not in name:
            continue
        g = by.setdefault(z0, {"top": top, "polys": []})
        g["top"] = max(g["top"], top)
        g["polys"].append(poly)
    spans, groups = [], []
    for z0 in sorted(by):
        spans.append(max(1, int(round((by[z0]["top"] - z0) / FLOOR_TO_FLOOR_M))))
        groups.append(by[z0]["polys"])
    return spans, groups


def _rules(name):
    import openubem.geometry.european_nocore as E

    if name == "defaults":
        E.NOCORE_RULESET.clear()
        E.NOCORE_RULESET.update(E.NOCORE_RULESET_DEFAULTS)
    else:
        E.NOCORE_RULESET.clear()
        E.NOCORE_RULESET.update({"max_flat_aspect": E.MAX_FLAT_ASPECT, "min_spread": E.MIN_SPREAD, "flat_area_cap_m2": None})
    return dict(E.NOCORE_RULESET)


def _observed_k(row, n_storey):
    from openubem.geometry.european_residential import allocate_european_dwellings

    try:
        alloc = allocate_european_dwellings(
            archetype_id=row["archetype_id"], building_type=row["building_type"],
            n_apartment=float(row["dwellings_used"]), n_storey=max(1, n_storey),
            plate_area_m2=float(row["gross_footprint_area_m2"]),
        )
    except Exception:
        return None
    return max((fa.dwelling_count for fa in alloc.floor_allocations), default=None)


def _divided_result(spans, storeys, rules, best_effort=None):
    import openubem.geometry.european_nocore as E

    dr = _driver()
    out = {}
    cache = {}
    fails = {c: 0 for c in CHECKS}
    nfail = 0
    nst = 0
    for span, polys in zip(spans, storeys):
        k = len(polys)
        nst += span
        key = (k, tuple(sorted(round(f.area, 3) for f in polys)))
        if key not in cache:
            cache[key] = dr._storey_record(E, polys, k)
        rec = cache[key]
        if rec is None:
            continue
        if not rec["verdict"]:
            nfail += span
        for c in CHECKS:
            if not rec[c]:
                fails[c] += span
    out["n_storeys"] = nst
    out["n_storeys_fail_verdict"] = nfail
    out["n_storeys_fail_c12"] = fails["C12"]
    for c in CHECKS:
        out[f"n_storeys_{c}_fail"] = fails[c]
    if (nfail > 0) if best_effort is None else best_effort:
        out["cls"] = "V1_divided_shape_rule_broken"
        return out
    j = {"floors": [{"zones": [{"coords_m": list(q.exterior.coords)[:-1]} for q in polys]} for polys in storeys]}
    sp, zmax, _c13, _wings, _maxv = _census().analyse_sidecar(j)
    if sp is not None and sp < rules["min_spread"]:
        out["cls"] = "V2_divided_unbalanced"
    elif zmax and zmax >= 1:
        out["cls"] = "V3_divided_wrapped_flat"
    else:
        out["cls"] = "OK"
    return out


def _sidecar_path(layout_dir, building_id):
    if layout_dir is None:
        return None
    p = Path(layout_dir) / "layouts" / f"{building_id}.json"
    return p if p.exists() else None


def _sidecar_storeys(j):
    spans, storeys = [], []
    for f in j.get("floors") or []:
        zs = [Polygon(z["coords_m"]).buffer(0) for z in f.get("zones") or []]
        zs = [z for z in zs if not z.is_empty]
        if not zs:
            continue
        spans.append(max(1, int(f.get("storey_span") or 1)))
        storeys.append(zs)
    return spans, storeys


def _sidecar_home(row, j, out, rules, floors_decide=False):
    go = j.get("geometry_outcome") or ""
    go_prep = row.get("geometry_outcome") or ""
    fr = j.get("fallback_reason") or row.get("fallback_reason") or ""
    if "REROUTED" in go or "REROUTED" in go_prep:
        out["cls"] = "U1_cut_lost_at_idf_write"
        return out
    if go.startswith("FALLBACK"):
        if "DENSITY" in fr:
            out["cls"] = "U2_more_than_12_flats"
        elif j.get("observed_max_per_floor") == 1:
            out["cls"] = "S1_one_flat_per_floor_by_data"
        elif "C4" in fr or "C5" in fr:
            out["cls"] = "U3_cut_breaks_hard_rule_C4_C5"
        else:
            out["cls"] = "U4_other_box"
        return out
    spans, storeys = _sidecar_storeys(j)
    out["k_max"] = max((len(s) for s in storeys), default=0)
    out.update(_divided_result(spans, storeys, rules, best_effort=None if floors_decide else "BEST_EFFORT" in go))
    return out


def _score_home(args):
    row, idf, ruleset, district, layout_dir, *extra = args
    floors_decide = bool(extra and extra[0])
    import openubem.geometry.european_nocore as E

    dr = _driver()
    rules = _rules(ruleset)
    out = {c: "" for c in COLUMNS}
    out.update(district=district, building_id=row["building_id"], stem=row["stem"], dw_used_1006=row.get("dwellings_used", ""))
    out.update(n_storeys=0, n_storeys_fail_verdict=0, n_storeys_fail_c12=0, **{f"n_storeys_{c}_fail": 0 for c in CHECKS})
    path = Path(idf)
    sc = _sidecar_path(layout_dir, row["building_id"])
    if sc is not None:
        out["class_source"] = "LAYOUT_SIDECAR"
        try:
            j = json.loads(sc.read_text(encoding="utf-8"))
            out["zones"] = len(list(dr._zone_map(str(path)))) if path.exists() else 0
            return _sidecar_home(row, j, out, rules, floors_decide)
        except Exception as exc:
            out["cls"] = "X_score_error"
            out["moved_1006_reason"] = f"{type(exc).__name__}: {str(exc)[:80]}"
            return out
    out["class_source"] = "IDF_FALLBACK" if layout_dir is not None else "IDF_ONLY"
    if not path.exists():
        out.update(cls="X_no_idf", zones=0, k_max=0)
        return out
    names = list(dr._zone_map(str(path)))
    nz = len(names)
    divided = any("_dwelling_" in n for n in names)
    spans, storeys = _storey_groups(str(path)) if divided else ([], [])
    out["zones"] = nz
    out["k_max"] = max((len(s) for s in storeys), default=0)
    go = row.get("geometry_outcome") or ""
    fr = row.get("fallback_reason") or ""
    if not divided:
        k_obs = _observed_k(row, len(_zone_footprints(str(path))))
        if "REROUTED" in go:
            out["cls"] = "U1_cut_lost_at_idf_write"
        elif "DENSITY" in fr:
            out["cls"] = "U2_more_than_12_flats"
        elif k_obs == 1:
            out["cls"] = "S1_one_flat_per_floor_by_data"
        elif "C4" in fr or "C5" in fr:
            out["cls"] = "U3_cut_breaks_hard_rule_C4_C5"
        else:
            out["cls"] = "U4_other_box"
        return out
    try:
        out.update(_divided_result(spans, storeys, rules))
    except Exception:
        spans, storeys = _storey_groups(str(path), True)
        out["k_max"] = max((len(s) for s in storeys), default=0)
        try:
            out.update(_divided_result(spans, storeys, rules))
        except Exception as exc:
            out["cls"] = "X_score_error"
            out["moved_1006_reason"] = f"{type(exc).__name__}: {str(exc)[:80]}"
    return out


def _resolve_dir(evidence, name):
    p = Path(name)
    return p if p.is_absolute() else evidence / name


def score(site: str, tree: str, workers: int, evidence: Path = EVIDENCE, out_dir: Path | None = None,
          ruleset: str = "final", only: set | None = None, layout_tree: str | None = None,
          floors_decide: bool = False) -> dict:
    tdir = _resolve_dir(evidence, tree)
    ldir = _resolve_dir(evidence, layout_tree) if layout_tree else None
    prep = pd.read_csv(tdir / "prepared_buildings.csv", dtype=str).fillna("")
    if only is not None:
        prep = prep[prep.building_id.isin(only)]
    jobs = [(r.to_dict(), str(tdir / "idfs" / f"{r['stem']}.idf"), ruleset, site, ldir, floors_decide) for _, r in prep.iterrows()]
    workers = max(1, min(workers, MAX_WORKERS))
    if workers > 1:
        with mp.Pool(workers) as pool:
            rows = pool.map(_score_home, jobs, chunksize=4)
    else:
        rows = [_score_home(j) for j in jobs]
    df = pd.DataFrame(rows, columns=COLUMNS)
    dest = Path(out_dir) if out_dir else tdir
    dest.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest / "division_classes.csv", index=False)
    left = df[~df.cls.isin(KEEP_CLASSES)]
    left.to_csv(dest / "left_out.csv", index=False)
    return {"homes": len(df), "left_out": len(left), "classes": df.cls.value_counts().to_dict(),
            "class_source": df.class_source.value_counts().to_dict(), "idf_fallback": int((df.class_source == "IDF_FALLBACK").sum()),
            "dir": str(dest)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--evidence-root")
    ap.add_argument("--layout-tree")
    ap.add_argument("--out-dir")
    ap.add_argument("--ruleset", choices=["final", "defaults"], default="final")
    ap.add_argument("--floors-decide", action="store_true")
    a = ap.parse_args(argv)
    evidence = Path(a.evidence_root) if a.evidence_root else EVIDENCE
    out = score(a.site, a.tree, a.workers, evidence, Path(a.out_dir) if a.out_dir else None, a.ruleset,
                layout_tree=a.layout_tree, floors_decide=a.floors_decide)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
