import argparse
import contextlib
import ctypes
import glob
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = "C:/Users/o_iseri/Desktop/OpenUBEM/"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

EVID = ROOT + "openubem/outputs/eu_evidence/EU-11/"
RES = EVID + "division_residual_2026-09-29/"
OUT = EVID + "rulebook_2026-09-30/"
SCRATCH = OUT + "scratch/dryrun/"
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
CH = ["C1", "C3", "C4", "C5", "C6", "C10", "C11", "C12", "C13"]
MAX_PROCS = 10
HOME_CAP_S = 600
REF = "0908"
SUFFIX = ""
BL_FILE = "baseline.csv"
WIN = {d: EVID + f"{d}_win_2026-10-06/" for d in DISTRICTS}

RUNS = {
    "R0": dict(rules={}, guard=True, homes="all"),
    "R1_275": dict(rules={"max_flat_aspect": 2.75}, guard=True, homes="unresolved"),
    "R1_30": dict(rules={"max_flat_aspect": 3.0}, guard=True, homes="unresolved"),
    "R1_35": dict(rules={"max_flat_aspect": 3.5}, guard=True, homes="unresolved"),
    "R2_45": dict(rules={"min_spread": 0.45}, guard=True, homes="unresolved"),
    "R2_40": dict(rules={"min_spread": 0.40}, guard=True, homes="unresolved"),
    "R2_33": dict(rules={"min_spread": 0.33}, guard=True, homes="unresolved"),
    "R3_150": dict(rules={"flat_area_cap_m2": 150.0}, guard=True, homes="notdivided"),
    "R3_200": dict(rules={"flat_area_cap_m2": 200.0}, guard=True, homes="notdivided"),
    "R3_300": dict(rules={"flat_area_cap_m2": 300.0}, guard=True, homes="notdivided"),
    "RALL": dict(rules={"max_flat_aspect": 3.0, "min_spread": 0.40, "flat_area_cap_m2": 200.0}, guard=False, homes="all"),
    "RALL_G": dict(rules={"max_flat_aspect": 3.0, "min_spread": 0.40, "flat_area_cap_m2": 200.0}, guard=True, homes="all"),
}
FULL = ["R0", "RALL", "RALL_G"]
LADDER = [r for r in RUNS if r not in FULL]
RANK = {"OK": 0, "S1_one_flat_per_floor_by_data": 0, "V3_divided_wrapped_flat": 1, "V2_divided_unbalanced": 2,
        "V1_divided_shape_rule_broken": 3, "U1_cut_lost_at_idf_write": 4, "U2_more_than_12_flats": 4,
        "U3_cut_breaks_hard_rule_C4_C5": 4, "U4_other_box": 4, "X_no_sidecar": 5, "NOT_PREPARED": 6, "NOT_IN_BASELINE": 0}
UNRESOLVED = {"U1_cut_lost_at_idf_write", "U2_more_than_12_flats", "U3_cut_breaks_hard_rule_C4_C5", "U4_other_box",
              "V1_divided_shape_rule_broken", "V2_divided_unbalanced"}
NOTDIVIDED = {"U1_cut_lost_at_idf_write", "U2_more_than_12_flats", "U3_cut_breaks_hard_rule_C4_C5", "U4_other_box"}


def _set_ref(ref):
    global REF, SUFFIX, BL_FILE, SCRATCH
    REF = ref
    SUFFIX = "_1006" if ref == "1006" else ""
    BL_FILE = "baseline_1006.csv" if ref == "1006" else "baseline.csv"
    SCRATCH = OUT + ("scratch/dryrun_1006/" if ref == "1006" else "scratch/dryrun/")


def _read_bl(cols):
    path = OUT + BL_FILE
    if REF == "1006":
        if not os.path.exists(path):
            return pd.DataFrame(columns=cols)
        bl = pd.read_csv(path, dtype=str)
        if "idf_sha256" in cols and "idf_sha256" not in bl.columns:
            r0 = OUT + "dryrun_R0_1006.csv"
            if os.path.exists(r0):
                bl = bl.merge(pd.read_csv(r0, dtype=str)[["district", "building_id", "idf_sha256"]], on=["district", "building_id"], how="left")
            else:
                bl["idf_sha256"] = ""
        return bl[[c for c in cols if c in bl.columns]]
    return pd.read_csv(path, dtype=str, usecols=cols)


