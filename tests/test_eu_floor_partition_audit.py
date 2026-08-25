"""GEO-01/GEO-09 local partition-audit contracts for European dwellings."""
from __future__ import annotations

import pytest
from shapely import affinity
from shapely.geometry import Polygon, box

from openubem.geometry.european_residential import (
    assess_european_floor_layout_feasibility,
    audit_european_floor_partition,
)


def _clean_rectangle_partition():
    footprint = box(0.0, 0.0, 12.0, 8.0)
    dwellings = (
        box(0.0, 0.0, 6.0, 4.0),
        box(6.0, 0.0, 12.0, 4.0),
        box(0.0, 4.0, 6.0, 8.0),
        box(6.0, 4.0, 12.0, 8.0),
    )
    return footprint, dwellings


def test_geo01_axis_aligned_rectangle_independently_conserves_plate_and_count():
    footprint, dwellings = _clean_rectangle_partition()
    audit = audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=4)

    assert audit.passed
    assert audit.observed_dwelling_count == 4
    assert audit.union_area_m2 == pytest.approx(96.0)
    assert audit.gap_area_m2 == pytest.approx(0.0)
    assert audit.overlap_area_m2 == pytest.approx(0.0)
    assert audit.outside_area_m2 == pytest.approx(0.0)
    assert audit.area_error_fraction == pytest.approx(0.0)


def test_geo02_rotated_rectangle_preserves_the_partition_audit_outcome():
    footprint, dwellings = _clean_rectangle_partition()
    baseline = audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=4)

    rotated_footprint = affinity.rotate(footprint, 31.0, origin="centroid")
    rotated_dwellings = tuple(
        affinity.rotate(dwelling, 31.0, origin=footprint.centroid) for dwelling in dwellings
    )
    rotated = audit_european_floor_partition(
        rotated_footprint,
        rotated_dwellings,
        expected_dwelling_count=4,
    )

    assert baseline.passed and rotated.passed
    assert rotated.failures == baseline.failures
    assert rotated.observed_dwelling_count == baseline.observed_dwelling_count
    assert rotated.union_area_m2 == pytest.approx(baseline.union_area_m2)
    assert rotated.gap_area_m2 == pytest.approx(baseline.gap_area_m2, abs=1e-10)
    assert rotated.overlap_area_m2 == pytest.approx(baseline.overlap_area_m2, abs=1e-10)
    assert rotated.outside_area_m2 == pytest.approx(baseline.outside_area_m2, abs=1e-10)
    assert rotated.area_error_fraction == pytest.approx(baseline.area_error_fraction, abs=1e-12)


def test_geo03_l_shaped_footprint_accepts_a_valid_non_convex_partition():
    footprint = Polygon(((0.0, 0.0), (12.0, 0.0), (12.0, 4.0), (8.0, 4.0), (8.0, 8.0), (0.0, 8.0)))
    dwellings = (
        box(0.0, 0.0, 4.0, 4.0),
        box(4.0, 0.0, 8.0, 4.0),
        box(8.0, 0.0, 12.0, 4.0),
        box(0.0, 4.0, 4.0, 8.0),
        box(4.0, 4.0, 8.0, 8.0),
    )

    audit = audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=5)

    assert footprint.is_valid and not footprint.convex_hull.equals(footprint)
    assert all(dwelling.is_valid for dwelling in dwellings)
    assert audit.passed
    assert audit.union_area_m2 == pytest.approx(80.0)
    assert audit.gap_area_m2 == pytest.approx(0.0)
    assert audit.overlap_area_m2 == pytest.approx(0.0)
    assert audit.outside_area_m2 == pytest.approx(0.0)


def test_geo05_courtyard_hole_is_preserved_and_a_crossing_dwelling_fails():
    footprint = Polygon(
        shell=((0.0, 0.0), (12.0, 0.0), (12.0, 12.0), (0.0, 12.0)),
        holes=(((4.0, 4.0), (8.0, 4.0), (8.0, 8.0), (4.0, 8.0)),),
    )
    dwellings = (
        box(0.0, 0.0, 4.0, 12.0),
        box(8.0, 0.0, 12.0, 12.0),
        box(4.0, 0.0, 8.0, 4.0),
        box(4.0, 8.0, 8.0, 12.0),
    )

    audit = audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=4)
    crossing = audit_european_floor_partition(
        footprint,
        (*dwellings[:2], box(4.0, 0.0, 8.0, 8.0), dwellings[3]),
        expected_dwelling_count=4,
    )

    assert footprint.interiors and audit.passed
    assert audit.union_area_m2 == pytest.approx(128.0)
    assert audit.gap_area_m2 == pytest.approx(0.0)
    assert audit.outside_area_m2 == pytest.approx(0.0)
    assert not crossing.passed
    assert "OUTSIDE_FOOTPRINT" in crossing.failures


