"""EU-21 no-core dwelling cutter and its seven checks -- the algorithm reviewed and
accepted as `_r5` (D-EU-79 .. D-EU-95), extracted read-only into library code so the
engine can draw the plans the owner accepted instead of the parked corridor regime.

Copied, not re-implemented (D-EU-95): every function and constant below is a verbatim
copy, body-for-body and comment-for-comment, of the reachable closure of `build_flats`
and `run_checks` in `scripts/eu21/07_nocore_tests.py` (sha256
fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717, computed 2026-09-03,
the recorded provenance of the four `*_nocore_2026-09-03_r5.json` files), plus the
handful of helpers that script itself re-exports read-only from
`scripts/eu21/05_group_cutters.py` (`_normalize`, `frame`, `to_local`, `to_world`,
`equal_area_x`) and `scripts/eu21/02_one_core_per_plate.py` (`SQUARE`, `sbuf`, `ok`,
`parts`, `biggest`, `weld`, `NECK_R`, `lobes_of`), and `scripts/eu21/04_group_tests.py`
(`NARROW_PROBES_M`, `widest_fit`, `usable_polygon`, `centred`). `07_nocore_tests.py`
and its siblings `01`-`06`/`08` are never imported (they load each other by absolute
Windows path) and never edited by this module or anything that imports it.

No circulation is carried in (D-EU-79): this module draws flats only, never a
corridor, a core, or an unconditioned circulation zone.

`FINDING 246`: the census never hands `build_flats` a raw footprint --
`08_district_viewer.py:160-181` passes `centred(usable_polygon(g))`, i.e. a
`buffer(0)` repair then a translate of the centroid to the origin, before every
`build_plate` call. `cut_storey_nocore` reproduces that same preprocessing so
`set_precision`'s millimetre grid lands on the same bits it did for `_r5`, whether the
caller hands it a footprint already near the origin (the `_r5` JSONs, a no-op) or a
raw UTM footprint at ~4.5 x 10⁶ m (the live engine, T03).

`_reflex_vertices` is imported lazily (inside the two functions that call it) from
`openubem.geometry.european_residential`, never re-implemented -- that module imports
this one (T03), so a module-level import here would be circular.
"""
import math

from shapely import set_precision
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import split as _shp_split
from shapely.ops import unary_union
from shapely.validation import make_valid

SQUARE = dict(cap_style="flat", join_style="mitre")


def sbuf(g, d):
    """Offset by d with square corners -- shapely's default round join turns every
    morphological open/close into a stack of tiny arc segments, which is what reads
    as an 'extra curve' on a boundary that should be one straight cut."""
    return g.buffer(d, **SQUARE)


def ok(g):
    """A shape welded out of pieces that touch along a line can come back self-intersecting,
    and every later difference() then throws instead of returning a plate. buffer(0) re-nodes
    it -- kept only when it did not quietly drop area on the way."""
    if g.is_valid:
        return g
    f = g.buffer(0)
    return f if not f.is_empty and abs(f.area - g.area) < 1e-6 else g


def parts(g):
    """Polygon sub-pieces of any geometry, including a GeometryCollection -- a chain of
    difference() calls can degenerate into one of those, mixing in stray points/lines."""
    if g.is_empty:
        return []
    g = ok(g)
    if g.geom_type == "Polygon":
        return [g]
    if hasattr(g, "geoms"):
        return [p for p in g.geoms if p.geom_type == "Polygon" and p.area > 1e-9]
    return []


def biggest(g, fb):
    p = parts(g)
    return max(p, key=lambda x: x.area) if p else fb


def weld(g, fb):
    """Like biggest(), but a numerical cut can leave a real second piece touching the
    main one (not a true gap) -- weld those back on instead of dropping the area."""
    p = parts(g)
    if not p:
        return fb
    p.sort(key=lambda x: -x.area)
    out = p[0]
    for extra in p[1:]:
        if out.distance(extra) < 0.05:
            out = ok(unary_union([out, extra]))
    # touching-at-a-point can still leave union() as a MultiPolygon; collapse to the
    # single largest piece rather than pass a shape rings() cannot handle downstream.
    return biggest(out, out)


NECK_R = 0.75
LOBE_MIN_M2 = 1.0


def lobes_of(f, r=NECK_R):
    """Split a flat into its compact lobes, or None if it is already one compact room.

    Erode by r: a shape joined only by a neck narrower than 2r falls apart, a genuinely
    solid room does not. Each surviving piece is then grown back inside the flat by the
    same wavefront used in absorb(), so the split lands on the neck itself rather than on
    an arbitrary straight line."""
    comps = [c for c in parts(sbuf(f, -r)) if c.area > 0.5]
    if len(comps) < 2:
        return None
    grown = list(comps)
    rest = f.difference(unary_union(grown))
    step, guard = 0.30, 0
    while not rest.is_empty and rest.area > 1e-6 and guard < 300:
        guard += 1
        progressed = False
        for i in range(len(grown)):
            claim = sbuf(grown[i], step).intersection(rest)
            if claim.is_empty or claim.area <= 1e-9:
                continue
            grown[i] = unary_union([grown[i], claim]).buffer(0)
            rest = rest.difference(claim)
            progressed = True
        if not progressed:
            step *= 1.5
    grown = [weld(g.intersection(f), g) for g in grown]
    return sorted(grown, key=lambda g: -g.area)


def _normalize(poly):
    g = make_valid(poly) if not poly.is_valid else poly
    g = set_precision(g, 0.001)
    if isinstance(g, MultiPolygon):
        g = max(g.geoms, key=lambda part: part.area)
    return g


def frame(poly):
    """Sheets 03-08 step 4: the plate's own frame -- MRR angle, centre, long/short side."""
    mrr = poly.minimum_rotated_rectangle
    corners = list(mrr.exterior.coords)[:-1]
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in edges]
    i_long = max(range(4), key=lambda idx: lengths[idx])
    (ax, ay), (bx, by) = edges[i_long]
    theta = math.degrees(math.atan2(by - ay, bx - ax))
    cx, cy = mrr.centroid.x, mrr.centroid.y
    L, W = max(lengths), min(lengths)
    return theta, cx, cy, L, W


def to_local(g, theta, cx, cy):
    return rotate(translate(g, -cx, -cy), -theta, origin=(0, 0), use_radians=False)


def to_world(g, theta, cx, cy):
    return translate(rotate(g, theta, origin=(0, 0), use_radians=False), cx, cy)


def equal_area_x(P, N):
    """Sheets 03-08 step 4: N-1 x-cuts splitting P into N equal-area local columns."""
    if N <= 1:
        return []
    minx, miny, maxx, maxy = P.bounds
    total = P.area
    xs = []
    for i in range(1, N):
        target = i / N * total
        lo, hi = minx, maxx
        for _ in range(40):
            if hi - lo < 1e-3:
                break
            mid = (lo + hi) / 2
            a = P.intersection(box(minx - 1, miny - 1, mid, maxy + 1)).area
            if a < target:
                lo = mid
            else:
                hi = mid
        xs.append((lo + hi) / 2)
    return xs


NARROW_PROBES_M = [4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5]


def widest_fit(zone):
    for w in NARROW_PROBES_M:
        if not zone.buffer(-w / 2).is_empty:
            return w
    return 0.0


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


def _pieces(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, MultiPolygon):
        return [p for p in g.geoms if (not p.is_empty) and p.area > 1e-9]
    if isinstance(g, Polygon) and g.area > 1e-9:
        return [g]
    return []


def _dodge_hole_boundaries(P, xs):
    """C5/D-EU-80: a courtyard footprint's own interior ring (the courtyard void,
    not part of the plate) must never fall entirely inside one column's x-range --
    that column then clips to a donut, a flat with a hole. Nudge whichever
    boundary sits closest to the hole's own centre into the hole's x-range
    instead, so the ring is always split between two flats. Only ever repositions
    an existing boundary, so the flat count k is unaffected."""
    xs = list(xs)
    if not xs:
        return xs
    for interior in P.interiors:
        hxs = [c[0] for c in interior.coords]
        hx0, hx1 = min(hxs), max(hxs)
        if any(hx0 < x < hx1 for x in xs):
            continue
        cx = (hx0 + hx1) / 2.0
        j = min(range(len(xs)), key=lambda i: abs(xs[i] - cx))
        xs[j] = cx
    return xs


def _cut_columns(P, k, bx=None):
    minx, miny, maxx, maxy = P.bounds
    if bx is None:
        xs = equal_area_x(P, k)
        xs = _dodge_hole_boundaries(P, xs)
        bx = [minx - 1] + xs + [maxx + 1]
    cols = []
    for i in range(k):
        c = P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1))
        cols.append(c)
    return cols


def _seed_flats(cols):
    seeds = []
    for c in cols:
        pieces = _pieces(c)
        seeds.append(max(pieces, key=lambda g: g.area) if pieces else Polygon())
    return seeds


def _equal_area_y(P, N):
    """D-EU-81/T04, attack-order item 2(iii): the same equal-area sweep as
    `equal_area_x` (05_group_cutters.py:106), along the perpendicular axis, so a
    grid cutter can band a plate before columning each band."""
    if N <= 1:
        return []
    minx, miny, maxx, maxy = P.bounds
    total = P.area
    ys = []
    for i in range(1, N):
        target = i / N * total
        lo, hi = miny, maxy
        for _ in range(40):
            if hi - lo < 1e-3:
                break
            mid = (lo + hi) / 2
            a = P.intersection(box(minx - 1, miny - 1, maxx + 1, mid)).area
            if a < target:
                lo = mid
            else:
                hi = mid
        ys.append((lo + hi) / 2)
    return ys


def _grid_seeds(P, k, rows=2):
    """D-EU-81/T04 attack-order item 2(iii): a `rows`-band grid instead of a
    single row of k columns -- each band gets roughly k/rows flats, so a column
    is roughly `rows` times wider than a single-row cut of the same k. Bands are
    split by equal-area y-cuts; each band is then columned by the same
    equal-area x-cuts and hole-dodge used everywhere else in this cutter. Returns
    None if there are fewer flats than rows (nothing to gain from banding)."""
    if rows < 2 or k < rows:
        return None
    minx, miny, maxx, maxy = P.bounds
    ys = _equal_area_y(P, rows)
    by = [miny - 1] + ys + [maxy + 1]
    band_polys = []
    band_areas = []
    for i in range(rows):
        band = P.intersection(box(minx - 1, by[i], maxx + 1, by[i + 1]))
        pieces = _pieces(band)
        band_poly = max(pieces, key=lambda g: g.area) if pieces else None
        band_polys.append(band_poly)
        band_areas.append(band_poly.area if band_poly is not None else 0.0)
    total_area = sum(band_areas) or 1.0
    counts = [max(1, round(k * a / total_area)) for a in band_areas]
    diff = k - sum(counts)
    order = sorted(range(rows), key=lambda i: -band_areas[i])
    guard = 0
    while diff != 0 and guard < 10 * rows:
        i = order[guard % rows]
        if diff > 0:
            counts[i] += 1
            diff -= 1
        elif counts[i] > 1:
            counts[i] -= 1
            diff += 1
        guard += 1
    seeds = []
    for i in range(rows):
        band_poly = band_polys[i]
        n_i = counts[i]
        if band_poly is None or n_i <= 0:
            continue
        xs = equal_area_x(band_poly, n_i)
        xs = _dodge_hole_boundaries(band_poly, xs)
        bxs = [minx - 1] + xs + [maxx + 1]
        for j in range(n_i):
            c = band_poly.intersection(box(bxs[j], by[i] - 1, bxs[j + 1], by[i + 1] + 1))
            seeds.append(c)
    return _seed_flats(seeds)


