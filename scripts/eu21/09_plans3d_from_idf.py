import argparse
import dataclasses
import html as htmllib
import importlib.util as ilu
import json
import pathlib
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely import make_valid
from shapely.ops import unary_union

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(ROOT))


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M08 = _load_module("eu21_m09_m08_district_viewer", str(ROOT / "scripts" / "eu21" / "08_district_viewer.py"))
M07 = M08.M07
M3D = M08.M3D
import scripts.eu_idf_plan_reader as READER  # noqa: E402
from scripts.eu_idf_plan_reader import read_building_plan  # noqa: E402
from openubem.geometry.european_residential import allocate_european_dwellings  # noqa: E402
from scripts.run_eu_s2_district_campaign import DISTRICTS, FLOOR_TO_FLOOR_M  # noqa: E402

EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
EU02 = ROOT / "openubem" / "outputs" / "eu02"
PLANS3D_DIR = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "plans3D"
DATE = "2026-10-01"
TAG = f"{DATE} from the simulated IDFs"
CIRC_COLOR = "#c98a1b"
WHOLE_COLOR = "#5c6773"
AREA_TOL = 0.005

PROBE_ID = "way/333138130"
RESIDUAL_DIR = EVIDENCE / "division_residual_2026-09-29"
UNDIVIDED_CSV = RESIDUAL_DIR / "undivided_excluded_2026-10-01.csv"
FAULT_CSV = RESIDUAL_DIR / "geometry_fault_excluded_2026-10-06.csv"
SOURCE_TAG = None
PREP = {}
FAULT_TEXT = "left out of results: broken shell (FINDING 291)"
UNDIVIDED_COLOR = (232, 60, 200)
M08.COLOR["UNDIVIDED"] = UNDIVIDED_COLOR
M08.LEGEND_LABELS["UNDIVIDED"] = "Not divided — not simulated"
OVERLAY_CSV = None
EXCLUDE_CSV = None
UNRESOLVED_COLOR = (120, 120, 120)
UNRESOLVED_LABEL = "Floor plan not resolved — left out of results"
UNRESOLVED_TEXT = "left out of results: floor plan not resolved (owner ruling 2026-10-08)"
M08.COLOR["UNRESOLVED"] = UNRESOLVED_COLOR
M08.LEGEND_LABELS["UNRESOLVED"] = UNRESOLVED_LABEL


def overlay_map(district):
    if OVERLAY_CSV is None:
        return {}
    d = pd.read_csv(OVERLAY_CSV, dtype=str)
    d = d[d["district"] == district]
    return dict(zip(d["building_id"], d["idf"]))


def unresolved_ids(district):
    if EXCLUDE_CSV is None:
        return set()
    d = pd.read_csv(EXCLUDE_CSV, dtype=str)
    return set(d.loc[d["district"] == district, "building_id"])


def undivided_ids(district):
    d = pd.read_csv(UNDIVIDED_CSV, dtype=str)
    return set(d.loc[d["district"] == district, "building_id"])


def fault_ids(district):
    if SOURCE_TAG is None or not FAULT_CSV.exists():
        return set()
    d = pd.read_csv(FAULT_CSV, dtype=str)
    return set(d.loc[d["district"] == district, "building_id"])


def trees(district):
    return EVIDENCE / f"{district}_fix_{DATE}", EVIDENCE / f"{district}_fix_{DATE}_t06f"


def manifest_outcomes(tree, district):
    m = pd.read_csv(tree / "prepared_buildings.csv", dtype=str)
    return dict(zip(m["building_id"], m["geometry_outcome"]))


def read_fault_plan(path, **kw):
    orig = READER.parse_idf_floor_zones

    def tolerant(p):
        names, rings, zmax = orig(p)
        return [n for n in names if rings.get(n)], rings, zmax

    READER.parse_idf_floor_zones = tolerant
    try:
        return read_building_plan(path, **kw)
    finally:
        READER.parse_idf_floor_zones = orig


