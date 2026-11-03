"""Fail-closed tests for the Madrid Catastro INSPIRE attribute ingestion (`D-EU-23` G1)."""
from __future__ import annotations

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from openubem.acquisition.catastro_inspire_fetcher import (
    NO_CATASTRO_PARTNER,
    PARTNER_WITHOUT_DWELLINGS,
    PARTNER_WITHOUT_YEAR,
    YEAR_PROVENANCE,
    build_es_attribute_sidecar,
    parse_catastro_buildings,
)
from openubem.semantic.european_archetype_mapping import (
    apply_attribute_sidecar,
    map_observed_building_to_tabula,
)


GML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
                       xmlns:gml="http://www.opengis.net/gml/3.2"
                       xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-ext2d/2.0">
  <wfs:member>
    <bu:Building gml:id="ES.SDGC.BU.0001">
      <bu:inspireId><bu:Identifier><bu:localId>0001AAA</bu:localId></bu:Identifier></bu:inspireId>
      <bu:currentUse>1_residential</bu:currentUse>
      <bu:numberOfDwellings>18</bu:numberOfDwellings>
      <bu:numberOfBuildingUnits>20</bu:numberOfBuildingUnits>
      <bu:conditionOfConstruction>functional</bu:conditionOfConstruction>
      <bu:dateOfConstruction><bu:DateOfEvent>
        <bu:beginning>1966-01-01T00:00:00</bu:beginning>
      </bu:DateOfEvent></bu:dateOfConstruction>
      <bu:geometry><gml:Polygon><gml:exterior><gml:LinearRing>
        <gml:posList>40.0 -3.0 40.0 -2.999 40.001 -2.999 40.001 -3.0 40.0 -3.0</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></bu:geometry>
    </bu:Building>
  </wfs:member>
  <wfs:member>
    <bu:Building gml:id="ES.SDGC.BU.0002">
      <bu:inspireId><bu:Identifier><bu:localId>0002AAA</bu:localId></bu:Identifier></bu:inspireId>
      <bu:currentUse>1_residential</bu:currentUse>
      <bu:numberOfDwellings>0</bu:numberOfDwellings>
      <bu:dateOfConstruction><bu:DateOfEvent>
        <bu:beginning>--01-01T00:00:00</bu:beginning>
      </bu:DateOfEvent></bu:dateOfConstruction>
      <bu:geometry><gml:Polygon><gml:exterior><gml:LinearRing>
        <gml:posList>41.0 -3.0 41.0 -2.999 41.001 -2.999 41.001 -3.0 41.0 -3.0</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></bu:geometry>
    </bu:Building>
  </wfs:member>
