from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

PROBE_M = 0.2
BASE_TOL_M = 0.02
MIN_FLOOR_AREA_M2 = 0.5
VOTE_FRACTIONS = (0.1, 0.3, 0.5, 0.7, 0.9)
VOTE_PROBES_M = (0.02, 0.2)
SURFACE_TYPES = ("FLOOR", "WALL", "CEILING", "ROOF")
_BS = "BUILDINGSURFACE:DETAILED"
_FEN = "FENESTRATIONSURFACE:DETAILED"


def _newell(pts) -> tuple[float, float, float]:
    nx = ny = nz = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    return nx, ny, nz


def _inside(pt, poly) -> bool:
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][0], poly[i][1]
        x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _pts(surface) -> list[tuple[float, float, float]]:
    return [tuple(float(c) for c in p) for p in surface.coords]


def _stype(surface) -> str:
    return str(surface.Surface_Type).strip().upper()


def _centre(pts) -> tuple[float, float, float]:
    n = len(pts)
    return (
        sum(p[0] for p in pts) / n,
        sum(p[1] for p in pts) / n,
        sum(p[2] for p in pts) / n,
    )


def _zone_floors(surfaces) -> dict[str, list]:
    floors: dict[str, list] = defaultdict(list)
    for s in surfaces:
        if _stype(s) == "FLOOR":
            pts = _pts(s)
            if len(pts) >= 3:
                floors[str(s.Zone_Name).strip().upper()].append(pts)
    return floors


def _zone_centroids(surfaces, floors) -> dict[str, tuple[float, float]]:
    out = {}
    for zone, polys in floors.items():
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        out[zone] = (sum(xs) / len(xs), sum(ys) / len(ys))
    rest: dict[str, list] = defaultdict(list)
    for s in surfaces:
        z = str(s.Zone_Name).strip().upper()
        if z not in out:
            rest[z].extend(_pts(s))
    for z, pts in rest.items():
        if pts:
            out[z] = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    return out


def _poly_area2(poly) -> float:
    n = len(poly)
    return 0.5 * sum(
        poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)
    )


def _wall_base(pts):
    zmin = min(p[2] for p in pts)
    base = [p for p in pts if p[2] - zmin <= BASE_TOL_M]
    if len(base) < 2:
        return None
    best = max(
        ((p, q) for i, p in enumerate(base) for q in base[i + 1:]),
        key=lambda pq: math.hypot(pq[0][0] - pq[1][0], pq[0][1] - pq[1][1]),
    )
    if math.hypot(best[0][0] - best[1][0], best[0][1] - best[1][1]) == 0.0:
        return None
    return best


