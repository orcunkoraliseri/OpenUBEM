//! `rstar` R-tree + local `(u, v)` reciprocal interzone surface matcher & splitter.

use rstar::{AABB, RTree, RTreeObject};

use crate::extrude::{
    BoundaryKind, ExtrudedSurface, SurfaceKind, newell_normal_and_area, polygon_overlap_area_m2,
};

#[derive(Debug, Clone)]
struct SurfEntry {
    idx: usize,
    aabb: AABB<[f64; 3]>,
}

impl RTreeObject for SurfEntry {
    type Envelope = AABB<[f64; 3]>;

    fn envelope(&self) -> Self::Envelope {
        self.aabb
    }
}

fn surface_aabb(verts: &[[f64; 3]], pad: f64) -> AABB<[f64; 3]> {
    let mut mn = [f64::INFINITY; 3];
    let mut mx = [f64::NEG_INFINITY; 3];
    for v in verts {
        for a in 0..3 {
            mn[a] = mn[a].min(v[a]);
            mx[a] = mx[a].max(v[a]);
        }
    }
    AABB::from_corners([mn[0] - pad, mn[1] - pad, mn[2] - pad], [mx[0] + pad, mx[1] + pad, mx[2] + pad])
}

fn same_vertex_set_reversed(a: &[[f64; 3]], b: &[[f64; 3]], tol: f64) -> bool {
    if a.len() != b.len() || a.is_empty() {
        return false;
    }
    let n = a.len();
    // EnergyPlus pairs are identical geometry with opposite winding.
    for shift in 0..n {
        let mut ok = true;
        for i in 0..n {
            let va = a[i];
            let vb = b[(shift + n - i) % n];
            let d = (va[0] - vb[0]).abs() + (va[1] - vb[1]).abs() + (va[2] - vb[2]).abs();
            if d > tol * 3.0 {
                ok = false;
                break;
            }
        }
        if ok {
            return true;
        }
    }
    false
}

