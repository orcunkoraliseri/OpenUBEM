import json
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.refrigeration import assign_refrigeration

CASES_PATH = Path(__file__).parent.parent / "openubem/data/refrigeration/supermarket_cases.json"
LUMPED_PATH = Path(__file__).parent.parent / "openubem/data/refrigeration/refrigeration_lumped.json"
TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
_BASE_TPL = str(TEMPLATES_DIR / "commercial_base.idf")

LUMPED_ARCHETYPES = {"FullServiceRestaurant", "QuickServiceRestaurant", "LargeHotel", "Hospital"}
EXPECTED_CASE_TYPES = {
    "LowTempFrozen", "MediumTempDairyDeli", "MediumTempMeat", "Produce",
    "LowTempIceCreamSpecialty",
}
RACK_TYPES = {"low_temp", "medium_temp"}


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


def _load_cases():
    return json.loads(CASES_PATH.read_text())


def _load_lumped():
    return json.loads(LUMPED_PATH.read_text())


def test_cases_file_exists():
    assert CASES_PATH.exists(), f"Missing: {CASES_PATH}"


def test_lumped_file_exists():
    assert LUMPED_PATH.exists(), f"Missing: {LUMPED_PATH}"


def test_lumped_coverage():
    lumped = _load_lumped()
    meta_keys = {"_schema", "_source", "_modeling_approach", "_note"}
    present = set(lumped.keys()) - meta_keys
    missing = LUMPED_ARCHETYPES - present
    assert not missing, f"Lumped refrigeration missing: {sorted(missing)}"


def test_lumped_no_extra_archetypes():
    lumped = _load_lumped()
    meta_keys = {"_schema", "_source", "_modeling_approach", "_note"}
    extra = (set(lumped.keys()) - meta_keys) - LUMPED_ARCHETYPES
    assert not extra, f"Unexpected lumped entries: {sorted(extra)}"


def test_lumped_eui_positive():
    lumped = _load_lumped()
    for arc in LUMPED_ARCHETYPES:
        eui = lumped[arc]["energy_intensity_kwh_m2_yr"]
        assert eui > 0, f"{arc} lumped EUI should be positive, got {eui}"


def test_lumped_site_share_plausible():
    lumped = _load_lumped()
    for arc in LUMPED_ARCHETYPES:
        share = lumped[arc]["site_energy_share_fraction"]
        assert 0 < share <= 0.20, f"{arc} site_energy_share_fraction {share} out of plausible range"


def test_cases_five_types():
    cases = _load_cases()
    found_types = {c["case_type"] for c in cases["cases"]}
    assert found_types == EXPECTED_CASE_TYPES, f"Expected case types {EXPECTED_CASE_TYPES}, got {found_types}"


def test_cases_five_case_sum_reference_length():
    cases = _load_cases()
    total = sum(c["reference_length_m"] for c in cases["cases"])
    assert abs(total - 89.3) < 0.1, f"5-case reference_length sum {total:.1f} != 89.3 m"


def test_cases_ratio_basis():
    cases = _load_cases()
    scaling = cases["_scaling"]
    ratio = scaling["case_mix_m_per_m2_floor_area"]
    store_area = scaling["reference_store_area_m2"]
    reference_total = scaling["reference_total_case_length_m"]
    assert abs(ratio - 0.021) < 0.0001, f"case_mix ratio != 0.021: {ratio}"
    assert abs(store_area - 4181) < 1, f"reference_store_area != 4181: {store_area}"
    computed = ratio * store_area
    assert abs(computed - reference_total) < 2.0, (
        f"ratio × area = {computed:.1f} m but reference_total = {reference_total} m "
        f"(gap = {reference_total - computed:.1f} m)"
    )


def test_cases_full_coverage():
    # R-CP-A-2: 5th case fills gap; listed == reference_total; coverage_fraction == 1.0
    cases = _load_cases()
    scaling = cases["_scaling"]
    listed = scaling["listed_case_length_m"]
    reference_total = scaling["reference_total_case_length_m"]
    assert abs(listed - reference_total) < 0.1, (
        f"listed_case_length ({listed} m) != reference_total ({reference_total} m) — expected full coverage"
    )
    assert abs(scaling["coverage_fraction"] - 1.0) < 0.001, (
        f"coverage_fraction {scaling['coverage_fraction']} != 1.0 after R-CP-A-2"
    )


def test_cases_rack_assignments():
    cases = _load_cases()
    for c in cases["cases"]:
        assert c["rack"] in RACK_TYPES, f"Case {c['case_type']} has unknown rack: {c['rack']}"


def test_cases_racks_cop_plausible():
    cases = _load_cases()
    racks = cases["_racks"]
    assert racks["low_temp"]["rack_cop"] == 1.50
    assert racks["medium_temp"]["rack_cop"] == 1.70