</wfs:FeatureCollection>
"""


def _catastro_frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(list(parse_catastro_buildings(GML)), geometry="geometry", crs=4326)


def test_parser_reads_both_signals_and_keeps_the_unknown_year_sentinel_unparsed():
    records = list(parse_catastro_buildings(GML))

    assert [record["catastro_local_id"] for record in records] == ["0001AAA", "0002AAA"]
    assert records[0]["year_built"] == 1966
    assert records[0]["n_dwellings"] == 18
    assert records[0]["current_use"] == "1_residential"
    assert records[0]["geometry"].area > 0
    # `--01-01T00:00:00` is the source's own unknown-year encoding, not a year.
    assert records[1]["year_built"] is None
    assert records[1]["raw_beginning"] == "--01-01T00:00:00"


def test_sidecar_credits_the_largest_overlap_partner_and_names_every_absence():
    catastro = _catastro_frame()
    footprints = gpd.GeoDataFrame(
        {"osm_id": ["way/1", "way/2", "way/3"]},
        geometry=[
            Polygon([(-3.0, 40.0), (-2.9995, 40.0), (-2.9995, 40.0005), (-3.0, 40.0005)]),
            Polygon([(-3.0, 41.0), (-2.9995, 41.0), (-2.9995, 41.0005), (-3.0, 41.0005)]),
            Polygon([(-1.0, 42.0), (-0.9995, 42.0), (-0.9995, 42.0005), (-1.0, 42.0005)]),
        ],
        crs=4326,
    )

    sidecar = build_es_attribute_sidecar(footprints, catastro, neighbourhood_id="ES-TEST")

    joined = sidecar.set_index("building_id")
    assert joined.loc["way/1", "year_built"] == 1966
    assert joined.loc["way/1", "n_dwellings"] == 18
    assert joined.loc["way/1", "provenance_year_built"] == YEAR_PROVENANCE
    assert joined.loc["way/1", "reason"] == ""
    # A partner that carries neither signal is recorded as such, never defaulted.
    assert pd.isna(joined.loc["way/2", "year_built"])
    assert joined.loc["way/2", "reason"] == f"{PARTNER_WITHOUT_YEAR};{PARTNER_WITHOUT_DWELLINGS}"
    # A footprint with no partner at all is a different fact and says so.
    assert joined.loc["way/3", "reason"] == NO_CATASTRO_PARTNER
    assert pd.isna(joined.loc["way/3", "catastro_local_id"])


def test_sidecar_refuses_a_manifest_without_osm_id():
    catastro = _catastro_frame()
    footprints = gpd.GeoDataFrame(
        {"other_id": ["a"]},
        geometry=[Polygon([(-3.0, 40.0), (-2.999, 40.0), (-2.999, 40.001), (-3.0, 40.001)])],
        crs=4326,
    )

    with pytest.raises(ValueError, match="osm_id"):
        build_es_attribute_sidecar(footprints, catastro, neighbourhood_id="ES-TEST")


def test_ingested_es_row_reaches_layout_ready_through_the_observed_tag():
    manifest = gpd.GeoDataFrame(
        {
            "osm_id": ["way/1"],
            "building_tag": ["apartments"],
            "year_built": [None],
            "provenance_year_built": ["OSM_MISSING"],
            "levels": [6.0],
            "surplus_tags": ["{}"],
        },
        geometry=[Polygon([(-3.0, 40.0), (-2.999, 40.0), (-2.999, 40.001), (-3.0, 40.001)])],
        crs=4326,
    )
    sidecar = pd.DataFrame(
        [{
            "building_id": "way/1",
            "year_built": 1966,
            "n_dwellings": 18,
            "provenance_year_built": YEAR_PROVENANCE,
            "provenance_dwellings": YEAR_PROVENANCE,
        }]
    )

    merged = apply_attribute_sidecar(manifest, sidecar)
    decision = map_observed_building_to_tabula(
        merged.iloc[0], neighbourhood_id="ES-TEST", country_stock_code="ES"
    )

    assert decision.building_type == "AB"
    assert decision.year_built == 1966
    assert decision.mapping_status == "MAPPED_LAYOUT_READY"
    assert decision.layout_ready
    # The type is observed, the dwelling count is ingested: two different
    # provenances that must stay separately readable.
    assert decision.type_provenance == "OBSERVED_TAG"
    assert decision.dwellings_provenance == YEAR_PROVENANCE


def test_an_ingested_row_without_a_storey_count_is_blocked_not_layout_ready():
    """The layout generator needs storeys as well as dwellings, so readiness does.

    France could never reach this branch -- its two-signal derivation only fires
    when both counts are present -- but Madrid's type comes from the tag, so the
    storey count is an independent signal that can be absent (166 of 1,194 OSM
    footprints carry no ``levels``).
    """
    manifest = gpd.GeoDataFrame(
        {
            "osm_id": ["way/1"],
            "building_tag": ["apartments"],
            "year_built": [None],
            "provenance_year_built": ["OSM_MISSING"],
            "levels": [None],
            "surplus_tags": ["{}"],
        },
        geometry=[Polygon([(-3.0, 40.0), (-2.999, 40.0), (-2.999, 40.001), (-3.0, 40.001)])],
        crs=4326,
    )
    sidecar = pd.DataFrame(
        [{
            "building_id": "way/1",
            "year_built": 1966,
            "n_dwellings": 18,
            "provenance_year_built": YEAR_PROVENANCE,
            "provenance_dwellings": YEAR_PROVENANCE,
        }]
    )

    decision = map_observed_building_to_tabula(
        apply_attribute_sidecar(manifest, sidecar).iloc[0],
        neighbourhood_id="ES-TEST",
        country_stock_code="ES",
    )

    assert decision.mapping_status == "MAPPED_LAYOUT_BLOCKED_MISSING_STOREY_COUNT"
    assert decision.reason == "MISSING_OBSERVED_STOREY_COUNT"
    assert not decision.layout_ready


def test_sidecar_without_a_dwelling_count_stops_short_of_layout_ready():
    manifest = gpd.GeoDataFrame(
        {
            "osm_id": ["way/1"],
            "building_tag": ["apartments"],
            "year_built": [None],
            "provenance_year_built": ["OSM_MISSING"],
            "levels": [6.0],
            "surplus_tags": ["{}"],
        },
        geometry=[Polygon([(-3.0, 40.0), (-2.999, 40.0), (-2.999, 40.001), (-3.0, 40.001)])],
        crs=4326,
    )
    sidecar = pd.DataFrame(
        [{
            "building_id": "way/1",
            "year_built": 1966,
            "n_dwellings": None,
            "provenance_year_built": YEAR_PROVENANCE,
            "provenance_dwellings": "CATASTRO_MISSING",
        }]
    )

    decision = map_observed_building_to_tabula(
        apply_attribute_sidecar(manifest, sidecar).iloc[0],
        neighbourhood_id="ES-TEST",
        country_stock_code="ES",
    )

    assert decision.mapping_status == "MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT"
    assert not decision.layout_ready
    assert decision.dwellings_provenance == "MISSING"
