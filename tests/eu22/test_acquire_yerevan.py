from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
_spec = importlib.util.spec_from_file_location("acquire_yerevan", ROOT / "scripts" / "eu22" / "acquire_yerevan.py")
ay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ay)

REAL_TABLES = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / "AM-EVN-NORNORK" / "armstat_tables.csv"


def dominant(counts: dict[str, int]) -> str:
    return max(counts, key=counts.get)


def test_residential_rule_per_route():
    assert ay.classify_use("apartments", "", False) == ("residential", "osm_residential_tag")
    assert ay.classify_use("house", "", False) == ("residential", "osm_residential_tag")
    assert ay.classify_use("semidetached_house", None, False) == ("residential", "osm_residential_tag")
    assert ay.classify_use("yes", "", True) == ("residential", "untagged_in_landuse_residential")
    assert ay.classify_use("yes", "", False) == ("unknown", "untagged_outside_landuse_residential")
    assert ay.classify_use("yes", "supermarket", True)[0] == "non_residential"
    assert ay.classify_use("garages", "", True)[0] == "non_residential"
    assert ay.classify_use("retail", "", True)[0] == "non_residential"


def test_storey_band_edges():
    assert [ay.storey_band(v) for v in (1, 2, 3, 4, 5, 6, 8, 9, 20)] == ["1", "2", "3", "4", "5", "6-8", "6-8", "9+", "9+"]
    assert ay.storey_band(pd.NA) is None
    assert ay.storey_band(float("nan")) is None
    assert ay.storey_band(0) is None


def test_storey_band_to_period_lookup_on_three_row_table():
    rows = ay.read_armstat_tables(FIXTURES / "yerevan_armstat_crossed.csv")
    c3, s3 = ay.period_counts(rows, "Test Unit", "3")
    c5, s5 = ay.period_counts(rows, "Test Unit", "5")
    c9, s9 = ay.period_counts(rows, "Test Unit", "9+")
    assert (s3, s5, s9) == ("storey_band", "storey_band", "storey_band")
    assert [dominant(c3), dominant(c5), dominant(c9)] == ["1951-1970", "1971-1980", "1981-1990"]
    c4, s4 = ay.period_counts(rows, "Test Unit", "4")
    assert s4 == "district" and dominant(c4) == "1951-1970"
    assert sum(c4.values()) == 20
    cn, sn = ay.period_counts(rows, "Test Unit", None)
    assert sn == "district" and cn == c4


def test_period_counts_fall_back_to_district_when_no_crossed_table():
    rows = ay.read_armstat_tables(REAL_TABLES)
    counts, scope = ay.period_counts(rows, ay.CENSUS_UNIT_ROW, "5")
    assert scope == "district"
    assert counts == {"up to 1950": 0, "1951-1970": 268, "1971-1980": 189, "1981-1990": 164, "1991-2000": 32, "2001-2010": 2, "2011+": 2}
    assert dominant(counts) == "1951-1970"


def test_private_house_without_period_source_is_excluded_with_reason():
    frame = gpd.GeoDataFrame(
        {
            "osm_id": ["a", "b", "c", "d", "e"],
            "building_tag": ["apartments", "house", "yes", "yes", "detached"],
            "levels": pd.array([5, 1, 2, pd.NA, pd.NA], dtype="Int64"),
            "use_class": ["residential"] * 5,
        },
        geometry=[Polygon([(0, 0), (1, 0), (1, 1)])] * 5,
        crs="EPSG:32638",
    )
    rows = ay.read_armstat_tables(FIXTURES / "yerevan_armstat_crossed.csv")
    out = ay.attach_period_source(frame, rows, "Test Unit")
    assert out["period_exclusion_reason"].tolist() == ["", ay.NO_PERIOD_PRIVATE, ay.NO_PERIOD_PRIVATE, "", ay.NO_PERIOD_PRIVATE]
    assert out["census_period_counts"].tolist()[1] == ""
    assert json.loads(out["census_period_counts"].iloc[0])["1971-1980"] == 4
    assert out["census_unit_id"].eq(ay.SITE).all()
    assert out["period_scope"].tolist() == ["storey_band", "", "", "district", ""]
    out.loc[out["period_exclusion_reason"] == ay.NO_PERIOD_PRIVATE, "use_class"] = "non_residential"
    from openubem.acquisition.boundary_clip import split_residential

    residential, excluded, counts = split_residential(out, ay.CROSSWALK, class_column="use_class")
    assert counts["residential"] == 2 and counts["non_residential"] == 3
    assert set(residential["osm_id"]) == {"a", "d"}


