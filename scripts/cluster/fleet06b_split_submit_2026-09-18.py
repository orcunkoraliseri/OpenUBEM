"""FLEET-06b split-submit (techtransfer block-6 plan, section 2d decision 2026-09-18).

Speed's SLURM MaxArraySize=10001 blocks a single `--array=1-65112%32` job. Per the pinned
decision in PLAN_techtransfer-block6-2026-09-18.md section 2d: split into 7 array jobs,
chained strictly sequentially via `--dependency=afterany:<previous_job_id>`, each
`--array=1-N%32 --time=7-00:00:00`. Contiguous manifest slices in row order: 6 x 9,302 +
1 x 9,300 = 65,112. Only one job's array is ever active at a time, so the account-wide
32-concurrent cap is respected exactly.

Reuses the already-staged remote directory (no re-upload of IDFs/weather): fetches the
already-extracted remote fleet.lst (65,112 lines, verified by FLEET-06b), slices it
locally into 7 contiguous chunks, uploads the 7 slice files, then submits the 7 chained
sbatch jobs from the login node (sbatch only -- no srun/ssh...python compute there).

Usage:
    .venv/Scripts/python.exe scripts/cluster/fleet06b_split_submit_2026-09-18.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/openubem/fleets"
FLEET_TAG = "fleet06b_2026-09-18"
REMOTE_FLEET_DIR = f"{REMOTE_FLEET_BASE}/{FLEET_TAG}"
REMOTE_SBATCH_DIR = "/speed-scratch/o_iseri/openubem/scripts/cluster"
REMOTE_SBATCH_SCRIPT = f"{REMOTE_SBATCH_DIR}/submit_fleet06b.sbatch"

WORK_DIR = Path(__import__("os").environ["TEMP"]) / "ubem_validation" / FLEET_TAG
WORK_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_FULL_LST = WORK_DIR / "remote_fleet.lst"

EXPECTED_TOTAL = 65112
SLICE_SIZES = [9302, 9302, 9302, 9302, 9302, 9302, 9300]
assert sum(SLICE_SIZES) == EXPECTED_TOTAL, sum(SLICE_SIZES)


def _ssh(cmd: str, timeout: int = 300) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def fetch_full_lst() -> list[str]:
    print(f"Fetching remote fleet.lst from {REMOTE_FLEET_DIR}/fleet.lst ...")
    r = subprocess.run(
        ["scp", f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/fleet.lst", str(LOCAL_FULL_LST)],
        capture_output=True, text=True, timeout=300,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp of remote fleet.lst failed rc={r.returncode}")
    lines = LOCAL_FULL_LST.read_text(encoding="utf-8").splitlines()
    lines = [ln for ln in lines if ln.strip()]
    print(f"Remote fleet.lst line count: {len(lines)}")
    if len(lines) != EXPECTED_TOTAL:
        raise SystemExit(f"STOP: remote fleet.lst has {len(lines)} lines != expected {EXPECTED_TOTAL}")
    return lines


def write_and_upload_slices(lines: list[str]) -> list[tuple[str, int]]:
    slices: list[tuple[str, int]] = []
    offset = 0
    for i, size in enumerate(SLICE_SIZES, start=1):
        chunk = lines[offset:offset + size]
        if len(chunk) != size:
            raise SystemExit(f"STOP: slice {i} expected {size} rows, got {len(chunk)}")
        local_path = WORK_DIR / f"fleet.lst.{i}"
        local_path.write_text("\n".join(chunk) + "\n", encoding="utf-8")
        remote_name = f"fleet.lst.{i}"
        r = subprocess.run(
            ["scp", str(local_path), f"{REMOTE_HOST}:{REMOTE_FLEET_DIR}/{remote_name}"],
            capture_output=True, text=True, timeout=300,
        )
        print(f"Uploaded slice {i} ({size} rows) -> {remote_name}: rc={r.returncode}")
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            raise SystemExit(f"STOP: scp of slice {i} failed rc={r.returncode}")
        slices.append((remote_name, size))
        offset += size
    if offset != EXPECTED_TOTAL:
        raise SystemExit(f"STOP: slices covered {offset} rows != expected {EXPECTED_TOTAL}")
    return slices


def upload_sbatch_script() -> None:
    local_sbatch = REPO / "scripts" / "cluster" / "submit_fleet06b.sbatch"
    r = subprocess.run(
        ["scp", str(local_sbatch), f"{REMOTE_HOST}:{REMOTE_SBATCH_SCRIPT}"],
        capture_output=True, text=True, timeout=300,
    )
    print(r.stdout, r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"STOP: scp of sbatch script failed rc={r.returncode}")


def submit_chain(slices: list[tuple[str, int]]) -> list[str]:
    job_ids: list[str] = []
    prev_id: str | None = None
    for i, (remote_lst, size) in enumerate(slices, start=1):
        dep = f"--dependency=afterany:{prev_id} " if prev_id else ""
        cmd = (
            f"sbatch --array=1-{size}%32 --time=7-00:00:00 {dep}"
            f"--export=FLEET_DIR={REMOTE_FLEET_DIR},FLEET_LST={remote_lst} "
            f"{REMOTE_SBATCH_SCRIPT}"
        )
        print(f"Submitting job {i}/7 ({size} tasks){' dep=' + prev_id if prev_id else ''} ...")
        out = _ssh(cmd, timeout=120)
        print(out.strip())
        line = out.strip().splitlines()[-1] if out.strip() else ""
        if not line.startswith("Submitted batch job"):
            raise SystemExit(f"STOP: job {i} submission did not return a job id. Output: {out}")
        job_id = line.split()[-1]
        job_ids.append(job_id)
        prev_id = job_id
    return job_ids


def main() -> None:
    lines = fetch_full_lst()
    slices = write_and_upload_slices(lines)
    upload_sbatch_script()
    print("Submitting 7 chained array jobs (afterany dependency, sequential) ...")
    job_ids = submit_chain(slices)
    print("Job IDs in chain order:", job_ids)
    for i, (jid, (remote_lst, size)) in enumerate(zip(job_ids, slices), start=1):
        print(f"  job {i}: id={jid} slice={remote_lst} size={size} array=1-{size}%32")
    print("Done. Poll with: squeue -u o_iseri ; sacct -u o_iseri --format=JobID,State,Elapsed,ExitCode | grep fleet06b")


if __name__ == "__main__":
    main()
