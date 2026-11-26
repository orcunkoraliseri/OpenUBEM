//! `i64` quantized grid snapping and collinear vertex elimination (`FINDING 221`).

/// Quantize a 2D vertex onto an integer `i64` grid of spacing `grid_m` meters and de-quantize.
#[inline]
pub fn quantize_pt(pt: [f64; 2], grid_m: f64) -> [f64; 2] {
    let inv = 1.0 / grid_m.max(1.0e-6);
    let qx = (pt[0] * inv).round() as i64;
    let qy = (pt[1] * inv).round() as i64;
    [(qx as f64) * grid_m, (qy as f64) * grid_m]
}

/// Exact shoelace signed area (positive = CCW, negative = CW).
pub fn signed_area_2d(ring: &[[f64; 2]]) -> f64 {
    let n = ring.len();
    if n < 3 {
        return 0.0;
    }
    let mut acc = 0.0_f64;
    for i in 0..n {
        let j = (i + 1) % n;
        acc += ring[i][0] * ring[j][1] - ring[j][0] * ring[i][1];
    }
    0.5 * acc
}

/// Remove consecutive duplicate and near-collinear vertices along a closed ring.
pub fn clean_ring_2d(ring: &[[f64; 2]], grid_m: f64, min_edge_m: f64) -> Vec<[f64; 2]> {
    let mut pts: Vec<[f64; 2]> = Vec::with_capacity(ring.len());
    for &raw in ring {
        let q = quantize_pt(raw, grid_m);
        if let Some(&prev) = pts.last() {
            if (q[0] - prev[0]).hypot(q[1] - prev[1]) < min_edge_m {
                continue;
            }
        }
        pts.push(q);
    }
    if pts.len() >= 2 {
        let first = pts[0];
        if let Some(&last) = pts.last() {
            if (last[0] - first[0]).hypot(last[1] - first[1]) < min_edge_m {
                pts.pop();
            }
        }
    }
    // Strip collinear interior vertices (iterative pass until fixed point)
    let mut changed = true;
    while changed && pts.len() >= 4 {
        changed = false;
        let n = pts.len();
        let mut filtered = Vec::with_capacity(n);
        for i in 0..n {
            let prev = pts[(i + n - 1) % n];
            let curr = pts[i];
            let next = pts[(i + 1) % n];
            let ux = curr[0] - prev[0];
            let uy = curr[1] - prev[1];
            let vx = next[0] - curr[0];
            let vy = next[1] - curr[1];
            let len_u = ux.hypot(uy);
            let len_v = vx.hypot(vy);
            if len_u < min_edge_m || len_v < min_edge_m {
                changed = true;
                continue;
            }
            let cross = (ux * vy - uy * vx).abs();
            let sin_theta = cross / (len_u * len_v);
            let dot = ux * vx + uy * vy;
            // Remove vertex if collinear forward (sin < 1e-4 and dot > 0)
            if sin_theta < 1.0e-4 && dot > 0.0 {
                changed = true;
                continue;
            }
            filtered.push(curr);
        }
        pts = filtered;
    }
    pts
}

/// Ensure ring is counter-clockwise (positive signed area).
pub fn ensure_ccw(ring: &mut Vec<[f64; 2]>) {
    if signed_area_2d(ring) < 0.0 {
        ring.reverse();
    }
}

/// Snap all zone coordinates globally to a shared `i64` coordinate grid.
pub fn snap_zones_globally(rings: &mut [Vec<[f64; 2]>], grid_m: f64, min_edge_m: f64) {
    for ring in rings.iter_mut() {
        *ring = clean_ring_2d(ring, grid_m, min_edge_m);
        ensure_ccw(ring);
    }
}
