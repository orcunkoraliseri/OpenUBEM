"""EU-21 district viewer (`D-EU-88`): applies the no-core rules cutter
(`07_nocore_tests.py`, itself importing `04_group_tests.py`/`01_cut_group_plans.py`)
to every census building of one district, draws the whole neighbourhood in 3D, and
on click shows the same TEST-sheet card the rules tests draw -- footprint, flats,
seven checks, no energy. Never runs EnergyPlus, never reads an IDF (`D-EU-55`).

Imports (never copies) `07_nocore_tests.py` for the cutter/checks/card/CSS, and
`generate_eu_3d_viewers.py` for the district-frame ring transform (`_scene_ring`)
and the dark-theme CSS + camera/orbit canvas painter, sliced verbatim out of its
own `HTML_HEADER_TEMPLATE`/`HTML_FOOTER` strings at run time.
"""
import argparse
import collections
import hashlib
import importlib.util as ilu
import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone

import geopandas as gpd

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(ROOT))


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CUTTER_PATH = ROOT / "scripts" / "eu21" / "07_nocore_tests.py"
M07 = _load_module("eu21_m08_m07_nocore_tests", str(CUTTER_PATH))
import scripts.generate_eu_3d_viewers as M3D  # noqa: E402
import scripts.eu20_morphology_atlas as M20

EU02 = ROOT / "openubem" / "outputs" / "eu02"
JSON_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "district_plans"
PLANS3D_DIR = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "plans3D"

CENSUS_BAR_FRACTION = 0.95
CHECK_IDS = ("C1", "C3", "C4", "C5", "C6", "C10", "C11")

COLOR = {
    "PASS": (46, 163, 94),
    "GENERIC": (24, 94, 46),
    "FAIL": (214, 69, 69),
    "REFUSED_K_GT_12": (217, 153, 34),
    "NO_CENSUS_ROW": (120, 128, 140),
    "UNUSABLE_FOOTPRINT": (149, 97, 209),
    "ERROR": (149, 97, 209),
}
LEGEND_LABELS = {
    "PASS": "PASS \u2014 all seven checks",
    "GENERIC": "GENERIC \u2014 uncatalogued fallback (unknown)",
    "FAIL": "FAIL \u2014 at least one check",
    "REFUSED_K_GT_12": "refused, k &gt; 12 — attempted, failed (D-EU-92)",
    "NO_CENSUS_ROW": "no census row (massing only)",
    "UNUSABLE_FOOTPRINT": "unusable footprint",
    "ERROR": "cutter raised",
}
LEGEND_ORDER = ("PASS", "GENERIC", "FAIL", "REFUSED_K_GT_12", "NO_CENSUS_ROW", "UNUSABLE_FOOTPRINT", "ERROR")

# ---------------------------------------------------------------------------
# JS/CSS reused (sliced, not retyped) from generate_eu_3d_viewers.py's own
# template strings, per the plan's dependency decision (3D scene, `:36`/`:160`).

_STYLE_I1 = M3D.HTML_HEADER_TEMPLATE.index("<style>")
_STYLE_I2 = M3D.HTML_HEADER_TEMPLATE.index("</style>") + len("</style>")
STYLE_BLOCK = M3D.HTML_HEADER_TEMPLATE[_STYLE_I1:_STYLE_I2].replace("{{", "{").replace("}}", "}")

_PAINTER_START = 'var cv=document.getElementById("c")'
_PAINTER_END = "function hover(e){"
_P1 = M3D.HTML_FOOTER.index(_PAINTER_START)
_P2 = M3D.HTML_FOOTER.index(_PAINTER_END, _P1)
PAINTER_JS = M3D.HTML_FOOTER[_P1:_P2]

