"""End-to-end Step 3 orchestrator tests (T14/T16). Validates DESIGN §5.1 CI thresholds."""
import shutil
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError
from shapely.geometry import box
from shapely.geometry import Polygon as _SPoly

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.builder import run_step3, _build_one, BuildingIDF

_TEMPLATES_DIR = Path(__file__).parent.parent / "openubem" / "idf" / "templates"


def _idd_safe():
    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass


_idd_safe()

_MANIFEST_COLUMNS = {
    "osm_id", "idf_path", "archetype_id", "zoning_strategy",
    "num_zones", "num_context_buildings", "simplification_status",
    "data_quality_flag", "generation_status",
}

_VALID_ZONING = {"single_zone", "one_zone_per_floor", "perimeter_core", ""}
_VALID_STATUS = {"dp_05", "dp_15", "hull", "bbox", "skip"}
_VALID_GEN = {"success", "skipped_invalid_geometry", "fallback_bbox"}


class TestStep3Orchestrator:
    def _run(self, synthetic_10_gdf, synthetic_schedule_library):
        tmpdir = tempfile.mkdtemp()
        try:
            manifest = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir))
            return manifest, tmpdir
        except Exception:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise

    def test_end_to_end_produces_10_idfs_and_manifest(
        self, synthetic_10_gdf, synthetic_schedule_library
    ):
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            assert len(manifest) == 10
            idf_dir = Path(tmpdir) / "idfs"
            idf_files = list(idf_dir.glob("*.idf"))
            # Count successful rows
            n_success = manifest[manifest["generation_status"] != "skipped_invalid_geometry"].shape[0]
            assert len(idf_files) == n_success
            assert (Path(tmpdir) / "03_idf_manifest.parquet").exists()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_manifest_schema(self, synthetic_10_gdf, synthetic_schedule_library):
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            assert set(manifest.columns) >= _MANIFEST_COLUMNS
            for col in ("num_zones", "num_context_buildings"):
                assert pd.api.types.is_integer_dtype(manifest[col]) or manifest[col].dtype in (
                    "int64", "int32", "object"
                ), f"{col} should be numeric"
            assert manifest["zoning_strategy"].isin(_VALID_ZONING).all()
            assert manifest["simplification_status"].isin(_VALID_STATUS).all()
            assert manifest["generation_status"].isin(_VALID_GEN).all()
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_pct_valid_idf_generated_100(self, synthetic_10_gdf, synthetic_schedule_library):
        """All synthetic fixture rows must produce valid IDFs (DESIGN §5.1 line 485)."""
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            success_rows = manifest[manifest["generation_status"] != "skipped_invalid_geometry"]
            assert len(success_rows) == 10, "All 10 synthetic buildings should succeed"
            for idf_path in success_rows["idf_path"]:
                assert Path(idf_path).exists(), f"IDF file missing: {idf_path}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_idf_syntax_validity(self, synthetic_10_gdf, synthetic_schedule_library):
        """Every emitted IDF must parse without error (DESIGN §5.1 line 484)."""
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            for idf_path in manifest["idf_path"]:
                if not idf_path:
                    continue
                idf = IDF(idf_path)
                assert idf is not None
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_pct_vertex_compliant_100(self, synthetic_10_gdf, synthetic_schedule_library):
        """Every BuildingSurface:Detailed must have ≤120 vertices (DESIGN §5.1 line 486)."""
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            for idf_path in manifest["idf_path"]:
                if not idf_path:
                    continue
                idf = IDF(idf_path)
                for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
                    # Count vertices: fields Vertex_1_Xcoordinate, Vertex_1_Ycoordinate, ...
                    n_verts = 0
                    for field in surf.fieldnames:
                        if field.startswith("Vertex_") and field.endswith("_Xcoordinate"):
                            n_verts += 1
                    assert n_verts <= 120, (
                        f"{Path(idf_path).name}: surface {surf.Name} has {n_verts} vertices (>120)"
                    )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_manifest_parquet_round_trip(self, synthetic_10_gdf, synthetic_schedule_library):
        """Manifest written as parquet can be read back with identical contents."""
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            reloaded = pd.read_parquet(Path(tmpdir) / "03_idf_manifest.parquet")
            assert list(reloaded.columns) == list(manifest.columns)
            assert len(reloaded) == len(manifest)
            assert list(reloaded["osm_id"]) == list(manifest["osm_id"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_idempotency(self, synthetic_10_gdf, synthetic_schedule_library):
        """Running run_step3 twice produces structurally identical manifests."""
        tmpdir1 = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        try:
            m1 = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir1))
            m2 = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir2))
            # Compare structural fields (not paths, which differ by tmpdir)
            for col in ("osm_id", "archetype_id", "zoning_strategy", "num_zones",
                        "simplification_status", "generation_status"):
                assert list(m1[col]) == list(m2[col]), f"Column {col} differs between runs"
        finally:
            shutil.rmtree(tmpdir1, ignore_errors=True)
            shutil.rmtree(tmpdir2, ignore_errors=True)

    def test_multi_floor_surfaces_at_correct_z(self, synthetic_10_gdf, synthetic_schedule_library):
        """R2 (C1): add_block(num_stories=N) stacks surfaces at true z heights.

        With the one-block-per-footprint approach, ZONE.Z_Origin stays 0 (geomeppy default)
        but upper-storey floor surfaces must have min z > 0.
        """
        manifest, tmpdir = self._run(synthetic_10_gdf, synthetic_schedule_library)
        try:
            # MidriseApartment (R2) has 4 floors → upper-storey floor surfaces at z=3.5, 7.0, 10.5
            r2_row = manifest[manifest["osm_id"] == "way/R2"].iloc[0]
            idf = IDF(r2_row["idf_path"])
            bsds = idf.idfobjects["BUILDINGSURFACE:DETAILED"]
            floor_z_mins = [
                min(pt[2] for pt in s.coords)
                for s in bsds
                if s.Surface_Type.lower() == "floor"
            ]
            # At least one floor surface must be at z > 0 (an upper storey floor)
            assert any(z > 0 for z in floor_z_mins), (
                f"All floor surfaces at z=0 — stacking failed: {floor_z_mins}"
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestParallelByteIdentity:
    """C10 / V09: n_jobs=1 and n_jobs=4 must produce byte-identical IDFs + identical manifests."""

    def test_parallel_byte_identity(self, synthetic_10_gdf, synthetic_schedule_library):
        tmpdir1 = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        try:
            m1 = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir1), n_jobs=1)
            m2 = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir2), n_jobs=4)

            # Manifest identity (excluding path columns that encode tmpdir)
            for col in ("osm_id", "archetype_id", "zoning_strategy", "num_zones",
                        "num_context_buildings", "simplification_status",
                        "data_quality_flag", "generation_status"):
                assert list(m1[col]) == list(m2[col]), f"Column '{col}' differs n_jobs=1 vs 4"

            # IDF byte-identity
            idfs1 = {p.name: p.read_bytes() for p in (Path(tmpdir1) / "idfs").glob("*.idf")}
            idfs2 = {p.name: p.read_bytes() for p in (Path(tmpdir2) / "idfs").glob("*.idf")}
            assert set(idfs1) == set(idfs2), "IDF filename sets differ between n_jobs=1 and n_jobs=4"
            for name in idfs1:
                assert idfs1[name] == idfs2[name], f"IDF bytes differ for {name}"
        finally:
            shutil.rmtree(tmpdir1, ignore_errors=True)
            shutil.rmtree(tmpdir2, ignore_errors=True)


