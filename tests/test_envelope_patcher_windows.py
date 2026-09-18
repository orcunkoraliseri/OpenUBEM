"""Unit tests for envelope_patcher.py's B03 additions (plan
docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block1-2026-09-17.md):
the `skip_when_better` clamp on `patch_envelope`, and the fail-loud orphaned/
mismatched WindowShadingControl check."""

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


def test_skip_when_better_off_matches_current_unconditional_overwrite():
    idf = _build_baseline_fixture(window_ufactor=1.0, window_shgc=0.1)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=False)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert fen, "no fenestration objects found"
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"


def test_skip_when_better_on_keeps_native_window_when_better_on_both():
    idf = _build_baseline_fixture(window_ufactor=1.0, window_shgc=0.1)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=True)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert fen, "no fenestration objects found"
    for f in fen:
        assert f.Construction_Name == "Buffalo_Window_Construction"


def test_skip_when_better_on_installs_archetype_when_native_worse_on_ufactor():
    idf = _build_baseline_fixture(window_ufactor=3.2, window_shgc=0.1)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=True)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert fen, "no fenestration objects found"
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"


def test_skip_when_better_on_installs_archetype_when_native_worse_on_shgc():
    idf = _build_baseline_fixture(window_ufactor=1.0, window_shgc=0.6)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=True)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert fen, "no fenestration objects found"
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"


def test_skip_when_better_on_installs_archetype_when_native_worse_on_both():
    idf = _build_baseline_fixture(window_ufactor=3.2, window_shgc=0.6)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row, skip_when_better=True)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    assert fen, "no fenestration objects found"
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"


def test_skip_when_better_default_is_false():
    idf = _build_baseline_fixture(window_ufactor=1.0, window_shgc=0.1)
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)

    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
    for f in fen:
        assert f.Construction_Name == "LA_Window_Construction"


def test_orphaned_shading_control_raises():
    idf = _build_baseline_fixture()
    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0]
    idf.newidfobject(
        "WINDOWSHADINGCONTROL",
        Name="TestShadingControl",
        Shading_Type="SwitchableGlazing",
        Construction_with_Shading_Name="Nonexistent_Shaded_Construction",
        Multiple_Surface_Control_Type="Sequential",
        Fenestration_Surface_1_Name=fen.Name,
    )
    row = _make_row()
    with pytest.raises(ValueError, match="does not exist"):
        envelope_patcher.patch_envelope(idf, row)


def test_shading_control_on_patched_window_raises_mismatch():
    idf = _build_baseline_fixture()
    fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0]
    idf.newidfobject(
        "CONSTRUCTION",
        Name="Buffalo_Window_Construction_Shaded",
        Outside_Layer="Buffalo_Window_Material",
    )
    idf.newidfobject(
        "WINDOWSHADINGCONTROL",
        Name="TestShadingControl",
        Shading_Type="SwitchableGlazing",
        Construction_with_Shading_Name="Buffalo_Window_Construction_Shaded",
        Multiple_Surface_Control_Type="Sequential",
        Fenestration_Surface_1_Name=fen.Name,
    )
    row = _make_row()
    with pytest.raises(ValueError, match="no longer matches"):
        envelope_patcher.patch_envelope(idf, row)


def test_no_shading_controls_never_raises():
    idf = _build_baseline_fixture()
    row = _make_row()
    envelope_patcher.patch_envelope(idf, row)
