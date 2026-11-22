#ifndef GPUSIM_SPIKE_COMMON_H
#define GPUSIM_SPIKE_COMMON_H

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
#endif

#define SPIKE_MAX_SURF 16
#define SPIKE_T_REF_K 293.15f
#define SPIKE_SIGMA 5.6697e-8f
#define SPIKE_ITER_DAMP 5.0f
#define SPIKE_MAX_ITERS 500
#define SPIKE_REEVAL_CONV 30
#define SPIKE_MAX_DEL_T 0.002f
#define SPIKE_WIN_MAX_ITER 100
#define SPIKE_WIN_ERR_TOL 0.02f

#define ZF_DT_MAT 0
#define ZF_W_ZONE_AVG 1
#define ZF_PB_SITE 2
#define ZF_DT_SKY 3
#define ZF_H_MIN 4
#define ZF_BEGIN_ENVRN 5

#define SF_DT_IN_INIT 0
#define SF_DT_OUT_INIT 1
#define SF_H_CONV_IN_INIT 2
#define SF_DTH1_INIT 3
#define SF_DTH2_INIT 4
#define SF_DT_OUT_SURF_AIR 5
#define SF_EPS_IN 6
#define SF_EPS_OUT 7
#define SF_COS_TILT 8
#define SF_SIN_TILT 9
#define SF_TILT_DEG 10
#define SF_HEIGHT 11
#define SF_VF_SKY_IR 12
#define SF_VF_GROUND_IR 13
#define SF_AIR_SKY_SPLIT 14
#define SF_SCON_WIN 15
#define SF_CTF_IN0 16
#define SF_CTF_CROSS0 17
#define SF_CTF_CONST_IN_SHIFTED 18

#define OF_DT_IN_OUT 0
#define OF_DT_OUT_OUT 1
#define OF_H_CONV_IN_OUT 2
#define OF_DTH1_OUT 3
#define OF_DTH2_OUT 4

#define FLAG_SURF_MASK 1
#define FLAG_IS_WINDOW 2
#define FLAG_IS_NON_WINDOW 4
#define FLAG_IS_INTMASS 8

// Psychrometrics.hh::PsyRhoAirFnPbTdbW
GPUSIM_FN float spike_psy_rho_air(float pb, float t_k, float dw) {
    float w = (dw > 1.0e-5f) ? dw : 1.0e-5f;
    return pb / (287.0f * t_k * (1.0f + 1.6077687f * w));
}

// Psychrometrics.hh::PsyCpAirFnW
GPUSIM_FN float spike_psy_cp_air(float dw) {
    float w = (dw > 1.0e-5f) ? dw : 1.0e-5f;
    return 1.00484e3f + w * 1.85895e3f;
}

