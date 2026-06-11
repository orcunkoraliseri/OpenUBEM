"""Step 2.1 orchestrator — enrich_climate() (DESIGN §3E, PLAN P5)."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

# 16-token closed vocabulary (DESIGN line 64 / F3)
_CLIMATE_ZONE_VOCAB = [
    "1A", "2A", "2B", "3A", "3B", "3C",
    "4A", "4B", "4C", "5A", "5B", "5C",
    "6A", "6B", "7", "8",
]


def _write_schema_json(gdf: gpd.GeoDataFrame, output_dir: Path) -> None:
    """Write 02a_buildings_climate.schema.json (P6 — mirrors building_classifier pattern)."""
    # provenance_role for the 3 new columns
    _NEW_ROLES = {
        "climate_zone": "derived",
        "epw_path": "derived",
        "provenance_climate_zone": "provenance",
    }
    entries = []
    for col in gdf.columns:
        role = _NEW_ROLES.get(col, "upstream")
        entry: dict = {"name": col, "dtype": str(gdf[col].dtype), "provenance_role": role}
        if col == "climate_zone":
            entry["vocabulary"] = _CLIMATE_ZONE_VOCAB
        elif col == "provenance_climate_zone":
            entry["vocabulary"] = ["ASHRAE_STANDARD", "HEURISTIC"]
        entries.append(entry)
    (output_dir / "02a_buildings_climate.schema.json").write_text(
        json.dumps({"schema_version": "1.0.0", "columns": entries}, indent=2),
        encoding="utf-8",
    )


def enrich_climate(
    gdf: gpd.GeoDataFrame,
    output_dir: Path | None = None,
    *,
    epw_dir: Path | None = None,
    offline: bool | None = None,
) -> gpd.GeoDataFrame:
    """Append climate_zone, epw_path, provenance_climate_zone to gdf (26 -> 29 cols).

    Parameters
    ----------
    gdf:
        26-column classified GeoDataFrame from Step 2 (UTM CRS).
    output_dir:
        When provided, write 02a_buildings_climate.gpkg + sidecar artifacts.
    epw_dir:
        User-provided directory containing .epw files (tier 1 of F10).
    offline:
        If None, reads config.OFFLINE. Skips network download tiers when True.

    Returns
    -------
    GeoDataFrame with 29 columns; upstream 26 byte-identical.
    """
    # Lazy imports to avoid circular import (acquisition/__init__ <- climate_zone
    # <- building_classifier <- osm_fetcher <- acquisition)
    from openubem import config  # noqa: PLC0415
    from openubem.acquisition.climate_zone import _validate_input_schema, assign_climate_zones  # noqa: PLC0415
    from openubem.acquisition.epw_manager import fetch_epw, load_stations, resolve_station  # noqa: PLC0415

    if offline is None:
        offline = config.OFFLINE

    _validate_input_schema(gdf)

    # §3B: per-building zone join
    zone_df = assign_climate_zones(gdf)

    # §3C: one EPW station per run at the neighbourhood union representative point
    union_pt = gdf.geometry.union_all().representative_point()
    union_pt_4326 = gpd.GeoDataFrame(geometry=[union_pt], crs=gdf.crs).to_crs(epsg=4326).geometry.iloc[0]
    run_lat, run_lon = union_pt_4326.y, union_pt_4326.x

    stations = load_stations()
    station, dist_km = resolve_station(run_lat, run_lon, stations)

    out_dir_path = Path(output_dir) if output_dir is not None else None

    if out_dir_path is None:
        import tempfile
        _tmp_dir = tempfile.mkdtemp(prefix="openubem_epw_")
        epw_out_dir: Path = Path(_tmp_dir)
    else:
        epw_out_dir = out_dir_path

    # §3D: resolve and validate EPW
    epw_dest = fetch_epw(
        station,
        epw_dir=Path(epw_dir) if epw_dir else None,
        offline=offline,
        output_dir=epw_out_dir,
    )

    # §3E: append 3 columns
    out = gdf.copy()
    out["climate_zone"] = pd.Categorical(
        zone_df["climate_zone"].values, categories=_CLIMATE_ZONE_VOCAB
    )
    out["epw_path"] = str(epw_dest)
    out["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )

    # Byte-identity invariant: upstream 26 columns must be unchanged (P5)
    pd.testing.assert_frame_equal(
        gdf.reset_index(drop=True),
        out[list(gdf.columns)].reset_index(drop=True),
    )

    assert out["climate_zone"].isna().sum() == 0, "climate_zone must never be null"
    assert out["epw_path"].isna().sum() == 0, "epw_path must never be null"
    assert out["provenance_climate_zone"].isna().sum() == 0, "provenance_climate_zone must never be null"

    if out_dir_path is not None:
        out_dir_path.mkdir(parents=True, exist_ok=True)

        out.to_file(
            str(out_dir_path / "02a_buildings_climate.gpkg"),
            layer="buildings",
            driver="GPKG",
        )
        _write_schema_json(out, out_dir_path)

        # Build sidecar (N×9) — DESIGN §3E F13
        sidecar = pd.DataFrame({
            "osm_id": gdf["osm_id"].values,
            "climate_zone": zone_df["climate_zone"].values,
            "climate_zone_method": zone_df["climate_zone_method"].values,
            "county_geoid": zone_df["county_geoid"].values,
            "state": zone_df["state"].values,
            "epw_station_id": str(station["station_id"]),
            "epw_path": str(epw_dest),
            "epw_distance_km": float(dist_km),
            "provenance_climate_zone": zone_df["provenance_climate_zone"].values,
        })
        sidecar.to_parquet(
            str(out_dir_path / "02a_climate_epw.parquet"),
            index=False,
        )

    return out
