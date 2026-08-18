"""
OPEN-07 / OPEN-38 T02 measurement.

Diffs the two surviving paired IDFs (A = as_classified_today / SmallHotel,
B = as_recorded_in_t19 / SmallOffice) for way/965718402 and way/965718403,
and runs a subsurface-fit test (OPEN-38's unfitted-subsurface sub-question)
on both sides, with a mandatory control against the repo's healthy
SmallHotel_90.1-2013.idf prototype.

Read-only. Emits openubem/outputs/comparisons/open07_smallhotel_idf_diff.csv.
"""

import csv
import os
import re
import sys

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCRATCH = os.path.join(
    REPO_ROOT, "scratchpad", "e-la-20-investigation", "i03", "work_part1"
)
A_DIR = os.path.join(SCRATCH, "step3_A_as_classified_today", "idfs")
B_DIR = os.path.join(SCRATCH, "step3_B_as_recorded_in_t19_SmallOffice", "idfs")

BUILDINGS = ["way_965718402", "way_965718403"]

CONTROL_IDF = os.path.join(
    REPO_ROOT,
    "docs",
    "docs_DONE",
    "LOADS & SCHEDULES",
    "scheduleDigitization",
    "sources",
    "SmallHotel_90.1-2013.idf",
)

HARVEST_ROOT = r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"

OUT_CSV = os.path.join(
    REPO_ROOT, "openubem", "outputs", "comparisons", "open07_smallhotel_idf_diff.csv"
)

# Tolerances for the subsurface-fit test.
PLANE_TOL_M = 0.02  # max perpendicular distance from subsurface vertex to base-surface plane
POLY_TOL_M = 0.02  # buffer distance a vertex may sit outside the 2D base polygon and still count "fitted"


def parse_idf_objects(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = re.sub(r"!.*", "", text)
    raw_objects = text.split(";")
    objects = []
    for raw in raw_objects:
        raw = raw.strip()
        if not raw:
            continue
        fields = [f.strip() for f in raw.split(",")]
        if not fields or fields[0] == "":
            continue
        obj_type = fields[0].strip().upper()
        objects.append((obj_type, fields))
    return objects


def get_surfaces(objects):
    surfaces = {}
    for obj_type, fields in objects:
        if obj_type != "BUILDINGSURFACE:DETAILED":
            continue
        name = fields[1]
        n_vert = int(float(fields[11]))
        coords = [float(x) for x in fields[12 : 12 + n_vert * 3]]
        verts = [
            (coords[i], coords[i + 1], coords[i + 2]) for i in range(0, len(coords), 3)
        ]
        surfaces[name] = {
            "name": name,
            "surface_type": fields[2],
            "zone_name": fields[4],
            "vertices": verts,
        }
    return surfaces


def get_subsurfaces(objects):
    subs = []
    for obj_type, fields in objects:
        if obj_type != "FENESTRATIONSURFACE:DETAILED":
            continue
        name = fields[1]
        surf_type = fields[2]
        base_surface = fields[4]
        multiplier = float(fields[8])
        n_vert = int(float(fields[9]))
        coords = [float(x) for x in fields[10 : 10 + n_vert * 3]]
        verts = [
            (coords[i], coords[i + 1], coords[i + 2]) for i in range(0, len(coords), 3)
        ]
        subs.append(
            {
                "name": name,
                "surface_type": surf_type,
                "base_surface": base_surface,
                "multiplier": multiplier,
                "vertices": verts,
            }
        )
    return subs


def get_zones(objects):
    return [fields[1] for obj_type, fields in objects if obj_type == "ZONE"]


def polygon_normal(verts):
    # Newell's method
    n = np.zeros(3)
    m = len(verts)
    for i in range(m):
        x1, y1, z1 = verts[i]
        x2, y2, z2 = verts[(i + 1) % m]
        n[0] += (y1 - y2) * (z1 + z2)
        n[1] += (z1 - z2) * (x1 + x2)
        n[2] += (x1 - x2) * (y1 + y2)
    norm = np.linalg.norm(n)
    if norm < 1e-12:
        return None
    return n / norm


def point_in_polygon_2d(pt, poly, tol):
    x, y = pt
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            x_int = xi + (y - yi) * (xj - xi) / (yj - yi + 1e-15)
            if x < x_int:
                inside = not inside
        j = i
    if inside:
        return True
    # not inside by ray-cast: check distance to boundary (edges) for tolerance buffer
    min_dist = min_point_to_polygon_edge_dist((x, y), poly)
    return min_dist <= tol


def min_point_to_polygon_edge_dist(pt, poly):
    px, py = pt
    n = len(poly)
    best = float("inf")
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        seg_len2 = dx * dx + dy * dy
        if seg_len2 < 1e-15:
            d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg_len2))
            cx, cy = x1 + t * dx, y1 + t * dy
            d = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        best = min(best, d)
    return best


