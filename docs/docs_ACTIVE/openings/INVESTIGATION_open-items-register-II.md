# INVESTIGATION — Register of everything open in OpenUBEM, book II

> **Slug:** `open-items-register-II` · **Opened:** 2026-08-20 · **Author:** manager session
> **Status:** INVESTIGATION document — a **register and a diagnosis**, not a plan. Nothing here is
> scheduled, scoped, costed or approved.
> **Predecessor:** `INVESTIGATION_open-items-register.md`, opened 2026-08-04, **🔒 CLOSED 2026-08-20**
> at 8,205 lines. It stays at its own path and is **not** archived, because 79 documents cite into it.
> It remains the authority on every closed item and on every item's full history.
> **This is the live register. Open work is tracked here and nowhere else.**

---

## 0. Why this book exists, and the two rules that carry over

The predecessor ran to **8,205 lines and 61 items, 40 of them struck**. Every executor dispatch and
every director resume began by reading it, and what a reader needs is the ~20 items that are open,
not the 40 that are shut. It was closed on the project's standing convention — *close a doc past
roughly a thousand lines, open a successor, cite the old one by ID and never restate it.*

**What carried over verbatim:** the 21 live rows in §2 below, copied from the predecessor's §1 table
without a word changed. **What did not:** the 40 struck rows, the amendment log of 2026-08-04 →
2026-08-20, and the per-item history sections. Those are in the predecessor and are cited by ID.

Two rules survive the rotation and are not negotiable:

1. **Correct in place, never delete.** A falsified sentence is struck through and corrected beside
   itself, so a later reader sees what was believed and why it was wrong. That is how the predecessor
   was written and how this book is written.
2. **A closure must name what survives it.** No item closes on "it looks fine now" — it closes on a
   measurement, and the closing note states what remains true after the item is gone.

**Where the numbers come from:** the count is recomputed from the table body by
`scripts/analysis/open_register_recount_2026-08-18.py`, never by hand. That script reads the
**predecessor's** path and its whole-sequence check (`OPEN-01 … OPEN-NN, no gaps`) only makes sense
against a table that still holds the struck rows. Against **this** book the check is the one in §1:
*live IDs + retired IDs = the full sequence.*

---

## 1. State at open — 2026-08-20

