"""T05/T07 - Bröde 210-coefficient operational UTCI polynomial (PLAN §7 T05/T06/T07).

⚠️ §4.1: the polynomial in the U01-U06 research corpus is FABRICATED (7 hand-written terms).
This module transcribes the OFFICIAL COST Action 730 reference implementation instead.

Provenance (Q-01 escalation ladder, rung 1 - the canonical source, reached successfully):
  File:      UTCI_a002.f90, function UTCI_approx(Ta, ehPa, Tmrt, va)
  Author:    Peter Bröde, Version a 0.002, October 2009
  Source:    https://www.utci.org/ -> "resources/UTCI Program Code.zip"
             (https://www.utci.org/resources/UTCI%20Program%20Code.zip)
  Retrieved: 2026-07-23
  Licence:   "released for public use after termination of COST Action 730" (no further
             restriction stated in ReadMe_UTCI_a002.txt; distributed "in the hope that it
             will be useful, WITHOUT ANY WARRANTY").
  All 210 coefficients below were read directly from that .f90 file (not from memory, not
  from the research corpus) and are transcribed digit-for-digit in the file's own term order.
  Cross-checked (T06) against an independent second transcription -- pythermalcomfort
  (https://github.com/pythermalcomfort/pythermalcomfort, MIT licence,
  pythermalcomfort/models/utci.py, retrieved 2026-07-23) -- and against a live execution of
  the official compiled UTCI_a002.exe for a handful of points (see CP-1 report).

§4.2 (binding wind convention): va here is the polynomial's own 10 m wind argument
(0.5-17.0 m/s), NOT the 1.1 m pedestrian field. wind.py computes v_1.1 for display/export
and converts back with va10_eq = v_1.1 / 0.680 before calling this module.

§4.4 (binding vapour-pressure convention): this module's public API takes e in kPa
(matching psychro.py / T03). The official Fortran signature is UTCI_approx(Ta, ehPa, Tmrt,
va) with ehPa in hPa (confirmed directly from source: ReadMe states "water vapour pressure
in hPa (below 50 hPa or 100% relative humidity)"); internally the Fortran itself does
`PA = ehPa/10.0  ! use vapour pressure in kPa` before the arithmetic. We mirror that exact
two-step chain (kPa -> hPa at the public boundary, then hPa -> kPa again just before the
210-term sum, exactly where the official routine does it) so the conversion point is single,
explicit, and testable -- see test_microclimate_utci.py::test_kpa_to_hpa_conversion_pinned.
"""
from __future__ import annotations

import numpy as np

FLAG_TA = np.uint8(0x01)
FLAG_TMRT = np.uint8(0x02)
FLAG_WIND = np.uint8(0x04)
FLAG_VAPOUR = np.uint8(0x08)

TA_BOUNDS = (-50.0, 50.0)
D_TMRT_BOUNDS = (-30.0, 70.0)
VA10_BOUNDS = (0.5, 17.0)
E_KPA_BOUNDS = (0.0, 5.0)


