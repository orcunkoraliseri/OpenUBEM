"""HVAC dispatcher (Phase-E).

Authorized deviation §0.1: DESIGN §3H IdealLoadsAirSystem replaced by archetype-
appropriate HVACTemplate objects per RESULT_01 Part C + RESULT_02 Tables A/C/D/E.
Phase-D PTAC kept for SmallHotel; all other archetypes get real systems (T06-T08).
"""
import json
import logging
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd
from geomeppy import IDF as GeomIDF

from openubem.semantic import provenance

logger = logging.getLogger(__name__)

# ── Tier-B silent-default provenance (Input-Imputation arc T02) ───────────────
# Every ASHRAE-default substitution below is an *instrumentation* fix: the default
# VALUE is unchanged (EUI must not move); we only record a queryable provenance
# token. A stored 0 is a data value — it is preserved and flagged distinctly, NOT
# silently promoted to the default.
_HVAC_SOURCE = "ASHRAE901"


def _default_flag(param: str) -> str:
    return provenance.impute_token("DEFAULT", f"{_HVAC_SOURCE}_{param}", "LOW")


def _zero_flag(param: str) -> str:
    return f"SUSPECT_ZERO_{param.upper()}"


def _absent(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _resolve(entry: dict, key: str, default, param: str, flags: set):
    """Single-key ASHRAE default with provenance (replaces `entry.get(k) or d`).

    absent/None -> default (+DEFAULT token); stored 0 -> kept (+SUSPECT_ZERO
    token); real value -> unchanged, no token.
    """
    v = entry.get(key, None)
    if _absent(v):
        flags.add(_default_flag(param))
        return default
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0:
        flags.add(_zero_flag(param))
        return v
    return v


def _resolve_chain(entry: dict, keys: list, default, param: str, flags: set):
    """Multi-source fallback `entry[k0] or entry[k1] or ... or default`.

    Preserves the `or`-chain idiom (first truthy source wins; a falsy/absent link
    falls through to the next source). Emits a DEFAULT token only when the terminal
    default is reached (no source supplied a value).
    """
    for k in keys:
        v = entry.get(k, None)
        if not _absent(v) and v:
            return v
    flags.add(_default_flag(param))
    return default

_DATA = Path(__file__).resolve().parent.parent / "data" / "loads"
_COP_JSON = _DATA / "hvac_cop_by_archetype.json"
_SYS_JSON = _DATA / "hvac_systems_by_archetype.json"

# Option-C single-zone guard (user ruling 2026-06-27): central / multi-zone-VAV / PVAV-reheat
# families that must be downgraded to a packaged single-zone RTU when a building resolves to
# exactly one thermal zone. (Data Center CRAC/CRAH is only central when central_plant=True.)
_CENTRAL_OR_VAV_FAMILIES = frozenset({
    "Packaged VAV w/ Electric Reheat",
    "Packaged VAV w/ Hot Water Reheat",
    "Built-up VAV w/ Chilled Water & Hot Water Reheat",
    "Four-Pipe Fan Coil Units",
    "Water-Loop Heat Pump",
    "Data Center CRAC / CRAH",
})
# Residential apartments are exempt — a dwelling unit must never be downgraded to a gas-furnace
# RTU; they keep their packaged/loop systems (MidriseApartment=PSZ-AC, HighriseApartment=WLHP).
_RESIDENTIAL_ARCHETYPES = frozenset({"MidriseApartment", "HighriseApartment"})


@lru_cache(maxsize=1)
def _load_cop_table() -> dict:
    return json.loads(_COP_JSON.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_sys_table() -> dict:
    return json.loads(_SYS_JSON.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Plant helpers (one plant per building — unique-object constraint in IDD)
# ---------------------------------------------------------------------------

def _add_chw_plant(idf: GeomIDF, chiller_cop: float) -> None:
    """CHW loop + centrifugal chiller + cooling tower.
    Setpoint 6.67 °C (44 °F), ΔT 8.33 °C (15 °F) per RESULT_02 Table C.
    """
    loop = idf.newidfobject("HVACTEMPLATE:PLANT:CHILLEDWATERLOOP")
    loop.Name = "OpenUBEM_CHW_Loop"
    loop.Chilled_Water_Design_Setpoint = 6.67
    loop.Loop_Design_Delta_Temperature = 8.33
    loop.Pump_Control_Type = "Intermittent"

    chiller = idf.newidfobject("HVACTEMPLATE:PLANT:CHILLER")
    chiller.Name = "OpenUBEM_Chiller"
    chiller.Chiller_Type = "ElectricCentrifugalChiller"
    chiller.Nominal_COP = chiller_cop
    chiller.Condenser_Type = "WaterCooled"
    chiller.Priority = "1"

    tower = idf.newidfobject("HVACTEMPLATE:PLANT:TOWER")
    tower.Name = "OpenUBEM_Tower"
    tower.Tower_Type = "TwoSpeed"
    tower.Template_Plant_Loop_Type = "ChilledWater"
    tower.Priority = "1"


def _add_hw_plant(idf: GeomIDF, htg_eff: float) -> None:
    """HW loop + gas boiler.
    Setpoint 60 °C (140 °F) per RESULT_02 Table C.
    CondensingHotWaterBoiler if eff >= 0.90, else HotWaterBoiler.
    """
    loop = idf.newidfobject("HVACTEMPLATE:PLANT:HOTWATERLOOP")
    loop.Name = "OpenUBEM_HW_Loop"
    loop.Hot_Water_Design_Setpoint = 60.0
    loop.Pump_Control_Type = "Intermittent"

    boiler = idf.newidfobject("HVACTEMPLATE:PLANT:BOILER")
    boiler.Name = "OpenUBEM_HW_Boiler"
    boiler.Boiler_Type = "CondensingHotWaterBoiler" if htg_eff >= 0.90 else "HotWaterBoiler"
    boiler.Efficiency = htg_eff
    boiler.Fuel_Type = "NaturalGas"
    boiler.Template_Plant_Loop_Type = "HotWater"
    boiler.Priority = "1"


def _add_mixed_water_plant(idf: GeomIDF, htg_eff: float) -> None:
    """Mixed-water loop (WLHP) + gas boiler + cooling tower.
    High setpoint 33 °C, low 20 °C (IDD defaults for WLHP per RESULT_02).
    """
    loop = idf.newidfobject("HVACTEMPLATE:PLANT:MIXEDWATERLOOP")
    loop.Name = "OpenUBEM_Mixed_Loop"
    loop.Pump_Control_Type = "Intermittent"
    loop.High_Temperature_Design_Setpoint = 33.0
    loop.Low_Temperature_Design_Setpoint = 20.0

    boiler = idf.newidfobject("HVACTEMPLATE:PLANT:BOILER")
    boiler.Name = "OpenUBEM_Mixed_Boiler"
    boiler.Boiler_Type = "CondensingHotWaterBoiler" if htg_eff >= 0.90 else "HotWaterBoiler"
    boiler.Efficiency = htg_eff
    boiler.Fuel_Type = "NaturalGas"
    boiler.Template_Plant_Loop_Type = "MixedWater"
    boiler.Priority = "1"

    tower = idf.newidfobject("HVACTEMPLATE:PLANT:TOWER")
    tower.Name = "OpenUBEM_Mixed_Tower"
    tower.Tower_Type = "TwoSpeed"
    tower.Template_Plant_Loop_Type = "MixedWater"
    tower.Priority = "1"


# ---------------------------------------------------------------------------
# Tier-1 system emitters
# ---------------------------------------------------------------------------

def _emit_ptac(idf: GeomIDF, zones: list[dict], cop_entry: dict, flags: set | None = None) -> None:
    """PTAC w/ Electric Reheat — per zone (SmallHotel)."""
    if flags is None:
        flags = set()
    cooling_cop = _resolve(cop_entry, "cooling_cop", 3.0, "cooling_cop", flags)
    htg_type = cop_entry.get("heating_coil_type")
    # Only resolved (and only flagged) for Gas coils — Electric coils never read this key.
    htg_eff = (
        _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
        if htg_type == "Gas" else None
    )
    for z in zones:
        zname = z["name"]
        obj = idf.newidfobject("HVACTEMPLATE:ZONE:PTAC")
        obj.Zone_Name = zname
        obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        obj.Cooling_Coil_Type = "SingleSpeedDX"
        obj.Cooling_Coil_Gross_Rated_Cooling_COP = cooling_cop
        if htg_type == "Gas":
            obj.Heating_Coil_Type = "Gas"
            try:
                obj.Gas_Heating_Coil_Efficiency = htg_eff
            except Exception:
                pass
        elif htg_type == "Electric":
            obj.Heating_Coil_Type = "Electric"
        try:
            obj.Outdoor_Air_Method = "Flow/Person"
            obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass
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


def _emit_psz_ac(
    idf: GeomIDF,
    zones: list[dict],
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """PSZ-AC w/ Gas Furnace — one System:Unitary + Zone:Unitary per zone."""
    if flags is None:
        flags = set()
    cooling_cop = _resolve(cop_entry, "cooling_cop", 3.0, "cooling_cop", flags)
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 622.5, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.55575, "fan_total_efficiency", flags)

    for z in zones:
        zname = z["name"]
        sysname = f"{zname}_PSZ_Sys"

        sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:UNITARY")
        sys_obj.Name = sysname
        sys_obj.Control_Zone_or_Thermostat_Location_Name = zname
        sys_obj.Supply_Fan_Total_Efficiency = fan_eff
        sys_obj.Supply_Fan_Delta_Pressure = fan_pa
        sys_obj.Cooling_Coil_Type = "SingleSpeedDX"
        sys_obj.Cooling_Coil_Gross_Rated_COP = cooling_cop
        sys_obj.Heating_Coil_Type = "Gas"
        sys_obj.Gas_Heating_Coil_Efficiency = htg_eff
        sys_obj.Economizer_Type = "DifferentialDryBulb"

        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:UNITARY")
        zone_obj.Zone_Name = zname
        zone_obj.Template_Unitary_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        try:
            zone_obj.Outdoor_Air_Method = "Flow/Person"
            zone_obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass


def _emit_psz_hp(
    idf: GeomIDF,
    zones: list[dict],
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """PSZ-HP w/ Gas Backup — one System:UnitaryHeatPump:AirToAir + Zone:Unitary per zone."""
    if flags is None:
        flags = set()
    cooling_cop = _resolve(cop_entry, "cooling_cop", 3.0, "cooling_cop", flags)
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 622.5, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.55575, "fan_total_efficiency", flags)

    for z in zones:
        zname = z["name"]
        sysname = f"{zname}_HP_Sys"

        sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:UNITARYHEATPUMP:AIRTOAIR")
        sys_obj.Name = sysname
        sys_obj.Control_Zone_or_Thermostat_Location_Name = zname
        sys_obj.Supply_Fan_Total_Efficiency = fan_eff
        sys_obj.Supply_Fan_Delta_Pressure = fan_pa
        sys_obj.Cooling_Coil_Gross_Rated_COP = cooling_cop
        sys_obj.Supplemental_Heating_Coil_Type = "Gas"
        sys_obj.Supplemental_Gas_Heating_Coil_Efficiency = htg_eff
        sys_obj.Economizer_Type = "DifferentialDryBulb"

        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:UNITARY")
        zone_obj.Zone_Name = zname
        zone_obj.Template_Unitary_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        try:
            zone_obj.Outdoor_Air_Method = "Flow/Person"
            zone_obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass


def _emit_pvav(
    idf: GeomIDF,
    zones: list[dict],
    bld: str,
    cop_entry: dict,
    sys_entry: dict,
    reheat_type: str,
    flags: set | None = None,
) -> None:
    """Packaged VAV — one System:PackagedVAV + N Zone:VAV.

    reheat_type: 'Electric' (no plant) or 'HotWater' (requires HW plant).
    """
    if flags is None:
        flags = set()
    cooling_cop = _resolve(cop_entry, "cooling_cop", 3.0, "cooling_cop", flags)
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 1389.42, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.6084, "fan_total_efficiency", flags)
    turndown = _resolve(sys_entry, "vav_min_turndown", 0.30, "vav_min_turndown", flags)
    sysname = f"{bld}_PVAV_Sys"

    sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:PACKAGEDVAV")
    sys_obj.Name = sysname
    sys_obj.Supply_Fan_Total_Efficiency = fan_eff
    sys_obj.Supply_Fan_Delta_Pressure = fan_pa
    sys_obj.Cooling_Coil_Type = "TwoSpeedDX"
    sys_obj.Cooling_Coil_Gross_Rated_COP = cooling_cop
    sys_obj.Heating_Coil_Type = reheat_type
    if reheat_type == "Gas":
        sys_obj.Gas_Heating_Coil_Efficiency = htg_eff
    sys_obj.Economizer_Type = "DifferentialDryBulb"
    # SAT reset (RD2): raises supply-air temp at low cooling load → collapses HW-reheat penalty
    try:
        sys_obj.Cooling_Coil_Setpoint_Reset_Type = "Warmest"
    except Exception:
        pass

    for z in zones:
        zname = z["name"]
        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:VAV")
        zone_obj.Zone_Name = zname
        zone_obj.Template_VAV_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        zone_obj.Supply_Air_Maximum_Flow_Rate = "autosize"
        zone_obj.Zone_Minimum_Air_Flow_Input_Method = "Constant"
        zone_obj.Constant_Minimum_Air_Flow_Fraction = turndown
        zone_obj.Reheat_Coil_Type = reheat_type
        try:
            zone_obj.Outdoor_Air_Method = "Flow/Person"
            zone_obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass

    if reheat_type == "HotWater":
        _add_hw_plant(idf, htg_eff)


def _emit_buildup_vav(
    idf: GeomIDF,
    zones: list[dict],
    bld: str,
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """Built-up VAV w/ CHW & HW Reheat — System:VAV + Zone:VAV + full plant."""
    if flags is None:
        flags = set()
    chiller_cop = _resolve_chain(
        cop_entry, ["chiller_cop_phaseE", "cooling_cop"], 3.0, "chiller_cop", flags
    )
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 1389.42, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.6084, "fan_total_efficiency", flags)
    turndown = _resolve(sys_entry, "vav_min_turndown", 0.30, "vav_min_turndown", flags)
    sysname = f"{bld}_VAV_Sys"

    sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:VAV")
    sys_obj.Name = sysname
    sys_obj.Supply_Fan_Total_Efficiency = fan_eff
    sys_obj.Supply_Fan_Delta_Pressure = fan_pa
    sys_obj.Cooling_Coil_Type = "ChilledWater"
    sys_obj.Cooling_Coil_Design_Setpoint = 12.8
    sys_obj.Heating_Coil_Type = "HotWater"
    sys_obj.Economizer_Type = "DifferentialDryBulb"
    # SAT reset (RD2): DOE-prototype-standard; reduces reheat for already-passing archetypes
    try:
        sys_obj.Cooling_Coil_Setpoint_Reset_Type = "Warmest"
    except Exception:
        pass

    for z in zones:
        zname = z["name"]
        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:VAV")
        zone_obj.Zone_Name = zname
        zone_obj.Template_VAV_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        zone_obj.Supply_Air_Maximum_Flow_Rate = "autosize"
        zone_obj.Zone_Minimum_Air_Flow_Input_Method = "Constant"
        zone_obj.Constant_Minimum_Air_Flow_Fraction = turndown
        zone_obj.Reheat_Coil_Type = "HotWater"
        try:
            zone_obj.Outdoor_Air_Method = "Flow/Person"
            zone_obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass

    _add_chw_plant(idf, chiller_cop)
    _add_hw_plant(idf, htg_eff)


# ---------------------------------------------------------------------------
# Tier-2 system emitters
# ---------------------------------------------------------------------------

def _emit_fcu(
    idf: GeomIDF,
    zones: list[dict],
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """Four-Pipe Fan Coil Units — Zone:FanCoil per zone + CHW+HW plant."""
    if flags is None:
        flags = set()
    chiller_cop = _resolve_chain(
        cop_entry, ["chiller_cop_phaseE", "cooling_cop"], 3.0, "chiller_cop", flags
    )
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 331.17, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.520, "fan_total_efficiency", flags)

    for z in zones:
        zname = z["name"]
        obj = idf.newidfobject("HVACTEMPLATE:ZONE:FANCOIL")
        obj.Zone_Name = zname
        obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        obj.Supply_Air_Maximum_Flow_Rate = "autosize"
        obj.Supply_Fan_Total_Efficiency = fan_eff
        obj.Supply_Fan_Delta_Pressure = fan_pa
        obj.Cooling_Coil_Type = "ChilledWater"
        obj.Heating_Coil_Type = "HotWater"
        try:
            obj.Outdoor_Air_Method = "Flow/Person"
            obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass

    _add_chw_plant(idf, chiller_cop)
    _add_hw_plant(idf, htg_eff)


def _emit_wlhp(
    idf: GeomIDF,
    zones: list[dict],
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """Water-Loop Heat Pump — Zone:WaterToAirHeatPump per zone + MixedWaterLoop plant."""
    if flags is None:
        flags = set()
    cooling_cop = _resolve_chain(
        cop_entry, ["chiller_cop_phaseE", "cooling_cop"], 3.0, "cooling_cop", flags
    )
    # heating_efficiency read is vestigial (result unused); loop boiler uses the hardcoded
    # 0.80 below, so no provenance token is emitted for it.
    htg_eff_raw = cop_entry.get("heating_efficiency", 1.0)  # noqa: F841
    # heating_efficiency for WLHP is HP COP (electric); boiler is gas for loop backup
    # Use default gas boiler eff 0.80 for loop boiler (no gas furnace entry in WLHP archetype)
    loop_boiler_eff = 0.80
    fan_pa = _resolve(sys_entry, "fan_static_pa", 622.5, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.55575, "fan_total_efficiency", flags)

    for z in zones:
        zname = z["name"]
        obj = idf.newidfobject("HVACTEMPLATE:ZONE:WATERTOAIRHEATPUMP")
        obj.Zone_Name = zname
        obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        obj.Cooling_Coil_Gross_Rated_COP = cooling_cop
        obj.Supply_Fan_Total_Efficiency = fan_eff
        obj.Supply_Fan_Delta_Pressure = fan_pa
        try:
            obj.Cooling_Supply_Air_Flow_Rate = "autosize"
            obj.Heating_Supply_Air_Flow_Rate = "autosize"
        except Exception:
            pass
        try:
            obj.Outdoor_Air_Method = "Flow/Person"
            obj.Outdoor_Air_Flow_Rate_per_Person = 0.01
        except Exception:
            pass

    _add_mixed_water_plant(idf, loop_boiler_eff)


# ---------------------------------------------------------------------------
# Tier-3 proxied system emitters
# ---------------------------------------------------------------------------

def _emit_crac_proxy(
    idf: GeomIDF,
    zones: list[dict],
    bld: str,
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """CRAC proxy → PSZ-DX per zone (cooling only; electric htg as required-field fallback).
    Proxy note: HVACTemplate:System:Unitary requires Heating_Coil_Type (no 'None'); Electric
    chosen as minimal-impact fallback since data centers are cooling-dominated (D4 T08).
    """
    if flags is None:
        flags = set()
    cooling_cop = _resolve(cop_entry, "cooling_cop", 3.0, "cooling_cop", flags)
    fan_pa = _resolve(sys_entry, "fan_static_pa", 622.5, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.55575, "fan_total_efficiency", flags)

    for z in zones:
        zname = z["name"]
        sysname = f"{zname}_CRAC_Sys"

        sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:UNITARY")
        sys_obj.Name = sysname
        sys_obj.Control_Zone_or_Thermostat_Location_Name = zname
        sys_obj.Supply_Fan_Total_Efficiency = fan_eff
        sys_obj.Supply_Fan_Delta_Pressure = fan_pa
        sys_obj.Cooling_Coil_Type = "SingleSpeedDX"
        sys_obj.Cooling_Coil_Gross_Rated_COP = cooling_cop
        sys_obj.Heating_Coil_Type = "Electric"  # required-field; DC never heats
        sys_obj.Economizer_Type = "DifferentialDryBulb"

        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:UNITARY")
        zone_obj.Zone_Name = zname
        zone_obj.Template_Unitary_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"


def _emit_crah_proxy(
    idf: GeomIDF,
    zones: list[dict],
    bld: str,
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """CRAH proxy → VAV-DX-CHW (no HW plant; cooling-only VAV + CHW chiller).
    Proxy note: CRAH recirculates cold-aisle air; VAV+CHW is closest HVACTemplate match (D4 T08).
    """
    if flags is None:
        flags = set()
    chiller_cop = _resolve_chain(
        cop_entry, ["chiller_cop_phaseE", "cooling_cop"], 3.0, "chiller_cop", flags
    )
    fan_pa = _resolve(sys_entry, "fan_static_pa", 1389.42, "fan_static_pa", flags)
    fan_eff = _resolve(sys_entry, "fan_total_efficiency", 0.6084, "fan_total_efficiency", flags)
    sysname = f"{bld}_CRAH_VAV_Sys"

    sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:VAV")
    sys_obj.Name = sysname
    sys_obj.Supply_Fan_Total_Efficiency = fan_eff
    sys_obj.Supply_Fan_Delta_Pressure = fan_pa
    sys_obj.Cooling_Coil_Type = "ChilledWater"
    sys_obj.Cooling_Coil_Design_Setpoint = 12.8
    sys_obj.Heating_Coil_Type = "None"
    sys_obj.Economizer_Type = "DifferentialDryBulb"
    # SAT reset (RD2): consistency with other VAV families; CRAH is cooling-only so effect is minimal
    try:
        sys_obj.Cooling_Coil_Setpoint_Reset_Type = "Warmest"
    except Exception:
        pass

    for z in zones:
        zname = z["name"]
        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:VAV")
        zone_obj.Zone_Name = zname
        zone_obj.Template_VAV_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"
        zone_obj.Supply_Air_Maximum_Flow_Rate = "autosize"
        zone_obj.Reheat_Coil_Type = "None"

    _add_chw_plant(idf, chiller_cop)


def _emit_warehouse_radiant_proxy(
    idf: GeomIDF,
    zones: list[dict],
    cop_entry: dict,
    sys_entry: dict,
    flags: set | None = None,
) -> None:
    """Heated-only radiant proxy → gas heating unitary, cooling disabled.
    Proxy note: HVACTemplate has no native radiant; Unitary with Cooling=None + Gas heating
    models the heating load; cooling capacity will be negligible (D4 T08).
    """
    if flags is None:
        flags = set()
    htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, "heating_efficiency", flags)

    for z in zones:
        zname = z["name"]
        sysname = f"{zname}_Htg_Sys"

        sys_obj = idf.newidfobject("HVACTEMPLATE:SYSTEM:UNITARY")
        sys_obj.Name = sysname
        sys_obj.Control_Zone_or_Thermostat_Location_Name = zname
        sys_obj.Supply_Fan_Total_Efficiency = 0.55575
        sys_obj.Supply_Fan_Delta_Pressure = 622.5
        sys_obj.Cooling_Coil_Type = "None"
        sys_obj.Heating_Coil_Type = "Gas"
        sys_obj.Gas_Heating_Coil_Efficiency = htg_eff
        sys_obj.Economizer_Type = "NoEconomizer"

        zone_obj = idf.newidfobject("HVACTEMPLATE:ZONE:UNITARY")
        zone_obj.Zone_Name = zname
        zone_obj.Template_Unitary_System_Name = sysname
        zone_obj.Template_Thermostat_Name = f"{zname}_Thermostat"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def assign_hvac(idf: GeomIDF, row: pd.Series, zones: list[dict]) -> list[str]:
    """Dispatch HVAC objects for one building based on archetype system_family.

    Reads hvac_systems_by_archetype.json (T01) for system_family + air-side params,
    hvac_cop_by_archetype.json (T02) for COP + efficiency values.
    One plant per building for central-plant archetypes (unique-object constraint).
    Thermostat objects emitted upstream by assign_loads (builder.py); do NOT remove.

    Any ASHRAE-default substitution records a provenance token (T02): the tokens are
    appended in place to ``row['data_quality_flag']`` and also returned (sorted) so a
    caller can merge them into its own flag accumulator.
    """
    flags: set = set()

    cop_table = _load_cop_table()
    sys_table = _load_sys_table()

    archetype_id = str(row.get("archetype_id", "OpenUBEMUnknown"))

    if archetype_id not in cop_table:
        raise KeyError(
            f"archetype_id {archetype_id!r} not found in hvac_cop_by_archetype.json; "
            "run extract_prototype_cop.py to regenerate."
        )

    cop_entry = cop_table[archetype_id]
    sys_entry = sys_table.get(archetype_id, sys_table.get("OpenUBEMUnknown", {}))
    family = sys_entry.get("system_family", "Packaged VAV w/ Hot Water Reheat")
    central = sys_entry.get("central_plant", False)

    if not zones:
        return []

    bld = zones[0]["name"].rsplit("_F", 1)[0]

    # ── Option-C single-zone guard (user ruling 2026-06-27) ──────────────────────
    # A building that resolves to exactly ONE thermal zone must not carry a central /
    # multi-zone-VAV / PVAV-reheat system (those model multi-zone load diversity, and on
    # degenerate single-zone geometry they drive a reheat runaway). Downgrade to a packaged
    # single-zone RTU — physically correct for a 1-zone building regardless of size
    # (Phase-D ran these exact schools fine on blanket packaged single-zone units).
    # Residential apartments and already-packaged single-zone systems are left untouched.
    if (
        len(zones) == 1
        and archetype_id not in _RESIDENTIAL_ARCHETYPES
        and family in _CENTRAL_OR_VAV_FAMILIES
        and not (family == "Data Center CRAC / CRAH" and not central)
    ):
        orig_family = family
        if family == "Data Center CRAC / CRAH":
            # closest single-zone packaged path for a cooling-only DC: CRAC proxy (PSZ-DX);
            # never a gas furnace on a data center
            central = False  # routes to _emit_crac_proxy below
            new_family = "Data Center CRAC (single-zone PSZ-DX)"
        else:
            family = "PSZ-AC w/ Gas Furnace"  # → _emit_psz_ac
            # PSZ uses its own RESULT_02 fan static (622.5 Pa default), not the VAV 1389 Pa:
            # drop the VAV fan fields so _emit_psz_ac falls back to PSZ defaults.
            sys_entry = {k: v for k, v in sys_entry.items()
                         if k not in ("fan_static_pa", "fan_total_efficiency")}
            new_family = family
        logger.warning(
            "single-zone HVAC downgrade: bld=%s archetype=%s %r -> %r",
            bld, archetype_id, orig_family, new_family,
        )
        print(f"[hvac] single-zone downgrade: {bld} archetype={archetype_id} "
              f"{orig_family!r} -> {new_family!r}")

    if family == "PTAC w/ Electric Reheat":
        _emit_ptac(idf, zones, cop_entry, flags)

    elif family == "PSZ-AC w/ Gas Furnace":
        _emit_psz_ac(idf, zones, cop_entry, sys_entry, flags)

    elif family == "PSZ-HP w/ Gas Backup":
        _emit_psz_hp(idf, zones, cop_entry, sys_entry, flags)

    elif family == "Packaged VAV w/ Electric Reheat":
        _emit_pvav(idf, zones, bld, cop_entry, sys_entry, reheat_type="Electric", flags=flags)

    elif family == "Packaged VAV w/ Hot Water Reheat":
        _emit_pvav(idf, zones, bld, cop_entry, sys_entry, reheat_type="HotWater", flags=flags)

    elif family == "Built-up VAV w/ Chilled Water & Hot Water Reheat":
        _emit_buildup_vav(idf, zones, bld, cop_entry, sys_entry, flags)

    elif family == "Four-Pipe Fan Coil Units":
        _emit_fcu(idf, zones, cop_entry, sys_entry, flags)

    elif family == "Water-Loop Heat Pump":
        _emit_wlhp(idf, zones, cop_entry, sys_entry, flags)

    elif family == "Data Center CRAC / CRAH":
        if central:
            _emit_crah_proxy(idf, zones, bld, cop_entry, sys_entry, flags)
        else:
            _emit_crac_proxy(idf, zones, bld, cop_entry, sys_entry, flags)

    elif family == "Heated-only Radiant / Unit Heaters":
        _emit_warehouse_radiant_proxy(idf, zones, cop_entry, sys_entry, flags)

    else:
        # Unknown family — fall back to PTAC to avoid silent failures
        _emit_ptac(idf, zones, cop_entry, flags)

    # Record the emitted default provenance on the building's row (T02). Instrumentation
    # only — the default VALUES above are unchanged, so simulated EUI does not move.
    for tok in sorted(flags):
        row["data_quality_flag"] = provenance.append_flag_token(
            row.get("data_quality_flag"), tok
        )
    return sorted(flags)