| | |
|---|---|
| **Live items** | **16** — 🔵 **was 19 at open; OPEN-27 closed 2026-08-20; OPEN-15 and OPEN-16 retired into OPEN-17 on 2026-08-20 (user ruling R2)** |
| **Retired / struck** | **46** |
| **Total ever opened** | **62** — `OPEN-01 … OPEN-62`, no gaps, no duplicates |
| **Next free item ID** | **`OPEN-63`** |
| **Next free defect ID** | `E-LA-42` · `E-UTCI-17` |
| **Adopted fleet figure** | **153.8231 kWh/m²** pooled over 8,153 buildings — ⚠️ **not volume-correct**, OPEN-56's ≈+1.0 is not in it, and 🔴 **low by OPEN-61 — the carried "~1 % on four buildings" is superseded 2026-08-20 by an estimated 6–13 % fleet-wide (§6), which is a size, not a correction** |
| **Rulings owed by the user** | **none.** ✅ `OPEN-62` was opened on the user's grant 2026-08-20, and the director's recommendation against a second ID for the storey-coverage finding stands (it lives in OPEN-03). ✅ **Four more rulings were asked and answered the same afternoon** — R1 fix OPEN-62's parser and restate control C9; R2 merge OPEN-15/16 into OPEN-17; **R3 retire none of OPEN-09/10/14/18/19/38 — the director recommended retiring 18 and 19 and the user declined, recorded as declined rather than left un-asked**; R4 the user applies OPEN-27's two edits and the director verifies. Full text: `implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §4. ✅ **R4 was superseded the same afternoon**: the user granted a narrow one-time exception to the never-edit-`docs_main/` rule for OPEN-27's two lines only, the director applied them, and **OPEN-27 is closed**. The exception was scoped to those two lines and does not generalise. |
| **Plans in force** | 🟢 **TWO, deliberately and for the first time in this arc.** (1) **`implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md`** — authorised 2026-08-20, **Arc B (T05) COMPLETE and CP-4 signed**; Arc A: **CP-1 and CP-2 signed**, **T03 — the full 8,153-building census — running locally at 12 workers**, T04 + CP-3 to follow. (2) **`implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`** — authorised 2026-08-20 (afternoon) on the user's four rulings, **T01 in flight**. ⚠️ **The second exists precisely because every task in it is CPU-cheap and needs no EnergyPlus**, so it runs *beside* the saturated census rather than behind it. **Neither is archived until both close** — the "only one plan in `implemenation/`" rule is about archiving completed plans, not about forbidding two live ones. The six completed plans were archived to `implemenation/previous/` on 2026-08-20 and all **80** citations into them were swept and repaired the same pass (0 broken, all 35 cited targets verified to resolve). |
| **Running on the cluster** | **nothing** |

**Live IDs (16):** `03, 09, 10, 14, 17, 18, 19, 35, 38, 53, 56, 58, 59, 60, 61, 62`

⚠️ **Two corrections are folded into that line, and both are stated rather than smoothed over.**
(1) It read **`(18)`** and omitted **OPEN-62**, which had been opened the same day and given a §2 row
and a §6 section — the same one-row-short failure this book's own rotation note (below) describes,
repeated within hours of being written about. (2) **`15` and `16` left the list on 2026-08-20**,
retired into OPEN-17 on the user's ruling R2, not closed and not solved. (3) **`27` left the list later the same afternoon** — genuinely closed, not retired: the two spec lines were corrected at source and verified to 0 remaining occurrences. **16 live + 46 retired = 62.**

⚠️ **`12` and `13` left this list on 2026-08-20** — closed by the director on T04 and T05 of
`PLAN_five-items-2026-08-20-late.md`. Their closing notes are in §6. **`20` left it the same day**,
retired rather than closed: it was a scope question, not a defect, and it now lives only in
`docs/docs_TODO/wider_validation_matrix.md`.

**Retired IDs (46):** `01, 02, 04, 05, 06, 07, 08, 11, 12, 13, 15, 16, 20, 21, 22, 23, 24, 25, 26,
27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 54,
55, 57`

16 + 46 = 62 = the full sequence. ⚠️ **The long-running reconciliation carries over:** the predecessor
counts **40 struck rows against 38 retired IDs**, and the difference of exactly 2 is **OPEN-02** and
**OPEN-28** — folded under OPEN-01 and never independently tracked as opened IDs. Above they are
listed with the retired, which is why that list read 40 and not 38 at open (**45** and not 42 now
that OPEN-12, OPEN-13, OPEN-15, OPEN-16 and OPEN-20 have joined them). **This is not a miscount and it
does not need re-deriving again.**

⚠️ **One correction was made at the moment of rotation.** **OPEN-61 was opened 2026-08-20 and given
its §-section and its amendment note, but never a §1 table row** — so the predecessor's own recount
script reported **20 live / next free `OPEN-61`** while its prose and the director prompt both said
**21 live / next free `OPEN-62`**. The row was written and inserted into the predecessor's table
before it was closed; the script now agrees with the prose at **21 live / 40 struck / 61 total**.
**The prose was right and the table was one row short.**

---

**Board:** `reporting/board_open-items.html` — the **17** items as a one-screen board, published at
<https://claude.ai/code/artifact/7960a833-541b-4eab-a006-403c53c4bddc>. **Update it in place** (same
file path, same URL) whenever this table changes; do not publish a second one.

---

## 2. The live items — **16** as of 2026-08-20 (this section was written at 19)

🔴 **Four rows below are AMENDED by §6 as of 2026-08-20 — read §6 before quoting them:**
**OPEN-61** (mechanism confirmed, size raised by an order of magnitude) and **OPEN-03** (its stated
mechanism is retracted) stay live. 🔒 **OPEN-12 and OPEN-13 were CLOSED by the director on
2026-08-20** and their rows are struck below. The rows themselves are left as written so the
amendment is visible as a change — nothing here is deleted.

Rows copied verbatim from the predecessor's §1 table. Where a row cites a `PLAN_*.md`, a
`MEASUREMENT_*.md` or a line of source, that citation is the predecessor's and is unchanged.

| ID | Item | Theme | Blast radius | Evidence |
|---|---|---|---|---|
| OPEN-03 | ~~`layout_assign` models all internal loads as 2022-code regardless of real vintage~~ 🔴 **REFRAMED AND THE CENTRAL CLAIM REFUTED 2026-08-20 (director, CP-2 of `implemenation/previous/PLAN_vintage-elasticity-2026-08-19.md`).** The gap is a load-**source** disagreement, not a load-**vintage** one: `auto` reads one fixed pair per archetype from `doe_prototype_loads.json` (no vintage key), `layout_assign` uses the DOE prototype baseline IDF's own densities for any archetype with a mapped `STD2022` baseline. **Both modes are equally vintage-blind.** | Reported numbers | ~~~half of a −29% cross-mode gap~~ **≈8% of the pooled −23.91% gap; 0.0% in the subset where loads are held identical** ➕ **2026-08-20 (T05): the re-framed storey question is now counted on all 8,160 — `layout_assign` represents the real storey count for only 30.0 %; for 70.0 % it builds the prototype's storeys regardless (real mean 3.12, max 105 → built mean 1.21, max 6).** | ✅ **measured — claim refuted; storey gap now sized fleet-wide, still open** |
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | ✅ **C06: "cosmetic" tested and holds — 96.3% distribution overlap, small correctly-signed residual** (audited) 🔵 **2026-08-18 (overnight, X03): NOT downstream of OPEN-56.** The ten non-convergent-but-successful buildings show 150 warnings baseline and 150 treated, 15/15 unchanged on every one, while the same treatment clears the volume warning 70/70 → 0/70. **Two independent defects overlapping on the same 16 buildings.** X07: E-LA-17 resolves to exactly this population and would double-count if adopted. |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) — **capability confirmed real from the schema; remedy narrower than claimed** | Capability | ~~90 buildings (**carried, not re-derivable without a fleet pass**)~~ **C03: 90 reproduces exactly — but that is 4.6% of the 1,976 inexpressible fleet-wide** + future | ✅ **measured + verified** ✅ **2026-08-18 (overnight, X08): the "90 buildings" RE-DERIVED EXACTLY — 66 `MidriseApartment` + 24 `HighriseApartment` — by running the experiment N11 named and declined. And a denominator at last: 90 of 1,992 `fallback_not_expressible` = 4.5 %; the other 1,902 (95.5 %) are structurally beyond the edit. `applied` is only 497 of 7,442.** 🔵 **CEILING RESTATED on run-4 data 2026-08-19 at CP-3 (T16): 4.78 % (was ~~4.5 %~~), 96 of 2,007.** The evaluated population reproduced exactly (7,442) but the 90-building `MidriseApartment`/`HighriseApartment` split did **NOT** — **69/27 against the carried 66/24, self-reported as a finding rather than smoothed over**, and explained: run 4 carries OPEN-35's storey corrections, which this item's own X08 finding already placed upstream of exactly that classification boundary. All other archetype counts unchanged. Capability and narrowness both reconfirmed. |
| ~~OPEN-12~~ | ~~Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2%~~ **both re-derive at 100%; a third cell is at 100% and was never named**. **N15: genuinely a source-coverage gap — NOT a spillover from OPEN-14** | Data acquisition | **3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide** | ⚠️ **numbers do not reproduce**  🔒 **CLOSED 2026-08-20** — closes on measurement, not on repair: the third cell is `nyc_suburban`, the fleet counts are confirmed exactly, and the two irreproducible percentages are replaced. **What survives it:** the 2,806-of-8,160 source-coverage gap itself, which is OPEN-14's and OPEN-15's business, not a defect of this item. |
| ~~OPEN-13~~ | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc — ~~both live at HEAD~~ **E-UTCI-13 fixed 2026-08-12; E-UTCI-12 contained only** | Data / Stage 6 | ~~the whole test suite cannot be collected~~ **collectable again (1937 tests, exit 0) — but 43 passing tests traded away**; cached re-read no longer nulls `levels`/`use_class` | 🟡 **1 of 2 fixed**  🔒 **CLOSED 2026-08-20** — closes on refutation: nothing was ever deleted and all 43 tests run at HEAD (`43 passed, 10 skipped in 0.65s`). **What survives it:** the 10 tests that stay skipped, reassigned to **OPEN-17**, and the restated suite baseline **1,918 passed / 56 skipped**. |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout — **confirmed; no Overture slice is tracked for any affected cell** | Reproducibility | Stage 6 inputs; ~~converges with OPEN-12 on the same 4 cells~~ **N15: coincidence — separate item** | ✅ **measured** ✅ **2026-08-18 (overnight, X09): the step this item named as "the next thing" is TAKEN. Zero `FUSED` provenance tokens across all 8,160 buildings — including `nyc_centre`, the one cell that HAS a tracked slice. The missing slices are a real but NON-OPERATIVE blocker; the config gate closes first. The OPEN-12 convergence is a coincidence.** |
| ~~OPEN-15~~ | ~~Imputation Phase E — documented-deferred, never executed — **no code path exists at all**~~ 🔒 **RETIRED 2026-08-20 into OPEN-17 on the user's ruling R2** (`implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §4). Not closed and not solved — **the fact is unchanged and is now carried by OPEN-17's row.** | Imputation | fleet inputs | ✅ **measured** — merged, not dropped |
| ~~OPEN-16~~ | ~~`ml` imputation tier built but permanently off — **never reachable from the production pipeline, only from the validation entry point**~~ 🔒 **RETIRED 2026-08-20 into OPEN-17 on the user's ruling R2** (same plan, §4). Not closed and not solved — **the fact is unchanged and is now carried by OPEN-17's row.** | Imputation | opt-in only | ✅ **measured** — merged, not dropped |
| OPEN-17 | 🔵 **CARRIER as of 2026-08-20 — this row now holds all three imputation facts, on the user's ruling R2.** They were one fact described three times: **the imputation tiers were built and never wired to the production router.** (a) *ex-OPEN-15* — Phase-E imputation is documented-deferred and **no code path exists at all**. (b) *ex-OPEN-16* — the `ml` tier is built but **reachable only from the validation entry point**, never from the production pipeline. (c) *its own* — 6 variance-preserving draw-tier imputers built, ~~off, awaiting a promotion decision~~ — 🔴 **not "off": the tier is unreachable; its router hook has never existed in any commit.** ⚠️ **Merging is a bookkeeping act, not progress** — nothing was measured, fixed or decided by it; the three facts and their evidence stand exactly as they did. | Imputation | ~~opt-in only~~ **the decision's cost was understated**; now the whole unwired-router surface in one row | ✅ **measured** (all three) ➕ **2026-08-20: inherits OPEN-13’s 10 residual skips** in `tests/test_draw_methods.py` (`TestDrawTierRouting` 6, `TestNoEUILeakage` 1, `TestDrawTierDeterminism` 1, 2 of 6 in `TestDefaultByteIdentity`) — they unskip themselves the day the router hook exists. |
| OPEN-18 | **Q3 — √S vertical-form distortion**, now confirmed unreachable by the mechanism built for it | Method | small buildings, cold cells | ✅ |
| OPEN-19 | LA runs ~+40% hot — Title 24 vs ASHRAE 90.1 — **not currently representable: no climate-zone or code-year switch exists; LA's HVAC comes from a Buffalo prototype** | Method | one whole city | ✅ **measured** |
| ~~OPEN-20~~ | Wider validation matrix beyond 3 cities × 4 rings | Method | external validity | 📄  🔒 **RETIRED 2026-08-20** — a scope question, not a defect: nothing broken, nothing blocked, nothing to measure, and tracked twice since 2026-06-17. Lives on in `docs/docs_TODO/wider_validation_matrix.md`. **ID retired, never to be reused.** |
| ~~OPEN-27~~ | ~~A DESIGN doc names an archetype that does not exist — **inside the coarse-metric definition**~~ 🔒 **CLOSED 2026-08-20.** Both lines now read `HighriseApartment`: `DESIGN_step-2…:529` and `PLAN_step-2.5-oq7-labelled-fixture.md:78`. Verified `grep -rn "MultifamilyHome" docs/docs_main/` → **0 occurrences**, and the archetype set re-derived from `openubem/data/openstudio_archetypes.json` → **exactly 2 Residential archetypes, `MidriseApartment` and `HighriseApartment`**, so the replacement was checked against the data rather than assumed. `pytest -k "multifamily or coarse"` **6 passed**. | Housekeeping → **spec integrity** | the accuracy metric's own definition | 🔒 **closed** |
| OPEN-35 | **Two fallbacks invent the missing storey count and disagree** — archetype chosen at group-median storeys, geometry built at 1. **2026-08-11: the mechanism is now proved by direct `.eio` evidence, not inferred.** The 2,611-building subpopulation matches its own broken `levels = 1.0` denominator almost exactly in `auto`/`building`/`floor` (**100% within ±1%, by construction** — those modes build zones from `levels`) and **breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)**, which assigns storeys from the archetype instead. **The two paths disagree, measured, on 40,800 runs.** **Still open** — the intended-fallback question is a DESIGN decision, not a measurement. ✅ **2026-08-19 (T04–T05): scope corrected 11 → **21** and the agreement fix landed.** The census was apartment-scoped; 10 `LargeHotel` buildings consume imputed levels through the identical mechanism, and the 11 are a **strict subset** of the 21 (set containment, not count). Naive 509-building variant **rejected**. Fix in `derive_num_floors()`, gated on the `GROUPMEDIAN_LEVELS_MED` token. 🔴 T04 landed it **inert** — no call site passed the new arguments — and said so; **T05 wired 2 of 3 and stopped at the parser with a quoted obstacle; T06 closed it — leaving 2-of-3 would have made the build and parse paths derive DIFFERENT floor counts for the same 21, recreating this very defect elsewhere.** ✅ All three paths now change the **identical 21 osm_ids** (0 missing / 0 extra, set membership, fleet-wide over 8,160 buildings), with a test pinning the three-way agreement. ⚠️ Baseline predates the fix and is stale w.r.t. 21 buildings; **no fleet re-run, no restatement.**| Simulation correctness | **2,611 / 8,160 = 32.00% of the fleet**; 1,031 of them given a mid/high-rise archetype and built at one storey | ✅ **mechanism verified + size measured + simulation-boundary proof 2026-08-11** 🔴 **2026-08-18 (overnight, X04): consequence measured for the first time, and the headline it produces MUST NOT be quoted. 2,611 / 32.00 % and 1,031 both re-derive exactly; the +47.9 % fleet EUI gap is composition (nyc_suburban is 1,589 of 2,611 with no comparison group) and WITHIN cells the direction is not even consistent — 4 lower, 4 higher. Needs an intervention, not a cross-section. 0 failures in 2,611.** |
| OPEN-38 | ~~**`layout_assign` subsurface geometry defect** — 7 tasks die on EnergyPlus **severe** *"Base surface does not surround subsurface"*, escalating to a two-space fatal~~ 🔴 **PREMISE FALSIFIED 2026-08-11 — item rewritten, still open.** That message is a **`** Warning **`**, not a Severe, at all **8** sites, and **kills nothing**. The item is now two measured defects: **(i)** all 7 `layout_assign` fatals die on **thermal runaway in zone `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / +182,399 °C) — the substituted prototype's laundry room, same zone token as OPEN-06, and **no other cause appears in that mode**; **(ii)** **8** buildings carry malformed door geometry, of which `nyc_rural/way_965718401` **completes successfully and publishes results** from it. All 8 are `layout_assign`; **zero in the other four modes**, verified across all 40,800 `.err` files. 🔴 **2026-08-18 (T04): population re-derived at 7, confirmed; tested against OPEN-42 and found to be a different mechanism on every measured axis (message class, zone position by `.eio` geometry — bottommost storey vs. OPEN-42's topmost, geometry origin — substituted `SmallHotel` prototype, mode — `layout_assign`-only). Recommend keeping the two items separate; director to rule.** ✅ **Ruling 2026-08-18: recommendation ACCEPTED — the two items stay separate.** | Simulation correctness | (i) 7 fatals, one prototype zone; (ii) 8 buildings, 1 of them publishing | ✅ **both mechanisms measured; the register's stated cause was wrong**; ✅ **2026-08-18: tested against OPEN-42, confirmed distinct; director ruled — stay separate** 🟢 **MECHANISM FOUND 2026-08-19 at CP-3 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md` (T14) for defect (i), and it is a LOADS/no-HVAC interaction — not geometry, and not a wrong template.** `LaundryRoomFlr1` has **zero HVAC** in the DOE `SmallHotel` prototype — absent from all 54 `ZoneHVAC:EquipmentConnections` entries — while carrying the floor's largest absolute internal-gain density (**46,286.64 W** gas dryer plus water-heater ambient losses). An unconditioned zone with nothing to cap that load free-floats into a `CalcHeatBalanceInsideSurf` divergence during Sizing. ⚠️ **Geometry is explicitly CLEARED and this is NOT an OPEN-56 stub**: that zone's `.eio` volume is **378.63 m³**, positive and plausible. Disjoint-mode claim reproduced exactly across all 40,800 `.err` files: **0** hits in `auto`/`building`/`floor`/`fast_zone`, **8** in `layout_assign`. No remedy authorised. |
| **OPEN-53** | 🔴 **874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells.** Opened 2026-08-18, found as a byproduct of T03's `.eio` census run for OPEN-37. Against **40,800** `n_building_dirs` and **40,800** `.eio`/`.err` (both exact, zero empty), `.sql` = **39,926** and `.end` = **39,925** — short by 874/875. Every short directory still carries its `.eio` and `.err`, so this is **not** OPEN-37's problem — ~~it is an incomplete-simulation signature~~ **it is a batch-scoped harvest gap, not an incomplete-simulation signature (T02, 2026-08-18): 874/875 report `EnergyPlus Completed Successfully`, 0 fatal, indistinguishable from a 200-directory healthy control (100% completed).** **874 of 875 concentrate in `austin_suburban_fast_zone`/`austin_suburban_floor` (100% of both, all other modes for the same buildings fully populated); the remaining one is `nyc_centre_fast_zone`, truncated mid-input-processing.** ~~No `.err` content from these specific directories has been read yet.~~ | Reported numbers → **run completeness** | up to 875 E02 harvest directories, two Austin sub-cells + one NYC directory | ✅ **census counted, location established**; ✅ **T02 2026-08-18: `.err` read for all 875 + 200-directory control — genuine EnergyPlus failure retired (0 fatal); harvest-artifact vs IDF-output-config not distinguishable from this artifact; 1 exception (`nyc_centre_fast_zone`) not determinable from `.err`**; ✅ **Ruling 2026-08-18 (CP-1): original question ANSWERED — files were produced, harvested and inventoried 2026-08-11, then deleted by a process outside this repo at 2026-08-17 16:21, which also emptied the whole E02 IDF corpus; no published number affected. STAYS OPEN, narrowed to the custody risk — nothing prevents recurrence, and `e02_corpus_inventory.csv` (2026-08-11) is now falsified by disk for two rows and must be read as a snapshot, not current state.** ⚠️ **2026-08-18 (overnight, X06): custody exposure quantified — 152.4 GB across three corpora, 145 GB of it `.sql`, none yet carrying the 2026-08-17 16:21 sweep signature. Under 0.12 GB preserves every finding this arc cites; the 76 GB of `.sql` is the bait and is re-derivable. And "E02 is gone" is too strong — its parquet manifests survived.** |
| **OPEN-56** | 🔴 **Every building in the fleet simulates with its zone air volume replaced by a 10 m³ stub.** EnergyPlus computes a **negative** volume from the geometry we hand it (`Indicated Zone Volume <= 0.0`, floors and ceilings wound the wrong way) and substitutes 10 m³. Opened 2026-08-18 (late) while looking for OPEN-42's mechanism. **8 160 / 8 160 = 100.00 %** of run 2, re-confirmed in run 3; **control: 0 / 2 on DOE-prototype geometry**, so it is our geometry, not EnergyPlus. OPEN-42's six failures are its extreme tail — failures average **−6 096 m³** computed volume against **−683 m³** for successes. ⚠️ **No claim is made that the published 157.1 is wrong**: infiltration is written `Flow/ExteriorWallArea`, not air-changes-per-hour, so it is not scaled by the stub, and the effect on annual EUI is **unmeasured**. | Simulation correctness | **all 8,160 buildings** | 🔵 **mechanism measured;** ~~writer not yet localised~~ ✅ **WRITER LOCALISED — tag corrected 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`** (this tag was already stale against this item's own §-section, and a task written from it found its premise false; see §1's CP-1 amendment). The winding is written by `geomeppy==0.12.2` and **its own corrector `set_entry_direction` is a provable NO-OP for our GGR convention** — `is_clockwise` is self-referential, testing against a point built from the same normal, so it returns `False` unconditionally and never inverts either winding. **Verified twice by the director independently of the executor**, by inspection and by execution on a CW- and a CCW-wound square. The IDF winding is therefore the **input footprint's own orientation**, and the one `orient()` call that exists (`openubem/idf/builder.py:464-465`) is gated `if resolution_mode != "auto"`, so it **never fires for the adopted baseline mode**; 0/20 sampled source footprints are CCW, matching the 100 % rate. **A THIRD remedy shape now exists: extend `orient()` to `auto` (sign unverified), alongside writing `Zone.Volume`. Neither applied — the remedy ruling is still owed to the user.** 8,160/8,160 (100.00 %) re-confirmed on run 4. ✅ **2026-08-18 (overnight, X01/X02): THE FLEET-SCALE COST IS MEASURED — 69 buildings, all twelve cells, control whole (70/70 baseline volume warning → 0/70 treated, 70/70 completed both arms). Mean +0.98 %, median +0.84 %, 65/69 same direction. The per-zone model is REFUTED (corr 0.113); it is a fixed per-BUILDING offset of ≈ +1.0 kWh/m². 157.1 deliberately NOT restated. ~~New lead: on 1 of 60 the treatment also moved the reported floor AREA by 4.18×.~~ 🔴 **RETRACTED 2026-08-19 (CP-1, T05): a FALSE LEAD.** Untouched production run-4 data gives `relation_3566904` `footprint_area_m2 = 2,682.23`, `levels = 14`, `floor_area_m2 = 37,551.22` — ratio **1.000001**, no anomaly at all. The 157,115 m² belongs to a different building, `relation/11171793`, and reached this experiment through **OPEN-58's `run_ep()` shared-cwd cross-contamination** — an independent second confirmation of OPEN-58's verdict from data that never touched the defective helper. Remedy still unauthorised.** |
| **OPEN-58** | 🔴 **`open56_zone_volume_experiment.py`'s `run_ep()` helper has two defects, and any earlier local batch result that imported it is exposed to both.** Opened 2026-08-19 by the director; found by **T04's own controls**, not by a task that went looking. (a) EnergyPlus `-x` lets outputs **cross-contaminate between buildings that share a working directory** — caught as two byte-identical `.sql` files for two different footprints. (b) It reads EUI by a formula that **does not match production's `total_eui_kwh_m2`** (`openubem/results/parser.py`), which sums per-end-use EUIs over a multiplier-aware `.eio` area rather than dividing Total Site Energy by Total Building Area. ✅ **T04 voided its own first full run and re-ran clean rather than patching the numbers** — its published `_results_v2.csv` is unaffected. ⚠️ **Explicitly NOT scoped to OPEN-35**, whose amendment records it: the question is which *other* results imported this helper. ~~**No audit of the blast radius has been done.**~~ **— stale tag, struck 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`; the audit is recorded later in this very row and in this item's §-section, and a task written from this sentence found its premise false at HEAD.** ✅ **Re-derived independently at CP-1 by a disk walk** (correctly chosen: the origin file and its real importers are **untracked**, and a tracked-files-only `git grep` was tested first and found only 5 of the 8 files) — **exactly reproduces the existing count: 3 real importers, 4 name-collisions, 1 origin, 8 total.** ✅ **BLAST RADIUS MEASURED 2026-08-19 (T06–T08): 3 real importers, 6 descended artifacts, 1 unsound row, 0 unverifiable.** 🔴 **This item's own stated mechanism was wrong:** defect (a) is **not** a shared `-d` outdir — every importer already passes a unique one — it is EnergyPlus's `-x` step working relative to the **shared process cwd**, so all three importers are exposed and **concurrency is not the discriminator**. One confirmed contamination in 166 recomputed cells (`nyc_centre/relation_3566904` carrying `relation_11171793`'s results — identical to **fifteen significant figures**); already excluded from the pooled statistic, but for a **wrong stated reason**. ✅ **Zero cited figures corrupted** — defect (b) shifts absolute EUI up to −24 % but every cited number is a **relative** change on the same building, which cancels. Still open; **no remedy authorised**.| Simulation correctness → reported numbers | unknown — every local batch result that imported `run_ep()` | 🔵 **both defects reproduced and understood; blast radius unmeasured.** No remedy authorised. |
| **OPEN-59** | 🔵 **REFRAMED 2026-08-19 (late, director) — this is a CALIBRATION item, not a bounds defect. Hypothesis 1 is REFUTED by direct measurement:** T02 of `implemenation/previous/PLAN_gap-decomposition-2026-08-19.md` screened **all four** drawn PDE columns for **all 290** `OpenUBEMUnknown` buildings against their donor bounds — **0 of 4 columns, 0 of 290 buildings, out of bounds**, worst excursion **0.0** on every column (`openubem/outputs/comparisons/open59_pde_bounds_screen.csv`). **This is NOT OPEN-55's sibling** — the draws are all legal, so no column-wise screen can fix it. **Hypothesis 2 stands by elimination:** the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, which makes the remedy a **different donor pool or better classification**, not a bounds fix. **Kept open under its own ID rather than closed** — the phenomenon is real and unexplained; only its diagnosis changed. ~~🔴 **With the Unknown equipment defect cured, Unknown buildings still use ~~1.7×~~ more than classified buildings — the gap moved from equipment to hot water and heating.** ⚠️ **The `1.7×` is a MEDIAN-PER-BUILDING statistic measured on `nyc_suburban` alone, and this row must carry both weightings — corrected 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`, measured fleet-wide on run 4.** **Floor-area-POOLED: Unknown 107.22 vs classified 155.56 — Unknown is 31 % BELOW.** **MEDIAN-PER-BUILDING: Unknown 309.95 vs classified 134.08 — Unknown is 2.31× ABOVE.** 🔵 **Both are real and they disagree for a traced reason, not an error:** the top 10 of 650 Unknown buildings hold **72.5 %** of all Unknown floor area and run at moderate EUI (r = **−0.27** between Unknown floor area and EUI), so area-weighting is dominated by a few large moderate buildings while the *typical* Unknown building is small and hot. **Never quote one without naming its weighting.** Fleet-wide the largest end-use multiple is **DHW at 10.2×**, ahead of heating (3.4×); `nyc_suburban`'s lighting **6.7× does NOT generalise — it is 1.00× fleet-wide.** Fleet Unknown population: **650 buildings, 3.7 % of fleet floor area.** Opened 2026-08-19 by the **director's audit of OPEN-55's passing acceptance test**, not by a task that went looking for it — the test asked only whether divergences fell, and they did. 🟢 **The OPEN-55 screen is confirmed to have worked, and this item does not reopen it:** Unknown equipment demand is now *below* classified (median **37.5 vs 43.4 kWh/m²**). 🔴 **But total demand did not follow.** `nyc_suburban`, 290 Unknown vs 1,299 classified, medians: **total 349.4 vs 202.8 kWh/m² (+146.6, 1.72×)**, DHW **103.5 vs 42.5 (+61.0)**, heating **140.1 vs 99.0 (+41.1)**, lighting **26.7 vs 4.0 (+22.7)**, cooling **25.0 vs 4.5 (+20.5)**. The lighting and cooling ratios (6.7× and 5.6×) are the largest multiples and are the natural first place to look. ❓ **Cause not diagnosed and no remedy proposed** — it is not yet established whether the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, or whether the same widened-bounds pattern OPEN-55 found in the equipment column also affects the DHW, lighting and occupancy columns, which would make this OPEN-55's sibling rather than a new phenomenon.~~ | Reported numbers | **every `OpenUBEMUnknown` building in every cell** — 18.3 % of `nyc_suburban`; fleet-wide share and fleet EUI effect **not yet measured**, commissioned as part of T04 | 🔵 **measured on one cell; cause unknown; fleet effect unmeasured** |
| **OPEN-60** | 🔴 **`total_eui_kwh_m2` undercounts Interior Lighting and Interior Equipment whenever a zone carries a multiplier > 1 — every `layout_assign` EUI this project has ever recorded is too low.** Opened 2026-08-19 by the **director**, on a reconciliation control run by T01 of `implemenation/previous/PLAN_gap-decomposition-2026-08-19.md` — **not by a task that went looking for it.** **Mechanism, traced and not inferred:** those two end uses are summed from per-zone hourly variables, which EnergyPlus does **not** scale by the zone multiplier, while the floor-area divisor **is** multiplier-aware (`openubem/results/parser.py:431-433`, `resolve_simulated_floor_area()`). Every other end use — cooling, heating, fans, pumps, hot water — matches the multiplier-correct ABUPS table to **<0.01 %**. **Size, n=48 untrimmed `layout_assign` buildings:** only **6 of 48** reconcile within 2 %; error median **4.71 %**, mean 17.56 %, p90 24.19 %, **max 192.28 %**; **14 exceed 10 %**. 🟢 **No adopted number is affected, and this was verified rather than assumed:** zone multipliers are written in exactly one module (`openubem/geometry/layout_assigner.py`, `match_storeys()`, `:649`), which the `auto` production path never calls, and three run-4 `auto` fleet IDFs were read directly — **every `Multiplier` field is 1**. **153.8231 kWh/m² pooled over 8,153 buildings is untouched.** 🔴 **The gate that catches this already exists and the fleet pipeline never calls it** — `check_building_integrity()` (`parser.py:602-646`) returns `abups_ok=False` for the worst offender, and is called by `scripts/run_r1_t12.py:211`, `run_r3_fleet.py:313`, `run_r3_step5.py:204`, `run_t12_boston.py:198`, but **not** by the path that produced `05_results.csv`. ❓ **Remedy not proposed and not authorised** — two shapes exist (sum the two end uses from ABUPS as the other five already are, or make the per-zone sum multiplier-aware) and choosing between them is feature code, which this session does not write. | Reported numbers | **every `layout_assign` EUI ever recorded**, including OPEN-03's and OPEN-18's published sample figures, which were corrected 2026-08-19 the same night; **zero adopted rows** | 🔴 **mechanism traced, size measured on n=48, blast radius bounded to a non-production mode** |
| **OPEN-61** | 🔴 **`total_eui_kwh_m2` drops the District Heating component of Water Systems.** Opened 2026-08-20 by the **director**, on a reconciliation control run by T01 of `implemenation/previous/PLAN_four-board-items-2026-08-20.md` — the third pass in a row where the defect came from an executor auditing its own arithmetic and **no plan asked for that control.** **Mechanism, verified at the `.sql` and not inferred:** `METER_QUERY` (`openubem/results/parser.py:48-54`) enumerates meters by name and contains `WaterSystems:NaturalGas` and `WaterSystems:Electricity` and **no `DistrictHeating` meter of any kind**; `dhw_eui_kwh_m2` is built from exactly those two names (`parser.py:469`), so district-heated DHW energy is dropped before `total_eui_kwh_m2` is formed. Director control on `way_1008727470`: ABUPS District Heating **0.72 GJ** against **59.22 GJ** total end uses = **1.22 %** unreported; T01 measured **1.03–1.10 %** on four buildings by the same route. 🔴 **Not a one-line fix** — adding the name to `METER_QUERY` changes nothing, because the `.sql` carries no `DistrictHeating` Run Period meter at all; the value survives only in the ABUPS tabular table. Any remedy must either request the meter in the IDF (changing what every future run emits, leaving every existing `.sql` unfixable) or read ABUPS as a second differently-shaped source of truth inside the parser. **Both are design decisions and neither is taken.** ⚠️ **The fleet `.sql` corpus that would have sized this was deleted 2026-08-20** under W9's prune (see OPEN-53) — sizing it now needs a **re-simulation, not a re-read**, and that cost is recorded here rather than discovered later. Same class as **OPEN-60**: two independent omissions in one formula found four days apart, which is the argument for a reconciliation control **inside** `parse_building()`. | Reported numbers | **unmeasured.** ~1 % on the four buildings where it has been measured; `153.8231 kWh/m²` over 8,153 stands unchanged and is low by an unknown amount. OPEN-03's **−23.61 %** paired result is sound — the omission is common-mode in both arms | 🔴 **mechanism traced at the `.sql`, size measured on n=4, blast radius explicitly unmeasured** |

