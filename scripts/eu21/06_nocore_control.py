"""EU-21 T10 (D-EU-79 control, DD-7): the no-corridor / no-core control. Re-cuts all
33 TEST_01 plates into k equal-area flats with circulation omitted entirely -- does
the corridor/core earn its complexity? Diagnostic only: never gates DD-1, never
replaces TEST_01, and the corridor stays in the product unless the owner rules
otherwise on the strength of these numbers (plan
implementation/PLAN_eu21-test01-clean-2026-09-02.md sect T10).

Imports frame/to_local/to_world/equal_area_x/_normalize from 05_group_cutters.py
read-only. Never edits 05, never invokes 04_group_tests.py, never writes
test_01.json. No EnergyPlus, no simulation (D-EU-55).
"""
import html
import importlib.util as ilu
import json
import pathlib
import statistics
import sys
import time
from datetime import datetime, timezone

from shapely.geometry import MultiPolygon, Polygon, box

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(ROOT))

IN_JSON = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "rules_tests" / "test_01.json"
OUT_JSON = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "rules_tests" / "test_01_nocore.json"
RULES_DIR = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "rules"
_FROZEN_NAME = "RULES_dwelling_layout_scheme_2026-08-28.html"
FROZEN = RULES_DIR / _FROZEN_NAME if (RULES_DIR / _FROZEN_NAME).exists() else RULES_DIR / "archive" / _FROZEN_NAME
OUT_HTML = RULES_DIR / "tests" / "TEST_01_nocore_2026-09-02.html"

TITLE = {"COURTYARD": "Courtyard", "SLIVER": "Sliver", "SQUARE": "Square",
         "RECTANGLE": "Rectangle", "CORRIDOR_RECTANGLE": "Corridor rectangle", "SLAB": "Slab",
         "TRIANGLE": "Triangle or trapezoid",
         "TRAPEZOID": "Parallelogram", "L_SHAPE": "L shape",
         "U_OR_T_SHAPE": "U or T shape", "COMPLEX_MULTI_WING": "Complex multi-wing"}
FILLS = ["--d1", "--d2", "--d3", "--d4", "--d5", "--d6", "--d7", "--d8"]


def _load_05(retries=3, delay=2.0):
    """T10 gotcha: 05_group_cutters.py is being edited concurrently by another
    executor. A transient SyntaxError during that edit is not this task's bug --
    wait a moment and re-import rather than working around it."""
    last = None
    for attempt in range(retries):
        try:
            spec = ilu.spec_from_file_location(
                "eu21_m05_for_nocore", str(ROOT / "scripts" / "eu21" / "05_group_cutters.py"))
            mod = ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except SyntaxError as e:
            last = e
            if attempt < retries - 1:
                time.sleep(delay)
    raise last


_M05 = _load_05()
frame = _M05.frame
to_local = _M05.to_local
to_world = _M05.to_world
equal_area_x = _M05.equal_area_x
_normalize = _M05._normalize
# Deviation (logged in the plan's T10 progress-log entry): the plan's own How-to-test
# and gotcha both require a C4 "no lobed flat" score, which needs the exact lobe
# test the census itself uses. 05_group_cutters.py already re-exports it verbatim
# from 02_one_core_per_plate.py (05:40, "T05b/D-EU-78: read-only reuse of 02's own
# lobe test ... so the cutter's own C4 pre-check matches the check exactly") -- this
# reuses that same already-exported name, read-only, rather than a second import of
# 02 or a hand-rolled lobe test.
lobes_of = _M05.lobes_of


def esc(s):
    return html.escape(str(s), quote=True)


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


