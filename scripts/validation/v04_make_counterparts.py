"""V04: Generate OpenUBEM counterpart IDFs for each mappable reference building.

For each reference with a mappable OpenUBEM archetype:
  - Build a one-row synthetic GDF (rectangular footprint = conditioned_area / storeys)
  - Force archetype_id to the mapped label; assign Buffalo lat/lon; CZ 6A
  - Run Step 2 enrichment + Step 3 IDF generation → counterparts/idfs/<stem>.idf

Outputs:
  %TEMP%/ubem_validation/level2/mapping.csv      (all 31 files with explicit decision)
  %TEMP%/ubem_validation/level2/counterparts/03_idf_manifest.parquet
  %TEMP%/ubem_validation/level2/counterparts/idfs/*.idf
"""
from __future__ import annotations

import math
import sys
import tempfile
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
INVENTORY_CSV = OUT_BASE / "ref_inventory.csv"
COUNTERPARTS_DIR = OUT_BASE / "counterparts"
MAPPING_CSV = OUT_BASE / "mapping.csv"

EPW_PATH_FILE = OUT_BASE / "epw_path.txt"
BUFFALO_LAT = 42.94
BUFFALO_LON = -78.73
BUFFALO_CZ = "6A"

ARCHETYPE_MAP: dict[str, str] = {
    "OfficeMedium": "MediumOffice",
    "OfficeLarge": "LargeOffice",
    "OfficeSmall": "SmallOffice",
    "ApartmentHighRise": "HighriseApartment",
    "ApartmentMidRise": "MidriseApartment",
    "TallBuilding": "TallBuilding",
    "SuperTallBuilding": "SuperTallBuilding",
    "College": "College",
    "OutPatientHealthCare": "Outpatient",
    "Hospital": "Hospital",
    "RestaurantFastFood": "QuickServiceRestaurant",
    "RestaurantSitDown": "FullServiceRestaurant",
    "RetailStandalone": "RetailStandalone",
    "RetailStripmall": "RetailStripmall",
    "Warehouse": "Warehouse",
    "HotelSmall": "SmallHotel",
    "HotelLarge": "LargeHotel",
    "SchoolPrimary": "PrimarySchool",
    "SchoolSecondary": "SecondarySchool",
    "Supermarket": "SuperMarket",
    "Laboratory": "Laboratory",
    "SmallDataCenterHighITE": "SmallDataCenterHighITE",
    "SmallDataCenterLowITE": "SmallDataCenterLowITE",
    "DataCenterLargeHighITE": "LargeDataCenterHighITE",
    "DataCenterLargeLowITE": "LargeDataCenterLowITE",
}

NOT_MAPPED_BUILDING_TYPES = {
    "AttachedHouse+CZ6A+IECC+2024",
    "DetachedHouse+CZ6A+IECC+2024",
    "MT5_HPE_NV_ECW_LED Small_Retail",
    "HighRise_ST15",
    "HighRise_ST20",
}

NOT_MAPPED_50PCT_STEMS = {
    "ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled",
    "ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled",
    "ASHRAE901_Warehouse_STD2022_Buffalo_50pct_downscaled",
}


def _make_rect_polygon(area_m2: float, crs_utm: str = "EPSG:32617") -> Polygon:
    side = math.sqrt(area_m2)
    return Polygon([(0, 0), (side, 0), (side, side), (0, side)])


def _build_synthetic_row(
    stem: str,
    archetype_id: str,
    floor_area_m2: float,
    storeys: int,
    epw_path: str,
    osm_id: int,
) -> dict:
    storeys = max(1, storeys)
    footprint_area = floor_area_m2 / storeys
    side = math.sqrt(footprint_area)
    perimeter = 4 * side
    height_m = storeys * 3.5

    geom = _make_rect_polygon(footprint_area)

    return {
        "geometry": geom,
        "osm_id": osm_id,
        "crs_utm": "EPSG:32617",
        "building_tag": "yes",
        "function_tag": pd.NA,
        "levels": pd.array([storeys], dtype="Int64")[0],
        "height_m": float(height_m),
        "year_built": pd.array([2019], dtype="Int64")[0],
        "postcode": pd.NA,
        "underground": pd.array([0], dtype="Int64")[0],
        "roof_shape": "flat",
        "roof_height_m": float(height_m),
        "footprint_area_m2": float(footprint_area),
        "perimeter_m": float(perimeter),
        "surplus_tags": "{}",
        "provenance_levels": "SYNTHETIC",
        "provenance_height_m": "SYNTHETIC",
        "provenance_year_built": "SYNTHETIC",
        "provenance_building_tag": "SYNTHETIC",
        "provenance_function_tag": "SYNTHETIC",
        "provenance_postcode": "SYNTHETIC",
        "provenance_geometry": "SYNTHETIC",
        "data_quality_flag": "",
        "archetype_id": archetype_id,
        "archetype_confidence": 1.0,
        "archetype_source": "VALIDATION_FORCED",
        "climate_zone": BUFFALO_CZ,
        "epw_path": epw_path,
        "provenance_climate_zone": "ASHRAE_STANDARD",
    }


