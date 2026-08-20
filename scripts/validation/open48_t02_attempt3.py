"""T02 (OPEN-55 acceptance test) attempt 3 — instrumented single-cell launcher.

Purpose: run v12_cell_pipeline.run_cell('nyc_suburban', ...) under T01's screen,
on the frozen run-2/run-3 GDF, into a BRAND-NEW output_subdir / remote fleet dir
so stale output can never be scored as a result (attempts 1 and 2 both left
1,589 stale remote directories at mtime 2026-08-18 18:08 that must not be
mistaken for this run's output).

Instrumentation added because attempts 1 and 2 both died unexplained:
  - attempt 1: clean exception, but the retry launcher's own log-truncation
    ('w' mode) destroyed the on-disk evidence.
  - attempt 2: silent local death mid IDF-generation, no traceback, no exit
    code ever recorded (the old detached-launcher pattern discarded it).

Fixes here:
  1. Log opened in append ('a') mode, never 'w' — this script's own log file
     name is unique to this attempt so append-vs-write is moot, but the rule
     is honoured literally anyway.
  2. Exit code captured the moment the child exits and written to a dedicated
     EXITCODE file (also append mode).
  3. Child stdout+stderr both redirected, unbuffered (-u), to the log.
  4. A heartbeat line (timestamp + phase-ish tail of the log + elapsed) is
     appended at least every 60s while the child runs, so a silent death is
     bounded in time.

Usage:
    .venv\\Scripts\\python.exe scripts\\validation\\open48_t02_attempt3.py
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

CELL = "nyc_suburban"
SRC_SUBDIR = "open48_refleet3"          # frozen source (run 3's original), read-only
NEW_SUBDIR = "open48_refleet3_t02a3"    # brand-new subdir -> brand-new remote fleet dir
EXPECTED_MD5 = "1198ed01bfd3b4463e50da0ae39d8e27"

RUN_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open48_t02_attempt3")
LOG_PATH = RUN_DIR / f"{CELL}.log"
HEARTBEAT_PATH = RUN_DIR / f"{CELL}.heartbeat.log"
EXITCODE_PATH = RUN_DIR / f"{CELL}.EXITCODE"

CHILD = (
    "import sys; sys.path.insert(0, r'{repo}'); "
    "from scripts.validation.v12_cell_pipeline import run_cell; "
    "run_cell('{cell}', output_subdir='{sub}')"
)


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _append(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8", errors="replace") as fh:
        fh.write(line if line.endswith("\n") else line + "\n")


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.strftime("%Y-%m-%d %H:%M:%S")
    _append(LOG_PATH, f"[{t_start}] === T02 attempt 3 launcher starting ===")

    src_gdf = Path(tempfile.gettempdir()) / "ubem_validation" / SRC_SUBDIR / CELL / "01_buildings.gpkg"
    if not src_gdf.exists():
        _append(LOG_PATH, f"STOP: frozen source GDF missing at {src_gdf}")
        print(f"STOP: frozen source GDF missing at {src_gdf}", flush=True)
        return 2
    src_md5 = _md5(src_gdf)
    _append(LOG_PATH, f"Frozen source GDF: {src_gdf} md5={src_md5}")
    if src_md5 != EXPECTED_MD5:
        _append(LOG_PATH, f"STOP: MD5 mismatch — expected {EXPECTED_MD5}, got {src_md5}")
        print(f"STOP: MD5 mismatch on frozen source", flush=True)
        return 3

    new_work_base = Path(tempfile.gettempdir()) / "ubem_validation" / NEW_SUBDIR / CELL
    new_work_base.mkdir(parents=True, exist_ok=True)
    new_gdf = new_work_base / "01_buildings.gpkg"
    if new_gdf.exists():
        _append(LOG_PATH, f"STOP: {new_gdf} already exists — refusing to overwrite, subdir not fresh.")
        print("STOP: destination GDF already exists, subdir not fresh", flush=True)
        return 4
    shutil.copy2(src_gdf, new_gdf)
    dst_md5 = _md5(new_gdf)
    _append(LOG_PATH, f"Seeded {new_gdf} md5={dst_md5} (copy, source untouched)")
    if dst_md5 != EXPECTED_MD5:
        _append(LOG_PATH, f"STOP: post-copy MD5 mismatch — {dst_md5}")
        print("STOP: post-copy MD5 mismatch", flush=True)
        return 5

    _append(LOG_PATH, f"PREFLIGHT OK — seeded GDF present, output_subdir={NEW_SUBDIR!r} "
                       f"(fresh; remote fleet dir will be /speed-scratch/o_iseri/fleets/"
                       f"{NEW_SUBDIR}_{CELL}, confirmed absent before launch)")

    child_code = CHILD.format(repo=REPO, cell=CELL, sub=NEW_SUBDIR)
    log_fh = open(LOG_PATH, "a", encoding="utf-8", errors="replace")
    log_fh.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] launching child: "
                 f"python -u -c \"{child_code}\"\n")
    log_fh.flush()

    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", child_code],
        cwd=str(REPO), stdout=log_fh, stderr=subprocess.STDOUT,
    )
    _append(HEARTBEAT_PATH, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] child launched pid={proc.pid}")
    print(f"launched pid={proc.pid}, log={LOG_PATH}, heartbeat={HEARTBEAT_PATH}, "
          f"exitcode_file={EXITCODE_PATH}", flush=True)

    t0 = time.monotonic()
    last_beat = t0
    while True:
        rc = proc.poll()
        now = time.monotonic()
        if rc is not None:
            break
        if now - last_beat >= 60:
            elapsed_min = (now - t0) / 60.0
            log_size = LOG_PATH.stat().st_size if LOG_PATH.exists() else -1
            _append(HEARTBEAT_PATH,
                    f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] alive pid={proc.pid} "
                    f"elapsed={elapsed_min:.1f}min log_bytes={log_size}")
            last_beat = now
        time.sleep(5)

    elapsed_min = (time.monotonic() - t0) / 60.0
    _append(EXITCODE_PATH, f"{rc}")
    _append(HEARTBEAT_PATH,
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] child EXITED pid={proc.pid} "
            f"rc={rc} elapsed={elapsed_min:.1f}min")
    log_fh.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] child exited rc={rc} "
                 f"elapsed={elapsed_min:.1f}min\n")
    log_fh.close()
    print(f"child exited rc={rc} elapsed={elapsed_min:.1f}min", flush=True)
    return rc if rc is not None else 99


if __name__ == "__main__":
    raise SystemExit(main())