def read_all_tag(district):
    tree = EVIDENCE / f"{district}_{SOURCE_TAG}"
    prepared = pd.read_csv(tree / "prepared_buildings.csv", dtype=str)
    off = tree / "origin_offset.json"
    dx = dy = 0.0
    if off.exists():
        o = json.loads(off.read_text(encoding="utf-8"))
        dx, dy = float(o["dx"]), float(o["dy"])
    plans = []
    ovl = overlay_map(district)
    for _, row in prepared.iterrows():
        PREP[row["building_id"]] = row
        path = tree / "idfs" / f"{row['stem']}.idf"
        if row["building_id"] in ovl:
            path = pathlib.Path(ovl[row["building_id"]])
        if not path.exists():
            continue
        kw = dict(stem=row["stem"], building_id=row["building_id"], district=district, geometry_outcome=row["geometry_outcome"])
        if row["building_id"] in fault_ids(district):
            plan = read_fault_plan(path, **kw)
        else:
            plan = read_building_plan(path, **kw)
        if row["building_id"] not in ovl:
            plan = dataclasses.replace(plan, origin_xy=(plan.origin_xy[0] + dx, plan.origin_xy[1] + dy))
        plans.append((plan, "ovl" if row["building_id"] in ovl else "win"))
    return plans


def read_all(district):
    if SOURCE_TAG is not None:
        return read_all_tag(district)
    fix, t06f = trees(district)
    prepared = pd.read_csv(fix / "prepared_buildings.csv", dtype=str)
    out_fix = manifest_outcomes(fix, district)
    out_t06f = manifest_outcomes(t06f, district)
    plans = []
    for _, row in prepared.iterrows():
        stem = row["stem"]
        p_t06f = t06f / "idfs" / f"{stem}.idf"
        if p_t06f.exists():
            path, src, outcome = p_t06f, "t06f", out_t06f.get(row["building_id"], out_fix[row["building_id"]])
        else:
            path, src, outcome = fix / "idfs" / f"{stem}.idf", "fix", out_fix[row["building_id"]]
        plan = read_building_plan(path, stem=stem, building_id=row["building_id"], district=district, geometry_outcome=outcome)
        plans.append((plan, src))
    return plans


def zone_geom(zone):
    g = None
    for ring in zone.rings:
        if len(ring) < 3:
            continue
        p = make_valid(Polygon(ring))
        g = p if g is None else g.symmetric_difference(p)
    return g


def outline_rings(zones, ox, oy):
    rings = []
    try:
        geoms = [zone_geom(z) for z in zones]
        geoms = [g for g in geoms if g is not None]
        u = unary_union(geoms) if geoms else None
    except Exception:
        for z in zones:
            for ring in z.rings:
                rings.append([[round(x + ox, 2), round(y + oy, 2)] for x, y in ring] + [[round(ring[0][0] + ox, 2), round(ring[0][1] + oy, 2)]])
        return rings
    if u is None or u.is_empty:
        return rings
    parts = list(u.geoms) if u.geom_type == "MultiPolygon" else [u]
    for part in parts:
        if part.geom_type != "Polygon":
            continue
        for ring in [part.exterior] + list(part.interiors):
            rings.append([[round(x + ox, 2), round(y + oy, 2)] for x, y in ring.coords])
    return rings


def typical_group(groups):
    best = None
    for g in sorted(groups):
        n = sum(1 for z in groups[g] if z.kind == "dwelling")
        if best is None or n > best[1]:
            best = (g, n)
    return best


def plan_checks(zones):
    dw = [z for z in zones if z.kind == "dwelling"]
    if not dw:
        return None, None
    flats = [zone_geom(z) for z in dw]
    plate = unary_union([zone_geom(z) for z in zones])
    if plate.geom_type != "Polygon":
        plate = plate.buffer(0.02, join_style=2).buffer(-0.02, join_style=2)
    if plate.geom_type != "Polygon" or any(f is None or f.geom_type != "Polygon" for f in flats):
        raise ValueError("a zone or the storey outline is not a single polygon")
    rec = {"drawn_per_floor": len(dw)}
    M07.run_checks(rec, flats, plate)
    ch = []
    for c in M08.CHECK_IDS:
        info = rec["checks"][c]
        ch.append([c, info["show"], 1 if info["pass"] else 0])
    return ch, rec["verdict"]


