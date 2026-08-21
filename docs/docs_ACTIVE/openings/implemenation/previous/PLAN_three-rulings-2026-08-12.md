# PLAN — three rulings, executed (2026-08-12, night-2)

**Slug:** `three-rulings-2026-08-12`
**Date opened:** 2026-08-12
**Author:** director session (manager). Executors are fresh Sonnet sessions.
**Predecessor:** `PLAN_three-new-items-2026-08-12.md` (§10 close-out), which ended with four
rulings held for the user. Three were answered 2026-08-12 night-2. This plan executes them.
**DESIGN pointers:** `docs/docs_stepE/DESIGN_phase-E-service-loads.md` (elevator emitter);
`docs/docs_step3/DESIGN_step-3-semantic.md` §3C (17-rule classifier).
**Register:** `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md` — OPEN-45,
OPEN-47, OPEN-48. Next free ID **OPEN-49**.

---

## 1. What the user ruled

| Ruling | Item | Decision as given |
|---|---|---|
| **2f** | OPEN-45 | **Fix both remaining sites, then close.** |
| **2d** | OPEN-48 | **Restore the load wiring and re-run the fleet.** |
| **2e** | OPEN-47 | **Measure first, then decide** — add the floor-count condition behind a flag, count how many of the 8,160 buildings change archetype, report, do **not** adopt unilaterally. |

### 1.1 The sequencing consequence the user was told, and accepted implicitly

`assign_elevators` dispatches on `row["archetype_id"]`
(`openubem/idf/elevators.py:31-34` — `arch = str(row["archetype_id"])`, then
`_ELEV_DATA.get(arch)`, `return []` if absent). **Therefore any archetype reclassification
changes elevator eligibility.** Running the fleet for OPEN-48 before OPEN-47's measurement is
resolved would mean running it twice.

**So the fleet re-run (T04) is gated behind CP-1**, at which the user rules on whether to adopt
the floor-count condition. T01–T03 are unblocked and run now, in parallel.

### 1.2 The CP-1 ruling on OPEN-47 — **keep area-only, document the deviation** (2026-08-12)

T02 measured it: **598 of 8,160 buildings (7.3%) change archetype** under the source's full rule,
all promotions (SmallOffice→MediumOffice 380, SmallOffice→LargeOffice 57,
MediumOffice→LargeOffice 161), and **437 would newly gain elevator loads**.

**The provenance of the floor counts is what decided it.** Of the 598, only **85 (14.2%)** rest on
an observed floor count (`OSM_OBSERVED`); **346 (57.9%)** come from the height heuristic and
**167 (27.9%)** from a use-class group median carrying no building-specific signal. Among the 437
gaining elevators, **166 rest on that group median**.

🔴 **And the same imputed quantity already drives the tiering once.** The size metric is
`total_floor_area_m2 = footprint_area_m2 × max(levels_imputed, 1)`
(`building_classifier.py:205`). Adding an explicit floor-count bound makes the archetype depend
on the *same* imputed `levels` **twice** — once through the area product, once through the new
bound — and then propagates that into elevator eligibility.

**Ruling (user, 2026-08-12): adopt the area half only. The floor-count half is deferred, not
rejected.** The flag stays in the code, defaulting OFF, as the evidence for the decision.
**OPEN-47 closes as a documented, deliberate deviation** — reopenable the day floor-count
coverage improves. See T05.

**Consequence for T04: no archetype changes. The fleet re-run adds elevators and nothing else.**

---

## 2. Hard rules for the executor

1. 🔴 **Never run compute on the Speed login node.** `sbatch --array` only, fire-and-forget,
   then read the output file. Login node: `mkdir`, `scp`, `tar`, `squeue`, `sacct` only.
2. 🔴 **Remote login shell is tcsh.** Always use the `_ssh()` helper
   (`scripts/cluster/t08_harvest_results.py:104`), which wraps in `bash -lc`. Never send a bare
   command string. Keep `_ssh()` payloads under 7,500 chars.
3. 🔴 **Never run `git commit`, `git push`, `git checkout <branch>`, `git reset`,
   `git stash drop`.** Git is handled externally by the user. Read-only git is fine.
4. 🔴 **Never edit** root `main.py`, anything under `docs/docs_main/`, or any OVERVIEW / DESIGN
   doc.
5. 🔴 **No `.py` files under `docs/`, ever.** (The archived copies already there are read-only
   reference; do not add to them, do not edit them.)
6. 🔴 **Do not edit** the open-items register, the director prompt, the published-numbers board,
   or §9 of this plan. Those are the director's. You append to §8 only.
7. Progress logs are append-only. All figures go flat to `openubem/outputs/`.
8. Default to no code comments. Stop and ask on spec ambiguity; never invent.
9. **Report what you actually observed, not what you expected.** A "completed" claim is audited
   against raw artifacts by the director. If a check did not run, say it did not run.
10. 🔴 **Non-vacuity is mandatory.** Every assertion you add must be shown to fail when the
    condition it tests is absent. A check that silently matches nothing is worse than no check —
    this arc has already been bitten twice by exactly that.

---

## 3. File layout

| Path | Task | Action |
|---|---|---|
| `openubem/simulation/runner.py` | T01 | edit (~2 lines) |
| `tests/test_sim_integration.py` | T01 | edit (~2 lines) |
| `openubem/results/err_parse.py` | T01 | read-only — already exists, already tested |
| `openubem/semantic/building_classifier.py` | T02 | edit (flag-gated) |
| `scripts/analysis/open47_floorcount_reclass.py` | T02 | new |
| `openubem/outputs/comparisons/open47_floorcount_reclass.csv` | T02 | new artifact |
| `openubem/idf/builder.py` | T03 | edit (exactly 2 lines) |
| `scripts/validation/open48_elevator_ab.py` | T03 | new |
| `tests/test_builder_elevators_wired.py` | T03 | new |

---

## 4. Dependency decisions (pinned)

- **No new third-party dependencies.** Everything here uses what is already imported in the
  touched modules (`re`, `pandas`, `pathlib`).
- **T01 reuses `openubem/results/err_parse.py` as-is.** Do **not** write a fourth hand-rolled
  marker check. If `err_parse` lacks the helper you need, add it *there* with tests, do not
  inline a regex at the call site.
- **T02's floor-count condition is flag-gated and defaults OFF.** Default behaviour must be
  byte-identical to today. This is a measurement task, not an adoption task.
- **T03 restores exactly the two lines the archived copy has** — an import and a call. Nothing
  else. No refactor, no reordering of the service-load block.

---

## 5. Facts, with citations

1. **`err_parse` already exists and is tested.** `openubem/results/err_parse.py` exposes
   `SEVERE_RE`, `FATAL_RE`, `WARNING_RE`, `iter_severe`, `first_severe`, `count_severe`,
   `has_fatal`. `tests/test_err_parse.py` — 16 tests, director-verified `16 passed in 0.05s`.
2. **The real marker spelling, censused over all 64 `.err` files on this machine:**
   `** Warning **` one space both sides (4,881 lines); `** Severe  **` **one space before, two
   after** (37 lines); `**  Fatal  **` two both sides (1 line).
   🔴 **A literal written for "two spaces both sides" misses Severe exactly as badly as a
   one-space literal does.** This corrects a belief the project itself had been repeating.
3. **The two surviving OPEN-45 sites:**
   - `openubem/simulation/runner.py:140` — `if "**  Fatal  **" in line:` — happens to be
     correct for Fatal (2 spaces both sides) but is a fourth hand-rolled literal.
   - `tests/test_sim_integration.py:171` —
     `severe = [l for l in lines if "**  Severe  **" in l or "**  Fatal  **" in l]` —
     **matches 0 of the 37 real Severe lines.** This test currently reports clean on runs that
     had severe errors.
4. **The elevator wiring is two lines.** Archived copy
   `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/openubem/idf/builder.py`:
   - `:37` — `from openubem.idf.elevators import assign_elevators`
   - `:509` — `assign_elevators(self.idf, row, extruded_zones)`, immediately after
     `assign_refrigeration`, inside the `# 3H-svc: Phase-E physical service loads` block.
   Live `openubem/idf/builder.py` has that block at `:604-607` with `assign_refrigeration` last
   and **no elevator call**. Live imports are at `:36-41`.
5. **`git log --all -S assign_elevators -- openubem/idf/builder.py` is empty.** Commit `ef19141`
   added only the *archived* copies. The code that produced the adopted run was never committed.
6. **The reporting half is already restored and proven harmless.** `parser.py`
   (`_ELEVATOR_METER` at `:57`, guarded de-fold at `:346-349`), `outputs.py:43` (14th meter),
   `carbon.py`, `aggregator.py` `_STEP5_COLS`. Director-verified bit-identical on meter-absent
   inputs: `total_eui_kwh_m2` hex `0x1.d492d97e88c30p+7` before and after.
   🔴 **The de-fold is guarded — `if elevators_kwh:` — deliberately unlike the archived copy,
   which subtracts unconditionally. Do not "fix" this to match the archive.**
7. **Elevator energy is de-folded OUT of `equipment_eui_kwh_m2` into its own column, not folded
   into it.** Adopted CSVs: `elevators_eui_kwh_m2` non-zero on **3,561 of 8,160** rows,
   Σ = 12,508.8 kWh/m². 🔴 **Two independent checks — one executor's and the director's — read
   "absence" by looking at the equipment column, which a de-fold leaves flat. Check the
   invariant a transform preserves (the total), never the column it moves energy out of.**
8. **The office tier function is area-only.** `openubem/semantic/building_classifier.py:174-179`,
   `_office_size_tier(total_floor_area_m2)`; thresholds `_OFFICE_SMALL_MAX_M2 = 2322.0`,
   `_OFFICE_MEDIUM_MAX_M2 = 9290.0` at `:164-165`. The metric is
   `total_floor_area_m2 = area * max(levels_imputed, 1)` (`:205`), so levels enter only through
   the product, never as a separate condition.
9. **The source really does condition on floor count as well.** Chen, Hong & Piette (2017),
   *Applied Energy* 205, 323-335, Table 1 — director opened the PDF and read the table. The
   comment at `:159-163` is already corrected to name it. It is that project's working
   classification, **not a cited external standard.**
10. **Adopted baseline:** `phaseE_elevrb`, 12 cells, 8,160 buildings (8,154 success / 6 failed),
    fleet EUI **157.1 kWh/m² pooled** (`Σ(EUI×area)/Σ(area)` = 157.0552). `158.0` is superseded.

---

## 6. Tasks

### T01 — OPEN-45: fix the two surviving marker sites, then the item can close

**What.** Repoint `openubem/simulation/runner.py:140` and `tests/test_sim_integration.py:171` to
`openubem/results/err_parse.py`.

**Why.** The test site matches none of the 37 real Severe lines on this machine, so it reports
clean on runs that had severe errors. The runner site is correct today by luck of Fatal's
spelling, but it is a fourth independent literal and will drift.

