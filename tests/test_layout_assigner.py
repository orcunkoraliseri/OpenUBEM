"""Unit tests for layout_assigner module and zoning integration (LayoutAssigner arc T01-T05)."""

import importlib
import logging
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
import shapely.geometry
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.geometry import layout_assigner, zoning
from openubem.idf.builder import BuildingIDF
from openubem.semantic import _ARCHETYPE_VOCAB

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_UNMAPPED_VOCAB = {"Courthouse", "OpenUBEMUnknown"}
_MAPPED_VOCAB = [a for a in _ARCHETYPE_VOCAB if a not in _UNMAPPED_VOCAB]

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SYNTHETIC_EPW = FIXTURES_DIR / "synthetic.epw"


def _blank_template_path():
    from pathlib import Path
    return Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"


def _build_two_zone_fixture():
    """2-zone synthetic IDF: one absolute-level Lights zone, one Watts/Area Lights zone,
    plus a Flow/Zone infiltration object on the absolute zone (T04 fixture)."""
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="Abs", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.add_block(name="Area", coordinates=[(100, 0), (110, 0), (110, 10), (100, 10)], height=3.0, num_stories=1)

    zone_names = [z.Name for z in idf.idfobjects["ZONE"]]
    zone_abs, zone_area = zone_names[0], zone_names[1]

    idf.newidfobject("SCHEDULE:CONSTANT", Name="AlwaysOn", Hourly_Value=1.0)
    lights_abs = idf.newidfobject(
        "LIGHTS", Name="LightsAbs", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_abs,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="LightingLevel",
        Lighting_Level=1000.0,
    )
    lights_area = idf.newidfobject(
        "LIGHTS", Name="LightsArea", Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_area,
        Schedule_Name="AlwaysOn", Design_Level_Calculation_Method="Watts/Area",
        Watts_per_Zone_Floor_Area=10.0,
    )
    infil = idf.newidfobject(
        "ZONEINFILTRATION:DESIGNFLOWRATE", Name="Infil1",
        Zone_or_ZoneList_or_Space_or_SpaceList_Name=zone_abs,
        Schedule_Name="AlwaysOn", Design_Flow_Rate_Calculation_Method="Flow/Zone",
        Design_Flow_Rate=0.05,
    )
    return idf, zone_abs, zone_area, lights_abs, lights_area, infil


# T09: legacy (pre-arc) tests below depend on the real external baseline library
# resolving MidriseApartment/Hospital/LargeHotel to real files -> skipif-guarded
# consistent with every other real-library test in this file (minimal-diff choice
# explicitly authorized by the plan's T09 "How" text).
@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_registry_indexing():
    reg = layout_assigner.BaselineIDFRegistry()
    assert reg.base_dir.exists()

    midrise = reg.get_baseline_idf("MidriseApartment")
    assert midrise is not None
    assert "ApartmentMidRise" in midrise.name

    hospital = reg.get_baseline_idf("Hospital")
    assert hospital is not None
    assert "Hospital" in hospital.name

    hotel = reg.get_baseline_idf("LargeHotel")
    assert hotel is not None
    assert "HotelLarge" in hotel.name


def test_scaling_factor_calculation():
    real_area = 5000.0
    baseline_area = 2500.0

    scaling = layout_assigner.calculate_scaling_factor(real_area, baseline_area)
    assert pytest.approx(scaling["area_scale_ratio"], 0.001) == 2.0
    assert pytest.approx(scaling["planar_scale_factor"], 0.001) == 1.4142  # sqrt(2)
    assert scaling["target_area_m2"] == real_area
    assert scaling["baseline_area_m2"] == baseline_area


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_assign_baseline_layout():
    poly = shapely.geometry.box(0, 0, 20, 25)  # 500 m2 footprint
    num_floors = 4
    real_area = 500 * 4  # 2000 m2

    meta = layout_assigner.assign_baseline_layout("osm_12345", poly, "MidriseApartment", num_floors)

    assert meta["osm_id"] == "osm_12345"
    assert meta["archetype_id"] == "MidriseApartment"
    assert meta["mode"] == "layout_assign"
    assert meta["no_baseline"] is False
    assert meta["target_floor_area_m2"] == real_area
    assert meta["area_scale_ratio"] > 0
    assert meta["planar_scale_factor"] > 0


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_zoning_integration():
    strategy = zoning.decide_zoning_strategy("Hospital", 1200.0, 5, resolution_mode="layout_assign")
    assert strategy == "layout_assign"

    poly = shapely.geometry.box(0, 0, 30, 40)
    zones = zoning.build_zones("osm_hospital_01", poly, "Hospital", 5, strategy=strategy)
    assert len(zones) == 1
    assert zones[0]["mode"] == "layout_assign"
    assert zones[0]["archetype_id"] == "Hospital"
    assert zones[0]["target_floor_area_m2"] == 30 * 40 * 5


# ── T01 — Registry portability + lazy init ──────────────────────────────────

def test_lazy_registry_no_scan_at_import(monkeypatch, caplog, tmp_path):
    missing_dir = tmp_path / "does_not_exist_baseline_lib"
    monkeypatch.setattr(config, "BASELINE_IDF_DIR", missing_dir)
    try:
        caplog.clear()
        with caplog.at_level(logging.WARNING):
            importlib.reload(layout_assigner)
        la_records = [r for r in caplog.records if r.name == "openubem.geometry.layout_assigner"]
        assert not any("does not exist" in r.message for r in la_records)
        assert layout_assigner._registry is None

        caplog.clear()
        with caplog.at_level(logging.WARNING):
            reg = layout_assigner.get_registry()
        la_records = [r for r in caplog.records if r.name == "openubem.geometry.layout_assigner"]
        assert any("does not exist" in r.message for r in la_records)
        assert reg.base_dir == missing_dir
    finally:
        layout_assigner._registry = None
        importlib.reload(layout_assigner)  # restore module state against the real (reverted) dir


# ── T02 — canonical-vocabulary re-keying ─────────────────────────────────────

@pytest.mark.parametrize("archetype_id", _MAPPED_VOCAB)
def test_vocab_has_filename_and_area_mapping(archetype_id):
    assert archetype_id in layout_assigner.ARCHETYPE_IDF_MAP
    assert layout_assigner.DEFAULT_BASELINE_AREAS.get(archetype_id) is not None
    assert layout_assigner.DEFAULT_BASELINE_AREAS[archetype_id] != 3000.0


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
@pytest.mark.parametrize("archetype_id", _MAPPED_VOCAB)
def test_vocab_resolves_to_real_file(archetype_id):
    reg = layout_assigner.BaselineIDFRegistry()
    path = reg.get_baseline_idf(archetype_id)
    assert path is not None, f"{archetype_id} did not resolve to a real baseline file"
    assert path.exists()


def test_removed_aliases_are_gone():
    for alias in ("HotelLarge", "OfficeLarge", "OfficeMedium", "OfficeSmall", "HotelSmall",
                  "StandaloneRetail", "StripMall", "FastFood", "SitDown", "DataCenter",
                  "OutPatient", "Supermarket", "DetachedHouse", "AttachedHouse"):
        assert alias not in layout_assigner.ARCHETYPE_IDF_MAP
        assert alias not in layout_assigner.DEFAULT_BASELINE_AREAS


def test_no_partial_match_fallback():
    reg = layout_assigner.BaselineIDFRegistry()
    # "Office" is a substring of several cached filenames but is not itself a vocab
    # token / dict key -> must resolve to None, never a fuzzy substring match.
    assert reg.get_baseline_idf("Office") is None


# ── T03 — graceful no-baseline fallback ──────────────────────────────────────

@pytest.mark.parametrize("archetype_id", sorted(_UNMAPPED_VOCAB))
def test_unmapped_archetypes_return_none(archetype_id):
    reg = layout_assigner.get_registry()
    assert reg.get_baseline_idf(archetype_id) is None
    assert reg.get_baseline_area(archetype_id) is None


def test_assign_baseline_layout_no_baseline_never_crashes():
    poly = shapely.geometry.box(0, 0, 20, 20)  # 400 m2
    meta = layout_assigner.assign_baseline_layout("osm_ch1", poly, "Courthouse", 3)
    assert meta["no_baseline"] is True
    assert meta["baseline_idf_filename"] is None
    assert meta["baseline_idf_path"] is None
    assert meta["area_scale_ratio"] is None
    assert meta["planar_scale_factor"] is None
    assert meta["target_floor_area_m2"] == 400.0 * 3
    assert meta["archetype_id"] == "Courthouse"


def test_zoning_layout_assign_courthouse_never_crashes():
    poly = shapely.geometry.box(0, 0, 20, 20)
    strategy = zoning.decide_zoning_strategy("Courthouse", 400.0, 3, resolution_mode="layout_assign")
    zones = zoning.build_zones("osm_ch2", poly, "Courthouse", 3, strategy=strategy)
    assert len(zones) == 1
    assert zones[0]["no_baseline"] is True


