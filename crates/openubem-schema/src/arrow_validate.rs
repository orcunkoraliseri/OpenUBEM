//! Zero-copy Apache Arrow schema validators and provenance batch scorers.

use std::collections::HashSet;

use arrow_array::cast::AsArray;
use arrow_array::types::{Int8Type, Int16Type, Int32Type, Int64Type};
use arrow_array::{Array, Float64Array, RecordBatch};
use arrow_schema::DataType;

use crate::adt::SimulationStatus;
use crate::error::SchemaError;
use crate::flags::{FlagDelimiterMode, QualityFlag, QualityFlagSet};
use crate::provenance::score_provenance_matrix;

/// Exact 23-column order of `openubem/acquisition/footprint_schema.py::SCHEMA_COLUMNS`.
pub const STEP1_SCHEMA_COLUMNS: [&str; 23] = [
    "geometry",
    "osm_id",
    "crs_utm",
    "building_tag",
    "function_tag",
    "levels",
    "height_m",
    "year_built",
    "postcode",
    "underground",
    "roof_shape",
    "roof_height_m",
    "footprint_area_m2",
    "perimeter_m",
    "surplus_tags",
    "provenance_levels",
    "provenance_height_m",
    "provenance_year_built",
    "provenance_building_tag",
    "provenance_function_tag",
    "provenance_postcode",
    "provenance_geometry",
    "data_quality_flag",
];

/// Exact 11-column order of `04_simulation_manifest.parquet` (`simulation/parallel.py:215-218`).
pub const STEP4_MANIFEST_COLUMNS: [&str; 11] = [
    "osm_id",
    "idf_path",
    "work_dir",
    "sql_path",
    "status",
    "n_warnings",
    "n_severe",
    "wall_clock_s",
    "ep_version",
    "epw_path",
    "error_summary",
];

/// Borrow Arrow string values uniformly across `Utf8`, `LargeUtf8`, `Utf8View`, and `Dictionary`.
pub fn extract_string_refs<'a>(col: &'a dyn Array, col_name: &str) -> Result<Vec<Option<&'a str>>, SchemaError> {
    let n = col.len();
    let mut out = Vec::with_capacity(n);
    match col.data_type() {
        DataType::Utf8 => {
            let arr = col.as_string::<i32>();
            for i in 0..n {
                out.push(if arr.is_null(i) { None } else { Some(arr.value(i)) });
            }
            Ok(out)
        }
        DataType::LargeUtf8 => {
            let arr = col.as_string::<i64>();
            for i in 0..n {
                out.push(if arr.is_null(i) { None } else { Some(arr.value(i)) });
            }
            Ok(out)
        }
        DataType::Utf8View => {
            let arr = col.as_string_view();
            for i in 0..n {
                out.push(if arr.is_null(i) { None } else { Some(arr.value(i)) });
            }
            Ok(out)
        }
        DataType::Dictionary(key_dt, val_dt) => {
            if !matches!(
                val_dt.as_ref(),
                DataType::Utf8 | DataType::LargeUtf8 | DataType::Utf8View
            ) {
                return Err(SchemaError::ColumnTypeMismatch {
                    column: col_name.to_owned(),
                    detail: format!("Dictionary values must be string, got {:?}", val_dt),
                });
            }
            match key_dt.as_ref() {
                DataType::Int8 => collect_dict_str::<Int8Type>(col, col_name),
                DataType::Int16 => collect_dict_str::<Int16Type>(col, col_name),
                DataType::Int32 => collect_dict_str::<Int32Type>(col, col_name),
                DataType::Int64 => collect_dict_str::<Int64Type>(col, col_name),
                _ => Err(SchemaError::ColumnTypeMismatch {
                    column: col_name.to_owned(),
                    detail: format!("Unsupported Dictionary key dtype {:?}", key_dt),
                }),
            }
        }
        DataType::Null => {
            out.resize(n, None);
            Ok(out)
        }
        other => Err(SchemaError::ColumnTypeMismatch {
            column: col_name.to_owned(),
            detail: format!("expected Utf8/LargeUtf8/Utf8View/Dictionary, got {:?}", other),
        }),
    }
}