def _ref_prepared(district):
    return pd.read_csv(WIN[district] + "prepared_buildings.csv", dtype=str)


def _zone_map(path):
    t = open(path, errors="ignore").read()
    zm = {m.strip(): 0.0 for m in re.findall(r"(?im)^\s*Zone,\s*\n\s*([^,!\n]+?)\s*,", t)}
    for blk in re.findall(r"(?is)BUILDINGSURFACE:DETAILED,(.*?);", t):
        vals = [re.sub(r"\s*!.*", "", v).strip().rstrip(",;") for v in blk.split("\n") if v.strip()]
        if len(vals) < 15 or vals[1].lower() != "floor":
            continue
        try:
            xyz = vals[11:]
            ring = [tuple(float(x) for x in xyz[i:i + 3]) for i in range(0, len(xyz) - 2, 3)]
        except ValueError:
            continue
        zm[vals[3]] = zm.get(vals[3], 0.0) + Polygon([(q[0], q[1]) for q in ring]).buffer(0).area
    return zm


def _moved_1006_reason(a, b):
    if set(a) != set(b):
        return "zone_names"
    if any(abs(a[k] - b[k]) > 0.2 for k in a):
        return "zone_area"
    return ""


def _set_rules(E, rules):
    E.NOCORE_RULESET.clear()
    E.NOCORE_RULESET.update(E.NOCORE_RULESET_DEFAULTS)
    E.NOCORE_RULESET.update(rules)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _floor_polys(path):
    t = open(path, errors="ignore").read()
    nz = len(re.findall(r"(?im)^\s*Zone,\s*$", t))
    by, areas = {}, []
    for blk in re.findall(r"(?is)BUILDINGSURFACE:DETAILED,(.*?);", t):
        vals = [re.sub(r"\s*!.*", "", v).strip().rstrip(",;") for v in blk.split("\n") if v.strip()]
        if len(vals) < 15 or vals[1].lower() != "floor":
            continue
        try:
            xyz = vals[11:]
            ring = [tuple(float(x) for x in xyz[i:i + 3]) for i in range(0, len(xyz) - 2, 3)]
        except ValueError:
            continue
        poly = Polygon([(p[0], p[1]) for p in ring]).buffer(0)
        areas.append(round(poly.area, 4))
        by.setdefault(round(min(p[2] for p in ring), 2), []).append(poly)
    storeys = []
    for z in sorted(by):
        uniq = []
        for q in by[z]:
            if not any(q.symmetric_difference(w).area < 0.01 for w in uniq):
                uniq.append(q)
        storeys.append(uniq)
    return nz, sorted(areas), storeys


def _storey_record(N, flats, k):
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
    if not live:
        return None
    whole = unary_union(live).buffer(0)
    parts = [g for g in getattr(whole, "geoms", [whole]) if g.geom_type == "Polygon"]
    groups = []
    for p in parts:
        mine = [f for f in live if f.representative_point().within(p)]
        if mine:
            groups.append((p, mine))
    recs = []
    for p, mine in groups:
        rec = {"drawn_per_floor": k if len(groups) == 1 else len(mine)}
        N.run_checks(rec, mine, p)
        recs.append(rec)
    d = {"verdict": all(r["verdict"] == "PASS" for r in recs)}
    for c in CH:
        d[c] = all(r["checks"][c]["pass"] for r in recs)
    return d


