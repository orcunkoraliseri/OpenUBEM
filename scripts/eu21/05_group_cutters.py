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
REFLEX_TOL_DEG = 10.0
MIN_WING_M2 = 15.0
MIN_WING_W = 3.0
SCRAP_M2 = 0.01
BIG = 10_000.0

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


def finish(fp, flats, circ):
    """D-EU-68: the only clean-up -- one room, no scrap, report (never patch) a hole."""
    flats = [_polygons_only(f) for f in flats]
    circ = _polygons_only(circ) if circ is not None else None
    state = {"circ": circ}
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

    flats = [_safe_precision(f) for f in flats]
    circ = _safe_precision(circ) if circ is not None else None
    flats.sort(key=lambda f: (-f.centroid.y, f.centroid.x))
    return {"flats": flats, "circ": circ, "unsnapped": unsnapped[0]}


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

        if grp in LINEAR_GALLERY_GROUPS:
            cxmin = minx - 1
            cxmax = xs[-1] if odd_through else maxx + 1
        else:
            cxmin = xs[0] - LANDING
            cxmax = xs[-1] if odd_through else xs[-1] + LANDING

        if M == 2:
            band = box(cxmin, yc - 0.9, cxmax, yc + 0.9).intersection(P)
            core_center = ((cxmin + cxmax) / 2, yc)
        else:
            xmid = (cxmin + cxmax) / 2
            strip = P.intersection(box(xmid - 0.05, miny - 1, xmid + 0.05, maxy + 1))
            maxy_local = strip.bounds[3] if not strip.is_empty else maxy
            band = box(cxmin, maxy_local - 1.8, cxmax, maxy_local).intersection(P)
            core_center = ((cxmin + cxmax) / 2, maxy_local - 0.9)

        core = box(core_center[0] - s / 2, core_center[1] - s / 2, core_center[0] + s / 2, core_center[1] + s / 2).intersection(P)
        circ_local = _polygons_only(unary_union([core, band]).intersection(P))
        for _pass in range(8):
            if circ_local.geom_type == "Polygon":
                break
            parts = sorted(circ_local.geoms, key=lambda g: g.area, reverse=True)
            circ_local = _bridge(parts[0], parts[1:], P)
        if circ_local.geom_type != "Polygon":
            raise Refusal("WING_TREE_FAILED")

        cells = []
        for i in range(N):
            if odd_through and i == N - 1:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1)))
            elif M == 2:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], yc)))
                cells.append(P.intersection(box(bx[i], yc, bx[i + 1], maxy + 1)))
            else:
                cells.append(P.intersection(box(bx[i], miny - 1, bx[i + 1], maxy + 1)))

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

    R_base = set_precision(
        Vl.buffer(CORRIDOR_W, cap_style="flat", join_style="mitre").difference(Vl).intersection(B), 0.001
    )

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

    cores = []
    for sx, sy in quads:
        if len(cores) >= n_c_target:
            break
        cb = set_precision(core_box(sx, sy).intersection(B), 0.001)
        if cb.area < 3.0 or not _touches(cb, R_base):
            cb2 = set_precision(translate(core_box(sx, sy), -sx * CORE_MIN_SIDE, 0).intersection(B), 0.001)
            if cb2.area >= 3.0:
                cores.append(cb2)
        else:
            cores.append(cb)
    if not cores:
        raise Refusal("WING_TREE_FAILED")
    n_c = len(cores)

    def notch(side):
        pad = 0.30
        if side == "-x":
            return box(-a - CORRIDOR_W - pad, -b - pad, -a + pad, b + pad)
        if side == "+x":
            return box(a - pad, -b - pad, a + CORRIDOR_W + pad, b + pad)
        if side == "+y":
            return box(-a - pad, b - pad, a + pad, b + CORRIDOR_W + pad)
        return box(-a - pad, -b - CORRIDOR_W - pad, a + pad, -b + pad)

    def opposite(side):
        return {"-x": "+x", "+x": "-x", "+y": "-y", "-y": "+y"}[side]

    def passage_for(side):
        if side == "+x":
            return box(a, -0.9, a + BIG, 0.9).intersection(B)
        if side == "-x":
            return box(-a - BIG, -0.9, -a, 0.9).intersection(B)
        if side == "+y":
            return box(-0.9, b, 0.9, b + BIG).intersection(B)
        return box(-0.9, -b - BIG, 0.9, -b).intersection(B)

    def trial(opening_side):
        R = set_precision(R_base.difference(notch(opening_side)), 0.001)
        merged = _bridge(R, cores, B)
        parts = [merged]
        if k == 1:
            parts.append(set_precision(passage_for(opposite(opening_side)), 0.001))
        circ_local = set_precision(unary_union(parts).intersection(B), 0.001)
        if circ_local.geom_type != "Polygon":
            raise Refusal("WING_TREE_FAILED")
        if len(circ_local.interiors) > 0:
            raise Refusal("WING_TREE_FAILED")

        segs = _perimeter_segs(opening_side)
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
                merged = _safe_union(sector_parts[i])
                if merged is None or merged.is_empty:
                    raise Refusal("CELL_EMPTY")
                flats_local.append(merged)
            for f in flats_local:
                _, _, _, _fL, fW = frame(f)
                if fW < MIN_FLAT_W:
                    raise Refusal("BAND_LT_3M")

        for sv in secondary_l:
            if not any(f.buffer(0.05).intersects(sv) for f in flats_local):
                raise Refusal("SECONDARY_VOID_UNCUT")

        access = [_shared_len_metric(f, circ_local) for f in flats_local] if k >= 2 else []
        n_access = sum(1 for m in access if m >= ACCESS_MIN_M) if access else len(flats_local)
        min_access = min(access) if access else None
        return flats_local, circ_local, n_access, min_access

    candidates = ["-x", "+x", "+y", "-y"]
    default_flats, default_circ, default_n, default_min = trial(candidates[0])
    if k < 2 or default_n == k:
        chosen_side = candidates[0]
        flats_local, circ_local, min_access = default_flats, default_circ, default_min
    else:
        best = (candidates[0], default_flats, default_circ, default_n, default_min)
        for side in candidates[1:]:
            try:
                trial_out = trial(side)
            except Refusal:
                continue
            f, c, n, m = trial_out
            if n > best[3]:
                best = (side, f, c, n, m)
        chosen_side, flats_local, circ_local, _n_access, min_access = best

    flats_world = [to_world(f, theta, cx, cy) for f in flats_local]
    circ_world = to_world(circ_local, theta, cx, cy)
    total_cov = sum(f.area for f in flats_world) + circ_world.area
    assert total_cov >= 0.999 * poly.area, f"coverage {total_cov:.2f} < 0.999*{poly.area:.2f}"
    out = finish(poly, flats_world, circ_world)
    out["scheme"] = "courtyard_cores_gallery"
    out["notes"] = {
        "n_cores": n_c,
        "opening_side": chosen_side,
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
        if len(finished) + len(pieces) > 8:
            raise Refusal("WING_TREE_FAILED")
        piece = pieces.pop(0)
        parts = _split_once(piece)
        if parts is None:
            finished.append(piece)
        else:
            pieces.extend(parts)
    if len(finished) > 8 or not finished:
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


def _junction(w, parent_w):
    sw = w.buffer(0.05, cap_style="flat", join_style="mitre")
    sp = parent_w.buffer(0.05, cap_style="flat", join_style="mitre")
    shared = sw.intersection(sp)
    pt = shared.centroid if not shared.is_empty else w.centroid
    return (pt.x, pt.y)


def _reduce_to_k_wings(wings, k):
    """Sheets 09-11 step 6: fewer flats than wings -- fold the smallest into its parent."""
    wings = list(wings)
    while len(wings) > max(k, 1):
        root, parent = _wing_tree(wings)
        candidates = [i for i in range(len(wings)) if i != root]
        if not candidates:
            break
        smallest = min(candidates, key=lambda i: wings[i].area)
        p = parent[smallest]
        merged = _safe_union([wings[smallest], wings[p]])
        if merged is None:
            raise Refusal("WING_TREE_FAILED")
        if merged.geom_type != "Polygon":
            merged = max(merged.geoms, key=lambda g: g.area)
        wings = [w for idx, w in enumerate(wings) if idx not in (smallest, p)] + [merged]
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


def cut_wings(poly, k):
    """Sheets 09-11 steps 3-4: wing decomposition, junction core, spine corridor."""
    wings = _reclaim_denoise_loss(_absorb_bays(_split_wings(poly)), poly)
    if len(wings) < 2:
        raise Refusal("WING_TREE_FAILED")
    if k < len(wings):
        wings = _reduce_to_k_wings(wings, k)
    n = len(wings)
    root, parent = _wing_tree(wings)
    children = {i: [] for i in range(n)}
    for j, p in parent.items():
        if p is not None:
            children[p].append(j)
    junctions = {j: _junction(wings[j], wings[p]) for j, p in parent.items() if p is not None}

    plate_ctr = (poly.centroid.x, poly.centroid.y)
    wframes = []
    for i, w in enumerate(wings):
        theta, cx, cy, _L, W = frame(w)
        ref_j = None
        if i in junctions:
            ref_j = junctions[i]
        elif children[i]:
            ref_j = junctions[max(children[i], key=lambda c: wings[c].area)]
        if ref_j is not None:
            ju = to_local(Point(*ref_j), theta, cx, cy).x
            if ju > 0:
                theta = theta + 180.0
        ctr_local = to_local(Point(*plate_ctr), theta, cx, cy)
        inner_sign = 1.0 if ctr_local.y >= 0 else -1.0
        wframes.append((theta, cx, cy, W, inner_sign))

    k_per_wing = _alloc_k(wings, poly, k)

    loading = []
    cell_polys_world = []
    band_geoms = []
    band_specs = []

    for i in range(n):
        theta, cx, cy, W, inner_sign = wframes[i]
        w_local = to_local(wings[i], theta, cx, cy)
        minx, miny, maxx, maxy = w_local.bounds
        if k_per_wing[i] >= 2:
            M_w, N_w = choose_loading(maxx - minx, W, k_per_wing[i])
        else:
            M_w = 2 if W >= DOUBLE_LOADED_MIN_DEPTH else 1
            N_w = 1
        loading.append(M_w)
        child_j = [to_local(Point(*junctions[c]), theta, cx, cy).x for c in children[i]]
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

        reach = list(child_j) + list(xs)
        if k_per_wing[i] == 1 and not children[i]:
            band_lo, u_far = minx - 0.5, minx + LANDING
            band = (box(band_lo, W / 2 - CORRIDOR_W, u_far, W / 2) if inner_sign > 0
                    else box(band_lo, -W / 2, u_far, -W / 2 + CORRIDOR_W))
        else:
            if i == root:
                band_lo = (min(reach) - LANDING) if reach else (minx - 0.5)
            else:
                band_lo = minx - 0.5
            if odd_through and xs and reach and xs[-1] >= max(reach) - 1e-9:
                u_far = xs[-1]
            else:
                u_far = (max(reach) + LANDING) if reach else maxx
            if M_w == 2:
                band = box(band_lo, -0.9, u_far, 0.9)
            elif inner_sign > 0:
                band = box(band_lo, W / 2 - CORRIDOR_W, u_far, W / 2)
            else:
                band = box(band_lo, -W / 2, u_far, -W / 2 + CORRIDOR_W)
        w_buf = w_local.buffer(1.0, cap_style="flat", join_style="mitre")
        band = band.intersection(w_buf)
        band_geoms.append(set_precision(to_world(band, theta, cx, cy).intersection(poly), 0.001))
        band_specs.append({
            "theta": theta, "cx": cx, "cy": cy, "M_w": M_w, "inner_sign": inner_sign,
            "W": W, "band_lo": band_lo, "u_far": u_far, "w_buf": w_buf, "grown": 0.0,
        })

    A_total = poly.area
    s = min(max(math.sqrt(CORE_FRACTION * A_total), CORE_MIN_SIDE), CORE_MAX_SIDE)
    theta_r, cx_r, cy_r, _W_r, inner_sign_r = wframes[root]
    root_children = children[root]
    if len(root_children) == 1:
        j_local = to_local(Point(*junctions[root_children[0]]), theta_r, cx_r, cy_r)
        core_center = (j_local.x, j_local.y + inner_sign_r * s / 2)
    elif len(root_children) >= 2:
        us = [to_local(Point(*junctions[c]), theta_r, cx_r, cy_r).x for c in root_children]
        core_center = (sum(us) / len(us), 0.0)
    else:
        core_center = (0.0, 0.0)
    core_local = box(
        core_center[0] - s / 2, core_center[1] - s / 2, core_center[0] + s / 2, core_center[1] + s / 2
    )
    core_world = set_precision(to_world(core_local, theta_r, cx_r, cy_r).intersection(poly), 0.001)

    def _rebuild_band(spec):
        if spec["M_w"] == 2:
            nb = box(spec["band_lo"], -0.9, spec["u_far"], 0.9)
        elif spec["inner_sign"] > 0:
            nb = box(spec["band_lo"], spec["W"] / 2 - CORRIDOR_W, spec["u_far"], spec["W"] / 2)
        else:
            nb = box(spec["band_lo"], -spec["W"] / 2, spec["u_far"], -spec["W"] / 2 + CORRIDOR_W)
        nb = nb.intersection(spec["w_buf"])
        return set_precision(to_world(nb, spec["theta"], spec["cx"], spec["cy"]).intersection(poly), 0.001)

    combined = _polygons_only(set_precision(unary_union([core_world] + band_geoms).intersection(poly), 0.001))
    if combined.geom_type != "Polygon":
        # T06a(2): grow a disconnected wing's own band toward its junction, in 0.5 m
        # steps up to 3.0 m total, before ever falling back to a drawn connector.
        for _g in range(6):
            if combined.geom_type == "Polygon":
                break
            parts = list(combined.geoms) if combined.geom_type == "MultiPolygon" else [combined]
            if len(parts) <= 1:
                break
            hub = max(parts, key=lambda g: g.area)
            grew = False
            for i, spec in enumerate(band_specs):
                if _touches(band_geoms[i], hub):
                    continue
                if spec["grown"] >= 3.0 - 1e-9:
                    continue
                spec["band_lo"] -= 0.5
                spec["grown"] += 0.5
                band_geoms[i] = _rebuild_band(spec)
                grew = True
            if not grew:
                break
            combined = _polygons_only(set_precision(unary_union([core_world] + band_geoms).intersection(poly), 0.001))

    for _pass in range(8):
        if combined.geom_type == "Polygon":
            break
        parts = sorted(combined.geoms, key=lambda g: g.area, reverse=True)
        combined = _bridge(parts[0], parts[1:], poly)

    circ_world = combined
    if circ_world.geom_type != "Polygon" or len(circ_world.interiors) > 0:
        raise Refusal("WING_TREE_FAILED")

    flats_world = []
    for cw in cell_polys_world:
        f = cw.intersection(poly).difference(circ_world)
        if f.is_empty or f.area < SCRAP_M2:
            raise Refusal("CELL_EMPTY")
        flats_world.append(f)

    out = finish(poly, flats_world, circ_world)
    out["scheme"] = "l_shape_decomposition" if n == 2 else "wing_spine_decomposition"
    out["notes"] = {"n_wings": n, "k_per_wing": k_per_wing, "loading": loading, "unsnapped": out.get("unsnapped", 0)}
    return out


def exterior_group(poly):
    """DD-7: mirror 01_cut_group_plans.py:27-39's cls() on the exterior ring alone."""
    ext = Polygon(poly.exterior.coords)
    _, _, _, L, W = frame(ext)
    if W < 8.0:
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
    if grp2 == "SLIVER":
        return cut_sliver(poly, k)
    if grp2 in WING_GROUPS:
        return cut_wings(poly, k)
    return cut_convex(poly, k, grp2)


def cut(poly, k, grp):
    poly = _normalize(poly)
    if k > MAXK:
        raise Refusal(DWELLING_DENSITY_REFUSAL_TOKEN)
    if grp == "COURTYARD":
        interiors = [Polygon(r) for r in poly.interiors]
        if interiors:
            V = max(interiors, key=lambda g: g.area)
            _, _, _, VL, VW = frame(V)
            if VW < COURTYARD_MIN_VOID_SIDE:
                if k == 1:
                    return {"flats": [poly], "circ": None, "scheme": "single_dwelling",
                            "notes": {"grp2": None}}
                grp2 = exterior_group(poly)
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
        return cut_wings(poly, k)
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
