struct Params {
    b_size: i32,
    n_surf: i32,
    pad0: i32,
    pad1: i32,
};

struct WinStart {
    dth1: f32,
    dth2: f32,
};

struct WinSol {
    dt_in: f32,
    dt_out: f32,
    h_in: f32,
    dth1: f32,
    dth2: f32,
};

@group(0) @binding(0) var<uniform> params: Params;
@group(0) @binding(1) var<storage, read> zone_in: array<f32>;
@group(0) @binding(2) var<storage, read> surf_in: array<f32>;
@group(0) @binding(3) var<storage, read> surf_flags: array<i32>;
@group(0) @binding(4) var<storage, read> script_f_sigma: array<f32>;
@group(0) @binding(5) var<storage, read_write> surf_out: array<f32>;
@group(0) @binding(6) var<storage, read_write> iter_out: array<i32>;

const SPIKE_T_REF_K: f32 = 293.15;
const SPIKE_SIGMA: f32 = 5.6697e-8;
const SPIKE_ITER_DAMP: f32 = 5.0;
const SPIKE_MAX_ITERS: i32 = 500;
const SPIKE_REEVAL_CONV: i32 = 30;
const SPIKE_MAX_DEL_T: f32 = 0.002;
const SPIKE_WIN_MAX_ITER: i32 = 100;
const SPIKE_WIN_ERR_TOL: f32 = 0.02;

const ZF_DT_MAT: i32 = 0;
const ZF_W_ZONE_AVG: i32 = 1;
const ZF_PB_SITE: i32 = 2;
const ZF_DT_SKY: i32 = 3;
const ZF_H_MIN: i32 = 4;
const ZF_BEGIN_ENVRN: i32 = 5;

const SF_DT_IN_INIT: i32 = 0;
const SF_DT_OUT_INIT: i32 = 1;
const SF_H_CONV_IN_INIT: i32 = 2;
const SF_DTH1_INIT: i32 = 3;
const SF_DTH2_INIT: i32 = 4;
const SF_DT_OUT_SURF_AIR: i32 = 5;
const SF_EPS_IN: i32 = 6;
const SF_EPS_OUT: i32 = 7;
const SF_COS_TILT: i32 = 8;
const SF_SIN_TILT: i32 = 9;
const SF_TILT_DEG: i32 = 10;
const SF_HEIGHT: i32 = 11;
const SF_VF_SKY_IR: i32 = 12;
const SF_VF_GROUND_IR: i32 = 13;
const SF_AIR_SKY_SPLIT: i32 = 14;
const SF_SCON_WIN: i32 = 15;
const SF_CTF_IN0: i32 = 16;
const SF_CTF_CROSS0: i32 = 17;
const SF_CTF_CONST_IN_SHIFTED: i32 = 18;

const OF_DT_IN_OUT: i32 = 0;
const OF_DT_OUT_OUT: i32 = 1;
const OF_H_CONV_IN_OUT: i32 = 2;
const OF_DTH1_OUT: i32 = 3;
const OF_DTH2_OUT: i32 = 4;

const FLAG_SURF_MASK: i32 = 1;
const FLAG_IS_WINDOW: i32 = 2;
const FLAG_IS_NON_WINDOW: i32 = 4;
const FLAG_IS_INTMASS: i32 = 8;

// Psychrometrics.hh::PsyRhoAirFnPbTdbW
fn spike_psy_rho_air(pb: f32, t_k: f32, dw: f32) -> f32 {
    let w: f32 = max(dw, 1.0e-5);
    return pb / (287.0 * t_k * (1.0 + 1.6077687 * w));
}

// Psychrometrics.hh::PsyCpAirFnW
fn spike_psy_cp_air(dw: f32) -> f32 {
    let w: f32 = max(dw, 1.0e-5);
    return 1.00484e3 + w * 1.85895e3;
}

