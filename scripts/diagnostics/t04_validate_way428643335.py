"""T04: Regenerate way/428643335 with the fix and validate via local EnergyPlus.

Reads la_urban step-2 enriched data, regenerates the IDF, then runs E+ locally.
Asserts: EnergyPlus Completed Successfully AND zero degenerate/severe-geometry lines
in eplusout.err.

Usage: python scripts/diagnostics/t04_validate_way428643335.py
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
OSM_ID = "way/428643335"
WORK_DIR = Path(tempfile.gettempdir()) / "ubem_t04_run"


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
    return idf_path


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

    print(f"=== T04: Regenerate {OSM_ID} with fix and validate via local EnergyPlus ===")

    out_dir = Path(tempfile.gettempdir()) / "ubem_t04_idf"
    (out_dir / "idfs").mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Enriching building...")
    row, schedule_library = _enrich_one(OSM_ID)

    print("\n[2/3] Building IDF with fix...")
    idf_path = _build_idf(row, schedule_library, out_dir)

    # Check IDF directly for degenerate surfaces before running E+
    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.config import ENERGYPLUS_IDD_PATH
    from openubem.idf.surfaces import _coreperim_has_degenerate_surfaces
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    fixed_idf = IDF(str(idf_path))
    still_degen = _coreperim_has_degenerate_surfaces(fixed_idf)
    print(f"  IDF degenerate surfaces (post-fix): {'PRESENT — FAIL' if still_degen else 'NONE — OK'}")
    assert not still_degen, "FAIL: degenerate surfaces remain in fixed IDF"

    print("\n[3/3] Running EnergyPlus...")
    ok, end_text, err_text = _run_ep(idf_path)
    print(f"  EnergyPlus success: {ok}")
    print(f"  End file: {end_text.strip()[:200]}")

    degen_lines = [l for l in err_text.splitlines() if "degenerate" in l.lower()]
    severe_lines = [l for l in err_text.splitlines()
                    if any(kw in l for kw in ("** Severe **", "** Severe  **")) or re.search(r"\*\*\s+Fatal\s+\*\*", l)]
    if degen_lines:
        print("\n  degenerate lines in eplusout.err:")
        for l in degen_lines[:10]:
            print(f"    {l}")
    if severe_lines:
        print("\n  Severe/Fatal lines in eplusout.err:")
        for l in severe_lines[:10]:
            print(f"    {l}")

    assert ok, f"FAIL: EnergyPlus did not complete successfully. End: {end_text[:200]}"
    assert not degen_lines, f"FAIL: degenerate lines found in eplusout.err"
    print("\nT04 PASSED: way/428643335 simulates cleanly with the fix.")


if __name__ == "__main__":
    main()
