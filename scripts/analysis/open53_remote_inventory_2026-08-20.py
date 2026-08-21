"""OPEN-53 T05: is the missing 874/875 harvest files still on Speed, or never made?

Read-only on the login node (ls/find/wc/scp only, via the tcsh-safe `_ssh()` helper
imported from scripts/cluster/t08_harvest_results.py:104). No srun, no sbatch, no
`ssh ... python`.

Remote fleet-dir convention for the E02 harvest corpus (found by grep, not guessed):
scripts/analysis/e02_cluster_readonly_audit.py:35 REMOTE_FLEET_BASE =
"/speed-scratch/o_iseri/fleets"; directories named "e02_{cell}_{mode}/out/{stem}"
(same file, lines 143-224).

The 874 shortfall's location was established by
docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md section 3: 874 of 875
sit entirely in austin_suburban_fast_zone and austin_suburban_floor (100% of both), the
remaining 1 in nyc_centre_fast_zone/way_1240348353 (out of scope here, single directory).

Local shortfall corpus: C:\\Users\\o_iseri\\AppData\\Local\\Temp\\ubem_e02_harvest
(layout: <cell>_<mode>/<stem>/{eplusout.eio,eplusout.err}, .sql/.end absent).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "cluster"))
from t08_harvest_results import _ssh, REMOTE_HOST  # noqa: E402

sys.path.insert(0, str(REPO))
from openubem.results.parser import parse_building  # noqa: E402

REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
LOCAL_HARVEST = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
SAMPLE_DIR = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\89a28ab2-bc04-4d19-9e55-89a800c96691\scratchpad\open53_sample"
)
OUT = REPO / "openubem" / "outputs" / "comparisons" / "open53_remote_inventory_2026-08-20.csv"

CELL_MODES = ["austin_suburban_fast_zone", "austin_suburban_floor"]


def remote_out_dir(cell_mode: str) -> str:
    return f"{REMOTE_FLEET_BASE}/e02_{cell_mode}/out"


def main() -> int:
    rows = []

    # ── C14: remote counts for both extensions, both buckets ──────────────
    for cell_mode in CELL_MODES:
        d = remote_out_dir(cell_mode)
        exists = _ssh(f"test -d {d} && echo YES || echo NO", timeout=30).strip()
        n_dirs = _ssh(f"find {d} -mindepth 1 -maxdepth 1 -type d | wc -l", timeout=60).strip()
        n_sql = _ssh(f"find {d} -name eplusout.sql | wc -l", timeout=60).strip()
        n_end = _ssh(f"find {d} -name eplusout.end | wc -l", timeout=60).strip()
        local_n = sum(
            1 for p in (LOCAL_HARVEST / cell_mode).iterdir() if p.is_dir()
        ) if (LOCAL_HARVEST / cell_mode).exists() else -1
        local_missing_sql = sum(
            1 for p in (LOCAL_HARVEST / cell_mode).iterdir()
            if p.is_dir() and not (p / "eplusout.sql").exists()
        ) if (LOCAL_HARVEST / cell_mode).exists() else -1
        rows.append({
            "cell_mode": cell_mode, "remote_dir": d, "remote_exists": exists,
            "remote_n_dirs": n_dirs, "remote_n_sql": n_sql, "remote_n_end": n_end,
            "local_n_dirs": local_n, "local_missing_sql": local_missing_sql,
        })
        print(f"[{cell_mode}] remote_dir={d} exists={exists} "
              f"remote_n_dirs={n_dirs} remote_n_sql={n_sql} remote_n_end={n_end} "
              f"local_n_dirs={local_n} local_missing_sql={local_missing_sql}")

    inv_df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    inv_df.to_csv(OUT, index=False)
    print(f"wrote {OUT}")

    # ── C15 verdict ─────────────────────────────────────────────────────
    total_remote_sql = sum(int(r["remote_n_sql"]) for r in rows)
    total_remote_end = sum(int(r["remote_n_end"]) for r in rows)
    total_local_missing = sum(r["local_missing_sql"] for r in rows)
    print(f"\nTOTAL remote .sql={total_remote_sql} .end={total_remote_end} "
          f"across the two buckets; local shortfall restated: 874/875 "
          f"(this task's own local recount of the same two buckets: "
          f"{total_local_missing} directories missing eplusout.sql)")
    if total_remote_sql >= total_local_missing and total_remote_end >= total_local_missing:
        verdict = ("the remote files exist -> this is a harvest defect "
                    f"({total_remote_sql} .sql + {total_remote_end} .end present on Speed "
                    f"for {total_local_missing} locally-missing directories)")
    else:
        verdict = ("the remote files are absent -> this is a simulation-side loss "
                    f"(only {total_remote_sql} .sql / {total_remote_end} .end on Speed "
                    f"against {total_local_missing} locally-missing directories)")
    print(f"\nC15 VERDICT: {verdict}")

    # ── fetch 20 samples, 10 per bucket ────────────────────────────────
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    parse_rows = []
    n_fetched = 0
    for cell_mode in CELL_MODES:
        d = remote_out_dir(cell_mode)
        listing = _ssh(f"ls -1 {d} | head -10", timeout=30).strip()
        stems = [s for s in listing.splitlines() if s]
        for stem in stems:
            local_dst = SAMPLE_DIR / cell_mode / stem
            local_dst.mkdir(parents=True, exist_ok=True)
            remote_src = f"{d}/{stem}"
            ok_sql = True
            for fname in ("eplusout.sql", "eplusout.end"):
                r = subprocess.run(
                    ["scp", "-q", f"{REMOTE_HOST}:{remote_src}/{fname}", str(local_dst / fname)],
                    capture_output=True, text=True, timeout=60,
                )
                if r.returncode != 0:
                    ok_sql = False
                    print(f"  scp FAILED {cell_mode}/{stem}/{fname}: {r.stderr.strip()[:300]}")
            eio_src = LOCAL_HARVEST / cell_mode / stem / "eplusout.eio"
            if eio_src.exists():
                shutil.copy(eio_src, local_dst / "eplusout.eio")
            if ok_sql and (local_dst / "eplusout.sql").exists():
                n_fetched += 1
            parse_rows.append({"cell_mode": cell_mode, "stem": stem, "dir": str(local_dst),
                                "scp_ok": ok_sql})

    print(f"\nfetched {n_fetched} of {len(parse_rows)} samples (20 requested)")

    # ── C16: parse_building() on each fetched sample ──────────────────
    parse_results = []
    n_ok = 0
    for pr in parse_rows:
        local_dst = Path(pr["dir"])
        sql_path = local_dst / "eplusout.sql"
        manifest_row = pd.Series({
            "osm_id": pr["stem"],
            "num_zones": 1,
            "data_quality_flag": "",
            "resolution_mode": "auto",
            "levels": 1,
            "height_m": float("nan"),
            "footprint_area_m2": 100.0,
        })
        try:
            metrics = parse_building(sql_path if sql_path.exists() else None, None, manifest_row)
            eui = metrics.get("total_eui_kwh_m2")
            status = metrics.get("parse_status")
            err = metrics.get("error_summary", "")
            ok = eui is not None and status == "success"
        except Exception as exc:
            eui, status, err, ok = None, "exception", str(exc)[:300], False
        if ok:
            n_ok += 1
        parse_results.append({
            "cell_mode": pr["cell_mode"], "stem": pr["stem"],
            "total_eui_kwh_m2": eui, "parse_status": status, "error_summary": err,
        })
        print(f"  parse [{pr['cell_mode']}/{pr['stem']}] "
              f"total_eui_kwh_m2={eui} parse_status={status} err={err[:120]}")

    parse_df = pd.DataFrame(parse_results)
    parse_out = OUT.parent / "open53_remote_inventory_2026-08-20_parse.csv"
    parse_df.to_csv(parse_out, index=False)
    print(f"wrote {parse_out}")
    print(f"\nC16: {n_ok} of {len(parse_results)} parsed with non-null total_eui_kwh_m2")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
