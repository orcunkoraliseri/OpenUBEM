"""S0 box-plan and source-component readback tests (X-05 / D-EU-01)."""
from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

import pytest
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH, ENERGYPLUS_PATH
from openubem.idf.european_box import (
    S0_ARCHETYPE_IDS,
    add_s0_equivalent_envelope,
    rectangular_tabula_box,
    source_h_transmission_w_m2k,
    source_h_ventilation_w_m2k,
)
from openubem.idf.european_controls import add_european_heating_controls
from openubem.validation.step8_gates import audit_saved_idf_geometries


DATA_DIR = Path(__file__).parent.parent / "openubem" / "data" / "construction"
_ENERGYPLUS = ENERGYPLUS_PATH / ("energyplus.exe" if sys.platform == "win32" else "energyplus")


@pytest.fixture(autouse=True)
def _idd() -> None:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))


def _records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for country in ("es", "gb", "it", "fr"):
        payload = json.loads((DATA_DIR / f"tabula_archetypes_{country}.json").read_text(encoding="utf-8"))
        records.update({record["archetype_id"]: record for record in payload["records"]})
    return records


def test_all_registry_transmission_components_read_back_to_tabula_target():
    for record in _records().values():
        assert source_h_transmission_w_m2k(record) == pytest.approx(
            record["h_transmission_w_m2k"], abs=1e-12
        )
        assert source_h_ventilation_w_m2k(record) == pytest.approx(
            record["h_ventilation_w_m2k"], rel=0.01
        )


def test_s0_has_one_feasible_fixture_per_residential_typology():
    records = _records()
    plans = [rectangular_tabula_box(records[archetype_id]) for archetype_id in S0_ARCHETYPE_IDS]
    assert {records[plan.archetype_id]["building_type"] for plan in plans} == {"SFH", "TH", "MFH", "AB"}
    for plan in plans:
        record = records[plan.archetype_id]
        geometry = record["geometry"]
        assert plan.plate_area_m2 * plan.storeys == pytest.approx(geometry["a_c_ref_m2"])
        assert plan.conditioned_volume_m3 == pytest.approx(geometry["v_c_m3"])
        assert plan.perimeter_m * plan.height_m * geometry["n_storey_effective_envelope"] == pytest.approx(
            plan.exposed_wall_area_m2
        )


def test_infeasible_box_is_rejected_instead_of_altering_tabula_areas():
    records = _records()
    with pytest.raises(ValueError, match="BOX_GEOMETRY_INFEASIBLE"):
        rectangular_tabula_box(records["ES.ME.TH.01.Gen.ReEx.001.001"])


def _vertices(surface):
    return [
        (
            float(getattr(surface, f"Vertex_{number}_Xcoordinate")),
            float(getattr(surface, f"Vertex_{number}_Ycoordinate")),
            float(getattr(surface, f"Vertex_{number}_Zcoordinate")),
        )
        for number in range(1, int(surface.Number_of_Vertices) + 1)
    ]


def _quadrilateral_area(surface) -> float:
    """Return the area of the planar rectangles emitted by the S0 adapter."""
    points = _vertices(surface)
    assert len(points) == 4
    first, second, third = points[:3]
    left = tuple(second[index] - first[index] for index in range(3))
    right = tuple(third[index] - first[index] for index in range(3))
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return math.sqrt(sum(value * value for value in cross))


def _construction_u(saved, construction_name: str) -> float:
    construction = saved.getobject("CONSTRUCTION", construction_name)
    material_name = construction.Outside_Layer
    material = saved.getobject("MATERIAL:NOMASS", material_name)
    if material is not None:
        return 1.0 / float(material.Thermal_Resistance)
    glazing = saved.getobject("WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", material_name)
    assert glazing is not None
    return float(glazing.UFactor)


def _surface_b_factor(saved, surface) -> float:
    if surface.Outside_Boundary_Condition == "Outdoors":
        return 1.0
    coefficients = saved.getobject(
        "SURFACEPROPERTY:OTHERSIDECOEFFICIENTS", surface.Outside_Boundary_Condition_Object
    )
    return float(coefficients.External_DryBulb_Temperature_Coefficient)


