"""Adapter: fetched cluster results directory → Step-4-compatible 04_simulation_manifest.parquet.

F8 manifest columns:
    osm_id, idf_path, work_dir, sql_path, status, n_warnings, n_severe,
    wall_clock_s, ep_version, epw_path, error_summary
"""

import re
import sys
import argparse
import subprocess
from pathlib import Path

import pandas as pd


EPW_NAME = "USA_MA_Boston.994971_TMYx.2011-2025.epw"
EP_VERSION = "23.1"
REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"


def parse_end_file(end_path: Path) -> str:
    """Return 'success' or 'failed' based on eplusout.end content."""
    if not end_path.exists():
        return "failed"
    text = end_path.read_text(errors="replace")
    if "EnergyPlus Completed Successfully" in text:
        return "success"
    return "failed"


def parse_err_file(err_path: Path) -> tuple[int, int, str]:
    """Return (n_warnings, n_severe, error_summary) from eplusout.err."""
    if not err_path.exists():
        return 0, 0, "err file missing"
    text = err_path.read_text(errors="replace")

    # Use the FINAL summary line ("Completed Successfully-- N Warning; M Severe")
    # — earlier Warmup/Sizing summary lines would otherwise match first with 0/0.
    summary_matches = re.findall(r"(\d+)\s+Warning;\s*(\d+)\s+Severe", text)
    if summary_matches:
        n_warnings, n_severe = (int(v) for v in summary_matches[-1])
    else:
        n_warnings, n_severe = 0, 0

    # Collect first severe line for summary
    from openubem.results.err_parse import first_severe
    error_summary = first_severe(text)
    return n_warnings, n_severe, error_summary


def get_sacct_elapsed(job_id: str) -> dict[str, float]:
    """Query sacct for per-task elapsed seconds; returns {array_task_str: seconds}."""
    if not job_id:
        return {}
    try:
        out = subprocess.run(
            ["ssh", REMOTE_HOST,
             f"bash -lc 'sacct -j {job_id} --format=JobID,Elapsed --noheader 2>&1'"],
            capture_output=True, text=True, timeout=30
        ).stdout
        elapsed_map = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            job_part, elapsed = parts[0], parts[1]
            if "_" not in job_part or "." in job_part:
                continue
            h, m, s = elapsed.split(":")
            seconds = int(h) * 3600 + int(m) * 60 + int(s)
            elapsed_map[job_part] = float(seconds)
        return elapsed_map
    except Exception:
        return {}


def build_manifest(
    fleet_dir: Path,
    idf_source_dir: Path,
    epw_path: Path,
    job_id: str = "",
    osm_ids: list[str] | None = None,
) -> pd.DataFrame:
    results_dir = fleet_dir

    if osm_ids is None:
        lst = fleet_dir / "fleet.lst"
        if not lst.exists():
            lst = fleet_dir.parent / "fleet.lst"
        if lst.exists():
            osm_ids = [l.strip() for l in lst.read_text().splitlines() if l.strip()]
        else:
            osm_ids = sorted(
                p.name for p in results_dir.iterdir()
                if p.is_dir() and p.name.isdigit()
            )

    sacct = get_sacct_elapsed(job_id)
    # sacct keys look like "955100_1", "955100_2" — map by index if we have them
    sacct_by_idx = {int(k.split("_")[1]): v for k, v in sacct.items() if "_" in k}

    rows = []
    for idx, osm_id in enumerate(osm_ids, start=1):
        bdir = results_dir / osm_id
        sql_path = bdir / "eplusout.sql"
        end_path = bdir / "eplusout.end"
        err_path = bdir / "eplusout.err"

        status = parse_end_file(end_path)
        n_warnings, n_severe, error_summary = parse_err_file(err_path)
        wall_clock_s = sacct_by_idx.get(idx, 0.0)

        rows.append({
            "osm_id": int(osm_id),
            "idf_path": str(idf_source_dir / f"{osm_id}.idf"),
            "work_dir": str(bdir),
            "sql_path": str(sql_path) if sql_path.exists() else "",
            "status": status,
            "n_warnings": n_warnings,
            "n_severe": n_severe,
            "wall_clock_s": wall_clock_s,
            "ep_version": EP_VERSION,
            "epw_path": str(epw_path),
            "error_summary": error_summary,
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Build Step-4 manifest from cluster results")
    parser.add_argument("results_dir", help="Local directory with per-building subdirs (fetched from cluster)")
    parser.add_argument("output_parquet", help="Output .parquet path")
    parser.add_argument("--idf-dir", default="", help="Directory containing source IDFs")
    parser.add_argument("--epw", default="", help="Path to EPW file")
    parser.add_argument("--job-id", default="", help="SLURM job ID for sacct elapsed lookup")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    idf_dir = Path(args.idf_dir) if args.idf_dir else results_dir.parent / "idfs"
    epw_path = Path(args.epw) if args.epw else results_dir.parent / "weather" / EPW_NAME

    df = build_manifest(results_dir, idf_dir, epw_path, job_id=args.job_id)
    print(df[["osm_id", "status", "n_warnings", "n_severe", "wall_clock_s"]].to_string())

    Path(args.output_parquet).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.output_parquet, index=False)
    print(f"\nManifest written: {args.output_parquet}  ({len(df)} rows)")


if __name__ == "__main__":
    main()
