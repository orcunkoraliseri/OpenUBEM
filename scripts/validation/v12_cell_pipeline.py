"""V12 — Generic cell pipeline for the case-study matrix.

Usage:
    py -3 scripts/validation/v12_cell_pipeline.py nyc_urban
    py -3 scripts/validation/v12_cell_pipeline.py nyc_suburban
    py -3 scripts/validation/v12_cell_pipeline.py nyc_rural

Each cell runs Steps 1-3 locally, ships to Speed cluster, polls for completion,
fetches results, and runs Step 5 locally.  Final deliverables go to:
    docs/validations/overAll/results/cases/<cell>/
Raw work dir:
    %TEMP%/ubem_validation/cases/<cell>/
Remote fleet dir:
    /speed-scratch/o_iseri/fleets/<cell>/
"""
from __future__ import annotations

import io
import json
import re as _re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"
SBATCH_REMOTE = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"

CELL_CONFIGS: dict[str, dict] = {
    "nyc_urban": {
        "lat": 40.7721, "lon": -73.9301, "radius_m": 500.0,
        "state": "NY", "epsg": 32618,
        "probe_count": 1526,
    },
    "nyc_suburban": {
        "lat": 40.7052, "lon": -73.5985, "radius_m": 500.0,
        "state": "NY", "epsg": 32618,
        "probe_count": 1313,
    },
    "nyc_rural": {
        "lat": 42.0396, "lon": -74.1143, "radius_m": 1000.0,
        "state": "NY", "epsg": 32618,
        "probe_count": 201,
    },
    "la_centre": {
        "lat": 34.0522, "lon": -118.2437, "radius_m": 500.0,
        "state": "CA", "epsg": 32611,
        "probe_count": 182,
    },
    "la_urban": {
        "lat": 34.0584, "lon": -118.3040, "radius_m": 500.0,
        "state": "CA", "epsg": 32611,
        "probe_count": 533,
    },
    "la_suburban": {
        "lat": 33.8359, "lon": -118.3406, "radius_m": 500.0,
        "state": "CA", "epsg": 32611,
        "probe_count": 1054,
    },
    "la_rural": {
        "lat": 34.7420, "lon": -118.2130, "radius_m": 1500.0,
        "state": "CA", "epsg": 32611,
        "probe_count": 143,
    },
    "austin_centre": {
        "lat": 30.2672, "lon": -97.7431, "radius_m": 500.0,
        "state": "TX", "epsg": 32614,
        "probe_count": 351,
    },
    "austin_urban": {
        "lat": 30.3072, "lon": -97.7400, "radius_m": 500.0,
        "state": "TX", "epsg": 32614,
        "probe_count": 320,
    },
    "austin_suburban": {
        "lat": 30.5085, "lon": -97.6789, "radius_m": 500.0,
        "state": "TX", "epsg": 32614,
        "probe_count": 410,
    },
    "austin_rural": {
        "lat": 30.5788, "lon": -98.2700, "radius_m": 1000.0,
        "state": "TX", "epsg": 32614,
        "probe_count": 184,
    },
}

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr


def _scp_put(local: Path, remote: str, timeout: int = 300) -> None:
    subprocess.run(["scp", "-r", str(local), f"{REMOTE_HOST}:{remote}"],
                   check=True, timeout=timeout)


def resolve_epw(lat: float, lon: float, work_base: Path) -> tuple[Path, str]:
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    stations = load_stations()
    station, dist_km = resolve_station(lat, lon, stations)
    print(f"  Resolved station: {station['station_id']} ({station.get('name', 'N/A')}) at {dist_km:.1f} km")
    epw_path = fetch_epw(station, output_dir=work_base)
    print(f"  EPW path: {epw_path}")
    with open(epw_path, encoding="utf-8", errors="replace") as fh:
        first_line = fh.readline()
    print(f"  EPW header: {first_line.strip()[:120]}")
    return epw_path, station.get("name", str(station["station_id"]))