def _grid_seeds_snapped(P, k, rows, reflex_xs_local):
    """eu21-colour-repair/T03 how: the same rows-band grid as `_grid_seeds`
    (never edited above -- this is a sibling, not a modification), but each
    band's own column boundaries are snapped onto a reflex vertex within
    `REFLEX_SNAP_TOLERANCE_M` first (`_snap_boundaries`). Returns `None` when
    nothing snapped in any band (nothing to add) or `_grid_seeds`'s own guard
    (`rows < 2 or k < rows`) applies -- snapping is one additional candidate,
    never a replacement for the unsnapped grid."""
    if rows < 2 or k < rows or not reflex_xs_local:
        return None
    minx, miny, maxx, maxy = P.bounds
    ys = _equal_area_y(P, rows)
    by = [miny - 1] + ys + [maxy + 1]
    band_polys, band_areas = [], []
    for i in range(rows):
        band = P.intersection(box(minx - 1, by[i], maxx + 1, by[i + 1]))
        pieces = _pieces(band)
        band_poly = max(pieces, key=lambda g: g.area) if pieces else None
        band_polys.append(band_poly)
        band_areas.append(band_poly.area if band_poly is not None else 0.0)
    total_area = sum(band_areas) or 1.0
    counts = [max(1, round(k * a / total_area)) for a in band_areas]
    diff = k - sum(counts)
    order = sorted(range(rows), key=lambda i: -band_areas[i])
    guard = 0
    while diff != 0 and guard < 10 * rows:
        i = order[guard % rows]
        if diff > 0:
            counts[i] += 1
            diff -= 1
        elif counts[i] > 1:
            counts[i] -= 1
            diff += 1
        guard += 1
    seeds = []
    snapped_any = False
    for i in range(rows):
        band_poly = band_polys[i]
        n_i = counts[i]
        if band_poly is None or n_i <= 0:
            continue
        xs = equal_area_x(band_poly, n_i)
        xs = _dodge_hole_boundaries(band_poly, xs)
        bxs = [minx - 1] + xs + [maxx + 1]
        snapped_xs = _snap_boundaries(xs, reflex_xs_local, bxs[0], bxs[-1]) if xs else None
        if snapped_xs is not None:
            snapped_any = True
            bxs = [minx - 1] + snapped_xs + [maxx + 1]
        for j in range(n_i):
            c = band_poly.intersection(box(bxs[j], by[i] - 1, bxs[j + 1], by[i + 1] + 1))
            seeds.append(c)
    if not snapped_any:
        return None
    return _seed_flats(seeds)


def _clean_merge(a, b):
    """D-EU-80: a merge is only accepted if it comes back as one clean Polygon.
    A candidate ranked by contact probe (_best_recipients) can still turn out not
    to truly touch `a` (a hairline gap, or contact along a single point) -- in
    that case shapely's union comes back a MultiPolygon, and silently keeping
    only its largest part is exactly how a piece gets dropped without being
    reported. Reject that merge instead so the caller tries the next candidate;
    the piece is only ever counted placed when nothing of it was lost."""
    cand = b if (a is None or a.is_empty) else unary_union([a, b])
    return cand if isinstance(cand, Polygon) else None


def _best_recipients(piece, flats):
    """D-EU-80/D-EU-77: rank flats by shared boundary with `piece`
    (piece.buffer(0.01, cap_style=3, join_style=2).intersection(flat.exterior).length),
    ties -> the smaller flat, so the donation also flattens the spread."""
    probe = piece.buffer(0.01, cap_style=3, join_style=2)
    scored = []
    for i, f in enumerate(flats):
        if f.is_empty:
            continue
        shared = probe.intersection(f.exterior).length
        if shared > 1e-9:
            scored.append((shared, f.area, i))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [i for _, _, i in scored]


def _bounded_split_piece(piece, target_area, toward_geom):
    """D-EU-107 (`FINDING 244` repair 2, plan `eu-plan-homogeneity-2026-09-07`
    T02b): split `piece` along the axis from its own centroid toward
    `toward_geom`'s centroid (the receiving flat), by bisection on the
    perpendicular boundary in that local frame, so the near side (the side
    that borders the receiving flat) comes out close to `target_area`. Returns
    `(near_world, far_world)` -- `near_world` is what gets merged into the
    receiving flat, `far_world` is fed back into the donation loop as a fresh
    leftover, so a leftover too big to donate whole is bounded rather than
    dumped intact into one flat. Returns `None` on any degenerate geometry
    (near-zero span, a split that does not resolve to two clean pieces) --
    the caller then falls back to today's whole-piece donation, exactly as
    the plan's fallback clause requires."""
    if piece.is_empty or piece.area <= 1e-9:
        return None
    c_piece = piece.centroid
    c_to = toward_geom.centroid
    dx, dy = c_to.x - c_piece.x, c_to.y - c_piece.y
    if math.hypot(dx, dy) < 1e-6:
        return None
    theta = math.degrees(math.atan2(dy, dx))
    p_local = to_local(piece, theta, c_piece.x, c_piece.y)
    minx, miny, maxx, maxy = p_local.bounds
    if maxx - minx < 1e-6:
        return None
    target_area = max(0.0, min(target_area, piece.area))
    lo, hi = minx, maxx
    for _ in range(24):
        mid = (lo + hi) / 2.0
        near = p_local.intersection(box(mid, miny - 1, maxx + 1, maxy + 1))
        near_area = sum(g.area for g in _pieces(near))
        if near_area > target_area:
            lo = mid
        else:
            hi = mid
    bx = (lo + hi) / 2.0
    near_local = p_local.intersection(box(bx, miny - 1, maxx + 1, maxy + 1))
    far_local = p_local.intersection(box(minx - 1, miny - 1, bx, maxy + 1))
    near_pieces, far_pieces = _pieces(near_local), _pieces(far_local)
    if not near_pieces or not far_pieces:
        return None
    near_world = to_world(unary_union(near_pieces), theta, c_piece.x, c_piece.y)
    far_world = to_world(unary_union(far_pieces), theta, c_piece.x, c_piece.y)
    if not isinstance(near_world, Polygon) or not isinstance(far_world, Polygon):
        return None
    if near_world.is_empty or far_world.is_empty:
        return None
    return near_world, far_world


def _clears_donation_gates(merged, P, other_live):
    """D-EU-107 T02b: the bounded-donation candidate must itself clear C4, C5,
    C6, C10, C11 (checked here in the same terms `run_checks`/`_plate_score`
    already use) before it is preferred over the unbounded fallback -- the
    plan's own fallback clause. `other_live` is every OTHER already-placed
    flat, used only for C5's no-a-flat-swallows-another-flat's-centre test;
    the full plate-wide `run_checks` pass still runs afterwards and is what
    actually gates the plate."""
    if merged is None or merged.is_empty or not isinstance(merged, Polygon):
        return False
    if lobes_of(merged) is not None:
        return False
    if len(merged.interiors) != 0:
        return False
    if len(merged.exterior.coords) - 1 > 40:
        return False
    if any(merged.contains(f.representative_point()) for f in other_live if not f.is_empty):
        return False
    contact = sbuf(merged, 0.05).intersection(P.exterior).length
    if contact < 2.50:
        return False
    if pinch_area(merged, P) > 0.10:
        return False
    if flat_aspect(merged) > MAX_FLAT_ASPECT:
        return False
    return True


def donate_leftovers(P, seeds):
    """D-EU-80: every square metre of P belongs to exactly one flat. Absorb every
    leftover piece (a non-largest column fragment, or a genuine gap between column
    clips) into the flat it touches most, never dropped, never left blank. A flat
    that a donation would turn into a lobed room is skipped for the next-best
    recipient instead (C4 must survive the donation). D-EU-107 (`FINDING 244`
    repair 2, T02b): a piece bigger than half the current mean flat area is not
    dumped whole into its best recipient -- `_bounded_split_piece` first tries
    to hand that recipient only up to half the mean, clearing C4/C5/C6/C10/C11
    (`_clears_donation_gates`) on the merge, and feeds the un-donated remainder
    back into the leftover pool for the next pass (a different flat, or the
    same one once it is no longer oversized). Only tried for the best-ranked
    recipient; if the split is geometrically degenerate or fails a gate, this
    falls back to today's unbounded whole-piece donation for that piece,
    honestly, never forced through."""
    flats = list(seeds)
    stuck = []
    for _ in range(25):
        covered = unary_union([f for f in flats if not f.is_empty]) if flats else Polygon()
        leftover = P.difference(covered) if not covered.is_empty else P
        pieces = _pieces(leftover)
        if not pieces:
            return flats, []
        live_now = [f for f in flats if not f.is_empty]
        mean_area = (sum(f.area for f in live_now) / len(live_now)) if live_now else 0.0
        progressed = False
        remaining = []
        for piece in pieces:
            candidates = _best_recipients(piece, flats)
            placed = False
            if candidates and mean_area > 0.0 and piece.area > 0.5 * mean_area:
                i = candidates[0]
                split = _bounded_split_piece(piece, 0.5 * mean_area, flats[i])
                if split is not None:
                    near_piece, far_piece = split
                    merged = _clean_merge(flats[i], near_piece)
                    other_live = [f for j, f in enumerate(flats) if j != i and not f.is_empty]
                    if merged is not None and _clears_donation_gates(merged, P, other_live):
                        flats[i] = merged
                        remaining.append(far_piece)
                        placed = True
                        progressed = True
            if not placed:
                for i in candidates:
                    merged = _clean_merge(flats[i], piece)
                    if merged is None:
                        continue
                    if lobes_of(merged) is not None and lobes_of(flats[i]) is None:
                        continue
                    flats[i] = merged
                    placed = True
                    progressed = True
                    break
            if not placed:
                remaining.append(piece)
        if not remaining:
            return flats, []
        if not progressed:
            stuck = remaining
            break
    return flats, stuck


def _delobe_and_donate(flats):
    """C4/D-EU-80: a flat with two or more lobes (lobes_of not None) is split at
    its own neck; every lobe but the largest is donated to whichever OTHER flat
    shares the most boundary with it (D-EU-77 metric), tried in order, skipped
    if the donation would lobe the recipient instead. A flat with no acceptable
    recipient for every one of its extra lobes is left exactly as it was -- a
    genuine residual, reported, never silently forced through."""
    flats = list(flats)
    for _ in range(len(flats) + 2):
        i = next((j for j, f in enumerate(flats)
                   if not f.is_empty and lobes_of(f) is not None), None)
        if i is None:
            return flats
        lobes = sorted((g for g in lobes_of(flats[i]) if not g.is_empty),
                        key=lambda g: g.area, reverse=True)
        if len(lobes) < 2:
            return flats
        keep, extras = lobes[0], lobes[1:]
        others_idx = [j for j in range(len(flats)) if j != i]
        new_flats = list(flats)
        new_flats[i] = keep
        moved_all = True
        for extra in extras:
            others_now = [new_flats[j] for j in others_idx]
            candidates = _best_recipients(extra, others_now)
            placed = False
            for local_c in candidates:
                j = others_idx[local_c]
                merged = _clean_merge(new_flats[j], extra)
                if merged is None:
                    continue
                if lobes_of(merged) is not None:
                    continue
                new_flats[j] = merged
                placed = True
                break
            if not placed:
                moved_all = False
                break
        if not moved_all or lobes_of(new_flats[i]) is not None:
            return flats
        flats = new_flats
    return flats


