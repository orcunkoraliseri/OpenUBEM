"""EU-11 ceiling82 — final harvest, merging multiple Speed waves per district.

Each ceiling82 district's EnergyPlus population is now the union of results
scattered across 2-3 separate Speed jobs/remote fleet directories (a
"backlog" wave, a "step2delta" wave of buildings added later, and for
Madrid/Bologna a "finding253_remedy" wave that re-ran a handful of
previously-FAILED stems with a bug fix). This script fetches every wave's
`out/<stem>/` directory contents, merges them per district with later waves
in `DISTRICT_WAVES` overriding earlier ones for any stem present in both,
then joins the merged per-stem results against the district's FINAL
population snapshot (`prepared_buildings.csv` + `fleet.lst` under
`<DISTRICT>_ceiling82_2026-09-05/`) and writes the final manifest +
summary.json.

This generalizes `scripts/cluster/harvest_eu11_district.py` (single job per
district) — see that script's docstring for the cluster rules this follows
(no compute on the Speed login node; file lists expanded remotely).

Usage:
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_ceiling82_final.py --district ES-MAD-BERRUGUETE
    .venv/Scripts/python.exe scripts/cluster/harvest_eu11_ceiling82_final.py --all

Outputs (per district):
    openubem/outputs/eu_evidence/EU-11/<DISTRICT>_ceiling82_2026-09-05/<slug>_manifest.csv
    openubem/outputs/eu_evidence/EU-11/<DISTRICT>_ceiling82_2026-09-05/summary.json
        (post-run; pre-run copy kept as summary_prerun.json)
"""
from __future__ import annotations

import argparse
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

# Per-district waves, in precedence order: list index 0 = lowest precedence,
# later entries OVERRIDE earlier ones for any stem present in both (matched
# by out/<stem>/ directory name). Bologna's first wave has an unusual remote
# dir name because that job is dual-purposed: it is both the FINDING-249
# remedy full-fleet rerun and the district's backlog job.
DISTRICT_WAVES = {
    "GB-LDN-STDUNSTANS": [
        ("EU11_GB-LDN-STDUNSTANS_backlog_2026-09-05", 1306951),
        ("EU11_GB-LDN-STDUNSTANS_step2delta_2026-09-05", 1308150),
    ],
    "FR-LYO-HAUTCOEURPENTES": [
        ("EU11_FR-LYO-HAUTCOEURPENTES_backlog_2026-09-05", 1306952),
        ("EU11_FR-LYO-HAUTCOEURPENTES_step2delta_2026-09-05", 1308159),
    ],
    "ES-MAD-BERRUGUETE": [
        ("EU11_ES-MAD-BERRUGUETE_backlog_2026-09-05", 1306953),
        ("EU11_ES-MAD-BERRUGUETE_step2delta_2026-09-05", 1308160),
        ("EU11_ES-MAD-BERRUGUETE_finding253_remedy_2026-09-05", 1309355),
    ],
    "IT-BOL-GALVANI2": [
        ("EU11_IT-BOL-GALVANI2_finding249_remedy_2026-09-04", 1305186),
        ("EU11_IT-BOL-GALVANI2_step2delta_2026-09-05", 1308161),
        ("EU11_IT-BOL-GALVANI2_finding253_remedy_2026-09-05", 1309357),
    ],
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

_EMPTY_TASK = {
    "eplus_return_code": pd.NA, "severe_errors": pd.NA, "fatal_errors": pd.NA,
    "heating_kwh": pd.NA, "platform": pd.NA, "energyplus_version": pd.NA,
}


# ── remote helpers (tcsh login shell: every command wrapped in bash -lc) ──────

def _ssh(cmd: str, timeout: int = 120) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def fetch_wave_out(remote_dir_name: str, dest_dir: Path) -> Path:
    """Fetch one wave's every task's out/<stem>/ directory contents.

    The file list (`*/eplusout.sql`, etc.) is a shell glob expanded by the
    remote login shell inside `out/`, never assembled locally.
    """
    remote_dir = f"{_REMOTE_FLEET_BASE}/{remote_dir_name}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"    fetching {remote_dir}/out ...")
    remote_cmd = (
        f"cd {remote_dir}/out && "
        f"tar czf - --ignore-failed-read "
        f"*/eplusout.sql */eplusout.err */eplusout.eio */task.rc "
        f"*/platform.txt */energyplus_version.txt"
    )
    tgz = dest_dir.parent / f"fetch_{remote_dir_name}.tgz"
    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE, text=True,
        )
        _, err = proc.communicate(timeout=3600)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(
            f"empty fetch for {remote_dir_name} (ssh rc={proc.returncode}); "
            f"{remote_dir}/out likely missing. remote stderr: {err.strip()[:400]}"
        )

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(dest_dir))
    tgz.unlink(missing_ok=True)

    n = len(list(dest_dir.iterdir()))
    print(f"    {n} task directories extracted from {remote_dir_name}")
    return dest_dir


def fetch_wave_fleet_lst(remote_dir_name: str) -> list[str]:
    raw = _ssh(f"cat {_REMOTE_FLEET_BASE}/{remote_dir_name}/fleet.lst")
    return [s.strip() for s in raw.splitlines() if s.strip()]


def fetch_sacct_elapsed(job_id: int) -> dict[int, int]:
    """Per-array-task elapsed seconds, keyed by array task index.

    `sacct` here is a listing/reading command (allowed on the login node),
    never compute. Excludes the `.batch`/`.extern` sub-steps that `sacct`
    also reports for every array task.
    """
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
        text = version_path.read_text(encoding="utf-8", errors="replace").strip()
        row["energyplus_version"] = text.splitlines()[0] if text else pd.NA

    return row


# ── merge waves, then harvest one district ─────────────────────────────────

