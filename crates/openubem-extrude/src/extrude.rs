//! Closed-shell 3D building extrusion with EnergyPlus outward-normal & divergence checks.

use geo::{Area, BooleanOps, Coord, LineString, Polygon, TriangulateEarcut};

use crate::error::ExtrudeError;
use crate::snap::{clean_ring_2d, ensure_ccw, signed_area_2d};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SurfaceKind {
    Wall,
    Floor,
    Ceiling,
    Roof,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BoundaryKind {
    Ground,
    Outdoors,
    Surface,
    Adiabatic,
}

/// Input specification for one thermal zone polygon.
#[derive(Debug, Clone)]
pub struct ZoneSpecInput {
    pub name: String,
    pub outer_ring: Vec<[f64; 2]>,
    pub hole_rings: Vec<Vec<[f64; 2]>>,
    pub z_floor: f64,
    pub z_ceiling: f64,
    pub is_top_storey: bool,
}

/// One generated EnergyPlus `BuildingSurface:Detailed` candidate.
#[derive(Debug, Clone)]
pub struct ExtrudedSurface {
    pub name: String,
    pub zone_name: String,
    pub kind: SurfaceKind,
    pub boundary: BoundaryKind,
    pub boundary_object: String,
    pub sun_exposed: bool,
    pub wind_exposed: bool,
    pub vertices: Vec<[f64; 3]>,
}

/// Compute 3D Newell polygon `(outward_unit_normal, area_m2)`.
pub fn newell_normal_and_area(verts: &[[f64; 3]]) -> ([f64; 3], f64) {
    let n = verts.len();
    if n < 3 {
        return ([0.0, 0.0, 1.0], 0.0);
    }
    let mut nx = 0.0_f64;
    let mut ny = 0.0_f64;
    let mut nz = 0.0_f64;
    for i in 0..n {
        let a = verts[i];
        let b = verts[(i + 1) % n];
        nx += (a[1] - b[1]) * (a[2] + b[2]);
        ny += (a[2] - b[2]) * (a[0] + b[0]);
        nz += (a[0] - b[0]) * (a[1] + b[1]);
    }
    let norm = (nx * nx + ny * ny + nz * nz).sqrt();
    if norm <= 1.0e-12 {
        return ([0.0, 0.0, 1.0], 0.0);
    }
    ([nx / norm, ny / norm, nz / norm], 0.5 * norm)
}

/// Divergence-theorem closed-shell volume check over all zone surfaces.
pub fn shell_signed_volume(surfaces: &[ExtrudedSurface]) -> f64 {
    let mut vol6 = 0.0_f64;
    for s in surfaces {
        if s.vertices.len() < 3 {
            continue;
        }
        let v0 = s.vertices[0];
        for i in 1..(s.vertices.len() - 1) {
            let v1 = s.vertices[i];
            let v2 = s.vertices[i + 1];
            // det([v0, v1, v2]) = v0 . (v1 x v2)
            let cx = v1[1] * v2[2] - v1[2] * v2[1];
            let cy = v1[2] * v2[0] - v1[0] * v2[2];
            let cz = v1[0] * v2[1] - v1[1] * v2[0];
            vol6 += v0[0] * cx + v0[1] * cy + v0[2] * cz;
        }
    }
    vol6 / 6.0
}

fn to_geo_polygon(outer: &[[f64; 2]], holes: &[Vec<[f64; 2]>]) -> Polygon<f64> {
    let mut ext: Vec<Coord<f64>> = outer.iter().map(|&p| Coord { x: p[0], y: p[1] }).collect();
    if let Some(&first) = ext.first() {
        ext.push(first);
    }
    let interiors: Vec<LineString<f64>> = holes
        .iter()
        .filter(|h| h.len() >= 3)
        .map(|h| {
            let mut hc: Vec<Coord<f64>> = h.iter().map(|&p| Coord { x: p[0], y: p[1] }).collect();
            if let Some(&first) = hc.first() {
                hc.push(first);
            }
            LineString::new(hc)
        })
        .collect();
    Polygon::new(LineString::new(ext), interiors)
}

/// Decompose a possibly-holed polygon into convex/simple EnergyPlus-safe horizontal patches.
fn decompose_horizontal_patches(
    outer: &[[f64; 2]],
    holes: &[Vec<[f64; 2]>],
) -> Vec<Vec<[f64; 2]>> {
    if holes.is_empty() {
        return vec![outer.to_vec()];
    }
    // Pure-Rust earcut triangulation avoids EnergyPlus holed-polygon fatal errors on courtyards.
    let poly = to_geo_polygon(outer, holes);
    let tris = poly.earcut_triangles_raw();
    let mut patches = Vec::with_capacity(tris.triangle_indices.len() / 3);
    for tri in tris.triangle_indices.chunks_exact(3) {
        let p0 = tris.vertices[tri[0]];
        let p1 = tris.vertices[tri[1]];
        let p2 = tris.vertices[tri[2]];
        let mut ring = vec![p0, p1, p2];
        if signed_area_2d(&ring).abs() > 1.0e-4 {
            ensure_ccw(&mut ring);
            patches.push(ring);
        }
    }
    patches
}

/// Extrude a closed building shell with quantized snapping and EnergyPlus normal conventions.
pub fn extrude_zone_shell(
    spec: &ZoneSpecInput,
    grid_m: f64,
    min_edge_m: f64,
) -> Result<Vec<ExtrudedSurface>, ExtrudeError> {
    let mut outer = clean_ring_2d(&spec.outer_ring, grid_m, min_edge_m);
    ensure_ccw(&mut outer);
    let area = signed_area_2d(&outer);
    if outer.len() < 3 || area < 1.0e-3 {
        return Err(ExtrudeError::DegeneratePolygon {
            zone: spec.name.clone(),
            reason: format!("outer ring len={} area={area:.6}", outer.len()),
        });
    }
    let height = spec.z_ceiling - spec.z_floor;
    if height <= 1.0e-3 {
        return Err(ExtrudeError::DegeneratePolygon {
            zone: spec.name.clone(),
            reason: format!("non-positive height {height:.6}"),
        });
    }

    let mut clean_holes = Vec::new();
    let mut holes_area = 0.0_f64;
    for h in &spec.hole_rings {
        let mut ch = clean_ring_2d(h, grid_m, min_edge_m);
        let ha = signed_area_2d(&ch).abs();
        if ch.len() >= 3 && ha >= 0.05 {
            // Courtyard wall inner loop: reverse to CW so outward wall normals point INTO the void!
            if signed_area_2d(&ch) > 0.0 {
                ch.reverse();
            }
            holes_area += ha;
            clean_holes.push(ch);
        }
    }
    let net_fp_area = (area - holes_area).max(1.0e-3);

    let mut out = Vec::new();
    let patches = decompose_horizontal_patches(&outer, &clean_holes);

    // 1. Floors (normal -Z => CW winding seen from +Z)
    let is_ground = spec.z_floor.abs() < 1.0e-4;
    for (pidx, patch) in patches.iter().enumerate() {
        let mut verts: Vec<[f64; 3]> = patch
            .iter()
            .rev()
            .map(|&[x, y]| [x, y, spec.z_floor])
            .collect();
        let (nrm, a) = newell_normal_and_area(&verts);
        if nrm[2] > 0.0 {
            verts.reverse();
        }
        if a >= 1.0e-4 {
            out.push(ExtrudedSurface {
                name: format!("{}_Floor_{pidx}", spec.name),
                zone_name: spec.name.clone(),
                kind: SurfaceKind::Floor,
                boundary: if is_ground {
                    BoundaryKind::Ground
                } else {
                    BoundaryKind::Outdoors
                },
                boundary_object: String::new(),
                sun_exposed: !is_ground,
                wind_exposed: !is_ground,
                vertices: verts,
            });
        }
    }

    // 2. Ceiling / Roof (normal +Z => CCW winding seen from +Z)
    let top_kind = if spec.is_top_storey {
        SurfaceKind::Roof
    } else {
        SurfaceKind::Ceiling
    };
    for (pidx, patch) in patches.iter().enumerate() {
        let mut verts: Vec<[f64; 3]> = patch
            .iter()
            .map(|&[x, y]| [x, y, spec.z_ceiling])
            .collect();
        let (nrm, a) = newell_normal_and_area(&verts);
        if nrm[2] < 0.0 {
            verts.reverse();
        }
        if a >= 1.0e-4 {
            out.push(ExtrudedSurface {
                name: format!("{}_{}_{pidx}", spec.name, if spec.is_top_storey { "Roof" } else { "Ceiling" }),
                zone_name: spec.name.clone(),
                kind: top_kind,
                boundary: BoundaryKind::Outdoors,
                boundary_object: String::new(),
                sun_exposed: spec.is_top_storey,
                wind_exposed: spec.is_top_storey,
                vertices: verts,
            });
        }
    }

    // 3. Outer + courtyard walls (UL -> LL -> LR -> UR = CCW from outside => outward normal)
    let mut all_rings = Vec::with_capacity(1 + clean_holes.len());
    all_rings.push((false, outer));
    for h in clean_holes {
        all_rings.push((true, h));
    }
    let mut wall_idx = 0usize;
    for (_is_hole, ring) in all_rings {
        let nr = ring.len();
        for i in 0..nr {
            let p0 = ring[i];
            let p1 = ring[(i + 1) % nr];
            if (p1[0] - p0[0]).hypot(p1[1] - p0[1]) < min_edge_m {
                continue;
            }
            let verts = vec![
                [p0[0], p0[1], spec.z_ceiling],
                [p0[0], p0[1], spec.z_floor],
                [p1[0], p1[1], spec.z_floor],
                [p1[0], p1[1], spec.z_ceiling],
            ];
            let (_, wa) = newell_normal_and_area(&verts);
            if wa < 1.0e-4 {
                continue;
            }
            out.push(ExtrudedSurface {
                name: format!("{}_Wall_{wall_idx}", spec.name),
                zone_name: spec.name.clone(),
                kind: SurfaceKind::Wall,
                boundary: BoundaryKind::Outdoors,
                boundary_object: String::new(),
                sun_exposed: true,
                wind_exposed: true,
                vertices: verts,
            });
            wall_idx += 1;
        }
    }

    let expected_vol = net_fp_area * height;
    let actual_vol = shell_signed_volume(&out);
    if (actual_vol - expected_vol).abs() > 1.0e-2 * expected_vol + 1.0e-2 {
        return Err(ExtrudeError::VolumeConservation {
            zone: spec.name.clone(),
            actual: actual_vol,
            expected: expected_vol,
        });
    }

    // Keep geo BooleanOps link live for Polygon usage cleanly
    let _ = std::hint::black_box(&to_geo_polygon);
    Ok(out)
}

/// Union/clip check helper wrapping `geo::BooleanOps` without `geos` (pure Rust).
pub fn polygon_overlap_area_m2(a: &[[f64; 2]], b: &[[f64; 2]]) -> f64 {
    let pa = to_geo_polygon(a, &[]);
    let pb = to_geo_polygon(b, &[]);
    pa.intersection(&pb).unsigned_area()
}
