"""EU-21 direct per-group cutters (D-EU-64, D-EU-67, D-EU-68): place circulation
first and cut flats with straight lines in the plate's own frame, clipped to the
surveyed footprint -- the algorithm rules/RULES_dwelling_layout_groups_2026-09-01.html
sheets' steps 3-4 describe, written as code. Never runs EnergyPlus (D-EU-55) and
never edits 01/02/03, group_plans.json or openubem/geometry/.
"""
import importlib.util as ilu
import json
import math
import pathlib
import sys

from shapely.affinity import rotate, translate
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points, split, unary_union
from shapely.validation import make_valid
from shapely import set_precision

ROOT = pathlib.Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(ROOT))

from openubem.geometry.european_residential import (
    RULED_GRID_MAX_DWELLINGS_PER_FLOOR as MAXK,
    DWELLING_DENSITY_REFUSAL_TOKEN,
)


def _load_frozen_t05b(name, relpath):
    spec = ilu.spec_from_file_location(name, str(ROOT / relpath))
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# T05b/D-EU-78: read-only reuse of 02's own lobe test (never edits 02) so the cutter's
# own C4 pre-check matches the check exactly, the same precedent 04_group_tests.py
# already sets for the same function.
_M02_T05B = _load_frozen_t05b("eu21_m02_lobes_t05b", "scripts/eu21/02_one_core_per_plate.py")
lobes_of = _M02_T05B.lobes_of
# T06c: same read-only reuse, so the neck target below matches 02's own erosion radius exactly.
NECK_R = _M02_T05B.NECK_R

CORRIDOR_W = 1.80
CORE_FRACTION = 0.06
CORE_MIN_SIDE = 2.40
CORE_MAX_SIDE = 4.00
DOUBLE_LOADED_MIN_DEPTH = 12.0
LANDING = 1.50
SLIVER_MAX_W = 8.0
BAND_MIN_W = 3.0
MIN_FLAT_W = BAND_MIN_W
COURTYARD_MIN_VOID_SIDE = 6.0
ACCESS_MIN_M = 1.0
DENOISE_TOL = 0.30
CORRIDOR_MAX_POINTS = 16  # D-EU-71, mirrors 04_group_tests.py:55 -- read-only cap, T05b's own acceptance gate
C10_MIN_WIDTH_M = 2.00  # D-EU-72, mirrors 04_group_tests.py:56 -- read-only guard, same reason
REFLEX_TOL_DEG = 10.0
MIN_WING_M2 = 15.0
MIN_WING_W = 3.0
SCRAP_M2 = 0.01
BIG = 10_000.0
MAX_WING_PIECES = 14

CONVEX_GROUPS = {"SQUARE", "RECTANGLE", "CORRIDOR_RECTANGLE", "SLAB", "TRIANGLE", "TRAPEZOID"}
LINEAR_GALLERY_GROUPS = {"CORRIDOR_RECTANGLE", "SLAB"}
WING_GROUPS = {"L_SHAPE", "U_OR_T_SHAPE", "COMPLEX_MULTI_WING"}


class Refusal(Exception):
    def __init__(self, token):
        super().__init__(token)
        self.token = token


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


def _equal_area_lines(P, N, axis):
    """D-EU-78/T09: `equal_area_x` generalised to either axis, for `corridor_rect`'s
    remainder piece only -- never called by, and never changes, the frozen
    `equal_area_x` above."""
    if N <= 1:
        return []
    minx, miny, maxx, maxy = P.bounds
    total = P.area
    lo0, hi0 = (minx, maxx) if axis == "x" else (miny, maxy)
    lines = []
    for i in range(1, N):
        target = i / N * total
        lo, hi = lo0, hi0
        for _ in range(40):
            if hi - lo < 1e-3:
                break
            mid = (lo + hi) / 2
            if axis == "x":
                a = P.intersection(box(minx - 1, miny - 1, mid, maxy + 1)).area
            else:
                a = P.intersection(box(minx - 1, miny - 1, maxx + 1, mid)).area
            if a < target:
                lo = mid
            else:
                hi = mid
        lines.append((lo + hi) / 2)
    return lines


def _snap_cuts_to_voids(P_local, xs, y_row=None):
    """DD-7 snap rule: the nearest cut (a column x, or the row line when M=2) snaps to
    every interior ring's centroid coordinate, no distance limit."""
    xs = list(xs)
    for ring in P_local.interiors:
        vc = Polygon(ring).centroid
        candidates = [("x", i, abs(vc.x - x)) for i, x in enumerate(xs)]
        if y_row is not None:
            candidates.append(("y", None, abs(vc.y - y_row)))
        if not candidates:
            continue
        kind, idx, _ = min(candidates, key=lambda c: c[2])
        if kind == "x":
            xs[idx] = vc.x
        else:
            y_row = vc.y
    return xs, y_row


def choose_loading(L_eff, W, k):
    """DD-6: pick M in {2,1} by the smaller max/min aspect, both col_w and depth >= MIN_FLAT_W."""
    best = None
    for M in (2, 1):
        N = math.ceil(k / M)
        col_w = L_eff / N if N > 0 else 0.0
        depth = (W - CORRIDOR_W) / M
        if col_w < MIN_FLAT_W or depth < MIN_FLAT_W:
            continue
        lo, hi = min(col_w, depth), max(col_w, depth)
        score = hi / lo if lo > 1e-9 else float("inf")
        if best is None or score < best[0]:
            best = (score, M, N)
    if best is None:
        raise Refusal("BAND_LT_3M")
    return best[1], best[2]


def _choose_loading_no_band(L_eff, W, k):
    """T07: `choose_loading`'s own layout search, minus the `CORRIDOR_W` reserved
    from `W` -- for a `cut_wings` limb the free-bearing band will not run through
    (D-EU-70: it is reached by a spur off the band-bearing limb instead, T03's
    existing `_ensure_flat_access`). A limb whose own depth cannot spare
    `CORRIDOR_W` and still keep `MIN_FLAT_W` (plate 25's `L_SHAPE`,
    `GB-LDN-STDUNSTANS way/1057823423`) is exactly the case D-EU-70 already
    describes: 'the band must be found in the limb that can hold it, remaining
    flats reached by spur' -- never a reason to refuse a genuine limb."""
    best = None
    for M in (2, 1):
        N = math.ceil(k / M)
        col_w = L_eff / N if N > 0 else 0.0
        depth = W / M
        if col_w < MIN_FLAT_W or depth < MIN_FLAT_W:
            continue
        lo, hi = min(col_w, depth), max(col_w, depth)
        score = hi / lo if lo > 1e-9 else float("inf")
        if best is None or score < best[0]:
            best = (score, M, N)
    if best is None:
        raise Refusal("BAND_LT_3M")
    return best[1], best[2]


def _shared_len_metric(part, other):
    if other is None or other.is_empty or part is None or part.is_empty or part.area <= 1e-6:
        return 0.0
    buf = part.buffer(0.02, cap_style="flat", join_style="mitre")
    return buf.intersection(other).area / 0.02


def _safe_union(geoms):
    try:
        return unary_union(geoms)
    except Exception:
        try:
            return unary_union([g.buffer(0) for g in geoms])
        except Exception:
            return None


def finish(fp, flats, circ, circ_is_rect=False):
    """D-EU-68: the only clean-up -- one room, no scrap, report (never patch) a hole.

    T09/D-EU-78: `circ_is_rect=True` marks a `circ` that came from `corridor_rect` --
    a rectangle "designed, not accumulated". The dissolve/gap passes below still
    offer every scrap to the flats first, exactly as before (byte-for-byte
    unchanged when `circ_is_rect` is false, the default for every other caller);
    only when a scrap can find no flat and would fall into `circ` is the event
    marked via `circ_contaminated` in the return value, so the caller can discard
    the rectangle result and fall back to the band path instead -- area is still
    never deleted (the union still happens), but the plate never keeps a corridor
    that had to absorb leftover area to stay whole."""
    flats = [_polygons_only(f) for f in flats]
    circ = _polygons_only(circ) if circ is not None else None
    state = {"circ": circ, "circ_is_rect": circ_is_rect, "circ_contaminated": False}
    unsnapped = [0]

    def _safe_precision(g):
        try:
            return set_precision(g, 0.001)
        except Exception:
            try:
                return set_precision(g.buffer(0), 0.001)
            except Exception:
                unsnapped[0] += 1
                return g

    def dissolve_pass():
        changed = False
        for idx in range(len(flats)):
            f = flats[idx]
            if f.geom_type != "MultiPolygon":
                continue
            changed = True
            parts = sorted(f.geoms, key=lambda p: p.area, reverse=True)
            flats[idx] = parts[0]
            for part in parts[1:]:
                order = sorted(
                    (j for j in range(len(flats)) if j != idx),
                    key=lambda j: _shared_len_metric(part, flats[j]),
                    reverse=True,
                )
                placed = False
                for j in order:
                    merged = _safe_union([flats[j], part])
                    if merged is not None and merged.geom_type == "Polygon":
                        flats[j] = merged
                        placed = True
                        break
                if not placed and state["circ"] is not None and part.intersects(state["circ"]):
                    if state["circ_is_rect"]:
                        state["circ_contaminated"] = True
                    merged = _safe_union([state["circ"], part])
                    if merged is not None:
                        state["circ"] = merged if merged.geom_type == "Polygon" else max(merged.geoms, key=lambda p: p.area)
        return changed

    for _pass in range(3):
        if not dissolve_pass():
            break

    for _pass in range(3):
        covered = _safe_union(flats + ([state["circ"]] if state["circ"] is not None else []))
        if covered is None:
            break
        U = fp.difference(covered)
        if U.is_empty:
            break
        parts = list(U.geoms) if U.geom_type == "MultiPolygon" else [U]
        changed = False
        for part in parts:
            if part.area <= SCRAP_M2:
                continue
            changed = True
            order = sorted(range(len(flats)), key=lambda j: _shared_len_metric(part, flats[j]), reverse=True)
            placed = False
            for j in order:
                merged = _safe_union([flats[j], part])
                if merged is not None and merged.geom_type == "Polygon":
                    flats[j] = merged
                    placed = True
                    break
            if not placed and state["circ"] is not None:
                merged = _safe_union([state["circ"], part])
                if merged is not None and merged.geom_type == "Polygon":
                    if state["circ_is_rect"]:
                        state["circ_contaminated"] = True
                    state["circ"] = merged
                    placed = True
        if not changed:
            break

    flats[:] = [_safe_precision(f) for f in flats]
    state["circ"] = _safe_precision(state["circ"]) if state["circ"] is not None else None
    if state["circ"] is not None and state["circ"].geom_type == "MultiPolygon":
        parts = sorted(state["circ"].geoms, key=lambda p: p.area, reverse=True)
        state["circ"] = parts[0]
        for part in parts[1:]:
            order = sorted(range(len(flats)), key=lambda j: _shared_len_metric(part, flats[j]), reverse=True)
            for j in order:
                merged = _safe_union([flats[j], part])
                if merged is not None and merged.geom_type == "Polygon":
                    flats[j] = merged
                    break

    for _pass in range(3):
        if not dissolve_pass():
            break

    circ = state["circ"]
    for f in flats:
        if len(f.interiors) > 0:
            raise Refusal("FLAT_ENCLOSES_ZONE")
    if circ is not None and len(circ.interiors) > 0:
        raise Refusal("FLAT_ENCLOSES_ZONE")

    flats, circ = _delobe_and_donate(fp, flats, circ)
    flats, circ = _corridor_reach(fp, flats, circ)
    flats, circ = _delobe_by_absorption(fp, flats, circ)

    flats = [_safe_precision(f) for f in flats]
    circ = _safe_precision(circ) if circ is not None else None
    flats.sort(key=lambda f: (-f.centroid.y, f.centroid.x))
    return {"flats": flats, "circ": circ, "unsnapped": unsnapped[0],
            "circ_contaminated": state["circ_contaminated"]}


def _denoise_corridor(circ, poly):
    """T05/C9: a finished corridor outline can copy every real facade jog and every
    orphan cell-cap `finish()` had to absorb into it (D-EU-76 (a): whole-cell bands are
    a preference, not a gate). Drop collinear/near-collinear corners with the file's
    own DENOISE_TOL -- accepted only when it neither pokes outside the real footprint
    nor measurably changes the corridor's own area, so C1 coverage never moves and no
    check threshold is loosened; a shape whose jaggedness is real stays as drawn."""
    if circ is None:
        return circ
    simplified = circ.simplify(DENOISE_TOL, preserve_topology=True)
    if simplified.geom_type != "Polygon":
        return circ
    if simplified.difference(poly).area > 1e-6:
        return circ
    if abs(simplified.area - circ.area) > 0.02:
        return circ
    return simplified


