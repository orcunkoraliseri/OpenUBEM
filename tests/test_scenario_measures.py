"""Unit tests for openubem.scenarios.measures (plan block-5 J02)."""

from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.scenarios import measures

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass


def _blank_template_path():
    return Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"


def _build_lights_fixture():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="Zone1", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    zone_name = idf.idfobjects["ZONE"][0].Name
    idf.newidfobject("SCHEDULE:CONSTANT", Name="AlwaysOn", Hourly_Value=1.0)

    high = idf.newidfobject(
        "LIGHTS", Name="LightsHigh", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="Watts/Area",
        Watts_per_Zone_Floor_Area=20.0,
    )
    low = idf.newidfobject(
        "LIGHTS", Name="LightsLow", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="Watts/Area",
        Watts_per_Zone_Floor_Area=3.0,
    )
    zero = idf.newidfobject(
        "LIGHTS", Name="LightsZero", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="Watts/Area",
        Watts_per_Zone_Floor_Area=0.0,
    )
    level = idf.newidfobject(
        "LIGHTS", Name="LightsLevel", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="LightingLevel",
        Lighting_Level=1000.0,
    )
    return idf, {"high": high, "low": low, "zero": zero, "level": level}


def _build_envelope_fixture(with_windows=True):
    idf = GeomIDF(str(_blank_template_path()))
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Wall_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.5, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Wall_Construction", Outside_Layer="Buffalo_Wall_Assembly")
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Roof_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.2, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Roof_Construction", Outside_Layer="Buffalo_Roof_Assembly")
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Floor_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.3, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Floor_Construction", Outside_Layer="Buffalo_Floor_Assembly")
    idf.newidfobject(
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", Name="Buffalo_Window_Material",
        UFactor=3.2, Solar_Heat_Gain_Coefficient=0.6, Visible_Transmittance=0.6,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Window_Construction", Outside_Layer="Buffalo_Window_Material")

    idf.add_block(name="Baseline", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    if with_windows:
        idf.set_wwr(wwr=0.3, construction="Buffalo_Window_Construction", force=True)

    surface_map = {
        "wall": "Buffalo_Wall_Construction", "roof": "Buffalo_Roof_Construction",
        "floor": "Buffalo_Floor_Construction", "ceiling": "Buffalo_Floor_Construction",
    }
    for surf in idf.getsurfaces():
        c = surface_map.get(surf.Surface_Type.lower())
        if c:
            surf.Construction_Name = c
    return idf


def _new_blank_idf():
    return GeomIDF(str(_blank_template_path()))


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


def _make_multiblock_schedule(idf, name, sched_type, field_tokens):
    s = idf.newidfobject("SCHEDULE:COMPACT")
    s.Name = name
    s.Schedule_Type_Limits_Name = sched_type
    fields = ["Through: 12/31"] + list(field_tokens)
    for i, val in enumerate(fields, start=1):
        setattr(s, f"Field_{i}", val)
    return s


_HTGSETP_SCH_YES_OPTIMUM_TOKENS = [
    "For: WinterDesignDay", "Until: 05:00", 15.6, "Until: 06:00", 17.6, "Until: 07:00", 19.6,
    "Until: 22:00", 21.0, "Until: 24:00", 15.6,
    "For: Weekdays", "Until: 05:00", 15.6, "Until: 06:00", 17.8, "Until: 07:00", 20.0,
    "Until: 22:00", 21.0, "Until: 24:00", 15.6,
    "For SummerDesignDay", "Until: 24:00", 15.6,
    "For: Saturday", "Until: 05:00", 15.6, "Until: 06:00", 17.8, "Until: 07:00", 20.0,
    "Until: 17:00", 21.0, "Until: 24:00", 15.6,
    "For:Sunday Holidays AllOtherDays", "Until: 24:00", 15.6,
]

_CLGSETP_SCH_YES_OPTIMUM_TOKENS = [
    "For: WinterDesignDay", "Until: 24:00", 26.7,
    "For: Weekdays", "Until: 05:00", 26.7, "Until: 06:00", 25.6, "Until: 07:00", 25.0,
    "Until: 22:00", 24.0, "Until: 24:00", 26.7,
    "For SummerDesignDay", "Until: 24:00", 26.7,
    "For: Saturday", "Until: 05:00", 26.7, "Until: 06:00", 25.6, "Until: 07:00", 25.0,
    "Until: 17:00", 24.0, "Until: 24:00", 26.7,
    "For:Sunday Holidays AllOtherDays", "Until: 24:00", 26.7,
]


def _build_thermostat_fixture(heating_blocks, cooling_blocks, heat_name="HeatSched", cool_name="CoolSched"):
    idf = _new_blank_idf()
    _make_compact_schedule(idf, heat_name, "Temperature", heating_blocks)
    _make_compact_schedule(idf, cool_name, "Temperature", cooling_blocks)
    t = idf.newidfobject(
        "THERMOSTATSETPOINT:DUALSETPOINT", Name="Tstat1",
        Heating_Setpoint_Temperature_Schedule_Name=heat_name,
        Cooling_Setpoint_Temperature_Schedule_Name=cool_name,
    )
    return idf, t


_DOE2_COEFFICIENTS = (0.0, 0.0, 0.224, 0.0)

_REAL_PROTOTYPE_OFFICESMALL_WALL_INFIL_M3_S_M2 = 0.0001993503
_REAL_PROTOTYPE_SCHOOL_DOOR_INFIL_M3_S = 5.114489639


def _build_infiltration_fixture(
    method, value, coefficients=_DOE2_COEFFICIENTS, name="TestInfiltration",
    coordinates=None, height=3.0, num_stories=1,
):
    idf = GeomIDF(str(_blank_template_path()))
    coords = coordinates or [(0, 0), (10, 0), (10, 10), (0, 10)]
    idf.add_block(name="InfilZone", coordinates=coords, height=height, num_stories=num_stories)
    idf.intersect_match()
    zone_name = idf.idfobjects["ZONE"][0].Name
    field_name = measures._INFILTRATION_METHOD_FIELDS[method.lower()][0]
    kwargs = {
        "Name": name,
        "Zone_or_ZoneList_or_Space_or_SpaceList_Name": zone_name,
        "Design_Flow_Rate_Calculation_Method": method,
        "Constant_Term_Coefficient": coefficients[0],
        "Temperature_Term_Coefficient": coefficients[1],
        "Velocity_Term_Coefficient": coefficients[2],
        "Velocity_Squared_Term_Coefficient": coefficients[3],
        field_name: value,
    }
    obj = idf.newidfobject("ZONEINFILTRATION:DESIGNFLOWRATE", **kwargs)
    return idf, obj, zone_name


def _add_infiltration_object(
    idf, zone_name, method, value, coefficients=_DOE2_COEFFICIENTS, name="TestInfiltration2",
):
    field_name = measures._INFILTRATION_METHOD_FIELDS[method.lower()][0]
    kwargs = {
        "Name": name,
        "Zone_or_ZoneList_or_Space_or_SpaceList_Name": zone_name,
        "Design_Flow_Rate_Calculation_Method": method,
        "Constant_Term_Coefficient": coefficients[0],
        "Temperature_Term_Coefficient": coefficients[1],
        "Velocity_Term_Coefficient": coefficients[2],
        "Velocity_Squared_Term_Coefficient": coefficients[3],
        field_name: value,
    }
    return idf.newidfobject("ZONEINFILTRATION:DESIGNFLOWRATE", **kwargs)


def test_load_measures_returns_both_ids_with_nonempty_source_for_active():
    table = measures.load_measures()
    assert set(table.keys()) == {
        "lighting_power_density", "envelope_u_upgrade", "thermostat_setback",
        "infiltration_tightening",
    }
    for measure_id, measure in table.items():
        if measure.get("status") == "active":
            assert measure.get("source")


def test_lighting_disabled_changes_nothing():
    idf, _ = _build_lights_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=False, archetype="MediumOffice")
    after = idf.idfstr()
    assert before == after
    assert summary["n_lowered"] >= 1
    assert summary["status"] == "disabled"


def test_envelope_withdrawn_apply_changes_nothing_and_reports_reason():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=False)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_envelope_withdrawn_apply_enabled_true_still_changes_nothing():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=True)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_applicable_measures_reports_envelope_withdrawn():
    idf = _build_envelope_fixture()
    result = measures.applicable_measures(idf)
    assert result["envelope_u_upgrade"]["applicable"] is False
    assert result["envelope_u_upgrade"]["status"] == "withdrawn"
    assert result["envelope_u_upgrade"]["withdrawn_reason"]


