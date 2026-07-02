"""Module 04: Vintage resolution and envelope lookup (DESIGN §3B–§3C)."""
from __future__ import annotations

import importlib.resources
import json
import logging
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from openubem.config import RANDOM_SEED

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ── VINTAGE_U_FACTORS ────────────────────────────────────────────────────────
# Committed per §5-R R-2.2-6 (PLAN, 2026-06-10).
# Derived as median ratio U_edition/U_2019 across 16 sub-zones ×
# {ExteriorRoof/IEAD, ExteriorWall/SteelFramed, ExteriorWall/Mass, ExteriorWindow/Fixed}
# Nonresidential from NREL/openstudio-standards commit 83b1e64.
# Source of truth: openubem/data/construction/PROVENANCE.md.
VINTAGE_U_FACTORS: dict[str, float] = {
    "DOERefPre1980":    1.6,     # spec-mandated (DESIGN §3C / Technical Pipeline §5)
    "DOERef1980to2004": 1.583,   # extracted median, n=64 sub-zone pairs
    "90.1-2007":        1.309,   # extracted median, n=32
    "90.1-2010":        1.309,   # extracted median, n=32 (tie with 2007 accepted R-2.2-6)
    "90.1-2013":        1.0,     # extracted median, n=32 (tie with 2019 accepted R-2.2-6)
    "90.1-2016":        1.0,     # extracted median, n=32 (tie with 2013 accepted R-2.2-6)
    "90.1-2019":        1.0,     # baseline
}

_VINTAGE_BIN_LABELS = (
    "DOERefPre1980",
    "DOERef1980to2004",
    "90.1-2007",
    "90.1-2013",
    "90.1-2019",
)

# NaN year_built flag token (DESIGN §3B / F4)
_VINTAGE_NAN_TOKEN = "VINTAGE_NAN_PERMISSIVE_DEFAULT"
_FLAG_SEP = "|"  # separator for multi-token data_quality_flag (matches Step 1/3 convention)

# Donor-tier provenance tokens (Input-Imputation arc T04, PINNED CONTRACT v2).
# Literal per §6 T04 -- tier 1 from T06 knn_fill's own HIGH/MEDIUM confidence tier,
# tier 2 is a flat MED (group-wise mode), tier 3 keeps the legacy LOW token above.
_HOTDECK_NEIGHBOR_HIGH = "HOTDECK_NEIGHBOR_HIGH"
_HOTDECK_NEIGHBOR_MED = "HOTDECK_NEIGHBOR_MED"
_GROUPMODE_MED = "GROUPMODE_MED"


# ── Table loading ─────────────────────────────────────────────────────────────

def _load_table(json_name: str) -> dict:
    """Load a bundled JSON from openubem/data/construction/."""
    pkg = importlib.resources.files("openubem.data.construction")
    return json.loads((pkg / json_name).read_text(encoding="utf-8"))


_ASHRAE_TABLE: dict | None = None


def _get_ashrae_table() -> dict:
    global _ASHRAE_TABLE
    if _ASHRAE_TABLE is None:
        _ASHRAE_TABLE = _load_table("ashrae_90_1_2019.json")
    return _ASHRAE_TABLE


# ── Flattened lookup DataFrame ─────────────────────────────────────────────────

def _build_flat_lookup(table: dict, table_name: str = "ashrae_90_1_2019") -> pd.DataFrame:
    """
    Flatten the JSON table into a lookup DataFrame keyed
    (lookup_table, archetype_id, climate_zone) → 8 envelope columns.
    One-time operation per table; result is cached.
    """
    rows = []
    for arch, zones in table.items():
        for cz, vals in zones.items():
            rows.append({
                "lookup_table":       table_name,
                "archetype_id":       arch,
                "climate_zone":       cz,
                "u_roof_w_m2k":       vals["roof"]["u_value"],
                "assembly_roof":      vals["roof"]["assembly"],
                "u_wall_w_m2k":       vals["wall"]["u_value"],
                "assembly_wall":      vals["wall"]["assembly"],
                "u_window_w_m2k":     vals["window"]["u_value"],
                "shgc_window":        vals["window"]["shgc"],
                "u_floor_w_m2k":      vals["floor"]["u_value"],
                "infiltration_m3_s_m2": vals["infiltration_rate"],
            })
    return pd.DataFrame(rows)


_FLAT_LOOKUP: pd.DataFrame | None = None


def _get_flat_lookup(custom_table: dict | None = None) -> pd.DataFrame:
    global _FLAT_LOOKUP
    if custom_table is not None:
        return _build_flat_lookup(custom_table)
    if _FLAT_LOOKUP is None:
        _FLAT_LOOKUP = _build_flat_lookup(_get_ashrae_table())
    return _FLAT_LOOKUP


