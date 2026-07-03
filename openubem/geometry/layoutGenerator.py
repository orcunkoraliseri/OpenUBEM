"""Room-level interior layout for non-rectangular footprints (PLAN layoutgenerator).

Generalizes the zone/B1 room-level strategy to L/U/T/O/ribbon footprints:
classify -> decompose to hole-free wings -> corridor spine -> double-loaded room
packing, conserving floor area. Dimensions trace to DOE prototypes (Deru et al. 2011),
ASHRAE 90.1-2019 App-G, and IBC 2021 (zero-fitted). See deepResearch RESULT_L04/L05/L06.
"""
import logging
import math
from enum import Enum

import shapely
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import linemerge, nearest_points, polygonize, unary_union

logger = logging.getLogger("openubem.geometry")

# --- Zero-fitted geometric thresholds (RESULT_L04 Table 2 / RESULT_L05) ---
PERIMETER_DEPTH_M = 4.57          # ASHRAE 90.1-2019 Table G3.1 No.7(a), 15 ft
CLASSIFY_SIMPLIFY_TOL_M = 1.0     # DP tolerance for shape vertex/concave counting (L04 ε)
CLEANUP_SIMPLIFY_TOL_M = 0.1      # DP tolerance for geometry cleanup (L05); 0.25 for noisy OSM
MIN_ZONE_AREA_M2 = 2.0            # sliver floor: merge zones below this (L05)
MIN_CELL_WIDTH_M = 1.0            # drop grid-cut cells narrower than this everywhere (< corridor
                                  # 1.68 m, < any habitable width): real OSM edges are not exactly
                                  # orthogonal, so axis-aligned cuts shear off degenerate slivers
CORNER_MERGE_AREA_M2 = 10.0       # corner-wedge merge threshold (L06)
CORNER_MERGE_ASPECT = 5.0         # corner-wedge merge if aspect ratio exceeds this (L06)
MIN_FOOTPRINT_AREA_M2 = 100.0     # below this: single-zone fallback regardless of shape (L04)
POINT_TOWER_AREA_M2 = 250.0       # compact + below this = point/tower (L04 Table 1)
RECTANGULARITY_COMPACT = 0.85     # area/MBR.area >= this = compact (L04)
CONVEXITY_CONVEX = 0.95           # area/hull.area >= this = convex (L04)
ELONGATION_SLAB = 0.40            # OBB min/max side < this = slab (L04)
OBB_NOTCH_MIN_FRACTION = 0.05     # OBB-difference component >= this fraction of area = real notch (L04)

# --- DOE per-archetype module specs (zero-fitted; Deru et al. 2011 §3.1.15) ---
# family: "units_corridor" (double-loaded corridor packing) | "core_perim" | "single"
MODULE_SPECS: dict[str, dict] = {
    "MidriseApartment": {
        "family": "units_corridor",
        "corridor_width_m": 1.68,        # 5.5 ft (IBC 2021 §1020.3; DOE proto)
        "unit_depth_m": 7.62,            # 25 ft dwelling-unit depth
        "bay_width_m": 11.58,            # 38 ft bay
        "unit_area_m2": 88.25,           # 950 ft^2
        "circulation_fraction": 0.099,   # 9.9% corridor share
        "unit_space_type": "Apartment",
        "corridor_space_type": "Corridor",
        "source": "Deru et al. 2011 (DOE Prototype) Table 3.1.15; IBC 2021 §1020.3",
    },
}


def wing_width_thresholds(spec: dict) -> tuple[float, float]:
    """Algebraic double/single-loaded wing-width thresholds (RESULT_L06, traceable)."""
    c = spec["corridor_width_m"]
    d = spec["unit_depth_m"]
    return (c + 2.0 * d, c + d)  # (W_double, W_single)


class ShapeClass(Enum):
    COMPACT = "compact"
    SLAB = "slab"
    L = "L"
    U = "U"
    T = "T"
    CROSS = "cross"
    O = "O"
    RIBBON = "ribbon"
    POINT = "point"
    IRREGULAR = "irregular"


def _largest_polygon(geom) -> Polygon:
    """Largest Polygon member of a Polygon / MultiPolygon / GeometryCollection.

    GeometryCollection matters: make_valid() on a zero-area spur returns the clean
    polygon plus a dangling LineString; we keep the polygon and discard the line.
    """
    if geom.geom_type == "Polygon":
        return geom
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        polys = [g for g in geom.geoms if g.geom_type == "Polygon" and not g.is_empty]
        if polys:
            return max(polys, key=lambda g: g.area)
    return geom


