# PLAN — OPEN-62 Z_Origin fix + three rulings (OPEN-15/16/17, OPEN-27)

**Slug:** `open62-z-origin-and-three-rulings`
**Date opened:** 2026-08-20 (afternoon)
**Author:** director session (manager). Executor tasks are for a fresh Sonnet.
**DESIGN pointers:** none of this plan changes a DESIGN doc. The two OPEN-27 edits are the user's,
in `docs/docs_main/`, and are explicitly outside every executor's reach.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` — §2 (the 19 live
items), §4 (priority order), §6 OPEN-62 at :399-472.

> **Status:** ✅ **CLOSED 2026-08-21.** T01, T02, T04, T05, T06, T07 complete and logged in §8.
> **T03 was replaced, not executed** — see the ruling at the end of the T02 entry (§8, "T03 is
> replaced, not executed"). **Archived to `implemenation/previous/` on 2026-08-21**, together
> with `PLAN_open61-census-open03-storeys-2026-08-20.md`, which ran beside it and also closed.

*(Historical note, kept as written: while this plan was live, two plans were in force at once,
deliberately. `PLAN_open61-census-open03-storeys-2026-08-20.md` was still running its T03 fleet
census locally at 12 workers. Neither plan was archived until both closed. This plan existed
because every task in it was CPU-cheap and needed no EnergyPlus, so it could run beside the
census instead of behind it.)*

**Why this plan exists.** The user asked, on 2026-08-20, what could move in parallel with the census
and ruled on four questions the same afternoon. Those rulings are §4 below. This plan executes them.

---

## 2. Hard rules for the executor

1. **You are the executor, not the planner.** Execute T01 then T02 in order. Do not propose
   alternatives, do not re-scope, do not skip a control. If this document is ambiguous, **STOP and
   quote the conflicting lines** rather than choosing.
2. 🔴 **RUN NO ENERGYPLUS. NOT ONE SIMULATION.** The machine is saturated: 12 EnergyPlus workers are
   running the OPEN-61 fleet census and will be until roughly 22:00. Everything in this plan is IDF
   text parsing. If a task seems to need a simulation, you have misread it — stop and say so.
3. 🔴 **Do not touch, move, read-lock, or delete anything under
   `openubem/outputs/comparisons/open61_census_fleet*.csv`** or any working directory named
   `open61_census_fleet_work`. That is the live census writing incrementally.
4. **Never overwrite the pre-fix CSVs.** `open03_envelope_decomposition.csv` and
   `open03_storey_census.csv` are the evidence the fix has to be judged against. Write new files.
5. **Never commit.** Git is handled externally by the user. Do not run `git add`, `git commit`,
   `git checkout`, or `git stash`.
6. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first**
   (~200 documented errors). **After solving any error, register it there before closing the task**,
   in the house format, one bullet in the matching chapter. Chapter 16 already holds the `[OPEN]`
   entry for this very defect — when T01 lands, **drop that `[OPEN]` marker**, do not add a second
   entry.
7. **No `.py` files under `docs/`, ever.** Analysis scripts live in `scripts/analysis/`.
8. **Windows:** invoke Python as `py -3`. A bare `python` hits the Store shim. The console is cp1252
   — do not print emoji or box-drawing characters from a script.
9. **`glob` with `**` double-counts this tree** (16,336 against a true 8,160). Walk explicitly.
10. **Append a progress-log entry to §8 of this document per completed task**, in the house format,
    and **stop at the checkpoint** after it. Report, then wait.

---

## 3. File layout

| Path | Role |
|---|---|
| `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` | **T01 edits this.** Holds `parse_idf()` at :117; the defect is at :146 (`wall_z_bases.add(round(min(zs), 1))`) and its consumer at :179 (`storey_count = len(wall_z_bases)`). |
| `scripts/analysis/open03_storey_census_2026-08-20.py` | **T02 re-runs this.** Imports `parse_idf()` unchanged at :104-107 and calls it at :175 and :198. `OUT_CSV` at :89. |
| `openubem/geometry/layout_assigner.py:465-495` | **Reference implementation — read, never edit.** `:471` reads `Z_Origin`; `:491-493` adds the origin back when `coord_sys == "RELATIVE"`. |
| `openubem/outputs/comparisons/open03_envelope_decomposition.csv` | Pre-fix 48-building sample. **Read-only.** |
| `openubem/outputs/comparisons/open03_storey_census.csv` | Pre-fix 8,160-building census. **Read-only.** |
| `openubem/outputs/comparisons/open03_envelope_decomposition_zfix.csv` | **T01 writes this.** |
| `openubem/outputs/comparisons/open03_storey_census_zfix.csv` | **T02 writes this.** |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_storey-census.md` | The predecessor measurement doc. T02 appends; does not rewrite. |
| `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 | Holds the `[OPEN]` entry for this defect. T01 clears the marker. |

---

## 4. Decisions, pinned — the user's rulings of 2026-08-20

These were asked and answered directly. They are not the director's inference and are not reopenable
by an executor.

| # | Question put to the user | **Ruling** |
|---|---|---|
| R1 | OPEN-62 — fix the parser now and re-run the census with a restated C9? | **Fix + restate C9.** Not "fix and keep the old C9", which would leave a control that re-runs the suspect code and calls the result agreement. |
| R2 | OPEN-15 / 16 / 17 — three facets of one fact (imputation tiers built, never wired to the production router). | **Merge into one, retire two.** OPEN-17 is the carrier — it holds the 10 skipped tests. OPEN-15 and OPEN-16 retire into it. Register goes 19 → 17 live. |
| R3 | OPEN-09 / 10 / 14 / 18 / 19 / 38 — measured, remedy never authorised. Retire any? | **None. All six stay live.** The director had recommended retiring 18 and 19; the user declined. Recorded as declined, not as un-asked. |
| R4 | OPEN-27 — two edits in files this session may not touch. | **The user makes both edits; the director verifies and closes.** No exception to the never-edit-DESIGN rule is granted. |

**Two further decisions, director's, pinned so T01 does not have to invent them:**

- **D1 — the fix is additive, not a replacement.** `parse_idf()` returns **both** numbers:
  `storey_count` (corrected, origin-aware) and `storey_count_naive` (the old value, bit-for-bit).
  This is what makes the legacy control checkable in the same run instead of by archaeology, and it
  is why C9a below can exist at all.
- **D2 — the restated C9 must not re-run the suspect code.** The old C9 passed 96/96 because both
  sides were produced by the same naive parser against the same files. The replacement control has
  to come from a reader that never imported `parse_idf()`. `layout_assigner.py`'s own origin-aware
  path is that reader.

---

### R6 and R7 — taken 2026-08-20 (evening), after CP-2

- **R6 — preserve the census `.sql` corpus.** The ≈38 GB written by the OPEN-61 fleet census is to be
  moved out of the ephemeral session scratchpad to a durable path **once the census finishes**, and
  entered in an inventory that is checked rather than written once. Chosen over the cheaper
  "preserve only what is cited" — which is the policy that already failed, because it protects
  answers already given and not the next unasked question. Priced: the last time this corpus was
  discarded it cost **97.2 CPU-hours** to regenerate. ⚠️ **Do not move it while the census is
  running.**
- **R7 — a storey count is to be derived from FLOOR SURFACES.** Count distinct `FLOOR`-surface
  elevations, origin-corrected. This is the independent reader that gave the correct **20** on
  `TallBuilding` where the wall-based method gave 10. Chosen over reusing `compute_band_map()`
  (rejected as too heavy a production dependency for an analysis script, though it remains the
  authority for OPEN-03's untouched 30 / 70 split) and over deferring.

## 5. Facts with citations — verified by the director at HEAD, 2026-08-20

1. **The defect is one line.** `scripts/analysis/open03_envelope_decomposition_2026-08-20.py:146`
   does `wall_z_bases.add(round(min(zs), 1))` over raw wall vertices. The `ZONE` loop at `:122-127`
   already iterates every `ZONE` object but reads only `Name` and `Part of Total Floor Area` — the
   `X/Y/Z_Origin` fields are right there and are dropped.
2. **Production does not share it.** `openubem/geometry/layout_assigner.py:469-471` builds
   `zone_origins[name] = (x0, y0, z0)`; `:491-493` applies
   `world_verts = [(v[0]+ox, v[1]+oy, v[2]+oz) ...]` when `coord_sys == "RELATIVE"`.
   `openubem/viz/geometry_extract.py:143-155` does the equivalent. A repo-wide search finds no third
   production reader that counts storeys from wall Z.
3. **Blast radius, measured zone-by-zone across all 18 baseline-mapped archetypes**
   (register §6, :417-427): severe in `SuperTallBuilding` 232/256, `TallBuilding` 145/164,
   `Outpatient` 59/118, `MidriseApartment` 18/27, `HighriseApartment` 18/27, `SecondarySchool` 21/46
   — **6 archetypes, 2,983 of 8,160 buildings, 36.6 %**. Immaterial in `LargeOffice` (3/23 zones,
   none floor-area-counting) and the two restaurants (1 zone each). Absent in the other 10.
4. **OPEN-03's headline survives it.** 60.8 % disagreement on the 5,177 clean rows against 59.2 % on
   the 2,983 at-risk rows (register §6, :433-436). The gap bounds per-archetype magnitude, not the
   fleet rate.
5. **Why C9 passing was not reassurance** — register §6, :438-442, verbatim: *"A shared parser
   reproducing itself is agreement, not correctness. This is worth carrying past this item: a
   control that re-runs the suspect code cannot exonerate it."*
6. **OPEN-27's two targets, re-verified at HEAD this afternoon.**
   `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`
   and `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78`, each naming
   `MultifamilyHome`. `grep -c MultifamilyHome openubem/data/openstudio_archetypes.json` → **0**.
7. **The code is already pinned against the error** by 3 regression tests
   (`FIX_five-more-items-2026-08-13.md:185-212`), so nothing regresses while the spec waits.

---

## 6. Task list

### T01 — Make `parse_idf()` origin-aware, additively

**What.** In `scripts/analysis/open03_envelope_decomposition_2026-08-20.py`, teach `parse_idf()` to
add each zone's own `Z_Origin` back into its wall vertices before taking the minimum, when the file's
`GlobalGeometryRules` coordinate system is `Relative`. Return **both** `storey_count` (corrected) and
`storey_count_naive` (the pre-fix value), per decision **D1**. Re-run the 48-building envelope
decomposition into `open03_envelope_decomposition_zfix.csv`.

**Why.** This is the whole of OPEN-62. Register §6 :466-468: *"The fix is the four lines
`layout_assigner.py:491-493` already contains."* The additive form is what lets the legacy control
be checked in the same run rather than reconstructed later.

**How.**
1. Read `openubem/geometry/layout_assigner.py:465-495` first and mirror its handling. Do not invent
   a second convention. Note it reads `X_Origin`/`Y_Origin` too — for a storey count only Z matters,
   but read all three so the code reads like the reference.
2. Parse `GLOBALGEOMETRYRULES` from the same block list. The field is `Coordinate System`. Treat a
   missing object as `Relative` **only if** you confirm that is EnergyPlus's default for these files
   — if you cannot confirm it from the IDD or the files themselves, **STOP and report**, do not guess.
3. Extend the existing `ZONE` loop at `:122-127` to also collect `Z_Origin` per zone name, defaulting
   to `0.0` on a blank or missing field, exactly as `:469-471` does.
4. At `:141-147`, compute the wall base twice: `min(zs)` for the naive value and `min(zs) + z0` for
   the corrected one, into two separate sets, each still `round(..., 1)`.
5. At `:179`, return both lengths. Add `storey_count_naive` to the returned dict and to the CSV
   header. **Do not reorder or rename any existing column** — `open03_storey_census_2026-08-20.py`
   consumes this dict by key at `:175` and `:198`.
6. Write to `OUT_CSV` = `open03_envelope_decomposition_zfix.csv`. **The original file is read-only**
   (hard rule 4).
7. Clear the `[OPEN]` marker on the chapter-16 entry for this defect in
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` and extend that same bullet with the fix
   location — do **not** append a second entry (hard rule 6).

**How to test — pre-registered, and a failure here is a finding, not something to reconcile.**
- **C9a — legacy reproduction.** `storey_count_naive` reproduces
  `open03_envelope_decomposition.csv` **exactly, 48/48**. This proves the change is additive and that
  nothing else in the parser drifted. A single mismatch means you changed something you should not
  have — stop and report it.
- **C12 — the mechanism's falsifiable prediction.** Run the corrected parser over all 18
  baseline-mapped archetype IDFs. `storey_count` must differ from `storey_count_naive` **only** in
  the 6 archetypes §5.3 names, and must be **identical** in the other 12. If a 13th archetype moves,
  the mechanism as written in the register is wrong — report that, do not adjust the register.
- Report both as counts with the archetype breakdown, not as prose.

---

### T02 — Re-run the fleet storey census and restate C9

**What.** Re-run `scripts/analysis/open03_storey_census_2026-08-20.py` over all 8,160 buildings with
the fixed parser, writing `open03_storey_census_zfix.csv` carrying both storey columns. Then restate
control C9 as a control that does not re-run the suspect code, and restate OPEN-03's fleet storey
headline on the corrected counts.

**Why.** Ruling **R1**: the fix and a restated C9 land together. Register §6 :466-468: re-running the
census with the fix *"changes what control C9 reproduces"*, so the census and the control move in the
same task or neither moves.

**How.**
1. Point `OUT_CSV` at `open03_storey_census_zfix.csv`. Leave the original in place.
2. Keep every other column and the `layout_assign_z_origin_collapse_risk` flag as they are. Add
   `layout_assign_storey_count_naive` beside the corrected column.
3. **This is single-process IDF parsing. Do not parallelise it beyond one worker** — the census owns
   the other 12 (hard rule 2).
4. Do not modify `open03_storey_census_2026-08-20.py`'s parsing logic. It imports `parse_idf()`
   deliberately (`:102-107`, *"C9 requires byte-identical reproduction, so import rather than
   reimplement"*). That comment is now stale — **update the comment to name this plan and R1**, and
   change nothing else about the import.

**How to test — pre-registered.**
- **C8 (carried)** — row count is **8,160**; the per-cell n sums to 8,160.
- **C9a (carried from T01, at fleet scale)** — `layout_assign_storey_count_naive` reproduces the
  pre-fix `open03_storey_census.csv` **exactly, 8,160/8,160**.
- 🔴 **C9b — the restatement, and the point of the whole task.** Check the corrected storey count
  against a reader that **never imported `parse_idf()`**: `layout_assigner.py`'s own origin-aware
  path (`get_registry` / `compute_band_map` / `match_storeys`, already imported by the census script
  at `:112`). Report the agreement rate over the 18 baseline-mapped archetypes and the disagreement
  list. **This control is allowed to fail.** If it does, that is the finding — an independent reader
  disagreeing is exactly the evidence the old C9 could never produce. Do not reconcile it silently
  and do not tune the parser until it agrees.
- **C12 (carried)** — at fleet scale: which archetypes moved, by how much, and did the 12 unaffected
  stay at delta 0.
- 🔴 **C13 — restate OPEN-03's published storey headline.** The register currently publishes
  *"`layout_assign` represents the real storey count for 2,446 (30.0 %) and ignores it for 5,714
  (70.0 %), the unmatched buildings averaging 3.12 real storeys (max 105) rendered at 1.21 (max 6)."*
  Recompute all six of those numbers on the corrected counts and **state the movement explicitly —
  old number, new number, delta.** If the headline barely moves, say so plainly; that is a result.
  If it moves a lot, say that plainly too. **Do not edit the register** — report the numbers and let
  the director restate them.

⚠️ **What you may not do in T02.** Do not change any production code. Do not re-run any EnergyPlus
simulation to "check" a storey count. Do not delete or overwrite the pre-fix CSVs. Do not close
OPEN-62 — closing an item is the director's, on the user's grant.

---

### T03 — Close OPEN-62 in the record *(director)*

**What.** On C9a/C9b/C12/C13 passing audit: amend register §6's OPEN-62 section with the fix, the
restated control, and the C13 movement; move OPEN-62 to closed in §2 and §4; update
`reporting/board_open-items.html`, the board artifact, `prompts/DIRECTOR_PROMPT_openings.md` and
`docs/PROJECT_CHECKLIST.md`; append to `extra/MEASUREMENT_open-03_storey-census.md`.

**Why.** An item is not closed until every surface that tracks it says so — the archiving rule's
citation-sweep discipline applied to a close.

**How to test.** `grep -c "OPEN-62"` across the four tracking surfaces returns a hit in each, and
the live-item count is consistent everywhere.

---

### T04 — Execute ruling R2: merge OPEN-15 and OPEN-16 into OPEN-17 *(director)*

**What.** Retire OPEN-15 and OPEN-16 into OPEN-17 as the carrier. Strike their §2 rows the way
OPEN-12/13/20 were struck — **left visible, not deleted** — with the ruling, its date, and the fact
that it was the user's. Rewrite OPEN-17's row so it carries all three facts: Phase-E imputation was
documented-deferred and no code path exists (ex-15); the `ml` tier is reachable only from the
validation entry point (ex-16); the draw tier's router hook has never existed in any commit, and 10
tests in `tests/test_draw_methods.py` unskip themselves the day it does (17's own).

**Why.** Ruling **R2**. Three register rows describing one unwired router is three chances to
re-litigate the same decision. One row with three facts is one.

**How to test.** Live count reads **17** everywhere: register §1, §2 heading, board HTML, artifact,
checklist. `grep -n "OPEN-15\|OPEN-16"` on the register shows struck rows plus the ruling, never a
deletion.

---

### T05 — Execute ruling R4: verify and close OPEN-27 *(director, gated on the user)*

**What.** The user makes two edits. The director verifies and closes.

**The two edits, exact.** In both, replace `MultifamilyHome` with `HighriseApartment`:

1. `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`
   `- **residential** ⇔ `sector == "Residential"` (2 archetypes — MidriseApartment, MultifamilyHome)`
2. `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78`
   `- residential ⇔ archetype's `sector == "Residential"` per `openubem/data/openstudio_archetypes.json` → exactly **2 archetypes**: `MidriseApartment`, `MultifamilyHome`.`

**Why.** Ruling **R4**, and §5.6: the JSON has 0 occurrences of `MultifamilyHome` while its two
Residential-sector archetypes are `MidriseApartment` and `HighriseApartment`. The spec defines the
coarse accuracy metric against an archetype the project does not have.

**How to test.** `grep -rn "MultifamilyHome" docs/docs_main/` returns **0**. Then
`py -3 -m pytest -q tests/ -k "multifamily or coarse"` stays green — the 3 regression tests pin the
code against the error and must not move.

---

### T06 — Derive `storey_count` from floor surfaces *(executor, ruling R7)*

**What.** In `scripts/analysis/open03_envelope_decomposition_2026-08-20.py::parse_idf()`, add a
third storey measure derived from **`FLOOR`-surface elevations**, origin-corrected exactly as the
wall path already is. **Additive, like T01 was:** keep `storey_count` and `storey_count_naive`
untouched and add `storey_count_floor`. Do not delete or repoint anything.

**Why.** C9b established that the existing `storey_count` counts *the heights at which a new
exterior wall starts*, which undercounts any facade spanning several floors — `TallBuilding` reads
10 against a true 20. R7 rules that a storey is a floor.

**How.** Mirror the existing origin handling (`GLOBALGEOMETRYRULES` `Coordinate System`, each
`ZONE`'s `X/Y/Z Origin`). Apply the **same zone filter the wall path uses** so the two are
comparable, and **report separately** what the count would be without that filter — CP-2 measured
20 floor bands unfiltered against 10 filtered exterior-wall bases, and the filter's contribution
must not be silently folded in.

**How to test — pre-registered, write them down before running:**
- **C14** — `storey_count_floor` reproduces the independent reader on all 18 baseline archetypes:
  `TallBuilding` **20**, `SuperTallBuilding` **30**, `Warehouse` **1**,
  `FullServiceRestaurant` / `QuickServiceRestaurant` / `SmallOffice` **2**. Report N/18.
- **C15** — `storey_count` and `storey_count_naive` are **byte-identical** to their T02 values on all
  8,160 rows. This task adds a column; it changes nothing.
- **C16** — `storey_count_floor >= storey_count` on every row. ⚠️ **This is allowed to fail.** If any
  row goes the other way, report it with the `osm_id` and stop — it would mean the undercounting
  story is incomplete, which is worth more than a clean pass.
- **C17** — restate C13 with `storey_count_floor`: built mean and built max, stated as **values**
  this time, against the lower bounds ≥ 2.25 and ≥ 16.

⚠️ **What you may not do.** Do not change production code. Do not run EnergyPlus. Do not modify
`storey_count` or `storey_count_naive`. Do not touch `open61_census_fleet*`. Do not close OPEN-62.
Do **fix** the stale "KNOWN CAVEAT ... NOT fixed here" paragraph in
`open03_storey_census_2026-08-20.py`'s module docstring, which is now wrong twice over.

### T07 — Preserve the census corpus *(director, ruling R6, gated on the census finishing)*

**What.** Once `open61_census_fleet.csv` reaches its final row count, move the fleet census work tree
out of `%LOCALAPPDATA%\Temp\claude\…\scratchpad\open61_census_fleet_work` to a durable path, and
record it in an inventory with its size, date and what it is for.

**Why.** R6. The previous corpus's deletion cost 97.2 CPU-hours to undo.

⚠️ **Not before the census finishes** — the run is still writing into that tree.

## 7. Stop-and-report points

| CP | After | The question it answers |
|---|---|---|
| **CP-1** | T01 | Is the fix additive — does the legacy value still reproduce 48/48 — and does the mechanism's 6-vs-12 prediction hold? |
| **CP-2** | T02 | Does an **independent** reader agree with the corrected count, and how far did OPEN-03's published headline move? |
| **CP-3** | T03–T05 | Is the record consistent: OPEN-62 closed, 15/16 merged into 17, OPEN-27 closed, live count 16 everywhere? |

---

## 8. Progress log

*(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then Artifacts /
Deviations / Test status / Notes.)*

#### T01 — Make `parse_idf()` origin-aware, additively — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` — `parse_idf()` (:117-224) now
  reads `GLOBALGEOMETRYRULES`' `Coordinate System` and each `ZONE`'s own `X/Y/Z Origin`, mirroring
  `layout_assigner.py:465-495`; wall-base Z is computed twice into `wall_z_bases_naive` (untouched)
  and `wall_z_bases` (+ `Z_Origin` when `coord_sys == "RELATIVE"`), returned as `storey_count_naive`
  and `storey_count`. `OUT_CSV` repointed to `open03_envelope_decomposition_zfix.csv`;
  `PRE_FIX_CSV` constant added pointing at the original (never opened for writing).
- `openubem/outputs/comparisons/open03_envelope_decomposition_zfix.csv` — written, 96 rows (48
  buildings × 2 arms), header carries `storey_count_naive` appended after `storey_count`, no
  existing column reordered or renamed.
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 — `[OPEN]` marker dropped from the
  Z_Origin bullet; same bullet extended with the fix location and the C9a/C12 result (no second
  entry added).
- Pre-fix files untouched: `open03_envelope_decomposition.csv` mtime unchanged (11:31, before this
  task ran) against the new zfix file's 16:46.

**Test status.**
- **C9a — 96/96 arm-rows (48 buildings × 2 arms) reproduce exactly, 0 mismatches.** (The plan's
  "48/48" refers to the building sample; the CSV itself carries one row per arm, 96 total — both
  arms checked, all exact.)
- **C12 — did NOT fully hold.** Ran the corrected parser directly on the 18 baseline archetype IDFs
  already sitting in this session's scratchpad (`open03_proto_saved/`, geomeppy-resaved copies from
  the T05/census work, vertex-comment format already matches this parser's regex). Only **4 of the
  6** register-named archetypes move at the whole-building `storey_count` level:
  `HighriseApartment`, `MidriseApartment`, `SuperTallBuilding`, `TallBuilding`. `Outpatient` and
  `SecondarySchool` hold at delta 0 despite their severe zone-level counts (59/118 and 21/46 zones).
  Traced directly, not assumed: both archetypes mix encodings — some zones on a given floor bake
  their elevation into wall vertices directly, others carry it in `Z_Origin` with local vertices:
  the `Z_Origin`-corrected band for the affected zones lands on a floor-band already present in the
  naive set from the directly-baked zones on the same floor, so the building-level distinct-band
  count is unchanged even though the individual zones were misread before the fix. No 13th
  archetype moved; the finding is 2 named archetypes not moving, not an extra one moving. Not
  reconciled and the register is not touched (director's call, T03).
  Full table in the report to the calling session (not duplicated here).

**Deviations.** None from the plan's instructions. One clarification, not a deviation: C9a's unit
is 96 arm-rows rather than 48 buildings, since the CSV always carried one row per (building, arm)
pair — the plan's own §3 table describes the file as "48-building envelope decomposition" but its
own row count was always 96 before this task touched it.

**Notes.** `GlobalGeometryRules` coordinate system confirmed `Relative` in all 48 layout_assign
sample IDFs, all 48 paired auto IDFs, and 17 of the 18 baseline archetype IDFs (`SuperMarket` is
`World` and correctly does not move) — confirmed by grepping the `Coordinate System` field directly
in every file, not assumed. No missing `GLOBALGEOMETRYRULES` object was observed in any corpus
parsed, so the missing-object default (mirrored from `layout_assigner.py:445`'s own `"WORLD"`
default) was never exercised. Stopped at CP-1 per plan; T02 not started.

#### CP-1 — signed 2026-08-20 *(director)*

**Verdict: released to T02.** The fix at `open03_envelope_decomposition_2026-08-20.py:117-224`
mirrors `layout_assigner.py:465-495` including its `"WORLD"` default, is additive, and does not
touch production code.

**What I re-ran myself rather than taking on report** (C12's partial hold is load-bearing for the
control, so the one command was re-run directly, not re-delegated): on the resaved `Outpatient`
prototype, **59 of 118 zones carry a non-zero `Z_Origin`**, distinct values `{0.0, 3.048, 6.096}`,
and `storey_count == storey_count_naive == 3`. `SecondarySchool`: 21/46 non-zero, `{0.0, 4.0}`,
2 == 2. `SuperTallBuilding`: 246/256 non-zero, **naive 1 → corrected 16**. The executor's report
reproduces exactly and its explanation — the corrected band lands on a floor-band the naive set
already held from the directly-baked zones on the same floor — is consistent with the measured
distinct-Z sets.

**C12 is amended, not passed.** The plan predicted 6 archetypes move and 12 hold. The measurement
is **4 move, 14 hold**. `Outpatient` and `SecondarySchool` are misread *at the zone level* and
correct *at the building level* by coincidence of their own mixed encoding. That is a weaker
guarantee than "unaffected" and must not be recorded as one: a building-level distinct-band count
can be right while every zone under it is wrong. **Any future measure that reads storeys per zone
rather than per building will see these two archetypes move.**

🔴 **Limitation found during the audit and not raised by the executor.** `parse_idf()` cannot read
the raw registry IDFs at all — run against
`config.BASELINE_IDF_DIR/ASHRAE901_OutPatientHealthCare_STD2022_Buffalo.idf` it returns **every
area as 0.0 and `storey_count` 0**, because it resolves fields by their `!- field name` comments
and the DOE files do not carry them. C12 therefore rests on **geomeppy-resaved** copies, which
were sitting in an ephemeral agent scratchpad. Those 18 files are now preserved at
`scratchpad/open03_proto_saved/` (32 MB, gitignored) so T02's C12 is reproducible. This does not
weaken C12 — the resave preserves the `ZONE` origins, as the 59/118 count confirms — but it means
**the parser is only valid on resaved corpora, and that was never stated anywhere.** Recorded here
because it would otherwise be rediscovered from scratch.

**C9a accepted at 96 arm-rows**, not 48. The plan's §3 mis-described the file; the file was right.

#### T02 — Re-run the fleet storey census and restate C9 — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open03_storey_census_2026-08-20.py` — `OUT_CSV` repointed to
  `open03_storey_census_zfix.csv`; `PRE_FIX_CSV` constant added pointing at the original (read-only,
  never opened for writing). The stale import comment (predecessor's :102-107) rewritten to name this
  plan and ruling R1. `la_lookup[arch]` now also carries `storey_count_naive` (from `parse_idf()`'s
  new key) and `auto_rows[...]` an internal (non-CSV) `auto_storey_count_naive`, used to derive
  `layout_assign_storey_count_naive` for the 2 no-baseline-fallback archetypes
  (Courthouse/OpenUBEMUnknown), which copy the auto arm's value either way. One new CSV column added,
  `layout_assign_storey_count_naive`, placed beside `layout_assign_storey_count`; no existing column
  reordered, renamed or removed. The pre-existing 48-sample "C9" print block (comparing against
  `open03_envelope_decomposition.csv`) was replaced with the two officially specified controls C9a
  (fleet-scale legacy reproduction) and C9b (independent-reader check) — see Deviations. C12 and C13
  sections added after C11, per the plan's test list.
- `openubem/outputs/comparisons/open03_storey_census_zfix.csv` — written, 8,160 rows, single worker,
  no parallelism added or removed (the script was already single-process).
- Pre-fix files untouched: `open03_storey_census.csv` mtime unchanged (13:45, before this task ran)
  against the new zfix file's 17:02; `open03_envelope_decomposition.csv` mtime unchanged (11:31).
- `openubem/outputs/comparisons/open61_census_fleet*` and `open61_census_fleet_work` — not read, not
  touched, not read-locked.

**Test status.**
- **C8 — PASS.** 8,160/8,160 rows, per-cell sum 8,160.
- **C9a (fleet scale) — PASS.** `layout_assign_storey_count_naive` reproduces the pre-fix
  `open03_storey_census.csv`'s `layout_assign_storey_count` exactly, **8,160/8,160, 0 mismatches**.
  (Cross-check, not a CSV column: `auto_storey_count` also came back **byte-identical for all 8,160
  rows** between the pre-fix and zfix runs — the fix's effect is confined to the layout_assign arm's
  baseline-lookup path, as the module docstring already predicted for the auto arm's own on-disk
  eppy-saved IDFs.)
- **C9b — ALLOWED TO FAIL, and it did.** Corrected `layout_assign_storey_count` (wall-Z bands,
  `parse_idf()`) agrees with `compute_band_map()`'s `n_proto` (FLOOR-surface bands, already
  origin-aware, never imported `parse_idf()`) on **12 of 18 archetypes**. The 6 disagreeing:
  `FullServiceRestaurant` (1 vs 2), `QuickServiceRestaurant` (1 vs 2), `SmallOffice` (1 vs 2),
  `Warehouse` (2 vs 1), `SuperTallBuilding` (16 vs 30), `TallBuilding` (11 vs 20) — covering **3,734
  buildings fleet-wide**. Worked example: `osm_id=way/37546502`, `austin_centre`, `TallBuilding`,
  wall-Z reads 11 storeys, FLOOR-band reads 20. Not reconciled, not tuned. This is a genuinely
  different measured quantity (distinct wall-Z bands vs distinct FLOOR-z bands, and the restaurants /
  SmallOffice disagree by exactly 1 band even with delta 0 in C12, i.e. these are naive-method
  under-counts the Z-Origin fix does not touch because those archetypes' coordinate system is not
  "Relative" or their affected zones are not floor-area-counting), not a residual bug in the T01 fix
  itself — C9a already proves the fix is additive and C12 already proves it is scoped to the 6
  register-named/4-CP-1-amended archetypes.
- **C12 — PASS against the CP-1 amended expectation.** `storey_count` differs from
  `storey_count_naive` in exactly **4 of 18** archetypes — `HighriseApartment`, `MidriseApartment`,
  `SuperTallBuilding`, `TallBuilding` — and is identical in the other **14**, including `Outpatient`
  and `SecondarySchool` (held at building level, per CP-1's amendment). No 13th or 5th archetype
  moved.
- **C13 — restated.** Matched: 2,446 (30.0%) -> 2,446 (30.0%), delta **0**. Unmatched: 5,714 (70.0%)
  -> 5,714 (70.0%), delta **0**. Real mean: 3.12 -> 3.12, delta **0.00**. Real max: 105 -> 105, delta
  **0**. Built mean: 1.21 -> **2.25**, delta **+1.04**. Built max: 6 -> **16**, delta **+10**. The
  match-status split (what fraction of buildings `layout_assign` represents at all) is untouched by
  the fix, because `match_storeys()`'s status depends on `compute_band_map()`, which was already
  origin-aware before this plan — only the *rendered* geometric storey count for the 70.0% unmatched
  population moved, and it moved up, not down.
- **All-zero-area failure mode (CP-1's raw-registry-IDF caveat) — 0 rows.** Verified directly:
  `auto_storey_count`, `layout_assign_storey_count` and `layout_assign_storey_count_naive` all have
  zero rows equal to 0 in the zfix CSV. This script never calls `parse_idf()` on a raw
  `config.BASELINE_IDF_DIR` file directly — the auto arm reads real on-disk eppy-saved IDFs, and the
  layout_assign arm resaves each baseline through `GeomIDF(...).save()` before parsing, exactly the
  geometry-only resave CP-1 requires.

**Deviations.**
1. Replaced the pre-existing 48-sample "C9" check (against `open03_envelope_decomposition.csv`) with
   the two controls the plan's own "How to test" names, C9a (fleet-scale) and C9b (independent
   reader) — plan §6 T02 "How to test" (lines 192-211) lists exactly C8/C9a/C9b/C12/C13, and the old
   block would now compare the *corrected* `layout_assign_storey_count` against the unchanged pre-fix
   env CSV's *naive* 48-sample values, silently "failing" for the 4 moved archetypes without being
   one of the pre-registered controls. Disclosed rather than silently dropped.
2. Left the module docstring's "KNOWN CAVEAT ... NOT fixed here" paragraph (predecessor's original
   text, describing the Z-Origin defect as unfixed) untouched even though it is now stale — plan step
   T02-How-4 (lines 187-190) scoped the comment edit explicitly to the ":102-107" import comment only
   ("change nothing else about the import"). Flagged here rather than re-scoped into a second edit.
3. Did not append to `extra/MEASUREMENT_open-03_storey-census.md`. Plan §3's file-layout table says
   "T02 appends", but §6 T03's own "How" step explicitly assigns that append to the director
   ("append to `extra/MEASUREMENT_open-03_storey-census.md`"). Treated the task-list assignment as
   controlling and left the doc for T03.

**Notes.** Single worker throughout — the script was already single-process (no multiprocessing to
disable). No production code under `openubem/` was touched (confirmed via `git status --porcelain --
openubem/`: no modifications, only pre-existing untracked output CSVs). No EnergyPlus run — the only
IDF mutation is `GeomIDF(...).save()`, a geometry-only re-serialization already used by the
predecessor script. No new error was hit while running this task, so no new
`OpenUBEM_debug_References.md` entry was needed (T01 already dropped the `[OPEN]` marker on the
relevant chapter-16 bullet). Stopped at CP-2 per plan; T03 not started.

#### T04 — Execute ruling R2: merge OPEN-15 and OPEN-16 into OPEN-17 — completed 2026-08-20 *(director)*

**Artifacts.**
- `INVESTIGATION_open-items-register-II.md` — §1 counts (19→17 live, 43→45 retired), Live-IDs line,
  Retired-IDs line, the `17 + 45 = 62` invariant, the reconciliation parenthetical, the board line,
  the §2 heading, the *Plans in force* row, the *Rulings owed* row, the OPEN-15/16/17 rows, and a new
  §7 amendment-log entry placed at the top of the log.
- `reporting/board_open-items.html` — OPEN-15 and OPEN-16 cards removed, OPEN-17 rewritten as the
  carrier, both count cards, the h1, the header stamp, the Theme-D count, the footer, and the
  "What is next" list.
- Board artifact republished **in place** at
  <https://claude.ai/code/artifact/7960a833-541b-4eab-a006-403c53c4bddc>.
- `prompts/DIRECTOR_PROMPT_openings.md` — the live 🟩🟩🟩 resume box now carries the second plan, the
  four rulings, the restated-C9 warning and the corrected register state.
- `docs/PROJECT_CHECKLIST.md` — header count corrected and a new dated section appended.

**Deviations.** None from §4 R2. One thing was done that the task did not ask for and it is disclosed
rather than folded in: **the §1 Live-IDs line read `(18)` and omitted OPEN-62**, so it was wrong
before this task touched it. It was repaired and named in three places (§1 itself, the §7 log, the
director prompt) rather than silently corrected, because it is the *second* instance in one day of the
same one-row-short failure — the first being OPEN-61's missing row at the rotation.

**Test status.** Counts re-derived after the edits: live IDs `03, 09, 10, 14, 17, 18, 19, 27, 35, 38,
53, 56, 58, 59, 60, 61, 62` = **17**; retired = **45**; 17 + 45 = **62** = the full sequence
`OPEN-01…OPEN-62`. Board cards enumerate to the same 17. No test suite is involved — no code changed.

**Notes.** The merge is recorded everywhere as **bookkeeping, not progress**. Nothing was measured,
fixed or decided by it, and each of the three facts is preserved verbatim in OPEN-17's row so no
evidence is lost behind a struck row. R3 is recorded as **declined**, not as un-asked: the director
recommended retiring OPEN-18 and OPEN-19 and the user said no, and writing that down is what stops the
recommendation reappearing next pass as if it were new.

#### T05 — Verify and close OPEN-27 — completed 2026-08-20 *(director)*

⚠️ **T05 as written assumed the user would apply the edits (ruling R4). They did not — they granted
a scoped exception instead (R5) and the director applied them.** The task's verification half ran
exactly as specified; only the actor changed. Recorded here rather than silently, because the plan
text still reads "the user applies".

**Artifacts.**
- `docs/docs_main/docs_step2/DESIGN_step-2-classify-…-archetyp.md:529` — `MultifamilyHome` →
  `HighriseApartment`.
- `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78` — same replacement.
- `INVESTIGATION_open-items-register-II.md` — §1 counts (17→16 live, 45→46 retired), Live-IDs line
  (16 IDs, `27` removed), Retired-IDs line (46 IDs, `27` added), the `16 + 46 = 62` invariant, the
  corrections note, the *Rulings owed* row, the §2 heading, the OPEN-27 row (struck, not deleted,
  carrying its own verification), §4 item 7, the R4/R5 entry in §7, and a new §7 amendment entry at
  the top of the log.
- `reporting/board_open-items.html` — OPEN-27 card removed, h1 17→16, both count cards, footer
  source line and footer tally; the "What is next" list gained the OPEN-27 closure **and** the CP-1
  C12 amendment. Republished in place at the existing artifact URL.
- `prompts/DIRECTOR_PROMPT_openings.md` — "Four rulings"→"Five", R4 marked superseded, R5 added with
  an explicit non-generalisation warning, register state restated with the ID list recounted inline,
  plus two new red warnings (C12 amended; `parse_idf()` fails silently to zero on raw IDFs).
- `docs/PROJECT_CHECKLIST.md` — header count and a new dated evening section.

**Test status.**
- `grep -rn "MultifamilyHome" docs/docs_main/` → **0 occurrences** (was 2).
- Residential archetype set re-derived from `openubem/data/openstudio_archetypes.json` → **exactly
  2: `MidriseApartment`, `HighriseApartment`** over 30 total. ⚠️ **The replacement was verified
  against the data, not copied from the item text** — the item asserted the correct name, but an
  item that has been wrong once is not a source.
- `py -3 -m pytest -q tests/ -k "multifamily or coarse"` → **6 passed, 1,968 deselected** (6 + 1,968
  = 1,974, consistent with the 1,918-passed / 56-skipped suite baseline).

**Deviations.** One, stated above: the actor changed from user to director under R5.

**Notes.** The item was open for weeks on a permission, not on a difficulty. It closed in four
minutes once the permission question was put directly. **The generalisable finding is about how the
question was framed, and it is now recorded in three places** (§4 item 7, the §7 amendment entry,
and the checklist) so it survives this plan's archiving.

#### CP-2 — signed 2026-08-20 *(director)* — 🔴 **T03 IS BLOCKED. OPEN-62 DOES NOT CLOSE.**

**Verdict: the plan's remaining task cannot run as written, and that is the correct outcome.**
T03 was "close OPEN-62 in the record". **C9b forbids it.**

### What C9b found

The restated control failed, as it was explicitly permitted to. Agreement **12 of 18** archetypes;
disagreement on 6, covering **3,734 buildings fleet-wide**: `FullServiceRestaurant` 1 v 2,
`QuickServiceRestaurant` 1 v 2, `SmallOffice` 1 v 2, `Warehouse` 2 v 1, `SuperTallBuilding` 16 v 30,
`TallBuilding` 11 v 20.

### The mechanism, traced by the director rather than accepted as a disagreement

Run directly on `scratchpad/open03_proto_saved/TallBuilding.idf`:

| what is counted | distinct elevations |
|---|---:|
| Floor surfaces (the independent reader) | **20** |
| All wall bases | 20 |
| Exterior wall bases | 19 |
| 🔴 **Exterior wall bases in floor-area-counting zones — what `parse_idf()` actually counts** | **10** |

The elevations it finds are `0.0, 4.9, 23.8, 55.3, 72.8, 88.6, 104.4, 118.4, 132.4, 135.9` — these
are the levels at which a **new exterior wall starts**. Between them are floors whose facade belongs
to a wall segment that started lower down. **A curtain wall spanning several floors contributes one
elevation, not several.**

🔴 **Therefore `storey_count` is not a storey count.** It is *the number of distinct base elevations
of exterior walls in floor-area-counting zones*, which happens to equal the storey count only when
every floor starts its own facade. **The `Z_Origin` fix was necessary and is correct; it was not
sufficient.** It removed one error from a quantity that was measuring the wrong thing to begin with.

### Why this vindicates ruling R1 specifically

The old C9 compared the parser against itself and passed **96/96**. Had the plan kept it, T01's fix
would have passed it again, OPEN-62 would have closed today, and the column would have been recorded
as correct while still undercounting `TallBuilding` by **9 storeys out of 20**. **The user's ruling
to restate the control rather than keep it is the only reason this was caught**, and it was caught
by the control's *failure*, not its success. This is the clearest evidence in this arc that a control
which cannot fail is not a control.

### Consequences, binding on whatever runs next

1. 🔴 **OPEN-62 stays open and its scope grows.** It was opened as "an analysis parser omits
   `Z_Origin`" and bounded to a measurement erratum. It is now **"an analysis parser's storey count
   is a proxy that undercounts by construction"**, which is a larger and different claim. The
   register must say so; carrying the old one-line framing forward would understate it.
2. 🔴 **C13's restatement must be published as a LOWER BOUND, not as a value.** T02 reports built
   mean **1.21 → 2.25** and built max **6 → 16**. Both corrected figures are produced by the same
   undercounting proxy, so the true values are **at least** these and probably higher. Any document
   quoting 2.25 as *the* corrected mean is wrong in the same way the pre-fix 1.21 was.
3. ✅ **The 30 / 70 split is untouched and stays quotable.** T02 confirms matched **2,446 / 30.0 %**
   and unmatched **5,714 / 70.0 %** at delta 0, because that split depends on `compute_band_map()`,
   which was already origin-aware before the fix. **OPEN-03's published headline does not move.**
4. ✅ **No production code is implicated.** `layout_assigner.py`'s own path was the reference the
   parser was checked against, and it is the one that reads 20. Production geometry remains clean.

### Controls, as accepted

| control | result |
|---|---|
| C8 | ✅ 8,160/8,160 rows, per-cell sum 8,160 |
| C9a (fleet) | ✅ 8,160/8,160 reproduce exactly, 0 mismatches |
| **C9b** | 🔴 **FAIL — 12/18 agree, 3,734 buildings affected. Accepted as the finding.** |
| C12 | ✅ 4 moved / 14 held, matching CP-1's amended expectation exactly |
| C13 | ⚠️ computed, but publishable only as a lower bound (see 2) |
| all-zero-area failure mode | ✅ 0 rows — the script resaves each baseline before parsing |

### Deviations, all accepted

(a) Replacing the pre-existing 48-sample "C9" block with C9a/C9b — **correct**; the old block would
have silently mismatched post-fix without being a pre-registered control. (b) Leaving the module
docstring's stale "NOT fixed here" paragraph — accepted, the plan scoped the comment edit narrowly;
🔴 **now superseded — that docstring is doubly wrong and is added to the T03 rewrite below.**
(c) Not appending to `MEASUREMENT_open-03_storey-census.md` — correct, that is the director's.

### T03 is replaced, not executed

The original T03 ("close OPEN-62") is **struck**. What replaces it is a record update that keeps the
item open with its enlarged scope, publishes C13 as a bound, and fixes the stale docstring. **A new
measurement — what the storey count should actually be derived from — is a separate question and
needs the user's ruling before anything is built.**

#### T06 — Derive `storey_count` from floor surfaces — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` — `parse_idf()` (:118-241) adds a
  `FLOOR`-surface branch that mirrors the wall path's origin correction (same
  `GLOBALGEOMETRYRULES`/`ZONE Z Origin` reads, no new parsing added). Returns two new keys, both
  additive, `storey_count`/`storey_count_naive` byte-for-bit untouched: `storey_count_floor`
  (distinct origin-corrected `FLOOR` elevations, **unfiltered** by zone) and
  `storey_count_floor_zonefiltered` (same but restricted to `counts_as_floor_area` zones, kept for
  reference, written to no CSV). Module docstring's bucket-definitions list gained one entry
  describing both.
- `scripts/analysis/open03_storey_census_2026-08-20.py` — module docstring's stale "KNOWN CAVEAT ...
  NOT fixed here" paragraph rewritten to describe both symptoms (Z_Origin, fixed T01; wall-base
  undercounting, found by C9b, addressed here) and both fixes in sequence, instead of claiming
  either is still open. `auto_rows` gained an internal (non-CSV) `auto_storey_count_floor`;
  `la_lookup[arch]` gained `storey_count_floor`/`storey_count_floor_zonefiltered`; the `[3]` print
  line reports both. New CSV column `layout_assign_storey_count_floor` added immediately after
  `layout_assign_storey_count_naive`; no existing column reordered, renamed or removed. Two new
  control sections added: **C14** (after C12) and **C16**/**C17** (after C13); C13's own print block
  gained one line flagging it as a lower bound.
- `openubem/outputs/comparisons/open03_storey_census_zfix.csv` — re-written, 8,160 rows, single
  worker (script was already single-process). `open03_envelope_decomposition_zfix.csv` (T01's file)
  was **not** re-run — T06 only needed `parse_idf()`'s new return keys, which the census script
  consumes directly; its mtime is unchanged from T01 (16:46).
- `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 16 — the existing Z_Origin/undercount
  bullet extended with T06's fix location, the filter-vs-C14-targets conflict and its resolution,
  and the C14/C16/C17 results. No second entry added.
- Pre-fix files untouched: `open03_storey_census.csv` mtime unchanged (13:45),
  `open03_envelope_decomposition.csv` mtime unchanged (11:31). `open61_census_fleet*` and
  `open61_census_fleet_work` not read, not touched.

**Deviations.**
1. **T06's own "How" text conflicts with its own pre-registered C14 targets, and the filtered
   reading was rejected.** Plan text: *"Apply the same zone filter the wall path uses so the two are
   comparable, and report separately what the count would be without that filter."* Built and
   measured literally, the zone-filtered `FLOOR` count on `TallBuilding.idf` is **11**, not the
   pre-registered C14 target of **20** — it collapses onto `storey_count` (also 11) because a zone's
   `FLOOR` surface sits at that same zone's own base elevation, and the filter drops 9 of the file's
   20 distinct zone-Z levels entirely (155/164 zones are floor-area-counting but concentrate on only
   11 Z values; measured directly, not assumed). The **unfiltered** count reproduces all 6 of C14's
   named targets exactly (20/30/1/2/2/2) and is what R7 itself defines ("Count distinct FLOOR-surface
   elevations, origin-corrected" — no filter in R7's own wording) and what the calling task's own
   "facts to respect" section names ("Your C14 targets come from the floor-surface reader" — CP-2's
   unfiltered "Floor surfaces (the independent reader) | 20" row). Resolved as: `storey_count_floor`
   = unfiltered (primary, CSV column, tested by C14/C16/C17); the zone-filtered value is computed as
   `storey_count_floor_zonefiltered`, reported here and in `parse_idf()`'s return dict, but not
   written to any CSV. Not a silent choice — flagged before code was finalized, per hard rule 1.
2. C14 was implemented as agreement between `storey_count_floor` and `layout_assigner.compute_band_map()`'s
   `n_proto` (a second, independently implemented production-code floor-surface reader, already
   imported by the census script for C9b) rather than against a fixed table, because the plan's own 6
   named targets are exactly `n_proto`'s values for those 6 archetypes (cross-checked against T02's
   own C9b report). This lets C14 cover all 18 archetypes, not just the 6 named ones, without
   inventing expected values for the other 12.

**Test status.**
- **C14 — 18/18 archetypes agree** between `storey_count_floor` and `compute_band_map()`'s `n_proto`.
  Named targets (6): `TallBuilding` 20, `SuperTallBuilding` 30, `Warehouse` 1,
  `FullServiceRestaurant`/`QuickServiceRestaurant`/`SmallOffice` 2 — all met, 6/6. No archetype
  missed.
- **C15 — PASS, 0 mismatches.** Every column shared between the T02 backup (captured before this
  task overwrote the file) and the new CSV — including `layout_assign_storey_count` and
  `layout_assign_storey_count_naive` — is identical across all 8,160 rows. The only new column is
  `layout_assign_storey_count_floor`.
- **C16 — FAIL, as explicitly allowed.** 38/8,160 rows have `storey_count_floor < storey_count`, all
  38 the same archetype, `Warehouse` (wall-base reads 2, floor-surface reads 1). Not reconciled.
  Example: `osm_id=way/427817519`.
- **C17 — computed as values.** Built mean (floor-surface) **2.94** (>= C13's 2.25 lower bound),
  built max (floor-surface) **30** (>= C13's 16 lower bound).

**Notes.** Single worker throughout, no parallelism added (script was already single-process). No
production code under `openubem/` touched (`git status --porcelain -- openubem/` shows only
untracked output CSVs, no `.py` diffs). No EnergyPlus run. OPEN-62 not closed, register not touched
— director's, per plan. No new *runtime* error was hit (the filter/target conflict was a plan-text
inconsistency, not an exception or a bug), so no new `OpenUBEM_debug_References.md` chapter-16 entry
was opened for it — the existing chapter-16 bullet for this defect was extended instead, per hard
rule 6.

---

#### CP-3 — director's audit of T06 — 2026-08-20

**Signed:** C15 only. **C14 accepted with a correction, C16 accepted as a finding, C17 REFUSED as
values.** Every number below was re-derived by the director directly from
`open03_storey_census_zfix.csv` and from the preserved prototypes in `scratchpad/open03_proto_saved/`,
not taken from the executor's report.

**Reproduced exactly.** 8,160 rows; new column `layout_assign_storey_count_floor` present; C16
violations **38**, all `Warehouse`, example `way/427817519` (floor 1 < wall 2); unmatched subset
5,714 (70.0 %), real mean 3.12 / max 105, built wall mean **2.25** / max **16**, built floor mean
**2.94** / max **30**. The executor's arithmetic is correct in every particular.

**Finding 1 — C14's agreement does not mean what the control implied it meant.**
18/18 agreement with `compute_band_map()`'s `n_proto` is real, and using `n_proto` instead of a
6-row table was the better choice. But `n_proto` is documented in production as
*"deliberately left as the measured Z-BAND COUNT, **never a represented-storey count**"*
(`openubem/geometry/layout_assigner.py:404-406`), where a band is a distinct FLOOR-surface elevation
at 0.2 m tolerance. So C14 proves the new reader **reproduces production's band counter**. It does
not certify that a band is a storey. 🔴 **This is not a production defect** — production uses
`n_proto` to branch `match_storeys()` and never publishes it as a storey count. The defect is the
census's, and the register's, for reading a band count as a storey count.

**Finding 2 — C16's failure retracts the director's own CP-2 framing.**
Mechanism verified directly on `scratchpad/open03_proto_saved/Warehouse.idf`: exterior wall z-bases
are `{0.0: 8 walls, 4.267: 2 walls}` while FLOOR surfaces are **3, all at z = 0.0**. The high-bay
facade is split into two vertical bands within one storey, and the wall-base method reads the split
as a second storey. Set against `TallBuilding` (20 floors, wall-base reads 11):

| | true storeys | `storey_count` (wall base) | direction |
|---|---:|---:|---|
| `TallBuilding` | 20 | 11 | **under** by 9 |
| `SuperTallBuilding` | 30 | 16 | **under** by 14 |
| `Warehouse` | 1 | 2 | **over** by 1 |

🔴 **`storey_count` is therefore not a bound in either direction.** CP-2 recorded it as a *lower
bound* and authorised C13's 2.25 / 16 to be published on that basis. **That framing is withdrawn
here by its own author.** It survives as a statement only because `floor < wall` happens to occur
**0 times inside the 5,714-row unmatched subset** (checked) — an accident of which archetypes land
there, not a property of the method.

**Finding 3 — C17 may not be published as values: the floor-surface reader has its own +1 bias.**
The reader counts an attic as a storey. Verified directly, origin-corrected:

- `SmallOffice.idf` — z = 0.0: 5 floor surfaces (`Core_ZN`, `Perimeter_ZN_1..4`); z = 3.05: **9 floor
  surfaces, every one of them zone `Attic`**.
- `FullServiceRestaurant.idf` / `QuickServiceRestaurant.idf` (both `Relative`) — z = 0.0: `Dining`,
  `Kitchen`; z = 3.049: **zone `attic`**.

All three are one-storey prototypes that `storey_count_floor` reports as 2. They are not marginal:

| | count | share |
|---|---:|---:|
| Attic-inflated archetypes, fleet | **3,580** | **43.9 %** of 8,160 |
| Attic-inflated rows inside the unmatched subset | **2,797** | **48.9 %** of 5,714 |
| Built floor mean as reported | 2.94 | — |
| Built floor mean, attic-corrected (−1 on those rows) | **2.45** | — |

🔴 **The honest restatement of OPEN-03's built-storey headline is the range 2.45 – 2.94, not the
value 2.94.** C17 claimed to convert C13's bound into a value; it did not. It replaced a
method biased in two unknown directions with a method biased in one known direction.

**Consequence — OPEN-62 stays open, scope enlarged a third time.**
The item is no longer "storey counts omit `Z_Origin`" (T01, fixed) or "`storey_count` is not a storey
count" (CP-2). It is: **no reader in this codebase returns a storey count.** The naive reader
collapses `Relative` files to 1; the wall-base reader is unbounded in both directions; the
floor-surface reader counts attics; and production's `n_proto`, which the floor-surface reader
matches 18/18, is explicitly documented as not being one. What a "storey" is for a DOE prototype with
an attic, a plenum or a high bay is a **definition question**, and it has never been answered in this
project. It is not an executor's to answer.

**Accepted without change.** The filtered/unfiltered deviation. R7's wording carries no filter, the
unfiltered reading is the band count, and the executor flagged the conflict with the plan's own "How"
text before finalising rather than after. Keeping `storey_count_floor_zonefiltered` out of the CSV
was also right — it is a diagnostic, and its value on `TallBuilding` (11) collides numerically with
`storey_count` for an unrelated reason.

**What must not happen next.** Do not let an executor "correct" `storey_count_floor` by excluding
zones named `Attic`. Name-matching zone names is exactly the generalisation A1 already falsified
(F-07, cited at `layout_assigner.py:389`), and it would silently move archetypes across
`match_storeys()`'s `n_proto` branches, which the production docstring warns against by name.

---

#### T07 — Preserve the census corpus — completed 2026-08-20 *(director, ruling R6)*

**Artifacts:**
- Corpus moved to **`C:/Users/o_iseri/OpenUBEM_corpora/open61_census_2026-08-20`**.
- `INVENTORY.json` written at the corpus root (per-cell counts, sizes, provenance).
- `docs/docs_ACTIVE/openings/extra/INVENTORY_preserved-simulation-corpora.md` — the human inventory.
- `scripts/analysis/corpus_inventory_check_2026-08-20.py` — the checker R6 asks for.

**Gate honoured.** Executed only after `open61_census_fleet.csv` reached its final **8,160 rows**, and
after confirming no `energyplus.exe` process was alive. Nothing was moved while the census ran.

**What was moved.** **7,861 building directories, 7,861 `.sql` files, 121.9 GB, 12 cells.** Same-volume
`os.rename` — **0.77 s, no copy, no extra disk**. Re-scanned at the destination immediately after:
12 cells, 7,861 dirs, 7,861 `.sql`, 121.9 GB. Checker run: **PASS**.

**Deviations — three, all deliberate:**
1. **R6 estimated ~38 GB; the corpus is 121.9 GB** — 3.2x the ruling's figure. Nothing was pruned to
   meet the estimate: R6 explicitly chose full preservation over "preserve only what is cited", so the
   whole tree moved. Composition: `.sql` 75.7 GB (all 7,861), `.eso` 33.8 GB (**only 799 buildings**),
   `.csv` 8.9 GB, `.htm` 1.8 GB, remainder < 1.5 GB. The `.eso`/`.htm`/`.csv` tail belongs to the 799
   buildings run before the driver was switched to a leaner output set, so per-building size is not a
   uniform quantity and must not be used as a signal.
2. **Destination is outside the Windows temp tree, breaking with the existing convention.** The other
   corpora live in `%LOCALAPPDATA%\Temp\ubem_validation\`. That is a standard Windows temp root, which Storage
   Sense and Disk Cleanup may purge by age without warning — the exact class of loss R6 was written
   after. Durability was ranked above convention. Still on the C: volume, so the move stayed a rename.
3. **A checker script was written**, which the task text did not name. R6's wording is "an inventory
   that is **checked** rather than written once"; an inventory with no way to check it does not satisfy
   the ruling. Exit 0 = intact, exit 1 = discrepancies listed.

**Test status:** `py -3 scripts/analysis/corpus_inventory_check_2026-08-20.py <root>` -> **PASS —
corpus matches its manifest.** 12 cells, 7,861 dirs, 7,861 `.sql`, 121.9 GB.

**Notes — the coverage number, stated so it is never quoted as 100 %.** 7,861 directories stand against
**8,152 `ok` census rows = 96.4 %**. The 291-building gap is the census's kill-and-resume: their
`sim_out` was reclaimed before preservation. Their *numbers* survive in `open61_census_fleet.csv`;
their raw EnergyPlus output does not, so anything needing a re-read of raw output for those 291 must
re-simulate. This was pre-committed in the OPEN-61 plan's T03 entry before the move and is reproduced
by the checker at every run.

**Named, not fixed:** the run-4 fleet corpus (`open48_refleet4`) and five siblings remain under
`%LOCALAPPDATA%\Temp\ubem_validation\`, exposed to the same temp-cleanup risk. Moving them is a
separate cost and a separate decision; it is recorded in the inventory doc §2 so the next person
decides knowingly rather than discovers it after a loss.
