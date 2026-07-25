"""Unit tests for layout_assigner module and zoning integration (LayoutAssigner arc T01-T05)."""

import importlib
import logging
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