VERTEX_SNAP_M = 0.005  # 5 mm grid — fallback sliver snap (well under E+ 1 cm coincident tol)


def _clean(poly: Polygon) -> Polygon:
    """Drop zero-area spikes / near-duplicate vertices from polygonize, clip, or union.

    Cutting at a reflex vertex whose line coincides with a boundary edge (e.g. an L's
    inner arm) leaves a degenerate spur. Preferred fix is make_valid (splits the spur
    into a dangling line that _largest_polygon discards) — area-preserving, no snap. For
    a rotation-fuzzed sub-mm sliver that make_valid keeps as a thin polygon, fall back to
    a 5 mm grid snap.
    """
    if poly.is_empty:
        return poly
    p = _largest_polygon(shapely.make_valid(poly))
    if p.geom_type == "Polygon" and not p.is_empty and _min_edge(p) >= VERTEX_SNAP_M:
        return p
    snapped = _largest_polygon(shapely.make_valid(shapely.set_precision(poly, VERTEX_SNAP_M)))
    if snapped.geom_type == "Polygon" and not snapped.is_empty:
        return snapped
    return p


def _min_edge(poly: Polygon) -> float:
    cs = list(poly.exterior.coords)
    return min((math.dist(cs[i], cs[i + 1]) for i in range(len(cs) - 1)), default=0.0)


def _is_degenerate_cell(poly: Polygon) -> bool:
    """A cell E+ cannot simulate: near-zero area, or a strip thinner than MIN_CELL_WIDTH_M.

    Dropping (not merging) is deliberate — merging cells across the grid reintroduces the
    T-junctions that crash geomeppy (T16b). generate_layout's 1% area-conservation net then
    degrades a footprint that loses too much to one_zone_per_floor.
    """
    if poly.area < MIN_ZONE_AREA_M2:
        return True
    return poly.buffer(-MIN_CELL_WIDTH_M / 2.0).is_empty


def _count_reflex_corners(poly: Polygon) -> int:
    """Count re-entrant (concave) exterior corners of a CCW-oriented simple polygon."""
    ring = orient(Polygon(poly.exterior), sign=1.0)  # force CCW, drop holes for corner test
    pts = list(ring.exterior.coords)[:-1]
    n = len(pts)
    reflex = 0
    for i in range(n):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        cx, cy = pts[(i + 1) % n]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if cross < -1e-9:  # CCW: convex vertex cross>0, reflex cross<0
            reflex += 1
    return reflex


def _obb_notch_count(poly: Polygon) -> int:
    """Count significant notches = OBB minus polygon components >= 5% of building area."""
    obb = poly.minimum_rotated_rectangle
    diff = obb.difference(poly)
    if diff.is_empty:
        return 0
    parts = diff.geoms if diff.geom_type == "MultiPolygon" else [diff]
    return sum(1 for p in parts if p.area >= OBB_NOTCH_MIN_FRACTION * poly.area)