def _wall_probe(pts, polys, zone_centre) -> tuple[str, str, int]:
    """Return (facing, how, vote_margin): facing is 'outward', 'inward' or 'unclear'."""
    n = _newell(pts)
    h = math.hypot(n[0], n[1])
    if h == 0.0:
        return "unclear", "degenerate", 0
    ux, uy = n[0] / h, n[1] / h
    big = [p for p in polys if abs(_poly_area2(p)) >= MIN_FLOOR_AREA_M2] or list(polys)
    base = _wall_base(pts)
    if base is not None and big:
        (x0, y0, _), (x1, y1, _) = base
        out_votes = in_votes = 0
        for frac in VOTE_FRACTIONS:
            bx, by = x0 + frac * (x1 - x0), y0 + frac * (y1 - y0)
            for d in VOTE_PROBES_M:
                fi = any(_inside((bx + d * ux, by + d * uy), p) for p in big)
                bi = any(_inside((bx - d * ux, by - d * uy), p) for p in big)
                if bi and not fi:
                    out_votes += 1
                elif fi and not bi:
                    in_votes += 1
        if out_votes != in_votes:
            return ("outward" if out_votes > in_votes else "inward"), "vote", abs(out_votes - in_votes)
        ex, ey = x1 - x0, y1 - y0
        el = math.hypot(ex, ey)
        ex, ey = ex / el, ey / el
        best_overlap = 0.0
        best_side = 0
        for poly in big:
            sign = 1 if _poly_area2(poly) > 0 else -1
            m = len(poly)
            for i in range(m):
                ax, ay = poly[i][0], poly[i][1]
                bx_, by_ = poly[(i + 1) % m][0], poly[(i + 1) % m][1]
                dx, dy = bx_ - ax, by_ - ay
                dl = math.hypot(dx, dy)
                if dl == 0.0:
                    continue
                dx, dy = dx / dl, dy / dl
                if abs((x0 - ax) * dy - (y0 - ay) * dx) > BASE_TOL_M:
                    continue
                if abs((x1 - ax) * dy - (y1 - ay) * dx) > BASE_TOL_M:
                    continue
                t0 = (x0 - ax) * dx + (y0 - ay) * dy
                t1 = (x1 - ax) * dx + (y1 - ay) * dy
                overlap = min(max(t0, t1), dl) - max(min(t0, t1), 0.0)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_side = sign * (-dy * ux + dx * uy)
        if best_overlap > 0.0 and best_side != 0:
            return ("outward" if best_side < 0 else "inward"), "edge", 0
    if zone_centre is None:
        return "unclear", "no_centroid", 0
    cx, cy, _ = _centre(pts)
    dot = ux * (cx - zone_centre[0]) + uy * (cy - zone_centre[1])
    if dot > 0:
        return "outward", "fallback", 0
    if dot < 0:
        return "inward", "fallback", 0
    return "unclear", "fallback", 0


def measure_outdoor_walls(idf) -> dict[str, int]:
    surfaces = list(idf.idfobjects[_BS])
    floors = _zone_floors(surfaces)
    counts = {"inward": 0, "outward": 0, "unclear": 0}
    for s in surfaces:
        if _stype(s) != "WALL" or str(s.Outside_Boundary_Condition).strip().upper() != "OUTDOORS":
            continue
        pts = _pts(s)
        if len(pts) < 3:
            continue
        n = _newell(pts)
        h = math.hypot(n[0], n[1])
        if h == 0.0:
            counts["unclear"] += 1
            continue
        ux, uy = n[0] / h, n[1] / h
        cx, cy, _ = _centre(pts)
        polys = floors.get(str(s.Zone_Name).strip().upper(), [])
        fi = any(_inside((cx + PROBE_M * ux, cy + PROBE_M * uy), p) for p in polys)
        bi = any(_inside((cx - PROBE_M * ux, cy - PROBE_M * uy), p) for p in polys)
        counts["inward" if fi and not bi else "outward" if bi and not fi else "unclear"] += 1
    return counts


def check_interzone_pairs(idf) -> dict[str, Any]:
    by_name = {str(s.Name).strip().upper(): s for s in idf.idfobjects[_BS]}
    seen: set[frozenset] = set()
    total = opposite = 0
    bad: list[tuple[str, str]] = []
    for s in idf.idfobjects[_BS]:
        if str(s.Outside_Boundary_Condition).strip().upper() != "SURFACE":
            continue
        a = str(s.Name).strip().upper()
        b = str(s.Outside_Boundary_Condition_Object).strip().upper()
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
        partner = by_name.get(b)
        if partner is None:
            bad.append((a, b))
            total += 1
            continue
        total += 1
        na, nb = _newell(_pts(s)), _newell(_pts(partner))
        if na[0] * nb[0] + na[1] * nb[1] + na[2] * nb[2] < 0:
            opposite += 1
        else:
            bad.append((a, b))
    return {"interzone_pairs": total, "interzone_opposite": opposite, "interzone_bad": bad}


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _fallback_margin(pts, zone_centre) -> float:
    n = _newell(pts)
    h = math.hypot(n[0], n[1])
    if h == 0.0 or zone_centre is None:
        return 0.0
    cx, cy, _ = _centre(pts)
    return abs(n[0] * (cx - zone_centre[0]) + n[1] * (cy - zone_centre[1])) / h