def _brode_polynomial_offset(ta, va, d_tmrt, eh_pa):
    """The official 210-term sum (excludes the leading '+Ta', per P-03). Args already clamped."""
    pa = eh_pa / 10.0  # official: PA = ehPa/10.0  "use vapour pressure in kPa"

    ta2 = ta * ta
    ta3 = ta2 * ta
    ta4 = ta3 * ta
    ta5 = ta4 * ta
    va2 = va * va
    va3 = va2 * va
    va4 = va3 * va
    va5 = va4 * va
    va6 = va5 * va
    d2 = d_tmrt * d_tmrt
    d3 = d2 * d_tmrt
    d4 = d3 * d_tmrt
    d5 = d4 * d_tmrt
    d6 = d5 * d_tmrt
    pa2 = pa * pa
    pa3 = pa2 * pa
    pa4 = pa3 * pa
    pa5 = pa4 * pa
    pa6 = pa5 * pa

    result = (
        6.07562052e-01
        + (-2.27712343e-02) * ta
        + 8.06470249e-04 * ta2
        + (-1.54271372e-04) * ta3
        + (-3.24651735e-06) * ta4
        + 7.32602852e-08 * ta5
        + 1.35959073e-09 * ta5 * ta
        + (-2.25836520e+00) * va
        + 8.80326035e-02 * ta * va
        + 2.16844454e-03 * ta2 * va
        + (-1.53347087e-05) * ta3 * va
        + (-5.72983704e-07) * ta4 * va
        + (-2.55090145e-09) * ta5 * va
        + (-7.51269505e-01) * va2
        + (-4.08350271e-03) * ta * va2
        + (-5.21670675e-05) * ta2 * va2
        + 1.94544667e-06 * ta3 * va2
        + 1.14099531e-08 * ta4 * va2
        + 1.58137256e-01 * va3
        + (-6.57263143e-05) * ta * va3
        + 2.22697524e-07 * ta2 * va3
        + (-4.16117031e-08) * ta3 * va3
        + (-1.27762753e-02) * va4
        + 9.66891875e-06 * ta * va4
        + 2.52785852e-09 * ta2 * va4
        + 4.56306672e-04 * va5
        + (-1.74202546e-07) * ta * va5
        + (-5.91491269e-06) * va6
        + 3.98374029e-01 * d_tmrt
        + 1.83945314e-04 * ta * d_tmrt
        + (-1.73754510e-04) * ta2 * d_tmrt
        + (-7.60781159e-07) * ta3 * d_tmrt
        + 3.77830287e-08 * ta4 * d_tmrt
        + 5.43079673e-10 * ta5 * d_tmrt
        + (-2.00518269e-02) * va * d_tmrt
        + 8.92859837e-04 * ta * va * d_tmrt
        + 3.45433048e-06 * ta2 * va * d_tmrt
        + (-3.77925774e-07) * ta3 * va * d_tmrt
        + (-1.69699377e-09) * ta4 * va * d_tmrt
        + 1.69992415e-04 * va2 * d_tmrt
        + (-4.99204314e-05) * ta * va2 * d_tmrt
        + 2.47417178e-07 * ta2 * va2 * d_tmrt
        + 1.07596466e-08 * ta3 * va2 * d_tmrt
        + 8.49242932e-05 * va3 * d_tmrt
        + 1.35191328e-06 * ta * va3 * d_tmrt
        + (-6.21531254e-09) * ta2 * va3 * d_tmrt
        + (-4.99410301e-06) * va4 * d_tmrt
        + (-1.89489258e-08) * ta * va4 * d_tmrt
        + 8.15300114e-08 * va5 * d_tmrt
        + 7.55043090e-04 * d2
        + (-5.65095215e-05) * ta * d2
        + (-4.52166564e-07) * ta2 * d2
        + 2.46688878e-08 * ta3 * d2
        + 2.42674348e-10 * ta4 * d2
        + 1.54547250e-04 * va * d2
        + 5.24110970e-06 * ta * va * d2
        + (-8.75874982e-08) * ta2 * va * d2
        + (-1.50743064e-09) * ta3 * va * d2
        + (-1.56236307e-05) * va2 * d2
        + (-1.33895614e-07) * ta * va2 * d2
        + 2.49709824e-09 * ta2 * va2 * d2
        + 6.51711721e-07 * va3 * d2
        + 1.94960053e-09 * ta * va3 * d2
        + (-1.00361113e-08) * va4 * d2
        + (-1.21206673e-05) * d3
        + (-2.18203660e-07) * ta * d3
        + 7.51269482e-09 * ta2 * d3
        + 9.79063848e-11 * ta3 * d3
        + 1.25006734e-06 * va * d3
        + (-1.81584736e-09) * ta * va * d3
        + (-3.52197671e-10) * ta2 * va * d3
        + (-3.36514630e-08) * va2 * d3
        + 1.35908359e-10 * ta * va2 * d3
        + 4.17032620e-10 * va3 * d3
        + (-1.30369025e-09) * d4
        + 4.13908461e-10 * ta * d4
        + 9.22652254e-12 * ta2 * d4
        + (-5.08220384e-09) * va * d4
        + (-2.24730961e-11) * ta * va * d4
        + 1.17139133e-10 * va2 * d4
        + 6.62154879e-10 * d5
        + 4.03863260e-13 * ta * d5
        + 1.95087203e-12 * va * d5
        + (-4.73602469e-12) * d6
        + 5.12733497e+00 * pa
        + (-3.12788561e-01) * ta * pa
        + (-1.96701861e-02) * ta2 * pa
        + 9.99690870e-04 * ta3 * pa
        + 9.51738512e-06 * ta4 * pa
        + (-4.66426341e-07) * ta5 * pa
        + 5.48050612e-01 * va * pa
        + (-3.30552823e-03) * ta * va * pa
        + (-1.64119440e-03) * ta2 * va * pa
        + (-5.16670694e-06) * ta3 * va * pa
        + 9.52692432e-07 * ta4 * va * pa
        + (-4.29223622e-02) * va2 * pa
        + 5.00845667e-03 * ta * va2 * pa
        + 1.00601257e-06 * ta2 * va2 * pa
        + (-1.81748644e-06) * ta3 * va2 * pa
        + (-1.25813502e-03) * va3 * pa
        + (-1.79330391e-04) * ta * va3 * pa
        + 2.34994441e-06 * ta2 * va3 * pa
        + 1.29735808e-04 * va4 * pa
        + 1.29064870e-06 * ta * va4 * pa
        + (-2.28558686e-06) * va5 * pa
        + (-3.69476348e-02) * d_tmrt * pa
        + 1.62325322e-03 * ta * d_tmrt * pa
        + (-3.14279680e-05) * ta2 * d_tmrt * pa
        + 2.59835559e-06 * ta3 * d_tmrt * pa
        + (-4.77136523e-08) * ta4 * d_tmrt * pa
        + 8.64203390e-03 * va * d_tmrt * pa
        + (-6.87405181e-04) * ta * va * d_tmrt * pa
        + (-9.13863872e-06) * ta2 * va * d_tmrt * pa
        + 5.15916806e-07 * ta3 * va * d_tmrt * pa
        + (-3.59217476e-05) * va2 * d_tmrt * pa
        + 3.28696511e-05 * ta * va2 * d_tmrt * pa
        + (-7.10542454e-07) * ta2 * va2 * d_tmrt * pa
        + (-1.24382300e-05) * va3 * d_tmrt * pa
        + (-7.38584400e-09) * ta * va3 * d_tmrt * pa
        + 2.20609296e-07 * va4 * d_tmrt * pa
        + (-7.32469180e-04) * d2 * pa
        + (-1.87381964e-05) * ta * d2 * pa
        + 4.80925239e-06 * ta2 * d2 * pa
        + (-8.75492040e-08) * ta3 * d2 * pa
        + 2.77862930e-05 * va * d2 * pa
        + (-5.06004592e-06) * ta * va * d2 * pa
        + 1.14325367e-07 * ta2 * va * d2 * pa
        + 2.53016723e-06 * va2 * d2 * pa
        + (-1.72857035e-08) * ta * va2 * d2 * pa
        + (-3.95079398e-08) * va3 * d2 * pa
        + (-3.59413173e-07) * d3 * pa
        + 7.04388046e-07 * ta * d3 * pa
        + (-1.89309167e-08) * ta2 * d3 * pa
        + (-4.79768731e-07) * va * d3 * pa
        + 7.96079978e-09 * ta * va * d3 * pa
        + 1.62897058e-09 * va2 * d3 * pa
        + 3.94367674e-08 * d4 * pa
        + (-1.18566247e-09) * ta * d4 * pa
        + 3.34678041e-10 * va * d4 * pa
        + (-1.15606447e-10) * d5 * pa
        + (-2.80626406e+00) * pa2
        + 5.48712484e-01 * ta * pa2
        + (-3.99428410e-03) * ta2 * pa2
        + (-9.54009191e-04) * ta3 * pa2
        + 1.93090978e-05 * ta4 * pa2
        + (-3.08806365e-01) * va * pa2
        + 1.16952364e-02 * ta * va * pa2
        + 4.95271903e-04 * ta2 * va * pa2
        + (-1.90710882e-05) * ta3 * va * pa2
        + 2.10787756e-03 * va2 * pa2
        + (-6.98445738e-04) * ta * va2 * pa2
        + 2.30109073e-05 * ta2 * va2 * pa2
        + 4.17856590e-04 * va3 * pa2
        + (-1.27043871e-05) * ta * va3 * pa2
        + (-3.04620472e-06) * va4 * pa2
        + 5.14507424e-02 * d_tmrt * pa2
        + (-4.32510997e-03) * ta * d_tmrt * pa2
        + 8.99281156e-05 * ta2 * d_tmrt * pa2
        + (-7.14663943e-07) * ta3 * d_tmrt * pa2
        + (-2.66016305e-04) * va * d_tmrt * pa2
        + 2.63789586e-04 * ta * va * d_tmrt * pa2
        + (-7.01199003e-06) * ta2 * va * d_tmrt * pa2
        + (-1.06823306e-04) * va2 * d_tmrt * pa2
        + 3.61341136e-06 * ta * va2 * d_tmrt * pa2
        + 2.29748967e-07 * va3 * d_tmrt * pa2
        + 3.04788893e-04 * d2 * pa2
        + (-6.42070836e-05) * ta * d2 * pa2
        + 1.16257971e-06 * ta2 * d2 * pa2
        + 7.68023384e-06 * va * d2 * pa2
        + (-5.47446896e-07) * ta * va * d2 * pa2
        + (-3.59937910e-08) * va2 * d2 * pa2
        + (-4.36497725e-06) * d3 * pa2
        + 1.68737969e-07 * ta * d3 * pa2
        + 2.67489271e-08 * va * d3 * pa2
        + 3.23926897e-09 * d4 * pa2
        + (-3.53874123e-02) * pa3
        + (-2.21201190e-01) * ta * pa3
        + 1.55126038e-02 * ta2 * pa3
        + (-2.63917279e-04) * ta3 * pa3
        + 4.53433455e-02 * va * pa3
        + (-4.32943862e-03) * ta * va * pa3
        + 1.45389826e-04 * ta2 * va * pa3
        + 2.17508610e-04 * va2 * pa3
        + (-6.66724702e-05) * ta * va2 * pa3
        + 3.33217140e-05 * va3 * pa3
        + (-2.26921615e-03) * d_tmrt * pa3
        + 3.80261982e-04 * ta * d_tmrt * pa3
        + (-5.45314314e-09) * ta2 * d_tmrt * pa3
        + (-7.96355448e-04) * va * d_tmrt * pa3
        + 2.53458034e-05 * ta * va * d_tmrt * pa3
        + (-6.31223658e-06) * va2 * d_tmrt * pa3
        + 3.02122035e-04 * d2 * pa3
        + (-4.77403547e-06) * ta * d2 * pa3
        + 1.73825715e-06 * va * d2 * pa3
        + (-4.09087898e-07) * d3 * pa3
        + 6.14155345e-01 * pa4
        + (-6.16755931e-02) * ta * pa4
        + 1.33374846e-03 * ta2 * pa4
        + 3.55375387e-03 * va * pa4
        + (-5.13027851e-04) * ta * va * pa4
        + 1.02449757e-04 * va2 * pa4
        + (-1.48526421e-03) * d_tmrt * pa4
        + (-4.11469183e-05) * ta * d_tmrt * pa4
        + (-6.80434415e-06) * va * d_tmrt * pa4
        + (-9.77675906e-06) * d2 * pa4
        + 8.82773108e-02 * pa5
        + (-3.01859306e-03) * ta * pa5
        + 1.04452989e-03 * va * pa5
        + 2.47090539e-04 * d_tmrt * pa5
        + 1.48348065e-03 * pa6
    )
    return result