def build_record(plan, src, geom, dcx, dcy, undivided=False, fault=False, unresolved=False):
    ox, oy = plan.origin_xy
    groups = {}
    for z in plan.zones:
        groups.setdefault(z.storey, []).append(z)
    gkeys = sorted(groups)
    storeys = plan.storey_count
    sg = []
    for s in range(storeys):
        eligible = [i for i, g in enumerate(gkeys) if g <= s]
        sg.append(eligible[-1] if eligible else 0)

    fs, fk, fn, fo, fa = [], [], [], [], []
    for g in gkeys:
        zs = groups[g]
        fs.append([[[[round(x, 2), round(y, 2)] for x, y in ring] for ring in z.rings] for z in zs])
        fk.append([z.kind for z in zs])
        fn.append([z.name for z in zs])
        fo.append(outline_rings(zs, 0.0, 0.0))
        fa.append(round(sum(z.area_m2 for z in zs), 3))

    tg, tn = typical_group(groups)
    ruled = plan.is_ruled()
    ch, verdict_checks, err = [], None, None
    if ruled and tn:
        try:
            ch, verdict_checks = plan_checks(groups[tg])
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    if unresolved:
        verdict = "UNRESOLVED"
        status = "UNRESOLVED"
    elif undivided:
        verdict = "UNDIVIDED"
        status = "UNDIVIDED"
    elif not ruled:
        verdict = "GENERIC"
        status = "GENERIC_NO_CENSUS"
    elif err is not None:
        verdict, status = "ERROR", "ERROR"
    else:
        verdict, status = verdict_checks, "direct"

    geom_ok = geom is not None and geom.geom_type == "Polygon" and not geom.is_empty
    if geom_ok:
        ext = [(c[0], c[1]) for c in geom.exterior.coords][:-1]
        fp = [list(geom.exterior.coords)] + [list(i.coords) for i in geom.interiors]
        fp = [[[c[0] - ox, c[1] - oy] for c in ring] for ring in fp]
        scene = M3D._scene_ring(ext, (0.0, 0.0), dcx, dcy)
    else:
        outline0 = outline_rings(groups[gkeys[0]], ox, oy)
        ext = outline0[0][:-1] if outline0 else []
        fp = [[[x - ox, y - oy] for x, y in ring] for ring in outline0]
        scene = M3D._scene_ring(ext, (0.0, 0.0), dcx, dcy)

    k = tn if ruled and tn else None
    n_dw = sum(1 for z in plan.zones if z.kind == "dwelling")
    used = None
    alloc = [None] * storeys
    prow = PREP.get(plan.building_id)
    if prow is not None and n_dw > 0:
        try:
            used = int(prow["dwellings_used"])
            fa_ = allocate_european_dwellings(
                archetype_id=prow["archetype_id"], building_type=prow["building_type"],
                n_apartment=used, n_storey=storeys, plate_area_m2=float(prow["gross_footprint_area_m2"]),
            )
            alloc = [f.dwelling_count for f in fa_.floor_allocations]
        except (ValueError, KeyError, AssertionError, TypeError):
            used = None
            alloc = [None] * storeys
    up = [a == 0 for a in alloc]
    n_circ = sum(1 for z in plan.zones if z.kind == "circulation")

    notes = []
    for s in range(storeys):
        gi = sg[s]
        zs = groups[gkeys[gi]]
        nd = sum(1 for z in zs if z.kind == "dwelling")
        nc = sum(1 for z in zs if z.kind == "circulation")
        nw = sum(1 for z in zs if z.kind == "whole")
        parts = []
        if nd and up[s]:
            parts.append(f"upper floor of the flat(s) below, {nd} zone{'s' if nd != 1 else ''}")
        elif nd:
            parts.append(f"{nd} dwelling{'s' if nd != 1 else ''}")
        if nc:
            parts.append(f"{nc} circulation zone{'s' if nc != 1 else ''}")
        if nw:
            parts.append("one zone for the whole floor (no flats drawn)")
        absorbed = [t for t in range(storeys) if sg[t] == gi]
        grp_txt = ""
        if len(absorbed) > 1:
            grp_txt = f" Storeys F{absorbed[0]}\u2013F{absorbed[-1]} are one extruded zone group in the IDF, so they share this plan."
        notes.append(f"Storey F{s}: {', '.join(parts)}; {fa[gi]:.1f} m\u00b2 of floor, as written in the IDF.{grp_txt}")

    chips = ""
    if ch:
        chips = '<div class="checks">' + " ".join(
            f'<span class="chk {"ok" if c[2] else "bad"}">{c[0]} {htmllib.escape(c[1])}</span>' for c in ch
        ) + "</div>"
    if verdict == "PASS":
        badge = "<span class='m-badge emitted'>ALL 7 CHECKS PASS</span>"
    elif verdict == "FAIL":
        failing = ", ".join(c[0] for c in ch if not c[2])
        badge = f"<span class='m-badge fallback'>FAIL</span> <b>Failing checks:</b> {failing}."
    elif verdict == "ERROR":
        badge = "<span class='m-badge fallback'>CHECKS NOT RUN</span> " + htmllib.escape(err or "")
    elif verdict == "UNRESOLVED":
        badge = f"<span class='m-badge fallback'>{htmllib.escape(UNRESOLVED_LABEL.upper())}</span> {htmllib.escape(UNRESOLVED_TEXT)}."
    elif verdict == "UNDIVIDED":
        badge = "<span class='m-badge unsim'>NOT DIVIDED &mdash; NOT SIMULATED</span> This home has one zone per floor and is left out of the simulations."
    else:
        badge = "<span class='m-badge unsim'>ONE ZONE PER FLOOR</span>"
    if fault:
        badge = f"<span class='m-badge fallback'>{htmllib.escape(FAULT_TEXT.upper())}</span> " + badge
    sb = (
        f"{badge}<br><p style='color:#8b95a7;font-size:11.5px;margin:4px 0 6px;'>"
        f"Read from the IDF <code>{plan.stem}</code> ({'fixed-homes overlay 2026-10-08' if src == 'ovl' else 'simulated tree ' + SOURCE_TAG if src == 'win' else 'second-fix tree' if src == 't06f' else 'first-fix tree'}). "
        f"IDF outcome <code>{htmllib.escape(plan.geometry_outcome)}</code>. "
        f"{n_dw} dwelling zones and {n_circ} circulation zones over {len(gkeys)} storey group(s). "
        f"{'Checks are run on the typical storey F' + str(tg) + '.' if ch else 'No flat checks apply.'}</p>{chips}"
    )

    group_label = f"{k} dwellings per floor" if k else "one zone per floor"
    return {
        "building_id": plan.building_id,
        "stem": plan.stem,
        "district": plan.district,
        "group": group_label,
        "k": k,
        "storeys": storeys,
        "declared_dwellings": used if used is not None else plan.dwelling_count,
        "zn": n_dw if used is not None else None,
        "up": up,
        "idf_state": plan.geometry_outcome + (f" - {FAULT_TEXT}" if fault else "") + (f" - {UNRESOLVED_TEXT}" if unresolved else ""),
        "area_m2": round(plan.gross_area_m2),
        "height_m": round(storeys * FLOOR_TO_FLOOR_M, 1),
        "status": status,
        "verdict": verdict,
        "footprint": fp,
        "footprint_scene": scene,
        "checks_list": ch,
        "fs": fs, "fk": fk, "fn": fn, "fo": fo, "sg": sg, "nt": notes, "sb": sb,
        "src": src,
        "geom_ok": geom_ok,
        "err": err,
    }


