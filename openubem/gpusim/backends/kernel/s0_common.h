#ifndef GPUSIM_S0_COMMON_H
#define GPUSIM_S0_COMMON_H

#ifdef GPUSIM_HOST
#include <math.h>
#ifndef GPUSIM_FN
#define GPUSIM_FN static inline
#endif
#ifndef GPUSIM_GLOBAL
#define GPUSIM_GLOBAL
#endif
#ifndef GPUSIM_GLOBAL_CONST
#define GPUSIM_GLOBAL_CONST const
#endif
#ifndef GPUSIM_THREAD
#define GPUSIM_THREAD
#endif
#ifndef GPUSIM_POW
#define GPUSIM_POW powf
#endif
#ifndef GPUSIM_EXP
#define GPUSIM_EXP expf
#endif
#ifndef GPUSIM_LOG
#define GPUSIM_LOG logf
#endif
#endif

#define S0_MAX_SURF 16
#define S0_MAX_CTF_HIST 8
#define S0_T_REF_C 20.0f
#define S0_T_REF_K 293.15f
#define S0_TRIPLE_POINT_K 273.16f
#define S0_SIGMA 5.6697e-8f
#define S0_ITER_DAMP 5.0f
#define S0_MAX_ITERS 500
#define S0_REEVAL_CONV 30
#define S0_MAX_DEL_T 0.002f
#define S0_WIN_MAX_ITER 100
#define S0_WIN_ERR_TOL 0.02f
#define S0_SMALL_TEMP_DIFF 1.0e-5f
#define S0_VERY_SMALL_MASS_FLOW 1.0e-12f
#define S0_MAX_ZONE_TEMP_DIFF 0.3f
#define S0_MIN_TIME_STEP_SYS_HR (1.0f / 60.0f)

#define FLAG_SURF_MASK 1
#define FLAG_IS_OSC 2
#define FLAG_IS_OUTDOORS_OP 4
#define FLAG_IS_INTMASS 8
#define FLAG_IS_WINDOW 16
#define FLAG_IS_NON_WINDOW 32

#define BF_ZONE_VOLUME 0
#define BF_ZONE_FLOOR_AREA 1
#define BF_ZONE_CENTROID_Z 2
#define BF_ZONE_LAPSE_OFFSET 3
#define BF_VENT_ACH 4
#define BF_VENT_FLOW_M3S 5
#define BF_HEAT_SP_DT 6
#define BF_COOL_SP_DT 7
#define BF_MAX_HEAT_SUP_DT 8
#define BF_MAX_HEAT_SUP_HUMRAT 9
#define BF_H_CONV_MIN 10
#define BF_H_CONV_MAX 11
#define BF_LOADS_CONV_TOL 12
#define BF_TEMP_CONV_TOL 13
#define BF_SITE_ELEVATION 14
#define BF_COUNT 15

#define BI_SITE_IDX 0
#define BI_WU_MIN_DAYS 1
#define BI_WU_MAX_DAYS 2
#define BI_NUM_SURF 3
#define BI_HAS_WINDOW 4
#define BI_COUNT 5

#define SS_AREA 0
#define SS_COS_TILT 1
#define SS_SIN_TILT 2
#define SS_TILT_DEG 3
#define SS_CENTROID_Z 4
#define SS_LAPSE_OFFSET 5
#define SS_U_VALUE 6
#define SS_OSC_C_CONST 7
#define SS_OSC_T_CONST_DT 8
#define SS_OSC_C_OUT 9
#define SS_OSC_C_ZONE 10
#define SS_OSC_SHIFT 11
#define SS_VF_SKY_IR 12
#define SS_VF_GROUND_IR 13
#define SS_AIR_SKY_SPLIT 14
#define SS_EPS_IN 15
#define SS_EPS_OUT 16
#define SS_HEIGHT 17
#define SS_SCON_WIN 18
#define SS_CTF_OUT0 19
#define SS_CTF_CROSS0 20
#define SS_CTF_IN0 21
#define SS_COUNT 22

#define WF_DT_DB 0
#define WF_HUM_RAT 1
#define WF_BARO_PRESS 2
#define WF_DT_SKY 3
#define WF_COUNT 4

#define ZS_T_MAT_DT 0
#define ZS_W_ZONE 1
#define ZS_W_ZONE_AVG 2
#define ZS_XMAT0 3
#define ZS_DSXMAT0 7
#define ZS_W_PREV0 11
#define ZS_DSW_PREV0 15
#define ZS_COUNT 19

#define ST_SURF_DT_IN 0
#define ST_SURF_DT_OUT 1
#define ST_DTH1_WIN 2
#define ST_DTH2_WIN 3
#define ST_COUNT 4

#define CH_T_OUT_DT 0
#define CH_T_IN_DT 1
#define CH_Q_OUT 2
#define CH_Q_IN 3
#define CH_COUNT 4

#define WU_STAT_MAX_T_DT 0
#define WU_STAT_MIN_T_DT 1
#define WU_STAT_MAX_H_RATE 2
#define WU_STAT_COUNT 3

#define PI_B_SIZE 0
#define PI_N_SURF 1
#define PI_N_SITES 2
#define PI_N_CTF_HIST 3
#define PI_SPH 4
#define PI_STEP_START 5
#define PI_STEP_END 6
#define PI_IS_WARMUP 7
#define PI_WARMUP_DAY 8
#define PI_RECORD_TEMP 9
#define PI_REC_STEP_OFFSET 10
#define PI_LIMIT_NUM_SYS 11
#define PI_N_WSTEPS 12

// Psychrometrics.hh::PsyRhoAirFnPbTdbW | psy_rho_air_fn_pb_tdb_w
GPUSIM_FN float s0_psy_rho_air(float pb, float t_k, float dw) {
    float w = (dw > 1.0e-5f) ? dw : 1.0e-5f;
    return pb / (287.0f * t_k * (1.0f + 1.6077687f * w));
}

// Psychrometrics.hh::PsyCpAirFnW | psy_cp_air_fn_w
GPUSIM_FN float s0_psy_cp_air(float dw) {
    float w = (dw > 1.0e-5f) ? dw : 1.0e-5f;
    return 1.00484e3f + w * 1.85895e3f;
}

// Psychrometrics.cc::PsyPsatFnTemp | psy_psat_fn_temp
GPUSIM_FN float s0_psy_psat_fn_temp(float dt_c) {
    float tkel = S0_T_REF_K + dt_c;
    if (tkel < 173.15f) {
        return 0.001405102123874164f;
    }
    if (tkel > 473.15f) {
        return 1555073.745636215f;
    }
    float log_t = GPUSIM_LOG(tkel);
    if (tkel < S0_TRIPLE_POINT_K) {
        float ice_exp = -5674.5359f / tkel + 6.3925247f +
            tkel *
                (-0.9677843e-2f +
                 tkel *
                     (0.62215701e-6f +
                      tkel * (0.20747825e-8f - 0.9484024e-12f * tkel))) +
            4.1635019f * log_t;
        return GPUSIM_EXP(ice_exp);
    }
    float liq_exp = -5800.2206f / tkel + 1.3914993f +
        tkel *
            (-0.048640239f +
             tkel * (0.41764768e-4f - 0.14452093e-7f * tkel)) +
        6.5459673f * log_t;
    return GPUSIM_EXP(liq_exp);
}

// Psychrometrics.hh::PsyWFnTdbRhPb | psy_w_fn_tdb_rh_pb
GPUSIM_FN float s0_psy_w_fn_tdb_rh_pb(float dt_c, float rh, float pb) {
    float pdew = rh * s0_psy_psat_fn_temp(dt_c);
    float diff = pb - pdew;
    float denom = (diff > 1000.0f) ? diff : 1000.0f;
    float w = pdew * 0.62198f / denom;
    return (w > 1.0e-5f) ? w : 1.0e-5f;
}

