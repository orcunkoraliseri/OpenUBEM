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
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.ops import split, unary_union


# --- EU-13B: ruled dwelling-layout scheme (footprint regularization, grid,
# morphological branching, habitability retry).  These are additive to the
# module above: ``generate_european_dwelling_layout`` keeps its existing
# behaviour unchanged as the ``equal_strip_multi_angle_sweep`` secondary
# route for storeys the ruled grid cannot serve.

RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 8
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
    # dwelling_count -> (nu, nv, ruled grid name, merge_one_pair)
    1: (1, 1, "ruled_grid_1x1", False),
    2: (2, 1, "ruled_grid_2x1", False),
    3: (2, 2, "ruled_grid_2x2", True),
    4: (2, 2, "ruled_grid_2x2", False),
    5: (3, 2, "ruled_grid_3x2", True),
    6: (3, 2, "ruled_grid_3x2", False),
    7: (4, 2, "ruled_grid_4x2", True),
    8: (4, 2, "ruled_grid_4x2", False),
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


def generate_european_grid_layout(
    plate: BaseGeometry,
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
    axis_angle_deg: float | None = None,
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
        raise ValueError("dwelling_count must be within the ruled grid's 1..8 range")
    if plate.geom_type != "Polygon" or plate.is_empty or not plate.is_valid or plate.area <= 0.0:
        raise ValueError("plate must be a valid positive-area Polygon")
    origin = plate.centroid
    base_nu, base_nv, base_name, base_merge = _grid_for_count(dwelling_count)
    long_angle = axis_angle_deg if axis_angle_deg is not None else _long_axis_angle_degrees(plate)

    def _try(nu: int, nv: int, scheme: str, merge: bool, angle: float) -> EuropeanGridLayout | None:
        plate_for_cutting = plate
        circulation_polygon = None
        circulation_area = 0.0
        wants_circulation = dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
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


def _split_at_reflex_vertex(
    footprint: BaseGeometry, *, tolerance_m: float = 0.15
) -> tuple[BaseGeometry, BaseGeometry]:
    """Report Sec 6.2: split a non-convex plate along the reflex orthogonal axis.

    Tries both axis-aligned lines through the (first) reflex vertex and keeps
    whichever produces exactly two polygon wings with the better combined
    rectangularity (``piece.area / piece.minimum_rotated_rectangle.area``),
    which is what "convex lobes" means in practice for an orthogonal plate.
    Pre-simplifies at ``tolerance_m`` (the pipeline's own regularization
    tolerance, not the coarser 0.5 m ``classify_building_morphology`` uses
    for its routing decision) so the cut line matches what regularization
    elsewhere would keep, and slivers/near-collinear GIS noise below that
    tolerance never register as a spurious second reflex vertex here.
    """
    denoised = footprint.simplify(tolerance_m, preserve_topology=True)
    if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
        denoised = footprint
    oriented = orient(denoised, sign=1.0)
    coords = list(oriented.exterior.coords)[:-1]
    n = len(coords)
    reflex_point = None
    for i in range(n):
        a, b, c = coords[i - 1], coords[i], coords[(i + 1) % n]
        dir_in = (b[0] - a[0], b[1] - a[1])
        dir_out = (c[0] - b[0], c[1] - b[1])
        cross = dir_in[0] * dir_out[1] - dir_in[1] * dir_out[0]
        dot = dir_in[0] * dir_out[0] + dir_in[1] * dir_out[1]
        turn = math.degrees(math.atan2(cross, dot))
        if 180.0 - turn > 185.0:
            reflex_point = b
            break
    if reflex_point is None:
        raise ValueError("footprint has no reflex vertex to split at")
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


def _l_shape_wings(
    footprint: BaseGeometry, *, tolerance_m: float = 0.15, max_wings: int = 4
) -> list[BaseGeometry]:
    """T03: recurse ``_split_at_reflex_vertex`` on the larger lobe.

    A single clean L-shape (one real reflex vertex at ``tolerance_m``) still
    returns the plain two-wing split. A noisy real footprint whose main lobe
    itself carries a residual reflex vertex at this tighter tolerance keeps
    splitting that lobe (always the larger of the two most-recently produced
    pieces, since ``_split_at_reflex_vertex`` already orders its return by
    area) until no wing has one left or ``max_wings`` is reached.
    """
    wings = [footprint]
    while len(wings) < max_wings:
        split_index = None
        for index, wing in enumerate(wings):
            denoised = wing.simplify(tolerance_m, preserve_topology=True)
            if denoised.is_empty or not denoised.is_valid or denoised.geom_type != "Polygon" or denoised.area <= 0.0:
                denoised = wing
            if _reflex_vertex_count(denoised) > 0:
                split_index = index
                break
        if split_index is None:
            break
        try:
            larger, smaller = _split_at_reflex_vertex(wings[split_index], tolerance_m=tolerance_m)
        except ValueError:
            break
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
    nodes_aligned = [
        box(cx - node_side / 2.0, cy - node_side / 2.0, cx + node_side / 2.0, cy + node_side / 2.0)
        for cx, cy in inner_corners
    ]

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
) -> EuropeanGridLayout:
    """Report Sec 6.4: courtyard / U-shape unfolding, the ``courtyard_secondary``
    route's actual implementation (T02). Subtracts the courtyard void, places
    a circulation node at each inner corner, then partitions each remaining
    wing by its own area fraction of ``dwelling_count`` -- recursing through
    ``generate_european_ruled_storey_layout`` exactly as the L-shape route's
    wings already do. Never approximates: any wing, audit or habitability
    failure raises so the caller falls back to the secondary route.
    """
    wants_circulation = dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION
    target_circulation_area = CIRCULATION_FRACTION_OF_PLATE * footprint.area if wants_circulation else 0.0
    wings, nodes = _courtyard_wings_and_nodes(footprint, circulation_area_total_m2=target_circulation_area)
    wing_areas = [wing.area for wing in wings]
    counts = _allocate_wing_dwelling_counts(wing_areas, dwelling_count)
    wing_results = [
        generate_european_ruled_storey_layout(
            wing, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
            regularization_tolerance_m=regularization_tolerance_m,
        )
        for wing, count in zip(wings, counts)
    ]
    combined = _combine_wing_results(
        footprint, wing_results, dwelling_count=dwelling_count,
        minimum_facade_contact_m=minimum_facade_contact_m, scheme="courtyard_wing_unfold",
        extra_circulation=nodes, keep_circulation_polygon=True,
    )
    if combined is None:
        raise ValueError("courtyard wing partition failed audit or habitability")
    outside_band = combined.circulation_outside_ruled_absolute_band or (
        wants_circulation
        and not (CIRCULATION_ABSOLUTE_BAND_M2[0] <= combined.circulation_area_m2 <= CIRCULATION_ABSOLUTE_BAND_M2[1])
    )
    if outside_band != combined.circulation_outside_ruled_absolute_band:
        combined = EuropeanGridLayout(**{**combined.__dict__, "circulation_outside_ruled_absolute_band": outside_band})
    return combined


