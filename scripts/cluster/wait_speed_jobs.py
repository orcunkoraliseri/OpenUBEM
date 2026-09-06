"""Wait until all European campaign SLURM jobs finish on Speed, then exit cleanly.

Runs silently until all tasks in jobs 1305158, 1305167, 1305176, 1305186 have left the queue.
"""
from __future__ import annotations

import subprocess
import time
import sys

JOBS = "1305158,1305167,1305176,1305186"
cmd = ["ssh", "o_iseri@speed.encs.concordia.ca", f"bash -lc 'squeue -u o_iseri -h -j {JOBS}'"]

print(f"Waiting for jobs {JOBS} to finish on Speed...")
sys.stdout.flush()

while True:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            lines = [l for l in res.stdout.splitlines() if l.strip()]
            if not lines:
                time.sleep(10)
                check = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if check.returncode == 0 and not [l for l in check.stdout.splitlines() if l.strip()]:
                    print(f"All jobs ({JOBS}) have completed on Speed.")
                    sys.exit(0)
    except Exception:
        pass
    time.sleep(120)