def test_geo04_narrow_footprint_has_a_stable_fail_closed_fallback_token():
    narrow = box(0.0, 0.0, 30.0, 7.99)
    at_threshold = box(0.0, 0.0, 30.0, 8.0)

    narrow_decision = assess_european_floor_layout_feasibility(
        narrow, requested_dwelling_count=4
    )
    threshold_decision = assess_european_floor_layout_feasibility(
        at_threshold, requested_dwelling_count=4
    )

    assert narrow_decision.minimum_width_m == pytest.approx(7.99)
    assert narrow_decision.fallback_required
    assert narrow_decision.status == "FALLBACK_ONE_ZONE_PER_FLOOR"
    assert narrow_decision.fallback_reason == "NARROW_FOOTPRINT_LT_8M"
    assert not narrow_decision.dwelling_layout_emitted

    assert threshold_decision.minimum_width_m == pytest.approx(8.0)
    assert not threshold_decision.fallback_required
    assert threshold_decision.status == "DWELLING_LAYOUT_REQUIRED"
    assert threshold_decision.fallback_reason is None
    # Passing the width gate is not a claim that a dwelling layout exists.
    assert not threshold_decision.dwelling_layout_emitted


@pytest.mark.parametrize(
    ("width_m", "fallback_required"),
    [(6.0, True), (7.99, True), (8.0, False), (9.0, False)],
)
def test_geo04_width_sweep_is_stable_at_the_registered_threshold(
    width_m: float, fallback_required: bool
):
    decision = assess_european_floor_layout_feasibility(
        box(0.0, 0.0, 30.0, width_m), requested_dwelling_count=2
    )

    assert decision.minimum_width_m == pytest.approx(width_m)
    assert decision.fallback_required is fallback_required
    assert decision.fallback_reason == (
        "NARROW_FOOTPRINT_LT_8M" if fallback_required else None
    )


def test_geo04_narrow_fallback_is_orientation_invariant():
    narrow = box(0.0, 0.0, 30.0, 7.5)
    rotated = affinity.rotate(narrow, 37.0, origin="centroid")

    baseline = assess_european_floor_layout_feasibility(
        narrow, requested_dwelling_count=3
    )
    rotated_decision = assess_european_floor_layout_feasibility(
        rotated, requested_dwelling_count=3
    )

    assert rotated_decision.minimum_width_m == pytest.approx(baseline.minimum_width_m)
    assert rotated_decision.fallback_required == baseline.fallback_required
    assert rotated_decision.fallback_reason == baseline.fallback_reason


def test_geo04_feasibility_rejects_invalid_footprint_and_requested_count():
    with pytest.raises(ValueError, match="requested_dwelling_count"):
        assess_european_floor_layout_feasibility(box(0.0, 0.0, 30.0, 7.0), requested_dwelling_count=0)
    with pytest.raises(ValueError, match="requested_dwelling_count"):
        assess_european_floor_layout_feasibility(box(0.0, 0.0, 30.0, 7.0), requested_dwelling_count=1.5)
    with pytest.raises(ValueError, match="footprint"):
        assess_european_floor_layout_feasibility(box(0.0, 0.0, 0.0, 7.0), requested_dwelling_count=1)


@pytest.mark.parametrize(
    ("mutation", "expected_failure"),
    [
        ("gap", "AREA_GAP"),
        ("overlap", "AREA_OVERLAP"),
        ("outside", "OUTSIDE_FOOTPRINT"),
        ("count", "DWELLING_COUNT"),
    ],
)
def test_geo09_partition_mutations_fail_their_named_gate(mutation: str, expected_failure: str):
    footprint, dwellings = _clean_rectangle_partition()
    if mutation == "gap":
        dwellings = dwellings[:-1]
    elif mutation == "overlap":
        dwellings = (*dwellings[:3], box(5.0, 4.0, 12.0, 8.0))
    elif mutation == "outside":
        dwellings = (*dwellings[:3], box(6.0, 4.0, 13.0, 8.0))
    elif mutation == "count":
        dwellings = dwellings[:3]

    audit = audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=4)
    assert not audit.passed
    assert expected_failure in audit.failures


def test_partition_auditor_rejects_invalid_contract_inputs():
    footprint, dwellings = _clean_rectangle_partition()
    with pytest.raises(ValueError, match="expected_dwelling_count"):
        audit_european_floor_partition(footprint, dwellings, expected_dwelling_count=0)
    with pytest.raises(ValueError, match="footprint"):
        audit_european_floor_partition(box(0.0, 0.0, 0.0, 1.0), dwellings, expected_dwelling_count=4)
