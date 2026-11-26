//! Single-pass `csv::ByteRecord` extractors for European campaign `eplusout.csv` files (`DR06`).

use std::fs::File;
use std::io::BufReader;
use std::path::Path;

use csv::{ByteRecord, ReaderBuilder};
use openubem_schema::J_TO_KWH;
use rayon::prelude::*;

use crate::error::ResultsError;

/// Canonical non-leap calendar hour counts per month (`european_campaign.py`).
pub const NON_LEAP_MONTH_HOURS: [u32; 12] =
    [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744];

/// Annual total hours in a non-leap calendar year (`8,760`).
pub const NON_LEAP_YEAR_HOURS: usize = 8760;

const VAR_HEATING: &str = "zone ideal loads zone total heating energy";
const VAR_COOLING: &str = "zone ideal loads zone total cooling energy";
const VAR_LIGHTING: &str = "zone lights electricity energy";
const VAR_EQUIPMENT: &str = "zone electric equipment electricity energy";

/// Output of single-pass four-end-use extraction (`extract_four_end_use_eplus_csv`).
#[derive(Debug, Clone)]
pub struct FourEndUseCsvResult {
    pub source_csv: String,
    pub heating_kwh: f64,
    pub cooling_kwh: f64,
    pub lighting_kwh: f64,
    pub equipment_kwh: f64,
    pub monthly_kwh: [f64; 12],
    pub hourly_kwh: Vec<f64>,
}

/// Find hourly `[J]` columns matching `required_lower`.
fn match_eplus_columns(headers: &[String], required_lower: &str, var_label: &str) -> Result<Vec<usize>, ResultsError> {
    let mut cols = Vec::new();
    for (idx, h) in headers.iter().enumerate() {
        let lower = h.to_ascii_lowercase();
        if lower.contains(required_lower) && lower.contains("[j]") && lower.contains("(hourly)") {
            cols.push(idx);
        }
    }
    if cols.is_empty() {
        return Err(ResultsError::InvalidCsv(format!(
            "retained EnergyPlus CSV lacks hourly J output: {var_label}"
        )));
    }
    Ok(cols)
}

#[inline]
fn parse_ep_month(raw: &[u8], row_number: usize) -> Result<usize, ResultsError> {
    let s = std::str::from_utf8(raw)
        .map_err(|_| ResultsError::InvalidCsv(format!("row {row_number} non-UTF8 Date/Time")))?
        .trim();
    if s.len() < 2 {
        return Err(ResultsError::InvalidCsv(format!(
            "row {row_number} has invalid EnergyPlus Date/Time: {s:?}"
        )));
    }
    let m: usize = s[..2].parse().map_err(|_| {
        ResultsError::InvalidCsv(format!(
            "row {row_number} has invalid EnergyPlus Date/Time: {s:?}"
        ))
    })?;
    if !(1..=12).contains(&m) {
        return Err(ResultsError::InvalidCsv(format!(
            "row {row_number} has invalid EnergyPlus month: {s:?}"
        )));
    }
    Ok(m)
}

#[inline]
fn strip_utf8_bom(bytes: &[u8]) -> &[u8] {
    bytes.strip_prefix(b"\xEF\xBB\xBF").unwrap_or(bytes)
}