def step1_fetch(lat: float, lon: float, radius_m: float, work_base: Path) -> gpd.GeoDataFrame:
    gdf_path = work_base / "01_buildings.gpkg"
    if gdf_path.exists():
        print(f"  Step 1: loading cached GDF from {gdf_path}")
        return gpd.read_file(str(gdf_path))
    print(f"  Step 1: fetching OSM buildings at ({lat}, {lon}) r={radius_m}m ...")
    t0 = time.monotonic()
    from openubem.acquisition.osm_fetcher import ingest_buildings
    gdf = ingest_buildings(location=(lat, lon), radius_m=radius_m)
    print(f"    fetched {len(gdf)} buildings ({time.monotonic()-t0:.1f}s)")
    work_base.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(gdf_path), driver="GPKG")
    print(f"    saved -> {gdf_path}")
    return gdf


def step2_classify_enrich(gdf_raw: gpd.GeoDataFrame, epw_path: Path,
                           work_base: Path, cell_name: str) -> tuple[gpd.GeoDataFrame, object]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    gdf_raw2 = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")

    print(f"  Step 2: classify ({len(gdf_raw2)} buildings) ...")
    t0 = time.monotonic()
    bc = BuildingClassifier()
    gdf_26 = bc.classify(gdf_raw2)
    n_unknown = int((gdf_26["archetype_id"] == "OpenUBEMUnknown").sum())
    print(f"    classified: {len(gdf_26)}, unknown={n_unknown} ({time.monotonic()-t0:.1f}s)")
    print("    archetype distribution:")
    print(gdf_26["archetype_id"].value_counts().to_string())

    print("  Step 2.1: climate enrichment ...")
    t0 = time.monotonic()
    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )
    print(f"    CZ distribution: {zone_df['climate_zone'].value_counts().to_dict()} ({time.monotonic()-t0:.1f}s)")

    sidecar = pd.DataFrame({
        "osm_id": gdf_26["osm_id"].values,
        "climate_zone": zone_df["climate_zone"].values,
        "climate_zone_method": zone_df["climate_zone_method"].values,
        "county_geoid": zone_df["county_geoid"].values,
        "state": zone_df["state"].values,
        "epw_path": str(epw_path),
        "provenance_climate_zone": zone_df["provenance_climate_zone"].values,
    })
    sidecar.to_parquet(str(work_base / "02a_climate_epw.parquet"), index=False)

    print("  Step 2.2: semantic enrichment ...")
    t0 = time.monotonic()
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    print(f"    enriched: {len(gdf_57)} buildings ({time.monotonic()-t0:.1f}s)")
    return gdf_57, schedule_library


def step3_generate(gdf_57: gpd.GeoDataFrame, schedule_library: object,
                   step3_dir: Path) -> pd.DataFrame:
    from openubem.idf.builder import run_step3
    step3_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = step3_dir / "03_idf_manifest.parquet"
    if manifest_path.exists():
        print(f"  Step 3: loading cached manifest from {manifest_path}")
        return pd.read_parquet(manifest_path)
    print(f"  Step 3: IDF generation (n_jobs=4) for {len(gdf_57)} buildings ...")
    t0 = time.monotonic()
    idf_manifest = run_step3(gdf_57, schedule_library, step3_dir, n_jobs=4)
    elapsed = time.monotonic() - t0
    status_counts = idf_manifest["generation_status"].value_counts().to_dict()
    n_success = status_counts.get("success", 0)
    n_total = len(idf_manifest)
    print(f"    generated: {n_success}/{n_total} IDFs in {elapsed:.1f}s")
    print(f"    status counts: {status_counts}")
    return idf_manifest


def live_smoke_check(idf_manifest: pd.DataFrame, cell_name: str) -> None:
    n_total = len(idf_manifest)
    n_success = int((idf_manifest["generation_status"] == "success").sum())
    pct_gen = n_success / n_total if n_total > 0 else 0.0
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_unknown = n_unknown / n_total if n_total > 0 else 0.0
    print(f"\n[{cell_name}] LIVE_SMOKE gates:")
    print(f"  generation success: {n_success}/{n_total} = {pct_gen*100:.1f}%  (gate >=95%: {'PASS' if pct_gen >= 0.95 else 'FAIL'})")
    print(f"  Unknown archetype: {n_unknown}/{n_total} = {pct_unknown*100:.1f}%  (gate <20%: {'PASS' if pct_unknown < 0.20 else 'FAIL'})")
    if pct_gen < 0.95:
        print(f"[{cell_name}] LIVE_SMOKE FAIL: generation success below 95%. STOP.", file=sys.stderr)
        sys.exit(1)
    if pct_unknown >= 0.20:
        print(f"[{cell_name}] LIVE_SMOKE FAIL: Unknown archetype share >= 20%. STOP.", file=sys.stderr)
        sys.exit(1)
    print(f"[{cell_name}] LIVE_SMOKE: both gates PASS. Proceeding to cluster ship.")


