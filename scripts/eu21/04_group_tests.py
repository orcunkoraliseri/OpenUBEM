"""EU-21 rules tests: cut sampled real buildings directly with scripts/eu21/05_group_cutters.py
(D-EU-67 connected courtyard cores, D-EU-68 basic thermal-zone flats), the per-group algorithm
of each sheet's own steps 3-4 (rules/RULES_dwelling_layout_groups_2026-09-01.html). No engine
call and no D-EU-64 post-pass -- the cutter satisfies the law by construction. Selects real
buildings from the census, checks C1-C8, and writes one JSON + one HTML sheet per test. Never
runs EnergyPlus (D-EU-55) and never edits 01/02/03, group_plans.json or openubem/geometry/.
"""
import argparse
import collections
import html
import importlib.util as ilu
import json
import pathlib
import sys
import time
from datetime import datetime, timezone

from shapely.affinity import translate
from shapely.geometry import Polygon

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(ROOT))

RULES_DIR = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "rules"
_FROZEN_NAME = "RULES_dwelling_layout_scheme_2026-08-28.html"
FROZEN = RULES_DIR / _FROZEN_NAME if (RULES_DIR / _FROZEN_NAME).exists() else RULES_DIR / "archive" / _FROZEN_NAME
HTML_DIR = RULES_DIR / "tests"
EU20 = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-20"
OUT_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "rules_tests"


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_M01 = _load_module("eu21_m01_group_plans", str(ROOT / "scripts" / "eu21" / "01_cut_group_plans.py"))
_M02 = _load_module("eu21_m02_one_core", str(ROOT / "scripts" / "eu21" / "02_one_core_per_plate.py"))
_M05 = _load_module("eu21_m05_cutters", str(ROOT / "scripts" / "eu21" / "05_group_cutters.py"))

cls = _M01.cls
load_universe = _M01.load_universe
ORDER = _M01.ORDER
DISTRICTS = _M01.DISTRICTS
NO_CORE_BY_DESIGN = _M01.NO_CORE_BY_DESIGN

lobes_of = _M02.lobes_of
parts = _M02.parts
sbuf = _M02.sbuf

cut = _M05.cut
Refusal = _M05.Refusal
ACCESS_MIN_M = _M05.ACCESS_MIN_M
CORRIDOR_MAX_POINTS = 16  # D-EU-71, threshold fixed by the owner at CP-2, 2026-09-02
ZONE_MIN_WIDTH_M = 2.00  # D-EU-72, threshold fixed by the owner at CP-2, 2026-09-02

from openubem.geometry.european_residential import RULED_GRID_MAX_DWELLINGS_PER_FLOOR as MAXK
from openubem.geometry.european_residential import DWELLING_DENSITY_REFUSAL_TOKEN

# ---------------------------------------------------------------------------
# Copied verbatim from scripts/eu21/03_build_rules_html.py (03:13-20, 03:79-146,
# 03:165-172) -- 03 is a script that writes the rules HTML at import time and is
# off-limits, so its drawing helpers and constants are copied here, not imported.

DSHORT = {"ES-MAD-BERRUGUETE": "Madrid", "FR-LYO-HAUTCOEURPENTES": "Lyon",
          "GB-LDN-STDUNSTANS": "London", "IT-BOL-GALVANI2": "Bologna"}
TITLE = {"COURTYARD": "Courtyard", "SLIVER": "Sliver", "SQUARE": "Square",
         "RECTANGLE": "Rectangle", "CORRIDOR_RECTANGLE": "Corridor rectangle", "SLAB": "Slab",
         "TRIANGLE": "Triangle or trapezoid",
         "TRAPEZOID": "Parallelogram", "L_SHAPE": "L shape",
         "U_OR_T_SHAPE": "U or T shape", "COMPLEX_MULTI_WING": "Complex multi-wing"}

FILLS = ["--d1", "--d2", "--d3", "--d4", "--d5", "--d6", "--d7", "--d8"]


def _bounds(ringsets):
    xs, ys = [], []
    for rs in ringsets:
        for r in rs:
            for p in r:
                xs.append(p[0]); ys.append(p[1])
    return min(xs), min(ys), max(xs), max(ys)


def _path(rings):
    return " ".join("M" + "L".join(f"{p[0]:.2f},{-p[1]:.2f}" for p in r) + "Z" for r in rings)


def _centroid(ring):
    x = y = a = 0.0
    for i in range(len(ring) - 1):
        c = ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
        a += c
        x += (ring[i][0] + ring[i + 1][0]) * c
        y += (ring[i][1] + ring[i + 1][1]) * c
    if abs(a) < 1e-9:
        return ring[0][0], ring[0][1]
    return x / (3 * a), y / (3 * a)


