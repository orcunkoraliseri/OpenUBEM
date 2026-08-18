"""V11 — NYC city-centre end-to-end pipeline (Steps 1-5).

Pilot cell: centre (40.7549, -73.9840), radius 500 m, expected CZ 4A.
Steps 1-3 run locally; EnergyPlus on Speed cluster; Step 5 locally from fetched results.

Outputs (final deliverables) → docs/validations/overAll/results/cases/nyc_centre/
Raw working dir              → %TEMP%/ubem_validation/cases/nyc_centre/
Remote fleet dir             → /speed-scratch/o_iseri/fleets/nyc_centre/
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd
import re as _re
from shapely.geometry import Point

NYC_LAT = 40.7549
NYC_LON = -73.9840
NYC_RADIUS_M = 500.0
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/nyc_centre"
CELL_NAME = "nyc_centre"

WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"

FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

EPW_CACHE = Path.home() / "AppData" / "Local" / "openubem" / "epw_cache"
CBECS_PATH = REPO / "inputs" / "reports" / "cbecs_2018_new_england_eui.csv"

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout + result.stderr


def _scp_put(local: Path, remote: str, timeout: int = 300) -> None:
    subprocess.run(["scp", "-r", str(local), f"{REMOTE_HOST}:{remote}"],
                   check=True, timeout=timeout)


def _scp_get(remote: str, local: Path, timeout: int = 600) -> None:
    local.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-r", f"{REMOTE_HOST}:{remote}", str(local)],
                   check=True, timeout=timeout)


def step1_fetch(gdf_path: Path) -> gpd.GeoDataFrame:
    if gdf_path.exists():
        print(f"[V11] Step 1: loading cached GDF from {gdf_path}")
        return gpd.read_file(str(gdf_path))

    print(f"[V11] Step 1: fetching OSM buildings at ({NYC_LAT}, {NYC_LON}) r={NYC_RADIUS_M}m ...")
    t0 = time.monotonic()
    from openubem.acquisition.osm_fetcher import ingest_buildings
    gdf = ingest_buildings(location=(NYC_LAT, NYC_LON), radius_m=NYC_RADIUS_M)
    print(f"  fetched {len(gdf)} buildings ({time.monotonic()-t0:.1f}s)")
    gdf_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(str(gdf_path), driver="GPKG")
    print(f"  saved -> {gdf_path}")
    return gdf


def step2_classify_enrich(gdf_raw: gpd.GeoDataFrame, epw_path: Path) -> tuple[gpd.GeoDataFrame, object]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition.climate_zone import assign_climate_zones
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    gdf_raw2 = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")

    print(f"[V11] Step 2: classify ({len(gdf_raw2)} buildings) ...")
    t0 = time.monotonic()
    bc = BuildingClassifier()
    gdf_26 = bc.classify(gdf_raw2)
    n_unknown = int((gdf_26["archetype_id"] == "OpenUBEMUnknown").sum())
    print(f"  classified: {len(gdf_26)}, unknown={n_unknown} ({time.monotonic()-t0:.1f}s)")
    print("  archetype distribution:")
    print(gdf_26["archetype_id"].value_counts().to_string())

    print("[V11] Step 2.1: climate enrichment ...")
    t0 = time.monotonic()
    zone_df = assign_climate_zones(gdf_26)
    gdf_29 = gdf_26.copy()
    gdf_29["climate_zone"] = pd.Categorical(zone_df["climate_zone"].values, categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_29["epw_path"] = str(epw_path)
    gdf_29["provenance_climate_zone"] = pd.Categorical(
        zone_df["provenance_climate_zone"].values,
        categories=["ASHRAE_STANDARD", "HEURISTIC"],
    )
    print(f"  CZ distribution: {zone_df['climate_zone'].value_counts().to_dict()} ({time.monotonic()-t0:.1f}s)")

    sidecar = pd.DataFrame({
        "osm_id": gdf_26["osm_id"].values,
        "climate_zone": zone_df["climate_zone"].values,
        "climate_zone_method": zone_df["climate_zone_method"].values,
        "county_geoid": zone_df["county_geoid"].values,
        "state": zone_df["state"].values,
        "epw_path": str(epw_path),
        "provenance_climate_zone": zone_df["provenance_climate_zone"].values,
    })
    sidecar.to_parquet(str(WORK_BASE / "02a_climate_epw.parquet"), index=False)

    print("[V11] Step 2.2: semantic enrichment ...")
    t0 = time.monotonic()
    gdf_57, schedule_library = enrich_semantics(gdf_29)
    print(f"  enriched: {len(gdf_57)} buildings ({time.monotonic()-t0:.1f}s)")
    return gdf_57, schedule_library


def step3_generate(gdf_57: gpd.GeoDataFrame, schedule_library: object) -> pd.DataFrame:
    from openubem.idf.builder import run_step3

    STEP3_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = STEP3_DIR / "03_idf_manifest.parquet"
    if manifest_path.exists():
        print(f"[V11] Step 3: loading cached manifest from {manifest_path}")
        return pd.read_parquet(manifest_path)

    print(f"[V11] Step 3: IDF generation (n_jobs=4) for {len(gdf_57)} buildings ...")
    t0 = time.monotonic()
    idf_manifest = run_step3(gdf_57, schedule_library, STEP3_DIR, n_jobs=4)
    elapsed = time.monotonic() - t0
    status_counts = idf_manifest["generation_status"].value_counts().to_dict()
    n_success = status_counts.get("success", 0)
    n_total = len(idf_manifest)
    print(f"  generated: {n_success}/{n_total} IDFs in {elapsed:.1f}s (n_jobs=4)")
    print(f"  status counts: {status_counts}")
    return idf_manifest


def live_smoke_check(idf_manifest: pd.DataFrame, gdf_26: gpd.GeoDataFrame) -> None:
    n_total = len(idf_manifest)
    n_success = int((idf_manifest["generation_status"] == "success").sum())
    pct_gen = n_success / n_total if n_total > 0 else 0.0
    n_unknown = int((idf_manifest["archetype_id"] == "OpenUBEMUnknown").sum())
    pct_unknown = n_unknown / n_total if n_total > 0 else 0.0

    print("\n[V11] LIVE_SMOKE gates:")
    print(f"  generation success: {n_success}/{n_total} = {pct_gen*100:.1f}%  (gate >=95%: {'PASS' if pct_gen >= 0.95 else 'FAIL'})")
    print(f"  Unknown archetype: {n_unknown}/{n_total} = {pct_unknown*100:.1f}%  (gate <20%: {'PASS' if pct_unknown < 0.20 else 'FAIL'})")

    if pct_gen < 0.95:
        print("[V11] LIVE_SMOKE FAIL: generation success below 95%. STOP.", file=sys.stderr)
        sys.exit(1)
    if pct_unknown >= 0.20:
        print("[V11] LIVE_SMOKE FAIL: Unknown archetype share >= 20%. STOP.", file=sys.stderr)
        sys.exit(1)
    print("[V11] LIVE_SMOKE: both gates PASS. Proceeding to cluster ship.")


def ship_to_cluster(idf_manifest: pd.DataFrame, epw_path: Path) -> None:
    print(f"\n[V11] Shipping fleet to cluster: {REMOTE_FLEET_DIR} ...")

    fleet_dir_local = WORK_BASE / "fleet_staging"
    idfs_local = fleet_dir_local / "idfs"
    weather_local = fleet_dir_local / "weather"
    idfs_local.mkdir(parents=True, exist_ok=True)
    weather_local.mkdir(parents=True, exist_ok=True)

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids = [str(r["osm_id"]) for _, r in success_rows.iterrows()]

    for _, row in success_rows.iterrows():
        src = Path(str(row["idf_path"]))
        dst = idfs_local / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

    shutil.copy2(epw_path, weather_local / epw_path.name)

    fleet_lst = fleet_dir_local / "fleet.lst"
    fleet_lst.write_text("\n".join(osm_ids) + "\n", encoding="utf-8")

    print(f"  fleet size: {len(osm_ids)} buildings")
    print(f"  creating remote dir ...")
    _ssh(f"mkdir -p {REMOTE_FLEET_DIR}/idfs {REMOTE_FLEET_DIR}/weather {REMOTE_FLEET_DIR}/out")

    print("  uploading fleet.lst ...")
    subprocess.run(["scp", str(fleet_lst), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/fleet.lst"],
                   check=True, timeout=60)

    print("  uploading EPW ...")
    subprocess.run(["scp", str(weather_local / epw_path.name),
                    f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/weather/"],
                   check=True, timeout=120)

    print("  uploading IDFs (tar stream) ...")
    import tarfile, io
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        for idf_file in sorted(idfs_local.glob("*.idf")):
            tf.add(str(idf_file), arcname=f"idfs/{idf_file.name}")
    tar_buf.seek(0)
    untar_cmd = f"cd {REMOTE_FLEET_DIR} && tar xz"
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc '{untar_cmd}'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.stdin.write(tar_buf.read())
    proc.stdin.close()
    proc.wait(timeout=300)
    print("  upload complete.")


def submit_cluster_array(n_jobs: int) -> str:
    sbatch_local = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"
    sbatch_remote = "/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet.sbatch"

    upload = subprocess.run(
        ["scp", str(sbatch_local), f"{REMOTE_HOST}:{sbatch_remote}"],
        capture_output=True, text=True, timeout=60
    )
    if upload.returncode != 0:
        print(f"  sbatch upload warning: {upload.stderr.strip()}")

    submit_cmd = (
        f"sbatch --array=1-{n_jobs}%32 "
        f"--export=FLEET_DIR={REMOTE_FLEET_DIR} "
        f"--job-name=openubem_{CELL_NAME} "
        f"--output={REMOTE_FLEET_DIR}/openubem_{CELL_NAME}_%A_%a.log "
        f"{sbatch_remote}"
    )
    print(f"[V11] Submitting SLURM array: {submit_cmd}")
    out = _ssh(submit_cmd, timeout=60)
    print(f"  sbatch output: {out.strip()}")

    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"[V11] ERROR: could not parse job ID from sbatch output:\n{out}", file=sys.stderr)
        sys.exit(1)
    print(f"[V11] Job ID: {job_id}")
    return job_id


def poll_cluster(job_id: str, n_jobs: int, poll_interval_s: int = 90) -> None:
    print(f"[V11] Polling job {job_id} (poll every {poll_interval_s}s) ...")
    while True:
        time.sleep(poll_interval_s)
        out = _ssh(f"squeue -j {job_id} --noheader 2>/dev/null | wc -l", timeout=60)
        pending_count = int(out.strip()) if out.strip().isdigit() else -1
        sacct_out = _ssh(
            f"sacct -j {job_id} --format=State --noheader 2>/dev/null | sort | uniq -c",
            timeout=60
        )
        print(f"  [{time.strftime('%H:%M:%S')}] squeue count={pending_count}  sacct states: {sacct_out.strip()}")
        if pending_count == 0:
            print(f"[V11] Job {job_id}: no tasks in queue. Checking completion ...")
            sacct_full = _ssh(
                f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null",
                timeout=60
            )
            print(sacct_full)
            break


def fetch_results(job_id: str, osm_ids: list[str]) -> None:
    print(f"\n[V11] Fetching results from cluster for {len(osm_ids)} buildings ...")
    SIM_OUT_DIR.mkdir(parents=True, exist_ok=True)

    fetch_cmd = (
        f"cd {REMOTE_FLEET_DIR}/out && "
        f"tar czf - --ignore-failed-read "
        + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio" for oid in osm_ids)
    )
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    import tarfile, io
    stdout_data, stderr_data = proc.communicate(timeout=600)
    if stderr_data:
        print(f"  fetch stderr: {stderr_data.decode(errors='replace')[:500]}")

    if stdout_data:
        with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
            tf.extractall(str(SIM_OUT_DIR))
        print(f"  extracted {len(list(SIM_OUT_DIR.rglob('eplusout.end')))} .end files")
    else:
        print("  WARNING: no data received from tar stream — trying scp fallback")
        for oid in osm_ids[:5]:
            _scp_get(f"{REMOTE_FLEET_DIR}/out/{oid}", SIM_OUT_DIR / oid, timeout=60)


def build_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path, job_id: str) -> pd.DataFrame:
    sys.path.insert(0, str(REPO / "scripts" / "cluster"))
    from make_manifest_from_cluster import build_manifest as _build_manifest

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids_int = [int(r["osm_id"]) for _, r in success_rows.iterrows()]
    osm_ids_str = [str(oid) for oid in osm_ids_int]

    sim_mf = _build_manifest(
        fleet_dir=SIM_OUT_DIR,
        idf_source_dir=STEP3_DIR / "idfs",
        epw_path=epw_path,
        job_id=job_id,
        osm_ids=osm_ids_str,
    )
    manifest_path = WORK_BASE / "04_simulation_manifest.parquet"
    sim_mf.to_parquet(str(manifest_path), index=False)
    status_counts = sim_mf["status"].value_counts().to_dict()
    print(f"[V11] Sim manifest: {len(sim_mf)} rows, status={status_counts}")
    return sim_mf


def _build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    rows = []
    for _, idf_row in idf_mf.iterrows():
        osm_id = str(idf_row["osm_id"])
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == osm_id]

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
            "osm_id": osm_id,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })
    return gpd.GeoDataFrame(rows, crs="EPSG:32618")


def step5_results(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame, epw_path: Path) -> tuple[gpd.GeoDataFrame, dict]:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("[V11] Building enriched GDF from SQL Zones ...")
    enriched_gdf = _build_enriched_gdf(idf_manifest, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    print("[V11] Step 5: aggregate_results ...")
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_manifest, enriched_gdf,
            RESULTS_DIR,
            state="NY",
            make_figures=True,
            ep_version="23.1.0",
        )
    print(f"  aggregate_results done in {time.monotonic()-t0:.1f}s")

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
    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())

    print("\n[V11] F12 GATE SUMMARY:")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}), PASS={pct_parse_success>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}), PASS={pct_plausible>=0.99}")
    if len(outliers) > 0:
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch}, PASS={n_zone_mismatch==0}")
    print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")

    cbecs_gates = compute_validation_gates(results_gdf, reference_path=CBECS_PATH)
    print("\n[V11] CBECS 2018 NE VALIDATION GATES (report-only):")
    print(f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}% PASS={cbecs_gates['cbecs_cv_rmse_pass']}")
    print(f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%  PASS={cbecs_gates['cbecs_nmbe_pass']}")
    print(f"  R²:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}")
    print(f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}  PASS={cbecs_gates['cbecs_ks_d_pass']}")

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    print("\n[V11] HEADLINE NUMBERS:")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f} kWh/m²/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    if mean_iod is not None:
        print(f"  mean_iod_c: {mean_iod:.4f} °C")
    if p95_iod is not None:
        print(f"  p95_iod_c: {p95_iod:.4f} °C")
    print(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

    print("\n[V11] Archetype distribution (simulated success):")
    if "archetype_id" in parsed.columns:
        print(parsed["archetype_id"].value_counts().to_string())

    return results_gdf, cbecs_gates


def write_gates_report(
    idf_manifest: pd.DataFrame,
    sim_mf: pd.DataFrame,
    results_gdf: gpd.GeoDataFrame,
    cbecs_gates: dict,
    epw_station_name: str,
    gen_elapsed_s: float,
    job_id: str,
    gen_success: int,
    gen_total: int,
) -> str:
    from openubem import config as cfg

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
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

    lines = ["=" * 72,
             "V11 NYC CITY-CENTRE GATES REPORT",
             f"  Cell:   NYC city-centre  ({NYC_LAT}, {NYC_LON}) r={NYC_RADIUS_M}m",
             f"  EPW:    {epw_station_name}",
             f"  Date:   2026-06-11",
             "=" * 72,
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
        f"  n={len(iod_vals)}, mean={iod_vals.mean():.4f}°C, p95={iod_vals.quantile(0.95):.4f}°C",
        "",
        "=== CBECS 2018 NE VALIDATION GATES (report-only) ===",
        f"  CV(RMSE): {cbecs_gates['cbecs_cv_rmse']:.3f}%  PASS={cbecs_gates['cbecs_cv_rmse_pass']}",
        f"  NMBE:     {cbecs_gates['cbecs_nmbe']:.3f}%   PASS={cbecs_gates['cbecs_nmbe_pass']}",
        f"  R²:       {cbecs_gates['cbecs_r2']}        PASS={cbecs_gates['cbecs_r2_pass']}",
        f"  KS_D:     {cbecs_gates['cbecs_ks_d']:.4f}   PASS={cbecs_gates['cbecs_ks_d_pass']}",
        "  Note: CBECS gates are report-only per ruling V-R5-5; FAIL does not block.",
        "",
        "=== HEADLINE NUMBERS (neighbourhood_eui_weighted) ===",
    ]
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            lines.append(f"  {k}: {v:.2f} kWh/m²/yr")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        lines.append(f"  GWP: {gwp:,.0f} kgCO2e")
    mean_iod = summary.get("mean_iod_c")
    p95_iod = summary.get("p95_iod_c")
    if mean_iod is not None:
        lines.append(f"  mean_iod_c: {mean_iod:.4f} °C")
    if p95_iod is not None:
        lines.append(f"  p95_iod_c: {p95_iod:.4f} °C")
    lines.append(f"  n_buildings_by_status: {summary.get('n_buildings_by_status')}")

    if "archetype_id" in parsed.columns:
        lines += ["", "=== ARCHETYPE MIX (simulated success) ==="]
        for arch, cnt in parsed["archetype_id"].value_counts().items():
            lines.append(f"  {arch}: {cnt}")

    lines += ["", "=" * 72, "END REPORT", "=" * 72]
    return "\n".join(lines)


def copy_final_deliverables() -> list[Path]:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in sorted(RESULTS_DIR.rglob("*")):
        if src.is_file():
            dst = FINAL_DIR / src.relative_to(RESULTS_DIR)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)
    sim_mf_src = WORK_BASE / "04_simulation_manifest.parquet"
    if sim_mf_src.exists():
        dst = FINAL_DIR / "04_simulation_manifest.parquet"
        shutil.copy2(sim_mf_src, dst)
        copied.append(dst)
    return copied


def main() -> None:
    WORK_BASE.mkdir(parents=True, exist_ok=True)
    print(f"[V11] Working dir: {WORK_BASE}")
    print(f"[V11] Final deliverables: {FINAL_DIR}")

    # ── EPW resolution ─────────────────────────────────────────────────────────
    print("\n[V11] Resolving EPW for NYC centre ...")
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw

    epw_weather_dir = WORK_BASE / "weather"
    stations = load_stations()
    station, dist_km = resolve_station(NYC_LAT, NYC_LON, stations)
    print(f"  Resolved station: {station['station_id']} ({station.get('name', 'N/A')}) at {dist_km:.1f} km")
    epw_path = fetch_epw(station, output_dir=WORK_BASE)
    print(f"  EPW path: {epw_path}")
    epw_station_name = station.get("name", str(station["station_id"]))

    with open(epw_path, encoding="utf-8", errors="replace") as fh:
        first_line = fh.readline()
    print(f"  EPW header: {first_line.strip()[:120]}")

    # ── Step 1: OSM fetch ──────────────────────────────────────────────────────
    gdf_path = WORK_BASE / "01_buildings.gpkg"
    gdf_raw = step1_fetch(gdf_path)
    n_fetched = len(gdf_raw)
    print(f"[V11] Fetched: {n_fetched} buildings")

    # ── Steps 2-2.2: classify + enrich ────────────────────────────────────────
    gdf_57, schedule_library = step2_classify_enrich(gdf_raw, epw_path)
    n_enriched = len(gdf_57)

    # ── Step 3: IDF generation with n_jobs=4 ──────────────────────────────────
    t3_start = time.monotonic()
    idf_manifest = step3_generate(gdf_57, schedule_library)
    gen_elapsed = time.monotonic() - t3_start
    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    n_gen_total = len(idf_manifest)
    print(f"[V11] Step 3: {n_generated}/{n_gen_total} success, wall={gen_elapsed:.1f}s")

    # ── LIVE_SMOKE ─────────────────────────────────────────────────────────────
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS
    live_smoke_check(idf_manifest, gdf_raw)

    # ── Ship to cluster ────────────────────────────────────────────────────────
    ship_to_cluster(idf_manifest, epw_path)

    # ── Submit SLURM array ────────────────────────────────────────────────────
    job_id = submit_cluster_array(n_generated)

    # ── Poll ──────────────────────────────────────────────────────────────────
    poll_cluster(job_id, n_generated, poll_interval_s=90)

    # ── Fetch results ─────────────────────────────────────────────────────────
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_ids = [str(int(r["osm_id"])) for _, r in success_rows.iterrows()]
    fetch_results(job_id, osm_ids)

    # ── Build simulation manifest ─────────────────────────────────────────────
    sim_mf = build_sim_manifest(idf_manifest, epw_path, job_id)

    # ── Zero-fail check ───────────────────────────────────────────────────────
    n_sim_total = len(sim_mf)
    n_sim_success = int((sim_mf["status"] == "success").sum())
    n_sim_fail = n_sim_total - n_sim_success
    print(f"\n[V11] Simulation: {n_sim_success}/{n_sim_total} success, {n_sim_fail} failed")

    if n_sim_fail > 0:
        failed_rows = sim_mf[sim_mf["status"] != "success"]
        print(f"[V11] ZERO-FAIL violation: {n_sim_fail} failed buildings:")
        for _, row in failed_rows.iterrows():
            print(f"  osm_id={row['osm_id']}, error={row['error_summary'][:200]}")
        print("[V11] Per zero-fail mandate: must diagnose and fix. Exiting for manual remediation.")
        sys.exit(2)

    # ── Step 5 ────────────────────────────────────────────────────────────────
    results_gdf, cbecs_gates = step5_results(idf_manifest, sim_mf, epw_path)

    # ── Gates report ──────────────────────────────────────────────────────────
    gates_text = write_gates_report(
        idf_manifest, sim_mf, results_gdf, cbecs_gates,
        epw_station_name=epw_station_name,
        gen_elapsed_s=gen_elapsed,
        job_id=job_id,
        gen_success=n_generated,
        gen_total=n_gen_total,
    )
    gates_report_path = RESULTS_DIR / "v11_gates_report.txt"
    gates_report_path.write_text(gates_text, encoding="utf-8")
    print(f"\n[V11] Gates report → {gates_report_path}")

    # ── Copy final deliverables ────────────────────────────────────────────────
    copied = copy_final_deliverables()
    print(f"[V11] Copied {len(copied)} files to {FINAL_DIR}")

    print("\n[V11] DONE — pilot cell nyc_centre complete.")
    print(f"  Fetched:   {n_fetched}")
    print(f"  Enriched:  {n_enriched}")
    print(f"  Generated: {n_generated}/{n_gen_total}")
    print(f"  Simulated: {n_sim_success}/{n_sim_total}")
    print(f"  Job ID:    {job_id}")


if __name__ == "__main__":
    main()