def normalise_surface_orientation(idf) -> dict[str, Any]:
    surfaces = list(idf.idfobjects[_BS])
    floors = _zone_floors(surfaces)
    centroids = _zone_centroids(surfaces, floors)
    result: dict[str, Any] = {
        t: {"reversed": 0, "kept": 0, "fallback": 0} for t in SURFACE_TYPES
    }
    result["other"] = 0
    decided: dict[str, dict[str, Any]] = {}
    wall_how: dict[str, int] = {}

    for s in surfaces:
        t = _stype(s)
        pts = _pts(s)
        name = str(s.Name).strip().upper()
        if t not in SURFACE_TYPES or len(pts) < 3:
            result["other"] += 1
            continue
        n = _newell(pts)
        zone = str(s.Zone_Name).strip().upper()
        by_fallback = False
        margin = 0.0
        vote_margin = 0
        if t == "FLOOR":
            flip = n[2] > 0
        elif t in ("CEILING", "ROOF"):
            flip = n[2] < 0
        else:
            facing, how, vote_margin = _wall_probe(pts, floors.get(zone, []), centroids.get(zone))
            wall_how[how] = wall_how.get(how, 0) + 1
            by_fallback = how not in ("vote", "edge")
            if by_fallback:
                margin = _fallback_margin(pts, centroids.get(zone))
            flip = facing == "inward"
        decided[name] = {
            "surface": s, "type": t, "pts": pts, "normal": n,
            "flip": flip, "fallback": by_fallback, "margin": margin, "vote_margin": vote_margin,
        }

    def final_normal(d):
        n = d["normal"]
        return (-n[0], -n[1], -n[2]) if d["flip"] else n

    result["wall_how"] = wall_how
    result["pair_rule1"] = 0
    result["pair_rule2"] = 0
    result["pair_rule3"] = []
    result["pair_rule4"] = 0
    seen: set[frozenset] = set()
    for name, a in decided.items():
        s = a["surface"]
        if str(s.Outside_Boundary_Condition).strip().upper() != "SURFACE":
            continue
        bname = str(s.Outside_Boundary_Condition_Object).strip().upper()
        b = decided.get(bname)
        key = frozenset((name, bname))
        if b is None or key in seen:
            continue
        seen.add(key)
        if _dot(final_normal(a), final_normal(b)) < 0:
            continue
        if a["fallback"] != b["fallback"]:
            loser = b if not a["fallback"] else a
            loser["flip"] = not loser["flip"]
            result["pair_rule1"] += 1
        elif a["fallback"] and b["fallback"]:
            loser = b if a["margin"] >= b["margin"] else a
            loser["flip"] = not loser["flip"]
            result["pair_rule2"] += 1
        elif a["vote_margin"] != b["vote_margin"]:
            loser = b if a["vote_margin"] > b["vote_margin"] else a
            loser["flip"] = not loser["flip"]
            result["pair_rule4"] += 1
        else:
            result["pair_rule3"].append((name, bname))

    flipped: set[str] = set()
    for name, d in decided.items():
        t = d["type"]
        if d["fallback"]:
            result[t]["fallback"] += 1
        if d["flip"]:
            d["surface"].setcoords(list(reversed(d["pts"])))
            flipped.add(name)
            result[t]["reversed"] += 1
        else:
            result[t]["kept"] += 1

    result["windows_reversed"] = 0
    result["windows_kept"] = 0
    for f in idf.idfobjects[_FEN]:
        if str(f.Building_Surface_Name).strip().upper() in flipped:
            f.setcoords(list(reversed([tuple(float(c) for c in p) for p in f.coords])))
            result["windows_reversed"] += 1
        else:
            result["windows_kept"] += 1

    result.update(check_interzone_pairs(idf))
    return result
