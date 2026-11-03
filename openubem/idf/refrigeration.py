"""Phase-E refrigeration emitter: physical cases/racks (SuperMarket) | lumped (others) (T11, D5)."""
import json
import math
from pathlib import Path

from openubem.semantic import provenance

_CASES_DATA = json.loads(
    (Path(__file__).parent.parent / "data/refrigeration/supermarket_cases.json").read_text()
)
_LUMPED_DATA = json.loads(
    (Path(__file__).parent.parent / "data/refrigeration/refrigeration_lumped.json").read_text()
)
_LUMPED_ARCHETYPES = frozenset(
    {"FullServiceRestaurant", "QuickServiceRestaurant", "LargeHotel", "Hospital"}
)


def _resolve_area(row, flags):
    """footprint_area_m2 with provenance (T03 residual, wave 2a). absent/None -> 400.0
    (+DEFAULT token); stored 0 -> kept (+SUSPECT_ZERO token); real value -> unchanged."""
    v = row.get("footprint_area_m2", None)
    if v is None or (isinstance(v, float) and math.isnan(v)):
        flags.add(provenance.impute_token("DEFAULT", "GEOMETRY_AREA", "LOW"))
        return 400.0
    fv = float(v)
    if fv == 0:
        flags.add("SUSPECT_ZERO_FOOTPRINT_AREA_M2")
        return fv
    return fv


def _total_floor_area(row, zones, flags=None):
    """Footprint × unique-floor count extracted from zone names.

    A missing footprint (→400 m²) or a missing floor count (→1 floor) records a
    provenance token in `flags`; default VALUES are unchanged (T03 residual,
    instrumentation only).
    """
    if flags is None:
        flags = set()
    footprint = _resolve_area(row, flags)
    explicit = max((int(z.get("num_floors", 0) or 0) for z in zones), default=0)
    if explicit > 0:
        return footprint * explicit
    floor_idx = set()
    for z in zones:
        parts = z.get("name", "").split("_F")
        if len(parts) >= 2:
            fi = parts[1].split("_")[0]
            if fi.isdigit():
                floor_idx.add(fi)
    if len(floor_idx) == 0:
        flags.add(provenance.impute_token("DEFAULT", "GEOMETRY_FLOORS", "LOW"))
    return footprint * max(len(floor_idx), 1)


def _sched_constant_once(idf, name, value):
    if not any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])):
        s = idf.newidfobject("SCHEDULE:CONSTANT")
        s.Name = name
        s.Hourly_Value = value


# Latent case credit curve name + method per case type (required by E+ 23.1)
_CASE_LATENT_CURVE = {
    "LowTempFrozen":           "OpenUBEM_RHCubic_LatentEnergyMult",
    "LowTempIceCreamSpecialty": "OpenUBEM_RHCubic_LatentEnergyMult",
    "MediumTempDairyDeli":     "OpenUBEM_MultiShelfVert_LatentEnergyMult",
    "MediumTempMeat":          "OpenUBEM_SingleShelfHoriz_LatentEnergyMult",
    "Produce":                 "OpenUBEM_MultiShelfVert_LatentEnergyMult",
}
_CASE_LATENT_CURVE_TYPE = {
    "LowTempFrozen":           "RelativeHumidityMethod",   # RH curve x=[17.32,80]
    "LowTempIceCreamSpecialty": "RelativeHumidityMethod",
    "MediumTempDairyDeli":     "CaseTemperatureMethod",    # temp curve x=[-35,20]
    "MediumTempMeat":          "CaseTemperatureMethod",
    "Produce":                 "CaseTemperatureMethod",
}

# Per-case defrost schedule: staggered 2×20-min pulses/day, matching canonical Supermarket.idf
_CASE_DEFROST_SCHEDULE = {
    "LowTempFrozen":            "OpenUBEM_DefrostSched_LowTemp",
    "LowTempIceCreamSpecialty": "OpenUBEM_DefrostSched_LowTemp",
    "MediumTempDairyDeli":      "OpenUBEM_DefrostSched_OffCycle",
    "MediumTempMeat":           "OpenUBEM_DefrostSched_MedTemp",
    "Produce":                  "OpenUBEM_DefrostSched_OffCycle",
}


def _emit_defrost_schedules_once(idf):
    """Emit pulsed ON/OFF defrost schedules (once per IDF, 2 cycles/day × 20 min each).

    Staggered per family to avoid simultaneous demand spikes.  Matches the
    canonical Supermarket.idf pattern (Interpolate:Average for sub-hourly accuracy).
    """
    existing = {s.Name for s in idf.idfobjects.get("SCHEDULE:COMPACT", [])}
    # (schedule_name, defrost_start_hour_1, defrost_start_hour_2)
    defrost_defs = [
        ("OpenUBEM_DefrostSched_LowTemp",   4, 14),   # frozen:    04:00–04:20 & 14:00–14:20
        ("OpenUBEM_DefrostSched_MedTemp",   8, 18),   # elec-term: 08:00–08:20 & 18:00–18:20
        ("OpenUBEM_DefrostSched_OffCycle", 11, 23),   # off-cycle: 11:00–11:20 & 23:00–23:20
    ]
    for name, h1, h2 in defrost_defs:
        if name in existing:
            continue
        s = idf.newidfobject("SCHEDULE:COMPACT")
        s.Name = name
        s.Schedule_Type_Limits_Name = "ON/OFF"
        fields = [
            "Through: 12/31",
            "For: AllDays",
            "Interpolate: Average",
            f"Until: {h1}:00,0",
            f"Until: {h1}:20,1",
            f"Until: {h2}:00,0",
            f"Until: {h2}:20,1",
            "Until: 24:00,0",
        ]
        for i, field in enumerate(fields, 1):
            setattr(s, f"Field_{i}", field)


