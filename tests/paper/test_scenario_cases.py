import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("scenario_cases", ROOT / "scripts" / "paper" / "scenario_cases.py")
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

CELLS = ["a", "b", "c"]


def _fleet(n=10):
    rows = []
    for i in range(n):
        rows.append({
            "cell": "nyc_centre" if i % 2 == 0 else "la_urban", "city": "nyc" if i % 2 == 0 else "la",
            "osm_id": f"way/{i}", "archetype_id": "LargeOffice" if i < 3 else "SmallOffice",
            "floor_area_m2": 100.0 + i, "source": ["base", "open35", "open38"][i % 3],
        })
    return pd.DataFrame(rows)


EPWS = {"nyc_centre": "nyc.epw", "la_urban": "la.epw"}


def test_rows_unique_and_waves_within_limit():
    cases = sc.build_case_list(_fleet(10), EPWS, CELLS, max_wave=8)
    assert len(cases) == 30
    assert not cases.duplicated(["cell", "stem"]).any()
    assert cases.groupby("wave").size().max() <= 8
    assert cases["wave"].nunique() == 4
    assert sc.check_case_list(cases, 10, CELLS, max_wave=8) == []


def test_wave_task_is_one_to_size_in_each_wave():
    cases = sc.build_case_list(_fleet(10), EPWS, CELLS, max_wave=8)
    for _, g in cases.groupby("wave"):
        assert sorted(g["wave_task"]) == list(range(1, len(g) + 1))
    assert list(cases["task"]) == list(range(1, 31))


def test_large_buildings_are_spread_across_waves():
    cases = sc.build_case_list(_fleet(10), EPWS, CELLS, max_wave=8)
    large = cases[cases["archetype"] == "LargeOffice"].groupby("wave").size()
    assert large.sum() == 9 and len(large) == 4 and large.max() - large.min() <= 1


def test_paths_epw_and_stem_follow_the_pilot_rules():
    cases = sc.build_case_list(_fleet(10), EPWS, CELLS, max_wave=8)
    r = cases[(cases["cell"] == "a") & (cases["osm_id"] == "way/1")].iloc[0]
    assert r["stem"] == "way_1"
    assert r["idf_path"].endswith("/open35_resim_2026-09-30_full/idfs/auto__la_urban__way_1.idf")
    assert r["epw_name"] == "la.epw" and r["geo_cell"] == "la_urban"
    base = cases[(cases["cell"] == "a") & (cases["osm_id"] == "way/0")].iloc[0]
    assert base["idf_path"].endswith("/t07_resim_2026-09-09/idfs/way_0.idf")


def test_check_catches_a_duplicate_and_a_wrong_count():
    cases = sc.build_case_list(_fleet(10), EPWS, CELLS, max_wave=8)
    bad = pd.concat([cases, cases.iloc[[0]]], ignore_index=True)
    problems = sc.check_case_list(bad, 10, CELLS, max_wave=8)
    assert any("rows" in p for p in problems) and any("unique" in p for p in problems)


def test_real_case_list_if_written():
    path = sc.OUT_CSV
    if not path.exists():
        return
    cases = pd.read_csv(path)
    assert len(cases) == 56973
    assert not cases.duplicated(["cell", "stem"]).any()
    assert cases.groupby("wave").size().max() <= 10000
    assert cases["cell"].nunique() == 7 and "baseline" not in set(cases["cell"])
