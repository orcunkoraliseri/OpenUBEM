"""Harvest cluster results for the 2026-09-04 EU-11 remedy campaign on Speed.

Fetches simulation outputs (eplusout.sql, eplusout.err, eplusout.eio, task.rc,
platform.txt, energyplus_version.txt) from remote:
    /speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/out/<stem>/
and writes results to:
    openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/

Usage:
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_remedy_campaign.py --status
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_remedy_campaign.py --district GB-LDN-STDUNSTANS
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_remedy_campaign.py --all
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
RUN_SUFFIX = "finding249_remedy_2026-09-04"

EVIDENCE_ROOT = REPO / "openubem" / "outputs" / "eu_evidence" / "EU-11"

DISTRICT_JOBS = {
    "GB-LDN-STDUNSTANS": 1305158,
    "FR-LYO-HAUTCOEURPENTES": 1305167,
    "ES-MAD-BERRUGUETE": 1305176,
    "IT-BOL-GALVANI2": 1305186,
}

MANIFEST_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "construction_period_provenance",
    "idf_sha256", "weather_sha256", "eplus_return_code", "severe_errors", "fatal_errors",
    "heating_kwh", "floor_area_m2", "eui_kwh_m2", "run_seconds", "platform", "energyplus_version",
]

J_TO_KWH = 1.0 / 3.6e6
_HEATING_SQL = (
    "SELECT SUM(r.Value) FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.Name = 'Zone Ideal Loads Zone Total Heating Energy'"
)


def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(district: str) -> str:
    return f"{_REMOTE_FLEET_BASE}/EU11_{district}_{RUN_SUFFIX}"


def get_cluster_status() -> dict[str, dict[str, int]]:
    job_ids_str = ",".join(str(jid) for jid in DISTRICT_JOBS.values())
    raw = _ssh(f"sacct -j {job_ids_str} -X --format=JobID,State,ExitCode --noheader", timeout=60)
    jid_to_dist = {str(v): k for k, v in DISTRICT_JOBS.items()}
    counts: dict[str, dict[str, int]] = {dist: collections.defaultdict(int) for dist in DISTRICT_JOBS}

    for line in raw.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            job_full, state = parts[0], parts[1]
            job_base = job_full.split("_")[0]
            if job_base in jid_to_dist:
                dist = jid_to_dist[job_base]
                counts[dist][state] += 1
    return {k: dict(v) for k, v in counts.items()}


def fetch_sacct_elapsed(job_id: int) -> dict[int, int]:
    raw = _ssh(
        f"sacct -j {job_id} --format=JobID,Elapsed --noheader --parsable2",
        timeout=60,
    )
    out: dict[int, int] = {}
    for line in raw.splitlines():
        line = line.strip()
        m = re.match(rf"^{job_id}_(\d+)\|(\d+)-(\d+):(\d+):(\d+)$", line)
        if m:
            idx, days, hh, mm, ss = m.groups()
            out[int(idx)] = int(days) * 86400 + int(hh) * 3600 + int(mm) * 60 + int(ss)
            continue
        m = re.match(rf"^{job_id}_(\d+)\|(\d+):(\d+):(\d+)$", line)
        if m:
            idx, hh, mm, ss = m.groups()
            out[int(idx)] = int(hh) * 3600 + int(mm) * 60 + int(ss)
    return out


def fetch_district_out(district: str, work_base: Path) -> Path:
    remote_dir = _remote_fleet_dir(district)
    sim_out = work_base / district
    sim_out.mkdir(parents=True, exist_ok=True)

    print(f"  [{district}] fetching outputs from {remote_dir}/out ...")
    remote_cmd = (
        f"cd {remote_dir}/out && "
        f"tar czf - --ignore-failed-read "
        f"*/eplusout.sql */eplusout.err */eplusout.eio */task.rc "
        f"*/platform.txt */energyplus_version.txt"
    )
    tgz = work_base / f"fetch_{district}.tgz"
    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE,
        )
        _, err = proc.communicate(timeout=3600)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(
            f"empty fetch for {district} (ssh rc={proc.returncode}); "
            f"{remote_dir}/out likely missing or empty. remote stderr: {err.decode('utf-8', errors='replace').strip()[:400]}"
        )

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(sim_out))
    tgz.unlink(missing_ok=True)

    n = len(list(sim_out.iterdir()))
    print(f"  [{district}] {n} task directories extracted")
    return sim_out


def _parse_heating_kwh(sql_path: Path) -> float | None:
    if not sql_path.exists():
        return None
    try:
        with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
            row = conn.execute(_HEATING_SQL).fetchone()
            if row is None or row[0] is None:
                return None
            return float(row[0]) * J_TO_KWH
    except sqlite3.Error:
        return None


def parse_task(bdir: Path) -> dict:
    row: dict = {
        "eplus_return_code": pd.NA, "severe_errors": pd.NA, "fatal_errors": pd.NA,
        "heating_kwh": pd.NA, "platform": pd.NA, "energyplus_version": pd.NA,
    }
    rc_path = bdir / "task.rc"
    if rc_path.exists():
        try:
            row["eplus_return_code"] = int(rc_path.read_text(encoding="utf-8", errors="replace").strip())
        except ValueError:
            row["eplus_return_code"] = -1

    err_path = bdir / "eplusout.err"
    err_text = err_path.read_text(encoding="utf-8", errors="replace") if err_path.exists() else ""
    row["severe_errors"] = len(re.findall(r"\*\*\s*Severe\s*\*\*", err_text, re.IGNORECASE))
    row["fatal_errors"] = len(re.findall(r"\*\*\s*Fatal\s*\*\*", err_text, re.IGNORECASE))
    completed = (
        pd.notna(row["eplus_return_code"])
        and row["eplus_return_code"] == 0
        and "Completed Successfully" in err_text
    )

    if completed:
        row["heating_kwh"] = _parse_heating_kwh(bdir / "eplusout.sql")

    platform_path = bdir / "platform.txt"
    if platform_path.exists():
        lines = [l.strip() for l in platform_path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        row["platform"] = " / ".join(lines)

    version_path = bdir / "energyplus_version.txt"
    if version_path.exists():
        lines = [l.strip() for l in version_path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        row["energyplus_version"] = " / ".join(lines)

    return row


def harvest_district(district: str, work_base: Path) -> Path:
    dist_dir = EVIDENCE_ROOT / f"{district}_{RUN_SUFFIX}"
    if not dist_dir.exists():
        raise FileNotFoundError(f"Local district directory not found: {dist_dir}")

    prep_csv = dist_dir / "prepared_buildings.csv"
    if not prep_csv.exists():
        raise FileNotFoundError(f"prepared_buildings.csv not found in {dist_dir}")

    job_id = DISTRICT_JOBS[district]
    print(f"[{district}] harvesting job {job_id} into {dist_dir} ...")
    sim_out = fetch_district_out(district, work_base)
    elapsed_by_task = fetch_sacct_elapsed(job_id)

    prep_df = pd.read_csv(prep_csv, dtype={"building_id": str})
    print(f"  [{district}] {len(prep_df)} buildings in prepared_buildings.csv")

    fleet_lst = [s.strip() for s in (dist_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()]
    results_rows = []
    for idx_0, stem in enumerate(fleet_lst):
        prow = prep_df[prep_df["stem"] == stem]
        if prow.empty:
            continue
        row = prow.iloc[0]
        b_id = str(row["building_id"])
        bdir = sim_out / stem
        t_res = parse_task(bdir) if bdir.exists() else {
            "eplus_return_code": pd.NA, "severe_errors": pd.NA, "fatal_errors": pd.NA,
            "heating_kwh": pd.NA, "platform": pd.NA, "energyplus_version": pd.NA,
        }
        task_idx = idx_0 + 1
        t_res["run_seconds"] = elapsed_by_task.get(task_idx, pd.NA)
        t_res["building_id"] = b_id

        # Copy over metadata columns from prepared_buildings
        for col in ["archetype_id", "building_type", "age_band", "geometry_outcome",
                    "construction_period_provenance", "floor_area_m2"]:
            t_res[col] = row.get(col, pd.NA)

        # Compute EUI if heating and floor_area are available
        fa = row.get("floor_area_m2")
        hkwh = t_res.get("heating_kwh")
        if pd.notna(hkwh) and pd.notna(fa) and float(fa) > 0:
            t_res["eui_kwh_m2"] = float(hkwh) / float(fa)
        else:
            t_res["eui_kwh_m2"] = pd.NA

        results_rows.append(t_res)

    res_df = pd.DataFrame(results_rows)
    slug = district.lower().replace("-", "_")
    manifest_path = dist_dir / f"{slug}_manifest.csv"
    res_df.to_csv(manifest_path, index=False)
    # Also write district_manifest.csv for compatibility
    res_df.to_csv(dist_dir / f"{district}_manifest.csv", index=False)
    print(f"  [{district}] wrote manifest -> {manifest_path}")

    # Summary JSON
    n_total = len(res_df)
    n_rc0 = int((res_df["eplus_return_code"] == 0).sum())
    n_fatal = int((res_df["fatal_errors"] > 0).sum())
    valid_eui = res_df["eui_kwh_m2"].dropna()
    mean_eui = float(valid_eui.mean()) if len(valid_eui) > 0 else None

    summary = {
        "district": district,
        "job_id": job_id,
        "n_total": n_total,
        "n_completed_rc0": n_rc0,
        "n_fatal": n_fatal,
        "mean_eui_kwh_m2": mean_eui,
    }
    summary_path = dist_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  [{district}] summary: {n_rc0}/{n_total} completed rc=0, mean EUI: {mean_eui}")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Harvest EU-11 remedy cluster campaign results")
    parser.add_argument("--status", action="store_true", help="Print current status of all 4 district jobs")
    parser.add_argument("--district", choices=list(DISTRICT_JOBS.keys()), help="Harvest single district")
    parser.add_argument("--all", action="store_true", help="Harvest all 4 districts")
    args = parser.parse_args()

    if args.status or (not args.district and not args.all):
        status = get_cluster_status()
        print("=== REMEDY CAMPAIGN SLURM STATUS ===")
        for d, s in status.items():
            print(f"  {d} [Job {DISTRICT_JOBS[d]}]: {s}")
        return

    work_base = Path(tempfile.mkdtemp(prefix="harvest_eu11_remedy_"))
    try:
        districts = list(DISTRICT_JOBS.keys()) if args.all else [args.district]
        for dist in districts:
            harvest_district(dist, work_base)
            print(f"  [{dist}] Updating 3D viewers and data in docs/docs_ACTIVE/europeanLocations/outputs_3D ...")
            try:
                from scripts.update_eu_outputs_3d import update_district_viewer
                update_district_viewer(dist)
            except Exception as e:
                print(f"  [{dist}] Warning: failed to update 3D viewer: {e}")
    finally:
        shutil.rmtree(work_base, ignore_errors=True)


if __name__ == "__main__":
    main()
