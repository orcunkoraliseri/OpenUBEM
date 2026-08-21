# PLAN — Twenty tasks across the nineteen live register items

> **Slug:** `twenty-items-2026-08-19` · **Date:** 2026-08-19 (late) · **Author:** manager/director session
> **Register:** `../INVESTIGATION_open-items-register.md` — 19 live / 40 struck / 59 total, next free `OPEN-60`
> **Predecessor:** `previous/PLAN_close-all-2026-08-19.md` (CP-2 signed 2026-08-19; fleet baseline restated to `153.8231 kWh/m²`)
> **Board:** `../reporting/board_published-numbers.html` → artifact `0615b50a-75d6-49c6-a354-d4f2f74d3639`

---

## 1. What this pass is, and what the user authorised

The user authorised this pass in one instruction, given on going to sleep: *"choisir 20 taches
ouverts et creer d'un plan implemenation et continuer executer"* — pick 20 open tasks, write an
implementation plan, and keep executing. The same message ordered the completed plan docs archived
into `implemenation/previous/`, which is done (30 docs moved, 243 citations swept and repaired, 0
unresolved).

**Every one of the 19 live items already has a first measurement.** A batch can therefore no longer
be *"items nobody has measured"*. The selection rule is the one the arc adopted on 2026-08-19:
**select on the next unanswered question, not on the item.** Each task below names a question that
is (a) written into the register as the item's own next step, or (b) newly opened by the run-4
restatement, and that is (c) answerable **without the cluster and without a user ruling**.

**Coverage.** All 19 live items are touched: OPEN-03, 09, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20,
27, 35, 38, 53, 56, 58, 59.

### 1.1 What this pass may NOT do

- **No fix, no remedy, no code change under `openubem/`.** Every task here measures. Where a task
  finds a remedy obvious, it writes the remedy down and stops. *(Arc rule: diagnose before
  remediate — a measurement task that also fixes is a task whose measurement cannot be trusted.)*
- **No cluster.** All twenty run on the local machine against artifacts already on disk. Nothing is
  submitted, nothing is `ssh`-ed, no login-node compute. If a task believes it needs the cluster,
  it stops and reports instead.
- **No item may be opened, closed, struck or retired.** That is the director's call at a
  checkpoint, and retiring an ID is the user's. Tasks *recommend*; they never act.
- **No fleet EUI figure is restated.** `153.8231 kWh/m²` pooled over 8,153 buildings is the adopted
  baseline as of CP-2 and stands until a checkpoint says otherwise.

## 2. Director actions taken BEFORE dispatch

1. Register recounted programmatically (`scripts/analysis/open_register_recount_2026-08-18.py`):
   **19 live, 40 struck, 59 total, OPEN-01…OPEN-59, none missing, none duplicated, next free
   `OPEN-60`.** Invariant *struck − retired = 2* (OPEN-02, OPEN-28) holds.
2. Every live item's §1 row read and its stated next step extracted; the twenty tasks below are
   built from those, not invented.
3. Run-4 artifact tree confirmed present on disk, all twelve cells with a non-empty
   `results/05_results.csv` (8,153 successes, 7 failures).
4. `implemenation/` archived to `implemenation/previous/` with the citation sweep the archiving rule
   obliges (CLAUDE.md; OPEN-33): **243 citations repaired across 73 files, 0 unresolved**, verified
   by resolving every cited path against disk.

## 3. Hard rules for the executor

1. **Execute the plan. Do not propose alternatives.** If a task's premise is false at HEAD, **stop
   and quote the conflict** — a falsified premise is a finding and must be reported as one, not
   worked around. (Several items on this register were opened on premises that later proved false;
   that is why this rule is first.)
2. **NEVER run compute on the login node** and **never submit to the cluster in this pass.** No
   `ssh`, no `srun`, no `sbatch`. If you conclude a question needs the cluster, write that
   conclusion down and move to the next task.
3. **Never touch another project's cluster runs.**
4. **Never edit** root `main.py`, any OVERVIEW doc, or any DESIGN doc. OPEN-27 concerns a DESIGN
   defect: you write an **erratum document**, you do not edit the DESIGN.
5. **No `.py` files under `docs/`, ever.** Analysis scripts go in `scripts/analysis/`; their outputs
   go to `openubem/outputs/comparisons/`; figures go to `openubem/outputs/` **flat**.
6. **Never run a git write command.** No `git add`, `commit`, `push`, `mv`, `checkout`, `reset`,
   `stash`. Git is handled outside this session. Read-only git (`log`, `show`, `diff`, `blame`,
   `rev-list`) is expected and encouraged — three tasks depend on it.
7. **Report the actual error text**, never a label. "It failed" and "connection refused" are not
   findings; the stderr and the exit code are.
8. **Append one progress-log entry per completed task** to §8 of this document, in the required
   shape: `#### TXX — <title> — completed YYYY-MM-DD` then **Artifacts / Deviations / Test status /
   Notes**. A task with no entry did not happen.
9. **Cite by `file:line`** for every claim about code. A claim about behaviour with no citation is
   an opinion.
10. **Do not delete or move anything** under `%LOCALAPPDATA%/Temp/`. T06 in particular is an
    inventory task and is forbidden from touching what it inventories.
11. **Where a number already exists in the register, re-derive it rather than quoting it**, and say
    so when it does not reproduce. Two items on this register are open precisely because a quoted
    number stopped reproducing.

## 4. File layout

