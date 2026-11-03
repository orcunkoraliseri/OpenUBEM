"""C09 gates report — recompute F12 + CBECS gates from persisted artifacts.

Inputs (no sql re-reading):
  - TEMP/ubem_boston_r3_results/05_results.csv
  - TEMP/ubem_boston_r3/04_simulation_manifest.parquet
  - inputs/reports/cbecs_2018_new_england_eui.csv

NaturalGas/ABUPS/meter gates require per-building sql — those ran during the
original C09 run.  This script marks them N/A and records the finding.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from openubem import config
from openubem.results import compute_validation_gates

CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"
R3_BASE = Path(tempfile.gettempdir()) / "ubem_boston_r3"
RESULTS_DIR = Path(tempfile.gettempdir()) / "ubem_boston_r3_results"
RESULTS_CSV = RESULTS_DIR / "05_results.csv"
SIM_MANIFEST = R3_BASE / "04_simulation_manifest.parquet"
SUMMARY_JSON = RESULTS_DIR / "05_neighbourhood_summary.json"
REPORT_OUT = RESULTS_DIR / "c09_gates_report.txt"

for p in [RESULTS_CSV, SIM_MANIFEST, SUMMARY_JSON, CBECS_PATH]:
    if not p.exists():
        print(f"ERROR: required artifact missing: {p}", file=sys.stderr)
        sys.exit(1)

results_df = pd.read_csv(RESULTS_CSV)
sim_mf = pd.read_parquet(SIM_MANIFEST)
summary = json.loads(SUMMARY_JSON.read_text())

print(f"Loaded 05_results.csv: {len(results_df)} rows")
print(f"Loaded 04_simulation_manifest.parquet: {len(sim_mf)} rows")

# Build minimal GeoDataFrame for compute_validation_gates (needs archetype_id + eui col)
gdf_rows = []
for _, row in results_df.iterrows():
    gdf_rows.append({
        "osm_id": str(row["osm_id"]),
        "archetype_id": row.get("archetype_id", "OpenUBEMUnknown"),
        "site_eui_kwh_m2": row.get("total_eui_kwh_m2"),
        "total_eui_kwh_m2": row.get("total_eui_kwh_m2"),
        "simulation_status": row.get("simulation_status", "success"),
        "geometry": Point(
            row.get("centroid_lon", 0.0) or 0.0,
            row.get("centroid_lat", 0.0) or 0.0,
        ),
    })
results_gdf = gpd.GeoDataFrame(gdf_rows, crs="EPSG:4326")

success_statuses = {"success", "success_cached", "success_csv_fallback"}
sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
n_sim_success = len(sim_success)
parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99

lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]

zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0

# Gas/ABUPS/meter: not recomputable from CSV — recorded N/A
gate_gas = None
gas_note = "not recomputable from 05_results.csv (no NaturalGas column); ran OK during original C09 run"

cbecs_gates = compute_validation_gates(results_gdf, reference_path=CBECS_PATH)

lines: list[str] = []
lines.append("=" * 72)
lines.append("C09 GATES REPORT — recomputed from persisted artifacts 2026-06-11")
lines.append(f"  05_results.csv:              {RESULTS_CSV}")
lines.append(f"  04_simulation_manifest.parquet: {SIM_MANIFEST}")
lines.append("=" * 72)

lines.append("")
lines.append("=== F12 GATE TABLE ===")
lines.append(f"{'Gate':<42} {'Value':>16}  {'Result':>6}")
lines.append("-" * 68)
lines.append(
    f"{'pct_parse_success >= 99%':<42} {pct_parse_success*100:>15.2f}%  {'PASS' if gate_pct_parse else 'FAIL':>6}"
)
lines.append(
    f"{'  n_parsed / n_sim_success':<42} {f'{n_parsed}/{n_sim_success}':>16}  {'':>6}"
)
lines.append(
    f"{'EUI plausibility >= 99% in [25,1000]':<42} {pct_plausible*100:>15.2f}%  {'PASS' if gate_eui else 'FAIL':>6}"
)
lines.append(
    f"{'  n_in_range / n_valid_eui':<42} {f'{in_range}/{len(valid_eui)}':>16}  {'':>6}"
)
if len(outliers) > 0:
    lines.append(
        f"{'  EUI outliers: min / max':<42} {outliers.min():>7.1f} / {outliers.max():>6.1f}  {'':>6}"
    )
lines.append(
    f"{'zone_count_integrity = 0 mismatches':<42} {n_zone_mismatch:>16}  {'PASS' if gate_zone else 'FAIL':>6}"
)
lines.append(
    f"{'NaturalGas:Facility = 0':<42} {'N/A (see note)':>16}  {'N/A':>6}"
)
lines.append("")
lines.append(f"  Note: NaturalGas/ABUPS/meter gates — {gas_note}")
lines.append("")
overall_live = gate_pct_parse and gate_eui and gate_zone
lines.append(f"  Overall (3 live CSV-recomputable gates): {'ALL PASS' if overall_live else 'SOME FAILED'}")

lines.append("")
lines.append("=== CBECS 2018 NORTHEAST VALIDATION GATES ===")
cv = cbecs_gates["cbecs_cv_rmse"]
nmbe = cbecs_gates["cbecs_nmbe"]
r2 = cbecs_gates["cbecs_r2"]
ks = cbecs_gates["cbecs_ks_d"]
cv_pass = cbecs_gates["cbecs_cv_rmse_pass"]
nmbe_pass = cbecs_gates["cbecs_nmbe_pass"]
r2_pass = cbecs_gates["cbecs_r2_pass"]
ks_pass = cbecs_gates["cbecs_ks_d_pass"]
lines.append(f"  n_sim_buildings (after exclusions): {cbecs_gates['n_sim_buildings']}")
lines.append(f"  n_excluded_all_gates: {cbecs_gates['n_excluded_all_gates']}")
lines.append("")
lines.append(f"{'Metric':<12} {'Threshold':>12} {'R1 Baseline':>14} {'R1 P/F':>8} {'R3 Result':>12} {'R3 P/F':>8} {'Delta':>10}")
lines.append("-" * 82)
lines.append(
    f"{'CV(RMSE)%':<12} {'< 30.0%':>12} {'53.784':>14} {'FAIL':>8} {cv:>12.3f} {'PASS' if cv_pass else 'FAIL':>8} {cv - 53.784:>+10.3f}"
)
lines.append(
    f"{'NMBE%':<12} {'< |10|%':>12} {'-10.813':>14} {'FAIL':>8} {nmbe:>12.3f} {'PASS' if nmbe_pass else 'FAIL':>8} {nmbe - (-10.813):>+10.3f}"
)
r2_str = f"{r2:.4f}" if r2 is not None else "N/A"
r2_delta = f"{r2 - 0.7312:+.4f}" if r2 is not None else "N/A"
lines.append(
    f"{'R²':<12} {'> 0.6':>12} {'0.7312':>14} {'PASS':>8} {r2_str:>12} {'PASS' if r2_pass else 'FAIL':>8} {r2_delta:>10}"
)
lines.append(
    f"{'KS_D':<12} {'< 0.10':>12} {'0.1902':>14} {'FAIL':>8} {ks:>12.4f} {'PASS' if ks_pass else 'FAIL':>8} {ks - 0.1902:>+10.4f}"
)
lines.append("")
lines.append("  Note: CBECS gates are report-only per ruling M-R2-4; FAIL does not block.")

lines.append("")
lines.append("=== HEADLINE NUMBERS (05_neighbourhood_summary.json) ===")
eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
          "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
    v = eui_map.get(k)
    if v is not None:
        lines.append(f"  {k}: {v:.4f} kWh/m²/yr")
gwp = summary.get("neighbourhood_gwp_total_kgco2")
if gwp:
    lines.append(f"  neighbourhood_gwp_total_kgco2: {gwp:,.0f} kgCO2e")
mean_iod = summary.get("mean_iod_c")
p95_iod = summary.get("p95_iod_c")
if mean_iod is not None:
    lines.append(f"  mean_iod_c: {mean_iod:.4f} °C")
if p95_iod is not None:
    lines.append(f"  p95_iod_c: {p95_iod:.4f} °C")
pfa = summary.get("pct_floor_area_simulated")
if pfa is not None:
    lines.append(f"  pct_floor_area_simulated: {pfa*100:.1f}%")
lines.append(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

lines.append("")
lines.append("=" * 72)
lines.append("END REPORT")
lines.append("=" * 72)

report_text = "\n".join(lines)
print(report_text)
REPORT_OUT.write_text(report_text, encoding="utf-8")
print(f"\n[gates_report] Written to {REPORT_OUT}")
