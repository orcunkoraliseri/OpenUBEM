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
| **Live items** | **12** — 🟢 **FOUR CLOSED 2026-08-21 on user ruling R3: OPEN-09, OPEN-10, OPEN-14, OPEN-18** (sections in §6; the arc's first closures since 2026-08-20). 🔵 was 19 at open; OPEN-27 closed 2026-08-20; OPEN-15 and OPEN-16 retired into OPEN-17 on 2026-08-20 (user ruling R2). ⚠️ **OPEN-18 was recommended for retirement on 2026-08-20 and the user DECLINED; on 2026-08-21 the user closed it. The reversal is recorded, not smoothed over.** |
| **Retired / struck** | **50** — 46 + the four closed 2026-08-21. Check: 12 + 50 = 62. |
| **Total ever opened** | **62** — `OPEN-01 … OPEN-62`, no gaps, no duplicates |
| **Next free item ID** | **`OPEN-63`** |
| **Next free defect ID** | `E-LA-42` · `E-UTCI-17` |
| **Adopted fleet figure** | **153.8231 kWh/m²** pooled over 8,153 buildings — 🛑 **CAVEAT, RULED 2026-08-22 (CP-2, user delegated the call to the director): the adopted figure is KNOWN LOW and is NOT being restated.** District heating served to hot water was dropped from `total_eui_kwh_m2`. **The parser was fixed 2026-08-22** (OPEN-61 T01/T01b), so every future run carries it. On the **census** population the fix moves the pooled figure **152.3011 → 171.7718 kWh/m² (+19.4707, +12.78 %, n = 8,144)**. ⚠️ **That is NOT a correction to 153.8231 — the two are different populations and must never be differenced.** **153.8231 over 8,153 stands as the published figure**, carrying this caveat. ⚠️ **not volume-correct**, OPEN-56's ≈+1.0 is not in it, and 🔴 **low by OPEN-61 — and the size is now MEASURED, not estimated (2026-08-20 night, CP-3): 19.4707 kWh/m² of district heating, pooled over 8,144 buildings, is present in the simulations and absent from the reported total** = **12.7 % of pooled site energy**, at the top of the earlier 6–13 % estimate. ⚠️ **This is a size, not a correction — 153.8231 stands unchanged**, and §C6b of `extra/MEASUREMENT_open-61_fleet-dh-number.md` shows it **cannot** be applied as a flat offset: **116 buildings (1.4 %) carry 70.5 % of it.** 🟢 **AND THE 116 NOW HAVE A NAME (2026-08-21, T04, director-verified to machine precision): they are `SuperTallBuilding` (24) + `TallBuilding` (92) — ONE class, lift 70.2×, 76.7 % of them in `nyc_centre`. The remedy is narrow, not parser-wide.** 🟢 **AND THE DENOMINATOR IS NO LONGER IN QUESTION (2026-08-21, T01, user ruling R1): `auto_storey_count` matches the REAL storey count on 8,153 of 8,160 buildings (99.91 %) and builds a denominator identical to reality's. The “~2.9× swing” reported at CP-F is RETRACTED as a description of ambiguity — it was the size of `layout_assign`'s error, not the width of a choice. See §6.** |
| **Rulings owed by the user** | **none.** ✅ `OPEN-62` was opened on the user's grant 2026-08-20, and the director's recommendation against a second ID for the storey-coverage finding stands (it lives in OPEN-03). ✅ **Four more rulings were asked and answered the same afternoon** — R1 fix OPEN-62's parser and restate control C9; R2 merge OPEN-15/16 into OPEN-17; **R3 retire none of OPEN-09/10/14/18/19/38 — the director recommended retiring 18 and 19 and the user declined, recorded as declined rather than left un-asked**; R4 the user applies OPEN-27's two edits and the director verifies. Full text: `implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §4. ✅ **R4 was superseded the same afternoon**: the user granted a narrow one-time exception to the never-edit-`docs_main/` rule for OPEN-27's two lines only, the director applied them, and **OPEN-27 is closed**. The exception was scoped to those two lines and does not generalise. |
| **Plans in force** | 🟢 **NONE — all three closed and archived 2026-08-21.** (1) `implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md` — T01–T05 complete, CP-1–CP-4 all signed; its stale "T03 running" header was corrected on archiving. (2) `implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` — T01, T02, T04–T07 complete, T03 replaced not executed. (3) `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md` — T01–T11 complete, CP-A–CP-D signed. **All 46 path citations into the three were swept and repaired the same pass**; bare-filename citations resolve unchanged, per the resolve-by-filename rule. `implemenation/` now holds only `previous/`. |
| | *(superseded 2026-08-21 by the row above; kept for the record)* 🟢 **TWO, deliberately and for the first time in this arc.** (1) **`implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md`** — authorised 2026-08-20, **Arc B (T05) COMPLETE and CP-4 signed**; Arc A: **CP-1 and CP-2 signed**, **T03 — the full 8,153-building census — running locally at 12 workers** ✅ **T03 FINISHED 2026-08-20 (evening): 8,153 rows, 8,153 unique `osm_id`, 8,151 `ok`, 2 EnergyPlus failures re-run solo. Wall clock 9,687 s for the final process-pool leg.** T04 + CP-3 to follow. (2) **`implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`** — authorised 2026-08-20 (afternoon) on the user's four rulings, **T01 in flight**. ⚠️ **The second exists precisely because every task in it is CPU-cheap and needs no EnergyPlus**, so it runs *beside* the saturated census rather than behind it. **Neither is archived until both close** — the "only one plan in `implemenation/`" rule is about archiving completed plans, not about forbidding two live ones. The six completed plans were archived to `implemenation/previous/` on 2026-08-20 and all **80** citations into them were swept and repaired the same pass (0 broken, all 35 cited targets verified to resolve). *(superseded 2026-08-21 by the row above)* |
| **Running on the cluster** | **nothing** |
| ⬛ **Overnight state, 2026-08-20 (evening)** | **THE OPEN-61 FLEET CENSUS IS FINISHED AND ITS NUMBER IS MEASURED** — the census closed at **8,160 rows, 8,160 unique `osm_id`** (8,152 `ok`, 7 never-simulated reason-rows, 1 EnergyPlus OOM crash), and **T04 + CP-3 returned the fleet figure: 19.4707 kWh/m² over n = 8,144**, director-re-derived to 6 decimals. **Ruling R6 is executed** — the 121.9 GB / 7,861-directory corpus is out of the scratchpad and under a checked inventory (OPEN-62 plan T07). **A third plan ran and closed the same night: `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md` (T01–T11)**, ten live items measured, **0 opened, 0 closed, no published number moved, no ruling taken.** Counts below are therefore unchanged. What changed is that **six items moved from "unmeasured" to "measured, awaiting your decision"** — see §4, part A. |

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

## 2. The live items — ~~**16**~~ ~~**12**~~ ~~**13**~~ **14** as of 2026-08-22 (this section was written 2026-08-20 at 19)

➕ **OPEN-63 was OPENED 2026-08-22** by the director while designing the OPEN-61 remedy — the carbon total does not follow the energy total. Its row is at the foot of this table and its section is in §6.

➕ **OPEN-64 was OPENED 2026-08-22** by the director, from a test failure — district heating that serves an end use **other than** Water Systems is dropped from every reported column, and the repository's own golden fixtures are exactly that shape. Row at the foot of this table, section in §6.

🔒 **FOUR ROWS BELOW ARE CLOSED as of 2026-08-21 on user ruling R3 — OPEN-09, OPEN-10, OPEN-14 and OPEN-18. Their closing notes are in §6 and each states what survives the closure and where it went.** The rows themselves are left as written so the change is visible — nothing here is deleted. ⚠️ **OPEN-18's closing note does not read like the other three: its question inverted under measurement (the population is reachable, n = 69) and the √S test itself is now available work with no home. Read it before assuming OPEN-18 is finished business.**

🔴 **AMENDED AGAIN 2026-08-21 by the second ten-item pass — see the 2026-08-21 entry in
§7 before quoting any row below.** Ten rows (OPEN-53, 17, 14, 35, 62, 38, 18, 19, 09, and
OPEN-56 by way of 38) now carry a measurement they did not have. **Still 16 live: nothing was closed,
nothing opened, no published number moved.**

🔴 **AMENDED A THIRD TIME 2026-08-21 (night) by `implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`** — see the **night-pass entry at the end of §7**. Ten items measured again against the *adopted run* (`evidence/open48_refleet4/`, **100 % `.eio`/`.err`/`.end`/IDF coverage**), which no earlier pass had read. Biggest changes: **OPEN-56 is fleet-wide** (91.64 % of zones carry `Volume == 10.00`; `WHOLE` zones 100 %, `CORE` zones 0 %), **OPEN-62 is a ~2.9× lever on the headline**, and **OPEN-17's largest hole has no source at all**. Still 16 live.

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
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | ✅ **C06: "cosmetic" tested and holds — 96.3% distribution overlap, small correctly-signed residual** (audited) 🔵 **2026-08-18 (overnight, X03): NOT downstream of OPEN-56.** The ten non-convergent-but-successful buildings show 150 warnings baseline and 150 treated, 15/15 unchanged on every one, while the same treatment clears the volume warning 70/70 → 0/70. **Two independent defects overlapping on the same 16 buildings.** X07: E-LA-17 resolves to exactly this population and would double-count if adopted. ✅ **INDEPENDENTLY REPRODUCED ON RUN 4 A SECOND TIME — 2026-08-20 (T03 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`), by a different executor, a different script and a different scan:** **16 / 8,160**, cell split **la_centre 2, la_rural 10, la_suburban 3, la_urban 1, all others 0** — identical to T13’s 2026-08-19 re-derivation, which was itself identical to run 2. ⚠️ **One correction to how this item is cited:** the signature is `Inside surface heat balance did not converge` (`scripts/analysis/open09_fleet_err_taxonomy.py:42`), **not `CheckWarmupConvergence`** — that string has **0 occurrences** in the auto corpus, and a task written against it would have measured nothing while appearing to measure this item. The executor caught that in the plan text and stopped rather than substituting silently. |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) — **capability confirmed real from the schema; remedy narrower than claimed** | Capability | ~~90 buildings (**carried, not re-derivable without a fleet pass**)~~ **C03: 90 reproduces exactly — but that is 4.6% of the 1,976 inexpressible fleet-wide** + future | ✅ **measured + verified** ✅ **2026-08-18 (overnight, X08): the "90 buildings" RE-DERIVED EXACTLY — 66 `MidriseApartment` + 24 `HighriseApartment` — by running the experiment N11 named and declined. And a denominator at last: 90 of 1,992 `fallback_not_expressible` = 4.5 %; the other 1,902 (95.5 %) are structurally beyond the edit. `applied` is only 497 of 7,442.** 🔵 **CEILING RESTATED on run-4 data 2026-08-19 at CP-3 (T16): 4.78 % (was ~~4.5 %~~), 96 of 2,007.** The evaluated population reproduced exactly (7,442) but the 90-building `MidriseApartment`/`HighriseApartment` split did **NOT** — **69/27 against the carried 66/24, self-reported as a finding rather than smoothed over**, and explained: run 4 carries OPEN-35's storey corrections, which this item's own X08 finding already placed upstream of exactly that classification boundary. All other archetype counts unchanged. Capability and narrowness both reconfirmed. |
| ~~OPEN-12~~ | ~~Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2%~~ **both re-derive at 100%; a third cell is at 100% and was never named**. **N15: genuinely a source-coverage gap — NOT a spillover from OPEN-14** | Data acquisition | **3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide** | ⚠️ **numbers do not reproduce**  🔒 **CLOSED 2026-08-20** — closes on measurement, not on repair: the third cell is `nyc_suburban`, the fleet counts are confirmed exactly, and the two irreproducible percentages are replaced. **What survives it:** the 2,806-of-8,160 source-coverage gap itself, which is OPEN-14's and OPEN-15's business, not a defect of this item. |
| ~~OPEN-13~~ | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc — ~~both live at HEAD~~ **E-UTCI-13 fixed 2026-08-12; E-UTCI-12 contained only** | Data / Stage 6 | ~~the whole test suite cannot be collected~~ **collectable again (1937 tests, exit 0) — but 43 passing tests traded away**; cached re-read no longer nulls `levels`/`use_class` | 🟡 **1 of 2 fixed**  🔒 **CLOSED 2026-08-20** — closes on refutation: nothing was ever deleted and all 43 tests run at HEAD (`43 passed, 10 skipped in 0.65s`). **What survives it:** the 10 tests that stay skipped, reassigned to **OPEN-17**, and the restated suite baseline **1,918 passed / 56 skipped**. |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout — **confirmed; no Overture slice is tracked for any affected cell** | Reproducibility | Stage 6 inputs; ~~converges with OPEN-12 on the same 4 cells~~ **N15: coincidence — separate item** | ✅ **measured** ✅ **2026-08-18 (overnight, X09): the step this item named as "the next thing" is TAKEN. Zero `FUSED` provenance tokens across all 8,160 buildings — including `nyc_centre`, the one cell that HAS a tracked slice. The missing slices are a real but NON-OPERATIVE blocker; the config gate closes first. The OPEN-12 convergence is a coincidence.** 🟢 **AND NOW THE OTHER HALF IS MEASURED — 2026-08-20 (T08 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`): if the gate were opened, the tier would fill 106 of 121 — 87.6 %.** With `FUSION_SOURCES_BY_TARGET` set to `{"height_m": ("overture",)}` **in a sandbox only** (`openubem/config.py` verified unmodified afterwards), the production router run over `nyc_centre` — the one cell with a tracked Overture slice — fills **106 of its 121 null `height_m` rows**, every one stamped `FUSED_OVERTURE_HIGH`. The 15 it does not fill are traced, not guessed: **14** match a footprint whose Overture record carries its own NaN height (`openubem/semantic/fusion.py:230-252`), **1** has no spatial match inside `NEAREST_TOLERANCE_M = 10.0` (`fusion.py:47`). 🔴 **So the machinery works and the blocker is entirely custody:** what stands between this project and a reproducible height backfill is one config default and eleven missing slices — not a broken tier. **This is a yield measurement, not a promotion** — nothing was enabled, no fleet input was regenerated, run 4 was not touched, and whether to open the gate is the user’s. Evidence: `extra/MEASUREMENT_open-14_fusion-yield.md`; `openubem/outputs/comparisons/open14_fusion_yield_nyc_centre_2026-08-20.csv`. |
| ~~OPEN-15~~ | ~~Imputation Phase E — documented-deferred, never executed — **no code path exists at all**~~ 🔒 **RETIRED 2026-08-20 into OPEN-17 on the user's ruling R2** (`implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §4). Not closed and not solved — **the fact is unchanged and is now carried by OPEN-17's row.** | Imputation | fleet inputs | ✅ **measured** — merged, not dropped |
| ~~OPEN-16~~ | ~~`ml` imputation tier built but permanently off — **never reachable from the production pipeline, only from the validation entry point**~~ 🔒 **RETIRED 2026-08-20 into OPEN-17 on the user's ruling R2** (same plan, §4). Not closed and not solved — **the fact is unchanged and is now carried by OPEN-17's row.** | Imputation | opt-in only | ✅ **measured** — merged, not dropped |
| OPEN-17 | 🔵 **CARRIER as of 2026-08-20 — this row now holds all three imputation facts, on the user's ruling R2.** They were one fact described three times: **the imputation tiers were built and never wired to the production router.** (a) *ex-OPEN-15* — Phase-E imputation is documented-deferred and **no code path exists at all**. (b) *ex-OPEN-16* — the `ml` tier is built but **reachable only from the validation entry point**, never from the production pipeline. (c) *its own* — 6 variance-preserving draw-tier imputers built, ~~off, awaiting a promotion decision~~ — 🔴 **not "off": the tier is unreachable; its router hook has never existed in any commit.** ⚠️ **Merging is a bookkeeping act, not progress** — nothing was measured, fixed or decided by it; the three facts and their evidence stand exactly as they did. | Imputation | ~~opt-in only~~ **the decision's cost was understated**; now the whole unwired-router surface in one row | ✅ **measured** (all three) ➕ **2026-08-20: inherits OPEN-13’s 10 residual skips** — 🔴 **restated 2026-08-21 (CP-1): the true figure is 15, not 10.** The 5 skips in `tests/test_debias.py` name OPEN-17 in their own skip reason (`config.IMPUTE_DEBIAS_NEWERSKEW` was never shipped) and were never counted against this item. **15 of the suite's 55 skips are OPEN-17's, and they are the ONLY skips in the suite that wait on a live decision** — see the CP-1 amendment at the end of §7 and the enumerated table in §9 of `implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`. The 10 originally inherited are in `tests/test_draw_methods.py` (`TestDrawTierRouting` 6, `TestNoEUILeakage` 1, `TestDrawTierDeterminism` 1, 2 of 6 in `TestDefaultByteIdentity`) — they unskip themselves the day the router hook exists. 🔵 **THE DECISION NOW HAS ITS CONTEXT — fleet tier census, 2026-08-20 (T09 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`, numbers re-derived by the director directly from run 4 rather than accepted): the imputation machinery covers ONE target out of seven.** Across all **8,160** buildings, the only imputer that fires in production is the vintage one, and it fills **5,913 of 5,913 missing `year_built` — 100 %**: `VINTAGE_NAN_PERMISSIVE_DEFAULT` **4,256**, `GROUPMODE_MED` **1,521**, `HOTDECK_NEIGHBOR_HIGH` **90**, `HOTDECK_NEIGHBOR_MED` **46**. **Every other target is filled by nothing at all** — `levels` 7,719 missing, `function_tag` 7,741, `postcode` 4,183, `building_tag` 4,105 generic, `height_m` 2,806 (OPEN-14/OPEN-12’s population), all carrying an acquisition token and no imputed value. ⚠️ **Two corrections to how this was nearly reported.** (a) The tokens are **not** in `01_buildings.gpkg` — its `provenance_*` columns hold acquisition states only (`OSM_OBSERVED`/`OSM_MISSING`/`OSM_GENERIC`) in runs 2, 3 and 4 alike; the imputation tokens live in `05_results.csv`’s `data_quality_flag`, so a census of the gpkg alone reads as “no tier ever fires”, which is false. (b) 🔴 **A small drift against the carried run-2 figures that nobody asked for:** run 2 recorded 4,255 / 1,519 / 90 / 46 and run 4 gives **4,256 / 1,521** / 90 / 46 — **+1 and +2 buildings**. Small, unexplained, and the same shape as the C04 leftover, so it is recorded rather than rounded away. ➕ **New at HEAD, worse than F7 predicted:** `openubem/results/impute_scatter.py` no longer even imports — `ImportError: cannot import name `recover_pairs` from `openubem.validation.mask_recover`` at `impute_scatter.py:63`, so it fails before reaching the unguarded `IMPUTE_DRAW_METHOD_BY_TARGET` read; `draw_leaderboard.py:174` still raises the predicted `AttributeError`. **The user’s decision is unchanged and untouched** — this is context for it, not a move on it. Evidence: `extra/MEASUREMENT_open-17_tier-census.md`; `openubem/outputs/comparisons/open17_tier_census_2026-08-20.csv`. |
| OPEN-18 | **Q3 — √S vertical-form distortion**, now confirmed unreachable by the mechanism built for it | Method | small buildings, cold cells | ✅ |
| OPEN-19 | LA runs ~+40% hot — Title 24 vs ASHRAE 90.1 — **not currently representable: no climate-zone or code-year switch exists; LA's HVAC comes from a Buffalo prototype** | Method | one whole city | ✅ **measured** |
| ~~OPEN-20~~ | Wider validation matrix beyond 3 cities × 4 rings | Method | external validity | 📄  🔒 **RETIRED 2026-08-20** — a scope question, not a defect: nothing broken, nothing blocked, nothing to measure, and tracked twice since 2026-06-17. Lives on in `docs/docs_TODO/wider_validation_matrix.md`. **ID retired, never to be reused.** |
| ~~OPEN-27~~ | ~~A DESIGN doc names an archetype that does not exist — **inside the coarse-metric definition**~~ 🔒 **CLOSED 2026-08-20.** Both lines now read `HighriseApartment`: `DESIGN_step-2…:529` and `PLAN_step-2.5-oq7-labelled-fixture.md:78`. Verified `grep -rn "MultifamilyHome" docs/docs_main/` → **0 occurrences**, and the archetype set re-derived from `openubem/data/openstudio_archetypes.json` → **exactly 2 Residential archetypes, `MidriseApartment` and `HighriseApartment`**, so the replacement was checked against the data rather than assumed. `pytest -k "multifamily or coarse"` **6 passed**. | Housekeeping → **spec integrity** | the accuracy metric's own definition | 🔒 **closed** |
| OPEN-35 | **Two fallbacks invent the missing storey count and disagree** — archetype chosen at group-median storeys, geometry built at 1. **2026-08-11: the mechanism is now proved by direct `.eio` evidence, not inferred.** The 2,611-building subpopulation matches its own broken `levels = 1.0` denominator almost exactly in `auto`/`building`/`floor` (**100% within ±1%, by construction** — those modes build zones from `levels`) and **breaks sharply under `layout_assign` (mean 2.3728, only 17.92% within ±1%)**, which assigns storeys from the archetype instead. **The two paths disagree, measured, on 40,800 runs.** **Still open** — the intended-fallback question is a DESIGN decision, not a measurement. ✅ **2026-08-19 (T04–T05): scope corrected 11 → **21** and the agreement fix landed.** The census was apartment-scoped; 10 `LargeHotel` buildings consume imputed levels through the identical mechanism, and the 11 are a **strict subset** of the 21 (set containment, not count). Naive 509-building variant **rejected**. Fix in `derive_num_floors()`, gated on the `GROUPMEDIAN_LEVELS_MED` token. 🔴 T04 landed it **inert** — no call site passed the new arguments — and said so; **T05 wired 2 of 3 and stopped at the parser with a quoted obstacle; T06 closed it — leaving 2-of-3 would have made the build and parse paths derive DIFFERENT floor counts for the same 21, recreating this very defect elsewhere.** ✅ All three paths now change the **identical 21 osm_ids** (0 missing / 0 extra, set membership, fleet-wide over 8,160 buildings), with a test pinning the three-way agreement. ⚠️ Baseline predates the fix and is stale w.r.t. 21 buildings; **no fleet re-run, no restatement.**| Simulation correctness | **2,611 / 8,160 = 32.00% of the fleet**; 1,031 of them given a mid/high-rise archetype and built at one storey | ✅ **mechanism verified + size measured + simulation-boundary proof 2026-08-11** 🔴 **2026-08-18 (overnight, X04): consequence measured for the first time, and the headline it produces MUST NOT be quoted. 2,611 / 32.00 % and 1,031 both re-derive exactly; the +47.9 % fleet EUI gap is composition (nyc_suburban is 1,589 of 2,611 with no comparison group) and WITHIN cells the direction is not even consistent — 4 lower, 4 higher. Needs an intervention, not a cross-section. 0 failures in 2,611.** |
| OPEN-38 | ~~**`layout_assign` subsurface geometry defect** — 7 tasks die on EnergyPlus **severe** *"Base surface does not surround subsurface"*, escalating to a two-space fatal~~ 🔴 **PREMISE FALSIFIED 2026-08-11 — item rewritten, still open.** That message is a **`** Warning **`**, not a Severe, at all **8** sites, and **kills nothing**. The item is now two measured defects: **(i)** all 7 `layout_assign` fatals die on **thermal runaway in zone `LAUNDRYROOMFLR1`** (−12,459 / −23,743 / −11,950 / −15,491 / −12,901 / −59,865 / +182,399 °C) — the substituted prototype's laundry room, same zone token as OPEN-06, and **no other cause appears in that mode**; **(ii)** **8** buildings carry malformed door geometry, of which `nyc_rural/way_965718401` **completes successfully and publishes results** from it. All 8 are `layout_assign`; **zero in the other four modes**, verified across all 40,800 `.err` files. 🔴 **2026-08-18 (T04): population re-derived at 7, confirmed; tested against OPEN-42 and found to be a different mechanism on every measured axis (message class, zone position by `.eio` geometry — bottommost storey vs. OPEN-42's topmost, geometry origin — substituted `SmallHotel` prototype, mode — `layout_assign`-only). Recommend keeping the two items separate; director to rule.** ✅ **Ruling 2026-08-18: recommendation ACCEPTED — the two items stay separate.** | Simulation correctness | (i) 7 fatals, one prototype zone; (ii) 8 buildings, 1 of them publishing | ✅ **both mechanisms measured; the register's stated cause was wrong**; ✅ **2026-08-18: tested against OPEN-42, confirmed distinct; director ruled — stay separate** 🟢 **MECHANISM FOUND 2026-08-19 at CP-3 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md` (T14) for defect (i), and it is a LOADS/no-HVAC interaction — not geometry, and not a wrong template.** `LaundryRoomFlr1` has **zero HVAC** in the DOE `SmallHotel` prototype — absent from all 54 `ZoneHVAC:EquipmentConnections` entries — while carrying the floor's largest absolute internal-gain density (**46,286.64 W** gas dryer plus water-heater ambient losses). An unconditioned zone with nothing to cap that load free-floats into a `CalcHeatBalanceInsideSurf` divergence during Sizing. ⚠️ **Geometry is explicitly CLEARED and this is NOT an OPEN-56 stub**: that zone's `.eio` volume is **378.63 m³**, positive and plausible. Disjoint-mode claim reproduced exactly across all 40,800 `.err` files: **0** hits in `auto`/`building`/`floor`/`fast_zone`, **8** in `layout_assign`. ✅ **THE ITEM'S OWN NAMED FIRST MEASUREMENT IS RUN — 2026-08-20 (T04 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`). The 43 nameless fatals now have names.** All **44 of 44** carry an identifiable `** Severe **` line before the generic trailer (`no_preceding_severe` = **0**), and **38 of 44 (86 %) are ONE family**: inside-surface heat-balance divergence — `Temperature (high) out of bounds` 21, `CalcHeatBalanceInsideSurf: The temperature of <N> C` 17, `Temperature (low) out of bounds` 5; the 44th is a non-convex shadowing severe. 🔴 **And the `la_rural` concentration resolves into an item we already have:** 11 `la_rural` stems fail in at least one of `fast_zone`/`auto`/`floor`, **6 of 11 in all three** — and **all 11 are `Warehouse`**, with 5 of the 6 mode-independent ones being EXACTLY run 4's five `la_rural` `not_simulated` buildings (`way/472960972`, `472961034`, `472961088`, `472961091`, `472961171`; director-verified against `open61_census_fleet.csv`). **The mode-independent half is OPEN-42/OPEN-56's `Warehouse` face, still fatal today — not a new input-validation item.** ⚠️ **The remaining 5 of 11 fail in only one or two modes and that half is NOT explained by the same mechanism** — the split is reported, not smoothed. 🔵 **Hypothesis recorded, explicitly NOT a finding and in tension with this row's own layout_assign evidence:** an OPEN-56 10 m³ volume stub would produce exactly this heat-balance divergence — but the `layout_assign` case above diverged with a healthy **378.63 m³** volume, so the stub is at most part of the story. **The cheap test (re-run a few of the 44 with `Zone.Volume` written) has not been run** and belongs to whoever scopes OPEN-56's remedy. No remedy authorised. |
| **OPEN-53** | 🔴 **874/875 E02 harvest directories are missing `.sql`/`.end`, concentrated in two Austin sub-cells.** Opened 2026-08-18, found as a byproduct of T03's `.eio` census run for OPEN-37. Against **40,800** `n_building_dirs` and **40,800** `.eio`/`.err` (both exact, zero empty), `.sql` = **39,926** and `.end` = **39,925** — short by 874/875. Every short directory still carries its `.eio` and `.err`, so this is **not** OPEN-37's problem — ~~it is an incomplete-simulation signature~~ **it is a batch-scoped harvest gap, not an incomplete-simulation signature (T02, 2026-08-18): 874/875 report `EnergyPlus Completed Successfully`, 0 fatal, indistinguishable from a 200-directory healthy control (100% completed).** **874 of 875 concentrate in `austin_suburban_fast_zone`/`austin_suburban_floor` (100% of both, all other modes for the same buildings fully populated); the remaining one is `nyc_centre_fast_zone`, truncated mid-input-processing.** ~~No `.err` content from these specific directories has been read yet.~~ | Reported numbers → **run completeness** | up to 875 E02 harvest directories, two Austin sub-cells + one NYC directory | ✅ **census counted, location established**; ✅ **T02 2026-08-18: `.err` read for all 875 + 200-directory control — genuine EnergyPlus failure retired (0 fatal); harvest-artifact vs IDF-output-config not distinguishable from this artifact; 1 exception (`nyc_centre_fast_zone`) not determinable from `.err`**; ✅ **Ruling 2026-08-18 (CP-1): original question ANSWERED — files were produced, harvested and inventoried 2026-08-11, then deleted by a process outside this repo at 2026-08-17 16:21, which also emptied the whole E02 IDF corpus; no published number affected. STAYS OPEN, narrowed to the custody risk — nothing prevents recurrence, and `e02_corpus_inventory.csv` (2026-08-11) is now falsified by disk for two rows and must be read as a snapshot, not current state.** ⚠️ **2026-08-18 (overnight, X06): custody exposure quantified — 152.4 GB across three corpora, 145 GB of it `.sql`, none yet carrying the 2026-08-17 16:21 sweep signature. Under 0.12 GB preserves every finding this arc cites; the 76 GB of `.sql` is the bait and is re-derivable. And "E02 is gone" is too strong — its parquet manifests survived.** 🟢 **ANSWERED 2026-08-20 (T05 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`, on the user’s grant of Speed resources): THE 874 FILES ARE STILL ON THE CLUSTER. This is a HARVEST defect, not a simulation-side loss, and no re-simulation is owed.** Remote read-only inventory of `/speed-scratch/o_iseri/fleets/e02_{cell}_{mode}/out/{stem}` (root found at `scripts/analysis/e02_cluster_readonly_audit.py:35`, login-node `find`/`wc` only) returns `austin_suburban_fast_zone` **437 `.sql` / 437 `.end`** and `austin_suburban_floor` **437 / 437** — **874 + 874, matching the local shortfall exactly, cell for cell.** The two short sub-cells are the two the item named. ⚠️ **But re-fetching would buy less than it looks:** 20 sampled files were `scp`-ed back and all 20 parse through production `parse_building()` **without an exception and without a usable number** — `parse_status="failed_zone_mismatch"`, `"zone count mismatch: found 0, manifest says 1"`, because these `.sql` files carry **no zone-level report variables at all** (meter-only output for that batch). So the custody question is settled and a **second, separate question is opened by the answer**: whether a meter-only `.sql` is worth harvesting, and why that batch was written meter-only when the rest of the fleet was not. **No re-fetch of the 874 was run — 20 samples only, by design, and the remedy is the user’s.** Evidence: `extra/MEASUREMENT_open-53_remote-inventory.md`; `openubem/outputs/comparisons/open53_remote_inventory_2026-08-20.csv` and `_parse.csv`. |
| **OPEN-56** | 🔴 **Every building in the fleet simulates with its zone air volume replaced by a 10 m³ stub.** EnergyPlus computes a **negative** volume from the geometry we hand it (`Indicated Zone Volume <= 0.0`, floors and ceilings wound the wrong way) and substitutes 10 m³. Opened 2026-08-18 (late) while looking for OPEN-42's mechanism. **8 160 / 8 160 = 100.00 %** of run 2, re-confirmed in run 3; **control: 0 / 2 on DOE-prototype geometry**, so it is our geometry, not EnergyPlus. OPEN-42's six failures are its extreme tail — failures average **−6 096 m³** computed volume against **−683 m³** for successes. ⚠️ **No claim is made that the published 157.1 is wrong**: infiltration is written `Flow/ExteriorWallArea`, not air-changes-per-hour, so it is not scaled by the stub, and the effect on annual EUI is **unmeasured**. | Simulation correctness | **all 8,160 buildings** | 🔵 **mechanism measured;** ~~writer not yet localised~~ ✅ **WRITER LOCALISED — tag corrected 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`** (this tag was already stale against this item's own §-section, and a task written from it found its premise false; see §1's CP-1 amendment). The winding is written by `geomeppy==0.12.2` and **its own corrector `set_entry_direction` is a provable NO-OP for our GGR convention** — `is_clockwise` is self-referential, testing against a point built from the same normal, so it returns `False` unconditionally and never inverts either winding. **Verified twice by the director independently of the executor**, by inspection and by execution on a CW- and a CCW-wound square. The IDF winding is therefore the **input footprint's own orientation**, and the one `orient()` call that exists (`openubem/idf/builder.py:464-465`) is gated `if resolution_mode != "auto"`, so it **never fires for the adopted baseline mode**; 0/20 sampled source footprints are CCW, matching the 100 % rate. **A THIRD remedy shape now exists: extend `orient()` to `auto` (sign unverified), alongside writing `Zone.Volume`. Neither applied — the remedy ruling is still owed to the user.** 8,160/8,160 (100.00 %) re-confirmed on run 4. ✅ **2026-08-18 (overnight, X01/X02): THE FLEET-SCALE COST IS MEASURED — 69 buildings, all twelve cells, control whole (70/70 baseline volume warning → 0/70 treated, 70/70 completed both arms). Mean +0.98 %, median +0.84 %, 65/69 same direction. The per-zone model is REFUTED (corr 0.113); it is a fixed per-BUILDING offset of ≈ +1.0 kWh/m². 157.1 deliberately NOT restated. ~~New lead: on 1 of 60 the treatment also moved the reported floor AREA by 4.18×.~~ 🔴 **RETRACTED 2026-08-19 (CP-1, T05): a FALSE LEAD.** Untouched production run-4 data gives `relation_3566904` `footprint_area_m2 = 2,682.23`, `levels = 14`, `floor_area_m2 = 37,551.22` — ratio **1.000001**, no anomaly at all. The 157,115 m² belongs to a different building, `relation/11171793`, and reached this experiment through **OPEN-58's `run_ep()` shared-cwd cross-contamination** — an independent second confirmation of OPEN-58's verdict from data that never touched the defective helper. Remedy still unauthorised.** ✅ **RE-DERIVED ON THE ADOPTED RUN — 2026-08-20 (T03 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`). The 100 % was a run-2 number until tonight.** A full `.err` census of run 4 — **8,160 / 8,160 files, no short cell** — finds `Indicated Zone Volume <= 0.0` in **8,160 / 8,160 = 100.0000 %**. The rate is not a sampling artifact and it is not stale: it is the adopted baseline’s own corpus. The same census counts **26 / 8,160** buildings carrying a `** Severe **` line and **7 / 8,160** carrying a two-space `**  Fatal  **`, and the 7 reconcile **exactly** with run 4’s 7 non-`success` rows. Artifacts: `openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv`; `extra/MEASUREMENT_open-56-09_run4-err-census.md`. |
| **OPEN-58** | 🔴 **`open56_zone_volume_experiment.py`'s `run_ep()` helper has two defects, and any earlier local batch result that imported it is exposed to both.** Opened 2026-08-19 by the director; found by **T04's own controls**, not by a task that went looking. (a) EnergyPlus `-x` lets outputs **cross-contaminate between buildings that share a working directory** — caught as two byte-identical `.sql` files for two different footprints. (b) It reads EUI by a formula that **does not match production's `total_eui_kwh_m2`** (`openubem/results/parser.py`), which sums per-end-use EUIs over a multiplier-aware `.eio` area rather than dividing Total Site Energy by Total Building Area. ✅ **T04 voided its own first full run and re-ran clean rather than patching the numbers** — its published `_results_v2.csv` is unaffected. ⚠️ **Explicitly NOT scoped to OPEN-35**, whose amendment records it: the question is which *other* results imported this helper. ~~**No audit of the blast radius has been done.**~~ **— stale tag, struck 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`; the audit is recorded later in this very row and in this item's §-section, and a task written from this sentence found its premise false at HEAD.** ✅ **Re-derived independently at CP-1 by a disk walk** (correctly chosen: the origin file and its real importers are **untracked**, and a tracked-files-only `git grep` was tested first and found only 5 of the 8 files) — **exactly reproduces the existing count: 3 real importers, 4 name-collisions, 1 origin, 8 total.** ✅ **BLAST RADIUS MEASURED 2026-08-19 (T06–T08): 3 real importers, 6 descended artifacts, 1 unsound row, 0 unverifiable.** 🔴 **This item's own stated mechanism was wrong:** defect (a) is **not** a shared `-d` outdir — every importer already passes a unique one — it is EnergyPlus's `-x` step working relative to the **shared process cwd**, so all three importers are exposed and **concurrency is not the discriminator**. One confirmed contamination in 166 recomputed cells (`nyc_centre/relation_3566904` carrying `relation_11171793`'s results — identical to **fifteen significant figures**); already excluded from the pooled statistic, but for a **wrong stated reason**. ✅ **Zero cited figures corrupted** — defect (b) shifts absolute EUI up to −24 % but every cited number is a **relative** change on the same building, which cancels. Still open; **no remedy authorised**. ✅ **RECORD REPAIRED 2026-08-20 (director, T06 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`) — the four corrections the blast-radius measurement recommended and did not take are now applied:** (a) the mechanism language is corrected from “shared outdir / shared working directory” to **shared process cwd** — the wrong phrasing had cleared the two serial importers, and **all three are exposed**; (b) the stated reason for excluding `nyc_centre/relation_3566904` is corrected from “geometry mis-reports area” to **cross-contamination** (its base arm’s zone keys read `RELATION/11171793_F0_WHOLE` and its three base-arm values are exact duplicates of `relation_11171793`’s, to the last decimal); (c) the raw artifact now warns for itself — `open56_fleet_cost_stratified.csv` gained a `data_quality_note` column marking that row **do not cite**; (d) **the remedy decision is the user’s and remains un-taken.** No published figure moved.| Simulation correctness → reported numbers | **3 importers, 6 descended artifacts, 1 unsound row, 0 unverifiable** (measured 2026-08-19; “unknown” is retired) | 🔵 **both defects reproduced and understood; blast radius MEASURED; record repaired 2026-08-20.** No remedy authorised — the choice is the user’s. |
| **OPEN-59** | 🔵 **REFRAMED 2026-08-19 (late, director) — this is a CALIBRATION item, not a bounds defect. Hypothesis 1 is REFUTED by direct measurement:** T02 of `implemenation/previous/PLAN_gap-decomposition-2026-08-19.md` screened **all four** drawn PDE columns for **all 290** `OpenUBEMUnknown` buildings against their donor bounds — **0 of 4 columns, 0 of 290 buildings, out of bounds**, worst excursion **0.0** on every column (`openubem/outputs/comparisons/open59_pde_bounds_screen.csv`). **This is NOT OPEN-55's sibling** — the draws are all legal, so no column-wise screen can fix it. **Hypothesis 2 stands by elimination:** the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, which makes the remedy a **different donor pool or better classification**, not a bounds fix. **Kept open under its own ID rather than closed** — the phenomenon is real and unexplained; only its diagnosis changed. ~~🔴 **With the Unknown equipment defect cured, Unknown buildings still use ~~1.7×~~ more than classified buildings — the gap moved from equipment to hot water and heating.** ⚠️ **The `1.7×` is a MEDIAN-PER-BUILDING statistic measured on `nyc_suburban` alone, and this row must carry both weightings — corrected 2026-08-19 at CP-1 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`, measured fleet-wide on run 4.** **Floor-area-POOLED: Unknown 107.22 vs classified 155.56 — Unknown is 31 % BELOW.** **MEDIAN-PER-BUILDING: Unknown 309.95 vs classified 134.08 — Unknown is 2.31× ABOVE.** 🔵 **Both are real and they disagree for a traced reason, not an error:** the top 10 of 650 Unknown buildings hold **72.5 %** of all Unknown floor area and run at moderate EUI (r = **−0.27** between Unknown floor area and EUI), so area-weighting is dominated by a few large moderate buildings while the *typical* Unknown building is small and hot. **Never quote one without naming its weighting.** Fleet-wide the largest end-use multiple is **DHW at 10.2×**, ahead of heating (3.4×); `nyc_suburban`'s lighting **6.7× does NOT generalise — it is 1.00× fleet-wide.** Fleet Unknown population: **650 buildings, 3.7 % of fleet floor area.** Opened 2026-08-19 by the **director's audit of OPEN-55's passing acceptance test**, not by a task that went looking for it — the test asked only whether divergences fell, and they did. 🟢 **The OPEN-55 screen is confirmed to have worked, and this item does not reopen it:** Unknown equipment demand is now *below* classified (median **37.5 vs 43.4 kWh/m²**). 🔴 **But total demand did not follow.** `nyc_suburban`, 290 Unknown vs 1,299 classified, medians: **total 349.4 vs 202.8 kWh/m² (+146.6, 1.72×)**, DHW **103.5 vs 42.5 (+61.0)**, heating **140.1 vs 99.0 (+41.1)**, lighting **26.7 vs 4.0 (+22.7)**, cooling **25.0 vs 4.5 (+20.5)**. The lighting and cooling ratios (6.7× and 5.6×) are the largest multiples and are the natural first place to look. ❓ **Cause not diagnosed and no remedy proposed** — it is not yet established whether the Unknown donor pool is genuinely higher-intensity than the buildings it stands in for, or whether the same widened-bounds pattern OPEN-55 found in the equipment column also affects the DHW, lighting and occupancy columns, which would make this OPEN-55's sibling rather than a new phenomenon.~~ | Reported numbers | **every `OpenUBEMUnknown` building in every cell** — 18.3 % of `nyc_suburban`; fleet-wide share and fleet EUI effect **not yet measured**, commissioned as part of T04 | 🔵 **measured on one cell; cause unknown; fleet effect unmeasured** |
| **OPEN-60** | 🔴 **`total_eui_kwh_m2` undercounts Interior Lighting and Interior Equipment whenever a zone carries a multiplier > 1 — every `layout_assign` EUI this project has ever recorded is too low.** Opened 2026-08-19 by the **director**, on a reconciliation control run by T01 of `implemenation/previous/PLAN_gap-decomposition-2026-08-19.md` — **not by a task that went looking for it.** **Mechanism, traced and not inferred:** those two end uses are summed from per-zone hourly variables, which EnergyPlus does **not** scale by the zone multiplier, while the floor-area divisor **is** multiplier-aware (`openubem/results/parser.py:431-433`, `resolve_simulated_floor_area()`). Every other end use — cooling, heating, fans, pumps, hot water — matches the multiplier-correct ABUPS table to **<0.01 %**. **Size, n=48 untrimmed `layout_assign` buildings:** only **6 of 48** reconcile within 2 %; error median **4.71 %**, mean 17.56 %, p90 24.19 %, **max 192.28 %**; **14 exceed 10 %**. 🟢 **No adopted number is affected, and this was verified rather than assumed:** zone multipliers are written in exactly one module (`openubem/geometry/layout_assigner.py`, `match_storeys()`, `:649`), which the `auto` production path never calls, and three run-4 `auto` fleet IDFs were read directly — **every `Multiplier` field is 1**. **153.8231 kWh/m² pooled over 8,153 buildings is untouched.** 🔴 **The gate that catches this already exists and the fleet pipeline never calls it** — `check_building_integrity()` (`parser.py:602-646`) returns `abups_ok=False` for the worst offender, and is called by `scripts/run_r1_t12.py:211`, `run_r3_fleet.py:313`, `run_r3_step5.py:204`, `run_t12_boston.py:198`, but **not** by the path that produced `05_results.csv`. ❓ **Remedy not proposed and not authorised** — two shapes exist (sum the two end uses from ABUPS as the other five already are, or make the per-zone sum multiplier-aware) and choosing between them is feature code, which this session does not write. | Reported numbers | **every `layout_assign` EUI ever recorded**, including OPEN-03's and OPEN-18's published sample figures, which were corrected 2026-08-19 the same night; **zero adopted rows** | 🔴 **mechanism traced, size measured on n=48, blast radius bounded to a non-production mode.** ✅ **THE BOUND IS NOW A CENSUS, NOT A SAMPLE — 2026-08-20 (T02 of `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`).** The claim that the adopted **153.8 kWh/m² pooled over 8,153** is untouched rested on the director reading **three** run-4 IDFs. All **8,160** were parsed: **0 files and 0 objects carry a `Multiplier` ≠ 1**, and **no `ZONEGROUP` object exists anywhere in the run-4 corpus**. The bound holds at the artifact, fleet-wide. (Field indices verified against a real object rather than assumed: the `ZONE` object's Multiplier field, evidenced at `open48_refleet4/austin_centre/fleet_staging/idfs/relation_13781131.idf:379` reading `1,  !- Multiplier`.) ⚠️ The positive control C6 could **not** be run — no `layout_assign` IDF survives on local disk — so the parser is proven to find a multiplier only on a prototype file, not on the mode that writes them. Artifact: `openubem/outputs/comparisons/open60_fleet_multiplier_census_2026-08-20.csv` (header-only, by design). 🔴 **AND THE THIRD QUESTION — “should the fleet pipeline call `check_building_integrity()` at all?” — IS ANSWERED WITH A NUMBER, AND THE ANSWER IS NOT A SIMPLE YES (T01, 2026-08-20).** The gate was run for the first time at fleet scale, over **7,860** `.sql` files of the fresh OPEN-61 census corpus, using production’s own function. Its three sub-gates behave completely differently and only one is usable. **(i) `abups_ok` — usable and quiet: 7,857 True / 2 False / 1 None, a 0.025 % fire rate**, against the 48-building `layout_assign` sample’s **42 of 48 (87.5 %)** — the expected direction, since the fleet is `auto` and carries no multipliers (T02). The two failures are `la_rural` 1/141 and `la_centre` 1/221 (`SecondarySchool` 1/11, `Warehouse` 1/32). **(ii) 🔴 `meter_ok` — MIS-SPECIFIED; wiring it as-is would flag 99.9 % of the fleet: 7,853 False / 6 True.** Director-diagnosed at the source rather than filed as a rate: it compares **zone lights + electric equipment** (`openubem/results/parser.py:658-665`) against **`Electricity:Facility`** (`:650-655`) — a subset against the total. Measured on `austin_centre/relation/13781131`, zone lights+equipment is **47.0 %** of facility electricity; the remainder is cooling, fans, pumps and electric DHW. **It can only pass for a building with no other electric end use.** ⚠️ **And its 6 “passes” are the degenerate branch, not healthy buildings:** all six have `Electricity:Facility` = **0** and zone electricity = **0**, so True comes from the `facility_j > 0` else-branch (`parser.py:667-671`). **A gate that reads True only when the simulation produced nothing is inverted in practice.** **(iii) `gas_zero` — informational by its own comment** (`parser.py:681`): 40 True / 7,819 False, the expected shape for gas-heat archetypes. ✅ **So “wire the existing gate” is not one decision but three, and the cheap safe one is `abups_ok` alone. No remedy is taken here — the choice is the user’s.** ➕ **Two side-findings from the same run, neither asked for.** (a) **6 census buildings produced `.sql` files with no zone-level data at all** — `parsed_parse_status = failed_zone_mismatch`, every EUI null, while run 4 records 389–873 kWh/m² for them (5 `LargeHotel` + 1 `FullServiceRestaurant`, all `nyc_centre`). **Same signature as OPEN-53’s meter-only `.sql`, appearing here in a LOCAL rebuild** — so that failure mode is not a cluster artifact. (b) The census work tree holds **7,861 building directories against 8,151 census rows — 290 short**, across all twelve cells, because the early thread-pool driver deleted each work directory on success. 🔴 **This bears directly on ruling R6:** the corpus being preserved is **96.4 % of the fleet, not 100 %**, and T07 of the OPEN-62 plan must record it as such. Evidence: `extra/MEASUREMENT_open-60_fleet-integrity-gate.md`; `openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv`. |
elation_13781131.idf:379`.) ⚠️ The positive control C6 could **not** be run — no `layout_assign` IDF survives on local disk — so the parser is proven to find a multiplier only on a prototype file, not on the mode that writes them. Artifact: `openubem/outputs/comparisons/open60_fleet_multiplier_census_2026-08-20.csv` (header-only, by design). |
| **OPEN-61** | 🔴 **`total_eui_kwh_m2` drops the District Heating component of Water Systems.** Opened 2026-08-20 by the **director**, on a reconciliation control run by T01 of `implemenation/previous/PLAN_four-board-items-2026-08-20.md` — the third pass in a row where the defect came from an executor auditing its own arithmetic and **no plan asked for that control.** **Mechanism, verified at the `.sql` and not inferred:** `METER_QUERY` (`openubem/results/parser.py:48-54`) enumerates meters by name and contains `WaterSystems:NaturalGas` and `WaterSystems:Electricity` and **no `DistrictHeating` meter of any kind**; `dhw_eui_kwh_m2` is built from exactly those two names (`parser.py:469`), so district-heated DHW energy is dropped before `total_eui_kwh_m2` is formed. Director control on `way_1008727470`: ABUPS District Heating **0.72 GJ** against **59.22 GJ** total end uses = **1.22 %** unreported; T01 measured **1.03–1.10 %** on four buildings by the same route. 🔴 **Not a one-line fix** — adding the name to `METER_QUERY` changes nothing, because the `.sql` carries no `DistrictHeating` Run Period meter at all; the value survives only in the ABUPS tabular table. Any remedy must either request the meter in the IDF (changing what every future run emits, leaving every existing `.sql` unfixable) or read ABUPS as a second differently-shaped source of truth inside the parser. **Both are design decisions and neither is taken.** ⚠️ **The fleet `.sql` corpus that would have sized this was deleted 2026-08-20** under W9's prune (see OPEN-53) — sizing it now needs a **re-simulation, not a re-read**, and that cost is recorded here rather than discovered later. Same class as **OPEN-60**: two independent omissions in one formula found four days apart, which is the argument for a reconciliation control **inside** `parse_building()`. ✅ **SIZED AT FLEET SCALE — 2026-08-20 night, T03 + T04 of `implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md`, CP-3 signed.** The corpus this row said would need "a re-simulation, not a re-read" was re-simulated: **8,160 buildings, one row each, 8,152 `ok`**, artifact `openubem/outputs/comparisons/open61_census_fleet.csv`. **THE NUMBER: 19.4707 kWh/m², pooled over n = 8,144** (Σ 470,831,194 kWh ÷ Σ 24,181,536 m²), re-derived by the director straight from the CSV to 6 decimals, **12.7 % of pooled site energy**. Insensitive to the floor-area column (**+0.0007 %** on `recorded` vs `parsed`) and to both known anomalies (**< 0.002 kWh/m²** each). 🔴 **The estimate that this replaces was biased low by construction, and saying "inside the 8.7–20.2 band" hides it.** The per-building **median** dh÷dhw ratio is **0.6503** but the **pooled** ratio is **0.9382 — 44 % higher**, because large buildings carry far more DH per unit of DHW. Re-running F5's own method against the fleet's measured pooled DHW of 20.75 kWh/m² tops out at **17.43**, so the measurement sits **11.7 % above what that method could have produced anywhere in its IQR**. **The sampling was fine; the median-ratio-applied-pooled step was not.** ⚠️ **A pre-registered control was answered wrongly by the executor and reversed by the director:** C6 was computed as DH ÷ *total site energy* and returned "NOT REPRESENTATIVE, ~50× off", with a false claim that the denominator matched the pilot's. The pre-registered ratio is **dh ÷ dhw_eui** (plan §5 fact F5). Corrected: fleet median **0.6503**, IQR **0.3117–0.8642** against the 60-building pilot's 0.714 / 0.362–0.840 and the 200-building pilot's 0.644 / 0.310–0.935 — **the small sample WAS representative.** Report §C6 and the script were both rewritten. 🔴 **AND THE TERM IS NOT A FLEET-WIDE OFFSET — this is the finding that constrains any remedy.** `SuperTallBuilding` (n=24, 36.01 kWh/m²) and `TallBuilding` (n=92, 38.27) are **116 buildings = 1.4 % of the population carrying 70.5 % of the fleet's district heating**; four archetypes carry **91.8 %**; every office/retail/shop archetype sits at **1.3–2.7 kWh/m²**, i.e. near zero. Applying 19.47 as a flat offset would move energy onto ~5,000 buildings that do not have it. **No corrected fleet EUI was produced and none is proposed — the plan forbids it and the concentration result means the remedy is a design question, carried to the user.** Evidence: `extra/MEASUREMENT_open-61_fleet-dh-number.md`; `scripts/analysis/open61_fleet_dh_number_2026-08-20.py`. | Reported numbers | **MEASURED: 19.4707 kWh/m² over 8,144 = 12.7 % of pooled site energy.** `153.8231 kWh/m²` over 8,153 stands unchanged and is low by that amount — **but concentrated, not uniform.** OPEN-03's **−23.61 %** paired result is sound — the omission is common-mode in both arms | 🔴 **mechanism traced at the `.sql`; size now measured fleet-wide on n=8,144; remedy is a design question, unproposed** |

| OPEN-62 | 🔴 **Storey counts read from a baseline IDF omit each zone's own `Z_Origin` under Relative coordinates.** Opened 2026-08-20 **on the user's grant**, on the director's CP-4 recommendation; found by the T05 executor while building the fleet storey census and registered `[OPEN]` in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 rather than silently fixed — the correct handling, since fixing it would have changed what control C9 had to reproduce. **Mechanism:** the wall-vertex method takes each zone's minimum wall Z and never adds the `ZONE` object's own `Z_Origin`, so any archetype that encodes a repeated floor band's elevation in `Z_Origin` while its wall vertices stay local (near Z=0) collapses to 1–3 storeys regardless of true floor count. **Measured zone-by-zone across all 18 baseline-mapped archetypes, not assumed:** severe in **MidriseApartment** (18/27 zones), **HighriseApartment** (18/27), **TallBuilding** (145/164), **SuperTallBuilding** (232/256), **Outpatient** (59/118), **SecondarySchool** (21/46) — **6 archetypes, 2,983 of 8,160 buildings (36.6 %)**; immaterial in `LargeOffice` and the two restaurant archetypes (the nonzero-`Z_Origin` zones are not floor-area-counting); absent in the remaining 10. ✅ **Director-checked: it does NOT drive OPEN-03's headline** — splitting the fleet on the flag gives 60.8 % disagreement on 5,177 clean rows against 59.2 % on 2,983 at-risk rows. What it does bound is the *per-archetype magnitude*, not the fleet-wide rate. 🟢 **Scope established the same day and it is narrow (director, at the source):** production code does **not** share the omission — `layout_assigner.py:471` + `:491-493` and `viz/geometry_extract.py:143-155` both add `Z_Origin` back before taking the minimum, and no third production reader exists. The gap is confined to **one analysis parser** (`open03_envelope_decomposition_2026-08-20.py::parse_idf`) and the single script that imports it. **This is a measurement-instrument erratum, not a geometry defect** — no building is built at the wrong height.  🔴 **SCOPE ENLARGED 2026-08-20 at CP-2 of `implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` — the `Z_Origin` fix is IN and CORRECT, and the item did NOT close, because the restated control C9b FAILED and the failure is the finding.** C9b checked the corrected parser against `layout_assigner.py`'s own origin-aware reader — a reader that never imported `parse_idf()`. **Agreement 12 of 18 archetypes; 6 disagree over 3,734 buildings** (`TallBuilding` 11 v 20, `SuperTallBuilding` 16 v 30, `Warehouse` 2 v 1, and 1 v 2 on `FullServiceRestaurant`/`QuickServiceRestaurant`/`SmallOffice`). **Mechanism traced by the director, not accepted as a bare disagreement** — on `TallBuilding.idf`: floor surfaces give **20** distinct elevations, all wall bases **20**, exterior wall bases **19**, and *exterior wall bases in floor-area-counting zones* — which is what `parse_idf()` actually counts — give **10**. The elevations found (`0.0, 4.9, 23.8, 55.3, 72.8, 88.6, 104.4, 118.4, 132.4, 135.9`) are the levels where a **new exterior wall starts**; a curtain wall spanning several floors contributes one elevation, not several. 🔴 **`storey_count` is therefore not a storey count** — it is the number of distinct exterior-wall base elevations in floor-area zones, equal to the storey count only when every floor starts its own facade. The `Z_Origin` fix was **necessary and not sufficient**: it removed one error from a quantity that was measuring the wrong thing. ⚠️ **The old C9 passed 96/96 and would have passed again after the fix**, closing this item today with the column recorded as correct while undercounting `TallBuilding` by 9 storeys of 20. **Ruling R1 — restate the control rather than keep it — is the only reason this was caught, and it was caught by the control failing.** ✅ **Still no production code implicated:** the reader that gives 20 IS `layout_assigner.py`'s. ✅ **OPEN-03's 30/70 headline is untouched** (it rests on `compute_band_map()`, already origin-aware). ~~🔴 **C13's restatement is a LOWER BOUND, not a value:** built mean 1.21 → **≥ 2.25**, built max 6 → **≥ 16**~~ — **WITHDRAWN BY ITS AUTHOR AT CP-3, 2026-08-20.** 🔴 **SCOPE ENLARGED A THIRD TIME at CP-3** (`implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` §CP-3). T06 added a floor-surface reader on ruling R7 and its own allowed-to-fail control **C16 failed: 38 rows, all `Warehouse`, floor 1 < wall 2.** Mechanism measured by the director on the preserved prototype: exterior wall z-bases `{0.0: 8 walls, 4.267: 2 walls}` against **3 FLOOR surfaces all at z = 0.0** — a single-storey high-bay facade split into two vertical wall bands. **So `storey_count` under-counts `TallBuilding` (20→11) and `SuperTallBuilding` (30→16) and OVER-counts `Warehouse` (1→2): it is not a bound in either direction.** C13's 2.25 / 16 survive only because `floor < wall` occurs **0 times** inside the 5,714-row unmatched subset — an accident of archetype mix, not a property of the method. 🔴 **And the replacement reader is biased too: `storey_count_floor` counts an ATTIC as a storey.** Verified origin-corrected on the prototypes — `SmallOffice.idf` z = 3.05 carries **9 floor surfaces, all in zone `Attic`**; both restaurant archetypes carry zone `attic` at z = 3.049. All three are one-storey prototypes read as 2, and they are **3,580 buildings (43.9 % of the fleet)** and **2,797 of the 5,714 unmatched rows (48.9 %)**. Attic-corrected the built mean is **2.45**, not the 2.94 T06 reported. **The publishable statement is the range 2.45 – 2.94.** ⚠️ **C14's 18/18 agreement with `compute_band_map()`'s `n_proto` does not certify a storey count** — `n_proto` is documented in production as *“deliberately left as the measured Z-BAND COUNT, never a represented-storey count”* (`openubem/geometry/layout_assigner.py:404-406`). ✅ **Still not a production defect:** production branches `match_storeys()` on `n_proto` and never publishes it as storeys. 🔴 **Net finding, and the item's current scope: no reader in this codebase returns a storey count** — the naive reader collapses `Relative` files to 1, the wall-base reader is unbounded in both directions, the floor-surface reader counts attics. What a storey IS for a prototype with an attic, a plenum or a high bay is a **definition question that has never been answered in this project**, and it is not an executor's to answer. ⚠️ **Do not “fix” this by excluding zones named `Attic`** — zone-name matching is the generalisation A1 already falsified (F-07, `layout_assigner.py:389`) and would move archetypes across `match_storeys()`'s `n_proto` branches. | Measurement instruments only | **6 archetypes / 2,983 buildings (36.6 %) flagged**; separately, **3,734 buildings** carry a wall-base storey count wrong in an unknown direction, and **3,580 (43.9 %)** carry a floor-surface count inflated by one attic. No published number depends on either | 🔴 **`Z_Origin` FIXED and verified 8,160/8,160. Open, enlarged TWICE (CP-2, CP-3). R7 answered “derive it from floor surfaces” and that reader was built and measured — it is right on `TallBuilding`/`Warehouse` and wrong on 43.9 % of the fleet, because it counts attics. What is now owed is not another reader but a DEFINITION of a storey for prototypes with attics, plenums and high bays.** |
| **OPEN-63** | 🔴 **`gwp_total_kgco2_m2` excludes district heating entirely, and no district-heating emission factor exists anywhere in the codebase.** Opened 2026-08-22 by the **director**, while designing the OPEN-61 remedy — not by a task that went looking for it, and **the fifth consecutive defect found by auditing arithmetic rather than by testing behaviour.** **Mechanism, read at the source and not inferred:** `openubem/results/carbon.py:106` builds `gwp_dhw = dhw_gas_eui * f_gas + dhw_elec_eui * f_elec` — from the two *fuel* columns only, **never from `dhw_eui_kwh_m2`** — and `openubem/config.py:83` defines exactly one factor, `GWP_NATURAL_GAS_KGCO2_KWH = 0.181`. There is no district-heating factor to apply and none is invented here. **Size:** the energy this misses is OPEN-61's measured **19.4707 kWh/m² over n = 8,144 = 12.78 % of pooled site energy**. ⚠️ **The gap is PRE-EXISTING, not caused by the OPEN-61 fix** — carbon has been missing this energy for as long as district heating has been simulated. What the fix changes is that the two totals become **visibly** inconsistent: `total_eui_kwh_m2` rises by 12.78 % and `gwp_total_kgco2_m2` does not move. ❓ **Remedy not proposed and not authorised** — choosing a district-heating carbon factor is a literature decision, not a coding one, and this session does not invent values. The shape of the question, at least: a single national factor, a per-state factor like electricity already has (`get_elec_factor(state)`), or an explicit refusal to report carbon for district-heated buildings at all. | Reported carbon, **not** reported energy | every `gwp_*_kgco2_m2` column ever produced for a district-heated building; **zero energy figures**, and **153.8231 kWh/m² over 8,153 is untouched** | 🔴 **mechanism traced at `carbon.py:106`; size known exactly because OPEN-61 already measured it; remedy is a literature question, unproposed** |
| **OPEN-64** | 🔴 **District heating that serves an end use other than Water Systems is dropped from `total_eui_kwh_m2` and from every end-use column — and the repository's own golden fixtures are precisely that shape.** Opened 2026-08-22 by the **director**, **from a test failure rather than from an audit** — the first defect of this arc found by the suite, and the counterexample to OPEN-61's F3. **Mechanism.** The ABUPS `End Uses` table carries a `District Heating` **column** broken down over 14 end-use **rows**. The parser (OPEN-61 T01b) reads exactly one of them, `Water Systems`, and folds it into `dhw_eui_kwh_m2`. **The other 13 rows are read by nothing.** **Evidence that this is not hypothetical:** `tests/fixtures/golden_sql/r1_single_zone.sql` → `Heating` **148.24 GJ**, `Water Systems` **0.00 GJ**; `r2_one_zone_per_floor.sql` → **709.99 GJ**; `r6_perimeter_core.sql` → **1,646.86 GJ**. That is **105.0456 / 78.8878 / 101.6580 kWh/m²** of real space-heating energy absent from each fixture's `heating_eui_kwh_m2` **and** from its `total_eui_kwh_m2`, and **the golden expected values encode the understatement** — `test_r1_heating_eui` passes *because* it agrees with the wrong number. 🟢 **Zero effect on any fleet figure.** Over 8,152 `ok` census rows, `max |dh_total_gj − dh_water_systems_gj|` = **0.0** and **0 rows** carry a non-Water-Systems district-heating row, so **153.8231 kWh/m² over 8,153 and OPEN-61's 152.3011 → 171.7718 are both untouched.** ❓ **Remedy not proposed and not authorised.** The general fix — fold each of the 14 rows into its matching end-use column — is mechanically clear but **would move golden expected values upward**, which is a director/user decision and not an executor's. | Reported **energy**, on any building whose district heating is not hot water | the three golden fixtures, measured; **zero fleet buildings**, measured | 🔴 **mechanism traced to the 14-row ABUPS breakdown; size measured exactly on all three fixtures; fleet exposure measured at zero; remedy unproposed because it moves golden values** |

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

🔴 **SUPERSEDED IN PART 2026-08-21.** The ordering below was written on 2026-08-20. The
second ten-item pass (`implemenation/previous/PLAN_ten-live-items-2026-08-21.md`) has since measured ten of
these items; **read BOTH 2026-08-21 entries in §7 first** (the day pass and the night pass) — it changes what several of the entries below
assert. In particular: item 2's "two questions" is now **one** (the harvest carries no zone detail
anywhere, so a re-fetch buys custody only); item 5's population is **39, not 21**, and is dominated by
**five buildings**; and item 7's "cheap test" **has been attempted** and reached only 23 of 44.

🔴 **REWRITTEN 2026-08-20 (evening/overnight), after the ten-item pass
(`implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`, T01–T11) and after the OPEN-61 fleet
census finished.** The list below is the director's ordering, not a user ruling, and it is not a
commitment. **Six items moved off "unmeasured" tonight and onto "measured, awaiting a decision" —
that is the whole shape of the change.**

**A. Decisions now waiting on the user — each one has its measurement in hand.**

1. 🔴 **OPEN-60 — which of the three integrity sub-gates, if any, gets wired into the fleet
   pipeline.** `abups_ok` fires on **2 of 7,860** and is safe. `meter_ok` would fire on **99.9 %**
   and is mis-specified (a subset of electricity compared against the total), and its only 6 passes
   are buildings that produced **no electricity at all**. `gas_zero` is informational by its own
   comment. **The remedy is not "wire the gate" but "wire `abups_ok`" — and that is still the user's
   call, not the director's.**
2. 🔴 **OPEN-53 — re-fetch or leave.** The 874 files **are on Speed** (874 `.sql` + 874 `.end`,
   matching the shortfall exactly), so this is a harvest defect and no re-simulation is owed. ⚠️ But
   the 20 sampled files parse to **nothing usable** — meter-only `.sql`, zero zone-level variables —
   so a re-fetch buys custody, not numbers. **Two questions, not one: fetch the 874? and should
   `parse_building()` fall back to a meter-only EUI when zone keys are absent?**
3. 🔴 **OPEN-14 — open the fusion gate, or acquire the missing slices, or neither.** Sized at last:
   with the gate opened in a sandbox the tier fills **106 of 121 (87.6 %)** of `nyc_centre`'s null
   `height_m`. The machinery works; the blocker is custody of eleven slices and one config default.
4. 🔴 **OPEN-17 — the one imputation decision**, now with its context: the machinery covers **one
   target out of seven**. `year_built` 5,913/5,913; `levels`, `function_tag`, `postcode`,
   `building_tag`, `height_m` **zero**.
5. 🔴 **OPEN-35's remaining half** — *which* fallback is correct. Unchanged tonight: 21 buildings, 42
   simulations, seven cells, a measured sign flip in `la_suburban`. **The oldest undecided item on
   this list.**
6. 🔴 **OPEN-62 — what a storey IS** for a prototype with an attic, a plenum or a high bay. A
   definition question, not a measurement, and explicitly not an executor's.

**B. Measured tonight, and what each one now points at.**

7. **OPEN-38 — no longer a null result.** All 44 fatals have a named cause; **38 of 44 (86 %) are one
   family** (inside-surface heat-balance temperature divergence). The `la_rural` concentration is
   **entirely `Warehouse`**, and 5 of the 6 mode-independent failures are exactly run 4's five
   `la_rural` `not_simulated` buildings — so that half is **OPEN-42/OPEN-56's face, not a new item**.
   The remaining 5 of 11 are mode-specific and unexplained. **Next step: whoever scopes OPEN-56's
   remedy should run the cheap test — re-run a few of the 44 with `Zone.Volume` written.**
8. **OPEN-56 / OPEN-09 — both re-derived on the adopted run** (8,160/8,160 stub; 16/8,160
   non-convergence). Neither number moved. OPEN-56's remedy shape is still open.
9. **OPEN-60's blast-radius bound is now a census**, not three files: **0 non-1 multipliers across
   8,160 IDFs**. The 153.8 headline is untouched, and now provably so.
10. ✅ **The C04 leftover is SETTLED: code drift, not non-determinism** — and it took two attempts to
    earn that. T10's double run gave 0 of 33 columns differing, but **both arms terminated
    `failed_fatal`**, so `NaN == NaN` was doing the work; that result was not banked. T11 repeated it
    on `austin_rural/way/1480414365` (`SmallOffice`), which **completes**: **28 columns compared, 23
    non-null in both, 0 differing** — `iod` 0.0 = 0.0, `simulation_status` `success` = `success`,
    `total_eui_kwh_m2` **100.01588245660348** to the last digit. **The pipeline is deterministic at a
    fixed HEAD.** ➕ **And the third explanation T10 surfaced is killed rather than left hanging:** the
    two on-disk IDFs for `way/266034056` are not a file and its repair — they are **two different
    zoning strategies** (`_F0_CORE`, 2.57 MB, vs `_F0_WHOLE`, 550 KB), and **both are `failed_fatal`**,
    so no status flip can be blamed on which file a run picked up. ⚠️ Both die the same way —
    `CalcHeatBalanceInsideSurf` at **1,940,305 °C** and **20,368,972 °C** — which is OPEN-38's 86 %
    family showing up in a third place tonight. **This is now a candidate for closure by the user, or
    for an item ID if they want it tracked; the director recommends neither a new ID nor further
    work.**

**C. Carried, untouched tonight.**

11. **OPEN-56's** remedy shape · the 4 `Courthouse` → `OpenUBEMUnknown` flips (477,804 m²) ·
    **OPEN-35's** regression remedy · **OPEN-18** (unsized; needs a purpose-built small-cold-cell
    sample) · **OPEN-19** (a Title 24 table must be acquired or authored before the hypothesis can be
    tested at all) · **OPEN-10** (settled at 4.5 % reach; no action) · **OPEN-03** Arc B complete,
    remedy is OPEN-18's territory.
12. 🔒 **OPEN-27 — CLOSED 2026-08-20.** The lesson stands and is worth re-reading: **an item whose
    only obstacle is a permission should be surfaced as a permission question, not carried as work.**
    It sat open for weeks and closed in four minutes once the right question was asked.

**The pattern that keeps repeating, now with a fourth instance.** OPEN-58, OPEN-60 and OPEN-61 were
each found by an executor auditing its own arithmetic when no plan asked for it. Tonight a **fourth**:
an executor refused a task because the plan named a signature (`CheckWarmupConvergence`) that matches
**0** buildings, and quoted the conflict instead of substituting one that would have produced a
plausible-looking number. **The remedy shape that keeps suggesting itself — a reconciliation check
inside `parse_building()` — is now joined by a second: the gate that would do it already exists and
one third of it is sound.**


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
`implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md` §6c. **Stays open, now with a number.**

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


### OPEN-62 / OPEN-03 — 🟢 THE DENOMINATOR QUESTION IS ANSWERED, 2026-08-21 (user ruling R1)

**The user was asked which storey definition should set the published denominator and declined to
rule on preference — "check against real storeys first".** That was the right call: the question had
an answer on disk and nobody had looked.

`openubem/outputs/comparisons/open03_storey_census.csv` (8,160 rows) carries `source_storey_count` —
the **real** storey count from the input data — beside `auto_storey_count` and
`layout_assign_storey_count`. Joined to `open61_census_fleet.csv` for footprint, recorded area and
recorded EUI, it answers R1 with no new computation. **Director-run; no executor involved.**

| Definition | Agrees with reality | Mean storeys (real 3.127, max 105) | Denominator | Pooled EUI |
|---|---|---|---|---|
| `source_storey_count` (**reality**) | — | 3.127, max 105 | 23,849,281.2 m² | **156.4692** |
| `auto_storey_count` (**adopted**) | **99.91 %** (8,153/8,160) | 3.131, max 105 | 23,849,281.2 m² | **156.4692** |
| `layout_assign_storey_count` | **39.78 %** (3,246/8,160) | 1.283, max 18 | 8,210,828.9 m² | **454.4825** |

**The adopted definition is the real one.** `auto_storey_count` differs from the true storey count on
**7 buildings out of 8,160**, and the denominator it builds is **identical, to the digit, to the one
reality builds**. Recorded floor area tracks `footprint × real storeys` at a median ratio of
**1.0000** (p10 0.9977, p90 1.0016).

🔴 **`layout_assign` is not a rival definition — it is wrong.** It disagrees on 4,914 buildings,
**4,670 of them by undercounting**, and its agreement collapses the moment a building has more than
one storey:

| Real storeys | n | `auto` agrees | `layout_assign` agrees |
|---|---|---|---|
| 1 | 3,245 | 99.78 % | 93.19 % |
| 2 | 1,988 | 100.00 % | 5.48 % |
| 3 | 1,439 | 100.00 % | 3.20 % |
| 4–5 | 698 | 100.00 % | 2.58 % |
| 6–10 | 396 | 100.00 % | 9.60 % |
| > 10 | 394 | 100.00 % | 2.79 % |

🔴 **RETRACTION — the "~2.9× swing" must stop being described as a definitional ambiguity.** CP-F of
the night pass reported that changing the storey definition moves pooled EUI from 153.91 to as much
as 442.24 and called the denominator "a choice, not a fact". **That framing is now withdrawn.** The
swing is real arithmetic but it is **the size of `layout_assign`'s storey error**, not the width of a
legitimate choice. Measured against reality there is no choice to make: one definition is right on
8,153 of 8,160 buildings and the other is wrong on 4,914. **153.8231 needs no defence beyond the
table above.**

**What this closes and what it does not.** OPEN-62's *denominator* question is **answered**. What
remains of OPEN-62 is the `layout_assign` storey defect itself, which is **OPEN-03's** territory and
stays open there. OPEN-62 also still owns its own Z_Origin history (fixed and verified 8,160/8,160).

🔵 **A cross-link found, not sought.** Five of the seven buildings where `auto` disagrees with reality
— `way/472960972`, `way/472961034`, `way/472961088`, `way/472961091`, `way/472961171`, all `la_rural`,
all `Warehouse` — are **exactly** run 4's five `la_rural` `not_simulated` buildings named in OPEN-38.
`auto` reads 3 storeys where the source says 1. **This is a third independent arrival at the same five
buildings** and is recorded, not resolved. The other two are `way/402215469` (`la_urban`, source 1 vs
auto 6) and `way/266034056` (`nyc_centre`, source 1 vs auto **19**).

⚠️ **One number above is not the adopted headline and must not be quoted as it.** Pooled over the
8,152 rows with usable recorded area this join returns **153.4929**, against the adopted 153.8231 over
8,153 — different row set, different provenance. **Do not restate the adopted figure.** See the
2026-08-21 non-reproducibility entry in `OpenUBEM_debug_References.md` ch. 8.

🟢 **The comparison is NOT circular, and the director checked this before ruling.** `source_storey_count` is the `levels` column of `05_results.csv` — the **input data** (`scripts/analysis/open03_storey_census_2026-08-20.py:181,184`, asserted non-null on all 8,160 rows). `auto_storey_count` is `storey_count` parsed back out of the **8,160 built IDFs on disk** (`:186-199`). Two different sources, one an intention and one an artifact. The 99.91 % is therefore a real end-to-end validation of the `auto` builder — **it writes the storey count the source asked for** — and not an identity restated.

**Evidence.** §6 of `implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md` (T01) ·
`openubem/outputs/comparisons/open03_storey_census.csv` · `open61_census_fleet.csv`.

### OPEN-09 — 🔒 CLOSED 2026-08-21 (user ruling R3)

**What it asked.** Whether `thermal_mass=True` drives warmup non-convergence, and whether calling the
effect "cosmetic" — never tested when the item was written (E-LA-23) — actually holds.

**Both halves are answered.** "Cosmetic" was tested and **holds**: 96.3 % distribution overlap with a
small, correctly-signed residual (audited). The population is **16 of 8,160**, cell split
`la_centre` 2, `la_rural` 10, `la_suburban` 3, `la_urban` 1, all others 0 — **reproduced three times
independently**: run 2, then run 4 on 2026-08-19 (T13), then run 4 again on 2026-08-20 (T03) by a
different executor, a different script and a different scan, **identical every time**.

**It is not downstream of OPEN-56**, and that was tested rather than assumed: the ten
non-convergent-but-successful buildings show 150 warnings baseline and 150 treated, **15/15 unchanged**,
while the same treatment clears the volume warning **70/70 → 0/70**. Two independent defects
overlapping on the same 16 buildings.

⚠️ **A citation correction that survives this item.** The signature is
`Inside surface heat balance did not converge` (`scripts/analysis/open09_fleet_err_taxonomy.py:42`),
**not `CheckWarmupConvergence`** — that string has **0 occurrences** in the auto corpus, and any future
task written against it would measure nothing while appearing to measure this item.

🔒 **CLOSING NOTE.** Nothing here is a defect anyone still has to fix: the effect is cosmetic, it is
bounded to 16 buildings, and it is reproducible on demand. **What survives:** the 16 belong to the
inside-surface heat-balance family that **OPEN-38** owns (38 of 44 fatals, same divergence class), and
**E-LA-17 resolves to exactly this population and would double-count if ever adopted** — that warning
now lives in OPEN-38. **Do not reopen to re-ask "is it cosmetic" — it was tested and it holds.**

### OPEN-10 — 🔒 CLOSED 2026-08-21 (user ruling R3)

**What it asked.** Whether a `ZoneGroup` list-multiplier edit would restore exact storey
expressibility (E-LA-37), and for how many buildings.

**Answered on both halves, and the answer is "real but narrow".** The capability is **confirmed real
from the schema**. The carried "90 buildings" **re-derived exactly** — 66 `MidriseApartment` + 24
`HighriseApartment` — by running the experiment N11 named and declined. **Restated on run-4 data at
CP-3 (T16): the ceiling is 4.78 %, 96 of 2,007** `fallback_not_expressible` buildings. The other
**95.2 % are structurally beyond the edit**, and `applied` is only 497 of 7,442.

🔵 **One honest non-reproduction, self-reported rather than smoothed over.** The evaluated population
reproduced exactly (7,442) but the 90-building archetype split did **not** — **69/27 against the
carried 66/24** — and the cause is understood: run 4 carries OPEN-35's storey corrections, which this
item's own X08 finding had already placed upstream of exactly that classification boundary. All other
archetype counts unchanged.

🔒 **CLOSING NOTE.** The item asked whether the edit is worth making and the measurement answers it:
it would fix **at most 4.78 %** of the inexpressible population. **What survives:** if the edit is ever
wanted, it is **new feature work and needs a new item** — it is not an open defect. The 95.2 % that is
structurally beyond it is a `layout_assign` storey-representation problem and belongs to **OPEN-03**.

### OPEN-14 — 🔒 CLOSED 2026-08-21 (user ruling R3)

**What it asked.** Whether the UTCI height backfill is reproducible from a clean checkout.

**Answered: it is not, and we now know exactly why.** **Zero `FUSED` provenance tokens across all
8,160 buildings** — including `nyc_centre`, the one cell that *has* a tracked Overture slice. The
missing slices are a real but **non-operative** blocker: **the config gate closes first.** The
suspected convergence with OPEN-12 on the same four cells is a **coincidence** (N15).

🟢 **And the other half is measured too.** With `FUSION_SOURCES_BY_TARGET` set to
`{"height_m": ("overture",)}` **in a sandbox only** (`openubem/config.py` verified unmodified
afterwards), the production router over `nyc_centre` fills **106 of its 121** null `height_m` rows —
**87.6 %** — every one stamped `FUSED_OVERTURE_HIGH`. The 15 it does not fill are **traced, not
guessed**: **14** match a footprint whose Overture record carries its own NaN height
(`openubem/semantic/fusion.py:230-252`), **1** has no spatial match inside
`NEAREST_TOLERANCE_M = 10.0` (`fusion.py:47`).

🔒 **CLOSING NOTE.** The machinery works. **What stands between this project and a reproducible height
backfill is one config default and eleven missing Overture slices — not a broken tier.** That is
custody, not a defect, and the item's own question is fully answered. **What survives:** whether to
open the gate is a **decision the user has not been asked for and that needs its own item when it is
wanted** — nothing was enabled, no fleet input was regenerated, run 4 was untouched. The
2,806-building source-height coverage gap itself belongs to **OPEN-17** (which absorbed OPEN-15 and
OPEN-16 under ruling R2 of 2026-08-20). **Do not reopen to re-ask "is it reproducible" — it is not,
and the two reasons are named above.**

### OPEN-18 — 🔒 CLOSED 2026-08-21 (user ruling R3)

**What it asked.** Q3 — whether the √S vertical-form distortion is reachable with the mechanism built
for it, in small buildings in cold cells.

**Answered, and the answer inverted along the way.** The item was carried as *"confirmed unreachable
by the mechanism built for it"*, and the population was recorded only qualitatively — *"small
buildings, cold cells"*, with **no numeric footprint band, no numeric cold threshold and no storey
range stated anywhere on disk**. The 2026-08-21 measurement searched for those criteria, did not find
them, proposed a band **as an explicit assumption of the executor's rather than the record's** (small
= ≤ 35th percentile of `footprint_area_m2` within cell, among successes; cold = ASHRAE zone 5 or
colder), and then counted.

🔵 **Finding that changed the item: the register's own "cold cells" proxy is not climatically
uniform**, so `nyc_rural`/`nyc_centre` could not be used as written. Under a standard external
definition the qualifying population is **n = 69, entirely in `nyc_rural`, and dominated by one
archetype (`SmallOffice` 56 of 69)**.

🔒 **CLOSING NOTE — read this one carefully, it does not close the way the others do.** The item's
question is answered: the population is **reachable**, not unreachable, and **no new simulation is
needed to take a first cut at n = 69 today**. ⚠️ **But the √S test itself has NOT been run, and no
minimum sample size for it is stated anywhere, so n = 69 cannot be checked for adequacy against the
record.** **What survives:** running the test on n = 69 is **available work that now has no home** —
if the user wants it, it needs a **new item**, and the director has flagged this rather than letting
it disappear into a closure. **Do not reopen this item to run the test; open a new one.**

**Evidence.** `extra/MEASUREMENT_open-18_small-cold-population.md` ·
`openubem/outputs/comparisons/open18_small_cold_population_2026-08-21.csv` (130 rows) ·
`extra/MEASUREMENT_open-18-20_method-bounds.md`.


### Handoffs from the 2026-08-21 closures — what the four closed items left behind

🔴 **Read this section as part of OPEN-38, OPEN-03 and OPEN-17.** Four items were closed on
2026-08-21 (user ruling R3). Each closing note in §6 says "what survives" and names a receiving item.
**A closing note that hands work to another item is a promise, and this section is where the promise
is kept** — the director checked before writing it that `E-LA-17` appeared **nowhere** in this book
outside the closing note itself, which would have made that note false. Nothing below is new
measurement; it is relocation, so that closing four items loses nothing.

**→ OPEN-38 inherits, from OPEN-09:**

1. ⚠️ **`E-LA-17` would double-count if ever adopted.** It resolves to exactly OPEN-09's 16-building
   population (X07), which is the same inside-surface heat-balance family OPEN-38 already owns
   (38 of its 44 named fatals). **Anyone costing E-LA-17 must net out OPEN-09's 16 first.**
2. ⚠️ **The signature is `Inside surface heat balance did not converge`**
   (`scripts/analysis/open09_fleet_err_taxonomy.py:42`), **not `CheckWarmupConvergence`** — 0
   occurrences of the latter in the auto corpus. A task written against the wrong string measures
   nothing while appearing to measure something. This bit the arc once already.
3. 🔵 **The 16 are cosmetic and that is tested, not assumed** — 96.3 % distribution overlap, small
   correctly-signed residual, reproduced identically three times. **They are not a fix target.** They
   matter to OPEN-38 only as a population to exclude, not as damage to repair.
4. 🔵 **They are NOT downstream of OPEN-56** — 15/15 unchanged under the volume treatment that clears
   the volume warning 70/70 → 0/70. So T02's zone-volume fix will **not** move them, and if a future
   pass finds them moved, something else changed.

**→ OPEN-03 inherits, from OPEN-10:**

5. 🔴 **The `ZoneGroup` list-multiplier edit has a hard ceiling of 4.78 %** — 96 of 2,007
   `fallback_not_expressible` buildings on run-4 data. **The other 95.2 % are structurally beyond any
   multiplier edit** and are a storey-representation problem, which is OPEN-03's. **Do not let the
   edit be re-proposed as a general remedy for inexpressibility** — it was measured and it is not one.
6. 🔵 **The 66/24 → 69/27 archetype-split shift is explained, not open**: run 4 carries OPEN-35's
   storey corrections, which sit upstream of exactly that classification boundary.

**→ OPEN-03 also inherits, from OPEN-62 (§6 above):**

7. 🔴 **`layout_assign_storey_count` is wrong, not merely different** — it agrees with the real storey
   count on 39.78 % of the fleet, undercounts on 4,670 buildings, and its agreement collapses to
   **2.6–9.6 % for every building over one storey**. This is now OPEN-03's central measured fact and
   the reason the "~2.9× denominator swing" framing was retracted.

**→ OPEN-17 inherits, from OPEN-14:**

8. 🔵 **The fusion machinery works; the blocker is custody.** If the gate were opened, the tier fills
   **106 of 121 (87.6 %)** on `nyc_centre`. What stands in the way is **one config default
   (`FUSION_SOURCES_BY_TARGET`) and eleven missing Overture slices** — not a broken tier. The 15
   non-fills are traced: 14 Overture-side NaN heights (`openubem/semantic/fusion.py:230-252`), 1
   outside `NEAREST_TOLERANCE_M = 10.0` (`fusion.py:47`).
9. 🔵 **The OPEN-12 four-cell convergence is a coincidence** (N15) — do not rebuild an argument on it.

**→ Nobody inherits this one, and that is the point:**

10. ⚠️ **The √S test on OPEN-18's n = 69 is available work with no home.** OPEN-18's question was
    "is the population reachable", and closing it answered that — **reachable, n = 69, `nyc_rural`,
    `SmallOffice` 56 of 69, and runnable today with no new simulation.** But the test itself was never
    run, and **no minimum sample size for it is stated anywhere on disk**, so n = 69 cannot be checked
    for adequacy. **If the user wants the √S test run, it needs a NEW item (`OPEN-63`); do not reopen
    OPEN-18.** Recorded here rather than allowed to vanish into a closure.

### OPEN-63 — OPENED 2026-08-22, while designing the OPEN-61 remedy

**How it was found, and why that matters.** It was not found by a test. The OPEN-61 remedy plan asked
one question that no task had been given — *if district heating is added to the energy total,
what happens to the carbon total?* — and the answer was read straight out of `carbon.py`.
**This is the fifth defect in a row that came from auditing arithmetic rather than from exercising
behaviour** (OPEN-58, OPEN-60, OPEN-61, OPEN-62, and now this). The pattern is no longer a
coincidence and is recorded as such: **the formulas in `openubem/results/` are not covered by any
control that reconciles their parts against their whole.**

**Mechanism — two citations, both verified for the OPEN-61 plan on 2026-08-22.**

- `openubem/results/carbon.py:106`:
  `gwp_dhw = dhw_gas_eui * f_gas + dhw_elec_eui * f_elec`. The DHW carbon term is assembled from the
  two **fuel-specific** columns, `dhw_gas_eui_kwh_m2` and `dhw_elec_eui_kwh_m2`. It **never reads**
  `dhw_eui_kwh_m2`, the combined column. Any DHW energy that is not gas and not electricity is
  therefore invisible to carbon **by construction, not by omission of a name**.
- `openubem/config.py:83`: `GWP_NATURAL_GAS_KGCO2_KWH: float = 0.181  # Iseri et al. (2025)`. This is
  the only fuel factor in the file; electricity is resolved per state by `get_elec_factor(state)`.
  **There is no district-heating factor of any kind.**

**Size — known exactly, because OPEN-61 already paid to measure it.** 19.4707 kWh/m² pooled
over n = 8,144, **12.78 % of pooled site energy**, concentrated: 116 buildings carry 70.5 % of it.
Those 116 are `SuperTallBuilding` + `TallBuilding` and hold **37 % of fleet floor area**, so the
carbon under-report is worst precisely on the buildings that dominate the fleet total.

⚠️ **This item does not blame the OPEN-61 fix, and the distinction is load-bearing.** The
carbon total has been missing this energy for as long as district heating has been simulated. The fix
does not create the gap; it makes the gap **legible**, by moving the energy into `total_eui_kwh_m2`
while `gwp_total_kgco2_m2` stays where it was. **A reader comparing the two after the fix will see an
inconsistency that was always there.** Reporting it as "caused by the fix" would be false and would
argue against the fix.

🟢 **What is NOT affected.** Every energy figure. `153.8231 kWh/m² pooled over 8,153`
is untouched by this item, and OPEN-61's restatement — when and if it is adopted — is an
energy restatement that stands on its own.

❓ **Remedy — not proposed, not authorised, and deliberately left to the user**, because the
missing input is a number from the literature and not a line of code. Three shapes exist and none is
recommended here: a single national district-heating factor; a per-state factor mirroring what
electricity already does; or an explicit refusal to publish carbon for district-heated buildings,
with the column set to `nan` rather than to a wrong number. **The third is the only one that needs no
new value**, which is worth knowing before the literature search starts.

**Evidence.** §5 fact F10 of `implemenation/PLAN_open61-dh-remedy-2026-08-22.md`.

### OPEN-64 — OPENED 2026-08-22, by a failing test rather than by an audit

**This one matters for how it was found.** The four defects before it — OPEN-58, OPEN-60,
OPEN-61, OPEN-62 — were all found by reading arithmetic. **This one was found by the test suite,
in the same pass that was fixing OPEN-61**, and it is the first time the suite has caught something
this arc did not already know. It is also the direct counterexample to a claim this project had
written down as settled.

**What was claimed, and what is actually true.** OPEN-61's plan recorded, as fact F3, that
*"100.00 % of fleet district heating is Water Systems — there is no question about which end use
this energy belongs to."* That is **true of the fleet and false of the code**. The first
implementation of the OPEN-61 fix read the ABUPS `Total End Uses` cell on the strength of F3; the
suite came back **3 failed / 1,933 passed / 55 skipped** and all three failures were
`TestEuiGolden::test_r{1,2,6}_total_eui`. **The repository's own golden fixtures are the mirror image
of the fleet: 100 % of their district heating is `Heating` and 0.00 GJ is `Water Systems`.**

**Mechanism.** The ABUPS `End Uses` table has a `District Heating` **column** and 14 end-use
**rows** — Heating, Cooling, Interior Lighting, Exterior Lighting, Interior Equipment, Exterior
Equipment, Fans, Pumps, Heat Rejection, Humidification, Heat Recovery, Water Systems, Refrigeration,
Generators. After OPEN-61 T01b the parser reads **one** of them. The remaining 13 are read by no
code path anywhere in `openubem/`, and no meter covers them either — OPEN-61 F1 established that
**0 of 8,152** simulated buildings carry a district-heating meter.

**Size, measured on every fixture rather than sampled.**

| fixture | DH `Heating` | DH `Water Systems` | floor area | missing from total |
|---|---|---|---|---|
| `r1_single_zone.sql` | 148.24 GJ | 0.00 GJ | 392 m² | **105.0456 kWh/m²** |
| `r2_one_zone_per_floor.sql` | 709.99 GJ | 0.00 GJ | 2,500 m² | **78.8878 kWh/m²** |
| `r6_perimeter_core.sql` | 1,646.86 GJ | 0.00 GJ | 4,500 m² | **101.6580 kWh/m²** |

🔴 **The uncomfortable part: the golden expectations encode the error.**
`test_r1_heating_eui` passes today, and it passes *because* the expected value agrees with a
`heating_eui_kwh_m2` that is missing 105.0456 kWh/m² of district-heated space heating. **A green
suite is not evidence of correctness here.** Any remedy therefore has to move golden expected values
**upward**, which is why none is proposed below.

🟢 **What is NOT affected, measured and not assumed.** Every fleet number. Over the 8,152 `ok`
rows of `open61_census_fleet.csv`: `max |dh_total_gj − dh_water_systems_gj|` = **0.0**, and the
count of rows with `dh_other_rows_sum_gj > 0` is **0** — per building, not merely in aggregate.
**153.8231 kWh/m² pooled over 8,153 is untouched, and so is OPEN-61's candidate restatement of
152.3011 → 171.7718.** This item changes nothing that has ever been published; it says that a
building type the fleet happens not to contain would be reported wrongly.

❓ **Remedy — not proposed, not authorised.** The general fix is mechanically obvious: fold
each of the 14 ABUPS district-heating rows into its matching end-use column instead of folding one.
It is not taken here for two reasons, both worth stating. **First, it moves golden expected values**,
and this session does not edit a validated expectation without a ruling. **Second, it has no fleet
justification** — the measured exposure is zero buildings, so it buys correctness on a
population this project has never simulated. **The honest framing for the user is: this is a
correctness debt with no current victim, and it should be paid before the first district-heated
space-heating building enters a fleet, not necessarily today.**

**Evidence.** §5 facts F3 (narrowed) and F11 of
`implemenation/PLAN_open61-dh-remedy-2026-08-22.md`; task T01b of the same plan.

## 7. Amendment log

**2026-08-20 (evening/overnight) — a TEN-ITEM PASS on the live register, run while the user slept.**
Plan: `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md`. Ten of the sixteen live items had a
next step that was a **measurement, not a decision**; those ten were planned and executed, and every
one of them stopped short of a remedy. **No item was closed, no item was opened, no published number
moved, and no ruling was taken.** What changed is what is known.

**What landed, item by item.**

- 🟢 **OPEN-53 is answered.** The 874 missing `.sql`/`.end` **are still on Speed** — 437/437 in
  `austin_suburban_fast_zone` and 437/437 in `austin_suburban_floor`, matching the local shortfall
  cell for cell. **It is a harvest defect, not a simulation-side loss; no re-simulation is owed.**
  ⚠️ And the answer opened a smaller question: the 20 sampled files parse to **nothing usable**
  (`failed_zone_mismatch`, zero zone-level variables — meter-only output for that batch).
- 🟢 **OPEN-38's own named first measurement is run**, a month after it was named. **44 of 44 fatals
  have a preceding severe** (`no_preceding_severe` = 0) and **38 of 44 (86 %) are one family** —
  inside-surface heat-balance temperature divergence. The `la_rural` concentration resolves into an
  item we already have: **all 11 failing stems are `Warehouse`**, and 5 of the 6 that fail in all
  three modes are exactly run 4's five `la_rural` `not_simulated` buildings.
- 🟢 **OPEN-14 is sized.** With the config gate opened in a sandbox, the fusion tier fills
  **106 of 121** null `height_m` rows in `nyc_centre` — **87.6 %** — all stamped `FUSED_OVERTURE_HIGH`.
  The machinery works; the blocker is entirely custody of the slices.
- 🟢 **OPEN-17 has its context at last:** the imputation machinery covers **one target out of seven**.
  `year_built` is filled 5,913 of 5,913 (100 %); `levels`, `function_tag`, `postcode`, `building_tag`
  and `height_m` are filled by nothing at all.
- ✅ **OPEN-60's blast-radius bound is now a census:** **0 non-1 multipliers across all 8,160** run-4
  IDFs (director-reproduced independently: 285,600 `Multiplier` fields, every one 1; zero `ZoneGroup`
  objects). It rested on three files before tonight.
- ✅ **OPEN-56's 100 % is re-derived on the adopted run** — 8,160/8,160 — instead of on run 2, and
  **OPEN-09's 16** reproduced a second time by a different executor and script.
- ✅ **OPEN-58's four outstanding record corrections are applied**, including the one that mattered:
  the mechanism is **shared process cwd**, not a shared outdir, and the wrong wording had cleared two
  of three exposed importers.
- ✅ **The archiving rule's own failure mode was caught live.** Book I's move into `DONE/` was
  committed with **129 dead citations across 58 files** and the checklist asserting in writing that
  nothing was dead. Swept to **1** (a `docs_DONE/` exclusion) and the checklist corrected.

**Two process findings worth more than any single number.**
1. 🔴 **An executor refused a task because the plan named the wrong string** — the plan asked for
   `CheckWarmupConvergence`, OPEN-09's real signature is `Inside surface heat balance did not
   converge`, and the wrong string matches **0** buildings. It stopped and quoted the conflict
   instead of substituting. **The director wrote that error; the executor caught it.**
2. 🔴 **A director's own literal search-and-replace corrupted its own quotation** of the dead path it
   was repairing. Recorded in the plan so the next sweep expects it.

**The last two landed after the entry above was written, and both changed a stated conclusion.**

- 🔴 **T01 — the gate exists, and only a third of it is usable.** First fleet-scale run of
  `check_building_integrity()`, 7,860 `.sql`. **`abups_ok` fires on 2** (0.025 %) and is safe to
  wire. **`meter_ok` would fire on 99.9 %** — it compares a subset of electricity against the total
  (`parser.py:658-665` vs `:650-655`; measured 47.0 % on one building), **and its only 6 passes are
  buildings that produced no electricity at all**, reaching True through the degenerate branch at
  `:667-671`. `gas_zero` is informational by its own comment. **"Wire the gate" is three decisions,
  not one.** ➕ Two unasked side-findings: **6 census buildings produced `.sql` with no zone-level
  data** — the same meter-only signature as OPEN-53, but in a *local* rebuild — and the census work
  tree holds **7,861 directories against 8,151 rows, 290 short**, which ruling R6's preservation task
  must record rather than claim 100 %.
- ✅ **T10 + T11 — the C04 leftover is CODE DRIFT, and it took two attempts to earn that sentence.**
  T10's double run returned 0 of 33 columns differing, **but both arms terminated `failed_fatal`**, so
  every EUI column was null in both and `NaN == NaN` was doing the work. The director did not bank it;
  T11 repeated the method on a building that **completes**: **28 columns compared, 23 non-null in both,
  0 differing** — `iod` 0.0 = 0.0, `simulation_status` `success` = `success`, `total_eui_kwh_m2`
  **100.01588245660348** identical to the last digit. **That is the determinism claim, properly made.**
- ➕ **And T11 killed the third explanation it was written to test, which is worth as much.** The two
  on-disk IDFs for `way/266034056` are **not** a file and its repair — they are **two different zoning
  strategies**: `fleet_staging/idfs` writes `WAY/266034056_F0_CORE` (core/perimeter, 2.57 MB) and
  `step3/idfs` writes `WAY/266034056_F0_WHOLE` (whole-floor, 550 KB). **Both fatal**, so a status flip
  cannot be explained by which file a run picked up for this building. ⚠️ Both die the same way —
  `CalcHeatBalanceInsideSurf` at **1,940,305 °C** and **20,368,972 °C** respectively — which is
  OPEN-38's 86 % family again, in a third place.

---

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
  agreement. Executing as `implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`.
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

---

**2026-08-20 (night) — ✅ THE OPEN-61 FLEET CENSUS CLOSED, ITS NUMBER MEASURED, AND RULING R6
EXECUTED. Counts unchanged: 16 live / 46 retired / 62 total, next free `OPEN-63`.**

Three things landed after the ten-item pass, all in `implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md`
and `implemenation/previous/PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`:

**1. The census closed at 8,160 — every fleet building has a row (T03).** 8,160 rows, 8,160 unique
`osm_id`: **8,152 `ok`**, 7 never-simulated upstream appended as reason-rows, and **1 EnergyPlus OOM
crash** (`nyc_centre way/266170763`, a 43-storey `LargeHotel`). The OOM was diagnosed rather than
written off — 0 Severe / 0 Fatal, `.err` ending mid-line in a `SizeWaterCoil:` warning, no `.end`, a
305 MB `.sql` with 36 tables but **no `TabularDataWithStrings`**, 15.6 GB working set at death. Same
silent `std::bad_alloc` signature already on record for an 89-storey building; the existing debug-
reference entry was **extended, not duplicated**, and now carries the `TabularDataWithStrings` test
that separates an OOM crash from a controlled fatal. Five deviations are disclosed in the T03 entry:
a kill-and-resume, a thread-pool→process-pool switch, 3 collision rows stripped, 4 smoke rows merged,
2 solo retries.

**2. 🔴 The number, and a correction to how the estimate should be judged (T04, CP-3 signed).**
**19.4707 kWh/m² pooled over n = 8,144**, director-re-derived from the CSV to six decimals =
**12.7 % of pooled site energy**. It is insensitive to the floor-area column and to both known
anomalies. Against the published band 8.7 / 17.2 / 20.2 it lands *inside*, 3.6 % under the ceiling —
**but that reading flatters the estimate.** The per-building median dh÷dhw ratio is 0.6503 while the
pooled ratio is **0.9382, 44 % higher**; F5's own method, re-run against the fleet's measured pooled
DHW of 20.75 kWh/m², tops out at **17.43**. The measurement is **11.7 % above anything that method
could have produced.** The sampling was sound — the error was applying a per-building median ratio to
a pooled quantity.

**3. 🔴 And the term is concentrated, which constrains every possible remedy.** 116 buildings —
`SuperTallBuilding` (24) and `TallBuilding` (92), **1.4 % of the population — carry 70.5 % of the
fleet's district heating**; four archetypes carry 91.8 %; offices, retail and shops sit near zero at
1.3–2.7 kWh/m². **19.47 is not a fleet-wide offset and must not be applied as one.** No corrected
fleet EUI was produced — the plan forbids it, and the concentration result makes the remedy a design
question. **Carried to the user, not decided.**

**One executor finding was overturned rather than accepted.** Pre-registered control C6 was answered
with the wrong denominator — DH ÷ *total site energy* instead of the plan's **dh ÷ dhw_eui** (§5 fact
F5) — and returned "NOT REPRESENTATIVE, ~50× off" together with a false claim that its denominator
matched the pilot's. Re-derived correctly: fleet median **0.6503**, IQR **0.3117–0.8642** against the
60-building pilot's 0.714 / 0.362–0.840 — **the small sample was representative.** The report section
and the script were both rewritten; the script's own verdict now prints REPRESENTATIVE. Recorded
because "the 60-building sample was unrepresentative" would have entered this register as a fact.
**This is the second time in two passes that a director re-derivation of a load-bearing executor
number changed the answer** (the first was T09's imputation claim in the ten-item pass).

**4. ✅ Ruling R6 executed — the corpus is out of the scratchpad (OPEN-62 plan T07).** Moved to
`C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20`: **7,861 building directories, 7,861
`.sql`, 121.9 GB, 12 cells**, by same-volume rename in **0.77 s**. R6 estimated ≈38 GB; the corpus is
**3.2× that**, and nothing was pruned to meet the estimate because R6 chose full preservation over
"preserve only what is cited". Destination is deliberately **outside** `%LOCALAPPDATA%\Temp`, breaking
with where the other corpora live, because that is a temp root Storage Sense may purge by age —
the exact failure R6 was written after. A checker was written (`scripts/analysis/corpus_inventory_check_2026-08-20.py`)
because "an inventory that is **checked** rather than written once" needs one; first run **PASS**.
⚠️ **Coverage is 96.4 %, not 100 %** — 7,861 directories against 8,152 `ok` rows; the 291-building gap
is the kill-and-resume, and those buildings' raw output is gone though their numbers survive in the
CSV. This was pre-committed in the T03 entry *before* the move, exactly so it could not be quoted as
100 % afterwards. **Named and not fixed:** run 4 and five sibling corpora still sit in the temp tree
under the same risk.


---

**2026-08-21 — a SECOND TEN-ITEM PASS, ten live items, four concurrent executors.**
Plan: `implemenation/previous/PLAN_ten-live-items-2026-08-21.md` (T01–T10, checkpoints CP-A…CP-D, all four
signed by the director 2026-08-21). Same discipline as the 2026-08-20 pass and the same outcome
shape: **no item closed, no item opened, no published number moved, no ruling taken.** Every task was
the measurement that makes a pending *user* decision decidable — never the decision. **§4's priority
ordering above is superseded by this entry** for the ten items named here.

**What landed, item by item.**

- 🔴 **OPEN-53's first question is CLOSED as a question, and the answer is worse than assumed.** The
  20-file sample was not unlucky. A full census of the harvest — **40,800 directories, no sampling** —
  finds **39,926 readable `.sql`, and every single one of them carries 0 ABUPS End-Uses rows and 0
  zone-level keys.** Meter-only is a property of the **whole harvest**, not of the 874. The 874
  themselves are entirely `austin_suburban`'s `fast_zone`/`floor` arms (437 each); `auto`, `building`
  and `layout_assign` are 8,160/8,160 complete. **Re-fetching the 874 buys custody and nothing else —
  no zone detail exists anywhere in this corpus to recover.** (`.end`-missing reproduced at 875,
  exact.) *(`extra/MEASUREMENT_open-53_harvest-sql-census.md`)*
- 🔴 **OPEN-53's second question is measured, and the director's audit overturned the executor's
  reading of it.** The executor reported a smooth divergence (median `pct_diff` ≈ 0 %, pooled gap
  −1.66 %). Re-deriving the pooled numbers independently shows it is **deterministic and
  archetype-structured, not smooth**: **3,810 of 8,153 buildings match the published EUI to full float
  precision**; `SmallOffice` (3,497), `RetailStandalone`, `QuickServiceRestaurant` match **100 %**,
  while `MidriseApartment` (2,818), `OpenUBEMUnknown`, `MediumOffice`, `LargeOffice`, `TallBuilding`,
  `LargeHotel`, `HighriseApartment` match **0 %**. The cause is the **elevator adder**:
  `published − meter_only` equals `elevators_eui_kwh_m2` to 1e-6 for **3,823 buildings**, and pooled
  elevators (2.2421) carry **≈88 % of the 2.5539 pooled gap** — a Phase-E post-processing addition no
  EnergyPlus meter can ever carry. **After removing elevators the residual is 0.31 kWh/m² pooled
  (≈0.2 %).** So the real remaining question is not "what does meter-only cost" but **"what is the
  0.2 % residual and its two-sided tail (min −502.68, max +873.37 kWh/m²) on a minority of
  buildings"** — which is unmeasured. *(`extra/MEASUREMENT_open-53_meter-only-eui-cost.md`, incl. the
  director addendum; only two meters exist fleet-wide, `Electricity:Facility` + `NaturalGas:Facility`,
  no district heating or cooling.)*
- 🟢 **OPEN-17 is sized on all seven targets, and a naive count would have got it wrong.**
  Needs-a-value: `levels` **7,719/8,160 (94.6 %)**, `function_tag` 7,741 (94.9 %), `year_built` 5,913
  (72.5 %, the one target filled 100 %), `postcode` 4,183 (51.3 %), `building_tag` 4,105 (50.3 %),
  `height_m` 2,806 (34.4 %), `geometry` 0. ⚠️ **`function_tag` and `building_tag` are never raw-null** —
  they carry placeholder/generic values instead, so a null count misses **two of the three largest
  holes.** The plan's placeholder target `roof_shape` does not exist as a provenance column; the
  executor used the register's own target list and said so.
  *(`extra/MEASUREMENT_open-17_target-null-census.md`)*
- 🟢 **OPEN-14's hole is fleet-wide and concentrated.** 2,806/8,160 (34.4 %) null `height_m`.
  `austin_rural`, `nyc_rural` and `nyc_suburban` are **100 % null** and hold **72.4 %** of the fleet
  total (`nyc_suburban` alone **56.6 %**). Extrapolating `nyc_centre`'s *measured* 87.6 % fusion fill
  to the other eleven cells' 2,685 nulls: **≈2,352 would fill, ≈333 would remain** — an extrapolation,
  labelled as one, not a second measurement. *(`extra/MEASUREMENT_open-14_null-height-by-cell.md`)*
- 🔴 **OPEN-35's population is nearly double what the item has been reasoning about, and it is
  top-heavy.** The undecided group-/global-median branch (`GROUPMEDIAN_LEVELS_MED`) carries
  **39 buildings, not 21** — and all 21 are inside the 39 (control passed). 38 were simulated.
  Swapping those 38 back to the pre-OPEN-35 `return 1` branch moves the fleet floor-area denominator
  **24,333,586.4 → 23,553,430.3 m², −3.21 %** (denominator only; the headline is **not** restated).
  ⚠️ **Director-added and decisive for how this decision should be weighed: the top 5 buildings carry
  ~71 % of that delta, and one building alone — `relation/7480583`, `austin_centre`, given 45 storeys
  by the fallback — carries 301,996 m², i.e. 1.24 % of the entire fleet floor area.** This is not a
  diffuse 39-building question; it is a handful-of-buildings question. *(director re-derivation;
  `extra/MEASUREMENT_open-35_fallback-population.md`)*
- 🟢 **OPEN-62 now has its decision table, and it recommends nothing — by design.** The register's
  30.0 %/70.0 % split is reproduced exactly (2,446/8,160 = 29.98 %; 5,714 = 70.02 %) on all 8,160
  rows. Agreement with `auto_storey_count`: Z_Origin-corrected **29.07 %**, naive **39.78 %**,
  floor-surface **23.75 %** — **none reaches 50 %.** On the six collapse-risk archetypes (2,983/8,160 =
  36.6 %, matching the register) the corrected and floor readers agree far less (11.5–11.7 % vs
  30.7–39.2 % off-risk). ⚠️ **The attic-excluded variant could not be built:** `auto_attic_zone_count`
  is **0 for all 8,160 rows**, making it numerically identical to the floor-surface column — reported
  as a finding rather than routed around. **What a storey IS remains the user's ruling.**
  *(`extra/MEASUREMENT_open-62_storey-definition-table.md`)*
- ⚠️ **OPEN-38's "cheap test" was run and it under-delivered — because the director's premise was
  wrong.** The plan asserted (as fact F5) that `.eio` survives fatal runs, generalising from **one**
  building. A full existence walk finds only **145 of 40,800 directories (0.36 %) have an `.eio` at
  all** — director-reproduced independently. Consequences, reported and not hidden: only **23 of the
  44** fatals were readable, and the 200-directory control could only be filled to **47**. On what
  could be read: zone-level volume-degenerate rate **19.19 % (fatal) vs 4.18 % (control)**, but the
  per-building rate **disagrees in direction** (26.09 % vs 34.04 %) because zone counts differ; fatal
  zone volumes are far smaller at the median (41.9 vs 453.2 m³) with a heavier tail. F7's 86 % family
  is resolved exactly — 21 high-temp + 17 `CalcHeatBalanceInsideSurf` = **38/44 = 86.4 %** — but
  **volume does not separate that family from the rest** (26.3 % vs 25.0 % degenerate). **The cheap
  test is not conclusive at this coverage and should not be quoted as fleet-scale.**
  *(`extra/MEASUREMENT_open-38-56_fatal-zone-volumes.md`)*
- 🟢 **OPEN-18 is reachable without new simulation, and the register's own proxy was wrong.** No
  numeric criteria for the √S test's population exist anywhere on disk — the executor quoted that
  absence and used a labelled assumption (small = per-cell footprint ≤ 35th pct; cold = ASHRAE 5+).
  ⚠️ **The register's "cold cells" shorthand `nyc_rural`/`nyc_centre` is not climatically uniform:
  only `nyc_rural` is zone 6A; `nyc_centre` is 4A, like its neighbours.** Qualifying population
  **n = 69**, all in `nyc_rural` (SmallOffice 56, MidriseApartment 7, OpenUBEMUnknown 5, SmallHotel 1).
  *(`extra/MEASUREMENT_open-18_small-cold-population.md`)*
- 🔴 **OPEN-19 does not reproduce at fleet scale — the sign is backwards.** City-to-city pooled EUI:
  Austin **161.00**, LA **128.13**, NYC **165.27** — **LA is the lowest of the three** (−20.4 % vs
  Austin, −22.5 % vs NYC), and archetype-matching over the 15 shared archetypes keeps the sign
  (−16.7 % / −25.3 %). The executor flagged, correctly and without conflating them, that this is a
  **sim-vs-sim across cities** comparison while the historic **+38.8 %** was **sim-vs-measured within
  LA** — so this does not refute that number, it fails to find any "LA runs hot" signature in the
  fleet itself. Code inventory re-confirms **zero** Title 24 / CALGreen / CEC references;
  `climate_zone` reaches only the `OpenUBEMUnknown` synthetic path; `economizer_db_limit_c` exists in
  data and is **read by none** of the 6 hardcoded HVAC call sites.
  *(`extra/MEASUREMENT_open-19_city-offset-fleet-scale.md`)*
- 🟢 **OPEN-09 × OPEN-38 overlap: overlapping, not identical, not disjoint.** |A| = 16 and |B| = 44
  both confirmed exactly. Auto-mode overlap **6 of 16**, and it splits cleanly on archetype: **all 6
  null-archetype buildings in A are also auto-mode fatals (100 %); all 10 `Warehouse` buildings never
  are (0 %)** — though half of those go fatal in other modes. **No merge proposed.**
  *(`extra/MEASUREMENT_open-09_open-38_overlap.md`)*

**⚠️ One unresolved discrepancy, surfaced twice independently and left standing rather than tidied
away.** T09's control C20 matched n exactly (8,153) but reproduced the pooled figure as
**153.8304**, not the adopted **153.8231** — a 0.0073 kWh/m² gap (0.005 %), with individual cells off
by up to 0.18. **The director's own independent re-derivation during the CP-A audit produced
153.8304 as well.** Two separate recomputations from `evidence/open48_refleet4` therefore do not
return the adopted number exactly. The difference is immaterial to every conclusion in this pass and
**the adopted baseline stands unchanged at 153.8231 pooled over 8,153** — but the adopted figure is
**not exactly reproducible from the adopted evidence**, and that is now a known, recorded, unexplained
loose end rather than a rounding footnote.

**Three process findings from this pass.**
1. 🔴 **A director premise generalised from a single file and cost a task most of its coverage** (F5,
   `.eio` survival: 1 building observed → asserted as fleet behaviour → true for 0.36 %). The
   executor caught it, measured the real rate, and reported the shortfall instead of quietly sampling
   around it. **The pattern is the same one the 2026-08-20 pass recorded: the plan's facts are the
   director's weakest link, not the executor's.**
2. 🟡 **Executor summary statistics can hide the structure that matters.** T02's median/IQR framing
   was accurate and uninformative; the archetype split and the elevator mechanism only appeared when
   the director re-derived the load-bearing number itself, per CLAUDE.md. **Re-derivation is not
   ceremony.**
3. 🟢 **Four concurrent executors appended ten progress entries to one plan doc with zero
   collisions**, each re-reading before appending as the plan required. The concurrency pattern
   works; it is worth reusing.

---

### Amendment — 2026-08-21, night pass — `implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`

Second pass of the day. Ten live items measured, four concurrent Sonnet executors, **CP-E–CP-H all
signed** (§9 of that plan). **No item closed, no item opened, no published number moved, no ruling
taken.** Still **16 live / 46 retired / 62 total, next free `OPEN-63`**.

**Why this pass exists at all.** The previous plan's F5 was wrong — it asserted that `.eio` survives
fatal runs, generalising from one building, and the resulting OPEN-38 test reached only 23 of 44
fatals. The diagnosis was not "`.eio` does not survive" but **"the director was reading the wrong
corpus"**. The `%TEMP%\ubem_e02_harvest` harvest has `.eio` in 145 of 40,800 dirs (0.36 %); the
**adopted run at `evidence/open48_refleet4/` has 8,160 of 8,160 `.eio`, `.err`, `.end` and staged
IDFs — 100 % coverage**, and nobody had read them. This entire pass is built on that corpus. §5 of
the night plan (F1–F13) was written from a census rather than a scout, per the lesson of the previous
pass.

**Item-by-item.**

- **OPEN-56 — now measured exactly, fleet-wide, and mechanistically localised.** All 8,160 `.eio`
  parsed, 46,127 zones. **42,269 zones (91.64 %) carry `Volume` written as literally 10.00**;
  **8,159 of 8,159 buildings (100 %) have at least one stubbed zone**; 7,769 (95.22 %) have every zone
  stubbed. Fleet built volume **11,477,578 m³** against an expected **85,704,214 m³** — ratio
  **0.133921**. ⚠️ The register's previous "8,160/8,160" phrasing is corrected: there are **8,159
  distinct buildings** in the zone census (one `_part0`/`_part1` pair merges).
  **Director extension, reproduced independently:** the stub is deterministic by zone role —
  `WHOLE` **100 %** stubbed (22,562/22,562), `PERIM*` 95.75 % (19,707/20,581), `CORE` **0.00 %**
  (0/2,984) — and all 3,858 non-stubbed zones sit within 1 % of `floor_area × ceiling_height`. The
  writer is correct whenever it fires; it never fires for a `WHOLE` zone. **OPEN-56 is one code path,
  not a data-quality spread.**
- **OPEN-38 — the volume/failure question is answered, and the answer is negative.** At full
  coverage, "any zone stubbed" is **100 % in all three groups** (7 fatal / 16 non-converging / 8,143
  remainder). A constant cannot discriminate anything. **This supersedes the 23-of-44 partial-coverage
  result of the previous pass**, and the ⚠️ caution issued at CP-C is **discharged**.
- **OPEN-09 / OPEN-45 — the adopted run's own error census reproduces the register.** 8,160/8,160
  `.err` read with no shortfall. `Inside surface heat balance did not converge` = **16 of 8,160**,
  exactly as the register holds. Fatals on the two-space marker = **7**; severes = 110; warnings
  339,168.
- **OPEN-62 — this is the largest lever on the headline found in either pass, not a bookkeeping
  detail.** Denominator-only sensitivity, energy held fixed, no re-simulation: baseline
  `auto_storey_count` reproduces the pinned fleet denominator to **−0.053 %** (24,320,581.9 against
  24,333,586.4 m²), while the three `layout_assign_*` definitions build denominators **48–65 %
  smaller**, moving pooled EUI from **153.91** to **236.30**, **296.27** and **442.24** kWh/m². A
  **~2.9× swing in the headline from the definition of a storey alone.** Re-derived independently by
  the director; all four figures match. Combined with the earlier finding that no definition agrees
  with `auto_storey_count` more than 40 % of the time, **the ruling is the user's and it is expensive.**
- **OPEN-53 — the residual after elevators is small and extremely concentrated.** Pooled residual
  (`gap − elevators`) = **+0.3118 kWh/m²** over 8,153 = **0.203 %**. But **9 buildings carry 50 % of
  the absolute residual mass, 26 carry 80 %, 41 carry 90 %.** Outliers (`|resid| > 10`) are 639 of
  8,153 (7.84 %) and track `OpenUBEMUnknown` archetype (613 of 650 Unknowns are outliers, 94.3 %),
  `single_zone` zoning (15.3 % vs 2–3 % for other strategies), and `VINTAGE_NAN_PERMISSIVE_DEFAULT`.
  Largest single contributor is `relation/7480583` — the same building OPEN-35 flags.
  **A flat fleet-wide adjustment cannot close this.**
- **OPEN-35 — the fallback's guess was actually built, and the CP-B basis conflict is resolved by
  measurement.** All 39 have a readable `.eio`; 38 of 39 simulated. For `relation/7480583`
  (`austin_centre`): the model built **45 zones across 45 distinct storey levels, summing to
  301,996.35 m², max Z 157.5 m** — matching the 45 storeys the fallback assigned, with no discrepancy.
  This settles the conflict recorded at CP-B of the previous plan: published 301,996.35 m² is the
  **simulated** area; the script-recomputed `footprint × storeys` value of 242,204.26 m² was the wrong
  basis. **The −3.21 % denominator delta stands, now on measurement rather than inference.**
- **OPEN-17 — the biggest hole has no source, and that is the finding.** `levels` is needed by
  **7,719 rows (94.6 % of the fleet)** and **0 of them carry any levels-related OSM tag** anywhere in
  `surplus_tags` or plausible alternate columns. **Wiring cannot fix it; only a new data source can.**
  The other four targets (`function_tag`, `postcode`, `building_tag`, `height_m`) trickle at
  0.02–1.80 % of their needs-value populations. `geometry` needs nothing.
- **OPEN-14 — the ≈2,352 extrapolation is qualified, not replaced.** The three 100 %-null cells that
  carry **72.4 %** of the height gap are *measurably less similar* to the `nyc_centre` donor
  population than the fleet average (composite distance **0.839 vs 0.723**), and `nyc_suburban` —
  **56.6 %** of the null-height total by itself — is the most dissimilar of all eleven cells. The
  figure therefore **leans upper-bound**. No new point estimate was fabricated, correctly.
- **OPEN-19 — decomposed, with a basis caveat.** Shift-share on the matched 15-archetype set: the
  LA−Austin gap **−25.85** and LA−NYC gap **−43.68** both close to floating-point. ⚠️ **The reported
  28.5/71.5 and 15.3/84.7 mix/intensity splits fold the interaction term into intensity.** Held out
  separately: LA vs Austin = mix −7.37 / intensity −11.12 / **interaction −7.36**; LA vs NYC = mix
  −6.69 / intensity −22.69 / **interaction −14.29**. The interaction is 28 % and 33 % of the two gaps,
  so **the split is convention-dependent** — on a three-term basis mix carries **39.9 %** of the
  LA-vs-Austin gap, not 28.5 %. **Direction survives either convention**: intensity outweighs mix in
  both comparisons. Matched-set pooled figures (Austin 154.94, LA 129.09, NYC 172.77) differ from the
  full-population 161.00/128.13/165.27; **LA is lowest under both**. Still explicitly **not** a
  refutation of the historic sim-vs-measured **+38.8 %**.

**The 153.8231 loose end is now a definite negative, not an open question.** T01 tested every row-set
filter, every rounding precision 0–5 dp, all five other `evidence/open48_refleet*` directories, **and
the restatement doc's own cited provenance path** (`%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\`,
still on disk). Every one of them returns **153.8304**; the provenance path returns it on an identical
sorted `osm_id` set. **Nothing on disk reproduces 153.8231.** The gap is 0.0073 kWh/m² (0.005 %) and
changes no conclusion anywhere. **The adopted baseline is unchanged at 153.8231 pooled over 8,153** —
but whoever next touches the fleet numbers must know it is not recoverable from the record's own
cited source, and must not silently round it away.

**Process findings.** (1) Four executors appended ten entries to one plan doc concurrently with **zero
collisions** for the second pass running — the re-read-before-append rule works and is reusable.
(2) For the second pass running, **the load-bearing corrections came from the director's own
re-derivation, not from a checking agent** — T02's zone-role mechanism and T10's interaction term were
both invisible in the executor reports and both changed how the result should be quoted. (3) The
previous pass's lesson held: writing §5 from a census instead of a scout produced thirteen facts of
which **none** was contradicted by execution.

### Amendment — 2026-08-21 (late night) — `implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md` — **the arc's first remediation plan**

**This is the entry where the register moves.** Three consecutive passes had left it at 16 live, and
that was structural rather than accidental: each was a measurement plan, and the project's own rule —
*no fixes in a measurement task* — meant none of them **could** close anything. Read side by side,
none of the sixteen statuses still said "unknown". They were answered questions waiting on decisions
nobody had asked for.

**Four questions were put to the user and all four were answered.** R1 storey definition — *check
against real storeys first*. R2 OPEN-56 / OPEN-60 fixes — *both, plan then execute*. R3 closures —
*close OPEN-09, OPEN-10, OPEN-14, OPEN-18*. R4 district heating — *measure the 116 first*.

#### What changed in the register

**16 live → 12. 46 retired → 50. 12 + 50 = 62, no gaps.** Sections and closing notes in §6; the
surviving facts from all four closures are carried into OPEN-38, OPEN-03 and OPEN-17 by the
**Handoffs** section immediately before this one.

#### R1 — the biggest reported result of the previous pass is RETRACTED, and that is the good outcome

The night pass had reported the denominator as **"a choice, not a fact"** worth a **~2.9× swing**
(153.91 → 236.30 / 296.27 / 442.24) and called it *"the single most expensive question on this board,
no further measurement will settle it"*. **The user declined to rule and asked for reality instead.**

`source_storey_count` — the real storey count — was already present for all 8,160 rows in
`open03_storey_census.csv`, generated the day before, and had never been compared against.

- `auto_storey_count` (**adopted**) agrees with reality on **8,153 / 8,160 = 99.91 %** and builds a
  denominator **identical to reality's**: 23,849,281.2 m² both.
- `layout_assign_storey_count` agrees on **39.78 %**, **undercounts on 4,670** buildings, and its
  agreement collapses to **2.6–9.6 %** for every building over one storey.

**There was never a choice between two defensible conventions — one is right and the other is
broken.** The swing measured `layout_assign`'s error, not the headline's uncertainty. **No denominator
ruling is owed and none should be offered.** The sentence "no further measurement will settle it" was
the most confident claim on the board and **one ten-minute measurement settled it.**

🟢 **The non-circularity was checked before the ruling was written**, because a >99 % agreement rate
is exactly the shape a circular comparison produces: `source_storey_count` is the input data's
`levels`, `auto_storey_count` is parsed back out of the **8,160 built IDFs on disk**. Intention
against artifact.

#### R4 — the 116 have a name, and the remedy is narrow

T04, **director-verified to machine precision — every figure reproduced exactly**: the 116 are
**`SuperTallBuilding` (24) + `TallBuilding` (92)**, one class, lift **70.2×**, **76.7 % of them in
`nyc_centre`**, holding **37.06 %** of analysable fleet floor area on 1.4 % of buildings. Adding DH
for those 116 alone: pooled **152.3017 → 166.0384 (+9.02 %)**.

⚠️ **Two cautions, both raised by the executor and not asked for by the plan.** The 116 is an
**archetype cut, not a rank cut** — a literal top-116 by `dh_total_kwh` gives **77.7 %**, not 70.5 %,
so **never call them "the biggest 116"**. And **29.5 % of fleet DH sits outside the class**,
thin-spread, so remedying the tall buildings **does not retire OPEN-61**.

#### R2 — both authorised fixes are written, and T02 found a better mechanism than the plan predicted

**OPEN-56.** §5 fact 2 of the plan predicted "the writer works whenever it fires; it never fires for
whole-building zones". **The real cause is sharper and the executor was told to stop if it differed:**
`geomeppy`'s core/perimeter path re-derives the core polygon through `Polygon2D.buffer()`, which
calls shapely's `orient(sign=1.0)` **unconditionally**
(`geomeppy/geom/polygons.py:104-113`) — so CORE/PERIM zones get their winding corrected **as a side
effect**. The `by_storey`/WHOLE path (`geomeppy/idf.py:263-267`) uses the **raw, unoriented footprint
coordinates** and never touches that correction. **That is why CORE is 0.00 % stubbed and WHOLE is
100.00 %** — it was never a writer that "fails to fire", it was an accidental correction on one path
only.

`BuildingIDF.build()` now calls `_write_zone_volumes()`, setting each zone's `Volume` explicitly to
`floor_area × height_m`. 🔵 **A trap the executor avoided and reported:** floor area is summed from
each zone's own `FLOOR` surfaces in the built IDF, **not** from the zones-dict `floor_polygon`, which
CORE/PERIM zone dicts **share as the whole-building placeholder footprint** and would have given the
wrong area for exactly the zones that were previously correct.

**OPEN-60.** `parse_eio_zone_multipliers()` reuses the existing `.eio` route's own constants — not a
second reader, as the plan required — and `_compute_eui()` now scales each zone's lighting and
equipment kWh by its own `Zone Multiplier × Zone List Multiplier` before summing. Unknown zone → 1.0;
empty map → **bit-identical to pre-OPEN-60 behaviour**, so no new failure mode.

⚠️ **The n=48 reconciliation could NOT be re-run, and the executor said so plainly instead of
inventing a number.** Those `.sql` files do not survive on local disk — they went in the same
2026-08-20 W9 prune recorded under OPEN-53. **"6 of 48 within 2 %" therefore still stands as the last
measured value and has NOT been re-measured after the fix.** Re-measuring needs a re-simulation of the
48-building sample. **Do not report the fix as verified against that sample.**

⚠️ **Neither fix has been through EnergyPlus.** Both are verified by unit test and by construction.
The OPEN-56 treatment's energy effect is already measured independently (≈ +1.0 kWh/m², 69 buildings,
70/70 → 0/70 warning clearance), but **no adopted number is restated by this plan and 153.8231
stands.**

#### 🔴 Process — three findings, and the first is about the director

1. **A closing note that hands work to another item is a promise, and it was nearly broken.** Four
   closing notes said what "survives" and named receiving items. On checking, **`E-LA-17` appeared
   nowhere in this book outside the closing note claiming it now lived in OPEN-38** — the note was
   false at the moment it was written. The **Handoffs** section now carries all ten surviving facts
   into OPEN-38, OPEN-03 and OPEN-17. **Rule: never write "this survives in OPEN-NN" without putting
   it into OPEN-NN in the same edit.**
2. **Both code executors stalled in the same documented way** — each parked waiting for a background
   `pytest` to notify it, which never happens. Both had already written their fix, their test, their
   `FIX_*.md` and their debug-reference entry; **only the §8 progress entry was missing**, and the
   director wrote those two entries instead. This is the known "executors block on disk artifacts"
   failure. **Tell code executors to run the suite in the foreground.**
3. **The director over-claimed and corrected it before acting.** The summary that opened this pass
   said "seven items are probably closable". On reading the seven, **only two were cleanly closable**;
   two more needed a user ruling and three had real work left. The user was given the honest count.

#### An archived duplicate, and a register row that was wrong about it

`PLAN_ten-live-items-2026-08-21.md` and `PLAN_ten-live-items-2026-08-21-night.md` were archived to
`implemenation/previous/`, **with the mandatory sweep in the same pass — 19 references repaired
across 15 files**, then verified clean. ⚠️ **A byte-identical duplicate of
`PLAN_open61-census-open03-storeys-2026-08-20.md` was found sitting in the live folder while §1 of
this register claimed all three earlier plans were "closed and archived".** An earlier archive had
copied instead of moved. Deleted after confirming the two copies were identical. **Archiving is `mv`,
never `cp`, and the count in the live folder is the check.**

**`implemenation/` now holds exactly one plan.**

### Amendment — 2026-08-21 (late night, CP-1) — the suite baseline is restated, and a count is replaced by a list

**New baseline: `pytest -q tests/` → 1,927 passed, 55 skipped, 0 failed** (28m17s). The previous
statement, **1,918 passed / 56 skipped**, is superseded. `+9` passes = the 8 tests T02 and T03 added,
**plus one test that used to skip and now passes**.

🔴 **Which test flipped cannot be recovered, and that is the finding worth keeping.** Every
restatement of this baseline in either book recorded **a count and never a list**, so there is nothing
to diff against. No skip marker changed under `tests/` (`git diff HEAD -- tests/` is clean of them);
the flip is environment-driven — a file that happened to be on disk this time. **The 55 skip reasons
are now enumerated in §9 of `implemenation/previous/PLAN_rulings-and-fixes-2026-08-21.md`, and that table, not
the number, is the baseline from here on.**

⚠️ **A reported number arrived with a wrong explanation attached.** T03's progress entry gives
`1,925 / 55` and attributes the delta to "T02's concurrent work landing in the same run". The counts
refute it: baseline total 1,974; T03's run 1,980 (**+6 — T03's own six, none of T02's two**); the
clean run 1,982 (**+8**, both files present). The diligent-sounding explanation would have buried the
real change. **Check a delta against the counts before accepting the story that comes with it.**

#### What this changes for OPEN-17 — it blocks 15 tests, not 10

OPEN-17's row records that it inherited **10** residual skips from OPEN-13 in
`tests/test_draw_methods.py`. The enumeration shows the true figure is **15**: those 10, **plus the 5
in `tests/test_debias.py`**, whose skip reason names OPEN-17 explicitly —
*"`config.IMPUTE_DEBIAS_NEWERSKEW` was never shipped… wiring it is a promotion decision reserved to
the user (OPEN-17)"*. The five were never counted against the item. **OPEN-17 is the single largest
block of dormant coverage in the suite, and its cost was understated by half again.**

🔵 **The rest of the skips are not live debt.** 31 of the 55 (`test_v19_*`, `test_impute_montage`) are
artifact-missing skips pinned to **OPEN-44, which was closed and its ID retired on 2026-08-13** — the
directories are generated outputs never checked in, so those tests are permanently dormant by design,
not blocked. The remaining 9 (`test_service_loads`, `test_plotting_suite`) depend on runtime cell data
and are the family the 56 → 55 flip almost certainly sits in.

**Net: of 55 skips, exactly 15 are waiting on a live decision, and all 15 are OPEN-17's.**


### Amendment — 2026-08-22 — `implemenation/PLAN_open61-dh-remedy-2026-08-22.md` — **the remedy that was called a design question is decided**

**The user's ruling was one word: *"open-61 vas-y"*.** It followed the director's recommendation that
OPEN-61 was the next action because it is **the only remaining item with a measured size**.

#### The register said the remedy was a design question. It is not, and here is why

For two days OPEN-61's row has ended *"any remedy must either request the meter in the IDF … or
read ABUPS as a second differently-shaped source of truth inside the parser. **Both are design
decisions and neither is taken.**"* Both were decidable on evidence already on disk, and neither had
been checked.

- **Shape (a) — request a `DistrictHeating` meter in the IDF — fixes nothing that exists.**
  `dh_b_available` is **True on 0 of 8,152** rows of `open61_census_fleet.csv`: not one simulated
  building in the fleet carries a district-heating meter, and the reader's own docstring recorded the
  same finding independently. Shape (a) would change what every *future* run emits and leave all
  **121.9 GB** of existing results unfixable.
- **Shape (b) — read ABUPS inside the parser — is not the novel step the row implies.**
  `check_building_integrity()` at `parser.py:693-702` **already issues an ABUPS
  `TabularDataWithStrings` query**, and has since Phase-E §5.1 P5. The objection described
  something the parser has been doing all along.

**Shape (b) is adopted as the fix. Shape (a) is recorded as an improvement, not rejected as an idea**
— it would give a second independent source and let the integrity gate cross-check the ABUPS
read, and it is out of scope only because it fixes nothing already on disk.

#### 🟢 The attribution question that everyone expected does not exist

The obvious risk in folding district heating into the ten end uses was deciding **which** end use it
belongs to. Measured, not assumed, over the 8,152 `ok` census rows:
Σ`dh_water_systems_gj` = **1,694,992.3 GJ**, Σ`dh_total_gj` = **1,694,992.3 GJ**,
Σ`dh_other_rows_sum_gj` = **0.0**. **100.00 % of the fleet's district heating is Water Systems.**
There is no heating/cooling split to rule on. It is DHW, and it goes into `dhw_eui_kwh_m2`.

#### 🟢 The concentration finding was read backwards, and correcting that is what unblocked this

T04 of the previous plan found that **116 buildings carry 70.5 %** of the term, and the board read
that as making the remedy harder. **It does the opposite.** That result rules out exactly one remedy
shape — applying 19.47 as a flat offset — and a per-building ABUPS read is the shape that
never wanted a flat offset. Each building gets **its own measured value**; a building with no
district heating reads 0.0 and does not move. **Concentration is irrelevant to the correctness of
this remedy.** It stays relevant to how the result is *reported*, which is why T03 must publish the
per-cell and per-archetype split rather than a single number.

#### 🟢 And no re-simulation is needed, which is the whole reason this is affordable

The row warned that sizing this needs "a re-simulation, not a re-read". It was re-simulated on
2026-08-20 and **the corpus was preserved under ruling R6**: **7,861 `.sql`, 121.9 GB, 12 cells** at
`C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20`, director-verified by re-count on
2026-08-22. The fix can therefore be **proven against real simulation output** rather than against
synthetic fixtures alone. ⚠️ **7,861 against 8,152 census rows — the corpus is 96.4 %
of the fleet, not 100 %**, and the validation task must say so.

#### The size, re-derived by the director for this plan

Over the n = 8,144 rows carrying both a parsed total and a DH value, weighted by floor area: pooled
**152.3011 → 171.7718 kWh/m²**, **+19.4707 = +12.78 %**.
⚠️ **152.3011 is the census rebuild's pooled figure, NOT the adopted 153.8231**, which is
run 4's over a different 8,153-building population. **The two must never be differenced.**
🔴 **No fleet figure is restated by this plan.** T03 produces a *candidate* and CP-2 carries
it to the user; adoption is a ruling, not an executor's output.

#### ➕ OPEN-63 opened in the same edit, because the fix makes a pre-existing gap visible

Designing the fix answered a question nobody had asked: **if energy rises 12.78 %, what does carbon
do?** Nothing. `carbon.py:106` builds the DHW carbon term from the two fuel columns only and never
from `dhw_eui_kwh_m2`, and `config.py:83` holds the only fuel factor in the codebase — there is
**no district-heating factor at all**. **The gap is pre-existing; the fix only makes it legible.**
Opened as **OPEN-63** with its own §6 section, in the same edit that discovered it, per the rule
written after the previous pass. **13 live / 50 retired / 63 total, next free `OPEN-64`.**

#### Housekeeping done in this pass

`PLAN_rulings-and-fixes-2026-08-21.md` was **archived to `implemenation/previous/` with its mandatory
citation sweep in the same pass** — 15 references located, the 6 path-qualified ones repaired,
0 left unswept, verified by re-grep. **`implemenation/` again holds exactly one plan.**


### Amendment — 2026-08-22 — **the OPEN-61 fix was wrong on its first attempt, the suite caught it, and that is worth more than the fix**

**What happened, in order.** T01 of `PLAN_open61-dh-remedy-2026-08-22.md` was executed exactly as
written and the full suite came back **3 failed / 1,933 passed / 55 skipped** against a
**1,927 / 55 / 0** baseline. The three failures were
`tests/test_results_parser.py::TestEuiGolden::test_r{1,2,6}_total_eui`. **The `heating`, `cooling`
and `lighting` tests on the same three fixtures all passed** — only the *total* moved, which is
the signature of energy being **added**, not of a component being recomputed.

**The cause was in the plan, not in the execution, and that is recorded here deliberately.** T01
step 2 instructed the executor to read `RowName='Total End Uses'`, verbatim, and the executor did.
The correct row is `'Water Systems'`. The director wrote the wrong instruction on the strength of
fact F3 — *"100.00 % of fleet district heating is Water Systems"* — which is a true
statement **about the fleet** that was silently used as a statement **about the code**. Corrected as
task **T01b**; F2 corrected in place; F3 narrowed; **F11 added** with both populations measured.

**The arithmetic closes to the last digit, which is why no further investigation was spent.**
`r1_single_zone.sql` carries `Heating` 148.24 GJ and `Water Systems` 0.00 GJ.
148.24 × 277.7778 ÷ 392 m² = **105.0456 kWh/m²**. The test reported 276.9193
against an expected 171.8739 — a difference of **105.0454**. R2 and R6 close identically. **The
diagnosis cost one sqlite query and one division.**

🟢 **No number moves, and this was measured rather than hoped.** Over the 8,152 `ok` census
rows, `max |dh_total_gj − dh_water_systems_gj|` = **0.0** and **0 rows** carry a
non-Water-Systems district-heating row — **per building, not in aggregate**. So T01b changes no
fleet result, **F7's 152.3011 → 171.7718 stands**, and **T02's corpus validation did not have to
be re-run**, which saved the pass.

➕ **OPEN-64 opened in this same edit** — the 13 unread district-heating rows, with the
golden fixtures as measured evidence and the fleet exposure measured at zero.
**14 live / 50 retired / 64 total, next free `OPEN-65`.**

**The lesson, stated plainly because it will recur.** *A measurement over the production fleet is
evidence about the production fleet. It is not evidence about the test corpus, and the test corpus is
what gates every merge.* F3 was measured honestly, cited honestly, and still produced a wrong
instruction, because nobody asked **"is the fixture population like the fleet population?"** That
question is now worth asking of every fact in every plan of this arc that was measured on the census.
