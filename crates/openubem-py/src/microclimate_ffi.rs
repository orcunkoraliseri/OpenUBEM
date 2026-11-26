//! PyO3 FFI bindings for `openubem-microclimate`.

use numpy::{
    PyArray1, PyArray2, PyArray3, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2,
    PyReadonlyArray3, PyUntypedArrayMethods,
};
use openubem_microclimate::{
    building_shadow_from_horizon, classify_stress_batch, compute_svf, utci_approx_batch,
    vegetation_transmission,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Compute SVF `[rows, cols]` (`f32`) and horizon angles `[n_az, rows, cols]` (`f32`).
#[pyfunction]
pub fn micro_compute_svf<'py>(
    py: Python<'py>,
    dsm: PyReadonlyArray2<'py, f64>,
    dem: PyReadonlyArray2<'py, f64>,
    res_m: f64,
    pedestrian_height_m: f64,
    n_azimuths: usize,
    max_radius_px: usize,
) -> PyResult<(Py<PyArray2<f32>>, Py<PyArray3<f32>>)> {
    let sh = dsm.shape();
    if sh.len() != 2 || dem.shape() != sh {
        return Err(PyValueError::new_err("dsm and dem must have matching 2D shape"));
    }
    let (rows, cols) = (sh[0], sh[1]);
    let dsm_v: Vec<f64> = dsm.as_array().iter().copied().collect();
    let dem_v: Vec<f64> = dem.as_array().iter().copied().collect();

    let res = py.detach(move || {
        compute_svf(
            &dsm_v,
            &dem_v,
            rows,
            cols,
            res_m,
            pedestrian_height_m,
            n_azimuths,
            max_radius_px,
        )
    });

    let svf_arr = PyArray1::from_vec(py, res.svf).reshape([rows, cols])?.unbind();
    let hz_arr = PyArray1::from_vec(py, res.horizon_angles)
        .reshape([n_azimuths, rows, cols])?
        .unbind();
    Ok((svf_arr, hz_arr))
}

/// Evaluate hourly building SUNLIT bool raster `[rows, cols]` from cached horizon stack.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn micro_building_shadow_from_horizon<'py>(
    py: Python<'py>,
    dsm: PyReadonlyArray2<'py, f64>,
    dem: PyReadonlyArray2<'py, f64>,
    horizon_angles: PyReadonlyArray3<'py, f32>,
    pedestrian_height_m: f64,
    altitude_deg: f64,
    azimuth_deg: f64,
) -> PyResult<Py<PyArray2<bool>>> {
    let sh = dsm.shape();
    let hsh = horizon_angles.shape();
    if sh.len() != 2 || dem.shape() != sh || hsh.len() != 3 || hsh[1] != sh[0] || hsh[2] != sh[1] {
        return Err(PyValueError::new_err("dsm/dem/horizon shapes mismatch"));
    }
    let (rows, cols) = (sh[0], sh[1]);
    let n_az = hsh[0];
    let dsm_v: Vec<f64> = dsm.as_array().iter().copied().collect();
    let dem_v: Vec<f64> = dem.as_array().iter().copied().collect();
    let hz_v: Vec<f32> = horizon_angles.as_array().iter().copied().collect();

    let sunlit = py.detach(move || {
        building_shadow_from_horizon(
            &dsm_v,
            &dem_v,
            &hz_v,
            rows,
            cols,
            n_az,
            pedestrian_height_m,
            altitude_deg,
            azimuth_deg,
        )
    });
    Ok(PyArray1::from_vec(py, sunlit).reshape([rows, cols])?.unbind())
}

/// Evaluate Beer-Lambert vegetation transmission `[rows, cols]` (`f32`).
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn micro_vegetation_transmission<'py>(
    py: Python<'py>,
    dem: PyReadonlyArray2<'py, f64>,
    cdsm: PyReadonlyArray2<'py, f64>,
    tdsm: PyReadonlyArray2<'py, f64>,
    res_m: f64,
    pedestrian_height_m: f64,
    altitude_deg: f64,
    azimuth_deg: f64,
    canopy_tau: f64,
) -> PyResult<Py<PyArray2<f32>>> {
    let sh = dem.shape();
    if sh.len() != 2 || cdsm.shape() != sh || tdsm.shape() != sh {
        return Err(PyValueError::new_err("dem/cdsm/tdsm shapes must match"));
    }
    let (rows, cols) = (sh[0], sh[1]);
    let dem_v: Vec<f64> = dem.as_array().iter().copied().collect();
    let cdsm_v: Vec<f64> = cdsm.as_array().iter().copied().collect();
    let tdsm_v: Vec<f64> = tdsm.as_array().iter().copied().collect();

    let out = py.detach(move || {
        vegetation_transmission(
            &dem_v,
            &cdsm_v,
            &tdsm_v,
            rows,
            cols,
            res_m,
            pedestrian_height_m,
            altitude_deg,
            azimuth_deg,
            canopy_tau,
        )
    });
    Ok(PyArray1::from_vec(py, out).reshape([rows, cols])?.unbind())
}

/// Evaluate 210-term Bröde UTCI `[N]` (`f64`) + out-of-bounds flags `[N]` (`u8`).
#[pyfunction]
pub fn micro_utci_approx<'py>(
    py: Python<'py>,
    ta_c: PyReadonlyArray1<'py, f64>,
    tmrt_c: PyReadonlyArray1<'py, f64>,
    va10_ms: PyReadonlyArray1<'py, f64>,
    e_kpa: PyReadonlyArray1<'py, f64>,
) -> PyResult<(Py<PyArray1<f64>>, Py<PyArray1<u8>>)> {
    let ta: Vec<f64> = ta_c.as_array().iter().copied().collect();
    let tmrt: Vec<f64> = tmrt_c.as_array().iter().copied().collect();
    let va: Vec<f64> = va10_ms.as_array().iter().copied().collect();
    let ek: Vec<f64> = e_kpa.as_array().iter().copied().collect();
    if tmrt.len() != ta.len() || va.len() != ta.len() || ek.len() != ta.len() {
        return Err(PyValueError::new_err("UTCI input arrays must have equal flattened length"));
    }
    let (utci, flags) = py.detach(move || utci_approx_batch(&ta, &tmrt, &va, &ek));
    Ok((
        PyArray1::from_vec(py, utci).unbind(),
        PyArray1::from_vec(py, flags).unbind(),
    ))
}

/// Classify 10 official UTCI stress tiers `[N]` (`u8`, `NaN -> 255`).
#[pyfunction]
pub fn micro_classify_stress<'py>(
    py: Python<'py>,
    utci_c: PyReadonlyArray1<'py, f64>,
) -> Py<PyArray1<u8>> {
    let vals: Vec<f64> = utci_c.as_array().iter().copied().collect();
    let out = py.detach(move || classify_stress_batch(&vals));
    PyArray1::from_vec(py, out).unbind()
}