def ship_to_cluster(idf_manifest: pd.DataFrame, epw_path: Path,
                    remote_fleet_dir: str, work_base: Path) -> None:
    fleet_staging = work_base / "fleet_staging"
    idfs_local = fleet_staging / "idfs"
    weather_local = fleet_staging / "weather"
    idfs_local.mkdir(parents=True, exist_ok=True)
    weather_local.mkdir(parents=True, exist_ok=True)

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    # Use the IDF filename stem (e.g. way_220649876) not osm_id (e.g. way/220649876)
    # so fleet.lst matches the idfs/<stem>.idf naming the sbatch script expects.
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]

    for _, row in success_rows.iterrows():
        src = Path(str(row["idf_path"]))
        dst = idfs_local / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

    shutil.copy2(epw_path, weather_local / epw_path.name)

    fleet_lst = fleet_staging / "fleet.lst"
    # Use binary write to guarantee Unix LF line endings (avoid Windows CRLF)
    fleet_lst.write_bytes(("\n".join(osm_ids) + "\n").encode("utf-8"))

    print(f"  fleet size: {len(osm_ids)} buildings")
    _ssh(f"mkdir -p {remote_fleet_dir}/idfs {remote_fleet_dir}/weather {remote_fleet_dir}/out")

    subprocess.run(["scp", str(fleet_lst), f"{REMOTE_HOST}:{remote_fleet_dir}/fleet.lst"],
                   check=True, timeout=60)
    subprocess.run(["scp", str(weather_local / epw_path.name),
                    f"{REMOTE_HOST}:{remote_fleet_dir}/weather/"],
                   check=True, timeout=120)

    print("  uploading IDFs (tar stream) ...")
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        for idf_file in sorted(idfs_local.glob("*.idf")):
            tf.add(str(idf_file), arcname=f"idfs/{idf_file.name}")
    tar_buf.seek(0)
    untar_cmd = f"cd {remote_fleet_dir} && tar xz"
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc '{untar_cmd}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc.stdin.write(tar_buf.read())
    proc.stdin.close()
    proc.wait(timeout=300)
    print("  upload complete.")


