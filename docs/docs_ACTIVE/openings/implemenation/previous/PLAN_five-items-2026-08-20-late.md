# PLAN — five open items, 2026-08-20 (late)

**Slug:** `five-items-2026-08-20-late` · **Written:** 2026-08-20 · **Author:** manager (director) session
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` — book II, 21 live
items, next free `OPEN-62`. Book I (`INVESTIGATION_open-items-register.md`) is **closed** and remains
the authority on each live item's full history.
**Board:** `openings/reporting/board_open-items.html` · <https://claude.ai/code/artifact/7960a833-541b-4eab-a006-403c53c4bddc>
**DESIGN pointer:** none new. **Nothing is designed and nothing is built by this plan.** Every task
reads artifacts that already exist or re-simulates IDFs that already exist. No remedy is authorised
here for any item, and no item is opened, closed or retired by an executor.

**Why these five, in this order.** They are tasks 1, 1, 2 and two unblocked cheap ones from the
priority order published on the board: **OPEN-61** (twice — its mechanism, then its size), **OPEN-03**
(the 44 % wall question), **OPEN-12** (numbers that do not reproduce) and **OPEN-13** (the 43 tests
that were traded away). OPEN-35's remaining half is deliberately **not** here: it is a DESIGN
decision, not a measurement, and its measurement was made on 2026-08-20.

---

## 1. What the director established before writing this plan

These are **director controls run on 2026-08-20, not assumptions**, and they are what make the tasks
below feasible. An executor may re-verify any of them cheaply; none may be silently contradicted —
if your measurement disagrees with one of these, **stop and report the disagreement**.

| # | Fact | How it was established |
|---|---|---|
| D1 | **The run-4 fleet corpus has no results database left.** `evidence/open48_refleet4/` holds **8,160** `.eio`, **8,160** `.err`, **8,160** `.end` and **16,336** `.idf` — and **0** `.sql`. | `find evidence/open48_refleet4 -name '*.sql' \| wc -l` → `0` |
| D2 | **The production IDFs survive.** Every run-4 building keeps its IDF under `<cell>/fleet_staging/idfs/<osm_id>.idf`. | 413 IDFs in `austin_centre/fleet_staging/idfs`; `way_1008727470.idf` present |
| D3 | **48 untrimmed `layout_assign` results survive**, 4 buildings in each of the 12 cells, with `.sql`, `.idf` and `eplusout.expidf`. | `scratchpad/open03-untrimmed-sample/*/sim/*/` — 48 `.sql`, 48 `.idf` |
| D4 | **The district-heating term is real and it is the whole of the anomaly.** On `way_1008727470`, the `End Uses` table's `District Heating` column is **0.00 GJ on every row except `Water Systems` (0.72 GJ)**, and `Total End Uses` District Heating is the same 0.72 GJ. | direct `TabularDataWithStrings` query on that building's `.sql` |
| D5 | 🔴 **No IDF anywhere declares district heating.** The string `district` appears in **0 of 16,336** run-4 fleet IDFs and **0 of 48** sample IDFs, case-insensitive. **The energy is booked to that column by something the model never names.** | `grep -rli district --include=*.idf` on both corpora |
| D6 | **The service-water objects are identical in shape in both corpora**: one `WaterHeater:Mixed` (fuel `NaturalGas`, efficiency 0.808, ambient-zone-coupled), one `WaterUse:Equipment`, one `WaterUse:Connections`, and **zero `PlantLoop` objects**. | read from `eplusout.expidf` of `way_1008727470` and from the run-4 IDF `relation_13781131.idf` |
| D7 | **The parser's meter list is the omission.** `METER_QUERY` (`openubem/results/parser.py:42`) names `WaterSystems:NaturalGas` and `WaterSystems:Electricity` and no district meter; `dhw_kwh` is the sum of exactly those two (`parser.py:469`). | read at HEAD |

**The director's hypothesis, which T01 must TEST and not assume:** a `WaterUse:Equipment` /
`WaterUse:Connections` pair that is **not served by a plant loop** has its water-heating energy
booked by EnergyPlus to the **District Heating** column, because there is no modelled plant to
charge it to. If that is what is happening, then **OPEN-61 is structural and fleet-wide, not a
sample artifact** — and a second question opens behind it that this plan does not answer: whether
that energy is *additional to*, or *double-counting with*, the gas water heater that sits in the
same model. **Report which of the three it is. Do not decide what to do about it.**

---

## 2. Hard rules for the executor

1. **Local only.** No `ssh`, no `sbatch`, no `srun`, nothing that touches Speed. If a task looks
   like it needs the cluster, it does not — stop and report.
2. **No production code changes.** `openubem/`, `tests/`, `scripts/validation/` and `scripts/cluster/`
   are **read-only for this plan.** New analysis harnesses go in `scripts/analysis/` under the dated
   names given in §3. **End every task by running `git status --short` and pasting the output into
   your progress-log entry** — it must show only the files §3 authorises for your task.
3. **No item is opened, closed, struck, merged or retired by an executor.** If you find a new defect
   — and on this arc, tasks routinely do — **write it up in your report under a heading
   `CANDIDATE DEFECT`** with its mechanism and its evidence. **The director opens IDs.**
4. 🔴 **Never import or copy `open56_zone_volume_experiment.py`'s `run_ep()`.** It is **OPEN-58**: it
   lets EnergyPlus outputs cross-contaminate between buildings sharing a working directory, and it
   reads EUI by a formula that is not production's. Use `run_ep_isolated()`
   (`scripts/analysis/open35_storey_intervention_2026-08-19.py:95`), which gives every invocation its
   own `cwd`. **One working directory per building, always.**
5. 🔴 **Never pool per-cell results into a single headline number.** Report **within-cell** statistics
   and name the cell. This rule is not stylistic: on 2026-08-20 the storey intervention measured
   **+75 % in one cell and −3 % in another** — pooling would have produced one confident positive
   number and erased the only structurally interesting result in the set.
6. **Pre-register your controls.** Before you run anything, write down in your report what you expect
   each control to show. A control invented after seeing the answer is not a control.
7. **Quote real output.** Real error strings, real counts, real file paths. Never paraphrase an error
   and never report a number you did not see printed.
8. **Report what is missing from your own work**, not only what is in it. If a control did not run,
   say so; if a sample is smaller than the task asked for, say why. Silence has cost this arc more
   than error has.
9. **If the DESIGN or this plan is ambiguous, STOP and quote the conflict.** Do not invent, and do
   not propose an alternative plan.
10. **Append one progress-log entry per completed task to §8 of this file**, in the house format.
    Do not edit the register — the director does that.

---

## 3. File layout — what each task may create

| Task | Harness (new) | Output (new) | Report (new) |
|---|---|---|---|
| T01 | `scripts/analysis/open61_district_source_2026-08-20.py` | `openubem/outputs/comparisons/open61_district_source.csv` | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md` |
| T02 | `scripts/analysis/open61_production_sample_2026-08-20.py` | `openubem/outputs/comparisons/open61_production_sample.csv` + `..._selection.csv` | §T02 appended to the T01 report |
| T03 | `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` | `openubem/outputs/comparisons/open03_envelope_decomposition.csv` | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md` |
| T04 | `scripts/analysis/open12_height_residual_2026-08-20.py` | `openubem/outputs/comparisons/open12_height_residual.csv` | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md` |
| T05 | none — git and pytest only | `openubem/outputs/comparisons/open13_lost_tests.csv` | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md` |

Scratch work goes under `scratchpad/` and is **not** an artifact — nothing in `scratchpad/` may be
cited as evidence in a report. Figures, if any, go flat in `openubem/outputs/`, never under `docs/`.

---

## 4. Dependency decisions — pinned, do not change

- **Python 3.13**, invoked as `py -3` on this machine. Bare `python` is not on PATH.
- **EnergyPlus 23.1.0-87ed9199d4** — the version every artifact in this arc was produced with.
  If your run reports a different version, **stop**: the comparison is void.
- **pandas** for tabular work; **`sqlite3` from the standard library** for reading `.sql`. Do not add
  a dependency. Do not use `eppy` where a text read of the IDF will do.
- **Test suite baseline is `py -3 -m pytest -q tests/`** — a bare root-level run reports ~36 false
  failures and is not the baseline.
- **Parallelism:** at most **6** concurrent EnergyPlus processes (T02 only). Each gets its own
  working directory per hard rule 4.

---

## 5. Facts with citations the tasks depend on

- `METER_QUERY` — `openubem/results/parser.py:42`, meter names at `:48-54`.
- `dhw_kwh` is `WaterSystems:NaturalGas + WaterSystems:Electricity` — `openubem/results/parser.py:469`.
- `resolve_simulated_floor_area()` — `openubem/results/parser.py:362`; it is multiplier-aware, which
  is the asymmetry behind **OPEN-60**.
- `check_building_integrity()` — `openubem/results/parser.py:602`; it exists, and the fleet path that
  produced `05_results.csv` never calls it (**OPEN-60**'s sharp edge).
- `parse_building()` — `openubem/results/parser.py:716`, the production entry point. **Every EUI this
  plan quotes must come through it**, not through a formula written in the harness (**OPEN-58**(b)).
- `run_ep_isolated()` — `scripts/analysis/open35_storey_intervention_2026-08-19.py:95`.
- Adopted fleet figure: **153.8231 kWh/m² pooled over 8,153 buildings**, not volume-correct
  (**OPEN-56** ≈ +1.0 not included). **No task in this plan restates it.**

---

## 6. Tasks

### T01 — OPEN-61: where does the district-heating energy come from, and how big is it on 48 buildings?

**What.** Two things, in this order. **(a)** Establish mechanically what puts energy in the
`District Heating` column of a model that never declares district heating (fact D5). **(b)** Size the
term on all **48** surviving untrimmed results (fact D3) — the item is currently sized on **4**.

**Why.** The item's blast radius is recorded as *explicitly unmeasured*, and its remedy shape cannot
be chosen until the source is known: if the energy is an artifact of an unconnected water-use object,
"add the meter to the query" is not merely insufficient (D5 already proves that) — it may be the
wrong thing to want. n=4 → n=48 also puts twelve cells under the number instead of one.

**How.**
1. Read `eplusout.expidf` for a handful of the 48 and find every object that could produce
   service-water heating: `WaterUse:Equipment`, `WaterUse:Connections`, `WaterHeater:*`,
   `Coil:WaterHeating:*`, any `PlantLoop`. Record which exist and how they are (or are not) wired.
2. Test the hypothesis in §1 **directly**: take **one** building, make **one** copy of its IDF in a
   scratch directory, and change **only** what is needed to connect or disconnect the water-use
   object from the water heater. Re-run it with `run_ep_isolated()`. **If the District Heating term
   moves, the hypothesis is confirmed; if it does not, it is refuted and you report that.** This is
   the only IDF edit this plan authorises, it is in scratch, and it touches no repository file.
3. For all 48: read `Water Systems` and `Total End Uses` for **every fuel column** from
   `TabularDataWithStrings`, and read the same building's production total through
   `parse_building()`. Compute, per building: district-heating GJ, its share of `Total End Uses`,
   and the share of the parser's own total that is missing.
4. Report **per cell** — twelve cells, no pooled headline (hard rule 5).

**How to test.** Three controls, pre-registered:
- **C1** — on `way_1008727470`, your pipeline must reproduce **0.72 GJ** District Heating under Water
  Systems and **0.72 GJ** at Total End Uses (fact D4). If it does not, your reader is wrong, not D4.
- **C2** — for every one of the 48, the ABUPS `Total End Uses` summed across all fuel columns must
  agree with the sum of that building's individual end-use rows to within **0.5 %**. A building that
  fails C2 is excluded from the statistics and **named** in the report.
- **C3** — the count of buildings whose District Heating is exactly 0.00 GJ must be stated. If it is
  48, then D4's building is anomalous and the whole item changes shape — **stop and report that**
  rather than continuing to T02.

---

### T02 — OPEN-61: does the adopted fleet carry it, and how much? *(gated behind CP-1)*

**What.** Re-simulate a stratified sample of **60** production (`auto`) buildings from the surviving
run-4 IDFs — 5 per cell across all 12 cells — and measure the district-heating share on production
geometry and production configuration.

**Why.** This is the question the item is blocked on, and the reason it is blocked is that the run-4
`.sql` corpus was deleted on 2026-08-20 (fact D1). **The IDFs survived** (fact D2), so the answer
costs a re-simulation and not a rebuild — no input pipeline runs, no classification, no imputation,
nothing upstream can drift. T01 measures `layout_assign` buildings; **the adopted figure is `auto`**,
and the two modes have never been assumed interchangeable on this arc.

**How.**
1. Build the selection **first and freeze it**: 5 buildings per cell, drawn deterministically (sort
   by `osm_id`, take every *k*-th, seed nothing) so the selection is reproducible without a seed.
   Write it to `open61_production_sample_selection.csv` **before any simulation runs**.
2. For each: copy the run-4 IDF and the cell's EPW into a per-building working directory, run
   `run_ep_isolated()`, keep the `.sql`.
3. Read district heating exactly as in T01, and read the production total through `parse_building()`.
4. Report per cell. State the sampling frame explicitly: **60 of 8,160, stratified, not a census.**

**How to test.** Three controls, pre-registered:
- **C4 — the rig reproduces the record.** For each of the 60, your `parse_building()` total must
  match that building's `total_eui_kwh_m2` in `evidence/open48_refleet4/<cell>/results/05_results.csv`
  to within **1.5 %**. This is the control that proves you are measuring the change and not the rig.
  ⚠️ It cannot be tighter than the district term itself (~1 %), which is the very thing you are
  measuring — **state the residual distribution, do not just assert the pass.**
- **C5 — EnergyPlus version.** Print it from the `.err` of the first run. Anything other than
  **23.1.0-87ed9199d4** voids the comparison; stop.
- **C6 — no cross-contamination.** Hash two different buildings' `.sql`. Identical hashes mean you
  have reproduced OPEN-58 inside this task; stop and report.

---

### T03 — OPEN-03: why does `layout_assign` build 44 % less wall on the same floor plate?

**What.** Decompose the envelope of the **48** sample buildings against their own production (`auto`)
IDFs: gross wall area, roof area, ground-contact area, window area, window-to-wall ratio, exterior
surface area per unit floor area, and storey count — read from the IDF geometry, both arms, same
building.

**Why.** OPEN-03's central claim (a load-vintage disagreement) was **refuted** on 2026-08-20; ≈92 % of
the remaining cross-mode gap is attributed to envelope geometry, and the next question is
mechanical: *where* does the wall go. The two arms exist on disk for the same 48 buildings (facts D2,
D3), so this costs no simulation at all.

**How.**
1. Pair each sample building with its run-4 IDF by `osm_id`. **Report the pairing rate**; any
   building that does not pair is named and excluded.
2. Compute areas from the surface vertex lists in the IDF — sum polygon areas by
   `Surface Type` × `Outside Boundary Condition`. Do not use eppy; a text read is enough and leaves
   no dependency behind.
3. Produce per-building rows and **per-cell** medians of each ratio (`layout_assign` ÷ `auto`).
4. State plainly which term carries the gap: wall, roof, ground, glazing, or storey count.

**How to test.** Two controls, pre-registered:
- **C7 — floor area agrees.** The two arms' total floor area must agree to within **2 %** per
  building; a building where the plate itself differs cannot answer "same floor plate" and is
  excluded and named. **Report how many were excluded** — if it is most of them, the question as
  posed is unanswerable on this sample and that is the finding.
- **C8 — the 44 % reproduces, or it does not.** State the measured wall ratio against the carried
  44 %. **If it does not reproduce, that is the result** — this arc has retracted three carried
  figures already, and a fourth is not a failure of the task.

---

### T04 — OPEN-12: name the third cell and lock the replacement numbers

**What.** Re-derive the rural `height_m` residual across all 12 cells, name the third cell that sits
at 100 %, and write down the replacement figures that supersede the recorded 36.4 % and 19.2 %.

**Why.** The item's own recorded percentages **do not reproduce** — both come back at 100 % — and a
third cell is also at 100 % and has never been named in the register. An item whose published numbers
are known wrong and whose replacements are not written down cannot be closed, quoted, or scoped.

**How.**
1. Read `extra/MEASUREMENT_open-12_height-residual-retrace.md` **first** and state what it already
   settled; do not re-derive what is already recorded there.
2. Work from the persisted per-cell inputs in `evidence/open48_refleet4/<cell>/01_buildings.gpkg`
   (and `04_simulation_manifest.parquet` where the manifest carries the resolved value).
3. For all 12 cells report: n buildings, n missing `height_m` at source, n filled by each mechanism,
   and the residual share — **per cell, named, never pooled**.
4. State the fleet-wide count that replaces the carried "2,806 / 8,160".

**How to test.** Two controls, pre-registered:
- **C9** — your per-cell totals must sum to **8,160**; print the sum.
- **C10** — the three cells you report at 100 % must be named, and the two the register names
  (`nyc_rural`, `austin_rural`) must be among them or you must explain which one is not and why.

---

### T05 — OPEN-13: what were the 43 tests covering?

**What.** Identify the **43 passing tests** that were traded away when the outdoor-comfort defect was
contained on 2026-08-12, name them, and state what each group covered and whether that coverage
exists anywhere else in the suite today.

**Why.** The item is recorded as "1 of 2 fixed", and the containment's cost is recorded as a number
with no names under it. A coverage loss nobody can enumerate cannot be restored, and cannot be
argued to be acceptable either.

**How.**
1. Find the containing commit from the register's OPEN-13 section in **book I** and from
   `git log --oneline --since=2026-08-10 --until=2026-08-14 -- tests/`. Keep every command capped
   (`--stat`, `--name-only`, `| head -40`) — do not print diffs.
2. List the removed or skipped test node IDs. For skips, quote the skip reason string verbatim.
3. Group them by what they exercise and state, per group, whether an equivalent assertion survives
   elsewhere — by test name search, not by reading whole files.
4. Run the baseline suite once (`py -3 -m pytest -q tests/`) and report the counts.

**How to test.** Two controls, pre-registered:
- **C11** — the number you enumerate must be **43**. If it is not, report the number you actually
  find and where the 43 came from; **do not adjust your evidence to reach 43.**
- **C12** — the suite must still report its known baseline (**1,875 passed / 55 skipped**, or
  1,937 collected under the newer count — state which you got and against what command).

---

## 6b. CP-1 — SIGNED by the director, 2026-08-20

T01 landed and was audited: only the three §3-authorised files plus the obligatory debug-reference
edit were touched. **C3 did not fire the stop condition** (43/48 zero, 5/48 non-zero), so the plan
continues. T01's mechanism finding is **CONFIRMED**: deleting the orphan `WaterUse:Equipment` /
`WaterUse:Connections` pair from one scratch IDF moved District Heating **0.72 GJ → 0.00 GJ** while
Water Systems Natural Gas stayed bit-identical (11.68 → 11.68 GJ) — the term is **additional energy,
not a double count**, on that building.

**Three director controls run at CP-1, which change what T02 is for:**

| # | Fact | How it was established |
|---|---|---|
| D8 | **The discriminator is exact on all 48.** District Heating > 0 **iff** the IDF carries a `DHW_WaterUse_*` `WaterUse:Equipment` object **and** no `PlantLoop`. 5 of 5 non-zero match it; the other 11 no-plant-loop buildings carry **no** `WaterUse:Equipment` at all and are all zero; the remaining 32 carry a real wired plant loop and are all zero. **No exception in 48.** | text read of the 48 sample IDFs + `open61_district_source.csv` |
| D9 | 🔴 **Every production IDF matches the affected pattern.** Of the **16,336** run-4 IDFs: **16,336** carry `WaterUse:Connections`, **16,336** carry a `DHW_WaterUse_*` `WaterUse:Equipment`, and **0** carry a `PlantLoop`. | `grep -rli --include=*.idf` on `evidence/open48_refleet4` |
| D10 | Fact **D6 was true of the two buildings it was read from, but is not universal** — 32 of the 48 sample IDFs do carry a `PlantLoop` (`SWHSys1`, wired, with `Pump:ConstantSpeed`). The production corpus does not. **D6 stands only for production; it is corrected here for the sample.** | same census, both corpora |

🔴 **What this means for T02.** The question *"does the adopted fleet carry it"* is **no longer T02's
job — D9 answers it from text: the whole production corpus matches the pattern that was non-zero 5
times out of 5 and zero 43 times out of 43.** T02's remaining job is **sizing on production
geometry**: how large the term is, per cell, and therefore how much energy `total_eui_kwh_m2` is
missing. T02 gains one control:

- **C4b — the discriminator must hold on production.** All 60 re-simulated buildings should return a
  **non-zero** District Heating term. **If any comes back 0.00, D8's discriminator is broken** —
  stop, name the building, and report; do not adjust the discriminator to fit.

**T02, T03, T04 and T05 are released.** T03–T05 were held back until CP-1 in case it stopped the plan.

---

## 6c. CP-2 — SIGNED by the director, 2026-08-20

T02 and T03 landed and were audited. Both are clean on file scope. Two audit notes and two new
director controls follow.

**T02 audit — C4 is valid, and the executor's own caveat on it is over-cautious.** The harness builds
`manifest_row` from the building's `05_results.csv` row, but that row supplies only the *geometry
inputs* (`footprint_area_m2`, `levels`, `data_quality_flag`); the EUI itself is computed by
`parse_building()` from the **newly simulated** `.sql`. A machine-precision residual (median 3.1e-14 %)
therefore means the re-simulation reproduced run-4 **bit-identically** — same IDF, same EPW, same
EnergyPlus 23.1.0-87ed9199d4. That is a strong pass, not a tautology. **C4b: 60 of 60 non-zero — D8's
discriminator holds on production.** No cross-contamination (C6), no simulation failures.

**T02 left the bimodal split undiagnosed (43 low / 17 high, up to 89 kWh/m²). The director diagnosed
it, because it decides how far the adopted figure moves:**

| # | Fact | How it was established |
|---|---|---|
| D11 | 🔴 **The split is by archetype, and the term tracks service hot water.** **14 of the 17 high buildings are `MidriseApartment`**; the low group is `SmallOffice`-dominated (27 of 43). Medians: high `dh` **32.25** vs `dhw_eui` **34.08** kWh/m²; low `dh` **1.40** vs `dhw_eui` **3.34**. Over all 60 the ratio **dh ÷ dhw_eui** has median **0.714**, IQR **0.362–0.840**, max 1.004 — *the model spends roughly another half to full DHW load through the unreported channel.* | join of `open61_production_sample.csv` with each cell's `05_results.csv` |
| D12 | 🔴 **This is not a tail case: `MidriseApartment` is 2,818 of 8,160 buildings (34.5 %) of the fleet** (`SmallOffice` 3,497; `HighriseApartment`/hotels/restaurants/schools add ~200 more high-DHW buildings). | archetype census over all 12 `05_results.csv` |

**Fleet exposure — an ESTIMATE, explicitly not a measurement.** Applying the sampled `dh ÷ dhw_eui`
ratio to each of the 8,153 buildings' *recorded* `dhw_eui_kwh_m2` gives a fleet-mean unreported term
of **8.7 kWh/m² at the IQR floor (0.362), 17.2 at the median (0.714), 20.2 at the IQR ceiling (0.840)**
— i.e. roughly **6–13 % of the adopted 153.8**. Per-cell medians at the median ratio (hard rule 5, no
pooled headline): austin_centre 3.21 · austin_rural 2.74 · austin_suburban 2.47 · austin_urban 2.30 ·
la_centre 2.30 · la_rural 4.07 · **la_suburban 24.10** · **la_urban 22.56** · nyc_centre 2.71 ·
nyc_rural 5.12 · **nyc_suburban 30.88** · nyc_urban 2.88. ⚠️ **This transfers a ratio measured on 60
buildings (only 14 of them `MidriseApartment`) onto 8,153. It sizes the exposure; it does not settle
it.** A census-scale measurement is the obvious next arc and is **not** authorised by this plan.

**T03 audit — a fourth carried figure does not generalise, and the item's framing was wrong.** The
44 % wall deficit reproduces **only on the single building it was originally measured on**
(`nyc_centre/way_265424467`, 0.5606). Across the other seven cells with a valid pair the wall ratio
runs from **+57 % to −64 %** with no consistent sign. More important: **C7 excluded 40 of 48** — the
two arms do not build the same floor plate, and 28 of those exclusions are **storey-count driven**.
Where storeys do match (8 buildings), roof and ground ratios are exactly **1.0000** and only wall
moves. **So OPEN-03's real mechanism is a storey-count disagreement between `layout_assign` and
`auto`, not a wall-construction difference** — which is a different item from the one on the board.
T03 also found 2 of 48 `layout_assign` IDFs using Zone `Multiplier` > 1 against 0 of 48 `auto`, which
touches **OPEN-60**.

**T04 landed and was audited too** (12 rows, per-cell n sums to 8,160): the third 100 %-missing-height
cell is **`nyc_suburban`** (1,589 of 1,589); `nyc_rural` 198/198 and `austin_rural` 245/245 are also
100 %, so the register's 36.4 % and 19.2 % are both wrong and are superseded by 100.0000 %. The
fleet-level "2,806 / 8,160" and "3 cells, 2,032 buildings" already in the register are **confirmed
exactly**. Unrecorded neighbour: **`austin_centre` sits at 84.5 % (349/413)**.

**Only T05 remains before CP-3.**

---

## 6d. CP-3 — SIGNED, and the plan is CLOSED, 2026-08-20

T05 landed. All five tasks are complete, all five progress-log entries are in §8, and every task
touched only the files §3 authorised it to touch.

🔴 **T05's finding reverses the item.** The 43 tests were **never lost**. Nothing was deleted from
git: commit `a3bf4d95` (2026-08-12) *added* a module-level
`pytest.skip(allow_module_level=True)` to `tests/test_draw_methods.py` (`--stat` shows `13 +`, no
deletions), and the 2026-08-13 `_HAS_DRAW_TIER` narrowing restored them. **Director control, run
directly rather than dispatched:** `py -3 -m pytest -q tests/test_draw_methods.py` prints
**`43 passed, 10 skipped in 0.65s`** at HEAD today. Same node IDs, same file. **C11 = 43, matching
the register's number exactly — but the number was never a coverage loss.** The 10 that do remain
skipped all wait on the still-unimplemented `imputation._draw_tier` / `_draw_stratum_col_for`, which
is **OPEN-17**, not OPEN-13.

🟡 **The suite baseline has moved and the recorded one is stale.** C12 printed
**`1918 passed, 56 skipped, 892 warnings in 1443.51s (0:24:03)`**, exit 0, from
`py -3 -m pytest -q tests/`. Neither pre-registered figure (1,875/55, or 1,937 collected) is current.
The executor reported it as printed and did not adjust it, which is correct. **The 1,918/56 pair is
the baseline to carry forward.**

**Disposition the director takes from this plan — items are updated in book II, none is closed here:**

- **OPEN-61** — mechanism confirmed, discriminator exact on 108 buildings (48 + 60), fleet-wide on
  production, and **an order of magnitude larger than the item states**. Blast radius is no longer
  "unmeasured"; it is sized on 60 and estimated on 8,153 (D11, D12). **Stays open, re-scoped and
  raised in priority.**
- **OPEN-03** — the 44 % wall figure is retracted (reproduces on exactly one building, the one it was
  measured on). **The item's stated mechanism is wrong**; the live question is a storey-count
  disagreement between `layout_assign` and `auto`. **Stays open, re-framed.**
- **OPEN-12** — replacement figures locked (three cells at 100.0000 %, third cell named
  `nyc_suburban`); the fleet-level counts already in the register are confirmed exactly.
  **Ready to close on the director's next pass.**
- **OPEN-13** — the recorded coverage loss does not exist. **Ready to close**, with the residual
  10 skips reassigned to **OPEN-17**.

**Nothing further is authorised by this plan. It is closed.**

---

## 7. Stop-and-report points

- **CP-1 — after T01.** The director audits the mechanism finding before any simulation is spent.
  **T02 does not start until CP-1 is signed.** If T01's control **C3** shows all 48 at zero, or the
  hypothesis is refuted with no replacement mechanism, **the plan stops here** and the remaining
  tasks are re-scoped.
- **CP-2 — after T02 and T03.** The director audits the production sizing and the envelope
  decomposition together — they are the two tasks that can move how a published number is read.
- **CP-3 — after T04 and T05.** The director audits the two bookkeeping tasks and closes the plan.

At each checkpoint: **stop, append your progress-log entries, and report.** Do not continue past a
checkpoint on your own judgement.

---

## 8. Progress log

*(one entry per completed task, appended by the executor, in the house format:*
`#### TXX — <title> — completed YYYY-MM-DD` *followed by* **Artifacts** / **Deviations** /
**Test status** / **Notes**)*

