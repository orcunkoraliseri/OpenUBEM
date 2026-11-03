import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
_P = ROOT / "scripts" / "validation" / "phaseE_rescore.py"
_spec = importlib.util.spec_from_file_location("phaseE_rescore", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

ELEVRB = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
FLEET = ROOT / "openubem" / "outputs" / "comparisons" / "paper_adopted_fleet_per_building_2026-10-21.csv"


def _synthetic(tmp_path):
    rows = []
    for cell in m._CELLS:
        rows.append({"cell": cell, "osm_id": f"way/{cell}", "archetype_id": "SmallOffice",
                     "parse_status": "success", "total_eui_kwh_m2": 100.0,
                     "floor_area_m2": 10.0, "total_kwh": 1000.0})
    p = tmp_path / "fleet.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_defaults_unchanged():
    assert m._INPUT is None
    assert m._PHASEE_DIR.name == "phaseE"
    assert m._REPORT_PATH.name == "REPORT_phaseE_final.md"
    assert m._OUTPUTS_DIR.name == "comparisons"


def test_load_input_csv_adds_city_density_status(tmp_path):
    df = m.load_input(_synthetic(tmp_path))
    assert set(df["city"]) == {"nyc", "la", "austin"}
    assert set(df["density"]) == set(m._DENSITIES)
    assert (df["simulation_status"] == "success").all()


def test_density_table_quartiles():
    derr = pd.DataFrame({"city": ["nyc"] * 4, "density": ["centre"] * 4, "err_pct": [-40.0, -30.0, -20.0, -10.0]})
    t = m.density_table(derr)
    assert len(t) == 1
    assert t.iloc[0]["n"] == 4 and t.iloc[0]["median_err_pct"] == -25.0


def test_density_errors_excludes_apartments_and_unknown(tmp_path):
    df = m.load_input(_synthetic(tmp_path))
    extra = df.iloc[:3].copy()
    extra["archetype_id"] = ["MidriseApartment", "OpenUBEMUnknown", "DataCenter"]
    out = m.density_errors(pd.concat([df, extra], ignore_index=True))
    assert not out["archetype_id"].isin({"MidriseApartment", "OpenUBEMUnknown", "DataCenter"}).any()
    assert len(out) == 12
    assert (out["err_pct"] == (100.0 - out["cbecs_wmean"]) / out["cbecs_wmean"] * 100.0).all()


@pytest.mark.skipif(not ELEVRB.exists(), reason="old Phase-E elevator re-run inputs absent")
def test_old_inputs_reproduce_old_city_errors():
    df = m.load_input(ELEVRB)
    t = m.score_city_anchors(df)
    overall = t[t["segment"].str.startswith("Overall")].set_index("city")["delta_pct"]
    assert round(overall["nyc"], 1) == -31.3
    assert round(overall["la"], 1) == -3.6
    assert round(overall["austin"], 1) == -30.5
    g = m.score_cbecs_all_cities(df)
    assert abs(g["nyc"]["cbecs_r2"] - 0.877) < 0.001
    assert abs(g["la"]["cbecs_r2"] - 0.902) < 0.001
    assert abs(g["austin"]["cbecs_r2"] - 0.723) < 0.001


@pytest.mark.skipif(not FLEET.exists(), reason="T01 table absent")
def test_new_run_population_is_8139():
    df = m.load_input(FLEET)
    assert len(df) == 8139
    assert int(df["simulation_status"].isin(m._SUCCESS_STATUSES).sum()) == 8139