// ConvectionCoefficients.cc::CalcASHRAETARPNatural | calc_ashrae_tarp_natural
GPUSIM_FN float s0_ashrae_tarp_natural(
    float dt_surf,
    float dt_amb,
    float cos_tilt
) {
    float delta_t = dt_surf - dt_amb;
    float abs_dt = (delta_t < 0.0f) ? -delta_t : delta_t;
    float abs_dt_cbrt =
        (abs_dt > 0.0f) ? GPUSIM_POW(abs_dt, 1.0f / 3.0f) : 0.0f;
    float abs_cos = (cos_tilt < 0.0f) ? -cos_tilt : cos_tilt;
    if (delta_t == 0.0f || cos_tilt == 0.0f) {
        return 1.31f * abs_dt_cbrt;
    }
    if ((delta_t < 0.0f && cos_tilt < 0.0f) ||
        (delta_t > 0.0f && cos_tilt > 0.0f)) {
        return 9.482f * abs_dt_cbrt / (7.238f - abs_cos);
    }
    return 1.810f * abs_dt_cbrt / (1.382f + abs_cos);
}

// ConvectionCoefficients.cc::CalcASHRAEDetailedIntConvCoeff | calc_inside_convection_opaque
GPUSIM_FN float s0_inside_conv_opaque(
    float dt_surf,
    float dt_zone,
    float cos_tilt,
    float h_min
) {
    float h_nat = s0_ashrae_tarp_natural(dt_surf, dt_zone, -cos_tilt);
    return (h_nat > h_min) ? h_nat : h_min;
}

// ConvectionCoefficients.cc::InitExteriorConvectionCoeff | calc_outside_convection_doe2
GPUSIM_FN float s0_outside_conv_doe2(
    float dt_surf,
    float dt_air,
    float cos_tilt
) {
    return s0_ashrae_tarp_natural(dt_surf, dt_air, cos_tilt);
}

// ConvectionCoefficients.cc::InitExteriorConvectionCoeff | calc_outside_rad_coeffs
GPUSIM_FN void s0_outside_rad_coeffs(
    float dt_surf,
    float dt_air,
    float dt_sky,
    float eps_out,
    float vf_sky_ir,
    float vf_ground_ir,
    float air_sky_split,
    GPUSIM_THREAD float* out_h_sky,
    GPUSIM_THREAD float* out_h_ground,
    GPUSIM_THREAD float* out_h_air
) {
    float ts_k = S0_T_REF_K + dt_surf;
    float ta_k = S0_T_REF_K + dt_air;
    float tsky_k = S0_T_REF_K + dt_sky;
    float ts_k2 = ts_k * ts_k;
    float ta_k2 = ta_k * ta_k;
    float tsky_k2 = tsky_k * tsky_k;
    float sky_fac = (ts_k2 + tsky_k2) * (ts_k + tsky_k);
    float air_fac = (ts_k2 + ta_k2) * (ts_k + ta_k);
    *out_h_sky = (ts_k == tsky_k)
        ? 0.0f
        : (S0_SIGMA * eps_out * vf_sky_ir * air_sky_split * sky_fac);
    *out_h_ground = (ts_k == ta_k)
        ? 0.0f
        : (S0_SIGMA * eps_out * vf_ground_ir * air_fac);
    *out_h_air = (ts_k == ta_k)
        ? 0.0f
        : (S0_SIGMA * eps_out * vf_sky_ir * (1.0f - air_sky_split) * air_fac);
}

// ConvectionCoefficients.cc::CalcISO15099WindowIntConvCoeff | calc_iso15099_window_int_conv_coeff
GPUSIM_FN float s0_iso15099_win_int_conv(
    float dt_surf,
    float dt_air,
    float hum_rat,
    float baro_press,
    float height,
    float tilt_deg,
    float sin_tilt,
    float h_min
) {
    float t_surf_k = S0_T_REF_K + dt_surf;
    float t_air_k = S0_T_REF_K + dt_air;
    float delta_t = dt_surf - dt_air;
    if (t_air_k < 200.0f || t_air_k > 400.0f || t_surf_k < 180.0f ||
        t_surf_k > 450.0f) {
        return h_min;
    }
    float t_film_k = t_air_k + 0.25f * delta_t;
    float rho = s0_psy_rho_air(baro_press, t_film_k, hum_rat);
    float lam = 2.873e-3f + 7.76e-5f * t_film_k;
    float mu = 3.723e-6f + 4.94e-8f * t_film_k;
    float cp = s0_psy_cp_air(hum_rat);
    float eff_tilt = (delta_t > 0.0f) ? (180.0f - tilt_deg) : tilt_deg;
    float safe_h = (height > 1.0e-6f) ? height : 1.0e-6f;
    float safe_sin = (sin_tilt > 1.0e-12f) ? sin_tilt : 1.0e-12f;
    float abs_dt = (delta_t < 0.0f) ? -delta_t : delta_t;
    float ra_h = (rho * rho) * (safe_h * safe_h * safe_h) * 9.81f * cp *
        abs_dt / (t_film_k * mu * lam);
    float nu_int = 0.0f;
    if (eff_tilt < 15.0f) {
        nu_int = (ra_h > 0.0f) ? (0.13f * GPUSIM_POW(ra_h, 1.0f / 3.0f)) : 0.0f;
    } else if (eff_tilt <= 90.0f) {
        float clamped = (eff_tilt < 15.0f) ? 15.0f : eff_tilt;
        float ra_cv =
            2.5e5f * GPUSIM_EXP(0.144f * clamped) / GPUSIM_POW(safe_sin, 0.2f);
        float ra_h_sin = ra_h * safe_sin;
        if (ra_h <= ra_cv) {
            nu_int =
                (ra_h_sin > 0.0f) ? (0.56f * GPUSIM_POW(ra_h_sin, 0.25f)) : 0.0f;
        } else {
            float p_rah = (ra_h > 0.0f) ? GPUSIM_POW(ra_h, 1.0f / 3.0f) : 0.0f;
            float p_racv = GPUSIM_POW(ra_cv, 1.0f / 3.0f);
            nu_int = 0.13f * (p_rah - p_racv) +
                0.56f * GPUSIM_POW(ra_cv * safe_sin, 0.25f);
        }
    } else if (eff_tilt <= 179.0f) {
        float ra_h_sin = ra_h * safe_sin;
        if (ra_h_sin < 1.0e5f) {
            nu_int = 9.958364696217969f;
        } else if (ra_h_sin >= 1.0e11f) {
            nu_int = 314.9111421065955f;
        } else {
            nu_int = 0.56f * GPUSIM_POW(ra_h_sin, 0.25f);
        }
    } else {
        if (ra_h > 1.0e11f) {
            nu_int = 91.92380516274462f;
        } else {
            nu_int = (ra_h > 0.0f) ? (0.58f * GPUSIM_POW(ra_h, 0.2f)) : 0.0f;
        }
    }
    float h_val = nu_int * lam / safe_h;
    return (h_val > h_min) ? h_val : h_min;
}

// WindowManager.cc::CalcWindowHeatBalanceInternalRoutines | calc_window_outside_ir
GPUSIM_FN float s0_window_outside_ir(
    float t_out_k,
    float t_sky_k,
    float vf_sky_ir,
    float vf_ground_ir,
    float air_sky_split
) {
    float t_out2 = t_out_k * t_out_k;
    float eb_out = S0_SIGMA * (t_out2 * t_out2);
    float t_sky2 = t_sky_k * t_sky_k;
    float eb_sky = S0_SIGMA * (t_sky2 * t_sky2);
    return vf_sky_ir *
        (air_sky_split * eb_sky + (1.0f - air_sky_split) * eb_out) +
        vf_ground_ir * eb_out;
}

// WindowManager.cc::StartingWindowTemps | starting_window_temps
GPUSIM_FN void s0_starting_window_temps(
    float dt_in,
    float dt_out,
    float h_in,
    float h_out,
    float scon,
    GPUSIM_THREAD float* out_dth1,
    GPUSIM_THREAD float* out_dth2
) {
    float hrad = 5.3f;
    float r1 = 1.0f / (h_out + hrad);
    float safe_scon = (scon > 1.0e-6f) ? scon : 1.0e-6f;
    float r2 = 1.0f / safe_scon;
    float r3 = 1.0f / (h_in + hrad);
    float r_tot = r1 + r2 + r3;
    float temdiff = dt_in - dt_out;
    float abs_td = (temdiff < 0.0f) ? -temdiff : temdiff;
    if (abs_td < 0.5f) {
        temdiff = 2.0f;
    }
    *out_dth1 = (r1 / r_tot) * temdiff + dt_out;
    *out_dth2 = ((r1 + r2) / r_tot) * temdiff + dt_out;
}

