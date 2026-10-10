"""FINDING 181 / T01 — is the S0 campaign instability caused by parallelism?

Diagnostic only. No change under openubem/. Calls run_campaign_cell unmodified.
Writes:
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_matrix.csv
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_summary.csv
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t01_selection.csv  (which cells, and why)
"""
from __future__ import annotations

import csv
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.campaign.eu_cell_runner import run_campaign_cell  # noqa: E402

SPEC_PATH = ROOT / "openubem/data/campaign/eu_campaign_cell_spec_v1.1.json"
SPEC_SHA256 = "16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6"
GSS_ROOT = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ")
BINDING_PATH = GSS_ROOT / "Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json"
NOTICE_PATH = GSS_ROOT / "Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md"
SCHEDULES_ROOT = GSS_ROOT / "Step7_docs/outputs_step7/schedules"

BASE_RUN_ROOT = ROOT / "openubem/outputs/_tmp_f181/t01"
OUT_DIR = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs"
MATRIX_CSV = OUT_DIR / "f181_t01_matrix.csv"
SUMMARY_CSV = OUT_DIR / "f181_t01_summary.csv"
SELECTION_CSV = OUT_DIR / "f181_t01_selection.csv"

FOLDS = ("uk", "it", "es")
MODES = ("serial", "thread", "process")
REPLICATES = (1, 2, 3)

ERR_MARKERS = {
    "marker_psy": "PsyPsatFnTemp",
    "marker_inside_hb": "Inside surface heat balance did not converge",
    "marker_calchb": "CalcHeatBalanceInsideSurf",
}

MATRIX_FIELDS = [
    "cell_id", "archetype_id", "survey_fold", "sensitivity_f", "mode", "replicate",
    "idf_sha256", "heating_kwh", "completed", "completion_status", "return_code",
    "severe_count", "fatal_count", "runtime_s",
    "marker_psy", "marker_inside_hb", "marker_calchb",
    "error",
]


def _load_spec_cells() -> list[dict]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["spec_status"] == "FROZEN_PINNED"
    assert spec["n_cells"] == 510
    return spec["cells"]


def _dry_run_builds(cell: dict) -> bool:
    try:
        run_campaign_cell(
            cell,
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
            schedules_root=SCHEDULES_ROOT,
            run_root=BASE_RUN_ROOT / "_dryrun_screen",
            dry_run=True,
        )
        return True
    except Exception:
        return False


def select_12_cells(cells: list[dict]) -> tuple[list[dict], list[dict]]:
    buildable = [c for c in cells if _dry_run_builds(c)]
    buildable_ids = {c["cell_id"] for c in buildable}

    selection_log: list[dict] = []
    selected: list[dict] = []

    for fold in FOLDS:
        fold_cells = [c for c in cells if c["survey_fold"] == fold and c["cell_id"] in buildable_ids]
        seen_f: dict[float, dict] = {}
        for c in fold_cells:
            f = c["sensitivity_f"]
            if f not in seen_f:
                seen_f[f] = c
        f_levels_sorted = sorted(seen_f.keys())
        chosen_f_levels: list[float] = []
        if 0.0 in seen_f:
            chosen_f_levels.append(0.0)
        for f in f_levels_sorted:
            if len(chosen_f_levels) >= 4:
                break
            if f not in chosen_f_levels:
                chosen_f_levels.append(f)

        note = "ok_4_distinct_f_levels" if len(chosen_f_levels) == 4 else (
            f"SHORT_ONLY_{len(chosen_f_levels)}_DISTINCT_F_LEVELS_AVAILABLE"
        )

        for f in chosen_f_levels:
            c = seen_f[f]
            selected.append(c)
            selection_log.append({
                "cell_id": c["cell_id"], "archetype_id": c["archetype_id"],
                "survey_fold": fold, "sensitivity_f": f, "note": note,
            })

    return selected, selection_log


def _err_markers(run_dir: Path) -> dict[str, bool]:
    err_path = run_dir / "eplusout.err"
    text = ""
    if err_path.exists():
        try:
            text = err_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    return {name: (needle in text) for name, needle in ERR_MARKERS.items()}


