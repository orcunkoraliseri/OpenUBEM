"""Offline tests for Solar DSM/nDSM processing, Places mapping, and fusion."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point, box

from openubem import config
from openubem.acquisition.gmaps_places_fetcher import (
    enrich_buildings_with_gmaps_places,
    fetch_places_nearby,
    parse_places_response,
)
from openubem.acquisition.gmaps_solar_fetcher import (
    derive_ndsm_from_solar_dsm,
    enrich_buildings_with_solar_insights,
    extract_canopy_cdsm_tdsm,
    parse_building_insights,
)
from openubem.semantic import fusion


def _write_raster(
    path: Path,
    arr: np.ndarray,
    *,
    crs: str = "EPSG:32636",
    nodata: float = -9999.0,
) -> Path:
    """Writes a synthetic single-band Float32 GeoTIFF into a test directory.

    Args:
        path: Output GeoTIFF file path.
        arr: 2D numpy pixel array.
        crs: Spatial coordinate reference system string.
        nodata: Nodata sentinel written into file metadata.

    Returns:
        Path to the written GeoTIFF file.
    """
    transform = from_origin(500000.0, 4500100.0, 1.0, 1.0)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(arr.astype(np.float32), 1)
    return path


def _make_synthetic_buildings() -> gpd.GeoDataFrame:
    """Builds 3 metric UTM building footprints overlapping the synthetic grid.

    Returns:
        GeoDataFrame in ``EPSG:32636`` covering pixels inside the 100x100 raster.
    """
    return gpd.GeoDataFrame(
        {
            "osm_id": ["b1", "b2", "b3"],
            "building_tag": ["yes", "commercial", "yes"],
            "use_class": ["unknown", "commercial", pd.NA],
            "function_tag": [pd.NA, "retail", pd.NA],
            "roof_shape": ["flat", "gabled", pd.NA],
            "height_m": [np.nan, np.nan, np.nan],
            "levels": [np.nan, np.nan, np.nan],
            "geometry": [
                box(500010.0, 4500070.0, 500030.0, 4500090.0),
                box(500040.0, 4500070.0, 500060.0, 4500090.0),
                box(500070.0, 4500040.0, 500090.0, 4500060.0),
            ],
        },
        crs="EPSG:32636",
    )


def test_solar_dsm_ndsm_with_dem_and_morphological_fallback(
    tmp_path: Path,
) -> None:
    """Checks exact DEM subtraction vs morphological minimum_filter fallback."""
    dem = np.full((100, 100), 50.0, dtype=np.float32)
    dsm = dem.copy()
    # rows 10..30 correspond to y = 4500090..4500070; cols 10..30 to x = 500010..500030
    dsm[10:30, 10:30] = 65.0  # 15 m building b1
    dsm[10:30, 40:60] = 74.0  # 24 m building b2
    # Tree cluster outside buildings: height 8 m
    dsm[70:80, 15:25] = 58.0

    mask = np.zeros((100, 100), dtype=np.float32)
    mask[10:30, 10:30] = 1.0
    mask[10:30, 40:60] = 1.0

    dsm_path = _write_raster(tmp_path / "dsm.tif", dsm)
    dem_path = _write_raster(tmp_path / "dem.tif", dem)
    mask_path = _write_raster(tmp_path / "mask.tif", mask, nodata=0.0)

    ndsm_exact, derived_exact = derive_ndsm_from_solar_dsm(
        dsm_path,
        tmp_path / "ndsm_exact.tif",
        dem_path=dem_path,
    )
    assert derived_exact is False
    with rasterio.open(ndsm_exact) as src:
        vals = src.read(1)
        assert vals[20, 20] == pytest.approx(15.0, abs=0.1)
        assert vals[20, 50] == pytest.approx(24.0, abs=0.1)

    ndsm_morph, derived_morph = derive_ndsm_from_solar_dsm(
        dsm_path,
        tmp_path / "ndsm_morph.tif",
        dem_path=None,
        ground_window_m=35.0,
    )
    assert derived_morph is True
    with rasterio.open(ndsm_morph) as src:
        mvals = src.read(1)
        assert mvals[20, 20] == pytest.approx(15.0, abs=0.5)
        assert mvals[5, 5] == pytest.approx(0.0, abs=0.5)

    cdsm_path, tdsm_path = extract_canopy_cdsm_tdsm(
        dsm_path,
        mask_path,
        tmp_path / "cdsm.tif",
        dem_path=dem_path,
        crown_depth_fraction=0.6,
    )
    with rasterio.open(cdsm_path) as csrc, rasterio.open(tdsm_path) as tsrc:
        c_arr = csrc.read(1)
        t_arr = tsrc.read(1)
        assert c_arr[20, 20] == pytest.approx(0.0, abs=1e-4)  # building masked out
        assert c_arr[75, 20] == pytest.approx(8.0, abs=1e-4)  # tree preserved
        assert t_arr[75, 20] == pytest.approx(3.2, abs=1e-4)  # 0.4 * 8.0


def test_solar_building_insights_parsing_and_enrichment() -> None:
    """Checks weighted pitch, dominant azimuth, roof_shape gate, and provenance."""
    payload = {
        "solarPotential": {
            "maxArrayPanelsCount": 42,
            "maxSunshineHoursPerYear": 1620.5,
            "wholeRoofStats": {
                "areaMeters2": 220.0,
                "sunshineQuantiles": [800.0, 1200.0, 1600.0],
            },
            "roofSegmentStats": [
                {
                    "pitchDegrees": 22.0,
                    "azimuthDegrees": 180.0,
                    "planeHeightAtCenterMeters": 14.0,
                    "stats": {"areaMeters2": 150.0},
                },
                {
                    "pitchDegrees": 10.0,
                    "azimuthDegrees": 0.0,
                    "planeHeightAtCenterMeters": 12.0,
                    "stats": {"areaMeters2": 50.0},
                },
            ],
        }
    }
    summary = parse_building_insights(payload)
    assert summary.roof_pitch_deg == pytest.approx(19.0)
    assert summary.roof_azimuth_deg == pytest.approx(180.0)
    assert summary.max_panel_count == 42

    bld = _make_synthetic_buildings()
    flat_payload = {
        "solarPotential": {
            "roofSegmentStats": [
                {
                    "pitchDegrees": 2.0,
                    "azimuthDegrees": 90.0,
                    "stats": {"areaMeters2": 100.0},
                }
            ]
        }
    }
    enriched = enrich_buildings_with_solar_insights(
        bld,
        insights_by_id={"b1": payload, "b2": payload, "b3": flat_payload},
        pitch_threshold_deg=5.0,
    )
    assert enriched.loc[0, "roof_shape"] == "pitched"
    assert enriched.loc[1, "roof_shape"] == "gabled"  # existing non-flat preserved
    assert pd.isna(enriched.loc[2, "roof_shape"])  # pitch 2.0 <= 5.0 stays unset
    assert "FUSED_GMAPSSOLAR_HIGH" in str(enriched.loc[0, "data_quality_flag"])


def test_places_parsing_tiebreak_and_fusion_registry(tmp_path: Path) -> None:
    """Checks Places parsing, energy-intensity tie-breaking, and GMaps fusion."""
    assert config.FUSION_SOURCES_BY_TARGET == {}
    assert {"gmaps_solar", "gmaps_places", "gmaps_svi"}.issubset(
        fusion._REGISTRY
    )

    # Zero side effect with default config
    bld = _make_synthetic_buildings()
    baseline_val, baseline_tok = fusion.fuse(bld, "height_m", cfg=config)
    assert baseline_val.isna().all()
    assert baseline_tok.isna().all()

    places_payload = {
        "places": [
            {
                "id": "p_closed",
                "displayName": {"text": "Closed Cafe"},
                "location": {"latitude": 40.65, "longitude": 29.0},
                "primaryType": "cafe",
                "businessStatus": "CLOSED_PERMANENTLY",
            },
            {
                "id": "p_rest",
                "displayName": {"text": "Bistro"},
                "location": {"latitude": 40.6507, "longitude": 29.0002},
                "primaryType": "restaurant",
                "businessStatus": "OPERATIONAL",
            },
        ]
    }
    parsed = parse_places_response(places_payload)
    assert len(parsed) == 1
    assert parsed.iloc[0]["use_class"] == "commercial"
    assert parsed.iloc[0]["function_tag"] == "restaurant"

    # Write spatial POI slice in EPSG:32636 matching synthetic buildings:
    # b1 gets BOTH apartment_building & restaurant inside -> restaurant wins HIGH
    # b3 gets supermarket 5 m outside footprint -> centroid fallback MED
    poi_gdf = gpd.GeoDataFrame(
        [
            {
                "place_id": "poi_apt",
                "primary_type": "apartment_building",
                "business_status": "OPERATIONAL",
                "geometry": Point(500018.0, 4500080.0),
            },
            {
                "place_id": "poi_rest",
                "primary_type": "restaurant",
                "business_status": "OPERATIONAL",
                "geometry": Point(500022.0, 4500080.0),
            },
            {
                "place_id": "poi_mkt",
                "primary_type": "supermarket",
                "business_status": "OPERATIONAL",
                "geometry": Point(500080.0, 4500064.0),  # 4 m north of b3 edge
            },
        ],
        crs="EPSG:32636",
    )
    places_path = tmp_path / "places.parquet"
    poi_gdf.to_parquet(places_path)

    loaded_places = fetch_places_nearby(slice_path=places_path)
    enriched_places = enrich_buildings_with_gmaps_places(bld, loaded_places)
    assert enriched_places.loc[0, "use_class"] == "commercial"
    assert enriched_places.loc[1, "use_class"] == "commercial"
    assert enriched_places.loc[1, "function_tag"] == "retail"  # preserved
    assert enriched_places.loc[2, "use_class"] == "commercial"
    assert "FUSED_GMAPSPLACES_HIGH" in str(
        enriched_places.loc[0, "data_quality_flag"]
    )
    assert "FUSED_GMAPSPLACES_MED" in str(
        enriched_places.loc[2, "data_quality_flag"]
    )

    # Fusion registry test with Solar DSM + DEM, Places, and Street View Insights
    dem = np.full((100, 100), 10.0, dtype=np.float32)
    dsm = dem.copy()
    dsm[10:30, 10:30] = 28.0  # b1 = 18 m
    dsm_path = _write_raster(tmp_path / "fusion_dsm.tif", dsm)
    dem_path = _write_raster(tmp_path / "fusion_dem.tif", dem)

    svi_gdf = gpd.GeoDataFrame(
        [{"levels_observed": 5.0, "geometry": box(500039, 4500069, 500061, 4500091)}],
        crs="EPSG:32636",
    )
    svi_path = tmp_path / "svi.geojson"
    svi_gdf.to_file(svi_path, driver="GeoJSON")

    custom_cfg = SimpleNamespace(
        FUSION_SOURCES_BY_TARGET={
            "height_m": ("gmaps_solar",),
            "use_class": ("gmaps_places",),
            "levels": ("gmaps_svi",),
        },
        FUSION_GMAPS_SOLAR_NDSM_PATH=None,
        FUSION_GMAPS_SOLAR_DSM_PATH=dsm_path,
        FUSION_GMAPS_SOLAR_DEM_PATH=dem_path,
        GMAPS_CACHE_DIR=tmp_path / "gmaps_cache",
        FUSION_GMAPS_PLACES_PATH=places_path,
        FUSION_GMAPS_SVI_PATH=svi_path,
        FUSION_GMAPS_SVI_FIELDS={},
    )

    h_val, h_tok = fusion.fuse(bld, "height_m", cfg=custom_cfg)
    assert h_val.loc[0] == pytest.approx(18.0, abs=0.1)
    assert h_tok.loc[0] == "FUSED_GMAPSSOLAR_HIGH"

    uc_val, uc_tok = fusion.fuse(bld, "use_class", cfg=custom_cfg)
    assert uc_val.loc[0] == "commercial"
    assert uc_tok.loc[0] == "FUSED_GMAPSPLACES_HIGH"
    assert uc_tok.loc[2] == "FUSED_GMAPSPLACES_MED"

    lvl_val, lvl_tok = fusion.fuse(bld, "levels", cfg=custom_cfg)
    assert lvl_val.loc[1] == pytest.approx(5.0)
    assert lvl_tok.loc[1] == "FUSED_GMAPSSVI_MED"