def test_s0_equivalent_envelope_saved_readback_preserves_each_fixture_h_transmission(tmp_path):
    """Read saved component surfaces, not cached workbook totals, for S0 R1."""
    records = _records()
    for archetype_id in S0_ARCHETYPE_IDS:
        record = records[archetype_id]
        path = tmp_path / f"{record['building_type']}.idf"
        path.write_text("Version,23.1;\nZone,EU Zone;\n", encoding="utf-8")
        idf = IDF(str(path))
        emitted = add_s0_equivalent_envelope(idf, record, "EU Zone")
        controls = add_european_heating_controls(idf, record, "EU Zone")
        saved_path = tmp_path / f"{record['building_type']}_saved.idf"
        idf.saveas(str(saved_path))
        saved = IDF(str(saved_path))

        zone = saved.getobject("ZONE", "EU Zone")
        assert float(zone.Volume) == pytest.approx(record["geometry"]["v_c_m3"])
        assert float(zone.Floor_Area) == pytest.approx(record["geometry"]["a_c_ref_m2"])
        assert len(emitted.surface_names) == len(saved.idfobjects["BUILDINGSURFACE:DETAILED"])
        ventilation = saved.getobject("ZONEVENTILATION:DESIGNFLOWRATE", controls["ventilation"])
        ideal_loads = saved.getobject("HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM", "EU Zone")
        assert float(ventilation.Air_Changes_per_Hour) == pytest.approx(controls["air_changes_per_hour"])
        assert ideal_loads.Cooling_Availability_Schedule_Name == controls["cooling_off"]

        opening_area_by_parent: dict[str, float] = {}
        for opening in saved.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
            opening_area_by_parent.setdefault(opening.Building_Surface_Name, 0.0)
            opening_area_by_parent[opening.Building_Surface_Name] += _quadrilateral_area(opening)

        model_h_w_k = 0.0
        for surface in saved.idfobjects["BUILDINGSURFACE:DETAILED"]:
            net_area = _quadrilateral_area(surface) - opening_area_by_parent.get(surface.Name, 0.0)
            model_h_w_k += _construction_u(saved, surface.Construction_Name) * _surface_b_factor(saved, surface) * net_area
        for opening in saved.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
            host = saved.getobject("BUILDINGSURFACE:DETAILED", opening.Building_Surface_Name)
            model_h_w_k += _construction_u(saved, opening.Construction_Name) * _surface_b_factor(saved, host) * _quadrilateral_area(opening)

        assert model_h_w_k / record["geometry"]["a_c_ref_m2"] == pytest.approx(
            # IDF vertex coordinates are serialized to a finite decimal
            # precision; this remains orders of magnitude tighter than the
            # D-EU-01 two-percent readback gate.
            record["h_transmission_w_m2k"] * record["f_red_temp"], abs=1e-7
        )
        assert emitted.reduced_h_transmission_w_m2k == pytest.approx(
            record["h_transmission_w_m2k"] * record["f_red_temp"]
        )
        assert emitted.source_area_m2 == pytest.approx(
            sum(record["geometry"]["a_floor_components_m2"])
            + sum(record["geometry"]["a_roof_components_m2"])
            + sum(record["geometry"]["a_wall_components_m2"])
            + sum(record["geometry"]["a_window_components_m2"])
            + record["geometry"]["a_door_m2"]
        )


def test_v8d_saved_idf_geometry_audit_reads_each_s0_archetype_own_file(tmp_path):
    """V8.d catches an IDF swap instead of reusing another plan's geometry."""
    records = _records()
    saved_idfs: dict[str, Path] = {}
    expected_geometry: dict[str, dict[str, object]] = {}
    for archetype_id in S0_ARCHETYPE_IDS:
        record = records[archetype_id]
        path = tmp_path / "{}.idf".format(record["building_type"])
        path.write_text("Version,23.1;\nZone,EU Zone;\n", encoding="utf-8")
        idf = IDF(str(path))
        add_s0_equivalent_envelope(idf, record, "EU Zone")
        saved_path = tmp_path / "{}_saved.idf".format(record["building_type"])
        idf.saveas(str(saved_path))
        saved_idfs[archetype_id] = saved_path
        geometry = record["geometry"]
        expected_geometry[archetype_id] = {
            "floor_area_m2": geometry["a_c_ref_m2"],
            "volume_m3": geometry["v_c_m3"],
            "storey_count": geometry["n_storey"],
        }

    clean = audit_saved_idf_geometries(saved_idfs, expected_geometry)
    assert all(audit.passed for audit in clean)

    swapped = dict(saved_idfs)
    first, second = S0_ARCHETYPE_IDS[:2]
    swapped[first] = saved_idfs[second]
    with pytest.raises(ValueError, match="distinct saved IDF path|does not identify archetype"):
        audit_saved_idf_geometries(swapped, expected_geometry)


@pytest.mark.skipif(not _ENERGYPLUS.exists(), reason="EnergyPlus 23.1 executable is not installed")
@pytest.mark.parametrize("archetype_id", S0_ARCHETYPE_IDS)
def test_s0_equivalent_envelope_heating_only_energyplus_smoke(tmp_path, archetype_id):
    """Every S0 typology's equivalent mesh is a runnable heating-only fixture."""
    record = _records()[archetype_id]
    path = tmp_path / "s0_fixture.idf"
    path.write_text(
        """Version,23.1;
Timestep,4;
Building,EU S0 Smoke,0,Suburbs,0.0001,0.000001,MinimalShadowing,30,1;
GlobalGeometryRules,UpperLeftCorner,CounterClockWise,World;
HeatBalanceAlgorithm,ConductionTransferFunction,200,0.1,10000000;
SimulationControl,No,No,No,Yes,No,No,1;
Site:Location,EU Site,40,-75,-5,0;
SizingPeriod:DesignDay,EU Cold Day,1,21,WinterDesignDay,0,0,,,Wetbulb,0,,,,,101325,0,0,No,No,No,ASHRAEClearSky,,,,0;
ScheduleTypeLimits,Any Number;
Zone,EU Zone;
Output:Variable,*,Zone Ideal Loads Zone Sensible Heating Rate,Timestep;
""",
        encoding="utf-8",
    )
    idf = IDF(str(path))
    add_s0_equivalent_envelope(idf, record, "EU Zone")
    add_european_heating_controls(idf, record, "EU Zone")
    idf.saveas(str(path))
    result = subprocess.run(
        [str(_ENERGYPLUS), "-x", "-r", "-d", str(tmp_path), str(path)],
        cwd=tmp_path, capture_output=True, text=True, timeout=90,
    )
    errors = (tmp_path / "eplusout.err").read_text(errors="replace")
    assert result.returncode == 0, errors
    assert "Completed Successfully" in errors
    assert "** Severe  **" not in errors, errors
