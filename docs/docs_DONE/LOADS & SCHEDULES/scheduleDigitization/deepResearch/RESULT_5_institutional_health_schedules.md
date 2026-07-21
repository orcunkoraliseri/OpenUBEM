# Verbatim DOE Prototype Schedules: Institutional & Health (School, Hospital, Outpatient)

This report documents the verbatim fractional operating schedules for Occupancy, Lighting, and Equipment for PrimarySchool, SecondarySchool, Hospital, and Outpatient building types. The schedules are extracted from the primary source database of the U.S. DOE Commercial Prototype Building Models (specifically the ASHRAE Standard 90.1-2013 edition as implemented in `NREL/openstudio-standards`).

---

## A) PrimarySchool

Primary schools exhibit strong seasonal and day-type variations. The schedules include a reduced-occupancy summer period (July 1 to September 1). The standard (school year) schedules are used for the bulk of the year.

### 1. Occupancy

* **Source Object Name:** `PrimarySchool Bldg Occ`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 1,761.75 hours (Occupancy)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday (School Year)** | 08:00 | 0.0 |
| | 16:00 | 0.75 |
| | 21:00 | 0.15 |
| | 24:00 | 0.0 |
| **Weekday (Summer: Jul 1 – Sep 1)** | 08:00 | 0.0 |
| | 21:00 | 0.15 |
| | 24:00 | 0.0 |
| **Saturday (All Year)** | 24:00 | 0.0 |
| **Sunday / Holiday (All Year)** | 24:00 | 0.0 |

*Daily EFLH: Weekday (School Year) = 6.75, Weekday (Summer) = 1.95, Saturday = 0.0, Sunday = 0.0. Annual EFLH calculated using school year weekday profile as the standard shape.*

### 2. Lighting

* **Source Object Name:** `PrimarySchool Bldg Light`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 4,193.8938 hours (Lighting)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday (School Year)** | 07:00 | 0.1773 |
| | 21:00 | 0.9 |
| | 24:00 | 0.1773 |
| **Weekday (Summer: Jul 1 – Sep 1)** | 08:00 | 0.1773 |
| | 20:00 | 0.5 |
| | 24:00 | 0.1773 |
| **Saturday (All Year)** | 24:00 | 0.1773 |
| **Sunday / Holiday (All Year)** | 24:00 | 0.1773 |

*Daily EFLH: Weekday (School Year) = 14.373, Weekday (Summer) = 8.1276, Saturday = 4.2552, Sunday = 4.2552. Annual EFLH = 14.3730 × 261 + 4.2552 × 52 + 4.2552 × 52.*

### 3. Equipment

* **Source Object Name:** `PrimarySchool Bldg Equip`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 4,475.4000 hours (Equipment)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday (School Year)** | 08:00 | 0.35 |
| | 17:00 | 0.95 |
| | 24:00 | 0.35 |
| **Weekday (Summer: Jul 1 – Sep 1)** | 08:00 | 0.25 |
| | 17:00 | 0.5 |
| | 24:00 | 0.25 |
| **Saturday (School Year)** | 24:00 | 0.35 |
| **Saturday (Summer)** | 24:00 | 0.25 |
| **Sunday / Holiday (School Year)** | 24:00 | 0.35 |
| **Sunday / Holiday (Summer)** | 24:00 | 0.25 |

*Daily EFLH: Weekday (School Year) = 13.80, Weekday (Summer) = 8.25, Saturday (School Year) = 8.40, Sunday (School Year) = 8.40. Annual EFLH = 13.80 × 261 + 8.40 × 52 + 8.40 × 52.*

---

## A2) SecondarySchool

SecondarySchool schedules are structurally similar to PrimarySchool schedules, but they differ in peak weekday occupancy fraction. Weekday occupancy peak is **0.70** for SecondarySchool compared to **0.75** for PrimarySchool. Lighting and Equipment profiles are identical to PrimarySchool.

