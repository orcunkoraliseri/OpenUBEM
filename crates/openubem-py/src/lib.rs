//! Thin PyO3 adapter exposing OpenUBEM Rust crates as `openubem._rust`.
//!
//! Core domain logic lives in pure-Rust workspace crates with zero `pyo3`
//! dependencies (Guardrail 2). This crate contains FFI translation, GIL release
//! (`py.detach`), and typed error mapping only.

mod extrude_ffi;
mod idf_ffi;
mod microclimate_ffi;
mod results_ffi;
mod schema_ffi;
mod shading_ffi;
mod sim_ffi;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use thiserror::Error;

/// Typed errors returned across the OpenUBEM Rust FFI boundary.
#[derive(Debug, Error)]
pub enum OpenUbemRustError {
    /// Raised when a caller supplies non-finite values where finite data is required.
    #[error("non-finite value encountered at index {index}")]
    NonFiniteInput { index: usize },
}

impl From<OpenUbemRustError> for PyErr {
    fn from(err: OpenUbemRustError) -> Self {
        PyValueError::new_err(err.to_string())
    }
}

/// Detect runtime CPU SIMD capabilities on the active host.
fn detect_simd_features() -> Vec<&'static str> {
    let mut features = Vec::new();
    #[cfg(target_arch = "aarch64")]
    {
        if std::arch::is_aarch64_feature_detected!("neon") {
            features.push("neon");
        }
        if std::arch::is_aarch64_feature_detected!("fp16") {
            features.push("fp16");
        }
        if std::arch::is_aarch64_feature_detected!("dotprod") {
            features.push("dotprod");
        }
    }
    #[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
    {
        if std::arch::is_x86_feature_detected!("sse4.2") {
            features.push("sse4.2");
        }
        if std::arch::is_x86_feature_detected!("avx2") {
            features.push("avx2");
        }
        if std::arch::is_x86_feature_detected!("fma") {
            features.push("fma");
        }
        if std::arch::is_x86_feature_detected!("avx512f") {
            features.push("avx512f");
        }
    }
    features
}

/// Pure-Rust deterministic scale-and-validate kernel used by Phase 0 smoke tests.
fn smoke_scale_kernel(values: &[f64], factor: f64) -> Result<Vec<f64>, OpenUbemRustError> {
    if !factor.is_finite() {
        return Err(OpenUbemRustError::NonFiniteInput { index: 0 });
    }
    for (index, &val) in values.iter().enumerate() {
        if !val.is_finite() {
            return Err(OpenUbemRustError::NonFiniteInput { index });
        }
    }
    Ok(values.iter().map(|&val| val * factor).collect())
}

/// Return diagnostic build metadata, target triple components, and SIMD flags.
#[pyfunction]
fn rust_smoke_info(py: Python<'_>) -> PyResult<Py<PyDict>> {
    let info = PyDict::new(py);
    info.set_item("crate_name", env!("CARGO_PKG_NAME"))?;
    info.set_item("crate_version", env!("CARGO_PKG_VERSION"))?;
    info.set_item("pyo3_abi", "abi3-py310")?;
    info.set_item("target_arch", std::env::consts::ARCH)?;
    info.set_item("target_os", std::env::consts::OS)?;
    info.set_item("target_family", std::env::consts::FAMILY)?;
    info.set_item("pointer_width", usize::BITS)?;
    info.set_item(
        "profile",
        if cfg!(debug_assertions) {
            "debug"
        } else {
            "release"
        },
    )?;
    info.set_item("simd_features", detect_simd_features())?;
    info.set_item("rayon_threads", rayon::current_num_threads())?;
    Ok(info.unbind())
}

/// Phase 0 FFI smoke function exercising `py.detach` and typed error mapping.
#[pyfunction]
fn rust_smoke_scale(py: Python<'_>, values: Vec<f64>, factor: f64) -> PyResult<Vec<f64>> {
    let out = py.detach(move || smoke_scale_kernel(&values, factor))?;
    Ok(out)
}

