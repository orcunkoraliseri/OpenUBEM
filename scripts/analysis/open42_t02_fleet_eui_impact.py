"""OPEN-42 T02 step 2-4: what the six 200.0 m^2 placeholder buildings do to the
adopted 158.0 kWh/m^2 fleet figure. Measurement only.

Step 1 (formula reproduction) lives in open42_t02_reproduce_fleet_eui.py and is not
repeated here; this script starts from its confirmed result:
    fleet-weighted headline = weighted mean of the 12 per-cell floor-area-weighted
    EUI numbers, weighted by each cell's TOTAL building count -> 158.0298, matching
    the adopted 158.03 / 158.0 to within 0.03 (well inside the 0.1 tolerance).
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE_elevrb"
AUDIT_CSV = ROOT / "openubem" / "outputs" / "comparisons" / "open01_denominator_audit.csv"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}

STEMS = {
    "la_rural": [
        "way_472960972", "way_472961034", "way_472961088",
        "way_472961091", "way_472961171",
    ],
    "la_urban": ["way_402215469"],
}
ALL_STEMS = [s for lst in STEMS.values() for s in lst]


def derive_num_floors(row: pd.Series, floor_to_floor_m: float = 3.5) -> int:
    if pd.notna(row["levels"]):
        return max(1, int(row["levels"]))
    if pd.notna(row["height_m"]):
        return max(1, math.ceil(row["height_m"] / floor_to_floor_m))
    return 1


def main() -> None:
    frames = []
    for cell in CELLS:
        df = pd.read_csv(RESULTS_DIR / cell / "05_results.csv")
        df["cell"] = cell
        df["_floor_area"] = df.apply(derive_num_floors, axis=1) * df["footprint_area_m2"]
        frames.append(df)
    fleet = pd.concat(frames, ignore_index=True)
    fleet["stem"] = fleet["osm_id"].astype(str).str.replace("/", "_", regex=False)

    six = fleet[fleet["stem"].isin(ALL_STEMS)]
    print("The six buildings in the ADOPTED baseline (phaseE_elevrb) 05_results.csv:")
    print(six[["cell", "stem", "footprint_area_m2", "simulation_status", "total_eui_kwh_m2", "archetype_id"]].to_string())

    n_success_total = fleet["simulation_status"].isin(_SUCCESS_STATUSES).sum()
    n_total = len(fleet)
    print(f"\nFleet: {n_total} rows, {n_success_total} success, {n_total - n_success_total} non-success.")
    non_success = fleet[~fleet["simulation_status"].isin(_SUCCESS_STATUSES)]
    print(f"Non-success stems (n={len(non_success)}): {sorted(non_success['stem'].tolist())}")
    print(f"These match the six OPEN-42 stems exactly: {sorted(non_success['stem'].tolist()) == sorted(ALL_STEMS)}")

    # Reproduced baseline (formula confirmed in open42_t02_reproduce_fleet_eui.py)
    per_cell_rows = []
    for cell in CELLS:
        d = fleet[fleet["cell"] == cell]
        succ = d[d["simulation_status"].isin(_SUCCESS_STATUSES)]
        fa = succ["_floor_area"].sum()
        weighted = (succ["total_eui_kwh_m2"] * succ["_floor_area"]).sum() / fa if fa > 0 else float("nan")
        per_cell_rows.append({"cell": cell, "n_total": len(d), "weighted_total_eui": weighted})
    per_cell_df = pd.DataFrame(per_cell_rows)
    fleet_weighted_published = (per_cell_df["weighted_total_eui"] * per_cell_df["n_total"]).sum() / per_cell_df["n_total"].sum()
    print(f"\nReproduced published fleet figure (count-of-cell weighted): {fleet_weighted_published:.4f} kWh/m2 (adopted: 158.03 / rounds to 158.0)")

    # The six are simulation_status == not_simulated with total_eui_kwh_m2 == NaN.
    # They are EXCLUDED from both the numerator (no EUI) and the per-cell denominator
    # (per-cell success filter) of the formula above. Correcting only their declared
    # footprint_area_m2 (200.0 -> multiplier-aware simulated area) changes nothing,
    # because they contribute zero rows to either sum today.
    audit = pd.read_csv(AUDIT_CSV)
    audit_auto = audit[(audit["mode"] == "auto") & (audit["stem"].isin(ALL_STEMS))]

    out_rows = []
    for _, r in audit_auto.iterrows():
        match = six[(six["cell"] == r["cell"]) & (six["stem"] == r["stem"])]
        eui_published = match["total_eui_kwh_m2"].iloc[0] if len(match) else float("nan")
        out_rows.append({
            "stem": r["stem"],
            "cell": r["cell"],
            "declared_area_m2": r["declared_area_m2"],
            "simulated_area_m2": r["area_multiplier_aware_m2"],
            "error_factor": r["error_factor"],
            "eui_published": eui_published,
            "eui_corrected": float("nan"),
            "delta_kwh_m2": 0.0,
            "note": "simulation_status=not_simulated in the adopted baseline; excluded from "
                    "both numerator (no EUI recorded) and denominator (per-cell success filter) "
                    "of the published 158.0 figure; correcting the denominator alone cannot move "
                    "a number this building was never part of",
        })

    fleet_summary = {
        "stem": "FLEET_SUMMARY",
        "cell": "ALL_12",
        "declared_area_m2": sum(r["declared_area_m2"] for r in out_rows),
        "simulated_area_m2": sum(r["simulated_area_m2"] for r in out_rows),
        "error_factor": float("nan"),
        "eui_published": fleet_weighted_published,
        "eui_corrected": fleet_weighted_published,
        "delta_kwh_m2": 0.0,
        "note": "measured impact of correcting the six placeholder denominators on the adopted "
                "158.0 kWh/m2 fleet figure is exactly 0.000 (0.00%) because all six buildings are "
                "already excluded from that aggregate (simulation_status=not_simulated, no EUI)",
    }
    out_rows.append(fleet_summary)

    out_df = pd.DataFrame(out_rows)
    out_path = ROOT / "openubem" / "outputs" / "comparisons" / "open42_fleet_eui_impact.csv"
    out_df.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(out_df.to_string())


if __name__ == "__main__":
    main()
