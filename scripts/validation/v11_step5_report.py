"""V11 Step-5 report: aggregate_results + gates + deliverables for NYC city-centre.

Inputs  (all on local disk, no cluster/network):
  %TEMP%\\ubem_validation\\cases\\nyc_centre\\04_simulation_manifest.parquet
  %TEMP%\\ubem_validation\\cases\\nyc_centre\\step3\\03_idf_manifest.parquet
  %TEMP%\\ubem_validation\\cases\\nyc_centre\\02a_climate_epw.parquet
  %TEMP%\\ubem_validation\\cases\\nyc_centre\\gdf_57.pkl

Outputs (per V-R5-7):
  %TEMP%\\ubem_validation\\cases\\nyc_centre\\results\\  (05_* files + v11_gates_report.txt)
  docs\\validations\\overAll\\results\\cases\\nyc_centre\\  (final deliverables)
"""
from __future__ import annotations

import json
import pickle
import shutil
import sys
import tempfile
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).parent.parent.parent
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

NYC_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / "nyc_centre"
SIM_MANIFEST_PATH = NYC_BASE / "04_simulation_manifest.parquet"
IDF_MANIFEST_PATH = NYC_BASE / "step3" / "03_idf_manifest.parquet"
CLIMATE_SIDECAR_PATH = NYC_BASE / "02a_climate_epw.parquet"
GDF_PKL_PATH = NYC_BASE / "gdf_57.pkl"
STEP1_GPKG = NYC_BASE / "01_buildings.gpkg"

RESULTS_DIR = NYC_BASE / "results"
RESULTS_DIR.mkdir(exist_ok=True)

FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / "nyc_centre"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

EP_VERSION = "23.1.0"

print(f"[V11] REPO:            {REPO}")
print(f"[V11] NYC_BASE:        {NYC_BASE}")
print(f"[V11] RESULTS_DIR:     {RESULTS_DIR}")
print(f"[V11] FINAL_DIR:       {FINAL_DIR}")

# ── Load manifests ─────────────────────────────────────────────────────────────
sim_mf = pd.read_parquet(SIM_MANIFEST_PATH)
idf_mf = pd.read_parquet(IDF_MANIFEST_PATH)
v11_res = pd.read_csv(RESULTS_DIR / "v11_results.csv")

print(f"[V11] sim_mf: {len(sim_mf)} rows, status={dict(sim_mf['status'].value_counts())}")
print(f"[V11] idf_mf: {len(idf_mf)} rows")
print(f"[V11] v11_results.csv: {len(v11_res)} rows")

# ── LIVE_SMOKE funnel ──────────────────────────────────────────────────────────
step1_gdf = gpd.read_file(STEP1_GPKG)
n_fetched = len(step1_gdf)
n_enriched = len(idf_mf)
n_generated = int((idf_mf["generation_status"] == "success").sum())
n_simulated = int((sim_mf["status"] == "success").sum())

gen_success_pct = n_generated / n_fetched * 100 if n_fetched > 0 else 0.0
unknown_count = int((idf_mf["archetype_id"] == "OpenUBEMUnknown").sum())
unknown_pct = unknown_count / n_enriched * 100 if n_enriched > 0 else 0.0
sim_success_pct = n_simulated / n_generated * 100 if n_generated > 0 else 0.0

print(f"\n=== LIVE_SMOKE FUNNEL ===")
print(f"  fetched (Step 1):   {n_fetched}")
print(f"  enriched (Step 2):  {n_enriched}")
print(f"  generated (Step 3): {n_generated}  ({gen_success_pct:.1f}% of fetched)")
print(f"  simulated success:  {n_simulated}  ({sim_success_pct:.1f}% of generated)")
print(f"  Unknown archetype:  {unknown_count}  ({unknown_pct:.1f}% of enriched)")
print(f"  LIVE_SMOKE gen>=95%: {'PASS' if gen_success_pct >= 95.0 else 'FAIL'}")
print(f"  LIVE_SMOKE Unknown<20%: {'PASS' if unknown_pct < 20.0 else 'FAIL'}")