def classify_footprint(footprint_poly: Polygon) -> tuple[ShapeClass, dict]:
    """Classify a footprint into a shape class via the RESULT_L04 metric ladder.

    Returns (ShapeClass, metrics) where metrics is a provenance-ready dict of the
    computed geometric ratios. Pure shapely, zero-fitted thresholds.
    """
    poly = shapely.make_valid(footprint_poly)
    poly = _largest_polygon(poly)
    poly = poly.simplify(CLEANUP_SIMPLIFY_TOL_M, preserve_topology=True)

    hull = poly.convex_hull
    mbr = poly.minimum_rotated_rectangle
    mbr_coords = list(mbr.exterior.coords)
    side_a = math.dist(mbr_coords[0], mbr_coords[1])
    side_b = math.dist(mbr_coords[1], mbr_coords[2])
    long_side, short_side = max(side_a, side_b), min(side_a, side_b)

    core = poly.buffer(-PERIMETER_DEPTH_M)
    simp = poly.simplify(CLASSIFY_SIMPLIFY_TOL_M, preserve_topology=True)
    simp = _largest_polygon(shapely.make_valid(simp))

    metrics = {
        "area_m2": poly.area,
        "rectangularity": poly.area / mbr.area if mbr.area else 0.0,
        "convexity": poly.area / hull.area if hull.area else 0.0,
        "compactness_pp": 4.0 * math.pi * poly.area / (poly.length ** 2) if poly.length else 0.0,
        "elongation": (short_side / long_side) if long_side else 0.0,
        "has_interior_ring": len(list(poly.interiors)) > 0,
        "core_empty": core.is_empty,
        "core_area_m2": 0.0 if core.is_empty else core.area,
        "simplified_vertices": len(list(simp.exterior.coords)) - 1,
        "reflex_corners": _count_reflex_corners(simp),
        "obb_notches": None,
    }

    # 1 — interior ring → O-shape/courtyard
    if metrics["has_interior_ring"]:
        return ShapeClass.O, metrics
    # 2 — erosion by 4.57 m collapses core → thin ribbon (no separate core)
    if core.is_empty or core.area < 10.0:
        return ShapeClass.RIBBON, metrics
    # small footprint: single-zone fallback regardless of shape
    if metrics["area_m2"] < MIN_FOOTPRINT_AREA_M2:
        return ShapeClass.RIBBON, metrics
    # 3 — convex + rectangular → compact / slab / point
    if metrics["convexity"] >= CONVEXITY_CONVEX and metrics["rectangularity"] >= RECTANGULARITY_COMPACT:
        if metrics["area_m2"] < POINT_TOWER_AREA_M2 and metrics["compactness_pp"] >= 0.60:
            return ShapeClass.POINT, metrics
        if metrics["elongation"] < ELONGATION_SLAB:
            return ShapeClass.SLAB, metrics
        return ShapeClass.COMPACT, metrics
    # 4/5/6 — concave templates by reflex-corner count (vertex count as cross-check)
    reflex = metrics["reflex_corners"]
    if reflex == 1:
        return ShapeClass.L, metrics
    if reflex == 2:
        metrics["obb_notches"] = _obb_notch_count(simp)
        return (ShapeClass.U if metrics["obb_notches"] <= 1 else ShapeClass.T), metrics
    if reflex >= 4:
        return ShapeClass.CROSS, metrics
    # default — irregular / concave blob
    return ShapeClass.IRREGULAR, metrics


# ---------------------------------------------------------------------------
# Corridor-spine double-loaded room packing (RESULT_L06)
# ---------------------------------------------------------------------------

def _long_edge_angle(obb: Polygon) -> float:
    """Return the angle (degrees) of the longest OBB edge, for local-frame alignment."""
    pts = list(obb.exterior.coords)[:-1]
    best_len, best_ang = -1.0, 0.0
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        length = math.hypot(x1 - x0, y1 - y0)
        if length > best_len:
            best_len = length
            best_ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return best_ang


def _dominant_edge_angle(poly: Polygon) -> float:
    """Angle (degrees) of the polygon's longest actual exterior edge.

    Preferred over the min-area OBB angle for orthogonal alignment: the min-area
    rectangle of a symmetric plus/cross is diagonal, which breaks axis-aligned cuts.
    """
    pts = list(poly.exterior.coords)
    best_len, best_ang = -1.0, 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        length = math.hypot(x1 - x0, y1 - y0)
        if length > best_len:
            best_len = length
            best_ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return best_ang


def _band_zone(local_box: Polygon, rotated_wing: Polygon, angle: float, origin) -> Polygon | None:
    """Clip a local-frame band to the wing, rotate it back to world coords."""
    clipped = local_box.intersection(rotated_wing)
    if clipped.is_empty:
        return None
    clipped = _clean(_largest_polygon(shapely.make_valid(clipped)))
    if clipped.geom_type != "Polygon" or clipped.is_empty:
        return None
    return _clean(affinity.rotate(clipped, angle, origin=origin))


def _merge_slivers(bands: list[dict]) -> list[dict]:
    """Merge sub-min-area bands into the neighbor with the longest shared edge.

    Guarantees exact area conservation (nothing is dropped). Union of edge-adjacent
    rectangles stays a simple hole-free polygon.
    """
    keepers = [b for b in bands if b["polygon"].area >= MIN_ZONE_AREA_M2]
    smalls = [b for b in bands if b["polygon"].area < MIN_ZONE_AREA_M2]
    if not keepers:
        return bands  # caller handles the all-tiny case (whole-wing fallback)
    for s in smalls:
        touch = s["polygon"].buffer(1e-6)
        best = max(keepers, key=lambda k: k["polygon"].intersection(touch).length)
        best["polygon"] = _clean(_largest_polygon(shapely.make_valid(
            unary_union([best["polygon"], s["polygon"]]))))
    return keepers