def load_geoms(district):
    gdf = gpd.read_file(EU02 / district / "02_residential_manifest.gpkg")
    idcol = "building_id" if "building_id" in gdf.columns else gdf.columns[0]
    geoms = {str(r[idcol]): r.geometry for _, r in gdf.iterrows()}
    cs = [g.centroid for g in geoms.values() if g is not None]
    return geoms, sum(c.x for c in cs) / len(cs), sum(c.y for c in cs) / len(cs)


JS_PATCHES = [
    ("var rings=(b.fp&&b.fp.length>0)?b.fp:[b.r];",
     "var gi=(b.sg&&b.sg[sIdx]!==undefined)?b.sg[sIdx]:sIdx;"
     "var rings=(b.fo&&b.fo[gi]&&b.fo[gi].length>0)?b.fo[gi]:((b.fp&&b.fp.length>0)?b.fp:[b.r]);"),
    ("var fl=b.fl||[];",
     "var fl=(b.fs&&b.fs[gi])?b.fs[gi]:(b.fl||[]);var fk=(b.fk&&b.fk[gi])||[];var fn=(b.fn&&b.fn[gi])||[];"
     "var lab=[];var dc=0;for(var q=0;q<fk.length;q++){lab.push(fk[q]===\"circulation\"?\"C\":(fk[q]===\"whole\"?\"W\":\"D\"+(++dc)));}"),
    ("var zc=ZONE_COLORS[z%ZONE_COLORS.length];",
     f"var zc=fk[z]===\"circulation\"?\"{CIRC_COLOR}\":(fk[z]===\"whole\"?\"{WHOLE_COLOR}\":ZONE_COLORS[z%ZONE_COLORS.length]);"),
    ('fpCtx.fillText("D"+(z+1),zcx,zcy);', "fpCtx.fillText(lab[z]||(\"D\"+(z+1)),zcx,zcy);"),
    ('var zName=b.id+"_F"+sIdx+"_dwelling_"+z;', 'var zName=fn[z]||(b.id+"_F"+sIdx+"_dwelling_"+z);'),
    ('"<td>Dwelling "+(z+1)+"</td>"',
     '"<td>"+(fk[z]==="circulation"?"Circulation":(fk[z]==="whole"?"One zone per floor":(b.up&&b.up[sIdx]&&fk[z]==="dwelling"?"Dwelling "+lab[z]+" (upper floor)":"Dwelling "+(lab[z]||"D"+(z+1)).substring(1))))+"</td>"'),
    ("if(b.fl&&b.fl.length>0&&storeys>1){", "if(b.fs&&b.fs.length>0&&storeys>1){"),
    ("mStatusBox.innerHTML=statusHtml;", "mStatusBox.innerHTML=b.sb||statusHtml;"),
    ('<div id="m-note">one plate, dwellings only &mdash; the same plan on every storey (D-EU-79)</div>', '<div id="m-note"></div>'),
    ("function openPopup(b){",
     "function setNote(b,s){document.getElementById(\"m-note\").textContent=(b.nt&&b.nt[s])?b.nt[s]:\"\";}\nfunction openPopup(b){"),
    ("  drawFloorPlan(b,0,-1);\n  modalBackdrop.style.display=\"flex\";", "  drawFloorPlan(b,0,-1);\n  setNote(b,0);\n  modalBackdrop.style.display=\"flex\";"),
    ("currentStoreyIndex=sIdx;", "currentStoreyIndex=sIdx;if(currentModalBuilding)setNote(currentModalBuilding,sIdx);"),
    ('"<b>Dwellings (census):</b> "', '(b.zn!=null?"<b>Dwellings:</b> ":"<b>Dwellings (in the IDF):</b> ")'),
    ('declLabel+dwellings+" &middot; "+', 'declLabel+dwellings+" &middot; "+(b.zn!=null?"<b>Zones in the model:</b> "+b.zn+" &middot; ":"")+'),
    ('"<b>Footprint:</b> "', '"<b>Gross floor area:</b> "'),
    ('&middot; footprint "', '&middot; gross floor area "'),
    ('"<br>status: <b>"+b.st+"</b>"', '"<br>IDF: <b>"+b.idf+"</b>"'),
]


