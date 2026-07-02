"""Canonical imputation provenance contract (Input-Imputation arc, T01).

Every imputer / silent-default site emits into *this* module so the audit's
Tier-B gap is closed uniformly and no site invents its own token. It EXTENDS the
existing provenance vocabulary — it does not replace it:

  * `provenance_*` column values stay `{ASHRAE_STANDARD, HEURISTIC, KDE_IMPUTED,
    PDE_GENERATED}` (Stage-2.2 DESIGN §12); those are NOT renamed here.
  * `data_quality_flag` stays a `|`-separated multi-token string
    (`construction_sets._FLAG_SEP`); new tokens follow the M09 §3A grammar
    ``{METHOD}_{SOURCE}_{TIER}`` with ``TIER ∈ {HIGH, MED, LOW}``.
  * confidence tiers stay `{HIGH, MEDIUM, LOW}` (as `archetype_confidence`).

Pure functions over scalars / (Geo)DataFrames. Stdlib + numpy + pandas only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Separator for multi-token data_quality_flag (matches construction_sets._FLAG_SEP,
# Step 1/3 convention).
_FLAG_SEP = "|"

# Existing canonical provenance-column values (DESIGN §12) — imported for reference,
# NOT renamed.
CANONICAL_PROVENANCE = ("ASHRAE_STANDARD", "HEURISTIC", "KDE_IMPUTED", "PDE_GENERATED")

# Confidence tiers (align with archetype_confidence ∈ {HIGH, MEDIUM, LOW}).
CONFIDENCE_TIERS = ("HIGH", "MEDIUM", "LOW")

# Canonical tier -> short token suffix (M09 §3A / plan T01 examples use 'MED').
_TIER_SUFFIX = {"HIGH": "HIGH", "MEDIUM": "MED", "LOW": "LOW"}
# Accepted inputs (canonical or short form) -> canonical tier.
_TIER_NORMALIZE = {
    "HIGH": "HIGH", "MEDIUM": "MEDIUM", "MED": "MEDIUM", "LOW": "LOW",
}
# Short suffix -> canonical tier (token parsing).
_SUFFIX_TO_TIER = {"HIGH": "HIGH", "MED": "MEDIUM", "LOW": "LOW"}

# Lineage weights (M09 §3B): HIGH=1.0 / MED=0.5 / LOW=0.1; observed field = 1.0.
CONFIDENCE_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.1}
_OBSERVED_METHOD = "OBSERVED"
_OBSERVED_SCORE = 1.0


# ── token builder / parser (M09 §3A) ─────────────────────────────────────────

def normalize_confidence(confidence: str) -> str:
    """Normalize a tier input ('HIGH'|'MEDIUM'|'MED'|'LOW') to a canonical tier."""
    tier = _TIER_NORMALIZE.get(str(confidence).upper())
    if tier is None:
        raise ValueError(
            f"confidence must be one of {sorted(_TIER_NORMALIZE)}, got {confidence!r}"
        )
    return tier


def impute_token(method: str, source: str, confidence: str) -> str:
    """Build a `{METHOD}_{SOURCE}_{TIER}` data_quality_flag token (M09 §3A).

    e.g. ``impute_token('DEFAULT', 'ASHRAE901', 'LOW') -> 'DEFAULT_ASHRAE901_LOW'``;
    ``impute_token('HOTDECK', 'NEIGHBOR', 'MEDIUM') -> 'HOTDECK_NEIGHBOR_MED'``.
    """
    tier = normalize_confidence(confidence)
    return f"{str(method).upper()}_{str(source).upper()}_{_TIER_SUFFIX[tier]}"


def parse_token(token: str) -> tuple[str, str, str] | None:
    """Inverse of `impute_token`: (METHOD, SOURCE, canonical TIER) or None.

    SOURCE may itself contain underscores (method = first segment, tier = last
    segment, source = everything between).
    """
    parts = str(token).split("_")
    if len(parts) < 3:
        return None
    suffix = parts[-1]
    tier = _SUFFIX_TO_TIER.get(suffix)
    if tier is None:
        return None
    source = "_".join(parts[1:-1])
    if not source:
        return None
    return parts[0], source, tier


# ── data_quality_flag helpers (idempotent `|`-append) ────────────────────────

def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v))


def append_flag_token(existing, token: str) -> str:
    """Idempotently append `token` to a `|`-separated flag string (scalar)."""
    s = "" if _is_missing(existing) else str(existing)
    tokens = [t for t in s.split(_FLAG_SEP) if t]
    if token not in tokens:
        tokens.append(token)
    return _FLAG_SEP.join(tokens)


def append_flag(gdf, token: str, mask=None, col: str = "data_quality_flag"):
    """Idempotently append `token` to `col` for masked rows. Returns a copy."""
    gdf = gdf.copy()
    if col not in gdf.columns:
        gdf[col] = ""
    if mask is None:
        idx = gdf.index
    else:
        idx = gdf.index[mask]
    gdf.loc[idx, col] = gdf.loc[idx, col].map(lambda e: append_flag_token(e, token))
    return gdf


# ── provenance column + confidence setter ────────────────────────────────────

def set_provenance(gdf, field: str, token: str, mask=None,
                   confidence: str | None = None,
                   prov_prefix: str = "provenance_"):
    """Set ``{prov_prefix}{field} = token`` for masked rows; optionally set a
    ``confidence_{field}`` column. Returns a copy.
    """
    gdf = gdf.copy()
    prov_col = f"{prov_prefix}{field}"
    if prov_col not in gdf.columns:
        gdf[prov_col] = ""
    idx = gdf.index if mask is None else gdf.index[mask]
    gdf.loc[idx, prov_col] = token
    if confidence is not None:
        conf_col = f"confidence_{field}"
        if conf_col not in gdf.columns:
            # object dtype so a HIGH/MEDIUM/LOW string can be assigned (not a float NaN column)
            gdf[conf_col] = pd.Series([None] * len(gdf), index=gdf.index, dtype="object")
        gdf.loc[idx, conf_col] = normalize_confidence(confidence)
    return gdf


# ── per-building lineage summary (M09 §3B) ───────────────────────────────────

def _field_score(cell) -> tuple[bool, float]:
    """(is_imputed, field_score) for one provenance-column cell (M09 §3B).

    A `{METHOD}_{SOURCE}_{TIER}` token with METHOD != OBSERVED is an imputed
    field scored by its tier weight; empty / `OBSERVED` / a legacy standards
    value (no tier) is an observed-grade field scored 1.0.
    """
    if _is_missing(cell):
        return False, _OBSERVED_SCORE
    s = str(cell).strip()
    if not s:
        return False, _OBSERVED_SCORE
    parsed = parse_token(s)
    if parsed is None:
        return False, _OBSERVED_SCORE
    method, _source, tier = parsed
    if method == _OBSERVED_METHOD:
        return False, _OBSERVED_SCORE
    return True, CONFIDENCE_WEIGHT[tier]


def add_lineage_summary(gdf, prov_cols=None,
                        count_col: str = "imputed_fields_count",
                        conf_col: str = "mean_imputation_confidence"):
    """Append the M09 §3B per-building lineage summary (once, end of enrichment).

    ``imputed_fields_count`` (int) = number of provenance columns marking an
    imputer fill; ``mean_imputation_confidence`` (float) = mean field score over
    the considered provenance columns (HIGH=1.0/MED=0.5/LOW=0.1, observed=1.0),
    or 1.0 when there are none. By default scans columns named ``provenance_*``
    or ``*_prov``. Returns a copy.
    """
    gdf = gdf.copy()
    if prov_cols is None:
        prov_cols = [c for c in gdf.columns
                     if c.startswith("provenance_") or c.endswith("_prov")]
    n = len(gdf)
    if not prov_cols:
        gdf[count_col] = np.zeros(n, dtype=int)
        gdf[conf_col] = np.full(n, _OBSERVED_SCORE, dtype=float)
        return gdf

    counts = np.zeros(n, dtype=int)
    score_sum = np.zeros(n, dtype=float)
    for c in prov_cols:
        for i, cell in enumerate(gdf[c].tolist()):
            imp, score = _field_score(cell)
            counts[i] += int(imp)
            score_sum[i] += score
    gdf[count_col] = counts
    gdf[conf_col] = score_sum / len(prov_cols)
    return gdf