class TestResolutionModes:
    """T05 — run_step3 per-mode integration on synthetic_10."""

    def test_building_mode_all_single_zone(self, synthetic_10_gdf, synthetic_schedule_library):
        tmpdir = tempfile.mkdtemp()
        try:
            manifest = run_step3(
                synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir), resolution_mode="building"
            )
            success = manifest[manifest["generation_status"] == "success"]
            bad = success[success["zoning_strategy"] != "single_zone"]
            assert bad.empty, f"Non-single_zone rows under building mode: {bad[['osm_id','zoning_strategy']]}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_floor_mode_all_one_zone_per_floor(self, synthetic_10_gdf, synthetic_schedule_library):
        tmpdir = tempfile.mkdtemp()
        try:
            manifest = run_step3(
                synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir), resolution_mode="floor"
            )
            success = manifest[manifest["generation_status"] == "success"]
            bad = success[success["zoning_strategy"] != "one_zone_per_floor"]
            assert bad.empty, f"Non-one_zone_per_floor rows under floor mode: {bad[['osm_id','zoning_strategy']]}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_fast_zone_mode_perimeter_core_or_fallback(self, synthetic_10_gdf, synthetic_schedule_library):
        # F4/F5 fallbacks (narrow/courtyard) may yield one_zone_per_floor; both are valid
        tmpdir = tempfile.mkdtemp()
        try:
            manifest = run_step3(
                synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir), resolution_mode="fast_zone"
            )
            success = manifest[manifest["generation_status"] == "success"]
            valid = {"perimeter_core", "one_zone_per_floor"}
            bad = success[~success["zoning_strategy"].isin(valid)]
            assert bad.empty, f"Unexpected strategy under fast_zone: {bad[['osm_id','zoning_strategy']]}"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_resolution_mode_column_propagated(self, synthetic_10_gdf, synthetic_schedule_library):
        for mode in ("building", "floor", "fast_zone"):
            tmpdir = tempfile.mkdtemp()
            try:
                manifest = run_step3(
                    synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir), resolution_mode=mode
                )
                assert "resolution_mode" in manifest.columns, (
                    f"resolution_mode column missing for mode={mode!r}"
                )
                assert (manifest["resolution_mode"] == mode).all(), (
                    f"resolution_mode column wrong for mode={mode!r}: {manifest['resolution_mode'].unique()}"
                )
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

    def test_num_zones_ordering_building_le_floor_le_fast_zone(
        self, synthetic_10_gdf, synthetic_schedule_library
    ):
        """Per building: num_zones(building) ≤ num_zones(floor) ≤ num_zones(fast_zone)."""
        tmpdirs = {m: tempfile.mkdtemp() for m in ("building", "floor", "fast_zone")}
        try:
            manifests = {
                m: run_step3(
                    synthetic_10_gdf, synthetic_schedule_library, Path(tmpdirs[m]), resolution_mode=m
                )
                for m in ("building", "floor", "fast_zone")
            }
            for osm_id in manifests["building"]["osm_id"]:
                b = manifests["building"].loc[
                    manifests["building"]["osm_id"] == osm_id, "num_zones"
                ].iloc[0]
                f = manifests["floor"].loc[
                    manifests["floor"]["osm_id"] == osm_id, "num_zones"
                ].iloc[0]
                fz = manifests["fast_zone"].loc[
                    manifests["fast_zone"]["osm_id"] == osm_id, "num_zones"
                ].iloc[0]
                assert b <= f, f"{osm_id}: building({b}) > floor({f})"
                assert f <= fz, f"{osm_id}: floor({f}) > fast_zone({fz})"
        finally:
            for td in tmpdirs.values():
                shutil.rmtree(td, ignore_errors=True)

    def test_auto_mode_regression(self, synthetic_10_gdf, synthetic_schedule_library):
        """resolution_mode='auto' must reproduce the default (no kwarg) manifest."""
        tmpdir_base = tempfile.mkdtemp()
        tmpdir_auto = tempfile.mkdtemp()
        try:
            m_base = run_step3(synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir_base))
            m_auto = run_step3(
                synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir_auto), resolution_mode="auto"
            )
            for col in ("zoning_strategy", "num_zones"):
                assert list(m_base[col]) == list(m_auto[col]), (
                    f"Column {col!r} differs: default vs resolution_mode='auto'"
                )
        finally:
            shutil.rmtree(tmpdir_base, ignore_errors=True)
            shutil.rmtree(tmpdir_auto, ignore_errors=True)

    def test_zone_mode_raises_before_fleet(self, synthetic_10_gdf, synthetic_schedule_library):
        """resolution_mode='zone' must raise NotImplementedError before the fleet loop (fail-fast)."""
        tmpdir = tempfile.mkdtemp()
        try:
            with pytest.raises(NotImplementedError):
                run_step3(
                    synthetic_10_gdf, synthetic_schedule_library, Path(tmpdir), resolution_mode="zone"
                )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_load_conservation_across_modes(tmp_path):
    """T05b — building totals identical across building/floor/fast_zone (F11/F13).

    Uses a 1-floor MediumOffice so Σ zone_areas equals the footprint in all three modes.
    Verifies F11 (area-normalised loads conserve totals) and F13 (absolute process loads once).
    """
    _EPW_PATH = str(Path(__file__).parent / "fixtures" / "synthetic.epw")
    _COMMON = {
        "osm_id": "cons_test", "archetype_id": "MediumOffice",
        "epw_path": _EPW_PATH, "provenance_climate_zone": "DEFAULT", "climate_zone": "3A",
        "vintage_standard": "DOERef1980to2004",
        "u_roof_w_m2k": 0.25, "u_wall_w_m2k": 0.40, "u_floor_w_m2k": 0.35,
        "u_window_w_m2k": 2.5, "shgc_window": 0.40,
        "assembly_roof": "NOMASS", "assembly_wall": "NOMASS",
        "provenance_u_roof": "DEFAULT", "provenance_u_wall": "DEFAULT",
        "provenance_u_window": "DEFAULT", "provenance_u_floor": "DEFAULT",
        "provenance_envelope": "DEFAULT",
        "infiltration_m3_s_m2": 0.0003, "wwr": 0.30,
        "lighting_w_m2": 10.76, "equipment_w_m2": 8.07, "occupant_m2_per_person": 9.3,
        "provenance_lighting": "DEFAULT", "provenance_equipment": "DEFAULT",
        "provenance_occupancy": "DEFAULT",
        "heating_setpoint_c": 21.0, "cooling_setpoint_c": 24.0,
        "heating_setback_c": 16.0, "cooling_setup_c": 30.0,
        "provenance_heating_setpoint": "DEFAULT", "provenance_cooling_setpoint": "DEFAULT",
        "data_quality_flag": "", "levels": 1, "height_m": float("nan"),
    }
    geom = box(0, 0, 30, 50)  # 1500 m², 1 floor → Σ zone_area identical across all modes (F11)
    gdf = gpd.GeoDataFrame([_COMMON], geometry=[geom])
    row = gdf.iloc[0]

    def _zone_areas(idf):
        za = {}
        for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
            if surf.Surface_Type.lower() == "floor":
                poly = _SPoly([(c[0], c[1]) for c in surf.coords])
                za[surf.Zone_Name] = za.get(surf.Zone_Name, 0) + abs(poly.area)
        return za

    def _sum_loads(objs, abs_methods, abs_attr, rate_attr, zone_attr, method_attr, za):
        """Sum installed loads, handling both absolute (Level) and Area-normalized methods.

        T08b: single_zone zones now carry floor_area_m2 and emit absolute design levels
        (LightingLevel/EquipmentLevel/People) even for num_floors==1 single_zone buildings
        (numerically identical total, different calc method) — so this must recognize both.
        """
        total = 0.0
        for obj in objs:
            method = getattr(obj, method_attr).lower()
            if method in abs_methods:
                total += float(getattr(obj, abs_attr))
            else:
                area = za.get(getattr(obj, zone_attr), 0.0)
                total += float(getattr(obj, rate_attr)) * area
        return total

    totals = {}
    wu_counts = {}
    for mode in ("building", "floor", "fast_zone"):
        out = tmp_path / mode
        out.mkdir()
        (out / "idfs").mkdir()
        result = BuildingIDF(row, resolution_mode=mode).build(gdf, {}, out)
        assert result["idf_path"], f"No IDF produced for mode={mode!r}"
        idf = IDF(result["idf_path"])
        za = _zone_areas(idf)

        lights_obj = [l for l in idf.idfobjects["LIGHTS"] if l.Name.startswith("Lights_")]
        equip_obj = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.Name.startswith("Equipment_")]
        people_obj = [p for p in idf.idfobjects["PEOPLE"] if p.Name.startswith("People_")]

        zone_key = "Zone_or_ZoneList_or_Space_or_SpaceList_Name"
        totals[mode] = {
            "lights": _sum_loads(
                lights_obj, {"lightinglevel"}, "Lighting_Level",
                "Watts_per_Zone_Floor_Area", zone_key, "Design_Level_Calculation_Method", za,
            ),
            "equip": _sum_loads(
                equip_obj, {"equipmentlevel"}, "Design_Level",
                "Watts_per_Zone_Floor_Area", zone_key, "Design_Level_Calculation_Method", za,
            ),
            "people": _sum_loads(
                people_obj, {"people"}, "Number_of_People",
                "People_per_Floor_Area", zone_key, "Number_of_People_Calculation_Method", za,
            ),
        }
        wu_counts[mode] = len(idf.idfobjects["WATERUSE:EQUIPMENT"])

    # F11: 1-floor → Σ zone_area = footprint in all modes → identical totals
    rel_tol = 1e-6
    ref = totals["floor"]
    for mode in ("building", "fast_zone"):
        for metric in ("lights", "equip", "people"):
            v, r = totals[mode][metric], ref[metric]
            assert abs(v - r) / max(abs(r), 1e-12) < rel_tol, (
                f"F11 violation: {metric} total differs — floor={r:.4f}, {mode}={v:.4f}"
            )

    # F13: absolute process load (WaterUse:Equipment) pinned to zones[0] → exactly once per mode
    for mode in ("building", "floor", "fast_zone"):
        assert wu_counts[mode] == 1, (
            f"F13 violation: WaterUse:Equipment count should be 1 in mode={mode!r}, got {wu_counts[mode]}"
        )


