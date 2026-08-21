# OpenUBEM — Master Progress Checklist

> Single-glance tracker. Past = one line each. **Current** and **Future** carry the detail.
> Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked / needs decision

---

## 🗺️ Path migration map — added 2026-08-06 (read this before following any `docs_ACTIVE/…` link below)

**Every arc that was archived into `docs/docs_DONE/` left its citations behind.** The journal blocks in
this file are append-only and have deliberately **not** been rewritten, so many of them still name the
old `docs/docs_ACTIVE/<arc>/…` location. Those directories no longer exist. Nothing is lost — the
documents were moved and, in a few cases, renamed. Use this table to resolve any stale path.

| Old prefix (dead) | Current location |
|---|---|
| `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` | `docs/docs_DONE/SETUP/layoutAssigner/` |
| `docs/docs_ACTIVE/simulation-Resolution/` *(the mode-switch arc)* | `docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/` |
| `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/` | `docs/docs_TODO/layoutgenerator/` |
| `docs/docs_ACTIVE/hvac-ServiceLoads/` | `docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/` |
| `docs/docs_ACTIVE/input/deepResearch/` | `docs/docs_DONE/BUGS/input-framework/deepResearch/` |
| `docs/docs_ACTIVE/input/imputation/` | `docs/docs_DONE/INPUTS/imputation/` |
| `docs/docs_ACTIVE/misclassification/` | `docs/docs_DONE/BUGS/misclassification/` |
| `docs/docs_ACTIVE/phaseC_combinedResim/` | `docs/docs_DONE/SETUP/phaseC_combinedResim/` |
| `docs/docs_ACTIVE/3D/` | `docs/docs_DONE/VISUALS/3D-visualization/` |
| `docs/docs_ACTIVE/UTCI/` | `docs/docs_DONE/OUTDOOR/UTCI/` |

🔒 **Added 2026-08-20 — one rotation, and it is NOT a move.**
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` was **closed** at 8,246 lines and
**stays exactly where it is**; the live register is now
`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` (**16** live items as of
2026-08-20 evening; it opened at 21). **No link in
this file is dead because of it** — the closed book is still the authority on closed items and on
each live item's full history. Follow an old link and you land on a 🔒 banner that points forward.

**Four files were also renamed by the move** — prefix substitution alone will not find them:

| Old filename | Current filename |
|---|---|
| `layoutAssigner/COMPLETION_REPORT.md` | `layoutAssigner/DONE/COMPLETION_REPORT.md` |
| `layoutAssigner/debug/PLAN_debug_implementation.md` | `layoutAssigner/debug/DONE/PLAN_debug_implementation.md` |
| `…/storey-Matching/PLAN_storey-matching_implementation.md` | `…/storey-Matching/DONE_PLAN_storey-matching_implementation.md` |
| `layoutAssigner/e-la-20/PLAN_e-la-20_multilayer-fix.md` | `layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md` |

**Scope, measured 2026-08-06:** 58 distinct dead paths cited from 23 live documents. All 58 resolve
through this table. The published deliverables under `docs/docs_EXPLANATION/` and
`docs/docs_REPORTS/` **have been repaired in place** and carry no dead links. This file's journal, the
frozen `docs_DONE/` arc records, the read-only `docs_main/` specs, and the parked
`docs_TODO/layoutgenerator/` set were deliberately left unedited — they are resolved by this table
instead. Tracked as **OPEN-33** in the open-items register.

**🔴 Archiving rule — ruled obligatory 2026-08-09, written here 2026-08-12 (OPEN-33).** Archiving an
arc into `docs_DONE/` is **not finished** until every citation pointing into it, from every live
document, has been swept and repaired. Resolve stale citations **by filename, not by path
rewriting** — four of the 58 originals were renamed by their own move (gained a `DONE_`/`DONE-`
prefix or were re-nested under a new `DONE/` folder), so a straight prefix substitution misses
them; matching on the (possibly `DONE_`/`DONE-`-stripped) filename finds them instead. **Standing
exclusions**, unchanged: `docs_DONE/` arc records, `docs_main/` specs, and
`docs_TODO/layoutgenerator/` are never edited to chase a citation — they are resolved through the
migration table above instead. **Measured cost: ~30 minutes per archive.**

**🔴 Classification before/after gate — ruled obligatory 2026-08-09 (CP-M3), written here
2026-08-12 (OPEN-31).** No change to `openubem/semantic/building_classifier.py` that can move
classification is adopted until the labelled fixture has been run on **both** sides of the change
and **both** accuracy numbers are recorded. A single "after" number does not satisfy the gate. What
it would have caught: E-R3-3 cost **4 points** of fine top-1 and reclassified **13.4%** of the shared
fleet, and **neither number existed at adoption time** — attributing the drift later took a
five-commit bisection, six weeks late. **What this ruling does not do:** it does not re-open any
already-adopted change retroactively (re-running M01–M05 is forbidden), and it does not certify the
fixture itself — OPEN-22 is rebuilding the labelled exam, and if the fixture changes, this gate
follows it. Also written at the head of `openubem/semantic/building_classifier.py`.

🔴 **AMENDED 2026-08-13 by ruling `2a` — the gate now spans TWO exams, and a before/after must report
both.** The exam did change, and the answer was not to swap it: **the old 50-row fixture keeps its
`≥0.70` fine top-1 gate and is never edited** (a retired item's bisect, OPEN-04, depends on it
byte-for-byte), and **`tests/fixtures/labelled_archetypes_tagrich_v2.csv` is gated separately at
`≥0.80`** — its measured accuracy is **88.8%** on 98 graded rows, with size-guessing down from **34.0%
to 3.1%**, which is the entire reason it was built. ⚠️ **Consequence for every document, not just this
gate: every accuracy figure must name its fixture.** A bare percentage is no longer meaningful here,
and **`92.0%` may be quoted as history but never as a comparison point** — its answer key was rewritten
in the commit after it was recorded. **OPEN-31's ID is retired (2026-08-13, ruling `2h`); this rule is
not.**

---

> **Last updated:** 2026-07-26 (**🔒 ARC L — E-LA-20 FIX ARC CLOSED, CP-C SIGNED.** The multilayer-fix
> plan is complete: the `Thickness = R × k` inversion is fixed at **both** defect sites via the new
> `openubem/idf/opaque_assembly.py`, and verified on **150/150** engaged fleet rows through the real
> production path — 0 CTF Fatal. Both constants (`T_ENGAGE = 0.868 m`, `T_MASS_MAX = 0.35 m`) were
> measured at the value and the `u` they ship to. Two corrections were forced at audit: E-LA-23 is the
> **fifth locus of an already-four-entry lineage**, not a new phenomenon — and this arc supplies its
> first matched control; and the EUI effect is **uniformly negative** (150/150), not bidirectional.
> **Not done, stated as a condition:** the fleet was never re-run and there is no T19 comparison.
> Detail in the Arc L update block below. Prior entry, 2026-07-25:
> **UTCI ARC ARCHIVED** — folder moved `docs_ACTIVE/UTCI/` →
> `docs_DONE/OUTDOOR/UTCI/`; Stage 6 promoted from arc-in-progress to a documented platform feature in
> `OpenUBEM_fundamentals.md` §11; graphical-abstract prompt extended with outdoor comfort. Same day:
> **E-UTCI-09 height-backfill CP-C SIGNED** — E-UTCI-09 dispositioned
> *materially fixed with a documented residual*, NOT closed; the flat-open-field `svf_mean = 1.0000`
> artefact is gone from all 3 cells that carried it, `austin_centre` densified 84.5 % → 2.7 % excluded,
> and a material rural residual [`nyc_rural` 36.4 %, `austin_rural` 19.2 % still `NaN`] is forwarded to
> a future Stage-1 acquisition arc. Detail in §I. Prior header entry, still accurate, below.)
>
> **Previously:** 2026-07-03 (**E-R3-3 sub-arc CLOSED — CP-3 ACCEPTED + T11.7 PROMOTED**: the committed `phaseE` baseline is now the E-R3-3-corrected fleet; move-away diagnosed [662 Medium→Small office flips cross a VAV→PSZ HVAC cliff, 89–100% classifier]; REPORT §14 addendum + new explanation doc authored. Prior: arc **G. input-parameter imputation** Phase B COMPLETE + CP-2 FULLY MET [real-city cluster A/B]; Phase C plan authored, not dispatched.)
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
>
> **🆕 Arc L — `layoutAssigner` (prototype-substitution resolution mode) — 🔒 T01–T10 DONE + CP-A/B/C SIGNED 2026-07-22 (autonomous director run); T11 DEFERRED by design; T12 PARTIAL (local leg only).** New `resolution_mode="layout_assign"` fully implemented end-to-end: registry/scaling engine (T01-T05), output-purge + location patch + full `builder.py` integration (T06-T07), E+ 22.1→23.1 library transition to a new 25-file `00.BaselineBuildings_NUs_v231` sibling (T08, original untouched), test portability + **LIVE_SMOKE-LA real EnergyPlus 23.1 run PASSED** (T09: MidriseApartment S=4.78, 0 severe, 411,303 kWh annual electricity), `compare_layout_assign.py` footgun fixes — fabricated ×1.01 EUI removed, real zone counts, MD-overwrite gated behind `--write-md` (T10). **T12 local leg:** 6 representative archetypes (apartment/office/hotel/school/retail/restaurant) built + simulated with REAL EnergyPlus, real EUI harvested (60–886 kWh/m²/yr, all plausible) — full 12-cell cluster leg deliberately out of scope for this run. **Two genuine OPEN-BLOCKED findings surfaced and carried forward** (director-verified from raw evidence, not just employee reports): E-LA-05 (`results/parser.py`'s zone-integrity gate is structurally incompatible with `layout_assign`'s DOE-native zone names — affects any future harvesting) and E-LA-06 (`scale_baseline_idf()` doesn't scale fixed-capacity auxiliary equipment — transformers/DHW tanks/HVAC coil ratings — causing real warning/severe floods, e.g. 73,803 Severe "Transformer Overloaded" on MediumOffice at S=1.60; only near-native-scale MidriseApartment stayed clean). En-route also corrected a real measurement error inherited from the v2.1 plan itself (E-LA-01: true zone counts are MidRise 27/Hospital 55, not the previously-cited 92/58 — a naive-grep contamination, independently re-verified by the director). Full report: `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/COMPLETION_REPORT.md` (now superseded by later phases below, kept for history).

> **UPDATE 2026-07-23 — 🔒 ARC L CLOSED, CP-E SIGNED** (Phases 4–6, T13–T17). T14 fixed E-LA-05 (parser zone-integrity gate now `layout_assign`-aware). T15 partially fixed E-LA-06 (transformer/DHW-tank/DX-coil capacity now scaled; 4/6 T12 archetypes reach Severe=0, 2 residual autosize-interaction Severes left OPEN-BLOCKED-PARTIAL). T16 built `envelope_patcher.py` (cross-CZ construction patching; honest negative finding — moves EUI only −0.43%, not the dominant gap driver). **T17 ran the full 12-cell/8,160-building cluster sweep** (12 `sbatch --array` jobs) and harvested it: **7,887/8,160 succeed (96.65%)**. 273 failures cleanly attributed to 3 classes: E-LA-07 (`LargeOffice`'s unscaled `FluidCooler:TwoSpeed` capacity, 221 buildings; plus `TallBuilding`/`SuperTallBuilding` warmup-instability Fatal in a small marginal zone), E-LA-08 (same warmup-instability class, confirmed to also hit `SmallOffice`/`MediumOffice`/`Hospital`, 46 total across 5 archetypes), E-LA-09 (`Outpatient` 100% Fatal fleet-wide, missing Controller List reference, 6 buildings). **Most consequential finding: E-LA-10** — `WaterHeater:Mixed.Peak_Use_Flow_Rate` is never scaled by S, a *silent* (non-Fatal) defect that produces a plausible-looking but wrong `dhw_eui` (~1/S) for `MidriseApartment`+`SmallOffice`, 80.1% of the successfully-simulated fleet (77.4% of the entire fleet) — explains anomalous `nyc_suburban`/`la_suburban` medians. Manager's CP-E audit independently re-verified the harvest CSV/sacct/spot-checked EUI values from scratch (all exact matches) and corrected 2 prose-only precision errors (a "5 of 12 cells at 100%" miscount, and the E-LA-10 percentage's denominator) directly in both docs. **`layout_assign` is adopted for its intended use (high-fidelity zone/HVAC-topology studies) but explicitly NOT production-grade for fleet-level EUI reporting** until a future arc fixes E-LA-10 (priority 1), then E-LA-07/08 and E-LA-09. Full record: `implementation_plan.md` §8/§9, results in `OpenUBEM_results_LayoutAssigner.md` (now under `figures/`).

> **UPDATE 2026-07-23 — 🔒 ARC L DEBUG-FIXES PLAN CLOSED, CP-E (v2) SIGNED** (autonomous director run, `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/PLAN_debug_implementation.md`). Picked up 2 of the 4 residual defects the arc above closed with, in priority order. **T01–T03 fixed E-LA-10** (`WaterHeater:Mixed.Peak_Use_Flow_Rate` + 4 sibling parasitic/loss-coefficient fields added to the scaling engine) — confirmed at 5-building local retest: distorted `dhw_eui` (up to 1643 kWh/m²) collapses to the scale-invariant ≈39.4 (MidriseApartment)/13.6 (SmallOffice) value the undistorted part of the fleet already showed. **T04–T05 fixed E-LA-07-class-1** (`FluidCooler:TwoSpeed` capacity fields on `LargeOffice`) — but surfaced a **new** Fatal, **E-LA-11** (WSHP coil autosize → `INF`/`NaN` on shrunk DataCenter zones → plant-loop runaway), on 2 of 3 retested buildings. **T06–T07 root-caused (but did not fix) both E-LA-07-class-2/E-LA-08** (root: `envelope_patcher`'s `MATERIAL:NOMASS` zero-thermal-mass construction swap) **and E-LA-11** (structural HVAC-autosize issue) — both correctly STOP-AND-REPORTed as out of this plan's additive-scaling-tuple scope; also surfaced **E-LA-12** (`Daylighting:ReferencePoint` not scaled, currently latent/masked). **T08–T09 fully root-caused E-LA-09**: not a baseline defect, not a `purge_baseline_outputs()` casualty — a third-party **eppy `IDF.save()` serialization bug** (`EpBunch.__repr__` zip-truncation corrupts `Outpatient`'s 2 oversized `Controller:MechanicalVentilation` objects, exactly 1/25 baselines affected) → logged as **E-LA-13**; STOP-AND-REPORTed, no safe fix available without regression-testing all 25 baselines. **T10 local regression found 1 new non-blocking regression, E-LA-14** (`SecondarySchool`-family `CheckWarmupConvergence` Severes, a side effect of T01/T02's fix — Severe-count only, `status` stays `success`) — accepted, not fixed. **T11 ran the full 12-cell/8,160-building cluster re-sweep** (fresh `t18_*` job set/harvest, `t17_*` originals untouched): **fleet success rose from 96.65% (T17) to 98.81% (T18)**, 273→97 failures, **zero new failures anywhere, 176 buildings recovered** (all `LargeOffice`). `LargeOffice` alone: 18.15%→83.33%. `n_warmup_convergence` (E-LA-14) confirmed fleet-wide at 1.29% (105/8,160), non-blocking. Director's CP-E audit independently re-derived every headline number from the raw T17/T18 CSVs (sacct cross-check, archetype breakdowns, failure-set diff) — all exact matches, zero discrepancies. **Net: `layout_assign` recommended for PARTIAL production use** — usable for fleet EUI aggregation with two explicit caveats: `Outpatient` (0/6, 100% data-absent) and `LargeOffice` (83%, not 100%, 45/270 still missing). `TallBuilding`/`SuperTallBuilding`/`SmallOffice`/`MediumOffice`/`Hospital` failure rates are unchanged from the arc above (E-LA-07-class-2/E-LA-08, still OPEN-BLOCKED). Three defects (E-LA-11, E-LA-07-class-2/E-LA-08, E-LA-09/E-LA-13) are now **fully root-caused with proposed fix shapes**, ready for a future arc to implement as one unit of structural work. Full record: `debug/COMPLETION_REPORT_debug.md`, results in `OpenUBEM_results_LayoutAssigner.md`'s new `## 5.` section, raw CSVs also archived under `docs_ACTIVE/simulation-Resolution/layoutAssigner/results/`.