| what | where |
|---|---|
| this plan | `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_twenty-items-2026-08-19.md` |
| findings docs | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_*.md` / `INVESTIGATION_*.md` |
| analysis scripts | `scripts/analysis/*.py` |
| tabular outputs | `openubem/outputs/comparisons/*.csv` |
| figures | `openubem/outputs/*.png` (**flat**) |
| register (director edits only) | `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` |

## 5. Pinned facts the tasks rest on

Re-derive these if a task depends on them; do not assume them.

| # | fact | source |
|---|---|---|
| F1 | Adopted fleet baseline **153.8231 kWh/m² pooled**, 8,153 successes, 24,320,582 m². Pooled = Σ(EUI × floor area) ÷ Σ(floor area) over `simulation_status == success`. | `extra/MEASUREMENT_fleet-restatement-2026-08-19.md` §1; OPEN-43's definition |
| F2 | Run-4 results: `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet4/<cell>/results/05_results.csv` — **note the `results/` subdirectory**. | run 4 |
| F3 | Baseline results: `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<cell>/05_results.csv` — **no `results/` subdirectory**. A script that assumes one silently reads nothing. | baseline tree |
| F4 | Twelve cells: `austin_{centre,rural,suburban,urban}`, `la_{centre,rural,suburban,urban}`, `nyc_{centre,rural,suburban,urban}`. 8,160 buildings. | run 4 |
| F5 | Run 4's Unknown population is **650 buildings, 3.7 % of fleet floor area**, pooled **107.22** against non-Unknown **155.55**. | restatement §3 |
| F6 | OPEN-56's cost is a **fixed per-building offset ≈ +1.0 kWh/m²**, not per-zone (corr 0.113). It is **not** inside 153.8231. | register OPEN-56; X01/X02 |
| F7 | `centroid_lat` in `05_results.csv` is **near zero for every building in every cell in both runs**. It is not a WGS84 latitude. Do not read a defect into it. | restatement §9(4) |
| F8 | `footprint_area_m2 == 200.0` is the **dropped-building placeholder** written at `scripts/validation/v12_cell_pipeline.py:659` and overwritten only on success at `:664`. It marks a failure; it is not a cause. | OPEN-42 closure note |
| F9 | Test-suite baseline is `.venv/Scripts/python.exe -m pytest -q tests/` → **1,919 passed / 55 skipped**. A bare root-level run reports ~36 false failures and is not the baseline. | project baseline |
| F10 | The run-4 artifact tree is in `%LOCALAPPDATA%/Temp/` and is **NOT durable** — a 2026-08-17 external sweep deleted a comparable corpus. Tasks that need it should read it early. | OPEN-53 |

---

## 6. Task list

Each task: **What / Why / How / How to test.** Twenty tasks, five groups, three checkpoints.

### Group A — loose ends the run-4 restatement itself created

#### T01 — OPEN-59 at fleet scale

- **What.** OPEN-59 says Unknown buildings run **1.7× classified** on total demand, with the gap
  moved from equipment into DHW, heating, lighting and cooling. It was measured on **one cell**
  (`nyc_suburban`), before run 4, and its §1 row records the fleet-wide share and fleet EUI effect as
  **"not yet measured, commissioned as part of T04"**. Measure it on all twelve run-4 cells.
- **Why.** Run 4 is the first fleet run carrying the OPEN-55 screen, so it is the first data on which
  this question is answerable. **A partial answer already exists and must be tested, not assumed:**
  pooled over floor area, run-4 Unknown is **107.22** against non-Unknown **155.55** — Unknown is now
  *below* classified, which is the opposite of the 1.7× the item records. Either the median-per-building
  statistic and the floor-area-pooled statistic disagree (in which case say which one the item should
  carry), or the screen changed the answer.
- **How.** Per cell and fleet-wide, over run-4 successes, split by `archetype_id == 'OpenUBEMUnknown'`:
  report **n**, floor-area share, pooled EUI, and **median per-building** total plus each end-use
  column (`heating`, `cooling`, `lighting`, `equipment`, `dhw`, `fans`, `pumps`). Reproduce
  OPEN-59's own `nyc_suburban` numbers as a control (it recorded total 349.4 vs 202.8, DHW 103.5 vs
  42.5, heating 140.1 vs 99.0, lighting 26.7 vs 4.0, cooling 25.0 vs 4.5). State explicitly whether
  each reproduces on run 4, and if not, by how much and in which direction.
- **How to test.** The control: your Unknown/classified counts for `nyc_suburban` must be **290 /
  1,299**. Your fleet Unknown count must be **650** and Unknown pooled must be **107.22 ± 0.01**.
  If any of the three disagrees, stop — your join is wrong, not the register.
- **Output.** `extra/MEASUREMENT_open-59_fleet-scale.md` + `openubem/outputs/comparisons/open59_unknown_gap_fleet.csv`.

#### T02 — OPEN-56: localise the writer

- **What.** OPEN-56's evidence mark is **"mechanism measured; writer not yet localised"**. Find the
  code that emits floors and ceilings wound such that EnergyPlus computes a negative zone volume.
- **Why.** The item cannot progress to a remedy ruling without knowing which of the two candidate
  remedies (write `Zone.Volume` explicitly vs fix the winding) is even available at a single site.
  That ruling is owed to the user and is blocked on this.
- **How.** Read `openubem/idf/surfaces.py` (the register already cites `:223-234,671-681` as a
  candidate) and the zone/surface emission path in `openubem/idf/builder.py`. Take **one** run-4 IDF
  known to carry the warning, extract the vertex order of one zone's floor and ceiling, and compute
  the signed area / normal direction yourself. State: which function writes those vertices, at which
  line, in which order, and whether the winding is inverted at emission or inherited from the
  footprint polygon upstream (`openubem/geometry/footprint.py`, `shapely.geometry.polygon.orient`).
- **How to test.** Your claim must predict, for a **second** IDF from a different cell, whether that
  building's zones carry the warning — check the prediction against its `eplusout.err`. A mechanism
  that explains one building and predicts nothing is not localised.
- **Output.** `extra/MEASUREMENT_open-56_writer-localisation.md`. **No fix.**

#### T03 — OPEN-58: measure the blast radius

- **What.** OPEN-58's size is recorded as **"unknown — every local batch result that imported
  `run_ep()`"**. Enumerate them.
- **Why.** Until the radius is known, every local batch number in this arc's history carries an
  unquantified doubt, and the item cannot close.
- **How.** Find every script that defines or imports `run_ep` (`scripts/`, and read-only git history
  for deleted ones: `git log --all --diff-filter=A --name-only`, `git grep -n run_ep $(git rev-list --all)`
  is acceptable but expensive — scope it). For each consumer, determine from the code whether it (a)
  shared a working directory across buildings under `-x`, and (b) used the non-production EUI formula.
  Then list, per consumer, which **published or cited** output files it produced and whether any
  finding in `extra/` or the register rests on them.
- **How to test.** T04 of `previous/PLAN_close-all-2026-08-19.md` voided its own first run and
  re-ran clean; its `_results_v2.csv` is recorded as unaffected. Your method must independently
  reach that same verdict for that file. If it does not, your method is wrong.
- **Output.** `extra/MEASUREMENT_open-58_blast-radius-enumeration.md` +
  `openubem/outputs/comparisons/open58_run_ep_consumers.csv`.

#### T04 — The OPEN-35 regression: is it one building or a population?

- **What.** Run 4 dropped `nyc_centre / way/266034056` — an OPEN-35 Scope-B building imputed 1 → 19
  storeys whose IDF then diverged (`CalcHeatBalanceInsideSurf`, 1.94e6 °C), survived neither the
  zero-area-surface strip nor the reroute to `one_zone_per_floor`, and was dropped. Three of its
  19-storey siblings needed repair before completing. **Establish whether the at-risk population is
  1 or larger.**
- **Why.** The director carried this to the user as needing an ID and a remedy ruling. The ruling
  is different if the fix endangers one building than if it endangers a class.
- **How.** Across all twelve run-4 cells: (a) count buildings that required **any** repair
  (`zero-area surfaces stripped`, `rerouted to`, `still failed after reroute`) by grepping the
  per-cell logs in `%LOCALAPPDATA%/Temp/open48_run4/*.log`, and cross-tabulate against the 20
  buildings whose `levels` changed; (b) for every building whose imputed `levels ≥ 10`, report
  whether it completed, needed repair, or dropped; (c) compare that repair rate against a
  matched control of buildings at similar storey counts whose `levels` did **not** change.
- **How to test.** Your repair census must recover exactly the buildings named in the run-4
  `nyc_centre` log line `Repaired and resimulated: [...]` — no more, no fewer.
- **Output.** `extra/MEASUREMENT_open-35_regression-population.md`. **Recommend an ID; do not open one.**

#### T05 — The EUI denominator census

- **What.** The old RESUME box named this **the single highest-yield unrun measurement**: on 1 of 60
  buildings (`nyc_centre/relation_3566904`) writing `Zone.Volume` also moved the reported **Total
  Building Area from 157,115 to 37,551 m² (÷4.18)**; the other 59 matched to within 0.1 %. **The
  project's EUI denominator is EnergyPlus's own simulated floor area**, so if that is not unique it
  reaches the denominator of every published number.
- **Why.** It is cheap, it is local, and it bears directly on F1.
- **How.** Fleet-wide over run-4 artifacts, compare each building's `.eio` simulated floor area
  against `footprint_area_m2 × levels` (multiplier-aware, as `openubem/results/parser.py` does).
  Report the distribution of the ratio, the count outside ±1 %, outside ±10 %, and outside 2×, and
  name every building outside 2× with its cell, archetype and zoning strategy.
- **How to test.** `auto` mode was measured at **99.63 % of buildings within 1 %** (OPEN-01's
  closure). Your distribution must reproduce that to within a few tenths of a percent, or your area
  extraction is wrong.
- **Output.** `extra/MEASUREMENT_eui-denominator-census.md` +
  `openubem/outputs/comparisons/eio_area_vs_derived_fleet.csv`.

### ⏸️ CP-1 — STOP AND REPORT (after T05)

Report T01–T05. **Do not continue past this point without the director's audit.** T01 and T05 can
each move how F1 must be read, and T04 can change a pending user ruling — those three are exactly
the class of result that must not be built on unaudited.

### Group B — custody and reproducibility

#### T06 — OPEN-53: what still exists, and what it would cost to preserve

- **What.** OPEN-53 is narrowed to a **custody risk**: 152.4 GB across three corpora, 145 GB of it
  `.sql`, none carried anywhere durable, and `e02_corpus_inventory.csv` (2026-08-11) is **falsified
  by disk for two rows** and must be read as a snapshot. Re-inventory against today's disk.
- **Why.** Seven live items rest on these artifacts, and a comparable corpus was deleted by an
  external process on 2026-08-17 without warning. Run 4's tree (F10) is now on the same footing.
- **How.** For each corpus (E02 harvest, `open48_refleet` run 2/3, `open48_refleet4`): count
  directories, count and total-size `.sql`, `.end`, `.err`, `.eio`, and the vector/CSV files. Then
  compute the **cited-evidence subset** — the files any finding in `extra/` or the register actually
  names — and its total size. Restate the earlier claim that the cited subset is *under 0.12 GB*:
  re-derive it, do not quote it.
- **How to test.** Your E02 counts must reproduce the recorded `.eio`/`.err` = **40,800** exactly, or
  explain the discrepancy as a disk change with a timestamp.
- **⚠️ Forbidden.** Do not move, copy, compress or delete anything. This task counts.
- **Output.** `extra/MEASUREMENT_open-53_custody-reinventory.md` +
  `openubem/outputs/comparisons/corpus_inventory_2026-08-19.csv`.

#### T07 — OPEN-14: the config gate that closes before the missing slices matter

- **What.** X09 established **zero `FUSED` provenance tokens across all 8,160 buildings**, including
  `nyc_centre` — the one cell that *has* a tracked Overture slice. So the missing slices are a real
  but **non-operative** blocker: the config gate closes first. **Localise that gate and state the
  minimal change that would open it.**
- **Why.** The item is stuck between two blockers and nobody has said which one to fix first. This
  answers that without fixing either.
- **How.** Trace the UTCI height-backfill path from its entry point to the point where `FUSED` would
  be written; find the config flag or branch that prevents it; cite `file:line`. Then state, in one
  paragraph, what would have to be true for a clean checkout to reproduce the backfill — the gate,
  the slice, or both, and in what order.
- **How to test.** Prove the gate is what closes by constructing the smallest possible local case
  where the gate is satisfied and showing whether a `FUSED` token then appears. If it cannot be
  constructed locally, say so explicitly and name what blocks it.
- **Output.** `extra/MEASUREMENT_open-14_config-gate.md`.

#### T08 — OPEN-12: re-derive the numbers that stopped reproducing

- **What.** OPEN-12's evidence mark is **⚠️ "numbers do not reproduce"**: the recorded rural
  `height_m` residuals (`nyc_rural` 36.4 %, `austin_rural` 19.2 %) both re-derive at 100 %, a third
  cell is at 100 % and was never named, and the size is carried as **3 cells / 2,032 buildings;
  2,806 of 8,160 fleet-wide**. Re-derive all of it on current data.
- **Why.** An item whose own numbers do not reproduce cannot be closed or acted on. This is the
  cheapest unblock on the register.
- **How.** Fleet-wide, per cell: count buildings with `height_m` absent from source vs backfilled vs
  observed, using the `data_quality_flag` census as the cross-check. Name the third cell. Re-derive
  2,032 and 2,806 and state whether each reproduces.
- **How to test.** Your fleet-wide flag census must sum to 8,160 with no building counted twice.
- **Output.** `extra/MEASUREMENT_open-12_residual-rederivation.md`.

#### T09 — OPEN-13: E-UTCI-12 containment and the 43 traded-away tests

- **What.** Two halves. (a) E-UTCI-13 is fixed; **E-UTCI-12 is "contained only"** — verify the
  containment still holds at HEAD and state what "contained" means operationally. (b) The suite fix
  that restored collection **cost 43 working tests**, reported by the director rather than the
  executor. Determine whether those 43 are still absent at HEAD.
- **Why.** (b) is a standing hole in the project's own safety net, and F9's baseline (1,919 passed)
  cannot be interpreted without knowing whether it includes them.
- **How.** For (a), find the containment mechanism, cite it, and construct the case it contains.
  For (b), diff the current collected test IDs against the pre-fix set recoverable from read-only
  git history; list the 43 by name; classify each as *deleted*, *renamed*, *skipped*, or *still
  present and passing*.
- **How to test.** Run `.venv/Scripts/python.exe -m pytest -q tests/` and report the exact counts
  against F9's **1,919 passed / 55 skipped**. Any deviation is itself a finding — report it, do not
  chase it.
- **Output.** `extra/MEASUREMENT_open-13_containment-and-lost-tests.md`.

### Group C — the imputation tier items

These three items (OPEN-15, 16, 17) are all marked ✅ measured and all block on the same kind of
decision. The tasks below make that decision *costable* without taking it.

#### T10 — OPEN-15: Phase E has no code path

- **What.** Confirm at HEAD that **no code path exists at all** for imputation Phase E, and state
  what implementing it would touch.
- **Why.** "Documented-deferred, never executed" is a claim about absence, and absence claims decay
  as code changes.
- **How.** Cite the DESIGN text that specifies Phase E (read-only) and show, by exhaustive search of
  `openubem/`, that nothing implements it. State the modules a implementation would have to touch
  and the tests that would have to exist, as a scoping estimate — **not** as a plan and **not** as code.
- **How to test.** Your absence claim must survive a search on the DESIGN's own vocabulary for the
  phase, not only on the string "Phase E".
- **Output.** `extra/MEASUREMENT_open-15_phase-e-absence.md`.

#### T11 — OPEN-16: the `ml` tier's reachability

- **What.** Confirm the `ml` imputation tier is **reachable only from the validation entry point,
  never from the production pipeline**, at HEAD, with citations.
- **How.** Trace both entry points to the tier router; cite the branch that admits `ml` and the one
  that does not. State what a production caller would have to pass to reach it.
- **How to test.** Construct the call that *would* reach it and show it is not reachable from the
  production entry point's argument surface.
- **Output.** `extra/MEASUREMENT_open-16_ml-tier-reachability.md`.

#### T12 — OPEN-17: the router hook that never existed

- **What.** OPEN-17 states, in red, that the six variance-preserving draw-tier imputers are **not
  "off" — the tier is unreachable and its router hook has never existed in any commit**. Verify that
  "in any commit" claim with read-only git archaeology.
- **Why.** It is the strongest claim on the register and rests on history, not on HEAD. If it is
  wrong, the item's whole framing changes.
- **How.** `git log --all`, `git rev-list --all` with a targeted `git grep` for the hook's name and
  for the tier's registration symbols. Report the earliest and latest commits touching the imputers
  themselves, and show the hook appears in none.
- **How to test.** Prove your search would have found the hook had it existed, by running the same
  search for a symbol you know *does* exist in history and showing it is found.
- **Output.** `extra/MEASUREMENT_open-17_router-hook-archaeology.md`.

### ⏸️ CP-2 — STOP AND REPORT (after T12)

Report T06–T12. T09(b) may change how F9 is read and T12 may reframe OPEN-17 entirely; neither
should be built on unaudited.

### Group D — simulation correctness

#### T13 — OPEN-09: does the non-convergence population still stand?

- **What.** OPEN-09 is measured at **64 % vs a 5.3 % control**, with the "cosmetic" defence tested
  and holding (96.3 % distribution overlap), and X03 established it is **independent of OPEN-56** —
  16 buildings shared, two defects. **Re-derive the population and the rate on run-4 artifacts.**
- **Why.** Every prior number for this item comes from run 2. Run 4 is the first fleet run since the
  OPEN-55 screen and the OPEN-35 geometry change, both of which touch the same buildings.
- **How.** Count warmup non-convergence warnings per building across run-4 `.err` files; report the
  rate, the population, and whether the 16-building overlap with OPEN-56 is still 16.
- **How to test.** X03's control — 150 warnings baseline, 150 treated, 15/15 unchanged — is the
  anchor. If your run-4 count for those ten buildings is not 150, say so loudly.
- **Output.** `extra/MEASUREMENT_open-09_run4-rederivation.md`.

#### T14 — OPEN-38 (i): the `LAUNDRYROOMFLR1` runaway at HEAD

- **What.** All 7 `layout_assign` fatals die on thermal runaway in one substituted-prototype zone
  (`LAUNDRYROOMFLR1`), with temperatures from −59,865 to +182,399 °C, and **no other cause appears
  in that mode**. Determine whether the mechanism still exists at HEAD.
- **Why.** `layout_assign` is *not certified for fleet EUI*, so this touches no published number —
  which is exactly why it is safe to work on and why it keeps being deferred.
- **How.** Locate the prototype substitution that introduces the zone, cite it, and determine from
  the code whether the runaway is a property of the zone's geometry, its loads, or its HVAC
  template. Do **not** re-simulate; this is a code-and-artifact question.
- **How to test.** Your explanation must account for **why zero fatals appear in the other four
  modes**, verified across all 40,800 `.err` files. An explanation that does not is incomplete.
- **Output.** `extra/MEASUREMENT_open-38_laundryroom-mechanism.md`.

#### T15 — OPEN-38 (ii): the building that publishes from malformed geometry

- **What.** 8 buildings carry malformed door geometry; **one of them
  (`nyc_rural/way_965718401`) completes successfully and publishes results.** Determine what its
  published numbers are worth.
- **Why.** This is the only known case in the arc of a *published* result resting on geometry known
  to be malformed. Its size may be zero — but nobody has checked.
- **How.** For that building: compare its run-4 EUI against its baseline EUI and against a
  same-archetype, same-cell peer group; quantify the malformation (which surface, how far outside
  its base surface); and state whether the published value is inside or outside the peer
  distribution.
- **How to test.** All 8 are `layout_assign` and **zero appear in the other four modes** — verify
  that before drawing any conclusion, because it bounds whether the adopted `auto` fleet is exposed
  at all.
- **Output.** `extra/MEASUREMENT_open-38_publishing-building.md`.

#### T16 — OPEN-10: the true ceiling on the `ZoneGroup` remedy

- **What.** X08 re-derived the 90 buildings exactly (66 `MidriseApartment` + 24 `HighriseApartment`)
  and, for the first time, gave a denominator: **90 of 1,992 `fallback_not_expressible` = 4.5 %**;
  the other 1,902 are structurally beyond the edit, and `applied` is only **497 of 7,442**.
  Re-derive all four numbers on run 4 and state the remedy's ceiling as a fraction of the fleet.
- **Why.** The item has been carried for weeks on a capability claim without a denominator. It now
  has one, from a single pass. Confirm it, then it is decidable.
- **How.** Recompute the expressibility classification across run-4 cells; report 90 / 1,992 / 1,902
  / 497 / 7,442 and whether each reproduces.
- **How to test.** The 90 must split **66 / 24** by archetype. If it does not, your classifier
  differs from X08's and the difference is the finding.
- **Output.** `extra/MEASUREMENT_open-10_expressibility-ceiling.md`.

### Group E — method and spec

#### T17 — OPEN-19: what a Title 24 switch would have to touch

- **What.** LA runs **~+40 % hot**, and the item records that this is **not currently representable**:
  no climate-zone or code-year switch exists, and LA's HVAC comes from a **Buffalo** prototype.
  Verify at HEAD and scope the change.
- **Why.** One whole city's results are affected. The item is measured; what is missing is a
  costing, and costing is not fixing.
- **How.** Cite where the prototype is selected and show it is climate-insensitive. Then enumerate
  the modules a code-year/climate-zone switch would touch, what it would need as input data, and
  which published numbers would move. **Design scoping only — write no code.**
- **How to test.** Confirm the Buffalo attribution by citation, not by repetition. If LA's prototype
  is not Buffalo at HEAD, that is the finding and the item's premise has decayed.
- **Output.** `extra/MEASUREMENT_open-19_title24-scoping.md`.

#### T18 — OPEN-03: `layout_assign` vintage at HEAD

- **What.** OPEN-03 — all internal loads modelled as 2022-code regardless of real vintage, sized at
  **~half of a −29 % cross-mode gap**. Re-verify the mechanism at HEAD and re-derive the size.
- **Why.** OPEN-01's closure changed the denominator path; whether that moved OPEN-03's number has
  never been checked.
- **How.** Cite where vintage is (not) consumed in the `layout_assign` load path. Re-derive the
  cross-mode gap on available artifacts and state how much of it the vintage path explains.
- **How to test.** The −29 % figure's `layout_assign` side is **T19, not T20** — a correction already
  recorded on this register. Use the corrected attribution; if you reproduce −29 % against T20 you
  have used the superseded framing.
- **Output.** `extra/MEASUREMENT_open-03_vintage-at-head.md`.

#### T19 — OPEN-27: the erratum for a DESIGN doc that names a non-existent archetype

- **What.** A DESIGN doc names an archetype that does not exist, **inside the coarse-metric
  definition**, and it is fixable only at the external source. Write the erratum.
- **Why.** It is spec integrity on the accuracy metric's own definition — the metric several other
  items are scored by.
- **How.** Quote the DESIGN line verbatim with its file and line number; show the archetype is
  absent from the archetype table at HEAD; name what the definition presumably meant and what it
  would take to correct it at source. **Write an erratum document. Do NOT edit the DESIGN doc**
  (§3 rule 4).
- **How to test.** Search the full archetype registry, not one table — the earlier check that
  established absence should be reproducible by you independently.
- **Output.** `extra/ERRATUM_open-27_design-archetype.md`.

#### T20 — OPEN-18 and OPEN-20: bound the two method items

- **What.** Two items, one task, because each needs a bound rather than a measurement.
  **(a) OPEN-18** — the Q3 √S vertical-form distortion is *"confirmed unreachable by the mechanism
  built for it"*: state precisely what is unreachable, and what the residual distortion is on small
  buildings in cold cells. **(b) OPEN-20** — the wider validation matrix beyond 3 cities × 4 rings:
  state what external-validity claim the current matrix does and does not support.
- **Why.** Both are carried as open with no next step named. A bound is a next step.
- **How.** For (a), cite the mechanism and the reason it cannot reach the distortion; quantify the
  residual from existing artifacts if it can be quantified, and say plainly if it cannot. For (b),
  write the external-validity statement the current 12-cell design supports — no new runs, no
  proposals for new cities.
- **How to test.** For (a) the honest answer may be "not quantifiable from what exists"; that is an
  acceptable result **if** you name the artifact that would quantify it.
- **Output.** `extra/MEASUREMENT_open-18-20_method-bounds.md`.

### ⏸️ CP-3 — STOP AND REPORT (after T20)

Report T13–T20 and hand back. The director audits, then decides which items are recommendable for
closure to the user. **No executor closes anything.**

---

## 7. Stop-and-report points

| checkpoint | after | why it is here |
|---|---|---|
| **CP-1** | T05 | T01 and T05 can change how the newly adopted `153.8231` must be read; T04 feeds a ruling already owed to the user. |
| **CP-2** | T12 | T09(b) can change how the test-suite baseline F9 is read; T12 can reframe OPEN-17 entirely. |
| **CP-3** | T20 | End of pass. Closure recommendations to the director, rulings to the user. |

## 8. Progress log

*(One entry per completed task, appended by the executor. Shape:
`#### TXX — <title> — completed YYYY-MM-DD`, then **Artifacts / Deviations / Test status / Notes**.)*

#### T06 — OPEN-53: custody re-inventory — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-53_custody-reinventory.md`;
`openubem/outputs/comparisons/corpus_inventory_2026-08-19.csv`;
`scripts/analysis/open53_t06_custody_reinventory_2026-08-19.py`.

**Deviations.** None from the task's What/How. Nothing moved, copied, compressed or deleted —
count-only, per the forbidden clause.

**Test status.** E02 `.err` reproduced the recorded 40,800 exactly. E02 `.eio` did **not**
reproduce (40,800 recorded → 145 on disk today) — explained per the task's own "how to test"
clause with a timestamp: all 40,655 now-missing directories carry mtime **2026-08-19 16:19**, one
minute-bucket, no code in `scripts/`/`openubem/` touches `eplusout.eio` for deletion. `.sql`
(39,926) and `.end` (39,925) reproduced exactly. `open48_refleet` (run 2) totals reproduced exactly
(8,297 dirs / 41,014 files / 79.75 GB). `open48_refleet3` (run 3) did **not** reproduce
(43,162/45.73 GB recorded vs 35,214/41.58 GB in the named directory today) — explained as growth
from two adjacent T02 crash-recovery directories (`_t02a3`, `_t02a4`) not swept by the original
count; summed the three together (46,357 files / 46.16 GB) is larger than the original figure, not
smaller. The cited-evidence subset for run 2 re-derived at 0.1180 GB, reproducing the register's
"under 0.12 GB" claim.

**Notes.** **Headline finding: a second, independent external sweep event took the E02 harvest's
`.eio` files today (2026-08-19 16:19), roughly two hours before this task ran** — same signature
class as the 2026-08-17 `.sql`/`.end` sweep already on the register (single timestamp, batch/fleet-
wide, external to this repository). No published number is known to depend on E02 harvest `.eio`.
Recommendation only, not applied: this reinforces OPEN-53's already-standing custody risk and its
existing closure condition; it does not change the ruling. Item not opened, closed, struck or
retired by this task.

#### T07 — OPEN-14: the config gate that closes before the missing slices matter — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-14_config-gate.md`;
`scripts/analysis/open14_t07_gate_construction_2026-08-19.py`.

**Deviations.** None. No code under `openubem/` changed — the constructed case monkeypatches
`config` attributes inside a throwaway script and a `try/finally` restores the originals; nothing
persists.

**Test status.** Constructed local case, real `overture_nyc_centre_slice.parquet`: gate closed
(shipped default `FUSION_SOURCES_BY_TARGET={}`) → `value=[nan] token=[None]`; gate open
(`{"height_m": ("overture",)}`) → `value=[8.7] token=['FUSED_OVERTURE_HIGH']`, reproduced both via
`fusion.fuse()` directly and via the full `impute_missing()` orchestrator. Existing regression
suite re-run fresh: `tests/test_height_backfill.py -k "TestFusionTierProvenanceAndFloor or
TestFuseHeightFromOfflineSlice"` → 5 passed, 0 failed.

**Notes.** Gate localised exactly to `openubem/config.py:141`
(`FUSION_SOURCES_BY_TARGET: dict = {}`), chain traced `fusion.precedence_for` (`fusion.py:167-
178`) → `fusion.fuse` (`fusion.py:379`) → `_fusion_tier` (`imputation.py:627-661`) →
`impute_missing` tier dispatch (`imputation.py:882`, `"fusion"` tier enabled by default at
`config.py:100`). **Finding beyond what the task assumed:** the register's framing treats this as
a single gate, but `impute_missing()` — the only function that reaches `fuse()` — is called from
exactly one place in the whole repository, `openubem/validation/mask_recover.py:330,338` (the
T08/T09 validation harness), and never from the production path
(`step1_fetch → BuildingClassifier.classify → _impute_levels`,
`building_classifier.py:137-155,591-694`, zero references to `fusion`/`impute_missing` — grep-
confirmed). So a clean checkout needs three things, not two, and in order: (a) the slice
committed for the target cell, (b) the production classify path rewired to call the fusion tier
for `height_m` (absent at HEAD), (c) the config gate opened — (c) alone reproduces nothing for a
fleet build, only for the validation harness. Item not opened, closed, struck or retired by this
task; recommendation only.

#### T08 — OPEN-12: re-derive the numbers that stopped reproducing — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-12_residual-rederivation.md`;
`openubem/outputs/comparisons/open12_t08_residual_rederivation_2026-08-19.csv`;
`scripts/analysis/open12_t08_residual_rederivation_2026-08-19.py`.

**Deviations.** Used run 4 (`open48_refleet4`) rather than run 2 (which the prior 2026-08-19
subset-check task already used) for the tracked-Stage-1 re-derivation, since run 4 is more current
and re-deriving on a different run than last time is a stronger reproduction test. Did not
re-derive the separate 36.4%/19.2% scratchpad-backfill pair — confirmed that pair describes a
different artifact (`scratchpad/e-utci-09-backfill/backfilled/*.gpkg`) than the tracked-fleet
numbers this task's How/How-to-test section targets, per the register's own explicit scope split.

**Test status.** Fleet-wide flag census sums to 8,160 with zero double-counts (per-cell `n` sums
exactly to 8,160). Fleet-wide 34.3873% (2,806/8,160) reproduces exactly. Three-cell 100%-absent
population sums to exactly 2,032 (245 + 198 + 1,589), reproducing the task's own stated figure.
`data_quality_flag` `no_height` vs `height_m.isna()` cross-check: **0 disagreements** across all
8,160 buildings.

**Notes.** Third (previously unnamed) 100%-absent cell confirmed as `nyc_suburban` (1,589/1,589).
`provenance_height_m` takes exactly two values fleet-wide (`OSM_OBSERVED`, `OSM_MISSING`) —
`n_backfilled = 0` in every cell, corroborating T07/OPEN-14's independent finding that no code
path backfills `height_m` on the fleet's tracked files. No STOP triggered; every number asked for
reproduced. Item not opened, closed, struck or retired by this task.

#### T01 — OPEN-59 at fleet scale — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-59_fleet-scale.md`;
`openubem/outputs/comparisons/open59_unknown_gap_fleet.csv`;
`scripts/analysis/open59_fleet_scale_2026-08-19.py`.

**Deviations.** None from the task's How.

**Test status.** All three required controls pass: `nyc_suburban` Unknown/classified split
290/1,299 (exact); fleet Unknown count 650 (exact); fleet Unknown pooled total EUI 107.21696
(required 107.22 ± 0.01); `nyc_suburban`'s own recorded median-per-building numbers (total, DHW,
heating, lighting, cooling) all reproduce to within rounding.

**Notes.** Both statistics named in the task are real and reproducible, and they disagree because
they answer different questions: pooled (floor-area-weighted) Unknown EUI is 107.22, **31 % below**
classified's 155.56; median per-building Unknown EUI is 309.95, **2.31×** classified's 134.08 —
larger fleet-wide than the 1.7× recorded on `nyc_suburban` alone. Cause of the disagreement traced
and cited: Unknown floor area is dominated by a handful of very large, moderate-EUI buildings
(top 10 of 650 hold 72.5 % of Unknown floor area; correlation between Unknown floor area and EUI is
r = −0.27), while the *typical* Unknown building is small and runs hot, matching the median
statistic. DHW is fleet-wide the largest end-use multiple (10.2×), ahead of heating (3.4×);
lighting's 6.7× on `nyc_suburban` alone does **not** generalise (1.00× fleet-wide). Recommendation
only, not acted on: OPEN-59's §1 row should carry both statistics, each labelled by which
population weighting it uses. Item not opened, closed, struck or retired by this task.

#### T02 — OPEN-56: localise the writer — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-56_writer-localisation.md`. No `.csv` — code citations and a
pass/fail control only, per the task's own output spec. No fix made; no file under `openubem/`
edited.

**Deviations.** None from the task's How, but the task's premise was found false at HEAD and is
reported per hard rule 1 (see below) rather than worked around.

**Test status.** Prediction test passed: a second building from a cell never previously cited for
this defect (`nyc_urban / relation_17949119`) carries both `Floor is upside down!` and `Roof/
Ceiling is upside down!` warnings, as predicted. Strengthened with a full fleet re-check: **8,160 /
8,160 (100.00 %)** of run-4 buildings across all twelve cells carry the warning, matching the
register's prior run-2/run-3 counts exactly on run 4 too.

**Notes.** 🔴 **Premise false at HEAD, per hard rule 1.** T02's **What** quotes the register's
stale top-line tag ("writer not yet localised"); the register's own `### OPEN-56` §-section
(`:7354-7357`, W05) already localises the writer to `geomeppy` (third-party, not `openubem/`). Rule
11 requires re-deriving rather than quoting, so this task re-derived independently and found W05's
conclusion **incomplete**: `geomeppy==0.12.2`'s own winding-correction step
(`set_entry_direction`, `geom/polygons.py:592-611`) is empirically a no-op for our GGR convention
(`entry_direction="counterclockwise"`) due to a self-referential bug in `outside_point()`/
`is_clockwise()` (`geom/polygons.py:349-364,311-323`) — verified directly against the installed
package with three standalone tests. Because that corrector never fires, the winding written to
the IDF is exactly what `geomeppy.builder.Block.floors`/`.ceilings`/`.roofs` (`builder.py:173-213`)
compute directly from the **input footprint's own orientation** — traced through
`openubem/geometry/zoning.py:52`, `openubem/geometry/footprint.py:52-55`, and
`openubem/idf/builder.py:464-465` (the one orientation call that exists, `orient(poly_local,
sign=1.0)`, is gated to fire only when `resolution_mode != "auto"` — never for the adopted
baseline mode). Measured directly: 0/20 random source footprints are CCW, matching the 100 %
defect rate. Two remedy shapes named, neither applied: extend the existing `orient()` call to
`auto` mode too (sign unverified), or write `Zone.Volume` explicitly as the register already
proposes. Item not opened, closed, struck or retired by this task.

#### T03 — OPEN-58: measure the blast radius — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-58_blast-radius-enumeration.md`;
`openubem/outputs/comparisons/open58_run_ep_consumers.csv`;
`scripts/analysis/open58_run_ep_enumeration_2026-08-19.py`.

**Deviations.** None from the task's How.

**Test status.** Required control passed by a different method than the one already on record: a
byte-identical-numeric-row check on `open35_storey_intervention_results_v2.csv` found **zero**
duplicated rows across 21 distinct buildings in either arm — independently reaches the same
"unaffected" verdict the existing record reports, without reusing its `.sql`-hashing method.

**Notes.** 🔴 **Premise false at HEAD, per hard rule 1.** T03's **What** quotes OPEN-58's
opening-time "unknown" population; the register's own `### OPEN-58` §-section (`:7713-7760`)
already carries a full blast-radius measurement (T06–T08 of a prior plan), with both cited
artifacts confirmed present on disk before this task started. Per rule 11, re-derived
independently anyway, by a disk walk (not `git grep` — the origin file and its real importers are
**untracked**, and a tracked-files-only search was tested first and found only 5 of the 8 files,
confirming the risk) plus a classifier script written from scratch. **Result: exactly reproduces
the existing record — 3 real importers (`open56_fleet_cost_stratified.py`,
`open56_fleet_cost_repair.py`, `open35_storey_intervention_2026-08-19.py`), 4 name-collisions, 1
origin file, 8 total.** No new recommendation beyond the four already on the register at
`:7757-7760`. Item not opened, closed, struck or retired by this task.

#### T04 — The OPEN-35 regression: is it one building or a population? — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-35_regression-population.md`;
`openubem/outputs/comparisons/open35_regression_population_2026-08-19.csv`;
`scripts/analysis/open35_regression_population_2026-08-19.py`.

**Deviations.** None from the task's How.

**Test status.** Required control passed exactly: the independently parsed repair census for
`nyc_centre` recovers the same 7 buildings named in that cell's own log line
`Repaired and resimulated: [...]`, de-duplicated — no more, no fewer.

**Notes.** Population is neither 1 nor all 21. Fleet-wide repair census (from
`open48_run4/*.log`, 9 buildings total) cross-tabulated against the 21-building Scope-B set
(`open35_fallback_agreement_scope.csv`) and a matched control (414 non-Scope-B buildings, real
`levels ≥ 10`): Scope-B's repair rate is **19.0 % (4/21)** against the matched control's **0.97 %
(4/414)**, a real ~20× elevation — but it is entirely concentrated in the `nyc_centre` /
`LargeHotel` / imputed-to-19-storeys subset (**4/8 = 50 %**); every other Scope-B subset, including
`austin_centre`'s even-taller 45-storey imputations, is **0/13 = 0 %**. Ruled out `nyc_centre`
itself as the explanation: that cell's own background repair rate on real tall buildings (292
buildings, levels ≥ 10) is 1.03 %, statistically indistinguishable from the fleet-wide control.
Only 1 of 21 (4.8 %) — the one already named — actually fails to complete; the other 3 affected
buildings repair and complete successfully. `way/402215469` (la_urban), which also needed repair,
is confirmed **not** an OPEN-35 building — it is the known OPEN-42/OPEN-56 Warehouse placeholder
building. **Recommendation, not an action:** scope the ID against the 8-building `nyc_centre`/
`LargeHotel`/19-storey population, not against the single building or the full 21. Item not
opened, closed, struck or retired by this task.

#### T05 — The EUI denominator census — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_eui-denominator-census.md`;
`openubem/outputs/comparisons/eio_area_vs_derived_fleet.csv`;
`scripts/analysis/open01_eui_denominator_census_2026-08-19.py`.

**Deviations.** None from the task's How.

**Test status.** Required control passed: OPEN-01's closure figure for `auto` mode (99.63 % within
±1 %) reproduces on run 4 at **99.74 %** — Δ = +0.11 percentage points, within "a few tenths of a
percent."

**Notes.** Fleet-wide (8,153 successes, all `floor_area_provenance == 'eio_simulated'`): median
ratio 1.000000, 99.74 % within ±1 %, 99.91 % within ±10 %, **100.00 % within 2× — zero buildings
outside 2×.** The 21 buildings outside ±1 % are, without exception, `zoning_strategy ==
'perimeter_core'` — a structural core/perimeter-split geometry effect, not a new defect; max
1.31×, none beyond 2×. **The lead this task's own framing carried forward — `relation_3566904`'s
reported area moving 157,115 → 37,551 m² (÷4.18) — is closed as a false lead.** This census's own
production-data row for that building (`footprint_area_m2 = 2,682.23`, `levels = 14`,
`floor_area_m2 = 37,551.22`, ratio **1.000001**) shows no anomaly at all; the 157,115 m² figure
belongs to a *different* building (`relation/11171793`, confirmed via this same task's fleet data),
and matches OPEN-58's own already-recorded finding that the OPEN-56 side-experiment's baseline arm
for `relation_3566904` was contaminated by `relation_11171793`'s output via the `run_ep()`
shared-cwd defect — an independent, second confirmation of OPEN-58's verdict from untouched
production data. **Conclusion: the `auto`-mode EUI denominator is sound fleet-wide on run 4; F1
(`153.8231 kWh/m²`) is not reopened, changed, or restated by this task.** Item not opened, closed,
struck or retired by this task.

### ⏸️ CP-1 reached — T01–T05 complete, reported for director audit. Not continuing past this
point without further instruction, per plan §7.

### ✅ CP-1 — AUDITED AND SIGNED 2026-08-19 (late), director

**Verdict: pass.** T01–T05 greenlit. Audited against the CLAUDE.md standard — progress-log
entries present and in format, stated controls re-checked, planned-files-only confirmed, citations
demanded for every unplanned conclusion.

**Artifacts.** All 13 claimed artifacts confirmed present on disk at the paths the log gives
(5 `extra/MEASUREMENT_*.md`, 4 `openubem/outputs/comparisons/*.csv`, 4 `scripts/analysis/*.py`).
No claimed artifact missing; no artifact written outside the plan's §4 file layout.

**Scope discipline.** `find openubem tests scripts/validation -mmin -180` returns **empty** — no
source file, test, or validation script was touched by any of the three executors. No `.py` was
written under `docs/`. No item was opened, closed, struck or retired. No git write command ran.
(Pre-existing, not this pass: ten `.py` files sit under `docs/docs_DONE/LOADS & SCHEDULES/
elevators/scripts/`, dated 2026-07-21 — a standing violation of the CLAUDE.md "no `.py` under
`docs/`" rule inherited from that archived arc. Flagged, not acted on.)

**Director's own re-verification of the load-bearing claim.** T02's central finding — that
`geomeppy==0.12.2`'s winding corrector is a provable no-op under our GGR convention — was not
taken on the executor's word. Re-derived twice, independently:
- *By inspection:* `Polygon3D.outside_point("counterclockwise")` returns `vertices[0] +
  normal_vector`; `is_clockwise(viewpoint)` then computes `v = vertices[0] − viewpoint =
  −normal_vector` and `sign = dot(−n, n) = −|n|² < 0`, so it returns `False` **unconditionally**.
  The CCW branch of `set_entry_direction` therefore never calls `invert_orientation()`. The test
  is self-referential: the "outside point" is constructed from the same normal the test consumes.
- *By execution:* a standalone run against the installed package on a CW-wound and a CCW-wound
  square both report `is_clockwise=False, inverted=False`. Neither winding is corrected.
The consequence the executor drew is therefore sound: the winding in the IDF is whatever the input
footprint's own orientation was. The gate at `openubem/idf/builder.py:464-465` was also read
directly and confirms the second half — `orient(poly_local, sign=1.0)` is guarded by
`if self.resolution_mode != "auto"`, so it never fires for the adopted baseline mode.

**Two false premises, correctly reported rather than worked around (hard rule 1).** T02 and T03
both found the task's **What** quoting a stale register top-line tag that the register's own
§-section already contradicts (`OPEN-56` at `:7354-7357`; `OPEN-58` at `:7713-7760`). Both
re-derived independently under rule 11 rather than stopping. T03's re-derivation reproduced the
existing count exactly (3 real importers, 4 name-collisions, 1 origin, 8 total) by a different
method — a disk walk, correctly chosen because the origin file and its importers are untracked and
a `git grep` was tested first and found only 5 of 8. **Director's note: the register's top-line
tags for OPEN-56 and OPEN-58 are stale against their own §-sections and should be resynced.**

**Findings carried forward.**
1. **OPEN-59** — both statistics are real and disagree legitimately: pooled Unknown EUI 107.22
   (−31 % vs classified 155.56) against median-per-building 309.95 (2.31× classified 134.08). Cause
   cited: the top 10 of 650 Unknown buildings hold 72.5 % of Unknown floor area and run at moderate
   EUI (r = −0.27 between area and EUI), so area-weighting and per-building medians answer
   different questions. The register's `1.7×` is the median statistic measured on `nyc_suburban`
   alone and does not generalise. Recommendation: OPEN-59's row should carry both, each labelled
   by weighting. `nyc_suburban`'s lighting 6.7× does **not** generalise (1.00× fleet-wide).
2. **OPEN-56** — a **third** remedy shape now exists and the mechanism is fully localised: extend
   the existing `orient()` call to `auto` mode (sign unverified), alongside the register's standing
   "write `Zone.Volume` explicitly". 8,160/8,160 (100.00 %) of run-4 buildings carry the warning.
   This sharpens, and does not resolve, the ruling already owed to the user.
3. **OPEN-35 regression** — population is neither 1 nor 21. Repair rate is 19.0 % (4/21) in Scope B
   against a matched control of 0.97 % (4/414), but concentrated entirely in the `nyc_centre` /
   `LargeHotel` / imputed-19-storey subset at **4/8 = 50 %**; every other Scope-B subset is 0/13,
   including `austin_centre`'s taller 45-storey imputations. Only 1 of 21 actually fails. Cell
   effect ruled out (`nyc_centre` background rate on real tall buildings = 1.03 %).
   **Recommendation to the user, not an action: scope the owed ID against the 8-building subset.**
4. **OPEN-01 denominator** — sound fleet-wide on run 4: 99.74 % within ±1 % (closure figure 99.63 %),
   100.00 % within 2×, zero buildings beyond. The 21 outside ±1 % are without exception
   `zoning_strategy == 'perimeter_core'`, a structural effect, max 1.31×. **F1 (`153.8231`) is not
   reopened, changed or restated.**
5. **A third retraction, this one of a standing lead.** `relation_3566904`'s reported ÷4.18 area
   anomaly is **closed as a false lead**: production run-4 data gives that building
   `footprint_area_m2 = 2,682.23`, `levels = 14`, `floor_area_m2 = 37,551.22`, ratio 1.000001 — no
   anomaly. The 157,115 m² belongs to `relation/11171793`, and the contamination path is OPEN-58's
   `run_ep()` shared-cwd defect. This is an independent second confirmation of OPEN-58's verdict,
   from untouched production data.

**Nothing in CP-1 changes the adopted baseline.** `153.8231 kWh/m²` pooled over 8,153 stands, with
the OPEN-56 volume caveat unchanged.

#### T10 — OPEN-15: Phase E has no code path — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-15_phase-e-absence.md`. No script (search-and-cite task;
every command reproduced verbatim in the doc).

**Deviations.** None.

**Test status.** Absence claim tested against both the bare phrase "Phase E" and the DESIGN's own
vocabulary for the four candidate families (`TabPFN`, `TABPFN_IMPUTED`, deep-generative, spatial
GNN, `GAIN`, `MIWAE`, `TabDDPM`, `MIDAS`, tab-transformer, foundation-model) via
`grep -rniE` across `openubem/` and `scripts/`. Only genuine hits: `openubem/results/
impute_figures.py:178-186,676-692`, confirmed to be figure-annotation metadata (plotting the
ruling as a chart), not an implementation. Zero hits in `openubem/semantic/imputation.py`.

**Notes.** DESIGN citation: `docs/docs_DONE/INPUTS/imputation/results/phase_E/RESULTS_phaseE.md`
("Phase E is documentation, not execution... No frontier method enters the default pipeline").
Scoping estimate given (new tier module, `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES` entry,
config surface, pinned model artifact, provenance token, tests) — explicitly labelled scoping
only, no code written, no plan authored. Item not opened, closed, struck or retired by this task.

#### T11 — OPEN-16: the `ml` tier's reachability — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-16_ml-tier-reachability.md`. No new script — re-ran an
existing targeted slice of `tests/test_ml_imputer.py` as the constructed reachability proof.

**Deviations.** None.

**Test status.** `.venv/Scripts/python.exe -m pytest -q tests/test_ml_imputer.py -k "TestRouting or
TestOptInOnly" -v` → 6 passed, 0 failed. `inspect.signature(enrich_semantics)` confirmed
`['gdf', 'output_dir', 'load_mode', 'random_seed', 'construction_table', 'loads_table',
'schedules_table']` — no tier-config parameter of any kind.

**Notes.** Production (`enrich_semantics`, `openubem/semantic/__init__.py:324-332`) never reaches
`_ml_tier`; its own imputation calls (`construction_sets.py:323-330`, `draw_methods.py:121`) use a
different, lower-level function (`impute_column`) with `method="kde"` hard-coded as a literal —
confirmed by grepping every non-test caller of `impute_column(` repo-wide. The only path to
`_ml_tier` is `impute_missing()`, whose only caller anywhere is the validation harness
(`openubem/validation/mask_recover.py:330,338`, established in T07). Confirms and structurally
strengthens N10's original finding. Item not opened, closed, struck or retired by this task.

#### T12 — OPEN-17: the router hook that never existed — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-17_router-hook-archaeology.md`. Read-only git archaeology
only; every command reproduced verbatim in the doc, no script.

**Deviations.** None.

**Test status.** `git log --all -S"_draw_tier" --oneline -- openubem/semantic/imputation.py` and
the same for `IMPUTE_DRAW_METHOD_BY_TARGET` against `config.py`: both empty, reproducing N10's
finding. **Positive control run per the task's own requirement:** identical command for `_ml_tier`
(known to exist at HEAD) against `imputation.py` → 2 commits found (`0df422e`, `03e2121`),
confirming the search method is not blind to a real symbol's introduction.

**Notes.** Widened to whole-repo `-S"_draw_tier"` (8 commits) — every one touches only test files
that reference the hoped-for hook, docs/register commits, or the commit that added the six
imputers themselves (`ef19141`, never `imputation.py`). `draw_methods.py` has exactly one commit
in its history (`ef19141`, 2026-07-21) and `imputation.py` was touched again four days later
(`3a925f9`, 2026-07-25) without adding the hook — ruling out "not chronologically possible yet" as
an innocent explanation. Verdict: claim reproduces and is strengthened, not weakened. Item not
opened, closed, struck or retired by this task.

#### T13 — OPEN-09: does the non-convergence population still stand? — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-09_run4-rederivation.md`.
`scripts/analysis/open09_run4_rederivation_2026-08-19.py`,
`openubem/outputs/comparisons/open09_run4_perbuilding.csv`.

**Deviations.** None.

**Test status.** X03 anchor reproduced exactly: the 10 control buildings sum to 150 warnings on run
4 (anchor: 150). Fleet-wide scan covered all 8,160 run-4 `.err` files (expected 8,160).

**Notes.** Population and rate are byte-identical to run 2: 16/8,160 (0.1961%), same cells, same
counts. The 16-building overlap with OPEN-56 reproduces exactly (still 16). New observation: the 6
OPEN-56/OPEN-42 fatal Warehouse buildings each carry exactly 15 non-convergence warnings in run 4,
same as the 10 successful X03 buildings — they sit inside OPEN-09's population by signature, and
fail for the separate, already-established OPEN-56 reason. Neither the OPEN-55 screen nor the
OPEN-35 storey correction touched this population. Item not opened, closed, struck or retired.

#### T14 — OPEN-38 (i): the `LAUNDRYROOMFLR1` runaway at HEAD — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-38_laundryroom-mechanism.md`. No new script for the
mechanism read (direct citation + reuse of same-day T05 rebuild artifacts); one ad hoc `grep` across
the 40,800-file E02 harvest for the "zero fatals elsewhere" control, command recorded in the report.

**Deviations.** None. No re-simulation performed, per the task's own rule.

**Test status.** `LAUNDRYROOMFLR1` token grepped across all 40,800 `.err` files in
`%LOCALAPPDATA%/Temp/ubem_e02_harvest`: 0 in `auto`/`building`/`floor`/`fast_zone`, 8 in
`layout_assign` (the 7 fatals + the 1 non-fatal `way/965718401`) — matches the register's disjoint-
mode claim exactly.

**Notes.** Mechanism still exists at HEAD (reconfirmed via same-day OPEN-38 T05 rebuild, 6/6
reproduced). Determined which of geometry/loads/HVAC the runaway is a property of: geometry is
clean (positive, plausible zone volume 378.63 m³ from `.eio`, not OPEN-56's stub); the DOE prototype
gives `LaundryRoomFlr1` **zero HVAC** (absent from all 54 `ZoneHVAC:EquipmentConnections` entries in
the baseline IDF); the zone carries the floor's largest absolute internal-gain density (46,286.64 W
gas dryer, scaled from the baseline's own extreme 40,096.03 W literal, plus a water heater's ambient
losses) with nothing to cap it. Verdict: an unconditioned zone with the fleet's largest absolute
load density free-floats into a `CalcHeatBalanceInsideSurf` numerical divergence during Sizing — a
loads/no-HVAC interaction, not a geometry defect and not a wrong HVAC template. Item not opened,
closed, struck or retired.

#### T15 — OPEN-38 (ii): the building that publishes from malformed geometry — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-38_publishing-building.md`.
`scripts/analysis/open38_t15_malformed_publisher_rebuild_2026-08-19.py`,
`scratchpad/open38-t15-rebuild/` (gitignored scratch).

**Deviations.** One local EnergyPlus rebuild was run (`nyc_rural/way_965718401`, `layout_assign`,
real unmodified pipeline) because neither the existing E02-harvest `.sql` nor any HEAD-consistent
`layout_assign` fleet table could supply this building's EUI — precedent: OPEN-38 T05 did the same
same-day for the fatal population. No cluster, no production code touched.

**Test status.** All 8 malformed-door buildings confirmed `layout_assign`-only, 0 in the other four
modes (shared control with T14). Rebuild reproduced the register's own citation almost exactly:
"EnergyPlus Completed Successfully — 58,101,663 Warning; 0 Severe" vs the register's 58,101,662.

**Notes.** The building's own published EUI is **not quantifiable from what exists on disk**: its
harvested `.sql` fails `parse_building()` (`failed_zone_mismatch`, empty `ReportDataDictionary`), and
a fresh HEAD rebuild reproduces the identical failure. Traced to root cause (shared with T18): every
`layout_assign` rebuild in this arc used `trim_outputs=True`, which skips the zone-level
`Output:Variable` block the parser's `layout_assign` zone-integrity gate requires — confirmed by
rebuilding a different building with `trim_outputs=False`, which parses successfully
(`total_eui_kwh_m2=68.28`). The only pre-existing `layout_assign` number for this osm_id
(`t20_layout_assign_eui.csv`, 911.41) is untrustworthy: that generation labels the building
`SmallOffice` while its own raw zone names are unambiguously `SmallHotel` (a fresh OPEN-06 instance),
and carries zero `SmallHotel` peers fleet-wide to benchmark against. Bound established independent of
the missing number: OPEN-32 already shows structurally that no adopted result depends on
`layout_assign`, so this building's size on any published figure is zero regardless. Named what would
quantify it: a `trim_outputs=False` rebuild of this building and its `SmallHotel` peers. Item not
opened, closed, struck or retired.

#### T16 — OPEN-10: the true ceiling on the `ZoneGroup` remedy — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-10_expressibility-ceiling.md`.
`scripts/analysis/open10_run4_expressibility_2026-08-19.py`,
`openubem/outputs/comparisons/open10_storey_expressibility_run4.csv`.

**Deviations.** None.

**Test status.** Evaluated population reproduced exactly (7,442). The 90-building split did **not**
reproduce exactly (69/27 vs carried 66/24) — per hard rule 11 this is reported as a finding, not
smoothed over.

**Notes.** Explained, not merely flagged: run 4 carries OPEN-35's storey-count corrections, which
OPEN-10's own X08 finding already identified as upstream of this exact classification boundary for
`MidriseApartment`/`HighriseApartment`. All other archetype counts in `fallback_not_expressible` are
unchanged. Restated ceiling: 96 of 2,007 `fallback_not_expressible` = 4.78% (carried: 4.5%),
`SmallOffice` still dominating the unreachable 95.22%. Capability and narrowness both reconfirmed on
current fleet-scale data. Item not opened, closed, struck or retired.

#### T17 — OPEN-19: what a Title 24 switch would have to touch — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-19_title24-scoping.md`. No script — citation and scoping
only, per the task's own rule ("write no code").

**Deviations.** None.

**Test status.** Buffalo-prototype premise re-verified by independent citation
(`layout_assigner.py:25`) — holds at HEAD, not decayed. Zero hits, independently re-grepped, for
Title 24/CEC/CALGreen across `openubem/`/`scripts/`. Economizer hardcode reconfirmed at all 6 cited
call sites.

**Notes.** Enumerated the modules a climate-zone/code-year switch would touch (`ARCHETYPE_IDF_MAP`/
`BaselineIDFRegistry`, `hvac.py`'s economizer and COP consumers, per-prototype envelope constants,
infiltration, `enrich_semantics`'s already-computed-but-unused `climate_zone`) and the data gap
(no Title 24 table exists anywhere in `openubem/data/`) that blocks it before code does. Noted the
existing `construction_table` hook is wired only to the `OpenUBEMUnknown` synthetic path, not to any
real archetype. Named which published numbers would move (LA cells directly; Austin flagged as an
adjacent, not-yet-opened question). Zero-fitted-parameters distinction restated, not re-litigated.
Item not opened, closed, struck or retired.

#### T18 — OPEN-03: `layout_assign` vintage at HEAD — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-03_vintage-at-head.md`.
`scripts/analysis/open03_t18_trim_hypothesis_check_2026-08-19.py`,
`scratchpad/open03-t18-trim-check/` (gitignored scratch).

**Deviations.** One local EnergyPlus rebuild (`la_urban/relation_6356887`, `layout_assign`, real
pipeline, `trim_outputs=False`) to test and confirm the root cause of a parsing blocker found while
scoping this task (shared with T15). No cluster, no production code touched.

**Test status.** Used the register's own corrected attribution (T19 vs T08, not T20 vs T08) — did
not reproduce −29% against the superseded T20 framing, as instructed. `grep vintage
openubem/idf/builder.py` → 0 matches, confirmed absent from the `layout_assign` load path at HEAD.

**Notes.** Confirmed structurally that no fleet-wide, HEAD-consistent, production-parseable
`layout_assign` EUI table currently exists on disk (run 4 has no `layout_assign` mode; every fresh
rebuild in this arc used `trim_outputs=True`, which the same-day trace shows blocks
`parse_building()` fleet-wide, not just for one building; older generations are independently
confirmed archetype-unreliable). Provided one HEAD-consistent, explicitly-not-generalised n=1
illustration (`layout_assign` −16.6% vs `auto` for one `SmallOffice` building, confounded by a large
denominator mismatch). Confirmed the vintage-blindness mechanism (2013-vs-2022 load ratios,
lighting 1.722/equipment 1.064/occupancy 1.000) is unchanged in code and therefore still the best
available estimate of "how much it explains," while being explicit that no fresh fraction against a
current fleet-wide gap was derived, because no such gap currently exists on disk. Named the artifact
that would fix this arc-wide (a `trim_outputs=False` rebuild, sampled or full). Item not opened,
closed, struck or retired.

#### T19 — OPEN-27: the erratum for a DESIGN doc that names a non-existent archetype — completed 2026-08-19

**Artifacts.** `extra/ERRATUM_open-27_design-archetype.md`. No script — direct citation only.

**Deviations.** None. DESIGN doc not edited, per hard rule 4 (absolute).

**Test status.** `grep -rn "MultifamilyHome" openubem/` → 0 matches, full-registry search (not one
table), reproducing the prior finding independently.

**Notes.** Quoted DESIGN line 529 verbatim; confirmed the registry's actual second Residential
archetype is `HighriseApartment`; wrote the paste-ready correction text for the user's external
DESIGN tool. Existing regression test (`TestOpen27ArchetypeNameBinding`) reconfirmed pinning the
code against ever silently matching the wrong DESIGN text. Item not opened, closed, struck or
retired (correction is the user's to apply at source).

#### T20 — OPEN-18 and OPEN-20: bound the two method items — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-18-20_method-bounds.md`. No new script — citation and
enumeration only, per the task's own rule (no new runs, no proposals for new cities).

**Deviations.** None.

**Test status.** OPEN-18's "shorter case unreachable" claim re-confirmed by direct docstring
citation at HEAD (`match_storeys()`, `layout_assigner.py:546-549`). OPEN-20's 12-cell/8,160-building
matrix re-confirmed against run 4 (T13's own independent 8,160-file count).

**Notes.** (a) OPEN-18: mechanism confirmed still structurally unable to reach the shorter case;
residual distortion size stated as **not quantifiable from what exists on disk**, with the reason
named (same `layout_assign`-parsing blocker T15/T18 traced this pass) and the artifact that would
quantify it named explicitly, per the plan's own acceptable-answer clause. (b) OPEN-20: wrote the
external-validity statement the current three-city/four-ring/12-cell/three-climate-zone matrix
supports and what it explicitly does not (no climate zones outside 2A/3B/4A, no building-stock
composition beyond the three sampled metros, urban-form typology unvalidated beyond this sample,
and — cross-referenced to T17 — even within the three sampled climates the underlying model does not
yet differentiate its physical response by climate zone). No new item opened. Item not opened,
closed, struck or retired.

### ✅ CP-3 — AUDITED AND SIGNED 2026-08-19 (late), director

**Verdict: pass.** T13–T20 greenlit. Same audit standard as CP-1.

**Artifacts.** All claimed artifacts confirmed present: 8 `extra/*.md` (7 `MEASUREMENT_*`, 1
`ERRATUM_*`), 4 `scripts/analysis/*.py`, 2 `openubem/outputs/comparisons/*.csv`. Two gitignored
scratch trees under `scratchpad/` as declared. No artifact outside the plan's §4 layout.

**Scope discipline.** `find openubem tests scripts/validation -type f -mmin -200` (excluding
`outputs/`) returns **empty** — no source file, test or validation script touched, despite two
tasks running real EnergyPlus rebuilds. No item opened, closed, struck or retired. No git write.

**Director's own re-verification.**
- **T13's control re-derived from the executor's own CSV by the director**: `has_converge` is true
  on **16 of 8,160 = 0.1961 %**, matching run 2 exactly. Population, rate and the 16-building
  OPEN-56 overlap all stand.
- **T20/T19's absence claim re-run**: `MultifamilyHome` has **zero** hits anywhere under
  `openubem/`, and `HighriseApartment` is present in `semantic/__init__.py` and
  `semantic/building_classifier.py`. The DESIGN doc names an archetype that does not exist; the
  erratum is correct and the DESIGN doc was **not** edited (hard rule 4 honoured).
- **The cross-cutting `trim_outputs` finding re-verified in code by the director**, not accepted on
  report: `BuildingIDF.__init__` takes `trim_outputs: bool = False` (`idf/builder.py:219,227`) and
  passes it to `write_outputs(self.idf, trim_hourly=self.trim_outputs)` at `:516` and `:638`; the
  parser's gate is `_check_zone_integrity` (`results/parser.py:203`, called at `:772-774`) and its
  own comment at `:85` states it "still looks for Ideal Loads variables to parse zones". Trimming
  the per-zone `Output:Variable` block therefore starves exactly the check that gates
  `layout_assign` parsing. **The mechanism is real and is confirmed independently of the executor.**

**🔴 One genuinely new cross-cutting finding, surfaced independently by three tasks (T15, T18,
T20a), and correctly NOT opened as an item by the executor.** No `layout_assign`-mode artifact
built anywhere in this arc — the E02 harvest or today's fresh rebuilds — can currently deliver a
production-parser EUI, because `trim_outputs=True` was used everywhere and strips the zone-level
output the parser's integrity gate requires. Consequences, all reported rather than worked around:
T15 cannot quantify the malformed-door building's EUI; T18 cannot produce a HEAD-consistent
fleet-wide `layout_assign` vintage comparison; T20(a) cannot size OPEN-18's residual distortion.
**Each named the artifact that would quantify it — a `trim_outputs=False` rebuild — rather than
substituting a weaker number.** ⚠️ **This is a measurement-capability defect, not a defect in any
published figure**: OPEN-32 already establishes structurally that no adopted result depends on
`layout_assign`, so the bound on all three is zero regardless. **Whether it becomes an item is the
director's call and, being a new ID, the user's to ratify — deliberately not taken here.**

**Findings carried forward.**
1. **OPEN-09 is unmoved and unmovable by this year's fixes** — 16/8,160 byte-identical to run 2,
   same cells, same counts; neither the OPEN-55 screen nor the OPEN-35 storey correction touches
   it. New observation: the 6 OPEN-56/OPEN-42 fatal `Warehouse` buildings each carry exactly 15
   non-convergence warnings, the same as the 10 successful X03 controls — they sit **inside**
   OPEN-09's population by signature while failing for the separate, already-established reason.
2. **OPEN-38(i)'s runaway is a loads/no-HVAC interaction, not geometry and not a wrong template.**
   `LaundryRoomFlr1` has **zero HVAC** in the DOE `SmallHotel` prototype — absent from all 54
   `ZoneHVAC:EquipmentConnections` entries — while carrying the floor's largest absolute
   internal-gain density (46,286.64 W gas dryer plus water-heater ambient losses). An unconditioned
   zone with nothing to cap that load free-floats into a `CalcHeatBalanceInsideSurf` divergence
   during Sizing. Geometry is explicitly cleared: zone volume 378.63 m³ from `.eio`, positive and
   plausible — **not** an OPEN-56 stub. Disjoint-mode claim reproduced exactly across all 40,800
   `.err` files: 0 hits in `auto`/`building`/`floor`/`fast_zone`, 8 in `layout_assign`.
3. **T15's rebuild corroborates the register to within one warning** — "58,101,663 Warning; 0
   Severe" against the register's recorded 58,101,662. ⚠️ It also found the only pre-existing
   `layout_assign` number for that building (911.41) is **untrustworthy for a second, independent
   reason**: that generation labels it `SmallOffice` while its own raw zone names are unambiguously
   `SmallHotel` — **a fresh OPEN-06 instance**, in an item already closed and retired.
4. **OPEN-10's ceiling restated on run-4 data: 4.78 % (was 4.5 %), 96 of 2,007.** The evaluated
   population reproduced exactly (7,442) but the 90-building split did **not** (69/27 against the
   carried 66/24) — **self-reported as a finding under rule 11 rather than smoothed over**, and
   explained: run 4 carries OPEN-35's storey corrections, which OPEN-10's own X08 finding already
   placed upstream of exactly this `MidriseApartment`/`HighriseApartment` boundary. All other
   archetype counts are unchanged. Capability and narrowness both reconfirmed.
5. **OPEN-19 is blocked by a data gap before it is blocked by code** — no Title 24 table exists
   anywhere in `openubem/data/`. Buffalo-prototype premise re-verified at HEAD, not decayed; zero
   Title 24/CEC/CALGreen hits; the economizer hardcode reconfirmed at all 6 sites; the existing
   `construction_table` hook found to be wired only to the `OpenUBEMUnknown` synthetic path, not to
   any real archetype.
6. **OPEN-27's erratum is written and the DESIGN doc is untouched**, with paste-ready correction
   text for the user's external tool. The existing `TestOpen27ArchetypeNameBinding` regression test
   still pins the code against silently matching the wrong DESIGN text.
7. **OPEN-20's external-validity statement is written**: the matrix supports three metros, four
   rings, 12 cells, climate zones 2A/3B/4A only — and, cross-referenced to T17, **even within those
   three the model does not yet differentiate its physical response by climate zone.**

**Nothing in CP-3 changes the adopted baseline.** `153.8231 kWh/m²` pooled over 8,153 stands.

#### T09 — OPEN-13: E-UTCI-12 containment and the 43 traded-away tests — completed 2026-08-19

**Artifacts.** `extra/MEASUREMENT_open-13_containment-and-lost-tests.md`;
`openubem/outputs/comparisons/open13_t09_containment_and_lost_tests.csv`;
`scripts/analysis/open13_t09_containment_and_lost_tests_2026-08-19.py`.

**Deviations.** None. Full-suite run (`.venv/Scripts/python.exe -m pytest -q tests/`) took
20m40s in the background, per the plan's own note that this is an expensive pass — run once,
not repeated.

**Test status.** (a) `grep -c "_draw_tier" openubem/semantic/imputation.py` → 0 (defect still
live, contained not fixed). `pytest -q tests/test_draw_methods.py -rs` → 43 passed, 10 skipped,
reproduced fresh. (b) Function-set diff, pre-containment commit `25924dd` (parent of the
2026-08-12 containment commit `a3bf4d9`) vs HEAD: 53 `def test_` occurrences both sides, set of
unique names identical, zero deletions/renames. Per-node-ID classification of a fresh verbose
run: 43 `still_present_and_passing`, 10 `skipped_future_feature_pin`, 0 mismatches. (c) Full
suite: **1919 passed, 55 skipped, 11 warnings, 1240.80s** — reproduces F9 exactly, no deviation.

**Notes.** Containment mechanism precisely identified: `tests/test_draw_methods.py:50`'s
`_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and hasattr(imp, "_draw_stratum_col_for")` converts
a collection-time `AttributeError` (pre-2026-08-12: whole-suite abort) into a boolean driving
per-test `skipif`. The 43 traded-away tests were traded by the 2026-08-12 module-level-skip
commit (`a3bf4d9`, blanket-skipped all 53 tests in the file as a side effect of fixing
collection) and restored by the 2026-08-13 narrowing commit (`6aeebb0`); both independently
re-verified here via git history and a fresh test run rather than taken from the register's own
account. E-UTCI-12 remains open on the router-wiring gap alone (OPEN-17's scope). Item not
opened, closed, struck or retired by this task.

### CP-2 report (T06–T12), filed by this executor — 2026-08-19

T06–T12 executed in order, as dispatched. No STOP triggered — every task's premise held at HEAD
(rule 1); where a carried number did not reproduce (E02 `.eio` count, `open48_refleet3` totals,
OPEN-10's 90-building split is T16's finding, not this block's), the discrepancy was explained
with a timestamp or an upstream cause per rule 11, not smoothed over. No file under `openubem/`
was changed; no git write command was run; nothing under `%LOCALAPPDATA%/Temp/` was moved, copied
or deleted; no register item was opened, closed, struck or retired — every task's output is a
recommendation, filed in `extra/`.

**Headline findings this block adds, beyond reproducing what was asked:**

1. **A second, independent external sweep hit the E02 harvest today** (T06) — `.eio` files
   collapsed from 40,800 to 145 at a single timestamp, 2026-08-19 16:19, roughly two hours before
   this task ran, same signature class as the 2026-08-17 `.sql`/`.end` sweep already on OPEN-53's
   record. No published number depends on it; it reinforces the item's existing custody risk and
   closure condition rather than changing them.
2. **OPEN-14's gate is not the only blocker** (T07) — the register's config-gate framing is
   accurate as far as it goes, but `impute_missing()` (the only function that ever reaches
   `fusion.fuse()`) is called from exactly one place in the whole repository,
   `openubem/validation/mask_recover.py`, never from the production `enrich_semantics` path. A
   clean checkout needs the slice, a production routing change that does not exist at HEAD, and
   the gate opened — in that order — not the gate alone.
3. **OPEN-12's tracked-fleet numbers reproduce exactly on a different run than last measured**
   (T08) — run 4 instead of run 2 — including the zero-disagreement `data_quality_flag`
   cross-check and the previously-unnamed third 100%-cell (`nyc_suburban`).
4. **OPEN-16's `ml`-tier unreachability is structural, not incidental** (T11) — confirmed by
   `inspect.signature(enrich_semantics)`: the production entry point has no parameter through
   which any tier configuration could be threaded at all, and its own internal imputation calls
   are hard-coded to a different method (`kde`) at the literal level.
5. **OPEN-17's "never existed in any commit" claim survives a positive control** (T12) — the
   identical search method that returns empty for `_draw_tier` correctly finds `_ml_tier`'s real
   introduction two commits before HEAD, proving the absence is not a blind spot in the search.
6. **F9 reproduces exactly** (T09): 1,919 passed / 55 skipped, and the 43 tests OPEN-13's
   containment traded away in 2026-08-12 are independently confirmed still running today (restored
   2026-08-13), both by git history and by a fresh test run.

**Per §7, this executor stops here per the dispatch's own instruction** ("Execute T06 through T12
in order. Stop at the first checkpoint after T12."). Noted for the director: the plan document's
own §8 shows T01–T05 and T13–T20 already completed and logged by other concurrent executor
sessions, reaching as far as a CP-3 report already filed in this same log — this executor's
mandate was T06–T12 only and did not touch, re-derive, or audit that other work.

### ✅ CP-2 — AUDITED AND SIGNED 2026-08-19 (late), director

**Verdict: pass.** T06–T12 greenlit. Same audit standard as CP-1 and CP-3 (progress-log entries →
test output → only planned files touched → DESIGN citation for any unplanned decision).

**Artifacts.** Every claimed `extra/*.md` and `scripts/analysis/*.py` confirmed present, inside the
plan's §4 layout. Seven progress-log entries, one per task, all carrying Artifacts / Deviations /
Test status / Notes. No item opened, closed, struck or retired. No git write.

**Director's own re-verification — six of seven controls re-run directly rather than accepted.**
- **T09(a) re-run**: `pytest -q tests/test_draw_methods.py` → **43 passed, 10 skipped in 0.64s**,
  matching the executor exactly. The containment mechanism read at source: `hasattr()` at
  `tests/test_draw_methods.py:50` converts a collection-time `AttributeError` into a boolean, so
  the defect is scoped to per-test `skipif`, not fixed.
- **T09(b) — independent full-suite control, run by the director in a separate shell**: the
  executor's own background suite died when its session ended (the known executor-stall failure
  mode), so the director re-ran it independently. Result: **1919 passed, 55 skipped, 11 warnings in
  1115.22 s (0:18:35)**. **F9 reproduces exactly** — identical pass/skip counts to the executor's
  report and to the F9 anchor, from a wholly separate process. The 43 restored tests are inside
  that 1,919, not a population beside it.
- **T07 re-run**: `impute_missing()` has exactly **two** non-test production call sites repo-wide,
  both in `openubem/validation/mask_recover.py:330,338` — none on the `enrich_semantics` path. The
  executor's "one place in the whole repository" is correct at file granularity.
- **T11 re-run**: `inspect.signature(enrich_semantics)` confirmed — `(gdf, output_dir=None, *,
  load_mode=None, random_seed=None, construction_table=None, loads_table=None,
  schedules_table=None)`. No parameter can reach the `ml` tier. OPEN-16's unreachability is
  structural, as claimed.
- **T12's positive control re-run**: `_ml_tier` appears in 3 commits, `_draw_tier` in **zero** —
  the search method demonstrably finds a real introduction, so OPEN-17's absence is not a blind
  spot.
- **T06 re-counted**: E02 harvest holds **145 `.eio` against 40,800 `.err`**, reproducing the
  sweep's signature.

**🔴 The load-bearing consequence of the second sweep was checked directly, not inferred.** Run 4
(`open48_refleet4`) still holds its **8,160 `.eio` intact** — the sweep hit the E02 harvest tree
only. **The adopted fleet EUI denominator is untouched**: 153.8231 kWh/m² pooled (total simulated
energy ÷ total simulated floor area) over 8,153 successful buildings / 24,320,582 m² stands
unchanged, with its usual caveat that it is **not volume-correct** (OPEN-56's 10 m³ zone-volume
stub, ≈ +1.0 kWh/m²/building, is outside it; a volume-correct ≈154.8 is **not** adopted).

**Findings carried forward from this block.**
1. **OPEN-14 needs three things in order, not one** — the slice, a production routing change that
   does not exist at HEAD, then the gate. The register's config-gate framing understates it.
2. **OPEN-53's custody risk is now a repeat pattern, not an incident** — two independent external
   sweeps (2026-08-17 `.sql`/`.end`, 2026-08-19 16:19 `.eio`) on the same tree. This strengthens
   the item's existing closure condition; it does not change any published number.
3. **F9 is safe to quote** at 1,919 / 55, now on two independent runs the same day.

**Nothing in this block moves an adopted figure.** Every task's output is a recommendation filed in
`extra/`; the executor correctly opened no item and took no remedy.
