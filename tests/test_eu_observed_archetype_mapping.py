"""Fail-closed EU-04 observed-building archetype mapping tests."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from openubem.semantic.european_archetype_mapping import (
    MISSING_OBSERVED_DWELLING_COUNT,
    MISSING_OBSERVED_STOREY_COUNT,
    TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14,
    TYPOLOGY_SIGNALS_DISAGREE,
    _observed_dwellings,
    compute_footprint_adjacency,
    derive_bdtopo_building_type,
    map_observed_building_to_tabula,
    write_eu02_archetype_mapping_readiness,
)


REPO_ROOT = Path(__file__).parent.parent
MANIFEST_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu02"


def _row(**overrides) -> pd.Series:
    values = {
        "osm_id": "way/test",
        "building_tag": "apartments",
        "year_built": 1928,
        "provenance_year_built": "OSM_OBSERVED",
    }
    values.update(overrides)
    return pd.Series(values)


def test_observed_apartment_year_maps_to_one_tabula_archetype_but_not_a_layout():
    decision = map_observed_building_to_tabula(
        _row(),
        neighbourhood_id="GB-TEST",
        country_stock_code="GB",
    )

    assert decision.building_type == "AB"
    assert decision.year_built == 1928
    assert decision.archetype_id == "GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001"
    assert decision.mapping_status == "MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT"
    assert decision.reason == "MISSING_OBSERVED_DWELLING_COUNT"
    assert not decision.layout_ready


def test_missing_year_and_ambiguous_house_are_explicit_exclusions():
    decision = map_observed_building_to_tabula(
        _row(building_tag="house", year_built=None, provenance_year_built="OSM_MISSING"),
        neighbourhood_id="GB-TEST",
        country_stock_code="GB",
    )

    assert decision.mapping_status == "EXCLUDED_MISSING_OR_AMBIGUOUS_INPUT"
    assert decision.reason == "MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE"
    assert decision.archetype_id is None


def test_all_live_manifests_are_accounted_for_with_fr_layout_readiness(tmp_path):
    frame, summary = write_eu02_archetype_mapping_readiness(MANIFEST_ROOT, tmp_path)

    assert len(frame) == 4186
    assert summary["total_buildings"] == 4186
    # `D-EU-04-G` (Option G1): France is derived, fail-closed, and now reaches
    # layout readiness; ES/GB/IT are untouched (regression check below).
    assert summary["layout_ready_count"] == 297
    assert frame["building_id"].is_unique
    assert (frame["mapping_status"] == "MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT").sum() == 1
    assert (tmp_path / "observed_archetype_mapping_readiness.csv").is_file()
    assert (tmp_path / "observed_archetype_mapping_readiness_summary.json").is_file()

    fr = frame[frame["neighbourhood_id"] == "FR-LYO-HAUTCOEURPENTES"]
    assert len(fr) == 530
    typed = fr[fr["type_provenance"] == "DERIVED_BDTOPO_TWO_SIGNAL"]
    assert len(typed) == 302
    typed_and_dated = typed[typed["layout_ready"]]
    assert len(typed_and_dated) == 297
    counts = typed_and_dated["building_type"].value_counts().to_dict()
    assert counts == {"AB": 146, "MFH": 123, "TH": 21, "SFH": 7}

    excluded = fr[fr["mapping_status"] == "EXCLUDED_MISSING_OR_AMBIGUOUS_INPUT"]["reason"]
    assert (excluded == TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14).sum() == 37
    assert (excluded == MISSING_OBSERVED_DWELLING_COUNT).sum() == 1
    assert (excluded == MISSING_OBSERVED_STOREY_COUNT).sum() == 1
    assert excluded.str.contains(TYPOLOGY_SIGNALS_DISAGREE).sum() == 189

    assert summary["site_counts"] == {
        "ES-MAD-BERRUGUETE": 1194,
        "FR-LYO-HAUTCOEURPENTES": 530,
        "GB-LDN-STDUNSTANS": 1242,
        "IT-BOL-GALVANI2": 1220,
    }


def _fr_row(**overrides) -> pd.Series:
    values = {
        "osm_id": "way/fr-test",
        "building_tag": "Résidentiel",
        "year_built": 1928,
        "provenance_year_built": "IGN_BDTOPO_OBSERVED",
        "surplus_tags": json.dumps({"nombre_de_logements": "1.0"}),
        "levels": 2,
        "is_attached": True,
    }
    values.update(overrides)
    return pd.Series(values)


def test_observed_dwellings_reads_four_surplus_tags_shapes():
    assert _observed_dwellings(pd.Series({"surplus_tags": '{"nombre_de_logements": "3.0"}'})) == 3
    assert _observed_dwellings(pd.Series({"surplus_tags": "{}"})) is None
    assert (
        _observed_dwellings(pd.Series({"surplus_tags": '{"nombre_de_logements": "abc"}'})) is None
    )
    assert (
        _observed_dwellings(pd.Series({"surplus_tags": '{"nombre_de_logements": "0"}'})) is None
    )


def test_footprint_adjacency_synthetic_fixture():
    gdf = gpd.GeoDataFrame(
        {"osm_id": ["a", "b", "c"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(7, 0, 8, 1)],
        crs="EPSG:2154",
    )

    result = compute_footprint_adjacency(gdf)

    assert result.tolist() == [True, True, False]


def test_derive_bdtopo_building_type_one_case_per_branch_and_exclusion():
    assert derive_bdtopo_building_type(1, 3, True) == ("TH", None)
    assert derive_bdtopo_building_type(1, 3, False) == ("SFH", None)
    assert derive_bdtopo_building_type(6, 4, True) == ("MFH", None)
    assert derive_bdtopo_building_type(20, 6, False) == ("AB", None)
    assert derive_bdtopo_building_type(None, 3, True) == (None, MISSING_OBSERVED_DWELLING_COUNT)
    assert derive_bdtopo_building_type(1, None, True) == (None, MISSING_OBSERVED_STOREY_COUNT)
    assert derive_bdtopo_building_type(13, 3, True) == (
        None,
        TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14,
    )
    assert derive_bdtopo_building_type(14, 3, True) == (
        None,
        TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14,
    )
    assert derive_bdtopo_building_type(6, 5, True) == (None, TYPOLOGY_SIGNALS_DISAGREE)


def test_fr_derivation_wires_behind_observed_tag_and_reaches_layout_ready():
    decision = map_observed_building_to_tabula(
        _fr_row(), neighbourhood_id="FR-TEST", country_stock_code="FR"
    )

    assert decision.building_type == "TH"
    assert decision.type_provenance == "DERIVED_BDTOPO_TWO_SIGNAL"
    assert decision.mapping_status == "MAPPED_LAYOUT_READY"
    assert decision.layout_ready


def test_fr_row_with_observed_tag_is_never_stamped_derived():
    decision = map_observed_building_to_tabula(
        _fr_row(building_tag="apartments"), neighbourhood_id="FR-TEST", country_stock_code="FR"
    )

    assert decision.building_type == "AB"
    assert decision.type_provenance == "OBSERVED_TAG"
