"""Finalize la_centre 226/226: compute gates, write report, copy deliverables.

Reads the already-aggregated Step 5 results (05_results.gpkg + summary) from the
repair2 run, computes F12 + CBECS gates, writes the 226/226 gates report, and
copies all final deliverables to docs/.../cases/la_centre/.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd
import geopandas as gpd

RUNTIME = REPO / "runtime" / "ubem_validation" / "cases" / "la_centre"
RESULTS_DIR = RUNTIME / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / "la_centre"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

CELL_NAME = "la_centre"
LAT, LON = 34.0522, -118.2437
EPW_STATION = "Los.Angeles.Downtown-USC.Campus.722874"
MAIN_JOB_ID = "964556"
REPAIR1_JOB_ID = "964792"
REPAIR2_JOB_ID = "964804"


def main() -> None:
    from openubem.results import compute_validation_gates
    from openubem import config as cfg

    idf_mf = pd.read_parquet(RUNTIME / "step3" / "03_idf_manifest.parquet")
    sim_mf = pd.read_parquet(RUNTIME / "04_simulation_manifest.parquet")
    results_gdf = gpd.read_file(str(RESULTS_DIR / "05_results.gpkg"))
    summary = json.loads((RESULTS_DIR / "05_neighbourhood_summary.json").read_text())

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse = n_parsed / n_sim_success if n_sim_success > 0 else 0.0

    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)

    n_gen = int((idf_mf["generation_status"] == "success").sum())
    n_total = len(idf_mf)
    n_unknown = int((idf_mf["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_gen = n_gen / n_total

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")

    print("=== GATES (226/226) ===")
    print(f"pct_parse_success: {pct_parse*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={pct_parse>=0.99}")
    print(f"EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={pct_plausible>=0.99}")
    if len(outliers):
        print(f"EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"zone_mismatch: {n_zone_mismatch} PASS={n_zone_mismatch==0}")
    print(f"IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")
    print(f"CBECS CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
    print(f"CBECS NMBE: {cbecs_gates['cbecs_nmbe']:.3f}% PASS={cbecs_gates['cbecs_nmbe_pass']}")
    print(f"CBECS R2: {cbecs_gates['cbecs_r2']} PASS={cbecs_gates['cbecs_r2_pass']}")
    print(f"CBECS KS_D: {cbecs_gates['cbecs_ks_d']:.4f} PASS={cbecs_gates['cbecs_ks_d_pass']}")
    print(f"HEADLINE: heat {eui_map.get('heating_eui_kwh_m2'):.2f} / cool {eui_map.get('cooling_eui_kwh_m2'):.2f} "
          f"/ light {eui_map.get('lighting_eui_kwh_m2'):.2f} / equip {eui_map.get('equipment_eui_kwh_m2'):.2f} "
          f"/ total {eui_map.get('total_eui_kwh_m2'):.2f}")
    print(f"GWP: {gwp:,.0f}  mean_iod {mean_iod:.4f}  p95_iod {p95_iod:.4f}")
    print(f"Archetype mix: {dict(parsed['archetype_id'].value_counts())}")

    lines = [
        "=" * 72,
        f"V12 {CELL_NAME.upper()} GATES REPORT (226/226 — after repair2 way/425993506)",
        f"  Cell:   {CELL_NAME}  ({LAT}, {LON}) r=500m",
        f"  EPW:    {EPW_STATION}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): 182",
        f"  Actual OSM fetch:    226",
        f"  Generation success:  {n_gen}/{n_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {n_gen}/{n_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{n_total} = {(n_unknown/n_total)*100:.1f}%  (<20%: {'PASS' if n_unknown/n_total<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_ids: {MAIN_JOB_ID} (main, 223/225) + {REPAIR1_JOB_ID} (repair1, 2/2) + {REPAIR2_JOB_ID} (repair2, 1/1)",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== REPAIR RECORD ===",
        f"  way/427817502: perimeter_core IndexError -> single_zone, job 964792_1, 0 Severe",
        f"  way/427817541: perimeter_core IndexError -> single_zone, job 964792_2, 0 Severe",
        f"  way/425993506 (repair2): perimeter_core IndexError (geomeppy break_polygons) -> single_zone, job {REPAIR2_JOB_ID}_1, 15 Warning 0 Severe",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse*100:.2f}% ({n_parsed}/{n_sim_success})  PASS={pct_parse>=0.99}",
        f"  EUI_plausibility [25,1000]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)})  PASS={pct_plausible>=0.99}",
    ]
    if len(outliers):
        lines.append(f"  EUI outliers: n={len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    lines += [
        f"  zone_count_integrity: {n_zone_mismatch} mismatches  PASS={n_zone_mismatch==0}",
        "",
        "=== IOD ===",
        f"  n={len(iod_vals)}, mean={iod_vals.mean():.4f}C, p95={iod_vals.quantile(0.95):.4f}C",
        "",
        "=== CBECS 2018 NE VALIDATION GATES (report-only per V-R5-5) ===",
        f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}",
        f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}",
        f"  R2:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}",
        f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}   PASS={cbecs_gates['cbecs_ks_d_pass']}",
        "  Note: CBECS gates are report-only per ruling V-R5-5; FAIL does not block.",
        "",
        "=== HEADLINE NUMBERS (neighbourhood_eui_weighted) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            lines.append(f"  {k}: {v:.2f} kWh/m2/yr")
    if gwp:
        lines.append(f"  GWP: {gwp:,.0f} kgCO2e")
    if mean_iod is not None:
        lines.append(f"  mean_iod_c: {mean_iod:.4f} C")
    if p95_iod is not None:
        lines.append(f"  p95_iod_c: {p95_iod:.4f} C")
    lines.append(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")
    if "archetype_id" in parsed.columns:
        lines += ["", "=== ARCHETYPE MIX (simulated success) ==="]
        for arch, cnt in parsed["archetype_id"].value_counts().items():
            lines.append(f"  {arch}: {cnt}")
    lines += ["", "=" * 72, "END REPORT", "=" * 72]
    report = "\n".join(lines)

    report_path = RESULTS_DIR / f"v12_{CELL_NAME}_gates_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nGates report written: {report_path}")

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(RESULTS_DIR.rglob("*")):
        if src.is_file():
            dst = FINAL_DIR / src.relative_to(RESULTS_DIR)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    sim_mf_src = RUNTIME / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        shutil.copy2(sim_mf_src, FINAL_DIR / "04_simulation_manifest.parquet")
        copied += 1
    print(f"Copied {copied} files to {FINAL_DIR}")


if __name__ == "__main__":
    main()
