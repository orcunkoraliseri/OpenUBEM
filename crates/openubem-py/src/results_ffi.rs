//! PyO3 adapters for `openubem-results` (parallel SQLite/CSV/EIO/ERR -> zero-copy `pyarrow.Table`).

use std::collections::HashMap;
use std::path::Path;

use openubem_results::{
    BuildingHarvestSpec, ResultsError, check_building_integrity_sql, count_severe,
    extract_four_end_use_csv, extract_heating_only_csv, first_severe,
    harvest_buildings_to_record_batch, harvest_heating_csv_batch, harvest_one_building_sql,
    has_fatal, iter_severe, parse_eio_file, query_hourly_to_record_batch, resolve_zone,
    write_record_batch_parquet,
};
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyTuple};
use pyo3_arrow::PyTable;

fn map_results_err(err: ResultsError) -> PyErr {
    match err {
        ResultsError::I2ForeignOsmId { .. } => PyRuntimeError::new_err(err.to_string()),
        other => PyValueError::new_err(other.to_string()),
    }
}

#[pyfunction]
pub fn results_resolve_zone(key_value: &str) -> Option<(String, i64, String)> {
    resolve_zone(key_value).map(|z| (z.osm_id_uc, z.floor, z.label))
}

#[pyfunction]
pub fn results_err_iter_severe(text: &str) -> Vec<String> {
    iter_severe(text).into_iter().map(str::to_owned).collect()
}

#[pyfunction]
pub fn results_err_first_severe(text: &str) -> String {
    first_severe(text).to_owned()
}

#[pyfunction]
pub fn results_err_count_severe(text: &str) -> usize {
    count_severe(text)
}

#[pyfunction]
pub fn results_err_has_fatal(text: &str) -> bool {
    has_fatal(text)
}

#[pyfunction]
pub fn results_parse_eio_zone_area(py: Python<'_>, eio_path: String) -> PyResult<Py<PyDict>> {
    let info = py.detach(move || parse_eio_file(Path::new(&eio_path)));
    let dict = PyDict::new(py);
    dict.set_item("n_zones", info.n_zones)?;
    dict.set_item("area_plain_m2", info.area_plain_m2)?;
    dict.set_item("area_multiplier_aware_m2", info.area_multiplier_aware_m2)?;
    dict.set_item("max_zone_multiplier", info.max_zone_multiplier)?;
    dict.set_item("max_zone_list_multiplier", info.max_zone_list_multiplier)?;
    dict.set_item(
        "n_zones_excluded_not_in_total_area",
        info.n_zones_excluded_not_in_total_area,
    )?;
    dict.set_item("parse_status", info.parse_status)?;
    Ok(dict.unbind())
}

#[pyfunction]
pub fn results_parse_eio_zone_multipliers(
    py: Python<'_>,
    eio_path: String,
) -> HashMap<String, f64> {
    let info = py.detach(move || parse_eio_file(Path::new(&eio_path)));
    info.zone_multipliers
}

#[pyfunction]
#[pyo3(signature = (sql_path, mmap_bytes=0))]
pub fn results_check_building_integrity(
    py: Python<'_>,
    sql_path: String,
    mmap_bytes: u64,
) -> PyResult<Py<PyDict>> {
    let integ = py.detach(move || check_building_integrity_sql(Path::new(&sql_path), mmap_bytes));
    let dict = PyDict::new(py);
    dict.set_item("abups_ok", integ.abups_ok)?;
    dict.set_item("meter_ok", integ.meter_ok)?;
    dict.set_item("gas_zero", integ.gas_zero)?;
    Ok(dict.unbind())
}

#[pyfunction]
#[pyo3(signature = (sql_path, mmap_bytes=0))]
pub fn results_parse_building_sql<'py>(
    py: Python<'py>,
    sql_path: String,
    mmap_bytes: u64,
) -> PyResult<Bound<'py, PyAny>> {
    let batch = py
        .detach(move || query_hourly_to_record_batch(Path::new(&sql_path), mmap_bytes))
        .map_err(map_results_err)?;
    let schema = batch.schema();
    let table = PyTable::try_new(vec![batch], schema)?;
    table.into_pyarrow(py)
}

