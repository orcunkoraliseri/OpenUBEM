"""Step-5 results orchestrator: aggregate_results + compute_validation_gates."""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
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

# ── CBECS gate helpers ────────────────────────────────────────────────────────

_PBA_MAP_PATH = Path(__file__).parent.parent / "data" / "cbecs_pba_map.json"

# F2 thresholds (DESIGN lines 221–224)
_CV_RMSE_THRESHOLD = 30.0
_NMBE_THRESHOLD = 10.0
_R2_THRESHOLD = 0.6
_KS_THRESHOLD = 0.10


def _load_pba_map() -> dict[str, Any]:
    with open(_PBA_MAP_PATH, encoding="utf-8") as fh:
        return json.load(fh)["pba_map"]


def _fleet_levels_medians(gdf: gpd.GeoDataFrame) -> "tuple[dict, int | None]":
    """OPEN-35 T06: the SAME group-/global-median levels lookup the classifier itself
    computes (BuildingClassifier._build_levels_median_lookup), called once on the
    enriched_gdf already in scope here -- not a second, independently-derived route.
    Mirrors builder.py/aggregator.py's T05 helper of the same name."""
    from openubem.semantic.building_classifier import BuildingClassifier
    return BuildingClassifier()._build_levels_median_lookup(gdf)


def _weighted_quantiles(values: np.ndarray, weights: np.ndarray, quantiles: np.ndarray) -> np.ndarray:
    """Weighted quantiles via sorted-CDF interpolation."""
    order = np.argsort(values)
    sv = values[order]
    sw = weights[order]
    cdf = np.cumsum(sw) / sw.sum()
    return np.interp(quantiles, cdf, sv)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(values, weights=weights))


def _weighted_cdf(values: np.ndarray, weights: np.ndarray, eval_points: np.ndarray) -> np.ndarray:
    """Weighted empirical CDF evaluated at eval_points."""
    order = np.argsort(values)
    sv = values[order]
    sw = weights[order]
    cdf = np.cumsum(sw) / sw.sum()
    return np.interp(eval_points, sv, cdf, left=0.0, right=1.0)


