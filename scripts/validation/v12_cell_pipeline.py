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

import gzip
import io
import json
import math
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
    "nyc_centre": {
        "lat": 40.7549, "lon": -73.9840, "radius_m": 500.0,
        "state": "NY", "epsg": 32618,
        "probe_count": 619,  # V10_matrix_proposal.md row 1 (approved 2026-06-11)
    },
}

_floor_rx = _re.compile(r"_F(\d+)_")


class RemoteCommandError(RuntimeError):
    """A remote command failed, timed out, or exited non-zero.

    OPEN-54. Before 2026-08-18 `_ssh` returned `stdout + stderr` and never looked at
    `returncode`, so a failed remote command surfaced later, somewhere else, with the
    evidence already discarded — twice in one run, and both times the transport error
    masked a model verdict that had already been reached.
    """


_ACTIVE_SLURM_STATES = {
    "PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED",
    "CONFIGURING", "COMPLETING",
}


def _ssh(cmd: str, timeout: int = 120, allow_fail: bool = False,
          stdin_data: str | None = None) -> str:
    """Run `cmd` on REMOTE_HOST under `bash -lc` and return stdout + stderr.

    The remote login shell is tcsh, so bash syntax sent bare would silently fail;
    the `bash -lc` wrapper is load-bearing and must not be removed.

    `stdin_data`, if given, is piped to the remote command's stdin (e.g. for a
    `while read` loop) instead of being embedded in `cmd` itself — OPEN-57. Default
    `None` preserves prior behaviour exactly: this path is untouched below, so every
    existing caller (which never passes `stdin_data`) is byte-for-byte unaffected.
    When `stdin_data` is given, it is sent as raw bytes rather than through
    `subprocess.run`'s `text=True` stdin — `text=True` wraps the child's stdin in a
    `TextIOWrapper(newline=None)`, which on Windows silently rewrites every `\n` to
    `os.linesep` (`\r\n`) on write, so a remote `while read o` receives `way_123\r`
    and every `[ -s "$o/..." ]` path test fails silently — OPEN-57's actual second
    cause, found after the stdin remedy alone still read back 0 complete against a
    populated fleet.

    Raises RemoteCommandError on a non-zero remote exit or a timeout. Pass
    `allow_fail=True` only where a non-zero exit is itself a legitimate answer —
    on timeout that returns "" so the caller re-polls rather than concluding.
    """
    argv = ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"]
    try:
        if stdin_data is None:
            result = subprocess.run(
                argv, capture_output=True, text=True, timeout=timeout, input=None,
            )
            stdout, stderr = result.stdout, result.stderr
        else:
            result = subprocess.run(
                argv, capture_output=True, timeout=timeout,
                input=stdin_data.encode("utf-8"),
            )
            stdout = result.stdout.decode("utf-8", errors="replace")
            stderr = result.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        if allow_fail:
            return ""
        partial_stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
        partial_stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        raise RemoteCommandError(
            f"remote command timed out after {timeout}s: {cmd}\n"
            f"partial stdout: {partial_stdout!r}\npartial stderr: {partial_stderr!r}"
        ) from exc
    if result.returncode != 0 and not allow_fail:
        raise RemoteCommandError(
            f"remote command exited {result.returncode}: {cmd}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )
    return stdout + stderr


def _parse_sacct_state_counts(sacct_out: str) -> dict[str, int]:
    """Parse `sacct --format=State --noheader | sort | uniq -c` into {STATE: count}."""
    counts: dict[str, int] = {}
    for line in sacct_out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            counts[parts[1].upper().rstrip("+")] = int(parts[0])
    return counts


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
    print(f"  Step 3: IDF generation (n_jobs=1 serial) for {len(gdf_57)} buildings ...")
    t0 = time.monotonic()
    idf_manifest = run_step3(gdf_57, schedule_library, step3_dir, n_jobs=1)
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
        out = _ssh(
            f"squeue -j {job_id} --noheader 2>/dev/null | wc -l; "
            f"echo SQ_EXIT=${{PIPESTATUS[0]}}",
            timeout=60, allow_fail=True,
        )
        pending_count, sq_exit = -1, None
        for line in out.splitlines():
            s = line.strip()
            if s.startswith("SQ_EXIT="):
                sq_exit = s.split("=", 1)[1]
            elif s.isdigit() and pending_count < 0:
                pending_count = int(s)
        sacct_out = _ssh(
            f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c",
            timeout=60, allow_fail=True,
        )
        print(f"  [{time.strftime('%H:%M:%S')}] squeue count={pending_count} (exit {sq_exit})  "
              f"sacct states: {sacct_out.strip()}")

        # OPEN-54: `squeue | wc -l` reports 0 both when the array is finished and when
        # squeue itself failed with stderr eaten by 2>/dev/null, so a controller hiccup
        # used to read as 'array complete'. Completion is now concluded only when sacct
        # positively corroborates it.
        if pending_count != 0:
            continue
        states = _parse_sacct_state_counts(sacct_out)
        if not states:
            print("  squeue says 0 but sacct returned no states — not concluding "
                  "completion; re-polling.")
            continue
        active = sum(n for st, n in states.items() if st in _ACTIVE_SLURM_STATES)
        if active:
            print(f"  squeue says 0 but sacct still shows {active} active task(s) "
                  f"{states} — re-polling.")
            continue
        print(f"[{cell_name}] Job {job_id}: no tasks in queue, sacct corroborates: {states}")
        sacct_full = _ssh(
            f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null",
            timeout=60, allow_fail=True,
        )
        print(sacct_full)
        break


def fetch_results(osm_ids: list[str], remote_fleet_dir: str, sim_out_dir: Path) -> None:
    print(f"  Fetching results from cluster for {len(osm_ids)} buildings ...")
    sim_out_dir.mkdir(parents=True, exist_ok=True)

    batch_size = 50
    batches = [osm_ids[i:i + batch_size] for i in range(0, len(osm_ids), batch_size)]
    n_batches = len(batches)
    print(f"  Splitting into {n_batches} batch(es) of up to {batch_size} buildings each.")

    for i, batch in enumerate(batches):
        tgz = sim_out_dir.parent / f"fetch_batch_{i:03d}.tgz"
        paths = " ".join(
            f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio"
            for oid in batch
        )
        remote_cmd = f"cd {remote_fleet_dir}/out && tar czf - --ignore-failed-read {paths}"

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            t0 = time.monotonic()
            with open(tgz, "wb") as fh:
                proc = subprocess.Popen(
                    ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
                    stdout=fh, stderr=subprocess.PIPE,
                )
                _, stderr_data = proc.communicate(timeout=3600)
            elapsed = time.monotonic() - t0
            mb = tgz.stat().st_size / 1e6

            rc_ok = (proc.returncode == 0)
            try:
                with gzip.open(tgz, "rb") as fh:
                    while fh.read(1 << 20):
                        pass
                gz_ok = True
            except Exception:
                gz_ok = False

            if rc_ok and gz_ok:
                break

            diag = "truncated" if rc_ok else f"ssh rc={proc.returncode}"
            print(
                f"  batch {i:03d} attempt {attempt}/{max_attempts} FAILED: "
                f"{diag}, {mb:.1f} MB, {elapsed:.0f}s"
            )
            if attempt == max_attempts:
                print(
                    f"  fetch_results: batch {i:03d} failed after {max_attempts} attempts. STOP.",
                    file=sys.stderr,
                )
                sys.exit(1)

        with tarfile.open(tgz, "r:gz") as tf:
            tf.extractall(str(sim_out_dir))
        try:
            tgz.unlink()
        except PermissionError:
            pass

    print(f"  fetched: {len(list(sim_out_dir.rglob('eplusout.end')))} .end files in {n_batches} batches")


def verify_and_repair(osm_ids: list[str], sim_out_dir: Path, step3_dir: Path,
                      remote_fleet_dir: str, cell_name: str, epw_path: Path,
                      gdf: "gpd.GeoDataFrame | None" = None,
                      schedule_library: "dict | None" = None) -> list[str]:
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
        # B2: defer to run_cell's drop-tolerance gate rather than hard-exit. The still-failed
        # buildings keep their fatal .end → build_sim_manifest marks them failed → the single
        # max(5,1%) tolerance in run_cell either drops (≤tol) or stops (>tol).
        print(f"  No IDFs could be zero-area-repaired; deferring {len(failed_ids)} "
              f"building(s) to B2 drop tolerance.", file=sys.stderr)
        return []

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

    if still_failed and gdf is not None and schedule_library is not None:
        # Reroute-aware second pass: regenerate with forced one_zone_per_floor then re-ship+re-sim.
        print(f"\n  Reroute-aware repair: {len(still_failed)} buildings rerouting to one_zone_per_floor ...")
        from openubem.idf.builder import BuildingIDF
        from geomeppy import IDF as GeomIDF
        from eppy.modeleditor import IDDAlreadySetError as _IDDErr
        import openubem.config as _cfg
        try:
            GeomIDF.setiddname(str(_cfg.ENERGYPLUS_IDD_PATH))
        except _IDDErr:
            pass
        reroute_ids = []
        for oid in still_failed:
            # osm_id stored in gdf may use "/" while IDF stem uses "_": try both.
            osm_id_slash = oid.replace("_", "/", 1) if not oid.startswith("way/") else oid
            mask = (gdf["osm_id"].astype(str) == oid) | (gdf["osm_id"].astype(str) == osm_id_slash)
            matches = gdf[mask]
            if matches.empty:
                print(f"    {oid}: not found in gdf — cannot reroute")
                continue
            row = matches.iloc[0].copy()
            # Force one_zone_per_floor by monkey-patching decide_zoning_strategy on the row.
            from openubem.geometry.zoning import decide_zoning_strategy as _dzs, build_zones as _bz
            orig_dzs = _dzs.__module__
            import openubem.idf.builder as _builder_mod
            _orig = _builder_mod.decide_zoning_strategy
            _builder_mod.decide_zoning_strategy = lambda arch, area, floors, *_a, **_k: "one_zone_per_floor"
            try:
                result = BuildingIDF(row).build(gdf, schedule_library, step3_dir)
            finally:
                _builder_mod.decide_zoning_strategy = _orig
            if result.get("generation_status") in ("success", "fallback_bbox"):
                idf_repair_path = Path(result["idf_path"])
                dst = repair_dir / idf_repair_path.name
                shutil.copy2(idf_repair_path, dst)
                reroute_ids.append(oid)
                print(f"    {oid}: rerouted to one_zone_per_floor -> {dst}")
            else:
                print(f"    {oid}: reroute failed with status={result.get('generation_status')}", file=sys.stderr)

        if reroute_ids:
            reroute_fleet_dir = remote_fleet_dir + "_reroute"
            _ssh(f"mkdir -p {reroute_fleet_dir}/idfs {reroute_fleet_dir}/weather {reroute_fleet_dir}/out")
            reroute_lst_local = step3_dir / "reroute_fleet.lst"
            reroute_lst_local.write_bytes(("\n".join(reroute_ids) + "\n").encode("utf-8"))
            subprocess.run(["scp", str(reroute_lst_local),
                            f"{REMOTE_HOST}:{reroute_fleet_dir}/fleet.lst"], check=True, timeout=30)
            subprocess.run(["scp", str(epw_path),
                            f"{REMOTE_HOST}:{reroute_fleet_dir}/weather/"], check=True, timeout=60)
            reroute_tar = io.BytesIO()
            with tarfile.open(fileobj=reroute_tar, mode="w:gz") as tf:
                for oid in reroute_ids:
                    tf.add(str(repair_dir / f"{oid}.idf"), arcname=f"idfs/{oid}.idf")
            reroute_tar.seek(0)
            proc2 = subprocess.Popen(
                ["ssh", REMOTE_HOST, f"bash -lc 'cd {reroute_fleet_dir} && tar xz'"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            proc2.stdin.write(reroute_tar.read())
            proc2.stdin.close()
            proc2.wait(timeout=120)
            reroute_job = submit_cluster_array(len(reroute_ids), reroute_fleet_dir, cell_name + "_reroute")
            poll_cluster(reroute_job, cell_name + "_reroute", poll_interval_s=90)
            fetch_results(reroute_ids, reroute_fleet_dir, sim_out_dir)
            still_failed = [
                oid for oid in reroute_ids
                if not (sim_out_dir / oid / "eplusout.end").exists()
                or "EnergyPlus Completed Successfully" not in (sim_out_dir / oid / "eplusout.end").read_text(errors="replace")
            ]
            # B2: any building still unrepairable after reroute keeps its fatal .end and is
            # deferred to run_cell's drop-tolerance gate (the single fail-tolerance authority).
            if still_failed:
                print(f"  {len(still_failed)} building(s) still failed after reroute "
                      f"(deferred to B2 drop tolerance): {still_failed}", file=sys.stderr)
            repaired.extend([oid for oid in reroute_ids if oid not in still_failed])
        elif still_failed:
            print(f"  No reroute candidates for {len(still_failed)} building(s) "
                  f"(deferred to B2 drop tolerance): {still_failed}", file=sys.stderr)
    elif still_failed:
        print(f"  {len(still_failed)} building(s) still failed after repair "
              f"(deferred to B2 drop tolerance): {still_failed}", file=sys.stderr)

    print(f"  Repair pass complete: {len(repaired)} building(s) recovered.")
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
            from openubem.results.err_parse import first_severe
            error_summary = first_severe(etxt)

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


def _remote_results_complete(osm_ids: list[str], remote_fleet_dir: str) -> bool:
    """True iff every oid already has a non-empty eplusout.sql AND a 'Completed Successfully'
    eplusout.end in {remote_fleet_dir}/out — i.e. the cluster already simulated this fleet."""
    if not osm_ids:
        return False
    # OPEN-57: the id list used to be embedded in the probe string itself; at fleet
    # sizes above ~565 ids that made the remote command long enough that tcsh (the
    # login shell `_ssh` hands it to) failed to parse it at all (`Unmatched '.`), so
    # every large fleet silently read back as 0/N complete. Sending ids on stdin
    # keeps the probe a few hundred characters regardless of fleet size.
    probe = (
        f"cd {remote_fleet_dir}/out 2>/dev/null || exit 0; "
        f"n=0; while read o; do "
        f'if [ -s "$o/eplusout.sql" ] && grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end" 2>/dev/null; '
        f"then n=$((n+1)); fi; done; echo COMPLETE=$n"
    )
    out = _ssh(probe, timeout=600, stdin_data="\n".join(osm_ids) + "\n")
    m = _re.search(r"COMPLETE=(\d+)", out)
    n_complete = int(m.group(1)) if m else 0
    print(f"  [{remote_fleet_dir.rsplit('/',1)[-1]}] remote completeness probe: {n_complete}/{len(osm_ids)} complete")
    return n_complete == len(osm_ids)


def run_cell(cell_name: str, output_subdir: str = "cases") -> None:
    cfg_cell = CELL_CONFIGS[cell_name]
    lat = cfg_cell["lat"]
    lon = cfg_cell["lon"]
    radius_m = cfg_cell["radius_m"]
    state = cfg_cell["state"]
    epsg = cfg_cell["epsg"]

    work_base = Path(tempfile.gettempdir()) / "ubem_validation" / output_subdir / cell_name
    step3_dir = work_base / "step3"
    sim_out_dir = work_base / "sim_out"
    results_dir = work_base / "results"
    final_dir = REPO / "docs" / "validations" / "overAll" / "results" / output_subdir / cell_name
    # Use a distinct remote fleet dir per output_subdir to avoid collision with R5 fleet dirs.
    fleet_tag = cell_name if output_subdir == "cases" else f"{output_subdir}_{cell_name}"
    remote_fleet_dir = f"/speed-scratch/o_iseri/fleets/{fleet_tag}"

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

    # Clear stale staging/sim dirs so re-runs never ship stale IDFs or collide with old sim output.
    for _stale_dir in (work_base / "fleet_staging", sim_out_dir):
        if _stale_dir.exists():
            shutil.rmtree(_stale_dir)
            print(f"[{cell_name}] Cleared {_stale_dir.name} for fresh run.")
    print(f"[{cell_name}] cleared fleet_staging/sim_out (step1/step2/EPW caches preserved).")

    # Mandatory fresh IDF regen: clear any stale manifest so IDFs rebuild from current code+data.
    stale_manifest = step3_dir / "03_idf_manifest.parquet"
    if stale_manifest.exists():
        stale_manifest.unlink()
        print(f"[{cell_name}] Cleared stale IDF manifest for fresh regen.")

    t3_start = time.monotonic()
    idf_manifest = step3_generate(gdf_57, schedule_library, step3_dir)
    gen_elapsed = time.monotonic() - t3_start
    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_gen_total = len(idf_manifest)
    print(f"[{cell_name}] Step 3: {n_generated}/{n_gen_total} success, wall={gen_elapsed:.1f}s")

    live_smoke_check(idf_manifest, cell_name)

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    # Use IDF stem (underscore format) for cluster dir names
    osm_ids = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]

    # T17-H2: if the cluster already holds complete results for every oid, skip
    # ship+submit+poll (resumable / avoids redundant re-simulation).
    if _remote_results_complete(osm_ids, remote_fleet_dir):
        print(f"[{cell_name}] REUSE: all {len(osm_ids)} results already complete on cluster — skipping ship/submit/poll.")
        job_id = "REUSED_REMOTE"
    else:
        print(f"\n[{cell_name}] Shipping fleet to {remote_fleet_dir} ...")
        ship_to_cluster(idf_manifest, epw_path, remote_fleet_dir, work_base)
        job_id = submit_cluster_array(n_generated, remote_fleet_dir, cell_name)
        poll_cluster(job_id, cell_name, poll_interval_s=90)

    print(f"\n[{cell_name}] Fetching results ...")
    fetch_results(osm_ids, remote_fleet_dir, sim_out_dir)

    repaired = verify_and_repair(osm_ids, sim_out_dir, step3_dir,
                                  remote_fleet_dir, cell_name, epw_path,
                                  gdf=gdf_57, schedule_library=schedule_library)
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
            print(f"  osm_id={row['osm_id']}, error={row.get('error_summary', '')[:200]}")
        # R-B2: tolerate up to max(5, 1%) failures — log them, do not halt (B2)
        max_tolerated = max(5, math.ceil(0.01 * n_sim_total))
        if n_sim_fail <= max_tolerated:
            results_dir.mkdir(parents=True, exist_ok=True)  # Step 5 makes this later; B2 writes first
            drop_path = results_dir / "dropped_buildings.csv"
            failed_rows.to_csv(drop_path, index=False)
            print(f"[{cell_name}] DROPPED {n_sim_fail} buildings (<= tolerance {max_tolerated}) -> {drop_path}")
            sim_mf = sim_mf[sim_mf["status"] == "success"].copy()
        else:
            print(f"[{cell_name}] ZERO-FAIL: {n_sim_fail} failures exceed tolerance {max_tolerated}. STOP.", file=sys.stderr)
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cell_name", choices=list(CELL_CONFIGS))
    ap.add_argument("--output-subdir", default="cases",
                    help="Sub-dir under results/ for final deliverables (default: cases)")
    args = ap.parse_args()
    run_cell(args.cell_name, output_subdir=args.output_subdir)
