from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import re
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from openubem.geometry.european_residential import allocate_european_dwellings
try:
    from scripts.run_eu_s2_district_campaign import ES_SIDECAR
except Exception:
    ES_SIDECAR = ROOT / "openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv"
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
DATA_3D = ROOT / "openubem" / "outputs" / "3D"
OUT_DIR = EVIDENCE / "integrity_2026-10-02"
DISTRICTS = {
    "ES": "ES-MAD-BERRUGUETE",
    "FR": "FR-LYO-HAUTCOEURPENTES",
    "GB": "GB-LDN-STDUNSTANS",
    "IT": "IT-BOL-GALVANI2",
}
SHIFTED = ("FR", "IT")
MAX_WORKERS = 10
STOREY_HEIGHT_M = 3.0
CHECKS = ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11", "I12", "I13"]
LEVEL_TOL_M = 0.02
I2_TOL = 0.01
I3_LOW, I3_HIGH = 0.97, 1.03
I4_TOL_M = 0.05
I5_MAX_ZONE_M = 4.5
I6_TOL = 0.01
I7_TOL = 0.001
I9_TOL = 0.02
I11_RANGE_M = 20000.0
I11_CENTROID_TOL_M = 1.0
I13_TOL = 0.01
I6_ABOVE_Z_TOL_M = 0.05
I6_ABOVE_OVERLAP_M2 = 0.01
I10_TOL = 0.01
IDF_HEIGHT_TOL_M = 0.05
OLD_IDF_TREES = ("{d}/idfs", "{d}_final_2026-09-07/idfs", "{d}_recut_2026-09-08/idfs")
LAYOUT_DIRS = ("{d}_layouts_2026-09-08b", "{d}_layouts_2026-09-08", "{d}/layouts")
I10_HOURS = 8760
I10_SUBCATEGORY = "EU_Step8_InternalGains"
I10_LEGACY_SUBCATEGORY = "EU_InternalGains"
UNCONDITIONED_RE = re.compile(r"core|circulation", re.IGNORECASE)
RERUN_DIR = EVIDENCE / "division_residual_2026-09-29"
ZERO_FLOOR_STEM = "97d478bc56840531"
CORE_RULE_STEMS = {
    "bb4d3f44d4fbe5b1",
    "bfbc1caab1a332a4",
    "933a2f079f1d6277",
    "05b52a0da00a6046",
    "1773a1e9f64767b1",
    "97d478bc56840531",
    "a53d307eac631355",
    "cc55f139215783a3",
}
BC_VALUES = {"OUTDOORS", "GROUND", "SURFACE", "ADIABATIC", "ZONE", "OTHERSIDECOEFFICIENTS", "OTHERSIDECONDITIONSMODEL", "GROUNDFCFACTORMETHOD", "GROUNDSLABPREPROCESSORAVERAGE", "GROUNDSLABPREPROCESSORCORE", "GROUNDSLABPREPROCESSORPERIMETER", "GROUNDBASEMENTPREPROCESSORAVERAGEWALL", "GROUNDBASEMENTPREPROCESSORAVERAGEFLOOR", "GROUNDBASEMENTPREPROCESSORUPPERWALL", "GROUNDBASEMENTPREPROCESSORLOWERWALL"}
DWELLING_RE = re.compile(r"_dwelling_(\d+)$")
COMMENT_RE = re.compile(r"!.*")


def _trailing_numbers(fields):
    out = []
    for f in reversed(fields):
        try:
            out.append(float(f))
        except ValueError:
            break
    out.reverse()
    drop = len(out) % 3
    return np.asarray(out[drop:], dtype=float).reshape(-1, 3)


