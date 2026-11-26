//! Single open-read-close `rusqlite` reader for `eplusout.sql` (`DR06`, `OPEN-46`, `OPEN-60`, `OPEN-61`, `OPEN-64`).

use std::collections::{BTreeMap, HashMap, HashSet};
use std::path::Path;
use std::time::Duration;

use openubem_schema::{
    AbupsDistrictRow, EndUse, EndUseLedger, FloorAreaProvenance, GJ_TO_KWH, J_TO_KWH,
    PositiveAreaM2, RawMeters, ReconciledLedger, ResolvedFloorArea, SchemaError,
    append_flag_token_delimited,
};
use rusqlite::{Connection, OpenFlags};

use crate::eio_reader::parse_eio_file;
use crate::error::ResultsError;

/// Encoded parsed zone name (`resolve_zone`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedZone {
    pub osm_id_uc: String,
    pub floor: i64,
    pub label: String,
}

/// Strip trailing case-insensitive `\s+IDEAL LOADS AIR SYSTEM$` suffix (`parser.py:94-99`).
pub fn strip_ideal_loads_suffix(key_value: &str) -> &str {
    const SUFFIX: &str = "IDEAL LOADS AIR SYSTEM";
    if key_value.len() <= SUFFIX.len() {
        return key_value;
    }
    let split_at = key_value.len() - SUFFIX.len();
    if key_value[split_at..].eq_ignore_ascii_case(SUFFIX) {
        let before = &key_value[..split_at];
        let trimmed = before.trim_end();
        if trimmed.len() < before.len() {
            return trimmed;
        }
    }
    key_value
}

fn strip_optional_storey_suffix(s: &str) -> &str {
    // Match `(?:\s+STOREY\s+\d+)?$` on uppercase input.
    let bytes = s.as_bytes();
    let mut end = bytes.len();
    let mut d = end;
    while d > 0 && bytes[d - 1].is_ascii_digit() {
        d -= 1;
    }
    if d == end {
        return s;
    }
    end = d;
    let mut ws2 = end;
    while ws2 > 0 && bytes[ws2 - 1].is_ascii_whitespace() {
        ws2 -= 1;
    }
    if ws2 == end {
        return s;
    }
    let before_num = &s[..ws2];
    let Some(before_kw) = before_num.strip_suffix("STOREY") else {
        return s;
    };
    let trimmed = before_kw.trim_end();
    if trimmed.len() < before_kw.len() {
        trimmed
    } else {
        s
    }
}

/// Deterministic Rust twin of `openubem/results/parser.py::resolve_zone`.
pub fn resolve_zone(key_value: &str) -> Option<ResolvedZone> {
    let stripped = strip_ideal_loads_suffix(key_value.trim());
    let upper = stripped.to_uppercase();
    let mut s = upper.as_str();
    if let Some(rest) = s.strip_prefix("BLOCK") {
        let rest_trimmed = rest.trim_start();
        if rest_trimmed.len() < rest.len() {
            s = rest_trimmed;
        }
    }
    let core = strip_optional_storey_suffix(s);
    let bytes = core.as_bytes();

    // Non-greedy `(?P<osm_id>.+?)_F(?P<floor>\d+)_(?P<label>WHOLE|CORE|PERIM\d*)$`:
    // scan left to right starting from index 1 (osm_id non-empty).
    for i in 1..bytes.len().saturating_sub(2) {
        if bytes[i] == b'_' && bytes[i + 1] == b'F' {
            let mut j = i + 2;
            while j < bytes.len() && bytes[j].is_ascii_digit() {
                j += 1;
            }
            if j == i + 2 || j >= bytes.len() || bytes[j] != b'_' {
                continue;
            }
            let floor_str = &core[i + 2..j];
            let Ok(floor) = floor_str.parse::<i64>() else {
                continue;
            };
            let label = &core[j + 1..];
            let label_ok = label == "WHOLE"
                || label == "CORE"
                || label
                    .strip_prefix("PERIM")
                    .map(|tail| tail.bytes().all(|b| b.is_ascii_digit()))
                    .unwrap_or(false);
            if label_ok {
                return Some(ResolvedZone {
                    osm_id_uc: core[..i].to_owned(),
                    floor,
                    label: label.to_owned(),
                });
            }
        }
    }
    None
}

