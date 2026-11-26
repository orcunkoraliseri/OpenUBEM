//! Watertight Woop, Benthin & Wald (2013) ray-triangle intersection in `f64` with shifted local coordinates.

/// Precomputed double-precision triangle in shifted district-local coordinates.
#[derive(Debug, Clone, Copy)]
pub struct LocalTriangle {
    pub v0: [f64; 3],
    pub v1: [f64; 3],
    pub v2: [f64; 3],
}

/// Precomputed ray transform parameters for Woop/Benthin/Wald (2013) watertight intersection.
#[derive(Debug, Clone, Copy)]
pub struct WatertightRayF64 {
    pub origin: [f64; 3],
    pub kx: usize,
    pub ky: usize,
    pub kz: usize,
    pub sx: f64,
    pub sy: f64,
    pub sz: f64,
}

impl WatertightRayF64 {
    /// Prepare Woop (2013) permutation + shear constants once per ray before BVH traversal.
    #[inline]
    pub fn new(origin: [f64; 3], dir: [f64; 3]) -> Option<Self> {
        let ax = dir[0].abs();
        let ay = dir[1].abs();
        let az = dir[2].abs();
        let kz = if ax > ay && ax > az {
            0
        } else if ay > az {
            1
        } else {
            2
        };
        let denom = dir[kz];
        if denom.abs() <= 1.0e-12 {
            return None;
        }
        let mut kx = kz + 1;
        if kx == 3 {
            kx = 0;
        }
        let mut ky = kx + 1;
        if ky == 3 {
            ky = 0;
        }
        // Swap kx and ky if dir[kz] < 0 to preserve winding sign across permutation.
        if denom < 0.0 {
            std::mem::swap(&mut kx, &mut ky);
        }
        let sz = 1.0 / denom;
        let sx = dir[kx] * sz;
        let sy = dir[ky] * sz;
        Some(Self {
            origin,
            kx,
            ky,
            kz,
            sx,
            sy,
            sz,
        })
    }

    /// Watertight ray-triangle intersection returning hit distance `t` if `t > t_eps`, else `f32::INFINITY`.
    #[inline]
    pub fn intersect_tri(&self, tri: &LocalTriangle, t_eps: f64) -> f32 {
        let a = [
            tri.v0[0] - self.origin[0],
            tri.v0[1] - self.origin[1],
            tri.v0[2] - self.origin[2],
        ];
        let b = [
            tri.v1[0] - self.origin[0],
            tri.v1[1] - self.origin[1],
            tri.v1[2] - self.origin[2],
        ];
        let c = [
            tri.v2[0] - self.origin[0],
            tri.v2[1] - self.origin[1],
            tri.v2[2] - self.origin[2],
        ];

        let ax = a[self.kx] - self.sx * a[self.kz];
        let ay = a[self.ky] - self.sy * a[self.kz];
        let bx = b[self.kx] - self.sx * b[self.kz];
        let by = b[self.ky] - self.sy * b[self.kz];
        let cx = c[self.kx] - self.sx * c[self.kz];
        let cy = c[self.ky] - self.sy * c[self.kz];

        // Scaled 2D Plücker edge coordinates (invariant under vertex cyclic permutation / shared edges).
        let u = cx * by - cy * bx;
        let v = ax * cy - ay * cx;
        let w = bx * ay - by * ax;

        let det = u + v + w;
        if det.abs() <= 1.0e-18 {
            return f32::INFINITY;
        }
        // Match Python Möller-Trumbore normalized barycentric edge tolerance (-1e-5 .. 1 + 1e-5)
        // in shifted f64 precision so shared-edge hits agree across Python and Rust.
        let inv_det = 1.0 / det;
        let b1 = v * inv_det;
        let b2 = w * inv_det;
        if b1 < -1.0e-5 || b1 > 1.0 + 1.0e-5 || b2 < -1.0e-5 || (b1 + b2) > 1.0 + 1.0e-5 {
            return f32::INFINITY;
        }

        let az = self.sz * a[self.kz];
        let bz = self.sz * b[self.kz];
        let cz = self.sz * c[self.kz];
        let t_scaled = u * az + v * bz + w * cz;

        let t = t_scaled * inv_det;
        if t > t_eps {
            t as f32
        } else {
            f32::INFINITY
        }
    }
}
