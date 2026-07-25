"""T03 — psychrometrics: saturation & actual vapour pressure (PLAN §7 T03).

All functions return kPa. The hPa conversion needed by the UTCI polynomial happens once,
inside utci.py (PLAN §4.4).
"""
from __future__ import annotations

import numpy as np


def saturation_vapour_pressure_kpa(ta_c):
    """Buck (1981) saturation vapour pressure over water, kPa. Valid -50..+50 degC
    (U02 Table 3 line 36) -- matches the UTCI polynomial's own Ta domain (P-01).

    Buck, A. L. (1981). New equations for computing vapor pressure and enhancement
    factor. J. Applied Meteorology, 20(12), 1527-1532.
    """
    ta = np.asarray(ta_c, dtype=float)
    return 0.61121 * np.exp((18.678 - ta / 234.5) * (ta / (257.14 + ta)))


def vapour_pressure_kpa(ta_c, rh_pct):
    """Actual (partial) water-vapour pressure, kPa, from RH% and Buck e_s."""
    rh = np.asarray(rh_pct, dtype=float)
    return (rh / 100.0) * saturation_vapour_pressure_kpa(ta_c)


def saturation_vapour_pressure_tetens_kpa(ta_c):
    """Tetens (1930) saturation vapour pressure, kPa -- comparison function, tests only.

    U02 Table 3 (lines 35-37): Buck vs Tetens agree within 0.1% over 0-50 degC.
    The official COST-730 routine uses its own Hardy (1998) ITS-90 formulation; the
    known, quantified, accepted deviation from Buck is +-0.05-0.15 degC UTCI at
    Ta > 35 degC (U05 §4.3 line 249).
    """
    ta = np.asarray(ta_c, dtype=float)
    return 0.61078 * np.exp(17.27 * ta / (ta + 237.3))
