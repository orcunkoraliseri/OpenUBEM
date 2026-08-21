"""T09 of PLAN_ten-live-items-2026-08-21-night.md.

Tests whether nyc_centre's null-height_m population resembles the other
eleven cells', which is the unstated assumption behind the 87.6% fusion-fill
extrapolation (F12). Measurement only, no fusion tier run, no fill applied.
"""
import geopandas as gpd
import pandas as pd
import numpy as np

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
EVID = "evidence/open48_refleet4"

CLASS = {c: c.split("_", 1)[1] for c in CELLS}

rows = []
archetype_shares = {}
for cell in CELLS:
    g = gpd.read_file(f"{EVID}/{cell}/01_buildings.gpkg")
    n_total = len(g)
    null_h = g[g["height_m"].isna()].copy()
    n_null = len(null_h)

    r = pd.read_csv(f"{EVID}/{cell}/results/05_results.csv")
    r_arch = r.set_index("osm_id")["archetype_id"]
    null_h["archetype_id"] = null_h["osm_id"].map(r_arch)

    area = null_h["footprint_area_m2"].dropna()
    med = area.median() if len(area) else np.nan
    q1 = area.quantile(0.25) if len(area) else np.nan
    q3 = area.quantile(0.75) if len(area) else np.nan

    n_also_null_levels = int(null_h["levels"].isna().sum())
    pct_levels_available = 100 * (1 - n_also_null_levels / n_null) if n_null else np.nan

    dqf = null_h["data_quality_flag"].fillna("")
    pct_generic_tag = 100 * dqf.str.contains("generic_tag").sum() / n_null if n_null else np.nan

    arch_counts = null_h["archetype_id"].value_counts(normalize=True)
    top3 = set(arch_counts.head(3).index)
    top1 = arch_counts.index[0] if len(arch_counts) else None
    top1_share = arch_counts.iloc[0] * 100 if len(arch_counts) else np.nan
    archetype_shares[cell] = arch_counts

    rows.append({
        "cell": cell, "class": CLASS[cell], "n_total": n_total, "n_null_height": n_null,
        "pct_null_height": 100 * n_null / n_total,
        "median_footprint_area_m2": med, "q1_footprint_area_m2": q1, "q3_footprint_area_m2": q3,
        "pct_levels_available": pct_levels_available,
        "pct_generic_tag": pct_generic_tag,
        "top1_archetype": top1, "top1_archetype_share_pct": top1_share,
        "top3_archetypes": ";".join(top3),
    })

out = pd.DataFrame(rows)
out_path = "openubem/outputs/comparisons/open14_t09_null_height_population_compare_2026-08-21b.csv"
out.to_csv(out_path, index=False)

print("=== C18 reproduction ===")
print("fleet n_null_height total:", out["n_null_height"].sum(), "(F12: 2806)")
hundred = out[out["pct_null_height"] >= 99.99]["cell"].tolist()
print("100%-null cells:", hundred, "(F12: austin_rural, nyc_rural, nyc_suburban)")

print("\n=== per-cell null-height population profile ===")
for _, r in out.iterrows():
    print(f"{r['cell']:16s} class={r['class']:9s} n={int(r['n_null_height']):5d} "
          f"med_area={r['median_footprint_area_m2']:.1f} IQR=[{r['q1_footprint_area_m2']:.1f},{r['q3_footprint_area_m2']:.1f}] "
          f"pct_levels_avail={r['pct_levels_available']:.1f}% pct_generic_tag={r['pct_generic_tag']:.1f}% "
          f"top1_arch={r['top1_archetype']}({r['top1_archetype_share_pct']:.1f}%)")

nyc_c = out[out["cell"] == "nyc_centre"].iloc[0]
nyc_top3 = set(nyc_c["top3_archetypes"].split(";"))

def dist_to_nyc_centre(row):
    d_area = abs(np.log(row["median_footprint_area_m2"]) - np.log(nyc_c["median_footprint_area_m2"])) if row["median_footprint_area_m2"] > 0 and nyc_c["median_footprint_area_m2"] > 0 else np.nan
    d_levels = abs(row["pct_levels_available"] - nyc_c["pct_levels_available"]) / 100
    d_generic = abs(row["pct_generic_tag"] - nyc_c["pct_generic_tag"]) / 100
    row_top3 = set(row["top3_archetypes"].split(";")) if row["top3_archetypes"] else set()
    jaccard = len(row_top3 & nyc_top3) / len(row_top3 | nyc_top3) if (row_top3 | nyc_top3) else 0
    d_archetype = 1 - jaccard
    return pd.Series({"d_area_logratio": d_area, "d_levels_avail": d_levels,
                       "d_generic_tag": d_generic, "archetype_top3_jaccard": jaccard,
                       "d_archetype": d_archetype,
                       "composite_dist": np.nanmean([d_area, d_levels, d_generic, d_archetype])})

dist = out.apply(dist_to_nyc_centre, axis=1)
out2 = pd.concat([out[["cell", "class", "n_null_height"]], dist], axis=1)
out2 = out2[out2["cell"] != "nyc_centre"].sort_values("composite_dist")
out2.to_csv("openubem/outputs/comparisons/open14_t09_distance_to_nyc_centre_2026-08-21b.csv", index=False)

print("\n=== distance-to-nyc_centre ranking (lower = more similar) ===")
for _, r in out2.iterrows():
    print(f"{r['cell']:16s} composite_dist={r['composite_dist']:.3f} "
          f"d_area_logratio={r['d_area_logratio']:.3f} d_levels_avail={r['d_levels_avail']:.3f} "
          f"d_generic_tag={r['d_generic_tag']:.3f} archetype_top3_jaccard={r['archetype_top3_jaccard']:.2f}")

fleet_avg_dist = out2["composite_dist"].mean()
hundred_dist = out2[out2["cell"].isin(["austin_rural", "nyc_rural", "nyc_suburban"])]["composite_dist"].mean()
print(f"\n=== C19 ===")
print(f"mean composite_dist across other 11 cells (fleet average baseline): {fleet_avg_dist:.3f}")
print(f"mean composite_dist for the three 100%-null cells: {hundred_dist:.3f}")
print("100%-null cells are", "MORE" if hundred_dist > fleet_avg_dist else "LESS", "different from nyc_centre than the 11-cell average")
