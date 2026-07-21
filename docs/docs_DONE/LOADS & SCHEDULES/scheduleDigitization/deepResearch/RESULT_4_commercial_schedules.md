# Verbatim DOE Prototype Schedules: Commercial Day-Operation

This report documents the verbatim fractional operating schedules (Occupancy, Lighting, and Plug/Process Equipment) for day-operation commercial building types (Office, Retail, Warehouse, Supermarket) from the U.S. DOE Commercial Prototype Building Models (ASHRAE 90.1-2013).

All schedule values have been transcribed directly from the verified primary source files of the Pacific Northwest National Laboratory (PNNL) Transactive Energy Simulation Platform (TESP) repository, which hosts the canonical DOE prototype EnergyPlus input data files (`.idf`).

---

## 1. MediumOffice (and LargeOffice / SmallOffice comparison)

*   **LargeOffice Comparison**: Programmatic comparison confirms that the schedule shapes for **LargeOffice** are **100% identical** to those of **MediumOffice** (same fractional values and time breakpoints).
*   **SmallOffice Comparison**: The schedules for **SmallOffice** are **not identical** to MediumOffice. SmallOffice features slightly shorter operating profiles (e.g. steeper ramp-downs in the evening and Saturday afternoon). Its profiles are detailed below in a separate section.

### MediumOffice / LargeOffice Occupancy Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 06:00 | 0.00 |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.20 |
| Weekday | 12:00 | 0.95 |
| Weekday | 13:00 | 0.50 |
| Weekday | 17:00 | 0.95 |
| Weekday | 18:00 | 0.70 |
| Weekday | 20:00 | 0.40 |
| Weekday | 22:00 | 0.10 |
| Weekday | 24:00 | 0.05 |
| Saturday | 06:00 | 0.00 |
| Saturday | 08:00 | 0.10 |
| Saturday | 14:00 | 0.50 |
| Saturday | 17:00 | 0.10 |
| Saturday | 24:00 | 0.00 |
| Sunday & All Other Days | 24:00 | 0.00 |

**Source Object**: `BLDG_OCC_SCH`  
**Source File**: [MediumOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/MediumOffice.idf) / [LargeOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/LargeOffice.idf)  
**Annual EFLH**: 2,844.20 hours  

### MediumOffice / LargeOffice Lighting Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 05:00 | 0.05 |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.30 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.70 |
| Weekday | 20:00 | 0.50 |
| Weekday | 22:00 | 0.30 |
| Weekday | 23:00 | 0.10 |
| Weekday | 24:00 | 0.05 |
| Saturday | 06:00 | 0.05 |
| Saturday | 08:00 | 0.10 |
| Saturday | 14:00 | 0.50 |
| Saturday | 17:00 | 0.15 |
| Saturday | 24:00 | 0.05 |
| Sunday & All Other Days | 24:00 | 0.05 |

**Source Object**: `BLDG_LIGHT_SCH`  
**Source File**: [MediumOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/MediumOffice.idf) / [LargeOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/LargeOffice.idf)  
**Annual EFLH**: 3,235.30 hours  

### MediumOffice / LargeOffice Equipment Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 08:00 | 0.40 |
| Weekday | 12:00 | 0.90 |
| Weekday | 13:00 | 0.80 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.80 |
| Weekday | 20:00 | 0.60 |
| Weekday | 22:00 | 0.50 |
| Weekday | 24:00 | 0.40 |
| Saturday | 06:00 | 0.30 |
| Saturday | 08:00 | 0.40 |
| Saturday | 14:00 | 0.50 |
| Saturday | 17:00 | 0.35 |
| Saturday | 24:00 | 0.30 |
| Sunday & All Other Days | 24:00 | 0.30 |

**Source Object**: `BLDG_EQUIP_SCH`  
**Source File**: [MediumOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/MediumOffice.idf) / [LargeOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/LargeOffice.idf)  
**Annual EFLH**: 4,744.40 hours  

---

## 2. SmallOffice

Schedules in SmallOffice differ slightly from MediumOffice. In particular, it features steeper ramp-downs in the evening on weekdays (e.g. lighting goes to 0.5 at 18:00 instead of 0.7) and shorter Saturday profiles.

