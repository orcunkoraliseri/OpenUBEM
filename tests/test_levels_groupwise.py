"""Tests for T05 — group-wise stratified `levels` imputation (building_classifier.py).

Covers the wave-2b PINNED CONTRACT: `_impute_levels`'s third branch (both `levels`
and `height_m` absent) now returns a use_class-stratified median (fit on
observed-levels rows only, no leakage) instead of the flat `1` /
`HEURISTIC_DEFAULT`. The first two branches (OSM_OBSERVED, HEURISTIC_HEIGHT) are
unchanged and are re-asserted here to prove the rename did not touch them.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from openubem.semantic.building_classifier import (
    BuildingClassifier,
    _impute_levels,
)

# ── row / GDF factories (mirrors tests/test_building_classifier.py conventions) ─

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


def _lev(n: int):
    return pd.array([n], dtype="Int64")[0]


def _make_gdf(rows: "list[dict]") -> gpd.GeoDataFrame:
    built = []
    for i, overrides in enumerate(rows):
        d = dict(_ROW_DEFAULTS)
        d["geometry"] = box(i, 0, i + 1, 1)
        d["osm_id"] = str(1000 + i)
        d.update(overrides)
        built.append(d)
    gdf = gpd.GeoDataFrame(built, geometry="geometry", crs="EPSG:32619")
    gdf["levels"] = gdf["levels"].astype("Int64")
    gdf["year_built"] = gdf["year_built"].astype("Int64")
    gdf["underground"] = gdf["underground"].astype("Int64")
    for col in ("height_m", "roof_height_m", "footprint_area_m2", "perimeter_m"):
        gdf[col] = gdf[col].astype("float64")
    return gdf


# ── TestImputeLevelsGroupwiseUnit — direct _impute_levels contract ─────────────

class TestImputeLevelsGroupwiseUnit:
    def test_group_median_used_when_present(self):
        r = _row(levels=pd.NA, height_m=float("nan"))
        lev, src = _impute_levels(
            r,
            use_class="commercial",
            levels_group_median={"commercial": 8, "residential": 3},
            levels_global_median=5,
        )
        assert lev == 8 and src == "GROUPMEDIAN_LEVELS_MED"

    def test_global_median_fallback_when_stratum_empty(self):
        r = _row(levels=pd.NA, height_m=float("nan"))
        lev, src = _impute_levels(
            r,
            use_class="industrial",  # not a key in the group lookup -> empty stratum
            levels_group_median={"commercial": 8, "residential": 3},
            levels_global_median=5,
        )
        assert lev == 5 and src == "GROUPMEDIAN_LEVELS_MED"

    def test_low_default_when_no_observed_levels_anywhere(self):
        r = _row(levels=pd.NA, height_m=float("nan"))
        lev, src = _impute_levels(
            r,
            use_class="commercial",
            levels_group_median={},
            levels_global_median=None,
        )
        assert lev == 1 and src == "LEVELS_DEFAULT_LOW"

    def test_height_path_untouched_even_with_lookup_available(self):
        r = _row(levels=pd.NA, height_m=7.0)
        lev, src = _impute_levels(
            r,
            use_class="commercial",
            levels_group_median={"commercial": 8},
            levels_global_median=8,
        )
        assert lev == 2 and src == "HEURISTIC_HEIGHT"

    def test_observed_path_untouched_even_with_lookup_available(self):
        r = _row(levels=_lev(5), height_m=float("nan"))
        lev, src = _impute_levels(
            r,
            use_class="commercial",
            levels_group_median={"commercial": 8},
            levels_global_median=8,
        )
        assert lev == 5 and src == "OSM_OBSERVED"

    def test_no_kwargs_defaults_to_low(self):
        # Calling with no lookup kwargs at all (legacy call-site shape) must not
        # silently resurrect the old HEURISTIC_DEFAULT token.
        r = _row(levels=pd.NA, height_m=float("nan"))
        lev, src = _impute_levels(r)
        assert lev == 1 and src == "LEVELS_DEFAULT_LOW"


# ── TestBuildLevelsMedianLookup — no-leakage lookup construction ───────────────

class TestBuildLevelsMedianLookup:
    def test_medians_from_observed_rows_only_no_leakage(self):
        gdf = _make_gdf([
            {"building_tag": "office", "levels": _lev(8)},
            {"building_tag": "office", "levels": _lev(8)},
            {"building_tag": "office", "levels": _lev(9)},
            {"building_tag": "apartments", "levels": _lev(4)},
            {"building_tag": "office", "levels": pd.NA},  # missing -> must not leak in
        ])
        bc = BuildingClassifier()
        group_median, global_median = bc._build_levels_median_lookup(gdf)
        assert group_median["commercial"] == 8
        assert group_median["residential"] == 4
        assert global_median == 8  # median of the 4 OBSERVED rows [8, 8, 9, 4]

    def test_empty_stratum_absent_from_lookup(self):
        gdf = _make_gdf([
            {"building_tag": "apartments", "levels": _lev(5)},
            {"building_tag": "apartments", "levels": _lev(6)},
            {"building_tag": "office", "levels": pd.NA},
        ])
        bc = BuildingClassifier()
        group_median, global_median = bc._build_levels_median_lookup(gdf)
        assert "commercial" not in group_median
        assert group_median["residential"] in (5, 6)  # median(5,6) rounded
        assert global_median in (5, 6)

    def test_no_observed_levels_anywhere_returns_empty(self):
        gdf = _make_gdf([
            {"building_tag": "office", "levels": pd.NA},
            {"building_tag": "apartments", "levels": pd.NA},
        ])
        bc = BuildingClassifier()
        group_median, global_median = bc._build_levels_median_lookup(gdf)
        assert group_median == {}
        assert global_median is None


# ── TestGroupwiseEndToEnd — full BuildingClassifier().classify() pipeline ──────

class TestGroupwiseEndToEnd:
    def test_office_stock_imputes_group_median_not_default(self):
        # Plan T05 "how to test": a both-absent office in a stock of 8-storey
        # offices imputes ~8 not 1. footprint=1200 m2 makes the two outcomes
        # land on different archetype tiers (LOW_MAX=2322, MED_MAX=9290 m2
        # total floor area = footprint * levels), so the tier itself proves
        # which level count was actually used:
        #   level=1  -> total=1200  -> SmallOffice
        #   level=8  -> total=9600  -> LargeOffice
        rows = [
            {"building_tag": "office", "levels": _lev(8), "footprint_area_m2": 1200.0},
            {"building_tag": "office", "levels": _lev(8), "footprint_area_m2": 1200.0},
            {"building_tag": "office", "levels": _lev(8), "footprint_area_m2": 1200.0},
            {"building_tag": "office", "levels": _lev(8), "footprint_area_m2": 1200.0},
            {"building_tag": "office", "levels": _lev(8), "footprint_area_m2": 1200.0},
            {"building_tag": "apartments", "levels": _lev(2), "footprint_area_m2": 600.0},
            # target: both absent
            {"building_tag": "office", "levels": pd.NA, "height_m": float("nan"),
             "footprint_area_m2": 1200.0},
        ]
        gdf = _make_gdf(rows)
        out = BuildingClassifier().classify(gdf)

        target = out.iloc[[6]]
        assert target["archetype_id"].iloc[0] == "LargeOffice"

    def test_residential_group_median_token_and_medium_confidence(self):
        rows = [
            {"building_tag": "apartments", "levels": _lev(8)},
            {"building_tag": "apartments", "levels": _lev(8)},
            {"building_tag": "apartments", "levels": _lev(8)},
            {"building_tag": "apartments", "levels": _lev(8)},
            # target: both absent, same use_class
            {"building_tag": "apartments", "levels": pd.NA, "height_m": float("nan")},
        ]
        gdf = _make_gdf(rows)
        out = BuildingClassifier().classify(gdf)

        target = out.iloc[4]
        assert target["archetype_id"] == "MidriseApartment"  # 8 < 9 threshold
        assert target["archetype_source"] == "RULE_RESIDENTIAL_TIER,GROUPMEDIAN_LEVELS_MED"
        assert target["archetype_confidence"] == "MEDIUM"

    def test_no_observed_levels_anywhere_gives_low_default_token(self):
        rows = [
            {"building_tag": "apartments", "levels": pd.NA, "height_m": float("nan")},
            {"building_tag": "apartments", "levels": pd.NA, "height_m": float("nan")},
        ]
        gdf = _make_gdf(rows)
        out = BuildingClassifier().classify(gdf)

        assert (out["archetype_id"] == "MidriseApartment").all()
        assert (out["archetype_source"] == "RULE_RESIDENTIAL_TIER,LEVELS_DEFAULT_LOW").all()
        # the legacy token must never appear post-rename
        assert not out["archetype_source"].str.contains("HEURISTIC_DEFAULT").any()

    def test_height_present_rows_still_heuristic_height_in_full_pipeline(self):
        rows = [
            {"building_tag": "apartments", "levels": _lev(8)},
            {"building_tag": "apartments", "levels": _lev(8)},
            # target: height present, levels absent -> HEURISTIC_HEIGHT untouched
            {"building_tag": "apartments", "levels": pd.NA, "height_m": 7.0},
        ]
        gdf = _make_gdf(rows)
        out = BuildingClassifier().classify(gdf)

        target = out.iloc[2]
        assert target["archetype_source"] == "RULE_RESIDENTIAL_TIER,HEURISTIC_HEIGHT"