#### T01 — OPEN-61: mechanism and 48-building sizing of the District Heating term — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open61_district_source_2026-08-20.py`
- `openubem/outputs/comparisons/open61_district_source.csv` (48 rows)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md`
- Scratch only (not artifacts, per §3): `scratchpad/open61_c2_experiment/{baseline,treated}/`
  (mechanism test IDFs + `.sql`)
- Debug reference registered: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` chapter 13,
  new bullet on `run_ep_isolated()` + relative paths.

**Deviations.** None from the plan's How. One implementation detail not specified by the plan:
`scripts/analysis/open35_storey_intervention_2026-08-19.py` has a hyphenated filename and cannot
be imported with a normal `import` statement; loaded via `importlib.util.spec_from_file_location`
to reuse `run_ep_isolated()` verbatim (not copied, not reimplemented) for the mechanism test.

**Test status.**
- C1: PASS — `way_1008727470` reproduced 0.72 GJ District Heating at both `Water Systems` and
  `Total End Uses`.
- C2: PASS on 48/48 — no building excluded.
- C3: **43/48 exactly 0.00 GJ; 5/48 non-zero.** Not 48 — plan's CP-1 stop-all-zero condition did
  not fire; proceeding to director review at CP-1 as scheduled.
- Mechanism test (single-building scratch IDF edit): CONFIRMED. Deleting the orphan
  `WaterUse:Equipment`/`WaterUse:Connections` pair on `way_1008727470` moved District Heating
  0.72 GJ → 0.00 GJ; Natural Gas (Water Systems) stayed bit-identical (11.68 → 11.68 GJ) —
  additional energy, not double-counting with the gas water heater, for this building.