def generate_european_linear_gallery_layout(
    plate: BaseGeometry, *, dwelling_count: int, minimum_facade_contact_m: float = 2.5,
) -> EuropeanGridLayout:
    """Report Sec 6.3: I-shape linear gallery, double-loaded corridor spine.

    A 1.80 m corridor band along the long axis splits the plate into two
    lateral bands; each band is then sliced into equal-area longitudinal
    bays by the same bisection primitive used for the point-block grid, and
    the total bay count across both bands sums to ``dwelling_count`` exactly
    (never a count reduction).
    """
    if dwelling_count <= 0 or dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError("dwelling_count must be within the ruled grid's 1..8 range")
    origin = plate.centroid
    angle = _long_axis_angle_degrees(plate)
    grid_name = _grid_for_count(dwelling_count)[2]
    wants_circulation = dwelling_count >= CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION

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


def generate_european_ruled_storey_layout(
    footprint: BaseGeometry,
    *,
    dwelling_count: int,
    minimum_facade_contact_m: float = 2.5,
    regularization_tolerance_m: float = 0.15,
) -> EuropeanGridLayout:
    """T04/T05 entry point: regularize, classify morphology, then partition.

    Falls back to the existing ``equal_strip_multi_angle_sweep`` secondary
    route (unchanged) whenever the ruled route cannot serve this storey --
    regularization area delta beyond the 2% gate, or a route this task does
    not implement (courtyard unfolding), or a habitability/audit failure the
    grid's own retries could not resolve.
    """
    if dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR:
        raise ValueError("caller must apply the >8 per-floor refusal before calling the ruled partitioner")

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
                regularization_tolerance_m=regularization_tolerance_m,
            )
        except (ValueError, IndexError):
            return _secondary(f"{morphology.reason}_FAILED")

    if morphology.route == "l_shape_decomposition":
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
        for wings in wing_candidates:
            try:
                counts = _allocate_wing_dwelling_counts([wing.area for wing in wings], dwelling_count)
                wing_results = [
                    generate_european_ruled_storey_layout(
                        wing, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
                        regularization_tolerance_m=regularization_tolerance_m,
                    )
                    for wing, count in zip(wings, counts)
                ]
                combined = _combine_wing_results(
                    footprint, wing_results, dwelling_count=dwelling_count,
                    minimum_facade_contact_m=minimum_facade_contact_m, scheme="l_shape_decomposition",
                    keep_circulation_polygon=False,
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
        if morphology.route == "i_shape_linear_gallery":
            result = generate_european_linear_gallery_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
            )
        else:
            result = generate_european_grid_layout(
                plate, dwelling_count=dwelling_count, minimum_facade_contact_m=minimum_facade_contact_m,
            )
    except (ValueError, IndexError):
        return _secondary("PARTITION_AUDIT_FAILED")
    if not result.dwelling_layout_emitted:
        return _secondary(result.fallback_reason)
    return result


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
            fallback_reason="DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8",
            observed_max_per_floor=observed_max_per_floor, scheme_by_storey=(),
            fallback_reason_by_storey=(),
        )
    cache: dict[int, EuropeanGridLayout] = {}

    def _layout_for(count: int) -> EuropeanGridLayout:
        if count not in cache:
            cache[count] = generate_european_ruled_storey_layout(
                footprint, dwelling_count=count, minimum_facade_contact_m=minimum_facade_contact_m,
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
    """
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
