"""Tests for openubem/semantic/building_classifier.py — plan T14."""

import json
import shutil
import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    SchemaError,
    _INPUT_SCHEMA_COLUMNS,
    _VALID_30,
    _apply_detailed_office,
    _apply_overrides,
    _apply_rule_table,
    _assign_confidence,
    _impute_levels,
    _normalise_use_class,
    _validate_input_schema,
    _validate_output_schema,
    classify_building,
)

# ── row / GDF factories ────────────────────────────────────────────────────────

_ROW_DEFAULTS: dict = {
    "geometry": box(0, 0, 1, 1),
    "osm_id": "1001",
    "crs_utm": "EPSG:32619",
    "building_tag": "",
    "function_tag": "",
    "levels": pd.NA,
    "height_m": float("nan"),
    "year_built": pd.NA,
    "postcode": "",
    "underground": 0,
    "roof_shape": "",
    "roof_height_m": float("nan"),
    "footprint_area_m2": 800.0,
    "perimeter_m": 120.0,
    "surplus_tags": "{}",
    "provenance_levels": "OSM_MISSING",
    "provenance_height_m": "OSM_MISSING",
    "provenance_year_built": "OSM_MISSING",
    "provenance_building_tag": "OSM_OBSERVED",
    "provenance_function_tag": "OSM_MISSING",
    "provenance_postcode": "OSM_MISSING",
    "provenance_geometry": "OSM_OBSERVED",
    "data_quality_flag": "",
}


def _row(**kwargs) -> pd.Series:
    d = dict(_ROW_DEFAULTS)
    d.update(kwargs)
    return pd.Series(d)


def _make_min_gdf(n: int = 3, **col_overrides) -> gpd.GeoDataFrame:
    rows = []
    for i in range(n):
        d = dict(_ROW_DEFAULTS)
        d["geometry"] = box(i, 0, i + 1, 1)
        d["osm_id"] = str(1000 + i)
        d.update(col_overrides)
        rows.append(d)
    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:32619")
    gdf["levels"] = gdf["levels"].astype("Int64")
    gdf["year_built"] = gdf["year_built"].astype("Int64")
    gdf["underground"] = gdf["underground"].astype("Int64")
    return gdf


# ── TestOpenStudioArchetypeRegistry ───────────────────────────────────────────

class TestOpenStudioArchetypeRegistry:
    def test_loads(self):
        from importlib.resources import files
        data = json.loads(files("openubem.data").joinpath("openstudio_archetypes.json").read_text())
        assert "archetypes" in data

    def test_count_30(self):
        from importlib.resources import files
        data = json.loads(files("openubem.data").joinpath("openstudio_archetypes.json").read_text())
        assert len(data["archetypes"]) == 30

    def test_unique_ids(self):
        ids = [a["archetype_id"] for a in __import__(
            "json").loads(__import__("importlib.resources", fromlist=["files"]).files(
                "openubem.data").joinpath("openstudio_archetypes.json").read_text())["archetypes"]]
        assert len(ids) == len(set(ids))

    def test_schema_version(self):
        from importlib.resources import files
        data = json.loads(files("openubem.data").joinpath("openstudio_archetypes.json").read_text())
        assert "schema_version" in data

    def test_openubem_unknown_present(self):
        assert "OpenUBEMUnknown" in _VALID_30

    def test_phase1_unreachable_count_2(self):
        from importlib.resources import files
        data = json.loads(files("openubem.data").joinpath("openstudio_archetypes.json").read_text())
        unreachable = [a["archetype_id"] for a in data["archetypes"] if a.get("phase_1_unreachable")]
        assert len(unreachable) == 2
        assert "SmallDataCenterLowITE" in unreachable
        assert "LargeDataCenterLowITE" in unreachable

    def test_all_rule_outputs_in_vocab(self):
        rule_outputs = {
            "SuperTallBuilding", "TallBuilding", "HighriseApartment", "MidriseApartment",
            "LargeHotel", "SmallHotel", "FullServiceRestaurant", "QuickServiceRestaurant",
            "Hospital", "Outpatient", "College", "SecondarySchool", "PrimarySchool",
            "Courthouse", "Laboratory", "SmallDataCenterHighITE", "LargeDataCenterHighITE",
            "Warehouse", "SuperMarket", "RetailStripmall", "RetailStandalone",
            "SmallOffice", "MediumOffice", "LargeOffice", "OpenUBEMUnknown",
        }
        assert rule_outputs.issubset(_VALID_30)


# ── TestUseClassMapping ────────────────────────────────────────────────────────

class TestUseClassMapping:
    def _load(self):
        from importlib.resources import files
        return json.loads(files("openubem.data").joinpath("osm_to_use_class.json").read_text())

    def test_loads(self):
        assert "tag_to_use_class" in self._load()

    def test_all_values_valid(self):
        data = self._load()
        valid = set(data["use_classes"])
        assert set(data["tag_to_use_class"].values()).issubset(valid)

    def test_spot_checks(self):
        m = self._load()["tag_to_use_class"]
        assert m["apartments"] == "residential"
        assert m["restaurant"] == "commercial"
        assert m["school"] == "institutional"
        assert m["data_center"] == "industrial"
        assert m["warehouse"] == "industrial"
        assert m["office"] == "commercial"


# ── TestNormaliseUseClass ──────────────────────────────────────────────────────