def test_lighting_applying_twice_matches_applying_once():
    idf, _ = _build_lights_fixture()
    measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    once = idf.idfstr()
    measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    twice = idf.idfstr()
    assert once == twice


def test_lighting_level_object_skipped_and_gate_named():
    idf, objs = _build_lights_fixture()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    entry = next(o for o in summary["objects"] if o["name"] == objs["level"].Name)
    assert entry["status"] == "skipped"
    assert entry["gate"] == "gate_lighting_method"
    assert objs["level"].Design_Level_Calculation_Method == "LightingLevel"
    assert float(objs["level"].Lighting_Level) == 1000.0


def test_zero_lpd_object_skipped_and_gate_named():
    idf, objs = _build_lights_fixture()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    entry = next(o for o in summary["objects"] if o["name"] == objs["zero"].Name)
    assert entry["status"] == "skipped"
    assert entry["gate"] == "gate_zero_lpd"
    assert float(objs["zero"].Watts_per_Zone_Floor_Area) == 0.0


def test_already_below_target_is_not_raised():
    idf, objs = _build_lights_fixture()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    entry = next(o for o in summary["objects"] if o["name"] == objs["low"].Name)
    assert entry["status"] == "already_compliant"
    assert float(objs["low"].Watts_per_Zone_Floor_Area) == pytest.approx(3.0)


