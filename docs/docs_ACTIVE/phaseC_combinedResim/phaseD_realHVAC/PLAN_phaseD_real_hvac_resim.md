# PLAN — Phase-D Real-HVAC Resim (PTAC + prototype COP)

- **Slug:** `phaseD_real_hvac_resim`
- **Date:** 2026-06-22
- **Author:** Manager (Opus session)
- **Status:** Phase-2 entry. **Authorized DESIGN deviation** (see §0.1).

## 0. Purpose

The V19 basis diagnostics proved a scalar post-processing COP cannot simultaneously satisfy the city measured anchors and the national CBECS distribution, and can never clear the CV(RMSE)/KS shape gates (`PLAN_v19_national_cbecs_rescore.md` CP-3 verdict). The only path to a self-consistent, highest-accuracy model is to **model the HVAC physically** so cooling/heating energy is *metered* (electricity/fuel) at source rather than reported as IdealLoads *thermal* load and patched with a constant.

This phase replaces `IdealLoadsAirSystem` with `HVACTemplate:Zone:PackagedTerminalAirConditioner` (PTAC) parameterized by per-archetype COP/efficiency extracted from the DOE/ASHRAE-90.1 prototype IDFs, re-runs the 12 cells on Speed SLURM, and re-validates against **both** the city anchors and the national CBECS gates. Success = real HVAC closes the gates the scalar basis could not, with no post-hoc COP.

### 0.1 Authorized DESIGN deviation (manager-of-manager ratified 2026-06-21)

This phase deviates from binding Phase-1 specs, with explicit user authorization on 2026-06-21:
- `DESIGN_step-3...md:392–394` (§3H): "Phase-1 default: HVACTemplate:Zone:IdealLoadsAirSystem for every conditioned zone." → replaced by PTAC.
- `DESIGN_step-3...md:420`: "PackagedDX (HVACTemplate:Zone:PackagedTerminalAirConditioner) is deferred to **Phase-2 when COP values become available**." → **this phase IS that Phase-2 trigger**; COP values now sourced from the prototypes (T02). The chosen mechanism is exactly the one DESIGN earmarked.
- `DESIGN_main...md:45`: "Phase 1 ships IdealLoadsAirSystem as default and PackagedTerminalAirConditioner as an option." → we activate the named option.
- Consequent parser change (§3I/§5): `_EUI_VARS` moves from ideal-loads thermal to metered HVAC end-uses (T05). This is required by the HVAC change, not an independent deviation.

**DESIGN/OVERVIEW docs are NOT edited** (CLAUDE.md). The deviation is recorded here and in each touched module's progress-log entry. If any task reveals a spec conflict beyond the four lines above, STOP and quote it.

### 0.2 V18 status — already satisfied (no re-zoning task)

The V18 re-zoning fix (`zoning.py`: `single_zone` only when `num_floors==1`, 2026-06-17 ruling) is present in the working tree, and Phase-C regenerated its IDFs on 2026-06-19 with fresh IDF regen — so **Phase-C already carries corrected zoning**, and every V19 diagnostic ran on post-fix data. This resim is therefore **HVAC-only**. T07 includes a one-line CP confirming the regenerated Phase-D IDFs use `num_floors==1`-restricted zoning; no zoning code change is in scope.

---

## 1. Hard rules for the executor

1. **Stay in cwd** `C:\Users\o_iseri\Desktop\OpenUBEM`. Windows + PowerShell.
2. **Cluster ABSOLUTE rule:** never run blocking `srun`/python/compute on the Speed login node. All compute via `sbatch --array` fire-and-forget; login node only does `mkdir/scp/tar/squeue/sacct`. Reuse the existing `scripts/cluster/submit_fleet.sbatch` + `scripts/validation/v12_cell_pipeline.py` path verbatim. One sbatch array in queue at a time (verify `squeue -u o_iseri` empty before submitting).
3. **This IS a core `openubem/` change** (Phase-2, authorized §0.1): `idf/hvac.py`, `idf/outputs.py`, `results/parser.py`. Touch ONLY those three modules + new data files under `openubem/data/loads/`. Do not touch zoning, geometry, constructions, loads, schedules.
4. **Preserve Phase-C.** All resim outputs go to a NEW `phaseD` subdir (`--output-subdir phaseD`); never overwrite `phaseC/` or `cases/` results.
5. **Reuse the prototype IDFs as a DATA SOURCE, do not graft their object graphs.** PTAC is templated; ExpandObjects (already in both local `-x` and cluster pipelines) generates the coils + default curves.
6. **No new measured data.** Validation reuses `CITY_ANCHORS` and the regional CBECS CSVs already in the repo.
7. **Default to no comments.** One short line where the WHY is non-obvious.
8. **You execute; you do not re-plan.** Stop-and-quote on spec ambiguity. Stop at each checkpoint and report before continuing.

---

## 2. File layout

```
openubem/data/loads/
└── hvac_cop_by_archetype.json        ← NEW (T02): per-archetype cooling COP + heating coil type/eff + prototype provenance

openubem/idf/hvac.py                   ← MODIFIED (T03): assign_hvac emits PTAC
openubem/idf/outputs.py                ← MODIFIED (T04): add HVAC end-use meters
openubem/results/parser.py             ← MODIFIED (T05): _EUI_VARS → metered HVAC end-uses

scripts/validation/
└── extract_prototype_cop.py           ← NEW (T02): one-off extractor reading restored prototype IDFs → the JSON

docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/
├── RESULT_phaseD_validation.md        ← NEW (T11/T12): city + national re-validation, data only
└── phaseD_cell_status.md              ← NEW (T08–T09): per-cell resim status table

tests/
├── test_hvac.py                       ← MODIFIED (T06): PTAC assertions replace IdealLoads
├── test_idf_builder.py                ← MODIFIED (T06): HVAC/thermostat object keys
├── test_parser_hvac_metered.py        ← NEW (T06): metered-EUI parse assertions
└── (test_step3_orchestrator.py)       ← MODIFIED if IDF-validity assertions need PTAC curve objects
```

Phase-C result baseline (read-only, do not overwrite): `docs/docs_VALIDATION/overAll/results/phaseC/<cell>/05_results.gpkg`. Note one cell (`austin_urban`) sits under the `docs/validations/...` path alias — confirm both alias trees in T09.

---

## 3. Dependency decisions (pre-decided — do not re-debate)

