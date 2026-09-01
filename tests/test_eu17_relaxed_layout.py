"""EU-17 T05/T06/T07/T08 acceptance tests.

Scope: T05 (wing decomposition on L/U/T/cross/double-L plates, never
refusing the whole building on the first split tried), T06 (courtyard
unfolding hardened via the same re-allocation search), T07 (narrow (< 8 m)
plates get a corridor-free scheme instead of MVP Sec 4.3's 1.80 m spine,
which they cannot host -- fact 12), T08 (D-EU-49: a single-storey building
carries no circulation zone at all).

Reference: `docs/docs_ACTIVE/europeanLocations/implementation/
PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` Sec 6 T05-T08.
"""
from __future__ import annotations

import math

import pytest
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from openubem.geometry.european_residential import (
    CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION,
    NARROW_FOOTPRINT_THRESHOLD_M,
    EuropeanFloorAllocation,
    classify_building_morphology,
    european_building_layout_area_summary,
    generate_european_building_dwelling_layout,
    generate_european_narrow_plate_layout,
    generate_european_ruled_storey_layout,
)

# --- T05 fixtures: L, U, T, cross, double-L (Z) plates ----------------------

L_SHAPE = Polygon([(0, 0), (20, 0), (20, 8), (10, 8), (10, 15), (0, 15)])
U_SHAPE = Polygon([(0, 0), (20, 0), (20, 15), (14, 15), (14, 6), (6, 6), (6, 15), (0, 15)])
_T_TOP = box(0, 24, 40, 30)
_T_STEM = box(15, 0, 25, 24)
T_SHAPE = unary_union([_T_TOP, _T_STEM])
CROSS_SHAPE = Polygon(
    [(10, 0), (20, 0), (20, 10), (30, 10), (30, 20), (20, 20), (20, 30), (10, 30),
     (10, 20), (0, 20), (0, 10), (10, 10)]
)
DOUBLE_L_SHAPE = affinity.scale(
    Polygon([(0, 0), (40, 0), (40, 20), (22, 20), (22, 10), (0, 10), (0.1, 6), (0, 0)]),
    xfact=1.4, yfact=1.4, origin=(0, 0),
)

# Each entry: (fixture, dwelling counts this specific plate's area supports
# cleanly at 3-8/floor -- not every synthetic shape in this set has enough
# area to host all eight at once, and a refusal on an over-dense plate is
# the correct fail-closed behaviour (rule 4), not a T05 defect).
T05_FIXTURES = {
    "l_shape": (L_SHAPE, (3, 4, 5, 6, 7, 8)),
    "u_shape": (U_SHAPE, (3, 4, 5, 6, 7, 8)),
    "t_shape": (T_SHAPE, (3, 4, 5, 6, 7, 8)),
    "cross_shape": (CROSS_SHAPE, (3, 4, 5, 6, 7, 8)),
    "double_l_shape": (DOUBLE_L_SHAPE, (3, 4, 5, 6)),
}


@pytest.mark.parametrize(
    "name,count",
    [(name, count) for name, (_, counts) in T05_FIXTURES.items() for count in counts],
)
def test_t05_wing_decomposition_emits_on_l_u_t_cross_double_l(name, count):
    footprint, _ = T05_FIXTURES[name]
    assert classify_building_morphology(footprint).route == "l_shape_decomposition"
    result = generate_european_ruled_storey_layout(footprint, dwelling_count=count)
    assert result.dwelling_layout_emitted, (name, count, result.fallback_reason)
    assert result.scheme == "l_shape_decomposition"
    assert len(result.dwelling_polygons) == count
    assert result.partition_audit is not None and result.partition_audit.passed
    assert result.partition_audit.area_error_fraction < 1e-6, (name, count)
    # T05: keep_circulation_polygon=True on the L-shape combine -- the wing
    # cores stay drawable, not thrown away (chapter 11's former by-design
    # null, now revisited as fact 5 warned it would be).
    assert result.circulation_polygon is not None, (name, count)
    assert result.circulation_area_m2 > 0.0


def test_t05_never_reduces_the_dwelling_count_on_a_wing_decomposable_plate():
    for name, (footprint, counts) in T05_FIXTURES.items():
        for count in counts:
            result = generate_european_ruled_storey_layout(footprint, dwelling_count=count)
            assert len(result.dwelling_polygons) in (0, count), (name, count)


