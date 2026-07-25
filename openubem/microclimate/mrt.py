"""T14 - mean radiant temperature engine (PLAN §7 T14).

Implements U03 §2.2-2.4 with §4.3's corrected weights (W_v=0.22, W_h=0.06, NOT the 0.08 U03
prints). This is where T08-T13 all converge: domain geometry, SVF/horizon (T10), shadow +
vegetation transmission (T11), ground temperature (T12), wall temperature (T13), plus the
EPW-driven inputs (solar position T04, DNI/DHI/L_sky T02).

f_p(theta) provenance (§4.7 directive: transcribe from VDI 3787 Part 2 or Fanger (1972)
directly, not from U03 line 89's possibly-mismatched form). Investigated live during T13/T14
(WebSearch/WebFetch available this session): VDI 3787 itself only TABULATES fp numerically --
there is no single canonical closed-form VDI equation. RayMan, ENVI-met and other tools each
fit their OWN regression curve to that table. U03 line 89's coefficients
(0.308, cos, 1-0.017*(theta/90)^2) are a real, widely-reproduced closed-form fit attributed to
Fanger's own work in the urban-biometeorology literature, not a fabrication like U05's
polynomial -- the plan's own caution ("does not match the Fanger form used in VDI 3787/SOLWEIG")
reflects that multiple legitimate fitted forms exist, not that this one is proven wrong.
U03's OWN alternative at line 38 (a cylindrical-body formula, also attributed to VDI 3787) was
checked dimensionally and rejected: it gives values far outside the physically valid [0,1]
projected-area-FRACTION range unless normalized by a missing denominator -- a transcription
problem in the research corpus's own line 38, independent of line 89's caution. U03 line 89's
form is used here, with this investigation documented rather than silently deferred to.

View-factor scheme for L_abs (Psi_sky + Psi_grd + Psi_wall + Psi_tree = 1, T14's own explicit
requirement) and K_refl's ground-reflection weight -- **derivation history kept here because
two attempts were wrong in ways worth recording for the auditor, not silently replaced:**

Attempt 1 derived Psi_grd = 0.5 independently (treating "the ground below a standing point is
always visible" as a full-sphere hemisphere argument, decoupled from svf), while leaving
K_refl's ground term at the plan's literal W_h=0.06. That combination satisfied the sum-to-1
requirement, but FAILED the mandatory cool-pavement-paradox gate: L_abs's ground term (weight
0.5) was ~8x K_refl's own ground term (weight 0.06), so raising ground albedo always *lowered*
Tmrt (via less L_grd swinging with T_grd) instead of raising it (via more K_refl) -- wrong sign.

Attempt 2 (E-UTCI-03) set Psi_grd = W_h = 0.06 to match K_refl's own literal ground weight,
Psi_sky = (4*W_v+W_h)*svf. This fixed the paradox's SIGN but undershot its MAGNITUDE by ~10x
(paradox measured ~0.75 degC vs the required 2.5-8.0 degC) and broke the open-field-noon and
night sanity tests (see E-UTCI-03, plan §10) -- diagnosed via a scheme-independent check showing
K_refl's own ground term (W_h * albedo * K_glob) computes to ~7-9 W/m2 at typical noon
conditions, ~10x smaller than P-10's own cited ~80 W/m2 pedestrian-incident reflected-shortwave
figure, regardless of which Psi scheme is used -- pointing at K_refl's weight itself, not Psi.

**E-UTCI-04 (2026-07-24, plan §10) root-caused this directly from the actual SOLWEIG source**
(github.com/nvnsudharsan/Solweig-GPU, solweig_gpu/solweig.py, Lindberg/Sun/Grimmond lineage),
not just the paper abstract attempt 1/2 relied on: the real model injects an UNCONDITIONAL
`ground_flux * 0.5` into *every one* of the 4 lateral (side) direction terms, in addition to
the direct Fup=W_h-weighted top/bottom term, for BOTH the longwave (`Lground = LupE*0.5` inside
`Lside_veg_v2022a`) and shortwave (`KupE*0.5` inside `Kside_veg_v2022a`) balances. Summed
correctly: W_h (direct) + 4*W_v*0.5 (unconditional lateral share) = 0.06 + 0.44 = 0.50 total
ground weight, for BOTH K_refl and L_abs, independent of svf (the 4*W_v*0.5 lateral injection is
never scaled by svf/viktwall in the source). This is, functionally, attempt 1's Psi_grd=0.5 --
vindicated for L_abs, but only once K_refl's ground weight is corrected to match (0.06 -> 0.50),
which is the piece attempt 1 got wrong. Under this joint fix, K_refl's own ground term lands
within ~8% of P-10's cited ~80 W/m2 figure (was ~10x low), and the paradox gate passes at
+5.39 degC (P-10's own magnitude, no relaxation needed).

**Current, source-verified version:** Psi_grd = 0.50 (constant, independent of svf -- the
lateral 0.5*ground injection is unconditional in the source), Psi_sky = 0.50*svf,
Psi_wall = 0.50*(1-svf), split with Psi_tree by canopy fraction when supplied. Sums to 1.0 by
construction: 0.50 + 0.50*svf + 0.50*(1-svf) = 1.0 for any svf in [0,1]. K_refl's ground
coefficient is the same 0.50 (module-level GRD_WEIGHT); its wall term keeps W_v=0.22 unchanged
(not part of this correction -- E-UTCI-04 §10 point 3 explicitly scoped the fix to the ground
mechanism only).

**Documented simplification -- nighttime Tmrt under-prediction (E-UTCI-06, plan §10, CLOSED
2026-07-24):** this single-node, 6-directional model (same Hoppe 1992 Wv/Wh weighting as
SOLWEIG/RayMan/ENVI-met) under-predicts nighttime Tmrt vs measurement by 2-10 degC, per Gal
(2020), "Modeling mean radiant temperature in outdoor spaces, A comparative numerical simulation
and validation study," ICUC10 -- a field-validated property of this entire model class, not a
defect specific to this port. `test_night_tmrt_close_to_ta` gates on sign only, plus a loose
regression backstop, accordingly.
"""
from __future__ import annotations