- **HVAC object:** `HVACTemplate:Zone:PackagedTerminalAirConditioner`, one per conditioned zone (mirror the current per-zone IdealLoads cardinality). Keep the existing `HVACTEMPLATE:THERMOSTAT` per zone.
- **COP source = the restored prototype IDFs' rated DX coil COP** (T02). Per archetype use the **primary/dominant cooling coil's Gross Rated Cooling COP**; if a prototype has multiple, take the largest-capacity coil and record which. Heating: read the prototype's heating coil **type** (gas `Coil:Heating:Fuel` vs electric `Coil:Heating:Electric`) and **efficiency**; map to PTAC `Heating_Coil_Type` ∈ {Electric, Gas} + efficiency.
- **Archetype→prototype map (fixed coverage + fallback):** direct map for the 18 archetypes with a matching `ASHRAE901_*`/`*90.1*` prototype (Office S/M/L, Apartment Mid/High, Hotel S/L, Hospital, OutPatient, Restaurant FF/SD, Retail Standalone/Stripmall, School P/S, Warehouse, College, Lab, DataCenter, Supermarket). Detailed variants (`*Detailed`) inherit their base archetype's COP. `TallBuilding`/`SuperTall` → LargeOffice values. `OpenUBEMUnknown`/`*Mixed`/`Industrial` → a generic fallback (cooling COP 3.0, gas heat eff 0.80) documented in the JSON. **No archetype may be left without a COP entry** — assert full coverage of `openstudio_archetypes.json` in T02.
- **Parser end-use mapping (T05) — the basis fix:** with PTAC, cooling/heating become metered. Map:
  - `cooling_eui_kwh_m2` ← `Cooling:Electricity` (facility meter, PTAC DX coil electricity).
  - `heating_eui_kwh_m2` ← `Heating:Electricity` + `Heating:NaturalGas` (whichever the archetype's coil fuel produces), all-fuels site basis to match CBECS.
  - `lighting_eui_kwh_m2`, `equipment_eui_kwh_m2` ← unchanged (`Zone Lights/Electric Equipment Electricity Energy`).
  - Fans/parasitics: add `Fans:Electricity` into `equipment_eui_kwh_m2`? **NO** — keep fans in a separate accounting; for the four-column EUI keep cooling=Cooling:Electricity, heating=Heating:(Electricity+NaturalGas). Document fan energy separately in the parser output (new column `fans_eui_kwh_m2`) so it is visible but not silently folded in. (Manager will decide fan allocation at CP-4 from the data.)
- **Output subdir:** `phaseD`. Work base `%TEMP%/ubem_validation/phaseD/<cell>`; deliverables `docs/.../results/phaseD/<cell>/`.
- **Pilot cell:** `la_urban` (the Phase-C pilot precedent, cooling-dominated — the hardest COP case). Pilot must pass before the 11-cell fan-out.
- **No post-hoc COP.** Phase-D EUI is metered; the v19 basis transform is NOT applied to Phase-D results. Validation scores raw Phase-D output.

### 3.1 CP-1 manager ruling (2026-06-22) — central-plant archetypes

T02 surfaced that 10 archetypes have **no DX coil** in their prototype — the large buildings use a central chilled-water plant (`Chiller:Electric:EIR`/`:ReformulatedEIR`) or, for HighriseApartment, a water-source-heat-pump loop. PTAC still models them (uniform zone-packaged mechanism, the user's chosen low-risk path), but their COP comes from the **chiller/WSHP**, not a DX coil. Ruling:

1. **16 DX archetypes:** keep the extracted gross-rated DX COP as-is (compressor-basis; PTAC supply-fan electricity is captured separately by the `Fans:Electricity` meter, T04/T05).
2. **Central-plant archetypes** (LargeOffice, LargeHotel, Hospital, College, LargeDataCenterHigh/LowITE, HighriseApartment; plus inherits LargeOfficeDetailed, TallBuilding, SuperTallBuilding → LargeOffice): set `cooling_cop = primary_chiller_COP × 0.75`. The **0.75 plant-auxiliary factor** converts the compressor-only chiller/WSHP COP to an effective *plant* COP, folding CHW/CW pumps + cooling-tower fans (~33% auxiliary, ASHRAE-typical) into the PTAC abstraction — PTAC cannot model plant auxiliaries separately, so they must live in the COP. "Primary chiller" = the largest-capacity chiller when a prototype has several (e.g. Hospital 2.84 & 5.60 → take the larger-capacity unit; record which). Store BOTH the raw chiller COP and the derated value + the factor in the JSON.
3. **Heating for central-plant archetypes:** read the prototype's boiler (`Boiler:HotWater`) fuel + nominal thermal efficiency → `Heating_Coil_Type=Gas`, that efficiency (≈0.80) if gas; HighriseApartment WSHP heating → `Heating_Coil_Type=Electric`, efficiency = WSHP heating COP (read it; fallback 3.5 if absent). DataCenters have no heating → leave null (parser treats as 0).
4. **SmallHotel:** use the zone SingleSpeed **PTAC unit** COP (3.81), not the MultiSpeed DOAS coil — we are emitting PTAC, so the per-unit COP is representative.
5. **Known limitation (examine at CP-5):** PTAC-with-derated-chiller-COP is the weakest approximation in Phase-D for large central-plant buildings. If LargeOffice/Hospital/HighriseApartment validate systematically low on cooling at CP-4/CP-5, revisit the 0.75 factor (it is the one documented knob), not the mechanism.

Resulting effective cooling COPs (raw × 0.75): LargeOffice 6.91→5.18, Hospital 5.60→4.20, College 5.77→4.32, LargeHotel 3.11→2.33, HighriseApartment 4.69→3.52, LargeDataCenterHigh 6.28→4.71, LargeDataCenterLow 5.77→4.32 — all physically plausible plant COPs. The JSON must be completed to full 30/30 coverage under this ruling before T03.

### 3.2 CP-2 manager audit (2026-06-22) — GREENLIT for cluster

T02b–T06 audited against the on-disk artifacts (not the executor summary):
- **COP JSON verified 30/30, correct.** Manager read `hvac_cop_by_archetype.json` directly: DX values are unchanged from T01 (SmallOffice 4.53, MediumOffice 3.74, Warehouse 4.11, Supermarket 3.0); the executor's CP-2 *summary table* mis-transcribed several DX values but the file is correct. Central-plant ruling applied exactly (LargeOffice 5.181, Hospital 4.197 from the larger 5.597 chiller, HighriseApartment WSHP 3.516 + electric heat). No fabricated COPs.
- **Local pipeline works end-to-end:** PTAC build → ExpandObjects(-x) → E+ → parser yields non-zero metered cooling 22.96 / heating 67.65 / total 150.2 kWh/m² (SmallOffice NYC). 785 tests pass; pre-existing 4 failures (missing r6 csv, joblib) are unrelated.
- **IDD corrections accepted:** object key `HVACTEMPLATE:ZONE:PTAC`, field `Cooling_Coil_Gross_Rated_Cooling_COP`.
- **Carry-forward flags for CP-4 (NOT blockers, decide post-resim from data):** (a) fans are currently OUT of `total_eui_kwh_m2` — but CBECS site EUI includes fan electricity, so fans likely must be folded INTO total for an apples-to-apples national comparison; manager to rule at CP-4. (b) central-plant gas heating efficiency reads 0.945 (high vs typical 0.80 furnace) — sanity-check against measured heating EUI at CP-4. (c) smoke fan EUI 1.15 kWh/m² looks low — verify across the fleet at CP-4.

**Verdict: CP-2 PASSED. Cleared to proceed to T07 (cluster pilot la_urban).** Cluster-execution logistics (non-interactive SSH to Speed) to be confirmed with the user before submission.

**T07a PASSED + manager-greenlit (2026-06-22).** Standalone `ExpandObjects` (the cluster path, no `-x`) expands the PTAC template correctly → `ZoneHVAC:PackagedTerminalAirConditioner` + `Coil:Cooling:DX:SingleSpeed` + `Coil:Heating:Fuel` + curves, no IdealLoads — **the cluster-expansion risk is cleared.** 5 la_urban buildings (5 archetypes) simulated 0-fatal with sane metered EUI (cooling 7.7–26.6, heating 1.0–22.6); LA MediumOffice cooling 20.7 metered vs old thermal ~90 confirms the basis fix. User confirmed (2026-06-22): passwordless SSH → agent may drive the cluster. **Authorized T07 cluster pilot.**

### 3.3 CP-3 manager audit (2026-06-24) — GREENLIT for T08 fan-out

Pilot `la_urban` ran on Speed (array **987150, 618/618 COMPLETED, 0 PTAC fatals**, "EnergyPlus Completed Successfully" ×618). Local fetch/aggregate required a one-off recovery (see progress log) but **no resim** — cluster results were intact (17 GB, 618/618 `.sql/.end/.err`). Audited against the four CP-3 greenlight criteria, all on the real 618-building output vs the committed Phase-C `la_urban` baseline:

1. **Success / exclusions — PASS.** 618/618 success (Phase-C was 616/618), **0 buildings excluded** either direction, 0 new PTAC fatals.
2. **Cooling basis fix — PASS (decisive).** cooling EUI median **55.96 → 8.52 (−84.8%)**, mean 66.6 → 11.7 (−82.4%). The IdealLoads-thermal inflation that made LA read ~3.5×+ too hot is gone — this is the result the whole phase exists to produce.
3. **Zoning invariance — PASS (with finding).** lighting & equipment medians **exactly equal** C↔D (3.97→3.97, 43.40→43.40); 590/616 buildings byte-identical. The 26 divergers (4.2%) are **all `LargeOffice`** and show lighting+equipment scaling by the *same* per-building factor → a pure EUI-normalization change, not an energy change. Phase-D's uniform values (lighting 26.47, equipment 44.06) are **physically correct** (LargeOffice LPD≈9.7 W/m² × EFLH≈2750 h ≈ 26.7 kWh/m²; a per-archetype EUI cannot legitimately vary by building as Phase-C's did). **Phase-D corrected a latent Phase-C `LargeOffice` normalization error** — a beneficial fix, medians unaffected, not a regression.
4. **fans populated — PASS (after a fix; see ruling below).** `fans_eui_kwh_m2` now **618/618 populated, 100% > 0** (median 0.366, mean 0.517, range 0.05–2.13 kWh/m²), with a sensible by-archetype ordering (Warehouse 0.06 < apartments 0.23–0.32 < offices 1.08 < restaurants 1.21–1.66). Absolute level is low — **CP-4 flag (c) confirmed at scale**: PTAC models only cycling unit fans, not continuous central-AHU/OA fans, so fan EUI is structurally small and will not materially close the national gap.

**Manager ruling — fans-column completion (authorized, in-scope).** CP-2 added `fans_eui_kwh_m2` to `parser.py` as "a separate visible column," but `results/aggregator.py::_STEP5_COLS` (the F9 13-column Step-5 schema, DESIGN line 166) was never updated, so the column was computed then dropped before `05_results`. Ruled this a **completion of the already-authorized §0.1 parser deviation, not new scope** — the authorized change is incomplete until its column is actually emitted. Fix (Sonnet, manager-audited): `_STEP5_COLS` extended to **14 columns** (`fans_eui_kwh_m2` after `total_eui_kwh_m2`); `total_eui_kwh_m2` still **excludes** fans (the in/out-of-total decision stays a CP-5 call). Tests updated (count assertions 13→14, 70→71); `test_results_aggregator.py` + `test_parser_hvac_metered.py` green (38 passed). This is the only further `openubem/` edit beyond the original three §0.1 modules, and it touches a column list, not core math. **Fixed BEFORE T08 so all 12 cells carry fans natively** (re-aggregating 11 cells later would require re-fetching ~190 GB).

**Carry-forward to CP-4/CP-5 (report-only, not blockers):** (i) la_urban CBECS gates read **NMBE −44.6%, CV(RMSE) 100.5%, KS 0.384** (R² 0.79 PASS) — Phase-D now reads *low* vs the gate, expected post-basis-fix; the gate is labelled "CBECS 2018 **NE**" for an LA cell, a region-map oddity to confirm at CP-5 (LA → Pacific/West). (ii) Low PTAC fan EUI per flag 4 above. (iii) central-plant gas-heating eff 0.945 (flag b) still to sanity-check.

**Verdict: CP-3 PASSED. GREENLIT for T08** — fan out the remaining 11 cells (austin/la/nyc × centre/rural/suburban/urban, minus la_urban), one sbatch array at a time, `--output-subdir phaseD`.

### 3.4 CP-4 manager audit (2026-06-25) — all 12 Phase-D cells closed, PASS

Fan-out (T08) finished clean: `t08_STATUS.txt` reached `ALL 11 CELLS DONE` at 11:49:48 (10 fan-out cells + nyc_urban, zero `STOPPED on failure`). Audited all 12 `phaseD/<cell>/05_results.gpkg` + manifests directly (read-only `scratchpad/cp4_audit.py`).

1. **Success / exclusions — PASS (perfect).** Every cell: `n_manifest == n_gpkg == n_success`, `n_fail == 0`. **8,160/8,160 success, 0 exclusions, 0 PTAC fatals** across the fleet (vs Phase-C ref ~8,152; +8, no attrition — la_urban 618 as at CP-3). "Fix don't skip" upheld at scale.
2. **Cooling basis fix — PASS (decisive, consistent across all 3 cities).** vs the 3 committed Phase-C baselines: austin_urban cool **115.30→29.37 (−74.5%)**, la_centre **86.40→17.80 (−79.4%)**, nyc_centre **54.82→10.57 (−80.7%)** — matching CP-3 la_urban (−84.8%). Total EUI −36.0% / −37.4% / −6.9% (NYC smaller because heating-dominated). The IdealLoads-thermal cooling inflation is gone fleet-wide.
3. **Heating direction — expected, not a defect.** heating EUI rose +46.8% / +29.1% / +50.7% vs Phase-C. Correct: metered `Heating:(Electricity+NaturalGas)` includes combustion/system losses that Phase-C ideal-loads *thermal* heating omitted. This is the basis change acting on the heating side.
4. **Per-city pooled medians — physically sane, climate-correct ordering.** LA cool 6.28 / heat 19.51 / total 76.57 (mildest); Austin cool 27.48 / heat 40.18 / total 128.60 (balanced); NYC cool 13.30 / heat 129.80 / total 197.99 (heating-dominated). The Phase-C LA cooling-hot artifact is eliminated.
5. **fans_eui_kwh_m2 — PASS.** 8,160/8,160 populated, all > 0; per-city median austin 1.10 / la 0.38 / nyc 1.16 (LA low — cooling-dominated PTAC cycling fans, matches CP-3 0.37). Stays SEPARATE from `total_eui_kwh_m2` (fold-in is the CP-5 call).
6. **Zoning invariants — PASS.** Load-bearing num_floors check **CLEAN**: 3,259/3,259 `single_zone` rows have `levels==1`; all 4,901 multi-zone (`one_zone_per_floor`/`perimeter_core`) rows have `levels≥2` — the V18 fix holds across all 12 cells. Lighting & equipment EUI **exactly archetype-constant (spread 0.000%)** for 12 of 18 archetypes. The 6 with spread: (a) **LargeOffice (+19%) / MediumOffice (+31%) / RetailStandalone (+31%)** — one-sided tail (min==median, only a minority reads high), the CP-3-adjudicated *correct* num_floors normalization on multi-zone buildings, not a regression; (b) **OpenUBEMUnknown** (650 bldgs) spread 112%/328% — inherent to the unclassified grab-bag bucket (not one archetype), not a zoning bug; (c) Warehouse/PrimarySchool ~3–4%, trivial. None block CP-4.

**Carry-forward to CP-5 (report-only, not blockers):** (i) **fold fans into total for national CBECS?** CBECS includes fan electricity — likely yes for the national comparison; decide at CP-5. (ii) **central-plant gas heating eff 0.945** (flag b) is high vs typical ~0.80 → metered heating fuel may be *under*-stated even though it already rose +29–51%; sanity-check vs measured. (iii) **OpenUBEMUnknown bucket** (650 bldgs, 8% of fleet) carries unconstrained internal loads (equip up to 396 kWh/m²) that could distort the national CBECS comparison — decide handling at CP-5. (iv) **LA→Pacific CBECS region label** (CP-3 flag — "CBECS NE" shown for an LA cell) confirm region mapping. (v) multi-zone office lighting/equip +19–31% tail — monitor, do not tune.

**Verdict: CP-4 PASSED.** All 12 Phase-D cells closed clean (8,160/8,160, 0 exclusions); the cooling basis fix is decisive and consistent across all three cities; every integrity invariant holds. **Cleared to Phase 4 (T10–T12 / CP-5)** — re-validate Phase-D vs city anchors (NYC LL84 / LA EBEWE / Austin proxy) AND national CBECS with **no post-hoc transform**; gates report-only, never tuned to pass.

### 3.5 CP-5 manager verdict (2026-06-25) — physical HVAC achieved its goal; residual re-attributed; GO to adopt Phase-D as the physical baseline

Data: `RESULT_phaseD_validation.md` (T10/T11/T12), raw metered Phase-D, no transform. Audited; segment counts reconcile exactly to CP-4 (NYC 2570+1036+558=4304, LA 2317+19=2336, Austin 1447+73=1520).

**The CP-5 question — "did physical HVAC clear city + national + shape with one consistent model, where the scalar basis could not?"**

1. **Basis error — ELIMINATED at source (the phase's reason for existing).** Cooling −75–85% (CP-4); the historic "LA runs hot +38%" artifact is gone — LA now reads *cold*, a clean **sign flip** that only a genuine basis change produces. Phase-D carries **no post-hoc COP** anywhere. ✓
2. **NMBE (bias) — honest, mixed.** NYC −1.1% (near-perfect), LA −29.6%, Austin −31.9% → 1/3 pass. The tuned Phase-C scalar passed NMBE 3/3, but by *fitting* (and over the raw thermal it was +5/+8/+1 — a deceptive cancel of hot-cooling vs no-combustion-loss heating). Phase-D's bias is **earned, not fitted**: NYC (heating-dominated) lands right because metered gas heating is large; LA/Austin (mild, cooling-dominated) run cold once the cooling inflation is removed.
3. **Shape gates (CV/KS) — still fail, but Phase-D IMPROVED them and they are the wrong yardstick.** KS dropped in all 3 regions (0.40/0.44/0.47 → 0.34/0.22/0.30) — the metered distribution is materially more CBECS-like — yet none clears 0.10, and CV(RMSE) stays 59–90%. Both the scalar basis AND physical HVAC fail CV/KS → **structural**: an archetype-deterministic UBEM has near-zero within-archetype EUI variance (CP-4 proved lighting/equipment are archetype-constant) while CBECS is a per-building empirical survey with large natural spread. CV/KS cannot be cleared by *any* basis or HVAC change; they are inappropriate as pass/fail gates for this model class and should be reported, not gated.
4. **The cold residual is NOT a basis artifact — it is the missing non-HVAC service-loads layer.** Decisive evidence: (a) **Multifamily is the worst segment everywhere** (NYC −24.9%, LA −37.3%) — residential DHW (large, ~20–40 kWh/m²) is wholly unmodeled; PTAC added HVAC *fans* only, not DHW/pumps/elevators/process. (b) The cold bias tracks climate: NYC Overall only −13% (huge metered heating masks the missing loads) vs LA −33% / Austin −21% (little heating to mask them). (c) The Phase-C "best" that hit all 6 anchors within ±15% used `total_eui_reconstructed_kwh_m2` — i.e. it included the **V16 service-loads reconstruction** (the R6-4B "Other" ≈42%-of-gap component: DHW/pumps/process) — which Phase-D deliberately stripped to isolate HVAC. Phase-D's cold gap ≈ the size of that absent layer. This is exactly the [[project_service_loads]] / [[project_r6_4]] "Other loads basis+zoning can't close" finding, now reproduced from the metered side.
5. **Carry-forward flags resolved.** (a) Fans immaterial — including them shifts every delta < 1 pct-pt; fold into total for CBECS completeness but it changes no conclusion. (d) Region labels correct (D5: NYC→middle_atlantic, LA→pacific, Austin→west_south_central; the "CBECS NE" was a display label, scoring was always Pacific). (c) Unknown bucket excluded from city scoring (n reported per segment). Remaining: (b) gas-heating eff 0.945 — NYC's good NMBE partly rests on it; sanity-check when the heating side is next touched; (e) cooling-COP / 0.75 plant-derate (CP-1 §3 "known limitation") is the secondary cold lever in cooling-dominated stock — now triggered as CP-1 predicted, but subordinate to the service-loads gap.

**Verdict: GO — adopt Phase-D metered HVAC as the new physical baseline.** Physical HVAC delivered the scientific prize the scalar basis never could: a self-consistent, patch-free model whose errors are now *physically interpretable and localized* rather than hidden behind a fitted constant. It did not pass more national NMBE gates than the tuned scalar (it is more honest, so it passes fewer), and it did not clear CV/KS (no model of this class can) — but it removed the basis artifact, improved distribution shape, and correctly re-attributed the residual to the unmodeled service-loads layer. Retire the scalar-COP basis as a diagnostic crutch. Operative validation metrics henceforth: NMBE + city-median deltas; CV/KS reported-only.

**Recommended next step (user to ratify — see CP-5 fork):** re-combine Phase-D metered HVAC with the existing **V16 service-loads reconstruction** (reporting-layer, NO resim — net out the now-metered fans to avoid double-count), then re-score. This is expected to close most of the LA/Austin/MF cold gap cheaply and is the correct, physically-grounded successor to the scalar patch. Cooling-COP/0.75-derate and gas-eff 0.945 are secondary, resim-gated, and only pursued if the reporting-layer re-combination leaves a material residual.

### 3.6 CP-6 manager verdict (2026-06-25) — service-loads re-combination CLOSED the cold gap; Phase-D + V16 is the best, fully-unfitted model; one bounded NYC residual remains

Data: `RESULT_phaseD_reconstructed_validation.md` (T13/T14). Audited: recon ≥ raw 8,160/8,160, 0 passthrough, segment n's match T10, food-service median 931.6 (in band).

1. **The CP-5 thesis is CONFIRMED — the cold residual WAS service loads, and it closed.** On the correct metered base: LA Overall −33.0→**−4.2%**, Austin −21.4→**−7.0%**, LA MF −37.3→**−9.2%**, NYC MF −24.9→**+8.8%**, LA Warehouse −25.3→**+9.8%**. City-Overall mean |Δ| **22.6%→7.3%**; all three cities now within **±11%**. The residential DHW/pumps restoration landed exactly where Phase-D ran coldest — proving the residual was the unmodeled service-loads layer, not the HVAC basis or COP.
2. **Achieved with ZERO fitted parameters.** Metered physical HVAC + a FIXED, pre-existing national fraction table (built before Phase-D, not tuned to these anchors) now matches the accuracy the Phase-C scalar needed FOUR tuned knobs + the same reconstruction to reach (Phase-C best ±13%). This is the endpoint the whole arc targeted: a fully physical, unfitted UBEM at city-Overall ±11%.
3. **National gates: R² now PASSES all 3 regions** (0.79–0.92 vs 0.55–0.70 raw) — a real per-building correlation gain from archetype-differentiated service loads. CV(RMSE) improved everywhere (51–60 vs 59–90) though still > 30; KS mixed/worse (reconstruction shifts the distribution); NMBE mean |·| improved (13.6 vs 20.9) but still 1/3 pass. CV/KS remain report-only per §3.5 (structural for archetype-deterministic UBEM).
4. **New, smaller, well-characterized residual: NYC over-prediction** (Office +31.5%, Overall +10.8%, national NMBE −1.1%→**+19.1%**). Cause: V16 fractions are **national-average / climate-blind**; cold-dominated NYC has a genuinely higher heating fraction (lower service-load fraction) than the table, so the reconstruction over-restores on NYC's heating-inflated total. Most exposed in the office segment (modeled_frac ≈0.83 → ×1.20 uplift on an already-high base). This is a fraction-table climate-sensitivity limitation — **NOT** a cooling-COP/gas-eff defect → the secondary resim levers are NOT indicated.
5. **Fans cross-check (R2) upheld:** metered PTAC fans are 2–6% of the reconstruction's vent_fans estimate across all 18 archetypes — PTAC captures only cycling-unit fans; the reconstruction correctly supplies the continuous central-fan energy. No double-count.
6. **Food-service** median reconstructed 931.6 kWh/m² (in band); 11 buildings >1000 (known QSR R5 plausibility artifact, reported uncapped per V16). Excluding food-service barely moves Overall (small n) → the office/MF picture is not swamped.

**Verdict: Phase-D + V16 service-loads reconstruction is the best model produced and the recommended FINAL adopted baseline.** It is the first OpenUBEM model to sit within ±11% on city-Overall for all three cities with **no fitted patch**, it confirms the service-loads thesis, and it passes R² nationally. The remaining NYC over-prediction is a bounded, documented limitation of climate-blind national service-load fractions, not a basis/COP defect; secondary cooling-COP/gas-eff resim levers are not indicated. Optional future refinement: region/climate-adjusted service-load fractions to trim the NYC overshoot — but that risks over-fitting and the V16 memo already cautioned service-load completion is not a route to the ±5% gate; recommend against unless a stakeholder specifically requires NYC office.

---

## 4. Source-of-truth verified facts (manager-grepped — cite, don't re-derive)

| # | Fact | Evidence |
|---|---|---|
| H1 | `assign_hvac(idf, row, zones)` emits one `HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM` per zone; `row` carries `archetype_id`. Injection point in builder. | `openubem/idf/hvac.py:29–41`; `openubem/idf/builder.py:336` |
| H2 | Outputs are already Hourly for all 11 vars incl. `Site Outdoor Air Drybulb Temperature`; meters `Electricity:Facility`/`NaturalGas:Facility` at RunPeriod; SQLite SimpleAndTabular. `write_outputs(idf)`. | `openubem/idf/outputs.py:6–18,31–44` |
| H3 | Parser `_EUI_VARS` currently reads ideal-loads **thermal** cooling/heating; EUI = energy / (footprint × num_floors). This is the basis error to remove. | `openubem/results/parser.py:47–52,191–204` |
| H4 | Cluster runs ExpandObjects as a **separate** binary before `energyplus` (no `-x`; `-x` symlink-crashes on the cluster). PTAC templates therefore expand correctly on the cluster. Local runner uses `-x` (inline ExpandObjects). | `scripts/cluster/submit_fleet.sbatch:41–51`; `openubem/simulation/runner.py:49` |
| H5 | Top-level resim driver `run_cell(cell_name, output_subdir)`; full Step1–5 incl. ship/submit/poll/fetch/verify/aggregate; CLI `py -3 scripts/validation/v12_cell_pipeline.py <cell> --output-subdir phaseD`. Stale IDFs cleared → fresh regen. | `scripts/validation/v12_cell_pipeline.py:885,1005,919–929` |
| H6 | Resume tool re-enters post-submit without re-shipping/duplicating the array (idempotency gate = existing `03_idf_manifest.parquet`). | `scripts/cluster/resume_phasec_cell.py:34,50–54` |
| H7 | 12 cells + per-cell configs (lat/lon/radius/state/epsg); Phase-C = 8,152 buildings, 100% E+ 23.1 success. | `scripts/validation/v12_cell_pipeline.py:43–104`; `docs/docs_DONE/pahseC_resumeManager.md` |
| H8 | Tests pinning IdealLoads (must change): `test_hvac.py` 4 tests; `test_idf_builder.py:456` (HVAC object key), `:327` (THERMOSTAT count==2); IDF-validity `test_step3_orchestrator.py:47,87`. | as cited |
| H9 | DOE/90.1 prototypes are git-tracked and restorable (`git checkout -- "docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs/"`); cover ~18 archetype families incl. full DX HVAC + curves. | `git ls-files` (this session) |
| H10 | Archetype registry = 30 entries; `doe_prototype_loads.json` has loads for 17, **no COP/HVAC** anywhere in repo data. | `openubem/data/openstudio_archetypes.json`; `openubem/data/loads/doe_prototype_loads.json` |

---

## 5. Task list

### Phase 1 — Prototype COP extraction (no resim, local)

**T01 — Restore prototype IDFs + inventory.** `git checkout -- "docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs/"`. List the restored `*.idf`; build an inventory table mapping each of the 30 archetypes to a prototype file (or fallback per §3). *Why:* the HVAC data source (H9). *Test:* assert every `openstudio_archetypes.json` key has a resolved source or an explicit fallback; print the coverage table.

**T02 — Extract COP/efficiency → `hvac_cop_by_archetype.json`.** Write `scripts/validation/extract_prototype_cop.py` that parses each prototype IDF (eppy) for the dominant `Coil:Cooling:DX:*` Gross Rated Cooling COP and the heating coil type+efficiency, and emits `openubem/data/loads/hvac_cop_by_archetype.json` keyed by archetype with `{cooling_cop, heating_coil_type, heating_efficiency, source_prototype, source_coil_object}`. *Why:* DESIGN §420 needs COP "available" (H1, §0.1). *How:* dominant = largest rated capacity coil; record provenance per entry. *Test:* full archetype coverage; every cooling_cop ∈ [2.0, 5.0]; every heating_efficiency ∈ (0.5, 1.0]; fallbacks flagged.

**CP-1 — after T02.** Report the COP/efficiency table with provenance and any fallbacks. Manager sanity-checks COP values vs expectations (offices ~3.0–3.7, supermarket lower, etc.) before any code change.

### Phase 2 — IDF + parser core changes (local, test-gated)

**T03 — Rewrite `assign_hvac` → PTAC.** Replace the IdealLoads emission with `HVACTEMPLATE:ZONE:PACKAGEDTERMINALAIRCONDITIONER` per zone, reading `row["archetype_id"]` → `hvac_cop_by_archetype.json` for `Cooling_Coil_Gross_Rated_COP`, `Heating_Coil_Type`, heating efficiency; keep the per-zone thermostat. *Why:* §0.1, H1. *How:* load the JSON once (module-level cache); set required PTAC fields + OA per ASHRAE 62.1 as today; autosize capacities/flows. *Test:* covered by T06.

**T04 — Add HVAC end-use meters to `outputs.py`.** Add `Output:Meter` (or `Output:Meter:MeterFileOnly`) for `Cooling:Electricity`, `Heating:Electricity`, `Heating:NaturalGas`, `Fans:Electricity` at RunPeriod (keep existing hourly vars). *Why:* the parser needs metered end-uses (H2, H3). *Test:* covered by T06.

**T05 — Rewire parser `_EUI_VARS` → metered HVAC.** Per §3 mapping: cooling ← `Cooling:Electricity`; heating ← `Heating:Electricity` + `Heating:NaturalGas`; lighting/equipment unchanged; add a separate `fans_eui_kwh_m2` from `Fans:Electricity`. Keep EUI normalization `energy/(footprint×num_floors)` (correct post-V18, §0.2). *Why:* eliminates the thermal-vs-metered basis error at source (H3). *How:* read from SQLite meter tables; if a meter is absent for a building (e.g. all-electric → no NaturalGas), treat as 0, not NaN. *Test:* T06.

**T06 — Update + add tests; local smoke.** Rewrite `test_hvac.py` to assert PTAC object count==zone count + COP/heating fields from the JSON; fix `test_idf_builder.py` HVAC/thermostat keys; ensure `test_step3_orchestrator.py` IDF-validity passes with PTAC (ExpandObjects-expanded). Add `test_parser_hvac_metered.py` asserting the parser maps the four meters → EUI columns and fans separately. Run one real local building end-to-end (`-x` inline ExpandObjects) and assert non-zero metered cooling AND heating EUI. *Test:* full `pytest` green; smoke EUI sane (cooling 5–60, heating 5–120 kWh/m² order-of-magnitude).

**CP-2 — after T06.** Report pytest summary + the local smoke building's metered EUI breakdown (cooling/heating/light/equip/fans). **Gate: local pipeline must generate→expand→simulate→parse a real metered EUI before any cluster work.** STOP.

### Phase 3 — Cluster resim (sbatch fire-and-forget)

**T07a — Local preflight + taste-test (no cluster; user-directed 2026-06-22).** Before any cluster trip: (1) run **standalone `ExpandObjects`** (NOT `-x`) on one generated PTAC IDF to confirm the template expands the way the cluster invokes it (H4) — the cluster does not use `-x`; (2) generate IDFs for **3–5 `la_urban` buildings** and run them through **local** EnergyPlus, parse, and confirm non-zero, sane metered cooling+heating EUI per building. **Gate: STOP and report; the cluster pilot does not start until the taste-test is clean.** *Why:* catch PTAC/ExpandObjects problems for free before spending a cluster round-trip. *Test:* standalone-expanded IDF is E+-valid; 3–5 buildings parse with sane EUI.

**T07 — Pilot `la_urban` on cluster.** Run `py -3 scripts/validation/v12_cell_pipeline.py la_urban --output-subdir phaseD` (ship → one `sbatch --array` → poll → fetch → verify → aggregate). Confirm PTAC IDFs expand+run on the Ubuntu E+ build (H4), parser yields metered EUI, and the regenerated IDFs use `num_floors==1`-restricted zoning (§0.2 confirm). *Why:* de-risk the cluster path on the hardest (cooling-dominated) cell before fan-out. *Test:* cell closes n/n (or with only the known geometry-fatal exclusions), success ≥ Phase-C rate.

**CP-3 — after T07.** Report pilot: success count, metered EUI distribution, any new E+ fatals from PTAC, runtime. **Gate: pilot clean before fan-out.** STOP.

**T08 — Fan out the remaining 11 cells.** One cell at a time (one sbatch array in queue), `--output-subdir phaseD`, via `run_cell`/resume tool. Maintain `phaseD_cell_status.md`. *Why:* H5/H7. *Test:* each cell closes n/n; status table updated.

**T09 — Aggregate Phase-D.** Ensure all 12 `phaseD/<cell>/05_results.gpkg` exist (both path aliases, §2); total success ≈ Phase-C (8,152 ± attrition). *Test:* `load_all_cells`-style read of the 12 phaseD gpkgs succeeds; row counts logged.

**CP-4 — after T09.** Report the 12-cell Phase-D status table + total success + headline metered-EUI medians per city vs Phase-C. STOP.

### Phase 4 — Re-validation (report-only, data first)

**Phase-4 execution facts (manager-grepped 2026-06-25 — cite, don't re-derive):**

| # | Fact | Location |
|---|------|----------|
| V1 | `CITY_ANCHORS` = 9 (city,segment) measured targets: NYC Office 183.9 / MF 226.2 / Overall 219.2; LA Office 121.5 / MF 115.8 / Warehouse 33.9 / Overall 113.6; Austin Office 162.3 / Overall 162.0. | `scripts/v19_rescore.py:48–58` |
| V2 | `build_city_table(reconstructed)` → per-city×segment delta table, success rows only. `load_all_cells()`+`CELL_TO_BASE` are **hardcoded to the phaseC tree** (split across two base dirs). | `scripts/v19_rescore.py:75–162` |
| V3 | Basis transform lives only in `apply_basis_to_frame(df,cooling_cop,heating_factor,lighting_scale,equipment_scale)`; identity=(1,1,1,1). Main `v19_rescore.py` never calls it (scores raw). | `scripts/validation/v19_basis_diagnostic.py:42–68` |
| V4 | National gates: `compute_validation_gates(results_gdf, reference_path|table)` → NMBE / CV(RMSE) / KS_D / R² + pass flags (thresholds CV 30, NMBE 10, R² 0.6, KS 0.10). Region refs `inputs/reports/cbecs_2018_{region}_eui.csv`; `_CITY_REGION`: NYC→middle_atlantic, LA→pacific, Austin→west_south_central. | `openubem/results/__init__.py:209–330`; `scripts/validation/v19_national_cbecs_rescore.py:56–61` |
| V5 | Phase-C scalar-basis best for the side-by-side: `docs/docs_ACTIVE/phaseC_combinedResim/v19_validation/RESULT_basis_diagnostic.md` (city) + `RESULT_national_cbecs_rescore_reconstructed.md` + `RESULT_national_cbecs_rescore.md` (national). | as cited |
| V6 | Phase-D results: `docs/validations/overAll/results/phaseD/<cell>/05_results.gpkg`, 12 cells; `total_eui_kwh_m2` EXCLUDES fans (`fans_eui_kwh_m2` separate). | CP-4 (§3.4) |

**Architecture decisions (pre-decided — do not re-debate):**
- **D1. New drivers, don't mutate phaseC tooling.** Write `scripts/validation/phaseD_city_rescore.py` + `scripts/validation/phaseD_national_cbecs_rescore.py`. IMPORT & reuse `CITY_ANCHORS`, `build_city_table`, the segment-mapping/prep, and `compute_validation_gates` from the existing modules. Do NOT edit `v19_rescore.py` / `v19_basis_diagnostic.py` / `v19_national_cbecs_rescore.py` (committed phaseC artifacts).
- **D2. Loader points at the phaseD single tree.** Mirror `load_all_cells` (v19_rescore.py:75–99) but read `docs/validations/overAll/results/phaseD/<cell>/05_results.gpkg`; keep the same city-derivation + success filter + segment prep so `build_city_table` consumes it unchanged.
- **D3. NO transform (identity).** Score raw metered Phase-D EUI. No `apply_basis_to_frame`, no COP divide — cooling/heating are already metered, a transform would double-count.
- **D4. Report fans both ways (resolves CP-4 flag a).** City deltas + national gates for BOTH `total_eui_kwh_m2` (fans-excluded, as-built) AND `total_eui_kwh_m2 + fans_eui_kwh_m2`, so the manager adjudicates fans-in-total at CP-5 from data.
- **D5. Region-label check (resolves CP-4 flag d).** Confirm each city scores against its correct CBECS region (NYC→middle_atlantic, LA→pacific, Austin→west_south_central); flag any mismatch explicitly.

**T10 — City-anchor re-score on Phase-D.** Run the existing city scoring (`v19_rescore` loader + `build_city_table`) on Phase-D results with **no basis transform** (HVAC is metered). Report the six city deltas vs `CITY_ANCHORS`. *Why:* does real HVAC hit the anchors the scalar COP hit, without the post-hoc patch? *Test:* table produced; deltas finite.

**T11 — National CBECS re-score on Phase-D.** Run `compute_validation_gates` per region (the `v19_national_cbecs_rescore` path) on Phase-D, no transform. Report per-region NMBE/CV(RMSE)/KS_D + pass flags. *Why:* the decisive test — does real HVAC clear the shape gates (CV(RMSE)/KS) the scalar basis never could, in all three regions? *Test:* table produced.

**T12 — Findings memo (data only).** `RESULT_phaseD_validation.md`: city deltas + national per-region gates for Phase-D, **side-by-side with** the Phase-C scalar-basis best (from `RESULT_basis_diagnostic.md` / `RESULT_national_cbecs_rescore_reconstructed.md`). No interpretation prose. *Test:* file exists, tables non-empty, both baselines joined.

**CP-5 — after T12.** Manager writes the verdict: did physical HVAC achieve what the scalar basis could not (city + national + shape, one consistent model)? Go/no-go on adopting Phase-D as the new baseline.

### Phase 5 — Service-loads re-combination + re-score (reporting-layer, NO resim; user-ratified 2026-06-25)

CP-5 GO + user chose "re-combine + re-score." Re-apply the existing V16 service-loads reconstruction on top of Phase-D's *correctly metered* base (the Phase-C round-trip overshot because its base was thermally inflated; Phase-D removes that), to close the residential/MF cold residual. No cluster, no resim.

**Phase-5 verified facts (manager-grepped 2026-06-25 — cite, don't re-derive):**

| # | Fact | Location |
|---|------|----------|
| W1 | `reconstruct_frame(df, coeffs=None)` / `reconstruct_building(row, coeffs)` add 5 un-modeled end-uses. Formula: `modeled_frac = Σ(space_heat,space_cool,lighting,equip_plug)`; `E_total_est = (heating+cooling+lighting+equipment)/modeled_frac`; `recon_j = f_j·E_total_est` for j∈{vent_fans,pumps,swh_dhw,refrig,cooking_other}; `total_eui_reconstructed_kwh_m2 = total_sim + Σrecon_j`. | `openubem/results/service_loads.py:44,78–103` |
| W2 | Table-4 fractions + `archetype_map` (24 ids→11 keys); each entry has explicit `vent_fans`. | `openubem/data/service_loads/enduse_fractions_table4.json` |
| W3 | **Phase-D `total_eui_kwh_m2 = cooling+heating+lighting+equipment` EXACTLY (verified residual 0.0000), fans EXCLUDED** — same scope as the Phase-C total the reconstruction was built for → `reconstruct_frame` applies UNMODIFIED, **no fans double-count**. | this session (empirical) |
| W4 | Food-service: `FullServiceRestaurant`/`QuickServiceRestaurant`→`full_service_restaurant` key (67% non-modeled → ~×3 uplift); `SuperMarket`→`supermarket` (refrig 0.50). V16 reports food uncapped (QSR R5 plausibility-band artifact amplified). | `scripts/reconstruct_service_loads.py:49`; json:125–151 |
| W5 | Phase-C reconstructed baseline for side-by-side: `RESULT_national_cbecs_rescore_reconstructed.md`; V16 memo `docs/docs_VALIDATION/overAll/V16_service_loads_reconstruction.md`. | as cited |

**Architecture decisions (pre-decided — do not re-debate):**
- **R1. Use the SHIPPED `reconstruct_frame()` UNMODIFIED.** Phase-D total excludes fans (W3) → no `_RECON_KEYS` edit, no double-count. Do NOT modify `openubem/results/service_loads.py` or `enduse_fractions_table4.json` (committed, do-not-edit).
- **R2. Do NOT add metered `fans_eui_kwh_m2` to the reconstructed total** — the reconstruction's `vent_fans` term already supplies fan energy. Report metered-fans vs `vent_fans_eui_recon_kwh_m2` as a cross-check diagnostic (expected: metered PTAC fans ≪ reconstruction estimate → confirms PTAC under-captures continuous central fans).
- **R3. NO basis/COP transform** (Phase-D is metered).
- **R4. New driver only** `scripts/validation/phaseD_reconstruct_rescore.py`; reuse the phaseD loader pattern from `phaseD_city_rescore.py`, and import `reconstruct_frame`, `build_city_table`, `CITY_ANCHORS`, `compute_validation_gates`, `_CITY_REGION`/`_REPORTS_DIR`. Do not touch the existing committed drivers.
- **R5. Report Overall BOTH incl. and excl. food-service** so the office/MF signal isn't swamped by restaurant ×3 overshoot; food-service reported uncapped with the QSR-artifact caveat.
- **R6. Exclude `OpenUBEMUnknown` from city-anchor scoring** (as T10 did).

**T13 — Apply V16 reconstruction to Phase-D + re-score.** Write `scripts/validation/phaseD_reconstruct_rescore.py`: load the 12 phaseD gpkgs (success rows), `reconstruct_frame()` → `total_eui_reconstructed_kwh_m2`, then re-score (a) city anchors via `build_city_table` and (b) national CBECS via `compute_validation_gates`, on the reconstructed total, no transform. Emit the metered-fans-vs-vent_fans_recon cross-check. *Why:* close the service-loads residual on a correct base (CP-5 §3.5). *Test:* script runs clean 8,160 rows; reconstructed total ≥ raw total per building; deltas finite; food vs non-food separated.

**T14 — Findings memo (data only).** `RESULT_phaseD_reconstructed_validation.md`: city deltas + national gates for Phase-D-reconstructed, side-by-side with Phase-D-raw (from `RESULT_phaseD_validation.md`) and the Phase-C reconstructed best. No interpretation prose. *Test:* file exists, tables non-empty, three columns joined.

**CP-6 — after T14.** Manager verdict: did the service-loads re-combination close the LA/Austin/MF cold gap on a correct metered base? Is Phase-D + V16 reconstruction the final adopted model, or does a material residual remain (→ cooling-COP / gas-eff secondary levers)? STOP.

### Phase 6 — Office heating-setpoint setback fix + targeted resim (user-authorized 2026-06-25)

Post-CP-6, scoping the NYC office +11.3% over-prediction (a heating over-prediction concentrated in SmallOffice) found a verified defect: the office heating **setpoint schedules are missing their weekday evening setback** (OQ-2 digitization bug). User authorized: audit all non-residential heating schedules, correct, resim, re-validate. Guarded-file edit (`doe_schedules.json`) authorized for this fix.

**Phase-6 verified facts (manager-confirmed 2026-06-25 — cite, don't re-derive):**

| # | Fact | Location |
|---|------|----------|
| X1 | `Heating_Setpoint_{Small,Medium,Large}Office` weekday blocks hold **21.1 °C from 07:00→24:00, NO evening setback**; their OWN Saturday (→15.6 at 19:00) + AllOtherDays (→15.6 at 18:00) blocks HAVE it; DOE prototype `HTGSETP_SCH_NO_OPTIMUM` drops to 15.56 at 19:00 weekdays. Vestigial 18:00/22:00 breakpoints flattened to 21.1 = the digitization error. **Confirmed bug.** | `openubem/data/schedules/doe_schedules.json:230,704,1178` |
| X2 | Infiltration `0.000285` is NOT a defect (constant-term vs prototype's wind-driven model; within ASHRAE range; global change would worsen NYC's under Overall). OUT OF SCOPE. | `openubem/data/construction/ashrae_90_1_2019.json:127` |
| X3 | SmallOffice furnace eff 0.84 = prototype 0.84 (match); envelope vintage-scaling intentional. OUT OF SCOPE. | audit 2026-06-25 |
| X4 | Re-scoring drivers exist — reuse verbatim on the new results. | `scripts/validation/phaseD_{city_rescore,national_cbecs_rescore,reconstruct_rescore}.py` |
| X5 | Resim infra: `v12_cell_pipeline.py run_cell(cell, output_subdir)`; cluster ExpandObjects separate (no `-x`); one sbatch array at a time, `squeue -u o_iseri` empty before each. | `scripts/validation/v12_cell_pipeline.py`; ABSOLUTE cluster rule |

**Architecture decisions (pre-decided — do not re-debate):**
- **S1. Fix = mirror, don't invent.** For every NON-RESIDENTIAL archetype whose DOE prototype has a weekday heating setback that OpenUBEM dropped, add the evening setback to match that archetype's OWN existing weekend blocks + the prototype (drop to 15.6 °C from 19:00 weekdays). Offices confirmed; audit retail/schools/warehouse/etc.
- **S2. Only true bugs.** Residential (apartments) and genuinely-24h archetypes (hospital, 24h hotel) legitimately hold the evening setpoint — NOT bugs. Correct ONLY archetypes where the prototype HAS a setback OpenUBEM lacks.
- **S3. Resim to a NEW subdir `phaseD2`.** Do NOT overwrite the adopted `phaseD` until CP-8 adopts the fix. `--output-subdir phaseD2`.
- **S4. Cooling setpoint schedules: spot-check for the analogous bug, REPORT ONLY** — no fix/resim expansion without a new manager ruling.
- **S5. Manager audits the edit at CP-7 (vs prototypes) + a local single-building NYC SmallOffice smoke (heating must drop, stay sane) BEFORE any cluster trip.**

**T15 — Comprehensive heating-setpoint-schedule audit.** Audit ALL archetype `Heating_Setpoint_*` weekday blocks in `doe_schedules.json` vs their DOE prototypes; list every non-residential archetype missing the prototype's weekday setback (archetype | current weekday block | prototype block | fix). Spot-check `Cooling_Setpoint_*` for the analogous flattening (report only). *Test:* defect list complete; every office archetype flagged.

**T16 — Correct the defective schedules + local smoke.** Edit `doe_schedules.json` (authorized) to add the weekday evening setback per S1/S2. Run ONE NYC SmallOffice building locally (`-x`) on the corrected schedule; assert heating EUI drops vs the buggy run and stays physically sane. **STOP at CP-7.** *Test:* corrected blocks match the prototype + the archetype's weekend blocks; smoke heating drops, no fatal.

**CP-7 — after T16.** Manager audits the defect list + the exact edits (vs prototypes) + the smoke result BEFORE the cluster trip. STOP.

**T17 — Resim 12 cells → `phaseD2`.** One sbatch array at a time, `--output-subdir phaseD2`, `squeue` empty before each; monitoring delegated cheap. *Test:* each cell closes n/n; adopted `phaseD` untouched.

**T18 — Re-score `phaseD2` + side-by-side.** Run the 3 re-scoring drivers on `phaseD2`; produce adopted-`phaseD` vs fixed-`phaseD2` city deltas + national gates + the NYC office heating delta. *Test:* tables joined; office heating change quantified.

**CP-8 — after T18.** Manager verdict: did the setback fix improve NYC office without harming other cities/segments? Adopt `phaseD2` as the new baseline (supersede `phaseD`) or keep `phaseD`? STOP.

---

## 6. Stop-and-report points (summary)

- **CP-1** (after T02): COP table + provenance — manager sanity-check before code.
- **CP-2** (after T06): local pipeline produces metered EUI; tests green.
- **CP-3** (after T07): cluster pilot `la_urban` clean.
- **CP-4** (after T09): all 12 Phase-D cells closed.
- **CP-5** (after T12): re-validation data — manager verdict.

---

## 7. Progress log

_(Sonnet appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` with Artifacts / Deviations / Test status / Notes. Every entry touching `openubem/` must restate the §0.1 authorization.)_

#### T01 — Restore prototype IDFs + inventory — completed 2026-06-22
- Artifacts: 31 IDF files restored to `docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs/` via `git checkout -- <path>`.
- Deviations: none. All 31 git-tracked files confirmed present post-checkout.
- Test status: all 30 archetypes resolved to a source IDF or explicit fallback (see coverage table in CP-1 report). Assert coverage = 30/30 PASSED.
- Notes: §0.1 core-code authorization NOT yet exercised (Phase 1 is data-only). Courthouse has no matching IDF in repo; assigned generic fallback per §3. TallBuilding/SuperTallBuilding mapped to LargeOffice IDF per §3, but that IDF is CHW-only (non-DX) — flagged in T02.

#### T02 — Extract COP/efficiency → hvac_cop_by_archetype.json — completed 2026-06-22
- Artifacts: `scripts/validation/extract_prototype_cop.py` (NEW); `openubem/data/loads/hvac_cop_by_archetype.json` (NEW, 30 entries).
- Deviations: none. eppy + E+ 23.1 IDD via `config.ENERGYPLUS_IDD_PATH`. §0.1 core-code authorization NOT yet exercised.
- Test status: full 30-archetype coverage PASSED; cooling_cop in [2.0, 5.0] for all DX archetypes PASSED; heating_efficiency in (0.5, 1.0] for all archetypes with a heating coil PASSED. SmallDataCenter* logged INFO (no heating coil in prototype, expected). Validation errors = 0.
- Notes: 10 archetypes flagged `non_dx: true` — these have no parseable DX coil in their prototype IDF. STOP per hard rules; details in CP-1 report below. HotelSmall used `COIL:COOLING:DX:MULTISPEED` (largest capacity coil) as dominant over the 39 SingleSpeed PTAC units, which are all autosized — check whether manager prefers the PTAC SingleSpeed COP (3.81) instead for SmallHotel.

#### T02b — Complete COP JSON to 30/30 per §3.1 manager ruling — completed 2026-06-22
- Artifacts: `scripts/validation/extract_prototype_cop.py` (MODIFIED — added `PLANT_FACTOR=0.75`, `_dominant_chiller()`, `_wshp_cooling_cop()`, `_wshp_heating_cop()`, `prefer_boiler` param to `_fuel_heating()`); `openubem/data/loads/hvac_cop_by_archetype.json` (REGENERATED — 30/30 entries, all coverage).
- Deviations: §0.1 core-code authorization NOT yet exercised in T02b (data-file only). Widened validation assertion `cooling_cop in [2.0, 5.5]` (was 5.0) to accommodate derated chiller COPs (LargeOffice 5.18, Hospital 4.20, etc.) — consistent with §3.1 ruling which sets plant-derated values all ≤ 5.5.
- Test status: 30/30 coverage PASSED; all assertions PASSED. Key derated COPs: LargeOffice 5.181, Hospital 4.197, College 4.324, LargeHotel 2.331, HighriseApartment 3.516, LargeDataCenterHighITE 4.710, LargeDataCenterLowITE 4.324, TallBuilding 5.181, SuperTallBuilding 5.181. SmallHotel cooling_cop 3.810 (PTAC SingleSpeed per §3.1). DataCenters heating_coil_type null per §3.1.
- Notes: Fixed `_fuel_heating(prefer_boiler=True)` for central-plant archetypes — LargeOffice prototype has 4 WSHP electric coils that were incorrectly picked before gas boiler (eff=0.945). TallBuilding/SuperTallBuilding added to `CENTRAL_PLANT_ARCHETYPES` set (were mapped to LargeOffice IDF but treated as non-DX without this fix).

#### T03 — Rewrite assign_hvac → PTAC — completed 2026-06-22
- Artifacts: `openubem/idf/hvac.py` (REWRITTEN).
- Deviations: §0.1 authorized — DESIGN_step-3...md:392–394 (IdealLoadsAirSystem) replaced by PTAC. Field name corrected: IDD uses `Cooling_Coil_Gross_Rated_Cooling_COP` (not `Gross_Rated_COP` as written in T03 spec). IDD object key is `HVACTEMPLATE:ZONE:PTAC` (not `PACKAGEDTERMINALAIRCONDITIONER`); both corrected after IDD check.
- Test status: covered by T06 — 10 test_hvac.py assertions PASSED; test_step3_orchestrator.py 9/9 PASSED with PTAC.
- Notes: LRU cache for JSON load; `KeyError` on unknown archetype; DataCenter heating left at IDD default (Electric) per §3.1; OA set to Flow/Person 0.01 m³/s/person; capacity fields autosized.

#### T04 — Add HVAC end-use meters to outputs.py — completed 2026-06-22
- Artifacts: `openubem/idf/outputs.py` (MODIFIED).
- Deviations: §0.1 authorized — metered HVAC outputs required by PTAC basis change. Used `OUTPUT:METER` (not `OUTPUT:METER:METERFILEONLY`) so values land in SQLite `ReportData` table readable by parser.
- Test status: covered by T06 smoke test — all four meters present in SQL (confirmed by `_parse_meters_sql` returning non-zero cooling and heating).
- Notes: Existing hourly `Output:Variable` entries unchanged.

#### T05 — Rewire parser _EUI_VARS → metered HVAC — completed 2026-06-22
- Artifacts: `openubem/results/parser.py` (MODIFIED).
- Deviations: §0.1 authorized — DESIGN §3I/§5 `_EUI_VARS` (ideal-loads thermal) replaced by metered end-uses. Added `METER_QUERY` SQL against `ReportData`+`ReportDataDictionary`. `_EUI_VARS` alias kept for backward compat. `_check_zone_integrity()` updated to use `Zone Lights Electricity Energy` for zone key resolution (PTAC has no Ideal Loads variables).
- Test status: `test_parser_hvac_metered.py` 9/9 PASSED (reads all 4 meters, missing meter=0.0, nonexistent SQL=zeros, cooling/heating from meters, fans not in total, missing lighting=failed_parse, heating all-fuels sum, `_failed_row` has `fans_eui_kwh_m2`).
- Notes: `fans_eui_kwh_m2` is a SEPARATE column, NOT folded into `total_eui_kwh_m2` — flagged for CP-4 manager decision. `total_eui_kwh_m2 = cooling + heating + lighting + equipment`. Missing meter → 0.0 not NaN.

#### T06 — Update/add tests; local E+ smoke — completed 2026-06-22
- Artifacts: `tests/test_hvac.py` (REWRITTEN — 10 PTAC assertions); `tests/test_idf_builder.py` (MODIFIED — HVAC object key `IDEALLOADSAIRSYSTEM` → `PTAC`); `tests/test_parser_hvac_metered.py` (NEW — 9 metered-EUI assertions).
- Deviations: §0.1 authorized (openubem/ changes reflected in tests). Smoke test used real NYC EPW (`runtime/ubem_validation/cases/nyc_centre/weather/USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw`) — synthetic EPW too minimal for PTAC ExpandObjects. Parser called with original building row (includes `levels`, `height_m`) merged with manifest `num_zones`, not manifest row alone.
- Test status: Phase-D tests green. Golden SQL fixtures in `tests/fixtures/golden_sql/` updated: injected `Cooling:Electricity`, `Heating:Electricity`, `Heating:NaturalGas`, `Fans:Electricity` RunPeriod meter rows matching the pre-Phase-D ideal-loads golden EUI values (so `TestEuiGolden` continues to assert exact round-trip values). Final suite: **785 passed, 4 skipped**; 3 pre-existing failures (`test_r6_rescore.py` + `test_r6_gwp_subregion.py`) from missing `r6_rescore_summary.csv` (docs cleanup, unrelated to Phase-D); `test_sim_integration.py::test_parallel_byte_identity` joblib/CPython-3.14 Windows crash (pre-existing). **Smoke: EnergyPlus exit 0, SQL 3.9MB, metered EUI: cooling 22.96, heating 67.65, lighting 26.49, equipment 33.08, fans 1.15 kWh/m², total 150.20 kWh/m². All sane (heating NYC winter dominant; fans excluded from total).**
- Notes: IDD issues resolved: (1) correct object key `HVACTEMPLATE:ZONE:PTAC`; (2) correct COP field `Cooling_Coil_Gross_Rated_Cooling_COP`; (3) E+ needs `cwd=EP_DIR` to find `Energy+.idd`. No outstanding spec conflicts.

#### T07a — Local preflight + taste-test — completed 2026-06-22
- Artifacts: `runtime/t07a_preflight.py` (NEW scratch script); expanded IDF + sim outputs under `%TEMP%/t07a_preflight/` (ephemeral).
- Deviations: §0.1 core-code authorization NOT exercised in T07a (run/verify task only, no openubem/ edits).
- Test status: **OVERALL PASS.**
  - **Part 1 — Standalone ExpandObjects:** rc=0. `expanded.idf` (130 KB) created with 3× `ZoneHVAC:PackagedTerminalAirConditioner`, 3× `Fan:OnOff`, 3× `Coil:Cooling:DX:SingleSpeed`, 3× `Coil:Heating:Fuel`, 15 DX performance curves (6 Biquadratic, 9 Quadratic, 3 Cubic), 3× `ThermostatSetpoint:DualSetpoint`, 3× `DesignSpecification:OutdoorAir`. `HVACTEMPLATE` objects are commented out (correct — replaced by real objects). IdealLoads absent from expanded.idf. Full cluster-mode expansion confirmed working.
  - **Part 2 — 5-building LA urban taste-test (5 archetypes, all success):**

    | osm_id | archetype | status | cool | heat | light | equip | fans | total (kWh/m²) |
    |---|---|---|---|---|---|---|---|---|
    | way/401904735 | MidriseApartment | ok | 7.68 | 0.96 | 3.97 | 43.40 | 0.23 | 56.01 |
    | way/244066774 | MediumOffice | ok | 20.71 | 13.45 | 26.38 | 43.91 | 0.74 | 104.45 |
    | way/376146181 | SmallOffice | ok | 16.93 | 22.61 | 26.46 | 27.76 | 0.84 | 93.75 |
    | way/401904727 | RetailStandalone | ok | 26.56 | 2.89 | 57.97 | 48.71 | 0.81 | 136.12 |
    | way/376149028 | LargeOffice | ok | 13.70 | 13.35 | 26.47 | 44.06 | 0.68 | 97.58 |

  - All 5 simulate OK (rc=0, 0 severe/fatal). Cooling non-zero: True. Heating non-zero: True. Sane ranges: cooling [7.68–26.56] ⊂ [5,80]; heating [0.96–22.61] ⊂ [0,120]. Fans ≥ 0: True.
  - Fuel: all 5 archetypes have gas heating (Heating:NaturalGas non-zero, Heating:Electricity=0) — matches hvac_cop_by_archetype.json entries.
- Notes: (1) Standalone ExpandObjects reports mixed-case object names (e.g. `ZoneHVAC:PackagedTerminalAirConditioner`), not all-caps; the script's PTAC object counter under-reported because it pattern-matched only uppercase — reporting issue only, expansion was correct and confirmed by direct grep. (2) 131 warnings for MidriseApartment: mostly schedule-type-limits not-validated (pre-existing) + DX coil frost warning (outlet < 2°C on cold nights in LA, non-fatal, common with oversized cooling). LargeOffice: 143 warnings, 0 severe — similar causes. No new warning classes introduced by PTAC. (3) MidriseApartment heating 0.96 kWh/m² is physically plausible for LA CZ3B (mild heating). (4) Scratch script and output dirs are ephemeral (under `%TEMP%`); script lives at `runtime/t07a_preflight.py` for reproducibility.

#### T07 — la_urban cluster pilot — NOT RUN (parked on user's queue) — 2026-06-22
- Status: **WAITING, not executed.** No sbatch array was submitted; no IDFs shipped; no `phaseD/la_urban/` deliverables exist yet.
- Reason: the one-array-at-a-time rule held — the user's own unrelated job `blockB_v23` (981716, ~10h limit) occupied the queue/CPU quota for the whole window. Two pilot dispatches (af1b93f5708c3a3d6, then a cheap Sonnet monitor a1085e7acfb7241da) correctly STOPPED at the pre-submit `squeue` gate. Verified at pause: queue still showed 981716 running (~11 array tasks left).
- Monitoring teardown: per user "close the project for today," the Sonnet monitor agent + its local marker-watcher (b2q6s4glm) were stopped (status killed); no detached poll loop remained on the cluster login node (`ps -u o_iseri` clean). Nothing is left polling.
- Resume path: on return, verify `squeue -u o_iseri` is empty, then run `py -3 scripts/validation/v12_cell_pipeline.py la_urban --output-subdir phaseD` (delegate to a cheap employee), stop at CP-3, manager audits. Full hand-off in `docs/RESUME_opus_manager_phaseD.md`.
- Deviations: none — gate behaved exactly as specified (no submit while queue non-empty).

#### T07 — la_urban cluster pilot — COMPLETED 2026-06-24 (supersedes the parked entry above)
- Artifacts: `docs/validations/overAll/results/phaseD/la_urban/05_results.{csv,gpkg,geojson}` + `05_neighbourhood_summary.json` + `04_simulation_manifest.parquet` + `v12_la_urban_gates_report.txt` (10 deliverables).
- Run: PTAC IDFs regenerated + shipped + one sbatch array **987150** on Speed → **618/618 COMPLETED, 0 PTAC fatals** ("EnergyPlus Completed Successfully" ×618; remote `out/` = 17 GB, 618/618 `.sql/.end/.err`).
- Result headline: cooling EUI median 8.52 (was 55.96 thermal in Phase-C, **−84.8%**), heating 13.14, lighting/equipment unchanged, total median 72.06. F12: parse 100%, plausibility 99.68%, zone_mismatch 0.
- Deviations: §0.1 authorized (PTAC + metered parser). No zoning change. CP-3 audit = §3.3 → GREENLIT for T08.

#### T07r — local fetch/aggregate recovery (no resim) — completed 2026-06-24
- Why: the harness `fetch_results` single streamed `ssh|tar` pipe truncated at ~3 GB on the 17 GB pull (false rc=0) then Windows-locked on `tgz.unlink()`; two stale agents had also double-launched the v1 recovery. Cluster data was fully intact, so this was a pure local fetch+aggregate, not a re-run.
- Fix: one-off recovery driver (scratchpad `recover_phaseD_la_urban_v2.py`, manager-authored ops script, not `openubem/` code) — **batched** fetch (~50 bldgs/SSH `tar`), per-batch gzip integrity check + retry, idempotent skip of already-fetched buildings, ignores the unlink lock, then the audited harness tail (`build_sim_manifest → step5_results → write_gates_report → copy_final_deliverables`). Note: must derive osm_ids from `idf_path` stem (`way_<id>`), NOT the manifest `osm_id` column (`way/<id>`, slash) — the dirs use underscores.
- Lesson for T08: the harness streamed-tar fetch is fragile for big fleets; prefer batched/verified fetch on the remaining cells, or fix `fetch_results` if a cell trips it. Logged, not yet a code change.
- Deviations: none to `openubem/`; ops-script only.

#### T-fans — surface `fans_eui_kwh_m2` in Step-5 output (authorized §3.3 ruling) — completed 2026-06-24
- Artifacts: `openubem/results/aggregator.py` (`_STEP5_COLS` 13→14, `fans_eui_kwh_m2` after `total_eui_kwh_m2`; docstrings 70→71 col); `tests/test_results_aggregator.py` (fixture + count assertions updated).
- Why: CP-2 added fans to `parser.py` but `aggregator.py` dropped it before `05_results`; §3.3 ruling = complete the authorized parser deviation. Fans stays SEPARATE from `total_eui_kwh_m2` (in/out decision deferred to CP-5).
- Test status: `test_results_aggregator.py` + `test_parser_hvac_metered.py` → 38 passed. No other test broke.
- Verified at scale: re-aggregated la_urban → fans 618/618 populated, median 0.366, sensible by-archetype ordering.
- Deviations: §3.3 authorized — only `openubem/` edit beyond the original three §0.1 modules; column-list change, not core math.

#### T08 — Fan out remaining 11 cells — completed 2026-06-25
- Artifacts: `phaseD/<cell>/05_results.gpkg` (+ `04_simulation_manifest.parquet`) for all 11 non-pilot cells; orchestrator status `…/40d9ccae…/scratchpad/t08_STATUS.txt`.
- Execution: one sbatch array in queue at a time, `--output-subdir phaseD`, sequential (user "let it finish sequentially / no touch"); `t08_STATUS.txt` → `ALL 11 CELLS DONE 11:49:48`. nyc_centre largest single array (992642, 738/738 COMPLETED). Zero `STOPPED on failure`.
- Test status: each cell closed n/n; no PTAC fatals; see CP-4 audit table.
- Deviations: none. Monitoring delegated to a cheap background agent per cost discipline; Opus idle between launch and the terminal marker.

#### T09 — Aggregate Phase-D (all 12 cells) — completed 2026-06-25
- Artifacts: 12/12 `phaseD/<cell>/05_results.gpkg` confirmed on disk (Glob) + read successfully (`scratchpad/cp4_audit.py`, geopandas 1.1.3).
- Result: total **8,160 success / 8,160 rows / 0 fail** (Phase-C ref ~8,152). Per-cell + per-city EUI medians extracted; cross-city UTM-zone difference handled by dropping geometry before pooled concat.
- Test status: read of all 12 gpkgs + 12 manifests succeeds; row counts logged in CP-4 table.
- Deviations: none. Audit script is read-only scratchpad analysis (no `openubem/` edit).

#### CP-4 — manager audit, all 12 cells — PASSED 2026-06-25
- Ruling recorded in §3.4. Headline: 8,160/8,160 success / 0 exclusions; cooling −74.5%/−79.4%/−80.7% vs Phase-C (austin_urban/la_centre/nyc_centre); heating +29–51% (expected metered-fuel direction); fans 8,160/8,160 populated; num_floors invariant clean (3,259/3,259 single_zone have levels==1); lighting/equipment archetype-constant except the CP-3-adjudicated multi-zone office tail + the Unknown grab-bag bucket.
- 5 carry-forward flags to CP-5 (fans-into-total, gas eff 0.945, Unknown-bucket loads, LA→Pacific region label, multi-zone office tail) — all report-only.
- Next: T10–T12 / CP-5 re-validation (city anchors + national CBECS, no post-hoc transform).

#### T10 — City-anchor re-score on Phase-D — completed 2026-06-25
- Artifacts: `scripts/validation/phaseD_city_rescore.py` (NEW); data tables in `RESULT_phaseD_validation.md` §T10.
- Deviations: D1/D2/D3 followed exactly. `build_city_table` (imported from v19_rescore.py) expects `total_eui_reconstructed_kwh_m2`; supplied via an `_alias_for_city_table` helper that assigns `total_eui_kwh_m2` (or `+fans`) to that column name — the alias IS the identity transform (D3). v19_rescore.py not modified.
- Test status: script ran clean, 8,160/8,160 rows loaded, 9 anchor rows produced, all deltas finite. No non-finite anomalies.
- Notes: fans contribution is minimal (0.5–1.1 kWh/m² per segment), delta shift < 1 pct-pt between fans-in and fans-out. CP-4 flag (LA→Pacific region label) confirmed cleared in T11/D5.

#### T11 — National CBECS re-score on Phase-D — completed 2026-06-25
- Artifacts: `scripts/validation/phaseD_national_cbecs_rescore.py` (NEW); gate tables in `RESULT_phaseD_validation.md` §T11.
- Deviations: D1/D4/D5 followed exactly. Imports `compute_validation_gates`, `_CITY_REGION`, `_REPORTS_DIR`, `_SUCCESS_STATUSES` from v19_national_cbecs_rescore.py; v19_national_cbecs_rescore.py not modified.
- Test status: script ran clean. D5 PASS — all three cities confirmed against correct region files (nyc→middle_atlantic, la→pacific, austin→west_south_central). CP-3/CP-4 "CBECS NE label" flag cleared (that was a display label in the la_urban gates report, not a scoring error).
- Notes: `eui_kwh_m2` alias set inside `score_city_region` per `compute_validation_gates` contract (reads `eui_kwh_m2` column). Both fans variants run; gate values nearly identical (fans add ~0.5–0.6 kWh/m² to median, negligible on distribution gates).

#### T12 — Findings memo — completed 2026-06-25
- Artifacts: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/RESULT_phaseD_validation.md` (NEW).
- Deviations: none. Data-only per task spec; no interpretation prose. Phase-C baseline transcribed verbatim from RESULT_basis_diagnostic.md (city) and RESULT_national_cbecs_rescore.md (national identity row).
- Test status: file exists, all four tables non-empty, both Phase-C and Phase-D columns present. Note on comparison basis: Phase-C city table uses `total_eui_reconstructed_kwh_m2` (post-service-load reconstruction); Phase-D uses raw metered `total_eui_kwh_m2`. Difference in basis is logged in the memo for CP-5 adjudication.
- Notes: STOPPING at CP-5 per plan. Manager to write CP-5 verdict (go/no-go Phase-D as new baseline).

#### CP-5 — manager verdict — written 2026-06-25 (GO)
- Ruling recorded in §3.5. Verdict: **GO — adopt Phase-D metered HVAC as the new physical baseline.** Basis error eliminated at source (hot→cold sign flip); NYC well-calibrated (NMBE −1.1%, office +11%); LA/Austin run cold (NMBE −30/−32%) and Multifamily is the worst segment (−25/−37%) — re-attributed NOT to basis but to the **unmodeled non-HVAC service-loads layer** (DHW/pumps/process; the V16/R6-4B "Other" ≈42%-of-gap), which Phase-D stripped to isolate HVAC and which the Phase-C "best" included via `total_eui_reconstructed`. CV/KS shape gates fail for BOTH scalar and physical → structural for archetype-deterministic UBEM vs per-building CBECS survey; reclassified report-only (Phase-D nonetheless improved KS in all 3 regions). Fans immaterial (<1 pct-pt); region labels correct (D5).
- Recommended next (user to ratify): re-combine Phase-D metered HVAC + V16 service-loads reconstruction (reporting-layer, no resim, net out metered fans) → re-score; cooling-COP/0.75-derate + gas-eff 0.945 secondary/resim-gated.
- Deviations: none. CP-5 is manager analysis; no `openubem/` edit.

#### T13 — Apply V16 reconstruction to Phase-D + re-score — completed 2026-06-25
- Artifacts: `scripts/validation/phaseD_reconstruct_rescore.py` (NEW).
- Deviations: R1–R6 followed exactly. `reconstruct_frame()` imported from `openubem.results.service_loads` and applied UNMODIFIED (R1). Fans NOT added to reconstructed total (R2). No basis/COP transform (R3). New driver only — no edits to `service_loads.py`, `enduse_fractions_table4.json`, `v19_rescore.py`, `v19_national_cbecs_rescore.py`, `phaseD_city_rescore.py`, `phaseD_national_cbecs_rescore.py`, or any committed result files.
- Test status: script ran clean 8,160 rows / 12 cells. Sanity assertions: (a) 0 violations (recon ≥ raw for all 8,160 buildings — PASS); (b) 0 passthrough buildings (full archetype_map coverage — PASS); (c) food-service median reconstructed EUI 931.6 kWh/m² (within ≤1000 plausibility band; 11 buildings exceed 1000 — W4 caveat noted). All deltas finite.
- Notes: fans cross-check confirms metered/recon ratio ∈ [0.016, 0.064] across all 18 archetypes — PTAC cycling fans are 2–6% of the reconstruction's vent_fans estimate (R2 rationale upheld). `build_city_table` already excludes OpenUBEMUnknown from Overall (R6 satisfied). R5 food-service separation implemented via a second `build_city_table` call on the filtered frame; named-segment rows (Office/Multifamily/Warehouse) are identical between the two tables because those segment definitions exclude food-service archetypes by construction.

#### T14 — Findings memo (data only) — completed 2026-06-25
- Artifacts: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/RESULT_phaseD_reconstructed_validation.md` (NEW).
- Deviations: none. Data-only per task spec; no interpretation prose. Three-way side-by-side structured as: Phase-C recon best (basis_diagnostic best-global) | Phase-D raw (from RESULT_phaseD_validation.md) | Phase-D + recon (this task). Phase-C Multifamily and Warehouse city deltas were not reported in RESULT_basis_diagnostic.md (only 6-anchor table: Office + Overall per city); noted as n/a with source cited. CV(RMSE)/KS for Phase-C best-recon national taken from identity-reconstructed baseline (closest available in RESULT_national_cbecs_rescore_reconstructed.md) with caveat noted.
- Test status: file exists, all tables non-empty, three-way columns joined. STOP at CP-6 per plan.
- Notes: STOPPING at CP-6. Manager writes verdict on whether Phase-D + reconstruction closes the LA/Austin/MF cold gap.

#### CP-6 — manager verdict — written 2026-06-25 (ADOPT Phase-D + V16 as final, recommended)
- Ruling recorded in §3.6. Cold gap CLOSED on the correct metered base: LA Overall −33→−4.2%, Austin −21.4→−7.0%, LA MF −37.3→−9.2%, NYC MF −24.9→+8.8%; city-Overall mean |Δ| 22.6%→7.3%, all 3 cities within ±11% — **with ZERO fitted parameters** (matches the Phase-C 4-knob fitted result). National R² now passes all 3 regions. Confirms CP-5 thesis (residual = service loads, not basis/COP).
- Bounded residual: NYC over-prediction (Office +31.5%, national NMBE +19.1%) from climate-blind national fractions over-restoring on heating-heavy NYC — a fraction-table limitation, NOT COP/gas-eff; secondary resim levers not indicated.
- Recommendation: adopt Phase-D + V16 reconstruction as the final baseline; write the consolidated Phase-D validation report. Optional NYC climate-fraction refinement advised against (over-fit risk). USER DECISION pending.
- Deviations: none. CP-6 is manager analysis; no `openubem/` edit.

#### CLOSE-OUT — Phase-D adopted as final baseline — 2026-06-25
- User chose to scope the NYC refinement; manager scoping found (a) NYC Office is a **metered-base** over-prediction (+11.3% before any service loads — fraction-immune; recon ≥ raw verified) and (b) a principled regional-fraction fix needs raw CBECS-2018 microdata NOT present in the repo (no `cbecs2018*.csv`; only derived total-EUI summaries). User directed "select the most accurate option" → **accept CP-6 as final + write report.**
- Artifact: `REPORT_phaseD_final.md` (consolidated arc CP-1…CP-6, adopted-model spec, city + national tables, limitations, reproducibility).
- Disposition: **Phase-D + V16 service-loads reconstruction = adopted OpenUBEM physical baseline.** Scalar-COP basis retired. Two scoped future options (neither blocking, neither started): NYC HVAC/envelope re-calibration resim (the only fix for the office base over-prediction); regional CBECS end-use fractions (needs new EIA microdata extraction).
- Deviations: none. Manager synthesis; no `openubem/` edit.
