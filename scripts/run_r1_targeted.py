"""R1: Targeted regen + re-simulation of the 8 failed Boston buildings.

Pipeline: Step-1 fixture → Step-2 classifier → Step-2.1 climate (offline) →
Step-2.2 semantics → Step-3 IDF generation (8 buildings, full-gdf shading context) →
Step-4 simulation (8 buildings, n_jobs=4) → merged manifest (C4 475 + R1 8 = 483).
"""
from __future__ import annotations

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

C4_BASE = Path(tempfile.gettempdir()) / "ubem_boston_c4"
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_boston_r1"
STEP3_DIR = OUT_BASE / "step3"
SIM_DIR = OUT_BASE / "sim"

TARGET_OSM_IDS = [
    "29716487", "240391795", "241978446", "1281831066",
    "29573070", "241186243", "788015166", "458718877",
]

print(f"[R1] Output base: {OUT_BASE}")
OUT_BASE.mkdir(exist_ok=True)
STEP3_DIR.mkdir(exist_ok=True)
SIM_DIR.mkdir(exist_ok=True)

# ── Step 1: Load Boston GDF ──────────────────────────────────────────────────
print("[R1] Loading Boston GDF...")
from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
gdf_raw = gpd.read_file(str(BOSTON_GDF))
gdf_raw = gdf_raw[_INPUT_SCHEMA_COLUMNS]
gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
print(f"  {len(gdf_raw)} buildings loaded")

# ── Step 2: Classify buildings ───────────────────────────────────────────────
print("[R1] Step 2: building classification...")
t0 = time.monotonic()
bc = BuildingClassifier()
gdf_26 = bc.classify(gdf_raw)
print(f"  {len(gdf_26)} buildings classified ({time.monotonic()-t0:.1f}s)")

# ── Step 2.1: Climate enrichment (offline, using cached EPW) ─────────────────
print("[R1] Step 2.1: climate enrichment (offline)...")
t0 = time.monotonic()

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
print(f"  climate zones assigned ({time.monotonic()-t0:.1f}s)")

# ── Step 2.2: Semantic enrichment ────────────────────────────────────────────
print("[R1] Step 2.2: semantic enrichment...")
t0 = time.monotonic()
from openubem.semantic import enrich_semantics
gdf_57, schedule_library = enrich_semantics(gdf_29)
print(f"  {len(gdf_57)} buildings enriched, {gdf_57.shape[1]} columns ({time.monotonic()-t0:.1f}s)")

# ── Step 3: IDF generation (8 buildings only, full gdf as shading context) ───
print(f"[R1] Step 3: IDF generation for {len(TARGET_OSM_IDS)} target buildings...")
t0 = time.monotonic()

from openubem.idf.builder import BuildingIDF

(STEP3_DIR / "idfs").mkdir(exist_ok=True)

target_mask = gdf_57["osm_id"].astype(str).isin(TARGET_OSM_IDS)
gdf_targets = gdf_57[target_mask]
print(f"  Target buildings found in enriched GDF: {len(gdf_targets)}")

manifest_rows = []
for _, row in gdf_targets.iterrows():
    # Pass full gdf_57 as shading context
    manifest_row = BuildingIDF(row).build(gdf_57, schedule_library, STEP3_DIR)
    osm = str(row["osm_id"])
    status = manifest_row.get("generation_status", "?")
    print(f"  [{osm}] generation_status={status}")
    manifest_rows.append(manifest_row)

idf_manifest_r1 = pd.DataFrame(manifest_rows)
idf_manifest_r1.to_parquet(STEP3_DIR / "03_idf_manifest.parquet", engine="pyarrow", index=False)
print(f"  IDF generation done ({time.monotonic()-t0:.1f}s)")
print(f"  generation_status counts: {idf_manifest_r1['generation_status'].value_counts().to_dict()}")

