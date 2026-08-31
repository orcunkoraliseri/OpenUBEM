"""`GEO-08` — independent-reimplementation agreement (`D-EU-04-F` F4, ruled 2026-08-28).

This is NOT Grasshopper parity. Parity with the Ankara/Grasshopper method is recorded as NOT TESTED
in MVP §4.8 and must never be written as passed. What is asserted here is that a second, entirely
independent Python partitioner — standard library only, importing nothing from `openubem` — agrees
with `openubem.geometry.european_residential` on zone count, areas, exterior facade contact and
adjacency, with ordering ignored.
"""
from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest
from shapely.geometry import Polygon
from shapely.affinity import rotate, translate

from openubem.geometry.european_residential import (
    generate_european_dwelling_layout,
    generate_external_unconditioned_core,
)
from tests.reference.geo08_reference_partitioner import (
    ReferenceLayout,
    attach_external_core,
    convex_intersection_area,
    partition,
    shoelace_area,
)

REFERENCE_SOURCE = Path(__file__).parent / "reference" / "geo08_reference_partitioner.py"
AREA_TOLERANCE = 0.01
CONTACT_TOLERANCE_M = 1e-3

FIXTURES = {
    "axis_aligned_rectangle": ([(0.0, 0.0), (30.0, 0.0), (30.0, 12.0), (0.0, 12.0)], 3),
    "wide_plate": ([(0.0, 0.0), (48.0, 0.0), (48.0, 16.0), (0.0, 16.0)], 4),
    "trapezoid": ([(0.0, 0.0), (40.0, 0.0), (34.0, 14.0), (6.0, 14.0)], 2),
    "square_pair": ([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)], 2),
}


def _ring(polygon: Polygon) -> list[tuple[float, float]]:
    return list(polygon.exterior.coords)[:-1]


def _implementation(footprint: Polygon, count: int):
    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=count)
    if not layout.dwelling_layout_emitted:
        pytest.skip(f"implementation declined this fixture: {layout.fallback_reason}")
    return layout


