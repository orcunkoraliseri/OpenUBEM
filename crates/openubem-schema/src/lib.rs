//! `openubem-schema` — pure-Rust physical units, provenance, quality flags, and Arrow schema validation.

pub mod adt;
pub mod arrow_validate;
pub mod error;
pub mod flags;
pub mod provenance;
pub mod units;

pub use adt::{
    AbupsDistrictRow, AbupsSlot, EndUse, EndUseLedger, EngineProvenance, FloorAreaProvenance,
    FuelSplitKwh, PureDistrictEndUse, RawMeters, ReconciledLedger, ResolvedFloorArea,
    SimulationStatus,
};
pub use arrow_validate::{
    STEP1_SCHEMA_COLUMNS, STEP4_MANIFEST_COLUMNS, build_step1_quality_flags,
    extract_string_refs, score_provenance_batch, validate_sim_manifest_batch,
    validate_step1_batch,
};
pub use error::SchemaError;
pub use flags::{
    FlagDelimiterMode, QualityFlag, QualityFlagSet, append_flag_token_delimited,
    merge_flag_strings,
};
pub use provenance::{
    ConfidenceTier, LegacyProvenance, ProvenanceLineage, impute_token, parse_token,
    score_provenance_cell, score_provenance_matrix,
};
pub use units::{
    AreaM2, ConfidenceWeight, EnergyJ, EnergyKwh, EuiKwhM2, FloorCount, GJ_TO_KWH, GwpKgCo2M2,
    HeightM, J_TO_KWH, PositiveAreaM2, TempCelsius, TempKelvin, UValueWm2K,
};