def make_hud(district, plates, n_t06f, n_fix, wall):
    dshort = M07.DSHORT.get(district, district)
    src_text = f"{district}_{SOURCE_TAG}" if SOURCE_TAG else f"{district}_fix_{DATE} + _t06f"
    n = len(plates)
    if SOURCE_TAG:
        src_rows = f'<div class="row"><span class="k">IDF from simulated tree ({SOURCE_TAG})</span><span>{n}</span></div>'
    else:
        src_rows = (f'<div class="row"><span class="k">IDF from second-fix tree (_t06f)</span><span>{n_t06f}</span></div>'
                    f'<div class="row"><span class="k">IDF from first-fix tree</span><span>{n_fix}</span></div>')
    c = {}
    for p in plates:
        c[p["verdict"]] = c.get(p["verdict"], 0) + 1
    ruled = sum(1 for p in plates if p["k"])
    fail_by = {cid: 0 for cid in M08.CHECK_IDS}
    for p in plates:
        for cid, _show, ok in p["checks_list"]:
            if not ok:
                fail_by[cid] += 1
    fail_line = " &middot; ".join(f"{k} {v}" for k, v in fail_by.items())
    unres_row = (f'  <div class="row"><span class="k">Floor plan not resolved, left out of results</span><span>{c.get("UNRESOLVED", 0)}</span></div>\n'
                 if OVERLAY_CSV or EXCLUDE_CSV else "")
    n_ovl = sum(1 for p in plates if p["src"] == "ovl")
    if n_ovl:
        src_rows += f'<div class="row"><span class="k">IDF from fixed-homes overlay (2026-10-08)</span><span>{n_ovl}</span></div>'
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    def sw(k):
        r = M08.COLOR[k]
        return f"rgb({r[0]},{r[1]},{r[2]})"

    labels = [
        ("PASS", "ruled plan, all seven checks pass"),
        ("FAIL", "ruled plan, at least one check fails"),
        ("GENERIC", "one zone per floor (no flats drawn)"),
        ("UNDIVIDED", "Not divided — not simulated"),
        ("UNRESOLVED", UNRESOLVED_LABEL),
        ("ERROR", "checks could not run"),
    ]
    legend_rows = "".join(
        f'<div><span class="sw" style="background:{sw(k)}"></span>{t} ({c.get(k, 0)})</div>' if k in ("UNDIVIDED", "UNRESOLVED")
        else f'<div><span class="sw" style="background:{sw(k)}"></span>{t} <b>{c.get(k, 0)}</b></div>'
        for k, t in labels if c.get(k, 0) > 0 or k in ("PASS", "FAIL")
    )
    hud = f'''<div id="hud">
  <h1>{htmllib.escape(dshort)}</h1>
  <div class="sub">{htmllib.escape(district)} &middot; from the simulated IDFs ({htmllib.escape(src_text)})</div>
  <div class="row"><span class="k">Buildings (IDFs read)</span><span>{n}</span></div>
{src_rows}
  <div class="row"><span class="k">Ruled plans (flats drawn)</span><span>{ruled}</span></div>
  <div class="row"><span class="k">One zone per floor</span><span>{n - ruled}</span></div>
  <div class="row"><span class="k">Not divided, not simulated</span><span>{c.get("UNDIVIDED", 0)}</span></div>
{unres_row}  <div class="row"><span class="k">PASS all 7 checks</span><span>{c.get("PASS", 0)}</span></div>
  <div class="row"><span class="k">FAIL</span><span>{c.get("FAIL", 0)}</span></div>
  <div class="row"><span class="k">Checks not run</span><span>{c.get("ERROR", 0)}</span></div>
  <hr>
  <div class="row"><span class="k">Fail by check</span></div>
  <div style="font-size:10.5px;color:#8b95a7;margin-bottom:6px">{fail_line}</div>
  <hr>
  <div class="row"><span class="k">Footprint</span><span style="text-align:right">eu02/{htmllib.escape(district)}/02_residential_manifest.gpkg</span></div>
  <div class="row"><span class="k">Built (UTC)</span><span>{built}</span></div>
  <div class="row"><span class="k">Wall time</span><span>{wall} s</span></div>
  <div class="sub" style="margin-top:6px">zones as written in the IDF &middot; checks run on the typical storey &middot; no simulated result shown</div>
  <div class="btns">
    <button id="bV" class="on">colour: verdict</button>
    <button id="bH">colour: height</button>
    <button id="bC" class="on">show no-census</button>
    <button id="bR">reset view</button>
  </div>
</div>
<div id="legend"><div class="t">plans &middot; {n} buildings</div><div id="lbody">{legend_rows}</div></div>
'''
    return hud


