# REPORT — Pilot Resim: Zoning Multi-Floor Fix (Phase B)

**Date:** 2026-06-17
**Plan:** `docs/implementation/zoningBug/PLAN_zoning-multifloor-fix.md` (T04-T06)
**Cell:** `la_urban` (47-building subset pilot)
**Scratch dir:** `runtime/zoning_pilot/`
**Results:** `runtime/zoning_pilot/pilot_results.csv`

---

## 1. Subset definition

47 buildings selected from `la_urban` success rows with `footprint_area_m2 < 500` and `levels > 1`.
Selection: up to 3-4 buildings per archetype per floor-count tier (levels 2-7).

| Archetype | n |
|---|---|
| MidriseApartment | 22 |
| MediumOffice | 11 |
| RetailStandalone | 8 |
| SmallOffice | 6 |
| **Total** | **47** |

Floor-count distribution: 13x level-2, 13x level-3, 7x level-4, 5x level-5, 5x level-6, 4x level-7.

---

## 2. IDF regeneration

All 47 IDFs regenerated using the patched `decide_zoning_strategy` (Phase A fix already committed).

- Generation success: 47/47
- Zoning strategy: `one_zone_per_floor` = 47 (0 single_zone — correct; all selected buildings have `levels > 1`)
- Zone name verification: 47/47 IDFs contain exactly `levels` zones named `_F{i}_WHOLE`

Before the fix, these 47 buildings would have been `single_zone` (footprint < 500 m2). After the fix they are `one_zone_per_floor`.

---

## 3. Simulation smoke pass

EnergyPlus 23.1 local run. All 47 buildings simulated and parsed successfully.

- Sim pass rate: 47/47 = 100%
- SQL parse rate: 47/47 = 100% (3 buildings required clean-directory re-run due to transient SQLite lock from prior interrupted session; all succeeded cleanly on re-run)

---

## 4. Before / after EUI by archetype

"Before" EUI from `r7_service_loads.csv` (old single_zone run). "After" from pilot resim (new one_zone_per_floor).

| Archetype | n | Old lighting median (kWh/m2) | New lighting median (kWh/m2) | Ratio | Old total median (kWh/m2) | New total median (kWh/m2) |
|---|---|---|---|---|---|---|
| MediumOffice | 11 | 11.27 | 33.80 | 3.00x | 81.2 | 180.1 |
| MidriseApartment | 22 | 10.98 | 43.93 | 4.04x | 66.8 | 188.8 |
| RetailStandalone | 8 | 21.60 | 64.59 | 2.99x | 107.3 | 239.5 |
| SmallOffice | 6 | 14.08 | 33.80 | 2.49x | 98.7 | 175.0 |

The ratio matches the median floor count per archetype in the subset (MediumOffice median 3 floors, MidriseApartment median 4 floors, RetailStandalone median 3 floors, SmallOffice median 2.5 floors) exactly the expected recovery factor.

**MidriseApartment new lighting EUI (43.93 kWh/m2) matches the existing NYC MidriseApartment value (43.9 kWh/m2)**, which was already correctly simulated as `one_zone_per_floor` (footprint >= 500 m2). This cross-city consistency confirms the fix is correct.

---

## 5. Lighting-vs-levels check

The bug fingerprint was `old_lighting_eui x levels = constant` per archetype. The fix must make `new_lighting_eui` constant per archetype regardless of floor count.

### New lighting EUI per archetype per floor count (kWh/m2)

| Archetype | level-2 | level-3 | level-4 | level-5 | level-6 | level-7 |
|---|---|---|---|---|---|---|
| MediumOffice | 33.80 | 33.80 | 33.79 | 33.80 | - | 33.64 |
| MidriseApartment | 43.71 | 43.93 | 43.87 | 43.89 | 43.92 | 43.93 |
| RetailStandalone | 64.49 | 64.55 | 64.46 | - | 64.80 | - |
| SmallOffice | 33.80 | 33.80 | - | - | - | - |

Within each archetype, new lighting EUI is constant across all floor counts (+-1% natural geometry variation). Floor count no longer appears in the lighting EUI signal.

### Per-building ratio check (new/old, all buildings)

Expected: `new_lighting_eui / old_lighting_eui ~= levels` (ratio_vs_expected ~= 1.000 for all rows).

All 47 buildings show `ratio_vs_expected` between 0.971 and 1.016 (median 1.000, max deviation +-3%).
The +-3% deviation (one building: way/402253660, MidriseApartment 4-floor) is within normal per-building geometry variation for stacked zones.

### Bug fingerprint summary

| Metric | Value | Interpretation |
|---|---|---|
| Old lighting x levels CV | 0.243 | Low (within-archetype ~0.00) = was constant = bug confirmed |
| New lighting EUI CV | 0.243 | Natural archetype spread (4 archetypes with different LPD) |
| Fraction buildings where lighting EUI rose | 100% | Fix active for all affected buildings |

---

## 6. Example buildings

| osm_id | Archetype | Floors | Old lighting | New lighting | Ratio | Expected |
|---|---|---|---|---|---|---|
| way/401910884 | MediumOffice | 7 | 4.83 | 33.80 | 7.00 | 7.0 |
| way/402036183 | MediumOffice | 5 | 6.76 | 33.80 | 5.00 | 5.0 |
| way/401907389 | MediumOffice | 4 | 8.45 | 33.80 | 4.00 | 4.0 |
| way/402264141 | MidriseApartment | 7 | 6.28 | 43.93 | 7.00 | 7.0 |
| way/401910885 | MidriseApartment | 6 | 7.32 | 43.93 | 6.00 | 6.0 |
| way/402036177 | MidriseApartment | 5 | 8.79 | 43.93 | 5.00 | 5.0 |
| way/428846124 | RetailStandalone | 6 | 10.80 | 64.80 | 6.00 | 6.0 |
| way/376146181 | SmallOffice | 2 | 16.90 | 33.79 | 2.00 | 2.0 |

---

## 7. VERDICT: GO

All go-criteria met:

1. **Lighting EUI rose for 100% of affected buildings** (threshold: >90%). Fix is active.
2. **Sim pass rate 100%** (threshold: >=95%). No IDF generation regressions.
3. **All 47 buildings now use `one_zone_per_floor`** (0 single_zone for multi-floor buildings).
4. **Ratio check: new/old ~= levels** for all 47 buildings (max deviation +-3%).
5. **LA Midrise converges to NYC Midrise** (43.93 vs 43.9 kWh/m2 lighting EUI) -- cross-city consistency confirmed.

The pilot confirms the Phase A fix is correct and ready for full-grid resim (Phase C, 9 cells).
**Await manager/user go before starting Phase C.**
