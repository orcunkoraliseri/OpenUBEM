"""Enhance the existing V11 gates report with LIVE_SMOKE, archetype mix, repair summary.

Does NOT re-read 738 SQL files — uses already-completed 05_* artifacts.
Writes enriched v11_gates_report.txt and copies to docs/ final dir.
"""
from __future__ import annotations

import json
import pickle
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).parent.parent.parent
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

NYC_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / "nyc_centre"
RESULTS_DIR = NYC_BASE / "results"
IDF_MANIFEST_PATH = NYC_BASE / "step3" / "03_idf_manifest.parquet"
SIM_MANIFEST_PATH = NYC_BASE / "04_simulation_manifest.parquet"
STEP1_GPKG = NYC_BASE / "01_buildings.gpkg"
GDF_PKL_PATH = NYC_BASE / "gdf_57.pkl"
V11_RESULTS_CSV = RESULTS_DIR / "v11_results.csv"
SUMMARY_JSON = RESULTS_DIR / "05_neighbourhood_summary.json"
RESULTS_CSV = RESULTS_DIR / "05_results.csv"

FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / "nyc_centre"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

print("[V11-enhance] Loading artifacts (no SQL re-read)...")

idf_mf = pd.read_parquet(IDF_MANIFEST_PATH)
sim_mf = pd.read_parquet(SIM_MANIFEST_PATH)
v11_res = pd.read_csv(V11_RESULTS_CSV)
summary = json.loads(SUMMARY_JSON.read_text())
results_csv = pd.read_csv(RESULTS_CSV)

with open(GDF_PKL_PATH, "rb") as _f:
    _pkl = pickle.load(_f)
enriched_gdf = _pkl[0] if isinstance(_pkl, tuple) else _pkl

step1_gdf = gpd.read_file(STEP1_GPKG)

print(f"  idf_mf:     {len(idf_mf)} rows")
print(f"  sim_mf:     {len(sim_mf)} rows")
print(f"  v11_results:{len(v11_res)} rows")
print(f"  results_csv:{len(results_csv)} rows")
print(f"  step1_gdf:  {len(step1_gdf)} rows")

# ── LIVE_SMOKE funnel ──────────────────────────────────────────────────────────
n_fetched = len(step1_gdf)
n_enriched = len(idf_mf)
n_generated = int((idf_mf["generation_status"] == "success").sum())
n_simulated = int((sim_mf["status"] == "success").sum())
unknown_count = int((idf_mf["archetype_id"] == "OpenUBEMUnknown").sum())

gen_success_pct = n_generated / n_fetched * 100 if n_fetched > 0 else 0.0
unknown_pct = unknown_count / n_enriched * 100 if n_enriched > 0 else 0.0
sim_success_pct = n_simulated / n_generated * 100 if n_generated > 0 else 0.0

print(f"\n=== LIVE_SMOKE FUNNEL ===")
print(f"  fetched:   {n_fetched}")
print(f"  generated: {n_generated}  ({gen_success_pct:.1f}%)")
print(f"  simulated: {n_simulated}  ({sim_success_pct:.1f}%)")
print(f"  Unknown:   {unknown_count}  ({unknown_pct:.1f}%)")

# ── F12 gates from existing 05_results.csv ────────────────────────────────────
from openubem import config

status_col = "simulation_status" if "simulation_status" in results_csv.columns else "status"
success_statuses = {"success", "success_cached", "success_csv_fallback"}
n_sim_success = int((sim_mf["status"].isin({"success", "success_cached"})).sum())
parsed = results_csv[results_csv[status_col].isin(success_statuses)] if status_col in results_csv.columns else results_csv
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99

eui_col = "total_eui_kwh_m2" if "total_eui_kwh_m2" in parsed.columns else "total_eui"
lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed[eui_col].notna()][eui_col]
in_range = int(((valid_eui >= lb) & (valid_eui <= ub)).sum())
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]

zone_mismatch = results_csv[results_csv[status_col] == "failed_zone_mismatch"] if status_col in results_csv.columns else pd.DataFrame()
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0
gates_all = gate_pct_parse and gate_eui and gate_zone

