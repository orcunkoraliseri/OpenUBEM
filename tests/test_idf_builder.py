"""Tests for config (T02), templates (T03), builder skeleton (T08), constructions (T10), loads (T11)."""
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem import config
from openubem.config import (
    DP_COARSE_TOLERANCE_M,
    DP_TOLERANCE_M,
    ENERGYPLUS_IDD_PATH,
    FLOOR_TO_FLOOR_M,
    MAX_VERTICES,
    PERIMETER_DEPTH_M,
    SHADING_SPHERE_RADIUS,
)
from openubem.idf.builder import (
    TEMPLATE_ROUTING,
    BuildingIDF,
    _parse_epw_location,
    _repair_oversized_epbunch_objls,
)


def _idf_setiddname_safe():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


_idf_setiddname_safe()

TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"
TEMPLATE_NAMES = [
    "commercial_base.idf",
    "residential_base.idf",
    "highrise_base.idf",
    "specialized_base.idf",
]


class TestConfig:
    def test_constants_match_spec(self):
        assert SHADING_SPHERE_RADIUS == 30.0
        assert DP_TOLERANCE_M == 0.5
        assert DP_COARSE_TOLERANCE_M == 1.5
        assert MAX_VERTICES == 120
        assert FLOOR_TO_FLOOR_M == 3.5
        assert PERIMETER_DEPTH_M == 4.57

    def test_idd_path_is_path_object(self):
        assert isinstance(ENERGYPLUS_IDD_PATH, Path)

    def test_env_var_override(self, monkeypatch):
        tmpdir = tempfile.mkdtemp()
        try:
            fake_idd = Path(tmpdir) / "fake.idd"
            fake_idd.write_text("")
            monkeypatch.setenv("OPENUBEM_ENERGYPLUS_IDD_PATH", str(fake_idd))
            from openubem.config import _resolve_idd_path
            result = _resolve_idd_path()
            assert result == fake_idd
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestTemplates:
    def test_all_four_files_exist(self):
        for name in TEMPLATE_NAMES:
            assert (TEMPLATES_DIR / name).exists(), f"Missing template: {name}"

    def test_templates_parse_with_eppy(self):
        for name in TEMPLATE_NAMES:
            path = TEMPLATES_DIR / name
            idf = IDF(str(path))
            assert idf is not None

    def test_each_template_has_seven_object_types(self):
        required = {
            "VERSION",
            "SIMULATIONCONTROL",
            "RUNPERIOD",
            "TIMESTEP",
            "SITE:LOCATION",
            "GLOBALGEOMETRYRULES",
            "SCHEDULE:CONSTANT",
        }
        for name in TEMPLATE_NAMES:
            idf = IDF(str(TEMPLATES_DIR / name))
            present = {k for k, v in idf.idfobjects.items() if v}
            assert required.issubset(present), f"{name} missing: {required - present}"

    def test_activity_level_schedule_value(self):
        for name in TEMPLATE_NAMES:
            idf = IDF(str(TEMPLATES_DIR / name))
            schedules = idf.idfobjects["SCHEDULE:CONSTANT"]
            act = next((s for s in schedules if s.Name == "Activity_Level"), None)
            assert act is not None, f"{name}: Activity_Level schedule missing"
            assert float(act.Hourly_Value) == 120.0

    def test_each_template_has_exactly_one_building_object(self):
        """B1: Building object required by EnergyPlus, North Axis 0 (R1)."""
        for name in TEMPLATE_NAMES:
            idf = IDF(str(TEMPLATES_DIR / name))
            buildings = idf.idfobjects["BUILDING"]
            assert len(buildings) == 1, f"{name}: expected 1 BUILDING, got {len(buildings)}"
            b = buildings[0]
            assert float(b.North_Axis) == 0.0, f"{name}: North_Axis should be 0"


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SYNTHETIC_EPW = FIXTURES_DIR / "synthetic.epw"

