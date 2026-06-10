"""Footprint simplification and form-factor helpers (DESIGN §3A)."""
import math

import pandas as pd
import shapely
import shapely.affinity

from openubem.config import DP_COARSE_TOLERANCE_M, DP_TOLERANCE_M, MAX_VERTICES


def _n_exterior_verts(poly: shapely.Polygon) -> int:
    return len(poly.exterior.coords) - 1


def _append_flag(dq_flag: str, new_token: str) -> str:
    if pd.isna(dq_flag) or dq_flag == "":
        return new_token
    tokens = [t.strip() for t in dq_flag.split(",")]
    if new_token in tokens:
        return dq_flag
    return dq_flag + "," + new_token


def simplify_footprint(
    geom: shapely.Polygon, dq_flag: str
) -> tuple[shapely.Polygon, str, str]:
    poly = shapely.simplify(geom, tolerance=DP_TOLERANCE_M, preserve_topology=True)
    if _n_exterior_verts(poly) <= MAX_VERTICES:
        return (poly, dq_flag, "dp_05")

    poly = shapely.simplify(geom, tolerance=DP_COARSE_TOLERANCE_M, preserve_topology=True)
    if _n_exterior_verts(poly) <= MAX_VERTICES:
        dq_flag = _append_flag(dq_flag, "idf_dp_coarse")
        return (poly, dq_flag, "dp_15")

    poly = geom.convex_hull
    if _n_exterior_verts(poly) <= MAX_VERTICES:
        dq_flag = _append_flag(dq_flag, "idf_hull_simplification")
        return (poly, dq_flag, "hull")

    poly = geom.minimum_rotated_rectangle
    dq_flag = _append_flag(dq_flag, "idf_bbox_simplification")
    return (poly, dq_flag, "bbox")


def validate_simplified(poly: shapely.Polygon) -> str | None:
    if not shapely.is_valid(poly) or poly.area <= 20.0:
        return "skipped_invalid_geometry"
    return None


def translate_to_origin(poly: shapely.Polygon) -> tuple[shapely.Polygon, float, float]:
    cx, cy = poly.centroid.coords[0]
    poly_local = shapely.affinity.translate(poly, xoff=-cx, yoff=-cy)
    return (poly_local, cx, cy)


def derive_num_floors(row: pd.Series, floor_to_floor_m: float = 3.5) -> int:
    if pd.notna(row["levels"]):
        return max(1, int(row["levels"]))
    if pd.notna(row["height_m"]):
        return max(1, math.ceil(row["height_m"] / floor_to_floor_m))
    return 1


def compute_form_factor(
    footprint_area_m2: float,
    perimeter_m: float,
    num_floors: int,
    floor_to_floor_m: float,
) -> tuple[float, float, float]:
    floor_area_m2 = footprint_area_m2 * num_floors
    envelope_surface_m2 = (perimeter_m * num_floors * floor_to_floor_m) + (2 * footprint_area_m2)
    form_factor = envelope_surface_m2 / floor_area_m2
    return (floor_area_m2, envelope_surface_m2, form_factor)