def parse_idf(text):
    zones = {}
    surfaces = []
    fens = []
    equip = []
    sched_files = {}
    for chunk in COMMENT_RE.sub("", text).split(";"):
        fields = [x.strip() for x in chunk.split(",")]
        key = fields[0].upper()
        if key == "ZONE":
            vol = None
            try:
                vol = float(fields[9])
            except (ValueError, IndexError):
                vol = None
            try:
                mult = float(fields[7]) if fields[7] else 1.0
            except (ValueError, IndexError):
                mult = 1.0
            part = fields[12].upper() if len(fields) > 12 and fields[12] else "YES"
            zones[fields[1]] = {"volume": vol, "mult": mult, "part": part != "NO"}
        elif key == "BUILDINGSURFACE:DETAILED":
            bc = fields[6] if fields[6].upper() in BC_VALUES else fields[5]
            surfaces.append((fields[1], fields[2].lower(), fields[4], bc.upper(), _trailing_numbers(fields)))
        elif key == "FENESTRATIONSURFACE:DETAILED":
            fens.append((fields[1], fields[2].lower(), fields[4], _trailing_numbers(fields)))
        elif key == "OTHEREQUIPMENT":
            def _f(i):
                try:
                    return float(fields[i])
                except (ValueError, IndexError):
                    return float("nan")
            equip.append({"name": fields[1], "zone": fields[3] if len(fields) > 3 else "", "schedule": fields[4] if len(fields) > 4 else "", "wm2": _f(7), "subcat": fields[13] if len(fields) > 13 else ""})
        elif key == "SCHEDULE:FILE":
            try:
                col = int(float(fields[4]))
                skip = int(float(fields[5]))
            except (ValueError, IndexError):
                col, skip = 1, 0
            sched_files[fields[1]] = (fields[3], col, skip)
    return {"zones": zones, "surfaces": surfaces, "fens": fens, "equip": equip, "sched_files": sched_files}


def poly_area(pts):
    if len(pts) < 3:
        return 0.0
    p = pts - pts[0]
    return 0.5 * float(np.linalg.norm(np.cross(p, np.roll(p, -1, axis=0)).sum(axis=0)))


def _cluster_levels(zs):
    levels = []
    for z in sorted(zs):
        if levels and z - levels[-1][-1] <= LEVEL_TOL_M:
            levels[-1].append(z)
        else:
            levels.append([z])
    return [float(np.mean(g)) for g in levels]


def _level_index(levels, z):
    return int(np.argmin([abs(z - lv) for lv in levels]))


def _floor_polygons(parsed):
    polys = []
    for _name, stype, _zone, _bc, pts in parsed["surfaces"]:
        if stype != "floor" or len(pts) < 3:
            continue
        poly = Polygon(pts[:, :2])
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            polys.append(poly)
    return polys


def footprint_centroid(parsed):
    polys = _floor_polygons(parsed)
    if not polys:
        return None
    c = unary_union(polys).centroid
    return float(c.x), float(c.y)


def _rel(a, b):
    if b is None or b == 0 or (isinstance(b, float) and math.isnan(b)):
        return float("nan")
    return a / b - 1.0


def _flag(ok):
    return "" if ok is None else bool(ok)


def _isnan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def storey_reference(ctx):
    sl = ctx.get("levels_sidecar")
    if not _isnan(sl) and sl != "" and float(sl) > 0:
        return int(round(float(sl))), "levels_sidecar"
    try:
        lv = float(ctx.get("levels_data"))
    except (TypeError, ValueError):
        lv = float("nan")
    if not math.isnan(lv) and lv > 0 and lv.is_integer():
        return int(lv), "levels"
    if ctx.get("country") == "IT":
        h = ctx.get("height_m")
        if str(ctx.get("height_source", "")).lower().startswith("measured") and not _isnan(h) and float(h) > 0:
            return max(1, round(float(h) / STOREY_HEIGHT_M)), "ctc_height"
    for lp in ctx.get("layout_paths") or []:
        lp = Path(lp)
        if not lp.exists():
            continue
        try:
            sv = json.loads(lp.read_text(encoding="utf-8")).get("storeys")
        except (ValueError, OSError):
            sv = None
        if sv is not None and not _isnan(sv):
            try:
                if float(sv) > 0 and float(sv).is_integer():
                    return int(sv), "layout_0908"
            except (TypeError, ValueError):
                pass
    for ip in ctx.get("old_idf_paths") or []:
        ip = Path(ip)
        if not ip.exists():
            continue
        got = _idf_storeys(ip)
        if got is not None:
            return got, "idf_height_0907"
        break
    return None, "storey_rule_unreproduced"


def _idf_storeys(path):
    parsed = parse_idf(Path(path).read_text(encoding="utf-8", errors="replace"))
    roof_z = [float(np.max(s[4][:, 2])) for s in parsed["surfaces"] if s[1] == "roof" and len(s[4])]
    floor_z = [float(np.min(s[4][:, 2])) for s in parsed["surfaces"] if s[1] == "floor" and len(s[4])]
    if not roof_z or not floor_z:
        return None
    height = max(roof_z) - min(floor_z)
    n = round(height / STOREY_HEIGHT_M)
    if n < 1 or abs(height - STOREY_HEIGHT_M * n) > IDF_HEIGHT_TOL_M:
        return None
    return int(n)


