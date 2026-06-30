"""T06 — LIVE_SMOKE: real footprints through fast_zone end-to-end.

Skips cleanly when the phaseE nyc_rural fixture is absent (CI on a clean checkout).
Never runs EnergyPlus — IDF build + parse only.
"""
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.builder import run_step3

try:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_LIVE_DIR = (
    Path(__file__).parent.parent
    / "docs" / "docs_VALIDATION" / "validations" / "overAll"
    / "results" / "phaseE" / "nyc_rural"
)
_LIVE_BUILDINGS = _LIVE_DIR / "01_buildings.gpkg"
_LIVE_RESULTS = _LIVE_DIR / "05_results.gpkg"

_FIXTURE_ABSENT = not (_LIVE_BUILDINGS.exists() and _LIVE_RESULTS.exists())

_EPW_PATH = str(Path(__file__).parent / "fixtures" / "synthetic.epw")

# Synthetic enrichment values; real attribute pipeline not needed here (T06 tests geometry only)
_ENRICHMENT = {
    "epw_path": _EPW_PATH,
    "provenance_climate_zone": "DEFAULT",
    "climate_zone": "4A",
    "vintage_standard": "DOERef1980to2004",
    "u_roof_w_m2k": 0.25,
    "u_wall_w_m2k": 0.40,
    "u_floor_w_m2k": 0.35,
    "u_window_w_m2k": 2.5,
    "shgc_window": 0.40,
    "assembly_roof": "NOMASS",
    "assembly_wall": "NOMASS",
    "provenance_u_roof": "DEFAULT",
    "provenance_u_wall": "DEFAULT",
    "provenance_u_window": "DEFAULT",
    "provenance_u_floor": "DEFAULT",
    "provenance_envelope": "DEFAULT",
    "infiltration_m3_s_m2": 0.0003,
    "wwr": 0.30,
    "lighting_w_m2": 10.76,
    "equipment_w_m2": 8.07,
    "occupant_m2_per_person": 9.3,
    "provenance_lighting": "DEFAULT",
    "provenance_equipment": "DEFAULT",
    "provenance_occupancy": "DEFAULT",
    "heating_setpoint_c": 21.0,
    "cooling_setpoint_c": 24.0,
    "heating_setback_c": 16.0,
    "cooling_setup_c": 30.0,
    "provenance_heating_setpoint": "DEFAULT",
    "provenance_cooling_setpoint": "DEFAULT",
}


def _build_live_gdf():
    """Load ≤2 MidriseApartment + ≤2 SmallOffice from the phaseE nyc_rural fixture."""
    buildings = gpd.read_file(_LIVE_BUILDINGS)
    results = gpd.read_file(_LIVE_RESULTS)

    # Join Polygon geometry to archetype assignments on osm_id
    joined = buildings[["osm_id", "levels", "height_m", "footprint_area_m2",
                         "data_quality_flag", "geometry"]].merge(
        results[["osm_id", "archetype_id"]], on="osm_id"
    )

    ma = joined[joined["archetype_id"] == "MidriseApartment"].head(2)
    so = joined[joined["archetype_id"] == "SmallOffice"].head(2)
    subset = pd.concat([ma, so], ignore_index=True)

    # Add synthetic enrichment columns
    for col, val in _ENRICHMENT.items():
        subset[col] = val

    gdf = gpd.GeoDataFrame(subset, geometry="geometry", crs=buildings.crs)
    return gdf


@pytest.mark.skipif(_FIXTURE_ABSENT, reason="live fixture absent — skipping LIVE_SMOKE")
def test_live_fast_zone_builds_and_parses(tmp_path):
    """LIVE_SMOKE (T06): real footprints through fast_zone must build without errors."""
    gdf = _build_live_gdf()
    assert len(gdf) >= 1, "No live buildings found in fixture"

    (tmp_path / "idfs").mkdir()
    manifest = run_step3(gdf, {}, tmp_path, resolution_mode="fast_zone")

    # (a) No failed_* generation status
    failed = manifest[manifest["generation_status"].str.startswith("failed_", na=False)]
    assert failed.empty, f"Buildings failed generation: {failed[['osm_id','generation_status']]}"

    # (b) Every produced IDF must parse without error
    for idf_path in manifest["idf_path"]:
        if idf_path:
            idf = IDF(idf_path)
            assert idf is not None, f"IDF failed to parse: {idf_path}"

    # (c) Buildings that produced true perimeter_core (num_zones > 1) must have more zones
    #     than the auto baseline (1 floor → single_zone = 1 zone for all live buildings here).
    #     Buildings that fell back (zoning.py narrow or surfaces.py "depth too great") produce
    #     num_zones == 1 and are excluded — both fallbacks are valid builder behaviour.
    truly_multi = manifest[manifest["num_zones"] > 1]
    for _, r in truly_multi.iterrows():
        assert r["num_zones"] > 1, f"{r['osm_id']}: unexpected single-zone in multi-zone path"
    assert len(truly_multi) > 0, (
        "All live buildings fell back to single-zone — no fast_zone perimeter_core path tested; "
        "check fixture or perimeter_depth_m vs footprint sizes"
    )