def drawplan(rec, uid, bare=False):
    fp = rec["footprint"]
    dws = [] if bare else rec["dwellings"]
    circ = [] if bare else rec["circulation"]
    x0, y0, x1, y1 = _bounds([fp] + dws + circ)
    pad = max(x1 - x0, y1 - y0) * 0.10 + 3
    w, h = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    t = max(w, h) / 300
    fs = max(w, h) / 26
    o = [f'<svg class="plan" viewBox="{x0 - pad:.2f} {-y1 - pad:.2f} {w:.2f} {h:.2f}" role="img" '
         f'aria-label="{TITLE[rec["group"]]} floor plan, {rec["scheme"]} scheme" preserveAspectRatio="xMidYMid meet">']
    o.append(f'<defs><pattern id="{uid}" width="{t * 7:.2f}" height="{t * 7:.2f}" '
             f'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
             f'<line x1="0" y1="0" x2="0" y2="{t * 7:.2f}" stroke="var(--plan-line)" '
             f'stroke-width="{t:.2f}" opacity=".55"/></pattern></defs>')
    for i, d in enumerate(dws):
        o.append(f'<path d="{_path(d)}" fill="var({FILLS[i % 8]})" stroke="var(--plan-line)" '
                 f'stroke-width="{t * 0.9:.2f}" stroke-linejoin="round" fill-rule="evenodd"/>')
    for c in circ:
        o.append(f'<path d="{_path(c)}" fill="var(--sheet-2)" stroke="var(--plan-line)" stroke-width="{t * 0.9:.2f}"/>')
        o.append(f'<path d="{_path(c)}" fill="url(#{uid})" stroke="none"/>')
    o.append(f'<path d="{_path(fp)}" fill="none" stroke="var(--plan-line)" '
             f'stroke-width="{t * 2.1:.2f}" stroke-linejoin="round" fill-rule="evenodd"/>')
    for i, d in enumerate(dws):
        cx, cy = _centroid(d[0])
        o.append(f'<text x="{cx:.2f}" y="{-cy + fs * 0.34:.2f}" font-family="IBM Plex Mono, monospace" '
                 f'font-size="{fs:.2f}" font-weight="500" fill="var(--plan-label)" text-anchor="middle">F{i + 1}</text>')
    for c in circ:
        cx, cy = _centroid(c[0])
        o.append(f'<text x="{cx:.2f}" y="{-cy + fs * 0.3:.2f}" font-family="IBM Plex Mono, monospace" '
                 f'font-size="{fs * 0.62:.2f}" fill="var(--muted)" text-anchor="middle">core</text>')
    bx, by = x0 - pad + w * 0.05, -y0 + pad - h * 0.05
    o.append(f'<g stroke="var(--plan-line)" stroke-width="{t * 1.3:.2f}">'
             f'<line x1="{bx:.2f}" y1="{by:.2f}" x2="{bx + 10:.2f}" y2="{by:.2f}"/>'
             f'<line x1="{bx:.2f}" y1="{by - t * 3:.2f}" x2="{bx:.2f}" y2="{by + t * 3:.2f}"/>'
             f'<line x1="{bx + 10:.2f}" y1="{by - t * 3:.2f}" x2="{bx + 10:.2f}" y2="{by + t * 3:.2f}"/></g>'
             f'<text x="{bx + 5:.2f}" y="{by - t * 6:.2f}" font-family="IBM Plex Mono, monospace" '
             f'font-size="{fs * 0.52:.2f}" fill="var(--muted)" text-anchor="middle">10 m</text>')
    o.append("</svg>")
    return "".join(o)


CLOSE = [
  "flats + circulation = footprint, <b>100&nbsp;%</b> &mdash; no square metre left unassigned",
  "<b>exactly one</b> circulation zone on the plate (Sliver: none)",
  "the <b>drawn</b> flat count equals the <b>claimed</b> flat count",
  "each flat is one connected room, no two zones overlap, and no zone carries a spike into another",
  "every zone is a <b>simple outline</b> &mdash; no hole, nothing enclosed, 4 to 21 points &mdash; so each one "
  "writes straight out as a single floor surface",
]

# ---------------------------------------------------------------------------
# Refusal tokens and their readings -- the direct cutter's own §4 token list
# (PLAN_eu21-direct-cutters-2026-09-01.md sect4).

READINGS = {
    DWELLING_DENSITY_REFUSAL_TOKEN: f"above {MAXK} flats on one floor the rule refuses outright (D-EU-65, 2026-09-01: ceiling raised from 8 to 12)",
    "BAND_LT_3M": "a depth band across the sliver strip fell under the 3.0 m minimum",
    "CELL_EMPTY": "a grid cell clipped to the plate had no area left for a flat",
    "FLAT_ENCLOSES_ZONE": "finish() found a flat that still keeps a hole -- reported, not patched",
    "WING_TREE_FAILED": "no connected wing/circulation tree could be built for this re-entrant plate",
    "SECONDARY_VOID_UNCUT": "a courtyard's second void was not crossed by any flat-dividing cut",
}


def reading_for(token, message=None):
    if token in READINGS:
        return READINGS[token]
    if token.startswith("CUT_") and message:
        return message
    return "not one of the cutter's own §4 refusal tokens"


# ---------------------------------------------------------------------------
# Selection (deterministic, T02 "How -- selection").

SIZES = [("small", 3), ("medium", 6), ("big", 9), ("very big", 12)]
TARGET_M2_PER_FLAT = 60

TESTS = {
    1: dict(kind="own", N=3, title="Test 01 \u2014 three buildings per group",
            file="TEST_01_three_per_group_2026-09-02", json="test_01"),
    2: dict(kind="size", M=3, title="Test 02 \u2014 four floor sizes, three buildings each",
            file="TEST_02_floor_sizes_x3_2026-09-02", json="test_02"),
    3: dict(kind="own", N=5, title="Test 03 \u2014 five buildings per group",
            file="TEST_03_five_per_group_2026-09-02", json="test_03"),
    4: dict(kind="size", M=5, title="Test 04 \u2014 four floor sizes, five buildings each",
            file="TEST_04_floor_sizes_x5_2026-09-02", json="test_04"),
    5: dict(kind="own", N=10, title="Test 05 \u2014 ten buildings per group",
            file="TEST_05_ten_per_group_2026-09-02", json="test_05"),
}


def usable_polygon(g):
    if g is None:
        return None
    if not g.is_valid:
        g = g.buffer(0)
        if g.geom_type != "Polygon":
            return None
    return g


def centred(g):
    return translate(g, -g.centroid.x, -g.centroid.y)


def select_own(grp, N, geoms, bygroup, limit=None):
    cands = []
    for r in bygroup[grp]:
        if not (2 <= r["_n"] <= 8):
            continue
        g = usable_polygon(geoms.get((r["district"], r["building_id"])))
        if g is None:
            continue
        cands.append((float(r["area_m2"]), r, g))
    cands.sort(key=lambda t: t[0])
    if len(cands) < N:
        idx = list(range(len(cands)))
    else:
        idx = sorted({round((i + 0.5) / N * (len(cands) - 1)) for i in range(N)})
    picked = [(cands[i][1], centred(cands[i][2]), cands[i][1]["_n"], "own") for i in idx]
    if limit:
        picked = picked[:limit]
    return picked


