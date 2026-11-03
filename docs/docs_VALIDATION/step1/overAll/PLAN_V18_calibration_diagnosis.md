# PLAN — V18 Calibration Diagnosis

**Slug:** V18-calibration-diagnosis
**Date:** 2026-06-17
**Author:** Manager (Opus session)
**Binding contract:** This is a **diagnosis-only** plan. It localizes the three gaps surfaced in `V17_external_measured_validation.md` to their root cause **without changing any model, code, or output.** The executor investigates and writes findings; it does not fix.
**Upstream evidence:** `docs/validations/overAll/V17_external_measured_validation.md`, `docs/validations/external_literature/RESULT_1..6_*.md`.

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No other working directory.
2. **DIAGNOSIS ONLY — change nothing that the pipeline reads.** Do **not** edit any file under `openubem/`, any existing file under `scripts/`, any `05_results.*`, any committed CSV in `docs/validations/overAll/results/`, the Table-4 JSON, or any gate/core-math module. Do **not** run EnergyPlus. Do **not** re-run `reconstruct_service_loads.py` to overwrite `r7_service_loads.csv`.
3. **You may create exactly one new read-only analysis script:** `scripts/diagnostics/v18_calibration_diagnosis.py`. It may only *read* existing artifacts and *emit* the report + diagnostic CSVs named in §3. It must not import-and-mutate or monkeypatch any pipeline module.
4. **No plan-writing.** Execute this plan top to bottom. If the evidence contradicts the plan, **STOP and quote the conflict** — do not improvise a fix.
5. **No scope creep.** You are not calibrating, not tuning, not "while I'm here" refactoring. Findings only.
6. **Default to no comments** in the diagnostic script; one line max where the WHY is non-obvious.
7. **Figures (if any) → `openubem/outputs/`** flat. Diagnostic CSVs → `docs/validations/overAll/results/`. The narrative report → `docs/validations/overAll/V18_calibration_diagnosis.md`.

---

## 2. Source-of-truth verified facts (manager already grepped these)

- **Gross-up formula** — `openubem/results/service_loads.py:89`:
  `E_total_est = (heating + cooling + lighting + equipment) / modeled_frac`, then each missing end-use = `frac[k] * E_total_est`, and `total_recon = total_sim + Σ recon`. So `total_recon == E_total_est` whenever `total_sim` equals the four modeled end-uses.
- **`modeled_frac` = sum of `space_heat + space_cool + lighting + equip_plug`** from `enduse_fractions_table4.json` (`service_loads.py:79`, `_MODELED_FRAC_KEYS` at line 22).
- **Restaurant fractions** (`enduse_fractions_table4.json:69-79`, `full_service_restaurant`): heat 0.12 + cool 0.07 + light 0.05 + equip 0.09 = **modeled_frac 0.33** → gross-up ×3.03. **QuickServiceRestaurant maps to `full_service_restaurant`** (`archetype_map`, line 135).
- **Mid-rise apartment fractions** (`:113-123`): heat 0.28 + cool 0.11 + light 0.08 + equip 0.22 = **modeled_frac 0.69** → gross-up ×1.45; `swh_dhw` assumed **0.23**. RESULT_6 (RECS 2020) measured MF DHW ≈ **0.33**.
- **Mapping is lossy:** `MediumOffice`, `Courthouse`, `Tall/SuperTallBuilding`, `OpenUBEMUnknown` all map to `large_office`; `Outpatient`→`hospital` (`archetype_map`).
- **Reconstruction reads each cell's `runtime/ubem_validation/cases/<cell>/results/05_results.gpkg`** (`service_loads.py:137`) and drops geometry only — it does **not** add or drop attribute columns.
- **V17 modeled medians (reconstructed total, kWh/m²):** NYC office 183.3 (meas 183.9, −0.3 %); LA office 208.9 (meas 121.5, +72 %); restaurants +110/+160 % vs ESPM; supermarket +2 % (validated); multifamily +32–34 % all cities.
- **Observed anomaly (manager ran this):** for the **identical office archetype**, simulated lighting+equipment EUI medians are NYC **19.1** vs LA/Austin **57.2** kWh/m² (3×). In `r7_service_loads.csv` the input columns (`lighting_w_m2`, `vintage_standard`, setpoints) are **populated for NYC rows but NaN for LA/Austin rows**, while the energy-output columns are populated for all three.

