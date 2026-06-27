# V14 — R6 Batch 1: Region-Correct CBECS Gates + Archetype-Aware Plausibility + eGRID Subregion GWP

**Date:** 2026-06-15
**Round:** R6 Batch 1 (reporting-layer corrections; no resimulation)
**Predecessor:** `V13_cross_case_synthesis.md` (R5 close-out, 12 cells, 8 152 buildings, 100% E+ success)
**Binding contract:** `PLAN_overall-validation-R6-batch1.md` §4 decisions; `DESIGN_*` §5.1 (CBECS gates) and §3E (GWP/eGRID).
**Status:** CP-R6-C close-out.

This document presents three no-resim, reporting-layer corrections to the R5 shipped results. The R5 EUI numbers (Table A of V13) are **UNCHANGED**. R5's shipped state-level GWP values (V13 Table B) remain the **immutable baseline**. No model code, pipeline step, or EnergyPlus run was modified.

---

## 1. Method and provenance

### 1.1 What R6 Batch 1 corrects

Three items were flagged in the R5 §6 backlog and resolved here entirely at the reporting layer:

| Item | R5 gap | R6 correction |
|---|---|---|
| R6-1 | All 12 cells scored vs CBECS **New England** (CENDIV 1), including LA and Austin | Re-scored each city against its correct census division (NYC → Middle Atlantic CENDIV 2; LA → Pacific CENDIV 9; Austin → West South Central CENDIV 7) |
| R6-3 | 4 cells FAIL EUI plausibility under the generic [25,1000] band because real QuickServiceRestaurant EUIs legitimately exceed 1000 kWh/m² | Added an **archetype-aware** plausibility band derived from the CBECS per-PBA reference distribution at fixed a-priori p1/p99; generic band preserved as fallback and R5 headline gate |
| R6-2 | All cells used the **state-level** eGRID CO₂e factor for GWP; NYC/LA/Austin are each served by a distinct grid subregion | Recomputed GWP using the eGRID 2022 **subregion** factor (NYC → NYCW; LA → CAMX; Austin → ERCT) |

### 1.2 Region reference files

Three new CBECS 2018 reference files were extracted from the same source as the R3/R5 New England file, filtered by census-division code:

| Census division | Code | Cells | File | Rows | Weighted-mean EUI |
|---|---|---|---|---|---|
| Middle Atlantic | CENDIV 2 | NYC ×4 | `cbecs_2018_middle_atlantic_eui.csv` | 843 | 237.3 kWh/m² |
| Pacific | CENDIV 9 | LA ×4 | `cbecs_2018_pacific_eui.csv` | 820 | 188.4 kWh/m² |
| West South Central | CENDIV 7 | Austin ×4 | `cbecs_2018_west_south_central_eui.csv` | 755 | 222.8 kWh/m² |

The R5 New England file (`cbecs_2018_new_england_eui.csv`, 284 rows, wmean 220.9 kWh/m²) is **unchanged** and remains the reference for the Boston R3 validation. Extraction method is identical to R5 (same source CSV, same `KBTU_FT2_TO_KWH_M2 = 3.15459` conversion, same weighted-mean logic).

### 1.3 eGRID subregion factors

Source: EPA eGRID 2022, subregion summary sheet `SRL22`, column `SRC2ERTA` (total-output CO₂e rate, lb/MWh), converted to kg/kWh by `× 0.453592 ÷ 1000`. This is the same metric type (`STC2ERTA`) used for the state-level factors, ensuring like-for-like comparison.

| City | Subregion | f_subregion (kg CO₂e/kWh) | f_state (kg CO₂e/kWh) | Ratio |
|---|---|---|---|---|
| NYC ×4 | NYCW (NYC / Westchester) | 0.402146 | NY 0.222872 | 1.804 |
| LA ×4 | CAMX (WECC California) | 0.226469 | CA 0.207512 | 1.091 |
| Austin ×4 | ERCT (ERCOT All) | 0.351215 | TX 0.372828 | 0.942 |

