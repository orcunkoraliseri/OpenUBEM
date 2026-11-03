import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "remove_dhw_double_count.py"
_spec = importlib.util.spec_from_file_location("remove_dhw_double_count", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def _row(osm, city, area, dhw_gas, dhw_dist, heating=50.0, lighting=10.0):
    d = {c: 0.0 for c in m.KEEP_FULL}
    dhw = dhw_gas + dhw_dist
    total = heating + lighting + dhw
    d.update(cell=f"{city}_centre", city=city, osm_id=osm, archetype_id="SmallOffice",
             parse_status="success", floor_area_m2=area, heating_eui_kwh_m2=heating,
             lighting_eui_kwh_m2=lighting, dhw_gas_eui_kwh_m2=dhw_gas,
             dhw_district_eui_kwh_m2=dhw_dist, dhw_eui_kwh_m2=dhw,
             total_eui_kwh_m2=total, total_kwh=total * area, data_quality_flag="", source="base")
    from openubem.results.carbon import compute_gwp
    d["gwp_total_kgco2"] = compute_gwp(d, m.STATE_OF[city])["gwp_total_kgco2_m2"] * area
    return d


def _fleet():
    return pd.DataFrame([_row("a", "nyc", 100.0, 20.0, 20.0),
                         _row("b", "la", 200.0, 10.0, 10.0),
                         _row("c", "austin", 50.0, 0.0, 0.0)])


def test_eui_drop_equals_removed_part():
    fleet = _fleet()
    fixed, checks = m.correct_table(fleet)
    drop = fleet["total_eui_kwh_m2"] - fixed["total_eui_kwh_m2"]
    assert (drop - fixed["dhw_district_removed_eui_kwh_m2"]).abs().max() < 1e-9
    assert (fixed["dhw_district_eui_kwh_m2"] == 0.0).all()
    assert abs(fixed.loc[0, "dhw_eui_kwh_m2"] - 20.0) < 1e-12
    assert abs(fixed.loc[0, "total_kwh"] - (fleet.loc[0, "total_kwh"] - 20.0 * 100.0)) < 1e-9
    assert checks["max_abs_diff_unchanged_carbon_terms_kg_m2"] < 1e-9


def test_carbon_drops_by_district_factor_only():
    fleet = _fleet()
    fixed, _ = m.correct_table(fleet)
    expected = (fleet["gwp_total_kgco2"] - fixed["gwp_total_kgco2"]).tolist()
    want = [20.0 * 100.0 * m.F_DH, 10.0 * 200.0 * m.F_DH, 0.0]
    assert all(abs(a - b) < 1e-6 for a, b in zip(expected, want))


def test_put_back_restores_adopted_figures():
    fleet = _fleet()
    fixed, _ = m.correct_table(fleet)
    eui, carbon = m.put_back(fixed)
    assert abs(eui - fleet["total_kwh"].sum() / fleet["floor_area_m2"].sum()) < 1e-9
    assert abs(carbon - fleet["gwp_total_kgco2"].sum() / 1000.0) < 1e-9
    shares = m.share_by_city(fixed)
    assert shares["austin"]["share_of_total_energy_removed_pct"] == 0.0
    assert shares["nyc"]["share_of_total_energy_removed_pct"] > 0.0