### SmallOffice Occupancy Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 06:00 | 0.00 |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.20 |
| Weekday | 12:00 | 0.95 |
| Weekday | 13:00 | 0.50 |
| Weekday | 17:00 | 0.95 |
| Weekday | 18:00 | 0.30 |
| Weekday | 20:00 | 0.10 |
| Weekday | 24:00 | 0.05 |
| Saturday | 06:00 | 0.00 |
| Saturday | 08:00 | 0.10 |
| Saturday | 12:00 | 0.30 |
| Saturday | 17:00 | 0.10 |
| Saturday | 24:00 | 0.00 |
| Sunday & All Other Days | 24:00 | 0.00 |

**Source Object**: `BLDG_OCC_SCH`  
**Source File**: [SmallOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SmallOffice.idf)  
**Annual EFLH**: 2,473.90 hours  

### SmallOffice Lighting Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 05:00 | 0.05 |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.30 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.50 |
| Weekday | 20:00 | 0.30 |
| Weekday | 22:00 | 0.20 |
| Weekday | 23:00 | 0.10 |
| Weekday | 24:00 | 0.05 |
| Saturday | 06:00 | 0.05 |
| Saturday | 08:00 | 0.10 |
| Saturday | 12:00 | 0.30 |
| Saturday | 17:00 | 0.15 |
| Saturday | 24:00 | 0.05 |
| Sunday & All Other Days | 24:00 | 0.05 |

**Source Object**: `BLDG_LIGHT_SCH`  
**Source File**: [SmallOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SmallOffice.idf)  
**Annual EFLH**: 2,948.50 hours  

### SmallOffice Equipment Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 08:00 | 0.40 |
| Weekday | 12:00 | 0.90 |
| Weekday | 13:00 | 0.80 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.50 |
| Weekday | 24:00 | 0.40 |
| Saturday | 06:00 | 0.30 |
| Saturday | 08:00 | 0.40 |
| Saturday | 12:00 | 0.50 |
| Saturday | 17:00 | 0.35 |
| Saturday | 24:00 | 0.30 |
| Sunday & All Other Days | 24:00 | 0.30 |

**Source Object**: `BLDG_EQUIP_SCH`  
**Source File**: [SmallOffice.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SmallOffice.idf)  
**Annual EFLH**: 4,493.90 hours  

---

## 3. RetailStandalone (and RetailStripmall)

*   **RetailStripmall Comparison**: Programmatic comparison confirms that the schedule shapes for **RetailStripmall** are **identical** to **RetailStandalone** (the exact same hourly fractional values and breakpoints). The only minor difference is the day-type label in the Sunday block (`Sunday Holidays AllOtherDays` in StripMall vs `AllOtherDays` in StandaloneRetail).

### RetailStandalone / RetailStripmall Occupancy Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.00 |
| Weekday | 08:00 | 0.10 |
| Weekday | 09:00 | 0.20 |
| Weekday | 11:00 | 0.50 |
| Weekday | 15:00 | 0.70 |
| Weekday | 16:00 | 0.80 |
| Weekday | 17:00 | 0.70 |
| Weekday | 19:00 | 0.50 |
| Weekday | 21:00 | 0.30 |
| Weekday | 24:00 | 0.00 |
| Saturday | 07:00 | 0.00 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.20 |
| Saturday | 10:00 | 0.50 |
| Saturday | 11:00 | 0.60 |
| Saturday | 17:00 | 0.80 |
| Saturday | 18:00 | 0.60 |
| Saturday | 21:00 | 0.20 |
| Saturday | 22:00 | 0.10 |
| Saturday | 24:00 | 0.00 |
| Sunday & All Other Days | 09:00 | 0.00 |
| Sunday & All Other Days | 10:00 | 0.10 |
| Sunday & All Other Days | 12:00 | 0.20 |
| Sunday & All Other Days | 17:00 | 0.40 |
| Sunday & All Other Days | 18:00 | 0.20 |
| Sunday & All Other Days | 19:00 | 0.10 |
| Sunday & All Other Days | 24:00 | 0.00 |

**Source Object**: `BLDG_OCC_SCH`  
**Source File**: [StandaloneRetail.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StandaloneRetail.idf) / [StripMall.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StripMall.idf)  
**Annual EFLH**: 2,414.80 hours  

