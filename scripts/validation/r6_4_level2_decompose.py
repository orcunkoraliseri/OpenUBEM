"""R6-4 T01–T03: Level-2 gap decomposition.

Inventory-first (T01): read roundtrip_report.csv; decide Tier-1 (data on disk) or
Tier-2 (must resim).  Tier-2 resim is conditional on --tier 2 or --tier auto.

T03: per-end-use contribution decomposition persisted as CSV + MD.

Usage:
  py -3 scripts/validation/r6_4_level2_decompose.py [--tier auto|1|2]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).parent.parent.parent
RESULTS_DIR = REPO / "docs" / "validations" / "overAll" / "results"
ROUNDTRIP_CSV = RESULTS_DIR / "roundtrip_report.csv"
MANIFEST_PARQUET = REPO / "runtime" / "ubem_validation" / "level2" / "counterparts_2d" / "03_idf_manifest.parquet"
ENDUSE_CSV = RESULTS_DIR / "r6_4_level2_enduse.csv"
DECOMP_CSV = RESULTS_DIR / "r6_4_decomposition.csv"
DECOMP_MD = RESULTS_DIR / "r6_4_decomposition.md"

THERMAL_RUNAWAY_DCS = {"LargeDataCenterHighITE", "LargeDataCenterLowITE", "SmallDataCenterHighITE"}


def _tier_decision(df: pd.DataFrame) -> str:
    """Return 'Tier-1' if all 4 per-end-use columns non-null for all success rows."""
    success = df[df["counter_status"] == "success"]
    cols = ["ref_heat", "ref_cool", "ref_light", "ref_equip",
            "counter_heat", "counter_cool", "counter_light", "counter_equip"]
    complete = success.dropna(subset=cols)
    if len(complete) >= len(success) and len(complete) > 0:
        return "Tier-1"
    return "Tier-2"


def _build_enduse_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Build r6_4_level2_enduse.csv from roundtrip_report.csv (Tier-1 path)."""
    try:
        manifest = pd.read_parquet(MANIFEST_PARQUET)
        mf_idx = manifest.set_index("ref_filename")
    except Exception:
        manifest = None
        mf_idx = None

    rows = []
    for _, r in df.iterrows():
        arch = r["openuben_archetype"]
        status = r["counter_status"]
        ref_fn = r["ref_filename"]

        if status == "failed" or arch in THERMAL_RUNAWAY_DCS:
            rows.append({
                "archetype": arch,
                "side": "ref",
                "heating": None, "cooling": None, "lighting": None,
                "equipment": None, "other": None, "total_eui_kwh_m2": r.get("ref_total_eui"),
                "floor_area_m2": None, "zoning_strategy": "N/A", "n_zones": None, "status": "N/A",
            })
            rows.append({
                "archetype": arch,
                "side": "counterpart",
                "heating": None, "cooling": None, "lighting": None,
                "equipment": None, "other": None, "total_eui_kwh_m2": None,
                "floor_area_m2": None, "zoning_strategy": "N/A", "n_zones": None, "status": "N/A",
            })
            continue

        ref_total = float(r["ref_total_eui"])
        ref_heat = float(r["ref_heat"])
        ref_cool = float(r["ref_cool"])
        ref_light = float(r["ref_light"])
        ref_equip = float(r["ref_equip"])
        ref_other = ref_total - (ref_heat + ref_cool + ref_light + ref_equip)

        ctr_total = float(r["counter_total_eui"])
        ctr_heat = float(r["counter_heat"])
        ctr_cool = float(r["counter_cool"])
        ctr_light = float(r["counter_light"])
        ctr_equip = float(r["counter_equip"])
        ctr_other = ctr_total - (ctr_heat + ctr_cool + ctr_light + ctr_equip)

        zoning = "unknown"
        n_zones = None
        if mf_idx is not None and ref_fn in mf_idx.index:
            mrow = mf_idx.loc[ref_fn]
            zoning = str(mrow["zoning_strategy"])
            n_zones = int(mrow["num_zones"])

        rows.append({
            "archetype": arch, "side": "ref",
            "heating": ref_heat, "cooling": ref_cool, "lighting": ref_light,
            "equipment": ref_equip, "other": ref_other, "total_eui_kwh_m2": ref_total,
            "floor_area_m2": None, "zoning_strategy": zoning, "n_zones": n_zones,
            "status": "success",
        })
        rows.append({
            "archetype": arch, "side": "counterpart",
            "heating": ctr_heat, "cooling": ctr_cool, "lighting": ctr_light,
            "equipment": ctr_equip, "other": ctr_other, "total_eui_kwh_m2": ctr_total,
            "floor_area_m2": None, "zoning_strategy": zoning, "n_zones": n_zones,
            "status": "success",
        })

    out = pd.DataFrame(rows)
    out.to_csv(ENDUSE_CSV, index=False)
    print(f"[T01] r6_4_level2_enduse.csv written: {ENDUSE_CSV}")
    return out


