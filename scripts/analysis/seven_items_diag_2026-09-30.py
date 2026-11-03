from __future__ import annotations

import csv
import math
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUT_CSV = OUT_DIR / "seven_items_diag_2026-09-30.csv"
ADOPTED = OUT_DIR / "open65_reparse_fleet_eui_2026-09-29.csv"
FIXRERUN = OUT_DIR / "open38_fix_rerun_2026-09-30.csv"
TMP = Path(tempfile.gettempdir()) / "ubem_validation"
WORK = TMP / "open38_fix_rerun_2026-09-30_full"
FETCHED = WORK / "fetched" / "out"
EVID = REPO / "evidence" / "open48_refleet4"
FETCH65 = TMP / "open65_reparse_2026-09-29"
BASELINE = Path(r"C:\Users\o_iseri\Desktop\NEXA-desktop\Content\00.BaselineBuildings_NUs_v231")
PROTO = BASELINE / "ASHRAE901_HotelSmall_STD2022_Buffalo.idf"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
OPEN69_BUILDINGS = ["way/472960972", "way/472961034", "way/472961088", "way/472961171",
                    "way/472961091", "way/472961164", "way/428015178"]

ROWS: list[dict] = []


def add(item: str, case: str, field: str, value) -> None:
    ROWS.append({"item": item, "case": case, "field": field, "value": value})


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def parse_idf(path: Path) -> list[tuple[str, list[str]]]:
    objs, cur = [], []
    for line in path.read_text(errors="replace").splitlines():
        code = line.split("!")[0]
        if not code.strip():
            continue
        cur.append(code)
        if ";" in code:
            txt = " ".join(cur)
            cur = []
            parts = [p.strip() for p in txt.rsplit(";", 1)[0].split(",")]
            objs.append((parts[0].upper(), parts[1:]))
    return objs


def num(s, default=0.0) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def newell(vs):
    sx = sy = sz = 0.0
    n = len(vs)
    for i in range(n):
        x1, y1, z1 = vs[i]
        x2, y2, z2 = vs[(i + 1) % n]
        sx += (y1 - y2) * (z1 + z2)
        sy += (z1 - z2) * (x1 + x2)
        sz += (x1 - x2) * (y1 + y2)
    return sx, sy, sz


def area_tilt(vs):
    sx, sy, sz = newell(vs)
    m = math.sqrt(sx * sx + sy * sy + sz * sz)
    if m == 0:
        return 0.0, float("nan")
    return 0.5 * m, math.degrees(math.acos(max(-1.0, min(1.0, sz / m))))


def is_convex(vs) -> bool:
    n = len(vs)
    if n < 4:
        return True
    nx, ny, nz = (abs(c) for c in newell(vs))
    drop = 0 if nx >= ny and nx >= nz else (1 if ny >= nz else 2)
    keep = [i for i in range(3) if i != drop]
    pts = [(v[keep[0]], v[keep[1]]) for v in vs]
    sign = 0
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cx, cy = pts[(i + 2) % n]
        cr = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cr) < 1e-9:
            continue
        s = 1 if cr > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return True