// ConvectionCoefficients.cc::CalcASHRAETARPNatural
fn spike_ashrae_tarp_natural(dt_surf: f32, dt_amb: f32, cos_tilt: f32) -> f32 {
    let delta_t: f32 = dt_surf - dt_amb;
    let abs_dt: f32 = abs(delta_t);
    var abs_dt_cbrt: f32 = 0.0;
    if (abs_dt > 0.0) {
        abs_dt_cbrt = pow(abs_dt, 1.0 / 3.0);
    }
    let abs_cos: f32 = abs(cos_tilt);
    if (delta_t == 0.0 || cos_tilt == 0.0) {
        return 1.31 * abs_dt_cbrt;
    }
    if ((delta_t < 0.0 && cos_tilt < 0.0) || (delta_t > 0.0 && cos_tilt > 0.0)) {
        return 9.482 * abs_dt_cbrt / (7.238 - abs_cos);
    }
    return 1.810 * abs_dt_cbrt / (1.382 + abs_cos);
}

// ConvectionCoefficients.cc::CalcASHRAEDetailedIntConvCoeff
fn spike_inside_conv_opaque(
    dt_surf: f32,
    dt_zone: f32,
    cos_tilt: f32,
    h_min: f32
) -> f32 {
    let h_nat: f32 = spike_ashrae_tarp_natural(dt_surf, dt_zone, -cos_tilt);
    return max(h_nat, h_min);
}

// ConvectionCoefficients.cc::InitExteriorConvectionCoeff
fn spike_outside_conv_doe2(dt_surf: f32, dt_air: f32, cos_tilt: f32) -> f32 {
    return spike_ashrae_tarp_natural(dt_surf, dt_air, cos_tilt);
}

// ConvectionCoefficients.cc::CalcISO15099WindowIntConvCoeff
fn spike_iso15099_win_int_conv(
    dt_surf: f32,
    dt_air: f32,
    hum_rat: f32,
    baro_press: f32,
    height: f32,
    tilt_deg: f32,
    sin_tilt: f32,
    h_min: f32
) -> f32 {
    let t_surf_k: f32 = SPIKE_T_REF_K + dt_surf;
    let t_air_k: f32 = SPIKE_T_REF_K + dt_air;
    let delta_t: f32 = dt_surf - dt_air;
    if (t_air_k < 200.0 || t_air_k > 400.0 || t_surf_k < 180.0 || t_surf_k > 450.0) {
        return h_min;
    }
    let t_film_k: f32 = t_air_k + 0.25 * delta_t;
    let rho: f32 = spike_psy_rho_air(baro_press, t_film_k, hum_rat);
    let lam: f32 = 2.873e-3 + 7.76e-5 * t_film_k;
    let mu: f32 = 3.723e-6 + 4.94e-8 * t_film_k;
    let cp: f32 = spike_psy_cp_air(hum_rat);
    var eff_tilt: f32 = tilt_deg;
    if (delta_t > 0.0) {
        eff_tilt = 180.0 - tilt_deg;
    }
    let safe_h: f32 = max(height, 1.0e-6);
    let safe_sin: f32 = max(sin_tilt, 1.0e-12);
    let ra_h: f32 = (rho * rho) * (safe_h * safe_h * safe_h) * 9.81 * cp *
        abs(delta_t) / (t_film_k * mu * lam);
    var nu_int: f32 = 0.0;
    if (eff_tilt < 15.0) {
        if (ra_h > 0.0) {
            nu_int = 0.13 * pow(ra_h, 1.0 / 3.0);
        }
    } else if (eff_tilt <= 90.0) {
        let clamped: f32 = max(eff_tilt, 15.0);
        let ra_cv: f32 = 2.5e5 * exp(0.144 * clamped) / pow(safe_sin, 0.2);
        let ra_h_sin: f32 = ra_h * safe_sin;
        if (ra_h <= ra_cv) {
            if (ra_h_sin > 0.0) {
                nu_int = 0.56 * pow(ra_h_sin, 0.25);
            }
        } else {
            var p_rah: f32 = 0.0;
            if (ra_h > 0.0) {
                p_rah = pow(ra_h, 1.0 / 3.0);
            }
            let p_racv: f32 = pow(ra_cv, 1.0 / 3.0);
            nu_int = 0.13 * (p_rah - p_racv) + 0.56 * pow(ra_cv * safe_sin, 0.25);
        }
    } else if (eff_tilt <= 179.0) {
        let ra_h_sin: f32 = ra_h * safe_sin;
        if (ra_h_sin < 1.0e5) {
            nu_int = 9.958364696217969;
        } else if (ra_h_sin >= 1.0e11) {
            nu_int = 314.9111421065955;
        } else {
            nu_int = 0.56 * pow(ra_h_sin, 0.25);
        }
    } else {
        if (ra_h > 1.0e11) {
            nu_int = 91.92380516274462;
        } else if (ra_h > 0.0) {
            nu_int = 0.58 * pow(ra_h, 0.2);
        }
    }
    let h_val: f32 = nu_int * lam / safe_h;
    return max(h_val, h_min);
}

