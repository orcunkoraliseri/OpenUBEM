"""
OPEN-61 T03 — fleet restatement, arithmetic only, over the census CSV.

Source: openubem/outputs/comparisons/open61_census_fleet.csv (already on disk).
No simulation, no corpus walk, no .sql reads. Read-only against the CSV.

Produces a CANDIDATE restated fleet figure for CP-2's adoption question.
It does NOT change the adopted published figure (153.8231 kWh/m^2 over 8,153),
which this script never touches and never writes.

Pre-registered gates (plan Sec 7, T03):
  C4 - recomputed "before" pooled figure must reproduce 152.3011 kWh/m^2 (F7)
       within 0.001. If it does not, STOP and report -- do not adjust.
  C5 - sum(dh_total_kwh) must equal sum(dh_water_systems_gj) * 277.7778
       within 0.01% (F3).
"""
import pandas as pd

CSV_IN = "openubem/outputs/comparisons/open61_census_fleet.csv"
CSV_OUT = "openubem/outputs/comparisons/open61_fleet_restatement_2026-08-22.csv"

GJ_TO_KWH = 1_000_000 / 3600  # 277.7778

TALL_ARCHETYPES = ["SuperTallBuilding", "TallBuilding"]


def pooled(df, value_col, weight_col="parsed_floor_area_m2"):
    w = df[weight_col]
    return (df[value_col] * w).sum() / w.sum()


