"""T05: the EUI denominator census, fleet-wide on run-4 artifacts.

Compares each building's .eio-derived, multiplier-aware simulated floor area
(already resolved into 05_results.csv's floor_area_m2 column when
floor_area_provenance == 'eio_simulated' -- see openubem/results/parser.py:264-390,
resolve_simulated_floor_area()) against footprint_area_m2 x levels (the naive,
non-multiplier-aware denominator).

Control: OPEN-01's closure measured auto mode at median error factor 1.0000,
99.63% of buildings within +/-1% (register :954). This script must reproduce
that on run-4 to within a few tenths of a percent.
"""
import pandas as pd
from pathlib import Path

RUN4_ROOT = Path(r"C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet4")
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]


def load_cell(cell):
    df = pd.read_csv(RUN4_ROOT / cell / "results" / "05_results.csv")
    df["cell"] = cell
    return df


def main():
    frames = [load_cell(c) for c in CELLS]
    fleet = pd.concat(frames, ignore_index=True)

    success = fleet[fleet["simulation_status"] == "success"].copy()
    print(f"fleet successes: {len(success)}")
    print(success["floor_area_provenance"].value_counts())

    eio = success[success["floor_area_provenance"] == "eio_simulated"].copy()
    print(f"\neio_simulated rows: {len(eio)}")

    eio["derived_area_m2"] = eio["footprint_area_m2"] * eio["levels"]
    eio = eio[eio["derived_area_m2"] > 0].copy()
    eio["ratio"] = eio["floor_area_m2"] / eio["derived_area_m2"]

    print(f"\nrows with valid derived area > 0: {len(eio)}")
    print("\n=== RATIO DISTRIBUTION (eio floor_area_m2 / (footprint_area_m2 x levels)) ===")
    print(eio["ratio"].describe())
    print("median:", eio["ratio"].median())

    within_1pct = ((eio["ratio"] - 1.0).abs() <= 0.01).sum()
    within_10pct = ((eio["ratio"] - 1.0).abs() <= 0.10).sum()
    within_2x = eio["ratio"].between(0.5, 2.0).sum()
    outside_2x = eio[~eio["ratio"].between(0.5, 2.0)]

    n = len(eio)
    print(f"\nwithin +/-1%:  {within_1pct} / {n} = {within_1pct/n*100:.2f}%")
    print(f"within +/-10%: {within_10pct} / {n} = {within_10pct/n*100:.2f}%")
    print(f"within 2x (0.5x-2.0x): {within_2x} / {n} = {within_2x/n*100:.2f}%")
    print(f"outside 2x: {len(outside_2x)} / {n} = {len(outside_2x)/n*100:.2f}%")

    print("\n=== BUILDINGS OUTSIDE 2x ===")
    cols = ["cell", "osm_id", "archetype_id", "zoning_strategy", "footprint_area_m2",
            "levels", "floor_area_m2", "derived_area_m2", "ratio"]
    outside_sorted = outside_2x.sort_values("ratio")[cols]
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(outside_sorted.to_string(index=False))

    out_path = Path(r"C:/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/comparisons/eio_area_vs_derived_fleet.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eio[cols].to_csv(out_path, index=False)
    print(f"\nWrote {out_path} ({len(eio)} rows)")


if __name__ == "__main__":
    main()