EXTRA_STYLE = (
    "<style>\n"
    "/* Modal popup styles - no-core EU-11 style (D-EU-89) */\n"
    "#modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px);"
    "display:none;align-items:center;justify-content:center;z-index:100}\n"
    "#modal{background:#12161f;border:1px solid #2d3646;border-radius:12px;width:90%;max-width:680px;"
    "max-height:90vh;overflow-y:auto;padding:18px 22px;box-shadow:0 20px 40px rgba(0,0,0,0.6);position:relative}\n"
    "#modal-close{position:absolute;top:14px;right:16px;background:transparent;border:0;color:#8b95a7;"
    "font-size:20px;line-height:1;cursor:pointer;padding:4px 8px;border-radius:4px}\n"
    "#modal-close:hover{color:#fff;background:#1e2634}\n"
    "#m-title{margin:0 0 4px;font-size:16px;color:#8fd0ff;font-family:\"Archivo\",ui-sans-serif,system-ui,sans-serif}\n"
    "#m-sub{color:#8b95a7;font-size:12px;margin-bottom:12px;line-height:1.4}\n"
    ".m-badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;margin-right:6px;font-weight:600;"
    "font-family:\"IBM Plex Mono\",monospace}\n"
    ".m-badge.emitted{background:#173d2a;color:#7ee787;border:1px solid #238636}\n"
    ".m-badge.generic{background:#0e2815;color:#7ee787;border:1px solid #1c6630}\n"
    ".m-badge.fallback{background:#3a2410;color:#f0c07a;border:1px solid #7a4b12}\n"
    ".m-badge.unsim{background:#22272e;color:#8b95a7;border:1px solid #373e47}\n"
    ".m-info-box{background:#161b24;border:1px solid #262d3a;border-radius:8px;padding:10px 12px;font-size:12px;margin-bottom:12px}\n"
    ".m-info-box p{margin:3px 0}\n"
    ".m-info-box code{background:#0d1117;padding:1px 5px;border-radius:3px;font-size:11px;color:#e6e9ef;"
    "font-family:\"IBM Plex Mono\",monospace}\n"
    ".storey-bar{display:flex;align-items:center;gap:6px;margin-bottom:10px;font-size:12px;flex-wrap:wrap}\n"
    ".storey-btn{background:#1a212c;border:1px solid #2d3646;color:#c8d1de;border-radius:4px;padding:3px 8px;font-size:11px;cursor:pointer}\n"
    ".storey-btn.active{background:#1f6feb;border-color:#388bfd;color:#fff;font-weight:bold}\n"
    "#fp-container{background:#0a0d13;border:1px solid #212835;border-radius:8px;padding:12px;display:flex;flex-direction:column;align-items:center;margin-bottom:12px}\n"
    "#fp-canvas{display:block;background:#090c10;border-radius:6px;border:1px solid #1a212d}\n"
    "#m-zones{font-size:11.5px;color:#8b95a7;margin-top:8px;width:100%}\n"
    "#m-zones table{width:100%;border-collapse:collapse;margin-top:4px}\n"
    "#m-zones th,#m-zones td{padding:5px 8px;text-align:left;border-bottom:1px solid #1e2531}\n"
    "#m-zones th{color:#6e7681;font-weight:500;font-family:\"IBM Plex Mono\",monospace;font-size:11px}\n"
    "#m-zones td{font-family:\"IBM Plex Mono\",monospace;font-size:11.5px;color:#c8d1de}\n"
    "#m-zones td code{font-size:11px;color:#8fd0ff}\n"
    ".checks{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}\n"
    ".chk{font-family:\"IBM Plex Mono\",monospace;font-size:11px;padding:2px 7px;border:1px solid #262d3a;border-radius:3px;color:#8b95a7;background:#161b24}\n"
    ".chk.ok{border-color:#238636;color:#7ee787;background:#173d2a}\n"
    ".chk.bad{border-color:#9e3c2c;color:#f59e8b;background:#2e1a16}\n"
    ".tok{font-family:\"IBM Plex Mono\",monospace;font-size:10.5px;color:#f0c07a}\n"
    "#m-note{color:#6e7681;font-size:11px;margin-bottom:8px}\n"
    "</style>"
)


def esc(s):
    return M07.esc(s)


# ---------------------------------------------------------------------------
# T01 -- cut every census building, classify every manifest building.

def district_centroid(geoms, district):
    xs, ys = [], []
    for (d, _bid), g in geoms.items():
        if d != district:
            continue
        c = g.centroid
        xs.append(c.x)
        ys.append(c.y)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def process_census(r, geoms, district):
    bid = r["building_id"]
    grp = M07._M04.cls(r)
    k = r["_n"]
    g = geoms.get((district, bid))
    rec = {
        "building_id": bid, "district": district, "group": grp, "k": k,
        "storeys": r["_st"],
        "declared_dwellings": int(round(float(r["dwellings_total"]))),
        "idf_state": r.get("idf_state", ""),
        "area_m2": round(g.area) if g is not None else 0,
        "height_m": round(r["_st"] * 3.0, 1),
    }
    if g is None:
        rec["status"] = "UNUSABLE_FOOTPRINT"
        rec["message"] = "no manifest geometry for this building_id"
        return rec, g
    usable = M07.usable_polygon(g)
    if usable is None:
        rec["status"] = "UNUSABLE_FOOTPRINT"
        rec["message"] = "footprint not a simple polygon after buffer(0) repair"
        return rec, g
    if k > 12:
        p = M07.centred(usable)
        plate, err = M07.attempt_k_gt_12(grp, r, p, k)
        rec["k_gt_12_attempted"] = True
        if err is None and plate is not None and plate.get("verdict") == "PASS":
            rec.update(plate)
            rec["status"] = "direct"
            return rec, g
        rec["status"] = "REFUSED_K_GT_12"
        rec["message"] = f"k={k} > 12, cut attempted at declared k and failed the seven checks (D-EU-92)"
        rec["area_m2"] = round(usable.area)
        if err is not None:
            rec["k_gt_12_attempt_error"] = err
        elif plate is not None:
            rec["fail_by_check"] = [c for c in CHECK_IDS if not plate.get("checks", {}).get(c, {}).get("pass", True)]
        return rec, g
    p = M07.centred(usable)
    plate = M07.build_plate("district", grp, r, p, k, "own", k)
    rec.update(plate)
    return rec, g


