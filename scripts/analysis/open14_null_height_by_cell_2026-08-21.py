"""T04 (PLAN_ten-live-items-2026-08-21) — OPEN-14 fleet-wide null-height_m sizing.

Measurement only. No fetch, no fusion run. Sizes the null-height_m hole across all twelve cells and
applies the nyc_centre fusion-tier fill rate (106/121, MEASUREMENT_open-14_fusion-yield.md) as a
labelled extrapolation bound, not a re-derivation.
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path

CELLS = [f"{city}_{kind}" for city in ("austin", "la", "nyc") for kind in ("centre", "rural", "suburban", "urban")]
EVIDENCE = Path("evidence/open48_refleet4")

FUSION_FILL_RATE_NYC_CENTRE = 106 / 121  # measured, MEASUREMENT_open-14_fusion-yield.md

rows = []
for cell in CELLS:
    gpkg_path = EVIDENCE / cell / "01_buildings.gpkg"
    gdf = gpd.read_file(gpkg_path)
    n_buildings = len(gdf)
    null_height = gdf["height_m"].isna()
    n_null_height = int(null_height.sum())
    pct_null_height = 100.0 * n_null_height / n_buildings if n_buildings else float("nan")

    null_levels_too = int((null_height & gdf["levels"].isna()).sum())

    rows.append({
        "cell": cell,
        "n_buildings": n_buildings,
        "n_null_height": n_null_height,
        "pct_null_height": round(pct_null_height, 4),
        "n_null_height_and_null_levels": null_levels_too,
        "pct_of_null_height_also_null_levels": round(100.0 * null_levels_too / n_null_height, 4) if n_null_height else 0.0,
        "extrapolated_fill_at_nyc_centre_rate": round(n_null_height * FUSION_FILL_RATE_NYC_CENTRE, 2),
        "extrapolated_remaining_null_after_fill": round(n_null_height * (1 - FUSION_FILL_RATE_NYC_CENTRE), 2),
    })

df_out = pd.DataFrame(rows)
out_path = Path("openubem/outputs/comparisons/open14_null_height_by_cell_2026-08-21.csv")
df_out.to_csv(out_path, index=False)

print(f"nyc_centre_fusion_fill_rate_measured = 106/121 = {FUSION_FILL_RATE_NYC_CENTRE:.6f}")
print()
print(df_out.to_string(index=False))
print()
fleet_total = df_out["n_buildings"].sum()
fleet_null = df_out["n_null_height"].sum()
nyc_centre_null = int(df_out.loc[df_out["cell"] == "nyc_centre", "n_null_height"].iloc[0])
other11_null = fleet_null - nyc_centre_null
print(f"fleet_total_buildings={fleet_total} fleet_null_height={fleet_null} pct={100*fleet_null/fleet_total:.4f}")
print(f"nyc_centre_null_height={nyc_centre_null} (measured population, C9 check)")
print(f"other_11_cells_null_height={other11_null}")
print(f"EXTRAPOLATED (not measured) other-11 fill at nyc_centre rate = {other11_null * FUSION_FILL_RATE_NYC_CENTRE:.1f} of {other11_null}")
