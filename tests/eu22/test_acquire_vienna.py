from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"

_spec = importlib.util.spec_from_file_location("acquire_vienna", ROOT / "scripts" / "eu22" / "acquire_vienna.py")
av = importlib.util.module_from_spec(_spec)
sys.modules["acquire_vienna"] = av
_spec.loader.exec_module(av)


def _raw(name: str) -> dict:
    return json.loads((FIXTURES / f"vienna_{name}.json").read_text(encoding="utf-8"))


def _fixture_frames():
    return (av.read_collection(_raw("fmzkgeb")), av.read_collection(_raw("bkm")), av.read_collection(_raw("info")))


def _info(rows: list[dict], x: float = 5.0, y: float = 5.0) -> gpd.GeoDataFrame:
    base = {"GESCH_ANZ": 0, "BAUJAHR": None, "L_BAUJ": None, "L_NUTZUNG": "Wohnnutzung"}
    data = [{**base, **row} for row in rows]
    return gpd.GeoDataFrame(data, geometry=[Point(x + i * 0.5, y) for i in range(len(data))], crs=av.UTM_CRS)


def _geb(boxes: list[tuple[int, tuple[float, float, float, float]]]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame({"BW_GEB_ID": [b[0] for b in boxes]}, geometry=[box(*b[1]) for b in boxes], crs=av.UTM_CRS)


def _bkm(rows: list[tuple[int, float, float, tuple[float, float, float, float]]]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"BW_GEB_ID": [r[0] for r in rows], "O_KOTE": [r[1] for r in rows], "HOEHE_DGM": [r[2] for r in rows]},
        geometry=[box(*r[3]) for r in rows], crs=av.UTM_CRS,
    )


def test_schema_and_census_columns():
    geb, bkm, info = _fixture_frames()
    frame, stats = av.build_rows(geb, bkm, info)
    out = av.finalize_vienna(frame)
    assert list(out.columns) == av.SCHEMA_COLUMNS and len(out.columns) == 23
    units = gpd.GeoDataFrame({"ZBEZ": ["1501"]}, geometry=[out.geometry.union_all().envelope.buffer(100)], crs=out.crs)
    census = {"1501": {label: 1 for label in av.PERIOD_YEARS}}
    full = av.attach_census(out, units, census)
    assert list(full.columns) == av.SCHEMA_COLUMNS + av.CENSUS_COLUMNS
    assert (full["census_unit_id"] == "1501").all()
    assert set(json.loads(full["census_period_counts"].iloc[0])) == set(av.PERIOD_YEARS)
    assert stats["geb_polygons"] == 20 and stats["footprint_parts"] < 20


def test_height_is_body_top_minus_terrain_and_building_takes_largest_body():
    geb, bkm, info = _fixture_frames()
    frame, _ = av.build_rows(geb, bkm, info)
    raw = _raw("bkm")["features"]
    target = next(i for i in {f["properties"]["BW_GEB_ID"] for f in raw}
                  if sum(1 for f in raw if f["properties"]["BW_GEB_ID"] == i) >= 1)
    expected = max(f["properties"]["O_KOTE"] - f["properties"]["HOEHE_DGM"] for f in raw
                   if f["properties"]["BW_GEB_ID"] == target and f["properties"]["O_KOTE"] is not None)
    row = frame[frame["osm_id"].str.startswith(f"AT-VIE-{target}")].iloc[0]
    assert row["height_m"] == pytest.approx(expected, abs=1e-6)
    geb2 = _geb([(1, (0, 0, 10, 10))])
    bkm2 = _bkm([(1, 105.0, 100.0, (0, 0, 5, 10)), (1, 109.0, 100.0, (5, 0, 10, 10)), (2, 130.0, 100.0, (0, 0, 10, 10))])
    frame2, _ = av.build_rows(geb2, bkm2, _info([{"GESCH_ANZ": 3}], 2, 2))
    assert frame2["height_m"].iloc[0] == pytest.approx(9.0)


