"""TechTransfer block 6, Task PV-WIRE: assert BuildingIDF.build actually wires

`openubem.idf.pv.inject_pv`/`strip_existing_pv` through the generic per-building
build path (config.PV_INJECTION_ENABLED gates whether a Generator:PVWatts object
lands on the built IDF for a building with a qualifying flat roof). No EnergyPlus
run here -- IDF-object assertions only, same pattern as
tests/test_builder_elevators_wired.py.
"""
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem import config
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
        "osm_id": f"way/TEST_PV_{archetype_id}",
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


def _build(row: pd.Series) -> tuple[dict, object]:
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        (out_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, out_path)
    return manifest, bidf.idf


def _row_with_qualifying_roof() -> pd.Series:
    # SmallOffice, single storey, 511.16 m2 footprint -- one flat roof surface
    # well above pv.MIN_QUALIFYING_ROOF_AREA_M2 (7.5 m2), same archetype/geometry
    # already used by tests/test_builder_elevators_wired.py for the non-elevator case.
    return _make_row("SmallOffice", footprint_area_m2=511.16, levels=1)


class TestPVBuildWiring:
    def test_flag_on_build_carries_pv_generator(self, monkeypatch):
        monkeypatch.setattr(config, "PV_INJECTION_ENABLED", True)
        row = _row_with_qualifying_roof()
        manifest, idf = _build(row)
        assert manifest.get("generation_status") == "success", manifest
        generators = idf.idfobjects["GENERATOR:PVWATTS"]
        assert len(generators) >= 1, (
            "Expected at least one Generator:PVWatts object on a qualifying-roof "
            f"build with PV_INJECTION_ENABLED=True; manifest={manifest}"
        )

    def test_flag_off_build_carries_no_pv_generator(self, monkeypatch):
        monkeypatch.setattr(config, "PV_INJECTION_ENABLED", False)
        row = _row_with_qualifying_roof()
        manifest, idf = _build(row)
        assert manifest.get("generation_status") == "success", manifest
        generators = idf.idfobjects["GENERATOR:PVWATTS"]
        assert len(generators) == 0, (
            "Expected no Generator:PVWatts object when PV_INJECTION_ENABLED=False; "
            f"got {[g.Name for g in generators]}"
        )
