"""FLEET-06b (techtransfer block-6 plan) -- submit the 65,112-case scenario campaign to Speed.

Reads the FLEET-06a manifest (building_id, cell_name, output_idf_path; 65,112 rows =
8 cells x 8,139 buildings), packs the IDFs into one tarball (weather is NOT re-packed --
it is reused unmodified from the existing t07_resim_2026-09-09 remote weather directory,
since every one of the 8,139 building_ids already has a stem->epw mapping there), ships
it to Speed, and submits ONE `sbatch --array=1-65112%32 --time=7-00:00:00`.

Fire-and-forget: this script never polls the array job to completion.

Usage:
    .venv/Scripts/python.exe scripts/cluster/fleet06b_submit_2026-09-18.py
"""
from __future__ import annotations

import csv
import io
import os
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/openubem/fleets"
FLEET_TAG = "fleet06b_2026-09-18"
REMOTE_FLEET_DIR = f"{REMOTE_FLEET_BASE}/{FLEET_TAG}"
REMOTE_SBATCH_DIR = "/speed-scratch/o_iseri/openubem/scripts/cluster"
REMOTE_T07_WEATHER_DIR = f"{REMOTE_FLEET_BASE}/t07_resim_2026-09-09/weather"
REMOTE_T07_FLEET_LST = f"{REMOTE_FLEET_BASE}/t07_resim_2026-09-09/fleet.lst"

MANIFEST_PATH = Path(os.environ["TEMP"]) / "ubem_validation" / "fleet06a_campaign_2026-09-18" / "manifest_65112.csv"
WORK_DIR = Path(os.environ["TEMP"]) / "ubem_validation" / FLEET_TAG
WORK_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_T07_LST = WORK_DIR / "t07_fleet.lst"
LOCAL_TAR = Path(os.environ["TEMP"]) / f"{FLEET_TAG}.tar.gz"

