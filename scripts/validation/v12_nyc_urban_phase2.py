"""V12 nyc_urban phase 2: job 959157 completed 1778/1778 on cluster.

Fetch via single streamed remote find|tar (avoids Windows 32k command-line limit),
then verify, sim manifest, Step 5, gates report, deliverables.
"""
from __future__ import annotations

import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "validation"))

import pandas as pd

import v12_nyc_urban_recovery as r

JOB_ID = "959157"


def fetch_streamed() -> None:
    r.SIM_OUT_DIR.mkdir(parents=True, exist_ok=True)
    tgz_path = r.WORK_BASE / "sim_out_fetch.tgz"
    remote_cmd = (
        f"cd {r.REMOTE_FLEET_DIR}/out && "
        f"find . -maxdepth 2 \\( -name eplusout.sql -o -name eplusout.err -o -name eplusout.end \\) -print0 "
        f"| tar czf - --null -T -"
    )
    print(f"[fetch] streaming tar from cluster -> {tgz_path}")
    t0 = time.monotonic()
    with open(tgz_path, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", r.REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE,
        )
        _, stderr_data = proc.communicate(timeout=3600)
    if proc.returncode != 0:
        print(f"[fetch] ssh rc={proc.returncode}: {stderr_data.decode(errors='replace')[:500]}", file=sys.stderr)
        sys.exit(1)
    size_mb = tgz_path.stat().st_size / 1e6
    print(f"[fetch] downloaded {size_mb:.1f} MB in {time.monotonic()-t0:.0f}s")

    print(f"[fetch] extracting ...")
    with tarfile.open(tgz_path, mode="r:gz") as tf:
        tf.extractall(str(r.SIM_OUT_DIR))
    n_ends = len(list(r.SIM_OUT_DIR.rglob("eplusout.end")))
    print(f"[fetch] extracted: {n_ends} .end files")
    tgz_path.unlink()


def main() -> None:
    print(f"[nyc_urban] Phase 2 — job {JOB_ID} completed on cluster, fetching + Step 5")

    idf_manifest = pd.read_parquet(r.STEP3_DIR / "03_idf_manifest.parquet")
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_id_stems = [Path(str(row["idf_path"])).stem for _, row in success_rows.iterrows()]
    n_generated = len(osm_id_stems)
    print(f"  IDF manifest: {len(idf_manifest)} rows, {n_generated} success")

    import geopandas as gpd
    n_fetched = len(gpd.read_file(str(r.WORK_BASE / "01_buildings.gpkg")))
    print(f"  n_fetched: {n_fetched}")

    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    stations = load_stations()
    station, dist_km = resolve_station(r.LAT, r.LON, stations)
    epw_path = fetch_epw(station, output_dir=r.WORK_BASE / "weather")
    epw_station_name = station.get("name", str(station["station_id"]))
    print(f"  EPW: {epw_path.name} ({dist_km:.1f} km)")

    fetch_streamed()

    ok_ids, failed_ids = r.verify_end_files(osm_id_stems)
    print(f"  Verified: {len(ok_ids)} success, {len(failed_ids)} failed")
    if failed_ids:
        print(f"  ZERO-FAIL violated: {failed_ids[:10]}", file=sys.stderr)
        sys.exit(2)

    print(f"\n[nyc_urban] Building sim manifest ...")
    sim_mf = r.build_sim_manifest(idf_manifest, epw_path, JOB_ID)
    n_sim_fail = int((sim_mf["status"] != "success").sum())
    if n_sim_fail > 0:
        print(f"  ZERO-FAIL: {n_sim_fail} failures in manifest", file=sys.stderr)
        sys.exit(2)

    print(f"\n[nyc_urban] Running Step 5 ...")
    results_gdf, cbecs_gates = r.step5_results(idf_manifest, sim_mf, epw_path)

    r.write_gates_report(idf_manifest, sim_mf, results_gdf, cbecs_gates,
                         epw_station_name=epw_station_name, job_id=JOB_ID, n_fetched=n_fetched)

    copied = r.copy_final_deliverables()
    print(f"\n[nyc_urban] Copied {len(copied)} files to {r.FINAL_DIR}")
    print(f"\n[nyc_urban] DONE — nyc_urban complete.")
    print(f"  Fetched:   {n_fetched}")
    print(f"  Generated: {n_generated}/{len(idf_manifest)}")
    print(f"  Simulated: {len(ok_ids)}/{n_generated}")
    print(f"  Job ID:    {JOB_ID}")


if __name__ == "__main__":
    main()
