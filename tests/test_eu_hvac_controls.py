"""EU-05 ruled residential heating/ventilation control tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.european_controls import add_european_heating_controls, european_air_change_per_hour


ROOT = Path(__file__).parents[1]
DATA_DIR = ROOT / "openubem" / "data" / "construction"


@pytest.fixture(autouse=True)
def _idd() -> None:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))


def _records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for country in ("es", "gb", "it", "fr"):
        payload = json.loads((DATA_DIR / f"tabula_archetypes_{country}.json").read_text(encoding="utf-8"))
        records.extend(payload["records"])
    return records


def _occupant_campaign_records() -> list[dict[str, object]]:
    return [record for record in _records() if record["country_stock_code"] in {"ES", "GB", "IT"}]


def test_all_frozen_records_emit_heating_only_all_convective_residential_controls(tmp_path: Path):
    """Audit every registry row, not merely the four S0 EnergyPlus fixtures."""
    records = _occupant_campaign_records()
    assert len(records) == 102
    for index, record in enumerate(records):
        path = tmp_path / f"controls_{index}.idf"
        path.write_text("Version,23.1;\nZone,EU Zone;\n", encoding="utf-8")
        idf = IDF(str(path))
        emitted = add_european_heating_controls(idf, record, "EU Zone")
        ventilation = idf.getobject("ZONEVENTILATION:DESIGNFLOWRATE", emitted["ventilation"])
        gains = idf.getobject("OTHEREQUIPMENT", emitted["gains"])
        ideal_loads = idf.getobject("HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM", "EU Zone")
        cooling_off = idf.getobject("SCHEDULE:CONSTANT", emitted["cooling_off"])
        assert float(ventilation.Air_Changes_per_Hour) == pytest.approx(european_air_change_per_hour(record))
        assert ventilation.Ventilation_Type == "Natural"
        assert float(gains.Power_per_Zone_Floor_Area) == pytest.approx(float(record["phi_int_w_m2"]))
        assert float(gains.Fraction_Latent) == 0.0
        assert float(gains.Fraction_Radiant) == 0.0
        assert float(gains.Fraction_Lost) == 0.0
        assert ideal_loads.Heating_Availability_Schedule_Name == emitted["always_on"]
        assert ideal_loads.Cooling_Availability_Schedule_Name == emitted["cooling_off"]
        assert float(cooling_off.Hourly_Value) == 0.0


def test_same_archetype_controls_are_distinct_per_zone(tmp_path: Path):
    record = _occupant_campaign_records()[0]
    path = tmp_path / "same_archetype_two_zones.idf"
    path.write_text("Version,23.1;\nZone,EU Zone;\nZone,EU Zone Two;\n", encoding="utf-8")
    idf = IDF(str(path))

    first = add_european_heating_controls(idf, record, "EU Zone")
    second = add_european_heating_controls(idf, record, "EU Zone Two")

    for key in ("always_on", "cooling_off", "thermostat", "ventilation", "gains"):
        assert first[key] != second[key] if key not in {"always_on", "cooling_off"} else first[key] == second[key]
    assert idf.getobject("ZONEVENTILATION:DESIGNFLOWRATE", first["ventilation"])
    assert idf.getobject("ZONEVENTILATION:DESIGNFLOWRATE", second["ventilation"])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"f_red_temp": 0.0}, "f_red_temp"),
        ({"f_red_temp": -0.5}, "f_red_temp"),
        ({"n_air_use_h_1": 0.0}, "n_air_use"),
        ({"n_air_infiltration_h_1": -0.1}, "infiltration"),
    ],
)
def test_air_change_validation_rejects_invalid_registry_values(overrides: dict[str, float], message: str):
    record = dict(_occupant_campaign_records()[0])
    record.update(overrides)
    with pytest.raises(ValueError, match=message):
        european_air_change_per_hour(record)


def test_fr_physical_row_with_f_red_temp_above_one_is_accepted_as_positive_multiplier():
    """Option 1 ruling: F_red_temp > 1.0 on FR.N.AB.10 is accepted as an exact positive source multiplier."""
    record = next(record for record in _records() if record["archetype_id"] == "FR.N.AB.10.Gen.ReEx.001.001")
    assert float(record["f_red_temp"]) > 1.0
    ach = european_air_change_per_hour(record)
    expected = (float(record["n_air_use_h_1"]) + float(record["n_air_infiltration_h_1"])) * float(record["f_red_temp"])
    assert ach == pytest.approx(expected)


def test_all_142_registry_records_have_valid_air_change():
    """All 142 records across ES, GB, IT, and FR compute air changes without error."""
    records = _records()
    assert len(records) == 142
    for record in records:
        ach = european_air_change_per_hour(record)
        assert ach > 0.0