EXPECTED_TOTAL = 65112
EXPECTED_BUILDINGS = 8139
EXPECTED_CELLS = 8


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def load_manifest() -> list[tuple[str, str, Path]]:
    rows = []
    with open(MANIFEST_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append((row["building_id"], row["cell_name"], Path(row["output_idf_path"])))
    return rows


def load_stem_to_epw() -> dict[str, str]:
    print(f"Fetching stem->epw mapping from {REMOTE_T07_FLEET_LST} ...")
    r = subprocess.run(
        ["scp", f"{REMOTE_HOST}:{REMOTE_T07_FLEET_LST}", str(LOCAL_T07_LST)],
        capture_output=True, text=True, timeout=300,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp of t07 fleet.lst failed rc={r.returncode}")
    mapping: dict[str, str] = {}
    with open(LOCAL_T07_LST, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line:
                continue
            stem, epw = line.split("\t")
            mapping[stem] = epw
    return mapping


def main() -> None:
    print("FLEET-06b -- loading manifest ...")
    rows = load_manifest()
    n = len(rows)
    print(f"Total case count: {n}")
    if n != EXPECTED_TOTAL:
        raise SystemExit(f"STOP: manifest row count {n} != expected {EXPECTED_TOTAL}")

    cells = sorted({c for _, c, _ in rows})
    buildings = {b for b, _, _ in rows}
    print(f"Cells ({len(cells)}): {cells}")
    print(f"Distinct buildings: {len(buildings)}")
    if len(cells) != EXPECTED_CELLS or len(buildings) != EXPECTED_BUILDINGS:
        raise SystemExit(
            f"STOP: expected {EXPECTED_CELLS} cells x {EXPECTED_BUILDINGS} buildings, "
            f"got {len(cells)} cells x {len(buildings)} buildings"
        )
    dupe_check = {(b, c) for b, c, _ in rows}
    if len(dupe_check) != n:
        raise SystemExit(f"STOP: duplicate (building_id, cell_name) pairs found: {n - len(dupe_check)}")

    stem_to_epw = load_stem_to_epw()
    missing_epw = sorted({b for b in buildings if b not in stem_to_epw})
    if missing_epw:
        raise SystemExit(f"STOP: {len(missing_epw)} building_ids have no epw mapping, e.g. {missing_epw[:10]}")
    unique_epws = sorted({stem_to_epw[b] for b in buildings})
    print(f"Unique EPWs referenced: {len(unique_epws)}")
    for e in unique_epws:
        print(" ", e)

    print(f"Packing tarball -> {LOCAL_TAR}")
    fleet_lst_lines = []
    missing_idf = []
    with tarfile.open(LOCAL_TAR, "w:gz", compresslevel=1) as tf:
        for i, (building_id, cell_name, idf_path) in enumerate(rows, start=1):
            if not idf_path.exists():
                missing_idf.append(str(idf_path))
                continue
            tf.add(str(idf_path), arcname=f"idfs/{cell_name}/{building_id}.idf")
            fleet_lst_lines.append(f"{cell_name}\t{building_id}\t{stem_to_epw[building_id]}")
            if i % 10000 == 0:
                print(f"  packed {i}/{n} ...", flush=True)

        fleet_lst_bytes = ("\n".join(fleet_lst_lines) + "\n").encode("utf-8")
        info = tarfile.TarInfo(name="fleet.lst")
        info.size = len(fleet_lst_bytes)
        tf.addfile(info, io.BytesIO(fleet_lst_bytes))

    if missing_idf:
        raise SystemExit(f"STOP: {len(missing_idf)} IDFs missing on disk, e.g. {missing_idf[:10]}")

    tar_size_mb = LOCAL_TAR.stat().st_size / 1e6
    print(f"Tarball built: {tar_size_mb:.1f} MB, {len(fleet_lst_lines)} fleet.lst lines")
    if len(fleet_lst_lines) != EXPECTED_TOTAL:
        raise SystemExit(f"STOP: fleet.lst line count {len(fleet_lst_lines)} != {EXPECTED_TOTAL}")

    print(f"Staging remote dir: {REMOTE_FLEET_DIR}")
    out = _ssh(f"mkdir -p {REMOTE_FLEET_DIR} {REMOTE_SBATCH_DIR}")
    print(out)

    print("Uploading tarball ...")
    r = subprocess.run(
        ["scp", str(LOCAL_TAR), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/fleet.tar.gz"],
        capture_output=True, text=True, timeout=7200,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp failed rc={r.returncode}")

    print("Uploading sbatch script ...")
    local_sbatch = REPO / "scripts" / "cluster" / "submit_fleet06b.sbatch"
    r = subprocess.run(
        ["scp", str(local_sbatch), f"{REMOTE_HOST}:{REMOTE_SBATCH_DIR}/submit_fleet06b.sbatch"],
        capture_output=True, text=True, timeout=300,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp of sbatch script failed rc={r.returncode}")

    print("Extracting remotely and linking weather ...")
    out = _ssh(
        f"cd {REMOTE_FLEET_DIR} && tar -xzf fleet.tar.gz && mkdir -p out && "
        f"cp -r {REMOTE_T07_WEATHER_DIR} weather && "
        f"echo FLEETLST_COUNT=$(wc -l < fleet.lst) && "
        f'echo IDF_COUNT=$(find idfs -name "*.idf" | wc -l) && '
        f"echo EPW_COUNT=$(ls weather | wc -l)",
        timeout=600,
    )
    print(out)

    print(f"Total case count: {n}. Parallel width (array throttle): 32.")
    print(f"Submitting sbatch --array=1-{n}%32 --time=7-00:00:00 ...")
    submit_cmd = (
        f"sbatch --array=1-{n}%32 --time=7-00:00:00 "
        f"--export=FLEET_DIR={REMOTE_FLEET_DIR} "
        f"{REMOTE_SBATCH_DIR}/submit_fleet06b.sbatch"
    )
    out = _ssh(submit_cmd, timeout=120)
    print(out)

    LOCAL_TAR.unlink(missing_ok=True)
    print("Done. Poll with: sacct -u o_iseri --format=JobID,State,Elapsed,ExitCode | grep fleet06b")


if __name__ == "__main__":
    main()
