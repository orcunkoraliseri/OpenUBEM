"""CLI: render simulation + validation figures into the two output dirs.

Usage:
    py -3 scripts/render_plots.py [--cells nyc_centre la_urban ...] [--only sim|val]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure repo root is importable
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from openubem.results.plotting_suite import (
    SIM_DIR,
    VAL_DIR,
    COMPARE_DIR,
    _load_cell_gdf,
    _load_cell_footprints,
    plot_eui_map,
    plot_eui_rank_curve,
    plot_archetype_eui_sorted_bar,
    plot_roundtrip_scatter,
    plot_dev_ranked_bar,
    plot_gap_decomposition,
    plot_climate_signal,
    plot_overview_grid,
    plot_eui_vs_reference,
    plot_sim_vs_reconstructed,
    plot_cross_cell_eui,
)

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre",  "la_urban",  "la_suburban",  "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

_VAL_BASE = _ROOT / "docs" / "validations" / "overAll" / "results"


def _render_sim(cells: list[str]) -> None:
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    for cell in cells:
        try:
            gdf = _load_cell_gdf(cell)
        except FileNotFoundError as exc:
            logger.warning("Skipping %s: %s", cell, exc)
            continue

        # Map uses real footprint polygons from 01_buildings.gpkg (real UTM coords)
        try:
            fp_gdf = _load_cell_footprints(cell)
        except FileNotFoundError as exc:
            logger.warning("Footprints unavailable for %s (%s); falling back to 05_results for map", cell, exc)
            fp_gdf = gdf

        p1 = plot_eui_map(fp_gdf, SIM_DIR / f"{cell}__eui_map.png", cell_name=cell)
        logger.info("Written: %s", p1)

        p2 = plot_eui_rank_curve(gdf, SIM_DIR / f"{cell}__eui_rank_curve.png", cell_name=cell)
        logger.info("Written: %s", p2)

        p3 = plot_archetype_eui_sorted_bar(gdf, SIM_DIR / f"{cell}__archetype_eui_bar.png", cell_name=cell)
        logger.info("Written: %s", p3)


def _render_val() -> None:
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    roundtrip_csv = _VAL_BASE / "roundtrip_report.csv"
    if roundtrip_csv.exists():
        df_rt = pd.read_csv(roundtrip_csv)
        p = plot_roundtrip_scatter(df_rt, VAL_DIR / "roundtrip_scatter.png")
        logger.info("Written: %s", p)
        p = plot_dev_ranked_bar(df_rt, VAL_DIR / "dev_ranked_bar.png")
        logger.info("Written: %s", p)
    else:
        logger.warning("roundtrip_report.csv not found at %s; skipping T04/T05", roundtrip_csv)

    decomp_csv = _VAL_BASE / "r6_4_decomposition.csv"
    if decomp_csv.exists():
        df_dc = pd.read_csv(decomp_csv)
        p = plot_gap_decomposition(df_dc, VAL_DIR / "gap_decomposition.png")
        logger.info("Written: %s", p)
    else:
        logger.warning("r6_4_decomposition.csv not found at %s; skipping T06", decomp_csv)

    # T07: build cell_stats from per-cell 05_results.gpkg
    rows = []
    for cell in _ALL_CELLS:
        city, ring = cell.rsplit("_", 1)
        try:
            gdf = _load_cell_gdf(cell)
            success = gdf[gdf["simulation_status"].isin({"success", "success_cached", "success_csv_fallback"})]
            rows.append({
                "cell": cell,
                "city": city,
                "ring": ring,
                "mean_heating_eui": float(success["heating_eui_kwh_m2"].mean()) if "heating_eui_kwh_m2" in success.columns else 0.0,
                "mean_cooling_eui": float(success["cooling_eui_kwh_m2"].mean()) if "cooling_eui_kwh_m2" in success.columns else 0.0,
            })
        except FileNotFoundError:
            rows.append({"cell": cell, "city": city, "ring": ring,
                         "mean_heating_eui": 0.0, "mean_cooling_eui": 0.0})

    if rows:
        cell_stats = pd.DataFrame(rows)
        p = plot_climate_signal(cell_stats, VAL_DIR / "climate_signal.png")
        logger.info("Written: %s", p)


def _render_overview() -> None:
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    out_path, vmin, vmax = plot_overview_grid(COMPARE_DIR / "eui_overview_grid.png")
    logger.info("Written: %s  (vmin=%.1f, vmax=%.1f)", out_path, vmin, vmax)


def _render_comparison() -> None:
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    p = plot_eui_vs_reference(COMPARE_DIR / "eui_vs_cbecs_reference.png")
    logger.info("Written: %s", p)
    p = plot_sim_vs_reconstructed(COMPARE_DIR / "eui_sim_vs_reconstructed.png")
    logger.info("Written: %s", p)
    p = plot_cross_cell_eui(COMPARE_DIR / "eui_cross_cell_summary.png")
    logger.info("Written: %s", p)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render OpenUBEM plotting suite figures.")
    parser.add_argument("--cells", nargs="+", default=_ALL_CELLS,
                        help="Cells to render sim figures for (default: all 12).")
    parser.add_argument("--only", choices=["sim", "val", "overview", "comparison"], default=None,
                        help="Render only sim, val, overview, or comparison figures.")
    args = parser.parse_args()

    if args.only in (None, "sim"):
        _render_sim(args.cells)
    if args.only in (None, "val"):
        _render_val()
    if args.only in (None, "overview"):
        _render_overview()
    if args.only in (None, "comparison"):
        _render_comparison()


if __name__ == "__main__":
    main()
