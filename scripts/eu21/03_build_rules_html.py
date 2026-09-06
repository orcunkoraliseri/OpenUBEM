import csv, json, html, pathlib, statistics
import importlib.util as ilu
from shapely.affinity import translate as _translate

REPO = pathlib.Path(r"C:/Users/o_iseri/Desktop/OpenUBEM")
EU20 = REPO / "openubem/outputs/eu_evidence/EU-20"
FROZEN = REPO / "docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_scheme_2026-08-28.html"
OUT = REPO / "docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html"

css = "\n".join(FROZEN.read_text(encoding="utf-8").splitlines()[2:122])

ORD = ["COURTYARD", "SLIVER", "SQUARE", "RECTANGLE", "CORRIDOR_RECTANGLE", "SLAB", "TRIANGLE",
       "TRAPEZOID", "L_SHAPE", "U_OR_T_SHAPE", "COMPLEX_MULTI_WING"]
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
DSHORT = {"ES-MAD-BERRUGUETE": "Madrid", "FR-LYO-HAUTCOEURPENTES": "Lyon",
          "GB-LDN-STDUNSTANS": "London", "IT-BOL-GALVANI2": "Bologna"}
TITLE = {"COURTYARD": "Courtyard", "SLIVER": "Sliver", "SQUARE": "Square",
         "RECTANGLE": "Rectangle", "CORRIDOR_RECTANGLE": "Corridor rectangle", "SLAB": "Slab",
         "TRIANGLE": "Triangle or trapezoid",
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
    if r["rectangularity"] >= 0.90 and 1.5 <= r["aspect_ratio"] < 2.0:
        return "RECTANGLE"
    if r["rectangularity"] >= 0.90 and 2.0 <= r["aspect_ratio"] < 3.0:
        return "CORRIDOR_RECTANGLE"
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


# PLANS is built after SPEC (DD-9 needs SPEC[g]["status"]) -- see below.

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


ABSORB = [
  "the wall between two flats is <b>one straight line</b>, wall to wall &mdash; the cut is drawn, not grown, "
  "so no dogleg is left where two claims met. A wall that genuinely bends round a wing is kept as it is",
  "every leftover pocket goes to the <b>flat that holds most of its wall</b>, claimed in 0.20&nbsp;m steps, so "
  "a margin running past two flats splits at the line between them instead of going whole to one",
  "a ribbon <b>along</b> the core, under a metre wide, is folded <b>into the core</b> &mdash; but only if it does "
  "not widen the band: a block across the end of a corridor is narrow too, and folding it draws a wide head",
  "a flat that comes out as two lobes joined by a neck gives the <b>smaller lobe to the neighbour</b> it shares "
  "the most wall with: a thermal zone is one room, not a room plus a tail",
  "the <b>outer wall is surveyed</b> and is never redrawn &mdash; a jagged edge there is the building. Every cut "
  "and offset uses square corners, so no staircase of centimetre steps survives into the drawing",
  "<b>no zone encloses another.</b> A flat that closes round the core, or a gallery that runs the whole way "
  "round a courtyard, is cut open and the piece handed to the neighbour that holds its wall: a zone floor is "
  "one outline, and neither a plan nor EnergyPlus can state a hole in it",
]

CLOSE = [
  "flats + circulation = footprint, <b>100&nbsp;%</b> &mdash; no square metre left unassigned",
  "<b>exactly one</b> circulation zone on the plate (Sliver: none)",
  "the <b>drawn</b> flat count equals the <b>claimed</b> flat count",
  "each flat is one connected room, no two zones overlap, and no zone carries a spike into another",
  "every zone is a <b>simple outline</b> &mdash; no hole, nothing enclosed, 4 to 21 points &mdash; so each one "
  "writes straight out as a single floor surface",
]

SPEC = {
 "COURTYARD": dict(
   num="01", status="in-force",
   rule="n_interior_rings &ge; 1",
   match=["ladder step <b>1 of 11</b> &mdash; tested before everything else",
          "the footprint encloses at least one interior void",
          "a ring plate breaks any grid that assumes a solid plate"],
   plate=["median <b>375&nbsp;m&sup2;</b> of built band around a 23.5&nbsp;m&sup2; void",
          "the band, not the bounding box, is what gets cut"],
   core=["<b>D-EU-67</b>: up to four corner stair cores at the void are joined into <b>one</b> circulation zone by the gallery band, not left as separate cores",
         "the gallery is <b>1.80&nbsp;m</b> wide and <b>open on one side</b>, so the joined zone is one outline and not a ring",
         "a void under <code>COURTYARD_MIN_VOID_SIDE&nbsp;=&nbsp;6.0&nbsp;m</code> is not a courtyard at all (<b>DD-7</b>): the plate is cut by its exterior&rsquo;s own group instead, the void left on a party wall"],
   cut=["<b>k</b> sector cuts radiating from the void, equal area",
        "every flat keeps its street facade"],
   scheme=["<code>courtyard_gallery_ring</code> &mdash; S5, new, drawn opposite",
           "then <code>courtyard_perimeter_band</code> (S1)",
           "today <code>courtyard_wing_unfold</code>, which refuses on this plate "
           "(<code>INTERIOR_RING_COURTYARD_UNFOLD_FAILED</code>)"],
   refuse="Band depth after subtracting the void falls below <code>NARROW_FOOTPRINT_THRESHOLD_M = 8.0</code> &mdash; the plate cannot hold a habitable room and a facade at once."),

 "SLIVER": dict(
   num="02", status="in-force",
   rule="min_rot_rect_w_m &lt; 8.0",
   match=["ladder step <b>2</b> &mdash; before any regularity test",
          "minimum rotated width under the 8.0&nbsp;m habitable-depth constant",
          "a strip this thin defeats every grid rule downstream"],
   plate=["median <b>77&nbsp;m&sup2;</b>, 5.9&nbsp;&times;&nbsp;13.7&nbsp;m, four denoised vertices",
          "largest group in the fleet: <b>637</b> buildings, a quarter of everything"],
   core=["<b>none</b> &mdash; the one group where zero is the right number",
         "direct street entry, a private stair inside each dwelling",
         "a shared corridor would consume the whole depth"],
   cut=["<b>k</b> depth bands across the strip, equal area",
        "the plan opposite still shows the small core the in-force grid drops; under "
        "<code>row_house_depth_bands</code> that area returns to the flats"],
   scheme=["<code>row_house_depth_bands</code> &mdash; S2, new",
           "today <code>narrow_plate_corridor_free</code>"],
   refuse="A band narrower than 3.0&nbsp;m across the long axis &mdash; below any national minimum room dimension."),

 "SQUARE": dict(
   num="03", status="in-force",
   rule="rectangularity &ge; 0.90 and aspect_ratio &lt; 1.5",
   match=["ladder step <b>3</b> &mdash; first of the regularity tests",
          "fills its own minimum rotated rectangle to 0.90 or better",
          "aspect under 1.5: close to equilateral, the classic point block"],
   plate=["median <b>150&nbsp;m&sup2;</b>, 11.8&nbsp;&times;&nbsp;13.9&nbsp;m, rectangularity 0.964",
          "the cleanest plate in the taxonomy"],
   core=["one central core at <code>CORE_FRACTION_OF_PLATE = 0.06</code> of the plate",
         "inside the plate, never against the outer wall"],
   cut=["<b>k</b> flats on an <b>N&times;M</b> grid around the core, each running out to the outer wall",
        "<b>DD-3</b>: at k&nbsp;&ge;&nbsp;5, <code>ceil(k/M)</code> equal-area columns &times; M rows, cut by a straight corridor",
        "<b>DD-6</b>: M&nbsp;&isin;&nbsp;{1,2}, whichever gives the smaller max/min aspect ratio, every flat &ge;&nbsp;3.0&nbsp;m wide",
        "no loading clears the 3.0&nbsp;m floor &rarr; <code>BAND_LT_3M</code>"],
   scheme=["<code>point_block_grid</code> &rarr; <code>ruled_grid_NxM</code>"],
   refuse="More than <code>RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 12</code> declared dwellings on one storey. (D-EU-65, 2026-09-01; was 8 until then)"),

 "RECTANGLE": dict(
   num="04", status="in-force",
   rule="rectangularity &ge; 0.90 and 1.5 &le; aspect_ratio &lt; 2.0",
   match=["ladder step <b>4</b>",
          "regular, and elongated but still short",
          "the 2.0 line is the engine&rsquo;s own <code>LINEAR_GALLERY_ASPECT_THRESHOLD</code>, not this "
          "taxonomy&rsquo;s choice"],
   plate=["median <b>189&nbsp;m&sup2;</b>, 10.8&nbsp;&times;&nbsp;18.6&nbsp;m, aspect 1.71",
          "four denoised vertices in every district"],
   core=["one core on the short axis",
         "still a core, not a corridor: below aspect 2.0 one core reaches every flat"],
   cut=["<b>k</b> flats on an <b>N&times;M</b> grid, N along the length, each running to the end wall",
        "<b>DD-3</b>: at k&nbsp;&ge;&nbsp;5, <code>ceil(k/M)</code> equal-area columns &times; M rows, cut by a straight corridor",
        "<b>DD-6</b>: M&nbsp;&isin;&nbsp;{1,2}, whichever gives the smaller max/min aspect ratio, every flat &ge;&nbsp;3.0&nbsp;m wide",
        "no loading clears the 3.0&nbsp;m floor &rarr; <code>BAND_LT_3M</code>"],
   scheme=["<code>ruled_grid_NxM</code>"],
   refuse="More than 8 declared dwellings on one storey."),

 "CORRIDOR_RECTANGLE": dict(
   num="05", status="in-force",
   rule="rectangularity &ge; 0.90 and 2.0 &le; aspect_ratio &lt; 3.0",
   match=["ladder step <b>5</b> &mdash; group added 2026-09-01",
          "regular, and elongated past the corridor threshold",
          "the engine already routes this plate to a corridor (<code>LENGTH_OVER_WIDTH_GE_2</code>); the "
          "taxonomy had no row for it, so an elongated plate was reported beside a square one"],
   plate=["median <b>245&nbsp;m&sup2;</b>, 10.7&nbsp;&times;&nbsp;25.3&nbsp;m, aspect 2.32",
          "a rectangle carried by one long facade, not two short ones"],
   core=["one <b>1.80&nbsp;m corridor</b> along the long axis, as a slab has",
         "no central core: past aspect 2.0 one core stops reaching every unit"],
   cut=["<b>k</b> flats off the corridor: <b>DD-3</b> equal-area columns, single-loaded (M&nbsp;=&nbsp;1) by design &mdash; a corridor rectangle&rsquo;s core is already the corridor, not a second row",
        "each column still needs &ge;&nbsp;3.0&nbsp;m width (the same <b>DD-6</b> floor), else <code>BAND_LT_3M</code>"],
   scheme=["<code>i_shape_linear_gallery</code>",
           "drawn at 3 flats/floor, not the group median of 2 &mdash; at 2 the scheme is a plain bisection "
           "with no corridor at all"],
   refuse="Depth below 8.0&nbsp;m &mdash; re-routed to <code>narrow_plate_corridor_free</code>, same as Slab."),

 "SLAB": dict(
   num="06", status="in-force",
   rule="rectangularity &ge; 0.90 and aspect_ratio &ge; 3.0",
   match=["ladder step <b>6</b>",
          "regular and long",
          "rarest group at 28 buildings, but the one where circulation geometry matters most"],
   plate=["median <b>367&nbsp;m&sup2;</b>, 10.1&nbsp;&times;&nbsp;37.9&nbsp;m",
          "the six London slabs reach 60&nbsp;m long at aspect 6.2"],
   core=["one <b>1.80&nbsp;m corridor</b> running the whole length",
         "one corridor however long the slab is &mdash; never a second"],
   cut=["<b>k</b> flats in a line off the corridor: <b>DD-3</b> equal-area columns, single-loaded (M&nbsp;=&nbsp;1) &mdash; the whole point of a slab is one row",
        "each column still needs &ge;&nbsp;3.0&nbsp;m width (the same <b>DD-6</b> floor), else <code>BAND_LT_3M</code>"],
   scheme=["<code>i_shape_linear_gallery</code>",
           "drawn at 3 flats/floor for the same reason as Corridor rectangle"],
   refuse="Fewer than 3 declared dwellings per floor &mdash; a corridor serving two flats is not a corridor."),

 "TRIANGLE": dict(
   num="07", status="proposed",
   rule="n_edges_ge_15pct_perimeter &le; 3 and reflex_count == 0",
   match=["ladder step <b>7</b> &mdash; first test that is not about regularity",
          "no reflex corner, and three or fewer <em>long</em> edges (under 15&nbsp;% of the perimeter does not count)",
          "a true triangle lands here, and so does a plate whose fourth side is a short blunt end"],
   plate=["median <b>216&nbsp;m&sup2;</b>, rectangularity 0.823",
          "only 8 of the 54 are carried by two long edges &mdash; mostly tapered trapezoids, not points"],
   core=["<b>DD-2</b>: one core at the plate&rsquo;s <b>centroid</b>, not the incentre &mdash; the convex cutter has no wedge geometry to centre on"],
   cut=["equal-area <b>columns</b> in the plate&rsquo;s own minimum-rotated-rectangle frame, cut by <code>cut_convex()</code>",
        "one straight row line through the centroid splits the columns top/bottom, not wedges radiating from a corner"],
   scheme=["<code>regularized_envelope_grid</code> &mdash; S4, new"],
   refuse="Sharpest corner under 25&deg; and the tip wedge below 6&nbsp;m&sup2; &mdash; the plate is a leftover, not a dwelling."),

 "TRAPEZOID": dict(
   num="08", status="proposed",
   rule="reflex_count == 0 and rectangularity &lt; 0.90",
   match=["ladder step <b>8</b>",
          "no reflex corner, but rectangularity under 0.90",
          "four long edges skewed off square &mdash; the catch-all for convex plates no grid fits squarely"],
   plate=["median <b>157&nbsp;m&sup2;</b>, 11.9&nbsp;&times;&nbsp;16.4&nbsp;m, rect. 0.863, aspect 1.39",
          "all 87 carry four long edges, 65 have exactly four vertices",
          "overwhelmingly a Madrid group: 74 of 87"],
   core=["one core on the regularised rectangle"],
   cut=["<b>k</b> flats cut on the regularised rectangle, then clipped back to the true outline",
        "each flat is then grown into the skew slivers the rectangle missed, so regularising costs no floor area"],
   scheme=["<code>regularized_envelope_grid</code> &mdash; S4, new"],
   refuse="Residual outside the inscribed rectangle above 0.35 of the plate &mdash; the regularisation would be a fiction."),

 "L_SHAPE": dict(
   num="09", status="in-force",
   rule="reflex_count == 1",
   match=["ladder step <b>9</b> &mdash; first of the three re-entrant groups",
          "exactly one reflex vertex: one elbow, two wings"],
   plate=["median <b>203&nbsp;m&sup2;</b>, six denoised vertices, hull deficit 0.097"],
   core=["<b>DD-5</b>: the corridor reaches into each wing from the elbow rather than the wing being refused for its length",
         "each wing&rsquo;s corridor spans only from the <b>first</b> served cut or junction to the <b>last</b>",
         "<b>DD-8</b>: a one-flat leaf wing gets a short <b>1.5&nbsp;m</b> landing stub, not a full corridor",
         "the strip left along the short wing is <b>not</b> a second core &mdash; it goes to the flat it touches"],
   cut=["<b>k</b> flats per wing, in proportion to wing area, each absorbing the leftover against its own outer wall",
        "<b>fallback</b>: a wing split into more than <code>MAX_WING_PIECES&nbsp;=&nbsp;14</code> pieces, or into fewer than two wings, is cut whole by <code>cut_convex()</code> on its own MRR frame instead of being refused"],
   scheme=["<code>l_shape_decomposition</code>",
           "falls to <code>wing_spine_decomposition</code> (S3) when one core cannot reach both wings"],
   refuse="A wing shorter than 6.0&nbsp;m after the elbow is cut away &mdash; it is a bay window, not a wing."),

 "U_OR_T_SHAPE": dict(
   num="10", status="proposed",
   rule="reflex_count == 2",
   match=["ladder step <b>10</b>",
          "exactly two reflex vertices: a connecting run with two arms",
          "U and T are the same problem, so they share a group"],
   plate=["median <b>239&nbsp;m&sup2;</b>, 13.6&nbsp;&times;&nbsp;22.0&nbsp;m, eight denoised vertices, hull deficit 0.117"],
   core=["<b>DD-5</b>: the spine corridor <b>reaches into</b> a long arm rather than the plate being refused for it",
         "the corridor in each arm spans only from the <b>first</b> served cut or junction to the <b>last</b> &mdash; no corridor runs past the last-served flat",
         "<b>DD-8</b>: a one-flat leaf arm gets a short <b>1.5&nbsp;m</b> landing stub, not a full corridor"],
   cut=["<b>k</b> flats assigned per wing",
        "each flat takes the pocket at its own arm end"],
   scheme=["<code>wing_spine_decomposition</code> &mdash; S3, new"],
   refuse="An arm longer than 15&nbsp;m from the spine core &mdash; refuse the plate rather than add a second core."),

 "COMPLEX_MULTI_WING": dict(
   num="11", status="proposed",
   rule="reflex_count &ge; 3",
   match=["ladder step <b>11</b> &mdash; terminal, takes everything the ten above declined",
          "three or more reflex vertices",
          "there is no rule below it, so it must never fail"],
   plate=["median <b>306&nbsp;m&sup2;</b>, 16 raw vertices, 12 after denoising, hull deficit 0.203",
          "425 buildings, second-largest group, and the worst served today at 9.9&nbsp;% with a plan"],
   core=["<b>DD-5</b>: the corridor reaches into each wing from the main spine rather than the wing being refused for its length",
         "each wing&rsquo;s corridor spans only from the <b>first</b> served cut or junction to the <b>last</b>",
         "<b>DD-8</b>: a one-flat leaf wing gets a short <b>1.5&nbsp;m</b> landing stub, not a full corridor",
         "edge pockets on the smaller wings go to the flats beside them, never to extra cores"],
   cut=["split at each reflex vertex, sharpest first, extending one of its two edges into a straight cut, repeated until every wing is convex",
        "<b>fallback</b>: a wing split into more than <code>MAX_WING_PIECES&nbsp;=&nbsp;14</code> pieces, or into fewer than two wings, is cut whole by <code>cut_convex()</code> on its own MRR frame instead of being refused"],
   scheme=["<code>wing_spine_decomposition</code> &mdash; S3, new, applied recursively"],
   refuse="Opening at d&nbsp;=&nbsp;4.0&nbsp;m yields no plate at all &mdash; the footprint is noise, not a building."),
}

USE_CUTTER = True  # DD-9: draw the eleven representative plans with the direct cutter
GROUP_PLANS_PATH = pathlib.Path(__file__).with_name("group_plans.json")
GROUP_PLANS_CUTTER_PATH = pathlib.Path(__file__).with_name("group_plans_cutter.json")


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_cutter_plans():
    """DD-9: cut the eleven representative plans with scripts/eu21/05_group_cutters.py --
    the same per-group algorithm each sheet's steps 3-4 now describe -- instead of the old
    engine + 02_one_core_per_plate.py post-pass. group_plans.json is only read here, never
    written; the result goes to a new group_plans_cutter.json."""
    m01 = _load_module("eu21_m01_for_03", str(pathlib.Path(__file__).with_name("01_cut_group_plans.py")))
    m05 = _load_module("eu21_m05_for_03", str(pathlib.Path(__file__).with_name("05_group_cutters.py")))
    geoms, rows, bygroup, perfloor, storeys = m01.load_universe()
    reps = {x["group"]: x for x in json.load(open(EU20 / "representatives.json", encoding="utf-8"))}
    # the old engine's corridor/gallery scheme activates at dwelling_count >= 3
    # (m01.MIN_DRAW_TO_SHOW_SCHEME); the direct cutter's own corridor band only
    # appears at k >= 5 (DD-3, cut_convex() :306). Drawing these two groups at 3
    # under the new cutter would show the plain box-core branch, not the scheme
    # the sheet's own text now describes -- so the cutter branch draws them at 5.
    CUTTER_MIN_DRAW = {"CORRIDOR_RECTANGLE": 5, "SLAB": 5}
    out = []
    for g in ORD:
        med = int(statistics.median(sorted(perfloor[g])))
        n_draw = max(CUTTER_MIN_DRAW.get(g, 2), med)
        rep_id = str(reps[g]["building_id"])
        members = sorted(bygroup[g], key=lambda r: (r["building_id"] != rep_id, abs(r["_n"] - n_draw)))
        tiers = {}
        for cand in members[:60]:
            geom = geoms.get((cand["district"], cand["building_id"]))
            if geom is None:
                continue
            if not geom.is_valid:
                geom = geom.buffer(0)
                if geom.geom_type != "Polygon":
                    continue
            p = _translate(geom, -geom.centroid.x, -geom.centroid.y)
            try:
                cut_out = m05.cut(p, n_draw, g)
            except m05.Refusal:
                continue
            except Exception:
                continue
            carea = cut_out["circ"].area if cut_out["circ"] is not None else 0.0
            scheme = cut_out["scheme"]
            clean = "+lightwell" not in scheme and scheme != "wing_fallback_convex"
            has_core = carea > 0.05 or g in m01.NO_CORE_BY_DESIGN
            # prefer a plate that draws by the group's own scheme (rank 0) over one that
            # only succeeds via a reroute/fallback (rank 1/2) -- DD-9's picture must match
            # the sheet's own core/cut text, not a different group's rule or the convex
            # fallback that fires when wing decomposition itself cannot.
            rank = 0 if (has_core and clean) else (1 if has_core else 2)
            if rank not in tiers:
                tiers[rank] = (cand, p, cut_out, carea)
                if rank == 0:
                    break
        picked = tiers.get(0) or tiers.get(1) or tiers.get(2)
        if picked is None:
            raise SystemExit(f"USE_CUTTER: no plate draws for group {g} at n={n_draw}")
        cand, p, cut_out, carea = picked
        dw = []
        for f in cut_out["flats"]:
            dw.extend(m01.rings_of(f))
        circ_poly = cut_out["circ"]
        circ = m01.rings_of(circ_poly) if circ_poly is not None and not circ_poly.is_empty else []
        out.append({
            "group": g,
            "district": cand["district"],
            "building_id": cand["building_id"],
            "storeys": cand["_st"],
            "median_per_floor": med,
            "drawn_per_floor": n_draw,
            "median_storeys": int(statistics.median(storeys[g])),
            "area_m2": round(float(cand["area_m2"])),
            "footprint": [list(p.exterior.coords)] + [list(i.coords) for i in p.interiors],
            "dwellings": dw,
            "circulation": circ,
            "scheme": cut_out["scheme"],
            "status": SPEC[g]["status"],
            "circ_m2": round(carea, 1),
        })
    json.dump(out, open(GROUP_PLANS_CUTTER_PATH, "w", encoding="utf-8"), separators=(",", ":"))
    return out


if USE_CUTTER:
    PLANS = {r["group"]: r for r in build_cutter_plans()}
else:
    PLANS = {r["group"]: r for r in json.load(open(GROUP_PLANS_PATH, encoding="utf-8"))}


def flow(s):
    """The right-hand column: the rule as an ordered flow of steps, each step a short list
    of bullets rather than a paragraph. Steps 5 and 6 are the same on every sheet -- they
    are the law, not the group -- and are marked as shared so that reads at a glance."""
    def bullets(items):
        return "".join(f"<li>{b}</li>" for b in items)

    def step(n, act, items, expr=None, shared=False):
        head = f'<p class="expr"><code>{expr}</code></p>' if expr else ""
        cls = " shared" if shared else ""
        return (f'<li class="fstep{cls}"><span class="s">{n}</span>'
                f'<div class="fbody"><span class="act">{act}</span>{head}'
                f'<ul>{bullets(items)}</ul></div></li>')

    return ('<ol class="flow">'
            + step(1, "Match &mdash; does the plate enter this group?", s["match"], expr=s["rule"])
            + step(2, "Read the plate", s["plate"])
            + step(3, "Place the circulation first", s["core"])
            + step(4, "Cut the flats", s["cut"])
            + step(5, "Absorb what is left over", ABSORB, shared=True)
            + step(6, "Close &mdash; accept only if", CLOSE, shared=True)
            + step(7, "Scheme that does it", s["scheme"])
            + "</ol>")


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
      <span class="sub"><a href="#LAW">The global law applies to this sheet as well &mdash; see LAW.</a></span>
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
      <div class="panehead"><span class="lbl">Floor type assigned to this group &mdash; step by step</span>
        <span class="lbl">steps 5 and 6 are the same on every sheet</span></div>
      {flow(s)}
    </div>
  </div>
  <p class="note"><b>Refuses when.</b> {s["refuse"]}</p>
</article>''')

body = f'''<div class="wrap">

<header class="mast">
  <div class="stack">
    <span class="eyebrow">EU-20 &middot; morphology census &middot; the group version of RULES_dwelling_layout_scheme_2026-08-28</span>
    <h1>Dwelling Plans Grouped</h1>
    <p class="lede">Every residential building in the four districts was scanned and sorted into eleven shape groups
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
  <div><span class="k">Groups</span><span class="v">11</span><span class="n">ordered first&#8209;match &mdash; every building lands in exactly one</span></div>
  <div><span class="k">With a real floor plan</span><span class="v" style="color:var(--alert)">{RULED}</span><span class="n">{pct(RULED / TOT)} &mdash; the rest simulate as one massing box per floor</span></div>
  <div><span class="k">The bar</span><span class="v" style="color:var(--ok)">{BAR}</span><span class="n">95&nbsp;% floor assignment, before any simulation</span></div>
  <div><span class="k">Gap</span><span class="v">{BAR - RULED}</span><span class="n">buildings that still need a floor type that holds</span></div>
  <div><span class="k">Largest group</span><span class="v">637</span><span class="n">Sliver &mdash; plates under 8&nbsp;m wide, a quarter of the fleet</span></div>
</div>

<section class="block">
  <div class="rulehead"><span class="num">FILTER</span><h2>The ladder &mdash; eleven rules, first match wins</h2></div>
  <p class="lede" style="margin-bottom:16px">Order is the rule. A courtyard is tested before width, width before
  regularity, regularity before re&#8209;entrance, and re&#8209;entrance last by count of reflex vertices. Every test
  is dimensionless except the 8.0&nbsp;m plate depth, which is a habitability constant rather than a local
  convention &mdash; that is what lets the ladder carry to countries the database has not reached yet.</p>
  <ol class="ladder">{ladder}</ol>
  <p class="lede" style="margin-top:14px">The last rule has no alternative below it: <b>Complex multi&#8209;wing</b>
  is terminal and takes everything the ten above declined. No building can leave the ladder unclassified.</p>
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

<section class="block" id="LAW">
  <div class="rulehead"><span class="num">LAW</span><h2>What is true on every floor plan, in every group</h2></div>
  <p class="lede" style="margin-bottom:16px">Nine clauses hold across all eleven groups, not one at a time. Six
  are coded, checked and capped &mdash; the owner fixed the last two numbers at <code>CP-2</code>, 2026-09-02. The
  last three, <code>D-EU-73</code>, <code>D-EU-75</code> and <code>D-EU-76</code>, are not themselves checked:
  they constrain how the cutter draws, and <code>D-EU-71</code>/<code>C9</code> and
  <code>D-EU-72</code>/<code>C10</code> measure the result.</p>
  <p class="lede" style="margin-bottom:14px"><b>Already law, restated.</b> Exactly one circulation zone per plate
  (<code>SLIVER</code> excepted, zero); flats and circulation cover at least 99.9&nbsp;% of the plate; drawn
  dwellings equal claimed dwellings; every zone is a simple polygon &mdash; no hole, no zone inside another; at most
  40 corner points per zone. <code>D-EU-64</code>.</p>
  <p class="lede" style="margin-bottom:14px"><b><code>D-EU-69</code> &mdash; every flat sees the outer
  fa&ccedil;ade.</b> Owner, 2026-09-02: &ldquo;every flat needs exposure to the sunlight and especially to the outer
  facade exposures, courtyard exposure is not enough.&rdquo; At least 2.50&nbsp;m of the flat&rsquo;s boundary lies
  on the plate&rsquo;s <b>outer</b> perimeter. A courtyard, a light&#8209;well or any interior void does not count.
  Measured by <code>C6</code>, which reads <code>footprint.exterior</code> only.</p>
  <p class="lede" style="margin-bottom:14px">Owner, 2026-09-02: &ldquo;no need to sunlight exposure for
  corridors.&rdquo; The corridor may be entirely interior &mdash; the second clause of <code>D-EU-69</code>.</p>
  <p class="lede" style="margin-bottom:14px"><b><code>D-EU-70</code> &mdash; the corridor reaches every flat.</b>
  Owner, 2026-09-02: &ldquo;corridor needs to touch to every flat zones.&rdquo; The single circulation zone shares
  at least <code>ACCESS_MIN_M</code> (1.00&nbsp;m) of boundary with every dwelling zone; no flat is reached through
  another flat. Measured by <code>C8</code>, promoted to a hard check in T03.</p>
  <div class="callout">
    <p><b><code>D-EU-71</code> &mdash; the corridor stays simple.</b> One band of near&#8209;constant width; no
    spurs, no blobs. Threshold fixed by the owner 2026-09-02 at <code>CP-2</code>: <b>at most 16 corner
    points</b>. Owner: &ldquo;if possible it can be lower than that, because mostly corridors are simple
    shapes.&rdquo; Not 12: the reference plate <code>i_shape_linear_gallery</code> (sheet 05, the corridor the
    owner praised) reads 15 corner points, so a cap of 12 would condemn the very shape the law is written to
    protect. Measured by <code>C9</code>. <code>R2</code>, the effective width
    <code>2&middot;area / perimeter</code> compared against <code>CORRIDOR_W</code> = 1.80&nbsp;m, remains a
    reading only.</p>
  </div>
  <div class="callout" style="margin-top:14px">
    <p><b><code>D-EU-72</code> &mdash; no narrow leftover space.</b> No zone is a sliver too thin to inhabit.
    Threshold fixed by the owner 2026-09-02 at <code>CP-2</code>: <b>no zone narrower than 2.00&nbsp;m</b>,
    measured as the largest width that still fits inside the zone. Measured by <code>C10</code>.</p>
  </div>
  <div class="callout" style="margin-top:14px">
    <p><b><code>D-EU-73</code> &mdash; how a corridor is drawn.</b> Stated by the owner 2026-09-02 from three
    annotated images (<code>Screenshot_30.png</code>, <code>Screenshot_31.png</code>, and a hand&#8209;redrawn
    <code>L_SHAPE</code>/multi&#8209;wing plate). In the first two a red box replaces a stepped, branched corridor
    with a single straight rectangle. In the third the owner redraws the whole plate: three flats, each one entire
    limb of the footprint with outer fa&ccedil;ade on three sides, and a short central red band at the waist where
    the limbs meet. Owner&rsquo;s words: &ldquo;red boundaries shows that we can propose simpler
    corridors&rdquo;; &ldquo;corridor can be central, the flat zones needs to be exposed to the outside facades,
    and simple design&rdquo;; &ldquo;the F2 proposal of yours was too complicated&rdquo;.</p>
    <p><b>(a) One limb, one flat.</b> Each arm, wing or lobe of the footprint becomes one whole flat. A limb is
    never split lengthwise, and a flat never spans two limbs. This is what gives every flat outer fa&ccedil;ade on
    three sides (<code>D-EU-69</code>), and it is decided before any corridor is drawn.</p>
    <p><b>(b) Central band, shortest that works.</b> The circulation zone is one straight rectangle of constant
    width <code>CORRIDOR_W</code> placed at the plate&rsquo;s <b>waist</b> &mdash; the junction where the limbs
    meet, or the mid&#8209;span of a single limb &mdash; bearing chosen so it touches every flat
    (<code>D-EU-70</code>). It is sized to the <b>minimum</b> length that achieves that, never run end to end for
    its own sake. The core sits against it.</p>
    <p><b>(c) No spur.</b> The corridor never branches to reach a flat the band does not already touch. If a flat
    is out of reach, the band moves or changes bearing, or a flat boundary moves; a stub is never added.</p>
    <p><b>(d) No step.</b> The band&rsquo;s two long edges are straight and parallel between its ends. A corner
    appears only where the outer boundary or a flat boundary clips an end.</p>
    <p><b>(e) Chain, not tree.</b> Where one band provably cannot touch every flat &mdash; a courtyard ring, four
    or more limbs &mdash; the circulation is a <b>chain of straight bands joined end to end</b>, each obeying
    (b)&ndash;(d). The joints are the only added corners. Never a T, never a cross, never a comb.</p>
    <p><b>(f) Corner budget.</b> 4 corner points per band, at most 2 more per clipped end, 4 more per additional
    band in the chain. This is what <code>D-EU-71</code>&rsquo;s cap of 16 is rationing: one straight band costs
    4&ndash;6, a two&#8209;band chain 8&ndash;10, a four&#8209;band courtyard ring 14&ndash;16.</p>
    <p class="lede" style="margin:10px 0 0"><b>(e) and (f) are superseded by <code>D-EU-75</code>, owner
    2026-09-02.</b> There is no chain and no ring: one plate, one band. Clauses (a)&ndash;(d) stand unchanged.</p>
    <p><code>D-EU-73</code> is a <b>cutter law, not a check</b>: it says how the drawing is produced, where
    <code>D-EU-71</code> and <code>C9</code> only measure the result. It is written into this document by this
    plan (T07); the cutter itself is not touched. Reference cases: TEST_01 <code>L_SHAPE</code> example 2 (Bologna
    29718), <code>R1</code> = 23 today and 4&ndash;6 under (a)&ndash;(b); and the owner&rsquo;s redrawn plate,
    where three limbs give three flats and one short waist band replaces a corridor that had been threaded through
    the middle of a flat.</p>
  </div>
  <div class="callout" style="margin-top:14px">
    <p><b><code>D-EU-75</code> &mdash; one corridor, one rectangle, any bearing.</b> Stated by the owner
    2026-09-02 from four redrawn sheets &mdash; <code>01&nbsp;Courtyard</code>, <code>09&nbsp;L&nbsp;shape</code>,
    <code>10&nbsp;U&nbsp;or&nbsp;T&nbsp;shape</code>, <code>11&nbsp;Complex&nbsp;multi&#8209;wing</code>:
    &ldquo;if needed update the corridor rule, simple, centered, less point to generate corridors.&rdquo; On every
    one of the four &mdash; a three&#8209;wing plate, an L, a U and a courtyard ring alike &mdash; the owner draws
    the same object: <b>one single straight rectangle</b>, short, near the middle, at whatever bearing suits the
    plate. On <code>11&nbsp;Complex&nbsp;multi&#8209;wing</code> the owner also draws the topology bare: three
    circles F1, F2, F3, and one circle marked <i>corridor</i> touching all three. That is the whole plan.</p>
    <p><b>(a) Exactly one band, in every group.</b> The circulation zone is a single straight rectangle for the
    whole plate, however many limbs the footprint has. <b>This supersedes <code>D-EU-73</code> (e).</b> There is
    no chain, no ring, no second band and no gallery. Where one band cannot touch every flat, the flat boundaries
    move or the plate refuses &mdash; a second band is not the answer.</p>
    <p><b>(b) Free bearing.</b> The band is not bound to the plate&rsquo;s axis, nor to any limb&rsquo;s axis. Its
    bearing is chosen from the footprint&rsquo;s own edge directions, and the bearing that touches every flat with
    the shortest band wins. The owner&rsquo;s rectangles lie diagonally across the L and U plates for exactly this
    reason: the façade they follow is not the bounding box.</p>
    <p><b>(c) Centred and short.</b> Placed where the flats meet, sized to the minimum length that touches them
    all. <code>D-EU-73</code> (b) unchanged &mdash; now with the bearing free instead of pinned.</p>
    <p><b>(d) Corner budget, restated.</b> One band is 4 corner points, at most 2 more per clipped end &mdash;
    <b>6 at most</b>, against <code>D-EU-71</code>&rsquo;s cap of 16. The 8&ndash;16 budget <code>D-EU-73</code>
    (f) allowed for chains and rings is withdrawn with (a).</p>
  </div>
  <div class="callout" style="margin-top:14px">
    <p><b><code>D-EU-76</code> &mdash; no absurd small space.</b> Owner, 2026-09-02, on sheet
    <code>05&nbsp;Corridor&nbsp;rectangle</code> (Madrid <code>way/435927693</code>), ringing the stepped nubs
    along the corridor&rsquo;s edge in red: &ldquo;never create this kind of small absurd spaces, every flat zone
    single zone and if there are these kind of spaces insert to the closest space, corridor.&rdquo;</p>
    <p><b>(a) Every flat is one zone.</b> One single polygon per dwelling. A flat that comes out of the cut in two
    or more pieces is not a flat: the largest piece is the flat, every other piece is a leftover.</p>
    <p><b>(b) Every leftover is absorbed.</b> A leftover is merged into the zone it shares the most boundary with
    &mdash; a flat, or the corridor. Nothing is left standing as a fragment and nothing is dropped: coverage stays
    at <code>D-EU-64</code>&rsquo;s 99.9&nbsp;%.</p>
    <p><b>(c) Thin means leftover only when it is a fragment.</b> A sliver narrower than <code>D-EU-72</code>&rsquo;s
    2.00&nbsp;m is absorbed under (b). A <b>whole flat</b> that thin is a cut that failed, and is reported by
    <code>C10</code> &mdash; never quietly merged away.</p>
  </div>
</section>

<section class="block"><div class="rulehead"><span class="num">GROUPS</span><h2>The eleven groups, each with its floor type</h2></div>
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
ol.flow{list-style:none;margin:0;padding:0;counter-reset:none}
ol.flow>li.fstep{display:flex;gap:11px;position:relative;padding:0 0 13px 0}
ol.flow>li.fstep:last-child{padding-bottom:0}
ol.flow>li.fstep::before{content:"";position:absolute;left:10.5px;top:22px;bottom:0;width:1px;background:var(--rule)}
ol.flow>li.fstep:last-child::before{display:none}
ol.flow .s{flex:0 0 22px;height:22px;border-radius:50%;background:var(--sheet-2);border:1px solid var(--rule);
  color:var(--ink-2);font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;
  display:flex;align-items:center;justify-content:center;position:relative;z-index:1}
ol.flow>li.shared .s{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
ol.flow .fbody{flex:1 1 auto;padding-top:1px}
ol.flow .act{display:block;font-family:"Archivo",sans-serif;font-weight:600;font-size:13px;
  color:var(--ink);letter-spacing:.005em;margin-bottom:3px}
ol.flow>li.shared .act{color:var(--accent)}
ol.flow .expr{margin:0 0 4px 0;font-size:12.5px}
ol.flow .expr code{font-size:11.5px}
ol.flow ul{margin:0;padding:0;list-style:none}
ol.flow ul li{position:relative;padding-left:12px;font-size:13.5px;line-height:1.5;color:var(--ink-2);margin-bottom:2px}
ol.flow ul li::before{content:"";position:absolute;left:2px;top:8.5px;width:4px;height:4px;border-radius:50%;background:var(--rule)}
ol.flow ul li b{color:var(--ink)}
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
