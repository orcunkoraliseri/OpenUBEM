"""OPEN-18 T08: size the small-footprint / cold-climate population against the existing fleet.

No numeric footprint/climate/storey criterion for the sqrt(S) test exists in any doc on disk
(confirmed by reading MEASUREMENT_open-18-20_method-bounds.md and
MEASUREMENT_open-03-18_untrimmed-sample.md). This script applies an EXECUTOR-PROPOSED, explicitly
labelled assumption, built from the only precedent on disk (the T04 8-building NYC sample), plus a
standard ASHRAE cold-zone threshold for "cold" since no doc states one numerically either.
"""
import os
import pandas as pd

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM\evidence\open48_refleet4"
OUT = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open18_small_cold_population_2026-08-21.csv"

COLD_ZONE_PREFIXES = ("5", "6", "7", "8")  # ASHRAE 169 zones 5-8 = cool/cold/very-cold/subarctic

rows = []
climate_rows = []

for cell in CELLS:
    epw_df = pd.read_parquet(os.path.join(ROOT, cell, "02a_climate_epw.parquet"))
    zones = epw_df["climate_zone"].unique().tolist()
    epws = epw_df["epw_path"].apply(os.path.basename).unique().tolist()
    climate_rows.append({
        "cell": cell,
        "climate_zone": ";".join(zones),
        "epw_basename": ";".join(epws),
        "is_cold_zone": any(str(z).startswith(COLD_ZONE_PREFIXES) for z in zones),
    })

    res = pd.read_csv(os.path.join(ROOT, cell, "results", "05_results.csv"))
    ok = res[res["simulation_status"] == "success"].copy()
    if ok.empty:
        continue
    p35 = ok["footprint_area_m2"].quantile(0.35)
    ok["is_small"] = ok["footprint_area_m2"] <= p35
    is_cold_cell = any(str(z).startswith(COLD_ZONE_PREFIXES) for z in zones)
    ok["is_cold"] = is_cold_cell

    for arch, grp in ok.groupby("archetype_id"):
        rows.append({
            "cell": cell,
            "archetype_id": arch,
            "climate_zone": ";".join(zones),
            "is_cold_zone_cell": is_cold_cell,
            "n_success": len(grp),
            "footprint_p35_threshold_m2": round(p35, 2),
            "n_small_footprint": int(grp["is_small"].sum()),
            "n_small_and_cold": int((grp["is_small"] & grp["is_cold"]).sum()),
            "levels_min": grp["levels"].min(),
            "levels_median": grp["levels"].median(),
            "levels_max": grp["levels"].max(),
        })

out_df = pd.DataFrame(rows)
out_df.to_csv(OUT, index=False)

climate_df = pd.DataFrame(climate_rows)

print("=== per-cell climate ===")
print(climate_df.to_string(index=False))

print("\n=== fleet totals ===")
total_success = out_df["n_success"].sum()
total_small = out_df["n_small_footprint"].sum()
total_small_cold = out_df["n_small_and_cold"].sum()
print(f"n_success (fleet) = {total_success}")
print(f"n_small_footprint (per-cell p35, fleet sum) = {total_small}")
print(f"n_small_and_cold (small AND in a zone-5+ cell) = {total_small_cold}")

print("\n=== per-cell small-and-cold ===")
by_cell = out_df.groupby("cell")[["n_success", "n_small_footprint", "n_small_and_cold"]].sum()
print(by_cell.to_string())

print("\n=== per-archetype, cold cells only ===")
cold_only = out_df[out_df["is_cold_zone_cell"]]
by_arch = cold_only.groupby("archetype_id")[["n_success", "n_small_footprint", "n_small_and_cold"]].sum()
print(by_arch.to_string())

print(f"\nRows written: {len(out_df)} -> {OUT}")