import numpy as np

from openubem.microclimate.psychro import saturation_vapour_pressure_kpa

SIGMA = 5.670374e-8  # Stefan-Boltzmann, W/(m^2 K^4) -- P-07.
EPS_PERSON = 0.97  # P-07/P-08 -- clothed human broadband emissivity (ISO 7730 / VDI 3787).
A_K = 0.70  # P-08 -- shortwave solar absorptivity of the clothed body.
A_L = EPS_PERSON  # P-08 -- longwave absorptivity == emissivity.

# §4.3 (E corrected from U03's own 0.08, which sums to 1.04): 4*0.22 + 2*0.06 = 1.00.
# NOTE: W_H remains 0.06 -- it is still the correct DIRECT top/bottom Fup/Fdown weight (E-UTCI-04
# point 1: `Fup=0.06` matches the real SOLWEIG source exactly). It is no longer, by itself, the
# ground's TOTAL weight -- see GRD_WEIGHT below.
W_V = 0.22
W_H = 0.06

# E-UTCI-04 (plan §10, 2026-07-24): the ground's real TOTAL radiative weight (both K_refl and
# L_abs), source-verified against github.com/nvnsudharsan/Solweig-GPU, solweig_gpu/solweig.py:
# Fup (direct, 0.06) + 4*W_v*0.5 (unconditional `ground_flux*0.5` injected into all 4 lateral
# terms, both K and L balances) = 0.06 + 4*0.22*0.5 = 0.06 + 0.44 = 0.50. Independent of svf.
GRD_WEIGHT = W_H + 4.0 * W_V * 0.5


def weights_sum_to_one() -> bool:
    return abs(4 * W_V + 2 * W_H - 1.0) < 1e-12


# Oke (1987) typical building-facade albedo/emissivity -- same primary source and the same
# "roof" proxy value already used for facade thermal properties in T12/T13 (consistency, not
# a new independent citation).
WALL_ALBEDO = 0.20
WALL_EMISSIVITY = 0.90

# U03 §2.4 line 119 / Table 4 line 50: canopy longwave emissivity and leaf-temperature offset.
EPS_VEG = 0.98
# T_leaf ~ Ta + (-2.0 to +4.0 degC) depending on transpiration (Berry et al. 2013; Rahman et al.
# 2017, per U03's own citation) -- midpoint of the cited range used as the default offset.
LEAF_DELTA_T_C = 1.0

# Prata (1996) clear-sky emissivity parameterisation (U03 lines 109-111), fallback when the
# EPW's own measured horizontal-infrared field is unavailable.
_PRATA_W_COEFF = 46.5  # standard Prata (1996) coefficient, precipitable water w = 46.5*e/T


