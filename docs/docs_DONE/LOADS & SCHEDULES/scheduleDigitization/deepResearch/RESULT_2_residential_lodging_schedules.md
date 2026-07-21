# RESULT_2_residential_lodging_schedules — Verbatim DOE prototype schedules: Residential & Lodging

This report documents the verbatim fractional operating schedules for occupancy, lighting, and plug/process equipment for the **MidriseApartment** (and **HighriseApartment**) and **SmallHotel** (and **LargeHotel**) prototype building models. These values are extracted from the authoritative primary sources: the U.S. DOE Commercial Prototype Building Models (ASHRAE Standard 90.1-2013 edition baselines), as implemented in NREL's `openstudio-standards` and PNNL's `building-energy-standards-data`.

---

## 1. MidriseApartment & HighriseApartment (Apartment Dwelling-Units)

### A. Occupancy
The apartment dwelling units in the DOE prototype building models are divided into two distinct occupant profiles: **Working Family** (applied to approximately 50% of the apartment zones) and **Stay-at-Home Family** (applied to the other 50% of the apartment zones).

#### A1. Stay-at-Home Family Occupancy Profile
* **Source Object Name:** `OCC_APT_SCH_STAY_HOME_FAMILY`
* **Source Files:** 
  * [MidriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/MidriseApartment_90.1-2013.idf)
  * [HighriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/HighriseApartment_90.1-2013.idf)
* **Source File URLs:**
  * [ASHRAE901_ApartmentMidRise_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentMidRise_STD2013.zip)
  * [ASHRAE901_ApartmentHighRise_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentHighRise_STD2013.zip)
* **Annual EFLH (Occupancy - Stay-at-Home Family):** **5,993.30 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **All Days** (Weekday, Saturday, Sunday) | 07:00 | 1.00000 |
| | 08:00 | 0.85000 |
| | 09:00 | 0.39000 |
| | 16:00 | 0.25000 |
| | 17:00 | 0.30000 |
| | 18:00 | 0.52000 |
| | 21:00 | 0.87000 |
| | 24:00 | 1.00000 |

*Note: In the prototype IDF, `OCC_APT_SCH_STAY_HOME_FAMILY` uses the `For: AllDays` field type, indicating the same schedule is applied across weekdays, Saturdays, Sundays, and holidays.*

#### A2. Working Family Occupancy Profile
* **Source Object Name:** `OCC_APT_SCH_WORKING_FAMILY`
* **Source Files:** Same as Stay-at-Home Family
* **Annual EFLH (Occupancy - Working Family):** **5,838.00 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 08:00 | 1.00000 |
| | 18:00 | 0.00000 |
| | 24:00 | 1.00000 |
| **Saturday** | 11:00 | 1.00000 |
| | 15:00 | 0.50000 |
| | 16:00 | 0.00000 |
| | 24:00 | 1.00000 |
| **Sunday / Holidays / AllOtherDays** | 11:00 | 1.00000 |
| | 15:00 | 0.50000 |
| | 16:00 | 0.00000 |
| | 24:00 | 1.00000 |

*Note: The prototype IDF applies `For: Weekday` and `For: Weekend AllOtherDays` for this schedule. In the table above, Saturday and Sunday have been explicitly detailed for consistency.*

---

### B. Lighting
* **Description:** Lighting is modeled using two identical schedule profiles for hardwired and plug-in fixtures. Both schedules share the exact same hourly fraction breakpoints.
* **Source Object Name:** `ltg_sch_apartment_hardwired` (and `ltg_sch_apartment_plugin`)
* **Source Files:**
  * [MidriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/MidriseApartment_90.1-2013.idf)
  * [HighriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/HighriseApartment_90.1-2013.idf)
