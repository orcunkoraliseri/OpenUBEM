from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from openubem.acquisition.boundary_clip import split_residential
from openubem.acquisition.footprint_schema import SCHEMA_COLUMNS, finalize_footprints

ROOT = Path(__file__).parent.parent.parent
FIX = Path(__file__).parent / "fixtures"
_spec = importlib.util.spec_from_file_location("acquire_helsinki", ROOT / "scripts" / "eu22" / "acquire_helsinki.py")
ah = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ah)


@pytest.fixture(scope="module")
def built():
    feats = json.loads((FIX / "helsinki_buildings.json").read_text(encoding="utf-8"))["features"]
    raw = gpd.GeoDataFrame.from_features(feats, crs="EPSG:3879")
    labels = json.loads((FIX / "helsinki_code_labels.json").read_text(encoding="utf-8"))
    mapped, attrs = ah.map_buildings(raw, labels)
    clean = ah.attach_attributes(finalize_footprints(mapped, source=ah.SOURCE), attrs)
    return mapped, attrs, clean


def _row(clean, i):
    return clean[clean.osm_id == f"FI-HEL-{900000 + i}"].iloc[0]


def test_fixture_has_20_features(built):
    assert len(built[2]) == 20


def test_schema_complete_and_crs(built):
    clean = built[2]
    assert list(clean.columns[:23]) == SCHEMA_COLUMNS
    assert "observed_dwellings" in clean.columns
    assert clean.crs.to_string() == "EPSG:32635"
    assert (clean["crs_utm"] == "EPSG:32635").all()


def test_year_forms(built):
    clean = built[2]
    assert _row(clean, 0).year_built == 1928
    assert _row(clean, 1).year_built == 1957
    assert _row(clean, 4).year_built == 1990
    assert _row(clean, 3).year_built == 1901
    assert _row(clean, 13).year_built is ah.pd.NA
    assert _row(clean, 14).year_built is ah.pd.NA
    assert _row(clean, 0).provenance_year_built == "HELSINKI_REKISTERI_OBSERVED"
    assert _row(clean, 15).provenance_year_built == "HELSINKI_REKISTERI_MISSING"


def test_storeys_zero_or_null_not_observed(built):
    clean = built[2]
    assert _row(clean, 0).levels == 5
    assert _row(clean, 2).levels is ah.pd.NA
    assert _row(clean, 3).levels is ah.pd.NA
    assert _row(clean, 2).provenance_levels == "HELSINKI_REKISTERI_MISSING"


def test_code_mapping(built):
    clean = built[2]
    tags = {i: _row(clean, i).building_tag for i in range(20)}
    assert tags[4] == "detached"
    assert tags[5] == "terrace" and tags[6] == "terrace"
    assert tags[7] == "apartments"
    assert tags[0] == "" and tags[8] == "" and tags[9] == "" and tags[10] == ""
    classes = {i: _row(clean, i).use_class for i in range(20)}
    for i in (0, 1, 4, 5, 6, 7, 8, 9, 10, 15, 16):
        assert classes[i] == "residential"
    for i in (11, 12, 13, 18):
        assert classes[i] == "non_residential"
    assert classes[14] == "unknown"
    assert _row(clean, 11).function_tag == "Office buildings"
    assert _row(clean, 4).function_tag == "One-dwelling houses"


def test_observed_dwellings(built):
    clean = built[2]
    assert _row(clean, 0).observed_dwellings == 12
    assert _row(clean, 4).observed_dwellings == 1
    assert _row(clean, 3).observed_dwellings is ah.pd.NA
    assert _row(clean, 16).observed_dwellings is ah.pd.NA
    assert _row(clean, 11).observed_dwellings is ah.pd.NA


def test_split_residential(built):
    res, exc, counts = split_residential(built[2], ah.CROSSWALK, class_column="use_class")
    assert counts["residential"] == 15 and counts["non_residential"] == 4 and counts["unknown"] == 1
    assert len(res) + len(exc) == 20