def utci_approx(ta_c, tmrt_c, va10_ms, e_kpa):
    """Bröde operational UTCI, fully vectorised. Returns (utci_c, flags).

    va10_ms is the polynomial's own 10 m wind argument (§4.2) -- NOT 1.1 m pedestrian wind.
    e_kpa is vapour pressure in kPa (§4.4); converted to hPa once, at this boundary.
    flags is a uint8 bitmask: 0x01 Ta out of [-50,50]; 0x02 (Tmrt-Ta) out of [-30,70];
    0x04 va10 out of [0.5,17.0]; 0x08 e out of [0,5] kPa. 0x00 = all in bounds.
    """
    ta = np.asarray(ta_c, dtype=np.float64)
    tmrt = np.asarray(tmrt_c, dtype=np.float64)
    va = np.asarray(va10_ms, dtype=np.float64)
    e_kpa_arr = np.asarray(e_kpa, dtype=np.float64)

    shape = np.broadcast_shapes(ta.shape, tmrt.shape, va.shape, e_kpa_arr.shape)
    ta = np.broadcast_to(ta, shape)
    tmrt = np.broadcast_to(tmrt, shape)
    va = np.broadcast_to(va, shape)
    e_kpa_arr = np.broadcast_to(e_kpa_arr, shape)

    flags = np.zeros(shape, dtype=np.uint8)

    raw_d_tmrt = tmrt - ta
    flags = np.where((ta < TA_BOUNDS[0]) | (ta > TA_BOUNDS[1]), flags | FLAG_TA, flags).astype(np.uint8)
    flags = np.where(
        (raw_d_tmrt < D_TMRT_BOUNDS[0]) | (raw_d_tmrt > D_TMRT_BOUNDS[1]), flags | FLAG_TMRT, flags
    ).astype(np.uint8)
    flags = np.where((va < VA10_BOUNDS[0]) | (va > VA10_BOUNDS[1]), flags | FLAG_WIND, flags).astype(np.uint8)
    flags = np.where(
        (e_kpa_arr < E_KPA_BOUNDS[0]) | (e_kpa_arr > E_KPA_BOUNDS[1]), flags | FLAG_VAPOUR, flags
    ).astype(np.uint8)

    ta_clamped = np.clip(ta, *TA_BOUNDS)
    d_tmrt_clamped = np.clip(raw_d_tmrt, *D_TMRT_BOUNDS)
    va_clamped = np.clip(va, *VA10_BOUNDS)
    e_kpa_clamped = np.clip(e_kpa_arr, *E_KPA_BOUNDS)
    eh_pa = e_kpa_clamped * 10.0  # kPa -> hPa: the ONE conversion point (§4.4)

    offset = _brode_polynomial_offset(ta_clamped, va_clamped, d_tmrt_clamped, eh_pa)
    utci_c = ta_clamped + offset  # P-03: polynomial evaluates the offset, UTCI = Ta + offset
    return utci_c, flags


