//! Clean-room L1/L2-tiled SVF + horizon-angle solver (zeros out `np.pad`, 1 `atan` per azimuth/pixel).

use rayon::prelude::*;

/// Output of [`compute_svf`]: `svf` `[rows * cols]` (`f32`), `horizon_angles` `[n_az * rows * cols]` (`f32` degrees).
#[derive(Debug, Clone)]
pub struct SvfResult {
    pub svf: Vec<f32>,
    pub horizon_angles: Vec<f32>,
}

/// Compute sky view factor (`[0, 1]`) and per-azimuth horizon angles (degrees, `>= 0`).
///
/// Uses `max_slope = max_{d}((dsm[r+dr, c+dc] - z_obs[r, c]) / (d * res))` followed by a single
/// `atan(max_slope)` per azimuth per pixel, omitting all temporary `np.pad` buffers.
pub fn compute_svf(
    dsm: &[f64],
    dem: &[f64],
    rows: usize,
    cols: usize,
    res_m: f64,
    pedestrian_height_m: f64,
    n_azimuths: usize,
    max_radius_px: usize,
) -> SvfResult {
    let n_pix = rows * cols;
    let mut svf = vec![0.0_f32; n_pix];
    let mut horizon_angles = vec![0.0_f32; n_azimuths * n_pix];
    if rows == 0 || cols == 0 || n_azimuths == 0 {
        svf.fill(1.0);
        return SvfResult {
            svf,
            horizon_angles,
        };
    }

    let z_obs: Vec<f64> = dem.iter().map(|&z| z + pedestrian_height_m).collect();
    let rad = max_radius_px;

    // Precompute integer step offsets and inverse physical distances once per azimuth.
    let az_steps: Vec<Vec<(isize, isize, f64)>> = (0..n_azimuths)
        .map(|k| {
            let az_rad = ((k as f64) * 360.0 / (n_azimuths as f64)).to_radians();
            let sin_a = az_rad.sin();
            let cos_a = az_rad.cos();
            (1..=rad)
                .map(|d| {
                    let df = d as f64;
                    let drow = -((df * cos_a).round() as isize);
                    let dcol = (df * sin_a).round() as isize;
                    (drow, dcol, 1.0 / (df * res_m))
                })
                .collect()
        })
        .collect();

    // Compute per-pixel across all azimuths cleanly in row-major chunks so z_obs stays in L1 cache.
    let n_az_f = n_azimuths as f64;
    let rad_to_deg = 180.0 / std::f64::consts::PI;

    // Temporary `[rows * cols]` accumulator for SVF sum(cos^2(gamma)), while writing horizon_angles rows.
    // Instead of atomic writes to strided `horizon_angles`, parallelize per azimuth k when n_azimuths >= 8,
    // or per row stripe to keep cache locality! Since n_azimuths = 32 across rows is independent per k,
    // each azimuth slice `&mut horizon_angles[k*n_pix .. (k+1)*n_pix]` is disjoint!
    horizon_angles
        .par_chunks_mut(n_pix)
        .enumerate()
        .for_each(|(k, hz_plane)| {
            let steps = &az_steps[k];
            for r in 0..rows {
                let row_off = r * cols;
                // Tile across columns in 64-element L1-friendly vectors for auto-vectorization / pulp
                let mut c0 = 0usize;
                while c0 < cols {
                    let c1 = (c0 + 64).min(cols);
                    let tile_len = c1 - c0;
                    let mut max_slope = [0.0_f64; 64];

                    for &(drow, dcol, inv_dist) in steps {
                        let rr = (r as isize) + drow;
                        if rr < 0 || rr >= (rows as isize) {
                            continue;
                        }
                        let nb_row_off = (rr as usize) * cols;
                        for t in 0..tile_len {
                            let cc = ((c0 + t) as isize) + dcol;
                            if cc < 0 || cc >= (cols as isize) {
                                continue;
                            }
                            let dz = dsm[nb_row_off + (cc as usize)] - z_obs[row_off + c0 + t];
                            let slope = dz * inv_dist;
                            if slope > max_slope[t] {
                                max_slope[t] = slope;
                            }
                        }
                    }

                    for t in 0..tile_len {
                        let s = max_slope[t];
                        let deg = if s > 0.0 { s.atan() * rad_to_deg } else { 0.0 };
                        hz_plane[row_off + c0 + t] = deg as f32;
                    }
                    c0 = c1;
                }
            }
        });

    // Reduce horizon_angles -> svf = mean(cos^2(rad(gamma))) matching svf.py lines 63-64.
    svf.par_chunks_mut(cols).enumerate().for_each(|(r, svf_row)| {
        let row_off = r * cols;
        for c in 0..cols {
            let idx = row_off + c;
            let mut acc = 0.0_f64;
            for k in 0..n_azimuths {
                let deg = horizon_angles[k * n_pix + idx] as f64;
                let cos_g = deg.to_radians().cos();
                acc += cos_g * cos_g;
            }
            let mean_v = (acc / n_az_f).clamp(0.0, 1.0);
            svf_row[c] = mean_v as f32;
        }
    });

    SvfResult {
        svf,
        horizon_angles,
    }
}
