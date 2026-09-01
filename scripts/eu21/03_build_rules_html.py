import csv, json, html, pathlib

REPO = pathlib.Path(r"C:/Users/o_iseri/Desktop/OpenUBEM")
EU20 = REPO / "openubem/outputs/eu_evidence/EU-20"
FROZEN = REPO / "docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_scheme_2026-08-28.html"
OUT = REPO / "docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html"

css = "\n".join(FROZEN.read_text(encoding="utf-8").splitlines()[2:122])

ORD = ["COURTYARD", "SLIVER", "SQUARE", "RECTANGLE", "SLAB", "TRIANGLE",
       "TRAPEZOID", "L_SHAPE", "U_OR_T_SHAPE", "COMPLEX_MULTI_WING"]
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
DSHORT = {"ES-MAD-BERRUGUETE": "Madrid", "FR-LYO-HAUTCOEURPENTES": "Lyon",
          "GB-LDN-STDUNSTANS": "London", "IT-BOL-GALVANI2": "Bologna"}
TITLE = {"COURTYARD": "Courtyard", "SLIVER": "Sliver", "SQUARE": "Square",
         "RECTANGLE": "Rectangle", "SLAB": "Slab", "TRIANGLE": "Triangle or trapezoid",
         "TRAPEZOID": "Parallelogram", "L_SHAPE": "L shape",
         "U_OR_T_SHAPE": "U or T shape", "COMPLEX_MULTI_WING": "Complex multi-wing"}

rows = list(csv.DictReader(open(EU20 / "morphology_census.csv", encoding="utf-8")))
NUM = ("n_interior_rings", "min_rot_rect_w_m", "rectangularity", "aspect_ratio",
       "n_edges_ge_15pct_perimeter", "reflex_count")
for r in rows:
    for k in NUM:
        r[k] = float(r[k])


def grp(r):
    if r["n_interior_rings"] >= 1:
        return "COURTYARD"
    if r["min_rot_rect_w_m"] < 8.0:
        return "SLIVER"
    if r["rectangularity"] >= 0.90 and r["aspect_ratio"] < 1.5:
        return "SQUARE"
    if r["rectangularity"] >= 0.90 and 1.5 <= r["aspect_ratio"] < 3.0:
        return "RECTANGLE"
    if r["rectangularity"] >= 0.90 and r["aspect_ratio"] >= 3.0:
        return "SLAB"
    if r["n_edges_ge_15pct_perimeter"] <= 3 and r["reflex_count"] == 0:
        return "TRIANGLE"
    if r["reflex_count"] == 0 and r["rectangularity"] < 0.90:
        return "TRAPEZOID"
    if r["reflex_count"] == 1:
        return "L_SHAPE"
    if r["reflex_count"] == 2:
        return "U_OR_T_SHAPE"
    return "COMPLEX_MULTI_WING"


per = {g: {"n": 0, "ruled": 0, "d": {d: 0 for d in DISTRICTS}} for g in ORD}
for r in rows:
    g = grp(r)
    per[g]["n"] += 1
    per[g]["d"][r["district"]] += 1
    if r["idf_state"] == "RULED":
        per[g]["ruled"] += 1

med = {}
for r in csv.DictReader(open(EU20 / "morphology_groups.csv", encoding="utf-8")):
    if r["district"] == "FLEET":
        med[r["group"]] = r

reps = {r["group"]: r for r in json.load(open(EU20 / "representatives.json", encoding="utf-8"))}
cen = {(r["district"], r["building_id"]): r for r in rows}


def svg(g):
    s = (EU20 / "svg" / f"{g}.svg").read_text(encoding="utf-8")
    s = s.replace('width="900" height="900" ', "")
    s = s.replace("<svg ", '<svg class="plan" ', 1)
    return s


PLANS = {r["group"]: r for r in json.load(open(pathlib.Path(__file__).with_name("group_plans.json"), encoding="utf-8"))}

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
         f'aria-label="{TITLE[rec["group"]]} floor plan" preserveAspectRatio="xMidYMid meet">']
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


