//! Clean-room Rust implementation of `openubem/gpusim/shading.py::compute_exterior_shading`.

use rayon::prelude::*;

use crate::bvh::DistrictShadingBvh;

const T_EPS_M: f64 = 1.0e-3;
const NORMAL_NUDGE_M: f64 = 2.0e-3;

/// Fan-triangulate planar polygons from flattened CSR vertex slice `[V, 3]`.
pub fn triangulate_flattened_polygons(
    verts_flat: &[[f64; 3]],
    poly_offsets: &[u32],
) -> Vec<[[f64; 3]; 3]> {
    let n_polys = poly_offsets.len().saturating_sub(1);
    let mut tris = Vec::with_capacity(n_polys * 2);
    for p in 0..n_polys {
        let start = poly_offsets[p] as usize;
        let end = poly_offsets[p + 1] as usize;
        let n = end.saturating_sub(start);
        if n < 3 {
            continue;
        }
        let v0 = verts_flat[start];
        for i in 0..(n - 2) {
            tris.push([v0, verts_flat[start + i + 1], verts_flat[start + i + 2]]);
        }
    }
    tris
}

/// Exact bilinear / barycentric surface sample generator matching `_sample_polygon_points`.
pub fn sample_polygon_points(verts: &[[f64; 3]], n_grid: usize) -> Vec<[f64; 3]> {
    let n = verts.len();
    if n == 4 {
        let mut pts = Vec::with_capacity(n_grid * n_grid);
        let v0 = verts[0];
        let v1 = verts[1];
        let v2 = verts[2];
        let v3 = verts[3];
        let nf = n_grid as f64;
        for iu in 0..n_grid {
            let u = (iu as f64 + 0.5) / nf;
            for iv in 0..n_grid {
                let v = (iv as f64 + 0.5) / nf;
                let w0 = (1.0 - u) * (1.0 - v);
                let w1 = u * (1.0 - v);
                let w2 = u * v;
                let w3 = (1.0 - u) * v;
                pts.push([
                    w0 * v0[0] + w1 * v1[0] + w2 * v2[0] + w3 * v3[0],
                    w0 * v0[1] + w1 * v1[1] + w2 * v2[1] + w3 * v3[1],
                    w0 * v0[2] + w1 * v1[2] + w2 * v2[2] + w3 * v3[2],
                ]);
            }
        }
        return pts;
    }

    if n < 3 {
        return verts.first().map(|&p| vec![p]).unwrap_or_default();
    }
    let mut pts = Vec::with_capacity((n - 2) * if n_grid >= 3 { 4 } else { 1 });
    let a = verts[0];
    for i in 0..(n - 2) {
        let b = verts[i + 1];
        let c = verts[i + 2];
        pts.push([
            (a[0] + b[0] + c[0]) / 3.0,
            (a[1] + b[1] + c[1]) / 3.0,
            (a[2] + b[2] + c[2]) / 3.0,
        ]);
        if n_grid >= 3 {
            pts.push([
                0.6 * a[0] + 0.2 * b[0] + 0.2 * c[0],
                0.6 * a[1] + 0.2 * b[1] + 0.2 * c[1],
                0.6 * a[2] + 0.2 * b[2] + 0.2 * c[2],
            ]);
            pts.push([
                0.2 * a[0] + 0.6 * b[0] + 0.2 * c[0],
                0.2 * a[1] + 0.6 * b[1] + 0.2 * c[1],
                0.2 * a[2] + 0.6 * b[2] + 0.2 * c[2],
            ]);
            pts.push([
                0.2 * a[0] + 0.2 * b[0] + 0.6 * c[0],
                0.2 * a[1] + 0.2 * b[1] + 0.6 * c[1],
                0.2 * a[2] + 0.2 * b[2] + 0.6 * c[2],
            ]);
        }
    }
    pts
}

/// Generate `n_dirs` Fibonacci hemisphere directions matching `shading.py:185-192`.
pub fn fibonacci_hemisphere_dirs(n_dirs: usize) -> Vec<[f64; 3]> {
    let golden = std::f64::consts::PI * (3.0 - 5.0_f64.sqrt());
    let nf = n_dirs as f64;
    (0..n_dirs)
        .map(|i| {
            let idx = (i as f64) + 0.5;
            let z = idx / nf;
            let r = (1.0 - z * z).max(0.0).sqrt();
            let phi = golden * idx;
            [r * phi.cos(), r * phi.sin(), z]
        })
        .collect()
}

/// Output buffers matching `(sunlit_frac[8760, S], dif_shdg_iso_sky[S])`.
#[derive(Debug, Clone)]
pub struct ShadingResult {
    pub sunlit_hr: Vec<f32>,
    pub dif_sky: Vec<f64>,
}

