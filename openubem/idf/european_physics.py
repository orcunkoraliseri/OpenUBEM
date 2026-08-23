"""European envelope physics primitives (D-EU-02).

TABULA supplies aggregate U-values and an areal thermal capacity, not an
arbitrary layered construction.  The campaign therefore represents each
opaque element with a single ``Material:NoMass`` at ``U + delta_u`` and puts
the complete, declared capacity in one ``InternalMass`` object per dwelling.
This module is deliberately small so the same arithmetic can be applied by
the future shoebox and layout builders without patching saved IDFs.
"""
from __future__ import annotations

import math
from typing import Any

EU_INTERNAL_MASS_WH_M2K = 45.0
_MASS_THICKNESS_M = 0.10
_MASS_DENSITY_KG_M3 = 1800.0
_MASS_SPECIFIC_HEAT_J_KGK = 900.0


def effective_u(u_value_w_m2k: float, delta_u_w_m2k: float = 0.0) -> float:
    """Return the D-EU-02 U-value after the TABULA bridge surcharge.

    The surcharge applies to every envelope element before its EnergyPlus
    construction is created.  Negative or zero realised U-values are not
    physically meaningful and are rejected at the adapter boundary.
    """
    realised = float(u_value_w_m2k) + float(delta_u_w_m2k)
    if realised <= 0:
        raise ValueError("u_value_w_m2k + delta_u_w_m2k must be positive")
    return realised


def add_nomass_construction(
    idf: Any,
    name: str,
    u_value_w_m2k: float,
    delta_u_w_m2k: float = 0.0,
) -> str:
    """Add and return a one-layer NoMass construction at ``U + delta_u``."""
    u_value = effective_u(u_value_w_m2k, delta_u_w_m2k)
    material_name = f"{name}_NoMass"
    construction_name = f"{name}_Construction"
    idf.newidfobject(
        "MATERIAL:NOMASS",
        Name=material_name,
        Roughness="MediumRough",
        Thermal_Resistance=1.0 / u_value,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=material_name)
    return construction_name


def add_european_internal_mass(
    idf: Any,
    zone_name: str,
    floor_area_m2: float,
    c_m_wh_m2k: float = EU_INTERNAL_MASS_WH_M2K,
) -> str:
    """Add exactly one internal-mass object with capacity ``c_m * A_floor``.

    The fixed material (0.1 m, 1800 kg/m3, 900 J/kgK) stores exactly
    162,000 J/m2K.  At the campaign value (45 Wh/m2K) its surface area is the
    dwelling floor area; the formula remains exact for an approved sensitivity
    value as well.
    """
    floor_area = float(floor_area_m2)
    c_m = float(c_m_wh_m2k)
    if floor_area <= 0 or c_m <= 0:
        raise ValueError("floor_area_m2 and c_m_wh_m2k must be positive")
    material_name = "EU_InternalMass_Material"
    construction_name = "EU_InternalMass_Construction"
    if not idf.getobject("MATERIAL", material_name):
        idf.newidfobject(
            "MATERIAL",
            Name=material_name,
            Roughness="MediumRough",
            Thickness=_MASS_THICKNESS_M,
            Conductivity=1.0,
            Density=_MASS_DENSITY_KG_M3,
            Specific_Heat=_MASS_SPECIFIC_HEAT_J_KGK,
            Thermal_Absorptance=0.9,
            Solar_Absorptance=0.7,
            Visible_Absorptance=0.7,
        )
        idf.newidfobject("CONSTRUCTION", Name=construction_name, Outside_Layer=material_name)
    capacity_per_area = _MASS_THICKNESS_M * _MASS_DENSITY_KG_M3 * _MASS_SPECIFIC_HEAT_J_KGK
    surface_area = c_m * 3600.0 * floor_area / capacity_per_area
    name = f"{zone_name}_EU_InternalMass"
    idf.newidfobject(
        "INTERNALMASS",
        Name=name,
        Construction_Name=construction_name,
        Zone_or_ZoneList_Name=zone_name,
        Surface_Area=surface_area,
    )
    return name


def internal_mass_capacity_j_k(idf: Any, internal_mass_name: str) -> float:
    """Read the declared InternalMass capacity from an IDF, independently."""
    mass = idf.getobject("INTERNALMASS", internal_mass_name)
    if mass is None:
        raise KeyError(f"InternalMass {internal_mass_name!r} was not found")
    construction = idf.getobject("CONSTRUCTION", mass.Construction_Name)
    if construction is None:
        raise KeyError(f"Construction {mass.Construction_Name!r} was not found")
    material = idf.getobject("MATERIAL", construction.Outside_Layer)
    if material is None:
        raise KeyError(f"Material {construction.Outside_Layer!r} was not found")
    return float(mass.Surface_Area) * float(material.Thickness) * float(material.Density) * float(material.Specific_Heat)


def add_b_factor_other_side_coefficients(idf: Any, name: str, b_factor: float = 0.5) -> str:
    """Add a D-EU-02 temperature-reduction boundary condition.

    TABULA's ``b`` is the fraction of the indoor--outdoor temperature
    difference seen by an element.  The equivalent other-side temperature is
    therefore ``(1-b) * T_zone + b * T_ext``: it gives the required loss
    ``b * U * A * (T_zone - T_ext)``.  The half-boundary R5 fixture remains
    0.5/0.5 and so is deliberately unchanged by this clarification.
    """
    b = float(b_factor)
    if not 0.0 <= b <= 1.0:
        raise ValueError("b_factor must be between zero and one")
    idf.newidfobject(
        "SURFACEPROPERTY:OTHERSIDECOEFFICIENTS",
        Name=name,
        # EnergyPlus's field is spelled ``ConvectiveRadiative`` (without an
        # underscore) in the IDD; use that exact eppy attribute spelling.
        Combined_ConvectiveRadiative_Film_Coefficient=0.0,
        Constant_Temperature=0.0,
        Constant_Temperature_Coefficient=0.0,
        External_DryBulb_Temperature_Coefficient=b,
        Ground_Temperature_Coefficient=0.0,
        Wind_Speed_Coefficient=0.0,
        Zone_Air_Temperature_Coefficient=1.0 - b,
    )
    return name


def r3_time_constant_hours(capacity_j_k: float, heat_loss_w_k: float) -> float:
    """Return the DR11 R3 free-float time constant in hours."""
    capacity = float(capacity_j_k)
    heat_loss = float(heat_loss_w_k)
    if capacity <= 0 or heat_loss <= 0:
        raise ValueError("capacity_j_k and heat_loss_w_k must be positive")
    return capacity / heat_loss / 3600.0


def r3_free_float_temperature_celsius(
    initial_temperature_c: float,
    external_temperature_c: float,
    elapsed_hours: float,
    capacity_j_k: float,
    heat_loss_w_k: float,
) -> float:
    """Analytical DR11 R3 reference for a one-node mass-loss fixture."""
    tau = r3_time_constant_hours(capacity_j_k, heat_loss_w_k)
    return float(external_temperature_c) + (
        float(initial_temperature_c) - float(external_temperature_c)
    ) * math.exp(-float(elapsed_hours) / tau)
