"""T20 - exposure metrics & parcel aggregation (PLAN §7 T20).

PHEH/CTSI formulas transcribed verbatim from the plan's own "How":
    PHEH = sum_zones sum_t Pop * dt * 1(UTCI > 46 degC)      [U06 Table 4 line 45]
    CTSI = integral max(0, UTCI - 26) dt   [degC*h]           [U06 Table 4 line 46]

No population raster exists anywhere in this project (no demographic layer, honest gap, plan's
own directive: "report area-hours instead of person-hours and say so in the field name... never
substitute a made-up density"). SHVI (U06 Table 4 line 47) needs one and is explicitly deferred.

buffer_m (aggregate_to_parcels' per-building surroundings ring) is a spatial-averaging SCALE the
caller chooses, exactly like wind.py's window_radius_m -- not a cited physical constant (that
module's own docstring makes the same distinction). 10 m is a sidewalk/immediate-frontage scale,
smaller than the neighbourhood-scale UTCI_DOMAIN_BUFFER_M (200 m, F-05/T08) because the question
this join answers is "what is it like immediately outside this specific building", not
"what is the neighbourhood doing".

§6a (binding): this module never reads or writes 05_* -- it operates purely on arrays and a
buildings/results GeoDataFrame/DataFrame the caller already loaded read-only. T18 is the only
place 05_results.gpkg is opened, and it opens it read-only, writing the join's result to
06_mc_summary.gpkg only.
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
from rasterio import features

PHEH_THRESHOLD_C = 46.0  # P-04 / U01 Table 1 -- "Extreme heat stress" class floor
CTSI_BASELINE_C = 26.0   # P-04 / U01 Table 1 -- "No thermal stress" class ceiling

DEFAULT_PARCEL_BUFFER_M = 10.0  # spatial-averaging SCALE, not a cited constant (module docstring)


def person_hours_extreme_heat(
    utci_stack_c,
    *,
    res_m: float,
    dt_hours=1.0,
    population_raster=None,
    threshold_c: float = PHEH_THRESHOLD_C,
):
    """PHEH = sum_cells sum_t weight_cell * dt * 1(UTCI > threshold_c).

    utci_stack_c: (n_hours, rows, cols). dt_hours: scalar or (n_hours,) array of hour-weights.
    weight_cell = population_raster (persons per cell, an absolute count) if supplied, else the
    cell's own area in m^2 (the honest area-hours proxy -- module docstring). Returns
    (total_value, field_name, per_cell_hours_over_threshold).
    """
    stack = np.asarray(utci_stack_c, dtype=np.float64)
    n_hours = stack.shape[0]
    exceed = (stack > threshold_c).astype(np.float64)
    dt = np.broadcast_to(np.asarray(dt_hours, dtype=np.float64), (n_hours,))
    hours_over = np.tensordot(dt, exceed, axes=(0, 0))  # (rows, cols)

    if population_raster is not None:
        weight = np.asarray(population_raster, dtype=np.float64)
        field_name = "person_hours_extreme_heat_h"
    else:
        weight = np.full(stack.shape[1:], float(res_m) * float(res_m), dtype=np.float64)
        field_name = "area_hours_extreme_heat_m2h"

    total = float(np.nansum(weight * hours_over))
    return total, field_name, hours_over


def cumulative_thermal_stress_index(utci_stack_c, *, dt_hours=1.0, baseline_c: float = CTSI_BASELINE_C):
    """CTSI = sum_t max(0, UTCI - baseline_c) * dt, per cell [degC*h]. Returns the (rows, cols)
    raster (never summed to a scalar here -- T18/exposure JSON decides how to reduce it further)."""
    stack = np.asarray(utci_stack_c, dtype=np.float64)
    n_hours = stack.shape[0]
    dt = np.broadcast_to(np.asarray(dt_hours, dtype=np.float64), (n_hours,))
    excess = np.clip(stack - baseline_c, 0.0, None)
    return np.tensordot(dt, excess, axes=(0, 0))


def aggregate_to_parcels(
    buildings_gdf: gpd.GeoDataFrame,
    results_df,
    domain,
    utci_peak_c,
    utci_mean_c,
    ctsi_degc_h,
    *,
    buffer_m: float = DEFAULT_PARCEL_BUFFER_M,
    osm_id_col: str = "osm_id",
) -> gpd.GeoDataFrame:
    """Zonal stats of utci_peak/utci_mean/ctsi over each building's footprint buffered by
    buffer_m, joined onto results_df (the caller's already-read-only-loaded 05_results
    attribute table) by osm_id. Never opens or writes 05_* itself (module docstring, §6a) --
    the caller (T18) owns the read-only open and the 06_mc_summary.gpkg write.
    """
    shape = domain.shape
    transform = domain.transform
    interior = domain.building_mask

    rows = []
    for _, b in buildings_gdf.iterrows():
        ring = b.geometry.buffer(buffer_m)
        mask = features.rasterize(
            [(ring, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8"
        ).astype(bool)
        mask &= ~interior
        n_valid = int(mask.sum())

        def _stat(field, fn):
            if n_valid == 0:
                return np.nan
            vals = np.asarray(field)[mask]
            vals = vals[np.isfinite(vals)]
            return float(fn(vals)) if vals.size else np.nan

        rows.append({
            osm_id_col: b[osm_id_col],
            "utci_peak_c": _stat(utci_peak_c, np.max),
            "utci_mean_c": _stat(utci_mean_c, np.mean),
            "ctsi_degc_h": _stat(ctsi_degc_h, np.mean),
            "n_valid_surrounding_pixels": n_valid,
            "parcel_buffer_m": buffer_m,
            "geometry": b.geometry,
        })

    parcel_gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=domain.crs)
    if results_df is not None and len(results_df) > 0:
        merged = parcel_gdf.merge(
            results_df.drop(columns=["geometry"], errors="ignore"),
            on=osm_id_col, how="left", suffixes=("", "_stage5"),
        )
        parcel_gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs=domain.crs)
    return parcel_gdf
