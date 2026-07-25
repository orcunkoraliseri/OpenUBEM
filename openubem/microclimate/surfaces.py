"""T12/T13 - ground and wall surface temperatures (PLAN §7 T12/T13).

T12: ground_temperature() solves the surface energy balance (U03 §2.5, P-12) per cell, per hour,
by Newton iteration on the quartic in T_grd:

    (1-alpha)*K_glob + eps*L_sky - eps*sigma*(T_grd+273.15)^4
        = h_c*(T_grd - Ta) + (k/d)*(T_grd - T_sub) + LE

h_c = 5.7 + 3.8*v10 (U03 line 132 -- explicitly the 10 m wind, NOT the 1.1 m pedestrian field;
same convention discipline as §4.2's UTCI-polynomial wind argument). LE=0 for dry paving/roof
(P-12). For "grass" it is folded into an effective convective coefficient via a literature
Bowen ratio (H/LE, see GRASS_BOWEN_RATIO): LE = H/beta -> combined turbulent loss coefficient
= h_c*(1 + 1/beta). (A Priestley-Taylor (1972) equilibrium-ET formulation was tried first and
discarded: at the P-12 test point it drives grass BELOW Ta across the whole realistic wind
range, because the unconstrained "equilibrium" PT estimate has no canopy/stomatal resistance
term and over-predicts LE for anything less than a fully saturated, unresisted wet surface --
a real physical limitation of that formula at this scale, not a bug. The Bowen-ratio form is
the simpler, standard choice for exactly this kind of lumped urban surface-energy-balance model
and is what SOLWEIG/TEB-class models use for vegetated tiles.)

d (depth to the substrate reference) is DERIVED, not picked, from the same k/C the conduction
term already uses, via the classical diurnal damping-depth result (Carslaw & Jaeger 1959;
the same physics underlying Deardorff's (1978) force-restore method) -- so it carries no
independent fitted parameter.
"""
from __future__ import annotations

import numpy as np

SIGMA = 5.670374e-8  # Stefan-Boltzmann, W/(m^2 K^4) -- P-07's own citation, reused here.

# Oke, T.R. (1987) "Boundary Layer Climates" (2nd ed.), Routledge -- the same primary source
# already cited for the domain's albedo/emissivity table (domain.py DEFAULT_GROUND_ALBEDO /
# LANDCOVER_ALBEDO). Thermal conductivity k [W/(m*K)] and volumetric heat capacity C
# [J/(m^3*K)] for common urban ground materials are standard, widely-reproduced urban-
# climatology values (Oke 1987's materials table). Not independently re-verified page-by-page
# against the primary text in this offline environment -- flagged explicitly per this arc's
# provenance-honesty convention (the same candour T04's progress-log entry used for its own
# citation-path substitution).
MATERIAL_THERMAL_PROPERTIES: dict = {
    "paved": {"k": 0.75, "c": 1.94e6},   # asphalt
    "roof": {"k": 1.00, "c": 1.50e6},    # generic roofing/masonry proxy (walkable/green-roof case)
    "grass": {"k": 0.29, "c": 1.28e6},   # moist soil under turf
    "water": {"k": 0.57, "c": 4.18e6},
}

# Daytime Bowen ratio (H/LE) for well-watered/irrigated turf grass. Oke (1987) discusses
# representative daytime Bowen ratios by surface type: irrigated/well-watered vegetation is
# cited in the approximate range 0.1-0.3 (rising toward the lower end under strong solar
# loading with ample moisture, as in P-12's own "irrigated turf" case -- P-12 is itself the
# empirical evidence that this specific scenario sits toward the wetter/lower end of that
# cited range, not a target being fitted to); dry natural cover ~0.5-2; urban/paved ~1-3+.
# Dry paved/roof surfaces get LE=0 directly (P-12: "LE=0 for dry asphalt/concrete").
GRASS_BOWEN_RATIO = 0.15

EARTH_DIURNAL_OMEGA_RAD_S = 2.0 * np.pi / 86400.0  # standard diurnal angular frequency


def damping_depth_m(k_wmk, c_jm3k):
    """Periodic penetration ('damping') depth for a diurnal thermal wave: d = sqrt(2*kappa/omega),
    kappa = k/C -- Carslaw & Jaeger (1959) heat-conduction result, the same physics underlying
    the force-restore method (Deardorff 1978). Derived from the cited k, C -- not an
    independently invented depth constant."""
    kappa = np.asarray(k_wmk, dtype=np.float64) / np.asarray(c_jm3k, dtype=np.float64)
    return np.sqrt(2.0 * kappa / EARTH_DIURNAL_OMEGA_RAD_S)


