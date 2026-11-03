from __future__ import annotations

import math
from io import StringIO
from typing import Any

COINCIDENT_M = 0.01
PLANE_DET = 1.0e-4
MIN_EDGE = 1.0e-8
TURN_THRESHOLD = 1.0e-6
_BS = "BUILDINGSURFACE:DETAILED"
_FEN = "FENESTRATIONSURFACE:DETAILED"
_SHADING = ("SHADING:SITE:DETAILED", "SHADING:BUILDING:DETAILED")


def _key(value) -> str:
    return str(value or "").strip().upper()


def _pts(surface) -> list[tuple[float, float, float]]:
    return [tuple(float(c) for c in p) for p in surface.coords]


def _area(pts) -> float:
    ax = ay = az = 0.0
    n = len(pts)
    for i in range(n):
        p = pts[i]
        q = pts[(i + 1) % n]
        ax += p[1] * q[2] - p[2] * q[1]
        ay += p[2] * q[0] - p[0] * q[2]
        az += p[0] * q[1] - p[1] * q[0]
    return 0.5 * math.sqrt(ax * ax + ay * ay + az * az)


def _dist(a, b) -> float:
    return math.dist(a, b)


def _coincident_events(pts) -> tuple[list[tuple[float, float, float]], int]:
    pts = list(pts)
    events = 0
    popped = True
    while popped:
        popped = False
        events = 0
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            if _dist(pts[i], pts[j]) < COINCIDENT_M:
                if len(pts) > 3:
                    del pts[j]
                    popped = True
                    break
                events += 1
    return pts, events


class _Arrays:
    def __init__(self, size: int = 256):
        self.x = [0.0] * size
        self.y = [0.0] * size
        self.z = [0.0] * size
        self.a = [0.0] * size
        self.b = [0.0] * size


def _collinear_events(pts, arrays: _Arrays) -> int:
    n = len(pts)
    x, y, z = arrays.x, arrays.y, arrays.z
    for i in range(n):
        x[i], y[i], z[i] = pts[i]
    x[n], y[n], z[n] = pts[0]
    x[n + 1], y[n + 1], z[n + 1] = pts[1]
    for first, second, name in ((x, y, "xy"), (x, z, "xz"), (y, z, "yz")):
        det = 0.0
        for i in range(n):
            det += first[i] * second[i + 1] - first[i + 1] * second[i]
        if abs(det) > PLANE_DET:
            arrays.a = list(first)
            arrays.b = list(second)
            break
    a, b = arrays.a, arrays.b
    collinear = 0
    prev_sign = None
    for i in range(n):
        v1 = (a[i + 1] - a[i], b[i + 1] - b[i])
        v2 = (a[i + 2] - a[i + 1], b[i + 2] - b[i + 1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if l1 <= MIN_EDGE or l2 <= MIN_EDGE:
            continue
        sinarg = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
        sinarg = max(-1.0, min(1.0, sinarg))
        theta = math.asin(sinarg)
        if theta > TURN_THRESHOLD:
            sign = True
        elif theta < -TURN_THRESHOLD:
            sign = False
        else:
            collinear += 1
            continue
        if prev_sign is None:
            prev_sign = sign
            continue
        if sign != prev_sign:
            break
        prev_sign = sign
    return 1 if collinear > 0 and n - collinear < 3 else 0


def energyplus_events(pts, arrays: _Arrays | None = None) -> int:
    pts = list(pts)
    if len(pts) <= 2:
        return 0
    pts, events = _coincident_events(pts)
    return events + _collinear_events(pts, arrays or _Arrays())


def _load(idf_text_or_obj):
    if not isinstance(idf_text_or_obj, str):
        return idf_text_or_obj
    from eppy.modeleditor import IDDAlreadySetError
    from geomeppy import IDF

    from scripts.run_eu_s2_campaign import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(StringIO(idf_text_or_obj))


def drop_degenerate_surfaces(idf_text_or_obj, apply: bool = True) -> dict[str, Any]:
    idf = _load(idf_text_or_obj)
    surfaces = {_key(s.Name): s for s in idf.idfobjects[_BS]}
    windows = {_key(w.Name): w for w in idf.idfobjects[_FEN]}
    arrays = _Arrays()
    shading_events = 0
    for kind in _SHADING:
        for sh in idf.idfobjects[kind]:
            shading_events += energyplus_events(_pts(sh), arrays)
    events = {}
    for s in idf.idfobjects[_BS]:
        events[_key(s.Name)] = energyplus_events(_pts(s), arrays)
    win_events = {}
    for w in idf.idfobjects[_FEN]:
        win_events[_key(w.Name)] = energyplus_events(_pts(w), arrays)
    degenerate = {name for name, n in events.items() if n > 0}
    degenerate_windows = {name for name, n in win_events.items() if n > 0}
    rows = []
    unpaired = []
    delete = set()
    for name in sorted(degenerate):
        s = surfaces[name]
        partner = _key(getattr(s, "Outside_Boundary_Condition_Object", ""))
        partner = partner if partner in surfaces else ""
        partner_degenerate = partner in degenerate if partner else True
        if partner and not partner_degenerate:
            unpaired.append((str(s.Name), str(surfaces[partner].Name)))
        else:
            delete.add(name)
        rows.append(
            {
                "name": str(s.Name),
                "kind": "surface",
                "zone": str(s.Zone_Name),
                "type": str(s.Surface_Type),
                "boundary": str(s.Outside_Boundary_Condition),
                "area_m2": _area(_pts(s)),
                "events": events[name],
                "partner": str(surfaces[partner].Name) if partner else "",
                "partner_deleted": "y" if partner and partner in delete else "n",
                "deleted": "y" if name in delete else "n",
            }
        )
    for row in rows:
        if row["partner"]:
            row["partner_deleted"] = "y" if _key(row["partner"]) in delete else "n"
    for name in sorted(degenerate_windows):
        w = windows[name]
        rows.append(
            {
                "name": str(w.Name),
                "kind": "window",
                "zone": str(getattr(w, "Building_Surface_Name", "")),
                "type": str(w.Surface_Type),
                "boundary": "Window",
                "area_m2": _area(_pts(w)),
                "events": win_events[name],
                "partner": "",
                "partner_deleted": "n",
                "deleted": "y",
            }
        )
    dropped_windows = []
    if apply:
        for name, w in windows.items():
            if name in degenerate_windows or _key(w.Building_Surface_Name) in delete:
                dropped_windows.append(str(w.Name))
                idf.removeidfobject(w)
        for name in delete:
            idf.removeidfobject(surfaces[name])
    n_deleted = len(delete) + len(degenerate_windows)
    return {
        "idf": idf,
        "surfaces": rows,
        "n_degenerate": len(rows),
        "n_events": sum(r["events"] for r in rows),
        "n_events_shading": shading_events,
        "n_events_total": sum(events.values()) + sum(win_events.values()) + shading_events,
        "n_deleted": n_deleted if apply else 0,
        "partner_not_degenerate": unpaired,
        "windows_deleted": dropped_windows,
    }
