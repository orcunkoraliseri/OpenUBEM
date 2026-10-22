import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("retrofit_carbon", ROOT / "scripts" / "paper" / "retrofit_carbon.py")
rcb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcb)
rd = rcb.rd

DISTRICT_ZERO = [c for c in rd.CARBON_COLS if c not in ("dhw_gas_eui_kwh_m2", "dhw_elec_eui_kwh_m2", "dhw_district_eui_kwh_m2")]
BUILDINGS = [("way/1", "nyc", "nyc_centre", 1000.0, 50.0, 10.0),
             ("way/2", "la", "la_urban", 2000.0, 20.0, 8.0),
             ("way/3", "austin", "austin_rural", 500.0, 30.0, 6.0)]


def _raw(osm, city, geo, area, heating, dd):
    r = {"osm_id": osm, "city": city, "cell": geo, "archetype_id": "SmallOffice", "floor_area_m2": area,
         "heating_eui_kwh_m2": heating, "cooling_eui_kwh_m2": 5.0, "lighting_eui_kwh_m2": 10.0,
         "equipment_eui_kwh_m2": 20.0, "fans_eui_kwh_m2": 3.0, "pumps_eui_kwh_m2": 1.0,
         "cooking_eui_kwh_m2": 0.0, "refrigeration_eui_kwh_m2": 0.0,
         "dhw_gas_eui_kwh_m2": 4.0, "dhw_elec_eui_kwh_m2": 0.0, "dhw_district_eui_kwh_m2": dd,
         "dhw_eui_kwh_m2": 4.0 + dd}
    for c in DISTRICT_ZERO:
        r.setdefault(c, 0.0)
    r["total_eui_kwh_m2"] = heating + 5.0 + 10.0 + 20.0 + 3.0 + 1.0 + 4.0 + dd
    r["total_kwh"] = r["total_eui_kwh_m2"] * area
    r["gwp_total_kgco2"] = 0.0
    return r


def _raw_frame(heating_by_osm=None):
    heating_by_osm = heating_by_osm or {}
    return pd.DataFrame([_raw(o, c, g, a, heating_by_osm.get(o, h), dd) for o, c, g, a, h, dd in BUILDINGS])


@pytest.fixture()
def world(tmp_path):
    raw = _raw_frame()
    fixed, _ = rd.correct_table(raw)
    fleet = raw[["osm_id", "total_kwh", "floor_area_m2"]]
    dhw = fixed[["osm_id", "city", "cell", "floor_area_m2", "total_kwh", "gwp_total_kgco2", "dhw_district_removed_eui_kwh_m2"]]
    eui = float(fixed["total_kwh"].sum() / fixed["floor_area_m2"].sum())
    carbon = float(fixed["gwp_total_kgco2"].sum() / 1000.0)
    summary = {"corrected": {"pooled_eui_kwh_m2": eui, "carbon_t": carbon}, "population": {"buildings": 3}}
    paths = {k: tmp_path / f"{k}.csv" for k in ("fleet", "dhw", "cases", "out_csv")}
    fleet.to_csv(paths["fleet"], index=False)
    dhw.to_csv(paths["dhw"], index=False)
    paths["summary"] = tmp_path / "summary.json"
    paths["summary"].write_text(json.dumps(summary), encoding="utf-8")
    paths["out"] = tmp_path / "out"
    rows = []
    for cell in ("a", "b"):
        for o, c, g, *_ in BUILDINGS:
            rows.append({"cell": cell, "stem": o.replace("/", "_"), "osm_id": o, "city": c, "geo_cell": g})
    pd.DataFrame(rows).to_csv(paths["cases"], index=False)
    return {"paths": paths, "raw": raw, "fixed": fixed, "eui": eui, "carbon": carbon}


def _write_changed(out, cell, osm, heating):
    b = next(x for x in BUILDINGS if x[0] == osm)
    row = _raw(osm, b[1], b[2], b[3], heating, b[5])
    d = out / cell / osm.replace("/", "_")
    d.mkdir(parents=True)
    r = pd.DataFrame([row])
    r["parse_status"] = "success"
    r["completed"] = 1
    r.to_csv(d / "row.csv", index=False)


def _write_unchanged(out, cell, osm):
    d = out / cell / osm.replace("/", "_")
    d.mkdir(parents=True)
    (d / "UNCHANGED").write_text("", encoding="utf-8")


def _run(w):
    p = w["paths"]
    return rcb.run(p["cases"], p["out"], p["fleet"], p["dhw"], p["summary"], p["out_csv"])


def test_baseline_rows_equal_summary_and_reproduce_correction(world):
    p = world["paths"]
    base, checks = rcb.baseline_from_tables(pd.read_csv(p["fleet"], dtype={"osm_id": str}),
                                            pd.read_csv(p["dhw"], dtype={"osm_id": str}))
    eui, carbon = rcb.pooled(base)
    assert checks["rows"] == 3 and checks["osm_id_unique"]
    assert checks["t01_minus_removed_vs_corrected_max_rel"] < 1e-12
    assert abs(eui - world["eui"]) < 1e-9 * world["eui"]
    assert abs(carbon - world["carbon"]) < 1e-9 * world["carbon"]