def merge_district_waves(district: str, work_base: Path) -> tuple[dict[str, dict], dict[str, int], list[int]]:
    """Fetch every wave for a district and merge per-stem task/elapsed data.

    Later waves in DISTRICT_WAVES[district] override earlier ones for any
    stem whose out/<stem>/ directory actually exists in that wave's fetch.
    """
    waves = DISTRICT_WAVES[district]
    district_work = work_base / district
    district_work.mkdir(parents=True, exist_ok=True)

    merged_task: dict[str, dict] = {}
    merged_elapsed: dict[str, int] = {}
    job_ids: list[int] = []

    for remote_dir_name, job_id in waves:
        job_ids.append(job_id)
        print(f"  [{district}] wave {remote_dir_name} (job {job_id})")
        wave_dir = fetch_wave_out(remote_dir_name, district_work / remote_dir_name)
        wave_fleet = fetch_wave_fleet_lst(remote_dir_name)
        wave_sacct = fetch_sacct_elapsed(job_id)
        wave_elapsed_by_stem = {stem: wave_sacct.get(i + 1, pd.NA) for i, stem in enumerate(wave_fleet)}

        n_present = 0
        for stem in wave_fleet:
            bdir = wave_dir / stem
            if bdir.exists():
                merged_task[stem] = parse_task(bdir)
                merged_elapsed[stem] = wave_elapsed_by_stem.get(stem, pd.NA)
                n_present += 1
        print(f"  [{district}] wave {remote_dir_name}: {n_present}/{len(wave_fleet)} stems merged in")

    return merged_task, merged_elapsed, job_ids


def harvest_district_final(district: str, work_base: Path) -> tuple[dict, list[str]]:
    dist_dir = EVIDENCE_ROOT / f"{district}_ceiling82_2026-09-05"
    prepared_path = dist_dir / "prepared_buildings.csv"
    if not prepared_path.exists():
        raise FileNotFoundError(f"missing {prepared_path}")
    prepared = pd.read_csv(prepared_path, dtype=str)

    fleet_lst = [s.strip() for s in (dist_dir / "fleet.lst").read_text(encoding="utf-8").splitlines() if s.strip()]

    merged_task, merged_elapsed, job_ids = merge_district_waves(district, work_base)

    rows = []
    missing_stems: list[str] = []
    for stem in fleet_lst:
        prow = prepared[prepared["stem"] == stem]
        if prow.empty:
            raise ValueError(f"fleet.lst stem {stem} not found in prepared_buildings.csv for {district}")
        prow = prow.iloc[0]
        floor_area_m2 = float(prow["floor_area_m2"])

        task = merged_task.get(stem)
        if task is None:
            missing_stems.append(stem)
            task = dict(_EMPTY_TASK)

        heating_kwh = task["heating_kwh"]
        eui = (heating_kwh / floor_area_m2) if (pd.notna(heating_kwh) and floor_area_m2 > 0) else pd.NA

        rows.append({
            "building_id": prow["building_id"],
            "archetype_id": prow["archetype_id"],
            "building_type": prow["building_type"],
            "age_band": prow["age_band"],
            "geometry_outcome": prow["geometry_outcome"],
            "construction_period_provenance": prow.get("construction_period_provenance", ""),
            "idf_sha256": prow["idf_sha256"],
            "weather_sha256": prow["weather_sha256"],
            "eplus_return_code": task["eplus_return_code"],
            "severe_errors": task["severe_errors"],
            "fatal_errors": task["fatal_errors"],
            "heating_kwh": round(heating_kwh, 6) if pd.notna(heating_kwh) else pd.NA,
            "floor_area_m2": round(floor_area_m2, 4),
            "eui_kwh_m2": round(eui, 6) if pd.notna(eui) else pd.NA,
            "run_seconds": merged_elapsed.get(stem, pd.NA),
            "platform": task["platform"],
            "energyplus_version": task["energyplus_version"],
        })

    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
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
        "speed_job_id": job_ids,
        "status": "HARVESTED_FROM_SPEED",
    }
    summary_path = dist_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  [{district}] summary written: {summary_path}")
    if missing_stems:
        print(f"  [{district}] WARNING: {len(missing_stems)} stems missing from all waves")
    print(f"  [{district}] run={n_run} success={n_success} failed={n_failed} pooled_eui={pooled_eui:.4f} kWh/m2"
          if n_success else f"  [{district}] run={n_run} success={n_success} failed={n_failed}")
    return summary, missing_stems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", choices=sorted(DISTRICT_WAVES), help="single district")
    parser.add_argument("--all", action="store_true", help="harvest all four ceiling82 districts")
    args = parser.parse_args()
    if not args.district and not args.all:
        parser.error("pass --district <NAME> or --all")

    districts = sorted(DISTRICT_WAVES) if args.all else [args.district]
    work_base = Path(tempfile.gettempdir()) / "ubem_eu11_ceiling82_harvest"
    work_base.mkdir(parents=True, exist_ok=True)
    print(f"EU-11 ceiling82 final harvest — work dir: {work_base}")

    summaries = {}
    all_missing = {}
    for district in districts:
        print(f"\n=== District: {district} ===")
        summaries[district], all_missing[district] = harvest_district_final(district, work_base)

    print("\n" + "=" * 80)
    for district, s in summaries.items():
        eui = s["pooled_eui_kwh_m2"]
        eui_txt = f"{eui:.4f} kWh/m2" if eui is not None else "n/a"
        missing = all_missing[district]
        missing_txt = f", missing={len(missing)}" if missing else ""
        print(f"{district}: run={s['population_run']} success={s['population_success']} "
              f"failed={s['population_failed_on_speed']} pooled_eui={eui_txt}{missing_txt}")
    print("=" * 80)


if __name__ == "__main__":
    main()
