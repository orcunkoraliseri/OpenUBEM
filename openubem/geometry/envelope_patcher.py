"""Cross-CZ envelope patching for `layout_assign` baselines (plan T16, un-defers T11).

Every `layout_assign` baseline prototype IDF ships with its own native Buffalo
CZ 6A envelope, regardless of the real building's actual simulated climate.
`patch_envelope()` overwrites the baseline's opaque/glazing material properties
in place with the real building's own already-resolved envelope values
(`row["u_wall_w_m2k"]`, `u_roof_w_m2k`, `u_floor_w_m2k`, `u_window_w_m2k`,
`shgc_window`) — computed by `openubem.semantic.construction_sets.get_construction_set()`
during Step-2 semantic enrichment, keyed on (archetype_id, real climate_zone),
identical for every resolution_mode (runs before Step-3/resolution_mode
branching) — so these columns are already correct and present on a
`layout_assign` row today; they were simply never applied to the baseline IDF.

Deliberately duplicates the material-creation snippet from
`builder.py::assign_constructions()` (fact #20) under new, uniquely-named
("LA_"-prefixed) constructions rather than calling/refactoring that CP-signed
method: `assign_constructions()` calls `idf.set_wwr()`, which regenerates
fenestration geometry and would destroy the baseline's validated, pre-built
window layout. `patch_envelope()` only reassigns `Construction_Name` on the
baseline's EXISTING surfaces/fenestration — it never calls `set_wwr()` and
never touches surface geometry or vertex counts.
"""

import math
from typing import Any

from openubem.idf.opaque_assembly import build_opaque_assembly

logger_name = "openubem.geometry.envelope_patcher"

# Field-name note (mirrors T04's precedent): the plan's prose names the
# FenestrationSurface:Detailed construction field as
# "Construction_or_Window_Construction_Name"; the real field in this
# project's locked EnergyPlus 23.1 IDD (config.ENERGYPLUS_IDD_PATH) is
# "Construction_Name" for both BuildingSurface:Detailed and
# FenestrationSurface:Detailed -- confirmed via eppy fieldnames introspection
# and cross-checked against builder.py's own existing
# test_wwr_window_construction_name assertions (tests/test_idf_builder.py).

_ENVELOPE_COLS = ("u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k", "shgc_window")

# Mirrors builder.py's _SURFACE_CONSTRUCTION_MAP (assign_constructions()) exactly,
# retargeted at the new LA-specific construction names.
_LA_SURFACE_CONSTRUCTION_MAP = {
    "wall": "LA_Wall_Construction",
    "roof": "LA_Roof_Construction",
    "floor": "LA_Floor_Construction",
    "ceiling": "LA_Floor_Construction",
}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(math.isnan(float(value)))
    except (TypeError, ValueError):
        return False


def _native_window_u_shgc(idf: Any, fen: Any) -> tuple[float, float] | None:
    """Resolves a FenestrationSurface:Detailed's own (pre-patch) construction to a
    (UFactor, SHGC) pair, returning None if it cannot be resolved (e.g. detailed
    glazing layers instead of WindowMaterial:SimpleGlazingSystem, per B01)."""
    cons_name = str(getattr(fen, "Construction_Name", "")).strip().lower()
    if not cons_name:
        return None
    cons = next(
        (c for c in idf.idfobjects.get("CONSTRUCTION", []) if str(c.Name).strip().lower() == cons_name),
        None,
    )
    if cons is None:
        return None
    layer_name = str(getattr(cons, "Outside_Layer", "")).strip().lower()
    mat = next(
        (
            m
            for m in idf.idfobjects.get("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", [])
            if str(m.Name).strip().lower() == layer_name
        ),
        None,
    )
    if mat is None:
        return None
    try:
        return float(mat.UFactor), float(mat.Solar_Heat_Gain_Coefficient)
    except (TypeError, ValueError):
        return None