def _load_census():
    spec = importlib.util.spec_from_file_location("census", ROOT + "scripts/analysis/eu_division_residual_census_2026-09-29.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _baseline_paths(district):
    base = pd.read_csv(RES + "scratch/t05/base_idfs.csv", dtype=str)
    base = base[base.district == district].set_index("stem").base_idf
    gc = pd.read_csv(RES + "scratch/t05/gate_candidates.csv", dtype=str)
    gc = gc[gc.district == district].set_index("building_id")
    drop = set(gc.index[(gc.state.isin(["same_class_same_sha", "worse"])) | (gc.index == "way/400445219")])
    return base, gc, drop


def _guardless(E, R):
    import math as _m

    def cut(footprint, count):
        base = R._nocore_cut_and_improve(footprint, count)
        plate, live, checks, verdict = base
        cap = E.NOCORE_RULESET["flat_area_cap_m2"]
        if cap is not None and (not checks["C4"]["pass"] or not checks["C5"]["pass"]) and plate.area / count > cap:
            n2 = _m.ceil(plate.area / cap)
            cand = R._nocore_cut_and_improve(footprint, n2)
            if R._nocore_strictly_better(E.rescore_cut(plate, live, count), E.rescore_cut(cand[0], cand[1], n2)):
                return cand + (n2,)
        return base + (count,)
    return cut


_ORIG = {}


def _memoize(C):
    import geopandas as gpd
    if _ORIG:
        return
    _ORIG["ok"] = True
    store = {}

    def wrap(obj, name):
        f = getattr(obj, name)

        def g(*a, **k):
            if name not in store:
                store[name] = f(*a, **k)
            return store[name]
        setattr(obj, name, g)

    rf = gpd.read_file
    cache = {}

    def read_file(path, *a, **k):
        key = str(path)
        if key not in cache:
            cache[key] = rf(path, *a, **k)
        return cache[key]

    class Shim:
        def __getattr__(self, n):
            return getattr(gpd, n)
    sh = Shim()
    sh.read_file = read_file
    C.gpd = sh
    for n in ("_gb_rows", "_it_rows", "_mapped_rows", "impute_from_neighbours", "compute_district_median_residential_height_m"):
        wrap(C, n)


LAYOUTS = {}


class HomeTimeout(RuntimeError):
    pass


def _disarm():
    t = _ORIG.pop("timer", None)
    if t is not None:
        t.cancel()


def _arm(key, tid):
    _disarm()

    def fire():
        _ORIG.setdefault("timeouts", []).append(key)
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), ctypes.py_object(HomeTimeout))

    t = threading.Timer(HOME_CAP_S, fire)
    t.daemon = True
    _ORIG["timer"] = t
    t.start()


def _capture(C):
    if "geo" in _ORIG:
        return
    _ORIG["geo"] = C._geometry
    real_build = C.build_idf_for_building

    def build(*a, **k):
        try:
            return real_build(*a, **k)
        finally:
            _disarm()
    C.build_idf_for_building = build

    def geo(row, records):
        _disarm()
        if str(row.building_id) in _ORIG.get("capped", ()):
            _arm((_ORIG["run"], _ORIG["district"], str(row.building_id)), threading.get_ident())
        try:
            return geo_inner(row, records)
        except BaseException:
            _disarm()
            raise

    def geo_inner(row, records):
        if "relaxed_ids" in _ORIG:
            import openubem.geometry.european_nocore as _E
            allowed = _ORIG["relaxed_ids"]
            _set_rules(_E, _ORIG["rules"] if allowed is None or str(row.building_id) in allowed else {})
        holder = {}
        real = C.generate_european_building_dwelling_layout

        def cap(*a, **k):
            r = real(*a, **k)
            holder["l"] = r
            return r
        C.generate_european_building_dwelling_layout = cap
        try:
            out = _ORIG["geo"](row, records)
        finally:
            C.generate_european_building_dwelling_layout = real
        lay = holder.get("l")
        groups = []
        if lay is not None and lay.dwelling_layout_emitted:
            for g in lay.storey_groups:
                pre = f"{row.building_id}_F{g.start_storey_index}_dwelling_"
                groups.append((int(g.storey_span), [z["floor_polygon"] for z in out[0] if z["name"].startswith(pre)]))
        LAYOUTS[str(row.building_id)] = (groups, None if lay is None else lay.observed_max_per_floor)
        return out
    C._geometry = geo