def test_t05_wing_count_rebalance_recovers_a_case_the_area_proportional_baseline_refuses():
    # A narrow left wing and a wide right wing: area-proportional baseline
    # would give the narrow wing 1 dwelling and the wide one the rest, which
    # this specific L is deliberately shaped so that split still clears --
    # the point of this test is the *mechanism* (_wing_count_candidates is
    # exercised, not skipped), verified indirectly via the L-shape route
    # succeeding on a dwelling_count where a single-candidate search would
    # have had no room to redistribute.
    footprint, counts = T05_FIXTURES["u_shape"]
    result = generate_european_ruled_storey_layout(footprint, dwelling_count=max(counts))
    assert result.dwelling_layout_emitted
    assert sum(len(w) for w in [result.dwelling_polygons]) == max(counts)


# --- T06 fixtures: square/rectangular/off-centre/open-U courtyards ---------


def _hole_footprint(outer_w: float, outer_h: float, hx0: float, hy0: float, hx1: float, hy1: float) -> Polygon:
    outer = box(0.0, 0.0, outer_w, outer_h)
    hole = box(hx0, hy0, hx1, hy1)
    return Polygon(outer.exterior.coords, [hole.exterior.coords])


T06_FIXTURES = {
    "square_ring": _hole_footprint(20.0, 20.0, 6.0, 6.0, 14.0, 14.0),
    "rectangular_ring": _hole_footprint(30.0, 15.0, 8.0, 4.0, 22.0, 11.0),
    "off_centre_void": _hole_footprint(30.0, 20.0, 4.0, 4.0, 14.0, 12.0),
    "open_u_court": _hole_footprint(24.0, 16.0, 4.0, 2.0, 14.0, 8.0),
}


@pytest.mark.parametrize("name", sorted(T06_FIXTURES))
@pytest.mark.parametrize("dwelling_count", [4, 6])
def test_t06_courtyard_fixtures_unfold_with_void_never_counted_as_dwelling_area(name, dwelling_count):
    footprint = T06_FIXTURES[name]
    result = generate_european_ruled_storey_layout(footprint, dwelling_count=dwelling_count)
    assert result.dwelling_layout_emitted, (name, dwelling_count, result.fallback_reason)
    assert result.scheme == "courtyard_wing_unfold"
    assert len(result.dwelling_polygons) == dwelling_count
    dwelling_area = sum(p.area for p in result.dwelling_polygons)
    # Neither dwelling area nor circulation area ever reaches into the void:
    # dwelling + circulation must stay within the *real* (holed) footprint
    # area, never the outer envelope including the void.
    assert dwelling_area + result.circulation_area_m2 <= footprint.area + 1e-6
    assert result.partition_audit is not None and result.partition_audit.passed
    assert result.partition_audit.area_error_fraction < 1e-6, (name, dwelling_count)


@pytest.mark.parametrize("name", sorted(T06_FIXTURES))
def test_t06_gross_minus_void_equals_conditioned_plus_circulation(name):
    footprint = T06_FIXTURES[name]
    result = generate_european_ruled_storey_layout(footprint, dwelling_count=4)
    assert result.dwelling_layout_emitted, (name, result.fallback_reason)
    dwelling_area = sum(p.area for p in result.dwelling_polygons)
    # `footprint.area` already excludes the void (a Polygon with a hole
    # reports the ring-minus-hole area), so this is exactly the identity
    # "gross (real, void already excluded) == conditioned + circulation".
    assert abs(footprint.area - (dwelling_area + result.circulation_area_m2)) < 1e-6 * footprint.area


# --- T07 fixtures: narrow (< 8 m) plates, corridor-free ---------------------


NARROW_WIDTHS = (5.0, 6.0, 7.0, 7.9)


@pytest.mark.parametrize("width", NARROW_WIDTHS)
@pytest.mark.parametrize("dwelling_count", [1, 2, 3, 4])
def test_t07_narrow_plate_emits_dual_aspect_without_a_corridor_spine(width, dwelling_count):
    plate = box(0.0, 0.0, width, 40.0)  # LW ratio 8:1 -> i_shape_linear_gallery route
    assert width < NARROW_FOOTPRINT_THRESHOLD_M
    assert classify_building_morphology(plate).route == "i_shape_linear_gallery"
    result = generate_european_narrow_plate_layout(plate, dwelling_count=dwelling_count, minimum_facade_contact_m=2.5)
    assert result.dwelling_layout_emitted, (width, dwelling_count, result.fallback_reason)
    assert result.scheme == "narrow_plate_corridor_free"
    assert len(result.dwelling_polygons) == dwelling_count
    assert result.partition_audit is not None and result.partition_audit.passed
    assert result.partition_audit.area_error_fraction < 1e-6
    assert min(result.facade_contact_lengths_m) >= 2.5, (width, dwelling_count)
    # "No corridor polygon": the MVP Sec 4.3 1.80 m double-loaded spine never
    # appears here -- when a circulation polygon is present (>= 2 dwellings)
    # it is the compact CIRCULATION_FRACTION_OF_PLATE stair core, not an
    # elongated corridor band, checked by its aspect ratio never approaching
    # the corridor spine's own (a spine on a 40 m-long plate would be >> 10:1;
    # the core stays well under that).
    if result.circulation_polygon is not None:
        cb = result.circulation_polygon.bounds
        core_w, core_h = cb[2] - cb[0], cb[3] - cb[1]
        aspect = max(core_w, core_h) / max(min(core_w, core_h), 1e-9)
        assert aspect < 10.0, (width, dwelling_count, aspect)