def coords(f: list[str], start: int):
    co = f[start:]
    return [tuple(num(x) for x in co[3 * k:3 * k + 3]) for k in range(len(co) // 3)]


class Model:
    def __init__(self, path: Path):
        self.path = path
        self.objs = parse_idf(path)
        self.materials: dict[str, str] = {}
        self.constructions: dict[str, list[str]] = {}
        self.surfaces: dict[str, dict] = {}
        self.zone_f: dict[str, list[str]] = {}
        self.shading: list[dict] = []
        for typ, f in self.objs:
            if typ == "MATERIAL":
                self.materials[f[0].upper()] = (
                    f"{f[0]}[thk={f[2]};k={f[3]};rho={f[4]};cp={f[5]}]")
            elif typ == "MATERIAL:NOMASS":
                self.materials[f[0].upper()] = f"{f[0]}[R={f[2]}]"
            elif typ.startswith("WINDOWMATERIAL:"):
                self.materials[f[0].upper()] = f"{f[0]}[{','.join(f[1:4])}]"
            elif typ == "CONSTRUCTION":
                self.constructions[f[0].upper()] = f[1:]
            elif typ == "ZONE":
                self.zone_f[f[0].upper()] = f
            elif typ in ("BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
                if typ == "BUILDINGSURFACE:DETAILED":
                    si = next(i for i, x in enumerate(f) if x.lower() in ("sunexposed", "nosun"))
                    vs = coords(f, si + 4)
                    rec = dict(kind="building", name=f[0], type=f[1], cons=f[2], zone=f[3],
                               bc=f[si - 2], bco=f[si - 1], sun=f[si], vs=vs)
                else:
                    vs = coords(f, 10) if len(f) > 10 else []
                    nv = int(num(f[9], len(vs))) if len(f) > 9 else len(vs)
                    vs = vs[:nv] if nv else vs
                    rec = dict(kind="fenestration", name=f[0], type=f[1], cons=f[2], zone="",
                               bc="outdoors", bco=f[3], sun="", vs=vs)
                self.surfaces[f[0].upper()] = rec
            elif typ.startswith("SHADING:") and typ.endswith(":DETAILED"):
                vs = coords(f, 3)
                self.shading.append(dict(kind=typ, name=f[0], vs=vs))

    def layers(self, cons: str) -> str:
        c = self.constructions.get(cons.upper())
        if c is None:
            return "MISSING"
        return ";".join(self.materials.get(m.upper(), m) for m in c)

    def by_zone(self, zone: str) -> list[dict]:
        return [s for s in self.surfaces.values()
                if s["kind"] == "building" and s["zone"].upper() == zone.upper()]

    def count(self, typ: str) -> int:
        return sum(1 for t, _ in self.objs if t == typ)


def eio_zones(eio: Path) -> dict[str, dict]:
    hdr, zones = None, {}
    if not eio.exists():
        return zones
    for l in eio.read_text(errors="replace").splitlines():
        if l.startswith("! <Zone Information>"):
            hdr = [h.strip() for h in l.split(",")]
        elif l.startswith(" Zone Information,") and hdr:
            f = [x.strip() for x in l.split(",")]
            d = dict(zip(hdr, f))
            zones[f[1].upper()] = dict(
                floor=num(d.get("Floor Area {m2}")), volume=num(d.get("Volume {m3}")),
                ceiling=num(d.get("Ceiling Height {m}")), mult=num(d.get("Zone Multiplier"), 1.0),
                zmin=num(d.get("Minimum Z {m}")), zmax=num(d.get("Maximum Z {m}")))
    return zones


def first_severe(err: Path) -> tuple[str, str]:
    lines = err.read_text(errors="replace").splitlines() if err.exists() else []
    for i, l in enumerate(lines):
        if re.search(r"\*\* +(Severe|Fatal) +\*\*", l):
            blk = [l.strip()]
            for k in lines[i + 1:i + 12]:
                if "~~~" in k:
                    blk.append(k.strip())
                else:
                    break
            return " || ".join(blk), "\n".join(blk)
    return "", ""


def fmt(x) -> str:
    return f"{x:.6g}" if isinstance(x, float) else str(x)


def surface_record(m: Model, zone: str, surf: str, eio: dict, meta: dict) -> dict:
    s = m.surfaces.get(surf.upper())
    z = eio.get(zone.upper(), {})
    rec = dict(meta)
    rec.update(zone=zone, surface=surf,
               zone_floor_m2=z.get("floor", ""), zone_volume_m3=z.get("volume", ""),
               zone_ceiling_height_m=z.get("ceiling", ""), zone_multiplier=z.get("mult", ""))
    if s:
        a, t = area_tilt(s["vs"])
        rec.update(surf_type=s["type"], construction=s["cons"], layers=m.layers(s["cons"]),
                   outside_bc=s["bc"], partner_surface=s["bco"] if s["bc"].lower() == "surface" else "",
                   surf_area_m2=a, surf_vertices=len(s["vs"]), surf_tilt_deg=t)
    return rec


def build_fail_records(meta_bld: dict) -> list[dict]:
    fx = pd.read_csv(FIXRERUN)
    fx = fx[(fx["group"].str.contains("open38|oom")) & (fx["terminal"] != "completed")]
    out = []
    for _, r in fx.iterrows():
        if r["osm_id"] not in OPEN69_BUILDINGS or not str(r["cause_class"]).startswith("C2"):
            continue
        case = r["name"]
        err = FETCHED / case / "eplusout.err"
        sev, _ = first_severe(err)
        zm = re.search(r'zone="([^"]+)"', sev)
        sm = re.search(r'surface="([^"]+)"', sev)
        tm = re.search(r"out of bounds [\[(](-?[\d.]+)", sev)
        stem = r["stem"]
        m = Model(WORK / r["cell"] / r["mode"] / "idfs" / f"{stem}.idf")
        eio = eio_zones(FETCHED / case / "eplusout.eio")
        meta = dict(group="fail", case=case, cell=r["cell"], mode=r["mode"], osm_id=r["osm_id"],
                    temp_c=tm.group(1) if tm else "")
        meta.update(meta_bld_for(r["cell"], r["osm_id"], m, eio))
        out.append(surface_record(m, zm.group(1), sm.group(1), eio, meta))
    return out


_GPKG: dict[str, pd.DataFrame] = {}


def meta_bld_for(cell: str, osm_id: str, m: Model, eio: dict) -> dict:
    if cell not in _GPKG:
        import geopandas as gpd
        _GPKG[cell] = gpd.read_file(str(EVID / cell / "01_buildings.gpkg")).set_index("osm_id")
    g = _GPKG[cell].loc[osm_id]
    fidx = sorted({int(mm.group(1)) for z in m.zone_f
                   if (mm := re.search(r"_F(\d+)_", z))})
    return dict(gpkg_levels=g["levels"], gpkg_height_m=g["height_m"],
                provenance_levels=g["provenance_levels"],
                footprint_area_m2=g["footprint_area_m2"],
                modelled_storeys=len(fidx) if fidx else "", n_zones=len(m.zone_f))


def build_control_records() -> list[dict]:
    a = pd.read_csv(ADOPTED)
    w = a[(a["cell"] == "la_rural") & (a["archetype_id"] == "Warehouse")
          & (a["parse_status"] == "success")]
    out = []
    for _, r in w.iterrows():
        stem = r["stem"]
        m = Model(EVID / "la_rural" / "fleet_staging" / "idfs" / f"{stem}.idf")
        eio = eio_zones(FETCH65 / "la_rural" / stem / "eplusout.eio")
        if set(m.zone_f) != set(eio):
            add("a_warning", f"auto__la_rural__{stem}", "idf_zones_vs_adopted_eio_zones",
                f"idf={len(m.zone_f)} eio={len(eio)} equal={set(m.zone_f) == set(eio)}")
        meta = dict(group="control", case=f"auto__la_rural__{stem}", cell="la_rural", mode="auto",
                    osm_id=r["osm_id"], temp_c="")
        meta.update(meta_bld_for("la_rural", r["osm_id"], m, eio))
        found = False
        for z in m.zone_f:
            if re.search(r"_F2_(CORE|WHOLE)$", z):
                for s in m.by_zone(z):
                    if s["type"].lower() in ("floor", "roof", "ceiling"):
                        out.append(surface_record(m, z, s["name"], eio, meta))
                        found = True
        if not found:
            out.append(dict(meta, zone="", surface="(no storey-2 core/whole zone)"))
    return out


def item_a() -> None:
    recs = build_fail_records({}) + build_control_records()
    for r in recs:
        key = f"{r['case']}|{r['surface']}|{r.get('surf_type', '')}"
        for k, v in r.items():
            if k not in ("case", "surface"):
                add("a_row", key, k, fmt(v) if v != "" else "")
    df = pd.DataFrame(recs)
    df["building_h_est"] = pd.to_numeric(df["zone_ceiling_height_m"], errors="coerce")
    fail = df[df["group"] == "fail"]
    ctl = df[(df["group"] == "control") & (df["zone"] != "")]
    add("a_population", "summary", "fail_rows", len(fail))
    add("a_population", "summary", "control_rows_with_surface", len(ctl))
    add("a_population", "summary", "control_buildings", df[df["group"] == "control"]["osm_id"].nunique())
    add("a_population", "summary", "control_buildings_with_storey2_zone",
        ctl["osm_id"].nunique())
    cols = ["surf_type", "construction", "layers", "outside_bc", "partner_surface", "surf_area_m2",
            "surf_vertices", "surf_tilt_deg", "zone_floor_m2", "zone_volume_m3",
            "zone_ceiling_height_m", "zone_multiplier", "gpkg_levels", "gpkg_height_m",
            "footprint_area_m2", "modelled_storeys", "n_zones"]
    for tag, fsub in (("all_modes", fail), ("auto_only", fail[fail["mode"] == "auto"])):
        for c in cols:
            fv, cv = fsub[c], ctl[c]
            nf = pd.to_numeric(fv, errors="coerce")
            nc = pd.to_numeric(cv, errors="coerce")
            key = f"{tag}:{c}"
            if nf.notna().sum() == len(fv.dropna()) and nc.notna().sum() == len(cv.dropna()) and nf.notna().any():
                fmin, fmax, cmin, cmax = nf.min(), nf.max(), nc.min(), nc.max()
                sep = bool(fmax < cmin or fmin > cmax)
                add("a_separation", key, "fail_range", f"{fmin:.6g}..{fmax:.6g}")
                add("a_separation", key, "control_range", f"{cmin:.6g}..{cmax:.6g}")
                add("a_separation", key, "separates", sep)
            else:
                fs = {x for x in map(str, fv.dropna()) if x not in ("", "nan")}
                cs = {x for x in map(str, cv.dropna()) if x not in ("", "nan")}
                add("a_separation", key, "fail_values", "|".join(sorted(fs))[:400])
                add("a_separation", key, "control_values", "|".join(sorted(cs))[:400])
                add("a_separation", key, "separates", (not (fs & cs)) if fs and cs else "n/a")
    fb = df[df["group"] == "fail"]["osm_id"].nunique()
    add("a_population", "summary", "fail_buildings", fb)
    add("a_population", "summary", "control_buildings_with_storey2_zone_ids",
        "|".join(sorted(ctl["osm_id"].unique())))
    cb = df[df["group"] == "control"].drop_duplicates("osm_id")
    add("a_population", "summary", "control_buildings_by_modelled_storeys",
        str(cb["modelled_storeys"].value_counts().sort_index().to_dict()))
    add("a_population", "summary", "auto_fail_buildings_modelled_storeys",
        str(df[(df["group"] == "fail") & (df["mode"] == "auto")].drop_duplicates("osm_id")["modelled_storeys"].to_dict()))


def item_b() -> None:
    def zone_objs(m: Model, zone: str):
        res = []
        for typ, f in m.objs:
            if typ in ("ZONE", "BUILDINGSURFACE:DETAILED", "FENESTRATIONSURFACE:DETAILED"):
                continue
            if any(x.upper() == zone.upper() for x in f):
                res.append((typ, f))
        return res

    def surf_sig(m: Model, zone: str) -> dict:
        sig = {}
        for s in m.by_zone(zone):
            a, t = area_tilt(s["vs"])
            key = f"{s['type']}|{s['bc']}"
            sig.setdefault(key, set()).add(m.layers(s["cons"]))
        return sig

    def zone_area(m: Model, zone: str) -> float:
        return sum(area_tilt(s["vs"])[0] for s in m.by_zone(zone) if s["type"].lower() == "floor")

    pm = Model(PROTO)
    lz = "LaundryRoomFlr1"
    pg = [(t, f) for t, f in zone_objs(pm, lz) if t == "GASEQUIPMENT"]
    proto_gas = pg[0][1]
    for i, v in enumerate(proto_gas):
        add("b_proto", "DOE_HotelSmall", f"GasEquipment[{i}]", v)
    psig = surf_sig(pm, lz)
    for k, v in psig.items():
        add("b_proto", "DOE_HotelSmall", f"surf_layers[{k}]", " / ".join(sorted(v)))
    add("b_proto", "DOE_HotelSmall", "zone_floor_m2", f"{zone_area(pm, lz):.4f}")
    add("b_proto", "DOE_HotelSmall", "zone_fields", "|".join(pm.zone_f[lz.upper()]))
    ptypes = Counter(t for t, _ in zone_objs(pm, lz))
    cases = ["layout_assign__la_centre__way_427942886", "layout_assign__la_urban__relation_6374725",
             "layout_assign__la_urban__way_401910463", "layout_assign__la_urban__way_428846131",
             "layout_assign__nyc_rural__way_965718400", "layout_assign__nyc_rural__way_965718402",
             "layout_assign__nyc_rural__way_965718403"]
    diff_count: Counter = Counter()
    gas_names = ("name", "zone", "schedule", "method", "design_level_W", "W_per_area", "W_per_person",
                 "fraction_latent", "fraction_radiant", "fraction_lost", "co2", "end_use")
    for c in cases:
        _, cell, stem = c.split("__")
        m = Model(WORK / cell / "layout_assign" / "idfs" / f"{stem}.idf")
        gs = [(t, f) for t, f in zone_objs(m, lz) if t == "GASEQUIPMENT"]
        cg = gs[0][1]
        for i in range(max(len(cg), len(proto_gas))):
            a = cg[i] if i < len(cg) else ""
            b = proto_gas[i] if i < len(proto_gas) else ""
            if a != b:
                nm = gas_names[i] if i < len(gas_names) else str(i)
                diff_count[f"GasEquipment.{nm}"] += 1
                add("b_diff", c, f"GasEquipment.{nm}", f"case={a} | prototype={b}")
        add("b_case", c, "GasEquipment_dryer_count_in_zone", len(gs))
        csig = surf_sig(m, lz)
        for k in sorted(set(psig) | set(csig)):
            a, b = csig.get(k, set()), psig.get(k, set())
            if a != b:
                diff_count[f"surf_layers[{k}]"] += 1
                add("b_diff", c, f"surf_layers[{k}]", f"case={' / '.join(sorted(a))} | prototype={' / '.join(sorted(b))}")
        fa = zone_area(m, lz)
        add("b_case", c, "zone_floor_m2", f"{fa:.4f}")
        add("b_case", c, "dryer_W_per_m2_case", f"{num(cg[4]) / fa:.3f}" if fa else "")
        add("b_case", c, "dryer_W_per_m2_prototype", f"{num(proto_gas[4]) / zone_area(pm, lz):.3f}")
        ctypes = Counter(t for t, _ in zone_objs(m, lz))
        for t in sorted(set(ptypes) | set(ctypes)):
            if ptypes.get(t, 0) != ctypes.get(t, 0):
                diff_count[f"zone_ref_count[{t}]"] += 1
                add("b_diff", c, f"zone_ref_count[{t}]", f"case={ctypes.get(t, 0)} | prototype={ptypes.get(t, 0)}")
        zf, pz = m.zone_f[lz.upper()], pm.zone_f[lz.upper()]
        for i, (x, y) in enumerate(zip(zf[1:], pz[1:]), start=1):
            if x != y:
                diff_count[f"Zone.field[{i}]"] += 1
                add("b_diff", c, f"Zone.field[{i}]", f"case={x} | prototype={y}")
    for k, v in sorted(diff_count.items()):
        add("b_diff_summary", "all_7_cases", k, f"differs in {v} of 7")


def _min_area(args):
    cell, stem = args
    p = FETCH65 / cell / stem / "eplusout.sql"
    try:
        with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as c:
            rows = [r[0] for r in c.execute("select FloorArea from Zones")]
    except sqlite3.Error:
        return cell, stem, None, None, None
    pos = [x for x in rows if x and x > 0]
    return cell, stem, (min(pos) if pos else None), len(rows), sum(1 for x in rows if not x or x <= 0)


def item_c() -> None:
    a = pd.read_csv(ADOPTED)
    jobs = list(zip(a["cell"], a["stem"]))
    with Pool(6) as pool:
        res = pool.map(_min_area, jobs, chunksize=50)
    df = pd.DataFrame(res, columns=["cell", "stem", "min_area", "n_zones", "n_zero_zones"])
    df = df.merge(a[["stem", "cell", "osm_id", "archetype_id"]], on=["stem", "cell"])
    add("c_population", "adopted", "buildings", len(df))
    add("c_population", "adopted", "sql_unreadable_or_missing", int(df["min_area"].isna().sum()))
    add("c_population", "adopted", "buildings_with_zero_area_zone", int((df["n_zero_zones"].fillna(0) > 0).sum()))
    hit = df[(df["min_area"] >= 0.5) & (df["min_area"] < 2.0)]
    add("c_count", "min_zone_floor_in_[0.5,2.0)", "buildings", len(hit))
    add("c_count", "min_zone_floor_<0.5", "buildings", int((df["min_area"] < 0.5).sum()))
    for cell, n in hit.groupby("cell").size().items():
        add("c_count_by_cell", cell, "buildings", int(n))
    for arch, n in hit.groupby("archetype_id").size().items():
        add("c_count_by_archetype", arch, "buildings", int(n))
    for _, r in hit.sort_values(["cell", "osm_id"]).iterrows():
        add("c_building", r["osm_id"], "cell|archetype|min_zone_floor_m2",
            f"{r['cell']}|{r['archetype_id']}|{r['min_area']:.4f}")


def item_d() -> None:
    case = "auto__la_rural__way_472961047"
    sev, blk = first_severe(FETCHED / case / "eplusout.err")
    add("d_err", case, "first_severe_block", sev)
    fatals = [l.strip() for l in (FETCHED / case / "eplusout.err").read_text(errors="replace").splitlines()
              if re.search(r"\*\* +Fatal +\*\*", l)]
    add("d_err", case, "first_fatal_line", fatals[0] if fatals else "")
    m = Model(WORK / "la_rural" / "auto" / "idfs" / "way_472961047.idf")
    cand = []
    for s in m.surfaces.values():
        if s["kind"] == "building" and s["sun"].lower() == "sunexposed":
            cand.append((f"building:{s['type']}:bc={s['bc']}", s["name"], s["vs"]))
    for s in m.shading:
        cand.append((s["kind"], s["name"], s["vs"]))
    add("d_geom", case, "candidate_casting_surfaces_sunexposed_building_plus_shading", len(cand))
    nonconvex = [(k, n, vs) for k, n, vs in cand if not is_convex(vs)]
    add("d_geom", case, "nonconvex_candidates", len(nonconvex))
    for k, n, vs in nonconvex:
        a, t = area_tilt(vs)
        add("d_casting", n, "kind|vertices|area_m2|tilt_deg", f"{k}|{len(vs)}|{a:.3f}|{t:.1f}")
    sc = [(t, f) for t, f in m.objs if t == "SHADOWCALCULATION"]
    add("d_shadowcalc", case, "ShadowCalculation_objects_in_IDF", len(sc))
    for t, f in sc:
        add("d_shadowcalc", case, "ShadowCalculation_as_written", ",".join(f))
    add("d_shadowcalc", case, "shading_detailed_objects", len(m.shading))
    sb = [(t, f) for t, f in m.objs if t == "BUILDING"]
    add("d_shadowcalc", case, "Building_solar_distribution", sb[0][1][4] if sb else "")


def item_e() -> None:
    def query(cmd: str, head: str) -> str:
        out = ""
        for _ in range(3):
            out = _ssh(cmd)
            if out.startswith(head):
                return out
        raise RuntimeError(f"sinfo failed, remote text: {out[:400]}")

    out1 = query('sinfo -o "%P %m %c"', "PARTITION")
    out2 = query('sinfo -p ps -N -o "%N %m %c"', "NODELIST")
    for l in out1.splitlines():
        if l.startswith("ps") or l.startswith("PARTITION"):
            add("e_sinfo", "partition_ps", "sinfo -o '%P %m %c'", l)
    mems = []
    for l in out2.splitlines()[1:]:
        p = l.split()
        if len(p) >= 3 and p[1].isdigit():
            mems.append((int(p[1]), p[0]))
    add("e_sinfo", "partition_ps", "nodes", len(mems))
    add("e_sinfo", "partition_ps", "max_memory_per_node_MB", max(mems)[0])
    add("e_sinfo", "partition_ps", "max_memory_node", max(mems)[1])
    add("e_sinfo", "partition_ps", "min_memory_per_node_MB", min(mems)[0])
    add("e_sinfo", "partition_ps", "nodes_with_ge_64GB", sum(1 for x, _ in mems if x >= 64000))
    m = Model(WORK / "la_centre" / "auto" / "idfs" / "way_319507579.idf")
    add("e_model", "auto__la_centre__way_319507579", "zones", m.count("ZONE"))
    add("e_model", "auto__la_centre__way_319507579", "buildingsurface_detailed", m.count("BUILDINGSURFACE:DETAILED"))
    add("e_model", "auto__la_centre__way_319507579", "fenestrationsurface_detailed", m.count("FENESTRATIONSURFACE:DETAILED"))
    add("e_model", "auto__la_centre__way_319507579", "shading_detailed", len(m.shading))
    add("e_model", "auto__la_centre__way_319507579", "surfaces_total_building_plus_fenestration",
        m.count("BUILDINGSURFACE:DETAILED") + m.count("FENESTRATIONSURFACE:DETAILED"))
    add("e_model", "auto__la_centre__way_319507579", "output_variable", m.count("OUTPUT:VARIABLE"))
    add("e_model", "auto__la_centre__way_319507579", "idf_bytes", (WORK / "la_centre" / "auto" / "idfs" / "way_319507579.idf").stat().st_size)


def main() -> None:
    sys.path.insert(0, str(REPO))
    item_a()
    item_b()
    item_c()
    item_d()
    item_e()
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "case", "field", "value"])
        w.writeheader()
        w.writerows(ROWS)
    print(len(ROWS), "rows ->", OUT_CSV)
    print(Counter(r["item"] for r in ROWS))


if __name__ == "__main__":
    main()
