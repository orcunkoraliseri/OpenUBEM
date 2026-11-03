"""EU-05 read-back HVAC/ventilation acceptance audit over the accepted `S3` 95.

Authority: ``D-EU-24`` promoted `S3` (95 of 96 `EPLUS_COMPLETED`, one
`EPLUS_FATAL` excluded). EU-05's own status line records S1-S3 and
dwelling/core acceptance as pending; this script closes that by
READ-BACK on the already-saved IDFs. It runs no EnergyPlus, touches no
network, and changes no geometry or builder code -- it only parses what
``scripts/run_eu_s2_campaign.py``/``scripts/run_eu_s3_campaign.py`` already
wrote to disk.

Contract asserted in the test battery (quoted, not invented):

* ``tests/test_eu_heating_controls.py:39-46`` -- the saved IDF carries a
  ``HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM`` whose
  ``Cooling_Availability_Schedule_Name`` points at a ``SCHEDULE:CONSTANT``
  with ``Hourly_Value == 0.0`` (heating-only).
* ``tests/test_eu_hvac_controls.py:50-53`` -- the per-zone ``OTHEREQUIPMENT``
  gains object has ``Fraction_Latent == Fraction_Radiant == Fraction_Lost
  == 0.0`` (all-convective).
* ``openubem/idf/european_controls.py:56-58`` -- ``add_european_heating_controls``
  raises if a zone's ``ZONEVENTILATION:DESIGNFLOWRATE`` name already exists,
  i.e. every per-zone object is namespaced by ``zone_name`` (no duplicate
  object names).

Circulation-core and meter conventions are NOT asserted in the test battery;
this script measures the actual saved-IDF zone-naming and output-request
conventions used by the real campaign builder
(``openubem/geometry/zoning.py:107,122`` -> ``{osm_id}_F{i}_whole``;
``openubem/geometry/european_residential.py:579`` -> ``{id}_F{floor}_dwelling_{index}``;
neither pattern contains ``core``), and reports what it finds without
inventing a contract for either.

Usage: .venv/Scripts/python.exe scripts/audit_eu05_s3_hvac.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from eppy.modeleditor import IDF

from openubem.config import ENERGYPLUS_IDD_PATH

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv"
IDF_ROOT = ROOT / "openubem/outputs/eu_evidence/EU-04/s3/s3_campaign"
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-05"
CSV_PATH = EVIDENCE / "s3_hvac_acceptance.csv"
SUMMARY_PATH = EVIDENCE / "s3_hvac_acceptance_summary.json"

CHECK_COLUMNS = [
    "heating_only",
    "all_convective",
    "core_unconditioned",
    "meters_present",
    "no_duplicate_object_names",
]


def _idf_path(row: pd.Series) -> Path:
    return IDF_ROOT / row["neighbourhood_id"] / row["run_slug"] / f"{row['run_slug']}.idf"


def _check_heating_only(idf: IDF) -> bool:
    if idf.idfobjects["COIL:COOLING:WATER"] or idf.idfobjects.get("COIL:COOLING:DX", []):
        return False
    ideal_systems = idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"]
    if not ideal_systems:
        return False
    for system in ideal_systems:
        schedule_name = system.Cooling_Availability_Schedule_Name
        schedule = idf.getobject("SCHEDULE:CONSTANT", schedule_name)
        if schedule is None or float(schedule.Hourly_Value) != 0.0:
            return False
    return True


def _check_all_convective(idf: IDF) -> bool:
    """Look up the gains object by zone assignment, not by a guessed name.

    ``build_idf_for_building`` (``scripts/run_eu_s2_campaign.py:255-273``)
    creates the ``add_european_heating_controls`` gains object named
    ``EU_InternalGains_{zone_name}`` and then immediately removes it,
    replacing it with ``emit_step8_gain_schedule``'s own object named
    ``EU_Step8_InternalGain_{zone_name}_f{...}``
    (``openubem/semantic/european_schedules.py:111,126-138``). The saved IDF
    therefore never carries the ``EU_InternalGains_`` name; this check
    resolves the live gains object by its ``Zone_or_ZoneList_or_Space_or_SpaceList_Name``
    field instead.
    """
    ideal_systems = idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"]
    if not ideal_systems:
        return False
    for system in ideal_systems:
        gains = [
            obj
            for obj in idf.idfobjects["OTHEREQUIPMENT"]
            if str(obj.Zone_or_ZoneList_or_Space_or_SpaceList_Name) == str(system.Zone_Name)
        ]
        if not gains:
            return False
        for gain in gains:
            if (float(gain.Fraction_Latent), float(gain.Fraction_Radiant), float(gain.Fraction_Lost)) != (0.0, 0.0, 0.0):
                return False
    return True


def _core_zone_names(idf: IDF) -> list[str]:
    return [str(zone.Name) for zone in idf.idfobjects["ZONE"] if "core" in str(zone.Name).casefold()]


def _check_core_unconditioned(idf: IDF, core_zones: list[str]) -> bool:
    if not core_zones:
        return True
    conditioned_zone_names = {
        str(system.Zone_Name) for system in idf.idfobjects["HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM"]
    }
    return not any(name in conditioned_zone_names for name in core_zones)


def _check_meters_present(idf: IDF) -> bool:
    return bool(idf.idfobjects["OUTPUT:METER"]) or bool(idf.idfobjects["OUTPUT:METER:METERFILEONLY"])


def _check_no_duplicate_object_names(idf: IDF) -> bool:
    for object_class in idf.idfobjects:
        names = []
        for obj in idf.idfobjects[object_class]:
            name = getattr(obj, "Name", None)
            if name:
                names.append(str(name))
        if len(names) != len(set(names)):
            return False
    return True


def audit() -> tuple[pd.DataFrame, dict[str, object]]:
    IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    manifest = pd.read_csv(MANIFEST_PATH)
    accepted = manifest.loc[manifest["eplus_return_code"] == 0].copy()

    rows: list[dict[str, object]] = []
    for _, row in accepted.iterrows():
        idf_path = _idf_path(row)
        idf = IDF(str(idf_path))
        core_zones = _core_zone_names(idf)
        rows.append(
            {
                "building_id": row["building_id"],
                "run_slug": row["run_slug"],
                "neighbourhood_id": row["neighbourhood_id"],
                "country_stock_code": row["country_stock_code"],
                "building_type": row["building_type"],
                "layout_mode": row["layout_mode"],
                "zone_count": row["zone_count"],
                "has_core_zone": bool(core_zones),
                "core_zone_names": ";".join(core_zones),
                "heating_only": _check_heating_only(idf),
                "all_convective": _check_all_convective(idf),
                "core_unconditioned": _check_core_unconditioned(idf, core_zones),
                "meters_present": _check_meters_present(idf),
                "no_duplicate_object_names": _check_no_duplicate_object_names(idf),
            }
        )

    frame = pd.DataFrame.from_records(rows)
    total = len(frame)
    summary: dict[str, object] = {
        "evidence_scope": "eu05_s3_hvac_readback_audit_only",
        "manifest": MANIFEST_PATH.as_posix(),
        "accepted_buildings": int(total),
        "check_pass_counts": {
            check: int(frame[check].sum()) for check in CHECK_COLUMNS
        },
        "check_pass_counts_denominator": int(total),
        "buildings_with_core_zone": int(frame["has_core_zone"].sum()),
        "buildings_without_core_zone": int((~frame["has_core_zone"]).sum()),
        "layout_mode_split": {
            str(key): int(value) for key, value in frame["layout_mode"].value_counts().items()
        },
        "layout_mode_split_by_check_failure": {
            check: {
                str(key): int(value)
                for key, value in frame.loc[~frame[check], "layout_mode"].value_counts().items()
            }
            for check in CHECK_COLUMNS
        },
        "interpretation": (
            "core_unconditioned and meters_present are measured against the actual saved-IDF "
            "conventions, not against an EU-05 test-battery assertion -- neither convention is "
            "asserted in tests/test_eu_heating_controls.py or tests/test_eu_hvac_controls.py."
        ),
    }
    return frame, summary


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    frame, summary = audit()
    frame.to_csv(CSV_PATH, index=False)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
