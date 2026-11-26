//! Error types for `openubem-results`.

use openubem_schema::SchemaError;
use thiserror::Error;

/// Typed errors emitted by SQLite/CSV/EIO/ERR/Parquet result harvesting.
#[derive(Debug, Error)]
pub enum ResultsError {
    /// I2 breach: foreign `osm_id` detected inside building result SQL (aborts entire campaign).
    #[error("I2 breach: foreign osm_id in work dir for {osm_id:?}: {foreign_samples:?} (abort whole run)")]
    I2ForeignOsmId {
        osm_id: String,
        foreign_samples: Vec<String>,
    },

    /// Missing file or unreadable path.
    #[error("file does not exist or cannot be read: {path}: {reason}")]
    Io { path: String, reason: String },

    /// Invalid or fail-closed European/EnergyPlus CSV structure.
    #[error("{0}")]
    InvalidCsv(String),

    /// SQLite query or open error.
    #[error("SQLite error for {path}: {detail}")]
    Sqlite { path: String, detail: String },

    /// Raw rusqlite error.
    #[error("SQLite query failed: {0}")]
    Rusqlite(#[from] rusqlite::Error),

    /// Non-empty orphan `-wal` or `-journal` sidecar detected alongside `eplusout.sql`.
    #[error("incomplete run: non-empty SQLite journal/WAL sidecar at {sidecar}")]
    IncompleteWalOrJournal { sidecar: String },

    /// Schema/unit domain validation failure from `openubem-schema`.
    #[error(transparent)]
    Schema(#[from] SchemaError),

    /// Arrow or Parquet serialization failure.
    #[error("Arrow/Parquet error: {0}")]
    ArrowParquet(String),

    /// JSON metadata parsing error.
    #[error("JSON error: {0}")]
    Json(String),
}
