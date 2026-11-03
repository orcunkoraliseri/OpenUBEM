"""OPEN-12 T05 -- retrace the 36.4% / 19.2% rural height residual to its source dataset.

The register carries the item's original percentages (`nyc_rural` 36.4%, `austin_rural` 19.2%)
side by side with a re-derived 100% / 100% on the fleet's tracked Stage-1 files, deliberately
unreconciled (register discipline). N15 already proved the fleet's Stage-1 files never consumed
the UTCI arc's E-UTCI-09 height backfill, and could not have, because the fusion path is not on
the fleet's code path at all. The one remaining candidate for where the original numbers could be
true -- the UTCI arc's own Stage-6 working dataset -- has never been checked. This script checks it.

Three re-derivations, each from a live read of a gpkg/parquet file, none inherited from a doc table:

  1. Fleet-side control: `height_m` NaN fraction in the tracked Stage-1 files
     (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`) for the
     three cells the item's numbers concern plus a fourth cell (`austin_centre`) as a control that
     was never claimed to be at 100%.
  2. UTCI-arc-side candidate: `height_m` NaN fraction in the arc's own post-E-UTCI-09-backfill
     working dataset (`scratchpad/e-utci-09-backfill/backfilled/<cell>_01_buildings_backfilled.gpkg`),
     read directly -- not quoted from the arc's own summary CSV/JSON.
  3. Git-tracking check on that scratch dataset, to establish whether it is a committed repository
     artifact or an ephemeral local file the E-UTCI-09 investigation happened to leave behind.

No fix, no code change, no simulation. Diagnosis only.

Emits openubem/outputs/comparisons/open12_height_residual_retrace.csv: one row per cell per dataset.
"""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parents[2]

FLEET_CELLS = ["nyc_rural", "austin_rural", "nyc_suburban", "austin_centre"]
FLEET_PATH_TMPL = "docs/docs_VALIDATION/validations/overAll/results/phaseE/{cell}/01_buildings.gpkg"

UTCI_CELLS = ["nyc_rural", "austin_rural", "nyc_suburban", "austin_centre"]
UTCI_PATH_TMPL = "scratchpad/e-utci-09-backfill/backfilled/{cell}_01_buildings_backfilled.gpkg"

REGISTER_ORIGINAL = {
    "nyc_rural": 36.4,
    "austin_rural": 19.2,
}


def height_na_fraction(path: Path) -> tuple[int, int, int]:
    gdf = gpd.read_file(path)
    n = len(gdf)
    na = int(gdf["height_m"].isna().sum())
    zero = int((gdf["height_m"] == 0).sum())
    return n, na, zero


def git_tracked(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT)
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(rel)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "tracked"
    ignore = subprocess.run(
        ["git", "check-ignore", "-v", str(rel)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if ignore.returncode == 0:
        return f"untracked, gitignored ({ignore.stdout.strip()})"
    return "untracked, not gitignored"


def main() -> None:
    rows = []

    for cell in FLEET_CELLS:
        path = REPO_ROOT / FLEET_PATH_TMPL.format(cell=cell)
        n, na, zero = height_na_fraction(path)
        pct = 100.0 * na / n if n else float("nan")
        rows.append(
            {
                "dataset": "fleet_stage1_tracked",
                "cell": cell,
                "path": str(path.relative_to(REPO_ROOT)),
                "n_buildings": n,
                "height_m_na": na,
                "height_m_present_zero": zero,
                "pct_na": round(pct, 4),
                "register_original_pct": REGISTER_ORIGINAL.get(cell, ""),
                "matches_register_original": (
                    abs(pct - REGISTER_ORIGINAL[cell]) < 0.1 if cell in REGISTER_ORIGINAL else ""
                ),
                "git_status": git_tracked(path),
            }
        )

    for cell in UTCI_CELLS:
        path = REPO_ROOT / UTCI_PATH_TMPL.format(cell=cell)
        if not path.exists():
            rows.append(
                {
                    "dataset": "utci_arc_backfilled_scratch",
                    "cell": cell,
                    "path": str(path.relative_to(REPO_ROOT)),
                    "n_buildings": "",
                    "height_m_na": "",
                    "height_m_present_zero": "",
                    "pct_na": "",
                    "register_original_pct": REGISTER_ORIGINAL.get(cell, ""),
                    "matches_register_original": "FILE ABSENT",
                    "git_status": "absent from disk",
                }
            )
            continue
        n, na, zero = height_na_fraction(path)
        pct = 100.0 * na / n if n else float("nan")
        rows.append(
            {
                "dataset": "utci_arc_backfilled_scratch",
                "cell": cell,
                "path": str(path.relative_to(REPO_ROOT)),
                "n_buildings": n,
                "height_m_na": na,
                "height_m_present_zero": zero,
                "pct_na": round(pct, 4),
                "register_original_pct": REGISTER_ORIGINAL.get(cell, ""),
                "matches_register_original": (
                    abs(pct - REGISTER_ORIGINAL[cell]) < 0.1 if cell in REGISTER_ORIGINAL else ""
                ),
                "git_status": git_tracked(path),
            }
        )

    out_path = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open12_height_residual_retrace.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "dataset",
        "cell",
        "path",
        "n_buildings",
        "height_m_na",
        "height_m_present_zero",
        "pct_na",
        "register_original_pct",
        "matches_register_original",
        "git_status",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