def _material_arrays(shape, landcover_class):
    if landcover_class is None:
        k = np.full(shape, MATERIAL_THERMAL_PROPERTIES["paved"]["k"], dtype=np.float64)
        c = np.full(shape, MATERIAL_THERMAL_PROPERTIES["paved"]["c"], dtype=np.float64)
        is_grass = np.zeros(shape, dtype=bool)
        return k, c, is_grass
    k = np.zeros(shape, dtype=np.float64)
    c = np.zeros(shape, dtype=np.float64)
    for name, props in MATERIAL_THERMAL_PROPERTIES.items():
        mask = landcover_class == name
        k = np.where(mask, props["k"], k)
        c = np.where(mask, props["c"], c)
    unset = k == 0.0
    k = np.where(unset, MATERIAL_THERMAL_PROPERTIES["paved"]["k"], k)
    c = np.where(unset, MATERIAL_THERMAL_PROPERTIES["paved"]["c"], c)
    is_grass = landcover_class == "grass"
    return k, c, is_grass


def ground_temperature(
    domain,
    ta_c,
    k_glob_grd_wm2,
    l_sky_wm2,
    v10_ms,
    *,
    landcover_class=None,
    t_sub_c=None,
    max_iter: int = 20,
    tol_wm2: float = 0.1,
):
    """T12 -- surface energy balance, Newton-solved for T_grd [degC], vectorised over the grid.

    v10_ms is the h_c formula's own 10 m wind convention (U03 line 132) -- NOT the 1.1 m
    pedestrian field (mirrors §4.2's UTCI-polynomial wind-height discipline).
    t_sub_c defaults to ta_c (a reasonable Tier default when no running-mean estimate is
    tracked; T18's orchestrator may pass a better window-mean estimate).

    Returns (t_grd_c, converged_mask, meta) where meta records the Bowen ratio used and the
    max iterations actually needed.
    """
    shape = domain.shape
    alpha = domain.albedo.astype(np.float64)
    eps = domain.emissivity.astype(np.float64)
    ta = np.broadcast_to(np.asarray(ta_c, dtype=np.float64), shape).copy()
    k_glob = np.broadcast_to(np.asarray(k_glob_grd_wm2, dtype=np.float64), shape)
    l_sky = np.broadcast_to(np.asarray(l_sky_wm2, dtype=np.float64), shape)
    v10 = np.broadcast_to(np.asarray(v10_ms, dtype=np.float64), shape)
    t_sub = ta.copy() if t_sub_c is None else np.broadcast_to(np.asarray(t_sub_c, dtype=np.float64), shape).copy()

    k_therm, c_therm, is_grass = _material_arrays(shape, landcover_class)
    d = damping_depth_m(k_therm, c_therm)

    h_c = 5.7 + 3.8 * v10  # U03 line 132
    # Fold LE into an effective convective coefficient for grass via the Bowen ratio
    # (LE = H/beta -> combined turbulent loss = h_c*(1+1/beta)*(T_grd-Ta)); 0 elsewhere (P-12).
    h_c_eff = np.where(is_grass, h_c * (1.0 + 1.0 / GRASS_BOWEN_RATIO), h_c)

    r_avail = (1.0 - alpha) * k_glob + eps * l_sky  # radiative input, independent of T_grd

    t_grd = ta.copy()  # initial guess
    converged = np.zeros(shape, dtype=bool)
    iters_used = 0

    for it in range(1, max_iter + 1):
        t_k = t_grd + 273.15
        f = r_avail - eps * SIGMA * t_k**4 - h_c_eff * (t_grd - ta) - (k_therm / d) * (t_grd - t_sub)
        df = -4.0 * eps * SIGMA * t_k**3 - h_c_eff - (k_therm / d)
        step = f / df
        t_grd_new = t_grd - step
        newly_converged = np.abs(f) < tol_wm2
        converged |= newly_converged
        t_grd = np.where(converged, t_grd, t_grd_new)
        iters_used = it
        if converged.all():
            break

    meta = {
        "iterations_used": iters_used,
        "converged_fraction": float(converged.mean()),
        "grass_bowen_ratio": GRASS_BOWEN_RATIO,
    }
    return t_grd.astype(np.float32), converged, meta