def process_no_census(bid, g, levels_by_id, enable_generic=False):
    lvl = levels_by_id.get(bid)
    try:
        lvlf = float(lvl) if lvl not in (None, "") else 0.0
    except (TypeError, ValueError):
        lvlf = 0.0
    height_m = round(lvlf * 3.0, 1) if lvlf > 0 else 9.0
    storeys = max(1, round(height_m / 3.0))
    area_m2 = round(g.area) if g is not None else 0

    if not enable_generic or g is None:
        return {
            "building_id": bid, "group": None, "k": None,
            "storeys": storeys, "declared_dwellings": None, "idf_state": "",
            "area_m2": area_m2, "height_m": height_m,
            "status": "NO_CENSUS_ROW",
            "message": "manifest building with no morphology_census row (not a morphology failure)",
        }

    usable = M07.usable_polygon(g)
    if usable is None:
        return {
            "building_id": bid, "group": None, "k": None,
            "storeys": storeys, "declared_dwellings": None, "idf_state": "",
            "area_m2": area_m2, "height_m": height_m,
            "status": "UNUSABLE_FOOTPRINT",
            "message": "footprint not a simple polygon after buffer(0) repair",
        }

    m = M20._measure_footprint(usable)
    grp = M07._M04.cls(m)
    k = 1 if grp == "SLIVER" else max(1, min(12, round(usable.area / 70.0)))
    p = M07.centred(usable)

    try:
        res = M07.build_flats(p, k)
        poly, flats = res[0], res[1]
        live = [f for f in flats if not f.is_empty]
        footprint = [list(poly.exterior.coords)] + [list(i.coords) for i in poly.interiors]
        dw = [M07.rings_of(f) for f in live]
        return {
            "building_id": bid, "group": grp, "k": k,
            "storeys": storeys, "declared_dwellings": k * storeys, "idf_state": "",
            "area_m2": round(usable.area), "height_m": height_m,
            "status": "GENERIC_NO_CENSUS",
            "verdict": "GENERIC",
            "message": f"uncatalogued (no census row) -- generic layout at k={k} (~70 m\u00b2/flat, {grp})",
            "footprint": footprint,
            "dwellings": dw,
            "scheme": "nocore_equal_area",
        }
    except Exception as e:
        return {
            "building_id": bid, "group": grp, "k": k,
            "storeys": storeys, "declared_dwellings": None, "idf_state": "",
            "area_m2": round(usable.area), "height_m": height_m,
            "status": "ERROR",
            "message": f"cutter error: {e}",
        }


def build_summary(plates, n_census, n_no_census, wall_time_s):
    status_counts = collections.Counter(p["status"] for p in plates)
    verdict_counts = collections.Counter(p.get("verdict") for p in plates if p["status"] == "direct")
    fail_by_check = {c: 0 for c in CHECK_IDS}
    for p in plates:
        if p["status"] == "direct" and p.get("verdict") == "FAIL":
            for c in CHECK_IDS:
                if not p["checks"][c]["pass"]:
                    fail_by_check[c] += 1
    drawn = status_counts.get("direct", 0)
    passed = verdict_counts.get("PASS", 0)
    failed = verdict_counts.get("FAIL", 0)
    generic = status_counts.get("GENERIC_NO_CENSUS", 0)
    return {
        "census_rows": n_census, "no_census_row": n_no_census,
        "manifest_total": n_census + n_no_census,
        "status_counts": dict(status_counts),
        "drawn": drawn, "drawn_pct": round(100.0 * drawn / n_census, 1) if n_census else 0.0,
        "pass": passed, "pass_pct": round(100.0 * passed / n_census, 1) if n_census else 0.0,
        "fail": failed,
        "generic": generic,
        "refused_k_gt_12": status_counts.get("REFUSED_K_GT_12", 0),
        "unusable_footprint": status_counts.get("UNUSABLE_FOOTPRINT", 0),
        "error": status_counts.get("ERROR", 0),
        "fail_by_check": fail_by_check,
        "bar_95pct": math.ceil(n_census * CENSUS_BAR_FRACTION),
        "wall_time_s": wall_time_s,
    }


def print_summary(district, summary, json_path, html_path=None, html_size=None):
    print(f"=== {district} ===")
    print(f"census rows        {summary['census_rows']}")
    print(f"no-census (mfst)    {summary['no_census_row']}  (outside the 95% denominator)")
    print(f"manifest total      {summary['manifest_total']}")
    print(f"drawn (direct)      {summary['drawn']}  ({summary['drawn_pct']}%)")
    if summary.get("generic"):
        print(f"generic fallback    {summary['generic']}  (dark green, uncatalogued)")
    print(f"PASS                {summary['pass']}  ({summary['pass_pct']}%)")
    print(f"FAIL                {summary['fail']}")
    print(f"refused k>12        {summary['refused_k_gt_12']}")
    print(f"unusable footprint  {summary['unusable_footprint']}")
    print(f"cutter error        {summary['error']}")
    print(f"95% bar             {summary['bar_95pct']} of {summary['census_rows']}")
    print("fail by check       " + " ".join(f"{c}:{summary['fail_by_check'][c]}" for c in CHECK_IDS))
    print(f"wall time           {summary['wall_time_s']} s")
    print(f"json                {json_path}")
    if html_path is not None:
        print(f"html                {html_path}  ({html_size / 1024 / 1024:.2f} MB)")


# ---------------------------------------------------------------------------
# T02 -- the page.

def local_footprint_rings(g):
    if g is None:
        return None
    usable = M07.usable_polygon(g)
    if usable is None:
        return None
    c = M07.centred(usable)
    return [list(c.exterior.coords)] + [list(i.coords) for i in c.interiors]


def make_card_html(rec, idx, geom):
    status = rec["status"]
    uid = f"d{idx}"
    if status == "direct":
        return M07.card(rec, uid, idx)
    grp = M07.disp_title(rec["group"]) if rec.get("group") else "n/a"
    rings = local_footprint_rings(geom)
    svg = M07.drawplan({"footprint": rings, "dwellings": [], "group": rec.get("group") or "n/a"}, uid) if rings else ""
    reason = rec.get("message", status)
    cap = (f'<b>{idx}</b> &middot; {esc(rec["building_id"])} &middot; {esc(grp)} &middot; '
           f'<span class="tok">{esc(status)}</span><br>{esc(reason)}')
    return f'<div class="fig">{svg}<p class="cap">{cap}</p></div>'