def drawplan(fp_rings, dw_rings, group, uid):
    x0, y0, x1, y1 = _bounds([fp_rings] + dw_rings)
    pad = max(x1 - x0, y1 - y0) * 0.10 + 3
    w, h = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    t = max(w, h) / 300
    fs = max(w, h) / 26
    o = [f'<svg class="plan" viewBox="{x0 - pad:.2f} {-y1 - pad:.2f} {w:.2f} {h:.2f}" role="img" '
         f'aria-label="{esc(TITLE.get(group, group))} no-core control plan" preserveAspectRatio="xMidYMid meet">']
    for i, d in enumerate(dw_rings):
        o.append(f'<path d="{_path(d)}" fill="var({FILLS[i % 8]})" stroke="var(--plan-line)" '
                 f'stroke-width="{t * 0.9:.2f}" stroke-linejoin="round" fill-rule="evenodd"/>')
    o.append(f'<path d="{_path(fp_rings)}" fill="none" stroke="var(--plan-line)" '
             f'stroke-width="{t * 2.1:.2f}" stroke-linejoin="round" fill-rule="evenodd"/>')
    for i, d in enumerate(dw_rings):
        cx, cy = _centroid(d[0])
        o.append(f'<text x="{cx:.2f}" y="{-cy + fs * 0.34:.2f}" font-family="IBM Plex Mono, monospace" '
                 f'font-size="{fs:.2f}" font-weight="500" fill="var(--plan-label)" text-anchor="middle">F{i + 1}</text>')
    bx, by = x0 - pad + w * 0.05, -y0 + pad - h * 0.05
    o.append(f'<g stroke="var(--plan-line)" stroke-width="{t * 1.3:.2f}">'
             f'<line x1="{bx:.2f}" y1="{by:.2f}" x2="{bx + 10:.2f}" y2="{by:.2f}"/>'
             f'<line x1="{bx:.2f}" y1="{by - t * 3:.2f}" x2="{bx:.2f}" y2="{by + t * 3:.2f}"/>'
             f'<line x1="{bx + 10:.2f}" y1="{by - t * 3:.2f}" x2="{bx + 10:.2f}" y2="{by + t * 3:.2f}"/></g>'
             f'<text x="{bx + 5:.2f}" y="{by - t * 6:.2f}" font-family="IBM Plex Mono, monospace" '
             f'font-size="{fs * 0.52:.2f}" fill="var(--muted)" text-anchor="middle">10 m</text>')
    o.append("</svg>")
    return "".join(o)


def _lobe_count(f):
    lb = lobes_of(f)
    return 1 if lb is None else (len(lb) if isinstance(lb, list) else lb)


def cut_nocore(poly, k):
    """No corridor, no core: k equal-area columns in the plate's own frame,
    clipped to the real footprint. Same primitive equal_area_x/frame use as the
    census cutter, minus every circulation step."""
    poly = _normalize(poly)
    theta, cx, cy, L, W = frame(poly)
    P = to_local(poly, theta, cx, cy)
    minx, miny, maxx, maxy = P.bounds
    xs = equal_area_x(P, k)
    bx = [minx - 1] + xs + [maxx + 1]
    cells_local = []
    for i in range(k):
        c = P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1))
        c = _normalize(c)
        cells_local.append(c)
    flats_world = [to_world(c, theta, cx, cy) for c in cells_local]
    return poly, flats_world


def score(poly, flats):
    cov = (sum(f.area for f in flats) / poly.area) if poly.area else 0.0
    c1_pass = 0.999 <= cov <= 1.001
    lobe_counts = [_lobe_count(f) for f in flats]
    c4_pass = all(n <= 1 for n in lobe_counts)
    areas = [f.area for f in flats]
    spread = (min(areas) / max(areas)) if areas and max(areas) > 0 else 0.0
    return cov, c1_pass, lobe_counts, c4_pass, spread


def rings_of(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, MultiPolygon):
        g = max(g.geoms, key=lambda p: p.area)
    return [list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]


def build_rec(src):
    test_n, grp = src["test"], src["group"]
    k = src["drawn_per_floor"]
    base = {
        "test": test_n, "group": grp, "district": src["district"], "building_id": src["building_id"],
        "storeys": src["storeys"], "declared_dwellings": src["declared_dwellings"],
        "own_k": src.get("own_k"), "drawn_per_floor": k, "size_label": src.get("size_label"),
        "area_m2": src.get("area_m2"), "baseline_verdict": src["verdict"],
    }
    checks_na = {"C2": "N/A", "C8": "N/A", "C9": "N/A", "C10": "N/A"}

    if "footprint" not in src:
        base.update(status="SKIPPED_NO_FOOTPRINT",
                     note="TEST_01 recorded this plate as REFUSED before a plan was drawn, so "
                          "test_01.json carries no footprint for it -- the no-core control has no "
                          "independent geometry source per its own test_01.json-only data contract.",
                     checks={"C1": "N/A", "C4": "N/A", **checks_na}, spread=None)
        return base

    fp_rings = src["footprint"]
    poly = Polygon(fp_rings[0], fp_rings[1:])

    try:
        poly_n, flats = cut_nocore(poly, k)
        cov, c1_pass, lobe_counts, c4_pass, spread = score(poly_n, flats)
        base.update(
            status="SCORED",
            footprint=rings_of(poly_n),
            dwellings=[rings_of(f) for f in flats],
            scheme="nocore_equal_area",
            checks={
                "C1": {"pass": c1_pass, "show": f"{cov * 100:.1f} %"},
                "C4": {"pass": c4_pass, "show": ",".join(str(n) for n in lobe_counts)},
                **checks_na,
            },
            spread=round(spread, 4),
            verdict="PASS" if (c1_pass and c4_pass) else "FAIL",
        )
    except Exception as e:
        base.update(status="ERROR", token=f"CUT_{type(e).__name__}", message=str(e)[:200],
                     checks={"C1": "N/A", "C4": "N/A", **checks_na}, spread=None, verdict="ERROR")
    return base