def _check_shading_controls(idf: Any) -> None:
    """B02 found zero WindowShadingControl objects in the current prototype
    library, so this is a guard against a future addition, not a repair for an
    existing case. Raises if a shading control references a construction that
    does not exist, or controls a fenestration surface that patch_envelope has
    repointed to LA_Window_Construction (the control's Construction_with_Shading_Name
    was built against the surface's original construction and no longer applies)."""
    construction_names = {
        str(getattr(c, "Name", "")).strip().lower() for c in idf.idfobjects.get("CONSTRUCTION", [])
    }
    fen_by_name = {
        str(getattr(f, "Name", "")).strip().lower(): f
        for f in idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", [])
    }
    for shc in idf.idfobjects.get("WINDOWSHADINGCONTROL", []):
        shc_name = getattr(shc, "Name", "?")
        shading_construction = str(getattr(shc, "Construction_with_Shading_Name", "")).strip()
        if shading_construction and shading_construction.lower() not in construction_names:
            raise ValueError(
                f"patch_envelope: WindowShadingControl {shc_name!r} references "
                f"Construction_with_Shading_Name={shading_construction!r}, which does not exist "
                "in this IDF -- orphaned shading control."
            )
        for field_name in getattr(shc, "fieldnames", []):
            if not field_name.lower().startswith("fenestration_surface_"):
                continue
            fen_name = str(getattr(shc, field_name, "")).strip()
            if not fen_name:
                continue
            fen = fen_by_name.get(fen_name.lower())
            if fen is None:
                continue
            if str(getattr(fen, "Construction_Name", "")).strip() == "LA_Window_Construction":
                raise ValueError(
                    f"patch_envelope: WindowShadingControl {shc_name!r} controls fenestration "
                    f"surface {fen_name!r}, which patch_envelope repointed to "
                    "'LA_Window_Construction' -- its Construction_with_Shading_Name="
                    f"{shading_construction!r} no longer matches this window after patching."
                )