---

## 3. Deliverables (file layout)

```
scripts/diagnostics/v18_calibration_diagnosis.py     ← NEW, read-only analysis
docs/validations/overAll/V18_calibration_diagnosis.md ← NEW, narrative findings
docs/validations/overAll/results/v18_la_enduse_gap.csv      ← NEW
docs/validations/overAll/results/v18_grossup_check.csv      ← NEW
openubem/outputs/v18_*.png                            ← OPTIONAL figures only
```

---

## 4. Task list

### D01 — Reproduce the three V17 gaps (anchor)
- **What:** From `r7_service_loads.csv` (success rows), reproduce the V17 headline numbers: per-city reconstructed-total medians (NYC/LA/Austin), and per-archetype reconstructed-total medians for Office (Small+Medium+Large), Multifamily (Midrise+Highrise), FullService/QuickService Restaurant, Supermarket, Warehouse.
- **Why:** Establish the diagnostic baseline matches V17 §3–4 before analysing causes. Guards against analysing a stale file.
- **How:** city = `cell.str.split('_').str[0]`. Use the median of `total_eui_reconstructed_kwh_m2`. Print a table; assert NYC office ≈183, LA office ≈209 (±2). If they don't match V17, STOP.
- **How to test:** values reproduce V17 within ±2 kWh/m².

### D02 — LA-hot end-use decomposition
- **What:** Decompose the LA office +72 % gap (and the LA city +40 % gap) into the four simulated end-uses. For Office across NYC/LA/Austin, tabulate median heating/cooling/lighting/equipment EUI and the reconstructed total. Quantify how much of the LA-vs-NYC office difference is cooling (climate, expected) vs lighting+equipment (not climate-driven → suspect). Repeat the lighting+equipment cross-city check for Multifamily and Retail.
- **Why:** V17 §3 flagged LA as P1 but did not separate "real climate response" from "input artifact." Lighting/plug EUI must not vary 3× by climate for one archetype.
- **How:** group by city; emit `v18_la_enduse_gap.csv` with columns [archetype_group, city, heat, cool, light, equip, sim_total, recon_total, n]. Compute, per archetype group, the lighting+equipment ratio LA/NYC and Austin/NYC.
- **How to test:** CSV written; the office lighting+equipment 3× gap (NYC 19 vs LA/Austin 57) is confirmed or refuted with numbers.

### D03 — Input-provenance trace (load-bearing) — **STOP-AND-REPORT after this task**
- **What:** Determine **why** the input columns are NaN for LA/Austin but populated for NYC, and whether the *actually-simulated* lighting/equipment/setpoint/vintage inputs differ by city for the same archetype. (1) Open `runtime/ubem_validation/cases/<cell>/results/05_results.gpkg` for one NYC, one LA, one Austin cell; list which attribute columns each carries. (2) If the input columns are absent from the LA/Austin gpkgs, the blank-column issue is a **per-cell pipeline-output difference**, not a reconstruction bug — state that. (3) Cross-check the real lighting/equipment power density and schedule that EnergyPlus used for an office building in each city: inspect the generated IDF under `runtime/ubem_validation/cases/<cell>/idf/` (or the semantic-enrichment output the cell carries) for `Lights`, `ElectricEquipment`, and thermostat objects. Compare W/m² and schedule between a NYC office and an LA/Austin office.
- **Why:** This is the fork that decides whether "LA runs hot" is a **config/input inconsistency** (different LPD/schedule/vintage assigned per city — a fixable bug, possibly no resim if the inputs are right and only the CSV is lossy) or a **genuine model-physics calibration need** (inputs are consistent; LA really simulates hot → resim required to fix).
- **How:** read-only `geopandas`/text inspection. Do not modify any gpkg or IDF. Report the LPD/EPD/schedule/vintage actually applied per city in a small table.
- **How to test:** a 3-row (NYC/LA/Austin) table of applied office LPD, EPD, lighting schedule id, vintage; plus an explicit one-line verdict: "blank columns = {results-plumbing artifact | genuine input divergence}."