/// Build an RFC-safe `file:<path>?mode=ro` SQLite URI without unsafe `immutable=1`.
fn sqlite_readonly_uri(sql_path: &Path) -> String {
    let raw = sql_path.to_string_lossy();
    let mut encoded = String::with_capacity(raw.len() + 16);
    encoded.push_str("file:");
    for b in raw.bytes() {
        match b {
            b'?' => encoded.push_str("%3F"),
            b'#' => encoded.push_str("%23"),
            b'%' => encoded.push_str("%25"),
            b';' => encoded.push_str("%3B"),
            _ => encoded.push(b as char),
        }
    }
    encoded.push_str("?mode=ro");
    encoded
}

/// Check for non-empty `-wal` or `-journal` sidecar files indicating an uncheckpointed/crashed DB.
pub fn find_nonempty_sqlite_sidecar(sql_path: &Path) -> Option<String> {
    let base = sql_path.as_os_str().to_string_lossy();
    for suffix in ["-wal", "-journal"] {
        let candidate = format!("{base}{suffix}");
        let p = Path::new(&candidate);
        if let Ok(meta) = p.metadata() {
            if meta.len() > 0 {
                return Some(p.display().to_string());
            }
        }
    }
    None
}

/// Open `eplusout.sql` read-only with safe `PRAGMA mmap_size` and 2s `busy_timeout`.
pub fn open_sqlite_readonly(sql_path: &Path, mmap_bytes: u64) -> Result<Connection, ResultsError> {
    if let Some(sidecar) = find_nonempty_sqlite_sidecar(sql_path) {
        return Err(ResultsError::IncompleteWalOrJournal { sidecar });
    }
    let uri = sqlite_readonly_uri(sql_path);
    let flags = OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI;
    let conn = Connection::open_with_flags(uri, flags).map_err(|e| ResultsError::Sqlite {
        path: sql_path.display().to_string(),
        detail: e.to_string(),
    })?;
    conn.busy_timeout(Duration::from_millis(2000))
        .map_err(|e| ResultsError::Sqlite {
            path: sql_path.display().to_string(),
            detail: e.to_string(),
        })?;
    let pragma = format!("PRAGMA mmap_size = {mmap_bytes};");
    let _ = conn.execute_batch(&pragma);
    Ok(conn)
}

/// Exact integrity check output (`parser.py::check_building_integrity`).
#[derive(Debug, Clone, Default)]
pub struct BuildingIntegrity {
    pub abups_ok: Option<bool>,
    pub meter_ok: Option<bool>,
    pub gas_zero: Option<bool>,
}

/// Run integrity gates on an already-open `rusqlite::Connection`.
pub fn check_integrity_on_conn(conn: &Connection) -> Result<BuildingIntegrity, rusqlite::Error> {
    let hourly_j: f64 = conn.query_row(
        "SELECT COALESCE(SUM(r.Value), 0.0) \
         FROM ReportData r \
         JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
         WHERE d.Name IN ('Zone Lights Electricity Energy', 'Zone Electric Equipment Electricity Energy') \
           AND d.ReportingFrequency = 'Hourly'",
        [],
        |row| row.get(0),
    )?;

    let abups_gj: f64 = conn.query_row(
        "SELECT COALESCE(SUM(CAST(Value AS REAL)), 0.0) \
         FROM TabularDataWithStrings \
         WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary' \
           AND TableName = 'End Uses' \
           AND RowName IN ('Interior Lighting', 'Interior Equipment') \
           AND ColumnName = 'Electricity' \
           AND Units = 'GJ'",
        [],
        |row| row.get(0),
    )?;
    let abups_j = abups_gj * 1e9;
    let abups_ok = if abups_j > 0.0 {
        (hourly_j - abups_j).abs() / abups_j <= 0.005
    } else {
        hourly_j == 0.0
    };

    let facility_j: f64 = conn.query_row(
        "SELECT COALESCE(SUM(r.Value), 0.0) \
         FROM ReportData r \
         JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
         WHERE d.Name = 'Electricity:Facility' AND d.ReportingFrequency = 'Run Period'",
        [],
        |row| row.get(0),
    )?;

    let meter_ok = if facility_j > 0.0 {
        (hourly_j - facility_j).abs() / facility_j <= 0.01
    } else {
        hourly_j == 0.0
    };

    let gas_j: f64 = conn.query_row(
        "SELECT COALESCE(SUM(r.Value), 0.0) \
         FROM ReportData r \
         JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
         WHERE d.Name = 'NaturalGas:Facility' AND d.ReportingFrequency = 'Run Period'",
        [],
        |row| row.get(0),
    )?;

    Ok(BuildingIntegrity {
        abups_ok: Some(abups_ok),
        meter_ok: Some(meter_ok),
        gas_zero: Some(gas_j == 0.0),
    })
}

