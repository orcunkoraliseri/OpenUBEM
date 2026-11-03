import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.eu22 import acquire_capetown as ac  # noqa: E402

X0, Y0 = 18.4600, -33.9300
D = 0.0003


def sq(i, j, w=1.0, h=1.0):
    return box(X0 + i * D, Y0 + j * D, X0 + (i + w * 0.6) * D, Y0 + (j + h * 0.6) * D)


def raw_frame():
    rows = [
        (101, 7.9, sq(0, 0)),
        (102, 9.1, sq(1, 0)),
        (103, 1.5, sq(2, 0)),
        (104, 3.0, sq(3, 0)),
        (105, 2.0, sq(4, 0)),
        (106, 4.4, sq(5, 0)),
        (107, 6.0, sq(6, 0)),
        (108, np.nan, sq(7, 0)),
        (109, 10.0, sq(8, 0)),
    ]
    return gpd.GeoDataFrame(
        {"OBJECTID": [r[0] for r in rows], "BLD_HGHT": [r[1] for r in rows], "DATA_SRC": "LIDAR", "ACQS_PRD": "2023", "ACQS_MTHD": "ML",
         "geometry": [r[2] for r in rows]},
        geometry="geometry", crs="EPSG:4326",
    )


def osm_frames():
    osm = gpd.GeoDataFrame(
        {
            "building": ["terrace", "apartments", "commercial", "yes", "yes", "house"],
            "landuse": None,
            "start_date": ["", "1925", "", "", "", ""],
            "amenity": [None, None, None, None, "school", None],
            "geometry": [sq(0, 0, 1.1, 1.1), sq(1, 0, 1.1, 1.1), sq(5, 0, 1.1, 1.1), sq(6, 0, 1.1, 1.1), sq(7, 0, 1.1, 1.1), sq(8, 0, 1.1, 1.1)],
        },
        geometry="geometry", crs="EPSG:4326",
    ).to_crs(ac.EXPECTED_CRS)
    for k in ac.OTHER_USE_KEYS:
        if k not in osm:
            osm[k] = None
    landuse = gpd.GeoDataFrame(
        {"landuse": ["residential"], "geometry": [box(X0 + 2.5 * D, Y0 - D, X0 + 7.5 * D, Y0 + 2 * D)]}, geometry="geometry", crs="EPSG:4326"
    ).to_crs(ac.EXPECTED_CRS)
    return osm, landuse


def test_paginate_stops_at_last_page():
    calls = []

    def fetch(offset, count):
        calls.append(offset)
        total = 4500
        n = max(0, min(count, total - offset))
        return {"features": [{}] * n}

    pages = ac.paginate(fetch, 2000)
    assert [len(p["features"]) for p in pages] == [2000, 2000, 500]
    assert calls == [0, 2000, 4000]


def test_paginate_exact_multiple_ends_on_empty_page():
    def fetch(offset, count):
        return {"features": [{}] * (count if offset < 4000 else 0)}

    pages = ac.paginate(fetch, 2000)
    assert [len(p["features"]) for p in pages] == [2000, 2000, 0]


def test_paginate_follows_transfer_limit_flag():
    def fetch(offset, count):
        return {"features": [{}] * 3, "exceededTransferLimit": offset < 6}

    pages = ac.paginate(fetch, 2000)
    assert len(pages) == 3


@pytest.mark.parametrize("h,expected", [(7.9, 3), (3.0, 1), (1.4, 1), (4.4, 1), (4.6, 2), (10.0, 3), (0.0, 1)])
def test_height_to_storeys(h, expected):
    assert ac.storeys_from_height(h) == expected


def test_missing_height_gives_missing_storeys():
    assert np.isnan(ac.storeys_from_height(np.nan))
    assert np.isnan(ac.storeys_from_height(None))