// WindowManager.cc::CalcWindowHeatBalanceInternalRoutines
fn spike_window_outside_ir(
    t_out_k: f32,
    t_sky_k: f32,
    vf_sky_ir: f32,
    vf_ground_ir: f32,
    air_sky_split: f32
) -> f32 {
    let t_out2: f32 = t_out_k * t_out_k;
    let eb_out: f32 = SPIKE_SIGMA * (t_out2 * t_out2);
    let t_sky2: f32 = t_sky_k * t_sky_k;
    let eb_sky: f32 = SPIKE_SIGMA * (t_sky2 * t_sky2);
    return vf_sky_ir *
        (air_sky_split * eb_sky + (1.0 - air_sky_split) * eb_out) +
        vf_ground_ir * eb_out;
}

// WindowManager.cc::StartingWindowTemps
fn spike_starting_window_temps(
    dt_in: f32,
    dt_out: f32,
    h_in: f32,
    h_out: f32,
    scon: f32
) -> WinStart {
    let hrad: f32 = 5.3;
    let r1: f32 = 1.0 / (h_out + hrad);
    let r2: f32 = 1.0 / max(scon, 1.0e-6);
    let r3: f32 = 1.0 / (h_in + hrad);
    let r_tot: f32 = r1 + r2 + r3;
    var temdiff: f32 = dt_in - dt_out;
    if (abs(temdiff) < 0.5) {
        temdiff = 2.0;
    }
    return WinStart(
        (r1 / r_tot) * temdiff + dt_out,
        ((r1 + r2) / r_tot) * temdiff + dt_out
    );
}

