//! Zero-copy `memchr` scanner for EnergyPlus `eplusout.eio` Zone Information (`OPEN-01`, `OPEN-60`).

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use memchr::memmem;

const EIO_HEADER_MARKER: &[u8] = b"! <Zone Information>";
const EIO_DATA_PREFIX: &[u8] = b" Zone Information,";

/// Parsed zone area & multiplier summary from one `eplusout.eio` file.
#[derive(Debug, Clone, Default)]
pub struct EioZoneInfo {
    pub n_zones: usize,
    pub area_plain_m2: f64,
    pub area_multiplier_aware_m2: f64,
    pub max_zone_multiplier: i64,
    pub max_zone_list_multiplier: i64,
    pub n_zones_excluded_not_in_total_area: usize,
    pub parse_status: String,
    pub zone_multipliers: HashMap<String, f64>,
}

/// Single-pass streaming parser for `eplusout.eio` matching both `parse_eio_zone_area` and `parse_eio_zone_multipliers`.
pub fn parse_eio_file(path: &Path) -> EioZoneInfo {
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            return EioZoneInfo {
                parse_status: format!("file_error:{e}"),
                ..Default::default()
            };
        }
    };

    let mut reader = BufReader::with_capacity(64 * 1024, file);
    let mut line_buf = Vec::with_capacity(512);

    let mut saw_header = false;
    let mut in_block = false;
    let mut idx_zone_name: Option<usize> = None;
    let mut idx_floor_area: Option<usize> = None;
    let mut idx_zm: Option<usize> = None;
    let mut idx_zlm: Option<usize> = None;
    let mut idx_part: Option<usize> = None;

    let mut n_zones = 0usize;
    let mut area_plain = 0.0_f64;
    let mut area_mult = 0.0_f64;
    let mut max_zm = 0.0_f64;
    let mut max_zlm = 0.0_f64;
    let mut n_excluded = 0usize;
    let mut n_row_errors = 0usize;
    let mut zone_multipliers = HashMap::new();

    let header_finder = memmem::Finder::new(EIO_HEADER_MARKER);

    loop {
        line_buf.clear();
        match reader.read_until(b'\n', &mut line_buf) {
            Ok(0) => break,
            Ok(_) => {}
            Err(e) => {
                return EioZoneInfo {
                    parse_status: format!("file_error:{e}"),
                    ..Default::default()
                };
            }
        }
        let line = &line_buf;
        if !saw_header {
            if line.starts_with(EIO_HEADER_MARKER) && header_finder.find(line).is_some() {
                saw_header = true;
                let mut rdr = csv::ReaderBuilder::new()
                    .has_headers(false)
                    .flexible(true)
                    .from_reader(line.as_slice());
                let mut rec = csv::StringRecord::new();
                if rdr.read_record(&mut rec).unwrap_or(false) {
                    for (i, field) in rec.iter().enumerate() {
                        match field.trim() {
                            "Zone Name" => idx_zone_name = Some(i),
                            "Floor Area {m2}" => idx_floor_area = Some(i),
                            "Zone Multiplier" => idx_zm = Some(i),
                            "Zone List Multiplier" => idx_zlm = Some(i),
                            "Part of Total Building Area" => idx_part = Some(i),
                            _ => {}
                        }
                    }
                }
            }
            continue;
        }
        if line.starts_with(EIO_DATA_PREFIX) {
            in_block = true;
            n_zones += 1;
            let mut rdr = csv::ReaderBuilder::new()
                .has_headers(false)
                .flexible(true)
                .from_reader(line.as_slice());
            let mut rec = csv::StringRecord::new();
            if !rdr.read_record(&mut rec).unwrap_or(false) {
                n_row_errors += 1;
                continue;
            }
            let get_f64 = |opt_idx: Option<usize>| -> Option<f64> {
                let idx = opt_idx?;
                let raw = rec.get(idx)?.trim();
                fast_float2::parse::<f64, _>(raw).ok()
            };
            let Some(zm) = get_f64(idx_zm) else {
                n_row_errors += 1;
                continue;
            };
            let Some(zlm) = get_f64(idx_zlm) else {
                n_row_errors += 1;
                continue;
            };
            if let Some(z_idx) = idx_zone_name {
                if let Some(zn) = rec.get(z_idx) {
                    zone_multipliers.insert(zn.trim().to_uppercase(), zm * zlm);
                }
            }
            let Some(floor_area) = get_f64(idx_floor_area) else {
                n_row_errors += 1;
                continue;
            };
            let Some(part_idx) = idx_part else {
                n_row_errors += 1;
                continue;
            };
            let Some(part_raw) = rec.get(part_idx) else {
                n_row_errors += 1;
                continue;
            };
            if zm > max_zm {
                max_zm = zm;
            }
            if zlm > max_zlm {
                max_zlm = zlm;
            }
            if part_raw.trim() == "Yes" {
                area_plain += floor_area;
                area_mult += floor_area * zm * zlm;
            } else {
                n_excluded += 1;
            }
        } else if in_block {
            break;
        }
    }

    let parse_status = if !saw_header {
        "no_zone_information_header".to_owned()
    } else if n_zones == 0 {
        "header_found_zero_rows".to_owned()
    } else if n_row_errors > 0 {
        format!("ok_with_{n_row_errors}_row_errors")
    } else {
        "ok".to_owned()
    };

    EioZoneInfo {
        n_zones,
        area_plain_m2: area_plain,
        area_multiplier_aware_m2: area_mult,
        max_zone_multiplier: max_zm.round() as i64,
        max_zone_list_multiplier: max_zlm.round() as i64,
        n_zones_excluded_not_in_total_area: n_excluded,
        parse_status,
        zone_multipliers,
    }
}
