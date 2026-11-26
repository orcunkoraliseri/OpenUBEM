//! Fast `&[u8]` schedule CSV column extraction & `Schedule:Compact` hourly compiler.

use std::path::Path;

use rayon::prelude::*;

use crate::error::IdfError;

const MONTH_DAYS: [usize; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const MONTH_START_DOY: [usize; 12] = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

#[inline]
fn trim_ascii(mut b: &[u8]) -> &[u8] {
    while let Some(&first) = b.first() {
        if first.is_ascii_whitespace() {
            b = &b[1..];
        } else {
            break;
        }
    }
    while let Some(&last) = b.last() {
        if last.is_ascii_whitespace() {
            b = &b[..b.len() - 1];
        } else {
            break;
        }
    }
    b
}

/// Zero-copy fast Schedule:File numeric extractor matching `schedules.py::load_schedule_file_hourly`.
pub fn load_schedule_file_hourly_bytes(
    bytes: &[u8],
    column_number: usize,
    rows_to_skip: usize,
    num_hours: usize,
    delimiter: u8,
) -> Result<Vec<f64>, IdfError> {
    if column_number == 0 {
        return Err(IdfError::ScheduleError(
            "column_number must be >= 1".to_string(),
        ));
    }
    let col_idx = column_number - 1;
    let mut values = Vec::with_capacity(num_hours);

    let mut line_start = 0usize;
    let mut line_num = 0usize;
    let len = bytes.len();

    while line_start < len {
        let line_end = memchr::memchr(b'\n', &bytes[line_start..])
            .map(|rel| line_start + rel)
            .unwrap_or(len);
        let mut line = &bytes[line_start..line_end];
        if line.ends_with(b"\r") {
            line = &line[..line.len() - 1];
        }
        line_start = line_end + 1;

        if line_num < rows_to_skip {
            line_num += 1;
            continue;
        }
        line_num += 1;

        let trimmed = trim_ascii(line);
        if trimmed.is_empty() {
            continue;
        }

        // Locate col_idx directly using delimiter scans without Vec allocation.
        let mut cur_col = 0usize;
        let mut pos = 0usize;
        let mut field_slice: Option<&[u8]> = None;
        while cur_col <= col_idx {
            let next_delim = memchr::memchr(delimiter, &trimmed[pos..])
                .map(|rel| pos + rel)
                .unwrap_or(trimmed.len());
            if cur_col == col_idx {
                field_slice = Some(trim_ascii(&trimmed[pos..next_delim]));
                break;
            }
            if next_delim == trimmed.len() {
                break;
            }
            pos = next_delim + 1;
            cur_col += 1;
        }

        let token = field_slice.ok_or_else(|| {
            IdfError::ScheduleError(format!(
                "missing column {column_number} on non-empty row {line_num}"
            ))
        })?;
        let val = fast_float2::parse::<f64, _>(token).map_err(|_| {
            IdfError::ScheduleError(format!(
                "invalid float '{}' on row {line_num}",
                String::from_utf8_lossy(token)
            ))
        })?;
        values.push(val);
        if values.len() == num_hours {
            break;
        }
    }

    if values.len() != num_hours {
        return Err(IdfError::ScheduleError(format!(
            "expected {num_hours} hourly schedule entries, got {}",
            values.len()
        )));
    }
    Ok(values)
}

/// Read and parse a schedule CSV file from disk.
pub fn load_schedule_file_hourly(
    path: &Path,
    column_number: usize,
    rows_to_skip: usize,
    num_hours: usize,
    delimiter: u8,
) -> Result<Vec<f64>, IdfError> {
    let data = std::fs::read(path)?;
    load_schedule_file_hourly_bytes(&data, column_number, rows_to_skip, num_hours, delimiter)
}

/// Parallel batch loader for Schedule:File requests via `rayon`.
pub fn load_schedule_files_batch(
    requests: &[(String, usize, usize, usize, u8)],
) -> Result<Vec<Vec<f64>>, IdfError> {
    requests
        .par_iter()
        .map(|(path, col, skip, hours, delim)| {
            load_schedule_file_hourly(Path::new(path), *col, *skip, *hours, *delim)
        })
        .collect()
}

fn parse_md_to_doy(md: &str) -> Result<usize, IdfError> {
    let (m_s, d_s) = md
        .trim()
        .split_once('/')
        .ok_or_else(|| IdfError::ScheduleError(format!("invalid MM/DD '{md}'")))?;
    let m: usize = m_s
        .trim()
        .parse()
        .map_err(|_| IdfError::ScheduleError(format!("invalid month '{m_s}'")))?;
    let d: usize = d_s
        .trim()
        .parse()
        .map_err(|_| IdfError::ScheduleError(format!("invalid day '{d_s}'")))?;
    let m_clamped = m.clamp(1, 12);
    let d_clamped = d.clamp(1, MONTH_DAYS[m_clamped - 1]);
    Ok(MONTH_START_DOY[m_clamped - 1] + (d_clamped - 1))
}

fn match_day_types(for_clause: &str, dow: usize) -> bool {
    let dow_names = [
        ("sunday", 0usize),
        ("monday", 1),
        ("tuesday", 2),
        ("wednesday", 3),
        ("thursday", 4),
        ("friday", 5),
        ("saturday", 6),
    ];
    for raw in for_clause.split_whitespace() {
        let tok = raw.trim().to_ascii_lowercase();
        if tok == "alldays" || tok == "allotherdays" {
            return true;
        }
        if tok == "weekdays" && (1..=5).contains(&dow) {
            return true;
        }
        if tok == "weekends" && (dow == 0 || dow == 6) {
            return true;
        }
        for &(name, idx) in &dow_names {
            if tok == name && dow == idx {
                return true;
            }
        }
    }
    false
}

/// Compile `Schedule:Compact` fields (starting at Name = fields[0]) into 8,760 hourly values.
pub fn compile_schedule_compact_hourly(
    fields: &[String],
    start_day_of_week: usize,
) -> Result<Vec<f64>, IdfError> {
    let mut out = vec![0.0_f64; 365 * 24];
    let mut filled = vec![false; 365];

    let mut idx = 2usize;
    let n = fields.len();
    let mut doy_start = 0usize;
    while idx < n {
        let tok = fields[idx].trim();
        let low = tok.to_ascii_lowercase();
        if let Some(after) = low.strip_prefix("through:") {
            let _ = after;
            let raw_md = tok.split_once(':').map(|(_, r)| r).unwrap_or("");
            let doy_end = parse_md_to_doy(raw_md)?;
            idx += 1;
            while idx < n && !fields[idx].trim().to_ascii_lowercase().starts_with("through:") {
                let sub = fields[idx].trim();
                let sub_low = sub.to_ascii_lowercase();
                if sub_low.starts_with("for:") {
                    let for_str = sub.split_once(':').map(|(_, r)| r).unwrap_or("");
                    let is_other = for_str.to_ascii_lowercase().contains("allotherdays");
                    idx += 1;
                    let mut day_vals = [0.0_f64; 24];
                    let mut hr_prev = 0usize;
                    while idx < n {
                        let nxt = fields[idx].trim();
                        let nlow = nxt.to_ascii_lowercase();
                        if nlow.starts_with("through:") || nlow.starts_with("for:") {
                            break;
                        }
                        if nlow.starts_with("interpolate:") {
                            idx += 1;
                            continue;
                        }
                        if nlow.starts_with("until:") {
                            let time_str = nxt.split_once(':').map(|(_, r)| r).unwrap_or("").trim();
                            let (hh_s, mm_s) = time_str.split_once(':').ok_or_else(|| {
                                IdfError::ScheduleError(format!("invalid Until time '{time_str}'"))
                            })?;
                            let hh: usize = hh_s.trim().parse().map_err(|_| {
                                IdfError::ScheduleError(format!("invalid hour '{hh_s}'"))
                            })?;
                            let mm: usize = mm_s.trim().parse().map_err(|_| {
                                IdfError::ScheduleError(format!("invalid minute '{mm_s}'"))
                            })?;
                            let hr_end = (hh + usize::from(mm > 0)).clamp(hr_prev, 24);
                            let val_tok = fields.get(idx + 1).ok_or_else(|| {
                                IdfError::ScheduleError("missing Schedule:Compact Until value".into())
                            })?;
                            let val: f64 = fast_float2::parse(val_tok.trim()).map_err(|_| {
                                IdfError::ScheduleError(format!("invalid schedule number '{val_tok}'"))
                            })?;
                            for slot in &mut day_vals[hr_prev..hr_end] {
                                *slot = val;
                            }
                            hr_prev = hr_end;
                            idx += 2;
                        } else {
                            idx += 1;
                        }
                    }
                    for d in doy_start..=doy_end.min(364) {
                        let dow = (start_day_of_week + d) % 7;
                        if is_other {
                            if !filled[d] {
                                out[(d * 24)..((d + 1) * 24)].copy_from_slice(&day_vals);
                                filled[d] = true;
                            }
                        } else if match_day_types(for_str, dow) {
                            out[(d * 24)..((d + 1) * 24)].copy_from_slice(&day_vals);
                            filled[d] = true;
                        }
                    }
                } else {
                    idx += 1;
                }
            }
            doy_start = doy_end + 1;
        } else {
            idx += 1;
        }
    }
    Ok(out)
}