# ── T04 — scale_baseline_idf() ───────────────────────────────────────────────

def test_scale_baseline_idf_vertices_and_absolute_loads():
    idf, zone_abs, zone_area, lights_abs, lights_area, infil = _build_two_zone_fixture()

    floor_before = {
        s.Zone_Name: s.area
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if s.Surface_Type.upper() == "FLOOR"
    }
    coords_before = list(idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords)
    lights_area_snapshot_before = {f: getattr(lights_area, f) for f in lights_area.fieldnames}

    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    # Vertices scale by sqrt(S).
    coords_after = list(idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords)
    k = scale["planar_scale_factor"]
    for (x0, y0, z0), (x1, y1, z1) in zip(coords_before, coords_after):
        assert x1 == pytest.approx(x0 * k)
        assert y1 == pytest.approx(y0 * k)
        assert z1 == pytest.approx(z0)  # Z unchanged

    # Floor area scales by S (within 1%).
    floor_after = {
        s.Zone_Name: s.area
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if s.Surface_Type.upper() == "FLOOR"
    }
    for zname, area0 in floor_before.items():
        assert floor_after[zname] == pytest.approx(area0 * scale["area_scale_ratio"], rel=0.01)

    # Absolute Lights level scales by S exactly.
    assert lights_abs.Lighting_Level == pytest.approx(1000.0 * scale["area_scale_ratio"])

    # Watts/Area Lights object is byte-identical after scaling.
    lights_area_snapshot_after = {f: getattr(lights_area, f) for f in lights_area.fieldnames}
    assert lights_area_snapshot_after == lights_area_snapshot_before

    # Flow/Zone infiltration scales by S exactly.
    assert infil.Design_Flow_Rate == pytest.approx(0.05 * scale["area_scale_ratio"])