* **Annual EFLH (Lighting):** **526.63 hours**
* **Daily EFLH:** **1.44 hours/day** (applied to Weekdays, Saturdays, and Sundays)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 04:00 | 0.01132 |
| | 05:00 | 0.03395 |
| | 06:00 | 0.07355 |
| | 07:00 | 0.07921 |
| | 08:00 | 0.07355 |
| | 09:00 | 0.03395 |
| | 15:00 | 0.02263 |
| | 16:00 | 0.03961 |
| | 17:00 | 0.07921 |
| | 18:00 | 0.11316 |
| | 19:00 | 0.15277 |
| | 21:00 | 0.18106 |
| | 22:00 | 0.12448 |
| | 23:00 | 0.06790 |
| | 24:00 | 0.02829 |
| **Saturday** | 04:00 | 0.01132 |
| | 05:00 | 0.03395 |
| | 06:00 | 0.07355 |
| | 07:00 | 0.07921 |
| | 08:00 | 0.07355 |
| | 09:00 | 0.03395 |
| | 15:00 | 0.02263 |
| | 16:00 | 0.03961 |
| | 17:00 | 0.07921 |
| | 18:00 | 0.11316 |
| | 19:00 | 0.15277 |
| | 21:00 | 0.18106 |
| | 22:00 | 0.12448 |
| | 23:00 | 0.06790 |
| | 24:00 | 0.02829 |
| **Sunday / AllOtherDays** | 04:00 | 0.01132 |
| | 05:00 | 0.03395 |
| | 06:00 | 0.07355 |
| | 07:00 | 0.07921 |
| | 08:00 | 0.07355 |
| | 09:00 | 0.03395 |
| | 15:00 | 0.02263 |
| | 16:00 | 0.03961 |
| | 17:00 | 0.07921 |
| | 18:00 | 0.11316 |
| | 19:00 | 0.15277 |
| | 21:00 | 0.18106 |
| | 22:00 | 0.12448 |
| | 23:00 | 0.06790 |
| | 24:00 | 0.02829 |

> [!WARNING]
> **Sanity Anchor Check & Low EFLH Flag:**
> The calculated annual EFLH of **526.63 hours** falls significantly below the typical residential lighting range of **1,500–2,500 EFLH/yr**. This is a known feature of the PNNL prototype building models:
> 1. **Embedded Coincidence Factor:** The fractional schedule values are pre-multiplied by a coincidence factor, meaning the peak fraction in the schedule is **0.18106** (18.1% of peak) rather than 1.0. 
> 2. **Un-scaled Equivalent Hours:** If we normalize the schedule to peak at 1.0 (dividing all fractions by 0.18106), the daily EFLH is **7.97 hours** and the annual equivalent hours is **2,908.57 EFLH/yr**, which aligns closely with typical residential operational hours.
> 3. **Modeling Impact:** When implementing this in OpenUBEM, ensure that the peak design Lighting Power Density (LPD) is matched with this specific pre-scaled schedule, or if you normalize the schedule to a peak of 1.0, you must scale down the peak LPD by multiplying it by **0.18106** to preserve correct energy EUI.

---

### C. Equipment (Plug and Process Loads)
* **Source Object Name:** `EQP_APT_SCH`
* **Source Files:**
  * [MidriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/MidriseApartment_90.1-2013.idf)
  * [HighriseApartment_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/HighriseApartment_90.1-2013.idf)
* **Annual EFLH (Equipment):** **5,763.35 hours**
* **Daily EFLH:** **15.79 hours/day** (applied to Weekdays, Saturdays, and Sundays)

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **All Days** (Weekday, Saturday, Sunday) | 01:00 | 0.45000 |
| | 02:00 | 0.41000 |
| | 03:00 | 0.39000 |
| | 05:00 | 0.38000 |
| | 06:00 | 0.43000 |
| | 07:00 | 0.54000 |
| | 08:00 | 0.65000 |
| | 09:00 | 0.66000 |
| | 10:00 | 0.67000 |
| | 11:00 | 0.69000 |
| | 12:00 | 0.70000 |
| | 13:00 | 0.69000 |
| | 14:00 | 0.66000 |
| | 15:00 | 0.65000 |
| | 16:00 | 0.68000 |
| | 17:00 | 0.80000 |
| | 19:00 | 1.00000 |
| | 20:00 | 0.93000 |
| | 21:00 | 0.89000 |
| | 22:00 | 0.85000 |
| | 23:00 | 0.71000 |
| | 24:00 | 0.58000 |

*Note: In the prototype IDF, `EQP_APT_SCH` uses the `For: AllDays` field type, indicating the same schedule is applied across all day-types.*

---
---

## 2. SmallHotel & LargeHotel (Guest-Room Zones)

Lodging models differentiate between guest rooms and common areas (lobbies, corridors). The tables below represent the dominant **Guest-Room** profile.

### A. Occupancy (Guest Rooms)
* **Source Object Name:** `GuestRoom_Occ_Sch`
* **Source Files:**
  * [SmallHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/SmallHotel_90.1-2013.idf)
  * [LargeHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/LargeHotel_90.1-2013.idf)
* **Source File URLs:**
  * [ASHRAE901_HotelSmall_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelSmall_STD2013.zip)
  * [ASHRAE901_HotelLarge_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelLarge_STD2013.zip)