/// Standalone `check_building_integrity` parity entrypoint.
pub fn check_building_integrity_sql(sql_path: &Path, mmap_bytes: u64) -> BuildingIntegrity {
    if !sql_path.exists() {
        return BuildingIntegrity::default();
    }
    let Ok(conn) = open_sqlite_readonly(sql_path, mmap_bytes) else {
        return BuildingIntegrity::default();
    };
    check_integrity_on_conn(&conn).unwrap_or_default()
}

/// Read `RunPeriod` meters + 14 ABUPS District Heating rows on one open `Connection`.
fn read_meters_on_conn(conn: &Connection) -> BTreeMap<&'static str, f64> {
    let mut meters: BTreeMap<&'static str, f64> = BTreeMap::new();
    let known = [
        "Cooling:Electricity",
        "Heating:Electricity",
        "Heating:NaturalGas",
        "Fans:Electricity",
        "Pumps:Electricity",
        "WaterSystems:NaturalGas",
        "WaterSystems:Electricity",
        "InteriorEquipment:NaturalGas",
        "Refrigeration:Electricity",
        "Elevators:InteriorEquipment:Electricity",
    ];
    for k in known {
        meters.insert(k, 0.0);
    }
    for row in AbupsDistrictRow::ALL {
        meters.insert(row.pseudo_meter_key(), 0.0);
    }

    if let Ok(mut stmt) = conn.prepare(
        "SELECT d.Name AS meter_name, r.Value AS value_j \
         FROM ReportData r \
         JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
         WHERE d.ReportingFrequency = 'Run Period' \
           AND d.Name IN ('Cooling:Electricity', 'Heating:Electricity', \
                          'Heating:NaturalGas', 'Fans:Electricity', \
                          'Pumps:Electricity', \
                          'WaterSystems:NaturalGas', 'WaterSystems:Electricity', \
                          'InteriorEquipment:NaturalGas', \
                          'Refrigeration:Electricity', \
                          'Elevators:InteriorEquipment:Electricity')",
    ) {
        if let Ok(mut rows) = stmt.query([]) {
            while let Ok(Some(row)) = rows.next() {
                if let (Ok(name), Ok(Some(val_j))) =
                    (row.get::<_, String>(0), row.get::<_, Option<f64>>(1))
                {
                    if let Some(&key) = known.iter().find(|&&k| k == name) {
                        if let Some(slot) = meters.get_mut(key) {
                            *slot += val_j * J_TO_KWH;
                        }
                    }
                }
            }
        }
    }

    // ABUPS District Heating read wrapped cleanly so missing ABUPS -> 0.0 (parser.py:217-222).
    if let Ok(mut stmt) = conn.prepare(
        "SELECT RowName, Value FROM TabularDataWithStrings \
         WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' \
           AND TableName='End Uses' AND ColumnName='District Heating'",
    ) {
        if let Ok(mut rows) = stmt.query([]) {
            while let Ok(Some(row)) = rows.next() {
                let Ok(row_name) = row.get::<_, String>(0) else {
                    continue;
                };
                let Some(abups) = AbupsDistrictRow::from_abups_row_name(&row_name) else {
                    continue;
                };
                let val_res = row.get::<_, Option<String>>(1);
                let gj_opt = match val_res {
                    Ok(Some(s)) => {
                        let trimmed = s.trim();
                        if trimmed.is_empty() {
                            None
                        } else {
                            fast_float2::parse::<f64, _>(trimmed).ok()
                        }
                    }
                    _ => row.get::<_, Option<f64>>(1).ok().flatten(),
                };
                if let Some(gj) = gj_opt {
                    meters.insert(abups.pseudo_meter_key(), gj * GJ_TO_KWH);
                }
            }
        }
    }
    meters
}

