from typing import Any

import numpy as np

from openubem.gpusim.physics.psychro import (
    KELVIN_CONV,
    STEFAN_BOLTZMANN,
    psy_cp_air_fn_w,
    psy_rho_air_fn_pb_tdb_w,
)

ATMOSPHERIC_TEMP_GRADIENT: float = 0.0065
EARTH_RADIUS: float = 6356766.0
WEATHER_TEMP_SENSOR_HEIGHT: float = 1.5
WEATHER_FILE_TEMP_MOD_COEFF: float = (
    ATMOSPHERIC_TEMP_GRADIENT
    * EARTH_RADIUS
    * WEATHER_TEMP_SENSOR_HEIGHT
    / (EARTH_RADIUS + WEATHER_TEMP_SENSOR_HEIGHT)
)
ROUGHNESS_MULTIPLIERS: tuple[float, ...] = (2.17, 1.67, 1.52, 1.13, 1.11, 1.0)
ONE_THIRD: float = 1.0 / 3.0
POW_5_25: float = 0.56 * (1.0e5**0.25)
POW_11_25: float = 0.56 * (1.0e11**0.25)
POW_11_2: float = 0.58 * (1.0e11**0.2)


def out_dry_bulb_temp_at(
    site_dry_bulb: Any,
    centroid_z: Any,
    xp: Any = np,
) -> Any:
    """DataEnvironment.cc::OutDryBulbTempAt"""
    base_temp = site_dry_bulb + WEATHER_FILE_TEMP_MOD_COEFF
    z_pos = xp.maximum(centroid_z, 0.0)
    lapse = ATMOSPHERIC_TEMP_GRADIENT * EARTH_RADIUS * z_pos / (EARTH_RADIUS + z_pos)
    return xp.where(centroid_z <= 0.0, base_temp, base_temp - lapse)


def calc_ashrae_tarp_natural(
    t_surf: Any,
    t_amb: Any,
    cos_tilt: Any,
    xp: Any = np,
) -> Any:
    """ConvectionCoefficients.cc::CalcASHRAETARPNatural"""
    delta_t = t_surf - t_amb
    abs_dt_cbrt = xp.power(xp.abs(delta_t), ONE_THIRD)
    abs_cos = xp.abs(cos_tilt)

    h_vert = 1.31 * abs_dt_cbrt
    h_unstable = 9.482 * abs_dt_cbrt / (7.238 - abs_cos)
    h_stable = 1.810 * abs_dt_cbrt / (1.382 + abs_cos)

    is_vert = (delta_t == 0.0) | (cos_tilt == 0.0)
    is_unstable = ((delta_t < 0.0) & (cos_tilt < 0.0)) | (
        (delta_t > 0.0) & (cos_tilt > 0.0)
    )
    return xp.where(is_vert, h_vert, xp.where(is_unstable, h_unstable, h_stable))


def calc_inside_convection_opaque(
    t_surf: Any,
    t_zone: Any,
    cos_tilt: Any,
    h_min: Any = 0.1,
    xp: Any = np,
) -> Any:
    """ConvectionCoefficients.cc::CalcASHRAEDetailedIntConvCoeff"""
    h_nat = calc_ashrae_tarp_natural(t_surf, t_zone, -cos_tilt, xp=xp)
    return xp.maximum(h_nat, h_min)


