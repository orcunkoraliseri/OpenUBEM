"""Phase-E cooking emitter: GasEquipment + ElectricEquipment + kitchen exhaust (T10, D6).

Deviation from D6: uses GasEquipment (not OtherEquipment) so cooking gas meters to
InteriorEquipment:NaturalGas (T12 meter requirement). OtherEquipment(NaturalGas)
routes to a different meter family.
"""
import json
import math
from pathlib import Path

from openubem.semantic import provenance

_COOK_DATA = json.loads(
    (Path(__file__).parent.parent / "data/loads/cooking_by_archetype.json").read_text()
)
_HGF = _COOK_DATA["_heat_gain_fractions"]


def _resolve_area(row, flags):
    """footprint_area_m2 with provenance (T03). absent/None -> 400.0 (+DEFAULT token);
    stored 0 -> kept (+SUSPECT_ZERO token); real value -> unchanged."""
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
    provenance token in `flags`; default VALUES are unchanged (T03, instrumentation).
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


def _sched_cook_exhaust_once(idf, name):
    """Kitchen exhaust operating window: 5am-1am (RESULT_04 Table 3), not 24/7."""
    if any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:COMPACT", [])):
        return
    s = idf.newidfobject("SCHEDULE:COMPACT")
    s.Name = name
    s.Field_1 = "Through: 12/31"
    s.Field_2 = "For: AllDays"
    s.Field_3 = "Until: 01:00"
    s.Field_4 = "1.0"
    s.Field_5 = "Until: 05:00"
    s.Field_6 = "0.0"
    s.Field_7 = "Until: 24:00"
    s.Field_8 = "1.0"


def assign_cooking(idf, row, zones):
    """Emit cooking process loads + kitchen exhaust ventilation (D6).

    Returns the sorted geometry-default provenance tokens (T03); they are also
    appended in place to ``row['data_quality_flag']``. The table-driven no_cooking
    skip is preserved and runs BEFORE any geometry resolution, so a no_cooking
    archetype emits no area/floors default token.
    """
    if not zones:  # degenerate geometry: no zone to host equipment (D4a defensive guard)
        return []
    arch = str(row["archetype_id"])
    data = _COOK_DATA.get(arch, {})
    if data.get("no_cooking"):
        return []

    flags: set = set()
    total_area = _total_floor_area(row, zones, flags)
    for tok in sorted(flags):
        row["data_quality_flag"] = provenance.append_flag_token(
            row.get("data_quality_flag"), tok
        )
    zone_name = zones[0]["name"]

    gas_w_m2 = data.get("gas_density_w_m2", 0.0)
    elec_w_m2 = data.get("elec_density_w_m2", 0.0)

    # Per-fuel schedule fractions (RESULT_04 Table 1)
    gas_frac = float(
        data.get("schedule_peak_fraction_gas", data.get("schedule_peak_fraction", 1.0))
    )
    elec_frac = float(
        data.get("schedule_peak_fraction_elec", data.get("schedule_peak_fraction", 1.0))
    )

    gas_sched = f"OpenUBEM_Cook_Gas_{arch}"
    elec_sched = f"OpenUBEM_Cook_Elec_{arch}"
    _sched_constant_once(idf, gas_sched, gas_frac)
    _sched_constant_once(idf, elec_sched, elec_frac)

    # GasEquipment — cooking gas routed to InteriorEquipment:NaturalGas (T12)
    hg_gas_key = data.get("heat_gain_gas")
    if gas_w_m2 > 0 and hg_gas_key:
        hgf = _HGF[hg_gas_key]
        gas_eq = idf.newidfobject("GASEQUIPMENT")
        gas_eq.Name = f"Cooking_Gas_{arch}"
        gas_eq.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
        gas_eq.Schedule_Name = gas_sched
        gas_eq.Design_Level_Calculation_Method = "EquipmentLevel"
        gas_eq.Design_Level = round(gas_w_m2 * total_area, 2)
        gas_eq.Fraction_Latent = hgf["latent"]
        gas_eq.Fraction_Radiant = hgf["radiant"]
        gas_eq.Fraction_Lost = hgf["lost"]
        gas_eq.EndUse_Subcategory = "Cooking"

    # ElectricEquipment — cooking electric routed to Cooking:InteriorEquipment:Electricity (T12)
    hg_elec_key = data.get("heat_gain_elec")
    if elec_w_m2 > 0 and hg_elec_key:
        hgf = _HGF[hg_elec_key]
        elec_eq = idf.newidfobject("ELECTRICEQUIPMENT")
        elec_eq.Name = f"Cooking_Elec_{arch}"
        elec_eq.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
        elec_eq.Schedule_Name = elec_sched
        elec_eq.Design_Level_Calculation_Method = "EquipmentLevel"
        elec_eq.Design_Level = round(elec_w_m2 * total_area, 2)
        elec_eq.Fraction_Latent = hgf["latent"]
        elec_eq.Fraction_Radiant = hgf["radiant"]
        elec_eq.Fraction_Lost = hgf["lost"]
        elec_eq.EndUse_Subcategory = "Cooking"

    # Kitchen exhaust ventilation (RESULT_04 Table 3). The tabulated exhaust_m3_s is the
    # whole-prototype-kitchen design flow; scale it by the building's floor area vs the
    # archetype prototype so a small building gets a proportional (not full) hood exhaust,
    # capped at the prototype value. Unscaled flow on a tiny single-zone building drove a
    # ~36 kW make-up-air conditioning runaway (CP-R1 root cause). Run on the prototype
    # 5am-1am operating window, not 24/7. Make-up air stays fully conditioned (prototype).
    exhaust_m3_s = data.get("exhaust_m3_s")
    if exhaust_m3_s:
        proto_area = data.get("prototype_floor_area_m2")
        scale = min(1.0, total_area / proto_area) if proto_area else 1.0
        _sched_cook_exhaust_once(idf, "OpenUBEM_Cook_ExhaustSched")
        vent = idf.newidfobject("ZONEVENTILATION:DESIGNFLOWRATE")
        vent.Name = f"KitchenExhaust_{arch}"
        vent.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
        vent.Schedule_Name = "OpenUBEM_Cook_ExhaustSched"
        vent.Design_Flow_Rate_Calculation_Method = "Flow/Zone"
        vent.Design_Flow_Rate = round(float(exhaust_m3_s) * scale, 4)
        vent.Ventilation_Type = "Exhaust"

    return sorted(flags)
