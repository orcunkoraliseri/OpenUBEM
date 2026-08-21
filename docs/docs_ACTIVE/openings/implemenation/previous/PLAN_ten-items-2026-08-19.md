# PLAN — ten open items, 2026-08-19

> **Slug:** `ten-items-2026-08-19` · **Date:** 2026-08-19 · **Author:** manager session
> **Register:** `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md`
> **Director prompt:** `docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`
> **Predecessor:** `PLAN_ten-items-2026-08-18-overnight.md` (X01–X10, all discharged)
> **Instruction:** *"choisir des nouvelles dix taches, preparer une plan d'implementation pour
> resoudre, et apres executer jusqu'a la fin"* (2026-08-19).

---

## 0. Three rulings were obtained before this plan was written

The user was asked three questions at selection time and answered all three. **This is the first pass
in six that starts unblocked.**

| # | Question | Ruling |
|---|---|---|
| **R1** | OPEN-55 — width of the Unknown donor screen | 🟢 **Option B+** — exclude the four data centres, `Laboratory`, and both restaurants. Equipment ceiling `16.15 W/m²`, uniform median `9.37 W/m²`. |
| **R2** | The four recommended-and-untaken closures | 🟢 **Take all four** — **OPEN-42** and **OPEN-11** fold into OPEN-56; **OPEN-07** and **OPEN-08** close on their own measurements. |
| **R3** | Durable custody of the run-2/run-3 evidence | 🟢 **Copy the cited material into the repository.** |

**R1 supersedes** *"Nothing will be patched before that ruling"* (`extra/PROPOSAL_open-55_unknown-pde-bounds.md` §10).
**R2 supersedes** the four "recommended, not taken" notes carried since 2026-08-18.
**R3 discharges** the costed open action recorded under OPEN-53 on 2026-08-18 (late).

---

## 1. Selection — and why these ten

**Every one of the 25 live items already has a first measurement.** Selection is therefore on the
*next unanswered question*, not on the item. Per the binding rule of 2026-08-18 (late), every
candidate below was checked against `docs/docs_ACTIVE/openings/extra/` and
`openubem/outputs/comparisons/` **before** this plan was written, to confirm the question is not
already answered on disk.

| task | item(s) | the question, and where the register names it |
|---|---|---|
| **T01** | OPEN-55 | Implement the B+ screen. Ruling R1; patch shape given in the proposal §7/§7A. |
| **T02** | OPEN-55 | The proposal's own falsifiable acceptance test: `nyc_suburban`, 71 divergences → **zero**, no other change, frozen input. Proposal §8. |
| **T03** | OPEN-56 / OPEN-01 | The "cheap census" the overnight pass named and deliberately did not generalise: `.eio` simulated floor area vs `footprint_area × levels` fleet-wide. Director prompt, overnight §"for the next session" item 4. |
| **T04** | OPEN-35 | *"It needs an intervention with a control"* — rebuild a sample at a corrected storey count and run both arms. Same design that worked for OPEN-56. Item 5 of the same list. |
| **T05** | OPEN-38 | *"`way/401910463` and 4 of the 7 `LAUNDRYROOMFLR1` fatals remain unmeasured — no IDF survives for them."* **That blocker is stale** — `layout_assign` IDFs can be built locally. |
| **T06** | OPEN-47 | The measurement OPEN-22's closure handed it: all 11 fine errors sit inside the correct coarse class, so how much of the fine error is the two untraced size thresholds? |
| **T07** | OPEN-12 / OPEN-35 | The register's own claim, never checked: *"1,589 of `nyc_suburban`'s buildings have neither input, so they are 61% of OPEN-35's 2,611."* Is OPEN-12 a strict subset of OPEN-35? |
| **T08** | OPEN-29 | X07 found the adoption material exists and **4 of 8 have no signature at all**. Adjudicate all eight. |
| **T09** | OPEN-42, OPEN-11, OPEN-07, OPEN-08 | Execute ruling R2 — closure records, struck rows, retired IDs, programmatic recount. |
| **T10** | OPEN-53 | Execute ruling R3 — copy the cited evidence into the repository with a hash manifest, then restate what remains of the closure condition. |

**Discarded candidates, and why:**

| candidate | why not |
|---|---|
| **OPEN-27** | remaining half is a DESIGN-doc edit at an external source; code side already pinned by `TestOpen27ArchetypeNameBinding`. |
| **OPEN-19** | needs a climate-zone / code-year switch that does not exist. Code before cycles. |
| **OPEN-15 / 16 / 17** | all three await a user decision, not a measurement. Re-surface next pass. |
| **OPEN-18** | both remaining routes are larger than anything this arc has closed; the register declines to scope them. |
| **OPEN-20** | needs new cities, i.e. new data collection. |
| **OPEN-49** | closure is blocked on a **twelve-cell** fleet figure. Run 3 landed seven. **T01/T02 are the precondition** — this is next pass's item, not this one's. |
| **OPEN-03 / OPEN-13 / OPEN-14** | all three are `layout_assign`-scoped or config-gated; each needs a ruling before a measurement would mean anything. |

---

## 2. Hard rules for the executor

1. **No cluster compute from an interactive shell.** No `srun`, no `ssh … python`. If a task needs the
   cluster it uses `sbatch --array`, fire-and-forget, then reads the output file. **T02 is the only
   task that touches the cluster** and it does so through the existing driver.
2. **Remote login shell is tcsh.** Any remote command goes through the `_ssh()` helper
   (`scripts/cluster/t08_harvest_results.py:104`) or `scripts/validation/v12_cell_pipeline.py`'s
   guarded wrapper. Never a bare command string.
3. **Never edit** root `main.py`, OVERVIEW/DESIGN docs, `docs/docs_DONE/`, `docs/docs_main/`,
   `docs/docs_stepN/`. **No `.py` file under `docs/`, ever.**
4. **Never run a git write command.** Git is handled externally. Read-only git only.
5. **Production code is changed by T01 alone.** Every other task is measurement, records, or file
   copying. Where any other task implies a remedy, it is **recommended to the user, not taken**.
6. **Any hand-run of a pipeline IDF passes `energyplus -x`** (`HVACTemplate:*` expansion).
7. **Cap EnergyPlus parallelism at 4 workers**, and **verify an empty output directory serially
   before scoring it as a failure.** Measured last pass: 140 jobs through a 6-worker pool left ten
   directories completely empty, and the identical file completed in 18 s serially with 0 severe.
8. **Pre-register every prediction** in the progress log *before* running the thing that tests it, and
   report it whether it holds or fails.
9. **A control that fails voids the numbers it guards.** No result is reported past a failed control.
10. **Print the imputation tier distribution** whenever an imputation output is re-derived, and check
    it against the fleet's own `data_quality_flag` census before quoting a number. Last pass a dropped
    geometry column silently degraded `knn_fill` to a group mode and produced a figure ten times too
    large; the tell was zero `HOTDECK_*` rows.
11. **Re-verify any `%LOCALAPPDATA%` artifact on disk at the moment you use it.** Do not cite
    `e02_corpus_inventory.csv` or any dated census as current state.
12. **Job `1266911` (`4J_s4_pe`) and anything else already queued under this account is not ours.**
    Leave it alone.

---

## 3. File layout