def test_above_target_object_is_lowered_to_target():
    idf, objs = _build_lights_fixture()
    table = measures.load_measures()
    target = table["lighting_power_density"]["parameters"]["target_lpd_w_m2"]
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    entry = next(o for o in summary["objects"] if o["name"] == objs["high"].Name)
    assert entry["status"] == "lowered"
    assert float(objs["high"].Watts_per_Zone_Floor_Area) == pytest.approx(target)
    assert summary["status"] == "applied"


def test_lighting_out_of_scope_archetype_is_skipped():
    idf, objs = _build_lights_fixture()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="Hospital")
    assert summary["status"] == "gate_archetype_out_of_scope"
    assert summary["gate"] == "gate_archetype_out_of_scope"
    assert summary["objects"] == []
    assert float(objs["high"].Watts_per_Zone_Floor_Area) == pytest.approx(20.0)


def test_lighting_none_archetype_is_skipped():
    idf, objs = _build_lights_fixture()
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True)
    assert summary["status"] == "gate_archetype_out_of_scope"
    assert summary["gate"] == "gate_archetype_out_of_scope"
    assert float(objs["high"].Watts_per_Zone_Floor_Area) == pytest.approx(20.0)


def test_applicable_measures_lighting_archetype_gate():
    idf, _ = _build_lights_fixture()
    out_of_scope = measures.applicable_measures(idf, archetype="Hospital")
    assert out_of_scope["lighting_power_density"]["applicable"] is False
    assert out_of_scope["lighting_power_density"]["gate"] == "gate_archetype_out_of_scope"

    none_scope = measures.applicable_measures(idf)
    assert none_scope["lighting_power_density"]["applicable"] is False
    assert none_scope["lighting_power_density"]["gate"] == "gate_archetype_out_of_scope"

    in_scope = measures.applicable_measures(idf, archetype="MediumOffice")
    assert in_scope["lighting_power_density"]["applicable"] is True
    assert in_scope["lighting_power_density"]["gate"] is None


def test_all_applicable_lights_already_compliant_reports_already_compliant_not_applied():
    idf, objs = _build_lights_fixture()
    objs["high"].Watts_per_Zone_Floor_Area = 2.0
    summary = measures.apply_measure(idf, "lighting_power_density", enabled=True, archetype="MediumOffice")
    assert summary["n_lowered"] == 0
    assert summary["status"] == "already_compliant"
    assert summary["status"] != "applied"