def _zone_geometry(parsed):
    zfloor_polys = {}
    zfloor_area = {}
    ztop = {}
    zfloor_z = {}
    for _name, stype, zone, _bc, pts in parsed["surfaces"]:
        if not len(pts):
            continue
        ztop[zone] = max(ztop.get(zone, -1e18), float(pts[:, 2].max()))
        if stype == "floor" and len(pts) >= 3:
            poly = Polygon(pts[:, :2])
            if not poly.is_valid:
                poly = poly.buffer(0)
            if not poly.is_empty:
                zfloor_polys.setdefault(zone, []).append(poly)
            zfloor_area[zone] = zfloor_area.get(zone, 0.0) + poly_area(pts)
            zfloor_z.setdefault(zone, []).append(float(np.mean(pts[:, 2])))
    return zfloor_polys, zfloor_area, ztop, zfloor_z


def top_floor_area(parsed):
    zfloor_polys, zfloor_area, ztop, zfloor_z = _zone_geometry(parsed)
    entries = sorted((float(np.mean(zs)), z) for z, zs in zfloor_z.items())
    zvals = [e[0] for e in entries]
    unions = {z: unary_union(ps) for z, ps in zfloor_polys.items()}
    total = 0.0
    uncovered = set()
    for zone, area in zfloor_area.items():
        ceil_z = ztop.get(zone)
        covered = False
        if ceil_z is not None and zone in unions:
            lo = bisect_left(zvals, ceil_z - I6_ABOVE_Z_TOL_M)
            hi = bisect_right(zvals, ceil_z + I6_ABOVE_Z_TOL_M)
            for k in range(lo, hi):
                other = entries[k][1]
                if other == zone or other not in unions:
                    continue
                if unions[zone].intersection(unions[other]).area > I6_ABOVE_OVERLAP_M2:
                    covered = True
                    break
        if not covered:
            total += area
            uncovered.add(zone)
    return total, uncovered


def expected_dwellings_per_storey(ctx, n_storeys):
    alloc = allocate_european_dwellings(
        archetype_id=ctx["archetype_id"], building_type=ctx["building_type"],
        n_apartment=ctx["dwellings_used"], n_storey=n_storeys, plate_area_m2=float(ctx["footprint_area_m2"]),
    )
    counts = [f.dwelling_count for f in alloc.floor_allocations]
    expected = []
    for s, c in enumerate(counts):
        expected.append(c if c > 0 else (expected[s - 1] if s else 0))
    return counts, expected, alloc.dwelling_count


def dwelling_zones_per_level(parsed, levels):
    _zp, _zfa, _zt, zfloor_z = _zone_geometry(parsed)
    per = [0] * len(levels)
    for zname in parsed["zones"]:
        if not DWELLING_RE.search(zname) or zname not in zfloor_z:
            continue
        per[_level_index(levels, min(zfloor_z[zname]))] += 1
    return per


def read_schedule_mean(path, col, skip):
    arr = pd.read_csv(path, header=None, usecols=[col - 1], skiprows=skip).iloc[:, 0].to_numpy(dtype=float)
    return len(arr), float(arr.mean()) if len(arr) else float("nan")


def check_i10(parsed, ctx):
    phi = ctx.get("phi_int_w_m2")
    sdir = ctx.get("schedule_dir")
    if _isnan(phi) or not sdir:
        return "", "", 0.0
    equip = parsed["equip"]
    legacy = sum(1 for e in equip if e["subcat"] == I10_LEGACY_SUBCATEGORY)
    by_zone = {}
    for e in equip:
        if e["subcat"] == I10_SUBCATEGORY:
            by_zone.setdefault(e["zone"], []).append(e)
    bad = legacy
    worst = 0.0
    for zname in parsed["zones"]:
        if UNCONDITIONED_RE.search(zname):
            continue
        es = by_zone.get(zname, [])
        if len(es) != 1 or not (abs(es[0]["wm2"] - 1.0) < 1e-9):
            bad += 1
            continue
        sf = parsed["sched_files"].get(es[0]["schedule"])
        if sf is None:
            bad += 1
            continue
        fpath = Path(sdir) / Path(sf[0].replace(chr(92), "/")).name
        try:
            n, mean = read_schedule_mean(fpath, sf[1], sf[2])
        except (OSError, ValueError, IndexError, pd.errors.EmptyDataError):
            bad += 1
            continue
        dev = abs(mean / float(phi) - 1.0) if float(phi) else float("inf")
        worst = max(worst, dev)
        if n != I10_HOURS or not dev <= I10_TOL:
            bad += 1
    return bad, bad == 0, worst


