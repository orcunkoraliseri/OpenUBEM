# PLAN — ten open items, overnight pass

> **Slug:** `ten-items-2026-08-18-overnight` · **Date:** 2026-08-18 (overnight) · **Author:** manager session
> **Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`
> **Predecessor:** `PLAN_ten-tasks-2026-08-18-night.md` (W01–W10, all discharged)
> **Instruction:** *"si des taches sont completes, choisir 10 taches differentes et demarrer de
> l'execution"* … *"continuer jusqu'a la fin, et mettre a jour ce prompt … je vais dormir."*
> The user is asleep. **This pass runs to the end unattended and updates the director prompt as it goes.**

---

## 1. Selection — and why these ten

**Every one of the 25 live items has now had a first measurement.** That is a new situation for this
arc: a batch can no longer be *"ten items nobody has measured"*. So the selection rule changes shape.

**Rule applied here:** for each candidate, read what the item's own §-section names as *the next
unanswered question*, then check `openings/extra/` and `openubem/outputs/comparisons/` to confirm
that question has **not** already been answered on disk. Six of the ten below are questions the
register itself writes down as *"the next thing on this item"*. **None of the ten is a re-run of an
existing artifact.**

**Discarded candidates, and why:**

| candidate | why not |
|---|---|
| **OPEN-27** | its remaining half is a **DESIGN-doc edit the user must make at source**; the code side is already pinned by `TestOpen27ArchetypeNameBinding`. Not a measurement. |
| **OPEN-19** | needs a climate-zone/code-year switch that does not exist. Code before cycles. |
| **OPEN-15/16/17** | all three are awaiting a **user decision**, not a measurement. |
| **OPEN-55** | **ruling outstanding.** Nothing is patched or measured until it comes. |
| **OPEN-18** | its two remaining routes are both larger than anything this arc has closed, and the register explicitly declines to scope them. |
| **OPEN-20** | needs new cities, i.e. new data collection. |

---

## 2. Hard rules for this pass

1. **No cluster.** Everything here is local disk or local EnergyPlus. No `srun`, no `ssh`.
2. **Never edit** root `main.py`, OVERVIEW/DESIGN docs, `docs/docs_DONE/`, `docs/docs_main/`,
   `docs/docs_stepN/`. **No `.py` under `docs/`.**
3. **Never commit.** Git is handled externally; read-only git only.
4. **No concurrent `pytest`** (OPEN-52's collision is fixed, but the rule stands for parallel agents).
5. **Any hand-run of a pipeline IDF passes `energyplus -x`.** Learned the hard way last pass.
6. **Measurement only.** No production code is changed by this plan. Where a remedy is implied, it is
   **recommended to the user and not taken**.
7. **Pre-register every prediction** before running the thing that tests it, and report the prediction
   whether it holds or fails.
8. **A control that fails voids the numbers it guards.** No result is reported past a failed control.

---

## 3. Corpus

`%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/` — **verified present at the start of this pass**:
twelve cells, `sim_out` populated (738 / 149 / 413 spot-checked), `step3/idfs` and `weather` intact,
results mirrored at `docs/validations/overAll/results/open48_refleet/`. **Still not durable** — the
2026-08-17 sweep emptied a sibling path.

---

## 4. Task list

### X01 — OPEN-56: the fleet-scale cost, stratified over all twelve cells
**What.** Repeat last pass's `Zone.Volume` intervention on a **stratified sample of all twelve cells**
instead of ten buildings in two rural cells.
**Why.** The register's own next step, verbatim: the remedy *"needs a fleet-scale cost measurement
rather than ten buildings."* Last pass's +0.75 % came from `la_rural` and `nyc_rural` only — the two
smallest, lowest-rise cells in the fleet. **A cost measured only on rural bungalows cannot be quoted
against a fleet that is 3,368 buildings of `nyc_suburban` + `nyc_urban`.**
**How.** Same treatment (one field, `Zone.Volume = floor_area × height`), same object-by-object diff
assertion, same in-session both-arms design, same `-x`. 5 successful buildings per cell × 12 cells.
**Pre-registered prediction:** mean stays positive and one-directional; **magnitude rises with zone
count**, so urban cells exceed +0.75 %.
**How to test.** Control: `Indicated Zone Volume <= 0.0` present in **every** baseline run and **absent
from every** treated run. Diff check `OK n zones, field 9 only` on every building. Either fails → no
number is reported.

### X02 — OPEN-56: what the cost scales with
**What.** Regress the per-building Δ against zone count, storey count, floor area and archetype, on
X01's output.
**Why.** Last pass observed the absolute Δ was near-uniform (+0.51…+1.30 kWh/m²) across buildings
spanning 41–524 m² — consistent with a **fixed per-zone** effect, which was a guess from ten points.
If it is per-zone, the fleet cost is predictable from the zone census **without re-running 8,160
buildings**, and that is the cheapest honest route to a fleet number.
**How.** Fit and report; no extrapolation to `157.1` is performed.
**How to test.** Report R² and the residual spread. **A weak fit is a reportable result** — it means the
per-zone story is wrong and the fleet cost needs the full run.

### X03 — OPEN-09 × OPEN-56: is the non-convergence downstream of the stub?
**What.** Take the **10 buildings that had ≥1 heat-balance non-convergence warning and still
succeeded**, and run both arms. Count non-convergence warnings in each.
**Why.** Last pass produced a perfect contingency — all 6 failures inside the 16 non-convergent
buildings, 0 outside — and named the two-stage picture (stub universal, non-convergence rare and
containing every failure) as the arc's missing link. **What it could not say is whether the two stages
are the same defect.** If writing `Zone.Volume` also clears the non-convergence, OPEN-09 is a
*symptom* of OPEN-56 and folds into it; if not, they are independent and OPEN-09 keeps its own life.
**How to test.** Same control as X01. Report the warning count per arm per building.

### X04 — OPEN-35: the consequence of building 2,611 buildings as one storey
**What.** On run 2, compare the EUI distribution of the **2,611** buildings persisted at `levels = 1.0`
(re-derived exactly last pass) against the rest of the fleet, and separately the **1,031** that were
given a mid- or high-rise archetype and built as a single storey.
**Why.** OPEN-35's mechanism is proved and its population is exact. **Its consequence has never been
measured.** The item cannot be ruled on — which fallback is intended is a DESIGN question — but the
size of what the ruling decides is measurable now.
**How to test.** Report medians and the full distribution, not a mean alone. **Confound stated up
front and not hidden:** these buildings are data-poor by definition, so a raw EUI gap is not a causal
estimate. Report it as a gap, with the confound named.

### X05 — OPEN-08: whether the vintage half is measurable at all today
**What.** Determine whether run 2 persists `vintage_standard`, and if so whether a cross-generation
vintage comparison is now constructible.
**Why.** The item's blocker was found to be seven days stale once already. The archetype half is at
13.40 %; the vintage half is blocked on *"no prior-generation source carries the column."* **Run 2 did
not exist when that was written.**
**How to test.** Column presence is a fact, not a judgement. If the comparison is constructible, build
it; if not, **state the exact remaining gap** so the next session does not re-check.

### X06 — OPEN-53: is the item still live after the E02 sweep?
**What.** Establish what still depends on the E02 harvest, given the 2026-08-17 sweep emptied it and
two full fleet runs (`open48_refleet`, `open48_refleet3`) now exist on frozen input.
**Why.** OPEN-53 is *"874/875 E02 harvest directories are missing `.sql`/`.end`."* If E02 is gone and
nothing cites it for a live claim, the item is about a corpus that no longer exists.
**How to test.** Sweep the live docs for load-bearing E02 citations. **A closure is recommended only
if nothing live depends on it** — and the recommendation is left to the user either way.

### X07 — OPEN-29: the adoption material, not another sweep
**What.** For each of the **8 defects hand-verified as genuinely still open**, record its current
status at HEAD and whether it duplicates a live register item.
**Why.** The item's question — *"which of these should this register adopt?"* — is a **user decision**
that has never been given the material to decide on.
🔴 **Explicit guard.** Last pass's automated status sweep was **circular** (it classified eight IDs
from OPEN-29's own candidate list) and lost to the existing hand re-trace. **This task does not
re-sweep.** Its input is the hand-verified list; its output is one line per defect.
**How to test.** Every line carries a file:line citation or is marked unciteable.

### X08 — OPEN-10: how many fleet buildings the `ZoneGroup` edit would actually help
**What.** Count, on run 2, the buildings in the two apartment archetypes that carry a `ZoneGroup`,
versus the seven `fallback_not_expressible` archetypes the edit cannot help.
**Why.** N11 established the capability is real and the remedy **narrower than claimed** — but it
never counted the buildings. *"Restore exact expressibility"* is currently a claim with no
denominator.
**How to test.** Counts per archetype per cell, summing to the fleet.

### X09 — OPEN-14: did the fleet's Stage-1 path ever consume a fusion slice?
**What.** Establish whether the fleet's `01_buildings.gpkg` was produced by a code path that would
have consumed an Overture slice had one been tracked.
**Why.** This is quoted verbatim from the item: *"proving it needs one more step … that step is a
measurement nobody has run, and it is the next thing on this item."* It is the step that decides
whether OPEN-12's residual is a source-coverage gap or is **this** item.
**How to test.** `FUSION_SOURCES_BY_TARGET` at HEAD, the Stage-1 entry point, and run 2's own inputs.
**Report the convergence as adjudicated only if the path check settles it** — otherwise say so.

### X10 — records
Register amendments (append-and-amend, strike with `~~`, never overwrite), measurement doc under
`extra/`, `docs/PROJECT_CHECKLIST.md`, **the director prompt**, this plan's §7 progress log, the
progress board artifact republished in place, and a **programmatic** register recount.

---

## 5. Stop-and-report points

- **CP-X1** — after X03. The three OPEN-56/09 experiments are the compute-bound half; everything after
  is disk-only. Report the control before any number.
- **CP-X2** — after X09, before X10.

---

## 6. What this pass may not do

- Close an item. **Closures are recommendations to the user**, and three are already outstanding
  (OPEN-42, OPEN-11, OPEN-07).
- Change production code.
- Extrapolate any of X01/X02 into a correction to the published `157.1 kWh/m²`.
- Act on OPEN-55 before its ruling.

---

## 7. Progress log

#### X01 — OPEN-56 fleet-scale cost, stratified over twelve cells — completed 2026-08-18 (overnight)
**Artifacts:** `scripts/analysis/open56_fleet_cost_stratified.py`,
`scripts/analysis/open56_fleet_cost_repair.py`,
`openubem/outputs/comparisons/open56_fleet_cost_stratified.csv`.
**Test status:** ✅ **control whole** — diff assertion `OK n zones, field 9 only` **70 / 70**;
`Indicated Zone Volume <= 0.0` in **70 / 70** baseline and **0 / 70** treated; **70 / 70 completed in
both arms.**
**Result:** mean **+0.98 %**, median **+0.84 %**, sd 0.75, range −0.23 % to +3.25 %, **65 / 69 same
direction**, absolute Δ mean **+1.00 kWh/m²**. Higher than the rural-only +0.75 % / +0.67 %; sign
unchanged. Per cell the ordering is geographic (LA high, NYC low, Austin middle), not morphological.
**Deviations:** ⚠️ the first execution ran 140 EnergyPlus jobs through a 6-worker pool and **ten
buildings produced empty output directories** in the baseline arm — no `.err` at all. Read literally
that reports the control as 60 / 70 and drops ten buildings, four of them the whole `nyc_centre`
sample. Re-run serially the identical `baseline.idf` completes in **18 s with 0 severe errors**, so it
was a concurrency artifact; the ten were re-run one at a time and merged before anything was reported.
**Notes:** `157.1 kWh/m²` deliberately **not** restated — 5 per cell is stratified, not
population-weighted, and §6 of this plan forbids the extrapolation.
🔴 **New lead:** `nyc_centre/relation_3566904` was excluded because the treatment also changed its
reported **Total Building Area, 157,115 → 37,551 m² (÷4.18)**. 59 of 60 were identical to within
0.1 %, so it is isolated — but the project's EUI denominator *is* EnergyPlus's simulated floor area.
Registered, **not generalised from n = 1**.

#### X02 — what the OPEN-56 cost scales with — completed 2026-08-18 (overnight)
**Artifacts:** same CSV; correlations and quartiles printed by `open56_fleet_cost_repair.py`.
**Test status:** ✅ reported with R-values and residual spread as the plan required; the weak-fit
branch was the outcome and is reported as a result, not hidden.
**Result:** 🔴 **the pre-registered prediction is half refuted.** Direction held (94.2 % same-sign).
*"Rises with zone count"* — **refuted**, `corr(pct_change, n_zones) = +0.113`. *"Urban cells exceed
+0.75 %"* — **refuted**, the three lowest cells are all NYC. The absolute Δ is the **more** stable
normalisation (cv **0.79** raw vs **1.09** per zone), so the effect is a **fixed per-building offset of
≈ +1.0 kWh/m²**, not per-zone. **This overturns the previous pass's inference from ten points.**
**Notes:** the only moderate correlate (baseline EUI, −0.478) is arithmetic, not physical.

#### X03 — is OPEN-09 downstream of OPEN-56? — completed 2026-08-18 (overnight)
**Artifacts:** same CSV, `group = nonconverged` rows.
**Test status:** ✅ same control as X01.
**Result:** 🔵 **clean negative.** 150 non-convergence warnings baseline, **150 treated**, **15 / 15
unchanged on every one of the ten** buildings, while the same treatment clears the volume warning
completely. **OPEN-09 and OPEN-56 are independent defects overlapping on 16 buildings.**
**Notes:** both facts stand together — the treatment repairs all six failures *and* leaves the
non-convergence warnings untouched in the ten that survive. Folding the two items would have been
wrong, and this is what stopped it.

#### X04 — OPEN-35's consequence — completed 2026-08-18 (overnight)
**Artifacts:** `scripts/analysis/open35_open10_consequence_census.py`,
`openubem/outputs/comparisons/open35_eui_consequence.csv`.
**Test status:** ✅ medians and full distribution reported, not a mean alone; the confound was
declared before the measurement.
**Result:** population re-derives exactly (**2,611 / 32.00 %**, all at `levels = 1.0`, **1,031**
apartment-archetype — 1,119 under the wider definition). 🔴 **The +47.9 % fleet EUI gap is composition,
not effect**: `nyc_suburban` supplies 1,589 of the 2,611 and has **no unaffected buildings at all**,
and **within cells the direction is not even consistent** — four lower, four higher.
**Notes:** the pre-declared confound turned out to be the entire finding. The item needs an
intervention with a control, as OPEN-56 got. **Named, not done.** Side result: **0 failures in 2,611.**

#### X05 — OPEN-08's vintage half — completed 2026-08-18 (overnight)
**Artifacts:** `scripts/analysis/open08_vintage_cross_generation.py`,
`openubem/outputs/comparisons/open08_vintage_cross_generation.csv`.
**Test status:** ✅ **in-task control 0.0000 %** archetype disagreement on the same join; tier counts
`HOTDECK_NEIGHBOR_HIGH` **90** / `_MED` **46** reproduce run 2's own census exactly.
**Result:** **3 / 8,160 = 0.0368 %**, all one bin apart, in `la_centre` (1) and `la_urban` (2). The
blocker was stale a third time — **the E02 parquet manifests survived the sweep** (61 files, twelve
cells). **Closure recommended, not taken.**
**Deviations:** 🔴 the first run dropped the geometry column, silently disabling the tier-1 spatial
donor, and produced **0.3554 % — ten times too large**. The **absent `HOTDECK_*` rows** in the tier
table were the tell. Fixed and re-run **before any number left the task.**

#### X06 — OPEN-53's custody exposure — completed 2026-08-18 (overnight)
**Artifacts:** measurement report §X06 (no new CSV; a disk census).
**Test status:** ✅ directory mtimes checked in three cells against the 2026-08-17 16:21 signature.
**Result:** **152.4 GB across three corpora, 145 GB of it `.sql`**, none yet swept. 🔵 The evidence
this arc actually cites is **under 0.12 GB** (`.err` 0.091 + vector/CSV 0.027); ~3.5 GB with the IDFs.
**The 76 GB of `.sql` is the bait and is re-derivable.**
**Notes:** ⚠️ observation only — **no file moved, copied or deleted.** Also falsifies *"E02 is gone"*
in the reassuring direction: its manifests survived.

#### X07 — OPEN-29's adoption material — completed 2026-08-18 (overnight)
**Artifacts:** measurement report §X07, off `open09_fleet_err_taxonomy.csv` and
`open10_storey_expressibility_fleet.csv`.
**Test status:** ✅ every line carries a signature count or is marked untestable by this route.
**Result:** four of the eight (**E-LA-15, E-LA-18, E-LA-19, E-LA-30**) have **no signature across
8,160 buildings**; **E-LA-16** is one building and no severity; 🔴 **E-LA-17 is OPEN-09's population
exactly** and would double-count; **E-LA-33 re-derives at 93.32 % inert**, inside its own 82–98 %
claim.
**Deviations:** none — and the plan's explicit guard held: **this task did not re-sweep.** The prior
automated attempt was circular; this one takes the hand-verified list as input.
**Notes:** limits stated — `.err` absence is evidence about the `auto` fleet at HEAD, not proof of
repair, and three of these were raised under `layout_assign`, which run 2 does not exercise.

#### X08 — OPEN-10's denominator — completed 2026-08-18 (overnight)
**Artifacts:** `scripts/analysis/open35_open10_consequence_census.py`,
`openubem/outputs/comparisons/open10_storey_expressibility_fleet.csv`.
**Test status:** ✅ **the historic figure reproduces exactly, split and all — 90 = 66 + 24.**
**Result:** `applied` **497 / 7,442 (6.7 %)**; `fallback_not_expressible` **1,992**, of which the
proposed edit reaches **90 (4.5 %)** and **1,902 (95.5 %)** are structurally beyond it (1,578
`SmallOffice`). Exactly two of eighteen archetypes carry a `ZoneGroup`.
**Notes:** this ran the experiment `MEASUREMENT_open-10_zonegroup-capability.md` §4 named and declined
under N11's no-CPU rule, using production `compute_band_map()` / `match_storeys()`. 🔵 Cross-item
finding: `nyc_suburban` and `nyc_rural` have **zero** `applied` because every building sits at
`levels = 1.0` — **OPEN-35 is upstream of E-LA-33's symptom.**

#### X09 — OPEN-14's named next step — completed 2026-08-18 (overnight)
**Artifacts:** measurement report §X09.
**Test status:** ✅ **control: `nyc_centre`, the one cell WITH a tracked slice, also carries zero
`FUSED` tokens.**
**Result:** **zero `FUSED` provenance tokens across all 8,160 buildings**, while every other
imputation tier fires and stamps normally. `FUSION_SOURCES_BY_TARGET = {}` closes the gate before the
slice is ever looked for. **The missing slices are real but NOT the binding blocker.**
**Notes:** this makes the OPEN-12 / OPEN-14 four-cell convergence adjudicable — **it is a coincidence
of coverage**, confirming N15 by a route N15 did not use.

#### X10 — records — completed 2026-08-18 (overnight)
**Artifacts:** register amendments (OPEN-08, 09, 10, 14, 29, 35, 53, 56 — §1 rows and §-sections, plus
a header amendment); `extra/MEASUREMENT_ten-items-2026-08-18-overnight.md`; `docs/PROJECT_CHECKLIST.md`;
`prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`; this log; the progress board republished in place.
**Test status:** ✅ programmatic recount (`scripts/analysis/open_register_recount_2026-08-18.py`):
**25 live, 31 struck — 56 total, exactly OPEN-01…OPEN-56, none missing, none duplicated. Next free
`OPEN-57`.** Unchanged, because **no item closed this pass.**
**Notes:** four closures now stand recommended and untaken — **OPEN-42**, **OPEN-11**, **OPEN-07** and
now **OPEN-08**.

### CP-X1 (after X03) — reported
Control before numbers, as required: **70 / 70 baseline volume warnings, 0 / 70 treated, 70 / 70
completed both arms, 70 / 70 diff assertions.** Only then the cost. The one building whose denominator
moved was excluded from the statistic and reported separately.

### CP-X2 (after X09) — reported
Six disk-only tasks landed; four register figures re-derived exactly; two stale blockers cleared; one
prediction half refuted and recorded as such.