class TestNormaliseUseClass:
    def test_pure_residential(self):
        uc, score = _normalise_use_class(_row(building_tag="apartments"))
        assert uc == "residential" and score == 1.0

    def test_pure_commercial(self):
        uc, score = _normalise_use_class(_row(building_tag="office"))
        assert uc == "commercial" and score == 1.0

    def test_function_building_disagree(self):
        uc, score = _normalise_use_class(_row(function_tag="shop", building_tag="apartments"))
        assert uc == "mixed" and score == 0.5

    def test_both_empty(self):
        uc, score = _normalise_use_class(_row(function_tag="", building_tag=""))
        assert uc == "unknown" and score == 0.0

    def test_building_yes_only(self):
        uc, score = _normalise_use_class(_row(building_tag="yes", function_tag=""))
        assert uc == "unknown" and score == 0.0

    def test_function_only_resolves(self):
        uc, score = _normalise_use_class(_row(function_tag="school", building_tag=""))
        assert uc == "institutional" and score == 1.0

    def test_building_only_resolves(self):
        uc, score = _normalise_use_class(_row(building_tag="warehouse", function_tag=""))
        assert uc == "industrial" and score == 1.0

    def test_agree_returns_1(self):
        uc, score = _normalise_use_class(_row(function_tag="office", building_tag="commercial"))
        assert uc == "commercial" and score == 1.0

    def test_unmapped_exotic(self):
        uc, score = _normalise_use_class(_row(building_tag="zeppelin_hangar_exotic", function_tag=""))
        assert uc == "unknown"

    def test_data_center_industrial(self):
        uc, score = _normalise_use_class(_row(building_tag="data_center"))
        assert uc == "industrial" and score == 1.0


# ── TestImputeLevels ──────────────────────────────────────────────────────────

class TestImputeLevels:
    def test_observed_int(self):
        r = _row(levels=pd.array([5], dtype="Int64")[0])
        lev, src = _impute_levels(r)
        assert lev == 5 and src == "OSM_OBSERVED"

    def test_observed_float_cast(self):
        r = _row(levels=pd.array([3], dtype="Int64")[0])
        lev, src = _impute_levels(r)
        assert isinstance(lev, int) and lev == 3

    def test_height_7m(self):
        r = _row(levels=pd.NA, height_m=7.0)
        lev, src = _impute_levels(r)
        assert lev == 2 and src == "HEURISTIC_HEIGHT"

    def test_height_3m(self):
        r = _row(levels=pd.NA, height_m=3.0)
        lev, src = _impute_levels(r)
        assert lev == 1 and src == "HEURISTIC_HEIGHT"

    def test_nan_nan(self):
        r = _row(levels=pd.NA, height_m=float("nan"))
        lev, src = _impute_levels(r)
        assert lev == 1 and src == "HEURISTIC_DEFAULT"

    def test_provenance_levels_invariant(self):
        r = _row(levels=pd.NA, provenance_levels="OSM_OBSERVED")
        _impute_levels(r)
        assert r["provenance_levels"] == "OSM_OBSERVED"


# ── TestApplyRuleTable ────────────────────────────────────────────────────────

class TestApplyRuleTable:
    def test_rule_1a_super_tall(self):
        r = _row(building_tag="office")
        aid, tok, _ = _apply_rule_table(r, 42, "commercial", 1.0)
        assert aid == "SuperTallBuilding" and tok == "RULE_HIGHRISE"

    def test_rule_1b_tall_building(self):
        r = _row(building_tag="office")
        aid, tok, _ = _apply_rule_table(r, 25, "commercial", 1.0)
        assert aid == "TallBuilding" and tok == "RULE_HIGHRISE"

    def test_rule_2b_midrise(self):
        r = _row(building_tag="apartments")
        aid, tok, _ = _apply_rule_table(r, 1, "residential", 1.0)
        assert aid == "MidriseApartment" and tok == "RULE_RESIDENTIAL_TIER"

    def test_rule_4b_cafe(self):
        r = _row(function_tag="cafe")
        aid, tok, _ = _apply_rule_table(r, 2, "commercial", 1.0)
        assert aid == "QuickServiceRestaurant" and tok == "RULE_FUNCTION_TAG"

    def test_rule_6b_composite_token(self):
        r = _row(function_tag="school", footprint_area_m2=6000.0)
        aid, tok, _ = _apply_rule_table(r, 2, "institutional", 1.0)
        assert aid == "SecondarySchool"
        assert tok == "RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED"

    def test_rule_6c_primary_school(self):
        r = _row(function_tag="kindergarten", footprint_area_m2=800.0)
        aid, tok, _ = _apply_rule_table(r, 2, "institutional", 1.0)
        assert aid == "PrimarySchool" and tok == "RULE_FUNCTION_TAG"

    def test_rule_17a_building_yes_size_default(self):
        # E-R3-2: building=yes → FALLBACK_SIZE_DEFAULT office (not OpenUBEMUnknown)
        # default footprint=800, levels=2 → total=1600 → MediumOffice
        r = _row(building_tag="yes", function_tag="")
        aid, tok, inh = _apply_rule_table(r, 2, "unknown", 0.0)
        assert aid == "MediumOffice"
        assert tok == "FALLBACK_SIZE_DEFAULT"
        assert inh is None

    def test_rule_17_fallback_unknown_non_yes(self):
        # Rule 17 still fires for non-yes tags (e.g. building=service)
        r = _row(building_tag="service", function_tag="")
        aid, tok, inh = _apply_rule_table(r, 2, "unknown", 0.0)
        assert aid == "OpenUBEMUnknown"
        assert tok == "FALLBACK_UNKNOWN"
        assert inh is None

    def test_exemption_residential_25(self):
        r = _row(building_tag="apartments")
        aid, tok, _ = _apply_rule_table(r, 25, "residential", 1.0)
        assert aid == "HighriseApartment" and tok == "RULE_RESIDENTIAL_TIER"

    def test_exemption_warehouse_25(self):
        r = _row(building_tag="warehouse")
        aid, tok, _ = _apply_rule_table(r, 25, "industrial", 1.0)
        assert aid == "Warehouse" and tok == "RULE_FUNCTION_TAG"

    def test_exemption_datacenter_25_large(self):
        r = _row(building_tag="data_center", footprint_area_m2=600.0)
        aid, tok, _ = _apply_rule_table(r, 25, "industrial", 1.0)
        assert aid == "LargeDataCenterHighITE" and tok == "RULE_FUNCTION_TAG_SIZE"

    def test_rule_15_mixed_dominant(self):
        # score=1.0 >= 0.60 → rule 15; dominant tag=apartments→residential; levels=12 → HighriseApartment
        r = _row(function_tag="", building_tag="apartments")
        aid, tok, inh = _apply_rule_table(r, 12, "mixed", 1.0)
        assert aid == "HighriseApartment"
        assert tok == "MIXED_USE_DOMINANT_TAG"
        assert inh == "RULE_RESIDENTIAL_TIER"

    def test_rule_16_no_dominant(self):
        # score=0.5 < 0.60 → rule 16 → MidriseApartment
        r = _row(function_tag="", building_tag="apartments")
        aid, tok, inh = _apply_rule_table(r, 5, "mixed", 0.5)
        assert aid == "MidriseApartment"
        assert tok == "MIXED_USE_DOMINANT_TAG"
        assert inh is None

    def test_rule_9a_small_dc(self):
        r = _row(building_tag="data_center", footprint_area_m2=300.0)
        aid, tok, _ = _apply_rule_table(r, 2, "industrial", 1.0)
        assert aid == "SmallDataCenterHighITE"

    def test_rule_12b_medium_office(self):
        # footprint=1000, levels=3 → total=3000 → MediumOffice (E-R3-1)
        r = _row(building_tag="office", footprint_area_m2=1000.0)
        aid, tok, _ = _apply_rule_table(r, 3, "commercial", 1.0)
        assert aid == "MediumOffice" and tok == "RULE_USE_CLASS_SIZE"

    def test_rule_12c_tall_slim_tower(self):
        # A01 E-R3-1: footprint=1000, levels=10 → total=10000 ≥ 4000 → LargeOffice
        r = _row(building_tag="office", footprint_area_m2=1000.0)
        aid, tok, _ = _apply_rule_table(r, 10, "commercial", 1.0)
        assert aid == "LargeOffice" and tok == "RULE_USE_CLASS_SIZE"

    def test_rule_17a_building_yes_small(self):
        # A02 E-R3-2: building=yes, levels=3, footprint=120 → total=360 < 500 → SmallOffice/FALLBACK_SIZE_DEFAULT
        r = _row(building_tag="yes", footprint_area_m2=120.0)
        aid, tok, _ = _apply_rule_table(r, 3, "unknown", 0.0)
        assert aid == "SmallOffice" and tok == "FALLBACK_SIZE_DEFAULT"

    def test_rule_17a_building_roof_still_unknown(self):
        # A02 E-R3-2: building=roof (not "yes") → still FALLBACK_UNKNOWN
        r = _row(building_tag="roof", footprint_area_m2=200.0)
        aid, tok, _ = _apply_rule_table(r, 1, "unknown", 0.0)
        assert aid == "OpenUBEMUnknown" and tok == "FALLBACK_UNKNOWN"


