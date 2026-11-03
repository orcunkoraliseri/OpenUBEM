import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "eu_climate_normalisation.py"
_spec = importlib.util.spec_from_file_location("eu_climate_normalisation", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def test_hdd_constant_year_exact():
    assert m.heating_degree_days(np.full(8760, 10.0)) == 365 * 8.0
    assert m.heating_degree_days(np.full(8760, 18.0)) == 0.0
    assert m.heating_degree_days(np.full(8760, 25.0)) == 0.0


def test_hdd_uses_daily_means():
    day_warm = np.r_[np.full(12, 0.0), np.full(12, 40.0)]
    assert m.heating_degree_days(np.tile(day_warm, 365)) == 0.0
    assert m.heating_degree_days(np.full(48, 8.0), base=18.0) == 20.0


def test_read_epw_synthetic(tmp_path):
    p = tmp_path / "x.epw"
    head = ["LOCATION,Test,,X,s,1,0,0,0", "a", "b", "c", "d", "e", "f", "g"]
    rows = [f"2020,1,1,{h % 24 + 1},60,?,{5.0}" for h in range(48)]
    p.write_text("\n".join(head + rows), encoding="utf-8")
    header, t = m.read_epw(p)
    assert header.startswith("LOCATION,Test") and len(t) == 48 and float(t.mean()) == 5.0


def test_output_ten_rows_and_cape_town_internal():
    df = pd.read_csv(m.OUT_CSV)
    assert len(df) == 10
    assert df["internal_only"].sum() == 1
    assert df.loc[df["internal_only"], "site"].iloc[0] == "ZA-CPT-WOODSTOCK"
    assert (df["hours"] == 8760).all()