def _snap_world(g):
    """FINDING (T04, `07:340/356`): `to_world`'s rotation can leave two flats'
    shared boundary vertex at two different floating-point positions only ULPs
    apart -- exact in local frame, but each independently rotated, so GEOS's
    `intersection()` on the *rotated* pair can read a false, large overlap
    (confirmed: raw `intersection().area` reported the entirety of the smaller
    flat's own area as 'shared' with its neighbour, though the two are disjoint
    except at that one corner). Snapping every world-frame flat to the same
    0.001 m grid (mirrors `_normalize`/`05_group_cutters.py`'s own
    `_safe_precision`) forces a shared vertex back to one shared coordinate.
    Falls back to `buffer(0)`, then the unsnapped geometry, exactly as
    `05_group_cutters.py:171-179` does, so a genuinely hard case is still
    returned rather than raising."""
    try:
        return set_precision(g, 0.001)
    except Exception:
        pass
    try:
        return set_precision(g.buffer(0), 0.001)
    except Exception:
        return g


def _fix_snap_multipolygons(flats):
    """T05d (FINDING 243): `_snap_world`'s 0.001 m precision grid can turn a flat
    that survived rotation as an INVALID, self-touching Polygon (a razor-thin
    bowtie neck introduced by the floating-point rotation itself, not by the
    cut) into a genuine `MultiPolygon` once GEOS resolves the self-touch under
    `set_precision`'s `valid_output` mode -- confirmed on `COMPLEX_MULTI_WING
    way/100704705` (`theta_offset=90`, the swept-boundary variant): flat 4 is a
    clean 141.84 m2 `Polygon` before `to_world`, an *invalid* 141.84 m2
    `Polygon` right after rotation, and a 141.57 + 0.25 m2 `MultiPolygon` the
    instant `_snap_world` runs. Every downstream reader (`_plate_score`,
    `_best_recipients`, `_delobe_and_donate`, `run_checks`) assumes one flat is
    one `Polygon` and raises `AttributeError` on `.exterior`/`.interiors` the
    moment it sees the extra piece -- the exact fault `FINDING 243` measured on
    17 census buildings the 550 test plates never happened to trigger (the
    swept-boundary and grid candidates that expose it are only ever reached by
    plates the 550-plate battery never drew at this k/theta combination).
    Same donation shape as `_clean_merge`/`_best_recipients` already use for
    D-EU-80 leftovers, and the same pattern as `05_group_cutters.py:264`'s own
    `dissolve_pass` (read-only, mirrored here, never imported): keep each
    flat's own largest piece, then give every other piece to whichever flat --
    any flat, including this one's own remaining piece -- shares the most
    boundary with it, via the exact `_clean_merge` gate (accepted only if the
    union comes back one clean `Polygon`). Never drops area: a piece with no
    directly-touching recipient is retried against a small buffer at the same
    scale as the 0.001 m snap grid that created it, escalated only as far as
    needed, before ever being counted unplaced."""
    flats = list(flats)
    leftovers = []
    for i, f in enumerate(flats):
        if f.is_empty or isinstance(f, Polygon):
            continue
        parts = sorted(_pieces(f), key=lambda g: g.area, reverse=True)
        if not parts:
            flats[i] = Polygon()
            continue
        flats[i] = parts[0]
        leftovers.extend(parts[1:])
    for piece in leftovers:
        if piece is None or piece.is_empty or piece.area <= 1e-9:
            continue
        candidates = _best_recipients(piece, flats)
        placed = False
        for j in candidates:
            for buf in (0.0, 0.005, 0.02, 0.1):
                cand_piece = piece if buf == 0.0 else piece.buffer(buf, cap_style=3, join_style=2)
                merged = _clean_merge(flats[j], cand_piece)
                if merged is not None:
                    flats[j] = merged
                    placed = True
                    break
            if placed:
                break
        if not placed:
            j = max(range(len(flats)), key=lambda idx: flats[idx].area if not flats[idx].is_empty else -1.0)
            for buf in (0.1, 0.5, 2.0):
                merged = _clean_merge(flats[j], piece.buffer(buf, cap_style=3, join_style=2))
                if merged is not None:
                    flats[j] = merged
                    placed = True
                    break
    return flats


def cut_nocore(poly, k, theta_offset=0.0, bx=None):
    """No corridor, no core: k equal-area columns in the plate's own frame, clipped
    to the real footprint, with every leftover fragment donated to the flat it
    touches most (D-EU-80). `theta_offset` (D-EU-81/T03) tries the perpendicular
    cut axis; `bx` (D-EU-81/T03) overrides the equal-area boundary positions with a
    swept set that maximises the narrowest flat."""
    poly = _normalize(poly)
    theta, cx, cy, L, W = frame(poly)
    theta = theta + theta_offset
    P = to_local(poly, theta, cx, cy)
    cols = _cut_columns(P, k, bx=bx)
    seeds = _seed_flats(cols)
    flats_local, stuck = donate_leftovers(P, seeds)
    flats_world = [_snap_world(to_world(f, theta, cx, cy)) for f in flats_local]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly, flats_world, stuck


def cut_grid(poly, k, theta_offset=0.0, rows=2):
    """D-EU-81/T04 attack-order item 2(iii): a `rows`-band grid in place of a
    single row of k columns, same footprint clip and D-EU-80 donation as
    `cut_nocore`. Returns None if `_grid_seeds` finds nothing to gain (k < rows)."""
    poly = _normalize(poly)
    theta, cx, cy, L, W = frame(poly)
    theta = theta + theta_offset
    P = to_local(poly, theta, cx, cy)
    seeds = _grid_seeds(P, k, rows=rows)
    if seeds is None:
        return None
    flats_local, stuck = donate_leftovers(P, seeds)
    flats_world = [_snap_world(to_world(f, theta, cx, cy)) for f in flats_local]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly, flats_world, stuck


def cut_grid_snapped(poly, k, theta_offset, rows, reflex_xs_local):
    """eu21-colour-repair/T03 how: `cut_grid`'s own sibling with reflex-vertex
    boundary snapping (`_grid_seeds_snapped`) -- `cut_grid` itself is never
    edited above. `reflex_xs_local` is precomputed by the caller (build_flats)
    in this exact `theta_offset`'s local frame, so the frame here matches the
    frame the boundaries were snapped in."""
    poly = _normalize(poly)
    theta, cx, cy, L, W = frame(poly)
    theta = theta + theta_offset
    P = to_local(poly, theta, cx, cy)
    seeds = _grid_seeds_snapped(P, k, rows, reflex_xs_local)
    if seeds is None:
        return None
    flats_local, stuck = donate_leftovers(P, seeds)
    flats_world = [_snap_world(to_world(f, theta, cx, cy)) for f in flats_local]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly, flats_world, stuck


def _split_at_y(merged, y0):
    """D-EU-86/T05b helper: an exact 2-way partition of `merged` at the local
    line y = y0, via shapely's own topological split (never a box-intersection
    pair, which can leave a hairline gap or overlap between the two halves
    after `_snap_world`'s precision rounding and inflate C5's point count).
    Returns (None, None) unless the split comes back exactly one polygon above
    the line and exactly one below -- a merged piece that the line cuts into
    more than two fragments (a ring wall crossing a corner, say) is refused
    rather than patched, so the caller falls back to the untouched pair."""
    minx, miny, maxx, maxy = merged.bounds
    line = LineString([(minx - 1.0, y0), (maxx + 1.0, y0)])
    try:
        pieces = list(_shp_split(merged, line).geoms)
    except Exception:
        return None, None
    tops = [g for g in pieces if g.geom_type == "Polygon" and g.representative_point().y >= y0]
    bots = [g for g in pieces if g.geom_type == "Polygon" and g.representative_point().y < y0]
    if len(tops) != 1 or len(bots) != 1:
        return None, None
    return tops[0], bots[0]


def cut_layered(poly, k, theta_offset=0.0, passes=3):
    """D-EU-86 (FINDING 240): the single-axis cut's own columns, but a column
    pair whose worst aspect still exceeds `MAX_FLAT_ASPECT` is merged with its
    run-wise neighbour and re-cut ACROSS ITS DEPTH (an equal-area split on the
    perpendicular axis, local to just that merged pair) instead of only along
    the run -- ruling clause 3's "a band whose local width exceeds roughly
    twice the target flat's short side is cut in two layers". A merge is kept
    only when: the depth-split comes back as exactly two clean polygons
    (`_split_at_y`); neither half is lobed; each half still carries >= 2.50 m
    of the plate's own OUTER-facade contact (`C6` is never loosened -- a
    courtyard's inner ring wall may not be isolated onto the void side only,
    which is exactly how the naive whole-plate `cut_grid` bands lost C6 for
    this shape); and the merge strictly lowers the pair's own worst aspect.
    Anything that fails one of these gates keeps its original two ribbons
    untouched -- this candidate can only ever help a plate, never regress one,
    and is one more entry in `build_flats`'s own best-of-score search, never a
    forced replacement. `passes` repeats the sweep so a flat freed by one
    merge can be re-tried against its new neighbour."""
    poly_n = _normalize(poly)
    theta, cx, cy, L, W = frame(poly_n)
    theta_full = theta + theta_offset
    P = to_local(poly_n, theta_full, cx, cy)
    cols = _cut_columns(P, k, bx=None)
    seeds = _seed_flats(cols)
    flats_local, stuck = donate_leftovers(P, seeds)
    if stuck:
        return None
    flats_local = list(flats_local)
    for _pass in range(passes):
        order = sorted(range(len(flats_local)),
                        key=lambda i: flats_local[i].centroid.x if not flats_local[i].is_empty else 0.0)
        changed = False
        i = 0
        while i + 1 < len(order):
            a_idx, b_idx = order[i], order[i + 1]
            fa, fb = flats_local[a_idx], flats_local[b_idx]
            if fa.is_empty or fb.is_empty:
                i += 1
                continue
            worst_before = max(flat_aspect(fa), flat_aspect(fb))
            if worst_before <= MAX_FLAT_ASPECT:
                i += 1
                continue
            merged = _clean_merge(fa, fb)
            if merged is None:
                i += 1
                continue
            ys = _equal_area_y(merged, 2)
            if not ys:
                i += 1
                continue
            new_top, new_bot = _split_at_y(merged, ys[0])
            if new_top is None or new_bot is None:
                i += 1
                continue
            if lobes_of(new_top) is not None or lobes_of(new_bot) is not None:
                i += 1
                continue
            contact_top = sbuf(to_world(new_top, theta_full, cx, cy), 0.05).intersection(poly_n.exterior).length
            contact_bot = sbuf(to_world(new_bot, theta_full, cx, cy), 0.05).intersection(poly_n.exterior).length
            if contact_top < 2.50 or contact_bot < 2.50:
                i += 1
                continue
            worst_after = max(flat_aspect(new_top), flat_aspect(new_bot))
            if worst_after >= worst_before:
                i += 1
                continue
            flats_local[a_idx] = new_top
            flats_local[b_idx] = new_bot
            changed = True
            i += 2
        if not changed:
            break
    flats_world = [_snap_world(to_world(f, theta_full, cx, cy)) for f in flats_local]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly_n, flats_world, []