def chip(check_id, cls_, text):
    return f'<span class="chk {cls_}">{esc(check_id)} {esc(text)}</span>'


def card(rec, uid, idx):
    cap1 = (f'<b>{idx}</b> &middot; {esc(rec["district"])} &middot; {esc(rec["building_id"])} &middot; '
            f'{rec["storeys"]} storeys &middot; {rec["declared_dwellings"]} dwellings declared &middot; '
            f'{rec.get("area_m2", "?")}&nbsp;m&sup2; &middot; baseline TEST_01: {esc(rec["baseline_verdict"])}')
    badge = f'<span class="fignum">{idx}</span>'
    if rec["status"] != "SCORED":
        reason = rec.get("note") or rec.get("message") or rec["status"]
        body = f'<div class="failbox"><span class="tok">{esc(rec["status"])}</span><p>{esc(reason)}</p></div>'
        return f'<div class="fig">{badge}{body}<p class="cap">{cap1}</p></div>'
    svg = drawplan(rec["footprint"], rec["dwellings"], rec["group"], uid)
    cap2 = (f'drawn at {rec["drawn_per_floor"]} flats, no corridor/no core &middot; '
            f'area spread (min/max) {rec["spread"]:.2f}')
    checks_html = '<div class="checks">' + "".join([
        chip("C1", "ok" if rec["checks"]["C1"]["pass"] else "bad", rec["checks"]["C1"]["show"]),
        chip("C4", "ok" if rec["checks"]["C4"]["pass"] else "bad", rec["checks"]["C4"]["show"]),
        chip("C2", "info", "N/A"), chip("C8", "info", "N/A"),
        chip("C9", "info", "N/A"), chip("C10", "info", "N/A"),
    ]) + '</div>'
    return f'<div class="fig">{badge}{svg}<p class="cap plan-cap">{cap1}<br>{cap2}</p>{checks_html}</div>'