def test_osm_fixture_route_gives_utm_38n_and_classes():
    from openubem.acquisition.osm_fetcher import ingest_buildings

    gdf = ingest_buildings(osm_path=FIXTURES / "yerevan_osm_buildings.osm")
    assert gdf.crs.to_string() == ay.EXPECTED_CRS
    assert len(gdf) == 4
    classes = {r.osm_id: ay.classify_use(r.building_tag, r.function_tag, False)[0] for r in gdf.itertuples()}
    assert sorted(classes.values()) == ["non_residential", "residential", "residential", "unknown"]
    apartments = gdf[gdf["building_tag"] == "apartments"].iloc[0]
    assert int(apartments["levels"]) == 5


def test_transcribed_table_totals_equal_pdf_totals():
    rows = ay.read_armstat_tables(REAL_TABLES)

    def total(table, unit, categories=None, band=None):
        sel = [r for r in rows if r["table_id"] == table and r["district_row"] == unit and (band is None or r["storey_band"] == band)]
        if categories is not None:
            sel = [r for r in sel if r["category"] in categories]
        return sum(r["count"] for r in sel)

    assert total("period_by_district", "Nor Nork") == 657 == total("period_total", "Nor Nork", {"all"})
    assert total("period_by_district", "Yerevan total") == 4721 == total("period_total", "Yerevan total", {"all"})
    assert total("material_by_district", "Nor Nork", {"stone", "panel", "monolithic"}) == 657
    assert total("material_by_district", "Nor Nork", {"pitched roof", "flat roof"}) == 657
    assert total("material_by_district", "Yerevan total", {"stone", "panel", "monolithic"}) == 4721
    assert total("period_by_district_district_managed", "Nor Nork") == 8
    bands = ["1", "2", "3", "4", "5", "6-8", "9+"]
    per_band = [total("storeys_by_material", "Nor Nork", {"all"}, band=b) for b in bands]
    assert sum(per_band) == 657
    for b in bands:
        assert total("storeys_by_material", "Nor Nork", {"stone", "panel", "monolithic"}, band=b) == total("storeys_by_material", "Nor Nork", {"all"}, band=b)
    assert sum(total("storeys_by_material", "Nor Nork", {"stone"}, band=b) for b in bands) == 205
    assert sum(total("storeys_by_material", "Nor Nork", {"panel"}, band=b) for b in bands) == 439
    assert sum(total("storeys_by_material", "Nor Nork", {"monolithic"}, band=b) for b in bands) == 13
    assert all(r["pdf_page"].isdigit() and r["printed_page"].isdigit() for r in rows)


def test_period_years_follow_midpoint_convention():
    assert ay.PERIOD_YEARS["1951-1970"] == 1960
    assert set(ay.PERIOD_YEARS) == set(ay.PERIOD_LABELS)


def test_boundary_polygon_from_relation_members():
    ring = [(44.0, 40.0), (44.1, 40.0), (44.1, 40.1), (44.0, 40.1), (44.0, 40.0)]
    element = {
        "members": [
            {"type": "way", "role": "outer", "geometry": [{"lon": a, "lat": b} for a, b in ring[:3]]},
            {"type": "way", "role": "outer", "geometry": [{"lon": a, "lat": b} for a, b in ring[2:]]},
            {"type": "way", "role": "inner", "geometry": [{"lon": 0, "lat": 0}, {"lon": 1, "lat": 1}]},
        ]
    }
    polygon = ay.boundary_polygon(element)
    assert polygon.bounds == pytest.approx((44.0, 40.0, 44.1, 40.1))


def test_overpass_logs_real_error_text_and_rotates_endpoints(capsys):
    class Resp:
        def __init__(self, status, body):
            self.status_code, self.content = status, body

    calls = []

    class Session:
        def post(self, url, data=None, headers=None, timeout=None):
            calls.append(url)
            if len(calls) == 1:
                return Resp(200, b"<html>runtime error: rate_limited</html>")
            if len(calls) == 2:
                return Resp(504, b"gateway timeout")
            return Resp(200, b'{"elements": []}')

    out = ay.overpass("q", endpoints=["https://a", "https://b", "https://c"], session=Session(), sleep=lambda s: None)
    assert out == b'{"elements": []}'
    assert calls == ["https://a", "https://b", "https://c"]
    err = capsys.readouterr().err
    assert "rate_limited" in err and "HTTP 504 gateway timeout" in err


def test_overpass_raises_with_last_error_when_all_fail():
    class Resp:
        status_code, content = 500, b"boom"

    class Session:
        def post(self, *a, **k):
            return Resp()

    with pytest.raises(RuntimeError, match="HTTP 500 boom"):
        ay.overpass("q", rounds=2, endpoints=["https://a"], session=Session(), sleep=lambda s: None)
