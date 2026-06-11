"""Module 12a: single-building EnergyPlus subprocess + outcome classification (DESIGN §3C, §3E)."""
from __future__ import annotations

import re
import sys
import time
import subprocess
from pathlib import Path

from openubem import config

# Resolve platform-appropriate binary path (P1: platform-aware, not DESIGN §3C naive sketch)
_EXE_NAME = "energyplus.exe" if sys.platform == "win32" else "energyplus"


def _exe() -> Path:
    return config.ENERGYPLUS_PATH / _EXE_NAME


def _version_handshake() -> str:
    """Run energyplus --version once; assert starts with ENERGYPLUS_VERSION (F5, P2)."""
    exe = _exe()
    try:
        result = subprocess.run(
            [str(exe), "--version"],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout + result.stderr
    except FileNotFoundError:
        raise RuntimeError(
            f"EnergyPlus binary not found at {exe}. "
            f"Set ENERGYPLUS_PATH env var or install EnergyPlus {config.ENERGYPLUS_VERSION}."
        )
    # Parse version token: "EnergyPlus, Version 23.1.0-..." or "EnergyPlus Version 23.1.0"
    m = re.search(r"Version\s+([\d.]+)", output, re.IGNORECASE)
    if not m:
        raise RuntimeError(
            f"Could not parse EnergyPlus version from output: {output!r}"
        )
    found = m.group(1)
    if not found.startswith(config.ENERGYPLUS_VERSION):
        raise RuntimeError(
            f"EnergyPlus version mismatch: expected {config.ENERGYPLUS_VERSION!r}, "
            f"found {found!r}. Set ENERGYPLUS_PATH to the correct installation."
        )
    return found


def run_energyplus(task, timeout_s: int = config.SIM_TIMEOUT_S) -> dict:
    """Launch one EnergyPlus process for task; return raw result dict (DESIGN §3C, F4)."""
    work_dir = Path(task.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(_exe()),
        "-w", task.epw_path,
        "-d", task.work_dir,
        "-x",   # ExpandObjects — REQUIRED (DESIGN §3C: HVACTemplate objects in every IDF)
        "-r",   # readVarsESO → eplusout.csv (Stage-5 fallback contract)
        task.idf_path,
    ]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=task.work_dir,
            capture_output=True, text=True, timeout=timeout_s,
        )
        wall = time.monotonic() - t0
        (work_dir / "openubem_run.log").write_text(
            proc.stdout + "\n--- STDERR ---\n" + proc.stderr,
            encoding="utf-8", errors="replace",
        )
        return {
            "osm_id": task.osm_id,
            "returncode": proc.returncode,
            "wall_clock_s": wall,
            "timed_out": False,
            "_stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        # kill is triggered by subprocess on TimeoutExpired (F6)
        return {
            "osm_id": task.osm_id,
            "returncode": None,
            "wall_clock_s": float(timeout_s),
            "timed_out": True,
            "_stderr": "",
        }


_SUCCESS_MARKER = "EnergyPlus Completed Successfully"
_FATAL_MARKER = "EnergyPlus Terminated--Fatal Error Detected"
_END_COUNT_RE = re.compile(r"(\d+)\s+Warning.*?(\d+)\s+Severe", re.IGNORECASE)


def _parse_end_counts(end_text: str) -> tuple[int | None, int | None]:
    """Parse warning/severe counts from eplusout.end summary line (F8)."""
    m = _END_COUNT_RE.search(end_text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def classify_outcome(raw_result: dict, work_dir: Path) -> dict:
    """
    Map a raw subprocess result to a closed status token + manifest fields (DESIGN §3E, F8).

    First-match-wins order: failed_timeout → failed_crash → failed_fatal → success.
    """
    osm_id = raw_result["osm_id"]
    base = {
        "osm_id": osm_id,
        "wall_clock_s": raw_result.get("wall_clock_s", 0.0),
        "n_warnings": None,
        "n_severe": None,
        "error_summary": "",
    }

    # 1. Timeout (F8 row 1)
    if raw_result.get("timed_out"):
        return {**base, "status": "failed_timeout",
                "error_summary": f"killed at {config.SIM_TIMEOUT_S}s"}

    # 2. Crash: no eplusout.end (F8 row 2)
    end_file = work_dir / "eplusout.end"
    if not end_file.exists():
        stderr = raw_result.get("_stderr", "") or ""
        return {**base, "status": "failed_crash",
                "error_summary": stderr[-500:]}

    end_text = end_file.read_text(errors="replace")

    # 3. Fatal (F8 row 3)
    if _FATAL_MARKER in end_text:
        n_warn, n_sev = _parse_end_counts(end_text)
        err_summary = ""
        err_file = work_dir / "eplusout.err"
        if err_file.exists():
            for line in err_file.read_text(errors="replace").splitlines():
                if "**  Fatal  **" in line:
                    err_summary = line.strip()
                    break
        return {**base, "status": "failed_fatal",
                "n_warnings": n_warn, "n_severe": n_sev,
                "error_summary": err_summary}

    # 4. Success (F8 row 4)
    if _SUCCESS_MARKER in end_text:
        sql_file = work_dir / "eplusout.sql"
        if sql_file.exists():
            n_warn, n_sev = _parse_end_counts(end_text)
            return {**base, "status": "success",
                    "n_warnings": n_warn, "n_severe": n_sev}
        # .end says success but sql missing → treat as crash
        return {**base, "status": "failed_crash",
                "error_summary": "eplusout.sql missing despite success marker"}

    # 5. Fallback crash (unrecognised .end content)
    return {**base, "status": "failed_crash",
            "error_summary": end_text[-500:]}
