import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "exclusion_census.py"
_spec = importlib.util.spec_from_file_location("exclusion_census", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

README_LEFT_OUT = {
    "CA-MTL-PLATEAU": 9, "AM-EVN-NORNORK": 16, "ZA-CPT-WOODSTOCK": 1,
    "FI-HEL-KALLIO": 38, "AT-VIE-RUDOLFSHEIM": 19, "HU-BUD-ERZSEBETVAROS": 48,
}


def _totals():
    return pd.DataFrame(m.us_rows() + m.four_district_rows() + m.six_district_rows())


def test_long_rows_synthetic():
    left = pd.DataFrame({"floor_area_m2": [10.0, 30.0, None], "reason": ["A", "A", "B"],
                         "reason_source": ["s", "s", "s"]})
    rows = m.long_rows("X", "t", 13, 10, left, 60.0, "v")
    tot = rows[0]
    assert tot["buildings_left_out"] == 3 and tot["left_out_floor_area_m2"] == 40.0
    assert tot["left_out_floor_area_known_n"] == 2
    assert tot["left_out_area_share_pct"] == 40.0
    assert {r["reason"]: r["n_reason"] for r in rows[1:]} == {"A": 2, "B": 1}


def test_us_in_plus_out_is_8160():
    d = _totals()
    us = d[(d["site"] == "US-12-cells") & (d["row_type"] == "site_total")].iloc[0]
    assert us["buildings_in_result"] + us["buildings_left_out"] == 8160
    assert us["buildings_left_out"] == 21 and us["buildings_in_result"] == 8139


def test_eu_left_out_equals_readme():
    d = _totals()
    t = d[d["row_type"] == "site_total"].set_index("site")
    for site, n in README_LEFT_OUT.items():
        assert int(t.loc[site, "buildings_left_out"]) == n, site
    four = [s for s in m.FOUR]
    assert int(t.loc[four, "buildings_left_out"].sum()) == 232


def test_reason_rows_sum_to_site_total():
    d = _totals()
    for site, g in d.groupby("site"):
        tot = g[g["row_type"] == "site_total"].iloc[0]["n_reason"]
        assert g[g["row_type"] == "reason"]["n_reason"].sum() == tot, site
