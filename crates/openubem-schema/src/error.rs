//! Error types for `openubem-schema`.

use thiserror::Error;

/// Typed errors produced by physical unit, provenance, quality-flag, and Arrow schema checks.
#[derive(Debug, Error)]
pub enum SchemaError {
    /// Raised when a denominator area is non-finite or not strictly positive.
    #[error("non-positive floor area: {0}")]
    NonPositiveFloorArea(f64),

    /// Raised when a meter or energy quantity is negative or non-finite.
    #[error("negative or non-finite meter value for {field}: {value}")]
    InvalidEnergyValue { field: String, value: f64 },

    /// Raised when an emission factor or GWP parameter is invalid.
    #[error("invalid carbon factor for {fuel}: {value}")]
    InvalidCarbonFactor { fuel: String, value: f64 },

    /// Raised when an unknown token is passed to strict `QualityFlagSet::parse_strict`.
    #[error("unregistered data_quality_flag token: {0}")]
    UnknownFlagToken(String),

    /// Raised when a confidence tier token cannot be normalized.
    #[error("confidence must be one of HIGH, MEDIUM, MED, LOW; got {0:?}")]
    InvalidConfidenceTier(String),

    /// Raised when a provenance token fails grammar checks.
    #[error("invalid provenance token: {0:?}")]
    InvalidProvenanceToken(String),

    /// Raised when an unknown simulation status token is encountered.
    #[error("invalid simulation_status token: {0:?}")]
    InvalidSimulationStatus(String),

    /// Raised when a schema check finds wrong column count.
    #[error("Schema error: expected {expected} columns, got {actual}")]
    ColumnCountMismatch { expected: usize, actual: usize },

    /// Raised when schema column names or ordering do not match.
    #[error("Schema error: column order mismatch: {detail}")]
    ColumnOrderMismatch { detail: String },

    /// Raised when an Arrow column has an unexpected data type.
    #[error("Schema error: column {column:?} has invalid Arrow dtype: {detail}")]
    ColumnTypeMismatch { column: String, detail: String },

    /// Raised when a required key column contains duplicates or nulls.
    #[error("Schema error: '{column}' column violates uniqueness or non-null invariant: {detail}")]
    KeyViolation { column: String, detail: String },

    /// Raised when row-level domain invariants (e.g., footprint >= 20 m2) fail.
    #[error("Schema error: row {row_index} fails domain check on {column:?}: {detail}")]
    DomainConstraintViolation {
        row_index: usize,
        column: String,
        detail: String,
    },
}
