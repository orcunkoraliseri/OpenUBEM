"""V03 part A: Pack the 31 reference IDFs and ship to cluster for simulation.

Stages refs_work/ copies (all 31) + EPW to /speed-scratch/o_iseri/openubem/fleets/val2/
Submits submit_fleet.sbatch array with N=31, throttle 16, --time=03:00:00.
Prints the SLURM job ID for use with v03_fetch.py.

Run after V01 has populated refs_work/ (copies already there; this script copies
any missing ones from the source if needed).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
REF_DIR = REPO / "docs" / "validations" / "Level 2 DOE round-trip" / "00.BaselineBuildings_NUs"
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
REFS_WORK = OUT_BASE / "refs_work_v23"

REMOTE = "o_iseri@speed.encs.concordia.ca"
REMOTE_BASE = "/speed-scratch/o_iseri/openubem"
REMOTE_FLEET = f"{REMOTE_BASE}/fleets/val2"
REMOTE_SBATCH = f"{REMOTE_BASE}/scripts/submit_fleet.sbatch"
SBATCH_LOCAL = REPO / "scripts" / "cluster" / "submit_fleet.sbatch"
THROTTLE = 16
TIME_LIMIT = "03:00:00"


def ssh(cmd: str, check: bool = True) -> str:
    result = subprocess.run(
        ["ssh", REMOTE, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=60,
        check=check,
    )
    return result.stdout.strip()


def _ensure_refs_work() -> list[str]:
    REFS_WORK.mkdir(parents=True, exist_ok=True)
    epw_txt = OUT_BASE / "epw_path.txt"
    if not epw_txt.exists():
        print("[V03] ERROR: epw_path.txt not found — run V02 first.")
        sys.exit(1)
    epw_src = Path(epw_txt.read_text().strip())
    if not epw_src.exists():
        print(f"[V03] ERROR: EPW not found at {epw_src}")
        sys.exit(1)

    idf_files = sorted(REF_DIR.glob("*.idf"))
    if len(idf_files) != 31:
        print(f"[V03] WARNING: expected 31 IDFs, found {len(idf_files)}")

    ids = []
    for idf in idf_files:
        dst = REFS_WORK / idf.name
        if not dst.exists():
            shutil.copy2(idf, dst)
        ids.append(idf.stem)
    return ids, epw_src


def main() -> None:
    ids, epw_src = _ensure_refs_work()
    n = len(ids)
    print(f"[V03] {n} IDFs staged in {REFS_WORK}")

    wx_dir = OUT_BASE / "weather"
    wx_dir.mkdir(exist_ok=True)
    epw_dst = wx_dir / epw_src.name
    if not epw_dst.exists():
        shutil.copy2(epw_src, epw_dst)

    fleet_lst = OUT_BASE / "fleet_val2.lst"
    fleet_lst.write_bytes(("\n".join(ids) + "\n").encode("utf-8"))

    tarball = OUT_BASE / "val2.tar.gz"
    print(f"[V03] Packing tarball: {tarball}")
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(REFS_WORK, arcname="idfs")
        tf.add(wx_dir, arcname="weather")
        tf.add(fleet_lst, arcname="fleet.lst")

    print(f"[V03] Creating remote fleet dir: {REMOTE_FLEET}")
    ssh(f"mkdir -p {REMOTE_FLEET}")

    print(f"[V03] Uploading tarball via scp ...")
    subprocess.run(
        ["scp", str(tarball), f"{REMOTE}:{REMOTE_FLEET}/val2.tar.gz"],
        check=True,
    )

    print(f"[V03] Extracting on cluster ...")
    ssh(f"cd {REMOTE_FLEET} && tar -xzf val2.tar.gz && rm val2.tar.gz")

    print(f"[V03] Uploading sbatch script ...")
    subprocess.run(
        ["scp", str(SBATCH_LOCAL), f"{REMOTE}:{REMOTE_BASE}/scripts/submit_fleet.sbatch"],
        check=True,
    )

    print(f"[V03] Submitting SLURM array (N={n}, throttle={THROTTLE}, time={TIME_LIMIT}) ...")
    sbatch_out = subprocess.run(
        ["ssh", REMOTE,
         f"bash -lc 'sbatch --array=1-{n}%{THROTTLE} --time={TIME_LIMIT} "
         f"--export=FLEET_DIR={REMOTE_FLEET} {REMOTE_SBATCH}'"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"[V03] sbatch output: {sbatch_out}")

    job_id = sbatch_out.split()[-1]
    job_id_file = OUT_BASE / "val2_job_id.txt"
    job_id_file.write_text(job_id)
    print(f"[V03] Job ID: {job_id} (written to {job_id_file})")
    print(f"[V03] Monitor with: ssh {REMOTE} bash -lc 'squeue -j {job_id}'")
    print(f"[V03] When done: python scripts/validation/v03_fetch.py {job_id}")
    print("[V03] DONE")


if __name__ == "__main__":
    main()
