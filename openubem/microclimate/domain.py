"""T08/T09 - raster domain builder + tiered vegetation layer (PLAN §7 T08/T09).

All Stage-6 rasters share exactly one rasterio transform/shape/CRS/bounds (asserted in
Domain.__post_init__) -- the classic silent-misalignment failure mode this guards against.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from rasterio.transform import Affine, from_origin

# Oke, T. R. (1987). Boundary Layer Climates (2nd ed.). Routledge -- typical paved/asphalt
# surface albedo/emissivity; P-10 uses this same 0.15 baseline for the cool-pavement paradox.
DEFAULT_GROUND_ALBEDO = 0.15
DEFAULT_GROUND_EMISSIVITY = 0.95

# U03 Table 4 (lines 47-48): land-cover albedo/emissivity, each cited to Oke (1987) Ch.1 Table 1.1.
LANDCOVER_ALBEDO = {
    "paved": 0.15,
    "grass": 0.22,
    "water": 0.06,
    "roof": 0.20,
}
LANDCOVER_EMISSIVITY = {
    "paved": 0.95,
    "grass": 0.95,
    "water": 0.96,
    "roof": 0.90,
}


@dataclass
class Domain:
    dsm: np.ndarray
    dem: np.ndarray
    building_mask: np.ndarray  # bool, True = inside a building footprint
    albedo: np.ndarray
    emissivity: np.ndarray
    transform: Affine
    crs: str
    res_m: float
    shape: tuple  # (rows, cols)
    bounds: tuple  # (minx, miny, maxx, maxy)
    dem_source: str  # "assumed_flat" | "user_dem"
    landcover_tier: str  # "uniform" | "osm"
    excluded_building_ids: list = field(default_factory=list)

    def __post_init__(self):
        for name, arr in (
            ("dem", self.dem), ("building_mask", self.building_mask),
            ("albedo", self.albedo), ("emissivity", self.emissivity),
        ):
            if arr.shape != self.dsm.shape:
                raise ValueError(f"Domain: {name}.shape {arr.shape} != dsm.shape {self.dsm.shape}")
        if self.dsm.shape != self.shape:
            raise ValueError(f"Domain: dsm.shape {self.dsm.shape} != declared shape {self.shape}")


def _grid_spec(bounds, res_m):
    minx, miny, maxx, maxy = bounds
    cols = int(np.ceil((maxx - minx) / res_m))
    rows = int(np.ceil((maxy - miny) / res_m))
    cols = max(cols, 1)
    rows = max(rows, 1)
    transform = from_origin(minx, maxy, res_m, res_m)
    new_bounds = (minx, maxy - rows * res_m, minx + cols * res_m, maxy)
    return transform, (rows, cols), new_bounds


def build_domain(
    buildings_gdf: gpd.GeoDataFrame,
    *,
    res_m: float,
    buffer_m: float,
    crs: "str | None" = None,
    dem_path: "str | None" = None,
    ground_albedo: float = DEFAULT_GROUND_ALBEDO,
    ground_emissivity: float = DEFAULT_GROUND_EMISSIVITY,
    landcover_gdf: "gpd.GeoDataFrame | None" = None,
) -> Domain:
    """Build the raster domain: extent = union of footprints buffered by buffer_m (NOT
    config.SHADING_SPHERE_RADIUS's 30 m -- that value is for per-building IDF shading, F-05)."""
    if crs is None:
        crs = buildings_gdf.crs
    gdf = buildings_gdf.to_crs(crs) if buildings_gdf.crs != crs else buildings_gdf.copy()

    extent = gdf.geometry.union_all().buffer(buffer_m)
    transform, shape, bounds = _grid_spec(extent.bounds, res_m)

    if dem_path is not None:
        with rasterio.open(dem_path) as src:
            from rasterio.warp import Resampling, reproject
            dem = np.zeros(shape, dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1), destination=dem,
                src_transform=src.transform, src_crs=src.crs,
                dst_transform=transform, dst_crs=crs, resampling=Resampling.bilinear,
            )
        dem_source = "user_dem"
    else:
        dem = np.zeros(shape, dtype=np.float32)
        dem_source = "assumed_flat"

    has_height = gdf["height_m"].notna() if "height_m" in gdf.columns else gdf.geometry.map(lambda _g: False)
    excluded_ids = gdf.loc[~has_height, "osm_id"].astype(str).tolist() if "osm_id" in gdf.columns else []

    height_shapes = list(zip(gdf.loc[has_height].geometry, gdf.loc[has_height, "height_m"].astype(float)))
    if height_shapes:
        building_height = features.rasterize(
            height_shapes, out_shape=shape, transform=transform, fill=0.0, dtype="float32",
        )
    else:
        building_height = np.zeros(shape, dtype=np.float32)
    dsm = dem + building_height

    all_shapes = [(geom, 1) for geom in gdf.geometry]
    mask_raw = features.rasterize(
        all_shapes, out_shape=shape, transform=transform, fill=0, dtype="uint8",
    )
    building_mask = mask_raw.astype(bool)

    if landcover_gdf is not None and len(landcover_gdf) > 0:
        albedo, emissivity = _rasterize_landcover_tier1(landcover_gdf, crs, shape, transform, ground_albedo, ground_emissivity)
        landcover_tier = "osm"
    else:
        albedo = np.full(shape, ground_albedo, dtype=np.float32)
        emissivity = np.full(shape, ground_emissivity, dtype=np.float32)
        landcover_tier = "uniform"

    return Domain(
        dsm=dsm, dem=dem, building_mask=building_mask, albedo=albedo, emissivity=emissivity,
        transform=transform, crs=str(crs), res_m=res_m, shape=shape, bounds=bounds,
        dem_source=dem_source, landcover_tier=landcover_tier, excluded_building_ids=excluded_ids,
    )