def worker(run, district, ids_file, out, memo=False):
    import openubem.geometry.european_nocore as E
    import openubem.geometry.european_residential as R
    from scripts import run_eu_s2_district_campaign as C
    if memo:
        _memoize(C)
    _capture(C)
    if "guard" not in _ORIG:
        _ORIG["guard"] = R._nocore_cut_with_guard
    spec = RUNS[run]
    _set_rules(E, spec["rules"])
    _ORIG["rules"] = spec["rules"]
    bl = _read_bl(["district", "building_id", "stem", "cls", "idf_sha256", "zones", "k_max"])
    bl = bl[bl.district == district].set_index("building_id")
    if REF == "1006" and spec["guard"] and spec["rules"]:
        _ORIG["relaxed_ids"] = frozenset(bl.loc[bl.cls.isin(UNRESOLVED), "stem"].astype(str))
    else:
        _ORIG["relaxed_ids"] = None
    _ORIG["capped"] = frozenset(bl.loc[bl.cls.isin(UNRESOLVED | NOTDIVIDED), "stem"].astype(str))
    _ORIG["run"], _ORIG["district"], _ORIG["timeouts"] = run, district, []
    R._nocore_cut_with_guard = _ORIG["guard"] if spec["guard"] else _guardless(E, R)
    out = Path(out)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(SCRATCH, exist_ok=True)
    only = None
    ref_prep = None
    if REF == "1006":
        ref_prep = _ref_prepared(district).set_index("building_id")
    if ids_file != "all":
        only = frozenset(str(v) for v in pd.read_csv(ids_file, dtype=str)["building_id"])
    elif ref_prep is not None:
        only = frozenset(ref_prep.index)
    try:
        C.prepare(district, None, None, None, out, True, only)
    finally:
        _disarm()
    prep = pd.read_csv(out / "prepared_buildings.csv", dtype=str)
    if REF == "1006":
        base, gc, drop = None, None, None
    else:
        base, gc, drop = _baseline_paths(district)
    census = _load_census()
    thr = E.NOCORE_RULESET["min_spread"]
    rows = []
    cache = {}
    for _, r in prep.iterrows():
        bid = r.building_id
        idf = out / "idfs" / f"{r.stem}.idf"
        go = r.geometry_outcome if isinstance(r.geometry_outcome, str) else ""
        fr = r.fallback_reason if isinstance(r.fallback_reason, str) else ""
        nz, areas, _idf_storeys = _floor_polys(idf)
        groups, kobs = LAYOUTS[r.stem]
        in_base = bid in bl.index
        b = bl.loc[bid] if in_base else pd.Series({"cls": "NOT_IN_BASELINE", "idf_sha256": "", "zones": "0", "k_max": "", "stem": ""})
        if REF == "0908" and b.cls == "X_no_sidecar":
            cls = "X_no_sidecar"
        elif "REROUTED" in go:
            cls = "U1_cut_lost_at_idf_write"
        elif go.startswith("FALLBACK"):
            if "DENSITY" in fr:
                cls = "U2_more_than_12_flats"
            elif kobs == 1:
                cls = "S1_one_flat_per_floor_by_data"
            elif "C4" in fr or "C5" in fr:
                cls = "U3_cut_breaks_hard_rule_C4_C5"
            else:
                cls = "U4_other_box"
        elif "BEST_EFFORT" in go:
            cls = "V1_divided_shape_rule_broken"
        else:
            j = {"floors": [{"zones": [{"coords_m": list(q.exterior.coords)[:-1]} for q in polys]} for _, polys in groups]}
            sp, zmax, c13, wings, maxv = census.analyse_sidecar(j)
            if sp is not None and sp < thr:
                cls = "V2_divided_unbalanced"
            elif zmax and zmax >= 1:
                cls = "V3_divided_wrapped_flat"
            else:
                cls = "OK"
        fails = {c: 0 for c in CH}
        nfail = 0
        nst = 0
        for span, fl in groups:
            k = len(fl)
            nst += span
            key = (k, tuple(sorted(round(f.area, 3) for f in fl)))
            if key not in cache:
                cache[key] = _storey_record(E, fl, k)
            rec = cache[key]
            if rec is None:
                continue
            if not rec["verdict"]:
                nfail += span
            for c in CH:
                if not rec[c]:
                    fails[c] += span
        new_sha = sha(idf)
        moved_reason = ""
        if not in_base:
            pass
        elif new_sha != b.idf_sha256:
            if cls != b.cls:
                moved_reason = "class"
            elif int(b.zones) != nz:
                moved_reason = "zones"
            else:
                if REF == "1006":
                    bp = f"{WIN[district]}idfs/{ref_prep.loc[bid].stem}.idf"
                elif bid in gc.index and bid not in drop:
                    bp = f"{EVID}{district}_fix_2026-09-29/idfs/{gc.loc[bid].stem_new}.idf"
                else:
                    bp = base[b.stem]
                _, bareas, _ = _floor_polys(bp)
                if len(bareas) != len(areas) or any(abs(x - y) > 0.01 for x, y in zip(bareas, areas)):
                    moved_reason = "area"
        elif cls != b.cls:
            moved_reason = "class"
        if not in_base:
            moved_reason = ""
        row = dict(run=run, district=district, building_id=bid, base_cls=b.cls, new_cls=cls, base_zones=int(b.zones), zones=nz,
                   idf_sha256=new_sha, base_sha256=b.idf_sha256, sha_changed=new_sha != b.idf_sha256,
                   moved=bool(moved_reason), moved_reason=moved_reason if in_base else "not_in_baseline", class_moved=(cls != b.cls) and in_base,
                   n_storeys=nst, n_storeys_fail_verdict=nfail,
                   n_storeys_fail_c12=fails["C12"])
        for c in CH:
            row[f"n_storeys_{c}_fail"] = fails[c]
        if REF == "1006":
            rp = ref_prep.loc[bid] if bid in ref_prep.index else None
            ref_idf = f"{WIN[district]}idfs/{rp.stem}.idf" if rp is not None else ""
            m1 = _moved_1006_reason(_zone_map(idf), _zone_map(ref_idf)) if ref_idf and os.path.exists(ref_idf) else "zone_names"
            dwr = r.get("dwellings_used", "")
            dw6 = rp.dwellings_used if rp is not None else ""
            row.update(dw_used_1006=dw6, dw_used_run=dwr, dw_match=str(dwr) == str(dw6), moved_1006=bool(m1), moved_1006_reason=m1)
            if run == "R0":
                row.update(moved=bool(m1), moved_reason=m1)
        rows.append(row)
    got = {x["building_id"] for x in rows}
    want = set(bl.index) if only is None else set(only)
    if REF == "1006":
        bl = bl.reindex(sorted(want | set(bl.index)))
        bl["cls"] = bl["cls"].fillna("NOT_IN_BASELINE")
        bl["zones"] = bl["zones"].fillna("0")
        bl["idf_sha256"] = bl["idf_sha256"].fillna("")
    for bid in sorted(want - got):
        b = bl.loc[bid]
        rows.append(dict(run=run, district=district, building_id=bid, base_cls=b.cls, new_cls="NOT_PREPARED", base_zones=int(b.zones),
                         zones=0, idf_sha256="", base_sha256=b.idf_sha256, sha_changed=True, moved=True,
                         moved_reason="not_prepared", class_moved=True, n_storeys=0, n_storeys_fail_verdict=0, n_storeys_fail_c12=0,
                         **{f"n_storeys_{c}_fail": 0 for c in CH}))
    pd.DataFrame(rows).to_csv(Path(SCRATCH) / f"part_{run}_{district}.csv", index=False)
    pd.DataFrame(_ORIG["timeouts"], columns=["run", "district", "stem"]).to_csv(out / "home_timeouts.csv", index=False)


