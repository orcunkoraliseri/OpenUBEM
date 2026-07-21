"""Phase-E elevator emitter: ElectricEquipment lift motor, DOE ElevatorLift/Elevators verbatim (T01, T02).

Deviation from DOE source: LargeOffice/LargeHotel/Hospital model the lift as
Exterior:FuelEquipment (no zone, no heat gain). OpenUBEM emits the interior-equivalent
ElectricEquipment form per PLAN §3 Dependency decision, using a Fraction_Radiant=0.5/
Latent=0/Lost=0 default for those three only; every other archetype transcribes its
DOE-authored heat-gain split verbatim (see elevators_by_archetype.json).
"""
import json
from pathlib import Path

from openubem.semantic import provenance
from openubem.idf.cooking import _total_floor_area

_ELEV_DATA = json.loads(
    (Path(__file__).parent.parent / "data/loads/elevators_by_archetype.json").read_text()
)


def assign_elevators(idf, row, zones):
    """Emit the DOE-verbatim elevator lift motor as ElectricEquipment (T02).

    Returns the sorted geometry-default provenance tokens (T03 pattern); they are also
    appended in place to ``row['data_quality_flag']``. Archetypes absent from the table
    (no DOE ElevatorLift/Elevators object found in source) emit nothing — byte-identical
    to today. The absent-archetype skip runs BEFORE any geometry resolution, matching
    cooking.assign_cooking's no_cooking early-return.
    """
    if not zones:  # degenerate geometry: no zone to host equipment (D4a defensive guard)
        return []
    arch = str(row["archetype_id"])
    data = _ELEV_DATA.get(arch)
    if data is None:
        return []

    flags: set = set()
    total_area = _total_floor_area(row, zones, flags)
    for tok in sorted(flags):
        row["data_quality_flag"] = provenance.append_flag_token(
            row.get("data_quality_flag"), tok
        )
    zone_name = zones[0]["name"]

    proto_area = data["prototype_floor_area_m2"]
    design_level_w = data["design_level_w"] * total_area / proto_area

    sched_name = f"OpenUBEM_Elevators_{arch}"
    if not any(s.Name == sched_name for s in idf.idfobjects.get("SCHEDULE:COMPACT", [])):
        sched = idf.newidfobject("SCHEDULE:COMPACT")
        sched.Name = sched_name
        sched.Schedule_Type_Limits_Name = "Fraction"
        for i, val in enumerate(data["schedule_fields"], start=1):
            setattr(sched, f"Field_{i}", val)

    hgf = data["heat_gain"]
    elev = idf.newidfobject("ELECTRICEQUIPMENT")
    elev.Name = f"Elevators_{arch}"
    elev.Zone_or_ZoneList_or_Space_or_SpaceList_Name = zone_name
    elev.Schedule_Name = sched_name
    elev.Design_Level_Calculation_Method = "EquipmentLevel"
    elev.Design_Level = round(design_level_w, 2)
    elev.Fraction_Latent = hgf["latent"]
    elev.Fraction_Radiant = hgf["radiant"]
    elev.Fraction_Lost = hgf["lost"]
    elev.EndUse_Subcategory = "Elevators"

    return sorted(flags)
