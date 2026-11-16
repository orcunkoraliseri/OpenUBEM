"""CLI entrypoint exporting OpenUBEM district results as a GeoLibre bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from openubem.viz.geolibre_export import export_geolibre_bundle


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for exporting a GeoLibre workspace bundle.

    Args:
        argv: Optional argument sequence for programmatic invocation.

    Returns:
        Parsed ``argparse.Namespace``.
    """
    parser = argparse.ArgumentParser(
        description="Export OpenUBEM district results to a GeoLibre GIS bundle."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--buildings-path", type=Path, default=None)
    parser.add_argument("--results-csv", type=Path, default=None)
    parser.add_argument("--district", type=str, default=None)
    parser.add_argument("--color-by", type=str, default=None)
    parser.add_argument("--colormap", type=str, default="turbo")
    parser.add_argument("--basemap", type=str, default="dark")
    parser.add_argument(
        "--scheme",
        type=str,
        choices=("quantile", "equal-interval"),
        default="quantile",
    )
    parser.add_argument("--class-count", type=int, default=5)
    parser.add_argument("--no-extrude", action="store_true")
    parser.add_argument("--no-story-map", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> dict[str, Path]:
    """Build the GeoLibre bundle and return paths to generated artifacts.

    Args:
        argv: Optional CLI argument sequence.

    Returns:
        Dictionary mapping artifact roles to created filesystem paths.
    """
    args = parse_args(argv)
    return export_geolibre_bundle(
        args.run_dir,
        output_dir=args.output_dir,
        buildings_path=args.buildings_path,
        results_csv_path=args.results_csv,
        district_filter=args.district,
        basemap=args.basemap,
        color_by=args.color_by,
        colormap=args.colormap,
        scheme=args.scheme,
        class_count=args.class_count,
        extrude=not args.no_extrude,
        include_story_map=not args.no_story_map,
    )


if __name__ == "__main__":
    bundle = main()
    print(json.dumps({k: str(v) for k, v in bundle.items()}, indent=2))
