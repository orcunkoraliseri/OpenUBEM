"""V12 nyc_urban phase 3: aggregate_results already done (05_results.gpkg saved).

Finish: CBECS gates (with eui_kwh_m2 alias), gates report, deliverables.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "validation"))

import geopandas as gpd
import pandas as pd

import v12_nyc_urban_recovery as r

JOB_ID = "959157"


def main() -> None:
    print("[nyc_urban] Phase 3 — gates + report + deliverables from saved Step 5 outputs")

    idf_manifest = pd.read_parquet(r.STEP3_DIR / "03_idf_manifest.parquet")
    sim_mf = pd.read_parquet(r.WORK_BASE / "04_simulation_manifest.parquet")
    results_gdf = gpd.read_file(str(r.RESULTS_DIR / "05_results.gpkg"))
    print(f"  idf_manifest: {len(idf_manifest)}, sim_mf: {len(sim_mf)}, results: {len(results_gdf)}")

    n_fetched = len(gpd.read_file(str(r.WORK_BASE / "01_buildings.gpkg")))

    from openubem.results import compute_validation_gates
    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=r.CBECS_PATH)
    print("\n[nyc_urban] CBECS 2018 NE GATES (report-only per V-R5-5):")
    for k in ["cbecs_cv_rmse", "cbecs_nmbe", "cbecs_r2", "cbecs_ks_d"]:
        print(f"  {k}: {cbecs_gates[k]}  PASS={cbecs_gates.get(k + '_pass')}")

    epw_station_name = "New.York-Central.Park.Obs-Belvedere.Castle"
    r.write_gates_report(idf_manifest, sim_mf, results_gdf, cbecs_gates,
                         epw_station_name=epw_station_name, job_id=JOB_ID, n_fetched=n_fetched)

    copied = r.copy_final_deliverables()
    print(f"\n[nyc_urban] Copied {len(copied)} files to {r.FINAL_DIR}")
    for p in copied:
        print(f"  {p}")
    print("\n[nyc_urban] DONE — phase 3 complete.")


if __name__ == "__main__":
    main()
