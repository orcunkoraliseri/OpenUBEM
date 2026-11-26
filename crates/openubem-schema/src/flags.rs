//! Stack-allocated canonical `QualityFlagSet` (`smallvec`, `D-RS-03`).

use std::fmt;

use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

use crate::error::SchemaError;
use crate::provenance::parse_token;

/// Closed vocabulary of canonical `data_quality_flag` tokens across OpenUBEM Steps 1–5.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum QualityFlag {
    GenericTag,
    HeightOnlyFt,
    IncompleteWalOrJournal,
    IodNoOccupiedHours,
    NoBuildingTag,
    NoFloors,
    NoFunction,
    NoHeight,
    NoYear,
    OverlapResolved,
    ResultsCsvFallback,
    /// Dynamic `{METHOD}_{SOURCE}_{TIER}` imputation provenance flag (`M09 §3A`).
    Imputed(String),
}

impl QualityFlag {
    /// Strict fail-closed parser for canonical Step 1–5 tokens and `{METHOD}_{SOURCE}_{TIER}`.
    pub fn parse_strict(token: &str) -> Result<Self, SchemaError> {
        let tok = token.trim();
        match tok {
            "generic_tag" => Ok(Self::GenericTag),
            "height_only_ft" => Ok(Self::HeightOnlyFt),
            "incomplete_wal_or_journal" => Ok(Self::IncompleteWalOrJournal),
            "IOD_NO_OCCUPIED_HOURS" => Ok(Self::IodNoOccupiedHours),
            "no_building_tag" => Ok(Self::NoBuildingTag),
            "no_floors" => Ok(Self::NoFloors),
            "no_function" => Ok(Self::NoFunction),
            "no_height" => Ok(Self::NoHeight),
            "no_year" => Ok(Self::NoYear),
            "overlap_resolved" => Ok(Self::OverlapResolved),
            "RESULTS_CSV_FALLBACK" => Ok(Self::ResultsCsvFallback),
            _ => {
                if let Some((_method, _source, _tier)) = parse_token(tok) {
                    Ok(Self::Imputed(tok.to_owned()))
                } else {
                    Err(SchemaError::UnknownFlagToken(tok.to_owned()))
                }
            }
        }
    }

    /// Canonical string token.
    pub fn as_str(&self) -> &str {
        match self {
            Self::GenericTag => "generic_tag",
            Self::HeightOnlyFt => "height_only_ft",
            Self::IncompleteWalOrJournal => "incomplete_wal_or_journal",
            Self::IodNoOccupiedHours => "IOD_NO_OCCUPIED_HOURS",
            Self::NoBuildingTag => "no_building_tag",
            Self::NoFloors => "no_floors",
            Self::NoFunction => "no_function",
            Self::NoHeight => "no_height",
            Self::NoYear => "no_year",
            Self::OverlapResolved => "overlap_resolved",
            Self::ResultsCsvFallback => "RESULTS_CSV_FALLBACK",
            Self::Imputed(s) => s.as_str(),
        }
    }
}

impl fmt::Display for QualityFlag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Output delimiter toggle (`D-RS-03`: canonical `|` vs legacy `,` for Step 1/5 shadow parity).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum FlagDelimiterMode {
    #[default]
    PipeCanonical,
    CommaLegacy,
}

impl FlagDelimiterMode {
    /// Separator character.
    pub const fn sep(self) -> &'static str {
        match self {
            Self::PipeCanonical => "|",
            Self::CommaLegacy => ",",
        }
    }
}

/// Stack-allocated normalized set of canonical `QualityFlag` values (`D-RS-03`).
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct QualityFlagSet(pub SmallVec<[QualityFlag; 8]>);

impl QualityFlagSet {
    /// Parse both `,` and `|` delimiters strictly, sort deterministically, and deduplicate.
    pub fn parse_strict(input: &str) -> Result<Self, SchemaError> {
        let mut flags: SmallVec<[QualityFlag; 8]> = SmallVec::new();
        for raw in input.split(|c| c == ',' || c == '|') {
            let tok = raw.trim();
            if tok.is_empty() {
                continue;
            }
            flags.push(QualityFlag::parse_strict(tok)?);
        }
        flags.sort_by(|a, b| a.as_str().cmp(b.as_str()));
        flags.dedup();
        Ok(Self(flags))
    }

    /// Insert a flag idempotently while maintaining canonical sorted order.
    pub fn insert(&mut self, flag: QualityFlag) {
        if !self.0.iter().any(|existing| existing == &flag) {
            self.0.push(flag);
            self.0.sort_by(|a, b| a.as_str().cmp(b.as_str()));
        }
    }