def test_footprint_frame_drops_sheds_and_sets_crs():
    out, rep = ac.footprint_frame(raw_frame())
    assert out.crs.to_string() == ac.EXPECTED_CRS
    assert rep["dropped_height_under_2m"] == 1
    assert rep["height_missing"] == 1
    assert "ZA-CPT-103" not in set(out["osm_id"])
    assert "ZA-CPT-105" in set(out["osm_id"])
    by = out.set_index("osm_id")
    assert int(by.at["ZA-CPT-101", "levels"]) == 3
    assert int(by.at["ZA-CPT-104", "levels"]) == 1
    assert pd.isna(by.at["ZA-CPT-108", "levels"])
    assert out["osm_id"].is_unique


def test_footprint_frame_dedups_objectid():
    raw = raw_frame()
    raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    raw = gpd.GeoDataFrame(raw, geometry="geometry", crs="EPSG:4326")
    out, rep = ac.footprint_frame(raw)
    assert rep["features_downloaded"] == 10
    assert rep["features_unique_objectid"] == 9


def test_residential_routes():
    out, _ = ac.footprint_frame(raw_frame())
    osm, landuse = osm_frames()
    use = ac.classify_use(out, osm, landuse).set_index(out["osm_id"])
    assert use.at["ZA-CPT-101", "route"] == "osm_residential_tag"
    assert use.at["ZA-CPT-102", "route"] == "osm_residential_tag"
    assert use.at["ZA-CPT-109", "route"] == "osm_residential_tag"
    assert use.at["ZA-CPT-104", "route"] == "landuse_residential_untagged"
    assert use.at["ZA-CPT-105", "route"] == "landuse_residential_untagged"
    assert use.at["ZA-CPT-106", "use_class"] == "non_residential"
    assert use.at["ZA-CPT-106", "route"] == "osm_other_use"
    assert use.at["ZA-CPT-107", "route"] == "landuse_residential_untagged"
    assert use.at["ZA-CPT-108", "use_class"] == "non_residential"
    assert use.at["ZA-CPT-108", "route"] == "osm_other_use"


def test_untagged_outside_landuse_is_not_residential():
    out, _ = ac.footprint_frame(raw_frame())
    osm, landuse = osm_frames()
    use = ac.classify_use(out, osm, landuse.iloc[0:0]).set_index(out["osm_id"])
    assert use.at["ZA-CPT-104", "route"] == "no_residential_evidence"
    assert use.at["ZA-CPT-104", "use_class"] == "non_residential"


def test_build_clean_pass_through_tags_and_schema():
    osm, landuse = osm_frames()
    raw = raw_frame()
    raw.loc[raw.OBJECTID == 104, "geometry"] = raw.loc[raw.OBJECTID == 104, "geometry"].apply(lambda g: g)
    clean, rep = ac.build_clean_buildings(raw, osm, landuse)
    assert clean.crs.to_string() == ac.EXPECTED_CRS
    by = clean.set_index("osm_id")
    assert by.at["ZA-CPT-101", "building_tag"] == "terrace"
    assert by.at["ZA-CPT-102", "building_tag"] == "apartments"
    assert by.at["ZA-CPT-104", "building_tag"] == ""
    assert by.at["ZA-CPT-102", "osm_start_date"] == "1925"
    assert by.at["ZA-CPT-101", "provenance_levels"] == "CPT_LIDAR_2023_HEIGHT_DERIVED"
    assert by.at["ZA-CPT-101", "provenance_height_m"] == "CPT_LIDAR_2023_OBSERVED"
    assert "ZA-CPT-103" not in by.index
    assert rep["dropped_height_under_2m"] == 1


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Early 20th C", 1916),
        ("Early 20th Century", 1916),
        ("Mid 20th C", 1949),
        ("Mid 20th Century", 1949),
        ("Early-Mid 20th Century", 1933),
        ("Late 19th C", 1883),
        ("Late 19th Century", 1883),
        ("Late 20th Century", 1983),
        ("Early 21st Century", 2016),
        ("Mid 21st Century", None),
        ("17th-18th C", 1699),
        ("17th-18th Century", 1699),
        ("Early-Mid 19th C", 1833),
    ],
)
def test_label_year_rule(label, expected):
    assert ac.label_year(label) == expected


def test_label_year_unreadable_label_gives_none():
    assert ac.label_year("") is None
    assert ac.label_year(None) is None
    assert ac.label_year("Victorian") is None


