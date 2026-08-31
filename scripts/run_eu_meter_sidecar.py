"""`EU-05` meter sidecar -- off-path re-run of the promoted 95 (`S3`).

Authority: `EXECUTOR_PROMPT_EU-05_meter_sidecar_2026-08-27.md`, owner authorisation
2026-08-27 ("vas-y je te donne le permission").

Copies each of the 95 accepted, promoted `S3` IDFs verbatim (SHA-256 checked
against the promoted manifest before the copy is made), adds `Output:Meter` /
`Output:Table:SummaryReports` objects only, and re-runs EnergyPlus in a
separate directory tree. Nothing under
`openubem/outputs/eu_evidence/EU-04/s3/` is read for anything but comparison,
and nothing there is written.

Usage:
    .venv/Scripts/python.exe scripts/run_eu_meter_sidecar.py --limit 3
    .venv/Scripts/python.exe scripts/run_eu_meter_sidecar.py
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

from openubem.acquisition.european_weather import sha256_file
from scripts.run_eu_s2_campaign import ENERGYPLUS_J_TO_KWH, run_energyplus_for_building
from scripts.run_eu_s3_campaign import verify_weather

ROOT = Path(__file__).resolve().parents[1]
S3_DIR = ROOT / "openubem/outputs/eu_evidence/EU-04/s3"
PROMOTED_MANIFEST_PATH = S3_DIR / "s3_campaign_manifest.csv"
PROMOTED_RUN_ROOT = S3_DIR / "s3_campaign"

SIDECAR_DIR = ROOT / "openubem/outputs/eu_evidence/EU-05/meter_sidecar"
SIDECAR_RUN_ROOT = SIDECAR_DIR / "runs"
SIDECAR_MANIFEST_PATH = SIDECAR_DIR / "meter_sidecar_manifest.csv"
SIDECAR_SUMMARY_PATH = SIDECAR_DIR / "meter_sidecar_summary.json"

METER_NAMES = [
    "Electricity:Facility",
    "DistrictHeating:Facility",
    "Heating:DistrictHeating",
    "InteriorEquipment:Electricity",
    "Electricity:Building",
]

MANIFEST_COLUMNS = [
    "building_id", "site", "layout_mode", "weather_fold",
    "promoted_idf_sha256", "sidecar_idf_sha256",
    "eplus_return_code", "severe_errors", "fatal_errors",
    "rows_compared", "max_abs_diff", "max_rel_diff", "identical",
    "heating_kwh_promoted", "heating_kwh_meter",
    "interior_equipment_electricity_kwh", "total_site_energy_kwh",
    "floor_area_m2", "run_seconds",
]


def load_accepted_rows() -> list[dict[str, str]]:
    with PROMOTED_MANIFEST_PATH.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return [row for row in rows if row["eplus_return_code"] == "0"]


def build_sidecar_idf(promoted_idf_path: Path, sidecar_idf_path: Path, expected_sha256: str) -> str:
    text = promoted_idf_path.read_text(encoding="utf-8")
    actual_sha256 = sha256_file(promoted_idf_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"promoted IDF SHA-256 mismatch for {promoted_idf_path}: "
            f"manifest={expected_sha256} recomputed={actual_sha256}"
        )

    additions = []
    for meter_name in METER_NAMES:
        additions.append(
            "\nOUTPUT:METER,\n"
            f"    {meter_name},               !- Name\n"
            "    Annual;                   !- Reporting Frequency\n"
        )
    additions.append(
        "\nOUTPUT:TABLE:SUMMARYREPORTS,\n"
        "    AllSummary;                !- Report 1 Name\n"
    )
    if "OUTPUTCONTROL:TABLE:STYLE" not in text.upper():
        additions.append(
            "\nOUTPUTCONTROL:TABLE:STYLE,\n"
            "    CommaAndHTML,             !- Column Separator\n"
            "    JtoKWH;                   !- Unit Conversion\n"
        )

    new_text = text.rstrip("\n") + "\n" + "\n".join(additions) + "\n"
    sidecar_idf_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_idf_path.write_text(new_text, encoding="utf-8")
    return sha256_file(sidecar_idf_path)


def _read_heating_hourly(csv_path: Path) -> tuple[list[str], dict[str, list[float]]]:
    # EnergyPlus's own CSV writer is inconsistent about a trailing space/CR on
    # the last header field between runs of the same model; the *content* of
    # the header (its stripped text) is what identifies the column, not its
    # exact byte form, so matching is done on the stripped name.
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        raw_fieldnames = reader.fieldnames or []
        columns = [
            field.strip() for field in raw_fieldnames
            if "zone ideal loads zone total heating energy" in field.casefold()
            and "[j]" in field.casefold() and "(hourly)" in field.casefold()
        ]
        raw_by_stripped = {
            field.strip(): field for field in raw_fieldnames if field.strip() in columns
        }
        data: dict[str, list[float]] = {column: [] for column in columns}
        for row in reader:
            for column in columns:
                data[column].append(float(row[raw_by_stripped[column]]))
    return columns, data


def compare_heating_series(promoted_csv: Path, sidecar_csv: Path) -> dict[str, object]:
    promoted_columns, promoted_data = _read_heating_hourly(promoted_csv)
    sidecar_columns, sidecar_data = _read_heating_hourly(sidecar_csv)

    if set(promoted_columns) != set(sidecar_columns):
        return {
            "rows_compared": 0, "max_abs_diff": None, "max_rel_diff": None,
            "identical": False,
            "note": "column set mismatch",
        }

    rows_compared = 0
    max_abs_diff = 0.0
    max_rel_diff = 0.0
    identical = True
    for column in promoted_columns:
        promoted_series = promoted_data[column]
        sidecar_series = sidecar_data[column]
        if len(promoted_series) != len(sidecar_series):
            identical = False
            continue
        for a, b in zip(promoted_series, sidecar_series):
            rows_compared += 1
            abs_diff = abs(a - b)
            rel_diff = abs_diff / abs(a) if abs(a) > 0 else (0.0 if abs_diff == 0.0 else float("inf"))
            max_abs_diff = max(max_abs_diff, abs_diff)
            max_rel_diff = max(max_rel_diff, rel_diff)
            if rel_diff > 1e-9 and abs_diff > 1e-9:
                identical = False

    return {
        "rows_compared": rows_compared,
        "max_abs_diff": max_abs_diff,
        "max_rel_diff": max_rel_diff,
        "identical": identical,
    }


def read_end_uses(sql_path: Path) -> dict[str, float | None]:
    # With OutputControl:Table:Style set to JtoKWH, EnergyPlus's own tabular
    # writer reports AnnualBuildingUtilityPerformanceSummary values already in
    # kWh (verified against the promoted heating_kwh figure for building
    # relation/12582232: table 'Heating'/'District Heating' = 109578.79,
    # manifest heating_kwh = 109578.787357). No further unit conversion is
    # applied; ColumnName carries no unit suffix under this table style.
    result = {
        "heating_kwh_meter": None,
        "interior_equipment_electricity_kwh": None,
        "total_site_energy_kwh": None,
    }
    if not sql_path.is_file():
        return result
    conn = sqlite3.connect(str(sql_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT RowName, ColumnName, Value FROM TabularDataWithStrings "
            "WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND TableName='End Uses'"
        )
        end_uses_rows = cur.fetchall()
        heating_kwh = 0.0
        interior_electricity_kwh = 0.0
        for row_name, column_name, value in end_uses_rows:
            try:
                value_f = float(value)
            except (TypeError, ValueError):
                continue
            if row_name.strip().lower() == "heating" and column_name.strip().lower() == "district heating":
                heating_kwh += value_f
            if row_name.strip().lower() == "interior equipment" and column_name.strip().lower() == "electricity":
                interior_electricity_kwh += value_f
        if end_uses_rows:
            result["heating_kwh_meter"] = heating_kwh
            result["interior_equipment_electricity_kwh"] = interior_electricity_kwh

        cur.execute(
            "SELECT RowName, ColumnName, Value FROM TabularDataWithStrings "
            "WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND TableName='Site and Source Energy' "
            "AND RowName='Total Site Energy'"
        )
        site_rows = cur.fetchall()
        for row_name, column_name, value in site_rows:
            if column_name.strip().lower() == "total energy":
                try:
                    result["total_site_energy_kwh"] = float(value)
                except (TypeError, ValueError):
                    pass
    finally:
        conn.close()
    return result


def meters_present_in_sql(sql_path: Path) -> set[str]:
    if not sql_path.is_file():
        return set()
    conn = sqlite3.connect(str(sql_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT VariableName FROM ReportMeterDataDictionary")
        return {row[0] for row in cur.fetchall()}
    except sqlite3.OperationalError:
        return set()
    finally:
        conn.close()


def run_sidecar(limit: int | None = None, building_ids: list[str] | None = None) -> tuple[list[dict[str, object]], set[str]]:
    accepted = load_accepted_rows()
    if building_ids is not None:
        wanted = set(building_ids)
        accepted = [row for row in accepted if row["building_id"] in wanted]
    elif limit is not None:
        accepted = accepted[:limit]

    weather_cache: dict[str, Path] = {}
    results: list[dict[str, object]] = []
    meters_seen: set[str] = set()

    for row in accepted:
        building_id = row["building_id"]
        site = row["neighbourhood_id"]
        run_slug = row["run_slug"]
        layout_mode = row["layout_mode"]
        fold = row["weather_fold"]

        if fold not in weather_cache:
            epw_path, _ = verify_weather(fold)
            weather_cache[fold] = epw_path
        epw_path = weather_cache[fold]

        promoted_run_dir = PROMOTED_RUN_ROOT / site / run_slug
        promoted_idf_path = promoted_run_dir / f"{run_slug}.idf"
        promoted_csv_path = promoted_run_dir / "eplusout.csv"

        sidecar_run_dir = SIDECAR_RUN_ROOT / site / run_slug
        sidecar_idf_path = sidecar_run_dir / f"{run_slug}.idf"

        sidecar_sha256 = build_sidecar_idf(promoted_idf_path, sidecar_idf_path, row["idf_sha256"])

        eplus_result = run_energyplus_for_building(sidecar_idf_path, sidecar_run_dir, epw_path=epw_path)

        sidecar_csv_path = sidecar_run_dir / "eplusout.csv"
        sidecar_sql_path = sidecar_run_dir / "eplusout.sql"

        if eplus_result["completed"] and sidecar_csv_path.is_file() and promoted_csv_path.is_file():
            comparison = compare_heating_series(promoted_csv_path, sidecar_csv_path)
        else:
            comparison = {"rows_compared": 0, "max_abs_diff": None, "max_rel_diff": None, "identical": False}

        end_uses = read_end_uses(sidecar_sql_path) if eplus_result["completed"] else {
            "heating_kwh_meter": None, "interior_equipment_electricity_kwh": None, "total_site_energy_kwh": None,
        }

        meters_seen |= meters_present_in_sql(sidecar_sql_path)

        results.append({
            "building_id": building_id,
            "site": site,
            "layout_mode": layout_mode,
            "weather_fold": fold,
            "promoted_idf_sha256": row["idf_sha256"],
            "sidecar_idf_sha256": sidecar_sha256,
            "eplus_return_code": eplus_result["eplus_return_code"],
            "severe_errors": eplus_result["severe_errors"],
            "fatal_errors": eplus_result["fatal_errors"],
            "rows_compared": comparison["rows_compared"],
            "max_abs_diff": comparison["max_abs_diff"],
            "max_rel_diff": comparison["max_rel_diff"],
            "identical": comparison["identical"],
            "heating_kwh_promoted": float(row["heating_kwh"]) if row.get("heating_kwh") else None,
            "heating_kwh_meter": end_uses["heating_kwh_meter"],
            "interior_equipment_electricity_kwh": end_uses["interior_equipment_electricity_kwh"],
            "total_site_energy_kwh": end_uses["total_site_energy_kwh"],
            "floor_area_m2": float(row["floor_area_m2"]) if row.get("floor_area_m2") else None,
            "run_seconds": eplus_result["run_seconds"],
        })

    return results, meters_seen


def write_manifest(results: list[dict[str, object]]) -> None:
    SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    with SIDECAR_MANIFEST_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


def _pooled_intensity(results: list[dict[str, object]], key: str) -> dict[str, object]:
    numerator = 0.0
    denominator = 0.0
    n = 0
    for row in results:
        value = row.get(key)
        area = row.get("floor_area_m2")
        if value is None or area is None:
            continue
        numerator += float(value)
        denominator += float(area)
        n += 1
    intensity = numerator / denominator if denominator else None
    return {"n": n, "total_energy_kwh": numerator, "total_floor_area_m2": denominator, "kwh_per_m2": intensity}


def build_summary(results: list[dict[str, object]], meters_seen: set[str]) -> dict[str, object]:
    n_accepted = len(results)
    n_identical = sum(1 for row in results if row["identical"])
    n_meters_present = sum(1 for name in METER_NAMES if name in meters_seen)

    pooled_heating = _pooled_intensity(results, "heating_kwh_meter")
    pooled_total = _pooled_intensity(results, "total_site_energy_kwh")
    ratio = None
    if pooled_heating["kwh_per_m2"] and pooled_total["kwh_per_m2"]:
        ratio = pooled_total["kwh_per_m2"] / pooled_heating["kwh_per_m2"]

    by_layout_mode: dict[str, object] = {}
    for mode in sorted({row["layout_mode"] for row in results}):
        subset = [row for row in results if row["layout_mode"] == mode]
        by_layout_mode[mode] = {
            "heating_only": _pooled_intensity(subset, "heating_kwh_meter"),
            "total_site": _pooled_intensity(subset, "total_site_energy_kwh"),
        }

    promoted_manifest_sha256_recorded = None
    promoted_artefacts_unchanged: dict[str, object] = {}
    named_idfs = []
    if results:
        named_idfs = [results[0], results[len(results) // 2], results[-1]]

    return {
        "n_accepted": n_accepted,
        "n_identical": n_identical,
        "n_meters_present": n_meters_present,
        "meters_present": sorted(name for name in METER_NAMES if name in meters_seen),
        "meters_absent": sorted(name for name in METER_NAMES if name not in meters_seen),
        "pooled_heating_only_intensity_kwh_m2": pooled_heating,
        "pooled_total_site_intensity_kwh_m2": pooled_total,
        "total_to_heating_ratio": ratio,
        "by_layout_mode": by_layout_mode,
        "promoted_artefacts_unchanged": promoted_artefacts_unchanged,
        "_named_sample_for_promoted_artefacts_check": [row["building_id"] for row in named_idfs],
    }


def verify_promoted_unchanged(results: list[dict[str, object]]) -> dict[str, object]:
    manifest_sha256 = sha256_file(PROMOTED_MANIFEST_PATH)
    accepted = load_accepted_rows()
    named_rows = []
    if accepted:
        named_rows = [accepted[0], accepted[len(accepted) // 2], accepted[-1]]

    idf_checks = {}
    all_ok = True
    for row in named_rows:
        idf_path = PROMOTED_RUN_ROOT / row["neighbourhood_id"] / row["run_slug"] / f"{row['run_slug']}.idf"
        recomputed = sha256_file(idf_path)
        matches = recomputed == row["idf_sha256"]
        all_ok = all_ok and matches
        idf_checks[row["building_id"]] = {
            "recorded": row["idf_sha256"], "recomputed": recomputed, "matches": matches,
        }

    n_unchanged = 0
    for row in load_accepted_rows():
        idf_path = PROMOTED_RUN_ROOT / row["neighbourhood_id"] / row["run_slug"] / f"{row['run_slug']}.idf"
        if sha256_file(idf_path) == row["idf_sha256"]:
            n_unchanged += 1

    return {
        "manifest_sha256_recomputed": manifest_sha256,
        "named_idf_checks": idf_checks,
        "all_named_idf_unchanged": all_ok,
        "n_promoted_idf_unchanged": n_unchanged,
        "n_promoted_idf_total": len(load_accepted_rows()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--building-ids", type=str, default=None)
    args = parser.parse_args()

    building_ids = args.building_ids.split(",") if args.building_ids else None
    results, meters_seen = run_sidecar(limit=args.limit, building_ids=building_ids)
    write_manifest(results)
    summary = build_summary(results, meters_seen)
    promoted_check = verify_promoted_unchanged(results)
    summary["promoted_artefacts_unchanged"] = promoted_check

    SIDECAR_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
