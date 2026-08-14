"""OPEN-42 T01 — per-building, per-mode failure cause for the six manifest-empty rows.

Measurement only. Locates the six `Warehouse` buildings named in the plan
(`docs/docs_ACTIVE/openings/implemenation/PLAN_two-measurements-2026-08-13.md`, T01) under the
E02 harvest corpus, checks every mode directory that contains each building stem (not only the
mode the manifest happened to record), and for every `eplusout.err` that carries a fatal, scans
BACKWARDS from the fatal line for the nearest preceding `** Severe **` line using the project's
own whitespace-tolerant helper (`openubem/results/err_parse.py`). No marker literal is
hand-written here — `SEVERE_RE` / `FATAL_RE` are imported directly from that module.

Also runs a non-vacuity control against three of OPEN-41's 44 already-explained fatals (one per
independent cause class) before any of the six buildings' results are trusted.

Writes: openubem/outputs/comparisons/open42_six_failure_causes.csv
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from openubem.results.err_parse import FATAL_RE, SEVERE_RE  # noqa: E402

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")

MODES = ["auto", "building", "fast_zone", "floor", "layout_assign"]

TARGET_BUILDINGS = [
    ("la_rural", "way_472960972"),
    ("la_rural", "way_472961034"),
    ("la_rural", "way_472961088"),
    ("la_rural", "way_472961091"),
    ("la_rural", "way_472961171"),
    ("la_urban", "way_402215469"),
]

CONTROL_CASES = [
    # (cell, mode, stem, expected cause-class substring, source)
    ("la_centre", "auto", "way_319507579", "CheckForRunawayPlantTemps",
     "OPEN-41 register: 1 CheckForRunawayPlantTemps"),
    ("nyc_centre", "auto", "way_266149332", "CalcHeatBalanceInsideSurf",
     "OPEN-41 register: 17 CalcHeatBalanceInsideSurf"),
    ("la_centre", "floor", "way_428015178", "Temperature (low) out of bounds",
     "OPEN-41 register: 25 Temperature (low) out of bounds"),
]

TEMP_BRACKET_RE = re.compile(r"\[(-?\d+\.?\d*)\]")
TEMP_PAREN_RE = re.compile(r"\((-?\d+\.?\d*)\]")
TEMP_OF_RE = re.compile(r"temperature of (-?\d+\.?\d*)\s*C", re.IGNORECASE)


def classify_cause(severe_line: str) -> str:
    if "CalcHeatBalanceInsideSurf" in severe_line:
        return "CalcHeatBalanceInsideSurf"
    if "Temperature (low) out of bounds" in severe_line:
        return "Temperature (low) out of bounds"
    if "Temperature (high) out of bounds" in severe_line:
        return "Temperature (high) out of bounds"
    if "CheckForRunawayPlantTemps" in severe_line or "Plant temperatures are getting far too hot" in severe_line:
        return "CheckForRunawayPlantTemps (plant loop runaway)"
    if severe_line.strip() == "":
        return "NO_SEVERE_FOUND_BEFORE_FATAL"
    return "OTHER: " + severe_line.strip()[:80]


def extract_temperature(severe_line: str) -> str:
    m = TEMP_OF_RE.search(severe_line)
    if m:
        return m.group(1)
    m = TEMP_BRACKET_RE.search(severe_line)
    if m:
        return m.group(1)
    m = TEMP_PAREN_RE.search(severe_line)
    if m:
        return m.group(1)
    return ""


def scan_err_file(err_path: Path):
    """Return a dict describing fatal/severe state for one eplusout.err file."""
    text = err_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    fatal_line_no = None
    fatal_line_text = ""
    for i, line in enumerate(lines):
        if FATAL_RE.match(line):
            fatal_line_no = i + 1
            fatal_line_text = line.strip()
            break

    severe_hits = []
    for i, line in enumerate(lines):
        if SEVERE_RE.match(line):
            severe_hits.append((i + 1, line.strip()))

    has_fatal = fatal_line_no is not None

    result = {
        "has_fatal": has_fatal,
        "fatal_line_no": fatal_line_no,
        "fatal_line_text": fatal_line_text,
        "n_severe_total": len(severe_hits),
        "severe_line_no": None,
        "severe_line_text": "",
        "cause_class": "",
        "temperature": "",
    }

    if not has_fatal:
        return result

    preceding = [h for h in severe_hits if h[0] <= fatal_line_no]
    if preceding:
        line_no, line_text = preceding[-1]
        result["severe_line_no"] = line_no
        result["severe_line_text"] = line_text
        result["cause_class"] = classify_cause(line_text)
        result["temperature"] = extract_temperature(line_text)
    else:
        result["cause_class"] = "NO_SEVERE_FOUND_BEFORE_FATAL"

    return result


def run_control_checks() -> list[str]:
    log = []
    all_pass = True
    for cell, mode, stem, expected_substring, source in CONTROL_CASES:
        err_path = HARVEST_ROOT / f"{cell}_{mode}" / stem / "eplusout.err"
        if not err_path.exists():
            log.append(f"CONTROL MISSING FILE: {err_path}")
            all_pass = False
            continue
        r = scan_err_file(err_path)
        ok = r["has_fatal"] and expected_substring in r["cause_class"]
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        log.append(
            f"CONTROL [{status}] {cell}/{mode}/{stem}: expected '{expected_substring}' "
            f"({source}) -> has_fatal={r['has_fatal']}, cause_class='{r['cause_class']}', "
            f"severe_line_no={r['severe_line_no']}, fatal_line_no={r['fatal_line_no']}"
        )
    log.append(f"CONTROL SUMMARY: {'ALL PASS' if all_pass else 'AT LEAST ONE FAIL'}")
    return log


def main():
    control_log = run_control_checks()
    print("\n".join(control_log))
    print()

    rows = []
    for cell, stem in TARGET_BUILDINGS:
        for mode in MODES:
            mode_dir = HARVEST_ROOT / f"{cell}_{mode}"
            building_dir = mode_dir / stem
            err_path = building_dir / "eplusout.err"
            end_path = building_dir / "eplusout.end"

            row = {
                "cell": cell,
                "stem": stem,
                "mode": mode,
                "mode_dir_exists": mode_dir.exists(),
                "building_dir_exists": building_dir.exists(),
                "err_file_exists": err_path.exists(),
                "end_file_exists": end_path.exists(),
                "end_file_text": "",
                "has_fatal": "",
                "fatal_line_no": "",
                "fatal_line_text": "",
                "n_severe_total": "",
                "severe_line_no": "",
                "severe_line_text": "",
                "cause_class": "",
                "temperature": "",
            }

            if end_path.exists():
                row["end_file_text"] = end_path.read_text(encoding="utf-8", errors="replace").strip()

            if not err_path.exists():
                row["cause_class"] = "NO_ERR_FILE_FOUND"
                rows.append(row)
                continue

            r = scan_err_file(err_path)
            row["has_fatal"] = r["has_fatal"]
            row["fatal_line_no"] = r["fatal_line_no"]
            row["fatal_line_text"] = r["fatal_line_text"]
            row["n_severe_total"] = r["n_severe_total"]
            row["severe_line_no"] = r["severe_line_no"]
            row["severe_line_text"] = r["severe_line_text"]
            row["cause_class"] = r["cause_class"] if r["has_fatal"] else "NO_FATAL_IN_FILE"
            row["temperature"] = r["temperature"]

            rows.append(row)

    out_path = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open42_six_failure_causes.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")

    for cell, stem in TARGET_BUILDINGS:
        print(f"\n--- {cell}/{stem} ---")
        for row in rows:
            if row["cell"] == cell and row["stem"] == stem:
                print(
                    f"  {row['mode']:14s} fatal={row['has_fatal']!s:6s} "
                    f"cause={row['cause_class']}"
                )


if __name__ == "__main__":
    main()