| what | where |
|---|---|
| production code change (T01 only) | `openubem/semantic/__init__.py` |
| regression test (T01) | `tests/test_semantic_unknown_bounds.py` |
| analysis scripts | `scripts/analysis/open<NN>_<slug>_2026-08-19.py` |
| CSV / numeric outputs | `openubem/outputs/comparisons/` (flat) |
| figures | `openubem/outputs/` (flat) — **never under `docs/`** |
| measurement write-ups | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_*.md` |
| preserved evidence (T10) | `docs/validations/overAll/evidence/open48_runs/` |
| progress log | §8 of this document, one entry per task |

---

## 4. Dependency decisions — pinned

- **No new third-party dependency.** Everything here uses what is already imported by
  `openubem/` or `scripts/analysis/`: `pandas`, `geopandas`, `numpy`, `scipy`, `matplotlib`.
- **EnergyPlus**: the same binary the arc has been using. Version is recorded in each run's
  `eplusout.err` header and must be quoted in any report that compares two arms.
- **Frozen inputs**: `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/<cell>/01_buildings.gpkg`.
  T02 uses these unchanged — **do not let step 1 re-fetch OSM.** A fresh fetch confounds the code
  change with a new input drift and reproduces run 2's own uninterpretability.
- **Fleet aggregation arithmetic**: `scripts/analysis/open43_fleet_aggregations.py`. Pooled, not a
  mean of cell means (OPEN-43). Any fleet figure quoted in this pass uses that script's arithmetic.

---

## 5. Facts with line citations — verified at HEAD on 2026-08-19

1. `openubem/semantic/__init__.py:82` — `_DONOR_ARCH = "MediumOffice"`, the Unknown envelope donor.
2. `openubem/semantic/__init__.py:212-222` — `_per_building_rng()`, the OPEN-49 fix: `blake2b(osm_id)`
   mixed with `config.RANDOM_SEED` through `SeedSequence`. **Do not disturb it.**
3. `openubem/semantic/__init__.py:225-247` — `_build_unknown_loads()`; `pde_cols` is the four columns
   `lighting_w_m2, equipment_w_m2, occupant_m2_per_person, wwr`; `scalar_cols` is the four setpoints;
   **`bounds = {col: (real_loads[col].min(), real_loads[col].max()) for col in pde_cols}` at `:247`
   is the line the data-centre rows reach.**
4. `openubem/semantic/__init__.py:366` — the call site, passing `_get_cross_archetype_loads()`
   **unconditionally** (OPEN-49 ruling 3). **This is what must stay true.**
5. `openubem/semantic/__init__.py:462-465` — `_get_cross_archetype_loads()` returns
   `openubem.semantic.loads._get_flat_loads()`, the full 29-row table, unscreened.
6. `openubem/semantic/__init__.py:383-386` — a data-centre exclusion set **already exists** in the
   probabilistic-perturbation branch, applied to *real* rows only. The Unknown branch has no
   equivalent. **T01 must not merge the two; they guard different populations.**
7. `scripts/validation/v12_cell_pipeline.py:138-141` — `step1_fetch` loads a cached
   `01_buildings.gpkg` when one exists and re-fetches OSM otherwise. This is why seeding freezes the
   input.
8. `scripts/validation/v12_cell_pipeline.py:111-116` — `_ssh` (OPEN-54's site; remedy landed
   2026-08-18). Timeouts are fatal at **every** call site, including display-only ones.
9. `scripts/validation/open48_fleet_run3.py` — the run-3 driver, with `_preflight`. **T02 reuses it
   for one cell.** Detached; it survives the agent that launches it.
10. `openubem/semantic/building_classifier.py:159` — `_OFFICE_SMALL_MAX_M2 = 2322.0` and
    `_OFFICE_MEDIUM_MAX_M2 = 9290.0`, exact conversions of 25,000 / 100,000 ft². **T06 reads these;
    T06 does not change them.**
11. `openubem/idf/surfaces.py:223` — a detector for the OPEN-56 signal exists, **disabled at
    `:671-681`** on the stated ground that the sign test would give false positives. Recorded as a
    code tension; **no task in this plan touches it.**

**Measured facts this plan relies on, each with its source:**

- OPEN-55 dose-response: 518 Unknown across `nyc_urban` + `nyc_suburban`, 154 failures, monotonic
  0.000 → 1.000 over eleven equipment-density bins. Nothing below **~2,496 W/m²** failed.
  (`extra/INVESTIGATION_open-55_pde-bounds-datacenter.md`.)
- B+ ceiling **16.15 W/m²** (`PrimarySchool`/`SecondarySchool`), median **9.37 W/m²**, against
  `MediumOffice`'s 10.76 — the envelope donor the same row already uses.
  (`extra/PROPOSAL_open-55_unknown-pde-bounds.md` §7A.)
- OPEN-56 fleet cost: **+0.98 % mean / +0.84 % median**, 65/69 positive, a **fixed per-building**
  offset (`corr(pct, n_zones) = +0.113`), control `Indicated Zone Volume <= 0.0` 70/70 → 0/70.
  (`extra/MEASUREMENT_ten-items-2026-08-18-overnight.md`.)
- The `nyc_centre/relation_3566904` anomaly: writing `Zone.Volume` moved **Total Building Area
  157,115 → 37,551 m² (÷4.18)** on **1 of 60**; the other 59 were identical to within 0.1 %.
- OPEN-35 population: **2,611 of 8,160 (32.00 %)** persisted at `levels = 1.0`, of which **1,031**
  were given a mid- or high-rise archetype and built as a single storey.
- OPEN-12: `nyc_suburban` — **1,589 buildings, the fleet's largest cell** — has no height for a
  single building.

---

## 6. Task list

Every task states **What / Why / How / How to test**. A task that cannot complete **stops and
reports**; it does not substitute a different measurement.

---

### T01 — OPEN-55: implement the B+ Unknown donor screen

**What.** Screen the Unknown PDE donor pool. Excluded on **every** PDE column: the four data centres
(`SmallDataCenterLowITE`, `SmallDataCenterHighITE`, `LargeDataCenterLowITE`, `LargeDataCenterHighITE`),
`Laboratory`, `FullServiceRestaurant`, `QuickServiceRestaurant`. Excluded **additionally on the
occupancy column only**: `Warehouse`.

**Why.** Ruling R1. An unnamed building currently draws `equipment_w_m2` uniformly over
`[2.58, 5381.96]`; with a uniform draw the maximum sets the *centre*, so half of all Unknown buildings
carry a load above 2,690 W/m². That is what stopped five cells of run 3, and below the crash threshold
it silently biases rather than failing.

**How.**
1. Add, next to `_DONOR_ARCH` at `openubem/semantic/__init__.py:82`:
   ```python
   _UNKNOWN_DONOR_EXCLUDE = {
       "SmallDataCenterLowITE", "SmallDataCenterHighITE",
       "LargeDataCenterLowITE", "LargeDataCenterHighITE",
       "Laboratory", "FullServiceRestaurant", "QuickServiceRestaurant",
   }
   _UNKNOWN_DONOR_EXCLUDE_OCCUPANCY = _UNKNOWN_DONOR_EXCLUDE | {"Warehouse"}
   ```
   with a comment naming **OPEN-55, ruling B+, 2026-08-19**.
2. Apply the screen **inside `_build_unknown_loads`**, at the `bounds` construction (`:247`) and at
   the `scalar_cols` median — *not* at the call site (`:366`), which must keep passing the full table
   unconditionally so OPEN-49's ruling 3 stays intact and visible.
3. `occupant_m2_per_person` uses `_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY`; the other three PDE columns and
   the four setpoints use `_UNKNOWN_DONOR_EXCLUDE`.
4. **Guard:** if screening would empty the pool for a column, raise — do not silently fall back to the
   unscreened table.
5. Do **not** touch `_per_building_rng` (`:212-222`) or the `dc_archs` set at `:383-386`.

**How to test.** New file `tests/test_semantic_unknown_bounds.py`:
- the screened equipment bounds are `[2.58, 16.15]` and the screened uniform median is `9.37`
  (2 dp), matching §7A's table exactly;
- the screened occupancy bounds exclude `Warehouse` and the unscreened ones do not;
- **reproducibility is preserved** — two calls with the same `osm_id` and `config.RANDOM_SEED` give
  bit-identical draws, and a *different* `osm_id` gives a different draw;
- **cell-independence is preserved** — the same `osm_id` draws identically whether or not other
  archetypes are present in the frame (this is OPEN-49's property; the test must fail if T01
  reintroduces the dependence);
- **non-vacuity:** widen the exclusion set to empty in the test and assert the ceiling returns to
  5381.96, proving the assertions are load-bearing.

Then `pytest -q tests/` — the baseline is **1875 passed, 55 skipped, exit 0** (~27 min). **Any
movement in `passed` other than the new file's own tests is a stop-and-report.**

---

### T02 — OPEN-55: the falsifiable acceptance test on `nyc_suburban`

**What.** Re-run the single cell `nyc_suburban` on its **frozen** `01_buildings.gpkg`, with T01's
change and nothing else, and score the proposal's §8 prediction.

**Pre-registered prediction, written before the run.**
> `nyc_suburban` — 1,589 buildings, 290 Unknown, **71 divergences today** — returns **zero
> divergences**. The screened ceiling is 16.15 W/m² against a lowest observed failure of ~2,496 W/m²,
> a factor of 155 below.

**If any building still diverges, the OPEN-55 mechanism is incomplete and the remedy is not the whole
story.** Report that outcome exactly as loudly as the success.

**Why.** This is the item's own acceptance criterion, it costs one cell (~45 min), and its inputs are
already seeded on disk. No fleet run is needed.

**How.**
1. **Re-verify on disk first:**
   `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/nyc_suburban/01_buildings.gpkg` present, and
   MD5 unchanged against the run-2 original. If absent → **stop and report**; do not re-fetch OSM.
2. Drive it with `scripts/validation/open48_fleet_run3.py` restricted to one cell. Detached, so it
   survives the agent. **Four concurrent maximum** — the six-concurrent setting of run 2 saturated the
   SSH link and killed two cells on transport.
3. `_preflight` must pass before launch.
4. Confirm from the cell's own log that step 1 reports **loading the cached GDF** and that **no OSM
   fetch occurred**.

**How to test.**
- **Primary:** divergence count, target 0 of 290.
- **Control 1 (non-vacuity):** the Unknown rows' drawn `equipment_w_m2` all fall in `[2.58, 16.15]`.
  If any exceeds it, T01 did not take effect and the zero is meaningless.
- **Control 2:** the classified (non-Unknown) buildings' results are unchanged against run 3 —
  the screen touches Unknown rows only.
- **Secondary, required in the same pass:** report the cell's EUI movement as a number. The occupancy
  median moves 235 → 49 m²/person and roughly half the Unknown rows shed an absurd equipment load.
  **That movement is a correction, not a regression** — but it is reported, never absorbed silently.
- **Do not aggregate to a fleet figure.** One cell is one cell.

---

### T03 — OPEN-56 / OPEN-01: does the `Zone.Volume` anomaly reach the EUI denominator?

**What.** A fleet-wide census comparing EnergyPlus's own simulated floor area (from `eplusout.eio`)
against `footprint_area_m2 × levels`, and a targeted check of whether
`nyc_centre/relation_3566904`'s ÷4.18 Total-Building-Area shift is unique.

**Why.** Since OPEN-01's remedy landed, **the project's EUI denominator is EnergyPlus's own simulated
floor area.** The overnight pass observed that writing `Zone.Volume` changed that area by a factor of
4.18 on one building of sixty and deliberately did not generalise. If it is not unique, the OPEN-56
remedy reaches the **denominator**, not just the numerator — and the +0.98 % cost figure is wrong.

**How.**
1. Parse simulated floor area from every available `.eio` in the run-3 corpus
   (`open48_refleet3/<cell>/sim_out/`), re-verifying presence on disk first.
2. Join to `footprint_area_m2 × levels` from each cell's `01_buildings.gpkg`.
3. Report the ratio distribution: median, IQR, and the count outside ±10 %, per cell and pooled.
4. For any building whose ratio sits near 4.18 or is otherwise an outlier, check whether it carries a
   **multiplier** — the OPEN-01 remedy is multiplier-aware and a multiplier is the expected benign
   explanation. Separate benign multiplier cases from genuine anomalies and report both counts.
5. Re-check `relation_3566904` specifically, in both arms if both survive.

**How to test.**
- **Control:** buildings with `levels = 1` and no multiplier must show a ratio ≈ 1.0. If they do not,
  the join is wrong and the census is void.
- **Control:** the total row count reconciles against the cell's building count, with drops itemised.
- **Stop condition:** if more than a handful of buildings show the ÷4.18 pattern *without* a
  multiplier explanation, **stop and report before generalising** — that finding is bigger than this
  task and changes OPEN-56's cost model.

---

### T04 — OPEN-35: an intervention with a control on the storey-count contradiction

**What.** Take a sample of the 2,611 buildings persisted at `levels = 1.0`, rebuild them at the
storey count the **archetype** was chosen on, and run both arms.

**Why.** The register's named next step, verbatim: the +47.9 % gap *cannot* be settled
cross-sectionally because X04 showed it is **composition, not effect**. Only an intervention with a
control can size it — exactly the design that worked for OPEN-56.

**How.**
1. Sample from the **1,031** buildings given a mid- or high-rise archetype and built as a single
   storey — that is the population where the two fallbacks disagree hardest. **Stratify across cells**
   and record the sampling rule before drawing. Target 40–60 buildings, capped by wall-clock.
2. **Baseline arm:** as built today, `levels = 1.0`.
3. **Treated arm:** the same buildings at the group-median storey count the archetype was selected on.
   Change the storey count and nothing else. Record exactly what was changed and where.
4. Run both arms locally. **Four workers maximum**; `energyplus -x`; verify empty output directories
   serially before scoring them.
5. Report per-building Δ EUI, the sign distribution, and whether the effect is per-building or
   per-storey — the same two normalisations X02 used, with their coefficients of variation, because
   that comparison is what refuted the per-zone model for OPEN-56.

**Pre-register the prediction before running.** State the expected sign and rough magnitude, and
report it whether it holds or fails.

**How to test.**
- **Control:** both arms complete on the same buildings. A building that fails in one arm is dropped
  from **both** and the drop is itemised — selective drops are the §4A.4(b) bias this arc has been
  burned by.
- **Control:** the treated arm's IDFs actually carry the new storey count; assert it, do not assume it.
- **Control:** an untreated hold-out subset reproduces the baseline to EnergyPlus float noise.
- **Do not restate 157.1.** A stratified sample is not population-weighted.

---

### T05 — OPEN-38: measure the five unmeasured `LAUNDRYROOMFLR1` fatals

**What.** Rebuild locally the `layout_assign` IDFs for `way/401910463` and the four other unmeasured
fatals of the seven, and test whether the thermal runaway reproduces.

**Why.** The item's stated blocker is *"no IDF survives for them"*. **That is a corpus statement, not
a capability statement** — the same class of stale blocker that was falsified twice on 2026-08-18.
The IDFs can be built. Two of the seven were measured; five were not.

**How.**
1. Identify the seven failing buildings from the E02 failure census (`nyc_rural` ×3, `la_centre` ×1,
   `la_urban` ×3) and record which two are already measured.
2. Rebuild each in `layout_assign` mode from its cell's frozen `01_buildings.gpkg`.
3. Run with `energyplus -x`. Grep the **two-space** form `"**  Fatal  **"` — the one-space form is the
   known E-LA-21 defect and misses real fatals.
4. For each: does the runaway reproduce? Which zone carries the Severe? What is the temperature?
5. Test the open geometry hypothesis: do the failing buildings share a condition the surviving
   `layout_assign` buildings in the same cell do not? **Use a matched control set** from the same
   cells — a signature present on healthy buildings refutes it, which is how the unfitted-subsurface
   lead was killed.

**How to test.**
- **Control (positive):** at least one of the two already-measured fatals is rebuilt too and must
  reproduce its known signature. If it does not, the rebuild is not faithful and **the other five
  results are void**.
- **Control (negative):** a matched healthy `layout_assign` building from the same cell completes.
- **Do not merge OPEN-38 into OPEN-42.** They were ruled separate on 2026-08-18 on five disagreeing
  axes. If this task finds evidence against that ruling, report it — do not act on it.

---

### T06 — OPEN-47: how much of the fine-classification error is the two untraced thresholds?

**What.** A sensitivity sweep of `_OFFICE_SMALL_MAX_M2` (2322.0) and `_OFFICE_MEDIUM_MAX_M2` (9290.0)
against the tag-rich fixture, measuring top-1 accuracy as a function of the thresholds.

**Why.** OPEN-22's closure handed this item its next measurement: the tag-rich exam scores **88.8 %
fine / 100 % coarse on 98 graded rows — all 11 errors sit inside the correct coarse class**, and the
office size tier is what splits a coarse class into fine ones. The thresholds have **no traceable
external primary source** (they are exact conversions of CBECS survey bin edges). If accuracy is flat
across a wide band, the provenance gap is harmless and the item can close on that basis; if it is
sharply peaked at 2322/9290, the untraced numbers are load-bearing and that is a finding.

**How.**
1. Read the thresholds at `openubem/semantic/building_classifier.py:159`. **Do not edit the file** —
   parameterise the sweep in the analysis script by monkeypatching or by calling the classifier with
   overridden constants.
2. Sweep each threshold over a defensible grid (e.g. ±50 % around its current value, plus the exact
   ft² bin edges 25k/100k and neighbouring CBECS edges), jointly where the grid allows.
3. Score **fine** top-1 and **coarse** top-1 at each point on the tag-rich fixture.
4. Report: accuracy surface, the location and width of the plateau containing 2322/9290, how many of
   the 11 errors move under any setting, and whether any setting beats 88.8 %.

**How to test.**
- **Control:** at the current values the sweep must reproduce **88.8 % fine / 100 % coarse on 98
  graded rows**, to four decimals, matching `extra/FIX_open-22_tagrich-gate.md`. If it does not, the
  harness is wrong and no other number in this task is quotable.
- **Neither fixture is edited.** Binding since 2026-08-13.
- **Every accuracy figure names its fixture.** Also binding.
- **This task changes no threshold.** If a better setting exists, it is **reported and recommended**,
  never applied — a classifier change is gated by OPEN-31's before/after discipline.

---

### T07 — OPEN-12 / OPEN-35: is the height-residual population a strict subset of the storey-count population?

**What.** Compute the exact overlap between OPEN-12's missing-height population (2,806 / 8,160
fleet-wide, 3 cells at 100 %) and OPEN-35's `levels = 1.0` population (2,611 / 8,160), building by
building.

**Why.** The register asserts *"1,589 of `nyc_suburban`'s buildings have neither input, so they are
61 % of OPEN-35's 2,611"* and calls the two items *"the same population seen from two sides"* —
**stated, never computed.** Two items that are one population should not be tracked as two; two items
that merely overlap must not be folded. Cheap, and it decides a closure.

**How.**
1. Build both populations from the fleet's Stage-1 files. Do **not** reuse either item's carried
   figure — re-derive both, and report any disagreement with the carried number as a finding.
2. Full 2×2 contingency, fleet-wide and per cell: missing height ∧ `levels = 1`, missing height only,
   `levels = 1` only, neither.
3. Check the specific `nyc_suburban` claim: 1,589 with neither input.
4. State the verdict in one line: strict subset, proper overlap, or largely disjoint.

**How to test.**
- **Control:** the four contingency cells sum to 8,160 exactly.
- **Control:** the marginals reproduce 2,806 and 2,611, or the discrepancy is reported as the finding
  it is.
- **Print the imputation tier distribution** for any re-derived imputed column and check it against
  the fleet's `data_quality_flag` census before quoting a number (hard rule 10).
- **Recommend, do not take, any merge.** Folding one item into another is the user's call.

---

### T08 — OPEN-29: adjudicate the eight forwarded defects that are still open

**What.** For each of the 8 (of 12) defects whose last recorded status is OPEN and that this register
never adopted, produce a signed disposition: **still open at HEAD / closed elsewhere / not
reproducible / adopt as a register item**.

**Why.** X07 established that the adoption material exists and that **4 of the 8 have no signature at
all**. The item cannot close while defects sit in an unadjudicated limbo, and adjudication is the only
remaining work on it — there is no measurement left to make.

**How.**
1. List all eight with their defining line and last recorded status.
2. For each, test the defect's stated signature **at HEAD** — code read, test, or artifact, whichever
   the defect's own statement calls for. Cite the line.
3. For the four with no signature, say so plainly and propose the narrowest signature that would
   settle it. **Do not invent a verdict where no signature exists.**
4. Produce the disposition table. Under the user's standing instruction of 2026-08-12, no-compute
   dispositions of this kind are the **director's** call — so the executor produces evidence and a
   recommendation, and the director rules.

**How to test.**
- **Control:** E-LA-21 must re-derive as CLOSED-ELSEWHERE (its one-space `has_fatal` defect is fixed
  at HEAD across all eight harvest sites). A harness that cannot reproduce that known verdict is not
  trusted for the other seven.
- Every verdict carries a citation. A verdict without one is not a verdict.

---

### T09 — Execute ruling R2: close and retire OPEN-42, OPEN-11, OPEN-07, OPEN-08

**What.** Take the four closures the user ruled. Write each item's closure record into its own
§-section, strike its §1 table row, retire the ID, and re-count the register programmatically.

**Why.** Ruling R2. All four have been recommended-and-untaken for one to two passes; each has its
evidence already on disk.

**How.** For each item, in its own §-section:
- **OPEN-42** — closes by **folding into OPEN-56**. Record what OPEN-56 explains (the `Warehouse`
  fatal concentration and its EUI reach) and, explicitly, **anything OPEN-56 does not explain**. A
  fold that quietly drops a residual is a records defect, not a closure.
- **OPEN-11** — same fold. Record that the "inverted geometry" label was **tested and not
  corroborated** (the upside-down-surface warning is universal to all 8,160 `auto` runs, not
  distinctive to these six) and that the remediation decision is **absorbed by OPEN-56's remedy**, not
  silently dropped.
- **OPEN-07** — closes on: all three buildings succeed at HEAD, and all three were simulated as
  `SmallHotel`, not the `SmallOffice` the file records. **Carry the provenance fact forward** — it
  outlives the item.
- **OPEN-08** — closes on X05: vintage half **0.0368 %** (3 / 8,160), archetype control **0.0000 %**
  on the same join. **Carry the correction forward:** *"E02 is gone"* is too strong — the parquet
  manifests survived; what is gone is E02's `.sql` and `.idf`.

Then:
- strike each §1 row with a dated closure note, in the **same edit** that closes it — the
  missing-row failure of 2026-08-10 is not repeated;
- update the header count, the retired-ID list, and the reconciliation prose;
- re-run `scripts/analysis/open_register_recount_2026-08-18.py` and quote its output.

**How to test.**
- **The recount is programmatic, not asserted.** Expected after this task: **21 live / 35 struck / 56
  total**, OPEN-01…OPEN-56, none missing, none duplicated, next free `OPEN-57`.
- **The reconciliation invariant must hold:** *struck rows − retired IDs = 2*, the 2 being OPEN-02 and
  OPEN-28. After this task: 35 struck − 2 = **33 retired IDs**. If the prose disagrees with the
  script, **the script is right and the prose is corrected**.
- **No debt is lost with an ID.** Each of the four closure records names what survives it.
- Note in the record that **T01 changes shipped code and OPEN-55 stays open** until T02 scores it —
  no closure in this task depends on T01.

---

### T10 — Execute ruling R3: preserve the cited evidence, then restate OPEN-53

**What.** Copy into the repository the run-2 / run-3 material that open items actually cite, with a
hash manifest, and restate what remains of OPEN-53's closure condition.

**Why.** Ruling R3. **43 GB sits under `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/`** — a
volatile path of exactly the class the 2026-08-17 sweep emptied — and it is load-bearing for OPEN-56,
OPEN-42, OPEN-11, OPEN-07, OPEN-09, OPEN-35 and OPEN-12. **The material actually cited is under
0.12 GB.**

**How.**
1. **Re-verify on disk first.** If the tree is already gone, **stop and report** — that is a finding
   in itself and the largest one this pass could produce.
2. Enumerate what open items cite: the six OPEN-42 buildings' and three OPEN-07 buildings' IDFs plus
   their `eplusout.err` / `.end`; the OPEN-56 A/B arms' `.err` and result vectors; the per-cell result
   CSVs backing OPEN-35 and OPEN-12; anything T02–T05 produce that a future task would need.
3. Copy to `docs/validations/overAll/evidence/open48_runs/`, preserving the
   `<run>/<cell>/<building>/` shape.
4. **Never copy `.sql`.** It is 95 % of the volume and nothing cites it.
5. Write `MANIFEST.md` beside it: source path, MD5, size, byte count, copy date, and **which open item
   cites each file**. A preserved file nothing cites should not be copied.
6. **Hard cap 0.15 GB.** If the enumeration exceeds it, stop and report rather than copying more —
   the budget is what the ruling was given on.
7. Restate OPEN-53's closure condition against what is now durable, and name precisely what is still
   only on the volatile path.

**How to test.**
- **Control:** every MD5 in the manifest re-verifies against the copy. A copy that does not verify is
  deleted and reported, not kept.
- **Control:** total size under the cap; report the actual figure.
- **No git write commands.** Files land in the working tree; committing is the user's, externally.
- Report the residual honestly: this discharges the condition **for the work that depends on the
  copied files**, and for nothing else. OPEN-53 stays open on the standing risk.

---

## 7. Stop-and-report points

| CP | after | what the director checks before the pass continues |
|---|---|---|
| **CP-1** | T01 | The screen is at `_build_unknown_loads`, **not** at the call site; `:366` still passes the full table unconditionally. Bounds re-derive to `[2.58, 16.15]` and median `9.37`. OPEN-49's per-building seed and cell-independence still hold, proved by the new tests. Non-vacuity probe passes. Full suite matches **1875 / 55 / exit 0**. **Nothing downstream runs until this is signed** — T02 measures a code change, and an unverified code change makes its zero meaningless. |
| **CP-2** | T02 + T03 | T02: the divergence count with **both** controls, and the EUI movement reported as a number. T03: the ratio census with its `levels = 1` control, and whether the ÷4.18 pattern is unique. **If T03 finds the anomaly is not unique, stop the whole pass and report** — OPEN-56's cost model and the EUI denominator are both implicated and that outranks the remaining tasks. |
| **CP-3** | T04 + T05 + T06 + T07 | Each task's controls signed individually. T04's and T05's positive controls are the load-bearing ones: a treated arm that did not change, or a rebuild that does not reproduce a known fatal, voids its task's numbers. |
| **CP-4** | T08 + T09 + T10 | The programmatic recount output is quoted, not asserted. The reconciliation invariant holds. Every closure record names what survives it. The evidence manifest verifies and is under cap. Plan closed. |

---

## 8. Progress log

*(One entry per completed task, appended by the executor:
`#### TXX — <title> — completed YYYY-MM-DD`, then **Artifacts / Deviations / Test status / Notes**.)*

