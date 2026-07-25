"""Bake a Stage-6 classified UTCI raster into an embeddable PNG (T25).

Mirrors `basemap_raster.py`'s exact output contract (PNG + JSON sidecar with
`crs`/`extent_utm`/`attribution`) so `viewer_export.py` can load it with the
same pattern as `_load_basemap` -- fetched/baked ONCE, embedded as a data-URI,
never fetched at view time (offline guarantee, PLAN T25 "How"). Unlike the
basemap there is no network call: the source is already a local GeoTIFF
written by `openubem/microclimate/raster_io.py::write_classified_geotiff`
(uint8 band + embedded 10-class GDAL colour table, T19).

Stage 6 is a separate, unvalidated analysis product (plan §6a) -- the baked
sidecar's `attribution` says so explicitly so the caveat travels with the
artifact into the viewer UI, not just the write-up docs.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

UTCI_LAYER_PNG_NAME = "06_mc_utci_viewer.png"
UTCI_LAYER_SIDECAR_NAME = "06_mc_utci_viewer.json"
_ATTRIBUTION = "OpenUBEM Stage 6 -- outdoor microclimate (UTCI), separate analysis product, not validated against measured data"


def bake_utci_layer(class_tif_path, out_dir: "Path | str", *, field: str = "utci_mean") -> "dict | None":
    """Read a T19 classified UTCI GeoTIFF (uint8 + GDAL colour table) and cache
    `<out_dir>/06_mc_utci_viewer.png` + `.json`. Returns the sidecar dict or
    `None` (missing file / read failure -- additive, never blocks the export,
    same non-fatal contract as `basemap_raster.generate_basemap`)."""
    try:
        return _bake_impl(class_tif_path, out_dir, field=field)
    except Exception:  # noqa: BLE001 - non-fatal by design, mirrors basemap_raster.py
        return None


def _bake_impl(class_tif_path, out_dir, *, field: str) -> "dict | None":
    import rasterio  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    class_tif_path = Path(class_tif_path)
    if not class_tif_path.exists():
        return None

    with rasterio.open(class_tif_path) as src:
        band = src.read(1)
        colormap = src.colormap(1)
        crs = src.crs
        left, bottom, right, top = src.bounds

    if crs is None:
        return None

    lut = np.zeros((256, 4), dtype=np.uint8)
    for idx, rgba in colormap.items():
        if 0 <= idx < 256:
            lut[idx] = rgba
    rgba_img = lut[band]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba_img, mode="RGBA").save(out_dir / UTCI_LAYER_PNG_NAME)

    sidecar = {
        "crs": crs.to_string(),
        "extent_utm": [float(left), float(bottom), float(right), float(top)],
        "attribution": _ATTRIBUTION,
        "field": field,
        "source": class_tif_path.name,
    }
    (out_dir / UTCI_LAYER_SIDECAR_NAME).write_text(
        json.dumps(sidecar, sort_keys=True, indent=2), encoding="utf-8")
    return sidecar