def main():
    df = pd.read_csv(CSV_IN)

    mask = df["parsed_total_eui_kwh_m2"].notna() & df["dh_total_kwh"].notna()
    sub = df.loc[mask].copy()
    n = len(sub)

    area = sub["parsed_floor_area_m2"]
    before_col = sub["parsed_total_eui_kwh_m2"]
    dh_eui = sub["dh_total_kwh"] / area
    after_col = before_col + dh_eui
    sub["dh_eui_kwh_m2"] = dh_eui
    sub["after_total_eui_kwh_m2"] = after_col

    pooled_before = pooled(sub, "parsed_total_eui_kwh_m2")
    pooled_after = pooled(sub, "after_total_eui_kwh_m2")
    delta = pooled_after - pooled_before

    # --- Gates ---
    c4_target = 152.3011
    c4_diff = abs(pooled_before - c4_target)
    c4_pass = c4_diff <= 0.001
    print(f"C4: recomputed before = {pooled_before:.4f} kWh/m^2, "
          f"target = {c4_target}, |diff| = {c4_diff:.6f}, "
          f"{'PASS' if c4_pass else 'FAIL'}")
    if not c4_pass:
        raise SystemExit(
            f"C4 GATE FAILED: recomputed before-figure {pooled_before:.4f} "
            f"does not reproduce {c4_target} within 0.001. STOPPING per plan "
            f"instruction -- no adjustment made."
        )

    sum_dh_total_kwh = sub["dh_total_kwh"].sum()
    sum_dh_ws_kwh = sub["dh_water_systems_gj"].sum() * GJ_TO_KWH
    c5_rel_diff = abs(sum_dh_total_kwh - sum_dh_ws_kwh) / sum_dh_ws_kwh
    c5_pass = c5_rel_diff <= 0.0001
    print(f"C5: sum(dh_total_kwh) = {sum_dh_total_kwh:.4f}, "
          f"sum(dh_water_systems_gj)*277.7778 = {sum_dh_ws_kwh:.4f}, "
          f"relative diff = {c5_rel_diff*100:.6f}%, "
          f"{'PASS' if c5_pass else 'FAIL'}")
    if not c5_pass:
        raise SystemExit(
            f"C5 GATE FAILED: relative diff {c5_rel_diff*100:.6f}% exceeds "
            f"0.01%. STOPPING per plan instruction -- no adjustment made."
        )

    print(f"\nPooled before: {pooled_before:.4f} kWh/m^2 (n={n})")
    print(f"Pooled after:  {pooled_after:.4f} kWh/m^2 (n={n})")
    print(f"Delta:         {delta:.4f} kWh/m^2 ({delta/pooled_before*100:.2f}%)")

    # --- Per-cell split ---
    rows = []
    rows.append({
        "level": "fleet", "key": "ALL", "n": n,
        "pooled_before_kwh_m2": round(pooled_before, 4),
        "pooled_after_kwh_m2": round(pooled_after, 4),
        "delta_kwh_m2": round(delta, 4),
    })

    cell_grp = sub.groupby("cell")
    cell_rows = []
    for cell, g in cell_grp:
        b = pooled(g, "parsed_total_eui_kwh_m2")
        a = pooled(g, "after_total_eui_kwh_m2")
        cell_rows.append({
            "level": "cell", "key": cell, "n": len(g),
            "pooled_before_kwh_m2": round(b, 4),
            "pooled_after_kwh_m2": round(a, 4),
            "delta_kwh_m2": round(a - b, 4),
        })
    cell_rows.sort(key=lambda r: -abs(r["delta_kwh_m2"]))
    rows.extend(cell_rows)

    # --- Per-archetype split ---
    arch_grp = sub.groupby("archetype_id")
    arch_rows = []
    for arch, g in arch_grp:
        b = pooled(g, "parsed_total_eui_kwh_m2")
        a = pooled(g, "after_total_eui_kwh_m2")
        arch_rows.append({
            "level": "archetype", "key": arch, "n": len(g),
            "pooled_before_kwh_m2": round(b, 4),
            "pooled_after_kwh_m2": round(a, 4),
            "delta_kwh_m2": round(a - b, 4),
        })
    arch_rows.sort(key=lambda r: -abs(r["delta_kwh_m2"]))
    rows.extend(arch_rows)

    # --- Tall class isolation ---
    tall_mask = sub["archetype_id"].isin(TALL_ARCHETYPES)
    tall = sub.loc[tall_mask]
    non_tall = sub.loc[~tall_mask]
    n_tall = len(tall)

    tall_dh_sum_kwh = tall["dh_total_kwh"].sum()
    total_dh_sum_kwh = sub["dh_total_kwh"].sum()
    tall_share_of_dh = tall_dh_sum_kwh / total_dh_sum_kwh

    b_tall = pooled(tall, "parsed_total_eui_kwh_m2")
    a_tall = pooled(tall, "after_total_eui_kwh_m2")
    delta_tall = a_tall - b_tall

    b_notall = pooled(non_tall, "parsed_total_eui_kwh_m2")
    a_notall = pooled(non_tall, "after_total_eui_kwh_m2")
    delta_notall = a_notall - b_notall

    rows.append({
        "level": "tall_class", "key": f"TALL_{n_tall}", "n": n_tall,
        "pooled_before_kwh_m2": round(b_tall, 4),
        "pooled_after_kwh_m2": round(a_tall, 4),
        "delta_kwh_m2": round(delta_tall, 4),
    })
    rows.append({
        "level": "tall_class", "key": "NON_TALL", "n": len(non_tall),
        "pooled_before_kwh_m2": round(b_notall, 4),
        "pooled_after_kwh_m2": round(a_notall, 4),
        "delta_kwh_m2": round(delta_notall, 4),
    })

    print(f"\nTall class (n={n_tall}, {TALL_ARCHETYPES}): "
          f"{tall_share_of_dh*100:.1f}% of Sigma dh_total_kwh")
    print(f"  tall pooled before/after/delta: "
          f"{b_tall:.4f} / {a_tall:.4f} / {delta_tall:.4f} kWh/m^2")
    print(f"Excluding tall class (n={len(non_tall)}): "
          f"before/after/delta: {b_notall:.4f} / {a_notall:.4f} / {delta_notall:.4f} kWh/m^2")

    # --- Building-level distribution of the change ---
    change = sub["dh_eui_kwh_m2"]
    median = change.median()
    q1 = change.quantile(0.25)
    q3 = change.quantile(0.75)
    iqr = q3 - q1
    p90 = change.quantile(0.90)
    mx = change.max()
    n_zero = int((sub["dh_total_kwh"] == 0.0).sum())

    print(f"\nBuilding-level change distribution (n={n}):")
    print(f"  median={median:.4f}, IQR=[{q1:.4f}, {q3:.4f}] ({iqr:.4f}), "
          f"p90={p90:.4f}, max={mx:.4f}")
    print(f"  buildings moving by exactly 0.0: {n_zero} / {n}")

    rows.append({
        "level": "distribution", "key": "median", "n": n,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": round(median, 4),
    })
    rows.append({
        "level": "distribution", "key": "iqr_q1", "n": n,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": round(q1, 4),
    })
    rows.append({
        "level": "distribution", "key": "iqr_q3", "n": n,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": round(q3, 4),
    })
    rows.append({
        "level": "distribution", "key": "p90", "n": n,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": round(p90, 4),
    })
    rows.append({
        "level": "distribution", "key": "max", "n": n,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": round(mx, 4),
    })
    rows.append({
        "level": "distribution", "key": "n_zero_change", "n": n_zero,
        "pooled_before_kwh_m2": None, "pooled_after_kwh_m2": None,
        "delta_kwh_m2": 0.0,
    })

    out = pd.DataFrame(rows)
    out.to_csv(CSV_OUT, index=False)
    print(f"\nWritten: {CSV_OUT}")


if __name__ == "__main__":
    main()
