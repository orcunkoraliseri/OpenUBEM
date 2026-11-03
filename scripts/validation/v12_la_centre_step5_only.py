"""Run Step 5 only for la_centre — sim_out already populated (225/225)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

# Import everything from the main fetch script (constants + functions)
from v12_la_centre_fetch_step5 import (
    CELL_NAME, WORK_BASE, STEP3_DIR, SIM_OUT_DIR, EPW_STATION,
    verify_all_complete, build_sim_manifest, step5_and_report,
)


def main() -> None:
    print(f"[{CELL_NAME}] step5_only: sim_out pre-populated, skipping fetch")
    print(f"  work_base: {WORK_BASE}")

    epw_path = list((WORK_BASE / "weather").rglob("*.epw"))[0]
    print(f"  EPW: {epw_path.name}")

    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    print(f"  IDF manifest: {len(idf_manifest)} rows, "
          f"success={(idf_manifest['generation_status']=='success').sum()}")

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    print(f"  Verifying {len(osm_ids)} buildings ...")
    verify_all_complete(osm_ids)

    print(f"\n[{CELL_NAME}] Building sim manifest ...")
    sim_mf = build_sim_manifest(idf_manifest, epw_path)

    n_fail = int((sim_mf["status"] == "failed").sum())
    if n_fail > 0:
        print(f"[{CELL_NAME}] ZERO-FAIL VIOLATION: {n_fail} failed", file=sys.stderr)
        sys.exit(2)

    print(f"\n[{CELL_NAME}] Running Step 5 ...")
    step5_and_report(idf_manifest, sim_mf, epw_path, EPW_STATION)

    print(f"\n[{CELL_NAME}] COMPLETE.")
    print(f"  Simulated: 225/225 (2 repaired via single_zone, job 964792)")
    print(f"  Main array job: 964556")
    print(f"  Repair job: 964792")


if __name__ == "__main__":
    main()