| OPEN-62 | 🔴 **Storey counts read from a baseline IDF omit each zone's own `Z_Origin` under Relative coordinates.** Opened 2026-08-20 **on the user's grant**, on the director's CP-4 recommendation; found by the T05 executor while building the fleet storey census and registered `[OPEN]` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 rather than silently fixed — the correct handling, since fixing it would have changed what control C9 had to reproduce. **Mechanism:** the wall-vertex method takes each zone's minimum wall Z and never adds the `ZONE` object's own `Z_Origin`, so any archetype that encodes a repeated floor band's elevation in `Z_Origin` while its wall vertices stay local (near Z=0) collapses to 1–3 storeys regardless of true floor count. **Measured zone-by-zone across all 18 baseline-mapped archetypes, not assumed:** severe in **MidriseApartment** (18/27 zones), **HighriseApartment** (18/27), **TallBuilding** (145/164), **SuperTallBuilding** (232/256), **Outpatient** (59/118), **SecondarySchool** (21/46) — **6 archetypes, 2,983 of 8,160 buildings (36.6 %)**; immaterial in `LargeOffice` and the two restaurant archetypes (the nonzero-`Z_Origin` zones are not floor-area-counting); absent in the remaining 10. ✅ **Director-checked: it does NOT drive OPEN-03's headline** — splitting the fleet on the flag gives 60.8 % disagreement on 5,177 clean rows against 59.2 % on 2,983 at-risk rows. What it does bound is the *per-archetype magnitude*, not the fleet-wide rate. 🟢 **Scope established the same day and it is narrow (director, at the source):** production code does **not** share the omission — `layout_assigner.py:471` + `:491-493` and `viz/geometry_extract.py:143-155` both add `Z_Origin` back before taking the minimum, and no third production reader exists. The gap is confined to **one analysis parser** (`open03_envelope_decomposition_2026-08-20.py::parse_idf`) and the single script that imports it. **This is a measurement-instrument erratum, not a geometry defect** — no building is built at the wrong height.  🔴 **SCOPE ENLARGED 2026-08-20 at CP-2 of `implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` — the `Z_Origin` fix is IN and CORRECT, and the item did NOT close, because the restated control C9b FAILED and the failure is the finding.** C9b checked the corrected parser against `layout_assigner.py`'s own origin-aware reader — a reader that never imported `parse_idf()`. **Agreement 12 of 18 archetypes; 6 disagree over 3,734 buildings** (`TallBuilding` 11 v 20, `SuperTallBuilding` 16 v 30, `Warehouse` 2 v 1, and 1 v 2 on `FullServiceRestaurant`/`QuickServiceRestaurant`/`SmallOffice`). **Mechanism traced by the director, not accepted as a bare disagreement** — on `TallBuilding.idf`: floor surfaces give **20** distinct elevations, all wall bases **20**, exterior wall bases **19**, and *exterior wall bases in floor-area-counting zones* — which is what `parse_idf()` actually counts — give **10**. The elevations found (`0.0, 4.9, 23.8, 55.3, 72.8, 88.6, 104.4, 118.4, 132.4, 135.9`) are the levels where a **new exterior wall starts**; a curtain wall spanning several floors contributes one elevation, not several. 🔴 **`storey_count` is therefore not a storey count** — it is the number of distinct exterior-wall base elevations in floor-area zones, equal to the storey count only when every floor starts its own facade. The `Z_Origin` fix was **necessary and not sufficient**: it removed one error from a quantity that was measuring the wrong thing. ⚠️ **The old C9 passed 96/96 and would have passed again after the fix**, closing this item today with the column recorded as correct while undercounting `TallBuilding` by 9 storeys of 20. **Ruling R1 — restate the control rather than keep it — is the only reason this was caught, and it was caught by the control failing.** ✅ **Still no production code implicated:** the reader that gives 20 IS `layout_assigner.py`'s. ✅ **OPEN-03's 30/70 headline is untouched** (it rests on `compute_band_map()`, already origin-aware). ~~🔴 **C13's restatement is a LOWER BOUND, not a value:** built mean 1.21 → **≥ 2.25**, built max 6 → **≥ 16**~~ — **WITHDRAWN BY ITS AUTHOR AT CP-3, 2026-08-20.** 🔴 **SCOPE ENLARGED A THIRD TIME at CP-3** (`implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §CP-3). T06 added a floor-surface reader on ruling R7 and its own allowed-to-fail control **C16 failed: 38 rows, all `Warehouse`, floor 1 < wall 2.** Mechanism measured by the director on the preserved prototype: exterior wall z-bases `{0.0: 8 walls, 4.267: 2 walls}` against **3 FLOOR surfaces all at z = 0.0** — a single-storey high-bay facade split into two vertical wall bands. **So `storey_count` under-counts `TallBuilding` (20→11) and `SuperTallBuilding` (30→16) and OVER-counts `Warehouse` (1→2): it is not a bound in either direction.** C13's 2.25 / 16 survive only because `floor < wall` occurs **0 times** inside the 5,714-row unmatched subset — an accident of archetype mix, not a property of the method. 🔴 **And the replacement reader is biased too: `storey_count_floor` counts an ATTIC as a storey.** Verified origin-corrected on the prototypes — `SmallOffice.idf` z = 3.05 carries **9 floor surfaces, all in zone `Attic`**; both restaurant archetypes carry zone `attic` at z = 3.049. All three are one-storey prototypes read as 2, and they are **3,580 buildings (43.9 % of the fleet)** and **2,797 of the 5,714 unmatched rows (48.9 %)**. Attic-corrected the built mean is **2.45**, not the 2.94 T06 reported. **The publishable statement is the range 2.45 – 2.94.** ⚠️ **C14's 18/18 agreement with `compute_band_map()`'s `n_proto` does not certify a storey count** — `n_proto` is documented in production as *“deliberately left as the measured Z-BAND COUNT, never a represented-storey count”* (`openubem/geometry/layout_assigner.py:404-406`). ✅ **Still not a production defect:** production branches `match_storeys()` on `n_proto` and never publishes it as storeys. 🔴 **Net finding, and the item's current scope: no reader in this codebase returns a storey count** — the naive reader collapses `Relative` files to 1, the wall-base reader is unbounded in both directions, the floor-surface reader counts attics. What a storey IS for a prototype with an attic, a plenum or a high bay is a **definition question that has never been answered in this project**, and it is not an executor's to answer. ⚠️ **Do not “fix” this by excluding zones named `Attic`** — zone-name matching is the generalisation A1 already falsified (F-07, `layout_assigner.py:389`) and would move archetypes across `match_storeys()`'s `n_proto` branches. | Measurement instruments only | **6 archetypes / 2,983 buildings (36.6 %) flagged**; separately, **3,734 buildings** carry a wall-base storey count wrong in an unknown direction, and **3,580 (43.9 %)** carry a floor-surface count inflated by one attic. No published number depends on either | 🔴 **`Z_Origin` FIXED and verified 8,160/8,160. Open, enlarged TWICE (CP-2, CP-3). R7 answered “derive it from floor surfaces” and that reader was built and measured — it is right on `TallBuilding`/`Warehouse` and wrong on 43.9 % of the fleet, because it counts attics. What is now owed is not another reader but a DEFINITION of a storey for prototypes with attics, plenums and high bays.** |

