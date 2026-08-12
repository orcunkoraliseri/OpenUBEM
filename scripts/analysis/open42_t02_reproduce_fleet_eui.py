"""OPEN-42 T02 step 1: reproduce the adopted 158.0 kWh/m^2 fleet figure from the
phaseE_elevrb per-cell 05_results.csv files. Measurement only, no writes to those files.

Formula under test (per openubem/results/aggregator.py compute_neighbourhood_summary):
    floor_area = footprint_area_m2 * derive_num_floors(row)   (levels if present, else height_m/3.5, else 1)
    per-cell weighted EUI = Sum(total_eui_kwh_m2 * floor_area) / Sum(floor_area), success rows only
    fleet-weighted EUI    = Sum over all 12 cells of (total_eui_kwh_m2 * floor_area) / Sum over all 12 cells of floor_area
    (i.e. the SAME area-weighted-mean formula applied once across the pooled fleet, not a mean of the 12 cell numbers)
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}


def derive_num_floors(row: pd.Series, floor_to_floor_m: float = 3.5) -> int:
    if pd.notna(row["levels"]):
        return max(1, int(row["levels"]))
    if pd.notna(row["height_m"]):
        return max(1, math.ceil(row["height_m"] / floor_to_floor_m))
    return 1


def main() -> None:
    frames = []
    per_cell_rows = []
    for cell in CELLS:
        csv_path = RESULTS_DIR / cell / "05_results.csv"
        df = pd.read_csv(csv_path)
        df["cell"] = cell
        df["_floor_area"] = df.apply(derive_num_floors, axis=1) * df["footprint_area_m2"]
        frames.append(df)

        succ = df[df["simulation_status"].isin(_SUCCESS_STATUSES)]
        fa = succ["_floor_area"].sum()
        weighted = (succ["total_eui_kwh_m2"] * succ["_floor_area"]).sum() / fa if fa > 0 else float("nan")
        per_cell_rows.append({
            "cell": cell,
            "n_total": len(df),
            "n_success": len(succ),
            "floor_area_m2": fa,
            "weighted_total_eui": weighted,
        })

    fleet = pd.concat(frames, ignore_index=True)
    print(f"fleet total rows: {len(fleet)}")

    success = fleet[fleet["simulation_status"].isin(_SUCCESS_STATUSES)]
    print(f"fleet success rows: {len(success)}")

    # Aggregation A: pooled area-weighted mean across all 8,160 buildings (same formula as per-cell, applied once)
    total_fa = success["_floor_area"].sum()
    fleet_weighted_pooled = (success["total_eui_kwh_m2"] * success["_floor_area"]).sum() / total_fa
    print(f"\nAggregation A - pooled area-weighted mean (Sum(EUI*area)/Sum(area) over all success buildings):")
    print(f"  {fleet_weighted_pooled:.4f} kWh/m2")

    # Aggregation B: floor-area-weighted mean OF THE 12 CELL NUMBERS (weight = each cell's own success floor area)
    per_cell_df = pd.DataFrame(per_cell_rows)
    fleet_weighted_of_cells = (per_cell_df["weighted_total_eui"] * per_cell_df["floor_area_m2"]).sum() / per_cell_df["floor_area_m2"].sum()
    print(f"\nAggregation B - floor-area-weighted mean of the 12 per-cell weighted numbers:")
    print(f"  {fleet_weighted_of_cells:.4f} kWh/m2")
    print("  (mathematically identical to A when using the same floor_area definition; shown for verification)")

    # Aggregation C: unweighted mean of the 12 cell numbers, for comparison/rule-out
    simple_mean_of_cells = per_cell_df["weighted_total_eui"].mean()
    print(f"\nAggregation C - simple (unweighted) mean of the 12 cell numbers (rule-out): {simple_mean_of_cells:.4f} kWh/m2")

    # Aggregation D: mean-of-per-building-EUI (not floor-area-weighted) fleet-wide, for comparison/rule-out
    mean_of_building_eui = success["total_eui_kwh_m2"].mean()
    print(f"\nAggregation D - mean of per-building EUI, unweighted (rule-out): {mean_of_building_eui:.4f} kWh/m2")

    print("\nPer-cell table:")
    print(per_cell_df.to_string(index=False))

    out_path = ROOT / "openubem" / "outputs" / "comparisons" / "open42_t02_percell_repro.csv"
    per_cell_df.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")

    print(f"\nTarget (adopted, register): 158.0 kWh/m2 (elevator plan raw: 158.03)")
    print(f"Aggregation A vs 158.03: diff = {fleet_weighted_pooled - 158.03:.4f}")
    print(f"Aggregation A vs 158.0:  diff = {fleet_weighted_pooled - 158.0:.4f}")


if __name__ == "__main__":
    main()
