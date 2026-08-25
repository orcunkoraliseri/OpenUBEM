"""Manual EU-02 Bologna raw-count reconciliation; never run from pytest."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.acquisition.bologna_fetcher import CTC_DATASET, classify_bologna_ctc, classify_bologna_rifter, fetch_bologna
from openubem.acquisition.boundary_clip import clip_to_boundary


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
BBOX = (44.492249, 44.484404, 11.358017, 11.339551)
BOUNDARY = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_IT-BOL-GALVANI2.geojson"
SHA256 = "7d7dcb8d9553ca2325f71ee5b7ca82ef3180ae4365627ef247007523d956714b"
def main() -> None:
    cadastral = clip_to_boundary(fetch_bologna("rifter_edif_pl", BBOX), BOUNDARY, verify_sha256=SHA256)
    ctc = clip_to_boundary(fetch_bologna(CTC_DATASET, BBOX), BOUNDARY, verify_sha256=SHA256)
    ctc_for_classification = gpd.GeoDataFrame({"building_tag": ctc["descrizion"].fillna("")}, geometry=ctc.geometry, crs=ctc.crs)
    cadastral_for_classification = gpd.GeoDataFrame({"building_tag": cadastral["tipologia"].fillna("")}, geometry=cadastral.geometry, crs=cadastral.crs)
    ctc_residential = ctc.loc[classify_bologna_ctc(ctc_for_classification) == "residential"].copy()
    cadastral_residential = cadastral.loc[classify_bologna_rifter(cadastral_for_classification) == "residential"].copy()
    cadastral_nonresidential = cadastral.loc[classify_bologna_rifter(cadastral_for_classification) == "non_residential"].copy()
    dissolved = ctc_residential.geometry.union_all()
    dissolved_components = len(dissolved.geoms) if dissolved.geom_type == "MultiPolygon" else 1
    joined = gpd.sjoin(
        ctc_residential[["geometry"]], cadastral[["codfab", "geometry"]], how="inner", predicate="intersects"
    )
    joined_cadastral = int(joined["codfab"].nunique())
    rows = [
        {"measure": "CTC residential volumetric bodies", "count": len(ctc_residential)},
        {"measure": "Connected components after dissolve", "count": dissolved_components},
        {"measure": "Cadastral objects touched by CTC residential bodies", "count": joined_cadastral},
        {"measure": "Ruled cadastral building objects", "count": len(cadastral)},
        {"measure": "Cadastral residential candidates", "count": len(cadastral_residential)},
        {"measure": "ISTAT 2011 residential buildings", "count": 1010},
    ]
    pd.DataFrame(rows).to_csv(OUT / "bologna_ctc_cadastral_relation.csv", index=False)
    payload = {
        "site_id": "IT-BOL-GALVANI2",
        "endpoint": "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/{ds}/exports/geojson?limit=-1",
        "licence": "CC BY 4.0, Comune di Bologna",
        "boundary_sha256": SHA256,
        "ctc_volumes_within_boundary": len(ctc),
        "ctc_residential_candidates": len(ctc_residential),
        "ctc_dissolved_connected_components": dissolved_components,
        "ctc_residential_to_cadastral_spatial_join_unique_objects": joined_cadastral,
        "rifter_cadastral_buildings_within_boundary": len(cadastral),
        "rifter_non_residential": len(cadastral_nonresidential),
        "rifter_residential_candidates": len(cadastral_residential),
        "istat_2011_residential_buildings": 1010,
        "expected": {"ctc_volumes_within_boundary": 2427, "ctc_residential_candidates": 2188, "rifter_cadastral_buildings_within_boundary": 1372},
    }
    (OUT / "bologna_live_reconciliation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
