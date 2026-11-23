import math
from typing import Any

import numpy as np

DEG2RAD: float = math.pi / 180.0
GROUND_ALBEDO_DEFAULT: float = 0.2

# EnergyPlus SolarShading.cc::Perez 1990 anisotropic sky diffuse coefficients
_PEREZ_EPS_BINS = np.asarray(
    [1.065, 1.23, 1.5, 1.95, 2.8, 4.5, 6.2], dtype=np.float64
)
_PEREZ_F11 = np.asarray(
    [-0.0083117, 0.1299457, 0.3296958, 0.5682053, 0.8730280, 1.1326077, 1.0601591, 0.6777470],
    dtype=np.float64,
)
_PEREZ_F12 = np.asarray(
    [0.5877285, 0.6825954, 0.4868735, 0.1874525, -0.3920403, -1.2367284, -1.5999137, -0.3272588],
    dtype=np.float64,
)
_PEREZ_F13 = np.asarray(
    [-0.0620636, -0.1513752, -0.2210958, -0.2951290, -0.3616149, -0.4118494, -0.3589221, -0.2504286],
    dtype=np.float64,
)
_PEREZ_F21 = np.asarray(
    [-0.0596012, -0.0189325, 0.0554140, 0.1088631, 0.2255647, 0.2877813, 0.2642124, 0.1561313],
    dtype=np.float64,
)
_PEREZ_F22 = np.asarray(
    [0.0721249, 0.0659650, -0.0639588, -0.1519229, -0.4620442, -0.8230357, -1.1272340, -1.3765031],
    dtype=np.float64,
)
_PEREZ_F23 = np.asarray(
    [-0.0220216, -0.0288748, -0.0260542, -0.0139754, 0.0012448, 0.0558651, 0.1310694, 0.2506212],
    dtype=np.float64,
)


