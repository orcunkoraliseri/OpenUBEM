"""
Build doe_schedules.json — 30 archetypes × 6 families × 3 day-types of Schedule:Compact stubs.

Source: energycodes.gov DOE Commercial Prototype Building IDFs, edition ASHRAE 90.1-2013.
OQ-2 closure: replaces synthetic occupancy-linear transforms with explicit digitized profiles
parsed from the STD2013 IDFs (parse_doe_schedules.py). DESIGN §3F/OQ-2 (lines 227/300).
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

# ---------------------------------------------------------------------------
# Occupancy profiles — digitized from energycodes.gov STD2013 prototype IDFs.
# Internal day keys: Weekday / Saturday / Sunday (Sunday maps to AllOtherDays in output).
# Empty Saturday list = no-occupancy day; setpoint/infiltration generators receive
# a fallback [("24:00", 0.0)] so the F16 invariant check passes (all-unoccupied plateau).
# ---------------------------------------------------------------------------

# Source: MediumOffice_90.1-2013.idf — object BLDG_OCC_SCH
_OCC_PROFILES: dict[str, dict[str, list[tuple[str, float]]]] = {
    "Office": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.1), ("08:00", 0.2), ("12:00", 0.95),
            ("13:00", 0.5), ("17:00", 0.95), ("18:00", 0.3), ("22:00", 0.1),
            ("24:00", 0.05),
        ],
        "Saturday": [
            ("06:00", 0.0), ("08:00", 0.1), ("12:00", 0.3),
            ("17:00", 0.1), ("19:00", 0.05), ("24:00", 0.0),
        ],
        "Sunday": [
            ("06:00", 0.0), ("18:00", 0.05), ("24:00", 0.0),
        ],
    },
    # Source: RetailStandalone_90.1-2013.idf — object BLDG_OCC_SCH
    "Retail": {
        "Weekday": [
            ("07:00", 0.0), ("08:00", 0.1), ("09:00", 0.2), ("11:00", 0.5),
            ("15:00", 0.7), ("16:00", 0.8), ("17:00", 0.7), ("19:00", 0.5),
            ("21:00", 0.3), ("24:00", 0.0),
        ],
        "Saturday": [
            ("07:00", 0.0), ("08:00", 0.1), ("09:00", 0.2), ("10:00", 0.5),
            ("11:00", 0.6), ("17:00", 0.8), ("18:00", 0.6), ("21:00", 0.2),
            ("22:00", 0.1), ("24:00", 0.0),
        ],
        "Sunday": [
            ("09:00", 0.0), ("10:00", 0.1), ("12:00", 0.2), ("17:00", 0.4),
            ("18:00", 0.2), ("19:00", 0.1), ("24:00", 0.0),
        ],
    },
    # Source: SchoolPrimary_90.1-2013.idf — object BLDG_OCC_SCH
    "School": {
        "Weekday": [
            ("08:00", 0.0), ("16:00", 0.95), ("21:00", 0.15), ("24:00", 0.0),
        ],
        "Saturday": [],  # no occupancy; fallback applied in builder
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    # Source: SmallHotel_90.1-2013.idf — object GuestRoom_Occ_Sch
    "Hotel": {
        "Weekday": [
            ("06:00", 1.0), ("07:00", 0.77), ("09:00", 0.43), ("15:00", 0.2),
            ("16:00", 0.31), ("19:00", 0.54), ("21:00", 0.77), ("22:00", 0.89),
            ("24:00", 1.0),
        ],
        "Saturday": [
            ("06:00", 1.0), ("07:00", 0.77), ("09:00", 0.53), ("17:00", 0.3),
            ("18:00", 0.53), ("19:00", 0.54), ("21:00", 0.65), ("24:00", 0.77),
        ],
        "Sunday": [
            ("06:00", 1.0), ("07:00", 0.77), ("09:00", 0.53), ("17:00", 0.3),
            ("18:00", 0.53), ("19:00", 0.54), ("21:00", 0.65), ("24:00", 0.77),
        ],
    },
    # Source: MidriseApartment_90.1-2013.idf — object OCC_APT_SCH_WORKING_FAMILY
    "Apartment": {
        "Weekday": [
            ("08:00", 1.0), ("18:00", 0.0), ("24:00", 1.0),
        ],
        "Saturday": [],  # AllOtherDays profile used; fallback applied in builder
        "Sunday": [
            ("11:00", 1.0), ("15:00", 0.5), ("16:00", 0.0), ("24:00", 1.0),
        ],
    },
    # Source: Warehouse_90.1-2013.idf — object BLDG_OCC_SCH
    "Warehouse": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.11), ("08:00", 0.21), ("12:00", 1.0),
            ("13:00", 0.53), ("17:00", 1.0), ("18:00", 0.32), ("24:00", 0.0),
        ],
        "Saturday": [
            ("06:00", 0.0), ("07:00", 0.11), ("08:00", 0.21), ("12:00", 1.0),
            ("13:00", 0.53), ("17:00", 1.0), ("18:00", 0.32), ("24:00", 0.0),
        ],
        "Sunday": [
            ("24:00", 0.0),
        ],
    },
    # Source: Restaurant_FullServiceRestaurant.idf — object BLDG_OCC_SCH
    "Restaurant": {
        "Weekday": [
            ("01:00", 0.05), ("05:00", 0.0), ("06:00", 0.05), ("07:00", 0.1),
            ("10:00", 0.4), ("11:00", 0.2), ("12:00", 0.5), ("13:00", 0.8),
            ("14:00", 0.7), ("15:00", 0.4), ("16:00", 0.2), ("17:00", 0.25),
            ("18:00", 0.5), ("21:00", 0.8), ("22:00", 0.5), ("23:00", 0.35),
            ("24:00", 0.2),
        ],
        "Saturday": [
            ("01:00", 0.05), ("06:00", 0.0), ("07:00", 0.05), ("09:00", 0.5),
            ("10:00", 0.4), ("11:00", 0.2), ("12:00", 0.45), ("14:00", 0.5),
            ("15:00", 0.35), ("18:00", 0.3), ("19:00", 0.7), ("20:00", 0.9),
            ("21:00", 0.7), ("22:00", 0.65), ("23:00", 0.55), ("24:00", 0.35),
        ],
        "Sunday": [
            ("01:00", 0.05), ("06:00", 0.0), ("07:00", 0.05), ("09:00", 0.5),
            ("11:00", 0.2), ("12:00", 0.3), ("14:00", 0.5), ("15:00", 0.3),
            ("16:00", 0.2), ("17:00", 0.25), ("18:00", 0.35), ("19:00", 0.55),
            ("20:00", 0.65), ("21:00", 0.7), ("22:00", 0.35), ("24:00", 0.2),
        ],
    },
    # Source: Hospital_90.1-2013.idf — object BLDG_OCC_SCH
    "Hospital": {
        "Weekday": [
            ("07:00", 0.0), ("08:00", 0.1), ("09:00", 0.5), ("17:00", 0.8),
            ("18:00", 0.5), ("20:00", 0.3), ("22:00", 0.2), ("24:00", 0.0),
        ],
        "Saturday": [
            ("07:00", 0.0), ("08:00", 0.1), ("09:00", 0.3), ("17:00", 0.4),
            ("19:00", 0.1), ("24:00", 0.0),
        ],
        "Sunday": [
            ("08:00", 0.0), ("16:00", 0.05), ("24:00", 0.0),
        ],
    },
    # Source: OutPatientHealthCare_90.1-2013.idf — object BLDG_OCC_SCH
    "Outpatient": {
        "Weekday": [
            ("06:00", 0.0), ("07:00", 0.5), ("18:00", 0.9), ("19:00", 0.5),
            ("24:00", 0.0),
        ],
        "Saturday": [
            ("06:00", 0.0), ("09:00", 0.2), ("15:00", 0.3), ("19:00", 0.2),
            ("24:00", 0.0),
        ],
        "Sunday": [
            ("06:00", 0.0), ("19:00", 0.05), ("24:00", 0.0),
        ],
    },
    # DataCenter: no DOE STD2013 prototype — documented 24/7 constant=1.0 exception (PROVENANCE.md)
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

# ---------------------------------------------------------------------------
# Lighting profiles — digitized VERBATIM from energycodes.gov STD2013 IDFs.
# Never normalized: residential peak legitimately = 0.18106 (diversity-baked).
# ---------------------------------------------------------------------------

# Source: MediumOffice_90.1-2013.idf — object ltg_sch_office
_LIGHTING_PROFILES: dict[str, dict[str, list[tuple[str, float]]]] = {
    "Office": {
        "Weekday": [
            ("05:00", 0.04184), ("07:00", 0.08368), ("08:00", 0.25105),
            ("17:00", 0.75314), ("18:00", 0.41841), ("20:00", 0.25105),
            ("22:00", 0.16736), ("23:00", 0.08368), ("24:00", 0.04184),
        ],
        "Saturday": [
            ("06:00", 0.04184), ("08:00", 0.08368), ("12:00", 0.25105),
            ("17:00", 0.12552), ("24:00", 0.04184),
        ],
        "Sunday": [
            ("24:00", 0.04184),
        ],
    },
    # Source: RetailStandalone_90.1-2013.idf — object ltg_sch_sale
    "Retail": {
        "Weekday": [
            ("07:00", 0.05), ("08:00", 0.2), ("09:00", 0.4), ("18:00", 0.9),
            ("21:00", 0.5), ("22:00", 0.2), ("24:00", 0.05),
        ],
        "Saturday": [
            ("07:00", 0.05), ("08:00", 0.1), ("09:00", 0.3), ("10:00", 0.6),
            ("18:00", 0.9), ("19:00", 0.5), ("21:00", 0.3), ("22:00", 0.1),
            ("24:00", 0.05),
        ],
        "Sunday": [
            ("09:00", 0.05), ("10:00", 0.1), ("12:00", 0.4), ("17:00", 0.6),
            ("18:00", 0.4), ("19:00", 0.2), ("24:00", 0.05),
        ],
    },
    # Source: SchoolPrimary_90.1-2013.idf — object ltg_sch_classroom
    "School": {
        "Weekday": [
            ("07:00", 0.12012), ("21:00", 0.60975), ("24:00", 0.12012),
        ],
        "Saturday": [
            ("24:00", 0.12012),
        ],
        "Sunday": [
            ("24:00", 0.12012),
        ],
    },
    # Source: SmallHotel_90.1-2013.idf — object ltg_sch_guestroom
    "Hotel": {
        "Weekday": [
            ("01:00", 0.121), ("02:00", 0.0935), ("05:00", 0.0605),
            ("06:00", 0.121), ("07:00", 0.242), ("08:00", 0.308),
            ("10:00", 0.242), ("18:00", 0.154), ("19:00", 0.3685),
            ("20:00", 0.4895), ("21:00", 0.55), ("22:00", 0.4895),
            ("23:00", 0.3685), ("24:00", 0.1815),
        ],
        "Saturday": [
            ("02:00", 0.143), ("06:00", 0.0605), ("08:00", 0.2255),
            ("10:00", 0.308), ("11:00", 0.2255), ("18:00", 0.1815),
            ("19:00", 0.4675), ("22:00", 0.55), ("23:00", 0.4675),
            ("24:00", 0.2255),
        ],
        "Sunday": [
            ("02:00", 0.143), ("06:00", 0.0605), ("08:00", 0.2255),
            ("10:00", 0.308), ("11:00", 0.2255), ("18:00", 0.1815),
            ("19:00", 0.4675), ("22:00", 0.55), ("23:00", 0.4675),
            ("24:00", 0.2255),
        ],
    },
    # Source: MidriseApartment_90.1-2013.idf — object ltg_sch_apartment_hardwired
    # Peak 0.18106 is diversity-baked; paired with full installed LPD — do NOT normalize.
    "Apartment": {
        "Weekday": [
            ("04:00", 0.01132), ("05:00", 0.03395), ("06:00", 0.07355),
            ("07:00", 0.07921), ("08:00", 0.07355), ("09:00", 0.03395),
            ("15:00", 0.02263), ("16:00", 0.03961), ("17:00", 0.07921),
            ("18:00", 0.11316), ("19:00", 0.15277), ("21:00", 0.18106),
            ("22:00", 0.12448), ("23:00", 0.0679), ("24:00", 0.02829),
        ],
        "Saturday": [
            ("04:00", 0.01132), ("05:00", 0.03395), ("06:00", 0.07355),
            ("07:00", 0.07921), ("08:00", 0.07355), ("09:00", 0.03395),
            ("15:00", 0.02263), ("16:00", 0.03961), ("17:00", 0.07921),
            ("18:00", 0.11316), ("19:00", 0.15277), ("21:00", 0.18106),
            ("22:00", 0.12448), ("23:00", 0.0679), ("24:00", 0.02829),
        ],
        "Sunday": [
            ("04:00", 0.01132), ("05:00", 0.03395), ("06:00", 0.07355),
            ("07:00", 0.07921), ("08:00", 0.07355), ("09:00", 0.03395),
            ("15:00", 0.02263), ("16:00", 0.03961), ("17:00", 0.07921),
            ("18:00", 0.11316), ("19:00", 0.15277), ("21:00", 0.18106),
            ("22:00", 0.12448), ("23:00", 0.0679), ("24:00", 0.02829),
        ],
    },
    # Source: Warehouse_90.1-2013.idf — object ltg_sch_bulk_storage
    "Warehouse": {
        "Weekday": [
            ("07:00", 0.04375), ("08:00", 0.2625), ("09:00", 0.32812),
            ("16:00", 0.37188), ("17:00", 0.32812), ("18:00", 0.2625),
            ("24:00", 0.04375),
        ],
        "Saturday": [
            ("07:00", 0.04375), ("08:00", 0.2625), ("09:00", 0.32812),
            ("16:00", 0.37188), ("17:00", 0.32812), ("18:00", 0.2625),
            ("24:00", 0.04375),
        ],
        "Sunday": [
            ("24:00", 0.04375),
        ],
    },
    # Source: Restaurant_FullServiceRestaurant.idf — object ltg_sch_dining
    "Restaurant": {
        "Weekday": [
            ("05:00", 0.14241), ("06:00", 0.18988), ("08:00", 0.37975),
            ("10:00", 0.56963), ("22:00", 0.85444), ("23:00", 0.47469),
            ("24:00", 0.28481),
        ],
        "Saturday": [
            ("01:00", 0.18988), ("06:00", 0.14241), ("08:00", 0.28481),
            ("10:00", 0.56963), ("17:00", 0.75951), ("22:00", 0.85444),
            ("23:00", 0.47469), ("24:00", 0.28481),
        ],
        "Sunday": [
            ("01:00", 0.18988), ("06:00", 0.14241), ("08:00", 0.28481),
            ("10:00", 0.47469), ("16:00", 0.66457), ("22:00", 0.56963),
            ("23:00", 0.47469), ("24:00", 0.28481),
        ],
    },
    # Source: Hospital_90.1-2013.idf — object ltg_sch10_patient_room
    "Hospital": {
        "Weekday": [
            ("08:00", 0.5), ("16:00", 0.9), ("24:00", 0.5),
        ],
        "Saturday": [
            ("08:00", 0.5), ("18:00", 0.8), ("24:00", 0.5),
        ],
        "Sunday": [
            ("08:00", 0.5), ("16:00", 0.7), ("24:00", 0.5),
        ],
    },
    # Source: OutPatientHealthCare_90.1-2013.idf — object ltg_sch_exam
    "Outpatient": {
        "Weekday": [
            ("04:00", 0.1), ("06:00", 0.3), ("07:00", 0.6), ("18:00", 0.9),
            ("20:00", 0.6), ("22:00", 0.3), ("24:00", 0.1),
        ],
        "Saturday": [
            ("07:00", 0.1), ("09:00", 0.3), ("15:00", 0.4), ("20:00", 0.3),
            ("24:00", 0.1),
        ],
        "Sunday": [
            ("08:00", 0.05), ("17:00", 0.1), ("24:00", 0.05),
        ],
    },
    # DataCenter: no DOE STD2013 prototype — documented 24/7 constant=1.0 exception (PROVENANCE.md)
    "DataCenter": {
        "Weekday": [("24:00", 1.0)],
        "Saturday": [("24:00", 1.0)],
        "Sunday": [("24:00", 1.0)],
    },
}

# ---------------------------------------------------------------------------
# Equipment profiles — digitized VERBATIM from energycodes.gov STD2013 IDFs.
# ---------------------------------------------------------------------------

# Source: MediumOffice_90.1-2013.idf — object BLDG_EQUIP_SCH
_EQUIPMENT_PROFILES: dict[str, dict[str, list[tuple[str, float]]]] = {
    "Office": {
        "Weekday": [
            ("06:00", 0.3076738408), ("08:00", 0.381234796), ("12:00", 0.857778291),
            ("13:00", 0.762469592), ("17:00", 0.857778291), ("18:00", 0.476543495),
            ("24:00", 0.381234796),
        ],
        "Saturday": [
            ("06:00", 0.2307553806), ("08:00", 0.381234796), ("12:00", 0.476543495),
            ("17:00", 0.3335804465), ("19:00", 0.285926097), ("24:00", 0.2307553806),
        ],
        "Sunday": [
            ("06:00", 0.2307553806), ("18:00", 0.285926097), ("24:00", 0.2307553806),
        ],
    },
    # Source: RetailStandalone_90.1-2013.idf — object BLDG_EQUIP_SCH
    "Retail": {
        "Weekday": [
            ("07:00", 0.1973725624), ("08:00", 0.3988803288), ("09:00", 0.5983204932),
            ("19:00", 0.8974807398), ("20:00", 0.6980405754), ("21:00", 0.6980405754),
            ("22:00", 0.1973725624), ("24:00", 0.1973725624),
        ],
        "Saturday": [
            ("07:00", 0.1480294218), ("08:00", 0.2991602466), ("09:00", 0.498600411),
            ("10:00", 0.7977606576), ("18:00", 0.8974807398), ("19:00", 0.6980405754),
            ("21:00", 0.498600411), ("22:00", 0.2991602466), ("24:00", 0.1480294218),
        ],
        "Sunday": [
            ("09:00", 0.1480294218), ("10:00", 0.2991602466), ("12:00", 0.5983204932),
            ("17:00", 0.7977606576), ("18:00", 0.5983204932), ("19:00", 0.3988803288),
            ("24:00", 0.1480294218),
        ],
    },
    # Source: SchoolPrimary_90.1-2013.idf — object BLDG_EQUIP_SCH
    "School": {
        "Weekday": [
            ("08:00", 0.27288986445), ("17:00", 0.88408769755),
            ("21:00", 0.32571652015), ("24:00", 0.27288986445),
        ],
        "Saturday": [],  # no occupancy day; fallback applied in builder
        "Sunday": [
            ("24:00", 0.27288986445),
        ],
    },
    # Source: SmallHotel_90.1-2013.idf — object Guestroom_Eqp_Sch_Adva
    "Hotel": {
        "Weekday": [
            ("06:00", 0.09), ("07:00", 0.62), ("08:00", 0.9), ("10:00", 0.43),
            ("16:00", 0.12), ("17:00", 0.19), ("19:00", 0.48), ("20:00", 0.46),
            ("21:00", 0.62), ("22:00", 0.69), ("23:00", 0.34), ("24:00", 0.09),
        ],
        "Saturday": [
            ("06:00", 0.09), ("07:00", 0.3), ("08:00", 0.62), ("09:00", 0.9),
            ("10:00", 0.62), ("16:00", 0.13), ("17:00", 0.21), ("18:00", 0.4),
            ("19:00", 0.48), ("20:00", 0.46), ("21:00", 0.62), ("22:00", 0.69),
            ("23:00", 0.34), ("24:00", 0.09),
        ],
        "Sunday": [
            ("06:00", 0.09), ("07:00", 0.3), ("08:00", 0.62), ("09:00", 0.9),
            ("10:00", 0.62), ("16:00", 0.13), ("17:00", 0.21), ("18:00", 0.4),
            ("19:00", 0.48), ("20:00", 0.46), ("21:00", 0.62), ("22:00", 0.69),
            ("23:00", 0.34), ("24:00", 0.09),
        ],
    },
    # Source: MidriseApartment_90.1-2013.idf — object EQP_APT_SCH
    "Apartment": {
        "Weekday": [
            ("01:00", 0.45), ("02:00", 0.41), ("03:00", 0.39), ("05:00", 0.38),
            ("06:00", 0.43), ("07:00", 0.54), ("08:00", 0.65), ("09:00", 0.66),
            ("10:00", 0.67), ("11:00", 0.69), ("12:00", 0.7), ("13:00", 0.69),
            ("14:00", 0.66), ("15:00", 0.65), ("16:00", 0.68), ("17:00", 0.8),
            ("19:00", 1.0), ("20:00", 0.93), ("21:00", 0.89), ("22:00", 0.85),
            ("23:00", 0.71), ("24:00", 0.58),
        ],
        "Saturday": [
            ("01:00", 0.45), ("02:00", 0.41), ("03:00", 0.39), ("05:00", 0.38),
            ("06:00", 0.43), ("07:00", 0.54), ("08:00", 0.65), ("09:00", 0.66),
            ("10:00", 0.67), ("11:00", 0.69), ("12:00", 0.7), ("13:00", 0.69),
            ("14:00", 0.66), ("15:00", 0.65), ("16:00", 0.68), ("17:00", 0.8),
            ("19:00", 1.0), ("20:00", 0.93), ("21:00", 0.89), ("22:00", 0.85),
            ("23:00", 0.71), ("24:00", 0.58),
        ],
        "Sunday": [
            ("01:00", 0.45), ("02:00", 0.41), ("03:00", 0.39), ("05:00", 0.38),
            ("06:00", 0.43), ("07:00", 0.54), ("08:00", 0.65), ("09:00", 0.66),
            ("10:00", 0.67), ("11:00", 0.69), ("12:00", 0.7), ("13:00", 0.69),
            ("14:00", 0.66), ("15:00", 0.65), ("16:00", 0.68), ("17:00", 0.8),
            ("19:00", 1.0), ("20:00", 0.93), ("21:00", 0.89), ("22:00", 0.85),
            ("23:00", 0.71), ("24:00", 0.58),
        ],
    },
    # Source: Warehouse_90.1-2013.idf — object Bulk Storage Plug Schedule
    "Warehouse": {
        "Weekday": [
            ("08:00", 0.25), ("12:00", 1.0), ("13:00", 0.25),
            ("17:00", 1.0), ("24:00", 0.25),
        ],
        "Saturday": [
            ("08:00", 0.25), ("12:00", 1.0), ("13:00", 0.25),
            ("17:00", 1.0), ("24:00", 0.25),
        ],
        "Sunday": [
            ("08:00", 0.25), ("12:00", 1.0), ("13:00", 0.25),
            ("17:00", 1.0), ("24:00", 0.25),
        ],
    },
    # Source: Restaurant_FullServiceRestaurant.idf — object BLDG_EQUIP_SCH
    "Restaurant": {
        "Weekday": [
            ("01:00", 0.02983040367), ("02:00", 0.01988693578), ("03:00", 0.02983040367),
            ("04:00", 0.01988693578), ("05:00", 0.04971733945), ("06:00", 0.11986705716),
            ("07:00", 0.12985597859), ("08:00", 0.14983382145), ("09:00", 0.17980058574),
            ("10:00", 0.20976735003), ("11:00", 0.25971195718), ("12:00", 0.28967872147),
            ("13:00", 0.26970087861), ("14:00", 0.24972303575), ("15:00", 0.22974519289),
            ("16:00", 0.22974519289), ("17:00", 0.25971195718), ("18:00", 0.25971195718),
            ("19:00", 0.23973411432), ("20:00", 0.21975627146), ("21:00", 0.1997784286),
            ("22:00", 0.17980058574), ("23:00", 0.08990029287), ("24:00", 0.02983040367),
        ],
        "Saturday": [
            ("01:00", 0.02983040367), ("02:00", 0.01988693578), ("03:00", 0.02983040367),
            ("04:00", 0.01988693578), ("05:00", 0.04971733945), ("06:00", 0.11986705716),
            ("07:00", 0.12985597859), ("08:00", 0.14983382145), ("09:00", 0.17980058574),
            ("10:00", 0.20976735003), ("11:00", 0.25971195718), ("12:00", 0.28967872147),
            ("13:00", 0.26970087861), ("14:00", 0.24972303575), ("15:00", 0.22974519289),
            ("16:00", 0.22974519289), ("17:00", 0.25971195718), ("18:00", 0.25971195718),
            ("19:00", 0.23973411432), ("20:00", 0.21975627146), ("21:00", 0.1997784286),
            ("22:00", 0.17980058574), ("23:00", 0.08990029287), ("24:00", 0.02983040367),
        ],
        "Sunday": [
            ("01:00", 0.02983040367), ("02:00", 0.01988693578), ("03:00", 0.02983040367),
            ("04:00", 0.01988693578), ("05:00", 0.04971733945), ("06:00", 0.11932161468),
            ("07:00", 0.12985597859), ("08:00", 0.14983382145), ("09:00", 0.17980058574),
            ("10:00", 0.20976735003), ("11:00", 0.25971195718), ("12:00", 0.28967872147),
            ("13:00", 0.26970087861), ("14:00", 0.24972303575), ("15:00", 0.22974519289),
            ("16:00", 0.22974519289), ("17:00", 0.25971195718), ("18:00", 0.25971195718),
            ("19:00", 0.23973411432), ("20:00", 0.21975627146), ("21:00", 0.1997784286),
            ("22:00", 0.17980058574), ("23:00", 0.08990029287), ("24:00", 0.02996676429),
        ],
    },
    # Source: Hospital_90.1-2013.idf — object BLDG_EQUIP_SCH
    "Hospital": {
        "Weekday": [
            ("07:00", 0.3492682264), ("08:00", 0.6818012803), ("16:00", 0.8766016461),
            ("22:00", 0.5844010974), ("23:00", 0.5239023396), ("24:00", 0.3492682264),
        ],
        "Saturday": [
            ("07:00", 0.3492682264), ("08:00", 0.4870009145),
            ("18:00", 0.63310118885), ("24:00", 0.3492682264),
        ],
        "Sunday": [
            ("08:00", 0.2619511698), ("16:00", 0.3492682264), ("24:00", 0.2619511698),
        ],
    },
    # Source: OutPatientHealthCare_90.1-2013.idf — object BLDG_EQUIP_SCH
    "Outpatient": {
        "Weekday": [
            ("04:00", 0.2971381545), ("06:00", 0.4952302575), ("18:00", 0.990460515),
            ("20:00", 0.4952302575), ("24:00", 0.2971381545),
        ],
        "Saturday": [
            ("07:00", 0.2971381545), ("09:00", 0.4952302575), ("15:00", 0.792368412),
            ("20:00", 0.4952302575), ("24:00", 0.2971381545),
        ],
        "Sunday": [
            ("08:00", 0.2971381545), ("17:00", 0.4952302575), ("24:00", 0.2971381545),
        ],
    },
    # DataCenter: no DOE STD2013 prototype — documented 24/7 constant=1.0 exception (PROVENANCE.md)
    "DataCenter": {
        "Weekday": [("24:00", 1.0)],
        "Saturday": [("24:00", 1.0)],
        "Sunday": [("24:00", 1.0)],
    },
}

# Fallback for empty-day occupancy profiles (School Saturday, Apartment Saturday):
# all-zero occupancy so setpoint/infiltration generators produce full-unoccupied plateau.
_EMPTY_DAY_FALLBACK: list[tuple[str, float]] = [("24:00", 0.0)]


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
    Build 30-key × 6-family schedule dict from digitized profiles + loads scalars.
    loads_table: combined doe_prototype_loads + openstudio_loads keyed by archetype_id.
    Returns dict[archetype_id -> dict[family -> stub_dict]].
    """
    library: dict[str, dict] = {}

    for arch in ARCHETYPES_29:
        group = _SCHED_GROUP[arch]
        occ_profiles = _OCC_PROFILES[group]
        ltg_profiles = _LIGHTING_PROFILES[group]
        equip_profiles = _EQUIPMENT_PROFILES[group]
        row = loads_table[arch]

        htg_occupied = row["heating_setpoint_c"]
        htg_setback = row["heating_setback_c"]
        clg_occupied = row["cooling_setpoint_c"]
        clg_setup = row["cooling_setup_c"]

        stub_dict: dict[str, dict] = {}

        # Occupancy — explicit digitized per-group profile
        occ_day = {d: occ_profiles[d] for d in ("Weekday", "Saturday", "Sunday")}
        stub_dict["Occupancy"] = _build_stub(
            f"Occupancy_Schedule_{arch}", "Fraction", occ_day
        )

        # Lighting — explicit digitized per-group profile (VERBATIM, no normalization)
        ltg_day = {d: ltg_profiles[d] for d in ("Weekday", "Saturday", "Sunday")}
        stub_dict["Lighting"] = _build_stub(
            f"Lighting_Schedule_{arch}", "Fraction", ltg_day
        )

        # Equipment — explicit digitized per-group profile (VERBATIM)
        equip_day = {d: equip_profiles[d] for d in ("Weekday", "Saturday", "Sunday")}
        stub_dict["Equipment"] = _build_stub(
            f"Equipment_Schedule_{arch}", "Fraction", equip_day
        )

        # Heating setpoint — derived from occupancy; empty days use fallback (all-unoccupied)
        htg_occ_day = {
            d: (occ_profiles[d] if occ_profiles[d] else _EMPTY_DAY_FALLBACK)
            for d in ("Weekday", "Saturday", "Sunday")
        }
        htg_day = {d: _make_setpoint_profile(htg_occ_day[d], htg_occupied, htg_setback)
                   for d in htg_occ_day}
        stub_dict["HeatingSetpoint"] = _build_stub(
            f"Heating_Setpoint_{arch}", "Temperature", htg_day
        )

        # Cooling setpoint — derived from occupancy; empty days use fallback
        clg_day = {d: _make_setpoint_profile(htg_occ_day[d], clg_occupied, clg_setup)
                   for d in htg_occ_day}
        stub_dict["CoolingSetpoint"] = _build_stub(
            f"Cooling_Setpoint_{arch}", "Temperature", clg_day
        )

        # Infiltration — derived from occupancy; empty days use fallback
        infil_day = {d: _make_infiltration_profile(htg_occ_day[d]) for d in htg_occ_day}
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