def test_the_reference_imports_nothing_from_openubem():
    """The independence is part of the gate: a reference that called the code under test proves nothing."""
    tree = ast.parse(REFERENCE_SOURCE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert imported, "the reference must import something, or this check is vacuous"
    assert not [name for name in imported if name.split(".")[0] == "openubem"]
    assert not [name for name in imported if name.split(".")[0] in {"shapely", "numpy", "geopandas"}]


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_zone_count_agrees(name: str):
    coords, count = FIXTURES[name]
    layout = _implementation(Polygon(coords), count)
    reference = partition(coords, count)
    assert reference.zone_count == len(layout.dwelling_polygons) == count


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_areas_agree_ordering_ignored(name: str):
    coords, count = FIXTURES[name]
    layout = _implementation(Polygon(coords), count)
    reference = partition(coords, count)
    implemented = sorted(float(polygon.area) for polygon in layout.dwelling_polygons)
    referenced = sorted(reference.areas_m2)
    for left, right in zip(implemented, referenced):
        assert abs(left - right) <= AREA_TOLERANCE * max(left, right)


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_total_area_is_conserved_by_both(name: str):
    coords, count = FIXTURES[name]
    layout = _implementation(Polygon(coords), count)
    reference = partition(coords, count)
    source_area = shoelace_area(coords)
    implemented_total = sum(float(polygon.area) for polygon in layout.dwelling_polygons)
    assert abs(implemented_total - source_area) <= AREA_TOLERANCE * source_area
    assert abs(reference.total_area_m2 - source_area) <= AREA_TOLERANCE * source_area


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_exterior_facade_contact_agrees_ordering_ignored(name: str):
    coords, count = FIXTURES[name]
    layout = _implementation(Polygon(coords), count)
    reference = partition(coords, count)
    implemented = sorted(float(value) for value in layout.facade_contact_lengths_m)
    referenced = sorted(reference.facade_contact_m)
    for left, right in zip(implemented, referenced):
        assert abs(left - right) <= max(CONTACT_TOLERANCE_M, 1e-6 * max(left, right))


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_adjacency_count_agrees(name: str):
    coords, count = FIXTURES[name]
    layout = _implementation(Polygon(coords), count)
    reference = partition(coords, count)
    shared = 0
    polygons = list(layout.dwelling_polygons)
    for left in range(len(polygons)):
        for right in range(left + 1, len(polygons)):
            if polygons[left].intersection(polygons[right]).length > CONTACT_TOLERANCE_M:
                shared += 1
    assert shared == len(reference.adjacency)


def test_reference_is_invariant_under_rotation_and_translation():
    """GEO-02's invariance must hold for the reference too, or it cannot arbitrate GEO-02."""
    coords, count = FIXTURES["axis_aligned_rectangle"]
    base = partition(coords, count)
    moved = Polygon(coords)
    moved = rotate(moved, 37.0, origin="centroid")
    moved = translate(moved, xoff=612_345.0, yoff=5_070_000.0)
    transformed = partition(_ring(moved), count)
    for left, right in zip(sorted(base.areas_m2), sorted(transformed.areas_m2)):
        assert abs(left - right) <= 1e-5 * max(left, right)
    for left, right in zip(sorted(base.facade_contact_m), sorted(transformed.facade_contact_m)):
        assert abs(left - right) <= 1e-5 * max(left, right, 1.0)


def test_reference_refuses_a_degenerate_footprint():
    with pytest.raises(ValueError):
        partition([(0.0, 0.0), (1.0, 1.0)], 2)


def test_reference_refuses_a_non_positive_dwelling_count():
    coords, _ = FIXTURES["axis_aligned_rectangle"]
    with pytest.raises(ValueError):
        partition(coords, 0)


def test_reference_long_axis_matches_the_geometric_expectation():
    coords, count = FIXTURES["wide_plate"]
    reference = partition(coords, count)
    assert math.isclose(abs(reference.long_axis_degrees) % 180.0, 0.0, abs_tol=1e-6)


CORE_FIXTURES = {
    "rect_30x12_core45": ([(0.0, 0.0), (30.0, 0.0), (30.0, 12.0), (0.0, 12.0)], 45.0),
    "rect_48x16_core60": ([(0.0, 0.0), (48.0, 0.0), (48.0, 16.0), (0.0, 16.0)], 60.0),
    "square_20_core25": ([(0.0, 0.0), (20.0, 0.0), (20.0, 20.0), (0.0, 20.0)], 25.0),
}

CORE_AREA_TOLERANCE_M2 = 1e-6


def _implementation_core(coords, area_m2):
    core = generate_external_unconditioned_core(
        Polygon(coords), requested_area_m2=area_m2
    )
    if core.core_polygon is None:
        pytest.skip(f"implementation declined this core: {core.fallback_reason}")
    return core


@pytest.mark.parametrize("name", sorted(CORE_FIXTURES))
def test_circulation_area_agrees(name: str):
    """GEO-08 compares circulation area, not only dwelling area (MVP §4.8)."""
    coords, requested = CORE_FIXTURES[name]
    implemented = _implementation_core(coords, requested)
    reference = attach_external_core(coords, requested)
    assert abs(float(implemented.emitted_area_m2) - reference.area_m2) <= CORE_AREA_TOLERANCE_M2
    assert abs(reference.area_m2 - requested) <= CORE_AREA_TOLERANCE_M2


@pytest.mark.parametrize("name", sorted(CORE_FIXTURES))
def test_circulation_shared_boundary_agrees(name: str):
    coords, requested = CORE_FIXTURES[name]
    implemented = _implementation_core(coords, requested)
    reference = attach_external_core(coords, requested)
    assert abs(
        float(implemented.shared_boundary_length_m) - reference.shared_boundary_m
    ) <= max(CONTACT_TOLERANCE_M, 1e-6 * reference.shared_boundary_m)


@pytest.mark.parametrize("name", sorted(CORE_FIXTURES))
def test_circulation_is_additional_area_never_carved_from_the_plate(name: str):
    """D-EU-01 semantics: the core is added outside `A_C_Ref`, never taken out of it."""
    coords, requested = CORE_FIXTURES[name]
    implemented = _implementation_core(coords, requested)
    reference = attach_external_core(coords, requested)
    assert float(implemented.overlap_area_m2) <= CORE_AREA_TOLERANCE_M2
    assert reference.overlap_m2 <= CORE_AREA_TOLERANCE_M2
    assert abs(shoelace_area(coords) - Polygon(coords).area) <= CORE_AREA_TOLERANCE_M2


@pytest.mark.parametrize("name", sorted(CORE_FIXTURES))
def test_circulation_share_of_gross_floor_area_agrees(name: str):
    """The quantity a reader actually quotes: core as a fraction of gross plate + core."""
    coords, requested = CORE_FIXTURES[name]
    implemented = _implementation_core(coords, requested)
    reference = attach_external_core(coords, requested)
    plate = shoelace_area(coords)
    implemented_share = float(implemented.emitted_area_m2) / (plate + float(implemented.emitted_area_m2))
    reference_share = reference.area_m2 / (plate + reference.area_m2)
    assert abs(implemented_share - reference_share) <= 1e-9


def test_reference_core_refuses_a_non_rectangular_plate():
    """Both sides refuse the same input: a plate with no declared gross-to-conditioned relation."""
    trapezoid = [(0.0, 0.0), (40.0, 0.0), (34.0, 14.0), (6.0, 14.0)]
    declined = generate_external_unconditioned_core(
        Polygon(trapezoid), requested_area_m2=40.0
    )
    assert declined.fallback_reason == "NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED"
    with pytest.raises(ValueError, match="NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED"):
        attach_external_core(trapezoid, 40.0)


def test_reference_core_refuses_a_non_positive_area():
    coords, _ = CORE_FIXTURES["rect_30x12_core45"]
    with pytest.raises(ValueError):
        attach_external_core(coords, 0.0)


def test_convex_intersection_area_is_itself_exercised():
    """The overlap check would be vacuous if the intersection routine always returned zero."""
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    shifted = [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
    assert abs(convex_intersection_area(square, shifted) - 25.0) <= 1e-9
    assert convex_intersection_area(square, [(20.0, 20.0), (30.0, 20.0), (30.0, 30.0), (20.0, 30.0)]) == 0.0