def submit_cluster_array(n_jobs: int, remote_fleet_dir: str, cell_name: str) -> str:
    upload = subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
        capture_output=True, text=True, timeout=60,
    )
    if upload.returncode != 0:
        print(f"  sbatch upload warning: {upload.stderr.strip()}")

    submit_cmd = (
        f"sbatch --array=1-{n_jobs}%32 "
        f"--export=FLEET_DIR={remote_fleet_dir} "
        f"--job-name=openubem_{cell_name} "
        f"--output={remote_fleet_dir}/openubem_{cell_name}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"  Submitting SLURM array: {submit_cmd}")
    out = _ssh(submit_cmd, timeout=60)
    print(f"  sbatch output: {out.strip()}")

    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  ERROR: could not parse job ID from sbatch output:\n{out}", file=sys.stderr)
        sys.exit(1)
    print(f"  Job ID: {job_id}")
    return job_id


def poll_cluster(job_id: str, cell_name: str, poll_interval_s: int = 90) -> None:
    print(f"[{cell_name}] Polling job {job_id} (poll every {poll_interval_s}s) ...")
    while True:
        time.sleep(poll_interval_s)
        out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", timeout=60)
        pending_count = int(out.strip()) if out.strip().isdigit() else -1
        sacct_out = _ssh(
            f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c",
            timeout=60,
        )
        print(f"  [{time.strftime('%H:%M:%S')}] squeue count={pending_count}  sacct states: {sacct_out.strip()}")
        if pending_count == 0:
            print(f"[{cell_name}] Job {job_id}: no tasks in queue.")
            sacct_full = _ssh(
                f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null",
                timeout=60,
            )
            print(sacct_full)
            break


def fetch_results(osm_ids: list[str], remote_fleet_dir: str, sim_out_dir: Path) -> None:
    print(f"  Fetching results from cluster for {len(osm_ids)} buildings ...")
    sim_out_dir.mkdir(parents=True, exist_ok=True)

    # Single streamed find|tar pipe: avoids Windows 32k command-line limit
    # (enumerating per-building paths truncated the ssh command on big fleets).
    tgz_path = sim_out_dir.parent / "sim_out_fetch.tgz"
    remote_cmd = (
        f"cd {remote_fleet_dir}/out && "
        f"find . -maxdepth 2 \\( -name eplusout.sql -o -name eplusout.err -o -name eplusout.end \\) -print0 "
        f"| tar czf - --null -T -"
    )
    t0 = time.monotonic()
    with open(tgz_path, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE,
        )
        _, stderr_data = proc.communicate(timeout=3600)
    if proc.returncode != 0:
        print(f"  fetch ssh rc={proc.returncode}: {stderr_data.decode(errors='replace')[:500]}", file=sys.stderr)
        sys.exit(1)
    print(f"  downloaded {tgz_path.stat().st_size/1e6:.1f} MB in {time.monotonic()-t0:.0f}s")
    with tarfile.open(tgz_path, mode="r:gz") as tf:
        tf.extractall(str(sim_out_dir))
    tgz_path.unlink()
    print(f"  extracted: {len(list(sim_out_dir.rglob('eplusout.end')))} .end files")


def verify_and_repair(osm_ids: list[str], sim_out_dir: Path, step3_dir: Path,
                      remote_fleet_dir: str, cell_name: str, epw_path: Path) -> list[str]:
    failed_ids = []
    for oid in osm_ids:
        end_path = sim_out_dir / oid / "eplusout.end"
        if not end_path.exists():
            failed_ids.append(oid)
            continue
        txt = end_path.read_text(errors="replace")
        if "EnergyPlus Completed Successfully" not in txt:
            failed_ids.append(oid)

    if not failed_ids:
        print(f"  Zero-fail: all {len(osm_ids)} buildings completed successfully.")
        return []

    print(f"\n  ZERO-FAIL violation: {len(failed_ids)} failed buildings.")
    for oid in failed_ids:
        err_path = sim_out_dir / oid / "eplusout.err"
        if err_path.exists():
            tail = err_path.read_text(errors="replace")[-2000:]
            print(f"    osm_id={oid} err tail:\n{tail}")
        else:
            print(f"    osm_id={oid}: no eplusout.err found")

    print(f"\n  Attempting zero-surface-area repair on {len(failed_ids)} failed buildings...")
    repair_dir = step3_dir / "repair"
    repair_dir.mkdir(exist_ok=True)
    repaired = []

    for oid in failed_ids:
        idf_src = step3_dir / "idfs" / f"{oid}.idf"
        if not idf_src.exists():
            print(f"    {oid}: source IDF not found, cannot repair")
            continue
        idf_repair = repair_dir / f"{oid}.idf"
        shutil.copy2(idf_src, idf_repair)
        _remove_zero_area_surfaces(idf_repair)
        repaired.append(oid)
        print(f"    {oid}: zero-area surfaces stripped -> {idf_repair}")

    if not repaired:
        print(f"  No IDFs could be repaired. STOP — manual intervention needed.", file=sys.stderr)
        sys.exit(2)

    repair_fleet_dir = remote_fleet_dir + "_repair"
    _ssh(f"mkdir -p {repair_fleet_dir}/idfs {repair_fleet_dir}/weather {repair_fleet_dir}/out")

    repair_lst_local = step3_dir / "repair_fleet.lst"
    repair_lst_local.write_bytes(("\n".join(repaired) + "\n").encode("utf-8"))

    subprocess.run(["scp", str(repair_lst_local),
                    f"{REMOTE_HOST}:{repair_fleet_dir}/fleet.lst"],
                   check=True, timeout=30)
    subprocess.run(["scp", str(epw_path),
                    f"{REMOTE_HOST}:{repair_fleet_dir}/weather/"],
                   check=True, timeout=60)

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        for oid in repaired:
            idf_file = repair_dir / f"{oid}.idf"
            tf.add(str(idf_file), arcname=f"idfs/{oid}.idf")
    tar_buf.seek(0)
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {repair_fleet_dir} && tar xz'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc.stdin.write(tar_buf.read())
    proc.stdin.close()
    proc.wait(timeout=120)

    repair_job = submit_cluster_array(len(repaired), repair_fleet_dir, cell_name + "_repair")
    poll_cluster(repair_job, cell_name + "_repair", poll_interval_s=90)

    fetch_results(repaired, repair_fleet_dir, sim_out_dir)

    still_failed = []
    for oid in repaired:
        end_path = sim_out_dir / oid / "eplusout.end"
        if not end_path.exists() or "EnergyPlus Completed Successfully" not in end_path.read_text(errors="replace"):
            still_failed.append(oid)

    if still_failed:
        print(f"  {len(still_failed)} buildings still failed after repair: {still_failed}", file=sys.stderr)
        sys.exit(2)

    print(f"  Repair successful: {len(repaired)} buildings now complete.")
    return repaired


def _remove_zero_area_surfaces(idf_path: Path) -> None:
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    import re
    pattern = re.compile(
        r"BuildingSurface:Detailed,[\s\S]*?(?=\n\s*\n|\Z)",
        re.MULTILINE,
    )
    blocks = pattern.findall(text)
    removed = 0
    for block in blocks:
        coord_lines = [l.strip() for l in block.split("\n") if _re.match(r"^\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*", l)]
        if len(coord_lines) < 3:
            text = text.replace(block, "")
            removed += 1
    if removed:
        print(f"      stripped {removed} degenerate surface blocks")
    idf_path.write_text(text, encoding="utf-8")


def build_sim_manifest(idf_manifest: pd.DataFrame, sim_out_dir: Path,
                       epw_path: Path, job_id: str, step3_dir: Path,
                       work_base: Path) -> pd.DataFrame:
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    # Use IDF stem (underscore format) for dir lookups; keep normalised osm_id for manifest rows.
    osm_id_stems = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    osm_ids_raw = [str(r["osm_id"]) for _, r in success_rows.iterrows()]

    sim_rows = []
    for oid_stem, oid_raw in zip(osm_id_stems, osm_ids_raw):
        oid = oid_stem
        bdir = sim_out_dir / oid
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        err_path = bdir / "eplusout.err"

        status = "failed"
        n_warnings, n_severe, error_summary = 0, 0, ""
        if end_path.exists():
            txt = end_path.read_text(errors="replace")
            status = "success" if "EnergyPlus Completed Successfully" in txt else "failed"
        if err_path.exists():
            etxt = err_path.read_text(errors="replace")
            matches = _re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", etxt)
            if matches:
                n_warnings, n_severe = int(matches[-1][0]), int(matches[-1][1])
            severes = [l.strip() for l in etxt.splitlines() if "** Severe **" in l]
            error_summary = severes[0] if severes else ""

        sim_rows.append({
            "osm_id": oid_raw,
            "idf_path": str(step3_dir / "idfs" / f"{oid}.idf"),
            "work_dir": str(bdir),
            "sql_path": str(sql_path) if sql_path.exists() else "",
            "status": status,
            "n_warnings": n_warnings,
            "n_severe": n_severe,
            "wall_clock_s": 0.0,
            "ep_version": "23.1.0",
            "epw_path": str(epw_path),
            "error_summary": error_summary,
            "csv_path": None,
        })

    sim_mf = pd.DataFrame(sim_rows)
    manifest_path = work_base / "04_simulation_manifest.parquet"
    sim_mf.to_parquet(str(manifest_path), index=False)
    status_counts = sim_mf["status"].value_counts().to_dict()
    print(f"  Sim manifest: {len(sim_mf)} rows, status={status_counts}")
    return sim_mf


def _build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame,
                         epsg: int) -> gpd.GeoDataFrame:
    rows = []
    for _, idf_row in idf_mf.iterrows():
        osm_id = str(idf_row["osm_id"])
        osm_id_norm = osm_id.replace("_", "/", 1) if "_" in osm_id and "/" not in osm_id else osm_id
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == osm_id_norm]

        footprint_area_m2 = 200.0
        num_floors = 1.0
        height_m = 3.5
        centroid_x, centroid_y = 0.0, 0.0

        if len(sim_row) > 0 and sim_row.iloc[0]["status"] == "success":
            sql_path = Path(str(sim_row.iloc[0]["sql_path"]))
            if sql_path.exists():
                try:
                    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
                    zones = conn.execute(
                        "SELECT ZoneName, CeilingHeight, FloorArea, CentroidX, CentroidY FROM Zones"
                    ).fetchall()
                    conn.close()
                    zoning = idf_row["zoning_strategy"]
                    num_zones = int(idf_row["num_zones"])

                    if zoning == "single_zone":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        height_m = float(z[1])
                        num_floors = max(1.0, round(height_m / 3.5))
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                    elif zoning == "one_zone_per_floor":
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        num_floors = float(num_zones)
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    elif "perimeter_core" in zoning:
                        floor_areas: dict[int, float] = {}
                        for z in zones:
                            m = _floor_rx.search(z[0])
                            if m:
                                f = int(m.group(1))
                                floor_areas[f] = floor_areas.get(f, 0.0) + float(z[2])
                        num_floors = max(1.0, float(len(floor_areas)))
                        footprint_area_m2 = floor_areas.get(0, sum(floor_areas.values()) / max(1, len(floor_areas)))
                        height_m = num_floors * 3.5
                        centroid_x = sum(float(zz[3]) for zz in zones) / len(zones)
                        centroid_y = sum(float(zz[4]) for zz in zones) / len(zones)
                    else:
                        z = zones[0]
                        footprint_area_m2 = float(z[2])
                        centroid_x, centroid_y = float(z[3]), float(z[4])
                except Exception as e:
                    print(f"  SQL error for {osm_id}: {e}")

        rows.append({
            "osm_id": osm_id_norm,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })
    return gpd.GeoDataFrame(rows, crs=f"EPSG:{epsg}")


