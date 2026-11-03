# RESULT_3_foodservice_schedules — Verbatim DOE prototype schedules: Food Service

This report provides the verbatim fractional operating schedules for occupancy, lighting, and plug/process equipment (electric and gas cooking) for **Full-Service Restaurant** and **Quick-Service Restaurant** archetypes. The data is transcribed directly from the U.S. DOE Commercial Prototype Building Models (ASHRAE Standard 90.1-2013 edition), as implemented by Pacific Northwest National Laboratory (PNNL) and NREL.

In the DOE prototype building models:
* **Full-Service Restaurant (FSR)** is represented by the **SitDown** prototype.
* **Quick-Service Restaurant (QSR)** is represented by the **FastFood** prototype.

Both models differentiate between the **Dining** and **Kitchen** zones, applying distinct lighting and cooking equipment schedules.

---

## 1. Full-Service Restaurant (FullServiceRestaurant / RestaurantSitDown)

### A. Occupancy (Dining & Kitchen Areas)
* **Description:** Both the Dining and Kitchen zones in the Full-Service Restaurant prototype utilize the same occupancy schedule.
* **Source Object Name:** `BLDG_OCC_SCH`
* **Source File:** [Restaurant_FullServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_FullServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantSitDown_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantSitDown_STD2013.zip)
* **Annual EFLH (Occupancy):** **2,962.00 hours**

| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.05000 |
| Weekday | 05:00 | 0.00000 |
| Weekday | 06:00 | 0.05000 |
| Weekday | 07:00 | 0.10000 |
| Weekday | 10:00 | 0.40000 |
| Weekday | 11:00 | 0.20000 |
| Weekday | 12:00 | 0.50000 |
| Weekday | 13:00 | 0.80000 |
| Weekday | 14:00 | 0.70000 |
| Weekday | 15:00 | 0.40000 |
| Weekday | 16:00 | 0.20000 |
| Weekday | 17:00 | 0.25000 |
| Weekday | 18:00 | 0.50000 |
| Weekday | 21:00 | 0.80000 |
| Weekday | 22:00 | 0.50000 |
| Weekday | 23:00 | 0.35000 |
| Weekday | 24:00 | 0.20000 |
| Saturday | 01:00 | 0.05000 |
| Saturday | 06:00 | 0.00000 |
| Saturday | 07:00 | 0.05000 |
| Saturday | 09:00 | 0.50000 |
| Saturday | 10:00 | 0.40000 |
| Saturday | 11:00 | 0.20000 |
| Saturday | 12:00 | 0.45000 |
| Saturday | 14:00 | 0.50000 |
| Saturday | 15:00 | 0.35000 |
| Saturday | 18:00 | 0.30000 |
| Saturday | 19:00 | 0.70000 |
| Saturday | 20:00 | 0.90000 |
| Saturday | 21:00 | 0.70000 |
| Saturday | 22:00 | 0.65000 |
| Saturday | 23:00 | 0.55000 |
| Saturday | 24:00 | 0.35000 |
| Sunday | 01:00 | 0.05000 |
| Sunday | 06:00 | 0.00000 |
| Sunday | 07:00 | 0.05000 |
| Sunday | 09:00 | 0.50000 |
| Sunday | 11:00 | 0.20000 |
| Sunday | 12:00 | 0.30000 |
| Sunday | 14:00 | 0.50000 |
| Sunday | 15:00 | 0.30000 |
| Sunday | 16:00 | 0.20000 |
| Sunday | 17:00 | 0.25000 |
| Sunday | 18:00 | 0.35000 |
| Sunday | 19:00 | 0.55000 |
| Sunday | 20:00 | 0.65000 |
| Sunday | 21:00 | 0.70000 |
| Sunday | 22:00 | 0.35000 |
| Sunday | 24:00 | 0.20000 |

*Note: In the EnergyPlus prototype, the "Sunday" table applies to "Sunday", "Holidays", and "AllOtherDays" types.*

---

### B. Lighting
* **Description:** The Dining and Kitchen areas use different lighting schedule shapes. The tables below show both.
* **Dining Area Lighting Schedule:**
  * **Source Object Name:** `ltg_sch_dining`
  * **Annual EFLH (Dining Lighting):** **4,829.64 hours**