def _emit_refrig_curves_once(idf):
    """Emit required rack-COP and latent-credit curves (once per IDF)."""
    existing = {c.Name for c in idf.idfobjects.get("CURVE:QUADRATIC", [])}
    if "OpenUBEM_RackCOPfT" not in existing:
        c = idf.newidfobject("CURVE:QUADRATIC")
        c.Name = "OpenUBEM_RackCOPfT"
        c.Coefficient1_Constant = 1.7603
        c.Coefficient2_x = -0.0377
        c.Coefficient3_x2 = 0.0004
        c.Minimum_Value_of_x = 10.0
        c.Maximum_Value_of_x = 35.0

    existing_cub = {c.Name for c in idf.idfobjects.get("CURVE:CUBIC", [])}
    cubic_defs = [
        ("OpenUBEM_RHCubic_LatentEnergyMult",
         -0.4641, 0.0268, 0.0, 0.0, 17.32, 80.0),
        ("OpenUBEM_MultiShelfVert_LatentEnergyMult",
         0.026526281, 0.001078032, -6.02558e-05, 1.23732e-06, -35.0, 20.0),
        ("OpenUBEM_SingleShelfHoriz_LatentEnergyMult",
         0.020375634, 0.000243779, 1.14001e-05, 1.81142e-07, -35.0, 20.0),
    ]
    for name, c1, c2, c3, c4, xmin, xmax in cubic_defs:
        if name not in existing_cub:
            c = idf.newidfobject("CURVE:CUBIC")
            c.Name = name
            c.Coefficient1_Constant = c1
            c.Coefficient2_x = c2
            c.Coefficient3_x2 = c3
            c.Coefficient4_x3 = c4
            c.Minimum_Value_of_x = xmin
            c.Maximum_Value_of_x = xmax

    # Defrost EIR ratio curve (constant 1.0) for temperature-terminated defrost types
    existing_lin = {c.Name for c in idf.idfobjects.get("CURVE:LINEAR", [])}
    if "OpenUBEM_DefrostEIRfT" not in existing_lin:
        c = idf.newidfobject("CURVE:LINEAR")
        c.Name = "OpenUBEM_DefrostEIRfT"
        c.Coefficient1_Constant = 1.0
        c.Coefficient2_x = 0.0
        c.Minimum_Value_of_x = -30.0
        c.Maximum_Value_of_x = 30.0


