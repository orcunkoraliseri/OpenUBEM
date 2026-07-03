# OpenUBEM — Master Progress Checklist

> Single-glance tracker. Past = one line each. **Current** and **Future** carry the detail.
> Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked / needs decision
>
> **Last updated:** 2026-07-03 (**E-R3-3 sub-arc CLOSED — CP-3 ACCEPTED + T11.7 PROMOTED**: the committed `phaseE` baseline is now the E-R3-3-corrected fleet; move-away diagnosed [662 Medium→Small office flips cross a VAV→PSZ HVAC cliff, 89–100% classifier]; REPORT §14 addendum + new explanation doc authored. Prior: arc **G. input-parameter imputation** Phase B COMPLETE + CP-2 FULLY MET [real-city cluster A/B]; Phase C plan authored, not dispatched.)
>
> **CURRENT BASELINE (adopted; E-R3-3-corrected 2026-07-03):** **`phaseE` full realism** — archetype HVAC (VAV/PSZ/FCU/WLHP, real fans+pumps) + physical DHW/cooking/refrigeration; reconstruction RETIRED; zero fitted parameters. 12-cell 8,160-building matrix. **As of the E-R3-3 fold-in:** city-Overall **−31.9% NYC / −6.2% LA / −30.7% Austin** vs measured; R²=**0.888/0.920/0.720** (shape held); CBECS NMBE **−14.7%/−25.5%/−16.2%**. (As-first-adopted 2026-06-27: −24.4/−5.6/−25.7%; R² 0.895/0.924/0.718; NMBE −10.6/−20.5/−11.9% — preserved in `REPORT_phaseE_final.md` §0–§13; the E-R3-3 shift + mechanism is §14 addendum + `docs/docs_EXPLANATION/OpenUBEM_results_archetypeClassification.md`.) The added under-prediction is the correct office down-tier exposing the DOE-SmallOffice-template gap (accept-and-report per zero-fitted-params). Phase-D2 is the prior superseded baseline; figures regenerated 2026-07-03.
>
> **✅ Sub-arc — E-R3-3 archetype threshold fix — CP-2 ACCEPTED 2026-07-01 (fix ratified; T11 parked)** (reopened a slice of the phaseE full-realism baseline): corrected the office / school / hotel classifier cut-points that misclassified their own DOE prototypes. **CP-1 MET 2026-06-30** — local code + tests green; CP-α coarse 100% / fine 92% on the re-ratified 50-building fixture. **CP-β DONE on the CLUSTER 2026-07-01** — `sbatch` job 1053384 (`openubem_er33_cpbeta_r3`, array 1-483%32): **483/483 COMPLETED, 0 FAILED**, array wall ~1h23m. **Re-classification (offices only, provably-more-correct LBNL-CBES tiers):** 185/483 flipped — LargeOffice 138→71 (−67), MediumOffice 168→117 (−51), SmallOffice 74→192 (+118); zero schools/hotels in the fleet. F12 integrity PASS (parse 100%, zone 0-mismatch, EUI-plausibility 98.76% — 6 "outliers" = legit high-EUI food service). **CBECS gates (465 eligible, report-only per M-R2-4) vs the anchor:** CV 53.78→60.63, NMBE −10.81→−10.99, R² 0.731→0.883, KS 0.190→0.350. **D3 school blind-spot** (Boston fleet has zero schools/hotels → untested by CP-α *and* CP-β) **closed as a unit-level lock (T12: Option B levels + missing-`levels`→PrimarySchool, 6 tests green; accuracy gate unchanged 100%/92%).** **CP-2 investigation (user chose "hold + investigate" first):** manager diagnostic (`scratchpad/diag_cbecs_drift.py`, fig `openubem/outputs/er33_cbecs_drift.png`) proved the "3 gates worsened vs anchor" framing is **confounded** — the anchor is the **R1 baseline (smaller fleet)**; the true 483 predecessor already scored 69.82/−16.05/0.731/0.273 AND used OLD pre-Phase-E HVAC (cooling 70.9 vs 18.2 now). **Isolated classifier effect (two reconstructions agree): CV IMPROVES −3–5, KS IMPROVES −0.08–0.10, R² ±0.000 (the "+0.15 R²" is a Phase-E artifact), NMBE −5–7 more negative (only real cost — down-tiering to the lower-intensity SmallOffice DOE template).** Large CV/KS are structural (office-dominated neighbourhood vs all-types CBECS survey 8–1883) + pre-existing → exactly why the gates are report-only. **User ruling: ACCEPT (E-R3-3 ratified); PARK T11** (defer the 8,160 Phase-E re-run, batch with a future baseline refresh — do NOT dispatch). Remote 43G scratch cleanup dispatched. Plan: `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md`.
>
> **✅ T11 CLOSED — CP-3 ACCEPTED + T11.7 PROMOTED 2026-07-03.** Full 8,160-bldg Phase-E re-run with the corrected E-R3-3 classifier, frozen-geometry + non-destructive (`--output-subdir phaseE_er33`). **Real bug found+fixed:** the post-sim reroute monkey-patch stub `v12_cell_pipeline.py:520` was a 3-arg lambda but commit e063865 added a 4th arg (`resolution_mode`) → crashed every cell reaching reroute; fixed to `*_a,**_k` (fan-out-critical, all 12 cells). All 12 cells landed 8,154/8,160 (the 6 drops = REPORT §7 limitation-#6 inverted-geometry buildings needing the post-hoc `10_fails_solution.md` remediation, not re-applied in the automated re-run — pre-existing, not E-R3-3). **Move-away diagnosis (user asked why before ruling):** 662 MediumOffice→SmallOffice flips (−71.8 each) cross a DOE HVAC-template cliff — VAV→PSZ fans 40→10 (−30), equipment −16, heating −15 — so the city median steps down (NYC −16.5/Austin −8.2/LA −0.7). Classifier-vs-drift decomposition: **89–100% is the fix** (NYC −14.7 of −16.5; LA/Austin 100%), ≤11% NYC same-signed code-drift tail. Correctness fix exposing the low-intensity DOE-SmallOffice-template gap; accepted per zero-fitted-params. **T11.7 executed:** 12 cells promoted → committed `phaseE` (md5-verified), figures regenerated (rescore reproduced NYC 149.3/LA 106.6/Austin 112.2 exactly), REPORT §14 addendum + new `docs/docs_EXPLANATION/OpenUBEM_results_archetypeClassification.md` authored. Baseline is now E-R3-3-corrected (see CURRENT BASELINE block). Full record: PLAN §8 T11.6b + T11.7.
>
> **🆕 Arc H — `layoutGenerator` room-level zoning (implements the deferred `zone` mode from arc F) — Phases 0–3 DONE, CP-1 + CP-2 MET 2026-07-02.** `openubem/geometry/layoutGenerator.py`: classify footprint → decompose L/U/T/courtyard wings → pack DOE-standard corridor+room modules → per-space-type loads with area/load conservation. Closes the gap where non-rectangular footprints silently degraded to one-zone-per-floor (courtyard = E+ Fatal). MidriseApartment first (self-validating vs its DOE prototype), then offices/hotels/schools. Opt-in only — `auto` and the 8,160 baseline untouched. **T01–T10 + T16 done: 130 unit tests green + a room_layout intersect_match fallback (T10a) + full-annual E+ 23.1 smoke on bar/L/U/T/O all Completed Successfully, 0 Fatal / 0 Severe. CP-2 MET (manager greenlight).** Next = Phase 4: T11 reproduce DOE MidriseApartment standard + T12 LIVE_SMOKE → CP-3. Detail = Section H.
>
> **🆕 Arc I — interactive 3D web visualization — DEEP-RESEARCH PROMPTS DRAFTED, pre-PLAN 2026-07-02.** A browser-based, navigable 3D viewer for the simulated neighbourhoods, two LODs (neighbourhood = surfaces/masses only; building = surfaces + sub-surfaces/windows) with function / population / energy-output (EUI heat-map) recolouring — the Torino-3d-heat-mapping / ubem.io analogue. Today OpenUBEM has only static matplotlib axonometrics + desktop-CAD exporters (COLLADA/OBJ/SketchUp) in the `idf_reader` ancestor; no interactive/web/output-driven view. **16-file deep-research prompt set (`00_README` + V01–V15) written under `docs/docs_ACTIVE/3D/deepResearch/`** (manager wrote README + core exemplars V01/V02/V06/V09; Sonnet drafted the rest, manager-audited). Two hard constraints: faithful-to-model (no invented geometry/values; flag imputed/degraded) + reproducible/self-contained/open-source (no paid tiles/proprietary engine). User runs prompts in Gemini Antigravity → manager audits each RESULT → then writes `PLAN_3dviz_implementation.md`. Load-bearing core to run first: V01+V02+V03+V05+V06+V09+V11+V15. **UPDATE 2026-07-03 — DEBUG REPRESENTATION FIX DELIVERED (D01–D06, `docs/docs_ACTIVE/3D/debug/PLAN_3dviz_debug_representation.md` + `debug_regen_report.md`):** user reported most Austin buildings rendering as transparent beige volumes with no EUI/archetype + low-res basemap. Root cause = T22 footprint-only muting (2806/8160 = 34% of buildings, up to 100% in some cells) painting beige `#E4DFD6`/opacity-0.45 over real EUI+archetype, overriding faithful colour; blur = basemap `zoom="auto"` upsampling. **Fix A** (`colormaps.mjs`) removed the mute short-circuit → every building shows its real EUI/archetype fill at full opacity; "no OSM height" now conveyed ONLY by dashed-magenta outline + detail-pane badge. **Fix B** (`basemap_raster.py` new `_resolve_zoom` + `target_px` 2048→3072) fetches high-enough native tiles, never upsamples. **All 12 cells regenerated** into `docs/docs_ACTIVE/3D/outputs/` AND copied byte-identical to `openubem/outputs/3D/`; 12/12 count-parity vs `05_results.csv`, 0 network requests / 0 console errors, no HTML ≥45MB. Tests: node 33/33, python `pytest -k viz` 54/54. Before/after screenshots in `docs/docs_ACTIVE/3D/debug/Image-outputs/`. **Awaiting user sign-off.**

---

## A. Completed (history — brief)

### Pipeline build (Steps 1–5)
- [x] Step 1 — data acquisition (OSM fetch, EPW resolve)
- [x] Step 2 — semantic enrichment (archetype classify, loads, schedules)
- [x] Step 3 — IDF generation (geometry, zoning, extrusion via geomeppy)
- [x] Step 4 — EnergyPlus simulation (parallel runner)
- [x] Step 5 — results parsing + carbon (eGRID)
- [x] Steps 1–3 audit + remediation → suite GREEN (2026-06-09)
- [x] Steps 2.1→5 orchestration plans written + executed (2026-06-10)

### Cluster + validation campaigns
- [x] **R4** — cluster offload closure; Boston 483/483 on Speed SLURM (2026-06-11)
- [x] **R5** — full validation matrix: 12 cells, 8,152 buildings, 100% E+ success (2026-06-15)
- [x] **R6 Batch 1** — reporting-layer hardening (region-correct CBECS, archetype plausibility, eGRID subregion GWP); no resim (2026-06-15)
- [x] **R6-4A** — Level-2 gap decomposition + reporting basis; STOP corroborated by deep research (2026-06-15)

### Calibration science (reporting-layer, no resim)
- [x] Service-loads reconstruction (Table-4 splits; round-trip does NOT close gap) (2026-06-17)
- [x] **V17** — external measured validation: NYC validated (office −0.3%), LA runs hot (+40%), restaurant/MF overshoot, supermarket refrigeration validated (2026-06-17)
- [x] **V18** — calibration diagnosis: found 1-floor-internal-loads ÷ n_floors zoning/geometry defect confounding V17 (2026-06-17)

### Fixes feeding the Phase C resim
- [x] **OQ-2 schedule digitization** — real DOE STD2013 schedules replace synthetic; apartment lighting EUI 43.9→3.97 kWh/m² (~11×); 669 tests pass (2026-06-17)
- [x] **Multi-floor zoning fix** — per-floor zone split for multi-floor sub-500 m² buildings (V18 fix) (2026-06-17)
- [x] **core/perim geometry fix (all 3 classes)** — pilot exposed 3 silent-success-then-E+-fatal geometry pathologies, all now fixed (zero buildings excluded), 61 tests pass (2026-06-18):
  - wedge-explosion degenerate (way_428643335) → post-intersect detector reroutes to one_zone_per_floor (E+'s own "<3 distinct vertices" rule, zero false positives)
  - non-planar/CheckConvexity (way_402036180) → caught by same detector
  - courtyard/interior-ring (relation_6374725) → pre-screen reroutes to one_zone_per_floor

---

## B. Current focus — Phase C combined resim (pilot)

**Goal:** re-simulate the validation cells with fresh IDFs carrying BOTH fixes
(multi-floor zoning + real DOE schedules) and the new core/perim fix, then re-score
against the V17 measured anchors. la_urban is the pilot before fanning out.

- [x] Phase C plan written (`docs/implementation/phaseC_combinedResim/`)
- [x] la_urban pilot — first cluster compute pass (614 buildings)
- [x] Pilot caught a real geometry bug → diagnosed + fixed (core/perim degenerate, see A)
- [x] **la_urban re-run with fixed IDFs** — *DONE 2026-06-18 (bg task `b7iwjmzhf`, exit 0)*
  - 616/618 generated · 616/616 cluster sim success · step3 IDF-gen 983.9s (~16 min, n_jobs=4 — watch-item is a non-issue, no 30-min stall)
  - deliverables in `docs/validations/overAll/results/phaseC/la_urban/`
- [x] Audit la_urban output — **CLEAN, pilot CLOSED 2026-06-19 00:xx** (clean re-run `b9hus1m9d`, exit 0; new cluster job 971039)
  - [x] **5 `failed_zone_mismatch` → RESOLVED.** Diagnosis confirmed exactly: harness ship≠manifest desync (cluster had simulated stale Jun-17 `fleet_staging/idfs/`; final core/perim fix landed Jun-18 after the ship; `if not dst.exists()` guard skipped overwriting). **DECISION (manager, user-delegated): clean full re-run** — cleared stale `fleet_staging/`+`sim_out/`+`step3/`+top manifest (preserved step1/step2/EPW caches), re-ran. Result: **616/616 parsed, `zone_count_integrity: 0 mismatches` PASS, status `{'success': 616}`, zero exclusions** (only the 2 expected `OpenUBEMUnknown` un-simulated). Headline barely moved (total_eui 154.80→154.82) — the 5 were a tiny weight. TRUE-POSITIVE gate vindicated; no geometry regression; NO manifest patch.
    - **Latent harness bug (still open):** `ship_to_cluster` copies regenerated IDF only `if not dst.exists()` (v12_cell_pipeline.py:249); `run_cell` never clears `fleet_staging`/`sim_out`. Fresh fan-out cells are SAFE (empty work_base). ANY cell **re-run** is poisoned until fixed → Sonnet hardening task queued (§C3); must precede any second pass.
  - [x] MidriseApartment lighting EUI = **3.97 kWh/m²** (n=446, uniform) — OQ-2 DOE schedules confirmed in resim (headline 22.21 is office-weighted blend, not the apartment check)
  - [x] R5 baseline `cases/la_urban/` untouched — all dated **Jun 12** (verified)
- [x] **V19** — re-score vs V17 anchors → `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md` (DONE 2026-06-20). **Findings:** fixes resolved V17's over-predictions (NYC MF +33.5→+0.7%, food-service +110/160→−1.6/+12%, NYC city +10.0% = pass). V17 NYC-office anchor was a V18 artifact → office now +37% (NEW P1 systematic bias, all cities +30–52% vs ESPM). **LA still hot +38.8% (unmoved −0.6%) → confirmed climate/HVAC problem, NOT zoning.** Revised calibration priority: P1 = office loads + LA climate.

---

## B2. Phase D real-HVAC resim (Phase-2 DESIGN deviation) — **COMPLETE + ADOPTED 2026-06-26**

**Goal:** kill the thermal-vs-metered basis error at the source. Replace `IdealLoadsAirSystem`
with `HVACTemplate:Zone:PTAC` + per-archetype prototype COP, and rewire the parser from
thermal loads → metered HVAC electricity/gas. Then re-validate all 12 cells vs city anchors
AND national CBECS with **no post-hoc transform**. V18 re-zoning already baked into Phase C →
Phase D is **HVAC-only**. Plan: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md`.

**Why this and not a scalar COP fix:** V19 basis diagnostic proved a scalar post-hoc COP passes
mean-level NMBE but never clears the shape gates (CV(RMSE)/KS) and can't reconcile city-optimal
COP (~3.5) with national-optimal (~2.5). Resim GO is evidence-backed. Authorized DESIGN deviation
(PLAN §0.1, user-ratified 2026-06-21): deviates from DESIGN_step-3 §3H, activates the line-420
PTAC Phase-2 hook. DESIGN docs NOT edited.

- [x] **CP-1** — COP extraction. `openubem/data/loads/hvac_cop_by_archetype.json`, 30/30 archetypes (manager-verified). 16 DX use gross-rated DX COP; 10 central-plant use chiller/WSHP COP × 0.75 plant factor (PLAN §3.1 ruling).
- [x] **CP-2** — core code landed + audited (the 3 authorized modules): `idf/hvac.py` (PTAC emission), `idf/outputs.py` (Cooling/Heating elec+gas/Fans meters), `results/parser.py` (`_EUI_VARS` thermal→metered + new `fans_eui_kwh_m2`). 785 tests pass (4 pre-existing unrelated).
- [x] **T07a local taste-test** — standalone ExpandObjects (cluster path, no `-x`) expands PTAC → real DX coils, no IdealLoads; 5 la_urban buildings 0-fatal, metered EUI sane. **LA MediumOffice cooling 20.7 metered vs old thermal ~90 → basis fix visibly working.** Cluster-expansion risk cleared.
- [x] **T07 la_urban cluster pilot — DONE 2026-06-24.** Array **987150, 618/618 COMPLETED, 0 PTAC fatals** (17 GB intact). Local fetch needed a one-off batched recovery driver (harness streamed-tar truncates on big pulls); no resim. Deliverables in `docs/validations/overAll/results/phaseD/la_urban/`.
- [x] **CP-3 — PASSED, GREENLIT for T08 (2026-06-24).** vs Phase-C `la_urban`: 618/618 success (0 exclusions); **cooling median 55.96→8.52 (−84.8%)** basis fix decisive; zoning invariant (26 `LargeOffice` divergers = a correct normalization fix, not a regression); fans 618/618 populated. Full audit = PLAN §3.3.
- [x] **Fans-column fix (CP-3 ruling)** — `aggregator.py::_STEP5_COLS` 13→14 (`fans_eui_kwh_m2` surfaced, still OUT of total); Sonnet, 38 tests green. Fixed before T08 so all 12 cells carry fans natively.
- [x] **T08–T09 / CP-4 — PASSED 2026-06-25.** Fan-out ran sequential & clean (`ALL 11 CELLS DONE 11:49:48`, zero failures; nyc_centre largest array 992642 738/738). All 12 cells closed: **8,160/8,160 success, 0 exclusions, 0 PTAC fatals** (Phase-C ref ~8,152). Cooling basis fix consistent across the 3 committed Phase-C baselines (austin_urban −74.5%, la_centre −79.4%, nyc_centre −80.7%; matches CP-3 −84.8%); heating +29–51% = expected metered-fuel direction; per-city totals climate-correct (LA 76.6 < Austin 128.6 < NYC 198.0); fans 8,160/8,160 populated; num_floors invariant clean (3,259/3,259 single_zone have levels==1). Full audit = PLAN §3.4.
- [x] **CP-5 carry-forward flags — resolved/dispositioned (PLAN §3.5):** (a) fans immaterial (<1 pct-pt) — fold into total for CBECS completeness, changes nothing; (d) region labels correct (D5: NYC→mid-atlantic, LA→pacific, Austin→WSC; "CBECS NE" was a display label, scoring always Pacific); (c) Unknown bucket excluded from city scoring; (b) gas eff 0.945 + (e) cooling-COP/0.75-derate → secondary, resim-gated, subordinate to the service-loads gap.
- [x] **T10–T12 — DONE 2026-06-25** (Sonnet, 3 new files: `scripts/validation/phaseD_city_rescore.py`, `phaseD_national_cbecs_rescore.py`, `docs/.../RESULT_phaseD_validation.md`; data-only, no transform; n's reconcile to CP-4).
- [x] **CP-5 — MANAGER VERDICT: GO (PLAN §3.5).** Adopt Phase-D metered HVAC as the new physical baseline. Basis error eliminated (LA hot→cold flip); NYC well-calibrated (NMBE −1.1%); LA/Austin cold (NMBE −30/−32%), Multifamily worst (−25/−37%) — re-attributed to the **missing non-HVAC service-loads layer** (DHW/pumps/process = V16/R6-4B "Other" ≈42%-of-gap), NOT basis. CV/KS fail for both scalar & physical → structural for archetype-deterministic UBEM → report-only (Phase-D still improved KS 3/3). Retire scalar-COP crutch; operative metrics = NMBE + city-median deltas.
- [x] **CP-5 fork — user chose "re-combine + re-score" (2026-06-25).**
- [x] **Phase 5 (T13–T14) — DONE 2026-06-25** (Sonnet, 2 new files: `scripts/validation/phaseD_reconstruct_rescore.py`, `docs/.../RESULT_phaseD_reconstructed_validation.md`; shipped `reconstruct_frame()` unmodified, no fans double-count, no transform).
- [x] **CP-6 — MANAGER VERDICT: cold gap CLOSED; adopt Phase-D + V16 as FINAL (PLAN §3.6).** LA Overall −33→−4.2%, Austin −21.4→−7.0%, LA MF −37.3→−9.2%, NYC MF −24.9→+8.8%; **city-Overall mean |Δ| 22.6%→7.3%, all 3 cities ±11%, ZERO fitted params** (= Phase-C's 4-knob fitted result). National R² passes all 3 regions. CONFIRMS the residual was service loads, not basis/COP. Bounded new residual = NYC over-predict (Office +31.5%, NMBE +19.1%) from climate-blind national fractions — fraction-table limit, not COP/gas-eff.
- [x] **CP-6 next step — RESOLVED 2026-06-25: Phase-D ADOPTED as final baseline.** User scoped the NYC refinement; manager found NYC Office is a metered-BASE over-prediction (+11.3% before service loads, fraction-immune) and a principled regional-fraction fix needs raw CBECS microdata absent from the repo → user "select most accurate option" → accept + report. Deliverable: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/REPORT_phaseD_final.md`.
- **➤ ADOPTED MODEL: metered PTAC HVAC + V16 service-loads reconstruction** (zero fitted params; city-Overall ±11% all 3 cities; national R² passes all regions; CV/KS report-only/structural). Scalar-COP basis retired. **Phase-D arc COMPLETE.**
- [x] **Phase 6 T15–T16 — DONE 2026-06-25 (Sonnet).** Audited all 30 archetypes' `HeatingSetpoint`; found the weekday-evening-setback bug in **11** (not 3): SmallOffice/MediumOffice/LargeOffice + their 3 `*Detailed` + College + Courthouse + TallBuilding + SuperTallBuilding + OpenUBEMUnknown — all held weekday 21.1°C flat to 24:00 while their OWN weekend blocks dropped to 15.6 at 19:00. Fixed (`doe_schedules.json` only) to mirror each archetype's own weekend setback. 19 correctly exempt. Local smoke NYC SmallOffice heating 91.30→79.96 (−12.4%, cooling unchanged, E+ exit 0).
- [x] **CP-7 — MANAGER VERDICT: PASS (PLAN §"Phase 6").** Independently re-audited: 11 buggy / 19 exempt classification correct; scope expansion 3→11 justified; edits S1-compliant (mirror own weekend); only `doe_schedules.json` touched; pre-fix smoke 91.30 reproduces phaseD EXACTLY → no OQ-2 confound. **S4 cooling ruling: do NOT fix cooling** (would cut cooling EUI → hurts already-cold LA/Austin, helps over-predicted NYC negligibly). Heating-only resim authorized.
- [x] **Phase 6 T17 — resim 12 cells → `phaseD2` — DONE 2026-06-26 (ALL_DONE 07:03:58).** After two attempts froze on a joblib/loky deadlock (Py3.14/Win) + an agent-kill, the manager hardened the path (H1 serial `n_jobs=1` build, H2 skip-if-remote-done resumable fetch) and ran it under `scratchpad/run_phaseD2_v4.ps1` (PID 37032, OS-detached). **All 12 cells closed first-attempt, 0 failures**; v4 fix = gate success on the **gpkg artifact**, not `$p.ExitCode` (Start-Process+RedirectStdout+timed-WaitForExit returns null exit). Adopted `phaseD` + GSSCanada `987039` untouched.
- [x] **Phase 6 T18 — re-score `phaseD2` + side-by-side — DONE 2026-06-26 (Sonnet).** One-line env-gate in `phaseD_city_rescore.py` (`OPENUBEM_PHASED_SUBDIR`, default `phaseD`; all 3 drivers inherit); 6 runs; memo `docs/.../phaseD_realHVAC/RESULT_phaseD2_setback_rescore.md`. **NYC office heating −9.86% (135.37→122.02); NYC Office anchor +11.3%→+4.1% raw, +31.5%→+23.3% recon.** Raw-basis cost: LA/Austin/Overall (already under) 3–7 pct-pt more under; reconstructed basis net-favorable (NYC Overall +10.8→+5.6, LA Office +13.0→+4.5); national reconstructed loses Austin NMBE.
- [x] **CP-8 — MANAGER VERDICT: ADOPT `phaseD2` (supersede `phaseD`); USER RATIFIED 2026-06-26 ("Adopt, then tackle LA/Austin").** The flat-setpoint was a confirmed digitization bug → phaseD2 is the physically-faithful model; raw "harm" is the cold bias being *unmasked*, not created. **REPORT Limitation #1 (NYC office over-heating) → RESOLVED.** `phaseD2` canonical; `phaseD` retained as pre-fix reference. Verdict + ratification in `PLAN_phaseD_real_hvac_resim.md` §8.
- [x] **➤ Regional CBECS service-load fractions (Direction A) — COMPLETE + ADOPTED 2026-06-26.** Evidence-first scoping found national-CBECS NMBE failures (NYC +12 / LA −17 / Austin −13) are driven by the V16 fraction table being climate-blind; manager recommended B (accept+document), **user chose A.** Recon confirmed the CBECS-2018 public file carries per-building MF end-use BTU cols → per-division `modeled_frac` from the SAME EIA source, no new data. **CP-1 caught a real defect** (wholesale CBECS-level swap inflates all cities — CBECS "Other" double-counts OpenUBEM's modeled equipment); **manager RULING = DD3b ratio-tilt** (CBECS relative deviation × validated national level, cancels the artifact, non-anchor-fitted). Guard passed. **Result: national NMBE FLIPS FAIL→PASS all 3 regions** (NYC +7.7 / LA −6.1 / Austin −9.9), unfitted, backward-compatible (78 tests green); NYC/Austin/LA-Overall improved/held. **Disclosed costs:** LA Office +4.5→+12.3%, LA Warehouse +9.8→+31.2% (n=38); CV/KS structural (mean-lever only); commercial-only (MF national). **User RATIFIED "Adopt regional" (CP-2).** PLAN: `docs/.../phaseD_realHVAC/PLAN_regional_service_load_fractions.md`. Adopted model = phaseD2 + V16-on-regional-fractions.
- [x] **➤ `REPORT_phaseD_final.md` regenerated to the adopted phaseD2 + regional-fraction model — DONE 2026-06-26.** Consolidates CP-8 (phaseD2 setback) + CP-2 (regional fractions). Headline: zero-fitted-parameter model, **city-Overall within ±9% all 3 cities** (NYC +2.1 / LA −3.7 / Austin −8.6), **national CBECS NMBE + R² passing all 3 regions** (first time). Limitations #1 (NYC office over-heat) + climate-blind fractions RESOLVED; LA Office/Warehouse regional-fraction costs + structural CV/KS disclosed. **Phase-D arc COMPLETE.**
- [x] **(1) regional CBECS end-use fractions — DONE + ADOPTED 2026-06-26** (Direction A / CP-2 above; no new EIA extraction needed — end-use cols were in the existing CBECS public file).
- [x] **(2) cooling-COP/0.75-derate + gas-eff 0.945 secondary HVAC levers — EVALUATED + CLOSED 2026-06-26: NOT indicated.** Disposed against the adopted phaseD2+regional results: (a) gas-eff 0.945→0.80 would RAISE gas heating fuel, but NYC (heating-dominated) already runs slightly over (Overall +2.1%, national NMBE +7.7%) → the correction is **contraindicated** (worsens NYC); (b) the cooling-COP/0.75-derate would raise cooling energy and could nudge LA/Austin (Overall −3.7%/−8.6%, marginally under) toward zero, but it is **resim-gated** (cooling is now metered) and the model already passes all gates within tolerance with zero fitted params → a resim is not warranted on its account. No residual demands either lever; closed.

---

## B3. Next moves — post-Phase-D consolidation & hardening (ordered, 2026-06-26)

Phase-D modeling science is COMPLETE (B2). Remaining = documentation + defensive robustness. Manager drives; step 3 is a Sonnet feature-code arc with an open scope decision. Executing step-by-step.

### Step 1 — Restaurant + MF reconstruction overshoot revisit (manager analysis) — **DONE 2026-06-26: RESOLVED**
- [x] Re-checked V17's restaurant/MF overshoot under the adopted phaseD2 + regional model (read-only analysis over the 12 gpkgs). **All resolved:** NYC MF +33.5%→**+8.8%**, LA MF +32.4%→**−9.2%** (city anchors, in band); Full-Service Restaurant +110%→**−26.8%**, Quick-Service Restaurant +160%→**−21.8%** (now mildly UNDER their national ESPM anchors — the 2–3× overshoot eliminated by the Phase-D metered base). Residual = the documented food-service plausibility tail (median 958 in band; 20 buildings >1000, 0 >2000 — vs V17 QSR median 3307). No new fix indicated; closes C3 "restaurant + MF reconstruction overshoot."

### Step 2 — Project-level report consolidation (manager) — **DONE 2026-06-26**
- [x] Reconciled `REPORT_R5_final.md` to the adopted baseline via a prominent **supersession banner** (preserves the frozen R5 record; points to `REPORT_phaseD_final.md` with the current headline numbers — city-Overall ±9% all 3 cities, national NMBE+R² pass all regions, restaurant/MF overshoot resolved).
- [x] Added the matching supersession pointer to `V13_cross_case_synthesis.md` (R5 climate-physics + structural-gap findings still hold; absolute EUI/gate values superseded).

### Step 3 — Geometry-robustness MULTI-class hardening — **ALREADY DONE (C1b fix batch, 2026-06-19); verified 2026-06-26**
- [x] The MULTI-class E+-fatal hardening C3 describes as "open" was in fact **landed in the C1b fix batch** and is wired in the build path (verified in code 2026-06-26): `_coreperim_has_tiny_zone_area` (0.5 m² sliver detector) + `_coreperim_has_degenerate_surfaces` → `_force_reroute_coreperim_to_one_zone_per_floor` (surfaces.py:555–561); interzone vertex-count-mismatch reroute at generation time (builder.py:278–319); `_coreperim_has_inverted_winding` defined but intentionally excluded from reroute (E+ winding convention). All 3 named pathology buildings reroute cleanly; the adopted fleet ran **8,160/8,160 clean** through Phase-C → Phase-D → phaseD2. No code work remains. (C3 lines describing this as open were STALE → reconciled.)
- [x] **GENERATION-time-drop rescue — COMPLETE + CLOSED 2026-06-26 (CP-2 PASS).** True HEAD drop count was 1 (not 4): `way/427274629` hang fixed by pre-intersect-match complexity gate (T=800; M_hang=1455; 0 perimeter_core successes with M>800); serial `n_jobs=1` loop hardened with per-building try/except; 9 new rescue tests + 123 existing tests green (132 total). Hang building: generates in 51 s (was >393 s hang), E+ smoke exit-0 (0 severe errors, EUI=90.6 kWh/m²). 3 other "drops" were stale-manifest artifacts — already rescued by C1b HEAD code. HEAD drop count = 0. PLAN: `docs/docs_ACTIVE/phaseC_combinedResim/PLAN_geometry_generation_drops.md`; memo: `RESULT_generation_drop_diagnosis.md`. NO cluster, NO adopted-baseline resim.

---

## C. Future — fan-out + beyond

### C1. Phase C fan-out — **[x] FANOUT DONE 2026-06-19 07:54** (bg task `bm9hpi645`, exit 0)
**Final tally: 12/12 cells clean** — fan-out (9) + the 3 fix-batch re-runs (austin_urban, la_centre, nyc_centre) all closed **2026-06-19, zero exclusions** (T10). All cells: parse 100%, zone_count_integrity 0, apartment lighting 3.965 (OQ-2 confirmed). The geometry fix-batch reroute resolved every previously-fatal building; none dropped. Per-cell detail below:

**Austin**
- [x] austin_centre — rc=0, parse **413/413**, zone_mismatch **0**, MidApt lighting **3.97**, total_eui 178.13 (CZ2A, cooling 95.27)
- [x] austin_urban — **FIXED + RE-RUN CLEAN 2026-06-19** (T10, job 979381): parse **425/425**, zone_mismatch **0**, status {success:425}, MidApt lighting **3.965**, total_eui 201.45 (CZ2A, cooling 107.43). Prior sliver-perim + MultiPolygon crash building (way/381810546) now reroutes via fallback — not dropped. *(history below)*
  - **ROOT CAUSE (confirmed, Sonnet diag):** highly non-convex footprint (14 perim segments); geomeppy's perimeter offset at a re-entrant corner yields a triangular **sliver** perim zone (F2_PERIM10 area 0.0645 m², 3 distinct verts but only **18.76 mm off collinear** — *above* the existing 10 mm collapse tol, so the `<3-distinct-vertex` detector does NOT fire). Sliver inverts winding → **all perim zones get negative computed volume**; E+ stubs most to 10 m³ but the extreme sliver diverges. **4th pathology class** beyond the existing 3 guards (coincident-vertex strip / courtyard / too-narrow-core).
  - **FIX DIRECTION (clean, same remedy):** extend the surfaces.py detector to also reroute → `one_zone_per_floor` when the core/perim decomposition yields any perim zone with floor area below a min threshold (~0.5 m²) OR inverted/negative signed area. Low-risk: identical reroute remedy + philosophy as existing guards. **Cross-cell exposure: yes** (low-freq, any perimeter_core cell w/ non-convex footprints — NYC dense fabric most likely). Manager writes the plan; Sonnet executes; re-run failed cells AFTER §C3 harness-hardening lands.
- [x] austin_suburban — rc=0, parse **437/437**, zone_mismatch **0**, total_eui 236.57 (CZ2A, cooling 131.08)
- [x] austin_rural — rc=0, parse **245/245**, zone_mismatch **0**, total_eui 175.50 (cooling 82.18) — sliver-perim class did NOT recur in suburban/rural

**Los Angeles**
- [x] la_urban *(pilot — CLEAN, see §B; NOT in the fan-out loop)*
- [x] la_centre — **FIXED + RE-RUN CLEAN 2026-06-19** (T10, job 979819): parse **226/226**, zone_mismatch **0**, status {success:226}, Mid/Highrise lighting **3.965**, total_eui 164.73 (cooling 93.17). Prior interzone-vertex-mismatch (way_427817502) + thermal-divergence (way_427817541) buildings now reroute — not dropped. *(history below)*
- [x] la_suburban — rc=0, parse **1343/1343**, zone_mismatch **0**, total_eui 120.08 (cooling 57.80) — MidApt lighting 3.97
- [x] la_rural — rc=0, parse **148/149** (1 expected not_sim), zone_mismatch **0**, total_eui 117.36 (cooling 57.95)

**New York City** — Phase C matrix = **12 cells** (NYC 4 + LA 4 + Austin 4). NOTE: `CELL_CONFIGS` in v12_cell_pipeline.py is **MISSING the nyc_centre entry** (has only urban/suburban/rural) — a real config-omission bug, NOT a phantom (corrected 2026-06-19 after user flagged the centre/urban asymmetry).
- [x] nyc_centre — **ADDED TO CONFIG (T08) + RAN CLEAN 2026-06-19** (T10, job 980072): parse **738/738**, zone_mismatch **0**, status {success:738}, Mid/Highrise lighting **3.965**, total_eui 164.56 (CZ4A, cooling 67.25). The missing 12th cell — clean on first pass. *(history below)*
- [x] nyc_urban — rc=0, parse **1778/1778**, zone_mismatch **0**, total_eui 192.87 (cooling 67.65) — 1 not_sim (interzone-vertex-mismatch caught at GEN-time, dropped cleanly, not an E+ fatal)
- [x] nyc_suburban — rc=0, parse **1589/1589**, zone_mismatch **0**, total_eui 189.42 (cooling 53.83)
- [x] nyc_rural — rc=0, parse **198/198**, zone_mismatch **0**, total_eui 214.48 (cooling 81.39) — geometry pathologies did NOT recur in dense NYC fabric

### C1b. Post-fan-out FIX BATCH (ORDERED) — **✅ COMPLETE 2026-06-19**
**Plan doc:** `docs/docs_ACTIVE/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md` (T01–T10, all completed; full suite green 21+50 passed). Executed in THIS order:
1. [x] **Harness hardening** (T01) — ship-guard made unconditional + clear `fleet_staging/`+`sim_out/` on re-run (caches preserved).
2. [x] **Geometry-robustness fix** (T02–T05) — MultiPolygon coerce, intersect_match try/except reroute, sliver/tiny-zone detector (0.5 m²), interzone-mismatch reroute-not-drop.
   - [x] **Regression tests** (T09) — 10 new tests for sliver / interzone-mismatch / thermal-divergence / MultiPolygon; `TestCleanRectNoFalseTrigger` stays green.
   - [x] **Verify the 3 named buildings** (T06) — all reroute to one_zone_per_floor, 0 degenerate/tiny/mismatch; confirmed clean in the T10 cluster re-run.
3. [x] **Add nyc_centre to CELL_CONFIGS** (T08) — 40.7549, −73.9840, the missing 12th cell.
4. [x] **Re-run** austin_urban + la_centre + nyc_centre (T10) → **12-cell Phase C set complete, zero exclusions**; R5 baselines untouched.
- [x] **OPEN DECISION RESOLVED (2026-06-26):** "fix don't skip" extended to GENERATION-time drops — see B3 Step 3 generation-drop rescue above. HEAD drop count = 0; genuinely-unbuildable footprints still drop cleanly (rule 4 preserved; test coverage in `tests/test_generation_drop_rescue.py`).

### C2. Cross-cell synthesis + final report
- [x] V19 full re-score across all 12 Phase C cells vs V17 anchors (DONE 2026-06-20 → `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`)
- [x] Cross-case synthesis (V13) reconciled to adopted baseline via supersession banner — **DONE 2026-06-26** (B3 Step 2)
- [x] Project-level report (`REPORT_R5_final.md`) reconciled to adopted baseline via supersession banner → points to `REPORT_phaseD_final.md` — **DONE 2026-06-26** (B3 Step 2)

### C3. Conditional / open scientific questions
- [x] **Why does LA run +40% hot?** — V19 (2026-06-20) ANSWERED the gating question: LA stays hot
  (+38.8%, unmoved −0.6% by the zoning fix) → it is NOT the zoning defect; confirmed a real
  climate/HVAC-response problem. **Deep-research now warranted** (was "do NOT research blind"): California
  Title 24 vs our ASHRAE 90.1 archetypes (envelope U-values, infiltration, HVAC COP/economizers for
  cooling-dominated CZ 3B). Gated on user go/no-go for the calibration phase.
- [x] Restaurant + multifamily reconstruction overshoot — **RESOLVED 2026-06-26** under adopted phaseD2 + regional (B3 Step 1): MF NYC +8.8/LA −9.2 in band; FSR/QSR flipped from +110/+160% to −27/−22%.
- [x] IDF-gen performance pre-filter — **CLOSED 2026-06-26.** The §B perf watch-item never proved prohibitive (recorded as a non-issue, no 30-min stall), so the conditional never triggered; AND the generation-drop fix's `T=800` core/perim **complexity gate** (B3 Step 3) now IS this cheap pre-filter — it reroutes only the genuinely-prohibitive high-M tail (e.g. the 1455-pair hang) away from intersect_match, with zero regression on succeeding buildings. Superseded; nothing further to add.
- [x] **Geometry robustness — MULTI-class — RESOLVED in the C1b fix batch (2026-06-19); verified in code + production 2026-06-26 (see B3 Step 3).** All 3 signatures below reroute → one_zone_per_floor (sliver/tiny-zone + degenerate detectors wired surfaces.py:555–561; interzone-mismatch reroute builder.py:278–319); 8,160/8,160 clean through phaseD2. Original signatures (now handled):
  - **(a) sliver perim zone** — austin_urban way/381810546: non-convex footprint → perim offset makes a collinear sliver zone (area 0.06 m², 18.76 mm off collinear, *above* the 10 mm vertex-collapse tol) that inverts winding → negative zone volumes → `CalcHeatBalanceInsideSurf` divergence. Existing `<3-distinct-vertex` detector misses it.
  - **(b) interzone vertex-count mismatch** — la_centre way_427817502: `GetSurfaceData` fatal, paired ceiling/floor have 12 vs 11 verts (geomeppy intersection artifact).
  - **(c) thermal divergence surviving repair** — la_centre way_427817541: temp out-of-bounds even after the zero-area-strip repair.
  - **AND the auto-repair path is insufficient** — the harness's zero-area-strip + re-submit fails for (a)/(b)/(c); the repair fallback should reroute the building → one_zone_per_floor, not just strip surfaces.
  - **Likely fix (manager plan, Sonnet executes):** a general pre-sim geometry validation that reroutes → one_zone_per_floor on ANY degenerate perim decomposition (min perim-zone area, signed-area/winding check, interzone vertex-count parity) + harden the repair fallback to do the same. This is a broader design decision than the original 3-guard detector → **flagged for user decision.** Re-run every rc=2 cell after the fix (full list TBD at fan-out end) — AFTER the harness-hardening below.
- [x] **Harness hardening — ship/staging coherence — DONE (C1b T01; verified in code 2026-06-26).** The `if not dst.exists()` ship guard is gone — ship copy is now **unconditional** (`v12_cell_pipeline.py:255`), and `run_cell` clears `fleet_staging/`+`sim_out/` at start preserving step1/step2/EPW caches (`:973–977`). The la_urban-style stale-IDF re-ship desync can no longer occur; confirmed sound by the phaseD2 (T17) re-run sweep across all 12 cells.

---

## D. How decisions flow (reminder)
- Manager (Opus session) writes/updates plans + audits; **never writes feature code**.
- Fresh Sonnet sessions execute plans; never plan.
- Cluster/long compute = user's explicit go/no-go.

---

## E. Phase-E "full realism" — ✅ COMPLETE 2026-06-27
Plan: `docs/docs_ACTIVE/hvac-ServiceLoads/PLAN_phaseE_full_realism.md`. CP-D ruling: `docs/docs_ACTIVE/hvac-ServiceLoads/pilot/RESULT_phaseE_CPD_gonogo.md`.

- [x] **CP-A** data tables (6 JSON) + rulings R-CP-A-1/-2 — PASSED.
- [x] **CP-B** HVAC dispatcher (PTAC→10 system families) + DHW/cooking/refrigeration emitters + parser/carbon/aggregator + reconstruction retired (T06–T15) — PASSED; **B-CP-B-1** supermarket refrigeration (1192→100.4 kWh/m², constant-defrost-schedule root cause) CLOSED; refrig params FROZEN.
- [!] **CP-D — la_urban pilot — NO-GO / HELD 2026-06-27.** E+ 617/618; pilot died on `run_cell` zero-fail `sys.exit(2)` before Step 5 (1 degenerate Warehouse `way/402215469`); manager recovered Step 5+rescore from on-disk SQL. **Win:** physical service loads centered bias → CBECS NMBE −39.3%→**−3.1% PASS**; median 104.68 = **−7.9% vs EBEWE** (zero fitting). **Blockers found** ⇒ fan-out NOT launched:
  - [~] **B1 — REFRAMED at CP-R1 (2026-06-27): degenerate-GEOMETRY defect, not HVAC.** Both la_urban PrimarySchools have inverted floor/ceiling normals → E+ negative zone volume → clamps to 10 m³ → autosizes airflow 13–21× too high → 0.30 min forces ~9 kW continuous reheat = 765–1565 kWh/m². SAME class as the Warehouse hard-fail (one root cause, two symptoms: E+ rejects OR clamps-and-garbles). SAT reset (RD2) is a real family-wide win (offices/courthouse −9…−14%, regression-clean, RETAINED) but cannot fix geometry over-autosizing. **Ruling D2:** screen `.err` for negative/forced-volume → drop into the same `dropped_buildings.csv` under the B2 tolerance (handles both symptoms; doubles as prevalence diagnostic). RD3 proven non-functional (E+ overrides it with the 0.30 floor).
  - [!] **B2 (pipeline blocker):** `run_cell` zero-fail `sys.exit(2)` will kill any fan-out cell with ≥1 unsimulatable bldg → make it tolerate a few **logged** geometry drops (PLAN forbids *silent* drops, not logged).
  - [!] **G2 (gate-spec):** fans+pumps 12–16 band mis-applied to residential-dominated median (pumps physics is CORRECT — nonzero for all central-plant archetypes); re-spec per-archetype/subset.
  - [ ] **W1 (verify):** MidriseApartment DHW=electric vs HighriseApartment DHW=gas — confirm against DOE prototypes; both are multifamily residential. **→ NOT a bug:** RESULT_03 Table 2 specifies Midrise=Electricity / Highrise=NaturalGas; JSON already matches → verify-and-document.
- [x] **CP-D2 PASSED → GO (user ruled "Accept + fan out" 2026-06-27).** Re-pilot scored (zero cluster, on-disk recovery): **CBECS NMBE −17.6%, R² 0.40→0.91, CV 58%, EBEWE −8.6%, G2 (a)+(b) PASS**, schools sane (175.6/239.4), SuperMarket 115.9, B2 dropped only the Warehouse. **The CP-D "−3.1% PASS" was a BUG ARTIFACT** (school/exhaust blow-ups inflated the commercial mean; fixing them revealed the honest mean + leapt R²). Two B2 plumbing bugs found+fixed by the pilot (manager): R-B2.2 `verify_and_repair` defer + the `dropped_buildings.csv` `mkdir` (would've crashed every fan-out cell with a drop).
  - **Under-prediction investigation = structural DOE-prototype-vs-CBECS offset, NOT a bug.** Lives in offices (112/161 commercial) all below CBECS Office 154: **SmallOffice 98** (`equipment_w_m2=6.78` in `doe_prototype_loads.json`), **Medium/Large 135-138** (`10.76`) — those are the **DOE prototype values themselves** (code-compliant idealizations) vs CBECS real older higher-plug stock = the same residual STOP-decided at R6-4B / confirmed V16–V19. Plus a composition effect (cell office/retail-heavy vs CBECS pop mean 188). Phase-E already **halved** the gap (−39→−16); closing further = fitting office loads to the benchmark = breaks **zero-fitted-params** → accept-and-report. Watch-items: retail +29% high; restaurants equipment-dominated 884–1326.
- [x] **T17 11-cell fan-out — COMPLETE 2026-06-27** (bg `bb7vpmqix`). 12-cell matrix complete; 8,160 buildings; 99.9% E+ success. la_rural: 5 B2 drops (OSM vertex winding defect, Lancaster CA; `REPORT_phaseE_final.md §5`).
- [x] **T18 re-score — COMPLETE 2026-06-27.** `scripts/validation/phaseE_rescore.py`; 3 figures in `openubem/outputs/`; `REPORT_phaseE_final.md`.
  - **CP-E RESULT:** Fleet 8,150/8,160 success (99.9%). R²=0.895/0.924/0.718 — excellent shape. City-Overall: NYC −24.4%, LA −5.6%, Austin −25.7% vs measured anchors. CBECS NMBE: −10.6%/−20.5%/−11.9% (hard gate fails). Under-prediction = structural DOE-prototype-vs-CBECS "Other" offset (R6-4B residual) — reconstruction was carrying the level; closing it = fitting = rejected. **Phase-E is the scientifically honest OpenUBEM baseline. ARC COMPLETE.**
- [x] **REMEDIATION Phase R1 — CP-R1 AUDITED + ACCEPTED 2026-06-27.** Plan: `docs/docs_ACTIVE/hvac-ServiceLoads/remediation/PLAN_phaseE_CPD_remediation.md` (rulings in §9). R1 delivered: SAT reset (RD2) on VAV/PVAV/CRAH (regression-clean), B2 logged-drop tolerance, G2 per-archetype gate, W1 confirmed. B1 reframed to geometry defect (see above). Manager rulings D1–D4: D1 RD3 dead/0.30 locked; D2 geometry-screen folded into B2 drops; D3 G2 verdict = gates (a)+(b) only, gate (c) report-only; D4 don't block on 2 pre-existing fails BUT fix `dhw.py:50` no-zone crash + **verify `total_eui` doesn't double-count fans (STOP P1 if it does)**.
- [~] **Phase R2 — D2 RETRACTED, prevalence scan in flight 2026-06-27.** Non-D2 work all clean (94 tests green): **D4(b) P1 gate PASSED** (fans counted exactly once in `total_eui` — CP-D wins NOT inflated), D4(a) no-zone crash fixed, D3 gate-(c) demoted, fixture restored. **D2 `.err`-screen FALSIFIED by executor** (the "Volume≤0" warning is anti-correlated with pathology — healthy LargeOffice has 44 such zones, runaway schools have 1). New fork: **A** = build-time geometry repair (correct, recovers buildings, fixes Warehouse, but touches validated Step-3 + needs re-sim + **scope expansion → user decision**); **B** = post-sim drop on clamped-zone floor-area fraction (climate-independent, low-risk, manager call if prevalence small). **Read-only scan of existing 617 `.sql` dispatched** (no cluster/sim) to measure prevalence + test the discriminator. Rule: clean + ≤tolerance → adopt B, re-pilot → CP-D2; systematic/no-clean-discriminator → HOLD + present A-vs-B to user. **HOLD at T18 for user** regardless. No commits (git external).
  - [x] **SCAN RESULT 2026-06-27.** Volume clamp is **UNIVERSAL: 587/617 (95%) clamped**, incl. 446 healthy MidriseApts — benign geomeppy artifact (never broke Phase-D/E validation). **No clean geometry discriminator** (pathology = clamped × high design-load × HW-reheat × SINGLE-ZONE; multi-zone Courthouse same-family is healthy). **Genuine pathology = exactly 2 single-zone PrimarySchools (0.32%)**; headline wins robust to them (D4(b) confirmed not inflated).
  - [~] **OPTION C guard DONE — manager-authored (CP-R1.8, 2026-06-27) → Sonnet dispatched for E+ verify + re-pilot (IN FLIGHT).** `hvac.py` single-zone guard (`_CENTRAL_OR_VAV_FAMILIES`, `_RESIDENTIAL_ARCHETYPES` consts; 1-zone non-res on central/VAV/PVAV-reheat → `"PSZ-AC w/ Gas Furnace"`; central DC → `_emit_crac_proxy`; residential + already-packaged untouched; downgrades logged); `test_hvac.py` 4 fixture-zone bumps (LargeOffice/LargeHotel single-zone tests → 2 zones) + new `TestSingleZoneGuard` class (5 tests). Manager-run tests: **58 passed** (test_hvac.py) + **32 passed** (test_idf_builder + test_b2_drop_tolerance). `hvac.py` + `test_hvac.py` FROZEN. Sonnet in-flight: (1) full pytest suite regression; (2) local 2-school E+ verify (STOP if phantom-cooling-gain inflates under PSZ); (3) R-RP full la_urban re-pilot (sbatch) = **CP-D2**. Re-pilot carries SAT reset + B2 + C-guard + D3 + D4. Backstop (Option B drop) deferred per user's C choice; Option A (geometry repair) = future work item. No fan-out without manager CP-D2 greenlight; **T18 final report HELD for user**.
  - [~] **TRUE ROOT CAUSE CONFIRMED (CP-R1.9, 2026-06-27) — KITCHEN-EXHAUST bug in `cooking.py`; SUPERSEDES both the geometry (CP-R1) and VAV-reheat (RD1) attributions.** Controlled experiment on byte-identical clamped geometry: Phase-D heating design load 2,021 W (sane) vs Phase-E 47,487 W (blown), **identical across PTAC/PSZ-AC/PSZ-HP** → not geometry-clamp, not HVAC system. Driver: `ZoneVentilation` kitchen exhaust = fixed absolute `exhaust_m3_s` (PrimarySchool 2.124 m³/s = 4500 cfm) on a hardcoded constant-1.0 (24/7/365) schedule on one zone; main HVAC fully conditions ~36 kW make-up air. **USER RULING: "Area-scale + schedule."** **Manager-authored fix** (delegated exception, same as CP-R1.8; Sonnet runs sims): `cooking_by_archetype.json` added `prototype_floor_area_m2` per food-service archetype (FSR 511 / QSR 232 / LargeHotel 11345 / Hospital 22422 / SecondarySchool 19592 / PrimarySchool 6871); `cooking.py` exhaust `Design_Flow_Rate = exhaust_m3_s × min(1, total_area/prototype_area)` on a new 5am–1am `Schedule:Compact` (RESULT_04 Table 3) replacing 24/7, make-up air still fully conditioned, `_sched_cook_exhaust_once` helper; `test_cooking.py` +4 tests. Manager-run pure-python: test_cooking.py **26 passed**, test_idf_builder.py **26 passed**, test_hvac.py **58 passed**. Sanity: 2 la_urban schools' exhaust 2.124 → 0.0175 / 0.0787 m³/s. `cooking.py`+`cooking_by_archetype.json`+`test_cooking.py` FROZEN; Option-C guard KEPT. **Broader implication:** same bug likely inflated the QSR/FSR restaurant outliers that crushed R² at CP-D → fan-out-quality fix, not a 2-school patch. Sonnet in-flight (NOT complete, no sim numbers yet): full pytest regression + local 2-school E+ re-verify + restaurant-outlier spot-check → R-RP la_urban re-pilot (sbatch) = **CP-D2**. No fan-out without manager CP-D2 greenlight; **T18 final report HELD for user**.
- Gates are report-only — never tuned to pass.

---

## F. Resolution-mode switch — **CP4 PASSED — all 4 modes GO (2026-07-01)**

Plan: `docs/docs_ACTIVE/simulation-Resolution/PLAN_resolution_mode_switch.md`. Binding spec: `openubem/geometry/zoning.py` contract + 5-mode table in `SIMULATION_RESOLUTION_zoning_by_building.md §1b`. Goal: expose `resolution_mode` param so users can force `building`/`floor`/`fast_zone` zoning instead of the adaptive `auto` default — zero physics change, `auto` baseline bit-identical.

- [x] **T01** — `decide_zoning_strategy` extended with `resolution_mode` param (4th arg, default `"auto"`); forced branches before existing auto logic; `"zone"` → `NotImplementedError`; unknown → `ValueError`. `build_zones` untouched. 43 tests green.
- [x] **T02** — `BuildingIDF.__init__` signature updated; `resolution_mode` stored and threaded to line-291 `decide_zoning_strategy` call. Bit-identical for all existing callers.
- [x] **T03** — `_build_one` + `run_step3` signatures updated; fail-fast validation at `run_step3` entry; serial and loky paths both thread `resolution_mode`.
- [x] **T03b** — `resolution_mode` recorded in every manifest row (5 return sites in `build()` + `_worker_exception_row`). Step-5 results schema untouched.
- [x] **CP1 — PASSED.** Feature wired. Auto-baseline regression clean.
- [x] **T04** — `tests/test_zoning.py` extended: new `TestForcedModes` class (19 tests): forced-mode inversions, gate-bypass assertions, `auto` re-assertions, `"zone"` → `NotImplementedError`, unknown → `ValueError`. 43 passed.
- [x] **T05** — `tests/test_step3_orchestrator.py` extended: `TestResolutionModes` class (7 tests): per-mode fleet strategy, `resolution_mode` column propagation, `num_zones` ordering (building ≤ floor ≤ fast_zone), auto regression, `"zone"` fail-fast. 17 passed.
- [x] **T05b** — `test_load_conservation_across_modes` standalone: 1-floor MediumOffice (30×50 m); all three modes → lights=16140.0 W, equip=12105.0 W, people=161.29; `WaterUse:Equipment=1` in all modes; F11+F13 confirmed within 1e-6.
- [x] **T06** — `tests/test_resolution_mode_live.py` NEW: LIVE_SMOKE on real nyc_rural MidriseApartment + SmallOffice footprints via `fast_zone`; skips cleanly if fixture absent; no E+ run. 1 passed (skips on clean checkout).
- [x] **CP2 — PASSED 2026-06-29.** Full `pytest tests/test_zoning.py tests/test_step3_orchestrator.py tests/test_resolution_mode_live.py` → **60/60 passed** in 44.49s.
  - Per-mode `num_zones` totals on synthetic_10: building=10, floor=30, fast_zone=138 (auto=42). R7 narrow fallback=2, R10 gear fallback=1.
  - Load conservation (F11/F13): 1-floor building → all three modes identical; WUE pinned to zones[0] exactly once per mode.
  - LIVE_SMOKE: 4/4 success; 3 hit surfaces.py "Perimeter depth is too great" fallback (complex OSM polygons); way/270445757 SmallOffice 228 m² → 9 zones (full perimeter_core path verified on real footprint).
- [x] **T07 — small pilot, all 4 modes — DONE.** `auto`/`floor`/`fast_zone`/`building` ran E+ + parsed clean; surfaced the `orient()` regression in `auto` (→ T07b fix, CP3b PASS, restored to phaseE baseline).
- [x] **T08 — full 12-cell re-sim, all 4 modes — HARVEST COMPLETE 2026-06-30; CP4 PARTIAL (NO-GO on `building` mode).** All 5 cluster cells (nyc_centre/urban/suburban/rural, la_centre) × 4 modes + local 7-cell remainder harvested: 8,160 buildings/half, fatal-free. `openubem/outputs/comparisons/t08_all_modes_eui.csv` (+ `_mode_cell_summary.csv`, `t08_*.png`).
  - Harvest parse bug (no `total_floor_area_m2` column in phaseE fixture → division-by-zero on all buildings) found + fixed (manager patch, local re-parse, no cluster contact); both halves now carry real EUI.
  - **CP4 finding:** `auto`/`floor`/`fast_zone` conserve full footprint×levels area exactly (bit-identical internal loads). **`building` (single_zone) mode does NOT** — models one zone of footprint-only area for multi-floor buildings (~1/num_floors too low; nyc_centre 102.7 vs auto 198.9 kWh/m²); low-rise cells unaffected. T05b's synthetic fixture was single-floor and missed it.
  - **VERDICT: GO on `auto`/`floor`/`fast_zone`. NO-GO on `building` mode** pending fix.
  - [x] **T08b — fix `building`-mode floor-area conservation — DONE + AUDITED (CP-fix PASS 2026-06-30).** single_zone carries `floor_area_m2 = footprint×num_floors`; assign_loads emits absolute design levels; 3 service emitters honor explicit num_floors. New `test_load_conservation_across_modes_multifloor` (5-floor) green; `pytest -k conservation` → 2 passed.
- [x] **CP-resim — building-mode 12-cell re-sim + conservation — PASSED 2026-07-01 → CP4 GO on `building`.** Cluster 5 cells (jobs 1048357–1048361) COMPLETED 0:0 across 4,530 tasks; local 7 done. **Stale-CSV trap** caught + resolved (first harvest reused pre-fix cached SQLs; the actual cluster IDF/SQL carry the fix — 67-floor tower way/265875648 InteriorLights 26.465 kWh/m²; only the aggregated CSV was stale, rebuilt from fresh SQLs, no relaunch). Conservation on fresh data: **all 12 cells `N_ratio<0.35 == 0`**, `median(bld/floor)` 0.861–1.000 (healthy 0.75–1.05 band). **M18 NO-GO resolved; all 4 modes {auto/floor/fast_zone/building} GO**, `zone` NotImplementedError by design. Table + evidence = PLAN §8 CP-resim entry. Follow-up (non-blocking): sanity-check tall-tower DHW scaling (~36.9 kWh/m²) in T09.
- [x] **T09 — author `deepResearch/literatureValidation/` prompt set — DONE + AUDITED 2026-07-01.** `deepResearch/literatureValidation/` = `00_README` + `V01–V06` (manager authored index+V01 exemplar; Sonnet authored V02–V06; manager audited). Axes: V01 annual-EUI sensitivity, V02 heating/cooling end-use split, V03 peak/sizing (report-only, GAP until AMI), V04 daylighting over-prediction (D7-off absolute+relative), V05 district wash-out (load-bearing), V06 archetype-cohort stratification. Commissions external envelopes to bracket T08/CP4 deltas — the in/out-of-envelope comparison vs returned `RESULT_V0x` is the follow-on after external run. Audit: 6 files, 8 sections each, cells empty, no fabrication, no `.py`. **Resolution-mode arc fully authored; all 4 modes GO, `zone` deferred by design.**

---

## G. Input-parameter imputation ("OpenUBEM AI") — **Phase A+B COMPLETE (CP-1, CP-2 MET); Phase C CP-3 CLOSED NOT-MET 2026-07-03 (attribute-leg marginal `knn` win; EUI do-no-harm leg FAILS −5.51 % NMBE) — USER ACCEPTED built-but-off ("keep it", per-target registry preserved); arc PARKED, T11.7 not pursued; Phases D–E gated**

New feature arc: impute/predict missing pipeline **input** parameters across four user-named tiers
(basic stats → "OpenUBEM AI" subsystem → basic ML → advanced/data-driven). Docs under
`docs/docs_ACTIVE/input/imputation/`. Grounding: manager audit `REPORT_missing_input_handling.md` +
İşeri et al. in-repo paper.

- [x] **Deep-research prompt set authored** (10 prompts M01–M10 + README), 2026-07-01.
- [x] **9/10 RESULT reports returned + audited** by manager (M01–M07, M09, M10; **M08 not run** — its
  subsystem-architecture synthesis folded into Phase B of the plan). User ran them via Gemini Antigravity.
- [x] **Implementation plan written + grounded in live code** — `PLAN_input_imputation_implementation.md`
  (T01–T13, five phases, four checkpoints). **Key finding: not greenfield** — `imputation.py` already
  ships the KDE/PDE tier + a `build_ml_imputer` **Phase-2 stub** (DESIGN §3E / F12); this arc = execute
  §3E Phase 2 + close the audit's Tier-B silent-default provenance gaps + add the research-endorsed
  fusion/spatial tiers + the M09 validation harness. Research verdict binds method choice:
  **classical-ML/spatial adopted, neural/GNN/LLM deferred-or-rejected** (zero-fitted-params + small-n).
- [x] **Phase A** (T01–T06) — provenance-complete statistical MVP: **COMPLETE + CP-1 MET 2026-07-01.**
  T01 provenance schema; T02/T03 HVAC/DHW/cooking Tier-B closures; T04 `year_built` donor/neighbour
  vintage (PINNED CONTRACT v2, position-stable, 52/52); T05 group-wise `levels` (+ wave-2b test cleanup,
  128/128); T06 spatial neighbour-fill + MNAR guard. **CP-1 CHECKPOINT MET:** (1) five gate suites 75/75
  green; (2b) MNAR-block deactivation discharged at unit level (`TestMNARGuard` + `TestMnarBlocksSpatialFill`);
  (2a) Tier-B instrumentation-only CONFIRMED via **exact local IDF field-diff** (user-ratified method,
  supersedes the planned `sbatch` full-sim) — 25/25 IDFs BYTE-IDENTICAL over a 24-archetype coverage fleet,
  current Tier-B vs `e063865` baseline, isolation invariant filecmp-verified. Dormant caveat (non-firing on
  all current data, carry-forward to M09): Tier-B also fixes a literal-`0`/`NaN`-truthiness edge that would
  change values only if a COP/area field ever carried 0/NaN. → **CP-1 ✅**.
- [x] **Phase B** (T07–T10) — "OpenUBEM AI" routing subsystem + strict mode + M09 validation harness
  (mask-and-recover, spatial-block hold-out, mandatory downstream-EUI check, optional `--replicates`).
  → **CP-2 FULLY MET 2026-07-03** (synthetic LIVE_SMOKE ✓ + real-OSM-city cluster A/B ✓). **COMPLETE 2026-07-02.**
  - [x] **T07** — routing orchestrator `impute_missing`/`ImputeConfig`/strict mode + `StrictImputationError`
    (`imputation.py`, `config.py`); **ACCEPTED** — 18/18 routing tests, CP-1 gate suite 183/183, and
    **no-reroute VERIFIED byte-identical** (`enrich_semantics` 0-diff, `test_step22_orchestrator` 21/21
    incl. 57-col/29-col byte-identical checks) so the CP-1 guarantee holds. Both carry-forward STOP-gates
    correctly tripped rather than worked around.
  - [x] **T07.1** — **GREENLIT.** The two ratified carry-forwards: legacy tier-less token reweight in
    `_field_score` (KDE/HEURISTIC→MED, PDE/ASHRAE_STANDARD→LOW; blast radius manager-verified =
    `add_lineage_summary` only, no EUI path) + lineage summary as a **side manifest** in the
    `enrich_semantics` return-dict (schedule-lib dict, inserted after the JSON dump so on-disk artifacts +
    57-col frame are untouched by construction). `test_provenance` 21/21, `test_step22_orchestrator` 21/21
    (byte-identical checks pass). IDF-build path verified to consume the dict by keyed lookup only, so the
    new key is inert; the in-flight T11 run uses committed code so is unaffected.
  - [x] **T08** — **ACCEPTED.** Mask-and-recover + spatial-block hold-out harness
    (`validation/mask_recover.py`), 22/22. Continuous path runs the real `impute_missing` router and scores
    recovery vs held-out truth; whole-block hold-out (no row-leakage); KS-fidelity metric bites; no EUI,
    no tuning. Surfaced that the router is continuous-only → `use_class` NOT_SCORABLE (honest, not
    fabricated) → resolved by T07.2.
  - [x] **T07.2** — **ACCEPTED** (45/45). Categorical routing in `impute_missing`: `use_class` via T06
    `neighbour_vote` (spatial) + group-**mode** (statistical), §5G tokens reused; continuous byte-identical;
    self-stratification leakage guard proven by test. Completes the routing subsystem — mask-and-recover now
    scores both input types. (Logged limitation: `_spatial_tier` discards T06's `gdf_out`, so the MNAR
    diagnostic flag isn't surfaced in `impute_missing` output — mandatory-provenance-on-values still holds;
    candidate M09-harness enhancement.)
  - [x] **T09 (math + scaffold)** — **ACCEPTED** (15/15, NO sim). Paired ASHRAE-G14 MBE/CV(RMSE)/peak
    comparator (5%/15% targets) + `compare_ab` A/B scaffold wrapping the real Stage-3→5 harness; read-only-
    on-imputer enforced structurally. Correctly rejected the unpaired CBECS quantile comparator.
  - [x] **T09 LIVE_SMOKE — DONE 2026-07-02.** Downstream-EUI A/B on a 36-bldg purpose-built synthetic fleet
    (6 clusters × 6 archetypes, real ground-truth year_built/levels, genuine spatial-block holdout, local E+,
    27 min, 0 fatals, 0 dropped). **Both M09 Step-C gates PASS:** fleet NMBE **0.012%** / CV(RMSE) **1.75%**;
    manager-recomputed held-out-only (10 rows) NMBE **≈0.04%** / CV(RMSE) **≈3.1%** — pass with wide margin.
    Tier breakdown: 10 held-out all `GROUPMODE_MED` (statistical fallback), spatial tier never fired =
    protocol-expected (block holdout removes same-cluster donors; 100 m radius ≪ 3–7 km spacing). **Manager
    caveats:** provisional pass on *homogeneous-cluster synthetic* data (optimistic floor); only the
    group-median tier exercised; fleet CV(RMSE) diluted by 26 unchanged buildings (held-out-only ≈3.1%).
    **USER DECISION 2026-07-02: larger synthetic now + cluster-confirm later** — this is the provisional gate
    number; **real-OSM-city cluster A/B owed as confirmation once T11 frees the cluster** (before Phase C ships).
  - [x] **T09-CC — Real-OSM-city cluster A/B (CP-2 CONFIRMATORY) — CONFIRMED 2026-07-03.**
    USER DECISION 2026-07-02: **"queue cluster A/B first"** (definitive number before Phase C planning).
    Two feasibility inventories done (LOCAL reads — real footprints committed at `.../phaseE/<cell>/01_buildings.gpkg`,
    23-col schema DOES carry `year_built`). **PINNED:** target = **`year_built`** (EUI-relevant via
    `resolve_vintage`→DOE construction sets); primary gate cell = **`nyc_centre`** (158 complete-case, flattest
    5-vintage spread → recovery genuinely stressed + spatial donor tier fires; retires the synthetic
    "too-homogeneous" caveat); secondary robustness cell = **`la_urban`** (542). Held-out = spatial-block 80/20
    over complete-case year_built; headline = **held-out-only** NMBE/CV(RMSE) (fixes dilution). **Phase 2a
    PASSED (2026-07-02)** — driver `t09cc_realcity_ab_nyc_centre.py` + 6-bldg local E+ wiring smoke: masking +
    real tokens (32 held-out = 30 GROUPMODE_MED + 2 HOTDECK_NEIGHBOR_HIGH), common-mode isolation EXACT
    (levels/geometry/etc 0/32 diff A-vs-B, only vintage-derived fields move), EUI sane + physics-correct
    (vintage-matched→byte-identical EUI; 2013→Pre1980 miss→+14%), held-out metric computes. Recovery via
    production `resolve_vintage`/T04 path (manager-accepted, stronger than the generic `impute_missing` reimpl
    which stays a CP-3 carry-forward). **Phase 2b DISPATCHED (Sonnet):** scale to ALL held-out (nyc 32×2 +
    la_urban ~108×2 ≈ 280 sims), sbatch array at STANDARD priority behind T11, harvest per-cell held-out-only
    NMBE/CV(RMSE). NOTE — real test: 11/32 vintages mis-recovered by group-mode ⟹ gate number non-trivial,
    could exceed 5% (a legitimate CP-2 outcome, unlike the rigged-green synthetic).
    **Phase 2b SUBMITTED 2026-07-02 — all 4 arrays queued behind T11, correct climate:** nyc_centre GATE
    (real NYC 725053 EPW, N=32) jobs 1058656/1058657; la_urban robustness (real LA EPW, N=124) jobs
    1058653/1058654. Manager caught + fixed a gate-critical defect (nyc initially on a Chicago placeholder EPW →
    HDD-inflated ΔEUI near the 5% line; scancel'd + resubmitted under real NYC weather). All PD under
    AssocGrpCpuLimit behind another project's array (1058490) + T11 (1058600), both untouched — number lands
    after the queue drains (hours). Harvest = per-cell held-out-only NMBE/CV(RMSE) via compare_ab (low-freq
    Sonnet monitor dispatched). **HARVESTED + CP-2 CONFIRMED 2026-07-03 (manager-audited):** all 4 arrays
    COMPLETED clean (0 dropped/0 parse-fail; N_paired 32 nyc / 124 la = full held-out set); held-out-only paired
    ASHRAE-G14 via `eui_impact.nmbe`/`cv_rmse` — **nyc_centre (GATE) NMBE +0.49% / CV(RMSE) 1.71%; la_urban NMBE
    +0.08% / CV(RMSE) 0.61% — both PASS 5%/15%.** Verified the actual gate fleet dirs ran real NYC Central Park +
    LA EPWs (harvester's "Chicago" footnote was a stale docstring read; numbers valid). Corroborates synthetic
    (CV(RMSE) 1.71% ≈ 1.75%). **CP-2 fully MET; Phase C SHIP-unblocked, NOT started — awaits user scope greenlight.**
  - [ ] **T10** — optional `--replicates M` uncertainty mode — **deferred** (not a CP-2 gate condition).
  - Phase-C carry-forward LOGGED: `impute_missing`'s generic vintage/levels reimpl may bin differently than
    the production `resolve_vintage`/`_impute_levels` — reconcile byte-identity when Phase C reroutes
    `enrich_semantics` through the orchestrator (T11+); not a Phase-B blocker.
- [~] **Phase C** (T11, GATED) — classical-ML imputer; ships only if it beats Phase-A baseline on
  mask-and-recover AND passes the EUI check. → **CP-3**. `PLAN_phaseC_ml_imputer.md` (T11.1–T11.7 +
  CP-3a/CP-3). User scope 2026-07-03: **full M04 six-method sklearn menu** behind one registry; EUI
  check = local IDF field-diff primary / cluster on divergence.
  - [x] **T11.1–T11.5 built** (Sonnet) — `build_ml_imputer` + 6-method registry, `_ml_tier` wiring,
    `_CANONICAL_TIER_ORDER` reorder, `impute_column` auto/model_path, joblib persistence; `test_ml_imputer.py` 40/40.
  - [x] **CP-3a MET 2026-07-03 (manager-audited)** — read the load-bearing file+tests; ratified T11.2
    `ML_<METHOD>_<TIER>` tokens into parent §5G; **ran a local probe that REFUTED a mean-fill risk the
    executor's finite-only tests didn't cover — all 6 methods verified feature-dependent** (missforest
    |Δ|=84.8 across footprint, 200-row spread 25.5 ≈ target std 26.1). Opt-in intact (`ml` ∉ default tiers).
  - [x] **T11.6 / CP-3 — CLOSED 2026-07-03 (manager-audited): NOT fully MET.** Step-0 test reconciliation
    green (171/0). Pooled 12-cell frame (n=8160, EPSG:5070; year_built N=2247 clears RF floor, levels N=441
    clears kNN floor only). **Attribute leg MET-but-marginal — winner = `knn`** (only method beating Phase-A
    on both targets): year_built MAE 26.4→25.1 (~5%) + better KS/Wasserstein but **exact-vintage-bin ~flat/
    slightly worse (456→449)**; levels MAE 9.18→8.39. **Flagship `missforest` does NOT beat Phase-A; `mice`/
    `linear` catastrophically extrapolate (MAE 900–1160) with HIGH confidence — real footgun.** **EUI do-no-harm
    leg FAILS:** cluster A/B (jobs **1064373** Phase-A / **1064406** Phase-C-knn, 167 IDFs each) harvested clean
    — EPW station 725053 confirmed via E+ `.eio` `Site:Location`, 167/167 both branches, footprints byte-identical
    A-vs-C — paired **NMBE −5.51 % (breaches <5 %), CV(RMSE) 7.93 % (passes <15 %)**; all 167 buildings shift
    DOWNWARD (systematic bias, not scatter — `knn` regresses vintages toward the newer urban-core stock).
    **VERDICT: ML does not clear the ship bar. USER ACCEPTED built-but-off 2026-07-03 ("one method need not cover
    all input params, keep it"): ML tier kept opt-in/off, per-target registry preserved, arc PARKED; candidate
    future fix (not scheduled) = observed-range/vintage-bin clamp then retry. T11.7 not pursued.**
- [ ] **Phase D** (T12, GATED/scoped) — fusion-first external joins (Overture/LiDAR/assessor, runtime-
  fetch, nothing bundled); LIVE_SMOKE before ship. → **CP-4**.
- [ ] **Phase E** (T13) — frontier documented-deferred (deep-generative/GNN/LLM out of scope; optional
  isolated experimental TabPFN track, never default).
- **STATUS (2026-07-03): Phase B COMPLETE — CP-2 FULLY MET (real-OSM-city cluster-confirmed).** All 5
  deliverables ACCEPTED (T07 router / T07.1 lineage side-manifest / T07.2 categorical routing / T08 mask-recover
  22/22 / T09 comparator-math 15/15); synthetic LIVE_SMOKE passed (fleet NMBE 0.012% / CV(RMSE) 1.75%); and the
  **definitive real-OSM-city cluster A/B lands PASS on both cells** — nyc_centre (GATE) N=32 NMBE +0.49% /
  CV(RMSE) 1.71%, la_urban N=124 NMBE +0.08% / CV(RMSE) 0.61%, both inside 5%/15% with wide margin; real NYC/LA
  EPWs verified on the gate fleet dirs; zero-fitted-params intact. The confirmatory number the user owed to see
  before Phase C ships is in hand and passes. **Phase-C CP-3 now CLOSED, NOT fully MET 2026-07-03** (manager-audited):
  CP-3a MET (local probe refuted a mean-fill risk → all 6 methods feature-dependent); attribute leg MET-but-marginal
  (winner `knn`, flagship `missforest` loses, `mice`/`linear` dangerous); **EUI do-no-harm leg FAILS** — cluster A/B
  harvested clean (EPW 725053 confirmed via `.eio`, 167/167, footprints byte-identical) but paired NMBE −5.51 %
  breaches the <5 % gate (CV(RMSE) 7.93 % passes); `knn` shifts all 167 nyc_centre buildings systematically downward.
  **Manager rec: ML stays built-but-off; T11.7 NOT unblocked. Awaiting user: accept built-but-off OR authorize an
  observed-range/vintage-bin clamp-and-retry.** Phase-C carry-forward (only if a ship is ever authorized) =
  re-establish `enrich_semantics` byte-identity when T11 reroutes through `impute_missing`. Optional deferred:
  held-out-only CV(RMSE) in `eui_impact_report`; T10 `--replicates`. Phases D–E stay GATED.

---

## H. `layoutGenerator` — room-level interior zoning (`zone` mode) — **Phases 0–4 DONE; CP-1 + CP-2 + CP-3 MET 2026-07-02; Phase 5 STARTED: T13a (hotels) ACCEPTED; T13b/T13c (offices/schools) DEFERRED (Opus); T14 FIRED 2026-07-03 (apartments + hotel re-fire after classifier ft-or-bt fix); T17 per-archetype grids DONE (hotels); harvest→T15→CP-4 USER SIGN-OFF not started**

Implements the `zone` resolution mode left as `NotImplementedError` at the close of arc F. Builds a
plausible **room-level floor plan** from a building's true footprint: classify shape → decompose
non-rectangular wings → pack a double-loaded corridor + DOE-standard room modules → per-space-type
loads with exact area/load conservation. Closes the real gap where the coarser strategies **silently
degrade any L/U/T/courtyard footprint to one-zone-per-floor** (a courtyard/donut footprint otherwise
causes an EnergyPlus *Fatal*). **MidriseApartment first** (its DOE prototype *is* a corridor+units
layout → self-validating), then offices/hotels/schools where room-level detail moves EUI 10–20%.
**Opt-in only** — `auto` and the adopted 8,160-building baseline are untouched (D-B). Zero fitted
parameters; provenance on every emitted zone.

Plan: `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/PLAN_layoutgenerator_implementation.md`
(mirrors the approved plan). Fundamentals write-up: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1.1.

### Phase 0 — scaffolding + classifier
- [x] **T01** — `layoutGenerator.py` skeleton + pinned `MODULE_SPECS` (MidriseApartment: corridor 1.68 m, unit depth 7.62 m, bay 11.58 m, unit 88.25 m², circ 9.9%) + public signatures. Every dim cites a source.
- [x] **T02** — `classify_footprint` — compact/slab/L/U/T/cross/O/ribbon/irregular via the L04 metric ladder (rectangularity, convexity, reflex-corner + OBB-notch count); pure shapely, `make_valid`+simplify first. Classifier unit tests green.

### Phase 1 — corridor-packing engine → **CP-1**
- [x] **T03** — `_pack_bar` double-loaded bar packer: OBB longitudinal centreline → 1.68 m corridor strip → two unit rows merged by cardinal orientation → `[corridor, N, S, E, W]`; fallback ladder (double ≥16.92 m / single 9.30–16.92 / offset-buffer / core<10 m² → one_zone_per_floor); sliver-merge guard.
- [x] **T04** — `_decompose_wings` (L/U/T/cross): orthogonal cuts at reflex vertices → hole-free rectangular wings → each routed to `_pack_bar`; dominant-*edge* alignment (fixed a symmetric-cross over-fragmentation where min-area OBB was diagonal).
- [x] **T05** — `_split_donut` (O/courtyard): tic-tac-toe cuts → 4 hole-free wings (never extrude a holed polygon → fixes the `zoning.py:89` courtyard E+ Fatal); inner-ring walls tagged Outdoors, inner/outer never merged.
- [x] **T06** — dispatch wiring: `decide_zoning_strategy("zone")` → `"room_layout"` for the units+corridor family (else `perimeter_core`); `build_zones` routes `room_layout` → `generate_layout` with `[]`→one_zone_per_floor fallback. `auto` untouched.
- [x] **CP-1 — MET.** Engine produces valid, area-conserving zones for rect/L/U/T/O MidriseApartment footprints; a `generate_layout` conservation safety-net drops to one-zone-per-floor if area drifts >1%; `auto` unchanged; no simulation yet.

### Phase 2 — per-space-type loads + conservation
- [x] **T07** — `openubem/data/loads/doe_space_type_loads.json` (Apartment LPD 5.27 / EPD 5.38; Corridor LPD 5.38 / EPD 0 / occ 0, Deru 2011 Table 3-51) + `get_space_type_loads` loader.
- [x] **T08** — Space-Type-Weighted Normalization in `assign_loads` (`I'_z = I_t·f_t·A_tot/A_t,gen`): building lighting/equipment/people conserve to the archetype total exactly regardless of geometry drift; corridor equipment/occupancy correctly zeroed (verified rel_tol 1e-9).

### Phase 3 — interior surfaces + synthetic sim tests → **CP-2 MET**
- [x] **T09** — interior boundary conditions: corridor↔unit = matched Surface, unit↔unit = Adiabatic, courtyard-inner = Outdoors; every generated zone sets `"extruded": True`; mismatch-gate kept happy. `test_layout_surfaces.py` — 9 tests, 0 mismatched interzone pairs.
- [x] **T10a** — **room_layout intersect_match fallback** (`surfaces.py::_force_reroute_room_layout_to_one_zone_per_floor`, manager/Opus): closes hard-rule #7 for the `zone` family — if geomeppy `break_polygons` ever raises on a room-level building (possible on live OSM footprints), the building degrades to one_zone_per_floor instead of `failed_worker_exception`. Reconstructs the true footprint (buffer round-trip closes sub-mm wing-seam drift); a real courtyard void ≥1 m² **declines** so no single holed block re-introduces the donut Fatal. 130 unit tests green; L→collapses cleanly, courtyard→declines.
- [x] **T10** — synthetic geometry + **E+ 0-Fatal smoke** (Sonnet, manager-audited). **All 5 shapes simulate clean:** full-annual E+ 23.1 runs — bar 15z/102surf, L 18z/114surf, U 30z/210surf, T 24z/162surf, O 48z/300surf — **every one Completed Successfully, 0 Fatal, 0 Severe**. Fallback did NOT fire (intersect_match succeeded first-pass on all synthetic shapes — it's the live-footprint net). Warnings are the known-harmless geomeppy "Floor/Roof upside down" vertex-order quirk + frost/freeze from deliberately-undersized synthetic HVAC. Plan §T10 has the full table + artifact paths.
- [x] **CP-2 — MET 2026-07-02 (manager greenlight).** Loads conserve across modes ✅, interior BCs correct + 0 mismatched pairs ✅, **0 E+ Fatal / 0 Severe on full-annual runs of all synthetic shapes** ✅, live-footprint fallback in place ✅. Phase 4 unblocked. (Not user sign-off — only CP-4 is.)

### Phase 4 — validation → **CP-3 MET 2026-07-02 (T11 DOE-repro PASS + T12 LIVE_SMOKE PASS after geometry fix; manager greenlight)**
- [x] **T11 — DONE 2026-07-02 (Sonnet, manager-audited) — PASS all thresholds.** DOE MidriseApartment prototype (46.33×16.92, 4 floors, 3.05 m) generated + simulated in E+ 23.1 vs `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` (version-transitioned to 23.1): area ~0% (PASS ±0.001%), per-space loads exact (PASS ±0.1%), circulation 6.66% vs 9.9% = −3.24 pp (PASS ±5 pp), **site EUI 114.63 vs 122.63 = −6.5% (PASS ±15%)**, 0 Fatal/0 Severe. Zones 20 (5/floor) vs DOE 27 (9/floor) = INFO, by design (L06 cardinal-merge, no intra-floor multiplier). Diff → `openubem/outputs/comparisons/t11_doe_vs_generated.md`. Weather caveat: both on Chicago TMY3 (no Buffalo EPW; internally fair). **Employee's DHW "District Heating" flag audited → baseline NOT affected** (production EUI reads explicit SQL meters via `parser.py::_parse_meters_sql`, never `eplustbl.htm`; no DistrictHeating summed). dhw.py physical-modeling review = lower-priority future note, not a blocker.
- [x] **T12 — DONE 2026-07-02 (Sonnet employee, local) — LIVE_SMOKE FAILED (as designed to catch).** Report: `openubem/outputs/LayoutGenerator/t12_live_smoke.md`. **Recon precondition MET:** 434/2,821 real MidriseApartments (15.4%) classify non-rect (L/U/T/CROSS/O) across 9/12 cells (richest `la_suburban` 228, `la_urban` 151) — the live path genuinely exercises the new geometry, not just synthetic boxes. **Both gates FAIL:** (1) zone-mode `run_step3` gen-success **80% (24/30)** on `la_suburban` (target ≥95%) — 6× `failed_interzone_vertex_mismatch`; (2) **4 of 5 real `generation_status=success` production IDFs are E+ 23.1 FATAL** despite parsing cleanly with geomeppy. **Two failure signatures:** (a) vertex-count / non-planar mismatch on `_WHOLE` zones → the **T10a internal reroute** (`surfaces.py:623`, my Opus code) does not repair real-footprint interfloor geometry (38-vs-41 vertex mismatch); (b) malformed-zone temp blowup (−871°C, −4.6M°C) on genuine room_layout zones → the **packer emits thermodynamically-degenerate slivers on messy OSM footprints**. Confirmed geometry (not pipeline) via standalone-recipe cross-check. Also surfaced: (c) manifest `zoning_strategy=room_layout` does NOT reflect the internal reroute (observability gap — 6/24 "successes" silently degraded to 2-zone); (d) `way/442340523` "success" ran with 103,394 warnings. **Synthetic 0-Fatal (T10/T16b) ≠ live-green — exactly the blind-spot rule.** Verbatim `.err` preserved in scratchpad `t12_real_idf_runs/<osm_id>/`.
- [x] **CP-3 — MET 2026-07-02 (manager greenlight; T11 DOE-repro PASS + T12 LIVE_SMOKE PASS after fix).** Root cause confirmed from a Fatal cell's IDF: way/442340538 `_W0C2` floor was a **degenerate triangle (2 verts 7 microns apart)** — real OSM footprints aren't exactly orthogonal, so axis-aligned grid cuts shear off near-zero-area slivers (→ E+ non-planar 538/549, or warmup temp blowup 503 −871°C / 539 −4.6M°C). **Fix = 4 surgical edits (Opus):** (1) `layoutGenerator.py` `_is_degenerate_cell` (area<2 OR narrower than `MIN_CELL_WIDTH_M=1.0` m via buffer test) → `_pack_connected_spine` **DROPS** slivers (NOT merge — merging remakes the T16b T-junction crash; the existing 1% area net degrades to one_zone_per_floor if too much drops); (2) `surfaces.py` reroute snaps footprint to 5 mm + simplify(0.02) → kills the near-collinear non-planar walls (549); (3) `builder.py` reflects a room_layout→per-floor degrade in manifest `zoning_strategy`; (4) `zoning.py` tags area-net fallback zones `room_layout_area_fallback` + `builder.py` honors it — re-validation showed the 4 footprints degrade via the area net (surfaces.py reroute fired 0×), so edit #3 alone would have left 25/30 rows mislabeled `room_layout`; edit #4 closes that. **130/130 unit tests green (donut2 machine-precision conservation intact).** **E+ re-validation (Sonnet employee, manager-audited) — all 4 gates PASS:** (A) 4 previously-Fatal footprints → **0 Fatal/0 Severe** (503 42Sev→0, 538 22→0, 539 1→0, 549 16→0; 523 warning storm 103,394→152); (B) synthetic bar/L/U/T/O/cross **STAY 0 Fatal/0 Severe**, reroute NO, room-level zoning intact (15–144 zones); (C) fresh la_suburban n=30 = **100% gen-success** (was 80%), 0 `failed_`; (D) 5 real non-rect footprints → **0 Fatal/0 Severe**. Report: `openubem/outputs/LayoutGenerator/t12_live_smoke.md`. **Intended graceful-degrade behavior:** most messy la_suburban non-rect MidriseApartments now legitimately fall back to per-floor rather than emit a broken room layout (correctness > coverage on adversarial live geometry).

### Phase 5 — expansion + full sim + DOE-vs-generated comparison → **CP-4 (USER SIGN-OFF)**
- [x] **T13a — SmallHotel + LargeHotel (units+corridor) ACCEPTED 2026-07-02.** L06-vs-L08 hotel-dim conflict RECONCILED (DOE/PNNL prototype dims win): SmallHotel corridor 1.83/depth 7.32/bay 3.66/unit 26.79; LargeHotel corridor 2.44/depth 7.32/bay 4.11/unit 30.09; GuestRoom+Corridor loads (Deru 2011 Table 3-51). **E+ smoke found a real defect: small hotel modules fragment complex footprints into fully-interior corridor cells too small for HVAC autosizing → Fatal/Severe.** Fix = per-archetype `complex_shapes_supported` flag (True only for MidriseApartment); `generate_layout` degrades small-module archetypes on multi-wing shapes (L/U/T/CROSS/O) to `one_zone_per_floor` (correctness>coverage). E+ re-validation via production dispatch: hotels bar room-level 0/0, hotels T/O degraded 0/0, MidriseApartment T room-level 0/0 (the 1 Fatal seen under a raw-load harness was confirmed a harness artifact — production α-normalized loads clear it). **155/155 unit tests.** Apartment path unchanged.
- [ ] **T13b/T13c — LargeOffice (corridor+core) + Primary/Secondary School (hybrid classroom-wing + assembly-block) — DEFERRED, Opus-delicate (new geometry), separate slices on user go.**
- [~] **T14** — cluster pilot. **FIRED 2026-07-03** (Sonnet employee, manager-audited): `scripts/cluster/t14_layout_pilot.py` new; **6 sbatch arrays / 240 tasks** la_suburban+la_urban × zone/floor/building (jobs 1064082/99/121 + 1064172/212/231); 40 non-rect MidriseApartment/cell, 100% gen-success. Arrays running (~hours); monitor cheap-model ≥30-min; harvest → `t14_zone_vs_floor_vs_building.csv` → T15. **⚠ FINDING: pilot is APARTMENT-ONLY — SmallHotel/LargeHotel = 0 in all 12 cells** (lodging rules `building_classifier.py:212/216` match `function_tag` only; OSM rows carry `building_tag=hotel` w/ non-lodging function_tag → miss; Hospital rule 5a checks ft OR bt, hotels check ft only). **⚠ zone degraded 69/80 to per-floor (11/80 kept room-level) → T15 reports ΔEUI on the 11, not the 80-avg.** **HOTEL GAP RESOLVED — user chose "fix classifier + re-fire" (T14-HOTELFIX, 2026-07-03):** `building_classifier.py` rules 3a/3b now `ft-or-bt` (mirror Hospital 5a); 149/149 tests; recon recovered **41 hotels/12 cells (21 simple-shape)**; re-fired **6 hotel arrays** (jobs 1064322/32/42 nyc_centre + 1064352/56/61 la_urban, `t14h_*`, 15 hotels/2 cells). Apartment arrays completed naturally. **⚠ FLEET-BASELINE IMPACT: 26 LargeHotel recovered in nyc_centre alone (formerly Office/TallBuilding) → fleet-wide promotion + city-EUI re-validation is a SEPARATE E-R3-3 item needing user sign-off; NOT done.** Harvest both `t14_*`+`t14h_*` when hotel arrays finish.
- [ ] **T15** — DOE-vs-generated comparison report + plots (zones, loads, EUI, runtime) → report + `.png`s in `openubem/outputs/`.
- [ ] **CP-4 — USER SIGN-OFF.** No production `auto` change and no baseline promotion without explicit user sign-off.

### Visual deliverable
- [x] **T16** — layout visual grid: DOE MidriseApartment single-floor reference panel + generated floor plans (bar/L/U/T/courtyard/rotated/wide-bar/cross), colored by space type. `scripts/plot_layout_grid.py` → **`openubem/outputs/LayoutGenerator/layoutgenerator_doe_vs_generated.png`** (all layoutGenerator figures now live under `openubem/outputs/LayoutGenerator/` per user directive 2026-07-02).
- [x] **T17** — per-archetype layout grids (the T16 figure **for every supported building type**), user-requested 2026-07-03. `plot_layout_grid.py` refactored to loop archetypes; **`layoutgrid_SmallHotel.png` + `layoutgrid_LargeHotel.png` DONE** (manager-verified by eye): bar shapes room-level GuestRoom/Corridor (5 zones), all 6 complex shapes honest "(degrades to per-floor)" panels (no `complex_shapes_supported`); CVD-validated colors. **T17b (user feedback "hotels look like recolored apartments"): panels now draw individual room modules — subdivide each band by `bay_width_m` → SmallHotel/LargeHotel bar = 24 rooms vs MidriseApartment 8 (3×), guest-room granularity now visible; corridor undivided; degraded panels unchanged; viz-only, model unchanged.** **T17c (user feedback "the two hotel grids are exactly the same"): hotels now draw compact+wide bars on a COMMON plate LENGTH (45 m / 60 m, viz-only) with per-archetype real width → SmallHotel 24 rooms + thin 1.83 m corridor vs LargeHotel 22 rooms + thicker 2.44 m corridor (wide 32 vs 30); manager-verified by eye, apartment untouched, viz-only. Difference is modest by nature (the two archetypes' floor-plate modules genuinely are similar).** **LargeOffice/Primary/SecondarySchool grids blocked on T13b/T13c** (script extends when their MODULE_SPECS land). **Open items flagged, NOT started (await user go): (a) T18-DIAG sliver zones on complex apartments — real geometry from full-span grid-cut bleed, needs E+ re-validation, Opus-delicate; (b) T13b/T13c offices+schools — not built (different geometry families); (c) "un-merge" hotels into per-guest-room thermal zones — real modeling change, E+ re-validation.**
- [x] **T16b — continuous corridor spine (manager/Opus, delicate) — DONE 2026-07-02, CP-2 RE-CONFIRMED.** User reviewed the T16 grid: DOE has one continuous central corridor but the generated L/U/T/O/Cross had a disconnected corridor stub per wing. Rebuilt so multi-wing + O route to `_pack_connected_spine` — wing midlines joined by orthogonal L-bridges into ONE network, `corridor = spine.buffer(c/2) ∩ footprint`, then a full-span `_grid_cut` (corridor-edge + wing-bound lines) into simple hole-free cells. **Conforming by construction → no merge step**, so the O-loop is cut at corners (donut Fatal cannot re-form) and geomeppy `intersect_match` never hits its coplanar-containment IndexError. (An earlier aggressive-merge cut looked cleaner at 8–15 zones but created T-junctions that crashed geomeppy on L → reroute → degenerate surfaces; removed it.) Single-wing (compact/slab) path UNCHANGED → T11 stays valid. Corridors now continuous & turn corners; zones/floor bar 5 / L 15 / U 27 / T 18 / O 48 / cross 21 (honest conforming count for continuous-corridor non-rect footprints); **area drift +0.00000%, min edge 1.68 m, intersect_match OK direct (no reroute); 130/130 unit tests green.** **E+ 23.1 re-verify DONE (Sonnet full-annual, Chicago TMY3): bar/L/U/T/O/cross all Completed Successfully, 0 Fatal / 0 Severe, reroute-fired=NO. L kept room-level zones (45, `_w0c0…`), O courtyard loop clean (144 zones). Extruded zone counts L 3→45, U 30→81, T 30→54, O 45→144, cross 36→63; bar 15 unchanged. → CP-2 RE-CONFIRMED for the revised geometry.**
