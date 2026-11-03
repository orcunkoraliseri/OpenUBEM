"""T03 wall-B measurement tests (PLAN_eu-recut-95pct-2026-09-08.md, director note:
this file and scripts/eu_wallb_measure_2026_09_08.py are the T03 executor's own
files, authorised so a second, concurrent executor never touches T01/T02/T04's
files). Unit tests for the new instrumentation, plus the plan's own T03
acceptance checks (row count 184, non-empty defect_on, histogram sums to 184)
against the measured ``wallB_defects.csv``.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from scripts.eu_wallb_measure_2026_09_08 import (
    OUT_DIR,
    _ring_area,
    classify_defect,
)

WALLB_CSV = OUT_DIR / "wallB_defects.csv"

VALID_DEFECT_ON = {"footprint_ring", "cut_edge", "interzone_pair"}
VALID_REFUSED_BY = {
    "chord_0.010m", "per_removal_1e-3", "cumulative_2e-3", "min_3_vertices", "not_on_ring",
}
VALID_DEFECT_KIND = {"near_duplicate", "collinear"}


def test_ring_area_unit_square():
    ring = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert _ring_area(ring) == pytest.approx(100.0)


def test_ring_area_zero_for_degenerate_line():
    ring = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    assert _ring_area(ring) == pytest.approx(0.0)


def test_classify_defect_not_on_any_ring_is_interzone_pair():
    from shapely.geometry import Polygon
    footprint = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    pre_rings = {"z1": [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]}
    post_rings = {"z1": [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]}
    defect = {"zone": "z1", "p1": (5.0, 5.0, 3.0), "defect_kind": "collinear", "min_edge_len_m": 0.001}
    defect_on, refused_by, perp, rel = classify_defect(defect, pre_rings, post_rings, footprint)
    assert (defect_on, refused_by) == ("interzone_pair", "not_on_ring")
    assert perp is None and rel is None


def test_classify_defect_on_footprint_boundary_vertex():
    from shapely.geometry import Polygon
    footprint = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    ring = [(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    defect = {"zone": "z1", "p1": (5.0, 0.0, 0.0), "defect_kind": "collinear", "min_edge_len_m": 5.0}
    defect_on, refused_by, perp, rel = classify_defect(defect, {"z1": ring}, {"z1": ring}, footprint)
    assert defect_on == "footprint_ring"
    assert refused_by in VALID_REFUSED_BY
    assert perp is not None and perp == pytest.approx(0.0, abs=1e-9)


def test_classify_defect_on_interior_cut_edge():
    from shapely.geometry import Polygon
    footprint = Polygon([(0, 0), (20, 0), (20, 10), (0, 10)])
    ring = [(10.0, 0.0), (10.0, 3.0), (10.0, 6.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    defect = {"zone": "z1", "p1": (10.0, 3.0, 0.0), "defect_kind": "near_duplicate", "min_edge_len_m": 0.0001}
    defect_on, refused_by, perp, rel = classify_defect(defect, {"z1": ring}, {"z1": ring}, footprint)
    assert defect_on == "cut_edge"
    assert refused_by in VALID_REFUSED_BY


def test_classify_defect_min_3_vertices():
    from shapely.geometry import Polygon
    footprint = Polygon([(0, 0), (20, 0), (20, 10), (0, 10)])
    ring = [(10.0, 3.0), (0.0, 0.0), (0.0, 10.0)]
    defect = {"zone": "z1", "p1": (10.0, 3.0, 0.0), "defect_kind": "near_duplicate", "min_edge_len_m": 0.0001}
    defect_on, refused_by, perp, rel = classify_defect(defect, {"z1": ring}, {"z1": ring}, footprint)
    assert refused_by == "min_3_vertices"


@pytest.mark.skipif(not WALLB_CSV.exists(), reason="wallB_defects.csv not yet measured")
class TestWallBMeasurement:
    @pytest.fixture(scope="class")
    def df(self):
        return pd.read_csv(WALLB_CSV)

    def test_row_count_is_184(self, df):
        assert len(df) == 184

    def test_every_row_has_nonempty_defect_on(self, df):
        assert df["defect_on"].notna().all()
        assert (df["defect_on"].astype(str).str.len() > 0).all()
        assert set(df["defect_on"].unique()) <= VALID_DEFECT_ON

    def test_defect_kind_and_refused_by_domains(self, df):
        assert set(df["defect_kind"].unique()) <= VALID_DEFECT_KIND
        assert set(df["refused_by"].unique()) <= VALID_REFUSED_BY

    def test_histogram_sums_to_184(self, df):
        hist = df.groupby(["defect_on", "refused_by"]).size()
        assert int(hist.sum()) == 184

    def test_stems_match_sha256_of_building_id(self, df):
        for _, row in df.iterrows():
            expected = hashlib.sha256(str(row["building_id"]).encode()).hexdigest()[:16]
            assert row["stem"] == expected

    def test_no_duplicate_building_ids(self, df):
        assert df["building_id"].duplicated().sum() == 0

    def test_district_population_matches_baseline(self, df):
        expected = {"Madrid": 67, "Lyon": 25, "London": 7, "Bologna": 85}
        counts = df["district"].value_counts().to_dict()
        assert counts == expected
