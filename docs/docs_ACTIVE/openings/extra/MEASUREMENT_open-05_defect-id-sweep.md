# MEASUREMENT — open-05-defect-id-sweep

> **Slug:** `open-05-defect-id-sweep` · **Date:** 2026-08-05 · **Register item:** OPEN-05
> **This is a measurement-only report.** No remediation, renumbering, or edits to any existing
> document were performed or proposed. The only write this task made is this file.

---

## 1. Method

**Search tool:** the Grep content-search tool (ripgrep-backed), run against the full working tree
at `C:\Users\o_iseri\Desktop\OpenUBEM` (no path restriction unless stated). No `rg`/`grep` CLI was
available in the Bash shell (`which rg` → not found), so all pattern matching went through the Grep
tool; deduplication/sorting of the resulting ID lists used the Bash `sed`/`sort`/`uniq` pipeline on
the tool's own persisted output files (not a re-implementation of the search itself).

**Patterns run, in order:**

1. `E-LA-\d+` and `E-UTCI-\d+`, `output_mode: files_with_matches`, no path filter — found the file
   sets touching each prefix (80 files for `E-LA-`, 28 files for `E-UTCI-`).
2. `E-LA-\d+` and `E-UTCI-\d+`, `output_mode: content`, `-n: true`, unlimited (`head_limit: 0`) — full
   line-content dump with file:line for every occurrence (1,210 / 450 matched lines after the tool's
   own truncation-to-disk).
3. `E-LA-\d+` and `E-UTCI-\d+`, `output_mode: content`, `-o: true` (only-matching), unlimited — a
   bare `path:line:E-LA-NN` list per occurrence (1,909 / 528 lines), used to derive the unique ID
   inventory via `sed -n 's/.*\(E-LA-[0-9]\+\)$/\1/p' | sort -t- -k3 -n -u` (and the `E-UTCI-`
   equivalent).
4. Targeted follow-ups per ID: `^#### E-LA-\d+` and `^#+.*E-LA-\d+` (defect-entry headers, the house
   style used throughout the layoutAssigner and UTCI plan docs), then individual `E-LA-NN` /
   `E-UTCI-NN` greps with context (`-C`/`-B`) against the specific plan file each ID's header
   pointed to, to pull the original defining paragraph rather than a later citation.
5. Full read of `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md` (470 lines) — this
   document is itself a **later consolidator**, not an original logging site, but it was read in full
   because it already names the known E-LA-21/E-LA-39 pair and several other open IDs' summaries; every
   number and file:line claim taken from it below was cross-checked against the ID's own original
   defining document, not taken on the register's word alone.

