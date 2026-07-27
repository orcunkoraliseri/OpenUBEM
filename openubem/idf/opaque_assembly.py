"""Shared opaque-assembly (roof/wall/floor) material+construction builder
(plan E-LA-20 multilayer-fix, §4-ter/§4-quinquies), used by both defect sites
(`envelope_patcher.patch_envelope()` and `builder.py::assign_constructions()`,
fact F-08) so the CTF-Fatal fix lives in exactly one place.

`thermal_mass=True` assemblies whose target thickness exceeds `T_ENGAGE` are
built as a capped `MATERIAL` mass layer plus a `MATERIAL:NOMASS` residual
carrying the remaining R (candidate (c2), adopted at CP-A-bis 2026-07-25).
Preserving total mass (the retired adaptive-N split, plan §4/§4-bis) was
falsified at fleet scale (F-14): the CTF solver responds to total R*C, which
a mass-preserving split cannot change. Capping and shedding capacity is the
only fix shape that survived (§4-ter).
"""

from typing import Any

_K = 0.12  # W/m*K light structural -- plan §4-ter (unchanged from today)
_RHO = 800.0  # kg/m^3 -- plan §4-ter (unchanged from today)
_CP = 1000.0  # J/kg*K -- plan §4-ter (unchanged from today)

# FROZEN 2026-07-25 at CP-A-bis. F-13: measured uncapped-safe limit, 0 FP / 0
# FN over the 8,160-row T19 fleet harvest. F-20: T_MASS_MAX measured safe at
# the value and the u it ships to (F03-T3), and stable across a +/-0.03 m
# window at the two exposed u values (10/10 pass). Neither constant may be
# re-derived, tuned, or made a function of anything -- see plan §4-quinquies.
T_ENGAGE = 0.868  # m
T_MASS_MAX = 0.35  # m


def build_opaque_assembly(idf: Any, name: str, u_value: float, thermal_mass: bool) -> str:
    """Creates the material object(s) and CONSTRUCTION for one opaque
    assembly (roof, wall or floor), and returns the construction name.

    Args:
        idf: A loaded geomeppy/eppy IDF object, mutated in place.
        name: Assembly/material base name, e.g. "LA_Roof_Assembly" or
            "Roof_Assembly". The construction is named by replacing the
            "_Assembly" suffix with "_Construction" (today's convention).
        u_value: Target U-value (W/m^2K) for the assembly.
        thermal_mass: False -> MATERIAL:NOMASS (today's default, unchanged).
            True -> MATERIAL, capped per §4-quinquies above T_ENGAGE.

    Returns:
        The CONSTRUCTION object's Name.
    """
    construction_name = name.replace("_Assembly", "_Construction")
    r_total = 1.0 / float(u_value)

    if not thermal_mass:
        idf.newidfobject(
            "MATERIAL:NOMASS",
            Name=name,
            Roughness="MediumRough",
            Thermal_Resistance=r_total,
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=name)
        return construction_name

    total_t = max(0.01, r_total * _K)

    if total_t <= T_ENGAGE:
        idf.newidfobject(
            "MATERIAL",
            Name=name,
            Roughness="MediumRough",
            Thickness=total_t,
            Conductivity=_K,
            Density=_RHO,
            Specific_Heat=_CP,
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=name)
        return construction_name

    t_mass = T_MASS_MAX
    r_residual = r_total - t_mass / _K

    if r_residual <= 1e-9:
        # Unreachable given T_MASS_MAX/_K (2.917) < T_ENGAGE/_K (7.233), but a
        # zero-R MATERIAL:NOMASS is an invalid object -- guard against it anyway.
        idf.newidfobject(
            "MATERIAL",
            Name=name,
            Roughness="MediumRough",
            Thickness=t_mass,
            Conductivity=_K,
            Density=_RHO,
            Specific_Heat=_CP,
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=name)
        return construction_name

    name_l2 = f"{name}_L2"
    idf.newidfobject(
        "MATERIAL",
        Name=name,
        Roughness="MediumRough",
        Thickness=t_mass,
        Conductivity=_K,
        Density=_RHO,
        Specific_Heat=_CP,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject(
        "MATERIAL:NOMASS",
        Name=name_l2,
        Roughness="MediumRough",
        Thermal_Resistance=r_residual,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject(
        "CONSTRUCTION",
        Name=construction_name,
        Outside_Layer=name,
        Layer_2=name_l2,
    )
    return construction_name