def _pack_bar(wing_poly: Polygon, spec: dict) -> tuple[list[dict], str]:
    """Pack one hole-free rectangular-ish wing into corridor + oriented perimeter zones.

    Returns (sub_zones, config) where each sub_zone is
    {"polygon", "space_type", "tag"} and config is the fallback-ladder rung fired.
    Tags are underscore-free so the downstream group key (last name token) is unique.
    """
    c = spec["corridor_width_m"]
    d = spec["unit_depth_m"]
    w_double, w_single = wing_width_thresholds(spec)
    unit_st = spec["unit_space_type"]
    corr_st = spec["corridor_space_type"]

    obb = wing_poly.minimum_rotated_rectangle
    angle = _long_edge_angle(obb)
    origin = wing_poly.centroid
    rot = affinity.rotate(wing_poly, -angle, origin=origin)
    minx, miny, maxx, maxy = rot.bounds
    Lx, Ly = maxx - minx, maxy - miny  # Lx >= Ly by long-edge alignment
    W = Ly

    # narrow wing: no room for corridor + units → single whole-wing zone (fallback)
    if W < w_single:
        return ([{"polygon": wing_poly, "space_type": unit_st, "tag": "whole"}],
                "wing_fallback_narrow")

    # E/W end-bands only when the wing is long enough to leave a real corridor middle
    end_d = d if Lx > 2.0 * d + spec["bay_width_m"] else 0.0
    x0, x1 = minx + end_d, maxx - end_d  # corridor/side-band x-extent (inset from ends)

    def wb(a, b, e, f):  # world-frame band from local rectangle
        return _band_zone(box(a, b, e, f), rot, angle, origin)

    subs: list[dict] = []

    if W >= w_double:
        config = "double_loaded"
        row = (Ly - c) / 2.0
        cy0, cy1 = miny + row, miny + row + c  # corridor y-extent (centered)
        bands = [
            (wb(minx, miny, minx + end_d, maxy), unit_st, "pw"),   # West end
            (wb(maxx - end_d, miny, maxx, maxy), unit_st, "pe"),   # East end
            (wb(x0, cy1, x1, maxy), unit_st, "pn"),                # North row
            (wb(x0, miny, x1, cy0), unit_st, "ps"),                # South row
            (wb(x0, cy0, x1, cy1), corr_st, "corr"),               # corridor spine
        ]
    else:
        config = "single_loaded"
        cy1 = miny + c  # corridor along south edge
        bands = [
            (wb(minx, miny, minx + end_d, maxy), unit_st, "pw"),   # West end
            (wb(maxx - end_d, miny, maxx, maxy), unit_st, "pe"),   # East end
            (wb(x0, cy1, x1, maxy), unit_st, "pn"),                # single unit row
            (wb(x0, miny, x1, cy1), corr_st, "corr"),              # corridor
        ]

    for poly, st, tag in bands:
        if poly is not None:
            subs.append({"polygon": poly, "space_type": st, "tag": tag})
    subs = _merge_slivers(subs)
    if not subs or all(s["polygon"].area < MIN_ZONE_AREA_M2 for s in subs):
        return ([{"polygon": wing_poly, "space_type": unit_st, "tag": "whole"}],
                "wing_fallback_degenerate")
    return subs, config


def _emit_floor_zones(
    osm_id: str, wing_id: int, sub_zones: list[dict], archetype_id: str,
    num_floors: int, floor_to_floor_m: float, config: str,
) -> list[dict]:
    """Stack per-wing sub-zones across floors into extrude-ready zone dicts.

    Naming: {osm_id}_F{i}_w{wing}{tag} — the last token (w{wing}{tag}) is the group key,
    so each distinct sub-polygon becomes its own add_block stacked num_floors storeys.
    """
    zones: list[dict] = []
    for sub in sub_zones:
        poly = sub["polygon"]
        coords = list(poly.exterior.coords)[:-1]
        token = f"w{wing_id}{sub['tag']}"
        for i in range(num_floors):
            zones.append({
                "name": f"{osm_id}_F{i}_{token}",
                "mode": "room_layout",
                "floor_polygon": poly,
                "coords_m": coords,
                "z_floor": i * floor_to_floor_m,
                "z_ceiling": (i + 1) * floor_to_floor_m,
                "height_m": floor_to_floor_m,
                "archetype_id": archetype_id,
                "floor_area_m2": poly.area,
                "space_type": sub["space_type"],
                "generation_status_note": config,
            })
    return zones


