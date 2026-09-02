"""Document-only pass over the plan JSON that feeds the group rules HTML.

One core per plate: the interior stair core is kept, every other circulation
piece and every uncovered scrap is absorbed into the flat it shares the most
wall with, and fragments are merged back down to the drawn flat count.
Reads and rewrites eu21_group_plans.json. No engine code is touched.
"""
import json
import math
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import pathlib
SRC = pathlib.Path(__file__).with_name("group_plans.json")
EPS = 0.02
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


def fuse(geoms):
    """Weld a set of zones into one shape. unary_union() over shapes that share an exact
    edge can drop one of them whole at GEOS precision and still report the result valid --
    a flat that simply vanishes from the plate, or a pocket that replaces the flat it was
    being welded onto. Add them one at a time and check the area after each; try the
    pairwise union as a second route, and refuse rather than return a wrong shape."""
    live = [g for g in geoms if g is not None and not g.is_empty]
    if not live:
        return Polygon()
    out = live[0]
    for g in live[1:]:
        want = out.area + g.area - out.intersection(g).area
        cand = ok(unary_union([out, g]))
        if cand.is_empty or abs(cand.area - want) > 0.01:
            cand = ok(out.union(g))
        if cand.is_empty or abs(cand.area - want) > 0.01:
            return None
        out = cand
    return out


def uncovered(fp, shapes):
    """What none of `shapes` covers. Taken one difference at a time: unary_union() over a
    set of zones that share exact edges can silently drop one of them at GEOS precision,
    and the whole missing zone then comes back as a gap and is welded onto its neighbour."""
    out = fp
    for g in shapes:
        if g is not None and not g.is_empty:
            out = out.difference(g)
    return out


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


NEEDLE_COS = 0.9995
NEEDLE_AREA = 0.25
FLAT_TOL = 0.01


def _ring_area(ring):
    n = len(ring)
    return 0.5 * abs(sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
                         for i in range(n)))


def _deneedle_ring(ring):
    """Drop every tip of an out-and-back needle: a vertex whose two edges leave it in the
    same direction, so the boundary runs out along a line and straight back over itself.
    Judged one vertex at a time -- a needle that is a hair off exact carries a little area
    with it, and refusing the whole ring over that is what leaves the needle in place."""
    ring = list(ring)
    changed = True
    while changed and len(ring) > 3:
        changed = False
        n = len(ring)
        for i in range(n):
            a, b, c = ring[i - 1], ring[i], ring[(i + 1) % n]
            la = math.dist(a, b)
            lc = math.dist(c, b)
            if la < 1e-9 or lc < 1e-9:
                ring = ring[:i] + ring[i + 1:]
                changed = True
                break
            # a point that sits on the line between its neighbours carries no information
            # and is not free: every offset-and-clip pass adds one more of them to the same
            # wall, and after a few passes the wall is a list of hundreds of vertices.
            cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
            if math.dist(a, c) > 1e-9 and cross / math.dist(a, c) < FLAT_TOL:
                ring = ring[:i] + ring[i + 1:]
                changed = True
                break
            cos = ((a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1])) / (la * lc)
            if cos <= NEEDLE_COS:
                continue
            trial = ring[:i] + ring[i + 1:]
            if abs(_ring_area(trial) - _ring_area(ring)) < NEEDLE_AREA:
                ring = trial
                changed = True
                break
    return ring


def deneedle(g):
    """A weld of two pieces that touch along a line, or a gap closed over a zero-width
    crack, leaves the ring travelling out and back along the same line: no area to speak
    of, but a real pair of edges in the drawing and a spike that reaches metres into the
    neighbour, which is enough to make a straight party wall read as a bend. Remove them
    exactly -- by dropping the tip vertex -- rather than by an erode/dilate that would move
    the shape. What little area the tip carried is left uncovered here and handed straight
    back by close_gaps(), to the zone that actually holds the wall it lies along."""
    if g is None or g.is_empty or g.geom_type != "Polygon":
        return g
    try:
        out = Polygon(_deneedle_ring(list(g.exterior.coords)[:-1]),
                      [_deneedle_ring(list(h.coords)[:-1]) for h in g.interiors])
        if out.is_valid and not out.is_empty:
            return out
    except Exception:
        pass
    return g


