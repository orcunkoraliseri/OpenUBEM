"""T03 of PLAN_vintage-elasticity-2026-08-19.md.

Reads the baseline (scale=1.0, already on disk from the predecessor arc) and the two
elasticity variants (scale=0.7, scale=1.3, produced by T02 of this plan) for the same
20-building subset, extracts ABUPS End-Uses per building per variant directly from each
eplusout.sql (RowName x fuel columns, summed, GJ -> kWh), computes EUI as
ABUPS Total End Uses / multiplier-aware simulated floor area (never total_eui_kwh_m2,
OPEN-60), and writes:

  - openubem/outputs/comparisons/open03_load_elasticity.csv       (per building x variant)
  - openubem/outputs/comparisons/open03_elasticity_summary.csv    (one row per variant)

Reuses the ABUPS End Uses query pattern from
scripts/analysis/open03_enduse_decomposition_2026-08-19.py (itself following
openubem/results/parser.py:629-637), extended to all RowNames and all fuel columns.

Read-only against openubem/. Writes only to openubem/outputs/comparisons/.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

BASELINE_ENDUSE_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open03_enduse_by_building.csv"
BASELINE_SQL_ROOT = REPO_ROOT / "scratchpad" / "open03-untrimmed-sample"
ELASTICITY_ROOT = REPO_ROOT / "openubem" / "outputs" / "open03_elasticity"
OUT_DETAIL_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open03_load_elasticity.csv"
OUT_SUMMARY_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open03_elasticity_summary.csv"

GJ_TO_KWH = 277.7778

END_USE_ROWS = [
    "Heating", "Cooling", "Interior Lighting", "Exterior Lighting",
    "Interior Equipment", "Exterior Equipment", "Fans", "Pumps",
    "Heat Rejection", "Humidification", "Heat Recovery", "Water Systems",
    "Refrigeration", "Generators",
]
# NOTE ON DEVIATION: scripts/analysis/open03_enduse_decomposition_2026-08-19.py's own
# END_USE_ROWS list (7 rows) under-reconciles by design for this sample -- the
# ASHRAE-90.1-2022 baseline-path archetypes (SmallOffice, MediumOffice, RetailStandalone,
# Warehouse) carry nonzero "Exterior Lighting" (parking-lot/facade lighting) that the
# fallback-template archetypes (OpenUBEMUnknown, Courthouse) do not; the 7-row list also
# omits Exterior Equipment/Heat Rejection/Humidification/Heat Recovery/Refrigeration/
# Generators, all standard ABUPS "End Uses" RowNames. Verified against
# TabularDataWithStrings directly for way/328529693 (scale 0.7): the full 14-row RowName
# set (excluding blank-RowName spacer rows) sums to 75.36 GJ vs ABUPS "Total End Uses"
# 75.37 GJ -- 0.01 GJ apart, i.e. ABUPS's own 2-decimal print rounding, not a defect.
# The 14-row list here is used instead so the T03(d) reconciliation control is meaningful.
END_USE_COLS = [r.replace(" ", "_") for r in END_USE_ROWS]

END_USE_QUERY = """
SELECT RowName, COALESCE(SUM(CAST(Value AS REAL)), 0.0) AS gj
FROM TabularDataWithStrings
WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
  AND TableName = 'End Uses'
  AND Units = 'GJ'
  AND RowName IN ({placeholders})
