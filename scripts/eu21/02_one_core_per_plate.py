"""Document-only pass over the plan JSON that feeds the group rules HTML.

One core per plate: the interior stair core is kept, every other circulation
piece and every uncovered scrap is absorbed into the flat it shares the most
wall with, and fragments are merged back down to the drawn flat count.
Reads and rewrites eu21_group_plans.json. No engine code is touched.
"""
import json
from shapely.geometry import Polygon
from shapely.ops import unary_union

import pathlib
SRC = pathlib.Path(__file__).with_name("group_plans.json")
EPS = 0.02


def parts(g):
    """Polygon sub-pieces of any geometry, including a GeometryCollection -- a chain of
    difference() calls can degenerate into one of those, mixing in stray points/lines."""
    if g.is_empty:
        return []
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
            out = unary_union([out, extra])
    # touching-at-a-point can still leave union() as a MultiPolygon; collapse to the
    # single largest piece rather than pass a shape rings() cannot handle downstream.
    return biggest(out, out)


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
        remaining = remaining.difference(core.buffer(0.001))
    grown = list(flats)
    buckets = [[f] for f in flats]
    step, guard = 0.20, 0
    while not remaining.is_empty and remaining.area > 1e-6 and guard < 400:
        guard += 1
        progressed = False
        for i in range(len(grown)):
            if remaining.is_empty:
                break
            claim = grown[i].buffer(step).intersection(remaining)
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
    claimed = core.buffer(0.001) if core is not None else Polygon()
    out = []
    for b in buckets:
        m = unary_union([b[0]] + [x.buffer(EPS) for x in b[1:]])
        m = m.intersection(fp).difference(claimed)
        m = weld(m, b[0])
        out.append(m)
        claimed = claimed.union(m)
    return out


def fold_narrow_to_core(fp, flats, core, r=0.5):
    """A flat pocket narrower than 2r that touches the core is circulation-shaped, not
    room-shaped: fold it into the core instead of leaving it as a sliver on the flat."""
    if core is None:
        return flats, core
    out = []
    for f in flats:
        body = f.buffer(-r).buffer(r).intersection(f)
        sliver = f.difference(body.buffer(1e-6))
        keep = f
        for p in parts(sliver):
            if p.area < 1e-6 or p.area > 0.5 * f.area or p.distance(core) > 0.05:
                continue
            # p can sit a hair off the core (rounding from the growth pass in absorb()).
            # A morphological close (dilate then erode by the same radius) bridges that
            # gap without permanently growing the shape into whatever else is nearby --
            # unlike buffering p outward, which would leak into the neighbour past it.
            core = weld(unary_union([core, p]).buffer(0.03).buffer(-0.03).intersection(fp), core)
            keep = keep.difference(p)
        out.append(weld(keep.intersection(fp), keep))
    return out, core


def close_gaps(fp, flats, core):
    """Snap any leftover sliver of numerical seam to whichever neighbour it borders,
    so plate coverage never reads short over a rounding crack."""
    covered = unary_union(flats + ([core] if core else []))
    gap = fp.difference(covered)
    for p in parts(gap):
        if p.area < 1e-9:
            continue
        pool = flats + ([core] if core else [])
        i = min(range(len(pool)), key=lambda k: pool[k].distance(p))
        if core is not None and i == len(flats):
            core = weld(unary_union([core, p]), core)
        else:
            flats[i] = weld(unary_union([flats[i], p]), flats[i])
    return flats, core


def merge_to(flats, target):
    """Weld fragments together until the drawing shows the flat count it claims."""
    while len(flats) > target:
        i = min(range(len(flats)), key=lambda k: flats[k].area)
        j, best = None, 0.05
        for k in range(len(flats)):
            if k == i:
                continue
            w = flats[i].buffer(EPS).intersection(flats[k]).area
            if w > best:
                j, best = k, w
        if j is None:
            break
        m = biggest(unary_union([flats[i].buffer(EPS), flats[j]]).buffer(-EPS / 2), flats[j])
        flats = [f for k, f in enumerate(flats) if k not in (i, j)] + [m]
    return flats


rows = json.load(open(SRC))
for r in rows:
    if not r.get("dwellings"):
        continue
    fp = Polygon(r["footprint"][0], r["footprint"][1:])
    flats = [Polygon(x[0], x[1:]) for x in r["dwellings"]]
    circs = [Polygon(x) for x in r["circulation"]]
    core, dropped = pick_core(fp, circs)
    before = sum(c.area for c in circs)
    if core is not None:
        core = biggest(core.intersection(fp), core)
    scraps = parts(fp.difference(unary_union(flats + ([core] if core else []))))
    flats = absorb(fp, flats, scraps, core)
    flats = merge_to(flats, int(r["drawn_per_floor"]))
    for _ in range(3):
        flats, core = fold_narrow_to_core(fp, flats, core)
    flats, core = close_gaps(fp, flats, core)
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

json.dump(rows, open(SRC, "w"), separators=(",", ":"))
print("rewrote", SRC)