_ALL_30_ARCHETYPES = [
    "SmallOffice", "MediumOffice", "LargeOffice", "SmallOfficeDetailed",
    "MediumOfficeDetailed", "LargeOfficeDetailed", "RetailStandalone",
    "RetailStripmall", "PrimarySchool", "SecondarySchool", "Outpatient",
    "Hospital", "SmallHotel", "LargeHotel", "QuickServiceRestaurant",
    "FullServiceRestaurant", "MidriseApartment", "HighriseApartment",
    "TallBuilding", "SuperTallBuilding", "Laboratory", "Warehouse",
    "SmallDataCenterHighITE", "LargeDataCenterHighITE",
    "SmallDataCenterLowITE", "LargeDataCenterLowITE",
    "NonResidentialMixed", "ResidentialMixed", "Industrial", "OpenUBEMUnknown",
]

_COMMERCIAL_DEFAULT = {
    "MediumOffice", "SmallOffice", "LargeOffice", "SmallOfficeDetailed",
    "MediumOfficeDetailed", "LargeOfficeDetailed", "RetailStandalone",
    "RetailStripmall", "PrimarySchool", "SecondarySchool", "Outpatient",
    "Hospital", "SmallHotel", "LargeHotel", "QuickServiceRestaurant",
    "FullServiceRestaurant", "NonResidentialMixed", "ResidentialMixed",
    "Industrial", "OpenUBEMUnknown",
}


