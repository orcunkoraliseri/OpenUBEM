"""Plotting suite: map v2 + ordered x-y charts + validation figures (DESIGN §3G / F11).
Additive module — does not import from visualization.py.
"""
from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.cm as mcm
import matplotlib.colors as mcolors
import numpy as np
import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output-dir constants
# ---------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parents[2]  # repo root
SIM_DIR = _BASE / "openubem" / "outputs" / "simulationResults"
VAL_DIR = _BASE / "openubem" / "outputs" / "validaitonResults"
COMPARE_DIR = _BASE / "openubem" / "outputs" / "comparisons"

_REGIONAL_COEFFS_PATH = _BASE / "openubem" / "data" / "service_loads" / "enduse_fractions_regional.json"
_PHASED_BASE = _BASE / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"


def _phased_subdir() -> "str | None":
    """Return OPENUBEM_PHASED_SUBDIR env value, or None when unset/empty."""
    return os.environ.get("OPENUBEM_PHASED_SUBDIR") or None

# ---------------------------------------------------------------------------
# Status sets (mirror visualization.py; do not import from it)
# ---------------------------------------------------------------------------
_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}
_FAILED_STATUSES = {"failed_parse", "failed_zone_mismatch", "not_simulated"}

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _save(fig: plt.Figure, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _load_cell_gdf(cell: str) -> gpd.GeoDataFrame:
    """Load 05_results.gpkg for a cell; raises FileNotFoundError if absent.

    When OPENUBEM_PHASED_SUBDIR is set (e.g. 'phaseD2'), reads from
    docs/validations/overAll/results/{subdir}/{cell}/05_results.gpkg and applies
    regional service-load reconstruction so total_eui_reconstructed_kwh_m2 is present.
    Default (no env var) reads from runtime/ubem_validation/cases/{cell}/results/
    unchanged.
    """
    phased = _phased_subdir()
    if phased:
        p = _PHASED_BASE / phased / cell / "05_results.gpkg"
    else:
        p = _BASE / "runtime" / "ubem_validation" / "cases" / cell / "results" / "05_results.gpkg"
    if not p.exists():
        raise FileNotFoundError(f"05_results.gpkg not found for cell {cell!r}: {p}")
    gdf = gpd.read_file(str(p))
    if phased:
        if "city" not in gdf.columns:
            gdf = gdf.copy()
            gdf["city"] = cell.rsplit("_", 1)[0]
        from openubem.results.service_loads import load_coefficients, reconstruct_frame  # noqa: PLC0415
        _coeffs = load_coefficients(_REGIONAL_COEFFS_PATH)
        _df = pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))
        _df_recon = reconstruct_frame(_df, _coeffs, region_col="city")
        for col in _df_recon.columns:
            gdf[col] = _df_recon[col].values
    return gdf


def _load_cell_footprints(cell: str) -> gpd.GeoDataFrame:
    """Load 01_buildings.gpkg polygons, left-merging EUI/status attrs from 05_results.gpkg on osm_id.
    Overlapping cols (levels, height_m, footprint_area_m2, data_quality_flag) prefer results values.
    Raises FileNotFoundError if either file is missing.

    When OPENUBEM_PHASED_SUBDIR is set, geometry always comes from the runtime tree
    (unchanged) but EUI/status attributes come from the phased results tree; regional
    reconstruction is applied to those attributes before the merge.
    """
    phased = _phased_subdir()
    p_fp = _BASE / "runtime" / "ubem_validation" / "cases" / cell / "01_buildings.gpkg"
    if phased:
        p_res = _PHASED_BASE / phased / cell / "05_results.gpkg"
    else:
        p_res = _BASE / "runtime" / "ubem_validation" / "cases" / cell / "results" / "05_results.gpkg"
    if not p_fp.exists():
        raise FileNotFoundError(f"01_buildings.gpkg not found for cell {cell!r}: {p_fp}")
    if not p_res.exists():
        raise FileNotFoundError(f"05_results.gpkg not found for cell {cell!r}: {p_res}")

    fp = gpd.read_file(str(p_fp))
    res = gpd.read_file(str(p_res))

    # When phased, apply regional reconstruction to results before merging
    if phased:
        if "city" not in res.columns:
            res = res.copy()
            res["city"] = cell.rsplit("_", 1)[0]
        from openubem.results.service_loads import load_coefficients, reconstruct_frame  # noqa: PLC0415
        _coeffs = load_coefficients(_REGIONAL_COEFFS_PATH)
        _df = pd.DataFrame(res.drop(columns=["geometry"], errors="ignore"))
        _df_recon = reconstruct_frame(_df, _coeffs, region_col="city")
        for col in _df_recon.columns:
            res[col] = _df_recon[col].values

    # Columns to bring from results (drop geometry; overlapping attrs handled via suffix then prefer)
    _OVERLAP = {"levels", "height_m", "footprint_area_m2", "data_quality_flag"}
    res_attr = res.drop(columns=["geometry"], errors="ignore")

    merged = fp.merge(res_attr, on="osm_id", how="left", suffixes=("_fp", "_res"))

    # Prefer results values for overlap columns
    for col in _OVERLAP:
        col_res = f"{col}_res"
        col_fp = f"{col}_fp"
        if col_res in merged.columns and col_fp in merged.columns:
            merged[col] = merged[col_res].combine_first(merged[col_fp])
            merged.drop(columns=[col_fp, col_res], inplace=True)

    return merged