def test_windowless_idf_reports_gate_no_fenestration_but_still_upgrades_opaque():
    idf = _build_envelope_fixture(with_windows=False)
    assert len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]) == 0
    table = measures.load_measures()
    target_wall = table["envelope_u_upgrade"]["parameters"]["u_wall_w_m2k"]
    summary = measures._apply_envelope_u_upgrade(idf, table["envelope_u_upgrade"], enabled=True)
    assert summary["window"]["gate"] == "gate_no_fenestration"
    assert summary["window"]["applied"] is False
    assert summary["wall"]["to_w_m2k"] == pytest.approx(target_wall)
    walls = [s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall"]
    assert walls
    for w in walls:
        assert w.Construction_Name == "LA_Wall_Construction"


def test_envelope_delegates_to_patch_envelope(monkeypatch):
    idf = _build_envelope_fixture()
    calls = []

    def _fake_patch_envelope(idf_arg, row, skip_when_better=False):
        calls.append((idf_arg, dict(row), skip_when_better))
        return idf_arg

    monkeypatch.setattr(
        "openubem.scenarios.measures.envelope_patcher.patch_envelope", _fake_patch_envelope
    )
    table = measures.load_measures()
    measures._apply_envelope_u_upgrade(idf, table["envelope_u_upgrade"], enabled=True)
    assert len(calls) == 1
    called_idf, called_row, called_skip = calls[0]
    assert called_idf is idf
    assert called_skip is True
    assert "u_wall_w_m2k" in called_row
    assert "u_window_w_m2k" in called_row


def test_clone_schedule_full_copy_and_independence():
    idf = _new_blank_idf()
    sched = _make_compact_schedule(
        idf, "SrcSched", "Temperature", [("07:00", 21.0), ("18:00", 21.0), ("24:00", 21.0)]
    )
    before = list(sched.fieldvalues)
    new_name = measures.clone_schedule(idf, "SrcSched", "SrcSched_clone")
    assert new_name == "SrcSched_clone"
    clones = [s for s in idf.idfobjects["SCHEDULE:COMPACT"] if s.Name == "SrcSched_clone"]
    assert len(clones) == 1
    clone = clones[0]
    assert list(sched.fieldvalues) == before
    assert len(clone.fieldvalues) == len(before)
    assert list(clone.fieldvalues[2:]) == list(before[2:])
    clone.Field_4 = 999.0
    assert float(sched.Field_4) == pytest.approx(21.0)
    assert list(sched.fieldvalues) == before


def test_clone_schedule_missing_source_raises():
    idf = _new_blank_idf()
    with pytest.raises(ValueError):
        measures.clone_schedule(idf, "NoSuchSchedule", "NoSuchSchedule_clone")


def test_thermostat_setback_clone_does_not_repoint_unrelated_references():
    idf = _new_blank_idf()
    idf.add_block(name="Zone1", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    zone_name = idf.idfobjects["ZONE"][0].Name
    shared = _make_compact_schedule(
        idf, "SharedHeatSched", "Temperature", [("07:00", 18.0), ("18:00", 21.0), ("24:00", 18.0)]
    )
    before_shared = list(shared.fieldvalues)
    _make_compact_schedule(
        idf, "CoolOkSched", "Temperature", [("07:00", 30.0), ("18:00", 24.0), ("24:00", 30.0)]
    )
    others = []
    for i in range(9):
        L = idf.newidfobject(
            "LIGHTS", Name=f"Lights{i}", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
            Schedule_Name="SharedHeatSched", Design_Level_Calculation_Method="Watts/Area",
            Watts_per_Zone_Floor_Area=5.0,
        )
        others.append(L)
    t = idf.newidfobject(
        "THERMOSTATSETPOINT:DUALSETPOINT", Name="Tstat1",
        Heating_Setpoint_Temperature_Schedule_Name="SharedHeatSched",
        Cooling_Setpoint_Temperature_Schedule_Name="CoolOkSched",
    )
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    assert summary["status"] == "applied"
    for L in others:
        assert L.Schedule_Name == "SharedHeatSched"
    shared_after = next(s for s in idf.idfobjects["SCHEDULE:COMPACT"] if s.Name == "SharedHeatSched")
    assert list(shared_after.fieldvalues) == before_shared
    assert t.Heating_Setpoint_Temperature_Schedule_Name != "SharedHeatSched"
    assert t.Heating_Setpoint_Temperature_Schedule_Name.startswith("SharedHeatSched__setback_")
    assert t.Cooling_Setpoint_Temperature_Schedule_Name == "CoolOkSched"
    clone_names = [s.Name for s in idf.idfobjects["SCHEDULE:COMPACT"]]
    assert clone_names.count(t.Heating_Setpoint_Temperature_Schedule_Name) == 1
    assert clone_names.count("SharedHeatSched") == 1


def test_constant_schedule_reports_gate_no_setback_block():
    idf, t = _build_thermostat_fixture(
        heating_blocks=[("07:00", 21.0), ("18:00", 21.0), ("24:00", 21.0)],
        cooling_blocks=[("07:00", 24.0), ("18:00", 24.0), ("24:00", 24.0)],
    )
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "gate_no_setback_block"
    assert summary["gate"] == "gate_no_setback_block"
    assert summary["n_gate_no_setback_block"] == 2
    for o in summary["objects"]:
        assert o["status"] == "gate_no_setback_block"
        assert o["gate"] == "gate_no_setback_block"
        assert o["magnitude_c"] == pytest.approx(0.0)
    assert t.Heating_Setpoint_Temperature_Schedule_Name == "HeatSched"
    assert t.Cooling_Setpoint_Temperature_Schedule_Name == "CoolSched"


def test_shallow_setback_is_deepened():
    idf, t = _build_thermostat_fixture(
        heating_blocks=[("05:00", 18.0), ("07:00", 18.0), ("22:00", 21.0), ("24:00", 18.0)],
        cooling_blocks=[("05:00", 26.0), ("07:00", 26.0), ("22:00", 24.0), ("24:00", 26.0)],
    )
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    assert summary["status"] == "applied"
    heat_obj = next(o for o in summary["objects"] if o["role"] == "heating")
    cool_obj = next(o for o in summary["objects"] if o["role"] == "cooling")
    assert heat_obj["status"] == "lowered"
    assert heat_obj["magnitude_c"] == pytest.approx(3.0)
    assert heat_obj["required_delta_c"] == pytest.approx(5.5556)
    assert cool_obj["status"] == "raised"
    assert cool_obj["magnitude_c"] == pytest.approx(2.0)
    assert cool_obj["required_delta_c"] == pytest.approx(2.7778)

    new_heat = next(s for s in idf.idfobjects["SCHEDULE:COMPACT"] if s.Name == t.Heating_Setpoint_Temperature_Schedule_Name)
    assert float(new_heat.Field_4) == pytest.approx(21.0 - 5.5556, abs=1e-3)
    assert float(new_heat.Field_6) == pytest.approx(21.0 - 5.5556, abs=1e-3)
    assert float(new_heat.Field_8) == pytest.approx(21.0)
    assert float(new_heat.Field_10) == pytest.approx(21.0 - 5.5556, abs=1e-3)

    new_cool = next(s for s in idf.idfobjects["SCHEDULE:COMPACT"] if s.Name == t.Cooling_Setpoint_Temperature_Schedule_Name)
    assert float(new_cool.Field_4) == pytest.approx(24.0 + 2.7778, abs=1e-3)
    assert float(new_cool.Field_6) == pytest.approx(24.0 + 2.7778, abs=1e-3)
    assert float(new_cool.Field_8) == pytest.approx(24.0)
    assert float(new_cool.Field_10) == pytest.approx(24.0 + 2.7778, abs=1e-3)


def test_already_deep_setback_reports_already_compliant_and_unchanged():
    idf, t = _build_thermostat_fixture(
        heating_blocks=[("07:00", 14.0), ("18:00", 21.0), ("24:00", 14.0)],
        cooling_blocks=[("07:00", 30.0), ("18:00", 24.0), ("24:00", 30.0)],
    )
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "already_compliant"
    for o in summary["objects"]:
        assert o["status"] == "already_compliant"


def test_thermostat_disabled_changes_nothing():
    idf, t = _build_thermostat_fixture(
        heating_blocks=[("05:00", 18.0), ("07:00", 18.0), ("22:00", 21.0), ("24:00", 18.0)],
        cooling_blocks=[("05:00", 26.0), ("07:00", 26.0), ("22:00", 24.0), ("24:00", 26.0)],
    )
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=False)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "disabled"
    assert summary["n_applied"] >= 1


def test_thermostat_applying_twice_matches_applying_once():
    idf, t = _build_thermostat_fixture(
        heating_blocks=[("05:00", 18.0), ("07:00", 18.0), ("22:00", 21.0), ("24:00", 18.0)],
        cooling_blocks=[("05:00", 26.0), ("07:00", 26.0), ("22:00", 24.0), ("24:00", 26.0)],
    )
    table = measures.load_measures()
    measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    once = idf.idfstr()
    measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    twice = idf.idfstr()
    assert once == twice


def test_no_thermostat_reports_gate_no_thermostat():
    idf = _new_blank_idf()
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    assert summary["status"] == "gate_no_thermostat"
    assert summary["gate"] == "gate_no_thermostat"
    assert summary["objects"] == []


def test_thermostat_missing_schedule_reports_gate_schedule_missing():
    idf = _new_blank_idf()
    t = idf.newidfobject(
        "THERMOSTATSETPOINT:DUALSETPOINT", Name="Tstat1",
        Heating_Setpoint_Temperature_Schedule_Name="DoesNotExistHeat",
        Cooling_Setpoint_Temperature_Schedule_Name="DoesNotExistCool",
    )
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    assert summary["status"] == "gate_schedule_missing"
    assert summary["gate"] == "gate_schedule_missing"
    assert summary["n_gate_schedule_missing"] == 2
    for o in summary["objects"]:
        assert o["status"] == "gate_schedule_missing"
        assert o["gate"] == "gate_schedule_missing"


def test_envelope_withdrawn_apply_changes_nothing_and_reports_reason_generic_path():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=False)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_envelope_withdrawn_apply_enabled_true_still_changes_nothing_generic_path():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=True)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_applicable_measures_reports_envelope_withdrawn_generic_path():
    idf = _new_blank_idf()
    result = measures.applicable_measures(idf)
    assert result["envelope_u_upgrade"]["applicable"] is False
    assert result["envelope_u_upgrade"]["status"] == "withdrawn"
    assert result["envelope_u_upgrade"]["withdrawn_reason"]