def _wedge(cx, cy, R, a0, a1):
    """T05d (FINDING 242, `D-EU-89` clause 2) helper for `cut_radial`: a pie-slice
    polygon from `(cx, cy)` out to radius `R`, spanning angle `a0` to `a1`
    (radians, `a1 > a0`). `R` is always called well beyond the plate's own
    extent, so only the two straight radial edges ever touch the real footprint
    -- the outer edge is approximated by short chords (15 degree steps) purely
    so the wedge stays a simple, valid polygon; the approximation error at that
    distance never reaches the plate."""
    n_arc = max(2, int(math.degrees(a1 - a0) / 15.0) + 1)
    pts = [(cx, cy)]
    for i in range(n_arc + 1):
        a = a0 + (a1 - a0) * i / n_arc
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    return Polygon(pts)


def _equal_area_theta(poly, cx, cy, N, R, a0):
    """T05d helper: `equal_area_x`'s own binary-search sweep, walked over angle
    around `(cx, cy)` instead of over x, starting at `a0`. Returns the `N - 1`
    interior angular boundaries (radians, ascending from `a0`); the caller closes
    the ring with `a0` and `a0 + 2*pi`."""
    if N <= 1:
        return []
    total = poly.area
    thetas = []
    prev = a0
    for i in range(1, N):
        target = i / N * total
        lo, hi = prev, a0 + 2 * math.pi
        for _ in range(40):
            if hi - lo < 1e-5:
                break
            mid = (lo + hi) / 2
            a = poly.intersection(_wedge(cx, cy, R, a0, mid)).area
            if a < target:
                lo = mid
            else:
                hi = mid
        mid = (lo + hi) / 2
        thetas.append(mid)
        prev = mid
    return thetas


def cut_radial(poly, k, theta_offset=0.0):
    """D-EU-89 clause 2 (`FINDING 242`): a courtyard ring's own void, cut into k
    equal-area angular sectors radiating from the void's centroid, instead of a
    plate-wide Cartesian band. Every sector spans the ring's full radial depth
    by construction, so it touches both the inner (void) and the outer
    boundary -- exactly the property the plate-wide band cut lacks (a
    horizontal band across a ring's middle touches only the inner hole
    boundary over part of its run, which is why `cut_layered`'s own C6 gate
    never accepts a merge there, `D-EU-86`'s own diagnosis). Returns None if
    `poly` has no interior ring (not a courtyard) -- never attempted on a shape
    it cannot help. `theta_offset` (degrees) rotates the sector boundaries, the
    same second-axis search `D-EU-83` already runs for every other candidate."""
    poly_n = _normalize(poly)
    if len(poly_n.interiors) == 0:
        return None
    void = max(poly_n.interiors, key=lambda ring: Polygon(ring).area)
    cx, cy = Polygon(void).centroid.x, Polygon(void).centroid.y
    minx, miny, maxx, maxy = poly_n.bounds
    R = 2.0 * max(maxx - minx, maxy - miny, 1.0) + 10.0
    a0 = math.radians(theta_offset)
    thetas = [a0] + _equal_area_theta(poly_n, cx, cy, k, R, a0) + [a0 + 2 * math.pi]
    seeds = []
    for i in range(k):
        w = _wedge(cx, cy, R, thetas[i], thetas[i + 1])
        seeds.append(poly_n.intersection(w))
    seeds = _seed_flats(seeds)
    flats_world, stuck = donate_leftovers(poly_n, seeds)
    flats_world = [_snap_world(f) for f in flats_world]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly_n, flats_world, stuck


# eu21-colour-repair/T04 -- courtyard ring bisection at low k, a sibling of
# `cut_radial` above (never edited), called from the same place in
# `build_flats`. `cut_radial` already handles rings but, at `k <= 2`, its
# equal-area angular sectors either don't fire (k==1 spans the full 2*pi and
# still carries the whole void as one flat -- the C5 defect the red report's
# §4 Step 2 names) or split at arbitrary equal-area angles that need not sit
# on the ring's own narrowest bridge. This candidate targets exactly that gap.
RING_BRIDGE_WIDTH_M = 0.05  # the wall opening this candidate cuts (D-EU-87's
                              # own 0.10 m2 pinch floor and C1's 0.999 coverage
                              # floor both clear this by a wide margin)
RING_BRIDGE_MIN_SEPARATION_FRACTION = 0.25  # of the void's own perimeter, k==2


def _ring_bridge_candidates(poly_n, void, n_samples=200):
    """T04 how: sample the void's own boundary and, for each sample, its
    distance to the plate's own outer boundary -- the material bridge width
    at that location, `(width, inner_pt, outer_pt, arc_position)` triples,
    narrowest first."""
    outer = poly_n.exterior
    ring = void.exterior
    length = ring.length
    if length <= 0:
        return []
    triples = []
    for i in range(n_samples):
        d = length * i / n_samples
        inner_pt = ring.interpolate(d)
        width = inner_pt.distance(outer)
        outer_pt = outer.interpolate(outer.project(inner_pt))
        triples.append((width, inner_pt, outer_pt, d))
    triples.sort(key=lambda t: t[0])
    return triples


def _bridge_cut_rect(outer_pt, inner_pt, width=RING_BRIDGE_WIDTH_M, ext=0.3):
    """A thin rectangle spanning from just outside `outer_pt` to just past
    `inner_pt` (into the void), `width` wide -- `poly.difference(rect)` opens
    the ring at that bridge via a robust, well-tested GEOS boolean, never
    hand-rolled ring surgery."""
    dx, dy = inner_pt.x - outer_pt.x, inner_pt.y - outer_pt.y
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    p0 = (outer_pt.x - ux * ext, outer_pt.y - uy * ext)
    p1 = (inner_pt.x + ux * ext, inner_pt.y + uy * ext)
    hw = width / 2.0
    return Polygon([
        (p0[0] + nx * hw, p0[1] + ny * hw),
        (p1[0] + nx * hw, p1[1] + ny * hw),
        (p1[0] - nx * hw, p1[1] - ny * hw),
        (p0[0] - nx * hw, p0[1] - ny * hw),
    ])


def cut_ring_bisect(poly, k):
    """eu21-colour-repair/T04 how: for a ring-shaped plate (`poly.interiors`
    non-empty) at `k in (1, 2)`, bisect the ring at its own narrowest
    bridge(s) instead of leaving a flat that inherits the hole. `k == 1`: one
    bridge cut opens the ring into a single simply-connected C-flat, scored
    against its OWN cut outline (not `poly_n`) -- `donate_leftovers` (D-EU-80,
    inside `_finish_candidate`) makes every square metre of its reference
    `poly` belong to some flat, so scoring a single flat against the
    uncut `poly_n` makes the bridge sliver a "leftover" and re-donates it
    straight back into that one flat, undoing the cut (found empirically,
    `relation/4154504`: `_finish_candidate` returned `interiors == 1` again).
    Scoring the flat against its own cut outline is exactly what every other
    `k == 1` candidate already does (one flat, one plate, byte-identical
    boundaries) -- not a new pattern. `k == 2`: the two narrowest bridges, at
    least
    `RING_BRIDGE_MIN_SEPARATION_FRACTION` of the void's own perimeter apart,
    cut two C-flats. Only the plate's LARGEST interior ring is targeted; a
    plate with more than one courtyard still carries its other holes on
    whichever piece inherits them, so this returns `None` there (checked via
    `len(piece.interiors) == 0`, never forced) -- a residual, not a bug (§6
    T04 how to test: "a residual is expected and must be named"). Returns
    `None` on a non-ring plate or `k not in (1, 2)`, exactly as `cut_radial`
    returns `None` on a non-ring plate. `_plate_score` decides whether the
    result wins (§5.2) -- this is one more candidate, never a replacement."""
    poly_n = _normalize(poly)
    if len(poly_n.interiors) == 0 or k not in (1, 2):
        return None
    void = max((Polygon(r) for r in poly_n.interiors), key=lambda p: p.area)
    candidates = _ring_bridge_candidates(poly_n, void)
    if not candidates:
        return None
    if k == 1:
        _, ipt, opt, _ = candidates[0]
        rect = _bridge_cut_rect(opt, ipt)
        try:
            cut = poly_n.difference(rect)
        except Exception:
            return None
        if cut.geom_type != "Polygon" or not cut.is_valid or len(cut.interiors) != 0:
            return None
        if cut.area / poly_n.area < 0.999:
            return None
        return cut, [cut], []
    void_perim = void.exterior.length or 1.0
    first = candidates[0]
    second = None
    for cand in candidates[1:]:
        d_sep = abs(cand[3] - first[3])
        d_sep = min(d_sep, void_perim - d_sep)
        if d_sep >= RING_BRIDGE_MIN_SEPARATION_FRACTION * void_perim:
            second = cand
            break
    if second is None:
        return None
    rect1 = _bridge_cut_rect(first[2], first[1])
    rect2 = _bridge_cut_rect(second[2], second[1])
    try:
        cut = poly_n.difference(unary_union([rect1, rect2]))
    except Exception:
        return None
    pieces = _pieces(cut)
    if len(pieces) != 2 or any((not p.is_valid) or len(p.interiors) != 0 for p in pieces):
        return None
    if sum(p.area for p in pieces) / poly_n.area < 0.999:
        return None
    return poly_n, pieces, []