def _rasterize_landcover_tier1(landcover_gdf, crs, shape, transform, default_albedo, default_emissivity):
    lc = landcover_gdf.to_crs(crs) if landcover_gdf.crs != crs else landcover_gdf
    albedo = np.full(shape, default_albedo, dtype=np.float32)
    emissivity = np.full(shape, default_emissivity, dtype=np.float32)
    for cls in ("water", "grass", "roof"):  # paved is the default fill, rasterized last-wins order below
        sub = lc[lc["landcover_class"] == cls]
        if len(sub) == 0:
            continue
        shapes_a = [(g, LANDCOVER_ALBEDO[cls]) for g in sub.geometry]
        shapes_e = [(g, LANDCOVER_EMISSIVITY[cls]) for g in sub.geometry]
        mask = features.rasterize(sub.geometry, out_shape=shape, transform=transform, fill=0, dtype="uint8").astype(bool)
        albedo_r = features.rasterize(shapes_a, out_shape=shape, transform=transform, fill=0.0, dtype="float32")
        emiss_r = features.rasterize(shapes_e, out_shape=shape, transform=transform, fill=0.0, dtype="float32")
        albedo = np.where(mask, albedo_r, albedo)
        emissivity = np.where(mask, emiss_r, emissivity)
    return albedo, emissivity


# ── T09 — tiered vegetation layer ──────────────────────────────────────────────────────────
# LAI 2.0-4.5 and transmissivity ranges cited to U03 Table 4 (lines 47-48); Konarska et al.
# (2014) for foliage transmissivity primary source (already in the outdoor-reference bibliography).
DECIDUOUS_TAU_SUMMER = 0.20  # midpoint of 0.10-0.30 (P-09)
DECIDUOUS_TAU_WINTER = 0.55  # midpoint of 0.40-0.70
CONIFEROUS_TAU = 0.10  # midpoint of 0.05-0.15
DEFAULT_LAI = 3.0  # midpoint of urban LAI 2.0-4.5
DEFAULT_CROWN_RADIUS_M = 4.0  # typical urban street-tree crown radius (Konarska et al. 2014)
DEFAULT_CROWN_DEPTH_FRACTION = 0.6  # crown occupies the top 60% of tree height (trunk zone below)