---

## 3. Where each item's full history lives

Every live item keeps a `### OPEN-NN` section in the **predecessor**, and that section — not the row
above — is the authority on how the item got to its present state. Find it by its heading; the
headings are unique. The theme section it sits under:

| Item | Predecessor section |
|---|---|
| OPEN-03 | §2 Theme A — integrity of the numbers we publish |
| OPEN-09, OPEN-10, OPEN-35, OPEN-38 | §4 Theme C — simulation correctness |
| OPEN-12, OPEN-13, OPEN-14, OPEN-15, OPEN-16, OPEN-17 | §5 Theme D — data acquisition and imputation |
| OPEN-18, OPEN-19, OPEN-20 | §6 Theme E — method and validation questions |
| OPEN-27 | §7 Theme F — June-audit remnants |
| OPEN-53, OPEN-56, OPEN-58, OPEN-59, OPEN-60, OPEN-61 | §10, appended as each was opened |
| OPEN-62 | **This book only** — it has no history in book I. §6 below is its whole record, plus `extra/MEASUREMENT_open-03_storey-census.md` and `OpenUBEM_debug_References.md` §16 |

**When an item is worked from here on, its new findings are written in THIS book**, in a `### OPEN-NN`
section appended under §6 below — not back into the predecessor, which is closed.