* **Kitchen Area Lighting Schedule:**
  * **Source Object Name:** `ltg_sch_kitchen`
  * **Annual EFLH (Kitchen Lighting):** **3,960.95 hours**
* **Source File:** [Restaurant_FullServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_FullServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantSitDown_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantSitDown_STD2013.zip)

#### Table B1: Dining Area Lighting (`ltg_sch_dining`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 05:00 | 0.14241 |
| Weekday | 06:00 | 0.18988 |
| Weekday | 08:00 | 0.37975 |
| Weekday | 10:00 | 0.56963 |
| Weekday | 22:00 | 0.85444 |
| Weekday | 23:00 | 0.47469 |
| Weekday | 24:00 | 0.28481 |
| Saturday | 01:00 | 0.18988 |
| Saturday | 06:00 | 0.14241 |
| Saturday | 08:00 | 0.28481 |
| Saturday | 10:00 | 0.56963 |
| Saturday | 17:00 | 0.75951 |
| Saturday | 22:00 | 0.85444 |
| Saturday | 23:00 | 0.47469 |
| Saturday | 24:00 | 0.28481 |
| Sunday | 01:00 | 0.18988 |
| Sunday | 06:00 | 0.14241 |
| Sunday | 08:00 | 0.28481 |
| Sunday | 10:00 | 0.47469 |
| Sunday | 16:00 | 0.66457 |
| Sunday | 22:00 | 0.56963 |
| Sunday | 23:00 | 0.47469 |
| Sunday | 24:00 | 0.28481 |

#### Table B2: Kitchen Area Lighting (`ltg_sch_kitchen`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 05:00 | 0.11679 |
| Weekday | 06:00 | 0.15572 |
| Weekday | 08:00 | 0.31145 |
| Weekday | 10:00 | 0.46717 |
| Weekday | 22:00 | 0.70076 |
| Weekday | 23:00 | 0.38931 |
| Weekday | 24:00 | 0.23359 |
| Saturday | 01:00 | 0.15572 |
| Saturday | 06:00 | 0.11679 |
| Saturday | 08:00 | 0.23359 |
| Saturday | 10:00 | 0.46717 |
| Saturday | 17:00 | 0.62289 |
| Saturday | 22:00 | 0.70076 |
| Saturday | 23:00 | 0.38931 |
| Saturday | 24:00 | 0.23359 |
| Sunday | 01:00 | 0.15572 |
| Sunday | 06:00 | 0.11679 |
| Sunday | 08:00 | 0.23359 |
| Sunday | 10:00 | 0.38931 |
| Sunday | 16:00 | 0.54503 |
| Sunday | 22:00 | 0.46717 |
| Sunday | 23:00 | 0.38931 |
| Sunday | 24:00 | 0.23359 |

---

### C. Equipment (Plug and Process Loads)
* **Description:** The electric equipment (misc plug loads and electric kitchen equipment) for both zones uses the `BLDG_EQUIP_SCH` schedule (with the exception of reach-in refrigeration which is `Always_on`). The gas cooking equipment uses the `Rest_GAS_EQUIP_SCH` schedule.
* **Electric Equipment Schedule:**
  * **Source Object Name:** `BLDG_EQUIP_SCH`
  * **Annual EFLH (Electric Equipment):** **1,439.83 hours**
* **Gas Cooking Equipment Schedule:**
  * **Source Object Name:** `Rest_GAS_EQUIP_SCH`
  * **Annual EFLH (Gas Cooking Equipment):** **1,441.75 hours**
* **Source File:** [Restaurant_FullServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_FullServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantSitDown_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantSitDown_STD2013.zip)

