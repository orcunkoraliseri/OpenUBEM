import json
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.dhw import assign_dhw

DHW_PATH = Path(__file__).parent.parent / "openubem/data/loads/dhw_by_archetype.json"
ARCHETYPES_PATH = Path(__file__).parent.parent / "openubem/data/openstudio_archetypes.json"
TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")

VALID_FUELS = {"Electricity", "NaturalGas", None}
DATA_CENTERS = {
    "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "LargeDataCenterHighITE", "LargeDataCenterLowITE",
}


def _fresh_idf():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _simple_zone(idf, name="BLD_F0_WHOLE"):
    z = idf.newidfobject("ZONE")
    z.Name = name
    return {"name": name}


def _load_archetype_ids():
    data = json.loads(ARCHETYPES_PATH.read_text())
    return {e["archetype_id"] for e in data["archetypes"]}


def _load_dhw():
    return json.loads(DHW_PATH.read_text())


def test_dhw_file_exists():
    assert DHW_PATH.exists(), f"Missing: {DHW_PATH}"


def test_dhw_full_coverage():
    archetype_ids = _load_archetype_ids()
    dhw = _load_dhw()
    missing = archetype_ids - set(dhw.keys())
    assert not missing, f"DHW file missing archetypes: {sorted(missing)}"


def test_dhw_no_extra_keys():
    archetype_ids = _load_archetype_ids()
    dhw = _load_dhw()
    meta_keys = {"_schema", "_source", "_city_mains_temp", "_zone_gain", "_recirc_pump"}
    extra = set(dhw.keys()) - archetype_ids - meta_keys
    assert not extra, f"DHW file has unexpected keys: {sorted(extra)}"


def test_data_centers_zero_flow():
    dhw = _load_dhw()
    for dc in DATA_CENTERS:
        assert dhw[dc]["peak_flow_l_h_m2"] == 0.0, f"{dc} should have zero DHW flow"
        assert dhw[dc]["annual_hw_vol_l_m2_yr"] == 0.0


def test_data_centers_no_dhw_flag():
    dhw = _load_dhw()
    for dc in DATA_CENTERS:
        assert dhw[dc].get("no_dhw") is True, f"{dc} missing no_dhw=true"


def test_food_service_high_flow():
    dhw = _load_dhw()
    fsr = dhw["FullServiceRestaurant"]["peak_flow_l_h_m2"]
    qsr = dhw["QuickServiceRestaurant"]["peak_flow_l_h_m2"]
    assert fsr > 0.1, f"FSR peak flow unexpectedly low: {fsr}"
    assert qsr > 0.1, f"QSR peak flow unexpectedly low: {qsr}"


def test_recirc_flags_expected():
    dhw = _load_dhw()
    should_recirc = {
        "MidriseApartment", "HighriseApartment",
        "SmallHotel", "LargeHotel",
        "Hospital", "Outpatient",
        "FullServiceRestaurant",
        "SecondarySchool",
        "College",
        "Laboratory",
        "TallBuilding", "SuperTallBuilding",
    }
    for arc in should_recirc:
        assert dhw[arc]["recirc"] is True, f"{arc} should have recirc=true"


def test_non_recirc_offices():
    dhw = _load_dhw()
    for arc in ("SmallOffice", "SmallOfficeDetailed", "MediumOffice", "MediumOfficeDetailed",
                "LargeOffice", "LargeOfficeDetailed"):
        assert dhw[arc]["recirc"] is False, f"{arc} should have recirc=false"


def test_setpoint_60c_for_occupied():
    dhw = _load_dhw()
    for arc, row in dhw.items():
        if arc.startswith("_"):
            continue
        if row.get("no_dhw"):
            continue
        assert row["setpoint_c"] == 60.0, f"{arc} setpoint != 60°C"


def test_heater_fuel_valid():
    dhw = _load_dhw()
    for arc, row in dhw.items():
        if arc.startswith("_"):
            continue
        assert row["heater_fuel"] in VALID_FUELS, f"{arc} unknown fuel: {row['heater_fuel']}"


