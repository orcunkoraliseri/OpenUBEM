# DIRECTOR PROMPT — European locations, occupant schedules, and simulation campaign

**Project:** OpenUBEM × GSSCanada Step 8 integration  
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`  
**Status at handoff:** documentation and reusable visual/table assets were updated on 2026-08-23; a **source-verification and citation audit closed on 2026-08-23** (§4.1, §18); a **source-alignment pass against the parent Step 8 authorities closed later the same day** (§4.2) — MVP §11 and walkthrough §12 are new; the same night the **DR08–DR11 deep-research reports were accepted and every closable decision closed** (§4.3 closure note, MVP §11.13) — only the upstream Step 7 chaining rule remains blocked, `f>0` cells only. **Implementation is in progress**: the current evidence and slice status are maintained in §19.5 and the append-only walkthrough log. **The newest checkpoint (2026-08-25T19:05:00Z) is `EU-04 / S1-EXEC-01-CP2`: `S1` ran to its end under the ruled Option H1 and met its ladder criterion — 12/12 accounted for, 11 `EPLUS_COMPLETED` and 1 `EPLUS_FATAL` (a real 173-vertex footprint against the IDD's ~120-vertex surface limit), with **no energy number produced**. Two findings are carried and deliberately unfixed: dwelling-layout success is **CRS-dependent** (rotation about `(0,0)` audited with an absolute tolerance), and the single dwelling-level run covers **one floor plate, not the stack**. See §19.5. The previous checkpoint (2026-08-25T17:42:47Z) was `EU-04 / FR-TYPOLOGY-RULED-01`: `D-EU-04-G` is RULED (Option G1, both consequences accepted), the implementation claim was audited and does NOT hold — nothing is blocked on a decision any more, only on execution, and a manager-authored executor prompt with pinned acceptance numbers is ready to dispatch. The previous checkpoint (2026-08-25T17:31:19Z) was `EU-04 / FR-YEAR-FIX-01` + `FR-TYPOLOGY-REQ-01`: the ruled remedy ran and was audited against disk — the France manifest now holds **522 of 530** observed years (1550–2010, median 1850, four pre-1677), all resolving to a TABULA French period, the `[OPEN]` debug entry is closed and 12 focused tests pass, with two deviations recorded rather than fixed (a hardcoded `current_year = 2026`; an unreported counts difference that is a population difference, not a source move). France is still `layout_ready_count = 0` on `UNMAPPABLE_RESIDENTIAL_TYPE: 522`, so **`D-EU-04-G` is OPEN and blocking** — `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md`, recommending G1 (dwelling and storey signals must agree, thresholds read off the FR TABULA registry) for a measured 302 typed / 297 with a year. The previous checkpoint (2026-08-25T17:20:50Z) was `EU-04 / FR-PARSE-PROMPT-01`: the ruled remedy for the France year blocker is specified in `prompts/previous/EXECUTOR_PROMPT_EU-04_fr_year_parse_fix_2026-08-25.md` (four tasks, checkpoint after the third, one authorized live IGN call) but not yet executed, and a **second independent French blocker was measured** — all 530 retained French rows carry `building_tag` `Résidentiel`/`Commercial et services`, which `OBSERVED_TAG_TO_TABULA_TYPE` does not map, so recovering the year still leaves France at `layout_ready_count = 0` and a French typology derivation is a new owner ruling. The previous checkpoint (2026-08-25T16:56:39Z) was `EU-04 / FR-YEAR-DIAG-01`: the owner ruled `D-EU-04-E` = E1 (re-acquire France through the existing BD TOPO adapter, live IGN WFS fetch authorized) and `D-EU-04-F` = F2 (defer `GEO-08`), and executing E1 revealed that the France observed construction year is present in the source but destroyed by a parse defect at `openubem/acquisition/bdtopo_fetcher.py:94` — so `GEO-10`/S1–S3 is blocked by a bug, not by a missing data source, and 529 of 530 French buildings already carry an observed dwelling count on disk. The previous checkpoint (2026-08-25T16:34:43Z) was `EU-04 / S0-SMOKE-02` together with `EU-05 / FRED-RULING-01`**: the owner ruled both outstanding fail-closed rows — GB `SyAv` fractional `n_Storey` by half-up rounding (Option A) and France `F_red_temp` as a strictly positive **source multiplier** (Option 1) — and both rulings are verified on disk and under test; the S0 equivalent-envelope EnergyPlus design-day smoke now covers all four residential typologies with a no-severe-diagnostic assertion (European suite 203 passed; whole repo 2,146 passed / 55 skipped). This is the single manager prompt for future sessions.
**Audience:** a future manager session coordinating and carrying out implementation, validation, and evidence
> **Morning checkpoint (2026-08-26T00:02:11Z):** EU-04 S2 C1A remains frozen and audit-accepted at 31 high-completeness buildings; no S2 simulation or energy result exists. D-EU-07-OB-LYO is ruled OB1 (the OneBuilding Lyon-Bron TMYx remains candidate-only). Project-owned CDS credentials and the ERA5 licence are now configured/accepted. Direct ERA5 Lyon-Bron acquisition is in progress through `scripts/acquire_era5_lyon_bron_2023.py`: the UTC boundary day plus January, February, March, and December 2023 archives are acquired; April is `running`; the remaining months must be submitted sequentially because concurrent CDS jobs were rejected. No EPW has been promoted to `weather_registry.json` yet. The next morning action is to poll April, submit May--November one at a time, then run `scripts/convert_era5_lyon_bron_2023_to_epw.py`, DR08 gates 1--4, the national monthly benchmark, and EnergyPlus smoke before any S2 runner is scoped.
> **Weather completion checkpoint (2026-08-26):** All 13 ERA5 archives (2022-12-31 boundary plus January--December 2023) are acquired and converted to `openubem/data/weather/fr_lyon_bron_2023_era5.epw` (SHA-256 `2cf15311b9c6d1124f856d80e6deed5e4a7d6f48389681305b90b6dbee88cc2c`). DR08 gates 1--4 pass: valid header, 8,760-hour continuity, no missing mandatory fields, and physical/solar bounds. DR08 gates 5--6 remain pending: external monthly national benchmark and EnergyPlus smoke. Do not promote the EPW to `weather_registry.json` or launch S2 until those two gates are evidenced.
> **Weather-gate continuation (2026-08-26):** Gate 6 now passes: a one-zone EnergyPlus 23.1 smoke with the Lyon EPW returned code 0, completed successfully, and reported 0 severe errors. Gate 5 is partial: official Lyon-Bron 2023 monthly mean temperatures differ from ERA5 by at most 1.25 K (within the 1.5 K limit), but the station source provides sunshine hours rather than monthly GHI, so the required 10% GHI test is not evidenced. Evidence is in `openubem/outputs/eu_evidence/EU-07/era5_lyon_bron_weather_gates_2026-08-26.md`; registry promotion and S2 remain held pending an authoritative monthly GHI series or an explicit owner ruling.
> **G5-A execution (2026-08-26):** The approved PVGIS/JRC same-coordinate 2023 GHI benchmark was acquired and compared. Eleven months are within the adopted 10% limit; November is 13.8% high relative to PVGIS. Gate 5 therefore remains **NOT PASS** under the unchanged rule. The discrepancy is recorded in the EU-07 evidence file; do not promote the EPW or launch S2 until the owner rules how to handle this measured exception.
> **G5-A ruling and S2 release (2026-08-26):** The owner approved the documented November exception: 11/12 monthly GHI checks pass, annual difference is 3.2%, and November is retained as an explicit deviation. Lyon is now `RULED_PINNED_EXCEPTION` in `openubem/data/weather/weather_registry.json`; gates 1--4 and 6 pass, gate 5 is `PASS_WITH_DOCUMENTED_NOVEMBER_EXCEPTION`. The frozen EU-04 C1A sample is verified at 31 unique buildings with quotas AB/MFH/TH=8 and SFH=7, all `HIGH_MAPPING_INPUT_COMPLETENESS`. S2 execution may now be prepared; no S2 energy result exists yet.
> **Next-session handoff (2026-08-26):** Weather acquisition and release are complete for the Lyon slice. Use `openubem/data/weather/fr_lyon_bron_2023_era5.epw` (SHA-256 `2cf15311b9c6d1124f856d80e6deed5e4a7d6f48389681305b90b6dbee88cc2c`) through the `fr` registry target, which is `RULED_PINNED_EXCEPTION`. Gate evidence is in `openubem/outputs/eu_evidence/EU-07/era5_lyon_bron_weather_gates_2026-08-26.md`; the owner-approved exception is documented in `debugs/docs/DECISION_REQUEST_EU-07_Lyon_gate5_GHI_2026-08-26.md`. Do not reacquire weather or use the rejected OneBuilding TMYx candidate. The frozen S2 input is `openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample.csv` with summary `s2_c1_high_completeness_sample_summary.json`: 31 unique rows, AB/MFH/TH=8 each, SFH=7, all high mapping-input completeness, building_id ordering, no outcome-based selection. `tests/test_eu_weather_registry.py` passes 6/6. The next session owns the S2 runner only: define its annual/short-period EnergyPlus contract, preserve the 31-row manifest and independent geometry-result columns, run the frozen sample, and write retained-campaign evidence. No S2 energy number has been produced yet, and no sample may be re-selected.
**Language rule:** the user may write in French; always answer the user in English. Keep code, documentation, filenames, and technical deliverables in English.
> **Session-capacity continuity warning (2026-08-25):** ⚠ Heads up, you have less than 25% of your 5h limit left. Run `/status` for a breakdown. Before the limit is exhausted, record any completed EU-04 slice in this §19.5 ledger and both walkthrough logs, retain test evidence, and let a new session resume from the newest dated entry. Do not restart completed EU-02 acquisition or earlier EU-04 local contracts.
> **New-session starting point (2026-08-25):** EU-02 is closed. Do not re-run selection or acquisition unless reproducing its evidence. Begin the next unblocked EU-04 geometry slice using the four audited clean manifests in `openubem/outputs/eu02/`, the final gate audit in `openubem/outputs/eu_evidence/X-11/eu02_ns02_gate_audit.json`, and the current EU-04 ledger below. Preserve raw-source census versus model-ready-clean count distinctions.
> **EU-02 final update (2026-08-25T14:26:20Z):** `NS-02` is **MET** and EU-02 acquisition is complete. The final audit at `openubem/outputs/eu_evidence/X-11/eu02_ns02_gate_audit.json` passes for all four selected sites: frozen-schema metadata, non-empty standard artifacts, disjoint manifests, complete endpoint/licence sidecar, and live reconciliation evidence. Raw-source census and model-ready-clean counts remain separately documented where cleaning removes features. Hand off to EU-04 geometry work.
> **EU-02 update (2026-08-25T14:25:13Z):** Bologna T07 is measured and written: 2,188 CTC residential volumes -> 231 dissolved components -> 1,312 CTC-touched cadastral objects; the ruled `rifter_edif_pl` census remains 1,372 objects (1,330 residential candidates), with ISTAT 2011 = 1,010 as cross-check. CTC remains reconciliation-only. The final four-site gate audit is next; `NS-02` remains `NOT_MET` until that evidence is accepted.
> **EU-02 update (2026-08-25T14:24:08Z):** All four selected sites now have live standard artifact sets under `openubem/outputs/eu02/` (clean footprints, residential and excluded manifests, counts, and endpoint/licence sidecar). Madrid/London match their recorded residential counts within one building. Lyon/Bologna retain distinct raw-source census and model-ready-clean counts for the remaining reconciliation; focused acquisition regression passes **67 tests in 2.27 s**. `NS-02` remains `NOT_MET` pending T07/T08 evidence and gate evaluation.
> **EU-02 update (2026-08-25T14:17:44Z):** Removed the obsolete duplicated OSM geometry cleaner. OSM now has one active shared seven-step implementation, supplied with its established overlap resolver and structured logger. Focused acquisition regression passes **66 tests in 2.28 s**. This is local contract evidence only; four live manifests, reconciliation, and final gate evidence remain outstanding.
> **EU-02 update (2026-08-25T11:09:51Z):** OSM now invokes the shared seven-step geometry cleaner, passing its existing overlap resolver and structured logger so multipart identifiers, cleaning sequence, and log records remain unchanged. Focused acquisition regression passes **66 tests in 2.20 s**. This is local contract evidence only; legacy duplicate cleanup, four live manifests, reconciliation, and final gate evidence remain outstanding.
> **EU-02 update (2026-08-25T11:08:41Z):** the shared provenance and quality-flag functions now own OSM's generic-tag, feet-only-height, and overlap-resolution cases; OSM compatibility wrappers delegate without changing the import surface. Focused acquisition regression passes **66 tests in 2.20 s**. The shared geometry-cleaning function and final live-manifest/reconciliation evidence remain outstanding.
> **EU-02 update (2026-08-25T11:07:33Z):** Bologna's CTC reconciliation crosswalk now pins the official 30-value catalogue: `Edificio generico` is the sole residential label and the other 29 values, including an empty description, are explicit non-residential exclusions. Unseen values fail closed. The focused acquisition regression now passes **66 tests in 2.21 s**. This is local source-contract evidence only; EU-02 remains in progress pending the shared geometry/provenance tail, four live manifests, reconciliation, and final gate evidence.
> **EU-02 update (2026-08-25T00:00:00Z):** the frozen 23-column validator and stable three-artifact serializer now have one implementation in `openubem/acquisition/footprint_schema.py`; the OSM compatibility functions delegate to it. Focused acquisition regression (`tests/test_eu02_fetchers.py`, `tests/test_boundary_clip.py`, and `tests/test_osm_fetcher.py`) passes **65 tests in 2.27 s**. This is local contract evidence only; EU-02 remains in progress pending the shared geometry/provenance tail, four live manifests, reconciliation, and final gate evidence.

> **Head box — read this first (2026-08-23, end of day).**
> - **START HERE - EU-04 `S1` is COMPLETE and AUDITED (2026-08-25T19:20:00Z, slice `S1-EXEC-01` + `S1-EXEC-01-AUDIT`). Nothing in this arc is blocked on a decision. Nothing is running. The next action is `S2` scoping.**
> 
>   **What `S1` produced.** The ladder criterion - *"12/12 accounted for; failures classified"* - is **met**. **Axis A** (dwelling-layout status) reproduces the owner-frozen sample exactly: **8** `REFUSED_BY_LAYOUT_CONTRACT`/`NON_CONVEX_FOOTPRINT`, **3** `FALLBACK_PENDING_LAYOUT`/`NARROW_FOOTPRINT_LT_8M`, **1** `DWELLING_LAYOUT_EMITTED` (`AB` `BATIMENT0000000240879449_part0`). **Axis B** (design-day EnergyPlus): **11 `EPLUS_COMPLETED`** (10 `FALLBACK_ONE_ZONE_PER_FLOOR` + the single `EUROPEAN_DWELLING_LAYOUT`) and **1 `EPLUS_FATAL`**. Row 12's party-wall audit passed (`party_face_count=8`, `reciprocal_pair_count=4`); 0 of the 12 hold a courtyard. Regression `pytest -q tests/test_eu_reciprocal_surface_audit.py tests/test_eu_box_generator.py` = **14 passed**. 🔴 **`S1` produced no energy number and must never be quoted as one** - it proves only that the observed-footprint-to-EnergyPlus path runs. Evidence: `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv` (12 rows), `.../s1_smoke/*.err` (12), `scripts/run_eu_s1_smoke.py`.
> 
>   **Three findings are CARRIED and deliberately NOT FIXED** (`S1` was a measurement task; the diagnose-before-remediate rule forbids fixing inside one). Each is registered, and each is a candidate work package, not a loose end:
> 
>   1. 🔴 **Dwelling-layout success is CRS-dependent.** `generate_european_dwelling_layout` rotates about the literal coordinate origin (`openubem/geometry/european_residential.py:504`, `origin=(0.0, 0.0)`) while `audit_european_floor_partition` checks its own output against an **absolute** `topology_tolerance_m2 = 1e-8` (`:643`), so rotation float-noise scales with distance from `(0,0)`. The same building is clean in the manifest's native `EPSG:32631` (~642000/5070000) and fails `AREA_GAP` + `OUTSIDE_FOOTPRINT` in `EPSG:2154` (~852000/6519000) at an `area_error_fraction` of **5.09e-12**. **A census run in Lambert-93 would have reported near-zero emitted layouts for this same corpus.** The executor hit this at its CP-1 and **stopped instead of switching CRS or patching the generator** - the correct move. Ruling: `S1` runs in the **native `EPSG:32631` with no reprojection**, and the *prompt text* was corrected, never the owner-frozen sample (re-picking the 12 would have reintroduced exactly the outcome-based selection `H2` was refused for). Registered `[OPEN]`, ch.5 of `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Candidate remedy: rotate about the footprint centroid and/or make the tolerance footprint-area-relative.
>   2. **The EnergyPlus vertex limit is a real property of this corpus, not a flake.** `BATIMENT0000000240877527_part0`'s exterior ring carries **173 vertices** against the IDD's ~120-vertex `BuildingSurface:Detailed` field limit, so E+ fails during input processing (`** Fatal ** Errors occurred on processing input file`). `build_zones(..., strategy="one_zone_per_floor")` uses `exterior.coords` verbatim, so any dense historic parcel can hit it. Recorded fail-closed as a **named refusal, never an energy result**; registered in **ch.1** of the debug references. Candidate remedy: a vertex-budget simplification with the simplification error recorded per building.
>   3. 🔴 **The single dwelling-level model is ONE FLOOR PLATE, not the stack.** `scripts/run_eu_s1_smoke.py:257` hands the layout to `european_layout_to_zone_specs` at `height_m = 3.0`, giving `zone_count = units_per_floor = 5` - **5 dwellings, not the 6-storey / 28-dwelling building** - while the 11 fallback rows go through `build_zones(num_floors=observed_storeys)` and **are** full stacks. The two axes are therefore **not comparable in vertical extent**, and the dwelling-level path must never be quoted as "a 6-storey dwelling-partitioned building runs". This is a limit of the manager's own executor prompt, not an executor deviation.
> 
>   **First action for a new session:** S2's C1A input sample is formed and audited: 31 high-completeness observed buildings (AB/MFH/TH 8 each; SFH 7), with geometry outcomes retained separately. The next action is **not** a simulation rerun: scope the short-period runner only after an approved/pinned Lyon weather window and CDS access are available. Carry forward, unchanged: **`S3` (96) cannot be typology-balanced for France** - `SFH` caps at **7** in this quarter; **`GEO-08`** Grasshopper parity stays deferred and unclaimed under `D-EU-04-F`; the hardcoded `current_year = 2026` at `openubem/acquisition/bdtopo_fetcher.py:82` stays recorded and unfixed; and `layout_ready` is still a misleading field name (it means *mapping inputs complete*, not *layout generable*) with a rename proposed but not ruled. **Standing lesson from this slice:** when a geometric contract is audited with an **absolute** tolerance, its pass rate is a property of the coordinate system rather than of the buildings - pin the CRS in the contract, or make the tolerance relative.
> - **Superseded framing, kept for the reasoning it records - EU-04 `S1-EXEC-01` as dispatched (2026-08-25T18:48:58Z): `D-EU-04-H` RULED (H1), the 12 FROZEN, executor running.** (The run has since finished; read the bullet above for the result.) The owner adopted H1 verbatim: *"S1 ladder execution proceeds with 12 buildings (3 per typology) selected by the established ladder rules, measuring real corpus yield and classifying all failure modes fail-closed."* Applying that rule - per typology the two lowest-`building_id` **irregular** footprints plus the lowest-`building_id` **simple** one - froze the sample and **corrected a second estimate of mine**: the decision request said "about 4" of the 12 would reach a dwelling-level run; **exactly 1 does** (`AB` `BATIMENT0000000240879449_part0`, 28 dwellings over 6 storeys, 544 m2). The other 11 are **8 `NON_CONVEX_FOOTPRINT` refusals + 3 `NARROW_FOOTPRINT_LT_8M` fallbacks**. That is the honest price of not selecting on the outcome, and it is what H1 bought. **The executor prompt (`prompts/EXECUTOR_PROMPT_EU-04_s1_smoke_2026-08-25.md`) pins two axes that are recorded in separate columns and may never be collapsed into one "passed" count:** *Axis A*, the dwelling-layout status the ruling asked to be classified; *Axis B*, a design-day EnergyPlus smoke whose zones come from the emitted layout where one exists and otherwise from the repository's already-ruled `one_zone_per_floor` strategy (`openubem/geometry/zoning.py:70`). A refused building that completes EnergyPlus is **a whole-floor smoke success and a dwelling-layout failure** - `european_residential.py:89` says a fallback "may never be counted as successful dwelling-level geometry", and that is enforced in the prompt. `S1` produces **no energy number**; it proves the observed-footprint-to-EnergyPlus path runs. Pinned assumptions to carry: floor-to-floor **3.0 m** (S0-consistent geometry constant, not a claim about Lyon) and **courtyard footprints extrude from the exterior ring only**, the hole filled - a pre-existing pipeline simplification, noted per row, not a new decision. Evidence will land at `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv` (12 rows) and `s1_smoke/*.err`.
> - **Latest EU-04 `S1-SCOPING-01` state (2026-08-25T18:30:36Z) — 🔴 `S1` IS BLOCKED AGAIN, on a different thing, and one of my own sentences is the reason it looked unblocked.** Scoping `S1` immediately after the previous bullet, I measured what the layout generator can actually do with the 297 layout-ready French rows: `units_per_floor` from `allocate_european_dwellings` on the observed dwelling and storey counts, then `generate_european_dwelling_layout` on the real footprint, all 297 rows. **It emits for 18 of them: 0 `SFH`, 1 `TH`, 14 `MFH`, 3 `AB`.** 23 fall back (`NARROW_FOOTPRINT_LT_8M` 13, `PARTITION_AUDIT_FAILED` 10) and **256 are refused outright** as non-convex or courtyard-holding — the generator's ruled contract wants a convex, hole-free plate ≥ 8 m wide with ≥ 2.5 m façade contact per dwelling (GEO-01/GEO-04/GEO-09), and a dense historic Lyon quarter simply is not that. **`layout_ready = True` means the mapping inputs are complete. It does not mean a layout can be generated.** **Correction, and it is load-bearing:** the sentence "`S1` (12 buildings, 3 per typology) becomes reachable immediately — every typology clears 3 with a year attached" in `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md` is **wrong**; clearing three *typed* rows is not clearing three *generable* rows, and the owner ruled `G1` partly on it. The `G1` derivation is unaffected (302 typed / 297 dated stands) and nothing downstream used the wrong number, because `S1` had not started. **`D-EU-04-H` is OPEN and blocking** — `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_H_S1_reachability_2026-08-25.md`, evidence `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv` (297 rows). Recommended **H1**: run the ladder's own 12 (3 per typology, 2 irregular + 1 simple, ordered by `building_id`) and classify every failure, because the ladder's acceptance criterion is *"12/12 accounted for; failures classified"*, not "12/12 succeed"; **H2** (form `S1` from the 18 that emit) buys 12 real runs at the price of selecting the sample on the outcome being tested, which this arc has refused everywhere else; **H3** extends the generator to concave/courtyard plates and is the right eventual answer for coverage, but it is a work package, not this slice; **H4** (relax 8 m or 2.5 m) is listed only to be refused. This pass wrote no feature code and changed no test. Proposed follow-up, not part of the ruling: rename `layout_ready`, or add a second explicit field, now that it demonstrably means something narrower than it says.
> - **Latest EU-04 `FR-TYPOLOGY-IMPL-01` state (2026-08-25T18:34:00Z) — the ruled `D-EU-04-G` (G1) is now IMPLEMENTED and AUDITED, and `S1` is unblocked.** T01–T04 ran on two cheap executors with a hard stop at CP-1 before any evidence was rewritten, and the manager audited both checkpoints against the artefacts on disk. `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness_summary.json` now reports **`layout_ready_count` 297** where it reported **0**, `derived_type_counts` for `FR-LYO-HAUTCOEURPENTES` = **7 `SFH` / 21 `TH` / 123 `MFH` / 146 `AB`**, `type_provenance_counts` `DERIVED_BDTOPO_TWO_SIGNAL` **302**, and `UNMAPPABLE_RESIDENTIAL_TYPE` has disappeared from France entirely. Exclusions are **189 `TYPOLOGY_SIGNALS_DISAGREE` + 37 gap-13-14 + 1 + 1 = 228 of 530**; `ES` (1,194), `GB` (1,242) and `IT` (1,220) are byte-identical. European suite **232 passed in 31.53 s**. **Two things to carry forward.** (1) The **233**-exclusion figure that circulated in an execution report is WRONG — superseded by **228**; under `G1` a missing year is not an exclusion reason, because a typed row with no year is still typed, merely not dated (5 such rows). (2) **FINDING — `type_provenance_counts` counts *rows*, not typed rows:** of the 3,884 stamped `OBSERVED_TAG` only **1,313** carry a `building_type`, the rest being typeless rows that never reached a derivation, including all 228 French exclusions. The fail-closed contract holds (no derived row is ever stamped `OBSERVED_TAG`), but **never quote 3,884 as an observed-type total.** Next slice: form `S1` — 12 French buildings, 3 per typology, from the 297 layout-ready rows.
> - **Latest EU-02 acquisition implementation state (2026-08-24T23:25:00Z):** `boundary_clip.write_manifests()` now writes a separate `01_source.json` sidecar with the neighbourhood ID, endpoint, source layer, and licence while preserving the three stable NS-08 manifest artefacts. The Bologna rifter classifier is fail-closed for unseen `tipologia` values. Focused acquisition regression (`tests/test_eu02_fetchers.py`, `tests/test_boundary_clip.py`, and `tests/test_osm_fetcher.py`) passes **65 tests**. This is local contract evidence only: EU-02 remains in progress pending shared-tail consolidation, four live site manifests, reconciliation, and final gate evidence. The append-only progress log is authoritative for newer steps.
> - **EU-02 executor gate — CLOSED 2026-08-24.** [`previous/EXECUTOR_PROMPT_EU-02_neighbourhood_selection_2026-08-24.md`](previous/EXECUTOR_PROMPT_EU-02_neighbourhood_selection_2026-08-24.md) was **executed in-session against live public APIs** on the user's instruction ("c'est ton tâche"), not delegated to an external LLM, so there is no untrusted returned packet to audit. The result is Revision B, next bullet.
> - **Latest EU-02 neighbourhood-selection state (2026-08-24, Revision B) — all four cities are now SELECTED.** Revision A's `NO_SELECTION` for Bologna and Lyon was **resolved, not overridden**, by substituting the residential classifier in those two countries only, on a measured coverage statistic (65.5 % and 61.1 % `building=yes`), with the ranking rule `R1`–`R5` carried over verbatim and the substitution written up in [`outputs/EU02_neighbourhood_selection_2026-08-24/eu02_prereg_selection_rule_v2_amendment.md`](../outputs/EU02_neighbourhood_selection_2026-08-24/eu02_prereg_selection_rule_v2_amendment.md) with an honest timing disclosure. **Italy** now uses **ISTAT 2011 `E3`/`E1`** (60 of 71 screened aree statistiche pass the 0.60 dominance gate, against 2 under OSM); **France** uses **IGN BD TOPO® `usage_1/2`** via the Géoplateforme WFS (11 of 36 quartiers pass, against 0). **SELECTED, all boundary-VERIFIED and checksummed:** `ES-MAD-BERRUGUETE` 1,195 residential / 1,977.5 per km² · `GB-LDN-STDUNSTANS` 1,241 / 1,827.5 (unchanged) · `IT-BOL-GALVANI2` 1,010 / 1,121.5 · `FR-LYO-HAUTCOEURPENTES` 544 / 1,449.6. The **owner released the `N1` 500–600 band on 2026-08-24**, voiding the "closest to 550" tie-break and moving Madrid from Bellas Vistas to the denser Berruguete; Lyon's 544 lands inside the original band with no relaxation. Cross-check: Spearman against Bologna's own families/km² rises from **0.777** (OSM) to **0.914** (ISTAT), and the selected unit moves from 52nd of 85 to 12th of 90. **Two Revision A findings are withdrawn**: "no single Lyon IRIS exceeds 230 residential buildings" (BD TOPO's largest is **513**, `La Plaine Charcot`), and the framing that Italy/France were blocked — they are now the **best-instrumented** countries (BD TOPO gives dwellings, storeys and height at 100 % coverage; ISTAT gives construction period, structural material, storeys and dwelling units), while OSM `start_date` coverage on the Madrid site is **0.0 %**. `NS-02` is `NOT_MET` for the IT and FR sites purely because the repository has **no BD TOPO adapter and no Bologna-ODS adapter**. ISTAT's `E`-column positions were verified by five arithmetic identities against `E3`, which caught an off-by-one first mapping — repeat that check on any re-run. Nothing was acquired into the repository: no footprint manifest, no geometry, no IDF, no simulation. **All three owner rulings are TAKEN under delegation on 2026-08-24** (§7 of the report): `D-EU-02-A` the French unit is the **quartier** `7016` (544 res, 1,449.6 per km², 6,387 dwellings) and **not** the `La Plaine Charcot` IRIS (513 res but 926.2 per km², 1,175 dwellings, 2.05 mean storeys); `D-EU-02-B` Madrid is **Berruguete** (rank 1 of the 28 barrios passing `R1`∧`R3`, storey coverage 0.861 vs Bellas Vistas 0.418); `D-EU-02-C` the size band is **permanent** — `N1` floor **≥ 100** with 500–600 as a preferred target and **no** 1,000 ceiling on `N2`. MVP Table 10, Table 10a `NS-05`, `content/table_9_7_sample_group_ladder.csv`, `content/table_9_7_neighbourhood_selection.csv`, the walkthrough ladder and §5.4/§13 of this prompt were all amended to match. Each ruling is reversible by a later owner ruling that quotes §7. **Nothing is owed by the owner before implementation starts.** The report also gained a self-contained §8 data appendix (all four site rows in full, top-10 rankings per city, bbox + SHA-256) so it can be handed to another session on its own, and one data error was corrected: the Lyon `unit_code` in `eu02_site_measurements_v2.{csv,json}` read `8075` (*Quartier Saxe Roosevelt*) and is now `7016`. Evidence: `outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md` (Revision B), Revision A retained at `debugs/docs/DONE-docs/EU02_neighbourhood_selection_2026-08-24_revA_superseded.md`, `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_bologna_istat.csv`, `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_candidates_lyon_{quartier,iris}_bdtopo.csv`, `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_site_measurements_v2.{csv,json}`, `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/`, `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json`, `openubem/outputs/eu02_selected_neighbourhoods_v2.png`.
> - **EU-02 acquisition plan OPENED 2026-08-24 (this is the next implementation work).** [`EXECUTOR_PROMPT_EU-02_acquisition_adapters_2026-08-24.md`](EXECUTOR_PROMPT_EU-02_acquisition_adapters_2026-08-24.md) is the manager-authored plan that closes `NS-02` at all four selected sites, as slices `X-09`–`X-11` (§19.5). It writes the two missing adapters — **IGN BD TOPO® V3** (FR) and **Comune di Bologna Opendatasoft** (IT) — behind the existing acquisition contract, after first lifting the source-agnostic tail of `osm_fetcher.py` (`_seven_step_clean` → `_assign_provenance` → `_build_quality_flag` → `_validate_schema` → `_serialize`) into a shared `footprint_schema.py` so all three sources emit the identical frozen 23-column schema and the same three artefacts. **One ruling was taken with it, `D-EU-02-D` (§5.4 of the plan):** `NS-02` is satisfied by a new adapter when it lives in `openubem/acquisition/`, is reached through the documented `ingest_buildings` dispatch, passes `validate_schema` untouched, writes the same three `_serialize` artefacts, and records its licence and endpoint — because the gate exists to forbid bespoke one-off scripts, not to freeze the source list; read literally, the IT and FR sites could never pass. Reversible by a later owner ruling quoting that section. **Two further rulings were taken 2026-08-24 so that NOTHING in this plan waits on the owner** — the plan now runs end to end and its three checkpoints are all report-and-continue. `D-EU-02-E` (§5.5 of the plan): at `IT-BOL-GALVANI2` **one building = one `rifter_edif_pl` cadastral object**, **1,372** on the retained boundary; the 2,188 residential CTC candidates are volumetric bodies and dissolve onto it, and the ISTAT **1,010** stays as the selection-time statistic and a reported cross-check. The reason it needed no owner: the other three sites already fix the granularity at one footprint polygon per building (OSM polygon, BD TOPO `batiment`), the cadastral object is Bologna's footprint polygon, and choosing it is the judgement already made elsewhere applied consistently — leaving it open was the only thing that would have made the four per-building EUIs incomparable. T07 still reports all three counts, as a cross-check rather than a question. `D-EU-02-F` (§5.6): the **Métropole de Lyon quartier boundary licence** is a **lookup folded into T05, not a gate** — the `NOT_VERIFIED` status came from the selection session never reading the dataset page's licence field, not from evidence the licence is restrictive; the executor records the exact string and retrieval date and flips it, and if and only if it is not open, retains IGN/INSEE CONTOURS-IRIS (Licence Ouverte / Etalab 2.0) clipped to the same quartier `7016` geometry as the **publication** boundary while keeping the Métropole geometry for **acquisition**, reporting the area delta. This does not re-open `D-EU-02-A`; the selected unit is still quartier `7016`. Both are reversible by a later owner ruling quoting the cited section. No code has been written yet; nothing is acquired.
> - **Latest EU-04 GEO-06 state (2026-08-24T15:14:58Z):** a saved-IDF party-wall auditor now requires every interzone wall to name one reciprocal wall with a back-reference, a different zone, and matching vertices. A reopened two-dwelling fixture has one reciprocal pair; corrupted reference and vertex fixtures fail their named conditions. Focused tests pass **24 tests in 1.47 s** and the complete European suite passes **182 tests in 18.77 s**. This is local saved-IDF audit evidence only, not a European dwelling-stack generator, real-footprint result, Grasshopper parity, sample group, or energy simulation. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo06_reciprocal_party_wall_audit.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo06_reciprocal_party_wall_audit.log`.
> - **Latest EU-04 GEO-04 state (2026-08-24T15:10:55Z):** a local European feasibility gate now treats the ruled narrow-width condition strictly as `<8 m`, using the short side of the minimum rotated rectangle and the stable `NARROW_FOOTPRINT_LT_8M` token. The width sweep (6.0, 7.99, 8.0, and 9.0 m) verifies the boundary; a rotated narrow fixture receives the same decision. A fallback is explicitly one-zone-per-floor and is never reported as emitted dwelling geometry. Focused tests pass **21 tests in 0.10 s** and the complete European suite passes **179 tests in 16.12 s**. This is local feasibility-contract evidence only, not a real-footprint dwelling generator, Grasshopper parity result, sample group, or IDF geometry. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo04_narrow_fallback.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo04_narrow_fallback.log`.
> - **Latest EU-04 GEO-07 Option A state (2026-08-24T14:47:05Z):** the owner ruled that all three GB `SyAv` fractional `n_Storey` values use stable half-up rounding (`3, 4, 4`), while their source floats remain in registry provenance. The plate is derived with the rounded physical storey count so its stack conserves `A_C_Ref`; quotient/remainder dwelling allocations are `[3,2,2]`, `[4,4,3,3]`, and `[5,4,4,4]`. The focused test passes **5 tests in 0.04 s** and the complete European suite passes **172 tests in 19.48 s**. This resolves only the former storey-count authority block; production layout generation, Grasshopper parity, sample groups, and S1-S3 remain pending. Evidence: `debugs/docs/DONE-docs/RESPONSE_TEMPLATE_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`, `openubem/outputs/eu_evidence/EU-04/targeted_geo07_syav_storey_rounding.log`, and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo07_syav_storey_rounding.log`.
> - **Latest EU-04 GEO-03 state (2026-08-24T13:45:29Z):** the complete European suite passes **170 tests in 19.07 s**. The independent supplied-floor-partition audit accepts a valid non-convex L-shaped 80 m² footprint partitioned into five dwellings with zero gap, overlap, and outside area. This is local non-convex-audit evidence only, not a production European layout generator, Grasshopper parity result, sample group, or a resolution of the three GB fractional-storey rows. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo03_geo09_partition_audit.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo03_partition_audit.log`.
> - **Latest EU-04 GEO-02 state (2026-08-24T13:38:47Z):** the complete European suite passes **169 tests in 15.93 s**. The independent supplied-floor-partition audit preserves the clean four-dwelling rectangle's count, union area, and zero gap, overlap, and outside area after a 31° rotation. This is local orientation-invariance evidence only, not a production European layout generator, Grasshopper parity result, sample group, or a resolution of the three GB fractional-storey rows. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo09_partition_audit.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo02_partition_audit.log`.
> - **Latest EU-04 GEO-01/GEO-09 state (2026-08-24T12:51:51Z):** the complete European suite passes **168 tests in 16.39 s**. A fail-closed supplied-floor-partition audit proves a clean axis-aligned 96 m² four-dwelling fixture has zero gap, overlap, and outside area, while named gap, overlap, outside, and count mutations fail. This is local audit-contract evidence only, not a production European layout generator, Grasshopper parity result, sample group, or a resolution of the three GB fractional-storey rows. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo09_partition_audit.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo01_geo09_partition_audit.log`.
> - **Latest EU-05 HVAC-03 state (2026-08-24T12:38:30Z):** the complete European suite passes **162 tests in 15.60 s**. The runnable S0 ES SFH equivalent-envelope fixture completes local EnergyPlus zone sizing and reports a nonzero **16,352.93390 W** design heating load. This is S0 fixture evidence only: it does not promote S1–S3, alter the fail-closed France multiplier row, acquire weather, or submit a campaign. Evidence: `openubem/outputs/eu_evidence/EU-05/targeted_hvac_sizing_design_day.log` and `openubem/outputs/eu_evidence/EU-05/all_european_tests_after_hvac_sizing.log`.
> - **Single-prompt handoff (2026-08-24T11:53:11Z):** this Director prompt is now the sole active, self-contained manager handoff for future sessions. `EXECUTOR_X-01_paste_into_codex.md` is superseded historical material and must not be used or updated. No work-package implementation status changed in this documentation-only consolidation.
> - **Latest EU-05 HVAC-02 state (2026-08-24T09:52:09Z):** the complete European suite passes **161 tests in 18.52 s**. Every ES/GB/IT occupant-campaign row now passes the heating-only IdealLoads, constant-air, and all-convective gain audit. `FR.N.AB.10.Gen.ReEx.001.001` has `F_red_temp=1.0086438144755208`, above the current reduction range; it is fail-closed and analyzed in `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-05_FR-Fred-temp_2026-08-24.md`, not clamped or silently altered. This is local control-contract evidence only.
> - **Latest EU-08 CAMPAIGN-02 state (2026-08-24T09:47:31Z):** the complete European suite passes **156 tests in 14.33 s**. `EU-08` now measures SHA-256 values from each IDF, emitted schedule, and weather file on disk and derives a canonical dependency digest including the EnergyPlus build identity, adapter configuration, and source commit. A cached result is reusable only when legacy output markers also pass, status is `success`, and the digest exactly matches. This is local fixture-contract evidence; no campaign was submitted. Evidence: `openubem/outputs/eu_evidence/EU-08/all_european_tests_after_dependency_digest_cache.log`.
> - **Latest EU-04 GEO-07 state (2026-08-24T01:28:08Z):** the complete European suite passes **154 tests in 14.10 s**. A D-EU-01/D-EU-04 allocation kernel now half-up rounds `n_Apartment`, allocates exact quotient/remainder totals across integral storeys, and places the ruled 6% core outside the conditioned plate only at ≥2 dwellings/storey. Three GB `SyAv` rows have non-integer `n_Storey`, for which no rounding rule was approved; they fail closed. Decision analysis: `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`. Continue independent work; do not model those rows yet.
> - **Latest EU-09 V8.d state (2026-08-24T01:24:42Z):** the complete European suite passes **150 tests in 14.32 s**. `EU-09` now independently reads area, volume, and integral storey count from each archetype's own retained S0 IDF; it also requires that IDF's saved surfaces to identify the same archetype. Reused paths, swapped files, missing fields, and mismatches fail. This closes V8.d locally. It is fixture-contract evidence only; retained campaign artefacts remain pending. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8d_saved_idf_audit.log`.
> - **Latest EU-09 V8.c state (2026-08-24T01:04:08Z):** the complete European suite passes **149 tests in 14.23 s**. `EU-09` moves all fixed G8.1–G8.6/G8.10 limits into one immutable imported module; G8.7 remains a required archetype-specific band input, not a copied generic threshold. This closes V8.c locally. Retained campaign artefacts and V8.d per-archetype retained-IDF audit remain pending and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8c_band_source.log`.
> - **Latest EU-10 dossier-contract state (2026-08-24T01:02:34Z):** the complete European suite passes **147 tests in 14.14 s**. `EU-10` now writes a fail-closed machine-readable dossier report only when exactly G8.0–G8.16 pass at hard severity and both campaign-manifest/result-bundle SHA-256 digests are measured. Its explicit evidence scope separates `local_fixture_contract` from `retained_campaign`; a schema fixture cannot be presented as campaign evidence. Retained campaign artefacts and final dossier evidence remain pending. Evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_dossier_contract.log`.
> - **Latest EU-10 retained-output state (2026-08-24T01:00:50Z):** the complete European suite passes **145 tests in 14.92 s**. `EU-10` now extracts the four ruled simulated end uses read-only from retained `eplusout.csv`: it requires `Date/Time`, each hourly J output, and a complete 8,760-row non-leap calendar before reconstructing the validated weather-window cell record. It never reads facility/service meters or mixes TABULA DHW into a time series. This is fixture-contract evidence only; campaign output capture and dossier export remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_retained_csv_extraction.log`.
> - **Latest EU-09 perturbation-coverage state (2026-08-24T00:57:08Z):** the complete European suite passes **143 tests in 14.05 s**. `EU-09` exports the frozen P01–P12 Table 17 matrix and locally cross-tabs every specified required-fail/required-clean transition, including G8.12 assignment/value arms and the all-clean null probe. A missing probe, a failure that remains clean, or a clean checkpoint that turns dirty fails the contract. This is fixture-contract evidence only: retained campaign artefacts plus the V8.c band source and V8.d retained-input audit remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_perturbation_coverage.log`.
> - **Latest superseding implementation state (2026-08-23T23:42:00Z):** `X-01`, `X-02`, `X-03`, `X-04`, `X-05`, `X-06`, and `X-08` are `LOCAL_PASS`; the complete European suite passes **114 tests in 13.25 s**. `EU-06` is `PARTIAL`: 7/7 focused tests prove an external, non-fractional `Schedule:File` f=0 control path and annual 3 W/m² conservation; its injected f>0 path remains correctly blocked by the upstream chaining rule. `EU-08` is `PARTIAL`: a 3/3-tested deterministic 510-row campaign plan creates Q3=102 controls and Q4=408 injected rows, but it cannot submit or report a run. `X-07` is `PARTIAL`: its deterministic `RULED_NOT_PINNED` registry and offline DR08 gates 1–4 pass **6/6** tests; live ERA5 acquisition, CDS-served licence capture, gates 5–6, and diary-window pinning remain blocked on CDS credentials and source data.
> - **Latest EU-09 continuation state (2026-08-24T00:16:55Z):** the complete European suite passes **117 tests in 16.09 s**. `EU-09` is `PARTIAL`: its 3 focused tests cover pre-submission G8.0/G8.8/G8.9/G8.14/G8.16 with a clean null fixture and named corruptions. Meter, saved-IDF, warning, geometry, and numerical-output gates are still unimplemented and must not be claimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_pre_submission_gates.log`.
> - **Latest EU-09 meter continuation state (2026-08-24T00:19:33Z):** the complete European suite passes **121 tests in 16.52 s**. `EU-09` adds 4 focused MDD-derived G8.10/G8.11 meter tests: legacy `Gas:Facility` fails both name and balance gates, while a zero end use fails balance only. Saved-IDF, warning, geometry, and numerical-output gates remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_meter_gates.log`.
> - **Latest EU-09 saved-IDF continuation state (2026-08-24T00:21:15Z):** the complete European suite passes **122 tests in 17.28 s**. `EU-09` adds independent G8.12/G8.13 saved-artifact auditing: a wrong consuming-object schedule fails G8.12 and `Interpolate to Timestep = Yes` fails G8.13. Warning, geometry, and numerical-output gates remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_saved_idf_gates.log`.
> - **Latest EU-09 warning continuation state (2026-08-24T00:22:36Z):** the complete European suite passes **125 tests in 16.45 s**. `EU-09` adds G8.15 warning-kind triage: a single unclassified warning fails even amid repeated benign warnings, and severe/fatal diagnostics fail hard. Geometry and numerical-output gates remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_warning_gate.log`.
> - **Latest EU-09 reproducibility continuation state (2026-08-24T00:28:47Z):** the complete European suite passes **127 tests in 14.12 s**. `EU-09` adds same-cell G8.1–G8.4 NMBE/CV(RMSE) scoring at the fixed monthly/hourly thresholds; the clean rerun passes and the 1.2 scale mutation fails G8.1/G8.3. G8.5–G8.7 peak/geometry gates remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_reproducibility_gates.log`.
> - **Latest EU-10 accounting continuation state (2026-08-24T00:30:12Z):** the complete European suite passes **129 tests in 16.43 s**. `EU-10` adds the ruled `four_end_use_tabula_dhw` accounting guard: four simulated end uses remain separate, `q_w_nd` is one labelled DHW post-processing column, and physical service loads are rejected to prevent double counting. Extraction, aggregation, and dossier export remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_four_end_use_accounting.log`.
> - **Latest EU-09 peak/geometry continuation state (2026-08-24T00:34:45Z):** the complete European suite passes **135 tests in 13.97 s**. `EU-09` now has local contracts for G8.0–G8.16: G8.5 uses the parent’s ±15% peak magnitude rule, G8.6 the ≤1 h timing rule against a mandatory named series, and G8.7 grades the as-modelled EUI band while making empirical comparison informational only; it also rejects a mismatched geometry denominator. The >15% peak, two-hour shift, and 1.5× wrong-area mutations fail. This is still not campaign evidence: retained artefacts and the complete V8 coverage cross-tab remain pending. Evidence: `openubem/outputs/eu_evidence/EU-09/all_european_tests_after_peak_geometry_gates.log`.
> - **Latest EU-10 result-record continuation state (2026-08-24T00:36:51Z):** the complete European suite passes **137 tests in 16.83 s**. `EU-10` now requires a self-describing cell result with weather identity/year, denominator, coefficient-table checksum, annual four-end-use accounting, 12 monthly and 8,760 hourly simulated-energy values that close, and a derived peak. TABULA DHW remains labelled post-processing, never a simulated time-series load. Retained-output extraction, aggregation, and dossier export remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_record_contract.log`.
> - **Latest EU-10 aggregation continuation state (2026-08-24T00:50:42Z):** the complete European suite passes **139 tests in 18.65 s**. `EU-10` corrects the result field to an explicit approved weather window, then aggregates only cells from the same fold/window and exports a deterministic JSON bundle. It rejects cross-weather mixing and still keeps TABULA DHW outside simulated time series. Retained-output extraction and dossier export remain unimplemented and unclaimed. Evidence: `openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_aggregation.log`.
> - **Tree:** `HEAD = fda5336`, dirty: the two arc documents, `content/README.md`, `content/walkthrough_progress_log.csv`, this prompt, and the untracked `debugs/` folder. The user commits; you do not.
> - **Current implementation state (supersedes the handoff wording above):** `X-01`, `X-02`, `X-03`, and `X-08` are local passes. `X-04`, `X-05`, and `X-06` are partial: R5/R7 pass while R3 remains a strict expected failure; X-05 has a passing four-type D-EU-01 box plan and exact source-coefficient readback; X-06 has passing saved-IDF heating, air, gain, no-cooling, and `F_red_temp` control emission. The box surfaces remain to be emitted. `X-07` has its approved dependencies installed but remains blocked for live ERA5 retrieval by absent CDS credentials. The append-only walkthrough log is authoritative for timestamps and evidence paths.
> - **What is true:** every claim in MVP §9.2 was re-verified against the code on 2026-08-23; nothing European exists under `openubem/data/construction/` (only `ashrae_90_1_2019.json` + `PROVENANCE.md`); the schedule writer emits `Schedule:Compact`; no G8 gate is implemented.
> - **What changed today (v1.3):** the parent's own 102-archetype parameter tables were read for the first time — see §4.2 for the eight facts that move the implementation. The most consequential: **all 102 archetypes use TABULA's EU boundary-condition set** (`c_m = 45`, `n_air_use = 0.4`, `phi_int = 3`, `θ_i = 20`), so several country-specific values in the older MVP/walkthrough text are *national* rows the campaign does not use; they are superseded in place, not deleted.
> - **Continuation rule for a fresh session:** do **not** restart historical slice `X-01`; it is complete. This file is the **only active handoff prompt**. Start from the current ledger in §19.5 and the append-only log, then continue bounded, evidence-led local work. No Speed work is authorised.
> - **Later the same evening (§4.3):** the user ruled *"vas-y résoudre maintenant"* on the open parent decisions. **Eight are now RULED** from the calculator workbook's cached values (`debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`, MVP §11.12 Table 20); **four are OWED to deep-research briefs** `DeepResearch/DR08`–`DR11` (weather sources/licences; TABULA licence + France registry; open EPC/cadastre data + neighbourhood candidates; TABULA→dynamic translation review); **one stays BLOCKED upstream** (Step 7 chaining rule, `f>0` only). The briefs are to be run by the user in a deep-research tool and their reports source-verified before any number enters the MVP.
> - **Closures (2026-08-23, night):** the user ran DR08–DR11 and the reports were audited and **ACCEPTED** (`DeepResearch/README.md` §Acceptance Record; caveats there bind). **D-EU-05/08/10/11 are CLOSED and D-EU-01/02/03/07 VALIDATED** — MVP §11.13 (Table 21) supersedes Table 20's status column; the decision record carries a closure addendum. Highlights: ERA5/C3S weather (publication-compatible, redistributable), stations Madrid/London/Bologna confirmed, six-gate EPW checklist adopted into EU-07 (slice **X-07**); TABULA publication **unblocked** with the mandatory `IEE Projects TABULA + EPISCOPE (www.episcope.eu)` attribution (clause re-verified live; X-02 files it, licence field `VERIFIED`); fourth city = **Lyon**, city datasets/crosswalks/candidates pinned (GB age-band straddles carry `PERIOD_STRADDLE_*` tokens); France = **40 `FR.N` rows**, 10 `FR.OPHM` excluded (slice **X-08**); DR11 overturned nothing (6 Standard, 4 Acceptable-with-caveat) and its three numeric fixtures join X-04. **The arc's only remaining block is D-EU-09** (upstream chaining rule, `f>0` cells and Q4 only) — everything else is pure execution.
> - **Do not:** submit cluster jobs; edit MVP §9.2; reintroduce any withdrawn figure (§18); treat a Q1/Q2 TMY smoke EUI as a baseline (MVP §11.6 rule 3); quote a DR10 neighbourhood count as a project number (candidates only — the project computes its own counts under `NS-03`/`NS-05`); quote DR11 bias magnitudes as project measurements (dossier caveat text only).

---

## 0. How to use this prompt

You are the technical director for the European-locations simulation arc. Your job is to preserve the scientific contract, establish the true repository state, direct implementation in auditable increments, and refuse to declare success without raw evidence.

At the start of a new session:

1. Read this prompt completely.
2. Read the authoritative documents in the order given below.
3. Inspect the current code, tests, working tree, and available evidence before describing status.
4. Separate clearly what is **documented**, **implemented**, **tested locally**, **submitted to Speed**, and **scientifically accepted**.
5. Report the verified state in plain English, then advance only the work the user has authorized.

The current documentation is approval of a design, not authorization to submit cluster work. Never submit a Speed job, launch a costly campaign, or alter an external system unless the current user request explicitly authorizes that action.

Do not assume this prompt remains perfectly current. Repository code and newly produced evidence may supersede its status statements. Verify rather than repeat.

---

## 1. Mission and scientific outcome

Prepare and validate OpenUBEM's residential building/neighbourhood and baseline simulation pipeline for four European populations:

- Spain (`ES`);
- England-limited TABULA stock represented by the `GB` country code, with the United Kingdom survey fold kept conceptually distinct;
- Italy (`IT`).
- France (`FR`).

Integrate the GSSCanada occupant-presence workflow for Spain, England-limited `GB`, and Italy. France-specific occupant diaries, held-out-fold logic, and non-zero occupant-effect schedules are a future branch; this deferral does not remove France from current building preparation or controlled baseline simulation work.

The current ES/GB/IT occupant campaign combines:

- 102 national building archetypes: 24 Spain + 36 England/GB + 42 Italy;
- 22 diary time bands;
- five occupant-effect levels: `f ∈ {0.00, 0.15, 0.30, 0.50, 1.00}`;
- occupant-derived `Schedule:File` inputs;
- country-appropriate weather aligned with the diary fieldwork period;
- an auditable EnergyPlus execution and post-processing chain;
- optional Speed HPC execution using controlled SLURM arrays.

The ES/GB/IT occupant design requires **510 annual simulations per weather specification**, including the 102 `f=0` controls. The controls are part of the 510 total; do not report 612 runs or 510 plus another 102 controls. France baseline cases use a separate manifest and denominator whose size remains `NOT_AUDITED` until the French physical archetype registry is accepted.

The campaign is not complete merely because EnergyPlus returns zero. It is complete only when inputs, assignments, outputs, accounting, comparisons, and failure-detection gates are supported by retained evidence.

Neighbourhood-scale `N1`/`N2` work uses one real contiguous dense residential neighbourhood per selected study location, acquired through OpenUBEM's established address, coordinate, bounding-box, or OSM-XML inputs. The `N1` floor is **≥ 100** post-filter residential buildings with 500–600 as a preferred target, and `N2` has no 1,000-building ceiling (amended 2026-08-24, ruling `D-EU-02-C`). The counts refer to residential buildings remaining inside the declared boundary after filtering, not a disconnected citywide sample.

---

## 2. Authority and source precedence

Use this precedence when sources disagree:

1. The parent GSSCanada Step 8 specification and its validation document:
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\4thJ_08_bemSimulation.md`
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\4thJ_08_bemSimulation_val.md`
2. The current OpenUBEM code and tests at the revision actually under review.
3. The Step 8 implementation document:
   - `C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\Step8_docs\IMP_step8\4thJ_08_bemSimulation_IMP.md`
4. Evidence and research in the Step 8 implementation folders:
   - `...\IMP_step8\resources`
   - `...\IMP_step8\DeepResearch`
   - `...\IMP_step8\extracted_scripts`
   - `...\IMP_step8\outputs`
5. Illustrative examples in older implementation prose.

For France regulatory context, use the current official RE2020/Th-BCE 2020 and DPE sources linked from MVP Table 2, plus the TABULA/EPISCOPE France country material. Candidate France values remain unaccepted until row-level provenance and local tests exist.

For day-to-day work, the additive correction sections in the two local planning documents are the active working specification:

- `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md`
- `docs/docs_ACTIVE/europeanLocations/WALKTHROUGH_european_locations.md`

Earlier sections in those documents remain as historical design material. Where an addendum labels an earlier command, API, count, or assumption as illustrative or superseded, follow the addendum.

---

## 3. Required reading order

Read only what is needed for the current task, but do not implement before understanding the relevant contract.

1. This director prompt.
2. The status notices and Sections 9–**11** of `MVP_european_locations.md` (§11 is the v1.3 source-alignment addendum: Tables 13–19).
3. The status notices and Sections 9–**12** of `WALKTHROUGH_european_locations.md` (§9.3.1 parent-table reconciliation; §12 executor contract and slices X-01–X-03).
3a. `Step8_docs/outputs_step8/archetype_parameter_provenance.md` §3–§6 and §11 — the honesty clause, the exclusion rules, the open decisions, and the weather ruling. Twenty minutes; it is the document the earlier arc text had not read.
4. `docs/docs_ACTIVE/europeanLocations/content/README.md` for reusable figure/table sources.
5. The parent and validation documents named in Section 2.
6. `docs/docs_DONE/SETUP/parallelProcessing/parallel_idf_prep_detailed.md`.
7. `scripts/cluster/README.md` and the current fleet submission scripts, including:
   - `scripts/cluster/submit_fleet.sbatch`
   - `scripts/cluster/submit_fleet_t08.sbatch`
8. The current modules and tests that own ingestion, imputation, IDF creation, schedules, execution, and result reconstruction.

When a document refers to an API, confirm the actual import path and signature in the current tree. Do not create compatibility code around an example API that never existed.

---

## 4. Verified handoff state

Treat the following as the last documented audit state, then re-check it:

- OpenUBEM is version `0.1.0` and remains primarily North-American in its current assumptions.
- The European implementation documents have been reviewed and improved additively. Existing material was not deleted.
- The MVP is the principal technical specification. The walkthrough is the ordered task/runbook document and owns the append-only progress log.
- Reusable figure/table sources are registered under `docs/docs_ACTIVE/europeanLocations/content/`; Markdown and these source assets are authoritative. PDF output is optional and not part of acceptance unless a future user request restores it.
- France is current scope for residential filtering, registry preparation, geometry, IDFs, weather, and controlled baseline physical simulation. Only its occupant-driven schedule branch is deferred.
- The European adapters, datasets, full tests, and production campaign described by those documents have not been demonstrated as implemented.
- No Speed production campaign is known to have been run for this arc.
- Expected production files such as Spanish, GB, Italian, and French TABULA archetype resources and European load/schedule resources were absent at the audit point.
- The current schedule writer used DOE-style `Schedule:Compact`; the European occupant contract requires a real external `Schedule:File` path.
- Current parallel neighbourhood execution uses local `joblib` behavior rather than being a ready-made SLURM campaign CLI.
- Older examples mentioning `IDFModelBuilder`, `reconstruct_eui`, or `fetch_osm_buildings` are not reliable descriptions of the current public API.
- Relevant current APIs observed during the audit included `ingest_buildings`, `impute_missing(gdf, cfg, targets, rng)`, `BuildingIDF`/`run_step3`, `run_neighbourhood`, and `reconstruct_frame`. Reconfirm names and signatures before use.
- Existing result reconstruction contains US-oriented assumptions and is normally disabled when service loads are modeled physically. A European implementation must choose one accounting path and prevent double counting.
- **(v1.3)** On the GSSCanada side, `Step8_docs/outputs_step8/archetype_parameters_{es,uk,it}.csv` and `archetype_parameter_provenance.md` exist (built 2026-08-21, 24/36/42 rows, 44 columns, raw workbooks pinned under `outputs_step8/raw/`). Nothing under `outputs_step8/` is an IDF, a weather file, a control run, or a gate result; the parent's own status line says so (`4thJ_08_bemSimulation.md` line 10).

At every handoff, classify each claim with one of these states:

- `DOCUMENTED`
- `IMPLEMENTED_NOT_TESTED`
- `LOCAL_PASS`
- `SPEED_SUBMITTED`
- `SPEED_COMPLETE_UNAUDITED`
- `ACCEPTED`
- `NOT_RUN`
- `BLOCKED`

Never convert absence of evidence, an empty parser result, or a successful command wrapper into `PASS`.

### 4.1 Citation audit — closed 2026-08-23

A source-verification pass compared every numeric claim attributed to *Iseri et al. (2025)* in the two
arc documents against the published paper and the four GSSCanada reference folders. **Nine
attributions failed verification**; all were remediated under
[`debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md`](../debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md)
(tasks T01–T07, CP-1 and CP-2 both satisfied, plan `CLOSED`). The five rulings that governed the
remediation are recorded in
[`debugs/docs/DONE-docs/DECISIONS_pending-rulings-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_pending-rulings-2026-08-23.md).

What a future director must carry forward:

- **The Ankara sample is 593 residential buildings of 642 in the study area, and 6,458 dwelling
  units.** The figure `277 buildings` — previously in both documents — appears in no source and is
  contradicted by the paper and by the raw data. It must never reappear.
- **Three figures were recomputed from the raw dataset** `IMP_step8/resources/AllV{1,2,3,4}_updated2023June.csv`,
  identically across all four versions: 593 distinct buildings (`parcelUBEM` × `blockUBEM`), mean
  dwelling floor area **109.11 m²**, range **18.70–434.80 m²**, and vertical-position counts
  **1,667 ground / 3,450 middle / 1,341 top**. The recomputed building count matches the paper
  exactly, which is what establishes those files as the genuine dataset behind the publication.
- **`87.3 m²` and `32–215 m²` are not merely uncited — they are wrong**, contradicted by the raw
  data. Same for `277` and `1,444 floors`.
- **`63.61`, `15.54`, `75.5%`, `3.2×`, `213.20`, `85.70`, `+148.8%`, `0.817`, `+44.6%` are not in the
  published paper.** They are computed in `IMP_step8/outputs/simulation_results_analysis_report.md`,
  a 2026-08-22 re-analysis of the paper's own simulation data. Cite that report — see §18.1.
- **`75.5%` is a standard-deviation ratio, not a variance ratio.** The same data expressed as
  variance give ≈94%. Say "standard deviation".
- **Four geometry-pipeline diagnostics remain `UNSOURCED` and cannot be recovered**: subdivision
  success rate, fallback rate, area-conservation error, and facade-contact pass rate. The result
  CSVs hold simulation outputs only, not generator diagnostics. Their European equivalents must be
  *measured* through the `GEO-01`–`GEO-10` matrix in MVP §4.8 — never inherited from Ankara.
- **Two claims were withdrawn for lack of any source**: the corner-unit heating penalty
  (`25–40%`) and the stair-core adjacent-dwelling demand reduction (`8–15%`). The physical
  mechanisms are retained; the magnitudes are not. The nearest sourced quantity for the second is
  30–50% moderation of *party-wall transmission losses* (`DR07` row 8) — a different quantity, not a
  substitute.
- **MVP §9.2 was re-verified true in full** (fifteen capability claims against the repository) and
  must not be edited without a fresh code audit.
- **Assets exception**: `content/` holds authored document assets, not pipeline figure outputs;
  pipeline outputs still go to `openubem/outputs/` flat. Recorded in `content/README.md` under
  ruling Q3-B.

Standing rule from this audit: **a number that reads as empirical validation is not evidence until
its source file and line are named.** Search the paper PDF, then `IMP_step8/outputs/`, then
`IMP_step8/DeepResearch/`, then `IMP_step8/resources/`, and record where it was found. Absence from
all four is a finding, not a formatting problem.

### 4.2 Source-alignment pass — closed 2026-08-23 (v1.3)

<!-- SEC:source-alignment-pass-2026-08-23 -->

The arc documents had been written from the tier-3 implementation document and the tier-4 research
syntheses. On 2026-08-23 the **tier-1** authorities were read in full for the first time —
`4thJ_08_bemSimulation.md` (529 lines), `4thJ_08_bemSimulation_val.md`,
`outputs_step8/archetype_parameter_provenance.md`, and the three parameter tables, whose column values
were re-read with a CSV reader. Eight facts moved the implementation; all are recorded in MVP §11 with
file and line, and each earlier passage they supersede carries an inline `v1.3` note (nothing deleted):

1. **The 102-archetype parameter tables already exist** — `outputs_step8/archetype_parameters_{es,uk,it}.csv`,
   24/36/42 data rows + three trailing `#` comment lines, 44 columns, built by `tools/4thJ_step8_tabula.py`
   from the two pinned workbooks. `EU-01` consumes and reconciles them (MVP §11.3, Table 14);
   re-deriving from the workbooks is the independent check, not the primary path.
2. **All 102 rows point at the EU boundary-condition set** (`EU.SUH` for SFH/TH, `EU.MUH` for MFH/AB):
   `θ_i = 20 °C`, `F_red_htr = 0.9/0.8` (SUH) and `0.95/0.85` (MUH), `n_air_use = 0.4 h⁻¹`,
   `phi_int = 3 W/m²`, `c_m = 45 Wh/(m²·K)` — identical in every fold (MVP Table 13). The
   country-specific ventilation rates (0.40/0.59/0.30) in MVP §2.2.2 and walkthrough §5.4, and the
   country-specific `c_m` (ES 50 / IT 87 / GB 32.8) in MVP §2.3.2, are TABULA *national* rows the
   parent ruling (`FINDING 57`) deliberately does not use, because they are country-correlated and
   confounded with the held-out-fold signal. Ruling Q5-A is unaffected: §2.3.2 stands as a declared
   mapping decision, but `EU-03`/`EU-05` realise the EU values.
3. **The 22 construction-year bands are listed verbatim** with year boundaries (MVP Table 15). The
   Spanish label is `CTE-79`, never `NBE-CT-79`. The walkthrough's §2.1 example and §4.1
   `map_construction_vintage` contradict the bands and are marked illustrative; the real
   `kbem_ankara_pipeline.py` function returns Turkish 1960/1980/2000 bins.
4. **The folds do not share one archetype structure**: ES 24/24 complete grid; GB 29/32 with parallel
   parameterisations (`.Gen` and `.Detached`) and merged periods; IT 42/48 with composite types
   (`MFH-AB`, `SFH-TH`) and periods. Which row represents a cell, and the 3 empty GB / 6 empty IT
   cells, is parent open decision §6.4 — **not taken** (MVP §11.5, Table 16). The 510 count is a count
   of table rows, not of grid cells.
5. **Weather is ruled, not acquired**: `es` 2009–2010, `uk` 2014–2015, `it` 2013–2014, actual
   meteorological year of each fold's fieldwork window. Three items are owed (fieldwork calendars →
   twelve definite months; a licence permitting *published* derived results; a station) and **no
   weather-driven number may be quoted until they are on disk — not even a provisional TMY one**
   (MVP §11.6). Q1/Q2 smoke runs on a TMY carry `weather_status: "SMOKE_TMY"` and are never baselines.
6. **Diary facts for the schedule adapter**: mean at-home 71.4 % of the day; **1,320 diaries (1.802 %)
   have zero at-home minutes** (`uk` 2.927 %, `es` 1.641 %, `it` 1.417 %) and must be an explicit
   branch, not a rejection (MVP §11.7). **The chaining rule (open decision 14) blocks every `f>0`
   cell**; `f=0` (Q1–Q3, FR-B) does not depend on it.
7. **The twelve-row perturbation matrix and the seven V8 guards are itemised** (MVP Tables 17–18),
   with the EnergyPlus-version note for the `Gas:Facility` mutation (valid name in 23.1 is
   `NaturalGas:Facility`) and the sentence that must accompany every G8.1–G8.4 report.
8. **Parent open decisions are mapped to work packages** (MVP Table 19): §6.1 geometry box, §6.3 layer
   build-up, §6.4 archetype selection, §7 licence, decision 14 chaining — all OPEN; §6.2 zoning, §6.5
   `phi_int`, §6.6 weather — RULED.

Standing lesson added by this pass: **read the parent's own artefacts before the parent's
illustrations.** The tier-3 document presented Madrid/London/Bologna, ERA5, E+ 9.2, hydronic plant
curves and national ventilation rates as settled; the tier-1 rulings and tables settle none of them
and contradict two. When a value in this arc has a country suffix, ask whether the campaign actually
uses the national row — on the EU set, it does not.

### 4.3 Parent open items ruled under delegation — 2026-08-23 (evening)

<!-- SEC:rulings-under-delegation-2026-08-23 -->

Asked why the open parent decisions should wait, the user ruled *"vas-y résoudre maintenant"*. The
director opened `tabula-calculator.xlsx` (`Calc.Set.Building`, cached values, `openpyxl`) for the
102 archetype keys and found that TABULA itself settles most of what the parent had listed as "ours
to assume": `n_Apartment` (dwellings per archetype), `g_gl_n_Window_1`, per-row `n_air_infiltration`
(0.05–0.4 on top of `n_air_use = 0.4`), `b_Transmission_*` factors, `delta_U_ThermalBridging`
("supplement to all U-values"), and a per-archetype `F_red_temp` (0.80–0.99). Extraction filed as
`debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv`; rulings in
`debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`; one-line table in MVP §11.12 (Table 20).

| ID | Ruling | Status |
|---|---|---|
| D-EU-01 | Box **from** TABULA areas; faces N/E/S/W literal; dwellings = `n_Apartment`; core outside `A_C_Ref` | RULED |
| D-EU-02 | Mass-less `NoMass` envelope at `U + ΔU_tb`; all mass = one `InternalMass` = `c_m`·A; `b = 0.5` via `OtherSideCoefficients`; `SHGC = g_gl_n` | RULED |
| D-EU-03 | Air change = `n_air_use + n_air_infiltration` (0.45–0.8 h⁻¹ per archetype) — **corrects the morning's "0.4 for every cell"** | RULED |
| D-EU-04 | All 102 rows run; deterministic observed-building mapping; ambiguity → exclusion; empty cell → nearest older band; non-integer `n_Apartment` rounded | RULED |
| D-EU-05 | Weather rules (12-month rule, ERA5-derived AMY candidate, station rule); files/licence/station confirmation OWED | RULES RULED → **DR08** → **CLOSED 2026-08-23** (stations confirmed; acquisition = X-07) |
| D-EU-06 | EUI accounting = four-end-use mode, DHW from TABULA `q_w_nd` | RULED |
| D-EU-07 | `OtherEquipment` all-convective gain; no cooling; `F_red_temp` as U and air-change multiplier | RULED |
| D-EU-08 | TABULA licence: internal use now, publication blocked until text filed | PROCESS RULED → **DR09 A** → **CLOSED 2026-08-23** (publication permitted with attribution; X-02 files the verbatim text) |
| D-EU-09 | Chaining rule — Step 7 experiment, not rulable here | BLOCKED upstream (`f>0` only) — **the arc's sole remaining block**; experiment protocol issued to the parent 2026-08-23 as §10 of `GSSCanada…\IMP_step8\4thJ_08_bemSimulation_IMP.md` (unblocks when the frozen rule + spread table are filed back) |
| D-EU-10 | Density metric ruled; datasets and candidate lists OWED | SHAPE RULED → **DR10** → **CLOSED 2026-08-23** (Lyon; datasets/crosswalks pinned; final unit by own counts) |
| D-EU-11 | France registry | OWED → **DR09 B** → **CLOSED 2026-08-23** (40 `FR.N` rows; `FR.OPHM` excluded; X-08 re-derives) |

Deciding principle, to reuse when a new gap appears: *reproduce TABULA's own monthly balance as
literally as a dynamic engine can, declare every assumption, make it a one-line sensitivity later.*
It yields two per-archetype read-back assertions (MVP §11.12) that tie every IDF to TABULA's own
`h_Transmission` and `h_Ventilation` — use them as EU-03/EU-05 acceptance gates.

The user may overrule any ruling with `D-EU-nn: overruled → <rule>`; record the overruling in the
decision record and in MVP Table 20 before any slice implements it.

**Deep-research briefs** (`docs/docs_ACTIVE/europeanLocations/DeepResearch/`, format of the parent
dossier; two files per topic: `_brief.md` written here, report saved next to it unchanged): DR08
weather sources and licences; DR09 TABULA licence + France subset; DR10 open building data +
neighbourhood candidates; DR11 TABULA→dynamic translation review of D-EU-01/02/03/07. When a report
comes back: open every cited source for each number the arc will use, mark the report `accepted` in
`DeepResearch/README.md` with the date, then and only then let a slice consume it.

**Done 2026-08-23 (night): all four reports returned and ACCEPTED.** Verdicts + binding caveats:
`DeepResearch/README.md` §Acceptance Record. Closures: decision-record closure addendum and MVP
§11.13 (Table 21 supersedes Table 20's status column). Director's live spot-checks: the episcope.eu
third-party clause matches DR09 verbatim; the DR08 Copernicus licence-PDF URL is stale (404) but
the current CDS ERA5 page states plain CC-BY — verdict unchanged, X-07 files the text served at
download time. Only **D-EU-09** remains blocked, and it gates `f>0` cells and Q4 only.

---

## 5. Frozen scientific decisions

Do not reopen these decisions without a documented reason and explicit approval:

1. The physical building/neighbourhood populations are Spain, England-limited TABULA/GB, Italy, and France. Do not silently generalize the GB stock to every UK nation.
2. France is current scope for residential preparation and controlled baseline simulations. France-specific diaries, held-out-fold logic, and non-zero occupant schedules remain future scope.
3. The ES/GB/IT occupant-campaign archetype counts are 24, 36, and 42, totaling 102. France has a separate physical registry count that remains `NOT_AUDITED` and must not be folded into 102/510.
4. Report every ES/GB/IT occupant-effect level: `0.00`, `0.15`, `0.30`, `0.50`, and `1.00`. Do not present `f=0.30` as the sole calibrated or primary case.
5. The mean internal-gain density `phi` is exactly `3 W/m²` for every occupant-campaign `f`. The Italian `4 W/m²` value is contextual literature information, not a replacement campaign parameter.
6. Every controlled baseline, including France, must use the same final `Schedule:File` implementation path as later non-zero cases, but with a constant controlled series and no stochastic diary draw.
7. Model one thermal zone per dwelling. Add a separately modeled common core only if its geometry and loads are explicitly justified. Do not claim within-dwelling room location because Step 7 provides at-home presence, not room-level tracking.
8. Preserve held-out-fold correctness for occupant-enabled countries. A country's evaluated schedules must not be generated from models or diary information that leak its held-out records.
9. Use actual weather aligned with each diary fieldwork period for occupant comparisons. France baseline weather must have a separate documented source/window; no France occupant alignment is implied until that branch opens.
10. Retain the TABULA heating-intermittency scalar. Do not introduce an additional thermostat night setback that double-counts intermittency.
11. Only residential buildings enter layout, IDF, and simulation manifests. Retain non-residential/unknown footprints in the audit source with explicit exclusion reasons.
12. `N1` and `N2` are real contiguous dense residential neighbourhoods. Preserve the selected natural/declared boundary, use it for every audit panel, and never trim or assemble disconnected buildings merely to force an exact count.

Any proposed change to these decisions needs a short decision record containing the old rule, proposed rule, evidence, expected effect, and approval status.

---

## 6. Decisions that still require evidence

These are genuine design obligations, not details to fill with convenient defaults:

- the exact geometry assumptions: footprint/aspect ratio, orientation, storeys, dwelling layout, core, window placement, and window-to-wall ratio;
- construction layer assemblies and internal thermal mass, beyond nominal U-values;
- the authoritative archetype selection and semantic crosswalk from source fields to OpenUBEM concepts;
- the authoritative France physical archetype subset/count, construction-period mapping, and baseline weather specification;
- the France occupant-input contract, which remains deliberately deferred;
- the precise actual-weather 12-month window, station/location, source, license, missing-data policy, and checksum;
- whether service loads are physically modeled or reconstructed after simulation;
- dwelling allocation and sampling rules where a building/archetype contains multiple dwellings;
- candidate-neighbourhood set, city-specific density metric/rule, selected boundary provenance, and rejected-candidate reasons;
- schedule column semantics, timestep, leap-day/DST treatment, and the object-level assignment of each column;
- gain-object radiant, latent, and lost fractions;
- any use of a separately conditioned or unconditioned common core.

Resolve these through explicit, reviewable artifacts. Never bury them as literals in a script.

**Status of this list on 2026-08-23 (evening), per §4.3:** geometry → D-EU-01 RULED; layers/mass → D-EU-02 RULED; archetype selection/crosswalk → D-EU-04 RULED; France registry → D-EU-11 OWED (DR09 B); France occupant contract → deferred by design; weather window/station/source/licence → D-EU-05 rules RULED, files OWED (DR08); service loads physical vs reconstructed → D-EU-06 RULED; dwelling allocation → D-EU-01 item 6 / D-EU-04 item 3 RULED; neighbourhood density rule → D-EU-10 shape RULED, data OWED (DR10); schedule semantics, timestep, DST → walkthrough §9.8 + MVP §11.7 (chaining rule BLOCKED upstream); gain fractions → D-EU-07 RULED; common core → D-EU-01 item 7 RULED.

**Final status, 2026-08-23 (night), after DR acceptance (§4.3 closure note, MVP §11.13):** every OWED entry above is CLOSED — France registry (D-EU-11: 40 `FR.N` rows, X-08), weather files/station/licence (D-EU-05: ERA5 + Madrid/London/Bologna, X-07), neighbourhood data (D-EU-10: Lyon + pinned datasets/crosswalks), licence text (D-EU-08: publication permitted with attribution, X-02). Deliberately open by design: the France occupant contract (future scope) and the Step 7 chaining rule (upstream, `f>0` only). **This list contains no decision an executor must wait on.**

---

## 7. Implementation work packages

Keep work divided into independently reviewable packages:

- **EU-01 — TABULA loader:** acquire licensed/source-controlled ES/GB/IT/FR records; preserve the 102-record occupant registry and a separate France physical registry; validate country, period, typology, units, completeness, and provenance.
- **EU-02 — Semantic crosswalk and neighbourhood selection:** map source terminology to stable OpenUBEM fields, rank candidate dense residential neighbourhoods, preserve the selected boundary, exclude non-residential/unknown uses explicitly, and expose unknown/unmapped required values as errors.
- **EU-03 — Envelope and internal mass:** generate constructions from explicit assemblies and prove achieved properties by IDF readback and EnergyPlus outputs.
- **EU-04 — Dwelling/core geometry:** create deterministic, valid geometry and zoning with area/volume reconciliation; complete `GEO-01`–`GEO-10`, including normalized Grasshopper/OpenUBEM parity and mutations.
- **EU-05 — HVAC and intermittency:** implement country/archetype systems and TABULA intermittency without duplicate setback logic.
- **EU-06 — Occupant schedules:** write, assign, and validate external `Schedule:File` objects, including the controlled baseline path used by France; do not create France non-zero schedules before `FR-OCC-FUTURE` is approved.
- **EU-07 — Weather:** produce the ES/GB/IT fold-to-weather manifest and separate France baseline-weather record; retrieve/prepare EPWs and verify location/year/checksums.
- **EU-08 — Campaign and SLURM:** define deterministic per-neighbourhood residential-only manifests, one-case runner, S0–S3 sample groups, `NS-01`–`NS-10` selection evidence, separate France baselines, resumable arrays, dependencies, harvesting, and failure accounting.
- **EU-09 — Gates and mutation tests:** implement G8.0–G8.16, V8.a–V8.g, and negative controls that prove gates fail when inputs are corrupted.
- **EU-10 — Results and dossier:** reconcile meters, calculate occupant effects, report uncertainty and failures, and package a reproducible evidence bundle.

Each package should end with:

- code or data artifact;
- targeted automated tests;
- a small retained fixture where practical;
- exact command(s) used;
- observed output and return code;
- limitations and remaining decisions;
- a status update in the active implementation documentation.
- an append-only walkthrough progress-log row with the exact command and evidence path.

Implementation can proceed in parallel only where interfaces are already frozen. Do not parallelize incompatible assumptions about schedules, geometry, weather, or accounting.

---

## 8. Critical path and acceptance checkpoints

### CP0 — Baseline and decision closure

- Record the repository revision and dirty-tree state without modifying user work.
- Run the existing relevant test baseline.
- Inventory European data/resources and their provenance.
- Convert unresolved scientific choices into decision records.
- Freeze manifest schema, stable case ID, output schema, and ownership boundaries.

### CP1 — Data and semantics accepted

- Complete EU-01 and EU-02.
- Validate all expected archetype counts and source classifications.
- Reproduce the separate France physical registry count and prove non-residential/unknown exclusions are absent from modelling manifests.
- Produce the four input-audit views described in Section 10.
- Stop if missing or unmapped values would be silently defaulted.

### CP2 — Physical components accepted

- Complete the first testable slices of EU-03 through EU-07.
- Prove geometry, construction, HVAC, weather, and schedule behavior independently.
- Demonstrate saved-IDF readback rather than trusting only in-memory objects.

### CP3 — Q1 and Q2 pass

- Run S0–S2 local sample groups before annual fleet work.
- Run the four-country physical smoke test: ES, GB, IT, and FR.
- Run the target 32-case physical pilot: 4 stocks × 4 residential typologies × 2 age bands, adjusting only when the accepted France registry lacks a stratum and recording the exclusion.
- Measure memory, runtime, scratch footprint, warning types, and output completeness.
- Adjust resources only from evidence.

### CP4 — Controls pass

- Run the 102-case `f=0` control array.
- Run the separate France baseline (`FR-B`) manifest with one controlled case per accepted France physical archetype.
- Run the independent G8.0 control audit.
- Do not release non-zero cases if the control audit fails or is incomplete.

### CP5 — Occupant campaign and dossier

- Run the remaining 408 cases only after CP4 acceptance.
- Audit all 510 cases together.
- Complete validation, meter reconciliation, effect calculations, and evidence packaging.

A director checkpoint is a scientific decision, not a count of completed tasks. Sign it only when the retained evidence answers the checkpoint's acceptance questions.

---

## 9. Pre-occupant simulation ladder

The pipeline must be tested before occupant information is introduced at campaign scale.

### Q0 — Local deterministic tests

Run unit and integration tests for data mapping, residential filtering, geometry, constructions, schedules, weather manifests, case manifests, parsing, and gates. Include deliberately broken fixtures and `GEO-01`–`GEO-10` Grasshopper/OpenUBEM parity tests.

Before neighbourhood scale, complete the sample ladder: `S0` four synthetic typologies, `S1` 12 observed buildings, `S2` 31 observed high-completeness buildings under `D-EU-04-S2-C` C1A, and `S3` 96 observed buildings. Then select `N1` as one real contiguous dense residential neighbourhood with **≥ 100** post-filter residential buildings (500–600 preferred where the official geography offers it); `N2` is any larger whole official unit, only after N1 (amended 2026-08-24, ruling `D-EU-02-C`). Promote only with complete per-building accounting and measured resource evidence.

### Q1 — Four-country physical smoke test

Run one representative controlled case for ES, GB, IT, and FR. Confirm IDF creation, EPW binding, EnergyPlus execution, required outputs, warning classification, and evidence harvesting.

### Q2 — Target 32-case stratified physical pilot

Target four stocks × four residential typologies × two old/new bands. Select cases that cover EPC availability, materials/construction sets, data completeness, and difficult footprints. If an accepted France registry lacks a requested stratum, document the exclusion rather than fabricating it. The pilot exposes pipeline and resource failures; it does not estimate occupant effects.

### Q3 — 102-case control campaign

Run every archetype at `f=0` through the final schedule and simulation paths. No stochastic occupant diary may affect these controls.

### FR-B — France controlled-baseline campaign

Run one controlled baseline per accepted France physical archetype under a separate manifest and denominator. Do not merge FR-B into the ES/GB/IT 510-case occupant analysis and do not generate France `f>0` cells.

### G8.0 — Control audit

Independently verify that each control case has the required constant schedule, assignments, loads, outputs, and status. Audit raw/saved artifacts, not only the campaign summary.

### Q4 — 408 non-zero cases

Run `f ∈ {0.15, 0.30, 0.50, 1.00}` only after G8.0 passes. Then combine Q3 and Q4 for the 510-case analysis.

Use scheduler dependencies so that Q4 cannot start merely because Q3's array ended; it must depend on a successful audit job.

---

## 10. Required input-audit maps

Before introducing occupant schedules at production scale, compare and select candidate neighbourhoods under `NS-01`–`NS-10`, then generate tables and spatial/categorical plots analogous to the Step 8 four-panel resource image. At minimum audit:

1. construction period;
2. EPC/EKB availability or the European equivalent, with missingness explicit;
3. building function and residential typology;
4. construction material or construction-set classification.

The four panels are four thematic views of the same selected neighbourhood—not four locations. They must share the boundary checksum, footprint geometry, and stable building-ID set. The point is not visual decoration: the maps/tables must demonstrate that the source-to-model crosswalk covers the simulated residential population and that missingness, fallbacks, and exclusions are visible before simulation. Non-residential and unresolved-use footprints remain visible as grey/hatched excluded context but must be absent from layout, IDF, and simulation manifests.

For non-spatial archetype campaigns, use equivalent archetype matrices or heatmaps. Preserve the underlying machine-readable audit table and its generation command. Store reusable sources for every figure/table under `docs/docs_ACTIVE/europeanLocations/content/` and give every document figure/table a descriptive caption.

---

## 11. Speed HPC operating contract

Use the official Speed documentation at <https://nag-devops.github.io/speed-hpc/> and the repository's established parallel-processing conventions. Verify current cluster policies at submission time because queue, account, modules, and limits can change.

Hard rules:

- Never run simulation compute on a login node. Login-node work is limited to lightweight inspection, transfer, queue/account checks, and submission.
- Do not submit any job unless the user explicitly authorizes submission in the current task.
- Use one EnergyPlus process per SLURM array task with `--cpus-per-task=1`, unless measurements prove a different supported execution model.
- Interpret `%32`, `%48`, or `%64` as the maximum number of simultaneous array tasks, not CPUs reserved by one task.
- Start production design at `%32`. Consider `%48` or `%64` only after Q2 demonstrates stable memory, I/O, runtime, licenses/modules, and fair cluster behavior, and after the campaign owner approves the escalation.
- Do not request 32 or 64 CPUs inside each EnergyPlus task merely to satisfy a “more than 32 CPUs” goal.
- Use the CPU `ps` partition unless current official guidance establishes another correct partition. No GPU is required.
- Treat `6G` per task only as an initial measured-default candidate; revise it from Q1/Q2 maximum resident memory plus a documented margin.
- Respect the current batch wall-time maximum; the planning documents record a seven-day ceiling, which must be reverified.
- Stage transient work under the correct Speed scratch location, then harvest durable evidence promptly. The documented scratch cleanup horizon is 90 days and must be reverified.
- Resolve the active account/project at submission time. Use a safely supplied value such as `SPEED_ACCOUNT`; never execute an angle-bracket placeholder.
- Avoid nested local parallelism inside array tasks unless total CPU use is explicitly budgeted.
- Preserve exact module versions, EnergyPlus version, environment, repository revision, manifest checksum, and submission command.

The recommended production dependency chain is:

```text
Q3: 102 f=0 array
        ↓ afterok
G8.0: independent control audit
        ↓ afterok
Q4: 408 f>0 array
        ↓ afterany / explicit audit policy
full campaign audit and dossier
```

Do not submit a single undifferentiated 510-case array that permits non-zero occupant runs before control acceptance.

Retain per-case evidence needed for Step 8, including the case manifest row, generated input/saved IDF, schedule/gain CSVs, EPW identity, `.err`, `.end`, `.eio`, SQL or required meter output, wrapper stdout/stderr, and actual return code. Capture return codes deliberately; shell `set -e` behavior is not a substitute for a case-status record.

Prefer the repository's current SSH/wrapper and `bash -lc` conventions after inspecting them. Never paste and execute an older illustrative Section 6.3 command without adapting it to the current cluster and repository.

---

## 12. Evidence and validation contract

Implement and enforce the detailed G8.0–G8.16 gates and V8.a–V8.g validations in the active MVP and walkthrough. The director should demand at least the following principles:

- **Non-vacuous checks:** an empty parser result is not zero warnings, zero unmet hours, or zero balance error.
- **Saved-artifact inspection:** independently reopen generated IDF and schedule files and verify the values EnergyPlus receives.
- **Assignment checks:** prove schedules are attached to the correct objects; validating only a CSV's values is insufficient.
- **Dependency integrity:** hash or otherwise identify upstream diary/model/weather inputs so stale cache reuse is detectable.
- **Mutation tests:** corrupt one requirement at a time and observe the intended gate fail. Restore the clean fixture and observe it pass.
- **Meter accounting:** reconcile component energy to the selected total within the documented `0.5%` tolerance, with an explicit physical-versus-reconstructed accounting policy.
- **Warning taxonomy:** classify warnings by kind and threshold. A raw warning count alone is not an acceptance rule.
- **Independent headline recomputation:** reproduce principal counts and energy/effect summaries by a second path before publication.
- **Failure visibility:** missing, failed, skipped, or unparsable cases remain visible in denominators and status tables.

Record gates as `NOT_RUN` until their command and evidence have actually been observed. A written test specification does not constitute a passing test.

Stop the campaign when any of these occurs:

- archetype counts or country semantics disagree with the frozen manifest;
- source provenance or license is unresolved;
- a crosswalk silently falls back for a required field;
- weather does not match the declared fold/window;
- schedules are malformed, shifted, unassigned, or leakage-prone;
- controls contain stochastic diary influence;
- geometry or construction reconciliation fails;
- EnergyPlus severe/fatal errors, required-output absence, or unclassified warnings exceed policy;
- result accounting double-counts a physically modeled load;
- case failures are hidden by aggregation;
- a mutation expected to fail is accepted;
- cluster resource use differs materially from the pilot without explanation.

---

## 13. Director operating rules

### Communication

- Reply to the user in English even when the user writes in French.
- Lead with the verified outcome or blocker, then provide the minimum detail needed to decide.
- Ask at most one focused question at a time when a decision truly cannot be inferred safely.
- Distinguish facts, inferences, proposals, and unverified assumptions.

### Repository safety

- Treat the working tree as potentially dirty and user-owned.
- Inspect before editing and preserve unrelated changes.
- Do not run `git add`, `git commit`, `git stash`, `git restore`, `git checkout`, or destructive reset/cleanup operations unless the user explicitly requests them.
- Make documentation corrections additively when preserving prior text is required: add status notices, correction notes, or superseding sections rather than erasing historical content.
- Use the project's normal patch/edit workflow and run verification proportional to risk.

### Scope and authorization

- A request to review or diagnose does not authorize implementation.
- A request to implement does not automatically authorize Speed submission.
- A request to prepare SLURM files does not automatically authorize submitting them.
- If asked to implement, finish a coherent tested slice rather than producing only a plan.
- Do not delegate work or create sub-agents unless the user explicitly requests delegation or the active session instructions expressly allow it. **Standing exception from 2026-08-23:** the user has ruled that implementation slices are executed by external LLM tooling (Codex, Antigravity) under §19. Delegation to those executors is therefore authorised by default; delegation to Claude sub-agents still is not, unless asked.
- Use primary or official sources for standards, software behavior, and Speed policy. Browse only when current facts or source verification require it.

### Scientific discipline

- Follow `measure → decide → plan → execute` for high-impact changes.
- Do not remediate a baseline while measuring it; retain the original result and apply the correction in a separate, attributable step.
- Never optimize concurrency before measuring the representative pilot.
- Never tune a model to force an expected narrative about occupant effects.

---

## 14. Documentation and handoff conventions

Keep one live manager prompt at the root of:

`docs/docs_ACTIVE/europeanLocations/prompts/`

When this prompt is superseded, preserve the previous version under a `previous/` subdirectory rather than deleting it. Update the live prompt after material decisions, checkpoint acceptance, or changes in implementation state.

Keep detailed implementation/evidence reports near the European-locations arc in clearly named subdirectories. Do not claim a directory or artifact exists until it has been created and inspected.

Treat `MVP_european_locations.md` as the principal method/implementation contract. Treat `WALKTHROUGH_european_locations.md` as the ordered task/runbook and append-only progress record. Do not duplicate or silently fork scientific decisions in the walkthrough.

Store reusable sources for every numbered figure/table under `docs/docs_ACTIVE/europeanLocations/content/`, keep `content/README.md` current, and add a descriptive caption to every figure/table in both documents. Illustrative images must say that they are not measured data or simulation evidence.

Every session handoff should state:

- current repository revision and dirty-tree caveat;
- which work package/checkpoint is active;
- what changed;
- exact verification commands and outcomes;
- evidence paths;
- jobs submitted and current/final scheduler states, if authorized;
- unresolved failures or decisions;
- the single recommended next action.
- a new walkthrough progress-log row for every material attempt, including failed attempts.

Do not paste enormous raw logs into planning documents. Preserve logs as artifacts and summarize them with paths, hashes where useful, and the decisive excerpts.

---

## 15. Definition of done

The European-locations arc is done only when all of the following are true:

- all 102 ES/GB/IT occupant archetypes and the separate France physical archetype registry are sourced, semantically mapped, and provenance-audited;
- non-residential and unresolved-use footprints are explicitly excluded and proven absent from layout, IDF, and simulation manifests;
- each N1/N2 site is a real contiguous dense residential neighbourhood accepted under `NS-01`–`NS-10`, with a versioned boundary and candidate-selection record;
- geometry, envelope, internal mass, HVAC, and weather decisions are explicit and tested;
- `GEO-01`–`GEO-10`, Grasshopper/OpenUBEM parity, and the S0–S3 residential sample ladder have observed outcomes;
- the external occupant schedule path, including `f=0`, is independently verified;
- held-out-fold and weather alignment are proven;
- Q0, S0–S3, four-country Q1, target physical Q2, ES/GB/IT Q3, G8.0, separate France `FR-B`, and ES/GB/IT Q4 have completed in the required order with retained evidence;
- all 510 expected cases per weather specification are accounted for, including failures;
- all accepted France baseline cases are accounted for in their separate manifest and denominator;
- G8.0–G8.16, V8.a–V8.g, and the mutation suite have observed outcomes;
- EnergyPlus errors/warnings and required output completeness satisfy policy;
- energy accounting is reconciled without double counting;
- headline results are independently recomputed;
- the final dossier is reproducible from manifests, versioned inputs, commands, and retained outputs;
- the active documents, reusable figure/table register, walkthrough progress log, and this director prompt accurately describe the achieved state rather than the intended state.

France occupant schedules and non-zero France occupant-effect simulations are a named future release branch. They are not required to close the current France physical + ES/GB/IT occupant release, but they must remain visible as `FR-OCC-FUTURE` and cannot be reported as implemented.

Until then, describe the arc by its actual checkpoint and status. Never call it complete because a document, script, array, or dashboard exists.

---

## 16. First-session response template

After completing the read-only audit, begin with a concise response in this form:

> I verified the European-locations arc at **[checkpoint/status]**. **[What is genuinely implemented or evidenced]**. **[What remains documented only or blocked]**. No Speed jobs were submitted / the following explicitly authorized jobs were submitted: **[IDs and states]**. The next safe action is **[one action]**.

Then list only the evidence, decisions, or authorization needed for that action.

---

## 17. Immediate next action at this handoff

**Current user-directed action (2026-08-24; supersedes any generic dispatch wording below):** **EU-02 neighbourhood selection is CLOSED.** The executor prompt was **executed in-session against live public APIs**, not delegated, so **no external packet is coming and none is to be waited for**; the prompt is archived at [`previous/EXECUTOR_PROMPT_EU-02_neighbourhood_selection_2026-08-24.md`](previous/EXECUTOR_PROMPT_EU-02_neighbourhood_selection_2026-08-24.md) and the result report is filed as a result artefact at [`../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md`](../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md) (Revision B, all four cities SELECTED). Treat that document as the EU-02 selection record and do not re-open it without a dated decision record. **What is actually next, in order:** (1) ~~three owner rulings~~ — **taken 2026-08-24 under delegation**, §7 of the report (`D-EU-02-A` quartier `7016`; `D-EU-02-B` Berruguete; `D-EU-02-C` size band permanent, MVP Table 10 / `NS-05` amended); nothing is owed by the owner; (2) `ingest_buildings(bbox=...)` for the two OSM-sourced sites `ES-MAD-BERRUGUETE` and `GB-LDN-STDUNSTANS`, clipped to the retained boundary GeoJSON, to produce the first European raw footprint manifest with the `NS-08` exclusion list; (3) the two missing acquisition adapters (IGN BD TOPO for `FR-LYO-HAUTCOEURPENTES`, Comune di Bologna ODS for `IT-BOL-GALVANI2`), which are the sole reason `NS-02` is `NOT_MET` at those two sites. **Actions (2) and (3) are now planned in full** as slices `X-09`–`X-11` in [`EXECUTOR_PROMPT_EU-02_acquisition_adapters_2026-08-24.md`](EXECUTOR_PROMPT_EU-02_acquisition_adapters_2026-08-24.md) (opened 2026-08-24): execute it top-to-bottom, stop at CP-A, CP-B and CP-C, and append one progress-log entry per task under its §8. If any later external packet on EU-02 does appear, it is a candidate handoff only and must be reconciled against the retained report before anything is changed.

Unless newer repository evidence changes the state, begin with **CP0 / EU-01–EU-02**: re-check the code/test/resource baseline, then implement the smallest local slice that defines the four-country physical registry contract, residential-only filter, and candidate-neighbourhood selection schema with explicit non-residential exclusions. Use tiny deterministic fixtures before S0, do not fabricate the unaudited France production count, and do not choose a production neighbourhood before its density rule is registered.

Do not submit Speed work during this initial audit. The planning documents and this prompt establish how to run the campaign safely; they do not grant submission authority.

**Superseded as a dispatch instruction on 2026-08-23T20:50Z.** `X-01` → `X-03` and `X-08` are complete. A new session must use §19.5 rather than this historical ordering. Its first independent implementation action is to complete saved-IDF S0 geometry/envelope emission and the heating-only fixture (`X-05`/`X-06`). It must preserve the two external dependencies: the strict R3 reconciliation in `debugs/docs/DONE-docs/ANALYSIS_REQUEST_X-04-R3_X-07-CDS_2026-08-23.md`, and live ERA5 retrieval until CDS credentials exist. It must not submit Speed work.

---

## 18. Constraints for any documentation-enrichment pass

<!-- SEC:documentation-pass-constraints-2026-08-23 -->

Give this section **verbatim** to any agent or external LLM asked to improve, enrich, expand, or
reformat `MVP_european_locations.md` or `WALKTHROUGH_european_locations.md`. It exists because a
source-verification pass on 2026-08-23 found nine numeric claims attributed to *Iseri et al. (2025)*
that the published paper does not contain. The full evidence, task list, and progress log are in
[`debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md`](../debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md).

```
Constraints for this documentation pass:

1. Do not delete anything; enrich only.
2. Do NOT edit MVP §9.2 (repository baseline audit) — every claim in it
   was verified true against the repo on 2026-08-23.
3. Fix these verified factual errors:
   - MVP §4.7: 277 buildings / 1,444 floors / 252 / 91.7% / 8.3% / 87.3 m²
     are unsourced. The paper reports 593 residential buildings of 642.
     Either remove the block or mark every unverifiable figure UNSOURCED.
   - Walkthrough line 41: "277 buildings" -> 593 buildings.
   - 63.61, 15.54, 75.5%, 3.2x are NOT in Iseri et al. (2025). Re-attribute to
     IMP_step8/outputs/simulation_results_analysis_report.md.
   - Walkthrough line 41: "corner units 25-40%", "top-floor 15-25%" are
     unsourced and contradicted (report: top-floor +148.8% vs mid-floor).
   - MVP §1.1 item 1: ">35%" -> "12-35%", and attribute to zoning resolution,
     not to US-vs-EU construction.
   - MVP §1.1 item 2: "15%-40%" -> "15-35%", restore the qualifier
     "for corner/top units adjacent to cooler or vacant dwellings".
   - Say "standard deviation", not "variance", wherever 63.61/15.54 appear.
4. Add no new numeric claim unless you can quote its source file and line.
   If a number cannot be sourced, mark it UNSOURCED rather than inventing one.
5. Keep the §9.1 status vocabulary (CURRENT / REUSABLE / TARGET / BLOCKED /
   VERIFIED). Never label anything VERIFIED without a produced artefact.
6. Add "# TARGET API - not runnable in OpenUBEM 0.1.0" to the walkthrough
   §7.1 snippet, which calls the non-existent reconstruct_eui().
7. Documentation only. Do not modify any .py file.
```

**Status of the seven items above at 2026-08-23:** all seven were executed in this repository under
`debugs/DONE/DONE_PLAN_citation-audit-fixes-2026-08-23.md` (tasks T01–T07). The block is retained verbatim so
that any later enrichment pass can be checked against it and cannot silently reintroduce the
corrected figures. If a future pass reinstates `277`, `15-25%`, `25-40%`, `>35%`, `15%-40%`, or
re-attributes the re-analysis statistics to the paper, reject that pass.

### 18.1 Standing citation rule for this arc

A figure derived from the `AllV*.csv` re-analysis is cited as
*`IMP_step8/outputs/simulation_results_analysis_report.md` (2026-08-22 re-analysis of the
Iseri et al. 2025 simulation data)* — never as *Iseri et al. (2025)* alone. Only the sample
description (6,458 dwelling units; 593 residential buildings of 642 in the study area) and the
method description come from the paper itself.

### 18.2 Standing lesson

A number that reads as empirical validation is not evidence until its source file and line are
named. Before any figure in this arc is promoted to `VERIFIED`, search it in the paper PDF, in
`IMP_step8/outputs/`, in `IMP_step8/DeepResearch/`, and in `IMP_step8/resources/` — in that order —
and record where it was found. Absence from all four is a finding, not a formatting problem.

### 18.3 Additional constraints after the v1.3 pass

Any later documentation pass must also be checked against these; a pass that breaks one is rejected:

```
8.  Do not re-attribute c_m = 50/87/32.8 or n_air_use = 0.40/0.59/0.30 as campaign
    values. The campaign set is EU.SUH/EU.MUH: c_m = 45, n_air_use = 0.4, phi_int = 3,
    theta_i = 20, F_red_htr = 0.9/0.8 (SUH) and 0.95/0.85 (MUH). Cite MVP Table 13.
9.  Do not re-type construction-year bands. Quote MVP Table 15 (22 verbatim codes).
    The Spanish ES.05 label is "CTE-79"; "NBE-CT-79" appears nowhere in the workbook.
10. Do not describe tabula_archetypes_*.json as derived from the workbooks directly.
    EU-01 consumes Step8_docs/outputs_step8/archetype_parameters_{es,uk,it}.csv.
11. Do not state a weather station, year or source as settled. Windows are ruled
    (es 2009-2010, uk 2014-2015, it 2013-2014); files, licence and station are owed.
12. Do not collapse GB parallel parameterisations or IT composite codes into one
    row per cell; that is parent open decision §6.4, not taken.
13. Do not present the Q1/Q2 TMY smoke EUIs as baselines or compare them to TABULA bands.
```

---

## 19. Single-manager continuation protocol

<!-- SEC:single-manager-continuation-protocol-2026-08-24 -->

This file is the sole active prompt for a new Codex or other LLM session. It combines the scientific
guardrails, implementation authority, acceptance procedure, and current-state ledger. Do not use or
maintain `EXECUTOR_X-01_paste_into_codex.md` for future handoffs; it is superseded historical
material. The manager both directs and performs bounded implementation slices.

### 19.1 Operating model

Work in dependency order and complete a coherent, locally verifiable slice before beginning another.
Before modifying files, verify the governing MVP/walkthrough requirement, inspect the affected code and
tests, and define the smallest safe file list. A slice requiring a scientific decision, live credentials,
network data, or a Speed submission must be documented as blocked while unrelated local work continues.

After every material completed, partial, blocked, or documented result, update all of the following in
the same change set:

1. the head box and §19.5 ledger in this prompt;
2. MVP §9.7 and `content/table_9_7_work_packages.csv`;
3. walkthrough Table 4 and append-only `content/walkthrough_progress_log.csv` with the same UTC row;
4. a decision/analysis record under `debugs/docs/` when authority is missing.

Never make a git state-changing command. Never submit a Speed/cluster job, retrieve live ERA5 data, or
print a credential unless the current user explicitly authorizes it and the required credentials are
available.

### 19.2 Pre-slice checks

1. Read the relevant walkthrough task and MVP requirement; the walkthrough is the runbook of record.
2. Confirm the source/fixture path and expected assertion; checksum copied inputs when applicable.
3. Inspect `git status --short` and `git diff --stat`; preserve unrelated dirty work.
4. Confirm the work is local, deterministic, and does not require an unrecorded scientific decision.
5. Run focused tests and proportionate regression tests; retain concise evidence under
   `openubem/outputs/eu_evidence/<work-package>/`.

### 19.3 Fresh-session instruction

Paste **this entire file** into the new session and set the working directory to
`C:\Users\o_iseri\Desktop\OpenUBEM`. Read the head box, §19.5, the last ten progress-log rows, and
MVP §9.7 before acting. EU-02 is closed and no external packet is pending; treat
`../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md` as the selection record and preserve it unless a
checked decision record explicitly supersedes it. Do not restart completed
historical `X-*` slices. Resume the first unblocked local dependency, report verified facts in English,
and continue without waiting for routine user confirmation. Stop only for a real authority conflict,
credential requirement, or external-state change; record it and continue independent work.

### 19.4 Manager evidence audit (do all of it before accepting)

1. Inspect `git status --short` and `git diff --stat`; changed files must stay within the chosen slice.
2. Re-run the named focused test command. Run the full European suite when proportionate; a known
   Windows/joblib stall is an infrastructure finding, never European proof of success or failure.
3. Open `openubem/outputs/eu_evidence/<slice>/`; every cited artefact must exist and be non-empty.
4. Compare each assertion with the relevant MVP/walkthrough requirement using observed values, not a
   passing tick alone. Do not apply X-01 loader criteria to a later slice.
5. Check that no `.py` landed under `docs/`, no unrelated test changed, and no GSSCanada source changed
   (`git -C C:\Users\o_iseri\Desktop\GSSCanada status --short` if it is a repository; otherwise compare
   the three CSV checksums against `tests/fixtures/eu/step8_outputs/SHA256SUMS`).
6. Turn every unresolved authority into a dated record under
   `docs/docs_ACTIVE/europeanLocations/debugs/docs/`; do not settle it only in chat.
7. Confirm each registered error is represented in `OpenUBEM_debug_References.md` in the house format.
8. Only then update the documents and logs listed in §19.1 and tell the user the verified outcome in
   the §16 form.

Never label a slice `LOCAL_PASS` when its named tests cannot be reproduced.

### 19.5 Slice ledger

**Morning continuation checkpoint, 2026-08-26T00:02:11Z:** the external weather block has changed from missing credentials to active acquisition. The current project-owned CDS client has submitted the boundary-day and 12 monthly jobs for direct ERA5 single-level data at the Lyon-Bron reference (45.72 N, 4.95 E; nearest returned ERA5 grid point retained in the future EPW). Acquired archives are `2022-12-31`, `2023-01`, `2023-02`, `2023-03`, and `2023-12`; the corrected `2023-04` job is `running`. Earlier rejected jobs are retained as evidence: the first batch used invalid day-31 requests and the concurrent retries exceeded CDS capacity. The reproducible acquisition/polling script is `scripts/acquire_era5_lyon_bron_2023.py`; the converter is `scripts/convert_era5_lyon_bron_2023_to_epw.py` and has loaded the real January archive (744 rows, all nine required variables). `h5netcdf` is now a project dependency. Until all 13 archives exist and the resulting EPW passes the six DR08 gates, the weather registry remains unchanged and S2 must not run.

**Latest verification checkpoint, 2026-08-25T19:36:37Z:** `EU-04` re-ran the controlled three-dwelling layout-to-IDF-to-EnergyPlus design-day smoke after the per-zone control-name fix. Focused geometry/control tests pass **13/13 in 3.37 s**; the complete currently discovered `tests/test_eu_*.py` suite passes **209/209 in 20.29 s**. Repeated use of one TABULA archetype across multiple dwelling zones no longer creates duplicate-name severe errors: per-zone ventilation, gains, and thermostat objects are unique, while the two constant availability schedules are shared once per IDF. This remains a controlled fixture result: no observed-building imputation, annual/weather result, core in an observed shell, Grasshopper parity, GEO-10, S2, or S3 claim. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_layout_energyplus_smoke.log` and `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_layout_energyplus_smoke.log`. A new session should begin from the S1 audit checkpoint below, then use this verification as the latest local engine evidence; preserve the native-CRS, vertex-limit, observed-input, and S2/S3 scope blocks.

**Latest S2 scope measurement, 2026-08-25T19:42:50Z:** `scripts/scope_eu_s2.py` measured the complete retained corpus before any S2 sample selection. Under the explicit S2 rule of **2 rows per type × old/new age band × high/low mapping-input completeness cell**, the 32-case target is **not formable**: the 4,186-row corpus contains 297 high-completeness typed/year rows (AB 146, MFH 123, TH 21, SFH 7), but no complete low-completeness typed/age cells. Among those 297 mapping-ready rows, the real-footprint layout contract emits only **18** layouts and leaves **279** explicit fallbacks: 200 non-convex, 58 narrow, 11 courtyard-topology, and 10 partition-audit failures. This is a measurement-only scope result: no outcome-balanced sample was selected, no threshold was relaxed, and no EnergyPlus run was made. Evidence: `openubem/outputs/eu_evidence/EU-04/s2_scope_measurement.csv`, `s2_scope_summary.json`, and `s2_scope_measurement.log`. The next session must treat S2 as **not yet formed** and either measure an owner-approved revised ladder or open a scoped geometry/data-completeness work package; do not present the 18 emitting rows as S2.

**Latest geometry-risk diagnostic, 2026-08-25T19:45:04Z:** `scripts/diagnose_eu_s2_geometry_limits.py` rechecked all 297 mapping-ready Lyon rows without modifying the generator. The native result remains 18 emitted layouts, but a centroid-translated sensitivity probe emits **28**: exactly **10** native `PARTITION_AUDIT_FAILED` rows change status, confirming that the fixed-origin rotation plus absolute tolerance is CRS/coordinate-magnitude sensitive. The same census finds **one** footprint with **173** exterior vertices, above the approximate ~120-vertex EnergyPlus `BuildingSurface:Detailed` field budget. This is diagnostic evidence only: no centroid translation was promoted, no geometry was simplified, no manifest changed, and no EnergyPlus run was made. Evidence: `openubem/outputs/eu_evidence/EU-04/s2_geometry_limits_diagnostic.csv`, `s2_geometry_limits_diagnostic_summary.json`, and `s2_geometry_limits_diagnostic.log`. Open the rotation-origin/tolerance and vertex-budget remedies as separate scoped work; do not fold these findings into S2 success.

**Latest S2 remedy decision note, 2026-08-25T19:55:21Z:** the 10 coordinate-sensitive IDs and the single 173-vertex ID are enumerated in `openubem/outputs/eu_evidence/EU-04/s2_geometry_remedy_decision_note.md`. Two owner rulings are required before implementation: coordinate/tolerance handling (centroid rotation, relative tolerance, or retain fail-closed) and over-budget ring handling (declared-error simplification or retain refusal). Until ruled, S2 remains diagnosed but not formable; no production geometry or EnergyPlus behavior changed.

**Owner-response document, 2026-08-25T19:58:00Z:** `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_S2_geometry_remedies_2026-08-25.md` is open for direct response. It requests `D-EU-04-S2-G` (G1/G2/G3) and `D-EU-04-S2-V` (V1/V2), with execution boundaries and evidence requirements. Do not implement either remedy or form S2 until both values are ruled.

**Latest S2 remedy execution, 2026-08-25T20:10:00Z:** owner rulings `D-EU-04-S2-G = G1` and `D-EU-04-S2-V = V1` were implemented. Focused geometry tests pass (29). The 297-row re-measurement now emits 28 native layouts with zero native/translated status changes; one over-budget ring is simplified deterministically with maximum Δarea 0.0146008 m² and Hausdorff error 0.0170423 m. The existing S1 smoke rerun is 12/12 `EPLUS_COMPLETED`, including the former 173-vertex failure. S2 remains not formable under the original completeness ladder and no sample was selected.

**Latest superseding continuation snapshot, 2026-08-25T19:05:00Z:** **`S1` ran to its end and met its ladder criterion** — *"12/12 accounted for; failures classified"* — and the manager audited the artefacts on disk rather than the report. **Axis A reproduces the frozen sample exactly**: 8 `REFUSED_BY_LAYOUT_CONTRACT`/`NON_CONVEX_FOOTPRINT`, 3 `FALLBACK_PENDING_LAYOUT`/`NARROW_FOOTPRINT_LT_8M`, 1 `DWELLING_LAYOUT_EMITTED`. **Axis B**: 11 `EPLUS_COMPLETED` (10 `FALLBACK_ONE_ZONE_PER_FLOOR` + the single `EUROPEAN_DWELLING_LAYOUT`) and **1 `EPLUS_FATAL`**. `S1` produced no energy number, by design. **Three things this slice establishes.** **(1) The executor stopped instead of adapting, and that is the whole value of the checkpoint.** Under the `EPSG:2154` reprojection the prompt then specified, the one emitting row flipped to `PARTITION_AUDIT_FAILED`; the cause is in the generator, not the sample — `generate_european_dwelling_layout` rotates about the literal coordinate origin (`openubem/geometry/european_residential.py:504`) while `audit_european_floor_partition` compares against an **absolute** `topology_tolerance_m2 = 1e-8` (`:643`), so float noise scales with distance from `(0,0)`: clean in the native `EPSG:32631` (~642000/5070000), failing `AREA_GAP` + `OUTSIDE_FOOTPRINT` in Lambert-93 (~852000/6519000) at an `area_error_fraction` of **5.09e-12**. **Dwelling-layout success is therefore CRS-dependent, and a census run in Lambert-93 would have reported near-zero emitted layouts for this same corpus.** The manager ruled the **native** CRS with no reprojection — the *prompt text* was corrected, never the owner-frozen sample, because re-picking the 12 would have reintroduced exactly the outcome-based selection `H2` was refused for — and the fragility was registered as an `[OPEN]` bullet in ch.5 of `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, **not fixed**, this being a measurement task. Candidate remedy for a later scoped item: rotate about the footprint centroid and/or make the topology tolerance area-relative. **(2) The one fatal is a real corpus property, not a flake.** `BATIMENT0000000240877527_part0`'s exterior ring carries **173 vertices** against the IDD's ~120-vertex `BuildingSurface:Detailed` limit, and `build_zones(..., "one_zone_per_floor")` uses `exterior.coords` verbatim, so any dense historic parcel can hit it — registered in ch.1, recorded fail-closed as a named refusal, never an energy result. **(3) A new caveat the run itself created:** the single dwelling-level EnergyPlus model is **one floor plate of 5 dwellings, not the 6-storey / 28-dwelling stack** (`zone_count = units_per_floor = 5`), while the 11 fallback models are full stacks (`zone_count = observed_storeys`) — the two axes are **not comparable in vertical extent**, and the dwelling-level path must never be quoted as "a 6-storey dwelling-partitioned building runs". The executor also fixed a bug **in its own runner** (relative `tmp_root` double-resolved against `subprocess.run(cwd=...)`, ch.13) and left the generator and `zoning.py` untouched; regression `pytest -q tests/test_eu_reciprocal_surface_audit.py tests/test_eu_box_generator.py` is **14 passed**. Evidence: `openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv`, `.../s1_smoke/*.err` (12), `scripts/run_eu_s1_smoke.py`. **Standing lesson, extending the previous snapshot's:** when a geometric contract is audited with an **absolute** tolerance, its pass rate is a property of the coordinate system, not of the buildings — pin the CRS in the contract, or make the tolerance relative. The next actions are `S2`/`S3` scoping (remembering `S3` cannot be typology-balanced for France, `SFH` caps at 7) and, as separate explicitly scoped items, the vertex-budget simplification and the rotation-origin fix **The next session must start from this checkpoint and from the START HERE bullet in the head box; its first action is to scope `S2` by measuring the corpus yield before promising it. Nothing is blocked on a decision and nothing is running.**

**Latest superseding continuation snapshot, 2026-08-25T18:48:58Z:** **`D-EU-04-H` is RULED - Option H1 adopted**, and `S1` is no longer blocked: it is *running*, with 12 frozen buildings and an executor prompt that forbids every shortcut the measurement exposed. Two things this slice establishes beyond the run itself. **(1) The ladder rule, applied honestly, costs almost all the runs.** Selecting `2 irregular + 1 simple` per typology by `building_id` order yields **1** dwelling-level layout of 12, not the "about 4" the decision request estimated - a second self-correction in two passes, both from the same root cause: quoting a downstream capability from an upstream count without re-measuring the stage in between. **(2) A fallback that runs is still a failure of the thing being tested.** The prompt keeps the dwelling-layout status and the EnergyPlus outcome in separate columns precisely so that 11 whole-floor smoke successes can never be reported as 11 laid-out buildings. **Standing lesson, extending the previous snapshot's:** re-measure the next stage before promising it, and when a fallback exists, name the axis it succeeds on - otherwise the fallback silently becomes the result.


**Latest superseding continuation snapshot, 2026-08-25T18:30:36Z:** `S1` was scoped and is **blocked again, on a different constraint**, and the previous snapshot's closing line — "form `S1`: 12 French buildings, 3 per typology, from the 297 layout-ready rows" — **cannot be executed as written**. Measured over all 297 layout-ready French rows, taking `units_per_floor` from `allocate_european_dwellings` on the observed dwelling and storey counts and calling `generate_european_dwelling_layout` on the real footprint: the generator emits for **18** — **0** `SFH`, **1** `TH`, **14** `MFH`, **3** `AB`; **23** fall back (`NARROW_FOOTPRINT_LT_8M` 13, `PARTITION_AUDIT_FAILED` 10); **256** are refused outright as non-convex or courtyard-holding. The generator contract — convex, no courtyard hole, minimum rotated width ≥ 8 m, ≥ 2.5 m façade contact per dwelling, independently audited — was ruled under GEO-01/GEO-04/GEO-09 and was not touched, and it is not wrong: 256 of 297 Lyon footprints genuinely are concave or hold a courtyard. **The mistake was mine, in the semantics of a field name.** `layout_ready = True` means the *archetype-mapping inputs* are complete — type, year, archetype, dwelling count — and I wrote into `D-EU-04-G` that "`S1` (12 buildings, 3 per typology) becomes reachable immediately", which the owner then ruled on. That sentence is **wrong and load-bearing**, and it is corrected in §0 of the new decision request rather than quietly dropped. The `G1` derivation itself is untouched by the correction (302 typed / 297 dated stands, `ES`/`GB`/`IT` unmoved), and nothing downstream was built on the wrong figure because `S1` never started. **`D-EU-04-H` is OPEN and blocking**: `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_H_S1_reachability_2026-08-25.md`, evidence `openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv`. The recommendation is **H1** — run the ladder's own 12 (3 per typology, 2 irregular and 1 simple, ordered by `building_id`) and classify every failure — because the ladder already states its acceptance criterion as *"12/12 accounted for; failures classified"*, and because **H2**, forming `S1` from the 18 that emit, would report a clean twelve-for-twelve that is clean only because the twelve were chosen for being clean. **H3**, extending the generator to concave and courtyard plates, is the right eventual answer for coverage and should be opened as a work package after `S1` has measured what it is worth; **H4**, relaxing the 8 m or 2.5 m threshold, is listed in the request only to be refused. **This was a measurement pass under the diagnose-before-remediate rule: no feature code was written, no test was changed, no threshold was moved, and no sample was formed.** **Standing lesson for this arc: a boolean named for a downstream capability will be read as that capability — `layout_ready` was true for 297 buildings of which 18 can be laid out. Name a gate for the inputs it actually checks, and re-measure the next stage before promising it.** The next session's first action is to obtain the `D-EU-04-H` ruling.

**Latest superseding continuation snapshot, 2026-08-25T18:34:00Z:** the ruled `D-EU-04-G` (G1) two-signal derivation is **implemented and audited**, and France reaches **`layout_ready_count` 297** from **0** — the first time any European site has produced a layout-ready observed building. The rule sits behind `OBSERVED_TAG_TO_TABULA_TYPE` for `FR` only, so `ES`, `GB` and `IT` did not move by a single row. Every pinned acceptance number was reproduced without adjustment: 302 typed of 530, 297 typed-and-dated (7/21/123/146), adjacency 488/42, exclusions 228. **The standing lesson of the previous snapshot was vindicated twice over.** The report that claimed the rule was already implemented was a quotation of the request; and its **233**-exclusion figure — "7 sans année, 1 sans logement" — was also invented, the real figure being **228**, because under `G1` the year is not an exclusion criterion at all. **Pin the acceptance numbers in the executor prompt and forbid tuning; then audit the artefact, not the report.** One finding is recorded rather than fixed: `type_provenance_counts` counts rows, not typed rows, so its `OBSERVED_TAG` 3,884 includes 2,571 typeless rows and must never be quoted as an observed-type total.


**Latest superseding continuation snapshot, 2026-08-25T17:42:47Z:** **`D-EU-04-G` is RULED — Option G1 adopted, both consequences accepted by the owner** (a derived type is stamped `DERIVED_BDTOPO_TWO_SIGNAL` and is never reported as observed; **`S3` is not typology-balanced for France** because `SFH` caps at **7** in this dense historic quarter). The decision document `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md` now reads status `RULED` with the owner block completed, so **nothing in this arc is blocked on a decision any more**. 🔴 **The accompanying claim that the rule had been implemented was audited and does not hold.** Three independent checks: `DERIVED_BDTOPO_TWO_SIGNAL` appears in **no `.py` file** in the repository; `openubem/semantic/european_archetype_mapping.py` was last modified at **10:56Z, before the ruling**; and `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness_summary.json` still reports `layout_ready_count: 0` with `UNMAPPABLE_RESIDENTIAL_TYPE: 522`. The yield figures returned as an execution result (302 typed, 297 dated, 7 `SFH` / 21 `TH` / 123 `MFH` / 146 `AB`) are **the manager's own measurement, written into §2 of the decision request while it was being drafted** — they were restated, not produced. **Standing lesson for this arc: when a report's numbers are exactly the ones the request already contained, treat them as a quotation until an artefact on disk carries them.** The remedy is manager-authored and ready: `prompts/EXECUTOR_PROMPT_EU-04_fr_typology_derivation_2026-08-25.md`, four tasks. **T01** reads `nombre_de_logements` out of `surplus_tags` — **no code reads it today**, which is precisely why the single mapped London building still ends at `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`, and wiring it is what lets a typed French row reach `layout_ready = True` rather than stopping one step short. **T02** computes footprint adjacency in **EPSG:2154** with a `touches`-or-non-point-intersection predicate and a zero-metre tolerance, expecting **488 attached / 42 free-standing**. **T03** applies the pinned rule **behind** `OBSERVED_TAG_TO_TABULA_TYPE` so the observed path is untouched and the derivation runs only for `FR` when the tag maps to nothing, adding a `type_provenance` field valued `OBSERVED_TAG` or `DERIVED_BDTOPO_TWO_SIGNAL`. **T04** regenerates the readiness evidence with separate provenance counters, expecting `layout_ready_count` **0 → 297** while the `ES` (1,194), `GB` (1,242) and `IT` (1,220) numbers stay byte-identical as the regression check. The acceptance numbers are pinned in §3 of the prompt and **a mismatch is a STOP, not an adjustment** — the rule must never be tuned to reach a count. The `bdtopo_fetcher.py:82` hardcoded `current_year = 2026` remains **recorded and unfixed**, and is explicitly out of scope for this slice. The next session's first action is to dispatch that prompt to a fresh executor and audit CP-1 against the pinned counts **before** any evidence is regenerated.

**Latest superseding continuation snapshot, 2026-08-25T17:31:19Z:** the ruled remedy **ran end to end and was audited against disk**, and the France construction year is **recovered**. `_parse_bdtopo_year` (`openubem/acquisition/bdtopo_fetcher.py:82`) extracts the leading four-digit calendar year with an anchored `^(\d{4})` pattern and returns `pd.NA` outside `[1000, current_year]`, with no datetime round-trip; the pinned `acquire_bdtopo_manifest.py` re-acquisition ran at 17:27:18Z as the **single authorized live IGN call**, against the same boundary SHA-256. **Verified by the manager rather than taken from the executor's report:** the retained manifest holds **522 of 530** observed years where it held **0**, spanning **1550 → 2010**, median **1850**, `IGN_BDTOPO_OBSERVED` on 522 and `IGN_BDTOPO_MISSING` on 8; **four of the recovered years are pre-1677**, exactly the class `datetime64[ns]` could never represent; **all 522 resolve to a TABULA French construction period** (`FR.01` 458, `FR.02` 9, `FR.03` 7, `FR.05` 5, `FR.06` 9, `FR.07` 28, `FR.08` 4, `FR.09` 2); the `[OPEN]` marker is gone from `OpenUBEM_debug_References.md` and its `Fix:` clause names the code and both regression tests; `pytest -q tests/test_eu02_fetchers.py tests/test_eu_observed_archetype_mapping.py` is **12 passed in 2.01 s**. **Two deviations are recorded, not fixed** (this was an audit pass): (1) `current_year` is a **hardcoded default of 2026**, so from 2027 the parser will silently reject valid construction years — the same class of defect it was written to remove, one year of latency instead of zero; (2) the script's exclusion counts (768 clipped / 530 residential / 172 unknown / 46 non-residential / 20 annexes) differ from its own `expected_raw_boundary_counts` (891/544/278/46/23) and the executor did not report the difference, but **the two are not the same population** — the expectation is the selection-time raw-boundary census while the script reports post-clean model-ready counts, and `raw_schema_rows` is **1,455 in both this run and the 14:22Z run**, so the live source did not move. 🔴 **France is nevertheless still `layout_ready_count = 0`**, and the readiness summary now reports the 522 recovered rows under one token, `UNMAPPABLE_RESIDENTIAL_TYPE: 522`. The second blocker was therefore quantified and written up as **decision request `D-EU-04-G`**, `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_FR_typology_2026-08-25.md`, which is **OPEN and blocking**. BD TOPO carries no TABULA-compatible type (all 530 rows `Résidentiel` 524 / `Commercial et services` 6). What it does carry, measured: `nombre_de_logements` on 529 of 530, `nombre_d_etages` on 530 of 530 (median 6, max 16), and computed footprint adjacency — **488 attached, 42 free-standing**. **The FR TABULA registry separates the types itself**: `SFH` and `TH` carry `n_apartment` = 1 in every one of the ten periods at 1–3 storeys, `MFH` spans 4–12 dwellings at 1–4 storeys, `AB` spans 15–86 dwellings at 5–10 storeys — so the boundary is **read off TABULA rather than invented**, which is the whole reason the recommendation is defensible. Recommended **G1** requires the dwelling signal and the storey signal to **agree** and excludes the row when they do not: **302 typed of 530**, **297** of them with a recovered year (**7** `SFH`, **21** `TH`, **123** `MFH`, **146** `AB`); the 228 exclusions are 189 signal disagreements, 37 rows in the registry's own 13–14 dwelling gap, and 2 missing a signal. `S1` (12, three per typology) and `S2` (32) are reachable today under G1; **`S3` (96) cannot be typology-balanced for France because `SFH` caps at 7** in this dense historic quarter — stated now rather than discovered at `S3`. Any derived type must be stamped `DERIVED_BDTOPO_TWO_SIGNAL` and never reported as observed. **No typology rule has been applied and no code was written for it; the manager will not invent one.** **Standing lesson for this arc: a hardcoded "current year" is the same silent-coercion defect with a one-year fuse — bound a plausibility check to a computed value, never to a literal.** The next session must start from this checkpoint, and its first action is to obtain the `D-EU-04-G` ruling.

**Latest superseding continuation snapshot, 2026-08-25T17:20:50Z:** the ruled remedy for the France year blocker is now **specified but not yet executed**. A paste-able executor prompt, `prompts/previous/EXECUTOR_PROMPT_EU-04_fr_year_parse_fix_2026-08-25.md`, carries four tasks with a checkpoint after the third: `T01` replaces the `openubem/acquisition/bdtopo_fetcher.py:94` expression with an **anchored leading-`YYYY` extraction** — never a datetime round-trip, since routing a plain calendar year through `datetime64[ns]` imposes a 1677–2262 range the French stock genuinely violates (1580 is a real observed value here) — and **excludes rather than clamps** years below 1000 or after the current year, so a rejected value becomes `pd.NA` and `finalize_footprints` stamps it `IGN_BDTOPO_MISSING` exactly as a genuinely absent one; `T02` adds a regression fixture in the **real** BD TOPO shape (bare `Z` suffix, a pre-1677 year) plus a **retained non-null-rate assertion**, and requires the executor to prove it by restoring the old expression and watching it fail — the existing fixture at `tests/test_eu02_fetchers.py:20,47` feeds `"1980-01-01"`, suffix-free and post-1677, which is precisely why a total parse failure passed CI; `T03` closes the `[OPEN]` debug-reference bullet **in place**; `T04`, after the checkpoint, runs the pinned `openubem/outputs/eu_evidence/X-10/acquire_bdtopo_manifest.py` as the **single authorized live IGN call** and regenerates the readiness artefacts, reporting any drift from the recorded `expected_raw_boundary_counts` as a finding rather than editing the expectation. 🔴 **A SECOND and independent French blocker was measured while scoping the prompt, and it changes what `D-EU-04-E` can deliver.** All **530** retained French rows carry `building_tag` = `Résidentiel` (**524**) or `Commercial et services` (**6**), while `OBSERVED_TAG_TO_TABULA_TYPE` at `openubem/semantic/european_archetype_mapping.py:30` maps only `apartments`, `detached` and `terrace`. **Recovering the year therefore still leaves every French row excluded on `UNMAPPABLE_RESIDENTIAL_TYPE`, and France still yields `layout_ready_count = 0`.** `D-EU-04-E` was framed on the premise of one missing input; two are missing. The FR TABULA registry holds **40** records across AB/MFH/SFH/TH (10 each), and BD TOPO supplies `nombre_de_logements` (measured: 31 rows at 1 dwelling, 18 at 2, 52 at 3–4, 180 at 5–10, 170 at 11–20, 78 above 20) and `nombre_d_etages` (all 530 non-null, median 6, max 16) but **no TABULA-compatible type tag** — so a French typology derivation is a **new owner ruling**, not an implementation detail, and the executor prompt explicitly forbids inventing one. **This pass wrote no code and ran no test.** The next actions are: dispatch the executor prompt for `T01`–`T03`, review at its checkpoint, release `T04`; and separately obtain the French typology ruling before any S1 group can be formed. **Standing lesson for this arc: a fail-closed mapping contract reports every missing input with the same token, so clearing one blocker does not reveal how many remain — count the exclusion reasons, not the exclusions.** The next session must start from this checkpoint.

**Latest superseding continuation snapshot, 2026-08-25T16:56:39Z:** the owner ruled the two decisions raised in `debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_GEO-08_GEO-10_2026-08-25.md` (now `RULED`): **`D-EU-04-E` = E1** — re-acquire `FR-LYO-HAUTCOEURPENTES` through the existing IGN BD TOPO adapter to form S1, with a **live WFS fetch to `https://data.geopf.fr/wfs/ows` explicitly authorized** under Licence Ouverte 2.0 — and **`D-EU-04-F` = F2** — `GEO-08` Grasshopper parity is **deferred until after S1–S3**, staying honestly open and unclaimed rather than waived, because it gates nothing downstream. Executing E1 began with a bounded live probe of the pinned Lyon bbox `(45.774784, 45.768891, 4.837450, 4.823612)`, and it **overturned the diagnosis the request itself was built on**. The France site was **already** acquired from BD TOPO (`01_source.json`, retrieved 2026-08-25T14:22Z), and the observed inputs are **not missing from the source**: **1,115 of 1,663** raw features carry `date_d_apparition` with real construction dates (`1998-01-01Z`, `1820-01-01Z`, `1580-01-01Z`), and **1,176** carry `nombre_de_logements`. Yet the retained manifest `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg` holds **0 of 530** years, every row stamped `provenance_year_built = IGN_BDTOPO_MISSING` and `data_quality_flag = 'no_year'`. The cause is a **parse defect** at `openubem/acquisition/bdtopo_fetcher.py:94`: `pd.to_datetime(raw["date_d_apparition"], format="mixed", errors="coerce").dt.year` returns `NaT` for **every** BD TOPO value under pandas 3.0.3, because the source formats the field as a date with a bare zone suffix and no time part, and because pre-1677 values fall outside `datetime64[ns]`; `errors="coerce"` then discards both failures silently. Reproduction: `pd.to_datetime(pd.Series(["1998-01-01Z","1820-01-01Z","1580-01-01Z"]), format="mixed", errors="coerce") -> [NaT, NaT, NaT]`. Separately, the dwelling-count half of the blocker **is already solved on disk**: **529 of the 530** retained French residential buildings carry an observed `nombre_de_logements` in `surplus_tags` (median 10, mean 12.0, max 83). **`EU-04`'s `GEO-10`/S1–S3 is therefore blocked by a one-expression parse bug, not by a missing data source** — E1 is narrowed, not overturned: no new adapter and no new source are needed, but the manifest must be rebuilt once the parser is corrected. Registered as an `[OPEN]` entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (European locations X-05 chapter). Evidence: `openubem/outputs/eu_evidence/EU-04/fr_bdtopo_year_availability_diagnosis.json`. **This was a measurement pass under the project's diagnose-before-remediate rule: no fix was applied, no manifest was rebuilt, no building was promoted to layout-ready, no S1 sample group exists, and `GEO-08` was not touched.** The next task is the parser correction — parse the leading `YYYY-MM-DD` explicitly (or take the leading four digits), never a datetime round-trip, and assert a retained non-null rate so a silent coercion can never pass again — followed by a re-run of the pinned Lyon acquisition and of the observed mapping readiness to form S1. **Standing lesson for this arc: `errors="coerce"` converts a parse failure into a data-absence claim, and every downstream document then reports the absence as a property of the source.** The next session must start from this checkpoint.

**Latest superseding continuation snapshot, 2026-08-25T16:34:43Z:** the arc's two outstanding fail-closed rows were **ruled by the owner** and both rulings are now verified on disk and under test rather than merely reported. (1) `EU-04 / GEO-07` GB `SyAv` fractional storeys: **Option A, half-up rounding** — `2.9632 -> 3`, `3.6535 -> 4`, `3.7497 -> 4`, with dwelling stacks `[3,2,2]`, `[4,4,3,3]`, `[5,4,4,4]`; the source floats stay in provenance and every rounded stack conserves `A_C_Ref`. `_rounded_count()` in `openubem/geometry/european_residential.py:298` implements the explicit `floor(x + 0.5)` convention rather than Python's bankers rounding, and `tests/test_eu_dwelling_allocation.py` is 5 passed. `RESPONSE_TEMPLATE_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md` is `RULED` and its analysis request `RESOLVED`. (2) `EU-05` France `F_red_temp`: **Option 1, any strictly positive source multiplier** — the field's semantics change from "strict reduction" to "source multiplier", `openubem/idf/european_controls.py:17` now raises only on `f_red <= 0.0`, and `FR.N.AB.10.Gen.ReEx.001.001` emits its exact `1.0086438144755208` untruncated, so the 40-row France physical registry is no longer fail-closed; the 102-row ES/GB/IT occupant campaign is untouched and every one of those rows remains `<= 1.0`. Covered by `tests/test_eu_hvac_controls.py:75` and the all-142-record check at `:84`. **Provenance caveat:** the executor report claimed `8/8` for that control file; the file holds **7** tests, so the count is a mis-tally — both ruled behaviours are nevertheless explicitly covered, which is what was checked. On top of those rulings, `EU-04` gained **`S0-SMOKE-02`**: the S0 equivalent-envelope EnergyPlus design-day smoke previously exercised the ES SFH fixture alone, and now runs **every S0 typology** — `ES.ME.SFH.04`, `FR.N.TH.09`, `ES.ME.MFH.03`, `ES.ME.AB.01` — and additionally asserts the error file contains **no severe diagnostic**, not merely a `Completed Successfully` line; the France TH fixture drives the newly ruled positive-multiplier control path end to end inside the engine. `tests/test_eu_box_generator.py` is **9 passed in 3.18 s with four real EnergyPlus runs and zero skips**, the complete European suite is **203 passed in 19.72 s**, and the whole repository is **2,146 passed / 55 skipped** with the skip count unchanged from baseline. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_s0_all_typology_energyplus_smoke.log`, `all_european_tests_after_s0_typology_smoke.log`, `full_suite_after_control_namespace_fix.log`. **S0's declared scope — geometry and IDF construction, one fixture per SFH/TH/MFH/AB — is therefore complete.** This remains single-zone equivalent-envelope fixture evidence: it is not an observed building, not an annual run with real weather, not Grasshopper parity (`GEO-08`), and not `GEO-10`/S1–S3. **`EU-04`'s only remaining items are `GEO-08`, blocked on a Grasshopper golden export, and `GEO-10`/S1–S3, blocked on observed construction year plus per-building dwelling count — 1 of 4,186 audited footprints maps and that one still has no dwelling count.** The next session must start from this checkpoint.

**Latest superseding continuation snapshot, 2026-08-25T15:52:41Z:** the generated three-dwelling layout was put through a **real EnergyPlus 23.1 design-day sizing run** for the first time, and the run **failed**, exposing a genuine integration defect rather than confirming the previous checkpoint. `add_european_heating_controls()` named every emitted object after the archetype alone (`EU_AlwaysOn_<archetype_id>`, and likewise for the cooling-off schedule, ventilation, gains and thermostat), but the dwellings of one building share a single archetype by construction, so the three zones overwrote one another and EnergyPlus terminated with **ten severe duplicate-name errors before simulation began**. Every prior control test used a single zone, which is why the whole EU-05 suite was green over a defect that made any multi-dwelling building unrunnable. The fix, in `openubem/idf/european_controls.py`, names the per-zone objects after `zone_name`, emits the two archetype-independent constant availability schedules **once per IDF** and shares them, and raises `ValueError` when controls are requested twice for the same zone so the collision fails in Python rather than in the engine. The fixture now returns `Completed Successfully` with `Beginning Zone Sizing` and still passes the independent GEO-06 reciprocal party-wall reader after readback. Focused tests are **18 passed in 4.58 s** and the complete European suite is **202 passed in 21.01 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_energyplus_design_day_smoke.log` and `all_european_tests_after_control_namespace_fix.log`; the failure mode is registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (European locations X-05 chapter). This is a controlled-fixture **design-day sizing** run only: it does not bypass the live observed-year/dwelling-count block, construct an observed-shell core, run an annual simulation with real weather, prove Grasshopper parity, or complete GEO-10/S1--S3. **Standing lesson for this arc: a single-zone control fixture cannot detect a per-building name collision — exercise every emitter at the multiplicity the fleet actually has.** The next session must start from this checkpoint.

**Latest superseding continuation snapshot, 2026-08-25T15:00:54Z:** `EU-04` now bridges the bounded real-footprint layout kernel to saved-IDF geometry. `european_layout_to_zone_specs()` refuses any fallback or failed partition, converts only a clean explicit-count layout into separately named dwelling-zone inputs, and carries the original Shapely polygons into `extrude_geometry()`. A three-dwelling 30 x 12 m supported layout was extruded, saved, reopened, and passed the independent GEO-06 reader with **four** party-wall faces forming **two** reciprocal pairs. Focused EU-04 tests are **23 passed in 3.08 s** and the complete European suite is **197 passed in 19.64 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_layout_idf_readback.log` and `all_european_tests_after_layout_idf_readback.log`. This is layout-to-IDF integration for a controlled fixture only: it does not bypass the live observed-year/dwelling-count block, construct an observed-shell core, prove Grasshopper parity, run EnergyPlus, or complete GEO-10/S1--S3. The next session must start from this checkpoint and the session-capacity warning at the head of this prompt.

**Latest superseding continuation snapshot, 2026-08-25T14:59:08Z:** `EU-04` now has an explicit unconditioned-core geometry contract for the D-EU-01/TABULA plate semantics. Given an explicit **rectangular conditioned plate** and core area, it attaches a rectangular core externally along the long side, preserving the conditioned plate, exact core area, zero overlap, and a shared boundary. The rotated 20 x 10 m fixture emits its 12 m2 core with 20 m shared contact; a non-rectangular plate fails closed as `NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED`. This is intentionally not applied to real acquired shells: no source provides a declared gross-to-conditioned/core relation, so doing so would silently recategorize source floor area. Focused EU-04 tests are **35 passed in 1.69 s** and the complete European suite is **196 passed in 21.05 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_external_core_contract.log` and `all_european_tests_after_external_core_contract.log`. This closes a local core-geometry contract only; it does not make any observed layout ready, authorize a core inside an observed shell, create IDF surfaces, establish Grasshopper parity, or complete GEO-10/S1--S3. Continue on independently runnable IDF extrusion/readback integration while preserving the observed-building input block.

**Latest superseding continuation snapshot, 2026-08-25T14:57:33Z:** `EU-04` now has a fail-closed observed-building-to-TABULA mapping readiness record over all **4,186** audited residential footprints. It maps only a source `apartments` tag to `AB`, `detached` to `SFH`, and `terrace` to `TH`; `house` is deliberately ambiguous and is not promoted. It further requires an observed integral construction year and delegates the country/type/year selection to the existing strict TABULA resolver. The live manifests yield **one** mapped construction archetype -- London `way/396595550`, `apartments`, observed 1928 -> `GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001` -- but it remains `MAPPED_LAYOUT_BLOCKED_MISSING_DWELLING_COUNT`. The other **4,185** are excluded, not imputed: 2,873 lack both an observed year and unambiguous type; 1,312 lack an observed year. `layout_ready_count=0`. Focused mapping/geometry tests are **33 passed in 1.69 s** and the complete European suite is **194 passed in 21.21 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.{csv,summary.json}`, `targeted_observed_archetype_mapping.log`, and `all_european_tests_after_observed_archetype_mapping.log`. This is mapping-readiness evidence only: it does not authorize year or dwelling-count imputation, core geometry, IDF emission, Grasshopper parity, or GEO-10. The next material input must be an evidence-backed source for observed construction year and per-building dwelling count, or an owner-approved imputation rule that records its provenance.

**Latest superseding continuation snapshot, 2026-08-25T14:54:24Z:** `EU-04` now has a deterministic **real-footprint dwelling-layout** adapter for its deliberately supported contract: a caller must supply a positive integral dwelling count; a broad, convex, no-courtyard Polygon is rotated to its long axis, equal-strip partitioned, rotated back, and independently audited for count, area, gaps, overlap, outside area, and at least 2.50 m exterior-facade contact per dwelling. A 0.1 µm numeric facade band is used only to restore coincident edges after rotation; the 2.50 m rule is unchanged. Narrow footprints, courtyards, non-convex polygons, and multipolygons fail closed under stable reason tokens and emit no zones. The adapter never infers a building's dwelling count from its manifest and emits no unconditioned core, because either action would silently alter the observed-source or conditioned-area contract. Focused EU-04 tests are **33 passed in 2.29 s** and the complete European suite is **191 passed in 21.15 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/targeted_real_footprint_layout_generator.log` and `all_european_tests_after_real_footprint_layout_generator.log`. This is a bounded production-layout kernel, not GEO-08 Grasshopper parity, a complete core adapter, a building-to-archetype/dwelling-count mapping, or GEO-10/S1--S3 completion. Continue with evidence-backed observed-building mapping and core semantics before using any emitted layout as a simulation input.

**Latest superseding continuation snapshot, 2026-08-25T14:38:42Z:** `EU-04` now has its first **real-footprint** GEO-04 feasibility census over the four audited model-ready residential manifests. The fail-closed reader requires a projected CRS, unique building IDs, and valid finite Polygon geometry; it records per-building source IDs, manifest SHA-256, minimum rotated-rectangle width, courtyard/non-convex topology, and the stable narrow rule. Across **4,186** clean footprints it records **1,848** `NARROW_FOOTPRINT_LT_8M` fallbacks, **388** courtyard footprints, and **3,062** non-convex footprints; every row remains `dwelling_layout_emitted=false`. Site totals are ES 1,194/287 narrow, FR 530/117, GB 1,242/1,034, and IT 1,220/410. Focused EU-04 tests are **27 passed in 2.23 s** and the complete European suite is **185 passed in 17.44 s**. Evidence: `openubem/outputs/eu_evidence/EU-04/real_footprint_feasibility.{csv,summary.json}`, `targeted_real_footprint_feasibility.log`, and `all_european_tests_after_real_footprint_feasibility.log`. This is pre-layout input evidence only: it neither infers typology or dwelling counts nor emits dwelling/core/IDF geometry, Grasshopper parity, or GEO-10 sample groups. Continue with a deterministic real-footprint dwelling/core layout generator and its audit; do not count narrow fallbacks as dwelling-level success.

**Latest superseding continuation snapshot, 2026-08-25T14:26:20Z:** EU-02 is **complete**. `NS-02` is `MET` for `ES-MAD-BERRUGUETE`, `GB-LDN-STDUNSTANS`, `FR-LYO-HAUTCOEURPENTES`, and `IT-BOL-GALVANI2`; the final four-site audit is `openubem/outputs/eu_evidence/X-11/eu02_ns02_gate_audit.json`. Each site has live clean footprints, disjoint residential/excluded manifests, count file, and endpoint/licence sidecar under `openubem/outputs/eu02/`. The raw-source census evidence is retained separately for Lyon and Bologna; do not replace it with model-ready-clean counts. `X-09`–`X-11` are closed. The next unblocked work is EU-04 real-footprint geometry, consuming these clean manifests; do not re-run EU-02 selection or acquisition absent a reproducibility request.

**Latest user-directed continuation snapshot, 2026-08-24 (closure):** EU-02 neighbourhood selection was **executed in-session, not delegated**, and is closed. The executor prompt is archived at `previous/EXECUTOR_PROMPT_EU-02_neighbourhood_selection_2026-08-24.md` and the result report moved to `../outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md` (Revision B; Revision A retained at `../debugs/docs/DONE-docs/EU02_neighbourhood_selection_2026-08-24_revA_superseded.md`). All four fixed cities - Madrid, London/England, Bologna, Lyon - are SELECTED with checksummed official boundaries. Nothing was acquired into the repository: no footprint manifest, no geometry, no IDF, no simulation. No external response may by itself change a selected status, satisfy `NS-05`, substitute a residential classifier, create a footprint manifest, or authorize real-footprint EU-04 geometry; substantive conflicts require a dated decision/analysis record and, where a choice is required, an owner ruling.

**Latest superseding continuation snapshot, 2026-08-24T15:14:58Z:** `EU-04` now has local GEO-06 saved-IDF reciprocal party-wall evidence. The reusable reader requires every `Wall` with `Outside_Boundary_Condition=Surface` to have one existing reciprocal wall with a two-way reference, a different zone, and matching vertices. A reopened two-dwelling fixture has two party faces and exactly one reciprocal pair; a missing reference and a mismatched-vertex mutation both fail after readback. Focused tests are 24 passed in 1.47 s and the full European suite is 182 passed in 18.77 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo06_reciprocal_party_wall_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo06_reciprocal_party_wall_audit.log`). This is local saved-IDF audit evidence only: no European dwelling-stack generator, real-footprint layout, Grasshopper parity, sample group, or energy simulation was emitted. Continue independent work.

**Prior superseding continuation snapshot, 2026-08-24T15:10:55Z:** `EU-04` now has local GEO-04 narrow-footprint feasibility evidence. The European-only gate measures the minimum-rotated-rectangle short side and applies the registered `<8 m` rule with stable `NARROW_FOOTPRINT_LT_8M`; a 6.0/7.99/8.0/9.0 m sweep proves the strict boundary, and rotating a 7.5 m plate leaves the decision unchanged. Any narrow result is explicitly `FALLBACK_ONE_ZONE_PER_FLOOR`, emits no dwelling layout, and therefore cannot masquerade as dwelling-level success. Focused tests are 21 passed in 0.10 s and the full European suite is 179 passed in 16.12 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo04_narrow_fallback.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo04_narrow_fallback.log`). This is a local feasibility contract only: no real footprint, production European dwelling/core polygons, Grasshopper parity, sample group, or IDF geometry was emitted. Continue independent work.

**Prior superseding continuation snapshot, 2026-08-24T14:47:05Z:** The owner has ruled `EU-04` GEO-07 Option A: half-up round the three GB `SyAv` source `n_Storey` values to `3, 4, 4`, preserve the original floats in registry provenance, and derive each physical plate from `A_C_Ref / n_storey_rounded`. The allocation kernel and its registry fixture prove both exact conditioned-area conservation and the required first-storey quotient/remainder allocations: `[3,2,2]`, `[4,4,3,3]`, and `[5,4,4,4]`. Focused tests are 5 passed in 0.04 s and the full European suite is 172 passed in 19.48 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo07_syav_storey_rounding.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo07_syav_storey_rounding.log`). This resolves the prior fractional-storey authority block only: no production TABULA dwelling/core polygons, real-footprint layout generator, Grasshopper parity, sample group, or IDF geometry were emitted. Continue independent work.

**Prior superseding continuation snapshot, 2026-08-24T13:46:50Z:** `EU-04` now has local GEO-05 courtyard-topology audit evidence. A 144 m² supplied footprint with a 16 m² courtyard hole accepts four dwellings that cover precisely the 128 m² valid plate; a replacement dwelling intruding into the courtyard fails with `OUTSIDE_FOOTPRINT`. Focused tests are 13 passed in 0.06 s and the full European suite is 171 passed in 19.18 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo03_geo05_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo05_partition_audit.log`). This is an independent local audit contract only: no production TABULA dwelling or core polygons, courtyard layout generator, Grasshopper export/parity, sample group, or IDF geometry were emitted. The three GB fractional-storey `SyAv` rows remain fail-closed; continue independent work.

**Latest superseding continuation snapshot, 2026-08-24T13:45:29Z:** `EU-04` now has local GEO-03 non-convex partition-audit evidence. A manually supplied L-shaped 80 m² plate is cleanly divided into five valid dwelling polygons, preserving count and area with zero gap, overlap, and outside area. Focused tests are 12 passed in 0.06 s and the full European suite is 170 passed in 19.07 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo03_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo03_partition_audit.log`). This is an independent local audit contract only: no production TABULA dwelling polygons, deterministic non-convex subdivision generator, Grasshopper export/parity, sample group, or IDF geometry were emitted. The three GB fractional-storey `SyAv` rows remain fail-closed; continue independent work.

**Latest superseding continuation snapshot, 2026-08-24T13:38:47Z:** `EU-04` now has local GEO-02 orientation-invariance evidence in addition to its supplied-floor-partition audit. Rotating both the clean 96 m² plate and its four supplied dwelling polygons by 31° preserves count, union area, and zero gap, overlap, and outside area. Focused tests are 11 passed in 0.06 s and the full European suite is 169 passed in 15.93 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo02_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo02_partition_audit.log`). This is an independent local audit contract only: no production TABULA dwelling polygons, inverse-transformed layout output, Grasshopper golden export/parity, sample group, or IDF geometry were emitted. The three GB fractional-storey `SyAv` rows remain fail-closed; continue independent work.

**Latest superseding continuation snapshot, 2026-08-24T12:51:51Z:** `EU-04` now has a local GEO-01/GEO-09 supplied-floor-partition auditor. Its clean 96 m² axis-aligned four-dwelling fixture has exact count and area conservation with zero gap, overlap, and outside area; named gap, overlap, outside, and count mutations fail their respective checkpoints. Focused tests are 10 passed in 0.05 s and the full European suite is 168 passed in 16.39 s (`openubem/outputs/eu_evidence/EU-04/targeted_geo01_geo09_partition_audit.log`, `openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo01_geo09_partition_audit.log`). This is an independent local audit contract only: no production TABULA dwelling polygons, Grasshopper golden export/parity, sample group, or IDF geometry were emitted. The three GB fractional-storey `SyAv` rows remain fail-closed; continue independent work.

**Latest superseding continuation snapshot, 2026-08-24T12:38:30Z:** `EU-05` now has a local EnergyPlus sizing/design-day acceptance for its runnable S0 ES SFH equivalent-envelope fixture. The fixture completes zone sizing and independently requires the retained `eplusout.eio` zone-sizing record to contain one nonzero **16,352.93390 W** calculated heating load. The new focused test passes and the full European suite is 162 passed in 15.60 s (`openubem/outputs/eu_evidence/EU-05/targeted_hvac_sizing_design_day.log`, `openubem/outputs/eu_evidence/EU-05/all_european_tests_after_hvac_sizing.log`). This is local S0 fixture evidence only: S1–S3, full dwelling/core acceptance, the France `F_red_temp` authority issue, real weather, and campaign execution remain pending or blocked. Continue independent work; do not normalize or emit the blocked France row.

**Latest handoff configuration, 2026-08-24T11:53:11Z:** this file is the sole active manager prompt for future sessions. The separate `EXECUTOR_X-01_paste_into_codex.md` file is historical, explicitly superseded, and not maintained. No implementation result or work-package status changed; walkthrough Table 4 and the append-only CSV record this documentation-only change. Continue the first unblocked local dependency: EU-05 sizing/design-day acceptance. Preserve all current EU-04, France-multiplier, EU-06, and EU-07 blocks.

**Latest superseding continuation snapshot, 2026-08-24T09:52:09Z:** `EU-05` now has an all-102-row ES/GB/IT local HVAC-control audit. Heating-only IdealLoads, constant natural air, and all-convective gains are emitted for every occupant-campaign record; invalid air inputs fail before an IDF is written. France baseline row `FR.N.AB.10.Gen.ReEx.001.001` carries `F_red_temp=1.0086438144755208`, outside the current ruled reduction range, and remains fail-closed under `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-05_FR-Fred-temp_2026-08-24.md`. The full European suite is 161 passed in 18.52 s (`openubem/outputs/eu_evidence/EU-05/all_european_tests_after_hvac_controls.log`). Continue independent work; do not normalize or emit that France row without a rule. `EU-04`, `EU-06`, and `EU-07` retain their existing blocks.

**Latest superseding continuation snapshot, 2026-08-24T09:47:31Z:** `EU-08` now has a 5/5-tested dependency-digest cache wrapper. It computes file SHA-256 values for IDF, emitted schedule, and weather, and canonically includes EnergyPlus build identity, adapter configuration, and source commit. A cache hit requires all of that digest evidence plus the legacy output markers and `status=success`; marker-only completion is never sufficient. The complete European suite is 156 passed in 14.33 s (`openubem/outputs/eu_evidence/EU-08/all_european_tests_after_dependency_digest_cache.log`). This is local fixture-contract evidence only: actual physical inputs and campaign execution remain pending. Continue other independent local work; `EU-06` f>0, `EU-07` live weather, and `EU-04` fractional-storey authority retain their blocks.

**Latest superseding continuation snapshot, 2026-08-24T01:28:08Z:** `EU-04` now has a partial GEO-07 allocation foundation. It half-up rounds `n_Apartment`, conserves that exact quotient/remainder total across integral storeys, and adds the 6% core outside conditioned TABULA area only at ≥2 dwellings/storey. The three GB `SyAv` rows carry non-integer `n_Storey`; unlike their apartments, this field has no approved rounding rule. They are fail-closed and analyzed in `debugs/docs/DONE-docs/ANALYSIS_REQUEST_EU-04_GEO-07_GB-SyAv-storeys_2026-08-24.md`; do not emit their geometry or IDFs. Four focused tests pass and the full European suite is 154 passed in 14.10 s (`openubem/outputs/eu_evidence/EU-04/all_european_tests_after_geo07_dwelling_allocation.log`). Continue other independent local work. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Prior superseding continuation snapshot, 2026-08-24T01:24:42Z:** `EU-09` now closes V8.d locally. Every S0 saved IDF persists its own explicit Zone area, volume, and equivalent per-storey height; the independent text audit derives integral storeys and verifies an exact archetype token in that file's saved surfaces before comparison. Reused paths, swapped files, omitted fields, and any geometry mismatch fail. Twelve focused tests pass and the full European suite is 150 passed in 14.32 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8d_saved_idf_audit.log`). This is local fixture-contract evidence only; retained campaign artefacts remain pending. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Prior superseding continuation snapshot, 2026-08-24T01:04:08Z:** `EU-09` now closes V8.c locally: fixed G8.1–G8.6/G8.10 bands are imported from one immutable module, while G8.7 remains an explicit archetype-specific input rather than a generic copied threshold. Two focused tests pass and the full European suite is 149 passed in 14.23 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_v8c_band_source.log`). This remains local contract evidence only; retained campaign artefacts and V8.d per-archetype retained-IDF audit remain pending. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T01:02:34Z:** `EU-10` now writes a fail-closed machine-readable dossier report only if it receives exactly G8.0–G8.16, all passed at hard severity, plus measured SHA-256 digests for the campaign manifest and result bundle. An explicit evidence scope distinguishes `local_fixture_contract` from `retained_campaign`, so a fixture can never masquerade as campaign evidence. Ten focused tests pass and the full European suite is 147 passed in 14.14 s (`openubem/outputs/eu_evidence/EU-10/all_european_tests_after_dossier_contract.log`). This is schema/fixture evidence only: retained campaign artefacts and final dossier evidence remain pending. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T01:00:50Z:** `EU-10` now has a read-only retained `eplusout.csv` extractor for heating, cooling, lighting and equipment. It fails closed unless the CSV contains `Date/Time`, all four hourly J variables and exactly 8,760 non-leap calendar rows; extracted annual/monthly/hourly series must then satisfy the existing explicit-weather-window/four-end-use closure contract. It neither reads facility/service meters nor adds TABULA DHW to simulated series. Eight focused tests pass and the full European suite is 145 passed in 14.92 s (`openubem/outputs/eu_evidence/EU-10/all_european_tests_after_retained_csv_extraction.log`). This is fixture-contract evidence, not a campaign run: campaign output capture and formal dossier export remain pending. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:57:08Z:** `EU-09` now exports the frozen P01–P12 Table 17 fixture matrix and cross-tabs every specified expected-fail/expected-clean transition against a clean local baseline. It rejects a missing probe, a named mutation whose required gate remains clean, and an explicitly clean gate that becomes dirty. P05 preserves the G8.12 assignment/value distinction; P12 proves all observed checkpoints stay clean. Four focused tests pass and the full European suite is 143 passed in 14.05 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_perturbation_coverage.log`). This is local fixture-contract evidence, not a campaign run: retained campaign artefacts plus the V8.c band source and V8.d retained-input audit remain pending. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:50:42Z:** `EU-10` corrects its local cell schema from a misleading scalar weather year to an explicit approved weather window, then adds within-fold aggregation plus deterministic JSON bundle export. The aggregate refuses cross-window inputs, preserves 12-month/8,760-hour closure, derives a peak, and keeps `q_w_nd` as labelled post-processing rather than a simulated time-series load. Its six focused tests pass; the full European suite is 139 passed in 18.65 s (`openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_aggregation.log`). Retained-output extraction and dossier export remain unimplemented and unclaimed. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:36:51Z:** `EU-10` now has a tested cell-result contract in `openubem.results.european_campaign`. It refuses an unnamed weather identity/year, invalid denominator or coefficient checksum, non-closing annual/monthly/hourly four-end-use energy series, and any physical service-load double count. It reports a derived peak and leaves TABULA `q_w_nd` explicitly outside simulated time series. Its four focused tests pass; the full European suite is 137 passed in 16.83 s (`openubem/outputs/eu_evidence/EU-10/all_european_tests_after_result_record_contract.log`). Retained-output extraction, aggregation, and dossier export remain unimplemented and unclaimed. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:34:45Z:** `EU-09` has local, parent-aligned contracts for every G8.0–G8.16 gate. The new six focused tests establish G8.5 peak magnitude (±15%), G8.6 peak timing (≤1 hour) against a mandatory named comparison series, and G8.7 as-modelled EUI-band grading with an explicit floor-area identity check; empirical comparison is informational only. The >15% peak, two-hour shift, and 1.5× wrong-geometry mutation fail. The full European suite is 135 passed in 13.97 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_peak_geometry_gates.log`). `EU-09` remains in progress: it has not evaluated retained campaign artefacts and has not yet implemented the complete V8 coverage cross-tab. `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:30:12Z:** `EU-10` is `PARTIAL` rather than unstarted. `openubem.results.european_campaign` enforces the accepted `four_end_use_tabula_dhw` accounting mode: it reports the four simulated end uses and one explicit TABULA DHW value, rejecting physical service loads to prevent double counting. Its 2 focused tests pass; the full European suite is 129 passed in 16.43 s (`openubem/outputs/eu_evidence/EU-10/all_european_tests_after_four_end_use_accounting.log`). Result extraction, aggregation, and dossier export remain unimplemented and unclaimed. `EU-09` retains G8.5–G8.7, while `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:28:47Z:** `EU-09` remains `PARTIAL`, now with thirteen focused tests. G8.1–G8.4 implement the fixed monthly/hourly NMBE and CV(RMSE) reproducibility thresholds and carry the required non-measured-validation disclaimer. The clean rerun passes; the 1.2 energy-scale mutation fails G8.1/G8.3. The full European suite is 127 passed in 14.12 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_reproducibility_gates.log`). G8.5–G8.7 peak and geometry gates are unimplemented and unclaimed; `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:22:36Z:** `EU-09` remains `PARTIAL`, now with eleven focused tests and G8.15/V8.f warning-kind triage. Its test fixtures prove that a single unclassified warning cannot be hidden by frequency, and that severe/fatal diagnostics fail hard. The full European suite is 125 passed in 16.45 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_warning_gate.log`). Geometry and numerical-output gates remain unimplemented and unclaimed; `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:21:15Z:** `EU-09` remains `PARTIAL`, now with eight focused tests and G8.12/G8.13 independently reading saved IDF text plus the gain file SHA-256. The correct artifact passes; an incorrect consuming-object schedule fails G8.12 and `Interpolate to Timestep = Yes` fails G8.13. The full European suite is 122 passed in 17.28 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_saved_idf_gates.log`). Warning, geometry, and numerical-output gates remain unimplemented and unclaimed; `EU-06` f>0 and `EU-07` actual weather retain their external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:19:33Z:** `EU-09` remains `PARTIAL`, now with 7 focused local tests. The meter-artifact layer parses the actual produced MDD text and implements G8.10 (component balance) and G8.11 (required names) in addition to the prior pre-submission gates. The pre-9.4 `Gas:Facility` mutation fails both gates and a zero component fails G8.10 while retaining G8.11. The full European suite is 121 passed in 16.52 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_meter_gates.log`). Saved-IDF, warning, geometry, and numerical-output gates remain unimplemented and unclaimed; `EU-06` f>0 and `EU-07` actual weather retain their respective external blocks.

**Latest superseding continuation snapshot, 2026-08-24T00:16:55Z:** `EU-09` is now `PARTIAL` rather than unstarted. `openubem.validation.step8_gates` implements the non-engine contract subset G8.0 (control before injection), G8.8 (distinct emitted schedules), G8.9 (dependency digest), G8.14 (immutable manifest), and G8.16 (held-out fold). Its three focused tests include a clean null fixture and designated corruptions; the full European suite is 117 passed in 16.09 s (`openubem/outputs/eu_evidence/EU-09/all_european_tests_after_pre_submission_gates.log`). Meter, saved-IDF, warning, geometry, and numerical-output gates are still unimplemented and unclaimed. `EU-06` f>0 remains upstream-blocked on chaining and `EU-07` live acquisition remains externally blocked on CDS credentials.

**Latest superseding continuation snapshot, 2026-08-23T23:42:00Z:** `X-01`, `X-02`, `X-03`,
`X-04`, `X-05`, `X-06`, and `X-08` are `LOCAL_PASS`. The S0 equivalent-envelope implementation
independently reads back every fixture's reduced `h_Transmission`; its SFH heating-only EnergyPlus
fixture completes with zero severe errors. Evidence is
`openubem/outputs/eu_evidence/X-05/equivalent_envelope_and_controls_pytest.log` (17 passed in
3.59 s) and `openubem/outputs/eu_evidence/X-05/all_european_tests_after_s0.log` (98 passed in
13.12 s); the full European suite now passes 114 tests in 13.25 s
(`openubem/outputs/eu_evidence/X-07/all_european_tests_after_weather_registry.log`). `X-07` is `PARTIAL`: `openubem/data/weather/weather_registry.json` is a deterministic
`RULED_NOT_PINNED` template, and `tests/test_eu_weather_registry.py` passes 6/6 offline checks for
secret-safe credential detection plus DR08 gates 1–4. It remains externally blocked on CDS
credentials for live ERA5, CDS-served licence capture, diary-window pinning, DR08 gate 5's national
benchmark, and gate 6's EnergyPlus smoke. The next manager session continues the next unblocked local
slice, not S0 rework. `EU-06` is `PARTIAL`: its local external-file f=0 path passes 7/7 focused
tests and records zero-presence days, but it must not emit f>0 without the upstream chaining rule;
real Step 7 input and saved-IDF assignment read-back remain outstanding. `EU-08` is `PARTIAL`:
its deterministic campaign plan has 102 Q3 controls and 408 Q4 rows, but no simulation may be
submitted until weather, IDFs, schedule inputs, and the pre-registered gates are ready.
The broader MVP work packages `EU-04` and `EU-05` remain `IN_PROGRESS`: X-05/X-06 are verified
S0 sub-slices, while their S1–S3/layout and sampled-dwelling gates remain outstanding.

**Live continuation snapshot, 2026-08-23T22:25:00Z (supersedes older X-04 wording below):**
`X-01`, `X-02`, `X-03`, `X-04`, and `X-08` are `LOCAL_PASS`; X-04's independently re-verified
evidence is 9/9 physics and 94/94 European tests. `X-05` and `X-06` are the current `IN_PROGRESS`
work: implement and validate an area-faithful equivalent-envelope saved-IDF emitter, then integrate
the heating-only fixture. The TABULA aggregates must not be silently reshaped into a false closed
prism. `X-07` is `IN_PROGRESS`, externally blocked only by missing CDS credentials for live ERA5.
MVP §9.7 and `content/table_9_7_work_packages.csv` are the human and machine-readable WP-status
views. On every material state change, update this snapshot, MVP §9.7, and both append-only
walkthrough logs.

**Status correction, 2026-08-23T22:08:25Z (this paragraph supersedes older R3 wording in this section):** `X-04` is `LOCAL_PASS` and accepted under the recorded R3-A/R3-B ruling. The analytical one-node R3 primitive remains normative; the revised EnergyPlus fixture uses natural convection and proves non-stagnating physical decay. Independent evidence: 9 physics tests passed in 2.92 s and 94 European `test_eu_*.py` tests passed in 12.28 s (`openubem/outputs/eu_evidence/X-04/targeted_pytest_complete_reverified.log`). The repository-wide rerun stalled at 10% on the known Windows/joblib process issue and is not claimed as complete. `X-05` and `X-06` remain the active local implementation work; `X-07` remains blocked only by absent CDS credentials.

**Current accepted slice status (2026-08-23T20:50:00Z):** `X-01`, `X-02`, `X-03`, and `X-08` are `LOCAL_PASS`; see their corresponding `openubem/outputs/eu_evidence/X-*/` directories. `X-04` is `PARTIAL`: R5 and R7 pass under the accepted engine-aware R5 criterion, while the local executable R3 fixture remains a strict expected failure (19.998714 C at tau versus the DR11 target 7.357589 C). Its complete evaluator packet is `debugs/docs/DONE-docs/ANALYSIS_REQUEST_X-04-R3_X-07-CDS_2026-08-23.md`; do not change R3's strict criterion without a recorded resolution. `X-05` is `PARTIAL`: its deterministic four-type D-EU-01 box plans and full source-coefficient readback pass 60 targeted tests; saved-IDF envelope emission remains. `X-06` is `PARTIAL`: saved-IDF heating-only, no-cooling, gain, ACH, and `F_red_temp` control emission passes 7 targeted tests; it awaits integration with X-05 geometry and a heating fixture. `X-07` is `PARTIAL`: `cdsapi`/`pvlib`/`xarray` are installed, but live ERA5 retrieval remains blocked by absent CDS credentials. X-01's targeted suite passed 24/24; its full-suite rerun stalled at 89% after unrelated Windows/joblib access violations in `tests/test_step3_orchestrator.py`. X-02's six targeted registry tests pass, X-03's 47 tests cover all 22 band boundaries, and X-08's combined 81 tests re-derive the France physical registry.

| Slice | Scope | Status | Evidence |
|---|---|---|---|
| `X-01` | CP0 baseline capture + EU-01 reconciliation loader over parent tables; fixture copy with SHA-256; one negative test | `LOCAL_PASS` | `openubem/outputs/eu_evidence/X-01/` |
| `X-02` | EU-01 registry JSON (`es`/`gb`/`it`) + EU boundary-condition join + `TABULA_PROVENANCE.md` + `exclusions.csv` | `LOCAL_PASS` | `openubem/outputs/eu_evidence/X-02/` |
| `X-03` | EU-02 22-band `tabula_period()` with boundary tests; multi-/no-match error path | `LOCAL_PASS` | `openubem/outputs/eu_evidence/X-03/` |
| `X-04` | EU-03 single-surface fixtures proving D-EU-02 arithmetic (NoMass U, `InternalMass` = `c_m`, `OtherSideCoefficients` 0.5/0.5) **+ the three DR11 §4 numeric fixtures** (R3 time constant 7.3576 °C ± 0.05 at τ; R5 flux 20.000 W ± 0.001; R7 scaling ratio 0.8500 ± 0.0001) | `PARTIAL` | R5/R7 pass; 8 passed, 1 strict R3 xfailed. The executable R3 fixture measures 19.998714 C at tau versus the DR11 target 7.357589 C; see `openubem/outputs/eu_evidence/X-04/targeted_pytest_r3_fixture.log`. |
| `X-05` | EU-04 box generator from TABULA areas (D-EU-01) on the S0 fixtures + `h_Transmission`/`h_Ventilation` read-back + GEO-01 | `PARTIAL` | 60 targeted tests pass: four S0 plans conserve ruled area/volume/walls and all source coefficients read back. Saved-IDF emission remains; `debugs/docs/DONE-docs/DECISIONS_X-05_s0-box-plan-2026-08-23.md`. |
| `X-06` | EU-05/EU-07 heating-only ideal loads, constant air change, `F_red_temp` multiplier, Q1 list prepared | `PARTIAL` | 7 saved-IDF control tests pass. Integrate S0 geometry-surface emission and run the heating-only fixture next. |
| `X-07` | EU-07 weather: ERA5 fetch (Madrid 2009–10, London 2014–15, Bologna 2013–14) → EPW via `pvlib` + six-gate checklist (DR08 §6) → `weather_registry.json` with the CDS-served licence text; 12-month pinning script (`RULED_NOT_PINNED` until corpus dates read) | `PARTIAL` | `cdsapi`, `pvlib`, and `xarray` are installed; live retrieval remains blocked only by absent CDS credentials. |
| `X-08` | EU-01 (FR): France registry from the pinned workbook — assert 50 existing rows, adopt 40 `FR.N`, exclude 10 `FR.OPHM` with reasons; `tabula_archetypes_fr.json` + FR bands in `tabula_period()` + tests | `LOCAL_PASS` | `openubem/outputs/eu_evidence/X-08/` |
| `X-09` | EU-02/EU-04 acquisition: shared footprint-schema tail, boundary clip/split, and live OSM acquisition for `ES-MAD-BERRUGUETE` and `GB-LDN-STDUNSTANS` | `CLOSED 2026-08-25` | Live manifests and evidence: `openubem/outputs/eu02/{ES-MAD-BERRUGUETE,GB-LDN-STDUNSTANS}/`; `openubem/outputs/eu_evidence/X-09/` |
| `X-10` | EU-02 (FR): IGN BD TOPO® V3 adapter, `usage_1/2` crosswalk, live `FR-LYO-HAUTCOEURPENTES` manifest, and raw-source reconciliation | `CLOSED 2026-08-25` | Raw-source counts are 891 / 23 / 544 / 278 / **46** (total / annex / residential / unknown / non-residential); model-ready-clean counts remain separately recorded. Evidence: `openubem/outputs/eu_evidence/X-10/` |
| `X-11` | EU-02 (IT): Comune di Bologna Opendatasoft adapter, complete 30-value CTC crosswalk, live `IT-BOL-GALVANI2` manifest, CTC-to-cadastral relation, and final gate audit | `CLOSED 2026-08-25` | T07 records 2,188 CTC candidates, 231 components, 1,312 CTC-touched cadastral objects, 1,372 ruled cadastral objects, and ISTAT 1,010. Final audit: `openubem/outputs/eu_evidence/X-11/eu02_ns02_gate_audit.json` |
| — | EU-02 residential filter, candidate-neighbourhood metrics, and acquisition (`NS-02`) | `CLOSED 2026-08-25` — all four sites are selected, acquired, reconciled, and audited. `NS-02` is `MET`; hand off the clean manifests to EU-04. | `outputs/EU02_neighbourhood_selection_2026-08-24/`; `openubem/outputs/eu02/` |

(Walkthrough §12.4 carries X-01–X-03 in full, §12.5 the X-04–X-06 outlines, and §12.6 the X-02/X-04 amendments plus X-07/X-08; X-02 was extended the same evening with the eleven extra `Calc.Set.Building` columns the rulings need, and again after DR09 acceptance: `TABULA_PROVENANCE.md` gets the verbatim clause and the licence field becomes `VERIFIED`.)

Update this ledger at every acceptance; it is the only prompt-local progress summary outside the
walkthrough log.

### 19.6 Fresh-session restart checklist

1. Read this prompt's head box and §19.5; then read the last ten rows of
   `content/walkthrough_progress_log.csv` and Table 4 in the walkthrough. Treat the newest dated row
   as the operational state if wording differs.
2. Inspect `git status --short`, `git diff --stat`, and the named evidence directory before changing
   code. The worktree is intentionally dirty; preserve all unrelated changes and never commit.
3. If the user has supplied the external EU-02 executor response, perform the required EU-02 intake
   and reconciliation before selecting a real-footprint action. Otherwise continue the first
   unblocked local dependency in the current ledger. Do not repeat tests merely to recreate evidence
   that already exists.
4. For every material result append the same UTC row to **both** Table 4 and
   `content/walkthrough_progress_log.csv`, with command, evidence path, observed result/blocker, and
   next action. Update this §19.5 ledger at the same time.
5. A response after the executor has ended is not background execution. A later session resumes only
   from the recorded state; it must not claim it continued while inactive.

**Latest post-remedy measurement, 2026-08-25T20:10:32Z:** `EU-04` S2 was re-measured after the ruled G1/V1 implementation with `scripts/scope_eu_s2.py`. The 4,186-row manifest is unchanged: 297 mapping-ready rows, 28 `dwelling_layout_emitted` rows, and 269 fail-closed fallbacks (`200` non-convex, `58` narrow, `11` courtyard). The original 32-case rule (two rows per type × age band × completeness cell) remains `s2_target_formable=false`; no sample was selected and no completeness claim was inferred. Evidence is the refreshed `openubem/outputs/eu_evidence/EU-04/s2_scope_summary.json` and `s2_scope.csv`. Next action: resolve the missing completeness strata or record an owner-approved S2 rule change; geometry remedies are complete.
The measurement CSV filename is `s2_scope_measurement.csv` (the summary JSON is alongside it); the prior shorthand `s2_scope.csv` above should be read as that artifact.

**S2 completeness decision guidance, 2026-08-25:** The current 32-case rule cannot be completed honestly by simply relabeling rows. The missing cells represent absent source completeness, not a geometry failure. Two legitimate paths remain:

1. **Preserve the current 32-case rule.** Add or reconcile source data so every combination of the four building types (`AB`, `MFH`, `SFH`, `TH`), two age bands (pre-1945/post-1945), and two completeness bands (high/low) has at least two genuinely incomplete-but-typed-and-dated buildings. This is 32 rows total. Only one eligible low-completeness row currently exists (`AB|OLD_PRE_1945`), so approximately 31 additional qualifying low-completeness rows are required. Each row needs defensible building type and construction year while still lacking another required mapping input; provenance must be recorded and the readiness audit regenerated.

2. **Recommended — revise the S2 ladder.** Keep the available mapping-ready buildings, define completeness independently from geometry/layout feasibility, report geometry outcomes as a separate audit dimension, and do not fabricate low-completeness rows. This changes the sampling definition and therefore requires an owner ruling before implementation.

**Recommendation:** pursue option 2. The corpus is sufficient to evaluate mapping and geometry, but it does not contain enough defensible low-completeness strata for the original ladder. Until an owner-approved amended ladder is recorded, S2 remains `MEASURED_NOT_FORMABLE` and no sample may be claimed.

**Latest S2 completeness decision request, 2026-08-25T20:44:08Z:** `D-EU-04-S2-C` is open at `debugs/docs/DECISION_REQUEST_EU-04_S2_completeness_ladder_2026-08-25.md`. The original 32-cell completeness rule remains unformable, and strict two-per-type/age coverage also fails for new-era SFH (one eligible row). The recommended C1 is a deterministic 32-row **high-completeness operational** sample: eight rows per type, four old/four new wherever available, with SFH recorded as the measured 1-new/7-old exception. Geometry feasibility and fallbacks remain reported outcome columns and are never selection inputs; low completeness remains a census finding, not an invented simulation stratum. No S2 sample may be formed or simulated until the owner records C1, C2, or C3.

**Latest C1 execution checkpoint, 2026-08-25T20:53:42Z:** C1 was ruled, but its stated 32-row composition is impossible in the retained census: the high-completeness SFH stock is **7** (`6` old, `1` new), not `8`. `scripts/form_eu_s2_c1_sample.py` fails closed before a manifest is written; the focused preflight/geometry tests pass **21/21**. No duplicate, incomplete, geometry-selected, or outcome-selected row was substituted; no S2 simulation ran. `D-EU-04-S2-C` now needs an owner amendment defining either a 31-row high-completeness sample or an explicit non-outcome-based quota change. S2 is `STOPPED_NOT_FORMABLE` until then.

**Latest S2 C1A formation, 2026-08-25T20:56:16Z:** the owner adopted the recommended conservative correction: `D-EU-04-S2-C = C1A`, a **31-row high-completeness operational sample**. `scripts/form_eu_s2_c1_sample.py` wrote `openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample.csv` and its checksum-bearing summary. It contains AB/MFH/TH `4 old + 4 new` each and SFH `6 old + 1 new`; all 31 rows are mapping-ready and are selected only by inputs plus `building_id` order. The retained independent geometry observations are 5 `DWELLING_LAYOUT_EMITTED` and 26 `FALLBACK_PENDING_LAYOUT`, not selection criteria. Focused tests are **21/21**. No S2 simulation is authorized or run; the next slice is a separate simulation-scope and audit step.

**Latest S2 C1A audit and simulation scope, 2026-08-25T20:57:22Z:** manager readback confirms 31 unique high-completeness rows, the 8/8/8/7 quotas, independent geometry columns, and equality between the recorded and recomputed source-census SHA-256. The S2 input sample is therefore frozen and audit-accepted. Short-period simulation remains **externally blocked**: `openubem/data/weather/weather_registry.json` is `RULED_NOT_PINNED` / `BLOCKED_NO_CDS_CREDENTIALS` and has no approved Lyon weather window. Do not substitute a different city, synthetic weather, or a design-day smoke as S2; no S2 energy result exists. Next action is to obtain the Lyon weather authority/input, then scope the runner.

**Latest Lyon OneBuilding candidate, 2026-08-25T21:23:32Z:** at user direction, the Lyon–Bron WMO 074800 2011–2025 TMYx archive was downloaded under `openubem/data/weather/candidates/onebuilding_lyon_bron_tmyx_2011_2025/`. Its EPW has a valid header, 8,760 rows, and required fields, but its own comment identifies an NCEI ISD/ERA5 **TMY composite**, not continuous actual weather. It also fails the existing DR08 5 W/m² solar-closure gate (3,389 daytime rows; max 132.834 W/m²). This is a candidate, never a silent replacement: `D-EU-07-OB-LYO` is open at `debugs/docs/DECISION_REQUEST_EU-07_onebuilding_lyon_bron_candidate_2026-08-25.md` with OB1 candidate-only (recommended), OB2 separate TMYx evaluation, and OB3 source-method replacement. The direct CDS/ERA5 registry is unchanged; no S2 simulation ran.
