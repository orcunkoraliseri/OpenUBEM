import json
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.elevators import assign_elevators

ELEVATORS_PATH = Path(__file__).parent.parent / "openubem/data/loads/elevators_by_archetype.json"
ARCHETYPES_PATH = Path(__file__).parent.parent / "openubem/data/openstudio_archetypes.json"
TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")


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


NO_ELEVATOR_ARCHETYPES = {
    "SmallOffice", "SmallOfficeDetailed", "RetailStandalone", "RetailStripmall",
    "Warehouse", "PrimarySchool", "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "LargeDataCenterHighITE", "LargeDataCenterLowITE", "TallBuilding", "SuperTallBuilding",
}


def _load_archetype_ids():
    data = json.loads(ARCHETYPES_PATH.read_text())
    return {e["archetype_id"] for e in data["archetypes"]}


def _load_elevators():
    return json.loads(ELEVATORS_PATH.read_text())


def test_elevators_file_exists():
    assert ELEVATORS_PATH.exists(), f"Missing: {ELEVATORS_PATH}"


def test_anchor_values_exact():
    data = _load_elevators()
    assert data["LargeOffice"]["design_level_w"] == 140025.3
    assert data["LargeHotel"]["design_level_w"] == 44860.63
    assert data["Hospital"]["design_level_w"] == 34667.95
    assert data["MediumOffice"]["design_level_w"] == 8517.82


def test_no_elevator_archetypes_absent():
    data = _load_elevators()
    for arc in ("SmallOffice", "Warehouse", "PrimarySchool"):
        assert arc not in data, f"{arc} should be absent from the elevator table"


def test_no_extra_archetype_keys():
    archetype_ids = _load_archetype_ids()
    data = _load_elevators()
    meta_keys = {k for k in data.keys() if k.startswith("_")}
    extra = set(data.keys()) - archetype_ids - meta_keys
    assert not extra, f"Elevators file has unexpected keys: {sorted(extra)}"


def test_prototype_floor_areas_positive():
    data = _load_elevators()
    for arc, row in data.items():
        if arc.startswith("_"):
            continue
        assert row["prototype_floor_area_m2"] > 0, f"{arc} prototype_floor_area_m2 <= 0"
        assert row["design_level_w"] > 0, f"{arc} design_level_w <= 0"


class TestElevatorsEmitter:
    def test_office_large_emits_one_electric_equipment(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 46320.38})
        assign_elevators(idf, row, [z])
        eqs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.EndUse_Subcategory == "Elevators"]
        assert len(eqs) == 1

    def test_office_large_design_level_matches_at_prototype_area(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 46320.38})
        assign_elevators(idf, row, [z])
        eq = idf.idfobjects["ELECTRICEQUIPMENT"][0]
        assert abs(float(eq.Design_Level) - 140025.3) < 1.0

    def test_small_office_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SmallOffice", "footprint_area_m2": 400.0})
        assign_elevators(idf, row, [z])
        assert not idf.idfobjects["ELECTRICEQUIPMENT"]

    def test_warehouse_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "Warehouse", "footprint_area_m2": 400.0})
        assign_elevators(idf, row, [z])
        assert not idf.idfobjects["ELECTRICEQUIPMENT"]

    def test_empty_zones_returns_empty_list(self):
        idf = _fresh_idf()
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 46320.38})
        result = assign_elevators(idf, row, [])
        assert result == []
        assert not idf.idfobjects["ELECTRICEQUIPMENT"]

    def test_design_level_scales_linearly_with_area(self):
        idf1 = _fresh_idf()
        z1 = _simple_zone(idf1)
        row1 = pd.Series({"archetype_id": "MediumOffice", "footprint_area_m2": 2000.0})
        assign_elevators(idf1, row1, [z1])
        level1 = float(idf1.idfobjects["ELECTRICEQUIPMENT"][0].Design_Level)

        idf2 = _fresh_idf()
        z2 = _simple_zone(idf2)
        row2 = pd.Series({"archetype_id": "MediumOffice", "footprint_area_m2": 4000.0})
        assign_elevators(idf2, row2, [z2])
        level2 = float(idf2.idfobjects["ELECTRICEQUIPMENT"][0].Design_Level)

        assert abs(level2 - 2 * level1) < 1.0

    def test_no_cap_above_prototype_area(self):
        """Unlike cooking's exhaust, elevator scaling has no cap (PLAN §3)."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        proto_area = _load_elevators()["MediumOffice"]["prototype_floor_area_m2"]
        row = pd.Series({"archetype_id": "MediumOffice", "footprint_area_m2": proto_area * 10})
        assign_elevators(idf, row, [z])
        level = float(idf.idfobjects["ELECTRICEQUIPMENT"][0].Design_Level)
        assert level > 8517.82 * 5

    def test_missing_footprint_provenance_token(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": None})
        flags = assign_elevators(idf, row, [z])
        assert any("GEOMETRY_AREA" in f for f in flags)

    def test_missing_floors_provenance_token(self):
        idf = _fresh_idf()
        z = {"name": "BLD_WHOLE"}  # no _F<n> floor index in name, no num_floors
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 46320.38})
        flags = assign_elevators(idf, row, [z])
        assert any("GEOMETRY_FLOORS" in f for f in flags)

    def test_schedule_compact_created(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "Hospital", "footprint_area_m2": 22436.18})
        assign_elevators(idf, row, [z])
        scheds = [s for s in idf.idfobjects["SCHEDULE:COMPACT"] if s.Name == "OpenUBEM_Elevators_Hospital"]
        assert len(scheds) == 1

    def test_heat_gain_fractions_transcribed_verbatim(self):
        """HighriseApartment source: Latent=0, Radiant=0, Lost=0.95 (not the office default)."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "HighriseApartment", "footprint_area_m2": 2350.94})
        assign_elevators(idf, row, [z])
        eq = idf.idfobjects["ELECTRICEQUIPMENT"][0]
        assert float(eq.Fraction_Radiant) == 0.0
        assert float(eq.Fraction_Lost) == 0.95

    @pytest.mark.parametrize("arc", sorted(NO_ELEVATOR_ARCHETYPES))
    def test_all_no_elevator_archetypes_emit_nothing(self, arc):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": arc, "footprint_area_m2": 1000.0})
        assign_elevators(idf, row, [z])
        assert not idf.idfobjects["ELECTRICEQUIPMENT"]