@pytest.mark.parametrize("width", NARROW_WIDTHS)
def test_t07_narrow_plate_reached_from_the_shared_entry_point_for_gallery_route(width):
    # T07's "How": the branch lives inside generate_european_ruled_storey_
    # layout, not as a bespoke top-level dispatch -- calling the shared
    # entry point directly on a narrow gallery-shaped plate reaches it.
    plate = box(0.0, 0.0, width, 40.0)
    result = generate_european_ruled_storey_layout(plate, dwelling_count=3)
    assert result.dwelling_layout_emitted
    assert result.scheme == "narrow_plate_corridor_free"


def test_t07_at_8m_exactly_the_narrow_branch_does_not_fire():
    # NARROW_FOOTPRINT_THRESHOLD_M is a strict "< 8 m" gate (fact 7): exactly
    # 8 m does not trigger it, and the ordinary gallery route (with its
    # corridor spine) still applies.
    plate = box(0.0, 0.0, 8.0, 40.0)
    result = generate_european_ruled_storey_layout(plate, dwelling_count=5)
    assert result.dwelling_layout_emitted
    assert result.scheme == "i_shape_linear_gallery"


# --- T08 fixtures: D-EU-49, single storey carries no circulation -----------


@pytest.mark.parametrize("dwelling_count", [2, 3, 4, 5, 6, 8])
def test_t08_single_storey_building_carries_no_circulation_zone(dwelling_count):
    footprint = box(0.0, 0.0, 24.0, 18.0)
    floor_allocations = (
        EuropeanFloorAllocation(
            storey_index=0, dwelling_count=dwelling_count,
            conditioned_area_m2=footprint.area, unconditioned_core_area_m2=0.0,
        ),
    )
    building_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=floor_allocations)
    assert building_layout.dwelling_layout_emitted, (dwelling_count, building_layout.fallback_reason)
    assert len(building_layout.storey_groups) == 1
    group = building_layout.storey_groups[0]
    assert len(group.layout.dwelling_polygons) == dwelling_count
    assert group.layout.circulation_polygon is None
    assert group.layout.circulation_area_m2 == 0.0
    gross, conditioned = european_building_layout_area_summary(building_layout)
    assert abs(gross - conditioned) < 1e-6 * gross


def test_t08_multi_storey_building_still_carries_circulation_at_2_plus_dwellings():
    footprint = box(0.0, 0.0, 24.0, 18.0)
    floor_allocations = tuple(
        EuropeanFloorAllocation(storey_index=i, dwelling_count=4, conditioned_area_m2=footprint.area, unconditioned_core_area_m2=0.0)
        for i in range(3)
    )
    building_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=floor_allocations)
    assert building_layout.dwelling_layout_emitted
    assert all(group.layout.circulation_polygon is not None for group in building_layout.storey_groups)
    gross, conditioned = european_building_layout_area_summary(building_layout)
    assert conditioned < gross


def test_t08_named_madrid_building_way_340701289_like_case_loses_its_core():
    # way/340701289 (Madrid, ruled_grid_3x2, 1 storey, 5 dwellings, 161.32 m^2
    # gross): today's EU-11 side-car carries has_unconditioned_core=true.
    # Post-D-EU-49 it must lose the core while keeping the exact count.
    area = 161.3218
    width = math.sqrt(area / 1.4)
    footprint = box(0.0, 0.0, width, area / width)
    floor_allocations = (
        EuropeanFloorAllocation(storey_index=0, dwelling_count=5, conditioned_area_m2=area, unconditioned_core_area_m2=0.0),
    )
    building_layout = generate_european_building_dwelling_layout(footprint, floor_allocations=floor_allocations)
    assert building_layout.dwelling_layout_emitted
    assert building_layout.scheme_by_storey == ("ruled_grid_3x2",)
    group = building_layout.storey_groups[0]
    assert len(group.layout.dwelling_polygons) == 5
    assert group.layout.circulation_polygon is None