#### T06 — OPEN-47: sensitivity sweep of the office size-tier thresholds — completed 2026-08-19

**Artifacts:**
- `scripts/analysis/open47_threshold_sweep_2026-08-19.py` — new analysis script, monkeypatches
  `_OFFICE_SMALL_MAX_M2` / `_OFFICE_MEDIUM_MAX_M2` in `openubem.semantic.building_classifier` in a
  `try/finally`, per-call, and asserts restoration before exit. Does not import from `tests/`; the
  test module's `_COARSE_CLASS_MAP` (mirrored, line-cited) is reproduced locally since it is not
  exported by the classifier module.
- `openubem/outputs/comparisons/open47_threshold_sweep.csv` — 782 scored grid points (2 of 784
  skipped for invalid `small_max ≥ medium_max` ordering).
- `openubem/outputs/open47_threshold_sweep_surface.png` — fine top-1 accuracy heatmap over the
  grid, current values marked, CBECS bin edges overlaid.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-47_threshold-sensitivity_2026-08-19.md` —
  full write-up.

**Result, in one line:** none of the 782 grid settings beats the current 88.8% fine top-1, none
fixes any of the 11 baseline fine errors, and coarse top-1 stays 100.0% everywhere on the grid —
the two untraced thresholds explain **zero** of OPEN-47's residual fine error. 3 of the 11 errors
never route through `_office_size_tier` at all (residential-tier / high-rise rules); 3 more are
`OpenUBEMUnknown`-expected rows where an office was wrongly emitted at all (unreachable by this
sweep, since `_office_size_tier` never returns `OpenUBEMUnknown`); the remaining 5 route through
the office-size rule but their footprint areas are small enough that the miss is attributable to
`levels_imputed` (a different, un-swept quantity), not to where the bin edge sits.

**Test status:**
- **Control (mandatory):** reproduced 87/98 = 0.8878 fine, 98/98 = 1.0000 coarse on the 98 graded
  rows of `tests/fixtures/labelled_archetypes_tagrich_v2.csv`, matching
  `extra/FIX_open-22_tagrich-gate.md` to four decimals. Script would have halted before sweeping
  had this not reproduced; it reproduced, so the sweep proceeded.
- Module-constant restoration checked and printed after the sweep: `True`
  (`_OFFICE_SMALL_MAX_M2=2322.0, _OFFICE_MEDIUM_MAX_M2=9290.0`).
- No pytest run for this task — the classifier was called directly from the analysis script, per
  the dispatch instruction (the concurrent full-suite run elsewhere was not touched).

**Deviations from the plan:** none. No threshold was changed in `building_classifier.py`. Neither
fixture was edited. No fleet/production code was touched. The "how many of the 11 errors move"
figure required separating *resolved* (fixed) from *newly broken* (previously-correct rows broken
by a worse setting) — the plan's phrasing ("how many...move") was read as asking about the 11
specifically getting fixed, which is 0; the 31 previously-correct rows that get broken elsewhere on
the grid are reported alongside as the reason no setting nets an improvement.

**Notes:** this measurement does not touch OPEN-47's separate, still-open provenance/area-vs-floor-
count question (Chen, Hong & Piette 2017 is a case-study table, not a cited external standard; the
source's rule is area AND floor count while the code is area only) — that finding stands
independently and this task recommends nothing about it. No new item is opened; a possible next
lead (`_impute_levels` / rule-entry conditions for the 5 `RULE_USE_CLASS_SIZE` rows) is named in
the write-up §6 as a recommendation only, not taken.

---

#### T03 — OPEN-56 / OPEN-01: does the `Zone.Volume` anomaly reach the EUI denominator? — completed 2026-08-19

**Artifacts:**
- `scripts/analysis/open56_denominator_census_2026-08-19.py`
- `openubem/outputs/comparisons/open56_denominator_census_2026-08-19.csv` (6,804 rows, per-building)
- `openubem/outputs/comparisons/open56_denominator_census_cellsummary_2026-08-19.csv` (reconciliation)
- `openubem/outputs/comparisons/open56_denominator_census_outliers_2026-08-19.csv`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56_denominator-census.md`

