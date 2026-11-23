#ifndef GPUSIM_GENERAL_COMMON_H
#define GPUSIM_GENERAL_COMMON_H

#ifdef GPUSIM_HOST
#include <math.h>
#define GPUSIM_FN static inline
#define GPUSIM_GLOBAL
#define GPUSIM_GLOBAL_CONST const
#define GPUSIM_POW powf
#define GPUSIM_EXP expf
#define GPUSIM_LOG logf
#define GPUSIM_SQRT sqrtf
#define GPUSIM_FABS fabsf
#define GPUSIM_FMAX fmaxf
#define GPUSIM_FMIN fminf
#elif defined(__CUDACC__)
#define GPUSIM_FN __device__ static inline
#define GPUSIM_GLOBAL
#define GPUSIM_GLOBAL_CONST const
#define GPUSIM_POW powf
#define GPUSIM_EXP expf
#define GPUSIM_LOG logf
#define GPUSIM_SQRT sqrtf
#define GPUSIM_FABS fabsf
#define GPUSIM_FMAX fmaxf
#define GPUSIM_FMIN fminf
#elif defined(__METAL_VERSION__)
#include <metal_stdlib>
using namespace metal;
#define GPUSIM_FN inline
#define GPUSIM_GLOBAL device
#define GPUSIM_GLOBAL_CONST constant
#define GPUSIM_POW pow
#define GPUSIM_EXP exp
#define GPUSIM_LOG log
#define GPUSIM_SQRT sqrt
#define GPUSIM_FABS fabs
#define GPUSIM_FMAX fmax
#define GPUSIM_FMIN fmin
#endif

#define GEN_MAX_MODES 12
#define GEN_KELVIN 273.15f
#define GEN_SIGMA 5.6697e-8f
#define GEN_ITER_DAMP 5.0f
#define GEN_MAX_ITERS 500
#define GEN_REEVAL_CONV 30
#define GEN_MAX_DEL_T 0.002f
#define GEN_WIN_MAX_ITER 100
#define GEN_WIN_ERR_TOL 0.02f
#define GEN_MAX_ZONE_TEMP_DIFF 0.3f
#define GEN_MIN_SYS_HR (1.0f / 60.0f)
#define GEN_WARMUP_MIN_LOAD 100.0f
#define GEN_LAPSE_MOD (0.0065f * 6356766.0f * 1.5f / (6356766.0f + 1.5f))

#define BOUND_OSC 0
#define BOUND_OUTDOORS 1
#define BOUND_INTMASS 2
#define BOUND_WINDOW 3
#define BOUND_DOOR 4
#define BOUND_GROUND 5
#define BOUND_ADIABATIC 6
#define BOUND_SURFACE 7

#define SURF_WALL 0
#define SURF_FLOOR 1
#define SURF_ROOF 2
#define SURF_WINDOW 3
#define SURF_DOOR 4
#define SURF_INTMASS 5

GPUSIM_FN float gen_psy_cp_air(float w) {
    float wc = GPUSIM_FMAX(w, 1.0e-5f);
    return 1004.84f + wc * 1858.95f;
}

GPUSIM_FN float gen_psy_rho_air(float pb, float tdb, float w) {
    float wc = GPUSIM_FMAX(w, 1.0e-5f);
    return pb / (287.0f * (tdb + GEN_KELVIN) * (1.0f + 1.6077687f * wc));
}

GPUSIM_FN float gen_out_dry_bulb_at(float t_site, float z) {
    float base = t_site + GEN_LAPSE_MOD;
    if (z <= 0.0f) return base;
    return base - 0.0065f * 6356766.0f * z / (6356766.0f + z);
}

GPUSIM_FN float gen_wind_speed_at(float ws_site, float z, int terrain_idx) {
    if (z <= 0.0f || ws_site <= 0.0f) return 0.0f;
    float delta = 270.0f;
    float alpha = 0.14f;
    if (terrain_idx == 1) { delta = 370.0f; alpha = 0.22f; }
    else if (terrain_idx == 2) { delta = 460.0f; alpha = 0.33f; }
    else if (terrain_idx == 3) { delta = 210.0f; alpha = 0.10f; }
    return ws_site * 1.5861734f * GPUSIM_POW(z / delta, alpha);
}

GPUSIM_FN int gen_is_windward(float az_deg, float wind_dir_deg) {
    float diff = GPUSIM_FABS(az_deg - wind_dir_deg);
    if (diff > 180.0f) diff = 360.0f - diff;
    return (diff <= 100.0f) ? 1 : 0;
}

GPUSIM_FN float gen_tarp_natural(float t_surf, float t_amb, float cos_tilt) {
    float dt = t_surf - t_amb;
    float adt = GPUSIM_FABS(dt);
    if (adt <= 1.0e-12f) return 0.0f;
    float cbrt_dt = GPUSIM_POW(adt, 1.0f / 3.0f);
    if (cos_tilt == 0.0f) return 1.31f * cbrt_dt;
    float acos_t = GPUSIM_FABS(cos_tilt);
    int unstable = ((dt < 0.0f && cos_tilt < 0.0f) || (dt > 0.0f && cos_tilt > 0.0f));
    if (unstable) return 9.482f * cbrt_dt / (7.238f - acos_t);
    return 1.810f * cbrt_dt / (1.382f + acos_t);
}

GPUSIM_FN float gen_inside_conv_opaque(float t_surf, float t_zone, float cos_tilt, float h_min) {
    float h = gen_tarp_natural(t_surf, t_zone, -cos_tilt);
    return GPUSIM_FMAX(h, h_min);
}

GPUSIM_FN float gen_outside_conv_doe2(
    float t_surf, float t_air, float cos_tilt,
    float v_loc, float rough_mult, int windward
) {
    float h_nat = gen_tarp_natural(t_surf, t_air, cos_tilt);
    if (v_loc <= 1.0e-7f) return h_nat;
    float hf_s = windward ? (3.26f * GPUSIM_POW(v_loc, 0.89f))
                          : (3.55f * GPUSIM_POW(v_loc, 0.617f));
    float hc_s = GPUSIM_SQRT(h_nat * h_nat + hf_s * hf_s);
    return h_nat + rough_mult * (hc_s - h_nat);
}

GPUSIM_FN float gen_iso15099_win_hin(
    float t_surf, float t_air, float w, float pb,
    float height, float tilt_deg, float sin_tilt, float h_min
) {
    float ts_k = t_surf + GEN_KELVIN;
    float ta_k = t_air + GEN_KELVIN;
    if (ta_k < 200.0f || ta_k > 400.0f || ts_k < 180.0f || ts_k > 450.0f) return h_min;
    float dt = t_surf - t_air;
    float tf_k = ta_k + 0.25f * (ts_k - ta_k);
    float rho = gen_psy_rho_air(pb, tf_k - GEN_KELVIN, w);
    float lam = 2.873e-3f + 7.76e-5f * tf_k;
    float mu = 3.723e-6f + 4.94e-8f * tf_k;
    float cp = gen_psy_cp_air(w);
    float eff_tilt = (dt > 0.0f) ? (180.0f - tilt_deg) : tilt_deg;
    float sh = GPUSIM_FMAX(height, 1.0e-6f);
    float ssin = GPUSIM_FMAX(sin_tilt, 1.0e-12f);
    float ra_h = (rho * rho) * (sh * sh * sh) * 9.81f * cp * GPUSIM_FABS(ts_k - ta_k) / (tf_k * mu * lam);
    float nu_int;
    if (eff_tilt < 15.0f) {
        nu_int = 0.13f * GPUSIM_POW(ra_h, 1.0f / 3.0f);
    } else if (eff_tilt <= 90.0f) {
        float ct = GPUSIM_FMIN(GPUSIM_FMAX(eff_tilt, 15.0f), 90.0f);
        float ra_cv = 2.5e5f * GPUSIM_POW(GPUSIM_EXP(0.72f * ct) / ssin, 0.2f);
        if (ra_h <= ra_cv) {
            nu_int = 0.56f * GPUSIM_POW(ra_h * ssin, 0.25f);
        } else {
            nu_int = 0.13f * (GPUSIM_POW(ra_h, 1.0f / 3.0f) - GPUSIM_POW(ra_cv, 1.0f / 3.0f))
                   + 0.56f * GPUSIM_POW(ra_cv * ssin, 0.25f);
        }
    } else if (eff_tilt <= 179.0f) {
        float rhs = ra_h * ssin;
        if (rhs < 1.0e5f) nu_int = 0.56f * GPUSIM_POW(1.0e5f, 0.25f);
        else if (rhs >= 1.0e11f) nu_int = 0.56f * GPUSIM_POW(1.0e11f, 0.25f);
        else nu_int = 0.56f * GPUSIM_POW(rhs, 0.25f);
    } else {
        nu_int = (ra_h > 1.0e11f) ? (0.58f * GPUSIM_POW(1.0e11f, 0.2f))
                                  : (0.58f * GPUSIM_POW(ra_h, 0.2f));
    }
    return GPUSIM_FMAX(nu_int * lam / sh, h_min);
}

GPUSIM_FN void gen_outside_rad_coeffs(
    float t_surf, float t_air, float t_sky,
    float eps_out, float vf_sky_ir, float vf_gnd_ir, float split,
    float *h_sky, float *h_gnd, float *h_air
) {
    float ts = t_surf + GEN_KELVIN;
    float ta = t_air + GEN_KELVIN;
    float tk = t_sky + GEN_KELVIN;
    float sf = (ts * ts + tk * tk) * (ts + tk);
    float af = (ts * ts + ta * ta) * (ts + ta);
    *h_sky = (ts == tk) ? 0.0f : (GEN_SIGMA * eps_out * vf_sky_ir * split * sf);
    *h_gnd = (ts == ta) ? 0.0f : (GEN_SIGMA * eps_out * vf_gnd_ir * af);
    *h_air = (ts == ta) ? 0.0f : (GEN_SIGMA * eps_out * vf_sky_ir * (1.0f - split) * af);
}