def evaluate(parsed, ctx):
    r = {}
    surfaces = parsed["surfaces"]
    zones = parsed["zones"]
    floors = [s for s in surfaces if s[1] == "floor"]
    roofs = [s for s in surfaces if s[1] == "roof"]
    all_pts = [s[4] for s in surfaces if len(s[4])]
    floor_z = [float(np.mean(s[4][:, 2])) for s in floors if len(s[4])]
    levels = _cluster_levels(floor_z)
    n_levels = len(levels)
    level_area = [0.0] * n_levels
    total_floor = 0.0
    for s, z in zip([f for f in floors if len(f[4])], floor_z):
        a = poly_area(s[4])
        level_area[_level_index(levels, z)] += a
        if zones.get(s[2], {"part": True})["part"]:
            total_floor += a

    ref, ref_source = storey_reference(ctx)
    csv_storeys = ctx.get("storey_count")
    r["storeys_data_csv"] = csv_storeys if csv_storeys is not None else ""
    r["storey_source"] = ref_source
    r["storeys_ref"] = ref if ref is not None else ""
    r["storeys_idf"] = n_levels
    r["I1_value"] = n_levels
    r["I1_pass"] = _flag(ref is not None and n_levels == ref)
    r["I1_info_vs_storey_count"] = _flag(csv_storeys is not None and n_levels == int(csv_storeys))

    if n_levels and level_area[0] > 0:
        devs = [abs(a - level_area[0]) / level_area[0] for a in level_area]
        i2 = max(devs)
    else:
        i2 = float("inf")
    r["I2_value"] = i2
    r["I2_pass"] = _flag(i2 <= I2_TOL)
    r["storey_areas_m2"] = ";".join(f"{a:.2f}" for a in level_area)

    r["floor_area_idf_m2"] = total_floor
    foot = float(ctx["footprint_area_m2"])
    if ref is not None:
        denom = ref * foot
        ratio = total_floor / denom if denom > 0 else float("nan")
        r["I3_value"] = ratio
        r["I3_pass"] = _flag(not math.isnan(ratio) and I3_LOW <= ratio <= I3_HIGH)
    else:
        r["I3_value"] = float("nan")
        r["I3_pass"] = ""
    sc_denom = float(csv_storeys) * foot if csv_storeys is not None else 0.0
    r["I3_info_vs_storey_count"] = total_floor / sc_denom if sc_denom > 0 else float("nan")

    roof_z = [float(np.max(s[4][:, 2])) for s in roofs if len(s[4])]
    if roof_z and floor_z:
        height = max(roof_z) - min(floor_z)
    else:
        height = float("nan")
    r["I4_value"] = height
    if ref is not None:
        r["I4_pass"] = _flag(not math.isnan(height) and abs(height - ref * STOREY_HEIGHT_M) <= I4_TOL_M)
    else:
        r["I4_pass"] = ""
    r["I4_info_vs_storey_count"] = _flag(csv_storeys is not None and not math.isnan(height) and abs(height - int(csv_storeys) * STOREY_HEIGHT_M) <= I4_TOL_M)

    zone_surfs = {}
    for name, stype, zone, _bc, pts in surfaces:
        zone_surfs.setdefault(zone, []).append((stype, pts))
    bad_zones = 0
    max_zone_h = 0.0
    for zname in zones:
        items = zone_surfs.get(zname, [])
        n_floor = sum(1 for t, _p in items if t == "floor")
        n_top = sum(1 for t, _p in items if t in ("ceiling", "roof"))
        zs = np.concatenate([p[:, 2] for _t, p in items if len(p)]) if items else np.array([])
        zh = float(zs.max() - zs.min()) if len(zs) else 0.0
        max_zone_h = max(max_zone_h, zh)
        vol = zones[zname]["volume"]
        if vol is None:
            vol = sum(poly_area(p) for t, p in items if t == "floor") * zh
        if n_floor < 1 or n_top < 1 or not vol > 0 or zh > I5_MAX_ZONE_M:
            bad_zones += 1
    zones_without_surfaces = [z for z in zone_surfs if z not in zones]
    bad_zones += len(zones_without_surfaces)
    r["zones"] = len(zones)
    r["zone_mult_max"] = max([z["mult"] for z in zones.values()] or [1.0])
    r["max_zone_height_m"] = max_zone_h
    r["I5_value"] = bad_zones
    r["I5_pass"] = _flag(bad_zones == 0 and len(zones) > 0)

    roof_out = sum(poly_area(s[4]) for s in roofs if s[3] == "OUTDOORS")
    roof_adia = sum(poly_area(s[4]) for s in roofs if s[3] == "ADIABATIC")
    top_area, uncovered = top_floor_area(parsed)
    roof_adia_top = sum(poly_area(s[4]) for s in roofs if s[3] == "ADIABATIC" and s[2] in uncovered)
    d_roof = abs(roof_out + roof_adia_top - top_area) / top_area if top_area > 0 else float("inf")
    d_roof_literal = abs(roof_out + roof_adia - top_area) / top_area if top_area > 0 else float("inf")
    polys = _floor_polygons(parsed)
    union = unary_union(polys) if polys else None
    ground_area = level_area[0] if level_area else 0.0
    if union is not None and union.area > 0:
        d_ground = abs(ground_area - union.area) / union.area
        centroid = (float(union.centroid.x), float(union.centroid.y))
    else:
        d_ground = float("inf")
        centroid = None
    r["roof_area_m2"] = roof_out
    r["roof_adiabatic_m2"] = roof_adia
    r["roof_adiabatic_uncovered_m2"] = roof_adia_top
    r["I6_roof_dev_literal"] = d_roof_literal
    r["top_floor_area_m2"] = top_area
    r["I6_roof_dev"] = d_roof
    r["I6_ground_dev"] = d_ground
    r["I6_value"] = max(d_roof, d_ground)
    r["I6_pass"] = _flag(d_roof <= I6_TOL and d_ground <= I6_TOL)

    prepared = float(ctx["prepared_floor_area_m2"])
    d7 = abs(total_floor - prepared) / prepared if prepared > 0 else float("inf")
    r["floor_area_prepared_m2"] = prepared
    r["I7_value"] = d7
    r["I7_pass"] = _flag(d7 <= I7_TOL)

    idx = set()
    for zname in zones:
        m = DWELLING_RE.search(zname)
        if m:
            idx.add(int(m.group(1)))
    r["dwellings_idf"] = len(idx)
    r["dwelling_zone_pairs"] = sum(1 for z in zones if DWELLING_RE.search(z))
    r["levels_data"] = ctx.get("levels_data", "")
    r["sidecar_overlap_m2"] = ctx.get("sidecar_overlap_m2", "")
    r["dwellings_used"] = ctx["dwellings_used"]
    whole_only = not idx and any(z.endswith("_whole") for z in zones)
    r["I8_literal"] = _flag(len(idx) == int(ctx["dwellings_used"])) if ctx["divided"] and not whole_only else ""
    if ctx["divided"] and not whole_only:
        if ref is not None:
            basis, r["I8_storey_basis"] = ref, "ref"
        elif csv_storeys is not None:
            basis, r["I8_storey_basis"] = int(csv_storeys), "storey_count_csv"
        else:
            basis, r["I8_storey_basis"] = n_levels, "idf"
        try:
            counts, expected, total = expected_dwellings_per_storey(ctx, basis)
            actual = dwelling_zones_per_level(parsed, levels)
            width = max(len(expected), len(actual))
            exp_p = expected + [0] * (width - len(expected))
            act_p = actual + [0] * (width - len(actual))
            ok8 = exp_p == act_p and sum(counts) == int(ctx["dwellings_used"]) and total == int(ctx["dwellings_used"])
            r["I8_value"] = ";".join(str(x) for x in act_p)
            r["I8_expected"] = ";".join(str(x) for x in exp_p)
            r["I8_pass"] = _flag(ok8)
        except (ValueError, KeyError, AssertionError, TypeError) as exc:
            r["I8_value"] = f"alloc_error:{type(exc).__name__}"
            r["I8_expected"] = ""
            r["I8_pass"] = False
    else:
        r["I8_value"] = ""
        r["I8_expected"] = ""
        r["I8_storey_basis"] = ""
        r["I8_pass"] = ""
        r["I8_note"] = "undivided"

    wall_out = sum(poly_area(s[4]) for s in surfaces if s[1] == "wall" and s[3] == "OUTDOORS")
    win = sum(poly_area(f[3]) for f in parsed["fens"])
    r["outdoor_wall_m2"] = wall_out
    r["window_m2"] = win
    target = ctx.get("share_target")
    if wall_out > 0:
        share = win / wall_out
        ok = win > 0 and target is not None and not (isinstance(target, float) and math.isnan(target)) and abs(share - target) <= I9_TOL
    else:
        share = float("nan")
        ok = win == 0
    r["share_target"] = target if target is not None else float("nan")
    r["I9_value"] = share
    r["I9_pass"] = _flag(ok)

    i10_val, i10_ok, i10_worst = check_i10(parsed, ctx)
    r["I10_value"] = i10_val
    r["I10_pass"] = i10_ok
    r["I10_worst_mean_dev"] = i10_worst

    if all_pts:
        cat = np.concatenate(all_pts)
        xmin, xmax = float(cat[:, 0].min()), float(cat[:, 0].max())
        ymin, ymax = float(cat[:, 1].min()), float(cat[:, 1].max())
    else:
        xmin = xmax = ymin = ymax = float("nan")
    r["x_min"], r["x_max"], r["y_min"], r["y_max"] = xmin, xmax, ymin, ymax
    offset = ctx.get("offset")
    if ctx["shifted"]:
        in_range = all(0.0 <= v <= I11_RANGE_M for v in (xmin, xmax, ymin, ymax))
        ok11 = in_range and offset is not None
    else:
        ok11 = offset is None
    ref_c = ctx.get("ref_centroid_abs")
    dist = float("nan")
    if centroid is not None and ref_c is not None:
        ox, oy = offset if offset is not None else (0.0, 0.0)
        dist = math.hypot(centroid[0] + ox - ref_c[0], centroid[1] + oy - ref_c[1])
        ok11 = ok11 and dist <= I11_CENTROID_TOL_M
    elif ref_c is not None:
        ok11 = False
    r["I11_value"] = dist
    r["I11_pass"] = _flag(ok11)

    a08 = ctx.get("area_0908")
    stem = ctx["stem"]
    if a08 is None or (isinstance(a08, float) and math.isnan(a08)) or a08 <= 0:
        r["I13_value"] = float("nan")
        r["I13_pass"] = ""
        r["I13_reason"] = "no_0908_value"
    else:
        diff = total_floor / a08 - 1.0
        r["I13_value"] = diff
        if abs(diff) <= I13_TOL:
            r["I13_pass"] = True
            r["I13_reason"] = ""
        else:
            ref13 = ref if ref is not None else csv_storeys
            codes = []
            if stem in CORE_RULE_STEMS:
                codes.append("core_rule")
            else:
                if diff > 0 and ctx.get("t06s_rerun"):
                    codes.append("t06s_fold_fix")
                if (
                    ref_source == "levels" and csv_storeys is not None and int(csv_storeys) != ref
                    and foot > 0 and abs(a08 / foot - int(csv_storeys)) <= 0.03 * int(csv_storeys)
                ):
                    codes.append("storey_source_levels")
                if diff > 0 and "storey_source_levels" not in codes and ref13 is not None and a08 < I3_LOW * ref13 * foot:
                    codes.append("up_class_09-08_short")
                if diff < 0 and ctx.get("n_deleted", 0) > 0:
                    codes.append("sliver_drop")
            code = ";".join(codes) if codes else "UNEXPLAINED"
            r["I13_reason"] = code
            r["I13_pass"] = code != "UNEXPLAINED"
    r["centroid_x"] = centroid[0] if centroid else float("nan")
    r["centroid_y"] = centroid[1] if centroid else float("nan")
    return r