def build_html(district, tag, plates, geom_by_bid, summary, cutter_sha256, wall_time_s):
    dshort = M07.DSHORT.get(district, district)

    scene_buildings = []
    for idx, rec in enumerate(plates, start=1):
        status = rec["status"]
        v = rec.get("verdict") if status in ("direct", "GENERIC_NO_CENSUS") else status
        if status == "GENERIC_NO_CENSUS":
            v = "GENERIC"

        fp_raw = rec.get("footprint")
        if not fp_raw and geom_by_bid.get(rec["building_id"]) is not None:
            fp_raw = local_footprint_rings(geom_by_bid[rec["building_id"]])
        fp = [[[round(pt[0], 2), round(pt[1], 2)] for pt in ring] for ring in fp_raw] if fp_raw else []

        fl_raw = rec.get("dwellings") or []
        fl = [[[[round(pt[0], 2), round(pt[1], 2)] for pt in ring] for ring in d] for d in fl_raw if d]

        ch = []
        if status == "direct" and "checks" in rec:
            for c in CHECK_IDS:
                chk_info = rec["checks"].get(c, {})
                ch.append([c, chk_info.get("show", ""), 1 if chk_info.get("pass") else 0])

        scene_buildings.append({
            "id": rec["building_id"],
            "r": rec.get("footprint_scene") or [],
            "h": rec.get("height_m", 9.0),
            "l": rec.get("storeys"),
            "a": rec.get("area_m2"),
            "st": status,
            "v": v,
            "g": M07.disp_title(rec["group"]) if rec.get("group") else "\u2014",
            "k": rec.get("k"),
            "idf": rec.get("idf_state") or "",
            "c": 1 if status == "NO_CENSUS_ROW" else 0,
            "fp": fp,
            "fl": fl,
            "ch": ch,
            "msg": rec.get("message") or rec.get("token") or "",
            "decl": rec.get("declared_dwellings"),
        })

    minx = miny = 1e18
    maxx = maxy = -1e18
    hmax = 1.0
    for b in scene_buildings:
        hmax = max(hmax, b["h"] or 0.0)
        for x, y in b["r"]:
            minx = min(minx, x); maxx = max(maxx, x)
            miny = min(miny, y); maxy = max(maxy, y)
    span = max(maxx - minx, maxy - miny) if scene_buildings and minx < 1e18 else 100.0

    generic_count = summary.get("generic", 0)
    no_census_remaining = max(0, summary["no_census_row"] - generic_count)
    legend_counts = {
        "PASS": summary["pass"],
        "GENERIC": generic_count,
        "FAIL": summary["fail"],
        "REFUSED_K_GT_12": summary["refused_k_gt_12"],
        "NO_CENSUS_ROW": no_census_remaining,
        "UNUSABLE_FOOTPRINT": summary["unusable_footprint"],
        "ERROR": summary["error"],
    }

    scene = {
        "district": district, "tag": tag, "buildings": scene_buildings,
        "span": span, "hmax": round(hmax, 1),
    }

    def swatch(rgb):
        return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"

    legend_rows = "".join(
        f'<div><span class="sw" style="background:{swatch(COLOR[k])}"></span>{LEGEND_LABELS[k]} '
        f'<b>{legend_counts[k]}</b></div>' for k in LEGEND_ORDER if legend_counts.get(k, 0) > 0 or k in ("PASS", "FAIL")
    )
    fail_line = " &middot; ".join(f'{c} {summary["fail_by_check"][c]}' for c in CHECK_IDS)
    built_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    generic_hud = f'<div class="row"><span class="k">Generic fallback (unknown)</span><span>{generic_count}</span></div>' if generic_count else ""

    hud = f'''<div id="hud">
  <h1>{esc(dshort)}</h1>
  <div class="sub">{esc(district)} &middot; EU-21 no-core rules &middot; D-EU-88 &middot; tag {esc(tag)}</div>
  <div class="row"><span class="k">Census rows</span><span>{summary["census_rows"]}</span></div>
  <div class="row"><span class="k">Drawn (direct cut)</span><span>{summary["drawn"]} ({summary["drawn_pct"]}%)</span></div>
  {generic_hud}
  <div class="row"><span class="k">PASS all 7 checks</span><span>{summary["pass"]} ({summary["pass_pct"]}%)</span></div>
  <div class="row"><span class="k">FAIL</span><span>{summary["fail"]}</span></div>
  <div class="row"><span class="k">Refused k&gt;12</span><span>{summary["refused_k_gt_12"]}</span></div>
  <div class="row"><span class="k">Unusable footprint</span><span>{summary["unusable_footprint"]}</span></div>
  <div class="row"><span class="k">Cutter error</span><span>{summary["error"]}</span></div>
  <div class="row"><span class="k">No census row</span><span>{no_census_remaining}</span></div>
  <div class="row"><span class="k">95% bar</span><span>{summary["bar_95pct"]} of {summary["census_rows"]}</span></div>
  <hr>
  <div class="row"><span class="k">Fail by check</span></div>
  <div style="font-size:10.5px;color:#8b95a7;margin-bottom:6px">{fail_line}</div>
  <hr>
  <div class="row"><span class="k">Census</span><span style="text-align:right">EU-20/morphology_census.csv</span></div>
  <div class="row"><span class="k">Manifest</span><span style="text-align:right">eu02/{esc(district)}/02_residential_manifest.gpkg</span></div>
  <div class="row"><span class="k">Cutter sha256</span><span>{cutter_sha256[:12]}&hellip;</span></div>
  <div class="row"><span class="k">MAX_FLAT_ASPECT</span><span>{M07.MAX_FLAT_ASPECT} \u2014 not frozen (D-EU-86 clause 2, FINDING 242)</span></div>
  <div class="row"><span class="k">Built (UTC)</span><span>{built_utc}</span></div>
  <div class="row"><span class="k">Wall time</span><span>{wall_time_s} s</span></div>
  <div class="sub" style="margin-top:6px">D-EU-79&hellip;D-EU-89 &middot; footprint + storeys + flats only, no simulated result, no IDF (D-EU-55)</div>
  <div class="btns">
    <button id="bV" class="on">colour: verdict</button>
    <button id="bH">colour: height</button>
    <button id="bC" class="on">show no-census</button>
    <button id="bR">reset view</button>
  </div>
</div>
<div id="legend"><div class="t">status &middot; {sum(legend_counts.values())} buildings</div><div id="lbody">{legend_rows}</div></div>'''

    modal = '''<div id="modal-backdrop">
  <div id="modal">
    <button id="modal-close" title="Close (Esc)">&times;</button>
    <h2 id="m-title"></h2>
    <div id="m-sub"></div>
    <div class="m-info-box" id="m-status-box"></div>
    <div class="storey-bar" id="m-storey-bar"></div>
    <div id="m-note">one plate, dwellings only &mdash; the same plan on every storey (D-EU-79)</div>
    <div id="fp-container">
      <canvas id="fp-canvas" width="580" height="320"></canvas>
      <div id="m-zones"></div>
    </div>
  </div>
</div>'''

    status_color_json = json.dumps({k: list(v) for k, v in COLOR.items()}, separators=(",", ":"))

    script_js = f'''var D=JSON.parse(document.getElementById("scene").textContent);
var B=D.buildings;

var RAMP=[[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
function ramp(t){{t=Math.max(0,Math.min(1,t));var s=t*(RAMP.length-1),i=Math.floor(s),f=s-i;
  if(i>=RAMP.length-1){{i=RAMP.length-2;f=1;}}
  var a=RAMP[i],b=RAMP[i+1];
  return [a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f];}}
var STATUS_COLOR={status_color_json};
var mode="v";
function baseColor(b){{
  if(mode==="h")return ramp(b.h/(D.hmax||30));
  return STATUS_COLOR[b.v]||[149,97,209];
}}

{PAINTER_JS}
function hover(e){{
  var b=findHit(e.clientX, e.clientY);
  if(b){{
    tip.innerHTML="<b>"+b.id+"</b><br>"+b.g+
      "<br>k "+(b.k===null?"\u2014":b.k)+" flats/floor &middot; "+(b.l===null?"\u2014":b.l)+" storeys"+
      "<br>height "+b.h.toFixed(1)+" m &middot; footprint "+(b.a||0).toFixed(0)+" m\u00b2"+
      "<br>status: <b>"+b.st+"</b>"+
      "<br><span style='color:#7fb3e0;font-size:10.5px;'>click for floor plan &rarr;</span>";
    tip.style.display="block";
    tip.style.left=Math.min(e.clientX+14,window.innerWidth-282)+"px";
    tip.style.top=(e.clientY+14)+"px";
    return;
  }}
  hide();
}}

var ZONE_COLORS=[
  "#287294",
  "#328452",
  "#937320",
  "#9e4438",
  "#7b5294",
  "#b35c34",
  "#2c8a85",
  "#8a4f7d",
  "#4f6b96",
  "#82802b",
  "#96425a",
  "#387680"
];

var modalBackdrop=document.getElementById("modal-backdrop"),
    modalClose=document.getElementById("modal-close"),
    mTitle=document.getElementById("m-title"),
    mSub=document.getElementById("m-sub"),
    mStatusBox=document.getElementById("m-status-box"),
    mStoreyBar=document.getElementById("m-storey-bar"),
    mZones=document.getElementById("m-zones"),
    fpCanvas=document.getElementById("fp-canvas"),
    fpCtx=fpCanvas.getContext("2d");

var currentModalBuilding=null;
var currentStoreyIndex=0;

function closePopup(){{modalBackdrop.style.display="none";cv.focus();}}
modalClose.onclick=closePopup;
modalBackdrop.onclick=function(e){{if(e.target===modalBackdrop)closePopup();}};
window.addEventListener("keydown",function(e){{if(e.key==="Escape")closePopup();}});

function openPopup(b){{
  hide();
  currentModalBuilding=b;
  currentStoreyIndex=0;
  mTitle.textContent=b.id+" \u2014 "+b.g;
  var storeys=b.l||1;
  var k=(b.k===null||b.k===undefined)?"\u2014":b.k;
  var dwellings=(b.decl===null||b.decl===undefined)?"\u2014":b.decl;
  var area=(b.a||0).toFixed(0);
  var declLabel = (b.v==="GENERIC"||b.st==="GENERIC_NO_CENSUS") ? "<b>Dwellings (est):</b> " : "<b>Dwellings (census):</b> ";
  mSub.innerHTML="<b>Storeys:</b> "+storeys+" &middot; "+
    "<b>Flats per floor:</b> "+k+" &middot; "+
    declLabel+dwellings+" &middot; "+
    "<b>Height:</b> "+b.h.toFixed(1)+" m <i>(from storeys \u00d7 3.0 m)</i> &middot; "+
    "<b>Footprint:</b> "+area+" m\u00b2";

  var statusHtml="";
  if(b.st==="direct"){{
    var chipsHtml="";
    var failList=[];
    if(b.ch&&b.ch.length>0){{
      chipsHtml='<div class="checks">';
      for(var ci=0;ci<b.ch.length;ci++){{
        var cid=b.ch[ci][0],cval=b.ch[ci][1],cpass=b.ch[ci][2];
        var ccls=cpass?"ok":"bad";
        if(!cpass)failList.push(cid);
        chipsHtml+='<span class="chk '+ccls+'">'+cid+' '+cval+'</span> ';
      }}
      chipsHtml+='</div>';
    }}
    if(b.v==="PASS"){{
      statusHtml="<span class='m-badge emitted'>PASS ALL 7 CHECKS</span> "+
        "<b>Scheme:</b> nocore equal-area cut.<br>"+
        "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0 6px;'>Divided into "+k+" dwellings only (no core/circulation, D-EU-79). Extruded across all "+storeys+" storeys.</p>"+
        chipsHtml;
    }}else{{
      statusHtml="<span class='m-badge fallback'>FAIL</span> "+
        "<b>Failing checks:</b> "+(failList.length>0?failList.join(", "):"see checks")+".<br>"+
        "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0 6px;'>Drawn at "+k+" dwellings only. Evaluated against all 7 no-core rules.</p>"+
        chipsHtml;
    }}
  }}else if(b.st==="GENERIC_NO_CENSUS"||b.v==="GENERIC"){{
    statusHtml="<span class='m-badge generic'>GENERIC (NO CENSUS)</span> "+
      "<b>Scheme:</b> nocore generic floor plan.<br>"+
      "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0 6px;'>Uncatalogued building with no census row (unknown). Partitioned generically into "+k+" dwelling(s) based on "+b.g+" morphology rule (~70 m\u00b2 per flat). Extruded across "+storeys+" storeys.</p>";
  }}else if(b.st==="REFUSED_K_GT_12"){{
    statusHtml="<span class='m-badge fallback'>REFUSED (k &gt; 12)</span> <code>D-EU-92</code><br>"+
      "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0;'>k="+k+" &gt; 12 flats/floor, refused by design ceiling.</p>";
  }}else if(b.st==="NO_CENSUS_ROW"){{
    statusHtml="<span class='m-badge unsim'>NO CENSUS ROW</span><br>"+
      "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0;'>Manifest building with no morphology census row (outside 95% denominator).</p>";
  }}else{{
    statusHtml="<span class='m-badge fallback'>"+b.st+"</span><br>"+
      "<p style='color:#8b95a7;font-size:11.5px;margin:4px 0;'>"+(b.msg||"Cutter raised an exception")+"</p>";
  }}
  mStatusBox.innerHTML=statusHtml;

  if(b.fl&&b.fl.length>0&&storeys>1){{
    var sHtml="<span style='color:#8b95a7;margin-right:4px;'>Storey:</span> ";
    for(var s=0;s<storeys;s++){{
      var z0=(s*3.0).toFixed(0),z1=((s+1)*3.0).toFixed(0);
      sHtml+="<button class='storey-btn"+(s===0?" active":"")+"' onclick='selectStorey("+s+")'>F"+s+" ("+z0+"\u2013"+z1+"m)</button> ";
    }}
    mStoreyBar.innerHTML=sHtml;
    mStoreyBar.style.display="flex";
  }}else if(storeys>1){{
    mStoreyBar.innerHTML="<span style='color:#8b95a7;'>"+b.st+" &middot; "+storeys+" stacked storeys</span>";
    mStoreyBar.style.display="flex";
  }}else{{
    mStoreyBar.innerHTML="<span style='color:#8b95a7;'>Single storey (0.0 to 3.0 m)</span>";
    mStoreyBar.style.display="flex";
  }}

  drawFloorPlan(b,0,-1);
  modalBackdrop.style.display="flex";
}}

window.selectStorey=function(sIdx){{
  currentStoreyIndex=sIdx;
  var btns=mStoreyBar.getElementsByClassName("storey-btn");
  for(var i=0;i<btns.length;i++){{
    btns[i].classList.toggle("active",i===sIdx);
  }}
  if(currentModalBuilding){{
    drawFloorPlan(currentModalBuilding,sIdx,-1);
  }}
}};

window.highlightDwelling=function(zIdx){{
  if(currentModalBuilding)drawFloorPlan(currentModalBuilding,currentStoreyIndex,zIdx);
}};
window.unhighlightDwelling=function(){{
  if(currentModalBuilding)drawFloorPlan(currentModalBuilding,currentStoreyIndex,-1);
}};

function drawFloorPlan(b,sIdx,hlIdx){{
  var cw=fpCanvas.width,ch=fpCanvas.height;
  fpCtx.clearRect(0,0,cw,ch);

  var rings=(b.fp&&b.fp.length>0)?b.fp:[b.r];
  if(!rings||rings.length===0||rings[0].length===0)return;

  var minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
  for(var k=0;k<rings.length;k++){{
    var rk=rings[k];
    for(var i=0;i<rk.length;i++){{
      if(rk[i][0]<minx)minx=rk[i][0];if(rk[i][0]>maxx)maxx=rk[i][0];
      if(rk[i][1]<miny)miny=rk[i][1];if(rk[i][1]>maxy)maxy=rk[i][1];
    }}
  }}
  var bw=maxx-minx,bh=maxy-miny;
  var bcx=(minx+maxx)/2,bcy=(miny+maxy)/2;
  var pad=44;
  var sc=Math.min((cw-pad*2)/Math.max(bw,5),(ch-pad*2)/Math.max(bh,5));

  function fx(x){{return (x-bcx)*sc+cw/2;}}
  function fy(y){{return -(y-bcy)*sc+ch/2;}}

  fpCtx.beginPath();
  for(var k=0;k<rings.length;k++){{
    var rk=rings[k];
    for(var j=0;j<rk.length;j++){{
      var X=fx(rk[j][0]),Y=fy(rk[j][1]);
      if(j===0)fpCtx.moveTo(X,Y);else fpCtx.lineTo(X,Y);
    }}
    fpCtx.closePath();
  }}
  fpCtx.fillStyle="rgba(255,255,255,0.04)";
  fpCtx.fill("evenodd");
  fpCtx.strokeStyle="#8b95a7";
  fpCtx.lineWidth=2;
  fpCtx.stroke();

  var fl=b.fl||[];
  var zonesTable="";
  if(fl.length>0){{
    zonesTable="<table><thead><tr><th>Zone Name</th><th>Colour</th><th>Dwelling Index</th><th>Storey Elevation</th></tr></thead><tbody>";
    var zLo=(sIdx*3.0).toFixed(0),zHi=((sIdx+1)*3.0).toFixed(0);
    for(var z=0;z<fl.length;z++){{
      var flatRings=fl[z];
      var zc=ZONE_COLORS[z%ZONE_COLORS.length];
      fpCtx.beginPath();
      for(var rk=0;rk<flatRings.length;rk++){{
        var zr=flatRings[rk];
        for(var v=0;v<zr.length;v++){{
          var ZX=fx(zr[v][0]),ZY=fy(zr[v][1]);
          if(v===0)fpCtx.moveTo(ZX,ZY);else fpCtx.lineTo(ZX,ZY);
        }}
        fpCtx.closePath();
      }}
      fpCtx.fillStyle=zc;
      fpCtx.fill("evenodd");
      if(hlIdx===z){{
        fpCtx.strokeStyle="#ffffff";
        fpCtx.lineWidth=2.4;
      }}else{{
        fpCtx.strokeStyle="rgba(255,255,255,0.85)";
        fpCtx.lineWidth=1.4;
      }}
      fpCtx.stroke();

      var extRing=flatRings[0];
      var area=0,cx=0,cy=0;
      for(var i=0,j=extRing.length-1;i<extRing.length;j=i++){{
        var p1=extRing[j],p2=extRing[i];
        var f=p1[0]*p2[1]-p2[0]*p1[1];
        area+=f;
        cx+=(p1[0]+p2[0])*f;
        cy+=(p1[1]+p2[1])*f;
      }}
      var zcx,zcy;
      if(Math.abs(area)>1e-5){{
        zcx=fx(cx/(3*area));
        zcy=fy(cy/(3*area));
      }}else{{
        var sx=0,sy=0;
        for(var i=0;i<extRing.length;i++){{sx+=extRing[i][0];sy+=extRing[i][1];}}
        zcx=fx(sx/extRing.length);
        zcy=fy(sy/extRing.length);
      }}
      fpCtx.save();
      fpCtx.shadowColor="rgba(0,0,0,0.85)";
      fpCtx.shadowBlur=4;
      fpCtx.fillStyle="#ffffff";
      fpCtx.font="bold 11px sans-serif";
      fpCtx.textAlign="center";
      fpCtx.textBaseline="middle";
      fpCtx.fillText("D"+(z+1),zcx,zcy);
      fpCtx.restore();

      var zName=b.id+"_F"+sIdx+"_dwelling_"+z;
      var rowStyle=hlIdx===z?" style='background:#1b2432;cursor:pointer'":" style='cursor:pointer'";
      zonesTable+="<tr"+rowStyle+" onmouseenter='highlightDwelling("+z+")' onmouseleave='unhighlightDwelling()'><td><code>"+zName+"</code></td>"+
        "<td><span style='display:inline-block;width:13px;height:13px;background:"+zc+";border:1px solid rgba(255,255,255,0.7);border-radius:2px;vertical-align:middle;'></span></td>"+
        "<td>Dwelling "+(z+1)+"</td>"+
        "<td>"+zLo+"\u2013"+zHi+" m</td></tr>";
    }}
    zonesTable+="</tbody></table>";
  }}else{{
    fpCtx.fillStyle="#8b95a7";
    fpCtx.font="12px sans-serif";
    fpCtx.textAlign="center";
    fpCtx.textBaseline="middle";
    fpCtx.fillText(b.msg||"Footprint outline only",cw/2,ch/2);
  }}
  mZones.innerHTML=zonesTable;

  var barMeters=10;
  if(sc>15)barMeters=5;
  if(sc>35)barMeters=2;
  if(sc<5)barMeters=20;
  if(sc<2)barMeters=50;
  var barPx=barMeters*sc;
  var bx0=24,by0=ch-20;
  fpCtx.beginPath();
  fpCtx.moveTo(bx0,by0-4);fpCtx.lineTo(bx0,by0);fpCtx.lineTo(bx0+barPx,by0);fpCtx.lineTo(bx0+barPx,by0-4);
  fpCtx.strokeStyle="#c9d1d9";
  fpCtx.lineWidth=1.5;
  fpCtx.stroke();
  fpCtx.fillStyle="#8b95a7";
  fpCtx.font="10px monospace";
  fpCtx.textAlign="left";
  fpCtx.textBaseline="bottom";
  fpCtx.fillText(barMeters+" m",bx0,by0-5);

  var nx0=cw-28,ny0=26;
  fpCtx.beginPath();
  fpCtx.moveTo(nx0,ny0-10);fpCtx.lineTo(nx0-5,ny0+6);fpCtx.lineTo(nx0,ny0+2);fpCtx.lineTo(nx0+5,ny0+6);
  fpCtx.closePath();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.fill();
  fpCtx.fillStyle="#7fb3e0";
  fpCtx.font="bold 10px sans-serif";
  fpCtx.textAlign="center";
  fpCtx.fillText("N",nx0,ny0+16);
}}

function setMode(m,btn){{
  mode=m;["bV","bH"].forEach(function(id){{document.getElementById(id).classList.remove("on");}});
  btn.classList.add("on");draw();
}}
document.getElementById("bV").onclick=function(){{setMode("v",this);}};
document.getElementById("bH").onclick=function(){{setMode("h",this);}};
document.getElementById("bC").onclick=function(){{showExc=!showExc;this.classList.toggle("on",showExc);draw();}};
document.getElementById("bR").onclick=function(){{fit();draw();}};

resize();fit();draw();
'''

    page = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>OpenUBEM \u2014 {esc(dshort)} \u2014 no-core rules ({esc(tag)})</title>\n"
        f"{STYLE_BLOCK}\n{EXTRA_STYLE}\n</head>\n<body>\n"
        "<canvas id=\"c\"></canvas>\n"
        f"{hud}\n{modal}\n"
        "<div id=\"tip\"></div>\n"
        "<div id=\"help\">click building for floor plan &middot; drag orbit &middot; shift-drag pan &middot; wheel zoom</div>\n"
        f'<script type="application/json" id="scene">{json.dumps(scene, separators=(",", ":"))}</script>\n'
        f"<script>(function(){{\n{script_js}\n}})();</script>\n"
        "</body>\n</html>\n"
    )
    return page


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--district", required=True, choices=list(M07._M04.DISTRICTS))
    ap.add_argument("--tag", required=True)
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    ap.add_argument("--render-only", action="store_true", help="Re-render HTML from existing evidence JSON")
    ap.add_argument("--generic-no-census", action="store_true", help="Generate generic floor plans for no-census buildings")
    args = ap.parse_args()
    district, tag = args.district, args.tag

    json_path = JSON_DIR / f"{district}_nocore_{tag}.json"
    html_path = PLANS3D_DIR / f"PLANS_{district}_nocore_{tag}.html"

    if args.render_only:
        src_json = json_path if json_path.exists() else JSON_DIR / f"{district}_nocore_2026-09-03.json"
        if not src_json.exists():
            print(f"ERROR: evidence JSON not found: {src_json}")
            sys.exit(1)
        if html_path.exists() and not args.overwrite:
            print(f"REFUSE: target HTML already exists -- {html_path}")
            sys.exit(1)

        t0 = time.perf_counter()
        evidence = json.loads(src_json.read_text(encoding="utf-8"))
        plates = evidence["plates"]
        summary = evidence["summary"]
        cutter_sha256 = evidence["cutter_sha256"]

        gdf = gpd.read_file(EU02 / district / "02_residential_manifest.gpkg")
        idcol = "building_id" if "building_id" in gdf.columns else gdf.columns[0]
        geom_by_bid = {str(row[idcol]): row.geometry for _, row in gdf.iterrows()}

        wall_time_s = summary.get("wall_time_s", 0.0)
        html = build_html(district, tag, plates, geom_by_bid, summary, cutter_sha256, wall_time_s)
        PLANS3D_DIR.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")
        html_size = html_path.stat().st_size
        print_summary(district, summary, src_json, html_path, html_size)
        return

    if not args.overwrite and (json_path.exists() or html_path.exists()):
        existing = json_path if json_path.exists() else html_path
        print(f"REFUSE: target already exists -- {existing}")
        sys.exit(1)

    t0 = time.perf_counter()
    geoms, rows, bygroup, perfloor, storeys = M07.load_universe()
    cutter_sha256 = hashlib.sha256(CUTTER_PATH.read_bytes()).hexdigest()

    census_rows = [r for r in rows if r["district"] == district]
    census_ids = {r["building_id"] for r in census_rows}
    manifest_ids = {bid for (d, bid) in geoms if d == district}
    no_census_ids = sorted(manifest_ids - census_ids)

    gdf = gpd.read_file(EU02 / district / "02_residential_manifest.gpkg")
    idcol = "building_id" if "building_id" in gdf.columns else gdf.columns[0]
    levels_by_id = {str(row[idcol]): row.get("levels") for _, row in gdf.iterrows()}

    dcx, dcy = district_centroid(geoms, district)

    plates = []
    geom_by_bid = {}

    for i, r in enumerate(census_rows, start=1):
        rec, g = process_census(r, geoms, district)
        bid = rec["building_id"]
        geom_by_bid[bid] = g
        if g is not None:
            ring = list(g.exterior.coords)[:-1]
            rec["footprint_scene"] = M3D._scene_ring(ring, (0.0, 0.0), dcx, dcy)
        else:
            rec["footprint_scene"] = []
        plates.append(rec)
        if i % 100 == 0:
            print(f"  {i}/{len(census_rows)} census buildings cut", flush=True)

    for bid in no_census_ids:
        g = geoms[(district, bid)]
        geom_by_bid[bid] = g
        rec = process_no_census(bid, g, levels_by_id, enable_generic=args.generic_no_census)
        rec["building_id"] = bid
        rec["district"] = district
        ring = list(g.exterior.coords)[:-1]
        rec["footprint_scene"] = M3D._scene_ring(ring, (0.0, 0.0), dcx, dcy)
        plates.append(rec)

    wall_time_s = round(time.perf_counter() - t0, 1)
    summary = build_summary(plates, len(census_rows), len(no_census_ids), wall_time_s)

    JSON_DIR.mkdir(parents=True, exist_ok=True)
    evidence = {
        "district": district, "tag": tag,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cutter_sha256": cutter_sha256,
        "max_flat_aspect": M07.MAX_FLAT_ASPECT,
        "summary": summary,
        "plates": plates,
    }
    json_path.write_text(json.dumps(evidence, separators=(",", ":")), encoding="utf-8")

    html = build_html(district, tag, plates, geom_by_bid, summary, cutter_sha256, wall_time_s)
    PLANS3D_DIR.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    html_size = html_path.stat().st_size

    print_summary(district, summary, json_path, html_path, html_size)


if __name__ == "__main__":
    main()
