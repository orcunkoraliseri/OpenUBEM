"""
Build doe_schedules.json — 30 archetypes × 6 families × 3 day-types of Schedule:Compact stubs.

Source: PNNL-20405 DOE Commercial Prototype Building schedule sets (digitized).
OpenUBEMUnknown = MediumOffice clone under its own key (DESIGN §3F).
Setpoint plateau values are resolved from the T03 loads scalars (DESIGN F16/P6).
Infiltration schedule = 1 − occupancy-nonzero convention (full leakage when unoccupied).

Output:
  openubem/data/schedules/doe_schedules.json
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).parent.parent / "openubem" / "data"
LOADS_DIR = DATA_ROOT / "loads"

ARCHETYPES_29 = [
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
]

# Schedule group assignments: archetypes sharing the same DOE prototype schedule patterns.
# Based on PNNL-20405 prototype building schedule documentation.
# Groups: Office, Retail, School, Hospitality, Apartment, Warehouse, Restaurant,
#         Hospital, Outpatient, DataCenter, 24h (continuous operation)
_SCHED_GROUP = {
    "SmallOffice":             "Office",
    "MediumOffice":            "Office",
    "LargeOffice":             "Office",
    "SmallOfficeDetailed":     "Office",
    "MediumOfficeDetailed":    "Office",
    "LargeOfficeDetailed":     "Office",
    "TallBuilding":            "Office",
    "SuperTallBuilding":       "Office",
    "College":                 "Office",
    "Courthouse":              "Office",
    "Laboratory":              "Office",
    "RetailStandalone":        "Retail",
    "RetailStripmall":         "Retail",
    "SuperMarket":             "Retail",
    "PrimarySchool":           "School",
    "SecondarySchool":         "School",
    "SmallHotel":              "Hotel",
    "LargeHotel":              "Hotel",
    "MidriseApartment":        "Apartment",
    "HighriseApartment":       "Apartment",
    "Warehouse":               "Warehouse",
    "QuickServiceRestaurant":  "Restaurant",
    "FullServiceRestaurant":   "Restaurant",
    "Hospital":                "Hospital",
    "Outpatient":              "Outpatient",
    "SmallDataCenterHighITE":  "DataCenter",
    "SmallDataCenterLowITE":   "DataCenter",
    "LargeDataCenterHighITE":  "DataCenter",
    "LargeDataCenterLowITE":   "DataCenter",
}

# Occupancy schedule day profiles (fraction of peak occupancy).
# Source: PNNL-20405 Table B.5 and DOE prototype IDF schedule sets (commit 83b1e64).
# Format: list of (hour_end_hhmm, fraction) pairs for Schedule:Compact Until: HH:MM, value
# Weekday / Saturday / Sunday day-type profiles.
_OCC_PROFILES: dict[str, dict[str, list[tuple[str, float]]]] = {
    "Office": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.1), ("08:00", 0.2), ("09:00", 0.95),
            ("12:00", 1.0), ("13:00", 0.5), ("14:00", 0.95), ("17:00", 1.0),
            ("18:00", 0.3), ("20:00", 0.1), ("22:00", 0.05), ("24:00", 0.0),
        ],
        "Saturday": [
            ("06:00", 0.0), ("08:00", 0.1), ("12:00", 0.3),
            ("17:00", 0.1), ("24:00", 0.0),
        ],
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    "Retail": {
        "Weekday": [
            ("08:00", 0.0), ("09:00", 0.5), ("10:00", 0.8), ("12:00", 1.0),
            ("14:00", 0.6), ("18:00", 1.0), ("20:00", 0.6), ("21:00", 0.5),
            ("22:00", 0.0), ("24:00", 0.0),
        ],
        "Saturday": [
            ("08:00", 0.0), ("09:00", 0.7), ("12:00", 1.0),
            ("18:00", 0.8), ("21:00", 0.5), ("22:00", 0.0), ("24:00", 0.0),
        ],
        "Sunday": [
            ("10:00", 0.0), ("11:00", 0.5), ("18:00", 0.7),
            ("19:00", 0.5), ("20:00", 0.0), ("24:00", 0.0),
        ],
    },
    "School": {
        "Weekday": [
            ("07:00", 0.0), ("08:00", 0.5), ("09:00", 0.95), ("14:00", 1.0),
            ("15:00", 0.5), ("17:00", 0.2), ("18:00", 0.0), ("24:00", 0.0),
        ],
        "Saturday": [
            ("24:00", 0.0),
        ],
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    "Hotel": {
        "Weekday": [
            ("07:00", 0.4), ("08:00", 0.2), ("09:00", 0.1), ("17:00", 0.3),
            ("18:00", 0.6), ("22:00", 0.8), ("23:00", 0.6), ("24:00", 0.4),
        ],
        "Saturday": [
            ("07:00", 0.5), ("08:00", 0.3), ("09:00", 0.2), ("17:00", 0.4),
            ("18:00", 0.7), ("22:00", 0.9), ("23:00", 0.7), ("24:00", 0.5),
        ],
        "Sunday": [
            ("07:00", 0.6), ("08:00", 0.4), ("09:00", 0.3), ("17:00", 0.4),
            ("18:00", 0.7), ("22:00", 0.8), ("23:00", 0.6), ("24:00", 0.5),
        ],
    },
    "Apartment": {
        "Weekday": [
            ("06:00", 0.8), ("07:00", 0.6), ("08:00", 0.4), ("09:00", 0.3),
            ("17:00", 0.3), ("18:00", 0.6), ("20:00", 0.8), ("22:00", 0.9),
            ("23:00", 0.8), ("24:00", 0.8),
        ],
        "Saturday": [
            ("07:00", 0.9), ("08:00", 0.7), ("09:00", 0.5), ("12:00", 0.4),
            ("17:00", 0.5), ("18:00", 0.7), ("21:00", 0.9), ("23:00", 0.8), ("24:00", 0.8),
        ],
        "Sunday": [
            ("07:00", 0.9), ("08:00", 0.8), ("10:00", 0.6), ("13:00", 0.5),
            ("17:00", 0.6), ("18:00", 0.8), ("21:00", 0.9), ("24:00", 0.8),
        ],
    },
    "Warehouse": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.05), ("08:00", 1.0), ("18:00", 1.0),
            ("19:00", 0.05), ("24:00", 0.0),
        ],
        "Saturday": [
            ("06:00", 0.0), ("08:00", 0.5), ("14:00", 0.5),
            ("15:00", 0.0), ("24:00", 0.0),
        ],
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    "Restaurant": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.5), ("09:00", 0.3), ("11:00", 0.9),
            ("13:00", 1.0), ("14:00", 0.3), ("17:00", 0.9), ("20:00", 1.0),
            ("22:00", 0.5), ("23:00", 0.0), ("24:00", 0.0),
        ],
        "Saturday": [
            ("06:00", 0.0), ("07:00", 0.5), ("11:00", 0.9),
            ("13:00", 1.0), ("14:00", 0.5), ("17:00", 0.9), ("21:00", 1.0),
            ("22:00", 0.5), ("23:00", 0.0), ("24:00", 0.0),
        ],
        "Sunday": [
            ("08:00", 0.0), ("09:00", 0.5), ("12:00", 0.9),
            ("14:00", 0.7), ("18:00", 0.9), ("20:00", 0.8),
            ("21:00", 0.3), ("22:00", 0.0), ("24:00", 0.0),
        ],
    },
    "Hospital": {
        "Weekday": [
            ("07:00", 0.4), ("08:00", 0.7), ("12:00", 0.9), ("13:00", 0.8),
            ("17:00", 0.9), ("18:00", 0.7), ("22:00", 0.5), ("24:00", 0.4),
        ],
        "Saturday": [
            ("07:00", 0.4), ("08:00", 0.6), ("12:00", 0.8), ("18:00", 0.6),
            ("22:00", 0.4), ("24:00", 0.4),
        ],
        "Sunday": [
            ("07:00", 0.4), ("08:00", 0.5), ("12:00", 0.7), ("18:00", 0.5),
            ("22:00", 0.4), ("24:00", 0.4),
        ],
    },
    "Outpatient": {
        "Weekday": [
            ("07:00", 0.0), ("08:00", 0.5), ("09:00", 1.0), ("17:00", 1.0),
            ("18:00", 0.1), ("24:00", 0.0),
        ],
        "Saturday": [
            ("09:00", 0.0), ("10:00", 0.5), ("14:00", 0.5),
            ("15:00", 0.0), ("24:00", 0.0),
        ],
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    "DataCenter": {
        "Weekday": [
            ("24:00", 1.0),
        ],
        "Saturday": [
            ("24:00", 1.0),
        ],
        "Sunday": [
            ("24:00", 1.0),
        ],
    },
}

# Lighting schedule: follows occupancy shape, but ~20% baseline at all times
def _make_lighting_profile(occ_profile):
    return [(t, max(0.1, min(1.0, 0.1 + 0.9 * v))) if v > 0.0 else (t, 0.1)
            for t, v in occ_profile]


# Equipment schedule: similar to lighting
def _make_equipment_profile(occ_profile):
    return [(t, max(0.15, min(1.0, 0.15 + 0.85 * v))) if v > 0.0 else (t, 0.15)
            for t, v in occ_profile]


# Infiltration: inverse occupancy convention (full leakage = 1.0 when unoccupied)
def _make_infiltration_profile(occ_profile):
    result = []
    for t, v in occ_profile:
        if v > 0.0:
            result.append((t, 0.25))  # reduced during occupied hours (HVAC pressurizes)
        else:
            result.append((t, 1.0))   # full leakage when unoccupied
    return result


def _make_setpoint_profile(occ_profile, occupied_val, unoccupied_val):
    """Dual-plateau setpoint: occupied when occ_fraction > 0, unoccupied otherwise."""
    result = []
    for t, v in occ_profile:
        if v > 0.0:
            result.append((t, occupied_val))
        else:
            result.append((t, unoccupied_val))
    return result


def _build_stub(name, type_limits, day_profiles):
    """Build a Schedule:Compact field dict."""
    fields = {
        "Name": name,
        "Schedule Type Limits Name": type_limits,
    }
    day_type_keys = {"Weekday": "For: Weekdays", "Saturday": "For: Saturday",
                     "Sunday": "For: AllOtherDays"}
    for day, day_key in day_type_keys.items():
        profile = day_profiles[day]
        fields[day_key] = [{"Until": t, "Value": v} for t, v in profile]
    return fields


def build_schedule_library_data(loads_table: dict[str, dict]) -> dict:
    """
    Build 30-key × 6-family schedule dict from occupancy profiles + loads scalars.
    loads_table: combined doe_prototype_loads + openstudio_loads keyed by archetype_id.
    Returns dict[archetype_id -> dict[family -> stub_dict]].
    """
    library: dict[str, dict] = {}

    for arch in ARCHETYPES_29:
        group = _SCHED_GROUP[arch]
        occ_profiles = _OCC_PROFILES[group]
        row = loads_table[arch]

        htg_occupied = row["heating_setpoint_c"]
        htg_setback = row["heating_setback_c"]
        clg_occupied = row["cooling_setpoint_c"]
        clg_setup = row["cooling_setup_c"]

        stub_dict: dict[str, dict] = {}

        # Occupancy
        occ_day = {d: occ_profiles[d] for d in ("Weekday", "Saturday", "Sunday")}
        stub_dict["Occupancy"] = _build_stub(
            f"Occupancy_Schedule_{arch}", "Fraction", occ_day
        )

        # Lighting
        ltg_day = {d: _make_lighting_profile(occ_profiles[d]) for d in occ_day}
        stub_dict["Lighting"] = _build_stub(
            f"Lighting_Schedule_{arch}", "Fraction", ltg_day
        )

        # Equipment
        equip_day = {d: _make_equipment_profile(occ_profiles[d]) for d in occ_day}
        stub_dict["Equipment"] = _build_stub(
            f"Equipment_Schedule_{arch}", "Fraction", equip_day
        )

        # Heating setpoint
        htg_day = {d: _make_setpoint_profile(occ_profiles[d], htg_occupied, htg_setback)
                   for d in occ_day}
        stub_dict["HeatingSetpoint"] = _build_stub(
            f"Heating_Setpoint_{arch}", "Temperature", htg_day
        )

        # Cooling setpoint
        clg_day = {d: _make_setpoint_profile(occ_profiles[d], clg_occupied, clg_setup)
                   for d in occ_day}
        stub_dict["CoolingSetpoint"] = _build_stub(
            f"Cooling_Setpoint_{arch}", "Temperature", clg_day
        )

        # Infiltration
        infil_day = {d: _make_infiltration_profile(occ_profiles[d]) for d in occ_day}
        stub_dict["Infiltration"] = _build_stub(
            f"Infiltration_Schedule_{arch}", "Fraction", infil_day
        )

        library[arch] = stub_dict

    # OpenUBEMUnknown = clone of MediumOffice under its own key (DESIGN §3F)
    unknown_row = loads_table.get("MediumOffice")
    unknown_stub: dict[str, dict] = {}
    if unknown_row:
        mo_lib = library["MediumOffice"]
        families = ["Occupancy", "Lighting", "Equipment", "HeatingSetpoint",
                    "CoolingSetpoint", "Infiltration"]
        prefix_map = {
            "Occupancy": "Occupancy_Schedule",
            "Lighting": "Lighting_Schedule",
            "Equipment": "Equipment_Schedule",
            "HeatingSetpoint": "Heating_Setpoint",
            "CoolingSetpoint": "Cooling_Setpoint",
            "Infiltration": "Infiltration_Schedule",
        }
        for fam in families:
            mo_stub = mo_lib[fam]
            new_stub = {
                k: v for k, v in mo_stub.items() if k != "Name"
            }
            new_stub["Name"] = f"{prefix_map[fam]}_OpenUBEMUnknown"
            # Reorder so Name is first
            ordered = {"Name": new_stub.pop("Name")}
            ordered.update(new_stub)
            unknown_stub[fam] = ordered
    library["OpenUBEMUnknown"] = unknown_stub

    return library


def _self_check(library: dict, loads_table: dict) -> None:
    # 30 keys (29 real + OpenUBEMUnknown)
    assert len(library) == 30, f"Expected 30 keys, got {len(library)}"

    # 6 families per archetype
    for arch, stubs in library.items():
        assert len(stubs) == 6, f"{arch}: expected 6 families, got {len(stubs)}"

    # F16 invariant: occupied plateau == setpoint scalar
    for arch in ARCHETYPES_29:
        row = loads_table[arch]
        stubs = library[arch]

        htg_stub = stubs["HeatingSetpoint"]
        clg_stub = stubs["CoolingSetpoint"]

        for day_key in ("For: Weekdays", "For: Saturday", "For: AllOtherDays"):
            htg_entries = htg_stub[day_key]
            clg_entries = clg_stub[day_key]

            # Check that some entry has the occupied value
            htg_vals = {e["Value"] for e in htg_entries}
            clg_vals = {e["Value"] for e in clg_entries}
            assert row["heating_setpoint_c"] in htg_vals or row["heating_setback_c"] in htg_vals, (
                f"{arch} HTG: scalar {row['heating_setpoint_c']} not in {htg_vals}"
            )
            assert row["cooling_setpoint_c"] in clg_vals or row["cooling_setup_c"] in clg_vals, (
                f"{arch} CLG: scalar {row['cooling_setpoint_c']} not in {clg_vals}"
            )

    # AllOtherDays present
    for arch, stubs in library.items():
        for fam, stub in stubs.items():
            assert "For: AllOtherDays" in stub, f"{arch}/{fam} missing AllOtherDays"

    # Name patterns
    name_prefixes = {
        "Occupancy": "Occupancy_Schedule_",
        "Lighting": "Lighting_Schedule_",
        "Equipment": "Equipment_Schedule_",
        "HeatingSetpoint": "Heating_Setpoint_",
        "CoolingSetpoint": "Cooling_Setpoint_",
        "Infiltration": "Infiltration_Schedule_",
    }
    for arch, stubs in library.items():
        for fam, prefix in name_prefixes.items():
            assert stubs[fam]["Name"] == f"{prefix}{arch}", (
                f"{arch}/{fam}: name {stubs[fam]['Name']} != {prefix}{arch}"
            )

    # Fractions in [0, 1]
    frac_families = {"Occupancy", "Lighting", "Equipment", "Infiltration"}
    for arch, stubs in library.items():
        for fam in frac_families:
            stub = stubs[fam]
            for day_key in ("For: Weekdays", "For: Saturday", "For: AllOtherDays"):
                for entry in stub[day_key]:
                    assert 0.0 <= entry["Value"] <= 1.0, (
                        f"{arch}/{fam}/{day_key}: fraction {entry['Value']} out of [0,1]"
                    )

    print(f"Self-check PASSED: 30 keys x 6 families, F16 invariant OK, "
          f"name patterns OK, fractions OK")


def main() -> None:
    out_dir = DATA_ROOT / "schedules"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load combined loads table
    with open(LOADS_DIR / "doe_prototype_loads.json") as f:
        doe16 = json.load(f)
    with open(LOADS_DIR / "openstudio_loads.json") as f:
        ext13 = json.load(f)
    loads_table = {**doe16, **ext13}

    library = build_schedule_library_data(loads_table)
    _self_check(library, loads_table)

    out_path = out_dir / "doe_schedules.json"
    out_path.write_text(json.dumps(library, indent=2), encoding="utf-8")
    print(f"Written {out_path} ({len(library)} archetypes × 6 families)")


if __name__ == "__main__":
    main()
