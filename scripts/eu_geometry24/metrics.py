from __future__ import annotations

import math

NEAR_DUP_M = 0.005
COLLINEAR_DEG = 0.1


def poly_area3(coords):
    ax = ay = az = 0.0
    n = len(coords)
    for i in range(n):
        x1, y1, z1 = coords[i]
        x2, y2, z2 = coords[(i + 1) % n]
        ax += (y1 - y2) * (z1 + z2)
        ay += (z1 - z2) * (x1 + x2)
        az += (x1 - x2) * (y1 + y2)
    return 0.5 * math.sqrt(ax * ax + ay * ay + az * az)


def effective_len(coords):
    pts = [tuple(c) for c in coords]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        for i in range(n):
            p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
            v1 = [a - b for a, b in zip(p0, p1)]
            v2 = [a - b for a, b in zip(p2, p1)]
            l1, l2 = math.sqrt(sum(c * c for c in v1)), math.sqrt(sum(c * c for c in v2))
            drop = l1 < NEAR_DUP_M or l2 < NEAR_DUP_M
            if not drop and l1 > 0 and l2 > 0:
                cosv = max(-1.0, min(1.0, sum(a * b for a, b in zip(v1, v2)) / (l1 * l2)))
                drop = math.degrees(math.acos(-cosv)) < COLLINEAR_DEG
            if drop:
                del pts[i]
                changed = True
                break
    return len(pts)


def idf_metrics(idf):
    bsd = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    by = {str(s.Name).upper(): s for s in bsd}
    pairs = set()
    for s in bsd:
        o = str(s.Outside_Boundary_Condition_Object or "").upper()
        if o and o in by:
            pairs.add(tuple(sorted((str(s.Name).upper(), o))))
    raw = eff = ndp = 0
    for a, b in pairs:
        ca, cb = list(by[a].coords), list(by[b].coords)
        if len(ca) != len(cb):
            raw += 1
        ea, eb = effective_len(ca), effective_len(cb)
        if ea != eb:
            eff += 1
        if ea != len(ca) or eb != len(cb):
            ndp += 1
    sl = sum(1 for s in bsd if poly_area3(list(s.coords)) < 1e-6)
    rep = 0
    mags = []
    for s in bsd:
        c = [tuple(p) for p in s.coords]
        n = len(c)
        rep += sum(1 for i in range(n) if c[i] == c[(i + 1) % n])
        mags += [abs(v) for p in c for v in p[:2]]
    return {
        "surfaces": len(bsd), "zones": len(idf.idfobjects["ZONE"]), "interzone_pairs": len(pairs),
        "raw_count_mismatch_pairs": raw, "effective_count_mismatch_pairs": eff,
        "pairs_with_neardup_or_collinear": ndp, "surfaces_lt_1e-6_m2": sl, "repeated_vertices": rep,
        "max_abs_xy": max(mags) if mags else float("nan"),
    }