def test_choose_subunits_expands_nearest_first():
    import geopandas as gpd
    from shapely.geometry import Point

    osa = gpd.GeoDataFrame(
        {"tunnus": ["A", "B", "C"], "nimi_fi": ["a", "b", "c"]},
        geometry=[box(25497000, 6674000, 25497100, 6674100), box(25497100, 6674000, 25497300, 6674100), box(25497300, 6674000, 25497900, 6674100)],
        crs="EPSG:3879",
    )
    pts = [Point(25497050 + (i % 10), 6674010 + i // 10) for i in range(60)] + [Point(25497150 + i, 6674050) for i in range(30)] + [Point(25497400 + i, 6674050) for i in range(30)]
    res = gpd.GeoDataFrame(geometry=[p.buffer(1) for p in pts], crs="EPSG:3879").to_crs("EPSG:32635")
    out = ah.choose_subunits(osa, res, box(25497000, 6674000, 25497300, 6674100), low=80, high=200)
    assert out["chosen"] == ["A", "B"] and out["total"] == 90


def _ring_fixture():
    from shapely.geometry import Point

    osa = gpd.GeoDataFrame(
        {"tunnus": ["IN1", "IN2", "R1", "R2", "R3"], "nimi_fi": ["i1", "i2", "r1", "r2", "r3"]},
        geometry=[
            box(25497000, 6674000, 25497100, 6674100), box(25497100, 6674000, 25497200, 6674100),
            box(25497200, 6674000, 25497300, 6674100), box(25496850, 6674000, 25497000, 6674100),
            box(25497300, 6674000, 25497400, 6674100),
        ],
        crs="EPSG:3879",
    )
    district = box(25497000, 6674000, 25497200, 6674100)
    pts = [Point(25497010 + (i % 50), 6674010 + i // 50) for i in range(60)] + [Point(25497110 + (i % 50), 6674010 + i // 50) for i in range(60)]
    pts += [Point(25496910 + (i % 50), 6674010 + i // 50) for i in range(40)] + [Point(25497210 + (i % 50), 6674010 + i // 50) for i in range(60)] + [Point(25497310 + (i % 50), 6674010 + i // 50) for i in range(60)]
    res = gpd.GeoDataFrame(geometry=[p.buffer(0.5) for p in pts], crs="EPSG:3879").to_crs("EPSG:32635")
    return osa, res, district


def test_whole_district_kept_and_nearest_outside_added():
    osa, res, district = _ring_fixture()
    out = ah.choose_subunits(osa, res, district, low=150, high=400)
    assert out["district_whole"] is True and out["district_total"] == 120
    assert set(out["chosen"][:2]) == {"IN1", "IN2"}
    assert out["added_outside"] == ["R1"] and out["total"] == 180
    assert out["expansion_steps"][0]["running_total"] == 180 and out["expansion_steps"][0]["inside_district"] is False
    assert out["boundary_geom"].covers(gpd.GeoSeries([district], crs="EPSG:3879").to_crs("EPSG:32635").iloc[0])


def test_whole_district_adds_until_threshold_nearest_first():
    osa, res, district = _ring_fixture()
    out = ah.choose_subunits(osa, res, district, low=200, high=400)
    assert out["added_outside"] == ["R1", "R2"] and out["total"] == 220
    assert [s["running_total"] for s in out["expansion_steps"]] == [180, 220]


def test_whole_district_not_used_when_district_reaches_low():
    osa, res, district = _ring_fixture()
    out = ah.choose_subunits(osa, res, district, low=100, high=400)
    assert "district_whole" not in out


def _raw_one(code, tyyppi):
    return gpd.GeoDataFrame(
        {"id": [910001], "tyyppi": [tyyppi], "c_kayttark": [code], "i_kerrlkm": [3], "c_valmpvm": ["1960"], "i_asuinhuoneistojen_lkm": [6], "postinumero": ["00530"]},
        geometry=[box(25497620, 6674560, 25497632, 6674570)],
        crs="EPSG:3879",
    )


def test_no_code_asuinrakennus_is_residential_with_tag():
    mapped, attrs = ah.map_buildings(_raw_one(None, "Asuinrakennus"), {})
    assert attrs.iloc[0].use_class == "residential"
    assert mapped.iloc[0].function_tag == "tyyppi:Asuinrakennus"
    assert mapped.iloc[0].building_tag == ""
    res, exc, counts = split_residential(ah.attach_attributes(finalize_footprints(mapped, source=ah.SOURCE), attrs), ah.CROSSWALK, class_column="use_class")
    assert counts["residential"] == 1 and counts["unknown"] == 0


def test_no_code_other_type_stays_unknown_and_code_wins_over_type():
    mapped, attrs = ah.map_buildings(_raw_one(None, "Muu rakennus"), {})
    assert attrs.iloc[0].use_class == "unknown" and mapped.iloc[0].function_tag == ""
    mapped, attrs = ah.map_buildings(_raw_one("151", "Asuinrakennus"), {"151": "Office buildings"})
    assert attrs.iloc[0].use_class == "non_residential" and mapped.iloc[0].function_tag == "Office buildings"


def _parts_frame(counts_total, areas, levels):
    import pandas as pd

    n = len(areas)
    ids = [f"FI-HEL-1_part{i}" for i in range(n)] + ["FI-HEL-2"]
    gdf = gpd.GeoDataFrame(
        {"osm_id": ids, "levels": pd.array(levels + [3], dtype="Int64"), "footprint_area_m2": areas + [100.0]},
        geometry=[box(0, 0, 1, 1)] * (n + 1),
        crs="EPSG:32635",
    )
    attrs = pd.DataFrame({"observed_dwellings": pd.array([counts_total, 7], dtype="Int64")}, index=["FI-HEL-1", "FI-HEL-2"])
    attrs["c_kayttark"] = ["032", "021"]
    attrs["use_class"] = ["residential", "residential"]
    return ah.attach_attributes(gdf, attrs)


def test_part_split_sums_to_building_total_and_weights_by_area_times_storeys():
    out = _parts_frame(312, [400.0, 400.0, 800.0, 200.0], [8, 8, 8, 8])
    parts = out[out.osm_id.str.contains("_part")]
    assert int(parts.observed_dwellings.sum()) == 312
    assert [int(v) for v in parts.observed_dwellings] == [69, 69, 139, 35]
    assert (parts.observed_dwellings >= 1).all()
    assert int(out[out.osm_id == "FI-HEL-2"].observed_dwellings.iloc[0]) == 7


def test_part_split_every_part_at_least_one_when_total_allows():
    out = _parts_frame(4, [10000.0, 10.0, 10.0], [5, 5, 5])
    parts = out[out.osm_id.str.contains("_part")]
    assert int(parts.observed_dwellings.sum()) == 4
    assert (parts.observed_dwellings >= 1).all()


def test_part_split_unknown_total_stays_unknown():
    out = _parts_frame(None, [100.0, 100.0], [3, 3])
    assert out[out.osm_id.str.contains("_part")].observed_dwellings.isna().all()


def test_split_counts_largest_remainder_exact():
    assert ah.split_counts(10, [1.0, 1.0, 1.0]) == [4, 3, 3]
    assert sum(ah.split_counts(39, [363.0, 500.0, 816.0, 600.0])) == 39