**How.**
- `runner.py`: import from `openubem.results.err_parse` and replace the literal test. If you
  need a per-line fatal predicate, use `FATAL_RE.match(line)`; if a whole-text one reads better,
  `has_fatal(text)` already exists. Preserve the existing behaviour of taking the **first**
  matching line, stripped.
- `tests/test_sim_integration.py`: replace the list comprehension with `iter_severe(text)`
  plus the fatal lines, preserving the existing `" | ".join(...[:3])` shape.
- Grep the whole tree for any remaining `"** ` marker literal outside `err_parse.py` and report
  what you find. Do not edit anything you find outside the two files named here — report it.

**How to test.**
- `pytest tests/test_err_parse.py tests/test_sim_integration.py -q`.
- 🔴 **Non-vacuity, mandatory:** feed the new test path a real `.err` file from this machine
  that contains Severe lines, and show it returns a **non-empty** excerpt. Paste the excerpt.
  Then show the **old** literal returns empty on that same file. Both directions, both pasted.
- Full suite: `pytest -q`, report the count against the known baseline of 147 passing.

---

### T02 — OPEN-47: measure the floor-count condition, decide nothing

**What.** Add the source's floor-count condition to office tiering **behind a flag defaulting to
OFF**, then count how many of the 8,160 adopted-run buildings change archetype when it is ON.

**Why.** The user's ruling is *measure first*. If a handful of buildings move, area-only stays
and we write down why. If many move, the full rule is adopted — and that must happen **before**
the fleet re-run, because archetype drives elevator eligibility.

**How.**
- Extend `_office_size_tier` to accept the floor count and a `use_floor_count: bool = False`
  keyword. **Default OFF must be byte-identical to today** — prove it.
- The condition per Chen 2017 Table 1: a building qualifies for a smaller tier only if it
  satisfies **both** the area bound and the floor-count bound; exceeding either promotes it.
  🔴 **Read the thresholds off the source, not off this plan.** The PDF is the authority; if the
  table's floor bounds are ambiguous, **STOP and quote the ambiguity** rather than picking one.
- Write `scripts/analysis/open47_floorcount_reclass.py`: load the adopted-run inputs, classify
  each building both ways, emit
  `openubem/outputs/comparisons/open47_floorcount_reclass.csv` with one row per building whose
  archetype changes — `osm_id, cell, area_m2, levels, archetype_off, archetype_on`.
- Report, in the progress log: **how many buildings change, out of 8,160**; the breakdown by
  direction (Small→Medium, Medium→Large, …); **how many of the changed buildings gain or lose
  elevator eligibility** (cross-check against the archetype keys in
  `openubem/data/loads/elevators_by_archetype.json`); and the total floor area affected.

**How to test.**
- `pytest tests/test_building_classifier.py -q` — must be unchanged with the flag OFF.
- 🔴 **Non-vacuity:** exhibit at least one concrete building that changes tier with the flag ON,
  with its area and levels, and show by hand arithmetic why it changes. If **zero** buildings
  change, that is a legitimate result — but then you must exhibit a *synthetic* row that does
  change, to prove the flag is wired at all.
- **Do not adopt the flag. Do not change any default. Do not touch the fleet.**

---

### T03 — OPEN-48 part 1: restore the load wiring and quantify it on one cell

**What.** Add the two missing lines to `openubem/idf/builder.py`, then run a LIVE A/B on a
single cell to prove elevators appear and to measure the delta.

**Why.** The adopted run's results contain elevator energy the committed code cannot produce.
This restores reproducibility. The A/B sizes the effect before committing the fleet to a re-run.

**How.**
- Add `from openubem.idf.elevators import assign_elevators` to the import block at `:36-41`.
- Add `assign_elevators(self.idf, row, extruded_zones)` immediately after the
  `assign_refrigeration` call at `:607`, inside `# 3H-svc: Phase-E physical service loads`.
  **Exactly these two lines. Nothing else in this file.**
- Write `tests/test_builder_elevators_wired.py`: build one IDF for an elevator-eligible
  archetype and assert an `ELECTRICEQUIPMENT` object named `Elevators_<arch>` exists with
  `EndUse_Subcategory == "Elevators"`; and build one for an archetype absent from
  `elevators_by_archetype.json` and assert none is emitted.
- Write `scripts/validation/open48_elevator_ab.py` on the pattern of the archived
  `elevators_live_smoke.py` (arm B monkeypatches `assign_elevators` to a no-op). Run it on
  **one** cell. 🔴 **This is a real EnergyPlus run — `sbatch --array` on Speed, never the login
  node, never `srun`.** One cell only; the fleet is T04 and is gated.
- Report: buildings with non-zero `elevators_eui_kwh_m2`, the cell's pooled EUI in both arms,
  and the delta.

**How to test.**
- `pytest tests/test_builder_elevators_wired.py tests/test_elevators.py tests/test_parser_elevators.py -q`.
- 🔴 **Non-vacuity:** show arm B produces **zero** elevator energy and arm A produces non-zero,
  on the same cell. A delta of zero means the wiring did not take — investigate, do not report
  it as success.
- 🔴 **Regression guard:** confirm that on meter-absent inputs the parser is still bit-identical
  (§5 fact 6). Re-run whatever check establishes that and paste the hex.
- Full suite `pytest -q`.

---

### T05 — OPEN-47: write the deviation down, then the item closes

**What.** Record in the code that OpenUBEM implements the **area half** of Chen, Hong & Piette
(2017) Table 1 deliberately, and why the floor-count half is deferred. No behaviour change.

**Why.** The ruling in §1.2. A deviation that is written down is a decision; one that is not is an
accident. This item exists because the previous state of that comment credited a paper containing
neither threshold.

**How.**
- Extend the comment block at `openubem/semantic/building_classifier.py:159-172` to state: the
  source's rule conditions on floor count as well as area; OpenUBEM applies the area bound only;
  the reason is that **only 14.2% of the 598 affected floor counts are observed**, and the size
  metric already multiplies by the same imputed `levels`, so the bound would double-weight it;
  the flag `use_floor_count` remains available, default OFF; measured impact was 598/8,160 rows
  and 437 elevator-eligibility gains.
- Cite the artifact path `openubem/outputs/comparisons/open47_floorcount_reclass.csv`.
- 🔴 **Comment and docstring only. Do not change any default, any threshold, or any behaviour.**

**How to test.** `pytest tests/test_building_classifier.py -q` — expect **131 passed**, unchanged.
Confirm `git diff` shows comment lines only.

---

### T04 — OPEN-48 part 2: fleet re-run 🔒 **GATED — brief written 2026-08-12, unlocks at CP-1**

🔒 **Do not start this task until the director has signed CP-1 in §9 of this plan.** The brief
below is written in advance so it can be dispatched the moment T03's A/B is audited. **An
executor must not begin T04 on its own initiative, whatever T01–T03 return.** If §9 carries no
CP-1 signature, stop and say so.

**What.** Re-run all **12 cells** through the standard pipeline with the restored elevator
wiring in place, producing a complete new fleet, and report the new fleet EUI against the
adopted **157.1 kWh/m² pooled**.

**Why.** The user ruled *"restore the wiring, re-run the fleet"* (ruling 2d, §1). The adopted
`phaseE_elevrb` results contain elevator energy the committed code could not produce; T03 put the
two lines back. This run makes the published number reproducible from version control.

✅ **This is a single-variable change.** Per §1.2, the OPEN-47 ruling keeps office tiering
area-only, so **no archetype moves**. The only difference from the adopted run is the elevator
call in the builder. 🔴 **Any archetype difference in the T04 output is a bug, not an expected
consequence — stop and report it rather than explaining it.**

**How.**
- Driver: `scripts.validation.v12_cell_pipeline.run_cell(cell_name, output_subdir="open48_refleet")`
  for each of the 12 keys in `CELL_CONFIGS` (`nyc_centre`, `nyc_urban`, `nyc_suburban`,
  `nyc_rural`, `la_centre`, `la_urban`, `la_suburban`, `la_rural`, `austin_centre`,
  `austin_urban`, `austin_suburban`, `austin_rural`). Write a thin runner under
  `scripts/validation/`; **do not edit `v12_cell_pipeline.py`.**
- 🔴 **`run_cell` calls `poll_cluster`, which blocks for as long as the array runs.** A
  foreground call will hit the tool's 10-minute cap and a backgrounded agent task will never wake
  you. **Launch the runner as a detached process writing to a log file, then poll that log and
  `squeue` yourself.** Do not sit on a blocking call and do not background a monitor and wait for
  it — that failure has now killed executors on this arc four times.
- 🔴 **Compute is `sbatch --array` only** (`run_cell` already does this via
  `submit_cluster_array`). Never `srun`, never python on the login node.
- 🔴 **The REUSE trap.** `run_cell` skips ship/submit/poll entirely when
  `_remote_results_complete` finds every result already on the cluster
  (`v12_cell_pipeline.py:1005`), printing `REUSE: ... skipping ship/submit/poll`. Remote fleet
  dirs are keyed `"{output_subdir}_{cell_name}"`, so `open48_refleet` gets fresh dirs and this
  should not fire. **If you see `REUSED_REMOTE` for any cell, stop — it means you are reporting
  someone else's simulations, not yours.**
- 🔴 **Never cancel or requeue a job that is not yours.** Speed's `MaxJobCount` is 20002; submit
  in waves if the queue will not take the whole fleet.

**How to test / what to report.**
- **Provenance first:** the `git rev-parse HEAD` you ran at, plus confirmation from
  `git status --porcelain` that `openubem/idf/builder.py` carries T03's two lines. Paste both.
- Per-cell: buildings fetched, generated, simulated, succeeded/failed, and the SLURM job ID.
  **12 cells, expect ~8,160 buildings and 6 known failures** (5 `la_rural`, 1 `la_urban`).
- 🔴 **Non-vacuity:** count rows with `elevators_eui_kwh_m2 > 0` across the new fleet. **Zero
  means the wiring did not take.** State the count and Σ against the adopted run's **3,561 of
  8,160, Σ 12,508.8 kWh/m²** — a close match is the expected result and is the point of the task.
- **New fleet EUI, pooled**, computed with `scripts/analysis/open43_fleet_aggregations.py`
  (the reference implementation — do not hand-roll the aggregation), against **157.0552**.
  Report the difference in kWh/m² and in %.
- **Attribute the difference.** Give the per-cell deltas and say which cells move. If the new
  figure differs from 157.1 by more than the elevator column can explain, **say so plainly and
  stop** rather than adopting a new headline.
- 🔴 **Do not restate the published fleet EUI anywhere outside your progress-log entry.** The
  board, the register and the director prompt are the director's; adoption of any new headline is
  the user's ruling, not yours.

---

## 7. Stop-and-report points

- **CP-1 — after T01, T02 and T03 all report.** Director audits by re-deriving every headline
  from raw artifacts. Then two things go to the user: the T02 reclassification count with a
  recommendation, and the T03 measured delta. **The fleet re-run is authorised at CP-1, not
  before.**
- **CP-2 — after T04.** New fleet EUI against 157.1, with the difference attributed.

