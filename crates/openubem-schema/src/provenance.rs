//! Canonical provenance tokens, legacy weights (`T07.1`), and lineage summary scorer (`M09 §3B`).

use crate::error::SchemaError;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

/// Canonical confidence tiers aligned with `openubem/semantic/provenance.py`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ConfidenceTier {
    High,
    Medium,
    Low,
}

impl ConfidenceTier {
    /// Normalize `"HIGH" | "MEDIUM" | "MED" | "LOW"` (case-insensitive) to canonical tier.
    pub fn parse(raw: &str) -> Result<Self, SchemaError> {
        match raw.trim().to_ascii_uppercase().as_str() {
            "HIGH" => Ok(Self::High),
            "MEDIUM" | "MED" => Ok(Self::Medium),
            "LOW" => Ok(Self::Low),
            _ => Err(SchemaError::InvalidConfidenceTier(raw.to_owned())),
        }
    }

    /// Canonical full string (`HIGH` / `MEDIUM` / `LOW`).
    pub const fn canonical_str(self) -> &'static str {
        match self {
            Self::High => "HIGH",
            Self::Medium => "MEDIUM",
            Self::Low => "LOW",
        }
    }

    /// Short token suffix (`HIGH` / `MED` / `LOW`).
    pub const fn token_suffix(self) -> &'static str {
        match self {
            Self::High => "HIGH",
            Self::Medium => "MED",
            Self::Low => "LOW",
        }
    }

    /// Lineage weight (`HIGH=1.0`, `MEDIUM=0.5`, `LOW=0.1`).
    pub const fn weight(self) -> f64 {
        match self {
            Self::High => 1.0,
            Self::Medium => 0.5,
            Self::Low => 0.1,
        }
    }

    fn from_suffix(suffix: &str) -> Option<Self> {
        match suffix {
            "HIGH" => Some(Self::High),
            "MED" => Some(Self::Medium),
            "LOW" => Some(Self::Low),
            _ => None,
        }
    }
}

/// Legacy tier-less provenance tokens ratified in `T07.1` (must not score as observed `1.0`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum LegacyProvenance {
    KdeImputed,
    Heuristic,
    PdeGenerated,
    AshraeStandard,
}

impl LegacyProvenance {
    /// Exact match lookup matching `LEGACY_TOKEN_WEIGHT` in `provenance.py:49-54`.
    pub fn parse(token: &str) -> Option<Self> {
        match token {
            "KDE_IMPUTED" => Some(Self::KdeImputed),
            "HEURISTIC" => Some(Self::Heuristic),
            "PDE_GENERATED" => Some(Self::PdeGenerated),
            "ASHRAE_STANDARD" => Some(Self::AshraeStandard),
            _ => None,
        }
    }

    /// Exact ratified weight (`0.5` for KDE/HEURISTIC, `0.1` for PDE/ASHRAE).
    pub const fn weight(self) -> f64 {
        match self {
            Self::KdeImputed | Self::Heuristic => 0.5,
            Self::PdeGenerated | Self::AshraeStandard => 0.1,
        }
    }
}

/// Canonical provenance lineage parsed from a cell value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProvenanceLineage {
    Observed,
    Imputed {
        method: String,
        source: String,
        tier: ConfidenceTier,
    },
    LegacyImputed(LegacyProvenance),
}

/// Build a `{METHOD}_{SOURCE}_{TIER}` token (`provenance.py::impute_token`).
pub fn impute_token(method: &str, source: &str, confidence: &str) -> Result<String, SchemaError> {
    let tier = ConfidenceTier::parse(confidence)?;
    Ok(format!(
        "{}_{}_{}",
        method.to_ascii_uppercase(),
        source.to_ascii_uppercase(),
        tier.token_suffix()
    ))
}