def corridor_rect(poly, core, k):
    """D-EU-78/T09: the circulation zone is chosen first, as one axis-aligned
    rectangle, before any flat is cut -- tried in `cut`/`_dispatch_group` ahead of
    the band solver. Orientations are the plate's own `frame()` axis and its
    perpendicular only. Candidates, in the owner's own order: centred through the
    core's centroid; slid to the plate's own extremes along both axes (a full-span
    band already touches every prospective flat, so "sliding" and "growing until
    every flat reaches it" collapse to the same full-span candidate here); and, on
    a plate with a void, flush against each side of that void. A candidate is kept
    only if `_normalize` leaves it a clean 4-point rectangle that never leaves the
    footprint, does not swallow the core, and leaves `poly - rect` as a single
    piece big enough to hold `k` `BAND_MIN_W`-wide flats -- the first such
    candidate wins; `None` when none qualifies, so the caller falls through to the
    existing band solver, byte-for-byte unchanged."""
    theta, cx, cy, L, W = frame(poly)
    P = to_local(poly, theta, cx, cy)
    minx, miny, maxx, maxy = P.bounds
    width = max(C10_MIN_WIDTH_M + 0.20, CORRIDOR_W)
    core_local = to_local(core, theta, cx, cy) if core is not None and not core.is_empty else None
    if core_local is not None and not core_local.is_empty:
        ccx, ccy = core_local.centroid.x, core_local.centroid.y
    else:
        ccx, ccy = P.centroid.x, P.centroid.y

    candidates = [
        box(minx - 1, ccy - width / 2, maxx + 1, ccy + width / 2),
        box(ccx - width / 2, miny - 1, ccx + width / 2, maxy + 1),
        box(minx - 1, maxy - width, maxx + 1, maxy + 1),
        box(minx - 1, miny - 1, maxx + 1, miny + width),
        box(maxx - width, miny - 1, maxx + 1, maxy + 1),
        box(minx - 1, miny - 1, minx + width, maxy + 1),
    ]
    for ring in P.interiors:
        void = Polygon(ring)
        vminx, vminy, vmaxx, vmaxy = void.bounds
        candidates.extend([
            box(vminx, vmaxy, vmaxx, vmaxy + width),
            box(vminx, vminy - width, vmaxx, vminy),
            box(vmaxx, vminy, vmaxx + width, vmaxy),
            box(vminx - width, vminy, vminx, vmaxy),
        ])

    for cand in candidates:
        rect = cand.intersection(P)
        if rect.is_empty:
            continue
        rect = _normalize(rect)
        if rect.geom_type != "Polygon" or len(rect.interiors) > 0:
            continue
        if len(rect.exterior.coords) - 1 != 4:
            continue
        if rect.difference(P).area > 1e-6:
            continue
        if core_local is not None and not core_local.is_empty and core_local.within(rect):
            continue
        rem = P.difference(rect)
        pieces = _polygon_pieces(rem)
        if len(pieces) != 1:
            continue
        if pieces[0].area < k * BAND_MIN_W * BAND_MIN_W:
            continue
        return to_world(rect, theta, cx, cy)
    return None


def _checks_pass(fp, flats, circ, n, grp):
    """D-EU-78/T09: a read-only mirror of 04_group_tests.py's own C1/C2/C4/C8/C9/C10
    formulas (04:318-380), the same precedent `_access_len`/`_widest_fit` already
    set, so `corridor_rect`'s candidate is accepted only by the exact bar the
    census applies -- never a looser one."""
    cores = [circ] if circ is not None else []
    cov = ((sum(f.area for f in flats) + sum(c.area for c in cores)) / fp.area) if fp.area else 0.0
    if not (0.999 <= cov <= 1.001):
        return False
    nc = len(cores)
    if not (nc == 1 or (grp == "SLIVER" and nc <= 1)):
        return False
    if any(lobes_of(f) is not None for f in flats):
        return False
    worst = 0.0
    for i in range(len(flats)):
        for j in range(i + 1, len(flats)):
            ov = flats[i].intersection(flats[j]).area
            if ov > worst:
                worst = ov
        for c in cores:
            ov = flats[i].intersection(c).area
            if ov > worst:
                worst = ov
    if not (worst < 0.02):
        return False
    if cores:
        circ_shape = cores[0]
        access_min = min((_access_len(circ_shape, f) for f in flats), default=0.0)
        if access_min < ACCESS_MIN_M:
            return False
        if (len(circ_shape.exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
            return False
    zones = flats + cores
    r3 = min(_widest_fit(z) for z in zones) if zones else 0.0
    if r3 < C10_MIN_WIDTH_M:
        return False
    return True


def _try_corridor_rect(poly, k, grp):
    """D-EU-78/T09: tries `corridor_rect` first; any failure at any step -- no
    rectangle, a contaminated circ, or a failed check -- falls through to `None`
    so the caller runs the existing dispatch untouched (DD-4: never a new
    refusal, never a widened one)."""
    try:
        s = min(max(math.sqrt(CORE_FRACTION * poly.area), CORE_MIN_SIDE), CORE_MAX_SIDE)
        ctr = poly.centroid
        core = box(ctr.x - s / 2, ctr.y - s / 2, ctr.x + s / 2, ctr.y + s / 2).intersection(poly)
        rect = corridor_rect(poly, core, k)
        if rect is None:
            return None
        theta, cx, cy, L, W = frame(poly)
        P = to_local(poly, theta, cx, cy)
        rect_local = to_local(rect, theta, cx, cy)
        rem_local = P.difference(rect_local)
        pieces = _polygon_pieces(rem_local)
        if len(pieces) != 1:
            return None
        rem = pieces[0]
        rminx, rminy, rmaxx, rmaxy = rect_local.bounds
        axis = "x" if (rmaxx - rminx) >= (rmaxy - rminy) else "y"
        lines = _equal_area_lines(rem, k, axis)
        minx, miny, maxx, maxy = rem.bounds
        cells_local = []
        if axis == "x":
            bx = [minx - 1] + lines + [maxx + 1]
            for i in range(k):
                c = rem.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1))
                if c.is_empty or c.area < SCRAP_M2 or (c.bounds[2] - c.bounds[0]) < BAND_MIN_W:
                    return None
                cells_local.append(c)
        else:
            by = [miny - 1] + lines + [maxy + 1]
            for i in range(k):
                c = rem.intersection(box(minx - 1, by[i], maxx + 1, by[i + 1]))
                if c.is_empty or c.area < SCRAP_M2 or (c.bounds[3] - c.bounds[1]) < BAND_MIN_W:
                    return None
                cells_local.append(c)
        flats_world = [to_world(c, theta, cx, cy) for c in cells_local]
        out = finish(poly, flats_world, rect, circ_is_rect=True)
        if out.get("circ_contaminated"):
            return None
        circ_out = out["circ"]
        if circ_out is None or circ_out.geom_type != "Polygon":
            return None
        if (len(circ_out.exterior.coords) - 1) != 4:
            return None
        if len(out["flats"]) != k:
            return None
        if not _checks_pass(poly, out["flats"], circ_out, k, grp):
            return None
        out["scheme"] = "corridor_rect"
        out["notes"] = {"unsnapped": out.get("unsnapped", 0)}
        return out
    except Exception:
        return None


def cut_sliver(poly, k):
    """Sheet 02 step 4: k depth bands across the strip, equal area, no circulation."""
    theta, cx, cy, L, W = frame(poly)
    P = to_local(poly, theta, cx, cy)
    minx, miny, maxx, maxy = P.bounds
    xs = equal_area_x(P, k)
    xs, _ = _snap_cuts_to_voids(P, xs)
    bx = [minx - 1] + xs + [maxx + 1]
    flats_local = []
    for i in range(k):
        f = P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1))
        if f.is_empty:
            raise Refusal("CELL_EMPTY")
        fminx, _, fmaxx, _ = f.bounds
        if (fmaxx - fminx) < BAND_MIN_W:
            raise Refusal("BAND_LT_3M")
        flats_local.append(f)
    flats_world = [to_world(f, theta, cx, cy) for f in flats_local]
    out = finish(poly, flats_world, None)
    out["scheme"] = "row_house_depth_bands"
    out["notes"] = {"unsnapped": out.get("unsnapped", 0)}
    return out