* **Annual EFLH (Occupancy):** **5,515.23 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 06:00 | 1.00000 |
| | 07:00 | 0.77000 |
| | 09:00 | 0.43000 |
| | 15:00 | 0.20000 |
| | 16:00 | 0.31000 |
| | 19:00 | 0.54000 |
| | 21:00 | 0.77000 |
| | 22:00 | 0.89000 |
| | 24:00 | 1.00000 |
| **Saturday** | 06:00 | 1.00000 |
| | 07:00 | 0.77000 |
| | 09:00 | 0.53000 |
| | 17:00 | 0.30000 |
| | 18:00 | 0.53000 |
| | 19:00 | 0.54000 |
| | 21:00 | 0.65000 |
| | 24:00 | 0.77000 |
| **Sunday / Holidays** | 06:00 | 1.00000 |
| | 07:00 | 0.77000 |
| | 09:00 | 0.53000 |
| | 17:00 | 0.30000 |
| | 18:00 | 0.53000 |
| | 19:00 | 0.54000 |
| | 21:00 | 0.65000 |
| | 24:00 | 0.77000 |

*Note: The prototype IDF applies `For: Weekdays` and `For: Saturday Sunday Holidays` for this schedule.*

---

### B. Lighting (Guest Rooms)
* **Source Object Name:** `ltg_sch_guestroom`
* **Source Files:**
  * [SmallHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/SmallHotel_90.1-2013.idf)
  * [LargeHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/LargeHotel_90.1-2013.idf)
* **Annual EFLH (Lighting):** **1,978.92 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 01:00 | 0.12100 |
| | 02:00 | 0.09350 |
| | 05:00 | 0.06050 |
| | 06:00 | 0.12100 |
| | 07:00 | 0.24200 |
| | 08:00 | 0.30800 |
| | 10:00 | 0.24200 |
| | 18:00 | 0.15400 |
| | 19:00 | 0.36850 |
| | 20:00 | 0.48950 |
| | 21:00 | 0.55000 |
| | 22:00 | 0.48950 |
| | 23:00 | 0.36850 |
| | 24:00 | 0.18150 |
| **Saturday** | 02:00 | 0.14300 |
| | 06:00 | 0.06050 |
| | 08:00 | 0.22550 |
| | 10:00 | 0.30800 |
| | 11:00 | 0.22550 |
| | 18:00 | 0.18150 |
| | 19:00 | 0.46750 |
| | 22:00 | 0.55000 |
| | 23:00 | 0.46750 |
| | 24:00 | 0.22550 |
| **Sunday / AllOtherDays** | 02:00 | 0.14300 |
| | 06:00 | 0.06050 |
| | 08:00 | 0.22550 |
| | 10:00 | 0.30800 |
| | 11:00 | 0.22550 |
| | 18:00 | 0.18150 |
| | 19:00 | 0.46750 |
| | 22:00 | 0.55000 |
| | 23:00 | 0.46750 |
| | 24:00 | 0.22550 |

*Note: The prototype IDF applies `For: Weekdays`, `For: Saturday`, and `For: AllOtherDays` (Sunday) for this schedule.*

---

### C. Equipment (Guest Rooms)
* **Description:** SmallHotel and LargeHotel use different equipment schedules. Specifically, the base plug/equipment load fraction during unoccupied sleeping hours (23:00 to 06:00) is **0.09** in SmallHotel, but **0.17** in LargeHotel. Both tables are detailed below.
* **Source Object Name:** `GuestRoom_Eqp_Sch_Adva` (spelled exactly as `GuestRoom_Eqp_Sch_Adva` in the IDF database)

#### C1. SmallHotel Equipment (`GuestRoom_Eqp_Sch_Adva`)
* **Source File:** [SmallHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/SmallHotel_90.1-2013.idf)
* **Annual EFLH (Equipment - SmallHotel):** **2,557.59 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 06:00 | 0.09000 |
| | 07:00 | 0.62000 |
| | 08:00 | 0.90000 |
| | 10:00 | 0.43000 |
| | 16:00 | 0.12000 |
| | 17:00 | 0.19000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.09000 |
| **Saturday** | 06:00 | 0.09000 |
| | 07:00 | 0.30000 |
| | 08:00 | 0.62000 |
| | 09:00 | 0.90000 |
| | 10:00 | 0.62000 |
| | 16:00 | 0.13000 |
| | 17:00 | 0.21000 |
| | 18:00 | 0.40000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.09000 |
| **Sunday / Holidays** | 06:00 | 0.09000 |
| | 07:00 | 0.30000 |
| | 08:00 | 0.62000 |
| | 09:00 | 0.90000 |
| | 10:00 | 0.62000 |
| | 16:00 | 0.13000 |
| | 17:00 | 0.21000 |
| | 18:00 | 0.40000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.09000 |

