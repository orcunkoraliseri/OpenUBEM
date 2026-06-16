"""
r6_4_basis_overlay.py — reporting-level COP/fuel basis-conversion overlay.

Pure-function module: no I/O, no globals, no side effects.
Constants from MEMO_phaseB_cbecs_diagnosis.md lines 55-59 / F-5.
"""

COOLING_COP = 3.5
HEATING_FUEL_FACTOR = 1.19


def apply_basis(
    cooling_thermal: float,
    heating_thermal: float,
    lighting: float,
    equipment: float,
    other: float,
    cop: float = COOLING_COP,
    fuel_factor: float = HEATING_FUEL_FACTOR,
) -> dict:
    """Convert thermal end-use EUIs to a delivered-energy basis.

    Cooling thermal ÷ cop; heating thermal × fuel_factor; lighting / equipment / other unchanged.
    Returns a dict with corrected values and corrected total.
    """
    cool_corr = cooling_thermal / cop
    heat_corr = heating_thermal * fuel_factor
    total_corr = heat_corr + cool_corr + lighting + equipment + other
    return {
        "heating_corr": heat_corr,
        "cooling_corr": cool_corr,
        "lighting_corr": lighting,
        "equipment_corr": equipment,
        "other_corr": other,
        "total_corr": total_corr,
    }
