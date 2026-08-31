"""Read-back audit of the EU-06 `f=0` schedule-file contract over the accepted `S3` IDFs.

Authority: EU-06 is *"f=0 schedule-file path locally tested; f>0 blocked on chaining
rule"*.  `f>0` is BLOCKED upstream (open decision 14, the chaining rule) and assigned
to GSSCanada -- out of scope here.  This script closes the `f=0` half by READ-BACK on
the already-saved `S3` IDFs promoted 2026-08-28 by ruling `D-EU-24` at 95 of 96.  No
EnergyPlus runs, no network, no simulation -- text parsing of saved IDFs only.

Contract asserted by ``tests/test_eu_external_schedules.py`` (all field values below
are quoted from there, not invented):
  * the emitter never creates a ``People`` object -- test line 76.
  * the internal gain is a single ``OtherEquipment`` object -- test line 68/72.
  * ``Interpolate_to_Timestep == "No"`` -- test line 69.
  * ``Schedule_Type_Limits_Name != "Fractional"`` (an "Any Number" schedule) -- test
    line 70.
  * ``gain["Schedule_Name"] == schedule["Name"]`` -- test line 71 (unique wiring).
The saved-IDF field values for ``Column_Number``, ``Rows_to_Skip_at_Top`` and
``Number_of_Hours_of_Data`` are taken from the emitter itself
(``openubem/semantic/european_schedules.py:119-124``): ``Column_Number=1``,
``Rows_to_Skip_at_Top=0``, ``Number_of_Hours_of_Data=8760``.

Usage:  .venv/Scripts/python.exe scripts/audit_eu06_s3_schedules.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv"
CAMPAIGN_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-04/s3/s3_campaign"
OUT_DIR = ROOT / "openubem/outputs/eu_evidence/EU-06"
OUT_CSV = OUT_DIR / "s3_schedule_acceptance.csv"
OUT_SUMMARY = OUT_DIR / "s3_schedule_acceptance_summary.json"

GAIN_PREFIX = "EU_Step8_GainSchedule_"

FIELD_NAMES = {
    "SCHEDULE:FILE": [
        "Name",
        "Schedule_Type_Limits_Name",
        "File_Name",
        "Column_Number",
        "Rows_to_Skip_at_Top",
        "Number_of_Hours_of_Data",
        "Column_Separator",
        "Interpolate_to_Timestep",
        "Minutes_per_Item",
        "Adjust_Schedule_for_Daylight_Savings",
    ],
    "OTHEREQUIPMENT": [
        "Name",
        "Fuel_Type",
        "Zone_or_ZoneList_or_Space_or_SpaceList_Name",
        "Schedule_Name",
        "Design_Level_Calculation_Method",
        "Design_Level",
        "Power_per_Zone_Floor_Area",
        "Power_per_Person",
        "Fraction_Latent",
        "Fraction_Radiant",
        "Fraction_Lost",
        "Carbon_Dioxide_Generation_Rate",
        "EndUse_Subcategory",
    ],
    "PEOPLE": [
        "Name",
        "Zone_or_ZoneList_or_Space_or_SpaceList_Name",
        "Number_of_People_Schedule_Name",
    ],
}


def parse_idf_objects(text: str) -> list[tuple[str, list[str]]]:
    """Return (object_type, fields) tuples for an IDF text body.

    IDF text format: one field per line, comments start at ``!``, an object is
    terminated by a field ending in ``;``.  This mirrors the plain-text layout
    written by ``openubem/semantic/european_schedules.py`` -- no eppy/IDD needed.
    """
    stripped_lines = []
    for line in text.splitlines():
        comment_at = line.find("!")
        clean = line[:comment_at] if comment_at != -1 else line
        clean = clean.strip()
        if clean:
            stripped_lines.append(clean)
    joined = " ".join(stripped_lines)
    raw_objects = [chunk.strip() for chunk in joined.split(";") if chunk.strip()]
    objects: list[tuple[str, list[str]]] = []
    for raw in raw_objects:
        parts = [p.strip() for p in raw.split(",")]
        if not parts:
            continue
        obj_type = parts[0].upper()
        fields = parts[1:]
        objects.append((obj_type, fields))
    return objects


def fields_to_dict(obj_type: str, fields: list[str]) -> dict[str, str]:
    names = FIELD_NAMES.get(obj_type, [])
    result: dict[str, str] = {}
    for i, value in enumerate(fields):
        key = names[i] if i < len(names) else f"field_{i}"
        result[key] = value
    return result


def audit_building(idf_path: Path) -> dict[str, object]:
    text = idf_path.read_text(encoding="latin-1")
    objects = parse_idf_objects(text)

    schedule_files = [
        fields_to_dict("SCHEDULE:FILE", f) for t, f in objects if t == "SCHEDULE:FILE"
    ]
    schedule_compacts = [
        fields_to_dict("SCHEDULE:COMPACT", f) for t, f in objects if t == "SCHEDULE:COMPACT"
    ]
    other_equipment = [
        fields_to_dict("OTHEREQUIPMENT", f) for t, f in objects if t == "OTHEREQUIPMENT"
    ]
    people = [fields_to_dict("PEOPLE", f) for t, f in objects if t == "PEOPLE"]

    eu_schedules = [s for s in schedule_files if s.get("Name", "").startswith(GAIN_PREFIX)]
    eu_compacts = [s for s in schedule_compacts if s.get("Name", "").startswith(GAIN_PREFIX)]

    schedule_file_used = len(eu_schedules) > 0 and len(eu_compacts) == 0

    interpolate_no = bool(eu_schedules) and all(
        s.get("Interpolate_to_Timestep") == "No" for s in eu_schedules
    )

    hours_8760 = bool(eu_schedules) and all(
        s.get("Number_of_Hours_of_Data") == "8760"
        and s.get("Rows_to_Skip_at_Top") == "0"
        and s.get("Column_Number") == "1"
        for s in eu_schedules
    )

    csv_paths: list[Path] = []
    csv_row_counts_ok = True
    for s in eu_schedules:
        file_name = s.get("File_Name", "")
        if not file_name:
            csv_row_counts_ok = False
            continue
        p = Path(file_name)
        csv_paths.append(p)
        if not p.exists():
            csv_row_counts_ok = False
            continue
        try:
            row_count = sum(1 for _ in p.open("r", encoding="latin-1"))
        except OSError:
            csv_row_counts_ok = False
            continue
        if row_count != 8760:
            csv_row_counts_ok = False
    csv_exists_and_reads = bool(eu_schedules) and csv_row_counts_ok

    eu_gains = [
        o for o in other_equipment if o.get("Schedule_Name", "").startswith(GAIN_PREFIX)
    ]
    zones_seen: dict[str, int] = {}
    for g in eu_gains:
        zone = g.get("Zone_or_ZoneList_or_Space_or_SpaceList_Name", "")
        zones_seen[zone] = zones_seen.get(zone, 0) + 1
    no_duplicate_zone = all(count == 1 for count in zones_seen.values())

    schedule_names = {s.get("Name") for s in eu_schedules}
    gain_schedule_refs = {g.get("Schedule_Name") for g in eu_gains}
    unique_wiring = schedule_names == gain_schedule_refs and len(eu_schedules) == len(eu_gains)

    eu_people = [
        p
        for p in people
        if p.get("Number_of_People_Schedule_Name", "").startswith(GAIN_PREFIX)
    ]
    no_people_object = len(eu_people) == 0

    people_assignment_unique = no_duplicate_zone and unique_wiring and no_people_object

    return {
        "schedule_file_used": schedule_file_used,
        "interpolate_no": interpolate_no,
        "hours_8760": hours_8760,
        "csv_exists_and_reads": csv_exists_and_reads,
        "people_assignment_unique": people_assignment_unique,
        "n_eu_schedules": len(eu_schedules),
        "n_eu_gains": len(eu_gains),
        "n_eu_people": len(eu_people),
        "csv_paths": [str(p) for p in csv_paths],
    }


def main() -> None:
    manifest = pd.read_csv(MANIFEST)
    accepted = manifest[manifest["eplus_return_code"] == 0].copy()

    rows = []
    all_csv_paths: set[str] = set()
    for _, row in accepted.iterrows():
        idf_path = CAMPAIGN_ROOT / row["neighbourhood_id"] / row["run_slug"] / f"{row['run_slug']}.idf"
        if not idf_path.exists():
            rows.append(
                {
                    "building_id": row["building_id"],
                    "run_slug": row["run_slug"],
                    "country_stock_code": row["country_stock_code"],
                    "building_type": row["building_type"],
                    "layout_mode": row["layout_mode"],
                    "zone_count": row["zone_count"],
                    "schedule_file_used": False,
                    "interpolate_no": False,
                    "hours_8760": False,
                    "csv_exists_and_reads": False,
                    "people_assignment_unique": False,
                    "n_eu_schedules": 0,
                    "n_eu_gains": 0,
                    "idf_missing": True,
                }
            )
            continue
        result = audit_building(idf_path)
        all_csv_paths.update(result.pop("csv_paths"))
        rows.append(
            {
                "building_id": row["building_id"],
                "run_slug": row["run_slug"],
                "country_stock_code": row["country_stock_code"],
                "building_type": row["building_type"],
                "layout_mode": row["layout_mode"],
                "zone_count": row["zone_count"],
                "idf_missing": False,
                **result,
            }
        )

    out_df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)

    n = len(out_df)
    check_cols = [
        "schedule_file_used",
        "interpolate_no",
        "hours_8760",
        "csv_exists_and_reads",
        "people_assignment_unique",
    ]
    per_check_pass = {c: int(out_df[c].sum()) for c in check_cols}
    layout_split = out_df["layout_mode"].value_counts().to_dict()
    all_pass = out_df[check_cols].all(axis=1)
    failing_buildings = out_df.loc[~all_pass, "building_id"].tolist()

    summary = {
        "n_accepted_manifest_rows": n,
        "per_check_pass_count_of_95": per_check_pass,
        "layout_mode_split": layout_split,
        "n_all_checks_pass": int(all_pass.sum()),
        "n_distinct_schedule_csv_files_referenced": len(all_csv_paths),
        "failing_building_ids": failing_buildings,
        "f_gt_0_status": "BLOCKED_UPSTREAM_CHAINING_RULE_ASSIGNED_TO_GSSCANADA",
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