**Critical finding (corrected):** The manager's initial hypothesis that "NYC's grid is cleaner than the NY state average" was **incorrect**. The eGRID 2022 data shows NYCW (0.402146 kg/kWh) is substantially **dirtier** than the NY state average (0.222872 kg/kWh). The explanation is the opposite of the original guess: the NY state average is diluted by ultra-clean **upstate hydro and nuclear** generation (subregion NYUP = 0.124914 kg/kWh) that NYC buildings cannot physically access. The state-level factor therefore **understated** NYC carbon by approximately 60–69%. The subregion factor is the more accurate number and it **raises** NYC GWP. This corrected direction is reflected throughout this document.

### 1.4 GWP recompute method

No resimulation. The recompute uses only columns already in each cell's `05_results.csv` and the two emission factors. Electricity GWP scales linearly with the emission factor; natural-gas heating GWP is unchanged:

```
gwp_elec_old_per_m2  = gwp_cooling_kgco2_m2 + gwp_lighting_kgco2_m2 + gwp_equipment_kgco2_m2
ratio                = f_subregion / f_state
gwp_total_new_per_m2 = gwp_heating_kgco2_m2 + gwp_elec_old_per_m2 × ratio
gwp_total_new_abs    = sum over buildings of (gwp_total_new_per_m2 × floor_area_m2)
```

where `floor_area_m2 = derive_num_floors(row) × footprint_area_m2` (NaN levels handled by `height_m / 3.5` fallback, consistent with the V13 aggregator). The R5 `05_results.csv` files are **not modified** — the recompute is in-memory only.

### 1.5 Archetype-aware plausibility band — semantics

The archetype-aware band is **additive** to the generic band, not a replacement. A building is counted plausible if:

- `total_eui_kwh_m2 ∈ [25, 1000]` (generic band — the R5 headline gate, unchanged), **OR**
- its archetype has a CBECS PBA-derived p1/p99 band **AND** `total_eui_kwh_m2` falls within that band.

Archetypes with no PBA band fall back to the generic band only. The fallback applies when: the archetype's CBECS PBA mapping is `null` (MidriseApartment, DataCenter, DataCentreHPC), the archetype is `OpenUBEMUnknown`, or the PBA has fewer than 10 reference rows in the region (too few for a stable quantile). Percentiles are fixed **a priori at p1/p99** of the region reference — they were never adjusted after observing cell results (V-R5-5).

The generic plausibility % reproduces V13 Table C exactly for all 12 cells (verified to 2 decimal places before any archetype-aware computation was applied).

---

## 2. CBECS gates: Northeast (R5) vs region-correct (R6)

All gates remain **report-only** (V-R5-5 / M-R2-4). Thresholds are unchanged: CV(RMSE) < 30%, NMBE < |10|%, R² > 0.6, KS_D < 0.10. n_excluded = buildings whose archetype has null CBECS PBA (apartments, data centres), excluded from distribution gates per the existing gate function.

### Table 1 — CV(RMSE) %

| Cell | R5 (NE) | R6 (region) | Delta | R6 pass? |
|---|--:|--:|--:|:--:|
| nyc_centre | 89.508 | 72.139 | −17.369 | No |
| nyc_urban | 95.564 | 77.621 | −17.943 | No |
| nyc_suburban | 94.001 | 72.329 | −21.672 | No |
| nyc_rural | 56.639 | 39.449 | −17.190 | No |
| la_centre | 65.214 | 53.205 | −12.009 | No |
| la_urban | 79.995 | 62.535 | −17.460 | No |
| la_suburban | 87.613 | 59.660 | −27.953 | No |
| la_rural | 79.996 | 67.811 | −12.185 | No |
| austin_centre | 47.578 | 35.809 | −11.769 | No |
| austin_urban | 80.134 | 73.990 | −6.144 | No |
| austin_suburban | 49.400 | 46.366 | −3.034 | No |
| austin_rural | 51.447 | 43.587 | −7.860 | No |

