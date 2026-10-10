"""EU-11 — Harvest cluster results for one or more European S2 district campaigns.

Run AFTER the district's `submit_fleet_t08.sbatch` array has finished on Speed
(`ship_eu11_fleet.sh` staged it, one array task per building). Fetches
eplusout.sql/.err/.eio, task.rc, platform.txt and energyplus_version.txt from
each task's remote `out/<stem>/` directory, joins them against the local
`prepared_buildings.csv` written by `scripts/run_eu_s2_district_campaign.py`,
and writes one results manifest + one post-run `summary.json` per district.

Cluster rules (see CLAUDE.md and PROMPT_EU-11_full_district_campaign_speed.md
§4): no compute on the Speed login node, only `mkdir`/`scp`/`tar`/`squeue`/
`sacct`-class listing/reading. File lists are expanded REMOTELY (a shell glob
inside `bash -lc`), never assembled on the Windows command line.

Usage:
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_district.py --district ES-MAD-BERRUGUETE
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_district.py --all

Outputs (per district):
    openubem/outputs/eu_evidence/EU-11/<DISTRICT>/<district_slug>_manifest.csv
    openubem/outputs/eu_evidence/EU-11/<DISTRICT>/summary.json   (post-run; pre-run copy kept as summary_prerun.json)
"""
from __future__ import annotations

import argparse
import hashlib
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

EVIDENCE_ROOT = REPO / "openubem" / "outputs" / "eu_evidence" / "EU-11"

# Real SLURM array job IDs of the latest resimulation for each district.
# EU-15/EU-16 T09 (post EU-15 T01-T05 ruled zoning + EU-16 T06/T07 context shading and
# adiabatic party walls, plan eu15-eu16-zoning-context-2026-08-30) — 2026-08-30.
DISTRICT_JOBS = {
    "ES-MAD-BERRUGUETE": 1299912,
    "FR-LYO-HAUTCOEURPENTES": 1299945,
    "GB-LDN-STDUNSTANS": 1299946,
    "IT-BOL-GALVANI2": 1299947,
}

# SLURM array job IDs for tagged re-runs, keyed by (district, tag).
TAGGED_DISTRICT_JOBS = {
    ("FR-LYO-HAUTCOEURPENTES", "final_2026-09-07"): 1311158,
    ("FR-LYO-HAUTCOEURPENTES", "delta_2026-09-07"): 1311699,
    ("GB-LDN-STDUNSTANS", "final_2026-09-07"): 1311214,
    ("GB-LDN-STDUNSTANS", "delta_2026-09-07"): 1311701,
    ("ES-MAD-BERRUGUETE", "final_2026-09-07"): 1311215,
    ("ES-MAD-BERRUGUETE", "delta_2026-09-07"): 1311703,
    ("IT-BOL-GALVANI2", "final_2026-09-07"): 1311244,
    ("IT-BOL-GALVANI2", "delta_2026-09-07"): 1311708,
    ("ES-MAD-BERRUGUETE", "recut_2026-09-08"): 1314028,
    ("FR-LYO-HAUTCOEURPENTES", "recut_2026-09-08"): 1314065,
    ("GB-LDN-STDUNSTANS", "recut_2026-09-08"): 1314066,
    ("IT-BOL-GALVANI2", "recut_2026-09-08"): 1314067,
    ("ES-MAD-BERRUGUETE", "fix_2026-09-29"): 1402184,
    ("FR-LYO-HAUTCOEURPENTES", "fix_2026-09-29"): 1402185,
    ("GB-LDN-STDUNSTANS", "fix_2026-09-29"): 1402186,
    ("IT-BOL-GALVANI2", "fix_2026-09-29"): 1402187,
    ("ES-MAD-BERRUGUETE", "fix_2026-10-01"): [1405556, 1405952, 1406517],
    ("FR-LYO-HAUTCOEURPENTES", "fix_2026-10-01"): [1405481, 1405950, 1406516],
    ("GB-LDN-STDUNSTANS", "fix_2026-10-01"): [1405523, 1405951],
    ("IT-BOL-GALVANI2", "fix_2026-10-01"): [1405559, 1406674],
}