---

## 8. Progress log

*(Executors append here, one entry per completed task:
`#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)*

#### T01 — OPEN-45: fix the two surviving marker sites — completed 2026-08-12

**Artifacts.**
- `openubem/simulation/runner.py` — added `from openubem.results.err_parse import FATAL_RE`
  (after the `openubem.config` import); replaced the `"**  Fatal  **" in line` literal at the
  old line 140 with `FATAL_RE.match(line)`. Preserves the existing "first matching line,
  stripped" behaviour.
- `tests/test_sim_integration.py` — added
  `from openubem.results.err_parse import iter_severe, FATAL_RE`; replaced the list
  comprehension at the old line 171
  (`[l for l in lines if "**  Severe  **" in l or "**  Fatal  **" in l]`) with
  `iter_severe(text) + [l.strip() for l in text.splitlines() if FATAL_RE.match(l)]`, preserving
  the `" | ".join(...[:3])` shape immediately after.
- No other file touched. `git diff -- openubem/simulation/runner.py tests/test_sim_integration.py`
  shows exactly the two hunks above; `openubem/results/err_parse.py` was read-only, as required.

**Grep sweep for remaining marker literals (report only, per the task — nothing outside the two
named files was edited).** `rg '\*\*\s*(Severe|Fatal|Warning)\s*\*\*' --type py` (via Grep tool)
still hits 22 files besides `err_parse.py`:
- `tests/test_err_parse.py` — expected; these are the fixture strings that test `err_parse`
  itself.
- One archived, read-only file under `docs/docs_DONE/...` — out of scope by hard rule 5/CLAUDE.md
  (no edits under `docs/`).
- 19 one-off scripts under `scripts/analysis/`, `scripts/diagnostics/`, `scripts/validation/`
  (e.g. `a2_parse_results.py`, `a3_measure_band_deletion.py`, `open42_six_failures.py`,
  `open45_severe_literal_sweep.py`, `phaseE_cpb_fixtures.py`, `run_v11_step5.py`, six
  `v12_la_*`/`v12_nyc_*` recovery scripts, three `tX_*` diagnostics, `c01_storey_matching_regression.py`).
  None of these are `runner.py` or `test_sim_integration.py`; per the task instructions they were
  left untouched and are reported here, not fixed.

**Non-vacuity, both directions, real `.err` file on this machine
(`docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/b06_s1ref/b06_s1ref_SchoolSecondary.err`,
21 real Severe lines):**

NEW (`iter_severe`, the code the test now calls) — non-empty:
```
count: 21
'** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="CORNER_CLASS_1_POD_1_ZN_1_FLR_2" did not converge after 25 warmup days.'
'** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="MULT_CLASS_1_POD_1_ZN_1_FLR_2" did not converge after 25 warmup days.'
'** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="CORNER_CLASS_1_POD_2_ZN_1_FLR_2" did not converge after 25 warmup days.'
'** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="MULT_CLASS_1_POD_2_ZN_1_FLR_2" did not converge after 25 warmup days.'
'** Severe  ** CheckWarmupConvergence: Loads Initialization, Zone="CORNER_CLASS_1_POD_3_ZN_1_FLR_2" did not converge after 25 warmup days.'
```

OLD (the exact literal that lived at `tests/test_sim_integration.py:171` before this edit,
`"**  Severe  **" in l or "**  Fatal  **" in l`, two-spaces-both-sides) — empty on the same file:
```
count: 0
[]
```
This is the file's actual bug: the real marker is `** Severe  **` (one space before, two after),
so the old two-space-both-sides literal matched none of the 21 real lines and would have reported
this run clean.

**Test status.**
- `pytest tests/test_err_parse.py tests/test_sim_integration.py -q` → **23 passed** (16 +
  7), exit code 0. One caveat: stderr shows Windows `access violation` stack traces from
  `joblib`'s `loky`/`resource_tracker` process-spawn path inside `run_neighbourhood`
  (`openubem/simulation/parallel.py:271`, called from
  `test_synthetic_fleet_full_annual`). These are faulthandler dumps from joblib's Windows
  multiprocessing backend, not from any code this task touched (`err_parse`, `runner.py`
  marker check) and not test failures — pytest still reports 23 passed / 0 failed, exit 0.
  Flagging in case the director wants it tracked separately; not investigated further here as
  out of T01 scope.
- Full suite (`pytest -q`) — **UNVERIFIED, not a number I observed.** First attempt
  auto-backgrounded after the tool's 10-minute foreground cap, having reached only 57% of
  collection with several early `F`/`E` blocks in the 3%–25% range. Per the coordinator's
  explicit instruction not to wait on backgrounded pytest (it will not wake this session), I
  stopped that background task rather than let it run unobserved, and did not get a re-run to
  completion inside the available foreground time. The `F`/`E` failures seen in the partial
  output are in the 3%–39% range, well before this task's two files would collect/execute in
  suite order, and `git diff --stat` shows numerous other files already modified in the working
  tree outside T01's scope (`openubem/idf/builder.py`, `openubem/semantic/building_classifier.py`,
  `openubem/results/{parser,aggregator,carbon}.py`, `openubem/idf/outputs.py` — consistent with
  T02/T03 work in flight elsewhere on this same plan) — so those failures are very unlikely to be
  caused by this task's two-file edit, but I did not verify this by isolating them and I am not
  reporting a pass count I did not see to completion.
- Targeted files individually confirmed clean: `pytest tests/test_err_parse.py -q` → 16 passed
  in 0.05s (matches the plan's cited baseline).

**Deviations.**
- Could not produce the full-suite pass count against the 147-passing baseline; reported as
  unverified above rather than guessed.
- `runner.py`'s import was placed directly after `from openubem import config` (no existing
  import-block convention to match against for a first-party results import); no other deviation
  from the "How" in §6 T01.

**Notes.**
- The DESIGN was not ambiguous for this task; no stop-and-quote was needed.

---

#### T02 — OPEN-47: measure the floor-count condition, decide nothing — completed 2026-08-12

**Artifacts.**
- `openubem/semantic/building_classifier.py` — `_office_size_tier` extended with
  `levels: int | None = None` and `use_floor_count: bool = False`; threaded through
  `_apply_rule_table` (incl. the rule-15 recursive sub-evaluation call), `classify_building`,
  and `BuildingClassifier.__init__`/`.classify()` as `self.use_floor_count`, default `False`
  everywhere.
- `scripts/analysis/open47_floorcount_reclass.py` — new, measurement only.
- `openubem/outputs/comparisons/open47_floorcount_reclass.csv` — new, 598 rows
  (`osm_id, cell, area_m2, levels, archetype_off, archetype_on`).

**Thresholds, read directly off the PDF (not off the plan, the code comment, or memory).**
Opened `Chen, Hong & Piette (2017), Applied Energy 205, 323–335` (LBNL author manuscript,
DOI 10.1016/j.apenergy.2017.07.128) myself, PDF page 19–20, **Table 1 "Summary of the
selected 940 buildings in Northeast San Francisco"**:
- Small office: `<2322 m² AND ≤3 floors`
- Medium office*: `2322 to 9290 m² AND ≤5 floors`
- Large office: `>9290 m² OR ≥6 floors`
- Footnote (*): "the medium office building definition also includes buildings that are
  <2300 m² with four or five floors" — a small area-threshold slip in the source's own text
  (2300 vs. 2322), not an ambiguity in the floor bounds. Implemented by exclusion (Large
  first, then Small, else Medium) so the footnote's edge case falls into Medium automatically
  regardless of which of the two area numbers is used — did not stop on this, since the floor
  bounds themselves (≤3 / ≤5 / ≥6) are stated unambiguously and the exclusion construction
  makes the 2300-vs-2322 wrinkle immaterial.

**Non-vacuity, both directions, real buildings from the adopted-run fleet (hand-verified):**
- `way/99259744` (austin_centre): area=286.1 m², levels=5 → total floor area 1,430.6 m².
  OFF: <2322 → SmallOffice. ON: not >9290 and levels(5)<6 → not Large; area<2322 but
  levels(5)>3 → fails Small → Medium. **SmallOffice → MediumOffice.**
- `way/379165919` (austin_centre): area=683.0 m², levels=7 → total floor area 4,781.3 m².
  OFF: 2322≤4,781.3<9290 → MediumOffice. ON: levels(7)≥6 → **MediumOffice → LargeOffice**
  regardless of area.
- `way/379166276` (austin_centre): area=32.9 m², levels=6 → total floor area 197.1 m².
  OFF: <2322 → SmallOffice. ON: levels(6)≥6 → **SmallOffice → LargeOffice** even though the
  building is tiny — a real, if odd, consequence of the source's OR-on-floors clause.

**Headline measurement (8,160 adopted-run buildings, `phaseE_elevrb`, 12 cells).**
- 4,135 buildings are office-tier candidates (only `RULE_USE_CLASS_SIZE` and
  `FALLBACK_SIZE_DEFAULT` call `_office_size_tier`; checked from `archetype_source`, not
  inferred from `archetype_id`).
- **598 / 8,160 buildings (7.3%) change archetype** when the flag is ON.
  - SmallOffice → MediumOffice: 380
  - MediumOffice → LargeOffice: 161
  - SmallOffice → LargeOffice: 57
  - (all changes are promotions; the OR-structure of the source table never demotes)
- Elevator eligibility (cross-checked against `openubem/data/loads/elevators_by_archetype.json`;
  SmallOffice is not a key, MediumOffice and LargeOffice both are):
  - **437 buildings gain elevator eligibility** (SmallOffice, ineligible → Medium/Large, eligible)
  - 161 buildings change tier but eligibility is unchanged (Medium→Large, both already eligible)
  - 0 buildings lose eligibility
- Total floor area affected (changed rows only): **1,368,418.1 m²**, 5.81% of the fleet's total
  floor area (23,547,068.4 m², all 8,160 buildings).
- 16 / 8,160 rows could not be reproduced locally at all (recomputed OFF archetype disagrees
  with the adopted run's own archetype_id on a *different archetype family*, e.g. LargeOffice
  vs. MidriseApartment — not a tier shift; no overrides CSV exists in this repo to explain
  them). Excluded from the analysis above and reported here, not silently dropped.

**Recommendation (measurement only — not adopted, not acted on).** 7.3% of the fleet
reclassifies, 437 buildings newly become elevator-eligible, and 5.8% of total floor area is
touched. This is not a handful-of-buildings result; it is a fleet-scale reclassification
directly upstream of OPEN-48's elevator wiring. Flagging for the user's ruling at CP-1 rather
than recommending adoption or rejection myself.

**Deviations from the plan's literal wording (all disclosed, none silent).**
- **T02's "adopted-run inputs" are not queryable as such locally.** `phaseE_elevrb` on disk
  carries only `05_results.csv` (Step-5 output: footprint_area_m2, levels, archetype_id — no
  archetype_source, no function_tag/building_tag). It has no local Step-1/Step-2 artifacts.
  `phaseE` (the pre-elevator-restoration sibling run) does have `01_buildings.gpkg`, and its
  osm_id set is verified identical to `phaseE_elevrb`'s across all 12 cells (8,160 = 8,160).
  Used `phaseE/<cell>/01_buildings.gpkg` as the raw input, ran today's `BuildingClassifier`
  on it, and cross-checked every recomputed archetype against `phaseE_elevrb`'s actual
  `archetype_id` before trusting it (see the 16-row exclusion above) — this check is what
  makes the substitution safe rather than assumed.
- **`_office_size_tier`'s flag was threaded through the whole classifier pipeline**
  (`_apply_rule_table` → `classify_building` → `BuildingClassifier`), not left as a
  bare-function-only keyword. The plan's wording ("Extend `_office_size_tier` to accept the
  floor count and a `use_floor_count` keyword") could be read either way; threading it fully
  is what let the script call `BuildingClassifier(use_floor_count=True).classify()` end to
  end rather than re-implementing rule-12/17a routing by hand, and it is what let the
  byte-identical-default proof below exercise the real call path, not a stand-in.
- **The CSV's `levels` column is `levels_imputed`, not the raw upstream `levels`.** The
  classifier's own output preserves the raw upstream `levels` column unchanged by design
  (byte-equality invariant, DESIGN §4 line 302) — it is NOT the number the rule table used.
  Recomputed `levels_imputed` locally (same group-median lookup `BuildingClassifier` builds
  internally) so the CSV is interpretable. First version of the script emitted the raw
  (frequently NaN) column and silently under-summed the floor-area total via pandas'
  default `skipna=True` on `.sum()` — caught before reporting, not after.

**Test status.**
- `pytest tests/test_building_classifier.py -q` — **131 passed**, run twice (once before any
  edit, once after all T02 edits), same count both times.
- Default-OFF byte-identical to the pre-T02 code, proved directly (not just "tests still
  pass"): saved `git show HEAD:openubem/semantic/building_classifier.py` to scratchpad,
  loaded it as a separate module, ran its `BuildingClassifier().classify()` against the
  edited module's `BuildingClassifier().classify()` (default ctor, and again with
  `use_floor_count=False` explicit) on all 12 `phaseE` cells' real `01_buildings.gpkg`
  (8,160 buildings total) — `archetype_id` / `archetype_confidence` / `archetype_source`
  identical on every cell, every row.
- Full suite (`pytest -q`, all files): **attempted, not verified.** First foreground attempt
  hit the tool's timeout and was moved to background; its output file was still empty after
  repeated checks. Per the coordinator's direction, stopped waiting on the backgrounded run
  (a backgrounded task does not wake a waiting agent) rather than hang, and re-ran only the
  task-scoped file in the foreground instead — that is the check T02's own "How to test"
  section requires, and is the number reported above. Also note (from T01's entry above,
  observed independently): the working tree has T03 edits in flight concurrently
  (`openubem/idf/builder.py`, `openubem/results/{parser,aggregator,carbon}.py`,
  `openubem/idf/outputs.py`), so a full-suite run right now would be measuring a mid-edit
  tree, not this task in isolation, on top of not having completed. The all-files count is
  not reported because it was not seen.

**Notes.** Did not touch T01, T03, or T04. Did not adopt the flag, did not change any
default, did not touch the fleet, per the plan's explicit prohibition.

**Addendum — 2026-08-12, coordinator follow-up: levels-source breakdown.**

Provenance for the PDF itself confirmed by the coordinator (independent `pypdf` re-extraction
of Table 1, footnote included, verbatim match). One correction made per the coordinator's
explicit authorization: the code comment at `openubem/semantic/building_classifier.py:167`
now reads "manuscript pp.17-18" (was "p.18" — the Small-office row is on manuscript p.17,
the Medium/Large rows and footnote on p.18; both page numbers are correct for what they
each cite, but the comment only named one).

Added `levels_source` (the token `_impute_levels` itself returns — `OSM_OBSERVED`,
`HEURISTIC_HEIGHT`, `GROUPMEDIAN_LEVELS_MED`, `LEVELS_DEFAULT_LOW`) as a column in
`scripts/analysis/open47_floorcount_reclass.py` and regenerated
`openubem/outputs/comparisons/open47_floorcount_reclass.csv` (still 598 rows; column order
now `osm_id, cell, area_m2, levels, levels_source, archetype_off, archetype_on`). No other
number in the T02 entry above changed.

**levels_source breakdown, 598 changed buildings:**
- `HEURISTIC_HEIGHT`: 346 (57.9%)
- `GROUPMEDIAN_LEVELS_MED`: 167 (27.9%)
- `OSM_OBSERVED`: 85 (14.2%)
- `LEVELS_DEFAULT_LOW`: 0

**levels_source breakdown, 437 elevator-eligibility-gaining buildings:**
- `HEURISTIC_HEIGHT`: 208 (47.6%)
- `GROUPMEDIAN_LEVELS_MED`: 166 (38.0%)
- `OSM_OBSERVED`: 63 (14.4%)
- `LEVELS_DEFAULT_LOW`: 0

Reading: only ~14% of both the changed set and the elevator-gaining set rest on an
OSM-observed floor count. The remaining ~86% is imputed — the majority (`HEURISTIC_HEIGHT`)
from `height_m / floor_to_floor_m`, and a large minority (`GROUPMEDIAN_LEVELS_MED`) from a
use-class group median with no building-specific signal at all. `LEVELS_DEFAULT_LOW`
(flat default of 1) never fires here because rows defaulted to 1 floor cannot reach the
`>=6` or even `>3` floor bounds this rule promotes on, so they mechanically cannot appear in
a "changed" set — this is a structural fact about the rule, not evidence that
`LEVELS_DEFAULT_LOW` rows are trustworthy elsewhere. Reported as measurement only; no
recommendation on adoption is implied by this addendum beyond what is stated in the
Recommendation paragraph above (unchanged).

**Test status (addendum).** `pytest tests/test_building_classifier.py -q` re-run after the
comment-only fix: 131 passed, unchanged.

---

#### T05 — OPEN-47: write the deviation down, then the item closes — completed 2026-08-12

**Artifacts.**
- `openubem/semantic/building_classifier.py` — extended the comment block immediately
  following the `_OFFICE_SMALL_MAX_M2` / `_OFFICE_MEDIUM_MAX_M2` bins and the existing
  OPEN-47 T02 comment (currently the block ending `_OFFICE_LARGE_MIN_LEVELS = 6`). Added
  text states: the source's rule conditions on floor count as well as area; OpenUBEM
  applies the area bound only by default; the reason (only 14.2% of the 598 affected floor
  counts are `OSM_OBSERVED`, and `total_floor_area_m2` already multiplies by the same
  imputed `levels`, so an explicit floor-count bound would double-weight it); `use_floor_count`
  remains available, default OFF, as the evidence for the decision, not a deprecated path;
  measured impact restated (598/8,160 archetype changes, 7.3%, all promotions with the
  SmallOffice→MediumOffice 380 / MediumOffice→LargeOffice 161 / SmallOffice→LargeOffice 57
  breakdown, 437 elevator-eligibility gains). Cites
  `openubem/outputs/comparisons/open47_floorcount_reclass.csv` and the T02 progress-log
  entry in this plan.
- No other file touched.

**Deviations.** None from §6 T05's "How". No default, threshold, or behaviour changed —
only comment lines were added; `_OFFICE_SMALL_MAX_LEVELS = 3` and
`_OFFICE_LARGE_MIN_LEVELS = 6` (pre-existing from T02) are unchanged in place.

**Test status.**
- `git diff -- openubem/semantic/building_classifier.py` reviewed by hand: the file already
  carried T02's uncommitted code changes (the `use_floor_count` threading) before this task
  started, so the whole-file diff against `HEAD` is not comment-only. Isolated to just this
  task's own edit (the `Edit` tool's before/after strings): every added line is a `#` comment
  or a blank line; the two pre-existing assignment lines
  (`_OFFICE_SMALL_MAX_LEVELS = 3`, `_OFFICE_LARGE_MIN_LEVELS = 6`) were carried through
  unchanged, not modified. No executable line was added or altered by this task.
- `pytest tests/test_building_classifier.py -q` → **131 passed**, run in the foreground,
  matches the expected baseline exactly.

**Notes.** Did not touch the register, the director prompt, the board, or §9 of this plan.
Did not touch any other file.

---

#### T03 — OPEN-48 part 1: restore the load wiring and quantify it on one cell — completed 2026-08-12

**Artifacts.**
- `openubem/idf/builder.py` — exactly the two lines §6 T03 specifies, verified by
  `git diff -- openubem/idf/builder.py`: `+from openubem.idf.elevators import assign_elevators`
  in the import block, and `+        assign_elevators(self.idf, row, extruded_zones)`
  immediately after `assign_refrigeration` in the `# 3I` service-load block. Nothing else in
  the file.
- `tests/test_builder_elevators_wired.py` — new, untracked.
- `scripts/validation/open48_elevator_ab.py` — new, untracked; `submit` / `harvest` interface.
- Cluster: `sbatch --array` on Speed, cell `austin_urban`, 425 tasks per arm, `%32` concurrency.
  **Arm A job `1222996` — 425/425 `COMPLETED`. Arm B job `1223029` — 425/425 `COMPLETED`.**
  Zero failed tasks in either arm (`sacct -X -j 1222996,1223029`). No login-node compute.
- Harvested to `%TEMP%\ubem_open48_ab\austin_urban\`: `parsed_A.parquet`, `parsed_B.parquet`
  (425 rows each, `parse_status == success` on all 850), `ab_result.json`, and the raw
  `sim_out_A/` `sim_out_B/` trees (1,275 files each = 425 x 3).

**Result — measured, then re-derived by the director from the parquets, not from the script's
own summary.**

| Quantity | Arm A (wiring ON) | Arm B (wiring OFF) |
|---|---|---|
| Buildings parsed | 425 | 425 |
| Buildings with non-zero `elevators_eui_kwh_m2` | **56** | **0** |
| Sum of `elevators_eui_kwh_m2` | 255.2512 | 0.0000 |
| Pooled cell EUI, `Sum(EUI x area)/Sum(area)` | **250.6512** | **244.5245** |

**Delta A - B = +6.1267 kWh/m2 = +2.5056%.**

✅ **Non-vacuity satisfied:** arm B is **exactly zero** on every one of 425 buildings and
arm A is non-zero on 56. The wiring took.

✅ **Single-variable confirmed:** `archetype_id` and `floor_area_m2` are identical
building-for-building across the two arms (checked, not assumed). The arms differ only in
whether `assign_elevators` ran.

**Area-weighted decomposition of the +6.1267:**

| End use | Delta A - B (kWh/m2) |
|---|---|
| `elevators_eui_kwh_m2` | +4.8684 |
| `cooling_eui_kwh_m2` | +0.6655 |
| `fans_eui_kwh_m2` | +0.5970 |
| `pumps_eui_kwh_m2` | +0.1660 |
| `heating_eui_kwh_m2` | -0.1694 |
| `lighting_eui_kwh_m2` | +0.0000 |
| `equipment_eui_kwh_m2` | -0.0000 |
| **`total_eui_kwh_m2`** | **+6.1267** |

Reading: **4.8684 of the 6.1267 is the elevator electricity itself; the remaining 1.2583 is
the HVAC response to elevator waste heat** — cooling, fans and pumps up, heating down, in a
cooling-dominated Austin cell. That is the physically expected sign pattern in all four terms.
Lighting and equipment move by exactly zero, so the change did not leak into any unrelated
end use.

**Test status.**
- `pytest tests/test_builder_elevators_wired.py tests/test_elevators.py tests/test_parser_elevators.py -q`
  -> **38 passed in 5.56s**, foreground.
- 🔴 **Regression guard — run on live data, and stronger than the recorded check.** The
  §5 fact-6 hex `0x1.d492d97e88c30p+7` came from a one-off harness whose manifest row was not
  preserved, so that single number is not reproducible as stated. The guard it stands for was
  re-run instead on **arm B's own 425 SQL files, which are genuinely meter-absent**: `HEAD`'s
  `openubem/results/parser.py` loaded side-by-side with the working-tree parser, same manifest
  row, same SQL, every shared float key compared as `float.hex()`.
  **425 / 425 buildings, 13 shared float keys each, BIT-IDENTICAL on every one.** The only
  difference is the added key `elevators_eui_kwh_m2`, reading `0.0` on all 425.
  `✅ The guarded de-fold does nothing when the meter is absent` is therefore now
  established on 425 real buildings rather than on one file.
- Full suite `pytest -q`: **not run.** The working tree carries in-flight edits across 15
  source files from T01/T02/T05 and this task, so a full-suite number now would measure the
  mid-arc tree, not T03.

**Deviations.**
1. The §5 fact-6 hex was not reproduced verbatim (harness not preserved). Substituted a live
   425-building bit-identity gate, recorded above. **The recorded hex should be treated as an
   un-reproducible artifact of a deleted harness, not as a standing invariant.**
2. Full `pytest -q` not run, for the reason given.

**Notes.** This entry was written by the director, not by an executor: T03's first executor
died before submitting anything, and its replacement backgrounded the harvest and stopped
before reading it. The harvest process survived the agent that launched it and completed on
its own; every number above was then computed by the director directly from
`parsed_A.parquet` / `parsed_B.parquet`. Did not touch T04. Did not touch the register, either
board, or the director prompt from inside this task.

**Provenance.** `git rev-parse HEAD` = `a3bf4d956e3ca207d6ecf660ae4ae33c77c3cfc1`, working tree
dirty (T01/T02/T03/T05 edits uncommitted, as expected mid-arc).

---

#### T04 — OPEN-48 part 2: fleet re-run — opened 2026-08-12 19:31, **completed 2026-08-13 12:47** (running record)

*Written by the director. This entry is the running record of the re-run as it happened; the
completion record is the section **"T04 — fleet complete, and the confirmatory repeat"** further
down (all twelve cells, pooled 159.2157, and the confirmatory repeat closed at both the IDF and
the results stage). No number below is a published number, and the adopted headline remains
**157.1 kWh/m² pooled** until the user rules.*

**Execution shape — deviation from the brief, and why.**

The brief did not prescribe an execution driver. The first one used,
`scripts/validation/open48_fleet_rerun.py`, loops the twelve cells **sequentially**, calling
`run_cell(cell, output_subdir="open48_refleet")` one after another. Cell 1 (`nyc_centre`)
started 19:31 and finished the results stage around 22:00 — **~2 h 20 min of wall clock for
738 buildings.** At that pace the fleet is more than a day.

The cost is not cluster time. Inside `run_cell`, Step 3 IDF generation is
`n_jobs=1` serial (`scripts/validation/v12_cell_pipeline.py:210-212`); for `nyc_centre` that
alone is ~26 min of single-core local work, and it happens **before** anything is shipped to
Speed. The array itself (`sbatch --array=1-738%32`, job `1223987`) is a small fraction. So the
sequential driver leaves both the local machine (20 cores, one in use) and Speed (idle between
cells) mostly empty. The queue looking empty was a symptom of that serialization, **not**
evidence that the run was being done locally instead of on the cluster — every one of the 738
`nyc_centre` simulations ran on Speed under `sbatch`, as the brief requires.

Replacement driver: **`scripts/validation/open48_fleet_rerun_parallel.py`** (new file).
It runs the eleven remaining cells **six at a time**, each in its own process with its own
log, staggered 180 s apart to avoid an SSH burst against `speed-submit2`. It calls the same
`run_cell` with the same `output_subdir`; **`v12_cell_pipeline.py` is not modified**, per §2.
Six concurrent cells occupy six of twenty local cores, and each cell still submits its own
array capped at `%32` on Speed, so neither the fair-share cap nor the login-node rule is
touched. Logs and a live `STATUS.txt` in `%TEMP%\open48_par\`.

**Kill point was clean.** The sequential runner (PIDs 5124, 13584) was stopped after
`nyc_centre` completed and while `nyc_urban` was still in local IDF generation. Checked before
killing: the only `open48_refleet_*` directories on Speed were `nyc_centre`'s, and the queue
was empty — so `nyc_urban` had shipped nothing, and the discarded work is locally regenerable.
`run_cell`'s step-1/step-2/EPW caches are preserved, so the restart does not re-fetch.

**Fleet-integrity precondition — checked, holds.** Per-cell building counts from the re-run so
far match the adopted `phaseE_elevrb` run exactly (`nyc_centre` 738, `nyc_urban` 1,779 fetched),
against adopted totals austin_centre 413 · austin_rural 245 · austin_suburban 437 ·
austin_urban 425 · la_centre 226 · la_rural 149 · la_suburban 1,343 · la_urban 618 ·
nyc_centre 738 · nyc_rural 198 · nyc_suburban 1,589 · nyc_urban 1,779 = **8,160**. The
comparison therefore stays single-variable on the building set.

**Cell 1 result — `nyc_centre`, complete.**

| quantity | value |
|---|---|
| buildings fetched | 738 (probe lower bound 619) |
| generated | 738 / 738 |
| simulated | 738 / 738 |
| SLURM job | `1223987` (+ repair `1224873`, reroute `1224878`) |
| `REUSED_REMOTE` | none |
| rows with `elevators_eui_kwh_m2 > 0` | **338 of 738** |
| Σ `elevators_eui_kwh_m2` | **1,757.7** |

🔴 **The non-vacuity control passes on cell 1:** 338 non-zero rows and a positive sum mean the
restored `assign_elevators` wiring reached the cluster and is present in the harvested results.
Under the sequential driver this was the trap most likely to fire silently.

**Not yet done, and deliberately not attempted on partial data.** Fleet pooled EUI against
`157.0552`; the fleet non-zero count against the adopted `3,561 of 8,160, Σ 12,508.8`;
per-cell delta attribution; the archetype-invariance check. A pooled figure computed on a
subset of cells is not comparable to a fleet figure and would be misleading, so none is
recorded here. **One correction to guard against repeating it:** an early quick recompute of
`nyc_centre` weighted by `footprint_area_m2` alone is **not** comparable to `157.0552` — the
adopted arithmetic in `scripts/analysis/open43_fleet_aggregations.py` weights by
`footprint_area_m2 × levels.clip(lower=1)`. The final number must come from that script's
arithmetic, not a hand-rolled one.

**Cell 2 — `nyc_rural`, complete (22:38).** 198 fetched, 198/198 generated, 198/198 simulated,
SLURM job `1224965`, no `REUSED_REMOTE`, `simulation_status` = `success` on all 198.
**27 of 198 rows carry `elevators_eui_kwh_m2 > 0`, Σ 97.1.** Wall clock 4 min — small cell,
empty queue, 21.5 s IDF generation. Running fleet tally: **2 of 12 cells, 936 buildings, 365
with elevator energy.**

**🔴 First failure — `la_rural`, rc=1 at 22:47, and it is the predicted SSH failure.**
It passed both LIVE_SMOKE gates (149/149 generated, 0 unknown archetypes), probed the remote
directory (`0/149 complete`, so no reuse), and then died **shipping** the fleet:

```
Connection closed by 132.205.2.12 port 22
subprocess.CalledProcessError: Command '['scp', ...fleet.lst',
  'o_iseri@speed.encs.concordia.ca:/speed-scratch/o_iseri/fleets/open48_refleet_la_rural/fleet.lst']'
  returned non-zero exit status 255
