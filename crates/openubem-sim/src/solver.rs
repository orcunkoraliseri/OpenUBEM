//! Generic `SimFloat` per-building Stage-A annual thermal solver (`f64` reference & `f32` GPU twin).

use rayon::prelude::*;

use crate::float_trait::SimFloat;
use crate::physics::{
    KELVIN_CONV, STEFAN_BOLTZMANN, calc_inside_convection_opaque,
    calc_iso15099_window_int_conv_coeff, calc_outside_convection_doe2, calc_outside_rad_coeffs,
    out_dry_bulb_temp_at, psy_cp_air_fn_w, psy_h_fn_tdb_w, psy_rho_air_fn_pb_tdb_w,
    psy_w_fn_tdb_rh_pb, simple_glazing_layer_conductance,
};

pub const BOUND_OSC: i32 = 0;
pub const BOUND_OUTDOORS: i32 = 1;
pub const BOUND_INTMASS: i32 = 2;
pub const BOUND_WINDOW: i32 = 3;
pub const BOUND_DOOR: i32 = 4;

const SURF_INITIAL_TEMP: f64 = 23.0;
const ZONE_INITIAL_TEMP: f64 = 23.0;
const MAX_ZONE_TEMP_DIFF: f64 = 0.3;
const MIN_TIME_STEP_SYS_HR: f64 = 1.0 / 60.0;
const WARMUP_MIN_LOAD: f64 = 100.0;
const ITER_DAMP_CONST: f64 = 5.0;
const ITERS_REEVAL_CONV_COEFF: usize = 30;
const MAX_INSIDE_SURF_ITERS: usize = 500;
const MAX_ALLOWED_DEL_TEMP: f64 = 0.002;
const WINDOW_MAX_ITER: usize = 100;
const WINDOW_ERR_TOL: f64 = 0.02;
const SMALL_TEMP_DIFF: f64 = 1.0e-5;
const VERY_SMALL_MASS_FLOW: f64 = 1.0e-12;

/// Owned input bundle for a single building (`n_s` active surfaces, flat `script_f` `[n_s * n_s]`).
#[derive(Debug, Clone)]
pub struct BuildingStageAInput {
    pub steps_per_hour: usize,
    pub n_run_steps: usize,
    pub warmup_min_days: i32,
    pub warmup_max_days: i32,
    pub temp_conv_tol: f64,
    pub loads_conv_tol: f64,
    pub h_conv_min: f64,
    pub zone_volume: f64,
    pub zone_centroid_z: f64,
    pub zone_vent_flow_m3s: f64,
    pub zone_heat_setpoint: f64,
    pub zone_cool_setpoint: f64,
    pub zone_max_heat_supply_temp: f64,

    pub n_surf: usize,
    pub surf_boundary: Vec<i32>,
    pub surf_area: Vec<f64>,
    pub surf_u_value: Vec<f64>,
    pub surf_centroid_z: Vec<f64>,
    pub surf_cos_tilt: Vec<f64>,
    pub surf_sin_tilt: Vec<f64>,
    pub surf_tilt_deg: Vec<f64>,
    pub surf_height: Vec<f64>,
    pub surf_eps_out: Vec<f64>,
    pub surf_eps_in: Vec<f64>,
    pub surf_vf_sky_ir: Vec<f64>,
    pub surf_vf_ground_ir: Vec<f64>,
    pub surf_air_sky_split: Vec<f64>,
    pub surf_osc_c_const: Vec<f64>,
    pub surf_osc_t_const: Vec<f64>,
    pub surf_osc_c_out: Vec<f64>,
    pub surf_osc_c_zone: Vec<f64>,
    pub script_f: Vec<f64>,

    pub ctf_n_terms: usize,
    pub ctf_outside: Vec<f64>,
    pub ctf_cross: Vec<f64>,
    pub ctf_inside: Vec<f64>,
    pub ctf_flux: Vec<f64>,

    pub weather_t_db: Vec<f64>,
    pub weather_w_out: Vec<f64>,
    pub weather_pb: Vec<f64>,
    pub weather_t_sky: Vec<f64>,
    pub wu_t_db: Vec<f64>,
    pub wu_w_out: Vec<f64>,
    pub wu_pb: Vec<f64>,
    pub wu_t_sky: Vec<f64>,

    pub gain_ts: Vec<f64>,
    pub wu_gain: Vec<f64>,

    pub has_solar: bool,
    pub q_sol_out: Vec<f64>,
    pub q_sw_in: Vec<f64>,
    pub q_sol_win: Vec<f64>,
    pub wu_q_out: Vec<f64>,
    pub wu_q_in: Vec<f64>,
    pub wu_q_win: Vec<f64>,
    pub record_zone_temp: bool,
}

/// Output metrics for one simulated building.
#[derive(Debug, Clone)]
pub struct BuildingStageAOutput {
    pub hourly_heating_j: Vec<f64>,
    pub annual_heating_kwh: f64,
    pub warmup_days: i32,
    pub zone_air_temp_c: Vec<f64>,
    pub zone_mean_air_temp_c: Vec<f64>,
}

