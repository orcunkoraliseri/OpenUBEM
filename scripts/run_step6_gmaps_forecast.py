"""CLI entrypoint running Stage 6 microclimate with Google Weather/AQ forecast."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import geopandas as gpd

from openubem.microclimate import run_step6
from openubem.microclimate.gmaps_air_quality import fetch_ambient_air_quality
from openubem.microclimate.gmaps_weather import fetch_hourly_weather_forecast


def _default_output_dir(run_dir: Path, explicit: Path | None) -> Path | None:
    """Redirects default Stage 6 outputs out of frozen validation directories.

    Args:
        run_dir: OpenUBEM Stage 1-5 run directory.
        explicit: Optional caller-supplied output directory.

    Returns:
        Output path outside ``docs/docs_VALIDATION/`` or ``None`` if mutable.
    """
    if explicit is not None:
        return explicit
    resolved = run_dir.resolve()
    if "docs_VALIDATION" in resolved.parts:
        repo_root = Path(__file__).resolve().parents[1]
        return repo_root / "openubem" / "outputs" / "microclimate" / resolved.name
    return None


def _infer_centroid_wgs84(
    run_dir: Path,
    buildings_path: Path | None,
) -> tuple[float, float]:
    """Resolves WGS 84 district center coordinates from run building footprints.

    Args:
        run_dir: Stage 1-5 run directory.
        buildings_path: Optional explicit path to building footprints.

    Returns:
        Tuple ``(lat, lon)`` in decimal degrees.

    Raises:
        FileNotFoundError: If no building file is found under ``run_dir``.
    """
    candidates = (
        [buildings_path]
        if buildings_path is not None
        else [
            run_dir / "05_results.gpkg",
            run_dir / "02_buildings_imputed.gpkg",
            run_dir / "01_buildings_clean.gpkg",
            run_dir / "01_buildings_raw.gpkg",
            run_dir / "01_buildings.gpkg",
            run_dir / "buildings.parquet",
        ]
    )
    chosen: Path | None = next((p for p in candidates if p and p.is_file()), None)
    if chosen is None:
        raise FileNotFoundError(
            f"Cannot infer lat/lon: no building vector file found under {run_dir}."
        )
    gdf = (
        gpd.read_parquet(chosen)
        if chosen.suffix.lower() == ".parquet"
        else gpd.read_file(chosen)
    )
    utm = gdf.to_crs(gdf.estimate_utm_crs())
    cent = gpd.GeoSeries(utm.geometry.centroid, crs=utm.crs).to_crs(epsg=4326)
    return float(cent.y.mean()), float(cent.x.mean())


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parses command-line flags for the Google Maps forecast Stage 6 runner.

    Args:
        argv: Optional argument sequence for programmatic/test invocation.

    Returns:
        Parsed ``argparse.Namespace``.
    """
    parser = argparse.ArgumentParser(
        description="Run OpenUBEM Stage 6 UTCI forecast using Google Weather/AQ APIs."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--buildings-path", type=Path, default=None)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--weather-json", type=Path, default=None)
    parser.add_argument("--air-quality-json", type=Path, default=None)
    parser.add_argument("--with-air-quality", action="store_true")
    parser.add_argument("--lat", type=float, default=None)
    parser.add_argument("--lon", type=float, default=None)
    parser.add_argument("--wall-temp-tier", type=str, default="empirical")
    parser.add_argument("--vegetation-tier", type=str, default=None)
    parser.add_argument("--wind-tier", type=str, default=None)
    parser.add_argument("--res-m", type=float, default=None)
    parser.add_argument("--buffer-m", type=float, default=None)
    parser.add_argument("--cdsm-path", type=Path, default=None)
    parser.add_argument("--tdsm-path", type=Path, default=None)
    parser.add_argument("--dem-path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> Path:
    """Executes Stage 6 forecast workflow and returns the Stage 6 output path.

    Args:
        argv: Optional CLI argument sequence.

    Returns:
        Directory path containing ``06_mc_*`` artifacts and risk alerts.
    """
    args = parse_args(argv)
    if args.lat is not None and args.lon is not None:
        lat, lon = float(args.lat), float(args.lon)
    else:
        lat, lon = _infer_centroid_wgs84(args.run_dir, args.buildings_path)

    weather_df, utc_offset_h = fetch_hourly_weather_forecast(
        lat,
        lon,
        hours=args.hours,
        json_path=args.weather_json,
    )
    aq_ctx = None
    if args.with_air_quality or args.air_quality_json is not None:
        aq_ctx = fetch_ambient_air_quality(
            lat,
            lon,
            json_path=args.air_quality_json,
        )

    out_dir = _default_output_dir(args.run_dir, args.output_dir)
    return run_step6(
        args.run_dir,
        output_dir=out_dir,
        buildings_path=args.buildings_path,
        res_m=args.res_m,
        buffer_m=args.buffer_m,
        window_mode="forecast",
        vegetation_tier=args.vegetation_tier,
        wall_temp_tier=args.wall_temp_tier,
        wind_tier=args.wind_tier,
        cdsm_path=args.cdsm_path,
        tdsm_path=args.tdsm_path,
        dem_path=args.dem_path,
        weather_df_override=weather_df,
        weather_location_override=(lat, lon, utc_offset_h, 0.0),
        air_quality_context=aq_ctx,
    )


if __name__ == "__main__":
    main()