# ── Load enriched GDF ──────────────────────────────────────────────────────────
print("\n[V11] Loading enriched GDF from gdf_57.pkl ...")
t0 = time.monotonic()
with open(GDF_PKL_PATH, "rb") as _f:
    _pkl = pickle.load(_f)
enriched_gdf: gpd.GeoDataFrame = _pkl[0] if isinstance(_pkl, tuple) else _pkl
print(f"[V11] enriched_gdf: {enriched_gdf.shape}, CRS={enriched_gdf.crs}  ({time.monotonic()-t0:.1f}s)")

# ── Step 5: aggregate_results ─────────────────────────────────────────────────
print("\n[V11] Step 5: aggregate_results ...")
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
print(f"[V11] aggregate_results done in {wall_step5:.1f}s, results_gdf={results_gdf.shape}")

# ── F12 gates ─────────────────────────────────────────────────────────────────
from openubem import config

print("\n=== F12 GATE TABLE ===")
success_statuses = {"success", "success_cached", "success_csv_fallback"}
sim_success_rows = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
n_sim_success = len(sim_success_rows)
parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99

lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
in_range = int(((valid_eui >= lb) & (valid_eui <= ub)).sum())
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]

zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0

failed_parse = results_gdf[results_gdf["simulation_status"] == "failed_parse"]
gates_all = gate_pct_parse and gate_eui and gate_zone

print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={gate_pct_parse}")
print(f"  EUI plausibility [{lb},{ub}]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={gate_eui}")
if len(outliers) > 0:
    print(f"    Outliers ({len(outliers)}): min={outliers.min():.1f}, max={outliers.max():.1f}")
print(f"  zone_count_integrity: {n_zone_mismatch} mismatches PASS={gate_zone}")
print(f"  failed_parse: {len(failed_parse)}")
print(f"  Overall: {'ALL PASS' if gates_all else 'SOME FAILED'}")

# ── IOD ────────────────────────────────────────────────────────────────────────
iod_vals = parsed["iod"].dropna()
if len(iod_vals) > 0:
    print(f"\nIOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p50={iod_vals.median():.4f}, "
          f"p95={iod_vals.quantile(0.95):.4f}, max={iod_vals.max():.4f}")
else:
    print("\nIOD: N/A (not computable from available outputs — no outdoor-air data in IdealAir SQL)")

# ── CBECS gates ────────────────────────────────────────────────────────────────
print("\n=== CBECS 2018 NORTHEAST GATES (report-only, V-R5-5) ===")
from openubem.results import compute_validation_gates

results_for_cbecs = results_gdf.copy()
if "eui_kwh_m2" not in results_for_cbecs.columns and "site_eui_kwh_m2" not in results_for_cbecs.columns:
    results_for_cbecs["site_eui_kwh_m2"] = results_for_cbecs["total_eui_kwh_m2"]
cbecs_gates = compute_validation_gates(results_for_cbecs, reference_path=CBECS_PATH)

print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% (<30%) PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}% (<|10|%) PASS={cbecs_gates['cbecs_nmbe_pass']}")
print(f"  R2:       {cbecs_gates['cbecs_r2']} (>0.6) PASS={cbecs_gates['cbecs_r2_pass']}")
print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f} (<0.10) PASS={cbecs_gates['cbecs_ks_d_pass']}")
print(f"  n_sim_buildings (after exclusions): {cbecs_gates['n_sim_buildings']}")
print(f"  n_excluded: {cbecs_gates['n_excluded_all_gates']}")
print("  CAVEAT: CBECS reference is NE-region (CT/ME/MA/NH/NJ/NY/PA/RI/VT).")
print("  NYC is IN the NE region, so this comparison is valid for region-level benchmarking.")
print("  NYC city-centre fleet is predominantly commercial offices — same composition bias")
print("  as Boston R3. CBECS NE includes diverse types (hospitals, food service) that inflate")
print("  the CBECS reference mean. Gates are report-only per V-R5-5.")