def cut_wingwise(poly, k, theta_offset=0.0):
    """D-EU-89 clause 2 (`FINDING 242`): a multi-wing plate's own wings (found by
    `lobes_of`, the same neck-erosion decomposition already used to split a
    lobed flat -- read-only, mirrored on the whole footprint here, not a flat),
    each cut into segments along ITS OWN frame instead of the plate's one
    shared axis. `D-EU-86`'s residual (`COMPLEX_MULTI_WING way/968439455` and
    kin) is a plate whose wings run at different bearings, so a single shared
    frame cuts across a wing at an angle and stretches the flat; each wing
    columned in its own local frame does not. Flats per wing are apportioned by
    area (the same rounding sweep `_grid_seeds` already uses). Returns None
    when the plate is not a multi-wing shape (`lobes_of` finds fewer than two
    wings) or there are more wings than flats to give them."""
    poly_n = _normalize(poly)
    wings_raw = lobes_of(poly_n)
    if wings_raw is None:
        return None
    wings = [w for w in wings_raw if not w.is_empty and w.area > 1e-6]
    if len(wings) < 2 or k < len(wings):
        return None
    areas = [w.area for w in wings]
    total = sum(areas) or 1.0
    counts = [max(1, round(k * a / total)) for a in areas]
    diff = k - sum(counts)
    order = sorted(range(len(wings)), key=lambda i: -areas[i])
    guard = 0
    while diff != 0 and guard < 10 * len(wings):
        i = order[guard % len(wings)]
        if diff > 0:
            counts[i] += 1
            diff -= 1
        elif counts[i] > 1:
            counts[i] -= 1
            diff += 1
        guard += 1
    seeds = []
    for w, n_i in zip(wings, counts):
        theta_w, cx_w, cy_w, L_w, W_w = frame(w)
        theta_w = theta_w + theta_offset
        w_local = to_local(w, theta_w, cx_w, cy_w)
        xs = equal_area_x(w_local, n_i)
        xs = _dodge_hole_boundaries(w_local, xs)
        wminx, wminy, wmaxx, wmaxy = w_local.bounds
        bxw = [wminx - 1] + xs + [wmaxx + 1]
        for j in range(n_i):
            c_local = w_local.intersection(box(bxw[j], wminy - 1, bxw[j + 1], wmaxy + 1))
            seeds.append(to_world(c_local, theta_w, cx_w, cy_w))
    seeds = _seed_flats(seeds)
    flats_world, stuck = donate_leftovers(poly_n, seeds)
    flats_world = [_snap_world(f) for f in flats_world]
    flats_world = _fix_snap_multipolygons(flats_world)
    return poly_n, flats_world, stuck

# ---------------------------------------------------------------------------
# D-EU-81/T03 -- boundary sweep and axis choice.


def _sweep_boundaries(P, k, passes=3, samples=24):
    """T03 step 1: equal area is no longer required (DD-C), so slide each interior
    column boundary to maximise the minimum widest_fit of the two columns it
    separates. Only the immediate neighbour columns are affected by one boundary,
    so this is a coordinate-descent sweep, a few passes to convergence."""
    minx, miny, maxx, maxy = P.bounds
    if k < 2:
        return None
    xs = _dodge_hole_boundaries(P, equal_area_x(P, k))
    for _ in range(passes):
        changed = False
        for i in range(len(xs)):
            lo = xs[i - 1] if i > 0 else minx - 1
            hi = xs[i + 1] if i + 1 < len(xs) else maxx + 1
            if hi - lo < 1e-6:
                continue
            best_x, best_score = xs[i], None
            for t in range(samples + 1):
                cand = lo + (hi - lo) * t / samples
                left = P.intersection(box(lo, miny - 1, cand, maxy + 1))
                right = P.intersection(box(cand, miny - 1, hi, maxy + 1))
                lp, rp = _pieces(left), _pieces(right)
                if not lp or not rp:
                    continue
                lf = max(lp, key=lambda g: g.area)
                rf = max(rp, key=lambda g: g.area)
                score = min(widest_fit(lf), widest_fit(rf))
                if best_score is None or score > best_score + 1e-9:
                    best_score, best_x = score, cand
            if abs(best_x - xs[i]) > 1e-6:
                xs[i] = best_x
                changed = True
        if not changed:
            break
    return [minx - 1] + xs + [maxx + 1]


def _coverage(poly, flats):
    live = [f for f in flats if not f.is_empty]
    if not live or not poly.area:
        return 0.0
    return sum(f.area for f in live) / poly.area


def _plate_score(poly, flats):
    """Higher is better: (D-EU-80 coverage, C5 simple-outline, C6 facade contact,
    C4-safe flat count, C11 proportion gate, C10 pinch gate, C12 area balance
    (`D-EU-107`, `FINDING 244`, plan `eu-plan-homogeneity-2026-09-07` T02a),
    -created-pinch area (D-EU-87) as the tie-break, min C6 contact value, -max
    flat aspect). Coverage, C5 and C6 are hard boolean gates, never traded away
    for a wider plate -- T04's own residual (`FINDING` note in the plan) showed
    a naive min-C10-first score silently trading a passing C6 (>= 2.50 m facade
    contact) for a wider flat, which is exactly the kind of regression rule 2 of
    this arc forbids. C4 (no lobed flat) ranks next, since a wider plate that
    still fails C4 is not an improvement (T03 how, step 2: "keep whichever
    plate-wide result scores better on min(C10), then C4, then C6"). C11
    (D-EU-82, T03) outranks the pinch-area tie-break -- a plate is not an
    improvement if it turns a flat into a ribbon. C10 (`c10_ok = pinch_total <=
    0.10`, director's ruling `D-EU-107 f`, 2026-09-07): booleanised and ranked
    beside the other hard gates, the same pattern C6 (`c6_ok` then `min_c6`) and
    C11 (`c11_ok` then `-max_aspect`) already use in this function -- T02a's
    first cut ranked `spread` ahead of the *continuous* `-pinch_total` term
    only, with no boolean C10 gate in the tuple at all, so a candidate could win
    on spread while silently failing C10; measured fleet-wide as 458 PASS ->
    FAIL regressions, all on C10, before this correction. `spread` (same
    field/formula as `run_checks`, `min(area) / max(area)` over the live flats)
    now ranks after C10 (as well as cov/C5/C6/C4/C11) and before the
    pinch/aspect tie-break: it never overrides any hard gate, it only chooses
    the more balanced candidate among those that already tie on every one of
    them. `widest_fit` no longer appears in this tuple at all (D-EU-87 clause
    1): the created-pinch area (D-EU-87 clause 2/3, `pinch_area`) is minimised
    as the tie-break, and `-max_aspect` is the final tie-break, so among
    candidates that already clear every gate the squarer, least-pinched, most
    balanced one wins."""
    live = [f for f in flats if not f.is_empty]
    cov_ok = _coverage(poly, flats) >= 0.999
    no_holes = all(len(f.interiors) == 0 for f in live)
    reps = [f.representative_point() for f in live]
    no_contain = all(not (i != j and fi.contains(pt)) for i, fi in enumerate(live) for j, pt in enumerate(reps))
    max_pts = max((len(f.exterior.coords) - 1 for f in live), default=0)
    c5_ok = no_holes and no_contain and max_pts <= 40
    contacts = [sbuf(f, 0.05).intersection(poly.exterior).length for f in live]
    min_c6 = min(contacts) if contacts else 0.0
    c6_ok = min_c6 >= 2.50
    c4_ok = sum(1 for f in live if lobes_of(f) is None)
    pinch_total = sum(pinch_area(f, poly) for f in live)
    c10_ok = pinch_total <= 0.10
    max_aspect = max((flat_aspect(f) for f in live), default=99.0)
    c11_ok = (len(live) <= 1) or (max_aspect <= MAX_FLAT_ASPECT)
    areas = [f.area for f in live]
    spread = (min(areas) / max(areas)) if areas and max(areas) > 0 else 0.0
    return (cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, c10_ok, round(spread, 4),
            round(-pinch_total, 3), round(min_c6, 3), round(-max_aspect, 3))


def _fully_ok(poly, flats):
    """True when every one of C1, C4, C5, C6, C10, C11 already passes -- the gate
    for both the fix ladder's early exit (T02/T03) and the T04 broadening: a
    plate is only skipped past the ladder when nothing (not just C10) still
    needs fixing. C10 (D-EU-87) is now the created-pinch-area test: total
    pinch <= 0.10 m2, the measured float-noise floor, never a widened
    allowance."""
    live = [f for f in flats if not f.is_empty]
    cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, c10_ok, _spread, neg_pinch, _, _ = _plate_score(poly, flats)
    return cov_ok and c5_ok and c6_ok and c4_ok == len(live) and c11_ok and c10_ok and (-neg_pinch) <= 0.10


def _donate_the_neck(poly, flats):
    """T03 step 3, retargeted at D-EU-87/T05c (`FINDING 241`): a pinch that
    survives axis choice and the boundary sweep is footprint geometry, not cut
    geometry. Driven by `_pinch_geom`/`pinch_area` (the created-pinch test C10
    now scores), not `widest_fit` -- `widest_fit` reports the best disc
    anywhere in a flat and stays silent about a narrow strip elsewhere in the
    same, otherwise-wide, flat, which is exactly the defect D-EU-87 measured.
    For the flat with the largest created-pinch area, give the pinch piece
    itself (the exact narrow geometry, not a probe-width guess) to the
    neighbour it shares the most boundary with -- exactly as D-EU-80 donates a
    leftover -- unless that donation would lobe a flat, in which case try the
    next-best recipient."""
    flats = list(flats)
    for _ in range(len(flats) + 2):
        pinches = [(pinch_area(f, poly), i) for i, f in enumerate(flats) if not f.is_empty]
        if not pinches:
            break
        p_max, i = max(pinches, key=lambda t: t[0])
        if p_max <= 0.10:
            break
        f = flats[i]
        waist = _pinch_geom(f, poly)
        waist_pieces = _pieces(waist) if waist is not None else []
        if not waist_pieces:
            break
        others = [g for j, g in enumerate(flats) if j != i and not g.is_empty]
        moved_any = False
        for piece in waist_pieces:
            if piece.area < 0.05:
                continue
            candidates = _best_recipients(piece, others)
            placed = False
            for cand_idx in candidates:
                target = others[cand_idx]
                real_i = flats.index(target)
                remainder = f.difference(piece.buffer(0.005))
                rem_pieces = _pieces(remainder)
                if len(rem_pieces) != 1:
                    continue
                new_f = rem_pieces[0]
                merged = _clean_merge(target, piece)
                if merged is None:
                    continue
                if lobes_of(new_f) is not None or lobes_of(merged) is not None:
                    continue
                new_pinch = pinch_area(new_f, poly)
                if new_pinch >= p_max and new_f.area < f.area:
                    continue
                flats[i] = new_f
                flats[real_i] = merged
                placed = True
                moved_any = True
                break
            if placed:
                break
        if not moved_any:
            break
    return flats


STAGE = "t03"  # "t01" seed columns only (06's own behaviour); "t02" + donation,
                # single axis, no sweep; "t03" full regime (axis + sweep + donation
                # + neck). Diagnostic-only switch for the plan's staged how-to-test;
                # production runs (main()) always use the "t03" default.


def _cut_nocore_t01(poly, k):
    """T01 baseline: verbatim port of 06_nocore_control.py's cut_nocore -- a
    clipped column that comes back a MultiPolygon has its non-largest pieces
    dropped by _normalize, exactly as 06 does. Kept only so T01's own
    how-to-test can be honestly reproduced; never used by main()."""
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
    return poly, flats_world, []


MAX_GRID_ROWS = 6  # D-EU-83/T04: rows searched from 1 (today's single row) up to this cap

# eu21-colour-repair/T02 -- the angle search's own candidate set.
MAX_THETA_OFFSETS = 12
LONG_EDGE_PERIM_FRACTION = 0.15
REFLEX_DENOISE_TOLERANCE_M = 0.5  # matches classify_building_morphology's own
                                    # denoise call immediately before it invokes
                                    # `_reflex_vertex_count` (european_residential.py:459)