```
(`v12_cell_pipeline.py:267`, called from `:1012`.)

This is the risk the 180 s stagger was meant to bound, and the stagger is evidently not enough
when six cells reach their ship stage near each other — `sshd` drops connections above its
unauthenticated-connection limit. 🔴 **It is a transport failure, not a modelling failure:
nothing was simulated, nothing partial was written, and the remote probe had already reported
`0/149`, so there is no stale-results hazard on retry.** Local work is cheap to redo (45.8 s of
IDF generation) because `run_cell`'s step-1/step-2/EPW caches survive. **Disposition: leave the
pool running and re-run every rc=1 cell afterwards at low concurrency.** No cell may be counted
as delivered on an rc=1; a missing cell would silently bias a pooled fleet figure.

**Cell 3 — `nyc_suburban`, complete (23:00).** 1,589 fetched (probe lower bound 1,313),
1,589/1,589 generated, 1,589/1,589 simulated, SLURM job `1224999`, no `REUSED_REMOTE`,
`simulation_status` = `success` on all 1,589 — matching the adopted count for this cell exactly.
**980 of 1,589 rows carry `elevators_eui_kwh_m2 > 0`, Σ 3,095.7.** Wall clock 29 min. Running
tally: **3 of 12 cells, 2,525 buildings, 1,345 with elevator energy, Σ 4,950.5.**

**🔴 Second failure — `austin_urban`, rc=1 at 23:20. Same cause, different call site.**
This one got further: it generated, shipped, and **submitted** its array (`1228045`), then died
in the *poll*:

```
subprocess.TimeoutExpired: Command '['ssh', 'o_iseri@speed.encs.concordia.ca',
  "bash -lc 'squeue -j 1228045 --noheader 2>/dev/null | wc -l'"]' timed out after 60 seconds
