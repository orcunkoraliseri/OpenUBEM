//! Generic `SimFloat` (f64 CPU reference & f32 GPU twin) EnergyPlus physics helpers.

use crate::float_trait::SimFloat;

pub const KELVIN_CONV: f64 = 273.15;
pub const TRIPLE_POINT_WATER_K: f64 = 273.16;
pub const STEFAN_BOLTZMANN: f64 = 5.6697e-8;
const ATMOSPHERIC_TEMP_GRADIENT: f64 = 0.0065;
const EARTH_RADIUS: f64 = 6356766.0;
const WEATHER_TEMP_SENSOR_HEIGHT: f64 = 1.5;
const WEATHER_FILE_TEMP_MOD_COEFF: f64 =
    ATMOSPHERIC_TEMP_GRADIENT * EARTH_RADIUS * WEATHER_TEMP_SENSOR_HEIGHT
        / (EARTH_RADIUS + WEATHER_TEMP_SENSOR_HEIGHT);

#[inline(always)]
pub fn psy_rho_air_fn_pb_tdb_w<F: SimFloat>(pb: F, tdb: F, dw: F) -> F {
    let w = dw.max(F::lit(1.0e-5));
    pb / (F::lit(287.0) * (tdb + F::lit(KELVIN_CONV)) * (F::lit(1.0) + F::lit(1.6077687) * w))
}

#[inline(always)]
pub fn psy_cp_air_fn_w<F: SimFloat>(dw: F) -> F {
    let w = dw.max(F::lit(1.0e-5));
    F::lit(1.00484e3) + w * F::lit(1.85895e3)
}

#[inline(always)]
pub fn psy_h_fn_tdb_w<F: SimFloat>(tdb: F, dw: F) -> F {
    let w = dw.max(F::lit(1.0e-5));
    F::lit(1.00484e3) * tdb + w * (F::lit(2.50094e6) + F::lit(1.85895e3) * tdb)
}

#[inline]
pub fn psy_psat_fn_temp<F: SimFloat>(temp_c: F) -> F {
    let tkel = temp_c.to_f64_lossless() + KELVIN_CONV;
    if tkel < 173.15 {
        return F::lit(0.001405102123874164);
    }
    if tkel > 473.15 {
        return F::lit(1555073.745636215);
    }
    let tk = tkel.clamp(173.15, 473.15);
    let log_t = tk.ln();
    let exp_val = if tkel < TRIPLE_POINT_WATER_K {
        -5674.5359 / tk
            + 6.3925247
            + tk * (-0.9677843e-2 + tk * (0.62215701e-6 + tk * (0.20747825e-8 - 0.9484024e-12 * tk)))
            + 4.1635019 * log_t
    } else {
        -5800.2206 / tk
            + 1.3914993
            + tk * (-0.048640239 + tk * (0.41764768e-4 - 0.14452093e-7 * tk))
            + 6.5459673 * log_t
    };
    F::lit(exp_val.exp())
}

#[inline(always)]
pub fn psy_w_fn_tdb_rh_pb<F: SimFloat>(tdb: F, rh: F, pb: F) -> F {
    let pdew = rh * psy_psat_fn_temp(tdb);
    let w = pdew * F::lit(0.62198) / (pb - pdew).max(F::lit(1000.0));
    w.max(F::lit(1.0e-5))
}

#[inline(always)]
pub fn out_dry_bulb_temp_at<F: SimFloat>(site_db: F, centroid_z: F) -> F {
    let base = site_db + F::lit(WEATHER_FILE_TEMP_MOD_COEFF);
    if centroid_z <= F::lit(0.0) {
        return base;
    }
    let er = F::lit(EARTH_RADIUS);
    let lapse = F::lit(ATMOSPHERIC_TEMP_GRADIENT) * er * centroid_z / (er + centroid_z);
    base - lapse
}

#[inline(always)]
pub fn calc_ashrae_tarp_natural<F: SimFloat>(t_surf: F, t_amb: F, cos_tilt: F) -> F {
    let dt = t_surf - t_amb;
    let abs_dt_cbrt = dt.abs().powf(F::lit(1.0 / 3.0));
    if dt == F::lit(0.0) || cos_tilt == F::lit(0.0) {
        return F::lit(1.31) * abs_dt_cbrt;
    }
    let abs_cos = cos_tilt.abs();
    let is_unstable = (dt < F::lit(0.0) && cos_tilt < F::lit(0.0))
        || (dt > F::lit(0.0) && cos_tilt > F::lit(0.0));
    if is_unstable {
        F::lit(9.482) * abs_dt_cbrt / (F::lit(7.238) - abs_cos)
    } else {
        F::lit(1.810) * abs_dt_cbrt / (F::lit(1.382) + abs_cos)
    }
}

#[inline(always)]
pub fn calc_inside_convection_opaque<F: SimFloat>(
    t_surf: F,
    t_zone: F,
    cos_tilt: F,
    h_min: F,
) -> F {
    calc_ashrae_tarp_natural(t_surf, t_zone, -cos_tilt).max(h_min)
}