def _fold_theta_offset(angle_deg, theta):
    """T02 (§6 how): an absolute bearing, expressed as a `theta_offset` delta
    from the frame's own axis `theta` and normalised into `[0, 90)` -- the
    domain the plan's how specifies. A candidate exactly on the fold boundary
    lands at `0.0`, so it collapses into today's own first candidate rather
    than minting a near-duplicate."""
    d = (angle_deg - theta) % 180.0
    if d >= 90.0:
        d -= 90.0
    return d


def _edge_theta_offsets(poly_n, theta):
    """T02(b): the bearing of every exterior edge at least 15% of the plate's
    own perimeter, folded to a `theta_offset` delta and returned longest-edge-
    first (the cap-12 tie-break order the how specifies)."""
    coords = list(poly_n.exterior.coords)[:-1]
    n = len(coords)
    if n < 2:
        return []
    perim = poly_n.exterior.length or 1.0
    edges = []
    for i in range(n):
        a, b = coords[i], coords[(i + 1) % n]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length >= LONG_EDGE_PERIM_FRACTION * perim:
            bearing = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            edges.append((length, _fold_theta_offset(bearing, theta)))
    edges.sort(key=lambda t: -t[0])
    return [d for _, d in edges]


def _bisector_deg(a, b, c):
    """Plain vector bisector of the corner a-b-c (degrees) -- generic
    geometry, not reflex-vertex detection, so it is not covered by §4.2's
    import-don't-reimplement rule."""
    ux, uy = b[0] - a[0], b[1] - a[1]
    vx, vy = c[0] - b[0], c[1] - b[1]
    la = math.hypot(ux, uy) or 1.0
    lc = math.hypot(vx, vy) or 1.0
    ux, uy, vx, vy = ux / la, uy / la, vx / lc, vy / lc
    bx, by = ux + vx, uy + vy
    if abs(bx) < 1e-9 and abs(by) < 1e-9:
        bx, by = ux, uy
    return math.degrees(math.atan2(by, bx))


