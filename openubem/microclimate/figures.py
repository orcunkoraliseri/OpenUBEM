"""T21 - figures (PLAN §7 T21).

Three deliverables: the 5-panel composite (four drivers + UTCI, same product shape as the
reference figure `1784462193769.jpg`), a diurnal UTCI curve at selected points, and a
stress-class area histogram. Every figure's caption states cell, date/hour, grid resolution,
vegetation tier, wall-temperature tier, and wind tier (plan §7 T21 "How": "A figure that does
not say what tier produced it is not auditable") -- required_caption() is the single place that
string gets built, so every figure function uses the identical format.

The UTCI panel/histogram always use the OFFICIAL 10-class discrete palette (T07's UTCI_CLASSES),
never a continuous colour ramp -- the classes are the physiological content (§6).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from openubem.microclimate.utci import UTCI_CLASSES, UTCI_NODATA_CLASS, classify_stress


def required_caption(*, cell: str, date_hour: str, res_m: float, vegetation_tier: str,
                      wall_temp_tier: str, wind_tier: str) -> str:
    """The one caption format every figure in this module uses (module docstring)."""
    return (
        f"{cell} | {date_hour} | res={res_m} m | vegetation_tier={vegetation_tier} | "
        f"wall_temp_tier={wall_temp_tier} | wind_tier={wind_tier}"
    )


def _mask_interior(arr, building_mask):
    out = np.asarray(arr, dtype=np.float64).copy()
    out = np.broadcast_to(out, building_mask.shape).copy()
    out[building_mask] = np.nan
    return out


def _utci_cmap_norm():
    cmap = mcolors.ListedColormap([c["hex"] for c in UTCI_CLASSES])
    bounds = list(range(len(UTCI_CLASSES) + 1))
    norm = mcolors.BoundaryNorm(bounds, cmap.N)
    return cmap, norm, bounds


def plot_five_panel(*, ta_c, e_kpa, v_1p1, tmrt_c, utci_c, domain, caption, out_path) -> Path:
    """Ta, e, v(1.1m), Tmrt (continuous ramps) + UTCI (10-class discrete) -- the reference
    figure's own layout. Building interiors -> NaN (unfilled/white in the plotted panel)."""
    mask = domain.building_mask
    panels = [
        (_mask_interior(ta_c, mask), "Ta [degC]", "inferno"),
        (_mask_interior(e_kpa, mask), "Vapour pressure e [kPa]", "viridis"),
        (_mask_interior(v_1p1, mask), "v(1.1m) [m/s]", "cividis"),
        (_mask_interior(tmrt_c, mask), "Tmrt [degC]", "inferno"),
    ]
    fig, axes = plt.subplots(1, 5, figsize=(24, 5.2))
    for ax, (arr, title, cmap) in zip(axes[:4], panels):
        im = ax.imshow(arr, cmap=cmap)
        ax.set_title(title)
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax = axes[4]
    classified = classify_stress(_mask_interior(utci_c, mask))
    plot_arr = np.where(classified == UTCI_NODATA_CLASS, np.nan, classified)
    cmap, norm, bounds = _utci_cmap_norm()
    im = ax.imshow(plot_arr, cmap=cmap, norm=norm)
    ax.set_title("UTCI stress class")
    ax.axis("off")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, ticks=[b + 0.5 for b in bounds[:-1]])
    cbar.ax.set_yticklabels([c["label"] for c in UTCI_CLASSES], fontsize=6)

    fig.suptitle(caption, fontsize=10)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_diurnal_curve(*, utci_stack_c, timestamps, points_rc: dict, caption, out_path) -> Path:
    """UTCI trajectory across the analysis window at named raster points.
    points_rc: {label: (row, col)}."""
    stack = np.asarray(utci_stack_c)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(timestamps))
    for label, (r, c) in points_rc.items():
        ax.plot(x, stack[:, r, c], marker="o", label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(t) for t in timestamps], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("UTCI [degC]")
    ax.legend(fontsize=8)
    ax.set_title(caption, fontsize=9)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def plot_stress_histogram(*, utci_c, domain, res_m: float, caption, out_path) -> Path:
    """Area [m^2] per UTCI stress class, outside building footprints, on the 10-class palette."""
    mask = domain.building_mask
    classified = classify_stress(_mask_interior(utci_c, mask))
    valid = classified[classified != UTCI_NODATA_CLASS]
    areas_m2 = np.array([(valid == c["index"]).sum() for c in UTCI_CLASSES], dtype=np.float64) * (res_m ** 2)
    colors = [c["hex"] for c in UTCI_CLASSES]
    labels = [c["label"] for c in UTCI_CLASSES]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(UTCI_CLASSES)), areas_m2, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(len(UTCI_CLASSES)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Area [m^2]")
    ax.set_title(caption, fontsize=9)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path
