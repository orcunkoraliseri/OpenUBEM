import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "hourly_case_list.py"
_spec = importlib.util.spec_from_file_location("hourly_case_list", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

BASE = "/speed-scratch/o_iseri/openubem/fleets"


def test_paths_follow_each_source_layout():
    assert m.remote_sql_path("base", "nyc_centre", "way/12") == (
        f"{BASE}/t07_resim_2026-09-09/out/way_12/eplusout.sql")
    assert m.remote_sql_path("open35", "la_urban", "relation/5") == (
        f"{BASE}/open35_resim_2026-09-30_full/out/auto__la_urban__relation_5/eplusout.sql")
    assert m.remote_sql_path("open38", "austin_rural", "way/7") == (
        f"{BASE}/open38_fix_rerun_2026-09-30_full/out/auto__austin_rural__way_7/eplusout.sql")


def test_case_list_is_numbered_from_one_in_cell_order():
    fleet = pd.DataFrame({
        "cell": ["b_cell", "a_cell", "a_cell"],
        "osm_id": ["way/3", "way/2", "way/1"],
        "source": ["base", "open35", "base"],
    })
    cases = m.build_case_list(fleet)
    assert list(cases["task"]) == [1, 2, 3]
    assert list(cases["osm_id"]) == ["way/1", "way/2", "way/3"]
    assert cases["sql_path"].is_unique
    assert cases.loc[1, "stem"] == "way_2"
