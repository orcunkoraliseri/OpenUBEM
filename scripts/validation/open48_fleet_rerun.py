"""T04 (OPEN-48 part 2) — thin runner for the 12-cell fleet re-run with the
restored elevator wiring (builder.py T03). Does not edit v12_cell_pipeline.py;
calls its run_cell() unchanged with output_subdir="open48_refleet" so remote
fleet dirs and local result dirs are fresh, not a collision with the adopted
phaseE_elevrb run or any other output_subdir.

Usage:
    .venv\\Scripts\\python.exe scripts\\validation\\open48_fleet_rerun.py
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from scripts.validation.v12_cell_pipeline import run_cell

CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]

OUTPUT_SUBDIR = "open48_refleet"


def main() -> int:
    results = {}
    for cell in CELLS:
        print(f"\n\n###### T04 STARTING CELL {cell} ######\n", flush=True)
        try:
            run_cell(cell, output_subdir=OUTPUT_SUBDIR)
            results[cell] = "DONE"
            print(f"\n###### T04 CELL {cell} DONE ######\n", flush=True)
        except SystemExit as e:
            results[cell] = f"SYSEXIT({e.code})"
            print(f"\n###### T04 CELL {cell} SYSEXIT code={e.code} ######\n", flush=True)
        except Exception as e:
            results[cell] = f"EXCEPTION({e})"
            print(f"\n###### T04 CELL {cell} EXCEPTION: {e} ######\n", flush=True)
            traceback.print_exc()

    print("\n\n###### T04 FLEET RE-RUN SUMMARY ######", flush=True)
    for cell in CELLS:
        print(f"  {cell}: {results.get(cell, 'NOT STARTED')}", flush=True)
    print("###### T04 ALL CELLS COMPLETE ######", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