def project_to_plane_2d(verts, origin, u, v):
    out = []
    for p in verts:
        rel = np.array(p) - origin
        out.append((float(np.dot(rel, u)), float(np.dot(rel, v))))
    return out


def build_basis(base_verts, normal):
    p0 = np.array(base_verts[0])
    p1 = np.array(base_verts[1])
    edge = p1 - p0
    edge_norm = np.linalg.norm(edge)
    if edge_norm < 1e-9:
        return None
    u = edge / edge_norm
    v = np.cross(normal, u)
    v_norm = np.linalg.norm(v)
    if v_norm < 1e-9:
        return None
    v = v / v_norm
    return p0, u, v


def test_subsurface_fit(sub, base_surface):
    base_verts = base_surface["vertices"]
    if len(base_verts) < 3:
        return None, "base_surface_degenerate"
    normal = polygon_normal(base_verts)
    if normal is None:
        return None, "base_surface_degenerate_normal"
    basis = build_basis(base_verts, normal)
    if basis is None:
        return None, "base_surface_degenerate_basis"
    origin, u, v = basis

    base_2d = project_to_plane_2d(base_verts, origin, u, v)

    max_plane_dist = 0.0
    for p in sub["vertices"]:
        rel = np.array(p) - origin
        dist = abs(float(np.dot(rel, normal)))
        max_plane_dist = max(max_plane_dist, dist)

    sub_2d = project_to_plane_2d(sub["vertices"], origin, u, v)
    all_inside = all(point_in_polygon_2d(pt, base_2d, POLY_TOL_M) for pt in sub_2d)
    coplanar = max_plane_dist <= PLANE_TOL_M

    fitted = bool(all_inside and coplanar)
    detail = f"max_plane_dist={max_plane_dist:.4f};all_vertices_inside_2d={all_inside}"
    return fitted, detail


def run_subsurface_census(idf_path, label):
    objects = parse_idf_objects(idf_path)
    surfaces = get_surfaces(objects)
    subs = get_subsurfaces(objects)
    rows = []
    n_fitted = 0
    n_unfitted = 0
    n_no_base = 0
    for sub in subs:
        base = surfaces.get(sub["base_surface"])
        if base is None:
            n_no_base += 1
            rows.append(
                {
                    "source": label,
                    "subsurface": sub["name"],
                    "surface_type": sub["surface_type"],
                    "base_surface": sub["base_surface"],
                    "fitted": "NO_BASE_SURFACE",
                    "detail": "base surface not found in this IDF",
                }
            )
            continue
        fitted, detail = test_subsurface_fit(sub, base)
        if fitted:
            n_fitted += 1
        else:
            n_unfitted += 1
        rows.append(
            {
                "source": label,
                "subsurface": sub["name"],
                "surface_type": sub["surface_type"],
                "base_surface": sub["base_surface"],
                "fitted": fitted,
                "detail": detail,
            }
        )
    summary = {
        "n_subsurfaces": len(subs),
        "n_fitted": n_fitted,
        "n_unfitted": n_unfitted,
        "n_no_base_surface": n_no_base,
    }
    return summary, rows