# ---------------------------------------------------------------------------
# T02 — Map v2: footprint polygons + basemap
# ---------------------------------------------------------------------------

def plot_eui_map(cell_gdf: gpd.GeoDataFrame, output_path: Path, cell_name: str = "") -> Path:
    """Footprint polygons coloured by EUI on CartoDB.Positron basemap.
    Failed buildings shown as grey /// hatched. Basemap degrades gracefully.
    Input gdf should come from _load_cell_footprints (Polygon geometry, real UTM coords).
    """
    output_path = Path(output_path)

    gdf = cell_gdf.copy()
    success_mask = gdf["simulation_status"].isin(_SUCCESS_STATUSES)

    # Reproject to Web Mercator for basemap
    try:
        gdf_web = gdf.to_crs(epsg=3857)
    except Exception as exc:  # noqa: BLE001
        logger.warning("CRS reproject failed (%s); using native CRS", exc)
        gdf_web = gdf

    success_gdf = gdf_web[success_mask].copy()
    failed_gdf = gdf_web[~success_mask].copy()

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    if len(success_gdf) > 0 and success_gdf["total_eui_kwh_m2"].notna().any():
        success_gdf.plot(
            column="total_eui_kwh_m2",
            cmap="YlOrRd",
            legend=True,
            legend_kwds={"label": "Total EUI (kWh/m²/yr)", "shrink": 0.6},
            ax=ax,
            edgecolor="0.3",
            linewidth=0.2,
            missing_kwds={"color": "lightgrey", "hatch": "///", "label": "No EUI data"},
        )
    else:
        gdf_web.plot(color="lightgrey", edgecolor="0.3", linewidth=0.2, ax=ax)

    if len(failed_gdf) > 0:
        failed_gdf.plot(color="grey", hatch="///", ax=ax, alpha=0.6)

    # Set extent to data bounds + 10% margin BEFORE add_basemap so zoom is sane
    bounds = gdf_web.total_bounds  # [minx, miny, maxx, maxy]
    x_margin = (bounds[2] - bounds[0]) * 0.10
    y_margin = (bounds[3] - bounds[1]) * 0.10
    ax.set_xlim(bounds[0] - x_margin, bounds[2] + x_margin)
    ax.set_ylim(bounds[1] - y_margin, bounds[3] + y_margin)

    # Basemap — graceful fallback; cap zoom to avoid out-of-range tiles
    basemap_ok = False
    try:
        import contextily as ctx  # noqa: PLC0415
        # Try progressively lower zooms if the auto-computed zoom is out of range
        for zoom in (None, 17, 16, 15, 14, 13):
            try:
                kwargs = {"source": ctx.providers.CartoDB.Positron}
                if zoom is not None:
                    kwargs["zoom"] = zoom
                ctx.add_basemap(ax, **kwargs)
                basemap_ok = True
                break
            except Exception:  # noqa: BLE001
                if zoom is None:
                    continue
                raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Basemap unavailable (%s); rendering footprints only", exc)

    failed_patch = mpatches.Patch(facecolor="grey", hatch="///", alpha=0.6, label="Failed/not simulated")
    ax.legend(handles=[failed_patch], loc="lower right", fontsize=8)

    title = f"{cell_name or 'Cell'} — Building Total EUI (kWh/m²/yr)"
    if not basemap_ok:
        title += "\n[basemap unavailable — footprints only]"
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T03a — EUI rank curve
# ---------------------------------------------------------------------------