**Disk re-verification (before use, per hard rule 11):** `open48_refleet3` re-checked cell by cell.
**10 / 12 cells have run-3 simulation output; `la_urban` and `nyc_centre` have none** (zero `.eio`
files, despite IDFs present). `nyc_centre` is the cell the ÷4.18 finding came from — its own cell
cannot be searched. The separate OPEN-56 A/B work directory
(`%TEMP%/open56_fleet_cost/nyc_centre__relation_3566904/`) survives independently and was used for
the targeted recheck.

**Result:**
- **Reconciliation control passed exactly** (10/10 available cells, `idf == sim_out == gpkg`, zero
  drops) after fixing a bug caught by the control itself: `stem_to_osm_id()` was merging the two
  `_partN`-suffixed stems in `nyc_urban` (`relation_17953040_part0/1`) back into one osm_id; the source
  `.gpkg` stores these as two separate pre-split rows. Fixed before reporting any number.
- **`levels==1`, no-multiplier control passed**: 71 buildings, ratio median 1.0000, IQR
  [0.9992, 1.0005].
- **Coverage caveat, load-bearing:** only 274 / 6,804 available-corpus buildings (4.03%) have a
  usable declared area — the other 6,530 are dropped for missing `levels` (OPEN-35's population).
  This structurally excludes the building class the known anomaly came from: `relation_3566904` itself
  has `levels = NaN`.
- **Pooled ratio among the 274 checkable: median 1.0000, IQR [0.9997, 1.0000]. 4 / 274 (1.46%)
  outside ±10%**, all in `la_centre`, ratio **1.12–1.18** (opposite direction and different magnitude
  from ÷4.18), no multiplier explanation, no underground/excluded-zone explanation found. Reported as
  a separate, smaller, unexplained lead — **not folded into OPEN-56.**
- **Stop condition (T03 "How to test") not triggered** — zero of the checkable buildings sit near the
  1/4.18 ≈ 0.239 ratio.
- **Targeted recheck of `relation_3566904` reproduces the overnight figures exactly**: baseline
  157,115.5 m² / treated 37,551.2 m², ratio **4.1840**, matching `157115/37551 = 4.1840` to 4
  decimals. Cross-validated by two independent extraction routes (raw `.eio` parse vs EnergyPlus's own
  `.sql` "Building Area" table) agreeing to 6 decimal places — **the original finding is confirmed
  real, not a single-method artifact.**

**Verdict, stated plainly (see write-up §5):** the anomaly reaches the denominator on the one building
where it is known to occur — confirmed twice, independently. **Whether it is unique fleet-wide is not
answered** by this census: the join (raw `levels`, as the plan specifies) covers 4% of the corpus and
structurally cannot reach the building class or the cell the known instance lives in. This is a real
negative result on a narrow slice, not a fleet clearance.

**Deviations:** none from the plan's How steps. One implementation bug (part-stem merge) was found and
fixed by the reconciliation control before any number was reported, per hard rule 8/9.

**Test status:** both specified controls passed (reconciliation exact; `levels==1` no-multiplier ratio
≈ 1.0000). Stop condition evaluated and not triggered.

**Notes for the next session:** OPEN-56's +0.98% / +0.84% fleet cost figure is unaffected — it already
excluded `relation_3566904` (overnight pass) and nothing here changes that 69-building sample.
Recommended, not taken: re-run with an imputed storey count so `relation_3566904`-like buildings become
checkable, and/or get `nyc_centre` / `la_urban` simulated in run 3 so the home cell of the known
instance can be searched directly.

#### T07 — OPEN-12 / OPEN-35: subset check — completed 2026-08-19

**Pre-registered prediction (before running):** by the two items' own stated definitions
(OPEN-12 = height missing, regardless of `levels`; OPEN-35 = neither `levels` nor `height_m`),
OPEN-35's predicate nests inside OPEN-12's, so OPEN-35 must be a **strict subset** of OPEN-12,
never the reverse. Expected residual (OPEN-12 \ OPEN-35) = 2,806 − 2,611 = 195 fleet-wide.
Expected `nyc_suburban` neither = 1,589, and 1,589 / 2,611 ≈ 60.86 % (≈ 61 %, matching the
register's claim), with height_null == neither exactly inside that one cell (100 % missing
both). **Every part of the prediction held — no discrepancy anywhere in this task.**

**Artifacts:**
- `scripts/analysis/open12_open35_subset_check_2026-08-19.py`
- `openubem/outputs/comparisons/open12_open35_subset_check.csv` (per-cell contingency)
- `openubem/outputs/comparisons/open12_open35_subset_check_buildings.csv` (8,160 per-building rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12-35_subset-check_2026-08-19.md`

**Results.** Re-derived fresh on run 2 (`open48_refleet`, all twelve Stage-1
`01_buildings.gpkg` re-verified present before reading — hard rule 11). Both carried figures
reproduced **exactly**: OPEN-12 2,806 / 8,160 = 34.39 %; OPEN-35 2,611 / 8,160 = 32.00 %.
Fleet-wide 2×2 contingency sums exactly to 8,160 (both present 246 / height-only 195 /
levels-only 5,108 / neither 2,611). **Verdict: OPEN-35 is a strict (proper) subset of OPEN-12**
— every "neither" building is by construction also a "height missing" building. The residual
(OPEN-12 \ OPEN-35) is **195 buildings fleet-wide (6.95 %)**, concentrated in `austin_centre`
(102) and `austin_suburban` (40), with smaller counts in six other cells and zero in
`nyc_suburban`/`nyc_rural`/`la_suburban`. `nyc_suburban`'s claim checked to the building: 1,589
matches exactly, 60.86 % of 2,611 matches the stated "61 %", and inside that one cell the two
populations coincide exactly (both 1,589) — this is the cell driving the register's "same
population" framing, correct for that cell but not fleet-wide. Control: all 2,611 "neither"
buildings persist at `levels = 1.0` in `05_results.csv`, 100.0000 %, no exceptions —
reconfirms OPEN-35's already-established mechanism on this corpus.

**Hard rule 10 compliance.** Cross-checked the Stage-1 `data_quality_flag` tokens (`no_height`
/ `no_floors`, stamped independently at acquisition, `openubem/acquisition/osm_fetcher.py:510`)
against the `.isna()` predicates used to build both populations, in every cell. **Zero
disagreements fleet-wide, on both tokens.** Present-but-zero `height_m`: 0 fleet-wide,
confirming the register's note. This is the acquisition-time independent check the rule calls
for; no imputation-pipeline tier (HOTDECK/GROUPMODE/knn_fill) is exercised by this task, since
both populations are built on raw Stage-1 `levels`/`height_m` nulls, never on an imputed value
— the one persisted/derived quantity touched (`levels` in `05_results.csv`) was checked as a
control (100 % at 1.0, above), not quoted as a headline figure.

**Deviations from the plan:** none. Corpus is `open48_refleet` (run 2), the same corpus X04
(2026-08-18 overnight) used and matched exactly — not `open48_refleet3`, which is mid-run for
T02's single cell and has no fleet-wide results yet; this is noted for anyone auditing corpus
choice, not a deviation from anything the plan pinned (the Dependency Decisions section pins
`open48_refleet3` for T02 only).

**Test status:** all controls in the task's "how to test" section passed — 2×2 sums to 8,160;
both marginals reproduce; nyc_suburban claim verified to the building; recommendation stated,
not taken.

**Notes / recommendation (not taken — user's call).** OPEN-35 is not equal to OPEN-12; it is a
proper subset covering 93.05 % of it. A merge of the two items would need to explicitly carry
forward the 195-building residual that only OPEN-12 covers (height missing, levels observed),
or the merge would silently drop a real, if small, tracked population. Recommending against a
same-item merge; recommending the two stay separate with this overlap recorded in both items'
sections, per ruling R2's own instruction that this plan does not take OPEN-12/OPEN-35 merge
decisions.

---

#### T08 — OPEN-29: adjudicate the eight forwarded defects — completed 2026-08-19

**Artifacts:**
- `openubem/outputs/comparisons/open29_eight_defect_adjudication_2026-08-19.csv` — per-ID
  disposition table with citations.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_eight-defect-adjudication.md` — full write-up.
- No new analysis script — two existing, already-audited scripts were re-run live instead of
  writing a third: `scripts/analysis/open09_fleet_err_taxonomy.py` and
  `scripts/analysis/open35_open10_consequence_census.py`. Both regenerated CSVs are byte-identical
  to their committed versions (`git diff --stat` empty), so the committed artifacts are confirmed
  current, not stale.

**Control (mandatory before the other eight): E-LA-21 re-derives as CLOSED-ELSEWHERE. PASSED.**
Re-grepped all eight harvest sites named in the register
(`t07_harvest_results.py:199`, `t07b_run_auto_refit_local.py:330`, `t08_harvest_results.py:246`,
`t08_local_remainder.py:431`, `t17_harvest_layout_assign.py:255`, `t18_harvest_layout_assign.py:252`,
`t19_harvest_layout_assign.py:260`, `t20_harvest_layout_assign.py:260`) — all eight carry the
tolerant `re.search(r"\*\*\s+Fatal\s+\*\*", err)`; a repo-wide search for the one-space literal
`"** Fatal **"` under `scripts/` and `openubem/` returns zero hits. `git log --since=2026-08-18`
across all eight files shows one commit (`b2d0220`), a comment-only correction on
`openubem/geometry/layout_assigner.py` (the E-LA-16 naming fix), no functional change.

**Disposition, all eight (full citations in the CSV):**

| ID | HEAD signature | Verdict |
|---|---|---|
| E-LA-06 | 32/8,160 (0.39%), Warning, matches its own mechanism | STILL-OPEN; overlaps OPEN-18 |
| E-LA-15 | 0/8,160 in the tested (auto-mode) corpus | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED |
| E-LA-16 | 1/8,160 (0.01%), Warning only | STILL-OPEN, immaterial-scale; overlaps OPEN-51 (naming only) |
| E-LA-17 | 16/8,160 (0.20%), exact population match to OPEN-09 | STILL-OPEN mechanism, NOT A SEPARATE DEFECT |
| E-LA-18 | 0/8,160 — zero `CheckWarmupConvergence` anywhere | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED |
| E-LA-19 | named building present, succeeds cleanly, 0 signature | NO SIGNATURE IN TESTED CORPUS — NOT ADJUDICATED |
| E-LA-30 | 🔴 reproduces at HEAD by direct code/format read (new this pass) | STILL-OPEN, CONFIRMED |
| E-LA-33 | 93.32% inert (497/7,442 applied), inside its own 82–98% band | STILL-OPEN, CONFIRMED |

**🔴 Correction to X07's framing, not just a re-confirmation.** X07 grouped E-LA-30 with the three
genuinely signature-absent defects under "no signature anywhere." That is imprecise: E-LA-30 was
never an `.err`-testable defect — its own statement calls for a code/artifact read, which this task
performed for the first time. `fast_scale_idf_text()`
(`scripts/analysis/a4_bis_generate_layout_assign_viewer.py:17-42`) only scales a vertex line when
`"Xcoordinate"`/`"Ycoordinate"` (no hyphen) appears in it. The true input population
(`openubem/config.py:49-52` `BASELINE_IDF_DIR`) is the 25 DOE/ASHRAE prototype IDFs; read directly,
`ASHRAE901_OfficeSmall_STD2022_Buffalo.idf:2058-2060` writes vertices as
`5,13.46,0,  !- X,Y,Z ==> Vertex 1 {m}` — the substring never appears, so the branch is dead code
against the real source, not merely against a proxy. This mechanically reproduces the "content
no-op on all 25 prototypes" claim by direct verification. **Verdict: STILL-OPEN, confirmed
reproducing** — not the "no signature" bucket X07 placed it in.

**Overall recommendation on OPEN-29 (evidence + recommendation only — director rules, per the
user's 2026-08-12 standing instruction on no-compute dispositions).** The item cannot close. Two
IDs (E-LA-06, E-LA-16) are confirmed still open with a real, sized `.err` signature; two
(E-LA-30, E-LA-33) are confirmed still open by direct code/artifact verification; one (E-LA-17) is
a live mechanism that duplicates OPEN-09's population exactly and should be struck from OPEN-29's
inherited list as a merge finding, not a fix; three (E-LA-15, E-LA-18, E-LA-19) remain genuinely
unadjudicated because they were raised under `layout_assign` mode and run 2 — the only corpus this
read-only task could reach — is `auto` mode. None of the eight is fixed; none warrants promotion to
a new top-level `OPEN-nn` item. **Recommended, not taken:** strike E-LA-17 from OPEN-29's tracked
list (merge into OPEN-09); before the next attempt to adjudicate E-LA-15/18/19, run three narrow
local `layout_assign` rebuilds — `way/965718401` (E-LA-15), `way/86121620` + `way/42496352`
(E-LA-18), `way/241836727` (E-LA-19) — each is a single named building, not a fleet sweep, and does
not need Speed. No new register items opened; the register itself was not edited by this task (T09
is where closures land, and none of the eight closes on this evidence).

**Deviations from the plan:** none. No production code touched. Two existing analysis scripts were
re-run rather than a new one written, since re-verifying already-audited tooling is stronger
evidence than reading a static CSV and needed no new code (hard rule 11).

**Test status:** control PASSED (E-LA-21 CLOSED-ELSEWHERE, re-derived independently). Both
regenerated CSVs (`open09_fleet_err_taxonomy.csv`, `open09_fleet_err_perbuilding.csv`,
`open10_storey_expressibility_fleet.csv`) are byte-identical to their committed versions. No pytest
run (excluded by dispatch instruction; a concurrent full-suite run elsewhere was not touched).

**Notes:** CP-4 covers T08+T09+T10 together and is not signed by this entry alone — only T08 is
complete. Stopping here per dispatch instruction to report before continuing into T09/T10.

---

#### T01 — OPEN-55: implement the B+ Unknown donor screen — completed 2026-08-19

**Artifacts:** `openubem/semantic/__init__.py` (modified — `_UNKNOWN_DONOR_EXCLUDE` /
`_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY` constants added next to `_DONOR_ARCH`; screen applied inside
`_build_unknown_loads` via a `_screened_donor_pool()` helper at the bounds/median construction).
`tests/test_semantic_unknown_bounds.py` (new, 10 tests). No other files touched — confirmed via
`git status --short -- tests/ openubem/semantic/` showing exactly these two paths.

**Numbers the code actually produces** (white-box, captured from `_build_unknown_loads`'s own
`bounds` dict via a recording fake RNG substituted for `_per_building_rng`, not re-derived
independently):
- screened equipment bounds: **`[2.58, 16.15]`** — matches §7A exactly.
- screened uniform median: midpoint `(2.58 + 16.15) / 2` computed via `Decimal` on the archetypes'
  own string values = `9.365` exactly, `ROUND_HALF_UP` at 2dp → **`9.37`** — matches §7A exactly.
  Note: plain `float` arithmetic on the same two numbers lands one ULP below `.365`
  (`9.364999999999998`) and Python's `round()` (round-half-to-even, on that already-perturbed float)
  gives `9.36` — a floating-point-representation artifact of the *test's rounding method*, not a
  code defect. The test uses `Decimal(str(lo))`/`Decimal(str(hi))` to avoid it, matching how §7A's
  table was almost certainly computed by hand.
- screened occupancy bounds (using `_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY`, Warehouse additionally
  excluded): `[4.65, 51.10]`.
- non-vacuity check: the *default* pool (data centres + Laboratory + both restaurants excluded,
  Warehouse still present) still carries Warehouse's `464.52` m²/person as its occupancy ceiling —
  proving the occupancy-only exclusion is load-bearing and not redundant with the default one.

**Test status — full suite: 1885 passed, 55 skipped, 11 warnings, exit 0, 1512.29s (0:25:12).**
Baseline was 1875 passed / 55 skipped / exit 0. Delta is **exactly +10 passed, 0 change in skipped**
— the 10 new tests in `tests/test_semantic_unknown_bounds.py`, confirmed independently by running
that file alone first (`10 passed in 0.73s`) before the full run. `grep -niE "FAILED|ERRORS|short
test summary"` over the full log returned nothing. No other test's pass/fail/skip state changed.
The log does contain repeated `Windows fatal exception: access violation` / faulthandler C-stack
dumps, all traced to `joblib`'s `loky` Windows subprocess spawn path inside
`tests/test_sim_integration.py::test_synthetic_fleet_full_annual` (`openubem/simulation/parallel.py:271`
→ `joblib.parallel` → `loky.backend.popen_loky_win32`/`resource_tracker`) — this is
platform multiprocessing noise on stderr, not a test failure; that test is counted among the 1885
passed and pytest's own summary line confirms `exit 0`. Unrelated to this patch (semantic module,
no multiprocessing).

**CP-1 checklist, explicit:**
1. Bounds/median as quoted above — code-derived, matching §7A's `[2.58, 16.15]` / `9.37`.
2. The screen lives **inside `_build_unknown_loads`** (`_screened_donor_pool()` at the `bounds`
   construction and at the `scalar_cols` median). The call site,
   `openubem/semantic/__init__.py:394` (`loads_unk = _build_unknown_loads(out, unk_mask,
   _get_cross_archetype_loads(), rng)`), is **unchanged** and still passes the full, unscreened
   29-row table unconditionally — confirmed by `git diff` showing no edit in that region, and by
   reading the current line directly.
3. OPEN-49's properties hold:
   - **per-building seed / reproducibility** — `test_reproducibility_bit_identical` (two
     `enrich_semantics(gdf, random_seed=42)` calls on the same frame are bit-identical across all
     eight PDE+scalar columns) and `test_different_osm_id_gives_different_draw` (two different
     `osm_id`s in the same frame draw differently).
   - **cell-independence** — `test_cell_independence_preserved_under_screen`: the same two Unknown
     rows (osm_id `way/test_2`, `way/test_3`) draw bit-identically (`atol=1e-9`) whether the frame's
     other two rows are `SmallOffice`/`MediumOffice` or `LargeDataCenterHighITE`/`Laboratory` — i.e.
     even swapping in archetypes that T01 newly excludes from the donor pool does not move the
     Unknown rows' draws, because the bounds come from the fixed cross-archetype table, never from
     what is present in the cell.
4. **Non-vacuity probe:** `test_non_vacuity_probe_widening_exclusion_to_empty_restores_unscreened_ceiling`
   — monkeypatches both exclusion sets to the empty set and asserts the captured equipment ceiling
   reverts to **`5381.96`** (the full unscreened `LargeDataCenterHighITE` value). This test would
   fail if the screen were wired as a no-op (e.g. constants defined but never consulted); it passed,
   so the screen is confirmed load-bearing, not vacuous. A second guard test,
   `test_guard_raises_if_screen_would_empty_the_pool`, monkeypatches the exclusion set to *all 29*
   archetypes and asserts `_build_unknown_loads` raises `ValueError` rather than silently falling
   back to the unscreened table (plan step 4's guard).
5. Full suite: **1885 passed, 55 skipped, exit 0** vs baseline **1875 passed, 55 skipped, exit 0** —
   delta is exactly the 10 new tests, no other movement (see Test status above for the grep/log
   evidence).
6. **`dc_archs` at `openubem/semantic/__init__.py:411-414`** (inside the `probabilistic`
   perturbation branch) is **untouched** — confirmed by `git diff` (no hunk touches that region) and
   by direct read: it still defines its own local 4-member data-centre set, separate from and not
   merged with `_UNKNOWN_DONOR_EXCLUDE`. Per plan step 5 and DESIGN fact 6, the two guard different
   populations (real rows under probabilistic perturbation vs. Unknown-row PDE donor pool) and were
   deliberately not unified.

**Deviations from the plan:** none in the production patch (exact shape specified in T01 §How and
DESIGN fact 3 — screen applied at `_build_unknown_loads`'s bounds/median construction, not the call
site). One test-authoring deviation, disclosed above: the plan's own worked example (§7A) states the
median as `9.37`, computed from decimal values; a naive `round((lo+hi)/2, 2)` in Python float
arithmetic gives `9.36` due to binary floating-point representation of `2.58`/`16.15`. The test uses
`Decimal(str(lo))`/`Decimal(str(hi))` with `ROUND_HALF_UP` to reproduce `9.37` exactly, and this
discrepancy is recorded here rather than silently choosing whichever rounding made the test pass.

**Notes:** T02 (the falsifiable `nyc_suburban` acceptance test) is the next task and depends on this
one; per the plan's CP-1 gate ("nothing downstream runs until this is signed") T02 has not been
started. This entry reports T01 alone.

---

#### T04 — OPEN-35: an intervention with a control on the storey-count contradiction — completed 2026-08-19

**Pre-registered prediction (written before any EnergyPlus run, in
`extra/MEASUREMENT_open-35_storey-intervention.md` §3, before results were seen):** treated EUI
< baseline EUI for all genuine-disagreement buildings (envelope form-factor mechanism), magnitude
scaling with the recovered levels value, and a per-storey (not per-building) CV signature.
**Outcome: sign prediction refuted for the majority (7/11 positive, not negative); magnitude
prediction partially held; the per-storey-vs-per-building CV test was inconclusive (mean near
zero from the sign split makes CV unstable, unlike OPEN-56's one-directional case); the negative-control
prediction (Δ≈0) held exactly.** Full scoring in the write-up §8.

**Census finding, made before spending any EnergyPlus compute (§1 of the write-up) — the
headline result of this task.** Before sampling, this task recovered — by calling
`_impute_levels()` directly with the same `levels_group_median`/`levels_global_median` lookup
step2 builds, code-reused not reimplemented — the storey count that actually drove archetype
selection for **all 1,031** buildings in the register's "mid/high archetype at one storey"
population (not a sample of it; cheap, no IDF built). Result: **only 11 / 1,031 (1.07%) carry a
genuine numeric disagreement** between archetype selection's group-median fallback and
geometry's unconditional 1. The other **1,020 (98.9%)** get the value 1 from *both* fallbacks —
either because the cell has zero ground-truth `levels` rows to compute a median from at all
(`nyc_suburban` + `nyc_rural`, 1,001 buildings, 97.1% on their own — `_impute_levels` returns
`LEVELS_DEFAULT_LOW`, not `GROUPMEDIAN_LEVELS_MED`) or because the group median genuinely
computes to 1 (`austin_rural` + `austin_suburban`, 19 buildings). **The register's "chosen as
though a 19-storey building, built as a 1-storey building" framing describes 11 buildings, not
1,031.** OPEN-35's mechanism and population count are unaffected (both re-derived exactly); this
corrects *why* for the large majority of the population. Full breakdown in the write-up §1.

**Intervention, run on the full census of 11 genuine-disagreement buildings (not a sample — the
census found only 11 exist) plus 10 stratified negative-control buildings (Δ=0 by construction,
seed=42), both arms, in-session, per the OPEN-56 design:**
- `austin_centre` (`HighriseApartment`, recovered levels=45, 3 buildings): **+40.5%, +18.6%,
  +4.6%** — all positive.
- `la_urban` (`MidriseApartment`, levels=7, 3 buildings): **+4.7%, +2.4%, +5.6%** — all positive.
- `nyc_urban` (`MidriseApartment`, levels=6, 5 buildings): **+1.7%, -10.4%, -10.6%, -6.8%,
  -12.6%** — 4 of 5 negative.
- Overall: **7 positive / 4 negative of 11.** Not one-directional. The sign splits along climate
  zone (2A/3B positive, 4A mostly negative) — recorded as a lead, not established causally on
  n=11 across 3 cells.
- **Negative controls: Δ EUI = 0.000000 exactly for all 10.**
- **No fleet figure quoted or implied. `157.1 kWh/m²` is not restated.**

**Two harness bugs found and fixed mid-task, before any number was trusted (both documented in
full in the write-up §4/§6, both discovered by this task's own controls, per hard rule 9):**
1. **Cross-building output contamination.** The first build+simulate pass (borrowing
   `open56_zone_volume_experiment.py`'s `run_ep()` unchanged) produced two "successful" runs
   with byte-identical `eplusout.sql` for two different buildings (different footprint, different
   floor count) — EnergyPlus's `-x` preprocessing appears to consult a cwd-relative file rather
   than one scoped to `-d`. Fixed by giving every invocation its own `cwd=outdir`
   (`run_ep_isolated()`); the full run was redone from scratch and came back clean (0 empty/wrong
   outputs on 42/42 EnergyPlus calls), plus an added contamination control (checks for duplicate
   `(floor_area_m2, site_energy_gj)` across different buildings) that will catch a recurrence.
2. **Wrong EUI formula.** The ad hoc "Total Site Energy ÷ Total Building Area" read borrowed from
   the OPEN-56 script does not match production's actual `total_eui_kwh_m2` (sum of per-end-use
   EUIs over a multiplier-aware `.eio` area, `openubem/results/parser.py`) — this task's own
   fidelity control (fresh baseline vs. archived run-2 EUI for the same 21 buildings) caught a
   systematic +15%–+37% gap and voided every number from the first pass, per hard rule 9. Fixed
   by re-parsing the same completed `.sql`/`.eio` files with production's own `parse_building()`
   (no re-simulation needed); the fidelity control then passed at 0.0047% max / 0.0009% mean
   error.

**Artifacts:**
- `scripts/analysis/open35_storey_intervention_2026-08-19.py` — census (all 1,031, no IDFs) +
  IDF build (both arms, floor-count control asserted from the IDF text, not assumed) +
  isolated-cwd EnergyPlus simulate (4 workers max) + serial re-verify of empty directories +
  cross-building contamination control.
- `scripts/analysis/open35_storey_intervention_reparse.py` — re-parses the completed outputs with
  production's `parse_building()`.
- `openubem/outputs/comparisons/open35_storey_intervention_census.csv` (1,031 rows, no IDFs).
- `openubem/outputs/comparisons/open35_storey_intervention_sample.csv`,
  `_prep.csv` (build-phase manifest + floor-count control), `_results.csv` (**superseded — wrong
  EUI formula, kept for provenance only, do not cite its EUI columns**),
  `_results_v2.csv` (**authoritative**).
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md` — full write-up
  (census, pre-registration, both harness-bug post-mortems, results, prediction scoring,
  verdict).

**Test status — every control in T04's "How to test" and the plan's hard rules:**
- **Both arms complete on the same buildings:** 21/21 (11 treatment + 10 negative control), no
  drops.
- **Treated arm's IDFs actually carry the new storey count — asserted, not assumed:**
  `actual_num_floors_from_idf()` independently parses `BUILDINGSURFACE:DETAILED` Z-extents from
  the IDF text (not the manifest) for every building; all 21/21 matched exactly
  (`floor_count_control_pass` in `_prep.csv`).
- **Untreated hold-out reproduces baseline to float noise:** the 10 true negative controls
  reproduce Δ=0.000000 exactly; the fidelity control (fresh baseline vs. archived run-2, all 21)
  passed at 0.0009% mean / 0.0047% max after the EUI-formula fix (§6) — both stronger than "float
  noise."
- **4-worker cap:** held (`ThreadPoolExecutor(max_workers=4)`); confirmed no more than 4
  `energyplus.exe` processes observed concurrently at any check.
- **Empty output directories verified serially, not scored as failures outright:** 4 occurred on
  the first (pre-fix) run; all 4 reproduced cleanly alone. Superseded by the cwd-isolation fix,
  which produced zero empty/wrong outputs on the clean re-run.
- **Imputation-tier distribution printed and cross-checked:** write-up §8b; the full 1,031-row
  `recovered_lev_src` distribution is the census itself, and its consistency with Stage-1
  `data_quality_flag` is inherited from T07 (same population, same pass, already checked
  fleet-wide with zero disagreements).
- **`01_buildings.gpkg` re-verified present, not re-fetched**, for all 7 cells touched.
- No git write commands. No production code, register, or director prompt edited.

**Deviations from the plan:**
- **Sample size.** The plan's How step 1 targets 40-60 buildings, capped by wall-clock. This
  task's census (run before sampling, and itself not specified as a required step, but necessary
  to draw a sample that means what the plan says it means) found only 11 buildings in the entire
  1,031-population carry the numeric disagreement the plan's Why section describes. The cap that
  actually bound was population availability, not wall-clock, and was not anticipated by the
  plan. All 11 were used (a full census, not a sample of a larger pool) plus 10 negative controls,
  for 21 buildings / 42 EnergyPlus runs total — reported as a finding, not treated as
  non-compliance, per this arc's standing practice of reporting a smaller-than-planned population
  honestly rather than substituting a different measurement.
- **Two harness bugs, both found and fixed mid-task** (§4/§6 above), neither anticipated by the
  plan. Both are documented in full rather than silently absorbed, per hard rule 9's "a control
  that fails voids the numbers it guards" — the first full run's results were discarded entirely,
  not patched.
- No production code changed (T01 remains the only task in this plan that changes shipped code,
  per hard rule 5).

**Notes for the next session / recommended, not taken:** (1) `open56_zone_volume_experiment.py`'s
`run_ep()` should get `cwd=outdir` added directly, and any future local batch-EnergyPlus script
that imports it should add a cross-building contamination control — this task's discovery is not
scoped to OPEN-35. (2) The climate-zone-correlated sign split (§8 of the write-up) is a lead worth
a wider check (more cells, more of the same two archetypes) if OPEN-35 or a related item is
revisited — not run here, 3 cells is too few to separate climate from archetype/magnitude.
(3) OPEN-35's own "which fallback is intended" DESIGN question is unchanged by this task; this
measures consequence, not intent, per the item's own standing scope.

---

#### T05 — OPEN-38: measure the five unmeasured `LAUNDRYROOMFLR1` fatals — completed 2026-08-19

**Pre-registered prediction (before any build/sim ran):** all 5 unmeasured buildings, rebuilt in
`layout_assign` mode from `open48_refleet`'s frozen `01_buildings.gpkg` (dated 2026-08-12, 2 days after
the 2026-08-10 harvest — chosen over the older, already-tried-and-failed `phaseE` fixture, decided
before running, not after seeing a result), would classify `SmallHotel` and reproduce
`CalcHeatBalanceInsideSurf` in zone `LAUNDRYROOMFLR1`, Sizing phase, immediate two-space `**  Fatal  **`
— not necessarily the same temperature. **Both predictions held, 6/6** (5 unmeasured + 1 positive
control).

**Artifacts:**
- `scripts/analysis/open38_five_fatals_rebuild_2026-08-19.py` — real pipeline, unmodified
  (`BuildingClassifier().classify()` → `assign_climate_zones()` → `enrich_semantics()` →
  `run_step3(resolution_mode="layout_assign")` → EnergyPlus via `openubem.simulation.runner`'s own
  `-w -d -x -r` command), max 4 concurrent.
- `scripts/analysis/open38_five_fatals_subsurface_check_2026-08-19.py` — reuses OPEN-07's own
  `test_subsurface_fit`/`run_subsurface_census`, no new geometry code.
- `openubem/outputs/comparisons/open38_five_fatals_rebuild.csv`
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_five-fatals-rebuild.md` — full write-up.
- Rebuilt IDFs + EnergyPlus outputs: `scratchpad/open38-t05-rebuild/<cell>/` (9 buildings: 6 fatal +
  3 healthy negative controls).

**Blocker status: stale, confirmed by test, not by assertion.** The E02 IDF corpus is genuinely gone
(re-checked: `ubem_e02_harvest`'s 7 target directories carry `.eio`/`.end`/`.err`/`.sql` but no `.idf`,
for all 7) — but a fresh `layout_assign` IDF can be built locally for any of the 5, and was.

**Result, all 5 + positive control:** `la_centre/way/427942886`, `la_urban/relation/6374725`,
`la_urban/way/401910463`, `la_urban/way/428846131`, `nyc_rural/way/965718400` all rebuild as
`SmallHotel` and fatal identically — `CalcHeatBalanceInsideSurf`, zone `LAUNDRYROOMFLR1`, 0 Severe in
Warmup / 1 in Sizing, immediate fatal, genuine two-space `**  Fatal  **` (grepped directly, hard rule
3). `la_urban/way/401910463`'s rebuilt surface name (`P_LAUNDRYROOMFLR1_10010_0_10008`) is
byte-identical to the register's 2026-08-06 director-verified citation for that building. Raw
temperatures are not bit-identical to the original harvest and one (`way/965718400`) even flips sign —
expected and not read as non-reproduction, given the originally recorded 7 already span 5 orders of
magnitude (−59,865 to +182,399 °C), i.e. extreme input-sensitivity is this failure's established
character, not new here. Every dimension T04 used to define "the same signature" (check, zone, phase,
severity count, marker form) matched on 6/6.

**Positive control (hard rule 9): PASSED.** `nyc_rural/way/965718402` rebuilt independently here
reproduces the identical mechanism. The other 5 results stand.

**Negative control:** one healthy `layout_assign` sibling per cell (`la_centre/relation/6333145`,
`la_urban/relation/6356887`, `nyc_rural/way/1103897842`, each confirmed 0-Severe in the original E02
harvest before rebuilding) all completed cleanly under current HEAD. Disclosed caveat: none classify as
`SmallHotel` today, so this control is matched on cell+mode, not archetype — the register's own
separate, already-existing finding (34 of 41 `SmallHotel`-substituted `layout_assign` buildings
succeed) remains the stronger archetype-matched control and was not re-derived here.

**Mode, named explicitly (binding context item 2):** all 6 rebuilds and the 3 negative controls ran
under `resolution_mode="layout_assign"` explicitly — the same mode the original population was raised
and scanned under. No mode mismatch of the T08 (E-LA-15/18/19) kind applies to this task.

**New finding, beyond what T05 asked for:** with real IDF geometry now on disk for the first time,
T04's second open question — do unfitted subsurfaces occur below the CHKSBS warning threshold, on the
dying zone specifically — is answered directly rather than left "not determinable." All 6 rebuilt
fatal IDFs: 106/106 subsurfaces fitted (identical to the healthy `SmallHotel_90.1-2013.idf` control
gate), all 3 of `LAUNDRYROOMFLR1`'s own subsurfaces fitted on every building
(`max_plane_dist=0.0000`), and each `.err` carries exactly 3 CHKSBS warnings — matching T04's original
census count exactly — consistent with T04's finding that those warnings sit on other zones
(`RearStairs`/`Corridor`/`FrontStairs`), never on `LaundryRoomFlr1`. **Unfitted subsurfaces are
confirmed, on real geometry, not the mechanism.**

**Hard rule 7 (empty-directory check):** all 9 run directories checked after simulation; none empty.

**Test status:** positive control passed (§ above). Empty-directory check passed (0/9). Mode named
explicitly. Two-space fatal grepped directly on all 6, not inferred from the tolerant regex alone.

**Deviations from the plan:** the `phaseE` fixture the plan's Dependency Decisions section does not
pin for this task was tried implicitly via precedent (the 2026-08-18 scratchpad script that already
used it) and found not to reproduce; this task used `open48_refleet` instead, decided and stated as a
prediction before running (§0 of the write-up), not chosen post hoc after a fixture failed here. No
production code touched. No merge of OPEN-38 into OPEN-42 taken or recommended — nothing measured here
bears on that ruling.

**Notes:** OPEN-38's own first open question — *why* `LaundryRoomFlr1` runs away when substituted —
remains open; this task did not open the prototype's constructions/schedules/HVAC sizing to look for
a driving cause, only established the failure is real, reproducible, mode-consistent, and not a
subsurface-fit artifact. CP-3 (T04+T05+T06+T07) is not signed by this entry alone — only T05 is
complete in this dispatch; stopping here per dispatch instruction to report before continuing.

---

#### T02 — OPEN-55: the falsifiable acceptance test on `nyc_suburban` — INCOMPLETE, stopped and reported 2026-08-19

**Pre-registered prediction (unrevised, restated before scoring):** `nyc_suburban` — 1,589 buildings,
290 Unknown, 71 divergences today — returns **zero** divergences after T01's screen, no other change.

**Result: the prediction is NEITHER confirmed NOR falsified. Zero buildings were simulated under T01's
code. This is a stopped, incomplete run, not a zero-divergence result.**

**Frozen-input verification (done first, per plan step 1):** `%LOCALAPPDATA%/Temp/ubem_validation/
open48_refleet3/nyc_suburban/01_buildings.gpkg` MD5 `1198ed01bfd3b4463e50da0ae39d8e27`, byte-identical
to `open48_refleet/nyc_suburban/01_buildings.gpkg` (run 2's original). Confirmed loaded from cache, not
re-fetched: both attempts' logs show `Step 1: loading cached GDF from ...01_buildings.gpkg` followed by
`Fetched: 1589 buildings`, with no OSM-fetch line — matching `v12_cell_pipeline.py:185-189`'s
cache-hit branch exactly.

**What actually ran — two attempts, both crashed before any EnergyPlus simulation occurred under T01's
code.**

*Attempt 1 (pid 14032, launched ~08:34, dead by 08:38 — the coordinator's own observation that
triggered this investigation).* Completed step 1 (cache load, 1589 buildings), step 2 (classify: 290
Unknown, archetype distribution `MidriseApartment 979 / SmallOffice 316 / OpenUBEMUnknown 290 /
Courthouse 2 / QuickServiceRestaurant 1 / MediumOffice 1`; semantic enrichment), step 3 (**1589/1589
IDFs generated in 239.6 s**), and the LIVE_SMOKE gates (generation 100.0% >=95% PASS; Unknown 18.3%
<20% PASS). It then crashed inside `run_cell` at `v12_cell_pipeline.py:1082`
(`_remote_results_complete`), which calls `_ssh` (`:1014`) to probe the remote fleet dir for reusable
results before shipping. `_ssh` raised `RemoteCommandError`: remote command exited 1, remote
stderr **"Unmatched '."** — a tcsh quote-parse fault, occurring before any reship/resubmit. **Zero new
simulation touched the cluster in this attempt.** The 1589 `out/<osm_id>` directories that exist under
`/speed-scratch/o_iseri/fleets/open48_refleet3_nyc_suburban/out/` are 100% stale: verified by listing,
every one carries mtime **2026-08-18 18:08**, i.e. they are the untouched output of the *original*
(pre-T01) run-3 attempt that produced the pre-registered "71 divergences today" baseline
(`nyc_suburban.log:626-628` shows that original attempt's own identical probe call succeeding cleanly
— `remote completeness probe: 0/1589 complete`, then `Shipping fleet` — against the same 1589-entry
osm_id list, measured at 23,171 characters, well under Windows' 32,767-char `CreateProcess` limit).
Since the identical call on the identical input succeeded once already, this reads as a **transient
SSH/remote-shell fault**, not a static length bug — reported as a finding, not fixed (T02 does not
touch code).

**Process deviation, disclosed:** the retry launcher (below) reopens the shared log path in `w` mode,
which truncated attempt 1's on-disk log before a standalone copy was saved. The traceback and error
text quoted above were transcribed verbatim from this session's own tool output, captured before the
truncation happened, not read back from a preserved file. Recorded here as an error in this task's own
process, per the plan's discipline of reporting deviations honestly.

*Attempt 2 (pid 47676, launched ~08:41 as a deliberate, single retry — watched live rather than left
unattended, per the standing retry-loop rule).* Step 1 and step 2 repeated identically (1589 fetched
from cache, 290 Unknown, no re-fetch). Step 3 (local IDF generation) began, progressed normally through
the Unknown-archetype block, then **the log stopped growing and the process disappeared from the
process list with no Python traceback, no error line, and no exit message of any kind** — a materially
different failure signature from attempt 1 (a clean, catchable exception) and one that occurred
**entirely locally**, before step 4 and before any SSH call. At the time, one `energyplus.exe` process
(~1.27 GB RSS) was running locally on this shared 20-core machine — plausibly one of T04's or T05's
concurrent local runs per hard rule 4 — but resource contention as the cause is **not confirmed**, only
plausible; no OS-level crash dump or Windows Event Log was checked.

**Two distinct, unexplained failures on two consecutive attempts is a stop point, not a third blind
retry** — per the plan's own rule ("a task that cannot complete stops and reports; it does not
substitute a different measurement") and the standing cluster rule against leaving retry loops
unattended without diagnosing the actual error text. No third attempt was made.

**What is known, computed locally without touching the cluster or EnergyPlus** (pure semantic-layer
output of T01's code on the frozen input; deterministic and cell/attempt-independent per OPEN-49's
per-building seed, so bit-identical to whatever either crashed attempt held in memory — re-derived
directly via `step1_fetch` + `step2_classify_enrich`, no pipeline modification):
- 1589 buildings fetched (cache), 290 classified `OpenUBEMUnknown` — both exactly match the
  pre-registered baseline counts.
- **Control 1 (T02's own non-vacuity control) — PASSED:** all 290 Unknown rows' drawn
  `equipment_w_m2` fall inside `[2.58, 16.15]`. Actual draws: min 2.590, median 9.153, max
  16.067. Zero of 290 exceed the ceiling.
- `occupant_m2_per_person`: min 4.744, median 31.070, max 51.050 (inside the screened `[4.65,
  51.10]`).
- `lighting_w_m2`: min 3.454, median 10.869, max 18.246 (inside the screened `[3.44, 18.30]`).

**Direct answers to the coordinator's questions:**
- **(a) crashed** — twice, in two different ways (attempt 1: clean exception from an SSH probe;
  attempt 2: silent process death during local IDF generation, no traceback). Neither is (b) a
  preflight/zero-fail gate, (c) genuine completion, or (d) writing nothing at all — both attempts did
  real, verifiable local work (step 1-3) before dying.
- **Buildings that actually simulated under T01's code: 0.** Buildings that generated valid IDFs under
  T01's code: 1589/1589 (attempt 1 only; attempt 2 did not finish step 3, exact count where it stopped
  not instrumented since generation logging is per-manifest-write, not per-building).
- **Empty output directories: not applicable to this run** — no shipping occurred in either attempt, so
  no new remote output directories exist from T01's code. The 1589 remote directories on disk predate
  T01 entirely (mtime 2026-08-18) and must not be scored as either passes or failures of this attempt.
- **Divergence count before: 71** (unchanged, confirmed on disk — original run-3 `nyc_suburban.log`:
  `ZERO-FAIL: 71 failures exceed tolerance 16. STOP.`, all 71 are `CalcHeatBalanceInsideSurf`/
  `Temperature (high) out of bounds` severes escalating to `EnergyPlus Terminated--Fatal Error
  Detected`, sampled and confirmed on `way/813470190`). **Divergence count after: not computable —
  no simulation ran.** The prediction (71 -> 0) remains untested.
- **Thermal runaway status under T01's code: unknown** — no new simulation ran to check.

**Test status:** Control 1 (non-vacuity) passed on the locally re-derived draws. Control 2
(classified-buildings-unchanged) and the primary (divergence count) are **not evaluable** — no
simulation ran. EUI movement: not evaluable, same reason.

**Recommended, not taken:** (1) retry once more in a quieter window, ideally after confirming T04/T05
have released their local EnergyPlus load, with a persistent watch on the process's own exit code
(the current detached-launcher pattern discards it) so a third silent death is distinguishable from a
hang; (2) flag `_remote_results_complete`'s single giant `_ssh` probe line as fragile against the tcsh
login shell — it is unrelated to T01 and this plan does not touch code, but it is now a reproduced,
if transient, fault worth a register entry if it recurs.

**Deviations from the plan:** two, both disclosed above (log truncation by the retry launcher; no
OS-level crash diagnostics gathered for attempt 2's silent death). T01's code was not modified,
inspected for a fix, or worked around. No git write command run. No fleet or multi-cell run attempted.
CP-1 (T01) is unaffected; **CP-2 cannot be signed on this entry** — T02's half of CP-2 is incomplete.

---

#### T10 — Execute ruling R3: preserve the cited evidence, then restate OPEN-53 — completed 2026-08-19

**Step 1 (load-bearing), done first:** both source trees re-verified present on disk —
`%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/` (all 12 cells) and `.../open48_refleet/` (run 2,
all 12 cells). **Neither tree is gone.** The stop-and-report branch does not apply.

**Artifacts:**
- `docs/validations/overAll/evidence/open48_runs/` — 323 files, 12,565,016 bytes (11.98 MB, 0.0126 GB),
  in five groups (`run2_refleet`, `run3_refleet3`, `open07_ab_sim`, `open38_t05_rebuild`,
  `open56_ab_arms`) — a named adaptation of the plan's `<run>/<cell>/<building>/` shape, since the
  actual evidence gap spans two `%LOCALAPPDATA%` fleet reruns plus two gitignored `scratchpad/`
  investigations plus one separate `%TEMP%` A/B-arm directory, not just run 2 / run 3.
- `docs/validations/overAll/evidence/open48_runs/MANIFEST.md` — per-file source path, MD5 (re-verified
  on the copy, not carried from source), byte size, copy date, citing open item(s).
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_evidence-preservation_2026-08-19.md` — full
  write-up, including the proposed OPEN-53 register restatement (not inserted — see deviation below).

**Before copying, found already durable (not duplicated):** `docs/validations/overAll/results/
open48_refleet/` (tracked in git, 122 files, backs OPEN-35/OPEN-12) and `.../open48_refleet3/` (5
finished cells, present on disk) both already hold the per-cell `05_results.csv`/manifests; and
`openubem/outputs/comparisons/open56_fleet_cost_stratified.csv` already holds the OPEN-56 aggregate
result vector. The actual gap copied was narrower than the plan's 0.12 GB estimate assumed: the six
OPEN-42/OPEN-11 buildings' IDF + `.err`/`.end` (run 2 whole, run 3's five surviving), two of OPEN-07's
three buildings' A/B IDF + real simulated `.err`/`.end`, OPEN-07's third building (`way/401910463`, no
original survives anywhere — T05's this-plan rebuild reproduces its register-cited fatal and was copied
as the gap-fill, also serving OPEN-38), and the OPEN-56/OPEN-09/OPEN-11 70-building A/B arms' raw
`.err`/`.end` (140 arm-sides). **Zero `.sql` files anywhere in the copy** (hard constraint 3).

**Controls:**
- **MD5 re-verify: 323/323, two independent passes** — once at copy time (source vs. freshly-hashed
  destination), once fully independently after `MANIFEST.md` was written (re-parsing the manifest text
  itself and re-hashing every destination file from disk against it). 0 deleted for mismatch.
- **Size cap: 12,565,016 bytes = 0.0126 GB against the 0.15 GB cap (8.4 %).**

**Findings surfaced while copying (reported, not smoothed over):** the OPEN-42 six's severe-error
counts do not agree exactly across the adopted `phaseE_elevrb` run / run 2 / run 3 (three of six match
run 2, a different subset matches run 3, none matches all six) — all three agree the six fatal, none
reproduces the others byte-for-byte, expected across evolving code and different runs.
`way/965718403`'s A-side (`SmallHotel`) simulation has a substantial `.err` but no `eplusout.end` — the
run did not reach a terminal state; preserved as-is, not represented as a pass or a fail. `la_urban/
way_402215469` (OPEN-42's sixth building) has zero run-3 footprint, consistent with T03's independent
finding that `la_urban`/`nyc_centre` have no run-3 simulation output at all.

**Deviation from the plan (per dispatch instruction, disclosed):** the register
(`INVESTIGATION_open-items-register.md`) was **not edited** — another executor owns it concurrently.
The OPEN-53 restatement (plan step 7) was instead written in full as a finished, ready-to-insert block
under `## Proposed OPEN-53 restatement (NOT yet inserted into the register)` in this task's own
measurement doc, for the director to insert. No other deviation. No git write command run.

**Residual, stated honestly:** this discharges OPEN-53's closure condition **only for the 323 files
named and copied** — not for the other ~8,150 buildings' run-2/run-3 output (fleet aggregates durable,
raw per-building output not, and not cited by name by any open item), not for the remaining 8 of 9
buildings in `scratchpad/open38-t05-rebuild/`, not for the ~110 MB balance of
`scratchpad/e-la-20-investigation/`, and not for the ~5 GB non-`.err`/`.end` remainder of
`%TEMP%/open56_fleet_cost/`. **OPEN-53 stays open** — the standing custody risk (an external process
can empty these volatile paths without the project's knowledge) is unchanged by this task. Full
reasoning and the exact restatement text: `extra/MEASUREMENT_open-53_evidence-preservation_2026-08-19.md`
§7–8.

**Test status:** both mandatory controls passed (323/323 MD5 re-verify; size under cap). No production
code touched. No cluster/EnergyPlus/compute run.

---

#### T09 — Execute ruling R2: close and retire OPEN-42, OPEN-11, OPEN-07, OPEN-08 — completed 2026-08-19

**Pre-registered prediction (before running the recount script):** 21 live / 35 struck / 56 total,
OPEN-01…OPEN-56, no row missing, none duplicated, next free `OPEN-57`; invariant *struck rows −
retired IDs = 2* (OPEN-02, OPEN-28) holds, so 35 − 2 = **33 retired IDs**. **The prediction held
exactly — no discrepancy anywhere in this task.**

**Recount script, literal stdout, run after all edits:**
```
Table body: lines 684-742 (1-indexed), 56 row-lines
Total OPEN-NN rows found: 56
Live (non-struck) rows: 21
Struck rows: 35
ID range: OPEN-01 .. OPEN-56
Missing IDs in sequence: none
Duplicate IDs: none
Next free item ID: OPEN-57

Struck IDs: OPEN-01, OPEN-02, OPEN-04, OPEN-05, OPEN-06, OPEN-07, OPEN-08, OPEN-11, OPEN-21, OPEN-22,
OPEN-23, OPEN-24, OPEN-25, OPEN-26, OPEN-28, OPEN-30, OPEN-31, OPEN-32, OPEN-33, OPEN-34, OPEN-36,
OPEN-37, OPEN-39, OPEN-40, OPEN-41, OPEN-42, OPEN-43, OPEN-44, OPEN-45, OPEN-46, OPEN-48, OPEN-51,
OPEN-52, OPEN-54, OPEN-50
```
(This is a straight re-run of `scripts/analysis/open_register_recount_2026-08-18.py`, unmodified —
no new script was written for this task.)

**Also re-run before any edit, as a baseline control:** the same script against HEAD-before-this-task
gave **25 live / 31 struck / 56 total**, next free `OPEN-57` — matching the header this task inherited,
confirming the starting point before editing.

**What was done, per the plan's "strike in the same edit" rule (2026-08-10's missing-row failure is
not repeated):**
1. **§1 table** — all four rows struck in the same edit that added their closure prose (`~~OPEN-NN~~`
   ID cells, closure note replacing the row's evidence/status cell): OPEN-07 (line ~692), OPEN-08
   (~693), OPEN-11 (~696), OPEN-42 (~723-728, two edits — the row opens with the closure marker and
   closes with the full "what OPEN-56 explains / does not explain" note).
2. **Four closure records**, one per item, each in the item's own §-section (not a shared block):
   OPEN-07 (header + closure block at its section's original top, since the section's actual
   "succeed at HEAD" finding lives in a 2026-08-18-late amendment appended elsewhere in the register
   under a different item's heading — a pre-existing misplacement, not touched, cited instead),
   OPEN-08 (header + closure block at its section's top), OPEN-42 (header + closure block appended at
   the end of its section, immediately before `### OPEN-43`), OPEN-11 (header + closure block appended
   at the end of its section, immediately before `### OPEN-46`).
3. **One short back-reference added inside OPEN-56's own section** (its header line), pointing to the
   two folded items and stating OPEN-56 itself is unchanged by the fold — no new claim written there,
   per the plan's limit.
4. **Header prose** (§1 first line): new dated entry prepended, struck the previous "25 tracked items"
   bold marker, stated the four closures, the recount output, the reconciliation arithmetic
   (35 − 2 = 33), and that none of the four depends on T01.
5. **The "Nothing closed... left to the user" paragraph** immediately above §1 (dated 2026-08-19, T03
   of this same plan) was amended with a short follow-up sentence recording that T09 took all four,
   rather than leaving it to silently read stale.

**No-debt-lost check, per closure (the plan's requirement (b), verified present in each record):**
- **OPEN-42** — states what OPEN-56 explains (Warehouse fatal-rate concentration via large-volume
  substitution error; face (ii)'s placeholder as a symptom of failure, not a separate cause) *and*
  four explicit things OPEN-56 does **not** explain: the intervention was only re-run on the 6
  face-(ii) buildings, not the other fatal Warehouses without a placeholder; the remedy is not
  authorised/implemented; the published 157.1/158.0 fleet EUI claim is explicitly not touched (0.00%
  impact, unchanged from the 2026-08-12 measurement); OPEN-56's separate ÷4.18 denominator finding
  (T03, this plan) is a different building and does not affect this closure.
- **OPEN-11** — records the "inverted geometry" label tested-and-not-corroborated (universal to all
  8,160 `auto` runs) and that the per-building remediation decision (`10_fails_solution.md`) is
  absorbed by OPEN-56's own fleet-wide closure condition, not dropped; explicitly no remedy applied.
- **OPEN-07** — carries forward the `SmallHotel`-not-`SmallOffice` provenance fact and the
  `layout_assign`-vs-certified-path caveat (closes on the certified path succeeding, not proof the
  mode where the regression was seen is fixed).
- **OPEN-08** — carries forward the "E02 is gone is too strong" correction (parquet manifests
  survived; only `.sql`/`.idf` were swept) and explicitly does not close or touch the separate,
  still-13.40%, T08-vs-T20 archetype comparison — named as context, not reopened under a new ID.

**T01/OPEN-55 disclosure, present in all four closure records and in the header:** T01 (this same
plan) changed shipped code (`openubem/semantic/__init__.py`, the OPEN-55 B+ donor screen). **OPEN-55
stays open** — T02, its own acceptance test, crashed twice and did not run, so the screen is
implemented and unit-tested but unproven in simulation. **No closure in this task depends on T01.**

**E-LA-17 disclosure:** T08's recommendation (strike E-LA-17 from OPEN-29's tracked list as a merge
into OPEN-09) is recorded in T08's own entry and in the register's OPEN-29 adjudication table, but is
**not executed** and is **not** one of R2's four closures. Not touched by this task.

**UTF-8 discipline:** every edit made with the Edit tool (no `perl -i -pe` / `sed -i` with literal
emoji). `grep -c "ð\|â€\|Ã"` over the full register file after all edits: **0**.

**Boundaries respected:** OPEN-53's section (`### OPEN-53` at line 6409-post-edit) and OPEN-55's
section (`### OPEN-55` at line 6726-post-edit) were read but not edited — confirmed by grep showing
both headers unchanged from their pre-task text, and both absent from the recount's struck-ID list.
No git write command run.

**Test status:** recount script re-run, output quoted verbatim above, matches the pre-registered
prediction exactly. Reconciliation invariant (struck − retired = 2) holds. All four closure records
verified present with a "what survives" statement, read back after writing. No number was massaged to
hit the prediction — the prediction held on its own.

**Deviations from the plan:** none. The plan's "strike in the same edit" discipline, the header/prose
update, the retired-ID naming (this pass's four, not a full 33-ID re-enumeration — matching this
document's own established convention since the 2026-08-17 correction, where only the delta is named
per pass and the full list is not re-typed), and the programmatic recount were all followed as
specified.

**Notes:** while reading the register for this task, two pre-existing misplacements were noticed and
left untouched, since fixing them is not part of R2's scope: a 2026-08-18-late OPEN-07 finding
("all three buildings succeed at HEAD") is physically located inside OPEN-36's §-section rather than
OPEN-07's own, and a 2026-08-18-night OPEN-09 finding (fleet error taxonomy) is physically located at
the tail of OPEN-11's §-section rather than OPEN-09's own. Both are cited correctly by evidence path
in this task's closure records regardless of their physical location; neither was moved, since moving
prose was not asked for and risks losing surrounding context. Flagged here for a future register-
hygiene pass, not acted on.

---

#### T02 (attempt 3) — OPEN-55: the falsifiable acceptance test on `nyc_suburban` — completed 2026-08-19

**Instrumented per this dispatch's hard requirements — new launcher
`scripts/validation/open48_t02_attempt3.py`, harness-only, `openubem/` untouched: log opened append-only,
child exit code captured to a dedicated `EXITCODE` file the instant the child exited, stdout+stderr both
redirected unbuffered to the log, and a 60s-cadence heartbeat log so a silent death would have been
bounded in time. It was not needed — this attempt's failure produced a clean traceback and a captured
exit code, unlike attempt 2's silent death.**

**Fresh remote run tag used, per hard requirement 2:** `output_subdir='open48_refleet3_t02a3'`
→ remote fleet dir `/speed-scratch/o_iseri/fleets/open48_refleet3_t02a3_nyc_suburban`, confirmed
**absent** on the cluster both before launch and after the crash. The 1,589 stale
`open48_refleet3_nyc_suburban/out/*` directories at mtime 2026-08-18 18:08 were never touched and
could not be scored as this run's output.

**Buildings simulated under T01's code: 0.** The prediction (71 divergences → 0) remains neither
confirmed nor falsified.

**What happened:** frozen-input MD5 re-verified (`1198ed01bfd3b4463e50da0ae39d8e27`, matching attempts
1/2), seeded by copy into the fresh work dir, copy's MD5 re-verified. Step 1 confirmed cache load, no
OSM fetch. Step 2: 1,589 fetched, 290 Unknown, archetype distribution identical to the pre-registered
baseline. Step 3: **1,589/1,589 IDFs generated in 199.6 s**. LIVE_SMOKE gates both PASS (generation
100.0%, Unknown 18.3%). Then, on the **first SSH call this run made**, to the brand-new never-shipped
remote fleet dir, `_remote_results_complete`'s `_ssh` probe (`v12_cell_pipeline.py:1082` → `:1014`)
raised `RemoteCommandError`: remote command exited 1, remote stderr **verbatim `"Unmatched '."`** —
captured exit code **1** (written to `EXITCODE` the instant the child died, elapsed 3.4 min).

**🔴 This is a SECOND, confirmed occurrence of the identical `Unmatched '.` tcsh fault seen in attempt
1**, at the identical code location, on a command built from the same 1,589-entry osm_id list, of
near-identical measured length (23,166 probe chars / 23,177 `bash -lc` wrapper / 23,213 full argv —
attempt 1 measured 23,171 on the same list against a different fleet-dir name), well under Windows'
~32,767-char `CreateProcess` limit. **Per this dispatch's hard requirement 4, no fourth attempt was
made.** No workaround, no bare-command retry, no code fix or inspection of `_ssh` beyond reading it to
locate the fault — out of this task's scope. Full verbatim text, exact lengths, and the run timeline:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-55_acceptance-test-attempt3.md`.

**Control 1 (non-vacuity) — PASSED, re-derived from this attempt's own artifacts** (not carried
forward from attempt 1): re-ran `step1_fetch` + `step2_classify_enrich`, unmodified, directly against
this run's own seeded GDF copy. 290 Unknown rows' `equipment_w_m2`: min 2.590187, median 9.152907,
max 16.066840 — 0/290 exceed the [2.58, 16.15] ceiling. `occupant_m2_per_person` and `lighting_w_m2`
also fall inside their screened ranges. Bit-identical to attempt 1's numbers, as expected under
OPEN-49's per-building determinism — evidence the screen's effect is stable, not evidence of reuse.

**Control 2, primary divergence count, EUI movement: NOT EVALUABLE** — zero buildings simulated. Divergence
count before T01 remains 71 (established on 2026-08-19, not re-verified again here). **No fleet figure
restated.**

**Test status:** Control 1 passed. Control 2, primary, and EUI-movement secondary are all not
evaluable — no simulation ran. Instrumentation itself worked exactly as designed: exit code captured,
log never truncated, heartbeat log corroborates a clean 3.4-minute run with no unexplained gap.

**Deviations from the plan:** none from the plan's own steps (frozen-input re-verify, ≤4 concurrent
local work — this attempt used 1, cell restricted to `nyc_suburban` only). One deviation from the
dispatch's default flow, explicitly authorized by the dispatch's own hard requirement 4: stopped after
one attempt this session instead of retrying, because the failure was a second occurrence of a named,
specific fault rather than a new failure mode. No production code touched (`openubem/semantic/__init__.py`
left exactly as T01 left it). No git write command run. Cluster job `1274884` (`4J_s4_le`, this
project's own user, presumably concurrent with another task in this pass) was left untouched; job
`1266911`/`4J_s4_pe` was not present in this account's `squeue` output and was not touched.

**Notes:** **OPEN-55 stays open. CP-2 still cannot be signed on T02's half** — three attempts across
two dispatches have now reached local completion (IDF generation + LIVE_SMOKE PASS) three times
without a single building ever reaching EnergyPlus, twice for the same named reason. The existing
INCOMPLETE entry above (attempts 1–2) is left unedited, standing as the record of those two attempts;
this entry adds a third, independently instrumented data point that narrows the failure to a specific,
reproducible, transient SSH/tcsh fault in one specific probe call — not a code-length bug, not a T01
regression, not a resource-contention artifact (this attempt's local machine was otherwise idle: 0
EnergyPlus processes before launch, 1 concurrent local worker used against a 4-concurrent ceiling).
Recommended, not taken: a register entry for the `_ssh`/`_remote_results_complete` transient fault
itself, since it has now blocked this specific acceptance test twice.