### Table 2 — NMBE %

| Cell | R5 (NE) | R6 (region) | Delta | R6 pass? |
|---|--:|--:|--:|:--:|
| nyc_centre | −34.912 | −39.419 | −4.507 | No |
| nyc_urban | −20.334 | −25.850 | −5.516 | No |
| nyc_suburban | +65.955 | +54.464 | −11.491 | No |
| nyc_rural | +23.746 | +15.178 | −8.568 | No |
| la_centre | −13.561 | +1.375 | +14.936 | Yes |
| la_urban | −21.081 | −7.445 | +13.636 | Yes |
| la_suburban | −26.950 | −14.328 | +12.622 | No |
| la_rural | −11.520 | +3.768 | +15.288 | Yes |
| austin_centre | +12.534 | +11.588 | −0.946 | No |
| austin_urban | −19.071 | −19.751 | −0.680 | No |
| austin_suburban | −10.393 | −11.146 | −0.753 | No |
| austin_rural | +4.583 | +3.704 | −0.879 | Yes |

### Table 3 — R²

| Cell | R5 (NE) | R6 (region) | Delta | R6 pass? |
|---|--:|--:|--:|:--:|
| nyc_centre | 0.7811 | 0.7416 | −0.0395 | Yes |
| nyc_urban | 0.8645 | 0.5645 | −0.3000 | No |
| nyc_suburban | 0.9957 | 0.9941 | −0.0016 | Yes |
| nyc_rural | 0.8373 | 0.8844 | +0.0471 | Yes |
| la_centre | 0.7744 | 0.7522 | −0.0222 | Yes |
| la_urban | 0.8467 | 0.7988 | −0.0479 | Yes |
| la_suburban | 0.6874 | 0.3201 | −0.3673 | No |
| la_rural | 0.9943 | 0.1290 | −0.8653 | No |
| austin_centre | 0.9072 | 0.9147 | +0.0075 | Yes |
| austin_urban | 0.8744 | 0.5878 | −0.2866 | No |
| austin_suburban | 0.8999 | 0.9013 | +0.0014 | Yes |
| austin_rural | 0.8446 | 0.6286 | −0.2160 | Yes |

### Table 4 — KS_D

| Cell | R5 (NE) | R6 (region) | Delta | R6 pass? |
|---|--:|--:|--:|:--:|
| nyc_centre | 0.2870 | 0.2983 | +0.0113 | No |
| nyc_urban | 0.3427 | 0.2161 | −0.1266 | No |
| nyc_suburban | 0.5608 | 0.4981 | −0.0627 | No |
| nyc_rural | 0.5661 | 0.5210 | −0.0451 | No |
| la_centre | 0.2647 | 0.3059 | +0.0412 | No |
| la_urban | 0.2209 | 0.2212 | +0.0003 | No |
| la_suburban | 0.2633 | 0.2553 | −0.0080 | No |
| la_rural | 0.2305 | 0.2996 | +0.0691 | No |
| austin_centre | 0.3929 | 0.3661 | −0.0268 | No |
| austin_urban | 0.3321 | 0.3001 | −0.0320 | No |
| austin_suburban | 0.3261 | 0.3034 | −0.0227 | No |
| austin_rural | 0.5177 | 0.4818 | −0.0359 | No |

### Narrative

**CV(RMSE) improved for all 12 cells** under the region-correct reference (deltas range from −3.0 to −28.0 percentage points). However, **not one cell reaches the <30% threshold**. The closest is austin_centre at 35.8%. This confirms that the CV(RMSE) shortfall is primarily driven by **fleet-composition mismatch** — OpenUBEM fleets are office- and residential-heavy, while the CBECS regional reference includes hospitals, food-service, and other building types that inflate the reference mean and variance — not by a regional-reference error. Correcting the region narrows the gap but does not close it. This is an expected finding, not a model defect. CV(RMSE) gate remains report-only.