def _ids_for(run, district, bl):
    h = RUNS[run]["homes"]
    if h == "all":
        return "all"
    sel = UNRESOLVED if h == "unresolved" else NOTDIVIDED
    ids = bl[(bl.district == district) & bl.cls.isin(sel)][["building_id"]]
    p = Path(SCRATCH) / f"ids_{run}_{district}.csv"
    ids.to_csv(p, index=False)
    return str(p) if len(ids) else None


def multi(district, runs):
    bl = _read_bl(["district", "building_id", "cls"])
    for run in runs:
        ids = _ids_for(run, district, bl)
        if ids is None or (Path(SCRATCH) / f"part_{run}_{district}.csv").exists():
            continue
        t0 = time.time()
        worker(run, district, ids, str(Path(SCRATCH) / f"out_{run}_{district}"), memo=True)
        print(run, district, "done", f"{time.time() - t0:.0f}s", flush=True)


def _alive(run, d, multi=False):
    multi_clause = " -or $_.CommandLine -like '*multi*'" if multi else ""
    cmd = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*dryrun*' -and "
           f"$_.CommandLine -like '*--district {d}*' -and ($_.CommandLine -like '*--run {run} *'{multi_clause})"
           "} | Measure-Object | Select-Object -ExpandProperty Count")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    try:
        return int(r.stdout.strip()) > 0
    except ValueError:
        return False


