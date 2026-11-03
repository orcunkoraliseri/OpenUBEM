"""Tests for attribute_binding (T05/T06) + metadata_block (T07).

Synthetic in-memory fixtures reusing the small real DOE Restaurant IDF for
geometry, with hand-built results/manifest/buildings frames so both the
present-field and absent-field (graceful-degrade) provenance paths are covered.
"""
import os

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from openubem.viz.attribute_binding import bind_provenance, bind_values
from openubem.viz.cityjson_emitter import build_cityjson, dumps
from openubem.viz.metadata_block import add_metadata_block, content_hash

_FIXTURE_IDF = os.path.join(
    os.path.dirname(__file__), "fixtures", "viz",
    "Restaurant_QuickServiceRestaurant_90.1-2013.idf",
)


def _sq(cx, cy, h=10.0):
    return Polygon([(cx - h, cy - h), (cx + h, cy - h),
                    (cx + h, cy + h), (cx - h, cy + h)])


def _manifest(rows):
    return pd.DataFrame(rows)


@pytest.fixture
def buildings_gdf():
    return gpd.GeoDataFrame(
        {
            "osm_id": ["way/A", "way/B", "way/C"],
            "levels": [2, 5, 3],
            "height_m": [7.0, 17.5, None],
            "year_built": [1990.0, 1985.0, 2001.0],
            "provenance_levels": ["OSM_OBSERVED", "OSM_MISSING", "OSM_OBSERVED"],
            "provenance_year_built": ["OSM_OBSERVED", "OSM_MISSING", "OSM_MISSING"],
            "geometry": [_sq(500000, 4500000), _sq(500250, 4500180),
                         _sq(500600, 4500400)],
        },
        crs="EPSG:32618",
    )


@pytest.fixture
def manifest_pilot():
    # Pilot-like: NO resolution_mode, NO archetype_confidence/_source, NO
    # imputation-lineage columns. All three buildings have IDFs.
    return _manifest([
        {"osm_id": "way/A", "idf_path": _FIXTURE_IDF, "zoning_strategy": "single_zone",
         "num_zones": 3, "generation_status": "success"},
        {"osm_id": "way/B", "idf_path": _FIXTURE_IDF, "zoning_strategy": "one_zone_per_floor",
         "num_zones": 5, "generation_status": "success"},
        {"osm_id": "way/C", "idf_path": _FIXTURE_IDF, "zoning_strategy": "single_zone",
         "num_zones": 3, "generation_status": "success"},
    ])


@pytest.fixture
def results_AB():
    # Success rows for A and B only (C absent -> never simulated).
    return pd.DataFrame([
        {"osm_id": "way/A", "footprint_area_m2": 400.0, "levels": 2,
         "height_m": 7.0, "archetype_id": "QuickServiceRestaurant",
         "total_eui_kwh_m2": 123.45, "heating_eui_kwh_m2": 40.0,
         "gwp_total_kgco2_m2": 55.5, "iod": 3.1,
         "data_quality_flag": ""},
        {"osm_id": "way/B", "footprint_area_m2": 900.0, "levels": 5,
         "height_m": 17.5, "archetype_id": "MediumOffice",
         "total_eui_kwh_m2": 67.8, "heating_eui_kwh_m2": 20.0,
         "gwp_total_kgco2_m2": 30.2, "iod": 1.4,
         "data_quality_flag": "no_height"},
    ])


@pytest.fixture
def cityjson(manifest_pilot, buildings_gdf):
    return build_cityjson(manifest_pilot, buildings_gdf)