GPUSIM_FN void gen_solve_simple_window(
    float t_in_c, float t_out_c, float t_sky_c, float w, float pb,
    float h_out, float rmir, float q_sol_abs, float scon,
    float eps_out, float eps_in, float vf_sky_ir, float vf_gnd_ir, float split,
    float height, float tilt_deg, float sin_tilt, float h_min,
    float *th1_io, float *th2_io, float *h_in_out
) {
    float ti_k = t_in_c + GEN_KELVIN;
    float to_k = t_out_c + GEN_KELVIN;
    float tk_k = t_sky_c + GEN_KELVIN;
    float eb_o = GEN_SIGMA * to_k * to_k * to_k * to_k;
    float eb_s = GEN_SIGMA * tk_k * tk_k * tk_k * tk_k;
    float out_ir = vf_sky_ir * (split * eb_s + (1.0f - split) * eb_o) + vf_gnd_ir * eb_o;
    float half_q = 0.5f * q_sol_abs;

    float th1 = *th1_io;
    float th2 = *th2_io;
    float h_in = 3.0f;

    for (int it = 0; it < GEN_WIN_MAX_ITER; ++it) {
        float hr1 = eps_out * GEN_SIGMA * th1 * th1 * th1;
        float hr2 = eps_in * GEN_SIGMA * th2 * th2 * th2;
        h_in = gen_iso15099_win_hin(th2 - GEN_KELVIN, t_in_c, w, pb, height, tilt_deg, sin_tilt, h_min);
        float a11 = hr1 + scon + h_out;
        float a22 = hr2 + scon + h_in;
        float b1 = out_ir * eps_out + h_out * to_k + half_q;
        float b2 = rmir * eps_in + h_in * ti_k + half_q;
        float det = a11 * a22 - scon * scon;
        if (GPUSIM_FABS(det) < 1.0e-12f) break;
        float s1 = (a22 * b1 + scon * b2) / det;
        float s2 = (scon * b1 + a11 * b2) / det;
        float w_old = ((it + 1) < (GEN_WIN_MAX_ITER / 4)) ? 0.5f : 0.75f;
        float n1 = w_old * th1 + (1.0f - w_old) * s1;
        float n2 = w_old * th2 + (1.0f - w_old) * s2;
        float err = 0.5f * (GPUSIM_FABS(n1 - th1) + GPUSIM_FABS(n2 - th2));
        th1 = n1;
        th2 = n2;
        if (err <= GEN_WIN_ERR_TOL) break;
    }
    *th1_io = th1;
    *th2_io = th2;
    *h_in_out = h_in;
}

GPUSIM_FN int gen_doy_to_month(int doy) {
    // doy in 0..364 -> month in 0..11
    if (doy < 31) return 0;
    if (doy < 59) return 1;
    if (doy < 90) return 2;
    if (doy < 120) return 3;
    if (doy < 151) return 4;
    if (doy < 181) return 5;
    if (doy < 212) return 6;
    if (doy < 243) return 7;
    if (doy < 273) return 8;
    if (doy < 304) return 9;
    if (doy < 334) return 10;
    return 11;
}

GPUSIM_FN void gen_down_interp_4(
    float dt_z_hr, float dt_s_hr,
    const float h[4], float out[4]
) {
    float r = dt_s_hr / dt_z_hr;
    out[0] = h[0];
    for (int k = 1; k <= 3; ++k) {
        float t = (float)k * r;
        int i0 = (int)t;
        if (i0 >= 3) { out[k] = h[3]; }
        else {
            float f = t - (float)i0;
            out[k] = h[i0] * (1.0f - f) + h[i0 + 1] * f;
        }
    }
}

GPUSIM_FN void gen_zone_air_step_1(
    float t_mat, float w_z, float pb, float vol, float dt_sec,
    const float xmat[4], const float w_prev[4],
    float sum_ha, float sum_hat, float mcpv, float vamfl, float mcptv,
    float q_gain_conv, float heat_sp, float cool_sp,
    float max_heat_sup_t, float min_cool_sup_t,
    int has_hvac, int has_cooling, float w_site,
    float *zt_new, float *w_new, float *sen_heat_w, float *tot_heat_w
) {
    float rho = gen_psy_rho_air(pb, t_mat, w_z);
    float cp = gen_psy_cp_air(w_z);
    float air_cap = rho * cp * vol / dt_sec;
    float air_hist = air_cap * (3.0f * xmat[0] - 1.5f * xmat[1] + (1.0f / 3.0f) * xmat[2]);
    float coeff_t = (11.0f / 6.0f) * air_cap + sum_ha + mcpv;
    float rhs_no_hvac = sum_hat + mcptv + q_gain_conv + air_hist;

    float m_sup = 0.0f;
    float t_sup = t_mat;
    float w_sup = w_z;
    float sh = 0.0f;
    float th = 0.0f;

    if (has_hvac) {
        float q_heat_req = coeff_t * heat_sp - rhs_no_hvac;
        float q_cool_req = coeff_t * cool_sp - rhs_no_hvac;
        if (q_heat_req > 1.0e-3f) {
            float dT_sup = GPUSIM_FMAX(max_heat_sup_t - t_mat, 0.5f);
            m_sup = q_heat_req / (cp * dT_sup);
            t_sup = max_heat_sup_t;
            sh = m_sup * cp * (t_sup - t_mat);
            th = sh;
        } else if (has_cooling && q_cool_req < -1.0e-3f) {
            float dT_sup = GPUSIM_FMAX(t_mat - min_cool_sup_t, 0.5f);
            m_sup = (-q_cool_req) / (cp * dT_sup);
            t_sup = min_cool_sup_t;
        }
    }

    float mcp_sys = m_sup * cp;
    *zt_new = (rhs_no_hvac + mcp_sys * t_sup) / GPUSIM_FMAX(coeff_t + mcp_sys, 1.0e-12f);

    float m_air = rho * vol / dt_sec;
    float w_hist = m_air * (3.0f * w_prev[0] - 1.5f * w_prev[1] + (1.0f / 3.0f) * w_prev[2]);
    *w_new = (vamfl * w_site + m_sup * w_sup + w_hist) / GPUSIM_FMAX((11.0f / 6.0f) * m_air + vamfl + m_sup, 1.0e-12f);
    *sen_heat_w = sh;
    *tot_heat_w = th;
}