def test_outlines_dissolve_and_split_parts_numbered_largest_first():
    geb = _geb([(7, (0, 0, 10, 10)), (7, (10, 0, 20, 10)), (8, (100, 0, 110, 10)), (8, (200, 0, 230, 10))])
    frame, stats = av.build_rows(geb, _bkm([(7, 110.0, 100.0, (0, 0, 20, 10))]), _info([{"GESCH_ANZ": 4}], 5, 5))
    ids = list(frame["osm_id"])
    assert ids.count("AT-VIE-7") == 1 and "AT-VIE-7_p1" not in ids
    assert "AT-VIE-8_p1" in ids and "AT-VIE-8_p2" in ids
    big = frame[frame["osm_id"] == "AT-VIE-8_p1"].iloc[0]
    assert big.geometry.area == pytest.approx(300.0)
    merged = frame[frame["osm_id"] == "AT-VIE-7"].iloc[0]
    assert merged.geometry.area == pytest.approx(200.0)
    assert stats["buildings_dissolved"] == 2 and stats["footprint_parts"] == 3


def test_year_rule_most_frequent_and_tie_means_no_year():
    pts = _info([{"BAUJAHR": 1900}, {"BAUJAHR": 1900}, {"BAUJAHR": 1910}])
    assert av.aggregate_points(pts)["year_built"] == 1900
    tie = av.aggregate_points(_info([{"BAUJAHR": 1900}, {"BAUJAHR": 1910}]))
    assert tie["year_built"] is None and tie["year_tie"] is True


def test_storeys_zero_is_not_observed_and_max_is_taken():
    assert av.aggregate_points(_info([{"GESCH_ANZ": 0}]))["levels"] is None
    assert av.aggregate_points(_info([{"GESCH_ANZ": 0}, {"GESCH_ANZ": 4}, {"GESCH_ANZ": 3}]))["levels"] == 4
    geb = _geb([(1, (0, 0, 10, 10))])
    frame, _ = av.build_rows(geb, _bkm([(1, 110.0, 100.0, (0, 0, 10, 10))]), _info([{"GESCH_ANZ": 0}], 5, 5))
    assert pd.isna(frame["levels"].iloc[0])


def test_year_out_of_range_is_not_used_and_single_year_text_is():
    assert av.point_year(1400, None) is None
    assert av.point_year(2020, None) is None
    assert av.point_year(1500, None) == 1500 and av.point_year(2016, None) == 2016
    assert av.point_year(None, "1848 -1918") is None
    assert av.point_year(None, "1925") == 1925
    assert av.point_year(2020, "1930") == 1930


def test_use_is_residential_when_at_least_half_of_points_are():
    assert av.aggregate_points(_info([{"L_NUTZUNG": "Wohnnutzung"}, {"L_NUTZUNG": "betriebliche Nutzung"}]))["function_tag"] == "Wohnnutzung"
    other = av.aggregate_points(_info([{"L_NUTZUNG": "Wohnnutzung"}, {"L_NUTZUNG": "Sonstige"}, {"L_NUTZUNG": "Sonstige"}]))
    assert other["function_tag"] == "Sonstige"


def test_points_outside_every_footprint_are_dropped_and_counted():
    geb, bkm, info = _fixture_frames()
    _, stats = av.build_rows(geb, bkm, info)
    assert stats["points_total"] == 20
    assert stats["points_dropped_outside_footprints"] == 10
    assert stats["buildings_with_0_points"] + stats["buildings_with_1_point"] + stats["buildings_with_2plus_points"] == stats["footprint_parts"]


def test_crs_is_utm_33n_and_provenance_strings():
    geb, bkm, info = _fixture_frames()
    frame, _ = av.build_rows(geb, bkm, info)
    assert str(frame.crs).upper() == "EPSG:32633"
    out = av.finalize_vienna(frame)
    assert str(out.crs).upper() == "EPSG:32633"
    assert set(out["provenance_geometry"]) <= {"VIENNA_FMZK_GEB", "VIENNA_FMZK_GEB_OVERLAP_RESOLVED"}
    assert set(out["provenance_height_m"]) <= {"VIENNA_BKM_MEASURED", "VIENNA_BKM_MISSING"}
    observed = out[out["levels"].notna()]
    assert len(observed) > 0 and (observed["provenance_levels"] == "VIENNA_GEBAEUDEINFO_OBSERVED").all()
