//! PyO3 FFI bindings for `openubem-sim`.

use numpy::{
    PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArray3,
    PyUntypedArrayMethods,
};
use openubem_sim::{
    BuildingStageAInput, BuildingStageAOutput, kernel_conformance_hash, run_stage_a_batch_f32,
    run_stage_a_batch_f64,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

type SimBatchArrays<'py> = (
    Py<PyArray2<f64>>,
    Py<PyArray1<f64>>,
    Py<PyArray1<i32>>,
    Option<Py<PyArray2<f64>>>,
    Option<Py<PyArray2<f64>>>,
);

fn req_1d_f64<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<Vec<f64>> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray1<'py, f64> = item.extract()?;
    Ok(arr.as_array().iter().copied().collect())
}

fn req_1d_i32<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<Vec<i32>> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray1<'py, i32> = item.extract()?;
    Ok(arr.as_array().iter().copied().collect())
}

fn req_2d_f64<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<(usize, usize, Vec<f64>)> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray2<'py, f64> = item.extract()?;
    let sh = arr.shape();
    Ok((sh[0], sh[1], arr.as_array().iter().copied().collect()))
}

fn req_2d_i32<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<(usize, usize, Vec<i32>)> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray2<'py, i32> = item.extract()?;
    let sh = arr.shape();
    Ok((sh[0], sh[1], arr.as_array().iter().copied().collect()))
}

fn req_2d_bool<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<(usize, usize, Vec<bool>)> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray2<'py, bool> = item.extract()?;
    let sh = arr.shape();
    Ok((sh[0], sh[1], arr.as_array().iter().copied().collect()))
}

fn req_3d_f64<'py>(d: &Bound<'py, PyDict>, k: &str) -> PyResult<(usize, usize, usize, Vec<f64>)> {
    let item = d
        .get_item(k)?
        .ok_or_else(|| PyValueError::new_err(format!("missing sim key '{k}'")))?;
    let arr: PyReadonlyArray3<'py, f64> = item.extract()?;
    let sh = arr.shape();
    Ok((sh[0], sh[1], sh[2], arr.as_array().iter().copied().collect()))
}

/// Return compile-time SHA-256 digest of the pure-Rust `openubem-sim` solver kernels.
#[pyfunction]
pub fn sim_kernel_conformance_hash() -> &'static str {
    kernel_conformance_hash()
}

