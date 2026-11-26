//! `openubem-extrude` — pure-Rust 3D zone extrusion & reciprocal interzone matcher (zero `geos`).

pub mod error;
pub mod extrude;
pub mod match_surfaces;
pub mod snap;

pub use error::ExtrudeError;
pub use extrude::{
    BoundaryKind, ExtrudedSurface, SurfaceKind, ZoneSpecInput, extrude_zone_shell,
    newell_normal_and_area, polygon_overlap_area_m2, shell_signed_volume,
};
pub use match_surfaces::match_and_split_interzone_surfaces;
pub use snap::{clean_ring_2d, ensure_ccw, quantize_pt, signed_area_2d, snap_zones_globally};

/// Full multi-zone extrusion + reciprocal interzone surface matching pipeline.
pub fn extrude_and_match_zones(
    zones: &[ZoneSpecInput],
    grid_m: f64,
    min_edge_m: f64,
    match_tol_m: f64,
) -> Result<Vec<ExtrudedSurface>, ExtrudeError> {
    let mut all_surfs = Vec::new();
    for z in zones {
        all_surfs.extend(extrude_zone_shell(z, grid_m, min_edge_m)?);
    }
    match_and_split_interzone_surfaces(&mut all_surfs, match_tol_m);
    Ok(all_surfs)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adjacent_dwellings_produce_strictly_reciprocal_party_wall() {
        let za = ZoneSpecInput {
            name: "ZoneA".into(),
            outer_ring: vec![[0.0, 0.0], [6.0, 0.0], [6.0, 8.0], [0.0, 8.0]],
            hole_rings: vec![],
            z_floor: 0.0,
            z_ceiling: 3.0,
            is_top_storey: true,
        };
        let zb = ZoneSpecInput {
            name: "ZoneB".into(),
            outer_ring: vec![[6.0, 0.0], [12.0, 0.0], [12.0, 8.0], [6.0, 8.0]],
            hole_rings: vec![],
            z_floor: 0.0,
            z_ceiling: 3.0,
            is_top_storey: true,
        };
        let surfs = extrude_and_match_zones(&[za, zb], 0.001, 0.001, 0.002).expect("valid shell");
        let party: Vec<&ExtrudedSurface> = surfs
            .iter()
            .filter(|s| s.boundary == BoundaryKind::Surface)
            .collect();
        assert_eq!(party.len(), 2);
        assert_eq!(party[0].boundary_object, party[1].name);
        assert_eq!(party[1].boundary_object, party[0].name);
        assert_eq!(party[0].vertices.len(), party[1].vertices.len());
    }

    #[test]
    fn courtyard_holed_zone_conserves_closed_shell_volume() {
        let courtyard = ZoneSpecInput {
            name: "CourtyardZone".into(),
            outer_ring: vec![[0.0, 0.0], [20.0, 0.0], [20.0, 20.0], [0.0, 20.0]],
            hole_rings: vec![vec![[6.0, 6.0], [14.0, 6.0], [14.0, 14.0], [6.0, 14.0]]],
            z_floor: 0.0,
            z_ceiling: 3.0,
            is_top_storey: true,
        };
        let surfs = extrude_and_match_zones(&[courtyard], 0.001, 0.001, 0.002).expect("closed shell");
        let vol = shell_signed_volume(&surfs);
        // Expected area = 400 - 64 = 336 m2 * 3 m = 1008 m3
        assert!((vol - 1008.0).abs() < 1e-3, "courtyard shell volume={vol}");
    }
}