class TestBindValues:
    def test_cp_value_total_eui_matches_source_exactly(self, cityjson, results_AB, buildings_gdf):
        bind_values(cityjson, results_AB, buildings_gdf)
        assert cityjson["CityObjects"]["way/A"]["attributes"]["total_eui_kwh_m2"] == 123.45
        assert cityjson["CityObjects"]["way/B"]["attributes"]["total_eui_kwh_m2"] == 67.8

    def test_year_built_joined_from_buildings(self, cityjson, results_AB, buildings_gdf):
        bind_values(cityjson, results_AB, buildings_gdf)
        assert cityjson["CityObjects"]["way/A"]["attributes"]["year_built"] == 1990.0

    def test_no_population_key_anywhere(self, cityjson, results_AB, buildings_gdf):
        bind_values(cityjson, results_AB, buildings_gdf)
        for co in cityjson["CityObjects"].values():
            assert "population" not in co["attributes"]

    def test_building_absent_from_results_has_no_eui_and_not_dropped(
        self, cityjson, results_AB, buildings_gdf
    ):
        bind_values(cityjson, results_AB, buildings_gdf)
        assert "way/C" in cityjson["CityObjects"]  # not dropped
        assert "total_eui_kwh_m2" not in cityjson["CityObjects"]["way/C"]["attributes"]


class TestBindProvenanceGracefulDegrade:
    def test_absent_resolution_mode_omitted_and_in_coverage(
        self, cityjson, manifest_pilot, results_AB, buildings_gdf
    ):
        cov = bind_provenance(cityjson, manifest_pilot, results_AB, buildings_gdf)
        for co in cityjson["CityObjects"].values():
            assert "resolution_mode" not in co["attributes"]  # never defaulted
        assert "resolution_mode" in cov["absent"]
        assert "archetype_confidence" in cov["absent"]
        assert "mean_imputation_confidence" in cov["absent"]

    def test_present_fields_roundtrip_verbatim(
        self, cityjson, manifest_pilot, results_AB, buildings_gdf
    ):
        bind_provenance(cityjson, manifest_pilot, results_AB, buildings_gdf)
        a = cityjson["CityObjects"]["way/A"]["attributes"]
        assert a["zoning_strategy"] == "single_zone"
        assert a["num_zones"] == 3
        assert a["generation_status"] == "success"
        assert a["data_quality_flag"] == ""
        assert a["provenance_levels"] == "OSM_OBSERVED"

    def test_trust_confidence_omitted_when_sides_absent(
        self, cityjson, manifest_pilot, results_AB, buildings_gdf
    ):
        cov = bind_provenance(cityjson, manifest_pilot, results_AB, buildings_gdf)
        for co in cityjson["CityObjects"].values():
            assert "trust_confidence" not in co["attributes"]
        assert cov["trust_confidence_computable"] is False

    def test_coverage_lists_present_fields(
        self, cityjson, manifest_pilot, results_AB, buildings_gdf
    ):
        cov = bind_provenance(cityjson, manifest_pilot, results_AB, buildings_gdf)
        assert "zoning_strategy" in cov["present"]
        assert "generation_status" in cov["present"]
        assert "data_quality_flag" in cov["present"]
        assert "provenance_levels" in cov["present"]


