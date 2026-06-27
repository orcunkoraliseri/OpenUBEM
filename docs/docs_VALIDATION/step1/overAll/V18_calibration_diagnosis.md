# V18 — Calibration Diagnosis

**Date:** 2026-06-17
**Author:** Sonnet executor (V18 plan)
**Plan:** `docs/validations/overAll/PLAN_V18_calibration_diagnosis.md`
**Status:** Diagnosis only. No model, code, or output files changed.
**Upstream:** V17 external measured validation; D01–D05 of this plan.
**Deliverables:** `v18_la_enduse_gap.csv`, `v18_grossup_check.csv`, `scripts/diagnostics/v18_calibration_diagnosis.py`

---

## ⚠ MANAGER AUDIT CORRECTION (2026-06-17, Opus)

The executor correctly root-caused Gap 1 (internal loads simulated for one floor, normalized over all floors), but its **fix-class call is overturned**. The report below states Gap 1 is a "reporting-layer parser bug, **Resim? No**." That is **wrong**. Verified by the manager:

- **Lighting & equipment** EUI are deterministically `one-floor ÷ levels` (MediumOffice: `light×levels = 33.80`, `equip×levels = 37.16` exactly, at every floor count). These could in principle be ×levels-corrected in reporting.
- **Heating & cooling** are **not** one-floor values — they are genuine single-tall-zone simulations (`heat×levels` climbs 17→538 across floor counts). A parser renormalization cannot recover the EUI of a correctly-zoned N-floor building from single-tall-zone output.
- A parser-only fix would correct internal loads but leave heating/cooling on a physically wrong basis. Test: ×levels-correcting only light+equip raises NYC office to ~221 kWh/m² → **overshoots** measured 184; dividing everything by footprint only gives ~635 → absurd. **Neither pure-reporting patch is sound.**
- **DESIGN §262 intends `one_zone_per_floor` (residential) / `perimeter_core` (large commercial) multi-floor zoning** for these buildings; producing one floor of internal loads is a **geometry/zoning defect relative to DESIGN**, and `floor_area = footprint × n_floors` (DESIGN §262/§300) is only valid if all floors are simulated.

**Corrected fix class for Gap 1: geometry/zoning defect (not reporting-layer). Resim: YES** — the correct fix is to make zoning emit the DESIGN-specified multi-floor zones and re-simulate. This is the **dominant confound in the V17 cross-city comparison**: NYC's "spot-on" office match (183 vs 184) is partly an artifact of internal-load under-counting in a tall-building stock, and LA/Austin "run hot" partly because their shorter stock under-counts less. The Gap-1 rows in §0 and §4 below are superseded by this note. Gap 2 and Gap 3 findings stand.

---

## 0. Executive summary

Three gaps surfaced in V17 are now root-caused. Two require EnergyPlus resimulation to close; one (the cross-city lighting/equipment gap that inflated the LA office EUI) does not — it is a reporting-layer normalization design choice. The fix priorities and resim requirements are:

| Gap | Fix class | Resim? | Priority |
|---|---|---|---|
| Cross-city lighting/equipment EUI gap (inflates LA office, deflates NYC MF medians) | Code/config bug in results parser | **No** | P1 (distorts all city comparisons) |
| Restaurant/food-service reconstruction overshoot (+110/+160 %) | Both: inflated sim base (resim required) + wrong assumed fraction (reporting fix) | **Yes (partial)** | P1 (egregious per-building error) |
| Multifamily reconstruction overshoot (+32–34 %) | Reconstruction-method limitation (assumed modeled_frac too low) | **No** (reporting fix) | P2 (2,850 buildings, systematic) |

---

## 1. Gap 1 — Cross-city lighting/equipment EUI divergence

### Evidence

From `v18_la_enduse_gap.csv` (D02):

| Group | City | Lighting+equip median (kWh/m2) |
|---|---|---|
| Office | NYC | 20.56 |
| Office | LA | 57.21 |
| Office | Austin | 57.21 |
| Multifamily | NYC | 89.09 |
| Multifamily | LA | 44.54 |
| Multifamily | Austin | 89.09 |

NYC office is 2.78x lower than LA/Austin. NYC multifamily is 2x higher than LA. The divergences go in opposite directions for the two archetypes.

**D03 corrected finding — per-level proof:**

The `MediumOffice` per-level breakdown for NYC single-zone buildings (from `r7_service_loads.csv`):

