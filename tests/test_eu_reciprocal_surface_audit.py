"""GEO-06 saved-IDF reciprocal party-wall checks for European integration."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF
from shapely.geometry import box

from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.geometry.european_residential import (
    european_layout_to_zone_specs,
    generate_european_dwelling_layout,
)
from openubem.idf.european_controls import add_european_heating_controls
from openubem.idf.surfaces import (
    audit_reciprocal_interzone_wall_surfaces,
    extrude_geometry,
)


TEMPLATE = Path(__file__).parent.parent / "openubem" / "idf" / "templates" / "commercial_base.idf"
DATA_DIR = Path(__file__).parent.parent / "openubem" / "data" / "construction"
ENERGYPLUS = ENERGYPLUS_PATH / (
    "energyplus.exe" if sys.platform == "win32" else "energyplus"
)


@pytest.fixture(autouse=True)
def _idd() -> None:
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


def _zone(name: str, footprint):
    return {
        "name": name,
        "floor_polygon": footprint,
        "coords_m": list(footprint.exterior.coords)[:-1],
        "z_floor": 0.0,
        "z_ceiling": 3.0,
        "height_m": 3.0,
    }


def _saved_two_dwelling_idf(tmp_path, name: str) -> IDF:
    idf = IDF(str(TEMPLATE))
    extrude_geometry(
        idf,
        [
            _zone("EU_GEO06_F0_dwelling_a", box(0.0, 0.0, 6.0, 8.0)),
            _zone("EU_GEO06_F0_dwelling_b", box(6.0, 0.0, 12.0, 8.0)),
        ],
        [],
    )
    saved_path = tmp_path / name
    idf.saveas(str(saved_path))
    return IDF(str(saved_path))


def _party_faces(idf):
    return [
        surface
        for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if surface.Surface_Type.lower() == "wall"
        and surface.Outside_Boundary_Condition.lower() == "surface"
    ]


def _s0_sfh_record() -> dict[str, object]:
    """Use only control inputs from the declared S0 fixture in this smoke test."""
    payload = json.loads((DATA_DIR / "tabula_archetypes_es.json").read_text(encoding="utf-8"))
    return next(
        record
        for record in payload["records"]
        if record["archetype_id"] == "ES.ME.SFH.04.Gen.ReEx.001.001"
    )


def _add_smoke_construction(idf: IDF) -> None:
    """Make a minimally physical envelope for the controlled geometry smoke run."""
    idf.newidfobject(
        "MATERIAL:NOMASS",
        Name="EU Layout Smoke R2",
        Roughness="MediumRough",
        Thermal_Resistance=2.0,
        Thermal_Absorptance=0.9,
        Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject(
        "CONSTRUCTION",
        Name="EU Layout Smoke Construction",
        Outside_Layer="EU Layout Smoke R2",
    )
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        surface.Construction_Name = "EU Layout Smoke Construction"


def test_geo06_reopened_saved_idf_has_exactly_one_reciprocal_party_wall_mate(tmp_path):
    saved = _saved_two_dwelling_idf(tmp_path, "geo06_clean.idf")

    audit = audit_reciprocal_interzone_wall_surfaces(saved)

    assert audit.passed
    assert audit.party_face_count == 2
    assert audit.reciprocal_pair_count == 1


def test_geo06_missing_reciprocal_reference_fails_after_saved_idf_readback(tmp_path):
    saved = _saved_two_dwelling_idf(tmp_path, "geo06_reference_source.idf")
    partner = _party_faces(saved)[1]
    partner.Outside_Boundary_Condition_Object = "UNKNOWN_PARTNER"
    corrupt_path = tmp_path / "geo06_reference_corrupt.idf"
    saved.saveas(str(corrupt_path))

    audit = audit_reciprocal_interzone_wall_surfaces(IDF(str(corrupt_path)))

    assert not audit.passed
    assert any(failure.startswith("RECIPROCAL_REFERENCE_MISMATCH:") for failure in audit.failures)
    assert any(failure.startswith("MISSING_RECIPROCAL_SURFACE:") for failure in audit.failures)


def test_geo06_nonmatching_reciprocal_vertices_fail_after_saved_idf_readback(tmp_path):
    saved = _saved_two_dwelling_idf(tmp_path, "geo06_vertices_source.idf")
    partner = _party_faces(saved)[1]
    partner.Vertex_1_Xcoordinate = float(partner.Vertex_1_Xcoordinate) + 0.25
    corrupt_path = tmp_path / "geo06_vertices_corrupt.idf"
    saved.saveas(str(corrupt_path))

    audit = audit_reciprocal_interzone_wall_surfaces(IDF(str(corrupt_path)))

    assert not audit.passed
    assert any(failure.startswith("RECIPROCAL_VERTEX_MISMATCH:") for failure in audit.failures)


def test_generated_european_layout_extrudes_to_reciprocal_saved_idf_party_walls(tmp_path):
    layout = generate_european_dwelling_layout(
        box(0.0, 0.0, 30.0, 12.0),
        requested_dwelling_count=3,
    )
    zones = european_layout_to_zone_specs(
        layout,
        building_id="EU_LAYOUT_READBACK",
        height_m=3.0,
    )
    idf = IDF(str(TEMPLATE))
    extrude_geometry(idf, zones, [])
    saved_path = tmp_path / "eu_layout_readback.idf"
    idf.saveas(str(saved_path))

    audit = audit_reciprocal_interzone_wall_surfaces(IDF(str(saved_path)))

    assert layout.dwelling_layout_emitted
    assert len(zones) == 3
    assert audit.passed
    assert audit.party_face_count == 4
    assert audit.reciprocal_pair_count == 2


@pytest.mark.skipif(not ENERGYPLUS.exists(), reason="EnergyPlus 23.1 executable is not installed")
def test_generated_european_layout_runs_energyplus_design_day_smoke(tmp_path):
    """A controlled layout-to-IDF fixture must survive an actual E+ design-day run.

    This test intentionally uses only the supported explicit-count rectangle and
    the existing S0 control parameters.  It is not a live observed-building
    result and it does not impute an archetype, dwelling count, or weather file.
    """
    layout = generate_european_dwelling_layout(
        box(0.0, 0.0, 30.0, 12.0),
        requested_dwelling_count=3,
    )
    zones = european_layout_to_zone_specs(
        layout,
        building_id="EU_LAYOUT_EPLUS",
        height_m=3.0,
    )
    path = tmp_path / "eu_layout_design_day.idf"
    path.write_text(
        """Version,23.1;