**Notes.** `git status --short` at end of task:
```
 M docs/PROJECT_CHECKLIST.md
 M docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
 M docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md
 M docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md
 M docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html
 M docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md
 M docs/docs_ACTIVE/openings/reporting/board_published-numbers.html
 D scratchpad_open_s03_tagpoor_full.csv
 D scratchpad_open_s03_tagrich_full.csv
 D scripts/analysis/open_s03_build_pool_2026-08-20.py
?? docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md
?? docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md
?? docs/docs_ACTIVE/openings/reporting/board_open-items.html
?? docs/docs_EXPLANATION/OpenUBEM_debug_References.md
?? openubem/outputs/comparisons/open03_enduse_localisation.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
?? openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
?? openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
?? openubem/outputs/comparisons/open61_district_source.csv
?? openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv
?? scripts/analysis/open03_enduse_localisation_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_runs_2026-08-20.py
?? scripts/analysis/open53_evidence_verify_2026-08-20.py
?? scripts/analysis/open61_district_source_2026-08-20.py
?? scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
?? scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
?? tests/fixtures/labelled_archetypes_tagpoor_v3.csv
?? tests/fixtures/labelled_archetypes_tagrich_v3.csv
```
All files this task touched (§3-authorised three, plus the obligatory debug-reference edit) are
present in this listing; everything else pre-dates this session. **STOPPED at CP-1 as instructed —
T02 was not started.**

