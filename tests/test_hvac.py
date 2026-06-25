"""Tests for openubem.idf.hvac — Phase-D PTAC (T06).
Authorized deviation §0.1: IdealLoadsAirSystem replaced by PTAC.
"""
import json
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.hvac import assign_hvac, _load_cop_table

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")

COP_JSON = Path(__file__).parent.parent / "openubem" / "data" / "loads" / "hvac_cop_by_archetype.json"


def _fresh_idf() -> IDF:
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _make_zones(n: int, osm_id: str = "bldg") -> list[dict]:
    return [{"name": f"{osm_id}_F{i}_whole"} for i in range(n)]


def _make_row(archetype_id: str = "MediumOffice") -> pd.Series:
    return pd.Series({"archetype_id": archetype_id})


class TestPTACHVAC:
    def test_ptac_count_equals_zone_count(self):
        idf = _fresh_idf()
        zones = _make_zones(3)
        assign_hvac(idf, _make_row(), zones)
        ptac_objs = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"]
        assert len(ptac_objs) == 3

    def test_zone_and_thermostat_fields_present(self):
        idf = _fresh_idf()
        zones = _make_zones(1, "bld")
        assign_hvac(idf, _make_row(), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0]
        assert obj.Zone_Name == "bld_F0_whole"
        assert obj.Template_Thermostat_Name == "bld_F0_whole_Thermostat"

    def test_cop_pulled_from_json_medium_office(self):
        """MediumOffice PTAC COP matches hvac_cop_by_archetype.json."""
        idf = _fresh_idf()
        zones = _make_zones(1)
        assign_hvac(idf, _make_row("MediumOffice"), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0]
        expected_cop = COP_JSON.read_text()
        cop_data = json.loads(expected_cop)["MediumOffice"]["cooling_cop"]
        assert abs(float(obj.Cooling_Coil_Gross_Rated_Cooling_COP) - cop_data) < 1e-9

    def test_cop_pulled_from_json_large_hotel(self):
        """LargeHotel uses derated chiller COP (central-plant, §3.1)."""
        idf = _fresh_idf()
        zones = _make_zones(1)
        assign_hvac(idf, _make_row("LargeHotel"), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0]
        cop_data = json.loads(COP_JSON.read_text())["LargeHotel"]["cooling_cop"]
        assert abs(float(obj.Cooling_Coil_Gross_Rated_Cooling_COP) - cop_data) < 1e-9

    def test_gas_heating_coil_type(self):
        idf = _fresh_idf()
        zones = _make_zones(1)
        assign_hvac(idf, _make_row("MediumOffice"), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0]
        assert obj.Heating_Coil_Type == "Gas"

    def test_electric_heating_for_highrise(self):
        idf = _fresh_idf()
        zones = _make_zones(1)
        assign_hvac(idf, _make_row("HighriseApartment"), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"][0]
        assert obj.Heating_Coil_Type == "Electric"

    def test_thermostat_name_matches_zone(self):
        idf = _fresh_idf()
        zones = _make_zones(2)
        assign_hvac(idf, _make_row(), zones)
        objs = idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"]
        for obj, z in zip(objs, zones):
            assert obj.Template_Thermostat_Name == f"{z['name']}_Thermostat"

    def test_unknown_archetype_raises(self):
        idf = _fresh_idf()
        zones = _make_zones(1)
        with pytest.raises(KeyError, match="not found in hvac_cop_by_archetype"):
            assign_hvac(idf, pd.Series({"archetype_id": "NonExistentArchetype"}), zones)

    def test_cop_table_full_coverage(self):
        """JSON covers all 30 archetypes and every entry has a cooling_cop."""
        cop_table = _load_cop_table()
        assert len(cop_table) == 30
        for arch_id, entry in cop_table.items():
            if entry.get("fallback") or entry.get("non_dx"):
                continue
            cop = entry.get("cooling_cop")
            assert cop is not None, f"{arch_id}: cooling_cop is None"
            assert 2.0 <= cop <= 5.5, f"{arch_id}: cooling_cop {cop} outside [2.0, 5.5]"

    def test_no_ideal_loads_objects(self):
        """PTAC replaces IdealLoads — no IdealLoadsAirSystem objects should be created."""
        idf = _fresh_idf()
        zones = _make_zones(2)
        assign_hvac(idf, _make_row(), zones)
        ideal_objs = idf.idfobjects.get("HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM", [])
        assert len(ideal_objs) == 0
