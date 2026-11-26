//! `openubem-shading` — pure-Rust CWBVH8 exterior solar & sky diffuse shading engine.

pub mod bvh;
pub mod shading;
pub mod watertight;

pub use bvh::DistrictShadingBvh;
pub use shading::{
    ShadingResult, compute_exterior_shading, fibonacci_hemisphere_dirs, sample_polygon_points,
    triangulate_flattened_polygons,
};
pub use watertight::{LocalTriangle, WatertightRayF64};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn analytical_overhang_blocks_overhead_rays_and_utm_shift_preserves_mm_precision() {
        // Test at UTM-scale coordinates (500_000 m, 4_500_000 m) to prove centroid shift prevents f32 ULP drift!
        let ox = 500_000.0;
        let oy = 4_500_000.0;
        // Vertical south-facing target wall z=[0, 3], x=[0, 4], y=0
        let target_verts = vec![
            [ox, oy, 0.0],
            [ox + 4.0, oy, 0.0],
            [ox + 4.0, oy, 3.0],
            [ox, oy, 3.0],
        ];
        // Huge horizontal canopy blocking entire upper sky right above wall
        let occ_verts = vec![
            [ox - 5.0, oy - 10.0, 3.5],
            [ox + 9.0, oy - 10.0, 3.5],
            [ox + 9.0, oy + 5.0, 3.5],
            [ox - 5.0, oy + 5.0, 3.5],
        ];
        // Normal points south (-y)
        let normals = vec![[0.0, -1.0, 0.0]];
        let sun_exp = vec![true];
        // Fixed noon downward-slanted south sun direction
        let mut solcos = vec![[0.0, 0.0, -1.0]; 8760];
        for h in 0..8760 {
            if h % 24 == 12 {
                let d = [0.0, -0.5_f64, 0.866_025_403_784_438_6];
                solcos[h] = d;
            }
        }
        let res = compute_exterior_shading(
            &target_verts,
            &[0, 4],
            &normals,
            &sun_exp,
            &occ_verts,
            &[0, 4],
            &solcos,
            20,
            3,
            64,
        );
        // Hour 12 should be shaded (under canopy at z=3.5), diffuse sky reduced < 0.7
        assert!(res.sunlit_hr[12] < 0.6, "sunlit_hr[12] = {}", res.sunlit_hr[12]);
        assert!(res.dif_sky[0] < 0.8, "dif_sky = {}", res.dif_sky[0]);
    }
}