> **UPDATE 2026-07-24 — 🔒 ARC L STRUCTURAL-FIXES PLAN CLOSED, CP-E SIGNED WITH CAVEAT** (autonomous director run, `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/PLAN_structural-fixes_implementation.md`). Implemented all 3 defects the debug-fixes plan left OPEN-BLOCKED, plus latent E-LA-12. **T01–T09 fixed E-LA-12** (`Daylighting:ReferencePoint` scaled by √S), **E-LA-11** (WSHP autosize-resolve-then-scale), and **E-LA-09/E-LA-13** (`objls` comment-padding around eppy's serialization bug) — **T10's full local regression found these 3 fully clean, zero new regressions.** **T11 ran the full 12-cell/8,160-building cluster re-sweep** (fresh `t19_*` job set/harvest, `t17_*`/`t18_*` originals untouched) and harvested it: `Outpatient` 0%→100%, `SuperTallBuilding` 50%→100%, `Hospital` 80%→100%, `LargeOffice` 83.3%→100% — all 3 targeted fixes verify clean at fleet scale. **But fleet-wide success rate went DOWN, 98.81% (T18) → 97.92% (T19)**, because the debug-fixes plan's own `thermal_mass=True` default (E-LA-07-class-2/E-LA-08's fix) unmasked a brand-new defect, **candidate E-LA-20**: 150/154 (97.4%) of `nyc_rural` `SmallOffice` buildings newly Fatal on a `LA_ROOF_CONSTRUCTION` CTF-convergence failure, invisible in every prior local retest sample, costing more buildings (150) than all 4 fixes recovered combined (64). `n_warmup_convergence` (E-LA-14/E-LA-19) roughly doubled to 2.49% fleet-wide, still cosmetic/non-blocking. Manager's CP-E audit independently re-derived the fleet success rates and the 150-building new-failure count directly from the raw `t17_`/`t18_`/`t19_` harvest CSVs — exact match, zero discrepancies. **CP-E signed WITH CAVEAT, not an unqualified pass: `layout_assign` is not yet unconditionally production-grade fleet-wide — E-LA-20 must be root-caused/fixed, or `thermal_mass=True` scoped away from the small-scale-factor regime that triggers it, before that claim can be made.** E-LA-20 logged OPEN (no candidate fix yet), carried forward as the seed of a likely future follow-up arc. Full record: plan's own §7 progress log (T01–T11, CP-A–E, E-LA-20's entry), results in `OpenUBEM_results_LayoutAssigner.md`'s new `## 6.` section. **[Caveat status as of 2026-07-25: E-LA-20 is fixed and verified 150/150 on the real production path (see the CP-C block below) — but this caveat is only PARTIALLY discharged, because the fleet was never re-run at `thermal_mass=True`, so the unconditional fleet-wide production-grade claim still cannot be made.]**

> **UPDATE 2026-07-25 — 🔬 ARC L E-LA-20 INVESTIGATION COMPLETE (investigated, NOT fixed)** (autonomous director run, `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/PLAN_e-la-20_investigation.md` + `COMPLETION_REPORT_e-la-20-investigation.md`). Investigation-only by design — **no production code was touched; `git status` verified clean after every task.** All 5 tasks (I01–I05) executed locally on real EnergyPlus 23.1 (~80 real runs, zero cluster compute), CP-INV synthesized. **Root cause confirmed, not hypothesized:** `patch_envelope()` holds conductivity fixed at `_K=0.12` and lets thickness absorb the whole target R (`Thickness = R × 0.12`). Harmless as `MATERIAL:NOMASS` (a pure resistance, no CTF series needed); once the structural-fixes plan's `thermal_mass=True` default turned it into a real `MATERIAL` (ρ=800, cp=1000), a well-insulated roof becomes a single homogeneous slab **over a metre thick** (~800 kg/m²) whose thermal time constant the CTF solver cannot expand at the model's 900 s timestep → Fatal in `InitConductionTransferFunctions`, ~0.1 s, before Warmup/Sizing. **The "small scale factor S" framing in E-LA-20's original log entry is falsified:** I01 reproduced the Fatal on 11/11 buildings across a **65× range of S** at an identical `u_roof`; S appears nowhere in the failing function. **I02 (the gating test) came back exactly as designed** — no-patch PASS, `thermal_mass=False` PASS, `thermal_mass=True` FATAL, on 4 buildings spanning the full S range; the plan's single stop condition did not fire. **I03 located a sharp, fully monotonic threshold** (25 real runs): fails iff `u_roof < ~0.138 W/m²K` ⇔ `Thickness > ~0.870 m` ⇔ Fourier number `Fo < ~1.785e-4`. **I04: the discriminant is vintage, not climate zone and not S** — `SmallOffice`'s base roof U is banded and 4A and 6A share the *same* 0.119; `nyc_rural` resolves to `90.1-2013` (×1.0 → 1.008 m → Fatal) while the other 3 NYC cells resolve to `DOERefPre1980` (×1.6 → 0.630 m → pass); that vintage traces to **one** real `year_built` among 150 buildings, propagated by group-mode imputation. **I05: 30/30 diagnostic probe runs PASS** across 4 distinct fix shapes, all agreeing on EUI to <1% — the fix choice is about fidelity/complexity/runtime, not about the answer. **Director's own fleet-exposure derivation (beyond any single task's scope): 204 of 3,248 `(archetype, zone, vintage)` combinations (6.3%) sit below the threshold** — 6 archetypes, 10 climate zones (4A–8), 5 vintages — so this is a **latent structural exposure**, not a `nyc_rural` curiosity; the 12-cell fleet exposed it in one cell only because it holds almost no modern-vintage buildings in cold zones. **Scope correction:** E-LA-20 affects **150/150 = 100%** of genuine `nyc_rural` `SmallOffice`, not 150/154 = 97.4% — the "4 survivors" are exactly the 4 `building_tag="hotel"`, fully-data-poor buildings, which classify as `SmallHotel` at current HEAD (logged as new **E-LA-22**: T19 archetype/vintage is not reproducible locally for data-poor buildings — material for any future cross-generation comparison). Also logged new **E-LA-21**: the harvest scripts' `has_fatal` column matches `"** Fatal **"` (one space) vs EnergyPlus's real `"**  Fatal  **"` (two), so it reads `False` on **all 8,160 rows** — reporting-only, no simulation impact, no existing conclusion depends on it. **Plan deliberately does NOT close — it ends OPEN at CP-INV.** Recommended follow-up (to be scoped by a manager, not drafted here): adopt I05's `(a)` multi-layer split as primary candidate with `(c2)` hybrid as fallback, guard on the **threshold** rather than on a cell name, verify at fleet scale (this defect was invisible to every ≤28-building local sample across two prior plans), and reject `ConductionFiniteDifference` as primary (~20× runtime).

> **UPDATE 2026-07-25 — 📝 ARC L FIX PLAN WRITTEN (not started, no code touched)** — `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/PLAN_e-la-20_multilayer-fix.md`. Adopts I05's `(a)` multi-layer split, promoted from candidate to pinned decision, with **adaptive N** (`N = ceil(total_thickness / L_max)`, `L_max = sqrt(α·Δt / (2·Fo_crit))`) rather than a fixed N, preserving total R **and** total mass exactly for any N. 12 tasks (F01–F12) across 3 phases with checkpoints CP-A/CP-B/CP-C; no production edit permitted before CP-A is signed. **Three scoping findings new to this plan, derived while writing it:** (1) **a second, identical defect site exists** at `builder.py::assign_constructions()` lines 218–253 — same `Thickness = R × _K` inversion, latent only because `thermal_mass` defaults `False` outside `layout_assign`; (2) **the baseline IDF library is not single-timestep** — `TIMESTEP` is 6/h ×20, 4/h ×3, 2/h ×2 across the 25 baselines, while the investigation measured the failure threshold at 4/h only, so `L_crit` is 0.710 m at 6/h and 1.230 m at 2/h, not a universal 0.870 m; (3) applying the Fourier criterion **per archetype at its own timestep** raises exposure from 204/3,248 (6.3%) to **394/3,136 (12.6%)**, spanning 25 archetypes, all 16 climate zones and all 7 vintages — ⚠️ this is a **model extrapolation from a single calibration point, not a measurement**, which is precisely why F01 (re-derive the threshold at 2/h and 6/h) and F02 (falsify it against the existing 8,160-row T19 harvest, read-only) run before any code is written. Exposure is **roof-only**: `u_wall`/`u_floor` bottom out at 0.182 → 0.659 m library-wide. Global worst case is `u_roof = 0.097` → **1.2371 m** (`SmallOffice`/`QuickServiceRestaurant`, zones 7–8, modern vintages), 23% thicker than anything I05 probed — F03 exists to cover it. E-LA-21 and E-LA-22 stay **OPEN and explicitly out of scope**. Execution is delegated to a separate executor session; this plan is documentation only.

> **UPDATE 2026-07-25 — 🔄 ARC L E-LA-20 FIX PLAN IN EXECUTION; CP-A SIGNED, BUT THE FIX SHAPE WAS FALSIFIED AND REPLACED.** Phase A ran on real local EnergyPlus 23.1 (~64 runs, zero cluster compute, **zero production-code edits — `git status --short openubem/ tests/ main.py` clean throughout**). The plan's own calibration tasks demolished its own design, exactly as they were built to: **F01** measured the single-layer CTF boundary at 2/4/6 timesteps-per-hour and **falsified the Fourier `sqrt(dt)` scaling** — the boundary is flat (0.868–0.946 m) and non-monotonic across a 3× Δt range, so `Fo_crit`/`SAFETY` were retired and the plan's headline **12.6% exposure extrapolation was withdrawn**. **F03-R then killed the adaptive-N multi-layer split outright**: at the fleet worst case (`u_roof = 0.097`, 1.2371 m) EnergyPlus Fatals with a genuine `CTF calculation convergence problem` at **every N from 1 to 10, at every timestep** — 30 runs. The controlling variable is **total** assembly thickness (equivalently `R·C`), not layer thickness, proven non-circularly by the executor's own data: a 0.3810 m layer FATALs at `total_t = 1.1429` while a *thicker* 0.5042 m layer PASSES at `total_t = 1.0084`. Splitting preserves total R **and** total mass exactly — the very property the plan advertised as the shape's chief virtue — hence preserves `R·C` exactly, hence cannot move what the solver responds to. **Corollary, binding: any mass-preserving fix is dead on arrival.** **F02-R** (the one unambiguously good news) measured true fleet exposure from all 8,160 harvested `eplusout.err` files: **150/8,160 = 1.84%**, all `nyc_rural`, predicted by `total_t > 0.868 m` with **zero false positives and zero false negatives**; manager re-derived the 8,160/150 counts independently by `grep` over the harvest. **Disposition: CP-A signed on the measurements; adaptive-N retired; reserve candidate (c2) — a capped mass layer plus a `MATERIAL:NOMASS` residual carrying the leftover R — promoted to adopted** (pre-registered in §3, so plan-as-written, not drift). It preserves U exactly, never exceeds 2 layers, and is byte-identical to today below the cap. **Phase B is CLOSED**: F04–F07 are written against the dead shape and will be rewritten by the manager. New **Phase A-ter / F03-T** now measures (c2)'s one free constant `T_MASS_MAX` — including a single-run discriminator between a constant-thickness cap and an `R·C`-scaled cap, and a **mandatory EUI-cost measurement**, because (c2) is the first shape in this arc that changes physics rather than only numerics (investigation fact F-11's "<1% across candidates" does **not** transfer to it). Two Phase-A tasks were **rejected at audit first** and redone — one for a circular ground-truth predicate, one whose harness died in `GetSurfaceData` and never reached the CTF solver on any of 11 runs; both rejections traced to reporting a wrapper's verdict or the `.end` file instead of the `** Severe **` line. Full record: the plan's §4-ter (shape + derivation), §5 facts F-13/F-14, §8 (two manager AUDIT entries).

> **UPDATE 2026-07-25 — 🔒 ARC L E-LA-20 FIX PLAN COMPLETE, CP-C SIGNED, ARC CLOSED.** The state changes from "investigated, NOT fixed" to **fixed and verified at the entire population that can reach it.** The signature rests on **0 Fatal CTF across 150/150 engaged rows on the real production path**, re-grepped by the manager from the raw `.err` files rather than read out of a harness PASS column; those 150 are the fix's whole blast radius (F02-R measured 150/8,160 with 0 FP / 0 FN, and CP-B proved the other 8,010 byte-identical below the threshold); and both frozen constants were run at the exact value and exact `u` they ship to, never inferred from a bracket — which F-17 forbids. Phase A-ter measured (c2)'s one free constant across three dispatches and two more falsifications before freezing it: an `R·C`-scaled cap (T-b) died on its own 16 points; a fractional cap (T-c) fit those same 16 but was then falsified by 24 more (F-17 — **CTF convergence is not monotone in the cap thickness**, a genuine isolated FATAL sandwiched between two PASSing neighbours, manager-verified on the raw IDFs), which recovered a **constant thickness cap** as the only rule consistent with all 40 pooled points. `T_MASS_MAX = 0.35 m` was then run at the exact value and the exact `u` it ships to (F03-T3), not inferred from a bracket — 1/1 PASS at the real exposed `u`, 10/10 PASS on a ±0.03 m stability window, PASS at 2/6 ts/h — **CP-A-bis SIGNED**, both constants FROZEN: `T_ENGAGE = 0.868 m` (F-13) and `T_MASS_MAX = 0.35 m` (F-20). **Phase B implemented** the shape as a new shared module `openubem/idf/opaque_assembly.py`, wired into both defect sites (`envelope_patcher.py`, `builder.py::assign_constructions()`, closing the latent second site F-08) — **CP-B SIGNED**: 88/88 tests green, and both byte-identity guarantees (unconditional `thermal_mass=False`; `thermal_mass=True` below the 0.868 m threshold, the 8,010-of-8,160 path) reproduced independently against `HEAD` by the manager's own scratchpad reconstruction, not accepted on the executor's word. **Phase C verified:** F08 (11/11 real-EnergyPlus regression on the investigation's own Fatal set), F09 (144/144 synthetic sweep across every distinct `u_roof`×timestep pair the library can produce, shipped-module parameters cross-checked at all 48 `u` values, 0 mismatches), F10 (the adopted simulation baseline proven untouched **by construction** — it resolves `thermal_mass=False` on every built row, no simulation needed). **F11 (full 8,160-row fleet re-run) was a manager NO-GO** — its own pass criterion required a T19 comparison that E-LA-22 makes irreproducible — and was replaced by **F11-N**: all **150** fleet rows above the engagement threshold (the entire at-risk population, not a sample), real production path, `thermal_mass=True` — **150/150 PASS, 0 CTF Fatal.** A matched `thermal_mass=False` control, **F11-N-b**, then corrected two things on the record: (1) **the fix measurably drives warmup non-convergence** — 96/150 (64%) engaged rows vs 8/150 (5.3%) in the control, same geometry/schedules/code, one variable changed — logged as **E-LA-23**, non-blocking (0 CTF, 0 Fatal either arm) and currently zero blast radius since the adopted baseline is `thermal_mass=False` everywhere — **but see the CP-C correction below: this is not a new phenomenon**; (2) **the EUI effect is uniformly negative, not bidirectional as first reported** — min −2.124%/median −1.732%/max −0.995% across all 150, 150 negative and 0 positive — the earlier "bidirectional +0.26% to +4.30%" figure was an artifact of comparing against a stale prior-artifact reference rather than a matched control, now logged as **E-LA-24** (reporting-layer only). **E-LA-21 and E-LA-22 remain OPEN and explicitly out of scope**, unchanged by this plan. Full record: `e-la-20/PLAN_e-la-20_multilayer-fix.md` §4-quinquies (shipped rule) + §8 (full progress log and every AUDIT entry, CP-A through CP-C) + §9 (error log); synthesis in `e-la-20/COMPLETION_REPORT_e-la-20-multilayer-fix.md`.
>
> **CP-C audit corrections (manager, 2026-07-25 — two things the executor's own framing got wrong).**
> **(1) E-LA-23 is the fifth locus of an existing lineage, not a new defect.** `thermal_mass=True`
> perturbing `CheckWarmupConvergence` is already logged four times — **E-LA-14** (`SecondarySchool`),
> **E-LA-16** (`Hospital`/`TallBuilding`), **E-LA-18** (`LargeOffice`), **E-LA-19** (zone-composition
> shift) — with fleet prevalence **105/8,160 (1.29%) at T18 → 203/8,160 (2.49%) at T19** when
> `thermal_mass=True` became the `layout_assign` default. Every one of those entries hedged its
> causality (E-LA-19 reads literally *"Root cause: not fully proven"*). What is new is **not the effect
> but the evidence**: F11-N-b is the first **matched control** ever run on it — same buildings, same
> geometry, same code, one variable — which turns a four-times-repeated hypothesis into a measured
> attribution. That makes the finding **stronger, not weaker**, and E-LA-23 the densest locus of the
> lineage (64% vs a 2.49% fleet background). Two consequences **forwarded, not decided**: (a) the 150
> are **additive** to the fleet count — they were Fatal at T19 and counted 0, so a fixed fleet run at
> `thermal_mass=True` projects **≈299/8,160 ≈ 3.66%** (a projection, not a measurement); (b) the
> **"cosmetic" label**, inherited unexamined across all four prior entries, is a claim about *accuracy*
> that no one in this lineage has ever tested — including this arc.
> **(2) The EUI effect is uniformly negative** — min −2.124% / median −1.732% / max −0.995%, **150
> negative, 0 positive**. F08's earlier positive deltas came from a reference hardcoded off a prior
> artifact instead of a matched control (**E-LA-24**, reporting-layer only).
>
> **What this arc did NOT do, stated as a binding condition rather than a footnote:** the **fleet was
> never re-run**; there is **no T19 comparison** (F11 was a manager NO-GO because E-LA-22 makes its own
> pass criterion irreproducible); and the 8,010 untouched rows rest on an **argument** — byte-identity
> plus determinism — which collapses the moment that path stops being byte-identical.
> **Still OPEN and out of scope:** E-LA-21, E-LA-22, plus new E-LA-23 and E-LA-24.
> **Next step is written and waiting, not started:** `layoutAssigner/prompt/DIRECTOR_PROMPT_post-e-la-20_2026-07-25.md`
> — it freezes both constants out of the next director's reach, frames the fleet-run decision
> (~15 h, and structurally unable to produce a clean T19 comparison — to be said before, not after),
> and encodes the six traps this lineage actually fell into, the manager's own included.

---

## 0. WHERE WE ARE NOW — 2026-07-26

> The one-screen answer. Everything below this section is either history (§A–§I) or the arc's own
> detail (§L); the quote-blocks above are the dated journal. If those three disagree, **this section
> and the arc plan docs win** — the journal is append-only and never rewritten.

**Adopted simulation baseline — RESTATED 2026-08-19.**
`phaseE` + E-R3-3 correction + elevators. NYC −31.3% / LA −3.6% / Austin −30.5%, fleet
~~158.0~~ ~~157.1~~ **153.8 kWh/m²** (pooled: total simulated energy ÷ total simulated floor area; the
first struck figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43;
the second was superseded 2026-08-19 by the twelve-cell re-run `open48_refleet4`). It resolves
`thermal_mass=False` on every built row, so the E-LA-20 fix is provably
inert on it (F10, by construction — no re-simulation was needed to establish this).

> **What changed, in one paragraph.** The re-run put four landed fixes through all twelve cells on the
> same 8,160 buildings. **Exactly one of them moved the number.** Buildings the model cannot identify
> (`OpenUBEMUnknown` — 650 of them, 3.7% of the fleet's floor area) had been drawing their equipment
> and lighting loads from a pool that included **data centres and laboratories**, which pushed some of
> them to 450–580 kWh/m² — implausible for an unnamed building. OPEN-55's screen removed those donors.
> That population fell **223.4 → 107.2 kWh/m² (−52%)** and pulled the fleet down **−4.16**; everything
> else drifted **+0.93**, for a net **−3.23 kWh/m², −2.06%**. **This is a correction, not a new model:
> the same buildings, the same definition, better donors.** ⚠️ **The new figure is not volume-correct
> — OPEN-56 is still open, every building still simulates with a 10 m³ zone-volume stub worth about
> +1.0 kWh/m², and that is NOT in the 153.8.** A volume-correct fleet would be ≈154.8. Derivation:
> `docs/docs_ACTIVE/openings/extra/MEASUREMENT_fleet-restatement-2026-08-19.md`.
>
> **Two things are waiting on you.** (1) The floor-count fix (OPEN-35) corrected 20 buildings that were
> wrongly modelled as single-storey — but the 21st, a 19-storey hotel in `nyc_centre`, **now fails to
> simulate at all** where it used to run. That is a regression the fix introduced; it needs an ID and a
> decision. (2) The donor screen also reclassified **4 `Courthouse` buildings to `Unknown`** — together
> 477,804 m², one of them the largest building in its cell. That may be the screen being properly
> cautious or over-rejecting; it is a judgement call, not a measurement.
>
> **Sharper now (CP-1 of the twenty-item pass, audited 2026-08-19 late).** On (1): the risk is **not**
> one building and **not** all 21 — it is an **8-building group**, all of them `nyc_centre` hotels
> imputed to 19 storeys, of which **4 needed repair and 1 failed outright**. Every other building the
> fix touched came through clean, including *taller* 45-storey ones in `austin_centre`. Scope the
> decision to those 8. A third open item, **OPEN-56** (the room-volume stub worth ≈ +1 kWh/m² that
> sits outside the 153.8 headline), also now has a second possible remedy: the winding-correction
> code we relied on turns out to never run at all — it tests each shape against a reference point
> built from that same shape, so it always concludes "already correct". So either write the volume
> explicitly, or turn on the orientation step that is currently switched off for our default mode.
> **All three are yours to rule on; none was taken here.**
>
> **The twenty-item pass is finished (2026-08-19, late).** All 20 tasks ran and all three
> checkpoints — CP-1, CP-3, CP-2, in the order they came back — are audited and signed. **Nothing in
> the whole pass moved the 153.8 headline**, and no open item was opened, closed or retired: the
> register still stands at 19 tracked, next free ID `OPEN-60`. Every task was measurement-only, and
> no file under `openubem/`, `tests/` or `scripts/validation/` was touched — checked, not assumed.
>
> **Four things now wait on you, not three.** The fourth is new and came out of CP-3: **we currently
> cannot measure the energy of anything built in `layout_assign` mode.** Every build in this arc was
> made with the output-trimming switch on, and that switch strips exactly the per-zone output the
> results parser checks for before it will read a building. Three separate tasks hit this wall and
> **each said so instead of substituting a weaker number** — which is the right behaviour. ⚠️ **This
> is a hole in what we can measure, not an error in any number we have published**: nothing adopted
> depends on that mode, so the impact on published results is zero. It needs a rebuild with the
> switch off to close, and **whether it becomes a tracked item is your call.**
>
> **Two things worth knowing from CP-2.** The test suite reproduces its baseline exactly —
> **1,919 passed / 55 skipped**, run twice the same day on two independent processes. And the
> scratch copy of the E02 results was **swept a second time by something outside this project**
> (2026-08-19 16:19), after the first sweep on 2026-08-17. **The fleet data itself is fine** — the
> run the 153.8 figure comes from still holds all 8,160 of its files, checked directly. But this is
> now a pattern rather than an accident, which is what OPEN-53 exists to track.

**Arc L — `layoutAssigner` — 🔄 RE-OPENED 2026-07-26 as the Q3 storey-matching arc.** The park
lasted a day: Q3 (the √S form distortion, recorded at close as the largest open problem) is now
under active work in
`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_implementation.md`,
which is the live source of state. Status as of 2026-07-26 evening:

- **Phase A + A-bis — CP-A signed with conditions.** Prototype storey structure mapped, multiplier
  and band-deletion mechanisms measured.
- **Phase B — implemented, CP-B audited but NOT signed.** Storey matching (`compute_band_map()`,
  `match_storeys()`, plate-ratio `calculate_scaling_factor()`) is in and the full suite is clean:
  **1756 passed / 25 failed** vs. the pre-change **1735 / 25**, +21 = exactly the new tests, zero
  regressions, all 25 failures pre-existing and outside the touched modules.
- **🔴 The blocker is B06.** D3(a)'s Zone Multiplier produces **134,642 Severe** "Transformer
  Overloaded" errors in a real production run; a geometric `n_real/n_proto` factor covers only 81%
  of the measured electricity growth (2.456× vs 2.0× applied). **C02, the ~15 h / 8,160-building
  fleet re-run, is gated on closing this** — running it sooner spends the cluster on numbers already
  known to be wrong.
- **⚠️ Scope, for the eventual write-up:** `match_storeys()` can only express `n_proto ∈ {1, 3}`;
  every other band structure falls back. Storey matching covers a *minority* of the fleet, and the
  closure doc must state the fraction as a number rather than claim Q3 is fixed fleet-wide.
- **E-LA-28 (unscaled `Zone` X/Y Origins) — fixed and verified in B05.** At `planar_k = 0.5` the
  absolute X extent goes 46.3273 → 23.1637 m (0.500000× exact), versus 40.5364 m (0.875×) unfixed.
  Energy effect measured and **null** (20/20 runs, 0 Severe, deltas ≤ 4×10⁻⁷%).
- **Three evidence defects found and logged this day, all the same class** — a comparison that
  turned out to be about itself: **E-LA-30** (the A4-bis viewer generator's scaler is a measured
  no-op on 25/25 prototypes, so its scenes never depicted the pipeline and its 98%/97% overlap
  figures are void), **E-LA-31** (a "pre-B05" control that was byte-identical to the post-fix build,
  200/200 IDFs), and E-LA-24 before them. Standing rule now in the plan: **a before/after is not
  reportable until the "before" has been shown to differ from the "after" on the quantity the fix
  changes.**
- **First valid overlap measurement of the fixed pipeline:** `nyc_suburban` 27.00%, `la_suburban`
  55.40%, against real-`auto` controls of 0.00% and 1.79%. A residual cross-building placement
  problem is visible (median 8.5 m centroid offset) but is **not yet attributed** — the honest
  pre-fix comparison is still being produced.

**⏸️ UPDATE 2026-07-27 — PARKED AGAIN, mid-critical-path, nothing blocked.** The user moved to
another project. B06/E-LA-27 was closed, CP-D was **signed 2026-07-26** with three binding
conditions, and the plan moved to its successor
`debug/storey-Matching/PLAN_storey-matching_REMAINder.md` (tasks R01–R10; the ~3,500-line
implementation plan is now CLOSED). **The 12-cell / 8,160-building T20 fleet re-run completed and has
never been harvested:** `squeue` empty, 12/12 arrays, **8,153 COMPLETED + 7 FAILED = 8,160** exactly
(nyc_rural 3, la_urban 3, la_centre 1 — SLURM-level, *not* simulation-level, and each must be mapped
to a defect ID). No `t20_*` artifact exists on disk and no R06 progress-log entry exists.
**Remaining path: R06b (harvest + 7 reported items) → director audit → R09 (five cross-mode figures)
→ R08 (documentation closure) → CP-E, the final checkpoint.** Both executor prompts are written and
current. **Resume by pasting
`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/prompt/DIRECTOR_PROMPT_storey-matching-closure_2026-07-27.md`
into a fresh manager session** — it is self-contained.

> **✅ SUPERSEDED 2026-08-04 — that whole path was walked and the arc is CLOSED.** R06b, R06c, R09 and
> R08 all completed and were audited; **CP-E is SIGNED**. The resume instruction above is spent — do
> not paste that director prompt again. Current state is §L of this document.

Everything below this line describes the arc as it stood at the 2026-07-26 park and is kept for
history. A cross-mode comparison and the Q3 √S finding were recorded at close — see §L.

**The arc itself (`resolution_mode="layout_assign"`). All five sub-arcs CLOSED.**
The last one, the E-LA-20 multilayer fix, signed CP-C on 2026-07-25. `layout_assign` is a
*separate resolution mode*, not the baseline — it substitutes scaled DOE prototypes instead of
building geometry from OSM footprints.

**The one number that matters and the one condition attached to it:**
- ✅ **150/150** engaged fleet rows PASS on the real production path, 0 CTF Fatal. That is the
  fix's entire blast radius, not a sample (F02-R: 150/8,160 = 1.84%, 0 FP / 0 FN).
- ⚠️ **The fleet was never re-run.** The remaining 8,010 rows rest on an *argument* — byte-identity
  plus determinism — not on a run. So `layout_assign` is **still not unconditionally
  production-grade fleet-wide**, and the 2026-07-24 CP-E caveat is only partially discharged.

**Open defects carried forward** (none blocks the adopted baseline):

| ID | What | Status |
|---|---|---|
| E-LA-21 | Harvest `has_fatal` matches `"** Fatal **"` vs E+'s real `"**  Fatal  **"` → reads `False` on all 8,160 rows | OPEN — reporting-only |
| E-LA-22 | T19 archetype/vintage not reproducible locally for data-poor buildings → blocks any clean cross-generation comparison | OPEN — this is what made a T19 comparison impossible |
| E-LA-23 | The fix drives warmup non-convergence, 96/150 (64%) vs 8/150 control | OPEN — non-blocking; 5th locus of the E-LA-14/16/18/19 lineage; zero blast radius today |
| E-LA-24 | A prior artifact was used as if it were a matched control | Closed by correction, logged for the generic lesson |

**Next decision — written, waiting, NOT started.**
`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/prompt/DIRECTOR_PROMPT_post-e-la-20_2026-07-25.md`
frames it: **re-run the fleet (~15 h) or not.** Note before choosing, not after — that run
*structurally cannot* produce a clean T19 comparison, because E-LA-22 is in force.

**Everything else, one line each:** UTCI/Stage 6 → ✅ done + archived (§I), now a platform feature.
`layoutGenerator` zone-mode → ⏸ parked pending redesign (§H). Input imputation → ⏸ parked,
built-but-off (§G). Resolution-mode switch → ✅ closed (§F). Phase C/D/E → ✅ history (§B, §B2, §E).

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

## B. Phase C combined resim (pilot) — ✅ HISTORICAL (closed 2026-06-20; superseded by Phase D → §B2, then Phase E → §E)

> ⚠️ This section was the "current focus" heading until 2026-07-26. It no longer is — it describes
> June work that Phase D and Phase E have both superseded. Current focus lives in **§0**.

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

---

## I. UTCI outdoor microclimate — new Stage 6 — **🗄️ ARCHIVED 2026-07-25 · T01-T26 COMPLETE, CP-1 THROUGH CP-5 ALL SIGNED — ARC CLOSED (2026-07-24)**

> 🗄️ **Arc folder archived 2026-07-25:** `docs/docs_ACTIVE/UTCI/` → **`docs/docs_DONE/OUTDOOR/UTCI/`**.
> Every path in this section already points at the new location. `docs_ACTIVE/` now holds only
> `simulation-Resolution/`.
>
> **Stage 6 is now described as a standing platform feature, not as an arc**, in
> `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §11 (expanded to the complete feature set:
> §11.1 what it computes, §11.2 what has actually been run and what is honestly limited) with a
> pointer from §3 explaining why it is deliberately *not* a sixth pipeline stage. The
> outdoor-analysis registry's stale "⏸ gated, not started" status for heat-mitigation scenarios was
> corrected to ✅ built, carrying T24's honest finding that three of five scenarios reproduce the
> literature's sign but undershoot its magnitude. The project graphical-abstract prompt
> gained a section 7 for outdoor comfort, drawn as a deliberately separate panel — **never a sixth
> pipeline step, never a fourth headline stat-card** — since UTCI is unvalidated and EUI is not.
>
> **Graphical abstract now has two versions**, both in `docs_DONE/GENERAL/graphicalAbstract/`:
> `PROMPT_graphical_abstract_2026-07-05.md` (**v1, frozen** — rendered as
> `docs_EXPLANATION/OpenUBEM_fundamentals_2026-07-05.png`, six panels, energy only) and
> `PROMPT_graphical_abstract_2026-07-25.md` (**v2, current** — adds the outdoor-comfort panel;
> **not yet rendered**, output goes to `OpenUBEM_fundamentals_2026-07-25.png` beside v1, never over
> it). Edit v2. v1 stays valid for material about the energy pipeline alone.

New perspective, orthogonal to everything above: OpenUBEM currently answers *"how much energy does
this building stock use?"*; this arc adds *"what does it feel like to stand outside in it?"* —
spatial pedestrian thermal stress (UTCI) at 1.1 m from the four driver fields (air temperature,
humidity, wind speed, mean radiant temperature), exported as GeoTIFF rasters plus parcel-level
exposure metrics.

- **Plan doc:** `docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`
  **v1.1 (2026-07-23): 26 tasks, 5 phases, 5 checkpoints CP-1…CP-5 — the WHOLE arc is now in
  autonomous executor scope.** v1.0 had excluded Phase 5, the EnergyPlus facade coupling, and
  CP-4's signature. Re-examination showed two were manager conservatism and one rested on a
  false premise: Tier-2 wall coupling never needed a production re-run — it patches *copies* of
  the archived IDFs and runs a short-window side-leg locally, touching no production module.
  With production structurally untouched, CP-4 became manager-signable. Plan §13 has the full
  before/after. Scope widened; every hard gate unchanged.
- **Research corpus:** `docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/` (U01–U06) — **research input, NOT a
  binding spec.** Manager audit found **7 load-bearing defects** in it, each of which would silently
  produce wrong UTCI values; §4 of the plan overrides the research on every one. The two worst: the
  UTCI polynomial code printed in U05 §3 and U06 §3 is **fabricated** (7 hand-written terms vs the
  real 210-coefficient Bröde polynomial), and the 6-directional weighting factors in U03 §2.3 don't
  sum to 1.0 (0.08 printed, 0.06 correct).
- **Three architectural commitments (pre-decided, not open for re-debate):** native in-repo engine
  implementing SOLWEIG's *published algorithms* (SOLWEIG stays a validation reference, never a
  runtime dep — it is a QGIS plugin and cannot run headless under `sbatch`); analysis-window scoped
  (default = hottest contiguous 7 days, not 8760 h); zero fitted parameters, same rule as Stages 1–5.
- **The scientific contribution:** every peer 2.5D tool assumes facade temperature ≈ air temperature.
  OpenUBEM has real EnergyPlus exterior surface temperatures, worth +5…+15 °C mean radiant
  temperature near sunlit walls. That coupling is Tier-2 of task T13.
- **New deps:** `rasterio` promoted from implicit-transitive to explicit (it is already imported in
  3 modules today — a latent bug independent of this arc). Rejected: `numba`, `pvlib`, `xarray`;
  `pythermalcomfort` dev-extra only.
- **Outdoor measurement registry (new, standing doc):**
  `docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` — the single lookup for everything
  OpenUBEM measures outdoors (definitions, units, measurement heights, valid ranges, status). UTCI
  is its first entry; every future outdoor analysis gets registered there first. Linked from
  `OpenUBEM_fundamentals.md` §10. Plan task **T23** promotes its statuses once the arc really runs.
- **Executor kickoff prompt:** `docs/docs_DONE/OUTDOOR/UTCI/prompt/KICKOFF_utci_full_arc.md` — paste-ready,
  runs a fresh Sonnet T01→T23 through CP-1/2/3 autonomously and stops at CP-4. Includes a narrower
  T01–T07 first-run variant for an unproven executor.
- **Status 2026-07-24: arc COMPLETE, all 26 tasks and all 5 checkpoints done.** CP-1/CP-2/CP-3
  self-signed on schedule (four real physics adjudication rounds along the way, all resolved —
  plan §10 E-UTCI-01 through 06). T22's live smoke test on `nyc_centre` found a real wind-tier
  defect (E-UTCI-07/08, macdonald tier only); adjudicated and fixed, re-verified clean, 0 bound
  violations domain-wide — **CP-4 self-signed**. Phase 5 then ran: **T24** (mitigation scenarios,
  domain-layer-only) done; **T25** (3D viewer UTCI layer, default-off) done — required a real fix
  (byte-identical regression guard had genuinely failed at handoff; root-caused and fixed, now
  hashed-identical, not eyeballed); **T26** (12-cell cluster sweep, 8,160 buildings across
  NYC/LA/Austin × centre/urban/suburban/rural) done — all 12 array tasks completed, harvested into
  a cross-city comparison table + figure. **CP-5 self-signed 2026-07-24 — arc closed.** One honest
  finding carried forward, not blocking: 3-4/12 cells have an upstream Stage-1 `height_m` data gap
  (zero/near-zero building massing for those cells specifically) — logged as **E-UTCI-09** (plan
  §10), forwarded to a future Stage-1 data-acquisition arc, not a UTCI-arc defect. Full write-up:
  `docs/docs_DONE/OUTDOOR/UTCI/results/OpenUBEM_results_UTCI_microclimate.md`.
- **🔎 E-UTCI-09 INVESTIGATION COMPLETE 2026-07-25 — investigated, NOT fixed.** An investigation-only
  plan (`docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/PLAN_e-utci-09_investigation.md`, tasks I01-I04) ran to
  CP-INV. **It implements no fix and adopts no candidate; it stays OPEN**, handed back for scoping of
  a follow-up Stage-1 implementation plan. Full write-up:
  `docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/COMPLETION_REPORT_e-utci-09-investigation.md`.
  - **What it found.** The gap is genuinely narrow and upstream: across all 12 cells / 12,809
    buildings, geometry validity, row counts, footprint areas and `building_tag` are healthy
    everywhere; only `height_m`/`levels` are hit, cleanly bimodal (8 cells 0.67-26.09 %, a 58 pp gap,
    then 4 cells 84.50-100.00 %), no borderline case. Cause is differential live OSM tagging density
    at those coordinates, not a code defect (F-07: identical call path for all 12 cells).
  - **Decisive negative result.** The platform's existing but unwired height-imputation
    infrastructure **cannot** fix it: `spatial_impute.py`'s `knn_fill` fills exactly **0** rows in the
    3 fully-affected cells at every radius from 100 m to 1000 m — every candidate donor is itself
    missing `height_m` by construction. That is the MNAR guard working as designed. Widening the
    radius is inert. Verified by two independent executions (employee + manager re-run).
  - **Two framing corrections.** `nyc_suburban` and `nyc_rural` are geographically **outside New York
    City** (Nassau County and the Catskills) despite their names — NYC municipal data cannot serve
    them. And `austin_centre` (84.5 %, 64 observed values, already partially fillable today) is
    structurally unlike the 3 fully-NaN cells → a **split strategy** is indicated, not one uniform fix.
  - **Candidate fix shapes, ranked, none adopted:** (b) ingest Microsoft Global ML Building Footprints
    (CDLA Permissive 2.0, nationwide, one-off enrichment script) > (f) wire `impute_column`'s existing
    KDE path for `austin_centre`-class cells > (d) structural cross-cell donor pooling > (c) zone-type
    median borrow > (a) targeted OSM re-fetch > (e) accept-and-document.
  - **New defect, logged OPEN, deliberately unfixed: E-UTCI-10** — `spatial_impute.py` silently skips
    zero-neighbour rows without MNAR-flagging them (6 rows in `nyc_rural`, 13 in `austin_rural`).
    Observability gap, not a correctness gap; matters only once spatial imputation is wired into a
    production path.
- **~~Next action~~ — SUPERSEDED 2026-07-25 by the height-backfill fix plan below** (the user granted
  the scoped one-off exception; the count came back 80.2/45.0/92.0/62.0 %, i.e. *not* thin, and the
  adopted fix was the existing `fusion` tier via Overture rather than candidate (b)'s new script).
  Original text kept for the record: a manager decision, then a new plan. The follow-up Stage-1 plan's ranking hinges on
  one fact this investigation could not obtain under its own local-only rules: **how densely Microsoft
  Global ML's height sub-attribute actually populates these 4 bounding boxes.** That must be *counted*
  from downloaded data, so it needs the user to either unblock CLAUDE.md's §5.3 live-network gate or
  grant a scoped one-off exception. If density is low, candidate (b) drops and (a)/(d) rise.
- **🔧 E-UTCI-09 HEIGHT-BACKFILL FIX PLAN — 🔒 CP-C SIGNED 2026-07-25, plan COMPLETE (T01-T07, T09-T13; T08 closed unbuilt at CP-B).**
  `docs/docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md`. CP-A (mechanism
  proven offline) and CP-B (coverage measured — 80.2/45.0/92.0/62.0% of each cell's gap, not thin
  anywhere — ruling: CONTINUE) both signed. The platform's existing-but-unwired `fusion` tier
  (source registry landed Phase D; router `_fusion_tier` was a stub, E-UTCI-11) was completed and
  routed `height_m` through Overture for the 4 affected cells, with a 2.1 m minimum-height sanity
  floor (IRC/IBC R305.1) and a spatial-tier fallback for fusion misses. E-UTCI-10's silent
  zero-neighbour skip was fixed alongside (distinct `SPATIAL_NO_NEIGHBOUR_SKIPPED` token, never
  conflated with `SPATIAL_CLUSTER_MNAR_BLOCKED`). 8 unaffected cells confirmed byte-identical /
  zero observed-value overwrites. Full detail and numbers in the sub-plan's own progress log and
  `docs/docs_DONE/OUTDOOR/UTCI/UTCI_CHECKLIST.md` §3b.
- **✅ T11 Stage-6 re-run COMPLETE 2026-07-25 — the flat-open-field signature is gone from every cell
  that carried it.** Precise statement (the manager corrected the executor's "all 4 cells" phrasing at
  CP-C): **three** cells carried `svf_mean = 1.0000` and all three left it — `nyc_suburban` 1.0000 →
  **0.9619**, `nyc_rural` 1.0000 → **0.9972**, `austin_rural` 1.0000 → **0.9935**; `zero_building_massing`
  flips `True → False` on exactly those three. `austin_centre` **never carried the signature** (0.9474,
  84.5 % excluded, not 100 %) and is judged on a different basis: exclusion 84.5 % → **2.7 %** and
  `svf_mean` 0.9474 → **0.8426**, the most enclosed value in the fleet, corroborated by a 216 m fused
  max matching downtown Austin's real skyline. Manager re-derived all four `svf_mean` directly from
  each `06_mc_svf.tif` with `rasterio` — agreement to 6 dp with `06_mc_manifest.parquet`; per-cell
  minima 0.0023–0.2409 (a flat field cannot produce a 0.0023 pixel) and the density ordering
  `austin_centre` < `nyc_suburban` < `austin_rural` < `nyc_rural` tracks fabric correctly. Before/after
  table for all 12 cells (8 unchanged, 4 changed, clearly flagged) and figure at
  `openubem/outputs/comparisons/t11_e_utci_09_before_after_comparison.csv` /
  `t11_e_utci_09_svf_before_after.png` (copies under
  `docs/docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/figures/`). T13 (docs/registry) done alongside —
  `docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` §3.3.1 (new) and
  `OpenUBEM_imputation_methods.md` §4.1 both updated.
- **🔒 CP-C SIGNED 2026-07-25 — E-UTCI-09 dispositioned MATERIALLY FIXED WITH A DOCUMENTED RESIDUAL,
  deliberately NOT closed.** Sub-plan §9 carries the full signature. **What is fixed:** no cell computes
  as a flat open field any more and the 12-cell fleet is internally comparable in a way it was not on
  2026-07-24; the 8 previously-healthy cells are byte-identical with **0** observed values overwritten;
  no EUI baseline moved (structural argument — only `config.py`, `imputation.py`, `spatial_impute.py`
  plus 2 new files touched; no Stage 1-5 module). **The residual, stated plainly:** post-fusion
  `height_m` stays `NaN` for 15/1589 rows in `nyc_suburban` (0.9 %, negligible), 11/413 in
  `austin_centre` (2.7 %, negligible), **47/245 in `austin_rural` (19.2 %, material)** and **72/198 in
  `nyc_rural` (36.4 %, material)** — those two cells' UTCI fields are computed on roughly four-fifths
  and two-thirds of their real building stock and **must not be quoted as complete**. Closing that
  residual needs better *sources* (LiDAR / municipal data for the Catskills and rural Travis County),
  not another imputation tier: the prior investigation proved the spatial imputer cannot close it and
  this plan proved fusion cannot either → **forwarded to a future Stage-1 acquisition arc.** Restated
  post-floor: the 2.1 m minimum-height floor (IRC/IBC R305.1) rejected 3 sub-metre Overture rows, moving
  `nyc_suburban`'s pre-floor 80.18 % gap-filled to **79.99 %** — a deliberate NaN over a physically
  absurd fill (the source contains a 0.216 m "building").
- **Full suite at CP-C: `67 failed, 1746 passed, 9 skipped, 36 errors`** — CP-B's prediction (67 + 36)
  landed exactly, no file outside the written 10-file known-bad baseline appears, and the two
  imputation-adjacent live-risk files (`test_debias.py`, `test_impute_montage.py`) held at exactly 5 and
  5. `tests/test_fusion.py` 4 → **0** as mandated (29/29), `tests/test_height_backfill.py` 15/15,
  `tests/test_imputation_routing.py` 23/23. **The §5.3 live-network gate stays CLOSED** — T05's one-off
  cached Overture pull is spent, test-guarded, and explicitly **not** precedent.
- **Defects leaving the sub-plan:** E-UTCI-10 ✅ fixed (T09), E-UTCI-14 ✅ fixed (obsolete stub-raise
  test, fixed by manager overrule rather than dumped on a later owner), E-UTCI-15 ✅ resolved (process
  incident — two concurrent Stage-6 runs raced on one output dir; both trees killed, both contaminated
  dirs destroyed, single clean re-run; **no shipped artifact affected**). Still OPEN and forwarded:
  **E-UTCI-11** (half-landed Phase-D fusion ship), **E-UTCI-12** (`test_draw_methods.py` aborts the
  whole suite at *collection*), **E-UTCI-13** (the height cache stores post-normalization output, so
  `levels`/`use_class` silently come back null on re-read — harmless today, a trap for the next arc
  that reuses it). **Standing lesson: the half-landed ship is a repo pattern, not an accident** — three
  instances in one arc of spec tests committed ahead of their implementation. Any future arc touching
  Stage-2 imputation should expect more, and must *run* a module's tests before letting "already exists
  and is tested" be load-bearing in a plan's §4.
- **📋 POST-CP-C COMPLETENESS PASS 2026-07-25 — the manager audited the plan *document* rather than the
  work, and found 5 traceability gaps.** None changed a number, a verdict, or the E-UTCI-09 disposition.
  Four fixed in place, one forwarded (sub-plan §9.8 has the table):
  - **The load-bearing one: the backfill is NOT reproducible from a clean checkout, and the plan never
    said so.** `config.FUSION_SOURCES_BY_TARGET` ships as `{}` and the Overture cache lives uncommitted
    at `~/.openubem/heights/` — so a fresh clone running Stage 6 on the 4 cells reproduces the **old**
    flat-field result (`svf_mean = 1.0000`). **That is not a regression and must not be diagnosed as
    one.** The fix lives in the *mechanism*, not in the committed data: fused heights were never
    written back into `01_buildings.gpkg`. New sub-plan **§10** documents the 4-step reproduction
    (re-pull → wire per-cell slice path via env var → `impute_missing` → Stage 6), flags that the
    endpoint is pinned to Overture release `2026-06-17.0` so the census percentages are release-bound,
    and notes a re-pull needs **its own** network authorization — §5.3 is still closed and T05's
    exception is spent, not inheritable. Two persistence options are sketched for a future arc
    (freeze the snapshot into the fixtures, or commit a slice + config profile); neither is adopted,
    both exceed this plan's mandate — and **neither moves the rural residual**, which is a source-
    coverage limit.
  - **New defect E-UTCI-16 — logged, forwarded, then ✅ FIXED the same day after the user challenged
    the forwarding.** The challenge was right: the comment was not inherited debt, **T07 of this plan
    made it false**. The plan had already ruled on this exact case at E-UTCI-14 ("cleaning up a test
    your own change invalidated is not scope creep; leaving it is debt-dumping") — §8 was applying to
    E-UTCI-16 the disposition it condemns two entries above. Fixed by Sonnet dispatch (comment-only,
    2 lines); manager re-read `config.py:90-150` directly to confirm `IMPUTE_ENABLED_TIERS` and all
    six `FUSION_*` defaults untouched; `pytest test_fusion + test_imputation_routing +
    test_height_backfill -q` → **67 passed**. *(The dispatch brief's own `git diff --stat` verification
    step was faulty — it assumed a clean tree against a repo carrying ~22 pre-existing modified files.
    The executor stopped on the false premise instead of reporting a misleading diff; the error was
    the manager's, in the brief.)* Original text of the defect: `openubem/config.py:139-140` still said
    "`fusion` itself stays OUT of `IMPUTE_ENABLED_TIERS`" while line 100 now ships
    `("fusion", "spatial", "statistical")` — the file states both the right thing (lines 95-98) and its
    negation, ~40 lines apart. Comment-only, zero behavioural effect, but it is the exact failure mode
    E-UTCI-11/12/14 documented, and CP-A's F-D′ ruling turned on trusting this very comment over a
    test's. Needs one short Sonnet dispatch; deliberately not self-fixed (manager writes no code).
  - Three housekeeping fixes: E-UTCI-14's fix had **no progress-log entry** and its cross-reference
    dangled (entry now written); §2's file layout omitted `tests/test_imputation_routing.py`; §9.3
    credited a "T07/T08" invariant when T08 was closed unbuilt.
  - **Lesson:** the three housekeeping gaps are all *the plan describing itself wrongly while its
    measurements were right*. CP-C verified the work and did not re-read the document. Both passes are
    needed and they are not the same pass.
- **🔒 SUB-PLAN CLOSED 2026-07-25 — closing statement in its §11.** Nothing awaiting a decision.
  Leaving it: the rural source-coverage residual (→ future Stage-1 acquisition arc), three open
  defects **E-UTCI-11 / E-UTCI-12 / E-UTCI-13** (→ whichever arc next owns Stage-2 imputation or
  `height_cache.py`), and the §10 reproducibility constraint. Closed inside the plan and forwarded to
  nobody: E-UTCI-09, E-UTCI-10, E-UTCI-14, E-UTCI-15, E-UTCI-16. The parent plan's §10 heading —
  which still read `OPEN — 2026-07-24` while carrying the CP-C disposition beneath it — was corrected
  to match.
- **🧹 Hard-rule violation found and fixed 2026-07-25:** `sub-plans/figures/t09_zero_neighbour_fix_check.py`
  was sitting under `docs/`, against CLAUDE.md's "no `.py` under `docs/` ever" — and T13's own progress
  log had reported that criterion clean. Verified byte-identical to its scratchpad original, deleted;
  `docs/docs_ACTIVE/` is now `.py`-free. **A larger pre-existing violation remains, and it is not
  cosmetic:** 12 `.py` files under `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/` are collected
  by pytest and account for **59 of the 107** known-bad test results in the CP-B baseline table
  (`test_elevators.py` 24, `test_step3_orchestrator.py` 17, `test_outputs.py` 10,
  `test_parser_elevators.py` 8). Moving or excluding them would cut the repo's known-bad count by more
  than half. Flagged for a repo-hygiene pass; out of scope for the UTCI arc.
- **🗂 Figure re-organisation (user, 2026-07-25):** the arc's `docs_ACTIVE` figure copies moved out of
  `implementation/` into **`docs/docs_DONE/OUTDOOR/UTCI/results/UTCI-maps/`** (5 spatial/raster panels) and
  **`docs/docs_DONE/OUTDOOR/UTCI/results/UTCI-figures/`** (3 plotted charts). `openubem/outputs/` remains the
  canonical flat home per the standing rule and every `openubem/outputs/...png` path in the docs is
  still correct. The two stale `docs_DONE/OUTDOOR/UTCI/implementation/` pointers — one in
  `OpenUBEM_results_UTCI_microclimate.md` §5.4, one in the parent plan's CP-3 entry — were updated, and
  §5.4 now carries a short "where the figures live" box.
- **✅ USER DECISION 2026-07-23 — Q-04 CLOSED, Option A: UTCI is a SEPARATE ANALYSIS PRODUCT**, not a
  headline output alongside EUI and carbon. Rationale: EUI is validated against measured data (LL84 /
  EBEWE / CBECS); UTCI will not be validated against anything measured in this arc, and an
  unvalidated number sitting in a validated table borrows authority it has not earned. Now binding —
  plan **§6a** converts it into five hard constraints (no UTCI columns in `05_results.*`, nothing in
  the neighbourhood summary, Stage 6 never part of a standard run, viewer keeps energy colouring with
  the UTCI layer default-off, never described as "validated"). Promotion stays available as a *future*
  decision on new evidence — after a measurement campaign, or for anchored cells only.
- **Remaining open questions** (plan §11): reachability of the official `UTCI_a002.f90` source
  (mitigated — §11 has a 3-rung ladder ending at ladybug-comfort / pythermalcomfort coefficients);
  and whether real tree-canopy data exists for NYC/LA/Austin. Neither blocks execution.
  *(Q-03 was closed in v1.1 as a false premise; Q-04 closed by the user 2026-07-23.)*

---

## L. `layoutAssigner` — prototype-substitution resolution mode — **ALL 6 SUB-ARCS CLOSED; last signature CP-E 2026-08-04 (storey matching) — nothing open**

> Added 2026-07-26. This arc ran for four days across five consecutive plans and had **no section in
> this document** — it existed only as six quote-blocks in the header. Those blocks stay as the dated
> journal; this section is the structured index. Root: `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/`.

**What it is.** A fourth resolution mode: instead of extruding OSM footprints, `layout_assign`
substitutes a **scaled DOE reference prototype** (25-baseline library, `00.BaselineBuildings_NUs_v231`)
for each building. It buys real zone topology and real HVAC plant; it costs geometric fidelity.
It is **not** the adopted baseline and never has been — see §0.

### Sub-arc index

| # | Sub-arc | Closed | Signature | What it left behind |
|---|---|---|---|---|
| 1 | **Base build** (T01–T12) | 2026-07-22 | CP-A/B/C | E-LA-05, E-LA-06 OPEN-BLOCKED |
| 2 | **Phases 4–6** (T13–T17) | 2026-07-23 | CP-E | First full 8,160 sweep: **96.65%**. E-LA-07/08/09, and E-LA-10 (silent wrong `dhw_eui` on 80% of the fleet) |
| 3 | **Debug-fixes** (T01–T11) | 2026-07-23 | CP-E (v2) | **96.65% → 98.81%**, 176 recovered, 0 new failures. E-LA-11/12/13/14 |
| 4 | **Structural-fixes** (T01–T11) | 2026-07-24 | CP-E **with caveat** | 4 fixes verified fleet-scale — **but 98.81% → 97.92%**, because `thermal_mass=True` unmasked **E-LA-20** (150 `nyc_rural` SmallOffice newly Fatal) |
| 5 | **E-LA-20 investigation** (I01–I05) | 2026-07-25 | CP-INV — **ended OPEN by design** | Root cause proven, not hypothesized. E-LA-21, E-LA-22 |
| 6 | **E-LA-20 multilayer fix** (F01–F11-N-b) | 2026-07-25 | **CP-C SIGNED** | Fixed + verified 150/150. E-LA-23, E-LA-24 |
| 7 | **Storey matching** (R01–R10) | 2026-08-04 | **CP-E SIGNED** | T20 fleet: **99.914%** (8,153/8,160), median 122.23 kWh/m²/yr. E-LA-36 fixed inside arc; E-LA-38/39/40/41 found; Q3 confirmed NOT closed |

### The E-LA-20 defect, in four lines

- **Root cause:** `patch_envelope()` pinned conductivity at `_K = 0.12` and let thickness absorb the
  whole target R (`Thickness = R × 0.12`). Harmless as `MATERIAL:NOMASS` — a pure resistance, no CTF
  series. Once `thermal_mass=True` became the default it became a **real** `MATERIAL` (ρ=800, cp=1000):
  a well-insulated roof turns into a single homogeneous slab **over a metre thick**, and the CTF solver
  cannot expand it → Fatal in `InitConductionTransferFunctions`, in ~0.1 s, before Warmup.
- **A second, identical site existed** at `builder.py::assign_constructions()` — latent only because
  `thermal_mass` defaults `False` outside `layout_assign`. Closed by the same fix (F-08).
- **Shipped shape:** capped mass layer + `MATERIAL:NOMASS` residual carrying the leftover R, in the new
  shared module `openubem/idf/opaque_assembly.py`. Preserves U exactly; never exceeds 2 layers;
  byte-identical to prior behaviour below the cap.
- **Frozen constants:** `T_ENGAGE = 0.868 m` (F-13), `T_MASS_MAX = 0.35 m` (F-20). Both **measured at
  the value and the `u` they ship to**, not inferred from a bracket.

### Three falsifications this arc survived — the reason to trust the result

1. **The Fourier `sqrt(dt)` scaling was wrong.** F01 measured the CTF boundary at 2/4/6 timesteps-per-hour
   and found it flat (0.868–0.946 m) and *non-monotonic*. The plan's own headline **12.6% exposure
   figure was withdrawn** — it had been an extrapolation from one calibration point.
2. **The adopted fix shape was killed by its own calibration task.** F03-R: the adaptive-N split Fatals
   at every N from 1 to 10, at every timestep. The control variable is **total** assembly thickness
   (`R·C`), not layer thickness. Splitting preserves total mass exactly — hence preserves `R·C` exactly
   — hence cannot move what the solver responds to. **Binding corollary: any mass-preserving fix is
   dead on arrival.**
3. **CTF convergence is not monotone in the cap thickness** (F-17): a genuine isolated FATAL sandwiched
   between two PASSing neighbours, manager-verified on the raw IDFs. This killed a rule that had fit 16
   points, and is why the shipped constant was run at its exact shipped value rather than bracketed.

### What this arc did NOT do — conditions, not footnotes

- **The fleet was never re-run.** F11 was a manager NO-GO: its own pass criterion required a T19
  comparison that E-LA-22 makes irreproducible. F11-N replaced it with the full 150-row at-risk
  population — complete coverage of what the fix can reach, but **not** a fleet run.
- **The 8,010 untouched rows rest on an argument** (byte-identity + determinism), which collapses the
  moment that path stops being byte-identical.
- **E-LA-23's accuracy cost was never measured.** Its presence is measured (96/150 vs 8/150); its effect
  on the annual number is not. The "cosmetic" label this lineage has carried across five entries is a
  claim about accuracy that **no one has ever tested**, this arc included.

### Cross-mode comparison — measured at arc close, 2026-07-26

The arc had compared `layout_assign` to the other 4 resolution modes in figures for months, but never
in numbers. Matched **building by building** on the 5 common cells (4,365 buildings where all 5 modes
succeed), reading T19 and t08 directly:

| | building | floor | auto | fast_zone | **layout_assign** |
|---|---|---|---|---|---|
| Success rate (n=4,530) | 100% | 99.98% | 99.96% | 99.96% | 96.45% |
| Zones/building (median) | 1 | 2 | 2 | 2 | **6** |
| Median total EUI | 159.9 | 175.1 | 178.9 | 183.3 | **109.7** |
| Median Δ vs `auto` | −0.8% | +1.8% | — | +2.1% | **−29.1%** |

**The other four cluster within ±5% because they differ only in zoning** — on `nyc_suburban`, lighting
(4.0), equipment (43.4) and DHW (43.2) are identical to the tenth across all four. `layout_assign` is
not a fifth zoning strategy; it replaces the whole building.

**Two findings, both new and both structural:**

1. **Half the −29% is by design, and was never quantified until now.** Lighting 26.5 → 10.2 and
   equipment 43.4 → 29.3, because the loads come from `ASHRAE901_*_STD2022` prototypes —
   **`layout_assign` models every building's internal loads as 2022-code construction regardless of
   real vintage.** The envelope *is* re-patched to real vintage/CZ by T16; internal loads are not.
2. **⚠️ The √S form distortion — open question Q3, resolved by default on day one, never revisited —
   is a bigger obstacle than E-LA-20 ever was.** Isolating one cell to kill the climate confound
   (`MidriseApartment`, `nyc_suburban`): `layout_assign` heating is **~2× `auto` at every size**
   (238.0 vs 118.1 at 79 m²), a *stable* ratio, so it is geometry, not an unscaled-quantity defect.
   `scale_baseline_idf()` scales vertices by √S in plan **while preserving height**, so a 79 m²
   building becomes a 4-storey prototype shrunk to 2.5% of its area with all 27 zones and an extreme
   surface-to-volume ratio. **Median S for `MidriseApartment` is 0.054; 67% of simulated rows are
   under 500 m²** — the mode runs overwhelmingly far below prototype scale. `la_suburban` (95.5%
   midrise) shows +0.1% only because LA has no heating load to amplify: the anomaly needs cold
   climate × small buildings, neither alone. E-LA-20 made 150 buildings fail loudly and is fixed;
   **Q3 silently doubles small-building heating in cold cells, fleet-wide.** Not fixed, not scoped.

Full derivation: results doc §7. Q3's own entry updated in the base plan's §7.

### Standing disposition — ARC CLOSED 2026-07-26, no further work scheduled

`layout_assign` is **adopted for its intended use** — high-fidelity zone/HVAC-topology studies — and
**not certified for fleet-level EUI reporting**. Two independent reasons, either sufficient: the
fleet was never re-run post-E-LA-20, and Q3's √S distortion is unquantified outside the one cell
measured above. The adopted simulation baseline is unaffected either way — it never runs this mode.

**Deliberately NOT done, and parked rather than forgotten:** the ~15 h fleet re-run (a decision, not
a task — and it cannot produce a clean T19 comparison while E-LA-22 holds); E-LA-21's `has_fatal`
grep fix (reporting-only); the 2 pre-existing `nyc_rural` failures. Anyone resuming starts at
`prompt/DIRECTOR_PROMPT_post-e-la-20_2026-07-25.md`.

### ✅ Storey matching (sub-arc 7) — **CLOSED 2026-08-04, CP-E SIGNED**

`debug/storey-Matching/` is the arc's single home. The original 12-task plan
(`DONE_PLAN_storey-matching_implementation.md`, now CLOSED) built the `Zone.Multiplier`-based
`match_storeys()` mechanism (A1–C04, CP-A/B/C signed 2026-07-26) so that a fleet building's real storey
count can exceed a prototype's own without abandoning the prototype; a follow-on plan
(`PLAN_storey-matching_REMAINder.md`, R01–R10) fixed defects the CLOSED plan's own audit surfaced,
re-ran the full fleet on T20, and closed documentation. **User's original diagnosis was correct**
(storey *height* stays real, storey *count* should follow the real building) **but the mechanism only
ever reaches the *taller*-than-prototype case** — the *shorter* case (the common one, at median
S=0.054) was explicitly declined by manager decision **R04** ("closed at option (a)": accept and
document the limit; extending to the shorter case "buys reach, not correctness" and would perturb the
82–98% of buildings currently running clean for no gain on the actual defect).

**T20 fleet result:** 8,153/8,160 = **99.914%** success, median `total_eui` **122.23** kWh/m²/yr — but
**150 of the +163-building success gain over T19 is the pre-existing E-LA-20 fix landing at fleet
scale, not this arc's own work** (full decomposition: results doc §8.1). **E-LA-36** (`Zone.Multiplier`
× `ZoneList` silent 50% storey over-count) was found and fixed *inside* this arc, 0/522 verified.
**E-LA-38** (41/8,160 buildings mislabelled Hotel→Office by the harvest's stale archetype source)
explains 100% of the fleet's 7 real failures — not a generic envelope defect. **E-LA-41** (EUI
denominator wrong by `n_storeys_represented / num_floors` for every non-`applied` building — the
large majority, 6,939/7,442 evaluated) is the arc's own quantified consequence of the mode's
fallback design. CP-D's two carried validation conditions are both answered on real fleet buildings
with real `eplusout.eio` (R06c): the denominator holds for `applied` (~0.002%) and fails at 4/3 for
non-`applied`; F-08's heating ratio moves *away* from 1.0 (0.32×/0.066×), scoped to one mild-climate
cell.

**⚠️ Q3 (§7.4/§9, the √S vertical-form distortion) is explicitly NOT closed by this arc.** The base
plan named a `Zone Multiplier` mechanism as "the obvious first candidate to evaluate" against Q3 —
this arc built exactly that mechanism, and it structurally cannot reach Q3's population (the shorter
case) or its mechanism (rendered geometry, not simulated-energy accounting — a multiplier writes no
vertex). Q3 remains open for a future arc; see `DONE-implementation_plan.md` §7 for the entry.

**Docs:** `PLAN_storey-matching_REMAINder.md` §5 (progress log: R01–R10, three director AUDIT entries
correcting non-reproducing executor numbers — see rule below) · results doc §8/§9
(`OpenUBEM_results_LayoutAssigner.md`) · `figures/README.md` (T20 figure disclosures) ·
`DONE_PLAN_storey-matching_implementation.md` (CLOSED, ~3,500 lines, cite by `F-nn`/`E-LA-nn` ID only).

**Recorded because it happened three times in this one arc:** an executor progress-log entry printed
a headline number that did not reproduce from the file it cited (F-11's transformer-cliff counts,
twice, and the 81.6%/98.4% inert shares going stale without a correcting entry). All three were caught
by director audit, not by the executor. Every number in the results-doc §8 addendum was traced to a
named file before being printed there.

**CP-E SIGNED 2026-08-04** — `PLAN_storey-matching_REMAINder.md` §5, final entry. The signature added
one definitional correction of its own: the replacement inert shares (100.0% `nyc_suburban` /
84.1% `la_suburban`) are a **status** measurement over the 7,442 evaluated buildings and exclude
`identity`; the old 81.6%/98.4% pair was an **archetype proxy** over all 8,160 and is not itself
stale — only its use as an inert share was. Results doc §8.2 now states both.

**Nothing in this arc is left in flight** — no cluster job outstanding, no fleet re-submission
pending, no executor mid-task. Open items were all forwarded with IDs (E-LA-21/22/23/24, E-LA-37,
E-LA-38, E-LA-40, E-LA-41) and Q3 remains open for a future arc.

**Reader-facing docs brought current 2026-08-05** — `OpenUBEM_fundamentals.md` §5.1/§5.1.2 and
`Results/OpenUBEM_results_Resolution.md` §1/§10 now reflect the closed arc; `layout_assign` is
deliberately given no fleet-EUI column (no `eio`-verified denominator, OPEN-01) pending a fleet
re-run that retains `eplusout.eio`.

---

## M. Open-items register — **the single tracker for everything still open (opened 2026-08-04)**

> # 🅿️ **PAUSED 2026-08-06 — the user is on other projects and will return.**
> **Nothing is running: no local job, no cluster job, no executor session.** Nothing is cancelled and
> ~~no task is half-finished. **32 items, OPEN-01 … OPEN-36, next free ID OPEN-37.**~~
> ~~**Count updated 2026-08-10 (twice; the later figure governs), kept consistent with the register's own §1 header: 35 tracked items
> (OPEN-01 … OPEN-40; IDs 05, 21, 23, 25 retired; OPEN-02 + OPEN-28 folded into OPEN-01), next free ID
> OPEN-41.** New since the line above: OPEN-38, OPEN-39, OPEN-40 (E02 completion census, 2026-08-10 —
> see the register's §0 amendment of that date for the numbers).~~
> **🔴 Count updated 2026-08-11 (the E02 audit and closure pass; this figure governs), kept consistent
> with the register's own §1 header: 31 tracked items / 31 findings (OPEN-01 … OPEN-42; IDs 05, 21, 23,
> 25, 30, 34, 39, 40, 41 retired; OPEN-02 + OPEN-28 folded into OPEN-01 and both discharged), next free
> item ID `OPEN-43`, next free defect IDs `E-LA-42` and `E-UTCI-17` unchanged.** Arithmetic:
> **35 − 5 closed + 1 opened = 31.** The live table was re-counted programmatically after the edit and
> re-derives to 31. Detail in the dated amendment further down this section.
>
> **The resume brief is the closing amendment of**
> `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — written to stand alone. The
> director handover `openings/prompts/DIRECTOR_PROMPT_openings_2026-08-06.md` now opens with a
> one-screen state box and closes with §11, the resume order. The board
> `openings/implemenation/board_published-numbers.html` carries a pause panel at its head (same
> published URL), with a snapshot copy at `openings/reporting/`.
>
> **Where the big run stands — 🟢 UPDATED 2026-08-09 (late): E02 IS SUBMITTED AND RUNNING ON SPEED.**
> ~~halted by a `MemoryError` and parked~~ — superseded. **CP-R1 and CP-R2 are both signed** on
> independent re-derivation; the R05 calibration probe (1,735 real simulations, 7.55 core-hours) resolved
> **both** pre-registered risks **CLEAN** — zero TIMEOUT (worst task 5.0% of the 2-hour wall) and zero
> OOM at `--mem=6G`. All 60 (cell, mode) arrays regenerated under a fresh **`e02`** fleet tag, 40,800
> IDFs verified on local disk **and** on the cluster. **19 arrays / 19,931 tasks (48.9%) queued at
> submission**, job IDs `1176411`–`1176599`; the remaining 41 are being placed by a shell retry loop.
> 🔴 **Why not all at once:** SLURM's cluster-wide **`MaxJobCount = 20002`** counts array *tasks*
> individually — 40,800 cannot be queued in one pass. Expected cost **6–27 h** on 32 CPUs (a range: both
> probe cells were rural; **no dense cell has ever been timed**).
> 🔴 **Before the harvest — not before the run:** **OPEN-37**, `t08_harvest_results.py:131` omits
> `*/eplusout.eio` from its tar list. The cluster keeps the file (manager-verified non-empty, 149/149 and
> 198/198); **the fetch never asks for it.** Harvest unfixed and the simulated-floor-area record — the
> independent check on OPEN-35 — is lost at retrieval. ~~`submit_fleet_t08.sbatch:63` deletes every
> `.eio`~~ — fixed by R01 and verified live.
>
> **Last work completed:** **C06** (OPEN-09's "cosmetic" label tested for the first time — it holds,
> 96.3% overlap, ≈0.20 kWh/m² residual), **C07** (fatal-detection fix in the E02 runner: 0 of 2 → 2 of
> 2 real fatals over 2,422 `.err` files), and the **≈10× correction** to
> `extra/SCOPING_five-mode-rerun-cost.md` (PART 3; Parts 1–2 left unedited so the failed prediction
> stays visible). **The no-compute queue is empty** — 16 tasks over 4 rounds, all landed, all audited.
>
> **Everything below this box is the history that led here. It is retained, not current.**

> **Current as of 2026-08-06 late evening: 31 items, OPEN-01 … OPEN-35, next free ID OPEN-36.**
> IDs **05, 21, 23, 25** are retired (closed / deferred / excluded / closed). Evening changes:
> **OPEN-25 CLOSED** (fixed 2026-06-10, the day after it was named — carried here for eight weeks
> afterwards); **OPEN-34 and OPEN-35 opened**, both found by *auditing* a completed task rather than
> by running one; first measurements made on **OPEN-22, OPEN-29, OPEN-06/07/11, OPEN-34**.
> Plan doc for the no-compute work: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_no-compute-queue.md`.
> The five-mode local re-run is **parked at the user's instruction** until a machine is free.
>
> **Superseded the same night — round 2 of the no-compute queue:
> `implemenation/previous/PLAN_no-compute-queue-2.md` (N06–N12). Now 32 items, OPEN-01 … OPEN-36, next free ID
> OPEN-37.** First measurements made on **OPEN-35 (size), OPEN-12, OPEN-06/07, OPEN-13, OPEN-14,
> OPEN-15/16/17, OPEN-10, OPEN-19**. Three findings that change what other documents mean:
> **(1) OPEN-06 is a provenance defect, not a labelling one** — the three failing buildings were
> *simulated* as `SmallHotel` while the results file records `SmallOffice`, so **every per-archetype
> grouping keys on a column that does not describe the run**;
> **(2) OPEN-35 touches 2,611 of 8,160 buildings (32.00%)**, all persisted at one storey, 1,031 of them
> classified mid/high-rise;
> **(3) OPEN-36 opened** — a progress-log entry marked *completed* describes code **no commit has ever
> contained**, while its tests *were* committed, which is why `pytest` can no longer collect the suite.
> **That last one makes every completion record in this file's history unverified until checked**, and
> checking costs no CPU.
>
> **Round 3 opened the same night — `implemenation/previous/PLAN_no-compute-queue-3.md` (N13–N15), all no-CPU.**
> **N15 has landed and is audited: OPEN-12 and OPEN-14 are two separate items, not one defect.** The
> four-cell convergence recorded under OPEN-14 — the four cells with no tracked Overture slice being the
> four worst for missing `height_m` — **is a coincidence.** The fleet's `01_buildings.gpkg` never
> consumed the UTCI backfill and **never could have**: `fusion.fuse()` has one caller fleet-wide
> (`imputation.py:655`) and `building_classifier.py` never imports imputation, so the fusion path is
> **architecturally unreachable** from the fleet's classification path, config-independent; and
> `nyc_centre`'s buildings file (`e063865`, 2026-06-30) predates its own Overture slice (`ef19141`,
> 2026-07-21) by three weeks. **OPEN-12 is a genuine OSM source-coverage gap — the UTCI arc's closing
> note was right.** N13 and N14 were still running at the time of writing.
>
> **N14 has since landed and is audited (OPEN-06 §3).** Stage 2 re-run at HEAD over four whole cells,
> all 33 columns of `05_results.gpkg` bucketed: **`archetype_id` is not the only column HEAD cannot
> reproduce — `data_quality_flag` cannot be reproduced either**, and what differs is *which imputation
> rule the classifier records as having fired* (`VINTAGE_NAN_PERMISSIVE_DEFAULT` / `HOTDECK_NEIGHBOR_*`
> at HEAD vs. `GROUPMODE_MED` committed). The `archetype_id` control passes exactly against N04's
> population file (per-cell 26 / 4 / 0 / 0). **Two director corrections on audit:** N14's claim that the
> two columns differ on the same rows is **struck** — 26 vs 38 on `nyc_centre`, the excess differing
> only by a `narrow_perimeter_fallback` token written at Stage 3 (`openubem/idf/builder.py:614-615`),
> which Stage 2 can never emit; and **26 of the 33 columns remain unchecked**, being Stage-3-or-later
> outputs no no-CPU task can reach. Useful side-finding: **`footprint_area_m2` is a third
> geometry-re-derived column** alongside `levels`/`height_m` — naive diffs of it report a defect that
> is not there (715/738 `nyc_centre` rows differ before any Stage-2 code runs).
> **N13's first attempt stalled and produced nothing** — the executor ended its turn waiting for a
> notification that never comes. Re-dispatched fresh with an explicit anti-stall clause; third
> occurrence of that failure mode.
>
> **Rounds 3 and 4 are now complete — sixteen tasks across four rounds, all landed, all audited by
> re-derivation. The no-compute queue is empty; every remaining first measurement needs CPU, and
> CPU-bound work stays parked at the user's instruction.**
> **N13 (OPEN-36) — T07 is the only one.** Full population swept, not a sample: **596** progress-log
> entries across 59 documents → PRESENT 424, MOVED 6, NEVER-COMMITTED 14, UNCHECKABLE 152. Of the 14,
> **one** is a governance gap (T07), **twelve** are this arc's own untracked measurement CSVs (each
> verified on disk, untracked, zero commits on any branch), **one** is a temp script its own entry
> declares deleted. Control re-run by the director: `_draw_tier` exists in **no commit on any branch**
> and not in the working tree, while its tests are committed. **The number started at 49** — a
> mechanical heuristic's output, of which **35 were misattributions** caught before reporting; both
> verdict columns retained. **An unaudited sweep would have reported 49 phantom completion records.**
> **N16 (OPEN-06) — the coverage gap is closed and the stated prediction held exactly.** Eight
> remaining cells swept; `archetype_id` differs 2/413 `austin_centre`, 4/226 `la_centre`, 5/618
> `la_urban`, **zero** in the other five, all 11 rows matching N04's population one-for-one on both
> values. With N14's four cells: 5,390 + 2,770 = **8,160 — every cell, whole**. **The 41-building
> mislabel population is fully accounted for and there is no third unreproducible column.**
> `data_quality_flag`'s 171 differences resolve to **168 Stage-3 token artifacts and 3 genuine
> provenance divergences** — the split needed four further Stage-3 appenders found beyond
> `narrow_perimeter_fallback` (`builder.py:145,439,473`; `geometry/footprint.py:33,38`, **the last two
> comma-separated**). **The 3 real divergences are not the same buildings as the archetype failures** —
> disjoint in `la_urban`, absent in `la_centre` — so the two defects are independent in both
> directions, finishing off N14's struck "same rows" claim.
>
> ### 2026-08-06 — the compute queue opens; **E02 is running**
> Plan: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_compute-queue.md` (C01–C06). **The user
> released the local workstation for simulation**, unparking every measurement the no-compute queue
> could not reach.
> 🔴 **A second prerequisite was found, and it had an attractive wrong answer.** Besides the known
> missing `layout_assign` mode, `LOCAL_CELLS` (`scripts/cluster/t08_local_remainder.py:48-51`) held
> **only 7 of 12 cells** — the four NYC cells and `la_centre` had **no `CELL_CONFIGS` and no
> `CITY_OF` entry**, and `CITY_OF` is read through a **silent fallback to the cell name** (`:423`), so
> the omission would have broken every city-level group-by without ever raising. The runner is *named*
> `t08_local_remainder`, which invites running 7 locally and reusing the cluster's T08 for the other
> 5 — **that would rebuild OPEN-28**, since T08 is five-week-old code that deleted every `.eio`.
> **Pinned: all twelve cells run locally, on one generation.**
> **C01 done, CP-C1 signed.** Runner extended to 12 cells / 5 modes (`layout_assign` last), plus
> `--output-csv` / `--work-base` flags — the runner clobbers its output CSV after every cell and the
> 2026-07-01 artifact had to survive. The executor declined the end-to-end test on a tail-risk
> argument that was **about `layout_assign`, not about the untested new cells**, so the director ran
> the bounded smoke it did not cover (`nyc_rural`/`building`): **198/198 success, 0 fatal,
> `city="NYC"`, 198 `.eio` retained, 0 `.eso` surviving.**
> **C02 = E02 launched:** 12 cells × 5 modes × 8,160 = **40,800 simulations**, 16 workers, `.eio`
> retained. It is the only measurement that closes **three** register items at once — **OPEN-01**
> (a verified multiplier-aware denominator per building), **OPEN-02** (the `.eio` that has never
> existed for any fleet building), **OPEN-28** (all five modes on one generation). Expectations were
> written down *before* the run: ≈7.3–11.3 h, ≈0.1% failure rate, ≈43 GB worst case.
> **CP-C2 is a completeness gate** — nothing downstream starts until every (cell, mode) is confirmed.
> 🔴 **C02 was killed once at ~02:15 by the director, not by a defect.** It had been started with the
> **session-bound** background facility rather than as an independent OS process, so a session
> compaction stopped it and every EnergyPlus child. The plan had already said *launch it detached*;
> the instruction was written and then not followed. At the kill: **561 of `nyc_centre/auto`'s 738**
> `.eio` written, **no disk guard, no traceback, no fatal, no `sim_done.txt`**. **Little was lost** —
> resume is **per building** (`t08_local_remainder.py:268` skips anything with an `eplusout.end`, and
> `.end` survives trimming), so only Step 2 + one Step-3 pass are redone. Relaunched 02:52 via
> `Win32_Process.Create` (WMI), which sits in no session job object; new log `e02_run_2.log`, the
> first log kept. **Read the ~35-minute gap as a kill, not a slow first cell — and do not read it as
> evidence about the ≈7.3–11.3 h estimate**, which is judged from the original 01:54 start.
> **C03 (OPEN-10) — done and audited. The carried "90 buildings" figure reproduces exactly**, from a
> fleet-wide pass over all twelve cells using the shipped `compute_band_map()`/`match_storeys()`:
> 66 `MidriseApartment` + 24 `HighriseApartment`, over the same 7,442-building population OPEN-01's
> crosstab uses. **Notable because carried numbers in this arc have a poor record** — OPEN-12's
> percentages did not reproduce, OPEN-28's framing was wrong, N14's "same rows" claim was wrong.
> Both of N11's limits confirmed at fleet scale (proposal populated for exactly the two ZoneGroup
> archetypes; all 2,276 apartment `fallback_shorter` rows at `num_floors ∈ {1,2}`, none moved).
> 🔴 **The side finding is the operative one: fleet-wide `fallback_not_expressible` is 1,976 across
> 10 archetypes — `SmallOffice` alone is 1,580 — so OPEN-10's remedy reaches 90 of 1,976 = 4.6%.**
> No future plan may present it as fixing inexpressibility. The mechanism was **modelled, not built**;
> the 100% flip is band arithmetic, not a verified EnergyPlus result. Director slip recorded: a first
> re-derivation reported 4,682 changed rows, a **NaN artifact** — the executor was right.
> **What compute cannot fix:** OPEN-19 needs code, not cycles (no climate-zone or code-year switch
> exists; LA's HVAC comes from a Buffalo prototype); OPEN-11 needs a user decision, not a measurement.
> **The paragraph below is the 2026-08-05 snapshot and is left unedited, per the append-only rule.**

> **🔴 Amended 2026-08-11 (later) — the E02 audit and closure pass.
> The register is now at 31 tracked items / 31 findings, down from 35 / 37.**
> Plan: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_e02-audit-and-closure.md` — T01–T06, all six
> landed, three checkpoints director-signed by independent re-derivation from raw artifacts.
> **Arithmetic, so it can be checked: 35 − 5 closed + 1 opened = 31.**
>
> **Closed:** **OPEN-30** (vintage demonstrated on 60/60 manifests, 40,800 rows, 5 distinct values,
> 93.44% `DOERefPre1980` vs the 92.9% expected, zero crossover against raw `year_built`) ·
> **OPEN-34** (all 12 adopted cells whole — `05_results.csv` rows = `01_buildings.gpkg` features,
> fleet 8,160) · **OPEN-39** (2.14 GB orphaned by failed tasks; zero of 15 `task.rc` references in 9
> scripts uses it as a completion test) · **OPEN-40** (submitter untraceable, which its own text names
> as the answer) · **OPEN-41** (all 44 fatals now have recorded causes — all thermal runaway, none
> structural). **Discharged:** **OPEN-02** and **OPEN-28**, the two findings folded under OPEN-01.
>
> 🟢 **The headline result: the adopted `auto` mode's EUI denominator is measured correct** — median
> error factor **1.0000**, **99.63% of 8,160 buildings within ±1%**, from all 40,800 `.eio` files with
> 0 parse failures. No mode had ever had this measured before.
>
> 🔴 **And three things that are wrong, stated in the same breath:**
> **(1)** `building` mode simulates exactly **one storey** while its published denominator multiplies
> footprint by `levels` — median error factor **0.5000**. E01c's *"verified sound at HEAD"* verdict on
> that mode did **not** cover the denominator.
> **(2)** **OPEN-42 opened:** the `Warehouse` type is 0.47% of the fleet but carries **26 of the 44
> fatals** (**≈309× relative risk**), and **six of them carry a placeholder `footprint_area_m2` of
> exactly 200.0 m²**, so the adopted `auto` mode divides by a denominator wrong by **20.3×–336.7× on
> six published buildings.** Its effect on the 158.0 kWh/m² fleet figure is **unmeasured.**
> **(3)** **OPEN-38's premise was falsified, not closed** — *"Base surface does not surround
> subsurface"* is a **Warning**, not a Severe, and kills nothing; all 7 `layout_assign` fatals are
> thermal runaway in the zone `LAUNDRYROOMFLR1`, and one building with the malformed geometry
> **completes and publishes results.**
>
> **OPEN-01 did NOT close.** Its (a) and (b) are answered on 40,800 runs; **(c) — one code state —
> cannot be proved, because no commit hash was recorded at generation time.** A ruling is owed on
> whether the circumstantial evidence suffices, or OPEN-01 can never close on this corpus.
> **Rulings owed, in order: OPEN-22 · OPEN-01(c) · OPEN-01's remedy · CP-M2 · OPEN-11.**
> **Nothing is queued, nothing is in flight, no agent is running, and Speed is not needed.**

`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` — **29 items, OPEN-01 … OPEN-32**
(**OPEN-23 `layoutGenerator` excluded by the user 2026-08-04**, ID retired — not a direction being
continued; the engine's record stays under `docs/docs_TODO/layoutgenerator/`. **OPEN-21 mixed-use
classification deferred by the user 2026-08-05**, ID retired — one function per building stands, full
record at `docs/docs_TODO/mixed_use_classification.md`, **question closed to further asking**),
compiled by sweeping this checklist, every arc plan doc, both June audit docs, and project memory.
It supersedes the per-arc "forwarded open" lists as the place to look; those stay as the historical
record inside their own arcs.

**It is an INVESTIGATION document, not a plan.** Per the user's instruction (2026-08-04): the register
first, execution documents after. Each item states what is known, what is only believed, where the
evidence lives, and **the one measurement needed before a plan can responsibly be written.** Every
claim carries an evidence mark — ✅ verified · 📄 documented, not re-verified · ⚠️ stale-risk ·
❓ unmeasured. **No 📄 or ⚠️ number goes into a plan without being re-derived first.**

**Director prompt for a fresh manager session:**
~~`docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-05.md` — self-contained, **current**.~~
**Amended 2026-08-11:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` —
self-contained, **current**. It is written after E02 finished *and* was harvested, so it opens on
audit → rule rather than on submission. **All earlier prompts (`..._2026-08-04/05/06/10.md`) are spent**
and now live in `prompts/previous/`, each marked superseded in-file; kept as historical record only.
Supporting documents for this arc live in `docs/docs_ACTIVE/openings/extra/`, per user instruction
2026-08-05 — the arc folder itself stays clean.

**Four patterns visible only with the items in one list:**
1. ~~**OPEN-01/02/03/04 can make already-published numbers wrong.** Everything else makes the project
   less *complete*.~~ **All four measured 2026-08-05 (M01–M05):** two confirmed large and
   unremediated (OPEN-01, OPEN-03), one cheap and approved in principle (OPEN-02), one recast as a
   process defect, not a metric defect (OPEN-04 → new OPEN-31). Three new items opened by the
   measurements themselves: **OPEN-30, OPEN-31, OPEN-32.**
2. **OPEN-08 and OPEN-14 are reproducibility defects** that undercut the evidence for other items —
   OPEN-08 puts an unquantified confound under every cross-generation comparison made so far.
3. **OPEN-22 costs a decision, not an arc** — it leaves the labelled-accuracy metric undefined while
   OPEN-04 reports an unexplained drift in that same metric. Read together. *(OPEN-21 was the other
   such item; deferred 2026-08-05.)*
4. ~~The register found a duplicate on its first pass~~ — **swept 2026-08-05 (OPEN-05, CLOSED):**
   41 `E-LA` + 16 `E-UTCI` IDs, **both sequences dense, no gaps, no ID reuse, and E-LA-21/E-LA-39 is
   the only duplicate** (treat E-LA-39 as an alias). Report:
   `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md`. Director-audited by independent
   re-enumeration. **Next free: E-LA-42, E-UTCI-17.** The sweep exposed a *different* hygiene defect,
   now **OPEN-29**: ~8 `E-LA` IDs are OPEN at their own defining line yet appear nowhere in the
   register — including `has_fatal` itself. Candidate list unverified; first measurement is to follow
   each ID forward to its final recorded status.

**Largest open modeling problem: OPEN-18 (Q3, the √S vertical-form distortion)** — unchanged in
substance, but one candidate mechanism has now been eliminated with evidence (see §L).

~~**Next free defect ID: E-LA-42 · next free register item ID: OPEN-33.**~~

🟩 **Current as of 2026-08-13 (CP-1 of `openings/implemenation/previous/PLAN_two-measurements-2026-08-13.md`),
kept consistent with the register's own §1 header: 35 tracked items (OPEN-01 … `OPEN-50`), next free
item ID `OPEN-51`; next free defect ID `E-LA-42` and next free UTCI defect ID `E-UTCI-17` both
unchanged — this pass opened no defect ID.** Arithmetic since the last figure written here:
**31 → 32** (12 Aug, OPEN-43 + OPEN-44 opened, OPEN-33 closed) → **33** (12 Aug night, OPEN-45 …
OPEN-48 opened across two passes) → **34** (13 Aug, OPEN-49, the `wwr` re-randomisation defect, on the
user's ruling) → **35** (13 Aug, OPEN-50, the test-suite fixture mutation, opened by the CP-1 audit).

🔴 **Two things this line must carry, because the count alone misleads in both directions.** The
published fleet EUI is **`157.1 kWh/m²` — pooled, total simulated energy ÷ total simulated floor area
over all 8,154 successful buildings.** The re-run's `159.2157` was **considered and rejected by the
user on 2026-08-13**; it is evidence inside OPEN-49 and **must never be restated as a fleet figure**.
And **five of the last seven items were opened by auditing a result, not by running a task** — a
register that only shrinks is being tidied, not audited.

~~⚠️ **Register-hygiene defect recorded 2026-08-13, not yet repaired:** the register's §1 summary table
jumps `OPEN-44` → `OPEN-50` — rows for `OPEN-45` … `OPEN-49` were never written, though all five have
full sections. **The sections are the authority; that table is not a valid item census until the five
rows exist.**~~

✅ **REPAIRED 2026-08-13 (evening), and repairing it exposed a second, larger census defect which the
user then ruled on (`2h`).** Both halves are now fixed and **the register's item count is auditable
against its own table for the first time since 2026-08-12.**

- **Half one — the five missing rows.** `OPEN-45`, `OPEN-46`, `OPEN-47`, `OPEN-48`, `OPEN-49` are now
  written into the §1 table in ID order, **each composed from its own §-section rather than from any
  summary**. Two things preserved rather than smoothed in the transfer: OPEN-46's row leads with the
  **reversal** of its own title (the title's alarming half is false — the published figure was never
  missing elevator energy), and OPEN-49's row carries `159.2157` **only** as within-item evidence.
- **Half two — three closures nobody had recorded.** With the five rows in, the table showed **38 live
  rows against a header of 35**. The gap was exactly `OPEN-04`, `OPEN-31` and `OPEN-43`: the 2026-08-12
  arithmetic had subtracted all three as closed, and **every count since was built on that subtraction**,
  but none of the three was marked closed in its own section, struck in the table, or listed as retired.
  🔴 **The published count of 35 rested on a closure that only one arithmetic line recorded.**
  **Ruled `2h` 2026-08-13: retire the three formally.** Done the same turn — closure blocks written into
  all three sections, rows struck, IDs added to the retired list (ten → **thirteen**), table re-counted:
  **35, matching the header.**
- 🔴 **Three constraints were deliberately carried forward out of those closures, because a closed
  item's constraints do not close with it.** From OPEN-04: **`92.0%` is unreproducible** (its answer key
  was rewritten in the next commit) and **the old 50-row fixture is never edited** — its bisect depends
  on it. From OPEN-31: **CP-M3 is obligatory**, and as of ruling `2a` it spans **two exams with two
  thresholds**, so **every accuracy figure must name its fixture** — a bare percentage is no longer a
  meaningful number in this project. From OPEN-43: **the headline is pooled `157.1 kWh/m²`** and
  **`159.2157` is never a fleet figure.**

✅ **Ruling 5 answered 2026-08-13 — OPEN-01(c) is settled.** You accepted the circumstantial evidence:
the corpus is treated as **one code state**, on the single unbroken **111-minute** generation window plus
one manifest schema across all 60 `(cell, mode)` pairs.

🔴 **The constraint that travels with it, and it is the whole point of recording this here.**
**One-code-state is now a RULED ASSUMPTION, not a measurement.** Every document that cites it must say so
in the same sentence. The ruling buys the project out of a question this corpus **cannot** answer — no
commit hash was ever stamped, and 25 of the 60 pairs have no generation-summary at all — **it does not
create the missing evidence.** If a cross-mode result ever turns on the assumption being exactly true,
**that result needs a fleet re-run with a recorded commit hash, and this ruling does not cover it.**

⚠️ **OPEN-01 does not close on this.** (a) and (b) were measured on 40,800 runs; (c) is now ruled; **what
is left is the remedy — that is ruling 6.** ~~and it is the next thing I owe you.~~ Answering 5 discharged
the "never ask 6 before 5" constraint, **and ruling 6 was then put and answered the same day.**

---

✅ **Ruling 6 answered 2026-08-13 — the remedy is: DIVIDE BY THE SIMULATED AREA.** Per-building EUI is to
be published against the multiplier-aware floor area **EnergyPlus actually simulated**, read per run from
`eplusout.eio`, instead of `footprint_area_m2 × levels`.

🟩 **This is the cheap one, and the reason is that the measurement already exists.**
`e02_simulated_floor_area.csv` holds all **40,800** rows, **0 parse failures**, **0 unmatched in both
directions in every one of the five modes**. So the remedy is a **denominator swap in the reporting
layer** — **no re-simulation, no cluster work, no `.idf` change.**

🔴 **Two things this ruling does NOT do, stated so they are never over-read.** It does **not** make
`building` mode simulate the right building — that mode still builds **one storey**, so after the swap its
EUI means *energy per **simulated** m²*, which for a multi-storey building is **not the real building's
area**. The number becomes **internally consistent, not physically representative**, and any document
using it must say which of the two it means. And it does **not** move the fleet: **157.1 kWh/m² pooled is
unchanged**, because `auto` — the adopted baseline's mode — already measured **1.0000 median / 99.63%
within ±1%**. Fixing the simulation itself was offered and not taken; **that door is not closed**, it was
priced (it would supersede every result those modes ever produced) and deferred.

⚠️ **OPEN-01 still does not close — but the reason has changed.** It is no longer waiting on you. It now
needs **a plan doc for the swap and a before/after per-building comparison across all five modes**, and
**that plan is not yet written.** It is the largest single piece of unstarted work this arc owns.

✅ **OPEN-01 CLOSED 2026-08-17 — `PLAN_open-49-and-open-01-2026-08-13.md` T05–T08 landed all three
things ruling 6 asked for.** The swap: `openubem/results/parser.py`/`aggregator.py` now divide by the
multiplier-aware simulated area from `eplusout.eio` (fallback to `footprint_area_m2 × levels` when
that file is missing or malformed, never a crash, always recorded which was used). Tested: 7 new
tests, non-vacuous. Measured on all five modes, 40,800 rows — every one of the audit's own targets
reproduced exactly: `auto` 1.0000/99.63%, `floor` 1.0000/98.43%, `fast_zone` 1.0000/94.80%,
`layout_assign` 0.9999/15.37%, `building` 0.5000/39.94%. **`157.1 kWh/m²` pooled is unchanged** —
`auto`'s error factor was already ≈1.0000. `building` mode is now internally consistent with what it
simulated, not physically representative of the real multi-storey building — a code comment says so at
the site that matters. Full record: `extra/MEASUREMENT_open-01_denominator-swap.md`, register
§OPEN-01.
> **OPEN-49 does not close alongside it.** Its remedy (per-building seed, fixed bounds) landed the same
> plan (T02–T03) and widened to **eight fields, not one** (four PDE columns + four setpoints, all
> carrying the identical present-archetype-bounds defect) — but closure still needs the third fleet
> re-run to reproduce `157.1` end to end, and ruling 4 explicitly declined that run. OPEN-49 is
> **mechanism fixed, closure blocked**, not open on an unknown cause and not closed on an unverified
> headline.

🟩 **Five more items now in execution — `openings/implemenation/previous/PLAN_five-items-2026-08-13.md`.** Chosen
on your instruction: **OPEN-50, OPEN-44 (which carries OPEN-13's residual), OPEN-45, OPEN-36, OPEN-26.**
One theme: **the test suite and this project's own completion records currently assert things that are
not true** — 45 red tests containing **zero real defects**, a fixture the suite silently rewrites, a
one-space matcher bug found three times, and a signed completion record for code that was never
committed. **None of the five can move a published number**, which is why they are safe to run together.
The executor is explicitly forbidden from making any red test green by building the thing it asks for —
that would enact OPEN-17, which is your decision.

✅ **CP-1 of that plan is signed 2026-08-13 — the suite is green for the first time.**
**26 failed · 1,859 passed · 10 skipped · 19 errors → 0 failed · 1,859 passed · 55 skipped · 0 errors.**
**OPEN-50 is fixed** (a full 24-minute suite run left the fixture's hash *and* mtime unmoved — measured
either side of the run, not taken on report) and **OPEN-44 is resolved**, which also discharges
**OPEN-13's** collection residual.

🔴 **Read the green with the rider attached: a skip is a debt, not a fix.** Nothing was repaired and no
feature was built — **the suite is now honest, not more capable.** 31 of the 45 skip because an artifact
is missing on this machine; **14 skip because a feature was never shipped, and shipping it is OPEN-17 —
still yours.** The one number that proves nothing was smuggled out: **passed stayed at 1,859**, so no test
was deleted or quietly downgraded into a skip. I verified the 45 node-for-node against the triage CSV with
an independent AST walk (5/5, 9/9, 5/5, 8/8, 18/18, zero either way) and read the whole diff — **none of
the four OPEN-17 symbols appears anywhere, and nothing under `openubem/` was touched.**

🔴 **ONE ACTION IS YOURS, and it is small: please discard `tests/fixtures/synthetic_30_archetype_coverage.gpkg`
in the working copy** (`git restore` that path). It is dirty from a run made *before* the fix. Neither I
nor my executors may run git write commands, so it will sit there until you clear it — and if it is
committed, the exact churn OPEN-50 exists to stop gets recorded one last time. **The rewrite already in
commit `6aeebb0` is history and is not being touched.**

~~🟩 **T02b + T03–T05 are now in execution**~~ ✅ **CP-2 SIGNED 2026-08-13 — THE PLAN IS CLOSED AND ALL
FIVE ITEMS ARE CLOSED.** Final suite, run by me rather than taken on report: **`1860 passed, 55 skipped,
11 warnings in 1487.81s`, exit 0** — 0 failed, 0 errors, +1 passed from the coverage split, skips unchanged.
**OPEN-50's fix held across a second full run** (hash and mtime still unmoved after 49 cumulative minutes of
testing). **Register: 34 tracked items → 29** — the biggest single-pass reduction this arc has made, and
the table was re-counted programmatically rather than asserted (**29 live rows, 20 struck**).

**What the other three did.** **OPEN-45** — sweep re-run, **zero live defects, no code changed**; the only
single-space literal left under `openubem/` sits inside `err_parse.py`'s own docstring describing the bug.
**OPEN-26** — both will-not-fix survivors re-verified at HEAD; `compute_form_factor` is called from nothing
but its own test, and the bbox recomputation costs CPU, not correctness. **OPEN-36** — you ruled the
correction goes into the record, so a dated banner now sits in the frozen
`IMPLEMENTATION_phaseC_ml_imputer.md` with the false half struck rather than rewritten. **The sharper
finding is that the record is not wholly false: the 53 tests really did ship; the implementation never
did.** That is the first time this project has annotated a frozen record.

🔴 **Three debts survive these closures — I am flagging them because retiring an ID is not the same as
finishing the work.** (1) **OPEN-17 is untouched and now blocks 14 skipped tests**, each naming it. (2) The
**`git restore`** above is still yours. (3) **OPEN-36's sweep was deliberately partial** — `T09b` and
`T11.8`/`T11.8b` were not re-verified, and if governance records matter beyond T07 that is a new item.

⚠️ **A defect I found in the register while re-counting and did NOT repair blind: the OPEN-46 row has 8
table columns instead of 6** and will render wrong. Pre-existing, unrelated to today's edits, recorded so
it is not inherited silently.

---

✅ **Ruling `2a` taken AND executed 2026-08-13 — OPEN-22 is closed and the board holds no unexecuted
ruling.** The user chose **option (b): keep the old gate, add a second one.** `test_fine_top1` stays at
**≥0.70 against the old 50-row fixture, untouched** (line 1049, quoted and verified); a **separate**
`TestTagRichTop1Accuracy` now gates `tests/fixtures/labelled_archetypes_tagrich_v2.csv` at **≥0.80**,
measuring **88.8% on 98 graded rows** — **8.8 points of headroom** (91.6% excluding fallback;
size-guessing 34.0% → 3.1%). `133 passed, no failures, no skips`.
Plan: `openings/implemenation/previous/PLAN_open22-tagrich-gate-2026-08-13.md` (CP-1 signed).
Evidence: `openings/extra/FIX_open-22_tagrich-gate.md`.
**Register: 35 tracked items → 34.**

🔴 **How this one was audited, because it is the reason to trust the number.** The gate was re-derived
**two independent ways** — the pytest assertion and `scripts/analysis/open22_grade_tagrich_fixture.py` —
agreeing to four decimals, with the grader's own precondition (old fixture still 44/50 = 88.0%)
reproducing first. **The gate was then proved non-vacuous by hand**: threshold raised to 0.95, watched to
fail, restored to 0.80. **A gate that cannot fail is not a gate**, and nothing here was accepted on a
report's say-so.

✅ **The full test suite was also reconciled node-for-node.** Scoped exactly as OPEN-44's own measurement
(`pytest tests/ --ignore=docs`, 18m22s): **26 failed, 1859 passed, 10 skipped, 19 errors** → **26 + 19 =
45**, and the failing **nodeids are identical to OPEN-44's triage CSV, node-for-node**. Passed rose
1857 → **1859 — exactly the two new tests. None of the 45 red nodes touch the classifier tests.**

⚠️ **One thing worth your attention that nobody asked for: coarse accuracy on the tag-rich fixture is
98/98 = 100% while fine is 88.8%** — meaning **all 11 errors are within the correct coarse class.** The
classifier never confuses an office with a warehouse; it picks the wrong office. **That is OPEN-47's next
measurement**, and it is also an argument against ever adding a coarse gate to this fixture, since any
plausible threshold would detect nothing.

🔴 **One correction to my own reporting, since it was on this page.** I earlier recorded here that the
executor had **stalled**. **It had not** — it was inside the 18-minute suite run above, which emits
nothing for its whole duration, and I misread silence as failure. Retracted here and in the plan log and
director prompt. It changed no number and cost no work, because the audit re-derived everything from raw
artifacts rather than waiting on the report — **which is the part of the process that should stay.**

---

✅ **Five more items swept 2026-08-13 (later) — `openings/implemenation/previous/PLAN_five-more-items-2026-08-13.md`, T01–T05, CP-1 and CP-2 both signed.**
**Closed and retired: OPEN-24, OPEN-32.** **Opened by the audit: OPEN-51, OPEN-52.**
**Register: 29 tracked items → 29.** *(The count is flat and that is the honest reading — this pass
closed two and found two. Re-counted programmatically: **29 live rows, 23 struck = 52, exactly
OPEN-01…OPEN-52**, none missing, none duplicated. The previous header's "20 struck" was a prose
miscount; the table itself was complete at 21.)*

| Item | Outcome |
|---|---|
| **OPEN-24** — live EnergyPlus gate | 🟢 **CLOSED. The gate was never parked — it had simply never been run on this machine.** EnergyPlus **23.1.0-87ed9199d4** is installed locally; **7 passed** in four sequential director runs (66.38 / 65.99 / 66.57 / 66.68 s); no test needs the network. An eight-week-old *blocked* status came from an assumption nobody had tested. |
| **OPEN-32** — net of the two opposing `layout_assign` errors | 🟢 **CLOSED. They do not cancel.** Net ≈ **1.12 at the median**, and **only 12.6% of buildings fall within ±10% of cancellation**; per-building net spans **0.0032 – 19.88** on n=8,153. |
| **OPEN-13** | Still open (E-UTCI-12 residual), but its carried-forward weakness is **discharged**: the fusion guard now derives its column set from the fetcher, pinned by a test proved non-vacuous by mutation. |
| **OPEN-27** | Still open — **only the user can edit DESIGN.** Now pinned meanwhile by 3 tests binding the coarse-class archetype names to the archetype JSON, so drift fails a test instead of going unnoticed. |
| **OPEN-29** | Still open. All eight forwarded defect IDs re-checked at HEAD: **all eight STILL-OPEN, no verdict changed.** The remaining measurement is **cluster-only** — now established rather than assumed. |

🔴 **The one number to take from OPEN-32: quote the deciles, never the median.** The error ratio's
deciles are **[0.316, 0.474, 1.000, 1.999, 4.000]** — powers of two, i.e. multiplier/storey arithmetic,
not continuous area error. The distribution is log-symmetric (44% above 1, 56% below), so **a median
near 1.0 would read as "they cancel" when the population is in fact split between ×2 and ×0.5.**

**The whole-tree suite, run alone, 21 minutes: `1910 passed, 35 failed, 55 skipped, 17 errors`.**
🟢 **Zero failures and zero errors under `tests/`** — nothing this arc touched is red, and OPEN-44's
`tests/`-scoped closure holds. All 52 non-passing results reduce to **two** causes: **51** are one
missing IDF template inside the **archived** elevators copy under `docs/docs_DONE/`, and **1** is the
`zones_found` `NameError` at `scripts/analysis/test_viewer_layout_assign.py:24` that OPEN-44 catalogued
on 2026-08-12 and nobody has fixed since.

🔴 **This changes what item 2c is worth doing.** The 30 stray `.py` files under `docs/` have been carried
as a tidiness item against the *no `.py` under `docs/`, ever* rule. **They are not tidiness — they put
51 red results into every whole-tree run**, which is exactly the noise floor a real regression hides
under. A suite permanently red by 52 cannot be used as a gate by anyone who has not first memorised
which 52. **Deleting the strays buys back the signal; leaving them costs it every run.**

⚠️ **One near-miss, recorded because it was luck, not design.** An executor ran a **tree-wide `git
stash`** to isolate a baseline and swept up two other arcs' uncommitted work; the `pop` then aborted on
a `.gpkg` conflict. **Nothing was lost** — both dropped stashes were still reachable via `git fsck
--unreachable`, and all 21 files diffed clean against the live tree except the known generated-binary
fixture. `git stash` is now named in the director prompt's *Never* list with the reason attached, and
goes into every brief.

⚠️ **One failure I caused and the executor was blamed for.** A "failing test" in T03 was my own parallel
dispatch: `pyproject.toml:54` pins `addopts = "--basetemp=.pytest_tmp"` at a fixed repo-relative path,
so **two concurrent pytest sessions delete each other's temporary directories.** The executor's report
was accurate; my dispatch was not safe. Opened as **OPEN-52**.

**Still owed by the user, unchanged by this pass:** `git restore
tests/fixtures/synthetic_30_archetype_coverage.gpkg` (generated-binary dirt); the **OPEN-17** ruling,
which alone blocks 14 skipped tests; and rulings **7 (CP-M2)** and **8 (OPEN-11)**.

---

**Amendment 2026-08-05 — OPEN-28 added.** Cross-mode comparisons mix two harvest generations
(`layout_assign` = T20; the other four modes = T08, never re-run). Found while auditing the
`layout_assign` documentation surfacing plan; it had existed only as a figure caption. **It bundles
with OPEN-01 and OPEN-02 — one fleet re-run retaining `eplusout.eio` closes all three, gated on a
disk-budget check, not a code change.**

**Amendment 2026-08-05 (measurement pass).** Five Phase-1 measurements (M01–M05) re-verified
OPEN-01/02/03/04/08/28. **CP-M1:** `.eio` retention approved in principle — median 76,068 B/run,
worst-case five-mode fleet pass ~43–45 GB against 8.1 TB free. OPEN-04's Phase-D suspicion is
**falsified** by bisect; real cause is E-R3-3 (commit `67ede73`). OPEN-28's `layout_assign`-is-T20
framing is corrected for the published −29.1% figure specifically — that figure's `layout_assign`
side is T19, not T20. Three new items opened by the measurements themselves: **OPEN-30** (vintage
never persisted by any harvest), **OPEN-31** (ratified classification changes lack a before/after on
the labelled fixture — CP-M3 decision owed), **OPEN-32** (OPEN-01 and OPEN-03's errors oppose each
other; net effect on `layout_assign` EUI unmeasured). Full detail:
`INVESTIGATION_open-items-register.md` §2.

**Nothing in this arc is scheduled, assigned, or costed.** The next step is a user selection.

---

**Amendment 2026-08-18 — `PLAN_five-items-2026-08-18.md`, T01–T06 complete.** Three items closed and
retired, two sharpened (stay open), one new item opened.

| Item | Outcome |
|---|---|
| **OPEN-06** | 🟢 **CLOSED.** Commit `67ede73` (2026-07-01) reproduces the committed `05_results.gpkg` archetype exactly for all 41 mislabelled buildings — the Hotel rule read `function_tag` only until a later commit added a `building_tag` check; the T11 fan-out that produced the committed file ran between the two commits. Resolves N07's open provenance gap. |
| **OPEN-37** | 🟢 **CLOSED.** All five remaining `.eio` fetch sites fixed (one line each); all ten fetch sites now request `.eio`. Local E02 census: 40,800/40,800 building dirs, `.eio` and `.err`, zero empty. The `.sql`/`.end` shortfall found by the same census is a different defect, out of scope — opened separately as **OPEN-53**. |
| **OPEN-51** | 🟢 **CLOSED.** `E-LA-16` adjudicated: it names the cooling-coil-design-UA/cooling-tower-UA-autosize family, not `CheckWarmupConvergence`. The live code comment was wrong and is corrected. Knock-on: OPEN-09's C06 "five inherited log entries" narrows to four. |
| **OPEN-52** | 🔴 **STAYS OPEN, sharpened to two sub-questions.** (a) The concurrent-pytest `--basetemp` collision is reproduced and real. (b) A second, newly-found OS-level lockout on `%LOCALAPPDATA%\Temp\pytest-of-o_iseri` blocks (a)'s specified remedy (deleting `addopts` gives `1 passed, 6 errors` on this machine). Choosing a remedy shape (ACL repair vs. a different remedy) is an **owed user ruling**, not a next measurement. |
| **OPEN-42** | 🔴 **STAYS OPEN, sharpened.** `eplusout.eio` was read for the first time: 15/16 fatal zones are on the topmost floor, geometry byte-identical to non-fatal siblings below. A required 20-building background control disproved two candidate distinguishing statistics. Verdict: not determinable from `eplusout.eio` — the next step needs a different artifact. |
| **OPEN-53** *(new)* | 🔴 **OPENED.** 874/875 E02 harvest directories are missing `.sql`/`.end` despite carrying `.eio`/`.err` — an incomplete-simulation signature, concentrated in `austin_suburban_fast_zone`/`austin_suburban_floor` (874) plus one `nyc_centre_fast_zone` directory. Cause untraced. |

**Register: 28 tracked items → 26** (three closed and retired, one opened). **Table re-counted
programmatically: 26 live / 27 struck / 53 total, exactly OPEN-01…OPEN-53, no row missing, none
duplicated. Twenty-five IDs retired in all** (22 going in + OPEN-06/OPEN-37/OPEN-51 this pass).
**Next free item ID: OPEN-54.**

**Full suite, run alone:** see the plan doc's T06 progress-log entry
(`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-18.md` §8) for the raw counts
against the 1875/55/0 baseline.

Full detail: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`.

---

**Amendment 2026-08-18 (evening) — `PLAN_four-items-2026-08-18.md`, T01–T05 complete.** One item closed
and retired, two sharpened (stay open, reframed/narrowed), one confirmed via director ruling.

| Item | Outcome |
|---|---|
| **OPEN-46** | 🟢 **CLOSED + ID RETIRED.** The item's stated blocker was stale — `builder.py` has wired `assign_elevators` since 2026-08-13. All four elevator-reporting links (load → meter → parse/de-fold → carbon/aggregator) verified at HEAD by file:line citation and by passing tests: 65/65 targeted tests, full suite `1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)` matching the 1875/55/0/0 baseline. One documentary defect found and corrected: the plan-named proof test (`test_medium_office_idf_contains_elevator_equipment`) does not exist in the live tree and never has — `tests/test_builder_elevators_wired.py` (already committed) proves the same fact and passes. |
| **OPEN-38** | 🔴 **STAYS OPEN. Director ruling: T04's recommendation accepted — stays a separate item from OPEN-42.** Every measured axis disagreed (Severe message class, temperature range, zone position, geometry origin, mode). |
| **OPEN-42** | 🔴 **STAYS OPEN, REFRAMED (director ruling).** The question is no longer "which zone is inverted" but "what is wrong with the topmost-storey geometry of these six buildings such that any zone built from it runs away." Zoning mode only decides whether the topmost storey gets a zone at all — `building` and `layout_assign`, the two modes that never fatal, are exactly the two that never zone that storey. Both `.eio` and `.err` are now exhausted for this question; the E02 IDF corpus that could answer it no longer exists on disk. No local next step named. |
| **OPEN-53** | 🔴 **STAYS OPEN, NARROWED (director ruling).** The original question — why the `.sql`/`.end` are missing — is answered: the files were produced, harvested and inventoried on 2026-08-11, then deleted by a process outside this repository at 2026-08-17 16:21, which also emptied the entire E02 IDF corpus. No published number is affected. What keeps it open is the custody risk, not the original question — nothing prevents recurrence, and `e02_corpus_inventory.csv` (2026-08-11) is now annotated as a snapshot, not current state, falsified by disk for two rows. |

**Register: 26 tracked items → 25** (one closed and retired). Table re-counted programmatically:
**25 live / 28 struck / 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated. Twenty-six
IDs retired in all** (25 going in + OPEN-46 this pass). Struck-vs-retired difference unchanged at
**exactly 2** (OPEN-02, OPEN-28). **Next free item ID: OPEN-54** (unchanged — no new item opened this
pass).

**Full suite, run alone (T01/A1, foreground):** `1875 passed, 55 skipped, 11 warnings in 1572.28s (0:26:12)`.

Full detail: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`;
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-items-2026-08-18.md` §8.

---

**Amendment 2026-08-18 (night) — `PLAN_open-52-and-four-items-2026-08-18.md`, T01–T06 complete.** One
item closed and retired, four measured and narrowed. The user delegated ruling `3a` to the director;
it was given, implemented and verified.

| Item | Outcome |
|---|---|
| **OPEN-52** | 🟢 **CLOSED + ID RETIRED.** Ruling `3a` answered: `addopts = "--basetemp=.pytest_tmp"` deleted, a repo-root `conftest.py` now sets `PYTEST_DEBUG_TEMPROOT` to `<repo>/.pytest_tmp`, so pytest numbers each session instead of clearing one shared root. Derived from pytest 9.0.3's source — the `--basetemp` branch calls `rm_rf(basetemp)` unconditionally at session start, which *is* the collision. Four verifications passed with real output, including a negative control that reproduced the original failure on the old config and a two-session test that landed in distinct `pytest-0`/`pytest-1` directories. 🔴 **Hand-off: the fix is an ~~uncommitted working-tree change (`conftest.py` untracked, `pyproject.toml` modified) — until both are committed, a fresh clone reproduces the item.~~** 🟢 **DISCHARGED 2026-08-18 (night): committed as `da6eed7` and pushed to `origin/main` (github.com/orcunkoraliseri/OpenUBEM), at the user's explicit instruction (*"tu fais aussi a toi-meme … pour open-52"*), which suspended the arc's standing git prohibition for this one commit. A fresh clone no longer reproduces the item.** |
| **OPEN-07** | 🔴 **STAYS OPEN, narrowed.** The "no IDF survives to diff" blocker is false — four survive under `scratchpad/`, covering 2 of 3 buildings in both classifications. The A side is the raw `SmallHotel` DOE prototype dropped in wholesale (67 zones / 485 surfaces / 106 subsurfaces, identical to the prototype's own counts) rather than an OSM extrusion; B is 6 / 43 / 23. Multipliers uniformly 1.0 on both sides — the multiplier-scaling hypothesis is refuted. |
| **OPEN-38** *(sub-question)* | 🔴 **Subsurface sub-question REFUTED, not merely unmeasured.** The three `CHKSBS` warnings sit on `RearStairs`, `Corridor` and `FrontStairs` — never on `LaundryRoomFlr1`, the zone that carries the Severe and kills the run. Every flagged door is 0.0000 m from its wall's plane and strictly inside it, with zero duplicate surface names. Unfitted subsurfaces are not this item's mechanism. |
| **OPEN-08** | 🔴 **STAYS OPEN, narrowed to 1 of 5 cells.** The "no harvest persists `vintage_standard`" blocker went stale when OPEN-30 closed. Vintage is measurable on 738 of 4,530 shared buildings (16.3%) — the other four cells' prior-generation file carries a stripped 21-column schema, a schema gap not a data gap. 🔴 **Director's correction to the executor's headline:** 3.79% vintage was compared against 13.40% archetype, which is a different population *and* generation pair. On the same 738 rows and same pair, archetype disagrees **50.54%** — so vintage is ~13x *more* stable than archetype, the opposite of the reported reading. OPEN-08's weight sits almost entirely in its archetype half; the vintage half is non-zero and data-poor-skewed (3.93% vs 0.00%). |
| **OPEN-29** | 🔴 **STAYS OPEN. 8 of 12 still open, was 9.** E-LA-21 moves to CLOSED-ELSEWHERE — its one-space `has_fatal` literal is gone from every code path, confirmed live at **eight** harvest sites (director-corrected from the executor's seven). 🔴 **A director lead was refuted:** the plan asserted E-LA-16 had closed via OPEN-51; OPEN-51 only adjudicated *which defect the ID names*, and the defect itself is unpatched. E-LA-16 stays open. |
| **OPEN-53** | 🔴 **STAYS OPEN by ruling, as a standing custody risk.** Both consequences discharged — `e02_corpus_inventory.csv` annotated by sidecar (its bytes untouched; no code reads it) and the two falsified `austin_suburban` rows re-verified live (inventory `n_end=437`, disk 0, directories intact at 437; the `auto` sibling returns 437/437 on the same disk, so the zero is real). A binding planning rule and an explicit closure condition are now recorded in the item. |

**Register: 25 tracked items → 24** (one closed and retired). Re-counted programmatically: **24 live /
29 struck / 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated. Twenty-seven IDs
retired in all.** Struck-vs-retired difference unchanged at **exactly 2** (OPEN-02, OPEN-28).
**Next free item ID: OPEN-54** (unchanged — no new item opened this pass).

**Full suite, run alone (T06, foreground):** `1875 passed, 55 skipped, 11 warnings in 1035.59s (0:17:15)`

Full detail: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`;
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-52-and-four-items-2026-08-18.md` §8;
director's log `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` §5.20.

---

**Amendment 2026-08-18 (late) — `PLAN_open-48-and-four-items-2026-08-18.md`, T01–T06 complete.**
🔴 **Zero items closed, and that is the correct outcome.** Four items whose register entries asserted
facts about the live tree were re-derived; **all four premises were false and all four items stay
open.** Correcting a record is not closing an item.

| Item | Outcome |
|---|---|
| **OPEN-48** | 🔴 **STAYS OPEN. All five rows of its evidence table were false** and are struck in place. At HEAD: `builder.py:40` imports `assign_elevators`, `:609` calls it, `outputs.py:43` carries the meter, `HVAC_METERS` = 14 not 13, both result columns present, and a live standalone `BuildingIDF.build()` emits 1 elevator object for LargeOffice/12-level and 0 for a SmallOffice/1-level control. **Reason re-shaped: the gap is no longer "code is missing" — it is "no post-fix fleet re-run exists." Authorising a third fleet run is a ruling owed to you, and is now the largest blocker on the register.** |
| **OPEN-47** | 🔴 **STAYS OPEN on Reason 2 alone.** Reason 1 — "the floor-count divergence is Not adjudicated" — was stale: **you ruled on it 2026-08-12** and the reasoning is in `building_classifier.py:167-189`. Every number in that ruling reproduces exactly on a freshly written script (598 changes, 380/161/57, 437 newly elevator-eligible, sources 85/346/167). What keeps it open is the citation half: a second fabricated DOI, a systemic wrong-locator pattern, two dead links. |
| **OPEN-13** | 🔴 **STAYS OPEN, narrowed to nothing of its own.** Its claim that a bare `pytest` aborts at collection is false at HEAD by two independent mechanisms. All ten skips (corrected from nine) are future-feature pinning for OPEN-17, not lost production coverage. |
| **OPEN-12** | 🔴 **STAYS OPEN; the six-week contradiction is explained.** Both original figures reproduce exactly on the UTCI arc's own untracked working copy; the fleet's tracked files really are 100% missing. **Two correct numbers describing two different populations — no reconciliation is owed.** |
| **OPEN-48 — superseded 2026-08-18 (late)** | 🟢 **The third fleet run was authorised by you and has run. The blocker above is discharged.** Full result: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-48_third-fleet-run.md`. **Answer: the OPEN-49 fix is worth nothing outside noise on classified buildings — under 0.08 %** (Unknown-free cells `la_rural` −0.0906 and `austin_urban` −0.0614; +0.0004 / +0.0001 / −0.0001 on three cells with Unknowns excluded). Every classified building changed value and no cell mean moved. 🔴 **CP-2 ruled: run 3 yields NO fleet figure** — five of twelve cells stopped on a defect the run itself found (**OPEN-55**, Unknown buildings drawing data-centre equipment loads up to 5381.96 W/m²), and four of the five passes passed *by dropping* exactly those buildings. 🔴 **CP-3 ruled: `157.1` STAYS** — OPEN-55 postdates it and nothing measured displaces it. ⚠️ **New, and it belongs beside the published figure:** run 2's Unknown path contributes **+4.058 kWh/m² (+2.615 %)** — 650 buildings, 3.7 % of floor area, mean EUI 264.9 vs fleet 159.2 — **nearly twice the +2.16 discrepancy this arc spent three fleet runs chasing.** Measured on run 2, **estimated** for the adopted run (whose per-building results are gone); **report it, never subtract it.** The run that could move 157.1 is one taken *after* the OPEN-55 ruling. |
| **OPEN-51** | ⚠️ **Already closed hours earlier — a director error in choosing the slate**, recorded in the register rather than buried. Re-run anyway, which **located the original `.err` evidence a previous closure had declared lost**; verdict unchanged, evidence grade upgraded. |

---

**Amendment 2026-08-18 (late, second pass) — `PLAN_ten-items-2026-08-18-late.md`, ten items selected, planned and executed.**
🔵 **Two items closed, one opened, and the one opened is the biggest thing here.** You asked for ten
open items to be chosen, planned and carried to the end. That was done. Five of the ten turned out to
be already answered — my selection error, recorded below rather than buried — and one of the remaining
five found a defect nobody had seen.

| Item | Outcome |
|---|---|
| 🔴 **OPEN-56 — NEW** | **Every building in the fleet simulates with a 10 m³ zone-volume stub.** EnergyPlus computes a **negative** air volume from the geometry we hand it (floors and ceilings wound the wrong way) and silently substitutes 10 m³. Measured at **8,160 / 8,160 — 100.00 %** of the twelve cells, re-confirmed in run 3. **Control: runs built from DOE-prototype geometry show 0 of 2**, so this is our geometry, not EnergyPlus. ⚠️ **This is NOT a claim that 157.1 is wrong** — infiltration is written per exterior-wall-area, not air-changes-per-hour, so it is not scaled by the stub, and the effect on annual EUI is **unmeasured and not assumed**. **What it needs first is a number, not a fix.** |
| ✅ **OPEN-42 — mechanism found** | The item has been open since 11 August on *why* six buildings blow up thermally. **Answer: nothing is wrong with those six.** Their fatal zone is identical to its non-fatal siblings in the same file on every measurable field, and the "always the topmost storey" rule the item relied on **fails in run 2 — 4 of 6, not 6 of 6.** They are the extreme tail of OPEN-56: failures average −6,096 m³ of computed volume against −683 m³ for successes. 🔴 **The ruling that closed this investigation said the artifact needed "no longer exists on disk". It did exist** — one run newer — and finding it took a directory listing. |
| ✅ **OPEN-48 — CLOSED, ID retired** | Its blocker was that no post-fix fleet re-run existed. One does now, and the fix it was testing measures **under 0.08 %**. Closes on a negative result, which is the honest closure. |
| ✅ **OPEN-54 — CLOSED, ID retired** | Remedy implemented and tested. `_ssh` now raises on a non-zero remote exit and on timeout; the poll loop no longer reads a failed `squeue` as "array complete" — completion needs `sacct` to corroborate. Nine local tests pass, **none of them touching the cluster**. ⚠️ Not yet exercised against the live cluster; the first real run through it should be watched. |
| 🟢 **OPEN-07 — closeable** | All three "regressed" buildings **succeed at HEAD**, 0 severe errors, on IDFs the item says do not exist. ⚠️ Caveat carried into the recommendation: the regression was seen in `layout_assign`, and this is the `auto`-family path. **Closure recommended, not taken — it is a scoping judgement, yours.** |
| 🟢 **OPEN-11 — remedy invalidated** | Its six are **exactly** OPEN-42's six, predicted in writing before measuring. Its remedy is a six-building patch for a defect now measured in all 8,160. **Folds into OPEN-56 or closes against it — recommended, not applied.** |
| ⚠️ **OPEN-38 / 53 / 29 / 13 / 12 — already done** | All five had a completed measurement in `openings/extra/`, four of them dated the same day. **I picked them off the register's summary rows, which still carried the original "not yet measured" framing with the answer recorded further down.** Cost: about half the pass. 🔵 **It exposes a real hygiene problem worth more than the wasted effort: the register's summary table is not a reliable index of what has already been measured.** |

---

**Amendment 2026-08-18 (overnight) — `PLAN_ten-items-2026-08-18-overnight.md`, ten items, all ten done.**
You asked for ten different open tasks while you slept, with this checklist and the director prompt
kept current. All ten landed. **This was the first batch where every live item already had a first
measurement**, so each was picked by what its *own entry* names as the next unanswered question — six
of the ten are questions the register itself writes down as *"the next thing on this item."*

| Task | Outcome |
|---|---|
| ✅ **The room-volume cost, now measured on the whole fleet** | Last night's figure came from ten rural bungalows. This time: **69 buildings across all twelve cells**, every check clean (the tell-tale warning in **70 of 70** untreated runs, **0 of 70** treated, all 140 runs finished). **The fault makes buildings look 0.98 % cheaper on average — about 1 kWh/m² each — and 65 of 69 move the same way.** Slightly larger than the rural estimate, same direction. **I have not applied it to the published 157.1**, and it does not need restating. |
| 🔴 **And my own prediction was half wrong** | I wrote down beforehand that the cost would grow with the number of rooms in a building. **It does not** — the correlation is 0.11, essentially nothing. It is a **flat ≈1 kWh/m² per building**, whatever its size. Last night's "per-room effect" reading was reasonable on ten buildings and is wrong on sixty-nine. |
| 🔵 **Two problems that looked like one are two** | Writing the correct room volume fixes the six failing buildings — but it leaves the separate *non-convergence* warnings **completely untouched** (150 before, 150 after, unchanged on every building). **They are two independent faults that happen to hit the same 16 buildings.** Fixing one will not fix the other, and merging them would have been a mistake. |
| ✅ **A figure declared un-reproducible, reproduced exactly** | A count of **90 buildings** has been quoted since early August; a previous check said reproducing it was out of scope and did not try. I ran it: **90 — and the same 66/24 split.** New with it: that fix would help **90 of 1,992 affected buildings, i.e. 4.5 %.** The other 95.5 % it cannot touch at all. |
| ✅ **A blocker that was stale for the third time** | One item has been stuck since 5 August on *"the data we would need no longer exists."* **It does exist** — last week's sweep deleted the big files but left the small ones. The measurement it was waiting for now reads **3 buildings in 8,160 (0.04 %)**, with a control at exactly 0. |
| 🔴 **A big-looking number that must not be quoted** | The 2,611 buildings with no storey data appear to use **48 % more energy** than the rest. **That is an illusion of mixing.** One neighbourhood supplies 1,589 of them and has nothing to compare against; **within neighbourhoods the direction is not even consistent** — four go up, four go down. The real answer needs the same kind of experiment I ran for the room-volume fault. |
| ✅ **An old question about map data, settled** | The external-height source has **never once been used** — zero uses across 8,160 buildings, *including the one neighbourhood where we actually have the data file*. So the missing files were never the real obstacle; a switch in the settings closes the door first. |
| 🔵 **Eight inherited defects, finally decidable** | Four of them (**E-LA-15, E-LA-18, E-LA-19, E-LA-30**) leave **no trace anywhere in 8,160 buildings**; a fifth is down to a single building. One (**E-LA-17**) turns out to be an existing item under another name — adopting it would count the same thing twice. **This is the material you need to say adopt or retire, and I have not decided for you.** |
| ⚠️ **How exposed the evidence is, in gigabytes** | The simulation archives this work rests on are **152 GB, and 95 % of that is one file type** — the same type last week's sweep deleted elsewhere. **The part actually cited is under 0.12 GB.** Nothing was moved or deleted; this is a note, not an action. |

⚠️ **Two mistakes of mine, caught before anything was reported, and recorded rather than quietly
fixed.** (1) The first version of one measurement dropped a column and produced a number **ten times
too large**; a missing row in its own summary table gave it away. (2) The fleet run put 140 jobs
through six parallel workers and **ten produced empty output**, which reads as failure — run one at a
time the same file finishes in 18 seconds. Both were corrected and re-run before any figure left the
task.

**No item was closed this pass and the count is unchanged.** Recommended closures now stand at
**four**, all left to you: **OPEN-42**, **OPEN-11**, **OPEN-07**, and now **OPEN-08**.

🔴 **Still waiting on you, unchanged since yesterday afternoon:** the **OPEN-55** ruling
(`extra/PROPOSAL_open-55_unknown-pde-bounds.md` §10). Nothing is patched until it comes.

**Register: 25 tracked items → 25** (nothing closed, nothing opened). Re-counted programmatically:
**25 live / 31 struck / 56 total, exactly OPEN-01…OPEN-56, no row missing, none duplicated. Next free
`OPEN-57`.** Struck-vs-retired difference unchanged at **exactly 2** (OPEN-02, OPEN-28).
Full record: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_ten-items-2026-08-18-overnight.md`.

---

**Amendment 2026-08-18 (night) — `PLAN_ten-tasks-2026-08-18-night.md`, ten tasks, all ten done.**
🔵 **The zone-volume defect found this evening is now proved, and it is fixable by writing one
number.** You asked for ten more open tasks chosen, planned and executed, with the director prompt
kept current for tomorrow. All ten landed.

| Task | Outcome |
|---|---|
| 🔵 **OPEN-56 — proved** | I wrote **one field** — the room's air volume — into a copy of each building's input file and re-ran EnergyPlus locally. **All six buildings that have been failing since 11 August now finish successfully with zero errors** (they had 9 to 39 errors each). The check that makes this trustworthy: the tell-tale warning appears in **16 of 16** untreated runs and **0 of 16** treated ones. **This is an experiment with a control, not a pattern spotted in a log.** |
| 🔵 **What it costs — now a number** | On ten buildings that *did* run: **+0.75 % on average, +0.67 % typical, worst case +1.67 %.** Small. **But nine of the ten move the same way**, so the defect is a **bias, not noise — it makes buildings look slightly cheaper to run than they are.** ⚠️ **Ten buildings from two rural neighbourhoods is a bound and a direction, not a fleet figure**, and I have deliberately not multiplied it out into a correction to 157.1. **The published number does not need withdrawing or restating.** |
| ✅ **OPEN-42 — solved** | Its question was *what is wrong with those six buildings.* **Nothing is.** They are simply the six where a fleet-wide defect tips over — the ones with the largest rooms, and therefore the largest error. **Closure recommended, not taken.** |
| ✅ **Where the fault comes from** | **Not our code.** No part of OpenUBEM sets the floor/ceiling corner order; it comes from the third-party geometry library. 🔴 **We already have a check for exactly this and switched it off on purpose**, with a comment explaining that the signal is normal and checking it would raise false alarms. **That comment is why nobody looked for six weeks.** I have written the contradiction down rather than resolving it — resolving it means changing code. |
| ✅ **A fleet-wide error taxonomy, a first** | All 8,160 error files censused: **123 message families, 9 present in every single building.** One that looked alarming — 52,932 "meter not found" warnings — was **checked and cleared**: every building with lift energy has its lift meter, every building carrying the warning has no lifts. Correct behaviour, and it independently confirms the lift-reporting item we closed earlier. |
| 🔵 **OPEN-09 — half right** | Its concern was simulation non-convergence. Fleet-wide it affects **16 buildings in 8,160 — 0.20 %**, all in LA. **But all six of our failures are among those 16, and nothing outside them ever fails.** So "cosmetic" is true about how common it is and false about what it leads to. |
| ✅ **Two old figures re-checked, both exact** | 32.00 % of buildings have neither a storey count nor a height; 34.39 % have no height. Both were measured on a fleet whose files were deleted last week. **Both reproduce to the unit on a fleet that still exists and can be re-run** — which is what the file-custody item has been asking for. |

**No item was closed this pass and the count is unchanged.** Two closures are **recommended and left
to you**, because retiring an item by folding it into another is your call, not mine.

🔴 **One thing is still waiting on you and has been since this afternoon:** the **OPEN-55** ruling —
how wide the screen on unnamed buildings should be (`extra/PROPOSAL_open-55_unknown-pde-bounds.md`
§10). Nothing is patched until it comes.



**Register: 24 tracked items → 24** (nothing closed, nothing opened). Re-counted programmatically:
**24 live / 29 struck / 53 total, exactly OPEN-01…OPEN-53, no row missing, none duplicated. Twenty-seven
IDs retired in all.** Struck-vs-retired difference unchanged at **exactly 2** (OPEN-02, OPEN-28).
**Next free item ID: OPEN-54.**

**Full suite, run alone (T06, foreground, `-rs`):** `1875 passed, 55 skipped, 11 warnings in 1477.74s (0:24:37)`
**Skip census by file:** `tests/test_v19_national_cbecs_rescore.py` 18, `tests/test_draw_methods.py` 10, `tests/test_v19_basis_diagnostic.py` 8, `tests/test_debias.py` 5, `tests/test_impute_montage.py` 5, `tests/test_service_loads.py` 5, `tests/test_plotting_suite.py` 4.

🔴 **Two things now waiting on you, both decisions rather than work.** (a) **Whether to authorise a
third full fleet run** — this is the only thing left standing between the project and a reproducible
published number. (b) **Whether to archive two sets of evidence out of gitignored scratch**: the three
`E-LA-16` `.err` originals and the UTCI backfill dataset that is the only thing reproducing OPEN-12's
original percentages. Both sit in the space the standing corpus-erosion warning covers.

**🟢 The progress board is current again** — `https://claude.ai/code/artifact/0615b50a-75d6-49c6-a354-d4f2f74d3639`,
six days stale when you asked, now carrying 13–18 August. Keeping it current is a standing obligation
from now on.

Full detail: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`;
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open-48-and-four-items-2026-08-18.md` §8;
director's log `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` §5.21.


---

**Amendment 2026-08-19 — `PLAN_ten-items-2026-08-19.md`, ten tasks, nine done.**
🟢 **Your four approved closures are done, and the pass's biggest result is that two of the
items were describing the problem wrongly.** You asked for ten new tasks chosen, planned and executed
to the end, and you gave three rulings up front. Nine tasks landed. **One — the test that would
prove the OPEN-55 fix works — never ran, and I am not going to dress that up.**

| Task | Outcome |
|---|---|
| ✅ **Your ruling R1 — implemented** | The screen on unnamed buildings is in. An unidentified building can no longer draw a **data centre's** equipment load: the ceiling drops from **5,382 W/m² to 16.15**. Ten new tests; the full suite passes (1,885 tests). |
| ⛔ **… but it is UNPROVEN** | The test that checks it actually works on real simulations **has failed to run three times** — **zero buildings simulated**. Every attempt died at the same point: the first call out to the cluster. **Do not read this as "it works."** |
| 🔵 **OPEN-35 — the register was wrong about the size** | The item said ~**1,031** buildings are "chosen as a 19-storey building but built as one storey." A full census of all 1,031 says it is **11**. The other 1,020 get "1 storey" from *both* methods, so there is nothing to disagree about — mostly because two NYC cells have **no storey data at all** to take a median from. |
| 🔵 **… and the effect is not one-directional** | On those 11, correcting the storey count moves energy use **up on 7 and down on 4** — from **+40.5 % to −12.6 %**, splitting by climate. The task's own prediction was **wrong**, and it said so. Controls were clean: 10 untreated buildings moved by **exactly zero**. |
| ✅ **OPEN-12 vs OPEN-35 — not the same population** | The register implied these two might be the same buildings. They are not: one is a **strict subset** of the other. |
| ✅ **Four items closed — your ruling R2** | **OPEN-42** and **OPEN-11** fold into OPEN-56; **OPEN-07** and **OPEN-08** close on their own measurements. Each closure record names **what survives it**, so nothing is lost by closing. |
| ✅ **Evidence copied into the repo — your ruling R3** | **323 files, 12 MB** — about **8 %** of the space we budgeted — with a hash list. I re-checked 40 of them at random myself: all match. |
| ✅ **OPEN-47 — de-scoped by a clean negative** | The two untraced size thresholds explain almost none of the errors we were blaming them for. |
| ✅ **OPEN-38 — the blocker was stale** | "No input file survives" was true of the *old files*, not of our ability to rebuild them. Rebuilt and measured. Third time in two days a "blocked" item turned out not to be. |

🔴 **Two new problems opened, and both were found by accident — which is the pattern worth
noticing.** Neither came from a task that went looking for it.

- **OPEN-57 — the cluster connection intermittently breaks.** Same failure, same place, twice, on
  two different runs. It is the reason the OPEN-55 test has never run: each attempt does **3–4
  minutes of good work locally** (all 1,589 buildings prepared successfully) and then throws it away
  at the first call to the cluster. I stopped after the third attempt rather than trying a fourth.
  **The OPEN-55 test cannot be retried until this is fixed.**
- **OPEN-58 — a test helper script has two bugs.** It let two different buildings **overwrite each
  other's results**, and it calculated energy use by a formula that is **not the one production
  uses**. The task that found it **threw away its own completed results and re-ran them clean**
  rather than publishing them — so this pass's numbers are fine. 🔴 **What is not known is
  which *older* results used that same helper.** Nobody has checked. That check is the single most
  useful next thing to do.

**Register: 21 tracked items → 23.** Four closed (your R2), two opened. Re-counted programmatically
after every edit: **23 live / 35 struck / 58 total, exactly OPEN-01…OPEN-58, no row missing, none
duplicated. Next free item ID: OPEN-59.**

**Checkpoints: three of four signed.** CP-1, CP-3 and CP-4 signed on evidence I re-derived myself
rather than taking on the executor's word. **CP-2 cannot be signed** — the acceptance test did not
run. Its stop condition was never triggered (it gates on a *wrong* answer, not a *missing* one), so
the rest of the pass continued as designed and none of the other nine tasks depended on it.

🔴 **What is waiting on you:** whether to spend a pass on **OPEN-57** (the cluster connection)
so the OPEN-55 test can finally run, and whether to spend one on **OPEN-58's** blast radius — which
old results used the buggy helper. Both are registered; neither is scheduled.

Full detail: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`;
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-items-2026-08-19.md` §8;
director's log `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`.

---

## 2026-08-19 (later) — four items driven to the end

**The cluster connection is fixed, and it was never intermittent.** It was two separate faults
stacked on top of each other, and the second one is the interesting one.

- **Fault 1 — the command was simply too long.** Every building's name was packed into one line
  sent to the cluster, and past a certain length the machine at the other end could not read it at
  all. It is exactly reproducible: **565 names work, 566 do not.** Worth recording because it is
  tempting to round: the last failing size is **one byte under 8,192**, so the obvious "it's an 8k
  limit" explanation is wrong, and no round number fits. The content makes no difference — only
  the length.
- **Fault 2 — and this one nearly slipped through.** With the names moved out of the command, the
  check **still reported zero finished buildings, against a folder that was full**. That looks
  exactly like a folder that had been cleaned out, and it was very nearly written off as one. It
  was not: Windows silently adds an invisible extra character to the end of every line sent that
  way, so each building's name arrived slightly wrong and no file was ever found. **It returns a
  clean, believable, completely wrong answer**, and it would never happen on a Linux machine.
  🔴 Had we accepted the first explanation, we would have shipped a check that always says
  "nothing is finished".
- ✅ **Proved working on real data:** the fixed check now reports **225 of 226** for a real
  neighbourhood — the exact number already on record for it from months ago.

**The helper-script bug's reach is now measured, and the item's own description was wrong.**
Three scripts really used it. The problem is **not** that they share an output folder — they don't
— it is that they share the folder the simulator itself works in, which means **all three were
affected, not only ones running side by side.** An audit looking for the wrong thing would have
cleared two of them. **One genuinely corrupted result was found** out of 166 rechecked: one
building carrying another building's numbers, identical to fifteen digits. It had already been
thrown out, but for the wrong stated reason. ✅ **No published number is affected** — the wrong
energy formula moves absolute values, and every figure we quote from those runs is a percentage
change on the same building, which cancels it out.

**The storey-count disagreement is fixed — and the count of affected buildings was wrong.** It was
recorded as 11. It is **21**: the original count looked only at apartments, and ten hotel buildings
reach the same invented storey count by the identical route. The 11 are entirely inside the 21. A
broader fix that would have moved 509 buildings was rejected as a different change, not this one.
🔴 The fix was first landed **switched off** — correct code that nothing actually called — and
then wired into two of the three places that need it. Stopping there would have left the building
step and the reading step disagreeing about the same 21 buildings, which is the very fault being
fixed, moved somewhere new. All three now agree, with a test holding them together.

**The office size-threshold question is answered.** The source is real and verified. What was still
open is that the source's rule uses floor area **and** number of floors, and our code uses only
area. **598 buildings would be classified differently — and every one of them would move to a
larger office type. Not one moves smaller.** So the omission is not neutral. **167 of those 598
have no floor count at all**, which is why this must be sequenced after the storey fix, not before.

**Test suite green throughout, checked three times as the work landed** — 1,893 then 1,896 then **1,919 passed, 55 skipped, nothing failing**. The baseline before this pass was 1,885; the extra 34 are the new tests written for these fixes.

🔴 **What is waiting on you:**
1. **The 1,589-building test can finally run** — the thing that blocked it is fixed. I did not run
   it; that needs your go-ahead.
2. **Whether to restate the published fleet figure.** It was computed before the storey fix and is
   now out of date for 21 buildings. I have not restated it.
3. **Whether to adopt the source's full office rule**, or record our departure from it deliberately.
4. **Four closures I recommend but have not made:** the connection fault, and the four earlier
   items whose evidence is now complete.

**Register unchanged at 23 live / 58 total** — nothing was closed, because closing is your call.

---

## 2026-08-19 (late) — you said close them all; three are closed, one is running

**Three items are closed and their IDs retired. The open count drops 23 → 20.**

- **The cluster connection fault — closed.** The fix is landed and it was checked against reality,
  not against itself: it now reports **225 of 226** for a real neighbourhood, which is the exact
  number already on record for that neighbourhood from months ago.
- **"Defects the register never adopted" — closed.** Every defect it was carrying is now either
  owned by another item, harmless, or sitting behind a mode the real pipeline never uses.
  🔴 **I wrote the limit into the closure rather than leaving it implied: this does not say
  those defects are fixed.** Nobody has tested them. It says the register no longer needs a separate
  line for them. If that mode is ever revived, they come back first.
- **The office size thresholds — closed, and this one needed no work at all.** It is closed as a
  **deliberate, documented departure from the source**, which is one of the two endings the item
  itself offered. 🔴 **The decision was already yours, taken on 2026-08-12, and it is written
  word-for-word into the code it governs.** The item stayed on the list for a week only because
  nobody had written that decision up as a closure. Nothing was changed to close it.
  ⚠️ **The uncomfortable half is recorded too, not buried:** all 598 buildings that would move
  are promotions, and not one is a demotion — so our simpler rule makes offices **systematically
  smaller** than the source intends. That is accepted knowingly, on the grounds you gave in August:
  adding the floor test would make the building's type depend on a guessed storey count twice over,
  and **167 of those 598 have no real storey count at all.**

**The 1,589-building test is running now.** Its result is fixed in advance so it cannot be talked
into a pass: the failure count has to come in well below 71. ⚠️ **If it does not, that gets
reported as a failure and the item stays open.** If it passes, **two items close together** — they
are formally coupled and neither can close alone.

🔴 **Before the fleet figure is restated, one thing you should have in front of you.** The
restatement needs a full re-run of all twelve areas, because today's code differs from the code
behind the published figure in four ways, not just the 21 buildings. **But the 10 m³ volume defect
is still unfixed and it touches every building in the fleet**, at a measured **≈ +1.0 kWh/m² with a
known direction**. So any figure produced now is **knowably too low by about that much, and will
have to be restated a second time** once that defect is fixed. I am proceeding because you asked me
to, and the restatement will carry that warning on its face rather than read as a clean number.

---

## 2026-08-19 (night) — the test passed; two more closed, one new thing found

**The 1,589-building test ran and passed.** The number that had to come in well below 71 came in at
**zero**. Two items closed together on it — they were formally coupled and neither could close
alone. **Open count 20 → 19.**

🟢 **This one closed the right way, and it is worth saying why.** The pass condition was
written down *before* the test and could have failed. It did not. Everything else on the list this
week closed on judgement; this closed on evidence.

⚠️ **It took four attempts and the first three proved nothing** — each simulated zero
buildings and each was a retry of a fault nobody had diagnosed. An item can sit implemented, ruled
and completely unproven for a week.

🔴 **I checked the passing run myself rather than taking the result, and found something the
test was not looking for.** The fix worked — unidentified buildings now use *less* equipment
energy than identified ones. **But they still use 1.7× as much energy overall.** The excess did
not go away; it moved to hot water and heating. Lighting is 6.7× and cooling 5.6× the
identified-building level.

- **This does not undo the closure.** The item asked whether the crashes stopped. They stopped.
- **It is a new item (OPEN-59), not a footnote inside a closed one** — something recorded only
  inside a closed item is something the next session will never find.
- **Cause unknown.** Either the same widened-bounds defect affects the other columns too — in
  which case the same fix applies and this is quick — or those buildings really are
  higher-intensity, which is a calibration question, not a bug. Telling the two apart is cheap and
  needs no cluster time.
- **These buildings are 18 % of that neighbourhood and occur everywhere**, so they lift the fleet
  figure by an amount nobody has measured. I have commissioned that measurement as part of the
  re-run already running.

**The full twelve-area re-run is now running.** 🔴 **The figure it produces will carry two
known caveats, not one:** the 10 m³ volume defect still makes it low by about 1 kWh/m² per
building, and now this. **It is still worth running** — the caveats have known direction and
rough size, so the number is usable as long as it is not quoted as final. **157.1 remains the
adopted figure until that run lands.**


---

## 2026-08-19 (night, later) — the measurement three tasks asked for, finally run

Three separate tasks in the last pass each stopped at the same wall and each named the same
missing artifact. **That artifact now exists.** 48 buildings — 4 per neighbourhood across all 12,
picked by size so the range is covered, no cherry-picking — rebuilt room-by-room with the detailed
outputs left switched on, simulated, and read back through the production parser.

🟢 **All 48 worked. No build failures, no simulation failures, no parse failures.** That settles a
question that has blocked this arc for weeks: the room-by-room mode was never broken, it was being
run with its detailed output switched off, and the parser needs that output to do its job.
Switching it on is the entire fix — across 12 neighbourhoods, 9 building types, 1 to 18 storeys.

🔵 **And it produced the number nobody has had.** Room-by-room comes out **about a quarter below**
the normal mode — **−26.3 % pooled, −24.4 % typical building, across the 48.** 47 of the 48 are
below; one small retail building is 2.7 % above. That is close to the −29 % recorded when this
question was first opened, so the old figure holds up.

🔴 **The obvious explanation is not the explanation.** More than half these buildings disagree
between the two modes about their own floor area, and I expected that to be the whole story. It
is not. On the 21 buildings where the floor areas *do* agree, the gap is still there — around
−26 % typical. **So there is a real energy-side difference of roughly a quarter between two modes
that are supposed to describe the same buildings, and nothing in this arc explains it.** That is
now the open question.

⚪ **What it does not settle.** It does not test *why* — the theory on the table is that
room-by-room models internal loads at 2022 code regardless of the building's real age, and testing
that needs a different run. And it does not size the small-buildings-in-cold-cities question: that
slice is only 8 of the 48, and its own spread (−12 % to −37 %) is far wider than the 3-point
difference from the rest. **8 is too few. I have said so rather than dressing it up.**

🔵 **One practical number:** running the whole fleet this way would cost about **160 GB** of disk,
not the 800+ GB feared. Affordable. **Whether to do it is your call, and I have not taken it.**

- **Nothing published changed.** **153.8 kWh/m² over 8,153 buildings stands untouched** — this is a
  48-building sample and is labelled as one everywhere it appears.
- **Nothing was opened, closed or struck.** Still 19 live items, next free ID OPEN-60.
- **The executor stalled mid-job** — it launched the run, then sat waiting for a notification that
  never comes. The run itself finished fine; I picked up the analysis and write-up myself. Third
  time this failure mode has cost a hand-off.
- Full detail: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.


---

## 2026-08-19 (night, last) — I have to correct the entry above, and the correction is worth more than the original

**The quarter-below number I reported an hour ago is too big.** I sent a follow-up task to split
those 48 buildings by end use — where the energy actually goes — and the first thing it did was
check that the pieces add up to the total. **They did not. Only 6 of the 48 added up.**

🔴 **The cause is a real fault, and it is in the part of the code that reports results.** When a
building is modelled as a few representative floors and then multiplied up to full height, the
lighting and equipment energy is counted **without** the multiplier while the floor area it is
divided by is counted **with** it. Everything else — heating, cooling, fans, pumps, hot water —
is fine to within a hundredth of a percent. So the energy-per-square-metre figure comes out too
low for any building modelled that way, which was **42 of the 48**.

✅ **Your published fleet figure is not affected, and I checked rather than assumed.** That
multiplying only happens in the room-by-room mode. I looked inside the actual model files from the
published run: **every multiplier is 1.** **153.8 over 8,153 buildings is untouched.** What it does
mean is that every room-by-room energy figure this project has recorded is too low — a fault in a
mode nothing published depends on.

🔵 **Corrected, the gap is real but smaller:** **−11 %** across all 48 pooled, **−18 %** for the
typical building, and **≈−24 %** on the cleanest subset. Eight buildings now come out *above* the
normal mode instead of one.

**The part of last night's finding that survives is the part that mattered:** the floor-area
confusion inflates the gap but does not cause it. That still holds, and holds more cleanly.
**The part that does not survive is the size** — "about a quarter below" is true only of the
cleanest subset, not of the sample.

⚠️ **And the follow-up task's own conclusion had to be withdrawn too.** It calculated that the
old-building-age effect could explain at most 7.8 % of total energy and called that far short of
half the gap — but it compared against the *uncorrected* gap. Against the corrected one, half is
8.9 % and 7.8 % is available. **So that theory is back in play, not ruled out.** Inconclusive, not
refuted, and recorded that way.

🔵 **One more thing found along the way:** the code that would have caught this **already exists**
and the fleet pipeline simply never calls it. Several other entry points do.

- **Whether this multiplier fault gets its own tracked item is your call** — I have not taken it.
- **The other question I owed you is answered and it is a clean answer:** for the 290 unnamed
  buildings, **all four** drawn columns are inside their allowed bounds — none out of range. So
  this is **not** a bounds defect like the last one. Those buildings look genuinely
  higher-intensity, which makes it a calibration question, not a bug.
- Full detail: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §10.


## 2026-08-19 (night, last two decisions taken + full board audit)

**You handed both reserved decisions back to me. Both are taken and both are written down with their reasoning, so you can overrule either.**

**1. The energy-reporting fault gets tracked — opened as OPEN-60.** `total_eui_kwh_m2` undercounts
lighting and equipment wherever a zone stands in for several storeys: those two end uses are read
per-zone, which EnergyPlus does not scale by the multiplier, while the floor area they are divided by is
scaled. **6 of 48 buildings reconcile within 2 %; the worst is out by 192 %.** I gave it an ID *because*
nothing published depends on it — that is exactly the kind of fault that gets forgotten and then
rediscovered expensively. 🟢 **No adopted number moves: 153.8 kWh/m² over 8,153 buildings is untouched**,
verified by reading three real fleet model files, not by argument. 🔴 **The more general finding:** the
check that catches this **already exists in the code** (`check_building_integrity()`) and the fleet
pipeline never calls it.

**2. The unnamed-buildings item is rewritten, not closed — OPEN-59.** The screen came back clean:
**0 of 4** drawn columns and **0 of 290** buildings outside their bounds. So it is **not** a repeat of the
data-centre defect and no screen can fix it — every draw is legal. By elimination the pool we borrow from
is genuinely more intensive than the buildings it stands in for: **a calibration question, not a bug.**
I kept the ID open because the screen answered *why not*, not *why* — those buildings still use **10.2×**
the hot water of named ones fleet-wide.

**Register: 20 live, 40 struck, 60 ever opened, next free ID OPEN-61.** Recounted programmatically.

---

## 2026-08-19 (night, the board) — it was not rendering, and that is how I found out

You quoted the board's counters — **12 decided, 6 in progress, 1 ready** — and asked me to finish those
tasks. **The task list under those counters had not been rendering at all.** Fifteen rows carried a
correction note appended to their status; the renderer could not match that against its five known
states; the error threw the whole list away and left the counters standing. **So the board was showing
numbers with nothing underneath them, and the numbers were the only part still working.** Fixed.

**Then every unfinished row was audited against the register or the code, one at a time. 19 of the 24
were already finished and had simply never been marked** — the re-run they were blocked on has run, the
rulings they waited for were made, the closures they recommended were executed. One was verified in the
source: the mis-credited paper is now cited by name at `openubem/semantic/building_classifier.py:216`.

**What is actually left, and it is short:**

- **3 ready.** The 26 untested result columns · the storey-count energy cost (OPEN-35) · the
  evidence-retention decision — which is **no longer hypothetical**, since 874 of 875 harvest directories
  from one earlier run have already lost their evidence files (OPEN-53).
- **1 yours.** Who writes the new labels for the rebuilt classifier exam, and how many rows.
- **1 running.** The vintage experiment below.

---

## 2026-08-19 (night, running) — testing the arc's oldest explanation, finally

**The cross-mode gap is real and it is not the floor-area confusion. The standing explanation for it has
never once been tested.** That explanation: the room-by-room mode gives every building 2022-code
lighting and equipment no matter how old it really is, and that accounts for about half the gap.

🔴 **I checked whether it can be tested honestly, and the answer shapes the experiment.** The load tables
in this repository carry **one** lighting and equipment figure per building type and **no era key at
all** — so a genuinely era-corrected rebuild would mean inventing a table, which this project does not do.

**So the experiment measures the response instead of assuming it.** Twenty buildings — the cleanest
subset, where both modes agree on floor area — rebuilt with internal loads scaled down 30 % and up 30 %,
and then the question inverted: **what would lighting and equipment have to be for this explanation to
account for half the gap?** If that comes out near 0.7× the answer is alive and worth pricing. If it comes
out at 0.1× it is dead, whatever any external table says.

**Why the arithmetic answer was not good enough:** the earlier attempt assumed total energy moves in
proportion to the lighting share. It does not — lowering lighting lowers cooling and *raises* heating,
and those do not cancel. Only a simulation measures that, and this one does.

Plan: `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_vintage-elasticity-2026-08-19.md`. Local, no cluster
time. First checkpoint is a control: rebuild one building with loads unchanged and confirm it reproduces
the run we already have to within 0.5 %.

### 2026-08-19 (late) — the 26 untested result columns, finally checked

Board row **C04** is closed. All 26 simulation-derived columns of the results file were compared
between the frozen June fixture (`docs/docs_VALIDATION/validations/overAll/results/phaseE/`) and the
August local re-run (`open48_refleet4`), across all twelve cells and 8,153 buildings that succeed in
both runs.

**The answer is not a per-column pass/fail — the fleet splits in two.** 48.2 % of buildings come back
unchanged within 0.1 %; 48.6 % within 1 %; **9.0 % move by more than 5 %**, and the 5th percentile of
the per-building ratio sits at 0.824. In **48.4 %** of buildings all six core end uses move by a
single common factor, which is the signature of a **divisor** changing rather than the physics —
independently agreeing with the code-drift adjudication that traced the movement to the OPEN-01
floor-area denominator change and the OPEN-46 elevator breakout, both made deliberately after the
fixture was frozen.

**Materially different, and named as such:** `pumps_eui_kwh_m2` (only 6.68 % of rows, but a median
1.48 % shift when it moves — the largest real per-building change), `dhw_gas_eui_kwh_m2`, and `iod`
(46.65 % of rows; **cause not established**, and recorded that way). Everything else differs only at
rounding scale (median ≈ 0.002 %) and is not a reproducibility failure in any sense a reader cares
about. `total_eui_kwh_m2` shows the largest >1 % share but is the **OPEN-60-defective** column and is
not treated as physical evidence.

**Two director corrections, both recorded because both would have looked like results.**
1. The executor's headline "25 of 26 columns differ" was measured at a 1e-9 tolerance, which counts
   rounding as failure. Re-derived with magnitudes, the picture inverts. Reported max-relative values
   of 156,376× (heating) and 15,928× (`iod`) are **near-zero-denominator artefacts**, now labelled.
2. **The first attempt compared against the wrong fixture family** — `step1/overAll/results/cases/`
   (20 columns) instead of `validations/overAll/results/phaseE/` (32 columns) — and returned a
   confident "NOT COMPARABLE" plus a suspected missing-fixture provenance defect. **Both were false
   and both trace to the director naming the wrong path in the dispatch.** Verified afterwards:
   commit `0df422e` **is** the commit that last touched the phaseE fixture, so OPEN-06b's provenance
   citation is sound. **No defect; do not reopen.**

**Standing lesson:** an executor handed a wrong baseline reports confidently on that baseline. Verify
the fixture family — column count and last-touching commit — *before* dispatching a comparison.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_twentysix-simulation-columns.md`,
`openubem/outputs/comparisons/open06_26col_reproducibility.csv`.

**Still open from this:** whether `iod` and one `simulation_status` flip are code drift or
non-determinism. Settling it needs a **same-HEAD double run** to test bit-stability — cheap, and
useful to the whole project beyond this row. Not started; the machine is busy with the elasticity run.

### 2026-08-20 — OPEN-03's central claim is refuted, by a control nobody designed

**The oldest live item in the arc claimed that ~half the cross-mode EUI gap comes from `layout_assign`
applying vintage-blind 2022-code internal loads. Measured: ≈8 % of the pooled gap. The claim is
refuted and the premise with it.**

The ±30 % load perturbation reached **4 of 20 buildings**. That is not a failed experiment — it is a
natural control. `layout_assign` has two internal-load paths (`openubem/idf/builder.py:69-83`,
`:228-236`): archetypes with a mapped `STD2022` baseline IDF take the baseline's own densities and
**never call `assign_loads()`**; archetypes without one read the **same archetype table `auto` reads**.

| subset | n | `auto` EUI | `layout_assign` EUI | gap | load drop | share of gap |
|---|---|---|---|---|---|---|
| all 20 | 20 | 170.14 | 129.45 | **−23.91 %** | +3.52 | **8.0 %** |
| loads held identical | 4 | 204.14 | 155.94 | **−23.61 %** | **−0.00** | **0.0 %** |
| prototype-baseline path | 16 | 115.09 | 86.56 | −24.79 % | +9.23 | 29.9 % |

**Four buildings whose internal loads are bit-identical across modes still show a −23.61 % gap** —
indistinguishable from the −24.79 % of the sixteen whose lighting differs 2.6×. Hold the suspected
cause perfectly constant and the effect does not move. The pooled −23.91 % reproduces the
independently established **−23.93 %** to two decimals, which is the control on the calculation.

**The premise was also wrong.** `auto` is equally vintage-blind — one fixed pair per archetype in
`doe_prototype_loads.json`, no vintage key. This is a load-**source** disagreement, not a
load-**vintage** one. **No era table would close it, and none should be commissioned for this item.**

**Superseded:** the `k ≈ 1.4–2.1×` inversion from T03 — computed on the 4 buildings with *zero*
load-driven gap, so it inverts a mechanism not operating there. The elasticity itself (0.21–0.29,
linear across ±30 %) stands and supplies the ~7.4 % net HVAC damping.

**Method lesson, and it was my error.** I wrote CP-1 to verify **one** building. That building was one
of the 4 reachable ones, so the gate passed while the intervention was inert in 16 of 20. **A control
on one exemplar cannot establish that an intervention reached a population.** Perturbation plans must
gate on the count of responding buildings. The executor found the 16 non-responders unprompted and was
right to flag rather than tidy them away.

**OPEN-03 stays live with its scope replaced:** ~92 % of a −23.9 % gap is unexplained and now known
**not** to be internal loads. **Cheapest next attack, no new simulation:** an end-use diff on the 4
from-scratch buildings, where loads, archetype and weather are identical across modes, so the whole
−23.61 % must live in geometry, zoning, envelope or HVAC sizing. Both runs are already on disk.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_load-elasticity.md` §CP-2 ·
`scripts/analysis/open03_load_source_decomposition_2026-08-20.py` ·
`openubem/outputs/comparisons/open03_load_source_decomposition.csv` · `..._per_building.csv`.
Register: **20 live / 40 struck / OPEN-01..OPEN-60 / next free OPEN-61** (re-derived after the edit).

### 2026-08-20 (overnight) — the four unfinished board rows, run while you slept

**You left with two instructions: take every decision yourself, and carry it to the end. Four
executors ran in parallel on `implemenation/previous/PLAN_four-board-items-2026-08-20.md`. Three rows are
finished, the fourth stopped at its own control and was re-scoped rather than forced.** Every ruling
below was taken by the director under your delegation of 2026-08-20.

**Register after this pass: 21 live / 40 struck / OPEN-01..OPEN-61 / next free OPEN-62.**

#### AA7 — the cross-mode gap is localised, and it is a geometry finding

The end-use diff on the 4 load-identical buildings ran with **no new simulation**, and it landed.
Controls first: all four per-building ratios reproduce, the pooled figure comes back at **−23.6090 %**
against the −23.61 % on record, and each arm's seven end uses reconcile to its own ABUPS total within
**0.031 %**.

| end use | Δ kWh/m² | share of gap |
|---|---:|---:|
| **Heating** | **−42.20** | **87.6 %** |
| Fans | −4.98 | 10.3 % |
| Cooling | −2.37 | 4.9 % |
| Pumps | −0.74 | 1.5 % |
| **Interior Lighting / Interior Equipment** | **0.00** | **0.0 %** |

🔴 **The cause is wall and window area, not loads and not vintage.** Floor area, zone count and WWR are
identical between arms in all four buildings. But `nyc_centre/265424467`, which dominates the pool by
floor area, has **44 % less exterior wall (16,270 → 9,122 m²) and 44 % less window (6,502 → 3,645 m²)**
under `layout_assign` — at the **same** floor area, the **same** 81 zones and the **same** 39.96 % WWR.
The other three buildings have identical envelopes in both modes and differ only in HVAC autosizing.
**OPEN-03 has carried a name about internal loads since the beginning and is really about geometry.**

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md` ·
`openubem/outputs/comparisons/open03_enduse_localisation{,_geometry,_pooled}.csv`.

#### 🔴 OPEN-61 opened — the energy total quietly drops a heat source

**Found by the task's own reconciliation control, which the plan did not ask for.** `METER_QUERY`
(`openubem/results/parser.py:48-54`) names no `DistrictHeating` meter of any kind, so
`total_eui_kwh_m2` drops the District Heating part of Water Systems. Director control on a real `.sql`:
ABUPS reports **0.72 GJ**, which is **1.22 %** of that building's total end uses.

🔴 **It is not a one-line fix.** No `DistrictHeating` Run Period meter exists in the file at all —
adding the name to the query would change nothing. The value survives only in the ABUPS tabular table.
Any remedy either requests the meter in the IDF (changing every future run, fixing no existing one) or
teaches the parser a second, differently-shaped source of truth. **Neither is chosen here.**

**The adopted `153.8231 kWh/m²` is NOT restated.** Four buildings do not size a fleet. The honest
statement is that it is low by an unknown amount that measures ~1 % where it has been measured.

**Standing lesson, now a pattern rather than a coincidence: three passes in a row, the defect came from
an executor checking its own arithmetic** — OPEN-60, then OPEN-61, neither commissioned. **The
reconciliation control belongs inside `parse_building()`, not in whichever task happens to think of it.**

#### S03 — the classifier exam rebuilt over all the data

You widened the question before delegating it: label **all** the data, not a sample. So the new exam
covers **every one of the 592 tag-rich buildings** (Boston 233 / Chicago 359 — reproducing the old
fixture's own pool definition exactly), with the remaining **290 tag-poor rows kept as a separate,
deliberately ungraded sheet**. Labels are written from tags, name and address; size may only choose
**small vs. large inside a class the tags already decided**. That is the circularity you objected to,
removed. **589 of 592 rows are strong evidence; the 3 thin ones are all flagged** — two hotels with no
size data at all, and one genuine conflict: a skyscraper that really is an office tower with a working
church inside it.

🔴 **The result is two numbers and must always be quoted as two.** Strictly graded, the classifier
agrees **71.1 %** of the time — but **106** of those disagreements are it applying its own deliberate
rule that very tall buildings get their own category, which the new answer key is forbidden to use.
Credit that rule and it scores **89.0 %**. **By family it is right 100 % of the time, on all 592.**

⚠️ **The honest catch:** of the 65 errors left after crediting the height rule, almost all are
**small-vs-medium-vs-large within the right family** — and the size band is the one part of the answer
key still allowed to look at size. **v3 removed the circular reasoning from the class and could not
remove it from the band, and that is exactly where the classifier now fails.** No amount of re-labelling
fixes that; it is a size judgement on both sides.

⚠️ **This is not an improvement on the old 88.8 % over 98 rows**, and ruling `2a` forbids saying it is.
The fair statement is *comparable performance on an exam six times larger and much less circular*.

**Gates set by the director:** coarse ≥ 0.98 (measured 1.000, pass) · fine with the height rule
credited ≥ 0.85 (measured 0.890, pass) · **strict fine left ungated as a diagnostic**, because gating it
would force a choice between deleting the classifier's height rule and bending the answer key to match
it, and a test threshold should not make that decision quietly. **No register ID opened.**

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md` ·
`tests/fixtures/labelled_archetypes_tagrich_v3.csv` (592) · `..._tagpoor_v3.csv` (290) ·
`openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv`. The two older fixtures were **not
touched**.

#### W9 — the archive is pruned, and it was bigger than I told you

Done in two stages with a signed checkpoint between them: inventory and copy first, deletion only after
the copy was verified.

| stage | result |
|---|---|
| re-inventory | **140,261 files / 233.9 GB across six sets** — my earlier 87,887 / 152.4 GB is **superseded, not retracted**; a twelfth-cell re-run was added after that count |
| copied out of Temp | **116,128 files / 11.7 GB** into `OpenUBEM\evidence\`, which is gitignored and cannot enter a commit |
| verified | every file type matched its source count exactly, all six sets; **380 files re-hashed byte for byte, 380/380 match** |
| deleted | **23,862 `.sql` files, 207 GB of disk recovered**; nothing else touched; remaining `.sql` there: **0** |

🔴 **One cost, recorded rather than glossed.** Another task was reading `.sql` **from that very folder**
while the copy was being checked. It finished first, so nothing was lost — but the safety check I ran
(*"nothing modified in the last 90 minutes"*) **could not have caught it, because reading a file leaves
no trace.** Re-deriving one of those energy numbers now means **re-simulating rather than re-reading** —
and OPEN-61 is already a live item that would have been sized from that corpus.

**Standing lesson: an mtime check does not prove a corpus is idle.** Before deleting shared evidence,
check what is *running*, not what was *written*.

**OPEN-53 itself stays open.** A storage prune does not touch its 874-of-875 finding.

#### C05 — the executor stopped at its own control, and that is the most useful result of the pass

T04 was told to intervene on 24 buildings across 8 cells. It could not fill `austin_rural`: across
**all 244** of that cell's affected buildings and all 11 archetypes present, the two storey fallbacks
**agree**, because the cell's group-median is 1 for every use class with an observed row. **It refused
to substitute a cell or pick a known-null triple, and stopped before EnergyPlus was invoked.** The
director re-derived both of its load-bearing claims from the 790-row census; both hold exactly.

**Two rulings followed:**

- **Proceed on 21 buildings across 7 cells; do not substitute a cell.** `austin_rural` is recorded as a
  **structural null, 0 of 244** — which is itself an answer to C05: where there is no storey evidence
  anywhere, the mismatch cannot arise. The other seven cells hold **459** eligible buildings.
- 🔴 **OPEN-35's stated population is stale and is corrected.** The headline *"1,031 mid-/high-rise
  apartments"* no longer describes reality: only **25** apartment-archetype candidates remain in the
  eight cells, **24 of the 25** already build at the group-median storey count in today's production
  after the item's own wiring fix of 2026-08-19, and **0** are eligible. *"As built today"* no longer
  equals *"levels = 1.0"* for most of the buildings the item was written about.

The 21-building paired run was dispatched and is the one piece of this pass still moving. **Its results
will be reported as within-cell medians only — never pooled into a headline, never restated as a fleet
EUI correction, never carried back onto the 1,031-building framing.**

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md` ·
`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20{,_census,_selection}.csv`.

**Standing lesson: an executor that stops at a failed control is worth more than one that delivers a
number.** T04 produced no measurement and still proved a cell is structurally empty and caught that the
item's headline population had silently self-corrected.

#### C05 — and then it ran: OPEN-35's first paired measurement, finished 02:37

The 21-building run landed while you slept. **21 buildings, 7 cells, 42 EnergyPlus runs.** Same
building twice: once with the storey count production actually uses (**1 storey, all 21**), once with
the alternative the archetype path would have picked (**2 to 19 storeys**). Same weather, same
archetype, one input changed — which is the design this item has needed since it was opened, and the
reason the old +62.20 kWh/m² number could never answer it.

**All three checks I wrote before the run passed.** The most important one first:

| check | required | measured |
|---|---|---|
| the untouched arm reproduces the number already on the fleet record | within 1 % | **0.0199 %** worst case, 0 of 21 outside |
| treated runs finish without a severe error | at least 18 of 21 | **19 of 21** — all 21 finished, **none fatal** |
| the treated building really was built taller, read from the file itself | 21 of 21 | **21 of 21** |

That first row is what makes the rest trustworthy: the test harness reproduces the production number
to two parts in ten thousand, so whatever the second arm does is the change and not the harness.

**The result, per cell — never pooled, as ruled:**

| cell | change |
|---|---:|
| la_centre | **+75.3 %** |
| austin_suburban | **+73.6 %** |
| austin_centre | **+73.1 %** |
| austin_urban | **+70.3 %** |
| nyc_centre | **+59.9 %** |
| la_urban | **+37.9 %** |
| **la_suburban** | **−2.6 %** |
| austin_rural | no eligible building exists |

So for the buildings where the two storey fallbacks genuinely disagree, **which one you pick is worth
tens of percent on that building's energy** — and production currently picks the lower one every time.

🔵 **The one result I did not expect, and it is the interesting one: the defect does not always point
the same way.** The two small offices in `la_suburban` that go from 1 to 2 storeys get **better**, not
worse (−11.3 % and −2.6 %). Giving a small building in a mild climate a second floor spreads its roof
and ground losses over twice the area faster than it adds load. **Had I pooled these 21 into a single
headline, it would have come out as one confident positive number and this would have vanished.** The
no-pooling rule has been standing on a statistical argument for weeks; it now stands on a measured
sign flip.

⚠️ **What it does not say.** It does not restate the fleet baseline — **21 buildings out of 8,153 do
not move `153.8 kWh/m²`** and I did not try. It is not an estimate of what the defect costs across the
fleet: these 21 were chosen *because* the two fallbacks disagree. And it still does **not** answer
**which fallback is right** — that is the design decision OPEN-35 has always been waiting for. Tonight
measured how much the question is worth, not its answer.

**Artifacts.** `extra/MEASUREMENT_open-35_storey-intervention.md` §T4b ·
`openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv`.

---

**🟢 The 2026-08-20 pass is closed. All four board rows — AA7, S03, W9, C05 — are done.** One new
item was opened (**OPEN-61**), one item's stated population was corrected (**OPEN-35**), one custody
obligation was discharged (**W9**), and **207 GB** of disk came back. **Register: 21 live, next free
`OPEN-62`. Nothing is waiting on a decision from you.**

---

### 2026-08-20 (later) — the open-items register was closed and a book II opened

You asked for the director prompt to be refreshed and for the register to be closed if it could be.
It could. **`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` is CLOSED** at 8,246
lines — 61 items, 40 of them already struck — and carries a 🔒 banner at its head saying so.

**The live register is now `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md`:
180 lines, the 21 live items and nothing else.** Their rows are copied over word for word; no item
was opened, closed, merged or re-scoped by the rotation.

**The closed book did not move and nothing was renamed** — 79 documents cite into it, and it stays
the authority on every closed item and on every live item's full history. Book II points back to it
by heading rather than restating it. Every `INVESTIGATION_open-items-register.md` link in this file's
journal above still resolves.

**One real defect was found in the act of closing:** OPEN-61 was opened earlier the same day with a
§-section and an amendment note but **never a §1 table row**, so the register's own recount script
reported **20 live / next free `OPEN-61`** while its prose and the director prompt both said **21 /
`OPEN-62`**. The prose was right and the table was one row short. The row was written and inserted
before the book was closed; the script now agrees with the prose at **21 live / 40 struck / 61 total,
`OPEN-01…OPEN-61`, no gap, next free `OPEN-62`.**

`openings/prompts/DIRECTOR_PROMPT_openings.md` now opens with a 🟪 resume box that supersedes every
earlier one — the 🟨 box's "a plan is in force and three executors are running it" was stale and is
struck in place — and its §2 points at book II.

🧹 **Left undone on purpose:** five completed plans still sit in `openings/implemenation/` rather
than `implemenation/previous/`. All are checkpoint-signed and closed, but moving them carries the
citation-sweep obligation, so it is left for a session that will finish it.

**A board for the 21 was built the same day** — `openings/reporting/board_open-items.html`, published
at <https://claude.ai/code/artifact/7960a833-541b-4eab-a006-403c53c4bddc>. It is a **second** board,
not a replacement: the published-numbers board still carries the adopted figures and the checkpoint
history, and this one carries only what is unfinished — each item with its size, what is bounded,
what is unmeasured, and what is next. Both are updated in place at their own URLs.

### 2026-08-20 (late) — five tasks ran against four open items, and two of them changed shape

`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md` was written, executed
T01–T05 by four Sonnet executors, audited at three checkpoints and closed the same day. Nothing was
committed; nothing ran on the cluster; only one task simulated, and it was gated behind the first
checkpoint.

**The finding that matters.** OPEN-61 — recorded as "the EUI total drops a district-heating term,
~1 % on four buildings, fleet share unmeasured" — is **fleet-wide and roughly ten times that size**.
The models carry a hot-water use object connected to no plant loop; EnergyPlus computes its load,
finds no plant to charge it to, and books it to a district-heating column the model never declares
and the parser never reads. Deleting that object on one building drove the term to zero while the gas
water heater's own consumption stayed bit-identical, so **this is energy the model spends and reports
nowhere**, not a double count. All 16,336 fleet IDFs match the affected pattern and 60 of 60
re-simulated production buildings carry it. It is concentrated by archetype: offices lose ~1.4
kWh/m², apartments ~32, and apartments are a third of the fleet. Fleet exposure is **estimated** at
8.7–20.2 kWh/m² — 6–13 % of the adopted 153.8231 — but that estimate transfers a 60-building ratio
onto 8,153 buildings and **must not be published as a correction**. A census-scale measurement is the
obvious next arc and was deliberately not authorised.

**Three smaller results.** OPEN-03's "44 % less wall" is retracted — it reproduces on exactly one
building, the one it was measured on, and the real disagreement between the two modes is storey
count. OPEN-12 is settled: the unnamed third cell is `nyc_suburban` (1,589 of 1,589 missing a source
height), the recorded 36.4 % and 19.2 % are both actually 100 %, and the fleet counts already in the
register are exactly right. OPEN-13 reverses: the 43 tests were never lost — nothing was deleted from
git, and all 43 run at HEAD today (`43 passed, 10 skipped in 0.65s`); the 10 that stay skipped belong
to OPEN-17. **OPEN-12 and OPEN-13 are ready to close.**

**Housekeeping.** The suite baseline is restated to **1,918 passed / 56 skipped** (`py -3 -m pytest -q
tests/`, 24 min); the carried 1,875/55 is stale. Two debug-reference entries were registered. The
open-items board is updated in place at its own URL. The register count is unchanged at 21 live / 40
retired / 61 total, next free `OPEN-62`.

### 2026-08-20 (latest) — OPEN-12 and OPEN-13 closed; the register count moves for the first time

Asked whether to close the two items the five-task pass had left ready, the user ruled *"oui ferme
OPEN-12 & 13"*. Both are now struck in `INVESTIGATION_open-items-register-II.md` §2, with a closing
note each in §6, and **the count moves from 21 live / 40 retired to 19 live / 42 retired**, 61 total,
next free `OPEN-62`. Live IDs, retired IDs, union and gap-check were all re-derived after the edit:
19 + 42 = 61, no overlap, no gaps.

**Neither closed on a repair.** OPEN-12 closed on a completed census — the unnamed third cell is
`nyc_suburban`, the recorded 36.4 % and 19.2 % are retracted for 100 % and 100 %, and the fleet counts
already in the register are confirmed exactly. OPEN-13 closed on a **refutation**: the 43 "lost" tests
were never lost and run at HEAD today. Per the register's standing rule, each closing note names what
survives it — **OPEN-12's real 2,806-of-8,160 source-coverage gap passes to OPEN-14 and OPEN-15**,
and **OPEN-13's 10 residual skips pass to OPEN-17**, recorded on OPEN-17's own row so the inheritance
is visible from the table and not only from the closed item.

**One stale caveat was corrected in the same pass.** §1's fleet-figure line still read that the
adopted 153.8231 kWh/m² was "~1 % low by OPEN-61 on the four buildings where that has been
measured". That is superseded: OPEN-61 is fleet-wide and the exposure is **estimated at 6–13 %**.
The line now says so, and says explicitly that the range is a size and not a correction.

**Still deliberately unfiled:** the storey-count disagreement behind OPEN-03, and the census-scale
OPEN-61 measurement. Both need the user's go-ahead before they get an ID.

### 2026-08-20 (latest) — three items leave the register, and the two arcs you authorised are planned

**OPEN-27 — the erratum is with you, and it turned out to be two edits, not one.** Preparing the
paste-ready text surfaced a **second occurrence nobody had recorded**:
`docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78` carries the same wrong
`MultifamilyHome` name as `DESIGN_step-2…:529`. Re-verified at HEAD: `MultifamilyHome` has **0**
occurrences in `openubem/data/openstudio_archetypes.json`, whose two `sector == "Residential"` entries
are `MidriseApartment` and `HighriseApartment`. The item stays live until the edits land.

**OPEN-20 — retired, not closed.** A scope question rather than a defect: nothing broken, nothing
blocked, nothing to measure, and tracked **twice** since 2026-06-17 (a register row *and*
`docs/docs_TODO/wider_validation_matrix.md`). Retired on the OPEN-21 precedent; the ID must never be
reused. ⚠️ **The caveat it carried survives it** and now belongs to the TODO doc and to OPEN-19:
the model does not vary construction or HVAC by climate zone, so even the three sampled climates are
weaker evidence than the geography suggests — and that binds the adopted **153.8231 kWh/m²**,
a pooled statistic over exactly this population.

**OPEN-18 was examined as a closure candidate and rejected as one.** Its ✅ marks the elimination of
the `Zone.Multiplier` *approach*, not of the defect. Book I §8 says so in as many words — *"Q3 stays
open; that approach does not"* — and calls it the largest open modelling problem in the project.

**Count: 18 live / 43 retired / 61 total, next free `OPEN-62`**, re-derived after each edit
(18 + 43 = 61, no overlap, no gaps).

**Both authorised arcs are now planned** in
`docs/docs_ACTIVE/openings/implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md`, T01–T05
over four checkpoints, not started. 🔴 **One discovery shaped the whole plan: run 4's `.sql` files
were discarded** — all 8,160 buildings kept only `.eio`, `.end` and `.err`, so the district-heating
term is **not recoverable from disk** and the census needs a re-run. Cost measured from run 4's own
`.end` files over a 400-building sample: median **14.2 s**, mean **52.5 s** per building,
**≈119 CPU-hours** for the fleet — an overnight job locally, minutes on Speed. The plan gates that
spend behind CP-2 and leaves the host choice to the pilot's measured rate. Arc B (OPEN-03's storey
census) needs no simulation at all.

---

## 2026-08-20 (later) — Arc B is finished: OPEN-03's storey question is counted on all 8,160

**The headline is 70 %, and it is worse than the raw disagreement rate suggests.** For **5,714 of
8,160 buildings (70.0 %)** the `layout_assign` mode builds the *prototype's* storey count and ignores
the real building's entirely. Those buildings average **3.12** real storeys and reach **105** — and
are built with an average of **1.21** geometric storeys, never more than **6**. The mode represents
the real storey count for only **2,446 (30.0 %)**.

⚠️ **Do not quote the 60.2 % figure as the finding.** It is the raw arm-vs-arm disagreement rate, and
it compares a per-building count against what turns out to be a **per-archetype constant** — 18 of the
20 archetypes have exactly one `layout_assign` storey value across every building they cover. That
made the 60.2 % close to true-by-construction. **70.0 % is the number that means something.** This was
the director's own check of the output, not something the measurement reported.

**Why the result can be trusted:** the census reproduces the earlier 48-building measurement
**exactly** — 96 of 96 rows across both arms, and restricted to those 48 it returns **28
disagreements of 48**, the predecessor's number to the unit. No sampling, no simulation, whole fleet.

🔴 **A new defect was found in the act of measuring, and was registered rather than quietly fixed.**
The storey-counting method omits a zone's own `Z_Origin` under Relative coordinates, under-reading for
6 archetypes — **2,983 buildings, 36.6 % of the fleet**, including the largest single archetype.
Fixing it mid-task would have changed what the reproduction control had to reproduce, so it was
flagged per row and written into the debug reference instead. ✅ **It does not affect the headline:**
excluding every at-risk building gives **60.8 %** against **59.2 %** for the at-risk group.

🟡 **One ruling is owed to you.** The director recommends granting **one** new item ID, `OPEN-62`, for
that `Z_Origin` parsing gap — a distinct defect, in a different place, with a different fix. And
recommends **against** a second ID for the storey-coverage finding, which belongs to OPEN-03 and is
already recorded there. **Neither has been opened.**

⚠️ **A correction to a published count.** The "**16,336** production IDFs" figure recorded earlier was
wrong — a recursive glob double-counts on this directory tree. The fleet is **8,160 IDFs, one per
building**. Re-run against the right denominator, the OPEN-61 discriminator is unchanged: **8,160 of
8,160** carry the orphan hot-water object, **0** carry a plant loop — 100.00 %. Struck and corrected
in place in the register.

**Arc A (the OPEN-61 fleet census) is still running** — the 200-building pilot is in flight and the
119-CPU-hour census stays gated behind CP-2.

---

## 2026-08-20 (later still) — the census is running, and OPEN-62 is open

**You granted the ID; it is opened, and it shrank the same hour.** `OPEN-62` now covers the
storey-reading gap. It was written down with the alarming reading marked *unchecked* rather than
asserted — "six building types may have been built at the wrong height" — and one search settled it:
**the real geometry code reads the height correctly.** Two analysis scripts have the bug and one
column of one spreadsheet is wrong. Nothing is built wrong, no energy number moves.

**The two gates before the expensive part are both signed.** A 200-building trial rebuilt buildings
from scratch and compared them against what was recorded before: **200 of 200 matched**, to four
decimal places past what anyone would check. The missing hot-water term was present on **200 of 200**,
and on every one of them it was the service-hot-water row and nothing else — the mechanism, visible in
the output rather than argued.

🔴 **The full census is running now — all 8,153 buildings, about eight hours, on this machine.** It
had to be a re-simulation: the original results files were deleted, so there is nothing left to
re-read. Cost, now measured rather than guessed: **97 CPU-hours**, and a tenth of the fleet buys half
of it.

⚠️ **One number in flight that must not be quoted yet.** The trial's pooled figure is 23.87 kWh/m².
**It is not the fleet number** — the trial deliberately over-sampled large buildings, which are the
ones carrying the most hot water. The real comparison against the 8.7–20.2 estimate happens when the
census lands, and not before.

**A correction I owe you:** between the two gates I projected the census at 33 CPU-hours. That was
wrong by a factor of three, and wrong for a reason worth knowing — I took the timings from a sample
that happened to contain none of the slow buildings. The original ≈119-hour estimate was the better
one all along. It is withdrawn in writing in the plan, not quietly dropped.

**Nothing is owed by you right now.** The one erratum (OPEN-27, two edits in spec documents) is still
yours whenever you want it.



---

## 2026-08-20 (afternoon) — four decisions taken, and a second plan started beside the census

**You asked what could move while the census runs, and then ruled on four questions.** All four are
recorded in `docs/docs_ACTIVE/openings/implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`
§4, which is the second plan now in force. It exists because none of its work needs EnergyPlus — it is
IDF text parsing — so it runs **beside** the saturated machine rather than behind it.

**Three imputation items became one.** OPEN-15, OPEN-16 and OPEN-17 were three rows describing a
single fact: the imputation tiers were built and never wired to the production router. OPEN-17 now
carries all three. ⚠️ **This is bookkeeping, not progress** — nothing was measured, fixed or decided
by the merge, and the register says so where a reader will hit it. What it buys is that the same
decision can no longer be re-argued from three directions. **Count: 17 live / 45 retired / 62 total,
next free `OPEN-63`.**

**Two register defects were found and repaired in the same pass, and neither is smoothed over.** The
§1 *Live IDs* line read `(18)` and omitted OPEN-62 — the identical one-row-short failure that book's
own rotation note warns about, repeated within hours of being written. And the *Plans in force* row
was stale, still describing a pilot as in flight that had finished.

**OPEN-62 is being fixed now, and the control it would have broken is being replaced rather than
kept.** This is the part worth your attention: the old control passed **96 out of 96** — and that
number meant nothing, because both sides of the comparison were produced by the *same* suspect
parser. A control that re-runs the code it is meant to check produces agreement, not correctness. The
replacement is checked against a reader that never touched that code, and **it is allowed to fail**.
If it fails, that is the finding.

**I recommended retiring OPEN-18 and OPEN-19 and you declined.** Recorded as declined rather than
left un-asked, so it is not quietly re-proposed at the next pass. All six measured-but-unremedied
items — OPEN-09, 10, 14, 18, 19, 38 — stay live.

**Still yours, unchanged:** OPEN-27's two edits, in
`docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`
and `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78` — replace `MultifamilyHome`
with `HighriseApartment` in both. No exception to the never-edit-spec-documents rule was granted, and
I did not take one.

## 2026-08-20 (evening) — OPEN-27 closed, and a control that came back amended

**OPEN-27 is closed.** A specification defined the accuracy metric against a building type this
project does not have. The fix was two words, in two lines. It stayed open for weeks not because it
was hard, but because those lines live in `docs_main/`, which this session may not edit — and the
question that had been put to you was *"will you make this edit?"* rather than *"will you let me?"*.
You granted a scoped one-time exception and it closed in four minutes. The replacement was checked
against `openstudio_archetypes.json` rather than taken on trust (exactly two Residential archetypes,
`MidriseApartment` and `HighriseApartment`), and the three regression tests guarding it still pass.
🔴 **Worth carrying forward: an item whose only obstacle is a permission is not work in progress,
and should be surfaced as a permission question.** The exception was scoped to those two lines and
does not generalise.

**The OPEN-62 parser fix is in and its first gate is signed — but control C12 is recorded as
amended, not passed.** Six archetypes were predicted to change under the fix; four did.
`Outpatient` and `SecondarySchool` are read wrongly floor-by-floor and come out right for the
building as a whole, purely by how their files happen to be written. Recording that as a pass would
have buried it — the next measurement that counts storeys per floor rather than per building will
see both move.

**A second thing surfaced in the audit that nobody had asked about.** The analysis parser at the
centre of OPEN-62 cannot read the original DOE files at all: it returns every area as zero, with no
error and no warning. Every result it has ever produced rests on re-saved copies of those files, and
that was written down nowhere. The 18 re-saved files are now preserved so the check stays
reproducible. **This is the same shape as OPEN-61** — a number that looks like an answer because the
failure is silent.

**Still running:** the 8,153-building census (OPEN-61) and the fleet-scale re-run of the storey
count with the corrected parser (OPEN-62 T02).

## 2026-08-20 (evening, later) — the replacement check failed, and that is the result worth having

You ruled this afternoon to **replace** a check rather than keep it. The old one compared the
measuring script against itself and passed 96 out of 96 — agreement, not correctness. The
replacement compares it against the real geometry code, and **it was written to be allowed to fail.**

**It failed.** The two readers agree on 12 of 18 building types and disagree on **3,734 buildings**.
Tracing it produced the finding of the day: **the script was never counting storeys.** It counts the
number of heights at which a new outside wall begins. On a tower whose glass facade runs unbroken
past several floors, that is one height, not several — so a genuine 20-storey building reads as 10.

🔴 **The height fix was correct and was not enough.** It removed an error from inside a measurement
of the wrong quantity. **Had the old check been kept, it would have passed again and this would have
been signed off as correct today.**

**What this changes, and what it does not.**
- **OPEN-62 stays open** and is now a bigger question than the one it was opened as. It needs a
  decision from you — what should a storey count be derived from? — not more measurement.
- **Any number from that column is a floor, not a value.** The corrected average storeys built is
  **at least 2.25**, the maximum **at least 16**. Never quote them as equalities.
- ✅ **Nothing built is wrong.** The reader that gets 20 right *is* the production geometry code.
- ✅ **OPEN-03's headline is untouched** — one mode still ignores the real storey count for **70 %**
  of the fleet, and that figure never depended on the broken column.

**Also done this evening:** OPEN-27 closed; three decision documents written for you (which storey
fallback is correct; a proposed reconciliation control; and OPEN-53's custody risk, which is
**recurring right now** — see below).

🔴 **One thing needs you before the census finishes.** The 8,153-building re-simulation is writing
≈38 GB of results into a temporary folder that no policy covers and that disappears with the
session. That re-simulation only exists because the previous copy was deleted, at a cost now measured
at **97.2 CPU-hours**. If this copy is swept too, the next question costs the same again. **Preserve
or discard — it is a disk-budget call and it is yours.** I have not moved it.

---

## 2026-08-20, later that evening — you answered both questions, and the answer to the second one turned out to be half right

**You ruled: preserve the 38 GB, and derive the storey count from floor surfaces.** Both are done or
in hand. The second one is the interesting one, so it goes first.

**Floor surfaces are a better reader, and they are still not a storey count.** The new reader was
built, run over all 8,160 buildings, and checked against four tests written in advance. It gets the
tower right — 20 storeys where the old method said 10 — and it settled a second question nobody had
asked: **the old method also counts too many, not only too few.** A warehouse is a one-storey
building whose tall outside wall is built in two stacked bands; the old reader called that two
storeys. So the old column is not a floor and not a ceiling. It simply is not a storey count in
either direction, and **the "at least 2.25 / at least 16" wording I gave you this afternoon is
withdrawn.**

🔴 **The new reader counts attics.** A small office is one storey with an attic above it. Its attic
has a floor, so the new reader calls it two storeys. The same is true of both restaurant types.
That is **3,580 buildings — 44 % of the fleet.** With attics removed, the average storeys built is
**2.45**, not the 2.94 the run reported. So the honest number is a **range, 2.45 to 2.94**, and I
have refused to publish it as a single figure.

**What this means for you.** OPEN-62 does not need a third reader. It needs something this project
has never written down: **what counts as a storey when a building has an attic, a plenum, or a
double-height bay?** That is a modelling definition, not a measurement, and it is yours to set. Until
it is set, the storey headline stays a range.

✅ **Nothing built is wrong, and no published figure moves.** The production geometry code was never
using the broken column, and OPEN-03's 70 % headline never depended on it.

**Worth noting about how this was caught.** Three checks in this arc were deliberately written so
they *could* fail. All three did, and each one found something. The comfortable version — fix the
bug, keep the check that already passes — would by now have closed this item twice with the wrong
number inside it.

**The 38 GB.** Preserved as you ruled. It moves out of the temporary folder the moment the
re-simulation stops writing, not before. The run is at **6,441 of 8,153**.