# ── T07 — stress categories & official palette ────────────────────────────────────────────
# Bounds half-open [min, max); transcribed verbatim from
# docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md §2.3, itself sourced from
# U01 Table 1 (lines 13-22) / U06 §2.1 palette (lines 91-102) -- P-04.
UTCI_CLASSES: list[dict] = [
    {"index": 0, "min": -np.inf, "max": -40.0, "label": "Extreme cold stress", "hex": "#4B0082"},
    {"index": 1, "min": -40.0, "max": -27.0, "label": "Very strong cold stress", "hex": "#8B00FF"},
    {"index": 2, "min": -27.0, "max": -13.0, "label": "Strong cold stress", "hex": "#0000FF"},
    {"index": 3, "min": -13.0, "max": 0.0, "label": "Moderate cold stress", "hex": "#007FFF"},
    {"index": 4, "min": 0.0, "max": 9.0, "label": "Slight cold stress", "hex": "#00FFFF"},
    {"index": 5, "min": 9.0, "max": 26.0, "label": "No thermal stress", "hex": "#00FF00"},
    {"index": 6, "min": 26.0, "max": 32.0, "label": "Moderate heat stress", "hex": "#FFFF00"},
    {"index": 7, "min": 32.0, "max": 38.0, "label": "Strong heat stress", "hex": "#FF7F00"},
    {"index": 8, "min": 38.0, "max": 46.0, "label": "Very strong heat stress", "hex": "#FF0000"},
    {"index": 9, "min": 46.0, "max": np.inf, "label": "Extreme heat stress", "hex": "#800000"},
]
UTCI_NODATA_CLASS = 255

