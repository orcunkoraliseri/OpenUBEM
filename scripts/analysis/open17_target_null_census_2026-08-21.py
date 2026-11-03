"""T03 (PLAN_ten-live-items-2026-08-21) — OPEN-17 fleet-wide null census per imputation target.

Measurement only. Reads the twelve 01_buildings.gpkg + matching results/05_results.csv.
Writes openubem/outputs/comparisons/open17_target_null_census_2026-08-21.csv.

Target list note: the plan text names a placeholder seventh target `roof_shape`, with an explicit
instruction to use the register's list instead if that is wrong. `01_buildings.gpkg` has no
`provenance_roof_shape` column (confirmed: columns are provenance_levels, provenance_height_m,
provenance_year_built, provenance_building_tag, provenance_function_tag, provenance_postcode,
provenance_geometry — matching plan section 4's pinned column list exactly). The register's own
citation for OPEN-17 (extra/MEASUREMENT_open-17_tier-census.md) enumerates the seven targets as
building_tag, function_tag, geometry, height_m, levels, postcode, year_built. So this script uses
that list: levels, height_m, year_built, function_tag, postcode, building_tag, geometry.
"""
import geopandas as gpd
import pandas as pd
from pathlib import Path

CELLS = [f"{city}_{kind}" for city in ("austin", "la", "nyc") for kind in ("centre", "rural", "suburban", "urban")]
EVIDENCE = Path("evidence/open48_refleet4")
TARGETS = ["levels", "height_m", "year_built", "function_tag", "postcode", "building_tag", "geometry"]
PROV_COL = {
    "levels": "provenance_levels",
    "height_m": "provenance_height_m",
    "year_built": "provenance_year_built",
    "function_tag": "provenance_function_tag",
    "postcode": "provenance_postcode",
    "building_tag": "provenance_building_tag",
    "geometry": "provenance_geometry",
}

rows = []
total_buildings = 0
for cell in CELLS:
    gpkg_path = EVIDENCE / cell / "01_buildings.gpkg"
    results_path = EVIDENCE / cell / "results" / "05_results.csv"
    gdf = gpd.read_file(gpkg_path)
    total_buildings += len(gdf)

    res = pd.read_csv(results_path, usecols=["osm_id", "simulation_status"])
    res = res.drop_duplicates(subset="osm_id")
    status_map = dict(zip(res["osm_id"], res["simulation_status"]))
    gdf["_sim_status"] = gdf["osm_id"].map(status_map)
    gdf["_simulated_ok"] = gdf["_sim_status"] == "success"

    for target in TARGETS:
        if target == "geometry":
            is_null = gdf.geometry.isna() | gdf.geometry.is_empty
        else:
            is_null = gdf[target].isna()

        n_total = len(gdf)
        n_null = int(is_null.sum())
        n_null_simulated = int((is_null & gdf["_simulated_ok"]).sum())
        pct_null = 100.0 * n_null / n_total if n_total else float("nan")

        prov_col = PROV_COL.get(target)
        if prov_col in gdf.columns:
            vc = gdf.loc[is_null, prov_col].fillna("NA").value_counts()
            provenance_breakdown = ";".join(f"{k}={v}" for k, v in vc.items())
            vc_all = gdf[prov_col].fillna("NA").value_counts()
            provenance_breakdown_all = ";".join(f"{k}={v}" for k, v in vc_all.items())
            needs_value = gdf[prov_col] != "OSM_OBSERVED"
            n_needs_value = int(needs_value.sum())
            n_needs_value_simulated = int((needs_value & gdf["_simulated_ok"]).sum())
        else:
            provenance_breakdown = "NO_PROVENANCE_COLUMN"
            provenance_breakdown_all = "NO_PROVENANCE_COLUMN"
            n_needs_value = None
            n_needs_value_simulated = None

        rows.append({
            "cell": cell,
            "target": target,
            "n_total": n_total,
            "n_null": n_null,
            "n_null_simulated": n_null_simulated,
            "pct_null": round(pct_null, 4),
            "n_needs_value_provenance": n_needs_value,
            "n_needs_value_provenance_simulated": n_needs_value_simulated,
            "provenance_breakdown_of_null_rows": provenance_breakdown,
            "provenance_breakdown_all_rows": provenance_breakdown_all,
        })

df_out = pd.DataFrame(rows)
out_path = Path("openubem/outputs/comparisons/open17_target_null_census_2026-08-21.csv")
df_out.to_csv(out_path, index=False)

print(f"total_buildings_across_12_gpkgs={total_buildings}")
print()
fleet = df_out.groupby("target").agg(
    n_total=("n_total", "sum"),
    n_null=("n_null", "sum"),
    n_null_simulated=("n_null_simulated", "sum"),
    n_needs_value_provenance=("n_needs_value_provenance", "sum"),
    n_needs_value_provenance_simulated=("n_needs_value_provenance_simulated", "sum"),
).reset_index()
fleet["pct_null"] = 100.0 * fleet["n_null"] / fleet["n_total"]
fleet["pct_needs_value"] = 100.0 * fleet["n_needs_value_provenance"] / fleet["n_total"]
print(fleet.to_string(index=False))
