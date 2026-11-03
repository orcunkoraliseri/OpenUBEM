"""T06: Validate interior-ring fix on relation/6374725 via local EnergyPlus.

Regenerates the IDF with the interior-ring guard applied and asserts:
  - EnergyPlus Completed Successfully
  - Zero vertex-mismatch Severe errors in eplusout.err
  - IDF uses one_zone_per_floor (_whole zones) not core/perim donut

Usage: python scripts/diagnostics/t06_validate_relation6374725.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

GDF_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\01_buildings.gpkg")
CZ_PATH  = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\02a_climate_epw.parquet")
EPW_PATH = (
    Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban")
    / "weather" / "weather"
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
EP_EXE = Path(r"C:\EnergyPlusV23-1-0\energyplus.exe")
EP_IDD = EP_EXE.parent / "Energy+.idd"
OSM_ID = "relation/6374725"
WORK_DIR = Path(tempfile.gettempdir()) / "ubem_t06_run"


def _enrich_one(osm_id: str) -> tuple[pd.Series, dict]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    raw_gdf = gpd.read_file(str(GDF_PATH))
    climate = pd.read_parquet(str(CZ_PATH))

    row_raw = raw_gdf[raw_gdf["osm_id"] == osm_id]
    assert len(row_raw) == 1, f"{osm_id} not found in GDF"
    pilot_input = row_raw[_INPUT_SCHEMA_COLUMNS].copy()
    pilot_input["levels"] = pilot_input["levels"].astype("Int64")

    bc = BuildingClassifier()
    gdf_26 = bc.classify(pilot_input)

    cz_map   = dict(zip(climate["osm_id"], climate["climate_zone"]))
    prov_map = dict(zip(climate["osm_id"], climate["provenance_climate_zone"]))
    gdf_26["climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(cz_map), categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_26["epw_path"] = str(EPW_PATH)
    gdf_26["provenance_climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(prov_map), categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )

    gdf_57, schedule_library = enrich_semantics(gdf_26)
    row = gdf_57[gdf_57["osm_id"] == osm_id].iloc[0]
    return row, schedule_library


def _build_idf(row: pd.Series, schedule_library: dict, out_dir: Path) -> Path:
    from openubem.idf.builder import BuildingIDF

    gdf = gpd.read_file(str(GDF_PATH))
    bidf = BuildingIDF(row)
    manifest = bidf.build(gdf, schedule_library, out_dir)
    print(f"  generation_status:  {manifest['generation_status']}")
    print(f"  zoning_strategy:    {manifest['zoning_strategy']}")
    print(f"  num_zones:          {manifest['num_zones']}")
    idf_path = Path(manifest["idf_path"])
    assert idf_path.exists(), f"IDF not created at {idf_path}"
    return idf_path, manifest


def _run_ep(idf_path: Path) -> tuple[bool, str, str]:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    idd_dest = WORK_DIR / "Energy+.idd"
    if not idd_dest.exists():
        shutil.copy2(str(EP_IDD), str(idd_dest))
    cmd = [str(EP_EXE), "-w", str(EPW_PATH), "-d", str(WORK_DIR), "-x", "-r", str(idf_path)]
    subprocess.run(cmd, capture_output=True, timeout=600, cwd=str(WORK_DIR))
    end_file = WORK_DIR / "eplusout.end"
    err_file = WORK_DIR / "eplusout.err"
    end_text = end_file.read_text(errors="replace") if end_file.exists() else ""
    err_text = err_file.read_text(errors="replace") if err_file.exists() else ""
    success = "EnergyPlus Completed Successfully" in end_text
    return success, end_text, err_text


def main():
    assert GDF_PATH.exists(), f"GDF not found: {GDF_PATH}"
    assert EPW_PATH.exists(), f"EPW not found: {EPW_PATH}"
    assert EP_EXE.exists(),   f"EnergyPlus not found: {EP_EXE}"

    print(f"=== T06: Validate interior-ring fix on {OSM_ID} ===")

    # Confirm footprint has interior ring
    gdf = gpd.read_file(str(GDF_PATH))
    geom = gdf[gdf["osm_id"] == OSM_ID].iloc[0]["geometry"]
    n_interiors = len(list(geom.interiors))
    print(f"\n[0/3] Footprint check: {n_interiors} interior ring(s), area={geom.area:.1f} m²")
    assert n_interiors > 0, "Expected interior ring(s) on relation/6374725"

    out_dir = Path(tempfile.gettempdir()) / "ubem_t06_idf"
    (out_dir / "idfs").mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Enriching building...")
    row, schedule_library = _enrich_one(OSM_ID)

    print("\n[2/3] Building IDF with interior-ring guard...")
    idf_path, manifest = _build_idf(row, schedule_library, out_dir)

    # Verify zones are _whole (one_zone_per_floor), not core/perim donut
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.config import ENERGYPLUS_IDD_PATH
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    fixed_idf = IDF(str(idf_path))
    zone_names = [z.Name for z in fixed_idf.idfobjects["ZONE"]]
    has_whole = any("_whole" in n for n in zone_names)
    has_coreperim = any("_core" in n or ("_perim" in n and n.rsplit("_perim", 1)[-1].isdigit())
                        for n in zone_names)
    print(f"  Zones: {len(zone_names)}")
    print(f"  Has _whole zones: {has_whole}  (expected True)")
    print(f"  Has core/perim zones: {has_coreperim}  (expected False)")
    assert has_whole, f"Expected _whole zones; got {zone_names[:5]}"
    assert not has_coreperim, f"core/perim zones remain: {[n for n in zone_names if '_core' in n or '_perim' in n][:5]}"

    # Vertex mismatch check in IDF
    from openubem.idf.surfaces import find_mismatched_interzone_pairs
    mismatches = find_mismatched_interzone_pairs(fixed_idf)
    print(f"  Vertex-mismatch pairs in IDF: {len(mismatches)}  (expected 0)")
    assert not mismatches, f"Vertex mismatches remain: {mismatches[:3]}"

    print("\n[3/3] Running EnergyPlus...")
    ok, end_text, err_text = _run_ep(idf_path)
    print(f"  EnergyPlus success: {ok}")
    print(f"  End file: {end_text.strip()[:200]}")

    mismatch_lines = [l for l in err_text.splitlines()
                      if "mismatch" in l.lower() or "vertex" in l.lower()]
    severe_lines = [l for l in err_text.splitlines()
                    if any(kw in l for kw in ("** Severe **", "** Severe  **")) or re.search(r"\*\*\s+Fatal\s+\*\*", l)]
    if mismatch_lines:
        print("\n  vertex/mismatch lines in eplusout.err:")
        for l in mismatch_lines[:10]:
            print(f"    {l}")
    if severe_lines:
        print("\n  Severe/Fatal lines in eplusout.err:")
        for l in severe_lines[:10]:
            print(f"    {l}")

    assert ok, f"FAIL: EnergyPlus did not complete successfully. End: {end_text[:200]}"
    mismatch_severes = [l for l in severe_lines if "mismatch" in l.lower() or "vertex" in l.lower()]
    assert not mismatch_severes, f"FAIL: vertex-mismatch Severe lines in eplusout.err: {mismatch_severes}"

    # Report which tier was used
    tier = "one_zone_per_floor" if has_whole else "bbox"
    print(f"\nTier used for relation/6374725: {tier}")
    print(f"\nT06 PASSED: {OSM_ID} simulates cleanly with interior-ring guard applied.")


if __name__ == "__main__":
    main()