def _decompose(df_report: pd.DataFrame) -> pd.DataFrame:
    """T03: per-end-use contribution decomposition."""
    success = df_report[df_report["counter_status"] == "success"].copy()

    for eu, ref_col, ctr_col in [
        ("heat", "ref_heat", "counter_heat"),
        ("cool", "ref_cool", "counter_cool"),
        ("light", "ref_light", "counter_light"),
        ("equip", "ref_equip", "counter_equip"),
    ]:
        success[f"contrib_{eu}"] = (
            (success[ctr_col] - success[ref_col]) / success["ref_total_eui"] * 100
        )

    success["ref_other"] = (
        success["ref_total_eui"]
        - success["ref_heat"] - success["ref_cool"]
        - success["ref_light"] - success["ref_equip"]
    )
    success["counter_other"] = (
        success["counter_total_eui"]
        - success["counter_heat"] - success["counter_cool"]
        - success["counter_light"] - success["counter_equip"]
    )
    success["contrib_other"] = (
        (success["counter_other"] - success["ref_other"]) / success["ref_total_eui"] * 100
    )

    success["contrib_sum"] = (
        success["contrib_heat"] + success["contrib_cool"]
        + success["contrib_light"] + success["contrib_equip"] + success["contrib_other"]
    )

    # Flag dominant end-use (by absolute contribution magnitude, excluding "other")
    eu_cols = ["contrib_heat", "contrib_cool", "contrib_light", "contrib_equip"]
    success["dominant_eu"] = success[eu_cols].abs().idxmax(axis=1).str.replace("contrib_", "")

    # Assert invariant: contributions sum = total dev to within 0.01%
    residual = (success["contrib_sum"] - success["dev_pct"]).abs()
    bad = residual[residual > 0.01]
    if len(bad) > 0:
        print(f"[T03] WARNING: contribution sum residual > 0.01% for: {list(bad.index)}")

    out_cols = [
        "openuben_archetype", "dev_pct", "verdict_5pct",
        "contrib_heat", "contrib_cool", "contrib_light", "contrib_equip", "contrib_other",
        "contrib_sum", "dominant_eu",
        "ref_total_eui", "counter_total_eui",
    ]
    decomp = success[out_cols].copy()
    decomp = decomp.sort_values("dev_pct", key=abs, ascending=False)
    decomp.to_csv(DECOMP_CSV, index=False)
    print(f"[T03] r6_4_decomposition.csv written: {DECOMP_CSV}")
    return decomp


def _write_decomp_md(decomp: pd.DataFrame) -> None:
    """T03: human-readable decomposition markdown table."""
    lines = [
        "# R6-4 Level-2 Gap Decomposition",
        "",
        "Per-end-use contribution to total deviation: `(counter_i - ref_i) / ref_total × 100`.",
        "Contributions sum to total dev% by construction.",
        "",
        "| Archetype | Dev% | Verdict | ΔHeat | ΔCool | ΔLight | ΔEquip | ΔOther | DomEU |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in decomp.iterrows():
        lines.append(
            f"| {r['openuben_archetype']} | {r['dev_pct']:+.1f} | {r['verdict_5pct']} |"
            f" {r['contrib_heat']:+.1f} | {r['contrib_cool']:+.1f} |"
            f" {r['contrib_light']:+.1f} | {r['contrib_equip']:+.1f} |"
            f" {r['contrib_other']:+.1f} | {r['dominant_eu']} |"
        )
    lines += [
        "",
        "**Key:** Dev% = (counter_total − ref_total)/ref_total × 100.  "
        "ΔX = (counter_X − ref_X)/ref_total × 100.  Sum(ΔHeat+ΔCool+ΔLight+ΔEquip+ΔOther) = Dev%.",
        "",
        f"N non-N/A archetypes: {len(decomp)}  |  N/A (thermal runaway): 3",
    ]
    DECOMP_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[T03] r6_4_decomposition.md written: {DECOMP_MD}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["auto", "1", "2"], default="auto")
    args = parser.parse_args()

    print("=" * 60)
    print("R6-4 Level-2 Gap Decomposition — T01 Inventory")
    print("=" * 60)

    df = pd.read_csv(ROUNDTRIP_CSV)
    print(f"\n[T01] roundtrip_report.csv columns: {list(df.columns)}")
    print(f"[T01] Total rows: {len(df)}")

    tier = _tier_decision(df)
    if args.tier == "1":
        tier = "Tier-1"
    elif args.tier == "2":
        tier = "Tier-2"

    print(f"\n[T01] TIER DECISION: {tier}")

    success = df[df["counter_status"] == "success"]
    na_rows = df[df["counter_status"] == "failed"]
    print(f"[T01] Success rows (non-N/A): {len(success)}")
    print(f"[T01] N/A (thermal runaway): {list(na_rows['openuben_archetype'])}")

    if tier == "Tier-2":
        print("[T02] Tier-2 detected — EnergyPlus resim required (not run in this script).")
        print("[T02] Run T02 resim logic or verify data completeness before proceeding.")
        sys.exit(1)

    print("\n[T01] Tier-1 confirmed: all per-end-use EUI already in roundtrip_report.csv")
    print("[T01] No EnergyPlus resim needed.")

    enduse_df = _build_enduse_csv(df)

    print("\n" + "=" * 60)
    print("R6-4 T03 — Per-end-use decomposition")
    print("=" * 60)
    decomp = _decompose(df)
    _write_decomp_md(decomp)

    print("\n[T03] Decomposition table (sorted by |dev%|):")
    print(decomp[[
        "openuben_archetype", "dev_pct", "verdict_5pct",
        "contrib_heat", "contrib_cool", "contrib_light", "contrib_equip", "contrib_other",
        "dominant_eu"
    ]].to_string(index=False))

    print("\n[CP-A] Contribution sum invariant check:")
    residual = (decomp["contrib_sum"] - decomp["dev_pct"]).abs()
    print(f"  Max residual: {residual.max():.6f}%  (threshold 0.01%)")
    print(f"  All OK: {(residual < 0.01).all()}")

    print("\n[CP-A] Done. Tier-1, no resim. See:")
    print(f"  {ENDUSE_CSV}")
    print(f"  {DECOMP_CSV}")
    print(f"  {DECOMP_MD}")


if __name__ == "__main__":
    main()