### D04 — Restaurant / food-service gross-up diagnosis
- **What:** Show quantitatively where the ×3 gross-up breaks. For each archetype with measured anchors (RESULT_5 ESPM/CBECS), compute: simulated 4-end-use base (median), `modeled_frac` (from Table-4), implied `E_total_est = base/modeled_frac`, measured total, and the implied **true** modeled fraction `base / measured_total`. Flag archetypes where assumed `modeled_frac` and implied true fraction diverge by >0.15. Specifically resolve whether restaurants overshoot because (a) `modeled_frac` (0.33) is too low vs the implied true fraction, (b) the simulated base itself is too high, (c) QSR borrowing FSR fractions, or (d) the divide-method is structurally unsuited to cooking-dominated types.
- **Why:** V17 §5 showed fractions are directionally right (supermarket +2 %) yet restaurants explode — the cause must be pinned to one of the four mechanisms before any fix is scoped.
- **How:** emit `v18_grossup_check.csv` with columns [archetype, mapped_to, sim_base_median, modeled_frac_assumed, E_total_est, measured_total_espm, implied_true_frac, frac_divergence, verdict]. Use ESPM medians from RESULT_5 §"Quick-Reference Summary"; where ESPM unavailable use CBECS mean and label it.
- **How to test:** CSV written; restaurant rows carry an explicit (a/b/c/d) root-cause label backed by the numbers.

### D05 — Multifamily gross-up diagnosis
- **What:** Same treatment for `mid_rise_apartment` (modeled_frac 0.69, ×1.45). NYC MF base ≈208, recon 302, measured 226. Determine whether the overshoot comes from the base being too high or the assumed service split (swh_dhw 0.23 vs RECS 0.33) inverting the gross-up. Note the direction paradox: our DHW fraction is *lower* than measured yet the total *overshoots* — explain why (i.e., if real MF buildings have a higher modeled-fraction / lower service share than Table-4 assumes, dividing by 0.69 still over-inflates).
- **Why:** Multifamily is ~2,850 buildings (high stock weight); the fix must target the right lever.
- **How:** add MF rows to `v18_grossup_check.csv`; compare implied_true_frac (base/measured 208/226 = 0.92) against assumed 0.69.
- **How to test:** MF row shows implied_true_frac ≈0.9 vs assumed 0.69, with a one-line explanation of the overshoot.

### D06 — Synthesis & fix-class assignment — **STOP-AND-REPORT after this task**
- **What:** Write `V18_calibration_diagnosis.md`. For each of the three gaps (LA-hot, restaurant, multifamily) assign exactly one **fix class**: `{code/config bug | reconstruction-method limitation | genuine calibration (resim required)}`, cite the D02–D05 evidence, name the minimal lever, and state **whether the fix requires EnergyPlus resimulation** (the governance gate). End with a prioritized, resim-flagged recommendation table.
- **Why:** Converts diagnosis into an actionable, governance-aware decision for the manager/user — which fixes can proceed under the current no-resim rule and which need the rule lifted.
- **How:** one section per gap (Evidence / Root cause / Fix class / Resim? / Minimal lever) + a closing recommendation table. No code changes proposed in diffs — describe the lever, do not write the fix.
- **How to test:** every gap has a fix class and an explicit Resim? yes/no; the report cross-references D02–D05 outputs.

---

## 5. Stop-and-report points

- **After D03** — the input-provenance trace. This decides bug-vs-calibration for the P1 LA gap; a wrong call here mis-scopes everything downstream. Report the per-city LPD/schedule/vintage table and the blank-columns verdict before continuing.
- **After D06** — full synthesis. Report the fix-class table for manager audit.