def patch_page(page, hud, district):
    for old, new in JS_PATCHES:
        cnt = page.count(old)
        if cnt != 1:
            raise RuntimeError(f"patch target found {cnt} times: {old[:70]!r}")
    for old, new in JS_PATCHES:
        page = page.replace(old, new)
    i1 = page.index('<div id="hud">')
    i2 = page.index('<div id="modal-backdrop">')
    page = page[:i1] + hud + page[i2:]
    dshort = M07.DSHORT.get(district, district)
    page = re.sub(r"<title>.*?</title>", f"<title>OpenUBEM \u2014 {htmllib.escape(dshort)} \u2014 plans from the simulated IDFs</title>", page, count=1)
    return page


def build_district(district):
    t0 = time.perf_counter()
    plans = read_all(district)
    geoms, dcx, dcy = load_geoms(district)
    und = undivided_ids(district)
    flt = fault_ids(district)
    unr = unresolved_ids(district)
    plates = [build_record(plan, src, geoms.get(plan.building_id), dcx, dcy, plan.building_id in und, plan.building_id in flt, plan.building_id in unr) for plan, src in plans]
    wall = round(time.perf_counter() - t0, 1)
    n = len(plates)
    c = {}
    for p in plates:
        c[p["verdict"]] = c.get(p["verdict"], 0) + 1
    fail_by = {cid: 0 for cid in M08.CHECK_IDS}
    for p in plates:
        for cid, _show, ok in p["checks_list"]:
            if not ok:
                fail_by[cid] += 1
    summary = {
        "census_rows": n, "no_census_row": 0, "manifest_total": n, "status_counts": {},
        "drawn": n, "drawn_pct": 100.0, "pass": c.get("PASS", 0), "pass_pct": 0.0,
        "fail": c.get("FAIL", 0), "generic": c.get("GENERIC", 0), "undivided": c.get("UNDIVIDED", 0), "unresolved": c.get("UNRESOLVED", 0), "refused_k_gt_12": 0,
        "unusable_footprint": 0, "error": c.get("ERROR", 0), "fail_by_check": fail_by,
        "bar_95pct": n, "wall_time_s": wall,
    }
    page = M08.build_html(district, TAG, [_scene_view(p) for p in plates], {}, summary, "", wall)
    n_t06f = sum(1 for p in plates if p["src"] == "t06f")
    hud = make_hud(district, plates, n_t06f, n - n_t06f, wall)
    page = patch_page(page, hud, district)
    page = inject_fields(page, plates)
    dst = PLANS3D_DIR / f"PLANS_{district}_{DATE}.html"
    dst.write_text(page, encoding="utf-8")
    nogeom = sum(1 for p in plates if not p["geom_ok"])
    print(f"{district}: {n} buildings, PASS {c.get('PASS', 0)}, FAIL {c.get('FAIL', 0)}, GENERIC {c.get('GENERIC', 0)}, "
          f"ERROR {c.get('ERROR', 0)}, UNDIVIDED {c.get('UNDIVIDED', 0)}, UNRESOLVED {c.get('UNRESOLVED', 0)}, overlay {sum(1 for p in plates if p['src'] == 'ovl')}, t06f {n_t06f}, no gpkg geometry {nogeom}, {dst.stat().st_size / 1048576:.2f} MB, {wall} s", flush=True)