| levels | lighting_eui (kWh/m2) | eui × levels |
|---|---|---|
| 1 | 33.80 | 33.80 |
| 2 | 16.90 | 33.80 |
| 3 | 11.27 | 33.80 |
| 4 | 8.45 | 33.80 |
| 5 | 6.76 | 33.80 |
| 6 | 5.63 | 33.80 |

`eui × levels` = 33.80 to four decimal places for all single-zone buildings regardless of city. Correlation(lighting_eui, 1/levels) = 0.63.

**IDF inspection** — three IDFs inspected directly (D03):
- NYC MediumOffice 1-floor (`way_265875636.idf`): 1 Zone, LPD=10.76 W/m2, schedule=`Lighting_Schedule_MediumOffice`
- NYC MediumOffice 4-floor (`way_265302107.idf`): **1 Zone** (ground floor only), LPD=10.76, same schedule
- LA MediumOffice 1-floor (`way_427942814.idf`): 1 Zone, LPD=10.76, same schedule

The schedule is **identical** across all three cities and both floor counts.

**Mechanism:** For `single_zone` IDFs, EnergyPlus simulates only the footprint zone (ground floor). The results parser (`openubem/results/parser.py` L191–204) divides annual energy by `footprint_area × levels`. For a 4-floor building with only 1 floor simulated, the parser divides by 4× the simulated area, yielding 1/4 of the correct EUI. NYC stock has higher median floor counts (MediumOffice: median 4 floors) vs LA (median 3) and Austin (median 2), producing lower aggregate medians.

The same mechanism explains the LA multifamily anomaly: LA MidriseApartment median levels = 2 (vs NYC = 1), so LA shows half the lighting EUI of NYC.

**The previous D03 conclusion was wrong:** it attributed the gap to per-footprint normalization being "physically correct for taller buildings." In fact the schedule is identical, LPD is identical, and the divergence is entirely traceable to `levels` in the building manifest versus `n_zones_simulated` in the IDF. LargeOffice is identical across cities (NYC median light_eui = 33.75 ≈ LA 33.80 ≈ Austin 33.80) because LargeOffice buildings have enough floors that the perimeter_core zoning strategy dominates, which does simulate multiple zones (producing higher aggregate energy) that partially compensates.

### Root cause

Single-zone IDF pipeline step simulates only 1 floor but the parser normalizes by all label floors. This is a **code/config bug** in the results parser (or equivalently an IDF generation design choice: the IDF should replicate zones for each floor, or the parser should normalize by the zone floor area E+ actually simulated rather than `footprint × label_levels`).

### Fix class

**Code/config bug** — reporting layer only.

### Resim?

**No.** The simulation outputs are correct for the 1-zone geometry E+ was given. The fix is to normalize the reported EUI by the zone floor area that E+ actually modeled, not by `footprint × label_levels` from the manifest. No EnergyPlus re-run required.

### Minimal lever

In `openubem/results/parser.py` function `_compute_eui` (L181–207): replace `floor_area = footprint_area * num_floors` with `floor_area = actual_simulated_floor_area` derived from the IDF zone areas or from `n_zones_per_floor × footprint_area`. Alternatively, divide by `footprint_area` only (report EUI per footprint, not per total floor area) with a matching change to benchmarks. The choice of normalization basis must be documented and applied consistently to measured comparisons.

**Governance note:** This fix changes the reported EUI values for all multi-story single-zone buildings without resimulation. It is a reporting-layer change that should be validated against V17 disclosure data after application.

---

## 2. Gap 2 — Restaurant/food-service reconstruction overshoot (+110/+160 %)

### Evidence

From `v18_grossup_check.csv` (D04):

| Archetype | sim_base_median | modeled_frac_assumed | E_total_est | ESPM measured | implied_true_frac | frac_divergence |
|---|---|---|---|---|---|---|
| FullServiceRestaurant | 712.3 | 0.33 | 2158.5 | 1027.2 | 0.693 | +0.363 |
| QuickServiceRestaurant | 1091.6 | 0.33 | 3307.9 | 1270.3 | 0.859 | +0.529 |
| Supermarket (control) | ~529 | 0.34 | ~1556 | 618.3 | ~0.86 | — |

**Root causes (a)/(b)/(c):**

