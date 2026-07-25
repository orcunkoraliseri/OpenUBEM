"""Unit tests for envelope_patcher.py (plan T16 -- un-defers T11: cross-CZ
envelope patching for layout_assign baselines)."""

from pathlib import Path

import pandas as pd
import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.geometry import envelope_patcher

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


def _build_baseline_fixture():
    """Tiny 'baseline'-shaped IDF: one zone with wall/roof/floor surfaces + windows,
    carrying an initial Buffalo-style construction/material that patch_envelope()
    is expected to overwrite (surface count/vertex coords must stay untouched)."""
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
        UFactor=3.2, Solar_Heat_Gain_Coefficient=0.6, Visible_Transmittance=0.6,
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


def _construction_thermal_resistance(idf, construction_name):
    cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == construction_name)
    mat = next(m for m in idf.idfobjects["MATERIAL:NOMASS"] if m.Name == cons.Outside_Layer)
    return float(mat.Thermal_Resistance)


def test_patch_envelope_preserves_surface_count_and_vertices():
    idf = _build_baseline_fixture()
    n_surfaces_before = len(idf.idfobjects["BUILDINGSURFACE:DETAILED"])
    n_fen_before = len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"])
    coords_before = {s.Name: list(s.coords) for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]}
    fen_coords_before = {f.Name: list(f.coords) for f in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]}

    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    assert len(idf.idfobjects["BUILDINGSURFACE:DETAILED"]) == n_surfaces_before
    assert len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]) == n_fen_before
    for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        assert list(s.coords) == coords_before[s.Name]
    for f in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
        assert list(f.coords) == fen_coords_before[f.Name]


def test_patch_envelope_wall_construction_matches_row_u_value():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    walls = [s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall"]
    assert walls, "no wall surfaces found"
    for w in walls:
        assert w.Construction_Name == "LA_Wall_Construction"
    r_val = _construction_thermal_resistance(idf, "LA_Wall_Construction")
    expected_r = 1.0 / row["u_wall_w_m2k"]
    assert abs(r_val - expected_r) / expected_r < 0.001


def test_patch_envelope_roof_and_floor_construction_match_row_u_values():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    roofs = [s for s in idf.getsurfaces() if s.Surface_Type.lower() == "roof"]
    floors = [s for s in idf.getsurfaces() if s.Surface_Type.lower() == "floor"]
    assert roofs and floors
    for r in roofs:
        assert r.Construction_Name == "LA_Roof_Construction"
    for f in floors:
        assert f.Construction_Name == "LA_Floor_Construction"

    r_roof = _construction_thermal_resistance(idf, "LA_Roof_Construction")
    r_floor = _construction_thermal_resistance(idf, "LA_Floor_Construction")
    assert abs(r_roof - 1.0 / row["u_roof_w_m2k"]) / (1.0 / row["u_roof_w_m2k"]) < 0.001
    assert abs(r_floor - 1.0 / row["u_floor_w_m2k"]) / (1.0 / row["u_floor_w_m2k"]) < 0.001


def test_patch_envelope_window_construction_matches_row_ufactor_and_shgc():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert len(fen) > 0
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"

    cons = next(c for c in idf.idfobjects["CONSTRUCTION"] if c.Name == "LA_Window_Construction")
    mat = next(
        m for m in idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"] if m.Name == cons.Outside_Layer
    )
    assert float(mat.UFactor) == pytest.approx(row["u_window_w_m2k"])
    assert float(mat.Solar_Heat_Gain_Coefficient) == pytest.approx(row["shgc_window"])


def test_patch_envelope_never_calls_set_wwr_or_changes_wwr_derived_fenestration_count():
    """No new/removed fenestration objects -- only Construction_Name reassignment."""
    idf = _build_baseline_fixture()
    n_fen_before = len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"])
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)
    assert len(idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]) == n_fen_before


@pytest.mark.parametrize("missing_col", list(envelope_patcher._ENVELOPE_COLS))
def test_patch_envelope_raises_on_null_envelope_column(missing_col):
    idf = _build_baseline_fixture()
    row = _make_row()
    row[missing_col] = float("nan")
    with pytest.raises(ValueError, match=missing_col):
        envelope_patcher.patch_envelope(idf, row)


def test_patch_envelope_skips_ground_fcfactor_surfaces():
    """Real-baseline finding (MediumOffice, see T16 progress log): ground-contact
    floors/basement walls modeled via Construction:FfactorGroundFloor /
    Construction:CfactorUndergroundWall (Outside_Boundary_Condition=
    "GroundFCfactorMethod") cannot take a plain layered Construction -- EnergyPlus
    fatals. patch_envelope() must leave these surfaces on their native construction."""
    idf = _build_baseline_fixture()
    ground_floor = next(s for s in idf.getsurfaces() if s.Surface_Type.lower() == "floor")
    idf.newidfobject(
        "CONSTRUCTION:FFACTORGROUNDFLOOR", Name="Ground_Ffactor",
        FFactor=0.9, Area=100.0, PerimeterExposed=40.0,
    )
    ground_floor.Outside_Boundary_Condition = "GroundFCfactorMethod"
    ground_floor.Construction_Name = "Ground_Ffactor"

    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    assert ground_floor.Construction_Name == "Ground_Ffactor"
    # every other (non-ground-contact) surface still gets patched normally
    walls = [s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall"]
    assert all(w.Construction_Name == "LA_Wall_Construction" for w in walls)


def test_patch_envelope_skips_door_fenestration_but_patches_glassdoor():
    """Real-baseline finding (SmallOffice/RetailStripmall, see T16 progress log):
    FenestrationSurface:Detailed Surface_Type="Door" (opaque) cannot take a
    WindowMaterial:SimpleGlazingSystem-based construction -- EnergyPlus fatals.
    Surface_Type="GlassDoor" is glazed and safe to repoint like a Window."""
    idf = _build_baseline_fixture()
    wall = next(s for s in idf.getsurfaces() if s.Surface_Type.lower() == "wall")
    door = idf.newidfobject(
        "FENESTRATIONSURFACE:DETAILED", Name="TestDoor", Surface_Type="Door",
        Construction_Name="Buffalo_Wall_Construction", Building_Surface_Name=wall.Name,
        View_Factor_to_Ground=0.5, Number_of_Vertices=4,
    )
    door.setcoords([(1, 0, 0), (2, 0, 0), (2, 0, 2), (1, 0, 2)])
    glassdoor = idf.newidfobject(
        "FENESTRATIONSURFACE:DETAILED", Name="TestGlassDoor", Surface_Type="GlassDoor",
        Construction_Name="Buffalo_Window_Construction", Building_Surface_Name=wall.Name,
        View_Factor_to_Ground=0.5, Number_of_Vertices=4,
    )
    glassdoor.setcoords([(3, 0, 0), (4, 0, 0), (4, 0, 2), (3, 0, 2)])

    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    assert door.Construction_Name == "Buffalo_Wall_Construction"  # untouched
    assert glassdoor.Construction_Name == "LA_Window_Construction"  # repointed


def test_patch_envelope_thermal_mass_uses_material_not_nomass():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, thermal_mass=True)

    mass_names = {m.Name for m in idf.idfobjects["MATERIAL"]}
    assert {"LA_Wall_Assembly", "LA_Roof_Assembly", "LA_Floor_Assembly"} <= mass_names
    nomass_names = {m.Name for m in idf.idfobjects["MATERIAL:NOMASS"]}
    assert "LA_Wall_Assembly" not in nomass_names
