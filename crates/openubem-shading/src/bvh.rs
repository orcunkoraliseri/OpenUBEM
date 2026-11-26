//! District-local `obvhs` CWBVH8 builder with `f64` centroid shift and conservative `1e-4` m padding.

use std::time::Duration;

use glam::Vec3A;
use obvhs::aabb::Aabb;
use obvhs::cwbvh::CwBvh;
use obvhs::cwbvh::builder::build_cwbvh;
use obvhs::ray::Ray;
use obvhs::{Boundable, BvhBuildParams};

use crate::watertight::{LocalTriangle, WatertightRayF64};

const AABB_PAD_M: f32 = 1.0e-3;

struct TriBounds(Aabb);

impl Boundable for TriBounds {
    #[inline]
    fn aabb(&self) -> Aabb {
        self.0
    }
}

/// BVH acceleration structure paired with `f64` centroid-shifted triangles in direct BVH order.
pub struct DistrictShadingBvh {
    pub origin_offset: [f64; 3],
    pub cwbvh: CwBvh,
    pub tris: Vec<LocalTriangle>,
}

impl DistrictShadingBvh {
    /// Shift global/UTM `f64` vertices to local centroid coordinates and construct CWBVH8.
    pub fn build(global_tris: &[[[f64; 3]; 3]]) -> Self {
        if global_tris.is_empty() {
            let empty_bounds: Vec<TriBounds> = Vec::new();
            let mut build_dur = Duration::ZERO;
            let cwbvh = build_cwbvh(&empty_bounds, BvhBuildParams::fastest_build(), &mut build_dur);
            return Self {
                origin_offset: [0.0, 0.0, 0.0],
                cwbvh,
                tris: Vec::new(),
            };
        }

        // Compute district centroid in f64 before casting AABBs to f32 (eliminates UTM 0.25m ULP drift).
        let mut min_xyz = [f64::INFINITY; 3];
        let mut max_xyz = [f64::NEG_INFINITY; 3];
        for tri in global_tris {
            for v in tri {
                for axis in 0..3 {
                    min_xyz[axis] = min_xyz[axis].min(v[axis]);
                    max_xyz[axis] = max_xyz[axis].max(v[axis]);
                }
            }
        }
        let origin_offset = [
            0.5 * (min_xyz[0] + max_xyz[0]),
            0.5 * (min_xyz[1] + max_xyz[1]),
            0.5 * (min_xyz[2] + max_xyz[2]),
        ];

        let pad = Vec3A::splat(AABB_PAD_M);
        let mut shifted_tris = Vec::with_capacity(global_tris.len());
        let mut bounds = Vec::with_capacity(global_tris.len());

        for tri in global_tris {
            let shift = |p: [f64; 3]| -> [f64; 3] {
                [
                    p[0] - origin_offset[0],
                    p[1] - origin_offset[1],
                    p[2] - origin_offset[2],
                ]
            };
            let v0 = shift(tri[0]);
            let v1 = shift(tri[1]);
            let v2 = shift(tri[2]);
            shifted_tris.push(LocalTriangle { v0, v1, v2 });

            let f0 = Vec3A::new(v0[0] as f32, v0[1] as f32, v0[2] as f32);
            let f1 = Vec3A::new(v1[0] as f32, v1[1] as f32, v1[2] as f32);
            let f2 = Vec3A::new(v2[0] as f32, v2[1] as f32, v2[2] as f32);
            let mut aabb = Aabb::from_points(&[f0, f1, f2]);
            aabb.min -= pad;
            aabb.max += pad;
            bounds.push(TriBounds(aabb));
        }

        let mut build_time = Duration::ZERO;
        let cwbvh = build_cwbvh(&bounds, BvhBuildParams::fastest_build(), &mut build_time);

        // Reorder triangles into direct CWBVH primitive order to eliminate leaf indirection.
        let ordered_tris: Vec<LocalTriangle> = cwbvh
            .primitive_indices
            .iter()
            .map(|&idx| shifted_tris[idx as usize])
            .collect();

        Self {
            origin_offset,
            cwbvh,
            tris: ordered_tris,
        }
    }

    /// Return true iff ray segment `(t_eps, +inf)` hits at least one occluder triangle.
    #[inline]
    pub fn is_occluded(&self, global_origin: [f64; 3], dir: [f64; 3], t_eps: f64) -> bool {
        if self.tris.is_empty() {
            return false;
        }
        let local_orig = [
            global_origin[0] - self.origin_offset[0],
            global_origin[1] - self.origin_offset[1],
            global_origin[2] - self.origin_offset[2],
        ];
        let Some(w_ray) = WatertightRayF64::new(local_orig, dir) else {
            return false;
        };
        let ray = Ray::new(
            Vec3A::new(local_orig[0] as f32, local_orig[1] as f32, local_orig[2] as f32),
            Vec3A::new(dir[0] as f32, dir[1] as f32, dir[2] as f32),
            t_eps as f32,
            f32::INFINITY,
        );
        let tris = &self.tris;
        let missed = self
            .cwbvh
            .ray_traverse_miss(ray, |_r, prim_idx| w_ray.intersect_tri(&tris[prim_idx], t_eps));
        !missed
    }
}