class TestBindProvenanceFullArtifacts:
    """Run WITH imputation + archetype confidence columns present."""

    @pytest.fixture
    def manifest_full(self):
        return _manifest([
            {"osm_id": "way/A", "idf_path": _FIXTURE_IDF, "zoning_strategy": "single_zone",
             "num_zones": 3, "generation_status": "success",
             "resolution_mode": "building", "archetype_confidence": "HIGH",
             "archetype_source": "rule_office_2322", "mean_imputation_confidence": 1.0,
             "imputed_fields_count": 0},
            {"osm_id": "way/B", "idf_path": _FIXTURE_IDF, "zoning_strategy": "one_zone_per_floor",
             "num_zones": 5, "generation_status": "failed_worker_exception",
             "resolution_mode": "floor", "archetype_confidence": "LOW",
             "archetype_source": "fallback", "mean_imputation_confidence": 0.5,
             "imputed_fields_count": 3},
            {"osm_id": "way/C", "idf_path": _FIXTURE_IDF, "zoning_strategy": "single_zone",
             "num_zones": 3, "generation_status": "success",
             "resolution_mode": "building", "archetype_confidence": "HIGH",
             "archetype_source": "rule", "mean_imputation_confidence": 1.0,
             "imputed_fields_count": 0},
        ])

    def test_trust_confidence_min_of_sides(
        self, cityjson, manifest_full, results_AB, buildings_gdf
    ):
        cov = bind_provenance(cityjson, manifest_full, results_AB, buildings_gdf)
        # A: imputation 1.0, archetype HIGH(1.0) -> 1.0
        assert cityjson["CityObjects"]["way/A"]["attributes"]["trust_confidence"] == 1.0
        # B: imputation 0.5, archetype LOW(0.1) -> min = 0.1
        assert cityjson["CityObjects"]["way/B"]["attributes"]["trust_confidence"] == 0.1
        assert cov["trust_confidence_computable"] is True

    def test_generation_status_literal_string_preserved(
        self, cityjson, manifest_full, results_AB, buildings_gdf
    ):
        bind_provenance(cityjson, manifest_full, results_AB, buildings_gdf)
        assert (cityjson["CityObjects"]["way/B"]["attributes"]["generation_status"]
                == "failed_worker_exception")

    def test_resolution_mode_present_when_run_carries_it(
        self, cityjson, manifest_full, results_AB, buildings_gdf
    ):
        cov = bind_provenance(cityjson, manifest_full, results_AB, buildings_gdf)
        assert cityjson["CityObjects"]["way/A"]["attributes"]["resolution_mode"] == "building"
        assert "resolution_mode" in cov["present"]


class TestMetadataBlock:
    def _pipeline(self, manifest, results, buildings, timestamp):
        cj = build_cityjson(manifest, buildings)
        bind_values(cj, results, buildings)
        cov = bind_provenance(cj, manifest, results, buildings)
        add_metadata_block(
            cj, run_id="test_run", provenance_coverage=cov,
            source_refs={"results": "05_results.csv", "manifest": "03_idf_manifest.parquet"},
            timestamp=timestamp,
        )
        return cj

    def test_block_has_seven_required_keys(self, manifest_pilot, results_AB, buildings_gdf):
        cj = self._pipeline(manifest_pilot, results_AB, buildings_gdf, "2026-07-02T00:00:00Z")
        repro = cj["metadata"]["+openubem_reproducibility"]
        for key in ("git_commit", "random_seed", "run_id", "building_counts",
                    "provenance_coverage", "viewer_spec_version", "source_refs"):
            assert key in repro
        assert "lod_spec_version" in repro
        assert repro["random_seed"] == 42

    def test_cp_reproducibility_hash_excludes_timestamp(
        self, manifest_pilot, results_AB, buildings_gdf
    ):
        a = self._pipeline(manifest_pilot, results_AB, buildings_gdf, "2026-07-02T01:00:00Z")
        b = self._pipeline(manifest_pilot, results_AB, buildings_gdf, "2099-01-01T09:09:09Z")
        assert dumps(a) != dumps(b)          # timestamps differ -> files differ
        assert content_hash(a) == content_hash(b)  # hash excludes timestamp

    def test_timestamp_not_in_hashed_region(self, manifest_pilot, results_AB, buildings_gdf):
        cj = self._pipeline(manifest_pilot, results_AB, buildings_gdf, "2026-07-02T00:00:00Z")
        import copy
        c = copy.deepcopy(cj)
        c["metadata"].pop("+openubem_build_timestamp", None)
        from openubem.viz.metadata_block import content_hash as ch
        # hash of the already-timestamp-stripped copy equals hash of the original
        assert ch(c) == ch(cj)

    def test_building_counts_group_by_zoning_when_no_resolution_mode(
        self, manifest_pilot, results_AB, buildings_gdf
    ):
        cj = self._pipeline(manifest_pilot, results_AB, buildings_gdf, "2026-07-02T00:00:00Z")
        bc = cj["metadata"]["+openubem_reproducibility"]["building_counts"]
        assert bc["grouped_by"] == "zoning_strategy"
        assert bc["counts"]["single_zone"] == 2
        assert bc["counts"]["one_zone_per_floor"] == 1
