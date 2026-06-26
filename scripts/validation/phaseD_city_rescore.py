"""Phase-D city-anchor re-score (no basis transform — HVAC is metered).

D1: imports CITY_ANCHORS, build_city_table, SEGMENT_ARCHETYPES from v19_rescore.py.
D2: mirrors load_all_cells but reads phaseD single tree.
D3: identity — score raw metered Phase-D EUI; no apply_basis_to_frame.
D4: report TWICE — total_eui_kwh_m2 (fans-excluded) AND total_eui_kwh_m2 + fans_eui_kwh_m2.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.v19_rescore import CITY_ANCHORS, SEGMENT_ARCHETYPES, build_city_table, _df_to_md_table

# V6: all 12 Phase-D cells in a single base dir; S6: env-gate for phaseD2 re-score
_BASE_D = ROOT / "docs" / "validations" / "overAll" / "results" / os.environ.get("OPENUBEM_PHASED_SUBDIR", "phaseD")

_CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre",     "la_rural",     "la_suburban",     "la_urban",
    "nyc_centre",    "nyc_rural",    "nyc_suburban",    "nyc_urban",
]

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}


def load_all_cells_phaseD() -> pd.DataFrame:
    """Read all 12 Phase-D 05_results.gpkg from the single phaseD tree (D2)."""
    missing = []
    frames = []
    for cell in _CELLS:
        gpkg = _BASE_D / cell / "05_results.gpkg"
        if not gpkg.exists():
            missing.append(cell)
            continue
        gdf = gpd.read_file(str(gpkg))
        df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name, errors="ignore"))
        city, density = cell.split("_", 1)
        df["cell"] = cell
        df["city"] = city
        df["density"] = density
        frames.append(df)

    if missing:
        raise FileNotFoundError(f"Missing Phase-D gpkg for cells: {missing}")

    combined = pd.concat(frames, ignore_index=True)
    found = combined["cell"].nunique()
    if found != 12:
        raise AssertionError(f"Expected 12 distinct cells, found {found}")
    return combined


def _alias_for_city_table(df: pd.DataFrame, eui_col: str) -> pd.DataFrame:
    """Alias eui_col → total_eui_reconstructed_kwh_m2 so build_city_table can consume it."""
    out = df.copy()
    out["total_eui_reconstructed_kwh_m2"] = out[eui_col]
    # simulation_status filter inside build_city_table expects startswith("success")
    return out


def run_city_rescore(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (table_fans_out, table_fans_in) per D4.

    table_fans_out: scored on total_eui_kwh_m2 (fans excluded, as-built).
    table_fans_in:  scored on total_eui_kwh_m2 + fans_eui_kwh_m2.
    """
    aliased_out = _alias_for_city_table(df, "total_eui_kwh_m2")
    table_out = build_city_table(aliased_out)

    df_fans_in = df.copy()
    df_fans_in["total_eui_kwh_m2_with_fans"] = (
        df_fans_in["total_eui_kwh_m2"] + df_fans_in["fans_eui_kwh_m2"]
    )
    aliased_in = _alias_for_city_table(df_fans_in, "total_eui_kwh_m2_with_fans")
    table_in = build_city_table(aliased_in)

    return table_out, table_in


def _check_finite(tbl: pd.DataFrame, label: str) -> None:
    """Assert all numeric delta values are finite; report anomalies."""
    for col in ["delta_vs_measured_pct"]:
        if col in tbl.columns:
            bad = tbl[~tbl[col].apply(lambda x: isinstance(x, (int, float)) and x == x)]
            if not bad.empty:
                print(f"  [ANOMALY] {label} has non-finite {col}:\n{bad}")


def main() -> None:
    print("=== Phase-D City-Anchor Re-score ===")

    df = load_all_cells_phaseD()
    print(f"Loaded {len(df)} rows across {df['cell'].nunique()} cells.")

    n_success = df["simulation_status"].isin(_SUCCESS_STATUSES).sum()
    print(f"Success rows: {n_success} / {len(df)}")

    for city in ("nyc", "la", "austin"):
        city_n = len(df[df["city"] == city])
        print(f"  {city}: {city_n} buildings")

    table_fans_out, table_fans_in = run_city_rescore(df)

    print("\n--- Table A: total_eui_kwh_m2 (fans EXCLUDED, as-built) ---")
    _check_finite(table_fans_out, "fans-out")
    print(table_fans_out[["city", "segment", "n", "model_recon_median", "measured",
                           "delta_vs_measured_pct"]].to_string(index=False))

    print("\n--- Table B: total_eui_kwh_m2 + fans_eui_kwh_m2 (fans INCLUDED) ---")
    _check_finite(table_fans_in, "fans-in")
    print(table_fans_in[["city", "segment", "n", "model_recon_median", "measured",
                          "delta_vs_measured_pct"]].to_string(index=False))

    return table_fans_out, table_fans_in


if __name__ == "__main__":
    main()