# ── Vintage resolution (T06) ──────────────────────────────────────────────────

_YEAR_BINS = [1980, 2004, 2010, 2016]
_YEAR_LABELS = [
    "DOERefPre1980",    # < 1980 or NaN
    "DOERef1980to2004", # [1980, 2004)
    "90.1-2007",        # [2004, 2010)
    "90.1-2013",        # [2010, 2016)
    "90.1-2019",        # [2016, ∞)
]


def resolve_vintage(gdf: pd.DataFrame) -> tuple[pd.Series, pd.Index, pd.Series]:
    """
    Map year_built → vintage_standard token per DESIGN §3B (F3/F4), with a
    three-tier donor fill on NaN year_built rows before the oldest-default
    (Input-Imputation arc T04, PINNED CONTRACT v2 — position-stable):

      1. Spatial neighbour donor (T06 ``spatial_impute.knn_fill``), stratified by
         ``use_class`` if present else ``archetype_id``; donors are observed-year
         rows only (leakage-safe); MNAR-guarded (T06's own >=60% local-missingness
         block routes the row to tier 2).
      2. Group-wise mode of observed vintage bins in the same stratum.
      3. Last-resort oldest-default (``DOERefPre1980``), unchanged legacy behaviour.

    Returns:
        vintage_series: Series of vintage tokens (str), index-aligned with gdf.
            Originally-NaN rows now carry the tier-1/tier-2 donor fill (re-binned
            via `_YEAR_BINS`/`_YEAR_LABELS`) when a donor exists; tier-3 rows keep
            `DOERefPre1980` (byte-identical to pre-T04 behaviour).
        nan_rows:       Index of EVERY row where year_built was originally NaN
            (position-1, unchanged meaning from pre-T04 -- env provenances are
            still HEURISTIC for all of these regardless of donor tier).
        vintage_prov:   Series[str] of the per-row provenance token (position-2,
            previously an unused duplicate of `nan_rows`), indexed over `nan_rows`:
            `HOTDECK_NEIGHBOR_HIGH` / `HOTDECK_NEIGHBOR_MED` (tier 1), `GROUPMODE_MED`
            (tier 2), or `VINTAGE_NAN_PERMISSIVE_DEFAULT` (tier 3, the legacy token).
    """
    year = gdf["year_built"].copy()
    nan_mask = year.isna()
    all_nan_rows = gdf.index[nan_mask]

    # pd.cut: right=False gives half-open [left, right) bins
    vintage = pd.cut(
        year.fillna(-1).astype(float),  # NaN → -1 → falls below 1980 → Pre1980 placeholder
        bins=[-np.inf] + _YEAR_BINS + [np.inf],
        labels=_YEAR_LABELS,
        right=False,
        ordered=False,
    ).astype(str)
    vintage[nan_mask] = "DOERefPre1980"  # tier-3 placeholder; may be overwritten by a donor below

    vintage_prov: pd.Series = pd.Series(index=all_nan_rows, dtype=object)
    if len(all_nan_rows) == 0:
        return vintage, all_nan_rows, vintage_prov

    if "use_class" in gdf.columns:
        strat_col = "use_class"
    elif "archetype_id" in gdf.columns:
        strat_col = "archetype_id"
    else:
        # No stratifier available: do not vote across all uses (STOP condition (a)
        # is a manager-verified precondition -- __init__.py:307 always has
        # archetype_id -- this branch is a defensive no-op fallback, not the
        # expected production path).
        vintage_prov.loc[:] = _VINTAGE_NAN_TOKEN
        return vintage, all_nan_rows, vintage_prov

    still_nan = pd.Series(True, index=all_nan_rows)

    # ── Tier 1: spatial neighbour donor (T06, leakage-safe, MNAR-guarded) ─────
    # Only meaningful on a geometry-bearing frame; plain DataFrame callers (unit
    # tests) fall straight through to tier 2/3.
    has_geometry = hasattr(gdf, "geometry") and "geometry" in getattr(gdf, "columns", [])
    if has_geometry:
        from openubem.semantic.spatial_impute import knn_fill

        for _stratum_value, group in gdf.groupby(strat_col, dropna=False):
            group_idx = group.index
            nan_in_group = group_idx.intersection(all_nan_rows)
            if len(nan_in_group) == 0:
                continue
            s_value, _s_dispersion, s_confidence, _gdf_out = knn_fill(group, "year_built")
            for idx in nan_in_group:
                conf = s_confidence.loc[idx]
                val = s_value.loc[idx]
                if conf in ("HIGH", "MEDIUM") and pd.notna(val):
                    binned = pd.cut(
                        pd.Series([float(val)]),
                        bins=[-np.inf] + _YEAR_BINS + [np.inf],
                        labels=_YEAR_LABELS,
                        right=False,
                        ordered=False,
                    ).astype(str).iloc[0]
                    vintage.loc[idx] = binned
                    vintage_prov.loc[idx] = (
                        _HOTDECK_NEIGHBOR_HIGH if conf == "HIGH" else _HOTDECK_NEIGHBOR_MED
                    )
                    still_nan.loc[idx] = False

    # ── Tier 2: group-wise mode (same stratifier, observed rows only) ─────────
    remaining = still_nan[still_nan].index
    if len(remaining) > 0:
        observed_idx = gdf.index[~nan_mask]
        if len(observed_idx) > 0:
            obs = pd.DataFrame(
                {
                    "_stratum": gdf.loc[observed_idx, strat_col].values,
                    "_vintage": vintage.loc[observed_idx].values,
                },
                index=observed_idx,
            )
            rng = np.random.default_rng(RANDOM_SEED)
            mode_lookup: dict = {}
            for stratum_value, group in obs.groupby("_stratum", dropna=False):
                counts = group["_vintage"].value_counts()
                top = counts.max()
                winners = counts[counts == top].index.to_numpy()
                winner = (
                    winners[0] if len(winners) == 1
                    else winners[int(rng.integers(len(winners)))]
                )
                mode_lookup[stratum_value] = winner

            for idx in remaining:
                stratum_value = gdf.at[idx, strat_col]
                if stratum_value in mode_lookup:
                    vintage.loc[idx] = mode_lookup[stratum_value]
                    vintage_prov.loc[idx] = _GROUPMODE_MED
                    still_nan.loc[idx] = False

    # ── Tier 3: oldest-default (legacy LOW token, unchanged) ───────────────────
    remaining = still_nan[still_nan].index
    if len(remaining) > 0:
        vintage.loc[remaining] = "DOERefPre1980"
        vintage_prov.loc[remaining] = _VINTAGE_NAN_TOKEN

    return vintage, all_nan_rows, vintage_prov


