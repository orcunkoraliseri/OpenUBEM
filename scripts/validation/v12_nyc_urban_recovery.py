"""V12 nyc_urban recovery: IDFs already uploaded, fleet.lst was wrong (slash format).

This script:
1. Rebuilds fleet.lst with underscore-format osm_ids from the local IDF manifest
2. Uploads the corrected fleet.lst to the cluster
3. Re-submits the SLURM array
4. Polls until complete
5. Fetches results
6. Runs verify/repair if needed
7. Builds sim manifest and runs Step 5
8. Copies final deliverables
"""
from __future__ import annotations

import io
import json
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import warnings
import re as _re
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

CELL_NAME = "nyc_urban"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/nyc_urban"
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
STEP3_DIR = WORK_BASE / "step3"
SIM_OUT_DIR = WORK_BASE / "sim_out"
RESULTS_DIR = WORK_BASE / "results"
FINAL_DIR = REPO / "docs" / "validations" / "overAll" / "results" / "cases" / CELL_NAME

LAT, LON, RADIUS_M = 40.7721, -73.9301, 500.0
STATE = "NY"
EPSG = 32618
PROBE_COUNT = 1526

_floor_rx = _re.compile(r"_F(\d+)_")


def _ssh(cmd: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout + result.stderr


def poll_cluster(job_id: str, poll_interval_s: int = 90) -> None:
    print(f"[{CELL_NAME}] Polling job {job_id} (poll every {poll_interval_s}s) ...")
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
            print(f"[{CELL_NAME}] Job {job_id}: no tasks in queue.")
            sacct_full = _ssh(
                f"sacct -j {job_id} --format=JobID,State,ExitCode --noheader 2>/dev/null",
                timeout=90,
            )
            print(sacct_full[:2000])
            break


def fetch_results(osm_ids: list[str]) -> None:
    print(f"  Fetching {len(osm_ids)} buildings from cluster ...")
    SIM_OUT_DIR.mkdir(parents=True, exist_ok=True)

    chunk_size = 200
    for i in range(0, len(osm_ids), chunk_size):
        chunk = osm_ids[i:i + chunk_size]
        fetch_cmd = (
            f"cd {REMOTE_FLEET_DIR}/out && tar czf - --ignore-failed-read "
            + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio"
                       for oid in chunk)
        )
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout_data, stderr_data = proc.communicate(timeout=600)
        if stderr_data:
            msg = stderr_data.decode(errors="replace")[:200]
            if msg.strip():
                print(f"  fetch stderr chunk {i//chunk_size}: {msg}")
        if stdout_data:
            with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
                tf.extractall(str(SIM_OUT_DIR))
        n_ends = len(list(SIM_OUT_DIR.rglob("eplusout.end")))
        print(f"  chunk {i//chunk_size+1}: {n_ends} .end files total")


def verify_end_files(osm_ids: list[str]) -> tuple[list[str], list[str]]:
    ok, failed = [], []
    for oid in osm_ids:
        end_path = SIM_OUT_DIR / oid / "eplusout.end"
        if end_path.exists() and "EnergyPlus Completed Successfully" in end_path.read_text(errors="replace"):
            ok.append(oid)
        else:
            failed.append(oid)
    return ok, failed