# ── TestAssignConfidence ──────────────────────────────────────────────────────

class TestAssignConfidence:
    def test_rule_4b_cafe_high(self):
        r = _row(function_tag="cafe", provenance_function_tag="OSM_OBSERVED")
        assert _assign_confidence(r, "RULE_FUNCTION_TAG", "OSM_OBSERVED", "commercial") == "HIGH"

    def test_rule_1a_imputed_levels_medium(self):
        r = _row(building_tag="office", provenance_building_tag="OSM_OBSERVED",
                 provenance_function_tag="OSM_MISSING")
        conf = _assign_confidence(r, "RULE_HIGHRISE", "HEURISTIC_DEFAULT", "commercial")
        assert conf == "MEDIUM"

    def test_rule_12b_commercial_no_tag_medium(self):
        r = _row(building_tag="office")
        assert _assign_confidence(r, "RULE_USE_CLASS_SIZE", "OSM_OBSERVED", "commercial") == "MEDIUM"

    def test_rule_17_fallback_unknown_low(self):
        r = _row(building_tag="yes")
        assert _assign_confidence(r, "FALLBACK_UNKNOWN", "OSM_OBSERVED", "unknown") == "LOW"

    def test_rule_17a_fallback_size_default_low(self):
        # A02 E-R3-2: FALLBACK_SIZE_DEFAULT confidence is LOW
        r = _row(building_tag="yes")
        assert _assign_confidence(r, "FALLBACK_SIZE_DEFAULT", "OSM_OBSERVED", "unknown") == "LOW"

    def test_osm_generic_low(self):
        r = _row(provenance_building_tag="OSM_GENERIC", function_tag="")
        assert _assign_confidence(r, "RULE_USE_CLASS_SIZE", "OSM_OBSERVED", "unknown") == "LOW"

    def test_rule_2a_observed_levels_high(self):
        r = _row(building_tag="apartments", provenance_building_tag="OSM_OBSERVED",
                 provenance_function_tag="OSM_MISSING")
        conf = _assign_confidence(r, "RULE_RESIDENTIAL_TIER", "OSM_OBSERVED", "residential")
        assert conf == "HIGH"

    def test_rule_2a_imputed_levels_medium(self):
        r = _row(building_tag="apartments", provenance_building_tag="OSM_OBSERVED",
                 provenance_function_tag="OSM_MISSING")
        conf = _assign_confidence(r, "RULE_RESIDENTIAL_TIER", "HEURISTIC_DEFAULT", "residential")
        assert conf == "MEDIUM"

    def test_rule_2a_function_tag_observed_high(self):
        r = _row(function_tag="residential", provenance_function_tag="OSM_OBSERVED",
                 provenance_building_tag="OSM_OBSERVED")
        conf = _assign_confidence(r, "RULE_RESIDENTIAL_TIER", "OSM_OBSERVED", "residential")
        assert conf == "HIGH"

    def test_rule_15_inherited_low_no_inflation(self):
        r = _row(building_tag="apartments")
        conf = _assign_confidence(
            r, "MIXED_USE_DOMINANT_TAG", "OSM_OBSERVED", "mixed",
            inherited_rule_tier="LOW"
        )
        assert conf == "LOW"

    def test_rule_16_medium(self):
        r = _row(building_tag="apartments")
        conf = _assign_confidence(
            r, "MIXED_USE_DOMINANT_TAG", "OSM_OBSERVED", "mixed",
            inherited_rule_tier=None
        )
        assert conf == "MEDIUM"


# ── TestApplyDetailedOffice ───────────────────────────────────────────────────