def plot_eui_rank_curve(cell_gdf: gpd.GeoDataFrame, output_path: Path, cell_name: str = "") -> Path:
    """Buildings sorted ascending by EUI (rank on X), EUI on Y; median/IQR lines."""
    output_path = Path(output_path)

    success_mask = cell_gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    df = cell_gdf[success_mask][["total_eui_kwh_m2"]].dropna().copy()
    df_sorted = df.sort_values("total_eui_kwh_m2").reset_index(drop=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))

    if len(df_sorted) > 0:
        ax.plot(df_sorted.index, df_sorted["total_eui_kwh_m2"], color="#d62728", linewidth=0.8)

        median_val = float(df_sorted["total_eui_kwh_m2"].median())
        q25 = float(df_sorted["total_eui_kwh_m2"].quantile(0.25))
        q75 = float(df_sorted["total_eui_kwh_m2"].quantile(0.75))

        ax.axhline(median_val, color="navy", linestyle="--", linewidth=1.0, label=f"Median {median_val:.1f}")
        ax.axhspan(q25, q75, color="navy", alpha=0.08, label=f"IQR [{q25:.1f}, {q75:.1f}]")
    else:
        ax.text(0.5, 0.5, "No success data", transform=ax.transAxes, ha="center")

    ax.set_xlabel("Building rank (sorted by EUI)", fontsize=10)
    ax.set_ylabel("Total EUI (kWh/m²/yr)", fontsize=10)
    ax.set_title(f"{cell_name or 'Cell'} — EUI Rank Curve", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T03b — Archetype EUI sorted bar
# ---------------------------------------------------------------------------

def plot_archetype_eui_sorted_bar(cell_gdf: gpd.GeoDataFrame, output_path: Path, cell_name: str = "") -> Path:
    """Archetypes on X sorted by median EUI; mean ± std EUI on Y (success rows)."""
    output_path = Path(output_path)

    success_mask = cell_gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    df = cell_gdf[success_mask][["archetype_id", "total_eui_kwh_m2"]].dropna().copy()

    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    if len(df) > 0 and "archetype_id" in df.columns and df["archetype_id"].notna().any():
        stats = (
            df.groupby("archetype_id")["total_eui_kwh_m2"]
            .agg(median="median", mean="mean", std="std")
            .fillna(0)
            .sort_values("median")
            .reset_index()
        )
        x = np.arange(len(stats))
        ax.bar(x, stats["mean"], yerr=stats["std"], color="#ff7f0e", alpha=0.85,
               error_kw={"elinewidth": 1, "capsize": 3}, label="Mean ± std")
        ax.plot(x, stats["median"], "v", color="navy", markersize=5, label="Median", zorder=5)
        ax.set_xticks(x)
        ax.set_xticklabels(stats["archetype_id"].astype(str), rotation=45, ha="right", fontsize=7)
    else:
        ax.text(0.5, 0.5, "No archetype data", transform=ax.transAxes, ha="center")

    ax.set_xlabel("Archetype (sorted by median EUI)", fontsize=10)
    ax.set_ylabel("Mean EUI ± std (kWh/m²/yr)", fontsize=10)
    ax.set_title(f"{cell_name or 'Cell'} — EUI by Archetype (sorted by median EUI)", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T04 — Validation: simulated-vs-reference scatter
# ---------------------------------------------------------------------------

def plot_roundtrip_scatter(df: pd.DataFrame, output_path: Path) -> Path:
    """X=ref_total_eui, Y=counter_total_eui, 1:1 line, ±5% band, pass/fail color.
    Only rows where counter_status starts with 'success' are plotted/included in stats.
    DataCenter archetypes excluded (off-scale).
    """
    output_path = Path(output_path)

    # Filter to success rows only (DESIGN §3G: never invisible — excluded count noted in caption)
    if "counter_status" in df.columns:
        success_mask = df["counter_status"].astype(str).str.startswith("success")
        n_excluded = (~success_mask).sum()
        df = df[success_mask].copy()
    else:
        n_excluded = 0

    # Exclude DataCenter archetypes (off-scale, distorts axis)
    dc_mask = df["openuben_archetype"].astype(str).str.contains("DataCenter")
    n_dc = int(dc_mask.sum())
    df = df[~dc_mask].copy()

    fig, ax = plt.subplots(1, 1, figsize=(7, 7))

    pass_mask = df["verdict_5pct"].astype(str).str.lower().isin({"pass", "true", "1"})
    for mask, color, label in [(pass_mask, "green", "Pass"), (~pass_mask, "red", "Fail")]:
        subset = df[mask]
        if len(subset) > 0:
            ax.scatter(subset["ref_total_eui"], subset["counter_total_eui"],
                       c=color, label=label, s=60, alpha=0.8, zorder=3)
            for _, row in subset.iterrows():
                ax.annotate(str(row["openuben_archetype"])[:10],
                            (row["ref_total_eui"], row["counter_total_eui"]),
                            fontsize=6, ha="left", va="bottom")

    all_vals = pd.concat([df["ref_total_eui"], df["counter_total_eui"]]).dropna()
    if len(all_vals) > 0:
        lo, hi = all_vals.min() * 0.9, all_vals.max() * 1.1
        xs = np.linspace(lo, hi, 200)
        ax.plot(xs, xs, "k--", linewidth=1.0, label="1:1")
        ax.fill_between(xs, xs * 0.95, xs * 1.05, color="grey", alpha=0.15, label="±5% band")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)

    n_archetypes = len(df)
    med_dev = df["dev_pct"].abs().median() if "dev_pct" in df.columns else float("nan")
    ax.text(0.04, 0.96, f"Median |dev| ({n_archetypes} archetypes) = {med_dev:.1f}%",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.7})

    ax.set_xlabel("Reference Total EUI (kWh/m²/yr)", fontsize=10)
    ax.set_ylabel("Simulated Total EUI (kWh/m²/yr)", fontsize=10)
    ax.set_title("Simulated vs. Reference EUI (Level-2 Roundtrip)", fontsize=11)
    ax.legend(fontsize=8)
    ax.set_aspect("equal", adjustable="box")

    captions = []
    if n_dc > 0:
        captions.append("Data-centre archetype excluded (off-scale, +151%)")
    if n_excluded > 0:
        captions.append(f"{n_excluded} archetype(s) excluded: counterpart simulation failed")
    if captions:
        fig.text(0.5, 0.01, "  |  ".join(captions),
                 ha="center", fontsize=7, color="grey", style="italic")

    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T05 — Validation: ranked deviation bar