def calc_iso15099_window_int_conv_coeff(
    t_surf: Any,
    t_air: Any,
    hum_rat: Any,
    baro_press: Any,
    height: Any,
    tilt_deg: Any,
    sin_tilt: Any,
    h_min: Any = 0.1,
    xp: Any = np,
) -> Any:
    """ConvectionCoefficients.cc::CalcISO15099WindowIntConvCoeff"""
    t_surf_k = t_surf + KELVIN_CONV
    t_air_k = t_air + KELVIN_CONV
    delta_t = t_surf - t_air

    out_of_range = (
        (t_air_k < 200.0) | (t_air_k > 400.0) | (t_surf_k < 180.0) | (t_surf_k > 450.0)
    )

    t_film_k = t_air_k + 0.25 * (t_surf_k - t_air_k)
    t_film_c = t_film_k - KELVIN_CONV

    rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_film_c, hum_rat, xp=xp)
    lam = 2.873e-3 + 7.76e-5 * t_film_k
    mu = 3.723e-6 + 4.94e-8 * t_film_k
    cp = psy_cp_air_fn_w(hum_rat, xp=xp)

    eff_tilt = xp.where(delta_t > 0.0, 180.0 - tilt_deg, tilt_deg)
    safe_h = xp.maximum(height, 1.0e-6)
    safe_sin = xp.maximum(sin_tilt, 1.0e-12)

    ra_h = (
        (rho * rho)
        * (safe_h * safe_h * safe_h)
        * 9.81
        * cp
        * xp.abs(t_surf_k - t_air_k)
        / (t_film_k * mu * lam)
    )

    nu_a = 0.13 * xp.power(ra_h, ONE_THIRD)

    clamped_tilt_b = xp.clip(eff_tilt, 15.0, 90.0)
    ra_cv = 2.5e5 * xp.power(xp.exp(0.72 * clamped_tilt_b) / safe_sin, 0.2)
    ra_h_sin = ra_h * safe_sin
    nu_b_lam = 0.56 * xp.power(ra_h_sin, 0.25)
    nu_b_turb = 0.13 * (
        xp.power(ra_h, ONE_THIRD) - xp.power(ra_cv, ONE_THIRD)
    ) + 0.56 * xp.power(ra_cv * safe_sin, 0.25)
    nu_b = xp.where(ra_h <= ra_cv, nu_b_lam, nu_b_turb)

    nu_c = xp.where(
        ra_h_sin < 1.0e5,
        POW_5_25,
        xp.where(ra_h_sin >= 1.0e11, POW_11_25, 0.56 * xp.power(ra_h_sin, 0.25)),
    )

    nu_d = xp.where(ra_h > 1.0e11, POW_11_2, 0.58 * xp.power(ra_h, 0.2))

    nu_int = xp.where(
        eff_tilt < 15.0,
        nu_a,
        xp.where(eff_tilt <= 90.0, nu_b, xp.where(eff_tilt <= 179.0, nu_c, nu_d)),
    )

    h_val = xp.where(out_of_range, h_min, nu_int * lam / safe_h)
    return xp.maximum(h_val, h_min)


def calc_outside_convection_doe2(
    t_surf: Any,
    t_air: Any,
    cos_tilt: Any,
    wind_speed: Any = 0.0,
    roughness_mult: Any = 1.0,
    is_windward: Any = True,
    xp: Any = np,
) -> Any:
    """ConvectionCoefficients.cc::InitExteriorConvectionCoeff"""
    t_surf_k = t_surf + KELVIN_CONV
    t_air_k = t_air + KELVIN_CONV
    h_nat = calc_ashrae_tarp_natural(t_surf_k, t_air_k, cos_tilt, xp=xp)
    hf_windward = 3.26 * xp.power(wind_speed, 0.89)
    hf_leeward = 3.55 * xp.power(wind_speed, 0.617)
    hf_smooth = xp.where(is_windward, hf_windward, hf_leeward)
    hc_smooth = xp.sqrt(h_nat * h_nat + hf_smooth * hf_smooth)
    h_forced = roughness_mult * (hc_smooth - h_nat)
    return h_nat + h_forced


def calc_outside_rad_coeffs(
    t_surf: Any,
    t_air: Any,
    t_sky: Any,
    eps_out: Any,
    vf_sky_ir: Any,
    vf_ground_ir: Any,
    air_sky_split: Any,
    xp: Any = np,
) -> tuple[Any, Any, Any]:
    """ConvectionCoefficients.cc::InitExteriorConvectionCoeff"""
    ts_k = t_surf + KELVIN_CONV
    ta_k = t_air + KELVIN_CONV
    tsky_k = t_sky + KELVIN_CONV

    sky_factor = (ts_k * ts_k + tsky_k * tsky_k) * (ts_k + tsky_k)
    air_factor = (ts_k * ts_k + ta_k * ta_k) * (ts_k + ta_k)

    h_sky = xp.where(
        ts_k == tsky_k,
        0.0,
        STEFAN_BOLTZMANN * eps_out * vf_sky_ir * air_sky_split * sky_factor,
    )
    h_ground = xp.where(
        ts_k == ta_k,
        0.0,
        STEFAN_BOLTZMANN * eps_out * vf_ground_ir * air_factor,
    )
    h_air = xp.where(
        ts_k == ta_k,
        0.0,
        STEFAN_BOLTZMANN * eps_out * vf_sky_ir * (1.0 - air_sky_split) * air_factor,
    )
    return h_sky, h_ground, h_air