**(a) Assumed modeled_frac 0.33 is too low.** The Table-4 `full_service_restaurant` fractions assign heat+cool+light+equip = 0.12+0.07+0.05+0.09 = 0.33, implying 67% of total energy is unmodeled service loads (cooking 0.355, refrigeration 0.15). This means the gross-up multiplier is 1/0.33 = 3.03×. But the implied true modeled fraction is sim_base/ESPM = 712.3/1027.2 = 0.69, so the correct multiplier is only 1.45×. The fraction assumption introduces a 2.1× error.

**(b) The simulated 4-end-use base is itself inflated.** The PNNL CZ6A prototype FSR total is 1063.7 kWh/m2, of which the 4-EU fraction is 1063.7 × 0.33 = 351 kWh/m2. Our FSR sim_base median = 712.3 kWh/m2, which is **2.03× the PNNL expected 4-EU base**. The restaurant archetype is likely being assigned office/retail schedules or LPD/EPD values that are inappropriate for cooking-dominated buildings. The simulation runs hot before the gross-up is even applied.

**(c) QuickServiceRestaurant borrows FSR fractions.** The `archetype_map` maps both `FullServiceRestaurant` and `QuickServiceRestaurant` to `full_service_restaurant` fractions. QSR operates on faster turnover with higher appliance intensity; its implied true fraction (0.86) is even higher than FSR's (0.69), confirming the FSR fraction is wrong for QSR specifically.

**(d) Structural unsuitability of the divide method for cooking-dominated types.** Even if the fraction were correct, the reconstruction method (divide sim_base by modeled_frac) amplifies any base error by 1/frac. For frac=0.33, a 2× base error becomes a 6× total-EUI error. Cooking-dominated types violate the implicit assumption that the 4 modeled end-uses are representative of total building intensity.

### Root cause

Compound: (a) wrong assumed fraction + (b) inflated simulation base. Both must be addressed.

### Fix class

- Fraction correction (a): **Reconstruction-method limitation** — the Table-4 fractions for FSR are empirically wrong for the buildings in this stock. Fix = recalibrate FSR modeled_frac in `enduse_fractions_table4.json` to 0.69 (reporting layer, no resim).
- Inflated base (b): **Genuine calibration (resim required)** — the 4-EU base is 2× PNNL expected, which reflects E+ simulation inputs (LPD/EPD/schedules) being tuned for office archetypes rather than restaurants. Fix = audit and correct FSR/QSR archetype inputs (LPD, EPD, schedules) in the IDF generation step and resimulate.

### Resim?

**Partially yes.** The fraction correction (a) is reporting-layer only and can proceed immediately. The base inflation (b) requires correcting simulation inputs and resimulating the ~83 restaurant buildings.

### Minimal lever

Step 1 (no resim): Update `enduse_fractions_table4.json` `full_service_restaurant.space_heat + .space_cool + .lighting + .equip_plug` from 0.33 to ~0.69. Adjust complementary fractions proportionally to preserve sum=1.
Step 2 (resim): Audit FSR/QSR archetype inputs — verify LPD, EPD, cooking equipment schedules are set to restaurant values not office defaults.
Step 3: Create a separate `quick_service_restaurant` entry in archetype_map rather than borrowing FSR fractions.

---

## 3. Gap 3 — Multifamily reconstruction overshoot (+32–34 %)

### Evidence

From `v18_grossup_check.csv` (D05):

| Archetype | sim_base_median | modeled_frac_assumed | E_total_est | ESPM measured | implied_true_frac | frac_divergence |
|---|---|---|---|---|---|---|
| MidriseApartment (all cities) | 157.9 | 0.69 | 228.8 | 187.9 | 0.840 | +0.150 |
| MidriseApartment (NYC) | 208.4 | 0.69 | 301.9 | 226.2 (measured) | 0.921 | +0.231 |

**Direction paradox:** Table-4 assumes MF DHW = 0.23 of total; RECS 2020 measured MF DHW = 0.33. If the real DHW share were 0.33, the unmodeled share is larger, the modeled_frac should be smaller (0.69 − (0.33 − 0.23) = 0.59), and the gross-up would be even larger (1/0.59 = 1.69×) — making the overshoot worse, not better. Yet the actual NYC overshoot is already only +34 % with the 0.69 assumption.

**Resolution:** The paradox resolves by observing that the NYC 4-end-use base (208.4 kWh/m2) already equals 92% of measured (226.2). Real NYC multifamily buildings have an unusually high share of their energy in space heating (NYC climate, CZ 4A, high heating load) and space cooling, leaving very little room for service loads. The Table-4 assumed modeled_frac of 0.69 is calibrated to a national US average MF stock; NYC-specific buildings have implied_true_frac ≈ 0.92 — i.e., the 4 modeled end-uses already account for 92% of actual energy. Applying a 1.45× gross-up to a base that is already 92% of measured inflates the total to 302 (= 208 / 0.69), a 34% overshoot.