### RetailStandalone / RetailStripmall Lighting Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.05 |
| Weekday | 08:00 | 0.20 |
| Weekday | 09:00 | 0.50 |
| Weekday | 18:00 | 0.90 |
| Weekday | 20:00 | 0.60 |
| Weekday | 21:00 | 0.50 |
| Weekday | 22:00 | 0.20 |
| Weekday | 24:00 | 0.05 |
| Saturday | 07:00 | 0.05 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.30 |
| Saturday | 10:00 | 0.60 |
| Saturday | 18:00 | 0.90 |
| Saturday | 19:00 | 0.50 |
| Saturday | 21:00 | 0.30 |
| Saturday | 22:00 | 0.10 |
| Saturday | 24:00 | 0.05 |
| Sunday & All Other Days | 08:00 | 0.05 |
| Sunday & All Other Days | 10:00 | 0.10 |
| Sunday & All Other Days | 12:00 | 0.40 |
| Sunday & All Other Days | 17:00 | 0.60 |
| Sunday & All Other Days | 18:00 | 0.40 |
| Sunday & All Other Days | 19:00 | 0.20 |
| Sunday & All Other Days | 24:00 | 0.05 |

**Source Object**: `BLDG_LIGHT_SCH`  
**Source File**: [StandaloneRetail.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StandaloneRetail.idf) / [StripMall.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StripMall.idf)  
**Annual EFLH**: 3,695.35 hours  

### RetailStandalone / RetailStripmall Equipment Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.20 |
| Weekday | 08:00 | 0.40 |
| Weekday | 09:00 | 0.70 |
| Weekday | 18:00 | 0.90 |
| Weekday | 20:00 | 0.80 |
| Weekday | 21:00 | 0.70 |
| Weekday | 22:00 | 0.40 |
| Weekday | 24:00 | 0.20 |
| Saturday | 07:00 | 0.15 |
| Saturday | 08:00 | 0.30 |
| Saturday | 09:00 | 0.50 |
| Saturday | 10:00 | 0.80 |
| Saturday | 18:00 | 0.90 |
| Saturday | 19:00 | 0.70 |
| Saturday | 21:00 | 0.50 |
| Saturday | 22:00 | 0.30 |
| Saturday | 24:00 | 0.15 |
| Sunday & All Other Days | 08:00 | 0.15 |
| Sunday & All Other Days | 10:00 | 0.30 |
| Sunday & All Other Days | 12:00 | 0.60 |
| Sunday & All Other Days | 17:00 | 0.80 |
| Sunday & All Other Days | 18:00 | 0.60 |
| Sunday & All Other Days | 19:00 | 0.40 |
| Sunday & All Other Days | 24:00 | 0.15 |

**Source Object**: `BLDG_EQUIP_SCH`  
**Source File**: [StandaloneRetail.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StandaloneRetail.idf) / [StripMall.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/StripMall.idf)  
**Annual EFLH**: 4,662.50 hours  

---

## 4. Warehouse

In the **Warehouse** prototype:
*   The conditioned/office portion uses `BLDG_OCC_SCH` for occupancy, `BLDG_LIGHT_SCH` for lighting, and `BLDG_EQUIP_SCH` for plug equipment in the `Office` zone.
*   The bulk-storage area uses `BLDG_LIGHT_SCH` for lighting and `BLDG_EQUIP_SCH` for equipment in the `BulkStorage` zone (there is no occupancy/people object defined for storage zones).
*   Thus, both zones share the same underlying schedule objects defined below.

### Warehouse Occupancy Schedule (Office zone)
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.00 |
| Weekday | 08:00 | 0.15 |
| Weekday | 09:00 | 0.70 |
| Weekday | 12:00 | 0.90 |
| Weekday | 13:00 | 0.50 |
| Weekday | 16:00 | 0.85 |
| Weekday | 17:00 | 0.20 |
| Weekday | 24:00 | 0.00 |
| Saturday | 08:00 | 0.00 |
| Saturday | 12:00 | 0.20 |
| Saturday | 16:00 | 0.10 |
| Saturday | 24:00 | 0.00 |
| Sunday & All Other Days | 24:00 | 0.00 |

**Source Object**: `BLDG_OCC_SCH`  
**Source File**: [Warehouse.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/Warehouse.idf)  
**Annual EFLH**: 1,837.20 hours  

### Warehouse Lighting Schedule (Office, BulkStorage, & FineStorage zones)
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.40 |
| Weekday | 09:00 | 0.70 |
| Weekday | 12:00 | 0.90 |
| Weekday | 13:00 | 0.80 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.30 |
| Weekday | 24:00 | 0.10 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.10 |
| Saturday | 12:00 | 0.24 |
| Saturday | 24:00 | 0.10 |
| Sunday & All Other Days | 24:00 | 0.10 |

**Source Object**: `BLDG_LIGHT_SCH`  
**Source File**: [Warehouse.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/Warehouse.idf)  
**Annual EFLH**: 2,829.24 hours  

