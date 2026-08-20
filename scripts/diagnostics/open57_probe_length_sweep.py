"""OPEN-57 — standalone transport probe for the tcsh `Unmatched '.` fault.

Reproduces `scripts/validation/v12_cell_pipeline.py`'s `_ssh` (:127) and
`_remote_results_complete` (:1002) transport byte-for-byte, WITHOUT importing that
module (plan §4.2) — so a failed experiment here cannot be attributed to any
module-level constant or side effect from the production pipeline.

Every call targets a remote directory that does not exist
(/speed-scratch/o_iseri/fleets/__open57_probe_nonexistent__), per plan §4.3, so the
`cd ... || exit 0` branch always short-circuits and no filesystem work happens on the
remote side. This makes the outcome a pure parse signal:
  - exit 0, empty stdout+stderr -> the command parsed
  - exit 1, stderr "Unmatched '."  -> the command did NOT parse

Usage: only ever invoked by this repo's own diagnostic tasks (T01-T03 of
docs/docs_ACTIVE/openings/implemenation/PLAN_open-57-and-58_2026-08-19.md), never on
its own from an ad hoc shell — always sequential, always logged.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
REMOTE_DIR = "/speed-scratch/o_iseri/fleets/__open57_probe_nonexistent__"

REPO = Path(__file__).parent.parent.parent
FROZEN_MANIFEST = (
    Path.home() / "AppData" / "Local" / "Temp" / "ubem_validation" /
    "open48_refleet3_t02a3" / "nyc_suburban" / "step3" / "03_idf_manifest.parquet"
)

LOG_PATH = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\210e1198-627d-476e-bf98-bffa15bc41b5\scratchpad\open57_probe_sweep.jsonl"
)


def build_probe(osm_ids: list[str], remote_fleet_dir: str = REMOTE_DIR) -> str:
    """Byte-identical to v12_cell_pipeline.py:1006-1012."""
    oid_list = " ".join(osm_ids)
    probe = (
        f"cd {remote_fleet_dir}/out 2>/dev/null || exit 0; "
        f"n=0; for o in {oid_list}; do "
        f'if [ -s "$o/eplusout.sql" ] && grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end" 2>/dev/null; '
        f"then n=$((n+1)); fi; done; echo COMPLETE=$n"
    )
    return probe


def load_real_ids() -> list[str]:
    """The frozen 1,589-id osm_id list from OPEN-55 attempt 3, still on disk.

    IDF-stem shape (way_605951159), identical to what v12_cell_pipeline.py:1078
    passes into _remote_results_complete. Falls back to a same-shape synthetic
    list if the frozen manifest is gone.
    """
    if FROZEN_MANIFEST.exists():
        import pandas as pd
        df = pd.read_parquet(FROZEN_MANIFEST)
        ids = [Path(str(p)).stem for p in df["idf_path"]]
        if len(ids) >= 1589:
            return ids
    print(
        "WARNING: frozen manifest not found or too short; synthesising "
        "same-shape ids (way_NNNNNNNNN, 13-14 chars) and recording this in the log.",
        file=sys.stderr,
    )
    return [f"way_{600000000 + i}" for i in range(1589)]


def ssh_call(cmd: str, timeout: int = 120) -> dict:
    """Exact transport of _ssh (v12_cell_pipeline.py:127-152), instrumented.

    Does not raise; every outcome (including timeout) is captured as data.
    """
    wrapper = f"bash -lc '{cmd}'"
    argv = ["ssh", REMOTE_HOST, wrapper]
    full_argv_str = " ".join(argv)
    t0 = time.time()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        wall = time.time() - t0
        return {
            "probe_len": len(cmd),
            "wrapper_len": len(wrapper),
            "argv_len": len(full_argv_str),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "wall_s": wall,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        wall = time.time() - t0
        return {
            "probe_len": len(cmd),
            "wrapper_len": len(wrapper),
            "argv_len": len(full_argv_str),
            "exit_code": None,
            "stdout": (exc.stdout or ""),
            "stderr": (exc.stderr or ""),
            "wall_s": wall,
            "timed_out": True,
        }


def run_probe(osm_ids: list[str], label: str, timeout: int = 120,
              remote_fleet_dir: str = REMOTE_DIR) -> dict:
    """Build+send one probe for `osm_ids`, append the record to LOG_PATH, return it."""
    probe = build_probe(osm_ids, remote_fleet_dir)
    record = ssh_call(probe, timeout=timeout)
    record["label"] = label
    record["id_count"] = len(osm_ids)
    record["remote_fleet_dir"] = remote_fleet_dir
    record["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(
        f"[{label}] n={record['id_count']} probe_len={record['probe_len']} "
        f"exit={record['exit_code']} timed_out={record['timed_out']} "
        f"stdout={record['stdout']!r} stderr={record['stderr']!r} "
        f"wall={record['wall_s']:.2f}s"
    )
    return record


def build_probe_variant(osm_ids: list[str], variant: str,
                         remote_fleet_dir: str = REMOTE_DIR) -> str:
    """T03: hold total probe length fixed, vary content.

    variant "real"          -> identical to build_probe (baseline, variant a).
    variant "single_token"  -> the id list collapsed into one token of the same
                                total character count (variant b).
    variant "no_quotes"     -> the two embedded double-quoted strings unquoted,
                                length restored with trailing pad spaces so the
                                total probe length is unchanged (variant c).
    """
    baseline = build_probe(osm_ids, remote_fleet_dir)
    if variant == "real":
        return baseline

    oid_list = " ".join(osm_ids)
    if variant == "single_token":
        token = "x" * len(oid_list)
        return (
            f"cd {remote_fleet_dir}/out 2>/dev/null || exit 0; "
            f"n=0; for o in {token}; do "
            f'if [ -s "$o/eplusout.sql" ] && grep -q "EnergyPlus Completed Successfully" "$o/eplusout.end" 2>/dev/null; '
            f"then n=$((n+1)); fi; done; echo COMPLETE=$n"
        )
    if variant == "no_quotes":
        probe = (
            f"cd {remote_fleet_dir}/out 2>/dev/null || exit 0; "
            f"n=0; for o in {oid_list}; do "
            f"if [ -s $o/eplusout.sql ] && grep -q EnergyPlus Completed Successfully $o/eplusout.end 2>/dev/null; "
            f"then n=$((n+1)); fi; done; echo COMPLETE=$n"
        )
        pad = len(baseline) - len(probe)
        if pad > 0:
            probe = probe + (" " * pad)
        elif pad < 0:
            raise ValueError(f"no_quotes variant is longer than baseline by {-pad} chars")
        return probe
    raise ValueError(f"unknown variant: {variant}")


def check_dir_absent(timeout: int = 30) -> dict:
    """One `ls` via the exact _ssh form, verifying REMOTE_DIR does not exist."""
    cmd = f"ls {REMOTE_DIR}"
    wrapper = f"bash -lc '{cmd}'"
    argv = ["ssh", REMOTE_HOST, wrapper]
    t0 = time.time()
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    wall = time.time() - t0
    record = {
        "label": "check_dir_absent",
        "id_count": 0,
        "probe_len": len(cmd),
        "wrapper_len": len(wrapper),
        "argv_len": len(" ".join(argv)),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "wall_s": wall,
        "timed_out": False,
        "remote_fleet_dir": REMOTE_DIR,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[check_dir_absent] exit={record['exit_code']} stderr={record['stderr']!r}")
    return record


if __name__ == "__main__":
    print("This module is imported by T01-T03 driver snippets, not run directly.")