### 1. Occupancy

* **Source Object Name:** `SecondarySchool Bldg Occ`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 1,657.35 hours (Occupancy)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday (School Year)** | 08:00 | 0.0 |
| | 16:00 | 0.7 |
| | 21:00 | 0.15 |
| | 24:00 | 0.0 |
| **Weekday (Summer: Jul 1 – Sep 1)** | 08:00 | 0.0 |
| | 21:00 | 0.15 |
| | 24:00 | 0.0 |
| **Saturday (All Year)** | 24:00 | 0.0 |
| **Sunday / Holiday (All Year)** | 24:00 | 0.0 |

*Daily EFLH: Weekday (School Year) = 6.35, Weekday (Summer) = 1.95, Saturday = 0.0, Sunday = 0.0. Annual EFLH = 6.35 × 261 + 0.0 × 52 + 0.0 × 52.*

### 2. Lighting
*Identical to PrimarySchool Bldg Light. Annual EFLH: 4,193.8938 hours.*

### 3. Equipment
*Identical to PrimarySchool Bldg Equip. Annual EFLH: 4,475.4000 hours.*

---

## B) Hospital

Hospitals operate 24/7, resulting in high baseline energy usage overnight and during weekends.

### 1. Occupancy

* **Source Object Name:** `Hospital BLDG_OCC_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 2,436.90 hours (Occupancy)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 07:00 | 0.0 |
| | 08:00 | 0.1 |
| | 09:00 | 0.5 |
| | 17:00 | 0.8 |
| | 18:00 | 0.5 |
| | 20:00 | 0.3 |
| | 22:00 | 0.2 |
| | 24:00 | 0.0 |
| **Saturday** | 07:00 | 0.0 |
| | 08:00 | 0.1 |
| | 09:00 | 0.3 |
| | 17:00 | 0.4 |
| | 19:00 | 0.1 |
| | 24:00 | 0.0 |
| **Sunday / Holiday** | 08:00 | 0.0 |
| | 16:00 | 0.05 |
| | 24:00 | 0.0 |

*Daily EFLH: Weekday = 8.50, Saturday = 3.80, Sunday = 0.40. Annual EFLH = 8.50 × 261 + 3.80 × 52 + 0.40 × 52.*

### 2. Lighting

* **Source Object Name:** `Hospital BLDG_LIGHT_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 3,135.8000 hours (Lighting)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 07:00 | 0.1 |
| | 08:00 | 0.5 |
| | 16:00 | 0.9 |
| | 23:00 | 0.3 |
| | 24:00 | 0.1 |
| **Saturday** | 07:00 | 0.1 |
| | 08:00 | 0.2 |
| | 18:00 | 0.4 |
| | 24:00 | 0.1 |
| **Sunday / Holiday** | 08:00 | 0.05 |
| | 16:00 | 0.1 |
| | 24:00 | 0.05 |

*Daily EFLH: Weekday = 10.60, Saturday = 5.50, Sunday = 1.60. Annual EFLH = 10.60 × 261 + 5.50 × 52 + 1.60 × 52.*

### 3. Equipment

