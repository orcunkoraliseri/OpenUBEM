"""Step-5 Module 14: spatial join, neighbourhood aggregation, and exports (DESIGN §3F-§3G).

Note (OPEN-43, 2026-08-12): this module aggregates per-cell (per-neighbourhood) only. There is no
fleet-wide roll-up function here or anywhere else in the codebase. The published fleet EUI is
computed outside this module, by pooling every simulated building's total_eui_kwh_m2 and floor area
across all cells at once: Sigma(EUI x floor_area) / Sigma(floor_area) over all successfully simulated
buildings. See scripts/analysis/open43_fleet_aggregations.py for the reference implementation and
docs/docs_ACTIVE/openings/extra/FIX_open-43_fleet-aggregation.md for the derivation. Do not confuse
this pooled fleet figure with any per-cell weighted_total_eui value produced by this module.
"""
from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from openubem import config

# ── F9: Step-5 output columns (Phase-E: 25 EUI/GWP + 3 meta) ─────────────────
# Phase-E T14: expanded from 14 to 28 columns (9 EUI + 9 GWP + iod + parse_status + error_summary +
# simulation_status + dhw_gas_eui + dhw_elec_eui).
_STEP5_COLS = [
    # Core EUI (4, always populated when simulation succeeds)
    "heating_eui_kwh_m2",
    "cooling_eui_kwh_m2",
    "lighting_eui_kwh_m2",
    "equipment_eui_kwh_m2",
    # Phase-E service-load EUI (7 new) + elevators (OPEN-46 T05, 10th end-use)
    "fans_eui_kwh_m2",
    "pumps_eui_kwh_m2",
    "dhw_gas_eui_kwh_m2",
    "dhw_elec_eui_kwh_m2",
    "dhw_eui_kwh_m2",
    "cooking_eui_kwh_m2",
    "refrigeration_eui_kwh_m2",
    "elevators_eui_kwh_m2",
    "total_eui_kwh_m2",
    # GWP columns (9 + elevators)
    "gwp_heating_kgco2_m2",
    "gwp_cooling_kgco2_m2",
    "gwp_lighting_kgco2_m2",
    "gwp_equipment_kgco2_m2",
    "gwp_fans_kgco2_m2",
    "gwp_pumps_kgco2_m2",
    "gwp_dhw_kgco2_m2",
    "gwp_cooking_kgco2_m2",
    "gwp_refrigeration_kgco2_m2",
    "gwp_elevators_kgco2_m2",
    "gwp_total_kgco2_m2",
    # meta
    "iod",
    "simulation_status",
    "error_summary",
    # OPEN-01 (T05, ruling 6): per-building EUI denominator, resolved once in
    # parser.py::parse_building and carried through so the aggregator never re-derives it.
    "floor_area_m2",
    "floor_area_provenance",
]

_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}