def aggregate_results(
    sim_manifest: "pd.DataFrame | Path",
    idf_manifest: "pd.DataFrame | Path",
    enriched_gdf: gpd.GeoDataFrame,
    output_dir: "Path | str",
    *,
    climate_sidecar: "pd.DataFrame | Path | None" = None,
    state: str | None = None,
    make_figures: bool = True,
    export_html: bool = False,
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
    export_html  : optionally emit the self-contained 3D viewer HTML (T13).
        Off by default (adds ~geometry-parse cost); also enabled by the env
        toggle OPENUBEM_EXPORT_HTML=1. Non-fatal, mirrors make_figures.
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

    # OPEN-35 T06: computed once, classifier's own route, so parse_building() can reach
    # the Scope B agreement fallback (derive_num_floors()'s levels_group_median /
    # levels_global_median kwargs) via manifest_row -- it has no other access to the
    # fleet-wide gdf. See _derive_num_floors_wired() in openubem/results/parser.py.
    _levels_group_median, _levels_global_median = _fleet_levels_medians(enriched_gdf)

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
        # Carry enriched GDF columns needed for EUI denominator. archetype_source
        # (OPEN-35 T06) added so parse_building() can gate the Scope B agreement fix.
        enriched_rows = enriched_gdf[enriched_gdf["osm_id"].astype(str) == osm_id]
        if len(enriched_rows) > 0:
            enriched_row = enriched_rows.iloc[0]
            for col in ["footprint_area_m2", "levels", "height_m", "data_quality_flag", "archetype_source"]:
                if col in enriched_rows.columns and col not in manifest_row.index:
                    manifest_row[col] = enriched_row[col]
            from openubem.semantic.building_classifier import _normalise_use_class
            manifest_row["_use_class"] = _normalise_use_class(enriched_row)[0]
        manifest_row["_levels_group_median"] = _levels_group_median
        manifest_row["_levels_global_median"] = _levels_global_median

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

    # ── T13: optional self-contained 3D viewer HTML (flag-gated, non-fatal) ────
    if export_html or bool(int(os.environ.get("OPENUBEM_EXPORT_HTML", "0"))):
        try:
            from openubem.viz.viewer_export import export_viewer
            run_id = output_dir.resolve().parent.name or "run"
            export_viewer(
                idf_manifest, enriched_gdf, results_gdf,
                run_id=run_id,
                source_refs={"results": "05_results.csv",
                             "buildings": "enriched_gdf",
                             "manifest": "03_idf_manifest.parquet"},
            )
        except Exception as exc:
            warnings.warn(f"Viewer HTML export failed (non-fatal): {exc}")

    return results_gdf


def compute_validation_gates(
    results_gdf: gpd.GeoDataFrame,
    reference_path: "Path | str | None" = None,
    reference_table: "pd.DataFrame | None" = None,
) -> dict[str, Any]:
    """Compute CBECS 2018 validation gates per DESIGN §5.1 and M-R2-3.

    With reference_path=None (legacy): returns four None values (OQ-1 stub).
    With a path or reference_table: computes real CV(RMSE), NMBE, R², KS_D.

    Exclusions per M-R2-2 / M-R2-5:
    - MidriseApartment, HighriseApartment: excluded from ALL four gates.
    - DataCenters: excluded from ALL four gates.
    - OpenUBEMUnknown: excluded from archetype R² only; included in distribution gates.
    """
    # Legacy stub: no reference provided
    if reference_path is None and reference_table is None:
        return {
            "cbecs_cv_rmse": None,
            "cbecs_nmbe": None,
            "cbecs_r2": None,
            "cbecs_ks_d": None,
            "note": "OQ-1: reference_path not provided; gates skipped",
        }

    # Load reference
    if reference_table is not None:
        ref = reference_table.copy()
    else:
        ref = pd.read_csv(reference_path)

    pba_map = _load_pba_map()

    # Columns expected in results_gdf: archetype_id, eui_kwh_m2 (or site_eui_kwh_m2)
    eui_col = "eui_kwh_m2" if "eui_kwh_m2" in results_gdf.columns else "site_eui_kwh_m2"

    # Drop rows without EUI
    sim = results_gdf[[eui_col, "archetype_id"]].dropna(subset=[eui_col]).copy()
    sim = sim.rename(columns={eui_col: "eui_kwh_m2"})

    # Exclusions: apartments and data centers from ALL gates (M-R2-2, M-R2-5)
    excluded_all = {
        k for k, v in pba_map.items() if v is None
    }
    sim_dist = sim[~sim["archetype_id"].isin(excluded_all)].copy()

    n_excluded = int((sim["archetype_id"].isin(excluded_all)).sum())

    sim_eui = sim_dist["eui_kwh_m2"].values.astype(float)
    ref_eui = ref["eui_kwh_m2"].values.astype(float)
    ref_wt = ref["finalwt"].values.astype(float)

    # ── (a) CV(RMSE) — M-R2-3a ──
    percentiles = np.linspace(0, 1, len(sim_eui) + 2)[1:-1]
    sim_sorted = np.sort(sim_eui)
    cbecs_q = _weighted_quantiles(ref_eui, ref_wt, percentiles)
    rmse = float(np.sqrt(np.mean((sim_sorted - cbecs_q) ** 2)))
    cbecs_wmean = _weighted_mean(ref_eui, ref_wt)
    cv_rmse = rmse / cbecs_wmean * 100.0

    # ── (b) NMBE — M-R2-3b ──
    sim_mean = float(np.mean(sim_eui))
    nmbe = (sim_mean - cbecs_wmean) / cbecs_wmean * 100.0

    # ── (c) R² archetype-level — M-R2-3c ──
    # Excluded from R²: apartments, data centers, OpenUBEMUnknown
    r2_excluded = excluded_all | {"OpenUBEMUnknown"}
    sim_arch = sim[~sim["archetype_id"].isin(r2_excluded)].copy()

    # Per-archetype simulation mean EUI
    arch_sim_means = (
        sim_arch.groupby("archetype_id")["eui_kwh_m2"].mean().reset_index()
    )
    arch_sim_means.columns = ["archetype_id", "sim_mean_eui"]
    arch_sim_means["pba_code"] = arch_sim_means["archetype_id"].map(pba_map)

    # Per-PBA CBECS weighted mean EUI; drop PBAs with unweighted n<10 in NE
    ref["pba_code"] = ref["pba_code"].astype(int)
    pba_stats = (
        ref.groupby("pba_code")
        .apply(lambda g: pd.Series({
            "wmean_eui": _weighted_mean(g["eui_kwh_m2"].values, g["finalwt"].values),
            "n_unweighted": len(g),
        }))
        .reset_index()
    )
    pba_stats_filtered = pba_stats[pba_stats["n_unweighted"] >= 10]
    dropped_pba_n_lt10 = pba_stats[pba_stats["n_unweighted"] < 10]["pba_code"].tolist()

    arch_sim_means["pba_code"] = arch_sim_means["pba_code"].astype(float).astype("Int64")
    merged = arch_sim_means.merge(
        pba_stats_filtered[["pba_code", "wmean_eui"]],
        on="pba_code",
        how="inner",
    )

    if len(merged) >= 2:
        from scipy.stats import pearsonr
        r, _ = pearsonr(merged["sim_mean_eui"].values, merged["wmean_eui"].values)
        r2 = float(r ** 2)
    else:
        r2 = float("nan")

    # ── (d) KS D — M-R2-3d ──
    eval_pts = np.sort(np.concatenate([sim_eui, ref_eui]))
    sim_cdf = np.searchsorted(np.sort(sim_eui), eval_pts, side="right") / len(sim_eui)
    cbecs_cdf = _weighted_cdf(ref_eui, ref_wt, eval_pts)
    ks_d = float(np.max(np.abs(sim_cdf - cbecs_cdf)))

    return {
        "cbecs_cv_rmse": round(cv_rmse, 3),
        "cbecs_cv_rmse_pass": cv_rmse < _CV_RMSE_THRESHOLD,
        "cbecs_nmbe": round(nmbe, 3),
        "cbecs_nmbe_pass": abs(nmbe) < _NMBE_THRESHOLD,
        "cbecs_r2": round(r2, 4) if not np.isnan(r2) else None,
        "cbecs_r2_pass": (not np.isnan(r2)) and r2 > _R2_THRESHOLD,
        "cbecs_ks_d": round(ks_d, 4),
        "cbecs_ks_d_pass": ks_d < _KS_THRESHOLD,
        "n_sim_buildings": len(sim_dist),
        "n_excluded_all_gates": n_excluded,
        "dropped_pba_n_lt10": dropped_pba_n_lt10,
    }