NEW_SITES = (
    "AT-VIE-RUDOLFSHEIM", "KR-SEO-MAPO", "CA-MTL-PLATEAU", "FI-HEL-KALLIO",
    "ZA-CPT-WOODSTOCK", "HU-BUD-ERZSEBETVAROS", "AM-EVN-NORNORK",
)
NEW_SITE_FLEET_PREFIX = "EU22"
COMPLETED_MARKER = "EnergyPlus Completed Successfully"

MANIFEST_COLUMNS = [
    "building_id", "archetype_id", "building_type", "age_band", "geometry_outcome",
    "construction_period_provenance",
    "idf_sha256", "weather_sha256", "eplus_return_code", "severe_errors", "fatal_errors",
    "heating_kwh", "floor_area_m2", "eui_kwh_m2", "run_seconds", "platform", "energyplus_version",
]

WIN5_TAG = "win_2026-10-05"
WIN6_TAG = "win_2026-10-06"

J_TO_KWH = 1.0 / 3.6e6
_HEATING_SQL = (
    "SELECT SUM(r.Value) FROM ReportData r "
    "JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex "
    "WHERE d.Name = 'Zone Ideal Loads Zone Total Heating Energy'"
)


# ── remote helpers (tcsh login shell: every command wrapped in bash -lc) ──────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_dir(district: str, tag: str | None = None) -> str:
    prefix = NEW_SITE_FLEET_PREFIX if district in NEW_SITES else "EU11"
    base = f"{_REMOTE_FLEET_BASE}/{prefix}_{district}"
    return f"{base}_{tag}" if tag else base


def fetch_district_out(district: str, work_base: Path, tag: str | None = None) -> Path:
    """Fetch every task's out/<stem>/ directory contents for one district.

    The file list (`*/eplusout.sql`, etc.) is a shell glob expanded by the
    remote login shell inside `out/`, never assembled locally — this avoids
    the Windows ~32k-char command-line limit at fleet sizes >~150 (see
    docs/docs_EXPLANATION/OpenUBEM_debug_References.md ch.12).
    """
    remote_dir = _remote_fleet_dir(district, tag)
    label = f"{district}_{tag}" if tag else district
    sim_out = work_base / label
    sim_out.mkdir(parents=True, exist_ok=True)

    print(f"  [{district}] fetching from {remote_dir}/out ...")
    remote_cmd = (
        f"cd {remote_dir}/out && "
        f"tar czf - --ignore-failed-read "
        f"*/eplusout.sql */eplusout.err */eplusout.eio */eplusout.end */task.rc "
        f"*/platform.txt */energyplus_version.txt"
    )
    tgz = work_base / f"fetch_{label}.tgz"
    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE, text=True,
        )
        _, err = proc.communicate(timeout=3600)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(
            f"empty fetch for {district} (ssh rc={proc.returncode}); "
            f"{remote_dir}/out likely missing. remote stderr: {err.strip()[:400]}"
        )

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(sim_out))
    tgz.unlink(missing_ok=True)

    n = len(list(sim_out.iterdir()))
    print(f"  [{district}] {n} task directories extracted")
    return sim_out


def fetch_sacct_elapsed(job_id: int, with_state: bool = False) -> dict:
    """Per-array-task elapsed seconds, keyed by array task index.

    With `with_state` the value is `(seconds, state)`. `sacct` here is a
    listing/reading command (allowed on the login node), never compute.
    Excludes the `.batch`/`.extern` sub-steps that `sacct` also reports for
    every array task.
    """
    fmt = "JobID,Elapsed,State" if with_state else "JobID,Elapsed"
    raw = _ssh(
        f"sacct -j {job_id} --format={fmt} --noheader --parsable2",
        timeout=60,
    )
    out: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        state = line.split("|")[2].split()[0] if with_state and line.count("|") >= 2 else ""
        m = re.match(rf"^{job_id}_(\d+)\|(\d+)-(\d+):(\d+):(\d+)(?:\|.*)?$", line)
        if m:
            idx, days, hh, mm, ss = m.groups()
            secs = int(days) * 86400 + int(hh) * 3600 + int(mm) * 60 + int(ss)
            out[int(idx)] = (secs, state) if with_state else secs
            continue
        m = re.match(rf"^{job_id}_(\d+)\|(\d+):(\d+):(\d+)(?:\|.*)?$", line)
        if m:
            idx, hh, mm, ss = m.groups()
            secs = int(hh) * 3600 + int(mm) * 60 + int(ss)
            out[int(idx)] = (secs, state) if with_state else secs
    return out