def test_real_prototype_setpoint_schedules_deepened_not_disabled():
    idf = _new_blank_idf()
    heat_sched = _make_multiblock_schedule(
        idf, "HTGSETP_SCH_YES_OPTIMUM", "Temperature", _HTGSETP_SCH_YES_OPTIMUM_TOKENS
    )
    cool_sched = _make_multiblock_schedule(
        idf, "CLGSETP_SCH_YES_OPTIMUM", "Temperature", _CLGSETP_SCH_YES_OPTIMUM_TOKENS
    )
    before_heat = list(heat_sched.fieldvalues)
    before_cool = list(cool_sched.fieldvalues)
    t = idf.newidfobject(
        "THERMOSTATSETPOINT:DUALSETPOINT", Name="Tstat1",
        Heating_Setpoint_Temperature_Schedule_Name="HTGSETP_SCH_YES_OPTIMUM",
        Cooling_Setpoint_Temperature_Schedule_Name="CLGSETP_SCH_YES_OPTIMUM",
    )
    table = measures.load_measures()
    summary = measures._apply_thermostat_setback(idf, table["thermostat_setback"], enabled=True)
    assert summary["status"] == "applied"

    assert list(heat_sched.fieldvalues) == before_heat
    assert list(cool_sched.fieldvalues) == before_cool

    new_heat = next(
        s for s in idf.idfobjects["SCHEDULE:COMPACT"]
        if s.Name == t.Heating_Setpoint_Temperature_Schedule_Name
    )
    new_cool = next(
        s for s in idf.idfobjects["SCHEDULE:COMPACT"]
        if s.Name == t.Cooling_Setpoint_Temperature_Schedule_Name
    )

    assert float(new_heat.Field_10) == pytest.approx(21.0)
    assert float(new_heat.Field_21) == pytest.approx(21.0)
    assert float(new_heat.Field_26) == pytest.approx(15.6)
    assert float(new_heat.Field_17) == pytest.approx(17.8)
    assert float(new_heat.Field_19) == pytest.approx(20.0)
    assert float(new_heat.Field_15) == pytest.approx(21.0 - 5.5556, abs=1e-3)
    assert float(new_heat.Field_23) == pytest.approx(21.0 - 5.5556, abs=1e-3)
    assert float(new_heat.Field_29) == pytest.approx(15.6)
    assert float(new_heat.Field_35) == pytest.approx(21.0)
    assert float(new_heat.Field_37) == pytest.approx(15.6)
    assert float(new_heat.Field_40) == pytest.approx(15.6)

    assert float(new_cool.Field_4) == pytest.approx(26.7)
    assert float(new_cool.Field_13) == pytest.approx(24.0)
    assert float(new_cool.Field_18) == pytest.approx(26.7)
    assert float(new_cool.Field_9) == pytest.approx(25.6)
    assert float(new_cool.Field_11) == pytest.approx(25.0)
    assert float(new_cool.Field_7) == pytest.approx(24.0 + 2.7778, abs=1e-3)
    assert float(new_cool.Field_15) == pytest.approx(24.0 + 2.7778, abs=1e-3)
    assert float(new_cool.Field_21) == pytest.approx(26.7)
    assert float(new_cool.Field_27) == pytest.approx(24.0)
    assert float(new_cool.Field_29) == pytest.approx(26.7)
    assert float(new_cool.Field_32) == pytest.approx(26.7)

    heat_obj = next(o for o in summary["objects"] if o["role"] == "heating")
    cool_obj = next(o for o in summary["objects"] if o["role"] == "cooling")
    assert heat_obj["magnitude_c"] == pytest.approx(21.0 - 15.6, abs=1e-6)
    assert heat_obj["status"] == "lowered"
    assert cool_obj["magnitude_c"] == pytest.approx(26.7 - 24.0, abs=1e-6)
    assert cool_obj["status"] == "raised"