/// Compute exterior beam sunlit fractions `[8760, S]` (row-major) and sky diffuse `[S]` using `obvhs` + `rayon`.
pub fn compute_exterior_shading(
    target_verts_flat: &[[f64; 3]],
    target_offsets: &[u32],
    target_normals: &[[f64; 3]],
    target_sun_exposed: &[bool],
    occ_verts_flat: &[[f64; 3]],
    occ_offsets: &[u32],
    solcos_hourly: &[[f64; 3]],
    periodic_days: usize,
    n_grid: usize,
    n_sky_rays: usize,
) -> ShadingResult {
    let n_surf = target_offsets.len().saturating_sub(1);
    let mut sunlit_hr = vec![1.0_f32; 8760 * n_surf];
    let mut dif_sky = vec![1.0_f64; n_surf];

    let has_any_sun = target_sun_exposed.iter().any(|&v| v);
    if occ_offsets.len() <= 1 || n_surf == 0 || !has_any_sun {
        return ShadingResult { sunlit_hr, dif_sky };
    }

    let tris = triangulate_flattened_polygons(occ_verts_flat, occ_offsets);
    if tris.is_empty() {
        return ShadingResult { sunlit_hr, dif_sky };
    }
    let bvh = DistrictShadingBvh::build(&tris);

    // Representative solar days + sunlit hours (`solcos_hourly[idx_h][2] > 0.01`).
    let step_days = periodic_days.max(1);
    let rep_days: Vec<usize> = (0..365).step_by(step_days).collect();
    let n_rep = rep_days.len();
    let mut rep_hours: Vec<(usize, usize, usize)> = Vec::new();
    for (di, &d) in rep_days.iter().enumerate() {
        for h in 0..24 {
            let idx_h = d * 24 + h;
            if solcos_hourly[idx_h][2] > 0.01 {
                rep_hours.push((di, h, idx_h));
            }
        }
    }
    let sky_dirs = fibonacci_hemisphere_dirs(n_sky_rays);

    // Build sample points per exposed surface, then evaluate each target surface independently in parallel!
    let surf_results: Vec<(usize, Vec<f32>, f64)> = (0..n_surf)
        .into_par_iter()
        .filter(|&s_idx| target_sun_exposed[s_idx])
        .filter_map(|s_idx| {
            let v_start = target_offsets[s_idx] as usize;
            let v_end = target_offsets[s_idx + 1] as usize;
            if v_end.saturating_sub(v_start) < 3 {
                return None;
            }
            let nrm = target_normals[s_idx];
            let mut pts = sample_polygon_points(&target_verts_flat[v_start..v_end], n_grid);
            if pts.is_empty() {
                return None;
            }
            for p in &mut pts {
                p[0] += NORMAL_NUDGE_M * nrm[0];
                p[1] += NORMAL_NUDGE_M * nrm[1];
                p[2] += NORMAL_NUDGE_M * nrm[2];
            }
            let inv_n_pts = 1.0 / (pts.len() as f64);

            // Representative [n_rep * 24] sunlit fractions initialized to 1.0.
            let mut rep_sun = vec![1.0_f32; n_rep * 24];
            for &(di, h, idx_h) in &rep_hours {
                let ray = solcos_hourly[idx_h];
                let dot_rn = ray[0] * nrm[0] + ray[1] * nrm[1] + ray[2] * nrm[2];
                // Pre-traversal backface cull matching shading.py:284 (`<= 0.0`).
                if dot_rn <= 0.0 {
                    continue;
                }
                let mut occ_cnt = 0usize;
                for &pt in &pts {
                    if bvh.is_occluded(pt, ray, T_EPS_M) {
                        occ_cnt += 1;
                    }
                }
                let frac = 1.0 - (occ_cnt as f64) * inv_n_pts;
                rep_sun[di * 24 + h] = frac as f32;
            }

            // Cosine-weighted sky diffuse factor (backface cull `cos_w > 0`).
            let mut num = 0.0_f64;
            let mut denom = 0.0_f64;
            for &sdir in &sky_dirs {
                let cos_w = sdir[0] * nrm[0] + sdir[1] * nrm[1] + sdir[2] * nrm[2];
                if cos_w <= 0.0 {
                    continue;
                }
                denom += cos_w;
                let mut occ_cnt = 0usize;
                for &pt in &pts {
                    if bvh.is_occluded(pt, sdir, T_EPS_M) {
                        occ_cnt += 1;
                    }
                }
                let vis = 1.0 - (occ_cnt as f64) * inv_n_pts;
                num += cos_w * vis;
            }
            let dif = if denom > 1.0e-9 { num / denom } else { 1.0 };

            Some((s_idx, rep_sun, dif))
        })
        .collect();

    for (s_idx, rep_sun, dif) in surf_results {
        dif_sky[s_idx] = dif;
        for d in 0..365 {
            let di = (d / step_days).min(n_rep - 1);
            for h in 0..24 {
                sunlit_hr[(d * 24 + h) * n_surf + s_idx] = rep_sun[di * 24 + h];
            }
        }
    }

    ShadingResult { sunlit_hr, dif_sky }
}
