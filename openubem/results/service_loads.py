"""Reporting-layer service-loads reconstruction (REPORT §R6-4B).

Adds the 5 un-modeled end-uses (vent_fans, pumps, swh_dhw, refrig, cooking_other)
back as a deterministic post-processing layer.  The simulated 05_results are never
modified; reconstruction writes only new columns.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

_DATA = Path(__file__).parent.parent / "data" / "service_loads" / "enduse_fractions_table4.json"

_MODELED_COLS = ("heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2", "equipment_eui_kwh_m2")
_MODELED_FRAC_KEYS = ("space_heat", "space_cool", "lighting", "equip_plug")
_RECON_KEYS = ("vent_fans", "pumps", "swh_dhw", "refrig", "cooking_other")

_RUNTIME_BASE = Path(__file__).resolve().parents[2] / "runtime" / "ubem_validation" / "cases"


def load_coefficients(path: "Path | None" = None) -> dict:
    """Load and validate enduse_fractions_table4.json.

    Asserts every archetype's fractions sum to 1.0 ± 1e-3.
    Returns {"fractions": ..., "archetype_map": ...}.
    """
    p = Path(path) if path is not None else _DATA
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    for key, fracs in data["fractions"].items():
        total = sum(fracs.values())
        if abs(total - 1.0) >= 1e-3:
            raise ValueError(f"Fractions for '{key}' sum to {total:.6f}, expected 1.0 ± 1e-3")
    return data


def reconstruct_building(row: "pd.Series | dict[str, Any]", coeffs: dict) -> dict:
    """Reconstruct the 5 missing end-uses for a single building row.

    Returns the 9 new provenance + reconstruction columns.
    Passthrough (zeros) when archetype unmapped, status non-success, or modeled_frac==0.
    """
    _passthrough = {
        "reconstruction_applied": False,
        "archetype_mapped_to": "passthrough",
        "reconstruction_basis": "",
        "vent_fans_eui_recon_kwh_m2": 0.0,
        "pumps_eui_recon_kwh_m2": 0.0,
        "swh_dhw_eui_recon_kwh_m2": 0.0,
        "refrig_eui_recon_kwh_m2": 0.0,
        "cooking_other_eui_recon_kwh_m2": 0.0,
        "total_eui_reconstructed_kwh_m2": float(row["total_eui_kwh_m2"]) if "total_eui_kwh_m2" in (row if isinstance(row, dict) else row.index) else 0.0,
    }

    def _get(key: str, default=None):
        if isinstance(row, dict):
            return row.get(key, default)
        return row[key] if key in row.index else default

    status = _get("simulation_status", "")
    if not isinstance(status, str) or not status.startswith("success"):
        return _passthrough

    archetype_id = _get("archetype_id", "")
    table4_key = coeffs["archetype_map"].get(archetype_id)
    if table4_key is None or table4_key == "passthrough":
        result = dict(_passthrough)
        result["archetype_mapped_to"] = "passthrough"
        return result

    fracs = coeffs["fractions"][table4_key]
    modeled_frac = sum(fracs[k] for k in _MODELED_FRAC_KEYS)
    if modeled_frac <= 0:
        return _passthrough

    heating = float(_get("heating_eui_kwh_m2", 0.0))
    cooling = float(_get("cooling_eui_kwh_m2", 0.0))
    lighting = float(_get("lighting_eui_kwh_m2", 0.0))
    equipment = float(_get("equipment_eui_kwh_m2", 0.0))
    total_sim = float(_get("total_eui_kwh_m2", 0.0))

    E_total_est = (heating + cooling + lighting + equipment) / modeled_frac

    recon = {k: fracs[k] * E_total_est for k in _RECON_KEYS}
    total_recon = total_sim + sum(recon.values())

    return {
        "reconstruction_applied": True,
        "archetype_mapped_to": table4_key,
        "reconstruction_basis": "table4_fraction_split",
        "vent_fans_eui_recon_kwh_m2": recon["vent_fans"],
        "pumps_eui_recon_kwh_m2": recon["pumps"],
        "swh_dhw_eui_recon_kwh_m2": recon["swh_dhw"],
        "refrig_eui_recon_kwh_m2": recon["refrig"],
        "cooking_other_eui_recon_kwh_m2": recon["cooking_other"],
        "total_eui_reconstructed_kwh_m2": total_recon,
    }


def reconstruct_frame(df: pd.DataFrame, coeffs: dict | None = None) -> pd.DataFrame:
    """Apply reconstruct_building across a DataFrame; adds reconstruction columns.

    Logs distinct unmapped archetype_ids once.  Input df is not mutated.
    """
    if coeffs is None:
        coeffs = load_coefficients()
    df = df.copy()

    results = df.apply(lambda r: pd.Series(reconstruct_building(r, coeffs)), axis=1)
    for col in results.columns:
        df[col] = results[col]

    unmapped = df.loc[
        df.get("reconstruction_applied", pd.Series(False, index=df.index)) == False,
        "archetype_id"
    ] if "archetype_id" in df.columns else pd.Series(dtype=str)
    distinct = set(unmapped.dropna().unique()) if len(unmapped) else set()
    if distinct:
        logger.warning("Unmapped archetype_ids (passthrough, no reconstruction): %s", sorted(distinct))

    return df


def reconstruct_cell(cell_name: str) -> pd.DataFrame:
    """Load 05_results.gpkg for a cell, run reconstruction, add 'cell' column.

    Raises FileNotFoundError if the cell results are absent.
    Returns a plain DataFrame (geometry dropped).
    """
    gpkg_path = _RUNTIME_BASE / cell_name / "results" / "05_results.gpkg"
    if not gpkg_path.exists():
        raise FileNotFoundError(f"No results for cell {cell_name!r}: {gpkg_path}")

    gdf = gpd.read_file(str(gpkg_path))
    df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name, errors="ignore"))

    coeffs = load_coefficients()
    df = reconstruct_frame(df, coeffs)
    df["cell"] = cell_name
    return df
