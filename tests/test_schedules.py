"""Tests for openubem/semantic/schedules.py — plan T11."""

import pytest

from openubem.semantic.schedules import (
    _FAMILIES,
    build_schedule_library,
    get_schedule_names,
    write_schedules_to_idf,
)


_ALL_ARCHETYPES = [
    "SmallOffice", "MediumOffice", "LargeOffice",
    "RetailStandalone", "RetailStripmall",
    "PrimarySchool", "SecondarySchool",
    "Outpatient", "Hospital",
    "SmallHotel", "LargeHotel",
    "Warehouse",
    "QuickServiceRestaurant", "FullServiceRestaurant",
    "MidriseApartment", "HighriseApartment",
    "SmallOfficeDetailed", "MediumOfficeDetailed", "LargeOfficeDetailed",
    "SuperMarket", "College", "Courthouse", "Laboratory",
    "SmallDataCenterHighITE", "SmallDataCenterLowITE",
    "LargeDataCenterHighITE", "LargeDataCenterLowITE",
    "TallBuilding", "SuperTallBuilding",
    "OpenUBEMUnknown",
]


# ── T11-1: 30 archetypes × 6 families = 180 named schedules ──────────────────

def test_30_archetypes_present():
    from openubem.semantic.schedules import _get_schedule_table
    table = _get_schedule_table()
    assert len(table) == 30, f"Expected 30 archetypes, got {len(table)}"


def test_six_families_per_archetype():
    from openubem.semantic.schedules import _get_schedule_table
    table = _get_schedule_table()
    for arch in table:
        families = set(table[arch].keys())
        assert families == set(_FAMILIES), (
            f"Archetype '{arch}' has families {families}, expected {set(_FAMILIES)}"
        )


def test_180_unique_schedule_names():
    """Each of the 30×6=180 schedule names must be unique."""
    names = []
    for arch in _ALL_ARCHETYPES:
        lib = build_schedule_library(arch)
        for fam in _FAMILIES:
            names.append(lib[fam]["Name"])
    assert len(names) == 180, f"Expected 180 names, got {len(names)}"
    assert len(set(names)) == 180, f"Duplicate schedule names found"


# ── T11-2: 3 day-types present in every entry ────────────────────────────────

_DAY_KEYS = {"For: Weekdays", "For: Saturday", "For: AllOtherDays"}


def test_three_day_types_per_entry():
    from openubem.semantic.schedules import _get_schedule_table
    table = _get_schedule_table()
    for arch, families in table.items():
        for fam, entry in families.items():
            present = {k for k in entry if k.startswith("For:")}
            assert present == _DAY_KEYS, (
                f"{arch}/{fam} has day-types {present}, expected {_DAY_KEYS}"
            )


# ── T11-3: F16 setpoint invariant — setpoint values are numeric ───────────────

def test_f16_setpoint_values_are_numeric():
    """
    F16 invariant: HeatingSetpoint and CoolingSetpoint schedules must contain
    numeric (float) 'Value' fields in each day-type entry.
    """
    from openubem.semantic.schedules import _get_schedule_table
    table = _get_schedule_table()
    for arch, families in table.items():
        for fam in ("HeatingSetpoint", "CoolingSetpoint"):
            entry = families[fam]
            for day_key in _DAY_KEYS:
                day_vals = entry.get(day_key, [])
                for item in day_vals:
                    assert isinstance(item["Value"], (int, float)), (
                        f"{arch}/{fam}/{day_key} has non-numeric value: {item['Value']}"
                    )


def test_f16_heating_below_cooling():
    """
    F16 invariant: In setpoint schedules, heating setpoints must be
    lower than cooling setpoints (no inversion in the stored profiles).
    """
    from openubem.semantic.schedules import _get_schedule_table
    table = _get_schedule_table()
    for arch, families in table.items():
        htg_entry = families["HeatingSetpoint"]
        clg_entry = families["CoolingSetpoint"]
        for day_key in _DAY_KEYS:
            htg_vals = [x["Value"] for x in htg_entry.get(day_key, [])]
            clg_vals = [x["Value"] for x in clg_entry.get(day_key, [])]
            if htg_vals and clg_vals:
                max_htg = max(htg_vals)
                min_clg = min(clg_vals)
                assert max_htg < min_clg, (
                    f"{arch}: max heating ({max_htg}°C) >= min cooling ({min_clg}°C) "
                    f"in {day_key}"
                )


# ── T11-4: OpenUBEMUnknown is a MediumOffice clone ───────────────────────────

def test_unknown_clone_of_medium_office():
    """
    OpenUBEMUnknown schedule profiles must be identical in structure to
    MediumOffice (values may differ by name substitution).
    """
    unk = build_schedule_library("OpenUBEMUnknown")
    med = build_schedule_library("MediumOffice")
    for fam in _FAMILIES:
        unk_entry = unk[fam]
        med_entry = med[fam]
        # Names differ (contain archetype suffix), profiles should be identical
        for day_key in _DAY_KEYS:
            unk_vals = [x["Value"] for x in unk_entry.get(day_key, [])]
            med_vals = [x["Value"] for x in med_entry.get(day_key, [])]
            assert unk_vals == med_vals, (
                f"OpenUBEMUnknown/{fam}/{day_key} values differ from MediumOffice: "
                f"{unk_vals} != {med_vals}"
            )


# ── T11-5: get_schedule_names returns 6 entries ───────────────────────────────

def test_get_schedule_names():
    names = get_schedule_names("MediumOffice")
    assert set(names.keys()) == set(_FAMILIES)
    for fam, name in names.items():
        assert isinstance(name, str) and len(name) > 0


# ── T11-6: missing archetype raises KeyError ─────────────────────────────────

def test_missing_archetype_raises():
    with pytest.raises(KeyError, match="No schedule library entry"):
        build_schedule_library("NonExistentBuilding")


# ── T11-7: write_schedules_to_idf dry-run returns 6 names ────────────────────

def test_write_schedules_dry_run():
    names = write_schedules_to_idf(idf=None, archetype_id="MediumOffice")
    assert len(names) == 6
    for name in names:
        assert "MediumOffice" in name