#[pyfunction]
#[pyo3(signature = (
    osm_id,
    sql_path,
    footprint_area_m2,
    num_floors,
    num_zones,
    data_quality_flag="",
    resolution_mode=None,
    summer_lo=6,
    summer_hi=9,
    include_integrity=false,
    mmap_bytes=0
))]
#[allow(clippy::too_many_arguments)]
pub fn results_harvest_one_building(
    py: Python<'_>,
    osm_id: String,
    sql_path: Option<String>,
    footprint_area_m2: f64,
    num_floors: i64,
    num_zones: i64,
    data_quality_flag: &str,
    resolution_mode: Option<String>,
    summer_lo: i64,
    summer_hi: i64,
    include_integrity: bool,
    mmap_bytes: u64,
) -> PyResult<Py<PyDict>> {
    let spec = BuildingHarvestSpec {
        osm_id,
        sql_path,
        footprint_area_m2,
        num_floors,
        num_zones,
        data_quality_flag: data_quality_flag.to_owned(),
        resolution_mode,
    };
    let parsed = py
        .detach(move || {
            harvest_one_building_sql(
                &spec,
                (summer_lo, summer_hi),
                include_integrity,
                mmap_bytes,
            )
        })
        .map_err(map_results_err)?;

    let out = PyDict::new(py);
    out.set_item("osm_id", &parsed.osm_id)?;
    out.set_item("parse_status", &parsed.parse_status)?;
    out.set_item("error_summary", &parsed.error_summary)?;
    out.set_item("data_quality_flag", &parsed.data_quality_flag)?;
    out.set_item("floor_area_m2", parsed.floor_area_m2)?;
    out.set_item("floor_area_provenance", &parsed.floor_area_provenance)?;
    out.set_item("iod", parsed.iod)?;
    if parsed.eui.is_empty() {
        for key in [
            "heating_eui_kwh_m2",
            "cooling_eui_kwh_m2",
            "lighting_eui_kwh_m2",
            "equipment_eui_kwh_m2",
            "fans_eui_kwh_m2",
            "elevators_eui_kwh_m2",
            "total_eui_kwh_m2",
        ] {
            out.set_item(key, f64::NAN)?;
        }
    } else {
        for (k, v) in parsed.eui {
            out.set_item(k, v)?;
        }
    }
    for gwp_key in [
        "gwp_heating_kgco2_m2",
        "gwp_cooling_kgco2_m2",
        "gwp_lighting_kgco2_m2",
        "gwp_equipment_kgco2_m2",
        "gwp_total_kgco2_m2",
    ] {
        out.set_item(gwp_key, py.None())?;
    }
    Ok(out.unbind())
}

fn build_batch_inputs(
    osm_ids: Vec<String>,
    sql_paths: Vec<Option<String>>,
    footprint_areas: Vec<f64>,
    num_floors: Vec<i64>,
    num_zones: Vec<i64>,
    data_quality_flags: Vec<String>,
    resolution_modes: Vec<Option<String>>,
    states: Vec<Option<String>>,
) -> PyResult<(Vec<BuildingHarvestSpec>, HashMap<String, String>)> {
    let n = osm_ids.len();
    if sql_paths.len() != n
        || footprint_areas.len() != n
        || num_floors.len() != n
        || num_zones.len() != n
        || data_quality_flags.len() != n
        || resolution_modes.len() != n
        || states.len() != n
    {
        return Err(PyValueError::new_err("batch input vectors must share identical length"));
    }
    let mut specs = Vec::with_capacity(n);
    let mut state_by_osm = HashMap::with_capacity(n);
    for i in 0..n {
        if let Some(st) = &states[i] {
            state_by_osm.insert(osm_ids[i].clone(), st.clone());
        }
        specs.push(BuildingHarvestSpec {
            osm_id: osm_ids[i].clone(),
            sql_path: sql_paths[i].clone(),
            footprint_area_m2: footprint_areas[i],
            num_floors: num_floors[i],
            num_zones: num_zones[i],
            data_quality_flag: data_quality_flags[i].clone(),
            resolution_mode: resolution_modes[i].clone(),
        });
    }
    Ok((specs, state_by_osm))
}