def _reflex_points(poly: Polygon) -> list[tuple[float, float]]:
    ring = orient(Polygon(poly.exterior), sign=1.0)
    pts = list(ring.exterior.coords)[:-1]
    n = len(pts)
    out = []
    for i in range(n):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        cx, cy = pts[(i + 1) % n]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if cross < -1e-9:
            out.append((bx, by))
    return out


def _orthogonal_cut(poly: Polygon, values: list[float], axis: str) -> list[Polygon]:
    """Split poly with full-span axis-aligned lines at the given coordinate values."""
    minx, miny, maxx, maxy = poly.bounds
    lines = []
    for v in values:
        if axis == "x":
            lines.append(LineString([(v, miny - 1.0), (v, maxy + 1.0)]))
        else:
            lines.append(LineString([(minx - 1.0, v), (maxx + 1.0, v)]))
    merged = unary_union([poly.boundary, *lines])
    return [p for p in polygonize(merged) if poly.contains(p.representative_point())]


def _decompose_wings(poly: Polygon) -> list[Polygon]:
    """Decompose an L/U/T/cross footprint into hole-free rectangular wings (RESULT_L05).

    Aligns to the footprint's orthogonal frame, casts cutting lines from reflex
    vertices along x and y, and keeps whichever axis yields the most rectangular wings.
    """
    ang = _dominant_edge_angle(poly)
    origin = poly.centroid
    aligned = affinity.rotate(poly, -ang, origin=origin)
    reflex = _reflex_points(aligned)
    if not reflex:
        return [poly]

    xs = sorted({round(p[0], 3) for p in reflex})
    ys = sorted({round(p[1], 3) for p in reflex})
    candidates = []
    for axis, vals in (("x", xs), ("y", ys)):
        pieces = [p for p in _orthogonal_cut(aligned, vals, axis) if p.area >= MIN_ZONE_AREA_M2]
        if len(pieces) >= 2:
            candidates.append(pieces)
    if not candidates:
        return [poly]

    def score(pieces):  # highest mean rectangularity, then fewest pieces
        mean_rect = sum(p.area / p.minimum_rotated_rectangle.area for p in pieces) / len(pieces)
        return (round(mean_rect, 6), -len(pieces))

    best = max(candidates, key=score)
    wings = [_clean(affinity.rotate(p, ang, origin=origin)) for p in best]
    return [w for w in wings if not w.is_empty and w.area >= MIN_ZONE_AREA_M2]


def _split_donut(poly: Polygon) -> list[Polygon]:
    """Split an O/courtyard footprint into hole-free wings around the void (RESULT_L05).

    Cuts full-span axis lines at each interior ring's bounding edges, polygonizes, and
    keeps the surrounding cells (the courtyard cell is excluded). Each wing extrudes as
    its own block, so courtyard-facing walls have no partner and stay Outdoors, and the
    inner/outer rings are never merged — the donut E+ Fatal (zoning.py:89) cannot recur.
    """
    if not list(poly.interiors):
        return [Polygon(poly.exterior)]

    ang = _dominant_edge_angle(Polygon(poly.exterior))
    origin = poly.centroid
    aligned = affinity.rotate(poly, -ang, origin=origin)
    minx, miny, maxx, maxy = aligned.bounds

    xs: set[float] = set()
    ys: set[float] = set()
    for ring in aligned.interiors:
        hx0, hy0, hx1, hy1 = LineString(ring).bounds
        xs.update([round(hx0, 3), round(hx1, 3)])
        ys.update([round(hy0, 3), round(hy1, 3)])

    lines = [LineString([(x, miny - 1.0), (x, maxy + 1.0)]) for x in xs]
    lines += [LineString([(minx - 1.0, y), (maxx + 1.0, y)]) for y in ys]
    merged = unary_union([aligned.boundary, *lines])
    pieces = [
        p for p in polygonize(merged)
        if aligned.contains(p.representative_point()) and p.area >= MIN_ZONE_AREA_M2
    ]
    if not pieces:
        return [Polygon(poly.exterior)]
    wings = [_clean(affinity.rotate(p, ang, origin=origin)) for p in pieces]
    return [w for w in wings if not w.is_empty and w.area >= MIN_ZONE_AREA_M2]


