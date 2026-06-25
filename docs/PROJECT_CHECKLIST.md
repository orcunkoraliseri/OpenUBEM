# OpenUBEM — Master Progress Checklist

> Single-glance tracker. Past = one line each. **Current** and **Future** carry the detail.
> Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked / needs decision
>
> **Last updated:** 2026-06-22

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

## B2. Current focus — Phase D real-HVAC resim (Phase-2 DESIGN deviation)

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
- [~] **Phase 6 — office heating-setback bug fix + resim (IN FLIGHT, user-authorized 2026-06-25).** Diagnosis of NYC office +11% found a verified defect: all 3 office `Heating_Setpoint_*` schedules miss the weekday evening setback (hold 21.1°C to 24:00; weekends + DOE prototype drop to 15.6 at 19:00) — an OQ-2 digitization bug over-heating offices in cold climates. (Infiltration 0.000285 examined → NOT a defect; furnace/envelope OK.) Plan = PLAN §"Phase 6" (T15–T18, CP-7/CP-8). Resim goes to a NEW `phaseD2` subdir (adopted `phaseD` stays safe until CP-8). T15/T16 (audit + correct + local smoke) running on a Sonnet employee; STOP at CP-7 for manager pre-resim audit.
- [ ] **Future (scoped, not started, non-blocking):** (1) regional CBECS end-use fractions — needs new EIA microdata extraction to trim NYC-Overall climate overshoot; (2) cooling-COP/0.75-derate + gas-eff 0.945 secondary HVAC levers (resim-gated, not indicated).

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
- [!] **OPEN DECISION (not urgent — needed when manager drafts the fix plan):** does "fix don't skip" extend to buildings dropped at GENERATION (Shapely multi-geometry / geomeppy IndexError → `not_simulated`), or are pure-unbuildable-geometry drops acceptable within the ≥95% generation gate? This sets how large the geometry fix is.

### C2. Cross-cell synthesis + final report
- [x] V19 full re-score across all 12 Phase C cells vs V17 anchors (DONE 2026-06-20 → `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`)
- [ ] Cross-case synthesis update (extends V13)
- [ ] Updated final report (extends `REPORT_R5_final.md`)

### C3. Conditional / open scientific questions
- [x] **Why does LA run +40% hot?** — V19 (2026-06-20) ANSWERED the gating question: LA stays hot
  (+38.8%, unmoved −0.6% by the zoning fix) → it is NOT the zoning defect; confirmed a real
  climate/HVAC-response problem. **Deep-research now warranted** (was "do NOT research blind"): California
  Title 24 vs our ASHRAE 90.1 archetypes (envelope U-values, infiltration, HVAC COP/economizers for
  cooling-dominated CZ 3B). Gated on user go/no-go for the calibration phase.
- [ ] Restaurant + multifamily reconstruction overshoot — revisit after Phase C re-score
- [ ] IDF-gen performance: add cheap core/perim pre-filter only if §B watch-item proves prohibitive
- [!] **Geometry robustness — MULTI-class (Phase C fan-out is a de-facto stress test surfacing several gaps).** Per-cell rc=2 failures so far, distinct signatures:
  - **(a) sliver perim zone** — austin_urban way/381810546: non-convex footprint → perim offset makes a collinear sliver zone (area 0.06 m², 18.76 mm off collinear, *above* the 10 mm vertex-collapse tol) that inverts winding → negative zone volumes → `CalcHeatBalanceInsideSurf` divergence. Existing `<3-distinct-vertex` detector misses it.
  - **(b) interzone vertex-count mismatch** — la_centre way_427817502: `GetSurfaceData` fatal, paired ceiling/floor have 12 vs 11 verts (geomeppy intersection artifact).
  - **(c) thermal divergence surviving repair** — la_centre way_427817541: temp out-of-bounds even after the zero-area-strip repair.
  - **AND the auto-repair path is insufficient** — the harness's zero-area-strip + re-submit fails for (a)/(b)/(c); the repair fallback should reroute the building → one_zone_per_floor, not just strip surfaces.
  - **Likely fix (manager plan, Sonnet executes):** a general pre-sim geometry validation that reroutes → one_zone_per_floor on ANY degenerate perim decomposition (min perim-zone area, signed-area/winding check, interzone vertex-count parity) + harden the repair fallback to do the same. This is a broader design decision than the original 3-guard detector → **flagged for user decision.** Re-run every rc=2 cell after the fix (full list TBD at fan-out end) — AFTER the harness-hardening below.
- [ ] **Harness hardening (Sonnet task) — ship/staging coherence.** Fix the `if not dst.exists()` ship guard (v12_cell_pipeline.py:249) so re-runs always re-copy regenerated IDFs, and make `run_cell` clear `fleet_staging/`+`sim_out/` at start (it already clears the step3 manifest). Without this, any cell RE-run silently re-ships stale IDFs (root cause of the la_urban 5-building desync). Fresh fan-out cells are unaffected; do BEFORE any cell needs a second pass. Manager writes the plan task; Sonnet executes; do NOT edit while bg task `b9hus1m9d` is using the file.

---

## D. How decisions flow (reminder)
- Manager (Opus session) writes/updates plans + audits; **never writes feature code**.
- Fresh Sonnet sessions execute plans; never plan.
- Cluster/long compute = user's explicit go/no-go.
- Gates are report-only — never tuned to pass.
