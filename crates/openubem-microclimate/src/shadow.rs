//! Clean-room zero-padding Beer-Lambert canopy transmission & building horizon shadow mapper.

use rayon::prelude::*;

/// Evaluate interpolated horizon shadow indicator (`true` = SUNLIT) from precomputed horizon stack.
pub fn building_shadow_from_horizon(
    dsm: &[f64],
    dem: &[f64],
    horizon_angles: &[f32],
    rows: usize,
    cols: usize,
    n_azimuths: usize,
    pedestrian_height_m: f64,
    altitude_deg: f64,
    azimuth_deg: f64,
) -> Vec<bool> {
    let n_pix = rows * cols;
    if altitude_deg <= 0.0 || n_pix == 0 || n_azimuths == 0 {
        return vec![false; n_pix];
    }
    let bin_step = 360.0 / (n_azimuths as f64);
    let az = azimuth_deg.rem_euclid(360.0);
    let idx_f = az / bin_step;
    let idx0 = (idx_f.floor() as usize) % n_azimuths;
    let idx1 = (idx0 + 1) % n_azimuths;
    let frac = idx_f - idx_f.floor();
    let one_minus_f = 1.0 - frac;

    let mut out = vec![false; n_pix];
    let p0 = &horizon_angles[(idx0 * n_pix)..((idx0 + 1) * n_pix)];
    let p1 = &horizon_angles[(idx1 * n_pix)..((idx1 + 1) * n_pix)];

    out.par_iter_mut().enumerate().for_each(|(i, sunlit)| {
        let hz = one_minus_f * (p0[i] as f64) + frac * (p1[i] as f64);
        let z_obs = dem[i] + pedestrian_height_m;
        let blocked = (altitude_deg <= hz) || (dsm[i] > z_obs);
        *sunlit = !blocked;
    });
    out
}

/// Evaluate Beer-Lambert canopy direct-beam transmission `sh_veg` in `[0, 1]` without `np.pad`.
pub fn vegetation_transmission(
    dem: &[f64],
    cdsm: &[f64],
    tdsm: &[f64],
    rows: usize,
    cols: usize,
    res_m: f64,
    pedestrian_height_m: f64,
    altitude_deg: f64,
    azimuth_deg: f64,
    canopy_tau: f64,
) -> Vec<f32> {
    let n_pix = rows * cols;
    if altitude_deg <= 0.0 {
        return vec![0.0_f32; n_pix];
    }
    let mut has_canopy = false;
    let mut canopy_top = f64::NEG_INFINITY;
    for &c in cdsm {
        if c > 0.0 {
            has_canopy = true;
            if c > canopy_top {
                canopy_top = c;
            }
        }
    }
    if !has_canopy {
        return vec![1.0_f32; n_pix];
    }

    let alt_r = altitude_deg.to_radians();
    let az_r = azimuth_deg.to_radians();
    let sin_a = az_r.sin();
    let cos_a = az_r.cos();
    let tan_alt = alt_r.tan();
    let log_tau_ref = canopy_tau.ln();
    let max_rad = (((rows * rows + cols * cols) as f64).sqrt()).ceil() as usize;

    let steps: Vec<(isize, isize, f64)> = (0..=max_rad)
        .map(|d| {
            let df = d as f64;
            let drow = -((df * cos_a).round() as isize);
            let dcol = (df * sin_a).round() as isize;
            let dh_next = (df + 1.0) * res_m * tan_alt;
            (drow, dcol, dh_next)
        })
        .collect();

    let crown_depth: Vec<f64> = cdsm
        .iter()
        .zip(tdsm.iter())
        .map(|(&c, &t)| (c - t).max(1.0e-6))
        .collect();

    let mut out = vec![1.0_f32; n_pix];
    out.par_chunks_mut(cols).enumerate().for_each(|(r, out_row)| {
        let row_off = r * cols;
        for c in 0..cols {
            let z_obs = dem[row_off + c] + pedestrian_height_m;
            let mut accum_log_t = 0.0_f64;
            let mut ray_h_prev = z_obs;

            for &(drow, dcol, dh_next) in &steps {
                let ray_h_next = z_obs + dh_next;
                let rr = (r as isize) + drow;
                let cc = (c as isize) + dcol;
                if rr >= 0 && rr < (rows as isize) && cc >= 0 && cc < (cols as isize) {
                    let nb_idx = (rr as usize) * cols + (cc as usize);
                    let cwin = cdsm[nb_idx];
                    if cwin > 0.0 {
                        let twin = tdsm[nb_idx];
                        let top = cwin.min(ray_h_next);
                        let bottom = ray_h_prev.max(twin);
                        if top > bottom {
                            accum_log_t += ((top - bottom) / crown_depth[nb_idx]) * log_tau_ref;
                        }
                    }
                }
                ray_h_prev = ray_h_next;
                if ray_h_next > canopy_top {
                    break;
                }
            }
            out_row[c] = accum_log_t.exp() as f32;
        }
    });

    out
}