def repair_and_resubmit(failed_ids: list[str], epw_path: Path) -> None:
    if not failed_ids:
        return
    print(f"\n  ZERO-FAIL: {len(failed_ids)} failed. Attempting repair ...")
    for oid in failed_ids[:5]:
        err_path = SIM_OUT_DIR / oid / "eplusout.err"
        if err_path.exists():
            print(f"    {oid} err tail: {err_path.read_text(errors='replace')[-500:]}")
        else:
            print(f"    {oid}: no err file")

    repair_dir = STEP3_DIR / "repair"
    repair_dir.mkdir(exist_ok=True)
    repaired = []
    for oid in failed_ids:
        src = STEP3_DIR / "idfs" / f"{oid}.idf"
        if not src.exists():
            print(f"    {oid}: source IDF not found")
            continue
        dst = repair_dir / f"{oid}.idf"
        shutil.copy2(src, dst)
        _strip_zero_area_surfaces(dst)
        repaired.append(oid)

    if not repaired:
        print("  No IDFs could be repaired.", file=sys.stderr)
        sys.exit(2)

    repair_fleet_dir = REMOTE_FLEET_DIR + "_repair"
    _ssh(f"mkdir -p {repair_fleet_dir}/idfs {repair_fleet_dir}/weather {repair_fleet_dir}/out")

    repair_lst_local = STEP3_DIR / "repair_fleet.lst"
    repair_lst_local.write_bytes(("\n".join(repaired) + "\n").encode("utf-8"))
    subprocess.run(["scp", str(repair_lst_local), f"{REMOTE_HOST}:{repair_fleet_dir}/fleet.lst"],
                   check=True, timeout=30)
    subprocess.run(["scp", str(epw_path), f"{REMOTE_HOST}:{repair_fleet_dir}/weather/"],
                   check=True, timeout=60)

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tf:
        for oid in repaired:
            tf.add(str(repair_dir / f"{oid}.idf"), arcname=f"idfs/{oid}.idf")
    tar_buf.seek(0)
    proc = subprocess.Popen(
        ["ssh", REMOTE_HOST, f"bash -lc 'cd {repair_fleet_dir} && tar xz'"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    proc.stdin.write(tar_buf.read())
    proc.stdin.close()
    proc.wait(timeout=120)

    upload = subprocess.run(["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
                             capture_output=True, text=True, timeout=60)
    submit_cmd = (
        f"sbatch --array=1-{len(repaired)}%32 "
        f"--export=FLEET_DIR={repair_fleet_dir} "
        f"--job-name=openubem_{CELL_NAME}_repair "
        f"--output={repair_fleet_dir}/openubem_{CELL_NAME}_repair_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    out = _ssh(submit_cmd, timeout=60)
    print(f"  repair sbatch: {out.strip()}")
    repair_job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            repair_job_id = line.strip().split()[-1]
            break
    if not repair_job_id:
        print(f"  ERROR: no repair job ID", file=sys.stderr)
        sys.exit(2)

    poll_cluster(repair_job_id, poll_interval_s=90)

    fetch_cmd = (
        f"cd {repair_fleet_dir}/out && tar czf - --ignore-failed-read "
        + " ".join(f"{oid}/eplusout.sql {oid}/eplusout.err {oid}/eplusout.end {oid}/eplusout.eio" for oid in repaired)
    )
    proc2 = subprocess.Popen(["ssh", REMOTE_HOST, f"bash -lc '{fetch_cmd}'"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, _ = proc2.communicate(timeout=300)
    if stdout_data:
        with tarfile.open(fileobj=io.BytesIO(stdout_data), mode="r:gz") as tf:
            tf.extractall(str(SIM_OUT_DIR))
    print(f"  post-repair .end count: {len(list(SIM_OUT_DIR.rglob('eplusout.end')))}")

    still_failed = [oid for oid in repaired
                    if not (SIM_OUT_DIR / oid / "eplusout.end").exists()
                    or "EnergyPlus Completed Successfully" not in
                    (SIM_OUT_DIR / oid / "eplusout.end").read_text(errors="replace")]
    if still_failed:
        print(f"  {len(still_failed)} still failed after repair: {still_failed}", file=sys.stderr)
        sys.exit(2)
    print(f"  Repair successful: {len(repaired)} buildings.")


def _strip_zero_area_surfaces(idf_path: Path) -> None:
    import re
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(r"BuildingSurface:Detailed,[\s\S]*?(?=\n\s*\n|\Z)", re.MULTILINE)
    blocks = pattern.findall(text)
    removed = 0
    for block in blocks:
        coord_lines = [l for l in block.split("\n")
                       if re.match(r"^\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*", l.strip())]
        if len(coord_lines) < 3:
            text = text.replace(block, "")
            removed += 1
    if removed:
        print(f"    stripped {removed} degenerate surfaces from {idf_path.name}")
    idf_path.write_text(text, encoding="utf-8")


def build_sim_manifest(idf_manifest: pd.DataFrame, epw_path: Path, job_id: str) -> pd.DataFrame:
    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_id_stems = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    osm_ids_raw = [str(r["osm_id"]) for _, r in success_rows.iterrows()]

    sim_rows = []
    for oid_stem, oid_raw in zip(osm_id_stems, osm_ids_raw):
        bdir = SIM_OUT_DIR / oid_stem
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
            "idf_path": str(STEP3_DIR / "idfs" / f"{oid_stem}.idf"),
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
    sim_mf.to_parquet(str(WORK_BASE / "04_simulation_manifest.parquet"), index=False)
    print(f"  Sim manifest: {len(sim_mf)} rows, status={sim_mf['status'].value_counts().to_dict()}")
    return sim_mf


def _build_enriched_gdf(idf_mf: pd.DataFrame, sim_mf: pd.DataFrame) -> gpd.GeoDataFrame:
    rows = []
    for _, idf_row in idf_mf.iterrows():
        oid_raw = str(idf_row["osm_id"])
        sim_row = sim_mf[sim_mf["osm_id"].astype(str) == oid_raw]

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
                    print(f"  SQL error for {oid_raw}: {e}")

        rows.append({
            "osm_id": oid_raw,
            "footprint_area_m2": footprint_area_m2,
            "levels": num_floors,
            "height_m": height_m,
            "archetype_id": idf_row["archetype_id"],
            "zoning_strategy": idf_row["zoning_strategy"],
            "data_quality_flag": idf_row.get("data_quality_flag", ""),
            "geometry": Point(centroid_x, centroid_y),
        })
    return gpd.GeoDataFrame(rows, crs=f"EPSG:{EPSG}")


def step5_results(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame, epw_path: Path) -> tuple[gpd.GeoDataFrame, dict]:
    from openubem.results import aggregate_results, compute_validation_gates
    from openubem import config as cfg

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("  Building enriched GDF ...")
    enriched_gdf = _build_enriched_gdf(idf_manifest, sim_mf)

    if "csv_path" not in sim_mf.columns:
        sim_mf = sim_mf.copy()
        sim_mf["csv_path"] = None

    climate_sidecar = WORK_BASE / "02a_climate_epw.parquet"

    print("  Step 5: aggregate_results ...")
    t0 = time.monotonic()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_gdf = aggregate_results(
            sim_mf, idf_manifest, enriched_gdf,
            RESULTS_DIR,
            climate_sidecar=climate_sidecar if climate_sidecar.exists() else None,
            state=STATE,
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

    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    print(f"\n[{CELL_NAME}] F12 GATE SUMMARY:")
    print(f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success}) PASS={pct_parse_success>=0.99}")
    print(f"  EUI plausibility: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)}) PASS={pct_plausible>=0.99}")
    if len(outliers):
        print(f"  EUI outliers: {len(outliers)}, min={outliers.min():.1f}, max={outliers.max():.1f}")
    print(f"  zone_mismatch: {n_zone_mismatch} PASS={n_zone_mismatch==0}")
    print(f"  IOD: n={len(iod_vals)}, mean={iod_vals.mean():.4f}, p95={iod_vals.quantile(0.95):.4f}")

    gates_input = results_gdf.copy()
    if "eui_kwh_m2" not in gates_input.columns and "site_eui_kwh_m2" not in gates_input.columns:
        gates_input["eui_kwh_m2"] = gates_input["total_eui_kwh_m2"]
    cbecs_gates = compute_validation_gates(gates_input, reference_path=CBECS_PATH)
    print(f"\n[{CELL_NAME}] CBECS 2018 NE GATES (report-only):")
    for k in ["cbecs_cv_rmse", "cbecs_nmbe", "cbecs_r2", "cbecs_ks_d"]:
        print(f"  {k}: {cbecs_gates[k]}")

    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})
    print(f"\n[{CELL_NAME}] HEADLINE NUMBERS:")
    for k in ["heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
              "equipment_eui_kwh_m2", "total_eui_kwh_m2"]:
        v = eui_map.get(k)
        if v is not None:
            print(f"  {k}: {v:.2f}")
    gwp = summary.get("neighbourhood_gwp_total_kgco2")
    if gwp:
        print(f"  GWP: {gwp:,.0f} kgCO2e")
    return results_gdf, cbecs_gates


def write_gates_report(idf_manifest: pd.DataFrame, sim_mf: pd.DataFrame,
                        results_gdf: gpd.GeoDataFrame, cbecs_gates: dict,
                        epw_station_name: str, job_id: str, n_fetched: int) -> None:
    from openubem import config as cfg
    summary_path = RESULTS_DIR / "05_neighbourhood_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

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
    gen_total = len(idf_manifest)
    gen_success = int((idf_manifest["generation_status"] == "success").sum())
    pct_unknown = n_unknown / gen_total if gen_total > 0 else 0.0
    pct_gen = gen_success / gen_total if gen_total > 0 else 0.0
    eui_map = summary.get("neighbourhood_eui_weighted_kwh_m2", {})

    lines = [
        "=" * 72,
        f"V12 NYC_URBAN GATES REPORT",
        f"  Cell:   nyc_urban  ({LAT}, {LON}) r={RADIUS_M}m",
        f"  EPW:    {epw_station_name}",
        f"  Date:   2026-06-12",
        "=" * 72,
        "",
        "=== FUNNEL ===",
        f"  V10 Overpass probe count (lower bound): {PROBE_COUNT}",
        f"  Actual OSM fetch:    {n_fetched}",
        f"  Generation success:  {gen_success}/{gen_total}",
        f"  Simulated (cluster): {n_sim_success}",
        f"  Parsed (Step 5):     {n_parsed}",
        "",
        "=== LIVE_SMOKE GATES ===",
        f"  generation_success: {gen_success}/{gen_total} = {pct_gen*100:.1f}%  (>=95%: {'PASS' if pct_gen>=0.95 else 'FAIL'})",
        f"  unknown_archetype: {n_unknown}/{gen_total} = {pct_unknown*100:.1f}%  (<20%: {'PASS' if pct_unknown<0.20 else 'FAIL'})",
        "",
        "=== SIMULATION STATUS ===",
        f"  cluster_job_id: {job_id}",
        f"  sim_manifest_rows: {len(sim_mf)}",
        f"  status_counts: {sim_mf['status'].value_counts().to_dict()}",
        "",
        "=== F12 GATE TABLE ===",
        f"  pct_parse_success: {pct_parse_success*100:.2f}% ({n_parsed}/{n_sim_success})  PASS={pct_parse_success>=0.99}",
        f"  EUI_plausibility [25,1000]: {pct_plausible*100:.2f}% ({in_range}/{len(valid_eui)})  PASS={pct_plausible>=0.99}",
    ]
    if len(outliers):
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
    report = "\n".join(lines)
    report_path = RESULTS_DIR / "v12_nyc_urban_gates_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[{CELL_NAME}] Gates report -> {report_path}")


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
    print(f"[{CELL_NAME}] Recovery run — IDFs already on cluster at {REMOTE_FLEET_DIR}/idfs/")
    print(f"[{CELL_NAME}] Working dir: {WORK_BASE}")
    print(f"[{CELL_NAME}] Final dir:   {FINAL_DIR}")

    idf_manifest = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
    print(f"  IDF manifest: {len(idf_manifest)} rows")
    n_generated = int((idf_manifest["generation_status"] == "success").sum())
    print(f"  success: {n_generated}/{len(idf_manifest)}")

    n_fetched = len(gpd.read_file(str(WORK_BASE / "01_buildings.gpkg"))) if (WORK_BASE / "01_buildings.gpkg").exists() else "N/A"
    print(f"  n_fetched (from cached GPKG): {n_fetched}")

    success_rows = idf_manifest[idf_manifest["generation_status"] == "success"]
    osm_id_stems = [Path(str(r["idf_path"])).stem for _, r in success_rows.iterrows()]
    print(f"  osm_id_stems sample: {osm_id_stems[:3]}")

    # Step 1: fix fleet.lst
    print(f"\n[{CELL_NAME}] Uploading corrected fleet.lst (underscore format) ...")
    fleet_lst_local = WORK_BASE / "fleet_staging" / "corrected_fleet.lst"
    fleet_lst_local.parent.mkdir(parents=True, exist_ok=True)
    fleet_lst_local.write_bytes(("\n".join(osm_id_stems) + "\n").encode("utf-8"))
    subprocess.run(["scp", str(fleet_lst_local), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/fleet.lst"],
                   check=True, timeout=60)
    print(f"  fleet.lst uploaded with {len(osm_id_stems)} entries")

    # Resolve EPW
    from openubem.acquisition.epw_manager import load_stations, resolve_station, fetch_epw
    stations = load_stations()
    station, dist_km = resolve_station(LAT, LON, stations)
    epw_path = fetch_epw(station, output_dir=WORK_BASE / "weather")
    epw_station_name = station.get("name", str(station["station_id"]))
    print(f"  EPW: {epw_path.name} (station: {epw_station_name}, {dist_km:.1f} km)")

    # Step 2: Re-submit SLURM array
    print(f"\n[{CELL_NAME}] Re-submitting SLURM array (n={n_generated}) ...")
    upload = subprocess.run(["scp", str(SBATCH_LOCAL), f"{REMOTE_HOST}:{SBATCH_REMOTE}"],
                             capture_output=True, text=True, timeout=60)
    submit_cmd = (
        f"sbatch --array=1-{n_generated}%32 "
        f"--export=FLEET_DIR={REMOTE_FLEET_DIR} "
        f"--job-name=openubem_{CELL_NAME} "
        f"--output={REMOTE_FLEET_DIR}/openubem_{CELL_NAME}_%A_%a.log "
        f"{SBATCH_REMOTE}"
    )
    print(f"  {submit_cmd}")
    out = _ssh(submit_cmd, timeout=60)
    print(f"  sbatch: {out.strip()}")
    job_id = ""
    for line in out.splitlines():
        if "Submitted batch job" in line:
            job_id = line.strip().split()[-1]
            break
    if not job_id:
        print(f"  ERROR: could not parse job ID", file=sys.stderr)
        sys.exit(1)
    print(f"  Job ID: {job_id}")

    # Step 3: Poll
    poll_cluster(job_id, poll_interval_s=90)

    # Step 4: Fetch results
    print(f"\n[{CELL_NAME}] Fetching results ...")
    fetch_results(osm_id_stems)

    # Step 5: Verify
    ok_ids, failed_ids = verify_end_files(osm_id_stems)
    print(f"  Verified: {len(ok_ids)} success, {len(failed_ids)} failed")
    if failed_ids:
        repair_and_resubmit(failed_ids, epw_path)
        ok_ids, failed_ids = verify_end_files(osm_id_stems)
        if failed_ids:
            print(f"  ZERO-FAIL: {len(failed_ids)} still unresolved", file=sys.stderr)
            sys.exit(2)

    # Step 6: Build sim manifest
    print(f"\n[{CELL_NAME}] Building sim manifest ...")
    sim_mf = build_sim_manifest(idf_manifest, epw_path, job_id)
    n_sim_fail = int((sim_mf["status"] != "success").sum())
    if n_sim_fail > 0:
        print(f"  ZERO-FAIL: {n_sim_fail} failures in manifest", file=sys.stderr)
        sys.exit(2)

    # Step 7: Step 5
    print(f"\n[{CELL_NAME}] Running Step 5 ...")
    results_gdf, cbecs_gates = step5_results(idf_manifest, sim_mf, epw_path)

    # Step 8: Gates report
    write_gates_report(idf_manifest, sim_mf, results_gdf, cbecs_gates,
                       epw_station_name=epw_station_name, job_id=job_id, n_fetched=n_fetched)

    # Step 9: Copy deliverables
    copied = copy_final_deliverables()
    print(f"\n[{CELL_NAME}] Copied {len(copied)} files to {FINAL_DIR}")
    print(f"\n[{CELL_NAME}] DONE — nyc_urban complete.")
    print(f"  Fetched:   {n_fetched}")
    print(f"  Generated: {n_generated}/{len(idf_manifest)}")
    print(f"  Simulated: {len(ok_ids)}/{n_generated}")
    print(f"  Job ID:    {job_id}")


if __name__ == "__main__":
    main()