GROUP BY RowName
"""

SAMPLE_20 = [
    ("austin_centre", "way/1008727470"), ("austin_centre", "way/328529693"),
    ("austin_rural", "way/1165379866"), ("austin_rural", "way/1480414338"),
    ("austin_rural", "way/762128912"), ("austin_rural", "way/1450171441"),
    ("austin_suburban", "way/382992872"), ("austin_urban", "way/381810583"),
    ("la_centre", "way/905248736"), ("la_centre", "way/427817563"),
    ("la_rural", "way/472961221"), ("nyc_centre", "way/265424467"),
    ("nyc_rural", "way/772627016"), ("nyc_rural", "way/772627029"),
    ("nyc_rural", "way/270445757"), ("nyc_rural", "way/772627043"),
    ("nyc_suburban", "way/846412106"), ("nyc_suburban", "way/815835776"),
    ("nyc_suburban", "way/610017070"), ("nyc_urban", "way/241862488"),
]

POOLED_GAP_PCT = -23.93  # PLAN §1/§6, corrected ABUPS-basis pooled gap, 20-building subset

# T02 finding: for archetypes with a registered layout_assign baseline IDF
# (openubem/idf/builder.py:69-79 _layout_assign_baseline_path -> layout_assigner.get_registry()
# .get_baseline_idf(archetype_id)), BuildingIDF.__init__ loads that static ASHRAE-90.1-2022
# prototype .idf wholesale and assign_loads()'s LIGHTS/ELECTRICEQUIPMENT objects for those
# buildings' zones (Core_ZN, Perimeter_ZN_1..4, named per the baseline prototype, not the
# footprint-derived zones) never appear in the written .idf -- verified by direct diff of the
# 0.7 vs 1.3 .idf text for way/328529693 (SmallOffice): Watts_per_Zone_Floor_Area = 6.181254
# in BOTH, byte-identical. Archetypes confirmed to have a registered baseline (loads_reach_model
# = False for these): SmallOffice, MediumOffice, RetailStandalone, Warehouse. Archetypes
# confirmed to have none (loads_reach_model = True): OpenUBEMUnknown, Courthouse.
BASELINE_PATH_ARCHETYPES = {"SmallOffice", "MediumOffice", "RetailStandalone", "Warehouse"}


def loads_reach_model(archetype_id: str) -> bool:
    return archetype_id not in BASELINE_PATH_ARCHETYPES


def extract_end_uses(sql_path: Path) -> dict[str, float] | None:
    if not sql_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = ["Total End Uses"] + END_USE_ROWS
        placeholders = ",".join("?" for _ in rows)
        q = END_USE_QUERY.format(placeholders=placeholders)
        result = dict(conn.execute(q, rows).fetchall())
        conn.close()
    except sqlite3.Error as exc:
        return {"_error": str(exc)}
    out = {}
    for r in END_USE_ROWS:
        out[r] = result.get(r, 0.0) * GJ_TO_KWH
    out["Total End Uses"] = result.get("Total End Uses", 0.0) * GJ_TO_KWH
    return out


def variant_rows(scale: float) -> list[dict]:
    join_csv = ELASTICITY_ROOT / str(scale) / "open03_elasticity_sample_join.csv"
    join = pd.read_csv(join_csv, dtype={"osm_id": str})
    join = join.set_index(["cell", "osm_id"])

    rows = []
    for cell, osm_id in SAMPLE_20:
        safe_id = osm_id.replace("/", "_")
        sql_path = ELASTICITY_ROOT / str(scale) / cell / "sim" / safe_id / "eplusout.sql"
        eu = extract_end_uses(sql_path)

        rec = {"variant": f"scale_{scale}", "scale": scale, "cell": cell, "osm_id": osm_id}
        if (cell, osm_id) in join.index:
            jrow = join.loc[(cell, osm_id)]
            if isinstance(jrow, pd.DataFrame):
                jrow = jrow.iloc[0]
            rec["archetype_id"] = jrow.get("archetype_id")
            rec["floor_area_m2"] = jrow.get("floor_area_m2")
            rec["parse_status"] = jrow.get("parse_status")
        else:
            rec["archetype_id"] = None
            rec["floor_area_m2"] = None
            rec["parse_status"] = "missing_from_join_csv"

        if eu is None:
            rec["extract_status"] = "file_missing"
            rows.append(rec)
            continue
        if "_error" in eu:
            rec["extract_status"] = f"sql_error:{eu['_error']}"
            rows.append(rec)
            continue

        rec["extract_status"] = "ok"
        for r, c in zip(END_USE_ROWS, END_USE_COLS):
            rec[c] = eu[r]
        rec["Total_End_Uses_kwh"] = eu["Total End Uses"]
        sum_end_uses = sum(eu[r] for r in END_USE_ROWS)
        rec["sum_end_uses_kwh"] = sum_end_uses
        total = eu["Total End Uses"]
        rec["reconcile_rel_err_pct"] = (
            abs(sum_end_uses - total) / total * 100.0 if total > 0 else None
        )
        rec["reconciled_within_2pct"] = (
            bool(rec["reconcile_rel_err_pct"] <= 2.0) if rec["reconcile_rel_err_pct"] is not None else False
        )
        fa = rec["floor_area_m2"]
        rec["eui_kwh_m2"] = total / fa if fa and fa > 0 else None
        rows.append(rec)
    return rows


def baseline_rows() -> list[dict]:
    """scale=1.0 reference point. Not re-run (plan §3.6): floor_area_m2/archetype_id come
    from the existing open03_enduse_by_building.csv join; end-use kWh are re-extracted
    directly from the baseline .sql (scratchpad/open03-untrimmed-sample/) with the full
    14-row END_USE_ROWS list here, rather than trusting that CSV's own 7-row extraction
    (which under-reconciles for baseline-path archetypes -- see note above END_USE_ROWS)."""
    meta = pd.read_csv(BASELINE_ENDUSE_CSV, dtype={"osm_id": str}).set_index(["cell", "osm_id"])
    rows = []
    for cell, osm_id in SAMPLE_20:
        rec = {"variant": "scale_1.0", "scale": 1.0, "cell": cell, "osm_id": osm_id}
        if (cell, osm_id) not in meta.index:
            rec["extract_status"] = "missing_from_baseline_csv"
            rows.append(rec)
            continue
        mrow = meta.loc[(cell, osm_id)]
        if isinstance(mrow, pd.DataFrame):
            mrow = mrow.iloc[0]
        rec["archetype_id"] = mrow.get("archetype_id")
        rec["floor_area_m2"] = mrow.get("floor_area_m2")
        rec["parse_status"] = "success"

        safe_id = osm_id.replace("/", "_")
        sql_path = BASELINE_SQL_ROOT / cell / "sim" / safe_id / "eplusout.sql"
        eu = extract_end_uses(sql_path)
        if eu is None:
            rec["extract_status"] = "file_missing"
            rows.append(rec)
            continue
        if "_error" in eu:
            rec["extract_status"] = f"sql_error:{eu['_error']}"
            rows.append(rec)
            continue

        rec["extract_status"] = "ok"
        for r, c in zip(END_USE_ROWS, END_USE_COLS):
            rec[c] = eu[r]
        rec["Total_End_Uses_kwh"] = eu["Total End Uses"]
        sum_end_uses = sum(eu[r] for r in END_USE_ROWS)
        rec["sum_end_uses_kwh"] = sum_end_uses
        total = eu["Total End Uses"]
        rec["reconcile_rel_err_pct"] = abs(sum_end_uses - total) / total * 100.0 if total > 0 else None
        rec["reconciled_within_2pct"] = (
            bool(rec["reconcile_rel_err_pct"] <= 2.0) if rec["reconcile_rel_err_pct"] is not None else False
        )
        fa = rec["floor_area_m2"]
        rec["eui_kwh_m2"] = total / fa if fa and fa > 0 else None
        rows.append(rec)
    return rows


def main() -> None:
    all_rows = baseline_rows() + variant_rows(0.7) + variant_rows(1.3)
    detail = pd.DataFrame(all_rows)

    n07 = ((detail["variant"] == "scale_0.7") & (detail["extract_status"] == "ok")).sum()
    n13 = ((detail["variant"] == "scale_1.3") & (detail["extract_status"] == "ok")).sum()
    print(f"[T03] extracted ok: scale_0.7={n07}/20  scale_1.3={n13}/20")

    n_recon_07 = ((detail["variant"] == "scale_0.7") & (detail["reconciled_within_2pct"] == True)).sum()
    n_recon_13 = ((detail["variant"] == "scale_1.3") & (detail["reconciled_within_2pct"] == True)).sum()
    print(f"[T03] RECONCILIATION (sum of end uses vs ABUPS Total End Uses, within 2%): "
          f"scale_0.7={n_recon_07}/{n07}  scale_1.3={n_recon_13}/{n13}  combined={n_recon_07+n_recon_13}/40")
    worst = detail[detail["variant"].isin(["scale_0.7", "scale_1.3"])].copy()
    worst = worst[worst["reconcile_rel_err_pct"].notna()].sort_values("reconcile_rel_err_pct", ascending=False)
    if len(worst):
        wr = worst.iloc[0]
        print(f"[T03] worst reconciliation error: {wr['reconcile_rel_err_pct']:.4f}% at "
              f"{wr['variant']}/{wr['cell']}/{wr['osm_id']}")

    # per-building elasticity, wide join on (cell, osm_id)
    base = detail[detail["variant"] == "scale_1.0"].set_index(["cell", "osm_id"])
    v07 = detail[detail["variant"] == "scale_0.7"].set_index(["cell", "osm_id"])
    v13 = detail[detail["variant"] == "scale_1.3"].set_index(["cell", "osm_id"])

    elas_rows = []
    for cell, osm_id in SAMPLE_20:
        key = (cell, osm_id)
        b = base.loc[key] if key in base.index else None
        r7 = v07.loc[key] if key in v07.index else None
        r13 = v13.loc[key] if key in v13.index else None
        if b is None or b.get("eui_kwh_m2") is None:
            continue
        eui_b = b["eui_kwh_m2"]
        rec = {"cell": cell, "osm_id": osm_id, "archetype_id": b.get("archetype_id"), "eui_baseline": eui_b}
        if r7 is not None and r7.get("eui_kwh_m2") is not None:
            pct_eui = (r7["eui_kwh_m2"] - eui_b) / eui_b * 100.0
            rec["pct_change_eui_minus30"] = pct_eui
            rec["elasticity_minus30"] = pct_eui / -30.0
        if r13 is not None and r13.get("eui_kwh_m2") is not None:
            pct_eui = (r13["eui_kwh_m2"] - eui_b) / eui_b * 100.0
            rec["pct_change_eui_plus30"] = pct_eui
            rec["elasticity_plus30"] = pct_eui / 30.0
        elas_rows.append(rec)
    elas_df = pd.DataFrame(elas_rows)
    elas_df["loads_reach_model"] = elas_df["archetype_id"].map(loads_reach_model)

    print("\n[T03] per-building elasticity (%dEUI / %dscale):")
    print(elas_df[["cell", "osm_id", "archetype_id", "loads_reach_model",
                    "elasticity_minus30", "elasticity_plus30"]].to_string(index=False))

    n_reach = int(elas_df["loads_reach_model"].sum())
    n_noreach = int((~elas_df["loads_reach_model"]).sum())
    print(f"\n[T03] loads_reach_model: True (scale actually reaches the IDF) = {n_reach}/20; "
          f"False (baseline-path archetype, scale never reaches the IDF) = {n_noreach}/20")

    mean_e_minus = elas_df["elasticity_minus30"].mean()
    median_e_minus = elas_df["elasticity_minus30"].median()
    mean_e_plus = elas_df["elasticity_plus30"].mean()
    median_e_plus = elas_df["elasticity_plus30"].median()
    print(f"\n[T03] mean/median elasticity at -30%: {mean_e_minus:.4f} / {median_e_minus:.4f}")
    print(f"[T03] mean/median elasticity at +30%: {mean_e_plus:.4f} / {median_e_plus:.4f}")

    # pooled elasticity: (Sigma energy / Sigma area) both sides
    def pooled_eui(df: pd.DataFrame) -> float:
        ok = df[df["extract_status"] == "ok"]
        return ok["Total_End_Uses_kwh"].sum() / ok["floor_area_m2"].sum()

    b_ok = detail[detail["variant"] == "scale_1.0"]
    v07_ok = detail[detail["variant"] == "scale_0.7"]
    v13_ok = detail[detail["variant"] == "scale_1.3"]

    pooled_eui_b = pooled_eui(b_ok)
    pooled_eui_07 = pooled_eui(v07_ok)
    pooled_eui_13 = pooled_eui(v13_ok)
    pooled_pct_minus = (pooled_eui_07 - pooled_eui_b) / pooled_eui_b * 100.0
    pooled_pct_plus = (pooled_eui_13 - pooled_eui_b) / pooled_eui_b * 100.0
    pooled_elas_minus = pooled_pct_minus / -30.0
    pooled_elas_plus = pooled_pct_plus / 30.0
    print(f"\n[T03] pooled EUI: baseline={pooled_eui_b:.4f}  scale_0.7={pooled_eui_07:.4f} "
          f"({pooled_pct_minus:.3f}%)  scale_1.3={pooled_eui_13:.4f} ({pooled_pct_plus:.3f}%)")
    print(f"[T03] pooled elasticity: minus30={pooled_elas_minus:.4f}  plus30={pooled_elas_plus:.4f}")

    ratio = max(pooled_elas_minus, pooled_elas_plus) / min(pooled_elas_minus, pooled_elas_plus)
    print(f"[T03] pooled elasticity ratio (max/min) = {ratio:.3f} -- "
          f"{'AGREE (<=1.5x)' if ratio <= 1.5 else 'DISAGREE (>1.5x), report as range'}")

    # reachable-only pooled elasticity (n=4: archetypes with no registered baseline IDF)
    reach_ids = set(elas_df.loc[elas_df["loads_reach_model"], "osm_id"])

    def pooled_eui_subset(df: pd.DataFrame, ids: set) -> float:
        ok = df[(df["extract_status"] == "ok") & (df["osm_id"].isin(ids))]
        return ok["Total_End_Uses_kwh"].sum() / ok["floor_area_m2"].sum()

    r_eui_b = pooled_eui_subset(b_ok, reach_ids)
    r_eui_07 = pooled_eui_subset(v07_ok, reach_ids)
    r_eui_13 = pooled_eui_subset(v13_ok, reach_ids)
    r_pct_minus = (r_eui_07 - r_eui_b) / r_eui_b * 100.0
    r_pct_plus = (r_eui_13 - r_eui_b) / r_eui_b * 100.0
    r_elas_minus = r_pct_minus / -30.0
    r_elas_plus = r_pct_plus / 30.0
    print(f"\n[T03] REACHABLE-ONLY (n=4) pooled EUI: baseline={r_eui_b:.4f}  "
          f"scale_0.7={r_eui_07:.4f} ({r_pct_minus:.3f}%)  scale_1.3={r_eui_13:.4f} ({r_pct_plus:.3f}%)")
    print(f"[T03] REACHABLE-ONLY pooled elasticity: minus30={r_elas_minus:.4f}  plus30={r_elas_plus:.4f}")

    # inversion: k required to close half / all of POOLED_GAP_PCT using pooled_elas_plus
    # (extrapolation is upward-scale direction, matching the sign needed to close a negative gap)
    target_half = abs(POOLED_GAP_PCT) / 2.0
    target_all = abs(POOLED_GAP_PCT)

    def k_for(target_pct_change: float, elasticity: float) -> float:
        pct_scale_needed = target_pct_change / elasticity
        return 1.0 + pct_scale_needed / 100.0

    k_half_plus = k_for(target_half, pooled_elas_plus)
    k_all_plus = k_for(target_all, pooled_elas_plus)
    k_half_minus = k_for(target_half, pooled_elas_minus)
    k_all_minus = k_for(target_all, pooled_elas_minus)
    print(f"\n[T03] INVERSION (ALL 20, diluted by 16 non-reachable) using plus30 slope: "
          f"k(half)={k_half_plus:.4f}  k(all)={k_all_plus:.4f}")
    print(f"[T03] INVERSION (ALL 20) using minus30 slope: k(half)={k_half_minus:.4f}  k(all)={k_all_minus:.4f}")

    r_k_half_plus = k_for(target_half, r_elas_plus)
    r_k_all_plus = k_for(target_all, r_elas_plus)
    r_k_half_minus = k_for(target_half, r_elas_minus)
    r_k_all_minus = k_for(target_all, r_elas_minus)
    print(f"[T03] INVERSION (REACHABLE-ONLY, n=4) using plus30 slope: "
          f"k(half)={r_k_half_plus:.4f}  k(all)={r_k_all_plus:.4f}")
    print(f"[T03] INVERSION (REACHABLE-ONLY, n=4) using minus30 slope: "
          f"k(half)={r_k_half_minus:.4f}  k(all)={r_k_all_minus:.4f}")

    # heating/cooling counter-movement, pooled, both variants
    def pooled_delta(df_variant: pd.DataFrame, df_base: pd.DataFrame, col: str) -> float:
        v = df_variant[df_variant["extract_status"] == "ok"].set_index(["cell", "osm_id"])[col]
        b = df_base[df_base["extract_status"] == "ok"].set_index(["cell", "osm_id"])[col]
        common = v.index.intersection(b.index)
        return v.loc[common].sum() - b.loc[common].sum()

    summary_rows = []
    for label, df_variant, sc, pct_scale in [
        ("scale_0.7", v07_ok, 0.7, -30.0), ("scale_1.3", v13_ok, 1.3, 30.0)
    ]:
        d_heat = pooled_delta(df_variant, b_ok, "Heating")
        d_cool = pooled_delta(df_variant, b_ok, "Cooling")
        d_light = pooled_delta(df_variant, b_ok, "Interior_Lighting")
        d_equip = pooled_delta(df_variant, b_ok, "Interior_Equipment")
        d_fans = pooled_delta(df_variant, b_ok, "Fans")
        d_pumps = pooled_delta(df_variant, b_ok, "Pumps")
        d_water = pooled_delta(df_variant, b_ok, "Water_Systems")
        d_total = pooled_delta(df_variant, b_ok, "Total_End_Uses_kwh")
        d_lightequip = d_light + d_equip
        counter = d_heat + d_cool
        counter_pct_of_gross = counter / d_lightequip * 100.0 if d_lightequip else float("nan")

        n_ok = int((df_variant["extract_status"] == "ok").sum())
        n_recon = int((df_variant["reconciled_within_2pct"] == True).sum())

        elas_col_minus = "elasticity_minus30" if sc == 0.7 else None
        row = {
            "variant": label, "scale": sc, "pct_change_scale": pct_scale,
            "n_extracted_ok": n_ok, "n_reconciled_2pct": n_recon,
            "pooled_eui_baseline": pooled_eui_b,
            "pooled_eui_variant": pooled_eui_07 if sc == 0.7 else pooled_eui_13,
            "pooled_pct_change_eui": pooled_pct_minus if sc == 0.7 else pooled_pct_plus,
            "pooled_elasticity": pooled_elas_minus if sc == 0.7 else pooled_elas_plus,
            "mean_per_building_elasticity": mean_e_minus if sc == 0.7 else mean_e_plus,
            "median_per_building_elasticity": median_e_minus if sc == 0.7 else median_e_plus,
            "delta_Heating_kwh_pooled": d_heat,
            "delta_Cooling_kwh_pooled": d_cool,
            "delta_Interior_Lighting_kwh_pooled": d_light,
            "delta_Interior_Equipment_kwh_pooled": d_equip,
            "delta_Fans_kwh_pooled": d_fans,
            "delta_Pumps_kwh_pooled": d_pumps,
            "delta_Water_Systems_kwh_pooled": d_water,
            "delta_lighting_plus_equipment_kwh_pooled": d_lightequip,
            "delta_Total_End_Uses_kwh_pooled": d_total,
            "heating_cooling_counter_movement_kwh_pooled": counter,
            "counter_movement_pct_of_gross_lightequip_delta": counter_pct_of_gross,
            "k_half_gap": k_half_minus if sc == 0.7 else k_half_plus,
            "k_all_gap": k_all_minus if sc == 0.7 else k_all_plus,
            "reachable_n": 4,
            "reachable_pooled_eui_baseline": r_eui_b,
            "reachable_pooled_eui_variant": r_eui_07 if sc == 0.7 else r_eui_13,
            "reachable_pooled_pct_change_eui": r_pct_minus if sc == 0.7 else r_pct_plus,
            "reachable_pooled_elasticity": r_elas_minus if sc == 0.7 else r_elas_plus,
            "reachable_k_half_gap": r_k_half_minus if sc == 0.7 else r_k_half_plus,
            "reachable_k_all_gap": r_k_all_minus if sc == 0.7 else r_k_all_plus,
            "pooled_gap_pct_target": POOLED_GAP_PCT,
        }
        summary_rows.append(row)
        print(f"\n[T03] {label}: dHeating={d_heat:.1f}  dCooling={d_cool:.1f}  "
              f"dLight+Equip={d_lightequip:.1f}  counter={counter:.1f}  "
              f"counter_pct_of_gross={counter_pct_of_gross:.2f}%  dTotal={d_total:.1f}")

    summary_df = pd.DataFrame(summary_rows)

    detail = detail.merge(
        elas_df[["cell", "osm_id", "elasticity_minus30", "elasticity_plus30", "loads_reach_model"]],
        on=["cell", "osm_id"], how="left",
    )

    OUT_DETAIL_CSV.parent.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUT_DETAIL_CSV, index=False)
    summary_df.to_csv(OUT_SUMMARY_CSV, index=False)
    print(f"\n[T03] wrote {OUT_DETAIL_CSV} rows={len(detail)}")
    print(f"[T03] wrote {OUT_SUMMARY_CSV} rows={len(summary_df)}")


if __name__ == "__main__":
    main()
