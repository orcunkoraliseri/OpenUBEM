"""C4.2 recovery: build 04_simulation_manifest.parquet from completed sim dirs.

Waits until all running EnergyPlus processes finish, then reconstructs the manifest
from disk without calling run_neighbourhood (which would try to delete locked dirs).
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

SIM_DIR = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_boston_c4/sim")
STEP3_DIR = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_boston_c4/step3")
EPW_PATH = "C:/Users/o_iseri/AppData/Local/Temp/openubem_epw_7rrpvd27/weather/USA_MA_Boston.994971_TMYx.2011-2025.epw"


def _ep_running() -> int:
    r = subprocess.run(["tasklist", "/fi", "imagename eq EnergyPlus.exe"], capture_output=True, text=True)
    return r.stdout.lower().count("energyplus.exe")


def _count_completed() -> int:
    marker = "EnergyPlus Completed Successfully"
    return sum(
        1 for f in SIM_DIR.rglob("eplusout.end")
        if marker in f.read_text(errors="replace")
    )


# ── Wait for EnergyPlus to finish ────────────────────────────────────────────
print("[manifest] Waiting for EnergyPlus processes to finish...")
while True:
    n_ep = _ep_running()
    n_ok = _count_completed()
    print(f"  ep_procs={n_ep} completed={n_ok}/479")
    if n_ep == 0:
        print("[manifest] All EnergyPlus processes done.")
        break
    time.sleep(30)

# ── Final count ───────────────────────────────────────────────────────────────
n_ok = _count_completed()
print(f"[manifest] Total completed: {n_ok}")

# ── Load IDF manifest ─────────────────────────────────────────────────────────
idf_mf = pd.read_parquet(STEP3_DIR / "03_idf_manifest.parquet")
print(f"[manifest] IDF manifest: {len(idf_mf)} rows")

# ── Reconstruct sim manifest from disk ───────────────────────────────────────
from openubem.simulation.runner import _SUCCESS_MARKER, _FATAL_MARKER, _parse_end_counts
from openubem import config

ep_version = "23.1.0"
rows = []

simulable = idf_mf[idf_mf["generation_status"] == "success"]
skipped = idf_mf[idf_mf["generation_status"] != "success"]

for _, row in simulable.iterrows():
    osm_id = str(row["osm_id"])
    idf_path = str(row["idf_path"])
    wd = SIM_DIR / osm_id
    end_file = wd / "eplusout.end"
    sql_file = wd / "eplusout.sql"

    if end_file.exists() and sql_file.exists():
        end_text = end_file.read_text(errors="replace")
        n_warn, n_sev = _parse_end_counts(end_text)

        if _SUCCESS_MARKER in end_text:
            status = "success"
            sql_path = str(sql_file)
            # Purge non-retained files
            for f in wd.iterdir():
                if f.is_file() and f.name not in config.SIM_RETAIN_FILES:
                    try:
                        f.unlink()
                    except Exception:
                        pass
        elif _FATAL_MARKER in end_text:
            status = "failed_fatal"
            sql_path = ""
        else:
            status = "failed_crash"
            sql_path = ""

        rows.append({
            "osm_id": osm_id,
            "idf_path": idf_path,
            "work_dir": str(wd),
            "sql_path": sql_path,
            "status": status,
            "n_warnings": n_warn,
            "n_severe": n_sev,
            "wall_clock_s": 0.0,
            "ep_version": ep_version,
            "epw_path": EPW_PATH,
            "error_summary": "",
        })
    elif wd.exists() and any(wd.iterdir()):
        # Partial dir with no .end file — timed out or crashed mid-run
        rows.append({
            "osm_id": osm_id,
            "idf_path": idf_path,
            "work_dir": str(wd),
            "sql_path": "",
            "status": "failed_crash",
            "n_warnings": None,
            "n_severe": None,
            "wall_clock_s": 0.0,
            "ep_version": ep_version,
            "epw_path": EPW_PATH,
            "error_summary": "no eplusout.end found",
        })
    else:
        rows.append({
            "osm_id": osm_id,
            "idf_path": idf_path,
            "work_dir": "",
            "sql_path": "",
            "status": "not_attempted_invalid_idf",
            "n_warnings": None,
            "n_severe": None,
            "wall_clock_s": 0.0,
            "ep_version": ep_version,
            "epw_path": EPW_PATH,
            "error_summary": "work_dir not found",
        })

for _, sk in skipped.iterrows():
    rows.append({
        "osm_id": str(sk["osm_id"]),
        "idf_path": str(sk.get("idf_path", "")) or "",
        "work_dir": "",
        "sql_path": "",
        "status": "not_attempted_invalid_idf",
        "n_warnings": None,
        "n_severe": None,
        "wall_clock_s": 0.0,
        "ep_version": ep_version,
        "epw_path": "",
        "error_summary": str(sk.get("generation_status", "")) or "",
    })

# ── Enforce schema ────────────────────────────────────────────────────────────
sim_mf = pd.DataFrame(rows)
sim_mf["n_warnings"] = sim_mf["n_warnings"].astype("Int64")
sim_mf["n_severe"] = sim_mf["n_severe"].astype("Int64")
sim_mf["error_summary"] = sim_mf["error_summary"].fillna("")

out_path = SIM_DIR / "04_simulation_manifest.parquet"
sim_mf.to_parquet(out_path, index=False)
print(f"[manifest] Written: {out_path}")
print(f"[manifest] Status counts: {sim_mf['status'].value_counts().to_dict()}")

n_success = (sim_mf["status"] == "success").sum()
n_cached = (sim_mf["status"] == "success_cached").sum()
print(f"[manifest] Success total: {n_success + n_cached} / {len(sim_mf)}")
print("[manifest] DONE")