def named_reasons(stem, row):
    codes = []
    if stem == ZERO_FLOOR_STEM:
        codes.append("zero_floor_flat")
    if stem in CORE_RULE_STEMS:
        codes.append("core_rule")
    if row.get("outdoor_wall_m2", 1.0) == 0:
        codes.append("finding283_no_outdoor_wall")
    if row.get("storey_source") == "storey_rule_unreproduced":
        codes.append("storey_rule_unreproduced")
    if row.get("I8_note") == "undivided":
        codes.append("undivided")
    return ";".join(codes)


def _load_offset(tree_dir):
    p = tree_dir / "origin_offset.json"
    if not p.exists():
        return None
    j = json.loads(p.read_text(encoding="utf-8"))
    return float(j["dx"]), float(j["dy"])


def _work(args):
    ctx, idf_path, ref_path, expected_md5 = args
    stem = ctx["stem"]
    row = {"stem": stem, "building_id": ctx.get("building_id", "")}
    idf_path = Path(idf_path)
    present = idf_path.exists()
    sched_ok = bool(ctx["schedule_dir"]) and Path(ctx["schedule_dir"]).is_dir()
    digest = None
    if present:
        raw = idf_path.read_bytes()
        digest = hashlib.md5(raw).hexdigest()
    md5_ok = expected_md5 is not None and digest is not None and digest == expected_md5
    in_universe = bool(ctx["in_universe"])
    row["idf_present"] = present
    row["md5_listed"] = expected_md5 is not None
    row["md5_match"] = md5_ok
    row["schedule_dir_present"] = sched_ok
    row["in_universe"] = in_universe
    row["I12_pass"] = bool(present and md5_ok and sched_ok and in_universe)
    row["I12_value"] = ""
    if not present or ctx.get("storey_count") is None:
        row["reason"] = "missing_idf" if not present else "no_source_data"
        return row
    parsed = parse_idf(raw.decode("utf-8", errors="replace"))
    if ref_path is not None:
        ref_parsed = parse_idf(Path(ref_path).read_text(encoding="utf-8", errors="replace"))
        c = footprint_centroid(ref_parsed)
        rox, roy = ctx.get("ref_offset") or (0.0, 0.0)
        ctx = dict(ctx)
        ctx["ref_centroid_abs"] = (c[0] + rox, c[1] + roy) if c else None
    elif ctx.get("self_ref"):
        ctx = dict(ctx)
        c = footprint_centroid(parsed)
        ox, oy = ctx.get("offset") or (0.0, 0.0)
        ctx["ref_centroid_abs"] = (c[0] + ox, c[1] + oy) if c else None
    row.update(evaluate(parsed, ctx))
    row["reason"] = named_reasons(stem, row)
    return row


