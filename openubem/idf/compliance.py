"""Pre-simulation envelope compliance audit for `patch_envelope()` output
(TechTransfer block 3, T4, Lane G, decisions G1-G5).

Reads an already-patched `layout_assign` IDF and reports whether
`openubem.geometry.envelope_patcher.patch_envelope()` actually landed what it
claims to have written. Never mutates the IDF, never writes a file, and
checks only against the patcher's own surface-type map, boundary-condition
rule and construction names -- nothing borrowed from an external code
baseline.
"""

from typing import Any

from openubem.geometry.envelope_patcher import _LA_SURFACE_CONSTRUCTION_MAP
from openubem.idf.european_physics import effective_u

_ASSEMBLY_ROW_COLS = {
    "LA_Wall_Construction": "u_wall_w_m2k",
    "LA_Roof_Construction": "u_roof_w_m2k",
    "LA_Floor_Construction": "u_floor_w_m2k",
}

_U_TOLERANCE_W_M2K = 0.01
_WINDOW_TOLERANCE = 0.01
_MAX_EXAMPLES = 5


def _get_named(idf: Any, idf_class: str, name: str) -> Any:
    lname = name.strip().lower()
    return next(
        (o for o in idf.idfobjects.get(idf_class, []) if str(getattr(o, "Name", "")).strip().lower() == lname),
        None,
    )


def _material_r_value(idf: Any, name: str) -> float | None:
    mat = _get_named(idf, "MATERIAL:NOMASS", name)
    if mat is not None:
        return float(mat.Thermal_Resistance)
    mat = _get_named(idf, "MATERIAL", name)
    if mat is not None:
        return float(mat.Thickness) / float(mat.Conductivity)
    return None


def _construction_effective_u(idf: Any, construction_name: str) -> float | None:
    cons = _get_named(idf, "CONSTRUCTION", construction_name)
    if cons is None:
        return None
    r_total = 0.0
    for field in getattr(cons, "fieldnames", []):
        field_lower = field.lower()
        if field_lower != "outside_layer" and not field_lower.startswith("layer_"):
            continue
        layer_name = str(getattr(cons, field, "")).strip()
        if not layer_name:
            continue
        r_value = _material_r_value(idf, layer_name)
        if r_value is None:
            return None
        r_total += r_value
    if r_total <= 0:
        return None
    return effective_u(1.0 / r_total, 0.0)


def audit_envelope_compliance(idf: Any, row: Any, skip_when_better: bool = False) -> dict:
    failures: list[dict] = []
    info: dict = {}

    incomplete_examples: list[str] = []
    incomplete_count = 0
    for surf in idf.getsurfaces():
        stype = str(surf.Surface_Type).strip().lower()
        expected_construction = _LA_SURFACE_CONSTRUCTION_MAP.get(stype)
        if expected_construction is None:
            continue
        obc = str(getattr(surf, "Outside_Boundary_Condition", "")).strip().lower()
        if obc == "groundfcfactormethod":
            continue
        if str(surf.Construction_Name).strip() != expected_construction:
            incomplete_count += 1
            if len(incomplete_examples) < _MAX_EXAMPLES:
                incomplete_examples.append(str(surf.Name))
    if incomplete_count:
        failures.append({
            "reason": "ENVELOPE_PATCH_INCOMPLETE",
            "count": incomplete_count,
            "examples": incomplete_examples,
        })

    u_mismatch_examples: list[str] = []
    u_mismatch_count = 0
    for construction_name, row_col in _ASSEMBLY_ROW_COLS.items():
        wanted = float(row[row_col])
        found = _construction_effective_u(idf, construction_name)
        if found is None or abs(found - wanted) > _U_TOLERANCE_W_M2K:
            u_mismatch_count += 1
            found_str = "unresolved" if found is None else f"{found:.4f}"
            if len(u_mismatch_examples) < _MAX_EXAMPLES:
                u_mismatch_examples.append(f"{construction_name}: wanted={wanted:.4f} found={found_str}")
    if u_mismatch_count:
        failures.append({
            "reason": "ENVELOPE_U_MISMATCH",
            "count": u_mismatch_count,
            "examples": u_mismatch_examples,
        })

    window_material = _get_named(idf, "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", "LA_Window_Material")
    if window_material is not None:
        wanted_u = float(row["u_window_w_m2k"])
        wanted_shgc = float(row["shgc_window"])
        found_u = float(window_material.UFactor)
        found_shgc = float(window_material.Solar_Heat_Gain_Coefficient)
        if abs(found_u - wanted_u) > _WINDOW_TOLERANCE or abs(found_shgc - wanted_shgc) > _WINDOW_TOLERANCE:
            failures.append({
                "reason": "WINDOW_PROPERTY_MISMATCH",
                "count": 1,
                "examples": [
                    f"LA_Window_Material: UFactor wanted={wanted_u:.4f} found={found_u:.4f}, "
                    f"SHGC wanted={wanted_shgc:.4f} found={found_shgc:.4f}"
                ],
            })

    unpatched_count = 0
    unpatched_examples: list[str] = []
    for fen in idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", []):
        if str(fen.Surface_Type).strip().lower() not in ("window", "glassdoor"):
            continue
        if str(fen.Construction_Name).strip() != "LA_Window_Construction":
            unpatched_count += 1
            if len(unpatched_examples) < _MAX_EXAMPLES:
                unpatched_examples.append(str(fen.Name))
    info["GLAZING_UNPATCHED"] = {
        "count": unpatched_count,
        "skip_when_better": skip_when_better,
        "examples": unpatched_examples,
    }
    if unpatched_count and not skip_when_better:
        failures.append({
            "reason": "GLAZING_UNPATCHED",
            "count": unpatched_count,
            "examples": unpatched_examples,
        })

    ground_count = 0
    ground_examples: list[str] = []
    for surf in idf.getsurfaces():
        stype = str(surf.Surface_Type).strip().lower()
        if stype not in _LA_SURFACE_CONSTRUCTION_MAP:
            continue
        obc = str(getattr(surf, "Outside_Boundary_Condition", "")).strip().lower()
        if obc == "groundfcfactormethod":
            ground_count += 1
            if len(ground_examples) < _MAX_EXAMPLES:
                ground_examples.append(str(surf.Name))
    info["GROUND_SURFACE_UNPATCHED"] = {"count": ground_count, "examples": ground_examples}

    status = "fail" if failures else "pass"
    return {"status": status, "failures": failures, "info": info}
