//! Zero-copy `&[u8]` IDF/ExpIDF parser and Newell surface geometry helpers.

/// Raw parsed IDF object preserving original casing alongside uppercase normalized type.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RawIdfObject {
    pub obj_type: String,
    pub raw_type: String,
    pub fields: Vec<String>,
}

/// Zero-copy-friendly `&[u8]` IDF scanner stripping `!` comments and splitting on `,` / `;`.
///
/// Handles single- and multi-line objects, trailing comments on lines, and whitespace trimming
/// matching `openubem.gpusim.subset.parse_expidf`.
pub fn parse_idf_bytes(bytes: &[u8]) -> Vec<RawIdfObject> {
    let mut objects = Vec::with_capacity(256);
    let mut current_fields: Vec<String> = Vec::new();
    let mut field_buf: Vec<u8> = Vec::with_capacity(64);

    let mut i = 0usize;
    let n = bytes.len();

    while i < n {
        let b = bytes[i];
        match b {
            b'!' => {
                // Skip to newline
                if let Some(rel) = memchr::memchr(b'\n', &bytes[i..]) {
                    i += rel + 1;
                } else {
                    break;
                }
            }
            b',' => {
                let s = String::from_utf8_lossy(trim_ascii_bytes(&field_buf)).into_owned();
                current_fields.push(s);
                field_buf.clear();
                i += 1;
            }
            b';' => {
                let s = String::from_utf8_lossy(trim_ascii_bytes(&field_buf)).into_owned();
                current_fields.push(s);
                field_buf.clear();

                if !current_fields.is_empty() {
                    let raw_type = current_fields.remove(0);
                    if !raw_type.is_empty() {
                        let obj_type = raw_type.to_ascii_uppercase();
                        objects.push(RawIdfObject {
                            obj_type,
                            raw_type,
                            fields: std::mem::take(&mut current_fields),
                        });
                    } else {
                        current_fields.clear();
                    }
                }
                i += 1;
            }
            _ => {
                field_buf.push(b);
                i += 1;
            }
        }
    }
    objects
}

#[inline]
fn trim_ascii_bytes(mut b: &[u8]) -> &[u8] {
    while let Some(&f) = b.first() {
        if f.is_ascii_whitespace() {
            b = &b[1..];
        } else {
            break;
        }
    }
    while let Some(&l) = b.last() {
        if l.is_ascii_whitespace() {
            b = &b[..b.len() - 1];
        } else {
            break;
        }
    }
    b
}

/// Newell polygon area and outward unit normal matching `openubem.gpusim.compile._newell_area_and_normal`.
pub fn newell_area_and_normal(verts: &[[f64; 3]]) -> (f64, [f64; 3]) {
    let n = verts.len();
    if n < 3 {
        return (0.0, [0.0, 0.0, 1.0]);
    }
    let mut nx = 0.0_f64;
    let mut ny = 0.0_f64;
    let mut nz = 0.0_f64;
    for i in 0..n {
        let p0 = verts[i];
        let p1 = verts[(i + 1) % n];
        nx += (p0[1] - p1[1]) * (p0[2] + p1[2]);
        ny += (p0[2] - p1[2]) * (p0[0] + p1[0]);
        nz += (p0[0] - p1[0]) * (p0[1] + p1[1]);
    }
    let norm = (nx * nx + ny * ny + nz * nz).sqrt();
    if norm <= 1.0e-12 {
        return (0.0, [0.0, 0.0, 1.0]);
    }
    (0.5 * norm, [nx / norm, ny / norm, nz / norm])
}

/// Compute EnergyPlus surface `(azimuth_deg, tilt_deg)` matching `compile._determine_azimuth_and_tilt`.
pub fn determine_azimuth_and_tilt(normal: [f64; 3]) -> (f64, f64) {
    let cos_t = normal[2].clamp(-1.0, 1.0);
    let tilt = cos_t.acos().to_degrees();
    let az = if normal[0].abs() < 1.0e-5 && normal[1].abs() < 1.0e-5 {
        0.0
    } else {
        let mut a = normal[0].atan2(normal[1]).to_degrees();
        if a < 0.0 {
            a += 360.0;
        }
        a
    };
    (az, tilt)
}

/// Fast batch envelope construction compliance checker for `openubem/idf/compliance.py`.
///
/// Validates that every surface in `surface_types` / `surface_constructions` maps to a
/// construction defined in `known_constructions` (normalized lowercase), returning failing indices.
pub fn check_surface_construction_links(
    surface_constructions: &[String],
    known_constructions: &[String],
) -> Vec<usize> {
    use std::collections::HashSet;
    let known: HashSet<unicase::UniCase<&str>> = known_constructions
        .iter()
        .map(|s| unicase::UniCase::new(s.trim()))
        .collect();
    surface_constructions
        .iter()
        .enumerate()
        .filter_map(|(idx, c)| {
            let k = unicase::UniCase::new(c.trim());
            if !k.is_empty() && !known.contains(&k) {
                Some(idx)
            } else {
                None
            }
        })
        .collect()
}