# ── Headline numbers ────────────────────────────────────────────────────────────
summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
summary = {}
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    print("\n=== HEADLINE NUMBERS (05_neighbourhood_summary.json) ===")
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
    if mean_iod is not None:
        print(f"  mean_iod_c: {mean_iod:.4f} degC")
    if p95_iod is not None:
        print(f"  p95_iod_c: {p95_iod:.4f} degC")
    pfa = summary.get("pct_floor_area_simulated")
    if pfa is not None:
        print(f"  pct_floor_area_simulated: {pfa*100:.1f}%")
    print(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

# ── Archetype mix ───────────────────────────────────────────────────────────────
print("\n=== ARCHETYPE MIX (enriched GDF) ===")
arch_counts = idf_mf["archetype_id"].value_counts()
for archetype, cnt in arch_counts.items():
    pct = cnt / len(idf_mf) * 100
    print(f"  {archetype:<30} {cnt:4d}  ({pct:.1f}%)")

if "archetype_id" in results_gdf.columns:
    print("\n=== EUI BY ARCHETYPE (success rows) ===")
    arch_stats = parsed.groupby("archetype_id")["total_eui_kwh_m2"].agg(["count", "mean", "median"])
    print(arch_stats.to_string())

# ── Area-weighted EUI from v11_results.csv ─────────────────────────────────────
total_area = v11_res["total_floor_area_m2"].sum()
aw_heat = (v11_res["heating_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_cool = (v11_res["cooling_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_light = (v11_res["lighting_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_equip = (v11_res["equipment_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_total = (v11_res["total_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area

print(f"\n=== AREA-WEIGHTED EUI (from v11_results.csv, 738 buildings) ===")
print(f"  heating:   {aw_heat:.2f} kWh/m2/yr")
print(f"  cooling:   {aw_cool:.2f} kWh/m2/yr")
print(f"  lighting:  {aw_light:.2f} kWh/m2/yr")
print(f"  equipment: {aw_equip:.2f} kWh/m2/yr")
print(f"  total:     {aw_total:.2f} kWh/m2/yr")
print(f"  total floor area: {total_area/1e6:.3f} million m2")

# ── GWP ────────────────────────────────────────────────────────────────────────
gwp_col = next((c for c in results_gdf.columns if "gwp" in c.lower()), None)
if gwp_col and gwp_col in parsed.columns:
    gwp_vals = parsed[gwp_col].dropna()
    print(f"\n=== GWP ({gwp_col}) ===")
    print(f"  n={len(gwp_vals)}, mean={gwp_vals.mean():.2f}, sum={gwp_vals.sum():.0f} kgCO2e")

# ── Write gates report ─────────────────────────────────────────────────────────
eui_summary = summary.get("neighbourhood_eui_weighted_kwh_m2", {}) if summary else {}
gwp_total = summary.get("neighbourhood_gwp_total_kgco2") if summary else None
mean_iod_v = summary.get("mean_iod_c") if summary else None
p95_iod_v = summary.get("p95_iod_c") if summary else None
pfa_v = summary.get("pct_floor_area_simulated") if summary else None

r2_str = f"{cbecs_gates['cbecs_r2']:.4f}" if cbecs_gates["cbecs_r2"] is not None else "N/A"

gates_lines = [
    "=" * 72,
    "V11 NYC CITY-CENTRE GATES REPORT — 2026-06-12",
    f"  sim_manifest:   {SIM_MANIFEST_PATH}",
    f"  idf_manifest:   {IDF_MANIFEST_PATH}",
    "=" * 72,
    "",
    "=== LIVE_SMOKE FUNNEL ===",
    f"  fetched (Step 1):   {n_fetched}",
    f"  enriched (Step 2):  {n_enriched}",
    f"  generated (Step 3): {n_generated}  ({gen_success_pct:.1f}% of fetched) [target >=95%: {'PASS' if gen_success_pct >= 95.0 else 'FAIL'}]",
    f"  simulated success:  {n_simulated}  ({sim_success_pct:.1f}% of generated) [target >=99%: {'PASS' if sim_success_pct >= 99.0 else 'FAIL'}]",
    f"  Unknown archetype:  {unknown_count}  ({unknown_pct:.1f}% of enriched) [target <20%: {'PASS' if unknown_pct < 20.0 else 'FAIL'}]",
    "",
    "=== F12 GATE TABLE ===",
    f"{'Gate':<42} {'Value':>16}  {'Result':>6}",
    "-" * 68,
    f"{'pct_parse_success >= 99%':<42} {pct_parse_success*100:>15.2f}%  {'PASS' if gate_pct_parse else 'FAIL':>6}",
    f"{'  n_parsed / n_sim_success':<42} {str(n_parsed)+'/'+str(n_sim_success):>16}  {'':>6}",
    f"{'EUI plausibility >= 99% in [25,1000]':<42} {pct_plausible*100:>15.2f}%  {'PASS' if gate_eui else 'FAIL':>6}",
    f"{'  n_in_range / n_valid_eui':<42} {str(in_range)+'/'+str(len(valid_eui)):>16}  {'':>6}",
]
if len(outliers) > 0:
    gates_lines.append(
        f"{'  EUI outliers: min / max':<42} {outliers.min():>7.1f} / {outliers.max():>6.1f}  {'':>6}"
    )
gates_lines += [
    f"{'zone_count_integrity = 0 mismatches':<42} {n_zone_mismatch:>16}  {'PASS' if gate_zone else 'FAIL':>6}",
    "",
    f"  Overall (3 live gates): {'ALL PASS' if gates_all else 'SOME FAILED'}",
    "",
    "=== CBECS 2018 NORTHEAST VALIDATION GATES (report-only, V-R5-5) ===",
    f"  n_sim_buildings (after exclusions): {cbecs_gates['n_sim_buildings']}",
    f"  n_excluded_all_gates: {cbecs_gates['n_excluded_all_gates']}",
    "  REGION NOTE: CBECS NE includes NY state; NYC is within the reference region.",
    "  COMPOSITION CAVEAT: NYC fleet is 83% office+tall; CBECS NE diverse stock",
    "  (hospitals, food service) inflates reference mean — same bias as Boston R3.",
    "",
    f"{'Metric':<12} {'Threshold':>12} {'R3 Boston':>14} {'Boston P/F':>10} {'NYC Result':>12} {'NYC P/F':>8}",
    "-" * 74,
    f"{'CV(RMSE)%':<12} {'< 30.0%':>12} {'69.823':>14} {'FAIL':>10} {cbecs_gates['cbecs_cv_rmse']:>12.3f} {'PASS' if cbecs_gates['cbecs_cv_rmse_pass'] else 'FAIL':>8}",
    f"{'NMBE%':<12} {'< |10|%':>12} {'-16.046':>14} {'FAIL':>10} {cbecs_gates['cbecs_nmbe']:>12.3f} {'PASS' if cbecs_gates['cbecs_nmbe_pass'] else 'FAIL':>8}",
    f"{'R2':<12} {'> 0.6':>12} {'0.7312':>14} {'PASS':>10} {r2_str:>12} {'PASS' if cbecs_gates['cbecs_r2_pass'] else 'FAIL':>8}",
    f"{'KS_D':<12} {'< 0.10':>12} {'0.2730':>14} {'FAIL':>10} {cbecs_gates['cbecs_ks_d']:>12.4f} {'PASS' if cbecs_gates['cbecs_ks_d_pass'] else 'FAIL':>8}",
    "",
    "  Note: CBECS gates are report-only per ruling V-R5-5/M-R2-4.",
]

if eui_summary:
    gates_lines += [
        "",
        "=== HEADLINE NUMBERS (05_neighbourhood_summary.json) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_summary.get(k)
        if v is not None:
            gates_lines.append(f"  {k}: {v:.4f} kWh/m2/yr")
    if gwp_total:
        gates_lines.append(f"  neighbourhood_gwp_total_kgco2: {gwp_total:,.0f} kgCO2e")
    if mean_iod_v is not None:
        gates_lines.append(f"  mean_iod_c: {mean_iod_v:.4f} degC")
    if p95_iod_v is not None:
        gates_lines.append(f"  p95_iod_c: {p95_iod_v:.4f} degC")
    if pfa_v is not None:
        gates_lines.append(f"  pct_floor_area_simulated: {pfa_v*100:.1f}%")

gates_lines += [
    "",
    "=== AREA-WEIGHTED EUI (v11_results.csv direct, 738/738 success) ===",
    f"  heating:   {aw_heat:.2f} kWh/m2/yr",
    f"  cooling:   {aw_cool:.2f} kWh/m2/yr",
    f"  lighting:  {aw_light:.2f} kWh/m2/yr",
    f"  equipment: {aw_equip:.2f} kWh/m2/yr",
    f"  total:     {aw_total:.2f} kWh/m2/yr",
    f"  total_floor_area_m2: {total_area:.0f}",
    "",
    "=== REPAIR SUMMARY (zero-fail interventions) ===",
    "  repair/  (3 buildings: way/265302023, way/266170758, way/266170788)",
    "    Action: Step-3 IDF regeneration with repair manifest",
    "    IDF content: hash-identical to originals — regeneration was the fix",
    "    (prior executor re-ran Step 3 generation; files byte-identical to step3/idfs/)",
    "  repair2/ (1 building: way/265302069)",
    "    Action: Step-3 IDF regeneration into repair2 manifest",
    "    IDF content: hash-identical to original",
    "  sim_out/way_265302069/",
    "    DEVIATION: EnergyPlus 23.1.0 run LOCALLY on 2026-06-12 00:59",
    "    (per eplusout.err header: 'YMD=2026.06.12 00:59')",
    "    This violates ruling V-R5-6 (all E+ runs via sbatch).",
    "    Result: 0 Severe, 174 Warnings, Completed Successfully, 3m36s elapsed",
    "    Prior backup identical to current output (same SQL size 136732672 bytes)",
    "    No anomalies in result; deviation recorded but not remediated (V-R5-5)",
    "",
    "=== CLUSTER JOB IDs ===",
    "  955857  (initial fleet submit, pre-Step-3 pipeline run)",
    "  956522  (738-sim array, main fleet)",
    "  957268_1 (repair array)",
    "  957302  (extract array)",
    "",
    "=" * 72,
    "END REPORT",
    "=" * 72,
]

gates_report = "\n".join(gates_lines)
gates_report_path = RESULTS_DIR / "v11_gates_report.txt"
gates_report_path.write_text(gates_report, encoding="utf-8")
print(f"\n[V11] Gates report written: {gates_report_path}")

# ── Copy deliverables to docs/ ─────────────────────────────────────────────────
print("\n[V11] Copying final deliverables to docs/ ...")
final_files = []
for f in sorted(RESULTS_DIR.rglob("*")):
    if f.is_file():
        dest = FINAL_DIR / f.relative_to(RESULTS_DIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        final_files.append(dest)
print(f"[V11] {len(final_files)} files copied to {FINAL_DIR}")

print("\n=== ARTIFACT TREE (final deliverables) ===")
for f in sorted(FINAL_DIR.rglob("*")):
    if f.is_file():
        size = f.stat().st_size
        rel = f.relative_to(REPO)
        print(f"  {rel}  ({size/1024:.1f} KB)")

print(f"\n[V11] step5 wall clock: {wall_step5:.1f}s")
print("[V11] DONE")