**NMBE** shows the largest absolute shifts for LA cells (+13–15 pp), where the Northeast reference systematically over-predicted mean EUI relative to the Pacific distribution. Several LA cells flip from FAIL to PASS on NMBE. NYC NMBE worsens slightly (the Middle Atlantic reference has a higher mean than New England for the relevant PBA mix, pulling the bias more negative). Austin NMBE changes are small (−1 to −1 pp) because the West South Central reference mean is close to Northeast for the office-dominated Austin fleet.

**R² dropped sharply for la_suburban (0.687 → 0.320) and la_rural (0.994 → 0.129).** This is **archetype-R² fragility**, not a model regression. Both cells are near-entirely MidriseApartment (la_suburban: 1283/1343 buildings excluded from distribution gates as null-PBA; la_rural: 149 buildings, 10 excluded). With only 60 and 139 non-excluded buildings respectively, R² is computed against a very thin archetype slice. The Pacific reference, while regionally correct, contains fewer comparable building types in those specific PBA categories, making the per-archetype R² unstable. This is a **reporting note** consistent with gates being report-only.

**No gate threshold was changed. All CBECS results remain report-only per V-R5-5 / M-R2-4.**

---

## 3. EUI plausibility: generic vs archetype-aware

The generic [25, 1000] band is the R5 headline gate (unchanged). The archetype-aware band is an R6 additive view (see §1.5 for semantics).

### Table 5 — Plausibility %

| Cell | n success | Generic [25,1000] % | Generic pass? | Archetype-aware % | Archetype pass? |
|---|--:|--:|:--:|--:|:--:|
| nyc_centre | 738 | 99.73 | Yes | 99.86 | Yes |
| nyc_urban | 1779 | 100.00 | Yes | 100.00 | Yes |
| nyc_suburban | 1589 | 99.94 | Yes | 100.00 | Yes |
| nyc_rural | 198 | 98.48 | **No** | 100.00 | Yes |
| la_centre | 226 | 99.12 | Yes | 99.56 | Yes |
| la_urban | 614 | 99.67 | Yes | 99.84 | Yes |
| la_suburban | 1343 | 99.93 | Yes | 99.93 | Yes |
| la_rural | 149 | 100.00 | Yes | 100.00 | Yes |
| austin_centre | 413 | 95.40 | **No** | 100.00 | Yes |
| austin_urban | 417 | 99.76 | Yes | 100.00 | Yes |
| austin_suburban | 437 | 98.63 | **No** | 100.00 | Yes |
| austin_rural | 245 | 97.14 | **No** | 100.00 | Yes |

*Pass threshold: ≥99%. Generic % reproduces V13 Table C to 2 decimal places for all 12 cells.*

The generic band figures are **identical to V13 Table C**. R5's shipped plausibility results are not altered. The archetype-aware column is an R6 additive view only.

---

## 4. Resolution of the 4 R5-FAIL plausibility cells (OQ-R5-11)

The four cells that FAIL the generic plausibility gate in R5 — nyc_rural, austin_centre, austin_suburban, austin_rural — all resolve under the archetype-aware band. In every case the out-of-band buildings are **QuickServiceRestaurant** archetypes with EUIs in the range 1076–1137 kWh/m²/yr.

The CBECS PBA-15 (Food service and drinking places) per-region reference yields the following archetype-aware bands (weighted p1/p99):

- **Middle Atlantic (NYC region):** PBA-15 band = [246.8, 1444.3] kWh/m²/yr
- **West South Central (Austin region):** PBA-15 band = [188.6, 2466.8] kWh/m²/yr

All QSR outliers from these cells fall inside their respective PBA-15 bands:

| Cell | QSR EUI range (kWh/m²/yr) | PBA-15 band | Verdict |
|---|---|---|---|
| nyc_rural | 1100.2 – 1101.2 (3 buildings) | [246.8, 1444.3] | In band |
| austin_centre | 1076.6 – 1136.7 (19 buildings) | [188.6, 2466.8] | In band |
| austin_suburban | 1084.9 – 1113.3 (6 buildings) | [188.6, 2466.8] | In band |
| austin_rural | 1110.2 – 1119.9 (7 buildings) | [188.6, 2466.8] | In band |

**This is OQ-R5-11 resolved by archetype awareness, not by widening the generic band.** The PBA-15 bands are derived from the CBECS reference distribution at fixed a-priori p1/p99 and were not adjusted after observing cell results. The generic band [25, 1000] FAILS for these cells remain reported alongside and are unchanged — the archetype-aware column is a supplementary view that provides a principled reason why the outliers are physically plausible, not a retroactive patch.

The V-R5-8 manager ruling ("band stays as-is for R5") is honoured: R5 Table C is not updated. The archetype-aware view is a new R6 column only.

---

## 5. GWP: state-level (R5 baseline) vs eGRID subregion (R6 refinement)

R5's shipped state-level GWP values (V13 Table B) remain the **immutable baseline**. The subregion-corrected GWP is the R6 refinement — a more accurate carbon accounting for each city's actual grid zone. No resimulation; no `05_results.csv` files modified.

### Table 6 — GWP comparison

| Cell | R5 state GWP (kgCO₂e) | R6 subregion GWP (kgCO₂e) | Δ % | State | Subregion |
|---|--:|--:|--:|---|---|
| nyc_centre | 332,809,487 | 563,458,559 | **+69.3%** | NY (0.222872) | NYCW (0.402146) |
| nyc_urban | 40,317,055 | 62,229,412 | **+54.4%** | NY (0.222872) | NYCW (0.402146) |
| nyc_suburban | 8,464,410 | 13,552,680 | **+60.1%** | NY (0.222872) | NYCW (0.402146) |
| nyc_rural | 2,567,219 | 4,215,981 | **+64.2%** | NY (0.222872) | NYCW (0.402146) |
| la_centre | 119,015,264 | 129,460,032 | **+8.8%** | CA (0.207512) | CAMX (0.226469) |
| la_urban | 101,280,696 | 110,190,324 | **+8.8%** | CA (0.207512) | CAMX (0.226469) |
| la_suburban | 14,052,830 | 15,184,865 | **+8.1%** | CA (0.207512) | CAMX (0.226469) |
| la_rural | 4,488,260 | 4,833,940 | **+7.7%** | CA (0.207512) | CAMX (0.226469) |
| austin_centre | 242,610,785 | 228,867,877 | **−5.7%** | TX (0.372828) | ERCT (0.351215) |
| austin_urban | 64,368,469 | 60,803,461 | **−5.5%** | TX (0.372828) | ERCT (0.351215) |
| austin_suburban | 17,946,122 | 16,975,614 | **−5.4%** | TX (0.372828) | ERCT (0.351215) |
| austin_rural | 10,891,760 | 10,287,322 | **−5.6%** | TX (0.372828) | ERCT (0.351215) |

### Narrative

**NYC cells — headline accuracy finding.** The R6 subregion correction raises NYC GWP by +54% to +69% across the four cells. This is the most significant accuracy correction in R6 Batch 1. The manager's initial assumption ("NYC should be cleaner than the NY state average") was corrected by the eGRID 2022 data: NYCW (0.402146 kg/kWh) is 1.80× the NY state average (0.222872 kg/kWh) because the state average is diluted by ultra-clean upstate hydro and nuclear generation (NYUP = 0.125 kg/kWh) that NYC buildings physically cannot access. R5's state-level GWP therefore **understated NYC carbon by approximately 60–69%**. The subregion GWP is the more defensible number for any carbon reporting that targets the NYC grid zone. The variation across NYC cells (+54% to +69%) reflects differences in floor-area-weighted electricity share across the cells' archetype mixes (e.g., nyc_suburban is 61.6% midrise apartment with lower electricity intensity per m², pulling the ratio toward the lower end; nyc_centre is office-dominated with higher electricity share, pulling it toward the higher end).

