//! Interior view-factor and ScriptF matrices using pure-Rust `faer` dense LU solve.

use faer::prelude::Solve;
use faer::Mat;
use rayon::prelude::*;

use crate::error::IdfError;

const SURF_FLOOR: i32 = 1;
const SURF_INTMASS: i32 = 5;
const SAME_ANGLE_LIMIT_DEG: f64 = 10.0;
const PRIMARY_CONVERGENCE: f64 = 0.001;
const DIFFERENCE_CONVERGENCE: f64 = 0.00001;
const MAX_FIX_ITERATIONS: usize = 400;
const MAX_EMISS_LIMIT: f64 = 0.99999;

/// Exact translation of `HeatBalanceIntRadExchange.cc::CalcApproximateViewFactors`.
pub fn calc_approximate_view_factors(
    areas: &[f64],
    azimuths: &[f64],
    tilts: &[f64],
    surf_classes: &[i32],
) -> Vec<f64> {
    let n = areas.len();
    let mut f_mat = vec![0.0_f64; n * n];
    let mut can_see = vec![false; n];
    for i in 0..n {
        let is_floor_i = surf_classes[i] == SURF_FLOOR;
        let is_im_i = surf_classes[i] == SURF_INTMASS;
        let mut zone_area = 0.0_f64;
        can_see.fill(false);
        for j in 0..n {
            let is_floor_j = surf_classes[j] == SURF_FLOOR;
            if i == j || (is_floor_i && is_floor_j) {
                continue;
            }
            let is_im_j = surf_classes[j] == SURF_INTMASS;
            let az_diff = (azimuths[i] - azimuths[j]).abs();
            let tilt_diff = (tilts[i] - tilts[j]).abs();
            if is_im_j
                || is_im_i
                || is_floor_j
                || is_floor_i
                || (az_diff > SAME_ANGLE_LIMIT_DEG && az_diff < 360.0 - SAME_ANGLE_LIMIT_DEG)
                || tilt_diff > SAME_ANGLE_LIMIT_DEG
            {
                can_see[j] = true;
                zone_area += areas[j];
            }
        }
        if zone_area > 0.0 {
            let row_off = i * n;
            for j in 0..n {
                if can_see[j] {
                    f_mat[row_off + j] = areas[j] / zone_area;
                }
            }
        }
    }
    f_mat
}

#[inline]
fn symmetrize_inplace(mat: &mut [f64], n: usize) {
    for i in 0..n {
        for j in (i + 1)..n {
            let avg = 0.5 * (mat[i * n + j] + mat[j * n + i]);
            mat[i * n + j] = avg;
            mat[j * n + i] = avg;
        }
    }
}

/// Exact translation of `HeatBalanceIntRadExchange.cc::FixViewFactors`.
pub fn fix_view_factors(areas: &[f64], f_approx: &[f64]) -> Vec<f64> {
    let n = areas.len();
    if n == 0 {
        return Vec::new();
    }
    let f_out = f_approx.to_vec();
    let orig_sum: f64 = f_out.iter().sum();
    let orig_check = (orig_sum - n as f64).abs();

    let mut fixed_af = vec![0.0_f64; n * n];
    fixed_af.copy_from_slice(f_approx);

    let total_area: f64 = areas.iter().sum();
    let mut largest_idx = 0usize;
    let mut largest_area = areas[0];
    for (idx, &a) in areas.iter().enumerate().skip(1) {
        if a > largest_area {
            largest_area = a;
            largest_idx = idx;
        }
    }
    if largest_area > 0.99 * (total_area - largest_area) && n > 3 {
        fixed_af[largest_idx * n + largest_idx] = (1.2 * largest_area / total_area).min(0.9);
    }

    for i in 0..n {
        let ai = areas[i];
        let off = i * n;
        for j in 0..n {
            fixed_af[off + j] *= ai;
        }
    }
    symmetrize_inplace(&mut fixed_af, n);

    let mut fixed_f = vec![0.0_f64; n * n];
    if n <= 3 {
        let mut row_sum_total = 0.0_f64;
        let mut max_row = 0.0_f64;
        for i in 0..n {
            let inv_a = 1.0 / areas[i];
            let mut rsum = 0.0_f64;
            for j in 0..n {
                let v = fixed_af[i * n + j] * inv_a;
                fixed_f[i * n + j] = v;
                rsum += v;
            }
            row_sum_total += rsum;
            max_row = max_row.max(rsum);
        }
        if row_sum_total > (n as f64) + 0.01 && max_row >= 1.0 {
            let scale = 1.0 / max_row;
            for v in &mut fixed_f {
                *v *= scale;
            }
        }
        return fixed_f;
    }

    let mut convrg_old = 10.0_f64;
    let mut num_iter = 0usize;

    loop {
        num_iter += 1;
        for i in 0..n {
            let off = i * n;
            let row_sum_af: f64 = fixed_af[off..(off + n)].iter().sum();
            let coef = if row_sum_af.abs() > 1.0e-10 {
                areas[i] / row_sum_af
            } else {
                1.0
            };
            for j in 0..n {
                fixed_af[off + j] *= coef;
            }
        }
        symmetrize_inplace(&mut fixed_af, n);

        let mut total_f_sum = 0.0_f64;
        for i in 0..n {
            let inv_a = 1.0 / areas[i];
            let off = i * n;
            for j in 0..n {
                let mut v = fixed_af[off + j] * inv_a;
                if v.abs() < 1.0e-10 {
                    v = 0.0;
                    fixed_af[off + j] = 0.0;
                }
                fixed_f[off + j] = v;
                total_f_sum += v;
            }
        }

        let convrg_new = (total_f_sum - n as f64).abs();
        if (convrg_old - convrg_new).abs() < DIFFERENCE_CONVERGENCE
            || convrg_new <= PRIMARY_CONVERGENCE
        {
            if convrg_new < orig_check || convrg_new < PRIMARY_CONVERGENCE {
                return fixed_f;
            }
            return f_out;
        }
        convrg_old = convrg_new;

        if num_iter > MAX_FIX_ITERATIONS {
            symmetrize_inplace(&mut fixed_af, n);
            let mut sum_f = 0.0_f64;
            for i in 0..n {
                let inv_a = 1.0 / areas[i];
                for j in 0..n {
                    let v = fixed_af[i * n + j] * inv_a;
                    fixed_f[i * n + j] = v;
                    sum_f += v;
                }
            }
            let fixed_check = (sum_f - n as f64).abs();
            if fixed_check < orig_check {
                return fixed_f;
            }
            return f_out;
        }
    }
}