#[inline]
pub fn calc_iso15099_window_int_conv_coeff<F: SimFloat>(
    t_surf: F,
    t_air: F,
    hum_rat: F,
    baro_press: F,
    height: F,
    tilt_deg: F,
    sin_tilt: F,
    h_min: F,
) -> F {
    let t_surf_k = t_surf + F::lit(KELVIN_CONV);
    let t_air_k = t_air + F::lit(KELVIN_CONV);
    if t_air_k < F::lit(200.0)
        || t_air_k > F::lit(400.0)
        || t_surf_k < F::lit(180.0)
        || t_surf_k > F::lit(450.0)
    {
        return h_min;
    }
    let delta_t = t_surf - t_air;
    let t_film_k = t_air_k + F::lit(0.25) * (t_surf_k - t_air_k);
    let t_film_c = t_film_k - F::lit(KELVIN_CONV);
    let rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_film_c, hum_rat);
    let lam = F::lit(2.873e-3) + F::lit(7.76e-5) * t_film_k;
    let mu = F::lit(3.723e-6) + F::lit(4.94e-8) * t_film_k;
    let cp = psy_cp_air_fn_w(hum_rat);

    let eff_tilt = if delta_t > F::lit(0.0) {
        F::lit(180.0) - tilt_deg
    } else {
        tilt_deg
    };
    let safe_h = height.max(F::lit(1.0e-6));
    let safe_sin = sin_tilt.max(F::lit(1.0e-12));
    let ra_h = (rho * rho)
        * (safe_h * safe_h * safe_h)
        * F::lit(9.81)
        * cp
        * (t_surf_k - t_air_k).abs()
        / (t_film_k * mu * lam);

    let nu_int = if eff_tilt < F::lit(15.0) {
        F::lit(0.13) * ra_h.powf(F::lit(1.0 / 3.0))
    } else if eff_tilt <= F::lit(90.0) {
        let clamped_b = eff_tilt.max(F::lit(15.0)).min(F::lit(90.0));
        let ra_cv = F::lit(2.5e5) * ((F::lit(0.72) * clamped_b).exp() / safe_sin).powf(F::lit(0.2));
        let ra_h_sin = ra_h * safe_sin;
        if ra_h <= ra_cv {
            F::lit(0.56) * ra_h_sin.powf(F::lit(0.25))
        } else {
            F::lit(0.13) * (ra_h.powf(F::lit(1.0 / 3.0)) - ra_cv.powf(F::lit(1.0 / 3.0)))
                + F::lit(0.56) * (ra_cv * safe_sin).powf(F::lit(0.25))
        }
    } else if eff_tilt <= F::lit(179.0) {
        let ra_h_sin = ra_h * safe_sin;
        if ra_h_sin < F::lit(1.0e5) {
            F::lit(0.56 * 1.0e5_f64.powf(0.25))
        } else if ra_h_sin >= F::lit(1.0e11) {
            F::lit(0.56 * 1.0e11_f64.powf(0.25))
        } else {
            F::lit(0.56) * ra_h_sin.powf(F::lit(0.25))
        }
    } else if ra_h > F::lit(1.0e11) {
        F::lit(0.58 * 1.0e11_f64.powf(0.2))
    } else {
        F::lit(0.58) * ra_h.powf(F::lit(0.2))
    };

    (nu_int * lam / safe_h).max(h_min)
}

#[inline(always)]
pub fn calc_outside_convection_doe2<F: SimFloat>(t_surf: F, t_air: F, cos_tilt: F) -> F {
    let t_surf_k = t_surf + F::lit(KELVIN_CONV);
    let t_air_k = t_air + F::lit(KELVIN_CONV);
    calc_ashrae_tarp_natural(t_surf_k, t_air_k, cos_tilt)
}

#[inline(always)]
pub fn calc_outside_rad_coeffs<F: SimFloat>(
    t_surf: F,
    t_air: F,
    t_sky: F,
    eps_out: F,
    vf_sky_ir: F,
    vf_ground_ir: F,
    air_sky_split: F,
) -> (F, F, F) {
    let ts_k = t_surf + F::lit(KELVIN_CONV);
    let ta_k = t_air + F::lit(KELVIN_CONV);
    let tsky_k = t_sky + F::lit(KELVIN_CONV);
    let sb = F::lit(STEFAN_BOLTZMANN);

    let h_sky = if ts_k == tsky_k {
        F::lit(0.0)
    } else {
        let sf = (ts_k * ts_k + tsky_k * tsky_k) * (ts_k + tsky_k);
        sb * eps_out * vf_sky_ir * air_sky_split * sf
    };
    let (h_grd, h_air) = if ts_k == ta_k {
        (F::lit(0.0), F::lit(0.0))
    } else {
        let af = (ts_k * ts_k + ta_k * ta_k) * (ts_k + ta_k);
        (
            sb * eps_out * vf_ground_ir * af,
            sb * eps_out * vf_sky_ir * (F::lit(1.0) - air_sky_split) * af,
        )
    };
    (h_sky, h_grd, h_air)
}

#[inline(always)]
pub fn simple_glazing_layer_conductance<F: SimFloat>(u_factor: F) -> F {
    let su = u_factor.max(F::lit(1.0e-6));
    let r_iw = if su < F::lit(5.85) {
        F::lit(1.0) / (F::lit(0.359073) * su.ln() + F::lit(6.949915))
    } else {
        F::lit(1.0) / (F::lit(1.788041) * su - F::lit(2.886625))
    };
    let r_ow = F::lit(1.0) / (F::lit(0.025342) * su + F::lit(29.163853));
    let r_lw = ((F::lit(1.0) / su) - r_iw - r_ow).max(F::lit(0.001));
    F::lit(1.0) / r_lw
}
