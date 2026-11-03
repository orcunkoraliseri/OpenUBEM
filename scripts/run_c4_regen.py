"""C4.2: Regenerate Boston IDFs and re-simulate fleet into fresh directories.

Pipeline: Step-1 fixture → Step-2 classifier → Step-2.1 climate (offline, cached EPW) →
Step-2.2 semantics → Step-3 IDF generation → Step-4 simulation.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).parent.parent
BOSTON_GDF = REPO / "tests" / "fixtures" / "boston_downtown_500m.gpkg"
EPW_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\openubem_epw_7rrpvd27\weather\USA_MA_Boston.994971_TMYx.2011-2025.epw")

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_boston_c4"
STEP3_DIR = OUT_BASE / "step3"
SIM_DIR = OUT_BASE / "sim"

print(f"[C4.2] Output base: {OUT_BASE}")
OUT_BASE.mkdir(exist_ok=True)
STEP3_DIR.mkdir(exist_ok=True)
SIM_DIR.mkdir(exist_ok=True)

# ── Step 1: Load Boston GDF ──────────────────────────────────────────────────
print("[C4.2] Loading Boston GDF...")
from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
gdf_raw = gpd.read_file(str(BOSTON_GDF))
gdf_raw = gdf_raw[_INPUT_SCHEMA_COLUMNS]
gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
print(f"  {len(gdf_raw)} buildings loaded")

# ── Step 2: Classify buildings ───────────────────────────────────────────────
print("[C4.2] Step 2: building classification...")
t0 = time.monotonic()
bc = BuildingClassifier()
gdf_26 = bc.classify(gdf_raw)
print(f"  {len(gdf_26)} buildings classified ({time.monotonic()-t0:.1f}s)")

# ── Step 2.1: Climate enrichment (offline, using cached EPW) ─────────────────
print("[C4.2] Step 2.1: climate enrichment (offline)...")
t0 = time.monotonic()

# Assign climate zones
from openubem.acquisition.climate_zone import assign_climate_zones
zone_df = assign_climate_zones(gdf_26)

gdf_29 = gdf_26.copy()
from openubem.acquisition import _CLIMATE_ZONE_VOCAB
gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=_CLIMATE_ZONE_VOCAB)
gdf_29["epw_path"] = str(EPW_PATH)
gdf_29["provenance_climate_zone"] = pd.Categorical(
    zone_df["provenance_climate_zone"].values,
    categories=["ASHRAE_STANDARD", "HEURISTIC"],
)

# Write Step-2.1 sidecar
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
print("[C4.2] Step 2.2: semantic enrichment...")
t0 = time.monotonic()
from openubem.semantic import enrich_semantics
gdf_57, schedule_library = enrich_semantics(gdf_29)
print(f"  {len(gdf_57)} buildings enriched, {gdf_57.shape[1]} columns ({time.monotonic()-t0:.1f}s)")

# ── Step 3: IDF generation ────────────────────────────────────────────────────
print("[C4.2] Step 3: IDF generation...")
t0 = time.monotonic()
from openubem.idf.builder import run_step3
idf_manifest = run_step3(gdf_57, schedule_library, STEP3_DIR)
success_idfs = (idf_manifest["generation_status"] == "success").sum()
print(f"  {success_idfs}/{len(idf_manifest)} IDFs generated ({time.monotonic()-t0:.1f}s)")
print(f"  generation_status counts: {idf_manifest['generation_status'].value_counts().to_dict()}")

# Spot-check: verify one IDF contains 'Zone Lights Electricity Energy'
success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
if len(success_rows) > 0:
    sample_idf = Path(success_rows.iloc[0]["idf_path"])
    if sample_idf.exists():
        idf_text = sample_idf.read_text(errors="replace")
        if "Zone Lights Electricity Energy" in idf_text:
            print(f"  [SPOT CHECK] Zone Lights Electricity Energy: PRESENT in {sample_idf.name}")
        elif "Zone Lights Electric Energy" in idf_text:
            print(f"  [SPOT CHECK] WARNING: old name 'Zone Lights Electric Energy' in {sample_idf.name}")
        else:
            print(f"  [SPOT CHECK] WARNING: neither name found in {sample_idf.name}")

# Build enriched GDF for simulation (needs epw_path per building)
print("[C4.2] Building enriched GDF for simulation...")
enriched_for_sim = gpd.GeoDataFrame(
    [{"osm_id": row["osm_id"], "epw_path": str(EPW_PATH)}
     for _, row in idf_manifest.iterrows()],
    geometry=gpd.GeoSeries([None] * len(idf_manifest)),
)

print(f"[C4.2] IDF generation done. step3 dir: {STEP3_DIR}")
print(f"[C4.2] Ready to simulate {success_idfs} buildings into {SIM_DIR}")
print(f"[C4.2] Starting fleet simulation at n_jobs=8 ...")

# ── Step 4: Fleet simulation ──────────────────────────────────────────────────
t_sim = time.monotonic()
from openubem.simulation import run_neighbourhood
sim_manifest = run_neighbourhood(
    idf_manifest, enriched_for_sim, SIM_DIR, n_jobs=8, backend="loky"
)
wall_sim = time.monotonic() - t_sim

print(f"\n[C4.2] Fleet simulation completed in {wall_sim/60:.1f} min")
status_counts = sim_manifest["status"].value_counts().to_dict()
print(f"[C4.2] Status counts: {status_counts}")

n_success = status_counts.get("success", 0)
n_cached = status_counts.get("success_cached", 0)
print(f"[C4.2] Success: {n_success + n_cached} / {len(sim_manifest)}")

# Verify new variable names present in one success SQL
success_sim = sim_manifest[sim_manifest["status"] == "success"]
if len(success_sim) > 0:
    import sqlite3
    sample_sql = Path(str(success_sim.iloc[0]["sql_path"]))
    if sample_sql.exists():
        conn = sqlite3.connect(f"file:{sample_sql}?mode=ro", uri=True)
        names = conn.execute("SELECT DISTINCT Name FROM ReportDataDictionary WHERE Name LIKE '%Electricity Energy%'").fetchall()
        conn.close()
        print(f"[C4.2] SQL spot-check: Electricity Energy variables: {[r[0] for r in names]}")

print(f"\n[C4.2] STEP3_DIR: {STEP3_DIR}")
print(f"[C4.2] SIM_DIR:   {SIM_DIR}")
print(f"[C4.2] SIM_MANIFEST: {SIM_DIR / '04_simulation_manifest.parquet'}")