def join(a, b):
    """Weld two zones that meet along a wall. Where each was cut separately their two
    boundaries can differ by a fraction of a millimetre, and unary_union() then hands back
    two pieces that merely touch -- the weld silently drops one of them and the area leaves
    the plate. A morphological close at 2 cm bridges that crack without moving a real
    corner, because both offsets use square joins."""
    m = fuse([a, b])
    if m is not None and m.geom_type == "Polygon":
        return m
    m = ok(unary_union([a, b]))
    try:
        c = biggest(sbuf(sbuf(m, 0.02), -0.02), Polygon())
    except Exception:
        c = Polygon()
    if not c.is_empty and c.area >= m.area - 0.05:
        # the close leaves a short fan of points where it bridged; drop them here, or a
        # pocket shared out step by step arrives carrying one fan per step.
        return deneedle(c)
    return biggest(m, a)


SPIKE_R = 0.05
SPIKE_AREA = 0.6


def despike(g):
    """Cut off filaments: a zone that ran out along one line and back along another a few
    centimetres away is not a needle with a tip to drop -- the two edges are not parallel
    enough for that -- but it is still a spike of no width reaching across the plate. A
    morphological open at SPIKE_R removes anything under 2*SPIKE_R wide and leaves every
    real corner where it was, because both offsets use square joins. Refused if it would
    cost real area, which would mean the shape itself is that thin."""
    if g is None or g.is_empty or g.geom_type != "Polygon":
        return g
    o = biggest(sbuf(sbuf(g, -SPIKE_R), SPIKE_R).intersection(g), g)
    return o if not o.is_empty and g.area - o.area < SPIKE_AREA else g


def rings(g):
    return [list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]


def pick_core(fp, circs):
    """The core is the interior piece: it does not run along the outer wall."""
    live = [c for c in circs if c.area >= 0.5]
    if not live:
        return None, list(circs)
    scored = sorted(
        live,
        key=lambda c: -(fp.boundary.distance(c.centroid)
                        - 0.5 * c.buffer(0.05).intersection(fp.exterior).length),
    )
    return scored[0], [c for c in circs if c is not scored[0]]


def absorb(fp, flats, scraps, core):
    """Each scrap joins the closest flat. A scrap can border more than one flat along
    its length (a margin running past a core, say) so it is grown into flat-by-flat in
    small steps rather than handed whole to a single winner: whichever flat's wavefront
    reaches a given point first claims it, splitting the scrap at the natural line
    equidistant between neighbours instead of at an arbitrary share-count tie-break."""
    remaining = unary_union([p for p in scraps if p.area > 1e-6]) if scraps else Polygon()
    if core is not None:
        remaining = remaining.difference(core)
    grown = list(flats)
    buckets = [[f] for f in flats]
    step, guard = 0.20, 0
    while not remaining.is_empty and remaining.area > 1e-6 and guard < 400:
        guard += 1
        progressed = False
        for i in range(len(grown)):
            if remaining.is_empty:
                break
            claim = sbuf(grown[i], step).intersection(remaining)
            if claim.is_empty or claim.area <= 1e-9:
                continue
            buckets[i].append(claim)
            grown[i] = unary_union([grown[i], claim]).buffer(0)
            remaining = remaining.difference(claim)
            progressed = True
        if not progressed:
            step *= 1.5
    if not remaining.is_empty and remaining.area > 1e-6:
        for p in parts(remaining):
            i = min(range(len(flats)), key=lambda k: flats[k].distance(p))
            buckets[i].append(p)
    claimed = core if core is not None else Polygon()
    out = []
    for b in buckets:
        m = unary_union([b[0]] + [sbuf(x, EPS) for x in b[1:]])
        m = m.intersection(fp).difference(claimed)
        m = weld(m, b[0])
        out.append(m)
        claimed = claimed.union(m)
    return out


CORE_GROWTH_CAP = 1.35
RIBBON_MEAN_W = 0.90
MRR_GROWTH = 2.5