def _run_one(cell: dict, mode: str, replicate: int) -> dict:
    run_root = BASE_RUN_ROOT / mode / f"rep{replicate}"
    run_root.mkdir(parents=True, exist_ok=True)
    row = {
        "cell_id": cell["cell_id"], "archetype_id": cell["archetype_id"],
        "survey_fold": cell["survey_fold"], "sensitivity_f": cell["sensitivity_f"],
        "mode": mode, "replicate": replicate,
        "idf_sha256": None, "heating_kwh": None, "completed": None,
        "completion_status": None, "return_code": None,
        "severe_count": None, "fatal_count": None, "runtime_s": None,
        "marker_psy": None, "marker_inside_hb": None, "marker_calchb": None,
        "error": "",
    }
    started = time.time()
    try:
        manifest = run_campaign_cell(
            cell,
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
            schedules_root=SCHEDULES_ROOT,
            run_root=run_root, dry_run=False,
        )
        row["idf_sha256"] = manifest.get("idf_sha256")
        row["heating_kwh"] = repr(manifest.get("heating_kwh"))
        row["completed"] = manifest.get("completed")
        row["completion_status"] = manifest.get("completion_status")
        row["return_code"] = manifest.get("return_code")
        row["severe_count"] = manifest.get("severe_count")
        row["fatal_count"] = manifest.get("fatal_count")
        row["runtime_s"] = manifest.get("runtime_s")
        run_dir = run_root / str(cell["cell_id"])
        markers = _err_markers(run_dir)
        row.update(markers)
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        row["runtime_s"] = round(time.time() - started, 3)
        run_dir = run_root / str(cell["cell_id"])
        try:
            markers = _err_markers(run_dir)
            row.update(markers)
        except Exception:
            pass
    return row


def _worker_entry(args: tuple[dict, str, int]) -> dict:
    cell, mode, replicate = args
    return _run_one(cell, mode, replicate)


def run_mode(cells: list[dict], mode: str) -> list[dict]:
    tasks = [(cell, mode, rep) for cell in cells for rep in REPLICATES]
    rows: list[dict] = []
    if mode == "serial":
        for cell, m, rep in tasks:
            rows.append(_run_one(cell, m, rep))
    elif mode == "thread":
        with ThreadPoolExecutor(max_workers=14) as pool:
            for row in pool.map(_worker_entry, tasks):
                rows.append(row)
    elif mode == "process":
        with ProcessPoolExecutor(max_workers=14) as pool:
            for row in pool.map(_worker_entry, tasks):
                rows.append(row)
    else:
        raise ValueError(mode)
    return rows


def write_matrix(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_selection(selection_log: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SELECTION_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["cell_id", "archetype_id", "survey_fold", "sensitivity_f", "note"])
        writer.writeheader()
        for row in selection_log:
            writer.writerow(row)


def write_summary(rows: list[dict]) -> None:
    by_mode_cell: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = (r["mode"], r["cell_id"])
        by_mode_cell.setdefault(key, []).append(r)

    summary_rows = []
    for mode in MODES:
        cell_ids = sorted({cid for (m, cid) in by_mode_cell if m == mode})
        n_cells = len(cell_ids)
        hash_identical = 0
        heating_bit_identical = 0
        max_rel_spread = 0.0
        for cid in cell_ids:
            group = by_mode_cell[(mode, cid)]
            hashes = {g["idf_sha256"] for g in group if g["idf_sha256"] is not None}
            if len(hashes) == 1 and len(group) == len([g for g in group if g["idf_sha256"] is not None]):
                hash_identical += 1
            heatings = []
            for g in group:
                if g["heating_kwh"] not in (None, "None"):
                    try:
                        heatings.append(float(g["heating_kwh"]))
                    except Exception:
                        pass
            if len(heatings) == len(group) and len(set(g["heating_kwh"] for g in group)) == 1:
                heating_bit_identical += 1
            if heatings and len(heatings) > 1:
                lo, hi = min(heatings), max(heatings)
                if lo != 0:
                    rel = (hi - lo) / abs(lo)
                    max_rel_spread = max(max_rel_spread, rel)
        summary_rows.append({
            "mode": mode, "n_cells": n_cells,
            "cells_idf_sha256_identical": hash_identical,
            "cells_heating_bit_identical": heating_bit_identical,
            "max_relative_heating_spread": max_rel_spread,
        })

    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "mode", "n_cells", "cells_idf_sha256_identical",
            "cells_heating_bit_identical", "max_relative_heating_spread",
        ])
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)


def main() -> None:
    cells = _load_spec_cells()
    selected, selection_log = select_12_cells(cells)
    write_selection(selection_log)
    print(f"selected {len(selected)} cells", flush=True)
    for c in selected:
        print(f"  {c['cell_id']} fold={c['survey_fold']} f={c['sensitivity_f']}", flush=True)

    all_rows: list[dict] = []
    for mode in MODES:
        t0 = time.time()
        print(f"=== mode {mode} starting ===", flush=True)
        rows = run_mode(selected, mode)
        all_rows.extend(rows)
        write_matrix(all_rows)
        print(f"=== mode {mode} done in {time.time() - t0:.1f}s, {len(rows)} rows ===", flush=True)

    write_matrix(all_rows)
    write_summary(all_rows)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
