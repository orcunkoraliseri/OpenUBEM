from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from openubem.acquisition.boundary_clip import split_residential
from openubem.acquisition.footprint_schema import SCHEMA_COLUMNS, finalize_footprints

ROOT = Path(__file__).parent.parent.parent
FIX = Path(__file__).parent / "fixtures"
_spec = importlib.util.spec_from_file_location("acquire_budapest", ROOT / "scripts" / "eu22" / "acquire_budapest.py")
ab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ab)


@pytest.fixture(scope="module")
def built():
    feats = json.loads((FIX / "budapest_osm_buildings.json").read_text(encoding="utf-8"))["features"]
    raw = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    raw.index = pd.MultiIndex.from_arrays([raw["element_type"], raw["osmid"]], names=["element_type", "osmid"])
    raw = raw.drop(columns=["element_type", "osmid"])
    frame = ab.map_osm_frame(raw)
    return finalize_footprints(frame, source="OSM")


def _row(clean, i):
    return clean[clean.osm_id == f"way/{9000 + i}"].iloc[0]


def test_schema_and_crs(built):
    assert list(built.columns) == SCHEMA_COLUMNS
    assert built.crs.to_string() == "EPSG:32634"
    assert (built["crs_utm"] == "EPSG:32634").all()
    assert len(built) == 10


def test_levels_rules(built):
    assert _row(built, 0).levels == 4
    assert _row(built, 1).levels is pd.NA
    assert _row(built, 2).levels is pd.NA
    assert _row(built, 3).levels is pd.NA
    assert _row(built, 4).levels is pd.NA or _row(built, 4).levels == 0
    assert _row(built, 0).provenance_levels == "OSM_OBSERVED"
    assert _row(built, 1).provenance_levels == "OSM_MISSING"


def test_only_plain_year_is_observed(built):
    assert _row(built, 0).year_built == 1898
    assert _row(built, 5).year_built == 1960
    for i in (1, 2, 3):
        assert _row(built, i).year_built is pd.NA
        assert _row(built, i).provenance_year_built == "OSM_MISSING"
    assert _row(built, 0).provenance_year_built == "OSM_OBSERVED"


def test_plain_year_function():
    assert ab.plain_year("1898") == 1898
    assert ab.plain_year(" 1898 ") == 1898
    assert ab.plain_year("c1900") is None
    assert ab.plain_year("C19") is None
    assert ab.plain_year("1898-1900") is None
    assert ab.plain_year("1898-05-01") is None
    assert ab.plain_year("0999") is None
    assert ab.plain_year(None) is None
    assert ab.plain_year(float("nan")) is None


def test_height_tag_kept(built):
    assert _row(built, 5).height_m == 7.0
    assert _row(built, 5).provenance_height_m == "OSM_OBSERVED"


def test_residential_split_uses_project_crosswalk(built):
    res, exc, counts = split_residential(built, ab.residential_crosswalk(), class_column="building_tag")
    assert set(res.building_tag) == {"apartments", "house", "terrace", "detached"}
    assert counts["unknown"] == 1 and counts["non_residential"] == 1
    assert counts["residential"] == 8


def test_census_page_parse():
    page = (FIX / "budapest_ksh2011_vii_page.txt").read_text(encoding="utf-8")
    counts = ab.parse_census_page(page)
    assert list(counts) == [label for label, _, _ in ab.CENSUS_PERIODS]
    assert list(counts.values()) == [26529, 458, 473, 53, 202, 102, 726, 1001]
    assert sum(counts.values()) == 29544


def test_census_page_selection_ignores_xvii():
    page = "3.3.2.1 table\n 1946 előtt\n XVII. kerület\n"
    with pytest.raises(ValueError):
        ab.census_page_for(page)
    text = "3.3.2.1\n1946 előtt\nVII. kerület\f3.3.2.1\n1946 előtt\nXVII. kerület"
    assert "VII. kerület" in ab.census_page_for(text) and "XVII" not in ab.census_page_for(text)


def test_census_columns_attached(built):
    district = gpd.GeoSeries([box(*built.total_bounds)], crs=built.crs).iloc[0]
    counts = {"before 1946": 10, "1946-1960": 2}
    out = ab.attach_census(built, district, counts)
    assert (out["census_unit_id"] == "HU-BUD-VII").all()
    assert json.loads(out["census_period_counts"].iloc[0]) == counts
    far = gpd.GeoSeries([box(0, 0, 1, 1)], crs=built.crs).iloc[0]
    none = ab.attach_census(built, far, counts)
    assert (none["census_unit_id"] == "").all() and (none["census_period_counts"] == "").all()


def test_oldest_class_year_follows_hu01():
    assert ab.OLDEST_CLASS_YEAR == 1944
    assert ab.PERIOD_YEARS["before 1946"] == 1944
    table = json.loads((Path(__file__).parent / "fixtures" / "tabula_period_years_at_hu.json").read_text(encoding="utf-8"))
    oldest_end = max(end for _, code, start, end in table["HU"].values() if code == "HU.01")
    assert oldest_end == 1944 == ab.PERIOD_YEARS["before 1946"]
    assert ab.PERIOD_YEARS["1946-1960"] == 1953


def test_period_years():
    assert ab.PERIOD_YEARS["before 1946"] == 1944
    assert ab.PERIOD_YEARS["1946-1960"] == 1953
    assert ab.PERIOD_YEARS["2006-2011"] == 2008
    assert len(ab.PERIOD_YEARS) == 8


def test_relation_polygon_with_hole():
    payload = json.loads((FIX / "budapest_relation.json").read_text(encoding="utf-8"))
    poly = ab.relation_polygon(payload)
    assert poly.geom_type == "Polygon"
    assert len(poly.interiors) == 1
    assert poly.area == pytest.approx(0.02 * 0.02 - 0.004 * 0.004)


def test_select_units_range():
    assert ab.select_units(805)["mode"] == "whole_district"
    assert ab.select_units(805)["steps"][0]["running_total"] == 805
    assert ab.select_units(499)["mode"] == "out_of_range"
    assert ab.select_units(1001)["mode"] == "out_of_range"
    assert ab.select_units(500)["mode"] == "whole_district"
    assert ab.select_units(1000)["mode"] == "whole_district"