#[inline]
fn down_interp_4<F: SimFloat>(old_dt: F, new_dt: F, old: &[F; 4]) -> [F; 4] {
    let ratio = old_dt / new_dt;
    let d10 = old[1] - old[0];
    let t1 = new_dt;
    let t2 = F::lit(2.0) * new_dt;
    let t3 = F::lit(3.0) * new_dt;
    let t4 = F::lit(4.0) * new_dt;
    if (ratio - F::lit(2.0)).abs() < F::lit(0.01) {
        let d21 = old[2] - old[1];
        [
            old[0] + d10 * (t1 / old_dt),
            old[0] + d10 * (t2 / old_dt),
            old[1] + d21 * ((t3 - old_dt) / old_dt),
            old[1] + d21 * ((t4 - old_dt) / old_dt),
        ]
    } else if (ratio - F::lit(3.0)).abs() < F::lit(0.01) {
        let d21 = (old[2] - old[1]) / old_dt;
        [
            old[0] + d10 * (t1 / old_dt),
            old[0] + d10 * (t2 / old_dt),
            old[0] + d10 * (t3 / old_dt),
            old[1] + d21 * ((t4 - old_dt) / old_dt),
        ]
    } else {
        [
            old[0] + d10 * (t1 / old_dt),
            old[0] + d10 * (t2 / old_dt),
            old[0] + d10 * (t3 / old_dt),
            old[0] + d10 * (t4 / old_dt),
        ]
    }
}

#[inline]
fn predict_zone_load_f<F: SimFloat>(
    t_zone_mat: F,
    hum_rat: F,
    baro_press: F,
    zone_vol: F,
    dt_sys_sec: F,
    ztm: &[F; 4],
    sum_ha: F,
    sum_hat: F,
    sum_mcp: F,
    sum_mcpt: F,
    sum_int_gain: F,
    heat_sp: F,
) -> F {
    let rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_zone_mat, hum_rat);
    let cp = psy_cp_air_fn_w(hum_rat);
    let cap = zone_vol * rho * cp / dt_sys_sec;
    let dep = (F::lit(11.0 / 6.0)) * cap + sum_ha + sum_mcp;
    let hist = cap * (F::lit(3.0) * ztm[0] - F::lit(1.5) * ztm[1] + F::lit(1.0 / 3.0) * ztm[2]);
    let ind = hist + sum_int_gain + sum_hat + sum_mcpt;
    dep * heat_sp - ind
}

#[inline]
fn calc_ideal_loads_heating_f<F: SimFloat>(
    q_heat_req: F,
    t_zone_node: F,
    w_zone_node: F,
    baro_press: F,
    max_heat_sup_t: F,
) -> (F, F, F, F, F) {
    if q_heat_req <= F::lit(0.0) {
        return (F::lit(0.0), t_zone_node, w_zone_node, F::lit(0.0), F::lit(0.0));
    }
    let cp = psy_cp_air_fn_w(w_zone_node);
    let dt = max_heat_sup_t - t_zone_node;
    if dt <= F::lit(SMALL_TEMP_DIFF) {
        return (F::lit(0.0), t_zone_node, w_zone_node, F::lit(0.0), F::lit(0.0));
    }
    let m_dot = q_heat_req / (cp * dt);
    if m_dot <= F::lit(VERY_SMALL_MASS_FLOW) {
        return (F::lit(0.0), t_zone_node, w_zone_node, F::lit(0.0), F::lit(0.0));
    }
    let t_sup = ((q_heat_req / (cp * m_dot)) + t_zone_node)
        .min(max_heat_sup_t)
        .max(t_zone_node);
    let w_sat = psy_w_fn_tdb_rh_pb(t_sup, F::lit(1.0), baro_press);
    let w_sup = w_zone_node.min(w_sat);
    let h_sup = psy_h_fn_tdb_w(t_sup, w_sup);
    let h_zone = psy_h_fn_tdb_w(t_zone_node, w_zone_node);
    let sen_out = m_dot * cp * (t_sup - t_zone_node);
    let lat_out = m_dot * (h_sup - h_zone) - sen_out;
    let sen_rate = sen_out.max(F::lit(0.0));
    let tot_rate = sen_rate + lat_out.max(F::lit(0.0));
    (m_dot, t_sup, w_sup, sen_rate, tot_rate)
}