def fold_narrow_to_core(fp, flats, core, r=0.6, budget=None):
    """A flat pocket narrower than 2r that touches the core is circulation-shaped, not
    room-shaped: fold it into the core instead of leaving it as a sliver on the flat.

    Three tests, not one. Narrow is not enough on its own -- the step at the end of a
    corridor is also narrow, and folding it draws the corridor with a wide head, which is
    neither the rule nor a plan. The pocket must also be a *ribbon along* the core: its
    mean width measured over the wall it shares with the core (area / shared length) under
    RIBBON_MEAN_W. And it must not make the core a wider band: a ribbon down one side barely
    changes the smallest rectangle the core fits in, while a head across one end widens that
    rectangle over the corridor's whole length -- tens of square metres of box for one square
    metre of pocket. Both are narrow; only the first is circulation. The area cap is left in
    as a backstop against a runaway, not as the discriminator."""
    if core is None:
        return flats, core
    ceiling = (budget if budget is not None else core.area) * CORE_GROWTH_CAP
    out = []
    for f in flats:
        body = sbuf(sbuf(f, -r), r).intersection(f)
        sliver = f.difference(sbuf(body, 1e-6))
        keep = f
        for p in parts(sliver):
            if p.area < 1e-6 or p.area > 0.5 * f.area or p.distance(core) > 0.05:
                continue
            sl = _shared_len(p, core)
            if sl < 1.0 or p.area / sl > RIBBON_MEAN_W:
                continue
            box = core.minimum_rotated_rectangle.area
            if unary_union([core, p]).minimum_rotated_rectangle.area - box > MRR_GROWTH * p.area:
                continue
            # p can sit a hair off the core (rounding from the growth pass in absorb()).
            # A morphological close (dilate then erode by the same radius) bridges that
            # gap without permanently growing the shape into whatever else is nearby --
            # unlike buffering p outward, which would leak into the neighbour past it.
            # Square joins keep the bridged edge one straight cut instead of a rounded tab.
            grown = weld(sbuf(sbuf(unary_union([core, p]), 0.03), -0.03).intersection(fp), core)
            if grown.area > ceiling:
                continue
            core = grown
            keep = keep.difference(p)
        out.append(weld(keep.intersection(fp), keep))
    return out, core


STRAIGHTEN_TOL = 0.20
WALL_BAND = 0.35


AREA_GUARD_FRAC = 0.01


def straighten(fp, flats, core):
    """absorb() grows each flat in 0.20 m wavefront steps, so the boundary it leaves
    between two flats is a staircase of ~0.2 m segments approximating what should be one
    straight cut. Simplify each flat (largest first) and re-clip against what earlier
    flats already claimed, so neighbours stay disjoint; close_gaps() mops up the sliver
    gaps this leaves along the old staircase. Simplifying can overreach on a shape built
    from many real, closely-spaced vertices (the courtyard gallery ring's arc-like void,
    say) -- guarded per flat/core against its own pre-straighten area, so one shape falling
    back to its unsimplified (but still re-clipped) form never costs its straightened
    neighbours their fix."""
    # square joins: a round band would hand every zone a fan of arc vertices along the
    # wall it restores, which is a staircase by another name.
    band = fp.exterior.buffer(WALL_BAND, **SQUARE)
    core2 = None
    if core is not None:
        cand = weld(core.simplify(STRAIGHTEN_TOL, preserve_topology=True).intersection(fp), core)
        cand = weld(ok(unary_union([cand, core.intersection(band)])).intersection(fp), cand)
        # guarded both ways: a core that grows while being straightened is a corridor
        # sprouting a head, which is exactly the artefact this pass exists to remove.
        core2 = core if abs(cand.area - core.area) > core.area * AREA_GUARD_FRAC else cand
    claimed = core2 if core2 is not None else Polygon()
    order = sorted(range(len(flats)), key=lambda i: -flats[i].area)
    out = [None] * len(flats)
    for i in order:
        cand = flats[i].simplify(STRAIGHTEN_TOL, preserve_topology=True)
        cand = weld(ok(unary_union([cand, flats[i].intersection(band)])), flats[i])
        cand = weld(ok(cand).difference(claimed).intersection(fp), Polygon())
        if cand.area < flats[i].area * (1 - AREA_GUARD_FRAC):
            cand = weld(ok(flats[i]).difference(claimed).intersection(fp), flats[i])
        out[i] = cand
        claimed = claimed.union(cand)
    return out, core2


KINK_SEG_MAX = 0.5
KINK_AREA_TOL = 0.3