#### T04 — OPEN-12: named the third 100% cell and locked the replacement figures — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open12_height_residual_2026-08-20.py`
- `openubem/outputs/comparisons/open12_height_residual.csv` (12 rows, one per cell)
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md`

**Deviations.** None from the plan's How. `04_simulation_manifest.parquet` never carries a
resolved-height field in any of the 12 cells checked (columns are run-status only:
`osm_id, idf_path, work_dir, sql_path, status, n_warnings, n_severe, wall_clock_s, ep_version,
epw_path, error_summary, csv_path`) — the plan's conditional "where the manifest carries the
resolved value" does not apply anywhere in this corpus; reported as a finding, not treated as an
error.

**Test status.**
- C9: PASS — sum of per-cell `n` printed by the script is **8160**.
- C10: PASS — the three cells at 100% are `austin_rural`, `nyc_rural`, `nyc_suburban`. Both cells
  the register already names (`nyc_rural`, `austin_rural`) are among them; the third, previously
  unnamed, is **`nyc_suburban`** (n=1589, 1589 missing at source).
- Unplanned but load-bearing: the fleet-wide sum of `n_missing_height_m_source` across all 12
  cells is **2,806**, and 245+198+1589 = **2,032** — both exactly match the register's already-
  carried "3 cells, 2,032 buildings; 2,806/8,160 fleet-wide". Neither figure needed replacing;
  only the two per-cell percentages (36.4%, 19.2%) and the third cell's name were unresolved, and
  both are now locked: `nyc_rural` and `austin_rural` → 100.0000% each; third cell = `nyc_suburban`
  → 100.0000%.

**Notes.** No error was hit in this task; no debug-reference entry was added.
`git status --short` at end of task:
```
 M docs/PROJECT_CHECKLIST.md
 M docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
 M docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md
 M docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md
 M docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html
 M docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md
 M docs/docs_ACTIVE/openings/reporting/board_published-numbers.html
 D scratchpad_open_s03_tagpoor_full.csv
 D scratchpad_open_s03_tagrich_full.csv
 D scripts/analysis/open_s03_build_pool_2026-08-20.py
?? docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md
?? docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md
?? docs/docs_ACTIVE/openings/reporting/board_open-items.html
?? docs/docs_EXPLANATION/OpenUBEM_debug_References.md
?? openubem/outputs/comparisons/open03_enduse_localisation.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv
?? openubem/outputs/comparisons/open12_height_residual.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
?? openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
?? openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
?? openubem/outputs/comparisons/open61_district_source.csv
?? openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv
?? scripts/analysis/open03_enduse_localisation_2026-08-20.py
?? scripts/analysis/open12_height_residual_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_runs_2026-08-20.py
?? scripts/analysis/open53_evidence_verify_2026-08-20.py
?? scripts/analysis/open61_district_source_2026-08-20.py
?? scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
?? scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
?? tests/fixtures/labelled_archetypes_tagpoor_v3.csv
?? tests/fixtures/labelled_archetypes_tagrich_v3.csv
```
The three §3-authorised T04 files are present in this listing; everything else pre-dates this
task (other executors' concurrent work on this same plan, plus untouched pre-existing changes).
**Only T04 was executed — stopping here per instructions, awaiting CP-3 (T04 + T05 together).**

#### T02 — OPEN-61: sizing on 60 re-simulated production (`auto`) buildings — completed 2026-08-20

**Artifacts.**
- `scripts/analysis/open61_production_sample_2026-08-20.py`
- `openubem/outputs/comparisons/open61_production_sample_selection.csv` (60 rows, frozen before
  any simulation — `select` phase run and written before the `simulate` phase started)
- `openubem/outputs/comparisons/open61_production_sample.csv` (60 rows)
- `## T02` appended to `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md`

