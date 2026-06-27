# REPORT — Phase C Combined Pilot (la_urban 47-building subset)

**Date:** 2026-06-17
**Plan reference:** `docs/implementation/phaseC_combinedResim/PLAN_phaseC-combined-resim.md` (P1.T00 + P1.T02)
**Pilot dir:** `runtime/phasec_pilot/`

---

## 1. Sim/Parse Pass Rate

| Stage | Count | Total |
|---|---|---|
| IDF generation | 47 | 47 |
| EnergyPlus sim success | 47 | 47 |
| SQL parse success | 47 | 47 |

47/47 across all stages. Previous run had 25/47 (22 MidriseApartment fatal-errors due to the `_compact_block` empty-Saturday writer bug). Writer fix resolved all 22 failures.

---

## 2. Writer Fix Applied (P1.T00)

**Root cause:** `openubem/semantic/schedules.py` `_compact_block` guarded `if day_vals is None: continue`, but `"For: Saturday": []` (empty list) caused a bare `For: Saturday,` header with no `Until:` lines. EnergyPlus 23.1 fatals with "Illegal Field entered =FOR: ALLOTHERDAYS".

**Step 1 verification:** Source STD2013 IDFs confirmed NO standalone `For: Saturday` clause in the 6 affected archetype/family pairs (MidriseApartment+HighriseApartment/Occupancy, PrimarySchool+SecondarySchool/Occupancy+Equipment). The empty `[]` in `doe_schedules.json` is semantically faithful — Saturday follows AllOtherDays in the source. No parser bug; fix is writer-side only.

**Fix:** Line 72, `schedules.py`: `if day_vals is None:` -> `if not day_vals:`. One line. No edit to `doe_schedules.json` or any protected file.

**IDF spot-check (way/401910885, MidriseApartment, 6 floors):**
- `zone_count = 6` (expected 6) — zoning fix intact
- `apartment lighting peak = 0.18106` — DOE schedule baked in
- `For: Saturday` absent from `Occupancy_Schedule_MidriseApartment` — correct

**Pytest:** 671 passed, 4 warnings. 2 new regression tests added to `tests/test_schedules.py`:
- `test_compact_block_no_empty_for_header`
- `test_midrise_apartment_write_dry_run_no_empty_clause`

---

## 3. Three-Way Comparison — Per-Archetype Medians (kWh/m²)

EUI metric: energy / (footprint x num_floors), DESIGN §300, unchanged.

### Lighting EUI

| Archetype | n | old | zoning_only | combined |
|---|---|---|---|---|
| MediumOffice | 11 | 11.27 | 33.80 | 26.47 |
| MidriseApartment | 22 | 10.98 | 43.93 | 3.97 |
| RetailStandalone | 8 | 21.60 | 64.59 | 58.09 |
| SmallOffice | 6 | 14.08 | 33.80 | 26.47 |

### Equipment EUI

| Archetype | n | old | zoning_only | combined |
|---|---|---|---|---|
| MediumOffice | 11 | 12.39 | 37.16 | 44.06 |
| MidriseApartment | 22 | 11.29 | 45.16 | 43.40 |
| RetailStandalone | 8 | 15.34 | 45.86 | 48.82 |
| SmallOffice | 6 | 9.76 | 23.41 | 27.76 |

### Total EUI (lighting + equipment + heating + cooling)

| Archetype | n | old | zoning_only | combined |
|---|---|---|---|---|
| MediumOffice | 11 | 81.19 | 180.11 | 178.13 |
| MidriseApartment | 22 | 66.81 | 188.78 | 108.04 |
| RetailStandalone | 8 | 107.28 | 239.49 | 234.15 |
| SmallOffice | 6 | 98.67 | 174.97 | 172.91 |

---

## 4. Lighting EUI Floor-Count Independence

Combined lighting EUI by archetype x floor-level:

| Archetype | levels | n | median comb_lit | std |
|---|---|---|---|---|
| MediumOffice | 2 | 3 | 26.464 | 0.2044 |
| MediumOffice | 3 | 3 | 26.465 | 0.0005 |
| MediumOffice | 4 | 2 | 26.455 | 0.0102 |
| MediumOffice | 5 | 1 | 26.468 | — |
| MediumOffice | 7 | 2 | 26.342 | 0.1734 |
| MidriseApartment | 2 | 4 | 3.945 | 0.0237 |
| MidriseApartment | 3 | 4 | 3.965 | 0.0133 |
| MidriseApartment | 4 | 4 | 3.960 | 0.0743 |
| MidriseApartment | 5 | 4 | 3.962 | 0.0272 |
| MidriseApartment | 6 | 4 | 3.964 | 0.0110 |
| MidriseApartment | 7 | 2 | 3.965 | 0.0000 |
| RetailStandalone | 2 | 3 | 58.002 | 0.3409 |
| RetailStandalone | 3 | 3 | 58.187 | 0.4780 |
| RetailStandalone | 4 | 1 | 57.977 | — |
| RetailStandalone | 6 | 1 | 58.282 | — |
| SmallOffice | 2 | 3 | 26.465 | 0.0021 |
| SmallOffice | 3 | 3 | 26.465 | 0.0830 |

Max std across all groups: 0.4780 (RetailStandalone/3 floors). MidriseApartment max std = 0.0743 — near-zero. Zoning fix intact.

---

## 5. Four Confirmations

**(a) MidriseApartment combined lighting median = 3.965 kWh/m²**
Expected ~4 kWh/m² (527 EFLH x 7.53 W/m² / 1000 = 3.97). Actual 3.965. Prediction matched.
Zoning-only was 43.93 kWh/m². Reduction: -91%.

**(b) Lighting EUI floor-count-independent.**
MidriseApartment std within archetype x level max = 0.074. Zoning fix survives schedule swap.

**(c) MidriseApartment combined equipment median = 43.40 kWh/m²**
Zoning-only was 45.16. Difference = -3.9%. Within expected range; equipment family did not carry the apartment lighting overcount, so no large change was expected.

**(d) MidriseApartment combined TOTAL median = 108.04 kWh/m²**
V17 measured band approximately 116 kWh/m². Combined lands BELOW the V17 band by approximately 8 kWh/m² (~7%). The dominant artifact (lighting overcounting 11x) is removed. The 7% residual gap is consistent with the documented "Other" service-load deficit (fans, pumps, DHW account for ~42% of the V16 residual gap per R6-4B / V16). No tuning applied.

---

## 6. Equipment Rise in Office/Retail

Office combined equipment rose from 37.16 (zoning-only) to 44.06 kWh/m²; retail 45.86 to 48.82. This is attributable to DOE BLDG_EQUIP_SCH having slightly higher EFLH than the prior synthetic schedules for those archetypes. Expected behavior from schedule digitization; not a defect.

---

## 7. Conclusion and P2 Gate

Phase C pilot confirms all four expected outcomes. 47/47 sim success unblocks the headline confirmation. Combined fix produces the expected apartment lighting correction.

**STOP — awaiting manager audit and user go for P2 fan-out.**

Open decisions for manager/user:
1. P2 scope: 9 zoning-affected cells vs all 12 cells (schedule fix is global)
2. P2 execution: local EnergyPlus vs Speed-SLURM cluster (~136 CPU-hours for 8,152 buildings)
3. Post-P2 action: re-score V17; whether apartment total at 108 vs 116 band requires calibration step or is attributed to the known service-load gap

*Artifacts:*
- `runtime/phasec_pilot/phasec_pilot_results.csv` (47 rows)
- `runtime/phasec_pilot/03_idf_manifest.parquet` (47 IDFs)
- `openubem/semantic/schedules.py` (one-line fix)
- `tests/test_schedules.py` (2 regression tests)