def test_peak_flow_non_negative():
    dhw = _load_dhw()
    for arc, row in dhw.items():
        if arc.startswith("_"):
            continue
        assert row["peak_flow_l_h_m2"] >= 0, f"{arc} negative peak flow"


def test_city_mains_temps():
    dhw = _load_dhw()
    mains = dhw["_city_mains_temp"]
    assert abs(mains["NYC_4A"]["annual_avg_c"] - 16.63) < 0.01
    assert abs(mains["LA_3B"]["annual_avg_c"] - 20.83) < 0.01
    assert abs(mains["Austin_2A"]["annual_avg_c"] - 23.73) < 0.01


def test_zone_gain_fractions():
    dhw = _load_dhw()
    zg = dhw["_zone_gain"]
    assert zg["sensible_fraction"] == 0.20
    assert zg["latent_fraction"] == 0.05
    assert zg["drain_fraction"] == 0.75


# --- T09 emitter tests ---

class TestDHWEmitter:
    def test_large_office_emits_gas_heater(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        heaters = idf.idfobjects["WATERHEATER:MIXED"]
        assert len(heaters) == 1
        assert heaters[0].Heater_Fuel_Type == "NaturalGas"
        assert abs(float(heaters[0].Heater_Thermal_Efficiency) - 0.808) < 0.001

    def test_large_office_flow_rate_positive(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        wh = idf.idfobjects["WATERHEATER:MIXED"][0]
        assert float(wh.Peak_Use_Flow_Rate) > 0

    def test_hriseapt_emits_gas_heater(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "HighriseApartment", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        heaters = idf.idfobjects["WATERHEATER:MIXED"]
        assert len(heaters) == 1
        assert heaters[0].Heater_Fuel_Type == "NaturalGas"

    def test_supermarket_emits_elec_heater(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        heaters = idf.idfobjects["WATERHEATER:MIXED"]
        assert len(heaters) == 1
        assert heaters[0].Heater_Fuel_Type == "Electricity"

    def test_datacenter_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SmallDataCenterHighITE", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        assert not idf.idfobjects["WATERHEATER:MIXED"]

    def test_water_use_equipment_emitted(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        assert len(idf.idfobjects["WATERUSE:EQUIPMENT"]) == 1
        assert len(idf.idfobjects["WATERUSE:CONNECTIONS"]) == 1

    def test_mains_temp_emitted_once(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        mains = idf.idfobjects["SITE:WATERMAINSTEMPERATURE"]
        assert len(mains) == 1
        assert mains[0].Calculation_Method == "CorrelationFromWeatherFile"

    def test_mains_temp_not_duplicated(self):
        # Two successive calls should still yield only one object
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        assign_dhw(idf, row, [z])
        assert len(idf.idfobjects["SITE:WATERMAINSTEMPERATURE"]) == 1

    def test_setpoint_schedule_60c(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf, row, [z])
        scheds = {s.Name: s for s in idf.idfobjects["SCHEDULE:CONSTANT"]}
        assert "OpenUBEM_DHW_Setpoint" in scheds
        assert float(scheds["OpenUBEM_DHW_Setpoint"].Hourly_Value) == 60.0

    def test_floor_area_scales_flow(self):
        idf1 = _fresh_idf()
        z1 = _simple_zone(idf1)
        row1 = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_dhw(idf1, row1, [z1])

        idf2 = _fresh_idf()
        z2 = _simple_zone(idf2)
        row2 = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 800.0})
        assign_dhw(idf2, row2, [z2])

        flow1 = float(idf1.idfobjects["WATERHEATER:MIXED"][0].Peak_Use_Flow_Rate)
        flow2 = float(idf2.idfobjects["WATERHEATER:MIXED"][0].Peak_Use_Flow_Rate)
        assert abs(flow2 / flow1 - 2.0) < 0.01