#### Table C1: Electric Equipment (`BLDG_EQUIP_SCH`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.02983 |
| Weekday | 02:00 | 0.01989 |
| Weekday | 03:00 | 0.02983 |
| Weekday | 04:00 | 0.01989 |
| Weekday | 05:00 | 0.04972 |
| Weekday | 06:00 | 0.11987 |
| Weekday | 07:00 | 0.12986 |
| Weekday | 08:00 | 0.14983 |
| Weekday | 09:00 | 0.17980 |
| Weekday | 10:00 | 0.20977 |
| Weekday | 11:00 | 0.25971 |
| Weekday | 12:00 | 0.28968 |
| Weekday | 13:00 | 0.26970 |
| Weekday | 14:00 | 0.24972 |
| Weekday | 15:00 | 0.22975 |
| Weekday | 16:00 | 0.22975 |
| Weekday | 17:00 | 0.25971 |
| Weekday | 18:00 | 0.25971 |
| Weekday | 19:00 | 0.23973 |
| Weekday | 20:00 | 0.21976 |
| Weekday | 21:00 | 0.19978 |
| Weekday | 22:00 | 0.17980 |
| Weekday | 23:00 | 0.08990 |
| Weekday | 24:00 | 0.02983 |
| Saturday | 01:00 | 0.02983 |
| Saturday | 02:00 | 0.01989 |
| Saturday | 03:00 | 0.02983 |
| Saturday | 04:00 | 0.01989 |
| Saturday | 05:00 | 0.04972 |
| Saturday | 06:00 | 0.11987 |
| Saturday | 07:00 | 0.12986 |
| Saturday | 08:00 | 0.14983 |
| Saturday | 09:00 | 0.17980 |
| Saturday | 10:00 | 0.20977 |
| Saturday | 11:00 | 0.25971 |
| Saturday | 12:00 | 0.28968 |
| Saturday | 13:00 | 0.26970 |
| Saturday | 14:00 | 0.24972 |
| Saturday | 15:00 | 0.22975 |
| Saturday | 16:00 | 0.22975 |
| Saturday | 17:00 | 0.25971 |
| Saturday | 18:00 | 0.25971 |
| Saturday | 19:00 | 0.23973 |
| Saturday | 20:00 | 0.21976 |
| Saturday | 21:00 | 0.19978 |
| Saturday | 22:00 | 0.17980 |
| Saturday | 23:00 | 0.08990 |
| Saturday | 24:00 | 0.02983 |
| Sunday | 01:00 | 0.02983 |
| Sunday | 02:00 | 0.01989 |
| Sunday | 03:00 | 0.02983 |
| Sunday | 04:00 | 0.01989 |
| Sunday | 05:00 | 0.04972 |
| Sunday | 06:00 | 0.11932 |
| Sunday | 07:00 | 0.12986 |
| Sunday | 08:00 | 0.14983 |
| Sunday | 09:00 | 0.17980 |
| Sunday | 10:00 | 0.20977 |
| Sunday | 11:00 | 0.25971 |
| Sunday | 12:00 | 0.28968 |
| Sunday | 13:00 | 0.26970 |
| Sunday | 14:00 | 0.24972 |
| Sunday | 15:00 | 0.22975 |
| Sunday | 16:00 | 0.22975 |
| Sunday | 17:00 | 0.25971 |
| Sunday | 18:00 | 0.25971 |
| Sunday | 19:00 | 0.23973 |
| Sunday | 20:00 | 0.21976 |
| Sunday | 21:00 | 0.19978 |
| Sunday | 22:00 | 0.17980 |
| Sunday | 23:00 | 0.08990 |
| Sunday | 24:00 | 0.02997 |

