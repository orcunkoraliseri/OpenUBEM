import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("hourly_pilot_cases", ROOT / "scripts" / "paper" / "hourly_pilot_cases.py")
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

BASE = "/speed-scratch/o_iseri/openubem/fleets"


def _cell(city, cell, n, eui, area=100.0, source="base", start=0):
    return pd.DataFrame({
        "city": city, "cell": cell,
        "osm_id": [f"way/{start + i}" for i in range(n)],
        "source": source,
        "floor_area_m2": area,
        "total_kwh": eui * area,
        "heating_eui_kwh_m2": 10.0, "cooling_eui_kwh_m2": 20.0,
    })


def _dhw(fleet):
    return pd.DataFrame({"osm_id": fleet["osm_id"], "dhw_district_removed_eui_kwh_m2": 2.0})


def test_pick_cell_takes_the_closest_to_the_city_among_cells_with_enough_buildings():
    fleet = pd.concat([
        _cell("nyc", "nyc_a", 60, 100.0, start=0),
        _cell("nyc", "nyc_b", 60, 150.0, start=100),
        _cell("nyc", "nyc_tiny", 10, 50.0, start=200),
    ], ignore_index=True)
    pick = m.pick_cell(fleet, "nyc")
    assert pick["buildings"] == 60
    assert pick["city_eui"] == pytest.approx((60 * 100 * 100 + 60 * 150 * 100 + 10 * 50 * 100) / (130 * 100))
    assert pick["cell"] == "nyc_a"


def test_tie_goes_to_the_cell_with_fewer_buildings():
    fleet = pd.concat([
        _cell("la", "la_a", 100, 90.0, area=100.0, start=0),
        _cell("la", "la_b", 50, 110.0, area=200.0, start=500),
    ], ignore_index=True)
    city = m.pooled_eui(fleet)
    a = abs(90.0 - city)
    b = abs(110.0 - city)
    assert a == pytest.approx(b)
    assert m.pick_cell(fleet, "la")["cell"] == "la_b"


def test_cells_under_the_minimum_are_never_picked():
    fleet = pd.concat([_cell("austin", "austin_big", 80, 200.0), _cell("austin", "austin_small", 49, 100.0, start=500)],
                      ignore_index=True)
    assert m.pick_cell(fleet, "austin")["cell"] == "austin_big"


def test_case_list_rows_columns_and_references():
    fleet = pd.concat([
        _cell("nyc", "nyc_a", 55, 100.0, start=0, source="base"),
        _cell("la", "la_a", 52, 100.0, start=1000, source="open35"),
        _cell("austin", "austin_a", 51, 100.0, start=2000, source="open38"),
        _cell("austin", "austin_small", 5, 100.0, start=3000),
    ], ignore_index=True)
    epws = {"nyc_a": "n.epw", "la_a": "l.epw", "austin_a": "a.epw", "austin_small": "s.epw"}
    cases, picks = m.build_case_list(fleet, _dhw(fleet), epws)
    assert len(cases) == 55 + 52 + 51
    assert list(cases["task"]) == list(range(1, len(cases) + 1))
    assert cases["stem"].is_unique and cases["idf_path"].is_unique
    assert not cases[list(m.REFERENCE_COLUMNS)].isna().any().any()
    assert m.check_case_list(cases, fleet, picks) == []
    row = cases.iloc[0]
    assert row["ref_heating_kwh"] == pytest.approx(10.0 * 100.0)
    assert row["ref_cooling_kwh"] == pytest.approx(20.0 * 100.0)
    assert row["ref_district_hot_water_kwh"] == pytest.approx(2.0 * 100.0)
    assert row["ref_electricity_gas_kwh"] == pytest.approx(100.0 * 100.0 - 200.0)


def test_idf_paths_follow_each_source_layout():
    assert m.remote_idf_path("base", "nyc_centre", "way/12") == f"{BASE}/t07_resim_2026-09-09/idfs/way_12.idf"
    assert m.remote_idf_path("open35", "la_urban", "relation/5") == (
        f"{BASE}/open35_resim_2026-09-30_full/idfs/auto__la_urban__relation_5.idf")
    assert m.remote_idf_path("open38", "austin_rural", "way/7") == (
        f"{BASE}/open38_fix_rerun_2026-09-30_full/idfs/auto__austin_rural__way_7.idf")


def test_check_flags_a_null_reference_and_a_duplicate_stem():
    fleet = _cell("nyc", "nyc_a", 55, 100.0)
    cases, picks = m.build_case_list(fleet, _dhw(fleet), {"nyc_a": "n.epw"})
    bad = cases.copy()
    bad.loc[0, "ref_heating_kwh"] = float("nan")
    bad.loc[1, "stem"] = bad.loc[2, "stem"]
    problems = m.check_case_list(bad, fleet, picks)
    assert any("null" in p for p in problems) and any("stem" in p for p in problems)


def test_written_case_list_matches_the_t01_cells_when_present():
    path = m.OUT_CSV
    if not path.exists():
        pytest.skip("case list not written")
    cases = pd.read_csv(path)
    fleet = pd.read_csv(m.FLEET_CSV)
    assert len(cases) == int(fleet[fleet["cell"].isin(cases["cell"].unique())].shape[0])
    assert cases["stem"].is_unique
    assert not cases[list(m.REFERENCE_COLUMNS)].isna().any().any()
    assert cases.groupby("city")["cell"].nunique().max() == 1