/// Inverse of `impute_token`: returns `(METHOD, SOURCE, canonical TIER)` or `None`.
///
/// Mirrors `provenance.py::parse_token` (sensitive to exact suffix match; caller uppercases when building).
pub fn parse_token(token: &str) -> Option<(String, String, ConfidenceTier)> {
    let mut parts = token.split('_');
    let method = parts.next()?;
    let rest: Vec<&str> = parts.collect();
    if rest.len() < 2 {
        return None;
    }
    let suffix = *rest.last()?;
    let tier = ConfidenceTier::from_suffix(suffix)?;
    let source = rest[..rest.len() - 1].join("_");
    if source.is_empty() {
        return None;
    }
    Some((method.to_owned(), source, tier))
}

/// Compute `(is_imputed, field_score)` for one provenance cell (`provenance.py::_field_score`).
pub fn score_provenance_cell(cell: Option<&str>) -> (bool, f64) {
    let Some(raw) = cell else {
        return (false, 1.0);
    };
    let s = raw.trim();
    if s.is_empty() {
        return (false, 1.0);
    }
    if let Some(legacy) = LegacyProvenance::parse(s) {
        return (true, legacy.weight());
    }
    let Some((method, _source, tier)) = parse_token(s) else {
        return (false, 1.0);
    };
    if method == "OBSERVED" {
        return (false, 1.0);
    }
    (true, tier.weight())
}

/// Score N rows across C provenance columns in parallel, returning `(counts, mean_conf)`.
///
/// Uses fixed column accumulation matching Python's `for c in prov_cols: score_sum[i] += score`
/// order for bit-exact float equivalence, while parallelizing across row chunks with `rayon`.
pub fn score_provenance_matrix(
    columns: &[Vec<Option<&str>>],
    n_rows: usize,
) -> (Vec<i64>, Vec<f64>) {
    if columns.is_empty() {
        return (vec![0; n_rows], vec![1.0; n_rows]);
    }
    let n_cols = columns.len() as f64;
    let pairs: Vec<(i64, f64)> = (0..n_rows)
        .into_par_iter()
        .map(|row_idx| {
            let mut count = 0_i64;
            let mut sum = 0.0_f64;
            for col in columns {
                let (imp, score) = score_provenance_cell(col[row_idx]);
                if imp {
                    count += 1;
                }
                sum += score;
            }
            (count, sum / n_cols)
        })
        .collect();

    let mut counts = Vec::with_capacity(n_rows);
    let mut means = Vec::with_capacity(n_rows);
    for (c, m) in pairs {
        counts.push(c);
        means.push(m);
    }
    (counts, means)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn legacy_weights_match_t07_1() {
        assert_eq!(score_provenance_cell(Some("KDE_IMPUTED")), (true, 0.5));
        assert_eq!(score_provenance_cell(Some("HEURISTIC")), (true, 0.5));
        assert_eq!(score_provenance_cell(Some("PDE_GENERATED")), (true, 0.1));
        assert_eq!(score_provenance_cell(Some("ASHRAE_STANDARD")), (true, 0.1));
        assert_eq!(score_provenance_cell(None), (false, 1.0));
        assert_eq!(score_provenance_cell(Some("")), (false, 1.0));
        assert_eq!(
            score_provenance_cell(Some("OBSERVED_OSM_HIGH")),
            (false, 1.0)
        );
    }

    #[test]
    fn parse_token_multi_underscore_source() {
        let tok = impute_token("DEFAULT", "ASHRAE901_COOLING_COP", "LOW").unwrap();
        assert_eq!(tok, "DEFAULT_ASHRAE901_COOLING_COP_LOW");
        assert_eq!(
            parse_token(&tok),
            Some((
                "DEFAULT".to_owned(),
                "ASHRAE901_COOLING_COP".to_owned(),
                ConfidenceTier::Low
            ))
        );
    }

    proptest! {
        #[test]
        fn fuzz_parse_and_score_never_panics(s in "\\PC*") {
            let _ = parse_token(&s);
            let (imp, w) = score_provenance_cell(Some(&s));
            prop_assert!(w.is_finite());
            prop_assert!((0.0..=1.0).contains(&w));
            if !imp {
                prop_assert_eq!(w, 1.0);
            }
        }
    }
}
