from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ARCHETYPE_DIR = ROOT / "openubem" / "data" / "construction"
COUNTRY_FILES = {
    "ES": "es", "FR": "fr", "GB": "gb", "IT": "it",
    "AT": "at", "KR": "kr", "CA": "ca", "FI": "fi", "ZA": "za", "HU": "hu", "AM": "am",
}
U_WINDOW_LIMIT_W_M2K = 7.0
MIN_WINDOW_AREA_M2 = 0.05
CONVEXITY_TOLERANCE = 1e-9
WINDOW_MATERIAL_NAME = "EU_Window_SimpleGlazing"
WINDOW_CONSTRUCTION_NAME = "EU_Window_Construction"

_REGISTRY: dict[str, list[dict[str, Any]]] = {}


def _records(country: str) -> list[dict[str, Any]]:
    key = country.upper()
    if key not in COUNTRY_FILES:
        raise ValueError(f"no TABULA registry for country {country!r}")
    if key not in _REGISTRY:
        path = ARCHETYPE_DIR / f"tabula_archetypes_{COUNTRY_FILES[key]}.json"
        _REGISTRY[key] = json.loads(path.read_text(encoding="utf-8"))["records"]
    return _REGISTRY[key]


def _has_window_data(record: dict[str, Any]) -> bool:
    u_window = record.get("u_window_w_m2k")
    components = record.get("geometry", {}).get("a_window_components_m2") or []
    return (
        isinstance(u_window, (int, float))
        and not isinstance(u_window, bool)
        and math.isfinite(float(u_window))
        and sum(components) > 0.0
    )


def _share(record: dict[str, Any]) -> float:
    window = sum(record["geometry"]["a_window_components_m2"])
    wall = sum(record["geometry"]["a_wall_components_m2"])
    return window / (window + wall)


def window_record(archetype_id: str, country: str | None = None) -> dict[str, Any]:
    country = (country or archetype_id[:2]).upper()
    records = _records(country)
    own = next((r for r in records if r["archetype_id"] == archetype_id), None)
    if own is None:
        raise ValueError(f"archetype_id not found in {country} TABULA registry: {archetype_id!r}")
    if _has_window_data(own):
        share = _share(own)
        u_window = float(own["u_window_w_m2k"])
        shgc = float(own["g_gl_window"])
        fallback = False
        n_donors = 0
    else:
        donors = [
            r for r in records
            if r["building_type"] == own["building_type"] and _has_window_data(r)
        ]
        if not donors:
            raise ValueError(f"no window donors for {archetype_id!r}")
        share = statistics.median(_share(r) for r in donors)
        u_window = statistics.median(float(r["u_window_w_m2k"]) for r in donors)
        shgc = statistics.median(float(r["g_gl_window"]) for r in donors)
        fallback = True
        n_donors = len(donors)
    f_red = float(own["f_red_temp"])
    delta_u = float(own["delta_u_tb_w_m2k"])
    return {
        "archetype_id": archetype_id,
        "share": share,
        "u_window_w_m2k": u_window,
        "g_gl_window": shgc,
        "delta_u_tb_w_m2k": delta_u,
        "f_red_temp": f_red,
        "u": (u_window + delta_u) * f_red,
        "shgc": shgc,
        "fallback": fallback,
        "n_donors": n_donors,
    }


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _newell(points) -> tuple[float, float, float]:
    nx = ny = nz = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    return (nx, ny, nz)


def polygon_area(points) -> float:
    n = _newell(points)
    return 0.5 * math.sqrt(_dot(n, n))


def is_convex(points) -> bool:
    normal = _newell(points)
    length = math.sqrt(_dot(normal, normal))
    if length == 0.0:
        return False
    sign = 0
    for i in range(len(points)):
        a, b, c = points[i], points[(i + 1) % len(points)], points[(i + 2) % len(points)]
        turn = _dot(_cross(_sub(b, a), _sub(c, b)), normal) / length
        if abs(turn) <= CONVEXITY_TOLERANCE:
            continue
        current = 1 if turn > 0 else -1
        if sign == 0:
            sign = current
        elif current != sign:
            return False
    return sign != 0


def scaled_window(points, share: float):
    factor = math.sqrt(share)
    n = len(points)
    centre = tuple(sum(p[k] for p in points) / n for k in range(3))
    return [tuple(centre[k] + factor * (p[k] - centre[k]) for k in range(3)) for p in points]


def add_tabula_windows(idf, record: dict[str, Any]) -> dict[str, Any]:
    wr = record if "share" in record and "u" in record else window_record(record["archetype_id"])
    u_value = float(wr["u"])
    if not u_value < U_WINDOW_LIMIT_W_M2K:
        raise ValueError(f"window U {u_value:.3f} W/m2K is not below {U_WINDOW_LIMIT_W_M2K}")
    share = float(wr["share"])
    shgc = float(wr["shgc"])

    walls = [
        s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if str(s.Surface_Type).strip().upper() == "WALL"
        and str(s.Outside_Boundary_Condition).strip().upper() == "OUTDOORS"
    ]
    plan = []
    skip_reasons: dict[str, int] = {}
    outdoor_wall_m2 = 0.0
    window_m2 = 0.0
    for wall in walls:
        points = [tuple(float(c) for c in p) for p in wall.coords]
        outdoor_wall_m2 += polygon_area(points) if len(points) >= 3 else 0.0
        if len(points) > 4:
            reason = "more_than_4_vertices"
        elif len(points) < 3 or not is_convex(points):
            reason = "not_convex"
        else:
            window_points = scaled_window(points, share)
            area = polygon_area(window_points)
            if area < MIN_WINDOW_AREA_M2:
                reason = "window_under_0.05_m2"
            else:
                plan.append((wall, window_points))
                window_m2 += area
                continue
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    if plan:
        idf.newidfobject(
            "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
            Name=WINDOW_MATERIAL_NAME,
            UFactor=u_value,
            Solar_Heat_Gain_Coefficient=shgc,
            Visible_Transmittance=min(1.0, shgc),
        )
        idf.newidfobject("CONSTRUCTION", Name=WINDOW_CONSTRUCTION_NAME, Outside_Layer=WINDOW_MATERIAL_NAME)
        for wall, window_points in plan:
            fen = idf.newidfobject(
                "FENESTRATIONSURFACE:DETAILED",
                Name=f"{wall.Name}_Win",
                Surface_Type="Window",
                Construction_Name=WINDOW_CONSTRUCTION_NAME,
                Building_Surface_Name=wall.Name,
                View_Factor_to_Ground="autocalculate",
                Multiplier=1,
            )
            fen.setcoords([tuple(p) for p in window_points])

    return {
        "share_target": share,
        "outdoor_wall_m2": outdoor_wall_m2,
        "window_m2": window_m2,
        "share_achieved": window_m2 / outdoor_wall_m2 if outdoor_wall_m2 > 0.0 else 0.0,
        "walls_with_window": len(plan),
        "walls_skipped": sum(skip_reasons.values()),
        "skip_reasons": json.dumps(skip_reasons, sort_keys=True),
        "u": u_value,
        "shgc": shgc,
        "fallback": bool(wr["fallback"]),
    }