def test_three_buildings_two_cells_one_unchanged(world):
    out = world["paths"]["out"]
    _write_changed(out, "a", "way/1", 40.0)
    _write_unchanged(out, "a", "way/2")
    _write_unchanged(out, "a", "way/3")
    for o, *_ in BUILDINGS:
        _write_unchanged(out, "b", o)
    assert _run(world) == 0
    res = pd.read_csv(world["paths"]["out_csv"])
    fleet_base = res[(res["scope"] == "fleet") & (res["cell"] == "baseline")].iloc[0]
    fleet_a = res[(res["scope"] == "fleet") & (res["cell"] == "a")].iloc[0]
    fleet_b = res[(res["scope"] == "fleet") & (res["cell"] == "b")].iloc[0]
    assert fleet_base["population"] == 3 and fleet_base["buildings_changed"] == 0
    assert abs(fleet_base["pooled_eui_kwh_m2"] - world["eui"]) < 1e-9 * world["eui"]
    assert fleet_a["buildings_changed"] == 1 and fleet_b["buildings_changed"] == 0
    assert abs(fleet_b["saving_kwh_m2"]) < 1e-12 and abs(fleet_b["saving_tco2e"]) < 1e-9
    expected_saving = 10.0 * 1000.0 / (1000.0 + 2000.0 + 500.0)
    assert abs(fleet_a["saving_kwh_m2"] - expected_saving) < 1e-9
    assert fleet_a["saving_tco2e"] > 0 and fleet_a["saving_pct"] > 0
    city_a = res[(res["scope"] == "city") & (res["cell"] == "a")].set_index("city")
    assert city_a.loc["nyc", "buildings_changed"] == 1 and city_a.loc["la", "buildings_changed"] == 0
    assert abs(city_a.loc["nyc", "saving_kwh_m2"] - 10.0) < 1e-9
    assert set(res["vintage"]) and (res["population"] > 0).all()


def test_changed_row_gets_the_dhw_correction(world):
    out = world["paths"]["out"]
    _write_changed(out, "a", "way/1", 50.0)
    _write_unchanged(out, "a", "way/2")
    _write_unchanged(out, "a", "way/3")
    for o, *_ in BUILDINGS:
        _write_unchanged(out, "b", o)
    assert _run(world) == 0
    res = pd.read_csv(world["paths"]["out_csv"])
    a = res[(res["scope"] == "fleet") & (res["cell"] == "a")].iloc[0]
    assert abs(a["saving_kwh_m2"]) < 1e-9
    assert abs(a["pooled_eui_kwh_m2"] - world["eui"]) < 1e-9 * world["eui"]


def test_missing_case_fails_and_writes_nothing(world):
    out = world["paths"]["out"]
    _write_changed(out, "a", "way/1", 40.0)
    _write_unchanged(out, "a", "way/2")
    for o, *_ in BUILDINGS:
        _write_unchanged(out, "b", o)
    assert _run(world) == 2
    assert not world["paths"]["out_csv"].exists()


def test_failed_parse_row_counts_as_missing(world):
    out = world["paths"]["out"]
    _write_changed(out, "a", "way/1", 40.0)
    csv = out / "a" / "way_1" / "row.csv"
    r = pd.read_csv(csv)
    r["completed"] = 0
    r.to_csv(csv, index=False)
    _write_unchanged(out, "a", "way/2")
    _write_unchanged(out, "a", "way/3")
    for o, *_ in BUILDINGS:
        _write_unchanged(out, "b", o)
    assert _run(world) == 2


def test_baseline_that_disagrees_with_summary_stops(world):
    p = world["paths"]
    s = json.loads(p["summary"].read_text())
    s["corrected"]["pooled_eui_kwh_m2"] *= 1.001
    p["summary"].write_text(json.dumps(s), encoding="utf-8")
    assert _run(world) == 1


def test_real_baseline_equals_the_dhw_fix_summary():
    fleet = pd.read_csv(rcb.FLEET_CSV, dtype={"osm_id": str})
    dhw = pd.read_csv(rcb.DHW_CSV, dtype={"osm_id": str})
    summary = json.loads(rcb.SUMMARY_JSON.read_text(encoding="utf-8"))
    base, checks = rcb.baseline_from_tables(fleet, dhw)
    eui, carbon = rcb.pooled(base)
    assert len(base) == 8139 and checks["osm_id_unique"]
    assert abs(eui - 154.0969) < 1e-6 * 154.0969 + 5e-5
    assert abs(carbon - 1037571.75) < 1e-6 * 1037571.75 + 0.005
    assert rcb.baseline_check(base, summary) == []