---

## 4. What is open and unstarted, in priority order

Carried from the close of the 2026-08-20 four-board pass. This is the director's ordering, not a
user ruling, and it is not a commitment.

1. ▶ **OPEN-61 — IN MEASUREMENT 2026-08-20, T03 running.** Arc A of
   `implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md` is past both of its gates: **T01
   complete / CP-1 signed**, **T02 complete / CP-2 signed** on five pre-registered controls
   (rebuild reproduces run 4 on **200/200** to within 1.5 × 10⁻⁴ kWh/m²; district heating non-zero on
   **200/200**; the "Water Systems == Total End Uses" mechanism holds on **200/200**). **T03 — the
   full 8,153-building census — is running locally at 12 workers**, ≈8 h, fire-and-forget.
   🔴 **It needed a re-simulation and there was no way around it** — run 4's `.sql` files were
   discarded; all 8,160 buildings kept only `.eio`, `.end`, `.err`. **Cost, now measured rather than
   estimated: 97.2 CPU-hours** (fleet-weighted from the pilot's per-archetype means). The carried
   ≈119 CPU-hours was a good estimate — within 19 % — and a director interim projection of 33
   CPU-hours was **withdrawn at CP-2** as a convenient-sample artifact. The carried **6–13 %** blast
   radius is still an estimate until T04 lands. The remedy shape (request the meter vs read ABUPS)
   stays an open design question and is **explicitly out of that plan's scope**.
2. ✅ **OPEN-03 — Arc B COMPLETE 2026-08-20, CP-4 signed.** The 44 %-less-wall question is
   **withdrawn**: it reproduced on one building. The storey-count disagreement is now **counted
   across all 8,160 with no sampling** — `layout_assign` represents the real storey count for
   **2,446 (30.0 %)** and ignores it for **5,714 (70.0 %)**, the unmatched buildings averaging 3.12
   real storeys (max 105) rendered at 1.21 (max 6). What stays open is the **remedy**, which is
   OPEN-18's territory, not a further measurement.
3. 🔴 **OPEN-62 — the fix landed, the control failed, and the item grew.** The `Z_Origin`
   omission is fixed and verified on 8,160/8,160. But the restated control C9b — the one the user
   ruled for over the cheaper option — **failed on 6 archetypes and 3,734 buildings**, and tracing it
   showed why: `parse_idf()`'s `storey_count` counts **distinct exterior-wall base elevations in
   floor-area zones**, which equals the storey count only when every floor starts its own facade.
   `TallBuilding` reads **10-11 against a true 20**. **The item is no longer a `Z_Origin` erratum; it
   is a wrong-quantity finding.** Production stays clean — the reader that gets 20 right is
   `layout_assigner.py`'s own. 🔴 **AND IT GREW AGAIN AT CP-3.** The user ruled R7 — derive it from
   floor surfaces — and that reader was built (T06) and audited. It gets `TallBuilding` (20) and
   `Warehouse` (1) right, and it is **wrong on 43.9 % of the fleet: it counts an attic as a storey**
   (`SmallOffice`, both restaurant archetypes — 3,580 buildings). Its own allowed-to-fail control
   C16 also proved the *old* method over-counts as well as under-counts (`Warehouse` 1 → 2), so the
   director's own "lower bound" framing from CP-2 is **withdrawn**. **Net: no reader in this codebase
   returns a storey count.** What is owed is no longer another reader but a **definition** — what a
   storey IS for a prototype carrying an attic, a plenum or a high bay. That question has never been
   answered here, and it is not an executor's to answer.
4. **OPEN-35's remaining half** — *which* fallback is correct. Now well-sized (21 buildings, 42
   simulations, seven cells, and a **measured sign flip** in `la_suburban`) and still undecided.
   The no-pooling prohibition now rests on that measurement, not on an argument.
5. **C04 leftover** — `iod` and one `simulation_status` flip: code drift or non-determinism? Needs a
   **same-HEAD double run**.
6. Carried forward untouched: **OPEN-56's** remedy shape, the 4 `Courthouse` → `OpenUBEMUnknown` flips
   (477,804 m²), **OPEN-35's** regression remedy, **OPEN-53's** own 874-of-875 finding.
7. 🔒 **OPEN-27 — CLOSED 2026-08-20.** Both spec lines now name `HighriseApartment`.
   The blocker was never technical: the item sat open for weeks because the two lines live in
   `docs_main/`, which this session may not edit. It closed in four minutes once the user was
   asked for a scoped exception rather than asked to do the edit themselves. **The lesson is
   about the ask, not about the fix** — an item whose only obstacle is a permission should be
   surfaced as a permission question, not carried as work. Verification: `grep -rn
   "MultifamilyHome" docs/docs_main/` → **0**; the Residential set re-derived from
   `openstudio_archetypes.json` → **exactly `MidriseApartment` and `HighriseApartment`**;
   `pytest -k "multifamily or coarse"` → **6 passed**.

A pattern named three passes running and still unaddressed: **OPEN-58, OPEN-60 and OPEN-61 were each
found by an executor auditing its own arithmetic, and no plan asked for that control.** The remedy
shape that keeps suggesting itself is a reconciliation check **inside** `parse_building()` rather than
in whichever task happens to look.

---

## 5. Settled — do not reopen by drift

The full list is the predecessor's **§8**, and it stands unchanged. The four that get re-litigated
most often, restated here so a reader does not have to open the closed book:

- **The post-Phase-E "Other" residual** is process + miscellaneous plug loads only. The STOP decision
  on it is **permanent**.
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** Current disposition, not a legacy caveat.
- **`T_ENGAGE = 0.868 m` and `T_MASS_MAX = 0.35 m` are frozen** on direct measurement. A fleet failure
  reopens the fix plan, never the constants.
- **The headline is the POOLED figure** — total simulated energy ÷ total simulated floor area — and
  per-cell results are **never merged into one number** (OPEN-43's ruling, and now OPEN-35's measured
  sign flip).

---

## 6. Item sections — opened in this book

*(the 21 live items keep their full history in the predecessor, per §3. Sections below record only
what this book has added.)*

### OPEN-61 — amended 2026-08-20, after `PLAN_five-items-2026-08-20-late.md` T01 + T02

**Mechanism — CONFIRMED, not inferred.** The models carry a `DHW_WaterUse_*` `WaterUse:Equipment` /
`WaterUse:Connections` pair with blank inlet/outlet nodes and **no `PlantLoop` to serve it**.
EnergyPlus computes its service-water heating load, finds no plant to charge it to, and books it to
the **District Heating** column — a fuel the IDF never declares. Deleting that pair from one scratch
IDF moved District Heating **0.72 GJ → 0.00 GJ** while Water Systems Natural Gas stayed bit-identical
(**11.68 → 11.68 GJ**). The energy is therefore **additional spend the model reports nowhere**, not a
double count of the gas water heater. `METER_QUERY` (`openubem/results/parser.py:42`, names `:48-54`)
has no district meter, so `total_eui_kwh_m2` silently drops it.

**The discriminator is exact on 108 buildings.** District Heating > 0 **iff** the IDF has a
`DHW_WaterUse_*` object **and** no `PlantLoop`: 5 of 5 in the 48-building `layout_assign` sample, 0 of
the 43 without it, and **60 of 60** on re-simulated production. ~~**All 16,336 production IDFs match the
affected pattern** (16,336 with `WaterUse:Connections`, 16,336 with `DHW_WaterUse_*`, **0** with a
`PlantLoop`).~~ 🔴 **The count was wrong and is corrected 2026-08-20 at CP-1 of
`PLAN_open61-census-open03-storeys-2026-08-20.md` (fact D15): the fleet is 8,160 IDFs, one per
building, and "16,336" came from a recursive `**` glob that double-counts on this tree.**
Re-derived directly over the twelve `fleet_staging/idfs/` directories: **8,160 of 8,160 carry a
`DHW_WaterUse_*` object and 0 carry a `PlantLoop` — 100.00 %.** **The finding is unchanged and the
share is identical; only the denominator was wrong. Cite 8,160, never 16,336.**
**The item is fleet-wide, not a sample artifact.**

🔴 **The size was understated by an order of magnitude, and it is concentrated by archetype.** Of 60
production buildings: 43 lose 0.5–5.3 kWh/m², **17 lose 17.3–89.1**. **14 of those 17 are
`MidriseApartment`**; the low group is `SmallOffice`-dominated (27 of 43). The term tracks service hot
water: **dh ÷ dhw_eui** has median **0.714**, IQR **0.362–0.840**, max 1.004. Per-cell measured share
of Total End Uses (n=5 each, never pooled): austin_centre 1.01 % · austin_rural 1.23 % ·
austin_suburban 0.96 % · austin_urban 1.22 % · la_centre 1.68 % · la_rural 1.16 % ·
**la_suburban 22.51 %** · **la_urban 22.37 %** · nyc_centre 1.42 % · nyc_rural 1.23 % ·
nyc_suburban 1.01 % · nyc_urban 1.04 %.

⚠️ **Fleet exposure is an ESTIMATE, not a measurement.** `MidriseApartment` is **2,818 of 8,160**
buildings (34.5 %). Transferring the sampled ratio onto every building's recorded `dhw_eui_kwh_m2`
gives a fleet-mean unreported term of **8.7 / 17.2 / 20.2 kWh/m²** at the IQR floor, median and
ceiling — roughly **6–13 % of the adopted 153.8**. It transfers a 60-building ratio (only 14 of them
`MidriseApartment`) onto 8,153. **It sizes the exposure; it does not settle it. Do not publish this
range as a correction.** A census-scale measurement is the next arc and is not yet authorised.

**Evidence.** `openubem/outputs/comparisons/open61_district_source.csv` (48) ·
`open61_production_sample.csv` + `open61_production_sample_selection.csv` (60) ·
`extra/MEASUREMENT_open-61_district-heating.md` (T01 + T02) ·
`PLAN_five-items-2026-08-20-late.md` §6b, §6c (director controls D8–D12). **Stays open, re-scoped,
raised in priority.**

### OPEN-03 — amended 2026-08-20, after T03

🔴 **The item's stated mechanism is retracted.** The carried "`layout_assign` builds 44 % less wall on
the same floor plate" reproduces on **exactly one building — the one it was measured on**
(`nyc_centre/way_265424467`, ratio 0.5606). Across the other seven cells with a valid pair the wall
ratio runs **+57 % to −64 %, with no consistent sign**. This is the **fourth** carried figure this arc
has had to retract.