def _reflex_theta_offsets(poly_n, theta):
    """T02(c): the bisector direction at each reflex vertex found by
    `_reflex_vertex_count`'s own 0.5 m denoise path -- `_reflex_vertices`
    (imported, §4.2) runs the identical denoise-and-detect walk at that same
    tolerance, so this is exactly that vertex set, never a re-derivation of
    which corners are reflex."""
    from openubem.geometry.european_residential import _reflex_vertices
    denoised = poly_n.simplify(REFLEX_DENOISE_TOLERANCE_M, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = poly_n
    points = _reflex_vertices(denoised, tolerance_m=REFLEX_DENOISE_TOLERANCE_M)
    if not points:
        return []
    coords = list(denoised.exterior.coords)[:-1]
    n = len(coords)
    if n < 3:
        return []
    offsets = []
    for pt in points:
        idx = min(range(n), key=lambda i: math.dist(coords[i], pt))
        a, b, c = coords[idx - 1], coords[idx], coords[(idx + 1) % n]
        offsets.append(_fold_theta_offset(_bisector_deg(a, b, c), theta))
    return offsets


def _theta_offset_candidates(poly_n, theta):
    """T02: the search's own candidate `theta_offset` set -- (a) `0.0` and
    `90.0` first, unfolded, so ties keep today's answer exactly; then (b) the
    long exterior edges, longest first; then (c) the reflex-vertex bisectors.
    Deduplicated at 1.0 degree resolution, capped at `MAX_THETA_OFFSETS`.
    Falls back to today's own `(0.0, 90.0)` on any geometry exception -- this
    candidate set can only ever add to the search (§5.2), never remove from
    it, so a failure here must reproduce the old behaviour, not crash it."""
    try:
        seen = set()
        out = []
        for d in (0.0, 90.0):
            key = round(d)
            if key not in seen and len(out) < MAX_THETA_OFFSETS:
                seen.add(key)
                out.append(d)
        for d in _edge_theta_offsets(poly_n, theta):
            key = round(d)
            if key not in seen and len(out) < MAX_THETA_OFFSETS:
                seen.add(key)
                out.append(round(d, 1))
        for d in _reflex_theta_offsets(poly_n, theta):
            key = round(d)
            if key not in seen and len(out) < MAX_THETA_OFFSETS:
                seen.add(key)
                out.append(round(d, 1))
        return out
    except Exception:
        return [0.0, 90.0]


# eu21-colour-repair/T03 -- reflex-vertex boundary snapping.
REFLEX_SNAP_TOLERANCE_M = 0.75  # T03 how: the gap a boundary may snap across
REFLEX_SNAP_DENOISE_TOLERANCE_M = 0.15  # `_split_at_reflex_vertex`'s own
                                          # default tolerance_m (§4.2, imported)


def _reflex_points_world(poly_n):
    """T03 (§4.2): every reflex vertex of `poly_n`, in world coordinates --
    `_reflex_vertices` (imported, never re-derived) at `_split_at_reflex_vertex`'s
    own denoise tolerance. Computed once per plate; each candidate below
    projects this same point set into its own local frame."""
    from openubem.geometry.european_residential import _reflex_vertices
    try:
        return list(_reflex_vertices(poly_n, tolerance_m=REFLEX_SNAP_DENOISE_TOLERANCE_M))
    except Exception:
        return []


def _reflex_local_xs(points_world, theta_full, cx, cy):
    xs = []
    for pt in points_world:
        try:
            xs.append(to_local(Point(pt), theta_full, cx, cy).x)
        except Exception:
            continue
    return xs


def _snap_boundaries(xs, reflex_xs, lo, hi):
    """T03 how: move each interior boundary in `xs` (ascending, local frame)
    onto the nearest reflex vertex within `REFLEX_SNAP_TOLERANCE_M`, unless
    the move would reorder boundaries or collapse a column to zero width.
    Returns `None` (nothing to add) when no boundary moved -- snapping is one
    additional candidate, never a replacement for the unsnapped one (§6 T03
    how); the caller only spends a cut on this when it actually changed
    something."""
    if not xs or not reflex_xs:
        return None
    xs = list(xs)
    snapped_any = False
    for i in range(len(xs)):
        left_bound = xs[i - 1] if i > 0 else lo
        right_bound = xs[i + 1] if i + 1 < len(xs) else hi
        candidates = [rx for rx in reflex_xs if abs(rx - xs[i]) <= REFLEX_SNAP_TOLERANCE_M]
        if not candidates:
            continue
        rx = min(candidates, key=lambda v: abs(v - xs[i]))
        if not (left_bound + 1e-6 < rx < right_bound - 1e-6):
            continue
        if abs(rx - xs[i]) < 1e-9:
            continue
        xs[i] = rx
        snapped_any = True
    return xs if snapped_any else None


def _finish_candidate(p, flats, stuck):
    """eu21-colour-repair/T02 fix: the created-pinch rescue (`_donate_the_neck`)
    is applied to EVERY candidate here, not only to the search's eventual
    winner. §5.2 assumes a broader search "can only raise the winning score
    or be discarded", but that only holds if every candidate is compared on
    its own best-achievable outcome -- a candidate with a large but rescuable
    raw pinch must get the same rescue chance as every other candidate before
    the `sc > best[0]` comparison runs, or a genuinely better raw candidate
    (small unrescuable residual pinch) can out-rank a worse-looking one that
    would have rescued cleanly, and the FINAL verdict regresses even though
    `_plate_score` never did (measured on control-set plate `way/311159688`:
    without this fix T02 turns its PASS at pinch 0.03 into a FAIL at pinch
    0.12). Mirrors the previous single post-loop rescue exactly, just run
    per-candidate; `_plate_score`/`_fully_ok` themselves are untouched (§2
    rule 5)."""
    flats = _delobe_and_donate(flats)
    flats, stuck = donate_leftovers(p, flats)
    score = _plate_score(p, flats)
    if not stuck and not _fully_ok(p, flats):
        try:
            flats2 = _donate_the_neck(p, flats)
            flats2 = _delobe_and_donate(flats2)
            flats2, stuck2 = donate_leftovers(p, flats2)
            score2 = _plate_score(p, flats2)
            if score2 > score:
                flats, stuck, score = flats2, stuck2, score2
        except Exception:
            pass
    return score, flats, stuck


def build_flats(poly, k):
    """D-EU-79/80/81/82/83: the production no-core cutter. Every plate is cut by
    every candidate scheme -- `rows x cols` for `rows` from 1 to `min(k, 6)`, at
    every `theta_offset` in `_theta_offset_candidates` (eu21-colour-repair/T02:
    `0.0`/`90.0` first, then long-edge and reflex-bisector directions, capped
    at 12) -- and the single best by
    `_plate_score` is kept (D-EU-83, T04): a single row of `k` columns
    (`rows == 1`) is one candidate among many, never the default that only loses
    when it fails. `rows == 1` additionally tries the swept-boundary variant
    (`_sweep_boundaries`, T03), the depth-layered variant (`cut_layered`,
    D-EU-86/T05b), the radial-sector variant for a courtyard's own ring
    (`cut_radial`, T05d/`FINDING 242`, `None` on a non-ring plate) and the
    per-wing variant for a multi-wing plate (`cut_wingwise`, T05d/`FINDING 242`,
    `None` when `lobes_of` finds fewer than two wings), same as before T04/T05b.
    Every candidate goes through `_finish_candidate`: `_delobe_and_donate` +
    `donate_leftovers`, then -- eu21-colour-repair/T02 fix -- the neck
    donation (`_donate_the_neck`, T03) if that candidate is not yet
    `_fully_ok`, kept only if it improves that candidate's own score. Rescuing
    every candidate, not only the loop's eventual winner, is what makes the
    broadened `theta_offset` search (T02) never regress an already-passing
    plate: a candidate is compared on its own best-achievable outcome, so one
    candidate's high raw pinch never loses to another's low raw pinch when
    the first rescues clean and the second does not."""
    if STAGE == "t01":
        return _cut_nocore_t01(poly, k)

    default = cut_nocore(poly, k, theta_offset=0.0, bx=None)
    if STAGE == "t02":
        return default

    poly_n = _normalize(poly)
    theta, cx, cy, L, W = frame(poly_n)
    theta_offsets = _theta_offset_candidates(poly_n, theta)
    reflex_pts_world = _reflex_points_world(poly_n)  # T03: computed once per plate
    ring_bisect = None  # T04: computed once per plate -- bridge location is a
    if len(poly_n.interiors) > 0 and k in (1, 2):  # property of the ring's own
        try:                                        # geometry, not of theta_offset
            ring_bisect = cut_ring_bisect(poly, k)
        except Exception:
            ring_bisect = None
    best = None
    max_rows = max(1, min(k, MAX_GRID_ROWS))
    # eu21-colour-repair/T02: each candidate is now scored in its own try/except.
    # `theta_offsets` (T02) adds non-cardinal angles the geometry helpers below
    # (lobes_of/_delobe_and_donate in particular) were never exercised against,
    # and a rare GEOS TopologyException on one candidate must discard only that
    # candidate -- exactly the "or be discarded" half of §5.2 -- never the whole
    # plate. Only widens what can be skipped; a candidate that used to complete
    # still completes, so this cannot regress an existing PASS.
    for rows_ in range(1, max_rows + 1):
        for theta_offset in theta_offsets:
            if rows_ == 1:
                try:
                    p1, flats1, stuck1 = cut_nocore(poly, k, theta_offset=theta_offset, bx=None)
                    score1, flats1, stuck1 = _finish_candidate(p1, flats1, stuck1)
                    if best is None or score1 > best[0]:
                        best = (score1, p1, flats1, stuck1, rows_)
                except Exception:
                    pass

                try:
                    theta_full = theta + theta_offset
                    P = to_local(poly_n, theta_full, cx, cy)
                    bx = _sweep_boundaries(P, k) if k >= 2 else None
                    p2, flats2, stuck2 = cut_nocore(poly, k, theta_offset=theta_offset, bx=bx)
                    score2, flats2, stuck2 = _finish_candidate(p2, flats2, stuck2)
                    if best is None or score2 > best[0]:
                        best = (score2, p2, flats2, stuck2, rows_)
                except Exception:
                    pass

                if reflex_pts_world and k >= 2:
                    try:
                        theta_full = theta + theta_offset
                        bx = _sweep_boundaries(to_local(poly_n, theta_full, cx, cy), k)
                        if bx is not None:
                            reflex_xs_local = _reflex_local_xs(reflex_pts_world, theta_full, cx, cy)
                            snapped_xs = _snap_boundaries(bx[1:-1], reflex_xs_local, bx[0], bx[-1])
                            if snapped_xs is not None:
                                bx_snapped = [bx[0]] + snapped_xs + [bx[-1]]
                                p2s, flats2s, stuck2s = cut_nocore(poly, k, theta_offset=theta_offset, bx=bx_snapped)
                                score2s, flats2s, stuck2s = _finish_candidate(p2s, flats2s, stuck2s)
                                if best is None or score2s > best[0]:
                                    best = (score2s, p2s, flats2s, stuck2s, rows_)
                    except Exception:
                        pass

                try:
                    layered = cut_layered(poly, k, theta_offset=theta_offset)
                    if layered is not None:
                        p3, flats3, stuck3 = layered
                        score3, flats3, stuck3 = _finish_candidate(p3, flats3, stuck3)
                        if best is None or score3 > best[0]:
                            best = (score3, p3, flats3, stuck3, rows_)
                except Exception:
                    pass

                try:
                    radial = cut_radial(poly, k, theta_offset=theta_offset)
                    if radial is not None:
                        p4, flats4, stuck4 = radial
                        score4, flats4, stuck4 = _finish_candidate(p4, flats4, stuck4)
                        if best is None or score4 > best[0]:
                            best = (score4, p4, flats4, stuck4, rows_)
                except Exception:
                    pass

                try:
                    wingwise = cut_wingwise(poly, k, theta_offset=theta_offset)
                    if wingwise is not None:
                        p5, flats5, stuck5 = wingwise
                        score5, flats5, stuck5 = _finish_candidate(p5, flats5, stuck5)
                        if best is None or score5 > best[0]:
                            best = (score5, p5, flats5, stuck5, rows_)
                except Exception:
                    pass
            else:
                try:
                    gridr = cut_grid(poly, k, theta_offset=theta_offset, rows=rows_)
                    if gridr is not None:
                        pg, flatsg, stuckg = gridr
                        scoreg, flatsg, stuckg = _finish_candidate(pg, flatsg, stuckg)
                        if best is None or scoreg > best[0]:
                            best = (scoreg, pg, flatsg, stuckg, rows_)
                except Exception:
                    pass

                if reflex_pts_world:
                    try:
                        theta_full = theta + theta_offset
                        reflex_xs_local = _reflex_local_xs(reflex_pts_world, theta_full, cx, cy)
                        gridr_s = cut_grid_snapped(poly, k, theta_offset, rows_, reflex_xs_local)
                        if gridr_s is not None:
                            pgs, flatsgs, stuckgs = gridr_s
                            scoregs, flatsgs, stuckgs = _finish_candidate(pgs, flatsgs, stuckgs)
                            if best is None or scoregs > best[0]:
                                best = (scoregs, pgs, flatsgs, stuckgs, rows_)
                    except Exception:
                        pass

    if ring_bisect is not None:
        try:
            pr, flatsr, stuckr = ring_bisect
            scorer, flatsr, stuckr = _finish_candidate(pr, flatsr, stuckr)
            if best is None or scorer > best[0]:
                best = (scorer, pr, flatsr, stuckr, 1)
        except Exception:
            pass

    score, p_out, flats, stuck, rows_chosen = best
    return p_out, flats, stuck, rows_chosen


# ---------------------------------------------------------------------------
# Checks -- DD-B: C1, C3, C4, C5, C6, C10 survive (no C2/C7/C8/C9/R2); C11 is a
# seventh, added by D-EU-82 (T02) -- no flat may be a ribbon.

# D-EU-82 / D-EU-84 -- T05 ladder, 2026-09-03, run against all 550 plates (TOTAL FAIL = sum of
# C11-only FAILs across the 5 nocore tests at that rung; "-" = plate count when a test has no FAIL):
#   rung 2.5: t1 2  t2 17  t3 3  t4 27  t5 2   -> TOTAL FAIL 51
#   rung 3.0: t1 -  t2  7  t3 2  t4 13  t5 2   -> TOTAL FAIL 24
#   rung 3.5: t1 -  t2  5  t3 1  t4 10  t5 1   -> TOTAL FAIL 17
#   rung 4.0: t1 -  t2  4  t3 -  t4  7  t5 -   -> TOTAL FAIL 11
# No rung reached FAIL 0 (D-EU-84's condition) -- CP-2 STOP, ruled at D-EU-86: no exemption, the
# three group rules are fixed instead (cut_layered below), not the limit. T05b re-ran the SAME
# ladder after that fix, 2026-09-03:
#   rung 2.5: t1 2  t2 10  t3 3  t4 16  t5 2   -> TOTAL FAIL 33
#   rung 3.0: t1 -  t2  4  t3 2  t4  8  t5 2   -> TOTAL FAIL 16
#   rung 3.5: t1 -  t2  3  t3 -  t4  7  t5 1   -> TOTAL FAIL 11
#   rung 4.0: t1 -  t2  1  t3 -  t4  4  t5 -   -> TOTAL FAIL  5
# Still no rung reaches FAIL 0 on all five tests. Residual at 4.0 (5 plate-appearances, all n=12,
# 4 unique buildings): COURTYARD 29659 14.1:1 (byte-identical to the pre-fix value -- cut_layered's
# own safety gates, C6 >= 2.50 m outer-facade contact on EACH half of a merge and an exact 2-piece
# split, never found a legal merge on this one plate; a compliant candidate (grid rows=3/4, aspect
# ~1.8-2.0) is generated but always isolates a flat against the courtyard void with zero outer
# contact, so it fails C6 and never wins), COURTYARD 31169 5.1:1 (unchanged), L_SHAPE
# way/290026256 5.0:1 (unchanged), L_SHAPE way/391279228 6.7:1 (unchanged). Fixed by the
# depth-division candidate (cut_layered, D-EU-86 clause 3): COURTYARD 28125 (was 6.8:1, now
# 3.2:1 PASS), COMPLEX_MULTI_WING way/968439455 (was 4.7:1, now 2.8:1 PASS), COMPLEX_MULTI_WING
# 31312 (was 5.6:1, now 3.8:1 PASS) -- 3 of the original 7 residual buildings are fully resolved,
# with zero regression on C1/C3/C4/C5/C6/C10 across all 550 plates. Per D-EU-86 clause 1's amended
# stop clause, T05b's own ladder is NOT re-run standalone (unchanged by T05c's edits, spot-checked at
# 2.5 -- identical 33 TOTAL FAIL) and execution continues straight into T05c, whose new C10 (D-EU-87,
# `pinch_area`) is scored and re-runs the ladder again below.
#
# D-EU-87/T05c -- C10 rebuilt as a created-pinch-area test (`pinch_area`, r=1.00 m mitre opening,
# tolerance 0.10 m2) and `_donate_the_neck` retargeted at it (was driven by `widest_fit`, which stays
# silent about a narrow strip inside an otherwise-wide flat -- exactly the D-EU-87 defect). Ladder
# re-run in full, 2026-09-03, `--test all` at every rung (TOTAL FAIL = sum of C10-or-C11 FAILs across
# the 5 nocore tests; a plate failing both counts once per test):
#   rung 2.5: t1 3  t2 27  t3 4  t4 44  t5 3   -> TOTAL FAIL 81
#   rung 3.0: t1 2  t2 20  t3 3  t4 34  t5 3   -> TOTAL FAIL 62
#   rung 3.5: t1 1  t2 16  t3 1  t4 25  t5 3   -> TOTAL FAIL 46
#   rung 4.0: t1 1  t2 14  t3 1  t4 22  t5 1   -> TOTAL FAIL 39
# Still no rung reaches FAIL 0. C10 is the dominant residual at every rung (2.5: 54 C10-check-fails;
# 4.0: 36), concentrated in COURTYARD/COMPLEX_MULTI_WING at n=12 -- the same shape family and the same
# worst plate (`COURTYARD 29659`, still single-axis `rows=1`, 34.11 m2 created pinch) as D-EU-86's own
# C11 residual: a courtyard ring whose local band is too thin to divide across its own depth without
# losing C6 contact against the void. Whole-fleet effect of D-EU-87 (baseline 2026-09-02 vs this build,
# `pinch_area` computed on both): total created-pinch 1358.78 m2 -> 134.63 m2 (-90%), plates over the
# 0.10 m2 tolerance 184/550 -> 33/550. The owner's own 4 marked plates: COMPLEX_MULTI_WING 29965
# 4.03->0.005 m2 PASS, COURTYARD 32052 0.00->0.00 m2 PASS, COURTYARD 30127 0.00->0.004 m2 PASS, COURTYARD
# 28754 38.19->1.06 m2 (still FAIL, -97%). Zero regression on C1/C3/C4/C5/C6 across all 550 plates.
# Per T05c's own stop-and-report: STOP, not a freeze -- the constant is left at 4.0 (least-strict rung
# tested, smallest residual) but is NOT adopted, no exemption is invented, the 0.10 m2 tolerance is not
# raised, `widest_fit` is not restored as the verdict, and T06/T07 do not run this session.
#
# D-EU-89 clause 2/T05d -- two new candidates added to `build_flats`'s search, `cut_radial` (a
# courtyard ring cut into equal-area angular sectors from the void's own centroid -- every sector
# spans the ring's full radial depth, so unlike a plate-wide Cartesian band it touches both the void
# and the outer boundary by construction, `FINDING 240`'s own diagnosis of why `cut_layered` could
# never win a ring) and `cut_wingwise` (each of a multi-wing plate's own wings, found by `lobes_of`
# read-only from `02_one_core_per_plate.py`, columned in ITS OWN local frame instead of the plate's one
# shared axis; `None` when `lobes_of` finds fewer than two wings -- confirmed on `COMPLEX_MULTI_WING
# way/968439455` at every neck radius up to 3.0 m, so this specific plate's wings are never separable by
# that test and `cut_wingwise` correctly never fires for it). Neither is preferred by name -- both are
# scored by the unchanged `_plate_score` and win only when they do. Also fixed in the same task
# (`FINDING 243`): `_fix_snap_multipolygons` repairs the rare flat that `_snap_world`'s 0.001 m
# precision grid fragments into a `MultiPolygon` (confirmed cause: a flat can leave rotation as an
# invalid, self-touching Polygon -- a razor-thin bowtie neck from the floating-point rotation itself --
# and `set_precision`'s `valid_output` mode then splits it for real); 17/17 previously-crashing census
# buildings now build `direct`, 0/17 area dropped (`C1` still 100.0 % on every one). Full ladder
# re-run, 2026-09-03, `--test all` at every rung (TOTAL FAIL = sum of C10-or-C11 FAILs across the 5
# nocore tests, same definition as T05c):
#   rung 2.5: t1 4  t2 27  t3 3  t4 44  t5 3   -> TOTAL FAIL 81
#   rung 3.0: t1 3  t2 20  t3 2  t4 34  t5 3   -> TOTAL FAIL 62
#   rung 3.5: t1 2  t2 15  t3 1  t4 24  t5 2   -> TOTAL FAIL 44
#   rung 4.0: t1 2  t2 13  t3 1  t4 20  t5 1   -> TOTAL FAIL 37
# Still no rung reaches FAIL 0 (every rung's own TOTAL FAIL is close to T05c's, 4.0 down 39 -> 37).
# `cut_radial` genuinely wins and measurably helps where it applies -- `COURTYARD 29659`'s own
# created-pinch drops 34.11 -> 5.37 m2 (C10), `COURTYARD 31169` 13.95 -> 2.14 m2 -- but neither drops
# under the 0.10 m2 tolerance, and the sector cut does not by itself square the flat (both plates' own
# `C11` still reads 4.9:1 at k=12, so a candidate that wins on pinch can still fail the aspect gate).
# `COMPLEX_MULTI_WING way/968439455` is unchanged (18.42 m2): its own wings never separate under
# `lobes_of` at any neck radius tried, so `cut_wingwise` never fires and the plate is an honest
# structural residual, not a missed candidate. Regression on C1/C3/C4/C5/C6: 0/550 (matched by
# `(group, building_id, drawn_per_floor)` against the pre-T05d on-disk JSONs). Per `D-EU-89` clause 2
# (ruled ahead of this task, `STATE_european_locations_v5.md` §4): since no rung reaches `FAIL 0` after
# this genuine second repair round, the constant is set to the STRICTEST rung, 2.5 -- never the
# least-failing one -- marked NOT calibrated (`D-EU-84`'s own condition was never met), and every
# residual plate at 2.5 (81 plate-appearances) is delivered as an honest `FAIL`, never an invented
# exemption. T05d's own stop-and-report (director-amended): the executor stops here and reports; T06
# does not run this session.
MAX_FLAT_ASPECT = 2.5

# D-EU-107 (`FINDING 244`, plan `eu-plan-homogeneity-2026-09-07`, CP-1 pinned
# 2026-09-07): C12, the area-balance gate. `spread = min(flat area) / max(flat
# area)` (same field/formula `run_checks` already stored). PASS at spread >=
# 0.50 (max/min <= 2.0 : 1, `FINDING 244`'s own number). Waived at k <= 1,
# same exemption and same reason C11 gets (D-EU-93): nothing was cut, so there
# is nothing to compare. C12 is reported alongside the frozen seven checks but
# never folds into `rec["verdict"]` -- hard rule 1/3 of the plan freeze
# C1/C3/C4/C5/C6/C10/C11's own pass/fail gate; C12 is additive, measured,
# never merged into it. Extracted (D-EU-95), not re-implemented, from
# `scripts/eu21/07_nocore_tests.py`, T03 of the same plan.
MIN_SPREAD = 0.50


def flat_aspect(f):
    """D-EU-82: long/short of the flat's own minimum rotated bounding rectangle.
    A degenerate (near-zero short side) rectangle scores 99.0, so it always fails."""
    if f is None or f.is_empty:
        return 99.0
    c = list(f.minimum_rotated_rectangle.exterior.coords)
    s = sorted(math.dist(c[i], c[i + 1]) for i in range(4))
    return (s[3] / s[0]) if s[0] > 0 else 99.0


def rings_of(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, MultiPolygon):
        g = max(g.geoms, key=lambda p: p.area)
    return [list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]


def _opening_lost(g, r=1.00):
    """D-EU-87 (FINDING 241): the part of `g` a mitre-joined r-radius opening
    (erode then dilate back) fails to return -- by construction, the part of
    `g` narrower than 2r. Guards the empty-erosion case: if the erosion is
    already empty, the whole of `g` is narrower than 2r and is returned as lost.
    Never lets GEOS raise (`CUT_GEOSException`, same family as `_safe_union`/
    `_safe_precision` elsewhere in this file): a `TopologyException` out of the
    mitre-joined buffer pair is retried once on `g.buffer(0)`-cleaned geometry;
    if that also raises, `g` itself is returned -- the whole flat counts as
    lost, the conservative answer (it can only make `C10` fail, never pass a
    pinch it could not actually measure), never a crash that takes the whole
    plate's `_plate_score` down with it."""
    if g is None or g.is_empty:
        return g
    try:
        eroded = g.buffer(-r, join_style=2, mitre_limit=5.0)
        if eroded.is_empty:
            return g
        opened = eroded.buffer(r, join_style=2, mitre_limit=5.0)
        return g.difference(opened)
    except Exception:
        pass
    try:
        gg = g.buffer(0)
        eroded = gg.buffer(-r, join_style=2, mitre_limit=5.0)
        if eroded.is_empty:
            return gg
        opened = eroded.buffer(r, join_style=2, mitre_limit=5.0)
        return gg.difference(opened)
    except Exception:
        return g


def _pinch_geom(f, plate):
    """D-EU-87 (FINDING 241): the geometry of flat `f` narrower than 2.00 m
    that the CUT created, not the area inherited from the plate's own
    footprint. `_opening_lost(f)` is every part of f narrower than 2 m;
    `_opening_lost(plate)` is the same test run on the plate footprint, i.e.
    the footprint's own acute tips/slots that no cut can remove. Only the part
    of f's lost area that lies OUTSIDE the plate's own lost area is charged to
    the cut."""
    if f is None or f.is_empty or f.area <= 0:
        return None
    lost = _opening_lost(f)
    if lost is None or lost.is_empty:
        return None
    plate_lost = _opening_lost(plate)
    if plate_lost is None or plate_lost.is_empty:
        return lost
    try:
        return lost.difference(plate_lost)
    except Exception:
        try:
            return lost.buffer(0).difference(plate_lost.buffer(0))
        except Exception:
            return lost


def pinch_area(f, plate):
    """D-EU-87 (FINDING 241): the area of `_pinch_geom(f, plate)` -- the part
    of flat `f` narrower than 2.00 m that the cut, not the footprint, created."""
    g = _pinch_geom(f, plate)
    return 0.0 if g is None or g.is_empty else g.area


def run_checks(rec, flats, poly):
    checks = {}
    n = rec["drawn_per_floor"]
    live = [f for f in flats if not f.is_empty]

    cov = (sum(f.area for f in live) / poly.area) if poly.area else 0.0
    checks["C1"] = {"pass": 0.999 <= cov <= 1.001, "show": f"{cov * 100:.1f} %"}

    checks["C3"] = {"pass": len(live) == n, "show": f"{len(live)}/{n}"}

    lobed = sum(1 for f in live if lobes_of(f) is not None)
    rooms_ok = lobed == 0
    worst = 0.0
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            ov = live[i].intersection(live[j]).area
            if ov > worst:
                worst = ov
    c4_show = (f"{worst:.2f} m\u00b2" if rooms_ok
               else (f"{lobed} lobed" if worst < 0.02 else f"{lobed} lobed, {worst:.2f} m\u00b2"))
    checks["C4"] = {"pass": rooms_ok and worst < 0.02, "show": c4_show}

    no_holes = all(len(f.interiors) == 0 for f in live)
    reps = [f.representative_point() for f in live]
    no_contain = True
    for i, fi in enumerate(live):
        for j, pt in enumerate(reps):
            if i != j and fi.contains(pt):
                no_contain = False
    pts_list = [len(f.exterior.coords) - 1 for f in live]
    max_pts = max(pts_list) if pts_list else 0
    checks["C5"] = {"pass": no_holes and no_contain and max_pts <= 40, "show": str(max_pts)}

    contacts = [sbuf(f, 0.05).intersection(poly.exterior).length for f in live]
    min_contact = min(contacts) if contacts else 0.0
    checks["C6"] = {"pass": min_contact >= 2.50, "show": f"{min_contact:.2f} m"}

    pinch_total = sum(pinch_area(f, poly) for f in live)
    checks["C10"] = {"pass": pinch_total <= 0.10, "show": f"{pinch_total:.2f} m²"}

    max_aspect = max((flat_aspect(f) for f in live), default=99.0)
    if len(live) <= 1:
        checks["C11"] = {"pass": True, "show": f"{max_aspect:.1f} : 1 (k=1, D-EU-93)"}
    else:
        checks["C11"] = {"pass": max_aspect <= MAX_FLAT_ASPECT, "show": f"{max_aspect:.1f} : 1"}

    areas = [f.area for f in live]
    spread = round((min(areas) / max(areas)) if areas and max(areas) > 0 else 0.0, 4)
    if len(live) <= 1:
        checks["C12"] = {"pass": True, "show": f"{spread:.4f} (k=1, D-EU-93 exemption)"}
    else:
        checks["C12"] = {"pass": spread >= MIN_SPREAD, "show": f"{spread:.4f}"}

    rec["checks"] = checks
    rec["spread"] = spread
    rec["verdict"] = "PASS" if all(checks[c]["pass"] for c in ("C1", "C3", "C4", "C5", "C6", "C10", "C11")) else "FAIL"


def cut_storey_nocore(footprint, dwelling_count):
    """Return (plate, flats, checks, verdict) for one storey. Reproduces the census's
    own preprocessing (FINDING 246): `usable_polygon` repair, then the centroid
    translated to the origin before cutting -- `set_precision`'s millimetre grid does
    not land on the same bits at a raw UTM footprint's ~4.5e6 m coordinates. Checks are
    scored in that same centred frame the census itself scores them in (translation-
    invariant, but bit-identical to `_r5` this way); the returned plate and every flat
    are translated back to the caller's own frame by (+cx, +cy) before returning.
    Never raises for geometry reasons -- a cutter exception is re-raised to the caller
    unchanged, exactly as build_plate:1668 lets it surface."""
    usable = usable_polygon(footprint)
    if usable is None:
        raise ValueError("footprint not a simple polygon after buffer(0) repair")
    cx, cy = usable.centroid.x, usable.centroid.y
    centred_poly = translate(usable, -cx, -cy)
    result = build_flats(centred_poly, dwelling_count)
    if len(result) == 4:
        poly, flats, stuck, rows_chosen = result
    else:
        poly, flats, stuck = result
        rows_chosen = 1
    live = [f for f in flats if not f.is_empty]
    rec = {"drawn_per_floor": dwelling_count}
    run_checks(rec, live, poly)
    poly_out = translate(poly, cx, cy)
    live_out = [translate(f, cx, cy) for f in live]
    return poly_out, live_out, rec["checks"], rec["verdict"]
