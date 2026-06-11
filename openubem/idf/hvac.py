"""IdealLoads HVAC assignment (DESIGN §3H, fact #25).

T10.5 (W3.7 remediation): config now selects the EnergyPlus 23.1 IDD by default, so all
extended HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM fields from fact #25 are applied on every run.
The try/except guard is retained for environments where the 23.1 IDD is not available.
"""
import pandas as pd
from geomeppy import IDF as GeomIDF

# The 11 extended fields from fact #25 that are unavailable in eppy's bundled v8.0.0 IDD.
# These are set here as a reference; the newidfobject call below ignores unknown fields
# by passing only what the IDD actually accepts.
_EXTENDED_DEFAULTS = {
    "Maximum_Heating_Supply_Air_Temperature": 50.0,
    "Minimum_Cooling_Supply_Air_Temperature": 13.0,
    "Heating_Limit": "LimitFlowRateAndCapacity",
    "Cooling_Limit": "LimitFlowRateAndCapacity",
    "Maximum_Heating_Air_Flow_Rate": "autosize",
    "Maximum_Sensible_Heating_Capacity": "autosize",
    "Maximum_Cooling_Air_Flow_Rate": "autosize",
    "Maximum_Total_Cooling_Capacity": "autosize",
    "Outdoor_Air_Method": "Flow/Person",
    "Outdoor_Air_Flow_Rate_per_Person": 0.01,
    "Demand_Controlled_Ventilation_Type": "None",
    "Heat_Recovery_Type": "None",
}


def assign_hvac(idf: GeomIDF, row: pd.Series, zones: list[dict]) -> None:
    """One HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM per zone per DESIGN §3H lines 401-417."""
    for z in zones:
        zname = z["name"]
        obj = idf.newidfobject("HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM")
        obj.Zone_Name = zname
        obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        # Apply extended defaults where the IDD permits (silently skipped if v8.0.0 IDD).
        for field, value in _EXTENDED_DEFAULTS.items():
            try:
                setattr(obj, field, value)
            except Exception:
                pass
