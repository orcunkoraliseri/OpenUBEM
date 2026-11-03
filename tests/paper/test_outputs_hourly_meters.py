from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf import outputs

TEMPLATE = Path(__file__).resolve().parents[2] / "openubem" / "idf" / "templates" / "commercial_base.idf"
FIXTURES = Path(__file__).parent / "fixtures"
KINDS = ["OUTPUT:VARIABLE", "OUTPUT:METER:METERFILEONLY", "OUTPUT:METER", "OUTPUTCONTROL:TABLE:STYLE",
         "OUTPUT:TABLE:SUMMARYREPORTS", "OUTPUT:SQLITE"]


def _idf():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(str(TEMPLATE))


def _snapshot(idf):
    return "".join(str(o) for k in KINDS for o in idf.idfobjects[k])


def _key(obj):
    try:
        return obj.Key_Name
    except Exception:
        return obj.Name


def test_default_output_is_byte_identical_to_the_pre_change_snapshot():
    idf = _idf()
    outputs.write_outputs(idf)
    assert _snapshot(idf) == (FIXTURES / "outputs_default_snapshot.txt").read_text(encoding="utf-8")


def test_trimmed_default_output_is_byte_identical_to_the_pre_change_snapshot():
    idf = _idf()
    outputs.write_outputs(idf, trim_hourly=True)
    assert _snapshot(idf) == (FIXTURES / "outputs_default_trim_snapshot.txt").read_text(encoding="utf-8")


def test_flag_adds_exactly_one_hourly_meter_per_name():
    base = _idf()
    outputs.write_outputs(base)
    flagged = _idf()
    outputs.write_outputs(flagged, hourly_meters=True)
    before = len(base.idfobjects["OUTPUT:METER"])
    after = flagged.idfobjects["OUTPUT:METER"]
    assert len(after) - before == len(outputs.HOURLY_METERS)
    added = after[before:]
    assert [_key(m) for m in added] == list(outputs.HOURLY_METERS)
    assert {m.Reporting_Frequency for m in added} == {"Hourly"}
    assert len(flagged.idfobjects["OUTPUT:VARIABLE"]) == len(base.idfobjects["OUTPUT:VARIABLE"])


def test_hourly_meter_names_are_the_two_facility_meters_the_run_period_meters_and_the_district_one():
    names = outputs.HOURLY_METERS
    assert names[:2] == ("Electricity:Facility", "NaturalGas:Facility")
    assert set(outputs.HVAC_METERS) <= set(names)
    assert names[-1] == outputs.DISTRICT_HOT_WATER_METER == "WaterSystems:DistrictHeating"
    assert len(names) == len(set(names)) == 17