# ---------------------------------------------------------------------------

def plot_dev_ranked_bar(df: pd.DataFrame, output_path: Path) -> Path:
    """Archetypes sorted by dev_pct; bars pass=green / fail=red; ±5% lines.
    Only rows where counter_status starts with 'success' are included.
    DataCenter archetypes excluded for consistency with scatter plot.
    """
    output_path = Path(output_path)

    # Filter to success rows only (DESIGN §3G: never invisible — excluded count noted in caption)
    if "counter_status" in df.columns:
        success_mask = df["counter_status"].astype(str).str.startswith("success")
        n_excluded = (~success_mask).sum()
        df = df[success_mask].copy()
    else:
        n_excluded = 0

    # Exclude DataCenter archetypes for consistency with scatter plot
    dc_mask = df["openuben_archetype"].astype(str).str.contains("DataCenter")
    n_dc = int(dc_mask.sum())
    df = df[~dc_mask].copy()

    df_sorted = df.sort_values("dev_pct").reset_index(drop=True)
    pass_mask = df_sorted["verdict_5pct"].astype(str).str.lower().isin({"pass", "true", "1"})
    colors = ["green" if p else "red" for p in pass_mask]

    fig, ax = plt.subplots(1, 1, figsize=(max(8, len(df_sorted) * 0.5), 5))
    x = np.arange(len(df_sorted))
    ax.bar(x, df_sorted["dev_pct"], color=colors, alpha=0.85)
    ax.axhline(5, color="grey", linestyle="--", linewidth=0.8)
    ax.axhline(-5, color="grey", linestyle="--", linewidth=0.8, label="±5% gate")
    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted["openuben_archetype"].astype(str), rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Archetype (sorted by deviation)", fontsize=10)
    ax.set_ylabel("Deviation (%)", fontsize=10)
    ax.set_title("EUI Deviation from Reference — Ranked", fontsize=11)

    pass_patch = mpatches.Patch(color="green", label="Pass (|dev|≤5%)")
    fail_patch = mpatches.Patch(color="red", label="Fail")
    ax.legend(handles=[pass_patch, fail_patch], fontsize=8)

    captions = []
    if n_dc > 0:
        captions.append("Data-centre archetype excluded (off-scale, +151%)")
    if n_excluded > 0:
        captions.append(f"{n_excluded} archetype(s) excluded: counterpart simulation failed")
    if captions:
        fig.text(0.5, 0.01, "  |  ".join(captions),
                 ha="center", fontsize=7, color="grey", style="italic")

    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T06 — Validation: gap decomposition stacked bar