def _make_row(archetype_id: str = "MediumOffice", epw: Path | None = None) -> pd.Series:
    return pd.Series({
        "osm_id": "way/123",
        "archetype_id": archetype_id,
        "epw_path": str(epw) if epw else "",
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


class TestBuildingIDFInit:
    def test_double_import_no_raise(self):
        import importlib
        import openubem.idf.builder as m
        importlib.reload(m)  # second setiddname should be caught by try/except

    def test_template_routing_covers_all_30_archetypes(self):
        for arch in _ALL_30_ARCHETYPES:
            tpl = TEMPLATE_ROUTING.get(arch, "commercial_base.idf")
            assert tpl.endswith(".idf"), f"{arch} maps to non-idf: {tpl}"

    def test_commercial_default_routes_correctly(self):
        for arch in _COMMERCIAL_DEFAULT:
            tpl = TEMPLATE_ROUTING.get(arch, "commercial_base.idf")
            assert tpl == "commercial_base.idf", f"{arch} should map to commercial_base.idf"

    def test_parse_epw_location_returns_correct_tuple(self):
        city, lat, lon, tz, elev = _parse_epw_location(SYNTHETIC_EPW)
        assert city == "Montreal"
        assert abs(lat - 45.47) < 1e-6
        assert abs(lon - (-73.75)) < 1e-6
        assert abs(tz - (-5.0)) < 1e-6
        assert abs(elev - 36.0) < 1e-6

    def test_buildingidf_init_sets_site_location(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        loc = bidf.idf.idfobjects["SITE:LOCATION"][0]
        assert loc.Name == "Montreal"
        assert abs(float(loc.Latitude) - 45.47) < 1e-4


# ── structural-fixes T03 — thermal_mass default resolution (E-LA-07-class-2/E-LA-08) ──

class TestThermalMassDefaultResolution:
    def test_layout_assign_defaults_thermal_mass_true(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        assert BuildingIDF(row, resolution_mode="layout_assign").thermal_mass is True

    def test_layout_assigner_alias_also_defaults_true(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        assert BuildingIDF(row, resolution_mode="layout_assigner").thermal_mass is True

    def test_auto_mode_defaults_thermal_mass_false(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        assert BuildingIDF(row, resolution_mode="auto").thermal_mass is False

    def test_building_mode_defaults_thermal_mass_false(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        assert BuildingIDF(row, resolution_mode="building").thermal_mass is False

    def test_default_constructor_call_defaults_thermal_mass_false(self):
        """No resolution_mode passed at all -> falls back to 'auto' -> False, unchanged behavior."""
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        assert BuildingIDF(row).thermal_mass is False

    def test_explicit_false_override_respected_for_layout_assign(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        bidf = BuildingIDF(row, thermal_mass=False, resolution_mode="layout_assign")
        assert bidf.thermal_mass is False

    def test_explicit_true_override_respected_for_auto(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        bidf = BuildingIDF(row, thermal_mass=True, resolution_mode="auto")
        assert bidf.thermal_mass is True


class TestOversizedEpBunchRepair:
    """E-LA-09/E-LA-13: eppy's EpBunch.__repr__ zip-truncates any object whose
    stored value count (obj) exceeds its field-name/comment list (objls),
    silently dropping the excess AND the correctly ';'-terminated final line.
    """

    def _make_idf(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        return BuildingIDF(row).idf

    def test_repair_pads_objls_to_match_oversized_obj(self):
        idf = self._make_idf()
        obj = idf.newidfobject("CONTROLLER:MECHANICALVENTILATION", Name="Test_DCV")
        obj.objls[:] = obj.objls[:4]
        obj.obj.extend(["ExtraZone0", "ExtraZone1", "ExtraZone2"])
        assert len(obj.obj) > len(obj.objls)

        n_repaired = _repair_oversized_epbunch_objls(idf)

        assert n_repaired >= 1
        assert len(obj.objls) >= len(obj.obj)

    def test_repair_is_a_noop_for_well_formed_objects(self):
        idf = self._make_idf()
        obj = idf.newidfobject("CONTROLLER:MECHANICALVENTILATION", Name="Test_DCV")
        before = list(obj.objls)

        n_repaired = _repair_oversized_epbunch_objls(idf)

        assert n_repaired == 0
        assert obj.objls == before

    def test_oversized_object_no_longer_truncates_on_save(self, tmp_path):
        idf = self._make_idf()
        obj = idf.newidfobject("CONTROLLER:MECHANICALVENTILATION", Name="Test_DCV")
        # Simulate the general E-LA-13 bug shape (objls shorter than obj) directly,
        # per T08's own test instruction ("construct or load an object where
        # len(obj.obj) > len(obj.objls)").
        obj.objls[:] = obj.objls[:4]
        sentinel = "SENTINEL_LAST_VALUE"
        obj.obj.extend(["ExtraZone0", "ExtraZone1", sentinel])

        _repair_oversized_epbunch_objls(idf)
        out_path = tmp_path / "oversized_repaired.idf"
        idf.save(str(out_path))
        text = out_path.read_text(encoding="utf-8", errors="replace")

        idx = text.find(sentinel)
        assert idx != -1, "sentinel value dropped by idf.save() -- repair did not fix truncation"
        line = text[idx: idx + 80].split("\n")[0]
        value_part = line.split("!-")[0].strip()
        assert value_part.endswith(";"), f"expected ';' terminator, got: {value_part!r}"

    def test_without_repair_oversized_object_truncates_on_save(self, tmp_path):
        """Negative control: confirms the synthetic repro is meaningful (the bug
        is real without the fix), not a tautology."""
        idf = self._make_idf()
        obj = idf.newidfobject("CONTROLLER:MECHANICALVENTILATION", Name="Test_DCV")
        obj.objls[:] = obj.objls[:4]
        sentinel = "SENTINEL_UNFIXED"
        obj.obj.extend(["ExtraZone0", "ExtraZone1", sentinel])

        out_path = tmp_path / "oversized_unfixed.idf"
        idf.save(str(out_path))
        text = out_path.read_text(encoding="utf-8", errors="replace")

        assert sentinel not in text, "expected the unrepaired object to silently drop the sentinel"


class TestConstructions:
    def _make_idf_with_constructions(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        from shapely.geometry import box
        sq = box(0, 0, 10, 10)
        # Add a minimal zone so set_wwr has surfaces to operate on.
        coords = list(sq.exterior.coords)[:-1]
        bidf.idf.add_block(name="way/123_F0_whole", coordinates=coords, height=3.5, num_stories=1)
        bidf.idf.intersect_match()
        bidf.assign_constructions()
        return bidf.idf, row

    def test_nomass_count_and_values(self):
        idf, row = self._make_idf_with_constructions()
        nomasses = idf.idfobjects["MATERIAL:NOMASS"]
        assert len(nomasses) == 3
        by_name = {m.Name: m for m in nomasses}
        assert abs(float(by_name["Roof_Assembly"].Thermal_Resistance) - 1.0 / 0.2) < 1e-6
        assert abs(float(by_name["Wall_Assembly"].Thermal_Resistance) - 1.0 / 0.3) < 1e-6
        assert abs(float(by_name["Floor_Assembly"].Thermal_Resistance) - 1.0 / 0.4) < 1e-6

    def test_constructions_count(self):
        idf, _ = self._make_idf_with_constructions()
        constructions = idf.idfobjects["CONSTRUCTION"]
        names = {c.Name for c in constructions}
        assert "Roof_Construction" in names
        assert "Wall_Construction" in names
        assert "Floor_Construction" in names
        assert "Window_Construction" in names

    def test_window_material(self):
        idf, row = self._make_idf_with_constructions()
        glazing = idf.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"]
        # set_default_constructions() may add a DefaultGlazing; find ours by name.
        our = next(g for g in glazing if g.Name == "Window_Material")
        assert abs(float(our.UFactor) - 2.5) < 1e-6
        assert abs(float(our.Solar_Heat_Gain_Coefficient) - 0.4) < 1e-6
        assert abs(float(our.Visible_Transmittance) - 0.6) < 1e-6

    def test_wwr_creates_fenestration(self):
        idf, _ = self._make_idf_with_constructions()
        fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
        assert len(fen) > 0

    def test_wwr_window_construction_name(self):
        """B2: every fenestration surface must reference Window_Construction (W3.3)."""
        idf, _ = self._make_idf_with_constructions()
        fen = idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]
        assert len(fen) > 0, "no fenestration surfaces found"
        for f in fen:
            assert f.Construction_Name == "Window_Construction", (
                f"fenestration {f.Name} has Construction_Name={f.Construction_Name!r}"
            )

    def test_surface_construction_wired(self):
        """B3: archetype constructions wired to opaque surfaces; no geomeppy default survives."""
        idf, _ = self._make_idf_with_constructions()
        wall_surfaces = [
            s for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
            if s.Surface_Type.lower() == "wall"
        ]
        assert len(wall_surfaces) > 0, "no wall surfaces found"
        assert any(s.Construction_Name == "Wall_Construction" for s in wall_surfaces), (
            "no wall surface references Wall_Construction"
        )
        for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
            assert s.Construction_Name != "Project Wall", (
                f"surface {s.Name} still references geomeppy default 'Project Wall'"
            )

    def test_infiltration_per_zone(self):
        row = _make_row("MediumOffice", SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        from shapely.geometry import box
        sq = box(0, 0, 10, 10)
        coords = list(sq.exterior.coords)[:-1]
        bidf.idf.add_block(name="way/123_F0_whole", coordinates=coords, height=3.5, num_stories=1)
        bidf.idf.intersect_match()
        zones = [
            {"name": "way/123_F0_whole"},
            {"name": "way/123_F1_whole"},
            {"name": "way/123_F2_whole"},
        ]
        bidf.assign_infiltration(zones)
        infil = bidf.idf.idfobjects["ZONEINFILTRATION:DESIGNFLOWRATE"]
        assert len(infil) == 3
        for obj in infil:
            assert obj.Schedule_Name == "Infiltration_Schedule_MediumOffice"
            # Field renamed in EnergyPlus 23.1 IDD (W3.7): Flow_per_Exterior_Surface_Area → Flow_Rate_per_Exterior_Surface_Area
            assert abs(float(obj.Flow_Rate_per_Exterior_Surface_Area) - 0.0003) < 1e-9


class TestLoads:
    def _make_stub_library(self, arch: str) -> dict:
        """Build a minimal schedule library with constant-value stubs."""
        from importlib.resources import files as _files
        tpl_path = str(_files("openubem.idf").joinpath("templates").joinpath("commercial_base.idf"))
        tmp_idf = IDF(tpl_path)
        families = {
            "lighting": f"Lighting_Schedule_{arch}",
            "equipment": f"Equipment_Schedule_{arch}",
            "occupancy": f"Occupancy_Schedule_{arch}",
            "heating_setpoint": f"Heating_Setpoint_{arch}",
            "cooling_setpoint": f"Cooling_Setpoint_{arch}",
            "infiltration": f"Infiltration_Schedule_{arch}",
        }
        stubs_by_family: dict[str, list] = {}
        for family, sched_name in families.items():
            obj = tmp_idf.newidfobject(
                "SCHEDULE:COMPACT",
                Name=sched_name,
                Schedule_Type_Limits_Name="Fraction",
                Field_1="Through: 12/31",
                Field_2="For: AllDays",
                Field_3="Until: 24:00",
                Field_4="1.0",
            )
            stubs_by_family[family] = [obj]
        return {arch: stubs_by_family}

    def test_copy_schedule_library(self):
        arch = "MediumOffice"
        row = _make_row(arch, SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        lib = self._make_stub_library(arch)
        bidf.copy_schedule_library(arch, lib)
        compact = bidf.idf.idfobjects["SCHEDULE:COMPACT"]
        names = {s.Name for s in compact}
        assert f"Lighting_Schedule_{arch}" in names
        assert len([s for s in compact if arch in s.Name]) == 6

    def test_assign_loads_two_zones(self):
        arch = "MediumOffice"
        row = _make_row(arch, SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        lib = self._make_stub_library(arch)
        bidf.copy_schedule_library(arch, lib)
        zones = [
            {"name": "way/123_F0_whole", "archetype_id": arch},
            {"name": "way/123_F1_whole", "archetype_id": arch},
        ]
        bidf.assign_loads(zones)
        assert len(bidf.idf.idfobjects["PEOPLE"]) == 2
        assert len(bidf.idf.idfobjects["LIGHTS"]) == 2
        assert len(bidf.idf.idfobjects["ELECTRICEQUIPMENT"]) == 2
        assert len(bidf.idf.idfobjects["HVACTEMPLATE:THERMOSTAT"]) == 2

    def test_loads_field_values(self):
        arch = "MediumOffice"
        row = _make_row(arch, SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        lib = self._make_stub_library(arch)
        bidf.copy_schedule_library(arch, lib)
        zones = [{"name": "way/123_F0_whole", "archetype_id": arch}]
        bidf.assign_loads(zones)
        people = bidf.idf.idfobjects["PEOPLE"][0]
        # Field renamed in EnergyPlus 23.1 IDD (W3.7): People_per_Zone_Floor_Area → People_per_Floor_Area
        assert abs(float(people.People_per_Floor_Area) - 1.0 / 10.0) < 1e-9
        assert people.Activity_Level_Schedule_Name == "Activity_Level"
        assert abs(float(people.Fraction_Radiant) - 0.3) < 1e-9
        lights = bidf.idf.idfobjects["LIGHTS"][0]
        assert abs(float(lights.Watts_per_Zone_Floor_Area) - 10.0) < 1e-9
        assert abs(float(lights.Fraction_Radiant) - 0.42) < 1e-9
        equip = bidf.idf.idfobjects["ELECTRICEQUIPMENT"][0]
        assert abs(float(equip.Fraction_Radiant) - 0.5) < 1e-9

    def test_activity_level_schedule_name(self):
        arch = "MediumOffice"
        row = _make_row(arch, SYNTHETIC_EPW)
        bidf = BuildingIDF(row)
        lib = self._make_stub_library(arch)
        bidf.copy_schedule_library(arch, lib)
        zones = [{"name": "way/123_F0_whole", "archetype_id": arch}]
        bidf.assign_loads(zones)
        people = bidf.idf.idfobjects["PEOPLE"][0]
        assert people.Activity_Level_Schedule_Name == "Activity_Level"


class TestZoningAreaColumn:
    """B5: zoning decision uses footprint_area_m2 column, not simplified poly area (W3.8)."""

    def test_zoning_follows_column_not_poly_area(self, monkeypatch):
        """footprint_area_m2 passed to decide_zoning_strategy is from the column, not poly.area."""
        import tempfile
        import geopandas as gpd
        from shapely.geometry import box as _box
        from openubem.geometry.zoning import decide_zoning_strategy

        captured: dict = {}

        def recording_decide(arch, area, floors, resolution_mode="auto"):
            captured["area"] = area
            return decide_zoning_strategy(arch, area, floors, resolution_mode)

        monkeypatch.setattr("openubem.idf.builder.decide_zoning_strategy", recording_decide)

        arch = "MediumOffice"
        poly = _box(0, 0, 50, 50)  # area = 2500 m² → would give perimeter_core if used directly
        row = _make_row(arch, SYNTHETIC_EPW)
        row["osm_id"] = "way/555"
        row["levels"] = 3
        row["height_m"] = 10.5
        # 499 m² < 500 threshold → one_zone_per_floor (multi-floor, post-fix);
        # key assertion is that the column value 499.0 is what reaches the function, not poly.area
        row["footprint_area_m2"] = 499.0
        row["geometry"] = poly
        row["data_quality_flag"] = ""

        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")
        bidf = BuildingIDF(row)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            (out_path / "idfs").mkdir()
            bidf.build(gdf, {}, out_path)

        assert abs(captured["area"] - 499.0) < 1e-6, (
            f"decide_zoning_strategy was called with area={captured['area']!r}, expected 499.0"
        )


class TestDoubleExtrusionFailure:
    """B4: zones whose footprint group fails both primary and bbox extrusion are excluded."""

    def test_double_failure_excluded_from_loads_and_manifest(self, monkeypatch):
        import tempfile
        import geopandas as gpd
        from shapely.geometry import box as _box

        arch = "MediumOffice"
        poly = _box(0, 0, 50, 50)
        row = _make_row(arch, SYNTHETIC_EPW)
        row["osm_id"] = "way/999"
        row["levels"] = 2
        row["height_m"] = 7.0
        row["footprint_area_m2"] = float(poly.area)
        row["geometry"] = poly
        row["data_quality_flag"] = ""

        gdf = gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:32618")

        bidf = BuildingIDF(row)

        # C2 (R7): MediumOffice 50×50 2-floor goes through core/perim native path.
        # Fail ALL add_block calls so both the core/perim attempt and its per-floor
        # fallback both raise → no zones extruded → num_zones == 0 in manifest.
        def always_fail(*args, **kwargs):
            raise ValueError("simulated total add_block failure")

        monkeypatch.setattr(bidf.idf, "add_block", always_fail)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            (out_path / "idfs").mkdir()
            manifest = bidf.build(gdf, {}, out_path)

        # No zones extruded → PEOPLE/LIGHTS/HVAC should reference nothing.
        # Field renamed in EnergyPlus 23.1 IDD (W3.7): Zone_or_ZoneList_or_Space_or_SpaceList_Name
        people_zones = {p.Zone_or_ZoneList_or_Space_or_SpaceList_Name for p in bidf.idf.idfobjects["PEOPLE"]}
        lights_zones = {l.Zone_or_ZoneList_or_Space_or_SpaceList_Name for l in bidf.idf.idfobjects["LIGHTS"]}
        hvac_zones = {h.Zone_Name for h in bidf.idf.idfobjects["HVACTEMPLATE:ZONE:PTAC"]}
        assert people_zones == set(), f"PEOPLE references zones despite extrusion failure: {people_zones}"
        assert lights_zones == set(), f"LIGHTS references zones despite extrusion failure: {lights_zones}"
        assert hvac_zones == set(), f"HVAC references zones despite extrusion failure: {hvac_zones}"
        assert manifest["num_zones"] == 0, f"expected num_zones==0, got {manifest['num_zones']}"