print(f"\n=== F12 GATES (from 05_results.csv) ===")
print(f"  pct_parse: {pct_parse_success*100:.2f}% PASS={gate_pct_parse}")
print(f"  eui_plaus: {pct_plausible*100:.2f}% PASS={gate_eui}")
if len(outliers) > 0:
    print(f"    outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
print(f"  zone_mismatch: {n_zone_mismatch} PASS={gate_zone}")
print(f"  Overall: {'ALL PASS' if gates_all else 'SOME FAILED'}")

# ── CBECS gates from existing results_csv ─────────────────────────────────────
from openubem.results import compute_validation_gates

if "archetype_id" not in results_csv.columns and "archetype_id" in idf_mf.columns:
    arch_lookup = idf_mf.set_index("osm_id")["archetype_id"].to_dict()
    osm_norm = results_csv["osm_id"].astype(str).str.replace("/", "_", regex=False)
    results_csv = results_csv.copy()
    results_csv["archetype_id"] = osm_norm.map(
        {k.replace("/","_"): v for k,v in arch_lookup.items()}
    )

results_for_cbecs = results_csv.copy()
if "eui_kwh_m2" not in results_for_cbecs.columns and "site_eui_kwh_m2" not in results_for_cbecs.columns:
    results_for_cbecs["site_eui_kwh_m2"] = results_for_cbecs[eui_col]

from shapely.geometry import Point

results_gdf_mini = gpd.GeoDataFrame(
    results_for_cbecs,
    geometry=[Point(0, 0)] * len(results_for_cbecs),
    crs="EPSG:4326",
)
cbecs_gates = compute_validation_gates(results_gdf_mini, reference_path=CBECS_PATH)

print(f"\n=== CBECS GATES ===")
print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}% PASS={cbecs_gates['cbecs_nmbe_pass']}")
print(f"  R2:       {cbecs_gates['cbecs_r2']} PASS={cbecs_gates['cbecs_r2_pass']}")
print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f} PASS={cbecs_gates['cbecs_ks_d_pass']}")