def step5_results(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame, epw_path: Path,
                   results_dir: Path, work_base: Path, state: str, epsg: int,
                   cell_name: str) -> tuple[gpd.GeoDataFrame, dict]:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Building enriched GDF from SQL Zones ...")
    enriched_gdf = _build_enriched_gdf(idf_manifest, sim_mf, epsg)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = work_base / "02a_climate_epw.parquet"

    print(f"  Step 5: aggregate_results ...")
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_manifest, enriched_gdf,
            results_dir,
            climate_sidecar=climate_sidecar if climate_sidecar.exists() else None,
            state=state,
            make_figures=True,
            ep_version="23.1.0",
        )
    wall = time.monotonic() - t0
    print(f"  aggregate_results done in {wall:.1f}s")

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0

    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()

    summary_path = results_dir / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    print(f"\n[{cell_name}] F12 GATE SUMMARY:")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}), PASS={pct_parse_success>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}), PASS={pct_plausible>=0.99}")
    if len(outliers) > 0:
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch}, PASS={n_zone_mismatch==0}")
    print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)
    print(f"\n[{cell_name}] CBECS 2018 NE VALIDATION GATES (report-only):")
    print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
    print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%  PASS={cbecs_gates['cbecs_nmbe_pass']}")
    print(f"  R2:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}")
    print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}  PASS={cbecs_gates['cbecs_ks_d_pass']}")

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    print(f"\n[{cell_name}] HEADLINE NUMBERS:")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")

    return results_gdf, cbecs_gates