def _district_contexts(code, tree, ref_tree):
    d = DISTRICTS[code]
    tdir = EVIDENCE / f"{d}_{tree}"
    rdir = EVIDENCE / f"{d}_{ref_tree}"
    prep = pd.read_csv(tdir / "prepared_buildings.csv")
    ref_prep = pd.read_csv(rdir / "prepared_buildings.csv")
    b = pd.read_csv(DATA_3D / f"eu_{d}_data" / "buildings.csv").set_index("building_id")
    win = pd.read_csv(tdir / "windows.csv").set_index("stem")
    man_path = next((EVIDENCE / f"{d}_merged_2026-09-08").glob("*_manifest.csv"))
    man = pd.read_csv(man_path).set_index("building_id")
    deg_path = sorted(tdir.glob("degenerate_*.csv"))
    deg = pd.read_csv(deg_path[-1]).set_index("stem") if deg_path else pd.DataFrame()
    date = tree[-10:]
    md5 = {}
    for line in (tdir / f"md5_{date}.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            md5[parts[1][:-4]] = parts[0]
    universe = set(ref_prep["stem"])
    country = code
    reg = json.loads((ROOT / "openubem" / "data" / "construction" / f"tabula_archetypes_{code.lower()}.json").read_text(encoding="utf-8"))["records"]
    phi_by_arch = {x["archetype_id"]: float(x["phi_int_w_m2"]) for x in reg}
    rerun_path = RERUN_DIR / f"t06s_rerun_{d}.txt"
    rerun = set(rerun_path.read_text(encoding="utf-8").split()) if rerun_path.exists() else set()
    idf_stems = {p.stem for p in (tdir / "idfs").glob("*.idf")}
    prep_by_stem = prep.set_index("stem")
    ref_by_stem = ref_prep.set_index("stem")
    offset = _load_offset(tdir)
    ref_offset = _load_offset(rdir)
    same = tree == ref_tree
    sidecar = None
    if code == "ES":
        sidecar = pd.read_csv(ES_SIDECAR)
        sidecar = sidecar.set_index(sidecar["building_id"].astype(str))
    ctxs = []
    for stem in sorted(universe | idf_stems):
        src = prep_by_stem.loc[stem] if stem in prep_by_stem.index else (ref_by_stem.loc[stem] if stem in ref_by_stem.index else None)
        ctx = {
            "stem": stem,
            "in_universe": stem in universe,
            "schedule_dir": str(tdir / "schedules" / stem) if (tdir / "schedules" / stem).is_dir() else "",
            "shifted": code in SHIFTED,
            "offset": offset,
            "ref_offset": ref_offset,
            "self_ref": same,
            "country": country,
            "t06s_rerun": stem in rerun,
        }
        if src is not None:
            bid = src["building_id"]
            ctx["building_id"] = bid
            ctx["prepared_floor_area_m2"] = float(src["floor_area_m2"])
            ctx["dwellings_used"] = int(src["dwellings_used"])
            ctx["divided"] = str(src["geometry_outcome"]).startswith("DWELLING_LAYOUT_EMITTED")
            ctx["archetype_id"] = src["archetype_id"]
            ctx["building_type"] = src["building_type"]
            ctx["phi_int_w_m2"] = phi_by_arch.get(src["archetype_id"], float("nan"))
            ctx["layout_paths"] = [str(EVIDENCE / ld.format(d=d) / f"{bid}.json") for ld in LAYOUT_DIRS]
            ctx["old_idf_paths"] = [str(EVIDENCE / od.format(d=d) / f"{stem}.idf") for od in OLD_IDF_TREES]
            if bid in b.index:
                ctx["storey_count"] = int(b.loc[bid, "storey_count"])
                ctx["footprint_area_m2"] = float(b.loc[bid, "footprint_area_m2"])
                lv = b.loc[bid, "levels"]
                ctx["levels_data"] = float(lv) if pd.notna(lv) else ""
                ctx["height_m"] = float(b.loc[bid, "height_m"]) if pd.notna(b.loc[bid, "height_m"]) else float("nan")
                ctx["height_source"] = str(b.loc[bid, "height_source"])
            if sidecar is not None and str(bid) in sidecar.index:
                sv = sidecar.loc[str(bid), "levels"]
                if pd.notna(sv):
                    ctx["levels_sidecar"] = float(sv)
                ov = sidecar.loc[str(bid), "overlap_area_m2"]
                ctx["sidecar_overlap_m2"] = float(ov) if pd.notna(ov) else ""
            if bid in man.index:
                v = man.loc[bid, "floor_area_m2"]
                ctx["area_0908"] = float(v) if pd.notna(v) else float("nan")
        if stem in win.index:
            ctx["share_target"] = float(win.loc[stem, "share_target"])
        if len(deg) and stem in deg.index:
            ctx["n_deleted"] = int(deg.loc[stem, "n_deleted"])
        ref_path = None if same else (rdir / "idfs" / f"{stem}.idf")
        if ref_path is not None and not ref_path.exists():
            ref_path = None
        ctxs.append((ctx, str(tdir / "idfs" / f"{stem}.idf"), None if ref_path is None else str(ref_path), md5.get(stem)))
    return d, ctxs, man_path, offset, md5, universe, idf_stems


def _summarize(df, d):
    rows = []
    for c in CHECKS:
        col = f"{c}_pass"
        if col in df.columns:
            vals = df[col]
        else:
            vals = pd.Series([""] * len(df))
        evaluated = vals.map(lambda v: isinstance(v, (bool, np.bool_)))
        fails = evaluated & vals.map(lambda v: isinstance(v, (bool, np.bool_)) and not bool(v))
        reasons = df["reason"].fillna("").astype(str)
        named = fails & reasons.str.contains("zero_floor_flat|core_rule", regex=True)
        unrep = fails & reasons.str.contains("storey_rule_unreproduced")
        row = {
            "district": d,
            "check": c,
            "n_evaluated": int(evaluated.sum()),
            "n_fail": int(fails.sum()),
            "n_fail_named_exception": int(named.sum()),
            "n_fail_unreproduced": int(unrep.sum()) if c in ("I1",) else 0,
        }
        if c == "I3" and "I3_value" in df.columns:
            v = pd.to_numeric(df["I3_value"], errors="coerce").dropna()
            row["p1"] = float(np.percentile(v, 1)) if len(v) else float("nan")
            row["p50"] = float(np.percentile(v, 50)) if len(v) else float("nan")
            row["p99"] = float(np.percentile(v, 99)) if len(v) else float("nan")
        rows.append(row)
    if "I13_reason" in df.columns:
        for code, n in df["I13_reason"].fillna("").astype(str).replace("", np.nan).dropna().value_counts().items():
            rows.append({"district": d, "check": f"I13:{code}", "n_evaluated": int(n), "n_fail": int(n) if code == "UNEXPLAINED" else 0, "n_fail_named_exception": 0})
    return rows


def run_district(code, tree, ref_tree, workers):
    d, ctxs, man_path, offset, md5, universe, idf_stems = _district_contexts(code, tree, ref_tree)
    if workers > 1:
        with mp.Pool(min(workers, MAX_WORKERS)) as pool:
            rows = list(pool.imap(_work, ctxs, chunksize=8))
    else:
        rows = [_work(c) for c in ctxs]
    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / f"{d}_{tree}_integrity.csv", index=False)
    return d, df, man_path.relative_to(ROOT).as_posix()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--districts", default="ES,FR,GB,IT")
    ap.add_argument("--ref-tree", default="win_2026-10-05")
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    a = ap.parse_args(argv)
    summary = []
    for code in [x.strip().upper() for x in a.districts.split(",") if x.strip()]:
        d, df, man = run_district(code, a.tree, a.ref_tree, a.workers)
        summary.extend(_summarize(df, d))
        print(f"{d}: {len(df)} rows; 09-08 manifest {man}", flush=True)
    sdf = pd.DataFrame(summary)
    sdf.to_csv(OUT_DIR / f"summary_{a.tree}.csv", index=False)
    piv = sdf[sdf["check"].isin(CHECKS)].pivot(index="check", columns="district", values="n_fail").reindex(CHECKS)
    print(piv.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