**What could NOT be searched, and why:** nothing. The working tree as checked out right now (including
the paths git shows as recently moved from `docs_ACTIVE/simulation-Resolution/layoutAssigner/...` to
`docs_DONE/SETUP/layoutAssigner/...`) was fully greppable; no binary or excluded-path content was
relevant (the pattern only ever appears in `.md`/`.py` text). `git log`/history was **not** consulted —
"original logging site" below means the earliest-defining *document* found in the current tree (the
task's own instruction: search the working tree as it is now), not the earliest commit.

**Validation of the method:** the known duplicate — E-LA-21 (`e-la-20/PLAN_e-la-20_investigation.md:493`)
and E-LA-39 (`storey-Matching/PLAN_storey-matching_REMAINder.md:1432/1442`) — **was rediscovered**, both
independently by the raw content sweep (step 2/3, both IDs present, both describing the `has_fatal`
double-space defect) and by reading the register's own §3 OPEN-05 entry (step 5). The method is sound
by this test.

---

## 2. Full ID inventory

### 2.1 `E-LA-nn` — 41 IDs found (E-LA-01 … E-LA-41). E-LA-42 exists in text only as a "next free ID"
marker (`docs/PROJECT_CHECKLIST.md:1063`, `INVESTIGATION_open-items-register.md:78`,
`DIRECTOR_PROMPT_openings_2026-08-04.md:209`) — **not a logged defect**, excluded from the table below.

| ID | One-line description (from original site) | Original logging site (path:line) | Status as stated at/near the original site |
|---|---|---|---|
| E-LA-01 | §3.1 measured zone-count table appears wrong for at least MidRise (naive-grep contamination) | `docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:584` | CLOSED — 2026-07-22 |
| E-LA-02 | T08 batch-transition success check unreliable (log-banner grep false-negatives) + a stale duplicate background run | `...DONE-implementation_plan.md:592` | CLOSED — 2026-07-22 |
| E-LA-03 | T09 LIVE_SMOKE-LA process lost/killed mid-run; employee failed to detect it and reported stale "still running" | `...DONE-implementation_plan.md:395` | CLOSED — 2026-07-22 |
| E-LA-04 | T10 pre-fix sanity probe ran the still-unmodified script, transiently overwrote the results doc with fabricated content | `...DONE-implementation_plan.md:600` | CLOSED — 2026-07-22 |
| E-LA-05 | `parser.py`'s zone-integrity gate structurally incompatible with `layout_assign` zone naming | `...DONE-implementation_plan.md:608` | CLOSED — 2026-07-23 |
| E-LA-06 | `scale_baseline_idf()` does not scale fixed-capacity auxiliary equipment; large real warning/severe-error counts at non-identity scale factors | `...DONE-implementation_plan.md:616` | OPEN-BLOCKED-PARTIAL → **RESIDUAL RE-ATTRIBUTED 2026-07-26** (warmup part folded into the E-LA-14/23 lineage; flow-balance part never revisited) |
| E-LA-07 | 3 never-locally-tested archetypes (`LargeOffice`, `TallBuilding`, `SuperTallBuilding`) systematically Fatal at true cluster scale | `...DONE-implementation_plan.md:635` | OPEN-BLOCKED → **BOTH CLASSES FIXED**, verified at T19 (status corrected 2026-07-26) |
| E-LA-08 | E-LA-07 "class 2" warmup-instability Fatal confirmed to also affect `SmallOffice`/`MediumOffice`/`Hospital`, not just `TallBuilding`/`SuperTallBuilding` | `...DONE-implementation_plan.md:645` | OPEN-BLOCKED → **FIXED** (root cause: envelope `MATERIAL:NOMASS` swap) — corrected 2026-07-26 |
| E-LA-09 | `Outpatient` 100% Fatal fleet-wide: `AirLoopHVAC:OutdoorAirSystem` references a non-existent Controller List | `...DONE-implementation_plan.md:653` | OPEN-BLOCKED → **FIXED**; actual root cause was an eppy `IDF.save()` serialization bug, logged separately as **E-LA-13** — corrected 2026-07-26 |
| E-LA-10 | `WaterHeater:Mixed.Peak_Use_Flow_Rate` not scaled by S: silent (non-Fatal) DHW energy distortion, 80% of successfully-simulated fleet | `...DONE-implementation_plan.md:661` | OPEN-BLOCKED → **FIXED** (debug-fixes T01–T03) — corrected 2026-07-26 |
| E-LA-11 | `LargeOffice` DataCenter WSHP plant-loop temperature-runaway Fatal, post-E-LA-07-class-1-fix, at small S | `docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:412` | "surfaced 2026-07-23 (T05)" — no explicit OPEN/CLOSED word at the header; `PROJECT_CHECKLIST.md:875` groups it under the debug-fixes phase that reports "176 recovered, 0 new failures" |
| E-LA-12 | `Daylighting:ReferencePoint` coordinates not scaled by `scale_baseline_idf`: refpoint falls inside/too close to the √S-scaled window plane → Fatal | `...PLAN_debug_implementation.md:424` | OPEN, LATENT/MASKED IN PRODUCTION — 2026-07-23 |
| E-LA-13 | eppy `EpBunch.__repr__` zip-truncation corrupts oversized extensible objects on `idf.save()` → `Outpatient` 100%-Fatal (root cause of E-LA-09) | `...PLAN_debug_implementation.md:433` | OPEN-BLOCKED — 2026-07-23 |
| E-LA-14 | `SecondarySchool` real `n_severe` jump 1→7 (`CheckWarmupConvergence` ×6, new), isolated to T01/T02's `WaterHeater:Mixed` field additions | `...PLAN_debug_implementation.md:456` | OPEN, NOT FATAL, GENUINE REGRESSION — 2026-07-23 |
| E-LA-15 | `SizeAirLoopBranches` minimum-air-flow Fatal at extreme small S, post-T03-fix | `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:270` | OPEN — 2026-07-23 (T04) |
| E-LA-16 | Cooling-coil-design-UA-failed / cooling-tower-UA-autosize-failed family, post-T03-fix, not confined to originally-failing buildings | `...PLAN_structural-fixes_implementation.md:279` | OPEN — 2026-07-23 (T04/T05) |
| E-LA-17 | E-LA-07-class-2/E-LA-08 NOT fully closed by T03: divergence persists in a second zone of the same building despite confirmed mass-bearing materials | `...PLAN_structural-fixes_implementation.md:290` | OPEN — 2026-07-23 (T04) |
| E-LA-18 | `CheckWarmupConvergence` Severe on `CORE_TOP`/`CORE_MID` (LargeOffice), T03-attributable, 3rd archetype family showing this pattern | `...PLAN_structural-fixes_implementation.md:338` | OPEN — 2026-07-23 (T07) |
| E-LA-19 | `way/241836727` (`SecondarySchool`, E-LA-14's regression pair) `CheckWarmupConvergence` zone-composition shift once T03 also live | `...PLAN_structural-fixes_implementation.md:488` | OPEN, informational — 2026-07-24 (T10) |
| E-LA-20 | CTF calculation-convergence Fatal on `Construction="LA_ROOF_CONSTRUCTION"`, 100% concentrated in `nyc_rural` `SmallOffice`, first visible only at fleet scale | `...PLAN_structural-fixes_implementation.md:559` | OPEN, informational — 2026-07-24 → **FIXED, verified 150/150** (`e-la-20/PLAN_e-la-20_investigation.md:516`, CP-C SIGNED 2026-07-25) |
| E-LA-21 | Harvest `has_fatal` column tests `"** Fatal **"` (1 space) vs EnergyPlus's real `"**  Fatal  **"` (2 spaces) → reads `False` on all 8,160 rows | `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:493` | OPEN, informational — 2026-07-25. **Duplicate: see §4, same defect as E-LA-39.** |
| E-LA-22 | 4 `building_tag="hotel"` buildings in `nyc_rural` recorded as `SmallOffice` in the T19 harvest but classify as `SmallHotel` at current HEAD — T19 local repro not archetype-faithful for data-poor buildings | `...PLAN_e-la-20_investigation.md:503` | OPEN, material — 2026-07-25 |
| E-LA-23 | `thermal_mass=True` (the E-LA-20 fix) drives warmup non-convergence on the engaged population: 96/150 (64%) vs 8/150 (5.3%) matched control | `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:1303` (§9 error log) | OPEN, non-blocking — 2026-07-25. Refiled at audit as the 5th locus of the E-LA-14/16/18/19 lineage |
| E-LA-24 | A prior-artifact EUI reference (`f08_run.py:51-53`, hardcoded from an earlier I02 run) was used as if it were a matched control; deltas invert once a true control is run | `...DONE-PLAN_e-la-20_multilayer-fix.md:1309` (§9 error log) | Closed by correction, logged for the generic lesson — 2026-07-25 |
| E-LA-25 | `baseline_area` disagrees with recomputed IDF geometry for 14 of 25 prototypes, up to +473% | `docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/DONE_PLAN_storey-matching_implementation.md:582` | Documented design fact, not tracked OPEN/CLOSED — 2026-07-26 |
| E-LA-26 | `n_proto` ambiguity: geometry vs registry disagree for the two apartment archetypes (3 vs 4/10 storeys) | `...DONE_PLAN_storey-matching_implementation.md:1117` (context), formal reading at `:1222` | Documented, used as an alternate reading in `b00_coverage_census.py` — not tracked OPEN/CLOSED |
| E-LA-27 | Capacity objects (ElectricLoadCenter:Transformer etc.) sized for the unmultiplied building silently corrupt under a `Zone Multiplier` | `...DONE_PLAN_storey-matching_implementation.md:563` (header `B01b — Close E-LA-27`) | NOT closed at first attempt → completed with a documented gap, 2026-07-26 (closed properly by B06) |
| E-LA-28 | Unscaled `Zone` X/Y Origin — building-overlap defect | `...DONE_PLAN_storey-matching_implementation.md:600` (header `B05d — Diagnose the building-overlap defect`) | FIXED and verified in B05 (`docs/PROJECT_CHECKLIST.md:114`) |
| E-LA-29 | `SmallOffice` shows the same unscaled plate as the E-LA-28 population | `...DONE_PLAN_storey-matching_implementation.md:3486` | RESOLVED by the manager 2026-07-26, superseded by E-LA-30 |
| E-LA-30 | The A4-bis viewer artifacts do not depict the real pipeline; its scaler (`fast_scale_idf_text()`) is a content no-op on all 25 prototypes | `...DONE_PLAN_storey-matching_implementation.md:3493` | OPEN, found by the manager at CP-B — 2026-07-26 |
| E-LA-31 | A "before" control was silently a byte-identical copy of the "after" treatment (standing control-validity rule); item 2 = a residual cross-building placement defect | `...DONE_PLAN_storey-matching_implementation.md:3443` | Item 1 CLOSED 2026-07-26 (genuine re-measurement); item 2 later "fixed to sub-mm" (B08a, `r=0.999999998`) |
| E-LA-32 | `Generator:PVWatts`/`ElectricLoadCenter:Generators` scaled by the wrong driver under a storey-matched multiplier | `...DONE_PLAN_storey-matching_implementation.md:3411` | OPEN, energy-affecting — 2026-07-26 → fixed by R03 (`scripts/cluster/t20_layout_assign_full_sweep.py:24`) |
| E-LA-33 | Storey matching is invisible in geometry, and inert for 82–98% of both viewer cells | `...DONE_PLAN_storey-matching_implementation.md:3353` | OPEN — 2026-07-26; still one of two grounds C02 go was withheld on |
| E-LA-34 | The `layout_assign` viewer payload is data-poor and mapless; the grey render is faithful (same origin as E-LA-33) | `...DONE_PLAN_storey-matching_implementation.md:3394` | OPEN — 2026-07-26 → remediated ("viewers made viewable"), then **FROZEN by user instruction** |
| E-LA-35 | Two compounding defects behind the `D_HIGHMULT`/`D_control` EUI mismatch: a hidden prototype `ZoneGroup` multiplier `compute_band_map()` never reads, plus an unpinned `area_scale_ratio` double-counting `WaterUse:Equipment`/`People` | `...DONE_PLAN_storey-matching_implementation.md:3176` | OPEN — diagnosed 2026-07-26 → fixed by R01 (cause A) / R02 (cause B) |
| E-LA-36 | `match_storeys()` compounds `Zone.Multiplier` on top of an existing `ZoneGroup` list multiplier | `docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:403` | NEW, opened by the P1 audit 2026-07-26 → **FIXED** (R10, verified on real EnergyPlus output) |
| E-LA-37 | Editing the `ZoneGroup`'s own Zone List Multiplier field would restore exact storey-matching expressibility (a different mechanism than the one built) | `...PLAN_storey-matching_REMAINder.md:1039` | Forwarded out, not actioned — 2026-07-26 |
| E-LA-38 | `05_results.gpkg` mislabels 100% of the fleet's true Hotel archetypes as Office archetypes (33 `LargeHotel` + 8 `SmallHotel` = 41/8,160) | `...PLAN_storey-matching_REMAINder.md:1436` | OPEN, forwarded (Stage-2 semantic-enrichment defect, outside this arc) — 2026-08-04 |
| E-LA-39 | Harvest `has_fatal` column is inert (cosmetic, no headline number depends on it) | `...PLAN_storey-matching_REMAINder.md:1442` | OPEN, forwarded — 2026-08-04. **Duplicate: see §4, same defect as E-LA-21.** |
| E-LA-40 | Three buildings regress from `success` (T19) to `failed` (T20): `la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403` | `...PLAN_storey-matching_REMAINder.md:1602` | OPEN, forwarded — 2026-08-04. Cause is "plausible and unverified", explicitly a hypothesis |
| E-LA-41 | The published EUI denominator is wrong by `n_storeys_represented / num_floors` for every non-`applied` building in `layout_assign` | `...PLAN_storey-matching_REMAINder.md:1911` | OPEN, forwarded, registered 2026-08-04, not fixed in this arc |

### 2.2 `E-UTCI-nn` — 16 IDs found (E-UTCI-01 … E-UTCI-16). No further numbers exist in the tree.

| ID | One-line description (from original site) | Original logging site (path:line) | Status as stated at/near the original site |
|---|---|---|---|
| E-UTCI-01 | CP-2 gate: horizon-angle SVF formula does not reduce to P-14's analytic canyon check | `docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md:3279` | OPEN-BLOCKED — 2026-07-23 → CLOSED (manager adjudication, CP-2) |
| E-UTCI-02 | CP-2 gate still fails against the E-UTCI-01-corrected target, by a small margin, for a different reason (pedestrian-height mismatch) | `...PLAN_utci_microclimate_implementation.md:3370` | OPEN-BLOCKED — 2026-07-23 → CLOSED |
| E-UTCI-03 | T14 CP-3 gate: no single `Psi_grd`/`Psi_sky`/`Psi_wall` scheme satisfies both the cool-pavement-paradox gate and the open-field/night sanity tests | `...PLAN_utci_microclimate_implementation.md:3461` | OPEN-BLOCKED — 2026-07-24; Part 1 later marked SUPERSEDED/WRONG by E-UTCI-04 |
| E-UTCI-04 | Part-1's "CLOSED" `Psi_grd`/`K_refl` ruling contradicted by direct SOLWEIG source inspection: real ground weight is 0.50 total, not `W_h=0.06` | `...PLAN_utci_microclimate_implementation.md:3628` | OPEN — 2026-07-24 → CLOSED (fixed in `mrt.py`) |
| E-UTCI-05 | E-UTCI-04's fix, once implemented in `mrt.py` (not just the standalone check), breaks the previously-passing canopy-shade test (P-09 gate) | `...PLAN_utci_microclimate_implementation.md:3787` | CLOSED — 2026-07-24 |
| E-UTCI-06 | Night-`Tmrt` residual (`test_night_tmrt_close_to_ta`): ground physics ruled out; the `-5..0°C` tolerance is uncited and likely too tight, no citable replacement found | `...PLAN_utci_microclimate_implementation.md:3897` | STOP → CLOSED — 2026-07-24 |
| E-UTCI-07 | T22 live run on `nyc_centre`: T15's `macdonald` wind tier produces physically impossible values | `...PLAN_utci_microclimate_implementation.md:4026` | OPEN-BLOCKED — 2026-07-24 → CLOSED, re-verified 0 bound violations |
| E-UTCI-08 | E-UTCI-07's fix reduces but does not eliminate the macdonald wind blow-up: a distinct, broader "log-ratio near zero" coincidence persists | `...PLAN_utci_microclimate_implementation.md:4178` | OPEN-BLOCKED — 2026-07-24 → CLOSED, re-verified 0 bound violations domain-wide |
| E-UTCI-09 | T26 cluster-wide harvest: 3–4 of 12 cells have upstream `height_m` data gaps causing zero/near-zero building massing | `...PLAN_utci_microclimate_implementation.md:4303` | OPEN — 2026-07-24 → **MATERIALLY FIXED, DOCUMENTED RESIDUAL** — CP-C SIGNED 2026-07-25 |
| E-UTCI-10 | `spatial_impute.py` silently skips zero-neighbour rows without MNAR-flagging them | `docs_DONE/OUTDOOR/UTCI/e-utci-09/PLAN_e-utci-09_investigation.md:526` | OPEN — 2026-07-25 → **FIXED** (T09 of the height-backfill sub-plan) |
| E-UTCI-11 | Half-landed Phase-D/T12 fusion ship: spec tests committed without the config surface or `_fusion_tier` router body | `docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md:1523` | OPEN → **CLOSED** (config half by T03, router body by T07) |
| E-UTCI-12 | Second half-landed ship: `test_draw_methods.py` references `imputation._draw_tier`, which does not exist → whole `pytest -q` run aborts at collection | `...DONE-PLAN_e-utci-09_height_backfill.md:1552` | OPEN, forwarded — pre-existing, out of scope of the height-backfill plan |
| E-UTCI-13 | T05's height cache stores post-normalization Overture output, silently voiding `levels`/`use_class` on re-read | `...DONE-PLAN_e-utci-09_height_backfill.md:1489` | OPEN, deliberately unfixed — harmless for this plan's `height_m` target, documented not fixed |
| E-UTCI-14 | `test_imputation_routing.py`'s `test_fusion_force_enabled_raises_not_implemented` asserts `_fusion_tier` always raises — obsoleted once T07 implemented it | `...DONE-PLAN_e-utci-09_height_backfill.md:1577` | **FIXED** 2026-07-25 (obsolete stub-raise test retired, manager-ordered) |
| E-UTCI-15 | Two concurrent Stage-6 runs raced on one output directory; root cause was a relaunch without checking for or killing the prior run | `...DONE-PLAN_e-utci-09_height_backfill.md:1656` | **RESOLVED** (process incident) — both trees killed, contaminated dirs destroyed |
| E-UTCI-16 | `config.py`'s fusion comment block claims `fusion` stays OUT of `IMPUTE_ENABLED_TIERS`, contradicting the tuple two lines above it | `...DONE-PLAN_e-utci-09_height_backfill.md:1708` | **FIXED** 2026-07-25 (comment-only correction, user-prompted) |

---

## 3. Gaps

**E-LA-nn: no gaps.** The unique-ID sweep (§1 step 3) returned every integer 01–41 with no missing
number. `E-LA-42` appears only as a forward-looking "next free ID" marker in three documents, never as
a defined defect — it is not a gap, it is the next slot.

**E-UTCI-nn: no gaps.** The unique-ID sweep returned every integer 01–16 with no missing number.

Both sequences are fully dense. There is no evidence of a lost record in either ID space as currently
represented in the tree (this does not rule out a record that was deleted outright and left no
citation anywhere — that would be invisible to a content search by construction, and no such case was
found or suspected).

---

## 4. Duplicate candidates

### 4.1 Confirmed — E-LA-21 = E-LA-39 (the known validation case, rediscovered)

> - **E-LA-21** (`e-la-20/PLAN_e-la-20_investigation.md:493`, 2026-07-25): *"`has_fatal` column is dead
>   fleet-wide in the T17/T18/T19 harvest scripts (reporting-layer defect, no simulation impact)"*
> - **E-LA-39** (`storey-Matching/PLAN_storey-matching_REMAINder.md:1442`, 2026-08-04): *"harvest
>   `has_fatal` column is inert (§4). Cosmetic, no headline number depends on it."* (§4 of the same
>   document, line 1427–1432, gives the mechanism: `has_fatal` tests `"** Fatal **"` against
>   EnergyPlus's real `"**  Fatal  **"`, so it reads `False` on all 8,160 rows.)

**Judgement: confident duplicate.** Same root cause (the string-match bug in the harvest scripts), same
observable (`has_fatal` reads `False` fleet-wide), same fix would close both. The register's own OPEN-05
entry already names this pair and my independent sweep reproduces it verbatim — **the method is
validated.**

### 4.2 Possible — E-LA-06's warmup residual and the E-LA-14/16/18/19/23 lineage

> - **E-LA-06** (`DONE-implementation_plan.md:616`, 2026-07-23): *"`scale_baseline_idf()` does not scale
>   fixed-capacity auxiliary equipment; large real warning/severe-error counts at non-identity scale
>   factors"* — status field literally reads *"~~OPEN-BLOCKED-PARTIAL~~ → RESIDUAL RE-ATTRIBUTED
>   2026-07-26 (warmup part → E-LA-14/23 lineage; flow-balance part never revisited)"*.
> - **E-LA-23** (`DONE-PLAN_e-la-20_multilayer-fix.md:1308`): *"thermal_mass=True perturbing
>   CheckWarmupConvergence is already logged four times in the structural-fixes plan: E-LA-14
>   (SecondarySchool), E-LA-16 (Hospital/TallBuilding), E-LA-18 (LargeOffice), E-LA-19
>   (zone-composition shift)."*

**Judgement: possible, but already self-corrected by the project, not a fresh finding here.** The
project's own record explicitly re-attributes E-LA-06's warmup-symptom half into the same lineage as
E-LA-14/16/18/19/23 — i.e., this "duplicate" was already caught and folded by the manager at the
2026-07-26 audit cited in E-LA-23's own entry. It is included here because the task asks for the full
sweep, but it should not be read as a new discovery: the re-attribution note is on record at the ID's
own defining line.

### 4.3 Possible — E-LA-33 and E-LA-34 ("same origin", different manifestation)

> - **E-LA-33** (`...DONE_PLAN_storey-matching_implementation.md:3353`): *"storey matching is invisible
>   in geometry, and inert for 82–98% of both viewer cells"*
> - **E-LA-34** (`...DONE_PLAN_storey-matching_implementation.md:3394`): *"the layout_assign viewer
>   payload is data-poor and mapless; the grey render is faithful"* — header states explicitly *"same
>   origin as E-LA-33"*.

**Judgement: rejected on inspection.** The document itself calls out the shared origin, but the two
defects have different objects (E-LA-33 is about storey-matching not being visually distinguishable in
rendered geometry; E-LA-34 is about the viewer's data payload lacking EUI/mappable fields) and different
fixes: E-LA-34 was remediated ("viewers made viewable") and then frozen by user instruction, while
E-LA-33 remained open and was still one of two grounds a later go/no-go was withheld on. Same root
cause in the loose sense of "the viewer pipeline is incomplete," but not the same defect by the task's
strict test (one fix did not close both).

### 4.4 Possible — E-LA-38 and E-LA-40 (population overlap, unconfirmed shared cause)

> - **E-LA-38** (`...PLAN_storey-matching_REMAINder.md:1436`): *"`05_results.gpkg` mislabels 100% of
>   the fleet's true Hotel archetypes as Office archetypes"* (41/8,160)
> - **E-LA-40** (`...PLAN_storey-matching_REMAINder.md:1602`): *"three buildings regress from success
>   (T19) to failed (T20)"* — text states *"All three sit inside the 7-building E-LA-38 mislabelled-
>   SmallHotel population... R09's hypothesis (multiplier scaling newly tipping the same warmup
>   divergence) is plausible and unverified — recorded as a hypothesis, not a finding."*

**Judgement: rejected on inspection (for now).** E-LA-40's population is a strict subset of E-LA-38's,
but the document is explicit that the causal link is an unconfirmed hypothesis, not a proven shared
mechanism. The register's own OPEN-07 entry agrees: "likely closes as a side effect... confirm rather
than assume." Not a duplicate until that confirmation exists — it is a related, overlapping-population
pair, which the task's instructions say is explicitly not sufficient for "duplicate."

### 4.5 Rejected — root-cause/symptom pairs that are already properly cross-referenced

- **E-LA-09 / E-LA-13**: E-LA-09 (`Outpatient` 100% Fatal, symptom) explicitly names E-LA-13 (eppy
  zip-truncation bug) as its root cause in E-LA-09's own status field. This is a documented causal
  chain with two intentionally distinct IDs (symptom vs. mechanism), not a hidden duplicate.
- **E-LA-07 / E-LA-08 / E-LA-17**: E-LA-08 explicitly extends E-LA-07's population; E-LA-17 explicitly
  states "E-LA-07-class-2/E-LA-08 NOT fully closed." All three are transparently cross-referenced
  continuations, not independent duplicate discoveries.
- **E-LA-29 / E-LA-30**: E-LA-29's own status field reads "superseded by E-LA-30" — an acknowledged
  supersession, not two IDs quietly describing the same thing.

No E-UTCI duplicate candidates were found. The closest surface-level similarity is E-UTCI-11 and
E-UTCI-12 (both "half-landed ship" patterns — spec tests committed ahead of implementation), but they
are different subsystems (fusion tier vs. draw tier) with different fixes, and E-UTCI-12's own entry
says "same **shape** as E-UTCI-11," explicitly flagging a repo-pattern similarity rather than claiming
they are the same defect. Rejected.

---

## 5. ID reuse (same number, two different meanings)

**None found.** Check run: for every ID above, all occurrences across the repo (§1 step 2 raw dump,
1,210 + 450 lines) were scanned for a second, unrelated description attached to the same number. Every
occurrence of a given ID across every file describes the same underlying defect as that ID's original
site — including numbers that carry two *items* under one entry (E-LA-31's "item 1" control-copy
diagnosis and "item 2" cross-building-placement defect are explicitly one entry with two dated
sub-findings, not two unrelated defects sharing a number).

The project's own ID-assignment discipline is visible in the text itself: `PLAN_storey-matching_
REMAINder.md:1445` — *"(Next free ID is E-LA-40. E-LA-37 was already taken by the `ZoneGroup`
list-multiplier option.)"* — showing IDs are tracked and incremented deliberately, which is consistent
with finding zero reuse.

---

## 6. Next free ID per prefix

Recomputed directly from §2's inventory (highest real ID + 1, ignoring the E-LA-42 placeholder text
which is itself already exactly this computation done by a prior session):

- **Next free `E-LA-` ID: E-LA-42** (highest logged: E-LA-41).
- **Next free `E-UTCI-` ID: E-UTCI-17** (highest logged: E-UTCI-16). No document in the tree currently
  states this UTCI number explicitly; it is derived here from the §2.2 inventory.