# ---------------------------------------------------------------------------

def plot_gap_decomposition(df: pd.DataFrame, output_path: Path) -> Path:
    """Stacked contribution bars per archetype; 'Other' visually emphasised."""
    output_path = Path(output_path)

    df_sorted = df.sort_values("dev_pct").reset_index(drop=True)
    contrib_cols = ["contrib_heat", "contrib_cool", "contrib_light", "contrib_equip", "contrib_other"]
    contrib_labels = ["Heating", "Cooling", "Lighting", "Equipment", "Other ★"]
    # Other gets a bold accent color
    contrib_colors = ["#d62728", "#1f77b4", "#ffdd57", "#2ca02c", "#9467bd"]

    fig, ax = plt.subplots(1, 1, figsize=(max(8, len(df_sorted) * 0.5), 5))
    x = np.arange(len(df_sorted))
    bottoms = np.zeros(len(df_sorted))

    for col, label, color in zip(contrib_cols, contrib_labels, contrib_colors):
        if col in df_sorted.columns:
            vals = df_sorted[col].fillna(0).values
            ax.bar(x, vals, bottom=bottoms, label=label, color=color, alpha=0.9)
            bottoms += vals

    ax.set_xticks(x)
    ax.set_xticklabels(df_sorted["openuben_archetype"].astype(str), rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Archetype (sorted by dev_pct)", fontsize=10)
    ax.set_ylabel("Contribution to EUI gap (kWh/m²/yr)", fontsize=10)
    ax.set_title("Gap Decomposition by End Use  [★ Other ≈ 42% of median gap]", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T07 — Validation: climate-signal grouped bar
# ---------------------------------------------------------------------------

def plot_climate_signal(cell_stats: pd.DataFrame, output_path: Path) -> Path:
    """Grouped bars: mean heating EUI and cooling EUI per city×ring (12 cells).
    cell_stats must have columns: cell, city, ring, mean_heating_eui, mean_cooling_eui.
    """
    output_path = Path(output_path)

    cities = cell_stats["city"].unique()
    rings = ["centre", "urban", "suburban", "rural"]
    x = np.arange(len(rings))
    width = 0.8 / max(len(cities), 1)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    city_colors = plt.cm.tab10(np.linspace(0, 0.6, len(cities)))

    for ax, metric, title in zip(
        axes,
        ["mean_heating_eui", "mean_cooling_eui"],
        ["Mean Heating EUI (kWh/m²/yr)", "Mean Cooling EUI (kWh/m²/yr)"],
    ):
        for i, (city, color) in enumerate(zip(cities, city_colors)):
            city_df = cell_stats[cell_stats["city"] == city].copy()
            city_df = city_df.set_index("ring").reindex(rings)
            offset = (i - len(cities) / 2 + 0.5) * width
            ax.bar(x + offset, city_df[metric].fillna(0).values, width=width * 0.9,
                   label=city, color=color, alpha=0.85)

        ax.set_xticks(x)
        ax.set_xticklabels(rings, fontsize=9)
        ax.set_xlabel("Ring", fontsize=10)
        ax.set_ylabel(title, fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8)

    fig.suptitle("Climate Signal: Heating vs. Cooling EUI by City and Ring", fontsize=12)
    fig.tight_layout()

    return _save(fig, output_path)


# ---------------------------------------------------------------------------
# T12 — Combined 12-cell overview grid
# ---------------------------------------------------------------------------

_CITIES = ["nyc", "la", "austin"]
_RINGS = ["centre", "urban", "suburban", "rural"]


def plot_overview_grid(output_path: Path | None = None) -> tuple[Path, float, float]:
    """3×4 small-multiples grid of EUI footprint maps for all 12 cells.

    Rows = cities (nyc, la, austin); cols = rings (centre, urban, suburban, rural).
    Shared color scale (2nd–98th pct of total_eui_kwh_m2 across all success buildings).
    Single shared colorbar. No basemap (footprints on white for fast/clean small multiples).

    Returns (output_path, vmin, vmax).
    """
    if output_path is None:
        output_path = COMPARE_DIR / "eui_overview_grid.png"
    output_path = Path(output_path)

    cells = [f"{city}_{ring}" for city in _CITIES for ring in _RINGS]

    # Pass 1: load all available cells; pool EUI values for shared scale
    cell_gdfs: dict[str, gpd.GeoDataFrame | None] = {}
    all_eui: list[float] = []

    for cell in cells:
        try:
            gdf = _load_cell_footprints(cell)
            success_mask = gdf["simulation_status"].isin(_SUCCESS_STATUSES)
            eui_vals = gdf.loc[success_mask, "total_eui_kwh_m2"].dropna().tolist()
            all_eui.extend(eui_vals)
            cell_gdfs[cell] = gdf
        except FileNotFoundError:
            cell_gdfs[cell] = None

    if all_eui:
        vmin = float(np.percentile(all_eui, 2))
        vmax = float(np.percentile(all_eui, 98))
    else:
        vmin, vmax = 0.0, 1.0  # fallback: all cells blank

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["YlOrRd"]

    fig, axes = plt.subplots(3, 4, figsize=(16, 12))

    n_data = 0
    n_blank = 0

    for row_idx, city in enumerate(_CITIES):
        for col_idx, ring in enumerate(_RINGS):
            cell = f"{city}_{ring}"
            ax = axes[row_idx][col_idx]
            gdf = cell_gdfs.get(cell)

            if gdf is None:
                ax.set_facecolor("white")
                ax.text(0.5, 0.5, f"{cell}\nno data",
                        transform=ax.transAxes, ha="center", va="center",
                        fontsize=8, color="grey")
                ax.set_axis_off()
                ax.set_title(cell, fontsize=8)
                n_blank += 1
                continue

            # Reproject to EPSG:3857 per panel (no basemap — footprints on white)
            try:
                gdf_web = gdf.to_crs(epsg=3857)
            except Exception:
                gdf_web = gdf

            success_mask = gdf_web["simulation_status"].isin(_SUCCESS_STATUSES)
            success_gdf = gdf_web[success_mask].copy()
            failed_gdf = gdf_web[~success_mask].copy()

            if len(success_gdf) > 0 and success_gdf["total_eui_kwh_m2"].notna().any():
                success_gdf.plot(
                    column="total_eui_kwh_m2",
                    cmap=cmap,
                    norm=norm,
                    ax=ax,
                    edgecolor="0.3",
                    linewidth=0.2,
                    legend=False,
                    missing_kwds={"color": "lightgrey"},
                )
            else:
                gdf_web.plot(color="lightgrey", edgecolor="0.3", linewidth=0.2, ax=ax)

            if len(failed_gdf) > 0:
                failed_gdf.plot(color="grey", hatch="///", ax=ax, alpha=0.5)

            # Set extent before basemap so zoom is sane
            panel_bounds = gdf_web.total_bounds
            px_margin = (panel_bounds[2] - panel_bounds[0]) * 0.10
            py_margin = (panel_bounds[3] - panel_bounds[1]) * 0.10
            ax.set_xlim(panel_bounds[0] - px_margin, panel_bounds[2] + px_margin)
            ax.set_ylim(panel_bounds[1] - py_margin, panel_bounds[3] + py_margin)

            try:
                import contextily as ctx  # noqa: PLC0415
                for zoom in (None, 17, 16, 15, 14, 13):
                    try:
                        kwargs = {"source": ctx.providers.CartoDB.Positron}
                        if zoom is not None:
                            kwargs["zoom"] = zoom
                        ctx.add_basemap(ax, **kwargs)
                        break
                    except Exception:  # noqa: BLE001
                        if zoom is None:
                            continue
                        raise
            except Exception as exc:  # noqa: BLE001
                logger.warning("Basemap unavailable for %s (%s); footprints only", cell, exc)

            ax.set_axis_off()
            ax.set_title(cell, fontsize=8, pad=3)
            n_data += 1

    # Single shared colorbar for the whole figure
    sm = mcm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, fraction=0.015, pad=0.02, shrink=0.6)
    cbar.set_label("Total EUI (kWh/m²/yr)", fontsize=10)

    fig.suptitle(
        f"OpenUBEM — EUI Overview (all 12 cells)  "
        f"[scale: {vmin:.0f}–{vmax:.0f} kWh/m²/yr, 2nd–98th pct]",
        fontsize=12, y=1.01,
    )

    return _save(fig, output_path), vmin, vmax


# ---------------------------------------------------------------------------
# Comparison helpers + Plot A/B/C
# ---------------------------------------------------------------------------

_CBECS_DIR = _BASE / "inputs" / "reports"
_CITY_TO_REGION = {"nyc": "middle_atlantic", "la": "pacific", "austin": "west_south_central"}
_R7_CSV = _BASE / "docs" / "docs_VALIDATION" / "step1" / "overAll" / "results" / "r7_service_loads.csv"


def _build_comparison_df() -> pd.DataFrame:
    """Load per-building data for comparison plots A/B/C.

    Default (no OPENUBEM_PHASED_SUBDIR): reads _R7_CSV unchanged.
    With env var set: reads all 12 cells from the phased tree, derives the city
    column from the cell name, and applies regional reconstruction so
    total_eui_reconstructed_kwh_m2 / reconstruction_applied are present.
    """
    phased = _phased_subdir()
    if not phased:
        return pd.read_csv(_R7_CSV)

    from openubem.results.service_loads import load_coefficients, reconstruct_frame  # noqa: PLC0415
    import geopandas as gpd  # already imported at top; re-import inside for clarity  # noqa: PLC0415

    _coeffs = load_coefficients(_REGIONAL_COEFFS_PATH)
    phased_base = _PHASED_BASE / phased
    frames = []
    for city in _CITIES:
        for ring in _RINGS:
            cell = f"{city}_{ring}"
            gpkg = phased_base / cell / "05_results.gpkg"
            if not gpkg.exists():
                logger.warning("phased gpkg absent for %s: %s", cell, gpkg)
                continue
            gdf = gpd.read_file(str(gpkg))
            df = pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))
            df["cell"] = cell
            if "city" not in df.columns:
                df["city"] = city
            df = reconstruct_frame(df, _coeffs, region_col="city")
            frames.append(df)

    if not frames:
        raise FileNotFoundError(f"No phased cells found under {phased_base}")
    return pd.concat(frames, ignore_index=True)