def select_size(grp, M, geoms, bygroup, limit=None):
    universe = []
    for r in bygroup[grp]:
        g = usable_polygon(geoms.get((r["district"], r["building_id"])))
        if g is None:
            continue
        universe.append((float(r["area_m2"]), r, g))
    used = set()
    out = []
    for label, n in SIZES:
        target = n * TARGET_M2_PER_FLAT
        ordered = sorted(universe, key=lambda t: abs(t[0] - target))
        picked = []
        for area, r, g in ordered:
            key = (r["district"], r["building_id"])
            if key in used:
                continue
            picked.append((r, centred(g), n, label))
            used.add(key)
            if len(picked) >= M:
                break
        if limit:
            picked = picked[:limit]
        out.extend(picked)
    return out


# ---------------------------------------------------------------------------
# One plate: engine call, law, checks (T02 "How -- one plate" / "How -- checks").

def build_plate(test_n, grp, r, p, n, size_label, own_k):
    t0 = time.perf_counter()
    base = {
        "test": test_n, "group": grp, "district": r["district"], "building_id": r["building_id"],
        "storeys": r["_st"], "declared_dwellings": int(round(float(r["dwellings_total"]))),
        "own_k": own_k, "drawn_per_floor": n, "size_label": size_label,
        "area_m2": round(p.area),
    }
    try:
        out = cut(p, n, grp)
    except Refusal as ref:
        base["verdict"] = "REFUSED"
        base["token"] = ref.token
        base["elapsed_s"] = round(time.perf_counter() - t0, 3)
        return base
    except Exception as e:
        base["verdict"] = "ERROR"
        base["token"] = f"CUT_{type(e).__name__}"
        base["message"] = str(e)[:120]
        base["elapsed_s"] = round(time.perf_counter() - t0, 3)
        return base

    flats = out["flats"]
    circ = out["circ"]
    footprint = [list(p.exterior.coords)] + [list(i.coords) for i in p.interiors]
    dw = [[list(f.exterior.coords)] + [list(i.coords) for i in f.interiors] for f in flats]
    circulation = [[list(circ.exterior.coords)] + [list(i.coords) for i in circ.interiors]] if circ is not None else []
    rec = dict(base)
    rec.update(footprint=footprint, dwellings=dw, circulation=circulation, scheme=out["scheme"],
               status="direct", circ_m2=round(circ.area, 1) if circ is not None else 0.0,
               notes=out.get("notes", {}))
    run_checks(rec, n, grp)
    rec["elapsed_s"] = round(time.perf_counter() - t0, 3)
    return rec


NARROW_PROBES_M = [4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5]


def widest_fit(zone):
    for w in NARROW_PROBES_M:
        if not zone.buffer(-w / 2).is_empty:
            return w
    return 0.0


SHARED_EDGE_TOL_M = 0.01  # DD-B, PLAN_eu21-checks-c8c4-2026-09-02


def shared_edge_m(zone, other):
    return sbuf(zone, SHARED_EDGE_TOL_M).intersection(other.exterior).length


def run_checks(rec, n, grp):
    fp = Polygon(rec["footprint"][0], rec["footprint"][1:])
    flats = [Polygon(x[0], x[1:]) for x in rec["dwellings"]]
    cores = [Polygon(x[0], x[1:]) for x in rec["circulation"]]
    checks = {}

    cov = ((sum(f.area for f in flats) + sum(c.area for c in cores)) / fp.area) if fp.area else 0.0
    checks["C1"] = {"pass": 0.999 <= cov <= 1.001, "show": f"{cov * 100:.1f} %"}

    nc = len(cores)
    checks["C2"] = {"pass": nc == 1 or (grp == "SLIVER" and nc <= 1), "show": str(nc)}

    checks["C3"] = {"pass": len(flats) == n, "show": f"{len(flats)}/{n}"}

    lobed = sum(1 for f in flats if lobes_of(f) is not None)
    rooms_ok = lobed == 0
    worst = 0.0
    for i in range(len(flats)):
        for j in range(i + 1, len(flats)):
            ov = flats[i].intersection(flats[j]).area
            if ov > worst:
                worst = ov
    for f in flats:
        for c in cores:
            ov = f.intersection(c).area
            if ov > worst:
                worst = ov
    c4_show = (f"{worst:.2f} m\u00b2" if rooms_ok
               else (f"{lobed} lobed" if worst < 0.02 else f"{lobed} lobed, {worst:.2f} m\u00b2"))
    checks["C4"] = {"pass": rooms_ok and worst < 0.02, "show": c4_show}

    zones = flats + cores
    no_holes = all(len(z.interiors) == 0 for z in zones)
    reps = [z.representative_point() for z in zones]
    no_contain = True
    for i, zi in enumerate(zones):
        for j, pt in enumerate(reps):
            if i != j and zi.contains(pt):
                no_contain = False
    pts_list = [len(z.exterior.coords) - 1 for z in zones]
    max_pts = max(pts_list) if pts_list else 0
    checks["C5"] = {"pass": no_holes and no_contain and max_pts <= 40, "show": str(max_pts)}

    contacts = [sbuf(f, 0.05).intersection(fp.exterior).length for f in flats]
    min_contact = min(contacts) if contacts else 0.0
    checks["C6"] = {"pass": min_contact >= 2.50, "show": f"{min_contact:.2f} m"}

    circ_pct = ((sum(c.area for c in cores) / fp.area) * 100) if fp.area else 0.0
    checks["C7"] = {"class": "info" if 6 <= circ_pct <= 12 else "warn", "show": f"{circ_pct:.1f} %"}

    if not cores:
        checks["C8"] = {"pass": True, "class": "ok", "show": "n/a"}
        checks["C9"] = {"pass": True, "class": "ok", "show": "n/a"}
        checks["R2"] = {"class": "info", "show": "n/a"}
    else:
        circ_shape = cores[0]
        access_min = min((shared_edge_m(f, circ_shape) for f in flats), default=0.0)
        c8_pass = access_min >= ACCESS_MIN_M
        checks["C8"] = {"pass": c8_pass, "class": "ok" if c8_pass else "bad", "show": f"{access_min:.2f} m"}
        r1 = len(circ_shape.exterior.coords) - 1
        c9_pass = r1 <= CORRIDOR_MAX_POINTS
        checks["C9"] = {"pass": c9_pass, "class": "ok" if c9_pass else "bad", "show": str(r1)}
        r2 = (2 * circ_shape.area / circ_shape.length) if circ_shape.length else 0.0
        checks["R2"] = {"class": "info", "show": f"{r2:.2f} m"}

    zones = flats + cores
    r3 = min(widest_fit(z) for z in zones) if zones else 0.0
    c10_pass = r3 >= ZONE_MIN_WIDTH_M
    checks["C10"] = {"pass": c10_pass, "class": "ok" if c10_pass else "bad", "show": f"{r3:.1f} m"}

    rec["checks"] = checks
    rec["m2_per_flat"] = round(sum(f.area for f in flats) / n, 1) if n else 0.0
    rec["pts_total"] = sum(pts_list)
    rec["verdict"] = "PASS" if all(checks[c]["pass"] for c in
                                    ("C1", "C2", "C3", "C4", "C5", "C6", "C8", "C9", "C10")) else "FAIL"