#[pyfunction]
#[pyo3(signature = (
    osm_ids,
    sql_paths,
    footprint_areas,
    num_floors,
    num_zones,
    data_quality_flags,
    resolution_modes,
    states,
    state_elec_map,
    f_gas,
    f_dh,
    summer_lo=6,
    summer_hi=9,
    include_integrity=false,
    mmap_bytes=0
))]
#[allow(clippy::too_many_arguments)]
pub fn results_harvest_batch_to_arrow<'py>(
    py: Python<'py>,
    osm_ids: Vec<String>,
    sql_paths: Vec<Option<String>>,
    footprint_areas: Vec<f64>,
    num_floors: Vec<i64>,
    num_zones: Vec<i64>,
    data_quality_flags: Vec<String>,
    resolution_modes: Vec<Option<String>>,
    states: Vec<Option<String>>,
    state_elec_map: HashMap<String, f64>,
    f_gas: f64,
    f_dh: f64,
    summer_lo: i64,
    summer_hi: i64,
    include_integrity: bool,
    mmap_bytes: u64,
) -> PyResult<Bound<'py, PyAny>> {
    let (specs, state_by_osm) = build_batch_inputs(
        osm_ids,
        sql_paths,
        footprint_areas,
        num_floors,
        num_zones,
        data_quality_flags,
        resolution_modes,
        states,
    )?;
    let batch = py
        .detach(move || {
            harvest_buildings_to_record_batch(
                &specs,
                &state_elec_map,
                &state_by_osm,
                f_gas,
                f_dh,
                (summer_lo, summer_hi),
                include_integrity,
                mmap_bytes,
            )
        })
        .map_err(map_results_err)?;
    let schema = batch.schema();
    PyTable::try_new(vec![batch], schema)?.into_pyarrow(py)
}

#[pyfunction]
#[pyo3(signature = (
    osm_ids,
    sql_paths,
    footprint_areas,
    num_floors,
    num_zones,
    data_quality_flags,
    resolution_modes,
    states,
    state_elec_map,
    f_gas,
    f_dh,
    out_parquet_path,
    summer_lo=6,
    summer_hi=9,
    include_integrity=false,
    mmap_bytes=0
))]
#[allow(clippy::too_many_arguments)]
pub fn results_harvest_batch_to_parquet(
    py: Python<'_>,
    osm_ids: Vec<String>,
    sql_paths: Vec<Option<String>>,
    footprint_areas: Vec<f64>,
    num_floors: Vec<i64>,
    num_zones: Vec<i64>,
    data_quality_flags: Vec<String>,
    resolution_modes: Vec<Option<String>>,
    states: Vec<Option<String>>,
    state_elec_map: HashMap<String, f64>,
    f_gas: f64,
    f_dh: f64,
    out_parquet_path: String,
    summer_lo: i64,
    summer_hi: i64,
    include_integrity: bool,
    mmap_bytes: u64,
) -> PyResult<()> {
    let (specs, state_by_osm) = build_batch_inputs(
        osm_ids,
        sql_paths,
        footprint_areas,
        num_floors,
        num_zones,
        data_quality_flags,
        resolution_modes,
        states,
    )?;
    py.detach(move || {
        let batch = harvest_buildings_to_record_batch(
            &specs,
            &state_elec_map,
            &state_by_osm,
            f_gas,
            f_dh,
            (summer_lo, summer_hi),
            include_integrity,
            mmap_bytes,
        )?;
        write_record_batch_parquet(&batch, Path::new(&out_parquet_path))
    })
    .map_err(map_results_err)
}

#[pyfunction]
pub fn results_extract_four_end_use_csv(py: Python<'_>, csv_path: String) -> PyResult<Py<PyDict>> {
    let res = py
        .detach(move || extract_four_end_use_csv(Path::new(&csv_path)))
        .map_err(map_results_err)?;

    let out = PyDict::new(py);
    out.set_item("source_csv", res.source_csv)?;

    let eu = PyDict::new(py);
    eu.set_item("heating", res.heating_kwh)?;
    eu.set_item("cooling", res.cooling_kwh)?;
    eu.set_item("lighting", res.lighting_kwh)?;
    eu.set_item("equipment", res.equipment_kwh)?;
    out.set_item("simulated_end_use_kwh", eu)?;

    let monthly_tuple = PyTuple::new(py, res.monthly_kwh.iter().copied())?;
    let hourly_tuple = PyTuple::new(py, res.hourly_kwh.iter().copied())?;
    out.set_item("monthly_simulated_four_end_use_kwh", monthly_tuple)?;
    out.set_item("hourly_simulated_four_end_use_kwh", hourly_tuple)?;
    Ok(out.unbind())
}

#[pyfunction]
pub fn results_extract_heating_only_csv(py: Python<'_>, csv_path: String) -> PyResult<f64> {
    py.detach(move || extract_heating_only_csv(Path::new(&csv_path)))
        .map_err(map_results_err)
}

#[pyfunction]
pub fn results_harvest_heating_csv_batch(
    py: Python<'_>,
    csv_paths: Vec<String>,
) -> PyResult<Vec<f64>> {
    py.detach(move || {
        let refs: Vec<&Path> = csv_paths.iter().map(|s| Path::new(s.as_str())).collect();
        harvest_heating_csv_batch(&refs)
    })
    .map_err(map_results_err)
}