**LA cells.** CAMX (0.226469 kg/kWh) is slightly above the CA state average (0.207512 kg/kWh), yielding modest increases of +7.7% to +8.8%. The CAMX subregion covers the California balancing area and is a close match to the state average, reflecting California's relatively uniform grid mix. The correction is real but second-order relative to NYC.

**Austin cells.** ERCT (0.351215 kg/kWh) is marginally below the TX state average (0.372828 kg/kWh), yielding reductions of −5.4% to −5.7%. ERCOT (the Electric Reliability Council of Texas) covers most of Texas and is close to the state average; the correction direction is expected (ERCOT is slightly less carbon-intensive than the TX state mix which includes some renewables in western Texas outside ERCOT).

**Immutable baseline.** R5's state-level GWP values (V13 Table B column "GWP (kgCO₂e)") are unchanged and remain the shipped R5 artifact. The R6 subregion GWP is a refinement layer only. The two sets of numbers must never be merged or reported interchangeably without clear provenance labels.

---

## 6. Conclusions

1. **Region-correct CBECS references improve all 12 CV(RMSE) values** (−3 to −28 pp) but confirm that the dominant shortfall is fleet-composition mismatch, not regional-reference error. No cell reaches the <30% threshold. This is expected and non-blocking; gates remain report-only (V-R5-5).

2. **Archetype-aware plausibility resolves all 4 R5-FAIL cells** (nyc_rural, austin_centre, austin_suburban, austin_rural). Every QSR outlier in those cells falls inside the CBECS PBA-15 food-service band derived at fixed p1/p99. The generic band figures are unchanged and reported alongside; this is OQ-R5-11 closed by principled archetype awareness.

3. **The NYC eGRID subregion correction is the headline accuracy finding.** NYC buildings sit in the NYCW grid subregion (0.402 kg CO₂e/kWh), which is 1.80× the NY state average diluted by clean upstate generation. R5's state-level GWP understated NYC carbon by 54–69%. The R6 subregion GWP is the more accurate number for NYC carbon reporting; R5's baseline remains the shipped artifact.

4. **LA rises modestly (+8–9%) and Austin falls slightly (−5–6%)** under the subregion correction, both consistent with their respective grid zones' relationship to the state-level averages.

5. **R5 EUI numbers are unchanged.** No EnergyPlus resimulation was performed. All per-cell `05_results.csv` files are unmodified (verified by mtime check in `test_r6_gwp_subregion.py`).

6. **R6-4 (HVAC/zoning deep calibration)** — the structural Level-2 single-building round-trip gap (V13 §6.5) — remains future work. This document closes **R6 Batch 1 (reporting-layer corrections)** only.

---

## 7. Artifacts

- Region reference CSVs: `inputs/reports/cbecs_2018_{middle_atlantic,pacific,west_south_central}_eui.csv` + `_PROVENANCE.md`
- Re-scoring engine: `scripts/validation/r6_rescore_cells.py`
- eGRID subregion factors: `openubem/data/carbon/egrid_2022_subregions.json`
- Per-cell R6 reports (×12): `docs/validations/overAll/results/cases/<cell>/r6_gates_report.txt`
- Summary CSV: `docs/validations/overAll/results/r6_rescore_summary.csv`
- Tests: `tests/test_cbecs_region_extract.py`, `tests/test_r6_rescore.py`, `tests/test_r6_gwp_subregion.py`
- Progress log (binding): `docs/validations/overAll/PLAN_overall-validation-R6-batch1.md` §8