def test_cases_lhr_bounds():
    cases = _load_cases()
    for c in cases["cases"]:
        lhr = c["latent_heat_ratio"]
        assert 0 < lhr <= 0.35, f"Case {c['case_type']} LHR={lhr} out of [0,0.35]"


def test_cases_operating_temps_ordered():
    cases = _load_cases()
    frozen = next(c for c in cases["cases"] if c["case_type"] == "LowTempFrozen")
    produce = next(c for c in cases["cases"] if c["case_type"] == "Produce")
    assert frozen["operating_temp_c"] < produce["operating_temp_c"], (
        "Frozen case should be colder than produce"
    )


def test_zone_case_credit_values():
    cases = _load_cases()
    zcc = cases["_zone_case_credit"]
    assert abs(zcc["net_sales_floor_cooling_w_m2_sales"] - 15.5) < 0.1
    assert abs(zcc["net_total_floor_cooling_w_m2_total"] - 12.7) < 0.1
    assert abs(zcc["night_curtain_credit_reduction_fraction"] - 0.20) < 0.01


# --- T11 emitter tests ---

class TestRefrigerationEmitter:
    def test_supermarket_emits_cases(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        cases = idf.idfobjects["REFRIGERATION:CASE"]
        assert len(cases) == 5, f"Expected 5 cases, got {len(cases)}"

    def test_supermarket_emits_two_racks(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        racks = idf.idfobjects["REFRIGERATION:COMPRESSORRACK"]
        assert len(racks) == 2, f"Expected 2 racks, got {len(racks)}"

    def test_supermarket_case_lengths_scale_with_area(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        cases = idf.idfobjects["REFRIGERATION:CASE"]
        total_len = sum(float(c.Case_Length) for c in cases)
        expected = 0.021 * 4181.0
        assert abs(total_len - expected) < 1.0, (
            f"Total case length {total_len:.1f} m != expected {expected:.1f} m"
        )

    def test_supermarket_emits_caselist(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        lists = idf.idfobjects["REFRIGERATION:CASEANDWALKINLIST"]
        assert len(lists) == 2

    def test_fsr_emits_lumped_elec(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_refrigeration(idf, row, [z])
        ees = idf.idfobjects["ELECTRICEQUIPMENT"]
        refrig_ees = [e for e in ees if "Refrig" in e.Name]
        assert len(refrig_ees) == 1
        assert refrig_ees[0].EndUse_Subcategory == "Refrigeration"

    def test_lumped_elec_power_nonzero(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "FullServiceRestaurant", "footprint_area_m2": 400.0})
        assign_refrigeration(idf, row, [z])
        ees = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if "Refrig" in e.Name]
        assert float(ees[0].Design_Level) > 0

    def test_office_emits_nothing(self):
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "LargeOffice", "footprint_area_m2": 400.0})
        assign_refrigeration(idf, row, [z])
        assert not idf.idfobjects["REFRIGERATION:CASE"]
        refrig_ees = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if "Refrig" in e.Name]
        assert not refrig_ees

    def test_supermarket_emits_pulsed_defrost_schedules(self):
        """Three staggered SCHEDULE:COMPACT defrost schedules must be emitted (not constant 1.0)."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        sched_names = {s.Name for s in idf.idfobjects.get("SCHEDULE:COMPACT", [])}
        expected = {
            "OpenUBEM_DefrostSched_LowTemp",
            "OpenUBEM_DefrostSched_MedTemp",
            "OpenUBEM_DefrostSched_OffCycle",
        }
        assert expected.issubset(sched_names), (
            f"Missing pulsed defrost schedules: {expected - sched_names}"
        )

    def test_supermarket_no_constant_defrost_sched(self):
        """OpenUBEM_RefrigDefrost_Allowed constant schedule must NOT be emitted for SuperMarket."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        const_names = {s.Name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])}
        assert "OpenUBEM_RefrigDefrost_Allowed" not in const_names, (
            "Constant 1.0 defrost schedule found — causes continuous defrost (B-CP-B-1)"
        )

    def test_supermarket_cases_use_correct_defrost_schedules(self):
        """Each case must reference a staggered pulsed schedule, not a constant 1.0."""
        idf = _fresh_idf()
        z = _simple_zone(idf)
        row = pd.Series({"archetype_id": "SuperMarket", "footprint_area_m2": 4181.0})
        assign_refrigeration(idf, row, [z])
        valid_scheds = {
            "OpenUBEM_DefrostSched_LowTemp",
            "OpenUBEM_DefrostSched_MedTemp",
            "OpenUBEM_DefrostSched_OffCycle",
        }
        for case in idf.idfobjects["REFRIGERATION:CASE"]:
            sname = case.Case_Defrost_Schedule_Name
            assert sname in valid_scheds, (
                f"Case {case.Name} uses unexpected defrost schedule {sname!r}"
            )