class TestApplyDetailedOffice:
    def test_false_noop(self):
        aid, src = _apply_detailed_office("MediumOffice", "RULE_USE_CLASS_SIZE", detailed_office=False)
        assert aid == "MediumOffice" and src == "RULE_USE_CLASS_SIZE"

    def test_medium_office_promoted(self):
        aid, src = _apply_detailed_office("MediumOffice", "RULE_USE_CLASS_SIZE", detailed_office=True)
        assert aid == "MediumOfficeDetailed"
        assert src == "RULE_USE_CLASS_SIZE,DETAILED_OFFICE"

    def test_small_office_promoted(self):
        aid, src = _apply_detailed_office("SmallOffice", "RULE_USE_CLASS_SIZE", detailed_office=True)
        assert aid == "SmallOfficeDetailed"

    def test_large_office_promoted(self):
        aid, src = _apply_detailed_office("LargeOffice", "RULE_USE_CLASS_SIZE", detailed_office=True)
        assert aid == "LargeOfficeDetailed"

    def test_non_office_unchanged(self):
        aid, src = _apply_detailed_office("MidriseApartment", "RULE_RESIDENTIAL_TIER", detailed_office=True)
        assert aid == "MidriseApartment" and src == "RULE_RESIDENTIAL_TIER"


# ── TestApplyOverrides ────────────────────────────────────────────────────────

class TestApplyOverrides:
    def _classified_gdf(self) -> gpd.GeoDataFrame:
        gdf = _make_min_gdf(2, building_tag="office")
        gdf["archetype_id"] = "MediumOffice"
        gdf["archetype_confidence"] = "MEDIUM"
        gdf["archetype_source"] = "RULE_USE_CLASS_SIZE"
        return gdf

    def test_none_noop(self):
        gdf = self._classified_gdf()
        out = _apply_overrides(gdf, None)
        assert (out["archetype_id"] == "MediumOffice").all()

    def test_missing_file_noop(self, caplog):
        gdf = self._classified_gdf()
        out = _apply_overrides(gdf, Path(tempfile.mkdtemp()) / "nonexistent.csv")
        assert (out["archetype_id"] == "MediumOffice").all()

    def test_single_match(self):
        gdf = self._classified_gdf()
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text("osm_id,archetype_id,note\n1000,Warehouse,test override\n")
            out = _apply_overrides(gdf, p)
            assert out.loc[out["osm_id"] == "1000", "archetype_id"].iloc[0] == "Warehouse"
            assert out.loc[out["osm_id"] == "1000", "archetype_confidence"].iloc[0] == "HIGH"
            assert out.loc[out["osm_id"] == "1000", "archetype_source"].iloc[0] == "OVERRIDE_USER(test override)"
            assert out.loc[out["osm_id"] == "1001", "archetype_id"].iloc[0] == "MediumOffice"
        finally:
            shutil.rmtree(td)

    def test_lowite_override_reachable(self):
        gdf = self._classified_gdf()
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text("osm_id,archetype_id,note\n1000,LargeDataCenterLowITE,ite_flag\n")
            out = _apply_overrides(gdf, p)
            assert out.loc[out["osm_id"] == "1000", "archetype_id"].iloc[0] == "LargeDataCenterLowITE"
        finally:
            shutil.rmtree(td)

    def test_invalid_archetype_raises(self):
        gdf = self._classified_gdf()
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text("osm_id,archetype_id,note\n1000,NotAnArchetype,\n")
            with pytest.raises(SchemaError, match="not in 30-element vocab"):
                _apply_overrides(gdf, p)
        finally:
            shutil.rmtree(td)

    def test_duplicate_osm_id_raises(self):
        gdf = self._classified_gdf()
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text("osm_id,archetype_id,note\n1000,Warehouse,\n1000,Hospital,\n")
            with pytest.raises(SchemaError, match="duplicate"):
                _apply_overrides(gdf, p)
        finally:
            shutil.rmtree(td)


# ── TestClassifyBuildingRow ───────────────────────────────────────────────────

class TestClassifyBuildingRow:
    def test_rule_2b_heuristic_default_source(self):
        r = _row(building_tag="apartments", function_tag="", levels=pd.NA,
                 height_m=float("nan"), provenance_function_tag="OSM_MISSING")
        aid, conf, src = classify_building(r)
        assert aid == "MidriseApartment"
        assert src == "RULE_RESIDENTIAL_TIER,HEURISTIC_DEFAULT"

    def test_rule_17a_building_yes_office_default(self):
        # E-R3-2: building=yes, levels=2, footprint=800 → total=1600 → MediumOffice/LOW/FALLBACK_SIZE_DEFAULT
        r = _row(building_tag="yes", function_tag="", data_quality_flag="generic_tag",
                 provenance_building_tag="OSM_GENERIC", provenance_function_tag="OSM_MISSING",
                 levels=pd.array([2], dtype="Int64")[0], provenance_levels="OSM_OBSERVED")
        aid, conf, src = classify_building(r)
        assert aid == "MediumOffice"
        assert conf == "LOW"
        assert src == "FALLBACK_SIZE_DEFAULT"

    def test_rule_4b_cafe(self):
        r = _row(function_tag="cafe", provenance_function_tag="OSM_OBSERVED",
                 levels=pd.array([1], dtype="Int64")[0], provenance_levels="OSM_OBSERVED")
        aid, conf, src = classify_building(r)
        assert aid == "QuickServiceRestaurant"
        assert conf == "HIGH"
        assert src == "RULE_FUNCTION_TAG"

    def test_rule_6b_secondary_school(self):
        r = _row(function_tag="school", footprint_area_m2=6000.0,
                 provenance_function_tag="OSM_OBSERVED", provenance_building_tag="OSM_OBSERVED")
        aid, conf, src = classify_building(r)
        assert aid == "SecondarySchool"
        assert src == "RULE_FUNCTION_TAG_SIZE,ASSUMPTION_DOE_PROTOTYPE_DERIVED"
        assert conf == "HIGH"

    def test_rule_6c_primary_school(self):
        r = _row(function_tag="kindergarten", footprint_area_m2=800.0,
                 provenance_function_tag="OSM_OBSERVED", provenance_building_tag="OSM_OBSERVED")
        aid, conf, src = classify_building(r)
        assert aid == "PrimarySchool"
        assert conf == "HIGH"

    def test_rule_1a_super_tall(self):
        r = _row(building_tag="office", levels=pd.array([42], dtype="Int64")[0],
                 provenance_levels="OSM_OBSERVED", provenance_building_tag="OSM_OBSERVED")
        aid, conf, src = classify_building(r)
        assert aid == "SuperTallBuilding"
        assert src == "RULE_HIGHRISE"

    def test_detailed_office_appends_token(self):
        r = _row(building_tag="office", footprint_area_m2=800.0,
                 provenance_function_tag="OSM_MISSING", provenance_building_tag="OSM_OBSERVED")
        aid, conf, src = classify_building(r, detailed_office=True)
        assert aid == "MediumOfficeDetailed"
        assert "DETAILED_OFFICE" in src