**Deviations.** One process deviation, not a plan deviation: the `simulate` phase was launched
with `run_in_background` and this session initially blocked on a `Monitor` watching for its
completion instead of continuing other work and polling the disk artifact itself — flagged live
by the director as a known failure mode on this project (a waiting agent is never woken). Fixed
mid-task: switched to a bounded `for`-loop polling the background output file every 15s, which is
what completed the wait. No plan-scoped deviation otherwise: selection method (sort by osm_id,
every k-th, k = n_idfs_in_cell // 5, no seed), `run_ep_isolated()` reused via
`importlib.util.spec_from_file_location` (not copied), 6 concurrent workers, one working directory
per building, all as specified.

**Test status.**
- C4: PASS 60/60 (≤1.5% tolerance). Residual distribution: min 0.0%, median 3.1e-14%, max
  2.2e-7% — machine-precision, because this harness's `manifest_row` and the record
  (`05_results.csv`) share the same source row; this proves rig fidelity, not that District
  Heating is small (it is not — see per-cell table in the report).
- C4b: PASS 60/60 non-zero. D8's discriminator (CP-1) holds on all 60 re-simulated production
  buildings; no break.
- C5: PASS. All 60 `.err` files report `EnergyPlus, Version 23.1.0-87ed9199d4`.
- C6: PASS. Two different buildings' `eplusout.sql` SHA-256 hashes differ
  (`5f9354a2...` vs `01d0ada1...`) — no OPEN-58 reproduction.
- 0 of 60 failed to simulate.

**Notes.** CANDIDATE DEFECT filed in the report: the 60-sample's district-heating term is
bimodal — 43/60 at 0.5–5.3 kWh/m² (matches T01's 48-sample range), 17/60 at 17.3–89.1 kWh/m²
(10–20x larger than anything T01 saw), present in 8 of 12 cells, and near-total in `la_suburban`
(5/5) and `la_urban` (4/5). Not diagnosed — flagged for the director. `git status --short` at end
of task:
```
 M docs/PROJECT_CHECKLIST.md
 M docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
 M docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md
 M docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md
 M docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html
 M docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md
 M docs/docs_ACTIVE/openings/reporting/board_published-numbers.html
 D scratchpad_open_s03_tagpoor_full.csv
 D scratchpad_open_s03_tagrich_full.csv
 D scripts/analysis/open_s03_build_pool_2026-08-20.py
?? docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md
?? docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md
?? docs/docs_ACTIVE/openings/reporting/board_open-items.html
?? docs/docs_EXPLANATION/OpenUBEM_debug_References.md
?? openubem/outputs/comparisons/open03_enduse_localisation.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv
?? openubem/outputs/comparisons/open03_envelope_decomposition.csv
?? openubem/outputs/comparisons/open12_height_residual.csv
?? openubem/outputs/comparisons/open13_lost_tests.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
?? openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
?? openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
?? openubem/outputs/comparisons/open61_district_source.csv
?? openubem/outputs/comparisons/open61_production_sample.csv
?? openubem/outputs/comparisons/open61_production_sample_selection.csv
?? openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv
?? scripts/analysis/open03_enduse_localisation_2026-08-20.py
?? scripts/analysis/open03_envelope_decomposition_2026-08-20.py
?? scripts/analysis/open12_height_residual_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_runs_2026-08-20.py
?? scripts/analysis/open53_evidence_verify_2026-08-20.py
?? scripts/analysis/open61_district_source_2026-08-20.py
?? scripts/analysis/open61_production_sample_2026-08-20.py
?? scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
?? scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
?? tests/fixtures/labelled_archetypes_tagpoor_v3.csv
?? tests/fixtures/labelled_archetypes_tagrich_v3.csv
```
All files this task touched (the two §3-authorised T02 harness/output files plus the
`open61_production_sample_selection.csv` output and the MEASUREMENT-doc append) are present in
this listing; everything else is other executors' concurrent work on this same plan (T03/T04/T05)
plus untouched pre-existing changes. **T02 complete, per §6b's redefinition (sizing only, D9
already answered "does production carry it").**

#### T03 — OPEN-03: envelope decomposition, 48 buildings, 12 cells — completed 2026-08-20

**Artifacts.** `scripts/analysis/open03_envelope_decomposition_2026-08-20.py`;
`openubem/outputs/comparisons/open03_envelope_decomposition.csv` (96 rows, 48 buildings x 2
arms); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md`.

**Deviations.** None from the task shape. Two bugs found and fixed *during* harness development
(before any number was reported): an object-boundary bug in the first parser draft let the last
`BUILDINGSURFACE:DETAILED`/`FENESTRATIONSURFACE:DETAILED` object per file pick up trailing
objects' vertices (fixed by splitting on blank lines, not on next-same-keyword); and a naive
"sum every floor-type surface" definition of total floor area double-counted buildings carrying
an unconditioned Attic zone (fixed using the IDF's own `Part of Total Floor Area` Zone field).
Both registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16. No eppy used, no
simulation run, no dependency added.

**Test status.** C7 (floor-area agreement within 2%): 40/48 excluded, 8 kept (one per cell
except `austin_suburban`, `austin_urban`, `la_rural`, `nyc_rural`, which have zero survivors) —
most excluded, so the question as posed ("same floor plate, different wall") is unanswerable on
most of this sample; the exclusions split into 12 borderline (5.26–5.67%, same storey count) and
28 large (25–200%, storey-count-driven) mismatches. C8: the carried 44% reproduces on
`nyc_centre/way_265424467` (0.5606, i.e. 43.9% less wall) *because that is the same building it
was measured on*; across the other 7 C7-surviving cells the wall ratio ranges +57% to −64% with
no consistent sign — the 44% is a single-building number, not a fleet or per-cell pattern (a
fourth carried figure that does not reproduce). Roof and ground-contact area ratios are exactly
1.0000 in all 8 C7-survivors; wall (and window riding under it) is the only envelope term that
moves once floor area is held fixed, but storey-count disagreement, not wall shape, is what
removes most of the 48 from a fair comparison in the first place. Full numbers, per-cell tables
and named exclusions are in the MEASUREMENT doc.

**Notes.** CANDIDATE DEFECT (not opened): `layout_assign` and `auto` assign different storey
counts to the same footprint on a large share of the 48 (28/48 by the C7 large-mismatch pattern,
median storey-count ratio 0.32–0.75 in 8 of 12 cells) — named example
`austin_centre/way_328649870`, 3 storeys vs. 1 storey on a bit-identical 735.05 m² footprint.
Distinct, previously unmeasured mechanism from OPEN-03's "44% less wall" framing; upstream of
wall shape and large enough to dominate any EUI comparison on affected buildings by itself.
Secondary, smaller: 2/48 `layout_assign` IDFs use Zone `Multiplier` > 1 to represent repeated
floors; 0/48 paired `auto` IDFs do.

`git status --short`:
```
 M docs/PROJECT_CHECKLIST.md
 M docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
 M docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md
 M docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md
 M docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html
 M docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md
 M docs/docs_ACTIVE/openings/reporting/board_published-numbers.html
 D scratchpad_open_s03_tagpoor_full.csv
 D scratchpad_open_s03_tagrich_full.csv
 D scripts/analysis/open_s03_build_pool_2026-08-20.py
?? docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md
?? docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md
?? docs/docs_ACTIVE/openings/reporting/board_open-items.html
?? docs/docs_EXPLANATION/OpenUBEM_debug_References.md
?? openubem/outputs/comparisons/open03_enduse_localisation.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv
?? openubem/outputs/comparisons/open03_envelope_decomposition.csv
?? openubem/outputs/comparisons/open12_height_residual.csv
?? openubem/outputs/comparisons/open13_lost_tests.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
?? openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
?? openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
?? openubem/outputs/comparisons/open61_district_source.csv
?? openubem/outputs/comparisons/open61_production_sample.csv
?? openubem/outputs/comparisons/open61_production_sample_selection.csv
?? openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv
?? scripts/analysis/open03_enduse_localisation_2026-08-20.py
?? scripts/analysis/open03_envelope_decomposition_2026-08-20.py
?? scripts/analysis/open12_height_residual_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_runs_2026-08-20.py
?? scripts/analysis/open53_evidence_verify_2026-08-20.py
?? scripts/analysis/open61_district_source_2026-08-20.py
?? scripts/analysis/open61_production_sample_2026-08-20.py
?? scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
?? scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
?? tests/fixtures/labelled_archetypes_tagpoor_v3.csv
?? tests/fixtures/labelled_archetypes_tagrich_v3.csv
```
All files this task touched (`scripts/analysis/open03_envelope_decomposition_2026-08-20.py`,
`openubem/outputs/comparisons/open03_envelope_decomposition.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md`, plus this
progress-log append and the `OpenUBEM_debug_References.md` §16 append) are present in this
listing; everything else is other executors' concurrent work on this same plan (T01/T02/T04/T05)
plus untouched pre-existing changes.

#### T05 — OPEN-13: what were the 43 tests covering? — completed 2026-08-20

**Artifacts.** `openubem/outputs/comparisons/open13_lost_tests.csv` (53 rows: every node ID in
`tests/test_draw_methods.py`, pass/skip status at HEAD, verbatim skip reason where applicable);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md`. No harness script — §3
authorises none for T05, and none was created. No production code, `tests/`, `scripts/validation/`
or `scripts/cluster/` file was changed.

**Containing commit.** `a3bf4d956e3ca207d6ecf660ae4ae33c77c3cfc1` — "docs/code: five-item openings
sweep, fusion fix for open-13, and placeholder trace analysis" (2026-08-12). `git show --stat`
confirms `tests/test_draw_methods.py | 13 +` — a module-level `pytest.skip(allow_module_level=True)`
was **inserted**, not a deletion; no `def test_` line was ever removed from git history in the
`--since=2026-08-10 --until=2026-08-14` window.

**C11.** 43, confirmed independently: `test_draw_methods.py` collects 53 tests; live
`py -3 -m pytest -q tests/test_draw_methods.py -rs` today prints `43 passed, 10 skipped in 0.76s`.
The 43 are named in the CSV. Matches the register's number, but book I's original 2026-08-12
provisional figures ("13 reference the draw-tier names", "43 passed, 9 failed") do not reproduce —
book I itself corrects this on 2026-08-18 to 10 skips, which is what was reproduced live here.

**Groups (all in `tests/test_draw_methods.py`) and survival, per §8 report:**
`TestDefaultByteIdentity` 4/6, `TestKDE` 9/9, `TestPMM` 6/6, `TestHotdeck` 5/5, `TestResid` 6/6,
`TestCatFreq` 7/7, `TestABB` 5/5 all pass with 0 skipped; `TestDrawTierRouting` 1/7 (6 skipped),
`TestNoEUILeakage` 0/1 (1 skipped), `TestDrawTierDeterminism` 0/1 (1 skipped) — the 8 skipped there
all need the still-unimplemented `imputation._draw_tier` / `_draw_stratum_col_for` (OPEN-17).
**For every one of the 43, identical coverage survives today** — same node ID, same file, passing —
because nothing was deleted; the 2026-08-13 `_HAS_DRAW_TIER` narrowing (already on record in book I)
restored collection and these 43 have been running since.

**C12.** `py -3 -m pytest -q tests/` → **`1918 passed, 56 skipped, 892 warnings in 1443.51s
(0:24:03)`**, exit 0. This does not match either pre-registered figure (1,875 passed/55 skipped, or
1,937 collected); 1918+56=1974 collected. Not adjusted to fit — reported as printed. The suite has
grown since the plan's baseline (concurrent T01–T04 work and other repo activity); reconciling the
full skip census is out of this task's scope per book I's own note.

**CANDIDATE DEFECT.** None found. This task enumerated and cross-checked only; it did not attempt to
reconcile the whole-suite 56-skip figure against `test_draw_methods.py`'s 10 (out of scope — book I
flags that reconciliation as a separate, undone full-suite task), and took no position on promoting
OPEN-17 (reserved to the user).