fn collect_dict_str<'a, K: arrow_array::types::ArrowDictionaryKeyType>(
    col: &'a dyn Array,
    col_name: &str,
) -> Result<Vec<Option<&'a str>>, SchemaError>
where
    K::Native: NumTraitsOrUsize,
{
    let dict = col.as_dictionary::<K>();
    let values = extract_string_refs(dict.values().as_ref(), col_name)?;
    let keys = dict.keys();
    let mut out = Vec::with_capacity(col.len());
    for i in 0..col.len() {
        if dict.is_null(i) {
            out.push(None);
        } else {
            let k = keys.value(i).to_idx();
            out.push(values[k]);
        }
    }
    Ok(out)
}

#[doc(hidden)]
pub trait NumTraitsOrUsize {
    fn to_idx(self) -> usize;
}
impl NumTraitsOrUsize for i8 {
    fn to_idx(self) -> usize {
        self as usize
    }
}
impl NumTraitsOrUsize for i16 {
    fn to_idx(self) -> usize {
        self as usize
    }
}
impl NumTraitsOrUsize for i32 {
    fn to_idx(self) -> usize {
        self as usize
    }
}
impl NumTraitsOrUsize for i64 {
    fn to_idx(self) -> usize {
        self as usize
    }
}

fn check_int64_col(batch: &RecordBatch, name: &str) -> Result<(), SchemaError> {
    let col = batch
        .column_by_name(name)
        .ok_or_else(|| SchemaError::ColumnOrderMismatch {
            detail: format!("missing required column {name:?}"),
        })?;
    if *col.data_type() != DataType::Int64 {
        return Err(SchemaError::ColumnTypeMismatch {
            column: name.to_owned(),
            detail: format!("expected Int64, got {:?}", col.data_type()),
        });
    }
    Ok(())
}

fn get_float64_col<'a>(batch: &'a RecordBatch, name: &str) -> Result<&'a Float64Array, SchemaError> {
    let col = batch
        .column_by_name(name)
        .ok_or_else(|| SchemaError::ColumnOrderMismatch {
            detail: format!("missing required column {name:?}"),
        })?;
    if *col.data_type() != DataType::Float64 {
        return Err(SchemaError::ColumnTypeMismatch {
            column: name.to_owned(),
            detail: format!("expected Float64, got {:?}", col.data_type()),
        });
    }
    Ok(col.as_any().downcast_ref::<Float64Array>().expect("Float64Array"))
}

/// Validate a Step-1 Arrow `RecordBatch` against OpenUBEM's 23-column footprint schema.
pub fn validate_step1_batch(batch: &RecordBatch) -> Result<(), SchemaError> {
    let schema = batch.schema();
    let cols: Vec<&str> = schema.fields().iter().map(|f| f.name().as_str()).collect();
    if cols.len() != STEP1_SCHEMA_COLUMNS.len() {
        return Err(SchemaError::ColumnCountMismatch {
            expected: STEP1_SCHEMA_COLUMNS.len(),
            actual: cols.len(),
        });
    }
    if cols != STEP1_SCHEMA_COLUMNS {
        return Err(SchemaError::ColumnOrderMismatch {
            detail: format!("got {cols:?}, expected {STEP1_SCHEMA_COLUMNS:?}"),
        });
    }
    for int_col in ["levels", "year_built", "underground"] {
        check_int64_col(batch, int_col)?;
    }
    for float_col in ["height_m", "roof_height_m", "footprint_area_m2", "perimeter_m"] {
        let _ = get_float64_col(batch, float_col)?;
    }
    let area = get_float64_col(batch, "footprint_area_m2")?;
    let perim = get_float64_col(batch, "perimeter_m")?;
    for i in 0..batch.num_rows() {
        if area.is_null(i) {
            return Err(SchemaError::DomainConstraintViolation {
                row_index: i,
                column: "footprint_area_m2".to_owned(),
                detail: "cannot be null".to_owned(),
            });
        }
        let a = area.value(i);
        if !a.is_finite() || a < 20.0 {
            return Err(SchemaError::DomainConstraintViolation {
                row_index: i,
                column: "footprint_area_m2".to_owned(),
                detail: format!("expected >= 20.0, got {a}"),
            });
        }
        if perim.is_null(i) || !perim.value(i).is_finite() || perim.value(i) <= 0.0 {
            return Err(SchemaError::DomainConstraintViolation {
                row_index: i,
                column: "perimeter_m".to_owned(),
                detail: "must be finite and > 0".to_owned(),
            });
        }
    }

    let osm_col = batch.column_by_name("osm_id").expect("osm_id");
    let osm_vals = extract_string_refs(osm_col.as_ref(), "osm_id")?;
    let mut seen = HashSet::with_capacity(osm_vals.len());
    for (i, val) in osm_vals.into_iter().enumerate() {
        let Some(s) = val else {
            return Err(SchemaError::KeyViolation {
                column: "osm_id".to_owned(),
                detail: format!("null osm_id at row {i}"),
            });
        };
        if s.is_empty() {
            return Err(SchemaError::KeyViolation {
                column: "osm_id".to_owned(),
                detail: format!("empty osm_id at row {i}"),
            });
        }
        if !seen.insert(s) {
            return Err(SchemaError::KeyViolation {
                column: "osm_id".to_owned(),
                detail: format!("duplicate osm_id {s:?} at row {i}"),
            });
        }
    }

    // Geometry column must carry Binary/LargeBinary/Utf8/GeoArrow WKB bytes (non-null).
    let geom_col = batch.column_by_name("geometry").expect("geometry");
    for i in 0..geom_col.len() {
        if geom_col.is_null(i) {
            return Err(SchemaError::DomainConstraintViolation {
                row_index: i,
                column: "geometry".to_owned(),
                detail: "geometry cannot be null".to_owned(),
            });
        }
    }
    Ok(())
}

