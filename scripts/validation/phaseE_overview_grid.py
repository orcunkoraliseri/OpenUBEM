"""Phase-E overview-grid footprint map.

T01: Re-fetch and persist 01_buildings.gpkg for all 12 phaseE cells.
T02: Build per-cell map GDFs (footprint polygons + phaseE EUI).
T03: Render 3-row × 4-col overview-grid figure.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

CELL_CONFIGS: dict[str, dict] = {
    "nyc_centre":      {"lat": 40.7549, "lon": -73.9840, "radius_m":  500.0, "epsg": 32618},
    "nyc_urban":       {"lat": 40.7721, "lon": -73.9301, "radius_m":  500.0, "epsg": 32618},
    "nyc_suburban":    {"lat": 40.7052, "lon": -73.5985, "radius_m":  500.0, "epsg": 32618},
    "nyc_rural":       {"lat": 42.0396, "lon": -74.1143, "radius_m": 1000.0, "epsg": 32618},
    "la_centre":       {"lat": 34.0522, "lon": -118.2437, "radius_m":  500.0, "epsg": 32611},
    "la_urban":        {"lat": 34.0584, "lon": -118.3040, "radius_m":  500.0, "epsg": 32611},
    "la_suburban":     {"lat": 33.8359, "lon": -118.3406, "radius_m":  500.0, "epsg": 32611},
    "la_rural":        {"lat": 34.7420, "lon": -118.2130, "radius_m": 1500.0, "epsg": 32611},
    "austin_centre":   {"lat": 30.2672, "lon": -97.7431, "radius_m":  500.0, "epsg": 32614},
    "austin_urban":    {"lat": 30.3072, "lon": -97.7400, "radius_m":  500.0, "epsg": 32614},
    "austin_suburban": {"lat": 30.5085, "lon": -97.6789, "radius_m":  500.0, "epsg": 32614},
    "austin_rural":    {"lat": 30.5788, "lon": -98.2700, "radius_m": 1000.0, "epsg": 32614},
}

RESULTS_BASE = REPO / "docs/docs_VALIDATION/validations/overAll/results/phaseE"
OUTPUTS_DIR  = REPO / "openubem/outputs"

CITIES = ["nyc", "la", "austin"]
RINGS  = ["centre", "urban", "suburban", "rural"]
CITY_LABELS = {"nyc": "NYC", "la": "LA", "austin": "Austin"}
RING_LABELS = {"centre": "Centre", "urban": "Urban", "suburban": "Suburban", "rural": "Rural"}


# ─── T01 ────────────────────────────────────────────────────────────────────

def t01_persist_footprints() -> dict[str, Path]:
    """Re-fetch OSM polygon footprints and persist to results tree."""
    from openubem.acquisition.osm_fetcher import ingest_buildings

    paths: dict[str, Path] = {}
    for cell, cfg in CELL_CONFIGS.items():
        dest = RESULTS_BASE / cell / "01_buildings.gpkg"
        if dest.exists():
            print(f"  {cell}: cached, skipping fetch")
        else:
            print(f"  {cell}: fetching ({cfg['lat']}, {cfg['lon']}) r={cfg['radius_m']}m ...")
            gdf = ingest_buildings(location=(cfg["lat"], cfg["lon"]),
                                   radius_m=cfg["radius_m"])
            print(f"    -> {len(gdf)} buildings, CRS={gdf.crs}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            gdf.to_file(str(dest), driver="GPKG")
            print(f"    saved {dest}")

        # Assertions
        gdf_chk = gpd.read_file(str(dest))
        assert len(gdf_chk) > 0, f"FAIL {cell}: empty gpkg"
        assert "osm_id" in gdf_chk.columns, f"FAIL {cell}: no osm_id"
        geom_types = set(gdf_chk.geometry.geom_type.unique())
        assert geom_types <= {"Polygon", "MultiPolygon"}, \
            f"FAIL {cell}: unexpected geom types {geom_types}"
        print(f"  [OK] {cell}: {len(gdf_chk)} polygons, CRS={gdf_chk.crs}")
        paths[cell] = dest

    assert len(paths) == 12, "FAIL: expected 12 footprint files"
    return paths


# ─── T02 ────────────────────────────────────────────────────────────────────

def t02_build_map_gdfs(fp_paths: dict[str, Path]) -> dict[str, gpd.GeoDataFrame]:
    """Join polygon footprints to phaseE EUI results on osm_id."""
    gdfs: dict[str, gpd.GeoDataFrame] = {}
    medians: dict[str, float] = {}

    print("\nPer-cell join stats:")
    for cell, fp_path in fp_paths.items():
        fp = gpd.read_file(str(fp_path))
        res = gpd.read_file(str(RESULTS_BASE / cell / "05_results.gpkg"))

        res_attr = res.drop(columns=["geometry"]) if "geometry" in res.columns else res
        cols = [c for c in ["osm_id", "total_eui_kwh_m2", "simulation_status"] if c in res_attr.columns]
        gdf = fp.merge(res_attr[cols], on="osm_id", how="left")

        fp_n   = len(fp)
        res_n  = len(res)
        match  = gdf["total_eui_kwh_m2"].notna().sum()
        pct    = 100.0 * match / fp_n
        med    = float(gdf["total_eui_kwh_m2"].median())
        medians[cell] = med
        print(f"  {cell:20s}  fp={fp_n} res={res_n} matched={match} ({pct:.1f}%)  "
              f"median={med:.1f} kWh/m²/yr")
        gdfs[cell] = gdf

    print("\nPer-cell median total_eui_kwh_m2:")
    for cell, med in medians.items():
        print(f"  {cell:20s}  {med:.1f}")

    return gdfs


# ─── T03 ────────────────────────────────────────────────────────────────────

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


def t03_render_grid(gdfs: dict[str, gpd.GeoDataFrame]) -> Path:
    """Render 3x4 choropleth grid with CartoDB Positron basemap and shared colorbar."""
    all_eui = np.concatenate([
        gdf["total_eui_kwh_m2"].dropna().values for gdf in gdfs.values()
    ])
    vmin = float(np.percentile(all_eui, 2))
    vmax = float(np.percentile(all_eui, 98))
    print(f"\nShared scale (2nd-98th pct pooled EUI): {vmin:.1f} - {vmax:.1f} kWh/m²/yr")

    cmap = plt.cm.YlOrRd
    norm = plt.Normalize(vmin=vmin, vmax=vmax)

    fig, axes = plt.subplots(3, 4, figsize=(20, 14))
    fig.suptitle(
        f"Phase-E — Building Total EUI (kWh/m²/yr)  "
        f"[scale: {vmin:.0f}-{vmax:.0f} kWh/m²/yr, 2nd-98th pct]",
        fontsize=13, y=1.01,
    )

    for j, ring in enumerate(RINGS):
        axes[0, j].set_title(RING_LABELS[ring], fontsize=12, fontweight="bold", pad=8)

    for i, city in enumerate(CITIES):
        for j, ring in enumerate(RINGS):
            cell = f"{city}_{ring}"
            ax   = axes[i, j]
            gdf  = gdfs[cell]

            # Reproject to Web Mercator for contextily basemap
            try:
                gdf_web = gdf.to_crs(epsg=3857)
            except Exception:
                gdf_web = gdf

            ok_mask   = (gdf_web["simulation_status"] == "success") & gdf_web["total_eui_kwh_m2"].notna()
            fail_mask = ~ok_mask

            if ok_mask.any():
                gdf_web[ok_mask].plot(ax=ax, column="total_eui_kwh_m2", cmap=cmap, norm=norm,
                                      linewidth=0.2, edgecolor="0.3", legend=False,
                                      missing_kwds={"color": "lightgrey"})
            if fail_mask.any():
                gdf_web[fail_mask].plot(ax=ax, color="grey", hatch="///", alpha=0.5,
                                        linewidth=0.2, edgecolor="0.3")

            # Set extent before basemap so tile zoom is correct
            bounds = gdf_web.total_bounds
            mx = (bounds[2] - bounds[0]) * 0.10
            my = (bounds[3] - bounds[1]) * 0.10
            ax.set_xlim(bounds[0] - mx, bounds[2] + mx)
            ax.set_ylim(bounds[1] - my, bounds[3] + my)

            _add_basemap(ax, cell)
            ax.set_axis_off()

    # Row labels — read axes positions after layout is settled
    fig.canvas.draw()
    for i, city in enumerate(CITIES):
        ax = axes[i, 0]
        pos = ax.get_position()
        ymid = (pos.y0 + pos.y1) / 2
        fig.text(pos.x0 - 0.015, ymid, CITY_LABELS[city],
                 fontsize=12, fontweight="bold", va="center", ha="right", rotation=90)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, fraction=0.015, pad=0.02, shrink=0.6)
    cbar.set_label("Total EUI (kWh/m²/yr)", fontsize=10)

    failed_patch = mpatches.Patch(facecolor="grey", edgecolor="0.3",
                                   hatch="///", alpha=0.5, label="Failed / not simulated")
    fig.legend(handles=[failed_patch], loc="lower center",
               bbox_to_anchor=(0.5, -0.02), fontsize=9)

    out = OUTPUTS_DIR / "phaseE_overview_grid.png"
    fig.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close(fig)

    size_kb = out.stat().st_size / 1024
    assert out.exists(), "FAIL: figure not written"
    assert size_kb > 100, f"FAIL: figure only {size_kb:.0f} KB"
    print(f"Figure saved -> {out}  ({size_kb:.0f} KB)")
    return out


# ─── main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== T01: Persist footprints ===")
    fp_paths = t01_persist_footprints()

    print("\n=== T02: Build map GeoDataFrames ===")
    gdfs = t02_build_map_gdfs(fp_paths)

    print("\n=== T03: Render overview grid ===")
    fig_path = t03_render_grid(gdfs)

    print("\n=== CHECKPOINT ===")
    print(f"Footprint files ({len(fp_paths)}):")
    for cell, p in fp_paths.items():
        print(f"  {p}")
    print(f"Figure: {fig_path}")
