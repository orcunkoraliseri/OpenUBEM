"""Fetch la_centre simulation outputs from cluster using streaming tar."""
from __future__ import annotations
import subprocess
import sys
import tarfile
import time
from pathlib import Path
import tempfile

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET_DIR = "/speed-scratch/o_iseri/fleets/la_centre"
CELL_NAME = "la_centre"
WORK_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "cases" / CELL_NAME
SIM_OUT_DIR = WORK_BASE / "sim_out"


def fetch_streaming() -> None:
    SIM_OUT_DIR.mkdir(parents=True, exist_ok=True)
    remote_cmd = (
        f"cd {REMOTE_FLEET_DIR}/out && "
        f"find . -maxdepth 2 \\( -name eplusout.sql -o -name eplusout.err -o -name eplusout.end \\) -print0 "
        f"| tar czf - --null -T -"
    )
    print(f"Fetching from {REMOTE_FLEET_DIR}/out ...")
    t0 = time.monotonic()
    # Write to a temp tgz file first
    tgz_path = WORK_BASE / "sim_out_fetch.tgz"
    with open(tgz_path, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, f"bash -lc '{remote_cmd}'"],
            stdout=fh, stderr=subprocess.PIPE,
        )
        _, stderr_data = proc.communicate(timeout=7200)
    if proc.returncode != 0:
        err = stderr_data.decode(errors="replace")[:500]
        print(f"SSH error rc={proc.returncode}: {err}", file=sys.stderr)
        sys.exit(1)
    sz_mb = tgz_path.stat().st_size / 1e6
    print(f"Downloaded {sz_mb:.1f} MB in {time.monotonic()-t0:.0f}s")

    print(f"Extracting ...")
    t0 = time.monotonic()
    with tarfile.open(tgz_path, mode="r:gz") as tf:
        tf.extractall(str(SIM_OUT_DIR))
    print(f"Extracted in {time.monotonic()-t0:.0f}s")
    tgz_path.unlink()

    n_end = len(list(SIM_OUT_DIR.rglob("eplusout.end")))
    n_sql = len(list(SIM_OUT_DIR.rglob("eplusout.sql")))
    print(f"Result: {n_end} .end files, {n_sql} .sql files in {SIM_OUT_DIR}")


if __name__ == "__main__":
    fetch_streaming()