#### Table C2: Gas Cooking Equipment (`Rest_GAS_EQUIP_SCH`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.03000 |
| Weekday | 02:00 | 0.02000 |
| Weekday | 03:00 | 0.03000 |
| Weekday | 04:00 | 0.02000 |
| Weekday | 05:00 | 0.05000 |
| Weekday | 06:00 | 0.12000 |
| Weekday | 07:00 | 0.13000 |
| Weekday | 08:00 | 0.15000 |
| Weekday | 09:00 | 0.18000 |
| Weekday | 10:00 | 0.21000 |
| Weekday | 11:00 | 0.26000 |
| Weekday | 12:00 | 0.29000 |
| Weekday | 13:00 | 0.27000 |
| Weekday | 14:00 | 0.25000 |
| Weekday | 15:00 | 0.23000 |
| Weekday | 16:00 | 0.23000 |
| Weekday | 17:00 | 0.26000 |
| Weekday | 18:00 | 0.26000 |
| Weekday | 19:00 | 0.24000 |
| Weekday | 20:00 | 0.22000 |
| Weekday | 21:00 | 0.20000 |
| Weekday | 22:00 | 0.18000 |
| Weekday | 23:00 | 0.09000 |
| Weekday | 24:00 | 0.03000 |
| Saturday | 01:00 | 0.03000 |
| Saturday | 02:00 | 0.02000 |
| Saturday | 03:00 | 0.03000 |
| Saturday | 04:00 | 0.02000 |
| Saturday | 05:00 | 0.05000 |
| Saturday | 06:00 | 0.12000 |
| Saturday | 07:00 | 0.13000 |
| Saturday | 08:00 | 0.15000 |
| Saturday | 09:00 | 0.18000 |
| Saturday | 10:00 | 0.21000 |
| Saturday | 11:00 | 0.26000 |
| Saturday | 12:00 | 0.29000 |
| Saturday | 13:00 | 0.27000 |
| Saturday | 14:00 | 0.25000 |
| Saturday | 15:00 | 0.23000 |
| Saturday | 16:00 | 0.23000 |
| Saturday | 17:00 | 0.26000 |
| Saturday | 18:00 | 0.26000 |
| Saturday | 19:00 | 0.24000 |
| Saturday | 20:00 | 0.22000 |
| Saturday | 21:00 | 0.20000 |
| Saturday | 22:00 | 0.18000 |
| Saturday | 23:00 | 0.09000 |
| Saturday | 24:00 | 0.03000 |
| Sunday | 01:00 | 0.03000 |
| Sunday | 02:00 | 0.02000 |
| Sunday | 03:00 | 0.03000 |
| Sunday | 04:00 | 0.02000 |
| Sunday | 05:00 | 0.05000 |
| Sunday | 06:00 | 0.12000 |
| Sunday | 07:00 | 0.13000 |
| Sunday | 08:00 | 0.15000 |
| Sunday | 09:00 | 0.18000 |
| Sunday | 10:00 | 0.21000 |
| Sunday | 11:00 | 0.26000 |
| Sunday | 12:00 | 0.29000 |
| Sunday | 13:00 | 0.27000 |
| Sunday | 14:00 | 0.25000 |
| Sunday | 15:00 | 0.23000 |
| Sunday | 16:00 | 0.23000 |
| Sunday | 17:00 | 0.26000 |
| Sunday | 18:00 | 0.26000 |
| Sunday | 19:00 | 0.24000 |
| Sunday | 20:00 | 0.22000 |
| Sunday | 21:00 | 0.20000 |
| Sunday | 22:00 | 0.18000 |
| Sunday | 23:00 | 0.09000 |
| Sunday | 24:00 | 0.03000 |

---
---

## 2. Quick-Service Restaurant (QuickServiceRestaurant / RestaurantFastFood)

### A. Occupancy (Dining & Kitchen Areas)
* **Description:** Both the Dining and Kitchen zones in the Quick-Service Restaurant prototype utilize the same occupancy schedule, which is identical to the Full-Service occupancy schedule.
* **Source Object Name:** `BLDG_OCC_SCH`
* **Source File:** [Restaurant_QuickServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_QuickServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantFastFood_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantFastFood_STD2013.zip)
* **Annual EFLH (Occupancy):** **2,962.00 hours**

| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.05000 |
| Weekday | 05:00 | 0.00000 |
| Weekday | 06:00 | 0.05000 |
| Weekday | 07:00 | 0.10000 |
| Weekday | 10:00 | 0.40000 |
| Weekday | 11:00 | 0.20000 |
| Weekday | 12:00 | 0.50000 |
| Weekday | 13:00 | 0.80000 |
| Weekday | 14:00 | 0.70000 |
| Weekday | 15:00 | 0.40000 |
| Weekday | 16:00 | 0.20000 |
| Weekday | 17:00 | 0.25000 |
| Weekday | 18:00 | 0.50000 |
| Weekday | 21:00 | 0.80000 |
| Weekday | 22:00 | 0.50000 |
| Weekday | 23:00 | 0.35000 |
| Weekday | 24:00 | 0.20000 |
| Saturday | 01:00 | 0.05000 |
| Saturday | 06:00 | 0.00000 |
| Saturday | 07:00 | 0.05000 |
| Saturday | 09:00 | 0.50000 |
| Saturday | 10:00 | 0.40000 |
| Saturday | 11:00 | 0.20000 |
| Saturday | 12:00 | 0.45000 |
| Saturday | 14:00 | 0.50000 |
| Saturday | 15:00 | 0.35000 |
| Saturday | 18:00 | 0.30000 |
| Saturday | 19:00 | 0.70000 |
| Saturday | 20:00 | 0.90000 |
| Saturday | 21:00 | 0.70000 |
| Saturday | 22:00 | 0.65000 |
| Saturday | 23:00 | 0.55000 |
| Saturday | 24:00 | 0.35000 |
| Sunday | 01:00 | 0.05000 |
| Sunday | 06:00 | 0.00000 |
| Sunday | 07:00 | 0.05000 |
| Sunday | 09:00 | 0.50000 |
| Sunday | 11:00 | 0.20000 |
| Sunday | 12:00 | 0.30000 |
| Sunday | 14:00 | 0.50000 |
| Sunday | 15:00 | 0.30000 |
| Sunday | 16:00 | 0.20000 |
| Sunday | 17:00 | 0.25000 |
| Sunday | 18:00 | 0.35000 |
| Sunday | 19:00 | 0.55000 |
| Sunday | 20:00 | 0.65000 |
| Sunday | 21:00 | 0.70000 |
| Sunday | 22:00 | 0.35000 |
| Sunday | 24:00 | 0.20000 |

---

### B. Lighting
* **Description:** The Dining and Kitchen areas use different lighting schedule shapes. The tables below show both.
* **Dining Area Lighting Schedule:**
  * **Source Object Name:** `ltg_sch_dining`
  * **Annual EFLH (Dining Lighting):** **4,641.47 hours**
* **Kitchen Area Lighting Schedule:**
  * **Source Object Name:** `ltg_sch_kitchen`
  * **Annual EFLH (Kitchen Lighting):** **4,406.10 hours**
* **Source File:** [Restaurant_QuickServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_QuickServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantFastFood_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantFastFood_STD2013.zip)

#### Table B3: Dining Area Lighting (`ltg_sch_dining`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 05:00 | 0.13686 |
| Weekday | 06:00 | 0.18248 |
| Weekday | 08:00 | 0.36496 |
| Weekday | 10:00 | 0.54743 |
| Weekday | 22:00 | 0.82115 |
| Weekday | 23:00 | 0.45620 |
| Weekday | 24:00 | 0.27372 |
| Saturday | 01:00 | 0.18248 |
| Saturday | 06:00 | 0.13686 |
| Saturday | 08:00 | 0.27372 |
| Saturday | 10:00 | 0.54743 |
| Saturday | 17:00 | 0.72991 |
| Saturday | 22:00 | 0.82115 |
| Saturday | 23:00 | 0.45620 |
| Saturday | 24:00 | 0.27372 |
| Sunday | 01:00 | 0.18248 |
| Sunday | 06:00 | 0.13686 |
| Sunday | 08:00 | 0.27372 |
| Sunday | 10:00 | 0.45620 |
| Sunday | 16:00 | 0.63867 |
| Sunday | 22:00 | 0.54743 |
| Sunday | 23:00 | 0.45620 |
| Sunday | 24:00 | 0.27372 |

#### Table B4: Kitchen Area Lighting (`ltg_sch_kitchen`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 05:00 | 0.12992 |
| Weekday | 06:00 | 0.17323 |
| Weekday | 08:00 | 0.34645 |
| Weekday | 10:00 | 0.51967 |
| Weekday | 22:00 | 0.77951 |
| Weekday | 23:00 | 0.43306 |
| Weekday | 24:00 | 0.25984 |
| Saturday | 01:00 | 0.17323 |
| Saturday | 06:00 | 0.12992 |
| Saturday | 08:00 | 0.25984 |
| Saturday | 10:00 | 0.51967 |
| Saturday | 17:00 | 0.69290 |
| Saturday | 22:00 | 0.77951 |
| Saturday | 23:00 | 0.43306 |
| Saturday | 24:00 | 0.25984 |
| Sunday | 01:00 | 0.17323 |
| Sunday | 06:00 | 0.12992 |
| Sunday | 08:00 | 0.25984 |
| Sunday | 10:00 | 0.43306 |
| Sunday | 16:00 | 0.60629 |
| Sunday | 22:00 | 0.51967 |
| Sunday | 23:00 | 0.43306 |
| Sunday | 24:00 | 0.25984 |

