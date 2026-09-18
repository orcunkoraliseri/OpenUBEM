"""Scenario/retrofit measure table, gates, and applier (plan block-5 J02).

Not wired into the build path. The only importer of `openubem.scenarios` is
`tests/test_scenario_measures.py` (see PLAN_techtransfer-block5-2026-09-17.md rule 3).

Table: `openubem/data/scenarios/measures.json`. One key per measure id, each carrying `name`,
`description`, `parameters`, `source`, `gates`, `status` ("active" or "withdrawn" +
`withdrawn_reason`). Provenance for every numeric parameter:
`openubem/data/scenarios/PROVENANCE.md`.

Measures shipped in this task, and only these two:

- `lighting_power_density` — lowers `Watts_per_Zone_Floor_Area` on `LIGHTS` objects whose
  `Design_Level_Calculation_Method == "Watts/Area"` to a public target, never raising it. The
  target is an Office-occupancy figure, so `applicable_measures`/`apply_measure` take an explicit
  `archetype` keyword and only act when it is in the measure row's `in_scope_archetypes` list.
  Gates: `gate_archetype_out_of_scope` (archetype is None, unknown, or not in scope: fails closed),
  `gate_lighting_method` (skips a Lights object not on Watts/Area),
  `gate_zero_lpd` (skips a Lights object already at exactly 0.0 W/m2).
- `envelope_u_upgrade` — **withdrawn** (see `measures.json["envelope_u_upgrade"]["withdrawn_reason"]`
  and `PROVENANCE.md`): its shipped targets were byte-identical to the code baseline OpenUBEM
  already applies, so it was a guaranteed no-op on its own archetype. `apply_measure` refuses to
  run it (reports `status: "withdrawn"`, changes nothing). The applier code below
  (`_apply_envelope_u_upgrade`) and its gate stay in place, unused by the public entry point, for
  reuse if a verified better-than-baseline target is supplied later. It still delegates to
  `openubem.geometry.envelope_patcher.patch_envelope()`: wall/roof/floor via a current-vs-target
  minimum computed here, window/SHGC via `patch_envelope(skip_when_better=True)`. Gate:
  `gate_no_fenestration` (no FenestrationSurface:Detailed in the idf).

Measure shipped in this task (plan block-5 J03), active:

- `thermostat_setback` — for each `THERMOSTATSETPOINT:DUALSETPOINT` object, examines its heating
  and cooling setpoint `Schedule:Compact` schedules. A schedule whose temperature values are
  constant across the whole schedule (no setback at all) is deepened, by cloning it and lowering
  (heating) / raising (cooling) the values outside a single occupied reference block, to the
  magnitude ASHRAE 90.1-2022 Section 6.4.3.3.2 requires a setback control to be capable of. A
  schedule with an existing setback shallower than that magnitude is deepened the same way; one
  already at or past the required magnitude is reported `already_compliant` and left untouched.
  Direction rule: only ever deepens or leaves equal, never narrows. Only the specific thermostat
  object being fixed is repointed to the clone; every other object still naming the original
  schedule is untouched (see `clone_schedule` below and the module's PROVENANCE.md for the
  245-shared-reference and 15-shared-thermostat cases this is built against).
  Gates: `gate_no_thermostat` (idf has no `ThermostatSetpoint:DualSetpoint`), `gate_schedule_missing`
  (a setpoint schedule named on the thermostat is not a `Schedule:Compact` present in the idf).

Measure shipped in this task (plan block-5 J04, revised J04b), withdrawn pending manager
verification:

- `infiltration_tightening` — **withdrawn** (see `measures.json["infiltration_tightening"]["withdrawn_reason"]`
  and `PROVENANCE.md`): `apply_measure` refuses to run it and changes nothing, pending J04c
  verification against a real DOE prototype. Computes three building-level areas once: `S` (the
  whole-building envelope area, from every `BuildingSurface:Detailed` (Wall, Roof, Ceiling, Floor)
  whose `Outside_Boundary_Condition` is Outdoors, Ground, GroundFCfactorMethod,
  GroundSlabPreprocessorAverage or OtherSideCoefficients), `AFLR` (the summed gross floor area of
  every zone that owns a `ZoneInfiltration:DesignFlowRate` object) and `AAGW` (the summed
  above-grade exterior wall area, `Outside_Boundary_Condition == Outdoors` only, of those same
  zones). Applies ASHRAE 90.1-2019 Addendum t Section 11.5.3's own intensities uniformly, exactly as
  written, no invented distribution: `IFLR = conversion_factor x i75pa_target_m3_s_m2 x S / AFLR` to
  every `Flow/Area` object, `IAGW = conversion_factor x i75pa_target_m3_s_m2 x S / AAGW` to every
  `Flow/ExteriorWallArea` object. `Flow/Zone` and `Flow/ExteriorArea` have no formula in Section
  11.5.3 and are gated unconditionally rather than approximated. Each covered object's existing
  declared value (already in m3/s-m2, the field's native unit) is compared directly against the
  uniform intensity for its method and the lower of the two is kept and written back through that
  same field; an object already at or below the uniform intensity is reported `already_compliant`
  and left byte-identical. `Design_Flow_Rate_Calculation_Method` is never changed and leakage is
  never moved between zones.
  Gates: `gate_no_infiltration_objects` (idf has no `ZoneInfiltration:DesignFlowRate`),
  `gate_unknown_calculation_method` (a calculation method outside the four supported, or a
  `ZoneInfiltration:EffectiveLeakageArea` / `ZoneInfiltration:FlowCoefficient` object),
  `gate_unsupported_calculation_method` (`Flow/Zone` or `Flow/ExteriorArea`: a real
  `ZoneInfiltration:DesignFlowRate` method Section 11.5.3 states no formula for),
  `gate_zero_normalizing_area` (the building-level `AFLR` or `AAGW` needed by that object's method
  is zero), `gate_no_geometry` (`S` computes to zero), `gate_unsupported_coefficients` (the object's
  four infiltration coefficients are not the DOE-2 wind-driven set `(0, 0, 0.224, 0)` within
  `1e-6`).

`clone_schedule(idf, schedule_name, new_name) -> str` — public helper. Creates a new
`Schedule:Compact` object under `new_name` that is a full copy of the named one (every populated
field, not just the first few — `Schedule:Compact` is extensible and its real field count is
`len(obj.fieldvalues)`, not `len(obj.fieldnames)`: eppy pads `fieldnames` to the IDD's extensible
maximum, 10001 entries, regardless of how many fields are actually set, so the copy is capped at
the source object's real field count). Does not modify the original and does not repoint anything;
repointing is the caller's job.
"""

