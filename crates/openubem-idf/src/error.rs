//! Typed errors for `openubem-idf`.

use thiserror::Error;

/// Error returned by IDF parsing, schedule loading, CTF, or view-factor kernels.
#[derive(Debug, Error)]
pub enum IdfError {
    /// Invalid input shape or empty layer list.
    #[error("invalid IDF/kernel input: {0}")]
    InvalidInput(String),
    /// Missing schedule entries or malformed numeric token.
    #[error("schedule parse error: {0}")]
    ScheduleError(String),
    /// CTF conservation or eigenvalue failure.
    #[error("modal conduction check failed: {0}")]
    CtfError(String),
    /// Linear solve failure in view-factor / ScriptF computation.
    #[error("linear algebra solve failed: {0}")]
    LinalgError(String),
    /// Filesystem read error.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}