### Warehouse Equipment Schedule (Office & BulkStorage zones)
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 07:00 | 0.10 |
| Weekday | 08:00 | 0.50 |
| Weekday | 09:00 | 0.80 |
| Weekday | 12:00 | 0.90 |
| Weekday | 13:00 | 0.80 |
| Weekday | 17:00 | 0.90 |
| Weekday | 18:00 | 0.40 |
| Weekday | 24:00 | 0.10 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.20 |
| Saturday | 12:00 | 0.40 |
| Saturday | 24:00 | 0.10 |
| Sunday & All Other Days | 24:00 | 0.10 |

**Source Object**: `BLDG_EQUIP_SCH`  
**Source File**: [Warehouse.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/Warehouse.idf)  
**Annual EFLH**: 2,937.70 hours  

---

## 5. SuperMarket

In the **SuperMarket** prototype, all primary zones (Sales, Deli, Produce, Bakery, DryStorage, Office) use the unified `BLDG_OCC_SCH`, `BLDG_LIGHT_SCH`, and `BLDG_EQUIP_SCH` schedules.

### SuperMarket Occupancy Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 06:00 | 0.00 |
| Weekday | 08:00 | 0.10 |
| Weekday | 09:00 | 0.20 |
| Weekday | 11:00 | 0.50 |
| Weekday | 15:00 | 0.70 |
| Weekday | 16:00 | 0.80 |
| Weekday | 17:00 | 0.70 |
| Weekday | 19:00 | 0.50 |
| Weekday | 22:00 | 0.30 |
| Weekday | 24:00 | 0.00 |
| Saturday | 06:00 | 0.00 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.20 |
| Saturday | 10:00 | 0.50 |
| Saturday | 11:00 | 0.60 |
| Saturday | 17:00 | 0.80 |
| Saturday | 18:00 | 0.60 |
| Saturday | 21:00 | 0.20 |
| Saturday | 22:00 | 0.10 |
| Saturday | 24:00 | 0.00 |
| Sunday & All Other Days | 06:00 | 0.00 |
| Sunday & All Other Days | 10:00 | 0.10 |
| Sunday & All Other Days | 12:00 | 0.20 |
| Sunday & All Other Days | 17:00 | 0.40 |
| Sunday & All Other Days | 18:00 | 0.20 |
| Sunday & All Other Days | 22:00 | 0.10 |
| Sunday & All Other Days | 24:00 | 0.00 |

**Source Object**: `BLDG_OCC_SCH`  
**Source File**: [SuperMarket.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SuperMarket.idf)  
**Annual EFLH**: 2,555.60 hours  

### SuperMarket Lighting Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 06:00 | 0.05 |
| Weekday | 08:00 | 0.20 |
| Weekday | 09:00 | 0.50 |
| Weekday | 18:00 | 0.90 |
| Weekday | 20:00 | 0.60 |
| Weekday | 21:00 | 0.50 |
| Weekday | 22:00 | 0.20 |
| Weekday | 24:00 | 0.05 |
| Saturday | 06:00 | 0.05 |
| Saturday | 08:00 | 0.10 |
| Saturday | 09:00 | 0.30 |
| Saturday | 10:00 | 0.60 |
| Saturday | 18:00 | 0.90 |
| Saturday | 19:00 | 0.50 |
| Saturday | 21:00 | 0.30 |
| Saturday | 22:00 | 0.10 |
| Saturday | 24:00 | 0.05 |
| Sunday & All Other Days | 06:00 | 0.05 |
| Sunday & All Other Days | 10:00 | 0.10 |
| Sunday & All Other Days | 12:00 | 0.40 |
| Sunday & All Other Days | 17:00 | 0.60 |
| Sunday & All Other Days | 18:00 | 0.40 |
| Sunday & All Other Days | 22:00 | 0.20 |
| Sunday & All Other Days | 24:00 | 0.05 |

**Source Object**: `BLDG_LIGHT_SCH`  
**Source File**: [SuperMarket.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SuperMarket.idf)  
**Annual EFLH**: 3,765.70 hours  