fn read_sql_zone_area_and_multipliers(conn: &Connection) -> (f64, HashMap<String, f64>) {
    let mut area = 0.0_f64;
    let mut mults = HashMap::new();
    let Ok(mut stmt) =
        conn.prepare("SELECT ZoneName, FloorArea, Multiplier, ListMultiplier, IsPartOfTotalArea FROM Zones")
    else {
        return (0.0, mults);
    };
    let Ok(mut rows) = stmt.query([]) else {
        return (0.0, mults);
    };
    while let Ok(Some(row)) = rows.next() {
        let Ok(zn) = row.get::<_, Option<String>>(0) else {
            continue;
        };
        let fa: f64 = row.get::<_, Option<f64>>(1).ok().flatten().unwrap_or(0.0);
        let zm: f64 = row.get::<_, Option<f64>>(2).ok().flatten().unwrap_or(1.0);
        let zlm: f64 = row.get::<_, Option<f64>>(3).ok().flatten().unwrap_or(1.0);
        let part: i64 = row.get::<_, Option<i64>>(4).ok().flatten().unwrap_or(0);
        if let Some(name) = zn {
            mults.insert(name.trim().to_uppercase(), zm * zlm);
        }
        if part == 1 {
            area += fa * zm * zlm;
        }
    }
    (area, mults)
}

/// Complete single-building metrics result returned from `parse_building_sql_single_pass`.
#[derive(Debug, Clone)]
pub struct ParsedBuildingMetrics {
    pub osm_id: String,
    pub parse_status: String,
    pub error_summary: String,
    pub data_quality_flag: String,
    pub floor_area_m2: f64,
    pub floor_area_provenance: String,
    pub eui: BTreeMap<&'static str, f64>,
    pub iod: f64,
    pub abups_ok: Option<bool>,
    pub meter_ok: Option<bool>,
    pub gas_zero: Option<bool>,
}

/// Input specification for one building harvest task.
#[derive(Debug, Clone)]
pub struct BuildingHarvestSpec {
    pub osm_id: String,
    pub sql_path: Option<String>,
    pub footprint_area_m2: f64,
    pub num_floors: i64,
    pub num_zones: i64,
    pub data_quality_flag: String,
    pub resolution_mode: Option<String>,
}

