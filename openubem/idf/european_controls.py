"""D-EU-03/D-EU-07 controls emitted into European saved-IDF fixtures."""
from __future__ import annotations

from typing import Any, Mapping


def european_air_change_per_hour(record: Mapping[str, object]) -> float:
    """Return the ruled, reduced constant residential air-change rate.

    The campaign applies ``F_red_temp`` as an explicit multiplier to both
    envelope U-values and the constant use-plus-infiltration air rate.  The
    validation is deliberately fail-closed before any IDF object is emitted.
    """
    f_red = float(record["f_red_temp"])
    use_air = float(record["n_air_use_h_1"])
    infiltration = float(record["n_air_infiltration_h_1"])
    if f_red <= 0.0:
        raise ValueError("f_red_temp must be positive")
    if use_air <= 0.0:
        raise ValueError("n_air_use_h_1 must be positive")
    if infiltration < 0.0:
        raise ValueError("n_air_infiltration_h_1 must be non-negative")
    return (use_air + infiltration) * f_red


def add_european_heating_controls(idf: Any, record: Mapping[str, object], zone_name: str) -> dict[str, str | float]:
    """Add constant air, gains, and heating-only IdealLoads controls for one zone.

    ``F_red_temp`` deliberately scales the infiltration/ventilation ACH here;
    callers apply the same multiplier to each envelope U before construction
    creation.  Cooling is represented by an always-off availability schedule.

    Every per-zone object is named after ``zone_name`` because a multi-dwelling
    building repeats one archetype across its zones; the two constant
    availability schedules are archetype-independent and are emitted once per
    IDF and shared.
    """
    f_red = float(record["f_red_temp"])
    ach = european_air_change_per_hour(record)
    names = {
        "always_on": "EU_AlwaysOn",
        "cooling_off": "EU_CoolingOff",
        "thermostat": f"EU_HeatOnly_{zone_name}",
        "ventilation": f"EU_ConstantAir_{zone_name}",
        "gains": f"EU_InternalGains_{zone_name}",
    }
    if idf.getobject("ZONEVENTILATION:DESIGNFLOWRATE", names["ventilation"]) is not None:
        raise ValueError(f"European heating controls already emitted for zone {zone_name!r}")
    if idf.getobject("SCHEDULE:CONSTANT", names["always_on"]) is None:
        idf.newidfobject("SCHEDULE:CONSTANT", Name=names["always_on"], Hourly_Value=1.0)
    if idf.getobject("SCHEDULE:CONSTANT", names["cooling_off"]) is None:
        idf.newidfobject("SCHEDULE:CONSTANT", Name=names["cooling_off"], Hourly_Value=0.0)
    idf.newidfobject(
        "ZONEVENTILATION:DESIGNFLOWRATE",
        Name=names["ventilation"],
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name=names["always_on"],
        Design_Flow_Rate_Calculation_Method="AirChanges/Hour",
        Air_Changes_per_Hour=ach,
        Ventilation_Type="Natural",
    )
    idf.newidfobject(
        "OTHEREQUIPMENT",
        Name=names["gains"],
        Fuel_Type="Electricity",
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_name,
        Schedule_Name=names["always_on"],
        Design_Level_Calculation_Method="Watts/Area",
        Power_per_Zone_Floor_Area=float(record["phi_int_w_m2"]),
        Fraction_Latent=0.0,
        Fraction_Radiant=0.0,
        Fraction_Lost=0.0,
        EndUse_Subcategory="EU_InternalGains",
    )
    idf.newidfobject(
        "HVACTEMPLATE:THERMOSTAT",
        Name=names["thermostat"],
        Constant_Heating_Setpoint=float(record["theta_i_c"]),
        # ExpandObjects requires the final thermostat field to be present;
        # cooling is still disabled by the availability schedule below.
        Constant_Cooling_Setpoint=50.0,
    )
    idf.newidfobject(
        "HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM",
        Zone_Name=zone_name,
        Template_Thermostat_Name=names["thermostat"],
        System_Availability_Schedule_Name=names["always_on"],
        Heating_Limit="NoLimit",
        Cooling_Limit="NoLimit",
        Heating_Availability_Schedule_Name=names["always_on"],
        Cooling_Availability_Schedule_Name=names["cooling_off"],
        Outdoor_Air_Method="None",
    )
    return {**names, "air_changes_per_hour": ach, "u_multiplier": f_red}