def _elapsed_for_jobs(job_ids: list[int]) -> dict[int, int]:
    per_job = [fetch_sacct_elapsed(j, with_state=True) for j in job_ids]
    merged: dict[int, int] = {}
    for idx in sorted({i for d in per_job for i in d}):
        having = [d[idx] for d in per_job if idx in d]
        completed = [secs for secs, state in having if state == "COMPLETED"]
        merged[idx] = completed[-1] if completed else having[-1][0]
    return merged


# ── parse one task's remote output ─────────────────────────────────────────

def _parse_heating_kwh(sql_path: Path) -> float | None:
    if not sql_path.exists():
        return None
    try:
        with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
            (val_j,) = conn.execute(_HEATING_SQL).fetchone()
    except sqlite3.Error:
        return None
    if val_j is None:
        return None
    return float(val_j) * J_TO_KWH


def parse_task(bdir: Path, require_end: bool = False) -> dict:
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

    if completed and require_end:
        end_path = bdir / "eplusout.end"
        end_text = end_path.read_text(encoding="utf-8", errors="replace") if end_path.exists() else ""
        completed = COMPLETED_MARKER in end_text

    if completed:
        row["heating_kwh"] = _parse_heating_kwh(bdir / "eplusout.sql")

    platform_path = bdir / "platform.txt"
    if platform_path.exists():
        lines = [l.strip() for l in platform_path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
        row["platform"] = " / ".join(lines)

    version_path = bdir / "energyplus_version.txt"
    if version_path.exists():
        text = version_path.read_text(encoding="utf-8", errors="replace").strip()
        row["energyplus_version"] = text.splitlines()[0] if text else pd.NA

    return row


# ── harvest one district ────────────────────────────────────────────────────

def harvest_district(district: str, work_base: Path, tag: str | None = None) -> dict:
    new_site = district in NEW_SITES
    if new_site and not (tag and tag.startswith("win_")):
        raise ValueError(f"{district}: a new site is harvested with --tag win_<date>, got {tag!r}")
    dist_dir = EVIDENCE_ROOT / (f"{district}_{tag}" if tag else district)
    prepared_path = dist_dir / "prepared_buildings.csv"
    if not prepared_path.exists():
        raise FileNotFoundError(f"missing {prepared_path} — run run_eu_s2_district_campaign.py first")
    prepared = pd.read_csv(prepared_path, dtype=str)

    fleet_lst = [s.strip() for s in (dist_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()]

    if tag and tag.startswith("win_"):
        jobs_path = dist_dir / "speed_jobs.txt"
        if not jobs_path.exists():
            raise FileNotFoundError(f"missing {jobs_path} - the director writes it after submission")
        job_id = [
            int(ln.split()[0]) for ln in jobs_path.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
    else:
        job_id = TAGGED_DISTRICT_JOBS.get((district, tag), DISTRICT_JOBS[district]) if tag else DISTRICT_JOBS[district]
    is_win5 = tag in (WIN5_TAG, WIN6_TAG) or new_site
    if is_win5:
        idf_dir = dist_dir / "idfs"
        stems = sorted(p.stem for p in idf_dir.glob("*.idf"))
        md5_map = {}
        for ln in (dist_dir / f"md5_{tag[len('win_'):]}.txt").read_text(encoding="utf-8").splitlines():
            parts = ln.split()
            if len(parts) >= 2:
                md5_map[Path(parts[1]).stem] = parts[0].lower()
        for stem in stems:
            got = hashlib.md5((idf_dir / f"{stem}.idf").read_bytes()).hexdigest()
            if md5_map.get(stem) != got:
                raise ValueError(f"{district}: md5 mismatch for {stem}: file {got} vs md5 list {md5_map.get(stem)}")
    else:
        stems = fleet_lst
    fleet_index = {s: i for i, s in enumerate(fleet_lst, start=1)}
    sim_out = fetch_district_out(district, work_base, tag)
    elapsed = _elapsed_for_jobs(job_id) if isinstance(job_id, list) else fetch_sacct_elapsed(job_id)

    shipped_path = dist_dir / "shipped_t06f.lst"
    shipped = (
        {s.strip() for s in shipped_path.read_text(encoding="utf-8").splitlines() if s.strip()}
        if shipped_path.exists() else set()
    )
    not_in_fleet = sorted(shipped - set(fleet_lst))
    if not_in_fleet:
        raise ValueError(f"shipped_t06f.lst stems not in fleet.lst for {district}: {not_in_fleet[:5]}")
    t06f_idf_dir = EVIDENCE_ROOT / f"{district}_{tag}_t06f" / "idfs"

    shipped_g_path = dist_dir / "shipped_t06g.lst"
    shipped_g = (
        {s.strip() for s in shipped_g_path.read_text(encoding="utf-8").splitlines() if s.strip()}
        if shipped_g_path.exists() else set()
    )
    not_in_fleet_g = sorted(shipped_g - set(fleet_lst))
    if not_in_fleet_g:
        raise ValueError(f"shipped_t06g.lst stems not in fleet.lst for {district}: {not_in_fleet_g[:5]}")
    t06g_idf_dir = EVIDENCE_ROOT / f"{district}_{tag}_t06g" / "idfs"
    has_variant = shipped_path.exists() or shipped_g_path.exists()

    rows = []
    for stem in stems:
        idx = fleet_index.get(stem)
        prow = prepared[prepared["stem"] == stem]
        if prow.empty:
            raise ValueError(f"fleet.lst stem {stem} not found in prepared_buildings.csv for {district}")
        prow = prow.iloc[0]
        floor_area_m2 = float(prow["floor_area_m2"])

        bdir = sim_out / stem
        task = parse_task(bdir, require_end=new_site) if bdir.exists() else {
            "eplus_return_code": pd.NA, "severe_errors": pd.NA, "fatal_errors": pd.NA,
            "heating_kwh": pd.NA, "platform": pd.NA, "energyplus_version": pd.NA,
        }

        heating_kwh = task["heating_kwh"]
        eui = (heating_kwh / floor_area_m2) if (pd.notna(heating_kwh) and floor_area_m2 > 0) else pd.NA

        if is_win5:
            idf_sha = hashlib.sha256((dist_dir / "idfs" / f"{stem}.idf").read_bytes()).hexdigest()
            idf_variant = "fix"
        elif stem in shipped_g:
            idf_sha = hashlib.sha256((t06g_idf_dir / f"{stem}.idf").read_bytes()).hexdigest()
            idf_variant = "t06g"
        elif stem in shipped:
            idf_sha = hashlib.sha256((t06f_idf_dir / f"{stem}.idf").read_bytes()).hexdigest()
            idf_variant = "t06f"
        else:
            idf_sha = prow["idf_sha256"]
            idf_variant = "fix"

        rows.append({
            "building_id": prow["building_id"],
            "archetype_id": prow["archetype_id"],
            "building_type": prow["building_type"],
            "age_band": prow["age_band"],
            "geometry_outcome": prow["geometry_outcome"],
            "construction_period_provenance": prow.get("construction_period_provenance", ""),
            "idf_sha256": idf_sha,
            "weather_sha256": prow["weather_sha256"],
            "eplus_return_code": task["eplus_return_code"],
            "severe_errors": task["severe_errors"],
            "fatal_errors": task["fatal_errors"],
            "heating_kwh": round(heating_kwh, 6) if pd.notna(heating_kwh) else pd.NA,
            "floor_area_m2": round(floor_area_m2, 4),
            "eui_kwh_m2": round(eui, 6) if pd.notna(eui) else pd.NA,
            "run_seconds": elapsed.get(idx, pd.NA) if idx is not None else pd.NA,
            "platform": task["platform"],
            "energyplus_version": task["energyplus_version"],
            "idf_variant": idf_variant if has_variant else pd.NA,
            "dwellings_used": prow.get("dwellings_used", pd.NA),
            "dwellings_source": prow.get("dwellings_source", pd.NA),
        })

    manifest_columns = MANIFEST_COLUMNS + (["idf_variant"] if has_variant else [])
    if is_win5:
        manifest_columns = manifest_columns + ["dwellings_used", "dwellings_source"]
    manifest = pd.DataFrame(rows, columns=manifest_columns)
    slug = district.lower().replace("-", "_")
    manifest_path = dist_dir / f"{slug}_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    print(f"  [{district}] manifest written: {manifest_path} ({len(manifest)} rows)")

    succ = manifest[manifest["eplus_return_code"] == 0]
    n_run = len(manifest)
    n_success = len(succ[pd.notna(succ["heating_kwh"])])
    n_failed = n_run - n_success
    fail_kinds: dict[str, int] = {}
    for _, r in manifest.iterrows():
        if pd.isna(r["heating_kwh"]):
            key = f"rc={r['eplus_return_code']},severe={r['severe_errors']},fatal={r['fatal_errors']}"
            fail_kinds[key] = fail_kinds.get(key, 0) + 1

    pooled_heating = float(succ["heating_kwh"].dropna().sum()) if n_success else float("nan")
    pooled_area = float(succ.loc[pd.notna(succ["heating_kwh"]), "floor_area_m2"].sum()) if n_success else float("nan")
    pooled_eui = pooled_heating / pooled_area if n_success and pooled_area > 0 else float("nan")

    prerun_summary_path = dist_dir / "summary.json"
    prerun_summary = json.loads(prerun_summary_path.read_text(encoding="utf-8")) if prerun_summary_path.exists() else {}
    prerun_copy_path = dist_dir / "summary_prerun.json"
    if prerun_summary_path.exists() and not prerun_copy_path.exists():
        shutil.copy2(prerun_summary_path, prerun_copy_path)

    epw_rel = prerun_summary.get("epw")
    epw_sha = prerun_summary.get("weather_sha256")

    platforms = sorted(set(manifest["platform"].dropna().astype(str)))
    versions = sorted(set(manifest["energyplus_version"].dropna().astype(str)))

    summary = {
        "district": district,
        "population_attempted": prerun_summary.get("population_attempted"),
        "population_prepared": prerun_summary.get("population_prepared", n_run),
        "population_run": n_run,
        "population_success": n_success,
        "population_failed_on_speed": n_failed,
        "prerun_blocker_exclusions": prerun_summary.get("blocker_exclusions", {}),
        "speed_failure_kinds": dict(sorted(fail_kinds.items())),
        "epw": epw_rel,
        "weather_sha256": epw_sha,
        "pooled_heating_kwh": round(pooled_heating, 4) if n_success else None,
        "pooled_floor_area_m2": round(pooled_area, 4) if n_success else None,
        "pooled_eui_kwh_m2": round(pooled_eui, 6) if n_success else None,
        "platform_observed": platforms,
        "energyplus_version_observed": versions,
        "speed_job_id": job_id,
        "status": "HARVESTED_FROM_SPEED",
    }
    summary_path = dist_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  [{district}] summary written: {summary_path}")
    print(f"  [{district}] run={n_run} success={n_success} failed={n_failed} pooled_eui={pooled_eui:.4f} kWh/m2"
          if n_success else f"  [{district}] run={n_run} success={n_success} failed={n_failed}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", choices=sorted(DISTRICT_JOBS) + list(NEW_SITES), help="single district")
    parser.add_argument("--all", action="store_true", help="harvest all three submitted districts")
    parser.add_argument("--tag", default=None, help="harvest a tagged re-run instead of the default campaign")
    args = parser.parse_args()
    if not args.district and not args.all:
        parser.error("pass --district <NAME> or --all")

    districts = sorted(DISTRICT_JOBS) if args.all else [args.district]
    work_base = Path(tempfile.gettempdir()) / "ubem_eu11_harvest"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"EU-11 harvest — work dir: {work_base}")

    summaries = {}
    for district in districts:
        print(f"\n=== District: {district} ===")
        summaries[district] = harvest_district(district, work_base, args.tag)

    print("\n" + "=" * 80)
    for district, s in summaries.items():
        eui = s["pooled_eui_kwh_m2"]
        eui_txt = f"{eui:.4f} kWh/m2" if eui is not None else "n/a"
        print(f"{district}: run={s['population_run']} success={s['population_success']} "
              f"failed={s['population_failed_on_speed']} pooled_eui={eui_txt}")
    print("=" * 80)


if __name__ == "__main__":
    main()