# ── TestBuildingClassifier ────────────────────────────────────────────────────

class TestBuildingClassifier:
    def _simple_gdf(self) -> gpd.GeoDataFrame:
        return _make_min_gdf(3, building_tag="office", footprint_area_m2=800.0)

    def test_byte_equality(self):
        gdf = self._simple_gdf()
        out = BuildingClassifier().classify(gdf)
        pd.testing.assert_frame_equal(
            gdf.reset_index(drop=True),
            out[gdf.columns].reset_index(drop=True),
        )

    def test_26_col_schema(self):
        out = BuildingClassifier().classify(self._simple_gdf())
        assert list(out.columns[-3:]) == ["archetype_id", "archetype_confidence", "archetype_source"]
        assert len(out.columns) == 26

    def test_determinism(self):
        gdf = self._simple_gdf()
        clf = BuildingClassifier()
        out1 = clf.classify(gdf)
        out2 = clf.classify(gdf)
        pd.testing.assert_frame_equal(out1, out2)

    def test_idempotency(self):
        gdf = self._simple_gdf()
        clf = BuildingClassifier()
        out1 = clf.classify(gdf)
        in_cols = list(gdf.columns)
        out2 = clf.classify(out1[in_cols])
        assert list(out1["archetype_id"]) == list(out2["archetype_id"])

    def test_all_archetype_ids_valid(self):
        out = BuildingClassifier().classify(self._simple_gdf())
        assert out["archetype_id"].isin(_VALID_30).all()

    def test_all_confidence_valid(self):
        out = BuildingClassifier().classify(self._simple_gdf())
        assert out["archetype_confidence"].isin({"HIGH", "MEDIUM", "LOW"}).all()

    def test_all_source_tokens_valid(self):
        import re
        OVERRIDE_RE = re.compile(r"^OVERRIDE_USER\(.*\)$")
        from openubem.semantic.building_classifier import _READ_SIDE_TOKENS
        out = BuildingClassifier().classify(self._simple_gdf())
        for src in out["archetype_source"]:
            if OVERRIDE_RE.match(str(src)):
                continue
            for tok in str(src).split(","):
                assert tok.strip() in _READ_SIDE_TOKENS, f"unexpected token: {tok!r}"

    def test_detailed_office_produces_detailed(self):
        gdf = _make_min_gdf(2, building_tag="office", footprint_area_m2=800.0)
        out = BuildingClassifier(detailed_office=True).classify(gdf)
        assert (out["archetype_id"] == "MediumOfficeDetailed").all()

    def test_overrides_applied(self):
        gdf = self._simple_gdf()
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text("osm_id,archetype_id,note\n1000,Warehouse,test\n")
            out = BuildingClassifier(overrides_path=p).classify(gdf)
            assert out.loc[out["osm_id"] == "1000", "archetype_id"].iloc[0] == "Warehouse"
            assert out.loc[out["osm_id"] == "1000", "archetype_source"].iloc[0] == "OVERRIDE_USER(test)"
        finally:
            shutil.rmtree(td)


# ── TestAllFallbackNeighbourhood ──────────────────────────────────────────────

class TestAllFallbackNeighbourhood:
    def test_all_fallback_warning(self, caplog):
        # E-R3-2: building=yes now routes to FALLBACK_SIZE_DEFAULT offices (not OpenUBEMUnknown)
        import logging
        gdf = _make_min_gdf(
            3,
            building_tag="yes",
            function_tag="",
            data_quality_flag="generic_tag",
            provenance_building_tag="OSM_GENERIC",
            provenance_function_tag="OSM_MISSING",
        )
        # give observed levels so _impute_levels doesn't confuse the rule path
        gdf["levels"] = pd.array([2, 2, 2], dtype="Int64")
        gdf["provenance_levels"] = "OSM_OBSERVED"

        with caplog.at_level(logging.WARNING, logger="openubem.semantic"):
            out = BuildingClassifier().classify(gdf)

        assert len(out) == 3
        # all rows: FALLBACK_SIZE_DEFAULT, LOW, office archetype
        assert (out["archetype_source"].str.startswith("FALLBACK_SIZE_DEFAULT")).all()
        assert (out["archetype_confidence"] == "LOW").all()
        assert out["archetype_id"].isin({"SmallOffice", "MediumOffice", "LargeOffice"}).all()
        warnings = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warnings) == 1
        payload = json.loads(warnings[0].message)
        assert payload == {
            "event": "all_fallback_archetype",
            "n_rows": 3,
            "archetype_id": "OpenUBEMUnknown",
        }


# ── TestSchemaValidation ──────────────────────────────────────────────────────

