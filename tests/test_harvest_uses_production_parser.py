import importlib
import shutil
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
GOLDEN_SQL = REPO / "tests" / "fixtures" / "golden_sql" / "r1_single_zone.sql"
HARVEST_FILES = [
    REPO / "scripts" / "cluster" / "t08_harvest_results.py",
    REPO / "scripts" / "cluster" / "t07_harvest_results.py",
]

sys.path.insert(0, str(REPO))

from openubem.results.parser import check_building_integrity, parse_building


def _manifest_row():
    return pd.Series({
        "osm_id": "way/R1", "footprint_area_m2": 196.0, "levels": 2.0,
        "height_m": float("nan"), "num_zones": 1, "data_quality_flag": "",
    })


@pytest.fixture()
def dh_hot_water_sql(tmp_path):
    dst = tmp_path / "eplusout.sql"
    shutil.copy2(GOLDEN_SQL, dst)
    with sqlite3.connect(dst) as conn:
        cur = conn.execute(
            "UPDATE TabularData SET Value='    50.00' WHERE TabularDataIndex=216"
        )
        assert cur.rowcount == 1
    return dst


@pytest.mark.parametrize("path", HARVEST_FILES, ids=lambda p: p.name)
def test_no_local_parse_sql(path):
    assert "def _parse_sql" not in path.read_text(encoding="utf-8")


def test_harvest_total_equals_parse_building_with_district_hot_water(dh_hot_water_sql):
    t08 = importlib.import_module("scripts.cluster.t08_harvest_results")
    t07 = importlib.import_module("scripts.cluster.t07_harvest_results")
    prod = parse_building(dh_hot_water_sql, None, _manifest_row())
    assert prod["dhw_district_eui_kwh_m2"] > 0.0

    legacy = t08._production_row(dh_hot_water_sql, _manifest_row())
    assert legacy["total_eui"] == prod["total_eui_kwh_m2"]
    assert legacy["dhw_district_eui_kwh_m2"] == prod["dhw_district_eui_kwh_m2"]
    assert legacy["floor_area_m2"] == prod["floor_area_m2"]

    direct = t07.parse_production(dh_hot_water_sql, _manifest_row())
    assert direct["total_eui_kwh_m2"] == prod["total_eui_kwh_m2"]
    assert direct["abups_ok"] == check_building_integrity(dh_hot_water_sql)["abups_ok"]
    assert "abups_ok" in legacy


def test_failed_production_parse_raises_not_fabricates(tmp_path):
    t08 = importlib.import_module("scripts.cluster.t08_harvest_results")
    missing = tmp_path / "eplusout.sql"
    with pytest.raises(ValueError):
        t08.parse_production(missing, _manifest_row())
