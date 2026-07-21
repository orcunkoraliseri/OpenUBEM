"""Harvest + analyze the elevator A/B austin_urban sim (jobs 1116396 / 1116425).

Fetches 05-level results (eplusout.sql) for both arms from Speed, parses each
building via openubem.results.parser.parse_building, and reports:
  - per-arm sim success counts
  - cell total EUI: median AND area-weighted mean, Arm A vs Arm B
  - delta (absolute kWh/m2 and %), vs the +2.7% hand-estimate
  - HVAC-interaction component = simulated delta - pure-electric elevator adder
  - elevators_eui_kwh_m2 populated in A, zero/absent in B

Run only AFTER both arrays complete. Fetch = scp/tar (lightweight); no login-node compute.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd

from scripts.validation.v12_cell_pipeline import fetch_results

INFO = json.loads(
    Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_ab\austin_urban\ab_job_info.json").read_text()
)


def _floor_area_from_sql(sql_path: Path) -> float:
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        rows = conn.execute("SELECT FloorArea FROM Zones").fetchall()
        conn.close()
        return float(sum(r[0] for r in rows if r[0] is not None))
    except Exception:
        return float("nan")


def harvest_arm(arm: str, step3_dir: Path, remote_fleet_dir: str) -> pd.DataFrame:
    from openubem.results.parser import parse_building

    manifest = pd.read_parquet(step3_dir / "03_idf_manifest.parquet")
    # Manifest lacks the geometry attributes parse_building/derive_num_floors need
    # (levels, height_m, footprint_area_m2). Join them from the Stage-1 buildings gpkg on osm_id.
    import geopandas as gpd

    bldgs = gpd.read_file(step3_dir.parent / "01_buildings.gpkg")[
        ["osm_id", "levels", "height_m", "footprint_area_m2"]
    ]
    bldgs["osm_id"] = bldgs["osm_id"].astype(str)
    manifest["osm_id"] = manifest["osm_id"].astype(str)
    manifest = manifest.merge(bldgs, on="osm_id", how="left")
    success = manifest[manifest["generation_status"] == "success"].copy()
    osm_stems = [Path(str(r["idf_path"])).stem for _, r in success.iterrows()]

    sim_out = step3_dir.parent / f"sim_out_{arm}"
    # Skip re-fetch of buildings whose eplusout.sql is already local (fetch_results
    # has no skip-existing logic and re-tar+scp of all 425 SQL exceeds any time window).
    missing = [s for s in osm_stems if not (sim_out / s / "eplusout.sql").exists()]
    print(f"\n[Arm {arm}] {len(osm_stems)} total, {len(osm_stems) - len(missing)} cached, "
          f"fetching {len(missing)} -> {sim_out}", flush=True)
    if missing:
        fetch_results(missing, remote_fleet_dir, sim_out)

    rows = []
    n_ep_ok = 0
    for _, mrow in success.iterrows():
        stem = Path(str(mrow["idf_path"])).stem
        bdir = sim_out / stem
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        ep_ok = end_path.exists() and "EnergyPlus Completed Successfully" in end_path.read_text(errors="replace")
        if ep_ok:
            n_ep_ok += 1
        if not sql_path.exists():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            metrics = parse_building(sql_path, None, mrow)
        if metrics.get("parse_status") not in ("success", "success_cached", "success_csv_fallback"):
            continue
        metrics["floor_area_m2"] = _floor_area_from_sql(sql_path)
        metrics["archetype_id"] = mrow["archetype_id"]
        rows.append(metrics)

    df = pd.DataFrame(rows)
    print(f"[Arm {arm}] EnergyPlus success: {n_ep_ok}/{len(osm_stems)}; parsed OK: {len(df)}")
    return df


def cell_eui(df: pd.DataFrame) -> tuple[float, float]:
    valid = df[df["total_eui_kwh_m2"].notna() & df["floor_area_m2"].notna() & (df["floor_area_m2"] > 0)]
    median = float(valid["total_eui_kwh_m2"].median())
    w = valid["floor_area_m2"].values
    aw_mean = float(np.average(valid["total_eui_kwh_m2"].values, weights=w))
    return median, aw_mean


def main() -> None:
    step3_a = Path(INFO["step3_a_dir"])
    step3_b = Path(INFO["step3_b_dir"])

    df_a = harvest_arm("A", step3_a, INFO["remote_fleet_a"])
    df_b = harvest_arm("B", step3_b, INFO["remote_fleet_b"])

    df_a.to_parquet(step3_a.parent / "parsed_A.parquet")
    df_b.to_parquet(step3_b.parent / "parsed_B.parquet")

    # Align to the common set of buildings parsed OK in BOTH arms (apples-to-apples).
    common = sorted(set(df_a["osm_id"]) & set(df_b["osm_id"]))
    a = df_a[df_a["osm_id"].isin(common)].set_index("osm_id").sort_index()
    b = df_b[df_b["osm_id"].isin(common)].set_index("osm_id").sort_index()
    print(f"\nCommon buildings parsed in BOTH arms: {len(common)} "
          f"(A={len(df_a)}, B={len(df_b)})")

    med_a, awm_a = cell_eui(a.reset_index())
    med_b, awm_b = cell_eui(b.reset_index())

    d_med = med_a - med_b
    d_awm = awm_a - awm_b
    pct_med = 100 * d_med / med_b
    pct_awm = 100 * d_awm / awm_b

    # Pure-electric elevator adder = area-weighted mean of the elevators_eui column in Arm A.
    va = a[a["elevators_eui_kwh_m2"].notna() & (a["floor_area_m2"] > 0)]
    pure_elec_awm = float(np.average(va["elevators_eui_kwh_m2"].values, weights=va["floor_area_m2"].values))
    pure_elec_pct = 100 * pure_elec_awm / awm_b

    elev_a_nonzero = int((a["elevators_eui_kwh_m2"].fillna(0) > 0).sum())
    elev_b_nonzero = int((b["elevators_eui_kwh_m2"].fillna(0) > 0).sum())

    # HVAC interaction = simulated total delta - pure-electric adder (area-weighted).
    hvac_interaction_awm = d_awm - pure_elec_awm

    print("\n" + "=" * 72)
    print("ELEVATOR A/B RESULT — austin_urban")
    print("=" * 72)
    print(f"  Arm A (elevators): total EUI  median={med_a:.3f}  area-wt-mean={awm_a:.3f} kWh/m2")
    print(f"  Arm B (no elev):   total EUI  median={med_b:.3f}  area-wt-mean={awm_b:.3f} kWh/m2")
    print(f"  Delta (A-B):       median={d_med:+.3f} ({pct_med:+.2f}%)  "
          f"area-wt-mean={d_awm:+.3f} ({pct_awm:+.2f}%) kWh/m2")
    print(f"\n  Hand-estimate (pure-electric adder): +2.7%")
    print(f"  Simulated pure-electric adder (Arm A elevators_eui, area-wt): "
          f"{pure_elec_awm:.3f} kWh/m2 = {pure_elec_pct:+.2f}% of Arm B total")
    print(f"  Simulated TOTAL delta (area-wt-mean): {pct_awm:+.2f}%")
    print(f"  HVAC-interaction component (total delta - pure-electric adder): "
          f"{hvac_interaction_awm:+.3f} kWh/m2 = {pct_awm - pure_elec_pct:+.2f} pp")
    print(f"\n  elevators_eui_kwh_m2 > 0 count: Arm A = {elev_a_nonzero}/{len(a)}  "
          f"Arm B = {elev_b_nonzero}/{len(b)} (expect 0)")

    # Per-end-use area-weighted means to confirm non-elevator uses unchanged.
    print("\n  Per-end-use area-weighted mean (kWh/m2), A vs B:")
    for col in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
                "equipment_eui_kwh_m2", "fans_eui_kwh_m2", "pumps_eui_kwh_m2",
                "dhw_eui_kwh_m2", "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2",
                "elevators_eui_kwh_m2", "total_eui_kwh_m2"]:
        if col not in a.columns:
            continue
        va2 = a[a[col].notna() & (a["floor_area_m2"] > 0)]
        vb2 = b[b[col].notna() & (b["floor_area_m2"] > 0)]
        ma = float(np.average(va2[col].values, weights=va2["floor_area_m2"].values)) if len(va2) else float("nan")
        mb = float(np.average(vb2[col].values, weights=vb2["floor_area_m2"].values)) if len(vb2) else float("nan")
        print(f"    {col:26s} A={ma:9.4f}  B={mb:9.4f}  d={ma-mb:+9.4f}")

    result = {
        "cell": "austin_urban",
        "job_a": INFO["job_a"], "job_b": INFO["job_b"],
        "n_common": len(common), "n_parsed_a": len(df_a), "n_parsed_b": len(df_b),
        "median_a": med_a, "median_b": med_b,
        "awmean_a": awm_a, "awmean_b": awm_b,
        "delta_median_abs": d_med, "delta_median_pct": pct_med,
        "delta_awmean_abs": d_awm, "delta_awmean_pct": pct_awm,
        "pure_elec_adder_awm": pure_elec_awm, "pure_elec_adder_pct": pure_elec_pct,
        "hvac_interaction_awm": hvac_interaction_awm,
        "hvac_interaction_pp": pct_awm - pure_elec_pct,
        "elev_nonzero_a": elev_a_nonzero, "elev_nonzero_b": elev_b_nonzero,
    }
    out = Path(INFO["work_base"]) / "ab_result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\n  Result JSON -> {out}")
    print("=" * 72)


if __name__ == "__main__":
    main()