// WindowManager.cc::SolveForWindowTemperatures | solve_simple_window
GPUSIM_FN void s0_solve_simple_window(
    float dt_in,
    float dt_out,
    float dt_sky,
    float hum_rat,
    float baro_press,
    float h_out,
    float rmir,
    float scon,
    float eps_out,
    float eps_in,
    float vf_sky_ir,
    float vf_ground_ir,
    float air_sky_split,
    float height,
    float tilt_deg,
    float sin_tilt,
    float h_min,
    float dth1_init,
    float dth2_init,
    GPUSIM_THREAD float* out_dt_in,
    GPUSIM_THREAD float* out_dt_out,
    GPUSIM_THREAD float* out_h_in,
    GPUSIM_THREAD float* out_dth1,
    GPUSIM_THREAD float* out_dth2
) {
    float t_out_k = S0_T_REF_K + dt_out;
    float t_sky_k = S0_T_REF_K + dt_sky;
    float out_ir = s0_window_outside_ir(
        t_out_k, t_sky_k, vf_sky_ir, vf_ground_ir, air_sky_split
    );
    float dth1 = dth1_init;
    float dth2 = dth2_init;
    float h_in = 3.0f;
    for (int it = 0; it < S0_WIN_MAX_ITER; ++it) {
        float th1 = S0_T_REF_K + dth1;
        float th2 = S0_T_REF_K + dth2;
        float hr1 = eps_out * S0_SIGMA * (th1 * th1 * th1);
        float hr2 = eps_in * S0_SIGMA * (th2 * th2 * th2);
        h_in = s0_iso15099_win_int_conv(
            dth2, dt_in, hum_rat, baro_press, height, tilt_deg, sin_tilt, h_min
        );
        float a11 = hr1 + scon + h_out;
        float a22 = hr2 + scon + h_in;
        float rhs1 = eps_out * out_ir - hr1 * S0_T_REF_K + h_out * dt_out;
        float rhs2 = eps_in * rmir - hr2 * S0_T_REF_K + h_in * dt_in;
        float det =
            (hr1 + h_out) * (hr2 + h_in) + scon * (hr1 + h_out + hr2 + h_in);
        float d_sol1 = (a22 * rhs1 + scon * rhs2) / det;
        float d_sol2 = (scon * rhs1 + a11 * rhs2) / det;
        float w_old = (it + 1 < (S0_WIN_MAX_ITER / 4)) ? 0.5f : 0.75f;
        float w_new = 1.0f - w_old;
        float new_dth1 = w_old * dth1 + w_new * d_sol1;
        float new_dth2 = w_old * dth2 + w_new * d_sol2;
        float e1 = new_dth1 - dth1;
        float e2 = new_dth2 - dth2;
        float err = 0.5f * ((e1 < 0.0f ? -e1 : e1) + (e2 < 0.0f ? -e2 : e2));
        dth1 = new_dth1;
        dth2 = new_dth2;
        if (err <= S0_WIN_ERR_TOL) {
            break;
        }
    }
    *out_dt_in = dth2;
    *out_dt_out = dth1;
    *out_h_in = h_in;
    *out_dth1 = dth1;
    *out_dth2 = dth2;
}

// HeatBalanceIntRadExchange.cc::CalcInteriorRadExchange | calc_interior_rad_exchange
GPUSIM_FN void s0_interior_rad_exchange(
    int b,
    int b_size,
    int n_surf,
    int compute_ir,
    GPUSIM_THREAD const float* cur_dt_in,
    GPUSIM_THREAD const int* flags,
    GPUSIM_GLOBAL_CONST float* surf_f,
    GPUSIM_GLOBAL_CONST float* script_f_sigma,
    GPUSIM_THREAD float* q_net_lw,
    GPUSIM_THREAD float* ir_parent
) {
    float t_k[S0_MAX_SURF];
    float t_k2[S0_MAX_SURF];
    for (int s = 0; s < n_surf; ++s) {
        float tk = S0_T_REF_K + cur_dt_in[s];
        t_k[s] = tk;
        t_k2[s] = tk * tk;
    }
    for (int i = 0; i < n_surf; ++i) {
        if ((flags[i] & FLAG_SURF_MASK) == 0) {
            q_net_lw[i] = 0.0f;
            ir_parent[i] = 0.0f;
            continue;
        }
        float q_acc = 0.0f;
        float ir_acc = 0.0f;
        int want_ir = compute_ir && ((flags[i] & FLAG_IS_WINDOW) != 0);
        int row_off = i * n_surf;
        for (int j = 0; j < n_surf; ++j) {
            float sf = script_f_sigma[(row_off + j) * b_size + b];
            float diff_t4 = (cur_dt_in[j] - cur_dt_in[i]) * (t_k[j] + t_k[i]) *
                (t_k2[j] + t_k2[i]);
            q_acc += sf * diff_t4;
            if (want_ir) {
                ir_acc += sf * (t_k2[j] * t_k2[j]);
            }
        }
        q_net_lw[i] = q_acc;
        if (want_ir) {
            float eps_in = surf_f[(SS_EPS_IN * n_surf + i) * b_size + b];
            float safe_eps = (eps_in > 1.0e-12f) ? eps_in : 1.0e-12f;
            ir_parent[i] = ir_acc / safe_eps;
        } else {
            ir_parent[i] = 0.0f;
        }
    }
}