def orchestrate_pool():
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(SCRATCH, exist_ok=True)
    bl = _read_bl(["district", "building_id", "cls"])
    est = {"ES-MAD-BERRUGUETE": (90, 50), "GB-LDN-STDUNSTANS": (35, 39), "IT-BOL-GALVANI2": (35, 33), "FR-LYO-HAUTCOEURPENTES": (22, 6)}
    jobs = []
    for d in DISTRICTS:
        for r in RUNS:
            if (Path(SCRATCH) / f"part_{r}_{d}.csv").exists():
                continue
            ids = _ids_for(r, d, bl)
            if ids is None:
                continue
            jobs.append((-est[d][0 if r in FULL else 1], r, d, ids))
    jobs.sort()
    errors = []

    def one(j):
        _, r, d, ids = j
        t0 = time.time()
        log = open(Path(SCRATCH) / f"log_{r}_{d}.txt", "w")
        p = subprocess.run([sys.executable, __file__, "worker", "--run", r, "--district", d, "--ids", ids,
                            "--out", str(Path(SCRATCH) / f"out_{r}_{d}"), "--ref", REF], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        log.close()
        print(r, d, "rc", p.returncode, f"{time.time() - t0:.0f}s", flush=True)
        if p.returncode:
            errors.append((r, d))

    print("jobs", len(jobs), flush=True)
    with ThreadPoolExecutor(MAX_PROCS) as ex:
        list(ex.map(one, jobs))
    print("errors", errors)


def _alive_pairs():
    cmd = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*dryrun*' -and "
           "$_.CommandLine -like '* worker *'} | ForEach-Object { $_.CommandLine }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    pairs = set()
    for line in r.stdout.splitlines():
        m = re.search(r"--run (\S+) --district (\S+)", line)
        if m:
            pairs.add((m.group(1), m.group(2)))
    return pairs


def orchestrate_pool2():
    os.makedirs(SCRATCH, exist_ok=True)
    bl = _read_bl(["district", "building_id", "cls"])
    est = {"ES-MAD-BERRUGUETE": (90, 50), "GB-LDN-STDUNSTANS": (35, 39), "IT-BOL-GALVANI2": (35, 33), "FR-LYO-HAUTCOEURPENTES": (22, 6)}
    jobs = []
    for d in DISTRICTS:
        for r in RUNS:
            ids = _ids_for(r, d, bl)
            if ids is not None:
                jobs.append((-est[d][0 if r in FULL else 1], r, d, ids))
    jobs.sort()
    started = {}
    while True:
        alive = _alive_pairs()
        pending = [j for j in jobs if not (Path(SCRATCH) / f"part_{j[1]}_{j[2]}.csv").exists() and (j[1], j[2]) not in alive
                   and started.get((j[1], j[2]), 0) < 1]
        if not pending and not alive:
            break
        if pending and len(alive) < MAX_PROCS:
            _, r, d, ids = pending[0]
            log = open(Path(SCRATCH) / f"log_{r}_{d}.txt", "w")
            subprocess.Popen([sys.executable, __file__, "worker", "--run", r, "--district", d, "--ids", ids,
                              "--out", str(Path(SCRATCH) / f"out_{r}_{d}"), "--ref", REF], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            started[(r, d)] = started.get((r, d), 0) + 1
            print("start", r, d, time.strftime("%H:%M:%S"), flush=True)
            time.sleep(20)
            continue
        time.sleep(20)
    missing = [(j[1], j[2]) for j in jobs if not (Path(SCRATCH) / f"part_{j[1]}_{j[2]}.csv").exists()]
    print("errors", missing)


def orchestrate_chains():
    os.makedirs(SCRATCH, exist_ok=True)
    errors = []

    def go(d, tag, names):
        log = open(Path(SCRATCH) / f"log_multi_{tag}_{d}.txt", "a")
        p = subprocess.run([sys.executable, __file__, "multi", "--district", d, "--runs", ",".join(names), "--ref", REF],
                           stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        log.close()
        print("chain", tag, d, "rc", p.returncode, flush=True)
        if p.returncode:
            errors.append((tag, d))

    threads = []
    for d in DISTRICTS:
        threads.append(threading.Thread(target=go, args=(d, "full", FULL)))
        threads.append(threading.Thread(target=go, args=(d, "ladder", LADDER)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("errors", errors)


def orchestrate_resume():
    os.makedirs(SCRATCH, exist_ok=True)
    bl = _read_bl(["district", "building_id", "cls"])
    errors = []

    def part(run, d):
        return (Path(SCRATCH) / f"part_{run}_{d}.csv").exists()

    def full_chain(d):
        for run in FULL:
            while not part(run, d) and _alive(run, d):
                time.sleep(20)
            if part(run, d):
                continue
            t0 = time.time()
            log = open(Path(SCRATCH) / f"log_{run}_{d}.txt", "w")
            p = subprocess.run([sys.executable, __file__, "worker", "--run", run, "--district", d, "--ids", "all",
                                "--out", str(Path(SCRATCH) / f"out_{run}_{d}"), "--ref", REF], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            log.close()
            print(run, d, "rc", p.returncode, f"{time.time() - t0:.0f}s", flush=True)
            if p.returncode:
                errors.append((run, d))

    def ladder_chain(d):
        while any(_alive(r, d, True) for r in LADDER if not part(r, d)):
            time.sleep(20)
        todo = [r for r in LADDER if not part(r, d) and _ids_for(r, d, bl) is not None]
        if not todo:
            return
        log = open(Path(SCRATCH) / f"log_multi_{d}.txt", "a")
        p = subprocess.run([sys.executable, __file__, "multi", "--district", d, "--runs", ",".join(todo), "--ref", REF],
                           stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        log.close()
        print("multi", d, "rc", p.returncode, flush=True)
        if p.returncode:
            errors.append(("multi", d))

    threads = []
    for d in DISTRICTS:
        threads.append(threading.Thread(target=full_chain, args=(d,)))
        threads.append(threading.Thread(target=ladder_chain, args=(d,)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("errors", errors)


def orchestrate(runs):
    os.makedirs(SCRATCH, exist_ok=True)
    bl = _read_bl(["district", "building_id", "cls"])
    sem = threading.Semaphore(MAX_PROCS)
    errors = []

    def one(run, d):
        ids = _ids_for(run, d, bl)
        if ids is None:
            return
        part = Path(SCRATCH) / f"part_{run}_{d}.csv"
        if part.exists():
            return
        with sem:
            t0 = time.time()
            log = open(Path(SCRATCH) / f"log_{run}_{d}.txt", "w")
            p = subprocess.run([sys.executable, __file__, "worker", "--run", run, "--district", d, "--ids", ids,
                                "--out", str(Path(SCRATCH) / f"out_{run}_{d}"), "--ref", REF], stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
            log.close()
            print(run, d, "rc", p.returncode, f"{time.time() - t0:.0f}s", flush=True)
            if p.returncode:
                errors.append((run, d))

    def chain(names, d):
        for n in names:
            one(n, d)

    threads = []
    for d in DISTRICTS:
        threads.append(threading.Thread(target=chain, args=([r for r in FULL if r in runs], d)))
        threads.append(threading.Thread(target=chain, args=([r for r in LADDER if r in runs], d)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("errors", errors)


def summarize():
    bl = _read_bl(["district", "building_id", "cls"])
    rows = []
    for run in RUNS:
        parts = [SCRATCH + f"part_{run}_{d}.csv" for d in DISTRICTS if os.path.exists(SCRATCH + f"part_{run}_{d}.csv")]
        if not parts:
            continue
        df = pd.concat([pd.read_csv(p, dtype={"idf_sha256": str, "base_sha256": str}) for p in parts], ignore_index=True)
        df.to_csv(OUT + f"dryrun_{run}{SUFFIX}.csv", index=False)
        new_rows = int((df.moved_reason == "not_in_baseline").sum())
        df = df[df.moved_reason != "not_in_baseline"]
        ok = df[df.base_cls.isin(["OK", "S1_one_flat_per_floor_by_data"])]
        unres = df[df.base_cls.isin(UNRESOLVED)]
        unres_all = int(bl.cls.isin(UNRESOLVED).sum())
        worse = df[df.new_cls.map(RANK) > df.base_cls.map(RANK)]
        s = dict(run=run, homes=len(df), not_in_baseline=new_rows, not_prepared=int((df.new_cls == 'NOT_PREPARED').sum()), class_moved=int(df.class_moved.sum()), sha_changed=int(df.sha_changed.sum()),
                 moved=int(df.moved.sum()), baseline_ok_in_run=len(ok), baseline_ok_moved=int(ok.moved.sum()),
                 baseline_ok_class_moved=int(ok.class_moved.sum()),
                 unresolved_in_run=len(unres), resolved_to_OK=int((unres.new_cls == "OK").sum()),
                 resolved_to_OK_or_V3=int(unres.new_cls.isin(["OK", "V3_divided_wrapped_flat"]).sum()),
                 improved_class=int((unres.new_cls.map(RANK) < unres.base_cls.map(RANK)).sum()),
                 homes_worse=len(worse), unresolved_total=unres_all,
                 storeys_fail_verdict=int(df.n_storeys_fail_verdict.sum()))
        for c in CH:
            s[f"storeys_fail_{c}"] = int(df[f"n_storeys_{c}_fail"].sum())
        rows.append(s)
    pd.DataFrame(rows).to_csv(OUT + f"dryrun_summary{SUFFIX}.csv", index=False)
    print(pd.DataFrame(rows).T.to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["worker", "run", "resume", "chains", "pool", "pool2", "multi", "summarize"])
    ap.add_argument("--run")
    ap.add_argument("--district")
    ap.add_argument("--ids")
    ap.add_argument("--out")
    ap.add_argument("--runs", default="")
    ap.add_argument("--ref", choices=["0908", "1006"], default="0908")
    a = ap.parse_args()
    _set_ref(a.ref)
    if a.mode == "worker":
        worker(a.run, a.district, a.ids, a.out)
    elif a.mode == "multi":
        multi(a.district, a.runs.split(","))
    elif a.mode == "pool2":
        orchestrate_pool2()
    elif a.mode == "pool":
        orchestrate_pool()
    elif a.mode == "chains":
        orchestrate_chains()
    elif a.mode == "resume":
        orchestrate_resume()
    elif a.mode == "run":
        orchestrate(set(a.runs.split(",")) if a.runs else set(RUNS))
    else:
        summarize()