    /// Serialize using `|` (canonical) or `,` (legacy Step 1/5 adapter).
    pub fn format(&self, mode: FlagDelimiterMode) -> String {
        let sep = mode.sep();
        let mut out = String::new();
        for (i, flag) in self.0.iter().enumerate() {
            if i > 0 {
                out.push_str(sep);
            }
            out.push_str(flag.as_str());
        }
        out
    }

    /// True if no flags are present.
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    /// Number of unique flags.
    pub fn len(&self) -> usize {
        self.0.len()
    }
}

/// Idempotently append `token` to a delimiter-separated flag string (`provenance.py::append_flag_token`).
///
/// Supports normalized canonical `|` emission or Python-legacy `,`/`|` token preservation.
pub fn append_flag_token_delimited(existing: Option<&str>, token: &str, sep: char) -> String {
    let mut tokens: SmallVec<[&str; 8]> = SmallVec::new();
    if let Some(raw) = existing {
        for part in raw.split(|c| c == ',' || c == '|') {
            let t = part.trim();
            if !t.is_empty() && !tokens.contains(&t) {
                tokens.push(t);
            }
        }
    }
    let tok = token.trim();
    if !tok.is_empty() && !tokens.contains(&tok) {
        tokens.push(tok);
    }
    let mut out = String::new();
    for (i, t) in tokens.iter().enumerate() {
        if i > 0 {
            out.push(sep);
        }
        out.push_str(t);
    }
    out
}

/// Merge two flag strings idempotently preserving base order (`aggregator.py::_merge_flags` parity).
pub fn merge_flag_strings(base: Option<&str>, delta: Option<&str>, sep: char) -> String {
    let mut tokens: SmallVec<[&str; 8]> = SmallVec::new();
    if let Some(b) = base {
        for part in b.split(|c| c == ',' || c == '|') {
            let t = part.trim();
            if !t.is_empty() && !tokens.contains(&t) {
                tokens.push(t);
            }
        }
    }
    if let Some(d) = delta {
        for part in d.split(|c| c == ',' || c == '|') {
            let t = part.trim();
            if !t.is_empty() && !tokens.contains(&t) {
                tokens.push(t);
            }
        }
    }
    let mut out = String::new();
    for (i, t) in tokens.iter().enumerate() {
        if i > 0 {
            out.push(sep);
        }
        out.push_str(t);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn parse_strict_dedups_sorts_and_bridges_delimiters() {
        let parsed = QualityFlagSet::parse_strict("no_year, no_height | no_year | DEFAULT_ASHRAE_LOW")
            .expect("valid canonical flags");
        assert_eq!(
            parsed.format(FlagDelimiterMode::PipeCanonical),
            "DEFAULT_ASHRAE_LOW|no_height|no_year"
        );
        assert_eq!(
            parsed.format(FlagDelimiterMode::CommaLegacy),
            "DEFAULT_ASHRAE_LOW,no_height,no_year"
        );
    }

    #[test]
    fn parse_strict_fails_closed_on_unknown() {
        let err = QualityFlagSet::parse_strict("no_height|bogus_typo_flag").unwrap_err();
        assert!(matches!(err, SchemaError::UnknownFlagToken(_)));
    }

    proptest! {
        #[test]
        fn flag_roundtrip_and_idempotence(
            items in prop::collection::vec(
                prop_oneof![
                    Just("no_floors"),
                    Just("no_height"),
                    Just("generic_tag"),
                    Just("no_function"),
                    Just("overlap_resolved"),
                    Just("height_only_ft"),
                    Just("no_building_tag"),
                    Just("no_year"),
                    Just("RESULTS_CSV_FALLBACK"),
                    Just("IOD_NO_OCCUPIED_HOURS"),
                    Just("DEFAULT_ASHRAE901_LOW"),
                ],
                0..12
            )
        ) {
            let joined_comma = items.join(",");
            let joined_pipe = items.join("|");
            let from_comma = QualityFlagSet::parse_strict(&joined_comma).unwrap();
            let from_pipe = QualityFlagSet::parse_strict(&joined_pipe).unwrap();
            prop_assert_eq!(&from_comma, &from_pipe);
            let canonical = from_comma.format(FlagDelimiterMode::PipeCanonical);
            let reparsed = QualityFlagSet::parse_strict(&canonical).unwrap();
            prop_assert_eq!(from_comma, reparsed);
        }

        #[test]
        fn fuzz_parse_strict_never_panics(s in "\\PC*") {
            let _ = QualityFlagSet::parse_strict(&s);
        }
    }
}
