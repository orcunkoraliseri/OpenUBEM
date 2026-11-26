//! Diagonal modal state-space conduction model (`build_modal_conduction`) using `nalgebra`.

use nalgebra::{DMatrix, SymmetricEigen};

use crate::error::IdfError;

/// One opaque construction layer ordered outside -> inside.
#[derive(Debug, Clone)]
pub struct LayerSpec {
    pub name: String,
    pub is_nomass: bool,
    pub r_value: f64,
    pub thickness: f64,
    pub conductivity: f64,
    pub density: f64,
    pub specific_heat: f64,
}

/// Diagonal modal state-space conduction coefficients (matches `ctf.py::ModalConductionModel`).
#[derive(Debug, Clone)]
pub struct ModalConductionModel {
    pub construction_name: String,
    pub num_modes: usize,
    pub dt_sec: f64,
    pub u_steady: f64,
    pub ctf_out0: f64,
    pub ctf_cross0: f64,
    pub ctf_in0: f64,
    pub decay: Vec<f64>,
    pub g_new_out: Vec<f64>,
    pub g_new_in: Vec<f64>,
    pub g_old_out: Vec<f64>,
    pub g_old_in: Vec<f64>,
    pub c_out: Vec<f64>,
    pub c_in: Vec<f64>,
    pub steady_out: Vec<f64>,
    pub steady_in: Vec<f64>,
}

