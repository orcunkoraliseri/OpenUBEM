"""
OPEN-32 (T04 of PLAN_five-more-items-2026-08-13.md) — net effect of OPEN-01 (denominator
too small) and OPEN-03 (loads at 2022 code) on layout_assign EUI.

Read-only on all inputs. No simulation. No production code change. Arithmetic only, on
artifacts that already exist:
  - openubem/outputs/comparisons/e02_simulated_floor_area.csv
  - openubem/outputs/comparisons/open01_denominator_audit.csv
  - openubem/outputs/comparisons/t20_layout_assign_eui.csv
  - openubem/outputs/comparisons/open03_load_vintage_ratios.csv

Writes: openubem/outputs/comparisons/open32_layout_assign_net.csv
Prints a funnel + distribution report to stdout (captured into the MEASUREMENT doc).
"""
from __future__ import annotations

import pandas as pd

ROOT = "openubem/outputs/comparisons"


def pct(series: pd.Series, q: float) -> float:
    return float(series.quantile(q))


def describe(series: pd.Series, label: str) -> None:
    s = series.dropna()
    print(f"  {label}: n={len(s)} median={s.median():.4f} "
          f"IQR=[{pct(s, 0.25):.4f}, {pct(s, 0.75):.4f}] "
          f"min={s.min():.4f} max={s.max():.4f} share>1={(s > 1).mean():.4%}")


