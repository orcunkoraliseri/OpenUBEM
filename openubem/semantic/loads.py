"""Module 05: Loads lookup and frame-level merge (DESIGN §3D)."""
from __future__ import annotations

import importlib.resources
import json
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_LOADS_TABLE: dict | None = None
_OS_TABLE: dict | None = None
_SPACE_TYPE_TABLE: dict | None = None


def _load_json(pkg_path: str, fname: str) -> dict:
    pkg = importlib.resources.files(pkg_path)
    return json.loads((pkg / fname).read_text(encoding="utf-8"))


def _get_loads_table() -> dict:
    global _LOADS_TABLE
    if _LOADS_TABLE is None:
        _LOADS_TABLE = _load_json("openubem.data.loads", "doe_prototype_loads.json")
    return _LOADS_TABLE


def _get_os_table() -> dict:
    global _OS_TABLE
    if _OS_TABLE is None:
        _OS_TABLE = _load_json("openubem.data.loads", "openstudio_loads.json")
    return _OS_TABLE


def get_space_type_loads(archetype_id: str) -> dict | None:
    """Per-space-type intensity table for a units+corridor archetype (or None).

    Returns {space_type: {lighting_w_m2, equipment_w_m2, has_occupancy}} used by
    layoutGenerator room_layout zones. Intensities are relative; assign_loads
    alpha-normalizes them to conserve the archetype-average building totals.
    """
    global _SPACE_TYPE_TABLE
    if _SPACE_TYPE_TABLE is None:
        _SPACE_TYPE_TABLE = _load_json("openubem.data.loads", "doe_space_type_loads.json")
    entry = _SPACE_TYPE_TABLE.get(archetype_id)
    return entry["space_types"] if entry else None


def _build_flat_loads(custom_table: dict | None = None) -> pd.DataFrame:
    """
    Merge DOE (16 rows) and OS-extended (13 rows) tables into a single
    flat DataFrame keyed by archetype_id (29 total, no duplicates).
    DOE rows take priority over OS rows for the same archetype.
    Renames JSON field names to canonical GDF column names.
    If custom_table is provided, it is used instead of the bundled tables.
    """
    if custom_table is not None:
        all_rows = [{"archetype_id": arch, **vals} for arch, vals in custom_table.items()]
        df = pd.DataFrame(all_rows).set_index("archetype_id")
        df = df.rename(columns=_JSON_TO_CANONICAL)
        df = df.drop(columns=["source"], errors="ignore")
        return df

    doe = _get_loads_table()
    os_ = _get_os_table()

    all_rows = []
    seen = set()
    for arch, vals in doe.items():
        row = {"archetype_id": arch, **vals}
        all_rows.append(row)
        seen.add(arch)
    for arch, vals in os_.items():
        if arch not in seen:
            row = {"archetype_id": arch, **vals}
            all_rows.append(row)
            seen.add(arch)

    df = pd.DataFrame(all_rows).set_index("archetype_id")
    df = df.rename(columns=_JSON_TO_CANONICAL)
    # Drop source column if present
    df = df.drop(columns=["source"], errors="ignore")
    return df


_FLAT_LOADS: pd.DataFrame | None = None


def _get_flat_loads(custom_table: dict | None = None) -> pd.DataFrame:
    global _FLAT_LOADS
    if custom_table is not None:
        return _build_flat_loads(custom_table)
    if _FLAT_LOADS is None:
        _FLAT_LOADS = _build_flat_loads()
    return _FLAT_LOADS


_LOADS_PROV_COLS = [
    "provenance_lighting", "provenance_equipment", "provenance_occupant_density",
    "provenance_heating_setpoint", "provenance_cooling_setpoint",
    "provenance_wwr",
]

# Canonical column names per DESIGN §3G F17 (exact 28-column order)
_LOADS_VALUE_COLS = [
    "lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person",
    "heating_setpoint_c", "cooling_setpoint_c",
    "heating_setback_c", "cooling_setup_c",
    "wwr",
]

# Rename map: JSON field name → canonical GDF column name (C2: lighting/equipment keep their names)
_JSON_TO_CANONICAL = {
    "occupant_density_m2_person": "occupant_m2_per_person",
}


def get_loads(gdf: pd.DataFrame, custom_table: dict | None = None) -> pd.DataFrame:
    """
    Vectorized loads merge keyed on archetype_id (DESIGN §3D / F9).

    Returns DataFrame with 8 load columns + 6 provenance columns, index-aligned
    with gdf. Missing archetype rows raise ValueError (bundled table is gap-free
    for all 29 archetypes; OpenUBEMUnknown handled separately by caller).
    custom_table: optional synthetic dict (same shape as doe_prototype_loads.json) for tests.
    """
    flat = _get_flat_loads(custom_table)
    result = gdf[["archetype_id"]].copy()
    result = result.merge(
        flat[_LOADS_VALUE_COLS].reset_index(),
        on="archetype_id",
        how="left",
    )
    result.index = gdf.index

    # Gap check — all 29 archetypes must resolve
    gap_mask = result["lighting_w_m2"].isna()
    if gap_mask.any():
        missing = gdf.loc[gap_mask, "archetype_id"].unique().tolist()
        raise ValueError(
            f"Loads table gap: no row for archetype(s) {missing}. "
            "Add them to doe_prototype_loads.json or openstudio_loads.json."
        )

    # Provenance
    for col in _LOADS_PROV_COLS:
        result[col] = "ASHRAE_STANDARD"

    # Setpoint inversion guard (DESIGN §3D / F15)
    bad = result["heating_setpoint_c"] >= result["cooling_setpoint_c"]
    if bad.any():
        raise ValueError(
            f"Setpoint inversion at rows {result.index[bad].tolist()}: "
            "heating_setpoint_c >= cooling_setpoint_c"
        )

    keep = _LOADS_VALUE_COLS + _LOADS_PROV_COLS
    return result[keep]
