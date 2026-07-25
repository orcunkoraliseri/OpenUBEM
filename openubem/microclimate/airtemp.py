"""T16 - air temperature field (PLAN §7 T16).

Deliberately the simplest module in the arc: Ta varies only 0.5-1.5 degC across a summer
neighbourhood while Tmrt varies 20-30 degC (P-05) -- pretending to resolve Ta at Tmrt's spatial
fidelity would be fabricating precision the physics does not support.

- Tier-0 (default): Ta = the EPW dry-bulb, spatially uniform. Justified directly by P-05's
  turbulent-mixing argument (near-surface air temperature over a neighbourhood-scale domain is
  well-mixed compared to the radiative field, which is dominated by line-of-sight geometry).
- Tier-1 (opt-in): adds a bounded offset, capped at P-11's own cited envelope (U06 Table 2 lines
  24-25: "HVAC condenser heat rejection elevates canyon Ta by +1.0...+3.0 degC on hot afternoons
  and up to +2.0 degC at night"), with two additive components:
    1. A canyon-enclosure term, linear in (1 - SVF): fully open (SVF=1) -> 0 offset; fully
       enclosed (SVF=0) -> the full P-11 cap. This is a documented, deliberately simple
       interpolation SHAPE, not an independently cited functional form -- the only numeric
       inputs are the already-computed, already-cited SVF field and P-11's own cited bounds, so
       no new fitted constant enters (rule 9). A real canyon-geometry UHI parameterisation (e.g.
       Oke 1981's H/W-based nocturnal-UHI formula) exists but produces values far outside P-11's
       cited range for realistic urban H/W and would have to be clamped back down to it anyway --
       using the citation's own bounds directly is the more honest choice here.
    2. An HVAC-rejection term, linear in the cell's cooling-energy intensity RELATIVE to the
       run's own maximum (0..1, i.e. the hottest-cooling-load building in this run reaches the
       full P-11 cap). This is a RELATIVE, per-run normalisation, not an absolute physical
       threshold -- documented explicitly as a limitation, because no absolute
       cooling-EUI-to-heat-rejection citation was found in the corpus.
  The two components are summed then clamped to [0, cap] -- the combined offset never exceeds
  P-11's own cited ceiling, regardless of how the two terms individually add (rule 10: never
  tune to pass a gate -- the clamp exists because P-11 IS the cited ceiling, not to force a
  result).
  `daytime` (`altitude_deg > 0`, same convention as mrt.py/§4.6) selects the day cap
  (+3.0 degC, P-11's "hot afternoons" upper bound) vs the night cap (+2.0 degC, P-11's own
  night figure).
"""
from __future__ import annotations

import numpy as np

DAY_HVAC_CANYON_CAP_C = 3.0    # P-11, U06 Table 2 lines 24-25 -- hot-afternoon upper bound
NIGHT_HVAC_CANYON_CAP_C = 2.0  # P-11, same source -- night figure

_TINY = 1e-9


def air_temperature_field_tier0(ta_epw_c, shape):
    """Ta = EPW dry-bulb, spatially uniform. Exact by construction -- the honest Tier-0 default."""
    return np.full(shape, float(ta_epw_c), dtype=np.float64)


def _hvac_canyon_cap(altitude_deg, shape):
    daytime = np.broadcast_to(np.asarray(altitude_deg, dtype=np.float64) > 0.0, shape)
    return np.where(daytime, DAY_HVAC_CANYON_CAP_C, NIGHT_HVAC_CANYON_CAP_C)


def canyon_enclosure_offset(svf, altitude_deg):
    """(1 - SVF) * cap -- see module docstring. svf: raster in [0,1]. Returns a raster of degC."""
    svf = np.asarray(svf, dtype=np.float64)
    cap = _hvac_canyon_cap(altitude_deg, svf.shape)
    return (1.0 - np.clip(svf, 0.0, 1.0)) * cap


def hvac_rejection_offset(cooling_energy_wm2, altitude_deg):
    """Linear in cooling-energy intensity relative to this run's own max (0..1) -- see module
    docstring's documented relative-normalisation caveat. All-zero input -> all-zero offset."""
    cooling = np.asarray(cooling_energy_wm2, dtype=np.float64)
    cap = _hvac_canyon_cap(altitude_deg, cooling.shape)
    peak = float(np.nanmax(cooling)) if cooling.size else 0.0
    if peak <= _TINY:
        return np.zeros_like(cooling)
    relative = np.clip(cooling, 0.0, None) / peak
    return relative * cap


def air_temperature_field_tier1(ta_epw_c, shape, *, svf, altitude_deg, cooling_energy_wm2=None):
    """Tier-1: Ta = Tier-0 + bounded offset. Returns (ta_c, offset_c, flags) where flags is a
    uint8 bitmask, 0x01 = offset was clamped to the P-11 cap.

    offset_c is 0 wherever svf == 1 and cooling_energy_wm2 is None/0 everywhere -- the plan's own
    "How to test" requirement.
    """
    svf = np.asarray(svf, dtype=np.float64)
    canyon = canyon_enclosure_offset(svf, altitude_deg)
    if cooling_energy_wm2 is None:
        hvac = np.zeros_like(canyon)
    else:
        hvac = hvac_rejection_offset(np.broadcast_to(np.asarray(cooling_energy_wm2, dtype=np.float64), svf.shape), altitude_deg)

    cap = _hvac_canyon_cap(altitude_deg, svf.shape)
    raw = canyon + hvac
    offset_c = np.clip(raw, 0.0, cap)
    flags = (raw != offset_c).astype(np.uint8)

    ta0 = air_temperature_field_tier0(ta_epw_c, shape)
    ta_c = ta0 + offset_c
    return ta_c, offset_c, flags


def air_temperature_field(ta_epw_c, shape, *, tier: str = "tier0", svf=None, altitude_deg=None,
                           cooling_energy_wm2=None):
    """Dispatcher. tier: "tier0" (default, uniform EPW dry-bulb) | "tier1" (bounded offset)."""
    if tier == "tier0":
        ta_c = air_temperature_field_tier0(ta_epw_c, shape)
        return ta_c, np.zeros(shape, dtype=np.float64), np.zeros(shape, dtype=np.uint8)
    if tier == "tier1":
        if svf is None or altitude_deg is None:
            raise ValueError("air_temperature_field(tier='tier1') requires svf and altitude_deg")
        return air_temperature_field_tier1(
            ta_epw_c, shape, svf=svf, altitude_deg=altitude_deg, cooling_energy_wm2=cooling_energy_wm2
        )
    raise ValueError(f"air_temperature_field: unknown tier {tier!r}")
