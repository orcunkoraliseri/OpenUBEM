//! Typed errors for `openubem-extrude`.

use thiserror::Error;

/// Error raised during footprint snapping, extrusion, or shell closure validation.
#[derive(Debug, Error)]
pub enum ExtrudeError {
    #[error("degenerate polygon for zone '{zone}': {reason}")]
    DegeneratePolygon { zone: String, reason: String },
    #[error("closed-shell volume conservation failed for zone '{zone}': got {actual:.4} vs expected {expected:.4}")]
    VolumeConservation {
        zone: String,
        actual: f64,
        expected: f64,
    },
}