/// Extract the 4 simulated end-uses from `eplusout.csv` in a single pass with `ByteRecord` reuse.
pub fn extract_four_end_use_csv(path: &Path) -> Result<FourEndUseCsvResult, ResultsError> {
    if !path.is_file() {
        return Err(ResultsError::InvalidCsv(format!(
            "retained EnergyPlus CSV does not exist: {}",
            path.display()
        )));
    }
    let file = File::open(path).map_err(|e| ResultsError::Io {
        path: path.display().to_string(),
        reason: e.to_string(),
    })?;
    let mut reader = ReaderBuilder::new()
        .has_headers(false)
        .from_reader(BufReader::with_capacity(64 * 1024, file));

    let mut header_rec = ByteRecord::new();
    if !reader
        .read_byte_record(&mut header_rec)
        .map_err(|e| ResultsError::InvalidCsv(e.to_string()))?
    {
        return Err(ResultsError::InvalidCsv(
            "retained EnergyPlus CSV requires a Date/Time column".to_owned(),
        ));
    }

    let mut headers = Vec::with_capacity(header_rec.len());
    for (idx, field) in header_rec.iter().enumerate() {
        let bytes = if idx == 0 { strip_utf8_bom(field) } else { field };
        headers.push(String::from_utf8_lossy(bytes).into_owned());
    }
    let dt_idx = headers
        .iter()
        .position(|h| h == "Date/Time")
        .ok_or_else(|| {
            ResultsError::InvalidCsv("retained EnergyPlus CSV requires a Date/Time column".to_owned())
        })?;

    let cols = [
        match_eplus_columns(&headers, VAR_HEATING, "Zone Ideal Loads Zone Total Heating Energy")?,
        match_eplus_columns(&headers, VAR_COOLING, "Zone Ideal Loads Zone Total Cooling Energy")?,
        match_eplus_columns(&headers, VAR_LIGHTING, "Zone Lights Electricity Energy")?,
        match_eplus_columns(
            &headers,
            VAR_EQUIPMENT,
            "Zone Electric Equipment Electricity Energy",
        )?,
    ];
    const END_USE_NAMES: [&str; 4] = ["heating", "cooling", "lighting", "equipment"];

    let mut monthly_by_eu = [[0.0_f64; 12]; 4];
    let mut observed_month_hours = [0_u32; 12];
    let mut hourly_total = Vec::with_capacity(NON_LEAP_YEAR_HOURS);
    let mut rec = ByteRecord::new();
    let mut row_number = 1_usize;

    while reader
        .read_byte_record(&mut rec)
        .map_err(|e| ResultsError::InvalidCsv(e.to_string()))?
    {
        row_number += 1;
        let dt_raw = rec.get(dt_idx).unwrap_or(b"");
        let month = parse_ep_month(dt_raw, row_number)?;
        observed_month_hours[month - 1] += 1;

        let mut row_kwh_sum = 0.0_f64;
        for (eu_idx, col_indices) in cols.iter().enumerate() {
            let mut sum_j = 0.0_f64;
            for &cidx in col_indices {
                let raw_val = rec.get(cidx).ok_or_else(|| {
                    ResultsError::InvalidCsv(format!(
                        "row {row_number} has invalid {} energy value",
                        END_USE_NAMES[eu_idx]
                    ))
                })?;
                let txt = std::str::from_utf8(raw_val).unwrap_or("").trim();
                let v: f64 = fast_float2::parse(txt).map_err(|_| {
                    ResultsError::InvalidCsv(format!(
                        "row {row_number} has invalid {} energy value",
                        END_USE_NAMES[eu_idx]
                    ))
                })?;
                sum_j += v;
            }
            if !sum_j.is_finite() || sum_j < 0.0 {
                return Err(ResultsError::InvalidCsv(format!(
                    "row {row_number} has invalid {} energy value",
                    END_USE_NAMES[eu_idx]
                )));
            }
            let val_kwh = sum_j * J_TO_KWH;
            monthly_by_eu[eu_idx][month - 1] += val_kwh;
            row_kwh_sum += val_kwh;
        }
        hourly_total.push(row_kwh_sum);
    }

    if hourly_total.len() != NON_LEAP_YEAR_HOURS {
        return Err(ResultsError::InvalidCsv(
            "retained EnergyPlus CSV requires exactly 8760 hourly rows".to_owned(),
        ));
    }
    if observed_month_hours != NON_LEAP_MONTH_HOURS {
        return Err(ResultsError::InvalidCsv(
            "retained EnergyPlus CSV month row counts are not the required non-leap calendar"
                .to_owned(),
        ));
    }

    let mut monthly_total = [0.0_f64; 12];
    for m in 0..12 {
        monthly_total[m] = monthly_by_eu[0][m]
            + monthly_by_eu[1][m]
            + monthly_by_eu[2][m]
            + monthly_by_eu[3][m];
    }

    Ok(FourEndUseCsvResult {
        source_csv: path.display().to_string(),
        heating_kwh: monthly_by_eu[0].iter().sum(),
        cooling_kwh: monthly_by_eu[1].iter().sum(),
        lighting_kwh: monthly_by_eu[2].iter().sum(),
        equipment_kwh: monthly_by_eu[3].iter().sum(),
        monthly_kwh: monthly_total,
        hourly_kwh: hourly_total,
    })
}

/// Extract annual heating energy `[kWh]` from an EU-08/S2 heating-only `eplusout.csv`.
pub fn extract_heating_only_csv(path: &Path) -> Result<f64, ResultsError> {
    if !path.is_file() {
        return Err(ResultsError::Io {
            path: path.display().to_string(),
            reason: "file does not exist".to_owned(),
        });
    }
    let file = File::open(path).map_err(|e| ResultsError::Io {
        path: path.display().to_string(),
        reason: e.to_string(),
    })?;
    let mut reader = ReaderBuilder::new()
        .has_headers(false)
        .from_reader(BufReader::with_capacity(64 * 1024, file));
    let mut header_rec = ByteRecord::new();
    if !reader
        .read_byte_record(&mut header_rec)
        .map_err(|e| ResultsError::InvalidCsv(e.to_string()))?
    {
        return Err(ResultsError::InvalidCsv(format!(
            "Empty eplusout.csv header: {}",
            path.display()
        )));
    }
    let mut headers = Vec::with_capacity(header_rec.len());
    for (idx, field) in header_rec.iter().enumerate() {
        let bytes = if idx == 0 { strip_utf8_bom(field) } else { field };
        headers.push(String::from_utf8_lossy(bytes).into_owned());
    }
    let cols = match_eplus_columns(&headers, VAR_HEATING, "Zone Ideal Loads Zone Total Heating Energy")?;

    let mut total_j = 0.0_f64;
    let mut rec = ByteRecord::new();
    while reader
        .read_byte_record(&mut rec)
        .map_err(|e| ResultsError::InvalidCsv(e.to_string()))?
    {
        let mut row_j = 0.0_f64;
        for &cidx in &cols {
            let txt = std::str::from_utf8(rec.get(cidx).unwrap_or(b""))
                .unwrap_or("")
                .trim();
            let v: f64 = fast_float2::parse(txt)
                .map_err(|_| ResultsError::InvalidCsv("invalid float in heating column".to_owned()))?;
            row_j += v;
        }
        total_j += row_j;
    }
    Ok(total_j * J_TO_KWH)
}

/// Parallel batch extractor for EU-08/S2 heating-only `eplusout.csv` files via `rayon`.
pub fn harvest_heating_csv_batch(paths: &[&Path]) -> Result<Vec<f64>, ResultsError> {
    paths
        .par_iter()
        .map(|p| extract_heating_only_csv(p))
        .collect()
}

/// Parallel batch extractor for four-end-use `eplusout.csv` files via `rayon`.
pub fn harvest_four_end_use_csv_batch(paths: &[&Path]) -> Result<Vec<FourEndUseCsvResult>, ResultsError> {
    paths
        .par_iter()
        .map(|p| extract_four_end_use_csv(p))
        .collect()
}