def build_html(data):
    plates = data["plates"]
    order = []
    for p in plates:
        if p["group"] not in order:
            order.append(p["group"])
    by_group = {g: [] for g in order}
    for rec in plates:
        by_group[rec["group"]].append(rec)

    scored = [p for p in plates if p["status"] == "SCORED"]
    skipped = [p for p in plates if p["status"] == "SKIPPED_NO_FOOTPRINT"]
    errored = [p for p in plates if p["status"] == "ERROR"]
    c1_pass = sum(1 for p in scored if p["checks"]["C1"]["pass"])
    c4_pass = sum(1 for p in scored if p["checks"]["C4"]["pass"])
    spreads = sorted(p["spread"] for p in scored)

    rows_html = []
    for g in order:
        gp = by_group[g]
        gscored = [p for p in gp if p["status"] == "SCORED"]
        gc1 = sum(1 for p in gscored if p["checks"]["C1"]["pass"])
        gc4 = sum(1 for p in gscored if p["checks"]["C4"]["pass"])
        rows_html.append(
            f'<tr><td class="g">{esc(TITLE.get(g, g))}</td><td>{len(gp)}</td><td>{len(gscored)}</td>'
            f'<td>{gc1}/{len(gscored)}</td><td>{gc4}/{len(gscored)}</td></tr>'
        )
    tfoot = (f'<tr><td class="g">Fleet</td><td>{len(plates)}</td><td>{len(scored)}</td>'
             f'<td>{c1_pass}/{len(scored)}</td><td>{c4_pass}/{len(scored)}</td></tr>')
    table_html = (
        '<table class="cov"><thead><tr><th>Group</th><th>Plates</th><th>Scored</th>'
        '<th>C1 pass</th><th>C4 pass</th></tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody><tfoot>{tfoot}</tfoot></table>'
    )

    sheets = []
    uid_counter = 0
    for gi, g in enumerate(order, start=1):
        gp = by_group[g]
        cards = []
        for p in gp:
            uid_counter += 1
            uid = f"nc{gi}n{uid_counter}"
            cards.append(card(p, uid, uid_counter))
        titleblock = (f'<div class="titleblock"><div class="stack" style="gap:4px">'
                      f'<span class="id">{gi:02d} &nbsp; {esc(TITLE.get(g, g))}</span>'
                      f'<span class="sub">{len(gp)} plates</span></div></div>')
        sheets.append(f'<article class="sheet" id="{g}">{titleblock}\n'
                      f'<div class="pane"><div class="figs">\n{chr(10).join(cards)}\n</div></div>\n</article>')

    spread_line = (f"min {spreads[0]:.2f} &middot; median {statistics.median(spreads):.2f} &middot; "
                   f"max {spreads[-1]:.2f}") if spreads else "n/a"

    header = (
        '<header class="mast"><div class="stack">'
        '<span class="eyebrow">EU-21 &middot; control, not acceptance &middot; T10, DD-7</span>'
        '<h1>No-corridor, no-core control</h1>'
        '<p class="lede">Every TEST_01 plate re-cut into k equal-area flats with circulation omitted '
        'entirely. Answers the owner\'s question with a number: does the circulation zone earn its '
        'complexity? Diagnostic only &mdash; never gates DD-1, never replaces TEST_01, and the corridor '
        'stays in the product unless the owner rules otherwise on the strength of these numbers.</p></div>'
        '<div class="meta"><span>2026-09-02</span>'
        '<span>source: openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json</span>'
        '<span>script: scripts/eu21/06_nocore_control.py</span>'
        '<span>law: DD-7</span></div></header>'
    )
    tally = (
        '<div class="tally">'
        f'<div><span class="k">Plates total</span><span class="v">{len(plates)}</span>'
        '<span class="n">every TEST_01 plate</span></div>'
        f'<div><span class="k">Scored</span><span class="v">{len(scored)}</span>'
        '<span class="n">footprint available, no-core cut attempted</span></div>'
        f'<div><span class="k">Skipped (no footprint)</span><span class="v" style="color:var(--alert)">{len(skipped)}</span>'
        '<span class="n">TEST_01 REFUSED plate(s) with no stored geometry</span></div>'
        f'<div><span class="k">Cutter errors</span><span class="v" style="color:var(--alert)">{len(errored)}</span>'
        '<span class="n">exception during the no-core cut</span></div>'
        f'<div><span class="k">C1 coverage passes</span><span class="v" style="color:var(--ok)">{c1_pass}/{len(scored)}</span>'
        '<span class="n">flats + nothing else = footprint</span></div>'
        f'<div><span class="k">C4 no-lobe passes</span><span class="v" style="color:var(--ok)">{c4_pass}/{len(scored)}</span>'
        '<span class="n">every flat is one compact room</span></div>'
        f'<div><span class="k">Equal-area spread</span><span class="v" style="font-size:16px">{spread_line}</span>'
        '<span class="n">min flat area / max flat area, per plate</span></div>'
        '</div>'
    )
    results_section = (
        '<section class="block"><div class="rulehead"><span class="num">RESULTS</span>'
        f'<h2>Every plate, by group</h2></div>{table_html}</section>'
    )
    groups_section = (
        '<section class="block"><div class="rulehead"><span class="num">GROUPS</span>'
        f'<h2>One sheet per group, every TEST_01 plate re-cut without circulation</h2></div>\n'
        f'{chr(10).join(sheets)}\n</section>'
    )
    footer = (
        '<footer><p><b>What this is.</b> A control: <code>scripts/eu21/06_nocore_control.py</code> '
        're-cuts every <code>TEST_01</code> plate into <code>k</code> equal-area flats using only the '
        'plate\'s own frame and <code>equal_area_x</code> (both read, unmodified, from '
        '<code>05_group_cutters.py</code>) &mdash; no corridor, no core. Scores only <code>C1</code> '
        '(coverage) and <code>C4</code> (no lobed flat), the two checks that still mean something without '
        'circulation; <code>C2</code>/<code>C8</code>/<code>C9</code>/<code>C10</code> are circulation '
        'checks and are reported <b>N/A</b>, never PASS.</p>'
        '<p><b>What this is not.</b> Not an acceptance path (<code>DD-7</code>): it never gates '
        '<code>DD-1</code> and never replaces <code>TEST_01</code>. Not an energy result: no EnergyPlus '
        'run stands behind any number here (<code>D-EU-55</code>).</p>'
        f'<p class="mono" style="color:var(--muted)">json: openubem/outputs/eu_evidence/EU-21/rules_tests/'
        f'test_01_nocore.json &middot; script: scripts/eu21/06_nocore_control.py</p></footer>'
    )
    body = "\n".join(['<div class="wrap">', header, tally, results_section, groups_section, footer, '</div>'])

    css = "\n".join(FROZEN.read_text(encoding="utf-8").splitlines()[2:122])
    extra = '''
<style>
table.cov{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;background:var(--sheet);border:1px solid var(--rule)}
table.cov th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:right;padding:12px 14px;border-bottom:1px solid var(--ink);font-weight:500}
table.cov th:first-child{text-align:left}
table.cov td{padding:10px 14px;text-align:right;border-bottom:1px solid var(--rule-soft);font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--ink-2)}
table.cov td.g{text-align:left;font-family:"Archivo",sans-serif;font-weight:600;color:var(--ink)}
table.cov tfoot td{border-top:1px solid var(--ink);border-bottom:none;color:var(--ink);font-weight:600;background:var(--sheet-2)}
.pane .lbl{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px}
.checks{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}
.chk{font-family:"IBM Plex Mono",monospace;font-size:10.5px;padding:2px 6px;border:1px solid var(--rule);border-radius:2px;color:var(--ink-2);background:var(--sheet)}
.chk.ok{border-color:var(--ok);color:var(--ok);background:var(--ok-soft)}
.chk.bad{border-color:var(--alert);color:var(--alert);background:var(--alert-soft)}
.chk.info{color:var(--muted)}
.failbox p{font-size:12.5px;color:var(--ink-2)}
.fig{flex:1 1 300px;position:relative}
.fignum{position:absolute;top:4px;left:4px;z-index:1;min-width:18px;height:18px;padding:0 4px;display:flex;align-items:center;justify-content:center;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;color:var(--sheet);background:var(--ink);border-radius:2px}
</style>
'''
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        + css.replace("<title>Dwelling Plans Redrawn</title>", "<title>No-Corridor Control</title>")
        + "\n" + extra + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )


def main():
    src = json.loads(IN_JSON.read_text(encoding="utf-8"))
    recs = [build_rec(p) for p in src["plates"]]
    data = {
        "test": "nocore", "title": "No-corridor / no-core control (T10, DD-7)",
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json",
        "plates": recs,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print("wrote", OUT_JSON, OUT_JSON.stat().st_size, "bytes")

    html_doc = build_html(data)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    print("wrote", OUT_HTML, OUT_HTML.stat().st_size, "bytes")

    scored = [p for p in recs if p["status"] == "SCORED"]
    skipped = [p for p in recs if p["status"] == "SKIPPED_NO_FOOTPRINT"]
    errored = [p for p in recs if p["status"] == "ERROR"]
    c1 = sum(1 for p in scored if p["checks"]["C1"]["pass"])
    c4 = sum(1 for p in scored if p["checks"]["C4"]["pass"])
    spreads = sorted(p["spread"] for p in scored)
    print(f"total {len(recs)} scored {len(scored)} skipped {len(skipped)} errored {len(errored)}")
    print(f"C1 pass {c1}/{len(scored)}  C4 pass {c4}/{len(scored)}")
    if spreads:
        print(f"spread min {spreads[0]:.4f} median {statistics.median(spreads):.4f} max {spreads[-1]:.4f}")
    for p in recs:
        c1s = p["checks"]["C1"]["pass"] if p["status"] == "SCORED" else p["status"]
        c4s = p["checks"]["C4"]["pass"] if p["status"] == "SCORED" else p["status"]
        print(p["test"], p["building_id"], p["group"], "baseline", p["baseline_verdict"],
              "C1", c1s, "C4", c4s, "spread", p.get("spread"))


if __name__ == "__main__":
    main()