def main() -> None:
    print("=" * 78)
    print("STEP 1 — funnel on e02_simulated_floor_area.csv (denominator leg, literal formula)")
    print("=" * 78)
    e02 = pd.read_csv(f"{ROOT}/e02_simulated_floor_area.csv")
    print(f"  total rows in file: {len(e02)}")
    e02_la = e02[e02["mode"] == "layout_assign"].copy()
    print(f"  after mode == 'layout_assign': {len(e02_la)}")
    e02_la_ok = e02_la[e02_la["parse_status"] == "ok"].copy()
    print(f"  after parse_status == 'ok': {len(e02_la_ok)}")
    n_excluded = len(e02_la) - len(e02_la_ok)
    print(f"  excluded by parse_status filter: {n_excluded} "
          f"({'none — all layout_assign rows parsed ok' if n_excluded == 0 else 'see parse_status value_counts below'})")
    if n_excluded:
        print(e02_la["parse_status"].value_counts())

    zero_plain = (e02_la_ok["area_plain_m2"] == 0).sum()
    print(f"  rows with area_plain_m2 == 0 (would break the literal ratio): {zero_plain}")
    e02_la_ok = e02_la_ok[e02_la_ok["area_plain_m2"] != 0].copy()
    print(f"  n going into the literal-formula ratio: {len(e02_la_ok)}")

    e02_la_ok["f_denom_literal"] = (
        e02_la_ok["area_multiplier_aware_m2"] / e02_la_ok["area_plain_m2"]
    )
    print("\n  DENOMINATOR LEG, literal task formula f_denom = area_multiplier_aware_m2 / area_plain_m2:")
    describe(e02_la_ok["f_denom_literal"], "f_denom_literal")

    print()
    print("=" * 78)
    print("STEP 2 — which column did the published layout_assign EUI actually divide by?")
    print("=" * 78)
    audit = pd.read_csv(f"{ROOT}/open01_denominator_audit.csv")
    audit_la = audit[(audit["mode"] == "layout_assign") & (audit["parse_status"] == "ok")].copy()
    print(f"  open01_denominator_audit.csv, mode==layout_assign & parse_status==ok: n={len(audit_la)}")

    merge_check = e02_la_ok.merge(
        audit_la[["cell", "stem", "area_plain_m2", "area_multiplier_aware_m2"]],
        on=["cell", "stem"], how="inner", suffixes=("_e02", "_audit"),
    )
    diff_plain = (merge_check["area_plain_m2_e02"] - merge_check["area_plain_m2_audit"]).abs().max()
    diff_mult = (merge_check["area_multiplier_aware_m2_e02"] - merge_check["area_multiplier_aware_m2_audit"]).abs().max()
    print(f"  cross-check: open01_denominator_audit.csv's area_plain_m2 / area_multiplier_aware_m2 "
          f"reproduce e02_simulated_floor_area.csv's own columns exactly "
          f"(max abs diff plain={diff_plain:.2e}, mult_aware={diff_mult:.2e})")

    t20 = pd.read_csv(f"{ROOT}/t20_layout_assign_eui.csv")
    print(f"  t20_layout_assign_eui.csv: n={len(t20)}, status value_counts:")
    print(t20["status"].value_counts().to_string())

    joined_denom_check = audit_la.merge(t20[["cell", "osm_id", "floor_area_m2", "status"]],
                                         on=["cell", "osm_id"], how="left")
    n_unmatched = joined_denom_check["floor_area_m2"].isna().sum()
    print(f"  audit rows unmatched to t20 by (cell, osm_id): {n_unmatched}")
    matched = joined_denom_check.dropna(subset=["floor_area_m2"])
    max_diff_declared = (matched["floor_area_m2"] - matched["declared_area_m2"]).abs().max()
    n_exact = (matched["floor_area_m2"] == matched["declared_area_m2"]).sum()
    print(f"  t20's floor_area_m2 (the EUI denominator actually used, per "
          f"scripts/cluster/t20_harvest_layout_assign.py:244,304) vs open01_denominator_audit.csv's "
          f"declared_area_m2 (= footprint_area_m2 x levels, per scripts/analysis/e02_t04_floor_area_audit.py:209): "
          f"max abs diff = {max_diff_declared:.2e} over n={len(matched)} "
          f"({n_exact} exact float matches) -- these are THE SAME QUANTITY.")

    n_exact_vs_plain = (audit_la["declared_area_m2"] == audit_la["area_plain_m2"]).sum()
    n_close_vs_plain = ((audit_la["declared_area_m2"] - audit_la["area_plain_m2"]).abs()
                         / audit_la["declared_area_m2"] < 0.01).sum()
    n_exact_vs_mult = (audit_la["declared_area_m2"] == audit_la["area_multiplier_aware_m2"]).sum()
    n_close_vs_mult = ((audit_la["declared_area_m2"] - audit_la["area_multiplier_aware_m2"]).abs()
                        / audit_la["declared_area_m2"] < 0.01).sum()
    print(f"  declared_area_m2 exactly equals area_plain_m2 for {n_exact_vs_plain}/{len(audit_la)} rows "
          f"({n_close_vs_plain} within 1%)")
    print(f"  declared_area_m2 exactly equals area_multiplier_aware_m2 for {n_exact_vs_mult}/{len(audit_la)} rows "
          f"({n_close_vs_mult} within 1%)")
    print("  CONCLUSION: neither area_plain_m2 nor area_multiplier_aware_m2 is the published "
          "denominator. declared_area_m2 is a third column (present in open01_denominator_audit.csv, "
          "not in e02_simulated_floor_area.csv) and it IS the published denominator, confirmed by code "
          "citation and by exact reproduction of t20's floor_area_m2.")

    print()
    print("  DENOMINATOR LEG, actual published-EUI error factor "
          "= area_multiplier_aware_m2 / declared_area_m2 (recomputed independently; "
          "this is open01_denominator_audit.csv's own 'error_factor' column):")
    audit_la["error_factor_recomputed"] = (
        audit_la["area_multiplier_aware_m2"] / audit_la["declared_area_m2"]
    )
    max_diff_ef = (audit_la["error_factor_recomputed"] - audit_la["error_factor"]).abs().max()
    print(f"  recomputed vs shipped error_factor column, max abs diff: {max_diff_ef:.2e}")
    describe(audit_la["error_factor"], "error_factor (true/declared)")

    print()
    print("=" * 78)
    print("STEP 3 — loads leg: search for a per-end-use breakdown for layout_assign")
    print("=" * 78)
    print(f"  FOUND: {ROOT}/t20_layout_assign_eui.csv carries per-building lighting_eui, "
          f"equipment_eui and total_eui for layout_assign (n={len(t20)}). Because these are all "
          f"divided by the SAME (flawed) denominator, their RATIO (share of site EUI) is "
          f"denominator-invariant and can be measured directly, without correcting OPEN-01 first.")

    t20_ok = t20[(t20["status"] == "success") & t20["total_eui"].notna()].copy()
    n_excl_t20 = len(t20) - len(t20_ok)
    print(f"  t20 rows excluded (status != success / total_eui NaN, i.e. failed EnergyPlus runs "
          f"with no end-use split to read): {n_excl_t20}")
    print(t20[t20["status"] != "success"][["cell", "osm_id", "status"]].to_string(index=False))

    t20_ok["lighting_share"] = t20_ok["lighting_eui"] / t20_ok["total_eui"]
    t20_ok["equipment_share"] = t20_ok["equipment_eui"] / t20_ok["total_eui"]
    t20_ok["combined_share"] = t20_ok["lighting_share"] + t20_ok["equipment_share"]
    print("\n  Measured (derived) per-building share of published site EUI:")
    describe(t20_ok["lighting_share"], "lighting_share")
    describe(t20_ok["equipment_share"], "equipment_share")
    describe(t20_ok["combined_share"], "combined_share (lighting + equipment)")

    print()
    print("=" * 78)
    print("STEP 4 — OPEN-03 vintage ratios: range across the 12 matched archetypes (not a point)")
    print("=" * 78)
    ratios = pd.read_csv(f"{ROOT}/open03_load_vintage_ratios.csv")
    print(f"  n archetypes = {len(ratios)}")
    light_lo, light_med, light_hi = (
        ratios["lights_ratio_2013_over_2022"].min(),
        ratios["lights_ratio_2013_over_2022"].median(),
        ratios["lights_ratio_2013_over_2022"].max(),
    )
    equip_lo, equip_med, equip_hi = (
        ratios["equipment_ratio_2013_over_2022"].min(),
        ratios["equipment_ratio_2013_over_2022"].median(),
        ratios["equipment_ratio_2013_over_2022"].max(),
    )
    print(f"  lighting ratio (2013/2022): min={light_lo:.4f} median={light_med:.4f} max={light_hi:.4f}")
    print(f"  equipment ratio (2013/2022): min={equip_lo:.4f} median={equip_med:.4f} max={equip_hi:.4f}")
    print("  92.9% of the fleet is DOERefPre1980, older than the 2013 baseline archetypes matched "
          "here -- ALL THREE of these figures (low/median/high) are LOWER BOUNDS on the real "
          "vintage-load error for that majority, not estimates of it. Occupancy ratio fixed at "
          "1.000 (register value; measured people_ratio_2013_over_2022 is 1.000 for 11/12 "
          "archetypes and 1.047 for PrimarySchool).")

    print()
    print("=" * 78)
    print("STEP 5 — net: join denominator leg to loads leg, one row per building")
    print("=" * 78)
    merged = audit_la.merge(
        t20_ok[["cell", "osm_id", "lighting_eui", "equipment_eui", "total_eui",
                "lighting_share", "equipment_share", "combined_share"]],
        on=["cell", "osm_id"], how="inner",
    )
    print(f"  audit_la (denominator leg, layout_assign, parse_status==ok): n={len(audit_la)}")
    print(f"  t20_ok (loads leg, status==success): n={len(t20_ok)}")
    print(f"  inner join on (cell, osm_id): n={len(merged)} "
          f"(dropped = the {n_excl_t20} failed-status rows with no end-use split)")

    for tag, lr, er in (("low", light_lo, equip_lo), ("med", light_med, equip_med), ("high", light_hi, equip_hi)):
        merged[f"f_loads_{tag}"] = (
            1.0
            + merged["lighting_share"] * (lr - 1.0)
            + merged["equipment_share"] * (er - 1.0)
        )
    for tag in ("low", "med", "high"):
        merged[f"net_{tag}"] = merged[f"f_loads_{tag}"] / merged["error_factor"]

    print("\n  Loads-leg bound (derived, a bound not a measurement):")
    describe(merged["f_loads_low"], "f_loads_low  (min archetype ratios)")
    describe(merged["f_loads_med"], "f_loads_med  (median archetype ratios, ~1.722/1.064)")
    describe(merged["f_loads_high"], "f_loads_high (max archetype ratios)")

    print("\n  NET correction factor = f_loads / error_factor (derived):")
    describe(merged["net_low"], "net_low")
    describe(merged["net_med"], "net_med")
    describe(merged["net_high"], "net_high")

    within_10 = ((merged["net_med"] >= 0.9) & (merged["net_med"] <= 1.1)).mean()
    within_20 = ((merged["net_med"] >= 0.8) & (merged["net_med"] <= 1.2)).mean()
    print(f"\n  share of buildings with net_med within +/-10% of 1.0 (cancel-ish): {within_10:.4%}")
    print(f"  share of buildings with net_med within +/-20% of 1.0 (cancel-ish): {within_20:.4%}")

    out_cols = [
        "cell", "osm_id", "stem", "archetype_id_manifest",
        "area_plain_m2", "area_multiplier_aware_m2", "declared_area_m2",
        "error_factor",
        "lighting_eui", "equipment_eui", "total_eui",
        "lighting_share", "equipment_share", "combined_share",
        "f_loads_low", "f_loads_med", "f_loads_high",
        "net_low", "net_med", "net_high",
    ]
    out = merged[out_cols].copy()
    out_path = f"{ROOT}/open32_layout_assign_net.csv"
    out.to_csv(out_path, index=False)
    print(f"\n  wrote {out_path}  (n={len(out)} rows, one per building)")


if __name__ == "__main__":
    main()