**And the premise fails before the measurement does.** Control C7 excluded **40 of 48 pairs** because
the two arms do not build the same floor plate; **28 of those are storey-count driven** (e.g.
`austin_centre/way_328649870`: `layout_assign` builds 3 storeys on a footprint bit-identical to
`auto`'s single storey). Among the 8 pairs where storeys do agree, **roof and ground-contact ratios
are exactly 1.0000** and only wall moves. **The live question is a storey-count disagreement between
`layout_assign` and `auto`, not wall construction.**

**Touches OPEN-60:** 2 of 48 `layout_assign` IDFs use Zone `Multiplier` > 1; 0 of 48 `auto` IDFs do.

**Evidence.** `openubem/outputs/comparisons/open03_envelope_decomposition.csv` ·
`extra/MEASUREMENT_open-03_envelope-decomposition.md`. **Stays open, re-framed.**

### OPEN-03 — amended again 2026-08-20, after T05: the storey disagreement is now counted fleet-wide

🔴 **The re-framed question is measured, and it is bigger than the 48-building sample showed.**
`open03_storey_census.csv` covers **all 8,160 buildings** (12 cells, no sampling, no simulation).
**C9 verified by the director: the census reproduces all 96 rows of the 48-building envelope
measurement exactly, both arms, 0 mismatches** — and restricted to those 48 it returns **28
disagreements of 48**, the predecessor's number to the unit.

**Headline, fleet-wide: 4,914 of 8,160 = 60.2 % disagree**, and the direction is nearly
one-sided — `layout_assign` is **shorter in 95.2 %** of disagreements (mean −3.07 storeys, worst
−104).

⚠️ **But 60.2 % is the weaker of the two readings and must not be quoted as the finding.** The
director's own check of the CSV shows `layout_assign_storey_count` is a **per-archetype constant** —
one value for every building of 18 of the 20 archetypes (`SmallOffice` = 1 against 12 distinct `auto`
values; `TallBuilding` = 1 against 19). Only the two no-baseline archetypes vary, and there the value
is copied from `auto`. So 60.2 % measures *real building vs its prototype*, which is close to
expected-by-construction.

🔴 **The reading that answers the item is the match-status coverage:** the `layout_assign` arm
represents the building's real storey count for **2,446 of 8,160 = 30.0 %** (`identity` 1,226 +
`applied` 502 + `no_baseline_fallback_auto` 718). For the other **5,714 = 70.0 %** it builds the
prototype's storeys regardless — those buildings average **3.12** real storeys and reach **105**, and
are rendered with an average of **1.21** geometric storeys, never more than **6**.

**Touches OPEN-60, now at scale:** `Zone.Multiplier` > 1 in **434 of 8,160** `layout_assign` buildings
(5.3 %) and **0 of 8,160** `auto` — the 2-of-48 vs 0-of-48 direction holds and the rate scales.

⚠️ **A measurement caveat found by the executor and not swept under:** the wall-min-Z storey-count
method never adds a zone's own `Z_Origin` under Relative coordinates, under-reading for 6 archetypes
(**2,983 buildings, 36.6 %**). Registered `[OPEN]` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
§16 and flagged per row. ✅ **It does not drive the headline** — director's split gives **60.8 %**
disagreement on the 5,177 clean rows against **59.2 %** on the 2,983 at-risk rows. It bounds the
per-archetype magnitudes for those 6, not the fleet rate.

**Evidence.** `openubem/outputs/comparisons/open03_storey_census.csv` ·
`extra/MEASUREMENT_open-03_storey-census.md` · CP-4 signed in
`implemenation/PLAN_open61-census-open03-storeys-2026-08-20.md` §6c. **Stays open, now with a number.**

### OPEN-12 — 🔒 CLOSED 2026-08-20 (amended after T04, then closed the same day)

**The third 100 % cell is `nyc_suburban`** (1,589 of 1,589 missing `height_m` at source), alongside
`nyc_rural` (198/198) and `austin_rural` (245/245). **The recorded 36.4 % and 19.2 % are superseded by
100.0000 % and 100.0000 %** — they only ever reproduced on a gitignored UTCI-arc scratch dataset that
was never committed and never read by the adopted pipeline.

**The fleet-level figures already in the register are CONFIRMED exactly:** missing across all 12 cells
sums to **2,806 of 8,160**, and the three 100 % cells hold **2,032** buildings (245 + 198 + 1,589).
Per-cell n sums to **8,160** (control C9). **Previously unrecorded:** `austin_centre` sits at
**84.5 % (349/413)** — not 100 %, so it never appeared in the "cells at 100 %" framing.

**Evidence.** `openubem/outputs/comparisons/open12_height_residual.csv` ·
`extra/MEASUREMENT_open-12_third-cell.md`.

🔒 **CLOSING NOTE — 2026-08-20, on the user's ruling.** The item asked which cells carry a
`height_m` residual and whether the recorded percentages hold. Both halves are now measured: the
unnamed third cell is **`nyc_suburban`**, and the recorded **36.4 %** and **19.2 %** are **retracted
and replaced by 100.0000 % and 100.0000 %**. **What survives this item:** the source-coverage gap it
measured — **2,806 of 8,160 buildings with no source height** — is real and stays open, but it belongs
to **OPEN-14** (no tracked Overture slice) and **OPEN-15** (no imputation Phase E), which already own
it. Nothing about this item is a defect anyone still has to fix. **Do not reopen it to re-ask "which
cells" — the answer is in `open12_height_residual.csv`, per cell, with n summing to 8,160.**

### OPEN-13 — 🔒 CLOSED 2026-08-20 (amended after T05, then closed the same day)

🔴 **The recorded coverage loss does not exist.** Nothing was deleted. Commit `a3bf4d95`
(2026-08-12) **added** a module-level `pytest.skip(allow_module_level=True)` to
`tests/test_draw_methods.py` (`--stat`: `13 +`, no deletions), and the 2026-08-13 `_HAS_DRAW_TIER`
narrowing restored the tests. **Director control at HEAD:**
`py -3 -m pytest -q tests/test_draw_methods.py` → **`43 passed, 10 skipped in 0.65s`**. Same node IDs,
same file, running today. C11 = 43 matches the register's number exactly — **but 43 was never a loss.**

**The 10 that remain skipped belong to OPEN-17,** not here: all wait on the still-unimplemented
`imputation._draw_tier` / `_draw_stratum_col_for` (`TestDrawTierRouting` 6, `TestNoEUILeakage` 1,
`TestDrawTierDeterminism` 1, and 2 of 6 in `TestDefaultByteIdentity`).

🟡 **Suite baseline moved.** `py -3 -m pytest -q tests/` printed
**`1918 passed, 56 skipped, 892 warnings in 1443.51s (0:24:03)`**, exit 0. The carried 1,875/55 is
stale. **Carry 1,918/56 forward.**

**Evidence.** `openubem/outputs/comparisons/open13_lost_tests.csv` ·
`extra/MEASUREMENT_open-13_lost-coverage.md`.

🔒 **CLOSING NOTE — 2026-08-20, on the user's ruling.** This item closes **on refutation, not on
repair** — the loss it recorded never happened. Both defects it forwarded out of the UTCI arc are
disposed of: **E-UTCI-13 fixed 2026-08-12**, **E-UTCI-12 contained**, and the "**43 passing tests
traded away**" is withdrawn — the 43 run at HEAD today. **What survives this item:** (1) the **10
tests that stay skipped**, which are **OPEN-17's** — they wait on the unbuilt
`imputation._draw_tier` / `_draw_stratum_col_for` router hook and will unskip themselves when OPEN-17
is built; (2) the restated suite baseline **1,918 passed / 56 skipped**. ⚠️ **The 43-test figure must
not be requoted as a loss anywhere.** It survives in the predecessor's §5 Theme D history and in this
book only as the number that was refuted.

---

### OPEN-20 — 🔒 RETIRED 2026-08-20, not closed

**Retired on the OPEN-21 precedent, by the user's ruling.** The item asked for a validation matrix
wider than 3 cities × 4 urban-form rings. It is **a scope question, not a defect** — nothing is
broken, nothing is blocked, and there is no measurement that would settle it. It sat unactioned from
**2026-06-17 to 2026-08-20** and was tracked **twice** for that entire time: as this row and as
`docs/docs_TODO/wider_validation_matrix.md`. Retiring the row removes the duplicate, not the question.

**Its substance was already discharged** by T20(b) of `PLAN_twenty-items-2026-08-19.md`, which wrote
the external-validity statement in full (`extra/MEASUREMENT_open-18-20_method-bounds.md` §(b)): what
the 12 cells support, what they do not, and the hardest bound on them — **OPEN-19's finding that the
model does not vary construction or HVAC by climate zone, so even within the three sampled cities the
physical basis for cross-climate generalisation is weaker than the geography suggests.**

⚠️ **What survives it:** that caveat, which applies to **every published figure including the
adopted 153.8231 kWh/m²** — a pooled statistic over exactly this population. Precision *within* the
population is not in question; reach *beyond* it is what the TODO doc now bounds. **Retiring the ID
does not retire the caveat, and the caveat is not OPEN-20's to carry any more — it is the TODO doc's
and OPEN-19's.** ✅ **`OPEN-20` is retired and must not be reused.**

---

### OPEN-62 — OPENED 2026-08-20 on the user's grant (Z_Origin under Relative coordinates)

**How it was found.** Not by looking for it. The T05 executor was building the fleet storey census
and validating its parser against the 18 baseline-mapped archetypes when the counts for six of them
refused to make sense. **It registered the gap `[OPEN]` in the debug reference and flagged every
affected row instead of fixing it** — the right call, because a fix would have changed the value
control **C9** was required to reproduce, and C9 was the only thing standing between this census and
the predecessor's 48-building result. Fourth item in a row found by an executor checking its own work
against something, and again no plan asked for the check.

**Mechanism, measured zone-by-zone rather than inferred.** A zone's storey elevation can live in
either of two places in an IDF: baked into every wall vertex, or carried in the `ZONE` object's own
`Z_Origin` with the vertices left local to it (`GlobalGeometryRules` Coordinate System `Relative`).
The census parser reads the minimum wall Z and **never adds `Z_Origin`**, so every zone in the second
family reports the same near-zero elevation and a tower collapses to 1–3 distinct storeys.

| Archetype | Zones affected | Verdict |
|---|---|---|
| `SuperTallBuilding` | 232 / 256 | 🔴 severe |
| `TallBuilding` | 145 / 164 | 🔴 severe |
| `Outpatient` | 59 / 118 | 🔴 severe |
| `MidriseApartment` | 18 / 27 | 🔴 severe |
| `HighriseApartment` | 18 / 27 | 🔴 severe |
| `SecondarySchool` | 21 / 46 | 🔴 severe |
| `LargeOffice` | 3 / 23 | ⚪ immaterial — none is a floor-area-counting zone; C9 reproduces its expected 4 exactly |
| `QuickServiceRestaurant`, `FullServiceRestaurant` | 1 each | ⚪ immaterial — same reason |
| 10 remaining archetypes | 0 | ⚪ absent — `Z_Origin == 0.0` uniformly |