SPEC = {
 "COURTYARD": dict(
   num="01", status="proposed",
   rule="n_interior_rings &ge; 1",
   rule_txt="The footprint encloses at least one interior void. Tested first, because a ring plate cannot be cut by any grid that assumes a simply-connected plate.",
   plate="A band of built depth wrapped around one or more open voids. Median plate 375&nbsp;m&sup2; with a 23.5&nbsp;m&sup2; void; the band, not the bounding box, is the plate that must be partitioned.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. Here that one zone is a <b>1.80&nbsp;m deck-access gallery running right round the courtyard face</b>, entered from one stair: every flat is reached off the gallery and still keeps its street facade, so the void becomes the access rather than dead space. Whatever the sector cuts leave over against the street wall is folded into the nearest flat, which is why no white gap remains beside <code>F3</code>. The engine today instead drops a small stair core at a sharp outer corner, which is why this group is redrawn under the proposal.",
   zones="<b>k</b> dwelling zones cut along the band by equal area &middot; <b>exactly 1</b> circulation zone, the gallery. The void is not a zone and carries no surfaces. Plate coverage closes at 100&nbsp;%: flats + gallery = footprint.",
   scheme="<code>courtyard_gallery_ring</code> &nbsp;(S5, new &mdash; drawn opposite) &middot; then <code>courtyard_perimeter_band</code> (S1) &middot; today <code>courtyard_wing_unfold</code>, which refuses on the representative plate (<code>INTERIOR_RING_COURTYARD_UNFOLD_FAILED</code>)",
   refuse="Band depth after subtracting the void falls below <code>NARROW_FOOTPRINT_THRESHOLD_M = 8.0</code> &mdash; the plate cannot hold a habitable room and a facade at once."),
 "SLIVER": dict(
   num="02", status="in-force",
   rule="min_rot_rect_w_m &lt; 8.0",
   rule_txt="The minimum rotated width is under the habitable-depth constant. Tested second, because a strip this thin defeats every grid rule downstream regardless of how regular it is.",
   plate="A narrow strip. Median 77&nbsp;m&sup2;, 5.9&nbsp;&times;&nbsp;13.7&nbsp;m, four denoised vertices. The single largest group in the fleet at 637 buildings &mdash; a quarter of everything.",
   circ="<b>None &mdash; the one group where zero is the right number.</b> Direct entry from the street, one private stair inside each dwelling; a shared corridor would consume the whole depth. The plan opposite is still cut by the grid rule in force, which does drop a small core; under <code>row_house_depth_bands</code> that core disappears and its area returns to the flats.",
   zones="<b>k</b> dwelling zones, no circulation zone at all. This is the only group where the absence of a circulation zone is correct rather than a defect. Plate coverage still closes at 100&nbsp;%.",
   scheme="<code>row_house_depth_bands</code> &nbsp;(S2, new) &middot; today <code>narrow_plate_corridor_free</code>",
   refuse="A band narrower than 3.0&nbsp;m across the long axis &mdash; below any national minimum room dimension."),
 "SQUARE": dict(
   num="03", status="in-force",
   rule="rectangularity &ge; 0.90 and aspect_ratio &lt; 1.5",
   rule_txt="Fills its own minimum rotated rectangle to 90&nbsp;% or better, and is close to equilateral. The classic point block.",
   plate="Compact and regular. Median 150&nbsp;m&sup2;, 11.8&nbsp;&times;&nbsp;13.9&nbsp;m, rectangularity 0.964 &mdash; the cleanest plate in the taxonomy.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. One central core sized at <code>CORE_FRACTION_OF_PLATE = 0.06</code> of the plate, dwellings arranged around it and extended out to the outer wall.",
   zones="<b>k</b> dwelling zones on an <b>N&times;M</b> grid &middot; <b>exactly 1</b> circulation zone at the centre. Flats + core = footprint.",
   scheme="<code>point_block_grid</code> &rarr; <code>ruled_grid_NxM</code>",
   refuse="More than <code>RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 8</code> declared dwellings on one storey."),
 "RECTANGLE": dict(
   num="04", status="in-force",
   rule="rectangularity &ge; 0.90 and 1.5 &le; aspect_ratio &lt; 3.0",
   rule_txt="Regular, and elongated but not yet a slab. The threshold at 3.0 is where a corridor starts to beat a core.",
   plate="Median 222&nbsp;m&sup2;, 10.7&nbsp;&times;&nbsp;21.7&nbsp;m. Four denoised vertices in every district &mdash; a genuinely rectangular plate.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. One core placed on the short axis, dwellings left and right of it, each running out to the end wall.",
   zones="<b>k</b> dwelling zones on an <b>N&times;M</b> grid, N along the length &middot; <b>exactly 1</b> circulation zone. Flats + core = footprint.",
   scheme="<code>ruled_grid_NxM</code>",
   refuse="More than 8 declared dwellings on one storey."),
 "SLAB": dict(
   num="05", status="in-force",
   rule="rectangularity &ge; 0.90 and aspect_ratio &ge; 3.0",
   rule_txt="Regular and long. Rarest group in the fleet at 28 buildings, but the one where circulation geometry matters most.",
   plate="Median 367&nbsp;m&sup2;, 10.1&nbsp;&times;&nbsp;37.9&nbsp;m. The six London slabs reach 60&nbsp;m long at 6.2 aspect.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. Here it is a 1.80&nbsp;m corridor running the length &mdash; single-loaded below 12&nbsp;m depth, double-loaded above; the depth decides, not the country. The corridor is the plate&rsquo;s only circulation zone however long the slab is.",
   zones="<b>k</b> dwelling zones in a line along the corridor &middot; <b>exactly 1</b> corridor zone spanning the storey. Flats + corridor = footprint.",
   scheme="<code>i_shape_linear_gallery</code>",
   refuse="Depth below 8.0&nbsp;m &mdash; the building is re-routed to <code>narrow_plate_corridor_free</code> instead."),
 "TRIANGLE": dict(
   num="06", status="proposed",
   rule="n_edges_ge_15pct_perimeter &le; 3 and reflex_count == 0",
   rule_txt="Convex, and carried by three or fewer <em>long</em> edges &mdash; edges shorter than 15&nbsp;% of the perimeter are not counted. A true triangle lands here, but so does a four-sided plate whose fourth side is a short blunt end: a trapezoid. Both are cut the same way, which is why they share a group.",
   plate="Median 216&nbsp;m&sup2;, rectangularity 0.823. Only 8 of the 54 are carried by two long edges; the other 46 have three, and most have four or more vertices &mdash; so the group is mostly tapered trapezoids, not points.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. Core at the incentre, dwellings as wedges radiating to the faces. The tip is merged into its neighbouring flat rather than becoming a zone of its own &mdash; the same absorption rule, applied to the sharpest corner on the plate.",
   zones="<b>k</b> dwelling zones, the tip wedge absorbed by the adjacent one &middot; <b>exactly 1</b> circulation zone. Flats + core = footprint.",
   scheme="<code>regularized_envelope_grid</code> &nbsp;(S4, new)",
   refuse="The largest inscribed rectangle covers less than 60&nbsp;% of the plate &mdash; the remainder cannot be absorbed honestly."),
 "TRAPEZOID": dict(
   num="07", status="proposed",
   rule="reflex_count == 0 and rectangularity &lt; 0.90",
   rule_txt="Convex, four long edges, but skewed off square. In practice these are parallelogram-like plates: opposite sides near-parallel, corners off 90&deg;. The catch-all for convex plates no grid fits squarely.",
   plate="Median 157&nbsp;m&sup2;, 11.9&nbsp;&times;&nbsp;16.4&nbsp;m, rectangularity 0.863, aspect 1.39. All 87 carry exactly four long edges and 65 have exactly four vertices &mdash; skewed quadrilaterals, not wedges. Overwhelmingly a Madrid group: 74 of 87.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. Core on the regularised rectangle; dwellings are cut on that rectangle, clipped back to the true outline, and then <b>grown into the skew slivers the rectangle missed</b>, so the regularisation costs no floor area.",
   zones="<b>k</b> dwelling zones, each clipped to the real footprint and then extended to fill it &middot; <b>exactly 1</b> circulation zone. Flats + core = footprint.",
   scheme="<code>regularized_envelope_grid</code> &nbsp;(S4, new)",
   refuse="Inscribed rectangle below 60&nbsp;% of the plate."),
 "L_SHAPE": dict(
   num="08", status="in-force",
   rule="reflex_count == 1",
   rule_txt="Exactly one reflex vertex &mdash; one elbow, two wings. The first of the three re-entrant groups.",
   plate="Median 203&nbsp;m&sup2;, one reflex vertex, six denoised vertices, hull deficit 0.097.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. <b>One core at the elbow</b>, positioned to serve both wings from a single landing. The strip the regularised rectangle leaves along the short wing is <b>not</b> a second core &mdash; it is handed to the flat it touches, which is why this sheet now shows one hatched zone instead of two.",
   zones="<b>k</b> dwelling zones, allocated per wing in proportion to wing area, each absorbing the leftover against its own outer wall &middot; <b>exactly 1</b> circulation zone at the elbow. Flats + core = footprint.",
   scheme="<code>l_shape_decomposition</code> &middot; falls to <code>wing_spine_decomposition</code> (S3) when one core cannot reach both wings",
   refuse="Either wing narrower than 8.0&nbsp;m after the split."),
 "U_OR_T_SHAPE": dict(
   num="09", status="proposed",
   rule="reflex_count == 2",
   rule_txt="Two reflex vertices &mdash; three wings on a spine. U and T are the same problem: a connecting run with two arms.",
   plate="Median 239&nbsp;m&sup2;, 13.6&nbsp;&times;&nbsp;22.0&nbsp;m, eight denoised vertices, hull deficit 0.117.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. A <b>single</b> spine core on the connecting wing, reaching both arms. Arms are <b>not</b> given cores of their own: the pockets left at the arm ends go into the flats there. An arm too long to be served from the spine is a reason to refuse the plate, not to add a second staircase.",
   zones="<b>k</b> dwelling zones assigned per wing, each absorbing its own arm-end pocket &middot; <b>exactly 1</b> circulation zone, the spine core. Flats + core = footprint.",
   scheme="<code>wing_spine_decomposition</code> &nbsp;(S3, new)",
   refuse="Any wing narrower than 8.0&nbsp;m, or a spine shorter than one dwelling width."),
 "COMPLEX_MULTI_WING": dict(
   num="10", status="proposed",
   rule="reflex_count &ge; 3",
   rule_txt="Three or more reflex vertices. The terminal bucket &mdash; anything the nine rules above did not claim lands here, so it must never fail.",
   plate="Median 306&nbsp;m&sup2;, 16 raw vertices, 12 after denoising, hull deficit 0.203. 425 buildings, second-largest group, and the worst served today at 9.9&nbsp;% ruled.",
   circ="<b>One circulation zone per plate, and one only.</b> It sits inside the plate, away from the outer wall. Any pocket a cut leaves over is <b>grown into by whichever flat is closest</b>, claimed in small steps so a margin that runs past two flats is split at the line equidistant between them rather than handed whole to one on an area tie-break. Once flats are settled, a sliver narrower than about a metre that still borders the core is <b>folded into the core</b> instead of staying a flat's narrow tail &mdash; a corner recess is usable room, not a staircase, but a thin neck against the core is circulation-shaped, not room-shaped. No square metre of the plate is left unassigned. Split into wings by morphological opening &mdash; <code>buffer(&minus;d).buffer(+d)</code> at d&nbsp;=&nbsp;4.0&nbsp;m &mdash; then every wing takes its own group rule recursively. <b>One core for the whole plate</b>, on the largest wing; the edge pockets on the smaller wings are absorbed by the flats beside them, not kept as extra cores.",
   zones="<b>k</b> dwelling zones spread over the wings, each taking the leftover at its own edge &middot; <b>exactly 1</b> circulation zone on the largest wing. Flats + core = footprint.",
   scheme="<code>wing_spine_decomposition</code> &nbsp;(S3, new), applied recursively",
   refuse="A wing that is itself Complex after one opening pass &mdash; recursion is capped at one level, by design, so the rule always terminates."),
}