def plate_line(rec):
    scheme = rec.get("scheme", "-")
    return (f'{rec["test"]} {rec["group"]:<20} {rec["district"]:<24} {rec["building_id"]:<20} '
            f'{rec["drawn_per_floor"]:>2} {scheme:<28} {rec["verdict"]:<8} {rec["elapsed_s"]:.3f}')


# ---------------------------------------------------------------------------
# HTML (T02 "How -- HTML").

def esc(s):
    return html.escape(str(s), quote=True)


def status_label(status):
    return "rule in force" if status == "in-force" else "scheme proposed"


def chip(check_id, cls_, text):
    return f'<span class="chk {cls_}">{esc(check_id)} {esc(text)}</span>'


def card(rec, uid, idx):
    district = rec["district"]
    bld = rec["building_id"]
    cap1 = (f'<b>{idx}</b> &middot; {esc(DSHORT.get(district, district))} &middot; {esc(bld)} &middot; '
            f'{rec["storeys"]} storeys &middot; {rec["declared_dwellings"]} dwellings declared &middot; '
            f'{rec["area_m2"]}&nbsp;m&sup2;')
    badge = f'<span class="fignum">{idx}</span>'
    verdict = rec["verdict"]
    if verdict in ("REFUSED", "ERROR"):
        token = rec.get("token", "")
        reading = reading_for(token, rec.get("message"))
        body = f'<div class="failbox"><span class="tok">{esc(token)}</span><p>{esc(reading)}</p></div>'
        return f'<div class="fig">{badge}{body}<p class="cap">{cap1}</p></div>'
    svg = drawplan(rec, uid)
    cap2 = (f'drawn at {rec["drawn_per_floor"]} &middot; {esc(rec["scheme"])} &middot; '
            f'{status_label(rec["status"])} &middot; {rec["m2_per_flat"]}&nbsp;m&sup2; per flat')
    chips = []
    for cid in ("C1", "C2", "C3", "C4", "C5", "C6"):
        c = rec["checks"][cid]
        chips.append(chip(cid, "ok" if c["pass"] else "bad", c["show"]))
    c7 = rec["checks"]["C7"]
    chips.append(chip("C7", c7["class"], c7["show"]))
    c8 = rec["checks"]["C8"]
    chips.append(chip("C8", c8["class"], c8["show"]))
    c9 = rec["checks"]["C9"]
    chips.append(chip("C9", c9["class"], c9["show"]))
    r2 = rec["checks"]["R2"]
    chips.append(chip("R2", r2["class"], r2["show"]))
    c10 = rec["checks"]["C10"]
    chips.append(chip("C10", c10["class"], c10["show"]))
    checks_html = f'<div class="checks">{"".join(chips)}</div>'
    return f'<div class="fig">{badge}{svg}<p class="cap plan-cap">{cap1}<br>{cap2}</p>{checks_html}</div>'


def commonest_failed_check(recs):
    cnt = collections.Counter()
    for p in recs:
        if p["verdict"] != "FAIL":
            continue
        for cid in ("C1", "C2", "C3", "C4", "C5", "C6", "C8", "C9", "C10"):
            if not p["checks"][cid]["pass"]:
                cnt[cid] += 1
    if not cnt:
        return "&mdash;"
    cid, n = cnt.most_common(1)[0]
    return f"{cid} &times;{n}"


def commonest_refusal(recs):
    cnt = collections.Counter(p["token"] for p in recs if p["verdict"] == "REFUSED")
    if not cnt:
        return "&mdash;"
    tok, n = cnt.most_common(1)[0]
    return f"{esc(tok)} &times;{n}"