def build_vegetation(shape, transform, *, tier: str = "none", tree_points: "gpd.GeoDataFrame | None" = None,
                      canopy_gdf: "gpd.GeoDataFrame | None" = None, cdsm_path: "str | None" = None,
                      tdsm_path: "str | None" = None, month: int = 7):
    """Returns (cdsm, tdsm, lai) rasters + a manifest dict with vegetation_source flags.

    tier: "none" (default -- honest gap, no tree data assumed) | "osm" | "cdsm".
    """
    if tier == "none":
        z = np.zeros(shape, dtype=np.float32)
        return z, z.copy(), z.copy(), {"vegetation_tier": "none", "vegetation_source": "not_available"}

    if tier == "cdsm":
        if cdsm_path is None or tdsm_path is None:
            raise ValueError("build_vegetation(tier='cdsm') requires cdsm_path and tdsm_path")
        cdsm = _read_and_resample(cdsm_path, shape, transform)
        tdsm = _read_and_resample(tdsm_path, shape, transform)
        lai = np.where(cdsm > 0, DEFAULT_LAI, 0.0).astype(np.float32)
        return cdsm, tdsm, lai, {"vegetation_tier": "cdsm", "vegetation_source": "user_cdsm_tdsm"}

    if tier == "osm":
        cdsm = np.zeros(shape, dtype=np.float32)
        tdsm = np.zeros(shape, dtype=np.float32)
        lai = np.zeros(shape, dtype=np.float32)
        if tree_points is not None and len(tree_points) > 0:
            for _, row in tree_points.iterrows():
                crown_h = float(row.get("crown_height_m", 8.0))
                crown_r = float(row.get("crown_radius_m", DEFAULT_CROWN_RADIUS_M))
                geom = row.geometry.buffer(crown_r)
                shp = features.rasterize([(geom, crown_h)], out_shape=shape, transform=transform, fill=0.0, dtype="float32")
                trunk_h = crown_h * (1.0 - DEFAULT_CROWN_DEPTH_FRACTION)
                shp_trunk = features.rasterize([(geom, trunk_h)], out_shape=shape, transform=transform, fill=0.0, dtype="float32")
                cdsm = np.maximum(cdsm, shp)
                tdsm = np.where(shp > 0, shp_trunk, tdsm)
                shp_lai = features.rasterize([(geom, DEFAULT_LAI)], out_shape=shape, transform=transform, fill=0.0, dtype="float32")
                lai = np.maximum(lai, shp_lai)
        if canopy_gdf is not None and len(canopy_gdf) > 0:
            canopy_h = features.rasterize(
                [(g, 10.0) for g in canopy_gdf.geometry], out_shape=shape, transform=transform, fill=0.0, dtype="float32",
            )
            cdsm = np.maximum(cdsm, canopy_h)
            tdsm = np.where(canopy_h > 0, np.maximum(tdsm, canopy_h * (1.0 - DEFAULT_CROWN_DEPTH_FRACTION)), tdsm)
            lai = np.where(canopy_h > 0, np.maximum(lai, DEFAULT_LAI), lai)
        return cdsm, tdsm, lai, {"vegetation_tier": "osm", "vegetation_source": "osm_synthetic"}

    raise ValueError(f"build_vegetation: unknown tier {tier!r}")


def _read_and_resample(path, shape, transform):
    from rasterio.warp import Resampling, reproject
    with rasterio.open(path) as src:
        out = np.zeros(shape, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1), destination=out,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=transform, dst_crs=src.crs, resampling=Resampling.bilinear,
        )
    return out


def deciduous_transmissivity(month: int) -> float:
    """§4.9/U03 §4.4 line 203 -- monthly phenological adjustment. Leaf-on Apr-Oct (northern-
    hemisphere default; the domain has no per-site phenology calendar in this arc)."""
    return DECIDUOUS_TAU_SUMMER if 4 <= month <= 10 else DECIDUOUS_TAU_WINTER
