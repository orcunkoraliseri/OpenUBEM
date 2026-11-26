//! `openubem-results` — parallel SQLite/CSV/EIO/ERR EnergyPlus results harvester.

pub mod csv_reader;
pub mod eio_reader;
pub mod err_reader;
pub mod error;
pub mod harvester;
pub mod sqlite_reader;

pub use csv_reader::{
    FourEndUseCsvResult, NON_LEAP_MONTH_HOURS, NON_LEAP_YEAR_HOURS, extract_four_end_use_csv,
    extract_heating_only_csv, harvest_four_end_use_csv_batch, harvest_heating_csv_batch,
};
pub use eio_reader::{EioZoneInfo, parse_eio_file};
pub use err_reader::{count_severe, first_severe, has_fatal, is_fatal_line, is_severe_line, iter_severe};
pub use error::ResultsError;
pub use harvester::{harvest_buildings_to_record_batch, write_record_batch_parquet};
pub use sqlite_reader::{
    BuildingHarvestSpec, BuildingIntegrity, ParsedBuildingMetrics, ResolvedZone,
    check_building_integrity_sql, find_nonempty_sqlite_sidecar, harvest_one_building_sql,
    open_sqlite_readonly, query_hourly_rows, query_hourly_to_record_batch, resolve_zone,
    strip_ideal_loads_suffix,
};