// ConvectionCoefficients.cc::CalcASHRAETARPNatural
GPUSIM_FN float spike_ashrae_tarp_natural(
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

// ConvectionCoefficients.cc::CalcASHRAEDetailedIntConvCoeff
GPUSIM_FN float spike_inside_conv_opaque(
    float dt_surf,
    float dt_zone,
    float cos_tilt,
    float h_min
) {
    float h_nat = spike_ashrae_tarp_natural(dt_surf, dt_zone, -cos_tilt);
    return (h_nat > h_min) ? h_nat : h_min;
}

// ConvectionCoefficients.cc::InitExteriorConvectionCoeff
GPUSIM_FN float spike_outside_conv_doe2(
    float dt_surf,
    float dt_air,
    float cos_tilt
) {
    return spike_ashrae_tarp_natural(dt_surf, dt_air, cos_tilt);
}

// ConvectionCoefficients.cc::CalcISO15099WindowIntConvCoeff
GPUSIM_FN float spike_iso15099_win_int_conv(
    float dt_surf,
    float dt_air,
    float hum_rat,
    float baro_press,
    float height,
    float tilt_deg,
    float sin_tilt,
    float h_min
) {
    float t_surf_k = SPIKE_T_REF_K + dt_surf;
    float t_air_k = SPIKE_T_REF_K + dt_air;
    float delta_t = dt_surf - dt_air;
    if (t_air_k < 200.0f || t_air_k > 400.0f || t_surf_k < 180.0f ||
        t_surf_k > 450.0f) {
        return h_min;
    }
    float t_film_k = t_air_k + 0.25f * delta_t;
    float rho = spike_psy_rho_air(baro_press, t_film_k, hum_rat);
    float lam = 2.873e-3f + 7.76e-5f * t_film_k;
    float mu = 3.723e-6f + 4.94e-8f * t_film_k;
    float cp = spike_psy_cp_air(hum_rat);
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

// WindowManager.cc::CalcWindowHeatBalanceInternalRoutines
GPUSIM_FN float spike_window_outside_ir(
    float t_out_k,
    float t_sky_k,
    float vf_sky_ir,
    float vf_ground_ir,
    float air_sky_split
) {
    float t_out2 = t_out_k * t_out_k;
    float eb_out = SPIKE_SIGMA * (t_out2 * t_out2);
    float t_sky2 = t_sky_k * t_sky_k;
    float eb_sky = SPIKE_SIGMA * (t_sky2 * t_sky2);
    return vf_sky_ir *
        (air_sky_split * eb_sky + (1.0f - air_sky_split) * eb_out) +
        vf_ground_ir * eb_out;
}

// WindowManager.cc::StartingWindowTemps
GPUSIM_FN void spike_starting_window_temps(
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

// WindowManager.cc::SolveForWindowTemperatures
GPUSIM_FN void spike_solve_simple_window(
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
    float t_out_k = SPIKE_T_REF_K + dt_out;
    float t_sky_k = SPIKE_T_REF_K + dt_sky;
    float out_ir = spike_window_outside_ir(
        t_out_k, t_sky_k, vf_sky_ir, vf_ground_ir, air_sky_split
    );
    float dth1 = dth1_init;
    float dth2 = dth2_init;
    float h_in = 3.0f;
    for (int it = 0; it < SPIKE_WIN_MAX_ITER; ++it) {
        float th1 = SPIKE_T_REF_K + dth1;
        float th2 = SPIKE_T_REF_K + dth2;
        float hr1 = eps_out * SPIKE_SIGMA * (th1 * th1 * th1);
        float hr2 = eps_in * SPIKE_SIGMA * (th2 * th2 * th2);
        h_in = spike_iso15099_win_int_conv(
            dth2, dt_in, hum_rat, baro_press, height, tilt_deg, sin_tilt, h_min
        );
        float a11 = hr1 + scon + h_out;
        float a22 = hr2 + scon + h_in;
        float rhs1 = eps_out * out_ir - hr1 * SPIKE_T_REF_K + h_out * dt_out;
        float rhs2 = eps_in * rmir - hr2 * SPIKE_T_REF_K + h_in * dt_in;
        float det =
            (hr1 + h_out) * (hr2 + h_in) + scon * (hr1 + h_out + hr2 + h_in);
        float d_sol1 = (a22 * rhs1 + scon * rhs2) / det;
        float d_sol2 = (scon * rhs1 + a11 * rhs2) / det;
        float w_old = (it + 1 < (SPIKE_WIN_MAX_ITER / 4)) ? 0.5f : 0.75f;
        float w_new = 1.0f - w_old;
        float new_dth1 = w_old * dth1 + w_new * d_sol1;
        float new_dth2 = w_old * dth2 + w_new * d_sol2;
        float e1 = new_dth1 - dth1;
        float e2 = new_dth2 - dth2;
        float err = 0.5f * ((e1 < 0.0f ? -e1 : e1) + (e2 < 0.0f ? -e2 : e2));
        dth1 = new_dth1;
        dth2 = new_dth2;
        if (err <= SPIKE_WIN_ERR_TOL) {
            break;
        }
    }
    *out_dt_in = dth2;
    *out_dt_out = dth1;
    *out_h_in = h_in;
    *out_dth1 = dth1;
    *out_dth2 = dth2;
}

// HeatBalanceIntRadExchange.cc::CalcInteriorRadExchange
GPUSIM_FN void spike_interior_rad_exchange(
    int b,
    int b_size,
    int n_surf,
    int compute_ir,
    GPUSIM_THREAD const float* cur_dt_in,
    GPUSIM_THREAD const int* flags,
    GPUSIM_GLOBAL_CONST float* surf_in,
    GPUSIM_GLOBAL_CONST float* script_f_sigma,
    GPUSIM_THREAD float* q_net_lw,
    GPUSIM_THREAD float* ir_parent
) {
    float t_k[SPIKE_MAX_SURF];
    float t_k2[SPIKE_MAX_SURF];
    for (int s = 0; s < n_surf; ++s) {
        float tk = SPIKE_T_REF_K + cur_dt_in[s];
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
            float eps_in = surf_in[(SF_EPS_IN * n_surf + i) * b_size + b];
            float safe_eps = (eps_in > 1.0e-12f) ? eps_in : 1.0e-12f;
            ir_parent[i] = ir_acc / safe_eps;
        } else {
            ir_parent[i] = 0.0f;
        }
    }
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2
GPUSIM_FN float spike_inside_surface_step(
    float dt_in_old,
    float dt_out_curr,
    float dt_zone,
    float h_conv_in,
    float q_rad_net_lw_in,
    float ctf_in0,
    float ctf_cross0,
    float ctf_const_in_shifted,
    int is_adiabatic
) {
    float temp_term =
        ctf_const_in_shifted + h_conv_in * dt_zone + q_rad_net_lw_in;
    float num = temp_term + SPIKE_ITER_DAMP * dt_in_old;
    float den = ctf_in0 + h_conv_in + SPIKE_ITER_DAMP;
    if (is_adiabatic) {
        den -= ctf_cross0;
    } else {
        num += ctf_cross0 * dt_out_curr;
    }
    return (den == 0.0f) ? num : (num / den);
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2CTFOnly
GPUSIM_FN void spike_inside_surface_iterate_core(
    int b,
    int b_size,
    int n_surf,
    GPUSIM_GLOBAL_CONST float* zone_in,
    GPUSIM_GLOBAL_CONST float* surf_in,
    GPUSIM_GLOBAL_CONST int* surf_flags,
    GPUSIM_GLOBAL_CONST float* script_f_sigma,
    GPUSIM_GLOBAL float* surf_out,
    GPUSIM_GLOBAL int* iter_out
) {
    float dt_mat = zone_in[ZF_DT_MAT * b_size + b];
    float w_zone_avg = zone_in[ZF_W_ZONE_AVG * b_size + b];
    float pb_site = zone_in[ZF_PB_SITE * b_size + b];
    float dt_sky = zone_in[ZF_DT_SKY * b_size + b];
    float h_min = zone_in[ZF_H_MIN * b_size + b];
    int begin_envrn = (zone_in[ZF_BEGIN_ENVRN * b_size + b] > 0.5f) ? 1 : 0;

    float cur_dt_in[SPIKE_MAX_SURF];
    float cur_dt_out[SPIKE_MAX_SURF];
    float cur_h_in[SPIKE_MAX_SURF];
    float new_dth1[SPIKE_MAX_SURF];
    float new_dth2[SPIKE_MAX_SURF];
    float dt_in_old[SPIKE_MAX_SURF];
    float q_net_lw[SPIKE_MAX_SURF];
    float ir_parent[SPIKE_MAX_SURF];
    int flags[SPIKE_MAX_SURF];
    int has_window = 0;

    for (int s = 0; s < n_surf; ++s) {
        cur_dt_in[s] = surf_in[(SF_DT_IN_INIT * n_surf + s) * b_size + b];
        cur_dt_out[s] = surf_in[(SF_DT_OUT_INIT * n_surf + s) * b_size + b];
        cur_h_in[s] = surf_in[(SF_H_CONV_IN_INIT * n_surf + s) * b_size + b];
        new_dth1[s] = surf_in[(SF_DTH1_INIT * n_surf + s) * b_size + b];
        new_dth2[s] = surf_in[(SF_DTH2_INIT * n_surf + s) * b_size + b];
        int fl = surf_flags[s * b_size + b];
        flags[s] = fl;
        if ((fl & FLAG_IS_WINDOW) != 0) {
            has_window = 1;
        }
    }

    int iters_taken = 0;
    for (int it = 0; it < SPIKE_MAX_ITERS; ++it) {
        iters_taken = it + 1;
        for (int s = 0; s < n_surf; ++s) {
            dt_in_old[s] = cur_dt_in[s];
        }
        spike_interior_rad_exchange(
            b,
            b_size,
            n_surf,
            (it == 0 && has_window) ? 1 : 0,
            cur_dt_in,
            flags,
            surf_in,
            script_f_sigma,
            q_net_lw,
            ir_parent
        );

        if (it > 0 && (it % SPIKE_REEVAL_CONV) == 0) {
            for (int s = 0; s < n_surf; ++s) {
                if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                    float cos_tilt =
                        surf_in[(SF_COS_TILT * n_surf + s) * b_size + b];
                    cur_h_in[s] = spike_inside_conv_opaque(
                        cur_dt_in[s], dt_mat, cos_tilt, h_min
                    );
                }
            }
        }

        if (it == 0 && has_window) {
            for (int s = 0; s < n_surf; ++s) {
                if ((flags[s] & FLAG_IS_WINDOW) != 0) {
                    float dt_out_air =
                        surf_in[(SF_DT_OUT_SURF_AIR * n_surf + s) * b_size + b];
                    float cos_tilt =
                        surf_in[(SF_COS_TILT * n_surf + s) * b_size + b];
                    float sin_tilt =
                        surf_in[(SF_SIN_TILT * n_surf + s) * b_size + b];
                    float tilt_deg =
                        surf_in[(SF_TILT_DEG * n_surf + s) * b_size + b];
                    float height =
                        surf_in[(SF_HEIGHT * n_surf + s) * b_size + b];
                    float eps_in =
                        surf_in[(SF_EPS_IN * n_surf + s) * b_size + b];
                    float eps_out =
                        surf_in[(SF_EPS_OUT * n_surf + s) * b_size + b];
                    float vf_sky =
                        surf_in[(SF_VF_SKY_IR * n_surf + s) * b_size + b];
                    float vf_grd =
                        surf_in[(SF_VF_GROUND_IR * n_surf + s) * b_size + b];
                    float split =
                        surf_in[(SF_AIR_SKY_SPLIT * n_surf + s) * b_size + b];
                    float scon =
                        surf_in[(SF_SCON_WIN * n_surf + s) * b_size + b];
                    float hc_ext_w = spike_outside_conv_doe2(
                        cur_dt_out[s], dt_out_air, cos_tilt
                    );
                    float dth1_i = new_dth1[s];
                    float dth2_i = new_dth2[s];
                    if (begin_envrn) {
                        spike_starting_window_temps(
                            dt_mat,
                            dt_out_air,
                            cur_h_in[s],
                            hc_ext_w,
                            scon,
                            &dth1_i,
                            &dth2_i
                        );
                    }
                    float w_dt_in = 0.0f;
                    float w_dt_out = 0.0f;
                    float w_h_in = 0.0f;
                    float w_dth1 = 0.0f;
                    float w_dth2 = 0.0f;
                    spike_solve_simple_window(
                        dt_mat,
                        dt_out_air,
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
                        tilt_deg,
                        sin_tilt,
                        h_min,
                        dth1_i,
                        dth2_i,
                        &w_dt_in,
                        &w_dt_out,
                        &w_h_in,
                        &w_dth1,
                        &w_dth2
                    );
                    cur_dt_in[s] = w_dt_in;
                    cur_dt_out[s] = w_dt_out;
                    cur_h_in[s] = w_h_in;
                    new_dth1[s] = w_dth1;
                    new_dth2[s] = w_dth2;
                }
            }
        }

        float max_del_t = 0.0f;
        for (int s = 0; s < n_surf; ++s) {
            if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                float ctf_in0 = surf_in[(SF_CTF_IN0 * n_surf + s) * b_size + b];
                float ctf_cross0 =
                    surf_in[(SF_CTF_CROSS0 * n_surf + s) * b_size + b];
                float ctf_const_sh =
                    surf_in[(SF_CTF_CONST_IN_SHIFTED * n_surf + s) * b_size + b];
                int is_ad = ((flags[s] & FLAG_IS_INTMASS) != 0) ? 1 : 0;
                float op_dt_in = spike_inside_surface_step(
                    dt_in_old[s],
                    cur_dt_out[s],
                    dt_mat,
                    cur_h_in[s],
                    q_net_lw[s],
                    ctf_in0,
                    ctf_cross0,
                    ctf_const_sh,
                    is_ad
                );
                cur_dt_in[s] = op_dt_in;
                float del = op_dt_in - dt_in_old[s];
                float abs_del = (del < 0.0f) ? -del : del;
                if (abs_del > max_del_t) {
                    max_del_t = abs_del;
                }
            }
        }

        if (max_del_t <= SPIKE_MAX_DEL_T) {
            break;
        }
    }

    for (int s = 0; s < n_surf; ++s) {
        surf_out[(OF_DT_IN_OUT * n_surf + s) * b_size + b] = cur_dt_in[s];
        surf_out[(OF_DT_OUT_OUT * n_surf + s) * b_size + b] = cur_dt_out[s];
        surf_out[(OF_H_CONV_IN_OUT * n_surf + s) * b_size + b] = cur_h_in[s];
        surf_out[(OF_DTH1_OUT * n_surf + s) * b_size + b] = new_dth1[s];
        surf_out[(OF_DTH2_OUT * n_surf + s) * b_size + b] = new_dth2[s];
    }
    iter_out[b] = iters_taken;
}

#endif
