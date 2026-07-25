"""T18 - Stage-6 (UTCI / outdoor microclimate) runner script.

Thin CLI over openubem.microclimate.run_step6 (F-02's "library function + runner" pattern).
Stage 6 is invoked explicitly, only via this script or a direct run_step6() call -- never from
any Stage 1-5 code path (plan §6a).

output-dir policy (module docstring of openubem/microclimate/__init__.py): defaults to run-dir,
matching F-08's convention for a normal, writable Stage 1-5 output tree. When run-dir sits under
the git-tracked docs/docs_VALIDATION/ archive, this script POINTS output-dir at
openubem/outputs/stage6/<cell-name>/ automatically unless --output-dir is given explicitly --
CP-4's gate requires docs_VALIDATION/ to show zero git modification, and that tree was measured
git-tracked and clean (2026-07-24); writing 06_mc_* into it would trip the gate immediately.

Usage:
    py -3 scripts/run_step6_microclimate.py --run-dir docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre
    py -3 scripts/run_step6_microclimate.py --run-dir <fresh_stage1_5_output_dir> --wind-tier macdonald --vegetation-tier osm
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from openubem.microclimate import run_step6  # noqa: E402

_VALIDATION_ROOT = (REPO / "docs" / "docs_VALIDATION").resolve()


def _default_output_dir(run_dir: Path) -> "Path | None":
    try:
        run_dir.resolve().relative_to(_VALIDATION_ROOT)
    except ValueError:
        return None  # not under docs_VALIDATION -- F-08 default (output_dir = run_dir) applies
    return REPO / "openubem" / "outputs" / "stage6" / run_dir.name


def main():
    ap = argparse.ArgumentParser(description="Stage 6 - outdoor microclimate & UTCI (T18 runner)")
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--output-dir", type=Path, default=None)
    ap.add_argument("--epw-path", type=Path, default=None)
    ap.add_argument("--res-m", type=float, default=None)
    ap.add_argument("--buffer-m", type=float, default=None)
    ap.add_argument("--window-mode", choices=["hottest_week", "design_hours", "annual"], default=None)
    ap.add_argument("--vegetation-tier", choices=["none", "osm", "cdsm"], default=None)
    ap.add_argument("--wall-temp-tier", choices=["empirical", "energyplus"], default=None)
    ap.add_argument("--wind-tier", choices=["cost730", "macdonald"], default=None)
    ap.add_argument("--override-annual-energyplus", action="store_true")
    args = ap.parse_args()

    run_dir = args.run_dir.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir is not None else _default_output_dir(run_dir)

    print(f"[step6] run_dir:    {run_dir}")
    print(f"[step6] output_dir: {output_dir or '(= run_dir, F-08 default)'}")

    t0 = time.time()
    result_dir = run_step6(
        run_dir,
        output_dir=output_dir,
        epw_path=args.epw_path,
        res_m=args.res_m,
        buffer_m=args.buffer_m,
        window_mode=args.window_mode,
        vegetation_tier=args.vegetation_tier,
        wall_temp_tier=args.wall_temp_tier,
        wind_tier=args.wind_tier,
        override_annual_energyplus=args.override_annual_energyplus,
    )
    wall_clock = time.time() - t0
    print(f"[step6] wrote artifacts to {result_dir} in {wall_clock:.1f}s")

    for f in sorted(Path(result_dir).glob("06_mc_*")):
        print(f"  {f.name}  ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
