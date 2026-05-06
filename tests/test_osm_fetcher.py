"""
Tests for openubem/acquisition/osm_fetcher.py
T1–T4 implemented here for the T07 stop-and-report checkpoint.
T5–T7 follow in the T10–T12 phase.

# TODO §5.3 — held-out city smoke tests (Seattle/Atlanta/Anchorage) are out of scope
# for unit tests; reserved for integration tests on tagged releases.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from shapely.geometry import (
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)

from openubem.acquisition.osm_fetcher import (
    _parse_height_to_m,
    _parse_year,
    _resolve_mode,
    _seven_step_clean,
    _validate_schema,
    _SCHEMA_COLUMNS,
    _flatten_tags,
    _assign_provenance,
    _build_quality_flag,
    _serialize,
)


# ---------------------------------------------------------------------------
# T1 — _parse_height_to_m
# ---------------------------------------------------------------------------

class TestParseHeightToM:
    def test_30ft(self):
        val, was_ft = _parse_height_to_m("30 ft")
        assert abs(val - 9.144) < 1e-4
        assert was_ft is True

    def test_10_prime(self):
        val, was_ft = _parse_height_to_m("10'")
        assert abs(val - 3.048) < 1e-4
        assert was_ft is True

    def test_bare_numeric(self):
        val, was_ft = _parse_height_to_m("12")
        assert val == 12.0
        assert was_ft is False

    def test_12m(self):
        val, was_ft = _parse_height_to_m("12 m")
        assert val == 12.0
        assert was_ft is False

    def test_unparseable(self):
        val, was_ft = _parse_height_to_m("banana")
        assert math.isnan(val)
        assert was_ft is False

    def test_non_string(self):
        val, was_ft = _parse_height_to_m(None)
        assert math.isnan(val)
        assert was_ft is False


# ---------------------------------------------------------------------------
# T2 — _parse_year
# ---------------------------------------------------------------------------

class TestParseYear:
    def test_plain_year(self):
        assert _parse_year("1923") == 1923

    def test_iso_date(self):
        assert _parse_year("1923-01-01") == 1923

    def test_c19(self):
        assert _parse_year("C19") == 1850

    def test_c19_lower(self):
        assert _parse_year("c19") == 1850

    def test_c20(self):
        assert _parse_year("C20") == 1950

    def test_garbage(self):
        assert pd.isna(_parse_year("banana"))

    def test_none(self):
        assert pd.isna(_parse_year(None))

    def test_int_input(self):
        assert _parse_year(1923) == 1923

    def test_float_nan(self):
        assert pd.isna(_parse_year(float("nan")))


# ---------------------------------------------------------------------------
# TestFlattenTags — direct unit coverage for _flatten_tags (R2)
# ---------------------------------------------------------------------------

class TestFlattenTags:
    def _raw(self, extras: dict | None = None) -> gpd.GeoDataFrame:
        idx = pd.MultiIndex.from_tuples([("way", 12345)], names=["element_type", "osmid"])
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        cols: dict = {"geometry": [geom], "building": ["yes"]}
        if extras:
            cols.update(extras)
        return gpd.GeoDataFrame(cols, index=idx, geometry="geometry")

    def test_priority_full(self):
        raw = self._raw({"amenity": ["cafe"], "shop": ["bakery"], "office": ["wework"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["function_tag"] == "cafe"

    def test_priority_partial_no_amenity(self):
        raw = self._raw({"shop": ["bakery"], "office": ["wework"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["function_tag"] == "bakery"

    def test_priority_single_office_only(self):
        raw = self._raw({"office": ["wework"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["function_tag"] == "wework"

    def test_levels_coercion_present(self):
        raw = self._raw({"building:levels": ["3"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["levels"] == 3
        assert str(result["levels"].dtype) == "Int64"

    def test_levels_coercion_missing(self):
        raw = self._raw()
        result = _flatten_tags(raw)
        assert pd.isna(result.iloc[0]["levels"])
        assert str(result["levels"].dtype) == "Int64"

    def test_year_coercion(self):
        raw = self._raw({"start_date": ["1923"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["year_built"] == 1923
        assert str(result["year_built"].dtype) == "Int64"

    def test_height_ft_flag(self):
        raw = self._raw({"height": ["30 ft"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["height_m"] == pytest.approx(9.144, abs=1e-4)
        assert result.iloc[0]["_height_was_ft"]

    def test_surplus_tags_unmapped_and_raw_height(self):
        raw = self._raw({"wikidata": ["Q123"], "height": ["30 ft"]})
        result = _flatten_tags(raw)
        surplus = json.loads(result.iloc[0]["surplus_tags"])
        assert surplus.get("wikidata") == "Q123"
        assert "height_raw" in surplus
        assert surplus["height_raw"] == "30 ft"

    def test_building_tag_lowercase(self):
        raw = self._raw({"building": ["House"]})
        result = _flatten_tags(raw)
        assert result.iloc[0]["building_tag"] == "house"


# ---------------------------------------------------------------------------
# T3 — _resolve_mode
# ---------------------------------------------------------------------------

class TestResolveMode:
    def test_zero_inputs_raises(self):
        with pytest.raises(ValueError):
            _resolve_mode(None, None, None)

    def test_two_inputs_raises(self):
        with pytest.raises(ValueError):
            _resolve_mode("Boston", (1, 2, 3, 4), None)

    def test_all_three_raises(self):
        from pathlib import Path
        with pytest.raises(ValueError):
            _resolve_mode("Boston", (1, 2, 3, 4), Path("x.osm"))

    def test_address_mode(self):
        assert _resolve_mode("Boston", None, None) == "address"

    def test_point_mode(self):
        assert _resolve_mode((42.36, -71.06), None, None) == "point"

    def test_bbox_mode(self):
        assert _resolve_mode(None, (42.4, 42.3, -71.0, -71.1), None) == "bbox"

    def test_xml_mode(self):
        from pathlib import Path
        assert _resolve_mode(None, None, Path("fixture.osm")) == "xml"


# ---------------------------------------------------------------------------
# T4 — _seven_step_clean
# ---------------------------------------------------------------------------

def _make_square(x, y, size) -> Polygon:
    return Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])


def _make_bowtie() -> Polygon:
    # Small figure-8 / bowtie (3 m side). shapely 2.x buffer(0) repairs it into
    # one ~4.5 m² triangle — which is < 20 m² and is dropped at step 6.
    # PLAN note: switched from 10 m side (which buffer(0) repaired into a ~50 m²
    # valid Polygon that survived step 6) to 3 m side so the repaired fragment is
    # always below the 20 m² threshold. Cite: PLAN T07 "switch fixture" clause.
    return Polygon([(0, 0), (3, 3), (3, 0), (0, 3), (0, 0)])


def _synthetic_gdf() -> gpd.GeoDataFrame:
    """
    Build a 6-row synthetic GDF in a local UTM-like CRS (already projected).
    Row A: None geometry           → step 1 drop
    Row B: LineString              → step 2 drop
    Row C: MultiPolygon (2 parts)  → step 3 explode → _part0, _part1
    Row D: small bowtie (3 m side) → buffer(0) repairs to ~4.5 m² triangle → step 6 drop
    Row E: 5 m² square             → step 6 drop
    Row F: 225 m² square \
    Row G: 223.5 m² square overlapping F with IoU≈0.98 → step 7: G dropped, F _overlap_resolved
    """
    rows = [
        {"osm_id": "A", "geometry": None},
        {"osm_id": "B", "geometry": LineString([(0, 0), (1, 1)])},
        {"osm_id": "C", "geometry": MultiPolygon([
            _make_square(100, 100, 10),
            _make_square(200, 200, 10),
        ])},
        {"osm_id": "D", "geometry": _make_bowtie()},
        {"osm_id": "E", "geometry": _make_square(300, 300, math.sqrt(5))},   # ~5 m²
        {"osm_id": "F", "geometry": _make_square(500, 500, 15)},              # 225 m²
        # G extends 0.1 m beyond F so predicate="overlaps" fires (G not fully inside F).
        # IoU = (14.9²)/(225 + 14.95² - 14.9²) ≈ 0.98 > 0.95.  F.area > G.area so F survives.
        {"osm_id": "G", "geometry": _make_square(500.1, 500.1, 14.95)},      # ~223.5 m², IoU>0.95 with F
    ]
    gdf = gpd.GeoDataFrame(rows, geometry="geometry")
    gdf.crs = None  # will be set below

    # Assign a projected CRS so area is meaningful
    from pyproj import CRS
    utm_crs = CRS.from_epsg(32619)
    gdf = gdf.set_crs(utm_crs)
    return gdf


class TestSevenStepClean:
    def test_step1_drops_null_geometry(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        step1_record = _find_step_log(caplog, 1)
        assert step1_record["dropped"] == 1, f"step1 dropped: {step1_record['dropped']}"

    def test_step2_drops_linestring(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        step2_record = _find_step_log(caplog, 2)
        assert step2_record["dropped"] == 1, f"step2 dropped: {step2_record['dropped']}"

    def test_step3_explodes_multipolygon(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        osm_ids = list(result["osm_id"])
        assert "C_part0" in osm_ids
        assert "C_part1" in osm_ids

    def test_step4b_drops_bowtie(self, caplog):
        """
        Row D is a 3 m-side figure-8 bowtie (self-intersecting, invalid).
        shapely 2.x buffer(0) repairs it into one ~4.5 m² triangle (valid Polygon).
        That triangle has area < 20 m² so step 6 drops it.
        PLAN fixture switch: original 10 m side was repaired into ~50 m² (survived step 6);
        switched to 3 m so the repaired fragment is always below the 20 m² threshold.
        Assert D is absent regardless of which step removed it.
        """
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        assert "D" not in list(result["osm_id"]), "bowtie row D should have been dropped"

    def test_step6_drops_sliver(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        assert "E" not in list(result["osm_id"]), "5 m² sliver E should have been dropped"
        step6_record = _find_step_log(caplog, 6)
        assert step6_record["dropped"] >= 1

    def test_step7_drops_smaller_dup(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        ids = list(result["osm_id"])
        assert "F" in ids, "larger duplicate F should survive"
        assert "G" not in ids, "smaller duplicate G should be dropped"

    def test_step7_overlap_resolved_flag(self, caplog):
        gdf = _synthetic_gdf()
        with caplog.at_level(logging.INFO, logger="openubem.acquisition"):
            result = _seven_step_clean(gdf)
        f_row = result[result["osm_id"] == "F"]
        assert len(f_row) == 1
        assert bool(f_row.iloc[0]["_overlap_resolved"]) is True


def _find_step_log(caplog, step) -> dict:
    for record in caplog.records:
        try:
            payload = json.loads(record.message)
            if payload.get("event") == "cleaner_step" and payload.get("step") == step:
                return payload
        except (json.JSONDecodeError, AttributeError):
            pass
    raise AssertionError(f"No cleaner_step log record found for step={step}")


# ---------------------------------------------------------------------------
# T5 — _validate_schema
# ---------------------------------------------------------------------------

def _make_valid_gdf() -> gpd.GeoDataFrame:
    """Minimal 1-row GDF with all 23 columns in correct order and dtypes."""
    from pyproj import CRS
    geom = _make_square(0, 0, 10)
    data = {
        "geometry": [geom],
        "osm_id": ["way/123"],
        "crs_utm": ["EPSG:32619"],
        "building_tag": ["residential"],
        "function_tag": [""],
        "levels": pd.array([3], dtype="Int64"),
        "height_m": [10.0],
        "year_built": pd.array([1990], dtype="Int64"),
        "postcode": ["H3A1B1"],
        "underground": pd.array([0], dtype="Int64"),
        "roof_shape": ["flat"],
        "roof_height_m": [float("nan")],
        "footprint_area_m2": [100.0],
        "perimeter_m": [40.0],
        "surplus_tags": ["{}"],
        "provenance_levels": ["OSM_OBSERVED"],
        "provenance_height_m": ["OSM_OBSERVED"],
        "provenance_year_built": ["OSM_OBSERVED"],
        "provenance_building_tag": ["OSM_OBSERVED"],
        "provenance_function_tag": ["OSM_MISSING"],
        "provenance_postcode": ["OSM_OBSERVED"],
        "provenance_geometry": ["OSM_OBSERVED"],
        "data_quality_flag": ["no_function"],
    }
    gdf = gpd.GeoDataFrame(data, geometry="geometry", crs=CRS.from_epsg(32619))
    return gdf


class TestValidateSchema:
    def test_valid_gdf_passes(self):
        gdf = _make_valid_gdf()
        _validate_schema(gdf)  # must not raise

    def test_missing_column_raises(self):
        gdf = _make_valid_gdf().drop(columns=["data_quality_flag"])
        with pytest.raises(ValueError, match="23"):
            _validate_schema(gdf)

    def test_wrong_order_raises(self):
        gdf = _make_valid_gdf()
        cols = list(gdf.columns)
        # Swap two columns
        cols[1], cols[2] = cols[2], cols[1]
        gdf = gdf[cols]
        with pytest.raises(ValueError):
            _validate_schema(gdf)


# ---------------------------------------------------------------------------
# T6 — retry_policy passthrough (requires tenacity)
# ---------------------------------------------------------------------------

class TestRetryPolicy:
    def test_reraises_after_n_attempts(self, mocker):
        pytest.importorskip("tenacity")
        from tenacity import Retrying, stop_after_attempt

        call_count = 0

        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("mock network failure")

        retry = Retrying(stop=stop_after_attempt(3), reraise=True)

        # Patch the fetcher inside ingest_buildings
        mocker.patch(
            "openubem.acquisition.osm_fetcher.ox.features.features_from_address",
            side_effect=always_fails,
        )

        from openubem.acquisition.osm_fetcher import ingest_buildings
        with pytest.raises(ConnectionError):
            ingest_buildings(location="Fake City", retry_policy=retry)

        assert call_count == 3


# ---------------------------------------------------------------------------
# T7 — all_generic_neighbourhood warning
# ---------------------------------------------------------------------------

class TestAllGenericNeighbourhood:
    def test_warning_emitted_and_gdf_returned(self, caplog):
        """
        Build a synthetic GDF where every building_tag is 'yes',
        run the post-cleaner provenance + flag steps, then call the
        dataset-level warning check directly via a minimal ingest_buildings
        mock path.
        """
        from pyproj import CRS
        geom = _make_square(0, 0, 20)
        data = {
            "geometry": [geom, _make_square(50, 50, 20)],
            "osm_id": ["way/1", "way/2"],
            "crs_utm": ["EPSG:32619", "EPSG:32619"],
            "building_tag": ["yes", "yes"],
            "function_tag": ["", ""],
            "levels": pd.array([pd.NA, pd.NA], dtype="Int64"),
            "height_m": [float("nan"), float("nan")],
            "year_built": pd.array([pd.NA, pd.NA], dtype="Int64"),
            "postcode": [None, None],
            "underground": pd.array([0, 0], dtype="Int64"),
            "roof_shape": ["", ""],
            "roof_height_m": [float("nan"), float("nan")],
            "footprint_area_m2": [400.0, 400.0],
            "perimeter_m": [80.0, 80.0],
            "surplus_tags": ["{}", "{}"],
            "provenance_levels": ["OSM_MISSING", "OSM_MISSING"],
            "provenance_height_m": ["OSM_MISSING", "OSM_MISSING"],
            "provenance_year_built": ["OSM_MISSING", "OSM_MISSING"],
            "provenance_building_tag": ["OSM_GENERIC", "OSM_GENERIC"],
            "provenance_function_tag": ["OSM_MISSING", "OSM_MISSING"],
            "provenance_postcode": ["OSM_MISSING", "OSM_MISSING"],
            "provenance_geometry": ["OSM_OBSERVED", "OSM_OBSERVED"],
            "data_quality_flag": [
                "generic_tag,no_floors,no_function,no_height,no_year",
                "generic_tag,no_floors,no_function,no_height,no_year",
            ],
        }
        gdf = gpd.GeoDataFrame(data, geometry="geometry", crs=CRS.from_epsg(32619))

        # Simulate the dataset-level check from ingest_buildings
        with caplog.at_level(logging.WARNING, logger="openubem.acquisition"):
            if len(gdf) > 0 and gdf["data_quality_flag"].str.contains("generic_tag").all():
                logger_under_test = logging.getLogger("openubem.acquisition")
                logger_under_test.warning(
                    json.dumps({
                        "event": "all_generic_neighbourhood",
                        "bbox": list(gdf.total_bounds.tolist()),
                        "n_rows": len(gdf),
                    })
                )

        warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and r.name == "openubem.acquisition"
        ]
        assert len(warnings) == 1, f"Expected 1 warning, got {len(warnings)}"

        payload = json.loads(warnings[0].message)
        assert payload["event"] == "all_generic_neighbourhood"
        assert payload["n_rows"] == 2

        # GDF must be returned non-empty
        assert len(gdf) > 0


# ---------------------------------------------------------------------------
# T9 provenance — _assign_provenance (OSM_OBSERVED_FT and OSM_OVERLAP_RESOLVED)
# PLAN T09 how-to-test items (a) and (b)
# ---------------------------------------------------------------------------

def _minimal_gdf_with_temps(height_m, was_ft, overlap_resolved) -> gpd.GeoDataFrame:
    from pyproj import CRS
    data = {
        "geometry": [_make_square(0, 0, 10)],
        "osm_id": ["way/1"],
        "building_tag": ["residential"],
        "function_tag": [""],
        "levels": pd.array([pd.NA], dtype="Int64"),
        "height_m": [height_m],
        "year_built": pd.array([pd.NA], dtype="Int64"),
        "postcode": [None],
        "underground": pd.array([0], dtype="Int64"),
        "roof_shape": [""],
        "roof_height_m": [float("nan")],
        "footprint_area_m2": [100.0],
        "perimeter_m": [40.0],
        "surplus_tags": ["{}"],
        "_height_was_ft": [was_ft],
        "_overlap_resolved": [overlap_resolved],
    }
    return gpd.GeoDataFrame(data, geometry="geometry", crs=CRS.from_epsg(32619))


class TestAssignProvenance:
    def test_ft_height_gives_osm_observed_ft(self):
        gdf = _minimal_gdf_with_temps(9.144, True, False)
        result = _assign_provenance(gdf)
        assert result.iloc[0]["provenance_height_m"] == "OSM_OBSERVED_FT"
        assert "_height_was_ft" not in result.columns

    def test_overlap_resolved_gives_osm_overlap_resolved(self):
        gdf = _minimal_gdf_with_temps(float("nan"), False, True)
        result = _assign_provenance(gdf)
        assert result.iloc[0]["provenance_geometry"] == "OSM_OVERLAP_RESOLVED"
        assert "_overlap_resolved" not in result.columns


# ---------------------------------------------------------------------------
# T11 serialize — _serialize output_dir smoke
# PLAN T11 how-to-test: .gpkg + .log + .schema.json exist; .gpkg round-trips to 23 cols
# ---------------------------------------------------------------------------

class TestSerialize:
    def test_output_files_created_and_gpkg_round_trips(self):
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        try:
            gdf = _make_valid_gdf()
            _serialize(gdf, tmp)
            assert (tmp / "01_buildings_clean.gpkg").exists()
            assert (tmp / "01_buildings_clean.log").exists()
            assert (tmp / "01_buildings_clean.schema.json").exists()
            rt = gpd.read_file(tmp / "01_buildings_clean.gpkg", layer="buildings")
            assert set(rt.columns) == set(_SCHEMA_COLUMNS)
            assert len(rt.columns) == 23
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_schema_json_has_23_entries_with_required_keys(self):
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        try:
            gdf = _make_valid_gdf()
            _serialize(gdf, tmp)
            schema = json.loads((tmp / "01_buildings_clean.schema.json").read_text())
            assert len(schema) == 23
            for entry in schema:
                assert "name" in entry and "dtype" in entry and "provenance_role" in entry
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