The DHW fraction discrepancy (0.23 vs 0.33) is real but secondary: the primary error is that Table-4 assumes 31% of MF energy is unmodeled service loads, when in heating-dominated NYC stock it is only ~8%.

### Root cause

**Reconstruction-method limitation:** the Table-4 MF modeled_frac (0.69) underestimates how much of the real building's energy the 4-end-use simulation captures for cold-climate MF stock. The assumed national fraction is inapplicable to NYC's heating-dominated multifamily stock.

### Fix class

**Reconstruction-method limitation** — the fraction is empirically wrong for this stock.

### Resim?

**No.** The simulation base is consistent with measured (NYC 4EU base 208 vs measured 226, −8%). The fix is a reporting-layer change: increase `mid_rise_apartment.modeled_frac` in the reconstruction fractions. The correction should be climate-zone-aware (NYC CZ 4A needs higher modeled_frac than national average).

### Minimal lever

Update `enduse_fractions_table4.json` `mid_rise_apartment` fraction: increase `space_heat + space_cool + lighting + equip_plug` toward 0.85–0.92 for cold climates. The simplest single-value fix is 0.85 (a compromise between the national implied 0.84 and NYC-specific 0.92). Adjust swh_dhw and vent_fans proportionally.

---

## 4. Prioritized recommendation table

| Priority | Gap | Fix class | Resim? | Lever | Expected outcome |
|---|---|---|---|---|---|
| **P0** | Cross-city EUI normalization bug (parser divides by label floors, not simulated floors) | Code/config bug | No | Fix `_compute_eui` in `parser.py` to normalize by actual simulated zone area | Corrects all multi-story EUI; may close most of the LA office gap |
| **P1a** | Restaurant fraction assumption (modeled_frac 0.33 → ~0.69) | Reconstruction-method limitation | No | Update `enduse_fractions_table4.json` FSR entry; separate QSR entry | Reduces FSR overshoot from +110% to ~+50%; QSR proportionally |
| **P1b** | Restaurant simulation base (2× PNNL expected) | Genuine calibration | **Yes** | Audit FSR/QSR archetype inputs (LPD/EPD/schedules); resim ~83 buildings | Eliminates remaining ~50% overshoot after P1a |
| **P2** | Multifamily modeled_frac too low (0.69 vs implied 0.85–0.92) | Reconstruction-method limitation | No | Update `mid_rise_apartment` modeled_frac; climate-zone-aware if possible | Reduces MF overshoot from +34% to <10% for NYC |

**Critical governance note on P0:** Applying the parser normalization fix will change EUI values for all multi-story single-zone buildings retroactively. The corrected NYC office EUI will increase (buildings are currently under-reported on a per-floor-area basis), and LA office EUI will decrease less than expected (LA has more perimeter_core buildings). This may re-score the V17 city-level table. The fix must be run through the full validation pipeline before being declared a calibration improvement.

---

## 5. Data sources and traceability

- D01/D02 anchor: `docs/validations/overAll/results/r7_service_loads.csv` (8,148 success rows)
- D02 output: `docs/validations/overAll/results/v18_la_enduse_gap.csv`
- D03 IDF files read:
  - `runtime/ubem_validation/cases/nyc_centre/step3/idfs/way_265875636.idf` (NYC MediumOffice 1-floor)
  - `runtime/ubem_validation/cases/nyc_centre/step3/idfs/way_265302107.idf` (NYC MediumOffice 4-floor)
  - `runtime/ubem_validation/cases/la_centre/step3/idfs/way_427942814.idf` (LA MediumOffice 1-floor)
- D03 parser: `openubem/results/parser.py` L181–207 (`_compute_eui`)
- D04/D05 output: `docs/validations/overAll/results/v18_grossup_check.csv`
- D04/D05 measured anchors: RESULT_5 ESPM-2024 medians (`docs/validations/external_literature/RESULT_5_per_archetype_benchmarks.md`)
- Table-4 fractions: `openubem/data/service_loads/enduse_fractions_table4.json`
- NYC measured MF: RESULT_1 LL84/133 CY2024 disclosure median = 226.2 kWh/m2 (V17 §3)