import json
import re
from pathlib import Path
from typing import Any

from openubem.geometry import envelope_patcher

_MEASURES_PATH = Path(__file__).parent.parent / "data/scenarios/measures.json"

_NON_WORKDAY_KEYWORDS = ("weekend", "saturday", "sunday", "holiday", "allotherday", "custom")
_DESIGN_DAY_KEYWORDS = ("winterdesignday", "summerdesignday")
_UNTIL_RE = re.compile(r"until:\s*(\d{1,2}):(\d{2})", re.IGNORECASE)

_ENVELOPE_SURFACE_TYPES = {"wall", "roof", "ceiling", "floor"}
_ENVELOPE_BOUNDARY_CONDITIONS = {
    "outdoors", "ground", "groundfcfactormethod", "groundslabpreprocessoraverage",
    "othersidecoefficients",
}
_INFILTRATION_METHOD_FIELDS = {
    "flow/zone": ("Design_Flow_Rate", None),
    "flow/area": ("Flow_Rate_per_Floor_Area", "floor"),
    "flow/exteriorarea": ("Flow_Rate_per_Exterior_Surface_Area", "exterior"),
    "flow/exteriorwallarea": ("Flow_Rate_per_Exterior_Surface_Area", "exterior_wall"),
}
_DOE2_INFILTRATION_COEFFICIENTS = (0.0, 0.0, 0.224, 0.0)
_COEFFICIENT_TOLERANCE = 1e-6
_UNSUPPORTED_CALCULATION_METHODS = {"flow/zone", "flow/exteriorarea"}


def load_measures() -> dict:
    return json.loads(_MEASURES_PATH.read_text())


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _lighting_applicability(idf: Any, archetype: "str | None", in_scope: "list[str]") -> dict:
    if archetype is None or archetype not in in_scope:
        return {"applicable": False, "gate": "gate_archetype_out_of_scope"}
    lights = idf.idfobjects.get("LIGHTS", [])
    watts_area = [
        L for L in lights
        if str(getattr(L, "Design_Level_Calculation_Method", "")).strip().lower() == "watts/area"
    ]
    if not watts_area:
        return {"applicable": False, "gate": "gate_lighting_method"}
    nonzero = [L for L in watts_area if _to_float(getattr(L, "Watts_per_Zone_Floor_Area", 0.0)) > 0.0]
    if not nonzero:
        return {"applicable": False, "gate": "gate_zero_lpd"}
    return {"applicable": True, "gate": None}