def _emit_supermarket(idf, zone_name, floor_area):
    """Emit Refrigeration:Case + CaseAndWalkInList + CompressorRack per rack type."""
    _emit_refrig_curves_once(idf)
    _emit_defrost_schedules_once(idf)

    scaling = _CASES_DATA["_scaling"]
    racks_data = _CASES_DATA["_racks"]
    total_case_m = scaling["case_mix_m_per_m2_floor_area"] * floor_area
    ref_total = scaling["reference_total_case_length_m"]

    # Build cases and group by rack type
    rack_cases: dict[str, list[str]] = {"low_temp": [], "medium_temp": []}
    for case_data in _CASES_DATA["cases"]:
        rack_type = case_data["rack"]
        scaled_len = (case_data["reference_length_m"] / ref_total) * total_case_m
        if scaled_len < 0.1:
            continue

        defrost_type = case_data["defrost_type"]
        anti_sweat = case_data["anti_sweat_w_m"]

        obj = idf.newidfobject("REFRIGERATION:CASE")
        case_name = f"RefrigCase_{case_data['case_type']}"
        obj.Name = case_name
        obj.Zone_Name = zone_name
        obj.Rated_Total_Cooling_Capacity_per_Unit_Length = case_data["rated_cooling_capacity_w_m"]
        obj.Rated_Latent_Heat_Ratio = case_data["latent_heat_ratio"]
        obj.Rated_Runtime_Fraction = 0.85
        obj.Case_Length = round(scaled_len, 3)
        obj.Case_Operating_Temperature = case_data["operating_temp_c"]
        obj.Standard_Case_Fan_Power_per_Unit_Length = case_data["fan_power_w_m"]
        obj.Operating_Case_Fan_Power_per_Unit_Length = case_data["fan_power_w_m"]
        obj.Standard_Case_Lighting_Power_per_Unit_Length = case_data["lighting_power_w_m"]
        obj.Installed_Case_Lighting_Power_per_Unit_Length = case_data["lighting_power_w_m"]
        if anti_sweat > 0:
            obj.Case_AntiSweat_Heater_Power_per_Unit_Length = anti_sweat
            obj.AntiSweat_Heater_Control_Type = "Constant"
        else:
            obj.AntiSweat_Heater_Control_Type = "None"
        obj.Case_Defrost_Type = defrost_type
        obj.Case_Defrost_Schedule_Name = _CASE_DEFROST_SCHEDULE[case_data["case_type"]]
        if defrost_type != "OffCycle":
            obj.Case_Defrost_Power_per_Unit_Length = case_data["defrost_energy_w_m"]
        if "TemperatureTermination" in defrost_type:
            # E+ 23.1 JSON-schema requires correction curve for temperature-terminated defrost
            obj.Defrost_Energy_Correction_Curve_Type = "CaseTemperatureMethod"
            obj.Defrost_Energy_Correction_Curve_Name = "OpenUBEM_DefrostEIRfT"
        else:
            obj.Defrost_Energy_Correction_Curve_Type = "None"
        case_type = case_data["case_type"]
        obj.Latent_Case_Credit_Curve_Type = _CASE_LATENT_CURVE_TYPE[case_type]
        obj.Latent_Case_Credit_Curve_Name = _CASE_LATENT_CURVE[case_type]

        rack_cases[rack_type].append(case_name)

    # Emit CaseAndWalkInList + CompressorRack per rack type
    for rack_type, case_names in rack_cases.items():
        if not case_names:
            continue
        rack_data = racks_data[rack_type]

        cawil = idf.newidfobject("REFRIGERATION:CASEANDWALKINLIST")
        cawil_name = f"RefrigCaseList_{rack_type}"
        cawil.Name = cawil_name
        for i, cn in enumerate(case_names, start=1):
            setattr(cawil, f"Case_or_WalkIn_{i}_Name", cn)

        rack = idf.newidfobject("REFRIGERATION:COMPRESSORRACK")
        rack.Name = f"RefrigRack_{rack_type}"
        rack.Heat_Rejection_Location = "Outdoors"
        rack.Design_Compressor_Rack_COP = rack_data["rack_cop"]
        rack.Compressor_Rack_COP_Function_of_Temperature_Curve_Name = "OpenUBEM_RackCOPfT"
        rack.Design_Condenser_Fan_Power = rack_data["condenser_fan_power_w"]
        rack.Condenser_Type = rack_data["condenser_type"]
        rack.EndUse_Subcategory = "Refrigeration"
        rack.Refrigeration_Case_Name_or_WalkIn_Name_or_CaseAndWalkInList_Name = cawil_name


def assign_refrigeration(idf, row, zones):
    """Emit refrigeration loads (D5): physical cases for SuperMarket, lumped elec for others.

    Returns the sorted geometry-default provenance tokens (T03 residual, wave 2a);
    they are also appended in place to ``row['data_quality_flag']``. Archetypes that
    get no refrigeration load at all (not SuperMarket, not in the lumped table, or a
    lumped archetype with eui<=0) are skipped BEFORE geometry resolution — mirrors the
    dhw/cooking no_dhw/no_cooking skip-ordering — so they never emit a geometry token.
    """
    if not zones:  # degenerate geometry: no zone to host cases/equipment (D4a defensive guard)
        return []
    arch = str(row["archetype_id"])
    zone_name = zones[0]["name"]
    is_supermarket = arch == "SuperMarket"

    data = None
    if not is_supermarket:
        if arch not in _LUMPED_ARCHETYPES:
            return []
        data = _LUMPED_DATA.get(arch, {})
        if data.get("energy_intensity_kwh_m2_yr", 0.0) <= 0:
            return []

    flags: set = set()
    total_area = _total_floor_area(row, zones, flags)
    for tok in sorted(flags):
        row["data_quality_flag"] = provenance.append_flag_token(
            row.get("data_quality_flag"), tok
        )

    if is_supermarket:
        _emit_supermarket(idf, zone_name, total_area)
        return sorted(flags)

    # Convert annual kWh/m²/yr to average watts (constant 24/7 operation)
    eui = data["energy_intensity_kwh_m2_yr"]
    avg_w_total = eui * total_area * 1000.0 / 8760.0

    _sched_constant_once(idf, "OpenUBEM_Refrig_ConstantSched", 1.0)
    elec_eq = idf.newidfobject("ELECTRICEQUIPMENT")
    elec_eq.Name = f"Refrig_Lumped_{arch}"
    elec_eq.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    elec_eq.Schedule_Name = "OpenUBEM_Refrig_ConstantSched"
    elec_eq.Design_Level_Calculation_Method = "EquipmentLevel"
    elec_eq.Design_Level = round(avg_w_total, 2)
    elec_eq.Fraction_Radiant = 0.0
    elec_eq.Fraction_Latent = 0.0
    elec_eq.Fraction_Lost = 1.0  # condenser rejects heat outdoors
    elec_eq.EndUse_Subcategory = "Refrigeration"

    return sorted(flags)
