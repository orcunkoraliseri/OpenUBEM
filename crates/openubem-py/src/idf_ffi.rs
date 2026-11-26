//! PyO3 FFI bindings for `openubem-idf`.

use std::path::PathBuf;

use numpy::{PyArray1, PyArray2, PyArrayMethods, PyReadonlyArray1, PyReadonlyArray2, PyUntypedArrayMethods};
use openubem_idf::{
    LayerSpec, build_modal_conduction, calc_approximate_view_factors, calc_script_f,
    calc_zone_view_and_script_f_batch, check_surface_construction_links,
    compile_schedule_compact_hourly, fix_view_factors, load_schedule_file_hourly, parse_idf_bytes,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

type ModalOutput<'py> = ((usize, f64, f64, f64, f64), Py<PyArray2<f64>>);

/// Zero-copy IDF/ExpIDF parser returning `(OBJ_TYPE, raw_type, fields)` tuples.
#[pyfunction]
pub fn idf_parse_objects(
    py: Python<'_>,
    idf_text: &str,
) -> PyResult<Vec<(String, String, Vec<String>)>> {
    let owned = idf_text.as_bytes().to_vec();
    let objs = py.detach(move || parse_idf_bytes(&owned));
    Ok(objs
        .into_iter()
        .map(|o| (o.obj_type, o.raw_type, o.fields))
        .collect())
}

/// Fast CSV column loader for `Schedule:File` returning float64 `[num_hours]` array.
#[pyfunction]
pub fn idf_load_schedule_file_hourly<'py>(
    py: Python<'py>,
    csv_path: &str,
    column_number: usize,
    rows_to_skip: usize,
    num_hours: usize,
    delimiter: &str,
) -> PyResult<Py<PyArray1<f64>>> {
    let delim = delimiter
        .bytes()
        .next()
        .ok_or_else(|| PyValueError::new_err("delimiter must be non-empty"))?;
    let path = PathBuf::from(csv_path);
    let vals = py
        .detach(move || {
            load_schedule_file_hourly(&path, column_number, rows_to_skip, num_hours, delim)
        })
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec(py, vals).unbind())
}

/// Compile `Schedule:Compact` fields into 8,760 hourly float64 values.
#[pyfunction]
pub fn idf_compile_schedule_compact_hourly<'py>(
    py: Python<'py>,
    fields: Vec<String>,
    start_day_of_week: usize,
) -> PyResult<Py<PyArray1<f64>>> {
    let vals = py
        .detach(move || compile_schedule_compact_hourly(&fields, start_day_of_week))
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(PyArray1::from_vec(py, vals).unbind())
}

/// Compute diagonal modal state-space conduction matrices using `nalgebra`.
#[pyfunction]
pub fn idf_build_modal_conduction<'py>(
    py: Python<'py>,
    layers: Vec<(String, bool, f64, f64, f64, f64, f64)>,
    dt_sec: f64,
    construction_name: &str,
    max_modes: usize,
) -> PyResult<ModalOutput<'py>> {
    let specs: Vec<LayerSpec> = layers
        .into_iter()
        .map(
            |(name, is_nomass, r_value, thickness, conductivity, density, specific_heat)| LayerSpec {
                name,
                is_nomass,
                r_value,
                thickness,
                conductivity,
                density,
                specific_heat,
            },
        )
        .collect();
    let cname = construction_name.to_string();
    let model = py
        .detach(move || build_modal_conduction(&specs, dt_sec, &cname, max_modes))
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    let k = model.num_modes;
    let mut stacked = Vec::with_capacity(9 * k);
    stacked.extend_from_slice(&model.decay);
    stacked.extend_from_slice(&model.g_new_out);
    stacked.extend_from_slice(&model.g_new_in);
    stacked.extend_from_slice(&model.g_old_out);
    stacked.extend_from_slice(&model.g_old_in);
    stacked.extend_from_slice(&model.c_out);
    stacked.extend_from_slice(&model.c_in);
    stacked.extend_from_slice(&model.steady_out);
    stacked.extend_from_slice(&model.steady_in);
    let mat = PyArray1::from_vec(py, stacked).reshape([9, k])?.unbind();

    Ok((
        (
            model.num_modes,
            model.u_steady,
            model.ctf_out0,
            model.ctf_cross0,
            model.ctf_in0,
        ),
        mat,
    ))
}