def _envelope_applicability(idf: Any) -> dict:
    has_fen = bool(idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", []))
    return {"applicable": True, "gate": None if has_fen else "gate_no_fenestration"}


def _thermostat_applicability(idf: Any) -> dict:
    thermostats = idf.idfobjects.get("THERMOSTATSETPOINT:DUALSETPOINT", [])
    if not thermostats:
        return {"applicable": False, "gate": "gate_no_thermostat"}
    return {"applicable": True, "gate": None}


def applicable_measures(
    idf: Any, measure_ids: "list[str] | None" = None, archetype: "str | None" = None
) -> dict:
    table = load_measures()
    ids = list(measure_ids) if measure_ids else list(table.keys())
    result = {}
    for mid in ids:
        if mid not in table:
            result[mid] = {"applicable": False, "gate": None}
            continue
        measure = table[mid]
        if measure.get("status") == "withdrawn":
            result[mid] = {
                "applicable": False,
                "gate": None,
                "status": "withdrawn",
                "withdrawn_reason": measure.get("withdrawn_reason"),
            }
            continue
        if mid == "lighting_power_density":
            result[mid] = _lighting_applicability(
                idf, archetype, measure.get("in_scope_archetypes", [])
            )
        elif mid == "envelope_u_upgrade":
            result[mid] = _envelope_applicability(idf)
        elif mid == "thermostat_setback":
            result[mid] = _thermostat_applicability(idf)
        elif mid == "infiltration_tightening":
            result[mid] = _infiltration_applicability(idf)
        else:
            result[mid] = {"applicable": False, "gate": None}
    return result


def _material_r_value(idf: Any, material_name: str) -> "float | None":
    name = str(material_name).strip().lower()
    for m in idf.idfobjects.get("MATERIAL:NOMASS", []):
        if str(m.Name).strip().lower() == name:
            return _to_float(m.Thermal_Resistance)
    for m in idf.idfobjects.get("MATERIAL", []):
        if str(m.Name).strip().lower() == name:
            thickness = _to_float(m.Thickness)
            conductivity = _to_float(m.Conductivity)
            if conductivity > 0:
                return thickness / conductivity
    return None


def _construction_u_value(idf: Any, construction_name: str) -> "float | None":
    name = str(construction_name).strip().lower()
    cons = next(
        (c for c in idf.idfobjects.get("CONSTRUCTION", []) if str(c.Name).strip().lower() == name),
        None,
    )
    if cons is None:
        return None
    total_r = 0.0
    for fname in getattr(cons, "fieldnames", []):
        if fname != "Outside_Layer" and not fname.startswith("Layer_"):
            continue
        layer_name = getattr(cons, fname, "")
        if not str(layer_name).strip():
            continue
        r = _material_r_value(idf, layer_name)
        if r is None:
            return None
        total_r += r
    if total_r <= 0:
        return None
    return 1.0 / total_r


def _max_opaque_u(idf: Any, surface_types: "str | tuple") -> "float | None":
    if isinstance(surface_types, str):
        surface_types = (surface_types,)
    wanted = {s.lower() for s in surface_types}
    values = []
    for surf in idf.getsurfaces():
        if surf.Surface_Type.lower() not in wanted:
            continue
        obc = str(getattr(surf, "Outside_Boundary_Condition", "")).strip().lower()
        if obc == "groundfcfactormethod":
            continue
        u = _construction_u_value(idf, surf.Construction_Name)
        if u is not None:
            values.append(u)
    return max(values) if values else None


def _apply_lighting_power_density(
    idf: Any, measure: dict, enabled: bool, archetype: "str | None" = None
) -> dict:
    target = float(measure["parameters"]["target_lpd_w_m2"])
    in_scope = measure.get("in_scope_archetypes", [])
    if archetype is None or archetype not in in_scope:
        return {
            "measure_id": "lighting_power_density",
            "enabled": enabled,
            "archetype": archetype,
            "status": "gate_archetype_out_of_scope",
            "gate": "gate_archetype_out_of_scope",
            "target_lpd_w_m2": target,
            "objects": [],
            "n_lowered": 0,
            "n_already_compliant": 0,
            "n_skipped_gate_lighting_method": 0,
            "n_skipped_gate_zero_lpd": 0,
        }
    objects = []
    for L in idf.idfobjects.get("LIGHTS", []):
        name = getattr(L, "Name", "")
        method = str(getattr(L, "Design_Level_Calculation_Method", "")).strip()
        if method.lower() != "watts/area":
            objects.append({"name": name, "status": "skipped", "gate": "gate_lighting_method"})
            continue
        current = _to_float(getattr(L, "Watts_per_Zone_Floor_Area", 0.0))
        if current == 0.0:
            objects.append({"name": name, "status": "skipped", "gate": "gate_zero_lpd"})
            continue
        if current <= target:
            objects.append({"name": name, "status": "already_compliant", "value_w_m2": current})
            continue
        objects.append(
            {"name": name, "status": "lowered", "from_w_m2": current, "to_w_m2": target}
        )
        if enabled:
            L.Watts_per_Zone_Floor_Area = target
    n_lowered = sum(1 for o in objects if o["status"] == "lowered")
    n_already_compliant = sum(1 for o in objects if o["status"] == "already_compliant")
    if enabled and n_lowered > 0:
        status = "applied"
    elif not enabled:
        status = "disabled"
    elif n_already_compliant > 0:
        status = "already_compliant"
    else:
        status = "no_applicable_objects"
    return {
        "measure_id": "lighting_power_density",
        "enabled": enabled,
        "archetype": archetype,
        "status": status,
        "target_lpd_w_m2": target,
        "objects": objects,
        "n_lowered": n_lowered,
        "n_already_compliant": n_already_compliant,
        "n_skipped_gate_lighting_method": sum(
            1 for o in objects if o.get("gate") == "gate_lighting_method"
        ),
        "n_skipped_gate_zero_lpd": sum(1 for o in objects if o.get("gate") == "gate_zero_lpd"),
    }


def _apply_envelope_u_upgrade(idf: Any, measure: dict, enabled: bool) -> dict:
    params = measure["parameters"]
    target_wall = float(params["u_wall_w_m2k"])
    target_roof = float(params["u_roof_w_m2k"])
    target_floor = float(params["u_floor_w_m2k"])
    target_window = float(params["u_window_w_m2k"])
    target_shgc = float(params["shgc_window"])

    has_fen = bool(idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", []))

    current_wall = _max_opaque_u(idf, "wall")
    current_roof = _max_opaque_u(idf, "roof")
    current_floor = _max_opaque_u(idf, ("floor", "ceiling"))

    row_wall = min(target_wall, current_wall) if current_wall is not None else target_wall
    row_roof = min(target_roof, current_roof) if current_roof is not None else target_roof
    row_floor = min(target_floor, current_floor) if current_floor is not None else target_floor

    row = {
        "archetype_id": "scenario_envelope_u_upgrade",
        "u_wall_w_m2k": row_wall,
        "u_roof_w_m2k": row_roof,
        "u_floor_w_m2k": row_floor,
        "u_window_w_m2k": target_window,
        "shgc_window": target_shgc,
    }

    summary = {
        "measure_id": "envelope_u_upgrade",
        "enabled": enabled,
        "wall": {"from_w_m2k": current_wall, "to_w_m2k": row_wall},
        "roof": {"from_w_m2k": current_roof, "to_w_m2k": row_roof},
        "floor": {"from_w_m2k": current_floor, "to_w_m2k": row_floor},
        "window": {
            "applied": has_fen,
            "gate": None if has_fen else "gate_no_fenestration",
            "to_w_m2k": target_window if has_fen else None,
            "to_shgc": target_shgc if has_fen else None,
        },
    }
    if enabled:
        envelope_patcher.patch_envelope(idf, row, skip_when_better=True)
    return summary


def _find_compact_schedule(idf: Any, name: "str | None") -> "Any | None":
    if not name:
        return None
    target = str(name).strip().lower()
    for s in idf.idfobjects.get("SCHEDULE:COMPACT", []):
        if str(s.Name).strip().lower() == target:
            return s
    return None


def clone_schedule(idf: Any, schedule_name: str, new_name: str) -> str:
    original = _find_compact_schedule(idf, schedule_name)
    if original is None:
        raise ValueError(f"clone_schedule: no Schedule:Compact named {schedule_name!r}")
    clone = idf.newidfobject("SCHEDULE:COMPACT")
    fieldnames = original.fieldnames
    fieldvalues = original.fieldvalues
    for fname, fvalue in zip(fieldnames[1:len(fieldvalues)], fieldvalues[1:]):
        setattr(clone, fname, fvalue)
    clone.Name = new_name
    return new_name


def _parse_until_minutes(text: str) -> "int | None":
    m = _UNTIL_RE.search(text)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _is_day_header(low: str) -> bool:
    return low.startswith("for:") or low.startswith("for ")


def _is_design_day(for_str: str) -> bool:
    low = for_str.lower()
    return any(k in low for k in _DESIGN_DAY_KEYWORDS)


def _parse_compact_value_entries(sched: Any) -> "list[dict]":
    fieldnames = sched.fieldnames
    fieldvalues = sched.fieldvalues
    entries = []
    current_for = ""
    current_until_min = None
    for idx in range(3, len(fieldvalues)):
        raw = fieldvalues[idx]
        text = str(raw).strip()
        low = text.lower()
        if low.startswith("through:"):
            continue
        if _is_day_header(low):
            current_for = text
            current_until_min = None
            continue
        if low.startswith("until:"):
            current_until_min = _parse_until_minutes(text)
            continue
        value = _to_float(raw, default=None)
        if value is None:
            continue
        if _is_design_day(current_for):
            continue
        entries.append(
            {
                "field_name": fieldnames[idx],
                "for_str": current_for,
                "until_minutes": current_until_min if current_until_min is not None else 1440,
                "value": value,
            }
        )
    return entries


def _is_nonworkday(for_str: str) -> bool:
    low = for_str.lower()
    return any(k in low for k in _NON_WORKDAY_KEYWORDS)


def _derive_occupied_and_setback(values: "list[float]", role: str) -> "tuple[float, float]":
    if role == "heating":
        return max(values), min(values)
    return min(values), max(values)


def _evaluate_setpoint_schedule(sched: Any, delta_c: float, role: str) -> "dict | None":
    entries = _parse_compact_value_entries(sched)
    workday_entries = [e for e in entries if not _is_nonworkday(e["for_str"])]
    if not workday_entries:
        return None
    values = [e["value"] for e in workday_entries]
    magnitude_c = max(values) - min(values)
    occupied, setback_level = _derive_occupied_and_setback(values, role)
    if occupied == setback_level:
        return {"magnitude_c": magnitude_c, "changes": [], "gate": "gate_no_setback_block"}
    changes = []
    for e in workday_entries:
        if e["value"] != setback_level:
            continue
        if role == "heating":
            new_value = occupied - delta_c
            if new_value >= e["value"]:
                continue
        else:
            new_value = occupied + delta_c
            if new_value <= e["value"]:
                continue
        changes.append({"field_name": e["field_name"], "from": e["value"], "to": new_value})
    return {"magnitude_c": magnitude_c, "changes": changes, "gate": None}


def _apply_thermostat_setback(idf: Any, measure: dict, enabled: bool) -> dict:
    params = measure["parameters"]
    delta_heat = float(params["heating_setback_delta_c"])
    delta_cool = float(params["cooling_setup_delta_c"])
    thermostats = idf.idfobjects.get("THERMOSTATSETPOINT:DUALSETPOINT", [])
    if not thermostats:
        return {
            "measure_id": "thermostat_setback",
            "enabled": enabled,
            "status": "gate_no_thermostat",
            "gate": "gate_no_thermostat",
            "objects": [],
            "n_applied": 0,
            "n_already_compliant": 0,
            "n_gate_schedule_missing": 0,
        }
    objects = []
    any_applied = False
    any_already_compliant = False
    any_gate_missing = False
    any_gate_no_setback_block = False
    roles = (
        ("heating", "Heating_Setpoint_Temperature_Schedule_Name", delta_heat, "lowered"),
        ("cooling", "Cooling_Setpoint_Temperature_Schedule_Name", delta_cool, "raised"),
    )
    for t in thermostats:
        name = getattr(t, "Name", "")
        for role, field_attr, delta_c, applied_label in roles:
            sched_name = str(getattr(t, field_attr, "")).strip()
            sched = _find_compact_schedule(idf, sched_name)
            if sched is None:
                objects.append(
                    {
                        "thermostat": name, "role": role, "schedule": sched_name,
                        "status": "gate_schedule_missing", "gate": "gate_schedule_missing",
                    }
                )
                any_gate_missing = True
                continue
            evaluation = _evaluate_setpoint_schedule(sched, delta_c, role)
            if evaluation is None:
                objects.append(
                    {
                        "thermostat": name, "role": role, "schedule": sched_name,
                        "status": "gate_schedule_missing", "gate": "gate_schedule_missing",
                    }
                )
                any_gate_missing = True
                continue
            if evaluation.get("gate") == "gate_no_setback_block":
                objects.append(
                    {
                        "thermostat": name, "role": role, "schedule": sched_name,
                        "status": "gate_no_setback_block", "gate": "gate_no_setback_block",
                        "magnitude_c": evaluation["magnitude_c"],
                    }
                )
                any_gate_no_setback_block = True
                continue
            if not evaluation["changes"]:
                objects.append(
                    {
                        "thermostat": name, "role": role, "schedule": sched_name,
                        "status": "already_compliant", "magnitude_c": evaluation["magnitude_c"],
                    }
                )
                any_already_compliant = True
                continue
            new_name = f"{sched_name}__setback_{name}_{role}"
            objects.append(
                {
                    "thermostat": name, "role": role, "schedule": sched_name,
                    "status": applied_label, "new_schedule": new_name,
                    "magnitude_c": evaluation["magnitude_c"], "required_delta_c": delta_c,
                }
            )
            any_applied = True
            if enabled:
                clone_schedule(idf, sched_name, new_name)
                clone = _find_compact_schedule(idf, new_name)
                for ch in evaluation["changes"]:
                    setattr(clone, ch["field_name"], ch["to"])
                setattr(t, field_attr, new_name)
    if enabled and any_applied:
        status = "applied"
    elif not enabled:
        status = "disabled"
    elif any_already_compliant:
        status = "already_compliant"
    elif any_gate_missing:
        status = "gate_schedule_missing"
    elif any_gate_no_setback_block:
        status = "gate_no_setback_block"
    else:
        status = "no_applicable_objects"
    return {
        "measure_id": "thermostat_setback",
        "enabled": enabled,
        "status": status,
        "gate": status if status in ("gate_schedule_missing", "gate_no_setback_block") else None,
        "objects": objects,
        "n_applied": sum(1 for o in objects if o["status"] in ("lowered", "raised")),
        "n_already_compliant": sum(1 for o in objects if o["status"] == "already_compliant"),
        "n_gate_schedule_missing": sum(1 for o in objects if o.get("gate") == "gate_schedule_missing"),
        "n_gate_no_setback_block": sum(1 for o in objects if o.get("gate") == "gate_no_setback_block"),
    }


def _compute_envelope_area_s(idf: Any) -> float:
    total = 0.0
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        surface_type = str(getattr(s, "Surface_Type", "")).strip().lower()
        if surface_type not in _ENVELOPE_SURFACE_TYPES:
            continue
        obc = str(getattr(s, "Outside_Boundary_Condition", "")).strip().lower()
        if obc not in _ENVELOPE_BOUNDARY_CONDITIONS:
            continue
        total += s.area
    return total


def _zone_surface_area(
    idf: Any, zone_name: str, surface_types: "set[str] | None", exterior_only: bool
) -> float:
    total = 0.0
    target_zone = str(zone_name).strip()
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        if str(getattr(s, "Zone_Name", "")).strip() != target_zone:
            continue
        if surface_types is not None:
            if str(getattr(s, "Surface_Type", "")).strip().lower() not in surface_types:
                continue
        if exterior_only:
            obc = str(getattr(s, "Outside_Boundary_Condition", "")).strip().lower()
            if obc != "outdoors":
                continue
        total += s.area
    return total


def _zone_area_for_kind(idf: Any, zone_name: str, kind: "str | None") -> "float | None":
    if kind is None:
        return None
    if kind == "floor":
        return _zone_surface_area(idf, zone_name, {"floor"}, exterior_only=False)
    if kind == "exterior":
        return _zone_surface_area(idf, zone_name, None, exterior_only=True)
    if kind == "exterior_wall":
        return _zone_surface_area(idf, zone_name, {"wall"}, exterior_only=True)
    raise ValueError(f"_zone_area_for_kind: unknown kind {kind!r}")


def _infiltration_coefficients(obj: Any) -> tuple:
    return (
        _to_float(getattr(obj, "Constant_Term_Coefficient", 0.0)),
        _to_float(getattr(obj, "Temperature_Term_Coefficient", 0.0)),
        _to_float(getattr(obj, "Velocity_Term_Coefficient", 0.0)),
        _to_float(getattr(obj, "Velocity_Squared_Term_Coefficient", 0.0)),
    )


def _coefficients_match_doe2(coefficients: tuple) -> bool:
    return all(
        abs(m - t) <= _COEFFICIENT_TOLERANCE
        for m, t in zip(coefficients, _DOE2_INFILTRATION_COEFFICIENTS)
    )


def _infiltration_applicability(idf: Any) -> dict:
    if not idf.idfobjects.get("ZONEINFILTRATION:DESIGNFLOWRATE", []):
        return {"applicable": False, "gate": "gate_no_infiltration_objects"}
    if _compute_envelope_area_s(idf) <= 0.0:
        return {"applicable": False, "gate": "gate_no_geometry"}
    return {"applicable": True, "gate": None}


def _infiltration_gate_summary(
    enabled: bool, conversion_factor: float, i75pa_target: float, status: str,
    unsupported_entries: list, envelope_area_s: float = 0.0, aflr: float = 0.0, aagw: float = 0.0,
) -> dict:
    return {
        "measure_id": "infiltration_tightening",
        "enabled": enabled,
        "status": status,
        "gate": status if status.startswith("gate_") else None,
        "conversion_factor": conversion_factor,
        "i75pa_target_m3_s_m2": i75pa_target,
        "envelope_area_s_m2": envelope_area_s,
        "floor_area_aflr_m2": aflr,
        "exterior_wall_area_aagw_m2": aagw,
        "q_design_total_m3_s": 0.0,
        "objects": unsupported_entries,
        "n_tightened": 0,
        "n_already_compliant": 0,
        "n_gate_unknown_calculation_method": len(unsupported_entries),
        "n_gate_unsupported_calculation_method": 0,
        "n_gate_zero_normalizing_area": 0,
        "n_gate_unsupported_coefficients": 0,
    }


def _apply_infiltration_tightening(idf: Any, measure: dict, enabled: bool) -> dict:
    params = measure["parameters"]
    conversion_factor = float(params["conversion_factor"])
    i75pa_target = float(params["i75pa_target_m3_s_m2"])

    infiltration_objects = list(idf.idfobjects.get("ZONEINFILTRATION:DESIGNFLOWRATE", []))
    unsupported_objects = list(idf.idfobjects.get("ZONEINFILTRATION:EFFECTIVELEAKAGEAREA", []))
    unsupported_objects += list(idf.idfobjects.get("ZONEINFILTRATION:FLOWCOEFFICIENT", []))
    unsupported_entries = [
        {
            "name": getattr(o, "Name", ""),
            "zone": None,
            "object_type": getattr(o, "key", ""),
            "status": "gate_unknown_calculation_method",
            "gate": "gate_unknown_calculation_method",
        }
        for o in unsupported_objects
    ]

    if not infiltration_objects:
        return _infiltration_gate_summary(
            enabled, conversion_factor, i75pa_target, "gate_no_infiltration_objects",
            unsupported_entries,
        )

    envelope_area_s = _compute_envelope_area_s(idf)
    if envelope_area_s <= 0.0:
        return _infiltration_gate_summary(
            enabled, conversion_factor, i75pa_target, "gate_no_geometry",
            unsupported_entries, envelope_area_s=envelope_area_s,
        )

    qualifying_zones = []
    seen_zones = set()
    for obj in infiltration_objects:
        zone_name = str(
            getattr(obj, "Zone_or_ZoneList_or_Space_or_SpaceList_Name", "")
        ).strip()
        if zone_name and zone_name not in seen_zones:
            seen_zones.add(zone_name)
            qualifying_zones.append(zone_name)

    aflr = sum(_zone_area_for_kind(idf, z, "floor") or 0.0 for z in qualifying_zones)
    aagw = sum(_zone_area_for_kind(idf, z, "exterior_wall") or 0.0 for z in qualifying_zones)

    i_flr = (conversion_factor * i75pa_target * envelope_area_s / aflr) if aflr > 0.0 else None
    i_agw = (conversion_factor * i75pa_target * envelope_area_s / aagw) if aagw > 0.0 else None
    q_design_total = conversion_factor * i75pa_target * envelope_area_s

    objects = list(unsupported_entries)
    n_tightened = 0
    n_already_compliant = 0
    for obj in infiltration_objects:
        name = getattr(obj, "Name", "")
        zone_name = str(
            getattr(obj, "Zone_or_ZoneList_or_Space_or_SpaceList_Name", "")
        ).strip()
        method_raw = str(getattr(obj, "Design_Flow_Rate_Calculation_Method", "")).strip()
        method = method_raw.lower() if method_raw else "flow/zone"
        coefficients = _infiltration_coefficients(obj)

        if method not in _INFILTRATION_METHOD_FIELDS:
            objects.append(
                {
                    "name": name, "zone": zone_name, "calculation_method": method_raw,
                    "coefficients": list(coefficients), "status": "gate_unknown_calculation_method",
                    "gate": "gate_unknown_calculation_method",
                }
            )
            continue

        if method in _UNSUPPORTED_CALCULATION_METHODS:
            objects.append(
                {
                    "name": name, "zone": zone_name, "calculation_method": method_raw,
                    "coefficients": list(coefficients),
                    "status": "gate_unsupported_calculation_method",
                    "gate": "gate_unsupported_calculation_method",
                }
            )
            continue

        if not _coefficients_match_doe2(coefficients):
            objects.append(
                {
                    "name": name, "zone": zone_name, "calculation_method": method_raw,
                    "coefficients": list(coefficients), "status": "gate_unsupported_coefficients",
                    "gate": "gate_unsupported_coefficients",
                }
            )
            continue

        field_name, area_kind = _INFILTRATION_METHOD_FIELDS[method]
        target_intensity = i_flr if area_kind == "floor" else i_agw
        if target_intensity is None:
            objects.append(
                {
                    "name": name, "zone": zone_name, "calculation_method": method_raw,
                    "coefficients": list(coefficients), "status": "gate_zero_normalizing_area",
                    "gate": "gate_zero_normalizing_area",
                }
            )
            continue

        own_area = _zone_area_for_kind(idf, zone_name, area_kind) or 0.0
        existing_declared = _to_float(getattr(obj, field_name, 0.0))
        new_declared = min(existing_declared, target_intensity)
        entry = {
            "name": name, "zone": zone_name, "calculation_method": method_raw,
            "coefficients": list(coefficients),
            "existing_flow_m3_s": existing_declared * own_area,
            "target_flow_m3_s": target_intensity * own_area,
        }
        if new_declared >= existing_declared - 1e-12:
            entry["status"] = "already_compliant"
            entry["new_flow_m3_s"] = existing_declared * own_area
            n_already_compliant += 1
        else:
            entry["status"] = "tightened"
            entry["new_flow_m3_s"] = new_declared * own_area
            n_tightened += 1
            if enabled:
                setattr(obj, field_name, new_declared)
        objects.append(entry)

    if enabled and n_tightened > 0:
        status = "applied"
    elif not enabled:
        status = "disabled"
    elif n_already_compliant > 0:
        status = "already_compliant"
    else:
        n_gate_unknown = sum(1 for o in objects if o.get("gate") == "gate_unknown_calculation_method")
        n_gate_unsupported_method = sum(
            1 for o in objects if o.get("gate") == "gate_unsupported_calculation_method"
        )
        n_gate_zero = sum(1 for o in objects if o.get("gate") == "gate_zero_normalizing_area")
        n_gate_coef = sum(1 for o in objects if o.get("gate") == "gate_unsupported_coefficients")
        if n_gate_unknown > 0:
            status = "gate_unknown_calculation_method"
        elif n_gate_unsupported_method > 0:
            status = "gate_unsupported_calculation_method"
        elif n_gate_zero > 0:
            status = "gate_zero_normalizing_area"
        elif n_gate_coef > 0:
            status = "gate_unsupported_coefficients"
        else:
            status = "no_applicable_objects"

    return {
        "measure_id": "infiltration_tightening",
        "enabled": enabled,
        "status": status,
        "gate": status if status.startswith("gate_") else None,
        "conversion_factor": conversion_factor,
        "i75pa_target_m3_s_m2": i75pa_target,
        "envelope_area_s_m2": envelope_area_s,
        "floor_area_aflr_m2": aflr,
        "exterior_wall_area_aagw_m2": aagw,
        "q_design_total_m3_s": q_design_total,
        "objects": objects,
        "n_tightened": n_tightened,
        "n_already_compliant": n_already_compliant,
        "n_gate_unknown_calculation_method": sum(
            1 for o in objects if o.get("gate") == "gate_unknown_calculation_method"
        ),
        "n_gate_unsupported_calculation_method": sum(
            1 for o in objects if o.get("gate") == "gate_unsupported_calculation_method"
        ),
        "n_gate_zero_normalizing_area": sum(
            1 for o in objects if o.get("gate") == "gate_zero_normalizing_area"
        ),
        "n_gate_unsupported_coefficients": sum(
            1 for o in objects if o.get("gate") == "gate_unsupported_coefficients"
        ),
    }


def apply_measure(
    idf: Any, measure_id: str, enabled: bool = False, archetype: "str | None" = None
) -> dict:
    table = load_measures()
    if measure_id not in table:
        raise ValueError(f"apply_measure: unknown measure_id {measure_id!r}")
    measure = table[measure_id]
    if measure.get("status") == "withdrawn":
        return {
            "measure_id": measure_id,
            "enabled": enabled,
            "status": "withdrawn",
            "withdrawn_reason": measure.get("withdrawn_reason"),
        }
    if measure_id == "lighting_power_density":
        return _apply_lighting_power_density(idf, measure, enabled, archetype)
    if measure_id == "envelope_u_upgrade":
        return _apply_envelope_u_upgrade(idf, measure, enabled)
    if measure_id == "thermostat_setback":
        return _apply_thermostat_setback(idf, measure, enabled)
    if measure_id == "infiltration_tightening":
        return _apply_infiltration_tightening(idf, measure, enabled)
    raise ValueError(f"apply_measure: no applier registered for {measure_id!r}")
