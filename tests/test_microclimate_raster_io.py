import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point

from openubem import config
from openubem.microclimate.domain import build_domain
from openubem.microclimate.raster_io import (
    apply_utci_palette,
    write_classified_geotiff,
    write_cog,
    write_geotiff,
)
from openubem.microclimate.utci import UTCI_CLASSES, UTCI_NODATA_CLASS


def _dom(res=2.0, buffer_m=20.0, height=10.0):
    gdf = gpd.GeoDataFrame(
        {"osm_id": ["b1"], "height_m": [height]}, geometry=[Point(0, 0).buffer(3.0)], crs="EPSG:32618"
    )
    return build_domain(gdf, res_m=res, buffer_m=buffer_m)


def test_write_geotiff_roundtrip_array_and_profile(tmp_path):
    dom = _dom()
    data = np.random.default_rng(0).uniform(20.0, 40.0, size=dom.shape).astype(np.float32)
    out = write_geotiff(tmp_path / "field.tif", data, dom, mask_buildings=False)
    with rasterio.open(out) as src:
        arr = src.read(1)
        assert src.crs.to_string().endswith("32618") or "32618" in src.crs.to_string()
        assert src.transform == dom.transform
        assert src.nodata == config.UTCI_RASTER_NODATA
    assert np.allclose(arr, data, atol=1e-4)


def test_write_geotiff_masks_building_interior(tmp_path):
    dom = _dom()
    data = np.full(dom.shape, 30.0, dtype=np.float32)
    out = write_geotiff(tmp_path / "field.tif", data, dom)
    with rasterio.open(out) as src:
        arr = src.read(1)
    assert np.all(arr[dom.building_mask] == config.UTCI_RASTER_NODATA)
    assert np.all(arr[~dom.building_mask] == 30.0)


def test_write_geotiff_multiband_band_descriptions(tmp_path):
    dom = _dom()
    stack = np.stack([np.full(dom.shape, i, dtype=np.float32) for i in range(3)])
    out = write_geotiff(tmp_path / "stack.tif", stack, dom, band_descriptions=["t0", "t1", "t2"], mask_buildings=False)
    with rasterio.open(out) as src:
        assert src.count == 3
        assert src.descriptions == ("t0", "t1", "t2")


def test_write_cog_has_cog_layout_tag(tmp_path):
    dom = _dom(res=1.0, buffer_m=60.0)
    data = np.random.default_rng(1).uniform(0.0, 1.0, size=dom.shape).astype(np.float32)
    out = write_cog(tmp_path / "field_cog.tif", data, dom, mask_buildings=False)
    with rasterio.open(out) as src:
        tags = src.tags(ns="IMAGE_STRUCTURE")
        assert tags.get("LAYOUT") == "COG"
        assert src.profile["tiled"] is True


def test_write_classified_geotiff_and_palette(tmp_path):
    dom = _dom()
    utci = np.full(dom.shape, 28.0, dtype=np.float32)  # class 6, "Moderate heat stress"
    out = write_classified_geotiff(tmp_path / "class.tif", utci, dom)
    with rasterio.open(out) as src:
        arr = src.read(1)
        cmap = src.colormap(1)
    assert arr.dtype == np.uint8
    assert np.all(arr[dom.building_mask] == UTCI_NODATA_CLASS)
    assert np.all(arr[~dom.building_mask] == 6)
    assert cmap[UTCI_NODATA_CLASS] == (0, 0, 0, 0)
    for c in UTCI_CLASSES:
        assert cmap[c["index"]][:3] == tuple(int(c["hex"][i : i + 2], 16) for i in (1, 3, 5))


def test_apply_utci_palette_ten_unique_colours(tmp_path):
    dom = _dom()
    utci = np.full(dom.shape, 0.0, dtype=np.float32)
    out = write_classified_geotiff(tmp_path / "class2.tif", utci, dom)
    apply_utci_palette(out)  # idempotent re-application
    with rasterio.open(out) as src:
        cmap = src.colormap(1)
    colours = {cmap[c["index"]] for c in UTCI_CLASSES}
    assert len(colours) == 10
