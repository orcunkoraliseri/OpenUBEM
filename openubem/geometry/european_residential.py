"""Ruled dwelling/core allocation for European TABULA archetypes (D-EU-01).

This module deliberately establishes allocation semantics before an observed
footprint adapter supplies polygons.  The core is additional unconditioned
geometry and never reduces TABULA's conditioned ``A_C_Ref`` floor plate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.ops import split, unary_union

from openubem.geometry.european_nocore import cut_storey_nocore


# --- EU-13B: ruled dwelling-layout scheme (footprint regularization, grid,
# morphological branching, habitability retry).  These are additive to the
# module above: ``generate_european_dwelling_layout`` keeps its existing
# behaviour unchanged as the ``equal_strip_multi_angle_sweep`` secondary
# route for storeys the ruled grid cannot serve.

RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 12
DWELLING_DENSITY_REFUSAL_TOKEN = f"DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_{RULED_GRID_MAX_DWELLINGS_PER_FLOOR}"
REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02
# FINDING 204 (PROMPT_EU-13B): MVP 4.3's 6-12% of GFA and 12.0-25.0 m2/floor
# bands are jointly satisfiable only for plates of 100.0-416.7 m2.  The owner
# has not ruled which criterion binds; this task measures and reports, and
# the percentage rule is applied per the prototype's documented resolution.
CIRCULATION_FRACTION_OF_PLATE = 0.09
# D-EU-39 §3 / EU-15 T05: the ruled band is 2-4 dwellings/storey for a
# centroidal stair core (report Sec 6.1-6.2), so a 2-dwelling storey
# (``ruled_grid_2x1``) carves and emits a core exactly like a 3- or
# 4-dwelling one. Was 3 (FINDING 209: 682 ruled_grid_2x1 buildings carried
# no circulation at all).
CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION = 2
CIRCULATION_ABSOLUTE_BAND_M2 = (12.0, 25.0)
LINEAR_GALLERY_ASPECT_THRESHOLD = 2.0
CORRIDOR_SPINE_WIDTH_M = 1.80
# D-EU-39 §3: the carved core/corridor is emitted as its own unconditioned
# thermal zone -- no heating/cooling, this constant infiltration rate only.
CIRCULATION_INFILTRATION_M3_S_M2 = 0.000500


@dataclass(frozen=True)
class EuropeanFootprintRegularization:
    """Report Sec 3: ``ConvexToConcave`` / ``EdgeTo4`` footprint regularization.

    The regularized polygon is an orthogonal quadrilateral fitted to the
    plate's own principal axes (``fit_quadrilateral_domain``) and rescaled to
    preserve gross floor area exactly, per the report's own stated design
    ("Preserves the gross internal floor area ... while regularizing edge
    vectors", Sec 3.2).  ``plate_area_delta_fraction`` is therefore expected
    to sit near zero for the vast majority of real footprints; the 2% gate
    is a numerical safety net for degenerate geometry, not a routine filter.
    """

    regularized_polygon: BaseGeometry
    plate_area_raw_m2: float
    plate_area_regularized_m2: float
    plate_area_delta_fraction: float
    vertices_raw: int
    vertices_regularized: int

    @property
    def exceeds_fallback_band(self) -> bool:
        return self.plate_area_delta_fraction > REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION


def fit_quadrilateral_domain(footprint: BaseGeometry) -> BaseGeometry:
    """Report Sec 3.2 ``EdgeTo4``: fit a 4-vertex orthogonal quadrilateral domain.

    Orientation and aspect come from the minimum rotated rectangle (the
    plate's own principal axes); the rectangle is then rescaled uniformly
    about its own centroid so its area matches the input polygon's area
    exactly, satisfying the report's explicit area-preservation contract.
    Deliberately imports nothing from the partitioner: this is an input to
    it, never the reverse.
    """
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")
    raw_area = float(footprint.area)
    rectangle = footprint.minimum_rotated_rectangle
    if rectangle.geom_type != "Polygon" or len(rectangle.exterior.coords) - 1 != 4:
        raise ValueError("minimum_rotated_rectangle did not produce a quadrilateral")
    rectangle_area = float(rectangle.area)
    if rectangle_area <= 0.0:
        raise ValueError("footprint minimum_rotated_rectangle has non-positive area")
    scale = math.sqrt(raw_area / rectangle_area)
    scaled = affinity.scale(rectangle, xfact=scale, yfact=scale, origin=rectangle.centroid)
    return orient(scaled, sign=1.0)


def regularize_footprint_orthogonal(
    footprint: BaseGeometry, *, tolerance_m: float = 0.15
) -> EuropeanFootprintRegularization:
    """Report Sec 3.1-3.3: drop colinear vertices, then fit the quad domain.

    Colinear-vertex removal within ``tolerance_m`` is delegated to Shapely's
    topology-preserving simplify, which is the same "spatial tolerance
    threshold" operation Sec 3.1 describes.  ``fit_quadrilateral_domain`` is
    never called on the raw, unsimplified ring directly.
    """
    if not math.isfinite(tolerance_m) or tolerance_m < 0.0:
        raise ValueError("tolerance_m must be finite and non-negative")
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")
    raw_area = float(footprint.area)
    vertices_raw = len(footprint.exterior.coords) - 1
    simplified = footprint.simplify(tolerance_m, preserve_topology=True)
    if simplified.is_empty or not simplified.is_valid or simplified.area <= 0.0 or simplified.geom_type != "Polygon":
        simplified = footprint
    quad = fit_quadrilateral_domain(simplified)
    vertices_regularized = len(quad.exterior.coords) - 1
    regularized_area = float(quad.area)
    delta = abs(regularized_area - raw_area) / raw_area
    return EuropeanFootprintRegularization(
        regularized_polygon=quad,
        plate_area_raw_m2=raw_area,
        plate_area_regularized_m2=regularized_area,
        plate_area_delta_fraction=delta,
        vertices_raw=vertices_raw,
        vertices_regularized=vertices_regularized,
    )


def _equal_area_axis_cuts(
    polygon: BaseGeometry, *, axis_angle_deg: float, n_parts: int, origin: BaseGeometry
) -> list[BaseGeometry]:
    """Equal-area bisection slices of ``polygon`` along ``axis_angle_deg``.

    This is the T04/EXAMPLE-mandated prototype decision: dwellings (and
    columns/rows of the ruled grid) are cut as equal-AREA slices of the real
    plate by bisection, never equal-width strips of a bounding box.  Works
    on polygons with interior holes (a plate with a carved-out circulation
    region) because area is measured by intersection, which already accounts
    for any hole.
    """
    if n_parts <= 0:
        raise ValueError("n_parts must be positive")
    aligned = affinity.rotate(polygon, -axis_angle_deg, origin=origin)
    min_x, min_y, max_x, max_y = aligned.bounds
    pad = max(max_x - min_x, max_y - min_y, 1.0) * 2.0
    cuts = [min_x]
    for k in range(1, n_parts):
        desired = k * (aligned.area / n_parts)
        lo, hi = cuts[-1], max_x
        for _ in range(48):
            mid = (lo + hi) / 2.0
            clip = box(min_x - pad, min_y - pad, mid, max_y + pad)
            if aligned.intersection(clip).area < desired:
                lo = mid
            else:
                hi = mid
        cuts.append((lo + hi) / 2.0)
    cuts.append(max_x)
    parts: list[BaseGeometry] = []
    for index in range(n_parts):
        clip = box(cuts[index], min_y - pad, cuts[index + 1], max_y + pad)
        piece = aligned.intersection(clip)
        if piece.geom_type in ("MultiPolygon", "GeometryCollection"):
            polygons = [g for g in piece.geoms if g.geom_type == "Polygon" and g.area > 0.0]
            if not polygons:
                raise ValueError("equal-area axis cut produced no polygon at this index")
            piece = max(polygons, key=lambda geom: geom.area)
        elif piece.geom_type != "Polygon" or piece.is_empty:
            raise ValueError("equal-area axis cut produced a non-polygon piece")
        parts.append(affinity.rotate(piece, axis_angle_deg, origin=origin))
    return parts


_DENSITY_GRID_TABLE: dict[int, tuple[int, int, str, bool]] = {
    # dwelling_count -> (nu, nv, ruled grid name, merge middle columns down to the count)
    1: (1, 1, "ruled_grid_1x1", False),
    2: (2, 1, "ruled_grid_2x1", False),
    3: (2, 2, "ruled_grid_2x2", True),
    4: (2, 2, "ruled_grid_2x2", False),
    5: (3, 2, "ruled_grid_3x2", True),
    6: (3, 2, "ruled_grid_3x2", False),
    7: (4, 2, "ruled_grid_4x2", True),
    8: (4, 2, "ruled_grid_4x2", False),
    9: (6, 2, "ruled_grid_6x2", True),
    10: (6, 2, "ruled_grid_6x2", True),
    11: (6, 2, "ruled_grid_6x2", True),
    12: (6, 2, "ruled_grid_6x2", False),
}


def _grid_for_count(dwelling_count: int) -> tuple[int, int, str, bool]:
    if dwelling_count in _DENSITY_GRID_TABLE:
        return _DENSITY_GRID_TABLE[dwelling_count]
    # Downgrade candidates keep nv and drop nu by one, redistributing the
    # exact requested count via merges -- used only by the habitability
    # retry, never to serve counts the ruled table does not define.
    raise ValueError(f"{dwelling_count} has no ruled grid (max {RULED_GRID_MAX_DWELLINGS_PER_FLOOR}/floor)")


def _merge_grid_cells(cells: list[list[BaseGeometry]], nu: int, nv: int, target_count: int) -> list[BaseGeometry]:
    """Union adjacent same-column cells until exactly ``target_count`` remain.

    Merges are applied to the middle column(s) first (report Sec 5: "2
    middle single-aspect units" merge into one landlocked-safe unit before
    any corner column is touched), matching the report's own 3x2 diagram.
    """
    columns = [list(column) for column in cells]
    total = nu * nv
    to_merge = total - target_count
    if to_merge < 0:
        raise ValueError("target_count exceeds the base grid cell count")
    order = sorted(range(nu), key=lambda i: abs(i - (nu - 1) / 2.0))
    idx = 0
    while to_merge > 0 and idx < len(order):
        column_index = order[idx]
        column = columns[column_index]
        if len(column) >= 2:
            merged = unary_union([column[0], column[1]])
            if merged.geom_type == "MultiPolygon":
                merged = max(merged.geoms, key=lambda geom: geom.area)
            columns[column_index] = [merged] + column[2:]
            to_merge -= 1
        else:
            idx += 1
    if to_merge > 0:
        raise ValueError("could not reach target_count via single-pair column merges")
    flat: list[BaseGeometry] = [cell for column in columns for cell in column]
    return flat


def _build_grid_cells(
    plate: BaseGeometry, *, nu: int, nv: int, axis_angle_deg: float, origin: BaseGeometry
) -> list[list[BaseGeometry]]:
    columns = _equal_area_axis_cuts(plate, axis_angle_deg=axis_angle_deg, n_parts=nu, origin=origin)
    grid: list[list[BaseGeometry]] = []
    for column in columns:
        if nv == 1:
            grid.append([column])
        else:
            grid.append(_equal_area_axis_cuts(column, axis_angle_deg=(axis_angle_deg + 90.0) % 180.0, n_parts=nv, origin=origin))
    return grid


def _centred_circulation_region(plate: BaseGeometry, *, axis_angle_deg: float, origin: BaseGeometry, area_m2: float) -> BaseGeometry:
    """A centroidal rectangle of exactly ``area_m2``, aligned to the plate's axes."""
    aligned = affinity.rotate(plate, -axis_angle_deg, origin=origin)
    min_x, min_y, max_x, max_y = aligned.bounds
    width, height = max_x - min_x, max_y - min_y
    aspect = width / height if height > 0 else 1.0
    core_height = math.sqrt(area_m2 / aspect) if aspect > 0 else math.sqrt(area_m2)
    core_width = area_m2 / core_height
    core_width = min(core_width, width * 0.9)
    core_height = min(core_height, height * 0.9)
    cx, cy = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    rect = box(cx - core_width / 2.0, cy - core_height / 2.0, cx + core_width / 2.0, cy + core_height / 2.0)
    return affinity.rotate(rect, axis_angle_deg, origin=origin)


@dataclass(frozen=True)
class EuropeanGridLayout:
    """A ruled ``n_u x n_v`` grid partition of one storey (T04/T05/T07a)."""

    scheme: str
    grid: str
    nu: int
    nv: int
    dwelling_polygons: tuple[BaseGeometry, ...]
    circulation_polygon: BaseGeometry | None
    circulation_area_m2: float
    circulation_pct_of_plate: float
    circulation_outside_ruled_absolute_band: bool
    facade_contact_lengths_m: tuple[float, ...]
    habitability_rotation_applied: bool
    habitability_downgrade_applied: bool
    partition_audit: EuropeanFloorPartitionAudit | None
    fallback_reason: str | None
    dwelling_layout_emitted: bool
    # EU-21 P05 / S4 (``regularized_envelope_grid``): the fraction of the
    # footprint outside the largest inscribed envelope, folded into
    # circulation. ``None`` for every other scheme -- never reported as if
    # it were a ruled grid.
    residual_fraction: float | None = None


def generate_european_grid_layout(
    plate: BaseGeometry,
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
    axis_angle_deg: float | None = None,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """Report Sec 5: the ruled ``n_u x n_v`` point-block grid, primary scheme.

    ``plate`` must already be the T03-regularized quadrilateral domain.  The
    habitability retry (T07a) first rotates the cutting frame 90 degrees at
    the same grid and the same dwelling count; if that still leaves a
    landlocked cell, it downgrades to the next coarser grid (``nu - 1``
    columns) while redistributing the exact same ``dwelling_count`` via
    column merges.  A count reduction is never attempted.
    """
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")
    if plate.geom_type != "Polygon" or plate.is_empty or not plate.is_valid or plate.area <= 0.0:
        raise ValueError("plate must be a valid positive-area Polygon")
    origin = plate.centroid
    base_nu, base_nv, base_name, base_merge = _grid_for_count(dwelling_count)
    long_angle = axis_angle_deg if axis_angle_deg is not None else _long_axis_angle_degrees(plate)

    def _try(nu: int, nv: int, scheme: str, merge: bool, angle: float) -> EuropeanGridLayout | None:
        plate_for_cutting = plate
        circulation_polygon = None
        circulation_area = 0.0
        wants_circulation = carve_circulation and dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
        if wants_circulation:
            target_area = CIRCULATION_FRACTION_OF_PLATE * plate.area
            circulation_polygon = _centred_circulation_region(plate, axis_angle_deg=angle, origin=origin, area_m2=target_area)
            plate_for_cutting = plate.difference(circulation_polygon)
            circulation_area = float(circulation_polygon.area)
        try:
            cells = _build_grid_cells(plate_for_cutting, nu=nu, nv=nv, axis_angle_deg=angle, origin=origin)
            if merge:
                dwellings = tuple(_merge_grid_cells(cells, nu, nv, dwelling_count))
            else:
                dwellings = tuple(cell for column in cells for cell in column)
        except (ValueError, IndexError):
            return None
        if len(dwellings) != dwelling_count or any(d.is_empty or d.area <= 0.0 for d in dwellings):
            return None
        audit = audit_european_floor_partition(
            plate_for_cutting if wants_circulation else plate,
            dwellings,
            expected_dwelling_count=dwelling_count,
            topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
        )
        facade_lengths = _facade_contact_lengths(plate, dwellings)
        pct = circulation_area / plate.area if plate.area > 0 else 0.0
        outside_band = wants_circulation and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= circulation_area <= CIRCULATION_ABSOLUTE_BAND_M2[1])
        if not audit.passed:
            return EuropeanGridLayout(
                scheme=scheme, grid=scheme, nu=nu, nv=nv, dwelling_polygons=dwellings,
                circulation_polygon=circulation_polygon, circulation_area_m2=circulation_area,
                circulation_pct_of_plate=pct, circulation_outside_ruled_absolute_band=outside_band,
                facade_contact_lengths_m=facade_lengths, habitability_rotation_applied=False,
                habitability_downgrade_applied=False, partition_audit=audit,
                fallback_reason="PARTITION_AUDIT_FAILED", dwelling_layout_emitted=False,
            )
        if any(length < minimum_facade_contact_m for length in facade_lengths):
            return EuropeanGridLayout(
                scheme=scheme, grid=scheme, nu=nu, nv=nv, dwelling_polygons=dwellings,
                circulation_polygon=circulation_polygon, circulation_area_m2=circulation_area,
                circulation_pct_of_plate=pct, circulation_outside_ruled_absolute_band=outside_band,
                facade_contact_lengths_m=facade_lengths, habitability_rotation_applied=False,
                habitability_downgrade_applied=False, partition_audit=audit,
                fallback_reason="INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M", dwelling_layout_emitted=False,
            )
        return EuropeanGridLayout(
            scheme=scheme, grid=scheme, nu=nu, nv=nv, dwelling_polygons=dwellings,
            circulation_polygon=circulation_polygon, circulation_area_m2=circulation_area,
            circulation_pct_of_plate=pct, circulation_outside_ruled_absolute_band=outside_band,
            facade_contact_lengths_m=facade_lengths, habitability_rotation_applied=False,
            habitability_downgrade_applied=False, partition_audit=audit,
            fallback_reason=None, dwelling_layout_emitted=True,
        )

    attempts: list[tuple[int, int, str, bool, float, bool, bool]] = [
        (base_nu, base_nv, base_name, base_merge, long_angle, False, False),
        (base_nu, base_nv, base_name, base_merge, (long_angle + 90.0) % 180.0, True, False),
    ]
    for smaller_nu in range(base_nu - 1, 0, -1):
        if smaller_nu * base_nv < dwelling_count:
            break
        merge_needed = smaller_nu * base_nv != dwelling_count
        attempts.append((smaller_nu, base_nv, base_name, merge_needed, long_angle, False, True))
        attempts.append((smaller_nu, base_nv, base_name, merge_needed, (long_angle + 90.0) % 180.0, True, True))

    last: EuropeanGridLayout | None = None
    for nu, nv, scheme, merge, angle, rotated, downgraded in attempts:
        result = _try(nu, nv, scheme, merge, angle)
        if result is None:
            continue
        last = result
        if result.dwelling_layout_emitted:
            if rotated or downgraded:
                result = EuropeanGridLayout(
                    **{**result.__dict__, "habitability_rotation_applied": rotated, "habitability_downgrade_applied": downgraded}
                )
            return result
    if last is not None:
        return last
    return EuropeanGridLayout(
        scheme=base_name, grid=base_name, nu=base_nu, nv=base_nv, dwelling_polygons=(),
        circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
        circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=(),
        habitability_rotation_applied=False, habitability_downgrade_applied=False,
        partition_audit=None, fallback_reason="PARTITION_AUDIT_FAILED", dwelling_layout_emitted=False,
    )


@dataclass(frozen=True)
class EuropeanMorphologyRoute:
    """T05: the morphological-branching dispatch decision for one plate."""

    route: str
    reason: str
    length_over_width: float
    has_reflex_vertex: bool
    has_courtyard: bool


def _reflex_vertex_count(footprint: BaseGeometry, angle_deg_threshold: float = 185.0) -> int:
    oriented = orient(footprint, sign=1.0)
    coords = list(oriented.exterior.coords)[:-1]
    n = len(coords)
    if n < 4:
        return 0
    count = 0
    for i in range(n):
        a, b, c = coords[i - 1], coords[i], coords[(i + 1) % n]
        dir_in = (b[0] - a[0], b[1] - a[1])
        dir_out = (c[0] - b[0], c[1] - b[1])
        cross = dir_in[0] * dir_out[1] - dir_in[1] * dir_out[0]
        dot = dir_in[0] * dir_out[0] + dir_in[1] * dir_out[1]
        turn = math.degrees(math.atan2(cross, dot))
        interior = 180.0 - turn
        if interior > angle_deg_threshold:
            count += 1
    return count


def classify_building_morphology(footprint: BaseGeometry) -> EuropeanMorphologyRoute:
    """Report Sec 6: choose the partition route from the plate's own morphology.

    Evaluated on the raw (pre-regularization) footprint, before any grid
    partitioning is attempted -- morphology decides the route, regularization
    then cleans up whichever plate (or wing) that route hands the grid.
    """
    if footprint.geom_type != "Polygon" or footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area Polygon")
    rectangle = footprint.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)
    edges = sorted(
        (math.dist(coords[i], coords[i + 1]) for i in range(len(coords) - 1)),
    )
    width, length = edges[0], edges[-1]
    lw_ratio = length / width if width > 0 else float("inf")
    has_courtyard = bool(footprint.interiors)
    # Raw GIS digitization noise (sub-metre jaggies) routinely produces a
    # technically-reflex vertex on an otherwise rectangular plate.  Denoise
    # with the same colinear-vertex tolerance T03 uses before testing for a
    # *real* re-entrant corner, and corroborate with a material convex-hull
    # deficit so noise never routes a clean plate away from the ruled grid.
    denoised = footprint.simplify(0.5, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    hull_deficit_fraction = (denoised.convex_hull.area - denoised.area) / denoised.area if denoised.area > 0 else 0.0
    reflex_count = 0
    if not has_courtyard and hull_deficit_fraction > 0.03:
        reflex_count = _reflex_vertex_count(denoised)

    if has_courtyard:
        return EuropeanMorphologyRoute(
            route="courtyard_secondary", reason="INTERIOR_RING_COURTYARD_UNFOLD",
            length_over_width=lw_ratio, has_reflex_vertex=False, has_courtyard=True,
        )
    if reflex_count > 0:
        return EuropeanMorphologyRoute(
            route="l_shape_decomposition", reason="REFLEX_VERTEX_DETECTED",
            length_over_width=lw_ratio, has_reflex_vertex=True, has_courtyard=False,
        )
    if lw_ratio >= LINEAR_GALLERY_ASPECT_THRESHOLD:
        return EuropeanMorphologyRoute(
            route="i_shape_linear_gallery", reason="LENGTH_OVER_WIDTH_GE_2",
            length_over_width=lw_ratio, has_reflex_vertex=False, has_courtyard=False,
        )
    return EuropeanMorphologyRoute(
        route="point_block_grid", reason="LENGTH_OVER_WIDTH_LT_2_CONVEX",
        length_over_width=lw_ratio, has_reflex_vertex=False, has_courtyard=False,
    )


def _reflex_vertices(footprint: BaseGeometry, *, tolerance_m: float = 0.15) -> list[tuple[float, float]]:
    """Every reflex (re-entrant) vertex of the (denoised) footprint, in
    perimeter traversal order -- one candidate split point per corner, not
    just the first one encountered."""
    denoised = footprint.simplify(tolerance_m, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    oriented = orient(denoised, sign=1.0)
    coords = list(oriented.exterior.coords)[:-1]
    n = len(coords)
    points: list[tuple[float, float]] = []
    for i in range(n):
        a, b, c = coords[i - 1], coords[i], coords[(i + 1) % n]
        dir_in = (b[0] - a[0], b[1] - a[1])
        dir_out = (c[0] - b[0], c[1] - b[1])
        cross = dir_in[0] * dir_out[1] - dir_in[1] * dir_out[0]
        dot = dir_in[0] * dir_out[0] + dir_in[1] * dir_out[1]
        turn = math.degrees(math.atan2(cross, dot))
        if 180.0 - turn > 185.0:
            points.append(b)
    return points


def _split_at_reflex_vertex(
    footprint: BaseGeometry, *, tolerance_m: float = 0.15, reflex_vertex_index: int = 0
) -> tuple[BaseGeometry, BaseGeometry]:
    """Report Sec 6.2: split a non-convex plate along a reflex orthogonal axis.

    T05: every reflex vertex is a candidate split point, not just the first
    one found -- ``reflex_vertex_index`` selects which one (in perimeter
    order) this call splits at, so a caller can try each in turn on a plate
    with more than one re-entrant corner (U, T, cross). For the chosen
    vertex, tries both axis-aligned lines through it and keeps whichever
    produces exactly two polygon wings with the better combined
    rectangularity (``piece.area / piece.minimum_rotated_rectangle.area``),
    which is what "convex lobes" means in practice for an orthogonal plate.
    Pre-simplifies at ``tolerance_m`` (the pipeline's own regularization
    tolerance, not the coarser 0.5 m ``classify_building_morphology`` uses
    for its routing decision) so the cut line matches what regularization
    elsewhere would keep, and slivers/near-collinear GIS noise below that
    tolerance never register as a spurious second reflex vertex here.
    """
    reflex_points = _reflex_vertices(footprint, tolerance_m=tolerance_m)
    if not reflex_points or reflex_vertex_index >= len(reflex_points):
        raise ValueError("footprint has no reflex vertex to split at")
    reflex_point = reflex_points[reflex_vertex_index]
    min_x, min_y, max_x, max_y = footprint.bounds
    span = max(max_x - min_x, max_y - min_y) * 2.0 + 1.0
    candidates = [
        LineString([(reflex_point[0], min_y - span), (reflex_point[0], max_y + span)]),
        LineString([(min_x - span, reflex_point[1]), (max_x + span, reflex_point[1])]),
    ]
    best: tuple[BaseGeometry, BaseGeometry] | None = None
    best_score = -1.0
    for line in candidates:
        result = split(footprint, line)
        pieces = [g for g in result.geoms if g.geom_type == "Polygon" and g.area > footprint.area * 0.02]
        if len(pieces) != 2:
            continue
        score = sum(p.area / p.minimum_rotated_rectangle.area for p in pieces)
        if score > best_score:
            best_score = score
            pieces.sort(key=lambda p: p.area, reverse=True)
            best = (pieces[0], pieces[1])
    if best is None:
        raise ValueError("reflex-vertex split did not yield two wings")
    return best


def _split_wing_best_of_all_reflex_vertices(
    wing: BaseGeometry, *, tolerance_m: float
) -> tuple[BaseGeometry, BaseGeometry] | None:
    """T05: try every reflex vertex on ``wing`` (not only the first), keep
    the split with the best combined rectangularity across all of them.

    A U/T/cross plate carries more than one re-entrant corner; splitting at
    whichever one happens to be first in perimeter order is not always the
    cut that leaves the cleanest two lobes to recurse on.
    """
    reflex_points = _reflex_vertices(wing, tolerance_m=tolerance_m)
    best: tuple[BaseGeometry, BaseGeometry] | None = None
    best_score = -1.0
    for index in range(len(reflex_points)):
        try:
            larger, smaller = _split_at_reflex_vertex(wing, tolerance_m=tolerance_m, reflex_vertex_index=index)
        except ValueError:
            continue
        score = (larger.area / larger.minimum_rotated_rectangle.area) + (
            smaller.area / smaller.minimum_rotated_rectangle.area
        )
        if score > best_score:
            best_score = score
            best = (larger, smaller)
    return best


def _l_shape_wings(
    footprint: BaseGeometry, *, tolerance_m: float = 0.15, max_wings: int = 6
) -> list[BaseGeometry]:
    """T03/T05: recurse the best available reflex-vertex split on whichever
    wing still carries one.

    A single clean L-shape (one real reflex vertex at ``tolerance_m``) still
    returns the plain two-wing split. A U-shape (two re-entrant corners)
    keeps splitting -- each split is chosen from *every* reflex vertex still
    present on that wing (``_split_wing_best_of_all_reflex_vertices``), not
    only the first one found, so a T or cross plate (three or four
    re-entrant corners) converges to more wings than a single-vertex search
    would reach -- until no wing has a reflex vertex left or ``max_wings`` is
    reached (raised from 4 to 6 for T05 to make room for a cross plate's
    five lobes).
    """
    wings = [footprint]
    while len(wings) < max_wings:
        split_index = None
        split_result: tuple[BaseGeometry, BaseGeometry] | None = None
        for index, wing in enumerate(wings):
            denoised = wing.simplify(tolerance_m, preserve_topology=True)
            if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
                denoised = wing
            if _reflex_vertex_count(denoised) > 0:
                candidate = _split_wing_best_of_all_reflex_vertices(wing, tolerance_m=tolerance_m)
                if candidate is not None:
                    split_index = index
                    split_result = candidate
                    break
        if split_index is None or split_result is None:
            break
        larger, smaller = split_result
        wings = wings[:split_index] + [larger, smaller] + wings[split_index + 1:]
    return wings


def _allocate_wing_dwelling_counts(wing_areas: list[float], dwelling_count: int) -> list[int]:
    """Area-fraction dwelling counts across N wings, conserving the exact total.

    Every wing gets at least one dwelling; any rounding remainder is settled
    by giving/taking one dwelling at a time, largest wing first, never
    reducing the requested ``dwelling_count``.
    """
    total_area = sum(wing_areas)
    if total_area <= 0.0 or dwelling_count < len(wing_areas):
        raise ValueError("wings cannot host dwelling_count without a per-wing count of zero")
    counts = [max(1, round(dwelling_count * area / total_area)) for area in wing_areas]
    diff = dwelling_count - sum(counts)
    order = sorted(range(len(wing_areas)), key=lambda i: -wing_areas[i])
    guard = 0
    while diff != 0 and guard < 10000:
        i = order[guard % len(order)]
        if diff > 0:
            counts[i] += 1
            diff -= 1
        elif counts[i] > 1:
            counts[i] -= 1
            diff += 1
        guard += 1
    if diff != 0 or any(count <= 0 for count in counts):
        raise ValueError("wing area fractions could not conserve dwelling_count")
    return counts


def _wing_count_candidates(
    wing_areas: list[float],
    dwelling_count: int,
    max_per_wing: int,
    *,
    max_candidates: int = 16,
    max_transfer_depth: int = 3,
) -> list[tuple[int, ...]]:
    """T05/T06: an ordered, bounded search of per-wing count vectors.

    Starts at the area-proportional baseline (``_allocate_wing_dwelling_counts``)
    and explores single-dwelling transfers between wings (donor keeps >= 1,
    receiver stays <= ``max_per_wing``) up to ``max_transfer_depth`` hops,
    breadth-first so nearer-to-baseline vectors are tried first. Never
    changes ``dwelling_count`` -- every candidate sums to it exactly.
    """
    baseline = tuple(_allocate_wing_dwelling_counts(wing_areas, dwelling_count))
    seen = {baseline}
    candidates = [baseline]
    frontier = [baseline]
    n = len(wing_areas)
    depth = 0
    while frontier and len(candidates) < max_candidates and depth < max_transfer_depth:
        next_frontier: list[tuple[int, ...]] = []
        for counts in frontier:
            for i in range(n):
                if counts[i] <= 1:
                    continue
                for j in range(n):
                    if i == j or counts[j] >= max_per_wing:
                        continue
                    new_counts = list(counts)
                    new_counts[i] -= 1
                    new_counts[j] += 1
                    key = tuple(new_counts)
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(key)
                    next_frontier.append(key)
                    if len(candidates) >= max_candidates:
                        break
                if len(candidates) >= max_candidates:
                    break
            if len(candidates) >= max_candidates:
                break
        frontier = next_frontier
        depth += 1
    return candidates


def _combine_wing_results(
    footprint: BaseGeometry,
    wing_results: list[EuropeanGridLayout],
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float,
    scheme: str,
    extra_circulation: list[BaseGeometry] | None = None,
    keep_circulation_polygon: bool = True,
) -> EuropeanGridLayout | None:
    """Combine independently-partitioned wings into one storey layout.

    Shared by the L-shape (T05/T03) and courtyard (T02) routes. Returns
    ``None`` (never an approximated layout) whenever the combined audit or
    habitability gate fails, so the caller can fall back to the secondary
    route exactly as before.
    """
    if not all(result.dwelling_layout_emitted for result in wing_results):
        return None
    combined_dwellings = tuple(
        polygon for result in wing_results for polygon in result.dwelling_polygons
    )
    wing_circulations = [
        result.circulation_polygon for result in wing_results if result.circulation_polygon is not None
    ]
    all_circulation = list(wing_circulations) + list(extra_circulation or [])
    audit_plate = footprint.difference(unary_union(all_circulation)) if all_circulation else footprint
    combined_audit = audit_european_floor_partition(
        audit_plate, combined_dwellings, expected_dwelling_count=dwelling_count,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    combined_facade = _facade_contact_lengths(footprint, combined_dwellings)
    if not combined_audit.passed or any(length < minimum_facade_contact_m for length in combined_facade):
        return None
    circulation_area_total = sum(float(polygon.area) for polygon in all_circulation)
    pct = circulation_area_total / footprint.area if footprint.area > 0 else 0.0
    outside_band = any(result.circulation_outside_ruled_absolute_band for result in wing_results)
    return EuropeanGridLayout(
        scheme=scheme, grid="+".join(result.grid for result in wing_results),
        nu=dwelling_count, nv=1, dwelling_polygons=combined_dwellings,
        circulation_polygon=(unary_union(all_circulation) if all_circulation else None) if keep_circulation_polygon else None,
        circulation_area_m2=circulation_area_total, circulation_pct_of_plate=pct,
        circulation_outside_ruled_absolute_band=outside_band,
        facade_contact_lengths_m=combined_facade,
        habitability_rotation_applied=any(result.habitability_rotation_applied for result in wing_results),
        habitability_downgrade_applied=any(result.habitability_downgrade_applied for result in wing_results),
        partition_audit=combined_audit, fallback_reason=None, dwelling_layout_emitted=True,
    )


def _courtyard_void_polygon(footprint: BaseGeometry) -> BaseGeometry:
    """The courtyard void: the interior ring if the footprint carries one,
    otherwise the concave notch bounded by the plate's own convex hull (an
    open U/C-shape courtyard, never digitized with a true hole)."""
    if footprint.interiors:
        interior_polygons = [Polygon(ring) for ring in footprint.interiors]
        return max(interior_polygons, key=lambda polygon: polygon.area)
    denoised = footprint.simplify(0.5, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    hull = denoised.convex_hull
    void = hull.difference(denoised)
    if void.is_empty:
        raise ValueError("footprint has no courtyard void to unfold")
    if void.geom_type == "MultiPolygon":
        void = max(void.geoms, key=lambda geom: geom.area)
    if void.geom_type != "Polygon" or void.area <= 0.0:
        raise ValueError("footprint courtyard void is degenerate")
    return void


def _courtyard_wings_and_nodes(
    footprint: BaseGeometry, *, circulation_area_total_m2: float
) -> tuple[list[BaseGeometry], list[BaseGeometry]]:
    """Report Sec 6.4: subtract the void, unfold the C-band into orthogonal
    wings, and place one circulation node at each of the void's *inner*
    corners (a void corner that does not sit on the plate's own bounding
    envelope) -- two inner corners for an open U/C-shape, four for a fully
    enclosed ring. Wings and nodes are returned in world coordinates.
    """
    angle = _long_axis_angle_degrees(footprint)
    origin = footprint.centroid
    void = _courtyard_void_polygon(footprint)
    aligned_footprint = affinity.rotate(footprint, -angle, origin=origin)
    aligned_void = affinity.rotate(void, -angle, origin=origin)
    fx0, fy0, fx1, fy1 = aligned_footprint.bounds
    vx0, vy0, vx1, vy1 = aligned_void.bounds
    span = max(fx1 - fx0, fy1 - fy0, 1.0)
    pad = span * 2.0
    eps = span * 1e-6

    inner_corners = [
        (cx, cy)
        for cx, cy in ((vx0, vy0), (vx1, vy0), (vx1, vy1), (vx0, vy1))
        if abs(cx - fx0) > eps and abs(cx - fx1) > eps and abs(cy - fy0) > eps and abs(cy - fy1) > eps
    ]
    circulation_area_each = circulation_area_total_m2 / len(inner_corners) if inner_corners else 0.0
    node_side = math.sqrt(circulation_area_each) if circulation_area_each > 0.0 else 0.0
    # T06: a node box centred exactly on the void's own inner corner has half
    # its area sitting inside the void -- never real footprint area, so
    # summing the *raw* box areas as "circulation" overstates it (discovered
    # while proving T06's own conservation identity, "gross - void =
    # conditioned + circulation"). Clipping each node to the aligned
    # footprint before it is returned changes nothing about the wings
    # (subtracting a void-extending box or its footprint-clipped remainder
    # from a piece that is already confined to the footprint is identical --
    # the void-only sliver was never part of any wing to begin with) but
    # makes the reported circulation area the area actually carved.
    nodes_aligned: list[BaseGeometry] = []
    for cx, cy in inner_corners:
        raw_node = box(cx - node_side / 2.0, cy - node_side / 2.0, cx + node_side / 2.0, cy + node_side / 2.0)
        clipped = raw_node.intersection(aligned_footprint)
        if clipped.geom_type == "MultiPolygon":
            clipped = max(clipped.geoms, key=lambda geom: geom.area)
        if clipped.is_empty or clipped.geom_type != "Polygon" or clipped.area <= 0.0:
            clipped = raw_node
        nodes_aligned.append(clipped)

    wing_boxes = [
        box(fx0 - pad, vy0, vx0, vy1),
        box(vx1, vy0, fx1 + pad, vy1),
        box(fx0 - pad, fy0 - pad, fx1 + pad, vy0),
        box(fx0 - pad, vy1, fx1 + pad, fy1 + pad),
    ]
    wings_aligned: list[BaseGeometry] = []
    for candidate in wing_boxes:
        piece = aligned_footprint.intersection(candidate)
        for node in nodes_aligned:
            piece = piece.difference(node)
        if piece.is_empty or piece.area <= aligned_footprint.area * 1e-6:
            continue
        if piece.geom_type == "MultiPolygon":
            piece = max(piece.geoms, key=lambda geom: geom.area)
        if piece.geom_type != "Polygon" or piece.area <= 0.0:
            continue
        wings_aligned.append(piece)

    if len(wings_aligned) < 3:
        raise ValueError("courtyard footprint did not unfold into at least three wings")

    wings = [affinity.rotate(piece, angle, origin=origin) for piece in wings_aligned]
    nodes = [affinity.rotate(node, angle, origin=origin) for node in nodes_aligned]
    return wings, nodes


def generate_european_courtyard_layout(
    footprint: BaseGeometry,
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
    regularization_tolerance_m: float = 0.15,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """Report Sec 6.4: courtyard / U-shape unfolding, the ``courtyard_secondary``
    route's actual implementation (T02/T06). Subtracts the courtyard void
    (kept as a hole in the plate, never counted as dwelling area -- the wing
    boxes only ever intersect the real footprint, so the void is excluded
    structurally whether it is a true interior ring or an open U/C notch),
    places a circulation node at each inner corner, then partitions each
    remaining wing by its own area fraction of ``dwelling_count`` --
    recursing through ``generate_european_ruled_storey_layout`` exactly as
    the L-shape route's wings already do. T06: reuses T05's bounded
    ``_wing_count_candidates`` rebalance search instead of only the single
    area-proportional baseline split, so a wing that cannot host its
    proportional share (corner wings stay >= 1 dwelling throughout) no
    longer fails the whole courtyard on that split alone. Never
    approximates: any wing, audit or habitability failure across every
    candidate raises so the caller falls back to the secondary route.
    """
    wants_circulation = carve_circulation and dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
    target_circulation_area = CIRCULATION_FRACTION_OF_PLATE * footprint.area if wants_circulation else 0.0
    wings, nodes = _courtyard_wings_and_nodes(footprint, circulation_area_total_m2=target_circulation_area)
    wing_areas = [wing.area for wing in wings]
    extra_circulation = nodes if wants_circulation else None
    for counts in _wing_count_candidates(wing_areas, dwelling_count, RULED_GRID_MAX_DWELLINGS_PER_FLOOR):
        try:
            wing_results = [
                generate_european_ruled_storey_layout(
                    wing, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                    regularization_tolerance_m=regularization_tolerance_m, carve_circulation=carve_circulation,
                )
                for wing, count in zip(wings, counts)
            ]
        except (ValueError, IndexError):
            continue
        combined = _combine_wing_results(
            footprint, wing_results, dwelling_count=dwelling_count,
            minimum_facade_contact_m=minimum_facade_contact_m, scheme="courtyard_wing_unfold",
            extra_circulation=extra_circulation, keep_circulation_polygon=True,
        )
        if combined is None:
            continue
        outside_band = combined.circulation_outside_ruled_absolute_band or (
            wants_circulation
            and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= combined.circulation_area_m2 <= CIRCULATION_ABSOLUTE_BAND_M2[1])
        )
        if outside_band != combined.circulation_outside_ruled_absolute_band:
            combined = EuropeanGridLayout(**{**combined.__dict__, "circulation_outside_ruled_absolute_band": outside_band})
        return combined
    raise ValueError("courtyard wing partition failed audit or habitability")


def generate_european_linear_gallery_layout(
    plate: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """Report Sec 6.3: I-shape linear gallery, double-loaded corridor spine.

    A 1.80 m corridor band along the long axis splits the plate into two
    lateral bands; each band is then sliced into equal-area longitudinal
    bays by the same bisection primitive used for the point-block grid, and
    the total bay count across both bands sums to ``dwelling_count`` exactly
    (never a count reduction).
    """
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")
    origin = plate.centroid
    angle = _long_axis_angle_degrees(plate)
    grid_name = _grid_for_count(dwelling_count)[2]
    wants_circulation = carve_circulation and dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION

    aligned = affinity.rotate(plate, -angle, origin=origin)
    min_x, min_y, max_x, max_y = aligned.bounds
    corridor_aligned = box(min_x, (min_y + max_y) / 2.0 - CORRIDOR_SPINE_WIDTH_M / 2.0, max_x, (min_y + max_y) / 2.0 + CORRIDOR_SPINE_WIDTH_M / 2.0)
    corridor = affinity.rotate(corridor_aligned, angle, origin=origin)
    if not wants_circulation:
        corridor = None
        remainder = plate
        circulation_area = 0.0
    else:
        remainder = plate.difference(corridor)
        circulation_area = float(corridor.area)

    north = math.ceil(dwelling_count / 2)
    south = dwelling_count - north
    # A full-width corridor spine disconnects ``remainder`` into two convex
    # lobes: split on which side of the spine's midline each part's centroid
    # falls, rather than re-clipping with boxes (which can slice through the
    # corridor boundary itself and yield a mixed-type GeometryCollection).
    aligned_remainder = affinity.rotate(remainder, -angle, origin=origin)
    mid_y = (min_y + max_y) / 2.0
    if aligned_remainder.geom_type == "Polygon":
        remainder_parts = [aligned_remainder]
    elif aligned_remainder.geom_type == "MultiPolygon":
        remainder_parts = [g for g in aligned_remainder.geoms if g.area > 1e-6]
    else:
        remainder_parts = [g for g in aligned_remainder.geoms if g.geom_type == "Polygon" and g.area > 1e-6]
    north_parts = [p for p in remainder_parts if p.centroid.y >= mid_y]
    south_parts = [p for p in remainder_parts if p.centroid.y < mid_y]
    north_band = affinity.rotate(unary_union(north_parts), angle, origin=origin) if north_parts else None
    south_band = affinity.rotate(unary_union(south_parts), angle, origin=origin) if south_parts else None

    dwellings: list[BaseGeometry] = []
    for band, count in ((north_band, north), (south_band, south)):
        if count <= 0 or band is None:
            continue
        bays = _equal_area_axis_cuts(band, axis_angle_deg=angle, n_parts=count, origin=origin)
        dwellings.extend(bays)

    if len(dwellings) != dwelling_count or any(d.is_empty or d.area <= 0.0 for d in dwellings):
        return EuropeanGridLayout(
            scheme="i_shape_linear_gallery", grid=grid_name, nu=dwelling_count, nv=1, dwelling_polygons=(),
            circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
            circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=(),
            habitability_rotation_applied=False, habitability_downgrade_applied=False,
            partition_audit=None, fallback_reason="PARTITION_AUDIT_FAILED", dwelling_layout_emitted=False,
        )
    dwellings_t = tuple(dwellings)
    audit_plate = remainder if wants_circulation else plate
    audit = audit_european_floor_partition(
        audit_plate, dwellings_t, expected_dwelling_count=dwelling_count,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    facade_lengths = _facade_contact_lengths(plate, dwellings_t)
    pct = circulation_area / plate.area if plate.area > 0 else 0.0
    outside_band = wants_circulation and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= circulation_area <= CIRCULATION_ABSOLUTE_BAND_M2[1])
    if not audit.passed:
        reason = "PARTITION_AUDIT_FAILED"
    elif any(length < minimum_facade_contact_m for length in facade_lengths):
        reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
    else:
        reason = None
    return EuropeanGridLayout(
        scheme="i_shape_linear_gallery", grid=grid_name, nu=dwelling_count, nv=1, dwelling_polygons=dwellings_t,
        circulation_polygon=corridor, circulation_area_m2=circulation_area, circulation_pct_of_plate=pct,
        circulation_outside_ruled_absolute_band=outside_band, facade_contact_lengths_m=facade_lengths,
        habitability_rotation_applied=False, habitability_downgrade_applied=False, partition_audit=audit,
        fallback_reason=reason, dwelling_layout_emitted=reason is None,
    )


NARROW_PLATE_SCHEME = "narrow_plate_corridor_free"


def generate_european_narrow_plate_layout(
    plate: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """T07: a plate whose minimum rotated width is below
    ``NARROW_FOOTPRINT_THRESHOLD_M`` cannot host MVP Sec 4.3's 1.80 m
    ``CORRIDOR_SPINE_WIDTH_M`` double-loaded corridor (fact 12's conflict in
    its sharpest form). Rather than inventing a resolution, this scheme
    partitions the plate dual-aspect across its own long axis with **no**
    corridor spine -- disclosed by its own ``scheme`` name
    (``narrow_plate_corridor_free``, reported at Stop-and-report 3 as
    ``CIRCULATION_SPINE_OMITTED_NARROW_PLATE``), never a silently-relabelled
    gallery layout. A centroidal stair core is still carved at
    ``CIRCULATION_FRACTION_OF_PLATE`` for >= 2 dwellings/storey -- that
    sizing rule is width-independent (MVP Sec 4.3's 2-4-dwelling band), only
    the >= 5-dwelling spine is what a < 8 m plate cannot host. If the core
    alone leaves no habitable remainder on both sides of it, the storey
    refuses with ``NARROW_PLATE_CORE_EXCEEDS_HABITABLE_SHARE`` rather than
    approximating the dwelling count down.
    """
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")
    if plate.geom_type != "Polygon" or plate.is_empty or not plate.is_valid or plate.area <= 0.0:
        raise ValueError("plate must be a valid positive-area Polygon")
    angle = _long_axis_angle_degrees(plate)
    origin = plate.centroid
    wants_circulation = carve_circulation and dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION

    def _refused(reason: str) -> EuropeanGridLayout:
        return EuropeanGridLayout(
            scheme=NARROW_PLATE_SCHEME, grid=NARROW_PLATE_SCHEME, nu=dwelling_count, nv=1, dwelling_polygons=(),
            circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
            circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=(),
            habitability_rotation_applied=False, habitability_downgrade_applied=False,
            partition_audit=None, fallback_reason=reason, dwelling_layout_emitted=False,
        )

    core: BaseGeometry | None = None
    circulation_area = 0.0
    remainder: BaseGeometry = plate
    if wants_circulation:
        # A centroidal stair core the same size CIRCULATION_MIN_DWELLINGS_
        # FOR_CIRCULATION already carves for a 2-4-dwelling storey (fact 12)
        # is compact along the plate's own short axis, so it never spans the
        # full width -- unlike the gallery's corridor, it does not disconnect
        # the plate into two lobes. It is cut as a hole and the *whole*
        # remainder is then sliced dual-aspect along the long axis in one
        # pass (``_equal_area_axis_cuts`` already conserves area around a
        # hole/notch), rather than pre-splitting into west/east bands that a
        # non-disconnecting core would leave empty on one side.
        target_area = CIRCULATION_FRACTION_OF_PLATE * plate.area
        core = _centred_circulation_region(plate, axis_angle_deg=angle, origin=origin, area_m2=target_area)
        remainder = plate.difference(core)
        if remainder.is_empty or remainder.area <= plate.area * 1e-6:
            return _refused("NARROW_PLATE_CORE_EXCEEDS_HABITABLE_SHARE")
        circulation_area = float(core.area)

    dwellings: list[BaseGeometry] = []
    try:
        dwellings.extend(_equal_area_axis_cuts(remainder, axis_angle_deg=angle, n_parts=dwelling_count, origin=origin))
    except (ValueError, IndexError):
        return _refused("NARROW_PLATE_CORE_EXCEEDS_HABITABLE_SHARE" if wants_circulation else "PARTITION_AUDIT_FAILED")

    if len(dwellings) != dwelling_count or any(d.is_empty or d.area <= 0.0 for d in dwellings):
        return _refused("PARTITION_AUDIT_FAILED")
    dwellings_t = tuple(dwellings)
    audit_plate = plate.difference(core) if core is not None else plate
    audit = audit_european_floor_partition(
        audit_plate, dwellings_t, expected_dwelling_count=dwelling_count,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    facade_lengths = _facade_contact_lengths(plate, dwellings_t)
    pct = circulation_area / plate.area if plate.area > 0 else 0.0
    outside_band = wants_circulation and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= circulation_area <= CIRCULATION_ABSOLUTE_BAND_M2[1])
    if not audit.passed:
        reason = "PARTITION_AUDIT_FAILED"
    elif any(length < minimum_facade_contact_m for length in facade_lengths):
        reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
    else:
        reason = None
    return EuropeanGridLayout(
        scheme=NARROW_PLATE_SCHEME, grid=NARROW_PLATE_SCHEME, nu=dwelling_count, nv=1, dwelling_polygons=dwellings_t,
        circulation_polygon=core, circulation_area_m2=circulation_area, circulation_pct_of_plate=pct,
        circulation_outside_ruled_absolute_band=outside_band, facade_contact_lengths_m=facade_lengths,
        habitability_rotation_applied=False, habitability_downgrade_applied=False, partition_audit=audit,
        fallback_reason=reason, dwelling_layout_emitted=reason is None,
    )


def generate_european_ruled_storey_layout(
    footprint: BaseGeometry,
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
    regularization_tolerance_m: float = 0.15,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """T04/T05/T07/T08 entry point: regularize, classify morphology, then partition.

    Falls back to the existing ``equal_strip_multi_angle_sweep`` secondary
    route (unchanged) whenever the ruled route cannot serve this storey --
    regularization area delta beyond the 2% gate, or a habitability/audit
    failure every wing-decomposition candidate this task tries could not
    resolve. ``carve_circulation`` (T08/D-EU-49) is threaded to every leaf
    route and to every recursive wing call so a single-storey building's
    caller can suppress circulation uniformly, regardless of which route the
    storey took -- never as a special case inside one route.
    """
    if dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"caller must apply the >{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} per-floor refusal before calling the ruled partitioner")

    if dwelling_count == 1:
        # A single dwelling always takes the whole plate exactly -- no
        # morphology routing, regularization, or narrow-plate gate can ever
        # apply, because there is nothing to partition.
        facade_lengths = _facade_contact_lengths(footprint, (footprint,))
        audit = audit_european_floor_partition(
            footprint, (footprint,), expected_dwelling_count=1,
            topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
        )
        return EuropeanGridLayout(
            scheme="ruled_grid_1x1", grid="ruled_grid_1x1", nu=1, nv=1, dwelling_polygons=(footprint,),
            circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
            circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=facade_lengths,
            habitability_rotation_applied=False, habitability_downgrade_applied=False, partition_audit=audit,
            fallback_reason=None, dwelling_layout_emitted=True,
        )

    def _secondary(reason_hint: str | None) -> EuropeanGridLayout:
        # D-EU-39 §2 / EU-15 T04: the strip cutter is retired as a success
        # path.  A storey the ruled route cannot express is refused, not
        # relabelled -- this always returns dwelling_layout_emitted=False,
        # whatever the legacy equal-width/equal-area sweep itself achieved,
        # so the caller (generate_european_building_dwelling_layout) fails
        # the whole building closed to the existing one_zone_per_floor
        # massing-box fallback, exactly as any other unlayoutable building.
        # EU-21 P02-P05: additive group-scheme chain, reachable only here --
        # on a path the existing ruled/L-shape/courtyard routes have already
        # refused. Never replaces a route that already succeeds (fact 2).
        # ``PARTITION_AUDIT_FAILED`` and the (unreachable at this level)
        # density refusal stay pure refusals -- no shape scheme is offered a
        # storey the audit itself already condemned.
        if reason_hint != "PARTITION_AUDIT_FAILED":
            try:
                morphology_here = classify_building_morphology(footprint)
            except (ValueError, IndexError):
                morphology_here = None
            if morphology_here is not None and morphology_here.has_courtyard:
                try:
                    s1 = generate_european_courtyard_perimeter_band_layout(
                        footprint, dwelling_count=dwelling_count,
                        minimum_facade_contact_m=minimum_facade_contact_m, carve_circulation=carve_circulation,
                    )
                except (ValueError, IndexError, AttributeError):
                    # P01c 2026-09-01: a degenerate dwelling polygon can reach
                    # _facade_contact_lengths as None (AttributeError on
                    # .boundary.intersection) -- same isolate-and-fall-through
                    # contract as the ValueError/IndexError cases above, not a
                    # change to any layout this scheme already emits.
                    s1 = None
                if s1 is not None and s1.dwelling_layout_emitted:
                    return s1
            try:
                width_here = _minimum_rotated_width_m(footprint)
            except (ValueError, IndexError):
                width_here = None
            if width_here is not None and width_here < NARROW_FOOTPRINT_THRESHOLD_M:
                try:
                    s2 = generate_european_row_house_depth_bands_layout(
                        footprint, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                    )
                except (ValueError, IndexError, AttributeError):
                    # P01c 2026-09-01: see s1 above -- same isolate-and-fall-through
                    # contract, widened to the same degenerate-polygon symptom.
                    s2 = None
                if s2 is not None and s2.dwelling_layout_emitted:
                    return s2
            if morphology_here is not None and morphology_here.route == "l_shape_decomposition":
                try:
                    s3 = generate_european_wing_spine_decomposition_layout(
                        footprint, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                        regularization_tolerance_m=regularization_tolerance_m, carve_circulation=carve_circulation,
                    )
                except (ValueError, IndexError, AttributeError):
                    # P01c 2026-09-01: see s1 above -- same isolate-and-fall-through
                    # contract, widened to the same degenerate-polygon symptom.
                    s3 = None
                if s3 is not None and s3.dwelling_layout_emitted:
                    return s3
            try:
                s4 = generate_european_regularized_envelope_grid_layout(
                    footprint, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                    carve_circulation=carve_circulation,
                )
            except (ValueError, IndexError, AttributeError):
                # P01c 2026-09-01: see s1 above -- same isolate-and-fall-through
                # contract, widened to the same degenerate-polygon symptom.
                s4 = None
            if s4 is not None and s4.dwelling_layout_emitted:
                return s4

        legacy = generate_european_dwelling_layout(
            footprint, requested_dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
        )
        scheme = "equal_strip_multi_angle_sweep"
        return EuropeanGridLayout(
            scheme=scheme, grid=scheme, nu=dwelling_count, nv=1, dwelling_polygons=legacy.dwelling_polygons,
            circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
            circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=legacy.facade_contact_lengths_m,
            habitability_rotation_applied=False, habitability_downgrade_applied=False,
            partition_audit=legacy.partition_audit,
            fallback_reason=legacy.fallback_reason if legacy.fallback_reason else reason_hint,
            dwelling_layout_emitted=False,
        )

    if dwelling_count == 2:
        # A dual-aspect 2x1 split is a single bisection of the whole plate --
        # no corridor, no wings, so the morphology dispatch (built for the
        # denser routes where circulation/wing topology matters) is skipped
        # entirely, exactly as it is for dwelling_count == 1 above.
        regularization = regularize_footprint_orthogonal(footprint, tolerance_m=regularization_tolerance_m)
        if regularization.exceeds_fallback_band:
            return _secondary("REGULARIZATION_AREA_DELTA_GT_2PCT")
        try:
            result = generate_european_grid_layout(
                regularization.regularized_polygon, dwelling_count=2, minimum_facade_contact_m=minimum_facade_contact_m,
                carve_circulation=carve_circulation,
            )
        except (ValueError, IndexError):
            return _secondary("PARTITION_AUDIT_FAILED")
        if not result.dwelling_layout_emitted:
            return _secondary(result.fallback_reason)
        return result

    morphology = classify_building_morphology(footprint)
    if morphology.route == "courtyard_secondary":
        try:
            return generate_european_courtyard_layout(
                footprint, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                regularization_tolerance_m=regularization_tolerance_m, carve_circulation=carve_circulation,
            )
        except (ValueError, IndexError):
            return _secondary(f"{morphology.reason}_FAILED")

    if morphology.route == "l_shape_decomposition":
        # T05: split at every reflex corner reachable, not one -- expresses
        # L, U, T and cross plates.  Candidates come from both single-cut
        # attempts (kept for the plain-L case, matching pre-T05 behaviour
        # exactly when only one reflex vertex exists) and the recursive
        # multi-wing decomposition, which now tries every reflex vertex on
        # each wing at each step (``_l_shape_wings``), not only the first.
        wing_candidates: list[list[BaseGeometry]] = []
        seen_area_signatures: list[list[float]] = []

        def _add_candidate(wings_to_add: list[BaseGeometry]) -> None:
            signature = [round(w.area, 6) for w in wings_to_add]
            if len(wings_to_add) >= 2 and signature not in seen_area_signatures:
                wing_candidates.append(wings_to_add)
                seen_area_signatures.append(signature)

        try:
            larger, smaller = _split_at_reflex_vertex(footprint, tolerance_m=0.5)
            _add_candidate([larger, smaller])
        except (ValueError, IndexError):
            pass
        try:
            larger, smaller = _split_at_reflex_vertex(footprint, tolerance_m=regularization_tolerance_m)
            _add_candidate([larger, smaller])
        except (ValueError, IndexError):
            pass
        try:
            _add_candidate(_l_shape_wings(footprint, tolerance_m=regularization_tolerance_m))
        except (ValueError, IndexError):
            pass
        try:
            _add_candidate(_l_shape_wings(footprint, tolerance_m=0.5))
        except (ValueError, IndexError):
            pass
        for wings in wing_candidates:
            wing_areas = [wing.area for wing in wings]
            try:
                count_candidates = _wing_count_candidates(wing_areas, dwelling_count, RULED_GRID_MAX_DWELLINGS_PER_FLOOR)
            except ValueError:
                continue
            # T05: when the area-proportional baseline gives a wing more (or
            # fewer) dwellings than it can host, re-allocate across wings
            # (bounded +/-1-at-a-time search) instead of refusing the whole
            # building on the first split tried -- only exhausting every
            # count vector on every wing candidate is a true refusal.
            for counts in count_candidates:
                try:
                    wing_results = [
                        generate_european_ruled_storey_layout(
                            wing, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                            regularization_tolerance_m=regularization_tolerance_m, carve_circulation=carve_circulation,
                        )
                        for wing, count in zip(wings, counts)
                    ]
                    combined = _combine_wing_results(
                        footprint, wing_results, dwelling_count=dwelling_count,
                        minimum_facade_contact_m=minimum_facade_contact_m, scheme="l_shape_decomposition",
                        keep_circulation_polygon=True,
                    )
                except (ValueError, IndexError):
                    combined = None
                if combined is not None:
                    return combined
        return _secondary("L_SHAPE_DECOMPOSITION_FAILED")

    regularization = regularize_footprint_orthogonal(footprint, tolerance_m=regularization_tolerance_m)
    if regularization.exceeds_fallback_band:
        return _secondary("REGULARIZATION_AREA_DELTA_GT_2PCT")
    plate = regularization.regularized_polygon

    try:
        if morphology.route == "i_shape_linear_gallery" and _minimum_rotated_width_m(footprint) < NARROW_FOOTPRINT_THRESHOLD_M:
            # T07: MVP Sec 4.3's 1.80 m corridor spine cannot fit a < 8 m
            # plate (fact 12) -- this is the branch that selects the
            # corridor-free scheme instead, reached here at top level and
            # (per fact 8's shared entry point) also from any wing T05
            # produces that turns out to be a deep, narrow lobe.
            result = generate_european_narrow_plate_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                carve_circulation=carve_circulation,
            )
        elif morphology.route == "i_shape_linear_gallery":
            result = generate_european_linear_gallery_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                carve_circulation=carve_circulation,
            )
        else:
            result = generate_european_grid_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
                carve_circulation=carve_circulation,
            )
    except (ValueError, IndexError):
        return _secondary("PARTITION_AUDIT_FAILED")
    if not result.dwelling_layout_emitted:
        return _secondary(result.fallback_reason)
    return result


def generate_european_nocore_storey_layout(
    footprint: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
) -> EuropeanGridLayout:
    """D-EU-79/D-EU-95: draw one storey with the accepted no-core cutter
    (``openubem.geometry.european_nocore.cut_storey_nocore``), proven at bit
    parity with ``_r5`` over all 2,529 drawn census plates (``CP-1``). Never
    carves circulation -- ``circulation_polygon`` is always ``None``. A
    ``FAIL`` verdict or a cutter exception returns
    ``dwelling_layout_emitted=False``, falling the building back to the
    existing ``one_zone_per_floor`` massing-box route, exactly as any other
    unlayoutable building does today.
    """
    try:
        plate, live, checks, verdict = cut_storey_nocore(footprint, dwelling_count)
    except Exception as exc:
        return EuropeanGridLayout(
            scheme="nocore_equal_area", grid=f"nocore_{dwelling_count}", nu=dwelling_count, nv=1,
            dwelling_polygons=(), circulation_polygon=None, circulation_area_m2=0.0,
            circulation_pct_of_plate=0.0, circulation_outside_ruled_absolute_band=False,
            facade_contact_lengths_m=(), habitability_rotation_applied=False,
            habitability_downgrade_applied=False, partition_audit=None,
            fallback_reason=f"NOCORE_CUTTER_{type(exc).__name__}", dwelling_layout_emitted=False,
        )

    live = tuple(live)
    if verdict == "PASS":
        partition_audit = audit_european_floor_partition(
            plate, live, expected_dwelling_count=dwelling_count,
            topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
        )
        fallback_reason = None
    else:
        partition_audit = None
        failed_ids = [check_id for check_id in ("C1", "C3", "C4", "C5", "C6", "C10", "C11") if not checks[check_id]["pass"]]
        fallback_reason = "NOCORE_CHECK_FAILED_" + "_".join(failed_ids)

    return EuropeanGridLayout(
        scheme="nocore_equal_area", grid=f"nocore_{dwelling_count}", nu=dwelling_count, nv=1,
        dwelling_polygons=live if verdict == "PASS" else (),
        circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
        circulation_outside_ruled_absolute_band=False,
        facade_contact_lengths_m=_facade_contact_lengths(plate, live),
        habitability_rotation_applied=False, habitability_downgrade_applied=False,
        partition_audit=partition_audit,
        fallback_reason=fallback_reason,
        dwelling_layout_emitted=(verdict == "PASS"),
    )


# --- EU-21: additive group schemes (S1-S4), each reachable only on the
# refusal path of ``generate_european_ruled_storey_layout`` (see
# ``_secondary`` above). None of these change any existing route's output.

COURTYARD_PERIMETER_BAND_SCHEME = "courtyard_perimeter_band"
ROW_HOUSE_DEPTH_BANDS_SCHEME = "row_house_depth_bands"
WING_SPINE_DECOMPOSITION_SCHEME = "wing_spine_decomposition"
REGULARIZED_ENVELOPE_GRID_SCHEME = "regularized_envelope_grid"
COURTYARD_BAND_MIN_DEPTH_M = 6.0
ROW_BAND_MIN_LENGTH_M = 4.0
WING_MIN_AREA_SHARE = 0.10
ENVELOPE_RESIDUAL_MAX_FRACTION = 0.35
ENVELOPE_ROTATION_STEP_DEG = 5.0
ENVELOPE_SEARCH_GRID_N = 24


def _refused_group_scheme(scheme: str, dwelling_count: int, reason: str) -> "EuropeanGridLayout":
    return EuropeanGridLayout(
        scheme=scheme, grid=scheme, nu=dwelling_count, nv=1, dwelling_polygons=(),
        circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
        circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=(),
        habitability_rotation_applied=False, habitability_downgrade_applied=False,
        partition_audit=None, fallback_reason=reason, dwelling_layout_emitted=False,
    )


def _wedge_polygon(origin: BaseGeometry, radius: float, angle_from_deg: float, angle_to_deg: float) -> BaseGeometry:
    """A pie-slice polygon from ``origin`` spanning ``angle_from_deg`` to
    ``angle_to_deg`` (may exceed 360) at ``radius``, arc-sampled every ~2
    degrees. Used only to delimit a band by two straight rays -- ``radius``
    is chosen large enough that the sampled arc itself lies outside the
    footprint being cut, so its curvature never matters."""
    span = angle_to_deg - angle_from_deg
    steps = max(2, int(abs(span) / 2.0) + 1)
    points = [(origin.x, origin.y)]
    for i in range(steps + 1):
        angle = math.radians(angle_from_deg + span * i / steps)
        points.append((origin.x + radius * math.cos(angle), origin.y + radius * math.sin(angle)))
    points.append((origin.x, origin.y))
    return Polygon(points)


def _ray_sector_cuts(
    band: BaseGeometry, origin: BaseGeometry, n_parts: int,
    *, tolerance_fraction: float = 0.01, max_iterations: int = 60,
) -> list[BaseGeometry]:
    """Cut ``band`` into ``n_parts`` angular sectors of equal area around
    ``origin`` by advancing each boundary ray's angle (bisection) until the
    swept sector holds ``area/n_parts`` within ``tolerance_fraction``. A pure
    ray cut, never an unfold -- defined for any footprint star-shaped about
    ``origin``, so it cannot fail on a re-entrant outer wall."""
    total_area = band.area
    if total_area <= 0.0 or n_parts <= 0:
        raise ValueError("band must have positive area and n_parts must be positive")
    target = total_area / n_parts
    minx, miny, maxx, maxy = band.bounds
    radius = math.hypot(maxx - minx, maxy - miny) * 2.0 + 1.0
    boundaries = [0.0]
    current = 0.0
    for _ in range(n_parts - 1):
        lo, hi = current, current + 360.0
        mid = hi
        for _ in range(max_iterations):
            mid = (lo + hi) / 2.0
            area = band.intersection(_wedge_polygon(origin, radius, current, mid)).area
            if abs(area - target) <= tolerance_fraction * target:
                break
            if area < target:
                lo = mid
            else:
                hi = mid
        boundaries.append(mid)
        current = mid
    boundaries.append(boundaries[0] + 360.0)
    segments: list[BaseGeometry] = []
    for i in range(n_parts):
        wedge = _wedge_polygon(origin, radius, boundaries[i], boundaries[i + 1])
        if not wedge.is_valid:
            wedge = wedge.buffer(0)
        segment = band.intersection(wedge)
        # Keep the full intersection, even when a sharp outward corner (e.g.
        # a courtyard band) splits one sector's wedge/band intersection into
        # several disconnected pieces -- a dwelling zone may legally be a
        # MultiPolygon the same way ``dwelling_polygons`` already tolerates
        # elsewhere in this module (EU-21 P08 Fix A). Dropping the smaller
        # pieces here used to leave real footprint area unclaimed by any
        # dwelling or circulation zone.
        if segment.is_empty or segment.geom_type not in ("Polygon", "MultiPolygon") or segment.area <= 0.0:
            raise ValueError("ray sector cut produced a degenerate segment")
        segments.append(segment)
    total_segment_area = sum(s.area for s in segments)
    if abs(total_segment_area - band.area) > 1e-6 * band.area:
        raise ValueError("ray sector cut lost or gained area relative to band")
    return segments


def _outer_ring_sharp_corners(footprint: BaseGeometry, angle_deg_threshold: float = 135.0) -> list[tuple[float, float]]:
    """Vertices of ``footprint``'s outer ring with interior angle below
    ``angle_deg_threshold`` -- the corners of a perimeter block, where the
    band is deepest and a stair core belongs."""
    oriented = orient(Polygon(footprint.exterior), sign=1.0)
    coords = list(oriented.exterior.coords)[:-1]
    n = len(coords)
    if n < 3:
        return []
    corners = []
    for i in range(n):
        a, b, c = coords[i - 1], coords[i], coords[(i + 1) % n]
        dir_in = (b[0] - a[0], b[1] - a[1])
        dir_out = (c[0] - b[0], c[1] - b[1])
        cross = dir_in[0] * dir_out[1] - dir_in[1] * dir_out[0]
        dot = dir_in[0] * dir_out[0] + dir_in[1] * dir_out[1]
        turn = math.degrees(math.atan2(cross, dot))
        interior = 180.0 - turn
        if interior < angle_deg_threshold:
            corners.append(b)
    return corners


def _corner_core_boxes(
    footprint: BaseGeometry, corners: list[tuple[float, float]], void: BaseGeometry, k: int, total_core_area_m2: float,
) -> list[BaseGeometry]:
    """``k`` square cores, one centred at each of the corners deepest (most
    distant) from the courtyard void, each clipped to ``footprint``."""
    if not corners or k <= 0 or total_core_area_m2 <= 0.0:
        return []
    ranked = sorted(corners, key=lambda pt: -void.distance(Point(pt)))
    chosen = ranked[:k]
    area_each = total_core_area_m2 / len(chosen)
    side = math.sqrt(area_each) if area_each > 0.0 else 0.0
    boxes: list[BaseGeometry] = []
    for cx, cy in chosen:
        raw = box(cx - side / 2.0, cy - side / 2.0, cx + side / 2.0, cy + side / 2.0)
        clipped = raw.intersection(footprint)
        if clipped.geom_type == "MultiPolygon":
            clipped = max(clipped.geoms, key=lambda g: g.area)
        if clipped.is_empty or clipped.geom_type != "Polygon" or clipped.area <= 0.0:
            continue
        boxes.append(clipped)
    return boxes


def generate_european_courtyard_perimeter_band_layout(
    footprint: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """S1 (EU-21 P02): the closed perimeter block -- the plate is kept *with*
    its hole, so no unfolding is ever attempted. Dwellings are equal-area
    angular bands cut by rays from the void's own representative point;
    circulation sits at the band's deepest corners. Reachable only where the
    existing ``courtyard_secondary`` unfold has already refused."""
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")
    if not footprint.interiors:
        raise ValueError("courtyard_perimeter_band requires a footprint with a real interior ring")

    void = max((Polygon(ring) for ring in footprint.interiors), key=lambda polygon: polygon.area)
    outer_perimeter = footprint.exterior.length
    inner_perimeter = void.exterior.length
    denom = outer_perimeter + inner_perimeter
    depth_m = 2.0 * footprint.area / denom if denom > 0.0 else 0.0
    if depth_m < COURTYARD_BAND_MIN_DEPTH_M:
        return _refused_group_scheme(COURTYARD_PERIMETER_BAND_SCHEME, dwelling_count, "COURTYARD_BAND_TOO_SHALLOW")

    wants_circulation = carve_circulation and dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
    band = footprint
    circulation_polygon: BaseGeometry | None = None
    circulation_area = 0.0
    if wants_circulation:
        corners = _outer_ring_sharp_corners(footprint)
        target_core_area = CORE_FRACTION_OF_PLATE * footprint.area
        k = max(1, math.ceil(dwelling_count / 3.0)) if corners else 0
        cores = _corner_core_boxes(footprint, corners, void, k, target_core_area) if k else []
        if cores:
            core_union = unary_union(cores)
            band = footprint.difference(core_union)
            circulation_polygon = core_union
            circulation_area = float(core_union.area)
        else:
            angle = _long_axis_angle_degrees(footprint)
            circulation_polygon = _centred_circulation_region(
                footprint, axis_angle_deg=angle, origin=footprint.centroid, area_m2=target_core_area,
            )
            band = footprint.difference(circulation_polygon)
            circulation_area = float(circulation_polygon.area)
        if band.is_empty or band.area <= footprint.area * 1e-6:
            return _refused_group_scheme(COURTYARD_PERIMETER_BAND_SCHEME, dwelling_count, "COURTYARD_BAND_TOO_SHALLOW")

    origin_pt = void.representative_point()
    try:
        segments = _ray_sector_cuts(band, origin_pt, dwelling_count)
    except (ValueError, IndexError):
        return _refused_group_scheme(COURTYARD_PERIMETER_BAND_SCHEME, dwelling_count, "PARTITION_AUDIT_FAILED")
    if len(segments) != dwelling_count or any(s.is_empty or s.area <= 0.0 for s in segments):
        return _refused_group_scheme(COURTYARD_PERIMETER_BAND_SCHEME, dwelling_count, "PARTITION_AUDIT_FAILED")

    dwellings_t = tuple(segments)
    audit = audit_european_floor_partition(
        band, dwellings_t, expected_dwelling_count=dwelling_count,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    facade_lengths = _facade_contact_lengths(footprint, dwellings_t)
    pct = circulation_area / footprint.area if footprint.area > 0 else 0.0
    outside_band = wants_circulation and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= circulation_area <= CIRCULATION_ABSOLUTE_BAND_M2[1])
    if not audit.passed:
        reason = "PARTITION_AUDIT_FAILED"
    elif any(length < minimum_facade_contact_m for length in facade_lengths):
        reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
    else:
        reason = None
    return EuropeanGridLayout(
        scheme=COURTYARD_PERIMETER_BAND_SCHEME, grid=COURTYARD_PERIMETER_BAND_SCHEME,
        nu=dwelling_count, nv=1, dwelling_polygons=dwellings_t,
        circulation_polygon=circulation_polygon, circulation_area_m2=circulation_area,
        circulation_pct_of_plate=pct, circulation_outside_ruled_absolute_band=outside_band,
        facade_contact_lengths_m=facade_lengths, habitability_rotation_applied=False,
        habitability_downgrade_applied=False, partition_audit=audit,
        fallback_reason=reason, dwelling_layout_emitted=reason is None,
    )


def generate_european_row_house_depth_bands_layout(
    footprint: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
) -> EuropeanGridLayout:
    """S2 (EU-21 P03): a party-wall row house / narrow burgage plot under
    ``NARROW_FOOTPRINT_THRESHOLD_M`` of width -- full-width bands front to
    back, no corridor. Reachable only where the existing route has already
    refused a footprint this narrow."""
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")
    if _minimum_rotated_width_m(footprint) >= NARROW_FOOTPRINT_THRESHOLD_M:
        raise ValueError("row_house_depth_bands only applies below the narrow-footprint threshold")

    angle = _long_axis_angle_degrees(footprint)
    origin = footprint.centroid
    try:
        bands = _equal_area_axis_cuts(footprint, axis_angle_deg=angle, n_parts=dwelling_count, origin=origin)
    except (ValueError, IndexError):
        return _refused_group_scheme(ROW_HOUSE_DEPTH_BANDS_SCHEME, dwelling_count, "PARTITION_AUDIT_FAILED")
    if len(bands) != dwelling_count or any(b.is_empty or b.area <= 0.0 for b in bands):
        return _refused_group_scheme(ROW_HOUSE_DEPTH_BANDS_SCHEME, dwelling_count, "PARTITION_AUDIT_FAILED")

    def _along_axis_length(band: BaseGeometry) -> float:
        aligned = affinity.rotate(band, -angle, origin=origin)
        minx, _miny, maxx, _maxy = aligned.bounds
        return maxx - minx

    if min(_along_axis_length(b) for b in bands) < ROW_BAND_MIN_LENGTH_M:
        return _refused_group_scheme(ROW_HOUSE_DEPTH_BANDS_SCHEME, dwelling_count, "ROW_BAND_TOO_SHORT")

    dwellings_t = tuple(bands)
    audit = audit_european_floor_partition(
        footprint, dwellings_t, expected_dwelling_count=dwelling_count,
        topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    )
    facade_lengths = _facade_contact_lengths(footprint, dwellings_t)
    if not audit.passed:
        reason = "PARTITION_AUDIT_FAILED"
    elif any(length < minimum_facade_contact_m for length in facade_lengths):
        reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
    else:
        reason = None
    return EuropeanGridLayout(
        scheme=ROW_HOUSE_DEPTH_BANDS_SCHEME, grid=ROW_HOUSE_DEPTH_BANDS_SCHEME,
        nu=dwelling_count, nv=1, dwelling_polygons=dwellings_t,
        circulation_polygon=None, circulation_area_m2=0.0, circulation_pct_of_plate=0.0,
        circulation_outside_ruled_absolute_band=False, facade_contact_lengths_m=facade_lengths,
        habitability_rotation_applied=False, habitability_downgrade_applied=False, partition_audit=audit,
        fallback_reason=reason, dwelling_layout_emitted=reason is None,
    )


def generate_european_wing_spine_decomposition_layout(
    footprint: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    regularization_tolerance_m: float = 0.15, carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """S3 (EU-21 P04): decompose a multi-wing plate by morphological opening
    (``buffer(-d/4).buffer(+d/4)``) instead of a reflex-vertex cut, so it
    needs no real corner -- reaches chamfered elbows, 3+-wing junctions and
    non-orthogonal returns the existing reflex-vertex route cannot. The
    junction (``footprint - wings``) becomes the circulation core. Reachable
    only where the existing route has already refused."""
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")

    perimeter = footprint.exterior.length
    depth_m = 2.0 * footprint.area / perimeter if perimeter > 0.0 else 0.0
    if depth_m <= 0.0:
        return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")

    opened = footprint.buffer(-depth_m / 4.0).buffer(depth_m / 4.0)
    if opened.is_empty:
        return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")
    raw_components = list(opened.geoms) if opened.geom_type == "MultiPolygon" else [opened]
    raw_wings: list[BaseGeometry] = []
    for component in raw_components:
        clipped = component.intersection(footprint)
        if clipped.geom_type == "MultiPolygon":
            clipped = max(clipped.geoms, key=lambda g: g.area)
        if clipped.is_empty or clipped.geom_type != "Polygon" or clipped.area <= 0.0:
            continue
        raw_wings.append(clipped)
    if not raw_wings:
        return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")

    threshold = WING_MIN_AREA_SHARE * footprint.area
    wings = [w for w in raw_wings if w.area >= threshold]
    small = [w for w in raw_wings if w.area < threshold]
    for s in small:
        if not wings:
            continue
        nearest_index = min(range(len(wings)), key=lambda i: wings[i].distance(s))
        merged = unary_union([wings[nearest_index], s])
        # A small component need not touch its nearest surviving wing (the
        # opening can leave a real gap), so the union can come back as a
        # MultiPolygon -- keep only the larger piece rather than pass a
        # non-Polygon geometry further down; the untouched sliver simply
        # stays out of every wing and is folded into the junction below.
        if merged.geom_type == "MultiPolygon":
            merged = max(merged.geoms, key=lambda g: g.area)
        wings[nearest_index] = merged

    # Exactly one surviving wing means the opening found the plate
    # effectively convex; per plan this hands off to the plain grid route
    # rather than a wing decomposition. Folded here into the same refusal as
    # zero wings (a genuine single-wing case is rare on a plate whose
    # morphology already tripped the reflex-vertex route) so the very next
    # step of the same fallback chain, S4's regularized envelope, covers it.
    if len(wings) < 2:
        return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")

    wing_areas = [w.area for w in wings]
    try:
        count_candidates = _wing_count_candidates(wing_areas, dwelling_count, RULED_GRID_MAX_DWELLINGS_PER_FLOOR)
    except ValueError:
        return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")

    junction = footprint.difference(unary_union(wings))
    extra_circulation = [junction] if carve_circulation and not junction.is_empty and junction.area > 0.0 else None

    for counts in count_candidates:
        try:
            wing_results = [
                generate_european_ruled_storey_layout(
                    wing, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                    regularization_tolerance_m=regularization_tolerance_m, carve_circulation=carve_circulation,
                )
                for wing, count in zip(wings, counts)
            ]
        except (ValueError, IndexError):
            continue
        combined = _combine_wing_results(
            footprint, wing_results, dwelling_count=dwelling_count,
            minimum_facade_contact_m=minimum_facade_contact_m, scheme=WING_SPINE_DECOMPOSITION_SCHEME,
            extra_circulation=extra_circulation, keep_circulation_polygon=True,
        )
        if combined is not None:
            return combined
    return _refused_group_scheme(WING_SPINE_DECOMPOSITION_SCHEME, dwelling_count, "WING_OPENING_YIELDED_NO_PLATE")


def _largest_axis_aligned_inscribed_rectangle(polygon: BaseGeometry, *, grid_n: int = ENVELOPE_SEARCH_GRID_N) -> BaseGeometry:
    """The largest axis-aligned rectangle inscribed in ``polygon`` (which is
    assumed already rotated to the candidate frame), found by a coarse
    occupancy grid plus the classic maximal-rectangle-in-a-binary-matrix scan
    (histogram method). A numerical-method resolution, not an architectural
    threshold -- ``grid_n`` is fixed and district-independent."""
    minx, miny, maxx, maxy = polygon.bounds
    width, height = maxx - minx, maxy - miny
    if width <= 0.0 or height <= 0.0:
        raise ValueError("polygon has degenerate bounds")
    cell_w, cell_h = width / grid_n, height / grid_n
    occupied = [
        [polygon.contains(Point(minx + (col + 0.5) * cell_w, miny + (row + 0.5) * cell_h)) for col in range(grid_n)]
        for row in range(grid_n)
    ]
    best_area = 0
    best_rect: tuple[int, int, int, int] | None = None
    heights = [0] * grid_n
    for row in range(grid_n):
        for col in range(grid_n):
            heights[col] = heights[col] + 1 if occupied[row][col] else 0
        stack: list[tuple[int, int]] = []
        for col in range(grid_n + 1):
            h = heights[col] if col < grid_n else 0
            start = col
            while stack and stack[-1][1] > h:
                idx, sh = stack.pop()
                area = sh * (col - idx)
                if area > best_area:
                    best_area = area
                    best_rect = (row - sh + 1, idx, row, col - 1)
                start = idx
            stack.append((start, h))
    if best_rect is None or best_area <= 0:
        raise ValueError("no inscribed rectangle found")
    row0, col0, row1, col1 = best_rect
    return box(minx + col0 * cell_w, miny + row0 * cell_h, minx + (col1 + 1) * cell_w, miny + (row1 + 1) * cell_h)


def generate_european_regularized_envelope_grid_layout(
    footprint: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
    carve_circulation: bool = True,
) -> EuropeanGridLayout:
    """S4 (EU-21 P05): the terminal scheme for a plate too irregular to
    decompose -- dwellings occupy the largest inscribed axis-aligned
    rectangle (rotation searched in 5-degree steps over 0-90), the irregular
    residue becomes circulation/stair/light-well/service, added to any
    circulation the grid route already carves. Reachable only where S1-S3
    have already refused for a shape reason."""
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError(f"dwelling_count must be within the ruled grid's 1..{RULED_GRID_MAX_DWELLINGS_PER_FLOOR} range")

    origin = footprint.centroid
    best_rect_world: BaseGeometry | None = None
    best_area = 0.0
    steps = int(round(90.0 / ENVELOPE_ROTATION_STEP_DEG))
    for i in range(steps + 1):
        theta = i * ENVELOPE_ROTATION_STEP_DEG
        aligned = affinity.rotate(footprint, -theta, origin=origin)
        try:
            rect_aligned = _largest_axis_aligned_inscribed_rectangle(aligned)
        except (ValueError, IndexError):
            continue
        if rect_aligned.area > best_area:
            best_area = rect_aligned.area
            best_rect_world = affinity.rotate(rect_aligned, theta, origin=origin)

    if best_rect_world is None or best_area <= 0.0:
        return _refused_group_scheme(REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, "ENVELOPE_RESIDUAL_GT_35PCT")

    envelope = best_rect_world.intersection(footprint)
    if envelope.geom_type == "MultiPolygon":
        envelope = max(envelope.geoms, key=lambda g: g.area)
    if envelope.is_empty or envelope.geom_type != "Polygon" or envelope.area <= 0.0:
        return _refused_group_scheme(REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, "ENVELOPE_RESIDUAL_GT_35PCT")

    residual_fraction = (footprint.area - envelope.area) / footprint.area if footprint.area > 0 else 1.0
    if residual_fraction > ENVELOPE_RESIDUAL_MAX_FRACTION:
        return _refused_group_scheme(REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, "ENVELOPE_RESIDUAL_GT_35PCT")

    try:
        result = generate_european_grid_layout(
            envelope, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
            carve_circulation=carve_circulation,
        )
    except (ValueError, IndexError):
        return _refused_group_scheme(REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, "PARTITION_AUDIT_FAILED")
    if not result.dwelling_layout_emitted:
        return _refused_group_scheme(
            REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, result.fallback_reason or "PARTITION_AUDIT_FAILED",
        )

    residue = footprint.difference(envelope)
    # EU-21 P08 Fix B: an irregular plate's residue is itself several
    # disconnected slivers (one per wing tip / corner). Only the piece that
    # touches the grid's own internal stair/elevator core is real
    # circulation; every other piece belongs to whichever dwelling it
    # adjoins, exactly as the owner described for groups 08-10.
    residue_components: list[BaseGeometry] = []
    if not residue.is_empty and residue.area > 0.0:
        if residue.geom_type == "MultiPolygon":
            residue_components = [g for g in residue.geoms if not g.is_empty and g.area > 0.0]
        elif residue.geom_type == "Polygon":
            residue_components = [residue]
        elif residue.geom_type == "GeometryCollection":
            residue_components = [
                g for g in residue.geoms
                if g.geom_type in ("Polygon", "MultiPolygon") and not g.is_empty and g.area > 0.0
            ]

    grid_core = result.circulation_polygon
    dwelling_polygons = list(result.dwelling_polygons)
    true_core_pieces: list[BaseGeometry] = []
    other_components: list[BaseGeometry] = []
    if residue_components:
        touching_idx = (
            [i for i, comp in enumerate(residue_components) if comp.intersects(grid_core)]
            if grid_core is not None
            else []
        )
        if touching_idx:
            true_core_pieces = [residue_components[i] for i in touching_idx]
            other_components = [comp for i, comp in enumerate(residue_components) if i not in touching_idx]
        else:
            largest_idx = max(range(len(residue_components)), key=lambda i: residue_components[i].area)
            true_core_pieces = [residue_components[largest_idx]]
            other_components = [comp for i, comp in enumerate(residue_components) if i != largest_idx]

    for component in other_components:
        touch_idx = next(
            (i for i, dwelling in enumerate(dwelling_polygons) if component.intersects(dwelling)),
            None,
        )
        if touch_idx is None:
            touch_idx = min(range(len(dwelling_polygons)), key=lambda i: component.distance(dwelling_polygons[i]))
        dwelling_polygons[touch_idx] = unary_union([dwelling_polygons[touch_idx], component])

    all_circulation = list([grid_core] if grid_core is not None else []) + true_core_pieces
    circulation_polygon = unary_union(all_circulation) if all_circulation else None
    circulation_area = float(circulation_polygon.area) if circulation_polygon is not None else 0.0
    pct = circulation_area / footprint.area if footprint.area > 0 else 0.0
    dwelling_polygons_t = tuple(dwelling_polygons)
    facade_lengths = _facade_contact_lengths(footprint, dwelling_polygons_t)
    if any(length < minimum_facade_contact_m for length in facade_lengths):
        return _refused_group_scheme(REGULARIZED_ENVELOPE_GRID_SCHEME, dwelling_count, "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M")
    return EuropeanGridLayout(
        scheme=REGULARIZED_ENVELOPE_GRID_SCHEME, grid=result.grid, nu=result.nu, nv=result.nv,
        dwelling_polygons=dwelling_polygons_t, circulation_polygon=circulation_polygon,
        circulation_area_m2=circulation_area, circulation_pct_of_plate=pct,
        circulation_outside_ruled_absolute_band=result.circulation_outside_ruled_absolute_band,
        facade_contact_lengths_m=facade_lengths, habitability_rotation_applied=result.habitability_rotation_applied,
        habitability_downgrade_applied=result.habitability_downgrade_applied, partition_audit=result.partition_audit,
        fallback_reason=None, dwelling_layout_emitted=True, residual_fraction=residual_fraction,
    )


RESIDENTIAL_TYPES = frozenset({"SFH", "TH", "MFH", "AB"})
CORE_FRACTION_OF_PLATE = 0.06
NARROW_FOOTPRINT_THRESHOLD_M = 8.0
# Relative area used to absorb floating-point topology noise after affine
# operations.  Unlike the former fixed m² tolerance, this scales with the
# footprint and is invariant under CRS translation.
EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION = 1e-9


REAL_FOOTPRINT_REQUIRED_COLUMNS = frozenset({"osm_id", "geometry"})


@dataclass(frozen=True)
class EuropeanFloorAllocation:
    """One storey's declared dwelling count and conditioned/core areas."""

    storey_index: int
    dwelling_count: int
    conditioned_area_m2: float
    unconditioned_core_area_m2: float


@dataclass(frozen=True)
class EuropeanDwellingAllocation:
    """D-EU-01 deterministic allocation independent of footprint geometry."""

    archetype_id: str
    building_type: str
    declared_apartments: float
    dwelling_count: int
    storey_count: int
    units_per_floor: int
    has_unconditioned_core: bool
    floor_allocations: tuple[EuropeanFloorAllocation, ...]


@dataclass(frozen=True)
class EuropeanFloorPartitionAudit:
    """Independent GEO-01/GEO-09 audit of one supplied dwelling-floor layout.

    This is an auditor, not a layout generator.  It deliberately does not
    import the existing DOE commercial layout-module dimensions for TABULA
    dwellings.  A later European footprint adapter supplies the polygons; this
    contract proves that its output neither changes the conditioned plate nor
    hides missing or overlapping dwelling areas.
    """

    expected_dwelling_count: int
    observed_dwelling_count: int
    footprint_area_m2: float
    union_area_m2: float
    gap_area_m2: float
    overlap_area_m2: float
    outside_area_m2: float
    area_error_fraction: float
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class EuropeanFloorLayoutFeasibility:
    """Fail-closed GEO-04 decision before a dwelling generator emits polygons.

    This is deliberately a feasibility gate, rather than an adapter around the
    repository's generic DOE room-layout generator.  That generator does not
    yet establish one-zone-per-European-dwelling semantics.  A narrow plate is
    therefore recorded as an explicit single-zone-per-floor fallback and may
    never be counted as successful dwelling-level geometry.
    """

    minimum_width_m: float
    requested_dwelling_count: int
    fallback_required: bool
    fallback_reason: str | None
    dwelling_layout_emitted: bool

    @property
    def status(self) -> str:
        return (
            "FALLBACK_ONE_ZONE_PER_FLOOR"
            if self.fallback_required
            else "DWELLING_LAYOUT_REQUIRED"
        )


@dataclass(frozen=True)
class EuropeanRealFootprintAudit:
    """A fail-closed geometry census over one acquired residential manifest.

    This records what the real source geometry can support before a European
    dwelling-layout generator exists.  In particular, it does *not* infer a
    typology, dwelling count, core, or emitted thermal zone from a footprint.
    Those inputs are not available in the frozen acquisition schema.
    """

    neighbourhood_id: str
    source_manifest: str
    source_sha256: str
    projected_crs: str
    footprint_count: int
    narrow_fallback_count: int
    courtyard_count: int
    non_convex_count: int
    dwelling_layout_emitted_count: int


@dataclass(frozen=True)
class EuropeanGeneratedFloorLayout:
    """A deterministic dwelling-only layout generated from one real footprint.

    The requested dwelling count is an explicit caller input.  Acquisition
    manifests do not identify per-building apartments, so this adapter must
    never derive it from a source tag, area, or geometry heuristic.  Core
    geometry is deliberately not emitted: fitting an unconditioned core inside
    an observed shell would silently change the conditioned-area contract.
    """

    requested_dwelling_count: int
    dwelling_polygons: tuple[BaseGeometry, ...]
    partition_audit: EuropeanFloorPartitionAudit | None
    facade_contact_lengths_m: tuple[float, ...]
    fallback_reason: str | None
    dwelling_layout_emitted: bool
    unconditioned_core_emitted: bool = False

    @property
    def status(self) -> str:
        return "DWELLING_LAYOUT_EMITTED" if self.dwelling_layout_emitted else "FALLBACK_PENDING_LAYOUT"


@dataclass(frozen=True)
class EuropeanUnconditionedCore:
    """An explicit unconditioned core attached outside a rectangular plate."""

    core_polygon: BaseGeometry | None
    requested_area_m2: float
    emitted_area_m2: float
    shared_boundary_length_m: float
    overlap_area_m2: float
    fallback_reason: str | None

    @property
    def emitted(self) -> bool:
        return self.core_polygon is not None and self.fallback_reason is None


def _minimum_rotated_width_m(footprint: BaseGeometry) -> float:
    """Return a polygon's short rotated-rectangle dimension in projected metres."""
    rectangle = footprint.minimum_rotated_rectangle
    coordinates = tuple(rectangle.exterior.coords)
    edge_lengths = tuple(
        math.dist(coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    if not edge_lengths or not all(math.isfinite(length) and length > 0.0 for length in edge_lengths):
        raise ValueError("footprint has no finite positive minimum-rectangle width")
    return min(edge_lengths)


def audit_real_footprint_manifest(
    manifest_path: Path | str,
    *,
    neighbourhood_id: str | None = None,
) -> tuple[pd.DataFrame, EuropeanRealFootprintAudit]:
    """Census real residential footprints without claiming generated layouts.

    The manifest must be projected because both width and area are physically
    interpreted.  Every returned row has ``dwelling_layout_emitted=False``;
    broad footprints are merely candidates for a future deterministic adapter,
    while narrow ones are explicitly recorded as the GEO-04 fallback.
    """
    path = Path(manifest_path)
    if not path.is_file():
        raise ValueError(f"Residential manifest does not exist: {path}")
    gdf = gpd.read_file(path)
    missing = REAL_FOOTPRINT_REQUIRED_COLUMNS - set(gdf.columns)
    if missing:
        raise ValueError(f"Residential manifest is missing required columns: {sorted(missing)}")
    if gdf.empty:
        raise ValueError("Residential manifest must contain at least one footprint")
    if gdf.crs is None or not gdf.crs.is_projected:
        raise ValueError("Residential manifest must use a projected CRS")
    if not gdf["osm_id"].is_unique:
        raise ValueError("Residential manifest osm_id values must be unique")

    site_id = neighbourhood_id or path.parent.name
    if not site_id:
        raise ValueError("neighbourhood_id is required")
    records: list[dict[str, object]] = []
    for row in gdf.sort_values("osm_id", kind="stable").itertuples(index=False):
        footprint = row.geometry
        if (
            footprint is None
            or footprint.is_empty
            or not footprint.is_valid
            or footprint.geom_type != "Polygon"
            or footprint.area <= 0.0
            or not all(math.isfinite(value) for value in footprint.bounds)
        ):
            raise ValueError(f"Invalid polygon geometry for building {row.osm_id!r}")
        minimum_width = _minimum_rotated_width_m(footprint)
        fallback_required = minimum_width < NARROW_FOOTPRINT_THRESHOLD_M
        records.append(
            {
                "neighbourhood_id": site_id,
                "building_id": str(row.osm_id),
                "footprint_area_m2": float(footprint.area),
                "minimum_width_m": minimum_width,
                "has_courtyard": bool(footprint.interiors),
                "is_non_convex": not footprint.equals(footprint.convex_hull),
                "fallback_required": fallback_required,
                "fallback_reason": "NARROW_FOOTPRINT_LT_8M" if fallback_required else "",
                "layout_status": (
                    "FALLBACK_ONE_ZONE_PER_FLOOR"
                    if fallback_required
                    else "DWELLING_LAYOUT_PENDING"
                ),
                "dwelling_layout_emitted": False,
            }
        )

    frame = pd.DataFrame.from_records(records)
    audit = EuropeanRealFootprintAudit(
        neighbourhood_id=site_id,
        source_manifest=path.as_posix(),
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        projected_crs=gdf.crs.to_string(),
        footprint_count=len(frame),
        narrow_fallback_count=int(frame["fallback_required"].sum()),
        courtyard_count=int(frame["has_courtyard"].sum()),
        non_convex_count=int(frame["is_non_convex"].sum()),
        dwelling_layout_emitted_count=0,
    )
    return frame, audit


def write_real_footprint_feasibility_census(
    manifests_root: Path | str,
    output_dir: Path | str,
) -> tuple[pd.DataFrame, list[EuropeanRealFootprintAudit]]:
    """Write reproducible GEO-04 real-footprint feasibility evidence.

    Only the audited ``02_residential_manifest.gpkg`` inputs are read.  The
    output remains a pre-layout census and cannot be treated as GEO-08 parity,
    GEO-10 sample-group completion, or emitted dwelling geometry.
    """
    root = Path(manifests_root)
    manifests = sorted(root.glob("*/02_residential_manifest.gpkg"))
    if not manifests:
        raise ValueError(f"No residential manifests found below {root}")
    frames: list[pd.DataFrame] = []
    audits: list[EuropeanRealFootprintAudit] = []
    for manifest in manifests:
        frame, audit = audit_real_footprint_manifest(manifest)
        frames.append(frame)
        audits.append(audit)
    all_rows = pd.concat(frames, ignore_index=True)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    all_rows.to_csv(destination / "real_footprint_feasibility.csv", index=False)
    summary = {
        "evidence_scope": "pre_layout_real_footprint_feasibility_only",
        "dwelling_layout_emitted": False,
        "site_audits": [audit.__dict__ for audit in audits],
        "total_footprints": int(len(all_rows)),
        "total_narrow_fallbacks": int(all_rows["fallback_required"].sum()),
        "total_courtyards": int(all_rows["has_courtyard"].sum()),
        "total_non_convex": int(all_rows["is_non_convex"].sum()),
    }
    (destination / "real_footprint_feasibility_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return all_rows, audits


def _rounded_count(value: float, name: str) -> int:
    """Apply D-EU-04's explicit half-up integer convention.

    Python's built-in ``round`` is bankers rounding; the ruled values are
    physical dwelling/storey counts, so this explicit convention remains stable at a
    half value and is recorded in the allocation metadata.
    """
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return int(math.floor(numeric + 0.5))


def derive_european_plate_area(
    *, conditioned_reference_area_m2: float, n_storey: float
) -> float:
    """Derive the D-EU-01 conditioned plate from the ruled storey count.

    The source float is preserved by the registry; the physical model must use
    the approved half-up integer count for both its storey stack and plate.
    This keeps the sum of conditioned floor areas exactly equal to ``A_C_Ref``
    for synthetic-average rows as well as for integral source rows.
    """
    reference_area = float(conditioned_reference_area_m2)
    if not math.isfinite(reference_area) or reference_area <= 0:
        raise ValueError("conditioned_reference_area_m2 must be finite and positive")
    return reference_area / _rounded_count(n_storey, "n_storey")


def assess_european_floor_layout_feasibility(
    footprint: BaseGeometry,
    *,
    requested_dwelling_count: int,
) -> EuropeanFloorLayoutFeasibility:
    """Apply GEO-04's registered narrow-plate fallback deterministically.

    Width is the short side of the minimum rotated rectangle, so the result is
    independent of orientation.  The operative rule is strictly ``< 8 m``:
    an exactly 8 m plate does not trigger this particular fallback.  Passing
    the gate does *not* claim a dwelling layout was generated; that remains
    impossible until the European footprint adapter supplies and audits its
    actual polygons.
    """
    requested_numeric = float(requested_dwelling_count)
    if (
        not math.isfinite(requested_numeric)
        or requested_numeric <= 0.0
        or not requested_numeric.is_integer()
    ):
        raise ValueError("requested_dwelling_count must be positive")
    requested = int(requested_numeric)
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")

    rectangle = footprint.minimum_rotated_rectangle
    coordinates = tuple(rectangle.exterior.coords)
    edge_lengths = tuple(
        math.dist(coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    minimum_width = min(edge_lengths)
    narrow = minimum_width < NARROW_FOOTPRINT_THRESHOLD_M
    return EuropeanFloorLayoutFeasibility(
        minimum_width_m=minimum_width,
        requested_dwelling_count=requested,
        fallback_required=narrow,
        fallback_reason="NARROW_FOOTPRINT_LT_8M" if narrow else None,
        dwelling_layout_emitted=False,
    )


def _is_convex_polygon(footprint: BaseGeometry, tolerance_m2: float = 1e-8) -> bool:
    return abs(float(footprint.convex_hull.area) - float(footprint.area)) <= tolerance_m2


def generate_external_unconditioned_core(
    conditioned_plate: BaseGeometry,
    *,
    requested_area_m2: float,
    tolerance_m2: float = 1e-8,
) -> EuropeanUnconditionedCore:
    """Attach the D-EU-01 core outside an explicit rectangular conditioned plate.

    This supports the ruled TABULA plate semantics: the core is additional
    unconditioned area, never carved from ``A_C_Ref``.  An observed irregular
    source shell lacks a declared gross-to-conditioned relationship, so it is
    intentionally outside this function's contract and receives no core.
    """
    area = float(requested_area_m2)
    if not math.isfinite(area) or area <= 0.0:
        raise ValueError("requested_area_m2 must be finite and positive")
    if conditioned_plate.geom_type != "Polygon" or conditioned_plate.is_empty or not conditioned_plate.is_valid:
        raise ValueError("conditioned_plate must be a valid Polygon")
    rectangle = conditioned_plate.minimum_rotated_rectangle
    if abs(float(rectangle.area) - float(conditioned_plate.area)) > tolerance_m2:
        return EuropeanUnconditionedCore(
            core_polygon=None,
            requested_area_m2=area,
            emitted_area_m2=0.0,
            shared_boundary_length_m=0.0,
            overlap_area_m2=0.0,
            fallback_reason="NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED",
        )
    angle = _long_axis_angle_degrees(conditioned_plate)
    aligned = affinity.rotate(conditioned_plate, -angle, origin=(0.0, 0.0))
    min_x, min_y, max_x, max_y = aligned.bounds
    long_length = max_x - min_x
    if long_length <= 0.0:
        raise ValueError("conditioned_plate must have positive long-axis length")
    # The full long side is shared, so the core stays a simple rectangular zone
    # and its exact area is controlled only by the outward thickness.
    core_aligned = box(min_x, max_y, max_x, max_y + area / long_length)
    core = affinity.rotate(core_aligned, angle, origin=(0.0, 0.0))
    shared_boundary = float(core.boundary.intersection(conditioned_plate.boundary.buffer(1e-7)).length)
    overlap = float(core.intersection(conditioned_plate).area)
    emitted_area = float(core.area)
    if abs(emitted_area - area) > tolerance_m2:
        reason = "CORE_AREA_CONSERVATION_FAILED"
    elif overlap > tolerance_m2:
        reason = "CORE_OVERLAPS_CONDITIONED_PLATE"
    elif shared_boundary <= tolerance_m2:
        reason = "CORE_NOT_ADJACENT_TO_CONDITIONED_PLATE"
    else:
        reason = None
    return EuropeanUnconditionedCore(
        core_polygon=core if reason is None else None,
        requested_area_m2=area,
        emitted_area_m2=emitted_area if reason is None else 0.0,
        shared_boundary_length_m=shared_boundary if reason is None else 0.0,
        overlap_area_m2=overlap,
        fallback_reason=reason,
    )


def _long_axis_angle_degrees(footprint: BaseGeometry) -> float:
    coordinates = tuple(footprint.minimum_rotated_rectangle.exterior.coords)
    edges = tuple(
        (coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )
    start, end = max(edges, key=lambda edge: math.dist(*edge))
    return math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))


def _facade_contact_lengths(footprint: BaseGeometry, dwellings: Iterable[BaseGeometry]) -> tuple[float, ...]:
    """Measure exterior contact after geometric transforms with a 0.1 µm tolerance."""
    facade_band = footprint.boundary.buffer(1e-7)
    return tuple(float(dwelling.boundary.intersection(facade_band).length) for dwelling in dwellings)


def generate_european_dwelling_layout(
    footprint: BaseGeometry,
    *,
    requested_dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
) -> EuropeanGeneratedFloorLayout:
    """Generate a deterministic partition for real European footprints.

    Supports convex, non-convex, and courtyard polygons via multi-angle sweep
    and radial sector partitioning.  The resulting candidates must pass the
    independent area/topology audit and every dwelling must have the declared
    exterior-facade contact.
    """
    requested_numeric = float(requested_dwelling_count)
    if (
        not math.isfinite(requested_numeric)
        or requested_numeric <= 0.0
        or not requested_numeric.is_integer()
    ):
        raise ValueError("requested_dwelling_count must be positive")
    if not math.isfinite(minimum_facade_contact_m) or minimum_facade_contact_m <= 0.0:
        raise ValueError("minimum_facade_contact_m must be finite and positive")
    if footprint.geom_type != "Polygon":
        raise ValueError("footprint must be a Polygon for dwelling layout generation")
    requested = int(requested_numeric)
    feasibility = assess_european_floor_layout_feasibility(
        footprint,
        requested_dwelling_count=requested,
    )
    if feasibility.fallback_required:
        return EuropeanGeneratedFloorLayout(
            requested_dwelling_count=requested,
            dwelling_polygons=(),
            partition_audit=None,
            facade_contact_lengths_m=(),
            fallback_reason=feasibility.fallback_reason,
            dwelling_layout_emitted=False,
        )

    if requested == 1:
        partition_audit = audit_european_floor_partition(
            footprint,
            (footprint,),
            expected_dwelling_count=1,
            topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
        )
        facade_lengths = _facade_contact_lengths(footprint, (footprint,))
        if not partition_audit.passed:
            reason = "PARTITION_AUDIT_FAILED"
        elif any(length < minimum_facade_contact_m for length in facade_lengths):
            reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
        else:
            reason = None
        return EuropeanGeneratedFloorLayout(
            requested_dwelling_count=1,
            dwelling_polygons=(footprint,) if reason is None else (),
            partition_audit=partition_audit,
            facade_contact_lengths_m=facade_lengths,
            fallback_reason=reason,
            dwelling_layout_emitted=reason is None,
        )

    # Strategy 1: Multi-Angle Sweep (Equal-Width and Equal-Area)
    target_area = footprint.area / requested
    rot_origin = footprint.centroid
    long_angle = _long_axis_angle_degrees(footprint)

    # Priority angles: long axis, orthogonal, and 2-degree increments across 180°
    angles_to_try = [long_angle, (long_angle + 90.0) % 180.0]
    for a in range(0, 180, 2):
        fa = float(a)
        if fa not in angles_to_try:
            angles_to_try.append(fa)

    last_fallback_reason = "PARTITION_AUDIT_FAILED"

    for angle in angles_to_try:
        aligned = affinity.rotate(footprint, -angle, origin=rot_origin)
        min_x, min_y, max_x, max_y = aligned.bounds
        if max_x - min_x < 1e-4:
            continue

        for mode in ("equal_width", "equal_area"):
            if mode == "equal_width":
                strip_width = (max_x - min_x) / requested
                cuts = [min_x + index * strip_width for index in range(requested + 1)]
            else:
                cuts = [min_x]
                for k in range(1, requested):
                    desired = k * target_area
                    lo, hi = min_x, max_x
                    for _ in range(25):
                        mid = (lo + hi) / 2.0
                        cbox = box(min_x, min_y - 1.0, mid, max_y + 1.0)
                        if aligned.intersection(cbox).area < desired:
                            lo = mid
                        else:
                            hi = mid
                    cuts.append((lo + hi) / 2.0)
                cuts.append(max_x)

            candidates = []
            possible = True
            for i in range(requested):
                clip_box = box(cuts[i], min_y - 1.0, cuts[i + 1], max_y + 1.0)
                inter = aligned.intersection(clip_box)
                if inter.is_empty:
                    possible = False
                    break
                cand = affinity.rotate(inter, angle, origin=rot_origin)
                if cand.geom_type == "Polygon":
                    candidates.append(cand)
                elif cand.geom_type == "MultiPolygon":
                    parts = [p for p in cand.geoms if p.area > 1e-4]
                    if len(parts) == 1:
                        candidates.append(parts[0])
                    else:
                        possible = False
                        break
                else:
                    possible = False
                    break

            if possible and len(candidates) == requested:
                cand_tuple = tuple(candidates)
                partition_audit = audit_european_floor_partition(
                    footprint,
                    cand_tuple,
                    expected_dwelling_count=requested,
                    topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
                )
                facade_lengths = _facade_contact_lengths(footprint, cand_tuple)
                if not partition_audit.passed:
                    last_fallback_reason = "PARTITION_AUDIT_FAILED"
                elif any(length < minimum_facade_contact_m for length in facade_lengths):
                    last_fallback_reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
                else:
                    return EuropeanGeneratedFloorLayout(
                        requested_dwelling_count=requested,
                        dwelling_polygons=cand_tuple,
                        partition_audit=partition_audit,
                        facade_contact_lengths_m=facade_lengths,
                        fallback_reason=None,
                        dwelling_layout_emitted=True,
                    )

    # Strategy 2: Radial / Angular Sector Partition around Centroid / Courtyard Hole
    origins = [footprint.centroid, footprint.representative_point()]
    if footprint.interiors:
        hole_poly = Polygon(footprint.interiors[0])
        origins.append(hole_poly.centroid)

    radius = max(footprint.bounds[2] - footprint.bounds[0], footprint.bounds[3] - footprint.bounds[1]) * 2.0
    step_deg = 360.0 / requested

    for orig in origins:
        cx, cy = orig.x, orig.y
        for start_deg in range(0, 360, 4):
            candidates = []
            possible = True
            for i in range(requested):
                a1 = math.radians(start_deg + i * step_deg)
                a2 = math.radians(start_deg + (i + 1) * step_deg)
                arc_pts = [
                    (cx + radius * math.cos(a), cy + radius * math.sin(a))
                    for a in (a1 + (a2 - a1) * t / 16.0 for t in range(17))
                ]
                wedge = Polygon([(cx, cy)] + arc_pts)
                inter = footprint.intersection(wedge)
                if inter.is_empty:
                    possible = False
                    break
                if inter.geom_type == "Polygon":
                    candidates.append(inter)
                elif inter.geom_type == "MultiPolygon":
                    parts = [p for p in inter.geoms if p.area > 1e-4]
                    if len(parts) == 1:
                        candidates.append(parts[0])
                    else:
                        possible = False
                        break
                else:
                    possible = False
                    break

            if possible and len(candidates) == requested:
                cand_tuple = tuple(candidates)
                partition_audit = audit_european_floor_partition(
                    footprint,
                    cand_tuple,
                    expected_dwelling_count=requested,
                    topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
                )
                facade_lengths = _facade_contact_lengths(footprint, cand_tuple)
                if not partition_audit.passed:
                    last_fallback_reason = "PARTITION_AUDIT_FAILED"
                elif any(length < minimum_facade_contact_m for length in facade_lengths):
                    last_fallback_reason = "INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M"
                else:
                    return EuropeanGeneratedFloorLayout(
                        requested_dwelling_count=requested,
                        dwelling_polygons=cand_tuple,
                        partition_audit=partition_audit,
                        facade_contact_lengths_m=facade_lengths,
                        fallback_reason=None,
                        dwelling_layout_emitted=True,
                    )

    return EuropeanGeneratedFloorLayout(
        requested_dwelling_count=requested,
        dwelling_polygons=(),
        partition_audit=None,
        facade_contact_lengths_m=(),
        fallback_reason=last_fallback_reason,
        dwelling_layout_emitted=False,
    )


def european_layout_to_zone_specs(
    layout: EuropeanGeneratedFloorLayout,
    *,
    building_id: str,
    floor_index: int = 0,
    z_floor_m: float = 0.0,
    height_m: float = 3.0,
    n_storey: int = 1,
) -> list[dict[str, object]]:
    """Translate one emitted dwelling layout into explicit extrusion inputs.

    When ``n_storey > 1``, repeats the in-plane dwelling partition across every
    storey (storey_index = 0 .. n_storey-1) at the appropriate z-offset, fixing
    FINDING EU-12-01.
    """
    identifier = str(building_id).strip()
    if not identifier:
        raise ValueError("building_id is required")
    if floor_index < 0:
        raise ValueError("floor_index must be non-negative")
    if n_storey < 1:
        raise ValueError("n_storey must be at least 1")
    if not math.isfinite(z_floor_m) or not math.isfinite(height_m) or height_m <= 0.0:
        raise ValueError("z_floor_m must be finite and height_m must be finite and positive")
    if not layout.dwelling_layout_emitted or not layout.partition_audit or not layout.partition_audit.passed:
        raise ValueError("Cannot create zone specs from a layout that was not emitted cleanly")

    zones: list[dict[str, object]] = []
    for s_idx in range(n_storey):
        storey_num = floor_index + s_idx
        zf = z_floor_m + s_idx * height_m
        zc = zf + height_m
        for d_idx, polygon in enumerate(layout.dwelling_polygons):
            zones.append({
                "name": f"{identifier}_F{storey_num}_dwelling_{d_idx}",
                "floor_polygon": polygon,
                "coords_m": list(polygon.exterior.coords)[:-1],
                "z_floor": zf,
                "z_ceiling": zc,
                "height_m": height_m,
                "mode": "european_dwelling_layout",
            })
    return zones


@dataclass(frozen=True)
class EuropeanStoreyGroup:
    """One or more consecutive storeys sharing the same emitted zones.

    ``allocate_european_dwellings`` can legitimately allocate 0 dwellings to
    a storey when the declared total is below the storey count (a single
    multi-storey SFH/TH dwelling): that storey is not a separate partition,
    it is the *same* dwelling continuing upward, so its height is absorbed
    into the previous non-zero storey's zones rather than emitting a
    zero-dwelling partition (which is undefined) or a spurious extra zone
    (which would break T01 conservation).
    """

    start_storey_index: int
    storey_span: int
    layout: EuropeanGridLayout


@dataclass(frozen=True)
class EuropeanBuildingDwellingLayout:
    """T01/T02: one building's conserved, per-storey ruled dwelling layout.

    ``storey_groups`` covers every physical storey exactly once (a group's
    ``storey_span`` may exceed 1 when trailing storeys were absorbed);
    consecutive groups sharing the same ``dwelling_count`` reuse the
    identical cached partition, per T01's caching instruction.

    ``fallback_reason_by_storey`` (EU-15 T01) carries each group's own reason
    for leaving the ruled route -- non-null wherever that group's scheme is
    ``equal_strip_multi_angle_sweep``, even when the building as a whole
    emits successfully and the top-level ``fallback_reason`` above is None.
    """

    storey_groups: tuple[EuropeanStoreyGroup, ...]
    dwelling_layout_emitted: bool
    fallback_reason: str | None
    observed_max_per_floor: int
    scheme_by_storey: tuple[str, ...]
    fallback_reason_by_storey: tuple[str | None, ...] = ()


EUROPEAN_LAYOUT_REGIME = "nocore"   # D-EU-79/D-EU-95. "ruled" = the parked corridor path.


def generate_european_building_dwelling_layout(
    footprint: BaseGeometry,
    *,
    floor_allocations: tuple[EuropeanFloorAllocation, ...],
    minimum_facade_contact_m: float = 2.5,
) -> EuropeanBuildingDwellingLayout:
    """Conserve the declared dwelling total across storeys (T01) and cap
    density at the ruled grid's 8/floor ceiling, failing the whole building
    closed rather than approximating above it (T02).

    Never reduces a building's declared dwelling count: a storey this
    function cannot serve fails the *building* closed and falls back to the
    existing massing-box ``one_zone_per_floor`` route, exactly as it does for
    any other unlayoutable building today.
    """
    if not floor_allocations:
        raise ValueError("floor_allocations must be non-empty")
    observed_max_per_floor = max(fa.dwelling_count for fa in floor_allocations)
    if observed_max_per_floor > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        return EuropeanBuildingDwellingLayout(
            storey_groups=(), dwelling_layout_emitted=False,
            fallback_reason=DWELLING_DENSITY_REFUSAL_TOKEN,
            observed_max_per_floor=observed_max_per_floor, scheme_by_storey=(),
            fallback_reason_by_storey=(),
        )
    cache: dict[int, EuropeanGridLayout] = {}
    # D-EU-49 / T08: a single-storey building carries no circulation zone at
    # all -- a stair core exists to connect storeys, and there is nothing to
    # connect. Gated once, here, at the building level (fact 8: both the IDF
    # path and the side-car emitter call this same function), so it applies
    # uniformly regardless of which route the storey's layout takes -- never
    # as a special case inside one route.
    carve_circulation = len(floor_allocations) != 1

    def _layout_for(count: int) -> EuropeanGridLayout:
        if count not in cache:
            if EUROPEAN_LAYOUT_REGIME == "nocore":
                cache[count] = generate_european_nocore_storey_layout(
                    footprint, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                )
            else:
                cache[count] = generate_european_ruled_storey_layout(
                    footprint, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                    carve_circulation=carve_circulation,
                )
        return cache[count]

    groups: list[EuropeanStoreyGroup] = []
    for index, allocation in enumerate(floor_allocations):
        count = allocation.dwelling_count
        if count == 0:
            if not groups:
                raise AssertionError("floor_allocations[0] must always carry at least one dwelling")
            groups[-1] = EuropeanStoreyGroup(
                start_storey_index=groups[-1].start_storey_index,
                storey_span=groups[-1].storey_span + 1,
                layout=groups[-1].layout,
            )
            continue
        groups.append(EuropeanStoreyGroup(start_storey_index=index, storey_span=1, layout=_layout_for(count)))
    if not all(group.layout.dwelling_layout_emitted for group in groups):
        reason = next(
            (group.layout.fallback_reason for group in groups if not group.layout.dwelling_layout_emitted),
            "PARTITION_AUDIT_FAILED",
        )
        return EuropeanBuildingDwellingLayout(
            storey_groups=(), dwelling_layout_emitted=False, fallback_reason=reason,
            observed_max_per_floor=observed_max_per_floor, scheme_by_storey=(),
            fallback_reason_by_storey=(),
        )
    scheme_by_storey: list[str] = []
    fallback_reason_by_storey: list[str | None] = []
    for group in groups:
        scheme_by_storey.extend([group.layout.scheme] * group.storey_span)
        fallback_reason_by_storey.extend([group.layout.fallback_reason] * group.storey_span)
    return EuropeanBuildingDwellingLayout(
        storey_groups=tuple(groups), dwelling_layout_emitted=True, fallback_reason=None,
        observed_max_per_floor=observed_max_per_floor, scheme_by_storey=tuple(scheme_by_storey),
        fallback_reason_by_storey=tuple(fallback_reason_by_storey),
    )


# EU-16 T09 / FINDING 210: a storey-group's circulation core is cut via a
# shapely boolean (``plate.difference(circulation_polygon)`` and the wing
# ``unary_union`` in ``_combine_wing_results``).  These boundary vertices can
# carry sub-millimetre floating-point noise or a near-collinear point that a
# different GEOS build resolves differently when EnergyPlus later pairs the
# ceiling of one storey with the floor of the storey above it -- observed on
# Speed's Linux/GEOS build as a genuine "Vertex size mismatch" FATAL
# (RoofCeiling:Detailed, base vs outside-boundary surface, e.g. 8 vs 9
# vertices) on rings that regenerate byte-identical and internally consistent
# on this Windows/GEOS build (proved by two independent local rebuilds of the
# named example, ``relation/12771676`` stem ``8b3598ac47b3f4a0``: identical
# geometry both times, 0 vertex-count mismatches locally). Snapping every
# emitted ring to a fixed 1 mm precision grid removes that GEOS-build-
# dependent fragility without moving the partition, the audit result, or any
# area by more than floating-point noise.
RING_STABILIZATION_GRID_M = 0.001


def _stabilize_ring_coords(polygon: BaseGeometry, grid_size_m: float = RING_STABILIZATION_GRID_M) -> list[tuple[float, float]]:
    """Return the exterior ring, snapped to a fixed precision grid (FINDING 210).

    Falls back to the unsnapped ring whenever snapping degenerates the
    polygon (collapses an edge to zero length, drops below 3 vertices, or
    changes geometry type) -- never silently emits an empty or invalid ring.

    P01c 2026-09-01: a caller's polygon (observed for a scheme's circulation
    remainder) can already be a ``MultiPolygon`` before snapping ever runs --
    take the largest piece by area so ``.exterior`` below always has a
    ``Polygon`` to read, same "never silently emits an empty or invalid
    ring" contract as the snap-degenerate fallback, one step earlier.
    """
    if polygon.geom_type == "MultiPolygon":
        polygon = max(polygon.geoms, key=lambda g: g.area)
    snapped = set_precision(polygon, grid_size=grid_size_m)
    if snapped.is_empty or snapped.geom_type != "Polygon" or snapped.area <= 0.0:
        return list(polygon.exterior.coords)[:-1]
    return list(snapped.exterior.coords)[:-1]


def european_building_layout_to_zone_specs(
    building_layout: EuropeanBuildingDwellingLayout,
    *,
    building_id: str,
    z_floor_m: float = 0.0,
    height_m: float = 3.0,
) -> list[dict[str, object]]:
    """Translate one conserved per-storey building layout into zone specs.

    Fixes defect 2 (FINDING 201): each storey group gets its own dwelling
    count from ``floor_allocations``, never a single ``units_per_floor``
    ceiling replayed across every storey.  A group spanning more than one
    physical storey (absorbed zero-count floors) emits one zone per
    dwelling, extruded across the group's full height -- never one zone per
    physical storey -- so the emitted zone count still equals the declared
    dwelling total exactly.

    D-EU-39 §3 / EU-15 T05: whenever a group's own layout carved a
    circulation polygon out of the plate, that polygon is emitted here too,
    as one additional zone per group tagged ``conditioned=False`` -- the
    unconditioned stair core / corridor spine, extruded across the same
    group height as its dwellings so every dwelling in the group shares a
    party wall with it. Every dwelling zone is tagged ``conditioned=True``.
    """
    identifier = str(building_id).strip()
    if not identifier:
        raise ValueError("building_id is required")
    if not math.isfinite(z_floor_m) or not math.isfinite(height_m) or height_m <= 0.0:
        raise ValueError("z_floor_m must be finite and height_m must be finite and positive")
    if not building_layout.dwelling_layout_emitted:
        raise ValueError("Cannot create zone specs from a layout that was not emitted cleanly")
    zones: list[dict[str, object]] = []
    for group in building_layout.storey_groups:
        zf = z_floor_m + group.start_storey_index * height_m
        zc = zf + group.storey_span * height_m
        for dwelling_index, polygon in enumerate(group.layout.dwelling_polygons):
            zones.append({
                "name": f"{identifier}_F{group.start_storey_index}_dwelling_{dwelling_index}",
                "floor_polygon": polygon,
                "coords_m": _stabilize_ring_coords(polygon),
                "z_floor": zf,
                "z_ceiling": zc,
                "height_m": zc - zf,
                "storey_span": group.storey_span,
                "mode": "european_dwelling_layout",
                "scheme": group.layout.scheme,
                "conditioned": True,
            })
        circulation_polygon = group.layout.circulation_polygon
        if circulation_polygon is not None:
            zones.append({
                "name": f"{identifier}_F{group.start_storey_index}_circulation",
                "floor_polygon": circulation_polygon,
                "coords_m": _stabilize_ring_coords(circulation_polygon),
                "z_floor": zf,
                "z_ceiling": zc,
                "height_m": zc - zf,
                "storey_span": group.storey_span,
                "mode": "european_dwelling_layout",
                "scheme": group.layout.scheme,
                "conditioned": False,
                "infiltration_m3_s_m2": CIRCULATION_INFILTRATION_M3_S_M2,
            })
    return zones


def european_building_layout_area_summary(
    building_layout: EuropeanBuildingDwellingLayout,
) -> tuple[float, float]:
    """Return ``(gross_footprint_area_m2, conditioned_floor_area_m2)``.

    D-EU-39 §3: circulation is carved out of the observed plate, so the two
    numbers diverge exactly on the buildings that carry a core. Summed once
    per storey group (never per absorbed physical storey), the same
    convention the existing per-building floor-area accounting already
    uses, so the two are directly comparable.
    """
    if not building_layout.dwelling_layout_emitted:
        raise ValueError("Cannot summarise area for a layout that was not emitted cleanly")
    gross = 0.0
    conditioned = 0.0
    for group in building_layout.storey_groups:
        layout = group.layout
        dwelling_area = sum(float(polygon.area) for polygon in layout.dwelling_polygons)
        conditioned += dwelling_area
        gross += dwelling_area + float(layout.circulation_area_m2)
    return gross, conditioned


def allocate_european_dwellings(
    *,
    archetype_id: str,
    building_type: str,
    n_apartment: float,
    n_storey: float,
    plate_area_m2: float,
) -> EuropeanDwellingAllocation:
    """Allocate dwelling zones per D-EU-01/D-EU-04 without silent loss.

    Floors receive quotient dwellings plus the first ``remainder`` storeys
    receiving one additional dwelling.  This fixes GEO-07's storey order and
    makes the exact total independently checkable.  A core is added outside
    the conditioned plate at the ruling's lower 6% bound only when the rounded
    dwelling density is at least two per storey.
    """
    identifier = str(archetype_id).strip()
    typology = str(building_type).strip().upper()
    if not identifier:
        raise ValueError("archetype_id is required")
    if typology not in RESIDENTIAL_TYPES:
        raise ValueError("building_type must be one of SFH, TH, MFH, AB")
    storeys = _rounded_count(n_storey, "n_storey")
    plate = float(plate_area_m2)
    if not math.isfinite(plate) or plate <= 0:
        raise ValueError("plate_area_m2 must be finite and positive")

    dwellings = _rounded_count(n_apartment, "n_apartment")
    quotient, remainder = divmod(dwellings, storeys)
    units_per_floor = math.ceil(dwellings / storeys)
    core_required = dwellings / storeys >= 2.0
    core_area = plate * CORE_FRACTION_OF_PLATE if core_required else 0.0
    floors = tuple(
        EuropeanFloorAllocation(
            storey_index=index,
            dwelling_count=quotient + (1 if index < remainder else 0),
            conditioned_area_m2=plate,
            unconditioned_core_area_m2=core_area,
        )
        for index in range(storeys)
    )
    if sum(floor.dwelling_count for floor in floors) != dwellings:
        raise AssertionError("internal dwelling allocation failed to conserve the rounded total")
    return EuropeanDwellingAllocation(
        archetype_id=identifier,
        building_type=typology,
        declared_apartments=float(n_apartment),
        dwelling_count=dwellings,
        storey_count=storeys,
        units_per_floor=units_per_floor,
        has_unconditioned_core=core_required,
        floor_allocations=floors,
    )


def audit_european_floor_partition(
    footprint: BaseGeometry,
    dwelling_polygons: Iterable[BaseGeometry],
    *,
    expected_dwelling_count: int,
    relative_area_tolerance: float = 0.01,
    topology_tolerance_fraction: float = EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION,
    topology_tolerance_m2: float | None = None,
) -> EuropeanFloorPartitionAudit:
    """Fail closed on a supplied European floor partition that violates GEO-01.

    The audit is intentionally independent of the future layout generator:
    it compares a union of emitted dwelling polygons to the source footprint.
    GEO-01 allows at most one-percent total area error, while gaps, overlaps,
    and geometry outside the plate remain separate topology failures.  The
    tiny topology tolerance only absorbs geometric floating-point noise.
    """
    expected = int(expected_dwelling_count)
    if expected <= 0:
        raise ValueError("expected_dwelling_count must be positive")
    if not 0.0 <= relative_area_tolerance <= 1.0:
        raise ValueError("relative_area_tolerance must be between zero and one")
    if topology_tolerance_fraction < 0.0:
        raise ValueError("topology_tolerance_fraction must be non-negative")
    if topology_tolerance_m2 is not None and topology_tolerance_m2 < 0.0:
        raise ValueError("topology_tolerance_m2 must be non-negative")
    if footprint.is_empty or not footprint.is_valid or footprint.area <= 0.0:
        raise ValueError("footprint must be a valid positive-area geometry")

    dwellings = tuple(dwelling_polygons)
    invalid = tuple(
        polygon
        for polygon in dwellings
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0.0
    )
    valid_dwellings = tuple(polygon for polygon in dwellings if polygon not in invalid)
    union = unary_union(valid_dwellings) if valid_dwellings else footprint.boundary
    union_area = float(union.area)
    footprint_area = float(footprint.area)
    # Compatibility callers may provide an explicit tolerance, but all
    # production European generation calls use the declared relative rule.
    topology_tolerance = (
        float(topology_tolerance_m2)
        if topology_tolerance_m2 is not None
        else footprint_area * float(topology_tolerance_fraction)
    )
    total_dwelling_area = sum(float(polygon.area) for polygon in valid_dwellings)
    gap_area = float(footprint.difference(union).area)
    outside_area = float(union.difference(footprint).area)
    overlap_area = max(0.0, total_dwelling_area - union_area)
    area_error = abs(union_area - footprint_area) / footprint_area

    failures: list[str] = []
    if len(dwellings) != expected:
        failures.append("DWELLING_COUNT")
    if invalid:
        failures.append("INVALID_DWELLING")
    if gap_area > topology_tolerance:
        failures.append("AREA_GAP")
    if overlap_area > topology_tolerance:
        failures.append("AREA_OVERLAP")
    if outside_area > topology_tolerance:
        failures.append("OUTSIDE_FOOTPRINT")
    if area_error > relative_area_tolerance:
        failures.append("AREA_CONSERVATION")
    return EuropeanFloorPartitionAudit(
        expected_dwelling_count=expected,
        observed_dwelling_count=len(dwellings),
        footprint_area_m2=footprint_area,
        union_area_m2=union_area,
        gap_area_m2=gap_area,
        overlap_area_m2=overlap_area,
        outside_area_m2=outside_area,
        area_error_fraction=area_error,
        failures=tuple(failures),
    )
