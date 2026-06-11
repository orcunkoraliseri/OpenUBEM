"""T12: Boston end-to-end test via aggregate_results.
Uses the C4-corrected Step 4 fleet from ubem_boston_c4.
"""
import json
import sqlite3
import time
import warnings
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ── Load artifacts ──────────────────────────────────────────────────────────
D = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_boston_c4")
SIM_DIR = D / "sim"
STEP3_DIR = D / "step3"

sim_mf = pd.read_parquet(SIM_DIR / "04_simulation_manifest.parquet")
idf_mf = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")

print(f"[T12] Sim manifest: {len(sim_mf)} rows, success: {(sim_mf.status == 'success').sum()}")
print(f"[T12] IDF manifest: {len(idf_mf)} rows")


def _build_enriched_gdf(idf_mf, sim_mf):
    """Reconstruct enriched GDF from IDF manifest + SQL Zones table."""
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
                        # Group by floor (zone names: {osm}_F{n}_...) to get correct fa_per_floor.
                        # EnergyPlus SQL orders zones by type not by floor, so zones[:5] is wrong.
                        import re as _re
                        _floor_rx = _re.compile(r"_F(\d+)_")
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


# ── Build enriched GDF ──────────────────────────────────────────────────────
print("[T12] Building enriched GDF from SQL Zones tables...")
t_gdf = time.monotonic()
enriched_gdf = _build_enriched_gdf(idf_mf, sim_mf)
print(f"[T12] Enriched GDF: {enriched_gdf.shape} ({time.monotonic()-t_gdf:.1f}s)")

# Add csv_path column if missing
if "csv_path" not in sim_mf.columns:
    sim_mf = sim_mf.copy()
    sim_mf["csv_path"] = None

# ── Run aggregate_results ────────────────────────────────────────────────────
OUT_DIR = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_boston_c4_results")
OUT_DIR.mkdir(exist_ok=True)
print(f"[T12] Output dir: {OUT_DIR}")

t0 = time.monotonic()
from openubem.results import aggregate_results

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    results_gdf = aggregate_results(
        sim_mf, idf_mf, enriched_gdf,
        OUT_DIR,
        state="MA",
        make_figures=True,
        ep_version="23.1.0",
    )
wall = time.monotonic() - t0
print(f"[T12] aggregate_results completed in {wall:.1f}s")

# ── F12 gates ────────────────────────────────────────────────────────────────
import math
from openubem import config

print("\n=== F12 GATE VALUES ===")

# 1. pct_parse_success
success_statuses = {"success", "success_cached", "success_csv_fallback"}
sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
n_sim_success = len(sim_success)
parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
n_parsed = len(parsed)
pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
gate_pct_parse = pct_parse_success >= 0.99
print(f"pct_parse_success: {pct_parse_success*100:.2f}% (n={n_parsed}/{n_sim_success}, gate: >=99%, PASS={gate_pct_parse})")

# 2. EUI plausibility
lb, ub = config.EUI_PLAUSIBILITY_BOUNDS
valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
gate_eui = pct_plausible >= 0.99
outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
print(f"EUI plausibility >=99% in [{lb},{ub}]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}), PASS={gate_eui}")
if len(outliers) > 0:
    print(f"  Outliers ({len(outliers)}): min={outliers.min():.1f}, max={outliers.max():.1f}, osm_ids={list(results_gdf[results_gdf['total_eui_kwh_m2'].isin(outliers.values)]['osm_id'])[:5]}")

# 3. Zone-count integrity
zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
n_zone_mismatch = len(zone_mismatch)
gate_zone = n_zone_mismatch == 0
print(f"Zone-count integrity: {n_zone_mismatch} mismatches (gate: 0, PASS={gate_zone})")

# 4. Failed parse count
failed_parse = results_gdf[results_gdf["simulation_status"] == "failed_parse"]
print(f"failed_parse buildings: {len(failed_parse)}")
if len(failed_parse) > 0:
    print(f"  Examples: {list(failed_parse['error_summary'].head(3))}")

# 5. Gas zero check (sample 20 success buildings)
print("\n[Checking gas/ABUPS/meter on 20 sample buildings...]")
from openubem.results.parser import check_building_integrity
gas_nonzero = 0
abups_results = []
meter_results = []
checked = 0
for _, row in parsed.head(20).iterrows():
    osm_id = str(row["osm_id"])
    sim_r = sim_mf[sim_mf["osm_id"].astype(str) == osm_id]
    if len(sim_r) > 0 and sim_r.iloc[0]["status"] == "success":
        sql = Path(str(sim_r.iloc[0]["sql_path"]))
        if sql.exists():
            try:
                conn = sqlite3.connect(f"file:{sql}?mode=ro", uri=True)
                gas_j = conn.execute("""
                    SELECT COALESCE(SUM(r.Value), 0.0)
                    FROM ReportData r
                    JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
                    WHERE d.Name = "NaturalGas:Facility" AND d.ReportingFrequency = "Run Period"
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
else:
    print("ABUPS: no TabularDataWithStrings in SQL fixtures (check skipped - known Step-3 issue)")
if meter_results:
    pct_meter = sum(meter_results) / len(meter_results)
    print(f"Meter closure +-1%: {sum(meter_results)}/{len(meter_results)} OK ({pct_meter*100:.1f}%)")

# 6. IOD stats
iod_vals = parsed["iod"].dropna()
print(f"\nIOD distribution: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p50={iod_vals.median():.4f}, p95={iod_vals.quantile(0.95):.4f}, max={iod_vals.max():.4f}")

# ── Summary JSON ─────────────────────────────────────────────────────────────
summary_path = OUT_DIR / "05_neighbourhood_summary.json"
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    print("\n=== 05_neighbourhood_summary.json HEADLINE NUMBERS ===")
    eui = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui.get(k)
        if v is not None:
            print(f"  {k}: {v:.4f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  neighbourhood_gwp_total_kgco2: {gwp:.1f} kg CO2e")
    print(f"  mean_iod_c: {summary.get('mean_iod_c'):.4f}" if summary.get("mean_iod_c") else "  mean_iod_c: N/A")
    print(f"  p95_iod_c: {summary.get('p95_iod_c'):.4f}" if summary.get("p95_iod_c") else "  p95_iod_c: N/A")
    pfa = summary.get("pct_floor_area_simulated")
    print(f"  pct_floor_area_simulated: {pfa*100:.2f}%" if pfa else "  pct_floor_area_simulated: N/A")
    print(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

# ── EUI by archetype ─────────────────────────────────────────────────────────
if "archetype_id" in results_gdf.columns:
    print("\n=== EUI by archetype (success rows) ===")
    arch_stats = parsed.groupby("archetype_id")["total_eui_kwh_m2"].agg(["count", "mean", "median"])
    print(arch_stats.to_string())

# ── Artifact tree ─────────────────────────────────────────────────────────────
print("\n=== ARTIFACT TREE ===")
for f in sorted(OUT_DIR.rglob("*")):
    if f.is_file():
        size = f.stat().st_size
        rel = f.relative_to(OUT_DIR)
        print(f"  {rel}  ({size/1024:.1f} KB)")

print(f"\n[T12] Wall clock: {wall:.1f}s")
print("[T12] DONE")
