"""End-to-end Step 3 orchestrator tests (T14/T16). Validates DESIGN §5.1 CI thresholds."""
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from geomeppy import IDF
from eppy.modeleditor import IDDAlreadySetError

from openubem.config import ENERGYPLUS_IDD_PATH
from openubem.idf.builder import run_step3

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
