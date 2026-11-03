import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_BASE = (
    REPO_ROOT
    / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE_elevrb"
)
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
OUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open43_fleet_aggregations.csv"

EXPECTED = {
    "pooled": 157.0552,
    "weighted_by_total_count": 158.0298,
    "weighted_by_success_count": 158.0557,
    "unweighted_mean_of_cell_means": 160.0993,
}


def per_cell_stats(cell: str) -> dict:
    df = pd.read_csv(RESULTS_BASE / cell / "05_results.csv")
    df["floor_area_m2"] = df["footprint_area_m2"] * df["levels"].clip(lower=1)
    succ = df[df["simulation_status"] == "success"]
    n_total = len(df)
    n_success = len(succ)
    floor_area_m2 = succ["floor_area_m2"].sum()
    weighted_total_eui = (succ["total_eui_kwh_m2"] * succ["floor_area_m2"]).sum() / floor_area_m2
    return {
        "cell": cell,
        "n_total": n_total,
        "n_success": n_success,
        "floor_area_m2": floor_area_m2,
        "weighted_total_eui": weighted_total_eui,
    }


def main() -> int:
    per_cell = pd.DataFrame([per_cell_stats(c) for c in CELLS])

    pooled = (per_cell["weighted_total_eui"] * per_cell["floor_area_m2"]).sum() / per_cell["floor_area_m2"].sum()
    weighted_by_total_count = (
        (per_cell["weighted_total_eui"] * per_cell["n_total"]).sum() / per_cell["n_total"].sum()
    )
    weighted_by_success_count = (
        (per_cell["weighted_total_eui"] * per_cell["n_success"]).sum() / per_cell["n_success"].sum()
    )
    unweighted_mean_of_cell_means = per_cell["weighted_total_eui"].mean()

    aggregations = {
        "pooled": pooled,
        "weighted_by_total_count": weighted_by_total_count,
        "weighted_by_success_count": weighted_by_success_count,
        "unweighted_mean_of_cell_means": unweighted_mean_of_cell_means,
    }

    out_rows = [
        {
            "aggregation": name,
            "value": value,
            "value_4dp": round(value, 4),
            "expected_4dp": EXPECTED[name],
        }
        for name, value in aggregations.items()
    ]
    out_df = pd.DataFrame(out_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)

    print(f"n_total (sum over 12 cells): {int(per_cell['n_total'].sum())}")
    print(f"n_success (sum over 12 cells): {int(per_cell['n_success'].sum())}")
    print(f"total floor area (success only): {per_cell['floor_area_m2'].sum():.1f} m^2")
    for name, value in aggregations.items():
        print(f"{name}: {value:.4f} (expected {EXPECTED[name]:.4f})")

    ok = True
    for name, expected in EXPECTED.items():
        got = round(aggregations[name], 4)
        if abs(got - expected) > 1e-4:
            print(f"MISMATCH: {name} got {got}, expected {expected}", file=sys.stderr)
            ok = False

    if not ok:
        return 1

    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
