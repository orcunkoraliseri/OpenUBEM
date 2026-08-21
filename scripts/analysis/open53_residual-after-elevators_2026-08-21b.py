import pandas as pd
import os

CELLS = [f"{city}_{zone}" for city in ("austin", "la", "nyc") for zone in ("centre", "rural", "suburban", "urban")]
EVID = r"evidence\open48_refleet4"

frames = []
for cell in CELLS:
    p = os.path.join(EVID, cell, "results", "05_results.csv")
    df = pd.read_csv(p)
    df["cell"] = cell
    frames.append(df)
results = pd.concat(frames, ignore_index=True)

meter = pd.read_csv(r"openubem\outputs\comparisons\open53_meter_only_eui_2026-08-21.csv")

print("results rows:", len(results), "meter rows:", len(meter))

join = meter.merge(
    results[["osm_id", "cell", "elevators_eui_kwh_m2", "floor_area_m2", "archetype_id",
             "zoning_strategy", "data_quality_flag", "floor_area_provenance", "simulation_status"]],
    on=["osm_id", "cell"], how="left", suffixes=("_meter", "_results")
)
print("join rows:", len(join), "unmatched:", join["floor_area_m2"].isna().sum())

join["gap"] = join["published_eui"] - join["meter_only_eui"]

# C6 - reproduce F8 pooled elevator and pooled gap
w = join["floor_area_m2"]
pooled_elev = (join["elevators_eui_kwh_m2"] * w).sum() / w.sum()
pooled_gap = (join["gap"] * w).sum() / w.sum()
print(f"\n=== C6 reproduce F8 ===")
print(f"pooled elevators = {pooled_elev:.4f} (expect 2.2421)")
print(f"pooled gap = {pooled_gap:.4f} (expect 2.5539)")

n_exact = ((join["gap"] - join["elevators_eui_kwh_m2"]).abs() < 1e-6).sum()
print(f"n exact match (gap == elevators to 1e-6): {n_exact} of {len(join)} (expect 3823 of 8153)")

join["resid"] = join["gap"] - join["elevators_eui_kwh_m2"]

pooled_resid = (join["resid"] * w).sum() / w.sum()
print(f"\n=== C7 ===")
print(f"n = {len(join)}")
print(f"pooled residual = {pooled_resid:.4f} kWh/m2 (sign: {'positive' if pooled_resid>0 else 'negative'})")
print(f"residual median = {join['resid'].median():.4f}")
print(f"residual min = {join['resid'].min():.2f}  max = {join['resid'].max():.2f}")

join["abs_resid_area"] = (join["resid"] * join["floor_area_m2"]).abs()
top = join.sort_values("abs_resid_area", ascending=False).iloc[0]
print(f"largest contributor by |resid*area|: {top['osm_id']} ({top['cell']}) resid={top['resid']:.4f} area={top['floor_area_m2']:.1f} contrib={top['abs_resid_area']:.1f}")

# distribution: how many carry 50/80/90% of absolute residual
sorted_df = join.reindex(join["abs_resid_area"].sort_values(ascending=False).index)
total_abs = sorted_df["abs_resid_area"].sum()
cum = sorted_df["abs_resid_area"].cumsum()
n50 = (cum <= 0.5 * total_abs).sum() + 1
n80 = (cum <= 0.8 * total_abs).sum() + 1
n90 = (cum <= 0.9 * total_abs).sum() + 1
print(f"\ntotal |resid*area| = {total_abs:.1f}")
print(f"buildings carrying 50% of abs residual mass: {n50} of {len(join)} ({100*n50/len(join):.2f}%)")
print(f"buildings carrying 80% of abs residual mass: {n80} of {len(join)} ({100*n80/len(join):.2f}%)")
print(f"buildings carrying 90% of abs residual mass: {n90} of {len(join)} ({100*n90/len(join):.2f}%)")

# outliers
outliers = join[join["resid"].abs() > 10]
print(f"\noutliers |resid|>10 kWh/m2: {len(outliers)} of {len(join)}")

def crosstab_report(col):
    vc = outliers[col].value_counts(dropna=False).head(10)
    total_vc = join[col].value_counts(dropna=False)
    print(f"\n-- {col} (outlier count / total count) --")
    for k, v in vc.items():
        tot = total_vc.get(k, 0)
        print(f"  {k}: {v} / {tot}")

print("\njoin columns:", list(join.columns))
for col in ["archetype_id_results", "cell", "zoning_strategy", "data_quality_flag", "floor_area_provenance"]:
    crosstab_report(col)

print("\nNote: T02's per-building zone-count output not available (T02 not run in this pass) - proceeding without it per plan instruction.")

join.to_csv(r"openubem\outputs\comparisons\open53_residual-after-elevators_2026-08-21b.csv", index=False)
outliers.to_csv(r"openubem\outputs\comparisons\open53_residual-outliers_2026-08-21b.csv", index=False)