def test_envelope_withdrawn_apply_changes_nothing_and_reports_reason_j04c_slot():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=False)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_envelope_withdrawn_apply_enabled_true_still_changes_nothing_j04c_slot():
    idf = _build_envelope_fixture()
    before = idf.idfstr()
    summary = measures.apply_measure(idf, "envelope_u_upgrade", enabled=True)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "withdrawn"
    assert summary["withdrawn_reason"]


def test_applicable_measures_reports_envelope_withdrawn_j04c_slot():
    idf = _build_envelope_fixture()
    result = measures.applicable_measures(idf)
    assert result["envelope_u_upgrade"]["applicable"] is False
    assert result["envelope_u_upgrade"]["status"] == "withdrawn"
    assert result["envelope_u_upgrade"]["withdrawn_reason"]


def test_infiltration_no_objects_reports_gate_no_infiltration_objects():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="Zone1", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    assert summary["status"] == "gate_no_infiltration_objects"
    assert summary["gate"] == "gate_no_infiltration_objects"
    assert summary["objects"] == []


def test_infiltration_no_geometry_reports_gate_no_geometry():
    idf = _new_blank_idf()
    zone = idf.newidfobject("ZONE", Name="Z1")
    idf.newidfobject(
        "ZONEINFILTRATION:DESIGNFLOWRATE", Name="Infil1",
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone.Name,
        Design_Flow_Rate_Calculation_Method="Flow/Zone", Design_Flow_Rate=1.0,
        Constant_Term_Coefficient=0.0, Temperature_Term_Coefficient=0.0,
        Velocity_Term_Coefficient=0.224, Velocity_Squared_Term_Coefficient=0.0,
    )
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    assert summary["status"] == "gate_no_geometry"
    assert summary["gate"] == "gate_no_geometry"
    assert summary["envelope_area_s_m2"] == 0.0


def test_infiltration_unknown_method_is_gated_and_unchanged():
    idf, obj, _ = _build_infiltration_fixture("Flow/Zone", 0.05)
    obj.Design_Flow_Rate_Calculation_Method = "AirChanges/Hour"
    obj.Air_Changes_per_Hour = 2.0
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    entry = next(o for o in summary["objects"] if o["name"] == "TestInfiltration")
    assert entry["status"] == "gate_unknown_calculation_method"
    assert entry["gate"] == "gate_unknown_calculation_method"
    assert summary["n_gate_unknown_calculation_method"] == 1


def test_infiltration_unsupported_coefficients_gated_and_unchanged():
    idf, _, _ = _build_infiltration_fixture("Flow/Area", 0.05, coefficients=(1.0, 0.0, 0.0, 0.0))
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    entry = summary["objects"][0]
    assert entry["status"] == "gate_unsupported_coefficients"
    assert entry["gate"] == "gate_unsupported_coefficients"
    assert entry["coefficients"] == [1.0, 0.0, 0.0, 0.0]
    assert summary["n_gate_unsupported_coefficients"] == 1