GPUSIM_FN void gen_step_building(
    int b,
    int step,
    int is_warmup,
    int begin_envrn,
    int sph,
    int n_weather_steps,
    int has_shading,
    int record_zone_temp,
    // Building metadata
    GPUSIM_GLOBAL_CONST int *site_idx,
    GPUSIM_GLOBAL_CONST int *terrain_idx,
    GPUSIM_GLOBAL_CONST int *zone_offset,
    GPUSIM_GLOBAL_CONST int *surf_offset,
    GPUSIM_GLOBAL_CONST float *site_ground_temp,
    GPUSIM_GLOBAL_CONST float *h_conv_min,
    // Zone metadata
    GPUSIM_GLOBAL_CONST int *zone_surf_offset,
    GPUSIM_GLOBAL_CONST int *zone_sf_offset,
    GPUSIM_GLOBAL_CONST float *zone_volume,
    GPUSIM_GLOBAL_CONST float *zone_centroid_z,
    GPUSIM_GLOBAL_CONST int *zone_has_hvac,
    GPUSIM_GLOBAL_CONST int *zone_has_cooling,
    GPUSIM_GLOBAL_CONST float *zone_max_heat_sup_t,
    GPUSIM_GLOBAL_CONST float *zone_min_cool_sup_t,
    GPUSIM_GLOBAL_CONST float *zone_heat_sp_hr,
    GPUSIM_GLOBAL_CONST float *zone_cool_sp_hr,
    GPUSIM_GLOBAL_CONST float *zone_gain_conv_hr,
    GPUSIM_GLOBAL_CONST float *zone_gain_rad_hr,
    GPUSIM_GLOBAL_CONST float *zone_vent_flow_hr,
    GPUSIM_GLOBAL_CONST float *zone_total_op_aa,
    GPUSIM_GLOBAL_CONST float *zone_floor_area_sw,
    GPUSIM_GLOBAL_CONST float *zone_floor_alpha_eff,
    GPUSIM_GLOBAL_CONST float *zone_total_eps_area,
    // Surface metadata
    GPUSIM_GLOBAL_CONST int *surf_class,
    GPUSIM_GLOBAL_CONST int *surf_boundary,
    GPUSIM_GLOBAL_CONST int *surf_partner_idx,
    GPUSIM_GLOBAL_CONST float *surf_area,
    GPUSIM_GLOBAL_CONST float *surf_tilt_deg,
    GPUSIM_GLOBAL_CONST float *surf_cos_tilt,
    GPUSIM_GLOBAL_CONST float *surf_sin_tilt,
    GPUSIM_GLOBAL_CONST float *surf_azimuth_deg,
    GPUSIM_GLOBAL_CONST float *surf_nx,
    GPUSIM_GLOBAL_CONST float *surf_ny,
    GPUSIM_GLOBAL_CONST float *surf_nz,
    GPUSIM_GLOBAL_CONST float *surf_centroid_z,
    GPUSIM_GLOBAL_CONST float *surf_height,
    GPUSIM_GLOBAL_CONST float *surf_roughness_mult,
    GPUSIM_GLOBAL_CONST int *surf_sun_exposed,
    GPUSIM_GLOBAL_CONST int *surf_wind_exposed,
    GPUSIM_GLOBAL_CONST float *surf_solar_abs_out,
    GPUSIM_GLOBAL_CONST float *surf_solar_abs_in,
    GPUSIM_GLOBAL_CONST float *surf_eps_in,
    GPUSIM_GLOBAL_CONST float *surf_eps_out,
    GPUSIM_GLOBAL_CONST float *surf_vf_ground,
    GPUSIM_GLOBAL_CONST float *surf_vf_sky,
    GPUSIM_GLOBAL_CONST float *surf_vf_sky_ir,
    GPUSIM_GLOBAL_CONST float *surf_vf_ground_ir,
    GPUSIM_GLOBAL_CONST float *surf_air_sky_split,
    GPUSIM_GLOBAL_CONST float *surf_osc_c_const,
    GPUSIM_GLOBAL_CONST float *surf_osc_t_const,
    GPUSIM_GLOBAL_CONST float *surf_osc_c_out,
    GPUSIM_GLOBAL_CONST float *surf_osc_c_zone,
    GPUSIM_GLOBAL_CONST float *surf_scon,
    GPUSIM_GLOBAL_CONST float *surf_t_norm,
    GPUSIM_GLOBAL_CONST float *surf_a_norm,
    GPUSIM_GLOBAL_CONST float *surf_tau_diff,
    GPUSIM_GLOBAL_CONST float *surf_abs_diff,
    // Modal conduction
    GPUSIM_GLOBAL_CONST int *surf_n_modes,
    GPUSIM_GLOBAL_CONST float *surf_ctf_out0,
    GPUSIM_GLOBAL_CONST float *surf_ctf_cross0,
    GPUSIM_GLOBAL_CONST float *surf_ctf_in0,
    GPUSIM_GLOBAL_CONST float *surf_lag_oo,
    GPUSIM_GLOBAL_CONST float *surf_lag_oi,
    GPUSIM_GLOBAL_CONST float *surf_lag_io,
    GPUSIM_GLOBAL_CONST float *surf_lag_ii,
    GPUSIM_GLOBAL_CONST float *surf_m_decay,
    GPUSIM_GLOBAL_CONST float *surf_m_gno,
    GPUSIM_GLOBAL_CONST float *surf_m_gni,
    GPUSIM_GLOBAL_CONST float *surf_m_goo,
    GPUSIM_GLOBAL_CONST float *surf_m_goi,
    GPUSIM_GLOBAL_CONST float *surf_m_co,
    GPUSIM_GLOBAL_CONST float *surf_m_ci,
    // ScriptF and Shading
    GPUSIM_GLOBAL_CONST float *script_f_sigma,
    GPUSIM_GLOBAL_CONST float *surf_dif_sky_shdg,
    GPUSIM_GLOBAL_CONST unsigned char *surf_sunlit_u8,
    // Weather [N_sites * n_weather_steps]
    GPUSIM_GLOBAL_CONST float *w_t_db,
    GPUSIM_GLOBAL_CONST float *w_hum_rat,
    GPUSIM_GLOBAL_CONST float *w_pb,
    GPUSIM_GLOBAL_CONST float *w_t_sky,
    GPUSIM_GLOBAL_CONST float *w_ws,
    GPUSIM_GLOBAL_CONST float *w_wd,
    GPUSIM_GLOBAL_CONST float *w_wb,
    GPUSIM_GLOBAL_CONST float *w_rain,
    GPUSIM_GLOBAL_CONST float *w_dni,
    GPUSIM_GLOBAL_CONST float *w_dhi,
    GPUSIM_GLOBAL_CONST float *w_sx,
    GPUSIM_GLOBAL_CONST float *w_sy,
    GPUSIM_GLOBAL_CONST float *w_sz,
    GPUSIM_GLOBAL_CONST float *w_f1,
    GPUSIM_GLOBAL_CONST float *w_f2,
    // Mutable state
    GPUSIM_GLOBAL float *t_surf_in,
    GPUSIM_GLOBAL float *t_surf_out,
    GPUSIM_GLOBAL float *t_surf_in_prev,
    GPUSIM_GLOBAL float *t_surf_out_prev,
    GPUSIM_GLOBAL float *t_surf_in_old,
    GPUSIM_GLOBAL float *theta1_win,
    GPUSIM_GLOBAL float *theta2_win,
    GPUSIM_GLOBAL float *h_conv_in,
    GPUSIM_GLOBAL float *ctf_const_in,
    GPUSIM_GLOBAL float *ctf_const_out,
    GPUSIM_GLOBAL float *q_sol_out,
    GPUSIM_GLOBAL float *q_sw_in,
    GPUSIM_GLOBAL float *q_sol_win,
    GPUSIM_GLOBAL float *modal_z,
    GPUSIM_GLOBAL float *t_mat,
    GPUSIM_GLOBAL float *xmat,
    GPUSIM_GLOBAL float *dsxmat,
    GPUSIM_GLOBAL float *w_zone,
    GPUSIM_GLOBAL float *w_zone_avg,
    GPUSIM_GLOBAL float *w_prev,
    GPUSIM_GLOBAL float *dsw_prev,
    GPUSIM_GLOBAL int *num_sys_last,
    // Outputs
    GPUSIM_GLOBAL float *hourly_heating_j,
    GPUSIM_GLOBAL float *zone_annual_kwh,
    GPUSIM_GLOBAL float *zone_temp_rec,
    float *day_max_t_io,
    float *day_min_t_io,
    float *day_max_h_io
) {
    int z0 = zone_offset[b];
    int z1 = zone_offset[b + 1];
    int s0_b = surf_offset[b];
    int s1_b = surf_offset[b + 1];
    int si = site_idx[b];
    int terr = terrain_idx[b];
    float h_min = h_conv_min[b];
    int w_off = si * n_weather_steps + step;

    float t_site = w_t_db[w_off];
    float w_site = w_hum_rat[w_off];
    float pb_site = w_pb[w_off];
    float t_sky_site = w_t_sky[w_off];
    float ws_site = w_ws[w_off];
    float wd_site = w_wd[w_off];
    float wb_site = w_wb[w_off];
    int is_rain = (w_rain[w_off] > 0.5f) ? 1 : 0;
    float dni = w_dni[w_off];
    float dhi = w_dhi[w_off];
    float sx = w_sx[w_off];
    float sy = w_sy[w_off];
    float sz = w_sz[w_off];
    float f1 = w_f1[w_off];
    float f2 = w_f2[w_off];

    int hr = step / sph;
    int doy = hr / 24;
    int month = gen_doy_to_month(doy);
    float t_gnd_m = site_ground_temp[b * 12 + month];
    float dt_zone_hr = 1.0f / (float)sph;
    float dt_zone_sec = 3600.0f / (float)sph;
    int limit_num_sys = (int)(dt_zone_hr / GEN_MIN_SYS_HR + 0.5f);
    if (limit_num_sys < 1) limit_num_sys = 1;

    float ghi = GPUSIM_FMAX(dni, 0.0f) * GPUSIM_FMAX(sz, 0.0f) + GPUSIM_FMAX(dhi, 0.0f);
    float b_den = GPUSIM_FMAX(0.08715574f, sz);

    // 1. Per-zone solar & interior radiant gains
    for (int z = z0; z < z1; ++z) {
        int zs0 = zone_surf_offset[z];
        int zs1 = zone_surf_offset[z + 1];
        float q_tb = 0.0f;
        float q_td = 0.0f;

        for (int s = zs0; s < zs1; ++s) {
            float qo = 0.0f;
            float qw = 0.0f;
            int bnd = surf_boundary[s];
            if (surf_sun_exposed[s] && sz > 0.0f) {
                float cos_i = sx * surf_nx[s] + sy * surf_ny[s] + sz * surf_nz[s];
                float cpos = (cos_i > 0.0f) ? cos_i : 0.0f;
                float sunlit = has_shading ? ((float)surf_sunlit_u8[s * 8760 + hr] * (1.0f / 255.0f)) : 1.0f;
                float ib = GPUSIM_FMAX(dni, 0.0f) * cpos * sunlit;
                float aniso = GPUSIM_FMAX(
                    0.0f,
                    (1.0f - f1) * surf_vf_sky[s] * surf_dif_sky_shdg[s]
                    + f1 * (cpos / b_den) * sunlit
                    + f2 * surf_sin_tilt[s]
                );
                float ids = GPUSIM_FMAX(dhi, 0.0f) * aniso;
                float idg = 0.2f * ghi * surf_vf_ground[s];
                if (bnd == BOUND_OUTDOORS || bnd == BOUND_DOOR) {
                    qo = (ib + ids + idg) * surf_solar_abs_out[s];
                } else if (bnd == BOUND_WINDOW) {
                    float f_t = 0.0f;
                    float f_a = 0.0f;
                    if (cpos > 0.0f) {
                        f_t = cpos * (3.5621f + cpos * (-6.3941f + cpos * (6.2454f - 2.4134f * cpos)));
                        f_t = GPUSIM_FMIN(1.05f, GPUSIM_FMAX(0.0f, f_t));
                        f_a = cpos * (2.6177f + cpos * (-3.1518f + cpos * (1.8944f - 0.3603f * cpos)));
                        f_a = GPUSIM_FMIN(1.15f, GPUSIM_FMAX(0.0f, f_a));
                    }
                    float tb = surf_t_norm[s] * f_t;
                    float ab = surf_a_norm[s] * f_a;
                    float td = surf_tau_diff[s];
                    float ad = surf_abs_diff[s];
                    qw = ib * ab + (ids + idg) * ad;
                    q_tb += ib * tb * surf_area[s];
                    q_td += (ids + idg) * td * surf_area[s];
                }
            }
            q_sol_out[s] = qo;
            q_sol_win[s] = qw;
        }

        float flr_a = zone_floor_area_sw[z];
        float flr_alpha = zone_floor_alpha_eff[z];
        float q_diff_pool = q_td + ((flr_a > 1.0e-6f) ? (1.0f - flr_alpha) * q_tb : q_tb);
        float q_diff_inc = q_diff_pool / GPUSIM_FMAX(zone_total_op_aa[z], 1.0e-12f);
        float q_rad_inc = zone_gain_rad_hr[z * 8760 + hr] / GPUSIM_FMAX(zone_total_eps_area[z], 1.0e-12f);

        for (int s = zs0; s < zs1; ++s) {
            int bnd = surf_boundary[s];
            if (bnd == BOUND_WINDOW) {
                q_sol_win[s] += q_diff_inc * surf_abs_diff[s];
                q_sw_in[s] = q_rad_inc * surf_eps_in[s]; // window interior rad gain
            } else {
                float q_beam_flr = (surf_class[s] == SURF_FLOOR && flr_a > 1.0e-6f)
                    ? (q_tb * surf_solar_abs_in[s] / flr_a) : 0.0f;
                q_sw_in[s] = q_beam_flr + q_diff_inc * surf_solar_abs_in[s] + q_rad_inc * surf_eps_in[s];
            }
        }
    }

    // 2. Modal history free-response & initial inside convection + outside surface temp
    for (int z = z0; z < z1; ++z) {
        int zs0 = zone_surf_offset[z];
        int zs1 = zone_surf_offset[z + 1];
        int n_sz = zs1 - zs0;
        int sf0 = zone_sf_offset[z];
        float tz = t_mat[z];
        float wz = w_zone_avg[z];

        for (int s = zs0; s < zs1; ++s) {
            int bnd = surf_boundary[s];
            if (bnd == BOUND_WINDOW) {
                h_conv_in[s] = gen_iso15099_win_hin(
                    t_surf_in[s], tz, wz, pb_site,
                    surf_height[s], surf_tilt_deg[s], surf_sin_tilt[s], h_min
                );
            } else {
                h_conv_in[s] = gen_inside_conv_opaque(t_surf_in[s], tz, surf_cos_tilt[s], h_min);
            }

            int nm = surf_n_modes[s];
            if (nm > 0) {
                float top = t_surf_out_prev[s];
                float tip = t_surf_in_prev[s];
                float co_s = surf_lag_oo[s] * top + surf_lag_oi[s] * tip;
                float ci_s = surf_lag_io[s] * top + surf_lag_ii[s] * tip;
                int mbase = s * GEN_MAX_MODES;
                for (int k = 0; k < nm; ++k) {
                    int mk = mbase + k;
                    float zf = surf_m_decay[mk] * modal_z[mk]
                             + surf_m_goo[mk] * top + surf_m_goi[mk] * tip;
                    co_s += surf_m_co[mk] * zf;
                    ci_s += surf_m_ci[mk] * zf;
                    modal_z[mk] = zf;
                }
                ctf_const_out[s] = co_s;
                ctf_const_in[s] = ci_s;
            } else {
                ctf_const_out[s] = 0.0f;
                ctf_const_in[s] = 0.0f;
            }
        }

        // Outside surface temps for zone z
        for (int li = 0; li < n_sz; ++li) {
            int s = zs0 + li;
            int bnd = surf_boundary[s];
            float t_out_air = gen_out_dry_bulb_at(t_site, surf_centroid_z[s]);
            if (bnd == BOUND_OSC) {
                t_surf_out[s] = surf_osc_c_zone[s] * tz
                              + surf_osc_c_out[s] * t_out_air
                              + surf_osc_c_const[s] * surf_osc_t_const[s];
            } else if (bnd == BOUND_GROUND) {
                t_surf_out[s] = t_gnd_m;
            } else if (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC) {
                t_surf_out[s] = t_surf_in[s];
            } else if (bnd == BOUND_SURFACE) {
                int p = surf_partner_idx[s];
                t_surf_out[s] = (p >= 0) ? t_surf_in[p] : t_surf_in[s];
            } else if (bnd == BOUND_OUTDOORS || bnd == BOUND_DOOR) {
                // Compute interior LWR for outside quick-balance
                float ti_k = t_surf_in[s] + GEN_KELVIN;
                float ti4 = ti_k * ti_k * ti_k * ti_k;
                float q_lw = 0.0f;
                int row_off = sf0 + li * n_sz;
                for (int lj = 0; lj < n_sz; ++lj) {
                    float tj_k = t_surf_in[zs0 + lj] + GEN_KELVIN;
                    float tj4 = tj_k * tj_k * tj_k * tj_k;
                    q_lw += script_f_sigma[row_off + lj] * (tj4 - ti4);
                }
                float v_loc = surf_wind_exposed[s] ? gen_wind_speed_at(ws_site, surf_centroid_z[s], terr) : 0.0f;
                int ww = surf_wind_exposed[s] ? gen_is_windward(surf_azimuth_deg[s], wd_site) : 1;
                float hc_ext = gen_outside_conv_doe2(
                    t_surf_out[s], t_out_air, surf_cos_tilt[s], v_loc, surf_roughness_mult[s], ww
                );
                float hsky, hgnd, hair;
                gen_outside_rad_coeffs(
                    t_surf_out[s], t_out_air, t_sky_site,
                    surf_eps_out[s], surf_vf_sky_ir[s], surf_vf_ground_ir[s], surf_air_sky_split[s],
                    &hsky, &hgnd, &hair
                );
                float c_o0 = surf_ctf_out0[s];
                float c_y0 = surf_ctf_cross0[s];
                float c_i0 = surf_ctf_in0[s];
                float ext_num = -ctf_const_out[s] + q_sol_out[s]
                              + (hc_ext + hair) * t_out_air + hsky * t_sky_site + hgnd * t_site;
                float ext_den = c_o0 + hc_ext + hair + hsky + hgnd;
                float num, den;
                if (c_y0 > 0.01f) {
                    float f_q = c_y0 / GPUSIM_FMAX(c_i0 + h_conv_in[s], 1.0e-12f);
                    num = ext_num + f_q * (ctf_const_in[s] + h_conv_in[s] * tz + q_lw + q_sw_in[s]);
                    den = ext_den - f_q * c_y0;
                } else {
                    num = ext_num + c_y0 * t_surf_in[s];
                    den = ext_den;
                }
                t_surf_out[s] = num / ((GPUSIM_FABS(den) < 1.0e-12f) ? 1.0f : den);
            }
        }
    }

    // 3. Coupled inside-surface iteration loop across all zones of building b
    for (int it = 0; it < GEN_MAX_ITERS; ++it) {
        for (int s = s0_b; s < s1_b; ++s) {
            t_surf_in_old[s] = t_surf_in[s];
        }
        // Update interzone Surface outside temps from partner inside temps
        for (int s = s0_b; s < s1_b; ++s) {
            if (surf_boundary[s] == BOUND_SURFACE) {
                int p = surf_partner_idx[s];
                if (p >= 0) t_surf_out[s] = t_surf_in_old[p];
            }
        }

        float max_del_t = 0.0f;
        for (int z = z0; z < z1; ++z) {
            int zs0 = zone_surf_offset[z];
            int zs1 = zone_surf_offset[z + 1];
            int n_sz = zs1 - zs0;
            int sf0 = zone_sf_offset[z];
            float tz = t_mat[z];
            float wz = w_zone_avg[z];

            for (int li = 0; li < n_sz; ++li) {
                int s = zs0 + li;
                int bnd = surf_boundary[s];

                float ti_k = t_surf_in_old[s] + GEN_KELVIN;
                float ti4 = ti_k * ti_k * ti_k * ti_k;
                float q_net_lw = 0.0f;
                int row_off = sf0 + li * n_sz;
                for (int lj = 0; lj < n_sz; ++lj) {
                    float tj_k = t_surf_in_old[zs0 + lj] + GEN_KELVIN;
                    float tj4 = tj_k * tj_k * tj_k * tj_k;
                    q_net_lw += script_f_sigma[row_off + lj] * (tj4 - ti4);
                }

                if (bnd == BOUND_WINDOW) {
                    if (it == 0) {
                        float t_out_air = gen_out_dry_bulb_at(t_site, surf_centroid_z[s]);
                        float v_loc = surf_wind_exposed[s] ? gen_wind_speed_at(ws_site, surf_centroid_z[s], terr) : 0.0f;
                        int ww = surf_wind_exposed[s] ? gen_is_windward(surf_azimuth_deg[s], wd_site) : 1;
                        float hc_ext = gen_outside_conv_doe2(
                            t_surf_out[s], t_out_air, surf_cos_tilt[s], v_loc, surf_roughness_mult[s], ww
                        );
                        float eps_i = GPUSIM_FMAX(surf_eps_in[s], 1.0e-6f);
                        float rmir = (q_net_lw + q_sw_in[s]) / eps_i + GEN_SIGMA * ti4;
                        float th1 = theta1_win[s];
                        float th2 = theta2_win[s];
                        if (begin_envrn) {
                            float hrad = 5.3f;
                            float r1 = 1.0f / (hc_ext + hrad);
                            float r2 = 1.0f / GPUSIM_FMAX(surf_scon[s], 1.0e-6f);
                            float r3 = 1.0f / (h_conv_in[s] + hrad);
                            float rt = r1 + r2 + r3;
                            float td = (tz - t_out_air);
                            if (GPUSIM_FABS(td) < 0.5f) td = 2.0f;
                            th1 = (r1 / rt) * td + (t_out_air + GEN_KELVIN);
                            th2 = ((r1 + r2) / rt) * td + (t_out_air + GEN_KELVIN);
                        }
                        float win_hin = h_conv_in[s];
                        gen_solve_simple_window(
                            tz, t_out_air, t_sky_site, wz, pb_site,
                            hc_ext, rmir, q_sol_win[s], surf_scon[s],
                            surf_eps_out[s], surf_eps_in[s],
                            surf_vf_sky_ir[s], surf_vf_ground_ir[s], surf_air_sky_split[s],
                            surf_height[s], surf_tilt_deg[s], surf_sin_tilt[s], h_min,
                            &th1, &th2, &win_hin
                        );
                        theta1_win[s] = th1;
                        theta2_win[s] = th2;
                        t_surf_out[s] = th1 - GEN_KELVIN;
                        t_surf_in[s] = th2 - GEN_KELVIN;
                        h_conv_in[s] = win_hin;
                    }
                } else {
                    if (it > 0 && (it % GEN_REEVAL_CONV == 0)) {
                        h_conv_in[s] = gen_inside_conv_opaque(t_surf_in_old[s], tz, surf_cos_tilt[s], h_min);
                    }
                    float hc = h_conv_in[s];
                    float ci0 = surf_ctf_in0[s];
                    float cy0 = surf_ctf_cross0[s];
                    float temp_term = ctf_const_in[s] + hc * tz + q_net_lw + q_sw_in[s];
                    int is_ad = (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC);
                    float num, den;
                    if (is_ad) {
                        num = temp_term + GEN_ITER_DAMP * t_surf_in_old[s];
                        den = ci0 - cy0 + hc + GEN_ITER_DAMP;
                    } else {
                        num = temp_term + GEN_ITER_DAMP * t_surf_in_old[s] + cy0 * t_surf_out[s];
                        den = ci0 + hc + GEN_ITER_DAMP;
                    }
                    float new_ti = num / ((GPUSIM_FABS(den) < 1.0e-12f) ? 1.0f : den);
                    t_surf_in[s] = new_ti;
                    float dt_s = GPUSIM_FABS(new_ti - t_surf_in_old[s]);
                    if (dt_s > max_del_t) max_del_t = dt_s;
                }
            }
        }
        if (max_del_t <= GEN_MAX_DEL_T) break;
    }

    // 4. Zone air balance & IdealLoads per zone
    float bldg_heat_j = 0.0f;
    float bldg_sen_w = 0.0f;
    for (int z = z0; z < z1; ++z) {
        int zs0 = zone_surf_offset[z];
        int zs1 = zone_surf_offset[z + 1];
        float sum_ha = 0.0f;
        float sum_hat = 0.0f;
        for (int s = zs0; s < zs1; ++s) {
            float ha = h_conv_in[s] * surf_area[s];
            sum_ha += ha;
            sum_hat += ha * t_surf_in[s];
        }

        float t_out_z = gen_out_dry_bulb_at(t_site, zone_centroid_z[z]);
        float v_flow = zone_vent_flow_hr[z * 8760 + hr];
        float rho_v = gen_psy_rho_air(pb_site, t_out_z, w_site);
        float cp_v = gen_psy_cp_air(w_site);
        float vamfl = v_flow * rho_v;
        float mcpv = vamfl * cp_v;
        float mcptv = mcpv * t_out_z;

        float q_gain_c = zone_gain_conv_hr[z * 8760 + hr];
        float heat_sp = zone_heat_sp_hr[z * 8760 + hr];
        float cool_sp = zone_cool_sp_hr[z * 8760 + hr];
        int has_hvac = zone_has_hvac[z];
        int has_cool = zone_has_cooling[z];
        float max_ht = zone_max_heat_sup_t[z];
        float min_ct = zone_min_cool_sup_t[z];
        float vol = zone_volume[z];

        float xm[4], wp[4];
        for (int k = 0; k < 4; ++k) { xm[k] = xmat[z * 4 + k]; wp[k] = w_prev[z * 4 + k]; }

        float zt_new, w_new, sh, th;
        gen_zone_air_step_1(
            t_mat[z], w_zone[z], pb_site, vol, dt_zone_sec,
            xm, wp, sum_ha, sum_hat, mcpv, vamfl, mcptv,
            q_gain_c, heat_sp, cool_sp, max_ht, min_ct, has_hvac, has_cool, w_site,
            &zt_new, &w_new, &sh, &th
        );

        float ztav = zt_new;
        float w_avg = w_new;
        float heat_j = th * dt_zone_sec;
        float sen_w = sh;
        int n_sys = 1;

        float t_chg = GPUSIM_FABS(zt_new - xm[0]);
        if (t_chg > GEN_MAX_ZONE_TEMP_DIFF) {
            int n_sub = (int)(t_chg / GEN_MAX_ZONE_TEMP_DIFF + 1.0f);
            if (n_sub > limit_num_sys) n_sub = limit_num_sys;
            float dt_sub_hr = GPUSIM_FMAX(dt_zone_hr / (float)n_sub, GEN_MIN_SYS_HR);
            float dt_sub_sec = dt_sub_hr * 3600.0f;
            float frac_sub = dt_sub_hr / dt_zone_hr;
            n_sys = n_sub;

            float b_mat = xm[0];
            float b_w = wp[0];
            float b_dsx[4], b_dsw[4];
            if (n_sub != num_sys_last[z]) {
                gen_down_interp_4(dt_zone_hr, dt_sub_hr, xm, b_dsx);
                gen_down_interp_4(dt_zone_hr, dt_sub_hr, wp, b_dsw);
            } else {
                for (int k = 0; k < 4; ++k) { b_dsx[k] = dsxmat[z * 4 + k]; b_dsw[k] = dsw_prev[z * 4 + k]; }
            }

            float acc_zt = 0.0f, acc_w = 0.0f, acc_e = 0.0f, acc_sen = 0.0f;
            for (int ss = 0; ss < n_sub; ++ss) {
                float zts, wns, shs, ths;
                gen_zone_air_step_1(
                    b_mat, b_w, pb_site, vol, dt_sub_sec,
                    b_dsx, b_dsw, sum_ha, sum_hat, mcpv, vamfl, mcptv,
                    q_gain_c, heat_sp, cool_sp, max_ht, min_ct, has_hvac, has_cool, w_site,
                    &zts, &wns, &shs, &ths
                );
                b_mat = zts; b_w = wns;
                b_dsx[3] = b_dsx[2]; b_dsx[2] = b_dsx[1]; b_dsx[1] = b_dsx[0]; b_dsx[0] = b_mat;
                b_dsw[3] = b_dsw[2]; b_dsw[2] = b_dsw[1]; b_dsw[1] = b_dsw[0]; b_dsw[0] = b_w;
                acc_zt += b_mat * frac_sub;
                acc_w += b_w * frac_sub;
                acc_e += ths * dt_sub_sec;
                acc_sen += shs * frac_sub;
            }
            zt_new = b_mat; w_new = b_w;
            ztav = acc_zt; w_avg = acc_w;
            heat_j = acc_e; sen_w = acc_sen;
            for (int k = 0; k < 4; ++k) { dsxmat[z * 4 + k] = b_dsx[k]; dsw_prev[z * 4 + k] = b_dsw[k]; }
        }

        t_mat[z] = zt_new;
        w_zone[z] = w_new;
        w_zone_avg[z] = w_avg;
        xmat[z * 4 + 3] = xm[2]; xmat[z * 4 + 2] = xm[1]; xmat[z * 4 + 1] = xm[0]; xmat[z * 4 + 0] = ztav;
        w_prev[z * 4 + 3] = wp[2]; w_prev[z * 4 + 2] = wp[1]; w_prev[z * 4 + 1] = wp[0]; w_prev[z * 4 + 0] = w_avg;
        num_sys_last[z] = n_sys;

        bldg_heat_j += heat_j;
        bldg_sen_w += sen_w;
        if (!is_warmup) {
            zone_annual_kwh[z] += heat_j * (1.0f / 3.6e6f);
            if (record_zone_temp) {
                zone_temp_rec[z * n_weather_steps + step] = ztav;
            }
        } else {
            if (ztav > *day_max_t_io) *day_max_t_io = ztav;
            if (ztav < *day_min_t_io) *day_min_t_io = ztav;
        }
    }

    if (!is_warmup) {
        hourly_heating_j[b * 8760 + hr] += bldg_heat_j;
    } else {
        if (bldg_sen_w > *day_max_h_io) *day_max_h_io = bldg_sen_w;
    }

    // 5. Update modal conduction states & previous surface temperatures
    for (int s = s0_b; s < s1_b; ++s) {
        int bnd = surf_boundary[s];
        float to = (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC) ? t_surf_in[s] : t_surf_out[s];
        if (bnd == BOUND_SURFACE) {
            int p = surf_partner_idx[s];
            to = (p >= 0) ? t_surf_in[p] : t_surf_in[s];
        }
        float ti = t_surf_in[s];
        int nm = surf_n_modes[s];
        if (nm > 0) {
            int mbase = s * GEN_MAX_MODES;
            for (int k = 0; k < nm; ++k) {
                int mk = mbase + k;
                modal_z[mk] += surf_m_gno[mk] * to + surf_m_gni[mk] * ti;
            }
        }
        t_surf_out_prev[s] = to;
        t_surf_in_prev[s] = ti;
    }
}

