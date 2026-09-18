"""Unit tests for compliance.py (TechTransfer block 3, T4, Lane G, G01)."""

from pathlib import Path

import pandas as pd
import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.geometry import envelope_patcher
from openubem.idf import compliance

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass


def _blank_template_path():
    return Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"


def _make_row(**overrides):
    base = {
        "archetype_id": "MediumOffice",
        "u_roof_w_m2k": 0.15,
        "u_wall_w_m2k": 0.25,
        "u_floor_w_m2k": 0.35,
        "u_window_w_m2k": 1.8,
        "shgc_window": 0.32,
    }
    base.update(overrides)
    return pd.Series(base)


def _build_baseline_fixture(window_ufactor=3.2, window_shgc=0.6):
    idf = GeomIDF(str(_blank_template_path()))
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Wall_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.5, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Wall_Construction", Outside_Layer="Buffalo_Wall_Assembly")
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Roof_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.2, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Roof_Construction", Outside_Layer="Buffalo_Roof_Assembly")
    idf.newidfobject(
        "MATERIAL:NOMASS", Name="Buffalo_Floor_Assembly", Roughness="MediumRough",
        Thermal_Resistance=1.0 / 0.3, Thermal_Absorptance=0.9, Solar_Absorptance=0.7,
        Visible_Absorptance=0.7,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Floor_Construction", Outside_Layer="Buffalo_Floor_Assembly")
    idf.newidfobject(
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", Name="Buffalo_Window_Material",
        UFactor=window_ufactor, Solar_Heat_Gain_Coefficient=window_shgc, Visible_Transmittance=0.6,
    )
    idf.newidfobject("CONSTRUCTION", Name="Buffalo_Window_Construction", Outside_Layer="Buffalo_Window_Material")

    idf.add_block(name="Baseline", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    idf.set_wwr(wwr=0.3, construction="Buffalo_Window_Construction", force=True)

    _map = {
        "wall": "Buffalo_Wall_Construction", "roof": "Buffalo_Roof_Construction",
        "floor": "Buffalo_Floor_Construction", "ceiling": "Buffalo_Floor_Construction",
    }
    for surf in idf.getsurfaces():
        c = _map.get(surf.Surface_Type.lower())
        if c:
            surf.Construction_Name = c
    return idf


def test_freshly_patched_idf_audits_pass():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "pass"
    assert result["failures"] == []


def test_repointed_wall_surface_yields_incomplete_failure():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    wall = next(s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall")
    wall.Construction_Name = "Buffalo_Wall_Construction"

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "fail"
    incomplete = [f for f in result["failures"] if f["reason"] == "ENVELOPE_PATCH_INCOMPLETE"]
    assert len(incomplete) == 1
    assert incomplete[0]["count"] == 1


def test_large_window_ufactor_perturbation_yields_mismatch():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    window_material = next(
        m for m in idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"] if m.Name == "LA_Window_Material"
    )
    window_material.UFactor = float(window_material.UFactor) + 0.5

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "fail"
    reasons = [f["reason"] for f in result["failures"]]
    assert "WINDOW_PROPERTY_MISMATCH" in reasons


def test_small_window_ufactor_perturbation_does_not_yield_mismatch():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    window_material = next(
        m for m in idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"] if m.Name == "LA_Window_Material"
    )
    window_material.UFactor = float(window_material.UFactor) + 0.001

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "pass"
    reasons = [f["reason"] for f in result["failures"]]
    assert "WINDOW_PROPERTY_MISMATCH" not in reasons


def test_ground_boundary_surfaces_are_informational_only():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    wall = next(s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall")
    wall.Outside_Boundary_Condition = "GroundFCfactorMethod"

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "pass"
    assert result["info"]["GROUND_SURFACE_UNPATCHED"]["count"] == 1
    assert all(f["reason"] != "ENVELOPE_PATCH_INCOMPLETE" for f in result["failures"])


def test_opaque_door_fenestration_never_flagged():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    existing_fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0]
    door = idf.copyidfobject(existing_fen)
    door.Name = "Test_Door"
    door.Surface_Type = "Door"
    door.Construction_Name = "Buffalo_Wall_Construction"

    result = compliance.audit_envelope_compliance(idf, row)

    assert result["status"] == "pass"
    assert result["info"]["GLAZING_UNPATCHED"]["count"] == 0
    assert all(f["reason"] != "GLAZING_UNPATCHED" for f in result["failures"])


def test_skip_when_better_makes_unpatched_glazing_informational():
    idf = _build_baseline_fixture(window_ufactor=1.0, window_shgc=0.1)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=True)

    result = compliance.audit_envelope_compliance(idf, row, skip_when_better=True)

    assert result["status"] == "pass"
    assert result["info"]["GLAZING_UNPATCHED"]["count"] > 0
    assert result["info"]["GLAZING_UNPATCHED"]["skip_when_better"] is True
    assert all(f["reason"] != "GLAZING_UNPATCHED" for f in result["failures"])
