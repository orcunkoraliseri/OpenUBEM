import json
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.cooking import assign_cooking

COOKING_PATH = Path(__file__).parent.parent / "openubem/data/loads/cooking_by_archetype.json"
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

FOOD_SERVICE = {"FullServiceRestaurant", "QuickServiceRestaurant"}
KITCHEN_ARCHETYPES = FOOD_SERVICE | {"LargeHotel", "Hospital", "SecondarySchool", "PrimarySchool", "College", "SuperMarket"}
NO_COOKING_OFFICES = {
    "SmallOffice", "SmallOfficeDetailed",
    "MediumOffice", "MediumOfficeDetailed",
    "LargeOffice", "LargeOfficeDetailed",
}
NO_COOKING_RESIDENTIAL = {"MidriseApartment", "HighriseApartment"}
VALID_HEAT_GAIN_KEYS = {
    "gas_hooded", "electric_hooded_fsr", "electric_hooded_qsr", "electric_unhooded", None
}


def _load_archetype_ids():
    data = json.loads(ARCHETYPES_PATH.read_text())
    return {e["archetype_id"] for e in data["archetypes"]}


def _load_cooking():
    return json.loads(COOKING_PATH.read_text())


def test_cooking_file_exists():
    assert COOKING_PATH.exists(), f"Missing: {COOKING_PATH}"


def test_cooking_full_coverage():
    archetype_ids = _load_archetype_ids()
    cooking = _load_cooking()
    meta_keys = {"_schema", "_source", "_basis", "_heat_gain_fractions"}
    missing = archetype_ids - set(cooking.keys())
    assert not missing, f"Cooking file missing archetypes: {sorted(missing)}"


def test_cooking_no_extra_keys():
    archetype_ids = _load_archetype_ids()
    cooking = _load_cooking()
    meta_keys = {"_schema", "_source", "_basis", "_heat_gain_fractions"}
    extra = set(cooking.keys()) - archetype_ids - meta_keys
    assert not extra, f"Cooking file has unexpected keys: {sorted(extra)}"


def test_food_service_nonzero():
    cooking = _load_cooking()
    for arc in FOOD_SERVICE:
        row = cooking[arc]
        assert not row.get("no_cooking"), f"{arc} should have cooking data"
        total = row["gas_density_w_m2"] + row["elec_density_w_m2"]
        assert total > 50.0, f"{arc} total cooking density unexpectedly low: {total}"


def test_offices_no_cooking():
    cooking = _load_cooking()
    for arc in NO_COOKING_OFFICES:
        assert cooking[arc].get("no_cooking") is True, f"{arc} should be no_cooking"


def test_residential_no_cooking():
    cooking = _load_cooking()
    for arc in NO_COOKING_RESIDENTIAL:
        assert cooking[arc].get("no_cooking") is True, f"{arc} should be no_cooking"


def test_data_centers_no_cooking():
    cooking = _load_cooking()
    for arc in ("SmallDataCenterHighITE", "SmallDataCenterLowITE",
                "LargeDataCenterHighITE", "LargeDataCenterLowITE"):
        assert cooking[arc].get("no_cooking") is True, f"{arc} should be no_cooking"


def test_kitchen_archetypes_have_densities():
    cooking = _load_cooking()
    for arc in KITCHEN_ARCHETYPES:
        row = cooking[arc]
        assert "gas_density_w_m2" in row, f"{arc} missing gas_density_w_m2"
        assert "elec_density_w_m2" in row, f"{arc} missing elec_density_w_m2"
        assert row.get("no_cooking") is not True, f"{arc} incorrectly flagged no_cooking"


def test_gas_elec_fractions_sum_to_one():
    cooking = _load_cooking()
    for arc in KITCHEN_ARCHETYPES:
        row = cooking[arc]
        total = row["gas_fraction"] + row["elec_fraction"]
        assert abs(total - 1.0) < 0.01, f"{arc} fractions sum to {total} not 1.0"


def test_fsr_exhaust_nonzero():
    cooking = _load_cooking()
    for arc in ("FullServiceRestaurant", "QuickServiceRestaurant"):
        assert cooking[arc]["exhaust_m3_s"] > 1.0, f"{arc} exhaust_m3_s suspiciously low"


def test_heat_gain_fractions_schema():
    cooking = _load_cooking()
    hgf = cooking["_heat_gain_fractions"]
    for key in ("gas_hooded", "electric_hooded_fsr", "electric_hooded_qsr", "electric_unhooded"):
        fracs = hgf[key]
        total = fracs["radiant"] + fracs["latent"] + fracs["lost"] + fracs["convective"]
        assert abs(total - 1.0) < 0.01, f"heat_gain_fractions.{key} sums to {total}"


def test_gas_hooded_fractions():
    cooking = _load_cooking()
    gh = cooking["_heat_gain_fractions"]["gas_hooded"]
    assert gh["radiant"] == 0.20
    assert gh["latent"] == 0.10
    assert gh["lost"] == 0.70
    assert gh["convective"] == 0.00