_CLASS_MINS = np.array([c["min"] for c in UTCI_CLASSES])


def classify_stress(utci_c) -> np.ndarray:
    """10-class official UTCI stress category per cell. Bounds half-open [min, max).
    NaN -> UTCI_NODATA_CLASS (255)."""
    arr = np.asarray(utci_c, dtype=np.float64)
    idx = np.searchsorted(_CLASS_MINS, arr, side="right") - 1
    idx = np.clip(idx, 0, len(UTCI_CLASSES) - 1)
    out = idx.astype(np.uint8)
    out = np.where(np.isnan(arr), UTCI_NODATA_CLASS, out)
    return out


# U01 §2.3 (lines 84-93) -- 4-tier municipal presentation layer over the 10 classes.
MUNICIPAL_TIERS: list[dict] = [
    {"index": 0, "min": -np.inf, "max": 26.0, "label": "Comfort"},
    {"index": 1, "min": 26.0, "max": 32.0, "label": "Caution / mitigation alert"},
    {"index": 2, "min": 32.0, "max": 38.0, "label": "High vulnerability"},
    {"index": 3, "min": 38.0, "max": np.inf, "label": "Emergency"},
]
_TIER_MINS = np.array([t["min"] for t in MUNICIPAL_TIERS])


def municipal_risk_tier(utci_c) -> np.ndarray:
    """4-tier presentation layer (U01 §2.3) -- a VIEW over classify_stress, never a replacement."""
    arr = np.asarray(utci_c, dtype=np.float64)
    idx = np.searchsorted(_TIER_MINS, arr, side="right") - 1
    idx = np.clip(idx, 0, len(MUNICIPAL_TIERS) - 1)
    out = idx.astype(np.uint8)
    out = np.where(np.isnan(arr), UTCI_NODATA_CLASS, out)
    return out