---

## 6. Progress log

_(Executor appends one entry per completed task: artifacts, deviations + cite, test status, notes.)_

#### D01 — Reproduce the three V17 gaps (anchor) — completed 2026-06-17
- Artifacts: `scripts/diagnostics/v18_calibration_diagnosis.py` (D01 block); no CSV (D01 is print-only per plan)
- Deviations: `OFFICE_IDS` excludes `OpenUBEMUnknown` — V17 §3 NYC=183.3 reproduced only without it (650 high-EUI unknowns inflate the all-cities median to 198.7 if included). Plan §2 lists OpenUBEMUnknown under office archetype_map, but V17 §6 explicitly calls Unknown a *classification gap*, not an office variant. Exclusion recovers NYC=182.9 ≈183.3 ±2 and LA=209.0 ≈208.9 ±2.
- Test status: assertion `abs(office_nyc - 183) <= 2` PASS (182.9); `abs(office_la - 209) <= 2` PASS (209.0)
- Notes: Per-city reconstructed medians: NYC 246.9, LA 158.6, Austin 199.8 kWh/m²; multifamily medians: NYC 302.0, LA 153.3, Austin 275.6; restaurant medians: NYC 2188, LA 1401, Austin 3290 (food-service archetypes confirmed wildly overshot)

#### D02 — LA end-use decomposition — completed 2026-06-17
- Artifacts: `docs/validations/overAll/results/v18_la_enduse_gap.csv` (9 data rows, 3 archetype groups × 3 cities)
- Deviations: none
- Test status: CSV written (10 lines incl. header); office lighting+equipment LA/NYC ratio = **2.78×** confirmed (NYC 20.56, LA/Austin 57.21 kWh/m²). The 3× gap cited in plan §2 is confirmed at 2.78× after excluding OpenUBEMUnknown.
- Notes: The 2.78× gap is shared identically by LA and Austin — both show 57.21 kWh/m² lighting+equipment median, while NYC shows 20.56. This is the critical diagnostic signal for D03. Multifamily and Retail show opposite patterns (LA<NYC for MF; LA≈Austin>NYC for Retail), so the gap is office-specific and climate-city-agnostic (LA and Austin behave identically despite different climates).

#### D03 — Input-provenance trace — completed 2026-06-17 [SUPERSEDED by correction below]
- Artifacts: `scripts/diagnostics/v18_calibration_diagnosis.py` (D03 block; IDF inspection read-only); no new CSV (D03 verdict is narrative per plan)
- Deviations: none
- Test status: 3-row IDF table produced; one-line verdict stated. All runtime paths present; no missing paths.
- Notes: **blank columns = results-plumbing artifact.** NYC `05_results.gpkg` carries 70 columns; LA/Austin carry 21 columns. IDF inspection confirms LPD=EPD=10.76 W/m² for all three cities; schedules identical. **The 2.78× lighting+equipment EUI gap is NOT an input-spec divergence.** ORIGINAL CONCLUSION (WRONG): attributed the gap to "per-footprint normalization / building height, physically correct." See correction entry below.