// ---------------------------------------------------------------------------
// Zone-parallel step: 1 thread per ZONE (100% GPU occupancy on multi-zone
// urban neighbourhoods, per-zone early exit, register-cached t4_buf).
// Interzone BOUND_SURFACE reads partner's t_surf_in_prev[p] cleanly without
// cross-zone write races.
// ---------------------------------------------------------------------------
GPUSIM_FN void gen_step_zone(
    int z,
    int step,
    int is_warmup,
    int begin_envrn,
    int sph,
    int n_weather_steps,
    int has_shading,
    int record_zone_temp,
    // Per-building [B]
    GPUSIM_GLOBAL const int *site_idx,
    GPUSIM_GLOBAL const int *terrain_idx,
    GPUSIM_GLOBAL const float *site_ground_temp,
    GPUSIM_GLOBAL const float *h_conv_min,
    // Per-zone [Z]
    GPUSIM_GLOBAL const int *zone_bldg_idx,
    GPUSIM_GLOBAL const int *zone_surf_offset,
    GPUSIM_GLOBAL const int *zone_sf_offset,
    GPUSIM_GLOBAL const float *zone_volume,
    GPUSIM_GLOBAL const float *zone_centroid_z,
    GPUSIM_GLOBAL const int *zone_has_hvac,
    GPUSIM_GLOBAL const int *zone_has_cooling,
    GPUSIM_GLOBAL const float *zone_max_heat_sup_t,
    GPUSIM_GLOBAL const float *zone_min_cool_sup_t,
    GPUSIM_GLOBAL const float *zone_heat_sp_hr,
    GPUSIM_GLOBAL const float *zone_cool_sp_hr,
    GPUSIM_GLOBAL const float *zone_gain_conv_hr,
    GPUSIM_GLOBAL const float *zone_gain_rad_hr,
    GPUSIM_GLOBAL const float *zone_vent_flow_hr,
    GPUSIM_GLOBAL const float *zone_total_op_aa,
    GPUSIM_GLOBAL const float *zone_floor_area_sw,
    GPUSIM_GLOBAL const float *zone_floor_alpha_eff,
    GPUSIM_GLOBAL const float *zone_total_eps_area,
    // Per-surface [S]
    GPUSIM_GLOBAL const int *surf_class,
    GPUSIM_GLOBAL const int *surf_boundary,
    GPUSIM_GLOBAL const int *surf_partner_idx,
    GPUSIM_GLOBAL const float *surf_area,
    GPUSIM_GLOBAL const float *surf_tilt_deg,
    GPUSIM_GLOBAL const float *surf_cos_tilt,
    GPUSIM_GLOBAL const float *surf_sin_tilt,
    GPUSIM_GLOBAL const float *surf_azimuth_deg,
    GPUSIM_GLOBAL const float *surf_nx,
    GPUSIM_GLOBAL const float *surf_ny,
    GPUSIM_GLOBAL const float *surf_nz,
    GPUSIM_GLOBAL const float *surf_centroid_z,
    GPUSIM_GLOBAL const float *surf_height,
    GPUSIM_GLOBAL const float *surf_roughness_mult,
    GPUSIM_GLOBAL const int *surf_sun_exposed,
    GPUSIM_GLOBAL const int *surf_wind_exposed,
    GPUSIM_GLOBAL const float *surf_solar_abs_out,
    GPUSIM_GLOBAL const float *surf_solar_abs_in,
    GPUSIM_GLOBAL const float *surf_eps_in,
    GPUSIM_GLOBAL const float *surf_eps_out,
    GPUSIM_GLOBAL const float *surf_vf_ground,
    GPUSIM_GLOBAL const float *surf_vf_sky,
    GPUSIM_GLOBAL const float *surf_vf_sky_ir,
    GPUSIM_GLOBAL const float *surf_vf_ground_ir,
    GPUSIM_GLOBAL const float *surf_air_sky_split,
    GPUSIM_GLOBAL const float *surf_osc_c_const,
    GPUSIM_GLOBAL const float *surf_osc_t_const,
    GPUSIM_GLOBAL const float *surf_osc_c_out,
    GPUSIM_GLOBAL const float *surf_osc_c_zone,
    GPUSIM_GLOBAL const float *surf_scon,
    GPUSIM_GLOBAL const float *surf_t_norm,
    GPUSIM_GLOBAL const float *surf_a_norm,
    GPUSIM_GLOBAL const float *surf_tau_diff,
    GPUSIM_GLOBAL const float *surf_abs_diff,
    GPUSIM_GLOBAL const int *surf_n_modes,
    GPUSIM_GLOBAL const float *surf_ctf_out0,
    GPUSIM_GLOBAL const float *surf_ctf_cross0,
    GPUSIM_GLOBAL const float *surf_ctf_in0,
    GPUSIM_GLOBAL const float *surf_lag_oo,
    GPUSIM_GLOBAL const float *surf_lag_oi,
    GPUSIM_GLOBAL const float *surf_lag_io,
    GPUSIM_GLOBAL const float *surf_lag_ii,
    GPUSIM_GLOBAL const float *surf_m_decay,
    GPUSIM_GLOBAL const float *surf_m_gno,
    GPUSIM_GLOBAL const float *surf_m_gni,
    GPUSIM_GLOBAL const float *surf_m_goo,
    GPUSIM_GLOBAL const float *surf_m_goi,
    GPUSIM_GLOBAL const float *surf_m_co,
    GPUSIM_GLOBAL const float *surf_m_ci,
    GPUSIM_GLOBAL const float *script_f_sigma,
    GPUSIM_GLOBAL const float *surf_dif_sky_shdg,
    GPUSIM_GLOBAL const unsigned char *surf_sunlit_u8,
    // Weather
    GPUSIM_GLOBAL const float *w_t_db,
    GPUSIM_GLOBAL const float *w_hum_rat,
    GPUSIM_GLOBAL const float *w_pb,
    GPUSIM_GLOBAL const float *w_t_sky,
    GPUSIM_GLOBAL const float *w_ws,
    GPUSIM_GLOBAL const float *w_wd,
    GPUSIM_GLOBAL const float *w_wb,
    GPUSIM_GLOBAL const float *w_rain,
    GPUSIM_GLOBAL const float *w_dni,
    GPUSIM_GLOBAL const float *w_dhi,
    GPUSIM_GLOBAL const float *w_sx,
    GPUSIM_GLOBAL const float *w_sy,
    GPUSIM_GLOBAL const float *w_sz,
    GPUSIM_GLOBAL const float *w_f1,
    GPUSIM_GLOBAL const float *w_f2,
    // State
    GPUSIM_GLOBAL float *t_surf_in,
    GPUSIM_GLOBAL float *t_surf_out,
    GPUSIM_GLOBAL float *t_surf_in_prev,
    GPUSIM_GLOBAL float *t_surf_out_prev,
    GPUSIM_GLOBAL float *t_surf_in_old,
    GPUSIM_GLOBAL float *theta1_win,
    GPUSIM_GLOBAL float *theta2_win,
    GPUSIM_GLOBAL float *h_conv_in,
    GPUSIM_GLOBAL float *ctf_const_in,
    GPUSIM_GLOBAL float *ctf_const_out,
    GPUSIM_GLOBAL float *q_sol_out,
    GPUSIM_GLOBAL float *q_sw_in,
    GPUSIM_GLOBAL float *q_sol_win,
    GPUSIM_GLOBAL float *modal_z,
    GPUSIM_GLOBAL float *t_mat,
    GPUSIM_GLOBAL float *xmat,
    GPUSIM_GLOBAL float *dsxmat,
    GPUSIM_GLOBAL float *w_zone,
    GPUSIM_GLOBAL float *w_zone_avg,
    GPUSIM_GLOBAL float *w_prev,
    GPUSIM_GLOBAL float *dsw_prev,
    GPUSIM_GLOBAL int *num_sys_last,
    // Outputs
    GPUSIM_GLOBAL float *zone_annual_kwh,
    GPUSIM_GLOBAL float *zone_temp_rec,
    float *step_heat_j_out,
    float *day_max_t_io,
    float *day_min_t_io,
    float *day_max_h_io
) {
    int b = zone_bldg_idx[z];
    int zs0 = zone_surf_offset[z];
    int zs1 = zone_surf_offset[z + 1];
    int n_sz = zs1 - zs0;
    int sf0 = zone_sf_offset[z];
    int si = site_idx[b];
    int terr = terrain_idx[b];
    float h_min = h_conv_min[b];
    int w_off = si * n_weather_steps + step;

    float t_site = w_t_db[w_off];
    float w_site = w_hum_rat[w_off];
    float pb_site = w_pb[w_off];
    float t_sky_site = w_t_sky[w_off];
    float ws_site = w_ws[w_off];
    float wd_site = w_wd[w_off];
    float dni = w_dni[w_off];
    float dhi = w_dhi[w_off];
    float sx = w_sx[w_off];
    float sy = w_sy[w_off];
    float sz = w_sz[w_off];
    float f1 = w_f1[w_off];
    float f2 = w_f2[w_off];

    int hr = step / sph;
    int doy = hr / 24;
    int month = gen_doy_to_month(doy);
    float t_gnd_m = site_ground_temp[b * 12 + month];
    float dt_zone_hr = 1.0f / (float)sph;
    float dt_zone_sec = 3600.0f / (float)sph;
    int limit_num_sys = (int)(dt_zone_hr / GEN_MIN_SYS_HR + 0.5f);
    if (limit_num_sys < 1) limit_num_sys = 1;

    // 1. Solar & interior radiant gains
    float q_tb = 0.0f;
    float q_td = 0.0f;
    if (sz > 0.0f) {
        float ghi = GPUSIM_FMAX(dni, 0.0f) * sz + GPUSIM_FMAX(dhi, 0.0f);
        float b_den = GPUSIM_FMAX(0.08715574f, sz);
        for (int s = zs0; s < zs1; ++s) {
            float qo = 0.0f;
            float qw = 0.0f;
            if (surf_sun_exposed[s]) {
                int bnd = surf_boundary[s];
                float cos_i = sx * surf_nx[s] + sy * surf_ny[s] + sz * surf_nz[s];
                float cpos = (cos_i > 0.0f) ? cos_i : 0.0f;
                float sunlit = has_shading ? ((float)surf_sunlit_u8[s * 8760 + hr] * (1.0f / 255.0f)) : 1.0f;
                float ib = GPUSIM_FMAX(dni, 0.0f) * cpos * sunlit;
                float aniso = GPUSIM_FMAX(
                    0.0f,
                    (1.0f - f1) * surf_vf_sky[s] * surf_dif_sky_shdg[s]
                    + f1 * (cpos / b_den) * sunlit
                    + f2 * surf_sin_tilt[s]
                );
                float ids = GPUSIM_FMAX(dhi, 0.0f) * aniso;
                float idg = 0.2f * ghi * surf_vf_ground[s];
                if (bnd == BOUND_OUTDOORS || bnd == BOUND_DOOR) {
                    qo = (ib + ids + idg) * surf_solar_abs_out[s];
                } else if (bnd == BOUND_WINDOW) {
                    float f_t = 0.0f;
                    float f_a = 0.0f;
                    if (cpos > 0.0f) {
                        f_t = cpos * (3.5621f + cpos * (-6.3941f + cpos * (6.2454f - 2.4134f * cpos)));
                        f_t = GPUSIM_FMIN(1.05f, GPUSIM_FMAX(0.0f, f_t));
                        f_a = cpos * (2.6177f + cpos * (-3.1518f + cpos * (1.8944f - 0.3603f * cpos)));
                        f_a = GPUSIM_FMIN(1.15f, GPUSIM_FMAX(0.0f, f_a));
                    }
                    float tb = surf_t_norm[s] * f_t;
                    float ab = surf_a_norm[s] * f_a;
                    float td = surf_tau_diff[s];
                    float ad = surf_abs_diff[s];
                    qw = ib * ab + (ids + idg) * ad;
                    q_tb += ib * tb * surf_area[s];
                    q_td += (ids + idg) * td * surf_area[s];
                }
            }
            q_sol_out[s] = qo;
            q_sol_win[s] = qw;
        }
    } else {
        for (int s = zs0; s < zs1; ++s) {
            q_sol_out[s] = 0.0f;
            q_sol_win[s] = 0.0f;
        }
    }

    float flr_a = zone_floor_area_sw[z];
    float flr_alpha = zone_floor_alpha_eff[z];
    float q_diff_pool = q_td + ((flr_a > 1.0e-6f) ? (1.0f - flr_alpha) * q_tb : q_tb);
    float q_diff_inc = q_diff_pool / GPUSIM_FMAX(zone_total_op_aa[z], 1.0e-12f);
    float q_rad_inc = zone_gain_rad_hr[z * 8760 + hr] / GPUSIM_FMAX(zone_total_eps_area[z], 1.0e-12f);

    for (int s = zs0; s < zs1; ++s) {
        int bnd = surf_boundary[s];
        if (bnd == BOUND_WINDOW) {
            q_sol_win[s] += q_diff_inc * surf_abs_diff[s];
            q_sw_in[s] = q_rad_inc * surf_eps_in[s];
        } else {
            float q_beam_flr = (surf_class[s] == SURF_FLOOR && flr_a > 1.0e-6f)
                ? (q_tb * surf_solar_abs_in[s] / flr_a) : 0.0f;
            q_sw_in[s] = q_beam_flr + q_diff_inc * surf_solar_abs_in[s] + q_rad_inc * surf_eps_in[s];
        }
    }

    // 2. Modal free-response, initial inside convection, and cached T^4 for outside HB
    float tz = t_mat[z];
    float wz = w_zone_avg[z];
    float t4_buf[64];
    int use_t4_buf = (n_sz <= 64) ? 1 : 0;

    for (int li = 0; li < n_sz; ++li) {
        int s = zs0 + li;
        float tsi = t_surf_in[s];
        if (use_t4_buf) {
            float tk = tsi + GEN_KELVIN;
            float tk2 = tk * tk;
            t4_buf[li] = tk2 * tk2;
        }
        int bnd = surf_boundary[s];
        if (bnd == BOUND_WINDOW) {
            h_conv_in[s] = gen_iso15099_win_hin(
                tsi, tz, wz, pb_site,
                surf_height[s], surf_tilt_deg[s], surf_sin_tilt[s], h_min
            );
        } else {
            h_conv_in[s] = gen_inside_conv_opaque(tsi, tz, surf_cos_tilt[s], h_min);
        }
        int nm = surf_n_modes[s];
        if (nm > 0) {
            float top = t_surf_out_prev[s];
            float tip = t_surf_in_prev[s];
            float co_s = surf_lag_oo[s] * top + surf_lag_oi[s] * tip;
            float ci_s = surf_lag_io[s] * top + surf_lag_ii[s] * tip;
            int mbase = s * GEN_MAX_MODES;
            for (int k = 0; k < nm; ++k) {
                int mk = mbase + k;
                float zf = surf_m_decay[mk] * modal_z[mk]
                         + surf_m_goo[mk] * top + surf_m_goi[mk] * tip;
                co_s += surf_m_co[mk] * zf;
                ci_s += surf_m_ci[mk] * zf;
                modal_z[mk] = zf;
            }
            ctf_const_out[s] = co_s;
            ctf_const_in[s] = ci_s;
        } else {
            ctf_const_out[s] = 0.0f;
            ctf_const_in[s] = 0.0f;
        }
    }

    for (int li = 0; li < n_sz; ++li) {
        int s = zs0 + li;
        int bnd = surf_boundary[s];
        if (bnd == BOUND_OSC) {
            float t_out_air = gen_out_dry_bulb_at(t_site, surf_centroid_z[s]);
            t_surf_out[s] = surf_osc_c_zone[s] * tz
                          + surf_osc_c_out[s] * t_out_air
                          + surf_osc_c_const[s] * surf_osc_t_const[s];
        } else if (bnd == BOUND_GROUND) {
            t_surf_out[s] = t_gnd_m;
        } else if (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC) {
            t_surf_out[s] = t_surf_in[s];
        } else if (bnd == BOUND_SURFACE) {
            int p = surf_partner_idx[s];
            t_surf_out[s] = (p >= 0) ? t_surf_in_prev[p] : t_surf_in[s];
        } else if (bnd == BOUND_OUTDOORS || bnd == BOUND_DOOR) {
            float t_out_air = gen_out_dry_bulb_at(t_site, surf_centroid_z[s]);
            float ti4;
            if (use_t4_buf) {
                ti4 = t4_buf[li];
            } else {
                float tk = t_surf_in[s] + GEN_KELVIN;
                float tk2 = tk * tk;
                ti4 = tk2 * tk2;
            }
            float q_lw = 0.0f;
            int row_off = sf0 + li * n_sz;
            if (use_t4_buf) {
                for (int lj = 0; lj < n_sz; ++lj) {
                    q_lw += script_f_sigma[row_off + lj] * (t4_buf[lj] - ti4);
                }
            } else {
                for (int lj = 0; lj < n_sz; ++lj) {
                    float tj_k = t_surf_in[zs0 + lj] + GEN_KELVIN;
                    float tj2 = tj_k * tj_k;
                    q_lw += script_f_sigma[row_off + lj] * (tj2 * tj2 - ti4);
                }
            }
            float v_loc = surf_wind_exposed[s] ? gen_wind_speed_at(ws_site, surf_centroid_z[s], terr) : 0.0f;
            int ww = surf_wind_exposed[s] ? gen_is_windward(surf_azimuth_deg[s], wd_site) : 1;
            float hc_ext = gen_outside_conv_doe2(
                t_surf_out[s], t_out_air, surf_cos_tilt[s], v_loc, surf_roughness_mult[s], ww
            );
            float hsky, hgnd, hair;
            gen_outside_rad_coeffs(
                t_surf_out[s], t_out_air, t_sky_site,
                surf_eps_out[s], surf_vf_sky_ir[s], surf_vf_ground_ir[s], surf_air_sky_split[s],
                &hsky, &hgnd, &hair
            );
            float c_o0 = surf_ctf_out0[s];
            float c_y0 = surf_ctf_cross0[s];
            float c_i0 = surf_ctf_in0[s];
            float ext_num = -ctf_const_out[s] + q_sol_out[s]
                          + (hc_ext + hair) * t_out_air + hsky * t_sky_site + hgnd * t_site;
            float ext_den = c_o0 + hc_ext + hair + hsky + hgnd;
            float num, den;
            if (c_y0 > 0.01f) {
                float f_q = c_y0 / GPUSIM_FMAX(c_i0 + h_conv_in[s], 1.0e-12f);
                num = ext_num + f_q * (ctf_const_in[s] + h_conv_in[s] * tz + q_lw + q_sw_in[s]);
                den = ext_den - f_q * c_y0;
            } else {
                num = ext_num + c_y0 * t_surf_in[s];
                den = ext_den;
            }
            t_surf_out[s] = num / ((GPUSIM_FABS(den) < 1.0e-12f) ? 1.0f : den);
        }
    }

    // 3. Per-zone inside-surface iteration loop with independent early exit
    for (int it = 0; it < GEN_MAX_ITERS; ++it) {
        for (int li = 0; li < n_sz; ++li) {
            int s = zs0 + li;
            float ts = t_surf_in[s];
            t_surf_in_old[s] = ts;
            if (use_t4_buf) {
                float tk = ts + GEN_KELVIN;
                float tk2 = tk * tk;
                t4_buf[li] = tk2 * tk2;
            }
        }
        float max_del_t = 0.0f;
        for (int li = 0; li < n_sz; ++li) {
            int s = zs0 + li;
            int bnd = surf_boundary[s];
            float ti4;
            if (use_t4_buf) {
                ti4 = t4_buf[li];
            } else {
                float tk = t_surf_in_old[s] + GEN_KELVIN;
                float tk2 = tk * tk;
                ti4 = tk2 * tk2;
            }
            float q_net_lw = 0.0f;
            int row_off = sf0 + li * n_sz;
            if (use_t4_buf) {
                for (int lj = 0; lj < n_sz; ++lj) {
                    q_net_lw += script_f_sigma[row_off + lj] * (t4_buf[lj] - ti4);
                }
            } else {
                for (int lj = 0; lj < n_sz; ++lj) {
                    float tj_k = t_surf_in_old[zs0 + lj] + GEN_KELVIN;
                    float tj2 = tj_k * tj_k;
                    q_net_lw += script_f_sigma[row_off + lj] * (tj2 * tj2 - ti4);
                }
            }

            if (bnd == BOUND_WINDOW) {
                if (it == 0) {
                    float t_out_air = gen_out_dry_bulb_at(t_site, surf_centroid_z[s]);
                    float v_loc = surf_wind_exposed[s] ? gen_wind_speed_at(ws_site, surf_centroid_z[s], terr) : 0.0f;
                    int ww = surf_wind_exposed[s] ? gen_is_windward(surf_azimuth_deg[s], wd_site) : 1;
                    float hc_ext = gen_outside_conv_doe2(
                        t_surf_out[s], t_out_air, surf_cos_tilt[s], v_loc, surf_roughness_mult[s], ww
                    );
                    float eps_i = GPUSIM_FMAX(surf_eps_in[s], 1.0e-6f);
                    float rmir = (q_net_lw + q_sw_in[s]) / eps_i + GEN_SIGMA * ti4;
                    float th1 = theta1_win[s];
                    float th2 = theta2_win[s];
                    if (begin_envrn) {
                        float hrad = 5.3f;
                        float r1 = 1.0f / (hc_ext + hrad);
                        float r2 = 1.0f / GPUSIM_FMAX(surf_scon[s], 1.0e-6f);
                        float r3 = 1.0f / (h_conv_in[s] + hrad);
                        float rt = r1 + r2 + r3;
                        float td = (tz - t_out_air);
                        if (GPUSIM_FABS(td) < 0.5f) td = 2.0f;
                        th1 = (r1 / rt) * td + (t_out_air + GEN_KELVIN);
                        th2 = ((r1 + r2) / rt) * td + (t_out_air + GEN_KELVIN);
                    }
                    float win_hin = h_conv_in[s];
                    gen_solve_simple_window(
                        tz, t_out_air, t_sky_site, wz, pb_site,
                        hc_ext, rmir, q_sol_win[s], surf_scon[s],
                        surf_eps_out[s], surf_eps_in[s],
                        surf_vf_sky_ir[s], surf_vf_ground_ir[s], surf_air_sky_split[s],
                        surf_height[s], surf_tilt_deg[s], surf_sin_tilt[s], h_min,
                        &th1, &th2, &win_hin
                    );
                    theta1_win[s] = th1;
                    theta2_win[s] = th2;
                    t_surf_out[s] = th1 - GEN_KELVIN;
                    t_surf_in[s] = th2 - GEN_KELVIN;
                    h_conv_in[s] = win_hin;
                }
            } else {
                if (it > 0 && (it % GEN_REEVAL_CONV == 0)) {
                    h_conv_in[s] = gen_inside_conv_opaque(t_surf_in_old[s], tz, surf_cos_tilt[s], h_min);
                }
                float hc = h_conv_in[s];
                float ci0 = surf_ctf_in0[s];
                float cy0 = surf_ctf_cross0[s];
                float temp_term = ctf_const_in[s] + hc * tz + q_net_lw + q_sw_in[s];
                int is_ad = (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC);
                float num, den;
                if (is_ad) {
                    num = temp_term + GEN_ITER_DAMP * t_surf_in_old[s];
                    den = ci0 - cy0 + hc + GEN_ITER_DAMP;
                } else {
                    num = temp_term + GEN_ITER_DAMP * t_surf_in_old[s] + cy0 * t_surf_out[s];
                    den = ci0 + hc + GEN_ITER_DAMP;
                }
                float new_ti = num / ((GPUSIM_FABS(den) < 1.0e-12f) ? 1.0f : den);
                t_surf_in[s] = new_ti;
                float dt_s = GPUSIM_FABS(new_ti - t_surf_in_old[s]);
                if (dt_s > max_del_t) max_del_t = dt_s;
            }
        }
        if (max_del_t <= GEN_MAX_DEL_T) break;
    }

    // 4. Zone air balance & IdealLoads
    float sum_ha = 0.0f;
    float sum_hat = 0.0f;
    for (int s = zs0; s < zs1; ++s) {
        float ha = h_conv_in[s] * surf_area[s];
        sum_ha += ha;
        sum_hat += ha * t_surf_in[s];
    }

    float t_out_z = gen_out_dry_bulb_at(t_site, zone_centroid_z[z]);
    float v_flow = zone_vent_flow_hr[z * 8760 + hr];
    float rho_v = gen_psy_rho_air(pb_site, t_out_z, w_site);
    float cp_v = gen_psy_cp_air(w_site);
    float vamfl = v_flow * rho_v;
    float mcpv = vamfl * cp_v;
    float mcptv = mcpv * t_out_z;

    float q_gain_c = zone_gain_conv_hr[z * 8760 + hr];
    float heat_sp = zone_heat_sp_hr[z * 8760 + hr];
    float cool_sp = zone_cool_sp_hr[z * 8760 + hr];
    int has_hvac = zone_has_hvac[z];
    int has_cool = zone_has_cooling[z];
    float max_ht = zone_max_heat_sup_t[z];
    float min_ct = zone_min_cool_sup_t[z];
    float vol = zone_volume[z];

    float xm[4], wp[4];
    for (int k = 0; k < 4; ++k) { xm[k] = xmat[z * 4 + k]; wp[k] = w_prev[z * 4 + k]; }

    float zt_new, w_new, sh, th;
    gen_zone_air_step_1(
        tz, w_zone[z], pb_site, vol, dt_zone_sec,
        xm, wp, sum_ha, sum_hat, mcpv, vamfl, mcptv,
        q_gain_c, heat_sp, cool_sp, max_ht, min_ct, has_hvac, has_cool, w_site,
        &zt_new, &w_new, &sh, &th
    );

    float ztav = zt_new;
    float w_avg = w_new;
    float heat_j = th * dt_zone_sec;
    float sen_w = sh;
    int n_sys = 1;

    float t_chg = GPUSIM_FABS(zt_new - xm[0]);
    if (t_chg > GEN_MAX_ZONE_TEMP_DIFF) {
        int n_sub = (int)(t_chg / GEN_MAX_ZONE_TEMP_DIFF + 1.0f);
        if (n_sub > limit_num_sys) n_sub = limit_num_sys;
        float dt_sub_hr = GPUSIM_FMAX(dt_zone_hr / (float)n_sub, GEN_MIN_SYS_HR);
        float dt_sub_sec = dt_sub_hr * 3600.0f;
        float frac_sub = dt_sub_hr / dt_zone_hr;
        n_sys = n_sub;

        float b_mat = xm[0];
        float b_w = wp[0];
        float b_dsx[4], b_dsw[4];
        if (n_sub != num_sys_last[z]) {
            gen_down_interp_4(dt_zone_hr, dt_sub_hr, xm, b_dsx);
            gen_down_interp_4(dt_zone_hr, dt_sub_hr, wp, b_dsw);
        } else {
            for (int k = 0; k < 4; ++k) { b_dsx[k] = dsxmat[z * 4 + k]; b_dsw[k] = dsw_prev[z * 4 + k]; }
        }

        float acc_zt = 0.0f, acc_w = 0.0f, acc_e = 0.0f, acc_sen = 0.0f;
        for (int ss = 0; ss < n_sub; ++ss) {
            float zts, wns, shs, ths;
            gen_zone_air_step_1(
                b_mat, b_w, pb_site, vol, dt_sub_sec,
                b_dsx, b_dsw, sum_ha, sum_hat, mcpv, vamfl, mcptv,
                q_gain_c, heat_sp, cool_sp, max_ht, min_ct, has_hvac, has_cool, w_site,
                &zts, &wns, &shs, &ths
            );
            b_mat = zts; b_w = wns;
            b_dsx[3] = b_dsx[2]; b_dsx[2] = b_dsx[1]; b_dsx[1] = b_dsx[0]; b_dsx[0] = b_mat;
            b_dsw[3] = b_dsw[2]; b_dsw[2] = b_dsw[1]; b_dsw[1] = b_dsw[0]; b_dsw[0] = b_w;
            acc_zt += b_mat * frac_sub;
            acc_w += b_w * frac_sub;
            acc_e += ths * dt_sub_sec;
            acc_sen += shs * frac_sub;
        }
        zt_new = b_mat; w_new = b_w;
        ztav = acc_zt; w_avg = acc_w;
        heat_j = acc_e; sen_w = acc_sen;
        for (int k = 0; k < 4; ++k) { dsxmat[z * 4 + k] = b_dsx[k]; dsw_prev[z * 4 + k] = b_dsw[k]; }
    }

    t_mat[z] = zt_new;
    w_zone[z] = w_new;
    w_zone_avg[z] = w_avg;
    xmat[z * 4 + 3] = xm[2]; xmat[z * 4 + 2] = xm[1]; xmat[z * 4 + 1] = xm[0]; xmat[z * 4 + 0] = ztav;
    w_prev[z * 4 + 3] = wp[2]; w_prev[z * 4 + 2] = wp[1]; w_prev[z * 4 + 1] = wp[0]; w_prev[z * 4 + 0] = w_avg;
    num_sys_last[z] = n_sys;

    if (!is_warmup) {
        zone_annual_kwh[z] += heat_j * (1.0f / 3.6e6f);
        *step_heat_j_out = heat_j;
        if (record_zone_temp) {
            zone_temp_rec[z * n_weather_steps + step] = ztav;
        }
    } else {
        *step_heat_j_out = 0.0f;
        if (ztav > *day_max_t_io) *day_max_t_io = ztav;
        if (ztav < *day_min_t_io) *day_min_t_io = ztav;
        if (sen_w > *day_max_h_io) *day_max_h_io = sen_w;
    }

    // 5. Update modal conduction states & previous surface temperatures
    for (int s = zs0; s < zs1; ++s) {
        int bnd = surf_boundary[s];
        float ti = t_surf_in[s];
        float to = (bnd == BOUND_INTMASS || bnd == BOUND_ADIABATIC) ? ti : t_surf_out[s];
        int nm = surf_n_modes[s];
        if (nm > 0) {
            int mbase = s * GEN_MAX_MODES;
            for (int k = 0; k < nm; ++k) {
                int mk = mbase + k;
                modal_z[mk] += surf_m_gno[mk] * to + surf_m_gni[mk] * ti;
            }
        }
        t_surf_out_prev[s] = to;
        t_surf_in_prev[s] = ti;
    }
}

#endif // GPUSIM_GENERAL_COMMON_H

