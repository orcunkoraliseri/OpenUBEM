//! `rayon` parallel campaign harvester producing Apache Arrow `RecordBatch` and Parquet (`DR06`).

use std::collections::HashMap;
use std::fs;
use std::path::Path;
use std::sync::Arc;

use arrow_array::builder::{BooleanBuilder, Float64Builder, StringBuilder};
use arrow_array::RecordBatch;
use arrow_schema::{DataType, Field, Schema};
use parquet::arrow::ArrowWriter;
use parquet::basic::Compression;
use parquet::file::properties::WriterProperties;
use rayon::prelude::*;

use crate::error::ResultsError;
use crate::sqlite_reader::{BuildingHarvestSpec, ParsedBuildingMetrics, harvest_one_building_sql};

/// Parallel harvest over `specs`, returning a zero-copy-ready Arrow `RecordBatch`.
pub fn harvest_buildings_to_record_batch(
    specs: &[BuildingHarvestSpec],
    state_elec_factors: &HashMap<String, f64>,
    state_by_osm: &HashMap<String, String>,
    f_gas: f64,
    f_dh: f64,
    summer_months: (i64, i64),
    include_integrity: bool,
    mmap_bytes: u64,
) -> Result<RecordBatch, ResultsError> {
    let parsed: Vec<ParsedBuildingMetrics> = specs
        .par_iter()
        .map(|spec| harvest_one_building_sql(spec, summer_months, include_integrity, mmap_bytes))
        .collect::<Result<Vec<_>, ResultsError>>()?;

    let n = parsed.len();
    let eui_cols = [
        "heating_eui_kwh_m2",
        "cooling_eui_kwh_m2",
        "lighting_eui_kwh_m2",
        "equipment_eui_kwh_m2",
        "fans_eui_kwh_m2",
        "pumps_eui_kwh_m2",
        "dhw_gas_eui_kwh_m2",
        "dhw_elec_eui_kwh_m2",
        "dhw_district_eui_kwh_m2",
        "dhw_eui_kwh_m2",
        "cooking_eui_kwh_m2",
        "refrigeration_eui_kwh_m2",
        "elevators_eui_kwh_m2",
        "total_eui_kwh_m2",
    ];
    let gwp_cols = [
        "gwp_heating_kgco2_m2",
        "gwp_cooling_kgco2_m2",
        "gwp_lighting_kgco2_m2",
        "gwp_equipment_kgco2_m2",
        "gwp_fans_kgco2_m2",
        "gwp_pumps_kgco2_m2",
        "gwp_dhw_kgco2_m2",
        "gwp_cooking_kgco2_m2",
        "gwp_refrigeration_kgco2_m2",
        "gwp_elevators_kgco2_m2",
        "gwp_total_kgco2_m2",
    ];

    let mut osm_id_b = StringBuilder::with_capacity(n, n * 16);
    let mut status_b = StringBuilder::with_capacity(n, n * 16);
    let mut err_b = StringBuilder::with_capacity(n, n * 16);
    let mut dq_b = StringBuilder::with_capacity(n, n * 24);
    let mut area_b = Float64Builder::with_capacity(n);
    let mut area_prov_b = StringBuilder::with_capacity(n, n * 20);
    let mut iod_b = Float64Builder::with_capacity(n);
    let mut eui_builders: Vec<Float64Builder> = (0..eui_cols.len())
        .map(|_| Float64Builder::with_capacity(n))
        .collect();
    let mut gwp_builders: Vec<Float64Builder> = (0..gwp_cols.len())
        .map(|_| Float64Builder::with_capacity(n))
        .collect();
    let mut abups_b = BooleanBuilder::with_capacity(n);
    let mut meter_b = BooleanBuilder::with_capacity(n);
    let mut gas_zero_b = BooleanBuilder::with_capacity(n);

    for row in &parsed {
        osm_id_b.append_value(&row.osm_id);
        status_b.append_value(&row.parse_status);
        err_b.append_value(&row.error_summary);
        dq_b.append_value(&row.data_quality_flag);
        area_b.append_value(row.floor_area_m2);
        area_prov_b.append_value(&row.floor_area_provenance);
        if row.iod.is_nan() {
            iod_b.append_null();
        } else {
            iod_b.append_value(row.iod);
        }

        let failed = row.eui.is_empty();
        for (idx, &col) in eui_cols.iter().enumerate() {
            if failed {
                eui_builders[idx].append_value(f64::NAN);
            } else {
                eui_builders[idx].append_value(*row.eui.get(col).unwrap_or(&0.0));
            }
        }

        let state_code = state_by_osm.get(&row.osm_id);
        let f_elec_opt = state_code.and_then(|st| state_elec_factors.get(&st.to_uppercase()).copied());
        if !failed && f_elec_opt.is_some() {
            let f_elec = f_elec_opt.expect("checked");
            let e = &row.eui;
            let get = |k: &str| *e.get(k).unwrap_or(&0.0);
            let gh = (get("heating_eui_kwh_m2") - get("heating_district_eui_kwh_m2")) * f_gas
                + get("heating_district_eui_kwh_m2") * f_dh;
            let gc = (get("cooling_eui_kwh_m2") - get("cooling_district_eui_kwh_m2")) * f_elec
                + get("cooling_district_eui_kwh_m2") * f_dh;
            let gl = (get("lighting_eui_kwh_m2") - get("lighting_district_eui_kwh_m2")) * f_elec
                + get("lighting_district_eui_kwh_m2") * f_dh;
            let ge = (get("equipment_eui_kwh_m2") - get("equipment_district_eui_kwh_m2")) * f_elec
                + get("equipment_district_eui_kwh_m2") * f_dh;
            let gf = (get("fans_eui_kwh_m2") - get("fans_district_eui_kwh_m2")) * f_elec
                + get("fans_district_eui_kwh_m2") * f_dh;
            let gp = (get("pumps_eui_kwh_m2") - get("pumps_district_eui_kwh_m2")) * f_elec
                + get("pumps_district_eui_kwh_m2") * f_dh;
            let gdhw = get("dhw_gas_eui_kwh_m2") * f_gas
                + get("dhw_elec_eui_kwh_m2") * f_elec
                + get("dhw_district_eui_kwh_m2") * f_dh;
            let gcook = get("cooking_eui_kwh_m2") * f_gas;
            let gref = (get("refrigeration_eui_kwh_m2") - get("refrigeration_district_eui_kwh_m2"))
                * f_elec
                + get("refrigeration_district_eui_kwh_m2") * f_dh;
            let gelev = get("elevators_eui_kwh_m2") * f_elec;
            let gtot = gh
                + gc
                + gl
                + ge
                + gf
                + gp
                + gdhw
                + gcook
                + gref
                + gelev
                + (get("exterior_lighting_eui_kwh_m2")
                    + get("exterior_equipment_eui_kwh_m2")
                    + get("heat_rejection_eui_kwh_m2")
                    + get("humidification_eui_kwh_m2")
                    + get("heat_recovery_eui_kwh_m2")
                    + get("generators_eui_kwh_m2"))
                    * f_dh;
            let vals = [gh, gc, gl, ge, gf, gp, gdhw, gcook, gref, gelev, gtot];
            for (idx, val) in vals.into_iter().enumerate() {
                gwp_builders[idx].append_value(val);
            }
        } else {
            for b in &mut gwp_builders {
                b.append_null();
            }
        }

        abups_b.append_option(row.abups_ok);
        meter_b.append_option(row.meter_ok);
        gas_zero_b.append_option(row.gas_zero);
    }

    let mut fields = vec![
        Field::new("osm_id", DataType::Utf8, false),
        Field::new("parse_status", DataType::Utf8, false),
        Field::new("error_summary", DataType::Utf8, false),
        Field::new("data_quality_flag", DataType::Utf8, false),
        Field::new("floor_area_m2", DataType::Float64, false),
        Field::new("floor_area_provenance", DataType::Utf8, false),
        Field::new("iod", DataType::Float64, true),
    ];
    let mut arrays: Vec<arrow_array::ArrayRef> = vec![
        Arc::new(osm_id_b.finish()),
        Arc::new(status_b.finish()),
        Arc::new(err_b.finish()),
        Arc::new(dq_b.finish()),
        Arc::new(area_b.finish()),
        Arc::new(area_prov_b.finish()),
        Arc::new(iod_b.finish()),
    ];

    for (name, mut b) in eui_cols.into_iter().zip(eui_builders) {
        fields.push(Field::new(name, DataType::Float64, false));
        arrays.push(Arc::new(b.finish()));
    }
    for (name, mut b) in gwp_cols.into_iter().zip(gwp_builders) {
        fields.push(Field::new(name, DataType::Float64, true));
        arrays.push(Arc::new(b.finish()));
    }
    fields.push(Field::new("abups_ok", DataType::Boolean, true));
    fields.push(Field::new("meter_ok", DataType::Boolean, true));
    fields.push(Field::new("gas_zero", DataType::Boolean, true));
    arrays.push(Arc::new(abups_b.finish()));
    arrays.push(Arc::new(meter_b.finish()));
    arrays.push(Arc::new(gas_zero_b.finish()));

    RecordBatch::try_new(Arc::new(Schema::new(fields)), arrays)
        .map_err(|e| ResultsError::ArrowParquet(e.to_string()))
}

/// Atomically stream a `RecordBatch` to Parquet (`SNAPPY` pure-Rust `snap`) via `.tmp` + rename.
pub fn write_record_batch_parquet(batch: &RecordBatch, out_path: &Path) -> Result<(), ResultsError> {
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent).map_err(|e| ResultsError::Io {
            path: parent.display().to_string(),
            reason: e.to_string(),
        })?;
    }
    let tmp_path = out_path.with_extension("parquet.tmp");
    {
        let file = fs::File::create(&tmp_path).map_err(|e| ResultsError::Io {
            path: tmp_path.display().to_string(),
            reason: e.to_string(),
        })?;
        let props = WriterProperties::builder()
            .set_compression(Compression::SNAPPY)
            .build();
        let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(props))
            .map_err(|e| ResultsError::ArrowParquet(e.to_string()))?;
        writer
            .write(batch)
            .map_err(|e| ResultsError::ArrowParquet(e.to_string()))?;
        writer
            .close()
            .map_err(|e| ResultsError::ArrowParquet(e.to_string()))?;
    }
    fs::rename(&tmp_path, out_path).map_err(|e| ResultsError::Io {
        path: out_path.display().to_string(),
        reason: e.to_string(),
    })?;
    Ok(())
}