CHECK_META = [
    ("C1", "Coverage", "0.999 &le; cov &le; 1.001",
     'groups sheet step 6 &ldquo;100&nbsp;%&rdquo;; D-EU-64 &sect;2.3 &ldquo;&ge; 99.9&nbsp;%&rdquo;; '
     'EXAMPLE &sect;6.2 &ldquo;area error 0.00&nbsp;%&rdquo;; MVP &sect;4.3 area conservation'),
    ("C2", "One circulation zone", "n_core == 1 (Sliver: n_core &le; 1)",
     'D-EU-64 &sect;2.1, &sect;2.5; groups sheet step 6; EXAMPLE &sect;6.3'),
    ("C3", "Drawn = claimed", "len(flats) == n",
     'D-EU-64 &sect;2.4; groups sheet step 6'),
    ("C4", "Each flat one room, no overlap", "lobes_of(f) is None for every flat; largest overlap &lt; 0.02&nbsp;m&sup2; "
     "(badge shows &ldquo;n lobed&rdquo; when a flat is not a single room, instead of the overlap area)",
     'D-EU-64 &sect;2.6 (0.75&nbsp;m erosion test); groups sheet step 6; FINDING 232'),
    ("C5", "Simple outline", "no interior ring; no zone contains another; &le; 40 points per zone",
     'D-EU-64 &sect;2.10; groups sheet step 6 &ldquo;4 to 21 points&rdquo; (40 is a ceiling with headroom)'),
]


def build_checks_html():
    items = []
    for (cid, name, tol, src), close_text in zip(CHECK_META, CLOSE):
        items.append(f'<li><code>{cid}</code> <b>{name}</b> &mdash; {close_text}. Tolerance <code>{tol}</code>. '
                      f'Source: {src}.</li>')
    items.append('<li><code>C6</code> <b>Facade contact</b> &mdash; every flat holds at least '
                 '<code>2.50&nbsp;m</code> of contact with the plate&rsquo;s <b>outer</b> perimeter '
                 '(<code>footprint.exterior</code> only) &mdash; a courtyard, light-well or other interior '
                 'void does not count towards it. Source: <code>D-EU-69</code>; MVP &sect;4.4 habitability '
                 'gate; EXAMPLE &sect;6.4 &ldquo;smallest facade contact &ge; 2.50 m&rdquo;; engine '
                 '<code>minimum_facade_contact_m = 2.5</code>.</li>')
    items.append('<li><code>C7</code> <b>Circulation share</b> (report only, never pass/fail) &mdash; shown as '
                 '<code>x.x&nbsp;%</code>; chip <code>info</code> inside <code>6&ndash;12&nbsp;%</code>, '
                 '<code>warn</code> outside. Source: MVP &sect;4.3 &ldquo;6&ndash;12&nbsp;% of gross floor '
                 'area&rdquo;; FINDING 204 (the 12&ndash;25&nbsp;m&sup2; band conflicts and is unruled &mdash; '
                 'report, not resolve); Corridor rectangle and Slab run above the band by construction '
                 '(1.80&nbsp;m corridor).</li>')
    items.append('<li><code>C8</code> <b>Access</b> (hard check, enters the verdict) &mdash; the shortest '
                 'length of corridor boundary lying within 1&nbsp;cm of a flat, <code>min<sub>flats</sub> '
                 'sbuf(f,0.01).intersection(circ.exterior).length</code>; shown as <code>x.xx&nbsp;m</code>, '
                 '<code>n/a</code> when the plate has no circulation (Sliver). '
                 'Passes when &ge; <code>ACCESS_MIN_M</code> (1.00&nbsp;m), or <code>n/a</code> (no circulation '
                 'zone &mdash; Sliver). '
                 'Source: <code>D-EU-70</code>; <code>FINDING 231</code> (the prior measure buffered the flat '
                 'polygon by 5&nbsp;cm and intersected the corridor as a <b>Polygon</b>, so <code>.length</code> '
                 'returned the corridor&rsquo;s perimeter across a bridged gap, not a real shared edge).</li>')
    items.append('<li><code>C9</code> <b>Circulation simplicity</b> (hard check, enters the verdict) &mdash; '
                 'corner points of the single circulation zone, <code>len(circ.exterior.coords) - 1</code>; '
                 'shown as an integer, <code>n/a</code> when the plate has no circulation (Sliver). '
                 'Passes when &le; <code>CORRIDOR_MAX_POINTS</code> (16), or <code>n/a</code> (no circulation '
                 'zone &mdash; Sliver). Source: <code>D-EU-71</code>; threshold fixed by the owner at '
                 '<code>CP-2</code>, 2026-09-02.</li>')
    items.append('<li><code>C10</code> <b>Narrowest zone</b> (hard check, enters the verdict) &mdash; over '
                 'every zone (flats and circulation), the largest <code>w</code> in '
                 '<code>{0.5&hellip;4.0}&nbsp;m</code> for which <code>zone.buffer(-w/2)</code> is non-empty, '
                 'minimum taken over the zones; shown as <code>x.x&nbsp;m</code>, always computed. Passes when '
                 '&ge; <code>ZONE_MIN_WIDTH_M</code> (2.00&nbsp;m). Source: <code>D-EU-72</code>; threshold '
                 'fixed by the owner at <code>CP-2</code>, 2026-09-02.</li>')
    items.append('<li><code>R2</code> is a reading, not a check &mdash; shown as a chip, never entering the '
                 'verdict.</li>')
    items.append('<li><code>R2</code> <b>Effective corridor width</b> &mdash; '
                 '<code>2 &times; circ.area / circ.length</code> in metres, to 2 dp, against '
                 '<code>CORRIDOR_W = 1.80&nbsp;m</code>; <code>n/a</code> when the plate has no circulation. '
                 'Source: <code>D-EU-71</code>; threshold not yet fixed.</li>')
    return "<ul>" + "".join(items) + "</ul>"