**Deviations.** Mid-task, after starting the baseline `pytest -q tests/` run in the background, this
executor stopped and handed control back to wait on it — a known bad pattern on this project (a
waiting agent is never woken). Corrected on resumption: polled the background output file directly
in a bounded loop (`tail -3` + process count, capped iterations, 15s interval) instead of blocking on
a monitor/notification, until the summary line appeared. No further such stalls occurred.

**Test status.** `py -3 -m pytest -q tests/` (the baseline command, not a bare root-level run) →
`1918 passed, 56 skipped` (see C12 above). No test file was modified or restored by this task.

**Notes.** Debug-references check performed before starting
(`grep -n -i "draw_tier" docs/docs_EXPLANATION/OpenUBEM_debug_References.md`) — the
`_draw_tier` AttributeError / collection-abort entry already exists at
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:838-844`; no new error was hit by this task, so
no new entry was appended.

`git status --short` at completion of T05:

```
 M docs/PROJECT_CHECKLIST.md
 M docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md
 M docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md
 M docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md
 M docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html
 M docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings.md
 M docs/docs_ACTIVE/openings/reporting/board_published-numbers.html
 D scratchpad_open_s03_tagpoor_full.csv
 D scratchpad_open_s03_tagrich_full.csv
 D scripts/analysis/open_s03_build_pool_2026-08-20.py
?? docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-12_third-cell.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md
?? docs/docs_ACTIVE/openings/extra/MEASUREMENT_s03_tagrich-v3-exam.md
?? docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md
?? docs/docs_ACTIVE/openings/reporting/board_open-items.html
?? docs/docs_EXPLANATION/OpenUBEM_debug_References.md
?? openubem/outputs/comparisons/open03_enduse_localisation.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_geometry.csv
?? openubem/outputs/comparisons/open03_enduse_localisation_pooled.csv
?? openubem/outputs/comparisons/open03_envelope_decomposition.csv
?? openubem/outputs/comparisons/open12_height_residual.csv
?? openubem/outputs/comparisons/open13_lost_tests.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv
?? openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv
?? openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv
?? openubem/outputs/comparisons/open53_evidence_verification_2026-08-20.csv
?? openubem/outputs/comparisons/open61_district_source.csv
?? openubem/outputs/comparisons/open61_production_sample.csv
?? openubem/outputs/comparisons/open61_production_sample_selection.csv
?? openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv
?? scripts/analysis/open03_enduse_localisation_2026-08-20.py
?? scripts/analysis/open03_envelope_decomposition_2026-08-20.py
?? scripts/analysis/open12_height_residual_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_2026-08-20.py
?? scripts/analysis/open35_storey_intervention_runs_2026-08-20.py
?? scripts/analysis/open53_evidence_verify_2026-08-20.py
?? scripts/analysis/open61_district_source_2026-08-20.py
?? scripts/analysis/open61_production_sample_2026-08-20.py
?? scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
?? scripts/analysis/open_s03_label_tagrich_v3_2026-08-20.py
?? tests/fixtures/labelled_archetypes_tagpoor_v3.csv
?? tests/fixtures/labelled_archetypes_tagrich_v3.csv
```

Only files this task's §3 authorises (`openubem/outputs/comparisons/open13_lost_tests.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-13_lost-coverage.md`) plus this progress-log
append are attributable to T05; everything else in the listing is other executors' concurrent work
on this same plan (T01–T04) or pre-existing changes untouched by this task.