/// Python extension entrypoint for `_openubem_rust` (re-exported via `openubem._rust`).
#[pymodule]
fn _openubem_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_smoke_info, m)?)?;
    m.add_function(wrap_pyfunction!(rust_smoke_scale, m)?)?;

    // Phase 1 — openubem-schema
    m.add_function(wrap_pyfunction!(schema_ffi::schema_normalize_confidence, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_impute_token, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_parse_token, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_append_flag_token, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_merge_flags, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_parse_strict_flags, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_score_provenance_table, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_validate_step1_table, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_validate_sim_manifest_table, m)?)?;
    m.add_function(wrap_pyfunction!(schema_ffi::schema_build_step1_quality_flags, m)?)?;

    // Phase 1 — openubem-results
    m.add_function(wrap_pyfunction!(results_ffi::results_resolve_zone, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_err_iter_severe, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_err_first_severe, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_err_count_severe, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_err_has_fatal, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_parse_eio_zone_area, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_parse_eio_zone_multipliers, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_check_building_integrity, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_parse_building_sql, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_harvest_one_building, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_harvest_batch_to_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_harvest_batch_to_parquet, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_extract_four_end_use_csv, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_extract_heating_only_csv, m)?)?;
    m.add_function(wrap_pyfunction!(results_ffi::results_harvest_heating_csv_batch, m)?)?;

    // Phase 2 — openubem-shading
    m.add_function(wrap_pyfunction!(shading_ffi::shading_compute_exterior, m)?)?;

    // Phase 3 — openubem-idf
    m.add_function(wrap_pyfunction!(idf_ffi::idf_parse_objects, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_load_schedule_file_hourly, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_compile_schedule_compact_hourly, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_build_modal_conduction, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_calc_approximate_view_factors, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_fix_view_factors, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_calc_script_f, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_calc_zone_view_and_script_f_batch, m)?)?;
    m.add_function(wrap_pyfunction!(idf_ffi::idf_check_surface_construction_links, m)?)?;

    // Phase 4 — openubem-sim
    m.add_function(wrap_pyfunction!(sim_ffi::sim_kernel_conformance_hash, m)?)?;
    m.add_function(wrap_pyfunction!(sim_ffi::sim_run_stage_a_batch, m)?)?;

    // Phase 4 — openubem-microclimate
    m.add_function(wrap_pyfunction!(microclimate_ffi::micro_compute_svf, m)?)?;
    m.add_function(wrap_pyfunction!(microclimate_ffi::micro_building_shadow_from_horizon, m)?)?;
    m.add_function(wrap_pyfunction!(microclimate_ffi::micro_vegetation_transmission, m)?)?;
    m.add_function(wrap_pyfunction!(microclimate_ffi::micro_utci_approx, m)?)?;
    m.add_function(wrap_pyfunction!(microclimate_ffi::micro_classify_stress, m)?)?;

    // Phase 5 — openubem-extrude
    m.add_function(wrap_pyfunction!(extrude_ffi::extrude_and_match, m)?)?;
    m.add_function(wrap_pyfunction!(extrude_ffi::extrude_snap_rings, m)?)?;
    m.add_function(wrap_pyfunction!(extrude_ffi::extrude_newell_normal_and_area, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn smoke_scale_kernel_exact() {
        let out = smoke_scale_kernel(&[1.5, -2.0, 4.25], 2.0).expect("finite input");
        assert_eq!(out, vec![3.0, -4.0, 8.5]);
    }

    #[test]
    fn smoke_scale_kernel_rejects_nan() {
        let err = smoke_scale_kernel(&[1.0, f64::NAN], 2.0).expect_err("must reject NaN");
        assert!(matches!(err, OpenUbemRustError::NonFiniteInput { index: 1 }));
    }

    #[test]
    fn simd_detection_runs_cleanly() {
        let features = detect_simd_features();
        #[cfg(target_arch = "aarch64")]
        assert!(features.contains(&"neon"));
        let _ = features;
    }
}