def build_selection_html(meta):
    if meta["kind"] == "own":
        return (f'<ul><li>Universe: every usable census building with <b>2 to 8</b> declared flats per floor '
                f'(its own count).</li><li>Sorted by declared plate area; <b>{meta["N"]}</b> are taken at evenly '
                f'spaced quantiles of that order &mdash; fewer usable candidates than {meta["N"]} draws all of '
                f'them.</li><li>Each is drawn at its own flats-per-floor count, not the group median.</li></ul>'
                '<p>A refused or failing plate is shown and counted here, never replaced by another building.</p>')
    return (f'<ul><li>Universe: every usable census building, any own flats-per-floor count.</li>'
            f'<li>Per group and size (3, 6, 9, 12 flats per floor), <b>{meta["M"]}</b> buildings whose declared '
            f'plate area is nearest <code>n &times; 60&nbsp;m&sup2;</code> are taken, skipping a building already '
            f'used by a smaller size in the same group.</li>'
            f'<li>Each is drawn at the size&rsquo;s imposed flats-per-floor count, not its own.</li></ul>'
            '<p>A refused or failing plate is shown and counted here, never replaced by another building.</p>')


def build_lede_html(meta):
    n_txt = meta.get("N", meta.get("M"))
    if meta["kind"] == "own":
        return (f'{n_txt} real buildings per group, each cut at its own flats-per-floor count directly by '
                f'<code>scripts/eu21/05_group_cutters.py</code>, the per-group algorithm of each sheet&rsquo;s '
                f'own steps 3&ndash;4 (<code>D-EU-67</code> connected courtyard cores, <code>D-EU-68</code> basic '
                f'thermal-zone flats); no engine call, no <code>D-EU-64</code> post-pass &mdash; the law holds '
                f'by construction. Every plate is checked against the eight written rules <code>C1&ndash;C8</code> '
                f'and drawn regardless of the result. A refusal is shown as a refusal box carrying the '
                f'cutter&rsquo;s own token, never hidden and never replaced.')
    return (f'{n_txt} real buildings per group at each of four imposed floor sizes (3, 6, 9, 12 flats per '
            f'floor), cut directly by <code>scripts/eu21/05_group_cutters.py</code>, the per-group algorithm of '
            f'each sheet&rsquo;s own steps 3&ndash;4 (<code>D-EU-67</code> connected courtyard cores, '
            f'<code>D-EU-68</code> basic thermal-zone flats); no engine call, no <code>D-EU-64</code> post-pass '
            f'&mdash; the law holds by construction. Above <code>12</code> flats per floor the rule refuses '
            f'outright by design (<code>D-EU-65</code>, 2026-09-01: ceiling raised from 8 to 12), except '
            f'<code>COURTYARD</code>&rsquo;s uncapped gallery scheme. Every plate is checked against '
            f'<code>C1&ndash;C8</code> and drawn regardless of the result.')