---

### C. Equipment (Plug and Process Loads)
* **Description:** The electric equipment (misc plug loads and electric kitchen equipment) for both zones uses the `BLDG_EQUIP_SCH` schedule (with the exception of reach-in refrigeration which is `Always_on`). The gas cooking equipment uses the `FF_GAS_EQUIP_SCH` schedule.
* **Electric Equipment Schedule:**
  * **Source Object Name:** `BLDG_EQUIP_SCH`
  * **Annual EFLH (Electric Equipment):** **1,439.97 hours**
* **Gas Cooking Equipment Schedule:**
  * **Source Object Name:** `FF_GAS_EQUIP_SCH`
  * **Annual EFLH (Gas Cooking Equipment):** **1,441.75 hours**
* **Source File:** [Restaurant_QuickServiceRestaurant.idf](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/implementation/scheduleDigitization/sources/Restaurant_QuickServiceRestaurant.idf)
* **Source File URL:** [ASHRAE901_RestaurantFastFood_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantFastFood_STD2013.zip)

#### Table C3: Electric Equipment (`BLDG_EQUIP_SCH`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.02997 |
| Weekday | 02:00 | 0.01990 |
| Weekday | 03:00 | 0.02985 |
| Weekday | 04:00 | 0.01990 |
| Weekday | 05:00 | 0.04975 |
| Weekday | 06:00 | 0.11987 |
| Weekday | 07:00 | 0.12986 |
| Weekday | 08:00 | 0.14984 |
| Weekday | 09:00 | 0.17980 |
| Weekday | 10:00 | 0.20977 |
| Weekday | 11:00 | 0.25972 |
| Weekday | 12:00 | 0.28969 |
| Weekday | 13:00 | 0.26971 |
| Weekday | 14:00 | 0.24973 |
| Weekday | 15:00 | 0.22975 |
| Weekday | 16:00 | 0.22975 |
| Weekday | 17:00 | 0.25972 |
| Weekday | 18:00 | 0.25972 |
| Weekday | 19:00 | 0.23974 |
| Weekday | 20:00 | 0.21976 |
| Weekday | 21:00 | 0.19978 |
| Weekday | 22:00 | 0.17980 |
| Weekday | 23:00 | 0.08990 |
| Weekday | 24:00 | 0.02997 |
| Saturday | 01:00 | 0.02997 |
| Saturday | 02:00 | 0.01990 |
| Saturday | 03:00 | 0.02985 |
| Saturday | 04:00 | 0.01990 |
| Saturday | 05:00 | 0.04975 |
| Saturday | 06:00 | 0.11941 |
| Saturday | 07:00 | 0.12986 |
| Saturday | 08:00 | 0.14984 |
| Saturday | 09:00 | 0.17980 |
| Saturday | 10:00 | 0.20977 |
| Saturday | 11:00 | 0.25972 |
| Saturday | 12:00 | 0.28969 |
| Saturday | 13:00 | 0.26971 |
| Saturday | 14:00 | 0.24973 |
| Saturday | 15:00 | 0.22975 |
| Saturday | 16:00 | 0.22975 |
| Saturday | 17:00 | 0.25972 |
| Saturday | 18:00 | 0.25972 |
| Saturday | 19:00 | 0.23974 |
| Saturday | 20:00 | 0.21976 |
| Saturday | 21:00 | 0.19978 |
| Saturday | 22:00 | 0.17980 |
| Saturday | 23:00 | 0.08990 |
| Saturday | 24:00 | 0.02997 |
| Sunday | 01:00 | 0.02997 |
| Sunday | 02:00 | 0.01990 |
| Sunday | 03:00 | 0.02985 |
| Sunday | 04:00 | 0.01990 |
| Sunday | 05:00 | 0.04975 |
| Sunday | 06:00 | 0.11941 |
| Sunday | 07:00 | 0.12986 |
| Sunday | 08:00 | 0.14984 |
| Sunday | 09:00 | 0.17980 |
| Sunday | 10:00 | 0.20977 |
| Sunday | 11:00 | 0.25972 |
| Sunday | 12:00 | 0.28969 |
| Sunday | 13:00 | 0.26971 |
| Sunday | 14:00 | 0.24973 |
| Sunday | 15:00 | 0.22975 |
| Sunday | 16:00 | 0.22975 |
| Sunday | 17:00 | 0.25972 |
| Sunday | 18:00 | 0.25972 |
| Sunday | 19:00 | 0.23974 |
| Sunday | 20:00 | 0.21976 |
| Sunday | 21:00 | 0.19978 |
| Sunday | 22:00 | 0.17980 |
| Sunday | 23:00 | 0.08990 |
| Sunday | 24:00 | 0.02997 |