/// Validate a Step-4 simulation manifest Arrow `RecordBatch` (`simulation/parallel.py`).
pub fn validate_sim_manifest_batch(batch: &RecordBatch) -> Result<(), SchemaError> {
    let schema = batch.schema();
    let cols: Vec<&str> = schema.fields().iter().map(|f| f.name().as_str()).collect();
    if cols != STEP4_MANIFEST_COLUMNS {
        return Err(SchemaError::ColumnOrderMismatch {
            detail: format!("got {cols:?}, expected {STEP4_MANIFEST_COLUMNS:?}"),
        });
    }
    check_int64_col(batch, "n_warnings")?;
    check_int64_col(batch, "n_severe")?;
    let wall = get_float64_col(batch, "wall_clock_s")?;
    for i in 0..batch.num_rows() {
        if wall.is_null(i) || !wall.value(i).is_finite() || wall.value(i) < 0.0 {
            return Err(SchemaError::DomainConstraintViolation {
                row_index: i,
                column: "wall_clock_s".to_owned(),
                detail: "must be finite and >= 0".to_owned(),
            });
        }
    }
    for required_non_null_str in ["osm_id", "sql_path", "error_summary", "status"] {
        let col = batch
            .column_by_name(required_non_null_str)
            .expect("column checked");
        let refs = extract_string_refs(col.as_ref(), required_non_null_str)?;
        for (i, val) in refs.into_iter().enumerate() {
            let Some(s) = val else {
                return Err(SchemaError::KeyViolation {
                    column: required_non_null_str.to_owned(),
                    detail: format!("null value at row {i} (use empty string instead)"),
                });
            };
            if required_non_null_str == "status" {
                SimulationStatus::from_token(s)?;
            }
        }
    }
    Ok(())
}

/// Vectorized provenance summary over an Arrow `RecordBatch` (`provenance.py::add_lineage_summary`).
pub fn score_provenance_batch(
    batch: &RecordBatch,
    prov_cols: Option<&[String]>,
) -> Result<(Vec<i64>, Vec<f64>), SchemaError> {
    let n_rows = batch.num_rows();
    let schema = batch.schema();
    let selected_names: Vec<String> = match prov_cols {
        Some(cols) => cols.to_vec(),
        None => schema
            .fields()
            .iter()
            .map(|f| f.name().clone())
            .filter(|name| name.starts_with("provenance_") || name.ends_with("_prov"))
            .collect(),
    };
    if selected_names.is_empty() {
        return Ok((vec![0; n_rows], vec![1.0; n_rows]));
    }
    let mut extracted = Vec::with_capacity(selected_names.len());
    for name in &selected_names {
        let col = batch
            .column_by_name(name)
            .ok_or_else(|| SchemaError::ColumnOrderMismatch {
                detail: format!("missing provenance column {name:?}"),
            })?;
        extracted.push(extract_string_refs(col.as_ref(), name)?);
    }
    Ok(score_provenance_matrix(&extracted, n_rows))
}

