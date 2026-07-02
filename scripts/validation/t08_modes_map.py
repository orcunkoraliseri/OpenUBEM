"""T08 per-resolution-mode spatial EUI comparison maps.

For each of nyc_centre / la_centre / austin_centre, render a 1x4 panel
(columns = resolution modes [auto, building, floor, fast_zone]) of the same
building footprints coloured by that mode's total site EUI on a shared colour
scale over a CartoDB.Positron basemap.

Reuses the _add_basemap approach from phaseE_overview_grid.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MODES = ["auto", "building", "floor", "fast_zone"]
CELLS = ["nyc_centre", "la_centre", "austin_centre"]

FP_PHASEE = REPO / "docs/docs_VALIDATION/validations/overAll/results/phaseE"
FP_STEP1  = REPO / "docs/docs_VALIDATION/step1/overAll/results/cases"
EUI_ALL   = REPO / "openubem/outputs/comparisons/t08_all_modes_eui.csv"
EUI_LOCAL = REPO / "openubem/outputs/comparisons/t08_local_remainder_eui.csv"
OUT_DIR   = REPO / "openubem/outputs/comparisons"


def _footprint_path(cell: str) -> tuple[Path, str]:
    p1 = FP_PHASEE / cell / "01_buildings.gpkg"
    if p1.exists():
        return p1, "phaseE/01_buildings.gpkg"
    p2 = FP_STEP1 / cell / "05_results.gpkg"
    if p2.exists():
        return p2, "step1/05_results.gpkg"
    raise FileNotFoundError(f"No footprint source for {cell}")


def _load_eui(cell: str) -> pd.DataFrame:
    """Return the mode/osm_id/total_eui rows for a cell from whichever CSV holds it."""
    frames = []
    for csv in (EUI_ALL, EUI_LOCAL):
        df = pd.read_csv(csv, usecols=lambda c: c in
                         {"cell", "mode", "osm_id", "total_eui", "status"})
        frames.append(df[df["cell"] == cell])
    out = pd.concat(frames, ignore_index=True)
    return out


def _add_basemap(ax, cell: str) -> None:
    """Add CartoDB.Positron basemap with zoom fallback; warn on failure."""
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
        print(f"  WARNING: basemap unavailable for {cell} ({exc}); footprints only")


def render_cell(cell: str) -> None:
    print(f"\n=== {cell} ===")
    fp_path, fp_src = _footprint_path(cell)
    fp = gpd.read_file(str(fp_path))
    fp = fp[["osm_id", "geometry"]].copy()
    fp_web = fp.to_crs(epsg=3857)
    n_fp = len(fp_web)
    print(f"  footprint source : {fp_src}")
    print(f"  footprint count  : {n_fp}")

    eui = _load_eui(cell)

    # Per-mode joined GeoDataFrames + pooled EUI for shared scale
    per_mode: dict[str, gpd.GeoDataFrame] = {}
    pooled: list[np.ndarray] = []
    match_stats: dict[str, tuple[int, float, float]] = {}
    for mode in MODES:
        sub = eui[eui["mode"] == mode][["osm_id", "total_eui"]]
        # collapse potential duplicate osm_id rows within a mode
        sub = sub.dropna(subset=["osm_id"]).drop_duplicates(subset=["osm_id"])
        g = fp_web.merge(sub, on="osm_id", how="left")
        per_mode[mode] = g
        matched = g["total_eui"].notna().sum()
        pct = 100.0 * matched / n_fp if n_fp else 0.0
        med = float(g["total_eui"].median()) if matched else float("nan")
        match_stats[mode] = (int(matched), pct, med)
        pooled.append(g["total_eui"].dropna().values)
        print(f"  mode {mode:10s} matched={matched:4d}/{n_fp} ({pct:5.1f}%)  median_eui={med:7.1f}")
        if pct < 80.0:
            print(f"    [!] LOW JOIN HIT RATE for {cell}/{mode}: {pct:.1f}% < 80%")

    all_eui = np.concatenate([p for p in pooled if p.size])
    vmin = float(np.percentile(all_eui, 2))
    vmax = float(np.percentile(all_eui, 98))
    print(f"  shared scale (2nd-98th pct pooled): {vmin:.1f} - {vmax:.1f} kWh/m2/yr")

    cmap = plt.cm.YlOrRd
    norm = plt.Normalize(vmin=vmin, vmax=vmax)

    # Shared spatial extent from footprints + 10% margin
    b = fp_web.total_bounds
    mx = (b[2] - b[0]) * 0.10
    my = (b[3] - b[1]) * 0.10
    xlim = (b[0] - mx, b[2] + mx)
    ylim = (b[1] - my, b[3] + my)

    fig, axes = plt.subplots(1, 4, figsize=(24, 7))
    fig.suptitle(
        f"{cell} — Building Total EUI by resolution mode (kWh/m²/yr) "
        f"[shared scale: {vmin:.0f}-{vmax:.0f}, 2nd-98th pct]",
        fontsize=14, y=1.02,
    )

    for ax, mode in zip(axes, MODES):
        g = per_mode[mode]
        ok = g["total_eui"].notna()
        if (~ok).any():
            g[~ok].plot(ax=ax, color="lightgrey", linewidth=0.2, edgecolor="0.3")
        if ok.any():
            g[ok].plot(ax=ax, column="total_eui", cmap=cmap, norm=norm,
                       linewidth=0.2, edgecolor="0.3", legend=False)
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        _add_basemap(ax, cell)
        ax.set_title(mode, fontsize=12, fontweight="bold", pad=8)
        ax.set_axis_off()

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, fraction=0.012, pad=0.02, shrink=0.75)
    cbar.set_label("Total EUI (kWh/m²/yr)", fontsize=10)

    fig.text(0.5, 0.02, "unmatched / not simulated → grey",
             ha="center", fontsize=9, color="0.3")

    out = OUT_DIR / f"t08_modes_map_{cell}.png"
    fig.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close(fig)

    size_kb = out.stat().st_size / 1024
    assert out.exists(), f"FAIL: figure not written for {cell}"
    assert size_kb > 100, f"FAIL {cell}: figure only {size_kb:.0f} KB"
    print(f"  saved -> {out}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cell in CELLS:
        render_cell(cell)
    print("\nDone.")
