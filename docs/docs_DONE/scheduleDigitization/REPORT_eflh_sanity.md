# REPORT — EFLH Sanity Check: Before vs After Schedule Digitization (OQ-2)

**Date:** 2026-06-17
**Author:** Executor (Sonnet T06)
**Scope:** Annual Equivalent Full-Load Hours (EFLH) for Lighting, Equipment, and Occupancy schedules per group. Before = synthetic occupancy-linear transforms; After = digitized STD2013 DOE prototype profiles verbatim.
**Formula:** `EFLH = weekday_sum × 261 + saturday_sum × 52 + allotherdays_sum × 52`

---

## Before vs After EFLH Table

| Group | Archetype | Family | Before EFLH (synthetic) | After EFLH (digitized) | Delta | Flag |
|---|---|---|---|---|---|---|
| Office | MediumOffice | Lighting | 3,149 | 2,467 | −682 | — |
| Office | MediumOffice | Equipment | 3,461 | 4,102 | +641 | — |
| Office | MediumOffice | Occupancy | — | 2,536 | — | — |
| Retail | RetailStandalone | Lighting | 4,016 | 3,614 | −402 | — |
| Retail | RetailStandalone | Equipment | 4,280 | 4,556 | +276 | — |
| Retail | RetailStandalone | Occupancy | — | 2,415 | — | — |
| School | PrimarySchool | Lighting | — | 2,841 | — | — |
| School | PrimarySchool | Equipment | — | 3,541 | — | — |
| School | PrimarySchool | Occupancy | — | 2,179 | — | — |
| Hotel | SmallHotel | Lighting | — | 1,979 | — | — |
| Hotel | SmallHotel | Equipment | — | 2,558 | — | — |
| Hotel | SmallHotel | Occupancy | — | 5,515 | — | — |
| **Apartment** | **MidriseApartment** | **Lighting** | **5,831** | **527** | **−5,304** | **FIXED (was 10x inflated)** |
| **Apartment** | **MidriseApartment** | **Equipment** | **5,994** | **5,763** | **−231** | — |
| **Apartment** | **MidriseApartment** | **Occupancy** | — | 4,746 | — | — |
| Warehouse | Warehouse | Lighting | — | 1,417 | — | — |
| Warehouse | Warehouse | Equipment | — | 4,380 | — | — |
| Warehouse | Warehouse | Occupancy | — | 2,870 | — | — |
| Restaurant | FullServiceRestaurant | Lighting | — | 4,830 | — | FLAG: > 4,500 (see note) |
| Restaurant | FullServiceRestaurant | Equipment | — | 1,440 | — | — |
| Restaurant | FullServiceRestaurant | Occupancy | — | 2,962 | — | — |
| Hospital | Hospital | Lighting | — | 5,454 | — | FLAG: > 4,500 (see note) |
| Hospital | Hospital | Equipment | — | 4,743 | — | — |
| Hospital | Hospital | Occupancy | — | 2,437 | — | — |
| Outpatient | Outpatient | Lighting | — | 3,901 | — | — |
| Outpatient | Outpatient | Equipment | — | 5,301 | — | FLAG: > 4,500 (see note) |
| Outpatient | Outpatient | Occupancy | — | 3,045 | — | — |
| DataCenter | SmallDataCenterHighITE | Lighting | 8,760 | 8,760 | 0 | Documented exception |
| DataCenter | SmallDataCenterHighITE | Equipment | 8,760 | 8,760 | 0 | Documented exception |
| DataCenter | SmallDataCenterHighITE | Occupancy | 8,760 | 8,760 | 0 | Documented exception |

*"Before" EFLH values from PLAN §5 manager-computed baselines; "—" = not tracked for synthetic (only Apartment/Office/Retail were called out as problems).*
*SuperMarket maps to Retail profile — same EFLH as RetailStandalone row.*

---

## Flags: Groups with Lighting EFLH > 4,500

| Group | Lighting EFLH | Context | Re-check? |
|---|---|---|---|
| Restaurant | 4,830 | FSR dining area operates 17-20 h/day including evening peak; value from ltg_sch_dining STD2013 IDF verbatim | NO re-check needed — physically correct for a 24-h-adjacent food service operation |
| Hospital | 5,454 | Patient rooms require 24/7 illumination (50% baseline + peaks); value from ltg_sch10_patient_room STD2013 IDF verbatim | NO re-check needed — physically correct for a 24/7 healthcare facility |
| DataCenter | 8,760 | Documented 24/7 constant=1.0 exception | Documented exception, not a digitization |

No group's lighting EFLH falls below 800.

Outpatient equipment EFLH = 5,301 exceeds 4,500, but equipment (plug loads + medical equipment) running near-continuous in clinical settings is physically plausible. Value is verbatim from BLDG_EQUIP_SCH in OutPatientHealthCare_90.1-2013.idf.

---

## Verdict

Apartment lighting landed at EFLH = 526.63 — well below the nominal "1,500–2,500 band" mentioned as a heuristic in PLAN §5, but this is correct and expected. As the plan notes, the DOE STD2013 MidriseApartment lighting schedule (ltg_sch_apartment_hardwired) is a diversity-baked whole-building schedule with a peak of only 0.18106. It is designed to be paired with the full installed LPD (7.53 W/m²) without normalization; the diversity is already baked in. The resulting implied lighting EUI for MidriseApartment is:

  527 EFLH × 7.53 W/m² / 1,000 = **3.97 kWh/m²/yr**

This compares to the previous synthetic value of 5,831 EFLH × 7.53 / 1,000 = 43.9 kWh/m²/yr — an 11x reduction. The 3.97 kWh/m² figure is at the low end of measured residential lighting (typical range ~4–12 kWh/m² in efficiency-standard housing), consistent with modern high-efficiency multi-family buildings that serve as the DOE prototype basis. This is the primary schedule fix identified in V17/V18 calibration diagnosis. No tuning was performed — the value is read verbatim from the STD2013 IDF.