/// Build an exact diagonal modal state-space conduction model using pure-Rust `nalgebra`.
pub fn build_modal_conduction(
    layers: &[LayerSpec],
    dt_sec: f64,
    construction_name: &str,
    max_modes: usize,
) -> Result<ModalConductionModel, IdfError> {
    if layers.is_empty() {
        return Err(IdfError::InvalidInput(format!(
            "Construction '{construction_name}' has no layers"
        )));
    }

    let mut total_r = 0.0_f64;
    let mut has_mass = false;
    for ly in layers {
        if ly.is_nomass {
            total_r += ly.r_value;
        } else {
            if ly.conductivity <= 0.0 {
                return Err(IdfError::InvalidInput(format!(
                    "Layer '{}' has non-positive conductivity {}",
                    ly.name, ly.conductivity
                )));
            }
            total_r += ly.thickness / ly.conductivity;
            if ly.density * ly.specific_heat * ly.thickness > 0.0 {
                has_mass = true;
            }
        }
    }
    let u_steady = 1.0 / total_r.max(1.0e-12);

    if !has_mass {
        return Ok(ModalConductionModel {
            construction_name: construction_name.to_string(),
            num_modes: 0,
            dt_sec,
            u_steady,
            ctf_out0: u_steady,
            ctf_cross0: u_steady,
            ctf_in0: u_steady,
            decay: Vec::new(),
            g_new_out: Vec::new(),
            g_new_in: Vec::new(),
            g_old_out: Vec::new(),
            g_old_in: Vec::new(),
            c_out: Vec::new(),
            c_in: Vec::new(),
            steady_out: Vec::new(),
            steady_in: Vec::new(),
        });
    }

    let max_m = max_modes.max(1);
    let mut massive_indices: Vec<usize> = Vec::new();
    let mut raw_counts: Vec<usize> = vec![0; layers.len()];
    for (idx, ly) in layers.iter().enumerate() {
        if !ly.is_nomass && ly.density * ly.specific_heat * ly.thickness > 0.0 {
            massive_indices.push(idx);
            let r_ly = ly.thickness / ly.conductivity;
            let c_ly = ly.density * ly.specific_heat * ly.thickness;
            let n_sub = (1.5 * (r_ly * c_ly / dt_sec.max(60.0)).max(1.0).sqrt()).ceil() as usize;
            raw_counts[idx] = n_sub.clamp(2, max_m);
        }
    }

    while raw_counts.iter().sum::<usize>() > max_m {
        let mut best_idx = None;
        let mut best_val = 1usize;
        for &idx in &massive_indices {
            if raw_counts[idx] > best_val {
                best_val = raw_counts[idx];
                best_idx = Some(idx);
            }
        }
        match best_idx {
            Some(idx) => raw_counts[idx] -= 1,
            None => break,
        }
    }

    let mut node_caps: Vec<f64> = Vec::new();
    let mut r_between: Vec<f64> = vec![0.0];
    for (idx, ly) in layers.iter().enumerate() {
        let n_sub = raw_counts[idx];
        if n_sub == 0 {
            let r = if ly.is_nomass {
                ly.r_value
            } else {
                ly.thickness / ly.conductivity
            };
            if let Some(last) = r_between.last_mut() {
                *last += r;
            }
            continue;
        }
        let r_ly = ly.thickness / ly.conductivity;
        let c_ly = ly.density * ly.specific_heat * ly.thickness;
        let r_sub = r_ly / (n_sub as f64);
        let c_sub = c_ly / (n_sub as f64);
        for _ in 0..n_sub {
            if let Some(last) = r_between.last_mut() {
                *last += 0.5 * r_sub;
            }
            node_caps.push(c_sub);
            r_between.push(0.5 * r_sub);
        }
    }

    let n_nodes = node_caps.len();
    let g_arr: Vec<f64> = r_between.iter().map(|&r| 1.0 / r.max(1.0e-15)).collect();
    let sqrt_c: Vec<f64> = node_caps.iter().map(|&c| c.sqrt()).collect();
    let inv_sqrt_c: Vec<f64> = sqrt_c.iter().map(|&s| 1.0 / s).collect();

    let mut m_mat = DMatrix::<f64>::zeros(n_nodes, n_nodes);
    for i in 0..n_nodes {
        m_mat[(i, i)] = -(g_arr[i] + g_arr[i + 1]) / node_caps[i];
        if i + 1 < n_nodes {
            let off = g_arr[i + 1] / (sqrt_c[i] * sqrt_c[i + 1]);
            m_mat[(i, i + 1)] = off;
            m_mat[(i + 1, i)] = off;
        }
    }

    let eig = SymmetricEigen::new(m_mat);
    let mut order: Vec<usize> = (0..n_nodes).collect();
    // Sort by -eigenvalue ascending (slowest mode = least negative eigenvalue first).
    order.sort_by(|&a, &b| {
        (-eig.eigenvalues[a])
            .partial_cmp(&(-eig.eigenvalues[b]))
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    let mut lam = Vec::with_capacity(n_nodes);
    let mut decay = Vec::with_capacity(n_nodes);
    let mut g_new_out = Vec::with_capacity(n_nodes);
    let mut g_new_in = Vec::with_capacity(n_nodes);
    let mut g_old_out = Vec::with_capacity(n_nodes);
    let mut g_old_in = Vec::with_capacity(n_nodes);
    let mut c_out = Vec::with_capacity(n_nodes);
    let mut c_in = Vec::with_capacity(n_nodes);
    let mut steady_out = Vec::with_capacity(n_nodes);
    let mut steady_in = Vec::with_capacity(n_nodes);

    for &col in &order {
        let lk = (-eig.eigenvalues[col]).max(1.0e-15);
        lam.push(lk);

        let q0 = eig.eigenvectors[(0, col)];
        let qn = eig.eigenvectors[(n_nodes - 1, col)];
        let bm0 = q0 * (g_arr[0] * inv_sqrt_c[0]);
        let bm1 = qn * (g_arr[n_nodes] * inv_sqrt_c[n_nodes - 1]);
        let cm0 = -g_arr[0] * inv_sqrt_c[0] * q0;
        let cm1 = g_arr[n_nodes] * inv_sqrt_c[n_nodes - 1] * qn;

        let a = lk * dt_sec;
        let e = (-a).exp();
        let phi0 = if a < 1.0e-4 {
            1.0 - 0.5 * a + (a * a) / 6.0 - (a * a * a) / 24.0
        } else {
            (1.0 - e) / a
        };
        let w_new = if a < 1.0e-4 {
            dt_sec * (0.5 - a / 6.0 + (a * a) / 24.0 - (a * a * a) / 120.0)
        } else {
            dt_sec * (1.0 - phi0) / a
        };
        let w_old = if a < 1.0e-4 {
            dt_sec * (0.5 - a / 3.0 + (a * a) / 8.0 - (a * a * a) / 30.0)
        } else {
            dt_sec * (phi0 - e) / a
        };

        decay.push(e);
        g_new_out.push(w_new * bm0);
        g_new_in.push(w_new * bm1);
        g_old_out.push(w_old * bm0);
        g_old_in.push(w_old * bm1);
        c_out.push(cm0);
        c_in.push(cm1);
        steady_out.push(bm0 / lk);
        steady_in.push(bm1 / lk);
    }

    let ctf_out0 = g_arr[0]
        + c_out
            .iter()
            .zip(g_new_out.iter())
            .map(|(&c, &g)| c * g)
            .sum::<f64>();
    let ctf_cross0 = -c_out
        .iter()
        .zip(g_new_in.iter())
        .map(|(&c, &g)| c * g)
        .sum::<f64>();
    let ctf_in0 = g_arr[n_nodes]
        - c_in
            .iter()
            .zip(g_new_in.iter())
            .map(|(&c, &g)| c * g)
            .sum::<f64>();

    let mut q_in_iso = ctf_cross0 - ctf_in0;
    let mut q_in_unit = ctf_cross0;
    for k in 0..n_nodes {
        q_in_iso += c_in[k] * (decay[k] * (steady_out[k] + steady_in[k]) + g_old_out[k] + g_old_in[k]);
        q_in_unit += c_in[k] * (decay[k] * steady_out[k] + g_old_out[k]);
    }
    if q_in_iso.abs() > 1.0e-7 || (q_in_unit - u_steady).abs() > 1.0e-6 * u_steady.max(1.0) {
        return Err(IdfError::CtfError(format!(
            "Modal conduction conservation check failed for '{construction_name}': q_iso={q_in_iso:.3e}, q_unit={q_in_unit:.6} vs U={u_steady:.6}"
        )));
    }

    Ok(ModalConductionModel {
        construction_name: construction_name.to_string(),
        num_modes: n_nodes,
        dt_sec,
        u_steady,
        ctf_out0,
        ctf_cross0,
        ctf_in0,
        decay,
        g_new_out,
        g_new_in,
        g_old_out,
        g_old_in,
        c_out,
        c_in,
        steady_out,
        steady_in,
    })
}