#[inline]
#[allow(clippy::too_many_arguments)]
fn correct_zone_f<F: SimFloat>(
    t_zone_mat: F,
    hum_rat: F,
    baro_press: F,
    zone_vol: F,
    dt_sys_sec: F,
    ztm: &[F; 4],
    w_prev: &[F; 4],
    sum_ha: F,
    sum_hat: F,
    sum_mcp: F,
    sum_mcpt: F,
    sum_int_gain: F,
    m_dot_sup: F,
    t_sup: F,
    w_sup: F,
    vamfl: F,
    out_w: F,
) -> (F, F) {
    let rho = psy_rho_air_fn_pb_tdb_w(baro_press, t_zone_mat, hum_rat);
    let cp = psy_cp_air_fn_w(hum_rat);
    let cap = zone_vol * rho * cp / dt_sys_sec;
    let sys_mcp = m_dot_sup * cp;
    let sys_mcpt = sys_mcp * t_sup;
    let dep = (F::lit(11.0 / 6.0)) * cap + sum_ha + sum_mcp + sys_mcp;
    let hist = cap * (F::lit(3.0) * ztm[0] - F::lit(1.5) * ztm[1] + F::lit(1.0 / 3.0) * ztm[2]);
    let ind = hist + sum_int_gain + sum_hat + sum_mcpt + sys_mcpt;
    let zt_new = ind / dep;

    let rho_w = psy_rho_air_fn_pb_tdb_w(baro_press, zt_new, hum_rat);
    let cw = rho_w * zone_vol / dt_sys_sec;
    let bw = vamfl * out_w + m_dot_sup * w_sup;
    let aw = m_dot_sup + vamfl;
    let wh = cw
        * (F::lit(3.0) * w_prev[0] - F::lit(1.5) * w_prev[1] + F::lit(1.0 / 3.0) * w_prev[2]);
    let mut w_new = ((bw + wh) / (F::lit(11.0 / 6.0) * cw + aw)).max(F::lit(0.0));
    let w_sat = psy_w_fn_tdb_rh_pb(zt_new, F::lit(1.0), baro_press);
    w_new = w_new.min(w_sat);
    (zt_new, w_new)
}