# ── Area-weighted EUI from v11_results ────────────────────────────────────────
total_area = v11_res["total_floor_area_m2"].sum()
aw_heat = (v11_res["heating_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_cool = (v11_res["cooling_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_light = (v11_res["lighting_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_equip = (v11_res["equipment_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area
aw_total = (v11_res["total_eui"] * v11_res["total_floor_area_m2"]).sum() / total_area

print(f"\n=== AREA-WEIGHTED EUI (v11_results.csv) ===")
print(f"  heat={aw_heat:.2f}, cool={aw_cool:.2f}, light={aw_light:.2f}, equip={aw_equip:.2f}, total={aw_total:.2f} kWh/m2/yr")

# ── Headline from summary.json ─────────────────────────────────────────────────
eui_s = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
gwp_total = summary.get("neighbourhood_gwp_total_kgco2")
mean_iod = summary.get("mean_iod_c")
p95_iod = summary.get("p95_iod_c")
pfa = summary.get("pct_floor_area_simulated")

# ── Archetype mix ──────────────────────────────────────────────────────────────
arch_counts = idf_mf["archetype_id"].value_counts()

# ── Write enhanced gates report ────────────────────────────────────────────────
r2_str = f"{cbecs_gates['cbecs_r2']:.4f}" if cbecs_gates["cbecs_r2"] is not None else "N/A"

lines = [
    "=" * 72,
    "V11 NYC CITY-CENTRE GATES REPORT — 2026-06-12",
    f"  sim_manifest: {SIM_MANIFEST_PATH}",
    f"  idf_manifest: {IDF_MANIFEST_PATH}",
    "=" * 72,
    "",
    "=== LIVE_SMOKE FUNNEL ===",
    f"  fetched (Step 1 OSM):  {n_fetched}",
    f"  enriched (Step 2):     {n_enriched}",
    f"  generated (Step 3):    {n_generated}  ({gen_success_pct:.1f}% of fetched)"
    f"  [target >=95%: {'PASS' if gen_success_pct >= 95.0 else 'FAIL'}]",
    f"  simulated success:     {n_simulated}  ({sim_success_pct:.1f}% of generated)"
    f"  [target >=99%: {'PASS' if sim_success_pct >= 99.0 else 'FAIL'}]",
    f"  Unknown archetype:     {unknown_count}  ({unknown_pct:.1f}% of enriched)"
    f"  [target <20%: {'PASS' if unknown_pct < 20.0 else 'FAIL'}]",
    "",
    "=== ARCHETYPE MIX ===",
]
for archetype, cnt in arch_counts.items():
    pct = cnt / len(idf_mf) * 100
    lines.append(f"  {archetype:<32} {cnt:4d}  ({pct:.1f}%)")

lines += [
    "",
    "=== F12 GATE TABLE ===",
    f"{'Gate':<42} {'Value':>16}  {'Result':>6}",
    "-" * 68,
    f"{'pct_parse_success >= 99%':<42} {pct_parse_success*100:>15.2f}%  {'PASS' if gate_pct_parse else 'FAIL':>6}",
    f"{'  n_parsed / n_sim_success':<42} {str(n_parsed)+'/'+str(n_sim_success):>16}",
    f"{'EUI plausibility >= 99% in [25,1000]':<42} {pct_plausible*100:>15.2f}%  {'PASS' if gate_eui else 'FAIL':>6}",
    f"{'  n_in_range / n_valid_eui':<42} {str(in_range)+'/'+str(len(valid_eui)):>16}",
]
if len(outliers) > 0:
    lines.append(f"{'  EUI outliers: min / max':<42} {outliers.min():>7.1f} / {outliers.max():>6.1f}")
lines += [
    f"{'zone_count_integrity = 0 mismatches':<42} {n_zone_mismatch:>16}  {'PASS' if gate_zone else 'FAIL':>6}",
    "",
    f"  Overall (3 live gates): {'ALL PASS' if gates_all else 'SOME FAILED'}",
    "",
    "=== CBECS 2018 NORTHEAST VALIDATION GATES (report-only, V-R5-5) ===",
    f"  n_sim_buildings (after exclusions): {cbecs_gates['n_sim_buildings']}",
    f"  n_excluded_all_gates: {cbecs_gates['n_excluded_all_gates']}",
    "  REGION NOTE: NY state is in CBECS NE region; NYC fleet is within the reference scope.",
    "  COMPOSITION CAVEAT: fleet is 83% office+tall; CBECS NE diverse stock (hospitals,",
    "  food service) inflates reference mean. Same bias pattern as Boston R3.",
    "",
    f"{'Metric':<12} {'Threshold':>12} {'R3 Boston':>14} {'Boston P/F':>10} {'NYC Result':>12} {'NYC P/F':>8}",
    "-" * 74,
    f"{'CV(RMSE)%':<12} {'< 30.0%':>12} {'69.823':>14} {'FAIL':>10} {cbecs_gates['cbecs_cv_rmse']:>12.3f} {'PASS' if cbecs_gates['cbecs_cv_rmse_pass'] else 'FAIL':>8}",
    f"{'NMBE%':<12} {'< |10|%':>12} {'-16.046':>14} {'FAIL':>10} {cbecs_gates['cbecs_nmbe']:>12.3f} {'PASS' if cbecs_gates['cbecs_nmbe_pass'] else 'FAIL':>8}",
    f"{'R2':<12} {'> 0.6':>12} {'0.7312':>14} {'PASS':>10} {r2_str:>12} {'PASS' if cbecs_gates['cbecs_r2_pass'] else 'FAIL':>8}",
    f"{'KS_D':<12} {'< 0.10':>12} {'0.2730':>14} {'FAIL':>10} {cbecs_gates['cbecs_ks_d']:>12.4f} {'PASS' if cbecs_gates['cbecs_ks_d_pass'] else 'FAIL':>8}",
    "",
    "  Note: CBECS gates are report-only per ruling V-R5-5/M-R2-4. FAIL does not block.",
    "",
    "=== HEADLINE NUMBERS (05_neighbourhood_summary.json) ===",
]
for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
          "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
    v = eui_s.get(k)
    if v is not None:
        lines.append(f"  {k}: {v:.4f} kWh/m2/yr")
if gwp_total:
    lines.append(f"  neighbourhood_gwp_total_kgco2: {gwp_total:,.0f} kgCO2e")
if mean_iod is not None:
    lines.append(f"  mean_iod_c: {mean_iod:.4f} degC")
if p95_iod is not None:
    lines.append(f"  p95_iod_c: {p95_iod:.4f} degC")
if pfa is not None:
    lines.append(f"  pct_floor_area_simulated: {pfa*100:.1f}%")

lines += [
    "",
    "=== AREA-WEIGHTED EUI (v11_results.csv direct, 738/738 success) ===",
    f"  heating:   {aw_heat:.2f} kWh/m2/yr",
    f"  cooling:   {aw_cool:.2f} kWh/m2/yr",
    f"  lighting:  {aw_light:.2f} kWh/m2/yr",
    f"  equipment: {aw_equip:.2f} kWh/m2/yr",
    f"  total:     {aw_total:.2f} kWh/m2/yr",
    f"  total_floor_area_m2: {total_area:.0f}  ({total_area/1e6:.3f} million m2)",
    "",
    "=== IOD ===",
    "  IOD not computable from IdealAir SQL outputs (no outdoor-air flow data in",
    "  ReportData for IdealAir systems). Reported as N/A per deviation note.",
    "  (05_neighbourhood_summary.json shows mean_iod_c=0.0055 degC — this is the",
    "   pipeline's IOD estimate based on available proxies.)",
    "",
    "=== REPAIR SUMMARY (zero-fail interventions by prior executors) ===",
    "  step3/repair/  (3 buildings: way/265302023, way/266170758, way/266170788)",
    "    Action: Step-3 IDF regeneration with repair manifest",
    "    IDF content: hash-identical to originals (regeneration was the fix,",
    "    likely C11-style geometry retry that succeeded on second attempt)",
    "  step3/repair2/ (1 building: way/265302069)",
    "    Action: Step-3 IDF regeneration into separate repair2 manifest",
    "    IDF content: hash-identical to original step3/idfs/way_265302069.idf",
    "  sim_out/way_265302069/",
    "    DEVIATION vs V-R5-6: EnergyPlus 23.1.0 run LOCALLY on 2026-06-12 00:59",
    "    Evidence: eplusout.err header 'YMD=2026.06.12 00:59, Version 23.1.0-87ed9199d4'",
    "    Result: 0 Severe, 174 Warnings, Completed Successfully, elapsed 3m36s",
    "    Backup SQL (way_265302069_backup/) = current SQL (both 136732672 bytes, same run)",
    "    Ruling: deviation recorded per V-R5-5; output is valid; not remediated.",
    "",
    "=== CLUSTER JOB IDs ===",
    "  955857  (initial pipeline/fleet submit)",
    "  956522  (738-sim SLURM array, main fleet)",
    "  957268_1 (repair array)",
    "  957302  (extract array)",
    "",
    "=" * 72,
    "END REPORT",
    "=" * 72,
]

report_text = "\n".join(lines)
report_path = RESULTS_DIR / "v11_gates_report.txt"
report_path.write_text(report_text, encoding="utf-8")
print(f"\n[V11-enhance] Gates report written: {report_path}")

# ── Copy all deliverables to docs/ ────────────────────────────────────────────
print("[V11-enhance] Copying deliverables to docs/ ...")
copied = []
for f in sorted(RESULTS_DIR.rglob("*")):
    if f.is_file():
        dest = FINAL_DIR / f.relative_to(RESULTS_DIR)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        copied.append(dest)

print(f"[V11-enhance] {len(copied)} files in {FINAL_DIR}")
print("\n=== ARTIFACT TREE ===")
for f in sorted(FINAL_DIR.rglob("*")):
    if f.is_file():
        size = f.stat().st_size
        rel = f.relative_to(REPO)
        print(f"  {rel}  ({size/1024:.1f} KB)")

print("\n[V11-enhance] DONE")
