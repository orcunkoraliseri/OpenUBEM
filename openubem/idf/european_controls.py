"""D-EU-03/D-EU-07 controls emitted into European saved-IDF fixtures."""
from __future__ import annotations

from typing import Any, Mapping


def add_european_heating_controls(idf: Any, record: Mapping[str, object], zone_name: str) -> dict[str, str | float]:
    """Add constant air, gains, and heating-only IdealLoads controls for one zone.

    ``F_red_temp`` deliberately scales the infiltration/ventilation ACH here;
    callers apply the same multiplier to each envelope U before construction
    creation.  Cooling is represented by an always-off availability schedule.
    """
    archetype = str(record["archetype_id"])
    f_red = float(record["f_red_temp"])
    if not 0.0 < f_red <= 1.0:
        raise ValueError("f_red_temp must be in (0, 1]")
    ach = (float(record["n_air_use_h_1"]) + float(record["n_air_infiltration_h_1"])) * f_red
    names = {
        "always_on": f"EU_AlwaysOn_{archetype}",
        "cooling_off": f"EU_CoolingOff_{archetype}",
        "thermostat": f"EU_HeatOnly_{archetype}",
        "ventilation": f"EU_ConstantAir_{archetype}",
        "gains": f"EU_InternalGains_{archetype}",
    }
    idf.newidfobject("SCHEDULE:CONSTANT", Name=names["always_on"], Hourly_Value=1.0)
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
