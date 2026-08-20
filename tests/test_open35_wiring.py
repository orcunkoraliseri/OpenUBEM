"""OPEN-35 T05/T06 (PLAN_board-17-ready-2026-08-19.md): proves T04's Scope B agreement
fix is actually reachable from a real build/aggregate/parse -- not just unit-provable
in isolation.

T05 covered the two call sites wired within the three allowed production files
(openubem/idf/builder.py, openubem/results/aggregator.py). T06 closes the third:
openubem/results/parser.py, wired via openubem/results/__init__.py's widened
manifest_row (archetype_source, _use_class, _levels_group_median,
_levels_global_median -- see aggregate_results()'s per-building loop).
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from openubem.geometry.footprint import derive_num_floors
from openubem.idf.builder import _derive_num_floors_wired as _builder_wired
from openubem.idf.builder import _fleet_levels_medians as _builder_medians
from openubem.results.aggregator import _derive_num_floors_wired as _agg_wired
from openubem.results.aggregator import _fleet_levels_medians as _agg_medians
from openubem.results.aggregator import compute_neighbourhood_summary, join_results
from openubem.results.parser import _derive_num_floors_wired as _parser_wired
from openubem.semantic.building_classifier import _normalise_use_class


def _poly(x_offset: float = 0.0) -> Polygon:
    return Polygon([
        (330000 + x_offset, 4690000),
        (330014 + x_offset, 4690000),
        (330014 + x_offset, 4690014),
        (330000 + x_offset, 4690014),
    ])


def _fleet_gdf() -> gpd.GeoDataFrame:
    """8 observed-levels residential rows (median levels = 5) + 1 target row with no
    levels/height that consumed the group-median fallback (archetype_source carries
    GROUPMEDIAN_LEVELS_MED), matching the Scope B population's own shape."""
    rows = []
    for i, lev in enumerate([3.0, 4.0, 5.0, 5.0, 5.0, 6.0, 7.0, 9.0]):
        rows.append({
            "osm_id": f"way/OBS{i}", "levels": lev, "height_m": float("nan"),
            "function_tag": "apartments", "building_tag": "",
            "footprint_area_m2": 100.0, "archetype_source": "RULE_RESIDENTIAL_TIER",
            "geometry": _poly(i * 100),
        })
    rows.append({
        "osm_id": "way/TARGET", "levels": float("nan"), "height_m": float("nan"),
        "function_tag": "apartments", "building_tag": "",
        "footprint_area_m2": 100.0,
        "archetype_source": "RULE_RESIDENTIAL_TIER,GROUPMEDIAN_LEVELS_MED",
        "geometry": _poly(800.0),
    })
    return gpd.GeoDataFrame(rows, crs="EPSG:32618")


class TestBuilderWiring:
    def test_medians_match_classifier(self):
        gdf = _fleet_gdf()
        group_median, global_median = _builder_medians(gdf)
        assert group_median["residential"] == 5
        assert global_median == 5

    def test_target_row_gets_median_not_one(self):
        gdf = _fleet_gdf()
        target = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0]
        n_floors = _builder_wired(target, gdf)
        assert n_floors == 5
        assert n_floors != 1

    def test_non_scope_b_row_unaffected(self):
        gdf = _fleet_gdf()
        row = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0].copy()
        row["archetype_source"] = "RULE_RESIDENTIAL_TIER"
        wired = _builder_wired(row, gdf)
        plain = derive_num_floors(row)
        assert wired == plain == 1

    def test_row_with_observed_levels_unaffected(self):
        gdf = _fleet_gdf()
        row = gdf[gdf["osm_id"] == "way/OBS0"].iloc[0]
        wired = _builder_wired(row, gdf)
        plain = derive_num_floors(row)
        assert wired == plain == 3


