"""C07: R3 IDF generation only (Steps 1-3, no simulation).

Generates 483 IDFs + 03_idf_manifest.parquet under TEMP/ubem_boston_r3/step3/.
Exits after Step 3. The cluster (C08) runs EnergyPlus remotely.
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
EPW_PATH = Path(r"C:\Users\o_iseri\AppData\Local\openubem\epw_cache\USA_MA_Boston.994971_TMYx.2011-2025.epw")

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_boston_r3"
STEP3_DIR = OUT_BASE / "step3"

print(f"[C07] Output base: {OUT_BASE}")
OUT_BASE.mkdir(exist_ok=True)
STEP3_DIR.mkdir(exist_ok=True)

# ── Step 1: Load Boston GDF ──────────────────────────────────────────────────
print("[C07] Loading Boston GDF...")
from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier

gdf_raw = gpd.read_file(str(BOSTON_GDF))
gdf_raw = gdf_raw[_INPUT_SCHEMA_COLUMNS]
gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
print(f"  {len(gdf_raw)} buildings loaded")

# ── Step 2: Classify buildings ───────────────────────────────────────────────
print("[C07] Step 2: building classification...")
t0 = time.monotonic()
bc = BuildingClassifier()
gdf_26 = bc.classify(gdf_raw)
print(f"  {len(gdf_26)} buildings classified ({time.monotonic()-t0:.1f}s)")

print("\n=== Archetype distribution (R3 classifier) ===")
arch_dist = gdf_26["archetype_id"].value_counts()
print(arch_dist.to_string())
print(f"  Total: {len(gdf_26)}")
n_unknown = int((gdf_26["archetype_id"] == "OpenUBEMUnknown").sum())
print(f"  OpenUBEMUnknown: {n_unknown}")
print(f"  FALLBACK_SIZE_DEFAULT: {int((gdf_26['archetype_source'] == 'FALLBACK_SIZE_DEFAULT').sum())}")

if n_unknown > 100:
    print(f"\n[C07] STOP: OpenUBEMUnknown = {n_unknown} > 100. Aborting.")
    sys.exit(1)
print(f"\n[C07] Unknown gate OK: {n_unknown} <= 100. Proceeding.\n")

# ── Step 2.1: Climate enrichment ─────────────────────────────────────────────
print("[C07] Step 2.1: climate enrichment...")
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
print(f"  climate zones assigned ({time.monotonic()-t0:.1f}s)")

# ── Step 2.2: Semantic enrichment ────────────────────────────────────────────
print("[C07] Step 2.2: semantic enrichment...")
t0 = time.monotonic()
from openubem.semantic import enrich_semantics

gdf_57, schedule_library = enrich_semantics(gdf_29)
print(f"  {len(gdf_57)} buildings enriched, {gdf_57.shape[1]} columns ({time.monotonic()-t0:.1f}s)")

# ── Step 3: IDF generation ────────────────────────────────────────────────────
print("[C07] Step 3: IDF generation...")
t0 = time.monotonic()
from openubem.idf.builder import run_step3

idf_manifest = run_step3(gdf_57, schedule_library, STEP3_DIR)
elapsed = time.monotonic() - t0

status_counts = idf_manifest["generation_status"].value_counts().to_dict()
n_success = status_counts.get("success", 0)
print(f"\n  {n_success}/{len(idf_manifest)} IDFs generated ({elapsed:.1f}s)")
print(f"  generation_status counts: {status_counts}")

print("\n=== IDF manifest archetype distribution ===")
arch_dist2 = idf_manifest["archetype_id"].value_counts()
print(arch_dist2.to_string())
n_unknown_idf = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
print(f"\n  OpenUBEMUnknown in IDF manifest: {n_unknown_idf}")

manifest_path = STEP3_DIR / "03_idf_manifest.parquet"
print(f"\n[C07] IDF manifest written to: {manifest_path}")
print(f"[C07] IDF directory: {STEP3_DIR / 'idfs'}")

n_idf_files = len(list((STEP3_DIR / "idfs").glob("*.idf")))
print(f"[C07] IDF files on disk: {n_idf_files}")

if n_success < 483:
    print(f"\n[C07] WARNING: only {n_success}/483 IDFs generated successfully.")

print("\n[C07] Generation complete. No simulation started (C07 gen-only).")
print("[C07] DONE")