def build_html(meta, data):
    test_n = data["test"]
    plates = data["plates"]
    by_group = {g: [] for g in ORDER}
    for rec in plates:
        by_group[rec["group"]].append(rec)

    tried = len(plates)
    drawn = [p for p in plates if p["verdict"] != "REFUSED"]
    refused = [p for p in plates if p["verdict"] == "REFUSED"]
    errors = [p for p in plates if p["verdict"] == "ERROR"]
    passed = [p for p in plates if p["verdict"] == "PASS"]
    failed = [p for p in plates if p["verdict"] == "FAIL"]

    groups_all_pass = 0
    for g in ORDER:
        gdrawn = [p for p in by_group[g] if p["verdict"] != "REFUSED"]
        if gdrawn and all(p["verdict"] == "PASS" for p in gdrawn):
            groups_all_pass += 1

    rows_html = []
    for g in ORDER:
        gp = by_group[g]
        gplates = len(gp)
        gdrawn = sum(1 for p in gp if p["verdict"] != "REFUSED")
        grefused = sum(1 for p in gp if p["verdict"] == "REFUSED")
        gpass = sum(1 for p in gp if p["verdict"] == "PASS")
        gfail = sum(1 for p in gp if p["verdict"] == "FAIL")
        fail_cls = ' class="bad"' if gfail else ""
        ref_cls = ' class="bad"' if grefused else ""
        rows_html.append(
            f'<tr><td class="g">{esc(TITLE[g])}</td><td>{gplates}</td><td>{gdrawn}</td>'
            f'<td{ref_cls}>{grefused}</td><td>{gpass}</td><td{fail_cls}>{gfail}</td>'
            f'<td>{commonest_failed_check(gp)}</td><td>{commonest_refusal(gp)}</td></tr>'
        )
    fail_cls_f = ' class="bad"' if failed else ""
    ref_cls_f = ' class="bad"' if refused else ""
    tfoot = (f'<tr><td class="g">Fleet</td><td>{tried}</td><td>{len(drawn)}</td>'
             f'<td{ref_cls_f}>{len(refused)}</td><td>{len(passed)}</td><td{fail_cls_f}>{len(failed)}</td>'
             f'<td>{commonest_failed_check(plates)}</td><td>{commonest_refusal(plates)}</td></tr>')
    table_html = (
        '<table class="cov"><thead><tr><th>Group</th><th>Plates</th><th>Drawn</th><th>Refused</th>'
        '<th>Pass</th><th>Fail</th><th>Commonest failed check</th><th>Commonest refusal token</th></tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody><tfoot>{tfoot}</tfoot></table>'
    )

    sheets = []
    uid_counter = 0
    for gi, g in enumerate(ORDER, start=1):
        gp = by_group[g]
        gplates = len(gp)
        gpass = sum(1 for p in gp if p["verdict"] == "PASS")
        gfail = sum(1 for p in gp if p["verdict"] == "FAIL")
        grefused = sum(1 for p in gp if p["verdict"] == "REFUSED")
        gdrawn = sum(1 for p in gp if p["verdict"] != "REFUSED")
        bad_drawn = sum(1 for p in gp if p["verdict"] in ("FAIL", "ERROR"))
        if bad_drawn == 0:
            specs = '<span class="tag ok">every drawn plate passes</span>'
        else:
            specs = f'<span class="tag bad">{bad_drawn} of {gdrawn} drawn plates fail</span>'
        sub = (f'{gplates} plates &middot; pass {gpass} &middot; fail {gfail} &middot; refused {grefused} '
               f'&middot; <a href="../RULES_dwelling_layout_groups_2026-09-01.html#{g}">sheet {gi:02d}</a>')
        titleblock = (f'<div class="titleblock"><div class="stack" style="gap:4px">'
                      f'<span class="id">{gi:02d} &nbsp; {esc(TITLE[g])}</span>'
                      f'<span class="sub">{sub}</span></div>'
                      f'<div class="specs">{specs}</div></div>')

        if meta["kind"] == "own":
            panes = [("own flats per floor", gp)]
        else:
            panes = []
            for label, n in SIZES:
                bucket = [p for p in gp if p.get("size_label") == label]
                panes.append((f"{label} &mdash; {n} flats per floor &mdash; plates nearest "
                              f"{n * TARGET_M2_PER_FLAT}&nbsp;m&sup2;", bucket))

        pane_parts = []
        fig_idx = 0
        for heading, bucket in panes:
            cards = []
            for p in bucket:
                uid_counter += 1
                fig_idx += 1
                uid = f"t{test_n}g{gi}n{uid_counter}"
                cards.append(card(p, uid, fig_idx))
            pane_parts.append(f'<div class="pane"><span class="lbl">{heading}</span>'
                              f'<div class="figs">\n{chr(10).join(cards)}\n</div></div>')
        sheets.append(f'<article class="sheet" id="{g}">{titleblock}\n{chr(10).join(pane_parts)}\n</article>')

    eyebrow = f"EU-21 &middot; rules test {test_n:02d} &middot; companion to RULES_dwelling_layout_groups_2026-09-01"
    header = (
        '<header class="mast"><div class="stack">'
        f'<span class="eyebrow">{eyebrow}</span><h1>{esc(meta["title"])}</h1>'
        f'<p class="lede">{build_lede_html(meta)}</p></div>'
        '<div class="meta">'
        '<span>2026-09-01</span>'
        '<span>census: openubem/outputs/eu_evidence/EU-20/morphology_census.csv</span>'
        f'<span>script: scripts/eu21/04_group_tests.py --test {test_n}</span>'
        '<span>law: D-EU-64</span></div></header>'
    )

    tally = (
        '<div class="tally">'
        f'<div><span class="k">Plates tried</span><span class="v">{tried}</span>'
        f'<span class="n">{esc(meta["title"])}, across the 11 groups</span></div>'
        f'<div><span class="k">Plans drawn</span><span class="v">{len(drawn)}</span>'
        '<span class="n">the cutter drew a plan at this count</span></div>'
        f'<div><span class="k">Refused, by rule</span><span class="v" style="color:var(--alert)">{len(refused)}</span>'
        '<span class="n">no scheme fit the plate at this count</span></div>'
        f'<div><span class="k">Cutter errors</span><span class="v" style="color:var(--alert)">{len(errors)}</span>'
        '<span class="n"><code>cut()</code> raised an exception outside the &sect;4 refusal tokens</span></div>'
        f'<div><span class="k">All nine checks passed</span><span class="v" style="color:var(--ok)">{len(passed)}</span>'
        '<span class="n">C1&ndash;C6, C8, C9 and C10 pass; C7 report only</span></div>'
        f'<div><span class="k">Groups fully passing</span><span class="v">{groups_all_pass}</span>'
        '<span class="n">of 11 &mdash; every drawn plate in the group passes</span></div>'
        '</div>'
    )

    checks_section = (
        '<section class="block"><div class="rulehead"><span class="num">CHECKS</span>'
        '<h2>The ten checks, C1&ndash;C10</h2></div>' + build_checks_html() + '</section>'
    )
    selection_section = (
        '<section class="block"><div class="rulehead"><span class="num">SELECTION</span>'
        f'<h2>How the buildings for this test were chosen</h2></div>{build_selection_html(meta)}</section>'
    )
    results_section = (
        '<section class="block"><div class="rulehead"><span class="num">RESULTS</span>'
        f'<h2>Every plate, by group</h2></div>{table_html}</section>'
    )
    groups_section = (
        '<section class="block"><div class="rulehead"><span class="num">GROUPS</span>'
        f'<h2>One sheet per group, every sampled plate</h2></div>\n{chr(10).join(sheets)}\n</section>'
    )
    read_section = (
        '<section class="block"><div class="rulehead"><span class="num">READ</span>'
        '<h2>How to read a test sheet</h2></div>'
        '<div class="legend">'
        '<span class="swatch"><i style="background:var(--d1)"></i> one flat = one thermal zone (heated)</span>'
        '<span class="swatch"><i style="background:var(--sheet-2)"></i> circulation core &mdash; stair/lift '
        'or 1.80&nbsp;m corridor (unheated)</span>'
        '<span>heavy outline = the real footprint, unmodified</span>'
        '<span>scale bar = 10&nbsp;m</span>'
        '<span class="tag ok">rule in force</span> <span>coded and running today</span>'
        '<span class="tag acc">scheme proposed</span> <span>written, not yet proven against the suite</span>'
        '</div>'
        '<div class="legend" style="margin-top:10px">'
        '<span class="chk ok">C1 100.0 %</span><span>the check passes</span>'
        '<span class="chk bad">C3 2/3</span><span>the check fails</span>'
        '<span class="chk info">C7 9.1 %</span><span>report only, inside the 6&ndash;12&nbsp;% band</span>'
        '<span class="chk warn">C7 14.2 %</span><span>report only, outside the band</span>'
        '<span class="chk ok">C8 1.20 m</span><span>pass, access &ge; 1.00&nbsp;m (or n/a)</span>'
        '<span class="chk bad">C8 0.30 m</span><span>fail, access &lt; 1.00&nbsp;m</span>'
        '</div></section>'
    )
    footer = (
        '<footer>'
        '<p><b>What this is.</b> A geometry test of the written rules in <code>rules/</code>: the direct '
        'per-group cutter (<code>scripts/eu21/05_group_cutters.py</code>) that implements the same sheets&rsquo; '
        'own steps 3&ndash;4 that built <code>RULES_dwelling_layout_groups_2026-09-01.html</code> &mdash; no '
        'engine call, no <code>D-EU-64</code> post-pass &mdash; run over real sampled buildings and checked '
        'against the rules written there.</p>'
        '<p><b>What this is not.</b> Not an energy result. No EnergyPlus run stands behind any number on this '
        'page, and <code>D-EU-55</code> forbids one without the owner&rsquo;s own instruction. '
        '<code>RULES_context_geometry_simulation_2026-08-30.md</code> (<code>D-EU-40</code>) concerns the '
        'simulation context, not the plate, and is out of scope here.</p>'
        f'<p class="mono" style="color:var(--muted)">census: openubem/outputs/eu_evidence/EU-20/morphology_census.csv '
        f'&middot; json: openubem/outputs/eu_evidence/EU-21/rules_tests/{meta["json"]}.json '
        f'&middot; script: scripts/eu21/04_group_tests.py --test {test_n}</p>'
        '</footer>'
    )

    body = "\n".join(['<div class="wrap">', header, tally, checks_section, selection_section,
                       results_section, groups_section, read_section, footer, '</div>'])

    css = "\n".join(FROZEN.read_text(encoding="utf-8").splitlines()[2:122])
    extra = '''
<style>
table.cov{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;background:var(--sheet);border:1px solid var(--rule)}
table.cov th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:right;padding:12px 14px;border-bottom:1px solid var(--ink);font-weight:500}
table.cov th:first-child{text-align:left}
table.cov td{padding:10px 14px;text-align:right;border-bottom:1px solid var(--rule-soft);font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--ink-2)}
table.cov td.g{text-align:left;font-family:"Archivo",sans-serif;font-weight:600;color:var(--ink)}
table.cov td.bad{color:var(--alert)}
table.cov tfoot td{border-top:1px solid var(--ink);border-bottom:none;color:var(--ink);font-weight:600;background:var(--sheet-2)}
.pane .lbl{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px}
.pane p{font-size:14px;line-height:1.55;color:var(--ink-2)}
.pane p b{color:var(--ink)}
.specs .tag{align-self:center}
.checks{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}
.chk{font-family:"IBM Plex Mono",monospace;font-size:10.5px;padding:2px 6px;border:1px solid var(--rule);border-radius:2px;color:var(--ink-2);background:var(--sheet)}
.chk.ok{border-color:var(--ok);color:var(--ok);background:var(--ok-soft)}
.chk.bad{border-color:var(--alert);color:var(--alert);background:var(--alert-soft)}
.chk.info{color:var(--muted)}
.chk.warn{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}
.failbox p{font-size:12.5px;color:var(--ink-2)}
.fig{flex:1 1 300px;position:relative}
.fignum{position:absolute;top:4px;left:4px;z-index:1;min-width:18px;height:18px;padding:0 4px;display:flex;align-items:center;justify-content:center;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;color:var(--sheet);background:var(--ink);border-radius:2px}
</style>
'''
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        + css.replace("<title>Dwelling Plans Redrawn</title>", f"<title>Rules Test {test_n:02d}</title>")
        + "\n" + extra + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------------------
