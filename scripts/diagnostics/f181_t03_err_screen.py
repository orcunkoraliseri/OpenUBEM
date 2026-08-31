"""FINDING 181 / T03 -- characterise the instability per archetype (branch B: the hash held).

Diagnostic only. No change under openubem/. Calls run_campaign_cell unmodified.
Writes:
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t03_cells.csv
  docs/docs_ACTIVE/europeanLocations/outputs/f181_t03_per_archetype.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
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

BASE_RUN_ROOT = ROOT / "openubem/outputs/_tmp_f181/t03"
OUT_DIR = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs"
CELLS_CSV = OUT_DIR / "f181_t03_cells.csv"
PER_ARCHETYPE_CSV = OUT_DIR / "f181_t03_per_archetype.csv"

BUILD_REFUSAL_MARKER = "S0 openings require an exterior (b=1) Wall_1 host"

def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


CHAINING_NOTICE_SHA256 = _sha256_file(NOTICE_PATH)

ERR_MARKERS = {
    "marker_psy": "Temperature out of range",
    "marker_inside_hb": "Inside surface heat balance did not converge",
    "marker_calchb": "CalcHeatBalanceInsideSurf",
}

CELLS_FIELDS = [
    "cell_id", "archetype_id", "survey_fold", "sensitivity_f", "class",
    "completed", "completion_status", "return_code", "severe_count", "fatal_count",
    "heating_kwh", "runtime_s", "marker_psy", "marker_inside_hb", "marker_calchb",
    "idf_sha256", "error",
]

PER_ARCHETYPE_FIELDS = [
    "archetype_id", "survey_fold", "attempted", "build_refused", "completed", "clean",
    "n_f_levels_completed", "n_f_levels_clean",
    "marker_psy_n", "marker_inside_hb_n", "marker_calchb_n",
]


def _load_spec_cells() -> list[dict]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["spec_status"] == "FROZEN_PINNED"
    assert spec["n_cells"] == 510
    return spec["cells"]


def _err_markers(run_dir: Path) -> dict[str, bool]:
    err_path = run_dir / "eplusout.err"
    text = ""
    if err_path.exists():
        try:
            text = err_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    return {name: (needle in text) for name, needle in ERR_MARKERS.items()}


def _run_one(cell: dict) -> dict:
    run_dir = BASE_RUN_ROOT / str(cell["cell_id"])
    row = {
        "cell_id": cell["cell_id"], "archetype_id": cell["archetype_id"],
        "survey_fold": cell["survey_fold"], "sensitivity_f": cell["sensitivity_f"],
        "class": None,
        "completed": None, "completion_status": None, "return_code": None,
        "severe_count": None, "fatal_count": None, "heating_kwh": None,
        "runtime_s": None,
        "marker_psy": False, "marker_inside_hb": False, "marker_calchb": False,
        "idf_sha256": None, "error": "",
    }
    started = time.time()
    try:
        manifest = run_campaign_cell(
            cell,
            spec_path=SPEC_PATH, spec_sha256=SPEC_SHA256,
            binding_path=BINDING_PATH, chaining_notice_path=NOTICE_PATH,
            chaining_notice_sha256=CHAINING_NOTICE_SHA256,
            schedules_root=SCHEDULES_ROOT,
            run_root=BASE_RUN_ROOT, dry_run=False,
        )
        row["idf_sha256"] = manifest.get("idf_sha256")
        row["heating_kwh"] = repr(manifest.get("heating_kwh"))
        row["completed"] = manifest.get("completed")
        row["completion_status"] = manifest.get("completion_status")
        row["return_code"] = manifest.get("return_code")
        row["severe_count"] = manifest.get("severe_count")
        row["fatal_count"] = manifest.get("fatal_count")
        row["runtime_s"] = manifest.get("runtime_s")
        row["class"] = "ATTEMPTED"
        markers = _err_markers(run_dir)
        row.update(markers)
    except Exception as exc:
        msg = str(exc)
        row["error"] = f"{type(exc).__name__}: {msg[:300]}"
        row["runtime_s"] = round(time.time() - started, 3)
        if BUILD_REFUSAL_MARKER in msg:
            row["class"] = "BUILD_REFUSED"
        elif run_dir.exists() and (run_dir / "eplusout.err").exists():
            row["class"] = "ATTEMPTED"
            row["completed"] = False
            row["completion_status"] = "EXCEPTION_AFTER_ENERGYPLUS_INVOKED"
            markers = _err_markers(run_dir)
            row.update(markers)
        else:
            row["class"] = "BUILD_REFUSED"
    return row


def _worker_entry(cell: dict) -> dict:
    return _run_one(cell)


def write_cells(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CELLS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CELLS_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_per_archetype(rows: list[dict]) -> None:
    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = (r["archetype_id"], r["survey_fold"])
        by_key.setdefault(key, []).append(r)

    out_rows = []
    for (archetype_id, fold), group in sorted(by_key.items()):
        attempted = [r for r in group if r["class"] == "ATTEMPTED"]
        build_refused = [r for r in group if r["class"] == "BUILD_REFUSED"]
        completed_rows = [r for r in attempted if r["completed"] is True]
        clean_rows = []
        for r in attempted:
            if (
                r["completed"] is True
                and r["severe_count"] == 0
                and r["fatal_count"] == 0
                and not r["marker_psy"] and not r["marker_inside_hb"] and not r["marker_calchb"]
            ):
                clean_rows.append(r)

        f_levels_completed = {r["sensitivity_f"] for r in completed_rows}
        f_levels_clean = {r["sensitivity_f"] for r in clean_rows}

        out_rows.append({
            "archetype_id": archetype_id, "survey_fold": fold,
            "attempted": len(attempted), "build_refused": len(build_refused),
            "completed": len(completed_rows), "clean": len(clean_rows),
            "n_f_levels_completed": len(f_levels_completed),
            "n_f_levels_clean": len(f_levels_clean),
            "marker_psy_n": sum(1 for r in attempted if r["marker_psy"]),
            "marker_inside_hb_n": sum(1 for r in attempted if r["marker_inside_hb"]),
            "marker_calchb_n": sum(1 for r in attempted if r["marker_calchb"]),
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PER_ARCHETYPE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PER_ARCHETYPE_FIELDS)
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)
    return out_rows


def main() -> None:
    cells = _load_spec_cells()
    print(f"loaded {len(cells)} cells", flush=True)

    rows: list[dict] = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=14) as pool:
        for i, row in enumerate(pool.map(_worker_entry, cells), start=1):
            rows.append(row)
            if i % 25 == 0:
                write_cells(rows)
                print(f"  {i}/{len(cells)} done in {time.time() - t0:.1f}s", flush=True)

    write_cells(rows)
    per_archetype_rows = write_per_archetype(rows)

    n_build_refused = sum(1 for r in rows if r["class"] == "BUILD_REFUSED")
    n_attempted = sum(1 for r in rows if r["class"] == "ATTEMPTED")
    print(f"BUILD_REFUSED={n_build_refused} ATTEMPTED={n_attempted}", flush=True)
    print(f"total={len(rows)}", flush=True)
    print(f"per-archetype rows: {len(per_archetype_rows)}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
