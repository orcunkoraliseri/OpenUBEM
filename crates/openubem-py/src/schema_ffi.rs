//! PyO3 adapters for `openubem-schema` (zero-copy `pyo3-arrow` + GIL release via `py.detach`).

use openubem_schema::{
    FlagDelimiterMode, QualityFlagSet, SchemaError, append_flag_token_delimited,
    build_step1_quality_flags, impute_token, merge_flag_strings, parse_token,
    score_provenance_batch, validate_sim_manifest_batch, validate_step1_batch,
    ConfidenceTier,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3_arrow::PyTable;

fn map_schema_err(err: SchemaError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
pub fn schema_normalize_confidence(confidence: &str) -> PyResult<&'static str> {
    ConfidenceTier::parse(confidence)
        .map(ConfidenceTier::canonical_str)
        .map_err(map_schema_err)
}

#[pyfunction]
pub fn schema_impute_token(method: &str, source: &str, confidence: &str) -> PyResult<String> {
    impute_token(method, source, confidence).map_err(map_schema_err)
}

#[pyfunction]
pub fn schema_parse_token(token: &str) -> Option<(String, String, &'static str)> {
    parse_token(token).map(|(m, s, tier)| (m, s, tier.canonical_str()))
}

#[pyfunction]
#[pyo3(signature = (existing, token, sep="|"))]
pub fn schema_append_flag_token(existing: Option<&str>, token: &str, sep: &str) -> PyResult<String> {
    let ch = sep
        .chars()
        .next()
        .ok_or_else(|| PyValueError::new_err("separator must be non-empty"))?;
    Ok(append_flag_token_delimited(existing, token, ch))
}

#[pyfunction]
#[pyo3(signature = (base, delta, sep=","))]
pub fn schema_merge_flags(base: Option<&str>, delta: Option<&str>, sep: &str) -> PyResult<String> {
    let ch = sep
        .chars()
        .next()
        .ok_or_else(|| PyValueError::new_err("separator must be non-empty"))?;
    Ok(merge_flag_strings(base, delta, ch))
}

#[pyfunction]
#[pyo3(signature = (raw, comma_legacy=false))]
pub fn schema_parse_strict_flags(raw: &str, comma_legacy: bool) -> PyResult<String> {
    let set = QualityFlagSet::parse_strict(raw).map_err(map_schema_err)?;
    let mode = if comma_legacy {
        FlagDelimiterMode::CommaLegacy
    } else {
        FlagDelimiterMode::PipeCanonical
    };
    Ok(set.format(mode))
}

/// Score provenance columns across an Arrow table (`provenance.py::add_lineage_summary`).
#[pyfunction]
#[pyo3(signature = (table, prov_cols=None))]
pub fn schema_score_provenance_table(
    py: Python<'_>,
    table: PyTable,
    prov_cols: Option<Vec<String>>,
) -> PyResult<(Vec<i64>, Vec<f64>)> {
    let (batches, schema) = table.into_inner();
    if batches.is_empty() {
        return Ok((Vec::new(), Vec::new()));
    }
    py.detach(move || {
        let mut all_counts = Vec::new();
        let mut all_means = Vec::new();
        let cols_ref = prov_cols.as_deref();
        let _ = &schema;
        for batch in &batches {
            let (mut c, mut m) = score_provenance_batch(batch, cols_ref).map_err(map_schema_err)?;
            all_counts.append(&mut c);
            all_means.append(&mut m);
        }
        Ok((all_counts, all_means))
    })
}

/// Validate a Step-1 Arrow table against OpenUBEM's 23-column footprint schema.
#[pyfunction]
pub fn schema_validate_step1_table(py: Python<'_>, table: PyTable) -> PyResult<()> {
    let (batches, _schema) = table.into_inner();
    py.detach(move || {
        for batch in &batches {
            validate_step1_batch(batch).map_err(map_schema_err)?;
        }
        Ok(())
    })
}

/// Validate a Step-4 simulation manifest Arrow table.
#[pyfunction]
pub fn schema_validate_sim_manifest_table(py: Python<'_>, table: PyTable) -> PyResult<()> {
    let (batches, _schema) = table.into_inner();
    py.detach(move || {
        for batch in &batches {
            validate_sim_manifest_batch(batch).map_err(map_schema_err)?;
        }
        Ok(())
    })
}

/// Vectorized Step-1 quality flag builder over an Arrow table (`footprint_schema.py`).
#[pyfunction]
#[pyo3(signature = (table, source=None, comma_legacy=true))]
pub fn schema_build_step1_quality_flags(
    py: Python<'_>,
    table: PyTable,
    source: Option<String>,
    comma_legacy: bool,
) -> PyResult<Vec<String>> {
    let (batches, _schema) = table.into_inner();
    py.detach(move || {
        let mut out = Vec::new();
        for batch in &batches {
            let mut flags = build_step1_quality_flags(batch, source.as_deref(), comma_legacy)
                .map_err(map_schema_err)?;
            out.append(&mut flags);
        }
        Ok(out)
    })
}