/// Exact translation of `HeatBalanceIntRadExchange.cc::CalcScriptF` using pure-Rust `faer` LU solve.
pub fn calc_script_f(areas: &[f64], f_mat: &[f64], emiss: &[f64]) -> Result<Vec<f64>, IdfError> {
    let n = areas.len();
    if n == 0 {
        return Ok(Vec::new());
    }
    let mut eps = Vec::with_capacity(n);
    let mut inv_one_minus_eps = Vec::with_capacity(n);
    let mut excite = Vec::with_capacity(n);
    for i in 0..n {
        let e = emiss[i].min(MAX_EMISS_LIMIT);
        let inv = 1.0 / (1.0 - e);
        eps.push(e);
        inv_one_minus_eps.push(inv);
        excite.push(-e * areas[i] * inv);
    }

    // c_mat[i, j] = areas[i] * f_mat[j, i], minus delta_{ij} * areas[i] / (1 - eps[i])
    let mut c_mat = Mat::<f64>::zeros(n, n);
    let mut rhs = Mat::<f64>::zeros(n, n);
    for i in 0..n {
        for j in 0..n {
            let mut v = areas[i] * f_mat[j * n + i];
            if i == j {
                v -= areas[i] * inv_one_minus_eps[i];
            }
            c_mat[(i, j)] = v;
            if i == j {
                rhs[(i, j)] = excite[j];
            }
        }
    }

    let lu = c_mat.partial_piv_lu();
    let j_mat = lu.solve(&rhs);

    let mut script_f = vec![0.0_f64; n * n];
    for i in 0..n {
        for j in 0..n {
            // script_f_raw[j, i] transposed -> [i, j] = eps_fac[j] * (j_mat[j, i] - delta_{ji}*eps[j])
            let eps_fac_j = eps[j] * inv_one_minus_eps[j];
            let diag = if i == j { eps[j] } else { 0.0 };
            let val = eps_fac_j * (j_mat[(j, i)] - diag);
            if !val.is_finite() {
                return Err(IdfError::LinalgError(format!(
                    "non-finite ScriptF entry at ({i}, {j})"
                )));
            }
            script_f[i * n + j] = val;
        }
    }
    Ok(script_f)
}

/// Parallel zone ScriptF batch evaluation across `rayon`.
pub fn calc_zone_view_and_script_f_batch(
    zone_areas: &[Vec<f64>],
    zone_azimuths: &[Vec<f64>],
    zone_tilts: &[Vec<f64>],
    zone_classes: &[Vec<i32>],
    zone_emiss: &[Vec<f64>],
) -> Result<Vec<(Vec<f64>, Vec<f64>)>, IdfError> {
    (0..zone_areas.len())
        .into_par_iter()
        .map(|idx| {
            let f_approx = calc_approximate_view_factors(
                &zone_areas[idx],
                &zone_azimuths[idx],
                &zone_tilts[idx],
                &zone_classes[idx],
            );
            let f_fixed = fix_view_factors(&zone_areas[idx], &f_approx);
            let sf = calc_script_f(&zone_areas[idx], &f_fixed, &zone_emiss[idx])?;
            Ok((f_fixed, sf))
        })
        .collect()
}
