"""V03 part B: Fetch cluster results and build local manifest.

Usage: python scripts/validation/v03_fetch.py <JOB_ID>
  JOB_ID: SLURM array job ID printed by v03_simulate_refs.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
OUT_BASE = Path(tempfile.gettempdir()) / "ubem_validation" / "level2"
REF_OUT = OUT_BASE / "ref_out"
REMOTE = "o_iseri@speed.encs.concordia.ca"
REMOTE_FLEET = "/speed-scratch/o_iseri/openubem/fleets/val2"


def ssh(cmd: str) -> str:
    result = subprocess.run(
        ["ssh", REMOTE, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=60,
    )
    return result.stdout.strip()


def main() -> None:
    job_id_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if not job_id_arg:
        job_id_file = OUT_BASE / "val2_job_id.txt"
        if job_id_file.exists():
            job_id_arg = job_id_file.read_text().strip()
    job_id = job_id_arg
    print(f"[V03-fetch] Job ID: {job_id}")

    fleet_lst_text = ssh(f"cat {REMOTE_FLEET}/fleet.lst")
    ids = [line.strip() for line in fleet_lst_text.splitlines() if line.strip()]
    n = len(ids)
    print(f"[V03-fetch] {n} buildings to fetch")

    REF_OUT.mkdir(parents=True, exist_ok=True)
    success, failed = 0, []
    for i, bname in enumerate(ids, 1):
        bdir = REF_OUT / bname
        bdir.mkdir(exist_ok=True)
        for f in ("eplusout.sql", "eplusout.err", "eplusout.end"):
            r = subprocess.run(
                ["scp", "-q",
                 f"{REMOTE}:{REMOTE_FLEET}/out/{bname}/{f}",
                 str(bdir / f)],
                capture_output=True, text=True, timeout=120,
            )
        end_path = bdir / "eplusout.end"
        if end_path.exists() and "Completed Successfully" in end_path.read_text(errors="replace"):
            success += 1
        else:
            failed.append(bname)
        if i % 10 == 0 or i == n:
            print(f"  fetched {i}/{n}  (success={success}  fail={len(failed)})")

    print(f"\n[V03-fetch] Fetch complete: {success}/{n} success")
    if failed:
        print(f"[V03-fetch] FAILED: {failed}")

    fleet_lst_local = REF_OUT / "fleet.lst"
    fleet_lst_local.write_text("\n".join(ids) + "\n")
    print(f"[V03-fetch] fleet.lst written: {fleet_lst_local}")

    if success < n:
        print(f"\n[V03-fetch] STOP: {n - success} simulations failed.")
        print("[V03-fetch] Inspect sacct + .err files; report to manager before continuing.")
        sacct = ssh(f"sacct -j {job_id} --format=JobID,State,ExitCode,Comment --noheader 2>&1 | head -40")
        print(f"\nsacct:\n{sacct}")
        sys.exit(1)

    print(f"\n[V03-fetch] All {n} completed. Run v03_extract_ref_eui.py next.")
    print("[V03-fetch] DONE")


if __name__ == "__main__":
    main()
