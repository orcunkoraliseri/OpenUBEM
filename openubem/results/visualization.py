"""Step-5 Module 16: observability-only figures (DESIGN §3G, F11). Non-binding artifacts."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless-safe backend (plan §2)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import geopandas as gpd
import pandas as pd


_FAILED_STATUSES = {"failed_parse", "failed_zone_mismatch", "not_simulated"}
_SUCCESS_STATUSES = {"success", "success_cached", "success_csv_fallback"}


def _is_failed(status: str) -> bool:
    return str(status) in _FAILED_STATUSES


def plot_eui_choropleth(
    results_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> Path:
    """EUI choropleth: success buildings coloured by total_eui_kwh_m2;
    failed buildings hatched grey (never invisible per DESIGN §3G).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    success_mask = results_gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    failed_mask = ~success_mask

    success_gdf = results_gdf[success_mask].copy()
    failed_gdf = results_gdf[failed_mask].copy()

    if len(success_gdf) > 0 and success_gdf["total_eui_kwh_m2"].notna().any():
        success_gdf.plot(
            column="total_eui_kwh_m2",
            cmap="YlOrRd",
            legend=True,
            legend_kwds={"label": "Total EUI (kWh/m²/yr)", "shrink": 0.6},
            ax=ax,
            missing_kwds={"color": "lightgrey", "hatch": "///", "label": "No EUI data"},
        )
    else:
        results_gdf.plot(color="lightgrey", ax=ax)

    # Failed buildings: hatched grey overlay
    if len(failed_gdf) > 0:
        failed_gdf.plot(color="grey", hatch="///", ax=ax, alpha=0.6)

    failed_patch = mpatches.Patch(facecolor="grey", hatch="///", alpha=0.6, label="Failed/not simulated")
    ax.legend(handles=[failed_patch], loc="lower right", fontsize=8)
    ax.set_title("Building Total EUI (kWh/m²/yr)", fontsize=12)
    ax.set_axis_off()

    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_eui_violin_by_archetype(
    results_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> Path:
    """Per-archetype EUI violin plots (success rows only)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success_mask = results_gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    df = results_gdf[success_mask].copy()
    df = df[df["total_eui_kwh_m2"].notna()].copy()

    archetype_col = "archetype_id" if "archetype_id" in df.columns else None
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    if archetype_col and len(df) > 0 and df[archetype_col].notna().any():
        archetypes = sorted(df[archetype_col].dropna().unique())
        data_by_arch = [df[df[archetype_col] == a]["total_eui_kwh_m2"].dropna().values for a in archetypes]
        data_by_arch = [d for d in data_by_arch if len(d) > 0]
        archetypes_with_data = [a for a, d in zip(archetypes, [df[df[archetype_col] == a]["total_eui_kwh_m2"].dropna().values for a in archetypes]) if len(d) > 0]
        if data_by_arch:
            ax.violinplot(data_by_arch, positions=range(len(archetypes_with_data)), showmedians=True)
            ax.set_xticks(range(len(archetypes_with_data)))
            ax.set_xticklabels([str(a) for a in archetypes_with_data], rotation=45, ha="right", fontsize=8)
        else:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
    else:
        eui_vals = df["total_eui_kwh_m2"].dropna().values
        if len(eui_vals) > 0:
            ax.violinplot([eui_vals], showmedians=True)
            ax.set_xticks([1])
            ax.set_xticklabels(["All"])
        else:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")

    ax.set_ylabel("Total EUI (kWh/m²/yr)")
    ax.set_title("EUI Distribution by Archetype")
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_gwp_stacked_by_archetype(
    results_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> Path:
    """Per-end-use GWP stacked bar by archetype (success rows, mean intensity)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success_mask = results_gdf["simulation_status"].isin(_SUCCESS_STATUSES)
    df = results_gdf[success_mask].copy()

    gwp_cols = [
        ("gwp_heating_kgco2_m2", "Heating (gas)"),
        ("gwp_cooling_kgco2_m2", "Cooling (elec)"),
        ("gwp_lighting_kgco2_m2", "Lighting (elec)"),
        ("gwp_equipment_kgco2_m2", "Equipment (elec)"),
    ]
    gwp_cols_present = [(c, lbl) for c, lbl in gwp_cols if c in df.columns]

    archetype_col = "archetype_id" if "archetype_id" in df.columns else None
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    colors = ["#d62728", "#1f77b4", "#ffdd57", "#2ca02c"]

    if archetype_col and len(df) > 0 and df[archetype_col].notna().any():
        archetypes = sorted(df[archetype_col].dropna().unique())
        x = np.arange(len(archetypes))
        bottoms = np.zeros(len(archetypes))
        for (col, label), color in zip(gwp_cols_present, colors):
            means = [float(df[df[archetype_col] == a][col].mean()) if df[df[archetype_col] == a][col].notna().any() else 0.0 for a in archetypes]
            ax.bar(x, means, bottom=bottoms, label=label, color=color)
            bottoms += np.array(means)
        ax.set_xticks(x)
        ax.set_xticklabels([str(a) for a in archetypes], rotation=45, ha="right", fontsize=8)
    else:
        means = []
        for col, label in gwp_cols_present:
            means.append(float(df[col].mean()) if len(df) > 0 and df[col].notna().any() else 0.0)
        bottom = 0.0
        for (col, label), mean_val, color in zip(gwp_cols_present, means, colors):
            ax.bar([0], [mean_val], bottom=bottom, label=label, color=color)
            bottom += mean_val
        ax.set_xticks([0])
        ax.set_xticklabels(["All"])

    ax.set_ylabel("Mean GWP (kg CO₂e/m²/yr)")
    ax.set_title("GWP by End Use and Archetype")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def render_all_figures(
    results_gdf: gpd.GeoDataFrame,
    figures_dir: Path,
) -> dict[str, Path]:
    """Render all three observability figures; return dict of paths."""
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    paths["eui_choropleth"] = plot_eui_choropleth(
        results_gdf, figures_dir / "eui_choropleth.png"
    )
    paths["eui_violin_by_archetype"] = plot_eui_violin_by_archetype(
        results_gdf, figures_dir / "eui_violin_by_archetype.png"
    )
    paths["gwp_stacked_by_archetype"] = plot_gwp_stacked_by_archetype(
        results_gdf, figures_dir / "gwp_stacked_by_archetype.png"
    )
    return paths