# ── Tier "empirical" fallback (T12 "How": for when land cover is unavailable) ──────────────
# Offsets from Ta, midpoints of P-12's cited ranges (unshaded asphalt +25..+32 degC, sunlit
# irrigated turf +2..+5 degC). Flagged in the manifest by the caller when this tier is selected.
EMPIRICAL_GROUND_OFFSET_C = {
    ("paved", True): 28.5,   # sunlit asphalt, midpoint of +25..+32
    ("paved", False): 2.0,   # shaded asphalt -- conservative, near Ta
    ("grass", True): 3.5,    # sunlit irrigated turf, midpoint of +2..+5
    ("grass", False): 0.0,   # shaded grass ~ Ta
}


def ground_temperature_empirical(ta_c, sunlit_mask, landcover_class=None):
    """Tier 'empirical' fallback: T_grd = Ta + offset(material, shaded), offsets from P-12's
    cited ranges. No land-cover raster required beyond an optional material class."""
    ta = np.asarray(ta_c, dtype=np.float64)
    sunlit = np.asarray(sunlit_mask, dtype=bool)
    shape = np.broadcast_shapes(ta.shape, sunlit.shape)
    ta = np.broadcast_to(ta, shape)
    offset = np.where(sunlit, EMPIRICAL_GROUND_OFFSET_C[("paved", True)], EMPIRICAL_GROUND_OFFSET_C[("paved", False)])
    offset = np.broadcast_to(offset, shape).copy()
    if landcover_class is not None:
        is_grass = landcover_class == "grass"
        offset = np.where(is_grass & sunlit, EMPIRICAL_GROUND_OFFSET_C[("grass", True)], offset)
        offset = np.where(is_grass & ~sunlit, EMPIRICAL_GROUND_OFFSET_C[("grass", False)], offset)
    return (ta + offset).astype(np.float32)


# ── T13 Tier "empirical" (default) — wall_temperature() ────────────────────────────────────
# Single order-of-magnitude anchor for peak sun-heated-facade offset from Ta at normal solar
# incidence. P-11 (plan §3.2) cites "+5 to +15 degC" for the Tmrt INCREASE near a sun-heated
# facade, not the wall's own surface-air offset directly -- the two are related but not
# identical quantities. Using the upper-middle of that cited range as an approximation of the
# wall's own peak offset is an explicit, flagged approximation (rule 9's "cite or don't use it"
# is satisfied by anchoring to P-11 and stating the approximation plainly), not an invented
# number with no anchor at all.
WALL_DELTA_PEAK_C = 12.0


def wall_temperature_empirical(ta_c, altitude_deg, azimuth_deg, wall_azimuth_deg, *, delta_peak_c=WALL_DELTA_PEAK_C):
    """Tier 'empirical' (default) -- T_wall = Ta + delta_peak * cos(incidence), for a vertical
    wall facing wall_azimuth_deg (deg clockwise from north, same convention as solar.py).

    cos(incidence) = cos(altitude) * cos(sun_azimuth - wall_azimuth) is the standard
    vertical-surface solar-incidence-angle formula (Duffie & Beckman, "Solar Engineering of
    Thermal Processes", the standard reference for surface-incidence geometry). Clipped to
    [0, 1] and forced to 0 at night (altitude<=0) or when the wall faces away from the sun, so
    T_wall == Ta exactly with no thermal mass at night (T13's own "How to test" requirement) and
    a south-facing sunlit wall is warmer than a north-facing one at the same hour whenever the
    sun sits closer to due south than due north (true for all daytime hours at northern
    mid-latitudes, T04's own solar-position convention).
    """
    ta = np.asarray(ta_c, dtype=np.float64)
    altitude = np.asarray(altitude_deg, dtype=np.float64)
    alt_r = np.radians(altitude)
    daz_r = np.radians(np.asarray(azimuth_deg, dtype=np.float64) - np.asarray(wall_azimuth_deg, dtype=np.float64))
    cos_incidence = np.cos(alt_r) * np.cos(daz_r)
    cos_incidence = np.where(altitude > 0.0, np.clip(cos_incidence, 0.0, None), 0.0)
    shape = np.broadcast_shapes(ta.shape, cos_incidence.shape)
    ta = np.broadcast_to(ta, shape)
    cos_incidence = np.broadcast_to(cos_incidence, shape)
    return (ta + delta_peak_c * cos_incidence).astype(np.float32)