def test_fsr_qsr_exhaust_ratio():
    cooking = _load_cooking()
    fsr = cooking["FullServiceRestaurant"]["exhaust_l_s_m2_kitchen"]
    qsr = cooking["QuickServiceRestaurant"]["exhaust_l_s_m2_kitchen"]
    assert abs(fsr - 18.28) < 0.01, f"FSR exhaust density {fsr} != 18.28 L/s·m²"
    assert abs(qsr - 13.41) < 0.01, f"QSR exhaust density {qsr} != 13.41 L/s·m²"


# --- T10 emitter tests ---

class TestCookingEmitter:
    def test_fsr_emits_gas_and_elec(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        gas_eqs = idf.idfobjects["GASEQUIPMENT"]
        elec_eqs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.EndUse_Subcategory == "Cooking"]
        assert len(gas_eqs) == 1, f"Expected 1 GasEquipment, got {len(gas_eqs)}"
        assert len(elec_eqs) == 1, f"Expected 1 cooking ElectricEquipment, got {len(elec_eqs)}"

    def test_fsr_gas_subcategory_cooking(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        gas_eq = idf.idfobjects["GASEQUIPMENT"][0]
        assert gas_eq.EndUse_Subcategory == "Cooking"

    def test_fsr_emits_exhaust_ventilation(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        vents = idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"]
        assert len(vents) == 1
        assert vents[0].Ventilation_Type == "Exhaust"
        assert float(vents[0].Design_Flow_Rate) > 0

    def test_fsr_gas_level_scales_with_area(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        gas_eq = idf.idfobjects["GASEQUIPMENT"][0]
        # gas_density=83.76 W/m² × 400 m² = 33,504 W
        assert abs(float(gas_eq.Design_Level) - 83.76 * 400.0) < 1.0

    def test_office_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        assert not idf.idfobjects["GASEQUIPMENT"]
        cook_elec = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"]
                     if e.EndUse_Subcategory == "Cooking"]
        assert not cook_elec

    def test_apartment_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "HighriseApartment", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        assert not idf.idfobjects["GASEQUIPMENT"]

    def test_supermarket_elec_only(self):
        # SuperMarket has gas_density=0, elec_density=7.18 W/m²
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        assert not idf.idfobjects["GASEQUIPMENT"]
        cook_elec = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"]
                     if e.EndUse_Subcategory == "Cooking"]
        assert len(cook_elec) == 1

    def test_college_elec_only_no_exhaust(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "College", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        assert not idf.idfobjects["GASEQUIPMENT"]
        assert not idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"]

    def test_qsr_exhaust_flow_rate(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "QuickServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        vents = idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"]
        assert len(vents) == 1
        # RESULT_04 Table 3: QSR exhaust_m3_s=1.557; 400 m² ≥ QSR prototype 232 → capped at full
        assert abs(float(vents[0].Design_Flow_Rate) - 1.557) < 0.01

    # --- CP-R1 cooking-exhaust fix: area-scaling + operating schedule ---

    def test_exhaust_scaled_down_on_small_building(self):
        """Tiny PrimarySchool (56.6 m² « 6871 m² prototype) → exhaust scaled far below full.

        This is the CP-R1 root-cause fix: an unscaled 2.124 m³/s drove a ~36 kW make-up
        conditioning runaway on these single-zone schools.
        """
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "PrimarySchool", "footprint_area_m2": 56.6})
        assign_cooking(idf, row, [z])
        flow = float(idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"][0].Design_Flow_Rate)
        # 2.124 × 56.6/6871 ≈ 0.0175 m³/s — negligible, not the full 2.124
        assert flow < 0.05, f"expected scaled-down exhaust, got {flow}"

    def test_exhaust_capped_at_prototype_on_large_building(self):
        """FSR larger than its prototype is capped at the prototype exhaust (fan-out safety)."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 4000.0})
        assign_cooking(idf, row, [z])
        flow = float(idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"][0].Design_Flow_Rate)
        assert abs(flow - 2.549) < 0.01, f"expected cap at prototype 2.549, got {flow}"

    def test_exhaust_scales_linearly_below_prototype(self):
        """Below prototype size, exhaust scales linearly with floor area."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 100.0})
        assign_cooking(idf, row, [z])
        flow = float(idf.idfobjects["ZONEVENTILATION:DESIGNFLOWRATE"][0].Design_Flow_Rate)
        # 2.549 × 100/511 ≈ 0.499 m³/s
        assert abs(flow - 2.549 * 100.0 / 511.0) < 0.01, f"expected linear scaling, got {flow}"

    def test_exhaust_schedule_is_operating_window_not_constant(self):
        """Exhaust runs on a SCHEDULE:COMPACT operating window, not a 24/7 SCHEDULE:CONSTANT."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_cooking(idf, row, [z])
        compact = [s for s in idf.idfobjects["SCHEDULE:COMPACT"]
                   if s.Name == "OpenUBEM_Cook_ExhaustSched"]
        constant = [s for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])
                    if s.Name == "OpenUBEM_Cook_ExhaustSched"]
        assert len(compact) == 1, "exhaust must use a SCHEDULE:COMPACT operating window"
        assert not constant, "exhaust must no longer use a constant 24/7 schedule"
