"""Saved-IDF tests for X-06 heating-only and F_red controls."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.european_controls import add_european_heating_controls


@pytest.fixture(autouse=True)
def _idd() -> None:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))


@pytest.fixture
def fixture_idf(tmp_path):
    path = tmp_path / "fixture.idf"
    path.write_text("Version,23.1;\nZone,EU Zone;\n", encoding="utf-8")
    return IDF(str(path))


def _record() -> dict:
    path = Path(__file__).parent.parent / "openubem" / "data" / "construction" / "tabula_archetypes_es.json"
    return json.loads(path.read_text(encoding="utf-8"))["records"][0]


def test_saved_idf_has_heating_only_constant_air_and_all_convective_gains(fixture_idf, tmp_path):
    record = _record()
    result = add_european_heating_controls(fixture_idf, record, "EU Zone")
    saved_path = tmp_path / "saved.idf"
    fixture_idf.saveas(str(saved_path))
    saved = IDF(str(saved_path))
    ventilation = saved.getobject("ZONEVENTILATION:DESIGNFLOWRATE", result["ventilation"])
    gains = saved.getobject("OTHEREQUIPMENT", result["gains"])
    ideal = saved.getobject("HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM", "EU Zone")
    assert float(ventilation.Air_Changes_per_Hour) == pytest.approx(
        (record["n_air_use_h_1"] + record["n_air_infiltration_h_1"]) * record["f_red_temp"]
    )
    assert float(gains.Power_per_Zone_Floor_Area) == pytest.approx(3.0)
    assert (float(gains.Fraction_Latent), float(gains.Fraction_Radiant), float(gains.Fraction_Lost)) == (0, 0, 0)
    assert ideal.Cooling_Availability_Schedule_Name == result["cooling_off"]
    assert float(saved.getobject("SCHEDULE:CONSTANT", result["cooling_off"]).Hourly_Value) == 0.0
    assert result["u_multiplier"] == pytest.approx(record["f_red_temp"])