def _cbecs_region_mean(region: str) -> float:
    """Weighted-mean site EUI (kWh/m²·yr) from CBECS-2018 region CSV."""
    p = _CBECS_DIR / f"cbecs_2018_{region}_eui.csv"
    df = pd.read_csv(p)
    return float(np.average(df["eui_kwh_m2"], weights=df["finalwt"]))


def plot_eui_vs_reference(output_path: Path | None = None) -> Path:
    """Plot A — per-cell modeled mean EUI vs region-correct CBECS-2018 reference.

    Saves to COMPARE_DIR/eui_vs_cbecs_reference.png by default.
    """
    if output_path is None:
        output_path = COMPARE_DIR / "eui_vs_cbecs_reference.png"
    output_path = Path(output_path)

    df = _build_comparison_df()
    df = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()

    cell_order = [f"{c}_{r}" for c in _CITIES for r in _RINGS]
    modeled = df.groupby("cell")["total_eui_kwh_m2"].mean().reindex(cell_order)

    refs = {}
    for city in _CITIES:
        region = _CITY_TO_REGION[city]
        mean_ref = _cbecs_region_mean(region)
        for ring in _RINGS:
            refs[f"{city}_{ring}"] = mean_ref
    ref_series = pd.Series(refs).reindex(cell_order)

    dev_pct = (modeled - ref_series) / ref_series * 100

    x = np.arange(len(cell_order))
    width = 0.35
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width / 2, modeled.fillna(0).values, width, label="Modeled mean", color="#d62728", alpha=0.85)
    ax.bar(x + width / 2, ref_series.values, width, label="CBECS-2018 region ref", color="#1f77b4", alpha=0.85)

    for i, (cell, dev) in enumerate(zip(cell_order, dev_pct)):
        if not np.isnan(dev):
            ax.text(i, max(modeled.iloc[i], ref_series.iloc[i]) + 3,
                    f"{dev:+.0f}%", ha="center", va="bottom", fontsize=6)

    ax.set_xticks(x)
    ax.set_xticklabels(cell_order, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Site EUI (kWh/m²/yr)", fontsize=10)
    ax.set_title("OpenUBEM — Modeled EUI vs CBECS-2018 region reference (per cell)", fontsize=11)
    ax.legend(fontsize=9)
    fig.text(0.5, -0.02,
             "Reference = region weighted-mean: NYC=Mid-Atlantic, LA=Pacific, Austin=W-S-Central",
             ha="center", fontsize=8, color="grey", style="italic")
    fig.tight_layout()

    return _save(fig, output_path)


def plot_sim_vs_reconstructed(output_path: Path | None = None) -> Path:
    """Plot B — simulated vs service-load-reconstructed EUI per cell.

    Saves to COMPARE_DIR/eui_sim_vs_reconstructed.png by default.
    """
    if output_path is None:
        output_path = COMPARE_DIR / "eui_sim_vs_reconstructed.png"
    output_path = Path(output_path)

    df = _build_comparison_df()
    df = df[df["reconstruction_applied"] == True].copy()  # noqa: E712

    cell_order = [f"{c}_{r}" for c in _CITIES for r in _RINGS]
    sim_mean = df.groupby("cell")["total_eui_kwh_m2"].mean().reindex(cell_order)
    recon_mean = df.groupby("cell")["total_eui_reconstructed_kwh_m2"].mean().reindex(cell_order)
    uplift_pct = (recon_mean - sim_mean) / sim_mean * 100

    x = np.arange(len(cell_order))
    width = 0.35
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - width / 2, sim_mean.fillna(0).values, width, label="Simulated", color="#1f77b4", alpha=0.85)
    ax.bar(x + width / 2, recon_mean.fillna(0).values, width, label="Reconstructed", color="#ff7f0e", alpha=0.85)

    for i, (cell, up) in enumerate(zip(cell_order, uplift_pct)):
        if not np.isnan(up):
            ax.text(i, max(sim_mean.iloc[i], recon_mean.iloc[i]) + 3,
                    f"+{up:.0f}%", ha="center", va="bottom", fontsize=6)

    ax.set_xticks(x)
    ax.set_xticklabels(cell_order, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Mean EUI (kWh/m²/yr)", fontsize=10)
    ax.set_title("OpenUBEM — Simulated vs Service-Load-Reconstructed EUI (per cell)", fontsize=11)
    ax.legend(fontsize=9)
    fig.text(0.5, -0.02,
             "Food-service uplift ~+203% inflates cells with QSR/restaurants; see V16 §4",
             ha="center", fontsize=8, color="grey", style="italic")
    fig.tight_layout()

    return _save(fig, output_path)


def plot_cross_cell_eui(output_path: Path | None = None) -> Path:
    """Plot C — building EUI distributions across all 12 cells, ranked by median.

    Saves to COMPARE_DIR/eui_cross_cell_summary.png by default.
    """
    if output_path is None:
        output_path = COMPARE_DIR / "eui_cross_cell_summary.png"
    output_path = Path(output_path)

    df = _build_comparison_df()
    df = df[df["simulation_status"].isin(_SUCCESS_STATUSES)].copy()

    cell_order = [f"{c}_{r}" for c in _CITIES for r in _RINGS]
    groups = [df.loc[df["cell"] == cell, "total_eui_kwh_m2"].dropna().values for cell in cell_order]

    medians = [float(np.median(g)) if len(g) > 0 else 0.0 for g in groups]
    sorted_idx = np.argsort(medians)
    sorted_cells = [cell_order[i] for i in sorted_idx]
    sorted_groups = [groups[i] for i in sorted_idx]
    sorted_medians = [medians[i] for i in sorted_idx]

    y_cap = float(np.percentile(df["total_eui_kwh_m2"].dropna(), 99))

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.boxplot(sorted_groups, positions=np.arange(len(sorted_cells)), showfliers=False,
               patch_artist=True,
               boxprops={"facecolor": "#aec7e8", "alpha": 0.8},
               medianprops={"color": "navy", "linewidth": 1.5})

    for i, med in enumerate(sorted_medians):
        ax.text(i, med + 1, f"{med:.0f}", ha="center", va="bottom", fontsize=6)

    ax.set_xticks(np.arange(len(sorted_cells)))
    ax.set_xticklabels(sorted_cells, rotation=45, ha="right", fontsize=8)
    ax.set_ylim(bottom=0, top=y_cap)
    ax.set_ylabel("Total EUI (kWh/m²/yr)", fontsize=10)
    ax.set_title("OpenUBEM — Building EUI distribution by cell (ranked by median)", fontsize=11)
    fig.tight_layout()

    return _save(fig, output_path)
