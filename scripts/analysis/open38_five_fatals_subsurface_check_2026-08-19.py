"""OPEN-38 T05 follow-up (2026-08-19) -- now that 6 fatal IDFs actually exist on
disk (built by open38_five_fatals_rebuild_2026-08-19.py), answer T04's second
open question ("do unfitted subsurfaces occur below the CHKSBS warning
threshold?") directly from IDF geometry, reusing the same fit-test
(`test_subsurface_fit` / `run_subsurface_census`) and the same healthy-prototype
gate control already used and passed in `open07_smallhotel_idf_diff.py`.

Read-only over freshly built IDFs. No production code touched.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
sys.path.insert(0, str(REPO))

_spec = importlib.util.spec_from_file_location(
    "open07_smallhotel_idf_diff", REPO / "scripts" / "analysis" / "open07_smallhotel_idf_diff.py"
)
o07 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o07)

TARGETS = {
    "la_centre/way_427942886": r"scratchpad\open38-t05-rebuild\la_centre\step3_layout_assign\idfs\way_427942886.idf",
    "la_urban/relation_6374725": r"scratchpad\open38-t05-rebuild\la_urban\step3_layout_assign\idfs\relation_6374725.idf",
    "la_urban/way_401910463": r"scratchpad\open38-t05-rebuild\la_urban\step3_layout_assign\idfs\way_401910463.idf",
    "la_urban/way_428846131": r"scratchpad\open38-t05-rebuild\la_urban\step3_layout_assign\idfs\way_428846131.idf",
    "nyc_rural/way_965718400": r"scratchpad\open38-t05-rebuild\nyc_rural\step3_layout_assign\idfs\way_965718400.idf",
    "nyc_rural/way_965718402 (positive control)": r"scratchpad\open38-t05-rebuild\nyc_rural\step3_layout_assign\idfs\way_965718402.idf",
}


def main():
    print("STEP 1 (GATE) -- control: subsurface-fit test on healthy SmallHotel prototype")
    control_summary, control_rows = o07.run_subsurface_census(o07.CONTROL_IDF, "control")
    print(f"  control: {control_summary}")

    print("\nSTEP 2 -- per-building subsurface fit, LAUNDRYROOMFLR1 zone only, on freshly built IDFs")
    for label, rel in TARGETS.items():
        idf_path = REPO / rel
        summary, rows = o07.run_subsurface_census(str(idf_path), label)
        laundry_rows = [r for r in rows if "LAUNDRYROOMFLR1" in str(r.get("base_surface", "")).upper()
                         or "LAUNDRYROOMFLR1" in str(r.get("subsurface", "")).upper()]
        laundry_unfit = [r for r in laundry_rows if r["fitted"] is False]
        print(f"  {label}: {summary}; {len(laundry_rows)} on LAUNDRYROOMFLR1 surfaces, "
              f"{len(laundry_unfit)} unfitted among those")
        for r in laundry_rows:
            print(f"    {r}")


if __name__ == "__main__":
    main()