def cut_convex(poly, k, grp):
    """Sheets 03-08 steps 3-4: core inside the plate, k flats on an N x M grid."""
    theta, cx, cy, L, W = frame(poly)
    P = to_local(poly, theta, cx, cy)
    minx, miny, maxx, maxy = P.bounds
    A = P.area
    yc = P.centroid.y
    s = min(max(math.sqrt(CORE_FRACTION * A), CORE_MIN_SIDE), CORE_MAX_SIDE)

    if k <= 4:
        M = 1 if k == 2 else 2
        N = math.ceil(k / M)
        xs = equal_area_x(P, N)
        if M == 2:
            xs, yc = _snap_cuts_to_voids(P, xs, yc)
        else:
            xs, _ = _snap_cuts_to_voids(P, xs)
        bx = [minx - 1] + xs + [maxx + 1]
        if M == 1:
            cells = [P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1)) for i in range(N)]
        else:
            raw = {}
            for i in range(N):
                bottom = P.intersection(box(bx[i], miny - 1, bx[i + 1], yc))
                top = P.intersection(box(bx[i], yc, bx[i + 1], maxy + 1))
                raw[i] = [bottom, top]
            if k == 3:
                def mean_depth(i):
                    w = bx[i + 1] - bx[i]
                    seg = P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1))
                    return seg.area / w if w > 0 else 0.0
                d0, d1 = mean_depth(0), mean_depth(N - 1)
                merge_i = 0 if d0 < d1 else (N - 1)
                cells = []
                for i in range(N):
                    if i == merge_i:
                        cells.append(unary_union(raw[i]))
                    else:
                        cells.extend(raw[i])
            else:
                cells = []
                for i in range(N):
                    cells.extend(raw[i])
        core_cx = xs[0] if N == 2 else P.centroid.x
        core = box(core_cx - s / 2, yc - s / 2, core_cx + s / 2, yc + s / 2).intersection(P)
        circ_local = core
        scheme = f"ruled_grid_{N}x{M}"
    else:
        L_eff = maxx - minx
        if grp in LINEAR_GALLERY_GROUPS:
            M = 1
            N = k
            if (L_eff / N if N > 0 else 0.0) < MIN_FLAT_W:
                raise Refusal("BAND_LT_3M")
        else:
            M, N = choose_loading(L_eff, W, k)
        xs = equal_area_x(P, N)
        if M == 2:
            xs, yc = _snap_cuts_to_voids(P, xs, yc)
        else:
            xs, _ = _snap_cuts_to_voids(P, xs)
        bx = [minx - 1] + xs + [maxx + 1]
        odd_through = (k % 2 == 1) and (M == 2)

        cells = []
        for i in range(N):
            if odd_through and i == N - 1:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1)))
            elif M == 2:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], yc)))
                cells.append(P.intersection(box(bx[i], yc, bx[i + 1], maxy + 1)))
            else:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1)))

        if grp in LINEAR_GALLERY_GROUPS:
            cxmin = minx - 1
            cxmax = xs[-1] if odd_through else maxx + 1
        else:
            cxmin = xs[0] - LANDING
            cxmax = xs[-1] if odd_through else xs[-1] + LANDING

        half_width = CORRIDOR_W / 2
        if M == 2:
            centre_hint = yc
        else:
            xmid = (cxmin + cxmax) / 2
            strip = P.intersection(box(xmid - 0.05, miny - 1, xmid + 0.05, maxy + 1))
            maxy_local = strip.bounds[3] if not strip.is_empty else maxy
            centre_hint = maxy_local - 0.9

        solved = solve_band_free(P, cells, centre_hint, half_width, cxmin, cxmax, whole_cells=True)
        band = solved["band"]
        core_center = (band.centroid.x, band.centroid.y)

        core = box(core_center[0] - s / 2, core_center[1] - s / 2, core_center[0] + s / 2, core_center[1] + s / 2).intersection(P)
        circ_local = _polygons_only(unary_union([core, band]).intersection(P))
        for _pass in range(8):
            if circ_local.geom_type == "Polygon":
                break
            parts = sorted(circ_local.geoms, key=lambda g: g.area, reverse=True)
            circ_local = _bridge(parts[0], parts[1:], P)
        if circ_local.geom_type != "Polygon":
            raise Refusal("WING_TREE_FAILED")

        scheme = "i_shape_linear_gallery" if grp in LINEAR_GALLERY_GROUPS else f"spine_grid_{N}x{M}"

    flats_local = []
    for cell in cells:
        f = cell.difference(circ_local) if circ_local is not None else cell
        if f.is_empty or f.area < SCRAP_M2:
            raise Refusal("CELL_EMPTY")
        flats_local.append(f)

    flats_world = [to_world(f, theta, cx, cy) for f in flats_local]
    circ_world = to_world(circ_local, theta, cx, cy) if circ_local is not None else None
    out = finish(poly, flats_world, circ_world)
    if grp in LINEAR_GALLERY_GROUPS:
        out["circ"] = _denoise_corridor(out["circ"], poly)
        if out["circ"] is not None and (len(out["circ"].exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
            out["flats"], out["circ"] = _rectify_and_reassign(poly, out["flats"], out["circ"])
    out["scheme"] = scheme
    out["notes"] = {"unsnapped": out.get("unsnapped", 0)}
    return out


_SIDE_CYCLE = ["+x", "+y", "-x", "-y"]


def _side_len(side, a, b):
    return 2 * b if side in ("+x", "-x") else 2 * a


def _side_point(side, u, a, b):
    if side == "+x":
        return (a, -b + u * 2 * b)
    if side == "+y":
        return (a - u * 2 * a, b)
    if side == "-x":
        return (-a, b - u * 2 * b)
    return (-a + u * 2 * a, -b)


def _side_normal(side):
    return {"+x": (1.0, 0.0), "-x": (-1.0, 0.0), "+y": (0.0, 1.0), "-y": (0.0, -1.0)}[side]


def _corner_after(side):
    return {"+x": "NE", "+y": "NW", "-x": "SW", "-y": "SE"}[side]


def _perimeter_segs(s0):
    i0 = _SIDE_CYCLE.index(s0)
    cyc = _SIDE_CYCLE[i0:] + _SIDE_CYCLE[:i0]
    return [(s0, 0.5, 1.0)] + [(s, 0.0, 1.0) for s in cyc[1:]] + [(s0, 0.0, 0.5)]


def _corner_ts(segs, a, b):
    out = {}
    off = 0.0
    for side, u0, u1 in segs:
        length = (u1 - u0) * _side_len(side, a, b)
        if abs(u1 - 1.0) < 1e-9:
            out.setdefault(_corner_after(side), off + length)
        off += length
    return out


def _u_of_side_point(side, pt, a, b):
    x, y = pt
    if side == "+x":
        return (y + b) / (2 * b)
    if side == "+y":
        return (a - x) / (2 * a)
    if side == "-x":
        return (b - y) / (2 * b)
    return (x + a) / (2 * a)


def _t_of_side_point(side, pt, a, b, segs):
    u = _u_of_side_point(side, pt, a, b)
    off = 0.0
    for s, u0, u1 in segs:
        length = (u1 - u0) * _side_len(s, a, b)
        if s == side and u0 - 1e-9 <= u <= u1 + 1e-9:
            frac = (u - u0) / (u1 - u0) if u1 > u0 else 0.0
            return off + frac * length
        off += length
    return 0.0


def _t_of_point(x, y, a, b, corner_ts, segs):
    if x > a and y > b:
        return corner_ts["NE"]
    if x > a and y < -b:
        return corner_ts["SE"]
    if x < -a and y > b:
        return corner_ts["NW"]
    if x < -a and y < -b:
        return corner_ts["SW"]
    if x > a:
        return _t_of_side_point("+x", (a, y), a, b, segs)
    if x < -a:
        return _t_of_side_point("-x", (-a, y), a, b, segs)
    if y > b:
        return _t_of_side_point("+y", (x, b), a, b, segs)
    if y < -b:
        return _t_of_side_point("-y", (x, -b), a, b, segs)
    margins = {"+x": a - x, "-x": x + a, "+y": b - y, "-y": y + b}
    side = min(margins, key=margins.get)
    return _t_of_side_point(side, _side_point(side, 0.5, a, b), a, b, segs)


def _point_at_t(t, segs, a, b):
    off = 0.0
    for side, u0, u1 in segs:
        length = (u1 - u0) * _side_len(side, a, b)
        if t <= off + length + 1e-9:
            frac = (t - off) / length if length > 1e-9 else 0.0
            u = u0 + frac * (u1 - u0)
            return _side_point(side, u, a, b), side
        off += length
    side, u0, u1 = segs[-1]
    return _side_point(side, u1, a, b), side


def _side_box(side, ua, ub, a, b):
    pa = _side_point(side, ua, a, b)
    pb = _side_point(side, ub, a, b)
    x0, x1 = sorted((pa[0], pb[0]))
    y0, y1 = sorted((pa[1], pb[1]))
    if side == "+x":
        return box(x0, y0, x1 + BIG, y1)
    if side == "-x":
        return box(x0 - BIG, y0, x1, y1)
    if side == "+y":
        return box(x0, y0, x1, y1 + BIG)
    return box(x0, y0 - BIG, x1, y1)


def _sector_polygon(t0, t1, corner_ts, segs, a, b):
    """Sheet 01 step 4: the swept region from t0 to t1 as a union of per-side strips."""
    boxes = []
    off = 0.0
    for side, su0, su1 in segs:
        length = (su1 - su0) * _side_len(side, a, b)
        seg_t0, seg_t1 = off, off + length
        lo, hi = max(t0, seg_t0), min(t1, seg_t1)
        if hi > lo + 1e-9:
            frac_lo = (lo - seg_t0) / length if length > 1e-9 else 0.0
            frac_hi = (hi - seg_t0) / length if length > 1e-9 else 1.0
            ua = su0 + frac_lo * (su1 - su0)
            ub = su0 + frac_hi * (su1 - su0)
            boxes.append(_side_box(side, ua, ub, a, b))
        off += length
    if not boxes:
        return Polygon()
    return unary_union(boxes)


def _equal_area_t(t0, t1, n_pieces, corner_ts, segs, a, b, Z):
    if n_pieces <= 1:
        return []
    total = _sector_polygon(t0, t1, corner_ts, segs, a, b).intersection(Z).area
    ts = []
    for i in range(1, n_pieces):
        target = i / n_pieces * total
        lo, hi = t0, t1
        for _ in range(40):
            if hi - lo < 1e-3:
                break
            mid = (lo + hi) / 2
            area = _sector_polygon(t0, mid, corner_ts, segs, a, b).intersection(Z).area
            if area < target:
                lo = mid
            else:
                hi = mid
        ts.append((lo + hi) / 2)
    return ts


def _distribute_cuts(forced_ts, k, corner_ts, segs, a, b, Z, P):
    forced_sorted = sorted(set(round(t, 6) for t in forced_ts))
    n_forced = len(forced_sorted)
    n_extra = max(0, k - n_forced)
    gaps = []
    for i in range(n_forced):
        t0 = forced_sorted[i]
        t1 = forced_sorted[(i + 1) % n_forced]
        if i == n_forced - 1:
            t1 += P
        gaps.append((t0, t1))
    gap_areas = [_sector_polygon(t0, t1, corner_ts, segs, a, b).intersection(Z).area for t0, t1 in gaps]
    total_area = sum(gap_areas) or 1.0
    raw = [n_extra * ga / total_area for ga in gap_areas]
    counts = [int(math.floor(r)) for r in raw]
    remainder = n_extra - sum(counts)
    order = sorted(range(len(gaps)), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[:remainder]:
        counts[i] += 1
    all_ts = list(forced_sorted)
    for (t0, t1), m in zip(gaps, counts):
        all_ts.extend(_equal_area_t(t0, t1, m + 1, corner_ts, segs, a, b, Z))
    return sorted(t if t < P else t - P for t in all_ts)


def _snap_to_corners(ts, corner_ts, P):
    candidates = []
    for i, t in enumerate(ts):
        best_d, best_c = None, None
        for cn, ct in corner_ts.items():
            d = min(abs(t - ct), P - abs(t - ct))
            if best_d is None or d < best_d:
                best_d, best_c = d, cn
        candidates.append((best_d, best_c, i))
    candidates.sort(key=lambda x: x[0])
    out = list(ts)
    claimed = set()
    for d, cn, i in candidates:
        if d < 1.0 and cn not in claimed:
            out[i] = corner_ts[cn]
            claimed.add(cn)
    return sorted(out)


def _quadrant_area(B, sx, sy):
    x0, x1 = (0, BIG) if sx > 0 else (-BIG, 0)
    y0, y1 = (0, BIG) if sy > 0 else (-BIG, 0)
    return B.intersection(box(x0, y0, x1, y1)).area


def _polygons_only(geom):
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    polys = [g for g in getattr(geom, "geoms", []) if g.geom_type in ("Polygon", "MultiPolygon")]
    return unary_union(polys) if polys else Polygon()


def rectify_band(container, axis, centre, half_width, lo, hi):
    """D-EU-74: the largest axis-aligned rectangle of full width 2*half_width,
    centred on `centre` across `axis`, spanning `[s, e]` inside `[lo, hi]` along
    `axis`, wholly contained in `container`. None when no admissible span of
    length >= 2 * CORRIDOR_W exists. Pure function: no flats, k or group state."""
    geom = _polygons_only(container)
    if geom.is_empty:
        return None
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    if geom.geom_type != "Polygon" or geom.is_empty:
        return None

    idx = 0 if axis == "x" else 1

    def make_rect(s, e):
        if axis == "x":
            return box(s, centre - half_width, e, centre + half_width)
        return box(centre - half_width, s, centre + half_width, e)

    def contained(s, e):
        if e - s <= 0:
            return False
        rect = set_precision(make_rect(s, e), 0.001)
        return geom.contains(rect)

    coords = list(geom.exterior.coords)
    for ring in geom.interiors:
        coords += list(ring.coords)
    raw_vals = {c[idx] for c in coords}
    vals = sorted({max(lo, min(hi, v)) for v in raw_vals} | {lo, hi})
    if len(vals) < 2:
        return None

    adm = [contained(vals[i], vals[i + 1]) for i in range(len(vals) - 1)]

    runs = []
    i = 0
    n = len(adm)
    while i < n:
        if adm[i]:
            j = i
            while j + 1 < n and adm[j + 1]:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1

    if not runs:
        return None

    refined = []
    for ri, rj in runs:
        s0, e0 = vals[ri], vals[rj + 1]

        if ri > 0:
            lo_b, hi_b = vals[ri - 1], s0
            while hi_b - lo_b > DENOISE_TOL:
                mid = (lo_b + hi_b) / 2
                if contained(mid, e0):
                    hi_b = mid
                else:
                    lo_b = mid
            s0 = hi_b

        if rj + 2 <= len(vals) - 1:
            lo_b, hi_b = e0, vals[rj + 2]
            while hi_b - lo_b > DENOISE_TOL:
                mid = (lo_b + hi_b) / 2
                if contained(s0, mid):
                    lo_b = mid
                else:
                    hi_b = mid
            e0 = lo_b

        refined.append((s0, e0))

    best = max(e - s for s, e in refined)
    if best < 2 * CORRIDOR_W:
        return None

    tied = [(s, e) for s, e in refined if (best - (e - s)) <= DENOISE_TOL]
    centroid_val = geom.centroid.coords[0][idx]
    s, e = min(tied, key=lambda pair: abs((pair[0] + pair[1]) / 2 - centroid_val))

    return set_precision(make_rect(s, e), 0.001)


def _band_rect(axis, centre, half_width, s, e):
    if axis == "x":
        return box(s, centre - half_width, e, centre + half_width)
    return box(centre - half_width, s, centre + half_width, e)


def _band_span(axis, rect):
    b = rect.bounds
    return (b[0], b[2]) if axis == "x" else (b[1], b[3])


def _band_centre_point(axis, centre, span):
    mid = (span[0] + span[1]) / 2
    return (mid, centre) if axis == "x" else (centre, mid)


def _cross_bounds(bounds, axis):
    minx, miny, maxx, maxy = bounds
    return (miny, maxy) if axis == "x" else (minx, maxx)


def _travel_bounds(bounds, axis):
    minx, miny, maxx, maxy = bounds
    return (minx, maxx) if axis == "x" else (miny, maxy)


def _single_polygon(container):
    geom = _polygons_only(container)
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    if geom.is_empty or geom.geom_type != "Polygon":
        return None
    return geom


def _centre_candidates(geom, axis, half_width, centre_hint):
    idx = 1 if axis == "x" else 0
    clo, chi = _cross_bounds(geom.bounds, axis)
    coords = list(geom.exterior.coords)
    for ring in geom.interiors:
        coords += list(ring.coords)
    cset = set()
    for c in coords:
        v = c[idx]
        cset.add(v + half_width)
        cset.add(v - half_width)
    cset.add(centre_hint)
    return sorted(c for c in cset if c - half_width >= clo - 1e-6 and c + half_width <= chi + 1e-6)


def _trim_span_to_predicate(s, e, ok, pin_end=None):
    """Shrink [s, e] inward by bisection at DENOISE_TOL, stopping at the tightest
    span for which `ok(a, b)` still holds. `pin_end="lo"` keeps `s` fixed and only
    trims `e`; `pin_end="hi"` keeps `e` fixed and only trims `s`; the default trims
    both ends, byte-identical to the original two-sided behaviour (T04)."""
    if pin_end == "lo":
        s2 = s
    else:
        lo_b, hi_b = s, e
        while hi_b - lo_b > DENOISE_TOL:
            mid = (lo_b + hi_b) / 2
            if ok(mid, e):
                lo_b = mid
            else:
                hi_b = mid
        s2 = lo_b
    if pin_end == "hi":
        e2 = e
    else:
        lo_b, hi_b = s2, e
        while hi_b - lo_b > DENOISE_TOL:
            mid = (lo_b + hi_b) / 2
            if ok(s2, mid):
                hi_b = mid
            else:
                lo_b = mid
        e2 = hi_b
    return s2, e2


def solve_band(container, cells, axis_hint, centre_hint, half_width, lo, hi, *,
                bearings=None, pin_end=None, allow_chain=True, touch_len=0.05,
                whole_cells=False, core_of=None):
    """D-EU-73 (b): the bearing, centre and length of a single circulation band are
    unknowns to solve for, not inputs to pin. Chooses them by scanning a finite
    candidate set (container boundary coordinates offset by half_width, plus
    centre_hint) with `rectify_band`, first on `axis_hint` then its perpendicular,
    keeping only candidates that touch every cell, then shortening the survivor to
    the minimum length that still touches every cell (D-EU-73 (b), "central" /
    "minimum length that achieves that"). When no single band touches every cell,
    chains a second, perpendicular band end to end (D-EU-73 (e)) via
    `chain_second_band`. `cells` is read only to score candidates -- `rectify_band`
    itself stays the pure feasibility primitive of `D-EU-74` (1).

    `bearings` (T04): restrict the candidate axes searched to this sequence; the
    default `None` reproduces today's `(axis_hint, axis_perp)` byte-for-byte. When
    the perpendicular axis is excluded, `chain_second_band` -- itself a perpendicular
    join -- is never attempted either (D-EU-73 (a): no cross-limb band).
    `pin_end` (T04): "lo" or "hi" keeps that end of the trimmed span fixed at the
    length `rectify_band` found, so the minimum-length step (D-EU-73 (b)) only ever
    shortens the *other*, free end -- used to hold a wing's band at its junction
    while its far end still shortens. The default `None` trims both ends, as before.
    `allow_chain` (T04, D-EU-75 (a)): when `False`, `chain_second_band` is never
    attempted -- a plate that does not touch every cell on a single band returns
    that best single band with `"full": False`, rather than chaining a second one.
    The default `True` reproduces every existing call site's behaviour unchanged.
    Every return carries `"full"`: `True` only for a band that touches every cell.
    `whole_cells` (T06, D-EU-76 (a)): when `True`, candidates are ranked first by how
    many cells they leave whole (`_cell_whole`) -- the candidate tying for the most
    is preferred, tie-broken by the sort already used inside the full-touch tier.
    This is a preference, not a gate: when no candidate leaves any cell whole the
    max is 0 and every candidate ties on it, so the choice degrades to today's
    full-touch answer unchanged -- a cell that is inherently un-whole-able (D-EU-76
    (b)) never drags the count down for the plate's other, otherwise-whole cells.
    The default `False` reproduces today's behaviour byte-for-byte -- every count
    is 0 and every candidate ties.
    `core_of` (T06, D-EU-76 (a)/FINDING 230): when `whole_cells` is set, this is
    called with each trimmed candidate band (this function's own frame) and must
    return the core geometry the caller will plant on that band's centroid once it
    is chosen -- or `None`/empty for no core. `_cell_whole` then subtracts
    `band ∪ core`, not `band` alone, so a candidate that only looks whole before the
    core lands is never preferred. The default `None` reproduces `_cell_whole`'s
    band-only test unchanged."""
    geom = _single_polygon(container)
    if geom is None:
        raise Refusal("BAND_LT_3M")

    axis_perp = "y" if axis_hint == "x" else "x"
    axes = bearings if bearings is not None else (axis_hint, axis_perp)

    feasible = []
    full_touch = []
    for axis in axes:
        t_lo, t_hi = (lo, hi) if axis == axis_hint else _travel_bounds(geom.bounds, axis)
        for c in _centre_candidates(geom, axis, half_width, centre_hint):
            rect = rectify_band(geom, axis, c, half_width, t_lo, t_hi)
            if rect is None:
                continue
            feasible.append((axis, c, rect))
            if all(_access_len(rect, cell) >= touch_len for cell in cells):
                full_touch.append((axis, c, rect))

    if not feasible:
        raise Refusal("BAND_LT_3M")

    if full_touch:
        trimmed = []
        for axis, c, rect in full_touch:
            s, e = _band_span(axis, rect)

            def ok(a, b, axis=axis, c=c):
                r = set_precision(_band_rect(axis, c, half_width, a, b), 0.001)
                return all(_access_len(r, cell) >= touch_len for cell in cells)

            pe = pin_end if axis == axis_hint else None
            s2, e2 = _trim_span_to_predicate(s, e, ok, pin_end=pe)
            rect2 = set_precision(_band_rect(axis, c, half_width, s2, e2), 0.001)
            core = core_of(rect2) if (whole_cells and core_of is not None) else None
            n_whole = (sum(1 for cell in cells if _cell_whole(rect2, cell, touch_len, core=core))
                       if whole_cells else 0)
            trimmed.append((axis, c, rect2, e2 - s2, n_whole))

        def _tier_key(t):
            return (t[3], abs(t[1] - centre_hint), 0 if t[0] == axis_hint else 1)

        # T06 (1a): the whole tier ranks by *how many* cells the candidate leaves whole,
        # not only "all of them" -- a plate whose cells cannot all be kept whole by any
        # single band (e.g. one cell is inherently re-entrant on its own, D-EU-76 (b))
        # must not fall back to ignoring whole-ness for every other cell too. Still a
        # preference, never a gate: when whole_cells is False every count is 0, so every
        # candidate ties and the max-tier filter keeps them all -- today's behaviour,
        # byte-for-byte.
        max_whole = max((t[4] for t in trimmed), default=0)
        chosen = sorted((t for t in trimmed if t[4] == max_whole), key=_tier_key)
        axis, c, rect, _, _ = chosen[0]
        return {"chained": False, "band": rect, "axis": axis, "centre": c,
                "span": _band_span(axis, rect), "first": rect, "second": None, "full": True,
                "whole": chosen[0][4] == len(cells), "n_whole": chosen[0][4]}

    if axis_perp not in axes:
        raise Refusal("BAND_LT_3M")

    def touch_count(rect):
        return sum(1 for cell in cells if _access_len(rect, cell) >= touch_len)

    feasible.sort(key=lambda t: (-touch_count(t[2]), abs(t[1] - centre_hint), 0 if t[0] == axis_hint else 1))
    axis, c, rect = feasible[0]

    if allow_chain:
        chained = chain_second_band(geom, cells, axis, c, rect, half_width)
        if chained is not None:
            union, second = chained
            return {"chained": True, "band": union, "axis": axis, "centre": c,
                    "span": _band_span(axis, rect), "first": rect, "second": second, "full": False,
                    "whole": False, "n_whole": 0}

    return {"chained": False, "band": rect, "axis": axis, "centre": c,
            "span": _band_span(axis, rect), "first": rect, "second": None, "full": False,
            "whole": False, "n_whole": 0}


def chain_second_band(container, cells, first_axis, first_centre, first_rect, half_width):
    """D-EU-73 (e): chain, not tree. One perpendicular band joined end to end to
    `first_rect`, used only when no single band touches every cell. The second
    band's centre is restricted to the two candidates that land its centreline on
    the first band's own end (`s + half_width`, `e - half_width`) -- forcing the
    joint to an end, so the result is an L, never a T or a cross (`D-EU-73` (e)).
    Never a spur: `_connector`/`_bridge` are not called from this path. Returns
    `(union_polygon, second_rect)`, or `None` when neither candidate improves on
    the first band's own touch count -- the caller then keeps the single band."""
    geom = _single_polygon(container)
    if geom is None:
        return None

    second_axis = "y" if first_axis == "x" else "x"
    lo2, hi2 = _travel_bounds(geom.bounds, second_axis)
    s, e = _band_span(first_axis, first_rect)
    base_touch = sum(1 for cell in cells if _touches(first_rect, cell))

    best = None
    for c2 in (s + half_width, e - half_width):
        rect2 = rectify_band(geom, second_axis, c2, half_width, lo2, hi2)
        if rect2 is None:
            continue
        union = _polygons_only(set_precision(unary_union([first_rect, rect2]), 0.001))
        if union.geom_type != "Polygon" or union.is_empty:
            continue
        touch = sum(1 for cell in cells if _touches(union, cell))
        s2, e2 = _band_span(second_axis, rect2)
        cand = (touch, -(e2 - s2), c2, rect2)
        if best is None or cand[:2] > best[:2]:
            best = cand

    if best is None or best[0] <= base_touch:
        return None

    touch, _neg_len, c2, rect2 = best
    s2, e2 = _band_span(second_axis, rect2)

    def ok(a, b):
        r2 = set_precision(_band_rect(second_axis, c2, half_width, a, b), 0.001)
        if not _touches(r2, first_rect):
            return False
        u = _polygons_only(set_precision(unary_union([first_rect, r2]), 0.001))
        if u.geom_type != "Polygon":
            return False
        return sum(1 for cell in cells if _touches(u, cell)) >= touch

    s2t, e2t = _trim_span_to_predicate(s2, e2, ok)
    rect2_trim = set_precision(_band_rect(second_axis, c2, half_width, s2t, e2t), 0.001)
    union_trim = _polygons_only(set_precision(unary_union([first_rect, rect2_trim]), 0.001))
    if union_trim.geom_type != "Polygon" or union_trim.is_empty:
        return _polygons_only(set_precision(unary_union([first_rect, rect2]), 0.001)), rect2
    return union_trim, rect2_trim


def solve_band_free(container, cells, centre_hint, half_width, lo, hi, whole_cells=False, core_of=None):
    """D-EU-75 (b): the corridor's bearing comes from the footprint's own edges, not
    the plate's local axis. Candidate bearings are the container's own exterior-ring
    edge directions, reduced modulo 90 into [0, 90) and rounded to 0.5 degrees
    (always including 0.0, so today's axis-aligned answer stays a candidate), capped
    at 12 by keeping the angles belonging to the longest edges. For each bearing the
    problem is rotated about the container's own centroid so that bearing becomes
    axis "x", solved with `solve_band` (`bearings=("x", "y")`, `allow_chain=False` --
    D-EU-75 (a): no chain, no ring, no second band), and the winning band rotated
    back. Selection keeps the bearing whose band is `"full": True` and shortest,
    tie-broken by smaller `|theta|` then by lower `theta`; if none is full, the
    bearing whose band touches the most cells, same tie-break.

    `lo`/`hi` are accepted for signature parity with `solve_band` (same arguments
    minus `axis_hint`) but not used: they are bounds in the *unrotated* frame and
    cannot be mapped onto an arbitrary rotated frame, so every bearing's own travel
    window is that rotated container's own bounds instead (pinned by this task).
    `whole_cells` (T06): forwarded to `solve_band` unchanged, every bearing tried.
    `core_of` (T06, D-EU-76 (a)): a callback in *this function's own, unrotated*
    frame -- given a candidate band already in that frame, returns the core the
    caller will plant on it. Wrapped per bearing (rotate the trial band out to this
    frame, call it, rotate its answer back in) before being forwarded to
    `solve_band`, so every bearing's whole-cell test sees the same core it would
    actually get were that bearing chosen."""
    geom = _single_polygon(container)
    if geom is None:
        raise Refusal("BAND_LT_3M")

    pivot = geom.centroid

    angle_len = {}
    coords = list(geom.exterior.coords)
    for i in range(len(coords) - 1):
        x0, y0 = coords[i]
        x1, y1 = coords[i + 1]
        length = math.hypot(x1 - x0, y1 - y0)
        if length <= 1.0:
            continue
        ang = round((math.degrees(math.atan2(y1 - y0, x1 - x0)) % 90.0) * 2) / 2.0
        if ang >= 90.0:
            ang -= 90.0
        angle_len[ang] = max(angle_len.get(ang, 0.0), length)
    angle_len.setdefault(0.0, 0.0)
    if len(angle_len) > 12:
        others = sorted((a for a in angle_len if a != 0.0), key=lambda a: -angle_len[a])
        keep = set(others[:11]) | {0.0}
        angle_len = {a: v for a, v in angle_len.items() if a in keep}
    thetas = sorted(angle_len.keys())

    hint_pt = Point(pivot.x, centre_hint)

    full_candidates = []
    partial_candidates = []
    for theta in thetas:
        rot_container = rotate(geom, -theta, origin=(pivot.x, pivot.y))
        rot_cells = [rotate(c, -theta, origin=(pivot.x, pivot.y)) for c in cells]
        rot_hint = rotate(hint_pt, -theta, origin=(pivot.x, pivot.y))
        rlo, rhi = _travel_bounds(rot_container.bounds, "x")

        def rot_core_of(rect_rot, theta=theta):
            if core_of is None:
                return None
            rect_outer = rotate(rect_rot, theta, origin=(pivot.x, pivot.y))
            core_outer = core_of(rect_outer)
            if core_outer is None or core_outer.is_empty:
                return None
            return rotate(core_outer, -theta, origin=(pivot.x, pivot.y))

        try:
            solved = solve_band(rot_container, rot_cells, "x", rot_hint.y, half_width, rlo, rhi,
                                 bearings=("x", "y"), allow_chain=False, touch_len=ACCESS_MIN_M,
                                 whole_cells=whole_cells,
                                 core_of=rot_core_of if core_of is not None else None)
        except Refusal:
            continue
        span = solved["span"]
        length = span[1] - span[0]
        if solved["full"]:
            # T06 (1b): rank bearings by how many cells their own chosen candidate
            # left whole, not only by whether it left *all* of them whole -- the
            # same D-EU-76 (a) generalisation as the per-bearing tier itself
            # (solve_band's own `n_whole`), else a bearing that is best-possible but
            # not perfect loses to a shorter bearing that is whole for fewer cells.
            full_candidates.append((-solved.get("n_whole", 0), length, abs(theta), theta, theta, solved))
        else:
            touch = sum(1 for cell in rot_cells if _touches(solved["band"], cell))
            partial_candidates.append((-touch, abs(theta), theta, theta, solved))

    if full_candidates:
        full_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
        theta = full_candidates[0][4]
        solved = full_candidates[0][5]
    elif partial_candidates:
        partial_candidates.sort(key=lambda t: (t[0], t[1], t[2]))
        theta = partial_candidates[0][3]
        solved = partial_candidates[0][4]
    else:
        raise Refusal("BAND_LT_3M")

    band_world = set_precision(rotate(solved["band"], theta, origin=(pivot.x, pivot.y)), 0.001)
    return {"band": band_world, "theta": theta, "full": solved["full"]}


def _connector(part, hub, width=CORRIDOR_W):
    if part.is_empty or hub.is_empty:
        return None
    shared = part.intersection(hub)
    if shared.length > 0.05 or shared.area > 1e-4:
        return None
    p1, p2 = nearest_points(part, hub)
    if p1.distance(p2) < 1e-6:
        return box(p1.x - width / 2, p1.y - width / 2, p1.x + width / 2, p1.y + width / 2)
    line = LineString([(p1.x, p1.y), (p2.x, p2.y)])
    return line.buffer(width / 2, cap_style="square", join_style="mitre")


def _touches(a, b):
    """T06a(3)/(4): the same touch test _connector uses, exposed for pre-checks."""
    shared = a.intersection(b)
    return shared.length > 0.05 or shared.area > 1e-4


def _access_len(band, cell):
    """D-EU-77: score contact exactly as C8 does (04_group_tests.py:308-309) --
    the real shared edge against the band's boundary, 1 cm tolerance, no wider buffer."""
    if band is None or cell is None or band.is_empty or cell.is_empty:
        return 0.0
    buffered = cell.buffer(0.01, cap_style=3, join_style=2)
    if band.geom_type == "MultiPolygon":
        return sum(buffered.intersection(g.exterior).length for g in band.geoms)
    return buffered.intersection(band.exterior).length


def _cell_whole(band, cell, touch_len, core=None):
    """T06 (1): D-EU-76 (a) checked where the band is chosen, not repaired after the
    cut. A band leaves `cell` whole when the remainder cell.difference(band) is a
    single Polygon of area >= SCRAP_M2, with contact >= touch_len against that
    remainder -- measured against the remainder, not the cell, the way C8 will
    measure it later. `core` (T06): when the caller also plants a core box onto the
    band's own centroid after the band is chosen, that core is what actually slices
    a cell the band alone left whole (FINDING 230) -- so when given, the whole-cell
    test subtracts `band ∪ core` instead of `band` alone, and contact is measured
    against that same union, matching what `circ_local` will be once the core lands."""
    subtract = band if core is None or core.is_empty else _polygons_only(unary_union([band, core]))
    rem = _polygons_only(cell.difference(subtract))
    if rem.geom_type != "Polygon" or rem.area < SCRAP_M2:
        return False
    return _access_len(subtract, rem) >= touch_len


def _bridge(hub, others, poly):
    """T06a(4): grow hub by unioning `others` one at a time, skipping a connector for
    any part that already touches the union built so far (never a redundant connector
    between two parts already joined through a third part)."""
    running = hub
    extra = [hub]
    for part in others:
        link = None if _touches(part, running) else _connector(part, running)
        extra.append(part)
        if link is not None:
            extra.append(set_precision(link.intersection(poly), 0.001))
        merged = _safe_union(extra)
        if merged is not None:
            running = merged if merged.geom_type == "Polygon" else max(merged.geoms, key=lambda g: g.area)
    return _polygons_only(set_precision(unary_union(extra).intersection(poly), 0.001))


def _ensure_flat_access(poly, flats, circ):
    """T03/D-EU-70: no orphan flat. Any flat scoring < ACCESS_MIN_M against `circ`
    under `_access_len` (D-EU-77) gets a CORRIDOR_W spur from `circ` via `_connector`,
    with the spur's area carved out of whichever flats it crosses. A candidate is
    accepted only if it keeps `circ` a single Polygon (C2), keeps every flat it
    touches a single Polygon of area >= SCRAP_M2 (never orphaning a piece, C4), keeps
    full coverage of `poly` (C1), and actually lifts the target flat's own access to
    >= ACCESS_MIN_M -- otherwise the flat is left exactly as it was, to fail C8
    honestly rather than be forced."""
    if circ is None or circ.is_empty:
        return flats, circ
    flats = list(flats)

    def _drop_slivers(g):
        if g.geom_type != "MultiPolygon":
            return g
        parts = [p for p in g.geoms if p.area >= SCRAP_M2]
        if len(parts) == 1:
            return parts[0]
        if not parts:
            return Polygon()
        return unary_union(parts)

    for i in range(len(flats)):
        if _access_len(circ, flats[i]) >= ACCESS_MIN_M:
            continue
        spur = _connector(flats[i], circ, width=CORRIDOR_W)
        if spur is None:
            continue
        spur = _drop_slivers(_polygons_only(set_precision(spur.intersection(poly), 0.001)))
        if spur.is_empty or spur.geom_type != "Polygon":
            continue
        new_circ = _safe_union([circ, spur])
        if new_circ is None or new_circ.geom_type != "Polygon" or len(new_circ.interiors) > 0:
            continue
        trial = list(flats)
        ok = True
        for j, g in enumerate(trial):
            if not spur.intersects(g) or spur.intersection(g).area < 1e-6:
                continue
            trimmed = _drop_slivers(_polygons_only(set_precision(g.difference(spur), 0.001)))
            if trimmed.is_empty or trimmed.geom_type != "Polygon" or trimmed.area < SCRAP_M2:
                ok = False
                break
            trial[j] = trimmed
        if not ok:
            continue
        if _access_len(new_circ, trial[i]) < ACCESS_MIN_M:
            continue
        total_cov = sum(f.area for f in trial) + new_circ.area
        if total_cov < 0.999 * poly.area:
            continue
        flats = trial
        circ = new_circ
    return flats, circ


_NARROW_PROBES_M = [4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5]


def _widest_fit(zone):
    """T05b: mirrors 04_group_tests.py:298 widest_fit exactly -- used only so a
    candidate redraw cannot silently create a new C10 failure."""
    for w in _NARROW_PROBES_M:
        if not zone.buffer(-w / 2).is_empty:
            return w
    return 0.0


def _valid_geom(g):
    if g.is_empty:
        return g
    if not g.is_valid:
        g = make_valid(g)
    return set_precision(g, 0.001)


def _polygon_pieces(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g] if g.area > 1e-9 else []
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and p.area > 1e-9]


def _apply_corridor_delta(poly, flats, old_circ, cand):
    """T05b/D-EU-78: accept `cand` as the new corridor only by *donating* the area
    difference against `old_circ` to the adjacent flats instead of dropping it --
    corridor growth is carved out of the one flat whose own territory the growth ate
    into; corridor shrinkage is unioned into the flat with the longest real shared
    edge against the vacated strip (scored exactly as C8/D-EU-77 does). Nothing is
    ever deleted, only moved, so C1 stays exact by construction. Returns the new
    flat list, or None if any hard check the redraw can move would break (C1, C2,
    C4, C8, C10) -- C9 is the caller's own concern."""
    gained = _valid_geom(cand.difference(old_circ))
    lost = _valid_geom(old_circ.difference(cand))
    trial = list(flats)

    for piece in _polygon_pieces(gained):
        best_i, best_area = None, 1e-9
        for i, f in enumerate(trial):
            ov = f.intersection(piece).area
            if ov > best_area:
                best_area, best_i = ov, i
        if best_i is None:
            return None
        trimmed = _valid_geom(trial[best_i].difference(piece))
        if trimmed.geom_type != "Polygon" or trimmed.is_empty or trimmed.area < SCRAP_M2 or len(trimmed.interiors) > 0:
            return None
        trial[best_i] = trimmed

    for piece in _polygon_pieces(lost):
        best_i, best_len = None, -1.0
        for i, f in enumerate(trial):
            edge = f.buffer(0.01, cap_style=3, join_style=2).intersection(piece.exterior).length
            if edge > best_len:
                best_len, best_i = edge, i
        if best_i is None or best_len <= 1e-9:
            return None
        merged = _valid_geom(unary_union([trial[best_i], piece]))
        if merged.geom_type != "Polygon" or merged.is_empty or len(merged.interiors) > 0:
            return None
        trial[best_i] = merged

    if any(f.geom_type != "Polygon" or f.is_empty or f.area < SCRAP_M2 or len(f.interiors) > 0 for f in trial):
        return None
    if any(f.intersection(cand).area >= 0.02 for f in trial):
        return None
    for i in range(len(trial)):
        for j in range(i + 1, len(trial)):
            if trial[i].intersection(trial[j]).area >= 0.02:
                return None
    if any(lobes_of(f) is not None for f in trial):
        return None
    cov = (sum(f.area for f in trial) + cand.area) / poly.area if poly.area else 0.0
    if not (0.999 <= cov <= 1.001):
        return None
    if any(_access_len(cand, f) < ACCESS_MIN_M for f in trial):
        return None
    if _widest_fit(cand) < C10_MIN_WIDTH_M:
        return None
    return trial


_RECTIFY_GUARD_STEPS = 200


def _rectify_and_reassign(poly, flats, circ):
    """T05b/D-EU-78: closes C9 on the plates the plain near-zero-change denoise
    (`_denoise_corridor`) cannot reach, because by the time it runs post-`finish()`
    the flats are already fixed and it has nowhere to put the area it would remove.
    T05's own attempt (`Polygon.simplify()` alone, and later at a single escalating
    tolerance) is dead: `simplify()` reshapes the ring globally, so even a `cand` with
    few enough points can differ from the old ring across a swath far from any real
    noise, splitting a flat it merely passes near into a disconnected piece -- the
    same "either loses area or bulges out" failure the plan already ruled out, just
    relocated into the donation step.

    This is a different transform, one vertex at a time: repeatedly drop the ring
    vertex whose removal changes the least area (the triangle it and its two
    neighbours form) -- that is always the local jog/staircase noise, never a real
    corner, because a real corner's triangle is large. Each removal's area delta is
    therefore a single small, local piece, and `_apply_corridor_delta` donates that
    piece to the flat that actually borders it (corridor growth taken from the one
    flat whose territory it ate; corridor shrinkage given to the flat with the
    longest real shared edge against it) -- never a distant, unrelated flat. Stops
    the moment a removal cannot be validated (tries the next-least-area vertex
    instead) or no vertex can be safely removed. Accepted as a whole only if the
    final ring is <= CORRIDOR_MAX_POINTS -- no partial credit, per plan text: a
    plate that cannot be fully closed is left exactly as drawn."""
    if circ is None or circ.is_empty:
        return flats, circ
    if len(circ.exterior.coords) - 1 <= CORRIDOR_MAX_POINTS:
        return flats, circ

    cur_flats = list(flats)
    cur_circ = circ
    cur_ring = list(circ.exterior.coords)[:-1]
    changed = False

    for _ in range(_RECTIFY_GUARD_STEPS):
        if len(cur_ring) <= CORRIDOR_MAX_POINTS:
            break
        n = len(cur_ring)
        if n <= 4:
            break
        order = sorted(
            range(n),
            key=lambda i: Polygon([cur_ring[(i - 1) % n], cur_ring[i], cur_ring[(i + 1) % n]]).area,
        )
        applied = False
        for i in order:
            new_ring = cur_ring[:i] + cur_ring[i + 1:]
            if len(new_ring) < 4:
                continue
            cand = _valid_geom(Polygon(new_ring))
            if cand.geom_type != "Polygon" or cand.is_empty or len(cand.interiors) > 0:
                continue
            cand = _valid_geom(cand.intersection(poly))
            if cand.geom_type != "Polygon" or cand.is_empty or len(cand.interiors) > 0:
                continue
            n1 = len(cand.exterior.coords) - 1
            if n1 >= n:
                continue
            trial_flats = _apply_corridor_delta(poly, cur_flats, cur_circ, cand)
            if trial_flats is None:
                continue
            cur_flats, cur_circ = trial_flats, cand
            cur_ring = list(cur_circ.exterior.coords)[:-1]
            applied = True
            changed = True
            break
        if not applied:
            break

    if changed and len(cur_ring) <= CORRIDOR_MAX_POINTS:
        return cur_flats, cur_circ
    return flats, circ


# T07/FINDING 237: mirrors 04_group_tests.py's own C5 cap (max_pts <= 40) read-only --
# never changes the check, only lets the donation below refuse a candidate that would
# fail it, and gives it one honest way to shed sub-metre weld noise instead.
_DELOBE_FLAT_MAX_PTS = 40


def _shed_vertices(shape, max_pts):
    """T07: a flat formed by donating a whole lobe elsewhere (see `_try_keep` below)
    inherits both parents' full corner counts, which can read over C5's own point cap
    even when most of the added corners are sub-metre weld noise, not real facade.
    Repeatedly drops the single ring vertex whose own triangle (with its two immediate
    neighbours) has the least area -- the same local, least-area method
    `_rectify_and_reassign` already uses for circ, generalised to any polygon -- until
    the ring is at or under `max_pts` or no further vertex can be dropped without
    breaking validity. The caller's own `_ok` coverage gate (0.999-1.001 of the
    footprint) is the only budget for the tiny area this can shift; a shape this
    cannot bring under `max_pts` is returned unchanged and `_ok` rejects it downstream."""
    if shape.geom_type != "Polygon" or len(shape.interiors) > 0:
        return shape
    coords = list(shape.exterior.coords[:-1])
    while len(coords) > max_pts and len(coords) > 4:
        n = len(coords)
        areas = []
        for i in range(n):
            a, b, c = coords[(i - 1) % n], coords[i], coords[(i + 1) % n]
            areas.append((abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0, i))
        areas.sort(key=lambda t: t[0])
        dropped = False
        for _, i in areas:
            cand = _valid_geom(Polygon(coords[:i] + coords[i + 1:]))
            if cand.geom_type == "Polygon" and cand.is_valid and len(cand.interiors) == 0:
                coords = list(cand.exterior.coords[:-1])
                dropped = True
                break
        if not dropped:
            break
    return _valid_geom(Polygon(coords)) if len(coords) >= 4 else shape


def _delobe_and_donate(poly, flats, circ):
    """T06b/D-EU-76 (b), the last three plates: T06 proved these three are not the
    circulation's doing (heal > lobes on all of them) -- the flat's own outline is
    re-entrant across a neck under 2*NECK_R. `lobes_of` (02's own test, reused
    read-only, same precedent as D-EU-78) already does step 1 for us: erode by NECK_R,
    keep components > 0.5 m^2, re-inflate each back inside the flat so the pieces
    partition it exactly. Keep the largest piece as the flat; donate every other piece
    to the neighbouring flat with the longest real shared edge against it, scored by
    the same formula C8/D-EU-77 uses (`_access_len`) -- never to circ, nothing is ever
    deleted, so C1 holds by construction. A donation is kept only if the whole plate
    still passes C1/C2/C4/C8/C9/C10 afterwards; otherwise the next-best neighbour is
    tried, and if none works the flat is left exactly as cut.

    T07/FINDING 237: keeping the largest lobe can itself fail C8 -- on a 2-flat
    courtyard the largest lobe can carry none of the flat's circulation contact
    while a smaller lobe carries all of it, so donating the smaller one away always
    leaves the retained (largest) piece an orphan and the whole attempt is refused.
    Only when the largest-first attempt above fails outright does this now retry
    with the *other* lobes as the kept piece, in order of their own access to
    `circ` (best first) -- never widening any check, only choosing which lobe is
    the flat when the default choice cannot pass at all."""

    def _ok(trial_flats, zone):
        if any(f.geom_type != "Polygon" or f.is_empty or f.area < SCRAP_M2 or len(f.interiors) > 0
               for f in trial_flats):
            return False
        if any((len(f.exterior.coords) - 1) > _DELOBE_FLAT_MAX_PTS for f in trial_flats):
            return False
        if zone is not None and (zone.geom_type != "Polygon" or zone.is_empty or len(zone.interiors) > 0):
            return False
        total = sum(f.area for f in trial_flats) + (zone.area if zone is not None else 0.0)
        cov = total / poly.area if poly.area else 0.0
        if not (0.999 <= cov <= 1.001):
            return False
        if any(lobes_of(f) is not None for f in trial_flats):
            return False
        if zone is not None:
            if any(_access_len(zone, f) < ACCESS_MIN_M for f in trial_flats):
                return False
            if (len(zone.exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
                return False
            if _widest_fit(zone) < C10_MIN_WIDTH_M:
                return False
        return True

    def _try_keep(base_flats, i, lobes, keep_idx):
        trial = list(base_flats)
        trial[i] = lobes[keep_idx]
        for pidx, piece in enumerate(lobes):
            if pidx == keep_idx:
                continue
            order = sorted(
                (j for j in range(len(trial)) if j != i),
                key=lambda j: _access_len(trial[j], piece),
                reverse=True,
            )
            donated = False
            for j in order:
                merged = _safe_union([trial[j], piece])
                if merged is None:
                    continue
                merged = _valid_geom(merged)
                if merged.geom_type != "Polygon" or merged.is_empty:
                    continue
                if (len(merged.exterior.coords) - 1) > _DELOBE_FLAT_MAX_PTS:
                    merged = _shed_vertices(merged, _DELOBE_FLAT_MAX_PTS)
                candidate = list(trial)
                candidate[j] = merged
                if _ok(candidate, circ):
                    trial = candidate
                    donated = True
                    break
            if not donated:
                return None
        return trial if _ok(trial, circ) else None

    flats = list(flats)
    for i in range(len(flats)):
        lobes = lobes_of(flats[i])
        if not lobes:
            continue
        trial = _try_keep(flats, i, lobes, 0)
        if trial is None and len(lobes) > 1 and circ is not None and not circ.is_empty:
            alt_order = sorted(range(1, len(lobes)), key=lambda idx: _access_len(circ, lobes[idx]), reverse=True)
            for keep_idx in alt_order:
                trial = _try_keep(flats, i, lobes, keep_idx)
                if trial is not None:
                    break
        if trial is not None:
            flats = trial
    return flats, circ


_CORRIDOR_REACH_RADII_M = [0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
_CORRIDOR_REACH_MARGIN_M = 0.10


def _corridor_reach(poly, flats, circ):
    """T06c mechanism (2), run first (before mechanism (1) below): D-EU-70, the
    corridor touches every flat. Where a flat is still lobed after
    `_delobe_and_donate` above has already rolled back *and* is starved of contact
    (< ACCESS_MIN_M, D-EU-77's own metric), grow `circ` toward that flat -- taking
    the grown area only from that flat, at the smallest tried radius that lifts its
    contact past ACCESS_MIN_M with a small margin -- rather than widening a neck
    the corridor itself should have reached. Nothing is ever deleted, so C1 stays
    exact by construction. Accepted only if `circ` stays one Polygon (C2) with
    corner points <= CORRIDOR_MAX_POINTS (C9) and min width >= C10_MIN_WIDTH_M
    (C10), the shrunken flat stays a single Polygon of area >= SCRAP_M2 (C4), and
    every flat's own contact with the grown corridor is still >= ACCESS_MIN_M (C8)
    -- otherwise the next radius is tried, and if none works the flat is left
    exactly as cut.

    T07/FINDING 236 follow-up: a flat that meets `circ` at a bare corner (plate 33's
    F3, `IT-BOL-GALVANI2 29891`) has almost none of its own territory near `circ`,
    so growing into the flat itself above can lift only a negligible amount of
    contact at any radius -- confirmed by direct measurement (max ~0.6 m^2 even at
    5 m). `circ` needs a real face against the flat, and the only place one can come
    from is whichever *other* flat is currently wedged between them. When the
    same-flat loop above still leaves a lobed flat starved, retry growing `circ`
    into each other flat in turn, same radii, same acceptance bar (`_ok` already
    checks every flat's own access, so a neighbour's remaining contact is guarded
    too) -- the starved flat's own area is never touched by this second pass."""
    if circ is None or circ.is_empty:
        return flats, circ
    flats = list(flats)

    def _ok(trial_flats, zone):
        if zone is None or zone.geom_type != "Polygon" or zone.is_empty or len(zone.interiors) > 0:
            return False
        if any(f.geom_type != "Polygon" or f.is_empty or f.area < SCRAP_M2 or len(f.interiors) > 0
               for f in trial_flats):
            return False
        total = sum(f.area for f in trial_flats) + zone.area
        cov = total / poly.area if poly.area else 0.0
        if not (0.999 <= cov <= 1.001):
            return False
        if (len(zone.exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
            return False
        if _widest_fit(zone) < C10_MIN_WIDTH_M:
            return False
        if any(_access_len(zone, f) < ACCESS_MIN_M for f in trial_flats):
            return False
        return True

    target = ACCESS_MIN_M + _CORRIDOR_REACH_MARGIN_M
    for i in range(len(flats)):
        if lobes_of(flats[i]) is None:
            continue
        if _access_len(circ, flats[i]) >= ACCESS_MIN_M:
            continue
        resolved = False
        for r in _CORRIDOR_REACH_RADII_M:
            grow = _valid_geom(circ.buffer(r, cap_style=3, join_style=2).intersection(flats[i]).intersection(poly))
            if grow.is_empty:
                continue
            new_flat = _valid_geom(flats[i].difference(grow))
            if new_flat.geom_type != "Polygon" or new_flat.is_empty or new_flat.area < SCRAP_M2 or len(new_flat.interiors) > 0:
                continue
            new_circ = _valid_geom(unary_union([circ, grow]))
            if new_circ.geom_type != "Polygon" or new_circ.is_empty:
                continue
            if _access_len(new_circ, new_flat) < target:
                continue
            trial = list(flats)
            trial[i] = new_flat
            if not _ok(trial, new_circ):
                continue
            flats = trial
            circ = new_circ
            resolved = True
            break
        if resolved:
            continue
        for j in range(len(flats)):
            if j == i:
                continue
            for r in _CORRIDOR_REACH_RADII_M:
                grow = _valid_geom(circ.buffer(r, cap_style=3, join_style=2).intersection(flats[j]).intersection(poly))
                if grow.is_empty:
                    continue
                new_donor = _valid_geom(flats[j].difference(grow))
                if new_donor.geom_type != "Polygon" or new_donor.is_empty or new_donor.area < SCRAP_M2 or len(new_donor.interiors) > 0:
                    continue
                if lobes_of(new_donor) is not None:
                    continue
                new_circ = _valid_geom(unary_union([circ, grow]))
                if new_circ.geom_type != "Polygon" or new_circ.is_empty:
                    continue
                if _access_len(new_circ, flats[i]) < target:
                    continue
                trial = list(flats)
                trial[j] = new_donor
                if not _ok(trial, new_circ):
                    continue
                flats = trial
                circ = new_circ
                resolved = True
                break
            if resolved:
                break
    return flats, circ


def _delobe_by_absorption(poly, flats, circ):
    """T06c mechanism (1), run second: D-EU-76 (b) from the other side of T06b's
    donation. Where a flat is still lobed after `_delobe_and_donate` and
    `_corridor_reach` above have already rolled back, its *larger* lobe is the one
    starved of contact, so amputating it (T06b's method) only fails C8 again. Keep
    the flat whole instead: bridge its two lobes along the shortest line between
    them, widened to >= 2*NECK_R + 0.1 m -- the same erosion radius `lobes_of`
    itself uses to find the neck -- and absorb that bridge from whichever single
    neighbour (flat or circ) currently owns it, most-overlapping candidate first.
    Nothing is ever deleted, so C1 stays exact by construction. A donation is kept
    only if it actually heals the flat (`lobes_of` returns None), the donor stays
    valid (a flat donor: single lobe, C4; circ donor: single polygon, C2/C9/C10),
    and the whole plate still passes C1/C2/C4/C8/C9/C10 afterwards -- otherwise the
    next donor is tried, and if none works the flat is left exactly as cut."""

    def _ok(trial_flats, zone):
        if any(f.geom_type != "Polygon" or f.is_empty or f.area < SCRAP_M2 or len(f.interiors) > 0
               for f in trial_flats):
            return False
        if zone is not None and (zone.geom_type != "Polygon" or zone.is_empty or len(zone.interiors) > 0):
            return False
        total = sum(f.area for f in trial_flats) + (zone.area if zone is not None else 0.0)
        cov = total / poly.area if poly.area else 0.0
        if not (0.999 <= cov <= 1.001):
            return False
        if any(lobes_of(f) is not None for f in trial_flats):
            return False
        if zone is not None:
            if any(_access_len(zone, f) < ACCESS_MIN_M for f in trial_flats):
                return False
            if (len(zone.exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
                return False
            if _widest_fit(zone) < C10_MIN_WIDTH_M:
                return False
        return True

    flats = list(flats)
    neck_target = 2 * NECK_R + 0.1
    for i in range(len(flats)):
        lobes = lobes_of(flats[i])
        if lobes is None or len(lobes) != 2:
            continue
        big, small = lobes[0], lobes[1]
        p1, p2 = nearest_points(big, small)
        if p1.distance(p2) < 1e-9:
            bridge = p1.buffer(neck_target / 2, cap_style=3, join_style=2)
        else:
            line = LineString([(p1.x, p1.y), (p2.x, p2.y)])
            bridge = line.buffer(neck_target / 2, cap_style=3, join_style=2)
        bridge = _valid_geom(bridge.intersection(poly))
        need = _valid_geom(bridge.difference(flats[i]))
        if need.is_empty:
            continue
        candidates = [("flat", j, flats[j]) for j in range(len(flats)) if j != i]
        if circ is not None and not circ.is_empty:
            candidates.append(("circ", None, circ))
        candidates.sort(key=lambda c: c[2].intersection(need).area, reverse=True)
        for kind, j, donor_poly in candidates:
            overlap = _valid_geom(donor_poly.intersection(need))
            if overlap.is_empty or overlap.area < 1e-6:
                continue
            new_flat = _valid_geom(unary_union([flats[i], overlap]))
            if new_flat.geom_type != "Polygon" or new_flat.is_empty:
                continue
            if lobes_of(new_flat) is not None:
                continue
            if kind == "flat":
                new_donor = _valid_geom(donor_poly.difference(overlap))
                if new_donor.geom_type != "Polygon" or new_donor.is_empty or new_donor.area < SCRAP_M2 or len(new_donor.interiors) > 0:
                    continue
                if lobes_of(new_donor) is not None:
                    continue
                trial = list(flats)
                trial[i] = new_flat
                trial[j] = new_donor
                if _ok(trial, circ):
                    flats = trial
                    break
            else:
                new_circ = _valid_geom(donor_poly.difference(overlap))
                if new_circ.geom_type != "Polygon" or new_circ.is_empty or len(new_circ.interiors) > 0:
                    continue
                trial = list(flats)
                trial[i] = new_flat
                if _ok(trial, new_circ):
                    flats = trial
                    circ = new_circ
                    break
    return flats, circ


def cut_courtyard(poly, k):
    """Sheet 01 steps 3-4: D-EU-67 connected cores at the void's corners, gallery ring."""
    interiors = [Polygon(r) for r in poly.interiors]
    if not interiors:
        raise Refusal("WING_TREE_FAILED")
    V = max(interiors, key=lambda g: g.area)
    secondary = [g for g in interiors if g is not V]

    theta, cx, cy, L, W = frame(V)
    a, b = L / 2, W / 2
    B = set_precision(to_local(poly, theta, cx, cy), 0.001)
    Vl = set_precision(to_local(V, theta, cx, cy), 0.001)
    secondary_l = [set_precision(to_local(g, theta, cx, cy), 0.001) for g in secondary]

    n_c_target = 1 if k == 1 else min(4, max(2, math.ceil(k / 3)))
    quads = sorted([(1, 1), (1, -1), (-1, 1), (-1, -1)],
                   key=lambda q: _quadrant_area(B, *q), reverse=True)

    def core_box(sx, sy):
        if sx > 0:
            x0, x1 = a + CORRIDOR_W, a + CORRIDOR_W + CORE_MIN_SIDE
        else:
            x0, x1 = -a - CORRIDOR_W - CORE_MIN_SIDE, -a - CORRIDOR_W
        if sy > 0:
            y0, y1 = b + CORRIDOR_W, b + CORRIDOR_W + CORE_MIN_SIDE
        else:
            y0, y1 = -b - CORRIDOR_W - CORE_MIN_SIDE, -b - CORRIDOR_W
        return box(x0, y0, x1, y1)

    # D-EU-75: the buffered ring is gone. Circulation is one single free-bearing band,
    # solved (never clipped) against the whole footprint B -- the void stays a void and
    # the band may cross it only where the plate is solid, which `rectify_band`'s own
    # containment test already guarantees. There is no pre-corridor flat partition for
    # a courtyard the way there is a grid for a rect or limbs for a wing, so the cells
    # the band is solved to touch are the `n_c_target` core sites themselves (D-EU-67:
    # cores attach to the band) -- not `[B]`, which would let "touches every cell"
    # trivially pass for any band, collapsing the minimum-length trim to near zero.
    minx, miny, maxx, maxy = B.bounds
    core_cells = [set_precision(core_box(sx, sy).intersection(B), 0.001) for sx, sy in quads[:n_c_target]]
    solved = solve_band_free(B, core_cells, B.centroid.y, CORRIDOR_W / 2, minx, maxx, whole_cells=True)
    band = solved["band"]

    cores = []
    for sx, sy in quads:
        if len(cores) >= n_c_target:
            break
        cb = set_precision(core_box(sx, sy).intersection(B), 0.001)
        if cb.area < 3.0 or not _touches(cb, band):
            cb2 = set_precision(translate(core_box(sx, sy), -sx * CORE_MIN_SIDE, 0).intersection(B), 0.001)
            if cb2.area >= 3.0:
                cores.append(cb2)
        else:
            cores.append(cb)
    if not cores:
        raise Refusal("WING_TREE_FAILED")
    n_c = len(cores)

    # D-EU-67: cores keep attaching to the band -- they never extend it.
    merged = _bridge(band, cores, B)
    circ_local = set_precision(merged.intersection(B), 0.001)
    if circ_local.geom_type != "Polygon":
        raise Refusal("WING_TREE_FAILED")
    if len(circ_local.interiors) > 0:
        raise Refusal("WING_TREE_FAILED")

    # T05/C9: the gallery ring's `.intersection(B)` above copies every real facade jog it
    # crosses into the ring outline (D-EU-71 cap of 16). Drop collinear/near-collinear
    # corners with the file's own DENOISE_TOL, computed before `Z` so the flats absorb
    # whatever area the simplified ring no longer claims -- coverage stays exact by
    # construction. Guarded: only kept when it does not poke outside the real footprint.
    simplified = set_precision(circ_local.simplify(DENOISE_TOL, preserve_topology=True), 0.001)
    if (simplified.geom_type == "Polygon" and len(simplified.interiors) == 0
            and simplified.difference(B).area < 1e-6):
        circ_local = simplified

    segs = _perimeter_segs("+x")
    corner_ts = _corner_ts(segs, a, b)
    P = sum((u1 - u0) * _side_len(s, a, b) for s, u0, u1 in segs)
    Z = B.difference(circ_local)

    if k == 1:
        flats_local = [Z]
    else:
        if P / k < MIN_FLAT_W:
            raise Refusal("BAND_LT_3M")
        forced = [0.0]
        for sv in secondary_l:
            vx, vy = sv.centroid.x, sv.centroid.y
            forced.append(_t_of_point(vx, vy, a, b, corner_ts, segs))
        ts = _distribute_cuts(forced, k, corner_ts, segs, a, b, Z, P)
        ts = _snap_to_corners(ts, corner_ts, P)
        ts = sorted(ts)
        bounds = ts + [ts[0] + P]
        lines = []
        for t in ts:
            pt, side = _point_at_t(t % P, segs, a, b)
            nx, ny = _side_normal(side)
            start = (pt[0] - nx * 0.3, pt[1] - ny * 0.3)
            lines.append(LineString([start, (pt[0] + nx * BIG, pt[1] + ny * BIG)]))
        split_result = split(Z, unary_union(lines))
        parts = [g for g in split_result.geoms if g.geom_type == "Polygon" and g.area > 1e-9]
        sector_parts = [[] for _ in range(k)]
        for part in parts:
            rp = part.representative_point()
            tp = _t_of_point(rp.x, rp.y, a, b, corner_ts, segs)
            if tp < bounds[0] - 1e-6:
                tp += P
            idx = k - 1
            for i in range(k):
                if bounds[i] - 1e-6 <= tp < bounds[i + 1]:
                    idx = i
                    break
            sector_parts[idx].append(part)
        flats_local = []
        for i in range(k):
            if not sector_parts[i]:
                raise Refusal("CELL_EMPTY")
            merged_sector = _safe_union(sector_parts[i])
            if merged_sector is None or merged_sector.is_empty:
                raise Refusal("CELL_EMPTY")
            flats_local.append(merged_sector)
        for f in flats_local:
            _, _, _, _fL, fW = frame(f)
            if fW < MIN_FLAT_W:
                raise Refusal("BAND_LT_3M")

    for sv in secondary_l:
        if not any(f.buffer(0.05).intersects(sv) for f in flats_local):
            raise Refusal("SECONDARY_VOID_UNCUT")

    access = [_shared_len_metric(f, circ_local) for f in flats_local] if k >= 2 else []
    min_access = min(access) if access else None

    flats_world = [to_world(f, theta, cx, cy) for f in flats_local]
    circ_world = to_world(circ_local, theta, cx, cy)
    total_cov = sum(f.area for f in flats_world) + circ_world.area
    assert total_cov >= 0.999 * poly.area, f"coverage {total_cov:.2f} < 0.999*{poly.area:.2f}"
    flats_world, circ_world = _ensure_flat_access(poly, flats_world, circ_world)
    out = finish(poly, flats_world, circ_world)
    out["scheme"] = "courtyard_cores_gallery"
    out["notes"] = {
        "n_cores": n_c,
        "access_min_m": round(min_access, 2) if min_access is not None else None,
        "unsnapped": out.get("unsnapped", 0),
    }
    return out


def _mrr_rectangularity(poly):
    mrr = poly.minimum_rotated_rectangle
    return poly.area / mrr.area if mrr.area > 1e-9 else 0.0


def _interior_angles_ccw(poly):
    poly = orient(poly, sign=1.0)
    coords = list(poly.exterior.coords)[:-1]
    n = len(coords)
    out = []
    for i in range(n):
        p0, p1, p2 = coords[i - 1], coords[i], coords[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        cross = e1[0] * e2[1] - e1[1] * e2[0]
        dot = e1[0] * e2[0] + e1[1] * e2[1]
        turn = math.degrees(math.atan2(cross, dot))
        out.append((180.0 - turn, p0, p1, p2))
    return out


def _split_once(piece):
    """Sheets 09-11 step 3: split a re-entrant piece at its sharpest reflex vertex."""
    reflex = [t for t in _interior_angles_ccw(piece) if t[0] > 180.0 + REFLEX_TOL_DEG]
    if not reflex:
        return None
    _, p0, p1, p2 = max(reflex, key=lambda t: t[0])

    def _unit(dx, dy):
        n = math.hypot(dx, dy)
        return (dx / n, dy / n) if n > 1e-9 else None

    candidates = []
    for d in (_unit(p1[0] - p0[0], p1[1] - p0[1]), _unit(p1[0] - p2[0], p1[1] - p2[1])):
        if d is None:
            continue
        far = (p1[0] + d[0] * BIG, p1[1] + d[1] * BIG)
        try:
            result = split(piece, LineString([p1, far]))
        except Exception:
            continue
        parts = [g for g in result.geoms if g.geom_type == "Polygon" and g.area > 1e-6]
        if len(parts) != 2 or min(pt.area for pt in parts) < MIN_WING_M2:
            continue
        rect = min(_mrr_rectangularity(pt) for pt in parts)
        candidates.append((rect, parts))
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])[1]


def _split_wings(poly):
    Q = poly.simplify(DENOISE_TOL, preserve_topology=True)
    if Q.geom_type != "Polygon":
        Q = max(Q.geoms, key=lambda g: g.area)
    pieces = [Q]
    finished = []
    while pieces:
        if len(finished) + len(pieces) > MAX_WING_PIECES:
            raise Refusal("WING_TREE_FAILED")
        piece = pieces.pop(0)
        parts = _split_once(piece)
        if parts is None:
            finished.append(piece)
        else:
            pieces.extend(parts)
    if len(finished) > MAX_WING_PIECES or not finished:
        raise Refusal("WING_TREE_FAILED")
    return finished


def _reclaim_denoise_loss(wings, poly):
    """The Q=simplify(poly) split can shave a sliver of the true poly off every wing; give it back."""
    wings = list(wings)
    residual = poly.difference(unary_union(wings))
    if residual.is_empty:
        return wings
    parts = [residual] if residual.geom_type == "Polygon" else list(residual.geoms)
    for part in parts:
        if part.area <= SCRAP_M2:
            continue
        j = max(range(len(wings)), key=lambda i: _shared_len_metric(part, wings[i]))
        merged = _safe_union([wings[j], part])
        if merged is not None:
            wings[j] = merged if merged.geom_type == "Polygon" else max(merged.geoms, key=lambda g: g.area)
    return wings


def _absorb_bays(wings):
    """Sheets 09-11 step 4: fold a too-small or too-narrow piece into its best neighbour."""
    wings = list(wings)
    changed = True
    while changed and len(wings) > 1:
        changed = False
        for i in range(len(wings)):
            w = wings[i]
            _, _, _, _L, W = frame(w)
            if w.area >= MIN_WING_M2 and W >= MIN_WING_W:
                continue
            others = [j for j in range(len(wings)) if j != i]
            j_best = max(others, key=lambda j: _shared_len_metric(w, wings[j]))
            merged = _safe_union([w, wings[j_best]])
            if merged is None:
                continue
            if merged.geom_type != "Polygon":
                merged = max(merged.geoms, key=lambda g: g.area)
            wings = [wings[k] for k in range(len(wings)) if k not in (i, j_best)] + [merged]
            changed = True
            break
    return wings


def _wing_tree(wings):
    """Sheets 09-11 step 5: root = largest wing, parent = strongest in-tree adjacency."""
    n = len(wings)
    if n == 1:
        return 0, {0: None}
    adj = {}
    for i in range(n):
        for j in range(i + 1, n):
            shared = _shared_len_metric(wings[i], wings[j])
            if shared > 1.0:
                adj[(i, j)] = adj[(j, i)] = shared
    root = max(range(n), key=lambda i: wings[i].area)
    parent = {root: None}
    in_tree = {root}
    remaining = set(range(n)) - {root}
    while remaining:
        best = None
        for j in remaining:
            for i in in_tree:
                w = adj.get((i, j))
                if w and (best is None or w > best[2]):
                    best = (i, j, w)
        if best is None:
            raise Refusal("WING_TREE_FAILED")
        i, j, _w = best
        parent[j] = i
        in_tree.add(j)
        remaining.discard(j)
    return root, parent


def _reduce_to_k_wings(wings, k):
    """Sheets 09-11 step 6: fewer flats than wings -- fold the smallest into its parent.

    T06 (b), D-EU-76 (b)/FINDING 236: the tree parent is only the *strongest*
    adjacency; folding the smallest wing into it can weld two pieces across a neck
    narrower than `lobes_of`'s 0.75 m erosion, handing the eventual flat two wings
    joined by that neck (a merge, not a cut, does the damage here -- `lobes_of` runs
    on the merge itself before any corridor touches it). Every other current wing the
    smallest one actually borders (shared edge > 1 m) is tried too, in descending
    shared-edge order, and the first merge that comes back single-lobe is kept; only
    when none does is the strongest (tree-parent) merge kept regardless, so a plate
    that is genuinely un-splittable this way is unchanged, not refused (DD-4).

    Two wider searches were tried and dropped (FINDING 236): an exhaustive search
    over every merge order optimises the partition for lobe count alone, blind to
    where the corridor then lands, and traded plate 32's whole pass for a worse one
    while orphaning plate 33's F3 outright; trying every adjacent pair at each step
    (not only pairs touching the smallest wing) reproduced plate 32's original break
    and introduced a fresh C6 failure elsewhere. This narrower, single-neighbour
    fold is the one call site (T05/T05b) already exercised without regressing
    anything outside T06's own four target rows, so it is the kept behaviour."""
    wings = list(wings)
    while len(wings) > max(k, 1):
        root, parent = _wing_tree(wings)
        candidates = [i for i in range(len(wings)) if i != root]
        if not candidates:
            break
        smallest = min(candidates, key=lambda i: wings[i].area)
        p = parent[smallest]
        neighbours = sorted(
            (j for j in range(len(wings)) if j != smallest
             and _shared_len_metric(wings[smallest], wings[j]) > 1.0),
            key=lambda j: -_shared_len_metric(wings[smallest], wings[j]),
        )
        if p not in neighbours:
            neighbours = [p] + neighbours
        chosen = None
        for j in neighbours:
            trial = _safe_union([wings[smallest], wings[j]])
            if trial is None:
                continue
            trial = trial if trial.geom_type == "Polygon" else max(trial.geoms, key=lambda g: g.area)
            if lobes_of(trial) is None:
                chosen = (j, trial)
                break
        if chosen is None:
            merged = _safe_union([wings[smallest], wings[p]])
            if merged is None:
                raise Refusal("WING_TREE_FAILED")
            if merged.geom_type != "Polygon":
                merged = max(merged.geoms, key=lambda g: g.area)
            chosen = (p, merged)
        j, merged = chosen
        wings = [w for idx, w in enumerate(wings) if idx not in (smallest, j)] + [merged]
    return wings


def _alloc_k(wings, poly, k):
    """Sheets 09-11 step 6: k_w by largest-remainder on wing area, every wing >= 1;
    DD-6 caps each wing at its MIN_FLAT_W floor and moves any surplus to spare capacity."""
    n = len(wings)
    caps = []
    for w in wings:
        _, _, _, L_w, W_w = frame(w)
        m_max = 2 if (W_w - CORRIDOR_W) / 2 >= MIN_FLAT_W else 1
        caps.append(max(1, int(math.floor(L_w / MIN_FLAT_W)) * m_max))
    if sum(caps) < k:
        raise Refusal("BAND_LT_3M")

    if k <= n:
        k_w = [1] * n
    else:
        areas = [w.intersection(poly).area for w in wings]
        total = sum(areas) or 1.0
        extra_total = k - n
        raw = [extra_total * a / total for a in areas]
        extra = [int(math.floor(r)) for r in raw]
        rem = extra_total - sum(extra)
        order = sorted(range(n), key=lambda i: raw[i] - extra[i], reverse=True)
        for i in order[:max(0, rem)]:
            extra[i] += 1
        k_w = [1 + e for e in extra]

    changed = True
    while changed:
        changed = False
        surplus = 0
        for i in range(n):
            if k_w[i] > caps[i]:
                surplus += k_w[i] - caps[i]
                k_w[i] = caps[i]
                changed = True
        while surplus > 0:
            spare = [(caps[i] - k_w[i], i) for i in range(n) if caps[i] > k_w[i]]
            if not spare:
                raise Refusal("BAND_LT_3M")
            spare.sort(reverse=True)
            k_w[spare[0][1]] += 1
            surplus -= 1
    return k_w


def _wing_columns(w_local, N_w, forced_x, minx, maxx):
    """Sheets 09-11 step 7: forced boundaries at every child junction, the rest equal-area."""
    edge_pad = min(1.0, (maxx - minx) / 4.0)
    forced_all = []
    last = minx
    for x in sorted(set(round(v, 6) for v in forced_x)):
        if x - last > edge_pad and maxx - x > edge_pad:
            forced_all.append(x)
            last = x
    if len(forced_all) > max(N_w - 1, 0):
        if N_w <= 1:
            forced = []
        else:
            step = len(forced_all) / N_w
            idx = sorted(set(min(len(forced_all) - 1, int(round(i * step))) for i in range(1, N_w)))
            forced = [forced_all[i] for i in idx]
    else:
        forced = forced_all
    bounds = [minx] + forced + [maxx]
    n_spans = len(bounds) - 1
    span_areas = [
        w_local.intersection(box(bounds[i] - 1e-6, -BIG, bounds[i + 1] + 1e-6, BIG)).area
        for i in range(n_spans)
    ]
    total = sum(span_areas) or 1.0
    extra_total = N_w - n_spans
    raw = [extra_total * a / total for a in span_areas]
    extra = [int(math.floor(r)) for r in raw]
    rem = extra_total - sum(extra)
    order = sorted(range(n_spans), key=lambda i: raw[i] - extra[i], reverse=True)
    for i in order[:max(0, rem)]:
        extra[i] += 1
    cols = [1 + e for e in extra]
    xs = list(forced)
    for i in range(n_spans):
        seg = w_local.intersection(box(bounds[i] - 1e-6, -BIG, bounds[i + 1] + 1e-6, BIG))
        xs.extend(equal_area_x(seg, cols[i]))
    xs = sorted(xs)
    xs, _ = _snap_cuts_to_voids(w_local, xs)
    return sorted(xs)


def _wing_fallback_convex(poly, k, grp):
    """T07 (b): a WING_TREE_FAILED raised by the wing decomposition itself (_split_wings,
    _wing_tree, _reduce_to_k_wings, _alloc_k) falls back to the convex cutter on the plate's
    own MRR frame rather than refusing outright. A refusal raised by the fallback itself
    (e.g. BAND_LT_3M, or the fallback's own WING_TREE_FAILED) propagates unchanged."""
    out = cut_convex(poly, k, grp)
    out["scheme"] = "wing_fallback_convex"
    out["notes"] = dict(out.get("notes") or {})
    out["notes"]["fallback"] = "WING_TREE_FAILED"
    return out


def cut_wings(poly, k, grp):
    """Sheets 09-11 steps 3-4: wing decomposition, single D-EU-75 free-bearing band."""
    try:
        wings = _reclaim_denoise_loss(_absorb_bays(_split_wings(poly)), poly)
    except Refusal as e:
        if e.token != "WING_TREE_FAILED":
            raise
        return _wing_fallback_convex(poly, k, grp)
    if len(wings) < 2:
        return _wing_fallback_convex(poly, k, grp)
    try:
        if k < len(wings):
            wings = _reduce_to_k_wings(wings, k)
        n = len(wings)
        k_per_wing = _alloc_k(wings, poly, k)
    except Refusal as e:
        if e.token != "WING_TREE_FAILED":
            raise
        return _wing_fallback_convex(poly, k, grp)

    loading = []
    cell_polys_world = []

    for i in range(n):
        theta, cx, cy, _L, W = frame(wings[i])
        w_local = to_local(wings[i], theta, cx, cy)
        minx, miny, maxx, maxy = w_local.bounds
        if k_per_wing[i] >= 2:
            try:
                M_w, N_w = choose_loading(maxx - minx, W, k_per_wing[i])
            except Refusal as e:
                if e.token != "BAND_LT_3M":
                    raise
                M_w, N_w = _choose_loading_no_band(maxx - minx, W, k_per_wing[i])
        else:
            M_w = 2 if W >= DOUBLE_LOADED_MIN_DEPTH else 1
            N_w = 1
        loading.append(M_w)
        xs = _wing_columns(w_local, N_w, [], minx, maxx)
        if xs is None:
            raise Refusal("WING_TREE_FAILED")
        bx = [minx - 1] + xs + [maxx + 1]
        odd_through = (k_per_wing[i] % 2 == 1) and (M_w == 2)
        yc = 0.0
        cells = []
        for ci in range(N_w):
            if odd_through and ci == N_w - 1:
                cells.append(w_local.intersection(box(bx[ci], miny - 1, bx[ci + 1], maxy + 1)))
            elif M_w == 2:
                cells.append(w_local.intersection(box(bx[ci], miny - 1, bx[ci + 1], yc)))
                cells.append(w_local.intersection(box(bx[ci], yc, bx[ci + 1], maxy + 1)))
            else:
                cells.append(w_local.intersection(box(bx[ci], miny - 1, bx[ci + 1], maxy + 1)))
        for c in cells:
            cell_polys_world.append(to_world(c, theta, cx, cy))

    # D-EU-75: the junction tree, the per-wing bands, `_junction` and every band-chaining
    # path are gone. A wing boundary is an artifact of the decomposition, not a real
    # architectural narrowing, so circulation is solved once, on a free bearing, against
    # the whole plate's own footprint (D-EU-73 (a): no cross-limb band -- there is only one
    # limb here, the whole plate), in the plate's own MRR frame -- theta=0.0 reproduces
    # today's axis-aligned answer, matching `cut_convex`'s own convention.
    theta_p, cx_p, cy_p, _L_p, _W_p = frame(poly)
    poly_local = to_local(poly, theta_p, cx_p, cy_p)
    cells_local = [to_local(cw, theta_p, cx_p, cy_p) for cw in cell_polys_world]
    minx_p, _miny_p, maxx_p, _maxy_p = poly_local.bounds
    centre_hint = poly_local.centroid.y
    half_width = CORRIDOR_W / 2

    A_total = poly.area
    s = min(max(math.sqrt(CORE_FRACTION * A_total), CORE_MIN_SIDE), CORE_MAX_SIDE)

    def _core_at(rect):
        ctr = rect.centroid
        return box(ctr.x - s / 2, ctr.y - s / 2, ctr.x + s / 2, ctr.y + s / 2)

    # T06 (2), D-EU-76 (a): one limb, one flat. When k <= len(wings), _alloc_k already
    # gave every wing k_w=1, and the odd_through branch above always takes the whole
    # per-wing box as a single cell -- no lengthwise split at construction time. What
    # remained was the free-bearing band, plus the core it is about to grow on its own
    # centroid (FINDING 230), cutting that whole box in two; `whole_cells` together
    # with `core_of=_core_at` is what keeps it undivided (T06 (1)) -- the core placed
    # here is the exact one built again at `core_local` below, so the candidate that
    # wins the search is the one that is actually still whole once the core lands.
    # When k < len(wings), `_reduce_to_k_wings` already merged limbs upstream and that
    # merge stands unchanged. Not touched here.
    solved = solve_band_free(poly_local, cells_local, centre_hint, half_width, minx_p, maxx_p,
                              whole_cells=True, core_of=_core_at)
    band_local = solved["band"]

    core_center = (band_local.centroid.x, band_local.centroid.y)
    core_local = box(
        core_center[0] - s / 2, core_center[1] - s / 2, core_center[0] + s / 2, core_center[1] + s / 2
    )

    circ_local = _polygons_only(unary_union([core_local, band_local]).intersection(poly_local))
    for _pass in range(8):
        if circ_local.geom_type == "Polygon":
            break
        parts = sorted(circ_local.geoms, key=lambda g: g.area, reverse=True)
        circ_local = _bridge(parts[0], parts[1:], poly_local)
    if circ_local.geom_type != "Polygon":
        raise Refusal("WING_TREE_FAILED")

    circ_world = set_precision(to_world(circ_local, theta_p, cx_p, cy_p).intersection(poly), 0.001)
    if circ_world.geom_type != "Polygon" or len(circ_world.interiors) > 0:
        raise Refusal("WING_TREE_FAILED")

    # T05/C9: `.intersection(poly)` above copies every real facade jog the band crosses
    # into the ring outline (D-EU-71 cap of 16). Drop collinear/near-collinear corners
    # with the file's own DENOISE_TOL before the wing cells are split, so a flat that
    # loses or gains a sliver here still gets it through the ordinary `difference`
    # below -- coverage stays exact by construction, not by a fixed-tolerance guard.
    simplified = set_precision(circ_world.simplify(DENOISE_TOL, preserve_topology=True), 0.001)
    if simplified.geom_type == "Polygon" and len(simplified.interiors) == 0:
        reclipped = set_precision(simplified.intersection(poly), 0.001)
        if reclipped.geom_type == "Polygon" and len(reclipped.interiors) == 0:
            circ_world = reclipped

    flats_world = []
    for cw in cell_polys_world:
        f = cw.intersection(poly).difference(circ_world)
        if f.is_empty or f.area < SCRAP_M2:
            raise Refusal("CELL_EMPTY")
        flats_world.append(f)

    flats_world, circ_world = _ensure_flat_access(poly, flats_world, circ_world)
    out = finish(poly, flats_world, circ_world)
    out["circ"] = _denoise_corridor(out["circ"], poly)
    if out["circ"] is not None and (len(out["circ"].exterior.coords) - 1) > CORRIDOR_MAX_POINTS:
        out["flats"], out["circ"] = _rectify_and_reassign(poly, out["flats"], out["circ"])
    out["scheme"] = "l_shape_decomposition" if n == 2 else "wing_spine_decomposition"
    out["notes"] = {"n_wings": n, "k_per_wing": k_per_wing, "loading": loading, "unsnapped": out.get("unsnapped", 0)}
    return out


def exterior_group(poly, allow_sliver=True):
    """DD-7: mirror 01_cut_group_plans.py:27-39's cls() on the exterior ring alone.

    T04 (PLAN_eu21-test01-clean-2026-09-02): `allow_sliver=False` skips the SLIVER
    shortcut. SLIVER's own scheme (`cut_sliver`, row_house_depth_bands) draws zero
    circulation zones, which is only legal under `C2` for a plate the census itself
    classified SLIVER (04_group_tests.py's check exempts `grp == "SLIVER"` only). The
    courtyard-lightwell fallback below is called with `grp == "COURTYARD"`, so a
    narrow-exterior plate routed to SLIVER here can never pass `C2` -- it is not a
    real sliver, it is a courtyard whose void was too small for the full scheme
    (D-EU-64: every plate carries exactly one circulation zone)."""
    ext = Polygon(poly.exterior.coords)
    _, _, _, L, W = frame(ext)
    if allow_sliver and W < 8.0:
        return "SLIVER"
    rec = _mrr_rectangularity(ext)
    ar = L / W if W > 1e-9 else float("inf")
    if rec >= 0.90:
        if ar < 1.5:
            return "SQUARE"
        if ar < 2.0:
            return "RECTANGLE"
        if ar < 3.0:
            return "CORRIDOR_RECTANGLE"
        return "SLAB"
    Q = ext.simplify(DENOISE_TOL, preserve_topology=True)
    if Q.geom_type != "Polygon":
        Q = max(Q.geoms, key=lambda g: g.area)
    rf = sum(1 for t in _interior_angles_ccw(Q) if t[0] > 180.0 + REFLEX_TOL_DEG)
    if rf == 0:
        return "TRAPEZOID"
    if rf == 1:
        return "L_SHAPE"
    if rf == 2:
        return "U_OR_T_SHAPE"
    return "COMPLEX_MULTI_WING"


def _dispatch_group(poly, k, grp2):
    if grp2 != "SLIVER" and k > 1:
        out = _try_corridor_rect(poly, k, grp2)
        if out is not None:
            return out
    if grp2 == "SLIVER":
        return cut_sliver(poly, k)
    if grp2 in WING_GROUPS:
        return cut_wings(poly, k, grp2)
    return cut_convex(poly, k, grp2)


def cut(poly, k, grp):
    poly = _normalize(poly)
    if k > MAXK:
        raise Refusal(DWELLING_DENSITY_REFUSAL_TOKEN)
    if grp != "SLIVER" and k > 1:
        out = _try_corridor_rect(poly, k, grp)
        if out is not None:
            return out
    if grp == "COURTYARD":
        interiors = [Polygon(r) for r in poly.interiors]
        if interiors:
            V = max(interiors, key=lambda g: g.area)
            _, _, _, VL, VW = frame(V)
            if VW < COURTYARD_MIN_VOID_SIDE:
                if k == 1:
                    return {"flats": [poly], "circ": None, "scheme": "single_dwelling",
                            "notes": {"grp2": None}}
                grp2 = exterior_group(poly, allow_sliver=False)
                out = _dispatch_group(poly, k, grp2)
                out["scheme"] = out["scheme"] + "+lightwell"
                out["notes"] = dict(out.get("notes") or {})
                out["notes"]["grp2"] = grp2
                return out
        return cut_courtyard(poly, k)
    if k == 1:
        return {"flats": [poly], "circ": None, "scheme": "single_dwelling", "notes": {}}
    if grp == "SLIVER":
        return cut_sliver(poly, k)
    if grp in CONVEX_GROUPS:
        return cut_convex(poly, k, grp)
    if grp in WING_GROUPS:
        return cut_wings(poly, k, grp)
    raise ValueError(f"unknown group {grp}")


PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
    "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295",
]


def _zone_pts(z):
    n = len(list(z.exterior.coords)) - 1
    for i in z.interiors:
        n += len(list(i.coords)) - 1
    return n


def _plot_zone(ax, z, **kw):
    xs, ys = z.exterior.xy
    ax.fill(xs, ys, **kw)
    ax.plot(xs, ys, "-", color="black", linewidth=0.6)
    ax.plot(xs, ys, "o", color="black", markersize=1.8)
    for i in z.interiors:
        ixs, iys = i.xy
        ax.plot(ixs, iys, "-", color="black", linewidth=0.6)
        ax.plot(ixs, iys, "o", color="black", markersize=1.8)


def _demo_one(plt, grp, rep):
    poly = Polygon(rep["exterior_ring"], rep.get("interior_rings") or [])
    ks = (2, 3, 6, 9, 12)
    fig, axes = plt.subplots(1, len(ks), figsize=(4.2 * len(ks), 4.6))
    if len(ks) == 1:
        axes = [axes]
    for ax, k in zip(axes, ks):
        xs, ys = poly.exterior.xy
        ax.plot(xs, ys, "-", color="black", linewidth=1.6)
        ax.plot(xs, ys, "o", color="black", markersize=1.8)
        for ring in poly.interiors:
            rxs, rys = ring.xy
            ax.plot(rxs, rys, "-", color="black", linewidth=1.6)
            ax.plot(rxs, rys, "o", color="black", markersize=1.8)
        try:
            out = cut(poly, k, grp)
        except Refusal as r:
            ax.set_title(f"k={k} REFUSED {r.token}", fontsize=8)
            ax.set_aspect("equal")
            ax.axis("off")
            continue
        except NotImplementedError:
            ax.set_title(f"k={k} NotImplementedError", fontsize=8)
            ax.set_aspect("equal")
            ax.axis("off")
            continue
        for i, f in enumerate(out["flats"]):
            _plot_zone(ax, f, facecolor=PALETTE[i % 12], alpha=0.75)
        if out["circ"] is not None:
            _plot_zone(ax, out["circ"], facecolor="0.85", hatch="//", edgecolor="0.4")
        total_pts = sum(_zone_pts(f) for f in out["flats"]) + (_zone_pts(out["circ"]) if out["circ"] is not None else 0)
        ax.set_title(f"k={k} {out['scheme']} pts={total_pts}", fontsize=8)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(grp)
    fig.tight_layout()
    out_dir = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-21" / "cutter_demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"demo_{grp}.png"
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def _load_module(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _main():
    if len(sys.argv) < 2 or sys.argv[1] != "--demo":
        print("usage: 05_group_cutters.py --demo [GROUP ...]")
        return 1
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m01 = _load_module("eu21_m01_group_plans", str(ROOT / "scripts" / "eu21" / "01_cut_group_plans.py"))
    groups = sys.argv[2:] if len(sys.argv) > 2 else list(m01.ORDER)
    reps = json.loads((ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-20" / "representatives.json").read_text(encoding="utf-8"))
    by_group = {r["group"]: r for r in reps}
    for grp in groups:
        rep = by_group[grp]
        path = _demo_one(plt, grp, rep)
        print(f"{grp} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
