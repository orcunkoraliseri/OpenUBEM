"""Tests for openubem.idf.outputs (T13)."""
from pathlib import Path

import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.outputs import STANDARD_OUTPUTS, HVAC_METERS, write_outputs

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


def _fresh_idf() -> IDF:
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


class TestOutputs:
    def test_output_variable_count(self):
        idf = _fresh_idf()
        write_outputs(idf)
        assert len(idf.idfobjects["OUTPUT:VARIABLE"]) == 11

    def test_all_hourly(self):
        idf = _fresh_idf()
        write_outputs(idf)
        for ov in idf.idfobjects["OUTPUT:VARIABLE"]:
            assert ov.Reporting_Frequency == "Hourly"

    def test_variable_names_match_standard_outputs(self):
        idf = _fresh_idf()
        write_outputs(idf)
        emitted = {ov.Variable_Name for ov in idf.idfobjects["OUTPUT:VARIABLE"]}
        expected = {v for v, _ in STANDARD_OUTPUTS}
        assert emitted == expected

    def test_meter_file_only_count_and_frequency(self):
        idf = _fresh_idf()
        write_outputs(idf)
        meters = idf.idfobjects["OUTPUT:METER:METERFILEONLY"]
        assert len(meters) == 2
        for m in meters:
            assert m.Reporting_Frequency == "RunPeriod"
        from eppy.bunch_subclass import BadEPFieldError

        def _meter_key(m):
            try:
                return m.Key_Name  # eppy >= 0.5.69
            except BadEPFieldError:
                return m.Name  # eppy < 0.5.69

        meter_names = {_meter_key(m) for m in meters}
        assert "Electricity:Facility" in meter_names
        assert "NaturalGas:Facility" in meter_names

    def test_single_objects(self):
        idf = _fresh_idf()
        write_outputs(idf)
        assert len(idf.idfobjects["OUTPUTCONTROL:TABLE:STYLE"]) == 1
        assert len(idf.idfobjects["OUTPUT:TABLE:SUMMARYREPORTS"]) == 1
        assert len(idf.idfobjects["OUTPUT:SQLITE"]) == 1

    def test_table_style_html(self):
        idf = _fresh_idf()
        write_outputs(idf)
        style = idf.idfobjects["OUTPUTCONTROL:TABLE:STYLE"][0]
        assert style.Column_Separator == "HTML"

    def test_sqlite_simple_and_tabular(self):
        idf = _fresh_idf()
        write_outputs(idf)
        sqlite = idf.idfobjects["OUTPUT:SQLITE"][0]
        assert sqlite.Option_Type == "SimpleAndTabular"

    def test_hvac_meters_count(self):
        assert len(HVAC_METERS) == 11

    def test_hvac_meters_phase_e_required(self):
        required = {
            "Pumps:Electricity",
            "WaterSystems:NaturalGas",
            "WaterSystems:Electricity",
            "Refrigeration:Electricity",
            "InteriorEquipment:NaturalGas",
            "Cooking:InteriorEquipment:Electricity",
            "Refrigeration:InteriorEquipment:Electricity",
        }
        assert required.issubset(set(HVAC_METERS))

    def test_hvac_meters_phase_d_retained(self):
        retained = {
            "Cooling:Electricity",
            "Heating:Electricity",
            "Heating:NaturalGas",
            "Fans:Electricity",
        }
        assert retained.issubset(set(HVAC_METERS))

    def test_output_meter_count(self):
        idf = _fresh_idf()
        write_outputs(idf)
        meters = idf.idfobjects["OUTPUT:METER"]
        assert len(meters) == 11