def test_attach_census_unlabeled_takes_block_counts():
    pts = gpd.GeoSeries([box(0, 0, 1, 1)] * 6, crs=ac.EXPECTED_CRS)
    frame = gpd.GeoDataFrame({"use_class": ["residential"] * 5 + ["non_residential"]}, geometry=pts)
    own = pd.DataFrame(
        {"site": ["HERITAGE:11", "HERITAGE:12", "", "", "", "HERITAGE:99"],
         "label": ["Early 20th C", "Early 20th C", "", "", "", "Mid 20th C"]}
    )
    block_id = pd.Series(["B1", "B1", "B1", "B2", np.nan, "B1"])
    mask = frame["use_class"] == "residential"
    out = ac.attach_census(frame, own, block_id, mask)
    assert out.at[0, "census_unit_id"] == "HERITAGE:11"
    assert out.at[0, "census_period_counts"] == '{"Early 20th C": 1}'
    assert out.at[2, "census_unit_id"] == "BLOCK:B1"
    assert out.at[2, "census_period_counts"] == '{"Early 20th C": 2}'
    assert out.at[3, "census_unit_id"] == "BLOCK:B2"
    assert out.at[3, "census_period_counts"] == "{}"
    assert out.at[4, "census_unit_id"] == ""
    assert out.at[4, "census_period_counts"] == ""
    assert out.at[5, "census_unit_id"] == "HERITAGE:99"
    assert out.at[2, "heritage_period"] == ""


def test_period_years_for_maps_used_labels_and_lists_unmapped():
    frame = pd.DataFrame({"census_period_counts": ['{"Early 20th C": 1}', '{"Mid 21st Century": 1}', '{"Early 20th C": 3, "Late 19th C": 1}', ""]})
    years, none = ac.period_years_for(frame)
    assert years == {"Early 20th C": 1916, "Late 19th C": 1883}
    assert none == ["Mid 21st Century"]


def test_year_split_counts_own_block_and_none():
    years = {"Early 20th C": 1916, "Mid 20th C": 1949}
    frame = pd.DataFrame(
        {
            "census_unit_id": ["HERITAGE:1", "HERITAGE:2", "BLOCK:B1", "BLOCK:B2", "BLOCK:B3", ""],
            "census_period_counts": [
                '{"Early 20th C": 1}', '{"Mid 21st Century": 1}', '{"Early 20th C": 2, "Mid 20th C": 1}',
                '{"Early 20th C": 1, "Mid 20th C": 1}', "{}", "",
            ],
        }
    )
    out = ac.year_split(frame, years)
    assert (out["own_label"], out["own_label_without_year"], out["block_label"], out["none"]) == (1, 1, 1, 4)
    assert out["none_reasons"] == {"OWN_LABEL_HAS_NO_YEAR": 1, "CENSUS_UNIT_PERIOD_TIE": 1, "CENSUS_UNIT_NO_PERIOD_DATA": 1, "NO_BLOCK": 1}


def test_block_selection_stops_at_first_total_of_500():
    counts = [240, 200, 150, 100, 50]
    blocks = gpd.GeoDataFrame(
        {"block_id": [f"B{i}" for i in range(5)]}, geometry=[box(i * 100, 0, (i + 1) * 100, 100) for i in range(5)], crs=ac.EXPECTED_CRS
    )
    pts = [
        box(i * 100 + 1 + (k % 50) * 1.9, 1 + (k // 50) * 20, i * 100 + 2 + (k % 50) * 1.9, 2 + (k // 50) * 20)
        for i, n in enumerate(counts)
        for k in range(n)
    ]
    residential = gpd.GeoDataFrame(geometry=pts, crs=ac.EXPECTED_CRS)
    picked = ac.choose_blocks(blocks, residential, box(0, 0, 500, 100))
    assert picked["chosen"] == ["B0", "B1", "B2"]
    assert picked["total"] == 590
    assert [s["running_total"] for s in picked["expansion_steps"]] == [440, 590]
    assert [b["running_total"] for b in ac.blocks_used(picked)] == [240, 440, 590]
