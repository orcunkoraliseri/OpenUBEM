//! Generic floating-point trait (`f64` reference & `f32` GPU twin) per `D-RS-05` Option A.

use num_traits::Float;

/// Scalar floating-point abstraction supporting both `f64` (CPU reference) and `f32` (GPU twin).
pub trait SimFloat: Float + Copy + Send + Sync + std::fmt::Debug + 'static {
    /// Convert literal `f64` constant cleanly to `Self`.
    fn lit(v: f64) -> Self;
    /// Convert `Self` back to `f64` for output reduction.
    fn to_f64_lossless(self) -> f64;
}

impl SimFloat for f64 {
    #[inline(always)]
    fn lit(v: f64) -> Self {
        v
    }

    #[inline(always)]
    fn to_f64_lossless(self) -> f64 {
        self
    }
}

impl SimFloat for f32 {
    #[inline(always)]
    fn lit(v: f64) -> Self {
        v as f32
    }

    #[inline(always)]
    fn to_f64_lossless(self) -> f64 {
        self as f64
    }
}
