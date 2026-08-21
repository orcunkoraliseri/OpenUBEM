"""
OPEN-61 T04 - characterise the 116 buildings that carry 70.5% of fleet DH.
Measurement only. No production code touched, no remedy proposed.

Input:  openubem/outputs/comparisons/open61_census_fleet.csv (8,160 rows)
Output: openubem/outputs/comparisons/open61_dh_concentration_2026-08-21.csv
"""
import pandas as pd

IN_PATH = "openubem/outputs/comparisons/open61_census_fleet.csv"
OUT_PATH = "openubem/outputs/comparisons/open61_dh_concentration_2026-08-21.csv"

df = pd.read_csv(IN_PATH)
n_fleet_rows = len(df)

d = df[df["dh_total_kwh"].notna()].copy()
n = len(d)
total_dh_kwh = d["dh_total_kwh"].sum()
total_floor_analysable = d["recorded_floor_area_m2"].sum()
pooled_dh_eui = total_dh_kwh / total_floor_analysable

print("ASCII-ONLY REPORT")
print("n_fleet_rows_total=%d" % n_fleet_rows)
print("n_analysable(dh_total_kwh notna)=%d" % n)
print("total_dh_kwh=%.4f" % total_dh_kwh)
print("total_floor_analysable_m2=%.4f" % total_floor_analysable)
print("pooled_dh_eui_kwh_m2=%.4f" % pooled_dh_eui)

# --- Step 1: which 116? Archetype-level pooled table (recomputation A) ---
grp = d.groupby("archetype_id").agg(
    n=("dh_total_kwh", "size"),
    dh_kwh_sum=("dh_total_kwh", "sum"),
    floor_sum=("recorded_floor_area_m2", "sum"),
).reset_index()
grp["pooled_dh_eui_kwh_m2"] = grp["dh_kwh_sum"] / grp["floor_sum"]
grp["share_of_fleet_dh"] = grp["dh_kwh_sum"] / total_dh_kwh
grp = grp.sort_values("share_of_fleet_dh", ascending=False).reset_index(drop=True)

print("\n--- archetype table (top 10 by share of fleet DH) ---")
for _, r in grp.head(10).iterrows():
    print("archetype=%s n=%d pooled_kwh_m2=%.4f share_of_fleet_dh=%.4f" % (
        r["archetype_id"], r["n"], r["pooled_dh_eui_kwh_m2"], r["share_of_fleet_dh"]))

# The "116" = union of the two tallest-residential archetypes (recomputation A: groupby+cumsum)
top2 = grp.head(2)
n_top2 = int(top2["n"].sum())
share_top2_A = float(top2["share_of_fleet_dh"].sum())
archetypes_116 = list(top2["archetype_id"])

# --- Step 2: independent recomputation B, via boolean mask (not groupby) ---
mask_116 = d["archetype_id"].isin(archetypes_116)
n_top2_B = int(mask_116.sum())
share_top2_B = float(d.loc[mask_116, "dh_total_kwh"].sum() / total_dh_kwh)

print("\n--- concentration reproduction ---")
print("archetypes_116=%s" % archetypes_116)
print("recomputation_A(groupby+cumsum): n=%d share=%.6f (%.1f%%)" % (n_top2, share_top2_A, 100 * share_top2_A))
print("recomputation_B(boolean mask):   n=%d share=%.6f (%.1f%%)" % (n_top2_B, share_top2_B, 100 * share_top2_B))
print("agree=%s" % (n_top2 == n_top2_B and abs(share_top2_A - share_top2_B) < 1e-9))

# NOTE: a literal rank-by-dh_total_kwh top-116 does NOT reproduce 70.5% (it gives ~77.7%).
# The 116/70.5% figure is archetype-defined: TallBuilding (n=92) + SuperTallBuilding (n=24) = 116,
# whose combined share of fleet DH energy is what reproduces 70.5%. Recorded here as a check,
# not asserted from memory.
top116_rank = d.sort_values("dh_total_kwh", ascending=False).reset_index(drop=True)
rank_116_share = float(top116_rank.loc[:115, "dh_total_kwh"].sum() / total_dh_kwh)
print("\ncheck_only: literal top-116-by-dh_total_kwh share=%.4f (%.1f%%) -- NOT the defining rule" % (
    rank_116_share, 100 * rank_116_share))

# --- Step 3: cross-tabulate the 116 against archetype_id, cell, zoning_strategy, size; report lift ---
d["in_116"] = mask_116
fleet_n = len(d)

def lift_table(col, label):
    rows = []
    fleet_counts = d[col].value_counts()
    sub_counts = d.loc[d["in_116"], col].value_counts()
    for val, fleet_n_val in fleet_counts.items():
        sub_n_val = int(sub_counts.get(val, 0))
        fleet_rate = fleet_n_val / fleet_n
        sub_rate = sub_n_val / n_top2_B if n_top2_B else 0.0
        lift = (sub_rate / fleet_rate) if fleet_rate > 0 else float("nan")
        rows.append({
            "dimension": label, "value": str(val),
            "fleet_n": int(fleet_n_val), "fleet_share": fleet_rate,
            "in116_n": sub_n_val, "in116_share": sub_rate,
            "lift": lift,
        })
    out = pd.DataFrame(rows).sort_values("in116_n", ascending=False)
    return out

lift_archetype = lift_table("archetype_id", "archetype_id")
lift_cell = lift_table("cell", "cell")
lift_zoning = lift_table("zoning_strategy", "zoning_strategy")

# size buckets by recorded_floor_area_m2 quartile (fleet-wide edges)
d["size_bucket"] = pd.qcut(d["recorded_floor_area_m2"], 4, labels=["Q1_smallest", "Q2", "Q3", "Q4_largest"])
lift_size = lift_table("size_bucket", "size_bucket")

