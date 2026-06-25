"""Phase-D national CBECS re-score (no basis transform — HVAC is metered).

D1: imports compute_validation_gates from openubem.results.__init__; region refs +
    _CITY_REGION from v19_national_cbecs_rescore.py.
D3: identity — score raw metered Phase-D EUI; no apply_basis_to_frame.
D4: report each region's gates BOTH ways (total_eui fans-excluded AND total_eui+fans).
D5: confirm each city scores against its correct CBECS region file; flag any mismatch.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results import compute_validation_gates
from scripts.validation.v19_national_cbecs_rescore import (
    _CITY_REGION,
    _REPORTS_DIR,
    _SUCCESS_STATUSES,
)
from scripts.validation.phaseD_city_rescore import load_all_cells_phaseD

_REGIONS = ["middle_atlantic", "pacific", "west_south_central"]

# D5: expected region assignment per city (V4)
_EXPECTED_REGION = {
    "nyc":    "middle_atlantic",
    "la":     "pacific",
    "austin": "west_south_central",
}


def load_region_refs() -> dict[str, pd.DataFrame]:
    return {
        region: pd.read_csv(_REPORTS_DIR / f"cbecs_2018_{region}_eui.csv")
        for region in _CITY_REGION.values()
    }


def _check_d5_region_labels(region_refs: dict[str, pd.DataFrame]) -> None:
    """D5: verify each city→region mapping and flag any mismatch."""
    print("\n[D5] Region-label confirmation:")
    all_ok = True
    for city, expected_region in _EXPECTED_REGION.items():
        actual_region = _CITY_REGION.get(city)
        ref_file = _REPORTS_DIR / f"cbecs_2018_{actual_region}_eui.csv"
        file_ok = ref_file.exists()
        match = actual_region == expected_region
        status = "OK" if (match and file_ok) else "MISMATCH"
        if not match or not file_ok:
            all_ok = False
        print(
            f"  {city} -> {actual_region} "
            f"(expected={expected_region}) "
            f"file_exists={file_ok} [{status}]"
        )
    if all_ok:
        print("  D5 PASS: all three cities score against their correct CBECS region file.")
    else:
        print("  D5 FAIL: region mismatch detected (see above).")


def score_city_region(
    df: pd.DataFrame,
    city: str,
    region: str,
    region_refs: dict[str, pd.DataFrame],
    eui_col: str,
) -> dict[str, Any]:
    """Score one city's buildings against its regional CBECS ref."""
    city_df = df[df["city"] == city].copy()
    city_df["eui_kwh_m2"] = city_df[eui_col]  # alias required by compute_validation_gates
    gates = compute_validation_gates(city_df, reference_table=region_refs[region])
    return gates


def run_national_rescore(
    df: pd.DataFrame,
    region_refs: dict[str, pd.DataFrame],
    eui_col: str,
) -> pd.DataFrame:
    """Score each city against its region; return summary DataFrame."""
    rows = []
    for city, region in _CITY_REGION.items():
        gates = score_city_region(df, city, region, region_refs, eui_col)
        rows.append({
            "city":          city,
            "region":        region,
            "eui_col":       eui_col,
            "n":             gates["n_sim_buildings"],
            "nmbe":          gates["cbecs_nmbe"],
            "nmbe_pass":     gates["cbecs_nmbe_pass"],
            "cv_rmse":       gates["cbecs_cv_rmse"],
            "cv_rmse_pass":  gates["cbecs_cv_rmse_pass"],
            "ks_d":          gates["cbecs_ks_d"],
            "ks_d_pass":     gates["cbecs_ks_d_pass"],
            "r2":            gates["cbecs_r2"],
            "r2_pass":       gates["cbecs_r2_pass"],
            "n_excluded":    gates["n_excluded_all_gates"],
        })
    return pd.DataFrame(rows)


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("=== Phase-D National CBECS Re-score ===")

    df_all = load_all_cells_phaseD()
    success_df = df_all[df_all["simulation_status"].isin(_SUCCESS_STATUSES)].copy()
    print(f"Success rows: {len(success_df)} / {len(df_all)}")

    region_refs = load_region_refs()

    _check_d5_region_labels(region_refs)

    # D4: fans-excluded (as-built)
    table_fans_out = run_national_rescore(success_df, region_refs, "total_eui_kwh_m2")

    # D4: fans-included
    success_df_with_fans = success_df.copy()
    success_df_with_fans["total_eui_with_fans"] = (
        success_df_with_fans["total_eui_kwh_m2"] + success_df_with_fans["fans_eui_kwh_m2"]
    )
    table_fans_in = run_national_rescore(success_df_with_fans, region_refs, "total_eui_with_fans")

    print("\n--- Table C: national gates on total_eui_kwh_m2 (fans EXCLUDED) ---")
    print(table_fans_out[["city", "region", "n", "nmbe", "nmbe_pass",
                           "cv_rmse", "cv_rmse_pass", "ks_d", "ks_d_pass",
                           "r2", "r2_pass"]].to_string(index=False))

    print("\n--- Table D: national gates on total_eui + fans_eui (fans INCLUDED) ---")
    print(table_fans_in[["city", "region", "n", "nmbe", "nmbe_pass",
                          "cv_rmse", "cv_rmse_pass", "ks_d", "ks_d_pass",
                          "r2", "r2_pass"]].to_string(index=False))

    return table_fans_out, table_fans_in


if __name__ == "__main__":
    main()