```
(`v12_cell_pipeline.py:112`, `_ssh`, 60 s timeout.)

Both failures are the same underlying condition — **six concurrent cells saturate the SSH link
to `speed-submit2`**, one dying on `scp` and one on a `squeue` poll. Neither is a modelling
failure and neither is a cluster-capacity failure.

**Orphan handling — an array was left running with nobody to harvest it.** When a cell's local
driver dies after `sbatch`, its array survives; `1228045` was still `PENDING` (verified with
`sacct -X -j 1228045`, so **nothing had simulated yet**). Two consequences were dealt with:
it would have burned queue time producing results no process would collect, and it would have
left a *complete* remote directory that the retry's completeness probe would read as reusable —
tripping the §9 `REUSED_REMOTE` trap and forcing a judgment call in the middle of the run.
**Action: `scancel 1228045` (our own job, orphaned, nothing yet run).** The retry will re-ship
and re-simulate from scratch, so `austin_urban` stays as clean as every other cell.
🔴 **Retry rule adopted for the rest of T04: before re-running a failed cell, confirm no orphan
array of ours survives for it, and prefer a fresh simulation over a reused remote directory —
the queue time is minutes and the provenance question is not worth it.**

**Cell 4 — `nyc_urban`, complete (23:57).** 1,779 fetched, 1,779/1,779 simulated, SLURM job
`1225386`, no `REUSED_REMOTE`, all `success`. **87 of 1,779 rows carry
`elevators_eui_kwh_m2 > 0`, Σ 314.0.** Wall clock 89 min.

---

### 🔴🔴 T04 interim finding — **the success criterion in §9 point 2 is wrong, and the data says so**

With four cells on disk the comparison against the adopted `phaseE_elevrb` run can be made
properly, and the result is not the one §9 predicted:

| cell | adopted pooled EUI | re-run pooled EUI | delta | archetypes | elevator rows (adopted → re-run) |
|---|---|---|---|---|---|
| `nyc_rural` | 234.9031 | 234.9031 | **−0.0000** | identical | 27 / 97.1 → 27 / 97.1 |
| `nyc_suburban` | 198.5571 | 198.5571 | **+0.0000** | identical | 980 / 3,095.7 → 980 / 3,095.7 |
| `nyc_urban` | 152.2766 | 152.2766 | **−0.0000** | identical | 87 / 314.0 → 87 / 314.0 |
| `nyc_centre` | 168.1111 | 171.6455 | **+3.5344 (+2.10%)** | **5 differ** | 338 / 1,757.3 → 338 / 1,757.7 |

(Pooled with the adopted arithmetic: `footprint_area_m2 × levels.clip(lower=1)` weights over
`simulation_status == "success"`.)

🔴 **Three of four cells reproduce the adopted run exactly — and that is the correct outcome,
not a failure.** §9 point 2 says *"the new fleet EUI must exceed 157.0552… zero or negative
means the wiring did not reach the cluster."* **That criterion conflates two different
comparisons and must not be used to judge T04:**

- **T03's +2.5056%** was *restored wiring* versus *repo `HEAD` with the wiring missing*. That
  is a comparison against the **broken repository**, and it is the number that proves the
  two-line `builder.py` fix works.
- **T04** is *restored wiring* versus the **adopted `phaseE_elevrb` run** — and the adopted run
  **already contains elevator energy**. That was settled by the OPEN-46 reversal: 3,561 of
  8,160 adopted buildings carry it, Σ 12,508.8. OPEN-48's complaint was never that the adopted
  numbers lacked elevators; it was that **the repository could no longer regenerate them.**

**So the target for T04 is reproduction, and the expected fleet delta is ≈ 0, not > 0.** A
large positive fleet delta would now be the alarming result, because it would mean the re-run
is not reproducing the run we published. 🔴 **The non-vacuity control is not the delta — it is
the elevator column itself,** and it passes decisively: the re-run's per-cell elevator counts
and sums match the adopted run's building-for-building (27/27, 980/980, 87/87, 338/338).
Adopted per-cell reference, re-derived here for the remaining comparison: austin_centre
127 / 592.5 · austin_rural 26 / 96.9 · austin_suburban 8 / 22.0 · austin_urban 56 / 249.5 ·
la_centre 91 / 432.2 · la_rural 17 / 56.5 · la_suburban 1,288 / 4,068.0 · la_urban 516 / 1,727.2
· nyc_centre 338 / 1,757.3 · nyc_rural 27 / 97.1 · nyc_suburban 980 / 3,095.7 · nyc_urban
87 / 314.0 — **total 3,561 of 8,154 successful rows, Σ 12,508.9**, which reconciles with the
adopted figure of 3,561 / Σ 12,508.8 quoted in the brief. Adopted success counts also confirm
the 6 known failures (8,160 rows, 8,154 success: la_rural 5, la_urban 1).

**🔴 `nyc_centre` is the one cell that does not reproduce, and it is not yet explained.**
73 of its 738 buildings differ in `total_eui_kwh_m2`, with deltas from **−361.0 to +321.2**
(median 0, mean +10.1), and 5 buildings change archetype (4 `Courthouse` → `OpenUBEMUnknown`,
1 `MidriseApartment` → `MediumOffice`) — which is the §9 point-1 trap firing. What has been
ruled out, by direct comparison of the two runs' results and manifests:

- **Geometry is identical** — `footprint_area_m2`, `levels`, `height_m` differ on **0** of 738.
- **Weather is identical** — same EPW basename on all 738
  (`USA_NY_New.York-Central.Park.Obs-Belvedere.Castle.725053_TMYx.2011-2025.epw`); the
  `epw_path` column differs only in its temp-directory prefix.
- **EnergyPlus version is identical** — `23.1.0` in both.
- **`n_severe` is identical building-for-building** (differs on 0), so no building failed in one
  run and not the other.
- **The code was not changing under the run.** All touched sources were last modified 17:38–17:59
  (`builder.py` 17:38:58, `building_classifier.py` 17:59:34, `parser.py` 17:00:58); `nyc_centre`
  started 19:31 and the other cells started after 22:28. **Every cell ran against the same tree.**

What is suggestive: the 73 differing buildings are **enriched in severe errors** (mean `n_severe`
0.41 versus 0.10 for the 665 that reproduce), they are the complex tall archetypes
(`SuperTallBuilding`, `TallBuilding`, `LargeOffice`, `LargeHotel`), and `n_warnings` differs on
34 of them. That pattern points at **run-to-run instability in buildings that already error**,
not at the elevator change — but it is a hypothesis, not a finding.

**Disposition — do not resolve this by argument.** `nyc_centre` will be re-run a second time
under the identical tree, and the decisive question is which pair matches:
- **run-2 ≈ run-1, both ≠ adopted** → the difference is in the *inputs or the adopted artifact*
  (e.g. an OSM tag snapshot that drifted, which would also explain the 5 archetype moves),
  and the adopted `nyc_centre` is the outlier, not our re-run.
- **run-2 ≈ adopted, ≠ run-1** → run-1 is the outlier and the cause is nondeterminism in the
  severe-error subset.
- **run-2 ≠ both** → the cell is genuinely nondeterministic and no single re-run reproduces it.

Run-1's `05_results.csv` and `04_simulation_manifest.parquet` have been copied aside to the
session scratchpad (`nyc_centre_run1/`) so the re-run cannot destroy the evidence.
🔴 **No fleet figure will be reported until this is settled**, because `nyc_centre` is 738 of
8,160 buildings and a +3.53 kWh/m² cell error is not negligible at fleet scale.

---

### 🔴 Second non-reproducing cell — `austin_centre` — and the pattern it reveals

`austin_centre` (00:48) also fails to reproduce: **168.7719 adopted → 170.5338 re-run,
+1.7618 (+1.04%)**, 69 of 413 buildings differing, **3 archetype moves** (2 `SmallHotel` →
`LargeHotel`, 1 `MidriseApartment` → `LargeOffice`). Elevator *count* still matches exactly
(127 = 127) but the *sum* moves, 592.5 → 604.3.

**This kills the severe-error hypothesis.** In `austin_centre` `n_severe` is **0 for every
building in both runs**, and it differs on none — yet 17% of the cell still moves. Whatever is
happening does not require a failing simulation.

**The pattern across eight cells is by density, not by size:**

| cell | delta | buildings differing |
|---|---|---|
| `nyc_centre` | **+3.5344** | 73 / 738 |
| `austin_centre` | **+1.7618** | 69 / 413 |
| `nyc_urban` | −0.0000 | 17 / 1,779 |
| `la_suburban` | −0.0000 | 4 / 1,343 |
| `austin_suburban` | 0.0000 | 4 / 437 |
| `nyc_rural`, `nyc_suburban`, `austin_rural` | 0.0000 | 0 |

🔴 **Both non-reproducing cells are `*_centre` cells — the dense downtown ones.** A third,
`la_centre`, is still running; **it is a live prediction that it will deviate too**, and it
should be checked first when it lands.

> **✅ Prediction confirmed at 01:15.** `la_centre` deviates: **132.8885 → 134.4862, +1.5978
> (+1.20%)**, archetypes differ, 24 of 226 buildings moved, elevator count identical (91 = 91)
> with the sum moving 432.2 → 447.2. The prediction was written down before the cell landed, so
> this is a test the hypothesis could have failed and did not.
>
> **⚠️ But the "centre only" framing is wrong, and `la_urban` (01:17) is the counter-example:**
> **130.0032 → 131.2175, +1.2142 (+0.93%)**, archetypes differ, 15 of 617 buildings moved. It is
> not a `*_centre` cell. 🔴 **The correct statement of the pattern is not about the cell's name
> but about a single observable: `archetype_id` inequality.** Across eleven cells, **every cell
> whose archetypes differ also moves in EUI, and every cell whose archetypes match reproduces to
> ±0.07 or better.** The split is exact, with no cell on the wrong side of it:
>
> | archetypes differ → cell moves | archetypes match → cell reproduces |
> |---|---|
> | `nyc_centre` +3.5344 · `austin_centre` +1.7618 · `la_centre` +1.5978 · `la_urban` +1.2142 | `nyc_rural` · `nyc_suburban` · `nyc_urban` · `la_suburban` · `la_rural` (+0.0657) · `austin_rural` · `austin_suburban` |
>
> Density is a correlate of that split, not the split itself — the four moving cells are simply
> where classification changed. **Anything that explains the archetype differences explains the
> EUI differences; nothing else needs explaining.**

By archetype, the concentration is sharp: **every `OpenUBEMUnknown` building differs in both
centre cells (37/37 in `austin_centre`, 31/31 in `nyc_centre`)**, along with 75% of
`SuperTallBuilding` and 50% of `TallBuilding` in `austin_centre`. But the rule is not clean —
`nyc_urban` has 228 `OpenUBEMUnknown` buildings and only 10 of them differ — so this is a
correlation to explain, not the explanation.

**Ruled out so far, across both cells:** geometry (footprint/levels/height differ on 0 of 738 in
`nyc_centre`, 1 of 413 in `austin_centre`), weather (same EPW file), EnergyPlus version (23.1.0
both), severe-error counts (identical building-for-building), and any change to the source tree
during the run. **`iod` was checked and eliminated as a cause** — it is an overheating metric
computed *from* the simulation output (`openubem/results/parser.py:385`), so its movement is a
symptom of the same difference, not a driver of it.

**What this means for the deliverable.** EnergyPlus is deterministic given an identical IDF and
EPW, so buildings that differ must have received **different IDFs** — which points at model
*generation*, not simulation.

---

### 🔴🔴 CAUSE FOUND — the IDFs were compared directly, and the mechanism is in the code

The adopted run's IDFs are still on Speed (`/speed-scratch/o_iseri/fleets/elev_rebaseline_nyc_centre/idfs`,
738 files) alongside the re-run's (`open48_refleet_nyc_centre/idfs`). Diffing them building-by-
building settles it. **All five files compared have identical line counts; only their contents move.**

| building | in-run behaviour | differing lines | what differs |
|---|---|---|---|
| `relation/1860567` | EUI identical | **6** | *only* the order of three `Output:Meter` key names |
| `relation/3565283` | EUI identical | **6** | same — meter ordering only |
| `way/265320169` | **−361.0 kWh/m²** | **506** | **window vertex Z-coordinates** |
| `way/266149299` | **+321.2 kWh/m²** | **378** | window vertex Z-coordinates |
| `relation/11171765` | reclassified | **140** | window geometry + archetype-driven content |

🔴 **The buildings that reproduce differ only cosmetically.** Their sole difference is that
`Elevators:InteriorEquipment:Electricity`, `InteriorLights:Electricity` and
`InteriorEquipment:Electricity` are emitted in a different order in the `Output:Meter` block —
no energy consequence, and incidentally a direct confirmation that **the elevator meter is
present in both runs**.

🔴 **The buildings that move differ in window geometry.** The diffs are runs of `Vertex N
Zcoordinate` values — e.g. `2.2441895576770805` → `2.355865987895366`, a shifted window head
and sill on every fenestration surface. Different window area means different solar gain and
different envelope loss, which is exactly the size and the sign-symmetry of the observed
±300 kWh/m² swings.

**Window geometry comes from `wwr`,** applied at `openubem/idf/builder.py:246`
(`idf.set_wwr(wwr=float(row["wwr"]), …, force=True)`), and for `OpenUBEMUnknown` buildings
`wwr` is **drawn at random**:

```python
# openubem/semantic/__init__.py:211-232  (_build_unknown_loads, "F13")
pde_cols = ["lighting_w_m2", "equipment_w_m2", "occupant_m2_per_person", "wwr"]
n = unk_mask.sum()
for col in pde_cols:
    lo, hi = real_loads[col].min(), real_loads[col].max()
    vals = rng.uniform(lo, hi, size=n)
