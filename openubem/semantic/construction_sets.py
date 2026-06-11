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


def resolve_vintage(gdf: pd.DataFrame) -> tuple[pd.Series, pd.Index, pd.Index]:
    """
    Map year_built → vintage_standard token per DESIGN §3B (F3/F4).

    Returns:
        vintage_series:    Series of vintage tokens (str), index-aligned with gdf.
        nan_rows:          Index of rows where year_built was NaN (get flag token).
        heuristic_mask:    Same as nan_rows (env provenances = HEURISTIC for these).
    """
    year = gdf["year_built"].copy()
    nan_mask = year.isna()

    # pd.cut: right=False gives half-open [left, right) bins
    vintage = pd.cut(
        year.fillna(-1).astype(float),  # NaN → -1 → falls below 1980 → Pre1980
        bins=[-np.inf] + _YEAR_BINS + [np.inf],
        labels=_YEAR_LABELS,
        right=False,
        ordered=False,
    ).astype(str)

    # NaN rows already map to DOERefPre1980 (fill value -1 < 1980) — confirm
    vintage[nan_mask] = "DOERefPre1980"

    return vintage, gdf.index[nan_mask], gdf.index[nan_mask]


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