class TestSchemaValidation:
    def _valid_23(self) -> gpd.GeoDataFrame:
        return _make_min_gdf(2, building_tag="office")

    def _valid_26(self) -> gpd.GeoDataFrame:
        gdf = BuildingClassifier().classify(self._valid_23())
        return gdf

    def test_valid_23_passes(self):
        _validate_input_schema(self._valid_23())

    def test_22_col_raises(self):
        gdf = self._valid_23().drop(columns=["osm_id"])
        with pytest.raises(SchemaError):
            _validate_input_schema(gdf)

    def test_wrong_order_raises(self):
        gdf = self._valid_23()
        cols = list(gdf.columns)
        cols[1], cols[2] = cols[2], cols[1]
        with pytest.raises(SchemaError):
            _validate_input_schema(gdf[cols])

    def test_valid_26_passes(self):
        _validate_output_schema(self._valid_26())

    def test_bad_archetype_id_raises(self):
        gdf = self._valid_26().copy()
        gdf.loc[gdf.index[0], "archetype_id"] = "NotReal"
        with pytest.raises(SchemaError):
            _validate_output_schema(gdf)

    def test_bad_confidence_raises(self):
        gdf = self._valid_26().copy()
        gdf.loc[gdf.index[0], "archetype_confidence"] = "VERY_HIGH"
        with pytest.raises(SchemaError):
            _validate_output_schema(gdf)

    def test_bad_source_token_raises(self):
        gdf = self._valid_26().copy()
        gdf.loc[gdf.index[0], "archetype_source"] = "MADE_UP_TOKEN"
        with pytest.raises(SchemaError):
            _validate_output_schema(gdf)

    def test_override_user_token_passes(self):
        gdf = self._valid_26().copy()
        gdf.loc[gdf.index[0], "archetype_source"] = "OVERRIDE_USER(some note)"
        _validate_output_schema(gdf)

    def test_openubem_unknown_high_confidence_raises(self):
        gdf = self._valid_26().copy()
        gdf.loc[gdf.index[0], "archetype_id"] = "OpenUBEMUnknown"
        gdf.loc[gdf.index[0], "archetype_confidence"] = "HIGH"
        gdf.loc[gdf.index[0], "archetype_source"] = "RULE_FUNCTION_TAG"
        with pytest.raises(SchemaError):
            _validate_output_schema(gdf)


# ── TestSerialize ─────────────────────────────────────────────────────────────

class TestSerialize:
    def _classified(self) -> gpd.GeoDataFrame:
        return BuildingClassifier().classify(_make_min_gdf(3, building_tag="office"))

    def test_all_four_files_exist(self):
        td = tempfile.mkdtemp()
        try:
            BuildingClassifier().classify(_make_min_gdf(2, building_tag="office"), output_dir=Path(td))
            assert (Path(td) / "02_buildings_classified.gpkg").exists()
            assert (Path(td) / "02_buildings_classified.log").exists()
            assert (Path(td) / "02_buildings_classified.schema.json").exists()
            assert (Path(td) / "02_archetype_distribution.csv").exists()
        finally:
            shutil.rmtree(td)

    def test_gpkg_roundtrip_26_cols(self):
        td = tempfile.mkdtemp()
        try:
            BuildingClassifier().classify(_make_min_gdf(2, building_tag="office"), output_dir=Path(td))
            back = gpd.read_file(Path(td) / "02_buildings_classified.gpkg", layer="buildings")
            assert len(back.columns) == 26
        finally:
            shutil.rmtree(td)

    def test_schema_json_26_entries(self):
        td = tempfile.mkdtemp()
        try:
            BuildingClassifier().classify(_make_min_gdf(2, building_tag="office"), output_dir=Path(td))
            schema = json.loads((Path(td) / "02_buildings_classified.schema.json").read_text())
            assert len(schema["columns"]) == 26
            for entry in schema["columns"]:
                assert "name" in entry and "dtype" in entry and "provenance_role" in entry
        finally:
            shutil.rmtree(td)

    def test_distribution_csv_rows(self):
        td = tempfile.mkdtemp()
        try:
            BuildingClassifier().classify(_make_min_gdf(2, building_tag="office"), output_dir=Path(td))
            dist = pd.read_csv(Path(td) / "02_archetype_distribution.csv")
            assert "archetype_id" in dist.columns
            assert "n_rows" in dist.columns
            assert len(dist) >= 1
        finally:
            shutil.rmtree(td)

    def test_log_file_non_empty_and_contains_fallback(self):
        # D4: log file must be > 0 bytes and contain the "FALLBACK" token.
        td = tempfile.mkdtemp()
        try:
            BuildingClassifier().classify(_make_min_gdf(2, building_tag="office"), output_dir=Path(td))
            log_path = Path(td) / "02_buildings_classified.log"
            assert log_path.stat().st_size > 0, "log file must not be 0 bytes"
            log_text = log_path.read_text(encoding="utf-8")
            assert "FALLBACK" in log_text, "log must contain FALLBACK token"
        finally:
            shutil.rmtree(td)


# ── synthetic_30_gdf session fixture (plan T13) ───────────────────────────────