def test_infiltration_zero_exterior_area_object_gated_not_divided_by_zero():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="OuterZone", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    interior_zone = idf.newidfobject("ZONE", Name="InteriorZone")
    _add_infiltration_object(
        idf, interior_zone.Name, "Flow/ExteriorWallArea", 0.001, name="InteriorInfil",
    )
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    interior_entry = next(o for o in summary["objects"] if o["name"] == "InteriorInfil")
    assert interior_entry["status"] == "gate_zero_normalizing_area"
    assert interior_entry["gate"] == "gate_zero_normalizing_area"
    assert summary["n_gate_zero_normalizing_area"] == 1
    assert summary["exterior_wall_area_aagw_m2"] == 0.0


def test_infiltration_already_tighter_object_is_unchanged():
    idf, _, _ = _build_infiltration_fixture("Flow/Area", 0.0000001)
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    entry = summary["objects"][0]
    assert entry["status"] == "already_compliant"
    assert summary["n_already_compliant"] == 1
    assert summary["n_tightened"] == 0


def test_infiltration_disabled_changes_nothing():
    idf, _, _ = _build_infiltration_fixture("Flow/Area", 5.0)
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=False)
    after = idf.idfstr()
    assert before == after
    assert summary["status"] == "disabled"
    assert summary["n_tightened"] >= 1


def test_infiltration_applying_twice_matches_applying_once():
    idf, _, _ = _build_infiltration_fixture("Flow/Area", 5.0)
    table = measures.load_measures()
    measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    once = idf.idfstr()
    measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    twice = idf.idfstr()
    assert once == twice


def test_infiltration_flow_area_writes_correct_units_and_never_increases():
    idf, obj, zone_name = _build_infiltration_fixture("Flow/Area", 0.01)
    existing_declared = float(obj.Flow_Rate_per_Floor_Area)
    floor_area = measures._zone_area_for_kind(idf, zone_name, "floor")
    existing_abs = existing_declared * floor_area
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    entry = summary["objects"][0]
    assert entry["status"] == "tightened"
    assert obj.Design_Flow_Rate_Calculation_Method.lower() == "flow/area"
    new_declared = float(obj.Flow_Rate_per_Floor_Area)
    new_abs = new_declared * floor_area
    assert new_abs == pytest.approx(entry["new_flow_m3_s"], abs=1e-9)
    assert new_abs <= existing_abs + 1e-9


def test_infiltration_exteriorwallarea_writes_correct_units_and_never_increases():
    idf, obj, zone_name = _build_infiltration_fixture("Flow/ExteriorWallArea", 0.01)
    existing_declared = float(obj.Flow_Rate_per_Exterior_Surface_Area)
    wall_area = measures._zone_area_for_kind(idf, zone_name, "exterior_wall")
    existing_abs = existing_declared * wall_area
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    entry = summary["objects"][0]
    assert entry["status"] == "tightened"
    assert obj.Design_Flow_Rate_Calculation_Method.lower() == "flow/exteriorwallarea"
    new_declared = float(obj.Flow_Rate_per_Exterior_Surface_Area)
    new_abs = new_declared * wall_area
    assert new_abs == pytest.approx(entry["new_flow_m3_s"], abs=1e-9)
    assert new_abs <= existing_abs + 1e-9


def test_infiltration_ela_and_flowcoefficient_objects_reported_as_unknown_method():
    idf, _, zone_name = _build_infiltration_fixture("Flow/Zone", 0.0000001)
    idf.newidfobject(
        "ZONEINFILTRATION:EFFECTIVELEAKAGEAREA", Name="ELA1",
        Zone_or_Space_Name=zone_name, Effective_Air_Leakage_Area=100.0,
    )
    idf.newidfobject(
        "ZONEINFILTRATION:FLOWCOEFFICIENT", Name="FC1",
        Zone_or_Space_Name=zone_name, Flow_Coefficient=0.5, Stack_Coefficient=0.001,
    )
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    unknown_names = {
        o["name"] for o in summary["objects"] if o["status"] == "gate_unknown_calculation_method"
    }
    assert {"ELA1", "FC1"}.issubset(unknown_names)
    assert summary["n_gate_unknown_calculation_method"] == 2


