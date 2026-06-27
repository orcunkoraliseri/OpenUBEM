# Phase B — Level-4 CBECS Diagnosis Memo (V06–V08, CP-V2)

> Consolidated 2026-06-11 by the manager from plan §8 entries V06–V08 (executor a3de95d6e6ab1c541).
> Full evidence with code/file citations lives in `PLAN_overall-validation-R5.md` §8.
> Raw V07 output: `%TEMP%\ubem_validation\v07_basis_correction_table.txt`. No `openubem/` code was modified (ruling V-R5-5 / M-R2-4: gates are report-only).

## Bottom line

The CBECS 2018 NE gate failures (NMBE −16.0%, CV(RMSE) 69.8%, KS 0.273) are a **mismatched comparison, not a model defect**. The R3 fleet (downtown Boston, 83% office/tall commercial) is being compared against the full CBECS NE stock (all building types incl. high-EUI food service ~620, hospitals ~350+, nursing ~467 kWh/m²/yr; all NE states incl. colder ME/VT/NH). Fuel-basis correction was tested and **falsified** as the gap driver.

## V06 — Basis audit

- CBECS MFBTU = all-fuels site energy; OpenUBEM cooling = IdealLoads thermal removed (≈3.5× the electricity CBECS would record at COP 3.5); OpenUBEM heating = thermal delivered (NE fuel-mix factor ≈ 1.190 to fuel input).
- Archetype→PBA mapping defensible (all offices → PBA 2; apartments/data centers excluded).
- Vintage gap real but moderate: DOERefPre1980 envelope (1.6× U-factors) with modern 90.1-2019 schedules/setpoints → est. ~10–15% EUI understatement vs 1985-centred stock.

## V07 — Basis-corrected gates (n=465, CBECS NE wmean 220.9 kWh/m²)

| Scenario | Formula | Sim mean kWh/m² | NMBE % |
|---|---|---|---|
| 1. As-is | heat_th + cool_th + light + equip | 185.5 | −16.0 FAIL |
| 2. Cool→electric (÷3.5) | heat_th + cool_th/3.5 + light + equip | 142.8 | −35.3 FAIL |
| 3. Heat fuel ×1.19 + cool ÷3.5 | heat_th×1.19 + cool_th/3.5 + light + equip | 155.7 | −29.5 FAIL |

Correcting the basis **widens** the gap: the as-is −16% is a coincidental offset (inflated cooling thermal masking under-stated heating fuel). Fuel basis is NOT the driver.

## V08 — Cooling dominance (cool 70.9 vs heat 27.9 kWh/m²) is physically plausible

Five-building spot check (constructions verified correct: 1.6× DOERefPre1980 on 90.1-2019 CZ5A base):

| Archetype | Floors | S/F | H/C |
|---|---|---|---|
| SmallOffice | 1 | 1.619 | 1.35 (heat-dom) |
| MediumOffice | 2 | 0.461 | 0.93 |
| LargeOffice | 5 | 0.354 | 0.90 |
| TallBuilding | 22 | 0.281 | 0.157 (cools even in January — internal gains exceed envelope loss) |
| HighriseApartment | 32 | 0.419 | 0.011 (24/7 equipment 0.83 off-hr frac + no heating setback) |

Falsifiable drivers: (1) S/F ratio should rank-correlate with H/C across all 483 buildings; (2) adding a night setback + 0.15 off-hr equip to HighriseApartment should raise H/C to ~0.05–0.10; (3) reweighting by building count instead of floor area raises fleet H/C.

## CP-V2 ruling (OQ-R5-2)

Gates remain **report-only** (V-R5-5 stands); proceed to Phase C. Deep calibration (PBA2-only Boston-climate CBECS sub-sample + vintage-matched schedules) deferred to a future R6 — logged as a user question in `OPEN_QUESTIONS_R5.md`.
