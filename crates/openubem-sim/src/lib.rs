//! `openubem-sim` — pure-Rust `SimFloat` (`f64`/`f32`) Stage-A thermal solver & conformance hash.

pub mod float_trait;
pub mod physics;
pub mod solver;

pub use float_trait::SimFloat;
pub use solver::{
    BuildingStageAInput, BuildingStageAOutput, run_stage_a_batch_f32, run_stage_a_batch_f64,
    simulate_building_stage_a,
};

/// Return the compile-time FIPS 180-4 SHA-256 conformance hash of the Rust kernel sources.
pub const fn kernel_conformance_hash() -> &'static str {
    env!("OPENUBEM_SIM_KERNEL_SHA256")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn conformance_hash_is_64_hex_chars() {
        let h = kernel_conformance_hash();
        assert_eq!(h.len(), 64);
        assert!(h.bytes().all(|b| b.is_ascii_hexdigit()));
    }
}
