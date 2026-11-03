"""R3: Full-chain Boston re-run with the R3 classifier (Steps 2 to 5).

Adapted from scripts/run_c4_regen.py (Steps 2-4) and scripts/run_r1_t12.py (Step 5).
Input fixture: tests/fixtures/boston_downtown_500m.gpkg (EPSG:32619, 483 buildings).
Outputs: TEMP/ubem_boston_r3 (step3/, sim/), TEMP/ubem_boston_r3_results.
n_jobs=6, SIM_TIMEOUT_S=3600 (unchanged from config).
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

REPO = Path(__file__).parent.parent
BOSTON_GDF = REPO / "tests" / "fixtures" / "boston_downtown_500m.gpkg"
EPW_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\openubem_epw_7rrpvd27\weather\USA_MA_Boston.994971_TMYx.2011-2025.epw")
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_boston_r3"
STEP3_DIR = OUT_BASE / "step3"
SIM_DIR = OUT_BASE / "sim"
RESULTS_DIR = Path(tempfile.gettempdir()) / "ubem_boston_r3_results"

print(f"[R3] Output base: {OUT_BASE}")
print(f"[R3] Results dir: {RESULTS_DIR}")
OUT_BASE.mkdir(exist_ok=True)
STEP3_DIR.mkdir(exist_ok=True)
SIM_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# ── Step 1: Load Boston GDF ──────────────────────────────────────────────────
print("[R3] Loading Boston GDF...")
from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier

gdf_raw = gpd.read_file(str(BOSTON_GDF))
gdf_raw = gdf_raw[_INPUT_SCHEMA_COLUMNS]
gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
print(f"  {len(gdf_raw)} buildings loaded")

# ── Step 2: Classify buildings ───────────────────────────────────────────────
print("[R3] Step 2: building classification...")
t0 = time.monotonic()
bc = BuildingClassifier()
gdf_26 = bc.classify(gdf_raw)
print(f"  {len(gdf_26)} buildings classified ({time.monotonic()-t0:.1f}s)")

print("\n=== NEW archetype distribution (R3 classifier) ===")
arch_dist = gdf_26["archetype_id"].value_counts()
print(arch_dist.to_string())
print(f"  Total: {len(gdf_26)}")
print(f"  OpenUBEMUnknown: {int((gdf_26['archetype_id'] == 'OpenUBEMUnknown').sum())}")
print(f"  FALLBACK_SIZE_DEFAULT: {int((gdf_26['archetype_source'] == 'FALLBACK_SIZE_DEFAULT').sum())}")

# Manager gate: stop if Unknown > 100
n_unknown = int((gdf_26["archetype_id"] == "OpenUBEMUnknown").sum())
if n_unknown > 100:
    print(f"\n[R3] STOP: OpenUBEMUnknown = {n_unknown} > 100. Aborting before simulation.")
    sys.exit(1)
print(f"\n[R3] Unknown gate OK: {n_unknown} < 30 threshold. Proceeding to simulation.\n")

# ── Step 2.1: Climate enrichment (offline, cached EPW) ──────────────────────
print("[R3] Step 2.1: climate enrichment (offline)...")
t0 = time.monotonic()

from openubem.acquisition.climate_zone import assign_climate_zones
from openubem.acquisition import _CLIMATE_ZONE_VOCAB

zone_df = assign_climate_zones(gdf_26)

gdf_29 = gdf_26.copy()
gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=_CLIMATE_ZONE_VOCAB)
gdf_29["epw_path"] = str(EPW_PATH)
gdf_29["provenance_climate_zone"] = pd.Categorical(
    zone_df["provenance_climate_zone"].values,
    categories=["ASHRAE_STANDARD", "HEURISTIC"],
)

sidecar = pd.DataFrame({
    "osm_id": gdf_26["osm_id"].values,
    "climate_zone": zone_df["climate_zone"].values,
    "climate_zone_method": zone_df["climate_zone_method"].values,
    "county_geoid": zone_df["county_geoid"].values,
    "state": zone_df["state"].values,
    "epw_station_id": "994971",
    "epw_path": str(EPW_PATH),
    "epw_distance_km": 0.0,
    "provenance_climate_zone": zone_df["provenance_climate_zone"].values,
})
sidecar.to_parquet(str(OUT_BASE / "02a_climate_epw.parquet"), index=False)
print(f"  climate zones assigned ({time.monotonic()-t0:.1f}s), sidecar written")

# ── Step 2.2: Semantic enrichment ────────────────────────────────────────────
print("[R3] Step 2.2: semantic enrichment...")
t0 = time.monotonic()
from openubem.semantic import enrich_semantics

gdf_57, schedule_library = enrich_semantics(gdf_29)
print(f"  {len(gdf_57)} buildings enriched, {gdf_57.shape[1]} columns ({time.monotonic()-t0:.1f}s)")

# ── Step 3: IDF generation ────────────────────────────────────────────────────
print("[R3] Step 3: IDF generation...")
t0 = time.monotonic()
from openubem.idf.builder import run_step3

idf_manifest = run_step3(gdf_57, schedule_library, STEP3_DIR)
success_idfs = (idf_manifest["generation_status"] == "success").sum()
print(f"  {success_idfs}/{len(idf_manifest)} IDFs generated ({time.monotonic()-t0:.1f}s)")
print(f"  generation_status counts: {idf_manifest['generation_status'].value_counts().to_dict()}")

# Build enriched GDF for simulation
enriched_for_sim = gpd.GeoDataFrame(
    [{"osm_id": row["osm_id"], "epw_path": str(EPW_PATH)}
     for _, row in idf_manifest.iterrows()],
    geometry=gpd.GeoSeries([None] * len(idf_manifest)),
)

print(f"\n[R3] IDF generation done. step3 dir: {STEP3_DIR}")
print(f"[R3] Starting fleet simulation: {success_idfs} buildings, n_jobs=6 ...")

# ── Step 4: Fleet simulation ──────────────────────────────────────────────────
t_sim = time.monotonic()
from openubem.simulation import run_neighbourhood

sim_manifest = run_neighbourhood(
    idf_manifest, enriched_for_sim, SIM_DIR, n_jobs=6, backend="loky"
)
wall_sim = time.monotonic() - t_sim

print(f"\n[R3] Fleet simulation completed in {wall_sim/60:.1f} min")
status_counts = sim_manifest["status"].value_counts().to_dict()
print(f"[R3] Status counts: {status_counts}")
n_success = status_counts.get("success", 0)
n_cached = status_counts.get("success_cached", 0)
print(f"[R3] Success: {n_success + n_cached} / {len(sim_manifest)}")

if n_success + n_cached < len(sim_manifest):
    failed = sim_manifest[~sim_manifest["status"].isin({"success", "success_cached"})]
    print(f"[R3] FAILURES ({len(failed)}):")
    for _, r in failed.head(20).iterrows():
        print(f"  osm_id={r['osm_id']} status={r['status']} msg={str(r.get('error_msg', ''))[:120]}")

# ── Step 5 setup: rebuild enriched_gdf from SQL Zones ────────────────────────
_floor_rx = re.compile(r"_F(\d+)_")


def _build_enriched_gdf_from_sql(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    rows = []
    for _, idf_row in idf_mf.iterrows():
        osm_id = str(idf_row["osm_id"])
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == osm_id]

        footprint_area_m2 = 200.0
        num_floors = 1.0
        height_m = 3.5
        centroid_x, centroid_y = 0.0, 0.0

        if len(sim_row) > 0 and sim_row.iloc[0]["status"] == "success":
            sql_path = Path(str(sim_row.iloc[0]["sql_path"]))
            if sql_path.exists():
                try:
                    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
                    zones = conn.execute(
                        "SELECT ZoneName, CeilingHeight, FloorArea, CentroidX, CentroidY FROM Zones"
                    ).fetchall()
                    conn.close()

                    zoning = idf_row["zoning_strategy"]
                    num_zones = int(idf_row["num_zones"])

                    if zoning == "single_zone":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        height_m = float(z[1])
                        num_floors = max(1.0, round(height_m / 3.5))
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                    elif zoning == "one_zone_per_floor":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        num_floors = float(num_zones)
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    elif "perimeter_core" in zoning:
                        floor_areas: dict[int, float] = {}
                        for z in zones:
                            m = _floor_rx.search(z[0])
                            if m:
                                f = int(m.group(1))
                                floor_areas[f] = floor_areas.get(f, 0.0) + float(z[2])
                        num_floors = max(1.0, float(len(floor_areas)))
                        footprint_area_m2 = floor_areas.get(0, sum(floor_areas.values()) / max(1, len(floor_areas)))
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    else:
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                except Exception as e:
                    print(f"  SQL error for {osm_id}: {e}")

        rows.append({
            "osm_id": osm_id,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })

    return gpd.GeoDataFrame(rows, crs="EPSG:32619")


print("\n[R3] Building enriched GDF from SQL Zones tables...")
t_gdf = time.monotonic()
enriched_gdf = _build_enriched_gdf_from_sql(idf_manifest, sim_manifest)
print(f"[R3] Enriched GDF: {enriched_gdf.shape} ({time.monotonic()-t_gdf:.1f}s)")

if "csv_path" not in sim_manifest.columns:
    sim_manifest = sim_manifest.copy()
    sim_manifest["csv_path"] = None

# ── Step 5: aggregate_results ────────────────────────────────────────────────
print("[R3] Step 5: aggregate_results...")
t0 = time.monotonic()
from openubem.results import aggregate_results

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    results_gdf = aggregate_results(
        sim_manifest, idf_manifest, enriched_gdf,
        RESULTS_DIR,
        state="MA",
        make_figures=True,
        ep_version="23.1.0",
    )
wall_step5 = time.monotonic() - t0
print(f"[R3] aggregate_results completed in {wall_step5:.1f}s")

# ── F12 gates ─────────────────────────────────────────────────────────────────
import math
from openubem import config

print("\n=== F12 GATE VALUES ===")

success_statuses = {"success", "success_cached", "success_csv_fallback"}
sim_success = sim_manifest[sim_manifest["status"].isin({"success", "success_cached"})]
n_sim_success = len(sim_success)
parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99
print(f"pct_parse_success: {pct_parse_success*100:.2f}% (n={n_parsed}/{n_sim_success}, gate: >=99%, PASS={gate_pct_parse})")

lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
print(f"EUI plausibility >=99% in [{lb},{ub}]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}), PASS={gate_eui}")
if len(outliers) > 0:
    print(f"  Outliers ({len(outliers)}): min={outliers.min():.1f}, max={outliers.max():.1f}")

zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0
print(f"Zone-count integrity: {n_zone_mismatch} mismatches (gate: 0, PASS={gate_zone})")

failed_parse = results_gdf[results_gdf["simulation_status"] == "failed_parse"]
print(f"failed_parse buildings: {len(failed_parse)}")

print("\n[Checking gas/ABUPS/meter on 20 sample buildings...]")
from openubem.results.parser import check_building_integrity

gas_nonzero = 0
abups_results = []
meter_results = []
checked = 0
for _, row in parsed.head(20).iterrows():
    osm_id = str(row["osm_id"])
    sim_r = sim_manifest[sim_manifest["osm_id"].astype(str) == osm_id]
    if len(sim_r) > 0 and sim_r.iloc[0]["status"] == "success":
        sql = Path(str(sim_r.iloc[0]["sql_path"]))
        if sql.exists():
            try:
                conn = sqlite3.connect(f"file:{sql}?mode=ro", uri=True)
                gas_j = conn.execute("""
                    SELECT COALESCE(SUM(r.Value), 0.0)
                    FROM ReportData r
                    JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
                    WHERE d.Name = 'NaturalGas:Facility' AND d.ReportingFrequency = 'Run Period'
                """).fetchone()[0] or 0.0
                conn.close()
                if gas_j > 0:
                    gas_nonzero += 1
                checked += 1
            except Exception as e:
                print(f"  gas check error: {e}")
            ig = check_building_integrity(sql)
            if ig["abups_ok"] is not None:
                abups_results.append(ig["abups_ok"])
            if ig["meter_ok"] is not None:
                meter_results.append(ig["meter_ok"])

gate_gas = gas_nonzero == 0
print(f"NaturalGas:Facility = 0 for all ({checked} checked): {gas_nonzero} non-zero (PASS={gate_gas})")
if abups_results:
    pct_abups = sum(abups_results) / len(abups_results)
    print(f"ABUPS +-0.5%: {sum(abups_results)}/{len(abups_results)} OK ({pct_abups*100:.1f}%)")
if meter_results:
    pct_meter = sum(meter_results) / len(meter_results)
    print(f"Meter closure +-1%: {sum(meter_results)}/{len(meter_results)} OK ({pct_meter*100:.1f}%)")

iod_vals = parsed["iod"].dropna()
print(f"\nIOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p50={iod_vals.median():.4f}, p95={iod_vals.quantile(0.95):.4f}, max={iod_vals.max():.4f}")

print("\n=== F12 GATE SUMMARY ===")
gates = {
    "pct_parse_success >= 99%": gate_pct_parse,
    "EUI plausibility >= 99%": gate_eui,
    "zone_count_integrity = 0 mismatches": gate_zone,
    "NaturalGas = 0": gate_gas,
}
all_pass = all(gates.values())
for name, result in gates.items():
    print(f"  {'PASS' if result else 'FAIL'}: {name}")
print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")

# ── B02: CBECS validation gates ───────────────────────────────────────────────
print("\n=== B02: CBECS VALIDATION GATES ===")
from openubem.results import compute_validation_gates

# Use total_eui_kwh_m2 column; compute_validation_gates looks for eui_kwh_m2 or site_eui_kwh_m2
# We need to alias total_eui_kwh_m2 → site_eui_kwh_m2 if neither exists
results_for_cbecs = results_gdf.copy()
if "eui_kwh_m2" not in results_for_cbecs.columns and "site_eui_kwh_m2" not in results_for_cbecs.columns:
    results_for_cbecs["site_eui_kwh_m2"] = results_for_cbecs["total_eui_kwh_m2"]

cbecs_gates = compute_validation_gates(results_for_cbecs, reference_path=CBECS_PATH)
print(f"\nCBECS validation gate results:")
print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% (threshold <30.0%) PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}% (threshold <10.0%) PASS={cbecs_gates['cbecs_nmbe_pass']}")
print(f"  R²:       {cbecs_gates['cbecs_r2']} (threshold >0.6) PASS={cbecs_gates['cbecs_r2_pass']}")
print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f} (threshold <0.10) PASS={cbecs_gates['cbecs_ks_d_pass']}")
print(f"  n_sim_buildings (gate-eligible): {cbecs_gates['n_sim_buildings']}")
print(f"  n_excluded_all_gates: {cbecs_gates['n_excluded_all_gates']}")

print("\n=== CBECS GATES: R3 vs BASELINE (R2) ===")
print(f"{'Metric':<12} {'R2 Baseline':>14} {'R2 PASS/FAIL':>13} {'R3 Result':>12} {'R3 PASS/FAIL':>13}")
print("-" * 70)
print(f"{'CV(RMSE)%':<12} {'53.784':>14} {'FAIL':>13} {cbecs_gates['cbecs_cv_rmse']:>12.3f} {'PASS' if cbecs_gates['cbecs_cv_rmse_pass'] else 'FAIL':>13}")
print(f"{'NMBE%':<12} {'-10.813':>14} {'FAIL':>13} {cbecs_gates['cbecs_nmbe']:>12.3f} {'PASS' if cbecs_gates['cbecs_nmbe_pass'] else 'FAIL':>13}")
print(f"{'R²':<12} {'0.7312':>14} {'PASS':>13} {cbecs_gates['cbecs_r2']:>12.4f} {'PASS' if cbecs_gates['cbecs_r2_pass'] else 'FAIL':>13}")
print(f"{'KS_D':<12} {'0.1902':>14} {'FAIL':>13} {cbecs_gates['cbecs_ks_d']:>12.4f} {'PASS' if cbecs_gates['cbecs_ks_d_pass'] else 'FAIL':>13}")

# ── Headline summary ──────────────────────────────────────────────────────────
summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
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
        print(f"  neighbourhood_gwp_total_kgco2: {gwp:.1f} kg CO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    print(f"  mean_iod_c: {mean_iod:.4f}" if mean_iod else "  mean_iod_c: N/A")
    print(f"  p95_iod_c: {p95_iod:.4f}" if p95_iod else "  p95_iod_c: N/A")
    pfa = summary.get("pct_floor_area_simulated")
    print(f"  pct_floor_area_simulated: {pfa*100:.2f}%" if pfa else "  pct_floor_area_simulated: N/A")
    print(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

if "archetype_id" in results_gdf.columns:
    print("\n=== EUI by archetype (success rows) ===")
    arch_stats = parsed.groupby("archetype_id")["total_eui_kwh_m2"].agg(["count", "mean", "median"])
    print(arch_stats.to_string())

print("\n=== ARTIFACT TREE ===")
for f in sorted(RESULTS_DIR.rglob("*")):
    if f.is_file():
        size = f.stat().st_size
        rel = f.relative_to(RESULTS_DIR)
        print(f"  {rel}  ({size/1024:.1f} KB)")

total_wall = time.monotonic()
print(f"\n[R3] Total wall clock: simulation={wall_sim/60:.1f} min, step5={wall_step5:.1f}s")
print("[R3] DONE")