def _scene_view(p):
    q = dict(p)
    q["checks"] = {cid: {"show": show, "pass": bool(ok)} for cid, show, ok in p["checks_list"]}
    q["dwellings"] = []
    if p["status"] != "direct":
        q.pop("checks", None)
    return q


def inject_fields(page, plates):
    m = re.search(r'(<script type="application/json" id="scene">)(.*?)(</script>)', page, re.DOTALL)
    scene = json.loads(m.group(2))
    by_id = {p["building_id"]: p for p in plates}
    for b in scene["buildings"]:
        p = by_id[b["id"]]
        b["zn"], b["up"] = p["zn"], p["up"]
        b["fs"], b["fk"], b["fn"], b["fo"], b["sg"], b["nt"], b["sb"] = p["fs"], p["fk"], p["fn"], p["fo"], p["sg"], p["nt"], p["sb"]
        b["ch"] = [list(c) for c in p["checks_list"]]
        b["fl"] = []
        b["stem"] = p["stem"]
    new = json.dumps(scene, separators=(",", ":"))
    return page[:m.start(2)] + new + page[m.end(2):]


def shoelace(ring):
    x0, y0 = ring[0]
    t = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0] - x0, ring[i][1] - y0
        x2, y2 = ring[(i + 1) % n][0] - x0, ring[(i + 1) % n][1] - y0
        t += x1 * y2 - x2 * y1
    return abs(t) / 2.0


def has_eui_key(o):
    if isinstance(o, dict):
        return any("eui" in str(k).lower() or has_eui_key(v) for k, v in o.items())
    if isinstance(o, list):
        return any(has_eui_key(v) for v in o)
    return False


