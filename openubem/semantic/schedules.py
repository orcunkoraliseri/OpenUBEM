"""Module 07: Schedule library loader and IDF Schedule:Compact writer (DESIGN §3F)."""
from __future__ import annotations

import importlib.resources
import json
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_SCHEDULE_TABLE: dict | None = None

_FAMILIES = ("Occupancy", "Lighting", "Equipment", "HeatingSetpoint", "CoolingSetpoint", "Infiltration")
_DAY_KEY_MAP = {
    "For: Weekdays":    "weekdays",
    "For: Saturday":    "saturday",
    "For: AllOtherDays": "other",
}


def _load_schedule_table() -> dict:
    pkg = importlib.resources.files("openubem.data.schedules")
    return json.loads((pkg / "doe_schedules.json").read_text(encoding="utf-8"))


def _get_schedule_table() -> dict:
    global _SCHEDULE_TABLE
    if _SCHEDULE_TABLE is None:
        _SCHEDULE_TABLE = _load_schedule_table()
    return _SCHEDULE_TABLE


def build_schedule_library(
    archetype_id: str,
    custom_table: dict | None = None,
) -> dict[str, Any]:
    """
    Return the 6-family schedule dict for the requested archetype (DESIGN §3F / F13).

    OpenUBEMUnknown → MediumOffice clone is already stored under its own key;
    this function simply returns the stored entry.
    custom_table: optional synthetic dict for tests (same shape as doe_schedules.json).

    Returns a dict keyed by family name, each value a dict with:
        Name, Schedule Type Limits Name, and day-type keys → list[{"Until":…, "Value":…}]
    """
    table = custom_table if custom_table is not None else _get_schedule_table()
    if archetype_id not in table:
        raise KeyError(
            f"No schedule library entry for archetype '{archetype_id}'. "
            f"Available: {sorted(table.keys())}"
        )
    return table[archetype_id]


def _compact_block(sched_entry: dict) -> list[str]:
    """
    Convert one schedule dict entry into EnergyPlus Schedule:Compact field lines.

    Returns a list of field strings (without 'Schedule:Compact,' prefix).
    The EDD format is: Name, Type Limits, [Through: ...], [For: ...], [Until: HH:MM, value], ...
    """
    lines = [
        sched_entry["Name"],
        sched_entry["Schedule Type Limits Name"],
        "Through: 12/31",
    ]
    for idd_key, friendly in _DAY_KEY_MAP.items():
        day_vals = sched_entry.get(idd_key)
        if day_vals is None:
            continue
        lines.append(idd_key)
        for entry in day_vals:
            lines.append(f"Until: {entry['Until']}, {entry['Value']}")
    return lines


def write_schedules_to_idf(
    idf: Any,
    archetype_id: str,
) -> list[str]:
    """
    Write 6 Schedule:Compact objects for the given archetype into an eppy IDF object.

    Returns the list of schedule names that were written (length 6, one per family).
    F16 setpoint invariant: setpoint/setback values are already baked into the JSON
    (built from loads-table scalars in scripts/build_schedules_json.py).

    If idf is None, returns the names without writing (dry-run / test mode).
    """
    lib = build_schedule_library(archetype_id)
    written = []
    for family in _FAMILIES:
        entry = lib[family]
        name = entry["Name"]
        if idf is not None:
            sc = idf.newidfobject("SCHEDULE:COMPACT")
            sc.Name = name
            sc.Schedule_Type_Limits_Name = entry["Schedule Type Limits Name"]
            # Build the field list for the compact schedule body
            fields = _compact_block(entry)
            # eppy uses Field_1 … Field_N for compact body
            for i, field_val in enumerate(fields[2:], start=1):  # skip Name and TypeLimits
                try:
                    setattr(sc, f"Field_{i}", field_val)
                except AttributeError:
                    logger.debug("Schedule compact field_%d skipped: %s", i, field_val)
        written.append(name)
    return written


def get_schedule_names(archetype_id: str) -> dict[str, str]:
    """Return {family: schedule_name} mapping for a given archetype."""
    lib = build_schedule_library(archetype_id)
    return {family: lib[family]["Name"] for family in _FAMILIES}