def test_infiltration_flow_area_uniform_intensity_applied_building_wide():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="ZoneA", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.add_block(name="ZoneB", coordinates=[(20, 0), (30, 0), (30, 10), (20, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    zones = idf.idfobjects["ZONE"]
    assert len(zones) == 2
    for i, z in enumerate(zones):
        _add_infiltration_object(idf, z.Name, "Flow/Area", 5.0, name=f"Infil{i}")
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    assert summary["n_tightened"] == 2
    assert summary["n_already_compliant"] == 0
    assert summary["n_gate_unknown_calculation_method"] == 0
    assert summary["n_gate_unsupported_calculation_method"] == 0
    assert summary["n_gate_zero_normalizing_area"] == 0
    assert summary["n_gate_unsupported_coefficients"] == 0
    expected_i_flr = (
        summary["conversion_factor"] * summary["i75pa_target_m3_s_m2"]
        * summary["envelope_area_s_m2"] / summary["floor_area_aflr_m2"]
    )
    for obj in idf.idfobjects["ZONEINFILTRATION:DESIGNFLOWRATE"]:
        assert float(obj.Flow_Rate_per_Floor_Area) == pytest.approx(expected_i_flr, abs=1e-9)


def test_infiltration_exteriorwallarea_uniform_intensity_applied_building_wide():
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="ZoneA", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.add_block(name="ZoneB", coordinates=[(20, 0), (30, 0), (30, 10), (20, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    zones = idf.idfobjects["ZONE"]
    assert len(zones) == 2
    for i, z in enumerate(zones):
        _add_infiltration_object(idf, z.Name, "Flow/ExteriorWallArea", 5.0, name=f"Infil{i}")
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    assert summary["n_tightened"] == 2
    assert summary["n_already_compliant"] == 0
    assert summary["n_gate_unknown_calculation_method"] == 0
    assert summary["n_gate_unsupported_calculation_method"] == 0
    assert summary["n_gate_zero_normalizing_area"] == 0
    assert summary["n_gate_unsupported_coefficients"] == 0
    expected_i_agw = (
        summary["conversion_factor"] * summary["i75pa_target_m3_s_m2"]
        * summary["envelope_area_s_m2"] / summary["exterior_wall_area_aagw_m2"]
    )
    for obj in idf.idfobjects["ZONEINFILTRATION:DESIGNFLOWRATE"]:
        assert float(obj.Flow_Rate_per_Exterior_Surface_Area) == pytest.approx(expected_i_agw, abs=1e-9)


def test_infiltration_flow_zone_and_exteriorarea_gated_unsupported_calculation_method():
    idf, _, zone_name = _build_infiltration_fixture("Flow/Zone", 1.0)
    _add_infiltration_object(idf, zone_name, "Flow/ExteriorArea", 0.001, name="ExtAreaInfil")
    before = idf.idfstr()
    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)
    after = idf.idfstr()
    assert before == after
    zone_entry = next(o for o in summary["objects"] if o["name"] == "TestInfiltration")
    ext_entry = next(o for o in summary["objects"] if o["name"] == "ExtAreaInfil")
    assert zone_entry["status"] == "gate_unsupported_calculation_method"
    assert zone_entry["gate"] == "gate_unsupported_calculation_method"
    assert ext_entry["status"] == "gate_unsupported_calculation_method"
    assert ext_entry["gate"] == "gate_unsupported_calculation_method"
    assert summary["n_gate_unsupported_calculation_method"] == 2


def test_real_prototype_infiltration_objects_only_ever_tighten():
    idf, wall_obj, zone_a = _build_infiltration_fixture(
        "Flow/ExteriorWallArea", _REAL_PROTOTYPE_OFFICESMALL_WALL_INFIL_M3_S_M2,
        name="Perimeter_ZN_1_Infiltration",
        coordinates=[(0, 0), (20, 0), (20, 15), (0, 15)],
    )
    idf.add_block(name="LobbyZone", coordinates=[(30, 0), (36, 0), (36, 6), (30, 6)], height=3.0, num_stories=1)
    idf.intersect_match()
    lobby_zone = next(z.Name for z in idf.idfobjects["ZONE"] if z.Name != zone_a)
    door_obj = _add_infiltration_object(
        idf, lobby_zone, "Flow/Zone", _REAL_PROTOTYPE_SCHOOL_DOOR_INFIL_M3_S,
        name="Lobby_ZN_1_FLR_1_Door_Infiltration",
    )
    existing_wall_declared = _REAL_PROTOTYPE_OFFICESMALL_WALL_INFIL_M3_S_M2
    existing_door_flow = _REAL_PROTOTYPE_SCHOOL_DOOR_INFIL_M3_S

    table = measures.load_measures()
    summary = measures._apply_infiltration_tightening(idf, table["infiltration_tightening"], enabled=True)

    assert summary["n_gate_unknown_calculation_method"] == 0
    assert summary["n_gate_zero_normalizing_area"] == 0
    assert summary["n_gate_unsupported_coefficients"] == 0
    assert summary["n_gate_unsupported_calculation_method"] == 1

    wall_entry = next(o for o in summary["objects"] if o["name"] == "Perimeter_ZN_1_Infiltration")
    door_entry = next(o for o in summary["objects"] if o["name"] == "Lobby_ZN_1_FLR_1_Door_Infiltration")

    assert door_entry["status"] == "gate_unsupported_calculation_method"
    assert door_entry["gate"] == "gate_unsupported_calculation_method"
    assert float(door_obj.Design_Flow_Rate) == pytest.approx(existing_door_flow, abs=1e-9)

    new_wall_declared = float(wall_obj.Flow_Rate_per_Exterior_Surface_Area)
    assert new_wall_declared <= existing_wall_declared + 1e-9
    assert wall_entry["new_flow_m3_s"] <= wall_entry["existing_flow_m3_s"] + 1e-9

    for entry in summary["objects"]:
        if "existing_flow_m3_s" in entry and "new_flow_m3_s" in entry:
            assert entry["new_flow_m3_s"] <= entry["existing_flow_m3_s"] + 1e-9
