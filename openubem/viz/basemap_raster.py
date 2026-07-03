"""Per-run georeferenced basemap: fetch once, reproject to UTM, cache (T16).

Feature F1 source side (PLAN Phase E). Same Carto/OSM basemap as the 2D
`scripts/validation/phaseE_overview_grid.py::_add_basemap` (CartoDB via
`contextily`), but cached to a per-run raster so the offline single-file HTML
never re-fetches at view time (PLAN §2 hard rule: live/streaming tiles in the
shipped HTML are PROHIBITED — the network touch happens ONLY here, at
generation time; the shipped file embeds the cached bytes, never fetches).

Must reproject Web-Mercator (EPSG:3857) -> the run's UTM CRS with
`rasterio.warp` (not a bare relabel): a relabel leaves ~17 m corner error from
meridian convergence over a ~1.5 km neighbourhood (PLAN T16 §How) — unfaithful.

Fetch failure / no network -> `generate_basemap` returns `None`, non-fatal: the
basemap is optional (T1 §0 deferred-then-added feature), the exporter must
still produce a viewer without one.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

_ATTRIBUTION = "© OpenStreetMap contributors © CARTO"
BASEMAP_PNG_NAME = "06_basemap_utm.png"
BASEMAP_SIDECAR_NAME = "06_basemap_utm.json"


def _default_provider():
    import contextily as ctx  # noqa: PLC0415

    return ctx.providers.CartoDB.PositronNoLabels


def _fetch_tile_image(w: float, s: float, e: float, n: float, *, zoom, provider):
    """The ONE network boundary — tests monkeypatch this, never the real fetch.

    `w, s, e, n` are lon/lat (WGS84) bounds. Returns `(img, ext)`: `img` an
    `(H, W, bands)` uint8 ndarray in EPSG:3857, `ext` the Mercator extent
    `(minx, maxx, miny, maxy)` (contextily's own `bounds2img` contract).
    """
    import contextily as ctx  # noqa: PLC0415

    return ctx.bounds2img(w, s, e, n, zoom=zoom, source=provider, ll=True)


def _resolve_zoom(w: float, s: float, e: float, n: float, *, zoom, provider, target_px: int) -> int:
    """Resolve `zoom="auto"` to an int high enough that the native fetched
    raster is NOT upsampled to `target_px` (debug fix D04, decision §6.4:
    `zoom="auto"` alone under-selects tile zoom, e.g. austin_centre fetches
    768x768 then bilinearly upsamples to 2048 -> blur).

    Pure local tile-count math (`mercantile`, no network) mirrors what
    `contextily.bounds2img` will actually fetch at a given zoom, so the right
    zoom can be picked BEFORE spending the one real network call. Explicit int
    `zoom` is honoured verbatim (F-B1) — this only resolves `"auto"`.
    """
    if zoom != "auto":
        return zoom

    import contextily as ctx  # noqa: PLC0415
    import mercantile  # noqa: PLC0415

    base_zoom = ctx.tile._calculate_zoom(w, s, e, n)  # noqa: SLF001
    max_zoom = provider.get("max_zoom") if hasattr(provider, "get") else None

    resolved = base_zoom
    tile_size = 256  # standard XYZ tile edge (no retina `{r}` requested)
    for bump in range(0, 4):  # auto, auto+1, auto+2, auto+3 (cap per §6.4)
        z = base_zoom + bump
        if max_zoom is not None and z > max_zoom:
            resolved = max(base_zoom, max_zoom)
            break
        tiles = list(mercantile.tiles(w, s, e, n, [z]))
        est_w = len({t.x for t in tiles}) * tile_size
        est_h = len({t.y for t in tiles}) * tile_size
        resolved = z
        if max(est_w, est_h) >= target_px:
            break
    return resolved


def generate_basemap(
    buildings_gdf,
    out_dir: Path | str,
    *,
    provider=None,
    padding_frac: float = 0.05,
    target_px: int = 3072,
    zoom: int | str = "auto",
) -> dict | None:
    """Fetch + reproject + cache a per-run basemap; return the sidecar dict or `None`.

    `buildings_gdf` must carry a projected UTM CRS (the run's `01_buildings.gpkg`
    CRS). Writes `<out_dir>/06_basemap_utm.png` + `<out_dir>/06_basemap_utm.json`
    (`{"crs","extent_utm":[minx,miny,maxx,maxy],"attribution","provider",
    "fetched_px","zoom"}`, no `Date`/random — the cache IS the reproducibility
    anchor). Any failure (no network, bad CRS, ...) is swallowed and returns
    `None` — the basemap is additive, never blocks the export.
    """
    try:
        return _generate_basemap_impl(
            buildings_gdf, out_dir, provider=provider,
            padding_frac=padding_frac, target_px=target_px, zoom=zoom)
    except Exception:  # noqa: BLE001 - non-fatal by design (PLAN T16 §What)
        return None


def _generate_basemap_impl(buildings_gdf, out_dir, *, provider, padding_frac,
                            target_px, zoom) -> dict:
    from PIL import Image  # noqa: PLC0415
    from rasterio.transform import array_bounds  # noqa: PLC0415
    from rasterio.transform import from_bounds as rio_from_bounds  # noqa: PLC0415
    from rasterio.warp import (  # noqa: PLC0415
        Resampling, calculate_default_transform, reproject, transform_bounds,
    )

    if provider is None:
        provider = _default_provider()

    utm_crs = buildings_gdf.crs
    if utm_crs is None:
        raise ValueError("buildings_gdf has no CRS; cannot geo-reference a basemap")
    utm_crs_str = utm_crs.to_string()

    minx, miny, maxx, maxy = (float(v) for v in buildings_gdf.total_bounds)
    px = (maxx - minx) * padding_frac
    py = (maxy - miny) * padding_frac
    minx, miny, maxx, maxy = minx - px, miny - py, maxx + px, maxy + py

    # Padded UTM bbox -> WGS84 lon/lat for the tile fetch (contextily `ll=True`).
    west, south, east, north = transform_bounds(
        utm_crs_str, "EPSG:4326", minx, miny, maxx, maxy)

    resolved_zoom = _resolve_zoom(west, south, east, north, zoom=zoom,
                                   provider=provider, target_px=target_px)
    img, merc_ext = _fetch_tile_image(west, south, east, north, zoom=resolved_zoom,
                                       provider=provider)
    img = np.asarray(img)
    if img.ndim == 2:
        img = img[:, :, None]
    src_minx, src_maxx, src_miny, src_maxy = (float(v) for v in merc_ext)
    src_h, src_w = img.shape[0], img.shape[1]
    src_transform = rio_from_bounds(
        src_minx, src_miny, src_maxx, src_maxy, src_w, src_h)

    # Pass 1: natural-resolution UTM footprint of the Mercator source, to learn
    # the destination aspect ratio.
    nat_transform, nat_w, nat_h = calculate_default_transform(
        "EPSG:3857", utm_crs_str, src_w, src_h,
        src_minx, src_miny, src_maxx, src_maxy)
    scale = target_px / max(nat_w, nat_h)
    dst_w = max(1, int(round(nat_w * scale)))
    dst_h = max(1, int(round(nat_h * scale)))

    # Pass 2: same bounds, resampled onto the target_px-sized grid.
    dst_transform, dst_w, dst_h = calculate_default_transform(
        "EPSG:3857", utm_crs_str, src_w, src_h,
        src_minx, src_miny, src_maxx, src_maxy,
        dst_width=dst_w, dst_height=dst_h)

    n_bands = img.shape[2]
    dst = np.zeros((n_bands, dst_h, dst_w), dtype=np.uint8)
    for b in range(n_bands):
        reproject(
            source=img[:, :, b],
            destination=dst[b],
            src_transform=src_transform, src_crs="EPSG:3857",
            dst_transform=dst_transform, dst_crs=utm_crs_str,
            resampling=Resampling.bilinear,
        )

    left, bottom, right, top = array_bounds(dst_h, dst_w, dst_transform)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    arr = np.moveaxis(dst, 0, -1)  # (H, W, bands)
    mode = {1: "L", 3: "RGB", 4: "RGBA"}.get(n_bands, "RGBA")
    Image.fromarray(arr, mode=mode).save(out_dir / BASEMAP_PNG_NAME)

    sidecar = {
        "crs": utm_crs_str,
        "extent_utm": [float(left), float(bottom), float(right), float(top)],
        "attribution": _ATTRIBUTION,
        "provider": getattr(provider, "name", str(provider)),
        "fetched_px": [int(src_w), int(src_h)],
        "zoom": resolved_zoom,
    }
    (out_dir / BASEMAP_SIDECAR_NAME).write_text(
        json.dumps(sidecar, sort_keys=True, indent=2), encoding="utf-8")
    return sidecar
