"""OPEN-48 T03: assert BuildingIDF.build actually wires assign_elevators.

Live builder.py never called openubem.idf.elevators.assign_elevators until the T03
restore (§5 fact 4 of PLAN_three-rulings-2026-08-12.md). These tests build one real
IDF through the full orchestrator (not the emitter function directly, which is
already covered by tests/test_elevators.py) and assert the ELECTRICEQUIPMENT object
appears for an elevator-eligible archetype and is absent for one that is not.
"""
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.builder import BuildingIDF

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SYNTHETIC_EPW = FIXTURES_DIR / "synthetic.epw"


def _idf_setiddname_safe():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


_idf_setiddname_safe()


def _make_row(archetype_id: str, footprint_area_m2: float, levels: int) -> pd.Series:
    from shapely.geometry import box

    side = footprint_area_m2 ** 0.5
    poly = box(0, 0, side, side)
    return pd.Series({
        "osm_id": f"way/TEST_{archetype_id}",
        "archetype_id": archetype_id,
        "epw_path": str(SYNTHETIC_EPW),
        "u_roof_w_m2k": 0.2,
        "u_wall_w_m2k": 0.3,
        "u_floor_w_m2k": 0.4,
        "u_window_w_m2k": 2.5,
        "shgc_window": 0.4,
        "wwr": 0.3,
        "infiltration_m3_s_m2": 0.0003,
        "lighting_w_m2": 10.0,
        "equipment_w_m2": 8.0,
        "occupant_m2_per_person": 10.0,
        "heating_setpoint_c": 21.0,
        "cooling_setpoint_c": 24.0,
        "climate_zone": "3A",
        "vintage_standard": "DOERef1980to2004",
        "levels": levels,
        "height_m": levels * 3.5,
        "footprint_area_m2": footprint_area_m2,
        "geometry": poly,
        "data_quality_flag": "",
    })


def _build(row: pd.Series) -> dict:
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        (out_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, out_path)
    return manifest, bidf.idf


class TestBuilderElevatorsWired:
    def test_elevator_eligible_archetype_emits_elevators_object(self):
        row = _make_row("LargeOffice", footprint_area_m2=46320.38, levels=12)
        manifest, idf = _build(row)
        assert manifest.get("generation_status") == "success", manifest
        elevs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"]
                 if e.EndUse_Subcategory == "Elevators"]
        assert len(elevs) == 1
        assert elevs[0].Name == "Elevators_LargeOffice"

    def test_non_elevator_archetype_emits_nothing(self):
        row = _make_row("SmallOffice", footprint_area_m2=511.16, levels=1)
        manifest, idf = _build(row)
        assert manifest.get("generation_status") == "success", manifest
        elevs = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"]
                 if e.EndUse_Subcategory == "Elevators"]
        assert elevs == []