def verify_district(district):
    plans = read_all(district)
    page = (PLANS3D_DIR / f"PLANS_{district}_{DATE}.html").read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="scene">(.*?)</script>', page, re.DOTALL)
    parse_ok = True
    try:
        scene = json.loads(m.group(1))
    except Exception:
        parse_ok = False
        scene = {"buildings": []}
    B = {b["id"]: b for b in scene["buildings"]}
    M = len(plans)
    p1 = sum(1 for plan, _ in plans if plan.building_id in B)
    p2_b, p2_s, p2_s_tot = 0, 0, 0
    p3_eui = has_eui_key(scene)
    p3_storey = 0
    for plan, _ in plans:
        b = B.get(plan.building_id)
        if b is None:
            continue
        groups = {}
        for z in plan.zones:
            groups.setdefault(z.storey, []).append(z)
        gkeys = sorted(groups)
        ok_b = True
        for s in range(plan.storey_count):
            p2_s_tot += 1
            idf_area = sum(z.area_m2 for z in groups[gkeys[b["sg"][s]]]) if s < len(b["sg"]) else -1
            drawn = sum(shoelace(r) for zone in b["fs"][b["sg"][s]] for r in zone) if s < len(b["sg"]) else 0
            if idf_area > 0 and abs(drawn - idf_area) <= AREA_TOL * idf_area:
                p2_s += 1
            else:
                ok_b = False
        p2_b += 1 if ok_b else 0
        if len(b["sg"]) == plan.storey_count and b["l"] == plan.storey_count and len(b["fs"]) == plan.zone_storey_group_count:
            p3_storey += 1
    size = (PLANS3D_DIR / f"PLANS_{district}_{DATE}.html").stat().st_size / 1048576
    print(f"{district} P1 {p1} of {M}; P2 buildings {p2_b} of {M}, storeys {p2_s} of {p2_s_tot}; "
          f"P3 parses {parse_ok}, eui keys {'YES' if p3_eui else 0}, storey list {p3_storey} of {M}; size {size:.2f} MB", flush=True)
    rng = random.Random(7)
    pool = [pl for pl, _ in plans]
    pick = [pl for pl in pool if pl.building_id == PROBE_ID] + rng.sample(pool, 5)
    for plan in pick:
        b = B[plan.building_id]
        groups = {}
        for z in plan.zones:
            groups.setdefault(z.storey, []).append(z)
        gkeys = sorted(groups)
        idf_dw = [sum(1 for z in groups[g] if z.kind == "dwelling") for g in gkeys]
        pg_dw = [sum(1 for k in b["fk"][i] if k == "dwelling") for i in range(len(b["fk"]))]
        pg_area = sum(shoelace(r) for i in range(len(b["fs"])) for zone in b["fs"][i] for r in zone)
        print(f"  {plan.building_id}: storeys idf {plan.storey_count} page {b['l']}; dwellings/storey idf {idf_dw} page {pg_dw}; "
              f"gross area idf {plan.gross_area_m2:.1f} page-zones {pg_area:.1f} page-a {b['a']}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--district", choices=sorted(DISTRICTS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--source-tag")
    ap.add_argument("--date")
    ap.add_argument("--overlay-manifest")
    ap.add_argument("--exclude-csv")
    args = ap.parse_args()
    global DATE, TAG, SOURCE_TAG, UNDIVIDED_CSV, OVERLAY_CSV, EXCLUDE_CSV
    if args.date:
        DATE = args.date
        TAG = f"{DATE} from the simulated IDFs"
    if args.overlay_manifest:
        OVERLAY_CSV = args.overlay_manifest
    if args.exclude_csv:
        EXCLUDE_CSV = args.exclude_csv
    if args.overlay_manifest or args.exclude_csv:
        TAG = f"{DATE} from the simulated IDFs (10-06 models + 193 fixed homes)"
    if args.source_tag:
        SOURCE_TAG = args.source_tag
        UNDIVIDED_CSV = RESIDUAL_DIR / "undivided_excluded_2026-10-05.csv"
    if args.all:
        procs = []
        for d in sorted(DISTRICTS):
            cmd = [sys.executable, __file__, "--district", d] + (["--verify"] if args.verify else [])
            if args.source_tag:
                cmd += ["--source-tag", args.source_tag]
            if args.date:
                cmd += ["--date", args.date]
            if args.overlay_manifest:
                cmd += ["--overlay-manifest", args.overlay_manifest]
            if args.exclude_csv:
                cmd += ["--exclude-csv", args.exclude_csv]
            procs.append(subprocess.Popen(cmd))
        sys.exit(max(p.wait() for p in procs))
    if args.verify:
        verify_district(args.district)
    else:
        build_district(args.district)


if __name__ == "__main__":
    main()
