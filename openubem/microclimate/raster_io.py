"""T19 - GeoTIFF / COG writer + palette embedding (PLAN §7 T19).

F-10: no GeoTIFF writer exists anywhere else in the repo -- this is the first one. Every raster
this package writes shares one convention: float32, DEFLATE, tiled, nodata = -9999.0
(config.UTCI_RASTER_NODATA), CRS/transform taken from the caller's Domain (svf.py etc. never
re-derive their own). Building interiors are always forced to nodata (U06 §2.1 line 72) -- the
one masking rule every writer in this module applies, so a caller cannot forget it.

COG: written via GDAL's own "COG" driver (rasterio.shutil.copy(..., driver="COG")), not a
manual overview-then-repack -- GDAL's COG driver is the primary-source-correct way to get valid
IFD ordering (tested live: the "LAYOUT": "COG" tag on the output confirms it, the assertable
substitute for `rio cogeo validate` since rio-cogeo is not a project dependency, plan §7 T19
"How": "validate ... otherwise assert the tiling/overview structure directly").
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
import rasterio.shutil as rio_shutil
from rasterio.enums import Resampling

from openubem import config
from openubem.microclimate.utci import UTCI_CLASSES, UTCI_NODATA_CLASS, classify_stress


def _hex_to_rgba(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, 255)


def _profile(domain, count: int, dtype: str, nodata: float) -> dict:
    return {
        "driver": "GTiff",
        "height": domain.shape[0],
        "width": domain.shape[1],
        "count": count,
        "dtype": dtype,
        "crs": domain.crs,
        "transform": domain.transform,
        "nodata": nodata,
        "compress": "deflate",
        "tiled": True,
    }


def write_geotiff(
    path,
    data,
    domain,
    *,
    band_descriptions: "list[str] | None" = None,
    nodata: float = config.UTCI_RASTER_NODATA,
    mask_buildings: bool = True,
    building_mask: "np.ndarray | None" = None,
) -> Path:
    """Write a (possibly multi-band) float32 GeoTIFF on domain's own grid.

    data: 2D (rows, cols) or 3D (bands, rows, cols) array. Building-interior pixels -> nodata
    (mask_buildings=True, default; building_mask defaults to domain.building_mask -- U06 §2.1
    line 72: building interiors are not a physically meaningful pedestrian-level quantity).
    """
    arr = np.asarray(data, dtype=np.float32)
    if arr.ndim == 2:
        arr = arr[np.newaxis, ...]
    count = arr.shape[0]
    if arr.shape[1:] != tuple(domain.shape):
        raise ValueError(f"write_geotiff: data shape {arr.shape[1:]} != domain.shape {domain.shape}")

    out = arr.copy()
    if mask_buildings:
        mask = domain.building_mask if building_mask is None else np.asarray(building_mask, dtype=bool)
        out[:, mask] = nodata
    out = np.where(np.isnan(out), nodata, out).astype(np.float32)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = _profile(domain, count, "float32", nodata)
    with rasterio.open(path, "w", **profile) as dst:
        for i in range(count):
            dst.write(out[i], i + 1)
            if band_descriptions is not None:
                dst.set_band_description(i + 1, str(band_descriptions[i]))
    return path


def write_cog(
    path,
    data,
    domain,
    *,
    band_descriptions: "list[str] | None" = None,
    nodata: float = config.UTCI_RASTER_NODATA,
    mask_buildings: bool = True,
    building_mask: "np.ndarray | None" = None,
    overview_resampling: str = "average",
) -> Path:
    """Write a Cloud-Optimized GeoTIFF: same content as write_geotiff, repacked through GDAL's
    COG driver for correct internal-overview/IFD ordering (module docstring)."""
    path = Path(path)
    tmp_path = path.with_suffix(".src.tif")
    write_geotiff(
        tmp_path, data, domain, band_descriptions=band_descriptions, nodata=nodata,
        mask_buildings=mask_buildings, building_mask=building_mask,
    )
    rio_shutil.copy(
        tmp_path, path, driver="COG", compress="DEFLATE", overview_resampling=overview_resampling,
    )
    tmp_path.unlink(missing_ok=True)
    return path


def apply_utci_palette(path, *, nodata_class: int = UTCI_NODATA_CLASS) -> Path:
    """Embed T07's 10-class GDAL colour table onto band 1 of an existing uint8-classified
    GeoTIFF, in place, so the file opens correctly styled in QGIS with no manual step."""
    colormap = {c["index"]: _hex_to_rgba(c["hex"]) for c in UTCI_CLASSES}
    colormap[int(nodata_class)] = (0, 0, 0, 0)
    with rasterio.open(path, "r+") as dst:
        dst.write_colormap(1, colormap)
    return Path(path)


def write_classified_geotiff(
    path,
    utci_c,
    domain,
    *,
    building_mask: "np.ndarray | None" = None,
) -> Path:
    """Classify a continuous UTCI field (T07::classify_stress) and write it as a uint8 GeoTIFF
    with the official palette embedded -- the "companion classified band" plan §7 T19 describes.
    Building interiors and NaN both collapse to UTCI_NODATA_CLASS (255)."""
    classified = classify_stress(utci_c)
    mask = domain.building_mask if building_mask is None else np.asarray(building_mask, dtype=bool)
    classified = np.where(mask, UTCI_NODATA_CLASS, classified).astype(np.uint8)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = _profile(domain, 1, "uint8", UTCI_NODATA_CLASS)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(classified, 1)
    return apply_utci_palette(path, nodata_class=UTCI_NODATA_CLASS)