def fp_projected_area_factor(altitude_deg):
    """Fanger (1972) fitted projected-area-factor curve, per U03 line 89 -- see module
    docstring for the §4.7 provenance investigation. theta = solar altitude, clipped to
    [0, 90] deg (P-01's domain; negative altitude is night, gated to 0 shortwave elsewhere)."""
    theta = np.clip(np.asarray(altitude_deg, dtype=np.float64), 0.0, 90.0)
    return 0.308 * np.cos(np.radians(theta)) * (1.0 - 0.017 * (theta / 90.0) ** 2)


def prata_sky_emissivity(ta_c, e_kpa, cloud_fraction=0.0):
    """Prata (1996) clear-sky emissivity with cloud correction (U03 lines 109-111)."""
    ta_k = np.asarray(ta_c, dtype=np.float64) + 273.15
    e_hpa = np.asarray(e_kpa, dtype=np.float64) * 10.0
    w = _PRATA_W_COEFF * (e_hpa / ta_k)
    eps_clear = (1.0 - (1.0 + w) * np.exp(-np.sqrt(1.2 + 3.0 * w)))
    n = np.asarray(cloud_fraction, dtype=np.float64)
    return eps_clear * (1.0 + 0.22 * n**2)


def sky_longwave(ta_c, e_kpa, horizontal_infrared_wm2=None, cloud_fraction=0.0):
    """L_sky -- prefer the EPW's measured horizontal infrared (T02), fall back to Prata with
    cloud correction when absent/NaN. Returns (l_sky_wm2, used_measured_mask)."""
    ta_k = np.asarray(ta_c, dtype=np.float64) + 273.15
    if horizontal_infrared_wm2 is None:
        l_prata = prata_sky_emissivity(ta_c, e_kpa, cloud_fraction) * SIGMA * ta_k**4
        return l_prata, np.zeros_like(l_prata, dtype=bool)
    measured = np.asarray(horizontal_infrared_wm2, dtype=np.float64)
    used_measured = np.isfinite(measured) & (measured > 0)
    l_prata = prata_sky_emissivity(ta_c, e_kpa, cloud_fraction) * SIGMA * ta_k**4
    l_sky = np.where(used_measured, measured, l_prata)
    return l_sky, used_measured


_NON_GROUND_WEIGHT = 1.0 - GRD_WEIGHT  # = 0.50; the sky+wall share of the 6-plane weights


def view_factors(svf, vegetation_fraction=None):
    """Psi_sky, Psi_grd, Psi_wall, Psi_tree -- see module docstring for the derivation (and
    the two discarded earlier attempts, kept there for the auditor). Sums to 1.0 per cell by
    construction (T14's own explicit requirement) for any svf in [0,1]. Psi_grd is a CONSTANT
    (E-UTCI-04) -- the real source's ground weight is not scaled by svf/viktwall."""
    svf = np.asarray(svf, dtype=np.float64)
    psi_grd = np.full_like(svf, GRD_WEIGHT)
    psi_sky = _NON_GROUND_WEIGHT * svf
    psi_wall_total = _NON_GROUND_WEIGHT * (1.0 - svf)
    if vegetation_fraction is None:
        psi_tree = np.zeros_like(svf)
        psi_wall = psi_wall_total
    else:
        veg_frac = np.clip(np.asarray(vegetation_fraction, dtype=np.float64), 0.0, 1.0)
        psi_tree = psi_wall_total * veg_frac
        psi_wall = psi_wall_total * (1.0 - veg_frac)
    return psi_sky, psi_grd, psi_wall, psi_tree