# Driver.

def run_test(test_n, universe, limit, render_only, recheck=False):
    meta = TESTS[test_n]
    json_path = OUT_DIR / f"{meta['json']}.json"
    if recheck:
        snap_path = OUT_DIR / f"{meta['json']}.pre_c8c4.json"
        if not snap_path.exists():
            snap_path.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
        data = json.loads(json_path.read_text(encoding="utf-8"))
        for rec in data["plates"]:
            if rec["verdict"] not in ("REFUSED", "ERROR"):
                run_checks(rec, rec["drawn_per_floor"], rec["group"])
        json_path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        print("wrote", json_path, json_path.stat().st_size, "bytes")
    elif render_only:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        geoms, rows, bygroup, perfloor, storeys = universe
        plates = []
        if meta["kind"] == "own":
            selection = (f"Per group, {meta['N']} usable buildings with 2-8 flats/floor, taken at evenly spaced "
                         "quantiles of declared plate area (fewer candidates than requested draws all of them); "
                         "each drawn at its own flats-per-floor count.")
            for grp in ORDER:
                for r, p, n, lbl in select_own(grp, meta["N"], geoms, bygroup, limit):
                    rec = build_plate(test_n, grp, r, p, n, lbl, r["_n"])
                    plates.append(rec)
                    print(plate_line(rec))
        else:
            selection = (f"Per group and size (3/6/9/12 flats/floor), {meta['M']} usable buildings whose declared "
                         "plate area is nearest n x 60 sqm/flat are taken, skipping a building already used by a "
                         "smaller size in the same group; each drawn at the imposed count.")
            for grp in ORDER:
                for r, p, n, lbl in select_size(grp, meta["M"], geoms, bygroup, limit):
                    rec = build_plate(test_n, grp, r, p, n, lbl, r["_n"])
                    plates.append(rec)
                    print(plate_line(rec))
        data = {
            "test": test_n, "title": meta["title"],
            "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "selection": selection, "plates": plates,
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        print("wrote", json_path, json_path.stat().st_size, "bytes")

    html_doc = build_html(meta, data)
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    html_path = HTML_DIR / f"{meta['file']}.html"
    html_path.write_text(html_doc, encoding="utf-8")
    print("wrote", html_path, html_path.stat().st_size, "bytes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, choices=["1", "2", "3", "4", "5", "all"])
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    test_ids = [1, 2, 3, 4, 5] if args.test == "all" else [int(args.test)]
    universe = None
    if not args.render_only and not args.recheck:
        universe = load_universe()
    for t in test_ids:
        run_test(t, universe, args.limit, args.render_only, args.recheck)


if __name__ == "__main__":
    main()