```

Two properties of that block make the whole cell fragile, and **one shared generator ties them
together** — `openubem/semantic/__init__.py:297`, `rng = np.random.default_rng(random_seed)`,
commented **"F14: one RNG per run"**, consumed in sequence by `_build_unknown_envelope` (:321),
`_build_unknown_loads` (:340), a noise term (:367) and a KDE resample (:372):

1. **The draw is a single vectorised block sized `n` = the number of Unknown buildings.** Change
   `n` and *every* Unknown building in the cell receives a different `wwr`, not just the new one.
2. **The bounds are `real_loads[col].min()/.max()` over the archetypes actually present.**
   Reclassify one building *between two known archetypes* and the bounds can move, which
   re-randomises the entire Unknown cohort even when `n` is unchanged.

**This predicts the observed split exactly, and the cohort counts confirm both halves:**

| cell | Unknown count adopted → re-run | archetypes | cell moves |
|---|---|---|---|
| `nyc_centre` | 31 → **35** (+4) | differ | **yes** — mechanism 1 |
| `austin_centre` | 37 → 37 | differ | **yes** — mechanism 2 |
| `la_centre` | 15 → 15 | differ | **yes** — mechanism 2 |
| `la_urban` | 2 → 2 | differ | **yes** — mechanism 2 |
| `nyc_suburban` | 290 → 290 | identical | no |
| `nyc_urban` | 228 → 228 | identical | no |
| `austin_suburban` · `austin_rural` · `nyc_rural` · `la_suburban` | unchanged | identical | no |

`nyc_centre`'s +4 is precisely its 4 `Courthouse` → `OpenUBEMUnknown` moves, and it is the only
cell where `n` changed — which is why it also has the largest delta (+3.53) and the only cell
where **100% of Unknown buildings** moved (31/31, and 37/37 in `austin_centre` by mechanism 2).

**🔴 The finding, stated plainly: a single reclassified building silently re-randomises the
window-to-wall ratio of every `OpenUBEMUnknown` building in the same neighbourhood.** The run is
reproducible only while the inputs never move; under any classification drift the "unchanged"
buildings change too. That is a reproducibility defect in its own right, and it is larger in
consequence than the missing elevator wiring OPEN-48 was opened for. **It should be registered
as a new item (next free ID OPEN-49) and ruled on by the user.**

**Why the classification drifted at all is a separate and still-open question.** The re-run
fetched OSM fresh tonight; the adopted run fetched earlier. `Courthouse` → `OpenUBEMUnknown` is
what tag removal upstream would look like. The adopted run's input `01_buildings.gpkg` no longer
exists locally (`%TEMP%\ubem_elev_rebaseline\nyc_centre\` retains only `fleet_staging`,
`results`, `sim_out`, `step3`, and its `idfs` staging directory is empty), so the two fetches
cannot be diffed directly. **Do not assert OSM drift as established — it is the leading
hypothesis, not a measurement.**

**Confirmatory test still worth running, now with a sharp prediction.** Because the generator is
seeded (`default_rng(random_seed)`), the mechanism predicts that a **repeat run on unchanged
inputs reproduces bit-for-bit**: `nyc_centre` run-2 should equal run-1 exactly, *not* drift again.
If run-2 differs from run-1, the diagnosis above is incomplete and an unseeded source remains.
Run-1 is preserved in the session scratchpad (`nyc_centre_run1/`) for that comparison.

**One honest caveat.** `la_rural` moved by **+0.0657** with archetypes identical and zero Unknown
buildings, on 3 of 144 buildings. That is far too small to affect any conclusion, but it is not
zero, so the "identical archetypes ⇒ bit-identical cell" rule holds only to within a small
residual on that cell. It is not explained by the mechanism above.

---

**Status at time of writing (23:22).** Running: `nyc_urban`, `la_centre`, `la_urban`,
`la_suburban` (31 tasks live on Speed), `austin_centre`, `austin_suburban`. Done: `nyc_centre`,
`nyc_rural`, `nyc_suburban`. **Failed, to retry at low concurrency: `la_rural`, `austin_urban`.**
Pending: `austin_rural`. Note the arrays now queue behind one another on Speed — with several
cells in flight the cluster, not the local machine, is the binding constraint, which is the
intended state.

---

### T04 — fleet complete, and the confirmatory repeat (2026-08-13, director)

**All twelve cells landed.** The two SSH-transport failures were re-run one at a time by
`scripts/validation/open48_fleet_retry.py`: `la_rural` rc=0 at 01:06 (17 min), `austin_urban` rc=0
at 01:42 (36 min, SLURM job `1232246`, 425/425 generated and simulated). Neither was counted on its
failed attempt and no `REUSED_REMOTE` fired on either. `%TEMP%\open48_par\retry.log` is the record.

**Fleet result, computed with `scripts/analysis/open43_fleet_aggregations.py`'s own arithmetic
(not hand-rolled):**

| quantity | adopted `phaseE_elevrb` | re-run `open48_refleet` |
|---|---|---|
| pooled fleet EUI | 157.0552 | **159.2157** (+2.1605, **+1.38%**) |
| buildings / successes | 8,160 / 8,154 | 8,160 / 8,154 (same 6 known failures) |
| rows with `elevators_eui_kwh_m2 > 0` | 3,561 | **3,561**, matching cell by cell |

✅ **The non-vacuity control passes and OPEN-48's own question is answered** — the repository
regenerates the elevator energy. **The +2.16 is not elevators.** It is the four classification-drift
cells: `nyc_centre` +3.53, `austin_centre` +1.76, `la_centre` +1.60, `la_urban` +1.21. The other
eight reproduce to ±0.07 or better. Cause and mechanism are in the CAUSE FOUND section above.

**🔴 The confirmatory repeat's first launch died and nobody noticed for seven hours.** It was started
at 01:43 as a `python -c` one-liner whose import line was malformed; it exited immediately with
`SyntaxError: Expected one or more names after 'import'`, leaving a 0-byte
`nyc_centre_repeat.log` that looked like a run that had simply not printed yet.
**Lesson to carry: confirm a launched process is alive (PID + a growing log), not merely launched.**

**Relaunched 2026-08-13 09:06 (PID 4316), and the setup is what makes it a test at all.**
`run_cell("nyc_centre", output_subdir="open48_repeat")` from a real script file, logging to
`%TEMP%\open48_par\nyc_centre_repeat.log`. The remote fleet dir `open48_repeat_nyc_centre` is fresh,
so the REUSE trap cannot fire. 🔴 **Run-1's cached `01_buildings.gpkg`, `02a_climate_epw.parquet`
and `weather/` were copied into the new work dir first**, because `step1_fetch`
(`v12_cell_pipeline.py:137-141`) caches per `output_subdir` — without the copy the repeat would
re-fetch OSM and would **not** be a run on unchanged inputs, which is the whole condition of the
test. Confirmed on launch: 738 buildings loaded from the cached GDF, matching run-1 exactly.

**The prediction, written before the result:** the RNG is seeded (`default_rng(random_seed)`), so
run-2 must equal run-1 **bit-for-bit**. If it drifts again, the diagnosis above is incomplete and an
unseeded source remains. Run-1 is preserved in the session scratchpad (`nyc_centre_run1/`).

**Live record of the repeat run (appended as it goes, 2026-08-13).**

| stage | observed |
|---|---|
| launch | 09:06:56, PID 4316, real script file, `output_subdir="open48_repeat"` |
| step 1 | **738 buildings loaded from the cached GDF** — no OSM re-fetch, so inputs = run-1's inputs |
| step 3 | **738/738 IDFs generated in 1,601.1 s** (serial, `n_jobs=1`, as expected) |
| remote probe | `0/738 complete` — **no `REUSED_REMOTE`**, the fresh dir behaved as intended |
| submit | 09:33, `sbatch --array=1-738%32`, **SLURM job `1232712`**, fleet dir `/speed-scratch/o_iseri/fleets/open48_repeat_nyc_centre` |
| poll | in progress at 09:38 — 243 tasks `COMPLETED`, 33 in queue |

**✅ ANSWERED at 09:45, at the model-generation stage rather than the results stage.** The two runs'
staged IDF sets were compared directly — `fleet_staging/idfs`, MD5 per file, 738 files each:

```
run1=738  run2=738  shared=738  DIFFERING=0
```

🔴 **All 738 IDFs are byte-identical. The prediction written before the run is confirmed: on
unchanged inputs the pipeline reproduces bit-for-bit, seeded random `wwr` included.** This is the
**stronger** form of the test, not a shortcut — it isolates *model generation*, which is where the
adopted-vs-re-run difference was localised, and it does not depend on EnergyPlus determinism to
interpret. The simulations were left to finish (job `1232712`) so the results-level comparison
exists too, but it can no longer change the conclusion: identical IDF + identical EPW is the
condition under which E+ is deterministic, and both hold.

**Which branch of §8's three-way decision rule fired:** *run-2 ≈ run-1, both ≠ adopted* → **the
difference is in the inputs or in the adopted artifact, not in nondeterminism.** No unseeded source
remains. Combined with the IDF diff that found the moving buildings differ in window-vertex
Z-coordinates, the chain is now closed end to end: **inputs drifted → classification moved → the
Unknown cohort's `wwr` was redrawn → window geometry moved → EUI moved.**

⚠️ **What this does NOT settle, and must not be claimed:** *why* the classification drifted. The
adopted run's input `01_buildings.gpkg` is gone, so the two OSM fetches cannot be diffed. Upstream
tag change remains the leading hypothesis and nothing more.

**Not adopted, and the recommendation is to wait.** `157.1 kWh/m²` remains the published figure;
**159.2 carries a known defect rather than a better model**, and replacing it is the user's ruling.

#### The repeat run's `FAILED` array tasks — checked, and they are a *further* confirmation

The monitor raised `FAILED` on job `1232712`. It was run down rather than assumed, and it is not a
new problem:

| | run-1 (`open48_refleet_nyc_centre`) | run-2 (`open48_repeat_nyc_centre`) |
|---|---|---|
| first-attempt fatals | 3 — `way/265302168`, `way/266149332`, `way/266170765` | same building set, reproduced |
| the severe | `CalcHeatBalanceInsideSurf: temperature of -4020212.95 C`, zone `WAY/265302168_F0_CORE` | identical text |
| elapsed before fatal | 15.75 s | 16.66 s |
| recovered by the reroute stage | yes — `…_nyc_centre_reroute/out` has all three, `EnergyPlus Completed Successfully` | yes — repair job `1233881`, all three recovered |
| recovered EUI (kWh/m²) | 394.6826 / 873.3690 / 396.6100 | 394.6826 / 873.3690 / 396.6100 — identical |

So **the same three buildings blow up on the first attempt in both runs, with the same severe and the
same zone** — which is one more independent demonstration of determinism, not a defect surfacing.
The pipeline's own repair → reroute path already absorbed them in run-1: the fleet's 6 counted
failures are still 5 `la_rural` + 1 `la_urban`, and `nyc_centre`'s `05_results.csv` carries all 738
rows with no null EUI, its three recovered values coming from the reroute run and not from the
fatal one.

⚠️ **A trap worth naming for whoever reads the remote dirs next:** the fatal `eplusout.err` /
`eplusout.end` left behind in a cell's main `out/` directory is the *first attempt*, and it is not
overwritten when the reroute succeeds in a sibling `…_reroute` directory. Counting fatals under
`out/` therefore over-reports failures — fleet-wide it gives 12 where the true count is 6. Read
`…_reroute/out` before calling any building failed.

#### The results-level comparison — completed 2026-08-13 12:47, and it agrees

The repeat run finished (`738/738` simulated, job `1232712` + repair `1233881`) and wrote
`TEMP\ubem_validation\open48_repeat\nyc_centre\results\05_results.csv`. Comparing it row-for-row
against run-1's preserved `…\open48_refleet\nyc_centre\results\05_results.csv`:

| | value |
|---|---|
| rows / columns | 738 × 36 in both; 738 shared `osm_id`, no unmatched row |
| null `total_eui_kwh_m2` | 0 in both |
| rows differing in `total_eui_kwh_m2` (> 1e-9) | **37 of 738** |
| largest difference, any building | **0.00836 kWh/m²** (≈ 0.005% of that building's EUI) |
| largest difference, any numeric column | 0.00836 (`total_eui`), 0.00469 (`cooling`), 0.00367 (`fans`) |
| cell EUI, footprint-area-weighted | run-1 176.160747 → run-2 176.160719, **Δ = −2.8e-05** |

The residual is confined to `cooling` and `fans` — the two end uses that come out of the iterative
HVAC solver — while `lighting` and `equipment` are bit-identical. That is EnergyPlus's own
floating-point convergence noise between two runs of the *same* IDF, four orders of magnitude below
the +2.16 kWh/m² fleet gap under investigation. `heating` moves by 3e-07 and `dhw` by 8e-07.

🔴 **This closes the confirmatory test.** The MD5 evidence was already decisive — 738/738 IDFs
byte-identical means run-2 = run-1 by construction — and the results now agree to within solver
noise. **Neither run reproduces the adopted `phaseE_elevrb` number, so the fleet discrepancy is not
nondeterminism in the pipeline; it lives in the inputs (`wwr` re-randomisation).** Nothing in this
comparison could have changed that conclusion, and nothing in it does.

---

## 9. Director's close-out — do not edit

### CP-1 — signed 2026-08-12

**T01, T02, T03 and T05 are audited and accepted. T04 is unlocked.**

What was checked, and how:

- **T01 (OPEN-45).** Both surviving hand-rolled marker literals routed through `err_parse`.
  23 passed.
- **T02 (OPEN-47).** 598 / 8,160 (7.3%) archetype changes, all promotions, 437 newly gaining
  elevator eligibility; `levels_source` breakdown shows only 14.2% rest on an OSM-observed
  floor count. Measurement only, no default changed.
- **T05 (OPEN-47).** Deviation written into `building_classifier.py`. Director verified
  comment-only by reading the block itself, not the report. 131 passed.
- **T03 (OPEN-48 part 1).** ✅ **Accepted.** Every headline re-derived by the director
  from `parsed_A.parquet` / `parsed_B.parquet`, not from `ab_result.json` or the executor's
  summary; both agree. Non-vacuity holds (arm B exactly 0 on 425 buildings, arm A non-zero on
  56). Arms are single-variable (`archetype_id` and `floor_area_m2` identical building-for-
  building). The end-use decomposition is physically coherent and lighting/equipment move by
  exactly zero. Cluster provenance confirmed by `sacct` (`1222996`, `1223029`, 425/425
  `COMPLETED` each, zero failures) — not by trusting a report.
  **One deviation accepted:** the §5 fact-6 hex is not reproducible (harness deleted); the
  substituted live gate — 425 meter-absent buildings, `HEAD` parser vs working-tree parser,
  13 shared float keys, all bit-identical — is stronger evidence for the same claim and is
  accepted in its place. §5 fact 6 should be amended to cite the live gate.

**🔴 Authorisation for T04.** The fleet re-run is authorised, under the brief already
written in §6 T04, with the following standing on top of it:

1. **The re-run is single-variable.** T02 measured the archetype question and the user ruled
   area-only, so archetypes must not move. 🔴 **Any archetype difference between the T04
   output and the adopted `phaseE_elevrb` run is a bug, not an expected consequence — stop and
   report it.**
2. **Expected direction and rough size.** austin_urban gained **+2.5056%** pooled. The fleet
   figure will differ — 3,561 of 8,160 adopted rows carry elevator energy versus 56 of 425
   here — but the sign must be **positive** and the new fleet EUI must exceed **157.0552**.
   🔴 **A fleet delta of zero, or a negative one, means the wiring did not reach the
   cluster. Do not report it as success.**
3. **The REUSE trap stands.** `REUSED_REMOTE` for any cell means stale simulations are being
   reported. Stop if it appears.
4. **Do not background a monitor and wait for it.** This has now killed executors on this arc
   five times, including twice on T03.

### CP-2 — signed 2026-08-13, and it closes the plan

**T04 is audited and accepted. All five tasks in this plan are complete. Nothing in this arc is
running.** The plan is closed to further execution; what it produced now lives as two rulings owed to
the user, carried in `prompts/DIRECTOR_PROMPT_openings_2026-08-11.md` §3 as **2f** and **2g**.

What was checked, and how:

- **All twelve cells landed, and the two failures were transport, not physics.** `la_rural` and
  `austin_urban` died in `scp` against `speed-submit2` (exit 255, `Connection closed`), were re-run
  one at a time by `open48_fleet_retry.py`, and returned rc=0 (01:06 and 01:42). Neither was counted
  on its failed attempt. Verified against `%TEMP%\open48_par\retry.log`, not against a summary.
- **Fleet integrity holds.** 8,160 buildings, 8,154 successes, the **same 6 known failures**
  (5 `la_rural`, 1 `la_urban`) as the adopted run. The comparison is therefore single-variable on
  the building set.
- **Non-vacuity passes, and it is the answer to OPEN-48's own question.** **3,561 rows carry
  `elevators_eui_kwh_m2 > 0`, matching the adopted run cell by cell.** The restored wiring reaches
  the cluster and survives the harvest. ✅ **The repository can now regenerate elevator energy.**
- **The fleet figure was computed with `scripts/analysis/open43_fleet_aggregations.py`'s own
  arithmetic, not hand-rolled:** pooled **159.2157** against the adopted **157.0552**, +2.1605
  (+1.38%).
- **No `REUSED_REMOTE` fired on any cell** — authorisation point 3 holds.

**🔴 Authorisation point 1 fired exactly as it was written to, and that is the finding of this
plan.** It said *"any archetype difference between the T04 output and the adopted run is a bug, not
an expected consequence — stop and report it."* Archetypes **did** move, in four cells, and the stop
was taken. Tracing it produced the mechanism now owed as ruling 2f: `wwr` is drawn as one vectorised
block over the unidentified cohort (`openubem/semantic/__init__.py:229`), so **one reclassified
building redraws the windows of every unidentified building in the same cell.** Every cell whose
archetypes moved also moved in EUI (+1.21 to +3.53); every cell whose archetypes matched reproduced
to ±0.07. **The +2.16 is not elevators.**

**🔴 Authorisation point 2 was wrong and is struck.** It required the new fleet EUI to *exceed*
157.0552 and called a zero delta a failure. That criterion was written before the OPEN-47 ruling made
the re-run single-variable; under it, **reproduction was the expected outcome and a delta of ≈ 0
would have been the success case.** The +2.16 that did appear is a defect signature, not the
confirmation the criterion was reaching for. **Do not carry this criterion into any future re-run
brief.** Recorded in full in the T04 interim finding in §8.

**The confirmatory repeat is closed at both stages, which is stronger than the plan asked for.** The
plan called for a results-level repeat; the IDF-generation stage was compared first — **738 vs 738
staged IDFs, `DIFFERING=0`, every file byte-identical** — and the results stage then agreed:
**37 of 738 rows differ at all, largest difference 0.00836 kWh/m², cell EUI Δ = −2.8e-05**, residual
confined to `cooling` and `fans` with `lighting` and `equipment` bit-identical. 🔴 **On unchanged
inputs the pipeline reproduces bit-for-bit. The adopted-vs-re-run gap lives in the INPUTS.**

**Two things are deliberately NOT done here, because they are the user's:** the register entry for
OPEN-49, and any change to the published `157.1 kWh/m²`. **The register, `docs/PROJECT_CHECKLIST.md`
and the published-numbers board were not touched by this plan.** Director's standing recommendation
on the headline: **keep 157.1** — 159.2157 is the same model run through a known defect, not a better
model.

⚠️ **Carried forward unexplained, and it should not be quietly dropped:** `la_rural` moved **+0.0657**
with archetypes identical and zero unidentified buildings, on 3 of 144 buildings. Too small to touch
any conclusion in this plan, and **not accounted for by the mechanism above.**
