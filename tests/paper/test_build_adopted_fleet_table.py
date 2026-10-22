import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "build_adopted_fleet_table.py"
_spec = importlib.util.spec_from_file_location("build_adopted_fleet_table", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def _row(osm, eui, area, gwp, cell="nyc_centre", **extra):
    d = {c: 0.0 for c in m.ENDUSES}
    d.update(cell=cell, osm_id=osm, archetype_id="SmallOffice", parse_status="success",
             floor_area_m2=area, total_eui_kwh_m2=eui, gwp_total_kgco2=gwp,
             data_quality_flag="")
    d.update(extra)
    return d


def test_overlays_replace_rows_and_tag_source():
    base = pd.DataFrame([_row("a", 100.0, 10.0, 1000.0, city="nyc"),
                         _row("b", 200.0, 10.0, 2000.0, city="nyc"),
                         _row("c", 300.0, 10.0, 3000.0, city="nyc")])
    t35 = pd.DataFrame([_row("b", 400.0, 20.0, 5000.0)])
    c38 = pd.DataFrame([_row("c", 50.0, 10.0, 500.0)])
    out = m.apply_overlays(base, t35, c38).set_index("osm_id")
    assert len(out) == 3
    assert out.loc["a", "source"] == "base"
    assert out.loc["b", "source"] == "open35"
    assert out.loc["c", "source"] == "open38"
    assert out.loc["b", "total_kwh"] == 8000.0
    eui, carbon = m.pooled(out.reset_index())
    assert abs(eui - (1000.0 + 8000.0 + 500.0) / (10.0 + 20.0 + 10.0)) < 1e-9
    assert abs(carbon - 6.5) < 1e-9


def test_open38_overlay_wins_over_open35():
    base = pd.DataFrame([_row("a", 100.0, 10.0, 1000.0, city="nyc")])
    t35 = pd.DataFrame([_row("a", 200.0, 10.0, 2000.0)])
    c38 = pd.DataFrame([_row("a", 300.0, 10.0, 3000.0)])
    out = m.apply_overlays(base, t35, c38)
    assert len(out) == 1 and out.iloc[0]["source"] == "open38" and out.iloc[0]["total_eui_kwh_m2"] == 300.0


def test_selectors():
    d35 = pd.DataFrame({"role": ["target", "control", "target"], "parse_status": ["success", "success", "failed"]})
    assert len(m.select_open35(d35)) == 1
    d38 = pd.DataFrame({"parse_status": ["success", "success", "failed"], "terminal": ["completed", "fatal", "completed"],
                        "group": ["cooking", "cooking", "cooking"], "mode": ["auto", "auto", "auto"]})
    assert len(m.select_open38(d38)) == 1
