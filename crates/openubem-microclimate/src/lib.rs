//! `openubem-microclimate` — clean-room Rust tiled SVF, canopy transmission, & 210-term UTCI.

pub mod shadow;
pub mod svf;
pub mod utci;

pub use shadow::{building_shadow_from_horizon, vegetation_transmission};
pub use svf::{SvfResult, compute_svf};
pub use utci::{classify_stress_batch, utci_approx_batch};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn analytic_flat_ground_svf_is_unity() {
        let dsm = vec![0.0; 25 * 25];
        let dem = vec![0.0; 25 * 25];
        let res = compute_svf(&dsm, &dem, 25, 25, 2.0, 1.1, 32, 12);
        assert!((res.svf[12 * 25 + 12] - 1.0).abs() < 1e-6);
    }

    #[test]
    fn utci_reference_point_matches_cost_730() {
        let (u, f) = utci_approx_batch(&[25.0], &[45.0], &[3.0], &[1.5]);
        assert_eq!(f[0], 0);
        // Official UTCI_a002 for Ta=25, Tmrt=45, va10=3.0, e=1.5kPa -> ~27.57667 C (class 6)
        assert!((u[0] - 27.576670146900057).abs() < 1e-12, "utci={}", u[0]);
        assert_eq!(classify_stress_batch(&u), vec![6]);
    }
}