// WindowManager.cc::SolveForWindowTemperatures
fn spike_solve_simple_window(
    dt_in: f32,
    dt_out: f32,
    dt_sky: f32,
    hum_rat: f32,
    baro_press: f32,
    h_out: f32,
    rmir: f32,
    scon: f32,
    eps_out: f32,
    eps_in: f32,
    vf_sky_ir: f32,
    vf_ground_ir: f32,
    air_sky_split: f32,
    height: f32,
    tilt_deg: f32,
    sin_tilt: f32,
    h_min: f32,
    dth1_init: f32,
    dth2_init: f32
) -> WinSol {
    let t_out_k: f32 = SPIKE_T_REF_K + dt_out;
    let t_sky_k: f32 = SPIKE_T_REF_K + dt_sky;
    let out_ir: f32 = spike_window_outside_ir(
        t_out_k, t_sky_k, vf_sky_ir, vf_ground_ir, air_sky_split
    );
    var dth1: f32 = dth1_init;
    var dth2: f32 = dth2_init;
    var h_in: f32 = 3.0;
    for (var it: i32 = 0; it < SPIKE_WIN_MAX_ITER; it = it + 1) {
        let th1: f32 = SPIKE_T_REF_K + dth1;
        let th2: f32 = SPIKE_T_REF_K + dth2;
        let hr1: f32 = eps_out * SPIKE_SIGMA * (th1 * th1 * th1);
        let hr2: f32 = eps_in * SPIKE_SIGMA * (th2 * th2 * th2);
        h_in = spike_iso15099_win_int_conv(
            dth2, dt_in, hum_rat, baro_press, height, tilt_deg, sin_tilt, h_min
        );
        let a11: f32 = hr1 + scon + h_out;
        let a22: f32 = hr2 + scon + h_in;
        let rhs1: f32 = eps_out * out_ir - hr1 * SPIKE_T_REF_K + h_out * dt_out;
        let rhs2: f32 = eps_in * rmir - hr2 * SPIKE_T_REF_K + h_in * dt_in;
        let det: f32 =
            (hr1 + h_out) * (hr2 + h_in) + scon * (hr1 + h_out + hr2 + h_in);
        let d_sol1: f32 = (a22 * rhs1 + scon * rhs2) / det;
        let d_sol2: f32 = (scon * rhs1 + a11 * rhs2) / det;
        var w_old: f32 = 0.75;
        if (it + 1 < (SPIKE_WIN_MAX_ITER / 4)) {
            w_old = 0.5;
        }
        let w_new: f32 = 1.0 - w_old;
        let new_dth1: f32 = w_old * dth1 + w_new * d_sol1;
        let new_dth2: f32 = w_old * dth2 + w_new * d_sol2;
        let err: f32 = 0.5 * (abs(new_dth1 - dth1) + abs(new_dth2 - dth2));
        dth1 = new_dth1;
        dth2 = new_dth2;
        if (err <= SPIKE_WIN_ERR_TOL) {
            break;
        }
    }
    return WinSol(dth2, dth1, h_in, dth1, dth2);
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2
fn spike_inside_surface_step(
    dt_in_old: f32,
    dt_out_curr: f32,
    dt_zone: f32,
    h_conv_in: f32,
    q_rad_net_lw_in: f32,
    ctf_in0: f32,
    ctf_cross0: f32,
    ctf_const_in_shifted: f32,
    is_adiabatic: bool
) -> f32 {
    let temp_term: f32 =
        ctf_const_in_shifted + h_conv_in * dt_zone + q_rad_net_lw_in;
    var num: f32 = temp_term + SPIKE_ITER_DAMP * dt_in_old;
    var den: f32 = ctf_in0 + h_conv_in + SPIKE_ITER_DAMP;
    if (is_adiabatic) {
        den = den - ctf_cross0;
    } else {
        num = num + ctf_cross0 * dt_out_curr;
    }
    if (den == 0.0) {
        return num;
    }
    return num / den;
}

// HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2CTFOnly
@compute @workgroup_size(64, 1, 1)
fn inside_surface_iterate(@builtin(global_invocation_id) gid: vec3<u32>) {
    let b: i32 = i32(gid.x);
    let b_size: i32 = params.b_size;
    let n_surf: i32 = params.n_surf;
    if (b >= b_size) {
        return;
    }

    let dt_mat: f32 = zone_in[ZF_DT_MAT * b_size + b];
    let w_zone_avg: f32 = zone_in[ZF_W_ZONE_AVG * b_size + b];
    let pb_site: f32 = zone_in[ZF_PB_SITE * b_size + b];
    let dt_sky: f32 = zone_in[ZF_DT_SKY * b_size + b];
    let h_min: f32 = zone_in[ZF_H_MIN * b_size + b];
    let begin_envrn: bool = zone_in[ZF_BEGIN_ENVRN * b_size + b] > 0.5;

    var cur_dt_in: array<f32, 16>;
    var cur_dt_out: array<f32, 16>;
    var cur_h_in: array<f32, 16>;
    var new_dth1: array<f32, 16>;
    var new_dth2: array<f32, 16>;
    var dt_in_old: array<f32, 16>;
    var t_k: array<f32, 16>;
    var t_k2: array<f32, 16>;
    var q_net_lw: array<f32, 16>;
    var ir_parent: array<f32, 16>;
    var flags: array<i32, 16>;
    var has_window: bool = false;

    for (var s: i32 = 0; s < n_surf; s = s + 1) {
        cur_dt_in[s] = surf_in[(SF_DT_IN_INIT * n_surf + s) * b_size + b];
        cur_dt_out[s] = surf_in[(SF_DT_OUT_INIT * n_surf + s) * b_size + b];
        cur_h_in[s] = surf_in[(SF_H_CONV_IN_INIT * n_surf + s) * b_size + b];
        new_dth1[s] = surf_in[(SF_DTH1_INIT * n_surf + s) * b_size + b];
        new_dth2[s] = surf_in[(SF_DTH2_INIT * n_surf + s) * b_size + b];
        let fl: i32 = surf_flags[s * b_size + b];
        flags[s] = fl;
        if ((fl & FLAG_IS_WINDOW) != 0) {
            has_window = true;
        }
    }

    var iters_taken: i32 = 0;
    for (var it: i32 = 0; it < SPIKE_MAX_ITERS; it = it + 1) {
        iters_taken = it + 1;
        for (var s: i32 = 0; s < n_surf; s = s + 1) {
            dt_in_old[s] = cur_dt_in[s];
            let tk: f32 = SPIKE_T_REF_K + cur_dt_in[s];
            t_k[s] = tk;
            t_k2[s] = tk * tk;
        }

        let compute_ir: bool = (it == 0) && has_window;
        for (var i: i32 = 0; i < n_surf; i = i + 1) {
            if ((flags[i] & FLAG_SURF_MASK) == 0) {
                q_net_lw[i] = 0.0;
                ir_parent[i] = 0.0;
                continue;
            }
            var q_acc: f32 = 0.0;
            var ir_acc: f32 = 0.0;
            let want_ir: bool = compute_ir && ((flags[i] & FLAG_IS_WINDOW) != 0);
            let row_off: i32 = i * n_surf;
            for (var j: i32 = 0; j < n_surf; j = j + 1) {
                let sf: f32 = script_f_sigma[(row_off + j) * b_size + b];
                let diff_t4: f32 = (cur_dt_in[j] - cur_dt_in[i]) *
                    (t_k[j] + t_k[i]) * (t_k2[j] + t_k2[i]);
                q_acc = q_acc + sf * diff_t4;
                if (want_ir) {
                    ir_acc = ir_acc + sf * (t_k2[j] * t_k2[j]);
                }
            }
            q_net_lw[i] = q_acc;
            if (want_ir) {
                let eps_in: f32 = surf_in[(SF_EPS_IN * n_surf + i) * b_size + b];
                ir_parent[i] = ir_acc / max(eps_in, 1.0e-12);
            } else {
                ir_parent[i] = 0.0;
            }
        }

        if (it > 0 && (it % SPIKE_REEVAL_CONV) == 0) {
            for (var s: i32 = 0; s < n_surf; s = s + 1) {
                if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                    let cos_tilt: f32 =
                        surf_in[(SF_COS_TILT * n_surf + s) * b_size + b];
                    cur_h_in[s] = spike_inside_conv_opaque(
                        cur_dt_in[s], dt_mat, cos_tilt, h_min
                    );
                }
            }
        }

        if (it == 0 && has_window) {
            for (var s: i32 = 0; s < n_surf; s = s + 1) {
                if ((flags[s] & FLAG_IS_WINDOW) != 0) {
                    let dt_out_air: f32 =
                        surf_in[(SF_DT_OUT_SURF_AIR * n_surf + s) * b_size + b];
                    let cos_tilt: f32 =
                        surf_in[(SF_COS_TILT * n_surf + s) * b_size + b];
                    let sin_tilt: f32 =
                        surf_in[(SF_SIN_TILT * n_surf + s) * b_size + b];
                    let tilt_deg: f32 =
                        surf_in[(SF_TILT_DEG * n_surf + s) * b_size + b];
                    let height: f32 =
                        surf_in[(SF_HEIGHT * n_surf + s) * b_size + b];
                    let eps_in: f32 =
                        surf_in[(SF_EPS_IN * n_surf + s) * b_size + b];
                    let eps_out: f32 =
                        surf_in[(SF_EPS_OUT * n_surf + s) * b_size + b];
                    let vf_sky: f32 =
                        surf_in[(SF_VF_SKY_IR * n_surf + s) * b_size + b];
                    let vf_grd: f32 =
                        surf_in[(SF_VF_GROUND_IR * n_surf + s) * b_size + b];
                    let split: f32 =
                        surf_in[(SF_AIR_SKY_SPLIT * n_surf + s) * b_size + b];
                    let scon: f32 =
                        surf_in[(SF_SCON_WIN * n_surf + s) * b_size + b];
                    let hc_ext_w: f32 = spike_outside_conv_doe2(
                        cur_dt_out[s], dt_out_air, cos_tilt
                    );
                    var dth1_i: f32 = new_dth1[s];
                    var dth2_i: f32 = new_dth2[s];
                    if (begin_envrn) {
                        let ws: WinStart = spike_starting_window_temps(
                            dt_mat, dt_out_air, cur_h_in[s], hc_ext_w, scon
                        );
                        dth1_i = ws.dth1;
                        dth2_i = ws.dth2;
                    }
                    let sol: WinSol = spike_solve_simple_window(
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
                        dth2_i
                    );
                    cur_dt_in[s] = sol.dt_in;
                    cur_dt_out[s] = sol.dt_out;
                    cur_h_in[s] = sol.h_in;
                    new_dth1[s] = sol.dth1;
                    new_dth2[s] = sol.dth2;
                }
            }
        }

        var max_del_t: f32 = 0.0;
        for (var s: i32 = 0; s < n_surf; s = s + 1) {
            if ((flags[s] & FLAG_IS_NON_WINDOW) != 0) {
                let ctf_in0: f32 =
                    surf_in[(SF_CTF_IN0 * n_surf + s) * b_size + b];
                let ctf_cross0: f32 =
                    surf_in[(SF_CTF_CROSS0 * n_surf + s) * b_size + b];
                let ctf_const_sh: f32 =
                    surf_in[(SF_CTF_CONST_IN_SHIFTED * n_surf + s) * b_size + b];
                let is_ad: bool = (flags[s] & FLAG_IS_INTMASS) != 0;
                let op_dt_in: f32 = spike_inside_surface_step(
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
                let abs_del: f32 = abs(op_dt_in - dt_in_old[s]);
                if (abs_del > max_del_t) {
                    max_del_t = abs_del;
                }
            }
        }

        if (max_del_t <= SPIKE_MAX_DEL_T) {
            break;
        }
    }

    for (var s: i32 = 0; s < n_surf; s = s + 1) {
        surf_out[(OF_DT_IN_OUT * n_surf + s) * b_size + b] = cur_dt_in[s];
        surf_out[(OF_DT_OUT_OUT * n_surf + s) * b_size + b] = cur_dt_out[s];
        surf_out[(OF_H_CONV_IN_OUT * n_surf + s) * b_size + b] = cur_h_in[s];
        surf_out[(OF_DTH1_OUT * n_surf + s) * b_size + b] = new_dth1[s];
        surf_out[(OF_DTH2_OUT * n_surf + s) * b_size + b] = new_dth2[s];
    }
    iter_out[b] = iters_taken;
}