def read_err_summary(err_path):
    if not os.path.exists(err_path):
        return None
    with open(err_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    fatal_lines = [
        (i, l.strip()) for i, l in enumerate(lines) if re.search(r"\*\*\s*Fatal\s*\*\*", l)
    ]
    severe_lines = [
        (i, l.strip()) for i, l in enumerate(lines) if re.search(r"\*\*\s*Severe\s*\*\*", l)
    ]
    laundryroom_severes = [
        (i, l.strip())
        for i, l in severe_lines
        if "LAUNDRYROOMFLR1" in l.strip().upper()
    ]
    subsurface_warnings = [
        (i, l.strip())
        for i, l in enumerate(lines)
        if "does not surround subsurface" in l.lower()
    ]
    return {
        "n_fatal": len(fatal_lines),
        "n_severe": len(severe_lines),
        "n_laundryroom_severe": len(laundryroom_severes),
        "n_subsurface_warning": len(subsurface_warnings),
        "fatal_lines": fatal_lines,
        "laundryroom_severes": laundryroom_severes,
        "subsurface_warnings": subsurface_warnings,
    }


def main():
    print("=" * 70)
    print("STEP 1 — artifact verification")
    print("=" * 70)
    artifact_rows = []
    for b in BUILDINGS:
        a_path = os.path.join(A_DIR, f"{b}.idf")
        b_path = os.path.join(B_DIR, f"{b}.idf")
        for label, p in [("A", a_path), ("B", b_path)]:
            exists = os.path.exists(p)
            size = os.path.getsize(p) if exists else 0
            mtime = os.path.getmtime(p) if exists else None
            print(f"{b} [{label}] exists={exists} size={size} mtime={mtime} path={p}")
            artifact_rows.append((b, label, exists, size, mtime, p))
            if not exists or size == 0:
                print(f"FATAL: artifact missing or empty: {p}")
                sys.exit(1)

    control_exists = os.path.exists(CONTROL_IDF)
    control_size = os.path.getsize(CONTROL_IDF) if control_exists else 0
    print(
        f"CONTROL SmallHotel_90.1-2013.idf exists={control_exists} size={control_size} path={CONTROL_IDF}"
    )
    if not control_exists or control_size == 0:
        print("FATAL: control artifact missing or empty")
        sys.exit(1)

    print()
    print("=" * 70)
    print("STEP 4 (GATE) — control: subsurface-fit test on healthy SmallHotel prototype")
    print("=" * 70)
    control_summary, control_rows = run_subsurface_census(CONTROL_IDF, "CONTROL_SmallHotel_prototype")
    print(f"Control summary: {control_summary}")
    unfitted_control = [r for r in control_rows if r["fitted"] is False]
    for r in unfitted_control[:20]:
        print(f"  CONTROL UNFITTED: {r}")

    print()
    print("=" * 70)
    print("STEP 2/3 — A vs B diff, and subsurface-fit census, per building")
    print("=" * 70)
    csv_rows = []
    err_summaries = {}
    for b in BUILDINGS:
        a_path = os.path.join(A_DIR, f"{b}.idf")
        b_path = os.path.join(B_DIR, f"{b}.idf")

        a_objects = parse_idf_objects(a_path)
        b_objects = parse_idf_objects(b_path)

        a_surfaces = get_surfaces(a_objects)
        b_surfaces = get_surfaces(b_objects)
        a_subs = get_subsurfaces(a_objects)
        b_subs = get_subsurfaces(b_objects)
        a_zones = get_zones(a_objects)
        b_zones = get_zones(b_objects)

        a_has_laundry = any("LAUNDRYROOM" in z.upper() for z in a_zones)
        b_has_laundry = any("LAUNDRYROOM" in z.upper() for z in b_zones)

        a_summary, a_rows = run_subsurface_census(a_path, f"{b}_A")
        b_summary, b_rows = run_subsurface_census(b_path, f"{b}_B")

        print(f"\n--- {b} ---")
        print(f"A (SmallHotel):  zones={len(a_zones)} surfaces={len(a_surfaces)} subsurfaces={len(a_subs)} has_LaundryRoom_zone={a_has_laundry}")
        print(f"B (SmallOffice): zones={len(b_zones)} surfaces={len(b_surfaces)} subsurfaces={len(b_subs)} has_LaundryRoom_zone={b_has_laundry}")
        print(f"A subsurface-fit summary: {a_summary}")
        print(f"B subsurface-fit summary: {b_summary}")

        a_multipliers = sorted(set(s["multiplier"] for s in a_subs))
        b_multipliers = sorted(set(s["multiplier"] for s in b_subs))
        print(f"A distinct subsurface multipliers: {a_multipliers}")
        print(f"B distinct subsurface multipliers: {b_multipliers}")

        err_path = os.path.join(
            HARVEST_ROOT, f"nyc_rural_layout_assign", b, "eplusout.err"
        )
        err_summary = read_err_summary(err_path)
        err_summaries[b] = err_summary
        print(f".err cross-check ({err_path}):")
        print(f"  {err_summary}")

        csv_rows.append(
            {
                "building": b,
                "side": "A_SmallHotel_as_classified_today",
                "zone_count": len(a_zones),
                "surface_count": len(a_surfaces),
                "subsurface_count": len(a_subs),
                "has_laundryroom_zone": a_has_laundry,
                "distinct_multipliers": ";".join(str(m) for m in a_multipliers),
                "subsurface_fitted": a_summary["n_fitted"],
                "subsurface_unfitted": a_summary["n_unfitted"],
                "subsurface_no_base_surface": a_summary["n_no_base_surface"],
                "err_n_fatal": err_summary["n_fatal"] if err_summary else None,
                "err_n_severe": err_summary["n_severe"] if err_summary else None,
                "err_n_laundryroom_severe": err_summary["n_laundryroom_severe"] if err_summary else None,
                "err_n_subsurface_warning": err_summary["n_subsurface_warning"] if err_summary else None,
            }
        )
        csv_rows.append(
            {
                "building": b,
                "side": "B_SmallOffice_as_recorded_in_t19",
                "zone_count": len(b_zones),
                "surface_count": len(b_surfaces),
                "subsurface_count": len(b_subs),
                "has_laundryroom_zone": b_has_laundry,
                "distinct_multipliers": ";".join(str(m) for m in b_multipliers),
                "subsurface_fitted": b_summary["n_fitted"],
                "subsurface_unfitted": b_summary["n_unfitted"],
                "subsurface_no_base_surface": b_summary["n_no_base_surface"],
                "err_n_fatal": None,
                "err_n_severe": None,
                "err_n_laundryroom_severe": None,
                "err_n_subsurface_warning": None,
            }
        )

    csv_rows.append(
        {
            "building": "CONTROL_SmallHotel_90.1-2013.idf",
            "side": "control_healthy_prototype",
            "zone_count": None,
            "surface_count": None,
            "subsurface_count": control_summary["n_subsurfaces"],
            "has_laundryroom_zone": None,
            "distinct_multipliers": None,
            "subsurface_fitted": control_summary["n_fitted"],
            "subsurface_unfitted": control_summary["n_unfitted"],
            "subsurface_no_base_surface": control_summary["n_no_base_surface"],
            "err_n_fatal": None,
            "err_n_severe": None,
            "err_n_laundryroom_severe": None,
            "err_n_subsurface_warning": None,
        }
    )

    fieldnames = [
        "building",
        "side",
        "zone_count",
        "surface_count",
        "subsurface_count",
        "has_laundryroom_zone",
        "distinct_multipliers",
        "subsurface_fitted",
        "subsurface_unfitted",
        "subsurface_no_base_surface",
        "err_n_fatal",
        "err_n_severe",
        "err_n_laundryroom_severe",
        "err_n_subsurface_warning",
    ]
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in csv_rows:
            w.writerow(r)
    print(f"\nWrote {OUT_CSV}")

    print()
    print("=" * 70)
    print("way/401910463 scope check")
    print("=" * 70)
    for side_dir, label in [(A_DIR, "A"), (B_DIR, "B")]:
        p = os.path.join(side_dir, "way_401910463.idf")
        print(f"way_401910463 [{label}]: exists={os.path.exists(p)} path={p}")


if __name__ == "__main__":
    main()