Timestep,4;
Building,EU Layout Design Day,0,Suburbs,0.0001,0.000001,MinimalShadowing,30,1;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,Yes,Yes,No,Yes,No,No,1;
Site:Location,EU Site,40,-75,-5,0;
SizingPeriod:DesignDay,EU Cold Day,1,21,WinterDesignDay,-10,0,,,Wetbulb,-10,,,,,101325,0,0,No,No,No,ASHRAEClearSky,,,,0;
ScheduleTypeLimits,Any Number;
""",
        encoding="utf-8",
    )
    idf = IDF(str(path))
    extrude_geometry(idf, zones, [])
    _add_smoke_construction(idf)
    record = _s0_sfh_record()
    for zone in zones:
        idf.newidfobject(
            "SIZING:ZONE",
            Zone_or_ZoneList_Name=zone["name"],
            Zone_Cooling_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Cooling_Design_Supply_Air_Temperature=13.0,
            Zone_Heating_Design_Supply_Air_Temperature_Input_Method="SupplyAirTemperature",
            Zone_Heating_Design_Supply_Air_Temperature=50.0,
            Zone_Cooling_Design_Supply_Air_Humidity_Ratio=0.008,
            Zone_Heating_Design_Supply_Air_Humidity_Ratio=0.008,
        )
        add_european_heating_controls(idf, record, zone["name"])
    idf.saveas(str(path))

    result = subprocess.run(
        [str(ENERGYPLUS), "-x", "-r", "-d", str(tmp_path), str(path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
    )
    err = (tmp_path / "eplusout.err").read_text(encoding="utf-8", errors="replace")
    assert result.returncode == 0, err
    assert "Completed Successfully" in err
    assert "Beginning Zone Sizing" in err
    assert audit_reciprocal_interzone_wall_surfaces(IDF(str(path))).passed