**6 archetypes, 2,983 of 8,160 buildings — 36.6 % of the fleet.** Flagged per row as
`layout_assign_z_origin_collapse_risk` in `openubem/outputs/comparisons/open03_storey_census.csv`.

✅ **What it does not contaminate, checked before the item was opened.** OPEN-03's fleet-wide storey
result survives excluding every affected building: **60.8 %** disagreement on the 5,177 clean rows
against **59.2 %** on the 2,983 at-risk rows. The gap bounds the *per-archetype magnitude* for those
six; it does not produce the headline. **No published number is known to depend on it.**

⚠️ **Why C9 passing is not reassurance.** C9 compares this census against the predecessor's
48-building sample and passes **96/96 exact** — because both were produced by the **same naive method
against the same baseline files**. A shared parser reproducing itself is agreement, not correctness.
This is worth carrying past this item: a control that re-runs the suspect code cannot exonerate it.

✅ **The question that gated the remedy — asked and ANSWERED the same day, by the director, at the
source.** It was opened as unchecked and is now checked: **production geometry code does NOT share
the omission.** Both production readers handle it correctly:

- `openubem/geometry/layout_assigner.py:471` reads each zone's `Z_Origin`, and `:491-493` adds it
  back into every vertex when `coord_sys == "RELATIVE"` before taking `min(v[2])`.
- `openubem/viz/geometry_extract.py:143-155` builds the same origin lookup and passes `dz` into
  `_parse_bsd_vertices()`.

A repo-wide search finds **no third production reader** that counts storeys from wall Z. The gap
lives in **one analysis parser** — `parse_idf()` in
`scripts/analysis/open03_envelope_decomposition_2026-08-20.py` — and in the **one** script that
imports it, `open03_storey_census_2026-08-20.py`. Nothing else consumes it.

🟢 **This resizes the item downward, and it is recorded as a downgrade rather than quietly dropped.**
OPEN-62 is a **measurement-instrument erratum**, not a geometry defect: no building was built at the
wrong height, no envelope area is wrong, no EUI is affected. What it does damage is the
**`layout_assign_storey_count` column** for the 6 flagged archetypes in
`open03_storey_census.csv` — which is exactly what its `layout_assign_z_origin_collapse_risk` flag
already says, and which OPEN-03's headline was shown to survive.

**What remains open, and it is small:** two analysis scripts read `Z_Origin` incorrectly and one CSV
column is a parsing artifact for 2,983 rows. The fix is the four lines `layout_assigner.py:491-493`
already contains. It is **not** urgent and it is **not** to be applied blind — re-running the census
with it changes what control C9 reproduces, so the fix and a restated C9 have to land together.

⚠️ **A note on how close this came to being mis-sized.** The item was opened with the alarming
reading — "six archetypes may be built at the wrong height" — deliberately stated as *unchecked*
rather than asserted. One grep settled it in under a minute. **The same lesson as D18: the check is
cheaper than the hedge.**

---

## 7. Amendment log

**2026-08-20 (evening) — 🔴 CP-2: the restated control FAILED, and the failure is the most
valuable result of the day.**

**Two rulings were taken on it the same evening.** **R6 — preserve the census `.sql` corpus**: the
≈38 GB the OPEN-61 census is writing moves out of the ephemeral session scratchpad to a durable path
once the run finishes, and into an inventory that is checked rather than written once. Chosen over
"preserve only what is cited", which is the policy that already failed — it protects answers already
given, not the next unasked question, and the last discard cost **97.2 CPU-hours**. **R7 — a storey
count is derived from FLOOR SURFACES**, origin-corrected: the reader that gave the correct **20** on
`TallBuilding` where the wall method gave 10. `compute_band_map()` was considered and set aside as
too heavy a production dependency for an analysis script, though it remains the authority for
OPEN-03's untouched 30 / 70 split. Both are executing as T06 and T07 of the OPEN-62 plan.

C9b compared the `Z_Origin`-corrected parser against `layout_assigner.py`'s own origin-aware reader —
a reader that never imported `parse_idf()`. **12 of 18 archetypes agree. Six disagree, over 3,734
buildings.** The director traced the cause rather than filing it as a disagreement: on
`TallBuilding.idf`, floor surfaces give **20** distinct elevations, all wall bases 20, exterior wall
bases 19, and *exterior wall bases in floor-area-counting zones* — what `parse_idf()` actually counts
— give **10**. Those ten are the levels where a **new exterior wall starts**. A curtain wall spanning
several floors contributes one elevation, not several.

🔴 **`storey_count` is not a storey count.** The `Z_Origin` fix is correct and was necessary; it was
not sufficient, because it removed one error from a quantity that was measuring the wrong thing.

⚠️ **This is the entry to re-read before writing the next control.** The old C9 passed **96/96**
before the fix and would have passed again after it, because both sides came from the same parser.
Had it been kept, OPEN-62 would have **closed today** with the column certified correct while
undercounting `TallBuilding` by 9 storeys out of 20. **The user's ruling R1 — restate the control
rather than keep it — is the only reason this surfaced, and it surfaced because the new control was
allowed to fail and did.** A control that cannot fail is not a control; this arc now has a measured
instance of that, not an argument for it.

**Consequences, all recorded rather than deferred.** OPEN-62 **stays open with enlarged scope** and
is no longer a "measurement erratum". C13's restatement is publishable **only as a lower bound** —
built mean 1.21 → **≥ 2.25**, built max 6 → **≥ 16** — since the corrected figures come from the same
undercounting proxy. ✅ **OPEN-03's 30 / 70 headline is untouched** and stays quotable: it rests on
`compute_band_map()`, which was already origin-aware. ✅ **No production code is implicated** — the
reader that reads 20 correctly *is* production's.

**What is owed is a ruling, not a measurement:** what should a storey count be derived from — floor
surfaces, `compute_band_map()`, or something else? Building the answer before that is decided would
repeat the mistake this entry exists to record.

**2026-08-20 (evening) — 🔴 CP-3: T06 audited, C17 REFUSED, and the director withdraws his own
CP-2 framing.**

T06 built the floor-surface reader the user ruled for (R7) and ran four pre-registered controls. The
executor's arithmetic is correct in every particular — all of it was re-derived by the director
directly from the CSV and from the preserved prototypes rather than accepted from the report — and
**three of the four controls still do not mean what they appear to mean.**

**C15 signed.** 0 mismatches on every pre-existing column across 8,160 rows; the change is additive.

**C16 failed as designed, and the failure is the finding.** 38 rows, all `Warehouse`, floor 1 < wall
2. Measured on `scratchpad/open03_proto_saved/Warehouse.idf`: exterior wall z-bases `{0.0: 8 walls,
4.267: 2 walls}` against **3 FLOOR surfaces all at z = 0.0** — a one-storey high-bay facade split
into two vertical wall bands, which the wall method reads as a second storey. 🔴 **The wall-base
method therefore over-counts as well as under-counts, and `storey_count` is not a bound in either
direction. CP-2's "publish C13 as a LOWER BOUND" instruction is withdrawn by its author.** It held
only because `floor < wall` occurs 0 times inside the unmatched subset — archetype mix, not method.

**C17 refused.** `storey_count_floor` counts an attic as a storey: `SmallOffice.idf` has **9 floor
surfaces at z = 3.05, every one in zone `Attic`**; both restaurants carry zone `attic` at z = 3.049.
Three one-storey prototypes read as 2, covering **3,580 buildings (43.9 % of the fleet)** and **2,797
of 5,714 unmatched rows (48.9 %)**. Attic-corrected the built mean is **2.45**, not 2.94. **OPEN-03's
built-storey headline may be published only as the range 2.45 – 2.94.** T06 claimed to turn a bound
into a value; it exchanged a bias of unknown direction for a bias of known direction.

**C14 accepted with a correction.** 18/18 agreement with `compute_band_map()`'s `n_proto` is real and
using `n_proto` beat the fixed table the plan specified. But `n_proto` is documented as *"deliberately
left as the measured Z-BAND COUNT, never a represented-storey count"*
(`openubem/geometry/layout_assigner.py:404-406`). The agreement proves the new reader reproduces
production's **band** counter. ✅ **Not a production defect** — production branches `match_storeys()`
on it and never publishes it as storeys. The defect belongs to the census and to this register, for
reading a band count as a storey count.

**The pattern is now three-for-three.** C9 could not fail and hid a wrong quantity. C9b was allowed
to fail, failed, and found it. C16 was allowed to fail, failed, and found the *opposite* error in the
same column. 🔴 **Every controls-passed report in this arc that came from a control sharing its
subject's assumptions has been wrong.** The cheap option — "fix it and keep the control" — would by
now have closed OPEN-62 twice.

**What is owed.** Not another reader. A **definition** of a storey for prototypes with attics,
plenums and high bays, which this project has never written down. ⚠️ **Do not let an executor
resolve it by excluding zones named `Attic`** — zone-name matching is the generalisation A1 already
falsified (F-07, `layout_assigner.py:389`), and it would move archetypes across `match_storeys()`'s
`n_proto` branches, which production's own docstring warns against by name.

**2026-08-20 (late afternoon) — 🔒 OPEN-27 CLOSED, and CP-1 of the OPEN-62 plan signed with
control C12 amended rather than passed.**

**OPEN-27 closed.** The user granted a narrow one-time exception (R5) to the never-edit-`docs_main/`
rule, for two lines only. Both now read `HighriseApartment`. Verified three ways, not one: `grep -rn
"MultifamilyHome" docs/docs_main/` → **0**; the Residential archetype set re-derived from
`openubem/data/openstudio_archetypes.json` → **exactly `MidriseApartment` and `HighriseApartment`**,
so the replacement was checked against the data rather than copied from the item text; and
`pytest -k "multifamily or coarse"` → **6 passed** (1,968 deselected, consistent with the 1,974-test
baseline). ⚠️ **Read the closure honestly:** this item was never hard. It was open because its only
obstacle was a permission this session could not grant itself, and nobody had put the permission
question to the user. It closed in minutes once asked. **An item blocked on a permission is not
work in progress and should not be carried as if it were.**

**CP-1 signed on the OPEN-62 plan, with C12 amended.** The parser fix mirrors
`layout_assigner.py:465-495`. The director re-ran the load-bearing measurement directly rather than
re-delegating it: `Outpatient` has **59 of 118 zones carrying a non-zero `Z_Origin`** (`{0.0, 3.048,
6.096}`) and still reports 3 storeys before and after the fix; `SuperTallBuilding` goes **1 → 16**.
The plan predicted **6 archetypes move, 12 hold**; the measurement is **4 move, 14 hold**. 🔴 **This
is recorded as an amendment, not a pass.** `Outpatient` and `SecondarySchool` are wrong *at the zone
level* and right *at the building level* by coincidence of their own mixed encoding — some zones on a
floor bake elevation into wall vertices, others carry it in `Z_Origin`, and the corrected band lands
on a band the naive set already held. **Any future measure that counts storeys per zone rather than
per building will see both archetypes move.** Calling C12 "passed" would have buried that.

