r"""V11: Step-5 aggregate_results for NYC city-centre pilot cell.

Inputs:
  %TEMP%\ubem_validation\cases\nyc_centre\sim_out\<osm_id>\eplusout.{sql,err,end}
  %TEMP%\ubem_validation\cases\nyc_centre\step3\03_idf_manifest.parquet
  %TEMP%\ubem_validation\cases\nyc_centre\02a_climate_epw.parquet
  %TEMP%\ubem_validation\cases\nyc_centre\gdf_57.pkl  (enriched GDF from steps 1-2)

Outputs:
  %TEMP%\ubem_validation\cases\nyc_centre\results\  (05_* files)
  docs\validations\overAll\results\cases\nyc_centre\  (final deliverables per V-R5-7)
"""
from __future__ import annotations

import json
import pickle
import re as _re
import shutil
import sys
import tempfile
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).parent.parent.parent
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

NYC_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / "nyc_centre"
SIM_OUT_DIR = NYC_BASE / "sim_out"
STEP3_DIR = NYC_BASE / "step3"
IDF_MANIFEST_PATH = STEP3_DIR / "03_idf_manifest.parquet"
CLIMATE_SIDECAR_PATH = NYC_BASE / "02a_climate_epw.parquet"
GDF_PKL_PATH = NYC_BASE / "gdf_57.pkl"

RESULTS_DIR = NYC_BASE / "results"
RESULTS_DIR.mkdir(exist_ok=True)

FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / "nyc_centre"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

EPW_PATH = NYC_BASE / "weather" / "USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw"
EP_VERSION = "23.1.0"

print(f"[V11] IDF manifest: {IDF_MANIFEST_PATH}")
print(f"[V11] SIM out dir:  {SIM_OUT_DIR}")
print(f"[V11] Results dir:  {RESULTS_DIR}")
print(f"[V11] Final dir:    {FINAL_DIR}")

idf_mf = pd.read_parquet(IDF_MANIFEST_PATH)
print(f"[V11] IDF manifest: {len(idf_mf)} rows")

sim_dirs = sorted(p for p in SIM_OUT_DIR.iterdir() if p.is_dir())
print(f"[V11] sim_out subdirs: {len(sim_dirs)}")

_floor_rx = _re.compile(r"_F(\d+)_")


def _parse_end(end_path: Path) -> str:
    if not end_path.exists():
        return "failed"
    txt = end_path.read_text(errors="replace")
    return "success" if "EnergyPlus Completed Successfully" in txt else "failed"


def _parse_err(err_path: Path) -> tuple[int, int, str]:
    if not err_path.exists():
        return 0, 0, "err missing"
    txt = err_path.read_text(errors="replace")
    matches = _re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", txt)
    if matches:
        nw, ns = int(matches[-1][0]), int(matches[-1][1])
    else:
        nw, ns = 0, 0
    severes = [l.strip() for l in txt.splitlines() if "** Severe **" in l]
    return nw, ns, (severes[0] if severes else "")


sim_rows = []
for bdir in sim_dirs:
    osm_id_str = bdir.name
    # normalise osm_id: sim_out dir uses e.g. "way_265302069", manifest uses "way/265302069"
    osm_id_norm = osm_id_str.replace("_", "/", 1) if "_" in osm_id_str and "/" not in osm_id_str else osm_id_str
    sql_path = bdir / "eplusout.sql"
    end_path = bdir / "eplusout.end"
    err_path = bdir / "eplusout.err"

    status = _parse_end(end_path)
    n_warnings, n_severe, error_summary = _parse_err(err_path)

    sim_rows.append({
        "osm_id": osm_id_norm,
        "idf_path": str(STEP3_DIR / "idfs" / f"{osm_id_str}.idf"),
        "work_dir": str(bdir),
        "sql_path": str(sql_path) if sql_path.exists() else "",
        "status": status,
        "n_warnings": n_warnings,
        "n_severe": n_severe,
        "wall_clock_s": 0.0,
        "ep_version": EP_VERSION,
        "epw_path": str(EPW_PATH),
        "error_summary": error_summary,
        "csv_path": None,
    })

sim_mf = pd.DataFrame(sim_rows)
sim_mf_path = NYC_BASE / "04_simulation_manifest.parquet"
sim_mf.to_parquet(sim_mf_path, index=False)
print(f"[V11] sim manifest: {len(sim_mf)} rows, status: {sim_mf['status'].value_counts().to_dict()}")

if _parse_end(SIM_OUT_DIR / "way_265302069" / "eplusout.end") != "success":
    raise RuntimeError("way_265302069 should be success (repair2 IDF ran OK) — check sim_out")

