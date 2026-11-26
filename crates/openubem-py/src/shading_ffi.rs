//! PyO3 FFI bindings for `openubem-shading`.

use numpy::{PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2, PyUntypedArrayMethods};
use openubem_shading::compute_exterior_shading;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn to_vec3(arr: &PyReadonlyArray2<'_, f64>, name: &str) -> PyResult<Vec<[f64; 3]>> {
    let shape = arr.shape();
    if shape.len() != 2 || shape[1] != 3 {
        return Err(PyValueError::new_err(format!(
            "{name} must have shape [N, 3], got {shape:?}"
        )));
    }
    let view = arr.as_array();
    let n = shape[0];
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let p = [view[[i, 0]], view[[i, 1]], view[[i, 2]]];
        if !p[0].is_finite() || !p[1].is_finite() || !p[2].is_finite() {
            return Err(PyValueError::new_err(format!(
                "{name} contains non-finite value at row {i}"
            )));
        }
        out.push(p);
    }
    Ok(out)
}

fn validate_offsets(offsets: &[u32], n_verts: usize, name: &str) -> PyResult<()> {
    if offsets.is_empty() {
        return Err(PyValueError::new_err(format!("{name} must have len >= 1")));
    }
    let mut prev = offsets[0];
    if prev != 0 {
        return Err(PyValueError::new_err(format!("{name}[0] must be 0, got {prev}")));
    }
    for (idx, &cur) in offsets.iter().enumerate().skip(1) {
        if cur < prev || (cur as usize) > n_verts {
            return Err(PyValueError::new_err(format!(
                "{name}[{idx}]={cur} invalid (prev={prev}, n_verts={n_verts})"
            )));
        }
        prev = cur;
    }
    Ok(())
}

/// Compute exterior solar beam sunlit fractions `[8760, S]` (`float32`) and diffuse sky factors `[S]` (`float64`).
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn shading_compute_exterior<'py>(
    py: Python<'py>,
    target_verts_flat: PyReadonlyArray2<'py, f64>,
    target_offsets: PyReadonlyArray1<'py, u32>,
    target_normals: PyReadonlyArray2<'py, f64>,
    target_sun_exposed: PyReadonlyArray1<'py, bool>,
    occ_verts_flat: PyReadonlyArray2<'py, f64>,
    occ_offsets: PyReadonlyArray1<'py, u32>,
    solcos_hourly: PyReadonlyArray2<'py, f64>,
    periodic_days: usize,
    n_grid: usize,
    n_sky_rays: usize,
) -> PyResult<(Py<PyArray2<f32>>, Py<PyArray1<f64>>)> {
    let t_verts = to_vec3(&target_verts_flat, "target_verts_flat")?;
    let t_offsets: Vec<u32> = target_offsets.as_array().iter().copied().collect();
    validate_offsets(&t_offsets, t_verts.len(), "target_offsets")?;

    let n_surf = t_offsets.len() - 1;
    let t_normals = to_vec3(&target_normals, "target_normals")?;
    if t_normals.len() != n_surf {
        return Err(PyValueError::new_err(format!(
            "target_normals rows ({}) != target surface count ({n_surf})",
            t_normals.len()
        )));
    }
    let t_sun_exposed: Vec<bool> = target_sun_exposed.as_array().iter().copied().collect();
    if t_sun_exposed.len() != n_surf {
        return Err(PyValueError::new_err(format!(
            "target_sun_exposed len ({}) != target surface count ({n_surf})",
            t_sun_exposed.len()
        )));
    }

    let o_verts = to_vec3(&occ_verts_flat, "occ_verts_flat")?;
    let o_offsets: Vec<u32> = occ_offsets.as_array().iter().copied().collect();
    validate_offsets(&o_offsets, o_verts.len(), "occ_offsets")?;

    let solcos = to_vec3(&solcos_hourly, "solcos_hourly")?;
    if solcos.len() != 8760 {
        return Err(PyValueError::new_err(format!(
            "solcos_hourly must have 8760 rows, got {}",
            solcos.len()
        )));
    }

    let res = py.detach(move || {
        compute_exterior_shading(
            &t_verts,
            &t_offsets,
            &t_normals,
            &t_sun_exposed,
            &o_verts,
            &o_offsets,
            &solcos,
            periodic_days,
            n_grid,
            n_sky_rays,
        )
    });

    let sunlit_arr = PyArray1::from_vec(py, res.sunlit_hr)
        .reshape([8760, n_surf])?
        .unbind();
    let dif_arr = PyArray1::from_vec(py, res.dif_sky).unbind();
    Ok((sunlit_arr, dif_arr))
}