### SuperMarket Equipment Schedule
| Day-Type | Until HH:MM | Fraction |
| :--- | :--- | :--- |
| Weekday | 06:00 | 0.20 |
| Weekday | 08:00 | 0.40 |
| Weekday | 09:00 | 0.70 |
| Weekday | 18:00 | 0.90 |
| Weekday | 20:00 | 0.80 |
| Weekday | 21:00 | 0.70 |
| Weekday | 22:00 | 0.40 |
| Weekday | 24:00 | 0.20 |
| Saturday | 06:00 | 0.15 |
| Saturday | 08:00 | 0.30 |
| Saturday | 09:00 | 0.50 |
| Saturday | 10:00 | 0.80 |
| Saturday | 18:00 | 0.90 |
| Saturday | 19:00 | 0.70 |
| Saturday | 21:00 | 0.50 |
| Saturday | 22:00 | 0.30 |
| Saturday | 24:00 | 0.15 |
| Sunday & All Other Days | 06:00 | 0.15 |
| Sunday & All Other Days | 10:00 | 0.30 |
| Sunday & All Other Days | 12:00 | 0.60 |
| Sunday & All Other Days | 17:00 | 0.80 |
| Sunday & All Other Days | 18:00 | 0.60 |
| Sunday & All Other Days | 22:00 | 0.40 |
| Sunday & All Other Days | 24:00 | 0.15 |

**Source Object**: `BLDG_EQUIP_SCH`  
**Source File**: [SuperMarket.idf](https://github.com/pnnl/tesp/blob/main/data/energyplus/SuperMarket.idf)  
**Annual EFLH**: 4,777.10 hours  

---

## 6. Citation

*   **Title**: U.S. Department of Energy (DOE) Commercial Prototype Building Models
*   **Agency**: Pacific Northwest National Laboratory (PNNL) & National Renewable Energy Laboratory (NREL)
*   **Standard Edition**: ANSI/ASHRAE/IES Standard 90.1-2013
*   **Repository URL**: [https://github.com/pnnl/tesp/tree/main/data/energyplus](https://github.com/pnnl/tesp/tree/main/data/energyplus)
*   **License**: BSD 3-Clause License (Copyright (c) 2017-2025, Battelle Memorial Institute)
*   **Access Date**: 2026-06-17

---

## 7. SuperMarket vs. RetailStandalone Comparison

### Does SuperMarket use materially longer operating hours / higher EFLH than RetailStandalone?

**Yes**, the DOE prototypes model SuperMarket with **longer daily operating hours**, but the resulting **annual EFLH values are only marginally higher**.

#### 1. Comparison of Operating Hours (Daily Duration)
*   **SuperMarket**: Operates from **06:00 to 22:00** every day (including Sundays and Holidays). This constitutes a **16-hour daily active profile**.
*   **RetailStandalone**: Operates from **07:00 to 21:00** on weekdays/Saturdays (**14-hour daily active profile**) and **08:00 to 19:00** on Sundays/Holidays (**11-hour daily active profile**).
*   **Delta**: SuperMarket is scheduled to be open for **2 additional hours** on weekdays/Saturdays and **5 additional hours** on Sundays compared to StandaloneRetail.

#### 2. Comparison of Annual EFLH (Equivalent Full-Load Hours)
Despite the longer schedule duration, the annual EFLH is only slightly higher in SuperMarket. This is because during the early morning (06:00-07:00/08:00) and late evening (21:00-22:00) hours, the fractional loads are set to low idle/startup values (e.g. occupancy 0.10, lighting 0.20, equipment 0.40).

The computed annual EFLH comparison is:
*   **Occupancy (`BLDG_OCC_SCH`)**:
    *   SuperMarket: **2,555.60** annual EFLH
    *   RetailStandalone: **2,414.80** annual EFLH
    *   *Delta*: **+140.80 hours (+5.8%)**
*   **Lighting (`BLDG_LIGHT_SCH`)**:
    *   SuperMarket: **3,765.70** annual EFLH
    *   RetailStandalone: **3,695.35** annual EFLH
    *   *Delta*: **+70.35 hours (+1.9%)**
*   **Equipment (`BLDG_EQUIP_SCH`)**:
    *   SuperMarket: **4,777.10** annual EFLH
    *   RetailStandalone: **4,662.50** annual EFLH
    *   *Delta*: **+114.60 hours (+2.5%)**

#### 3. Key Modeling Note (Refrigeration)
It is important to note that **refrigeration compressors and cases** (which constitute the primary energy end-use in supermarkets and run 24/7) are **not** represented in the plug/process load equipment schedule (`BLDG_EQUIP_SCH`). In EnergyPlus, refrigeration systems are simulated using specialized `Refrigeration:System` and `Refrigeration:Case` objects which have their own constant 24/7 operational controls. This explains why the plug equipment schedule (`BLDG_EQUIP_SCH`) for SuperMarket has an annual EFLH (+2.5% delta) very close to that of a typical RetailStandalone building.