def patch_envelope(idf: Any, row: Any, thermal_mass: bool = False, skip_when_better: bool = False) -> Any:
    """Patches a `layout_assign` baseline IDF's envelope material properties in
    place to `row`'s already-resolved (archetype_id, climate_zone) envelope
    values. Never touches surface/fenestration geometry, vertex counts, or WWR
    (no `idf.set_wwr()` call) -- only `Construction_Name` reassignment on the
    baseline's own existing surfaces.

    Args:
        idf: A loaded (post scale_baseline_idf) geomeppy/eppy IDF object, mutated in place.
        row: Row (pd.Series or dict-like) carrying u_wall_w_m2k/u_roof_w_m2k/
            u_floor_w_m2k/u_window_w_m2k/shgc_window (Step-2 semantic enrichment
            output, present regardless of resolution_mode).
        thermal_mass: Mirrors BuildingIDF.thermal_mass -- MATERIAL (mass) vs.
            MATERIAL:NOMASS (default) for the opaque assemblies.
        skip_when_better: Default False (byte-identical to today's unconditional
            overwrite). When True, a fenestration surface whose own native window
            is already better than the archetype window on BOTH UFactor and SHGC
            (strictly lower on both) is left on its native construction instead
            of being repointed to LA_Window_Construction (B01/D8).

    Returns:
        The same idf object, for chaining.

    Raises:
        ValueError: if any required envelope column is null/missing on `row`
            (never silently defaulted -- plan's own explicit instruction).
    """
    for col in _ENVELOPE_COLS:
        val = row[col] if col in row else None
        if _is_missing(val):
            raise ValueError(
                f"patch_envelope: row[{col!r}] is null/missing for "
                f"archetype_id={row.get('archetype_id') if hasattr(row, 'get') else row['archetype_id']!r} "
                "-- layout_assign envelope patching requires Step-2 semantic "
                "enrichment's construction_sets.get_construction_set() output; refusing to silently default."
            )

    for name, u_col in [
        ("LA_Roof_Assembly", "u_roof_w_m2k"),
        ("LA_Wall_Assembly", "u_wall_w_m2k"),
        ("LA_Floor_Assembly", "u_floor_w_m2k"),
    ]:
        build_opaque_assembly(idf, name, float(row[u_col]), thermal_mass)

    new_window_ufactor = float(row["u_window_w_m2k"])
    new_window_shgc = float(row["shgc_window"])
    idf.newidfobject(
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
        Name="LA_Window_Material",
        UFactor=new_window_ufactor,
        Solar_Heat_Gain_Coefficient=new_window_shgc,
        Visible_Transmittance=0.6,
    )
    idf.newidfobject(
        "CONSTRUCTION",
        Name="LA_Window_Construction",
        Outside_Layer="LA_Window_Material",
    )

    # Opaque surfaces: idf.getsurfaces() covers every IDD SurfaceNames-group
    # class present in these baselines (BuildingSurface:Detailed and any
    # compact wall/roof/floor/ceiling forms) -- same method assign_constructions()
    # uses, matched on Surface_Type exactly as _SURFACE_CONSTRUCTION_MAP does.
    #
    # Ambiguity resolved conservatively (autonomous-overnight call, plan §1a --
    # see T16 progress log for full rationale): surfaces whose
    # Outside_Boundary_Condition is "GroundFCfactorMethod" (basement/slab-on-grade
    # surfaces modeled via Construction:FfactorGroundFloor / Construction:
    # CfactorUndergroundWall, found in Hospital/LargeHotel/LargeOffice/TallBuilding/
    # SuperTallBuilding et al.) are skipped entirely and left on their native
    # baseline construction. That modeling method encodes exposed-perimeter/area
    # in a per-surface F/C-factor, not a simple layered U-value -- it is not
    # algebraically derivable from row["u_floor_w_m2k"]/["u_wall_w_m2k"] alone,
    # and reassigning a plain Construction onto one is an EnergyPlus Fatal
    # ("invalid Outside Boundary Condition ... is not type
    # Construction:FfactorGroundFloor") confirmed via a real local build+simulate
    # (see T16 progress log). Out of scope for this task; not guess-fixed.
    for surf in idf.getsurfaces():
        stype = surf.Surface_Type.lower()
        construction = _LA_SURFACE_CONSTRUCTION_MAP.get(stype)
        if construction is None:
            continue
        obc = str(getattr(surf, "Outside_Boundary_Condition", "")).strip().lower()
        if obc == "groundfcfactormethod":
            continue
        surf.Construction_Name = construction

    # Fenestration: reassigned separately (FenestrationSurface:Detailed is not
    # in the SurfaceNames IDD group, so idf.getsurfaces() never returns it) --
    # never regenerated, only re-pointed to the new LA-specific window construction.
    #
    # Ambiguity resolved conservatively: only Surface_Type in {"Window", "GlassDoor"}
    # (both glazed, both confirmed in the real baseline library to already reference
    # glazing-material constructions, e.g. SmallOffice/RetailStripmall's GlassDoor
    # objects use "Window_U_..._SHGC_..." constructions) are repointed to the new
    # LA_Window_Construction. Surface_Type=="Door" (opaque door leaf, confirmed
    # present in the real baseline library) is left untouched -- EnergyPlus fatals
    # if an opaque Door fenestration is given a WindowMaterial:SimpleGlazingSystem-
    # based construction ("has Window materials ... because Surface Type=DOOR",
    # confirmed via a real local build+simulate, see T16 progress log). No
    # corresponding row column exists for door U-value (plan's 5 envelope columns
    # are wall/roof/floor/window/shgc only) -- out of scope, not guess-fixed.
    for fen in idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", []):
        if str(fen.Surface_Type).strip().lower() not in ("window", "glassdoor"):
            continue
        if skip_when_better:
            native = _native_window_u_shgc(idf, fen)
            if native is not None and native[0] < new_window_ufactor and native[1] < new_window_shgc:
                continue
        fen.Construction_Name = "LA_Window_Construction"

    _check_shading_controls(idf)

    return idf