def test_scale_baseline_idf_skips_blank_and_autosize_fields():
    idf, zone_abs, zone_area, lights_abs, lights_area, infil = _build_two_zone_fixture()
    oa = idf.newidfobject(
        "DESIGNSPECIFICATION:OUTDOORAIR", Name="OA1",
        Outdoor_Air_Method="Flow/Zone", Outdoor_Air_Flow_per_Zone="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert oa.Outdoor_Air_Flow_per_Zone == "autosize"
    # Watts/Area Lighting_Level field stays blank, never coerced/multiplied.
    assert lights_area.Lighting_Level == ""


# ── T15 — E-LA-06 fixed-capacity auxiliary equipment scaling ────────────────

def test_scale_baseline_idf_scales_transformer_and_waterheater_fields():
    idf, *_ = _build_two_zone_fixture()
    transformer = idf.newidfobject(
        "ELECTRICLOADCENTER:TRANSFORMER", Name="Transformer 1", Rated_Capacity=45000.0,
    )
    water_heater = idf.newidfobject(
        "WATERHEATER:MIXED", Name="WH1", Tank_Volume=0.378541, Heater_Maximum_Capacity=29307.1,
        Peak_Use_Flow_Rate=0.0000631,
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    assert transformer.Rated_Capacity == pytest.approx(45000.0 * scale["area_scale_ratio"])
    assert water_heater.Tank_Volume == pytest.approx(0.378541 * scale["area_scale_ratio"])
    assert water_heater.Heater_Maximum_Capacity == pytest.approx(29307.1 * scale["area_scale_ratio"])
    # E-LA-10: Peak_Use_Flow_Rate must now scale like the other absolute DHW fields.
    assert water_heater.Peak_Use_Flow_Rate == pytest.approx(0.0000631 * scale["area_scale_ratio"])


# ── T02 audit — WaterHeater:Mixed parasitic/loss-coefficient DHW fields ─────

def test_scale_baseline_idf_scales_waterheater_parasitic_and_loss_coefficient_fields():
    idf, *_ = _build_two_zone_fixture()
    water_heater = idf.newidfobject(
        "WATERHEATER:MIXED", Name="WH1",
        Off_Cycle_Parasitic_Fuel_Consumption_Rate=87.0,
        On_Cycle_Parasitic_Fuel_Consumption_Rate=87.0,
        Off_Cycle_Loss_Coefficient_to_Ambient_Temperature=2.01255976571014,
        On_Cycle_Loss_Coefficient_to_Ambient_Temperature=2.01255976571014,
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    s = scale["area_scale_ratio"]
    assert water_heater.Off_Cycle_Parasitic_Fuel_Consumption_Rate == pytest.approx(87.0 * s)
    assert water_heater.On_Cycle_Parasitic_Fuel_Consumption_Rate == pytest.approx(87.0 * s)
    assert water_heater.Off_Cycle_Loss_Coefficient_to_Ambient_Temperature == pytest.approx(2.01255976571014 * s)
    assert water_heater.On_Cycle_Loss_Coefficient_to_Ambient_Temperature == pytest.approx(2.01255976571014 * s)


def test_scale_baseline_idf_skips_autosize_waterheater_parasitic_and_loss_coefficient_fields():
    idf, *_ = _build_two_zone_fixture()
    water_heater = idf.newidfobject(
        "WATERHEATER:MIXED", Name="WH1",
        Off_Cycle_Parasitic_Fuel_Consumption_Rate="autosize",
        On_Cycle_Parasitic_Fuel_Consumption_Rate="autosize",
        Off_Cycle_Loss_Coefficient_to_Ambient_Temperature="autosize",
        On_Cycle_Loss_Coefficient_to_Ambient_Temperature="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert water_heater.Off_Cycle_Parasitic_Fuel_Consumption_Rate == "autosize"
    assert water_heater.On_Cycle_Parasitic_Fuel_Consumption_Rate == "autosize"
    assert water_heater.Off_Cycle_Loss_Coefficient_to_Ambient_Temperature == "autosize"
    assert water_heater.On_Cycle_Loss_Coefficient_to_Ambient_Temperature == "autosize"


def test_scale_baseline_idf_scales_coil_cooling_dx_multispeed_literal_speeds_only():
    idf, *_ = _build_two_zone_fixture()
    coil = idf.newidfobject(
        "COIL:COOLING:DX:MULTISPEED", Name="MultiSpeed Coil 1",
        Speed_1_Gross_Rated_Total_Cooling_Capacity=14541.685,
        Speed_1_Rated_Air_Flow_Rate=0.963386666666667,
        Speed_2_Gross_Rated_Total_Cooling_Capacity=29083.37,
        Speed_2_Rated_Air_Flow_Rate=1.44508,
        # Speed 3/4 left blank -- must stay untouched, never coerced to 0.0.
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    s = scale["area_scale_ratio"]
    assert coil.Speed_1_Gross_Rated_Total_Cooling_Capacity == pytest.approx(14541.685 * s)
    assert coil.Speed_1_Rated_Air_Flow_Rate == pytest.approx(0.963386666666667 * s)
    assert coil.Speed_2_Gross_Rated_Total_Cooling_Capacity == pytest.approx(29083.37 * s)
    assert coil.Speed_2_Rated_Air_Flow_Rate == pytest.approx(1.44508 * s)
    assert coil.Speed_3_Gross_Rated_Total_Cooling_Capacity == ""
    assert coil.Speed_3_Rated_Air_Flow_Rate == ""
    assert coil.Speed_4_Gross_Rated_Total_Cooling_Capacity == ""
    assert coil.Speed_4_Rated_Air_Flow_Rate == ""


def test_scale_baseline_idf_skips_autosize_transformer_and_waterheater():
    idf, *_ = _build_two_zone_fixture()
    transformer = idf.newidfobject(
        "ELECTRICLOADCENTER:TRANSFORMER", Name="Transformer 1", Rated_Capacity="autosize",
    )
    water_heater = idf.newidfobject(
        "WATERHEATER:MIXED", Name="WH1", Tank_Volume=0.5, Heater_Maximum_Capacity="autosize",
        Peak_Use_Flow_Rate="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert transformer.Rated_Capacity == "autosize"
    assert water_heater.Heater_Maximum_Capacity == "autosize"
    assert water_heater.Tank_Volume == pytest.approx(0.5 * scale["area_scale_ratio"])
    # E-LA-10: autosize Peak_Use_Flow_Rate must be left untouched, same as the other autosize fields.
    assert water_heater.Peak_Use_Flow_Rate == "autosize"


# ── T04 — FluidCooler:TwoSpeed capacity fields (E-LA-07 class 1) ───────────

def test_scale_baseline_idf_scales_fluidcooler_twospeed_capacity_fields():
    idf, *_ = _build_two_zone_fixture()
    cooler = idf.newidfobject(
        "FLUIDCOOLER:TWOSPEED", Name="Central Tower",
        Performance_Input_Method="NominalCapacity",
        High_Speed_Nominal_Capacity=582060.0,
        Low_Speed_Nominal_Capacity=291030.0,
        Design_Water_Flow_Rate="autosize",
        High_Fan_Speed_Air_Flow_Rate="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    s = scale["area_scale_ratio"]
    assert cooler.High_Speed_Nominal_Capacity == pytest.approx(582060.0 * s)
    assert cooler.Low_Speed_Nominal_Capacity == pytest.approx(291030.0 * s)
    # Untouched fields (autosize) stay autosize -- confirmed on the raw LargeOffice
    # baseline these are genuinely still autosize, not exposed to this fix.
    assert cooler.Design_Water_Flow_Rate == "autosize"
    assert cooler.High_Fan_Speed_Air_Flow_Rate == "autosize"


def test_scale_baseline_idf_skips_autosize_fluidcooler_twospeed_capacity_fields():
    idf, *_ = _build_two_zone_fixture()
    cooler = idf.newidfobject(
        "FLUIDCOOLER:TWOSPEED", Name="Central Tower",
        Performance_Input_Method="NominalCapacity",
        High_Speed_Nominal_Capacity="autosize",
        Low_Speed_Nominal_Capacity="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert cooler.High_Speed_Nominal_Capacity == "autosize"
    assert cooler.Low_Speed_Nominal_Capacity == "autosize"


# ── structural-fixes T01 — Daylighting:ReferencePoint scaling (E-LA-12) ─────

def test_scale_baseline_idf_scales_daylighting_refpoint_xy():
    idf, zone_abs, zone_area, *_ = _build_two_zone_fixture()
    rp = idf.newidfobject(
        "DAYLIGHTING:REFERENCEPOINT", Name="RP1", Zone_or_Space_Name=zone_abs,
        XCoordinate_of_Reference_Point=2.0, YCoordinate_of_Reference_Point=3.0,
        ZCoordinate_of_Reference_Point=0.8,
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    k = scale["planar_scale_factor"]
    assert rp.XCoordinate_of_Reference_Point == pytest.approx(2.0 * k)
    assert rp.YCoordinate_of_Reference_Point == pytest.approx(3.0 * k)
    assert rp.ZCoordinate_of_Reference_Point == pytest.approx(0.8)  # Z unchanged


def test_scale_baseline_idf_daylighting_refpoint_stays_relative_to_window_plane():
    """Refpoint scales by the same √S as the surrounding surfaces, so its position
    relative to a scaled window plane is preserved (not left behind at S != 1)."""
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="Room", coordinates=[(0, 0), (10, 0), (10, 10), (0, 10)], height=3.0, num_stories=1)
    idf.intersect_match()
    idf.newidfobject(
        "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM", Name="WinMat",
        UFactor=2.5, Solar_Heat_Gain_Coefficient=0.4, Visible_Transmittance=0.6,
    )
    idf.newidfobject("CONSTRUCTION", Name="WinCons", Outside_Layer="WinMat")
    idf.set_wwr(wwr=0.3, construction="WinCons", force=True)

    zone_name = idf.idfobjects["ZONE"][0].Name
    window = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"][0]
    win_coords_before = list(window.coords)
    win_cx_before = sum(c[0] for c in win_coords_before) / len(win_coords_before)
    win_cy_before = sum(c[1] for c in win_coords_before) / len(win_coords_before)

    rp = idf.newidfobject(
        "DAYLIGHTING:REFERENCEPOINT", Name="RP1", Zone_or_Space_Name=zone_name,
        XCoordinate_of_Reference_Point=win_cx_before, YCoordinate_of_Reference_Point=5.0,
        ZCoordinate_of_Reference_Point=0.8,
    )

    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)
    k = scale["planar_scale_factor"]

    win_coords_after = list(window.coords)
    win_cx_after = sum(c[0] for c in win_coords_after) / len(win_coords_after)

    assert win_cx_after == pytest.approx(win_cx_before * k)
    assert rp.XCoordinate_of_Reference_Point == pytest.approx(win_cx_before * k)
    # Same scale factor keeps the refpoint aligned with the window plane's new position.
    assert rp.XCoordinate_of_Reference_Point == pytest.approx(win_cx_after)
    assert rp.YCoordinate_of_Reference_Point == pytest.approx(5.0 * k)


def test_scale_baseline_idf_daylighting_controls_has_no_coordinate_fields_to_scale():
    """E-LA-12 audit: Daylighting:Controls carries no embedded X/Y/Z fields of its
    own (only reference-point name/fraction/illuminance settings) -- confirms the
    plan's required audit found nothing to add for this class."""
    idf, zone_abs, *_ = _build_two_zone_fixture()
    dc = idf.newidfobject(
        "DAYLIGHTING:CONTROLS", Name="DC1", Zone_or_Space_Name=zone_abs,
        Daylighting_Method="SplitFlux",
        Daylighting_Reference_Point_1_Name="RP1",
        Fraction_of_Lights_Controlled_by_Reference_Point_1=1.0,
        Illuminance_Setpoint_at_Reference_Point_1=300.0,
    )
    fields_before = {f: getattr(dc, f) for f in dc.fieldnames}
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    fields_after = {f: getattr(dc, f) for f in dc.fieldnames}
    assert fields_after == fields_before


# ── structural-fixes T06 — LargeOffice DataCenter WSHP autosize (E-LA-11) ───

def test_scale_baseline_idf_resolves_datacenter_wshp_autosize_by_exact_name():
    """E-LA-11: the 8 named DataCenter WSHP coils resolve from autosize to the
    S=1 raw-baseline literal, scaled by area_scale_ratio."""
    idf, zone_abs, *_ = _build_two_zone_fixture()
    heat = idf.newidfobject(
        "COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT",
        Name="AirLoop DataCenter bot Heating Coil",
        Rated_Air_Flow_Rate="autosize", Rated_Water_Flow_Rate="autosize",
        Gross_Rated_Heating_Capacity="autosize",
    )
    cool = idf.newidfobject(
        "COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT",
        Name="AirLoop DataCenter bot Cooling Coil",
        Rated_Air_Flow_Rate="autosize", Rated_Water_Flow_Rate="autosize",
        Gross_Rated_Total_Cooling_Capacity="autosize",
        Gross_Rated_Sensible_Cooling_Capacity="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)  # S=4
    layout_assigner.scale_baseline_idf(idf, scale)

    s = scale["area_scale_ratio"]
    assert heat.Rated_Air_Flow_Rate == pytest.approx(0.48949 * s)
    assert heat.Rated_Water_Flow_Rate == pytest.approx(2.44640e-4 * s)
    assert heat.Gross_Rated_Heating_Capacity == pytest.approx(9893.94684 * s)
    assert cool.Rated_Air_Flow_Rate == pytest.approx(0.48949 * s)
    assert cool.Rated_Water_Flow_Rate == pytest.approx(2.44640e-4 * s)
    assert cool.Gross_Rated_Total_Cooling_Capacity == pytest.approx(10448.14012 * s)
    assert cool.Gross_Rated_Sensible_Cooling_Capacity == pytest.approx(7110.88362 * s)


def test_scale_baseline_idf_skips_non_autosize_datacenter_wshp_coil():
    """A matching-Name coil that is NOT actually autosize (unexpected) is left
    untouched, same _is_blank_or_autosize guard as every other spec class."""
    idf, *_ = _build_two_zone_fixture()
    heat = idf.newidfobject(
        "COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT",
        Name="AirLoop DataCenter bot Heating Coil",
        Rated_Air_Flow_Rate=1.23, Rated_Water_Flow_Rate=4.56,
        Gross_Rated_Heating_Capacity=789.0,
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert heat.Rated_Air_Flow_Rate == 1.23
    assert heat.Rated_Water_Flow_Rate == 4.56
    assert heat.Gross_Rated_Heating_Capacity == 789.0


def test_scale_baseline_idf_does_not_touch_wshp_coil_with_unmatched_name():
    """Cross-archetype safety (E-LA-11): a Coil:*:WaterToAirHeatPump:EquationFit
    object whose Name is NOT one of the 8 LargeOffice DataCenter coils (e.g. an
    ApartmentHighRise-style per-apartment AirLoop coil) must stay untouched --
    proves the fix is scoped by exact Name, not by IDF class alone."""
    idf, *_ = _build_two_zone_fixture()
    heat = idf.newidfobject(
        "COIL:HEATING:WATERTOAIRHEATPUMP:EQUATIONFIT",
        Name="AirLoop G SW Heating Coil",  # real ApartmentHighRise coil name
        Rated_Air_Flow_Rate="autosize", Rated_Water_Flow_Rate="autosize",
        Gross_Rated_Heating_Capacity="autosize",
    )
    scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
    layout_assigner.scale_baseline_idf(idf, scale)
    assert heat.Rated_Air_Flow_Rate == "autosize"
    assert heat.Rated_Water_Flow_Rate == "autosize"
    assert heat.Gross_Rated_Heating_Capacity == "autosize"


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_scale_baseline_idf_datacenter_wshp_named_specs_match_real_largeoffice_coils():
    """The 8 _NAMED_ABSOLUTE_SPECS Names/fields resolve real objects (not typos)
    on the real LargeOffice baseline, and all 8 are genuinely autosize there."""
    path = config.BASELINE_IDF_DIR / layout_assigner.ARCHETYPE_IDF_MAP["LargeOffice"]
    idf = GeomIDF(str(path))
    matched = 0
    for cls, obj_name, value_field, _s1_value in layout_assigner._NAMED_ABSOLUTE_SPECS:
        objs = [o for o in idf.idfobjects.get(cls, []) if str(o.Name).strip() == obj_name]
        assert len(objs) == 1, f"expected exactly 1 match for {cls}/{obj_name!r}"
        val = getattr(objs[0], value_field)
        assert layout_assigner._is_blank_or_autosize(val), f"{obj_name}/{value_field} not autosize on real baseline: {val!r}"
        matched += 1
    assert matched == len(layout_assigner._NAMED_ABSOLUTE_SPECS) == 28


# ── B05 — Zone X/Y Origin scaling (E-LA-28) ──────────────────────────────────
# PLAN_storey-matching_implementation.md §5 B05 (D7 closed 2026-07-26): rooms
# shrank correctly (BuildingSurface:Detailed vertices) while the building's own
# outer extent stayed frozen at the raw S=1 baseline, because Zone X/Y Origin
# was never in _GEOMETRY_SURFACE_CLASSES. Three assertions required: identity,
# area invariant, and XY bounding-box extent -- never area, per the plan's own
# warning that area checks cannot detect this defect (zone floor areas are
# surface geometry and scale correctly regardless of the Origin bug).

def _idf_xy_bbox(idf):
    """Min/max X/Y across every BuildingSurface:Detailed vertex, in WORLD
    coordinates (zone Origin + relative vertex offset) -- the actual outer
    extent of the building as EnergyPlus/the viewer would place it."""
    zone_origins = {
        z.Name: (float(z.X_Origin or 0.0), float(z.Y_Origin or 0.0))
        for z in idf.idfobjects.get("ZONE", [])
    }
    xs, ys = [], []
    for s in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        ox, oy = zone_origins.get(s.Zone_Name, (0.0, 0.0))
        for x, y, _z in s.coords:
            xs.append(x + ox)
            ys.append(y + oy)
    return min(xs), max(xs), min(ys), max(ys)


class TestScaleBaselineIdfZoneOrigins:
    """B05: scale_baseline_idf() must scale Zone X/Y Origin by planar_scale_factor."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_identity_case_still_recentres_zone_origins(self):
        """SUPERSEDES the old B05-era 'bit-identical' assertion -- B08b/D8
        (2026-07-26, PLAN_storey-matching_implementation.md) made re-centring
        UNCONDITIONAL: planar_k == 1.0 (real_area == baseline_area) no longer
        leaves Zone Origins bit-identical to the raw baseline, because the
        cross-building placement defect it closes (B08a) is not a scaling
        defect -- MidriseApartment's raw Origins are not already centred on
        its own footprint. Z is untouched either way (D8's own rule)."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        z_before = {z.Name: z.Z_Origin for z in idf.idfobjects["ZONE"]}
        recomputed_area = layout_assigner.compute_band_map(idf)["recomputed_area_m2"]
        scale = layout_assigner.calculate_scaling_factor(recomputed_area, recomputed_area)
        assert scale["planar_scale_factor"] == 1.0
        layout_assigner.scale_baseline_idf(idf, scale)
        z_after = {z.Name: z.Z_Origin for z in idf.idfobjects["ZONE"]}
        assert z_before == z_after  # Z untouched, D8's own rule
        x0min, x0max, y0min, y0max = _idf_xy_bbox(idf)
        assert (x0min + x0max) / 2.0 == pytest.approx(0.0, abs=1e-6)
        assert (y0min + y0max) / 2.0 == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_area_invariant_total_floor_area_unchanged_by_origin_scaling(self):
        """Total floor area per building is unaffected by the Origin fix (rule:
        'the one thing layout_assign does correctly today and the fix may not
        carry it off') -- area was never going to detect E-LA-28, so this test
        exists to prove the fix does not regress the thing that already worked."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))

        def _total_floor_area(idf_obj):
            return sum(
                s.area for s in idf_obj.idfobjects["BUILDINGSURFACE:DETAILED"]
                if str(s.Surface_Type).strip().upper() == "FLOOR"
            )

        area_before = _total_floor_area(idf)
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=150.0, baseline_area_m2=2350.94)
        layout_assigner.scale_baseline_idf(idf, scale)
        area_after = _total_floor_area(idf)
        assert area_after == pytest.approx(area_before * scale["area_scale_ratio"], rel=0.01)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_xy_bounding_box_shrinks_by_planar_k_not_by_one(self):
        """The defect this test guards: before B05, the whole-model XY bounding
        box stayed at the raw S=1 extent (shrink factor 1.0) no matter what
        planar_k was, because Zone Origin never moved. Assert on the bounding
        box, never on the area -- see the plan's own warning."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf_before = GeomIDF(str(path))
        x0min, x0max, y0min, y0max = _idf_xy_bbox(idf_before)
        span_x_before, span_y_before = x0max - x0min, y0max - y0min

        idf_after = GeomIDF(str(path))
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=150.0, baseline_area_m2=2350.94)
        k = scale["planar_scale_factor"]
        assert k != 1.0  # otherwise this test can't distinguish the two cases
        layout_assigner.scale_baseline_idf(idf_after, scale)
        x1min, x1max, y1min, y1max = _idf_xy_bbox(idf_after)
        span_x_after, span_y_after = x1max - x1min, y1max - y1min

        assert span_x_after == pytest.approx(span_x_before * k, rel=0.01)
        assert span_y_after == pytest.approx(span_y_before * k, rel=0.01)
        # The pre-B05 defect: span_after == span_before * 1.0 (frozen extent).
        # Guard that a regression back to that state would fail this assertion.
        assert span_x_after != pytest.approx(span_x_before, rel=0.05)


# ── B08b — cross-building placement re-centring (E-LA-31 item 2 / D8) ───────
# PLAN_storey-matching_implementation.md D8 (manager ruling 2026-07-26, on
# B08a's diagnosis): scale_baseline_idf() scaled the prototype about its own
# arbitrary local (0,0) and never re-centred, so builder.py's existing
# `+ footprint_centroid_utm` placement step landed a corner, not the
# prototype's own centroid, on the real building -- median offset 8.49 m
# (nyc) / 11.49 m (la), B08a n=2,630. The fix is a pure translation inside
# scale_baseline_idf(), unconditional on planar_scale_factor.

class TestScaleBaselineIdfRecentring:
    """B08b/D8: scale_baseline_idf() re-centres the whole model's
    BuildingSurface:Detailed XY bounding box onto local (0, 0), independent of
    the scale factor, using the SAME `_idf_xy_bbox` world-coordinate helper
    B05's own extent test already relies on."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_scaled_case_recentres_bbox_to_origin(self):
        """Non-identity planar_k (the common case: a real building far from
        its prototype's own size) also lands the bbox centre at (0, 0)."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=150.0, baseline_area_m2=2350.94)
        assert scale["planar_scale_factor"] != 1.0
        layout_assigner.scale_baseline_idf(idf, scale)
        x0min, x0max, y0min, y0max = _idf_xy_bbox(idf)
        assert (x0min + x0max) / 2.0 == pytest.approx(0.0, abs=1e-6)
        assert (y0min + y0max) / 2.0 == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_recentring_does_not_touch_z(self):
        """D8's own rule, same as B05: Z is never touched by the translation.
        Compared as a multiset, not by position: the pre-existing (pre-B08b)
        planar_k vertex-scale loop's own `surf.setcoords()` call -- unrelated
        to this task -- already re-orders a surface's vertex list on any
        non-1.0 planar_k, so position is not a stable basis for comparison."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        z_before = sorted(z0 for _, _, z0 in idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords)
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=150.0, baseline_area_m2=2350.94)
        layout_assigner.scale_baseline_idf(idf, scale)
        z_after = sorted(z0 for _, _, z0 in idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].coords)
        assert z_before == pytest.approx(z_after)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_world_coordinate_baseline_also_recentres(self):
        """Supermarket_V22.1.idf is GlobalGeometryRules Coordinate_System =
        World, the one archetype (of 25) that is NOT Relative (2026-07-26
        survey) -- exercises the direct-vertex-shift branch, not the
        Zone-Origin-only branch every other archetype takes. Bbox computed
        from RAW surface vertices with NO zone-origin addition (unlike
        `_idf_xy_bbox`, which assumes Relative and would double-count the
        Zone Origin shift here) -- World-mode vertices are already absolute,
        exactly as scale_baseline_idf()'s own anchor computation treats them."""
        path = layout_assigner.get_registry().get_baseline_idf("SuperMarket")
        idf = GeomIDF(str(path))
        rules = idf.idfobjects["GLOBALGEOMETRYRULES"]
        assert rules[0].Coordinate_System.upper() == "WORLD"
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=1500.0, baseline_area_m2=4181.0)
        layout_assigner.scale_baseline_idf(idf, scale)
        xs, ys = [], []
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
            for x, y, _z in s.coords:
                xs.append(x)
                ys.append(y)
        assert (min(xs) + max(xs)) / 2.0 == pytest.approx(0.0, abs=1e-6)
        assert (min(ys) + max(ys)) / 2.0 == pytest.approx(0.0, abs=1e-6)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_recentring_shifts_position_only_never_shape(self):
        """Translation must not distort the envelope: span (max - min) in X
        and Y is invariant to re-centring -- only the position moves. This is
        the B05 span test's own quantity, re-asserted after B08b's addition."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf_no_recentre_ref = GeomIDF(str(path))
        x0min, x0max, y0min, y0max = _idf_xy_bbox(idf_no_recentre_ref)
        span_x_before, span_y_before = x0max - x0min, y0max - y0min

        idf = GeomIDF(str(path))
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=150.0, baseline_area_m2=2350.94)
        k = scale["planar_scale_factor"]
        layout_assigner.scale_baseline_idf(idf, scale)
        x1min, x1max, y1min, y1max = _idf_xy_bbox(idf)
        span_x_after, span_y_after = x1max - x1min, y1max - y1min

        assert span_x_after == pytest.approx(span_x_before * k, rel=0.01)
        assert span_y_after == pytest.approx(span_y_before * k, rel=0.01)


# ── B01/B02/B03 — storey matching (plan storey-Matching Phase B) ────────────
# PLAN_storey-matching_implementation.md D2/D3(a)/B00-B04.

class TestComputeBandMap:
    """compute_band_map() reproduces A1's accepted geometry map
    (results/a1_prototype_storey_structure.csv) via the same Z-clustering method,
    independently of that CSV file (no production read of docs/ artifacts)."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    @pytest.mark.parametrize("archetype_id,expected_n_proto,expected_plate_proto", [
        ("MidriseApartment", 3, 783.65),      # G/M/T, A1 avg_storey_plate_area_m2
        ("HighriseApartment", 3, 783.65),     # G/M/T
        ("MediumOffice", 3, 1660.73),         # F1/F2/F3, single middle band
        ("RetailStandalone", 1, 2293.99),     # single-storey (degenerate band)
        ("SmallOffice", 2, 539.57),           # "other" convention, no middle band (A1/F-07)
        ("LargeOffice", 4, 11580.09),         # F1/F2/..., 2 non-uniform middle bands
    ])
    def test_matches_a1_recomputed_geometry(self, archetype_id, expected_n_proto, expected_plate_proto):
        path = layout_assigner.get_registry().get_baseline_idf(archetype_id)
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == expected_n_proto
        assert band_map["plate_proto_m2"] == pytest.approx(expected_plate_proto, abs=0.5)
        assert len(band_map["bands"]) == expected_n_proto
        # bands ordered bottom-to-top
        z_levels = [b["z_level_m"] for b in band_map["bands"]]
        assert z_levels == sorted(z_levels)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_never_reads_zone_names_only_z_geometry(self):
        """SmallOffice's 'other' convention (A1/F-07) still clusters correctly --
        proof compute_band_map never assumes G/M/T zone-name prefixes."""
        path = layout_assigner.get_registry().get_baseline_idf("SmallOffice")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        names = [n for b in band_map["bands"] for n in b["zone_names"]]
        assert not any(n.split()[0] in ("G", "M", "T") for n in names)
        assert band_map["n_proto"] == 2


class TestComputeBandMapZoneGroupAware:
    """R01 (PLAN_storey-matching_REMAINder.md, AMENDED SCOPE 2026-07-26,
    E-LA-35 Cause A): compute_band_map() must read ZoneList/ZoneGroup so a
    band whose zones are repeated by a ZoneGroup's "Zone List Multiplier" is
    no longer invisible to recomputed_area_m2. Exactly 2 of the 25 pinned
    baselines carry a real ZoneGroup: ApartmentHighRise (list mult 8) and
    ApartmentMidRise (list mult 2, object spelled ZONEGROUP upper-case in
    that file -- the AUDIT entry's finding)."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    @pytest.mark.parametrize("archetype_id,expected_n_storeys,expected_recomputed_area", [
        ("HighriseApartment", 10, 7836.48),  # 1 (G) + 8 (ZoneGroup mid) + 1 (T)
        ("MidriseApartment", 4, 3134.61),    # 1 (G) + 2 (ZoneGroup mid) + 1 (T)
    ])
    def test_zonegroup_aware_recomputed_area_and_storeys_represented(
        self, archetype_id, expected_n_storeys, expected_recomputed_area
    ):
        path = layout_assigner.get_registry().get_baseline_idf(archetype_id)
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        # n_proto stays the measured Z-BAND count (3, the G/M/T shape) -- match_storeys()
        # branches on it and must not be perturbed (R04 is closed at option (a)).
        assert band_map["n_proto"] == 3
        assert band_map["n_storeys_represented"] == expected_n_storeys
        assert band_map["recomputed_area_m2"] == pytest.approx(expected_recomputed_area, abs=0.5)
        # plate_proto_m2 (average area of ONE physical floor) is unaffected: dividing
        # the now-ZoneGroup-aware total by the now-ZoneGroup-aware storey count
        # reproduces the same per-floor plate the old n_proto-based division gave,
        # because the G/M/T bands are uniform-area in both prototypes.
        assert band_map["plate_proto_m2"] == pytest.approx(783.65, abs=0.5)

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_other_23_prototypes_byte_identical_band_map(self):
        """Byte-identity guard: for every mapped archetype EXCEPT the 2 apartment
        ones, compute_band_map()'s return must be unchanged by the ZoneGroup-aware
        rewrite (no ZoneGroup object exists in those 23 files at all)."""
        exempt = {"HighriseApartment", "MidriseApartment"}
        checked = 0
        for archetype_id in _MAPPED_VOCAB:
            if archetype_id in exempt:
                continue
            path = layout_assigner.get_registry().get_baseline_idf(archetype_id)
            if path is None:
                continue
            checked += 1
            idf = GeomIDF(str(path))
            band_map = layout_assigner.compute_band_map(idf)
            assert band_map["n_storeys_represented"] == band_map["n_proto"], archetype_id
            for b in band_map["bands"]:
                assert b["storeys_in_band"] == pytest.approx(1.0), archetype_id
        # 25-file library, 2 exempt (apartment archetypes may repeat via aliases
        # e.g. LargeOfficeDetailed -> same file as LargeOffice, so this counts
        # DISTINCT archetype_id entries, not distinct files -- report both.
        assert checked >= 23, f"only checked {checked} non-apartment archetypes"


class TestMatchStoreys:
    """match_storeys() per plan D3(a)/CP-A 'PROCEED, RE-SCOPED' ruling."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_identity_is_a_noop_and_leaves_multipliers_untouched(self):
        """n_real == n_proto: status identity, idf byte-identical (B02 regression guard)."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        result = layout_assigner.match_storeys(idf, band_map["n_proto"], band_map)
        assert result["status"] == "identity"
        assert result["multiplier"] is None
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_taller_applies_multiplier_to_middle_band_only(self):
        """MediumOffice n_real=6 vs n_proto=3 -> Multiplier=4 on the 5 middle-band
        zones only (manager-reproduced value, CP-A A2-bis: Zone Multiplier=4,
        eplusout.eio CORE_MID record; results/a2_run_multiplier/)."""
        path = layout_assigner.get_registry().get_baseline_idf("MediumOffice")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 3
        result = layout_assigner.match_storeys(idf, 6, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 4
        assert len(result["band_zone_names"]) == 5
        mid_names = set(result["band_zone_names"])
        for z in idf.idfobjects["ZONE"]:
            expected = 4 if z.Name in mid_names else 1
            assert float(z.Multiplier) == expected, f"{z.Name} Multiplier={z.Multiplier}, expected {expected}"

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_degenerate_single_band_multiplies_the_whole_prototype(self):
        """n_proto == 1 (RetailStandalone): the sole band is bottom=middle=top,
        multiplied directly by n_real."""
        path = layout_assigner.get_registry().get_baseline_idf("RetailStandalone")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 1
        result = layout_assigner.match_storeys(idf, 3, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 3
        for z in idf.idfobjects["ZONE"]:
            assert float(z.Multiplier) == 3

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_shorter_falls_back_untouched_frozen_literal(self):
        """n_real < n_proto: D3(b) rejected (A3) -> fallback_shorter, idf
        byte-identical -- frozen literal behaviour on the fallback path."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        result = layout_assigner.match_storeys(idf, 2, band_map)  # n_proto=3
        assert result["status"] == "fallback_shorter"
        assert result["multiplier"] is None
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_taller_but_not_expressible_falls_back_untouched(self):
        """LargeOffice n_proto=4 has 2 non-uniform middle bands (A1: baseline
        already bakes Multiplier>1 into its own 'mid' band) -- no single band can
        be bumped unambiguously, so a taller real building still falls back,
        idf byte-identical, tagged distinctly from the shorter case (D5/B03)."""
        path = layout_assigner.get_registry().get_baseline_idf("LargeOffice")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 4
        result = layout_assigner.match_storeys(idf, 8, band_map)  # taller (8 > 4)
        assert result["status"] == "fallback_not_expressible"
        assert result["multiplier"] is None
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after

    def test_n_proto_zero_is_identity_never_crashes(self):
        """Defensive: an idf with no FLOOR surfaces (n_proto=0) never raises,
        degrades to identity/no-op."""
        band_map = {"n_proto": 0, "plate_proto_m2": 0.0, "recomputed_area_m2": 0.0, "bands": []}
        result = layout_assigner.match_storeys(None, 5, band_map)
        assert result["status"] == "identity"


class TestMatchStoreysResidualZoneGroup:
    """R10 (E-LA-36, plan §5 REMAINder 2026-07-26): match_storeys() must solve for
    the RESIDUAL Zone.Multiplier on a ZoneGroup-carrying band, not the absolute
    one, since EnergyPlus compounds Zone.Multiplier with a pre-existing ZoneGroup
    Zone List Multiplier. MidriseApartment n_real=4 (list mult 2) previously wrote
    Multiplier=2 -> 1+4+1=6 simulated storeys; the fix must write NOTHING (residual
    == 1) and still report n_real as matched."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_midrise_n_real_4_residual_is_1_no_field_write(self):
        """MidriseApartment: n_proto=3 (band count), ZoneGroup list mult=2 on the
        middle band. n_real=4 -> non_middle_storeys=1+1=2, list_multiplier=2,
        residual=(4-2)/2=1 -> exact no-op: status 'applied', multiplier=1,
        band_zone_names=[], and the idf's Zone.Multiplier fields are UNTOUCHED
        (the prototype's own ZoneGroup already reproduces n_real=4)."""
        path = layout_assigner.get_registry().get_baseline_idf("MidriseApartment")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 3
        assert band_map["n_storeys_represented"] == 4
        result = layout_assigner.match_storeys(idf, 4, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 1
        assert result["band_zone_names"] == []
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after, "residual==1 must not write a redundant Zone.Multiplier field"

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_highrise_n_real_10_residual_is_1_no_field_write(self):
        """HighriseApartment: ZoneGroup list mult=8. n_real=10 (its own native
        represented-storey count) -> non_middle_storeys=2, residual=(10-2)/8=1 ->
        no-op, matching the plan's required 'report the HighriseApartment case
        too' line."""
        path = layout_assigner.get_registry().get_baseline_idf("HighriseApartment")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 3
        assert band_map["n_storeys_represented"] == 10
        result = layout_assigner.match_storeys(idf, 10, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 1
        assert result["band_zone_names"] == []
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_highrise_n_real_18_writes_exact_residual_2(self):
        """HighriseApartment, n_real=18 (taller than the native 10): non_middle
        storeys=2, list_multiplier=8, raw=16, residual=16/8=2 (exact, >=1) ->
        Zone.Multiplier=2 written on the 9 middle-band zones only, which compounds
        with the ZoneGroup's own list mult 8 to give 1 + (2*8) + 1 = 18 represented
        storeys, matching n_real exactly -- not the old absolute formula's value
        of 8 (10 - (3-1)), which would have compounded to 1 + (8*8) + 1 = 66."""
        path = layout_assigner.get_registry().get_baseline_idf("HighriseApartment")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        result = layout_assigner.match_storeys(idf, 18, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 2
        assert len(result["band_zone_names"]) == 9
        mid_names = set(result["band_zone_names"])
        for z in idf.idfobjects["ZONE"]:
            expected = 2 if z.Name in mid_names else 1
            assert float(z.Multiplier) == expected, f"{z.Name} Multiplier={z.Multiplier}, expected {expected}"

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_highrise_n_real_not_exactly_divisible_falls_back(self):
        """HighriseApartment, n_real=15: non_middle_storeys=2, raw=13, list_multiplier=8
        -> 13 % 8 != 0, so the residual is not exact -> fallback_not_expressible,
        idf byte-identical (never silently rounds)."""
        path = layout_assigner.get_registry().get_baseline_idf("HighriseApartment")
        idf = GeomIDF(str(path))
        before = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        band_map = layout_assigner.compute_band_map(idf)
        result = layout_assigner.match_storeys(idf, 15, band_map)
        assert result["status"] == "fallback_not_expressible"
        assert result["multiplier"] is None
        after = {z.Name: float(z.Multiplier) for z in idf.idfobjects["ZONE"]}
        assert before == after

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_other_23_prototypes_byte_identical_taller_case(self):
        """Byte-identity guard (rule: assert both, do not assume either): for a
        non-ZoneGroup archetype exercising the n_proto==3 taller branch
        (MediumOffice, list_multiplier==1 for every band), R10's residual formula
        must reduce EXACTLY to the pre-R10 absolute formula (n_real - (n_proto-1))
        -- same status, same multiplier, same written zone set as before R10."""
        path = layout_assigner.get_registry().get_baseline_idf("MediumOffice")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 3
        for b in band_map["bands"]:
            assert b["storeys_in_band"] == pytest.approx(1.0)
        result = layout_assigner.match_storeys(idf, 6, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 4  # pre-R10 value, unchanged (6 - (3-1))
        assert len(result["band_zone_names"]) == 5

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_other_23_prototypes_byte_identical_degenerate_case(self):
        """Same byte-identity guard for the n_proto==1 degenerate branch
        (RetailStandalone): residual formula must reduce exactly to
        multiplier == n_real, unchanged from pre-R10."""
        path = layout_assigner.get_registry().get_baseline_idf("RetailStandalone")
        idf = GeomIDF(str(path))
        band_map = layout_assigner.compute_band_map(idf)
        assert band_map["n_proto"] == 1
        result = layout_assigner.match_storeys(idf, 3, band_map)
        assert result["status"] == "applied"
        assert result["multiplier"] == 3  # pre-R10 value, unchanged


class TestScalingFactorStoreyMatching:
    """calculate_scaling_factor()'s D2 plate-ratio decomposition (B02)."""

    def test_identity_case_is_byte_identical_to_old_2arg_call(self):
        """🔑 THE REGRESSION GUARD (B02): n_real == n_proto must reproduce the
        pre-storey-matching 2-arg formula EXACTLY -- asserted with ==, not approx."""
        real_area, baseline_area = 2350.96, 3135.0  # MidriseApartment-shaped numbers
        old = layout_assigner.calculate_scaling_factor(real_area, baseline_area)
        for n in (1, 3, 7):  # identity must hold for ANY n_real == n_proto, not just one
            new = layout_assigner.calculate_scaling_factor(
                real_area, baseline_area, num_floors=n, n_proto=n
            )
            assert new["planar_scale_factor"] == old["planar_scale_factor"]
            assert new["area_scale_ratio"] == old["area_scale_ratio"]
            assert new["target_area_m2"] == old["target_area_m2"]
            assert new["baseline_area_m2"] == old["baseline_area_m2"]

    def test_omitted_num_floors_n_proto_is_byte_identical_to_old_signature(self):
        """Backward compatibility (B02 'keep the old signature working'):
        omitting num_floors/n_proto entirely takes the exact same code path."""
        old = layout_assigner.calculate_scaling_factor(5000.0, 2500.0)
        new = layout_assigner.calculate_scaling_factor(5000.0, 2500.0, num_floors=None, n_proto=None)
        assert new == old

    def test_taller_uses_plate_ratio_not_total_area_ratio(self):
        """D2: the double-shrink trap. planar_scale_factor must come from the
        plate ratio (plate_target/plate_proto), not real_area/baseline_area_m2."""
        real_area, baseline_area, n_real, n_proto = 6000.0, 4982.19, 6, 3
        result = layout_assigner.calculate_scaling_factor(
            real_area, baseline_area, num_floors=n_real, n_proto=n_proto, storeys_matched=True
        )
        plate_target = real_area / n_real
        plate_proto = baseline_area / n_proto
        expected_planar = math.sqrt(plate_target / plate_proto)
        assert result["planar_scale_factor"] == pytest.approx(expected_planar, rel=1e-12)
        # NOT the naive old formula (which would double-shrink the plate):
        assert result["planar_scale_factor"] != pytest.approx(math.sqrt(real_area / baseline_area), rel=1e-6)

    def test_storeys_matched_flag_changes_area_scale_ratio_not_planar_factor(self):
        """E-LA-27: area_scale_ratio must reflect the storey-multiplier growth
        ONLY when a Zone Multiplier was actually set on the idf (storeys_matched
        True). Otherwise (fallback -- D5) it must stay pinned to the plate ratio,
        or absolute-load/capacity fields get scaled for a multiplier that was
        never applied -- the fallback-population mirror of E-LA-27."""
        real_area, baseline_area, n_real, n_proto = 6000.0, 4982.19, 6, 3
        applied = layout_assigner.calculate_scaling_factor(
            real_area, baseline_area, num_floors=n_real, n_proto=n_proto, storeys_matched=True
        )
        not_applied = layout_assigner.calculate_scaling_factor(
            real_area, baseline_area, num_floors=n_real, n_proto=n_proto, storeys_matched=False
        )
        assert applied["planar_scale_factor"] == not_applied["planar_scale_factor"]
        assert applied["area_scale_ratio"] != not_applied["area_scale_ratio"]
        assert applied["area_scale_ratio"] == pytest.approx(
            not_applied["area_scale_ratio"] * (n_real / n_proto), rel=1e-9
        )
        plate_ratio = (real_area / n_real) / (baseline_area / n_proto)
        assert not_applied["area_scale_ratio"] == pytest.approx(plate_ratio, rel=1e-12)


class TestRoofScaleRatioPVInvariance:
    """R03 (PLAN_storey-matching_REMAINder.md, E-LA-32): PV/generator nameplate
    capacity must track roof area (planar_scale_factor ** 2) and be INVARIANT to
    the storey multiplier, unlike transformer_scale_ratio which deliberately
    compounds with it (D9)."""

    def test_roof_scale_ratio_is_planar_squared_and_ignores_multiplier(self):
        real_area, baseline_area, n_real, n_proto = 6000.0, 4982.19, 6, 3
        applied = layout_assigner.calculate_scaling_factor(
            real_area, baseline_area, num_floors=n_real, n_proto=n_proto,
            storeys_matched=True, multiplier=4,
        )
        not_applied = layout_assigner.calculate_scaling_factor(
            real_area, baseline_area, num_floors=n_real, n_proto=n_proto,
            storeys_matched=False, multiplier=None,
        )
        # roof_scale_ratio must be identical whether or not the multiplier applied --
        # the multiplier only ever repeats a MIDDLE band, never the roof.
        assert applied["roof_scale_ratio"] == pytest.approx(not_applied["roof_scale_ratio"], rel=1e-12)
        assert applied["roof_scale_ratio"] == pytest.approx(applied["planar_scale_factor"] ** 2, rel=1e-12)
        # And it must differ from transformer_scale_ratio, which DOES compound
        # with the multiplier (D9) -- proof the two are genuinely different scalars,
        # not the same number under two names.
        assert applied["transformer_scale_ratio"] == pytest.approx(
            applied["roof_scale_ratio"] * 4, rel=1e-12
        )
        assert applied["transformer_scale_ratio"] != pytest.approx(applied["roof_scale_ratio"], rel=1e-6)

    def test_scale_baseline_idf_scales_pvwatts_and_generators_by_roof_not_area_ratio(self):
        idf, *_ = _build_two_zone_fixture()
        pv = idf.newidfobject("GENERATOR:PVWATTS", Name="PV 1", DC_System_Capacity=50000.0)
        gen = idf.newidfobject(
            "ELECTRICLOADCENTER:GENERATORS", Name="Generators",
            Generator_1_Rated_Electric_Power_Output=50000.0,
        )
        # storeys_matched=True + multiplier=4: area_scale_ratio/transformer_scale_ratio
        # grow much faster than roof_scale_ratio for the same S -- proves PV is NOT
        # riding on either of those two.
        scale = layout_assigner.calculate_scaling_factor(
            real_area_m2=2400.0, baseline_area_m2=100.0, num_floors=8, n_proto=2,
            storeys_matched=True, multiplier=4,
        )
        layout_assigner.scale_baseline_idf(idf, scale)

        assert pv.DC_System_Capacity == pytest.approx(50000.0 * scale["roof_scale_ratio"])
        assert gen.Generator_1_Rated_Electric_Power_Output == pytest.approx(50000.0 * scale["roof_scale_ratio"])
        # Not scaled by the multiplier-inflated ratios (guards against a future
        # regression silently putting these back on area_s/transformer_s).
        assert pv.DC_System_Capacity != pytest.approx(50000.0 * scale["area_scale_ratio"], rel=1e-6)
        assert pv.DC_System_Capacity != pytest.approx(50000.0 * scale["transformer_scale_ratio"], rel=1e-6)

    def test_skips_autosize_pvwatts_and_generators(self):
        idf, *_ = _build_two_zone_fixture()
        pv = idf.newidfobject("GENERATOR:PVWATTS", Name="PV 1", DC_System_Capacity="autosize")
        scale = layout_assigner.calculate_scaling_factor(real_area_m2=400.0, baseline_area_m2=100.0)
        layout_assigner.scale_baseline_idf(idf, scale)
        assert pv.DC_System_Capacity == "autosize"


class TestBuilderStoreyMatchWiring:
    """B03: builder.py:~447 call site wiring and D5 fallback tagging."""

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_shorter_case_tags_data_quality_flag(self, tmp_path):
        """Real building shorter than its MidriseApartment prototype (n_proto=3)
        -> D5 fallback, tagged 'storey_match_fallback_shorter', never silently."""
        row = _make_layout_assign_row("MidriseApartment", SYNTHETIC_EPW, footprint_area_m2=300.0, levels=1)
        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        bidf = BuildingIDF(row, resolution_mode="layout_assign")
        (tmp_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, tmp_path)
        assert manifest["generation_status"] == "success"
        assert "storey_match_fallback_shorter" in manifest["data_quality_flag"]

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_not_expressible_case_tags_distinctly_from_shorter(self, tmp_path):
        """LargeOffice, real building taller than its n_proto=4 band count but the
        band structure has no single repeatable middle band -> fallback tagged
        'storey_match_fallback_not_expressible', distinct from the shorter tag."""
        row = _make_layout_assign_row("LargeOffice", SYNTHETIC_EPW, footprint_area_m2=50000.0, levels=8)
        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        bidf = BuildingIDF(row, resolution_mode="layout_assign")
        (tmp_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, tmp_path)
        assert manifest["generation_status"] == "success"
        assert "storey_match_fallback_not_expressible" in manifest["data_quality_flag"]
        assert "storey_match_fallback_shorter" not in manifest["data_quality_flag"]

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_taller_applied_case_is_not_tagged_and_sets_multiplier(self, tmp_path):
        """Real building taller than MediumOffice's n_proto=3 -> status applied,
        NOT tagged in data_quality_flag (only the fallback statuses are D5)."""
        row = _make_layout_assign_row("MediumOffice", SYNTHETIC_EPW, footprint_area_m2=1000.0, levels=6)
        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        bidf = BuildingIDF(row, resolution_mode="layout_assign")
        (tmp_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, tmp_path)
        assert manifest["generation_status"] == "success"
        assert "storey_match_fallback" not in manifest["data_quality_flag"]
        saved = GeomIDF(str(Path(manifest["idf_path"])))
        multipliers = sorted(float(z.Multiplier) for z in saved.idfobjects["ZONE"])
        assert 4 in multipliers  # the middle band was actually multiplied in the saved idf

    @pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
    def test_identity_case_not_tagged(self, tmp_path):
        """Real building exactly matching MidriseApartment's n_proto=3 -> identity,
        not tagged (it is a no-op, not a fallback)."""
        row = _make_layout_assign_row("MidriseApartment", SYNTHETIC_EPW, footprint_area_m2=800.0, levels=3)
        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        bidf = BuildingIDF(row, resolution_mode="layout_assign")
        (tmp_path / "idfs").mkdir()
        manifest = bidf.build(gdf, {}, tmp_path)
        assert manifest["generation_status"] == "success"
        assert "storey_match" not in manifest["data_quality_flag"]


# ── T05 — parse_baseline_zones() ─────────────────────────────────────────────

def test_parse_baseline_zones_synthetic():
    idf, zone_abs, zone_area, *_ = _build_two_zone_fixture()
    zones = layout_assigner.parse_baseline_zones(idf, "SyntheticTestArchetype")
    assert len(zones) == len(idf.idfobjects["ZONE"]) == 2
    names = {z["name"] for z in zones}
    assert names == {zone_abs, zone_area}
    for z in zones:
        assert z["archetype_id"] == "SyntheticTestArchetype"
        assert z["extruded"] is True
        assert z["floor_area_m2"] == pytest.approx(100.0)


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_parse_baseline_zones_real_midrise():
    path = config.BASELINE_IDF_DIR / layout_assigner.ARCHETYPE_IDF_MAP["MidriseApartment"]
    idf = GeomIDF(str(path))
    zones = layout_assigner.parse_baseline_zones(idf, "MidriseApartment")
    assert len(zones) == len(idf.idfobjects["ZONE"])
    assert all(z["extruded"] for z in zones)


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_parse_baseline_zones_real_hospital():
    path = config.BASELINE_IDF_DIR / layout_assigner.ARCHETYPE_IDF_MAP["Hospital"]
    idf = GeomIDF(str(path))
    zones = layout_assigner.parse_baseline_zones(idf, "Hospital")
    assert len(zones) == len(idf.idfobjects["ZONE"])


# ── T06 — purge_baseline_outputs() / patch_location_and_weather() ───────────

_OUTPUT_LIKE_CLASSES = (
    "OUTPUT:VARIABLE", "OUTPUT:METER", "OUTPUT:METER:METERFILEONLY",
    "OUTPUT:METER:CUMULATIVE", "OUTPUT:TABLE:SUMMARYREPORTS", "OUTPUT:TABLE:MONTHLY",
    "OUTPUTCONTROL:TABLE:STYLE", "OUTPUT:SQLITE",
)


def test_purge_baseline_outputs_removes_all_output_classes():
    idf, *_ = _build_two_zone_fixture()
    idf.newidfobject(
        "OUTPUT:VARIABLE", Key_Value="*",
        Variable_Name="Zone Mean Air Temperature", Reporting_Frequency="Hourly",
    )
    idf.newidfobject("OUTPUT:METER", Key_Name="Electricity:Facility", Reporting_Frequency="Hourly")
    idf.newidfobject(
        "OUTPUT:METER:METERFILEONLY", Key_Name="NaturalGas:Facility", Reporting_Frequency="RunPeriod",
    )
    idf.newidfobject(
        "OUTPUT:METER:CUMULATIVE", Key_Name="Electricity:Facility", Reporting_Frequency="Hourly",
    )
    idf.newidfobject("OUTPUT:TABLE:SUMMARYREPORTS", Report_1_Name="AllSummary")
    idf.newidfobject(
        "OUTPUT:TABLE:MONTHLY", Name="Test Monthly", Digits_After_Decimal=2,
    )
    idf.newidfobject("OUTPUTCONTROL:TABLE:STYLE", Column_Separator="HTML")
    idf.newidfobject("OUTPUT:SQLITE", Option_Type="SimpleAndTabular")
    for cls in _OUTPUT_LIKE_CLASSES:
        assert len(idf.idfobjects[cls]) > 0, f"fixture setup failed for {cls}"

    layout_assigner.purge_baseline_outputs(idf)

    for cls in [c for c in idf.idfobjects if c.startswith("OUTPUT")]:
        assert len(idf.idfobjects[cls]) == 0, f"{cls} not purged: {idf.idfobjects[cls]}"


def test_patch_location_and_weather_sets_site_location_and_single_full_year_runperiod():
    idf, *_ = _build_two_zone_fixture()
    assert len(idf.idfobjects["RUNPERIOD"]) == 1
    base_rp = idf.idfobjects["RUNPERIOD"][0]
    base_rp.Begin_Month, base_rp.Begin_Day_of_Month = 6, 1
    base_rp.End_Month, base_rp.End_Day_of_Month = 6, 30
    idf.newidfobject(
        "RUNPERIOD", Name="Extra", Begin_Month=1, Begin_Day_of_Month=1,
        End_Month=3, End_Day_of_Month=31,
    )
    assert len(idf.idfobjects["RUNPERIOD"]) == 2

    layout_assigner.patch_location_and_weather(idf, SYNTHETIC_EPW)

    locs = idf.idfobjects["SITE:LOCATION"]
    assert len(locs) == 1
    assert locs[0].Name == "Montreal"
    assert abs(float(locs[0].Latitude) - 45.47) < 1e-6
    assert abs(float(locs[0].Longitude) - (-73.75)) < 1e-6
    assert abs(float(locs[0].Time_Zone) - (-5.0)) < 1e-6
    assert abs(float(locs[0].Elevation) - 36.0) < 1e-6

    rps = idf.idfobjects["RUNPERIOD"]
    assert len(rps) == 1
    assert int(rps[0].Begin_Month) == 1 and int(rps[0].Begin_Day_of_Month) == 1
    assert int(rps[0].End_Month) == 12 and int(rps[0].End_Day_of_Month) == 31


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_purge_and_patch_real_midrise():
    path = config.BASELINE_IDF_DIR / layout_assigner.ARCHETYPE_IDF_MAP["MidriseApartment"]
    idf = GeomIDF(str(path))

    layout_assigner.purge_baseline_outputs(idf)
    for cls in _OUTPUT_LIKE_CLASSES:
        assert len(idf.idfobjects[cls]) == 0, f"{cls} not purged"

    layout_assigner.patch_location_and_weather(idf, SYNTHETIC_EPW)
    locs = idf.idfobjects["SITE:LOCATION"]
    assert len(locs) == 1
    assert locs[0].Name == "Montreal"
    rps = idf.idfobjects["RUNPERIOD"]
    assert len(rps) == 1
    assert int(rps[0].Begin_Month) == 1 and int(rps[0].Begin_Day_of_Month) == 1
    assert int(rps[0].End_Month) == 12 and int(rps[0].End_Day_of_Month) == 31


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_purge_and_patch_real_hospital():
    path = config.BASELINE_IDF_DIR / layout_assigner.ARCHETYPE_IDF_MAP["Hospital"]
    idf = GeomIDF(str(path))

    layout_assigner.purge_baseline_outputs(idf)
    for cls in _OUTPUT_LIKE_CLASSES:
        assert len(idf.idfobjects[cls]) == 0, f"{cls} not purged"

    layout_assigner.patch_location_and_weather(idf, SYNTHETIC_EPW)
    locs = idf.idfobjects["SITE:LOCATION"]
    assert len(locs) == 1
    assert locs[0].Name == "Montreal"
    rps = idf.idfobjects["RUNPERIOD"]
    assert len(rps) == 1
    assert int(rps[0].Begin_Month) == 1 and int(rps[0].Begin_Day_of_Month) == 1
    assert int(rps[0].End_Month) == 12 and int(rps[0].End_Day_of_Month) == 31


# ── T07 — builder.py layout_assign branch (end-to-end) ───────────────────────

def _make_layout_assign_row(archetype_id: str, epw: Path | None = None,
                             footprint_area_m2: float = 800.0, levels: int = 4) -> pd.Series:
    return pd.Series({
        "osm_id": "way/la_e2e_1",
        "archetype_id": archetype_id,
        "epw_path": str(epw) if epw else "",
        "geometry": shapely.geometry.box(0, 0, 20, 40),  # 800 m2
        "footprint_area_m2": footprint_area_m2,
        "levels": levels,
        "height_m": levels * 3.5,
        "data_quality_flag": "",
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
    })


_MANIFEST_STANDARD_KEYS = (
    "osm_id", "idf_path", "archetype_id", "zoning_strategy", "num_zones",
    "num_context_buildings", "simplification_status", "data_quality_flag",
    "generation_status", "resolution_mode",
)


@pytest.mark.skipif(not config.BASELINE_IDF_DIR.exists(), reason="external baseline library not present")
def test_build_layout_assign_real_baseline_e2e(tmp_path):
    row = _make_layout_assign_row("MidriseApartment", SYNTHETIC_EPW)
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row, resolution_mode="layout_assign")
    (tmp_path / "idfs").mkdir()

    manifest = bidf.build(gdf, {}, tmp_path)

    for key in _MANIFEST_STANDARD_KEYS:
        assert key in manifest, f"manifest missing standard key {key!r}"
    assert manifest["zoning_strategy"] == "layout_assign"
    assert manifest["generation_status"] == "success"
    assert manifest["num_zones"] > 0
    assert manifest["num_context_buildings"] == 0
    assert manifest["resolution_mode"] == "layout_assign"
    assert "layout_assign_fallback_auto" not in manifest["data_quality_flag"]
    idf_path = Path(manifest["idf_path"])
    assert idf_path.exists()

    saved = GeomIDF(str(idf_path))
    assert len(saved.idfobjects["ZONE"]) == manifest["num_zones"]
    assert len(saved.idfobjects["OUTPUT:VARIABLE"]) > 0  # written by write_outputs(), not the purged baseline set
    assert saved.idfobjects["SITE:LOCATION"][0].Name == "Montreal"


def test_build_layout_assign_fallback_courthouse_e2e(tmp_path):
    row = _make_layout_assign_row("Courthouse", SYNTHETIC_EPW)
    gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
    bidf = BuildingIDF(row, resolution_mode="layout_assign")
    (tmp_path / "idfs").mkdir()

    manifest = bidf.build(gdf, {}, tmp_path)

    for key in _MANIFEST_STANDARD_KEYS:
        assert key in manifest, f"manifest missing standard key {key!r}"
    assert manifest["generation_status"] == "success"
    assert "layout_assign_fallback_auto" in manifest["data_quality_flag"]
    assert manifest["zoning_strategy"] != "layout_assign"
    assert Path(manifest["idf_path"]).exists()
