"""T02 (PLAN_ten-live-items-2026-08-20-evening.md) -- OPEN-60 multiplier census.

Scan every run-4 `auto` IDF (<cell>/fleet_staging/idfs/*.idf) for Zone objects
whose Multiplier field is not 1, and ZoneGroup objects whose Zone List
Multiplier field is not 1. Plain-text, stdlib-only positional parse -- no
eppy, no re-implementation of layout_assigner.

Field indices (0-indexed on the fields *after* the object keyword, i.e.
fields[0] == Name), confirmed against inline IDF field comments:
  ZONE       fields[6] == Multiplier
             (Name, Direction of Relative North, X Origin, Y Origin,
              Z Origin, Type, Multiplier, ...)
             evidence: .../austin_centre/fleet_staging/idfs/relation_13781131.idf:379
               "    1,                         !- Multiplier"
  ZONEGROUP  fields[2] == Zone List Multiplier
             (Name, Zone List Name, Zone List Multiplier)
             evidence: docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/
               sources/HighriseApartment_90.1-2013.idf:2670
               "    8;                       !- Zone List Multiplier"
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

RUN4_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
OUT_CSV = Path(
    r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons"
    r"\open60_fleet_multiplier_census_2026-08-20.csv"
)

OBJECT_RE = re.compile(
    r"^\s*(ZONE|ZONEGROUP)\s*,(.*?);",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

ZONE_MULT_IDX = 6
ZONEGROUP_MULT_IDX = 2


def _split_fields(body: str) -> list[str]:
    fields = []
    for raw in body.split(","):
        val = raw.split("!", 1)[0].strip()
        fields.append(val)
    return fields


def scan_idf(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for m in OBJECT_RE.finditer(text):
        obj_type = m.group(1).upper()
        fields = _split_fields(m.group(2))
        if obj_type == "ZONE":
            idx = ZONE_MULT_IDX
            field_name = "Multiplier"
        else:
            idx = ZONEGROUP_MULT_IDX
            field_name = "Zone List Multiplier"
        if idx >= len(fields):
            continue
        raw_val = fields[idx]
        name = fields[0] if fields else ""
        try:
            val = float(raw_val)
        except ValueError:
            continue
        if val != 1:
            rows.append(
                {
                    "file": str(path),
                    "cell": path.parts[path.parts.index("open48_refleet4") + 1]
                    if "open48_refleet4" in path.parts
                    else "",
                    "stem": path.stem,
                    "object_type": obj_type,
                    "object_name": name,
                    "field_name": field_name,
                    "field_index": idx,
                    "value": val,
                }
            )
    return rows


def main():
    idf_files = sorted(RUN4_ROOT.glob("*/fleet_staging/idfs/*.idf"))
    file_count = len(idf_files)
    print(f"C4: idf file count = {file_count} (expected 8160)")
    if file_count != 8160:
        print("C4 FAIL: file count is not 8160 -- stopping before further processing.")
        with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "file",
                    "cell",
                    "stem",
                    "object_type",
                    "object_name",
                    "field_name",
                    "field_index",
                    "value",
                ]
            )
        print(f"C4 FAIL: wrote header-only CSV to {OUT_CSV}")
        return

    all_rows = []
    files_with_offense = set()
    archetypes_with_offense = set()
    for idf_path in idf_files:
        rows = scan_idf(idf_path)
        if rows:
            files_with_offense.add(str(idf_path))
            archetypes_with_offense.add(idf_path.stem)
        all_rows.extend(rows)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "file",
            "cell",
            "stem",
            "object_type",
            "object_name",
            "field_name",
            "field_index",
            "value",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"C5: files scanned = {file_count}")
    print(f"C5: files with any non-1 multiplier object = {len(files_with_offense)}")
    print(f"C5: offending objects (rows) = {len(all_rows)}")
    print(f"C5: distinct archetypes involved = {len(archetypes_with_offense)}")
    if all_rows:
        print("C5 FINDING: non-1 multipliers were found -- OPEN-60's bound is wrong.")
    else:
        print("C5: expected result confirmed -- 0 non-1 multipliers across the census.")
    print(f"Wrote {OUT_CSV}")

    run_c6_positive_control()


def run_c6_positive_control():
    candidate_roots = [
        Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_b05f_work"),
        Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_b08b_work"),
        Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_five_mode"),
        Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet"),
        Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest"),
    ]
    candidates = []
    for root in candidate_roots:
        if not root.exists():
            continue
        for p in root.rglob("*layout_assign*"):
            if p.is_dir():
                candidates.extend(p.rglob("*.idf"))
    if not candidates:
        print(
            "C6: NOT RUN -- no layout_assign IDF found on disk under the "
            "checked roots (ubem_b05f_work, ubem_b08b_work, "
            "ubem_e02_five_mode, ubem_e02_fleet, ubem_e02_harvest); "
            "their step3_layout_assign/idfs directories exist but hold no "
            ".idf files."
        )
        return
    found_multiplier = False
    for p in candidates:
        rows = scan_idf(p)
        if rows:
            found_multiplier = True
            print(f"C6: PASS -- detected {len(rows)} non-1 multiplier object(s) in {p}")
            break
    if not found_multiplier:
        print(
            f"C6: {len(candidates)} layout_assign IDF(s) found but none carried "
            "a non-1 multiplier -- could not confirm the positive control."
        )


if __name__ == "__main__":
    main()