#### Table C4: Gas Cooking Equipment (`FF_GAS_EQUIP_SCH`)
| Day-type | Until HH:MM | Fraction |
|---|---|---|
| Weekday | 01:00 | 0.03000 |
| Weekday | 02:00 | 0.02000 |
| Weekday | 03:00 | 0.03000 |
| Weekday | 04:00 | 0.02000 |
| Weekday | 05:00 | 0.05000 |
| Weekday | 06:00 | 0.12000 |
| Weekday | 07:00 | 0.13000 |
| Weekday | 08:00 | 0.15000 |
| Weekday | 09:00 | 0.18000 |
| Weekday | 10:00 | 0.21000 |
| Weekday | 11:00 | 0.26000 |
| Weekday | 12:00 | 0.29000 |
| Weekday | 13:00 | 0.27000 |
| Weekday | 14:00 | 0.25000 |
| Weekday | 15:00 | 0.23000 |
| Weekday | 16:00 | 0.23000 |
| Weekday | 17:00 | 0.26000 |
| Weekday | 18:00 | 0.26000 |
| Weekday | 19:00 | 0.24000 |
| Weekday | 20:00 | 0.22000 |
| Weekday | 21:00 | 0.20000 |
| Weekday | 22:00 | 0.18000 |
| Weekday | 23:00 | 0.09000 |
| Weekday | 24:00 | 0.03000 |
| Saturday | 01:00 | 0.03000 |
| Saturday | 02:00 | 0.02000 |
| Saturday | 03:00 | 0.03000 |
| Saturday | 04:00 | 0.02000 |
| Saturday | 05:00 | 0.05000 |
| Saturday | 06:00 | 0.12000 |
| Saturday | 07:00 | 0.13000 |
| Saturday | 08:00 | 0.15000 |
| Saturday | 09:00 | 0.18000 |
| Saturday | 10:00 | 0.21000 |
| Saturday | 11:00 | 0.26000 |
| Saturday | 12:00 | 0.29000 |
| Saturday | 13:00 | 0.27000 |
| Saturday | 14:00 | 0.25000 |
| Saturday | 15:00 | 0.23000 |
| Saturday | 16:00 | 0.23000 |
| Saturday | 17:00 | 0.26000 |
| Saturday | 18:00 | 0.26000 |
| Saturday | 19:00 | 0.24000 |
| Saturday | 20:00 | 0.22000 |
| Saturday | 21:00 | 0.20000 |
| Saturday | 22:00 | 0.18000 |
| Saturday | 23:00 | 0.09000 |
| Saturday | 24:00 | 0.03000 |
| Sunday | 01:00 | 0.03000 |
| Sunday | 02:00 | 0.02000 |
| Sunday | 03:00 | 0.03000 |
| Sunday | 04:00 | 0.02000 |
| Sunday | 05:00 | 0.05000 |
| Sunday | 06:00 | 0.12000 |
| Sunday | 07:00 | 0.13000 |
| Sunday | 08:00 | 0.15000 |
| Sunday | 09:00 | 0.18000 |
| Sunday | 10:00 | 0.21000 |
| Sunday | 11:00 | 0.26000 |
| Sunday | 12:00 | 0.29000 |
| Sunday | 13:00 | 0.27000 |
| Sunday | 14:00 | 0.25000 |
| Sunday | 15:00 | 0.23000 |
| Sunday | 16:00 | 0.23000 |
| Sunday | 17:00 | 0.26000 |
| Sunday | 18:00 | 0.26000 |
| Sunday | 19:00 | 0.24000 |
| Sunday | 20:00 | 0.22000 |
| Sunday | 21:00 | 0.20000 |
| Sunday | 22:00 | 0.18000 |
| Sunday | 23:00 | 0.09000 |
| Sunday | 24:00 | 0.03000 |