#### D03 — Correction applied 2026-06-17
- **This entry supersedes the wrong conclusion above. History preserved per plan instructions.**
- Artifacts: `scripts/diagnostics/v18_calibration_diagnosis.py` (D03 CORRECTED block); no new CSV
- Deviations from original: corrected root cause per manager instruction — previous executor compared different archetypes across cities (SuperTallBuilding NYC vs MediumOffice LA vs LargeOffice Austin) and concluded "physically correct height normalization." That is refuted.
- Corrected finding (two-part):
  - **(1) Blank columns = results-plumbing artifact** [UNCHANGED AND CORRECT]: NYC gpkg 70 cols (full semantic passthrough), LA/Austin gpkg 21 cols (stripped schema). Not a reconstruction bug.
  - **(2) Cross-city lighting/equipment EUI gap = single-zone IDF + parser normalization mismatch [NEW]:** All three cities use identical schedule (`Lighting_Schedule_MediumOffice`) and LPD/EPD=10.76 W/m² (verified by direct IDF reads for NYC 1-floor, NYC 4-floor, LA 1-floor MediumOffice IDFs). Single-zone IDFs simulate only the footprint (ground floor). The results parser (`parser.py` L191-204) divides energy by `footprint_area × levels`. For a 4-floor NYC single-zone building this divides by 4× the simulated area → EUI = 33.8/4 = 8.45. Proof: for all NYC single-zone MediumOffice buildings, `lighting_eui × levels` = 33.80 exactly (constant to 4 decimal places), Corr(light_eui, 1/levels) = 0.63. Same archetype, same floor count → IDENTICAL EUI across cities (LargeOffice level=5: NYC 35.13, LA 35.03, Austin 33.80). The aggregate cross-city gap is a stock-composition artifact: NYC stock has higher median floor counts (MediumOffice median 4 floors vs LA 3, Austin 2). This is NOT a schedule difference and NOT physically correct — it is a reporting-layer normalization design choice that conflates building label floors with simulated floor area.
- Fix class: **Code/config bug** (reporting layer) — Resim? **No**
- Test status: per-level EUI table produced; IDF schedules and LPD confirmed identical across cities

#### D04 — Restaurant gross-up diagnosis — completed 2026-06-17
- Artifacts: `docs/validations/overAll/results/v18_grossup_check.csv` (4 archetype rows: FSR, QSR, MidriseApt, HighriseApt); `scripts/diagnostics/v18_calibration_diagnosis.py` (D04 block)
- Deviations: plan calls for including Supermarket as control row; Supermarket row is omitted from grossup_check.csv because `sim_base_4eu` for Supermarket could not be cleanly separated from refrigeration (Supermarket maps to a refrigeration-heavy fraction; the sim_base includes equipment that is partly refrigeration-adjacent). The Supermarket control verdict (+2% validated) is documented in V17 §4 and referenced in V18 D06 report. The four rows that are present carry explicit a/b/c/d root-cause labels per plan.
- Test status: CSV written (5 lines incl. header); FSR verdict = "(a)+(b)"; QSR verdict = "(b)+(c)"
- Notes: FSR sim_base = 712.3 kWh/m2 (2.03× PNNL 4EU expected of 351); implied_true_frac = 0.693 vs assumed 0.33. QSR sim_base = 1091.6 (2.10× PNNL expected); implied_true_frac = 0.859. Root causes: (a) assumed modeled_frac=0.33 is 2× below implied true, (b) simulation base inflated ~2×, (c) QSR borrows FSR fractions incorrectly.

#### D05 — Multifamily gross-up diagnosis — completed 2026-06-17
- Artifacts: MF rows added to `v18_grossup_check.csv` (MidriseApartment, HighriseApartment rows); `scripts/diagnostics/v18_calibration_diagnosis.py` (D05 block)
- Deviations: plan asks for MF rows in grossup_check; done. Plan also specifically asks for NYC numbers; reported in script output and V18 report.
- Test status: MidriseApartment implied_true_frac = 0.84 (all-city), 0.921 (NYC specific) vs assumed 0.69 — matches plan's expected "≈0.9 vs assumed 0.69"
- Notes: Direction paradox resolved — higher real DHW share would worsen the gross-up, but the root cause is the NYC 4EU base being 92% of measured already. The Table-4 0.69 assumption is calibrated to national US average MF stock, not heating-dominated NYC stock.

#### D06 — Synthesis report written — completed 2026-06-17
- Artifacts: `docs/validations/overAll/V18_calibration_diagnosis.md`
- Deviations: none
- Test status: all three gaps have explicit fix class and Resim? assignment; recommendation table present; D02-D05 outputs cross-referenced
- Notes: The corrected D03 changes the fix class for the LA office gap from "genuine calibration (resim required)" to "code/config bug (no resim)." This is the governance-relevant finding: LA can be partially fixed without lifting the no-resim rule. Restaurants require partial resim (base inflation). Multifamily is a reporting fix only.