🔴 **A limitation found in the audit and not raised by the executor.**
`open03_envelope_decomposition_2026-08-20.py:parse_idf()` **cannot read the raw registry IDFs at
all** — against `config.BASELINE_IDF_DIR`'s own `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf`
it returns every area as `0.0` and `storey_count` `0`, silently, because it resolves fields by their
`!- field name` comments and the DOE files do not carry them. Every result this parser has ever
produced rests on **geomeppy-resaved** copies, and that was stated nowhere. The 18 resaved
prototypes have been preserved at `scratchpad/open03_proto_saved/` (gitignored) so the control is
reproducible. **A parser that fails to zero instead of raising is the same class of defect as
OPEN-61's silent District Heating booking** — the number looks like an answer.

**2026-08-20 (afternoon, while the OPEN-61 census runs) — 🔒 OPEN-15 and OPEN-16 RETIRED into
OPEN-17 on the user's ruling R2; three further rulings recorded.** The user asked what could move in
parallel with the saturated machine and then ruled on four questions put to them directly.

- **R1 — OPEN-62: fix the parser and restate control C9.** Chosen over the cheaper "fix and keep the
  old C9", which would have left a control that re-runs the suspect code and calls the result
  agreement. Executing as `implemenation/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`.
- **R2 — OPEN-15 + OPEN-16 merge into OPEN-17.** Three rows described **one** fact: the imputation
  tiers were built and never wired to the production router. OPEN-17 carries all three; the other two
  rows are **struck, not deleted**, and say where their fact went. ⚠️ **This is bookkeeping, not
  progress** — nothing was measured, fixed or decided, and the entry says so where a reader will hit
  it. **Count: 17 live / 45 retired / 62 total, next free `OPEN-63`.**
- **R3 — retire none of OPEN-09 / 10 / 14 / 18 / 19 / 38.** The director recommended retiring
  **OPEN-18** (mechanism confirmed unreachable) and **OPEN-19** (needs a climate-zone/code-year switch
  that does not exist). **The user declined.** Recorded as *declined*, not as never-asked, so the
  recommendation is not quietly re-proposed next pass.
- **R4 — OPEN-27 stays with the user** — ⚠️ **superseded the same afternoon by R5.**
- **R5 — a narrow one-time exception to the never-edit-`docs_main/` rule, for OPEN-27's two lines
  only.** The user granted it explicitly when told that rule was the *only* thing keeping the item
  open. The director applied both edits, verified, and closed OPEN-27. **The exception is scoped to
  those two lines and does not generalise** — `docs_main/`, OVERVIEW and DESIGN stay unwritable
  without a fresh grant, and this entry exists so a later pass does not read one exception as a
  standing permission.

Two §1 defects were repaired in the same pass and are named rather than smoothed over: the **Live IDs
line read `(18)` and omitted OPEN-62** — the identical one-row-short failure the rotation note two
entries below describes, repeated within hours of being written — and the **"Plans in force" row was
stale**, still describing T02's pilot as in flight. It now records **two** live plans, which is a
first for this arc and is deliberate.

**2026-08-20 — book opened.** Predecessor closed at 8,205 lines / 61 items / 40 struck. 21 live rows
carried over verbatim. One correction made in the act of rotating: **OPEN-61's missing §1 table row**
was written and inserted into the predecessor before it was closed, so its recount script and its
prose now agree at 21 live / 40 struck / 61 total, next free `OPEN-62`. **No item was opened, closed,
merged or re-scoped by the rotation.**

**2026-08-20 (later) — `PLAN_five-items-2026-08-20-late.md` executed and closed, T01–T05.** Four items
amended in §6: **OPEN-61** (mechanism confirmed, fleet-wide, size raised by an order of magnitude —
re-scoped and raised in priority), **OPEN-03** (stated mechanism retracted; the live question is
storey count — re-framed), **OPEN-12** and **OPEN-13** (**both ready to close**; OPEN-13's 10
residual skips reassign to **OPEN-17**). **No item was opened, closed, struck or merged by this
pass** — the count stands at **21 live / 40 retired / 61 total, next free `OPEN-62`.** Suite baseline
restated to **1,918 passed / 56 skipped**. Two new debug-reference entries were registered by the
executors (`run_ep_isolated()` + relative paths, ch. 13; IDF vertex-parsing object-boundary bug and
Attic-zone floor double-count, ch. 16).

**2026-08-20 (later still) — 🔒 OPEN-12 and OPEN-13 CLOSED on the user's ruling.** Asked directly
whether to close the two the plan had left ready, the user answered *"oui ferme OPEN-12 & 13"*. Both
close on measurement, neither on repair: **OPEN-12** on a completed census (third cell `nyc_suburban`;
36.4 %/19.2 % retracted for 100 %/100 %; fleet counts confirmed exactly), **OPEN-13** on a refutation
(the 43 "lost" tests were never lost and run at HEAD). Their §2 rows are struck, not deleted, and each
carries a closing note in §6 naming what survives it — **OPEN-12's residual gap to OPEN-14/OPEN-15,
OPEN-13's 10 skips to OPEN-17**. **Count moves for the first time in this book: 19 live / 42 retired /
61 total, next free `OPEN-62`.** The §1 fleet-figure caveat was corrected in the same pass — the
carried "~1 % low by OPEN-61 on four buildings" is superseded by the fleet-wide 6–13 % **estimate**.

**2026-08-20 (fourth entry of the day) — 🔒 OPEN-20 RETIRED, and OPEN-27 given its paste-ready
erratum.** Asked to rule on three possible further closures, the user retired **OPEN-20** on the
**OPEN-21 precedent** — a scope question, not a defect, duplicated in `docs/docs_TODO/` since
2026-06-17. Its ID is retired and must not be reused; the external-validity caveat it carried passes
to that TODO doc and to **OPEN-19**. **OPEN-27** stays live on the user's own ruling: they took the
paste-ready erratum to fix at source. 🔴 **A second occurrence was found in the act of preparing it
and was never recorded before** — `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78`
carries the same wrong `MultifamilyHome` name as `DESIGN_step-2…:529`, so the erratum is **two edits,
not one**. Director re-verified at HEAD: `MultifamilyHome` has **0** occurrences in
`openubem/data/openstudio_archetypes.json`, whose two `sector == "Residential"` entries are
`MidriseApartment` and `HighriseApartment`. ⚪ **OPEN-18 was examined as a closure candidate and
REJECTED as one** — its ✅ marks the elimination of the `Zone.Multiplier` *approach*, not of the
defect; book I §8 says so explicitly (*"Q3 stays open; that approach does not"*) and calls it the
largest open modelling problem in the project. **Count: 18 live / 43 retired / 61 total, next free
`OPEN-62`.**

**2026-08-20 (fifth entry of the day) — ✅ OPEN-03's storey question counted across the whole fleet
(T05 / CP-4 of `PLAN_open61-census-open03-storeys-2026-08-20.md`).** First census of the storey
disagreement beyond 48 buildings: **all 8,160, no sampling, no simulation.** Director re-derived every
control against the CSV rather than accepting the report — **C9 passes 96/96 exact** and the 48-row
restriction returns **28 of 48**, reproducing the predecessor exactly. 🔴 **The headline number
carried forward is 70.0 %, not 60.2 %:** the disagreement rate compares a per-building count against a
**per-archetype constant** (director's finding, not in the executor's report — 18 of 20 archetypes
have exactly one `layout_assign` storey value), so the meaningful statement is coverage —
`layout_assign` represents the real storey count for **2,446 of 8,160 (30.0 %)** and ignores it for
**5,714 (70.0 %)**. ⚠️ **A new parsing defect was found in the act of measuring** — the wall-min-Z
method omits `Z_Origin` under Relative coordinates, affecting 6 archetypes / 2,983 buildings (36.6 %);
the executor registered it rather than silently fixing it, and the director confirmed it does **not**
drive the headline (60.8 % clean vs 59.2 % at-risk). 🟡 **Director recommends granting ONE new ID,
`OPEN-62`, for that parsing gap** — and recommends **against** a second ID for the storey coverage
finding, which belongs to OPEN-03 and is now recorded there. **Neither is opened; a new ID is the
user's to grant.** 🔴 **And one lead that fell out of it, checked rather than hedged:** the `auto` arm
reproduces the source storey count **8,153 times in 8,160**, and the director intersected those 7
exceptions with the 7 buildings the adopted baseline excludes — **they are the same seven, 7 of 7**
(six `Warehouse`, one `LargeHotel`, every one `not_simulated`, every one stating `levels = 1` while
built at 3, 6 or 19 storeys). **The adopted 8,153 denominator and the storey-parse 8,153 are one
fact, not two.** Why a storey over-read and a simulation failure travel together is **untraced** and
was not in scope here. **Count unchanged: 18 live / 43 retired / 61
total, next free `OPEN-62`.**

**2026-08-20 (sixth entry of the day) — ✅ CP-2 signed, T03 launched, and 🆕 OPEN-62 opened on the
user's grant.** Two things landed together. **(a) Arc A cleared its second gate.** T02's stratified
200-building pilot passed all five pre-registered controls, every one re-derived by the director from
the CSV rather than accepted on report: the HEAD rebuild reproduces run 4's recorded EUI on **200/200**
(largest deviation anywhere **1.49 × 10⁻⁴ kWh/m²**), district heating is non-zero on **200/200**
(0.09–19,234 GJ), **C2b** — added at CP-1 — holds on **200/200** with the largest non-Water-Systems
district row in the entire pilot at **0.000000 GJ**, mean rate **47.7 s** against F4's 52.5 s, and all
**20 of 20** archetypes are represented. The census cost is now measured, not estimated:
**97.2 CPU-hours** fleet-weighted, dominated by a heavy tail — 797 buildings (9.8 % of the fleet) buy
53 % of the compute. 🔴 **A director estimate was withdrawn in the same act:** the interim projection
of **33.1 CPU-hours** was wrong by a factor of three because it came from the read-verification
sample, which contained none of that tail. **F4's original ≈119 was the better number all along.**
Host ruled **local, 12 workers** — the harness's 200/200 reproduction is evidence about *this*
machine and none of it would transfer to a Speed port. **T03 is running.** ⚠️ **The pilot's pooled
23.87 kWh/m² is NOT a fleet number and may not be quoted as one** — the pilot is stratified, not
proportional, so it over-weights the large buildings that carry the most service hot water; the
comparison against 8.7 / 17.2 / 20.2 is C5's job in T04. **(b) The user granted the ID the director
recommended at CP-4.** **OPEN-62** is opened for the `Z_Origin` parsing gap (6 archetypes, 2,983
buildings, 36.6 %), and the recommendation *against* a second ID for the storey-coverage finding
stands — that result lives in OPEN-03, where it was recorded. The new item is opened with its own
first question already named: is the gap in production geometry code, or only in the measuring
script? 🟢 **It was opened unchecked and answered the same hour, at the source: production does NOT
share it** — `layout_assigner.py:471` and `:491-493` add `Z_Origin` back before taking the minimum,
`viz/geometry_extract.py:143-155` does the same, and no third production reader exists. **OPEN-62 is
therefore a measurement-instrument erratum bounded to two analysis scripts and one CSV column, not a
geometry defect: no building is built at the wrong height.** It is recorded as a downgrade rather
than quietly dropped, and it stays live because it is unfixed. **The check cost one grep; the hedge
would have cost the item its proportion** — the same lesson D18 recorded four hours earlier.
**Count: 19 live / 43 retired / 62 total, next free `OPEN-63`.**