---
---

## 3. Reference Citation Block

* **Title:** Commercial Prototype Building Models (ASHRAE Standard 90.1-2013 edition)
* **Author / Agency:** Pacific Northwest National Laboratory (PNNL) / U.S. Department of Energy (DOE) Building Energy Codes Program
* **Standard Edition:** ANSI/ASHRAE/IES Standard 90.1-2013
* **Repository / URL:**
  * Full-Service Restaurant (SitDown): [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantSitDown_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantSitDown_STD2013.zip)
  * Quick-Service Restaurant (FastFood): [https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantFastFood_STD2013.zip](https://www.energycodes.gov/sites/default/files/2023-10/ASHRAE901_RestaurantFastFood_STD2013.zip)
* **Access Date:** June 17, 2026
* **License:** Public Domain / BSD-3 (open-source redistribution permitted)

---

## 4. FSR-vs-QSR Difference Analysis

### Do FullServiceRestaurant (SitDown) and QuickServiceRestaurant (FastFood) use different schedule shapes in the DOE prototypes, or the same?

**Verdict:** They share the same underlying **baseline** schedule shapes, but they differ in simulated values because of different **control reduction multipliers** applied by the OpenStudio prototype building generator.

#### Detailed Analysis:
1. **Occupancy (`BLDG_OCC_SCH`):**
   * **Result:** **Identical**. Both SitDown (FSR) and FastFood (QSR) use the exact same `BLDG_OCC_SCH` schedule for occupancy in both the Dining and Kitchen zones.
   * **Weekday EFLH:** 8.40 hours.

2. **Lighting (`ltg_sch_dining` & `ltg_sch_kitchen`):**
   * **Result:** **Different simulated values, but identical baseline shapes**.
   * **Dining area lighting (`ltg_sch_dining`):** Both prototypes share the same baseline weekday shape of `[0.15, 0.20, 0.40, 0.60, 0.90, 0.50, 0.30]`. However, SitDown scales this by a control factor of **`0.949377`** (giving `0.14241`, etc.) while FastFood scales it by **`0.912400`** (giving `0.13686`, etc.).
   * **Kitchen area lighting (`ltg_sch_kitchen`):** Both share the same baseline weekday shape `[0.15, 0.20, 0.40, 0.60, 0.90, 0.50, 0.30]`. SitDown scales it by **`0.77862`** (giving `0.11679`, etc.) while FastFood scales it by **`0.86612`** (giving `0.12992`, etc.).

3. **Electric Equipment (`BLDG_EQUIP_SCH`):**
   * **Result:** **Slightly different due to controls**.
   * **Analysis:** Both prototypes share the same baseline equipment shape (Weekday values like `0.03`, `0.02`, `0.05`, `0.12`, etc.). However, different control scaling factors are applied during occupied vs. unoccupied hours:
     * In FSR (SitDown), unoccupied hours (01:00-05:00, 24:00) use a multiplier of **`0.994347`** (giving `0.02983` for `0.03`) and occupied hours use **`0.998892`** (giving `0.11987` for `0.12`).
     * In QSR (FastFood), unoccupied hours (02:00-05:00) use a multiplier of **`0.995073`** (giving `0.01990` for `0.02`) and other hours use **`0.998916`** (giving `0.02997` for `0.03`).
   * **Annual EFLH:** Practically identical (FSR = 1,439.83 hours vs. QSR = 1,439.97 hours).

4. **Gas Cooking Equipment (`Rest_GAS_EQUIP_SCH` & `FF_GAS_EQUIP_SCH`):**
   * **Result:** **Identical**. No control scaling factors are applied to the gas cooking equipment, so the schedules are identical, consisting of clean baseline numbers (e.g., peak value `0.29`, unoccupied minimum `0.02`).
   * **Annual EFLH:** 1,441.75 hours for both.