// HeatBalanceSurfaceManager.cc::InitSurfaceHeatBalance | calc_ctf_const_parts
GPUSIM_FN void s0_ctf_const_parts(
    int b,
    int b_size,
    int n_surf,
    int n_ctf_hist,
    GPUSIM_THREAD const int* flags,
    GPUSIM_GLOBAL_CONST float* ctf_vec,
    GPUSIM_GLOBAL_CONST float* state_ctf_hist,
    GPUSIM_THREAD float* ctf_const_in,
    GPUSIM_THREAD float* ctf_const_out
) {
    float bias_in = ctf_vec[4 * n_ctf_hist];
    float bias_out = ctf_vec[4 * n_ctf_hist + 1];
    for (int s = 0; s < n_surf; ++s) {
        if ((flags[s] & FLAG_IS_INTMASS) == 0) {
            ctf_const_in[s] = 0.0f;
            ctf_const_out[s] = 0.0f;
            continue;
        }
        float cin = bias_in;
        float cout = bias_out;
        for (int m = 0; m < n_ctf_hist; ++m) {
            float cx = ctf_vec[m];
            float cy = ctf_vec[n_ctf_hist + m];
            float cz = ctf_vec[2 * n_ctf_hist + m];
            float cf = ctf_vec[3 * n_ctf_hist + m];
            int idx_base = (m * n_surf + s) * b_size + b;
            int stride = n_ctf_hist * n_surf * b_size;
            float to_h = state_ctf_hist[CH_T_OUT_DT * stride + idx_base];
            float ti_h = state_ctf_hist[CH_T_IN_DT * stride + idx_base];
            float qo_h = state_ctf_hist[CH_Q_OUT * stride + idx_base];
            float qi_h = state_ctf_hist[CH_Q_IN * stride + idx_base];
            cin += cy * to_h - cz * ti_h + cf * qi_h;
            cout += cx * to_h - cy * ti_h + cf * qo_h;
        }
        ctf_const_in[s] = cin;
        ctf_const_out[s] = cout;
    }
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceOutsideSurf | calc_osc_outside_temp
GPUSIM_FN float s0_calc_osc_outside_temp(
    float dt_zone,
    float dt_out_surf_air,
    float c_const,
    float dt_const,
    float c_out,
    float c_zone,
    float osc_shift
) {
    return c_zone * dt_zone + c_out * dt_out_surf_air +
        c_const * dt_const + osc_shift;
}

// HeatBalanceSurfaceManager.cc::CalcOutsideSurfTemp | calc_outdoors_outside_temp
GPUSIM_FN float s0_calc_outdoors_outside_temp(
    float dt_zone,
    float dt_out_surf_air,
    float dt_sky,
    float dt_site,
    float dt_in_prev,
    float ctf_out0,
    float ctf_cross0,
    float ctf_in0,
    float ctf_const_out,
    float ctf_const_in,
    float h_c_ext,
    float h_air_ext,
    float h_sky_ext,
    float h_grd_ext,
    float h_conv_in,
    float q_rad_net_lw_in
) {
    float ext_num = -ctf_const_out + (h_c_ext + h_air_ext) * dt_out_surf_air +
        h_sky_ext * dt_sky + h_grd_ext * dt_site;
    float ext_den = ctf_out0 + h_c_ext + h_air_ext + h_sky_ext + h_grd_ext;
    if (ctf_cross0 > 0.01f) {
        float in_den = ctf_in0 + h_conv_in;
        float safe_in_den = (in_den > 1.0e-12f) ? in_den : 1.0e-12f;
        float f1 = ctf_cross0 / safe_in_den;
        float num = ext_num +
            f1 * (ctf_const_in + h_conv_in * dt_zone + q_rad_net_lw_in);
        float den = ext_den - f1 * ctf_cross0;
        return (den == 0.0f) ? 0.0f : (num / den);
    }
    float slow_num = ext_num + ctf_cross0 * dt_in_prev;
    return (ext_den == 0.0f) ? 0.0f : (slow_num / ext_den);
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2 | calc_inside_surface_step
GPUSIM_FN float s0_inside_surface_step(
    float dt_in_old,
    float dt_out_curr,
    float dt_zone,
    float h_conv_in,
    float q_rad_net_lw_in,
    float ctf_in0,
    float ctf_cross0,
    float ctf_const_in,
    int is_adiabatic
) {
    float temp_term = ctf_const_in + h_conv_in * dt_zone + q_rad_net_lw_in;
    float num = temp_term + S0_ITER_DAMP * dt_in_old;
    float den = ctf_in0 + h_conv_in + S0_ITER_DAMP;
    if (is_adiabatic) {
        den -= ctf_cross0;
    } else {
        num += ctf_cross0 * dt_out_curr;
    }
    return (den == 0.0f) ? num : (num / den);
}

// HeatBalanceSurfaceManager.cc::UpdateThermalHistories | update_ctf_histories
GPUSIM_FN void s0_update_ctf_histories(
    int b,
    int b_size,
    int n_surf,
    int n_ctf_hist,
    GPUSIM_THREAD const int* flags,
    GPUSIM_THREAD const float* cur_dt_out,
    GPUSIM_THREAD const float* cur_dt_in,
    GPUSIM_THREAD const float* ctf_const_in,
    GPUSIM_THREAD const float* ctf_const_out,
    GPUSIM_GLOBAL_CONST float* surf_f,
    GPUSIM_GLOBAL float* state_ctf_hist
) {
    int stride = n_ctf_hist * n_surf * b_size;
    for (int s = 0; s < n_surf; ++s) {
        if ((flags[s] & FLAG_IS_INTMASS) == 0) {
            continue;
        }
        float c_out0 = surf_f[(SS_CTF_OUT0 * n_surf + s) * b_size + b];
        float c_cross0 = surf_f[(SS_CTF_CROSS0 * n_surf + s) * b_size + b];
        float c_in0 = surf_f[(SS_CTF_IN0 * n_surf + s) * b_size + b];
        float qi_curr =
            cur_dt_out[s] * c_cross0 - cur_dt_in[s] * c_in0 + ctf_const_in[s];
        float qo_curr =
            cur_dt_out[s] * c_out0 - cur_dt_in[s] * c_cross0 + ctf_const_out[s];

        for (int m = n_ctf_hist - 1; m > 0; --m) {
            int dst_off = (m * n_surf + s) * b_size + b;
            int src_off = ((m - 1) * n_surf + s) * b_size + b;
            state_ctf_hist[CH_T_OUT_DT * stride + dst_off] =
                state_ctf_hist[CH_T_OUT_DT * stride + src_off];
            state_ctf_hist[CH_T_IN_DT * stride + dst_off] =
                state_ctf_hist[CH_T_IN_DT * stride + src_off];
            state_ctf_hist[CH_Q_OUT * stride + dst_off] =
                state_ctf_hist[CH_Q_OUT * stride + src_off];
            state_ctf_hist[CH_Q_IN * stride + dst_off] =
                state_ctf_hist[CH_Q_IN * stride + src_off];
        }
        int off0 = s * b_size + b;
        state_ctf_hist[CH_T_OUT_DT * stride + off0] = cur_dt_out[s];
        state_ctf_hist[CH_T_IN_DT * stride + off0] = cur_dt_in[s];
        state_ctf_hist[CH_Q_OUT * stride + off0] = qo_curr;
        state_ctf_hist[CH_Q_IN * stride + off0] = qi_curr;
    }
}

// ZoneEquipmentManager.cc::CalcAirFlowSimple | calc_ventilation_mcp
GPUSIM_FN void s0_calc_ventilation_mcp(
    float vent_vol_flow,
    float dt_out_zone,
    float out_hum_rat,
    float baro_press,
    GPUSIM_THREAD float* out_mcpv,
    GPUSIM_THREAD float* out_vamfl
) {
    float air_density = s0_psy_rho_air(
        baro_press, S0_T_REF_K + dt_out_zone, out_hum_rat
    );
    float cp_air = s0_psy_cp_air(out_hum_rat);
    float vvf = (vent_vol_flow > 0.0f) ? vent_vol_flow : 0.0f;
    float raw_mcpv = vvf * air_density * cp_air;
    float mcpv = (raw_mcpv > 0.0f) ? raw_mcpv : 0.0f;
    *out_mcpv = mcpv;
    *out_vamfl = mcpv / cp_air;
}

// ZoneTempPredictorCorrector.cc::predictSystemLoad | predict_zone_load
GPUSIM_FN float s0_predict_zone_load(
    float dt_zone_mat,
    float hum_rat,
    float baro_press,
    float zone_vol,
    float dt_sys_sec,
    GPUSIM_THREAD const float* dt_ztm,
    float sum_ha,
    float sum_hat_dt,
    float sum_mcp,
    float dt_out_zone,
    float sum_int_gain,
    float dt_heat_sp
) {
    float rho = s0_psy_rho_air(
        baro_press, S0_T_REF_K + dt_zone_mat, hum_rat
    );
    float cp = s0_psy_cp_air(hum_rat);
    float air_power_cap = zone_vol * rho * cp / dt_sys_sec;
    float dt0 = dt_ztm[0];
    float d1 = dt0 - dt_ztm[1];
    float d2 = dt_ztm[1] - dt_ztm[2];
    float hist_diff =
        air_power_cap * ((7.0f / 6.0f) * d1 - (1.0f / 3.0f) * d2);
    float cap_11_6 = (11.0f / 6.0f) * air_power_cap;
    float sum_ha_rel0 = sum_hat_dt - sum_ha * dt0;
    return (cap_11_6 + sum_ha) * (dt_heat_sp - dt0) +
        sum_mcp * (dt_heat_sp - dt_out_zone) -
        (hist_diff + sum_int_gain + sum_ha_rel0);
}

// PurchasedAirManager.cc::CalcPurchAirLoads | calc_ideal_loads_heating
GPUSIM_FN void s0_calc_ideal_loads_heating(
    float q_heat_req,
    float dt_zone_node,
    float w_zone_node,
    float baro_press,
    float dt_max_heat_sup,
    GPUSIM_THREAD float* out_m_dot_sup,
    GPUSIM_THREAD float* out_dt_sup,
    GPUSIM_THREAD float* out_w_sup,
    GPUSIM_THREAD float* out_sen_rate,
    GPUSIM_THREAD float* out_tot_rate
) {
    float cp_air = s0_psy_cp_air(w_zone_node);
    float delta_t = dt_max_heat_sup - dt_zone_node;
    float m_dot_sup = 0.0f;
    if (q_heat_req > 0.0f && delta_t > S0_SMALL_TEMP_DIFF) {
        float m_raw = q_heat_req / (cp_air * delta_t);
        if (m_raw > S0_VERY_SMALL_MASS_FLOW) {
            m_dot_sup = m_raw;
        }
    }
    if (m_dot_sup <= 0.0f) {
        *out_m_dot_sup = 0.0f;
        *out_dt_sup = dt_zone_node;
        *out_w_sup = w_zone_node;
        *out_sen_rate = 0.0f;
        *out_tot_rate = 0.0f;
        return;
    }
    float dt_sup = q_heat_req / (cp_air * m_dot_sup) + dt_zone_node;
    if (dt_sup > dt_max_heat_sup) {
        dt_sup = dt_max_heat_sup;
    }
    if (dt_sup < dt_zone_node) {
        dt_sup = dt_zone_node;
    }
    float w_sat = s0_psy_w_fn_tdb_rh_pb(dt_sup, 1.0f, baro_press);
    float w_sup = (w_zone_node < w_sat) ? w_zone_node : w_sat;
    float sen_out = m_dot_sup * cp_air * (dt_sup - dt_zone_node);
    float w_eff_s = (w_sup > 1.0e-5f) ? w_sup : 1.0e-5f;
    float w_eff_z = (w_zone_node > 1.0e-5f) ? w_zone_node : 1.0e-5f;
    float lat_out = m_dot_sup * (w_eff_s - w_eff_z) *
        (2.50094e6f + 1.85895e3f * (S0_T_REF_C + dt_sup));
    float sen_rate = (sen_out > 0.0f) ? sen_out : 0.0f;
    float tot_rate = sen_rate + ((lat_out > 0.0f) ? lat_out : 0.0f);
    *out_m_dot_sup = m_dot_sup;
    *out_dt_sup = dt_sup;
    *out_w_sup = w_sup;
    *out_sen_rate = sen_rate;
    *out_tot_rate = tot_rate;
}

// ZoneTempPredictorCorrector.cc::correctAirTemp | correct_zone_air_temp_and_humrat
GPUSIM_FN void s0_correct_air_temp_and_humrat(
    float dt_zone_mat,
    float hum_rat,
    float baro_press,
    float zone_vol,
    float dt_sys_sec,
    GPUSIM_THREAD const float* dt_ztm,
    GPUSIM_THREAD const float* w_prev,
    float sum_ha,
    float sum_hat_dt,
    float sum_mcp,
    float dt_out_zone,
    float sum_int_gain,
    float m_dot_sup,
    float dt_sup,
    float w_sup,
    float vamfl,
    float out_hum_rat,
    GPUSIM_THREAD float* out_dt_new,
    GPUSIM_THREAD float* out_w_new
) {
    float rho = s0_psy_rho_air(
        baro_press, S0_T_REF_K + dt_zone_mat, hum_rat
    );
    float cp = s0_psy_cp_air(hum_rat);
    float air_power_cap = zone_vol * rho * cp / dt_sys_sec;
    float sys_mcp = m_dot_sup * cp;
    float dt0 = dt_ztm[0];
    float d1 = dt0 - dt_ztm[1];
    float d2 = dt_ztm[1] - dt_ztm[2];
    float hist_diff =
        air_power_cap * ((7.0f / 6.0f) * d1 - (1.0f / 3.0f) * d2);
    float den_t = (11.0f / 6.0f) * air_power_cap + sum_ha + sum_mcp + sys_mcp;
    float sum_ha_rel0 = sum_hat_dt - sum_ha * dt0;
    float delta_num_t = sum_int_gain + sum_ha_rel0 +
        sum_mcp * (dt_out_zone - dt0) + sys_mcp * (dt_sup - dt0) + hist_diff;
    float dt_new = dt0 + delta_num_t / den_t;

    float rho_w = s0_psy_rho_air(baro_press, S0_T_REF_K + dt_new, hum_rat);
    float c_w = rho_w * zone_vol / dt_sys_sec;
    float w0 = w_prev[0];
    float dw1 = w0 - w_prev[1];
    float dw2 = w_prev[1] - w_prev[2];
    float w_hist_diff = c_w * ((7.0f / 6.0f) * dw1 - (1.0f / 3.0f) * dw2);
    float den_w = (11.0f / 6.0f) * c_w + m_dot_sup + vamfl;
    float delta_num_w = vamfl * (out_hum_rat - w0) + m_dot_sup * (w_sup - w0) +
        w_hist_diff;
    float w_new = w0 + delta_num_w / den_w;
    if (w_new < 0.0f) {
        w_new = 0.0f;
    }
    float w_sat = s0_psy_w_fn_tdb_rh_pb(dt_new, 1.0f, baro_press);
    if (w_new > w_sat) {
        w_new = w_sat;
    }
    *out_dt_new = dt_new;
    *out_w_new = w_new;
}

// ZoneTempPredictorCorrector.cc::DownInterpolate4HistoryValues | down_interpolate_4_history_values
GPUSIM_FN void s0_down_interpolate_4(
    float old_dt,
    float new_dt,
    GPUSIM_THREAD const float* old_vals,
    GPUSIM_THREAD float* new_vals
) {
    float ratio = old_dt / new_dt;
    float v0 = old_vals[0];
    float v1 = old_vals[1];
    float v2 = old_vals[2];
    float ts1 = 1.0f * new_dt;
    float ts2 = 2.0f * new_dt;
    float ts3 = 3.0f * new_dt;
    float ts4 = 4.0f * new_dt;
    float r2 = ratio - 2.0f;
    float r3 = ratio - 3.0f;
    if ((r2 < 0.0f ? -r2 : r2) < 0.01f) {
        float d10 = v1 - v0;
        float d21 = v2 - v1;
        new_vals[0] = v0 + d10 * (ts1 / old_dt);
        new_vals[1] = v0 + d10 * (ts2 / old_dt);
        new_vals[2] = v1 + d21 * ((ts3 - old_dt) / old_dt);
        new_vals[3] = v1 + d21 * ((ts4 - old_dt) / old_dt);
    } else if ((r3 < 0.0f ? -r3 : r3) < 0.01f) {
        float d10 = v1 - v0;
        float d21 = (v2 - v1) / old_dt;
        new_vals[0] = v0 + d10 * (ts1 / old_dt);
        new_vals[1] = v0 + d10 * (ts2 / old_dt);
        new_vals[2] = v0 + d10 * (ts3 / old_dt);
        new_vals[3] = v1 + d21 * ((ts4 - old_dt) / old_dt);
    } else {
        float d10 = v1 - v0;
        new_vals[0] = v0 + d10 * (ts1 / old_dt);
        new_vals[1] = v0 + d10 * (ts2 / old_dt);
        new_vals[2] = v0 + d10 * (ts3 / old_dt);
        new_vals[3] = v0 + d10 * (ts4 / old_dt);
    }
}

// HeatBalanceSurfaceManager.cc::ManageSurfaceHeatBalance | run_stage_a_batch::_step_one
GPUSIM_FN void s0_run_chunk_core(
    int b,
    GPUSIM_GLOBAL_CONST float* bldg_f,
    GPUSIM_GLOBAL_CONST int* bldg_i,
    GPUSIM_GLOBAL_CONST float* surf_f,
    GPUSIM_GLOBAL_CONST int* surf_flags,
    GPUSIM_GLOBAL_CONST float* script_f_sigma,
    GPUSIM_GLOBAL_CONST float* ctf_vec,
    GPUSIM_GLOBAL_CONST float* weather_buf,
    GPUSIM_GLOBAL_CONST float* sched_gain_w,
    GPUSIM_GLOBAL float* state_zone_f,
    GPUSIM_GLOBAL int* state_num_sys_last,
    GPUSIM_GLOBAL float* state_surf_f,
    GPUSIM_GLOBAL float* state_ctf_hist,
    GPUSIM_GLOBAL_CONST int* active_mask,
    GPUSIM_GLOBAL float* wu_stats,
    GPUSIM_GLOBAL float* hourly_heating_j,
    GPUSIM_GLOBAL float* zone_t_rec,
    GPUSIM_GLOBAL float* zone_ztav_rec,
    GPUSIM_GLOBAL_CONST int* params_i
) {
    int b_size = params_i[PI_B_SIZE];
    int n_surf = params_i[PI_N_SURF];
    int n_sites = params_i[PI_N_SITES];
    int n_ctf_hist = params_i[PI_N_CTF_HIST];
    int sph = params_i[PI_SPH];
    int step_start = params_i[PI_STEP_START];
    int step_end = params_i[PI_STEP_END];
    int is_warmup = params_i[PI_IS_WARMUP];
    int warmup_day = params_i[PI_WARMUP_DAY];
    int record_temp = params_i[PI_RECORD_TEMP];
    int rec_offset = params_i[PI_REC_STEP_OFFSET];
    int limit_num_sys = params_i[PI_LIMIT_NUM_SYS];
    int n_wsteps = params_i[PI_N_WSTEPS];

    if (is_warmup && active_mask[b] == 0) {
        return;
    }

    int site_idx = bldg_i[BI_SITE_IDX * b_size + b];
    int has_window = bldg_i[BI_HAS_WINDOW * b_size + b];
    float zone_vol = bldg_f[BF_ZONE_VOLUME * b_size + b];
    float zone_lapse = bldg_f[BF_ZONE_LAPSE_OFFSET * b_size + b];
    float vent_flow = bldg_f[BF_VENT_FLOW_M3S * b_size + b];
    float dt_heat_sp = bldg_f[BF_HEAT_SP_DT * b_size + b];
    float dt_max_sup = bldg_f[BF_MAX_HEAT_SUP_DT * b_size + b];
    float h_min = bldg_f[BF_H_CONV_MIN * b_size + b];

    float dt_zone_hr = 1.0f / (float)sph;
    float dt_zone_sec = 3600.0f / (float)sph;

    float dt_mat = state_zone_f[ZS_T_MAT_DT * b_size + b];
    float w_zone = state_zone_f[ZS_W_ZONE * b_size + b];
    float w_zone_avg = state_zone_f[ZS_W_ZONE_AVG * b_size + b];
    float dt_xmat[4];
    float dt_dsxmat[4];
    float w_prev[4];
    float dsw_prev[4];
    for (int k = 0; k < 4; ++k) {
        dt_xmat[k] = state_zone_f[(ZS_XMAT0 + k) * b_size + b];
        dt_dsxmat[k] = state_zone_f[(ZS_DSXMAT0 + k) * b_size + b];
        w_prev[k] = state_zone_f[(ZS_W_PREV0 + k) * b_size + b];
        dsw_prev[k] = state_zone_f[(ZS_DSW_PREV0 + k) * b_size + b];
    }
    int num_sys_last = state_num_sys_last[b];

    float cur_dt_in[S0_MAX_SURF];
    float cur_dt_out[S0_MAX_SURF];
    float theta1_win[S0_MAX_SURF];
    float theta2_win[S0_MAX_SURF];
    int flags[S0_MAX_SURF];
    for (int s = 0; s < n_surf; ++s) {
        int s_off = s * b_size + b;
        int surf_stride = n_surf * b_size;
        cur_dt_in[s] = state_surf_f[ST_SURF_DT_IN * surf_stride + s_off];
        cur_dt_out[s] = state_surf_f[ST_SURF_DT_OUT * surf_stride + s_off];
        theta1_win[s] = state_surf_f[ST_DTH1_WIN * surf_stride + s_off];
        theta2_win[s] = state_surf_f[ST_DTH2_WIN * surf_stride + s_off];
        flags[s] = surf_flags[s_off];
    }

    float day_max_dt = -9999.0f;
    float day_min_dt = 1000.0f;
    float day_max_h = -9999.0f;
    int cur_hour = -1;
    float hour_energy_acc = 0.0f;

    float dt_out_surf_air[S0_MAX_SURF];
    float cur_h_in[S0_MAX_SURF];
    float ctf_const_in[S0_MAX_SURF];
    float ctf_const_out[S0_MAX_SURF];
    float q_net_lw[S0_MAX_SURF];
    float ir_parent[S0_MAX_SURF];
    float dt_in_old[S0_MAX_SURF];
    float new_dth1[S0_MAX_SURF];
    float new_dth2[S0_MAX_SURF];

    for (int step = step_start; step < step_end; ++step) {
        int w_idx = step * n_sites + site_idx;
        int wf_stride = n_wsteps * n_sites;
        float dt_site = weather_buf[WF_DT_DB * wf_stride + w_idx];
        float w_site = weather_buf[WF_HUM_RAT * wf_stride + w_idx];
        float pb_site = weather_buf[WF_BARO_PRESS * wf_stride + w_idx];
        float dt_sky = weather_buf[WF_DT_SKY * wf_stride + w_idx];
        int hour_idx = step / sph;
        float gain_w = sched_gain_w[hour_idx * b_size + b];
        int begin_envrn = (is_warmup && warmup_day == 1 && step == 0) ? 1 : 0;

        float dt_out_zone_air = dt_site + zone_lapse;
        for (int s = 0; s < n_surf; ++s) {
            int sb_idx = s * b_size + b;
            dt_out_surf_air[s] =
                dt_site + surf_f[(SS_LAPSE_OFFSET * n_surf * b_size) + sb_idx];
            if ((flags[s] & FLAG_SURF_MASK) == 0) {
                cur_h_in[s] = 0.0f;
                continue;
            }
            float cos_tilt = surf_f[(SS_COS_TILT * n_surf * b_size) + sb_idx];
            if ((flags[s] & FLAG_IS_WINDOW) != 0) {
                float sin_tilt =
                    surf_f[(SS_SIN_TILT * n_surf * b_size) + sb_idx];
                float tilt_deg =
                    surf_f[(SS_TILT_DEG * n_surf * b_size) + sb_idx];
                float height = surf_f[(SS_HEIGHT * n_surf * b_size) + sb_idx];
                cur_h_in[s] = s0_iso15099_win_int_conv(
                    cur_dt_in[s],
                    dt_mat,
                    w_zone_avg,
                    pb_site,
                    height,
                    tilt_deg,
                    sin_tilt,
                    h_min
                );
            } else {
                cur_h_in[s] = s0_inside_conv_opaque(
                    cur_dt_in[s], dt_mat, cos_tilt, h_min
                );
            }
        }

        s0_ctf_const_parts(
            b,
            b_size,
            n_surf,
            n_ctf_hist,
            flags,
            ctf_vec,
            state_ctf_hist,
            ctf_const_in,
            ctf_const_out
        );

        s0_interior_rad_exchange(
            b,
            b_size,
            n_surf,
            0,
            cur_dt_in,
            flags,
            surf_f,
            script_f_sigma,
            q_net_lw,
            ir_parent
        );

        for (int s = 0; s < n_surf; ++s) {
            int fl = flags[s];
            int sb_idx = s * b_size + b;
            int ss_stride = n_surf * b_size;
            if ((fl & FLAG_IS_OSC) != 0) {
                float c_const = surf_f[SS_OSC_C_CONST * ss_stride + sb_idx];
                float dt_const =
                    surf_f[SS_OSC_T_CONST_DT * ss_stride + sb_idx];
                float c_out = surf_f[SS_OSC_C_OUT * ss_stride + sb_idx];
                float c_zone = surf_f[SS_OSC_C_ZONE * ss_stride + sb_idx];
                float osc_sh = surf_f[SS_OSC_SHIFT * ss_stride + sb_idx];
                cur_dt_out[s] = s0_calc_osc_outside_temp(
                    dt_mat,
                    dt_out_surf_air[s],
                    c_const,
                    dt_const,
                    c_out,
                    c_zone,
                    osc_sh
                );
            } else if ((fl & FLAG_IS_OUTDOORS_OP) != 0) {
                float cos_t = surf_f[SS_COS_TILT * ss_stride + sb_idx];
                float eps_o = surf_f[SS_EPS_OUT * ss_stride + sb_idx];
                float vf_sky = surf_f[SS_VF_SKY_IR * ss_stride + sb_idx];
                float vf_grd = surf_f[SS_VF_GROUND_IR * ss_stride + sb_idx];
                float split = surf_f[SS_AIR_SKY_SPLIT * ss_stride + sb_idx];
                float c_out0 = surf_f[SS_CTF_OUT0 * ss_stride + sb_idx];
                float c_cross0 = surf_f[SS_CTF_CROSS0 * ss_stride + sb_idx];
                float c_in0 = surf_f[SS_CTF_IN0 * ss_stride + sb_idx];
                float hc_ext = s0_outside_conv_doe2(
                    cur_dt_out[s], dt_out_surf_air[s], cos_t
                );
                float h_sky = 0.0f;
                float h_grd = 0.0f;
                float h_air = 0.0f;
                s0_outside_rad_coeffs(
                    cur_dt_out[s],
                    dt_out_surf_air[s],
                    dt_sky,
                    eps_o,
                    vf_sky,
                    vf_grd,
                    split,
                    &h_sky,
                    &h_grd,
                    &h_air
                );
                cur_dt_out[s] = s0_calc_outdoors_outside_temp(
                    dt_mat,
                    dt_out_surf_air[s],
                    dt_sky,
                    dt_site,
                    cur_dt_in[s],
                    c_out0,
                    c_cross0,
                    c_in0,
                    ctf_const_out[s],
                    ctf_const_in[s],
                    hc_ext,
                    h_air,
                    h_sky,
                    h_grd,
                    cur_h_in[s],
                    q_net_lw[s]
                );
            } else if ((fl & FLAG_IS_INTMASS) != 0) {
                cur_dt_out[s] = cur_dt_in[s];
            }
            new_dth1[s] = theta1_win[s];
            new_dth2[s] = theta2_win[s];
        }

        for (int it = 0; it < S0_MAX_ITERS; ++it) {
            for (int s = 0; s < n_surf; ++s) {
                dt_in_old[s] = cur_dt_in[s];
            }
            s0_interior_rad_exchange(
                b,
                b_size,
                n_surf,
                (it == 0 && has_window) ? 1 : 0,
                cur_dt_in,
                flags,
                surf_f,
                script_f_sigma,
                q_net_lw,
                ir_parent
            );
            if (it > 0 && (it % S0_REEVAL_CONV) == 0) {
                for (int s = 0; s < n_surf; ++s) {
                    if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                        float cos_t = surf_f
                            [(SS_COS_TILT * n_surf + s) * b_size + b];
                        cur_h_in[s] = s0_inside_conv_opaque(
                            cur_dt_in[s], dt_mat, cos_t, h_min
                        );
                    }
                }
            }
            if (it == 0 && has_window) {
                for (int s = 0; s < n_surf; ++s) {
                    if ((flags[s] & FLAG_IS_WINDOW) != 0) {
                        int sb_idx = s * b_size + b;
                        int ss_stride = n_surf * b_size;
                        float cos_t = surf_f[SS_COS_TILT * ss_stride + sb_idx];
                        float sin_t = surf_f[SS_SIN_TILT * ss_stride + sb_idx];
                        float tilt_d =
                            surf_f[SS_TILT_DEG * ss_stride + sb_idx];
                        float height = surf_f[SS_HEIGHT * ss_stride + sb_idx];
                        float eps_in = surf_f[SS_EPS_IN * ss_stride + sb_idx];
                        float eps_out =
                            surf_f[SS_EPS_OUT * ss_stride + sb_idx];
                        float vf_sky =
                            surf_f[SS_VF_SKY_IR * ss_stride + sb_idx];
                        float vf_grd =
                            surf_f[SS_VF_GROUND_IR * ss_stride + sb_idx];
                        float split =
                            surf_f[SS_AIR_SKY_SPLIT * ss_stride + sb_idx];
                        float scon = surf_f[SS_SCON_WIN * ss_stride + sb_idx];
                        float hc_ext_w = s0_outside_conv_doe2(
                            cur_dt_out[s], dt_out_surf_air[s], cos_t
                        );
                        float dth1_i = new_dth1[s];
                        float dth2_i = new_dth2[s];
                        if (begin_envrn) {
                            s0_starting_window_temps(
                                dt_mat,
                                dt_out_surf_air[s],
                                cur_h_in[s],
                                hc_ext_w,
                                scon,
                                &dth1_i,
                                &dth2_i
                            );
                        }
                        float w_tin = 0.0f;
                        float w_tout = 0.0f;
                        float w_hin = 0.0f;
                        float w_d1 = 0.0f;
                        float w_d2 = 0.0f;
                        s0_solve_simple_window(
                            dt_mat,
                            dt_out_surf_air[s],
                            dt_sky,
                            w_zone_avg,
                            pb_site,
                            hc_ext_w,
                            ir_parent[s],
                            scon,
                            eps_out,
                            eps_in,
                            vf_sky,
                            vf_grd,
                            split,
                            height,
                            tilt_d,
                            sin_t,
                            h_min,
                            dth1_i,
                            dth2_i,
                            &w_tin,
                            &w_tout,
                            &w_hin,
                            &w_d1,
                            &w_d2
                        );
                        cur_dt_in[s] = w_tin;
                        cur_dt_out[s] = w_tout;
                        cur_h_in[s] = w_hin;
                        new_dth1[s] = w_d1;
                        new_dth2[s] = w_d2;
                    }
                }
            }

            float max_del_t = 0.0f;
            for (int s = 0; s < n_surf; ++s) {
                if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                    int sb_idx = s * b_size + b;
                    int ss_stride = n_surf * b_size;
                    float c_in0 = surf_f[SS_CTF_IN0 * ss_stride + sb_idx];
                    float c_cross0 = surf_f[SS_CTF_CROSS0 * ss_stride + sb_idx];
                    int is_ad = ((flags[s] & FLAG_IS_INTMASS) != 0) ? 1 : 0;
                    float op_dt = s0_inside_surface_step(
                        dt_in_old[s],
                        cur_dt_out[s],
                        dt_mat,
                        cur_h_in[s],
                        q_net_lw[s],
                        c_in0,
                        c_cross0,
                        ctf_const_in[s],
                        is_ad
                    );
                    cur_dt_in[s] = op_dt;
                    float del = op_dt - dt_in_old[s];
                    float abs_d = (del < 0.0f) ? -del : del;
                    if (abs_d > max_del_t) {
                        max_del_t = abs_d;
                    }
                }
            }
            if (max_del_t <= S0_MAX_DEL_T) {
                break;
            }
        }

        float sum_ha = 0.0f;
        float sum_hat_dt = 0.0f;
        for (int s = 0; s < n_surf; ++s) {
            if ((flags[s] & FLAG_SURF_MASK) != 0) {
                float area = surf_f[(SS_AREA * n_surf + s) * b_size + b];
                float ha = cur_h_in[s] * area;
                sum_ha += ha;
                sum_hat_dt += ha * cur_dt_in[s];
            }
        }

        float mcpv = 0.0f;
        float vamfl = 0.0f;
        s0_calc_ventilation_mcp(
            vent_flow, dt_out_zone_air, w_site, pb_site, &mcpv, &vamfl
        );

        float q_load_h = s0_predict_zone_load(
            dt_mat,
            w_zone,
            pb_site,
            zone_vol,
            dt_zone_sec,
            dt_xmat,
            sum_ha,
            sum_hat_dt,
            mcpv,
            dt_out_zone_air,
            gain_w,
            dt_heat_sp
        );
        float m_sup = 0.0f;
        float dt_sup = 0.0f;
        float w_sup = 0.0f;
        float sen_heat = 0.0f;
        float tot_heat = 0.0f;
        s0_calc_ideal_loads_heating(
            q_load_h,
            dt_mat,
            w_zone,
            pb_site,
            dt_max_sup,
            &m_sup,
            &dt_sup,
            &w_sup,
            &sen_heat,
            &tot_heat
        );
        float dt_new = 0.0f;
        float w_new = 0.0f;
        s0_correct_air_temp_and_humrat(
            dt_mat,
            w_zone,
            pb_site,
            zone_vol,
            dt_zone_sec,
            dt_xmat,
            w_prev,
            sum_ha,
            sum_hat_dt,
            mcpv,
            dt_out_zone_air,
            gain_w,
            m_sup,
            dt_sup,
            w_sup,
            vamfl,
            w_site,
            &dt_new,
            &w_new
        );

        float t_chg = dt_new - dt_xmat[0];
        float abs_t_chg = (t_chg < 0.0f) ? -t_chg : t_chg;
        float dt_ztav = dt_new;
        float w_avg = w_new;
        float heat_energy_j = tot_heat * dt_zone_sec;
        float sn_heat_rate = sen_heat;
        int new_num_sys = 1;

        if (abs_t_chg > S0_MAX_ZONE_TEMP_DIFF) {
            int n_sub = (int)(abs_t_chg / S0_MAX_ZONE_TEMP_DIFF + 1.0f);
            if (n_sub > limit_num_sys) {
                n_sub = limit_num_sys;
            }
            float dt_sub_hr = dt_zone_hr / (float)n_sub;
            if (dt_sub_hr < S0_MIN_TIME_STEP_SYS_HR) {
                dt_sub_hr = S0_MIN_TIME_STEP_SYS_HR;
            }
            float dt_sub_sec = dt_sub_hr * 3600.0f;
            float frac_sub = dt_sub_hr / dt_zone_hr;
            new_num_sys = n_sub;

            float b_mat = dt_xmat[0];
            float b_w = w_prev[0];
            float b_dsx[4];
            float b_dsw[4];
            if (n_sub != num_sys_last) {
                s0_down_interpolate_4(dt_zone_hr, dt_sub_hr, dt_xmat, b_dsx);
                s0_down_interpolate_4(dt_zone_hr, dt_sub_hr, w_prev, b_dsw);
            } else {
                for (int k = 0; k < 4; ++k) {
                    b_dsx[k] = dt_dsxmat[k];
                    b_dsw[k] = dsw_prev[k];
                }
            }

            float acc_zt = 0.0f;
            float acc_w = 0.0f;
            float acc_e = 0.0f;
            float acc_sen = 0.0f;
            for (int k_sub = 0; k_sub < n_sub; ++k_sub) {
                float ql_s = s0_predict_zone_load(
                    b_mat,
                    b_w,
                    pb_site,
                    zone_vol,
                    dt_sub_sec,
                    b_dsx,
                    sum_ha,
                    sum_hat_dt,
                    mcpv,
                    dt_out_zone_air,
                    gain_w,
                    dt_heat_sp
                );
                float ms_s = 0.0f;
                float ts_s = 0.0f;
                float ws_s = 0.0f;
                float sh_s = 0.0f;
                float th_s = 0.0f;
                s0_calc_ideal_loads_heating(
                    ql_s,
                    b_mat,
                    b_w,
                    pb_site,
                    dt_max_sup,
                    &ms_s,
                    &ts_s,
                    &ws_s,
                    &sh_s,
                    &th_s
                );
                float zt_s = 0.0f;
                float wn_s = 0.0f;
                s0_correct_air_temp_and_humrat(
                    b_mat,
                    b_w,
                    pb_site,
                    zone_vol,
                    dt_sub_sec,
                    b_dsx,
                    b_dsw,
                    sum_ha,
                    sum_hat_dt,
                    mcpv,
                    dt_out_zone_air,
                    gain_w,
                    ms_s,
                    ts_s,
                    ws_s,
                    vamfl,
                    w_site,
                    &zt_s,
                    &wn_s
                );
                b_mat = zt_s;
                b_w = wn_s;
                b_dsx[3] = b_dsx[2];
                b_dsx[2] = b_dsx[1];
                b_dsx[1] = b_dsx[0];
                b_dsx[0] = b_mat;
                b_dsw[3] = b_dsw[2];
                b_dsw[2] = b_dsw[1];
                b_dsw[1] = b_dsw[0];
                b_dsw[0] = b_w;
                acc_zt += b_mat * frac_sub;
                acc_w += b_w * frac_sub;
                acc_e += th_s * dt_sub_sec;
                acc_sen += sh_s * frac_sub;
            }
            dt_new = b_mat;
            w_new = b_w;
            dt_ztav = acc_zt;
            w_avg = acc_w;
            heat_energy_j = acc_e;
            sn_heat_rate = acc_sen;
            for (int k = 0; k < 4; ++k) {
                dt_dsxmat[k] = b_dsx[k];
                dsw_prev[k] = b_dsw[k];
            }
        }

        dt_xmat[3] = dt_xmat[2];
        dt_xmat[2] = dt_xmat[1];
        dt_xmat[1] = dt_xmat[0];
        dt_xmat[0] = dt_ztav;
        w_prev[3] = w_prev[2];
        w_prev[2] = w_prev[1];
        w_prev[1] = w_prev[0];
        w_prev[0] = w_avg;

        s0_update_ctf_histories(
            b,
            b_size,
            n_surf,
            n_ctf_hist,
            flags,
            cur_dt_out,
            cur_dt_in,
            ctf_const_in,
            ctf_const_out,
            surf_f,
            state_ctf_hist
        );

        dt_mat = dt_new;
        w_zone = w_new;
        w_zone_avg = w_avg;
        num_sys_last = new_num_sys;
        for (int s = 0; s < n_surf; ++s) {
            theta1_win[s] = new_dth1[s];
            theta2_win[s] = new_dth2[s];
        }

        if (is_warmup) {
            if (dt_ztav > day_max_dt) {
                day_max_dt = dt_ztav;
            }
            if (dt_ztav < day_min_dt) {
                day_min_dt = dt_ztav;
            }
            if (sn_heat_rate > day_max_h) {
                day_max_h = sn_heat_rate;
            }
        } else {
            if (hour_idx != cur_hour) {
                if (cur_hour >= 0) {
                    hourly_heating_j[cur_hour * b_size + b] += hour_energy_acc;
                }
                cur_hour = hour_idx;
                hour_energy_acc = heat_energy_j;
            } else {
                hour_energy_acc += heat_energy_j;
            }
            if (record_temp) {
                int rec_idx = (step - rec_offset) * b_size + b;
                zone_t_rec[rec_idx] = dt_mat;
                zone_ztav_rec[rec_idx] = dt_ztav;
            }
        }
    }

    if (is_warmup) {
        wu_stats[WU_STAT_MAX_T_DT * b_size + b] = day_max_dt;
        wu_stats[WU_STAT_MIN_T_DT * b_size + b] = day_min_dt;
        wu_stats[WU_STAT_MAX_H_RATE * b_size + b] = day_max_h;
    } else if (cur_hour >= 0) {
        hourly_heating_j[cur_hour * b_size + b] += hour_energy_acc;
    }

    state_zone_f[ZS_T_MAT_DT * b_size + b] = dt_mat;
    state_zone_f[ZS_W_ZONE * b_size + b] = w_zone;
    state_zone_f[ZS_W_ZONE_AVG * b_size + b] = w_zone_avg;
    for (int k = 0; k < 4; ++k) {
        state_zone_f[(ZS_XMAT0 + k) * b_size + b] = dt_xmat[k];
        state_zone_f[(ZS_DSXMAT0 + k) * b_size + b] = dt_dsxmat[k];
        state_zone_f[(ZS_W_PREV0 + k) * b_size + b] = w_prev[k];
        state_zone_f[(ZS_DSW_PREV0 + k) * b_size + b] = dsw_prev[k];
    }
    state_num_sys_last[b] = num_sys_last;

    int surf_stride = n_surf * b_size;
    for (int s = 0; s < n_surf; ++s) {
        int s_off = s * b_size + b;
        state_surf_f[ST_SURF_DT_IN * surf_stride + s_off] = cur_dt_in[s];
        state_surf_f[ST_SURF_DT_OUT * surf_stride + s_off] = cur_dt_out[s];
        state_surf_f[ST_DTH1_WIN * surf_stride + s_off] = theta1_win[s];
        state_surf_f[ST_DTH2_WIN * surf_stride + s_off] = theta2_win[s];
    }
}

#endif