@pytest.fixture(scope="session")
def synthetic_30_gdf():
    """23-col GDF with one row per default-reachable archetype (25 rows).

    5 archetypes excluded from default-mode coverage:
    - SmallDataCenterLowITE, LargeDataCenterLowITE (PHASE_1_UNREACHABLE — covered
      via override CSV in test_lowite_reachable_via_override)
    - SmallOfficeDetailed, MediumOfficeDetailed, LargeOfficeDetailed
      (detailed_office=True only — covered in test_detailed_reachable_via_flag)
    Plan T13 stated "27 rows"; correct arithmetic is 30 − 2 − 3 = 25.
    Deviation logged in T13 progress entry.
    """
    fixture_path = Path("tests/fixtures/synthetic_30_archetype_coverage.gpkg")

    def _r(i, ft, bt, levels, area, **kw):
        d = dict(_ROW_DEFAULTS)
        d["geometry"] = box(i, 0, i + 1, 1)
        d["osm_id"] = f"SYN_{i + 1:03d}"
        d["function_tag"] = ft
        d["building_tag"] = bt
        d["levels"] = levels
        d["footprint_area_m2"] = area
        if ft:
            d["provenance_function_tag"] = "OSM_OBSERVED"
        d.update(kw)
        return d

    rows = [
        _r(0,  "",           "office",      pd.NA,   200.0),  # SmallOffice
        _r(1,  "",           "office",      pd.NA,   800.0),  # MediumOffice
        _r(2,  "",           "office",      pd.NA,  5000.0),  # LargeOffice
        _r(3,  "retail",     "",            pd.NA,   300.0),  # RetailStandalone
        _r(4,  "",           "strip_mall",  pd.NA,   400.0),  # RetailStripmall
        _r(5,  "",           "supermarket", pd.NA,  2000.0),  # SuperMarket
        _r(6,  "restaurant", "",            pd.NA,   200.0),  # FullServiceRestaurant
        _r(7,  "cafe",       "",            pd.NA,   150.0),  # QuickServiceRestaurant
        _r(8,  "hotel",      "",            2,       500.0,
           provenance_levels="OSM_OBSERVED"),                 # SmallHotel (levels<4)
        _r(9,  "hotel",      "",            5,      1000.0,
           provenance_levels="OSM_OBSERVED"),                 # LargeHotel (levels>=4)
        _r(10, "",           "apartments",  5,       600.0,
           provenance_levels="OSM_OBSERVED"),                 # MidriseApartment (levels<9)
        _r(11, "",           "apartments",  12,     1000.0,
           provenance_levels="OSM_OBSERVED"),                 # HighriseApartment (levels>=9)
        _r(12, "hospital",   "",            pd.NA,  2000.0),  # Hospital
        _r(13, "clinic",     "",            pd.NA,   400.0),  # Outpatient
        _r(14, "school",     "",            pd.NA,  1000.0),  # PrimarySchool (<5000 m²)
        _r(15, "school",     "",            pd.NA,  6000.0),  # SecondarySchool (>=5000 m²)
        _r(16, "university", "",            pd.NA,  3000.0),  # College
        _r(17, "government", "",            pd.NA,  1500.0),  # Courthouse
        _r(18, "",           "data_center", pd.NA,   300.0),  # SmallDataCenterHighITE (<500 m²)
        _r(19, "",           "data_center", pd.NA,   600.0),  # LargeDataCenterHighITE (>=500 m²)
        _r(20, "laboratory", "",            pd.NA,   800.0),  # Laboratory
        _r(21, "",           "warehouse",   pd.NA,  1000.0),  # Warehouse
        _r(22, "",           "office",      25,      800.0,
           provenance_levels="OSM_OBSERVED"),                 # TallBuilding (20<=levels<40)
        _r(23, "",           "office",      45,      800.0,
           provenance_levels="OSM_OBSERVED"),                 # SuperTallBuilding (levels>=40)
        _r(24, "",           "yes",         2,       200.0,   # SmallOffice (rule 17a E-R3-2)
           data_quality_flag="generic_tag",
           provenance_building_tag="OSM_GENERIC",
           provenance_function_tag="OSM_MISSING",
           provenance_levels="OSM_OBSERVED"),
    ]

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:32619")
    gdf["levels"] = gdf["levels"].astype("Int64")
    gdf["year_built"] = gdf["year_built"].astype("Int64")
    gdf["underground"] = gdf["underground"].astype("Int64")

    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(fixture_path, layer="synthetic", driver="GPKG")
    return gdf


# ── TestArchetypeCoverage30 ───────────────────────────────────────────────────

class TestArchetypeCoverage30:
    """Exercises every default-reachable archetype via synthetic_30_gdf (plan T13)."""

    # E-R3-2: building=yes now routes to FALLBACK_SIZE_DEFAULT offices; OpenUBEMUnknown
    # is no longer reachable from the synthetic fixture (row 24 yields SmallOffice).
    _EXPECTED_DEFAULT = frozenset({
        "SmallOffice", "MediumOffice", "LargeOffice",
        "RetailStandalone", "RetailStripmall", "SuperMarket",
        "FullServiceRestaurant", "QuickServiceRestaurant",
        "SmallHotel", "LargeHotel",
        "MidriseApartment", "HighriseApartment",
        "Hospital", "Outpatient",
        "PrimarySchool", "SecondarySchool", "College",
        "Courthouse",
        "SmallDataCenterHighITE", "LargeDataCenterHighITE",
        "Laboratory", "Warehouse",
        "TallBuilding", "SuperTallBuilding",
    })

    def test_default_mode_coverage(self, synthetic_30_gdf):
        out = BuildingClassifier().classify(synthetic_30_gdf)
        assert set(out["archetype_id"]) == self._EXPECTED_DEFAULT

    def test_lowite_reachable_via_override(self, synthetic_30_gdf):
        td = tempfile.mkdtemp()
        try:
            p = Path(td) / "ov.csv"
            p.write_text(
                "osm_id,archetype_id,note\n"
                "SYN_019,SmallDataCenterLowITE,ite_test\n"
                "SYN_020,LargeDataCenterLowITE,ite_test\n"
            )
            out = BuildingClassifier(overrides_path=p).classify(synthetic_30_gdf)
            produced = set(out["archetype_id"])
            assert "SmallDataCenterLowITE" in produced
            assert "LargeDataCenterLowITE" in produced
        finally:
            shutil.rmtree(td)

    def test_detailed_reachable_via_flag(self, synthetic_30_gdf):
        out = BuildingClassifier(detailed_office=True).classify(synthetic_30_gdf)
        produced = set(out["archetype_id"])
        assert "SmallOfficeDetailed" in produced
        assert "MediumOfficeDetailed" in produced
        assert "LargeOfficeDetailed" in produced


# ── TestExactBoundaries (E2) ──────────────────────────────────────────────────

