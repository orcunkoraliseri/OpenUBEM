"""CLI entrypoint exporting the Google Maps 3D Web Companion & AI Studio bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from openubem.viz.gmaps_web_export import export_gmaps_companion_bundle


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parses command-line arguments for exporting the 3D companion bundle.

    Args:
        argv: Optional argument sequence for programmatic invocation.

    Returns:
        Parsed ``argparse.Namespace``.
    """
    parser = argparse.ArgumentParser(
        description="Export OpenUBEM district results for Google Maps 3D Web Viewer."
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--buildings-path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> dict[str, Path]:
    """Builds the 3D companion bundle and returns paths to generated files.

    Args:
        argv: Optional CLI argument sequence.

    Returns:
        Dictionary of generated artifact paths.
    """
    args = parse_args(argv)
    return export_gmaps_companion_bundle(
        args.run_dir,
        output_dir=args.output_dir,
        buildings_path=args.buildings_path,
    )


if __name__ == "__main__":
    main()