# ---------------------------------------------------------------------------
# Connected corridor spine (RESULT_L06): one continuous double-loaded corridor
# that turns at wing junctions instead of an isolated stub per wing. The DOE
# prototype's central corridor is a single connected run; L/U/T/cross/O footprints
# must preserve that (a walkable path), not fragment it.
# ---------------------------------------------------------------------------

def _wing_centerline(wing: Polygon) -> LineString:
    """Long-axis midline of an axis-aligned wing rectangle (aligned frame)."""
    wx0, wy0, wx1, wy1 = wing.bounds
    if (wx1 - wx0) >= (wy1 - wy0):
        y = 0.5 * (wy0 + wy1)
        return LineString([(wx0, y), (wx1, y)])
    x = 0.5 * (wx0 + wx1)
    return LineString([(x, wy0), (x, wy1)])


def _components(net) -> list:
    """Connected line components of a (Multi)LineString after node-merging."""
    merged = linemerge(net) if net.geom_type == "MultiLineString" else net
    return list(merged.geoms) if merged.geom_type == "MultiLineString" else [merged]


def _connect_centerlines(lines: list[LineString], footprint: Polygon) -> "object":
    """Join disjoint wing midlines into one connected network with L-bridges.

    Each pass links the two nearest components with an orthogonal (horizontal-then-
    vertical) bridge that stays inside the footprint, so the corridor turns square
    corners at junctions. Falls back to the direct segment if no L-elbow fits.
    """
    net = unary_union(lines)
    parts = _components(net)
    guard = 0
    while len(parts) > 1 and guard < 64:
        guard += 1
        best = None
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                d = parts[i].distance(parts[j])
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        pa, pb = nearest_points(parts[i], parts[j])
        bridge = None
        for corner in ((pb.x, pa.y), (pa.x, pb.y)):
            cand = LineString([(pa.x, pa.y), corner, (pb.x, pb.y)])
            if footprint.buffer(1e-6).contains(cand):
                bridge = cand
                break
        if bridge is None:
            bridge = LineString([(pa.x, pa.y), (pb.x, pb.y)])
        net = unary_union([net, bridge])
        parts = _components(net)
    return net


def _spine_cut_values(net, wings: list[Polygon], spec: dict) -> tuple[list[float], list[float]]:
    """Grid-cut coordinates: corridor edges (centerline +/- c/2) and wing bounds.

    Placing cuts on the corridor edges makes every grid cell fall wholly inside or
    wholly outside the corridor, so a single point-in-corridor test tags each cell.
    No bay subdivision: apartments coarsen to cardinal bands (matching the validated
    single-wing _pack_bar behavior), which keeps the tiling conforming and low-count.
    """
    c = spec["corridor_width_m"]
    xs: set[float] = set()
    ys: set[float] = set()
    geoms = net.geoms if net.geom_type == "MultiLineString" else [net]
    for g in geoms:
        cs = list(g.coords)
        for (x0, y0), (x1, y1) in zip(cs[:-1], cs[1:]):
            if abs(y1 - y0) <= 1e-6:            # horizontal run → corridor edges only
                ys.update([y0 - c / 2.0, y0 + c / 2.0])
            elif abs(x1 - x0) <= 1e-6:          # vertical run → corridor edges only
                xs.update([x0 - c / 2.0, x0 + c / 2.0])
    for w in wings:
        wx0, wy0, wx1, wy1 = w.bounds
        xs.update([wx0, wx1])
        ys.update([wy0, wy1])
    return _dedupe(xs), _dedupe(ys)


def _dedupe(vals: set[float], tol: float = 0.05) -> list[float]:
    """Collapse cut coordinates closer than tol so the grid has no degenerate slivers.

    Two cut lines within tol (e.g. a corridor edge grazing a wing bound) would carve a
    ~0-width cell whose extruded wall E+ flags as a degenerate surface; keep one.
    """
    out: list[float] = []
    for v in sorted(vals):
        if not out or v - out[-1] > tol:
            out.append(v)
    return out