def write_gates_report(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame,
                        results_gdf: gpd.GeoDataFrame, cbecs_gates: dict,
                        epw_station_name: str, gen_elapsed_s: float, job_id: str,
                        gen_success: int, gen_total: int, fetched_count: int,
                        cell_name: str, cfg_lat: float, cfg_lon: float,
                        cfg_radius: float, results_dir: Path) -> str:
    from openubem import config as cfg

    summary_path = results_dir / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    success_statuses = {"success", "success_cached", "success_csv_fallback"}
    sim_success = sim_mf[sim_mf["status"].isin({"success", "success_cached"})]
    n_sim_success = len(sim_success)
    parsed = results_gdf[results_gdf["simulation_status"].isin(success_statuses)]
    n_parsed = len(parsed)
    pct_parse_success = n_parsed / n_sim_success if n_sim_success > 0 else 0.0
    lb, ub = cfg.EUI_PLAUSIBILITY_BOUNDS
    valid_eui = parsed[parsed["total_eui_kwh_m2"].notna()]["total_eui_kwh_m2"]
    in_range = ((valid_eui >= lb) & (valid_eui <= ub)).sum()
    pct_plausible = in_range / len(valid_eui) if len(valid_eui) > 0 else 0.0
    outliers = valid_eui[(valid_eui < lb) | (valid_eui > ub)]
    zone_mismatch = results_gdf[results_gdf["simulation_status"] == "failed_zone_mismatch"]
    n_zone_mismatch = len(zone_mismatch)
    iod_vals = parsed["iod"].dropna()
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_unknown = n_unknown / gen_total if gen_total > 0 else 0.0
    pct_gen = gen_success / gen_total if gen_total > 0 else 0.0
    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    sim_status_counts = sim_mf["status"].value_counts().to_dict()

    lines = [
        "=" * 72,
        f"V12 {cell_name.upper()} GATES REPORT",
        f"  Cell:   {cell_name}  ({cfg_lat}, {cfg_lon}) r={cfg_radius}m",
        f"  EPW:    {epw_station_name}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): {CELL_CONFIGS[cell_name]['probe_count']}",
        f"  Actual OSM fetch:    {fetched_count}",
        f"  Generation success:  {gen_success}/{gen_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {gen_success}/{gen_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{gen_total} = {pct_unknown*100:.1f}%  (<20%: {'PASS' if pct_unknown<0.20 else 'FAIL'})",
        f"  step3_wall_clock: {gen_elapsed_s:.1f}s  (n_jobs=4)",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_id: {job_id}",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_status_counts}",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success})  PASS={pct_parse_success>=0.99}",
        f"  EUI_plausibility [25,1000]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)})  PASS={pct_plausible>=0.99}",
    ]
    if len(outliers) > 0:
        lines.append(f"  EUI outliers: n={len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    lines += [
        f"  zone_count_integrity: {n_zone_mismatch} mismatches  PASS={n_zone_mismatch==0}",
        "",
        "=== IOD ===",
        f"  n={len(iod_vals)}, mean={iod_vals.mean():.4f}C, p95={iod_vals.quantile(0.95):.4f}C",
        "",
        "=== CBECS 2018 NE VALIDATION GATES (report-only per V-R5-5) ===",
        f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}",
        f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}",
        f"  R2:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}",
        f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}   PASS={cbecs_gates['cbecs_ks_d_pass']}",
        "  Note: CBECS gates are report-only per ruling V-R5-5; FAIL does not block.",
        "",
        "=== HEADLINE NUMBERS (neighbourhood_eui_weighted) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            lines.append(f"  {k}: {v:.2f} kWh/m2/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        lines.append(f"  GWP: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    if mean_iod is not None:
        lines.append(f"  mean_iod_c: {mean_iod:.4f} C")
    if p95_iod is not None:
        lines.append(f"  p95_iod_c: {p95_iod:.4f} C")
    lines.append(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

    if "archetype_id" in parsed.columns:
        lines += ["", "=== ARCHETYPE MIX (simulated success) ==="]
        for arch, cnt in parsed["archetype_id"].value_counts().items():
            lines.append(f"  {arch}: {cnt}")

    lines += ["", "=" * 72, "END REPORT", "=" * 72]
    return "\n".join(lines)


def copy_final_deliverables(results_dir: Path, final_dir: Path, work_base: Path) -> list[Path]:
    final_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in sorted(results_dir.rglob("*")):
        if src.is_file():
            dst = final_dir / src.relative_to(results_dir)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)
    sim_mf_src = work_base / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        dst = final_dir / "04_simulation_manifest.parquet"
        shutil.copy2(sim_mf_src, dst)
        copied.append(dst)
    return copied


def run_cell(cell_name: str) -> None:
    cfg_cell = CELL_CONFIGS[cell_name]
    lat = cfg_cell["lat"]
    lon = cfg_cell["lon"]
    radius_m = cfg_cell["radius_m"]
    state = cfg_cell["state"]
    epsg = cfg_cell["epsg"]

    work_base = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / cell_name
    step3_dir = work_base / "step3"
    sim_out_dir = work_base / "sim_out"
    results_dir = work_base / "results"
    final_dir = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / cell_name
    remote_fleet_dir = f"/speed-scratch/o_iseri/fleets/{cell_name}"

    work_base.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*72}")
    print(f"[{cell_name}] STARTING — centre ({lat}, {lon}) r={radius_m}m")
    print(f"[{cell_name}] Working dir: {work_base}")
    print(f"[{cell_name}] Final dir:   {final_dir}")
    print(f"{'='*72}\n")

    print(f"[{cell_name}] Resolving EPW ...")
    epw_path, epw_station_name = resolve_epw(lat, lon, work_base / "weather")

    gdf_raw = step1_fetch(lat, lon, radius_m, work_base)
    n_fetched = len(gdf_raw)
    print(f"[{cell_name}] Fetched: {n_fetched} buildings (probe lower bound: {cfg_cell['probe_count']})")

    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path, work_base, cell_name)

    t3_start = time.monotonic()
    idf_manifest = step3_generate(gdf_57, schedule_library, step3_dir)
    gen_elapsed = time.monotonic() - t3_start
    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_gen_total = len(idf_manifest)
    print(f"[{cell_name}] Step 3: {n_generated}/{n_gen_total} success, wall={gen_elapsed:.1f}s")

    live_smoke_check(idf_manifest, cell_name)

    print(f"\n[{cell_name}] Shipping fleet to {remote_fleet_dir} ...")
    ship_to_cluster(idf_manifest, epw_path, remote_fleet_dir, work_base)

    job_id = submit_cluster_array(n_generated, remote_fleet_dir, cell_name)

    poll_cluster(job_id, cell_name, poll_interval_s=90)

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    # Use IDF stem (underscore format) for cluster dir names
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    print(f"\n[{cell_name}] Fetching results ...")
    fetch_results(osm_ids, remote_fleet_dir, sim_out_dir)

    repaired = verify_and_repair(osm_ids, sim_out_dir, step3_dir,
                                  remote_fleet_dir, cell_name, epw_path)
    if repaired:
        print(f"[{cell_name}] Repaired and resimulated: {repaired}")

    print(f"\n[{cell_name}] Building simulation manifest ...")
    sim_mf = build_sim_manifest(idf_manifest, sim_out_dir, epw_path, job_id, step3_dir, work_base)

    n_sim_total = len(sim_mf)
    n_sim_success_count = int((sim_mf["status"] == "success").sum())
    n_sim_fail = n_sim_total - n_sim_success_count
    print(f"[{cell_name}] Simulation: {n_sim_success_count}/{n_sim_total} success, {n_sim_fail} failed")
    if n_sim_fail > 0:
        failed_rows = sim_mf[sim_mf["status"] != "success"]
        for _, row in failed_rows.iterrows():
            print(f"  osm_id={row['osm_id']}, error={row['error_summary'][:200]}")
        print(f"[{cell_name}] ZERO-FAIL: still {n_sim_fail} unresolved. STOP.", file=sys.stderr)
        sys.exit(2)

    print(f"\n[{cell_name}] Running Step 5 ...")
    results_gdf, cbecs_gates = step5_results(
        idf_manifest, sim_mf, epw_path, results_dir, work_base, state, epsg, cell_name
    )

    gates_text = write_gates_report(
        idf_manifest, sim_mf, results_gdf, cbecs_gates,
        epw_station_name=epw_station_name,
        gen_elapsed_s=gen_elapsed,
        job_id=job_id,
        gen_success=n_generated,
        gen_total=n_gen_total,
        fetched_count=n_fetched,
        cell_name=cell_name,
        cfg_lat=lat,
        cfg_lon=lon,
        cfg_radius=radius_m,
        results_dir=results_dir,
    )
    gates_report_path = results_dir / f"v12_{cell_name}_gates_report.txt"
    gates_report_path.write_text(gates_text, encoding="utf-8")
    print(f"[{cell_name}] Gates report -> {gates_report_path}")

    copied = copy_final_deliverables(results_dir, final_dir, work_base)
    print(f"[{cell_name}] Copied {len(copied)} files to {final_dir}")
    print(f"\n[{cell_name}] DONE.")
    print(f"  Fetched:   {n_fetched}  (probe lower bound {cfg_cell['probe_count']})")
    print(f"  Generated: {n_generated}/{n_gen_total}")
    print(f"  Simulated: {n_sim_success_count}/{n_sim_total}")
    print(f"  Job ID:    {job_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: py -3 {__file__} <cell_name>")
        print(f"  cell_name must be one of: {list(CELL_CONFIGS)}")
        sys.exit(1)
    cell = sys.argv[1]
    if cell not in CELL_CONFIGS:
        print(f"Unknown cell '{cell}'. Known cells: {list(CELL_CONFIGS)}", file=sys.stderr)
        sys.exit(1)
    run_cell(cell)