* **Source Object Name:** `Hospital BLDG_EQUIP_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 4,743.3580 hours (Equipment)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 07:00 | 0.3492682264 |
| | 08:00 | 0.6818012803 |
| | 16:00 | 0.8766016461 |
| | 22:00 | 0.584401097 |
| | 23:00 | 0.5239023396 |
| | 24:00 | 0.3492682264 |
| **Saturday** | 07:00 | 0.3492682264 |
| | 08:00 | 0.4870009145 |
| | 18:00 | 0.63310118885 |
| | 24:00 | 0.3492682264 |
| **Sunday / Holiday** | 08:00 | 0.2619511698 |
| | 16:00 | 0.3492682264 |
| | 24:00 | 0.2619511698 |

*Daily EFLH: Weekday = 14.5191, Saturday = 11.3585, Sunday = 6.9854. Annual EFLH = 14.5191 × 261 + 11.3585 × 52 + 6.9854 × 52.*

---

## C) Outpatient (Outpatient HealthCare)

Outpatient clinics are daytime-focused facilities. They operate primarily during weekdays and Saturday mornings, with minimal baseloads overnight and on Sundays.

### 1. Occupancy

* **Source Object Name:** `OutPatientHealthCare BLDG_OCC_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 3,480.90 hours (Occupancy)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 04:00 | 0.05 |
| | 06:00 | 0.2 |
| | 07:00 | 0.5 |
| | 18:00 | 0.9 |
| | 20:00 | 0.5 |
| | 22:00 | 0.2 |
| | 24:00 | 0.05 |
| **Saturday** | 07:00 | 0.05 |
| | 09:00 | 0.2 |
| | 15:00 | 0.3 |
| | 20:00 | 0.2 |
| | 24:00 | 0.05 |
| **Sunday / Holiday** | 08:00 | 0.0 |
| | 17:00 | 0.05 |
| | 24:00 | 0.0 |

*Daily EFLH: Weekday = 12.50, Saturday = 3.75, Sunday = 0.45. Annual EFLH = 12.50 × 261 + 3.75 × 52 + 0.45 × 52.*

### 2. Lighting

* **Source Object Name:** `OutPatientHealthCare BLDG_LIGHT_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 3,900.5000 hours (Lighting)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 04:00 | 0.1 |
| | 06:00 | 0.3 |
| | 07:00 | 0.6 |
| | 18:00 | 0.9 |
| | 20:00 | 0.6 |
| | 22:00 | 0.3 |
| | 24:00 | 0.1 |
| **Saturday** | 07:00 | 0.1 |
| | 09:00 | 0.3 |
| | 15:00 | 0.4 |
| | 20:00 | 0.3 |
| | 24:00 | 0.1 |
| **Sunday / Holiday** | 08:00 | 0.05 |
| | 17:00 | 0.1 |
| | 24:00 | 0.05 |

*Daily EFLH: Weekday = 13.50, Saturday = 5.60, Sunday = 1.65. Annual EFLH = 13.50 × 261 + 5.60 × 52 + 1.65 × 52.*

### 3. Equipment

* **Source Object Name:** `OutPatientHealthCare BLDG_EQUIP_SCH`
* **Source File:** `lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json`
* **File URL:** [ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Annual EFLH:** 5,351.6000 hours (Equipment)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 04:00 | 0.3 |
| | 06:00 | 0.5 |
| | 18:00 | 1.0 |
| | 20:00 | 0.5 |
| | 24:00 | 0.3 |
| **Saturday** | 07:00 | 0.3 |
| | 09:00 | 0.5 |
| | 15:00 | 0.8 |
| | 20:00 | 0.5 |
| | 24:00 | 0.3 |
| **Sunday / Holiday** | 08:00 | 0.3 |
| | 17:00 | 0.5 |
| | 24:00 | 0.3 |

*Daily EFLH: Weekday = 16.40, Saturday = 11.60, Sunday = 9.00. Annual EFLH = 16.40 × 261 + 11.60 × 52 + 9.00 × 52.*

---

## Citation

* **Title:** U.S. Department of Energy Commercial Prototype Building Models
* **Agency:** Pacific Northwest National Laboratory (PNNL) & National Renewable Energy Laboratory (NREL)
* **Standard Edition:** ANSI/ASHRAE/IES Standard 90.1-2013
* **Repository / Database Name:** openstudio-standards GitHub Repository
* **Repository URL:** [https://github.com/NREL/openstudio-standards](https://github.com/NREL/openstudio-standards)
* **Data Source File URL:** [https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json](https://raw.githubusercontent.com/NREL/openstudio-standards/master/lib/openstudio-standards/standards/ashrae_90_1/data/ashrae_90_1.schedules.json)
* **Access Date:** 2026-06-17