/// Single open-read-close parse of one building (`eplusout.eio` + `eplusout.sql`).
pub fn harvest_one_building_sql(
    spec: &BuildingHarvestSpec,
    summer_months: (i64, i64),
    include_integrity: bool,
    mmap_bytes: u64,
) -> Result<ParsedBuildingMetrics, ResultsError> {
    let sql_path_opt = spec.sql_path.as_deref().map(Path::new);

    // Resolve `.eio` first in one streaming pass (`OPEN-01` + `OPEN-60`).
    let mut eio_info = None;
    let mut floor_area = spec.footprint_area_m2 * (spec.num_floors as f64);
    let mut area_prov = FloorAreaProvenance::FootprintFallback;
    let mut zone_multipliers: HashMap<String, f64> = HashMap::new();

    if let Some(sql_p) = sql_path_opt {
        if let Some(parent) = sql_p.parent() {
            let eio_p = parent.join("eplusout.eio");
            if eio_p.exists() {
                let info = parse_eio_file(&eio_p);
                let ok_status = info.parse_status == "ok" || info.parse_status.starts_with("ok_with_");
                if ok_status && info.area_multiplier_aware_m2 > 0.0 {
                    floor_area = info.area_multiplier_aware_m2;
                    area_prov = FloorAreaProvenance::EioSimulated;
                }
                if !info.zone_multipliers.is_empty() {
                    zone_multipliers = info.zone_multipliers.clone();
                }
                eio_info = Some(info);
            }
        }
    }

    let Some(sql_p) = sql_path_opt.filter(|p| p.exists()) else {
        return Ok(failed_metrics(
            spec,
            "failed_parse",
            "no SQL or CSV",
            floor_area,
            area_prov,
        ));
    };

    let conn = match open_sqlite_readonly(sql_p, mmap_bytes) {
        Ok(c) => c,
        Err(ResultsError::IncompleteWalOrJournal { sidecar }) => {
            let dq = append_flag_token_delimited(
                Some(&spec.data_quality_flag),
                "incomplete_wal_or_journal",
                ',',
            );
            return Ok(ParsedBuildingMetrics {
                osm_id: spec.osm_id.clone(),
                parse_status: "failed_parse".to_owned(),
                error_summary: format!("incomplete SQLite WAL/journal sidecar: {sidecar}"),
                data_quality_flag: dq,
                floor_area_m2: floor_area,
                floor_area_provenance: area_prov.as_str().to_owned(),
                eui: BTreeMap::new(),
                iod: f64::NAN,
                abups_ok: None,
                meter_ok: None,
                gas_zero: None,
            });
        }
        Err(e) => {
            return Ok(failed_metrics(
                spec,
                "failed_parse",
                &e.to_string(),
                floor_area,
                area_prov,
            ));
        }
    };

    // Fallback to SQL Zones if `.eio` didn't resolve floor area or multipliers.
    if area_prov == FloorAreaProvenance::FootprintFallback || zone_multipliers.is_empty() {
        let (sql_area, sql_mults) = read_sql_zone_area_and_multipliers(&conn);
        if area_prov == FloorAreaProvenance::FootprintFallback && sql_area > 0.0 {
            floor_area = sql_area;
            area_prov = FloorAreaProvenance::SqlSimulated;
        }
        if zone_multipliers.is_empty() && !sql_mults.is_empty() {
            zone_multipliers = sql_mults;
        }
    }
    let _ = eio_info;

    // Fetch only the 5 hourly variables needed for EUI/zone-integrity/IOD + IdealLoads keys for fallback integrity.
    let hourly_sql = "\
        SELECT d.KeyValue, d.Name, d.Units, t.Month, t.Day, t.Hour, r.Value \
        FROM ReportData r \
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
        JOIN Time t ON r.TimeIndex = t.TimeIndex \
        WHERE d.ReportingFrequency = 'Hourly' \
          AND (d.Name IN ( \
              'Zone Lights Electricity Energy', \
              'Zone Electric Equipment Electricity Energy', \
              'Site Outdoor Air Drybulb Temperature', \
              'Zone Operative Temperature', \
              'Zone People Occupant Count' \
          ) OR d.Name LIKE 'Zone Ideal Loads%')";

    let mut lights_by_zone: HashMap<String, f64> = HashMap::new();
    let mut equip_by_zone: HashMap<String, f64> = HashMap::new();
    let mut has_lights_var = false;
    let mut has_equip_var = false;
    let mut ideal_loads_keys: HashSet<String> = HashSet::new();

    // IOD accumulators
    let mut site_sum = [0.0_f64; 13];
    let mut site_cnt = [0_u64; 13];
    let mut has_site_temp = false;
    let mut ot_rows: Vec<(String, i64, i64, i64, f64)> = Vec::new();
    let mut occ_map: HashMap<(String, i64, i64, i64), f64> = HashMap::new();
    let mut has_occ_var = false;

    let mut row_count = 0usize;
    {
        let Ok(mut stmt) = conn.prepare(hourly_sql) else {
            return Ok(failed_metrics(
                spec,
                "failed_parse",
                "ReportData hourly query prepare failed",
                floor_area,
                area_prov,
            ));
        };
        let Ok(mut rows) = stmt.query([]) else {
            return Ok(failed_metrics(
                spec,
                "failed_parse",
                "ReportData hourly query failed",
                floor_area,
                area_prov,
            ));
        };
        while let Ok(Some(row)) = rows.next() {
            row_count += 1;
            let kv: String = row.get::<_, Option<String>>(0)?.unwrap_or_default();
            let var_name: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
            let units: String = row.get::<_, Option<String>>(2)?.unwrap_or_default();
            let month: i64 = row.get::<_, i64>(3)?;
            let day: i64 = row.get::<_, i64>(4)?;
            let hour: i64 = row.get::<_, i64>(5)?;
            let mut val: f64 = row.get::<_, f64>(6)?;
            if units == "J" {
                val *= J_TO_KWH;
            }
            match var_name.as_str() {
                "Zone Lights Electricity Energy" => {
                    has_lights_var = true;
                    let key_up = kv.trim().to_uppercase();
                    *lights_by_zone.entry(key_up).or_insert(0.0) += val;
                }
                "Zone Electric Equipment Electricity Energy" => {
                    has_equip_var = true;
                    let key_up = kv.trim().to_uppercase();
                    *equip_by_zone.entry(key_up).or_insert(0.0) += val;
                }
                "Site Outdoor Air Drybulb Temperature" => {
                    has_site_temp = true;
                    if (1..=12).contains(&month) {
                        site_sum[month as usize] += val;
                        site_cnt[month as usize] += 1;
                    }
                }
                "Zone Operative Temperature" => {
                    if month >= summer_months.0 && month <= summer_months.1 {
                        ot_rows.push((kv, month, day, hour, val));
                    }
                }
                "Zone People Occupant Count" => {
                    has_occ_var = true;
                    if month >= summer_months.0 && month <= summer_months.1 {
                        occ_map.insert((kv, month, day, hour), val);
                    }
                }
                _ => {
                    if var_name.starts_with("Zone Ideal Loads") {
                        ideal_loads_keys.insert(kv.to_uppercase());
                    }
                }
            }
        }
    }

    if row_count == 0 {
        return Ok(failed_metrics(
            spec,
            "failed_zone_mismatch",
            &format!("zone count mismatch: found 0, manifest says {}", spec.num_zones),
            floor_area,
            area_prov,
        ));
    }

    // Zone integrity check (`_check_zone_integrity` parity + I2 fail-fast)
    let zone_keys: HashSet<String> = if has_lights_var {
        lights_by_zone.keys().cloned().collect()
    } else {
        ideal_loads_keys
    };

    let layout_mode = matches!(
        spec.resolution_mode.as_deref(),
        Some("layout_assign") | Some("layout_assigner")
    );
    if layout_mode {
        if !zone_keys.iter().any(|k| !k.trim().is_empty()) {
            return Ok(failed_metrics(
                spec,
                "failed_zone_mismatch",
                "layout_assign: zero zone-level keys found in SQL (corrupt/empty result)",
                floor_area,
                area_prov,
            ));
        }
    } else {
        let target_uc = spec.osm_id.to_uppercase();
        let mut foreign = Vec::new();
        let mut resolved_ids = HashSet::new();
        for kv in &zone_keys {
            if let Some(parsed) = resolve_zone(kv) {
                if parsed.osm_id_uc != target_uc {
                    foreign.push(kv.clone());
                } else {
                    resolved_ids.insert(format!(
                        "{}_F{}_{}",
                        parsed.osm_id_uc, parsed.floor, parsed.label
                    ));
                }
            }
        }
        if !foreign.is_empty() {
            return Err(ResultsError::I2ForeignOsmId {
                osm_id: spec.osm_id.clone(),
                foreign_samples: foreign.into_iter().take(3).collect(),
            });
        }
        if resolved_ids.is_empty() {
            return Ok(failed_metrics(
                spec,
                "failed_zone_mismatch",
                &format!("zone count mismatch: found 0, manifest says {}", spec.num_zones),
                floor_area,
                area_prov,
            ));
        }
    }

    if !has_lights_var {
        return Ok(failed_metrics(
            spec,
            "failed_parse",
            "missing required EUI variable: Zone Lights Electricity Energy",
            floor_area,
            area_prov,
        ));
    }
    if !has_equip_var {
        return Ok(failed_metrics(
            spec,
            "failed_parse",
            "missing required EUI variable: Zone Electric Equipment Electricity Energy",
            floor_area,
            area_prov,
        ));
    }

    let sum_scaled = |map: &HashMap<String, f64>| -> f64 {
        if zone_multipliers.is_empty() {
            map.values().sum()
        } else {
            map.iter()
                .map(|(k, &v)| v * zone_multipliers.get(k).copied().unwrap_or(1.0))
                .sum()
        }
    };
    let lighting_kwh = sum_scaled(&lights_by_zone);
    let equipment_kwh = sum_scaled(&equip_by_zone);

    let meters = read_meters_on_conn(&conn);
    let area_pos = PositiveAreaM2::try_new(floor_area)
        .map_err(|_| ResultsError::Schema(SchemaError::NonPositiveFloorArea(floor_area)))?;
    let mut ledger: EndUseLedger<RawMeters> = EndUseLedger::new(ResolvedFloorArea {
        area_m2: area_pos,
        provenance: area_prov,
    });
    ledger.set_core_gas_elec(EndUse::Cooling, 0.0, meters["Cooling:Electricity"]);
    ledger.set_core_gas_elec(
        EndUse::Heating,
        meters["Heating:NaturalGas"],
        meters["Heating:Electricity"],
    );
    ledger.set_core_gas_elec(EndUse::InteriorLighting, 0.0, lighting_kwh);
    ledger.set_core_gas_elec(EndUse::InteriorEquipment, 0.0, equipment_kwh);
    ledger.set_core_gas_elec(EndUse::Fans, 0.0, meters["Fans:Electricity"]);
    ledger.set_core_gas_elec(EndUse::Pumps, 0.0, meters["Pumps:Electricity"]);
    ledger.set_core_gas_elec(
        EndUse::WaterSystems,
        meters["WaterSystems:NaturalGas"],
        meters["WaterSystems:Electricity"],
    );
    ledger.set_core_gas_elec(EndUse::Cooking, meters["InteriorEquipment:NaturalGas"], 0.0);
    ledger.set_core_gas_elec(EndUse::Refrigeration, 0.0, meters["Refrigeration:Electricity"]);
    ledger.set_core_gas_elec(
        EndUse::Elevators,
        0.0,
        meters["Elevators:InteriorEquipment:Electricity"],
    );
    for row in AbupsDistrictRow::ALL {
        ledger.set_abups_district(row, meters[row.pseudo_meter_key()]);
    }
    let reconciled: EndUseLedger<ReconciledLedger> = ledger.reconcile()?;
    let eui = reconciled.to_eui_columns();

    // Compute IOD (`_compute_iod`)
    let mut dq_flag = spec.data_quality_flag.clone();
    let iod = if !has_site_temp || ot_rows.is_empty() || !has_occ_var {
        dq_flag = append_flag_token_delimited(Some(&dq_flag), "IOD_NO_OCCUPIED_HOURS", ',');
        f64::NAN
    } else {
        let mut monthly_mean = [0.0_f64; 13];
        for m in 1..=12 {
            if site_cnt[m] > 0 {
                monthly_mean[m] = site_sum[m] / (site_cnt[m] as f64);
            }
        }
        let mut by_zone: HashMap<String, (f64, u64, f64)> = HashMap::new();
        for (kv, m, d, h, ot) in ot_rows {
            let occ = occ_map.get(&(kv.clone(), m, d, h)).copied().unwrap_or(0.0);
            if occ > 0.0 {
                let tave = monthly_mean[m as usize];
                let tcomf = (0.31 * tave + 17.8) + 2.5;
                let exc = (ot - tcomf).max(0.0);
                let entry = by_zone.entry(kv).or_insert((0.0, 0, 0.0));
                entry.0 += exc;
                entry.1 += 1;
                entry.2 += occ;
            }
        }
        let total_weight: f64 = by_zone.values().map(|v| v.2).sum();
        if by_zone.is_empty() || total_weight == 0.0 {
            dq_flag = append_flag_token_delimited(Some(&dq_flag), "IOD_NO_OCCUPIED_HOURS", ',');
            f64::NAN
        } else {
            by_zone
                .values()
                .map(|&(sum_exc, cnt, tot_occ)| (sum_exc / (cnt as f64)) * tot_occ)
                .sum::<f64>()
                / total_weight
        }
    };

    let integrity = if include_integrity {
        check_integrity_on_conn(&conn).unwrap_or_default()
    } else {
        BuildingIntegrity::default()
    };

    Ok(ParsedBuildingMetrics {
        osm_id: spec.osm_id.clone(),
        parse_status: "success".to_owned(),
        error_summary: String::new(),
        data_quality_flag: dq_flag,
        floor_area_m2: floor_area,
        floor_area_provenance: area_prov.as_str().to_owned(),
        eui,
        iod,
        abups_ok: integrity.abups_ok,
        meter_ok: integrity.meter_ok,
        gas_zero: integrity.gas_zero,
    })
}

