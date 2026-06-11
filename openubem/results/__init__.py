"""Step-5 results orchestrator: aggregate_results + compute_validation_gates."""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from openubem import config
from openubem.results.aggregator import (
    _STEP5_COLS,
    _SUCCESS_STATUSES,
    compute_neighbourhood_summary,
    export_results,
    join_results,
)
from openubem.results.carbon import attach_gwp
from openubem.results.parser import parse_building


def aggregate_results(
    sim_manifest: "pd.DataFrame | Path",
    idf_manifest: "pd.DataFrame | Path",
    enriched_gdf: gpd.GeoDataFrame,
    output_dir: "Path | str",
    *,
    climate_sidecar: "pd.DataFrame | Path | None" = None,
    state: str | None = None,
    make_figures: bool = True,
    ep_version: str | None = None,
) -> gpd.GeoDataFrame:
    """Orchestrate Steps 3A-3G for a neighbourhood fleet (DESIGN §3F / PLAN P3/P4).

    Parameters
    ----------
    sim_manifest : path or DataFrame — 04_simulation_manifest.parquet
    idf_manifest : path or DataFrame — 03_idf_manifest.parquet
    enriched_gdf : 57-col GeoDataFrame from Steps 1-2
    output_dir   : directory for 05_* outputs
    climate_sidecar : 02a_climate_epw.parquet (primary state source, F8)
    state        : explicit 2-letter state code (used when climate_sidecar is None)
    make_figures : render the three observability figures (Module 16)
    ep_version   : EnergyPlus version string for summary metadata
    """
    output_dir = Path(output_dir)

    # ── Load manifests ────────────────────────────────────────────────────────
    if isinstance(sim_manifest, (str, Path)):
        sim_manifest = pd.read_parquet(sim_manifest)
    if isinstance(idf_manifest, (str, Path)):
        idf_manifest = pd.read_parquet(idf_manifest)

    # ── Resolve state per F8 / P3 ─────────────────────────────────────────────
    if climate_sidecar is not None:
        if isinstance(climate_sidecar, (str, Path)):
            climate_sidecar = pd.read_parquet(climate_sidecar)
        states_by_osm: dict[str, str] = {
            str(r["osm_id"]): str(r["state"])
            for _, r in climate_sidecar.iterrows()
            if "state" in climate_sidecar.columns
        }
    else:
        states_by_osm = {}

    def _resolve_state(osm_id: str) -> str | None:
        if osm_id in states_by_osm:
            return states_by_osm[osm_id]
        if state is not None:
            return state
        return None

    # ── Filter success rows ───────────────────────────────────────────────────
    success_statuses = {"success", "success_cached"}
    success_rows = sim_manifest[sim_manifest["status"].isin(success_statuses)].copy()

    # Build lookup: osm_id → idf manifest row (for num_zones, zoning_strategy)
    idf_lookup: dict[str, pd.Series] = {
        str(r["osm_id"]): r for _, r in idf_manifest.iterrows()
    }

    # ── P4: per-building sequential loop ────────────────────────────────────
    metrics_rows: list[dict[str, Any]] = []

    for _, sim_row in success_rows.iterrows():
        osm_id = str(sim_row["osm_id"])
        sql_path = sim_row.get("sql_path")
        csv_path = sim_row.get("csv_path")

        # Merge idf manifest info into manifest row for parse_building
        idf_row = idf_lookup.get(osm_id, pd.Series(dtype=object))
        manifest_row = sim_row.copy()
        for col in ["num_zones", "zoning_strategy"]:
            if col in idf_row.index and col not in manifest_row.index:
                manifest_row[col] = idf_row[col]
        # Carry enriched GDF columns needed for EUI denominator
        enriched_rows = enriched_gdf[enriched_gdf["osm_id"].astype(str) == osm_id]
        if len(enriched_rows) > 0:
            for col in ["footprint_area_m2", "levels", "height_m", "data_quality_flag"]:
                if col in enriched_rows.columns and col not in manifest_row.index:
                    manifest_row[col] = enriched_rows.iloc[0][col]

        try:
            parsed = parse_building(sql_path, csv_path, manifest_row)
        except RuntimeError as exc:
            # I2 breach: foreign osm_id → abort whole run (DESIGN §3B)
            raise RuntimeError(f"I2 breach in run for {osm_id}: {exc}") from exc

        # Attach GWP
        bld_state = _resolve_state(osm_id)
        if bld_state and parsed["parse_status"] != "failed_parse" and parsed["parse_status"] != "failed_zone_mismatch":
            parsed = attach_gwp(parsed, bld_state)

        # Map parse_status → simulation_status (F9: extended token set)
        parsed["simulation_status"] = parsed.pop("parse_status")
        metrics_rows.append(parsed)

    # Non-success rows pass through with NaN metrics + their status
    non_success = sim_manifest[~sim_manifest["status"].isin(success_statuses)].copy()
    for _, row in non_success.iterrows():
        nan_row: dict[str, Any] = {
            "osm_id": str(row["osm_id"]),
            "simulation_status": str(row.get("status", "not_simulated")),
            "error_summary": str(row.get("error_msg", "")),
        }
        for col in _STEP5_COLS:
            if col not in ("simulation_status", "error_summary"):
                nan_row[col] = float("nan") if "eui" in col or "gwp" in col or col == "iod" else None
        metrics_rows.append(nan_row)

    metrics_df = pd.DataFrame(metrics_rows)

    # ── F9: LEFT join onto 57-col enriched GDF ───────────────────────────────
    results_gdf = join_results(enriched_gdf, metrics_df)

    # ── F10: neighbourhood summary ────────────────────────────────────────────
    # Determine dominant eGRID subregion for metadata
    egrid_subregion: str | None = None
    if state:
        try:
            from openubem.results.carbon import load_egrid
            egrid = load_egrid()
            if state.upper() in egrid:
                egrid_subregion = egrid[state.upper()].get("subregion")
        except Exception:
            pass

    summary = compute_neighbourhood_summary(
        results_gdf,
        gwp_convention=config.GWP_CONVENTION,
        ep_version=ep_version or config.ENERGYPLUS_VERSION,
        egrid_subregion=egrid_subregion,
    )

    # ── §3G: Export ───────────────────────────────────────────────────────────
    export_results(results_gdf, output_dir, summary)

    # ── Module 16: figures ────────────────────────────────────────────────────
    if make_figures:
        try:
            from openubem.results.visualization import render_all_figures
            render_all_figures(results_gdf, output_dir / "figures")
        except Exception as exc:
            warnings.warn(f"Figure rendering failed (non-fatal): {exc}")

    return results_gdf


def compute_validation_gates(
    results_gdf: gpd.GeoDataFrame,
    reference_table: "pd.DataFrame | None" = None,
) -> dict[str, Any]:
    """Compute CBECS-style validation gates (P8: CBECS gates parked, OQ-1).

    Returns gate results dict; CBECS gates return None pending OQ-1 resolution.
    """
    # CBECS CV(RMSE)/NMBE/R²/KS gates blocked by OQ-1 — see PLAN §5 P8
    return {
        "cbecs_cv_rmse": None,
        "cbecs_nmbe": None,
        "cbecs_r2": None,
        "cbecs_ks_d": None,
        "note": "OQ-1: CBECS 2018 reference not extracted; gates skipped per PLAN P8",
    }
