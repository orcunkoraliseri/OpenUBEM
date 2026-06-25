"""PTAC HVAC assignment (Phase-D, §0.1 authorized deviation from DESIGN §3H IdealLoads default).

Authorized deviation: DESIGN_step-3...md:392-394 (IdealLoadsAirSystem) replaced by
HVACTemplate:Zone:PackagedTerminalAirConditioner per §0.1 ratified 2026-06-21.
COP values sourced from openubem/data/loads/hvac_cop_by_archetype.json (T02/T02b).
"""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
from geomeppy import IDF as GeomIDF

_COP_JSON = Path(__file__).resolve().parent.parent / "data" / "loads" / "hvac_cop_by_archetype.json"


@lru_cache(maxsize=1)
def _load_cop_table() -> dict:
    return json.loads(_COP_JSON.read_text(encoding="utf-8"))


def assign_hvac(idf: GeomIDF, row: pd.Series, zones: list[dict]) -> None:
    """One HVACTEMPLATE:ZONE:PTAC per zone.

    Reads archetype_id from row → hvac_cop_by_archetype.json for:
      - Cooling_Coil_Gross_Rated_Cooling_COP
      - Heating_Coil_Type (Gas or Electric)
      - Heating_Coil_Capacity / efficiency field

    Raises KeyError if archetype_id is absent from the JSON (full coverage asserted in T02b).
    Keeps per-zone HVACTEMPLATE:THERMOSTAT (emitted by assign_loads in builder.py).
    """
    cop_table = _load_cop_table()
    archetype_id = str(row.get("archetype_id", "OpenUBEMUnknown"))

    if archetype_id not in cop_table:
        raise KeyError(
            f"archetype_id {archetype_id!r} not found in hvac_cop_by_archetype.json; "
            "run extract_prototype_cop.py to regenerate."
        )

    entry = cop_table[archetype_id]
    cooling_cop = entry.get("cooling_cop") or 3.0
    htg_type = entry.get("heating_coil_type")  # "Gas", "Electric", or None
    htg_eff = entry.get("heating_efficiency")   # float or None

    for z in zones:
        zname = z["name"]
        obj = idf.newidfobject("HVACTEMPLATE:ZONE:PTAC")
        obj.Zone_Name = zname
        obj.Template_Thermostat_Name = f"{zname}_Thermostat"

        # Cooling coil
        obj.Cooling_Coil_Type = "SingleSpeedDX"
        obj.Cooling_Coil_Gross_Rated_Cooling_COP = cooling_cop

        # Heating coil
        if htg_type == "Gas":
            obj.Heating_Coil_Type = "Gas"
            try:
                obj.Gas_Heating_Coil_Efficiency = htg_eff if htg_eff is not None else 0.8
            except Exception:
                pass
        elif htg_type == "Electric":
            obj.Heating_Coil_Type = "Electric"
        else:
            # DataCenters: no heating coil — leave default (Electric per IDD)
            pass

        # OA per ASHRAE 62.1 (autosize flow, method = Flow/Person default)
        try:
            obj.Outdoor_Air_Method = "Flow/Person"
            obj.Outdoor_Air_Flow_Rate_per_Person = 0.01  # 10 L/s/person
        except Exception:
            pass

        # Autosize capacities and flows
        for cap_field in (
            "Cooling_Coil_Gross_Rated_Total_Capacity",
            "Cooling_Coil_Gross_Rated_Sensible_Heat_Ratio",
            "Cooling_Supply_Air_Flow_Rate",
            "Heating_Supply_Air_Flow_Rate",
            "No_Load_Supply_Air_Flow_Rate",
        ):
            try:
                setattr(obj, cap_field, "autosize")
            except Exception:
                pass