def test_load_conservation_across_modes_multifloor(tmp_path):
    """T08b CP-fix — multi-floor (num_floors=5) conservation across building/floor/fast_zone.

    Regression for M18: `single_zone` ("building" mode) used to emit only ONE floor's
    worth of area-normalized loads (zone floor area = footprint, not footprint × num_floors),
    so a 5-floor building got 0.200× the correct lights/equipment/people/process-load totals
    vs "floor"/"fast_zone". This is the blind spot the original (1-floor) T05b test missed.
    Uses FullServiceRestaurant so DHW + cooking (gas+elec) + refrigeration (lumped) all fire.
    """
    _EPW_PATH = str(Path(__file__).parent / "fixtures" / "synthetic.epw")
    _COMMON = {
        "osm_id": "cons_test_mf", "archetype_id": "FullServiceRestaurant",
        "epw_path": _EPW_PATH, "provenance_climate_zone": "DEFAULT", "climate_zone": "3A",
        "vintage_standard": "DOERef1980to2004",
        "u_roof_w_m2k": 0.25, "u_wall_w_m2k": 0.40, "u_floor_w_m2k": 0.35,
        "u_window_w_m2k": 2.5, "shgc_window": 0.40,
        "assembly_roof": "NOMASS", "assembly_wall": "NOMASS",
        "provenance_u_roof": "DEFAULT", "provenance_u_wall": "DEFAULT",
        "provenance_u_window": "DEFAULT", "provenance_u_floor": "DEFAULT",
        "provenance_envelope": "DEFAULT",
        "infiltration_m3_s_m2": 0.0003, "wwr": 0.30,
        "lighting_w_m2": 10.76, "equipment_w_m2": 8.07, "occupant_m2_per_person": 9.3,
        "provenance_lighting": "DEFAULT", "provenance_equipment": "DEFAULT",
        "provenance_occupancy": "DEFAULT",
        "heating_setpoint_c": 21.0, "cooling_setpoint_c": 24.0,
        "heating_setback_c": 16.0, "cooling_setup_c": 30.0,
        "provenance_heating_setpoint": "DEFAULT", "provenance_cooling_setpoint": "DEFAULT",
        "data_quality_flag": "", "levels": 5, "height_m": float("nan"),
    }
    geom = box(0, 0, 30, 50)  # 1500 m² footprint, 5 floors → 7500 m² total floor area
    gdf = gpd.GeoDataFrame([_COMMON], geometry=[geom])
    row = gdf.iloc[0]

    def _zone_areas(idf):
        za = {}
        for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
            if surf.Surface_Type.lower() == "floor":
                poly = _SPoly([(c[0], c[1]) for c in surf.coords])
                za[surf.Zone_Name] = za.get(surf.Zone_Name, 0) + abs(poly.area)
        return za

    def _sum_loads(objs, abs_methods, abs_attr, rate_attr, zone_attr, method_attr, za):
        """Sum installed loads, handling both absolute (Level) and Area-normalized methods."""
        total = 0.0
        for obj in objs:
            method = getattr(obj, method_attr).lower()
            if method in abs_methods:
                total += float(getattr(obj, abs_attr))
            else:
                area = za.get(getattr(obj, zone_attr), 0.0)
                total += float(getattr(obj, rate_attr)) * area
        return total

    zone_key = "Zone_or_ZoneList_or_Space_or_SpaceList_Name"
    totals = {}
    process = {}
    for mode in ("building", "floor", "fast_zone"):
        out = tmp_path / f"mf_{mode}"
        out.mkdir()
        (out / "idfs").mkdir()
        result = BuildingIDF(row, resolution_mode=mode).build(gdf, {}, out)
        assert result["idf_path"], f"No IDF produced for mode={mode!r}"
        idf = IDF(result["idf_path"])
        za = _zone_areas(idf)

        lights_obj = [l for l in idf.idfobjects["LIGHTS"] if l.Name.startswith("Lights_")]
        equip_obj = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.Name.startswith("Equipment_")]
        people_obj = [p for p in idf.idfobjects["PEOPLE"] if p.Name.startswith("People_")]

        totals[mode] = {
            "lights": _sum_loads(
                lights_obj, {"lightinglevel"}, "Lighting_Level",
                "Watts_per_Zone_Floor_Area", zone_key, "Design_Level_Calculation_Method", za,
            ),
            "equip": _sum_loads(
                equip_obj, {"equipmentlevel"}, "Design_Level",
                "Watts_per_Zone_Floor_Area", zone_key, "Design_Level_Calculation_Method", za,
            ),
            "people": _sum_loads(
                people_obj, {"people"}, "Number_of_People",
                "People_per_Floor_Area", zone_key, "Number_of_People_Calculation_Method", za,
            ),
        }

        # Absolute process loads pinned to zones[0] (F13) — single scalar per mode, not summed.
        cook_gas = [g for g in idf.idfobjects["GASEQUIPMENT"] if g.Name.startswith("Cooking_Gas_")]
        cook_elec = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.Name.startswith("Cooking_Elec_")]
        refrig = [e for e in idf.idfobjects["ELECTRICEQUIPMENT"] if e.Name.startswith("Refrig_Lumped_")]
        wu = idf.idfobjects["WATERUSE:EQUIPMENT"]
        assert len(cook_gas) == 1 and len(cook_elec) == 1 and len(refrig) == 1 and len(wu) == 1, (
            f"mode={mode!r}: expected exactly one each of cooking-gas/cooking-elec/refrig/dhw, "
            f"got {len(cook_gas)}/{len(cook_elec)}/{len(refrig)}/{len(wu)}"
        )
        process[mode] = {
            "cook_gas": float(cook_gas[0].Design_Level),
            "cook_elec": float(cook_elec[0].Design_Level),
            "refrig": float(refrig[0].Design_Level),
            "dhw": float(wu[0].Peak_Flow_Rate),
        }

    # 5-floor → Σ zone_area / floor_area_m2 = footprint × 5 in all three modes → identical totals.
    # This is exactly the M18 regression: pre-fix, "building" totals were 0.200× the others.
    rel_tol = 1e-6
    ref = totals["floor"]
    ref_proc = process["floor"]
    for mode in ("building", "fast_zone"):
        for metric in ("lights", "equip", "people"):
            v, r = totals[mode][metric], ref[metric]
            assert abs(v - r) / max(abs(r), 1e-12) < rel_tol, (
                f"M18 regression: {metric} total differs — floor={r:.4f}, {mode}={v:.4f}"
            )
        for metric in ("cook_gas", "cook_elec", "refrig", "dhw"):
            v, r = process[mode][metric], ref_proc[metric]
            assert abs(v - r) / max(abs(r), 1e-12) < rel_tol, (
                f"M18 regression: process load {metric!r} differs — floor={r:.6g}, {mode}={v:.6g}"
            )