class TestAggregatorWiring:
    def test_medians_match_classifier(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        assert group_median["residential"] == 5
        assert global_median == 5

    def test_target_row_gets_median_not_one(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        target = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0]
        n_floors = _agg_wired(target, group_median, global_median)
        assert n_floors == 5
        assert n_floors != 1

    def test_non_scope_b_row_unaffected(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        row = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0].copy()
        row["archetype_source"] = "RULE_RESIDENTIAL_TIER"
        wired = _agg_wired(row, group_median, global_median)
        plain = derive_num_floors(row)
        assert wired == plain == 1

    def test_end_to_end_through_compute_neighbourhood_summary(self):
        """The wiring must actually move the aggregate floor area, not just the
        standalone helper -- exercised via the real compute_neighbourhood_summary path.
        neighbourhood_gwp_total_kgco2 = Sigma(gwp_total_kgco2_m2 * floor_area), so with
        gwp_total_kgco2_m2=1.0 it reads back the floor area directly: footprint(100) *
        num_floors. 500 (median=5) proves the fix is live; 100 (num_floors=1) would mean
        it is not."""
        gdf = _fleet_gdf()
        metrics = pd.DataFrame([{
            "osm_id": "way/TARGET",
            "simulation_status": "success",
            "heating_eui_kwh_m2": 10.0, "cooling_eui_kwh_m2": 5.0,
            "lighting_eui_kwh_m2": 2.0, "equipment_eui_kwh_m2": 3.0,
            "total_eui_kwh_m2": 20.0,
            "gwp_total_kgco2_m2": 1.0,
        }])
        result = join_results(gdf, metrics)
        summary = compute_neighbourhood_summary(result)
        assert summary["neighbourhood_gwp_total_kgco2"] == 500.0


def _as_manifest_row(row: pd.Series, group_median: dict, global_median) -> pd.Series:
    """Build the manifest_row shape aggregate_results() (openubem/results/__init__.py)
    hands to parse_building() -- archetype_source is a real copied column;
    _use_class/_levels_group_median/_levels_global_median are the T06-added fields
    carrying the classifier's own _normalise_use_class()/_build_levels_median_lookup()
    results, since parse_building() has no fleet-wide gdf of its own to compute them."""
    manifest_row = row.copy()
    manifest_row["_use_class"] = _normalise_use_class(row)[0]
    manifest_row["_levels_group_median"] = group_median
    manifest_row["_levels_global_median"] = global_median
    return manifest_row


class TestParserWiring:
    def test_medians_match_classifier(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        assert group_median["residential"] == 5
        assert global_median == 5

    def test_target_row_gets_median_not_one(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        target = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0]
        manifest_row = _as_manifest_row(target, group_median, global_median)
        n_floors = _parser_wired(manifest_row)
        assert n_floors == 5
        assert n_floors != 1

    def test_non_scope_b_row_unaffected(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        row = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0].copy()
        row["archetype_source"] = "RULE_RESIDENTIAL_TIER"
        manifest_row = _as_manifest_row(row, group_median, global_median)
        wired = _parser_wired(manifest_row)
        plain = derive_num_floors(row)
        assert wired == plain == 1

    def test_row_with_observed_levels_unaffected(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        row = gdf[gdf["osm_id"] == "way/OBS0"].iloc[0]
        manifest_row = _as_manifest_row(row, group_median, global_median)
        wired = _parser_wired(manifest_row)
        plain = derive_num_floors(row)
        assert wired == plain == 3

    def test_missing_median_fields_fall_back_to_one(self):
        """A manifest_row that never received the T06 fields (e.g. an older caller)
        must not crash -- it degrades to the pre-T06 fallback of 1, same as
        derive_num_floors() with no kwargs, never a KeyError."""
        gdf = _fleet_gdf()
        target = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0].copy()
        n_floors = _parser_wired(target)
        assert n_floors == 1


class TestThreeWayAgreement:
    """OPEN-35 T06 hard bound: the builder, aggregator and parser wired paths must
    change the SAME rows, by set membership. This pins that agreement so a future
    change to any one path cannot silently desynchronise it from the other two."""

    def test_all_three_paths_agree_on_scope_b_row(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        target = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0]

        builder_result = _builder_wired(target, gdf)
        agg_result = _agg_wired(target, group_median, global_median)
        parser_result = _parser_wired(_as_manifest_row(target, group_median, global_median))

        assert builder_result == agg_result == parser_result == 5

    def test_all_three_paths_agree_on_non_scope_b_row(self):
        gdf = _fleet_gdf()
        group_median, global_median = _agg_medians(gdf)
        row = gdf[gdf["osm_id"] == "way/TARGET"].iloc[0].copy()
        row["archetype_source"] = "RULE_RESIDENTIAL_TIER"

        builder_result = _builder_wired(row, gdf)
        agg_result = _agg_wired(row, group_median, global_median)
        parser_result = _parser_wired(_as_manifest_row(row, group_median, global_median))

        assert builder_result == agg_result == parser_result == 1

    def test_all_three_paths_agree_fleet_wide_on_scope_b_census(self):
        """Independent re-derivation against the authoritative 21-osm_id scope
        (openubem/outputs/comparisons/open35_fallback_agreement_scope.csv), across all
        12 phaseE cells, using the actual wired helpers -- not a re-implementation.
        Skips (not fails) if the phaseE fixture directory or scope CSV is unavailable
        in the current environment, matching this repo's other fleet-wide census tests."""
        import pytest
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        phasee = root / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
        scope_csv = root / "openubem" / "outputs" / "comparisons" / "open35_fallback_agreement_scope.csv"
        if not phasee.exists() or not scope_csv.exists():
            pytest.skip("phaseE fixtures or scope CSV not present in this environment")

        import geopandas as gpd
        from openubem.geometry.footprint import derive_num_floors as _dnf
        from openubem.semantic.building_classifier import (
            BuildingClassifier,
            _INPUT_SCHEMA_COLUMNS,
        )

        cells = [
            "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
            "la_centre", "la_rural", "la_suburban", "la_urban",
            "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
        ]
        changed_b: set[str] = set()
        changed_a: set[str] = set()
        changed_p: set[str] = set()
        for cell in cells:
            fleet = gpd.read_file(phasee / cell / "01_buildings.gpkg")
            fleet = fleet[_INPUT_SCHEMA_COLUMNS].copy()
            fleet["levels"] = fleet["levels"].astype("Int64")
            clf = BuildingClassifier()
            classified = clf.classify(fleet.copy())
            work = fleet.copy()
            work["archetype_source"] = classified["archetype_source"]
            gm, gbm = _agg_medians(work)
            for idx in work.index:
                row = work.loc[idx]
                osm_id = str(row["osm_id"])
                old = _dnf(row)
                if old != _builder_wired(row, work):
                    changed_b.add(osm_id)
                if old != _agg_wired(row, gm, gbm):
                    changed_a.add(osm_id)
                if old != _parser_wired(_as_manifest_row(row, gm, gbm)):
                    changed_p.add(osm_id)

        scope = pd.read_csv(scope_csv)
        expected = set(scope.loc[scope["changed_scope_b"] == True, "osm_id"].astype(str))

        assert changed_b == expected
        assert changed_a == expected
        assert changed_p == expected
        assert changed_b == changed_a == changed_p