/// Simulate one building across warm-up + annual steps using `F: SimFloat`.
pub fn simulate_building_stage_a<F: SimFloat>(inp: &BuildingStageAInput) -> BuildingStageAOutput {
    let sph = inp.steps_per_hour;
    let dt_zone_hr = F::lit(1.0 / (sph as f64));
    let dt_zone_sec = F::lit(3600.0 / (sph as f64));
    let steps_per_day = 24 * sph;
    let limit_num_sys = ((1.0 / (sph as f64)) / MIN_TIME_STEP_SYS_HR).round().max(1.0) as i32;
    let ns = inp.n_surf;
    let nhist = inp.ctf_n_terms;

    let h_min = F::lit(inp.h_conv_min);
    let zone_vol = F::lit(inp.zone_volume);
    let zone_cen_z = F::lit(inp.zone_centroid_z);
    let vent_flow = F::lit(inp.zone_vent_flow_m3s);
    let heat_sp = F::lit(inp.zone_heat_setpoint);
    let max_sup_t = F::lit(inp.zone_max_heat_supply_temp);

    let area: Vec<F> = inp.surf_area.iter().map(|&v| F::lit(v)).collect();
    let uval: Vec<F> = inp.surf_u_value.iter().map(|&v| F::lit(v)).collect();
    let cen_z: Vec<F> = inp.surf_centroid_z.iter().map(|&v| F::lit(v)).collect();
    let cos_t: Vec<F> = inp.surf_cos_tilt.iter().map(|&v| F::lit(v)).collect();
    let sin_t: Vec<F> = inp.surf_sin_tilt.iter().map(|&v| F::lit(v)).collect();
    let tilt_d: Vec<F> = inp.surf_tilt_deg.iter().map(|&v| F::lit(v)).collect();
    let s_height: Vec<F> = inp.surf_height.iter().map(|&v| F::lit(v)).collect();
    let eps_out: Vec<F> = inp.surf_eps_out.iter().map(|&v| F::lit(v)).collect();
    let eps_in: Vec<F> = inp.surf_eps_in.iter().map(|&v| F::lit(v)).collect();
    let vf_sky: Vec<F> = inp.surf_vf_sky_ir.iter().map(|&v| F::lit(v)).collect();
    let vf_grd: Vec<F> = inp.surf_vf_ground_ir.iter().map(|&v| F::lit(v)).collect();
    let air_sky: Vec<F> = inp.surf_air_sky_split.iter().map(|&v| F::lit(v)).collect();
    let osc_cc: Vec<F> = inp.surf_osc_c_const.iter().map(|&v| F::lit(v)).collect();
    let osc_tc: Vec<F> = inp.surf_osc_t_const.iter().map(|&v| F::lit(v)).collect();
    let osc_co: Vec<F> = inp.surf_osc_c_out.iter().map(|&v| F::lit(v)).collect();
    let osc_cz: Vec<F> = inp.surf_osc_c_zone.iter().map(|&v| F::lit(v)).collect();
    let sf_sigma: Vec<F> = inp
        .script_f
        .iter()
        .map(|&v| F::lit(v * STEFAN_BOLTZMANN))
        .collect();

    let is_osc: Vec<bool> = inp.surf_boundary.iter().map(|&b| b == BOUND_OSC).collect();
    let is_ext_op: Vec<bool> = inp
        .surf_boundary
        .iter()
        .map(|&b| b == BOUND_OUTDOORS || b == BOUND_DOOR)
        .collect();
    let is_intmass: Vec<bool> = inp.surf_boundary.iter().map(|&b| b == BOUND_INTMASS).collect();
    let is_win: Vec<bool> = inp.surf_boundary.iter().map(|&b| b == BOUND_WINDOW).collect();
    let has_window = is_win.iter().any(|&w| w);

    let scon_win: Vec<F> = (0..ns)
        .map(|s| {
            if is_win[s] {
                simple_glazing_layer_conductance(uval[s])
            } else {
                F::lit(1.0)
            }
        })
        .collect();

    let ctf_out0: Vec<F> = (0..ns)
        .map(|s| if is_intmass[s] { F::lit(inp.ctf_outside[0]) } else { uval[s] })
        .collect();
    let ctf_cross0: Vec<F> = (0..ns)
        .map(|s| if is_intmass[s] { F::lit(inp.ctf_cross[0]) } else { uval[s] })
        .collect();
    let ctf_in0: Vec<F> = (0..ns)
        .map(|s| if is_intmass[s] { F::lit(inp.ctf_inside[0]) } else { uval[s] })
        .collect();
    let ctf_out_tail: Vec<F> = (0..nhist).map(|h| F::lit(inp.ctf_outside[h + 1])).collect();
    let ctf_cross_tail: Vec<F> = (0..nhist).map(|h| F::lit(inp.ctf_cross[h + 1])).collect();
    let ctf_in_tail: Vec<F> = (0..nhist).map(|h| F::lit(inp.ctf_inside[h + 1])).collect();
    let ctf_flux_tail: Vec<F> = (0..nhist).map(|h| F::lit(inp.ctf_flux[h])).collect();

    let init_db = F::lit(inp.wu_t_db[0]);
    let mut t_surf_in = vec![F::lit(SURF_INITIAL_TEMP); ns];
    let mut t_surf_out: Vec<F> = (0..ns)
        .map(|s| {
            if is_ext_op[s] || is_win[s] {
                out_dry_bulb_temp_at(init_db, cen_z[s])
            } else {
                F::lit(SURF_INITIAL_TEMP)
            }
        })
        .collect();
    let mut t_in_hist = vec![F::lit(SURF_INITIAL_TEMP); ns * nhist];
    let mut t_out_hist = vec![F::lit(0.0); ns * nhist];
    let mut q_out_hist = vec![F::lit(0.0); ns * nhist];
    let mut q_in_hist = vec![F::lit(0.0); ns * nhist];
    for s in 0..ns {
        let qi = if is_intmass[s] {
            F::lit(0.0)
        } else {
            uval[s] * (t_surf_out[s] - F::lit(SURF_INITIAL_TEMP))
        };
        for h in 0..nhist {
            t_out_hist[s * nhist + h] = t_surf_out[s];
            q_out_hist[s * nhist + h] = qi;
            q_in_hist[s * nhist + h] = qi;
        }
    }

    let mut t_mat = F::lit(ZONE_INITIAL_TEMP);
    let mut xmat = [F::lit(ZONE_INITIAL_TEMP); 4];
    let mut dsxmat = [F::lit(ZONE_INITIAL_TEMP); 4];
    let init_w = F::lit(inp.wu_w_out[0]);
    let mut w_zone = init_w;
    let mut w_zone_avg = init_w;
    let mut w_prev_ts = [init_w; 4];
    let mut dsw_prev_ts = [init_w; 4];
    let mut num_sys_last = 1i32;

    let mut theta1_win: Vec<F> = t_surf_out.iter().map(|&t| t + F::lit(KELVIN_CONV)).collect();
    let mut theta2_win: Vec<F> = t_surf_in.iter().map(|&t| t + F::lit(KELVIN_CONV)).collect();

    // Scratch buffers reused per step (zero allocation in tight time loop!)
    let mut ctf_const_in = vec![F::lit(0.0); ns];
    let mut ctf_const_out = vec![F::lit(0.0); ns];
    let mut cur_t_out = vec![F::lit(0.0); ns];
    let mut cur_t_in = vec![F::lit(0.0); ns];
    let mut t_in_old = vec![F::lit(0.0); ns];
    let mut cur_h_in = vec![F::lit(0.0); ns];
    let mut q_net_lw = vec![F::lit(0.0); ns];
    let mut ir_parent = vec![F::lit(0.0); ns];
    let mut t_k = vec![F::lit(0.0); ns];
    let mut t_k2 = vec![F::lit(0.0); ns];
    let mut t_k4 = vec![F::lit(0.0); ns];
    let mut t_out_surf_air = vec![F::lit(0.0); ns];

    let mut step_one = |t_site: F,
                        w_site: F,
                        pb_site: F,
                        t_sky_site: F,
                        gain_w: F,
                        begin_envrn: bool,
                        q_so: &[f64],
                        q_si: &[f64],
                        q_sw: &[f64]|
     -> (F, F, F, F) {
        let t_out_zone_air = out_dry_bulb_temp_at(t_site, zone_cen_z);
        for s in 0..ns {
            let tsa = out_dry_bulb_temp_at(t_site, cen_z[s]);
            t_out_surf_air[s] = tsa;

            cur_h_in[s] = if is_win[s] {
                calc_iso15099_window_int_conv_coeff(
                    t_surf_in[s],
                    t_mat,
                    w_zone_avg,
                    pb_site,
                    s_height[s],
                    tilt_d[s],
                    sin_t[s],
                    h_min,
                )
            } else {
                calc_inside_convection_opaque(t_surf_in[s], t_mat, cos_t[s], h_min)
            };

            if is_intmass[s] && nhist > 0 {
                let mut cin = F::lit(0.0);
                let mut cout = F::lit(0.0);
                let base = s * nhist;
                for h in 0..nhist {
                    let toh = t_out_hist[base + h];
                    let tih = t_in_hist[base + h];
                    let qoh = q_out_hist[base + h];
                    let qih = q_in_hist[base + h];
                    cin = cin + ctf_cross_tail[h] * toh - ctf_in_tail[h] * tih + ctf_flux_tail[h] * qih;
                    cout = cout + ctf_out_tail[h] * toh - ctf_cross_tail[h] * tih + ctf_flux_tail[h] * qoh;
                }
                ctf_const_in[s] = cin;
                ctf_const_out[s] = cout;
            } else {
                ctf_const_in[s] = F::lit(0.0);
                ctf_const_out[s] = F::lit(0.0);
            }
        }

        // Initial LW pass using prev-step t_surf_in
        for s in 0..ns {
            let k = t_surf_in[s] + F::lit(KELVIN_CONV);
            t_k[s] = k;
            t_k2[s] = k * k;
        }
        for s in 0..ns {
            let tk = t_k[s];
            let tk2 = t_k2[s];
            let mut lw = F::lit(0.0);
            let row = s * ns;
            for j in 0..ns {
                let sfs = sf_sigma[row + j];
                let d4 = (t_k[j] - tk) * (t_k[j] + tk) * (t_k2[j] + tk2);
                lw = lw + sfs * d4;
            }
            if is_osc[s] {
                cur_t_out[s] = osc_cz[s] * t_mat + osc_co[s] * t_out_surf_air[s] + osc_cc[s] * osc_tc[s];
            } else if is_ext_op[s] {
                let qso = F::lit(q_so[s]);
                let qsi = F::lit(q_si[s]);
                let hc_ext = calc_outside_convection_doe2(t_surf_out[s], t_out_surf_air[s], cos_t[s]);
                let (hsky, hgrd, hair) = calc_outside_rad_coeffs(
                    t_surf_out[s],
                    t_out_surf_air[s],
                    t_sky_site,
                    eps_out[s],
                    vf_sky[s],
                    vf_grd[s],
                    air_sky[s],
                );
                let ext_num = -ctf_const_out[s]
                    + qso
                    + (hc_ext + hair) * t_out_surf_air[s]
                    + hsky * t_sky_site
                    + hgrd * t_site;
                let ext_den = ctf_out0[s] + hc_ext + hair + hsky + hgrd;
                if ctf_cross0[s] > F::lit(0.01) {
                    let safe_in = (ctf_in0[s] + cur_h_in[s]).max(F::lit(1.0e-12));
                    let f1 = ctf_cross0[s] / safe_in;
                    let qn = ext_num + f1 * (ctf_const_in[s] + cur_h_in[s] * t_mat + lw + qsi);
                    let qd = ext_den - f1 * ctf_cross0[s];
                    cur_t_out[s] = if qd == F::lit(0.0) { qn } else { qn / qd };
                } else {
                    let sn = ext_num + ctf_cross0[s] * t_surf_in[s];
                    cur_t_out[s] = if ext_den == F::lit(0.0) { sn } else { sn / ext_den };
                }
            } else if is_intmass[s] {
                cur_t_out[s] = t_surf_in[s];
            } else {
                cur_t_out[s] = t_surf_out[s];
            }
            cur_t_in[s] = t_surf_in[s];
        }

        let mut new_th1 = theta1_win.clone();
        let mut new_th2 = theta2_win.clone();

        for it in 0..MAX_INSIDE_SURF_ITERS {
            t_in_old.copy_from_slice(&cur_t_in);
            for s in 0..ns {
                let k = cur_t_in[s] + F::lit(KELVIN_CONV);
                let k2 = k * k;
                t_k[s] = k;
                t_k2[s] = k2;
                t_k4[s] = k2 * k2;
            }
            for s in 0..ns {
                let tk = t_k[s];
                let tk2 = t_k2[s];
                let row = s * ns;
                let mut lw = F::lit(0.0);
                let mut ir = F::lit(0.0);
                for j in 0..ns {
                    let sfs = sf_sigma[row + j];
                    lw = lw + sfs * (t_k[j] - tk) * (t_k[j] + tk) * (t_k2[j] + tk2);
                    if has_window && is_win[s] {
                        ir = ir + sfs * t_k4[j];
                    }
                }
                q_net_lw[s] = lw;
                ir_parent[s] = if is_win[s] {
                    ir / eps_in[s].max(F::lit(1.0e-12))
                } else {
                    F::lit(0.0)
                };
            }

            if it > 0 && (it % ITERS_REEVAL_CONV_COEFF == 0) {
                for s in 0..ns {
                    if !is_win[s] {
                        cur_h_in[s] = calc_inside_convection_opaque(cur_t_in[s], t_mat, cos_t[s], h_min);
                    }
                }
            }

            if it == 0 && has_window {
                for s in 0..ns {
                    if !is_win[s] {
                        continue;
                    }
                    let hc_ext_w = calc_outside_convection_doe2(cur_t_out[s], t_out_surf_air[s], cos_t[s]);
                    let (mut th1, mut th2) = if begin_envrn {
                        let r1 = F::lit(1.0) / (hc_ext_w + F::lit(5.3));
                        let r2 = F::lit(1.0) / scon_win[s].max(F::lit(1.0e-6));
                        let r3 = F::lit(1.0) / (cur_h_in[s] + F::lit(5.3));
                        let rtot = r1 + r2 + r3;
                        let tk_in = t_mat + F::lit(KELVIN_CONV);
                        let tk_out = t_out_surf_air[s] + F::lit(KELVIN_CONV);
                        let td = if (tk_in - tk_out).abs() < F::lit(0.5) {
                            F::lit(2.0)
                        } else {
                            tk_in - tk_out
                        };
                        ((r1 / rtot) * td + tk_out, ((r1 + r2) / rtot) * td + tk_out)
                    } else {
                        (theta1_win[s], theta2_win[s])
                    };

                    let tk_in = t_mat + F::lit(KELVIN_CONV);
                    let tk_out = t_out_surf_air[s] + F::lit(KELVIN_CONV);
                    let tk_sky = t_sky_site + F::lit(KELVIN_CONV);
                    let eb_out = F::lit(STEFAN_BOLTZMANN) * tk_out * tk_out * tk_out * tk_out;
                    let eb_sky = F::lit(STEFAN_BOLTZMANN) * tk_sky * tk_sky * tk_sky * tk_sky;
                    let out_ir = vf_sky[s]
                        * (air_sky[s] * eb_sky + (F::lit(1.0) - air_sky[s]) * eb_out)
                        + vf_grd[s] * eb_out;
                    let half_q = F::lit(0.5 * q_sw[s]);
                    let mut h_in_w = F::lit(3.0);

                    for wit in 0..WINDOW_MAX_ITER {
                        let hr1 = eps_out[s] * F::lit(STEFAN_BOLTZMANN) * th1 * th1 * th1;
                        let hr2 = eps_in[s] * F::lit(STEFAN_BOLTZMANN) * th2 * th2 * th2;
                        h_in_w = calc_iso15099_window_int_conv_coeff(
                            th2 - F::lit(KELVIN_CONV),
                            t_mat,
                            w_zone_avg,
                            pb_site,
                            s_height[s],
                            tilt_d[s],
                            sin_t[s],
                            h_min,
                        );
                        let a11 = hr1 + scon_win[s] + hc_ext_w;
                        let a22 = hr2 + scon_win[s] + h_in_w;
                        let b1 = out_ir * eps_out[s] + hc_ext_w * tk_out + half_q;
                        let b2 = ir_parent[s] * eps_in[s] + h_in_w * tk_in + half_q;
                        let det = a11 * a22 - scon_win[s] * scon_win[s];
                        let sol1 = (a22 * b1 + scon_win[s] * b2) / det;
                        let sol2 = (scon_win[s] * b1 + a11 * b2) / det;
                        let w_old = if wit + 1 < WINDOW_MAX_ITER / 4 {
                            F::lit(0.5)
                        } else {
                            F::lit(0.75)
                        };
                        let w_new = F::lit(1.0) - w_old;
                        let n1 = w_old * th1 + w_new * sol1;
                        let n2 = w_old * th2 + w_new * sol2;
                        let err = F::lit(0.5) * ((n1 - th1).abs() + (n2 - th2).abs());
                        th1 = n1;
                        th2 = n2;
                        if err <= F::lit(WINDOW_ERR_TOL) {
                            break;
                        }
                    }
                    cur_t_in[s] = th2 - F::lit(KELVIN_CONV);
                    cur_t_out[s] = th1 - F::lit(KELVIN_CONV);
                    cur_h_in[s] = h_in_w;
                    new_th1[s] = th1;
                    new_th2[s] = th2;
                }
            }

            let mut max_del = F::lit(0.0);
            for s in 0..ns {
                if is_win[s] {
                    continue;
                }
                let qsi = F::lit(q_si[s]);
                let temp_term = ctf_const_in[s] + cur_h_in[s] * t_mat + q_net_lw[s] + qsi;
                let (num, den) = if is_intmass[s] {
                    (
                        temp_term + F::lit(ITER_DAMP_CONST) * t_in_old[s],
                        ctf_in0[s] - ctf_cross0[s] + cur_h_in[s] + F::lit(ITER_DAMP_CONST),
                    )
                } else {
                    (
                        temp_term + F::lit(ITER_DAMP_CONST) * t_in_old[s] + ctf_cross0[s] * cur_t_out[s],
                        ctf_in0[s] + cur_h_in[s] + F::lit(ITER_DAMP_CONST),
                    )
                };
                let next_t = if den == F::lit(0.0) { num } else { num / den };
                cur_t_in[s] = next_t;
                let dt = (next_t - t_in_old[s]).abs();
                if dt > max_del {
                    max_del = dt;
                }
            }
            if max_del <= F::lit(MAX_ALLOWED_DEL_TEMP) {
                break;
            }
        }

        let mut sum_ha = F::lit(0.0);
        let mut sum_hat = F::lit(0.0);
        for s in 0..ns {
            let ha = cur_h_in[s] * area[s];
            sum_ha = sum_ha + ha;
            sum_hat = sum_hat + ha * cur_t_in[s];
        }

        let air_density = psy_rho_air_fn_pb_tdb_w(pb_site, t_out_zone_air, w_site);
        let cp_out = psy_cp_air_fn_w(w_site);
        let vvf = vent_flow.max(F::lit(0.0));
        let mcpv = (vvf * air_density * cp_out).max(F::lit(0.0));
        let vamfl = mcpv / cp_out;
        let mcptv = mcpv * t_out_zone_air;

        let ql = predict_zone_load_f(
            t_mat, w_zone, pb_site, zone_vol, dt_zone_sec, &xmat, sum_ha, sum_hat, mcpv, mcptv,
            gain_w, heat_sp,
        );
        let (ms, ts, ws, mut sn_rate, tot_rate) =
            calc_ideal_loads_heating_f(ql, t_mat, w_zone, pb_site, max_sup_t);
        let (mut zt_new, mut w_new) = correct_zone_f(
            t_mat, w_zone, pb_site, zone_vol, dt_zone_sec, &xmat, &w_prev_ts, sum_ha, sum_hat,
            mcpv, mcptv, gain_w, ms, ts, ws, vamfl, w_site,
        );

        let temp_change = (zt_new - xmat[0]).abs();
        let mut ztav = zt_new;
        let mut w_avg = w_new;
        let mut heat_j = tot_rate * dt_zone_sec;
        let mut new_num_sys = 1i32;

        if temp_change > F::lit(MAX_ZONE_TEMP_DIFF) {
            let ratio = (temp_change / F::lit(MAX_ZONE_TEMP_DIFF)).to_f64_lossless() + 1.0;
            let n_sub = (ratio as i32).min(limit_num_sys).max(1);
            let dt_sub_hr = (dt_zone_hr / F::lit(n_sub as f64)).max(F::lit(MIN_TIME_STEP_SYS_HR));
            let dt_sub_sec = dt_sub_hr * F::lit(3600.0);
            let frac_sub = dt_sub_hr / dt_zone_hr;
            new_num_sys = n_sub;

            let mut b_mat = xmat[0];
            let mut b_w = w_prev_ts[0];
            let (mut b_dsx, mut b_dsw) = if n_sub != num_sys_last {
                (
                    down_interp_4(dt_zone_hr, dt_sub_hr, &xmat),
                    down_interp_4(dt_zone_hr, dt_sub_hr, &w_prev_ts),
                )
            } else {
                (dsxmat, dsw_prev_ts)
            };

            let mut acc_zt = F::lit(0.0);
            let mut acc_w = F::lit(0.0);
            let mut acc_e = F::lit(0.0);
            let mut acc_sen = F::lit(0.0);
            for _ in 0..n_sub {
                let ql_s = predict_zone_load_f(
                    b_mat, b_w, pb_site, zone_vol, dt_sub_sec, &b_dsx, sum_ha, sum_hat, mcpv,
                    mcptv, gain_w, heat_sp,
                );
                let (ms_s, ts_s, ws_s, sh_s, th_s) =
                    calc_ideal_loads_heating_f(ql_s, b_mat, b_w, pb_site, max_sup_t);
                let (zn_s, wn_s) = correct_zone_f(
                    b_mat, b_w, pb_site, zone_vol, dt_sub_sec, &b_dsx, &b_dsw, sum_ha, sum_hat,
                    mcpv, mcptv, gain_w, ms_s, ts_s, ws_s, vamfl, w_site,
                );
                b_mat = zn_s;
                b_w = wn_s;
                b_dsx = [b_mat, b_dsx[0], b_dsx[1], b_dsx[2]];
                b_dsw = [b_w, b_dsw[0], b_dsw[1], b_dsw[2]];
                acc_zt = acc_zt + b_mat * frac_sub;
                acc_w = acc_w + b_w * frac_sub;
                acc_e = acc_e + th_s * dt_sub_sec;
                acc_sen = acc_sen + sh_s * frac_sub;
            }
            zt_new = b_mat;
            w_new = b_w;
            ztav = acc_zt;
            w_avg = acc_w;
            heat_j = acc_e;
            sn_rate = acc_sen;
            dsxmat = b_dsx;
            dsw_prev_ts = b_dsw;
        }

        xmat = [ztav, xmat[0], xmat[1], xmat[2]];
        w_prev_ts = [w_avg, w_prev_ts[0], w_prev_ts[1], w_prev_ts[2]];
        t_mat = zt_new;
        w_zone = w_new;
        w_zone_avg = w_avg;
        num_sys_last = new_num_sys;

        // Shift CTF histories
        if nhist > 0 {
            for s in 0..ns {
                let base = s * nhist;
                let qo = cur_t_in[s] * ctf_cross0[s] - cur_t_out[s] * ctf_out0[s] - ctf_const_out[s];
                let qi = cur_t_out[s] * ctf_cross0[s] - cur_t_in[s] * ctf_in0[s] + ctf_const_in[s];
                for h in (1..nhist).rev() {
                    t_out_hist[base + h] = t_out_hist[base + h - 1];
                    t_in_hist[base + h] = t_in_hist[base + h - 1];
                    q_out_hist[base + h] = q_out_hist[base + h - 1];
                    q_in_hist[base + h] = q_in_hist[base + h - 1];
                }
                t_out_hist[base] = cur_t_out[s];
                t_in_hist[base] = cur_t_in[s];
                q_out_hist[base] = qo;
                q_in_hist[base] = qi;
            }
        }
        t_surf_in.copy_from_slice(&cur_t_in);
        t_surf_out.copy_from_slice(&cur_t_out);
        theta1_win.copy_from_slice(&new_th1);
        theta2_win.copy_from_slice(&new_th2);

        (heat_j, ztav, t_mat, sn_rate)
    };

    let zero_sol = vec![0.0_f64; ns];
    let mut warmup_days = 0i32;
    let mut max_t_prev = -9999.0_f64;
    let mut min_t_prev = 1000.0_f64;
    let mut max_h_prev = -9999.0_f64;

    for day in 1..=inp.warmup_max_days {
        let mut max_t_day = -9999.0_f64;
        let mut min_t_day = 1000.0_f64;
        let mut max_h_day = -9999.0_f64;

        for step in 0..steps_per_day {
            let (qso, qsi, qsw) = if inp.has_solar {
                let off = step * ns;
                (
                    &inp.wu_q_out[off..(off + ns)],
                    &inp.wu_q_in[off..(off + ns)],
                    &inp.wu_q_win[off..(off + ns)],
                )
            } else {
                (&zero_sol[..], &zero_sol[..], &zero_sol[..])
            };
            let (_, ztav_step, _, sn_step) = step_one(
                F::lit(inp.wu_t_db[step]),
                F::lit(inp.wu_w_out[step]),
                F::lit(inp.wu_pb[step]),
                F::lit(inp.wu_t_sky[step]),
                F::lit(inp.wu_gain[step]),
                day == 1 && step == 0,
                qso,
                qsi,
                qsw,
            );
            let zf = ztav_step.to_f64_lossless();
            let hf = sn_step.to_f64_lossless();
            max_t_day = max_t_day.max(zf);
            min_t_day = min_t_day.min(zf);
            max_h_day = max_h_day.max(hf);
        }

        let pass_max_t = (max_t_prev - max_t_day).abs() <= inp.temp_conv_tol;
        let pass_min_t = (min_t_prev - min_t_day).abs() <= inp.temp_conv_tol;
        let eff_h_day = max_h_day.max(WARMUP_MIN_LOAD).abs();
        let eff_h_prev = max_h_prev.max(WARMUP_MIN_LOAD).abs();
        let rel_h_diff = ((eff_h_day - eff_h_prev) / eff_h_day).abs();
        let pass_h = if max_h_day > 1.0e-4 {
            rel_h_diff <= inp.loads_conv_tol
        } else {
            true
        };

        if (pass_max_t && pass_min_t && pass_h && day >= inp.warmup_min_days)
            || day >= inp.warmup_max_days
        {
            warmup_days = day;
            break;
        }
        max_t_prev = max_t_day;
        min_t_prev = min_t_day;
        max_h_prev = eff_h_day;
    }

    let n_hours = inp.n_run_steps / sph;
    let mut hourly_heating_j = vec![0.0_f64; n_hours];
    let mut z_temp_rec = if inp.record_zone_temp {
        vec![0.0_f64; inp.n_run_steps]
    } else {
        Vec::new()
    };
    let mut z_mean_rec = if inp.record_zone_temp {
        vec![0.0_f64; inp.n_run_steps]
    } else {
        Vec::new()
    };

    for step in 0..inp.n_run_steps {
        let (qso, qsi, qsw) = if inp.has_solar {
            let off = step * ns;
            (
                &inp.q_sol_out[off..(off + ns)],
                &inp.q_sw_in[off..(off + ns)],
                &inp.q_sol_win[off..(off + ns)],
            )
        } else {
            (&zero_sol[..], &zero_sol[..], &zero_sol[..])
        };
        let (heat_j, ztav_step, t_mat_step, _) = step_one(
            F::lit(inp.weather_t_db[step]),
            F::lit(inp.weather_w_out[step]),
            F::lit(inp.weather_pb[step]),
            F::lit(inp.weather_t_sky[step]),
            F::lit(inp.gain_ts[step]),
            false,
            qso,
            qsi,
            qsw,
        );
        hourly_heating_j[step / sph] += heat_j.to_f64_lossless();
        if inp.record_zone_temp {
            z_temp_rec[step] = t_mat_step.to_f64_lossless();
            z_mean_rec[step] = ztav_step.to_f64_lossless();
        }
    }

    let annual_heating_kwh = hourly_heating_j.iter().sum::<f64>() / 3.6e6;
    BuildingStageAOutput {
        hourly_heating_j,
        annual_heating_kwh,
        warmup_days,
        zone_air_temp_c: z_temp_rec,
        zone_mean_air_temp_c: z_mean_rec,
    }
}

/// Parallel `rayon` batch Stage-A evaluation (CPU `f64` reference mode).
pub fn run_stage_a_batch_f64(inputs: &[BuildingStageAInput]) -> Vec<BuildingStageAOutput> {
    inputs
        .par_iter()
        .map(simulate_building_stage_a::<f64>)
        .collect()
}

/// Parallel `rayon` batch Stage-A evaluation (`f32` GPU-twin parity mode).
pub fn run_stage_a_batch_f32(inputs: &[BuildingStageAInput]) -> Vec<BuildingStageAOutput> {
    inputs
        .par_iter()
        .map(simulate_building_stage_a::<f32>)
        .collect()
}