# ── Envelope merge (T07) ───────────────────────────────────────────────────────

_PROV_COLS = [
    "provenance_u_roof", "provenance_u_wall", "provenance_u_window",
    "provenance_u_floor", "provenance_infiltration",
]
_ENVELOPE_VALUE_COLS = [
    "u_roof_w_m2k", "assembly_roof", "u_wall_w_m2k", "assembly_wall",
    "u_window_w_m2k", "shgc_window", "u_floor_w_m2k", "infiltration_m3_s_m2",
]


def get_construction_set(
    gdf: pd.DataFrame,
    vintage_series: pd.Series,
    custom_table: dict | None = None,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """
    Vectorized envelope merge (DESIGN §3C / F5/F7/F8).

    For each row: look up (archetype_id, climate_zone) in the flattened 90.1-2019
    baseline table, then apply VINTAGE_U_FACTORS[vintage] to u-values.
    SHGC and infiltration are vintage-invariant (DESIGN §3C / F5).
    Assembly labels do not change with vintage.

    Gap guard: if a (archetype_id, climate_zone) entry is missing from the table
    (can only happen for custom tables — bundled table is gap-free), fill via KDE
    over sibling-zone entries for the same archetype (DESIGN §3C / F8).

    Returns DataFrame with the 8 envelope value columns + 5 provenance columns
    + 'vintage_standard', index-aligned with gdf.
    """
    flat = _get_flat_lookup(custom_table)
    lkp = flat.copy()
    lkp = lkp.rename(columns={"archetype_id": "archetype_id", "climate_zone": "climate_zone"})

    merged = gdf[["archetype_id", "climate_zone"]].copy()
    merged["_vintage"] = vintage_series

    result = merged.merge(
        lkp[["archetype_id", "climate_zone"] + _ENVELOPE_VALUE_COLS],
        on=["archetype_id", "climate_zone"],
        how="left",
    )
    result.index = gdf.index

    # Detect gaps
    gap_mask = result["u_roof_w_m2k"].isna()
    if gap_mask.any():
        gap_archs = gdf.loc[gap_mask, "archetype_id"].unique()
        for arch in gap_archs:
            arch_mask = gap_mask & (gdf["archetype_id"] == arch)
            warnings.warn(
                json.dumps({
                    "event": "construction_lookup_gap",
                    "archetype": arch,
                    "zones": gdf.loc[arch_mask, "climate_zone"].tolist(),
                }),
                stacklevel=2,
            )
            # KDE fill from sibling-zone entries
            sibling_rows = flat[flat["archetype_id"] == arch]
            for col in _ENVELOPE_VALUE_COLS:
                if pd.api.types.is_numeric_dtype(sibling_rows[col]):
                    from openubem.semantic.imputation import impute_column
                    sibling_vals = sibling_rows[col].dropna()
                    if len(sibling_vals) > 0:
                        gap_col = result.loc[arch_mask, col]
                        filled = impute_column(
                            gap_col,
                            method="kde",
                            bounds=(sibling_vals.min(), sibling_vals.max()),
                            rng=rng,
                        )
                        result.loc[arch_mask, col] = filled

    # Apply vintage U-factor (U-values only; SHGC + infiltration unchanged)
    u_cols = ["u_roof_w_m2k", "u_wall_w_m2k", "u_window_w_m2k", "u_floor_w_m2k"]
    for idx in result.index:
        vt = result.at[idx, "_vintage"] if "_vintage" in result.columns else vintage_series.at[idx]
        f = VINTAGE_U_FACTORS.get(str(merged.at[idx, "_vintage"]), 1.0)
        for col in u_cols:
            result.at[idx, col] = round(result.at[idx, col] * f, 3)

    # Provenance assignment
    nan_rows = gdf.index[vintage_series == "DOERefPre1980"][
        gdf.loc[vintage_series == "DOERefPre1980", "year_built"].isna().values
    ] if "year_built" in gdf.columns else pd.Index([])
    # More robust: nan flag was already set by caller via nan_vintage_rows
    # Provenance = ASHRAE_STANDARD by default; HEURISTIC for NaN-vintage rows
    for col in _PROV_COLS:
        result[col] = "ASHRAE_STANDARD"
    # Overwrite gap-filled rows to KDE_IMPUTED
    if gap_mask.any():
        for col in _PROV_COLS:
            result.loc[gap_mask, col] = "KDE_IMPUTED"

    result["vintage_standard"] = vintage_series

    keep_cols = ["vintage_standard"] + _ENVELOPE_VALUE_COLS + _PROV_COLS
    return result[keep_cols]


def apply_nan_vintage_provenance(
    envelope_df: pd.DataFrame,
    nan_vintage_rows: pd.Index,
) -> pd.DataFrame:
    """Set envelope provenances to HEURISTIC for NaN-year_built rows (DESIGN F4)."""
    if len(nan_vintage_rows) > 0:
        for col in _PROV_COLS:
            envelope_df.loc[nan_vintage_rows, col] = "HEURISTIC"
    return envelope_df


def append_vintage_nan_flag(
    gdf: pd.DataFrame,
    nan_vintage_rows: pd.Index,
) -> pd.DataFrame:
    """Append VINTAGE_NAN_PERMISSIVE_DEFAULT to data_quality_flag for NaN year_built rows."""
    if len(nan_vintage_rows) == 0:
        return gdf
    gdf = gdf.copy()
    existing = gdf.loc[nan_vintage_rows, "data_quality_flag"].fillna("").astype(str)
    # Append token once (idempotent guard)
    needs_token = ~existing.str.contains(_VINTAGE_NAN_TOKEN, regex=False)
    existing_with_token = existing.copy()
    existing_with_token[needs_token & (existing[needs_token] == "")] = _VINTAGE_NAN_TOKEN
    existing_with_token[needs_token & (existing[needs_token] != "")] = (
        existing[needs_token & (existing[needs_token] != "")] + _FLAG_SEP + _VINTAGE_NAN_TOKEN
    )
    gdf.loc[nan_vintage_rows, "data_quality_flag"] = existing_with_token
    return gdf


def append_vintage_donor_flags(
    gdf: pd.DataFrame,
    vintage_prov: pd.Series,
) -> pd.DataFrame:
    """Append each row's per-row donor/tier provenance token (T04 v2, position-2
    of `resolve_vintage`) to `data_quality_flag`, via the same idempotent
    `_FLAG_SEP`-guarded append logic as `append_vintage_nan_flag` (substring
    guard against duplicate append, `|`-joined). `vintage_prov` is indexed over
    the originally-NaN `year_built` rows; tier-3 rows carry the legacy
    `VINTAGE_NAN_PERMISSIVE_DEFAULT` token unchanged, tier-1/tier-2 rows carry
    `HOTDECK_NEIGHBOR_HIGH`/`HOTDECK_NEIGHBOR_MED`/`GROUPMODE_MED`.
    """
    if len(vintage_prov) == 0:
        return gdf
    gdf = gdf.copy()
    idx = vintage_prov.index
    existing = gdf.loc[idx, "data_quality_flag"].fillna("").astype(str)

    def _append_once(current: str, token: str) -> str:
        if token in current:
            return current
        return token if current == "" else current + _FLAG_SEP + token

    updated = pd.Series(
        [_append_once(cur, str(tok)) for cur, tok in zip(existing, vintage_prov)],
        index=idx,
        dtype=object,
    )
    gdf.loc[idx, "data_quality_flag"] = updated
    return gdf