@pytest.mark.parametrize("tag_overrides,levels_val,area_val,expected_archetype", [
    # area=500: exactly at Small/Medium boundary → MediumOffice (DESIGN §3C: 500 ≤ area < 4000)
    ({"building_tag": "office", "footprint_area_m2": 500.0}, pd.NA, 500.0, "MediumOffice"),
    # area=4000: exactly at Medium/Large boundary → LargeOffice (DESIGN §3C: area ≥ 4000)
    ({"building_tag": "office", "footprint_area_m2": 4000.0}, pd.NA, 4000.0, "LargeOffice"),
    # area=5000 with school → SecondarySchool (DESIGN §3C rule 6b: area ≥ 5000)
    ({"function_tag": "school", "footprint_area_m2": 5000.0,
      "provenance_function_tag": "OSM_OBSERVED"}, pd.NA, 5000.0, "SecondarySchool"),
    # levels=4 with hotel → LargeHotel (DESIGN §3C rule 3a: levels ≥ 4)
    ({"function_tag": "hotel", "provenance_function_tag": "OSM_OBSERVED",
      "provenance_levels": "OSM_OBSERVED"}, 4, 800.0, "LargeHotel"),
    # levels=9 with residential → HighriseApartment (DESIGN §3C rule 2a: levels ≥ 9)
    ({"building_tag": "apartments", "provenance_levels": "OSM_OBSERVED"}, 9, 800.0, "HighriseApartment"),
    # levels=20 with commercial → TallBuilding (DESIGN §3C rule 1b: 20 ≤ levels < 40)
    ({"building_tag": "office", "provenance_levels": "OSM_OBSERVED"}, 20, 800.0, "TallBuilding"),
    # levels=40 with commercial → SuperTallBuilding (DESIGN §3C rule 1a: levels ≥ 40)
    ({"building_tag": "office", "provenance_levels": "OSM_OBSERVED"}, 40, 800.0, "SuperTallBuilding"),
])
class TestExactBoundaries:
    def test_boundary(self, tag_overrides, levels_val, area_val, expected_archetype):
        kw = {"footprint_area_m2": area_val}
        kw.update(tag_overrides)
        if levels_val is not pd.NA:
            kw["levels"] = pd.array([levels_val], dtype="Int64")[0]
        r = _row(**kw)
        aid, _conf, _src = classify_building(r)
        assert aid == expected_archetype, (
            f"area={area_val}, levels={levels_val} → expected {expected_archetype}, got {aid}"
        )


# ── TestInputDtypeValidation (E3) ─────────────────────────────────────────────

class TestInputDtypeValidation:
    def test_float64_levels_raises_valueerror(self):
        gdf = _make_min_gdf(2, building_tag="office")
        gdf["levels"] = gdf["levels"].astype("float64")
        with pytest.raises(ValueError, match="levels"):
            _validate_input_schema(gdf)

    def test_int64_levels_raises_valueerror(self):
        gdf = _make_min_gdf(2, building_tag="office")
        gdf["levels"] = gdf["levels"].astype("float64").fillna(0).astype("int64")
        with pytest.raises(ValueError, match="levels"):
            _validate_input_schema(gdf)

    def test_correct_dtypes_passes(self):
        gdf = _make_min_gdf(2, building_tag="office")
        _validate_input_schema(gdf)


# ── TestEmptyGDFGuard (E4) ────────────────────────────────────────────────────

class TestEmptyGDFGuard:
    def test_zero_row_input_returns_26_cols_no_exception(self):
        gdf_full = _make_min_gdf(2, building_tag="office")
        gdf_empty = gdf_full.iloc[0:0].copy()
        assert len(gdf_empty) == 0
        out = BuildingClassifier().classify(gdf_empty)
        assert len(out) == 0
        assert len(out.columns) == 26
        assert "archetype_id" in out.columns
        assert "archetype_confidence" in out.columns
        assert "archetype_source" in out.columns


# ── TestLabelledTop1Accuracy (OQ-7 L2) ───────────────────────────────────────

# Coarse class map per F5 / OQ-7 plan §5.5
_COARSE_CLASS_MAP: dict[str, str] = {
    "MidriseApartment": "residential",
    "HighriseApartment": "residential",
    **{aid: "commercial" for aid in _VALID_30 - {"MidriseApartment", "HighriseApartment"}},
}


def _run_labelled_fixture():
    """Classify both gpkg fixtures and merge with labelled CSV. Returns merged DataFrame."""
    csv_path = Path("tests/fixtures/labelled_archetypes_50.csv")
    if not csv_path.exists():
        return None
    lab = pd.read_csv(csv_path, comment="#")
    bos = gpd.read_file("tests/fixtures/boston_downtown_500m.gpkg")
    chi = gpd.read_file("tests/fixtures/chicago_loop_500m.gpkg")
    for gdf in (bos, chi):
        for col in ("levels", "year_built", "underground"):
            if col in gdf.columns:
                gdf[col] = gdf[col].astype("Int64")
    def _reorder(gdf):
        geom_col = gdf.geometry.name
        cols = [geom_col] + [c for c in _INPUT_SCHEMA_COLUMNS if c != geom_col and c in gdf.columns]
        return gdf[cols]
    bos = _reorder(bos)
    chi = _reorder(chi)
    clf = BuildingClassifier()
    bos_out = clf.classify(bos)
    chi_out = clf.classify(chi)
    results = pd.concat([
        bos_out[["osm_id", "archetype_id"]],
        chi_out[["osm_id", "archetype_id"]],
    ])
    results["osm_id"] = results["osm_id"].astype(str)
    lab["osm_id"] = lab["osm_id"].astype(str)
    return lab.merge(results, on="osm_id", how="left")


class TestLabelledTop1Accuracy:
    """OQ-7 L2: live accuracy gate against ratified 50-label fixture (F5, F6)."""

    def test_coarse_top1(self):
        merged = _run_labelled_fixture()
        if merged is None:
            pytest.skip("labelled fixture not found")
        pred_coarse = merged["archetype_id"].map(_COARSE_CLASS_MAP)
        acc = (pred_coarse == merged["expected_coarse_class"]).mean()
        assert acc >= 0.90, f"coarse top-1 {acc:.1%} < 90% gate"

    def test_fine_top1(self):
        merged = _run_labelled_fixture()
        if merged is None:
            pytest.skip("labelled fixture not found")
        acc = (merged["archetype_id"] == merged["expected_archetype"]).mean()
        assert acc >= 0.70, f"fine top-1 {acc:.1%} < 70% gate"

    def test_archetype_coverage_min10(self):
        merged = _run_labelled_fixture()
        if merged is None:
            pytest.skip("labelled fixture not found")
        n_distinct = merged["expected_archetype"].nunique()
        assert n_distinct >= 10, f"only {n_distinct} distinct archetypes in fixture (need ≥10)"