def dekink(poly, wall=None):
    """simplify()'s Douglas-Peucker only drops a point when it is close to the chord
    between its *distant* surviving neighbours -- a short run of a few centimetre-scale
    edges tucked partway along a genuine long wall (left by absorb()'s wavefront growth
    or fold_narrow_to_core()'s dilate/erode) sits far from that chord and survives
    untouched, which is what still reads as a little staircase in the drawing. Remove
    points one at a time instead: any point with at least one edge shorter than
    KINK_SEG_MAX is dropped if doing so changes the polygon's own area by less than
    KINK_AREA_TOL m2 -- a bound on a single point, not a tolerance on the whole shape, so
    it cannot eat a real corner the way a larger simplify() tolerance can.

    Vertices on the outer wall are skipped when `wall` is given: the wall is surveyed, its
    short edges are the building, and dropping one both falsifies the plan and opens a
    wedge along the wall that close_gaps() has to weld back as a hairline needle."""
    if poly.is_empty or poly.geom_type != "Polygon":
        return poly
    ring = list(poly.exterior.coords)[:-1]
    holes = [list(h.coords) for h in poly.interiors]
    changed = True
    guard = 0
    while changed and guard < len(ring) + 5:
        changed = False
        guard += 1
        n = len(ring)
        if n < 4:
            break
        i = 0
        while i < n:
            a, b, c = ring[i - 1], ring[i], ring[(i + 1) % n]
            if wall is not None and wall.contains(Point(b)):
                i += 1
                continue
            if ((ring[i - 1][0] - b[0]) ** 2 + (ring[i - 1][1] - b[1]) ** 2) ** 0.5 < KINK_SEG_MAX or \
               ((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2) ** 0.5 < KINK_SEG_MAX:
                trial = ring[:i] + ring[i + 1:]
                try:
                    tp = Polygon(trial, holes)
                    if tp.is_valid and abs(tp.area - poly.area) < KINK_AREA_TOL:
                        ring = trial
                        poly = tp
                        changed = True
                        n = len(ring)
                        continue
                except Exception:
                    pass
            i += 1
    return poly


def _shared_len(a, b):
    """Length of the wall two shapes hold in common."""
    return sbuf(a, 0.06).intersection(sbuf(b, 0.06)).length / 2


def _touch_len(a, b):
    """Same, but only where the two actually meet: the 0.06 m version bridges a hairline
    third zone lying between them and reports a wall that is not there."""
    return sbuf(a, 0.001).intersection(sbuf(b, 0.001)).length / 2


def _share(pocket, flats, idxs):
    """Grow the given flats into a pocket in small steps until it is gone, each point
    going to whichever flat's wavefront reaches it first -- the same split absorb() uses.

    A pocket handed whole to its nearest flat is what puts a hole in a zone: the seam left
    around an interior core is one connected ring, and the flat that takes it closes around
    the core through a hairline neck. Split, each flat gets only the side of the ring it
    already faces and no zone encloses another. The wavefront runs on a working copy and
    each flat is welded once at the end -- welding at every step would hand it one bridging
    fan of points per step."""
    rest = pocket
    grown = {k: flats[k] for k in idxs}
    step, guard = 0.05, 0
    while not rest.is_empty and rest.area > 1e-9 and guard < 200:
        guard += 1
        moved = False
        for k in idxs:
            try:
                claim = sbuf(grown[k], step).intersection(rest)
                if claim.is_empty or claim.area <= 1e-12:
                    continue
                grown[k] = ok(unary_union([grown[k], claim]))
                rest = ok(rest.difference(claim))
            except Exception:
                continue
            moved = True
        if not moved:
            step *= 1.5
    for k in idxs:
        if grown[k].area <= flats[k].area + 1e-9:
            continue
        merged = join(flats[k], grown[k])
        if merged.geom_type == "Polygon" and merged.area >= flats[k].area - 0.01:
            flats[k] = merged
    return flats


def close_gaps(fp, flats, core):
    """Snap any leftover sliver of numerical seam to whichever neighbour it borders,
    so plate coverage never reads short over a rounding crack.

    A leftover pocket belongs to a flat, never to the core: the core is a stair or a
    1.80 m corridor sized by the rule, and welding whatever the cut left nearest to it
    draws a corridor with a wide head instead of the band the sheet claims. A pocket that
    runs past more than one flat is split between them rather than handed to one."""
    gap = uncovered(fp, flats + ([core] if core else []))
    for p in parts(gap):
        if p.area < 1e-9:
            continue
        near = [k for k in range(len(flats)) if flats[k].distance(p) < 0.05]
        if len(near) > 1:
            flats = _share(p, flats, near)
            continue
        i = near[0] if near else min(range(len(flats)), key=lambda k: flats[k].distance(p))
        flats[i] = join(flats[i], p)
    return flats, core


def merge_to(flats, target):
    """Weld fragments together until the drawing shows the flat count it claims."""
    while len(flats) > target:
        i = min(range(len(flats)), key=lambda k: flats[k].area)
        j, best = None, 0.05
        for k in range(len(flats)):
            if k == i:
                continue
            w = sbuf(flats[i], EPS).intersection(flats[k]).area
            if w > best:
                j, best = k, w
        if j is None:
            break
        m = biggest(sbuf(unary_union([sbuf(flats[i], EPS), flats[j]]), -EPS / 2), flats[j])
        flats = [f for k, f in enumerate(flats) if k not in (i, j)] + [m]
    return flats


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


def unsnake(fp, flats, core):
    """A thermal zone is one room, not a room plus a corridor-thin tail reaching across
    the plate. Where a flat comes out of the cut as two lobes joined by a neck, the
    smaller lobe is handed to the neighbouring flat it shares the most wall with -- the
    closest zone -- rather than left dangling on its own."""
    for _ in range(4):
        moved = False
        for i in range(len(flats)):
            found = lobes_of(flats[i])
            if not found:
                continue
            for lobe in found[1:]:
                if lobe.area < LOBE_MIN_M2:
                    continue
                best, share = None, 0.02
                for k in range(len(flats)):
                    if k == i:
                        continue
                    w = sbuf(lobe, 0.05).intersection(flats[k]).area
                    if w > share:
                        best, share = k, w
                if best is None:
                    continue
                flats[i] = weld(flats[i].difference(lobe), flats[i])
                flats[best] = weld(unary_union([flats[best], lobe]), flats[best])
                moved = True
        if not moved:
            break
    return flats, core


CUT_MIN_SPAN = 1.5
CUT_MAX_BEND = 2.5
CUT_MAX_SWING = 0.20


def _coords(g):
    """Every vertex of a boundary piece, whatever mix of lines a difference() returned."""
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return list(g.coords)
    if g.geom_type == "Point":
        return [(g.x, g.y)]
    out = []
    for q in getattr(g, "geoms", []):
        out += _coords(q)
    return out


def _span(pts):
    """The two vertices furthest apart -- for a party wall those are its two ends, where
    it meets the outer wall, whether or not the core splits it into two pieces on the way."""
    best, pair = 0.0, None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.dist(pts[i], pts[j])
            if d > best:
                best, pair = d, (pts[i], pts[j])
    return best, pair


def _side(p0, u, q):
    return (q[0] - p0[0]) * u[1] - (q[1] - p0[1]) * u[0]


def _halfplane(p0, u, reach):
    n = (u[1], -u[0])
    a = (p0[0] - u[0] * reach, p0[1] - u[1] * reach)
    b = (p0[0] + u[0] * reach, p0[1] + u[1] * reach)
    return Polygon([a, b,
                    (b[0] + n[0] * reach, b[1] + n[1] * reach),
                    (a[0] + n[0] * reach, a[1] + n[1] * reach)])


def _wall_pts(a, b):
    return _coords(a.exterior.intersection(sbuf(b, 0.05)))


def _line_of(pts):
    """The line a run of wall points lies on: through its two furthest-apart vertices."""
    span, ends = _span(pts)
    if span < 1e-9:
        return None
    p0 = ends[0]
    return span, p0, ((ends[1][0] - p0[0]) / span, (ends[1][1] - p0[1]) / span)


def straight_cuts(fp, flats, core):
    """The wall between two flats is a design decision, and a designer draws it as one
    straight line from outer wall to outer wall. absorb() instead grows it in 0.20 m
    wavefront steps, so what comes out is that line with a dogleg or two left where the
    two wavefronts met -- the extra edges visible in the sheets.

    Re-cut by the straight line through the ends of the wall, taking only the union of the
    flats concerned so nothing else on the plate can move and an interior core is stepped
    around rather than through. One flat at a time, and all its neighbours *together* when
    their walls with it lie on one line: a flat facing a row of others is a T-junction, and
    cutting each pair on its own line is exactly what leaves the two halves of that wall at
    slightly different heights -- the step still visible beside the core. What the cut moves
    to the far side is shared out between the neighbours by wavefront, never handed whole.

    Refused, and the drawn wall kept, when the wall is not straight to begin with (a genuine
    bend around a wing, CUT_MAX_BEND), when it is too short to define a direction
    (CUT_MIN_SPAN), when the straight version would move more than CUT_MAX_SWING of the
    smallest flat concerned, or when the pieces no longer add up."""
    reach = 3 * max(fp.bounds[2] - fp.bounds[0], fp.bounds[3] - fp.bounds[1])
    order = sorted(range(len(flats)), key=lambda i: -flats[i].area)
    for i in order:
        nb = []
        for j in range(len(flats)):
            if j == i:
                continue
            pts = _wall_pts(flats[i], flats[j])
            L = _line_of(pts) if len(pts) >= 2 else None
            if L is None or L[0] < CUT_MIN_SPAN:
                continue
            nb.append((j, pts))
        if not nb:
            continue
        for grp in ([nb] if len(nb) > 1 else []) + [[x] for x in nb]:
            js = [j for j, _ in grp]
            pts = [q for _, ps in grp for q in ps]
            L = _line_of(pts)
            if L is None or L[0] < CUT_MIN_SPAN:
                continue
            span, p0, u = L
            if max(abs(_side(p0, u, q)) for q in pts) > CUT_MAX_BEND:
                continue
            si = _side(p0, u, flats[i].representative_point().coords[0])
            if si == 0 or any(_side(p0, u, flats[j].representative_point().coords[0]) * si >= 0
                              for j in js):
                continue
            hp = _halfplane(p0, u, reach) if si > 0 else _halfplane(p0, (-u[0], -u[1]), reach)
            both = fuse([flats[i]] + [flats[j] for j in js])
            if both is None:
                continue
            swing = CUT_MAX_SWING * min([flats[i].area] + [flats[j].area for j in js])
            ci = weld(both.intersection(hp), flats[i])
            if ci.is_empty or abs(ci.area - flats[i].area) > swing:
                continue
            trial, bad = list(flats), False
            for j in js:
                c = weld(flats[j].difference(hp), flats[j])
                if c.is_empty or abs(c.area - flats[j].area) > swing:
                    bad = True
                    break
                trial[j] = c
            if bad:
                continue
            trial[i] = ci
            left = both.difference(hp)
            for j in js:
                left = left.difference(trial[j])
            for pk in parts(left):
                if pk.area > 1e-9:
                    trial = _share(pk, trial, js)
            if abs(sum(trial[k].area for k in [i] + js) - both.area) > max(0.10, 0.005 * both.area):
                continue
            flats = trial
            break
    return close_gaps(fp, flats, core)


def tidy(fp, flats, core):
    """Straighten, de-kink and gap-close one plate. Run after every pass that grows a
    shape by wavefront, because that growth is what leaves the ~0.2 m staircase on a
    boundary that should be one straight cut."""
    pre_flats, pre_core = flats, core
    pre_cov = (sum(f.area for f in pre_flats) + (pre_core.area if pre_core else 0.0)) / fp.area
    s_flats, s_core = straighten(fp, pre_flats, pre_core)
    s_flats = [deneedle(despike(f)) for f in s_flats]
    s_core = deneedle(s_core)
    s_flats, s_core = close_gaps(fp, s_flats, s_core)
    s_cov = (sum(f.area for f in s_flats) + (s_core.area if s_core else 0.0)) / fp.area
    if s_cov < pre_cov - 0.003:
        # straighten()'s per-flat simplify can overreach on a shape with many real,
        # closely-spaced vertices (the courtyard gallery ring, say) and cut away area
        # close_gaps() cannot fully recover -- when that happens, keep the unstraightened
        # (but still gap-closed) plate rather than trade a cosmetic fix for lost coverage.
        flats, core = close_gaps(fp, pre_flats, pre_core)
    else:
        flats, core = s_flats, s_core
    wall = fp.exterior.buffer(0.05, **SQUARE)
    for _ in range(2):
        # dekink() on each shape by itself would let a flat and the core disagree on
        # where their shared corner sits (each drops a different one of the two nearby
        # points), leaving a sliver that close_gaps() has to weld onto one side with a
        # pile of extra vertices -- the same shared-boundary trap straighten() avoids by
        # re-deriving each flat as fp minus what is already claimed. Do the same here:
        # dekink the core once, then dekink and re-clip each flat against it in turn.
        if core is not None:
            cand = dekink(core, wall)
            core = core if abs(cand.area - core.area) > core.area * AREA_GUARD_FRAC else cand
        claimed = core if core is not None else Polygon()
        order = sorted(range(len(flats)), key=lambda i: -flats[i].area)
        out = [None] * len(flats)
        for i in order:
            s = weld(ok(dekink(flats[i], wall)).difference(claimed).intersection(fp), Polygon())
            s = dekink(s, wall)
            out[i] = deneedle(despike(s))
            claimed = claimed.union(out[i])
        flats = out
        flats, core = close_gaps(fp, flats, core)
    return flats, core


RING_SLICE_W = 1.20


def _open_ring(z, fp, others):
    """Cut one zone open along a radial line so it no longer encircles a void.

    Candidates are taken from the corners of the void's own box: first the wedge between
    two neighbouring corners, which hands over one whole side of the ring -- a room -- and
    only then the thin slice through a single corner, which hands over a finger. A cut is
    only usable if it leaves the zone in one hole-free piece *and* reaches a neighbour that
    can take it; a bite out of the middle of the ring, walled in by the ring itself, would
    leave the plate short instead. Returns (rest, cut) or None."""
    if z is None or z.is_empty or not z.interiors:
        return None
    reach = 3 * max(fp.bounds[2] - fp.bounds[0], fp.bounds[3] - fp.bounds[1])
    h = Polygon(z.interiors[0])
    c = h.centroid.coords[0]
    box = list(h.minimum_rotated_rectangle.exterior.coords)[:-1]

    def far(corner):
        d = (corner[0] - c[0], corner[1] - c[1])
        n = math.hypot(*d)
        return None if n < 1e-9 else (d[0] / n, d[1] / n)

    cands = []
    for k in range(len(box)):
        u0, u1 = far(box[k]), far(box[(k + 1) % len(box)])
        if u0 and u1:
            cands.append((0, Polygon([c, (c[0] + u0[0] * reach, c[1] + u0[1] * reach),
                                      (c[0] + u1[0] * reach, c[1] + u1[1] * reach)])))
    for corner in box:
        u = far(corner)
        if not u:
            continue
        w = (-u[1] * RING_SLICE_W / 2, u[0] * RING_SLICE_W / 2)
        cands.append((1, Polygon([(c[0] + w[0], c[1] + w[1]),
                                  (c[0] + u[0] * reach + w[0], c[1] + u[1] * reach + w[1]),
                                  (c[0] + u[0] * reach - w[0], c[1] + u[1] * reach - w[1]),
                                  (c[0] - w[0], c[1] - w[1])])))
    best = None
    for rank, sl in cands:
        cut = z.intersection(sl)
        rest = parts(z.difference(sl))
        if cut.is_empty or len(rest) != 1 or rest[0].interiors:
            continue
        if max([_touch_len(cut, o) for o in others] or [0.0]) < 0.5:
            continue
        if rest[0].area - despike(rest[0]).area > 0.2:
            # the cut ran along an edge the zone already had and left a hairline arm of it
            # behind: that arm is what walls the piece off from the neighbour meant to take it.
            continue
        key = (rank, cut.area)
        if best is None or key < best[0]:
            best = (key, rest[0], cut)
    return (best[1], best[2]) if best else None


def open_rings(fp, flats, core):
    """No zone may enclose a void or another zone. A gallery that runs the whole way round
    a courtyard comes out as one zone with a hole in the middle of its floor, and a zone
    floor is a single outline: there is no way to state a hole in it, EnergyPlus has no
    object for it, and no plan draws one. Cut the ring open with a radial slice, at the
    corner of the void where it costs the least, and hand the slice to the flats that hold
    its wall -- the circulation comes out as a C, every zone stays one simple outline, and
    the plate stays covered."""
    for _ in range(3):
        got = _open_ring(core, fp, flats)
        if got is None:
            break
        core, cut = got
        for pk in parts(cut):
            near = [k for k in range(len(flats)) if flats[k].distance(pk) < 0.05]
            if near:
                flats = _share(pk, flats, near)
            else:
                i = min(range(len(flats)), key=lambda k: flats[k].distance(pk))
                flats[i] = join(flats[i], pk)
    for i in range(len(flats)):
        for _ in range(3):
            got = _open_ring(flats[i], fp,
                              [flats[k] for k in range(len(flats)) if k != i] +
                              ([core] if core is not None else []))
            if got is None:
                break
            flats[i], cut = got
            others = [k for k in range(len(flats)) if k != i and flats[k].distance(cut) < 0.05]
            for pk in parts(cut):
                if others:
                    flats = _share(pk, flats, others)
                elif core is not None and core.distance(pk) < 0.05:
                    core = join(core, pk)
    return flats, core


def disjoint(fp, flats, core):
    """Last word on the plate: re-derive every shape as what is left after the shapes
    before it, largest first, so no two zones can claim the same square metre, then
    hand any crack this opens back to its neighbour."""
    claimed = core if core is not None else Polygon()
    order = sorted(range(len(flats)), key=lambda i: -flats[i].area)
    out = [None] * len(flats)
    for i in order:
        out[i] = deneedle(despike(weld(ok(flats[i]).difference(claimed).intersection(fp), Polygon())))
        claimed = claimed.union(out[i])
    return close_gaps(fp, out, core)


def apply_law(r):
    if not r.get("dwellings"):
        return r
    fp = Polygon(r["footprint"][0], r["footprint"][1:])
    flats = [Polygon(x[0], x[1:]) for x in r["dwellings"]]
    circs = [Polygon(x) for x in r["circulation"]]
    core, dropped = pick_core(fp, circs)
    before = sum(c.area for c in circs)
    if core is not None:
        core = biggest(core.intersection(fp), core)
    scraps = parts(uncovered(fp, flats + ([core] if core else [])))
    flats = absorb(fp, flats, scraps, core)
    flats = merge_to(flats, int(r["drawn_per_floor"]))
    budget = core.area if core is not None else 0.0
    for _ in range(3):
        flats, core = fold_narrow_to_core(fp, flats, core, budget=budget)
    for _ in range(3):
        # tidy() re-derives every shape, so it can hand a flat a tail the previous
        # unsnake() had already given away; alternate the two until neither changes
        # anything rather than trusting a single pass of each.
        flats, core = tidy(fp, flats, core)
        flats, core = unsnake(fp, flats, core)
    for _ in range(2):
        flats, core = straight_cuts(fp, flats, core)
        flats, core = tidy(fp, flats, core)
    flats, core = open_rings(fp, flats, core)
    flats, core = disjoint(fp, flats, core)
    flats = [deneedle(despike(f)) for f in flats]
    core = deneedle(core)
    # the hairline the despike gave up goes back to the zone that owns its wall. Three
    # times, because welding one seam can expose the next along the same wall -- then a
    # last de-needle, because a weld that had to bridge a crack arrives with the points it
    # bridged with and nothing after it would drop them.
    for _ in range(3):
        flats, core = close_gaps(fp, flats, core)
    # sharing a pocket out leaves a 5 cm staircase where the two wavefronts met -- small
    # enough to be invisible in the drawing and still a dozen extra points on a wall that
    # is one line. Take it off, re-clip, and close what taking it off opened.
    wall = fp.exterior.buffer(0.05, **SQUARE)
    for _ in range(2):
        if core is not None:
            core = deneedle(dekink(core, wall))
        flats = [deneedle(dekink(f, wall)) for f in flats]
        flats, core = disjoint(fp, flats, core)
        flats, core = close_gaps(fp, flats, core)
    flats = [deneedle(f) for f in flats]
    core = deneedle(core)
    flats = sorted(flats, key=lambda f: (-f.centroid.y, f.centroid.x))
    r["dwellings"] = [rings(f) for f in flats]
    r["circulation"] = [rings(core)] if core is not None else []
    r["circ_m2"] = round(core.area, 1) if core is not None else 0.0
    r["cores_before"] = len(circs)
    r["circ_m2_before"] = round(before, 1)
    tot = sum(f.area for f in flats) + (core.area if core else 0.0)
    print(f'{r["group"]:<20} cores {len(circs)}->1  circ {before:6.1f}->{r["circ_m2"]:5.1f} m2 '
          f'({100*r["circ_m2"]/fp.area:4.1f}%) | flats {len(flats)} = {sum(f.area for f in flats):6.1f} '
          f'| plate {fp.area:6.1f} covered {100*tot/fp.area:6.2f}%')
    return r


def main():
    rows = json.load(open(SRC))
    for r in rows:
        apply_law(r)
    json.dump(rows, open(SRC, "w"), separators=(",", ":"))
    print("rewrote", SRC)


if __name__ == "__main__":
    main()