#### C2. LargeHotel Equipment (`GuestRoom_Eqp_Sch_Adva`)
* **Source File:** [LargeHotel_90.1-2013.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/LargeHotel_90.1-2013.idf)
* **Annual EFLH (Equipment - LargeHotel):** **2,761.99 hours**

| Day-type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| **Weekday** | 06:00 | 0.17000 |
| | 07:00 | 0.62000 |
| | 08:00 | 0.90000 |
| | 10:00 | 0.43000 |
| | 16:00 | 0.12000 |
| | 17:00 | 0.19000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.17000 |
| **Saturday** | 06:00 | 0.17000 |
| | 07:00 | 0.30000 |
| | 08:00 | 0.62000 |
| | 09:00 | 0.90000 |
| | 10:00 | 0.62000 |
| | 16:00 | 0.13000 |
| | 17:00 | 0.21000 |
| | 18:00 | 0.40000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.17000 |
| **Sunday / Holidays** | 06:00 | 0.17000 |
| | 07:00 | 0.30000 |
| | 08:00 | 0.62000 |
| | 09:00 | 0.90000 |
| | 10:00 | 0.62000 |
| | 16:00 | 0.13000 |
| | 17:00 | 0.21000 |
| | 18:00 | 0.40000 |
| | 19:00 | 0.48000 |
| | 20:00 | 0.46000 |
| | 21:00 | 0.62000 |
| | 22:00 | 0.69000 |
| | 23:00 | 0.34000 |
| | 24:00 | 0.17000 |

---
---

## 3. Reference Citation Block

* **Title:** Commercial Prototype Building Models (ASHRAE Standard 90.1-2013 edition)
* **Author / Agency:** Pacific Northwest National Laboratory (PNNL) / U.S. Department of Energy (DOE) Building Energy Codes Program
* **Standard Edition:** ANSI/ASHRAE/IES Standard 90.1-2013
* **Repository / URLs:**
  * MidriseApartment: [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentMidRise_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentMidRise_STD2013.zip)
  * HighriseApartment: [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentHighRise_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_ApartmentHighRise_STD2013.zip)
  * SmallHotel: [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelSmall_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelSmall_STD2013.zip)
  * LargeHotel: [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelLarge_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_HotelLarge_STD2013.zip)
* **Access Date:** June 17, 2026
* **License:** Public Domain / BSD-3 (open-source redistribution permitted)

---

## 4. Discrepancy & Difference Analysis

### A. MidriseApartment vs. HighriseApartment
**Verdict:** **Identical**.
MidriseApartment and HighriseApartment archetypes share the exact same underlying schedule shapes and values for dwelling units. 
* Occupancy is split identically between `OCC_APT_SCH_WORKING_FAMILY` and `OCC_APT_SCH_STAY_HOME_FAMILY`.
* Lighting uses the identical hardwired/plugin profiles `ltg_sch_apartment_hardwired`.
* Equipment uses the identical `EQP_APT_SCH` plug load profile.

### B. SmallHotel vs. LargeHotel
**Verdict:** **Materially different in equipment schedules**.
* **Occupancy (`GuestRoom_Occ_Sch`):** Identical. Both hotels utilize the same occupancy pattern for guest rooms, with identical Weekday, Saturday, and Sunday profiles (Annual Occupancy EFLH = 5,515.23 hours).
* **Lighting (`ltg_sch_guestroom`):** Identical. Both hotels utilize the same guest room lighting pattern (Annual Lighting EFLH = 1,978.92 hours).
* **Equipment (`GuestRoom_Eqp_Sch_Adva`):** **DIFFERENT**. 
  * The SmallHotel guest-room equipment schedule has a minimum base load fraction of **0.09** (9% of peak) during unoccupied sleeping hours (23:00 to 06:00).
  * The LargeHotel guest-room equipment schedule has a minimum base load fraction of **0.17** (17% of peak) during those same hours.
  * This difference results in a **7.9% higher annual EFLH** for LargeHotel equipment (2,761.99 hours vs. 2,557.59 hours for SmallHotel).

### C. Zone-Specific Naming and Applicability
In both hotel models:
* The schedules presented above (`GuestRoom_Occ_Sch`, `ltg_sch_guestroom`, and `GuestRoom_Eqp_Sch_Adva`) are applied strictly to **Guest-Room zones** (representing the dominant floor area of the building).
* Common zones such as the Lobby, Office, Corridor, Laundry, and Restrooms use distinct, separate schedule shapes tailored to those space types (e.g., `Lobby_Occ_Sch`, `ltg_sch_lobby`, `ltg_sch_office`, `ltg_sch_corridor`), which are not to be confused with the private guest room profiles.\n