/// Interior approximate view factors `[N, N]`.
#[pyfunction]
pub fn idf_calc_approximate_view_factors<'py>(
    py: Python<'py>,
    areas: PyReadonlyArray1<'py, f64>,
    azimuths: PyReadonlyArray1<'py, f64>,
    tilts: PyReadonlyArray1<'py, f64>,
    surf_classes: PyReadonlyArray1<'py, i32>,
) -> PyResult<Py<PyArray2<f64>>> {
    let a: Vec<f64> = areas.as_array().iter().copied().collect();
    let az: Vec<f64> = azimuths.as_array().iter().copied().collect();
    let tl: Vec<f64> = tilts.as_array().iter().copied().collect();
    let cl: Vec<i32> = surf_classes.as_array().iter().copied().collect();
    let n = a.len();
    if az.len() != n || tl.len() != n || cl.len() != n {
        return Err(PyValueError::new_err("array lengths must match"));
    }
    let flat = py.detach(move || calc_approximate_view_factors(&a, &az, &tl, &cl));
    Ok(PyArray1::from_vec(py, flat).reshape([n, n])?.unbind())
}

/// Symmetrize and row-normalize zone view factor matrix `[N, N]`.
#[pyfunction]
pub fn idf_fix_view_factors<'py>(
    py: Python<'py>,
    areas: PyReadonlyArray1<'py, f64>,
    f_approx: PyReadonlyArray2<'py, f64>,
) -> PyResult<Py<PyArray2<f64>>> {
    let a: Vec<f64> = areas.as_array().iter().copied().collect();
    let n = a.len();
    let sh = f_approx.shape();
    if sh.len() != 2 || sh[0] != n || sh[1] != n {
        return Err(PyValueError::new_err("f_approx must be [N, N]"));
    }
    let f_vec: Vec<f64> = f_approx.as_array().iter().copied().collect();
    let flat = py.detach(move || fix_view_factors(&a, &f_vec));
    Ok(PyArray1::from_vec(py, flat).reshape([n, n])?.unbind())
}

/// Compute zone ScriptF radiosity matrix `[N, N]` using pure-Rust `faer`.
#[pyfunction]
pub fn idf_calc_script_f<'py>(
    py: Python<'py>,
    areas: PyReadonlyArray1<'py, f64>,
    f_mat: PyReadonlyArray2<'py, f64>,
    emiss: PyReadonlyArray1<'py, f64>,
) -> PyResult<Py<PyArray2<f64>>> {
    let a: Vec<f64> = areas.as_array().iter().copied().collect();
    let n = a.len();
    let e: Vec<f64> = emiss.as_array().iter().copied().collect();
    let sh = f_mat.shape();
    if e.len() != n || sh.len() != 2 || sh[0] != n || sh[1] != n {
        return Err(PyValueError::new_err("dimensions must match [N, N]"));
    }
    let f_vec: Vec<f64> = f_mat.as_array().iter().copied().collect();
    let flat = py
        .detach(move || calc_script_f(&a, &f_vec, &e))
        .map_err(|err| PyValueError::new_err(err.to_string()))?;
    Ok(PyArray1::from_vec(py, flat).reshape([n, n])?.unbind())
}

/// Batch parallel computation of `(f_final, script_f)` across zones using `rayon` + `faer`.
#[pyfunction]
pub fn idf_calc_zone_view_and_script_f_batch<'py>(
    py: Python<'py>,
    zone_areas: Vec<Vec<f64>>,
    zone_azimuths: Vec<Vec<f64>>,
    zone_tilts: Vec<Vec<f64>>,
    zone_classes: Vec<Vec<i32>>,
    zone_emiss: Vec<Vec<f64>>,
) -> PyResult<Vec<(Py<PyArray2<f64>>, Py<PyArray2<f64>>)>> {
    let n_zones = zone_areas.len();
    if zone_azimuths.len() != n_zones
        || zone_tilts.len() != n_zones
        || zone_classes.len() != n_zones
        || zone_emiss.len() != n_zones
    {
        return Err(PyValueError::new_err("zone batch vector lengths must match"));
    }
    let sizes: Vec<usize> = zone_areas.iter().map(Vec::len).collect();
    let results = py
        .detach(move || {
            calc_zone_view_and_script_f_batch(
                &zone_areas,
                &zone_azimuths,
                &zone_tilts,
                &zone_classes,
                &zone_emiss,
            )
        })
        .map_err(|err| PyValueError::new_err(err.to_string()))?;

    let mut out = Vec::with_capacity(n_zones);
    for (n, (f_mat, sf_mat)) in sizes.into_iter().zip(results.into_iter()) {
        out.push((
            PyArray1::from_vec(py, f_mat).reshape([n, n])?.unbind(),
            PyArray1::from_vec(py, sf_mat).reshape([n, n])?.unbind(),
        ));
    }
    Ok(out)
}

/// Return failing surface indices whose construction link is missing from `known_constructions`.
#[pyfunction]
pub fn idf_check_surface_construction_links(
    py: Python<'_>,
    surface_constructions: Vec<String>,
    known_constructions: Vec<String>,
) -> Vec<usize> {
    py.detach(move || check_surface_construction_links(&surface_constructions, &known_constructions))
}