fn failed_metrics(
    spec: &BuildingHarvestSpec,
    status: &str,
    msg: &str,
    floor_area: f64,
    area_prov: FloorAreaProvenance,
) -> ParsedBuildingMetrics {
    let err = if msg.len() > 500 { &msg[..500] } else { msg };
    ParsedBuildingMetrics {
        osm_id: spec.osm_id.clone(),
        parse_status: status.to_owned(),
        error_summary: err.to_owned(),
        data_quality_flag: spec.data_quality_flag.clone(),
        floor_area_m2: floor_area,
        floor_area_provenance: area_prov.as_str().to_owned(),
        eui: BTreeMap::new(),
        iod: f64::NAN,
        abups_ok: None,
        meter_ok: None,
        gas_zero: None,
    }
}

/// Query hourly rows into an Arrow `RecordBatch` matching `parse_building_sql` columns.
pub fn query_hourly_to_record_batch(
    sql_path: &Path,
    mmap_bytes: u64,
) -> Result<arrow_array::RecordBatch, ResultsError> {
    use arrow_array::builder::{Float64Builder, Int64Builder, StringBuilder};
    use arrow_schema::{DataType, Field, Schema};
    use std::sync::Arc;

    let rows = query_hourly_rows(sql_path, mmap_bytes)?;
    let n = rows.len();
    let mut kv_b = StringBuilder::with_capacity(n, n * 16);
    let mut name_b = StringBuilder::with_capacity(n, n * 32);
    let mut units_b = StringBuilder::with_capacity(n, n * 4);
    let mut month_b = Int64Builder::with_capacity(n);
    let mut day_b = Int64Builder::with_capacity(n);
    let mut hour_b = Int64Builder::with_capacity(n);
    let mut val_b = Float64Builder::with_capacity(n);

    for (kv, name, units, m, d, h, v) in rows {
        kv_b.append_value(kv);
        name_b.append_value(name);
        units_b.append_value(units);
        month_b.append_value(m);
        day_b.append_value(d);
        hour_b.append_value(h);
        val_b.append_value(v);
    }

    let schema = Arc::new(Schema::new(vec![
        Field::new("key_value", DataType::Utf8, false),
        Field::new("variable_name", DataType::Utf8, false),
        Field::new("units", DataType::Utf8, false),
        Field::new("Month", DataType::Int64, false),
        Field::new("Day", DataType::Int64, false),
        Field::new("Hour", DataType::Int64, false),
        Field::new("value", DataType::Float64, false),
    ]));
    arrow_array::RecordBatch::try_new(
        schema,
        vec![
            Arc::new(kv_b.finish()),
            Arc::new(name_b.finish()),
            Arc::new(units_b.finish()),
            Arc::new(month_b.finish()),
            Arc::new(day_b.finish()),
            Arc::new(hour_b.finish()),
            Arc::new(val_b.finish()),
        ],
    )
    .map_err(|e| ResultsError::ArrowParquet(e.to_string()))
}

