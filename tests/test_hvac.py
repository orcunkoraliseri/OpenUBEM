"""Tests for openubem.idf.hvac (T12)."""
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.hvac import assign_hvac

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


def _fresh_idf() -> IDF:
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    return IDF(_BASE_TPL)


def _make_zones(n: int, osm_id: str = "bldg") -> list[dict]:
    return [{"name": f"{osm_id}_F{i}_whole"} for i in range(n)]


def _make_row() -> pd.Series:
    return pd.Series({"archetype_id": "MediumOffice"})


class TestHVAC:
    def test_three_zones_produce_three_objects(self):
        idf = _fresh_idf()
        zones = _make_zones(3)
        assign_hvac(idf, _make_row(), zones)
        hvac_objs = idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"]
        assert len(hvac_objs) == 3

    def test_zone_and_thermostat_fields_present(self):
        # eppy's bundled IDD v8.0.0 only exposes Zone_Name + Template_Thermostat_Name.
        # Extended fields (temperatures, flow rates) are present in EnergyPlus 23.1 IDD only.
        idf = _fresh_idf()
        zones = _make_zones(1, "bld")
        assign_hvac(idf, _make_row(), zones)
        obj = idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"][0]
        assert obj.Zone_Name == "bld_F0_whole"
        assert obj.Template_Thermostat_Name == "bld_F0_whole_Thermostat"

    def test_extended_defaults_applied_if_idd_permits(self):
        """Extended fields silently skipped when using bundled IDD — no exception raised."""
        idf = _fresh_idf()
        zones = _make_zones(1)
        assign_hvac(idf, _make_row(), zones)  # must not raise

    def test_thermostat_name_matches_zone(self):
        idf = _fresh_idf()
        zones = _make_zones(2)
        assign_hvac(idf, _make_row(), zones)
        objs = idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"]
        for obj, z in zip(objs, zones):
            assert obj.Template_Thermostat_Name == f"{z['name']}_Thermostat"