/// Reorder and pair exact/overlapping interzone walls & ceilings/floors bijectively.
///
/// Guarantees:
/// - Every `Surface` partner link is strictly reciprocal `(A <-> B)`.
/// - Zero `Roof <-> Roof` or same-type horizontal pairs (`FINDING` guards).
/// - Partial vertical wall overlaps are cleanly split into exact reciprocal `(u,v)` patches + outdoors tails.
pub fn match_and_split_interzone_surfaces(surfaces: &mut Vec<ExtrudedSurface>, tol_m: f64) {
    // Pass 1: match horizontal inter-floor Floor <-> Ceiling pairs cleanly
    let mut tree = RTree::bulk_load(
        surfaces
            .iter()
            .enumerate()
            .map(|(idx, s)| SurfEntry {
                idx,
                aabb: surface_aabb(&s.vertices, tol_m),
            })
            .collect(),
    );

    let n_orig = surfaces.len();
    let mut matched = vec![false; n_orig];

    for i in 0..n_orig {
        if matched[i] || surfaces[i].boundary == BoundaryKind::Surface {
            continue;
        }
        let kind_i = surfaces[i].kind;
        let zone_i = surfaces[i].zone_name.clone();
        let (ni, ai) = newell_normal_and_area(&surfaces[i].vertices);
        if ai < 1.0e-4 {
            continue;
        }
        let box_i = surface_aabb(&surfaces[i].vertices, tol_m);
        let cands: Vec<usize> = tree
            .locate_in_envelope_intersecting(box_i)
            .map(|e| e.idx)
            .collect();

        for j in cands {
            if j <= i || matched[j] || surfaces[j].zone_name == zone_i {
                continue;
            }
            let kind_j = surfaces[j].kind;
            // Disallow Roof<->Roof or Floor<->Floor pairs; allow Wall<->Wall or Ceiling/Roof<->Floor
            let compatible_kind = match (kind_i, kind_j) {
                (SurfaceKind::Wall, SurfaceKind::Wall) => true,
                (SurfaceKind::Ceiling | SurfaceKind::Roof, SurfaceKind::Floor) => true,
                (SurfaceKind::Floor, SurfaceKind::Ceiling | SurfaceKind::Roof) => true,
                _ => false,
            };
            if !compatible_kind {
                continue;
            }
            let (nj, aj) = newell_normal_and_area(&surfaces[j].vertices);
            let dot = ni[0] * nj[0] + ni[1] * nj[1] + ni[2] * nj[2];
            if dot > -0.999 {
                continue;
            }

            if (ai - aj).abs() <= 1.0e-2
                && same_vertex_set_reversed(&surfaces[i].vertices, &surfaces[j].vertices, tol_m)
            {
                let name_i = surfaces[i].name.clone();
                let name_j = surfaces[j].name.clone();
                surfaces[i].boundary = BoundaryKind::Surface;
                surfaces[i].boundary_object = name_j;
                surfaces[i].sun_exposed = false;
                surfaces[i].wind_exposed = false;

                surfaces[j].boundary = BoundaryKind::Surface;
                surfaces[j].boundary_object = name_i;
                surfaces[j].sun_exposed = false;
                surfaces[j].wind_exposed = false;

                if surfaces[i].kind == SurfaceKind::Roof {
                    surfaces[i].kind = SurfaceKind::Ceiling;
                }
                if surfaces[j].kind == SurfaceKind::Roof {
                    surfaces[j].kind = SurfaceKind::Ceiling;
                }
                matched[i] = true;
                matched[j] = true;
                break;
            } else if kind_i != SurfaceKind::Wall
                && kind_j != SurfaceKind::Wall
                && (surfaces[i].vertices[0][2] - surfaces[j].vertices[0][2]).abs() <= tol_m
            {
                // Horizontal interfloor cyclic / partial overlap check
                let p_i: Vec<[f64; 2]> = surfaces[i].vertices.iter().map(|v| [v[0], v[1]]).collect();
                let p_j: Vec<[f64; 2]> = surfaces[j].vertices.iter().map(|v| [v[0], v[1]]).collect();
                let ov_a = polygon_overlap_area_m2(&p_i, &p_j);
                if ov_a >= (ai.min(aj) * 0.99) && surfaces[i].vertices.len() == surfaces[j].vertices.len() {
                    let name_i = surfaces[i].name.clone();
                    let name_j = surfaces[j].name.clone();
                    surfaces[i].boundary = BoundaryKind::Surface;
                    surfaces[i].boundary_object = name_j;
                    surfaces[i].sun_exposed = false;
                    surfaces[i].wind_exposed = false;
                    surfaces[j].boundary = BoundaryKind::Surface;
                    surfaces[j].boundary_object = name_i;
                    surfaces[j].sun_exposed = false;
                    surfaces[j].wind_exposed = false;
                    if surfaces[i].kind == SurfaceKind::Roof {
                        surfaces[i].kind = SurfaceKind::Ceiling;
                    }
                    if surfaces[j].kind == SurfaceKind::Roof {
                        surfaces[j].kind = SurfaceKind::Ceiling;
                    }
                    matched[i] = true;
                    matched[j] = true;
                    break;
                }
            }
        }
    }

    // Pass 2: Handle partial/offset vertical shared walls via local 1D tangent + Z interval splitting
    let _ = &mut tree;
    let mut additions: Vec<ExtrudedSurface> = Vec::new();
    let mut split_retired = vec![false; surfaces.len()];

    for i in 0..surfaces.len() {
        if matched[i] || split_retired[i] || surfaces[i].kind != SurfaceKind::Wall {
            continue;
        }
        let va = &surfaces[i].vertices;
        if va.len() != 4 {
            continue;
        }
        let (na, _) = newell_normal_and_area(va);
        // Tangent unit along bottom edge va[1] -> va[2]
        let dx = va[2][0] - va[1][0];
        let dy = va[2][1] - va[1][1];
        let len_a = dx.hypot(dy);
        if len_a < 1.0e-3 {
            continue;
        }
        let ux = dx / len_a;
        let uy = dy / len_a;
        let orig = [va[1][0], va[1][1]];
        let za0 = va[1][2].min(va[0][2]);
        let za1 = va[1][2].max(va[0][2]);

        for j in (i + 1)..surfaces.len() {
            if matched[j]
                || split_retired[j]
                || surfaces[j].kind != SurfaceKind::Wall
                || surfaces[j].zone_name == surfaces[i].zone_name
            {
                continue;
            }
            let vb = &surfaces[j].vertices;
            if vb.len() != 4 {
                continue;
            }
            let (nb, _) = newell_normal_and_area(vb);
            if na[0] * nb[0] + na[1] * nb[1] + na[2] * nb[2] > -0.999 {
                continue;
            }
            let zb0 = vb[1][2].min(vb[0][2]);
            let zb1 = vb[1][2].max(vb[0][2]);
            let z0 = za0.max(zb0);
            let z1 = za1.min(zb1);
            if z1 - z0 < 1.0e-2 {
                continue;
            }
            // Normal plane distance check
            let d_plane = ((vb[1][0] - orig[0]) * na[0] + (vb[1][1] - orig[1]) * na[1]).abs();
            if d_plane > tol_m {
                continue;
            }
            let tb0_raw = (vb[1][0] - orig[0]) * ux + (vb[1][1] - orig[1]) * uy;
            let tb1_raw = (vb[2][0] - orig[0]) * ux + (vb[2][1] - orig[1]) * uy;
            let tb0 = tb0_raw.min(tb1_raw);
            let tb1 = tb0_raw.max(tb1_raw);

            let ov0 = 0.0_f64.max(tb0);
            let ov1 = len_a.min(tb1);
            if ov1 - ov0 < 1.0e-2 {
                continue;
            }

            // Build exact shared reciprocal quad [ov0..ov1, z0..z1]
            let p_ov0 = [orig[0] + ov0 * ux, orig[1] + ov0 * uy];
            let p_ov1 = [orig[0] + ov1 * ux, orig[1] + ov1 * uy];
            let shared_a_name = format!("{}_sh_{j}", surfaces[i].name);
            let shared_b_name = format!("{}_sh_{i}", surfaces[j].name);

            let verts_a = vec![
                [p_ov0[0], p_ov0[1], z1],
                [p_ov0[0], p_ov0[1], z0],
                [p_ov1[0], p_ov1[1], z0],
                [p_ov1[0], p_ov1[1], z1],
            ];
            // Reverse winding for opposite normal on partner zone
            let verts_b = vec![
                [p_ov1[0], p_ov1[1], z1],
                [p_ov1[0], p_ov1[1], z0],
                [p_ov0[0], p_ov0[1], z0],
                [p_ov0[0], p_ov0[1], z1],
            ];

            additions.push(ExtrudedSurface {
                name: shared_a_name.clone(),
                zone_name: surfaces[i].zone_name.clone(),
                kind: SurfaceKind::Wall,
                boundary: BoundaryKind::Surface,
                boundary_object: shared_b_name.clone(),
                sun_exposed: false,
                wind_exposed: false,
                vertices: verts_a,
            });
            additions.push(ExtrudedSurface {
                name: shared_b_name,
                zone_name: surfaces[j].zone_name.clone(),
                kind: SurfaceKind::Wall,
                boundary: BoundaryKind::Surface,
                boundary_object: shared_a_name,
                sun_exposed: false,
                wind_exposed: false,
                vertices: verts_b,
            });

            // Keep left/right exterior remainder tails on A if > 1 cm
            for (tag, t0, t1, z_lo, z_hi, zn, nm) in [
                ("L", 0.0, ov0, za0, za1, &surfaces[i].zone_name, &surfaces[i].name),
                ("R", ov1, len_a, za0, za1, &surfaces[i].zone_name, &surfaces[i].name),
            ] {
                if t1 - t0 >= 1.0e-2 {
                    let q0 = [orig[0] + t0 * ux, orig[1] + t0 * uy];
                    let q1 = [orig[0] + t1 * ux, orig[1] + t1 * uy];
                    additions.push(ExtrudedSurface {
                        name: format!("{nm}_tail{tag}"),
                        zone_name: zn.clone(),
                        kind: SurfaceKind::Wall,
                        boundary: BoundaryKind::Outdoors,
                        boundary_object: String::new(),
                        sun_exposed: true,
                        wind_exposed: true,
                        vertices: vec![
                            [q0[0], q0[1], z_hi],
                            [q0[0], q0[1], z_lo],
                            [q1[0], q1[1], z_lo],
                            [q1[0], q1[1], z_hi],
                        ],
                    });
                }
            }
            // Keep left/right exterior remainder tails on B (using opposite tangent direction)
            for (tag, t0, t1) in [("BL", tb0, ov0), ("BR", ov1, tb1)] {
                if t1 - t0 >= 1.0e-2 {
                    let q0 = [orig[0] + t1 * ux, orig[1] + t1 * uy];
                    let q1 = [orig[0] + t0 * ux, orig[1] + t0 * uy];
                    additions.push(ExtrudedSurface {
                        name: format!("{}_tail{tag}", surfaces[j].name),
                        zone_name: surfaces[j].zone_name.clone(),
                        kind: SurfaceKind::Wall,
                        boundary: BoundaryKind::Outdoors,
                        boundary_object: String::new(),
                        sun_exposed: true,
                        wind_exposed: true,
                        vertices: vec![
                            [q0[0], q0[1], zb1],
                            [q0[0], q0[1], zb0],
                            [q1[0], q1[1], zb0],
                            [q1[0], q1[1], zb1],
                        ],
                    });
                }
            }

            split_retired[i] = true;
            split_retired[j] = true;
            matched[i] = true;
            matched[j] = true;
            break;
        }
    }

    if !additions.is_empty() {
        let mut kept = Vec::with_capacity(surfaces.len() + additions.len());
        for (idx, s) in surfaces.drain(..).enumerate() {
            if !split_retired[idx] {
                kept.push(s);
            }
        }
        kept.extend(additions);
        *surfaces = kept;
    }
}