/// Execute Stage-A warm-up + annual heat-balance across `[B]` buildings in parallel (`rayon`).
#[pyfunction]
pub fn sim_run_stage_a_batch<'py>(
    py: Python<'py>,
    payload: &Bound<'py, PyDict>,
    use_f32: bool,
) -> PyResult<SimBatchArrays<'py>> {
    let b_size: usize = payload
        .get_item("b_size")?
        .ok_or_else(|| PyValueError::new_err("missing b_size"))?
        .extract()?;
    let n_surf_max: usize = payload
        .get_item("n_surf_max")?
        .ok_or_else(|| PyValueError::new_err("missing n_surf_max"))?
        .extract()?;
    let sph: usize = payload
        .get_item("steps_per_hour")?
        .ok_or_else(|| PyValueError::new_err("missing steps_per_hour"))?
        .extract()?;
    let n_run_steps: usize = payload
        .get_item("n_run_steps")?
        .ok_or_else(|| PyValueError::new_err("missing n_run_steps"))?
        .extract()?;
    let ctf_n_terms: usize = payload
        .get_item("ctf_n_terms")?
        .ok_or_else(|| PyValueError::new_err("missing ctf_n_terms"))?
        .extract()?;
    let record_zone_temp: bool = payload
        .get_item("record_zone_temp")?
        .ok_or_else(|| PyValueError::new_err("missing record_zone_temp"))?
        .extract()?;
    let has_solar: bool = payload
        .get_item("has_solar")?
        .ok_or_else(|| PyValueError::new_err("missing has_solar"))?
        .extract()?;

    let warmup_min = req_1d_i32(payload, "warmup_min_days")?;
    let warmup_max = req_1d_i32(payload, "warmup_max_days")?;
    let temp_tol = req_1d_f64(payload, "temp_conv_tol")?;
    let loads_tol = req_1d_f64(payload, "loads_conv_tol")?;
    let h_conv_min = req_1d_f64(payload, "h_conv_min")?;
    let zone_vol = req_1d_f64(payload, "zone_volume")?;
    let zone_cen_z = req_1d_f64(payload, "zone_centroid_z")?;
    let zone_vent = req_1d_f64(payload, "zone_vent_flow_m3s")?;
    let zone_hsp = req_1d_f64(payload, "zone_heat_setpoint")?;
    let zone_csp = req_1d_f64(payload, "zone_cool_setpoint")?;
    let zone_sup_t = req_1d_f64(payload, "zone_max_heat_supply_temp")?;

    let (_, _, surf_mask) = req_2d_bool(payload, "surf_mask")?;
    let (_, _, surf_boundary) = req_2d_i32(payload, "surf_boundary")?;
    let (_, _, surf_area) = req_2d_f64(payload, "surf_area")?;
    let (_, _, surf_u) = req_2d_f64(payload, "surf_u_value")?;
    let (_, _, surf_cz) = req_2d_f64(payload, "surf_centroid_z")?;
    let (_, _, surf_ct) = req_2d_f64(payload, "surf_cos_tilt")?;
    let (_, _, surf_st) = req_2d_f64(payload, "surf_sin_tilt")?;
    let (_, _, surf_td) = req_2d_f64(payload, "surf_tilt_deg")?;
    let (_, _, surf_h) = req_2d_f64(payload, "surf_height")?;
    let (_, _, surf_eo) = req_2d_f64(payload, "surf_eps_out")?;
    let (_, _, surf_ei) = req_2d_f64(payload, "surf_eps_in")?;
    let (_, _, surf_vf_sky) = req_2d_f64(payload, "surf_vf_sky_ir")?;
    let (_, _, surf_vf_grd) = req_2d_f64(payload, "surf_vf_ground_ir")?;
    let (_, _, surf_air_sky) = req_2d_f64(payload, "surf_air_sky_rad_split")?;
    let (_, _, surf_osc_cc) = req_2d_f64(payload, "surf_osc_c_const")?;
    let (_, _, surf_osc_tc) = req_2d_f64(payload, "surf_osc_t_const")?;
    let (_, _, surf_osc_co) = req_2d_f64(payload, "surf_osc_c_out")?;
    let (_, _, surf_osc_cz) = req_2d_f64(payload, "surf_osc_c_zone")?;
    let (_, _, _, script_f) = req_3d_f64(payload, "script_f")?;

    let ctf_outside = req_1d_f64(payload, "ctf_outside")?;
    let ctf_cross = req_1d_f64(payload, "ctf_cross")?;
    let ctf_inside = req_1d_f64(payload, "ctf_inside")?;
    let ctf_flux = req_1d_f64(payload, "ctf_flux")?;

    let (_, n_w_steps, t_db_all) = req_2d_f64(payload, "t_db_all")?;
    let (_, _, w_out_all) = req_2d_f64(payload, "w_out_all")?;
    let (_, _, pb_all) = req_2d_f64(payload, "pb_all")?;
    let (_, _, t_sky_all) = req_2d_f64(payload, "t_sky_all")?;
    let (_, n_wu_steps, wu_db) = req_2d_f64(payload, "wu_db")?;
    let (_, _, wu_w) = req_2d_f64(payload, "wu_w")?;
    let (_, _, wu_pb) = req_2d_f64(payload, "wu_pb")?;
    let (_, _, wu_sky) = req_2d_f64(payload, "wu_sky")?;

    let (_, _, gain_ts) = req_2d_f64(payload, "gain_ts")?;
    let (_, _, wu_gain) = req_2d_f64(payload, "wu_gain")?;

    let (q_sol_out_all, q_sw_in_all, q_sol_win_all, wu_q_out, wu_q_in, wu_q_win) = if has_solar {
        (
            req_3d_f64(payload, "q_sol_out_all")?.3,
            req_3d_f64(payload, "q_sw_in_all")?.3,
            req_3d_f64(payload, "q_sol_win_all")?.3,
            req_3d_f64(payload, "wu_q_out")?.3,
            req_3d_f64(payload, "wu_q_in")?.3,
            req_3d_f64(payload, "wu_q_win")?.3,
        )
    } else {
        (vec![], vec![], vec![], vec![], vec![], vec![])
    };

    let mut inputs = Vec::with_capacity(b_size);
    for b in 0..b_size {
        let base_s = b * n_surf_max;
        let active_idx: Vec<usize> = (0..n_surf_max)
            .filter(|&s| surf_mask[base_s + s])
            .collect();
        let ns = active_idx.len();

        let pick_s = |src: &[f64]| -> Vec<f64> {
            active_idx.iter().map(|&s| src[base_s + s]).collect()
        };
        let pick_s_i32 = |src: &[i32]| -> Vec<i32> {
            active_idx.iter().map(|&s| src[base_s + s]).collect()
        };

        let mut sf = Vec::with_capacity(ns * ns);
        let sf_b = b * n_surf_max * n_surf_max;
        for &si in &active_idx {
            for &sj in &active_idx {
                sf.push(script_f[sf_b + si * n_surf_max + sj]);
            }
        }

        let pack_sol = |src: &[f64], n_t: usize| -> Vec<f64> {
            if !has_solar {
                return Vec::new();
            }
            let mut dst = Vec::with_capacity(n_t * ns);
            let b_off = b * n_t * n_surf_max;
            for t in 0..n_t {
                let t_off = b_off + t * n_surf_max;
                for &si in &active_idx {
                    dst.push(src[t_off + si]);
                }
            }
            dst
        };

        let w_off = b * n_w_steps;
        let wu_off = b * n_wu_steps;
        inputs.push(BuildingStageAInput {
            steps_per_hour: sph,
            n_run_steps,
            warmup_min_days: warmup_min[b],
            warmup_max_days: warmup_max[b],
            temp_conv_tol: temp_tol[b],
            loads_conv_tol: loads_tol[b],
            h_conv_min: h_conv_min[b],
            zone_volume: zone_vol[b],
            zone_centroid_z: zone_cen_z[b],
            zone_vent_flow_m3s: zone_vent[b],
            zone_heat_setpoint: zone_hsp[b],
            zone_cool_setpoint: zone_csp[b],
            zone_max_heat_supply_temp: zone_sup_t[b],
            n_surf: ns,
            surf_boundary: pick_s_i32(&surf_boundary),
            surf_area: pick_s(&surf_area),
            surf_u_value: pick_s(&surf_u),
            surf_centroid_z: pick_s(&surf_cz),
            surf_cos_tilt: pick_s(&surf_ct),
            surf_sin_tilt: pick_s(&surf_st),
            surf_tilt_deg: pick_s(&surf_td),
            surf_height: pick_s(&surf_h),
            surf_eps_out: pick_s(&surf_eo),
            surf_eps_in: pick_s(&surf_ei),
            surf_vf_sky_ir: pick_s(&surf_vf_sky),
            surf_vf_ground_ir: pick_s(&surf_vf_grd),
            surf_air_sky_split: pick_s(&surf_air_sky),
            surf_osc_c_const: pick_s(&surf_osc_cc),
            surf_osc_t_const: pick_s(&surf_osc_tc),
            surf_osc_c_out: pick_s(&surf_osc_co),
            surf_osc_c_zone: pick_s(&surf_osc_cz),
            script_f: sf,
            ctf_n_terms,
            ctf_outside: ctf_outside.clone(),
            ctf_cross: ctf_cross.clone(),
            ctf_inside: ctf_inside.clone(),
            ctf_flux: ctf_flux.clone(),
            weather_t_db: t_db_all[w_off..(w_off + n_w_steps)].to_vec(),
            weather_w_out: w_out_all[w_off..(w_off + n_w_steps)].to_vec(),
            weather_pb: pb_all[w_off..(w_off + n_w_steps)].to_vec(),
            weather_t_sky: t_sky_all[w_off..(w_off + n_w_steps)].to_vec(),
            wu_t_db: wu_db[wu_off..(wu_off + n_wu_steps)].to_vec(),
            wu_w_out: wu_w[wu_off..(wu_off + n_wu_steps)].to_vec(),
            wu_pb: wu_pb[wu_off..(wu_off + n_wu_steps)].to_vec(),
            wu_t_sky: wu_sky[wu_off..(wu_off + n_wu_steps)].to_vec(),
            gain_ts: gain_ts[w_off..(w_off + n_w_steps)].to_vec(),
            wu_gain: wu_gain[wu_off..(wu_off + n_wu_steps)].to_vec(),
            has_solar,
            q_sol_out: pack_sol(&q_sol_out_all, n_w_steps),
            q_sw_in: pack_sol(&q_sw_in_all, n_w_steps),
            q_sol_win: pack_sol(&q_sol_win_all, n_w_steps),
            wu_q_out: pack_sol(&wu_q_out, n_wu_steps),
            wu_q_in: pack_sol(&wu_q_in, n_wu_steps),
            wu_q_win: pack_sol(&wu_q_win, n_wu_steps),
            record_zone_temp,
        });
    }

    let outputs: Vec<BuildingStageAOutput> = py.detach(move || {
        if use_f32 {
            run_stage_a_batch_f32(&inputs)
        } else {
            run_stage_a_batch_f64(&inputs)
        }
    });

    let n_hours = n_run_steps / sph;
    let mut flat_hourly = Vec::with_capacity(b_size * n_hours);
    let mut flat_annual = Vec::with_capacity(b_size);
    let mut flat_warmup = Vec::with_capacity(b_size);
    let mut flat_zt = Vec::new();
    let mut flat_zm = Vec::new();
    if record_zone_temp {
        flat_zt.reserve(b_size * n_run_steps);
        flat_zm.reserve(b_size * n_run_steps);
    }
    for o in outputs {
        flat_hourly.extend_from_slice(&o.hourly_heating_j);
        flat_annual.push(o.annual_heating_kwh);
        flat_warmup.push(o.warmup_days);
        if record_zone_temp {
            flat_zt.extend_from_slice(&o.zone_air_temp_c);
            flat_zm.extend_from_slice(&o.zone_mean_air_temp_c);
        }
    }

    let h_arr = PyArray1::from_vec(py, flat_hourly)
        .reshape([b_size, n_hours])?
        .unbind();
    let a_arr = PyArray1::from_vec(py, flat_annual).unbind();
    let w_arr = PyArray1::from_vec(py, flat_warmup).unbind();
    let (zt_opt, zm_opt) = if record_zone_temp {
        (
            Some(
                PyArray1::from_vec(py, flat_zt)
                    .reshape([b_size, n_run_steps])?
                    .unbind(),
            ),
            Some(
                PyArray1::from_vec(py, flat_zm)
                    .reshape([b_size, n_run_steps])?
                    .unbind(),
            ),
        )
    } else {
        (None, None)
    };
    Ok((h_arr, a_arr, w_arr, zt_opt, zm_opt))
}