print("\n--- lift: archetype_id (in-116 rows only, top entries) ---")
for _, r in lift_archetype[lift_archetype["in116_n"] > 0].iterrows():
    print("archetype=%s fleet_n=%d fleet_share=%.4f in116_n=%d in116_share=%.4f lift=%.2f" % (
        r["value"], r["fleet_n"], r["fleet_share"], r["in116_n"], r["in116_share"], r["lift"]))

print("\n--- lift: cell (in-116 rows only) ---")
for _, r in lift_cell[lift_cell["in116_n"] > 0].iterrows():
    print("cell=%s fleet_n=%d fleet_share=%.4f in116_n=%d in116_share=%.4f lift=%.2f" % (
        r["value"], r["fleet_n"], r["fleet_share"], r["in116_n"], r["in116_share"], r["lift"]))

print("\n--- lift: zoning_strategy (in-116 rows only) ---")
for _, r in lift_zoning[lift_zoning["in116_n"] > 0].iterrows():
    print("zoning=%s fleet_n=%d fleet_share=%.4f in116_n=%d in116_share=%.4f lift=%.2f" % (
        r["value"], r["fleet_n"], r["fleet_share"], r["in116_n"], r["in116_share"], r["lift"]))

print("\n--- lift: size_bucket (in-116 rows only) ---")
for _, r in lift_size[lift_size["in116_n"] > 0].iterrows():
    print("size_bucket=%s fleet_n=%d fleet_share=%.4f in116_n=%d in116_share=%.4f lift=%.2f" % (
        r["value"], r["fleet_n"], r["fleet_share"], r["in116_n"], r["in116_share"], r["lift"]))

# num_zones summary for the 116 vs fleet
print("\n--- num_zones: fleet vs 116 ---")
print("fleet median=%.1f mean=%.2f" % (d["num_zones"].median(), d["num_zones"].mean()))
print("116   median=%.1f mean=%.2f" % (d.loc[mask_116, "num_zones"].median(), d.loc[mask_116, "num_zones"].mean()))

# --- Step 4: floor-area share of the 116, and pooled EUI if DH added for the 116 only ---
floor_116 = d.loc[mask_116, "recorded_floor_area_m2"].sum()
floor_area_share_116 = floor_116 / total_floor_analysable

numerator_no_dh = (d["recorded_total_eui_kwh_m2"] * d["recorded_floor_area_m2"]).sum()
pooled_total_eui_no_dh = numerator_no_dh / total_floor_analysable

dh_kwh_116 = d.loc[mask_116, "dh_total_kwh"].sum()
numerator_with_dh_116_only = numerator_no_dh + dh_kwh_116
pooled_total_eui_with_dh_116 = numerator_with_dh_116_only / total_floor_analysable

print("\n--- floor area and pooled EUI effect ---")
print("floor_116_m2=%.2f" % floor_116)
print("floor_area_share_116_of_analysable=%.6f (%.2f%%)" % (floor_area_share_116, 100 * floor_area_share_116))
print("pooled_total_eui_no_dh_kwh_m2=%.4f  (n=%d)" % (pooled_total_eui_no_dh, n))
print("pooled_total_eui_with_dh_added_for_116_only_kwh_m2=%.4f" % pooled_total_eui_with_dh_116)
print("delta_kwh_m2=%.4f" % (pooled_total_eui_with_dh_116 - pooled_total_eui_no_dh))
print("delta_pct=%.4f%%" % (100 * (pooled_total_eui_with_dh_116 - pooled_total_eui_no_dh) / pooled_total_eui_no_dh))

# --- write output CSV ---
summary_rows = [
    {"metric": "n_fleet_rows_total", "value": n_fleet_rows},
    {"metric": "n_analysable", "value": n},
    {"metric": "total_dh_kwh", "value": total_dh_kwh},
    {"metric": "pooled_dh_eui_kwh_m2", "value": pooled_dh_eui},
    {"metric": "archetypes_116", "value": " + ".join(archetypes_116)},
    {"metric": "n_116_recomputation_A_groupby", "value": n_top2},
    {"metric": "share_116_recomputation_A_groupby", "value": share_top2_A},
    {"metric": "n_116_recomputation_B_boolean_mask", "value": n_top2_B},
    {"metric": "share_116_recomputation_B_boolean_mask", "value": share_top2_B},
    {"metric": "check_only_literal_rank_top116_share", "value": rank_116_share},
    {"metric": "floor_116_m2", "value": floor_116},
    {"metric": "floor_area_share_116_of_analysable", "value": floor_area_share_116},
    {"metric": "pooled_total_eui_no_dh_kwh_m2", "value": pooled_total_eui_no_dh},
    {"metric": "pooled_total_eui_with_dh_added_for_116_only_kwh_m2", "value": pooled_total_eui_with_dh_116},
    {"metric": "delta_kwh_m2", "value": pooled_total_eui_with_dh_116 - pooled_total_eui_no_dh},
]
summary_df = pd.DataFrame(summary_rows)

with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
    f.write("# OPEN-61 T04 -- concentration summary\n")
    summary_df.to_csv(f, index=False)
    f.write("\n# archetype table (all archetypes, sorted by share of fleet DH)\n")
    grp.to_csv(f, index=False)
    f.write("\n# lift table: archetype_id\n")
    lift_archetype.to_csv(f, index=False)
    f.write("\n# lift table: cell\n")
    lift_cell.to_csv(f, index=False)
    f.write("\n# lift table: zoning_strategy\n")
    lift_zoning.to_csv(f, index=False)
    f.write("\n# lift table: size_bucket (recorded_floor_area_m2 quartile)\n")
    lift_size.to_csv(f, index=False)

print("\nWROTE %s" % OUT_PATH)
