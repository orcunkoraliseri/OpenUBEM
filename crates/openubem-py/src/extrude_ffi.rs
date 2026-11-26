//! PyO3 FFI bindings for `openubem-extrude`.

use openubem_extrude::{
    BoundaryKind, SurfaceKind, ZoneSpecInput, extrude_and_match_zones, newell_normal_and_area,
    snap_zones_globally,
};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

type ZoneTupleInput = (String, Vec<[f64; 2]>, Vec<Vec<[f64; 2]>>, f64, f64, bool);
type SurfaceTupleOutput = (String, String, String, String, String, bool, bool, Vec<[f64; 3]>);

fn kind_str(k: SurfaceKind) -> String {
    match k {
        SurfaceKind::Wall => "Wall".to_string(),
        SurfaceKind::Floor => "Floor".to_string(),
        SurfaceKind::Ceiling => "Ceiling".to_string(),
        SurfaceKind::Roof => "Roof".to_string(),
    }
}

fn bc_str(b: BoundaryKind) -> String {
    match b {
        BoundaryKind::Ground => "Ground".to_string(),
        BoundaryKind::Outdoors => "Outdoors".to_string(),
        BoundaryKind::Surface => "Surface".to_string(),
        BoundaryKind::Adiabatic => "Adiabatic".to_string(),
    }
}

/// Extrude multi-zone/holed footprints and compute strictly reciprocal interzone matches.
#[pyfunction]
pub fn extrude_and_match(
    py: Python<'_>,
    zones: Vec<ZoneTupleInput>,
    grid_m: f64,
    min_edge_m: f64,
    match_tol_m: f64,
) -> PyResult<Vec<SurfaceTupleOutput>> {
    let inputs: Vec<ZoneSpecInput> = zones
        .into_iter()
        .map(
            |(name, outer_ring, hole_rings, z_floor, z_ceiling, is_top_storey)| ZoneSpecInput {
                name,
                outer_ring,
                hole_rings,
                z_floor,
                z_ceiling,
                is_top_storey,
            },
        )
        .collect();
    let out = py
        .detach(move || extrude_and_match_zones(&inputs, grid_m, min_edge_m, match_tol_m))
        .map_err(|e| PyValueError::new_err(e.to_string()))?;

    Ok(out
        .into_iter()
        .map(|s| {
            (
                s.name,
                s.zone_name,
                kind_str(s.kind),
                bc_str(s.boundary),
                s.boundary_object,
                s.sun_exposed,
                s.wind_exposed,
                s.vertices,
            )
        })
        .collect())
}

/// Snap 2D footprint rings to an integer `i64` quantized grid and remove collinear vertices.
#[pyfunction]
pub fn extrude_snap_rings(
    py: Python<'_>,
    mut rings: Vec<Vec<[f64; 2]>>,
    grid_m: f64,
    min_edge_m: f64,
) -> Vec<Vec<[f64; 2]>> {
    py.detach(move || {
        snap_zones_globally(&mut rings, grid_m, min_edge_m);
        rings
    })
}

/// Compute 3D Newell `(unit_normal, area_m2)` for an ordered polygon ring.
#[pyfunction]
pub fn extrude_newell_normal_and_area(
    py: Python<'_>,
    verts: Vec<[f64; 3]>,
) -> ([f64; 3], f64) {
    py.detach(move || newell_normal_and_area(&verts))
}