def _grid_cut(poly: Polygon, xs: list[float], ys: list[float]) -> list[Polygon]:
    """Slice poly with full-span axis lines at xs/ys; keep interior cells.

    poly.boundary carries any interior ring, so cells over a courtyard void are
    dropped and no emitted cell inherits a hole (the donut E+ Fatal cannot recur).
    """
    minx, miny, maxx, maxy = poly.bounds
    m = 0.05  # drop cut lines grazing the boundary (poly.boundary already cuts there) → no slivers
    lines = [LineString([(x, miny - 1.0), (x, maxy + 1.0)]) for x in xs if minx + m < x < maxx - m]
    lines += [LineString([(minx - 1.0, y), (maxx + 1.0, y)]) for y in ys if miny + m < y < maxy - m]
    merged = unary_union([poly.boundary, *lines])
    return [p for p in polygonize(merged)
            if poly.contains(p.representative_point()) and p.area >= 1e-6]


def _wings_in_frame(poly: Polygon, is_donut: bool) -> list[Polygon]:
    """Decompose an already axis-aligned footprint into rectangular wings, no rotation.

    Same logic as _decompose_wings / _split_donut but operating in-frame, so the caller
    performs exactly ONE rotation round-trip (compound rotation fuzzes the aligned
    rectangles and breaks machine-precision area conservation on rotated footprints).
    """
    if is_donut:
        if not list(poly.interiors):
            return [Polygon(poly.exterior)]
        minx, miny, maxx, maxy = poly.bounds
        xs: set[float] = set()
        ys: set[float] = set()
        for ring in poly.interiors:
            hx0, hy0, hx1, hy1 = LineString(ring).bounds
            xs.update([hx0, hx1])   # exact (no rounding) so cuts match the footprint vertices
            ys.update([hy0, hy1])
        lines = [LineString([(x, miny - 1.0), (x, maxy + 1.0)]) for x in xs]
        lines += [LineString([(minx - 1.0, y), (maxx + 1.0, y)]) for y in ys]
        merged = unary_union([poly.boundary, *lines])
        pieces = [p for p in polygonize(merged)
                  if poly.contains(p.representative_point()) and p.area >= MIN_ZONE_AREA_M2]
        return pieces or [Polygon(poly.exterior)]

    reflex = _reflex_points(poly)
    if not reflex:
        return [poly]
    xs = sorted({p[0] for p in reflex})   # exact (no rounding) so cuts match footprint vertices
    ys = sorted({p[1] for p in reflex})
    candidates = []
    for axis, vals in (("x", xs), ("y", ys)):
        pieces = [p for p in _orthogonal_cut(poly, vals, axis) if p.area >= MIN_ZONE_AREA_M2]
        if len(pieces) >= 2:
            candidates.append(pieces)
    if not candidates:
        return [poly]

    def score(pieces):
        mean_rect = sum(p.area / p.minimum_rotated_rectangle.area for p in pieces) / len(pieces)
        return (round(mean_rect, 6), -len(pieces))

    return max(candidates, key=score)


