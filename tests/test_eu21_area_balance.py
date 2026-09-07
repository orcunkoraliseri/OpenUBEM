"""D-EU-107 (`FINDING 244`, plan `eu-plan-homogeneity-2026-09-07`, T02) unit
tests for the C12 area-balance gate and its two cut repairs. Imports (never
copies) `scripts/eu21/07_nocore_tests.py`, same dynamic-load pattern that
module's own siblings (`08_district_viewer.py`, `10_engine_census.py`) use.
"""
from __future__ import annotations

import importlib.util as ilu
import pathlib

import pytest
from shapely.geometry import Polygon, box

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_m07():
    spec = ilu.spec_from_file_location(
        "eu21_m07_area_balance_test", str(ROOT / "scripts" / "eu21" / "07_nocore_tests.py")
    )
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def m07():
    return _load_m07()


def test_c12_exempt_at_k_le_1(m07):
    poly = box(0, 0, 10, 6)
    rec = {"drawn_per_floor": 1}
    m07.run_checks(rec, [poly], poly)
    assert rec["checks"]["C12"]["pass"] is True
    assert "k=1" in rec["checks"]["C12"]["show"]


def test_c12_gate_threshold(m07):
    poly = box(0, 0, 20, 6)
    a = box(0, 0, 15, 6)
    b = box(15, 0, 20, 6)
    rec = {"drawn_per_floor": 2}
    m07.run_checks(rec, [a, b], poly)
    assert rec["spread"] == pytest.approx(30.0 / 90.0, abs=1e-4)
    assert rec["checks"]["C12"]["pass"] is False

    a2 = box(0, 0, 11, 6)
    b2 = box(11, 0, 20, 6)
    rec2 = {"drawn_per_floor": 2}
    m07.run_checks(rec2, [a2, b2], poly)
    assert rec2["spread"] >= m07.MIN_SPREAD
    assert rec2["checks"]["C12"]["pass"] is True


def test_wingwise_two_wing_plate_allocates_2_and_2(m07):
    left = box(0, 0, 10, 10)
    right = box(30, 0, 40, 10)
    neck = box(10, 4.5, 30, 5.5)
    poly = left.union(right).union(neck)
    result = m07.cut_wingwise(poly, 4)
    assert result is not None
    poly_out, flats, stuck = result
    live = [f for f in flats if not f.is_empty]
    assert len(live) == 4
    xs_left = [f.centroid.x for f in live if f.centroid.x < 20]
    xs_right = [f.centroid.x for f in live if f.centroid.x >= 20]
    assert len(xs_left) == 2
    assert len(xs_right) == 2


def test_bounded_split_shrinks_a_large_leftover(m07):
    flat = box(0, 0, 6, 10)
    piece = box(6, 0, 30, 10)
    near, far = m07._bounded_split_piece(piece, 0.5 * flat.area, flat)
    assert near is not None and far is not None
    assert near.area == pytest.approx(0.5 * flat.area, rel=0.05)
    assert near.area < piece.area
    assert far.area > 0.0
    assert near.area + far.area == pytest.approx(piece.area, rel=1e-6)


def test_donate_leftovers_bounds_an_oversized_piece(m07):
    p = box(0, 0, 4, 10)
    plate = box(0, 0, 4, 100)
    flats, stuck = m07.donate_leftovers(plate, [p])
    assert not stuck
    covered_area = sum(f.area for f in flats if not f.is_empty)
    assert covered_area == pytest.approx(plate.area, rel=1e-6)


def test_no_balanced_split_falls_back_and_reports_c12_fail(m07):
    seed_a = box(0, 0, 1.0, 100)
    seed_b = box(29, 0, 30, 100)
    plate = box(0, 0, 30, 100)
    flats, stuck = m07.donate_leftovers(plate, [seed_a, seed_b])
    assert not stuck
    live = [f for f in flats if not f.is_empty]
    covered = sum(f.area for f in live)
    assert covered == pytest.approx(plate.area, rel=1e-6)
    rec = {"drawn_per_floor": 2}
    m07.run_checks(rec, live, plate)
    assert rec["checks"]["C12"]["pass"] is False
    assert rec["verdict"] in ("PASS", "FAIL")