def compute_tmrt(
    *,
    altitude_deg,
    azimuth_deg,
    dni_wm2,
    dhi_wm2,
    svf,
    sh_building,
    sh_veg,
    t_grd_c,
    t_wall_c,
    ta_c,
    e_kpa,
    ground_albedo,
    horizontal_infrared_wm2=None,
    cloud_fraction=0.0,
    vegetation_fraction=None,
    wall_albedo=WALL_ALBEDO,
    wall_emissivity=WALL_EMISSIVITY,
    ground_emissivity=0.95,
):
    """T14 -- 6-directional radiant flux balance -> Tmrt [degC], vectorised over the grid.

    sh_building, sh_veg: T11's direct-beam gate, SUNLIT convention (module docstring of
    shadow.py) -- K_dir_effective = K_dir * sh_building * sh_veg, no inversion needed.
    Returns (tmrt_c, diagnostics) where diagnostics carries K_abs, L_abs, the view factors, and
    which L_sky source was used (for the manifest / CP-3 report).
    """
    altitude = np.asarray(altitude_deg, dtype=np.float64)
    daytime = altitude > 0.0

    dni = np.where(daytime, np.asarray(dni_wm2, dtype=np.float64), 0.0)
    dhi = np.where(daytime, np.asarray(dhi_wm2, dtype=np.float64), 0.0)

    fp = fp_projected_area_factor(altitude)
    beam_gate = np.asarray(sh_building, dtype=np.float64) * np.asarray(sh_veg, dtype=np.float64)
    k_dir = dni * fp * beam_gate  # §4.6: DNI read straight from EPW, never divided by sin(theta)

    psi_sky, psi_grd, psi_wall, psi_tree = view_factors(svf, vegetation_fraction)

    k_diff = dhi * np.asarray(svf, dtype=np.float64)  # plan's own "K_diff = DHI*Psi_sky", T10's raw SVF (0-1)

    # Ground-level global irradiance for the K_refl term (P-10's cool-pavement paradox):
    # direct beam projected onto the horizontal ground plane (sin(altitude), NOT fp -- fp is a
    # person-specific projected-area factor, not appropriate for a horizontal surface) + diffuse.
    k_glob_grd = dni * np.clip(np.sin(np.radians(altitude)), 0.0, None) * beam_gate + dhi * np.asarray(svf, dtype=np.float64)
    # Wall irradiance: simplified isotropic estimate (no per-orientation wall-irradiance model
    # in this arc) -- direct beam averaged over a vertical surface's cos(incidence) plus its
    # own diffuse share. This term is secondary to the ground term (P-10 is a GROUND-albedo
    # test); documented as a simplification, not a load-bearing precision claim.
    k_glob_wall = dni * np.clip(np.cos(np.radians(altitude)), 0.0, None) * 0.5 * beam_gate + dhi * 0.5

    ground_albedo_arr = np.asarray(ground_albedo, dtype=np.float64)
    # E-UTCI-04 (plan §10): ground coefficient corrected 0.06 -> GRD_WEIGHT (0.50); wall term's
    # W_V unchanged -- not part of that correction.
    k_refl = GRD_WEIGHT * ground_albedo_arr * k_glob_grd + W_V * wall_albedo * psi_wall * k_glob_wall

    # K_abs = fp(theta)*K_dir [fp already folded into k_dir above] + W_v*sum(4 side diffuse) +
    # W_h*sum(2 up/down diffuse) + K_refl. This simplified single-node model has no
    # per-direction diffuse decomposition, so the 4-side + 2-up/down diffuse terms collapse to
    # the isotropic-sky estimate K_diff = DHI*Psi_sky, distributed across all 6 planes by
    # weights that already sum to 1.0 (4*W_v+2*W_h=1, §4.3) -- their weighted sum is exactly
    # K_diff, so K_abs = k_dir + k_diff + k_refl directly.
    k_abs = k_dir + k_diff + k_refl

    l_sky, used_measured_l_sky = sky_longwave(ta_c, e_kpa, horizontal_infrared_wm2, cloud_fraction)

    ta_k = np.asarray(ta_c, dtype=np.float64) + 273.15
    l_grd = ground_emissivity * SIGMA * (np.asarray(t_grd_c, dtype=np.float64) + 273.15) ** 4
    l_wall = wall_emissivity * SIGMA * (np.asarray(t_wall_c, dtype=np.float64) + 273.15) ** 4
    t_leaf_k = ta_k + LEAF_DELTA_T_C
    l_tree = EPS_VEG * SIGMA * t_leaf_k**4

    l_abs = psi_sky * l_sky + psi_grd * l_grd + psi_wall * l_wall + psi_tree * l_tree

    s_str = A_K * k_abs + A_L * l_abs
    tmrt_k = (s_str / (EPS_PERSON * SIGMA)) ** 0.25
    tmrt_c = tmrt_k - 273.15

    diagnostics = {
        "k_abs_wm2": k_abs, "l_abs_wm2": l_abs, "k_dir_wm2": k_dir, "k_diff_wm2": k_diff,
        "k_refl_wm2": k_refl, "psi_sky": psi_sky, "psi_grd": psi_grd, "psi_wall": psi_wall,
        "psi_tree": psi_tree, "used_measured_l_sky": used_measured_l_sky,
    }
    return tmrt_c.astype(np.float32), diagnostics