print("[V11] Loading enriched GDF from gdf_57.pkl ...")
t0 = time.monotonic()
with open(GDF_PKL_PATH, "rb") as _f:
    _pkl = pickle.load(_f)
enriched_gdf: gpd.GeoDataFrame = _pkl[0] if isinstance(_pkl, tuple) else _pkl
print(f"[V11] Enriched GDF: {enriched_gdf.shape} CRS={enriched_gdf.crs} ({time.monotonic()-t0:.1f}s)")

print("[V11] Step 5: aggregate_results...")
t1 = time.monotonic()
from openubem.results import aggregate_results

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    results_gdf = aggregate_results(
        sim_mf,
        idf_mf,
        enriched_gdf,
        RESULTS_DIR,
        climate_sidecar=CLIMATE_SIDECAR_PATH,
        state="NY",
        make_figures=True,
        ep_version=EP_VERSION,
    )
wall_step5 = time.monotonic() - t1
print(f"[V11] aggregate_results completed in {wall_step5:.1f}s")

from openubem import config

print("\n=== F12 GATE TABLE ===")
success_statuses = {"success", "success_cached", "success_csv_fallback"}
sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
n_sim_success = len(sim_success)
parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99
print(f"pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={gate_pct_parse}")

lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
print(f"EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={gate_eui}")
if len(outliers) > 0:
    print(f"  Outliers ({len(outliers)}): min={outliers.min():.1f}, max={outliers.max():.1f}")

zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0
print(f"Zone-count integrity: {n_zone_mismatch} mismatches PASS={gate_zone}")

failed_parse = results_gdf[results_gdf["simulation_status"] == "failed_parse"]
print(f"failed_parse buildings: {len(failed_parse)}")

iod_vals = parsed["iod"].dropna()
print(f"\nIOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p50={iod_vals.median():.4f}, p95={iod_vals.quantile(0.95):.4f}, max={iod_vals.max():.4f}")

print("\n=== CBECS 2018 NORTHEAST GATES ===")
from openubem.results import compute_validation_gates

results_for_cbecs = results_gdf.copy()
if "eui_kwh_m2" not in results_for_cbecs.columns and "site_eui_kwh_m2" not in results_for_cbecs.columns:
    results_for_cbecs["site_eui_kwh_m2"] = results_for_cbecs["total_eui_kwh_m2"]

cbecs_gates = compute_validation_gates(results_for_cbecs, reference_path=CBECS_PATH)
print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% (threshold <30.0%) PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}% (threshold <10.0%) PASS={cbecs_gates['cbecs_nmbe_pass']}")
print(f"  R²:       {cbecs_gates['cbecs_r2']} (threshold >0.6) PASS={cbecs_gates['cbecs_r2_pass']}")
print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f} (threshold <0.10) PASS={cbecs_gates['cbecs_ks_d_pass']}")
print(f"  n_sim_buildings: {cbecs_gates['n_sim_buildings']}")

summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    print("\n=== HEADLINE NUMBERS ===")
    eui = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui.get(k)
        if v is not None:
            print(f"  {k}: {v:.4f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  neighbourhood_gwp_total_kgco2: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    print(f"  mean_iod_c: {mean_iod:.4f}" if mean_iod else "  mean_iod_c: N/A")
    print(f"  p95_iod_c: {p95_iod:.4f}" if p95_iod else "  p95_iod_c: N/A")
    print(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

if "archetype_id" in results_gdf.columns:
    print("\n=== EUI by archetype ===")
    arch_stats = parsed.groupby("archetype_id")["total_eui_kwh_m2"].agg(["count", "mean", "median"])
    print(arch_stats.to_string())

gates_all = gate_pct_parse and gate_eui and gate_zone
print(f"\n=== F12 SUMMARY: {'ALL PASS' if gates_all else 'SOME FAILED'} ===")

gates_report_lines = [
    "=" * 72,
    "V11 NYC CITY-CENTRE GATES REPORT — 2026-06-12",
    f"  sim_out dir: {SIM_OUT_DIR}",
    f"  IDF manifest: {IDF_MANIFEST_PATH}",
    "=" * 72,
    "",
    "=== F12 GATE TABLE ===",
    f"{'Gate':<42} {'Value':>16}  {'Result':>6}",
    "-" * 68,
    f"{'pct_parse_success >= 99%':<42} {pct_parse_success*100:>15.2f}%  {'PASS' if gate_pct_parse else 'FAIL':>6}",
    f"{'  n_parsed / n_sim_success':<42} {f'{n_parsed}/{n_sim_success}':>16}  {'':>6}",
    f"{'EUI plausibility >= 99% in [25,1000]':<42} {pct_plausible*100:>15.2f}%  {'PASS' if gate_eui else 'FAIL':>6}",
    f"{'  n_in_range / n_valid_eui':<42} {f'{in_range}/{len(valid_eui)}':>16}  {'':>6}",
]
if len(outliers) > 0:
    gates_report_lines.append(f"{'  EUI outliers: min / max':<42} {outliers.min():>7.1f} / {outliers.max():>6.1f}  {'':>6}")
gates_report_lines += [
    f"{'zone_count_integrity = 0 mismatches':<42} {n_zone_mismatch:>16}  {'PASS' if gate_zone else 'FAIL':>6}",
    "",
    f"  Overall (3 live CSV-recomputable gates): {'ALL PASS' if gates_all else 'SOME FAILED'}",
    "",
    "=== CBECS 2018 NORTHEAST VALIDATION GATES (report-only per V-R5-5) ===",
    f"  n_sim_buildings (after exclusions): {cbecs_gates['n_sim_buildings']}",
    f"  n_excluded_all_gates: {cbecs_gates['n_excluded_all_gates']}",
    "",
    f"{'Metric':<12} {'Threshold':>12} {'R3 Boston':>14} {'Boston P/F':>10} {'NYC Result':>12} {'NYC P/F':>8}",
    "-" * 74,
    f"{'CV(RMSE)%':<12} {'< 30.0%':>12} {'69.823':>14} {'FAIL':>10} {cbecs_gates['cbecs_cv_rmse']:>12.3f} {'PASS' if cbecs_gates['cbecs_cv_rmse_pass'] else 'FAIL':>8}",
    f"{'NMBE%':<12} {'< |10|%':>12} {'-16.046':>14} {'FAIL':>10} {cbecs_gates['cbecs_nmbe']:>12.3f} {'PASS' if cbecs_gates['cbecs_nmbe_pass'] else 'FAIL':>8}",
]
r2_str = f"{cbecs_gates['cbecs_r2']:.4f}" if cbecs_gates['cbecs_r2'] is not None else "N/A"
gates_report_lines += [
    f"{'R2':<12} {'> 0.6':>12} {'0.7312':>14} {'PASS':>10} {r2_str:>12} {'PASS' if cbecs_gates['cbecs_r2_pass'] else 'FAIL':>8}",
    f"{'KS_D':<12} {'< 0.10':>12} {'0.2730':>14} {'FAIL':>10} {cbecs_gates['cbecs_ks_d']:>12.4f} {'PASS' if cbecs_gates['cbecs_ks_d_pass'] else 'FAIL':>8}",
    "",
    "  Note: CBECS gates are report-only per ruling V-R5-5/M-R2-4.",
]

if summary_path.exists():
    eui = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    gates_report_lines += [
        "",
        "=== HEADLINE NUMBERS (05_neighbourhood_summary.json) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui.get(k)
        if v is not None:
            gates_report_lines.append(f"  {k}: {v:.4f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        gates_report_lines.append(f"  neighbourhood_gwp_total_kgco2: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    if mean_iod is not None:
        gates_report_lines.append(f"  mean_iod_c: {mean_iod:.4f} deg C")
    if p95_iod is not None:
        gates_report_lines.append(f"  p95_iod_c: {p95_iod:.4f} deg C")
    pfa = summary.get("pct_floor_area_simulated")
    if pfa is not None:
        gates_report_lines.append(f"  pct_floor_area_simulated: {pfa*100:.1f}%")

gates_report_lines += ["", "=" * 72, "END REPORT", "=" * 72]
gates_report = "\n".join(gates_report_lines)
gates_report_path = RESULTS_DIR / "v11_gates_report.txt"
gates_report_path.write_text(gates_report, encoding="utf-8")
print(f"\n[V11] Gates report: {gates_report_path}")

print("\n[V11] Copying final deliverables to docs/validations/overAll/results/cases/nyc_centre/ ...")
final_files = []
for f in sorted(RESULTS_DIR.rglob("*")):
    if f.is_file():
        dest = FINAL_DIR / f.relative_to(RESULTS_DIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        final_files.append(dest)
        print(f"  {dest.relative_to(REPO)}")

print(f"\n[V11] {len(final_files)} final files in {FINAL_DIR}")
print(f"[V11] step5 wall clock: {wall_step5:.1f}s")
print("[V11] DONE")