TOT = sum(per[g]["n"] for g in ORD)
RULED = sum(per[g]["ruled"] for g in ORD)
BAR = 2417


def pct(x):
    return f"{100 * x:.1f}&thinsp;%"


cov = []
for g in ORD:
    n, r = per[g]["n"], per[g]["ruled"]
    need = -(-95 * n // 100)
    cov.append((g, n, n / TOT, r, r / n, need, need - r))

covrows = "".join(
    f'<tr><td class="g">{TITLE[g]}</td><td>{n}</td><td>{pct(sh)}</td><td>{r}</td>'
    f'<td class="{"bad" if rs < 0.25 else ""}">{pct(rs)}</td><td>{need}</td>'
    f'<td class="gap">{gap}</td></tr>'
    for g, n, sh, r, rs, need, gap in cov)

ladder = "".join(
    f'<li><code>{SPEC[g]["rule"]}</code><b>{TITLE[g]}</b><em>{per[g]["n"]}</em></li>'
    for g in ORD)

sheets = []
for g in ORD:
    s, p, m, rep = SPEC[g], per[g], med[g], reps[g]
    dbits = " &middot; ".join(f'{DSHORT[d]} <b>{p["d"][d]}</b>' for d in DISTRICTS)
    pl = PLANS[g]
    plan_svg = drawplan(pl, f"h{g.lower()}")
    n_flats = len(pl["dwellings"])
    circ_share = (100.0 * pl["circ_m2"] / pl["area_m2"]) if pl["area_m2"] else 0.0
    dr = cen[(pl["district"], pl["building_id"])]
    bare_svg = drawplan(pl, f"b{g.lower()}", bare=True)
    prov = ("the rule in force today" if pl["status"] == "in-force"
            else "the proposed rule, not yet in the engine")
    if pl["scheme"] == "courtyard_gallery_ring":
        circ_txt = (f'a <b>{pl["circ_m2"]:.0f}&nbsp;m&sup2;</b> deck-access gallery running round the courtyard '
                    f'({circ_share:.0f}&nbsp;% of the plate, 1.80&nbsp;m wide)')
    elif pl["circ_m2"] > 0.05:
        circ_txt = (f'a <b>{pl["circ_m2"]:.0f}&nbsp;m&sup2;</b> circulation core '
                    f'({circ_share:.0f}&nbsp;% of the plate)')
    else:
        circ_txt = 'no separate core at this count &mdash; each wing is reached from its own stair'
    dropped = int(pl.get("cores_before", 1)) - 1
    lost = float(pl.get("circ_m2_before", pl["circ_m2"])) - float(pl["circ_m2"])
    fold_note = ('' if dropped < 1 else
                 f' <b>One core, not {dropped + 1}.</b> The scheme also left {dropped} '
                 f'{"pocket" if dropped == 1 else "pockets"} of leftover space against the outer wall '
                 f'({lost:.0f}&nbsp;m&sup2;); each is folded into the flat it adjoins, because a corner '
                 f'recess is usable room, not a second staircase.')
    med_note = ('' if pl["median_per_floor"] >= 2 else
                ' The group median is 1 flat per floor; drawn at 2 so the cut is visible.')
    plan_cap = (f'<b>2 &middot; the floor plan the rule produces.</b> {n_flats} flats '
                f'(<code>F1</code>&hellip;<code>F{n_flats}</code>) + {circ_txt}. Cut on the very same plate by '
                f'<code>{pl["scheme"]}</code> &mdash; {prov} &mdash; at <b>{pl["drawn_per_floor"]}</b> flats per '
                f'floor, the group median, repeated on each of ~{pl["median_storeys"]} storeys.{med_note}'
                f'{fold_note} Every square metre of the plate outside the core belongs to a flat: '
                f'the drawing leaves no unassigned space.')
    tag = ('<span class="tag ok">rule in force</span>' if s["status"] == "in-force"
           else '<span class="tag acc">scheme proposed</span>')
    sheets.append(f'''
<article class="sheet" id="{g}">
  <div class="titleblock">
    <div class="stack" style="gap:4px">
      <span class="id">{s["num"]} &nbsp; {TITLE[g]}</span>
      <span class="sub">{p["n"]} buildings &middot; {pct(p["n"] / TOT)} of the fleet &middot; {dbits}</span>
    </div>
    <div class="specs">{tag}<span><b>{p["ruled"]}</b> with a real plan</span><span><b>{pct(p["ruled"] / p["n"])}</b> of the group</span></div>
  </div>
  <div class="plans">
    <div class="pane">
      <div class="panehead"><span class="lbl">Footprint &rarr; floor plan &mdash; one and the same building</span>
        <span class="lbl">{DSHORT[pl["district"]]} &middot; {html.escape(str(pl["building_id"]))}</span></div>
      <div class="figs">
        <div class="fig">{bare_svg}
          <p class="cap"><b>1 &middot; the plate as surveyed.</b> {dr["storeys"]} storeys &middot;
          {dr["dwellings_total"]} dwellings declared &middot; {float(dr["area_m2"]):.0f}&nbsp;m&sup2; &middot;
          aspect {dr["aspect_ratio"]:.2f} &middot; rect. {dr["rectangularity"]:.2f} &middot;
          reflex {dr["reflex_count"]:.0f} &middot; rings {dr["n_interior_rings"]:.0f}</p></div>
        <div class="fig">{plan_svg}
          <p class="cap plan-cap">{plan_cap}</p></div>
      </div>
      <div class="readout">
        <span>median area <b>{float(m["median_area_m2"]):.0f}</b>&nbsp;m&sup2;</span>
        <span>plate <b>{float(m["median_min_rot_rect_w_m"]):.1f}&times;{float(m["median_min_rot_rect_l_m"]):.1f}</b>&nbsp;m</span>
        <span>aspect <b>{float(m["median_aspect_ratio"]):.2f}</b></span>
        <span>rect. <b>{float(m["median_rectangularity"]):.3f}</b></span>
        <span>reflex <b>{float(m["median_reflex_count"]):.0f}</b></span>
        <span>storeys <b>{float(m["median_storeys"]):.0f}</b></span>
        <span>dwellings <b>{float(m["median_dwellings_total"]):.0f}</b></span>
      </div>
    </div>
    <div class="pane">
      <div class="panehead"><span class="lbl">Floor type assigned to this group</span></div>
      <div class="stack" style="gap:13px">
        <div><span class="lbl">Filter</span><p><code>{s["rule"]}</code><br>{s["rule_txt"]}</p></div>
        <div><span class="lbl">Plate</span><p>{s["plate"]}</p></div>
        <div><span class="lbl">Circulation</span><p>{s["circ"]}</p></div>
        <div><span class="lbl">Thermal zones per floor</span><p>{s["zones"]}</p></div>
        <div><span class="lbl">Scheme</span><p>{s["scheme"]}</p></div>
      </div>
    </div>
  </div>
  <p class="note"><b>Refuses when.</b> {s["refuse"]}</p>
</article>''')

body = f'''<div class="wrap">

<header class="mast">
  <div class="stack">
    <span class="eyebrow">EU-20 &middot; morphology census &middot; the group version of RULES_dwelling_layout_scheme_2026-08-28</span>
    <h1>Dwelling Plans Grouped</h1>
    <p class="lede">Every residential building in the four districts was scanned and sorted into ten shape groups
    before any layout was attempted. This sheet states the filter that defines each group, the floor type assigned
    to it &mdash; circulation element and thermal zones &mdash; and how far that group still is from the 95&nbsp;%
    bar. The 2026-08-28 scheme document is unchanged; this one sits beside it.</p>
  </div>
  <div class="meta">
    <span>2026-09-01</span>
    <span>census: openubem/outputs/eu_evidence/EU-20/morphology_census.csv &middot; {TOT} rows</span>
    <span>additive &mdash; nothing in the 2026-08-28 rules was edited</span>
  </div>
</header>

<div class="tally">
  <div><span class="k">Buildings scanned</span><span class="v">{TOT}</span><span class="n">every residential building in Madrid, Lyon, London and Bologna</span></div>
  <div><span class="k">Groups</span><span class="v">10</span><span class="n">ordered first&#8209;match &mdash; every building lands in exactly one</span></div>
  <div><span class="k">With a real floor plan</span><span class="v" style="color:var(--alert)">{RULED}</span><span class="n">{pct(RULED / TOT)} &mdash; the rest simulate as one massing box per floor</span></div>
  <div><span class="k">The bar</span><span class="v" style="color:var(--ok)">{BAR}</span><span class="n">95&nbsp;% floor assignment, before any simulation</span></div>
  <div><span class="k">Gap</span><span class="v">{BAR - RULED}</span><span class="n">buildings that still need a floor type that holds</span></div>
  <div><span class="k">Largest group</span><span class="v">637</span><span class="n">Sliver &mdash; plates under 8&nbsp;m wide, a quarter of the fleet</span></div>
</div>

<section class="block">
  <div class="rulehead"><span class="num">FILTER</span><h2>The ladder &mdash; ten rules, first match wins</h2></div>
  <p class="lede" style="margin-bottom:16px">Order is the rule. A courtyard is tested before width, width before
  regularity, regularity before re&#8209;entrance, and re&#8209;entrance last by count of reflex vertices. Every test
  is dimensionless except the 8.0&nbsp;m plate depth, which is a habitability constant rather than a local
  convention &mdash; that is what lets the ladder carry to countries the database has not reached yet.</p>
  <ol class="ladder">{ladder}</ol>
  <p class="lede" style="margin-top:14px">The last rule has no alternative below it: <b>Complex multi&#8209;wing</b>
  is terminal and takes everything the nine above declined. No building can leave the ladder unclassified.</p>
</section>

<section class="block">
  <div class="rulehead"><span class="num">COVERAGE</span><h2>How far each group is from 95&nbsp;%</h2></div>
  <p class="lede" style="margin-bottom:14px"><b>&ldquo;Real floor plan&rdquo; means the building is cut into
  separate flats and a circulation core, floor by floor, and that partition survives into the energy model.</b>
  A building without one is not skipped &mdash; it is simulated as a single empty box per floor, one thermal zone,
  no interior walls, no core. It still produces a number; that number just cannot describe flats. The goal is that
  <b>95&nbsp;%</b> of the {TOT:,} buildings carry a real plan. Today {RULED:,} do.</p>
  <table class="cov">
    <thead><tr><th>Shape group</th><th>Buildings<br><span class="sub2">in the 4 districts</span></th>
      <th>Share of<br><span class="sub2">all buildings</span></th>
      <th>Real floor plan<br><span class="sub2">today</span></th>
      <th>Of the group<br><span class="sub2">that works</span></th>
      <th>Needed<br><span class="sub2">to reach 95&nbsp;%</span></th>
      <th>Still missing</th></tr></thead>
    <tbody>{covrows}</tbody>
    <tfoot><tr><td class="g">Fleet</td><td>{TOT}</td><td>100.0&thinsp;%</td><td>{RULED}</td><td>{pct(RULED / TOT)}</td><td>{BAR}</td><td class="gap">{BAR - RULED}</td></tr></tfoot>
  </table>
  <div class="callout warn" style="margin-top:22px">
    <p><b>The share with a real plan is nearly flat across the taxonomy</b> &mdash; 9.9&nbsp;% for Complex multi&#8209;wing,
    35.7&nbsp;% for Slab, and every group in between. If shape alone decided the outcome the spread would be far
    wider. Recorded as <code>FINDING&nbsp;222</code>: morphology is the second problem, not the first.</p>
    <p>The first problem is <code>FINDING&nbsp;221</code>. Roughly 939 buildings across the fleet compute a sound
    floor plan and then lose it, because the IDF writer demotes them to one massing box per floor when geomeppy&rsquo;s
    clipper fails on its own intermediate geometry. Those plans exist; they are simply discarded. Recovering them is
    worth more than any new shape rule &mdash; on Lyon it moved the district from 35.4&nbsp;% to 66.0&nbsp;% on its
    own, without a single new scheme.</p>
  </div>
</section>

<section class="block"><div class="rulehead"><span class="num">GROUPS</span><h2>The ten groups, each with its floor type</h2></div>
{"".join(sheets)}
</section>

<section class="block">
  <div class="rulehead"><span class="num">READ</span><h2>How to read a group sheet</h2></div>
  <p class="lede" style="margin-bottom:8px">Every sheet is one real building from that group &mdash; a representative,
  not a sketch, with its district and id in the corner. <b>Drawing&nbsp;1 is the plate as surveyed.</b>
  <b>Drawing&nbsp;2 is the same plate after the group&rsquo;s rule has cut it</b>: each coloured cell is one flat and
  one thermal zone, the hatched cell is the circulation core, and the heavy outline is the original footprint, never
  modified. Both drawings were produced by the layout engine itself, not drawn by hand. Right of them is the rule in
  words: what defines the group, what the plate is, where circulation goes, how many zones a floor ends up with, and
  the named scheme. The line at the foot of each sheet is the refusal condition &mdash; the case the rule declines
  rather than guesses.</p>
  <p class="lede" style="margin-bottom:8px">Each plan is cut at the group&rsquo;s <b>median flats per floor</b> and
  repeats unchanged on every storey. Real buildings in the group carry more or fewer; the rule is the same, only the
  count changes. Above <code>8</code> flats on one floor the rule refuses outright.</p>
  <div class="legend">
    <span class="swatch"><i style="background:var(--d1)"></i> one flat = one thermal zone (heated)</span>
    <span class="swatch"><i style="background:var(--sheet-2)"></i> circulation core &mdash; stair/lift or 1.80&nbsp;m corridor (unheated)</span>
    <span>heavy outline = the real footprint, unmodified</span>
    <span>scale bar = 10&nbsp;m</span>
    <span class="tag ok">rule in force</span> <span>coded and running today</span>
    <span class="tag acc">scheme proposed</span> <span>written, not yet proven against the suite</span>
  </div>
</section>

<footer>
  <p><b>What this is.</b> The first step of the pipeline, written down: scan every building, sort it into a group, and
  only then assign a floor type. It replaces nothing &mdash;
  <code>RULES_dwelling_layout_scheme_2026-08-28.html</code> is frozen and still governs the two schemes it documents.
  The four new schemes named here (S1 courtyard perimeter band, S2 row-house depth bands, S3 wing spine
  decomposition, S4 regularized envelope grid) exist in <code>openubem/geometry/european_residential.py</code> but
  have not yet been proven against the test suite.</p>
  <p><b>What this is not.</b> Not an energy result. No EnergyPlus run stands behind any number on this page, and
  <code>D-EU-55</code> forbids one without the owner&rsquo;s own instruction. The counts are geometry and declared
  dwelling counts only.</p>
  <p class="mono" style="color:var(--muted)">census: openubem/outputs/eu_evidence/EU-20/morphology_census.csv &middot;
  groups: EU-20/morphology_groups.csv &middot; representatives: EU-20/representatives.json &middot;
  classifier: scripts/eu20_morphology_atlas.py:204 &middot; language: figure_4_2_dwelling_layout_schemes.svg</p>
</footer>
</div>'''

extra = '''
<style>
ol.ladder{list-style:none;counter-reset:l;margin:0;padding:0;border:1px solid var(--rule);background:var(--rule);display:flex;flex-direction:column;gap:1px}
ol.ladder li{counter-increment:l;background:var(--sheet);padding:11px 18px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--ink-2)}
ol.ladder li::before{content:counter(l,decimal-leading-zero);color:var(--accent);font-weight:600;min-width:22px}
ol.ladder li code{background:none;padding:0}
ol.ladder li b{font-family:"Archivo",sans-serif;font-size:14px;color:var(--ink);margin-left:auto}
ol.ladder li em{font-style:normal;color:var(--muted);font-variant-numeric:tabular-nums;min-width:46px;text-align:right}
table.cov{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;background:var(--sheet);border:1px solid var(--rule)}
table.cov th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:right;padding:12px 14px;border-bottom:1px solid var(--ink);font-weight:500}
table.cov th:first-child{text-align:left}
table.cov td{padding:10px 14px;text-align:right;border-bottom:1px solid var(--rule-soft);font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--ink-2)}
table.cov td.g{text-align:left;font-family:"Archivo",sans-serif;font-weight:600;color:var(--ink)}
table.cov td.bad{color:var(--alert)}
table.cov td.gap{color:var(--ink);font-weight:600}
table.cov tfoot td{border-top:1px solid var(--ink);border-bottom:none;color:var(--ink);font-weight:600;background:var(--sheet-2)}
.pane .lbl{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px}
.pane p{font-size:14px;line-height:1.55;color:var(--ink-2)}
.pane p b{color:var(--ink)}
.specs .tag{align-self:center}
.wrap>section.block>article.sheet:first-of-type{margin-top:0}
@media (max-width:820px){table.cov th:nth-child(3),table.cov td:nth-child(3){display:none}}
table.cov th .sub2{display:block;font-size:9.5px;letter-spacing:.06em;text-transform:none;color:var(--muted);font-weight:400;opacity:.85;margin-top:2px}
.fig .cap.plan-cap b{color:var(--ink)}
.zonebar{display:flex;gap:3px;margin-top:2px}
.zonebar i{height:9px;flex:1 1 auto;display:block;border:1px solid var(--plan-line)}
</style>
'''

OUT.write_text(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    + css.replace("<title>Dwelling Plans Redrawn</title>", "<title>Dwelling Plans Grouped</title>")
    + "\n" + extra + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n",
    encoding="utf-8")

print("wrote", OUT, OUT.stat().st_size, "bytes")
for g, n, sh, r, rs, need, gap in cov:
    print(f"{g:22s} n={n:5d} ruled={r:4d} {100 * rs:5.1f}%  need={need:5d} gap={gap:5d}")
print("TOTAL", TOT, "ruled", RULED, "bar", BAR, "gap", BAR - RULED)