def join_results(
    enriched_gdf: gpd.GeoDataFrame,
    metrics_df: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """LEFT-join Phase-E Step-5 metric columns onto the enriched GDF (DESIGN line 166).

    Phase-E (T14): 28 columns (9 EUI + 9 GWP + dhw_gas/elec + iod + 3 meta).
    Returns a GDF with NaN metrics for buildings not simulated or with failed parsing.
    data_quality_flag merged append-only per P1.
    """
    # Normalize osm_id for join
    enriched = enriched_gdf.copy()
    metrics = metrics_df.copy()

    enriched["_osm_id_key"] = enriched["osm_id"].astype(str)
    metrics["_osm_id_key"] = metrics["osm_id"].astype(str)

    # Columns to take from metrics_df (14 + data_quality_flag delta + osm_id key)
    metric_cols = _STEP5_COLS + ["data_quality_flag", "_osm_id_key"]
    metrics_sub = metrics[[c for c in metric_cols if c in metrics.columns]].copy()

    result = enriched.merge(metrics_sub, on="_osm_id_key", how="left", suffixes=("", "_step5"))

    # P1: data_quality_flag append-only (merge from right into left)
    if "data_quality_flag_step5" in result.columns:
        result["data_quality_flag"] = result.apply(
            lambda r: _merge_flags(r["data_quality_flag"], r["data_quality_flag_step5"]),
            axis=1,
        )
        result = result.drop(columns=["data_quality_flag_step5"])

    result = result.drop(columns=["_osm_id_key"])

    # Fill simulation_status for buildings not in metrics (never attempted)
    if "simulation_status" in result.columns:
        result["simulation_status"] = result["simulation_status"].fillna("not_simulated")

    return result


def _merge_flags(base: Any, delta: Any) -> str:
    """Append delta tokens to base flag string; skip if identical or empty."""
    import pandas as _pd
    base_str = "" if (_pd.isna(base) or base is None) else str(base)
    delta_str = "" if (_pd.isna(delta) or delta is None) else str(delta)
    if not delta_str:
        return base_str
    if not base_str:
        return delta_str
    base_tokens = {t.strip() for t in base_str.split(",") if t.strip()}
    new_tokens = [t.strip() for t in delta_str.split(",") if t.strip() and t.strip() not in base_tokens]
    if not new_tokens:
        return base_str
    return base_str + "," + ",".join(new_tokens)


def compute_neighbourhood_summary(
    results_gdf: gpd.GeoDataFrame,
    *,
    gwp_convention: str = config.GWP_CONVENTION,
    ep_version: str | None = None,
    egrid_subregion: str | None = None,
    run_timestamp: str | None = None,
) -> dict[str, Any]:
    """Compute F10 neighbourhood-level aggregates (DESIGN lines 168-177, 189).

    Floor-area weighting: Σ kWh ÷ Σ m² per end use (not mean-of-intensities).
    Timestamps excluded from determinism comparisons per P6.
    """
    import math

    # OPEN-01 (T05, ruling 6): floor area denominator. Read the per-building value
    # parser.py already resolved (floor_area_m2 — simulated area from eplusout.eio,
    # footprint x floors on fallback; see resolve_simulated_floor_area()) rather than
    # re-deriving it here, per plan step 3. Rows without that column (e.g. synthetic
    # GeoDataFrames built directly for tests, never routed through parse_building) fall
    # back to the pre-OPEN-01 footprint x floors computation so older call sites are unaffected.
    from openubem.geometry.footprint import derive_num_floors

    gdf = results_gdf.copy()
    if "floor_area_m2" in gdf.columns:
        fallback = gdf.apply(
            lambda r: float(r["footprint_area_m2"]) * derive_num_floors(r), axis=1
        )
        gdf["_floor_area"] = pd.to_numeric(gdf["floor_area_m2"], errors="coerce").fillna(fallback)
    else:
        gdf["_floor_area"] = gdf.apply(
            lambda r: float(r["footprint_area_m2"]) * derive_num_floors(r), axis=1
        )

    success_mask = gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    success = gdf[success_mask].copy()

    # Per-end-use floor-area-weighted EUI (Σ kWh ÷ Σ m²)
    eui_cols = [
        "heating_eui_kwh_m2",
        "cooling_eui_kwh_m2",
        "lighting_eui_kwh_m2",
        "equipment_eui_kwh_m2",
        "total_eui_kwh_m2",
    ]
    weighted_eui: dict[str, Any] = {}
    total_success_floor_area = float(success["_floor_area"].sum()) if len(success) > 0 else 0.0
    for col in eui_cols:
        if col in success.columns and total_success_floor_area > 0:
            annual_kwh = (success[col] * success["_floor_area"]).sum()
            weighted_eui[col] = (
                float(annual_kwh / total_success_floor_area)
                if not math.isnan(annual_kwh) else None
            )
        else:
            weighted_eui[col] = None

    # Absolute GWP (Σ gwp_total × floor_area)
    gwp_total: Any = None
    if "gwp_total_kgco2_m2" in success.columns and len(success) > 0:
        gwp_abs = (success["gwp_total_kgco2_m2"] * success["_floor_area"]).sum()
        gwp_total = float(gwp_abs) if not math.isnan(gwp_abs) else None

    # IOD stats
    iod_vals = success["iod"].dropna() if "iod" in success.columns else pd.Series([], dtype=float)
    mean_iod = float(iod_vals.mean()) if len(iod_vals) > 0 else None
    p95_iod = float(iod_vals.quantile(0.95)) if len(iod_vals) > 0 else None

    # Status breakdown
    n_by_status: dict[str, int] = gdf["simulation_status"].fillna("not_simulated").value_counts().to_dict()

    # pct_floor_area_simulated
    total_floor_area = float(gdf["_floor_area"].sum())
    pct_fa_sim = (
        float(total_success_floor_area / total_floor_area)
        if total_floor_area > 0 else 0.0
    )

    summary: dict[str, Any] = {
        "neighbourhood_eui_weighted_kwh_m2": weighted_eui,
        "neighbourhood_gwp_total_kgco2": gwp_total,
        "mean_iod_c": mean_iod,
        "p95_iod_c": p95_iod,
        "n_buildings_by_status": {str(k): int(v) for k, v in n_by_status.items()},
        "pct_floor_area_simulated": pct_fa_sim,
        "metadata": {
            "gwp_convention": gwp_convention,
            "ep_version": ep_version,
            "egrid_subregion": egrid_subregion,
            # P6: timestamps present but excluded from determinism comparisons
            "generated_utc": run_timestamp or datetime.now(timezone.utc).isoformat(),
        },
    }
    return summary


def export_results(
    results_gdf: gpd.GeoDataFrame,
    output_dir: Path,
    summary: dict[str, Any],
) -> dict[str, Path]:
    """Write F11 export trio + schema sidecar + summary JSON (DESIGN lines 184-193).

    Returns dict of artifact paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, Path] = {}

    # ── 05_results.gpkg (canonical, UTM) ──────────────────────────────────────
    gpkg_path = output_dir / "05_results.gpkg"
    results_gdf.to_file(str(gpkg_path), layer="buildings", driver="GPKG")
    artifacts["gpkg"] = gpkg_path

    # ── 05_results.schema.json (70 entries) ──────────────────────────────────
    schema_entries = []
    for col in results_gdf.columns:
        if col == "geometry":
            continue
        dtype = str(results_gdf[col].dtype)
        schema_entries.append({"name": col, "dtype": dtype})
    schema_path = output_dir / "05_results.schema.json"
    schema_path.write_text(
        json.dumps({"columns": schema_entries, "n_columns": len(schema_entries)}, indent=2),
        encoding="utf-8",
    )
    artifacts["schema"] = schema_path

    # ── 05_results.geojson (EPSG:4326) ────────────────────────────────────────
    geojson_path = output_dir / "05_results.geojson"
    gdf_wgs84 = results_gdf.to_crs(epsg=4326)
    gdf_wgs84.to_file(str(geojson_path), driver="GeoJSON")
    artifacts["geojson"] = geojson_path

    # ── 05_results.csv (geometry dropped; centroid lon/lat added) ─────────────
    # Compute centroids in original CRS (metric), then reproject to WGS84
    csv_path = output_dir / "05_results.csv"
    gdf_wgs84_cent = gdf_wgs84.copy()
    centroids_wgs84 = results_gdf.geometry.centroid.to_crs(epsg=4326)
    gdf_wgs84_cent["centroid_lon"] = centroids_wgs84.x
    gdf_wgs84_cent["centroid_lat"] = centroids_wgs84.y
    csv_df = pd.DataFrame(gdf_wgs84_cent.drop(columns=["geometry"]))
    csv_df.to_csv(csv_path, index=False)
    artifacts["csv"] = csv_path

    # ── 05_neighbourhood_summary.json ─────────────────────────────────────────
    summary_path = output_dir / "05_neighbourhood_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    artifacts["summary"] = summary_path

    return artifacts