def calc_solar_direction_cosines(
    latitude_deg: float,
    longitude_deg: float,
    time_zone: float,
    steps_per_hour: int = 12,
    n_days: int = 365,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """WeatherManager.cc::ReadEPlusWeatherForDay & SolarShading.cc::SunPosition.

    Computes solar direction cosines ``(solcos_x, solcos_y, solcos_z)`` (East, North, Up)
    and extraterrestrial normal irradiance ``i_ext`` [W/m2] at the midpoint of every
    zone timestep over ``n_days`` (non-leap year 1..365).
    """
    n_steps_day = 24 * steps_per_hour
    n_total = n_days * n_steps_day

    jday = np.repeat(np.arange(1, n_days + 1, dtype=np.float64), n_steps_day)
    step_in_day = np.tile(np.arange(n_steps_day, dtype=np.float64), n_days)
    # EnergyPlus WeatherManager.cc timestep solar time alignment
    t_std = (step_in_day + 1.0) / float(steps_per_hour)

    # EnergyPlus WeatherManager.cc (Woolf / ASHRAE) day angle
    g = 2.0 * math.pi * (jday - 1.0) / 365.0
    # Equation of time (hours) and declination (radians) — Spencer 1971 / ASHRAE
    eot_hr = (229.18 / 60.0) * (
        0.000075
        + 0.001868 * np.cos(g)
        - 0.032077 * np.sin(g)
        - 0.014615 * np.cos(2.0 * g)
        - 0.04089 * np.sin(2.0 * g)
    )
    decl = (
        0.006918
        - 0.399912 * np.cos(g)
        + 0.070257 * np.sin(g)
        - 0.006758 * np.cos(2.0 * g)
        + 0.000907 * np.sin(2.0 * g)
        - 0.002697 * np.cos(3.0 * g)
        + 0.00148 * np.sin(3.0 * g)
    )

    t_sol = t_std + eot_hr + (longitude_deg - 15.0 * time_zone) / 15.0
    ha = math.pi * (t_sol - 12.0) / 12.0

    lat = latitude_deg * DEG2RAD
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_decl = np.sin(decl)
    cos_decl = np.cos(decl)
    sin_ha = np.sin(ha)
    cos_ha = np.cos(ha)

    solcos_z = sin_lat * sin_decl + cos_lat * cos_decl * cos_ha
    solcos_x = -cos_decl * sin_ha
    solcos_y = sin_decl * cos_lat - cos_decl * sin_lat * cos_ha
    i_ext = 1367.0 * (1.0 + 0.033 * np.cos(2.0 * math.pi * jday / 365.0))
    return (
        solcos_x.reshape(n_total),
        solcos_y.reshape(n_total),
        solcos_z.reshape(n_total),
        i_ext.reshape(n_total),
    )


def calc_perez_sky_factors(
    dni: np.ndarray,
    dhi: np.ndarray,
    cos_z: np.ndarray,
    i_ext: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """SolarShading.cc::AnisoSkyViewFactors (Perez 1990 F1, F2 brightness coeffs)."""
    cos_z_pos = np.maximum(cos_z, 0.0)
    z_rad = np.arccos(np.clip(cos_z_pos, 0.0, 1.0))
    z_deg = z_rad / DEG2RAD

    day_mask = (cos_z > 0.0) & (dhi > 1.0e-3)
    dhi_safe = np.where(day_mask, dhi, 1.0)
    z3_term = 1.041 * (z_rad**3)
    eps = (((dhi_safe + np.maximum(dni, 0.0)) / dhi_safe) + z3_term) / (1.0 + z3_term)

    bin_idx = np.searchsorted(_PEREZ_EPS_BINS, eps, side="right")
    bin_idx = np.clip(bin_idx, 0, 7)

    # Kasten-Young air mass
    denom_am = np.maximum(cos_z_pos + 0.15 * np.power(np.maximum(93.885 - z_deg, 0.5), -1.253), 1.0e-4)
    air_mass = np.where(cos_z > 0.0, 1.0 / denom_am, 38.0)
    delta = np.where(day_mask, dhi * air_mass / np.maximum(i_ext, 1.0), 0.0)

    f1 = np.maximum(
        0.0,
        _PEREZ_F11[bin_idx] + _PEREZ_F12[bin_idx] * delta + _PEREZ_F13[bin_idx] * z_rad,
    )
    f2 = _PEREZ_F21[bin_idx] + _PEREZ_F22[bin_idx] * delta + _PEREZ_F23[bin_idx] * z_rad
    f1 = np.where(day_mask, f1, 0.0)
    f2 = np.where(day_mask, f2, 0.0)
    return f1, f2


def calc_surface_incident_solar(
    dni: np.ndarray,
    dhi: np.ndarray,
    solcos_x: np.ndarray,
    solcos_y: np.ndarray,
    solcos_z: np.ndarray,
    perez_f1: np.ndarray,
    perez_f2: np.ndarray,
    tilt_deg: np.ndarray,
    azimuth_deg: np.ndarray,
    vf_ground: np.ndarray,
    sun_exposed: np.ndarray,
    sunlit_frac: np.ndarray | None = None,
    albedo: float = GROUND_ALBEDO_DEFAULT,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """SolarShading.cc::CalcInteriorSolarDistribution & InitSolarCalculations.

    Args:
        dni, dhi, solcos_*, perez_f*: Time-series arrays ``[T]`` (or ``[B, T]``).
        tilt_deg, azimuth_deg, vf_ground, sun_exposed: Surface arrays ``[S]``.
        sunlit_frac: Optional beam sunlit fraction ``[T, S]`` in ``[0, 1]`` (S3 shading).

    Returns:
        Tuple ``(i_beam, i_diff_sky, i_diff_gnd, cos_inc)``, each shape ``[T, S]``.
    """
    tilt = tilt_deg * DEG2RAD
    az = azimuth_deg * DEG2RAD
    sin_t = np.sin(tilt)
    cos_t = np.cos(tilt)
    nx = sin_t * np.sin(az)
    ny = sin_t * np.cos(az)
    nz = cos_t

    cos_inc = (
        solcos_x[:, None] * nx[None, :]
        + solcos_y[:, None] * ny[None, :]
        + solcos_z[:, None] * nz[None, :]
    )
    sun_up = (solcos_z > 0.0)[:, None]
    exp_mask = sun_exposed[None, :].astype(bool)

    cos_inc_pos = np.where(sun_up & exp_mask & (cos_inc > 0.0), cos_inc, 0.0)
    i_beam = np.maximum(dni[:, None], 0.0) * cos_inc_pos
    if sunlit_frac is not None:
        i_beam = i_beam * sunlit_frac

    b_denom = np.maximum(0.08715574274765817, solcos_z)[:, None]  # max(cos(85 deg), cosZ)
    vf_sky = 0.5 * (1.0 + cos_t)[None, :]
    f1 = perez_f1[:, None]
    f2 = perez_f2[:, None]
    aniso_mult = np.maximum(
        0.0,
        (1.0 - f1) * vf_sky + f1 * (cos_inc_pos / b_denom) + f2 * sin_t[None, :],
    )
    i_diff_sky = np.where(sun_up & exp_mask, np.maximum(dhi[:, None], 0.0) * aniso_mult, 0.0)

    ghi = np.maximum(dni, 0.0) * np.maximum(solcos_z, 0.0) + np.maximum(dhi, 0.0)
    i_diff_gnd = np.where(
        sun_up & exp_mask,
        albedo * ghi[:, None] * vf_ground[None, :],
        0.0,
    )
    return i_beam, i_diff_sky, i_diff_gnd, cos_inc_pos


def simple_glazing_normal_optics(
    u_factor: Any, shgc: Any
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """HeatBalanceManager.cc::SetupSimpleWindowGlazingSystem normal-incidence optics.

    Computes equivalent single-layer normal solar transmittance ``t_sol``,
    front reflectance ``r_sol``, and solar absorptance ``abs_sol`` from
    SimpleGlazingSystem ``(u_factor, shgc)``.
    """
    u = np.asarray(u_factor, dtype=np.float64)
    g = np.clip(np.asarray(shgc, dtype=np.float64), 0.0, 1.0)

    # EnergyPlus HeatBalanceManager.cc::SetupSimpleWindowGlazingSystem
    # High-U (single glazing, U >= 4.5) has lower direct T_sol (more inward absorbed fraction)
    def _tsol_u_high(sh: np.ndarray) -> np.ndarray:
        return np.where(
            sh < 0.7206,
            0.939998 * sh * sh + 0.20332 * sh,
            1.30415 * sh - 0.30515,
        )

    def _tsol_u_low(sh: np.ndarray) -> np.ndarray:
        return np.where(
            sh <= 0.15,
            0.41040 * sh * sh + 0.16085 * sh,
            0.085775 * sh * sh + 0.963954 * sh - 0.084958,
        )

    t_low = _tsol_u_low(g)
    t_high = _tsol_u_high(g)
    w_blend = np.clip((u - 3.4) / (4.5 - 3.4), 0.0, 1.0)
    t_sol = np.where(
        u <= 3.4,
        t_low,
        np.where(u >= 4.5, t_high, (1.0 - w_blend) * t_low + w_blend * t_high),
    )
    t_sol = np.clip(t_sol, 0.0, g)

    # Inward-flowing fraction N_in (NFRC summer film balance: R_out_s ~ 1/20.47, R_in_s ~ 1/7.7)
    r_tot = 1.0 / np.maximum(u, 0.1)
    r_out_s = 1.0 / 20.47
    r_in_s = 1.0 / 7.7
    r_glass = np.maximum(r_tot - r_out_s - r_in_s, 0.0)
    n_in = np.clip((r_out_s + 0.5 * r_glass) / np.maximum(r_out_s + r_glass + r_in_s, 1.0e-6), 0.05, 0.85)
    abs_sol = np.clip((g - t_sol) / np.maximum(n_in, 1.0e-6), 0.0, 1.0 - t_sol)
    r_sol = np.clip(1.0 - t_sol - abs_sol, 0.0, 1.0)
    return t_sol, r_sol, abs_sol


def interpolate_epw_solar_to_timestep(
    hourly: np.ndarray,
    steps_per_hour: int = 12,
) -> np.ndarray:
    """WeatherManager.cc::ReadEPlusWeatherForDay centered-hour solar interpolation."""
    prev = np.empty_like(hourly, dtype=np.float64)
    prev[0] = hourly[23]
    prev[1:] = hourly[:-1]
    nxt = np.empty_like(hourly, dtype=np.float64)
    nxt[-1] = hourly[0]
    nxt[:-1] = hourly[1:]
    out = np.empty((len(hourly), steps_per_hour), dtype=np.float64)
    half = steps_per_hour // 2
    for ts in range(1, steps_per_hour + 1):
        if ts <= half:
            w = 0.5 + ts / float(steps_per_hour)
            out[:, ts - 1] = (1.0 - w) * prev + w * hourly
        else:
            w = (ts - half) / float(steps_per_hour)
            out[:, ts - 1] = (1.0 - w) * hourly + w * nxt
    return out.reshape(-1)


def distribute_full_exterior_interior_solar(
    q_win_trans_beam_w: np.ndarray,
    q_win_trans_diff_w: np.ndarray,
    surf_area: np.ndarray,
    surf_alpha_in_sw: np.ndarray,
    is_floor: np.ndarray,
    is_opaque_interior: np.ndarray,
    win_back_loss_area: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """SolarShading.cc::CalcInteriorSolarDistribution (FullExterior).

    Transmitted beam solar strikes the zone floor; the floor absorbs
    ``alpha_floor`` of it and reflects ``(1 - alpha_floor)`` diffusely.
    Reflected beam plus transmitted diffuse solar are distributed across
    all interior opaque surfaces proportional to ``area * alpha_in_sw``
    (accounting for back-transmitted/absorbed window loss via ``win_back_loss_area``).

    Returns:
        Tuple ``(q_sw_in_abs, q_diff_incident_w_m2)`` where ``q_sw_in_abs`` is
        absorbed shortwave flux [W/m2] on each surface ``[T, S]`` and
        ``q_diff_incident_w_m2`` is interior diffuse shortwave irradiance [W/m2] ``[T]``.
    """
    floor_mask = is_floor & is_opaque_interior
    floor_area_sum = float(np.sum(np.where(floor_mask, surf_area, 0.0)))
    floor_alpha_area = float(np.sum(np.where(floor_mask, surf_area * surf_alpha_in_sw, 0.0)))

    total_aa = (
        float(np.sum(np.where(is_opaque_interior, surf_area * surf_alpha_in_sw, 0.0)))
        + max(win_back_loss_area, 0.0)
    )
    inv_total_aa = 1.0 / max(total_aa, 1.0e-12)
    diff_weight = np.where(
        is_opaque_interior,
        surf_alpha_in_sw * inv_total_aa,
        0.0,
    )

    if floor_area_sum > 1.0e-12:
        floor_alpha_eff = floor_alpha_area / floor_area_sum
        floor_beam_flux = np.where(
            floor_mask,
            surf_alpha_in_sw / floor_area_sum,
            0.0,
        )
        beam_reflected_frac = 1.0 - floor_alpha_eff
    else:
        floor_beam_flux = np.zeros_like(surf_area)
        beam_reflected_frac = 1.0

    q_beam = np.asarray(q_win_trans_beam_w, dtype=np.float64)[..., None]
    q_diff = np.asarray(q_win_trans_diff_w, dtype=np.float64)[..., None]
    q_diff_pool = q_diff + beam_reflected_frac * q_beam
    q_sw_in_abs = q_beam * floor_beam_flux + q_diff_pool * diff_weight
    q_diff_inc = (q_diff_pool[..., 0]) * inv_total_aa
    return q_sw_in_abs, q_diff_inc


def simple_glazing_angular_factors(
    cos_inc: np.ndarray,
    u_factor: np.ndarray,
    shgc: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """WindowManager.cc::SimpleWindow angular transmittance and absorptance.

    Returns ``(tau_beam, abs_beam, tau_diff, abs_diff)`` for arrays of
    ``cos_inc`` ``[T, S]`` and per-surface ``u_factor, shgc`` ``[S]``.
    """
    t_norm, _r_norm, a_norm = simple_glazing_normal_optics(u_factor, shgc)
    c = np.clip(cos_inc, 0.0, 1.0)
    # EnergyPlus single-layer uncoated glass angular polynomial (SolarShading.cc / WindowManager.cc)
    # T(cos_i) / T(0) = c * (a0 + c * (a1 + c * (a2 + c * (a3 + c * a4))))
    # Standard EnergyPlus clear-glass polynomial normalized to 1.0 at c=1:
    f_t = c * (
        3.5621
        + c * (-6.3941 + c * (6.2454 + c * (-2.4134)))
    )
    f_t = np.where(c > 0.0, np.clip(f_t, 0.0, 1.05), 0.0)
    f_a = c * (
        2.6177
        + c * (-3.1518 + c * (1.8944 + c * (-0.3603)))
    )
    f_a = np.where(c > 0.0, np.clip(f_a, 0.0, 1.15), 0.0)

    tau_beam = t_norm[None, :] * f_t
    abs_beam = a_norm[None, :] * f_a
    # Hemispherical diffuse integral of the polynomial (2 * integral_0^1 f(c)*c dc)
    # For clear glass, E+ hemispherical diffuse ratio is ~0.887 * T_norm, ~0.946 * A_norm
    tau_diff = np.broadcast_to((0.887 * t_norm)[None, :], cos_inc.shape)
    abs_diff = np.broadcast_to((0.946 * a_norm)[None, :], cos_inc.shape)
    return tau_beam, abs_beam, tau_diff, abs_diff
