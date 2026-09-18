"""Unit tests for openubem.scenarios.campaign (plan block-6 SCEN-01)."""

from itertools import permutations
from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.scenarios import campaign, measures

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass


def _blank_template_path():
    return Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"


def _make_compact_schedule(idf, name, sched_type, blocks, for_str="For: AllDays"):
    s = idf.newidfobject("SCHEDULE:COMPACT")
    s.Name = name
    s.Schedule_Type_Limits_Name = sched_type
    fields = ["Through: 12/31", for_str]
    for until, value in blocks:
        fields.append(f"Until: {until}")
        fields.append(value)
    for i, val in enumerate(fields, start=1):
        setattr(s, f"Field_{i}", val)
    return s


def _build_full_factorial_fixture():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(
        name="Zone1", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1,
    )
    idf.intersect_match()
    zone_name = idf.idfobjects["ZONE"][0].Name

    idf.newidfobject("SCHEDULE:CONSTANT", Name="AlwaysOn", Hourly_Value=1.0)
    idf.newidfobject(
        "LIGHTS", Name="Lights1", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="Watts/Area",
        Watts_per_Zone_Floor_Area=20.0,
    )

    _make_compact_schedule(
        idf, "HeatSched", "Temperature",
        [("05:00", 18.0), ("07:00", 18.0), ("22:00", 21.0), ("24:00", 18.0)],
    )
    _make_compact_schedule(
        idf, "CoolSched", "Temperature",
        [("05:00", 26.0), ("07:00", 26.0), ("22:00", 24.0), ("24:00", 26.0)],
    )
    idf.newidfobject(
        "THERMOSTATSETPOINT:DUALSETPOINT", Name="Tstat1",
        Heating_Setpoint_Temperature_Schedule_Name="HeatSched",
        Cooling_Setpoint_Temperature_Schedule_Name="CoolSched",
    )

    idf.newidfobject(
        "ZONEINFILTRATION:DESIGNFLOWRATE", Name="Infil1",
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Design_Flow_Rate_Calculation_Method="Flow/Area",
        Constant_Term_Coefficient=0.0, Temperature_Term_Coefficient=0.0,
        Velocity_Term_Coefficient=0.224, Velocity_Squared_Term_Coefficient=0.0,
        Flow_Rate_per_Floor_Area=0.01,
    )
    return idf


_ALL_THREE_MEASURE_IDS = (
    "lighting_power_density", "thermostat_setback", "infiltration_tightening",
)


def test_campaign_has_exactly_eight_cells_no_duplicates():
    cells = campaign.build_full_factorial_campaign()
    assert len(cells) == 8
    names = [c.name for c in cells]
    assert len(set(names)) == 8
    measure_sets = [frozenset(c.measure_ids) for c in cells]
    assert len(set(measure_sets)) == 8
    assert frozenset() in measure_sets
    assert frozenset(_ALL_THREE_MEASURE_IDS) in measure_sets


def test_campaign_covers_every_non_empty_subset_of_active_measures():
    cells = campaign.build_full_factorial_campaign()
    measure_sets = {frozenset(c.measure_ids) for c in cells}
    active = set(_ALL_THREE_MEASURE_IDS)
    expected = set()
    for r in range(len(active) + 1):
        for combo in permutations(active, r):
            expected.add(frozenset(combo))
    assert measure_sets == expected


def test_baseline_cell_is_named_baseline_and_empty():
    cells = campaign.build_full_factorial_campaign()
    baseline = next(c for c in cells if c.measure_ids == ())
    assert baseline.name == "baseline"


def test_all_three_cell_named_and_ordered_as_expected():
    cells = campaign.build_full_factorial_campaign()
    all_three = next(c for c in cells if frozenset(c.measure_ids) == frozenset(_ALL_THREE_MEASURE_IDS))
    assert all_three.name == "lighting+setback+infiltration"
    assert all_three.measure_ids == _ALL_THREE_MEASURE_IDS


def test_build_full_factorial_campaign_rejects_mismatched_active_table():
    table = measures.load_measures()
    table["lighting_power_density"] = dict(table["lighting_power_density"])
    table["lighting_power_density"]["status"] = "withdrawn"
    with pytest.raises(ValueError):
        campaign.build_full_factorial_campaign(table)


def test_all_three_cell_is_order_independent():
    all_three = next(
        c for c in campaign.build_full_factorial_campaign()
        if frozenset(c.measure_ids) == frozenset(_ALL_THREE_MEASURE_IDS)
    )
    results = []
    for order in permutations(all_three.measure_ids):
        idf = _build_full_factorial_fixture()
        for measure_id in order:
            measures.apply_measure(idf, measure_id, enabled=True, archetype="MediumOffice")
        results.append(idf.idfstr())
    assert all(r == results[0] for r in results)


def test_applying_a_cell_twice_matches_applying_it_once():
    all_three = next(
        c for c in campaign.build_full_factorial_campaign()
        if frozenset(c.measure_ids) == frozenset(_ALL_THREE_MEASURE_IDS)
    )
    idf = _build_full_factorial_fixture()
    campaign.apply_cell(idf, all_three, enabled=True, archetype="MediumOffice")
    once = idf.idfstr()
    campaign.apply_cell(idf, all_three, enabled=True, archetype="MediumOffice")
    twice = idf.idfstr()
    assert once == twice


def test_apply_cell_baseline_changes_nothing():
    baseline = next(c for c in campaign.build_full_factorial_campaign() if c.name == "baseline")
    idf = _build_full_factorial_fixture()
    before = idf.idfstr()
    summaries = campaign.apply_cell(idf, baseline, enabled=True, archetype="MediumOffice")
    after = idf.idfstr()
    assert summaries == []
    assert before == after
