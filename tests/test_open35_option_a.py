import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from openubem.geometry.footprint import derive_num_floors
from openubem.idf.builder import _derive_num_floors_wired as builder_wired
from openubem.results.aggregator import _derive_num_floors_wired as agg_wired
from openubem.results.aggregator import _fleet_levels_medians
from openubem.results.parser import _derive_num_floors_wired as parser_wired
from openubem.semantic.building_classifier import _normalise_use_class


def _poly(x):
    return Polygon([(330000 + x, 4690000), (330014 + x, 4690000), (330014 + x, 4690014), (330000 + x, 4690014)])


def _fleet(target_levels=float("nan"), target_height=float("nan"), source="RULE_USE_CLASS_SIZE"):
    rows = []
    for i, lev in enumerate([3.0, 4.0, 5.0, 5.0, 5.0, 6.0, 7.0, 9.0]):
        rows.append({"osm_id": f"way/OBS{i}", "levels": lev, "height_m": float("nan"),
                     "function_tag": "apartments", "building_tag": "",
                     "footprint_area_m2": 100.0, "archetype_source": "RULE_RESIDENTIAL_TIER",
                     "geometry": _poly(i * 100)})
    rows.append({"osm_id": "way/TARGET", "levels": target_levels, "height_m": target_height,
                 "function_tag": "apartments", "building_tag": "",
                 "footprint_area_m2": 100.0, "archetype_source": source, "geometry": _poly(800)})
    return gpd.GeoDataFrame(rows, crs="EPSG:32618")


def _three(gdf):
    row = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0]
    gm, glob = _fleet_levels_medians(gdf)
    manifest = row.copy()
    manifest["_use_class"] = _normalise_use_class(row)[0]
    manifest["_levels_group_median"] = gm
    manifest["_levels_global_median"] = glob
    return builder_wired(row, gdf), agg_wired(row, gm, glob), parser_wired(manifest)


@pytest.mark.parametrize("source", ["RULE_USE_CLASS_SIZE", "RULE_RESIDENTIAL_TIER", "RULE_RESIDENTIAL_TIER,GROUPMEDIAN_LEVELS_MED", None])
def test_both_missing_gets_median_in_all_paths(source):
    assert _three(_fleet(source=source)) == (5, 5, 5)


def test_observed_levels_unchanged():
    assert _three(_fleet(target_levels=2.0)) == (2, 2, 2)


def test_height_only_unchanged():
    assert _three(_fleet(target_height=10.0)) == (3, 3, 3)


def test_no_medians_falls_back_to_one():
    row = pd.Series({"levels": float("nan"), "height_m": float("nan")})
    assert derive_num_floors(row) == 1


def test_global_median_used_when_group_absent():
    row = pd.Series({"levels": float("nan"), "height_m": float("nan")})
    assert derive_num_floors(row, use_class="x", levels_group_median={"y": 3}, levels_global_median=4) == 4

