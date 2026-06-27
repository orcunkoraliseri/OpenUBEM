"""Phase-E cooking emitter: GasEquipment + ElectricEquipment + kitchen exhaust (T10, D6).

Deviation from D6: uses GasEquipment (not OtherEquipment) so cooking gas meters to
InteriorEquipment:NaturalGas (T12 meter requirement). OtherEquipment(NaturalGas)
routes to a different meter family.
"""
import json
from pathlib import Path

_COOK_DATA = json.loads(
    (Path(__file__).parent.parent / "data/loads/cooking_by_archetype.json").read_text()
)
_HGF = _COOK_DATA["_heat_gain_fractions"]


def _total_floor_area(row, zones):
    """Footprint × unique-floor count extracted from zone names."""
    footprint = float(row.get("footprint_area_m2") or 400.0)
    floor_idx = set()
    for z in zones:
        parts = z.get("name", "").split("_F")
        if len(parts) >= 2:
            fi = parts[1].split("_")[0]
            if fi.isdigit():
                floor_idx.add(fi)
    return footprint * max(len(floor_idx), 1)


def _sched_constant_once(idf, name, value):
    if not any(s.Name == name for s in idf.idfobjects.get("SCHEDULE:CONSTANT", [])):
        s = idf.newidfobject("SCHEDULE:CONSTANT")
        s.Name = name
        s.Hourly_Value = value


def assign_cooking(idf, row, zones):
    """Emit cooking process loads + kitchen exhaust ventilation (D6)."""
    arch = str(row["archetype_id"])
    data = _COOK_DATA.get(arch, {})
    if data.get("no_cooking"):
        return

    total_area = _total_floor_area(row, zones)
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

    # Kitchen exhaust ventilation (where specified; D6 "zone exhaust/OA")
    exhaust_m3_s = data.get("exhaust_m3_s")
    if exhaust_m3_s:
        _sched_constant_once(idf, "OpenUBEM_Cook_ExhaustSched", 1.0)
        vent = idf.newidfobject("ZONEVENTILATION:DESIGNFLOWRATE")
        vent.Name = f"KitchenExhaust_{arch}"
        vent.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
        vent.Schedule_Name = "OpenUBEM_Cook_ExhaustSched"
        vent.Design_Flow_Rate_Calculation_Method = "Flow/Zone"
        vent.Design_Flow_Rate = float(exhaust_m3_s)
        vent.Ventilation_Type = "Exhaust"