/// Vectorized Step-1 quality flag builder (`footprint_schema.py::build_quality_flag`).
pub fn build_step1_quality_flags(
    batch: &RecordBatch,
    source: Option<&str>,
    comma_legacy: bool,
) -> Result<Vec<String>, SchemaError> {
    let n = batch.num_rows();
    let levels = batch
        .column_by_name("levels")
        .ok_or_else(|| SchemaError::ColumnOrderMismatch {
            detail: "missing levels".to_owned(),
        })?;
    let height = batch
        .column_by_name("height_m")
        .ok_or_else(|| SchemaError::ColumnOrderMismatch {
            detail: "missing height_m".to_owned(),
        })?;
    let year_built = batch
        .column_by_name("year_built")
        .ok_or_else(|| SchemaError::ColumnOrderMismatch {
            detail: "missing year_built".to_owned(),
        })?;
    let btag = extract_string_refs(
        batch
            .column_by_name("building_tag")
            .ok_or_else(|| SchemaError::ColumnOrderMismatch {
                detail: "missing building_tag".to_owned(),
            })?
            .as_ref(),
        "building_tag",
    )?;
    let ftag = extract_string_refs(
        batch
            .column_by_name("function_tag")
            .ok_or_else(|| SchemaError::ColumnOrderMismatch {
                detail: "missing function_tag".to_owned(),
            })?
            .as_ref(),
        "function_tag",
    )?;
    let pgeom = extract_string_refs(
        batch
            .column_by_name("provenance_geometry")
            .ok_or_else(|| SchemaError::ColumnOrderMismatch {
                detail: "missing provenance_geometry".to_owned(),
            })?
            .as_ref(),
        "provenance_geometry",
    )?;
    let pheight = extract_string_refs(
        batch
            .column_by_name("provenance_height_m")
            .ok_or_else(|| SchemaError::ColumnOrderMismatch {
                detail: "missing provenance_height_m".to_owned(),
            })?
            .as_ref(),
        "provenance_height_m",
    )?;
    let height_f64 = height.as_any().downcast_ref::<Float64Array>();
    let mode = if comma_legacy {
        FlagDelimiterMode::CommaLegacy
    } else {
        FlagDelimiterMode::PipeCanonical
    };
    let is_osm = source == Some("OSM");
    let mut out = Vec::with_capacity(n);

    for i in 0..n {
        let mut set = QualityFlagSet::default();
        if levels.is_null(i) {
            set.insert(QualityFlag::NoFloors);
        }
        let h_missing = height.is_null(i)
            || height_f64.map(|arr| !arr.value(i).is_finite()).unwrap_or(false);
        if h_missing {
            set.insert(QualityFlag::NoHeight);
        }
        let bt = btag[i];
        let is_generic_bt = matches!(bt, None | Some("") | Some("yes"));
        if is_osm {
            if is_generic_bt {
                set.insert(QualityFlag::GenericTag);
            }
            if matches!(ftag[i], Some("")) && is_generic_bt {
                set.insert(QualityFlag::NoFunction);
            }
            if matches!(pgeom[i], Some("OSM_OVERLAP_RESOLVED")) {
                set.insert(QualityFlag::OverlapResolved);
            }
            if matches!(pheight[i], Some("OSM_OBSERVED_FT")) {
                set.insert(QualityFlag::HeightOnlyFt);
            }
        } else if matches!(bt, None | Some("")) {
            set.insert(QualityFlag::NoBuildingTag);
        }
        if year_built.is_null(i) {
            set.insert(QualityFlag::NoYear);
        }
        out.push(set.format(mode));
    }
    Ok(out)
}