# Abort if any target still has fallback_bbox
failed_gen = idf_manifest_r1[idf_manifest_r1["generation_status"] != "success"]
if len(failed_gen) > 0:
    print(f"\n[R1] ERROR: {len(failed_gen)} buildings still not generation_status=success:")
    print(failed_gen[["osm_id", "generation_status"]].to_string())
    sys.exit(1)

# ── Step 4: Simulate 8 buildings ─────────────────────────────────────────────
print(f"[R1] Step 4: simulating {len(idf_manifest_r1)} buildings with n_jobs=4...")

enriched_for_sim = gpd.GeoDataFrame(
    [{"osm_id": row["osm_id"], "epw_path": str(EPW_PATH)}
     for _, row in idf_manifest_r1.iterrows()],
    geometry=gpd.GeoSeries([None] * len(idf_manifest_r1)),
)

t_sim = time.monotonic()
from openubem.simulation import run_neighbourhood
sim_manifest_r1 = run_neighbourhood(
    idf_manifest_r1, enriched_for_sim, SIM_DIR, n_jobs=4, backend="loky"
)
wall_sim = time.monotonic() - t_sim

print(f"\n[R1] Simulation completed in {wall_sim/60:.1f} min")
print(f"[R1] R1 status counts: {sim_manifest_r1['status'].value_counts().to_dict()}")

non_success_r1 = sim_manifest_r1[sim_manifest_r1["status"] != "success"]
if len(non_success_r1) > 0:
    print(f"\n[R1] STOP — {len(non_success_r1)} buildings still failed:")
    for _, r in non_success_r1.iterrows():
        osm = str(r["osm_id"])
        print(f"  osm_id={osm}, status={r['status']}, error_summary={r.get('error_summary','')}")
        # Print eplusout.err excerpt
        work_dir = Path(str(r.get("work_dir", "")))
        err_file = work_dir / "eplusout.err"
        if err_file.exists():
            lines = err_file.read_text(errors="replace").splitlines()
            severe = [l for l in lines if "Severe" in l or "Fatal" in l]
            print(f"    err excerpt (severe/fatal lines): {severe[:5]}")
    sys.exit(1)

print(f"\n[R1] All 8 buildings succeeded.")

# ── Merged manifest ───────────────────────────────────────────────────────────
print("[R1] Building merged manifest...")
c4_mf = pd.read_parquet(C4_BASE / "sim" / "04_simulation_manifest.parquet")
print(f"  C4 manifest: {len(c4_mf)} rows, status counts: {c4_mf['status'].value_counts().to_dict()}")

# Drop the 8 failed rows from C4
c4_clean = c4_mf[~c4_mf["osm_id"].astype(str).isin(TARGET_OSM_IDS)].copy()
print(f"  C4 after dropping 8: {len(c4_clean)} rows")

# Ensure column alignment
for col in c4_clean.columns:
    if col not in sim_manifest_r1.columns:
        sim_manifest_r1[col] = None
sim_manifest_r1_aligned = sim_manifest_r1[c4_clean.columns]

merged = pd.concat([c4_clean, sim_manifest_r1_aligned], ignore_index=True)
merged_path = OUT_BASE / "04_simulation_manifest_merged.parquet"
merged.to_parquet(merged_path, engine="pyarrow", index=False)

print(f"\n[R1] Merged manifest: {len(merged)} rows")
print(f"[R1] Merged status counts: {merged['status'].value_counts().to_dict()}")

non_success_merged = merged[merged["status"] != "success"]
if len(non_success_merged) > 0:
    print(f"\n[R1] WARNING: {len(non_success_merged)} non-success rows in merged manifest:")
    print(non_success_merged[["osm_id", "status"]].to_string())
else:
    print(f"[R1] ACCEPTANCE PASS: 483 success / 0 anything-else")

print(f"\n[R1] SIM_DIR:        {SIM_DIR}")
print(f"[R1] MERGED_MANIFEST: {merged_path}")
print("[R1] R04 DONE")