def main() -> None:
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    inv = pd.read_csv(INVENTORY_CSV)
    epw_path = EPW_PATH_FILE.read_text().strip()

    mapping_rows = []
    build_rows = []
    osm_counter = 90001

    for _, inv_row in inv.iterrows():
        fname = inv_row["filename"]
        stem = fname.replace(".idf", "")
        btype = str(inv_row["building_type"])
        floor_area = float(inv_row["conditioned_floor_area_m2"])
        storeys = int(inv_row["storeys"])

        if stem in NOT_MAPPED_50PCT_STEMS:
            mapping_rows.append({"filename": fname, "building_type": btype,
                                  "openuben_archetype": "NOT_MAPPED",
                                  "reason": "50pct_downscaled_duplicate"})
            continue

        if btype in NOT_MAPPED_BUILDING_TYPES:
            mapping_rows.append({"filename": fname, "building_type": btype,
                                  "openuben_archetype": "NOT_MAPPED",
                                  "reason": "outside_30type_taxonomy"})
            continue

        if btype not in ARCHETYPE_MAP:
            mapping_rows.append({"filename": fname, "building_type": btype,
                                  "openuben_archetype": "NOT_MAPPED",
                                  "reason": "no_taxonomy_match"})
            continue

        archetype_id = ARCHETYPE_MAP[btype]
        mapping_rows.append({"filename": fname, "building_type": btype,
                              "openuben_archetype": archetype_id,
                              "reason": "mapped"})
        syn_row = _build_synthetic_row(stem, archetype_id, floor_area, storeys, epw_path, osm_counter)
        syn_row["_ref_stem"] = stem
        build_rows.append(syn_row)
        osm_counter += 1

    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_csv(MAPPING_CSV, index=False)
    n_mapped = (mapping_df["openuben_archetype"] != "NOT_MAPPED").sum()
    print(f"[V04] Mapping complete: {n_mapped}/{len(mapping_df)} mapped -> {MAPPING_CSV}")
    not_mapped = mapping_df[mapping_df["openuben_archetype"] == "NOT_MAPPED"]
    if len(not_mapped):
        print("[V04] NOT_MAPPED:")
        for _, r in not_mapped.iterrows():
            print(f"  {r['filename']}  reason={r['reason']}")

    if not build_rows:
        print("[V04] ERROR: no mappable buildings")
        sys.exit(1)

    ref_stems = [r.pop("_ref_stem") for r in build_rows]

    schema_cols_base = [
        "geometry", "osm_id", "crs_utm",
        "building_tag", "function_tag", "levels", "height_m", "year_built",
        "postcode", "underground", "roof_shape", "roof_height_m",
        "footprint_area_m2", "perimeter_m", "surplus_tags",
        "provenance_levels", "provenance_height_m", "provenance_year_built",
        "provenance_building_tag", "provenance_function_tag", "provenance_postcode",
        "provenance_geometry", "data_quality_flag",
        "archetype_id", "archetype_confidence", "archetype_source",
        "climate_zone", "epw_path", "provenance_climate_zone",
    ]

    gdf_raw = gpd.GeoDataFrame(build_rows, crs="EPSG:32617")[schema_cols_base]
    gdf_raw["levels"] = gdf_raw["levels"].astype("Int64")
    gdf_raw["year_built"] = gdf_raw["year_built"].astype("Int64")
    gdf_raw["underground"] = gdf_raw["underground"].astype("Int64")
    gdf_raw["climate_zone"] = pd.Categorical(gdf_raw["climate_zone"], categories=_CLIMATE_ZONE_VOCAB)
    gdf_raw["provenance_climate_zone"] = pd.Categorical(
        gdf_raw["provenance_climate_zone"], categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )

    print(f"[V04] Enriching {len(gdf_raw)} buildings via enrich_semantics...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf_enriched, schedule_lib = enrich_semantics(gdf_raw, random_seed=42)
    print(f"[V04] Enrichment done: {gdf_enriched.shape}")

    COUNTERPARTS_DIR.mkdir(parents=True, exist_ok=True)
    from openubem.idf.builder import run_step3
    print(f"[V04] Running Step 3 IDF generation -> {COUNTERPARTS_DIR}")
    manifest = run_step3(gdf_enriched, schedule_lib, COUNTERPARTS_DIR)
    success = (manifest["generation_status"] == "success").sum()
    print(f"[V04] {success}/{len(manifest)} IDFs generated")

    fail_mask = manifest["generation_status"] != "success"
    if fail_mask.any():
        print("[V04] FAILURES:")
        print(manifest[fail_mask][["osm_id", "archetype_id", "generation_status"]].to_string())

    osm_to_stem = {
        row["osm_id"]: stem
        for row, stem in zip(build_rows, ref_stems)
    }
    idf_dir = COUNTERPARTS_DIR / "idfs"
    for osm_id, stem in zip(gdf_enriched["osm_id"], ref_stems):
        src = idf_dir / f"{osm_id}.idf"
        dst = idf_dir / f"{stem}_counterpart.idf"
        if src.exists() and not dst.exists():
            src.rename(dst)

    manifest["ref_stem"] = ref_stems
    manifest["ref_filename"] = [s + ".idf" for s in ref_stems]
    manifest.to_parquet(COUNTERPARTS_DIR / "03_idf_manifest.parquet", index=False)
    print(f"[V04] Manifest written: {COUNTERPARTS_DIR / '03_idf_manifest.parquet'}")
    print("[V04] DONE")


if __name__ == "__main__":
    main()