/// Provide a minimal SQLite table read equivalent to `parse_building_sql(sql_path)` for direct FFI use.
pub fn query_hourly_rows(
    sql_path: &Path,
    mmap_bytes: u64,
) -> Result<Vec<(String, String, String, i64, i64, i64, f64)>, ResultsError> {
    let conn = open_sqlite_readonly(sql_path, mmap_bytes)?;
    let q = "\
        SELECT d.KeyValue, d.Name, d.Units, t.Month, t.Day, t.Hour, r.Value \
        FROM ReportData r \
        JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex \
        JOIN Time t ON r.TimeIndex = t.TimeIndex \
        WHERE d.ReportingFrequency = 'Hourly'";
    let mut stmt = conn.prepare(q).map_err(|e| ResultsError::Sqlite {
        path: sql_path.display().to_string(),
        detail: e.to_string(),
    })?;
    let mut rows = stmt.query([]).map_err(|e| ResultsError::Sqlite {
        path: sql_path.display().to_string(),
        detail: e.to_string(),
    })?;
    let mut out = Vec::new();
    while let Ok(Some(row)) = rows.next() {
        let kv: String = row.get::<_, Option<String>>(0).unwrap_or(None).unwrap_or_default();
        let name: String = row.get::<_, Option<String>>(1).unwrap_or(None).unwrap_or_default();
        let raw_units: String = row.get::<_, Option<String>>(2).unwrap_or(None).unwrap_or_default();
        let month: i64 = row.get(3).unwrap_or(0);
        let day: i64 = row.get(4).unwrap_or(0);
        let hour: i64 = row.get(5).unwrap_or(0);
        let raw_val: f64 = row.get(6).unwrap_or(f64::NAN);
        let (units, val) = if raw_units == "J" {
            ("kWh".to_owned(), raw_val * J_TO_KWH)
        } else {
            (raw_units, raw_val)
        };
        out.push((kv, name, units, month, day, hour, val));
    }
    Ok(out)
}