def _pack_connected_spine(
    poly_world: Polygon, spec: dict, is_donut: bool,
) -> list[dict] | None:
    """Pack a multi-wing footprint around ONE connected corridor spine.

    Returns world-frame sub-zones [{polygon, space_type, tag}], or None to let the
    caller fall back to independent per-wing packing. Corridor = the buffered spine
    network intersected with the footprint; apartments = footprint minus corridor,
    grid-sliced into simple (hole-free) cells so extrusion stays Fatal-free.
    """
    ang = _dominant_edge_angle(Polygon(poly_world.exterior))
    origin = poly_world.centroid
    aligned = _largest_polygon(shapely.make_valid(affinity.rotate(poly_world, -ang, origin=origin)))
    if aligned.geom_type != "Polygon":
        return None
    wings = [w for w in _wings_in_frame(aligned, is_donut)
             if w.geom_type == "Polygon" and w.area >= MIN_ZONE_AREA_M2]
    if len(wings) < 2:
        return None

    c = spec["corridor_width_m"]
    net = _connect_centerlines([_wing_centerline(w) for w in wings], aligned)
    corridor = net.buffer(c / 2.0, cap_style=2, join_style=2).intersection(aligned)
    corridor = shapely.make_valid(corridor)

    xs, ys = _spine_cut_values(net, wings, spec)
    cells = _grid_cut(aligned, xs, ys)
    if not cells:
        return None

    unit_st = spec["unit_space_type"]
    corr_st = spec["corridor_space_type"]
    # The full-span grid cut is conforming by construction (every cell edge lies on a
    # global grid line), so intersect_match never hits its coplanar-containment IndexError;
    # emit cells directly. Corridor cells = those whose point falls inside the buffered spine.
    subs: list[dict] = []
    for cell in cells:
        rp = cell.representative_point()
        st = corr_st if corridor.contains(rp) else unit_st
        subs.append({"polygon": cell, "space_type": st, "tag": ""})
    if not subs:
        return None

    out: list[dict] = []
    ci = ui = 0
    for s in subs:
        aligned_poly = s["polygon"].simplify(0.001, preserve_topology=True)  # drop collinear verts
        world_poly = _clean(affinity.rotate(aligned_poly, ang, origin=origin))
        if world_poly.is_empty or world_poly.geom_type != "Polygon" or _is_degenerate_cell(world_poly):
            continue  # drop slivers (don't merge — merging remakes the T16b T-junction crash);
                      # generate_layout's 1% area net degrades to one_zone_per_floor if too much goes
        if s["space_type"] == corr_st:
            tag = f"c{ci}"; ci += 1
        else:
            tag = f"u{ui}"; ui += 1
        out.append({"polygon": world_poly, "space_type": s["space_type"], "tag": tag})
    return out or None


def generate_layout(
    osm_id: str,
    footprint_poly: Polygon,
    archetype_id: str,
    num_floors: int,
    floor_to_floor_m: float = 3.5,
) -> list[dict]:
    """Generate room-level zone dicts for a units+corridor archetype.

    Returns [] when the archetype/shape is unsupported so the caller can fall back
    to one_zone_per_floor. Extrude-ready: each sub-polygon becomes its own add_block.
    """
    spec = MODULE_SPECS.get(archetype_id)
    if spec is None or spec.get("family") != "units_corridor":
        return []

    shape, _metrics = classify_footprint(footprint_poly)
    poly = _largest_polygon(shapely.make_valid(footprint_poly))
    poly = poly.simplify(CLEANUP_SIMPLIFY_TOL_M, preserve_topology=True)

    multi_wing = False
    if shape in (ShapeClass.COMPACT, ShapeClass.SLAB, ShapeClass.POINT):
        wings = [Polygon(poly.exterior)]
    elif shape in (ShapeClass.L, ShapeClass.U, ShapeClass.T, ShapeClass.CROSS):
        wings = _decompose_wings(poly)
        multi_wing = True
    elif shape is ShapeClass.O:
        wings = _split_donut(poly)
        multi_wing = True
    else:  # RIBBON / IRREGULAR → let caller fall back
        return []

    zones: list[dict] = []
    # Multi-wing footprints: one connected corridor spine turning at junctions.
    if multi_wing:
        spine = _pack_connected_spine(poly, spec, shape is ShapeClass.O)
        if spine:
            zones = _emit_floor_zones(
                osm_id, 0, spine, archetype_id, num_floors, floor_to_floor_m, "connected_spine",
            )
    # Single wing, or spine declined → independent per-wing packing (fallback).
    if not zones:
        for wing_id, wing in enumerate(wings):
            if wing.is_empty or wing.area < MIN_ZONE_AREA_M2:
                continue
            subs, config = _pack_bar(wing, spec)
            zones.extend(_emit_floor_zones(
                osm_id, wing_id, subs, archetype_id, num_floors, floor_to_floor_m, config,
            ))
    if not zones:
        return []

    # Conservation safety-net: a mis-decomposed footprint (e.g. some rotated U/T cases)
    # must degrade to one_zone_per_floor rather than emit a badly-conserved layout.
    gen_area = sum(z["floor_area_m2"] for z in zones) / num_floors
    if abs(gen_area - poly.area) > 0.01 * poly.area:
        logger.warning(
            "osm_id=%s room_layout area drift %.2f%% > 1%% (%s) → fallback",
            osm_id, 100.0 * (gen_area - poly.area) / poly.area, shape.value,
        )
        return []
    return zones
